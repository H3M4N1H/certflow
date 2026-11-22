"""Native pywebview smoke test. Requires a working desktop display."""
import os
import sys
import tempfile
import threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['QT_API'] = 'pyside6'
import local_runtime
import webview

with tempfile.TemporaryDirectory() as directory:
    url = local_runtime.start(directory)
    window = webview.create_window('CertFlow native verification', url, width=1100, height=800)
    failures = []
    complete = threading.Event()
    def verify():
        try:
            assert window.run_js("document.querySelector('#certificateEditor') !== null")
            assert window.run_js("typeof getEmailPayload === 'function'")
            assert window.run_js("document.querySelectorAll('#mailerSmtpUser').length") == 0
            complete.set()
        except Exception as exc:
            failures.append(str(exc))
        finally:
            window.destroy()
    window.events.loaded += verify
    timer = threading.Timer(45, window.destroy);timer.start()
    try: webview.start(gui='qt')
    finally: timer.cancel();local_runtime.stop()
    assert complete.is_set(), failures or 'Native window did not load in 45 seconds'
    assert not failures,failures
    print('PASS native pywebview/Qt window loaded the local editor and shared mail UI')
