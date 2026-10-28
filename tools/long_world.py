"""Long-world test: whole worlds for decades, every shot simulated, saved so they can be inspected.

    python tools/long_world.py --seeds 2027 3031 4049 --years 25 --out reports/long_world
    python tools/long_world.py --seeds 2027 --years 3 --out <dir> --strict    # the integration gate
    python tools/long_world.py --out reports/long_world --report-only         # re-report saved data

Per run directory:
    manifest.json            exact engine commit (and whether the tree was dirty), configuration,
                             seeds, years requested and completed per seed, checkpoint format
    archive_<s>/             the world's history archive (golfsim/archive.py): durable facts, one file
                             per season — explore with tools/history_query.py
    seed_<s>.save            a resumable simulation save (golfsim/savegame.py), every --save-every
                             seasons; `--resume` continues an interrupted run exactly
    seed_<s>.json.gz         player-facing records (no hidden attributes), checkpointed every 5 years
    seed_<s>.debug.json.gz   hidden attributes per golfer-year and staff skills (debug only)
    REPORT.md                player-facing report: checks, annual highlights, careers, staff, majors
    DEBUG.md                 development and hidden-attribute analysis

Checks run every season, during the run: every golfer's cash reconciles with their ledger; payments to
coaches and caddies equal what they received; staff invariants (coach capacity, one golfer per caddie,
nobody retired on a payroll); and the population reconciles (golfers this season = last season −
retirements and golfers who joined the staff + new juniors). Zero-start seasons carry the reason recorded
by the monthly plans; career decisions carry their reasons.

Different seeds are different worlds and should tell different stories; nothing here steers them.
"""
from __future__ import annotations

import argparse
import gzip
import json
import platform
import random
import statistics as S
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FORMAT = 'golf-legacy-long-world/2'
MAJORS = ('TOUR_MASTERS', 'PREMIER_TOUR_CHAMPIONSHIP', 'USA_OPEN', 'BRITANNIA_OPEN')
MAJOR_NAME = {'TOUR_MASTERS': 'Tour Masters', 'PREMIER_TOUR_CHAMPIONSHIP': 'Premier Tour Championship',
              'USA_OPEN': 'USA Open', 'BRITANNIA_OPEN': 'Britannia Open'}
LEVEL = {1: 'Premier', 2: 'Challenger', 3: 'Regional', 4: 'Mini', 5: 'College', 6: 'Amateur', 9: '—'}
ROW = ('status', 'lifestyle', 'tier', 'next_tier', 'events', 'wins', 'wins_by_tier', 'majors', 'top10', 'cuts',
       'prize', 'net', 'cash', 'wr', 'am', 'injury_weeks', 'zero_start', 'coach', 'deal', 'caddie',
       'coaching', 'caddie_cost', 'sponsors', 'salary', 'work', 'support', 'living', 'event_costs',
       'play_wk', 'train_wk', 'rest_wk', 'work_wk')
EXITS = ('retired', 'became coach', 'became caddie')


def git_state():
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--', 'golfsim'], cwd=ROOT, text=True).strip())
        return commit, dirty
    except Exception:
        return 'unknown', True


def config():
    from golfsim import careers as C, finance as F, staff as ST, population as P, development as D
    return {'finance': {k: getattr(F, k) for k in ('LIVING', 'LIVING_WORKING', 'WORK_WAGE', 'CREDIT_BASE', 'CREDIT_SHARE',
                                                   'CREDIT_CAP', 'RESERVE_WEEKS', 'PRIOR_PRIZE_SHARE', 'CADDIE_SHARE')},
            'staff': {k: getattr(ST, k) for k in ('SELF_TEACHING', 'SCOUT_SHARE', 'SELF_CADDIE', 'CADDIE_TIERS',
                                                  'COACH_OF_MEANS', 'CADDIE_OF_MEANS')},
            'careers': {'LIFE_AGE': C.LIFE_AGE},
            'population': {k: getattr(P, k) for k in ('POTENTIAL_SD', 'CANDIDATES_PER_POOL', 'SCOUTING_SD')},
            'development': {k: getattr(D, k) for k in ('BASE_TRAIN', 'BASE_PLAY', 'MATURING')}}


