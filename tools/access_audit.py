"""Competition access audit: who gets to play, and why the others do not.

    python tools/access_audit.py                      -> run season 1 of seed 2027, write reports/ACCESS_AUDIT.md
    python tools/access_audit.py --seeds 2027 3031 --out reports/ACCESS_AUDIT.md
    python tools/access_audit.py --data a.pkl         -> report from saved data (written with --save)
    python tools/access_audit.py --compare before.pkl after.pkl --out COMPARE.md

Every golfer-week of a full season is classified (golfsim.season.ACCESS): played a first choice, an
alternative or a selected field (major, invitation, qualifier, post-season); injured; shut out of every
acceptable field; not selected for a college lineup; no suitable event scheduled (nothing at their level
in their region that week); not eligible for what was scheduled; could not afford any event; declined
what was on offer; or chose to train, rest or work. Reported by playing status, circuit, region and
career stage with annual starts and rounds (10th / 25th / median percentiles), starts against each
golfer's intended schedule (Season.target_events) and repeated denials (longest run of weeks shut out).

The capacity section compares, region by region and level by level, the places the calendar offers with
the starts the members intend to make. It reads no hidden attributes.
"""
from __future__ import annotations

import argparse
import pickle
import statistics as S
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SHORT = {'played: first choice': 'P1', 'played: alternative': 'Palt', 'played: selected field': 'Psel',
         'injured': 'inj', 'shut out: every acceptable field full': 'FULL',
         'not selected for the college lineup': 'LINE', 'no suitable event scheduled': 'NONE',
         'not eligible for the events scheduled': 'INEL', 'could not afford any event': 'AFF',
         'declined the events on offer': 'decl', 'chose to train': 'train', 'chose to rest': 'rest',
         'chose to work': 'work'}
LEVEL = {1: 'Premier', 2: 'Challenger', 3: 'Regional', 4: 'Mini', 5: 'College', 6: 'Amateur', 7: 'Club pro'}


def run(seed, years=1, workers=None):
    from golfsim.calendar import TOUR_BY_KEY
    from golfsim.population import generate_world
    from golfsim.season import Season
    s = Season(generate_world(seed=seed), seed=seed, development=True, workers=workers)
    out = {'seed': seed, 'seasons': []}
    for y in range(s.first_year, s.first_year + years):
        targets = {g.id: s.target_events(g) for g in s.world.golfers}
        t0 = time.perf_counter()
        s.run_year(y)
        secs = time.perf_counter() - t0
        snap = s.snapshots.pop(y)
        rows = {}
        for g in s.world.golfers:
            r = snap.get(g.id)
            if r is None or g.id not in targets:
                continue
            rows[g.id] = dict(status=r['status'], lifestyle=r['lifestyle'], tour=r['tour'], tier=r['tier'],
                              level=s.level_tier(g) if r['tour'] == g.tour else r['tier'], country=g.country,
                              age=g.age(y), events=r['events'], rounds=s.season_rounds[y].get(g.id, 0.0),
                              access=dict(s.week_access[y].get(g.id, {})), maxrun=s.max_denied_run[y].get(g.id, 0),
                              target=targets[g.id], rights=s.rights_of(g.id, y) if hasattr(s, 'rights_of') else '',
                              new=g.id not in out.get('_ids', ()) and y > s.first_year)
        events = [r for k, r in s.results.items() if k.startswith(f'{y}:')]
        by_tier = Counter()
        for r in events:
            ser = s.cal.by_id[r.series_id]
            by_tier[ser.tier] += 1
        out['seasons'].append({'year': y, 'rows': rows, 'seconds': secs, 'holes': s.holes_played[y],
                               'events': len(events), 'events_by_tier': dict(by_tier),
                               'capacity': capacity(s, y, targets)})
        out['_ids'] = set(rows)
    s.close()
    out.pop('_ids', None)
    return out


def capacity(s, year, targets):
    """Region x level: members, starts they intend (sum of target_events), and places the calendar offers
    there (events at that level hosted in the region x field x sites)."""
    from golfsim.geography import COUNTRIES
    from golfsim.season import region_of
    places = Counter()
    events = Counter()
    for ed in s.cal.editions(year):
        ser = ed.series
        if ser.kind == 'major':
            continue
        reg = COUNTRIES[ser.host_country].region
        tier = 7 if ser.eligibility == 'club_pro' else ser.tier
        if tier > 7:
            continue
        places[(reg, tier)] += ser.field * ser.sites
        events[(reg, tier)] += 1
    members, intent = Counter(), Counter()
    for g in s.world.golfers:
        if g.lifestyle == 'retired' or g.id not in targets:
            continue
        key = (region_of(g), s.level_tier(g))
        members[key] += 1
        intent[key] += targets[g.id]
    return {'places': dict(places), 'events': dict(events), 'members': dict(members), 'intent': dict(intent)}


