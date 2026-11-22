import base64
import io
import os
import sqlite3
import zipfile
from urllib.parse import urlsplit
from PIL import Image
import app
import local_runtime

app.limiter.enabled = False
origin = local_runtime._origin
client = app.app.test_client()
assert client.get('/health', base_url=origin).status_code == 403
response = client.get('/local/open?token=' + local_runtime._bootstrap, base_url=origin)
assert response.status_code == 302
with client.session_transaction(base_url=origin) as session:
    session['_csrf_token'] = 'android-test'
headers = {'X-CSRFToken': 'android-test'}
response = client.post('/parse-csv', base_url=origin, headers=headers, data={
    'headerMode':'yes', 'csvFile':(io.BytesIO(b'Name,Department,College,Email\nAlice,IT,College,a@example.com\n'), 'people.csv')})
assert response.status_code == 200, response.get_data(as_text=True)
people = response.get_json()['participants']
image = io.BytesIO();Image.new('RGB', (600, 400), 'white').save(image, 'PNG')
template = 'data:image/png;base64,' + base64.b64encode(image.getvalue()).decode()
fields = [{'column':0,'X':300,'Y':100,'FontSize':38,'Font':'arial.ttf','Align':'center','Anchor':'top'}]
payload = dict(template=template, participants=people, settings={'fields':fields,'exportFormat':'png'})
response = client.post('/editor/text', base_url=origin, headers=headers, json={'fields':fields,'values':people[0]['values']})
assert response.status_code == 200, response.get_data(as_text=True)
response = client.post('/generate-batch', base_url=origin, headers=headers, json=payload)
assert response.status_code == 200, response.get_data(as_text=True)
with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
    generated = Image.open(io.BytesIO(archive.read(archive.namelist()[0])))
    assert generated.size == (600,400)
    assert generated.getextrema() != ((255,255),)*3
payload['settings']['exportFormat']='pdf'
response = client.post('/generate-batch', base_url=origin, headers=headers, json=payload)
assert response.status_code == 200 and response.data.startswith(b'%PDF'), response.get_data(as_text=True)
# No SMTP: validate SQLite persistence across independent connections.
with sqlite3.connect(app.DB_PATH) as connection:
    connection.execute("INSERT OR REPLACE INTO mailer_state VALUES ('tm_manual_pause','1')")
assert app._mstate_get('tm_manual_pause') == '1'
print('ANDROID PASS: loopback authentication, CSV, text raster, PNG/ZIP/PDF, SQLite')
