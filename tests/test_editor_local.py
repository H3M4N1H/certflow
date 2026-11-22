"""Pixel accuracy and recovery tests; all mail operations are mocked."""
import base64
import io
import json
import os
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch
from PIL import Image, ImageChops
import test_dynamic_mail as helpers
module = helpers.module
from local_worker import queue_lock


class EditorTests(unittest.TestCase):
    setUp = helpers.WorkflowTests.setUp
    post = helpers.WorkflowTests.post
    def test_sprite_matches_export_at_every_alignment(self):
        for alignment in ('left', 'center', 'right'):
            for size in (12, 38, 90):
                field = dict(column=0, X=250, Y=100, Font='arial.ttf', FontSize=size,
                             Color='#124abc', Bold=True, Align=alignment, Anchor='top')
                response = self.post('/editor/text', {'fields': [field], 'values': ['Alice gyp']})
                tile = response.get_json()['fields'][0]
                sprite = Image.open(io.BytesIO(base64.b64decode(tile['image'].split(',')[1])))
                expected = Image.new('RGB', (800, 500), 'white')
                expected.paste(sprite, (250 + tile['offset'], 100), sprite)
                actual = module.draw_certificate(Image.new('RGB', (800, 500), 'white'), '', '',
                    module.validate_settings({'fields': [field]}), values=['Alice gyp'])
                self.assertIsNone(ImageChops.difference(expected, actual).getbbox())

    def test_static_text_and_validation(self):
        data = {'fields': [dict(column=-1, Text='Award', Anchor='top')]}
        self.assertEqual(self.post('/editor/text', data).status_code, 200)
        for bad in ([{'column': -2}], [{'column': 0, 'Text': 'x'*201}], [{'column': 0}]*101):
            self.assertEqual(self.post('/editor/text', {'fields': bad}).status_code, 400)
        self.assertEqual(self.client.post('/editor/text', json=data).status_code, 403)

    def test_queue_lock_and_crash_recovery(self):
        with closing(sqlite3.connect(module.DB_PATH)) as conn, conn:
            conn.execute("INSERT INTO mailer_queue (email,name,status) VALUES ('a@example.com','Alice','sending')")
        with queue_lock(module.DB_PATH) as first:
            self.assertTrue(first)
            with queue_lock(module.DB_PATH) as second:
                self.assertFalse(second)
            self.assertEqual(self.client.get('/mailer/send-next').get_json()['status'], 'sending')
        with patch.object(module, '_tm_send_one') as send:
            self.client.get('/mailer/send-next')
            send.assert_not_called()
        self.assertEqual(self.client.get('/mailer/status').get_json()['uncertain'], 1)

    def test_gap_cooldown_and_persisted_batch_size(self):
        with closing(sqlite3.connect(module.DB_PATH)) as conn, conn:
            conn.executemany("INSERT INTO mailer_queue (email,name) VALUES (?,?)", [('a@example.com','A'),('b@example.com','B')])
        now = module.time.time()
        now = module.time.time()
        module._mstate_set('tm_batch_size', 15)
        module._mstate_set('tm_batch_count', 14)
        with patch.object(module, '_tm_send_one') as send, patch.object(module.time, 'time', return_value=now):
            self.assertEqual(self.client.get('/mailer/send-next').get_json()['status'], 'sent')
            self.assertEqual(self.client.get('/mailer/send-next').get_json()['status'], 'paused')
            self.assertEqual(module._mstate_get('tm_batch_size'), '15')
            send.assert_called_once()
        with patch.object(module, '_tm_send_one') as send, patch.object(module.time, 'time', return_value=now+10000):
            self.assertEqual(self.client.get('/mailer/send-next').get_json()['status'], 'sent')
            send.assert_called_once()

    def test_uncertain_delivery_requires_explicit_resolution(self):
        with closing(sqlite3.connect(module.DB_PATH)) as conn, conn:
            rid=conn.execute("INSERT INTO mailer_queue (email,name) VALUES ('a@example.com','A')").lastrowid
        with patch.object(module, '_tm_send_one', side_effect=module.DeliveryUncertain()):
            self.assertEqual(self.client.get('/mailer/send-next').status_code, 409)
        self.assertEqual(module._mstate_get('tm_manual_pause'), '1')
        self.assertEqual(self.post('/mailer/resolve', {'id':rid, 'action':'sent'}).status_code,200)
        self.assertEqual(self.client.get('/mailer/status').get_json()['sent'],1)


if __name__ == '__main__': unittest.main()
