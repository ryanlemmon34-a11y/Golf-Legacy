"""Cohort study: careers in several full-size worlds, every shot simulated.

    python tools/cohort_study.py --seeds 2027 3031 4049 --years 30            # run, then report
    python tools/cohort_study.py --seeds 2027 3031 4049 --report-only         # report from saved data

Each seed is a different world, run for --years seasons with development on. After every season the
completed-season evidence of every golfer (the snapshot taken before tour cards change) is saved, so
the report is computed from yearly records rather than from biographies:

* unique golfers vs career episodes (a golfer who stops and comes back has two full-time episodes)
* the debut cohort: golfers who turned professional during the run, early enough to be observed for at
  least --mature seasons afterwards. Golfers who were already professionals when the world began are
  left-censored (their debut and early results were never observed) and are reported separately.
* career lengths, highest level reached, failed careers, debut / peak / exit ages, debt, comebacks
* card retention by tour level, and how concentrated major championships were
* a random sample of ordinary careers (not a highlight reel)

"First observed" achievements (e.g. a first major in the run) are not "first ever" for golfers who
started the run as established professionals: the world has no recorded history before its first year.
The world itself is a selected sample of competitive golfers (see docs/DEVELOPMENT_AND_CAREERS.md),
so its failure rates describe that sample, not everyone who ever tried golf.
"""
from __future__ import annotations

import argparse
import gzip
import json
import random
import statistics as S
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MAJORS = ('TOUR_MASTERS', 'PREMIER_TOUR_CHAMPIONSHIP', 'USA_OPEN', 'BRITANNIA_OPEN')
TIER_NAME = {1: 'Premier', 2: 'Challenger', 3: 'Regional', 4: 'Mini', 5: 'College', 6: 'Amateur', 9: '—'}
FIELDS = ('status', 'lifestyle', 'tier', 'next_tier', 'events', 'wins', 'top10', 'prize', 'net', 'cash',
          'overall', 'wr', 'am')


# ---- running a world --------------------------------------------------------------------------------
def run_world(seed, years, workers, data_dir):
    from golfsim.calendar import TOUR_BY_KEY
    from golfsim.population import generate_world
    from golfsim.season import Season
    t0 = time.perf_counter()
    world = generate_world(seed=seed)
    s = Season(world, seed=seed, development=True, workers=workers)
    first = s.first_year
    start = {g.id: [g.status, g.lifestyle, g.turned_pro] for g in world.golfers}
    rows = {}
    for y in range(first, first + years):
        s.run_year(y)
        snap = s.snapshots.pop(y)
        yr = {}
        for gid, r in snap.items():
            g = s.g[gid]
            nt = TOUR_BY_KEY[r['next_tour']].tier if r.get('next_tour') in TOUR_BY_KEY else 9
            yr[gid] = [r['status'], r['lifestyle'], r['tier'], nt, r['events'], r['wins'], r['top10'],
                       round(r['prize']), round(r['net']), round(g.cash), round(g.overall, 1),
                       r['wr_end'], r['am_end']]
        rows[y] = yr
        print(f'seed {seed}: {y} done, {len(yr)} active, {time.perf_counter() - t0:.0f} s', flush=True)
        if (y - first + 1) % 5 == 0 or y == first + years - 1:
            path = save(s, seed, first, y - first + 1, rows, start, data_dir, t0)   # a checkpoint
    s.close()
    return path


def save(s, seed, first, years, rows, start, data_dir, t0):
    """Write everything recorded so far (an interrupted run still leaves its completed seasons)."""
    golfers = {g.id: {'born': g.born, 'country': g.country, 'name': g.name, 'final': [g.status, g.lifestyle],
                      'turned_pro': g.turned_pro, 'potential': g.potential, 'start': start.get(g.id)}
               for g in s.world.golfers}
    keep = ('Turned professional', 'Stopped chasing', 'Quit their job', 'Retired', 'College eligibility')
    history = {gid: [(y, t) for y, _, t in h if t.startswith(keep)] for gid, h in s.history.items()}
    majors = {}
    for y in range(first, first + years):
        for m in MAJORS:
            r = s.results.get(f'{y}:{m}')
            if r and r.winner():
                majors[f'{y}:{m}'] = r.winner()
    routes = {f'{y}:{sid}': Counter(v.values()) for (y, sid), v in s.entry_routes.items() if sid in MAJORS}
    data = {'seed': seed, 'first': first, 'years': years, 'rows': rows, 'golfers': golfers, 'history': history,
            'majors': majors, 'routes': routes, 'unpaid': dict(s.unpaid),
            'holes': sum(s.holes_played.values()), 'minutes': (time.perf_counter() - t0) / 60}
    path = Path(data_dir) / f'cohort_{seed}.json.gz'
    tmp = path.with_suffix('.tmp')
    with gzip.open(tmp, 'wt') as f:
        json.dump(data, f)
    tmp.replace(path)
    return path


