"""Process-death, credential exclusion and explicit SMTP rejection regression tests."""
import json
import os
import sqlite3
import subprocess
import sys
import unittest
from contextlib import closing
from unittest.mock import patch
import test_dynamic_mail as helpers
module = helpers.module


class RecoveryTests(unittest.TestCase):
    setUp = helpers.WorkflowTests.setUp
    post = helpers.WorkflowTests.post
    payload = helpers.WorkflowTests.payload

    def test_process_death_releases_lock_and_preserves_uncertainty(self):
        code = '''import os, sqlite3, sys
from local_worker import queue_lock
with queue_lock(sys.argv[1]) as acquired:
    assert acquired
    with sqlite3.connect(sys.argv[1]) as connection:
        connection.execute("INSERT INTO mailer_queue (email,name,status) VALUES ('a@example.com','Alice','sending')")
    os._exit(9)
'''
        result = subprocess.run([sys.executable, '-c', code, module.DB_PATH], check=False)
        self.assertEqual(result.returncode, 9)
        with patch.object(module, '_tm_send_one') as send:
            self.assertEqual(self.client.get('/mailer/send-next').get_json()['status'], 'manual_pause')
            self.assertEqual(self.client.get('/mailer/status').get_json()['uncertain'], 1)
            send.assert_not_called()
        with closing(sqlite3.connect(module.DB_PATH)) as conn:
            self.assertEqual(conn.execute("SELECT value FROM mailer_state WHERE key='tm_manual_pause'").fetchone()[0], '1')

    def test_bulk_payload_survives_reload_without_password(self):
        with patch.object(module, '_make_smtp_connection', side_effect=OSError('offline')):
            self.post('/send-certificates', self.payload()).get_data()
        with closing(sqlite3.connect(module.DB_PATH)) as conn:
            payload = json.loads(conn.execute('SELECT payload FROM send_jobs').fetchone()[0])
            self.assertNotIn('smtpPassword', payload)
        saved = self.client.get('/send-jobs/latest').get_json()['job']
        self.assertEqual(saved['jobId'], self.payload()['jobId'])
        self.assertEqual(saved['participants'], self.payload()['participants'])
        self.assertNotIn('smtpPassword', saved)

    def test_explicit_smtp_rejection_is_retryable_not_uncertain(self):
        class SMTP:
            def sendmail(self, *args): raise module.smtplib.SMTPDataError(451, b'Try later')
            def quit(self): pass
        with patch.object(module, '_make_smtp_connection', return_value=SMTP()):
            response = self.post('/send-certificates', self.payload()).get_data(as_text=True)
        self.assertIn('"type": "retry"', response)
        with closing(sqlite3.connect(module.DB_PATH)) as conn:
            self.assertEqual(json.loads(conn.execute('SELECT completed FROM send_jobs').fetchone()[0]), {})


if __name__ == '__main__': unittest.main()
