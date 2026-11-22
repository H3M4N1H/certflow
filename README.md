# certflow 📜

> Bulk certificate generator. Upload a template, add names, download a ZIP. Built for college events.

Made this because generating 200 individual certificates by hand was not happening. Used it for AKIRA CTF at Velammal Engineering College and CYVENTURA at the CSE Cyber Security dept. It works.

## How it works

1. Upload your certificate PNG template
2. Paste participant names + departments (one per line)
3. Add text layers, bind CSV columns, and drag/style them on the certificate
4. Preview → generate → download all as ZIP

## Bulk Certificate Editor

Open `/bulk-editor` to apply the same visual edit to existing PNG/JPG certificates:

1. Upload one sample certificate image
2. Draw one or more rectangular regions on the sample
3. Choose a cover color and optional replacement text for each region
4. Upload the certificate image batch as loose PNG/JPG files or a ZIP archive
5. Download the processed certificates as a ZIP

## Run

```bash
# Local
pip install -r requirements.txt
python app.py

# Docker
docker compose up
```

Open `http://localhost:5000`.

## API

```
POST /generate        → single certificate
POST /generate-batch  → bulk generation, returns ZIP
POST /bulk-editor/process → bulk image edits, returns ZIP
```

## Stack

- Python / Flask
- Pillow
- Docker

### Dynamic text and resumable email sending

Upload a CSV (or paste CSV data) in Step 2. Use the interactive editor in Step 3
to add independent text fields, choose CSV columns, and drag or resize them.
Manual X/Y inputs remain under Precise position. Save/reload layouts as JSON.

Configure email once in Step 5. Send continuously there, or prepare the same
messages in Step 6 for scheduled sending with randomized gaps and cooldowns.
Both modes preserve pause/resume and checkpoints. Uncertain delivery is held
for explicit review instead of blindly retrying.

See [Cross-platform applications and build guide](CROSS_PLATFORM.md) for desktop
packaging, local Android generation, background scheduling, signing, limits and tests.
