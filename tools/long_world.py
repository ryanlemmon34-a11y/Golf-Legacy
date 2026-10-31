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
    world_<s>/               --session: the persistent session itself (checkpoint generations, the
                             archive in world_<s>/archive, opened by tools/observer.py); every season is
                             skipped through the observer and timed (seed_<s>.json.gz 'perf');
                             seed_<s>.state.pkl and .pending.pkl let --resume continue exactly
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
import shutil
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
def major_order(key):
    """Chronological sort key for a recorded major, 'year:SERIES': the year, the week the engine's calendar
    plays that major (golfsim.calendar.MAJORS), then the series id (a stable tie-breaker). Never the
    display name."""
    from golfsim.calendar import MAJOR_ID_BY_WEEK
    y, sid = key.split(':')
    week = next((w for w, s in MAJOR_ID_BY_WEEK.items() if s == sid), 99)
    return int(y), week, sid


LEVEL = {1: 'Premier', 2: 'Challenger', 3: 'Regional', 4: 'Mini', 5: 'College', 6: 'Amateur', 9: '—'}
ROW = ('status', 'lifestyle', 'tier', 'next_tier', 'events', 'wins', 'wins_by_tier', 'majors', 'top10', 'cuts',
       'prize', 'net', 'cash', 'wr', 'am', 'injury_weeks', 'zero_start', 'coach', 'deal', 'caddie',
       'coaching', 'caddie_cost', 'sponsors', 'salary', 'work', 'support', 'living', 'event_costs',
       'play_wk', 'train_wk', 'rest_wk', 'work_wk', 'rounds', 'wanted_wk', 'shut_wk', 'declined', 'school_trips',
       'club_trips', 'backer_support', 'moving', 'home')
EXITS = ('retired', 'became coach', 'became caddie')


def git_state():
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--', 'golfsim'], cwd=ROOT, text=True).strip())
        return commit, dirty
    except Exception:
        return 'unknown', True


def analysis_note(man):
    """Which tools wrote a report, apart from which engine simulated the world: a report regenerated
    from saved data is a corrected analysis of the same world, not a new simulation."""
    try:
        head = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--', 'tools', 'golfsim'], cwd=ROOT,
                                             text=True).strip())
    except Exception:
        head, dirty = 'unknown', True
    sim = str(man.get('commit', '?'))[:7]
    if head != 'unknown' and sim.startswith(head[:7]) and not dirty:
        return f'Written by the run itself (tools and engine `{sim}`).'
    return (f'Analysis written from the run\'s saved data by the report tools at `{head}`'
            f'{" (with uncommitted changes)" if dirty else ""}; the world was simulated by engine `{sim}`. '
            'Re-generated analysis of the same world, not a new simulation.')