# ---- running ------------------------------------------------------------------------------------------
def checks(s, year, snap, active_before):
    """Invariants for one completed season (after its end-of-season decisions)."""
    led = s.ledgers[year]
    start = s.cash_start[year]                        # juniors arriving at year end start next season
    recon = sum(1 for gid, c0 in start.items()
                if abs(s.g[gid].cash - (c0 + (led[gid].net if gid in led else 0.0)))
                > max(0.01, 1e-12 * abs(s.g[gid].cash)))      # a cent, or float rounding on fortunes
    rec = s.staff_receipts[year]
    paid_caddie = sum(l.caddie + l.caddie_share for l in led.values())
    paid_coach = sum(l.coaching + l.coach_share for l in led.values())
    got_caddie = sum(v for (k, _), v in rec.items() if k == 'caddie')
    got_coach = sum(v for (k, _), v in rec.items() if k == 'coach')
    st = s.staff
    load = Counter(st.coach_of.values())
    staff_bad = (sum(1 for cid, n in load.items() if n > st.coaches[cid].capacity)
                 + len(st.caddie_of) - len(set(st.caddie_of.values()))
                 + sum(1 for gid in list(st.coach_of) + list(st.caddie_of) if s.g[gid].lifestyle == 'retired')
                 + sum(1 for cid in st.coach_of.values() if st.coaches[cid].status != 'active')
                 + sum(1 for kid in st.caddie_of.values() if st.caddies[kid].status != 'active'))
    exits = sum(1 for t in s.transitions.get(year, ()) if t['kind'] in EXITS)
    juniors = s.juniors_added.get(year + 1, 0)
    active_after = sum(1 for g in s.world.golfers if g.lifestyle != 'retired')
    return {'reconcile_errors': recon, 'caddie_paid': round(paid_caddie, 2), 'caddie_received': round(got_caddie, 2),
            'coach_paid': round(paid_coach, 2), 'coach_received': round(got_coach, 2), 'staff_violations': staff_bad,
            'active_before': active_before, 'exits': exits, 'juniors': juniors, 'active_after': active_after,
            'population_ok': active_before - exits + juniors == active_after,
            'min_cash': round(min(g.cash for g in s.world.golfers if g.lifestyle != 'retired'))}


def year_rows(s, year, snap):
    from golfsim.calendar import TOUR_BY_KEY
    a = s.assignments.get(year, {})
    rows, debug = {}, {}
    for gid, r in snap.items():
        g = s.g[gid]
        led = s.ledgers[year].get(gid)
        act = s.activity_counts[year].get(gid, {})
        nt = TOUR_BY_KEY[r['next_tour']].tier if r.get('next_tour') in TOUR_BY_KEY else 9
        rows[gid] = [r['status'], r['lifestyle'], r['tier'], nt, r['events'], r['wins'], r['wins_by_tier'], r['majors'],
                     r['top10'], r['cuts'], round(r['prize']), round(r['net']), round(g.cash), r['wr_end'], r['am_end'],
                     r['injury_weeks'], r.get('zero_start_reason', ''), a.get('coach_of', {}).get(gid),
                     a.get('deal', {}).get(gid), a.get('caddie_of', {}).get(gid),
                     round(led.coaching + led.coach_share) if led else 0, round(led.caddie + led.caddie_share) if led else 0,
                     round(led.sponsors) if led else 0, round(led.salary) if led else 0, round(led.work) if led else 0,
                     round(led.support) if led else 0, round(led.living) if led else 0, round(led.events) if led else 0,
                     act.get('play', 0), act.get('train', 0), act.get('rest', 0), act.get('work', 0)]
        debug[gid] = [round(g.overall, 2), round(g.potential, 1),
                      round(sum(g.ceilings[k] - g.attrs[k] for k in g.attrs) / len(g.attrs), 2) if g.ceilings else None]
    return rows, debug


