"""Explore a history archive from the command line (a debug view, until profile screens exist).

    python tools/history_query.py ARCHIVE person 1234       # playing and staff careers of one person
    python tools/history_query.py ARCHIVE find "Sam Rogers" # person ids with that name
    python tools/history_query.py ARCHIVE staff 1234        # golfer -> everyone who coached/caddied
    python tools/history_query.py ARCHIVE clients 1234      # coach/caddie -> clients and results in each stint
    python tools/history_query.py ARCHIVE course georgia-national-golf-club
    python tools/history_query.py ARCHIVE recap 2029
    python tools/history_query.py ARCHIVE examples          # finds real linked histories to show
    python tools/history_query.py ARCHIVE boards            # the records and frivolities lists
    python tools/history_query.py ARCHIVE board most-majors # one list, with its evidence

Everything is read from the archive's facts (ids, dated stints, the team recorded with each result).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim.archive import Archive                                   # noqa: E402


def when(t):
    return f'{t[0]} wk {t[1]}' if t else 'now'


def person(a, pid):
    p = a.people[pid]
    out = [f'{a.name(pid)} — person #{pid}, born {p["born"]}, roles: {", ".join(a.roles(pid))}']
    career = a.playing_career(pid)
    if career:
        out.append('  Playing career:')
        for y, r in career:
            out.append(f'    {y}: {r["status"]}/{r["lifestyle"]} on {r["tour"] or "—"}: {r["events"]} events, '
                       f'{r["wins"]} wins, ${r["prize"]:,} prize, world rank {r["wr_end"] or "—"}'
                       + (f' — no starts: {r["zero_start_reason"]}' if r.get('zero_start_reason') else ''))
    for role in ('coach', 'caddie'):
        if role in p:
            info = p[role]
            out.append(f'  {role.title()} career ({info["background"]}, now {info["status"]}, '
                       f'earned ${info["earnings"]:,}):')
            out += [f'    {y}: {t}' for y, t in info['history']]
            for c in a.staff_clients(pid, role):
                s = c['stint']
                out.append(f'    {when(s.start)} → {when(s.end)}: {a.name(s.golfer)} ({s.arrangement}); '
                           f'{c["starts"]} starts together, {len(c["wins"])} wins'
                           + (f' incl. majors {c["majors"]}' if c['majors'] else '')
                           + (f'; ended: {s.reason_end} ({s.ended_by})' if s.end else ''))
    return out


def staff(a, pid):
    out = [f'People around {a.name(pid)}:']
    for s in a.golfer_staff(pid):
        who = a.name(s.staff) if s.staff else s.arrangement
        out.append(f'  {s.kind:7s} {when(s.start)} → {when(s.end)}: {who} ({s.arrangement}, started by {s.started_by}'
                   + (f'; ended: {s.reason_end} by {s.ended_by}' if s.end else '') + f'; worked {s.work:.0f})')
    wins = [r for r in a.results(pid) if r['pos'] == 1]
    for r in wins:
        out.append(f'  Won {r["event"]}: coach {a.name(r["coach"]) if r["coach"] else "none"}, '
                   f'caddie {a.name(r["caddie"]) if r["caddie"] else "own bag"}')
    return out


def clients(a, pid):
    out = [f'Clients of {a.name(pid)}:']
    for c in a.staff_clients(pid):
        s = c['stint']
        out.append(f'  {s.kind} {when(s.start)} → {when(s.end)}: {a.name(s.golfer)}: {c["starts"]} starts, '
                   f'wins {c["wins"] or "none"}' + (f'; ended: {s.reason_end}' if s.end else ''))
    return out


def course(a, cid):
    d = a.course(cid)
    out = [f'{d["course"]["name"]} ({d["course"]["city"]}), {len(d["editions"])} editions:']
    for e in d['editions'][:12]:
        out.append(f'  {e["event"]} ({e["layout"]}): winner {a.name(e["winner"]) if e["winner"] else "—"}')
    for lid, r in d['records'].items():
        cr = r['course_record']
        if cr:
            out.append(f'  {lid} record {cr["score"]} by {a.name(cr["golfer_id"])} (#{cr["golfer_id"]}) in {cr["event_id"]}')
    return out


def recap(a, y):
    return [f'{y}:'] + [f'  - {f["text"]}' for f in a.recap(y)]


def examples(a):
    """Real linked histories from this archive (found, never forced)."""
    out = []
    former = [pid for pid, p in a.people.items() if 'golfer' in p and ('coach' in p or 'caddie' in p)]
    worked = [pid for pid in former if a.rel.of_staff(pid)]
    out.append(f'{len(former)} former players joined the staff; {len(worked)} have worked with players since.')
    for pid in worked[:2]:
        out += [''] + person(a, pid)
    winners = [(y, e) for y, e in a.events() if a.world['series'][e['series']]['kind'] == 'major']
    for y, e in winners[-2:]:
        w = next((g for g, p, _ in e['finish'][0] if p == 1), None)
        if w:
            out += [''] + staff(a, w)
    multi = [g for g, ids in a.rel.by_golfer.items()
             if len({a.rel.stints[i].staff for i in ids if a.rel.stints[i].kind == 'coach'}) >= 2]
    if multi:
        out += ['', f'{len(multi)} golfers have had two or more coaches; e.g.:'] + staff(a, multi[0])
    reunions = [k for k in a.rel.pairs if sum(1 for i in a.rel.by_golfer.get(k[2], ())
                                              if a.rel.stints[i].staff == k[1] and a.rel.stints[i].kind == k[0]) > 1]
    out.append(f'\nPairs that split and reunited: {len(reunions)}.')
    busiest = max((pid for pid, p in a.people.items() if 'coach' in p), key=lambda p: len(a.rel.of_staff(p, 'coach')),
                  default=None)
    if busiest:
        out += [''] + clients(a, busiest)
    if a.years:
        out += [''] + recap(a, a.years[-1])
    return out


def boards(a):
    from golfsim.history_stats import BOARDS
    return [f'{k:30s} {t}' for k, (t, _, _) in BOARDS.items()]


def one_board(a, name):
    from golfsim.history_stats import HistoryStats, board
    title, rows = board(HistoryStats(a), name, n=20)
    out = [title, '(A = active career, still changing; P = began before the archive: earlier results unknown)']
    for i, r in enumerate(rows, 1):
        flags = ('A' if r['active'] else '-') + ('P' if r['partial'] else '-')
        out.append(f'{i:3d}. {r["name"]:34s} {r["value"]:>10} {flags}  ' + ', '.join(r['evidence'][:4]))
    return out


def main():
    a = Archive(sys.argv[1])
    cmd = sys.argv[2]
    arg = sys.argv[3] if len(sys.argv) > 3 else None
    fn = {'person': lambda: person(a, int(arg)), 'staff': lambda: staff(a, int(arg)), 'clients': lambda: clients(a, int(arg)),
          'course': lambda: course(a, arg), 'recap': lambda: recap(a, int(arg)),
          'find': lambda: [f'{pid}: {a.name(pid)}, born {a.people[pid]["born"]}' for pid in a.find(arg)],
          'examples': lambda: examples(a), 'boards': lambda: boards(a), 'board': lambda: one_board(a, arg)}[cmd]
    print('\n'.join(fn()))


if __name__ == '__main__':
    main()
