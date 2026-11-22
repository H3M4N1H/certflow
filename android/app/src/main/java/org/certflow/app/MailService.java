package org.certflow.app;
import android.app.*;
import android.content.*;
import android.os.*;
import java.util.concurrent.*;

public class MailService extends Service {
    private ScheduledExecutorService executor;
    @Override public void onCreate() {
        super.onCreate();
        if (Build.VERSION.SDK_INT >= 26) getSystemService(NotificationManager.class).createNotificationChannel(new NotificationChannel("mail", "Certificate sending", NotificationManager.IMPORTANCE_LOW));
    }
    private Notification notification(String status) {
        Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(this,"mail") : new Notification.Builder(this);
        PendingIntent open = PendingIntent.getActivity(this, 0, new Intent(this, MainActivity.class), PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        b.setContentTitle("CertFlow scheduled mail").setContentText(status + ". Android may defer delivery.").setSmallIcon(android.R.drawable.stat_notify_sync).setOngoing(true).setContentIntent(open);
        for (String action: new String[]{"Pause", "Resume"}) {
            Intent i = new Intent(this, MailService.class).setAction(action);
            PendingIntent p = PendingIntent.getService(this, action.hashCode(), i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            b.addAction(new Notification.Action.Builder(null, action, p).build());
        }
        return b.build();
    }
    @Override public int onStartCommand(Intent intent, int flags, int id) {
        startForeground(1, notification("Active"));
        if (executor == null) {
            executor = Executors.newSingleThreadScheduledExecutor();
            executor.scheduleWithFixedDelay(() -> {
                try { String status=RuntimeHost.tick(this); getSystemService(NotificationManager.class).notify(1, notification(status)); }
                catch (Exception e) { getSystemService(NotificationManager.class).notify(1, notification("Waiting for recovery")); }
            }, 2, 15, TimeUnit.SECONDS);
        }
        if (intent != null && intent.getAction() != null) {
            final boolean paused = intent.getAction().equals("Pause");
            executor.execute(() -> { try {RuntimeHost.pause(this, paused);} catch(Exception ignored) {} });
        }
        MailWorker.schedule(this);
        return START_NOT_STICKY;
    }
    @Override public void onTimeout(int startId, int fgsType) { stopSelf(); }
    @Override public void onDestroy() { if(executor!=null) executor.shutdownNow(); super.onDestroy(); }
    @Override public IBinder onBind(Intent intent) { return null; }
}
