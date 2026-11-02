"""Shared fixture for the career tests: a small world (scale 0.05, seed 11) played to its first newcomer boundary,
and a digest of a world's state for all-AI equivalence checks.

The digest covers what the simulation decides: every golfer's status, tour, lifestyle, overall and attributes, money
and staff; every event's winner; the world ranking's top 100; the cursor. Not timings or caches.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SEED = 11
SCALE = 0.05
_CACHE = {}


def digest(session):
    s = session.season
    h = hashlib.sha256()
    for g in sorted(s.world.golfers, key=lambda g: g.id):
        c = s.staff.coach(g.id)
        k = s.staff.caddie(g.id)
        h.update(repr((g.id, g.name, g.status, g.tour, g.lifestyle, round(g.overall, 6),
                       tuple(round(v, 6) for _, v in sorted(g.attrs.items())), round(g.cash, 4), round(g.backing, 4),
                       c.id if c else None, k.id if k else None)).encode())
    for eid in sorted(s.results):
        h.update(repr((eid, s.results[eid].winner())).encode())
    year, week = session.cursor['year'], session.cursor['week']
    h.update(repr(s.ctx.ranking(year, max(1, week - 1))[:100]).encode())
    h.update(repr(sorted(session.cursor.items())).encode())
    return h.hexdigest()


def tmpdir(prefix='career_'):
    return Path(tempfile.mkdtemp(prefix=prefix, dir=os.environ.get('TMPDIR')))


def first_boundary():
    """A session directory holding the fixture world at its second season's 1 January (cursor 'start'): the
    first junior class (the newcomers of the second season) exists. Built once per process and copied."""
    if 'boundary' not in _CACHE:
        from golfsim.population import generate_world
        from golfsim.session import Session
        d = tmpdir('career_fixture_')
        s = Session.create(d / 'w', seed=SEED, world=generate_world(year=2027, seed=SEED, scale=SCALE), workers=1)
        s.advance(52)
        s.close()
        _CACHE['boundary'] = d / 'w'
    return _CACHE['boundary']


def copy_of(src):
    d = tmpdir() / 'w'
    shutil.copytree(src, d)
    return d
