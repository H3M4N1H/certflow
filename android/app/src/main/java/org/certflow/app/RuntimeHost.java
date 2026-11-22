package org.certflow.app;

import android.content.Context;
import com.chaquo.python.Python;
import com.chaquo.python.PyObject;
import com.chaquo.python.android.AndroidPlatform;
import java.io.*;

public final class RuntimeHost {
    private static PyObject runtime;
    private static String url;
    public static synchronized String start(Context context) throws IOException {
        if (url != null) return url;
        Context app = context.getApplicationContext();
        CredentialVault.init(app);
        File assets = new File(app.getFilesDir(), "runtime");
        copy(app, "runtime", assets);
        if (!Python.isStarted()) Python.start(new AndroidPlatform(app));
        runtime = Python.getInstance().getModule("local_runtime");
        Python.getInstance().getModule("os").get("environ").callAttr("__setitem__", "CERTFLOW_RESOURCE_DIR", assets.getAbsolutePath());
        Python.getInstance().getModule("os").get("environ").callAttr("__setitem__", "CERTFLOW_ANDROID", "1");
        url = runtime.callAttr("start", new File(app.getFilesDir(), "data").getAbsolutePath()).toString();
        return url;
    }
    public static String tick(Context c) throws IOException { start(c); return runtime.callAttr("scheduler_tick").toString(); }
    public static void pause(Context c, boolean pause) throws IOException { start(c); runtime.callAttr("pause", pause); }
    private static void copy(Context c, String source, File dest) throws IOException {
        String[] children = c.getAssets().list(source);
        if (children != null && children.length > 0) {
            if (!dest.isDirectory() && !dest.mkdirs()) throw new IOException("Cannot create runtime assets");
            for (String child: children) copy(c, source + "/" + child, new File(dest, child));
        } else {
            try (InputStream in = c.getAssets().open(source); OutputStream out = new FileOutputStream(dest)) { byte[] buffer = new byte[65536]; int n; while ((n = in.read(buffer)) != -1) out.write(buffer, 0, n); }
        }
    }
}
