CertFlow cross-platform testing release

Built from development commit `5adf65290470440f6ec1e5d312840623b2744b90`. Main has not been merged or changed.

### Downloads and signing

- **Android APK:** debug-signed and installable for testing. This is not production signing. Future APKs signed with a different key may require uninstalling this build; export important local data first.
- **Windows installer:** unsigned (no Authenticode publisher certificate). Windows may display an unknown-publisher warning.
- **Linux x86_64 archive:** native application bundle, without a publisher signature. Extract and launch the included CertFlow executable.
- **SHA256SUMS.txt:** integrity checksums for the attached binaries; these are not publisher signatures.

### Validation

The automated tests and Windows, Linux, and Android build jobs passed in [GitHub Actions run 45031984727](https://github.com/H3M4N1H/certflow/actions/runs/45031984727). These results do not establish that all device workflows work.

Please test template and CSV imports, mouse/touch text placement, layout save/reload, preview versus generated output, PDF/PNG/ZIP export, and restart recovery. Steps 5 and 6 share email configuration; Step 5 sends continuously, while Step 6 uses scheduled gaps and batch cooldowns. Use test recipients only for email tests.

Remaining checks include Android document-picker/export cancellation and lifecycle recovery, background notification Pause/Resume and network recovery, clean Windows installation and desktop file dialogs, and Android arm64/API 36 compatibility. Android does not guarantee exact background sending intervals. See [VALIDATION.md](https://github.com/H3M4N1H/certflow/blob/5adf65290470440f6ec1e5d312840623b2744b90/VALIDATION.md) for the full verification record and limitations.

This prerelease is for testing, not a production-signed distribution.
