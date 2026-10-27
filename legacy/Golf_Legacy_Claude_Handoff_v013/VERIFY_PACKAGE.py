"""Verify all non-generated files in this Golf Legacy handoff against SHA256_MANIFEST.txt."""
import hashlib
from pathlib import Path
root=Path(__file__).resolve().parent
checks=root/'SHA256_MANIFEST.txt'
if not checks.exists():
    raise SystemExit('No SHA256_MANIFEST.txt found')
fail=[]; count=0
for line in checks.read_text(encoding='utf-8').splitlines():
    if not line.strip() or line.startswith('#'):continue
    h, rel=line.split('  ',1)
    path=root/rel
    if not path.is_file():fail.append(rel+' [missing]');continue
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != h:fail.append(rel+' [hash mismatch]')
    count+=1
print(f'Verified {count} files; failures: {len(fail)}')
for item in fail:print('FAIL',item)
raise SystemExit(1 if fail else 0)
