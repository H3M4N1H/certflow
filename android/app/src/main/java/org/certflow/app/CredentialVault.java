package org.certflow.app;
import android.content.Context;
import android.security.keystore.*;
import android.util.Base64;
import java.security.KeyStore;
import javax.crypto.*;
import javax.crypto.spec.GCMParameterSpec;

public final class CredentialVault {
    private static Context context;
    public static void init(Context c){context=c.getApplicationContext();}
    private static SecretKey key() throws Exception {
        KeyStore ks=KeyStore.getInstance("AndroidKeyStore");ks.load(null);
        if(!ks.containsAlias("certflow-smtp")){
            KeyGenerator g=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");
            g.init(new KeyGenParameterSpec.Builder("certflow-smtp",KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());g.generateKey();
        }
        return ((KeyStore.SecretKeyEntry)ks.getEntry("certflow-smtp",null)).getSecretKey();
    }
    public static void put(String password) throws Exception {
        Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.ENCRYPT_MODE,key());
        String data=Base64.encodeToString(cipher.getIV(),Base64.NO_WRAP)+":"+Base64.encodeToString(cipher.doFinal(password.getBytes("UTF-8")),Base64.NO_WRAP);
        if(!context.getSharedPreferences("vault",0).edit().putString("smtp",data).commit())throw new Exception("Credential save failed");
    }
    public static String get() throws Exception {
        String data=context.getSharedPreferences("vault",0).getString("smtp",null);if(data==null)return "";
        String[] parts=data.split(":");Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.DECRYPT_MODE,key(),new GCMParameterSpec(128,Base64.decode(parts[0],Base64.NO_WRAP)));
        return new String(cipher.doFinal(Base64.decode(parts[1],Base64.NO_WRAP)),"UTF-8");
    }
    public static void clear(){context.getSharedPreferences("vault",0).edit().remove("smtp").commit();}
}