def load(data_dir, seed):
    with gzip.open(Path(data_dir) / f'cohort_{seed}.json.gz', 'rt') as f:
        d = json.load(f)
    d['rows'] = {int(y): {int(g): dict(zip(FIELDS, v)) for g, v in yr.items()} for y, yr in d['rows'].items()}
    d['golfers'] = {int(g): v for g, v in d['golfers'].items()}
    d['history'] = {int(g): v for g, v in d['history'].items()}
    return d


# ---- analysis ---------------------------------------------------------------------------------------
def q(xs, p):
    xs = sorted(xs)
    if not xs:
        return float('nan')
    k = (len(xs) - 1) * p
    lo = int(k)
    return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (k - lo)


def full_time(r):
    return r['status'] == 'pro' and r['lifestyle'] == 'full_time'


def analyse(d, mature):
    rows, golfers, first = d['rows'], d['golfers'], d['first']
    last = first + d['years'] - 1
    years = sorted(rows)
    out = {}
    # career timelines -------------------------------------------------------------------------------
    timeline = defaultdict(dict)                         # gid -> year -> row
    for y in years:
        for gid, r in rows[y].items():
            timeline[gid][y] = r
    episodes = defaultdict(list)                         # gid -> [[start, end]] of full-time pro seasons
    for gid, tl in timeline.items():
        for y in sorted(tl):
            if full_time(tl[y]):
                if episodes[gid] and episodes[gid][-1][1] == y - 1:
                    episodes[gid][-1][1] = y
                else:
                    episodes[gid].append([y, y])
    start_pro = {gid for gid, g in golfers.items() if g['start'] and g['start'][0] == 'pro' and g['start'][1] == 'full_time'}
    out['unique'] = len(golfers)
    out['unique_pros'] = len(episodes)
    out['episodes'] = sum(len(e) for e in episodes.values())
    out['multi_episode'] = sum(1 for e in episodes.values() if len(e) > 1)
    out['left_censored'] = len(start_pro & set(episodes))
    # the debut cohort: turned pro (first full-time season) during the run, observable for `mature` years
    cohort = [gid for gid, e in episodes.items() if gid not in start_pro and e[0][0] > first
              and e[0][0] <= last - mature + 1]
    out['cohort'] = len(cohort)
    age = lambda gid, y: y - golfers[gid]['born']
    debut_age = [age(gid, episodes[gid][0][0]) for gid in cohort]
    length = [sum(b - a + 1 for a, b in episodes[gid]) for gid in cohort]
    still = [gid for gid in cohort if episodes[gid][-1][1] == last]
    best_tier = {gid: min(timeline[gid][y]['tier'] for y in timeline[gid] if full_time(timeline[gid][y]))
                 for gid in cohort}
    net = {gid: sum(timeline[gid][y]['net'] for a, b in episodes[gid] for y in range(a, b + 1)) for gid in cohort}
    min_cash = {gid: min(timeline[gid][y]['cash'] for y in timeline[gid] if y >= episodes[gid][0][0]) for gid in cohort}
    exits = [gid for gid in cohort if episodes[gid][-1][1] < last]
    exit_age = [age(gid, episodes[gid][-1][1]) for gid in exits]
    exit_cash = [timeline[gid][episodes[gid][-1][1]]['cash'] for gid in exits]
    failed = [gid for gid in exits if best_tier[gid] >= 4]
    peak_age, rank_peak_age = [], []
    for gid in cohort:
        tl = timeline[gid]
        span = [y for y in tl if y >= episodes[gid][0][0]]
        if max(span) - min(span) + 1 >= mature:
            peak_age.append(age(gid, max(span, key=lambda y: (tl[y]['overall'], -y))))
            ranked = [y for y in span if tl[y]['wr']]
            if ranked:
                rank_peak_age.append(age(gid, min(ranked, key=lambda y: (tl[y]['wr'], y))))
    out.update(debut_age=debut_age, length=length, still=len(still), best_tier=Counter(best_tier.values()),
               exit_age=exit_age, exit_cash=exit_cash, failed=len(failed), exits=len(exits),
               lost_money=sum(1 for gid in exits if net[gid] < 0), min_cash=list(min_cash.values()),
               peak_age=peak_age, rank_peak_age=rank_peak_age)
    # what came after the chase
    after = Counter()
    for gid in exits:
        e = episodes[gid][-1][1]
        nxt = timeline[gid].get(e + 1)
        if nxt is None:
            after['retired from competition'] += 1
        elif nxt['status'] == 'club_pro':
            after['club professional'] += 1
        elif nxt['status'] == 'amateur':
            after['reinstated amateur'] += 1
        else:
            after['part-time professional'] += 1
    out['after'] = after
    # comebacks (any golfer: a second or later full-time episode)
    cb = [(gid, a) for gid, e in episodes.items() for a, _ in e[1:]]
    cb += [(gid, e[0][0]) for gid, e in episodes.items() if gid not in start_pro and e[0][0] > first
           and age(gid, e[0][0]) >= 27 and any(not full_time(r) and r['status'] in ('amateur', 'pro') and r['lifestyle'] == 'part_time'
                                              for y, r in timeline[gid].items() if y < e[0][0])]
    out['comebacks'] = len(cb)
    out['comeback_age'] = [age(gid, y) for gid, y in cb]
    better = 0
    for gid, y in cb:
        before = [r['tier'] for yy, r in timeline[gid].items() if yy < y and full_time(r)]
        later = [r['tier'] for yy, r in timeline[gid].items() if yy >= y and full_time(r)]
        if later and (not before or min(later) < min(before)):
            better += 1
    out['comeback_better'] = better
    # card retention ----------------------------------------------------------------------------------
    ret = {}
    for t in (1, 2, 3):
        for label, ys in (('early', [y for y in years if y < first + 4]), ('later', [y for y in years if y >= first + 4])):
            held = kept = 0
            for y in ys:
                for gid, r in rows[y].items():
                    if full_time(r) and r['tier'] == t:
                        held += 1
                        nxt = rows.get(y + 1, {}).get(gid)
                        kept += bool(nxt and full_time(nxt) and nxt['tier'] <= t) if y < last else r['next_tier'] <= t
            ret[(t, label)] = kept / held if held else float('nan')
    out['retention'] = ret
    # majors ------------------------------------------------------------------------------------------
    wins = Counter(d['majors'].values())
    out['majors'] = len(d['majors'])
    out['major_winners'] = len(wins)
    out['major_top'] = wins.most_common(5)
    out['major_top5_share'] = sum(n for _, n in wins.most_common(5)) / max(1, len(d['majors']))
    out['major_hhi'] = sum((n / max(1, len(d['majors']))) ** 2 for n in wins.values())
    out['major_multi'] = sum(1 for n in wins.values() if n > 1)
    out['major_from_start_world'] = sum(n for gid, n in wins.items() if golfers[int(gid)]['start'])
    decades = defaultdict(Counter)
    for k, w in d['majors'].items():
        decades[(int(k.split(':')[0]) - first) // 10][w] += 1
    out['major_decades'] = [(dd, sum(c.values()), len(c), c.most_common(1)[0][1]) for dd, c in sorted(decades.items())]
    # population over time ----------------------------------------------------------------------------
    out['population'] = [(y, len(rows[y]), sum(1 for r in rows[y].values() if full_time(r)),
                          sum(1 for r in rows[y].values() if r['lifestyle'] == 'part_time')) for y in years]
    # ordinary careers: a random sample of the cohort --------------------------------------------------
    rng = random.Random(f'sample:{d["seed"]}')
    sample = rng.sample(cohort, min(8, len(cohort)))
    lines = []
    for gid in sample:
        g, tl = golfers[gid], timeline[gid]
        track = ' '.join((TIER_NAME[tl[y]['tier']][0] if full_time(tl[y]) else
                          {'amateur': 'a', 'club_pro': 'c'}.get(tl[y]['status'], 'p')) for y in sorted(tl))
        e0 = episodes[gid][0][0]
        end = 'still chasing' if episodes[gid][-1][1] == last else f'stopped at {age(gid, episodes[gid][-1][1])}'
        lines.append(f'{g["name"]} ({g["country"]}): turned pro at {age(gid, e0)}, best level {TIER_NAME[best_tier[gid]]}, '
                     f'{sum(tl[y]["wins"] for y in tl)} wins, net from golf ${net[gid]:,.0f}, lowest savings '
                     f'${min_cash[gid]:,.0f}, {end}. Seasons from {min(tl)}: `{track}`')
    out['sample'] = lines
    out['routes'] = d['routes']
    out['unpaid'] = sum(d['unpaid'].values())
    out['holes'], out['minutes'] = d['holes'], d['minutes']
    return out


def fmt_dist(xs, money=False):
    if not xs:
        return '—'
    f = (lambda v: f'${v:,.0f}') if money else (lambda v: f'{v:.0f}')
    return f'{f(q(xs, .1))} / {f(q(xs, .5))} / {f(q(xs, .9))}'


def report(results, args):
    seeds = [r['seed'] for r in results]
    A = [r['a'] for r in results]
    head = '| | ' + ' | '.join(f'seed {s}' for s in seeds) + ' |'
    sep = '|---|' + '---|' * len(seeds)
    row = lambda label, f: f'| {label} | ' + ' | '.join(f(a) for a in A) + ' |'
    pct = lambda n, d: f'{100 * n / d:.0f}%' if d else '—'
    out = ['# Golf Legacy — Cohort Study', '',
           f'{len(seeds)} independent worlds (seeds {", ".join(map(str, seeds))}), {args.years} seasons each, development on, '
           f'every shot simulated ({sum(a["holes"] for a in A):,} holes in {sum(a["minutes"] for a in A):.0f} minutes of '
           'simulation). Generated by `python tools/cohort_study.py`.', '',
           '**How to read this.** The numbers describe the simulated world, which is a *selected sample* of '
           'competitive golfers (the world keeps every good golfer and a sample of weaker ones), so its rates '
           'are not population-wide rates for everyone who ever played. Golfers who were already professionals '
           'when a world began are left-censored and kept out of the debut cohort. "Debut cohort" = golfers who '
           f'turned professional during the run early enough to be followed for at least {args.mature} seasons. '
           'Distributions are shown as 10th percentile / median / 90th percentile. Different seeds disagreeing '
           'is information about how much luck and circumstance matter, not an error.', '',
           '## 1. Golfers and career episodes', '', head, sep,
           row('Unique golfers who lived in the world', lambda a: f'{a["unique"]:,}'),
           row('Unique golfers with a full-time professional season', lambda a: f'{a["unique_pros"]:,}'),
           row('Full-time professional episodes', lambda a: f'{a["episodes"]:,}'),
           row('Golfers with 2+ episodes (stopped, then came back)', lambda a: f'{a["multi_episode"]:,}'),
           row('Already full-time pros when the world began (left-censored)', lambda a: f'{a["left_censored"]:,}'),
           row(f'Debut cohort (followed {args.mature}+ seasons)', lambda a: f'{a["cohort"]:,}'),
           '', '## 2. The debut cohort: how careers went', '', head, sep,
           row('Age in first full-time pro season (10/50/90%)', lambda a: fmt_dist(a['debut_age'])),
           row('Full-time seasons, all episodes (10/50/90%)', lambda a: fmt_dist(a['length'])),
           row('Lasted 2 seasons or fewer', lambda a: pct(sum(1 for x in a['length'] if x <= 2), a['cohort'])),
           row('Lasted 10 seasons or more', lambda a: pct(sum(1 for x in a['length'] if x >= 10), a['cohort'])),
           row('Still full-time at the end (censored)', lambda a: pct(a['still'], a['cohort'])),
           row('Best level reached: Premier Tour', lambda a: pct(a['best_tier'].get(1, 0), a['cohort'])),
           row('Best level reached: Challenger', lambda a: pct(a['best_tier'].get(2, 0), a['cohort'])),
           row('Best level reached: Regional', lambda a: pct(a['best_tier'].get(3, 0), a['cohort'])),
           row('Never above the mini tours', lambda a: pct(a['best_tier'].get(4, 0), a['cohort'])),
           row('Stopped chasing / retired by the end', lambda a: pct(a['exits'], a['cohort'])),
           row('… of whom never got past the mini tours', lambda a: pct(a['failed'], a['exits'])),
           row('… of whom lost money overall chasing it', lambda a: pct(a['lost_money'], a['exits'])),
           row('Age when they stopped (10/50/90%)', lambda a: fmt_dist(a['exit_age'])),
           row('Savings when they stopped (10/50/90%)', lambda a: fmt_dist(a['exit_cash'], True)),
           row('Lowest savings during career (10/50/90%)', lambda a: fmt_dist(a['min_cash'], True)),
           row('Ever $50k+ in debt', lambda a: pct(sum(1 for x in a['min_cash'] if x < -50000), a['cohort'])),
           row('Peak age, by ability (10/50/90%)', lambda a: fmt_dist(a['peak_age'])),
           row('Peak age, by best world ranking (10/50/90%)', lambda a: fmt_dist(a['rank_peak_age'])),
           '', '**After the chase** (debut cohort, what they did the next season):', '', head, sep]
    kinds = sorted({k for a in A for k in a['after']})
    out += [row(k, lambda a, k=k: pct(a['after'].get(k, 0), a['exits'])) for k in kinds]
    out += ['', '## 3. Comebacks', '', head, sep,
            row('Comebacks (a new full-time run after a job / amateur golf)', lambda a: f'{a["comebacks"]}'),
            row('Age at comeback (10/50/90%)', lambda a: fmt_dist(a['comeback_age'])),
            row('… reached a higher level than before', lambda a: pct(a['comeback_better'], a['comebacks'])),
            '', '## 4. Keeping a card', '',
            'Share of full-time card holders who held a card at the same level or better the next season. '
            '"Early" = the first four seasons (still settling from the generated start); "later" = afterwards.', '',
            head, sep]
    for t in (1, 2, 3):
        for label in ('early', 'later'):
            out.append(row(f'{TIER_NAME[t]} ({label})', lambda a, t=t, label=label: f'{100 * a["retention"][(t, label)]:.0f}%'))
    out += ['', '## 5. Major championships', '', head, sep,
            row('Majors played', lambda a: f'{a["majors"]}'),
            row('Different winners', lambda a: f'{a["major_winners"]}'),
            row('Multiple major winners', lambda a: f'{a["major_multi"]}'),
            row('Most by one golfer', lambda a: f'{a["major_top"][0][1] if a["major_top"] else 0}'),
            row('Share won by the 5 most successful', lambda a: f'{100 * a["major_top5_share"]:.0f}%'),
            row('Concentration (HHI; 1/winners if all equal)', lambda a: f'{a["major_hhi"]:.3f}'),
            row('Won by golfers already in the world at the start', lambda a: f'{a["major_from_start_world"]}'),
            '', 'By decade (majors, different winners, most by one golfer):', '']
    for r in results:
        out.append(f'- seed {r["seed"]}: ' + '; '.join(f'years {10 * dd + 1}-{10 * dd + 10}: {n} majors, {w} winners, max {m}'
                                                      for dd, n, w, m in r['a']['major_decades']))
    out += ['', 'Major fields by entry route (season 1 vs the last season; INIT = inaugural invitations, first '
            'Tour Masters only; ALT = alternates replacing withdrawals):', '']
    for r in results:
        a = r['a']
        for key in sorted(a['routes'], key=lambda k: (int(k.split(':')[0]), k)):
            y = int(key.split(':')[0])
            if y in (r['first'], r['first'] + args.years - 1) and key.endswith('TOUR_MASTERS'):
                c = a['routes'][key]
                out.append(f'- seed {r["seed"]} {key}: {sum(c.values())} entrants — ' + ', '.join(f'{k} {v}' for k, v in sorted(c.items())))
    out += ['', '## 6. The world over time', '', '| Seed | Season | Active golfers | Full-time pros | Part-timers |', '|---|---|---|---|---|']
    for r in results:
        pop = r['a']['population']
        for y, n, ft, pt in pop[::5] + ([pop[-1]] if (len(pop) - 1) % 5 else []):
            out.append(f'| {r["seed"]} | {y} | {n:,} | {ft:,} | {pt:,} |')
    out += ['', '## 7. Ordinary careers (a random sample of each debut cohort, not a highlight reel)', '',
            'Season codes: P/C/R/M = full-time on the Premier / Challenger / Regional / mini tours, '
            'a = amateur, c = club professional, p = part-time professional.', '']
    for r in results:
        out += [f'**Seed {r["seed"]}**', ''] + [f'- {x}' for x in r['a']['sample']] + ['']
    out += ['## 8. Accounting', '', '| | ' + ' | '.join(f'seed {s}' for s in seeds) + ' |', sep,
            row('Purse money not paid out (unfilled paid places)', lambda a: f'${a["unpaid"]:,.0f}')]
    return '\n'.join(out) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, nargs='+', default=[2027, 3031, 4049])
    ap.add_argument('--years', type=int, default=30)
    ap.add_argument('--mature', type=int, default=12)
    ap.add_argument('--workers', type=int, default=None)
    ap.add_argument('--data', default=str(ROOT / 'reports' / 'cohort_data'))
    ap.add_argument('--out', default=str(ROOT / 'reports' / 'COHORT_STUDY.md'))
    ap.add_argument('--report-only', action='store_true')
    args = ap.parse_args()
    Path(args.data).mkdir(parents=True, exist_ok=True)
    if not args.report_only:
        for seed in args.seeds:
            run_world(seed, args.years, args.workers, args.data)
    results = []
    for seed in args.seeds:
        d = load(args.data, seed)
        args.years = d['years']
        results.append({'seed': seed, 'first': d['first'], 'a': analyse(d, args.mature)})
    Path(args.out).write_text(report(results, args))
    print('wrote', args.out)


if __name__ == '__main__':
    main()
