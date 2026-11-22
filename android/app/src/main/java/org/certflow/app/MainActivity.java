package org.certflow.app;
import android.app.*;
import android.content.*;
import android.net.Uri;
import android.os.*;
import android.webkit.*;
import android.widget.*;
import java.io.*;
import java.net.*;
import java.util.concurrent.*;

public class MainActivity extends Activity {
    private WebView web;
    private ValueCallback<Uri[]> upload;
    private String origin, exportToken, exportName;
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        int systemAppearance = android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
        if(Build.VERSION.SDK_INT>=26) systemAppearance |= android.view.View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
        getWindow().getDecorView().setSystemUiVisibility(systemAppearance);
        if (saved != null) {exportToken=saved.getString("exportToken");exportName=saved.getString("exportName");}
        LinearLayout layout = new LinearLayout(this);layout.setOrientation(LinearLayout.VERTICAL);
        layout.setOnApplyWindowInsetsListener((view,insets)->{
            if(Build.VERSION.SDK_INT>=30){
                android.graphics.Insets bars=insets.getInsets(android.view.WindowInsets.Type.systemBars());
                view.setPadding(bars.left,bars.top,bars.right,bars.bottom);
            }else view.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
            return insets;
        });
        Button background = new Button(this);background.setText("Background mail options");background.setAllCaps(false);layout.addView(background);
        background.setOnClickListener(v -> new AlertDialog.Builder(this).setTitle("Scheduled email")
            .setMessage("Android can delay delivery or stop an active session. Recovery work runs when Android permits. Core editing works offline.")
            .setPositiveButton("Start active session", (d,w)-> {
                if(Build.VERSION.SDK_INT>=33)requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"},10);
                Intent intent=new Intent(this,MailService.class);
                try {if(Build.VERSION.SDK_INT>=26)startForegroundService(intent);else startService(intent);}
                catch(Exception e){Toast.makeText(this,"Android cannot start background sending now. Keep the app open or try later.",Toast.LENGTH_LONG).show();}
            }).setNeutralButton("Stop active session",(d,w)->stopService(new Intent(this,MailService.class)))
            .setNegativeButton("Close",null).show());
        web=new WebView(this);layout.addView(web,new LinearLayout.LayoutParams(-1,0,1));setContentView(layout);
        web.getSettings().setJavaScriptEnabled(true);web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setAllowFileAccess(false);web.getSettings().setAllowContentAccess(true);
        web.getSettings().setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        web.addJavascriptInterface(new Exports(),"CertFlowNative");
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri u=request.getUrl(); if(origin!=null && u.toString().startsWith(origin+"/"))return false;
                if ("https".equals(u.getScheme())) {try {startActivity(new Intent(Intent.ACTION_VIEW,u));}catch(Exception ignored){}}
                return true;
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if(upload!=null)upload.onReceiveValue(null);upload=callback;
                Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("*/*");
                i.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,params.getMode()==FileChooserParams.MODE_OPEN_MULTIPLE);
                startActivityForResult(i,1);return true;
            }
        });
        io.execute(()-> {
            try {String url=RuntimeHost.start(this);origin=url.substring(0,url.indexOf("/local/"));runOnUiThread(()->web.loadUrl(url));MailWorker.schedule(this);}
            catch(Exception e){runOnUiThread(()->new AlertDialog.Builder(this).setMessage("Unable to start the local certificate engine. Restart the app.").setPositiveButton("Close",(d,w)->finish()).show());}
        });
    }
    private class Exports {
        @JavascriptInterface public void save(String token,String name) {
            if(!token.matches("[0-9a-f]{48}"))return;
            runOnUiThread(()-> {
                if(exportToken!=null){Toast.makeText(MainActivity.this,"Finish the current export first.",Toast.LENGTH_SHORT).show();return;}
                exportToken=token;exportName=name.replaceAll("[/\\\\]","_");
                Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("application/octet-stream").putExtra(Intent.EXTRA_TITLE,exportName);
                startActivityForResult(i,2);
            });
        }
    }
    @Override protected void onSaveInstanceState(Bundle out) {super.onSaveInstanceState(out);out.putString("exportToken",exportToken);out.putString("exportName",exportName);}
    @Override protected void onActivityResult(int request,int result,Intent data) {
        super.onActivityResult(request,result,data);
        if(request==1 && upload!=null){upload.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result,data));upload=null;}
        if(request==2){
            final String token=exportToken;exportToken=null;
            if(result!=RESULT_OK||data==null||token==null)return;
            Uri destination=data.getData();String cookie=android.webkit.CookieManager.getInstance().getCookie(origin);
            io.execute(()-> {
                try {
                    HttpURLConnection c=(HttpURLConnection)new URL(origin+"/local/exports/"+token).openConnection();c.setRequestProperty("Cookie",cookie);c.setConnectTimeout(15000);c.setReadTimeout(120000);
                    if(c.getResponseCode()!=200)throw new IOException("Export expired");
                    try(InputStream in=c.getInputStream();OutputStream out=getContentResolver().openOutputStream(destination)) {
                        byte[] buffer=new byte[65536];int n;while((n=in.read(buffer))!=-1)out.write(buffer,0,n);
                    } finally {c.disconnect();}
                    runOnUiThread(()->Toast.makeText(this,"Certificate export saved",Toast.LENGTH_LONG).show());
                }catch(Exception e){runOnUiThread(()->Toast.makeText(this,"Export could not be saved. Generate it again.",Toast.LENGTH_LONG).show());}
            });
        }
    }
    @Override public void onBackPressed(){if(web.canGoBack())web.goBack();else super.onBackPressed();}
    @Override protected void onDestroy(){if(upload!=null)upload.onReceiveValue(null);web.destroy();io.shutdown();super.onDestroy();}
}