# ---- report ----------------------------------------------------------------------------------------
def q(xs, p):
    xs = sorted(xs)
    return xs[int(p * (len(xs) - 1))] if xs else 0


def status(r):
    if r['status'] == 'club_pro':
        return 'club pro'
    if r['status'] == 'amateur':
        return 'college' if (r['tour'] or '').startswith('CO_') else f"amateur {'part-time' if r['lifestyle'] == 'part_time' else 'full-time'}"
    lvl = LEVEL.get(r['tier'], 'other')
    return f"pro {lvl}{' (part-time)' if r['lifestyle'] == 'part_time' else ''}"


def stage(r):
    a = r['age']
    return '18-22' if a <= 22 else '23-26' if a <= 26 else '27-32' if a <= 32 else '33-40' if a <= 40 else '41+'


def table(rows, keyf, title, minn=20):
    groups = defaultdict(list)
    for r in rows.values():
        if r['lifestyle'] != 'retired':
            groups[keyf(r)].append(r)
    cols = list(SHORT.values())
    out = [f'### {title}', '',
           '| Group | Golfers | ' + ' | '.join(cols) + ' | Starts p10 / p25 / p50 | Intended (median) | ≥75% of intended '
           '| Rounds p10 / p50 | Denied 3+ / 6+ weeks running |',
           '|---|---|' + '---|' * (len(cols) + 5)]
    for k in sorted(groups, key=str):
        gs = groups[k]
        if len(gs) < minn:
            continue
        tot = Counter()
        for r in gs:
            tot.update(r['access'])
        n = sum(tot.values()) or 1
        cells = [f'{100 * tot[a] / n:.0f}' for a in SHORT]
        st = [r['events'] for r in gs]
        rd = [r['rounds'] for r in gs]
        reach = sum(1 for r in gs if r['events'] >= 0.75 * r['target']) / len(gs)
        out.append(f'| {k} | {len(gs)} | ' + ' | '.join(cells) + f' | {q(st, .1)} / {q(st, .25)} / {q(st, .5)} '
                   f'| {S.median(r["target"] for r in gs):.0f} | {100 * reach:.0f}% | {q(rd, .1):.0f} / {q(rd, .5):.0f} '
                   f'| {100 * sum(r["maxrun"] >= 3 for r in gs) / len(gs):.0f}% / {100 * sum(r["maxrun"] >= 6 for r in gs) / len(gs):.0f}% |')
    return out + ['']


def capacity_table(cap):
    out = ['### Capacity: places offered vs starts intended, by region and level', '',
           'Places = events at that level hosted in the region × field × sites (Challenger and Premier members also '
           'travel, so their regions are not closed). Intended = sum of members\' target starts. A ratio under ~1.3 means '
           'members cannot all reach their intended schedules once visitors, travel limits and lineups are counted.', '',
           '| Region | Level | Members | Intended starts | Events | Places | Places / intended |', '|---|---|---|---|---|---|---|']
    keys = sorted(set(cap['members']) | set(cap['places']), key=lambda k: (k[1], k[0]))
    for reg, tier in keys:
        m, i = cap['members'].get((reg, tier), 0), cap['intent'].get((reg, tier), 0)
        p, e = cap['places'].get((reg, tier), 0), cap['events'].get((reg, tier), 0)
        if not m and not p:
            continue
        ratio = f'{p / i:.1f}' if i else '—'
        out.append(f'| {reg} | {LEVEL.get(tier, tier)} | {m} | {i:.0f} | {e} | {p} | {ratio} |')
    return out + ['']


