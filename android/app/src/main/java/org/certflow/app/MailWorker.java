package org.certflow.app;
import android.content.Context;
import androidx.work.*;
import java.util.concurrent.TimeUnit;

public class MailWorker extends Worker {
    public MailWorker(Context c, WorkerParameters p) { super(c, p); }
    @Override public Result doWork() {
        try { String status = RuntimeHost.tick(getApplicationContext()); return status.equals("retry_wait") ? Result.retry() : Result.success(); }
        catch (Exception e) { return Result.retry(); }
    }
    public static void schedule(Context c) {
        Constraints constraints = new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();
        PeriodicWorkRequest work = new PeriodicWorkRequest.Builder(MailWorker.class, 15, TimeUnit.MINUTES).setConstraints(constraints).build();
        WorkManager.getInstance(c).enqueueUniquePeriodicWork("certflow-recovery", ExistingPeriodicWorkPolicy.KEEP, work);
    }
}