def run_world(seed, years, workers, out, resume=False, save_every=1):
    """Run (or resume) one world. Each season it appends to the world's history archive
    (archive_<seed>/) and, every `save_every` seasons, writes a resumable simulation save
    (seed_<seed>.save) plus this tool's own running totals, so an interrupted run continues exactly."""
    import pickle
    from golfsim.archive import ArchiveWriter
    from golfsim.population import generate_world
    from golfsim.savegame import load_simulation, save_simulation
    from golfsim.season import Season
    t0 = time.perf_counter()
    save_path, state_path = out / f'seed_{seed}.save', out / f'seed_{seed}.state.pkl'
    if resume and save_path.exists() and state_path.exists():
        s, meta = load_simulation(save_path)
        s.workers = workers or s.workers
        with open(state_path, 'rb') as f:
            data, debug, created, initial, arch_created = pickle.load(f)
        print(f'seed {seed}: resumed after {data["years"]} seasons ({meta["commit"][:10]})', flush=True)
    else:
        world = generate_world(seed=seed)
        s = Season(world, seed=seed, development=True, workers=workers)
        created = {g.id: s.first_year for g in world.golfers}
        initial = {g.id for g in world.golfers}
        data = {'format': FORMAT, 'seed': seed, 'first': s.first_year, 'years': 0, 'rows': {}, 'checks': {},
                'majors': {}, 'transitions': {}, 'routes': {}, 'unpaid': {}, 'number_one': {}}
        debug = {'format': FORMAT, 'seed': seed, 'rows': {}}
        arch_created = None
    first = data['first']
    archive = ArchiveWriter(out / f'archive_{seed}', s)
    if arch_created:
        archive.created, archive.initial = arch_created, initial
    for y in range(first + data['years'], first + years):
        active_before = sum(1 for g in s.world.golfers if g.lifestyle != 'retired')
        s.run_year(y)
        archive.write_year(s, y)                            # the durable history, before the snapshot goes
        snap = s.snapshots.pop(y)
        rows, dbg = year_rows(s, y, snap)
        data['rows'][y], debug['rows'][y] = rows, dbg
        data['checks'][y] = checks(s, y, snap, active_before)
        data['transitions'][y] = s.transitions.get(y, [])
        data['unpaid'][y] = s.unpaid[y]
        data['number_one'][y] = next((gid for gid, r in snap.items() if r['wr_end'] == 1), None)
        for m in MAJORS:
            r = s.results.get(f'{y}:{m}')
            if r and r.winner():
                data['majors'][f'{y}:{m}'] = r.winner()
            if (y, m) in s.entry_routes:
                data['routes'][f'{y}:{m}'] = Counter(s.entry_routes[(y, m)].values())
        for g in s.world.golfers:
            created.setdefault(g.id, y + 1)
        data['years'] = y - first + 1
        c = data['checks'][y]
        print(f'seed {seed}: {y} done ({data["years"]}/{years}), {c["active_after"]} active, '
              f'reconcile errors {c["reconcile_errors"]}, staff violations {c["staff_violations"]}, '
              f'population {"ok" if c["population_ok"] else "MISMATCH"}, {time.perf_counter() - t0:.0f} s', flush=True)
        last = y == first + years - 1
        if data['years'] % 5 == 0 or last:
            save(s, data, debug, created, initial, out, t0)
        if data['years'] % save_every == 0 or last:
            archive.write_state(s)
            save_simulation(s, save_path, f'seed {seed} after {y}')
            with open(state_path, 'wb') as f:
                pickle.dump((data, debug, created, initial, archive.created), f)
    s.close()


def save(s, data, debug, created, initial, out, t0):
    st = s.staff
    data['golfers'] = {g.id: {'name': g.name, 'country': g.country, 'born': g.born, 'created': created.get(g.id),
                              'initial': g.id in initial, 'final': [g.status, g.lifestyle, g.tour],
                              'history': [(y, t) for y, _, t in s.history.get(g.id, ())]}
                       for g in s.world.golfers}
    data['coaches'] = {c.id: {'name': c.name, 'country': c.country, 'born': c.born, 'speciality': c.speciality,
                              'youth': c.youth, 'reputation': c.reputation, 'background': c.background,
                              'former_golfer': c.former_golfer, 'status': c.status, 'earnings': round(c.earnings),
                              'history': c.history} for c in st.coaches.values()}
    data['caddies'] = {k.id: {'name': k.name, 'country': k.country, 'born': k.born, 'reputation': k.reputation,
                              'background': k.background, 'former_golfer': k.former_golfer, 'status': k.status,
                              'earnings': round(k.earnings), 'seasons': k.seasons, 'history': k.history}
                       for k in st.caddies.values()}
    data['staff_year'] = {y: {f'{kind}:{i}': v for (kind, i), v in d.items()} for y, d in s.staff_year.items()}
    data['receipts'] = {y: {f'{kind}:{i}': round(v, 2) for (kind, i), v in d.items()} for y, d in s.staff_receipts.items()}
    data['holes'] = sum(s.holes_played.values())
    data['minutes'] = (time.perf_counter() - t0) / 60
    debug['staff'] = {'coaches': {c.id: [c.teaching, c.scouting] for c in st.coaches.values()},
                      'caddies': {k.id: k.skills for k in st.caddies.values()}}
    for name, obj in ((f'seed_{data["seed"]}.json.gz', data), (f'seed_{data["seed"]}.debug.json.gz', debug)):
        tmp = out / (name + '.tmp')
        with gzip.open(tmp, 'wt') as f:
            json.dump(obj, f)
        tmp.replace(out / name)
    man = load_manifest(out)
    man.setdefault('seeds', {})[str(data['seed'])] = {'years_completed': data['years'], 'minutes': round(data['minutes'], 1),
                                                      'holes': data['holes'], 'commit': man['commit']}
    (out / 'manifest.json').write_text(json.dumps(man, indent=1, default=str))


