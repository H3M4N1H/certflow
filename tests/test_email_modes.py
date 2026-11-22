"""The only difference between Step 5 and Step 6 is dispatch timing."""
import base64
import io
import os
import sqlite3
import tempfile
import unittest
import zipfile
from contextlib import closing
from email import message_from_bytes, message_from_string
from unittest.mock import patch
from PIL import Image
import test_dynamic_mail as helpers
module=helpers.module


def normalized(msg):
    return (msg['From'],msg['To'],msg['Subject'],
            [(part.get_content_type(),part.get_filename(),part.get_payload(decode=True))
             for part in msg.walk() if not part.is_multipart()])


class EmailModeTests(unittest.TestCase):
    setUp=helpers.WorkflowTests.setUp
    post=helpers.WorkflowTests.post

    def test_same_messages_for_plain_certificate_zip_and_combined_modes(self):
        image=io.BytesIO();Image.new('RGB',(400,200),'white').save(image,'PNG')
        zipped=io.BytesIO()
        with zipfile.ZipFile(zipped,'w') as z:z.writestr('pass.txt',b'Participant pass')
        for certificate,extra in ((False,False),(True,False),(False,True),(True,True)):
            with self.subTest(certificate=certificate,extra=extra), tempfile.TemporaryDirectory() as root:
                self.setUp()
                payload={'smtpUser':'sender@example.com','smtpPassword':'fake','smtpProvider':'gmail',
                         'participants':[{'name':'Alice','email':'a@example.com','values':['Alice','IT','Winner']}],
                         'emailSubject':'Award for {string3}', 'emailBody':'Hello {string1} from {string2}',
                         'fromName':'Event Team', 'attachCert':certificate,'emailAttachFormat':'png',
                         'settings':{'fields':[{'column':0,'X':50,'Y':50,'Anchor':'top'}]}}
                if certificate:payload['template']='data:image/png;base64,'+base64.b64encode(image.getvalue()).decode()
                if extra:payload['attachmentsZip']='data:application/zip;base64,'+base64.b64encode(zipped.getvalue()).decode()
                messages=[]
                class SMTP:
                    def sendmail(self,sender,recipient,message):
                        messages.append(message_from_bytes(message) if isinstance(message,bytes) else message_from_string(message))
                    def quit(self):pass
                with patch.dict(os.environ,{'CERTFLOW_DATA_DIR':root}),patch.object(module,'_make_smtp_connection',return_value=SMTP()):
                    response=self.post('/send-certificates',payload).get_data(as_text=True)
                    self.assertIn('"sent": 1',response)
                    scheduled=self.post('/mailer/generate-queue',payload)
                    self.assertEqual(scheduled.status_code,200,scheduled.get_data(as_text=True))
                    self.assertEqual(module._mstate_get('tm_manual_pause'),'1')
                    self.post('/mailer/control',{'action':'resume'})
                    self.assertEqual(self.client.get('/mailer/send-next').get_json()['status'],'sent')
                    self.assertEqual(len(messages),2)
                    self.assertEqual(normalized(messages[0]),normalized(messages[1]))
                    self.assertEqual(self.client.get('/mailer/send-next').get_json()['status'],'done')
                    self.assertEqual(len(messages),2)


if __name__=='__main__':unittest.main()
