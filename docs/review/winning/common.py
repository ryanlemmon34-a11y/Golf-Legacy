"""Shared, read-only access to an archived world (the JSON history only: never the pickled checkpoint).

Every reader opens files read-only and streams one season at a time. Provenance: the sha256 of every archive
file read, the save's own metadata (world id, engine id, generation) and the git commit of these scripts.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CARDENAS = 19411


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(chunk), b''):
            h.update(b)
    return h.hexdigest()


def manifest(save):
    save = Path(save)
    return json.loads((save / 'archive' / 'MANIFEST.json').read_text())


def year_files(save):
    """{year: path} of the archived seasons (the manifest's generation)."""
    save = Path(save)
    man = manifest(save)
    out = {}
    for p in (save / 'archive' / 'years').glob('*.json.gz'):
        y = int(p.name.split('.')[0])
        out[y] = p
    assert sorted(out) == man['years'], 'archive years do not match the manifest'
    return dict(sorted(out.items()))


def load_year(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return json.load(f)


def load_json_gz(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return json.load(f)


def save_meta(save):
    save = Path(save)
    cur = json.loads((save / 'CURRENT').read_text())
    meta = json.loads((save / cur['dir'] / 'meta.json').read_text())
    return {'world_id': meta['world_id'], 'engine': meta['engine'], 'generation': meta['generation'],
            'cursor': meta['cursor'], 'state_sha256': meta['sha256'], 'calendar': meta.get('calendar')}


def git_head():
    try:
        return subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return 'unknown'


def git_dirty():
    try:
        out = subprocess.run(['git', '-C', str(ROOT), 'status', '--porcelain', '--', 'docs/review/winning'],
                             capture_output=True, text=True, check=True).stdout
        return bool(out.strip())
    except Exception:
        return None