def load_manifest(out):
    p = out / 'manifest.json'
    return json.loads(p.read_text()) if p.exists() else {}


def load(out, seed):
    with gzip.open(out / f'seed_{seed}.json.gz', 'rt') as f:
        d = json.load(f)
    if d.get('format') != FORMAT:
        raise SystemExit(f'seed {seed}: checkpoint format {d.get("format")} is not {FORMAT}; re-run it')
    d['rows'] = {int(y): {int(g): dict(zip(ROW, v)) for g, v in yr.items()} for y, yr in d['rows'].items()}
    d['checks'] = {int(y): v for y, v in d['checks'].items()}
    d['transitions'] = {int(y): v for y, v in d['transitions'].items()}
    d['golfers'] = {int(g): v for g, v in d['golfers'].items()}
    d['number_one'] = {int(y): v for y, v in d['number_one'].items()}
    for r in (r for yr in d['rows'].values() for r in yr.values()):
        r['wins_by_tier'] = {int(t): n for t, n in r['wins_by_tier'].items()}
    return d


def load_debug(out, seed):
    with gzip.open(out / f'seed_{seed}.debug.json.gz', 'rt') as f:
        d = json.load(f)
    return {int(y): {int(g): v for g, v in yr.items()} for y, yr in d['rows'].items()}


# ---- analysis -----------------------------------------------------------------------------------------
def q(xs, p):
    xs = sorted(xs)
    if not xs:
        return float('nan')
    k = (len(xs) - 1) * p
    lo = int(k)
    return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (k - lo)


def dist(xs, money=False):
    if not xs:
        return '—'
    f = (lambda v: f'${v:,.0f}') if money else (lambda v: f'{v:.0f}')
    return f'{f(q(xs, .1))} / {f(q(xs, .5))} / {f(q(xs, .9))}'


def full_time(r):
    return r['status'] == 'pro' and r['lifestyle'] == 'full_time'


def careers(d):
    rows, golfers, first = d['rows'], d['golfers'], d['first']
    years = sorted(rows)
    last = years[-1]
    tl = defaultdict(dict)
    for y in years:
        for gid, r in rows[y].items():
            tl[gid][y] = r
    eps = defaultdict(list)
    for gid, t in tl.items():
        for y in sorted(t):
            if full_time(t[y]):
                if eps[gid] and eps[gid][-1][1] == y - 1:
                    eps[gid][-1][1] = y
                else:
                    eps[gid].append([y, y])
    return tl, eps, years, last


def name(d, gid):
    g = d['golfers'][gid]
    return f'{g["name"]} ({g["country"]})'


