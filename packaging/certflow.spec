# Explicit allowlist: never bundle databases, uploads, mailer/certs, or participant data.
from pathlib import Path
import sys
root = Path(SPECPATH).parent
analysis = Analysis([str(root / 'desktop' / 'main.py')], pathex=[str(root)],
    datas=[(str(root / 'templates'), 'templates'), (str(root / 'static'), 'static')],
    hiddenimports=['app', 'local_runtime', 'local_worker', 'keyring.backends.Windows',
                   'keyring.backends.SecretService', 'pypdfium2'] + (['webview.platforms.qt', 'PySide6.QtWebEngineWidgets'] if sys.platform.startswith('linux') else []),
    excludes=['pytest', 'pandas', 'tkinter'])
pyz = PYZ(analysis.pure)
exe = EXE(pyz, analysis.scripts, [], exclude_binaries=True, name='CertFlow',
          console=False, icon=str(root / 'packaging' / 'certflow.ico'))
coll = COLLECT(exe, analysis.binaries, analysis.datas, name='CertFlow')
