# CertFlow installed applications

This development branch upgrades the existing Flask application. The hosted web routes,
login, CSRF checks, bulk image editor, CSV parsing, generation, and both sending modes
remain available. No hosted server is required by the installed applications.

## Designing certificates

Upload a PNG/JPG template and CSV, then use **Add text**. Choose a CSV column or static
text in the properties panel. Drag a layer, drag its corner to resize, or use arrow keys
(Shift = 10 pixels). Select layers to duplicate/delete or change font, weight, color,
alignment, and content. Use Fit/zoom and scroll the canvas to pan. Undo/redo covers field
changes. Precise X/Y inputs are under **Precise position**.

**Save layout** exports a version 2 JSON file without participant data or credentials.
**Open layout** validates and restores it; load a template of the original dimensions
and a CSV with the same column order. Layouts refer to CSV columns by index; column labels
are saved for reference. The record selector previews actual rows. Layout files do not
include the image itself.

Positions are integers in original-image pixels. X is the left/center/right alignment
anchor; Y is the top of visible text. Text previews and exports use the same Pillow
rasterization and bundled Noto fonts (license in `static/fonts/LICENSE`). Viewport size,
scroll, zoom, and device pixel ratio do not change stored coordinates. Existing API
fields without `Anchor: top` retain their old Pillow positioning convention.

ZIP generation renders one image at a time and uses unique indexed filenames. Merged
PDFs have a 100-million-total-pixel limit to avoid retaining unbounded page images;
choose individual PDFs in ZIP for larger jobs. Request, CSV, image and ZIP limits remain
in force. Large encoded output archives still use memory; split very large batches.

## One email configuration, two dispatch modes

Set recipients, SMTP credentials, sender name, subject/body placeholders, certificate
format and optional ZIP attachments in Steps 1–5. Both modes call the same validated
message builder, including all custom CSV columns and attachment combinations.

- **Step 5:** sends continuously, with progress, pause/resume and per-row checkpoints.
  Reopening the app offers the latest unfinished bulk job. Re-enter its SMTP password;
  passwords are excluded from the saved bulk payload. Resume uses the saved message
  configuration, rather than newly edited fields.
- **Step 6:** **Prepare scheduled emails from Step 5** creates the same messages as
  durable `.eml` files and starts the queue paused. Resume enables delivery. It preserves
  3–5 minute base gaps ±30% jitter, batches of 15–20 and 15–25 minute base cooldowns ±30%
  jitter. A hosted cron call to `/mailer/send-next?secret=...` remains supported.
  Installed apps use the same scheduler logic without external cron.

Preparing a queue replaces the existing scheduled queue. Editing Step 5 afterward does
not silently modify messages already queued. Pause completes the current SMTP operation
before stopping. Recipient acknowledgement and the next gap/cooldown are committed in
one SQLite transaction. OS-owned locks prevent concurrent workers for a queue or bulk
job; locks are released by the OS after process death.

A lost SMTP acknowledgement cannot be distinguished from accepted delivery. These
recipients become **uncertain**, and automatic retries stop. Check the sender's sent
mail and delivery records, then explicitly mark delivered or retry (which may duplicate).
Definite temporary SMTP rejections and connection failures remain retryable. This is not
an exactly-once delivery guarantee. Throttling also does not guarantee provider quota
compliance.

Old `/mailer/load-queue` and credential routes remain for API compatibility; the UI
no longer requires a separate SMTP form or recipient file for Step 6.

## Desktop

`desktop/main.py` launches Flask on `127.0.0.1` with an OS-assigned port, then opens
pywebview. A per-launch capability bootstraps an authenticated local session. Requests
must use the exact loopback host/port and local session; unsafe requests also require
CSRF. Proxy headers are not trusted locally. The capability is excluded from request
logs. OS account access controls protect the installed application; hosted login remains
unchanged.

Data uses `platformdirs.user_data_dir('CertFlow', 'CertFlow')`, not the installation
folder. SMTP passwords use Windows Credential Manager or the Linux Secret Service
keyring. If the keyring is unavailable/locked, scheduling fails with a visible message
instead of writing a plaintext password. Hosted credential storage retains its existing
SQLite behavior. Native WebView upload/download dialogs handle file selection.

The desktop checkbox **Continue scheduled email after closing this window** starts a
single detached scheduler when the window closes. It lasts until logout, shutdown or
until the preference is disabled. Pause/resume stays persistent. It is not an autostart
system service. Reopening can coexist safely with that worker. Bulk sends remain an
active-window workflow; interrupted bulk sends can be resumed from their checkpoint.

Build prerequisites: Python 3.11, platform build tools, network access for dependencies.

```sh
python -m venv .venv
# Activate the virtual environment for your OS
pip install -r requirements-desktop.txt
pyinstaller --noconfirm packaging/certflow.spec
# Developer smoke check with an isolated writable directory:
dist/CertFlow/CertFlow --self-test --data-dir /tmp/certflow-smoke
```

