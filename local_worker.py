"""Shared scheduler heartbeat. Timing and pause decisions remain in app.py."""
import os
import threading
from contextlib import contextmanager


@contextmanager
def queue_lock(database):
    """OS-owned lock: released on process death, never expires during SMTP I/O."""
    path = database + '.mailer.lock'
    with open(path, 'a+b') as handle:
        if os.name == 'nt':
            import msvcrt
            handle.seek(0); handle.write(b'0'); handle.flush(); handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                yield False
                return
        else:
            import fcntl
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                yield False
                return
        try:
            yield True
        finally:
            if os.name == 'nt':
                handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def tick():
    import app
    with app.app.app_context():
        return app.mailer_tick()


class LocalScheduler:
    def __init__(self):
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run, name='certflow-scheduler', daemon=True)

    def start(self):
        self.thread.start()

    def run(self):
        import app
        while not self.stop_event.is_set():
            try:
                tick()
            except Exception:
                # Exception strings from SMTP may contain account details.
                app.logger.error('Local scheduler tick failed; will retry.')
            self.stop_event.wait(15)

    def stop(self):
        self.stop_event.set()