def report(datas, title='Golf Legacy — Competition Access Audit'):
    out = [f'# {title}', '', 'Generated by `python tools/access_audit.py`. Columns are shares (%) of golfer-weeks: '
           '**P1** played their first choice, **Palt** played an alternative after missing it, **Psel** played a field chosen by '
           'the event (major, invitation, qualifier, college post-season), **inj** injured, **FULL** shut out of every acceptable '
           'field, **LINE** not selected for a college lineup, **NONE** no suitable event scheduled (nothing at their level in their '
           'region), **INEL** not eligible for what was scheduled, **AFF** could not afford any event, **decl** planned to play but '
           'declined what was on offer, **train / rest / work** chosen. "Intended" is each golfer\'s target number of starts.', '']
    for d in datas:
        for sea in d['seasons']:
            rows = sea['rows']
            out += [f'## Seed {d["seed"]}, season {sea["year"]}', '',
                    f'{sea["events"]} events ({", ".join(f"{LEVEL.get(t, "Major" if t == 0 else "Qualifying")} {n}" for t, n in sorted(sea["events_by_tier"].items()))}), '
                    f'{sea["holes"]:,} holes played, {sea["seconds"]:.0f} s to simulate.', '']
            out += table(rows, status, 'By playing status')
            out += table(rows, lambda r: r['tour'] or ('club pro' if r['status'] == 'club_pro' else '—'), 'By circuit (membership)')
            if any(r.get('rights') for r in rows.values()):
                out += table({k: r for k, r in rows.items() if r.get('rights')}, lambda r: r['rights'], 'Premier members by playing rights', 1)
            from golfsim.geography import COUNTRIES
            out += table(rows, lambda r: f"{COUNTRIES[r['country']].region} · {status(r)}", 'By region and status', 15)
            out += table(rows, lambda r: f"{stage(r)} · {status(r)}", 'By career stage and status', 15)
            out += capacity_table(sea['capacity'])
    return '\n'.join(out) + '\n'


def compare(before, after):
    """Side by side: share of weeks played / blocked / chosen, and starts, by playing status."""
    def summary(ds):
        rows = {}
        for d in ds:
            for sea in d['seasons']:
                for gid, r in sea['rows'].items():
                    rows[(d['seed'], sea['year'], gid)] = r
        groups = defaultdict(list)
        for r in rows.values():
            groups[status(r)].append(r)
        out = {}
        for k, gs in groups.items():
            tot = Counter()
            for r in gs:
                tot.update(r['access'])
            n = sum(tot.values()) or 1
            played = sum(tot[a] for a in SHORT if a.startswith('played')) / n
            blocked = sum(tot[a] for a in ('shut out: every acceptable field full', 'no suitable event scheduled',
                                            'not eligible for the events scheduled')) / n
            st = [r['events'] for r in gs]
            out[k] = (len(gs), played, blocked, tot['could not afford any event'] / n, q(st, .1), q(st, .25), q(st, .5),
                      sum(1 for r in gs if r['events'] >= 0.75 * r['target']) / len(gs),
                      sum(r['maxrun'] >= 6 for r in gs) / len(gs))
        return out
    a, b = summary(before), summary(after)
    out = ['| Status | Golfers | Weeks played | Weeks blocked (full / no event / ineligible) | Could not afford | Starts p10 / p25 / p50 '
           '| ≥75% of intended | Denied 6+ weeks running |', '|---|---|---|---|---|---|---|---|']
    for k in sorted(set(a) | set(b)):
        x, y = a.get(k), b.get(k)
        f = lambda v, i, pct=True: '—' if v is None else (f'{100 * v[i]:.0f}%' if pct else f'{v[i]}')
        out.append(f'| {k} | {f(x, 0, False)} → {f(y, 0, False)} | {f(x, 1)} → {f(y, 1)} | {f(x, 2)} → {f(y, 2)} | {f(x, 3)} → {f(y, 3)} '
                   f'| {"—" if x is None else f"{x[4]}/{x[5]}/{x[6]}"} → {"—" if y is None else f"{y[4]}/{y[5]}/{y[6]}"} '
                   f'| {f(x, 7)} → {f(y, 7)} | {f(x, 8)} → {f(y, 8)} |')
    return out


def load(path):
    with open(path, 'rb') as f:
        d = pickle.load(f)
    return d if isinstance(d, list) else [d]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, nargs='+', default=[2027])
    ap.add_argument('--years', type=int, default=1)
    ap.add_argument('--workers', type=int, default=None)
    ap.add_argument('--out', default=str(ROOT / 'reports' / 'ACCESS_AUDIT.md'))
    ap.add_argument('--save', help='also pickle the data here')
    ap.add_argument('--data', nargs='+', help='report from saved data instead of running')
    ap.add_argument('--compare', nargs=2, metavar=('BEFORE', 'AFTER'))
    a = ap.parse_args()
    if a.compare:
        b, c = (load(p) for p in a.compare)
        Path(a.out).write_text('\n'.join(compare(b, c)) + '\n')
        print('wrote', a.out)
        return
    datas = [d for p in a.data for d in load(p)] if a.data else [run(s, a.years, a.workers) for s in a.seeds]
    if a.save:
        with open(a.save, 'wb') as f:
            pickle.dump(datas, f)
    Path(a.out).write_text(report(datas))
    print('wrote', a.out)


if __name__ == '__main__':
    main()
