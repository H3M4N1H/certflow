"""Run with the app's virtualenv; uses isolated local data and no SMTP."""
import io
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
from playwright.sync_api import sync_playwright
import local_runtime

with tempfile.TemporaryDirectory() as directory:
    url = local_runtime.start(directory)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            for width, dpi in ((1280, 1), (720, 2), (390, 3)):
                context = browser.new_context(viewport={'width':width,'height':900}, device_scale_factor=dpi, has_touch=True, accept_downloads=True)
                context.route('**/*', lambda route: route.continue_() if route.request.url.startswith(url.split('/local/')[0]) else route.abort())
                page=context.new_page(); errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(url)
                assert context.request.get(url.split('/local/')[0]+'/health', headers={'Origin':'https://untrusted.example'}).status == 403
                assert context.request.post(url.split('/local/')[0]+'/editor/text', data={'fields':[]}).status == 403
                image=io.BytesIO();Image.new('RGB',(1920,1080),'white').save(image,'PNG')
                page.locator('#templateFile').set_input_files({'name':'template.png','mimeType':'image/png','buffer':image.getvalue()})
                page.locator('#csvFile').set_input_files({'name':'people.csv','mimeType':'text/csv','buffer':b'Name,Department,College,Position,Email\nAlice,IT,College A,Winner,a@example.com\nBob,CS,College B,Runner,b@example.com\n'})
                page.wait_for_function('() => csvParticipants.length===2')
                page.locator('[data-action=add]').click();page.wait_for_selector('.editor-object')
                before=page.evaluate('({x:editor.fields[0].X,y:editor.fields[0].Y,scale:editor.factor})')
                page.locator('.editor-object').scroll_into_view_if_needed();box=page.locator('.editor-object').bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2
                page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+40,y+20,steps=5);page.mouse.up()
                after=page.evaluate('({x:editor.fields[0].X,y:editor.fields[0].Y})')
                assert abs(after['x']-before['x']-40/before['scale'])<=1,(width,before,after)
                assert abs(after['y']-before['y']-20/before['scale'])<=1
                page.locator('[data-action=undo]').click();assert page.evaluate('editor.fields[0].X')==before['x']
                page.locator('[data-action=redo]').click();assert page.evaluate('editor.fields[0].X')==after['x']
                page.locator('[data-action=in]').click();page.locator('[data-action=fit]').click();page.wait_for_timeout(400)
                # Real browser touch input, not mouse events labeled as touch.
                page.locator('.editor-object').scroll_into_view_if_needed();box=page.locator('.editor-object').bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2
                before_touch=page.evaluate('editor.fields[0].Y');factor=page.evaluate('editor.factor')
                cdp=context.new_cdp_session(page)
                cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
                cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y+25}]})
                cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
                assert abs(page.evaluate('editor.fields[0].Y')-before_touch-25/factor)<=1
                page.locator('[data-action=duplicate]').click();assert page.evaluate('editor.fields.length')==2
                page.locator('[data-key=column]').select_option('2')
                page.locator('.editor-record').fill('2');page.locator('.editor-record').dispatch_event('change')
                page.wait_for_timeout(250)
                with page.expect_download() as downloaded:page.locator('[data-action=save]').click()
                layout=Path(directory)/f'layout-{width}.json';downloaded.value.save_as(layout)
                saved=page.evaluate('editor.fields')
                page.locator('[data-action=delete]').click()
                page.locator('.editor-load input').set_input_files(layout)
                page.wait_for_function('() => editor.fields.length===2')
                assert page.evaluate('editor.fields')==saved
                page.locator('#previewBtn').click();page.wait_for_selector('#previewImage[src^="data:"]')
                with page.expect_download() as downloaded:page.locator('#generateBtn').click()
                assert downloaded.value.suggested_filename.endswith('.zip')
                page.locator('#certificateEditor').screenshot(path=f'/tmp/certflow-editor-{width}.png')
                assert not errors,errors
                print(f'PASS editor mouse/touch, coordinates, zoom, undo/redo, layout, preview, ZIP: {width}px @ {dpi}x')
                context.close()
            browser.close()
    finally:local_runtime.stop()
