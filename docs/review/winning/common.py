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


class ArchiveError(RuntimeError):
    """The archive does not match its manifest: nothing is read (fail closed)."""


def archive_file(save, key):
    """The manifest's file for `key` ('world', 'people', 'relations', 'records'): never a glob, so a stale
    generation's file is never read. Missing -> ArchiveError."""
    save = Path(save)
    name = manifest(save)['files'].get(key)
    if not isinstance(name, str):
        raise ArchiveError(f'manifest names no {key} file')
    p = save / 'archive' / name
    if not p.is_file():
        raise ArchiveError(f'manifest file missing: {p}')
    return p


def year_files(save):
    """{year: path} of the archived seasons, exactly the files the manifest names (manifest['files']['years']),
    never a glob: a stale generation's file in the directory is ignored. Fails closed (ArchiveError) if the
    manifest's year list and file map disagree or a named file is missing."""
    save = Path(save)
    man = manifest(save)
    files = man['files']['years']
    if sorted(int(y) for y in files) != list(man['years']):
        raise ArchiveError('manifest year list and year files disagree')
    out = {}
    for y, name in files.items():
        p = save / 'archive' / name
        if not p.is_file():
            raise ArchiveError(f'manifest year file missing: {p}')
        out[int(y)] = p
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


def provenance(inputs=(), extra=None):
    """Binding metadata for an output: sha256 of every input file actually read and of every script in this
    directory, plus the git commit and whether the study directory had uncommitted changes."""
    return {'scripts_commit': git_head(), 'scripts_dirty': git_dirty(),
            'scripts_sha256': {p.name: sha256(p) for p in sorted(HERE.glob('*.py'))},
            'inputs_sha256': {str(Path(p).name): sha256(p) for p in inputs}, **(extra or {})}