def analyse(d, mature):
    tl, eps, years, last = careers(d)
    golfers, first = d['golfers'], d['first']
    age = lambda gid, y: y - golfers[gid]['born']
    left = {gid for gid in eps if golfers[gid]['initial'] and eps[gid][0][0] == first}
    cohort = [gid for gid in eps if gid not in left and eps[gid][0][0] <= last - mature + 1]
    best = {gid: min(tl[gid][y]['tier'] for y in tl[gid] if full_time(tl[gid][y])) for gid in eps}
    length = {gid: sum(b - a + 1 for a, b in eps[gid]) for gid in eps}
    exits = [gid for gid in cohort if eps[gid][-1][1] < last]
    netsum = {gid: sum(tl[gid][y]['net'] for a, b in eps[gid] for y in range(a, b + 1)) for gid in eps}
    mincash = {gid: min(tl[gid][y]['cash'] for y in tl[gid] if y >= eps[gid][0][0]) for gid in eps}
    rank_peak = []
    for gid in cohort:
        ranked = [y for y in tl[gid] if tl[gid][y]['wr'] and y >= eps[gid][0][0]]
        if ranked and last - eps[gid][0][0] + 1 >= mature:
            rank_peak.append(age(gid, min(ranked, key=lambda y: (tl[gid][y]['wr'], y))))
    a = {'unique': len(golfers), 'unique_pros': len(eps), 'episodes': sum(len(e) for e in eps.values()),
         'multi': sum(1 for e in eps.values() if len(e) > 1), 'left': len(left), 'cohort': len(cohort),
         'debut_age': [age(g, eps[g][0][0]) for g in cohort], 'length': [length[g] for g in cohort],
         'still': sum(1 for g in cohort if eps[g][-1][1] == last), 'best': Counter(best[g] for g in cohort),
         'exits': len(exits), 'failed': sum(1 for g in exits if best[g] >= 4),
         'lost': sum(1 for g in exits if netsum[g] < 0), 'exit_age': [age(g, eps[g][-1][1]) for g in exits],
         'exit_cash': [tl[g][eps[g][-1][1]]['cash'] for g in exits], 'min_cash': [mincash[g] for g in cohort],
         'rank_peak': rank_peak}
    # card retention, zero-start seasons
    ret = {}
    for t in (1, 2, 3):
        held = kept = 0
        for y in years[3:]:
            for gid, r in d['rows'][y].items():
                if full_time(r) and r['tier'] == t:
                    held += 1
                    nxt = d['rows'].get(y + 1, {}).get(gid)
                    kept += (bool(nxt and full_time(nxt) and nxt['tier'] <= t) if y < last else r['next_tier'] <= t)
        ret[t] = kept / held if held else float('nan')
    a['retention'] = ret
    zero = Counter()
    seasons = Counter()
    for y in years:
        for r in d['rows'][y].values():
            if full_time(r) and r['tier'] <= 4:
                seasons[r['tier']] += 1
                if r['events'] == 0:
                    zero[(r['tier'], r['zero_start'])] += 1
    a['zero'], a['ft_seasons'] = zero, seasons
    # majors
    wins = Counter(d['majors'].values())
    a['majors'] = len(d['majors'])
    a['major_winners'] = len(wins)
    a['major_multi'] = sum(1 for n in wins.values() if n > 1)
    a['major_top'] = wins.most_common(5)
    a['major_hhi'] = sum((n / max(1, a['majors'])) ** 2 for n in wins.values())
    # transitions
    tr = Counter(t['kind'] for y in years for t in d['transitions'].get(y, ()))
    a['transitions'] = tr
    a['_tl'], a['_eps'], a['_best'], a['_length'] = tl, eps, best, length      # per-golfer lookups
    return a


def highlights(d, a):
    """Annual highlights, assembled only from recorded events."""
    out = []
    g = d['golfers']
    by_year = defaultdict(list)
    for k, w in d['majors'].items():
        y, m = k.split(':')
        by_year[int(y)].append(f'{MAJOR_NAME[m]}: {name(d, w)}')
    prev_no1 = None
    for y in sorted(d['rows']):
        bits = []
        if by_year[y]:
            bits.append('Majors — ' + '; '.join(by_year[y]))
        no1 = d['number_one'].get(y)
        if no1 and no1 != prev_no1:
            bits.append(f'New world No.1 at year end: {name(d, no1)}')
        prev_no1 = no1 or prev_no1
        tr = d['transitions'].get(y, [])
        cb = [t for t in tr if t['kind'] == 'comeback']
        if cb:
            bits.append(f'{len(cb)} comeback(s)' + (', e.g. ' + ', '.join(f'{name(d, t["gid"])} at {t["age"]}' for t in cb[:2])))
        staff = [t for t in tr if t['kind'] in ('became coach', 'became caddie')]
        winners = [t for t in staff if sum(sum(r['wins_by_tier'].values()) for r in (a['_tl'][t['gid']].values())) > 0]
        if staff:
            bits.append(f'{len(staff)} golfer(s) joined the staff ranks' +
                        (', incl. tournament winners ' + ', '.join(f'{name(d, t["gid"])} ({t["kind"][7:]})' for t in winners[:2])
                         if winners else ''))
        champs_retired = [t for t in tr if t['kind'] == 'retired' and any(w == t['gid'] for w in d['majors'].values())]
        if champs_retired:
            bits.append('Major champions retiring: ' + ', '.join(name(d, t['gid']) for t in champs_retired))
        out.append(f'- **{y}:** ' + '. '.join(bits) + '.')
    return out


