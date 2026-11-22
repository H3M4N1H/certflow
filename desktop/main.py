"""CertFlow desktop entry point; packaged users never need a terminal."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    import argparse
    import subprocess
    import time
    from platformdirs import user_data_dir
    import local_runtime
    from local_worker import LocalScheduler, queue_lock
    parser = argparse.ArgumentParser()
    parser.add_argument('--background', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--data-dir', default=user_data_dir('CertFlow', 'CertFlow'))
    args = parser.parse_args()
    local_runtime.configure(args.data_dir)
    import app
    if args.background:
        with queue_lock(app.DB_PATH + '.background') as acquired:
            if not acquired:
                return
            worker = LocalScheduler()
            worker.start()
            try:
                while app._mstate_get('desktop_background') == '1':
                    time.sleep(5)
            finally:
                worker.stop()
        return
    url = local_runtime.start(args.data_dir)
    worker = LocalScheduler()
    worker.start()
    try:
        if args.self_test:
            import urllib.request
            import http.cookiejar
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
            with opener.open(url) as response:
                assert b'certificateEditor' in response.read()
            assert app.load_font('arial.ttf', 38).getname()[0] == 'Noto Sans'
            print('CertFlow packaged runtime self-test passed')
        else:
            import webview
            webview.settings['ALLOW_DOWNLOADS'] = True
            webview.create_window('CertFlow', url, width=1240, height=850, min_size=(420, 600))
            if sys.platform.startswith('linux'):
                os.environ['QT_API'] = 'pyside6'
                webview.start(gui='qt', icon=str(Path(app.RESOURCE_DIR) / 'static' / 'icon.png'))
            else:
                webview.start()
    finally:
        worker.stop()
        local_runtime.stop()
        if not args.self_test and app._mstate_get('desktop_background') == '1':
            command = [sys.executable]
            if not getattr(sys, 'frozen', False):
                command.append(str(Path(__file__).resolve()))
            command += ['--background', '--data-dir', args.data_dir]
            options = {'stdin': subprocess.DEVNULL, 'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL}
            if os.name == 'nt':
                options['creationflags'] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                options['start_new_session'] = True
            subprocess.Popen(command, **options)


if __name__ == '__main__':
    main()
