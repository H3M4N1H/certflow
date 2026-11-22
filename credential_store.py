"""OS-protected SMTP password storage for installed applications."""
import os


def set_password(password):
    if os.environ.get('CERTFLOW_ANDROID') == '1':
        from java import jclass
        jclass('org.certflow.app.CredentialVault').put(password)
    else:
        import keyring
        keyring.set_password('CertFlow', 'scheduled-smtp', password)


def get_password():
    if os.environ.get('CERTFLOW_ANDROID') == '1':
        from java import jclass
        return str(jclass('org.certflow.app.CredentialVault').get())
    import keyring
    return keyring.get_password('CertFlow', 'scheduled-smtp')


def clear_password():
    if os.environ.get('CERTFLOW_ANDROID') == '1':
        from java import jclass
        jclass('org.certflow.app.CredentialVault').clear()
    else:
        import keyring
        if keyring.get_password('CertFlow', 'scheduled-smtp') is not None:
            keyring.delete_password('CertFlow', 'scheduled-smtp')
