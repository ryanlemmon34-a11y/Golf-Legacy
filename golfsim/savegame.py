"""Simulation saves: the complete state of a running world, to resume exactly where it stopped.

This is the third kind of saved data (see archive.py): not a summary and not a history, but the whole
`Season` — people, staff and relationships, rankings, money, plans, fatigue, injuries, results so far,
course library and records — pickled. Loading it and carrying on produces exactly the same world as if
the simulation had never stopped (tested), so long runs can survive interruptions.

A save is tied to the engine version that wrote it: the file records the git commit and the engine's
identity (a fingerprint of the simulation code, so commits that only touch tools, docs or the
persistence modules do not change it), and loading a save written by a different engine is refused unless `allow_other_engine=True` (old saves are for resuming,
not for reading history — use the archive for that).
"""
from __future__ import annotations

import gzip
import pickle
import subprocess
from pathlib import Path

FORMAT = 'golf-legacy-save/1'
ROOT = Path(__file__).resolve().parents[1]


def _git(*args):
    try:
        return subprocess.check_output(['git', *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return 'unknown'


def engine_commit():
    return _git('rev-parse', 'HEAD')


PERSISTENCE = ('golfsim/savegame.py', 'golfsim/archive.py', 'golfsim/session.py')   # how worlds are stored, not how they play


def _files_engine_id():
    """The same fingerprint computed from the files themselves (git's blob hash of each), for a source copy
    without git metadata (an exported tarball): identical to engine_id() of the commit it was taken from."""
    import hashlib
    lines = []
    for p in sorted((ROOT / 'golfsim').rglob('*.py')):
        rel = p.relative_to(ROOT).as_posix()
        if rel in PERSISTENCE or '__pycache__' in rel:
            continue
        data = p.read_bytes()
        blob = hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()
        lines.append((f'100644 blob {blob}\t{rel}', f'{blob}\t{rel}'))
    if not lines:
        return 'unknown'
    return hashlib.sha1('\n'.join(b for _, b in sorted(lines)).encode()).hexdigest()


def engine_id(commit='HEAD'):
    """The engine's identity: a fingerprint of the simulation code in the golfsim package at a commit
    (every file's git blob except the persistence modules), so commits that only touch tools, docs or
    the save/archive code do not change it; '+dirty' when that code has uncommitted edits."""
    import hashlib
    listing = _git('ls-tree', '-r', commit, '--', 'golfsim')
    if listing == 'unknown':
        return _files_engine_id() if commit == 'HEAD' else 'unknown'
    lines = sorted(l for l in listing.splitlines() if l.endswith('.py') and l.split('\t')[1] not in PERSISTENCE)
    fid = hashlib.sha1('\n'.join(l.split(None, 2)[2] for l in lines).encode()).hexdigest()
    if commit == 'HEAD':
        changed = [l.split(maxsplit=1)[1] for l in _git('status', '--porcelain', '--', 'golfsim').splitlines() if l.strip()]
        if any(f.endswith('.py') and f not in PERSISTENCE for f in changed):
            fid += '+dirty'
    return fid


def save_simulation(season, path, note=''):
    """Write a resumable save. The worker pool is not saved; it restarts on demand."""
    path = Path(path)
    pool = season.__dict__.pop('_pool', None)
    try:
        meta = {'format': FORMAT, 'commit': engine_commit(), 'engine': engine_id(), 'year': season.year, 'note': note}
        tmp = path.with_suffix(path.suffix + '.tmp')
        with gzip.open(tmp, 'wb') as f:
            pickle.dump(meta, f, protocol=pickle.HIGHEST_PROTOCOL)
            pickle.dump(season, f, protocol=pickle.HIGHEST_PROTOCOL)
        tmp.replace(path)
    finally:
        if pool is not None:
            season._pool = pool
    return meta


def load_simulation(path, allow_other_engine=False):
    """(season, meta) from a save written by save_simulation."""
    with gzip.open(path, 'rb') as f:
        meta = pickle.load(f)
        if meta.get('format') != FORMAT:
            raise ValueError(f'not a Golf Legacy simulation save: {meta.get("format")}')
        saved = meta.get('engine') or engine_id(meta['commit'])
        if not allow_other_engine and saved != engine_id():
            raise ValueError(f'save written by engine {saved} (commit {meta["commit"]}), this engine is {engine_id()}')
        season = pickle.load(f)
    return season, meta
