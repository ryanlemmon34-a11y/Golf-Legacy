"""Reconstruct each layout's lowest tournament totals from an archive's evidence (read-only).

    python tools/reconstruct_totals.py ARCHIVE [--engine-commit 7334ffe] [--out report.md]

Worlds simulated before tournament totals were recorded have none in their records table. This rebuilds
them from what the archive keeps: every edition's sites (course and layout) and every finisher's total,
which the engine gives only to a golfer who played every round (a missed cut has none; match play has
none). What the archive does not always keep is an edition's length: editions archived since the
format was recorded carry `rounds` and `match_play` (basis "recorded": exact). Older ones take the
series' length from the engine's calendar -- the standard course library's, which worlds play unless
given another (basis "calendar"): exact only if the calendar the world was played with is this one,
which `--engine-commit` checks (golfsim/calendar.py at that commit against
this one; "unverified" otherwise). Nothing is written to the world: the report says which totals are
exact and which are not, and nothing is invented.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim.archive import Archive                                   # noqa: E402


def calendar_unchanged_since(commit):
    """Whether golfsim/calendar.py at `commit` is this one (None: cannot tell, e.g. no git)."""
    try:
        then = subprocess.check_output(['git', 'show', f'{commit}:golfsim/calendar.py'], cwd=ROOT)
    except Exception:
        return None
    return then == (ROOT / 'golfsim' / 'calendar.py').read_bytes()


def reconstruct(a, calendar=None):
    """{'layouts': {layout id: {holes: mark}}, 'basis': {basis: seasons}, 'since': first season}. Marks
    are dicts like the records table's (score, to_par, golfer, golfer_id, event_id, year, week, tier); the
    first to post a total holds it, in the order the archive keeps the editions."""
    lengths = None
    best, basis = {}, Counter()
    for y in a.years:
        season_basis = 'recorded'
        for e in a.year(y)['events']:
            if 'rounds' in e:
                rounds, match_play = e['rounds'], e['match_play']
            else:
                if lengths is None:                      # worlds play the standard library's calendar
                    from golfsim.course_library import default_library
                    cal = calendar or default_library().calendar
                    lengths = {s.series_id: (s.rounds, bool(s.match_play)) for s in cal.series}
                if e['series'] not in lengths:
                    season_basis = 'missing'
                    continue
                rounds, match_play = lengths[e['series']]
                season_basis = 'calendar' if season_basis == 'recorded' else season_basis
            if match_play or not rounds or rounds < 2:   # (one round is a round: the course record)
                continue
            for site, (course, layout, _) in enumerate(e['sites']):
                if site >= len(e['finish']):
                    continue
                par = a.world['courses'][course]['layouts'][layout]['par'] * rounds
                lid, holes = f'{course}:{layout}', rounds * 18
                for gid, pos, total in e['finish'][site]:
                    if total is None:
                        continue
                    cur = best.get((lid, holes))
                    if cur is None or total < cur['score']:
                        person = a.people.get(gid, {})
                        best[(lid, holes)] = {'score': total, 'to_par': total - par, 'golfer': person.get('name'),
                                              'golfer_id': gid, 'event_id': e['id'], 'year': y, 'week': e['week'],
                                              'tier': e.get('tier')}
        basis[season_basis] += 1
    layouts = {}
    for (lid, holes), m in best.items():
        layouts.setdefault(lid, {})[holes] = m
    return {'layouts': layouts, 'basis': dict(basis), 'since': a.years[0] if a.years else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('archive')
    ap.add_argument('--engine-commit', help='the engine the world was simulated with (checks the calendar)')
    ap.add_argument('--out', help='write the report here (default: print it)')
    args = ap.parse_args()
    with Archive(args.archive) as a:
        r = reconstruct(a)
        recorded_now = sum(len(v.get('lowest_totals') or {}) for v in a.records.values())
    same = calendar_unchanged_since(args.engine_commit) if args.engine_commit else None
    exact_calendar = 'exact (calendar unchanged since that engine)' if same else \
        'UNVERIFIED (calendar changed or engine unknown)' if args.engine_commit else 'unverified (no --engine-commit)'
    lines = ['# Lowest tournament totals, reconstructed from the archive', '',
             f'Seasons {a.years[0]}–{a.years[-1]}; by basis: ' + ', '.join(f'{k} {v}' for k, v in sorted(r['basis'].items()))
             + f'. Seasons on the "calendar" basis: {exact_calendar}. Totals in the records table now: {recorded_now}.', '',
             '| Layout | Holes | Total | To par | Golfer | Edition |', '|---|---|---|---|---|---|']
    for lid in sorted(r['layouts']):
        for holes, m in sorted(r['layouts'][lid].items()):
            lines.append(f'| {lid} | {holes} | {m["score"]} | {m["to_par"]:+d} | {m["golfer"]} (#{m["golfer_id"]}) | {m["event_id"]} |')
    text = '\n'.join(lines) + '\n'
    if args.out:
        Path(args.out).write_text(text)
        print('wrote', args.out)
    else:
        print(text)


if __name__ == '__main__':
    main()
