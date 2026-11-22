# Validation and remaining release work

Development branch: `feat/local-apps-interactive-editor`
Review PR: https://github.com/H3M4N1H/certflow/pull/2

## Continuation verification (2026-11-22)

- Re-ran the host regressions in an isolated Python environment: all 16 Python tests
  passed, the JavaScript preview test passed, and all required Python modules compiled.
- Rechecked the protected worktree state: the pre-existing modified `certflow_users.db`
  and untracked `mailer/` directory were not changed or staged.
- The current local environment has no `adb` executable, so Android document-provider,
  notification, Doze, process-death, and device recovery tests could not be executed.
  A local `assembleDebug` retry also could not download Gradle 8.13 because the network
  connection timed out. The previously built debug APK remains at
  `android/app/build/outputs/apk/debug/app-debug.apk`.
- Final-head CI for commit `6eb1f6b` passed the test, Ubuntu desktop, and Android jobs;
  the Windows job was still pending when this verification was recorded. No platform
  gate is inferred from that pending status.

## Verified during implementation

- 16 Python regressions passed, using temporary databases and mocked SMTP.
- JavaScript preview regression passed.
- Chromium workflow passed at 1280px/1x, 720px/2x and 390px/3x: mouse and real touch
  events, original-image coordinate conversion, zoom, undo/redo, layout reload,
  CSV record switching, preview and ZIP generation. External requests were blocked.
- Pillow preview tiles matched generated PNG pixels at three font sizes and every
  alignment. Browser layer geometry no longer stretches small-scale text.
- Shared message tests proved that Steps 5 and 6 produce the same subject, body,
  sender and attachments for plain, certificate, ZIP and combined modes.
- Process-death regression verified OS lock release and persistent uncertain-delivery
  handling. Explicit SMTP 451 rejections remain retryable. Saved bulk payloads omit
  SMTP passwords. Manual pause, gaps, cooldowns and duplicate-worker blocking passed.
- Linux PyInstaller bundle built. Both `--self-test` and `--ui-self-test` passed,
  including the actual packaged pywebview/Qt window.
- Android debug APK built and APK signature verification passed. It installed on an
  Android 15/API 35 x86_64 emulator. Two instrumentation tests passed: embedded
  Flask/Pillow CSV/text/PNG/ZIP/PDF/SQLite and Keystore checks; local WebView/editor
  startup. No real SMTP was used.
- Starting the Android foreground session from its UI produced an active `dataSync`
  foreground service with a persistent notification containing two actions.
- Artifact scans found no known user databases, uploads, queued messages or signing
  keys in the Linux bundle and main Android APK.
- GitHub Actions run [45004519903](https://github.com/H3M4N1H/certflow/actions/runs/45004519903)
  passed tests and Windows, Linux and Android builds at `f3a73bb` (before the final
  Android inset/status-copy refinements). Windows CI built the Inno Setup installer
  and passed its packaged backend self-test. Check the latest PR run for final-head CI.

These checks are not a production-readiness certification. No real email was sent.
Windows GUI installation/use and physical Android hardware have not been verified.

## Remaining verification / release gates

1. End-to-end native document imports and exports on Android: PNG/JPG/CSV/ZIP import;
   save PDF, PNG/ZIP and layout JSON to several document providers; cancel the picker;
   rotate/background/terminate during selection or save. The document-picker and
   export bridge code is implemented, but a complete SAF save round trip was not verified.
2. Android notification Pause/Resume, network loss/reconnection, Doze, process kill,
   force-stop/reopen, and foreground-service timeout recovery. Use mocked/local test
   SMTP, never participant addresses. WorkManager timing remains OS-controlled.
3. Test Windows installation, native upload/download dialogs, keyring persistence and
   background checkbox behavior on a clean Windows machine. Test Linux on the Ubuntu
   baseline and with a locked/unavailable Secret Service keyring. Desktop background
   handoff on window close needs an end-to-end mock-SMTP test.
4. Run Android tests on arm64 hardware and Android 16/API 36, including 16 KB-page-size
   compatibility. The current emulator result is API 35/x86_64 only.
5. Production signing: supply the owner's Android signing identity and Windows
   Authenticode certificate through secure build configuration. Existing APKs are
   debug-signed testing builds; Windows installers are not Authenticode-signed.
6. Recheck Android native dependency security/support before release: available
   Chaquopy Pillow is 11.0.0, while web/desktop use the existing 11.1.0 pin. Do not silently
   claim latest native library security or universal Linux compatibility.

## Continuation prompt

Copy the following into a new Codex session if needed:

> Continue CertFlow in `/home/luffy/Projects/certflow`, branch
> `feat/local-apps-interactive-editor`, PR https://github.com/H3M4N1H/certflow/pull/2.
> Read `AGENTS.md`, `CROSS_PLATFORM.md`, and `VALIDATION.md` first. Do not rewrite or
> merge main. Preserve the pre-existing modified `certflow_users.db` and untracked
> `mailer/`; never stage them or include participant data in builds.
>
> The interactive editor, shared local Flask runtime, pywebview/PyInstaller desktop
> packaging, Chaquopy Android project, local scheduler, and build workflows are
> implemented. Crucially, Steps 5 and 6 must use the SAME recipients, SMTP settings,
> subject/body and attachments. Only dispatch differs: continuous versus the existing
> randomized gaps/batches/cooldowns. Preserve CSRF, validation, secure local credentials,
> SQLite checkpoints, manual pause and uncertain-delivery safeguards.
>
> Complete the six remaining verification/release gates in VALIDATION.md. Prioritize
> Android's native document-picker/export round trip and background recovery using
> mocked SMTP; then Windows clean installation and desktop background handoff. The
> Android instrumentation tests live in `android/app/src/androidTest`; run
> `./gradlew connectedDebugAndroidTest` on a dedicated emulator/device. Never send
> real participant email. Fix actual failures with targeted changes, rerun relevant
> tests, rebuild artifacts, and update VALIDATION.md and the existing PR. Confirm
> final-head GitHub Actions and provide artifact links. Do not claim untested hardware,
> long-running recovery, signing, or release publication has passed. Production keys
> must come from the owner through secure configuration; do not invent or commit keys.