Build on each target OS; PyInstaller does not cross-compile. `dist/CertFlow` contains the
executable and bundled Python, fonts, templates, Qt web engine and libraries. Keep the
whole directory together. Windows and Linux both bundle the Qt web engine through pywebview; no separate
WebView2 installation is required. Inno Setup 6 compiles
`packaging/certflow.iss` into a per-user Windows installer. Production Windows signing
requires your own Authenticode certificate and timestamp service; none is included.

Linux CI builds on Ubuntu 22.04 and produces a portable directory in a `.tar.gz`.
Extract and launch `CertFlow` using the desktop file manager. This distribution needs a
compatible Linux display environment/system libraries; it is not a universal AppImage.
The local Arch build requires its newer system ABI and is only a local testing artifact.
Linux keyring support requires an unlocked Secret Service implementation.

## Android

The Gradle project embeds Python 3.11 using Chaquopy 17.2 and runs the shared Flask app
on private loopback inside the app process. It is not a wrapper around a hosted website.
The shared frontend, Pillow engine, SQLite queue, fonts and templates are bundled.
Only explicit source/resource allowlists are copied into the APK.

- Android 7/API 24 minimum; target/compile API 36; arm64-v8a and x86_64.
- Build with JDK 17, Python 3.11, Android SDK 36 and Gradle wrapper 8.13.
- Chaquopy's available Android Pillow wheel is 11.0.0, rather than desktop/web 11.1.0.
  Recheck native-wheel availability/security updates before a production release.
- Template/CSV/ZIP imports use `ACTION_OPEN_DOCUMENT`. Exports stream from the private
  runtime to a document URI selected with `ACTION_CREATE_DOCUMENT`; no broad storage
  permission is requested. PNG/JPG templates and PDF/PNG/ZIP exports use local code.
  PDF-template import is supported on web/desktop, but not Android in this version.
- SMTP credentials are AES-GCM encrypted with an Android Keystore key. App backups are
  disabled. No signing secrets or participant data are packaged.
- WorkManager performs network-constrained recovery with a 15-minute periodic minimum.
  The user can start an active `dataSync` foreground session from **Background mail
  options**. Its notification has Pause/Resume. Timeout stops the service and leaves
  persistent progress for eligible recovery work. No boot-time foreground service or
  battery-policy bypass is used.
- Android may delay/stop background delivery. Android 15+ also limits `dataSync`
  foreground-service time. There is **no guarantee** of uninterrupted 3–5 minute sends.
  Force-stop requires the user to reopen the app. Bulk sends require the visible page;
  process death preserves the saved job and marks interrupted SMTP delivery uncertain.

```sh
cd android
./gradlew assembleDebug
# APK: app/build/outputs/apk/debug/app-debug.apk
./gradlew assembleRelease
```

Debug APKs are installable testing builds, signed with a developer/debug key. Release
builds are unsigned unless `ANDROID_KEYSTORE`, `ANDROID_STORE_PASSWORD`,
`ANDROID_KEY_ALIAS`, and `ANDROID_KEY_PASSWORD` are supplied. Store these only in secure
CI secrets or your local build environment. Preserve your production signing identity
for upgrades. Hardware/WebView, document-provider, notification, background/Doze and
process-death tests are required on real Android devices before production distribution.

## CI and release artifacts

`.github/workflows/build.yml` runs Python, JavaScript and browser regressions, builds
Windows and Linux independently, and builds the Android debug APK. Build outputs are
uploaded as Actions artifacts. `v*` tags create a **draft** release with those artifacts;
production signing and device verification are release gates, not implied successes.

The PyInstaller spec and Android staging tasks exclude databases, uploads, generated
certificates, the existing untracked standalone `mailer/`, credentials and signing keys.
The existing modified `certflow_users.db` is intentionally not part of this change.

## Validation commands

```sh
python -m py_compile app.py generate_certs.py process_certificates.py local_runtime.py local_worker.py
python -m unittest discover -s tests -p 'test_*.py'
node --test tests/test_preview.cjs
pip install playwright
python -m playwright install chromium
python tests/browser_editor.py
```

Tests use temporary databases and mocked SMTP. Browser tests exercise desktop/mobile
sizes, mouse/touch dragging, zoom, layout round trips, CSV record switching, previews
and downloads. Rendering tests compare Pillow preview tiles against exported pixels.

Reference constraints: [Chaquopy versions](https://chaquo.com/chaquopy/doc/current/versions.html),
[WorkManager requests](https://developer.android.com/develop/background-work/background-tasks/persistent/getting-started/define-work),
[foreground-service timeouts](https://developer.android.com/develop/background-work/services/fgs/timeout),
[pywebview API](https://pywebview.flowrl.com/api/).