def interesting(d, a, n=6):
    """Careers picked by rules on recorded results (not by hidden ability)."""
    tl, eps, best = a['_tl'], a['_eps'], a['_best']
    g = d['golfers']
    majors = Counter(d['majors'].values())
    wins = {gid: sum(sum(r['wins_by_tier'].values()) for r in t.values()) for gid, t in tl.items()}
    picks = []
    def add(label, gid):
        if gid is not None and gid not in [p for _, p in picks]:
            picks.append((label, gid))
    add('Most majors', majors.most_common(1)[0][0] if majors else None)
    add('Most wins', max(wins, key=lambda x: (wins[x], -x)) if wins else None)
    climb = [gid for gid in eps if not g[gid]['initial'] and best[gid] == 1
             and tl[gid][eps[gid][0][0]]['tier'] >= 4]
    add('From the mini tours to the Premier Tour', min(climb, key=lambda x: (eps[x][0][0], x)) if climb else None)
    late = [gid for gid in eps if best[gid] == 1 and min(y for y in tl[gid] if full_time(tl[gid][y]) and tl[gid][y]['tier'] == 1)
            - g[gid]['born'] >= 31]
    add('Late bloomer (first Premier season at 31+)', min(late, key=lambda x: x) if late else None)
    cbs = [gid for gid, e in eps.items() if len(e) > 1 and min(tl[gid][y]['tier'] for y in range(e[1][0], e[-1][1] + 1) if y in tl[gid])
           < min(tl[gid][y]['tier'] for y in range(e[0][0], e[0][1] + 1))]
    add('A comeback that went further than before', min(cbs) if cbs else None)
    add('Longest full-time career', max(a['_length'], key=lambda x: (a['_length'][x], -x)) if a['_length'] else None)
    out = []
    for label, gid in picks[:n]:
        out.append(f'- **{label} — {name(d, gid)}**, born {g[gid]["born"]}:')
        out += [f'  - {y}: {t}' for y, t in g[gid]['history'] if not t.startswith(('Hired', 'Approached', 'Left coach', 'Parted'))][:14]
    return out