def config():
    from golfsim import careers as C, finance as F, staff as ST, population as P, development as D, residence as R
    return {'finance': {k: getattr(F, k) for k in ('LIVING', 'LIVING_WORKING', 'WORK_WAGE', 'CREDIT_BASE', 'CREDIT_SHARE',
                                                   'CREDIT_CAP', 'RESERVE_WEEKS', 'PRIOR_PRIZE_SHARE', 'CADDIE_SHARE',
                                                   'BACKER_SHARE', 'EVIDENCE_DECAY', 'PROVEN_EVENTS', 'SELF_FUNDED_SEASONS')},
            'residence': {k: getattr(R, k) for k in ('MOVE_COST', 'MIN_STAY', 'STAY_YEARS', 'HOME_PULL', 'MOVE_MARGIN',
                                                     'MOVE_SCALE', 'CADDIE_FOLLOWS', 'COACH_FOLLOWS', 'HOME_STATE_COLLEGE')},
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
    # family money falls only by what was drawn from it; backers' money (after they put up the season's
    # on 1 January) only by what was drawn and what went back to them when a deal ended
    pots = 0
    for gid, (backing0, funds0) in s.support_start.get(year, {}).items():
        l, g = led.get(gid), s.g[gid]
        back = s.backer_flows[year][(gid, 'returned')]
        pots += (abs(g.backing - (backing0 - (l.support if l else 0.0))) > 0.01
                 or abs(g.backer_funds - (funds0 - (l.backer_support if l else 0.0) - back)) > 0.01)
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
    # amateur support: each contract within its cap, its payments adding up to what it drew, and each golfer's
    # ledger line equal to the payments made for them
    sup_bad = 0
    for gid, c in getattr(s, 'am_support_seasons', {}).get(year, {}).items():
        sup_bad += c['drawn'] > c['cap'] + 0.01 or abs(sum(c['paid'].values()) - c['drawn']) > 0.5
    paid_for, n_paid = Counter(), Counter()
    for p in getattr(s, 'am_support_log', {}).get(year, ()):      # (each payment logged to the cent)
        paid_for[p['gid']] += p['amount']
        n_paid[p['gid']] += 1
    sup_bad += sum(1 for gid, l in led.items()
                   if abs(l.am_support - paid_for.get(gid, 0.0)) > 0.005 * n_paid.get(gid, 0) + 0.01)
    # development evidence: each golfer's recorded parts add up to their change in Overall (unrounded here)
    from golfsim import development as D
    dev_bad = 0
    for gid, v in getattr(s, 'dev_acc', {}).get(year, {}).items():
        o0 = s.overall_start.get(year, {}).get(gid)
        if o0 is None or not v[D.OV_PRE]:
            continue
        dev_bad += abs(v[D.OV_PRE] - o0 - sum(v[D.OVERALL + i] for i in range(4))) > 0.015
        dev_bad += bool(v[D.OV_POST]) and abs(v[D.OV_POST] - v[D.OV_PRE] - v[D.OVERALL + 4]) > 0.015
    exits = sum(1 for t in s.transitions.get(year, ()) if t['kind'] in EXITS)
    juniors = s.juniors_added.get(year + 1, 0) + s.new_pros_added.get(year + 1, 0)   # every arrival
    active_after = sum(1 for g in s.world.golfers if g.lifestyle != 'retired')
    return {'reconcile_errors': recon, 'support_errors': pots, 'caddie_paid': round(paid_caddie, 2), 'caddie_received': round(got_caddie, 2),
            'coach_paid': round(paid_coach, 2), 'coach_received': round(got_coach, 2), 'staff_violations': staff_bad,
            'active_before': active_before, 'exits': exits, 'juniors': juniors, 'active_after': active_after,
            'population_ok': active_before - exits + juniors == active_after,
            'support_cap_errors': sup_bad, 'development_errors': dev_bad,
            'work_pathway': len(getattr(s, 'work_pathway', {}).get(year, ())),
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
                     r['top10'], r['cuts'], round(r['prize']), round(led.net if led else r['net']), round(g.cash), r['wr_end'], r['am_end'],
                     r['injury_weeks'], r.get('zero_start_reason', ''), a.get('coach_of', {}).get(gid),
                     a.get('deal', {}).get(gid), a.get('caddie_of', {}).get(gid),
                     round(led.coaching + led.coach_share) if led else 0, round(led.caddie + led.caddie_share) if led else 0,
                     round(led.sponsors) if led else 0, round(led.salary) if led else 0, round(led.work) if led else 0,
                     round(led.support) if led else 0, round(led.living) if led else 0, round(led.events) if led else 0,
                     act.get('play', 0), act.get('train', 0), act.get('rest', 0), act.get('work', 0),
                     round(s.season_rounds[year].get(gid, 0), 1), s.entry_wants[year].get(gid, 0),
                     s.entry_misses[year].get(gid, 0), len(s.declined[year].get(gid, ())), s.school_trips[year].get(gid, 0),
                     s.club_trips[year].get(gid, 0), round(led.backer_support) if led else 0,
                     round(getattr(led, 'moving', 0.0)) if led else 0, s.home_country(g)]
        debug[gid] = [round(g.overall, 2), round(g.potential, 1),
                      round(sum(g.ceilings[k] - g.attrs[k] for k in g.attrs) / len(g.attrs), 2) if g.ceilings else None]
    return rows, debug


def stage(g, row, year):
    """A golfer's career stage for diagnostics: college, amateur, new professional (first three seasons),
    established professional, part-time, club professional."""
    if row['tour'].startswith('CO_'):
        return 'college'
    if row['status'] == 'amateur':
        return 'amateur'
    if row['status'] == 'club_pro':
        return 'club pro'
    if row['lifestyle'] == 'part_time':
        return 'part-time pro'
    return 'new pro' if g.turned_pro and year - g.turned_pro < 3 else 'established pro'


def season_extras(s, year, snap):
    """Per-season diagnostics kept beside the rows: competition access by career stage and tour (every
    golfer-week classified, financial barriers kept apart from injury, full fields and choice), money that
    moved, and the winter's relocations."""
    access = Counter()
    for gid, row in snap.items():
        g = s.g[gid]
        key = f'{stage(g, row, year)}|{row["tour"]}'
        for outcome, n in s.week_access.get(year, {}).get(gid, {}).items():
            access[f'{key}|{outcome}'] += n
        declined = len(s.declined[year].get(gid, ()))
        if declined:
            access[f'{key}|declined an invitation or place for cost'] += declined
    moves = [{'person': m['person'], 'from': list(m['from']) if m['from'] else None, 'to': list(m['to']),
              'reason': m['reason']} for m in s.move_log.get(year, [])]
    # every amateur's season, for the support comparison and the work pathway's excluded groups: (age, lifestyle,
    # in college, amateur rank at the end, events, longest count of genuinely cash-blocked weeks, support band,
    # support drawn, family money left, the week they took work by the pathway, region)
    from golfsim.season import region_of
    from golfsim import work_pathway as WP
    took = {t['gid']: t['week'] for t in getattr(s, 'work_pathway', {}).get(year, ())}
    held = getattr(s, 'am_support_seasons', {}).get(year, {})
    blocked = getattr(s, 'cash_blocked_max', {}).get(year, {})
    amateurs = {}
    for gid, row in snap.items():
        if row['status'] != 'amateur' and gid not in took:
            continue
        g, c = s.g[gid], held.get(gid)
        amateurs[gid] = (g.age(year), row['lifestyle'], row['tour'].startswith('CO_'), row.get('am_end'),
                         row['events'], blocked.get(gid, 0), c['band'] if c else None,
                         round(c['drawn']) if c else 0, g.backing > 0, took.get(gid), region_of(g))
    return {'access': dict(access), 'moves': moves, 'move_blocked': s.move_blocked.get(year, 0),
            'amateurs': amateurs,
            'flows': {f'{gid}:{k}': round(v, 2) for (gid, k), v in s.backer_flows.get(year, {}).items()},
            'stage': {gid: stage(s.g[gid], row, year) for gid, row in snap.items()}}


def collect(s, y, snap, active_before):
    """Everything this tool keeps about one completed season (before its snapshot is archived)."""
    rows, dbg = year_rows(s, y, snap)
    out = {'rows': rows, 'debug': dbg, 'checks': checks(s, y, snap, active_before),
           'transitions': s.transitions.get(y, []), 'unpaid': s.unpaid[y],
           'entry_stats': {t: dict(c) for t, c in s.entry_stats[y].items()},
           'number_one': next((gid for gid, r in snap.items() if r['wr_end'] == 1), None),
           'majors': {}, 'routes': {}, 'extras': season_extras(s, y, snap)}
    for m in MAJORS:
        r = s.results.get(f'{y}:{m}')
        if r and r.winner():
            out['majors'][f'{y}:{m}'] = r.winner()
        if (y, m) in s.entry_routes:
            out['routes'][f'{y}:{m}'] = Counter(s.entry_routes[(y, m)].values())
    return out


def merge(data, debug, y, c):
    data['rows'][y], debug['rows'][y] = c['rows'], c['debug']
    for k in ('checks', 'transitions', 'unpaid', 'entry_stats', 'number_one'):
        data[k][y] = c[k]
    data.setdefault('extras', {})[y] = c['extras']
    data['majors'].update(c['majors'])
    data['routes'].update(c['routes'])


def dir_bytes(p):
    return sum(f.stat().st_size for f in Path(p).rglob('*') if f.is_file()) if Path(p).exists() else 0


SEASON_LIMIT = 420.0             # seconds: a season above this stops the run (a runaway safeguard, not a target)
DISK_FLOOR = 3e9                 # bytes free below which the run stops
POPULATION_FLAG = 0.20           # active population moving more than this from its start: flagged, checked


def check_support(saved, asked, what):
    """A resumed run keeps the amateur-support setting its world was created with: a different flag on the
    command line is refused (never silently relabelled or switched)."""
    if bool(saved) != bool(asked):
        raise SystemExit(f'{what} was created with amateur support {"on" if saved else "off"}; resume it with '
                         f'{"no --no-amateur-support" if saved else "--no-amateur-support"}')


class Stop(Exception):
    """A long run's safeguard tripped: the run stops with what it has saved, and says why."""


def safeguards(data, y, ch, total, out, start_active):
    """The stopping conditions of docs/LONG_RUN_PLAN.md, after season y; a population flag is recorded."""
    if total > SEASON_LIMIT:
        raise Stop(f'season {y} took {total:.0f} s (limit {SEASON_LIMIT:.0f} s)')
    bad = {k: ch.get(k) for k in ('reconcile_errors', 'support_errors', 'support_cap_errors', 'development_errors',
                                   'staff_violations') if ch.get(k)}
    if abs(ch['caddie_paid'] - ch['caddie_received']) > 0.01 or abs(ch['coach_paid'] - ch['coach_received']) > 0.01:
        bad['staff_payments'] = True
    if not ch['population_ok']:
        bad['population_accounting'] = (ch['active_before'], ch['exits'], ch['juniors'], ch['active_after'])
    if bad:
        raise Stop(f'season {y}: a reconciliation failed {bad}')
    free = shutil.disk_usage(out).free
    if free < DISK_FLOOR:
        raise Stop(f'season {y}: {free / 1e9:.1f} GB free (floor {DISK_FLOOR / 1e9:.0f} GB)')
    change = ch['active_after'] / start_active - 1
    if abs(change) > POPULATION_FLAG:                 # a diagnostic flag: the accounting above already holds
        data.setdefault('flags', {})[y] = (f'active population {ch["active_after"]} is {change:+.0%} from its start '
                                           f'({start_active}); accounting reconciles (arrivals {ch["juniors"]}, '
                                           f'exits {ch["exits"]})')
        print(f'FLAG {data["flags"][y]}', flush=True)


def record_world_rules(data, season):
    """Per-world rule settings the report reads, recorded after a world is created or resumed (either mode): the
    work pathway's minimum age in force (rules 2026-11-10: 18 in new worlds; 21 in a world started earlier, which
    is also what the report assumes for a run that never recorded it)."""
    data['work_pathway_min_age'] = getattr(season, 'work_pathway_min_age', 21)


def run_world_session(seed, years, workers, out, resume=False, scale=1.0, amateur_support=True, keep_after=None):
    """Run (or resume) one world through the persistent weekly session and the observer, exactly as a
    player skips to the end of each season: the session's checkpoint generations are the resumable saves
    and its archive (world_<seed>/archive) the history. Each season is timed part by part (simulate, save,
    publish, observer reload, overview, first Records page), with the archive's and checkpoint's size."""
    import pickle
    from unittest import mock
    sys.path.insert(0, str(ROOT / 'tools'))
    import observer
    from golfsim import session as SES
    from golfsim.session import Session
    d = out / f'world_{seed}'
    state_path, pending_path = out / f'seed_{seed}.state.pkl', out / f'seed_{seed}.pending.pkl'
    t_start = time.perf_counter()
    if resume and (d / 'CURRENT').exists() and state_path.exists():
        with open(state_path, 'rb') as f:
            data, debug, created, initial = pickle.load(f)
        print(f'seed {seed}: resuming after {data["years"]} seasons', flush=True)
        check_support(data.get('amateur_support', True), amateur_support, f'seed {seed} (its saved run state)')
    else:
        if (d / 'CURRENT').exists():
            raise SystemExit(f'{d} already holds a world; pass --resume or use a new directory')
        from golfsim.population import generate_world
        s = Session.create(d, seed=seed, workers=workers, world=generate_world(seed=seed, scale=scale),
                           amateur_support=amateur_support)
        created = {g.id: s.season.first_year for g in s.season.world.golfers}
        initial = {g.id for g in s.season.world.golfers}
        data = {'format': FORMAT, 'seed': seed, 'first': s.season.first_year, 'years': 0, 'rows': {}, 'checks': {},
                'majors': {}, 'transitions': {}, 'routes': {}, 'unpaid': {}, 'number_one': {}, 'entry_stats': {},
                'extras': {}, 'perf': {}, 'session': True, 'amateur_support': amateur_support,
                'start_active': sum(1 for g in s.season.world.golfers if g.lifestyle != 'retired')}
        debug = {'format': FORMAT, 'seed': seed, 'rows': {}}
        s.close()
    w = observer.World(d)
    check_support(getattr(w.session.season, 'amateur_support_on', True), amateur_support, f'seed {seed} (its world)')
    record_world_rules(data, w.session.season)
    first = data['first']
    if pending_path.exists():                       # a season captured but not yet merged when the run stopped
        with open(pending_path, 'rb') as f:
            y, c = pickle.load(f)
        if y == first + data['years'] and w.session.cursor['year'] > y:      # it was committed: keep it
            merge(data, debug, y, c)
            data['years'] = y - first + 1
        pending_path.unlink()
    captured = {}

    def hook(season, year):
        c = collect(season, year, season.snapshots[year], captured['active_before'])
        captured[year] = c
        with open(pending_path, 'wb') as f:
            pickle.dump((year, c), f)
    while data['years'] < years:
        sess = w.session
        sess.on_season_end = hook
        c = sess.cursor
        y = c['year']
        captured['active_before'] = sum(1 for g in sess.season.world.golfers if g.lifestyle != 'retired')
        parts = {}
        real_commit, real_publish = Session._commit, SES._publish_archive

        def timed_commit(self, *a, **k):
            t = time.perf_counter()
            real_commit(self, *a, **k)
            parts['save+publish'] = parts.get('save+publish', 0.0) + time.perf_counter() - t

        def timed_publish(*a, **k):
            t = time.perf_counter()
            real_publish(*a, **k)
            parts['publish'] = parts.get('publish', 0.0) + time.perf_counter() - t
        form = {'weeks': ['season'], 'year': [str(y)], 'week': [str(c['week'])], 'phase': [c['phase']],
                'op': [f'long-{seed}-{y}']}
        t_reload = [0.0]
        real_reload = w.reload

        def timed_reload():
            t = time.perf_counter()
            real_reload()
            t_reload[0] = time.perf_counter() - t
        t0 = time.perf_counter()
        with mock.patch.object(Session, '_commit', timed_commit), mock.patch.object(SES, '_publish_archive', timed_publish):
            w.reload = timed_reload
            w.submit(form)
            w.reload = real_reload
        t1 = time.perf_counter()
        observer.overview(w, {})
        t2 = time.perf_counter()
        observer.record(w, {}, 'most-wins')
        t3 = time.perf_counter()
        if y not in captured:
            raise SystemExit(f'seed {seed}: season {y} did not complete')
        merge(data, debug, y, captured.pop(y))
        s = w.session.season
        for g in s.world.golfers:
            created.setdefault(g.id, y + 1)
        data['years'] = y - first + 1
        total = t1 - t0 + (t2 - t1)
        sp = parts.get('save+publish', 0.0)
        data['perf'][y] = {'skip': round(total, 1), 'simulate': round(t1 - t0 - sp - t_reload[0], 1),
                           'save': round(sp - parts.get('publish', 0.0), 1), 'publish': round(parts.get('publish', 0.0), 1),
                           'reload': round(t_reload[0], 2), 'overview': round(t2 - t1, 2), 'records': round(t3 - t2, 2),
                           'active': len(s.active_golfers()), 'people': len(s.world.golfers),
                           'archive_mb': round(dir_bytes(d / 'archive') / 1e6, 1),
                           'checkpoint_mb': round(dir_bytes(d / f'gen_{w.session.generation:06d}') / 1e6, 1)}
        ch = data['checks'][y]
        print(f'seed {seed}: {y} done ({data["years"]}/{years}), {ch["active_after"]} active, reconcile errors '
              f'{ch["reconcile_errors"]}+{ch.get("support_errors", 0)}, staff violations {ch["staff_violations"]}, '
              f'population {"ok" if ch["population_ok"] else "MISMATCH"}, skip {total:.0f} s '
              f'(save {data["perf"][y]["save"]} s, publish {data["perf"][y]["publish"]} s), '
              f'{time.perf_counter() - t_start:.0f} s', flush=True)
        with open(str(state_path) + '.tmp', 'wb') as f:
            pickle.dump((data, debug, created, initial), f)
        Path(str(state_path) + '.tmp').replace(state_path)
        if pending_path.exists():
            pending_path.unlink()
        last = data['years'] >= years
        if data['years'] % 5 == 0 or last:
            save(s, data, debug, created, initial, out, t_start)
        if keep_after and data['years'] == keep_after:   # the determinism check's starting point (a copy)
            w.session.close()
            shutil.copytree(d, out / f'world_{seed}_after{keep_after}')
            w = observer.World(d)
        if keep_after and data['years'] == keep_after + 1:   # what the replay must reproduce
            sys.path.insert(0, str(ROOT / 'tools'))
            import equivalence_check as EQ
            data['determinism'] = {'season': y, 'parts': EQ.parts(w.session, d)}
            with open(str(state_path) + '.tmp', 'wb') as f:
                pickle.dump((data, debug, created, initial), f)
            Path(str(state_path) + '.tmp').replace(state_path)
        try:
            safeguards(data, y, ch, total, out, data.get('start_active') or ch['active_before'])
        except Stop as e:
            data['stopped'] = str(e)
            with open(str(state_path) + '.tmp', 'wb') as f:
                pickle.dump((data, debug, created, initial), f)
            Path(str(state_path) + '.tmp').replace(state_path)
            save(s, data, debug, created, initial, out, t_start)
            w.session.close()
            print(f'STOP seed {seed}: {e}', flush=True)
            raise SystemExit(3)
    w.session.close()


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
                'majors': {}, 'transitions': {}, 'routes': {}, 'unpaid': {}, 'number_one': {}, 'entry_stats': {}}
        debug = {'format': FORMAT, 'seed': seed, 'rows': {}}
        arch_created = None
    first = data['first']
    record_world_rules(data, s)
    archive = ArchiveWriter(out / f'archive_{seed}', s)
    if arch_created:
        archive.created, archive.initial = arch_created, initial
    for y in range(first + data['years'], first + years):
        active_before = sum(1 for g in s.world.golfers if g.lifestyle != 'retired')
        s.run_year(y)
        archive.write_year(s, y)                            # the durable history, before the snapshot goes
        snap = s.snapshots.pop(y)
        merge(data, debug, y, collect(s, y, snap, active_before))
        for g in s.world.golfers:
            created.setdefault(g.id, y + 1)
        data['years'] = y - first + 1
        c = data['checks'][y]
        print(f'seed {seed}: {y} done ({data["years"]}/{years}), {c["active_after"]} active, '
              f'reconcile errors {c["reconcile_errors"]}+{c.get("support_errors", 0)}, staff violations {c["staff_violations"]}, '
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
    d['extras'] = {int(y): v for y, v in d.get('extras', {}).items()}
    d['perf'] = {int(y): v for y, v in d.get('perf', {}).items()}
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
    # competition access for everyone still playing (amateurs and college too), and competitive rounds
    access, levels, rounds = Counter(), Counter(), defaultdict(list)
    for y in years[1:]:                                          # the first season starts from a seeded world
        for r in d['rows'][y].values():
            lv = LEVEL.get(r['tier'], '—') + (' (part-time)' if r['lifestyle'] == 'part_time' else '')
            levels[lv] += 1
            rounds[lv].append(r.get('rounds', 0))
            if r['events'] == 0:
                access[(lv, r['zero_start'])] += 1
    a['access'], a['levels'], a['rounds'] = access, levels, rounds
    shut = defaultdict(Counter)                                  # by the golfer's own level (membership)
    for y in years[1:]:
        for r in d['rows'][y].values():
            if r.get('wanted_wk'):
                lv = LEVEL.get(r['tier'], '—') + (' (part-time)' if r['lifestyle'] == 'part_time' else '')
                shut[lv]['wanted'] += r['wanted_wk']
                shut[lv]['shut out'] += r['shut_wk']
    a['entry'] = shut
    a['declined'] = sum(r.get('declined', 0) for y in years for r in d['rows'][y].values())
    a['school_trips'] = sum(r.get('school_trips', 0) for y in years for r in d['rows'][y].values())
    a['club_trips'] = sum(r.get('club_trips', 0) for y in years for r in d['rows'][y].values())
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
    for k, w in sorted(d['majors'].items(), key=lambda kw: major_order(kw[0])):
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


WIN_LEVEL = {**LEVEL, 8: 'club professional (section)'}
MILESTONE_LOGS = ('Arrived on the scene', 'Turned professional', 'Stopped chasing', 'Retired from competitive',
                  'Took a job', 'Became a caddie', 'Became a coach', 'Became a club', 'College eligibility ended',
                  'Reinstated', 'Returned to', 'Moved to', 'Moved back')


def milestones(d, a, gid, best_week=None, limit=16):
    """A career told by its milestones, in order: arrival and turning professional, each new level
    reached, the first win, the first win at each level, majors, world No. 1, career changes and comebacks
    (recorded results and decisions only; never the first lines of a log that may be all early travel)."""
    tl, g = a['_tl'][gid], d['golfers'][gid]
    out = []
    if g['initial']:
        out.append((d['first'], 0, 'In the starting world (career before the archive unknown)'))
    for y, text in g['history']:
        if text.startswith(MILESTONE_LOGS):
            out.append((y, 1, text))
    seen_level, won_any, won_level = set(), False, set()
    for y in sorted(tl):
        r = tl[y]
        if full_time(r) and r['tier'] not in seen_level and (not seen_level or r['tier'] < min(seen_level)):
            out.append((y, 2, f'First full-time season at {LEVEL.get(r["tier"], "?")} level'))
        if full_time(r):
            seen_level.add(r['tier'])
        for tier, n in sorted(r['wins_by_tier'].items()):
            if n and tier not in won_level and tier != 0:            # (majors, tier 0, are listed below)
                won_level.add(tier)
                out.append((y, 3, ('First win, at ' if not won_any else 'First win at ') + f'{WIN_LEVEL.get(tier, "?")} level'
                            + (f' ({n} that season)' if n > 1 else '')))
                won_any = True
    majors = [(int(k.split(':')[0]), MAJOR_NAME[k.split(':')[1]])        # in the order they were played
              for k in sorted((k for k, w in d['majors'].items() if w == gid), key=major_order)]
    for i, (y, m) in enumerate(majors):
        out.append((y, 4, f'Won the {m} (major No. {i + 1})'))
    no1 = sorted(y for y, w in d['number_one'].items() if w == gid)
    if no1:
        out.append((no1[0], 5, f'World No. 1 at a season\'s end for the first time ({len(no1)} season ends in all)'))
    for y in sorted(d['transitions']):
        for t in d['transitions'][y]:
            if t['gid'] == gid and t['kind'] == 'comeback':
                out.append((y, 6, f'Came back to full-time golf at {t.get("age", "?")}'))
    out.sort(key=lambda x: (x[0], x[1]))
    keep = out if len(out) <= limit else out[:limit - 1] + [out[-1]]   # the latest milestone always shown
    wins = sum(sum(r['wins_by_tier'].values()) for r in tl.values())
    lines = [f'  - {y}: {text}' for y, _, text in keep]
    if len(out) > limit:
        lines.insert(limit - 1, f'  - … {len(out) - limit} more milestones')
    seasons = sum(1 for r in tl.values() if full_time(r))
    lines.append(f'  - In all: {seasons} full-time professional seasons in the archive, {wins} wins at every level '
                 f'(amateur and college included), {len(majors)} majors'
                 + (f', best weekly world ranking {best_week[gid]}' if best_week and gid in best_week else ''))
    return lines


def interesting(d, a, n=6, best_week=None):
    """Careers picked by rules on recorded results (not by hidden ability). Golfers already in the
    starting world are not 'late bloomers' (their careers began before the archive)."""
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
    late = [gid for gid in eps if not g[gid]['initial'] and best[gid] == 1
            and min(y for y in tl[gid] if full_time(tl[gid][y]) and tl[gid][y]['tier'] == 1) - g[gid]['born'] >= 31]
    add('Late bloomer (arrived in the world, first Premier season at 31+)', min(late) if late else None)
    cbs = [gid for gid, e in eps.items() if len(e) > 1 and min(tl[gid][y]['tier'] for y in range(e[1][0], e[-1][1] + 1) if y in tl[gid])
           < min(tl[gid][y]['tier'] for y in range(e[0][0], e[0][1] + 1))]
    add('A comeback that went further than before', min(cbs) if cbs else None)
    add('Longest full-time career', max(a['_length'], key=lambda x: (a['_length'][x], -x)) if a['_length'] else None)
    out = []
    for label, gid in picks[:n]:
        out.append(f'- **{label} — {name(d, gid)}**, born {g[gid]["born"]}:')
        out += milestones(d, a, gid, best_week)
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
           analysis_note(man), '',
           f'Engine commit `{man.get("commit", "?")}`' + (' (**uncommitted engine changes present**)' if man.get('dirty') else '')
           + f', format `{FORMAT}`. Seeds and seasons completed: '
           + ', '.join(f'{s} ({man["seeds"][str(s)]["years_completed"]})' for s in seeds) + '. '
           'Every shot simulated. This report contains no hidden attributes (see DEBUG.md).', '',
           '## 1. Checks (every season)', '', head, sep,
           row('Seasons with cash not reconciling', lambda a, d: str(sum(1 for c in d['checks'].values() if c['reconcile_errors']))),
           row('Seasons with family or backers\' money not reconciling',
               lambda a, d: str(sum(1 for c in d['checks'].values() if c.get('support_errors')))),
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
    out += ['', '## 3b. Competition access for everyone playing (season two on)', '',
            'Seasons with no start, by level and recorded reason (blocked: full fields, no affordable trip, no '
            'eligible event; or choice), and the weeks golfers wanted to play a regular event, by their own level: '
            'the share shut out of every field they tried (majors and invitations are chosen by the event and not '
            'counted here). Competitive rounds per season: 10th / median / 90th percentile.', '',
            head, sep]
    lvls = sorted({lv for a in A for lv in a['levels']})
    for lv in lvls:
        out.append(row(f'{lv}: competitive rounds', lambda a, d, lv=lv: dist(a['rounds'].get(lv, []))))
        for why in sorted({w for a in A for (l, w) in a['access'] if l == lv}):
            out.append(row(f'{lv}: no start — {why}', lambda a, d, lv=lv, why=why: pct(a['access'][(lv, why)], a['levels'][lv])))
    for lv in sorted({lv for a in A for lv in a['entry']}):
        out.append(row(f'{lv} entries: weeks wanted / shut out',
                       lambda a, d, lv=lv: f'{a["entry"][lv]["wanted"]:,} / {pct(a["entry"][lv]["shut out"], a["entry"][lv]["wanted"])}'))
    out += [row('Invitations and qualified places declined for cost', lambda a, d: f'{a["declined"]:,}'),
            row('Events paid for by a school', lambda a, d: f'{a["school_trips"]:,}'),
            row('Events paid for by a club', lambda a, d: f'{a["club_trips"]:,}')]
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
        names = [f'{k.split(":")[0]} {MAJOR_NAME[k.split(":")[1]]}: {name(d, w)}' for k, w in sorted(d['majors'].items(), key=lambda kw: major_order(kw[0]))
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
        # development by competitive rounds played (golfers with room to grow: 3+ points below ceilings)
        byr = defaultdict(lambda: defaultdict(list))
        bands = ((0, 0, 'none'), (0.1, 20, '1-20'), (20.1, 40, '21-40'), (40.1, 80, '41-80'), (80.1, 1e9, '80+'))
        for y in sorted(dbg):
            for gid, (ov, pot, gap) in dbg[y].items():
                prev = dbg.get(y - 1, {}).get(gid)
                row = d['rows'][y].get(gid)
                if prev is None or row is None or prev[2] is None or prev[2] < 3:
                    continue
                age = y - d['golfers'][gid]['born']
                if not 18 <= age <= 30:
                    continue
                rd = row.get('rounds', 0)
                band = next(n for lo, hi, n in bands if lo <= rd <= hi)
                byr['18-23' if age <= 23 else '24-30'][band].append(ov - prev[0])
        out += [f'## Seed {d["seed"]}: change in hidden overall per season by competitive rounds played (ages 18-30, '
                '3+ points below their ceilings)', '', '| Age | ' + ' | '.join(n for _, _, n in bands) + ' |',
                '|---|' + '---|' * len(bands)]
        for band in ('18-23', '24-30'):
            out.append(f'| {band} | ' + ' | '.join(f'{S.mean(byr[band][n]):+.2f} ({len(byr[band][n])})' if byr[band][n] else '—'
                                                  for _, _, n in bands) + ' |')
        out += ['', '(Selection again: golfers who play more are also the ones with cards, money and form.)', '']
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
    ap.add_argument('--scale', type=float, default=1.0, help='population scale (1 = the full world; smaller only '
                    'to try the tool)')
    ap.add_argument('--session', action='store_true', help='run through the persistent session and the observer, '
                    'timing every season skip (the long test)')
    ap.add_argument('--no-amateur-support', action='store_true', help='the comparison arm: the same build and rules '
                    'with amateur support switched off (session mode, new worlds only)')
    ap.add_argument('--keep-after', type=int, default=None, help='copy the world after this many seasons and record '
                    'the next season\'s digests, for a determinism replay (tools/determinism_replay.py)')
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
        if man and 'amateur_support' in man:                 # a resume keeps the folder's recorded setting
            check_support(man['amateur_support'], not a.no_amateur_support, str(out))
        from golfsim.savegame import engine_id as _eid
        sys.path.insert(0, str(ROOT / 'tools'))
        from benchmark_skip import machine
        man.update({'format': FORMAT, 'commit': commit, 'engine': _eid(), 'dirty': dirty, 'python': platform.python_version(),
                    'machine': machine(),
                    'started': time.strftime('%Y-%m-%d %H:%M:%S'), 'years_requested': a.years,
                    'config': config(), 'mature': a.mature, 'amateur_support': not a.no_amateur_support})
        man.setdefault('seeds', {})
        (out / 'manifest.json').write_text(json.dumps(man, indent=1, default=str))
        for seed in a.seeds:
            if a.session:
                run_world_session(seed, a.years, a.workers, out, a.resume, a.scale, not a.no_amateur_support,
                                  a.keep_after)
            else:
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
               if c['reconcile_errors'] or c.get('support_errors') or c['staff_violations'] or not c['population_ok']
               or abs(c['caddie_paid'] - c['caddie_received']) > 0.01 or abs(c['coach_paid'] - c['coach_received']) > 0.01]
        if bad:
            print('CHECKS FAILED:', bad)
            sys.exit(1)
        print('all checks passed')


if __name__ == '__main__':
    main()
