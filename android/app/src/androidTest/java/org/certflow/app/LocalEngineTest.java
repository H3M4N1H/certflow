package org.certflow.app;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import static androidx.test.platform.app.InstrumentationRegistry.getInstrumentation;
import static org.junit.Assert.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import com.chaquo.python.Python;
import java.io.*;

/** Runs the actual packaged Flask/Pillow/SQLite stack on an Android device. */
@RunWith(AndroidJUnit4.class)
public class LocalEngineTest {
    @Test public void testOfflineEngineAndCredentialVault() throws Exception {
        String url=RuntimeHost.start(getInstrumentation().getTargetContext());
        assertTrue(url.startsWith("http://127.0.0.1:"));
        String script;
        try (InputStream in=getInstrumentation().getContext().getAssets().open("android_engine_checks.py")) {
            ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buffer=new byte[8192];int n;
            while((n=in.read(buffer))!=-1)out.write(buffer,0,n);
            script=out.toString("UTF-8");
        }
        Python.getInstance().getModule("builtins").callAttr("exec",script);
        CredentialVault.put("instrumentation-only");
        assertEquals("instrumentation-only",CredentialVault.get());
        CredentialVault.clear();assertEquals("",CredentialVault.get());
    }

    @Test public void testWebViewLoadsLocalEditor() throws Exception {
        android.app.Activity activity = getInstrumentation().startActivitySync(
            new android.content.Intent(getInstrumentation().getTargetContext(), MainActivity.class)
                .addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK));
        try {
            boolean ready = false;
            for (int attempt=0; attempt<40 && !ready; attempt++) {
                java.util.concurrent.CountDownLatch latch=new java.util.concurrent.CountDownLatch(1);
                java.util.concurrent.atomic.AtomicBoolean result=new java.util.concurrent.atomic.AtomicBoolean();
                getInstrumentation().runOnMainSync(()->{
                    android.webkit.WebView view=findWebView(activity.getWindow().getDecorView());
                    if(view==null){latch.countDown();return;}
                    view.evaluateJavascript("location.hostname === '127.0.0.1' && document.querySelector('#certificateEditor') !== null && typeof getEmailPayload === 'function'",value->{result.set("true".equals(value));latch.countDown();});
                });
                assertTrue(latch.await(5,java.util.concurrent.TimeUnit.SECONDS));
                ready=result.get();if(!ready)Thread.sleep(500);
            }
            assertTrue("Android WebView must load the bundled local editor",ready);
        } finally {getInstrumentation().runOnMainSync(activity::finish);}
    }
    private android.webkit.WebView findWebView(android.view.View view) {
        if(view instanceof android.webkit.WebView)return (android.webkit.WebView)view;
        if(view instanceof android.view.ViewGroup){
            android.view.ViewGroup group=(android.view.ViewGroup)view;
            for(int i=0;i<group.getChildCount();i++){
                android.webkit.WebView result=findWebView(group.getChildAt(i));if(result!=null)return result;
            }
        }
        return null;
    }
}
