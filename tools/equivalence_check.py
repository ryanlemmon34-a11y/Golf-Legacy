"""Advance a copy of a saved world and digest everything the simulation changes, part by part, so a
performance-only change can be shown to leave the world exactly as it was.

    python tools/equivalence_check.py --world <session dir> --weeks 8 --workers 4 --out digest.json

Copy this file into another checkout to run the same check with that code. Parts digested: every event
result (finishes and totals per site, playoffs, teams), per-golfer performance statistics, rounds and
holes played, development (attributes, ceilings), course familiarity of golfers and caddies, finances
(cash, family money, backers' money, every ledger), staff (relationships with their work and duration,
caddies' and coaches' work and earnings), fatigue and injuries, rankings, course records (with totals),
moments, the history log, and -- when a season ended -- the published history. Also counts what the window
covered: match-play events, playoffs, missed cuts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def digest(x):
    return hashlib.sha256(repr(x).encode()).hexdigest()[:16]


def canon(x):
    """A deterministic, comparable form (dict order removed; objects by their fields)."""
    if isinstance(x, dict):
        return tuple(sorted((repr(k), canon(v)) for k, v in x.items()))
    if isinstance(x, (list, tuple)):
        return tuple(canon(v) for v in x)
    if isinstance(x, set):
        return tuple(sorted(repr(v) for v in x))
    if hasattr(x, '__dict__') and not isinstance(x, type):
        return (type(x).__name__, canon(vars(x)))
    if hasattr(x, '__dataclass_fields__'):
        return (type(x).__name__, canon({k: getattr(x, k) for k in x.__dataclass_fields__}))
    slots = getattr(type(x), '__slots__', None)
    if slots:
        return (type(x).__name__, canon({k: getattr(x, k, None) for k in slots}))
    if type(x).__repr__ is object.__repr__:
        raise TypeError(f'no deterministic form for {type(x).__name__}')   # (its repr has an address)
    return x


def parts(s, session_dir):
    season = s.season
    gs = sorted(season.world.golfers, key=lambda g: g.id)
    st = season.staff
    out = {
        'results': [(eid, r.finish, r.playoff, sorted(r.team.items())) for eid, r in sorted(season.results.items())],
        'performance': canon(season.pstats),
        'rounds_and_holes': (canon(season.season_rounds), canon(season.holes_played), canon(season.week_rounds)),
        'development': [(g.id, sorted(g.attrs.items()), sorted(g.ceilings.items())) for g in gs],
        'familiarity': ([(g.id, sorted(g.familiarity.items())) for g in gs],
                        [(k.id, sorted(k.familiarity.items())) for k in sorted(st.caddies.values(), key=lambda k: k.id)]),
        'finances': ([(g.id, g.cash, g.backing, g.backer_funds) for g in gs], canon(season.ledgers)),
        'staff': (canon(st.rel.export()),
                  [(k.id, k.rounds_worked, k.weeks_worked, round(k.earnings, 6)) for k in sorted(st.caddies.values(), key=lambda k: k.id)],
                  [(c.id, round(getattr(c, 'earnings', 0.0), 6)) for c in sorted(st.coaches.values(), key=lambda c: c.id)],
                  sorted(st.coach_of.items()), sorted(st.caddie_of.items())),
        'fatigue_injuries': (sorted(season.fatigue.items()), sorted(season.injured.items()), canon(season.injuries)),
        'rankings': (sorted(season.wr_pos.items()), sorted(season.am_pos.items())),
        'records': canon(season.records.to_dict()),
        'moments': canon(season.moments),
        'history': canon(season.history),
        'cursor': s.cursor,
    }
    a = Path(session_dir) / 'archive'
    m = a / 'MANIFEST.json'
    if m.exists():
        from golfsim.archive import _read, read_manifest
        man = read_manifest(a)
        seasons = {y: _read(a / f) for y, f in man['files']['years'].items()}
        # development evidence is observation only (nothing reads it back): digested on its own, so a change that
        # adds or extends it can still be shown to leave every outcome as it was
        out['diagnostics'] = {y: digest(canon(d.pop('diagnostics', None))) for y, d in seasons.items()}
        out['published'] = (man['years'], {y: digest(canon(d)) for y, d in seasons.items()},
                            {k: digest(canon(_read(a / f) if f.endswith('.gz') else json.loads((a / f).read_text())))
                             for k, f in man['files'].items() if k != 'years'})
    return {k: digest(v) for k, v in out.items()}


def coverage(season, before):
    new = [r for eid, r in season.results.items() if eid not in before]
    match = sum(1 for r in new if season.cal.by_id[r.series_id].match_play)
    playoffs = sum(1 for r in new if r.playoff)
    missed = sum(1 for r in new for site in r.finish for _, pos, total in site if pos is None and total is None)
    return {'events': len(new), 'match_play': match, 'playoffs': playoffs, 'missed_cuts': missed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--world', required=True, help='a saved session directory (copied; never changed)')
    ap.add_argument('--weeks', type=int, default=8)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    from golfsim.session import Session
    tmp = Path(tempfile.mkdtemp())
    try:
        d = tmp / 'world'
        shutil.copytree(a.world, d)
        s = Session.open(d, workers=a.workers, allow_other_engine=True)
        before = set(s.season.results)
        t = time.perf_counter()
        s.advance(a.weeks)
        el = time.perf_counter() - t
        out = {'weeks': a.weeks, 'seconds': round(el, 1), 'coverage': coverage(s.season, before), 'parts': parts(s, d)}
        s.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