def staff_stories(d, limit=4):
    out = []
    people = [('coach', c) for c in d['coaches'].values() if c['former_golfer']] + \
             [('caddie', k) for k in d['caddies'].values() if k['former_golfer']]
    people.sort(key=lambda x: (-x[1]['earnings'], x[1]['name']))
    coaches = [x for x in people if x[0] == 'coach'][:limit // 2]
    people = coaches + [x for x in people if x[0] == 'caddie'][:limit - len(coaches)]
    for role, p in people:
        gid = p['former_golfer']
        hist = d['golfers'][gid]['history']
        played = [t for _, t in hist if t.startswith(('Turned professional', 'Won the'))][:3]
        out.append(f'- **{p["name"]}** ({p["country"]}), {p["background"]} → {role}'
                   + (f' ({p.get("speciality", "").replace("_", " ")} specialist)' if role == 'coach' else '')
                   + f'; earned ${p["earnings"]:,} from it; now {p["status"]}.')
        out += [f'  - as a player: {t}' for t in played]
        out += [f'  - {y}: {t}' for y, t in p['history'][:4]]
    return out


def report(results, man, mature):
    seeds = [r['d']['seed'] for r in results]
    A = [r['a'] for r in results]
    head = '| | ' + ' | '.join(f'seed {s}' for s in seeds) + ' |'
    sep = '|---|' + '---|' * len(seeds)
    row = lambda label, f: f'| {label} | ' + ' | '.join(f(r['a'], r['d']) for r in results) + ' |'
    pct = lambda n, t: f'{100 * n / t:.0f}%' if t else '—'
    out = ['# Golf Legacy — Long-World Test', '',
           f'Engine commit `{man.get("commit", "?")}`' + (' (**uncommitted engine changes present**)' if man.get('dirty') else '')
           + f', format `{FORMAT}`. Seeds and seasons completed: '
           + ', '.join(f'{s} ({man["seeds"][str(s)]["years_completed"]})' for s in seeds) + '. '
           'Every shot simulated. This report contains no hidden attributes (see DEBUG.md).', '',
           '## 1. Checks (every season)', '', head, sep,
           row('Seasons with cash not reconciling', lambda a, d: str(sum(1 for c in d['checks'].values() if c['reconcile_errors']))),
           row('Seasons where staff payments ≠ receipts', lambda a, d: str(sum(1 for c in d['checks'].values()
               if abs(c['caddie_paid'] - c['caddie_received']) > 0.01 or abs(c['coach_paid'] - c['coach_received']) > 0.01))),
           row('Staff invariant violations', lambda a, d: str(sum(c['staff_violations'] for c in d['checks'].values()))),
           row('Seasons where the population does not reconcile', lambda a, d: str(sum(1 for c in d['checks'].values() if not c['population_ok']))),
           row('Lowest savings seen', lambda a, d: f'${min(c["min_cash"] for c in d["checks"].values()):,}'),
           '', '## 2. Population and career transitions', '',
           '| Seed | Season | Golfers | Exits (retired / joined staff) | New juniors | Next season |', '|---|---|---|---|---|---|']
    for r in results:
        for y, c in sorted(r['d']['checks'].items()):
            if (y - r['d']['first']) % 5 == 0 or y == max(r['d']['checks']):
                out.append(f'| {r["d"]["seed"]} | {y} | {c["active_before"]:,} | {c["exits"]} | {c["juniors"]} | {c["active_after"]:,} |')
    kinds = sorted({k for a in A for k in a['transitions']})
    out += ['', 'Career decisions over the whole run:', '', head, sep] + [row(k, lambda a, d, k=k: str(a['transitions'].get(k, 0))) for k in kinds]
    out += ['', '## 3. Full-time seasons with no start, by reason', '', head, sep]
    reasons = sorted({k for a in A for k in a['zero']})
    for t, why in reasons:
        out.append(row(f'{LEVEL[t]}: {why}', lambda a, d, t=t, why=why: pct(a['zero'][(t, why)], a['ft_seasons'][t])))
    out += ['', '## 4. Careers (golfers who turned pro during the run, followed ' f'{mature}+ seasons)', '',
            'Golfers already professional when a world began are left-censored and excluded. 10th / median / 90th percentile.', '',
            head, sep,
            row('Unique golfers / with a full-time season', lambda a, d: f'{a["unique"]:,} / {a["unique_pros"]:,}'),
            row('Full-time episodes (golfers with 2+)', lambda a, d: f'{a["episodes"]:,} ({a["multi"]})'),
            row('Debut cohort', lambda a, d: f'{a["cohort"]:,}'),
            row('Age in first full-time season', lambda a, d: dist(a['debut_age'])),
            row('Full-time seasons', lambda a, d: dist(a['length'])),
            row('Still full-time at the end', lambda a, d: pct(a['still'], a['cohort'])),
            row('Best level: Premier', lambda a, d: pct(a['best'].get(1, 0), a['cohort'])),
            row('Best level: Challenger', lambda a, d: pct(a['best'].get(2, 0), a['cohort'])),
            row('Best level: Regional', lambda a, d: pct(a['best'].get(3, 0), a['cohort'])),
            row('Never above the mini tours', lambda a, d: pct(a['best'].get(4, 0), a['cohort'])),
            row('Stopped by the end … never past the mini tours', lambda a, d: pct(a['failed'], a['exits'])),
            row('… lost money overall', lambda a, d: pct(a['lost'], a['exits'])),
            row('Age when they stopped', lambda a, d: dist(a['exit_age'])),
            row('Savings when they stopped', lambda a, d: dist(a['exit_cash'], True)),
            row('Lowest savings in their career', lambda a, d: dist(a['min_cash'], True)),
            row('Ever $50k+ in debt', lambda a, d: pct(sum(1 for x in a['min_cash'] if x < -50000), a['cohort'])),
            row('Age at best world ranking', lambda a, d: dist(a['rank_peak'])),
            row('Kept a Premier card (from season 4)', lambda a, d: f'{100 * a["retention"][1]:.0f}%'),
            row('Kept a Challenger card', lambda a, d: f'{100 * a["retention"][2]:.0f}%'),
            row('Kept a Regional card', lambda a, d: f'{100 * a["retention"][3]:.0f}%'),
            '', '## 5. Majors', '', head, sep,
            row('Majors / different winners / multiple winners', lambda a, d: f'{a["majors"]} / {a["major_winners"]} / {a["major_multi"]}'),
            row('Most by one golfer', lambda a, d: str(a['major_top'][0][1] if a['major_top'] else 0)),
            row('Concentration (HHI)', lambda a, d: f'{a["major_hhi"]:.3f}'), '']
    for r in results:
        d = r['d']
        names = [f'{k.split(":")[0]} {MAJOR_NAME[k.split(":")[1]]}: {name(d, w)}' for k, w in sorted(d['majors'].items())
                 if int(k.split(':')[0]) > d['first']]
        out += [f'**Seed {d["seed"]} — major winners from season two on:** ' + '; '.join(names), '']
        masters = [k for k in sorted(d['routes']) if k.endswith('TOUR_MASTERS')]
        if masters:
            k = masters[-1]
            out += [f'Last Tour Masters field by route ({k}): ' + ', '.join(f'{c} {n}' for c, n in sorted(d['routes'][k].items())), '']
    out += ['## 6. Annual highlights (from recorded events)', '']
    for r in results:
        out += [f'### Seed {r["d"]["seed"]}', ''] + highlights(r['d'], r['a']) + ['']
    out += ['## 7. Interesting careers (picked by rules on results)', '']
    for r in results:
        out += [f'### Seed {r["d"]["seed"]}', ''] + interesting(r['d'], r['a']) + ['']
    out += ['## 8. Former players on the staff', '']
    for r in results:
        out += [f'### Seed {r["d"]["seed"]}', ''] + staff_stories(r['d']) + ['']
    return '\n'.join(out) + '\n'


def debug_report(results, out_dir):
    out = ['# Golf Legacy — Long-World Debug (hidden attributes)', '',
           'Player-facing reports never show these. Overall = hidden ability; gap = average room to ceilings.', '']
    for r in results:
        d = r['d']
        dbg = load_debug(out_dir, d['seed'])
        years = sorted(dbg)
        change = defaultdict(lambda: defaultdict(list))
        for y in years[1:]:
            for gid, (ov, pot, gap) in dbg[y].items():
                prev = dbg.get(y - 1, {}).get(gid)
                if prev is None:
                    continue
                age = y - d['golfers'][gid]['born']
                row = d['rows'][y].get(gid)
                coached = 'paid coach' if row and row['deal'] == 'fee' else 'scouting coach' if row and row['deal'] == 'share' else 'no coach'
                band = '18-21' if age <= 21 else '22-25' if age <= 25 else '26-30' if age <= 30 else '31-35' if age <= 35 else '36+'
                change[band][coached].append(ov - prev[0])
        out += [f'## Seed {d["seed"]}: change in hidden overall per season, by age and coaching', '',
                '| Age | No coach | Paid coach | Scouting coach |', '|---|---|---|---|']
        for band in ('18-21', '22-25', '26-30', '31-35', '36+'):
            cells = [f'{S.mean(change[band][k]):+.2f} ({len(change[band][k])})' if change[band][k] else '—'
                     for k in ('no coach', 'paid coach', 'scouting coach')]
            out.append(f'| {band} | ' + ' | '.join(cells) + ' |')
        out += ['', '(Coached golfers are not a random sample — scouts pick fast improvers, payers are better off — '
                'so differences mix cause and selection.)', '']
    (out_dir / 'DEBUG.md').write_text('\n'.join(out) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, nargs='+', default=[2027, 3031, 4049])
    ap.add_argument('--years', type=int, default=25)
    ap.add_argument('--mature', type=int, default=12)
    ap.add_argument('--workers', type=int, default=None)
    ap.add_argument('--out', default=str(ROOT / 'reports' / 'long_world'))
    ap.add_argument('--report-only', action='store_true')
    ap.add_argument('--resume', action='store_true', help='continue interrupted seeds from their simulation saves')
    ap.add_argument('--save-every', type=int, default=1, help='seasons between simulation saves')
    ap.add_argument('--strict', action='store_true', help='exit non-zero if any check fails (integration gate)')
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if not a.report_only:
        commit, dirty = git_state()
        man = load_manifest(out)
        from golfsim.savegame import engine_id
        if man and (man.get('engine') or engine_id(man['commit'])) != engine_id():
            raise SystemExit(f'{out} holds checkpoints from another engine (commit {man.get("commit")}); use a new directory')
        if man and not a.resume and any(int(k) in a.seeds for k in man.get('seeds', {})):
            raise SystemExit(f'{out} already holds these seeds; pass --resume to continue them or use a new directory')
        from golfsim.savegame import engine_id as _eid
        man.update({'format': FORMAT, 'commit': commit, 'engine': _eid(), 'dirty': dirty, 'python': platform.python_version(),
                    'started': time.strftime('%Y-%m-%d %H:%M:%S'), 'years_requested': a.years,
                    'config': config(), 'mature': a.mature})
        man.setdefault('seeds', {})
        (out / 'manifest.json').write_text(json.dumps(man, indent=1, default=str))
        for seed in a.seeds:
            run_world(seed, a.years, a.workers, out, a.resume, a.save_every)
    man = load_manifest(out)
    seeds = [int(s) for s in man['seeds']] if a.report_only else a.seeds
    results = []
    for seed in seeds:
        d = load(out, seed)
        results.append({'d': d, 'a': analyse(d, min(a.mature, d['years']))})
    (out / 'REPORT.md').write_text(report(results, man, a.mature))
    debug_report(results, out)
    print('wrote', out / 'REPORT.md', 'and', out / 'DEBUG.md')
    if a.strict:
        bad = [(r['d']['seed'], y, c) for r in results for y, c in r['d']['checks'].items()
               if c['reconcile_errors'] or c['staff_violations'] or not c['population_ok']
               or abs(c['caddie_paid'] - c['caddie_received']) > 0.01 or abs(c['coach_paid'] - c['coach_received']) > 0.01]
        if bad:
            print('CHECKS FAILED:', bad)
            sys.exit(1)
        print('all checks passed')


if __name__ == '__main__':
    main()
