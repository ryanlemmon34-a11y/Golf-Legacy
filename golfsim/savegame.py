"""Simulation saves: the complete state of a running world, to resume exactly where it stopped.

This is the third kind of saved data (see archive.py): not a summary and not a history, but the whole
`Season` — people, staff and relationships, rankings, money, plans, fatigue, injuries, results so far,
course library and records — pickled. Loading it and carrying on produces exactly the same world as if
the simulation had never stopped (tested), so long runs can survive interruptions.

A save is tied to the engine version that wrote it: the file records the git commit, and loading a save
written by a different engine is refused unless `allow_other_engine=True` (old saves are for resuming,
not for reading history — use the archive for that).
"""
from __future__ import annotations

import gzip
import pickle
import subprocess
from pathlib import Path

FORMAT = 'golf-legacy-save/1'
ROOT = Path(__file__).resolve().parents[1]


def engine_commit():
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return 'unknown'


def save_simulation(season, path, note=''):
    """Write a resumable save. The worker pool is not saved; it restarts on demand."""
    path = Path(path)
    pool = season.__dict__.pop('_pool', None)
    try:
        meta = {'format': FORMAT, 'commit': engine_commit(), 'year': season.year, 'note': note}
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
        if not allow_other_engine and meta['commit'] != engine_commit():
            raise ValueError(f'save written by engine {meta["commit"]}, this is {engine_commit()}')
        season = pickle.load(f)
    return season, meta
