"""Reject application runtime data in release artifacts; no secret values are read."""
import argparse
import zipfile
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('artifact', type=Path)
args = parser.parse_args()
paths = (list(args.artifact.rglob('*')) if args.artifact.is_dir()
         else [Path(name) for name in zipfile.ZipFile(args.artifact).namelist()])
bad = []
for path in paths:
    if path.name in ('certflow_users.db', 'certflow.db', 'session.key', 'recipients.json', '.env'):
        bad.append(str(path))
    elif path.suffix in ('.eml', '.jks', '.keystore', '.xlsx', '.ods'):
        bad.append(str(path))
    elif any(part in ('output_certs', 'uploads') for part in path.parts):
        bad.append(str(path))
if bad:
    raise SystemExit('Private/runtime files found in artifact:\n' + '\n'.join(bad))
print('PASS release artifact contains no known application runtime data or signing keys')
