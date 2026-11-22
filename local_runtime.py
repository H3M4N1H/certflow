"""Private embedded runtime shared by desktop and Android. Never binds publicly."""
import os
import secrets
import threading
from pathlib import Path

_server = None
_origin = None
_bootstrap = None


def configure(data_dir):
    root = Path(data_dir).resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != 'nt':
        os.chmod(root, 0o700)
    key = root / 'session.key'
    try:
        fd = os.open(key, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        pass
    else:
        with os.fdopen(fd, 'w') as handle:
            handle.write(secrets.token_hex(32))
    os.environ.update(CERTFLOW_LOCAL='1', CERTFLOW_DATA_DIR=str(root),
                      DB_PATH=str(root / 'certflow.db'), UPLOAD_FOLDER=str(root / 'uploads'),
                      SECRET_KEY=key.read_text(), SESSION_COOKIE_SECURE='false',
                      GLOBAL_RATE_LIMIT='10000 per hour')
    return root


def start(data_dir):
    global _server, _origin, _bootstrap
    if _server:
        return _origin + '/local/open?token=' + _bootstrap
    root = configure(data_dir)
    import app as module
    from flask import request, session, abort, redirect, jsonify, send_file
    from werkzeug.serving import make_server
    _bootstrap = secrets.token_urlsafe(32)
    export_dir = root / 'exports'
    export_dir.mkdir(mode=0o700, exist_ok=True)
    # Incomplete/stale exports have no durable job state and are safe to discard.
    for path in export_dir.glob('*.bin'):
        path.unlink()

    @module.app.before_request
    def local_boundary():
        if request.host != _origin.removeprefix('http://'):
            abort(403)
        origin = request.headers.get('Origin')
        if origin and origin != _origin:
            abort(403)
        if request.path == '/local/open':
            if not secrets.compare_digest(request.args.get('token', ''), _bootstrap):
                abort(403)
            session['local_access'] = True
            session['authenticated'] = True
            session['username'] = 'local-owner'
            return redirect('/')
        if not session.get('local_access'):
            abort(403)

    @module.app.route('/local/background', methods=['GET', 'POST'])
    def background_setting():
        if os.environ.get('CERTFLOW_ANDROID') == '1':
            return jsonify(platform='android')
        if request.method == 'POST':
            module.require_csrf()
            module._mstate_set('desktop_background', '1' if (request.get_json(silent=True) or {}).get('enabled') is True else '0')
        return jsonify(platform='desktop', enabled=module._mstate_get('desktop_background') == '1')

    @module.app.post('/local/exports')
    def store_export():
        module.require_csrf()
        token = secrets.token_hex(24)
        path = export_dir / (token + '.bin')
        # Bound disk usage, including abandoned picker operations.
        if sum(p.stat().st_size for p in export_dir.glob('*.bin')) > 512 * 1024 * 1024:
            return jsonify(error='Export cache full. Restart the app after saving exports.'), 413
        with path.open('wb') as out:
            import shutil
            shutil.copyfileobj(request.stream, out, length=1024*1024)
        return jsonify(token=token)

    @module.app.get('/local/exports/<token>')
    def read_export(token):
        if len(token) != 48 or any(c not in '0123456789abcdef' for c in token):
            abort(404)
        return send_file(export_dir / (token + '.bin'), as_attachment=True)

    # No request logging: bootstrap capability must never enter logs.
    from werkzeug.serving import WSGIRequestHandler
    class QuietHandler(WSGIRequestHandler):
        def log_request(self, *args, **kwargs):
            pass
    _server = make_server('127.0.0.1', 0, module.app, threaded=True, request_handler=QuietHandler)
    _origin = f'http://127.0.0.1:{_server.server_port}'
    threading.Thread(target=_server.serve_forever, daemon=True, name='certflow-http').start()
    return _origin + '/local/open?token=' + _bootstrap


def stop():
    global _server
    if _server:
        _server.shutdown()
        _server = None


def scheduler_tick():
    from local_worker import tick
    response = tick()
    if isinstance(response, tuple):
        response = response[0]
    return response.get_json()['status']


def pause(paused):
    import app
    app._mstate_set('tm_manual_pause', '1' if paused else '0')
