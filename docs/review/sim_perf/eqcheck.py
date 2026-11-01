"""Compare two worlds after the same skip: the saved simulation state (decompressed pickle bytes) and every
published history file (decoded JSON). Equal means the same world and the same history; differences in file
encoding (compression, gzip members) are reported apart and do not count as differences.

    python eqcheck.py WORLD_A WORLD_B
"""
import gzip
import hashlib
import json
import sys
from pathlib import Path


def gen_dir(d):
    cur = json.loads((Path(d) / 'CURRENT').read_text())
    return Path(d) / cur['dir']


def state_digest(d):
    h = hashlib.sha256()
    n = 0
    with gzip.open(gen_dir(d) / 'state.pkl.gz', 'rb') as f:
        while True:
            b = f.read(1 << 22)
            if not b:
                break
            h.update(b)
            n += len(b)
    return h.hexdigest(), n


def history(d):
    a = Path(d) / 'archive'
    m = json.loads((a / 'MANIFEST.json').read_text()) if (a / 'MANIFEST.json').exists() else None
    out = {}
    files = m['files'] if m and 'files' in m else None
    for p in sorted(a.rglob('*.json.gz')) + sorted(a.rglob('*.json')):
        if p.name in ('MANIFEST.json',):
            continue
        rel = p.relative_to(a).as_posix()
        out[rel] = p
    return out, m


def load(p):
    if p.suffix == '.gz':
        with gzip.open(p, 'rt') as f:
            return json.load(f)
    return json.loads(p.read_text())


def logical(rel):
    """years/2077.g000051.json.gz -> years/2077.json.gz (generation tags name the producing generation)."""
    import re
    return re.sub(r'\.g\d{6}(\.json)', r'\1', rel)


def main(a, b):
    ok = True
    da, db = state_digest(a), state_digest(b)
    print('state pickle:', 'IDENTICAL' if da == db else 'DIFFERENT', da[1], db[1])
    ok &= da == db
    ha, ma = history(a)
    hb, mb = history(b)
    la = {logical(k): v for k, v in ha.items()}
    lb = {logical(k): v for k, v in hb.items()}
    if set(la) != set(lb):
        print('history files differ:', sorted(set(la) ^ set(lb)))
        ok = False
    enc = 0
    for k in sorted(set(la) & set(lb)):
        x, y = load(la[k]), load(lb[k])
        if k.endswith('world.json'):
            for v in (x, y):
                v.pop('written', None)
        if x != y:
            print('history DIFFERENT:', k)
            ok = False
        elif la[k].read_bytes() != lb[k].read_bytes():
            enc += 1
    print(f'history files: {len(la)} compared; {enc} differ only in encoding')
    print('EQUIVALENT' if ok else 'NOT EQUIVALENT')
    return ok


if __name__ == '__main__':
    sys.exit(0 if main(sys.argv[1], sys.argv[2]) else 1)
