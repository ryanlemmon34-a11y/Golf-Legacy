#!/usr/bin/env python3
"""Controlled same-seed comparison of the comparison arms (pinned build c0d1ea5): writes ARMS_COMPARISON.md.

    nice -n 19 python3 analyze.py                         # default folders below; partial results are labelled
    nice -n 19 python3 analyze.py --arms a21old=DIR a18old=DIR a18new=DIR seed2=DIR --out ARMS_COMPARISON.md
    nice -n 19 python3 analyze.py --stories               # also (re)time story assembly on the pinned long archive

READ-ONLY on every run folder: only manifest.json, the run state (seed_<s>.state.pkl / seed_<s>.json.gz) and the
archive files its MANIFEST.json names are opened, for reading. No World, Session or Archive object is opened on an
arm. Seasons used: those both merged in the run state and published in the archive at read time. Season summaries
are cached in armsan/cache (keyed by the immutable season file name), so a rerun decodes only new seasons.
Story timing (section 4) runs in its own process (stories_timing.py) and is kept in armsan/story_timing.json;
without --stories the last measurement is reported.
"""
from __future__ import annotations

import argparse
import json
import statistics as S
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import extract as X                                                    # noqa: E402

V18 = HERE.parent
DEFAULT_BUILD = V18 / 'arms' / 'build_c0d1ea5'
DEFAULT_ARMS = {k: V18 / 'arms' / k for k in ('a21old', 'a18old', 'a18new', 'seed2')}
DEFAULT_STORY_ARCHIVE = V18 / 'runs' / 'A' / 'world_360013' / 'archive'
# what each arm's sections read of the season summaries (the rest is dropped after loading, to keep memory modest)
_COMMON = {'prestige', 'created', 'arrival_log', 'venue_sites', 'ar_ev', 'aj_ev', 'cash_blocked_max', 'work_pathway', 'transitions',
           'careers'}
KEEP = {'a21old': {'plans', 'careers', 'transitions', 'work_pathway', 'oo', 'open_starts', 't5_starts', 'start_weeks'} | _COMMON,
        'a18old': {'plans', 'careers', 'transitions', 'work_pathway', 'oo', 'open_starts', 't5_starts', 'start_weeks'} | _COMMON,
        'a18new': {'careers', 'transitions', 'work_pathway', 'oo', 'open_starts', 't5_starts', 'weather',
                   'all_starts', 'familiar_base', 'home_floor_starts'} | _COMMON,
        'seed2': {'careers', 'transitions', 'weather', 'all_starts', 'familiar_base', 'home_floor_starts'} | _COMMON}
REQUESTED = {'a21old': 10, 'a18old': 10, 'a18new': 10, 'seed2': 5}


# ---- formatting ----------------------------------------------------------------------------------------------------
def pct(a, b, d=1):
    return '—' if not b else f'{100 * a / b:.{d}f}%'


def frac(a, b, d=1):
    return f'{a}/{b} ({pct(a, b, d)})' if b else f'{a}/0'


def per(a, b, d=2):
    return '—' if not b else f'{a / b:.{d}f}'


def q(xs, p):
    xs = sorted(xs)
    if not xs:
        return float('nan')
    k = (len(xs) - 1) * p
    lo = int(k)
    return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (k - lo)


def dist(xs, d=0):
    xs = [x for x in xs if x is not None]
    if not xs:
        return '—'
    f = lambda v: f'{v:.{d}f}'
    return f'{f(min(xs))} / {f(q(xs, .25))} / {f(q(xs, .5))} / {f(q(xs, .75))} / {f(max(xs))} (n={len(xs)})'


def table(head, rows):
    out = ['| ' + ' | '.join(map(str, head)) + ' |', '|' + '---|' * len(head)]
    out += ['| ' + ' | '.join('' if c is None else str(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)


def band(age):
    return '<18' if age < 18 else '18-20' if age <= 20 else '21+'


def seasons_label(arm):
    s = arm['seasons']
    if not s:
        return f'{arm["name"]}: no committed season'
    req = REQUESTED.get(arm['name'], arm['man'].get('years_requested'))
    part = '' if len(s) >= (req or 0) else f' — PARTIAL ({len(s)} of {req})'
    return f'{arm["name"]}: seasons {s[0]}–{s[-1]} ({len(s)}){part}'


# ---- divergence ------------------------------------------------------------------------------------------------------
def divergence(a, b):
    """Per season, how many golfer rows (long_world year_rows: results, money, staff, activity) are identical."""
    out = []
    common = [y for y in a['seasons'] if y in b['seasons']]
    for y in common:
        ra, rb = a['data']['rows'][y], b['data']['rows'][y]
        ka, kb = set(ra), set(rb)
        both = ka & kb
        same = sum(1 for g in both if list(ra[g]) == list(rb[g]))
        out.append((y, len(ka), len(kb), len(both), same))
    return out


# ---- section 1: the pathway's age --------------------------------------------------------------------------------
def tracked_rows(arm, y):
    """Full-time non-college amateurs this season (extras 'amateurs'; a pathway entrant is part-time by the season's end
    but was tracked until the week they took work)."""
    out = {}
    for g, r in arm['data']['extras'].get(y, {}).get('amateurs', {}).items():
        age, life, college, rank, events, blocked, sband, drawn, fam, took, region = r
        if college:
            continue
        if life == 'full_time' or took is not None:
            out[int(g)] = {'age': age, 'events': events, 'blocked': blocked, 'took': took, 'rank': rank,
                           'support': sband, 'family': fam, 'region': region, 'life': life}
    return out


def weeks_timeline(arm):
    """gid -> {absolute week: (availability, injured)} from the monthly plans' recorded availability."""
    first = arm['seasons'][0] if arm['seasons'] else 0
    tl = defaultdict(dict)
    for y in arm['seasons']:
        for g, plans in arm['summ'][y]['plans'].items():
            for w0, avail, _plan, inj in plans:
                for k, a in enumerate(avail):
                    wk = w0 + k
                    if wk > 52:
                        continue
                    tl[g][(y - first) * 52 + wk] = (a, k < (inj or 0))
    return tl, first


def time_to_job(arm, tl, first, rec):
    """Plan-based reconstruction (monthly-plan availability, not actual weekly access). Walking back from the decision
    week as work_pathway.count would read these weeks ('unaff' counts, 'none'/'inelig'/injured pause, anything else
    resets): (span of the last n compatible counted weeks to the job, counted weeks found before stopping at the
    recorded n, the recorded n, weeks without a recorded plan inside that span, the full compatible run -- scanning on
    past n until a reset or the start of the data -- and whether that full scan reached the start of the data)."""
    g, y, wk, n = rec['gid'], rec['year'], rec['week'], rec['weeks_blocked']
    j = (y - first) * 52 + wk
    t = tl.get(g, {})
    found, firstw, unknown, full, hit_start = 0, None, 0, 0, True
    a = j - 1
    lo = (arm['seasons'][0] - first) * 52 + 1
    while a >= lo:
        v = t.get(a)
        if v is None:
            if found < n:
                unknown += 1
        else:
            av, inj = v
            if inj or av in ('none', 'inelig'):
                pass
            elif av == 'unaff':
                full += 1
                if found < n:
                    found += 1
                    firstw = a
            else:
                hit_start = False
                break
        a -= 1
    return (j - firstw if firstw is not None else None), found, n, unknown, full, hit_start


def later_outcome(arm, g, y):
    """The first career transition of golfer g in the winter after season y or later, within the committed run."""
    for yy in arm['seasons']:
        if yy < y:
            continue
        for t in arm['summ'][yy]['transitions']:
            if t.get('gid') == g:
                return f'{t["kind"]} ({yy})'
    last = arm['seasons'][-1]
    c = arm['summ'][last]['careers'].get(g)
    if c is None:
        return 'not in the last season'
    return f'no transition: {c["status"]} {c["lifestyle"]} at {last}'


def outcome_kind(s):
    return s.split(' (')[0] if '(' in s else s.split(' at ')[0]


def follow(arm, g, y):
    """(starts in y, starts in y+1, overall change over y+1, outcome) -- None where y+1 is not committed."""
    s = arm['summ']
    c0 = s[y]['careers'].get(g)
    c1 = s[y + 1]['careers'].get(g) if (y + 1) in s else None
    st0 = c0['events'] if c0 else None
    st1 = c1['events'] if c1 else (None if (y + 1) not in s else 0)
    dev = (c1['overall'] - c0['overall']) if (c0 and c1 and c0['overall'] is not None and c1['overall'] is not None) else None
    return st0, st1, dev, later_outcome(arm, g, y)


def same_person(a, b, g):
    pa, pb = a['people'].get(g), b['people'].get(g)
    return bool(pa and pb and pa['name'] == pb['name'] and pa['born'] == pb['born'] and pa['country'] == pb['country'])


def row_fields():
    """long_world.ROW: the run state's golfer-row columns (read from the pinned build's tool, nothing run)."""
    sys.path.insert(0, str(Path(DEFAULT_BUILD) / 'tools'))
    import long_world as LW
    return LW.ROW


STATUSES = ('pro, full-time', 'pro, part-time', 'club pro', 'amateur, full-time', 'amateur, part-time', 'college',
            'retired', 'staff (coach or caddie)', 'dead', 'not recorded')
EXIT_KINDS = {'retired': 'retired', 'became coach': 'staff (coach or caddie)', 'became caddie': 'staff (coach or caddie)'}


def status_at(arm, g, y):
    """A golfer's status at the end of season y: their season row (season file `careers`) before that winter's
    decisions; a golfer with no active row that season is classified by the last exit recorded in an earlier
    winter's transitions (retired, became coach / caddie) or by a death recorded before the season."""
    p = arm['people'].get(g) or {}
    c = arm['summ'][y]['careers'].get(g)
    if c is not None and c['lifestyle'] != 'retired':
        if c['status'] == 'pro':
            return 'pro, full-time' if c['lifestyle'] == 'full_time' else 'pro, part-time'
        if c['status'] == 'club_pro':
            return 'club pro'
        if c['status'] == 'amateur':
            if c['tour'].startswith('CO_'):
                return 'college'
            return 'amateur, full-time' if c['lifestyle'] == 'full_time' else 'amateur, part-time'
        return 'not recorded'
    if p.get('died') is not None and p['died'] < y:
        return 'dead'
    last = None
    for yy in arm['seasons']:
        if yy > y or (yy == y and c is not None):
            break
        for t in arm['summ'][yy]['transitions']:
            if t.get('gid') == g and t['kind'] in EXIT_KINDS:
                last = EXIT_KINDS[t['kind']]
    if last is None and c is not None:
        return 'retired'
    return last or 'not recorded'


def cohort_outcomes(arm, ids, seasons):
    """Per-arm outcomes of a fixed group over `seasons` (denominator: the group's size)."""
    last = seasons[-1]
    st = Counter(status_at(arm, g, last) for g in ids)
    starts = {g: sum((arm['summ'][y]['careers'].get(g) or {}).get('events', 0) or 0 for y in seasons) for g in ids}
    zero_seasons = active_seasons = 0
    zero_golfers = set()
    for y in seasons:
        for g in ids:
            c = arm['summ'][y]['careers'].get(g)
            if c is None or c['lifestyle'] == 'retired':
                continue
            active_seasons += 1
            if c['events'] == 0:
                zero_seasons += 1
                zero_golfers.add(g)
    ids_set = set(ids)
    entries = [r for y in seasons for r in arm['summ'][y]['work_pathway'] if r['gid'] in ids_set]
    overall = [arm['summ'][last]['careers'][g]['overall'] for g in ids
               if g in arm['summ'][last]['careers'] and arm['summ'][last]['careers'][g]['overall'] is not None]
    return {'status': st, 'starts': starts, 'zero_seasons': zero_seasons, 'active_seasons': active_seasons,
            'zero_golfers': len(zero_golfers), 'entrants': len({r['gid'] for r in entries}), 'entries': entries,
            'overall': overall}


def cohort_table(arms_out, N, last):
    names = list(arms_out)
    rows = [(f'status at the end of {last}: {k}', *[frac(o['status'].get(k, 0), N) for o in arms_out.values()])
            for k in STATUSES if any(o['status'].get(k) for o in arms_out.values())]
    rows.append(('starts, cumulative (min/q1/med/q3/max)', *[dist(list(o['starts'].values())) for o in arms_out.values()]))
    rows.append(('starts, total', *[f'{sum(o["starts"].values()):,}' for o in arms_out.values()]))
    rows.append(('golfers with any zero-start season', *[frac(o['zero_golfers'], N) for o in arms_out.values()]))
    rows.append(('zero-start seasons / seasons with an active row', *[frac(o['zero_seasons'], o['active_seasons'])
                                                                      for o in arms_out.values()]))
    rows.append(('golfers who entered the pathway', *[frac(o['entrants'], N) for o in arms_out.values()]))
    rows.append(('pathway entries (ages at entry)', *[f'{len(o["entries"])} (' + ', '.join(
        f'{a}: {n}' for a, n in sorted(Counter(r["age"] for r in o["entries"]).items())) + ')' for o in arms_out.values()]))
    rows.append((f'Overall at the end of {last} (golfers with a {last} row)', *[dist(o['overall'], 1) for o in arms_out.values()]))
    return table(['outcome (denominator: the fixed cohort, N = ' + f'{N})', *names], rows)


STATUS_NOTE = ('Status at the end of {last} is the golfer\'s {last} season row before that winter\'s decisions; a golfer '
               'with no active row is classified by the exit recorded in an earlier winter (retired, became coach or '
               'caddie) or a recorded death. Starts and zero-start seasons count every season the golfer had an active '
               'row, whatever their status that season.')


def cohort_block(a21, a18, lines, title, intro, ids, seasons, by_age_year):
    N, last = len(ids), seasons[-1]
    lines.append(title)
    lines.append('')
    lines.append(intro)
    lines.append('')
    lines.append(f'N = {N} (by age in {by_age_year}: ' + ', '.join(f'{a}: {n}' for a, n in sorted(Counter(
        by_age_year - a21['people'][g]['born'] for g in ids).items())) + f'). Outcomes over seasons {seasons[0]}–{last}; '
                 'denominator N in both columns (the same people).')
    lines.append('')
    if not N:
        return
    out = {'a21old': cohort_outcomes(a21, ids, seasons), 'a18old': cohort_outcomes(a18, ids, seasons)}
    lines.append(cohort_table(out, N, last))
    lines.append('')
    lines.append(STATUS_NOTE.format(last=last))
    lines.append('')


def original_cohort(a21, a18, lines):
    """Three fixed cohorts, never pooled: (b) pretreatment from the shared first season, (c) the next season's arrivals
    by their creation record, (a) a cohort selected by the control arm's end-of-second-season status."""
    common = [y for y in a21['seasons'] if y in a18['seasons']]
    if len(common) < 2:
        lines += ['### Fixed cohorts', '', 'Needs two committed seasons in both arms.', '']
        return []
    ROW = row_fields()
    yb, y0 = common[0], common[1]
    rb21, rb18 = a21['data']['rows'][yb], a18['data']['rows'][yb]
    base_same = sum(1 for g in rb21 if g in rb18 and list(rb21[g]) == list(rb18[g]))
    r21, r18 = a21['data']['rows'][y0], a18['data']['rows'][y0]
    diff = sorted(g for g in set(r21) & set(r18) if list(r21[g]) != list(r18[g]))
    lines.append('The three fixed-cohort tables below each describe the same people under each arm\'s rule, as recorded. None of them shows a '
                 'guaranteed rescue or a causal effect on any individual\'s career; differences between the columns are '
                 'arm-level differences within the stated group (the worlds diverge from 2028, so other people and '
                 'events differ too).')
    lines.append('')
    seasons = [y for y in common if y >= y0]

    # (b) PRETREATMENT: the shared first season, identical in both arms
    cb = a21['summ'][yb]['careers']
    ids_b, exc_b = [], Counter()
    for g, row in rb21.items():
        d = dict(zip(ROW, row))
        p = a21['people'].get(g) or {}
        if d['status'] != 'amateur' or not p.get('born') or not 17 <= yb - p['born'] <= 20:
            continue
        if g not in rb18 or list(rb18[g]) != list(row) or not same_person(a21, a18, g):
            exc_b['not identical in both arms'] += 1
            continue
        c = cb.get(g)
        if c is None or c['tour'].startswith('CO_'):
            exc_b['in college' if c else 'no season-file record'] += 1
            continue
        if d['lifestyle'] != 'full_time':
            exc_b['part-time'] += 1
            continue
        ids_b.append(g)
    cohort_block(a21, a18, lines,
                 f'### PRETREATMENT COHORT: the shared {yb} baseline (fixed membership, the same people in both arms)',
                 f'The arms are identical through all of {yb} ({base_same}/{len(rb21)} {yb} rows identical), so a '
                 f'{yb} end-of-season state is pretreatment. Definition: golfers whose {yb} season row (identical in both '
                 f'arms, same person by id, name, birth year and country) shows an amateur on a non-college tour '
                 f'({yb} season file `careers.tour`), full-time, aged 17–20 in {yb} ({yb} minus birth year). Left out: '
                 + (', '.join(f'{k} {v}' for k, v in exc_b.items()) or 'none') + '.',
                 ids_b, seasons, yb)

    # (c) ARRIVALS for the second season, by their creation record
    cr21, cr18 = a21['summ'][y0]['created'], a18['summ'][y0]['created']
    al21, al18 = a21['summ'][y0]['arrival_log'], a18['summ'][y0]['arrival_log']
    juniors = sorted(g for g, r in cr21.items() if r[0] == 'junior')
    same_rec = [g for g in juniors if cr18.get(g) == cr21[g] and al18.get(g) == al21.get(g) and same_person(a21, a18, g)]
    names = {}
    from golfsim.calendar import TOUR_BY_KEY
    for k, t in TOUR_BY_KEY.items():
        names[t.name] = k
    ids_c, exc_c = [], Counter()
    for g in same_rec:
        txt = al21.get(g) or ''
        tour_name = txt[txt.find('(') + 1:txt.rfind(')')] if '(' in txt else None
        tk = names.get(tour_name)
        if tk is None:
            exc_c['creation tour not recorded'] += 1
        elif tk.startswith('CO_'):
            exc_c['in college at creation'] += 1
        else:
            ids_c.append(g)
    ok_c = len(same_rec) == len(juniors) and set(cr18) == set(cr21)
    intro_c = (f'Golfers who arrived for {y0} (first row in {y0}), defined by their creation record, not their end-of-{y0} '
               f'row. Fields used: the {y0} season file\'s `diagnostics.created` (written by Season.note_creation at '
               f'creation, week 0: path, age, Overall, attributes) and the arrival line of their history at week 1 '
               f'(`log`, written by careers.add_juniors: "Arrived on the scene at 18 (<tour>)", the tour assigned by '
               f'population.junior_class at creation); lifestyle at creation is the Golfer default, full-time '
               f'(golfer.py). Verification: {len(juniors)} junior arrivals in a21old, {len(cr18)} creation records in '
               f'a18old vs {len(cr21)} in a21old; identical extracted creation fields (path, age, Overall, week), arrival '
               f'line and identity (name, birth year, country) in both arms for '
               f'{len(same_rec)}/{len(juniors)} — ' + ('PASSED (full attributes and ceilings were not compared)' if ok_c else 'NOT identical: the cohort keeps only the '
                                                         'identical ones') + '. Kept: juniors (all aged 18 at creation) '
               f'whose creation tour is not a college tour. Left out: ' + (', '.join(f'{k} {v}' for k, v in exc_c.items())
                                                                          or 'none') +
               '. Late entrants (new professionals, path "late_entrant", aged 21–26) are not amateurs and are not included.')
    cohort_block(a21, a18, lines, f'### ARRIVAL COHORT: juniors created for {y0} (fixed at creation, the same people in '
                                  'both arms)', intro_c, ids_c, seasons, y0)

    # (a) SELECTED by the control arm's end-of-second-season status
    c21 = a21['summ'][y0]['careers']
    ids, excluded = [], Counter()
    for g, row in r21.items():
        d = dict(zip(ROW, row))
        p = a21['people'].get(g) or {}
        if d['status'] != 'amateur' or not p.get('born') or not 17 <= y0 - p['born'] <= 20:
            continue
        c = c21.get(g)
        if g not in r18 or not same_person(a21, a18, g):
            excluded['not the same person in both arms'] += 1
            continue
        if c is None:
            excluded['no season-file record'] += 1
            continue
        if c['tour'].startswith('CO_'):
            excluded['in college'] += 1
            continue
        if d['lifestyle'] != 'full_time':
            excluded['part-time'] += 1
            continue
        ids.append(g)
    cohort_block(a21, a18, lines,
                 f'### FIXED COHORT selected by the control arm\'s (a21old) end-{y0} status: the same people in both arms, '
                 f'chosen after week 45 of {y0}, not pretreatment',
                 f'Selected by a21old\'s end-of-{y0} row, after the arms diverged in week 45 of {y0}; the group is the '
                 f'same people in both columns, but its selection used a post-divergence state, so it is not a '
                 f'pretreatment group. Definition: golfers with a {y0} row in both arms, the same person in both, and in '
                 f'a21old\'s {y0} row an amateur on a non-college tour, full-time, aged 17–20. The {y0} rows differ '
                 f'between the arms for {len(diff)} golfers ({", ".join(map(str, diff))}). Left out: '
                 + (', '.join(f'{k} {v}' for k, v in excluded.items()) or 'none') + '. Read every difference below '
                 'as a descriptive arm difference within this selected group (for example in retirements), not as the '
                 'pathway causing it.',
                 ids, seasons, y0)
    return diff


def golfer_5217(a21, a18, lines, diff, y0):
    """The one near-clean individual case: the first entry below 21, in the season where only two rows differ."""
    ROW = row_fields()
    lines.append(f'### The first entry below 21 (season {y0}), up to the point the worlds diverge')
    lines.append('')
    lines.append(f'Season {y0} is the last season in which the arms are nearly identical ({y0 - 1} is identical; in {y0} the rows of '
                 f'{len(diff)} golfers differ). From the next season fewer than 1% of rows are identical, so a golfer\'s '
                 'later seasons in the other arm are not a counterfactual for that person and are not compared here.')
    lines.append('')
    took = {r['gid']: r for r in a18['summ'][y0]['work_pathway']}
    for g in diff:
        p = a18['people'].get(g) or {}
        d21, d18 = dict(zip(ROW, a21['data']['rows'][y0][g])), dict(zip(ROW, a18['data']['rows'][y0][g]))
        changed = [k for k in ROW if d21.get(k) != d18.get(k)]
        lines.append(f'- Golfer {g} (born {p.get("born")}, {p.get("country")}): {y0} row columns that differ: '
                     + ', '.join(changed) + '.')
        show = ['status', 'lifestyle', 'events'] + [k for k in changed if k not in ('status', 'lifestyle', 'events')]
        lines.append('  - a21old: ' + ', '.join(f'{k} {d21[k]}' for k in show)
                     + f'; longest cash-blocked count {(tracked_rows(a21, y0).get(g) or {}).get("blocked", "—")}.')
        rec = took.get(g)
        lines.append('  - a18old: ' + ', '.join(f'{k} {d18[k]}' for k in show)
                     + f'; longest cash-blocked count {(tracked_rows(a18, y0).get(g) or {}).get("blocked", "—")}'
                     + (f'; took work by the pathway in week {rec["week"]} at age {rec["age"]} after {rec["weeks_blocked"]} '
                        'counted weeks' if rec else '') + '.')
    lines.append('')


def section1(a21, a18, lines):
    lines.append('## 1. Pathway age: a21old (minimum age 21) vs a18old (minimum age 18), seed 4207, college order old')
    lines.append('')
    lines.append(f'Seasons: {seasons_label(a21)}; {seasons_label(a18)}.')
    lines.append('')
    # divergence
    div = divergence(a21, a18)
    first_entry = None
    for y in a18['seasons']:
        for r in a18['summ'][y]['work_pathway']:
            if r['age'] < 21:
                first_entry = (y, r['week'], r['gid'], r['age'])
                break
        if first_entry:
            break
    lines.append('### Where the arms diverge')
    lines.append('')
    lines.append('Golfer rows of the run state (long_world `year_rows`: results, money, staff, activity counts) compared '
                 'season by season between the two arms.')
    lines.append('')
    lines.append(table(['season', 'rows a21old', 'rows a18old', 'in both', 'identical'],
                       [(y, na, nb, nboth, frac(same, nboth)) for y, na, nb, nboth, same in div]))
    lines.append('')
    if first_entry:
        lines.append(f'First pathway entry below 21 in a18old: season {first_entry[0]}, week {first_entry[1]} '
                     f'(golfer {first_entry[2]}, age {first_entry[3]}).')
    else:
        lines.append('No pathway entry below 21 in a18old in the committed seasons.')
    fd = next((y for y, na, nb, nboth, same in div if same != nboth or na != nb), None)
    lines.append(f'First season with any differing row: {fd if fd else "none in the committed seasons"}.')
    if fd:
        ra, rb = a21['data']['rows'][fd], a18['data']['rows'][fd]
        diff = sorted(g for g in set(ra) & set(rb) if list(ra[g]) != list(rb[g]))
        only = sorted(set(ra) ^ set(rb))
        took = {r['gid'] for r in a18['summ'][fd]['work_pathway'] if r['age'] < 21}
        lines.append(f'Rows differing in {fd}: {len(diff)} ({", ".join(str(g) + (" (entered the pathway below 21 in a18old)" if g in took else "") for g in diff[:8])}'
                     f'{" …" if len(diff) > 8 else ""}); rows in one arm only: {len(only)}.')
    lines.append('')
    diff = original_cohort(a21, a18, lines)
    if diff:
        golfer_5217(a21, a18, lines, diff, [y for y in a21['seasons'] if y in a18['seasons']][1])
    # tracked seasons by band
    lines.append('### END-STATUS denominators: tracked full-time non-college amateurs (golfer-seasons), by age band')
    lines.append('')
    lines.append('**Denominator: end-status golfer-seasons.** Membership depends on each season\'s end status (or a '
                 'pathway entry during the season), so the group\'s makeup differs between the arms from 2028 on; these '
                 'tables compare arm-level rates, not the same people (see the ORIGINAL COHORT table for that). Tracked: '
                 'amateur, not in college, full-time at the season end or took work by the pathway during it '
                 '(extras `amateurs`). "Blocked" is the season\'s longest count of genuinely cash-blocked weeks '
                 '(work_pathway.count: only "could not afford any event" adds).')
    lines.append('')
    for arm in (a21, a18):
        rows = []
        per_season = []
        tot = defaultdict(Counter)
        for y in arm['seasons']:
            tr = tracked_rows(arm, y)
            sc = defaultdict(Counter)
            for g, r in tr.items():
                b = band(r['age'])
                for c in (sc[b], tot[b]):
                    c['n'] += 1
                    c['zero'] += r['events'] == 0
                    c['blocked'] += r['blocked'] >= 1
                    c['8+'] += r['blocked'] >= 8
                    c['entry'] += r['took'] is not None
                    c['8+entry'] += r['took'] is not None and r['blocked'] >= 8
            per_season.append((y, sc))
        for b in ('<18', '18-20', '21+'):
            c = tot[b]
            rows.append((b, c['n'], frac(c['zero'], c['n']), frac(c['blocked'], c['n']), frac(c['8+'], c['n']),
                         frac(c['entry'], c['n']), frac(c['8+entry'], c['8+']), c['entry'] - c['8+entry']))
        lines.append(f'**{arm["name"]}** (END-STATUS denominators, pooled over {len(arm["seasons"])} seasons)')
        lines.append('')
        lines.append(table(['age band', 'tracked seasons', 'zero-start', 'any blocked week', 'count 8+ (in-season max)',
                            'pathway entries / tracked', 'count-8+ seasons that entered',
                            'entries with in-season max < 8 (count carried from the season before)'], rows))
        lines.append('')
        srows = []
        for y, sc in per_season:
            srows.append((y, *[f'{sc[b]["n"]} / {sc[b]["zero"]} / {sc[b]["blocked"]} / {sc[b]["8+"]} / {sc[b]["entry"]}'
                               for b in ('18-20', '21+')]))
        zr = Counter()
        for y in arm['seasons']:
            rows_y = arm['data']['rows'][y]
            for g, r in tracked_rows(arm, y).items():
                if r['events'] == 0:
                    row = rows_y.get(g)
                    zr[(band(r['age']), ((row[16] if row else '') or '(no reason recorded)').split(':')[0])] += 1
        if zr:
            lines.append('Zero-start reasons (run state rows, `zero_start_reason`): '
                         + '; '.join(f'{b}: {why} — {n}' for (b, why), n in sorted(zr.items())))
            lines.append('')
        lines.append('Per season (END-STATUS denominators) — tracked / zero-start / any blocked / count 8+ / entries:')
        lines.append('')
        lines.append(table(['season', '18-20', '21+'], srows))
        lines.append('')
    # entries by age
    lines.append('### Pathway entries by age (season file `work_pathway` records; counts of entries, no denominator)')
    lines.append('')
    ages = sorted({r['age'] for arm in (a21, a18) for y in arm['seasons'] for r in arm['summ'][y]['work_pathway']})
    rows = []
    for arm in (a21, a18):
        c = Counter(r['age'] for y in arm['seasons'] for r in arm['summ'][y]['work_pathway'])
        rows.append((arm['name'], sum(c.values()), *[c.get(a, 0) for a in ages]))
    lines.append(table(['arm', 'entries', *[f'age {a}' for a in ages]], rows))
    lines.append('')
    # time to job
    lines.append('### Reconstructed: the last n plan weeks compatible with the recorded count (monthly-plan '
                 'availability, not actual weekly access); unknown weeks shown')
    lines.append('')
    lines.append('The weekly access outcome is not stored week by week. This walks back from each entry\'s decision week '
                 'over the availability the monthly plans recorded for each week (decision evidence /2, `schedule`), '
                 'reading it as work_pathway.count reads access ("unaff" counts, "none"/"inelig"/injured pause, anything '
                 'else resets). "Compatible" means the plan weeks contain the recorded `weeks_blocked` (n) counted weeks '
                 'before any reset; it shows the plan data do not contradict the stored count, and does not validate it '
                 'independently (the walk stops at n) nor give the golfer\'s actual weeks. "Span" is the calendar weeks '
                 'from the earliest of those n plan weeks to the decision (pauses included); it is not a measured time '
                 'from the first blocked week. "Longer run" scans on past n until a reset: entries whose plan-based '
                 'compatible run is longer than the stored count. Plan-week availability and the weekly access ledger '
                 'can differ, so a longer plan-based run is not evidence of a miscount.')
    lines.append('')
    rows = []
    for arm in (a21, a18):
        tl, first = weeks_timeline(arm)
        by = defaultdict(list)
        agree = defaultdict(Counter)
        for y in arm['seasons']:
            for r in arm['summ'][y]['work_pathway']:
                span, found, n, unknown, full, hit_start = time_to_job(arm, tl, first, r)
                b = band(r['age'])
                agree[b]['n'] += 1
                agree[b]['ok'] += found == n
                agree[b]['unknown'] += unknown > 0
                agree[b]['unknown_weeks'] += unknown
                agree[b]['longer'] += full > n
                agree[b]['start'] += hit_start and full > n
                if span is not None and found == n:
                    by[b].append(span)
                by[b + ' recorded count'].append(n)
                by[b + ' full'].append(full)
        for b in ('18-20', '21+'):
            if agree[b]['n']:
                rows.append((arm['name'], b, agree[b]['n'], frac(agree[b]['ok'], agree[b]['n']),
                             f'{agree[b]["unknown"]} ({agree[b]["unknown_weeks"]} weeks)',
                             dist(by[b]), dist(by[b + ' recorded count']),
                             frac(agree[b]['longer'], agree[b]['n']) + f'; {agree[b]["start"]} reach the data start',
                             dist(by[b + ' full'])))
    lines.append(table(['arm', 'age band', 'entries', 'compatible', 'entries with unknown plan weeks in the span',
                        'span, plan weeks (min/q1/med/q3/max)', 'recorded weeks_blocked',
                        'longer plan-based run than recorded', 'plan-based run, scanned to a reset'], rows))
    lines.append('')
    # what happened after
    lines.append('### After the job (denominator: each arm\'s pathway entries; the entrants differ between arms)')
    lines.append('')
    lines.append('Event-based groups: who enters depends on the arm, so these are arm-level descriptions, not a '
                 'comparison of the same people. For each entry in season Y: season starts in Y (including starts made '
                 'before the job), starts from the decision week on (the weeks of the editions whose finishes list the '
                 'golfer, from the season file `events`), the weeks from the decision to the first such start, starts in '
                 'Y+1 (season file `careers`), Overall change over Y+1 (ratings as each season ends), and the first career '
                 'transition from the winter after Y on (within the committed seasons). Entries in the last committed '
                 'season have no Y+1.')
    lines.append('')
    rows, outs = [], {}
    for arm in (a21, a18):
        for b in ('18-20', '21+'):
            st0, after, gap, st1, dev, oc = [], [], [], [], [], Counter()
            n = none_after = 0
            for y in arm['seasons']:
                for r in arm['summ'][y]['work_pathway']:
                    if band(r['age']) != b:
                        continue
                    n += 1
                    a0, a1, d, o = follow(arm, r['gid'], y)
                    st0.append(a0)
                    wks = [w for w in arm['summ'][y]['start_weeks'].get(r['gid'], []) if w >= r['week']]
                    after.append(len(wks))
                    if wks:
                        gap.append(wks[0] - r['week'])
                    else:
                        none_after += 1
                    if (y + 1) in arm['summ']:
                        st1.append(a1)
                        dev.append(d)
                    oc[outcome_kind(o)] += 1
            if n:
                rows.append((arm['name'], b, n, dist(st0), dist(after), dist(gap),
                             frac(none_after, n), dist(st1), dist(dev, 2)))
                outs[(arm['name'], b)] = (n, oc)
    lines.append(table(['arm', 'band', 'entries', 'season starts in Y (including before the job)',
                        'starts in Y from the decision week on', 'weeks from the decision to the first start after it',
                        'no start after the decision in Y', 'starts in Y+1', 'Overall change over Y+1'], rows))
    lines.append('')
    for (nm, b), (n, oc) in outs.items():
        lines.append(f'- {nm} {b}: ' + '; '.join(f'{k} {frac(v, n)}' for k, v in oc.most_common()))
    lines.append('')
    # comparison: tracked count-8+ golfers who did not enter
    lines.append('### END-STATUS denominators: tracked golfer-seasons with a count of 8+ that did not enter that season')
    lines.append('')
    lines.append('Membership depends on end status and on not entering, both of which differ between arms; arm-level '
                 'description only.')
    lines.append('')
    rows = []
    for arm in (a21, a18):
        for b in ('18-20', '21+'):
            st0, st1, dev, oc = [], [], [], Counter()
            n = 0
            for y in arm['seasons']:
                for g, r in tracked_rows(arm, y).items():
                    if band(r['age']) != b or r['blocked'] < 8 or r['took'] is not None:
                        continue
                    n += 1
                    a0, a1, d, o = follow(arm, g, y)
                    st0.append(a0)
                    if (y + 1) in arm['summ']:
                        st1.append(a1)
                        dev.append(d)
                    oc[outcome_kind(o)] += 1
            if n:
                rows.append((arm['name'], b, n, dist(st0), dist(st1), dist(dev, 2),
                             '; '.join(f'{k} {v}' for k, v in oc.most_common(4))))
    lines.append(table(['arm', 'band', 'golfer-seasons', 'starts in Y', 'starts in Y+1', 'Overall change over Y+1',
                        'first transition after (top 4)'], rows))
    lines.append('')


# ---- section 2: college open access ------------------------------------------------------------------------------
def college_cohort(old, new, lines, defs, reg2series):
    """ORIGINAL COHORT for the college comparison: membership fixed in the first season, before any week is played."""
    common = [y for y in old['seasons'] if y in new['seasons']]
    if not common:
        lines += ['### Fixed cohort', '', 'Needs a committed season in both arms.', '']
        return None
    y0 = common[0]
    OAR = defs['OPEN_AMATEUR_REGIONS']
    co, cn = old['summ'][y0]['careers'], new['summ'][y0]['careers']
    groups, mismatch = defaultdict(lambda: defaultdict(list)), 0
    for g, c in co.items():
        if c['status'] != 'amateur' or not (c['tour'].startswith('CO_') or c['tour'] in OAR):
            continue
        d = cn.get(g)
        if d is None or d['tour'] != c['tour'] or d['res'] != c['res'] or not same_person(old, new, g):
            mismatch += 1
            continue
        if c['tour'].startswith('CO_'):
            key = reg2series.get(defs['REGION'].get(c['res'])) if c['res'] else None
            groups['college'][key or 'unplaced'].append(g)
        else:
            groups['members'][c['tour']].append(g)
    # creation check: the residence in the first season's record is the one recorded at creation (week 0 of the first
    # season) in both arms, for every member kept
    members = [g for kind in groups for ids in groups[kind].values() for g in ids]
    bad = []
    for g in members:
        for arm in (old, new):
            fr = (arm['people'].get(g) or {}).get('first_res') or (None, None, None, None)
            if fr[0] != y0 or fr[1] != 0 or fr[2] != arm['summ'][y0]['careers'][g]['res']:
                bad.append((arm['name'], g))
    passed = not bad
    lines.append('### ' + ('COHORT fixed at creation (pretreatment): ' if passed else
                           'FIXED COHORT (creation check failed: not labelled pretreatment): ')
                 + f'{y0} college players and series members, the same people in both arms')
    lines.append('')
    lines.append(f'These two arms differ from week 1 of {y0}, so no played season is shared. Membership comes from the '
                 f'{y0} season record\'s tour and residence, which are the creation values: a golfer\'s tour is '
                 'assigned at world creation (golfsim/population.py `generate_world`: `_college_or_series` and the '
                 'amateur series, lines 582, 676, 678) and is changed only after the season\'s snapshot is taken '
                 '(golfsim/season.py `end_of_season`: snapshot at line 2621, then `apply_cards` 2628, `careers.decide` '
                 '2647, `residence.review_moves` 2668); the residence is set at creation by `residence.settle(first_year, 0)` '
                 '(season.py line 559), and the only writer of a move, `residence._record` (residence.py line 278), is '
                 'called at week 0 or week 53 (settle, review_moves, staff_moves), never during weeks 1–52; the season '
                 'file\'s `careers.residence` is `residence_at(gid, year, 52)` (archive.py line 213). Data check: for all '
                 f'{len(members)} members kept, the {y0} residence equals the people table\'s `first_residence` dated '
                 f'({y0}, week 0) in both arms — ' + ('PASSED' if passed else f'FAILED for {len(bad)}') + '. '
                 f'Kept: amateurs whose {y0} tour and residence are the same in both arms and who are the same person '
                 f'(id, name, birth year, country); {mismatch} differ and are left out. College players are placed by '
                 f'that residence, members by their series. Denominator: the fixed group\'s size, the same people in '
                 'both arms.')
    lines.append('')

    def outcomes(arm, ids):
        o = Counter()
        for y in common:
            s = arm['summ'][y]
            for g in ids:
                os_ = s['open_starts'].get(g, {})
                o['open'] += sum(os_.values())
                o['t5'] += s['t5_starts'].get(g, 0)
                c = s['careers'].get(g) or {}
                o['shut'] += c.get('oo_shut', 0)
                o['alt'] += c.get('oo_alt', 0)
        st = Counter(status_at(arm, g, common[-1]) for g in ids)
        return o, st

    rows, got = [], {}
    span = f'{common[0]}–{common[-1]}'
    for kind in ('college', 'members'):
        for key in sorted(groups[kind]):
            ids = groups[kind][key]
            N = len(ids)
            oo, so = outcomes(old, ids)
            on, sn = outcomes(new, ids)
            got[(kind, key)] = (N, oo, on)
            f = lambda o: f'{per(o["open"], N, 1)} / {per(o["t5"], N, 1)} / {per(o["shut"], N, 1)} ({per(o["alt"], N, 1)})'
            top = lambda st: ', '.join(f'{k} {frac(v, N, 0)}' for k, v in st.most_common(3))
            rows.append((kind, key.replace('AM_', ''), N, f(oo), f(on), top(so), top(sn)))
    lines.append(f'Per-head columns are CUMULATIVE {span} values per member of N (the fixed group\'s size): ordinary '
                 'open starts / tier-5 (college) starts / weeks shut out of a full ordinary open field '
                 '(in brackets: weeks they played elsewhere instead).')
    lines.append('')
    lines.append(table(['group', 'series region', 'N (fixed)',
                        f'a18old: cumulative {span} per member of N — open starts / tier-5 starts / open shut-out weeks (alt)',
                        f'a18new: cumulative {span} per member of N — same', f'a18old status end {common[-1]} (top 3)',
                        f'a18new status end {common[-1]} (top 3)'], rows))
    lines.append('')
    return {'got': got, 'span': span, 'last': common[-1]}


def section2(old, new, lines):
    lines.append('## 2. College access: a18old (open access OFF) vs a18new (ON), seed 4207, pathway age 18')
    lines.append('')
    lines.append(f'Seasons: {seasons_label(old)}; {seasons_label(new)}.')
    lines.append('')
    defs = old['defs'] if old['seasons'] else new['defs']
    OAR = defs['OPEN_AMATEUR_REGIONS']
    reg2series = {r: t for t, rs in OAR.items() for r in rs}
    lines.append('Definitions as the build has them (golfsim/season.py): an ordinary open amateur event is tier 6, '
                 'category "regular", amateur eligibility, of a tour in `OPEN_AMATEUR_REGIONS` '
                 f'({", ".join(f"{t}: {"/".join(rs)}" for t, rs in OAR.items())}); field capacity = field × '
                 f'{defs["EXPANSION"]} (AMATEUR_OPEN_EXPANSION). College players: amateurs on a college tour (tier 5, '
                 '`CO_*`), placed in the series region of where they lived that season (season file `careers.residence`, '
                 'the residence `home_college_amateur` reads). Members: amateurs whose tour is that series. Shut out: '
                 'weeks recorded in the access ledger (`careers.denied`) whose first choice was an ordinary open event '
                 'and every acceptable field was full ("shut out"), or they played elsewhere ("alternative"). The two '
                 'arms differ from the first season (the setting acts from week 1).')
    lines.append('')

    def season_stats(arm, y):
        s = arm['summ'][y]
        reg = defs['REGION']
        st = defaultdict(Counter)
        for g, c in s['careers'].items():
            if c['status'] != 'amateur':
                continue
            if c['tour'].startswith('CO_'):
                series = reg2series.get(reg.get(c['res'])) if c['res'] else None
                key = series or 'unplaced'
                os_ = s['open_starts'].get(g, {})
                for k in (key, 'ALL'):
                    st[k]['col'] += 1
                    st[k]['col_open'] += sum(os_.values())
                    st[k]['col_open_home'] += os_.get(series, 0) if series else 0
                    st[k]['col_t5'] += s['t5_starts'].get(g, 0)
                    st[k]['col_shut'] += c.get('oo_shut', 0)
                    st[k]['col_alt'] += c.get('oo_alt', 0)
                    st[k]['col_any_open'] += sum(os_.values()) > 0
                    st[k]['col_zero'] += c['events'] == 0
            elif c['tour'] in OAR:
                os_ = s['open_starts'].get(g, {})
                for k in (c['tour'], 'ALL'):
                    st[k]['mem'] += 1
                    st[k]['mem_open'] += sum(os_.values())
                    st[k]['mem_open_home'] += os_.get(c['tour'], 0)
                    st[k]['mem_shut'] += c.get('oo_shut', 0)
                    st[k]['mem_alt'] += c.get('oo_alt', 0)
                    st[k]['mem_zero'] += c['events'] == 0
                    if c['lifestyle'] == 'part_time':
                        st[k]['mem_pt'] += 1
                        st[k]['mem_pt_events'] += c['events']
                        st[k]['mem_pt_open'] += sum(os_.values())
                        st[k]['mem_pt_zero'] += c['events'] == 0
        for e in s['oo'].values():
            for k in (e['tour'], 'ALL'):
                st[k]['ev'] += 1
                st[k]['cap'] += e['cap']
                st[k]['ent'] += e['entrants']
                st[k]['full'] += e['entrants'] >= e['cap']
        return st

    years = sorted(set(old['seasons']) | set(new['seasons']))
    first = min(years) if years else 0
    cache = {(a['name'], y): season_stats(a, y) for a in (old, new) for y in a['seasons']}

    def cell(a, y, k, f):
        st = cache.get((a['name'], y))
        return '—' if st is None else f(st[k])

    coh = college_cohort(old, new, lines, defs, reg2series)
    common = [y for y in old['seasons'] if y in new['seasons']]
    cap_line = None
    if coh and common:
        g = coh['got']
        ly = common[-1]
        so, sn = cache[('a18old', ly)], cache[('a18new', ly)]
        P = []
        def chg(a, b):
            return f'{a:.1f} → {b:.1f} ({(b - a) / a * 100:+.0f}%)' if a else f'{a:.1f} → {b:.1f}'
        na_m, na_c = g.get(('members', 'AM_NORTH_AMERICA')), g.get(('college', 'AM_NORTH_AMERICA'))
        if na_m:
            N, a, b = na_m
            P.append(f'North America members (fixed, N = {N}): cumulative {coh["span"]} open starts per head '
                     f'{chg(a["open"] / N, b["open"] / N)}, cumulative open shut-out weeks per head '
                     f'{a["shut"] / N:.1f} → {b["shut"] / N:.1f}')
        if na_c:
            N, a, b = na_c
            P.append(f'North America college players (fixed, N = {N}): cumulative open starts per head '
                     f'{chg(a["open"] / N, b["open"] / N)}, cumulative open shut-out weeks per head '
                     f'{a["shut"] / N:.1f} → {b["shut"] / N:.1f}')
        A_o, A_n = so['ALL'], sn['ALL']
        NA_o, NA_n = so['AM_NORTH_AMERICA'], sn['AM_NORTH_AMERICA']
        cap_line = (f'All regions, end-status {ly} (yr {ly - common[0] + 1}): member open starts per member '
                    f'{per(A_o["mem_open"], A_o["mem"])} → {per(A_n["mem_open"], A_n["mem"])}; member shut-out weeks per '
                    f'member {per(A_o["mem_shut"], A_o["mem"])} → {per(A_n["mem_shut"], A_n["mem"])}; college open '
                    f'starts per player {per(A_o["col_open"], A_o["col"])} → {per(A_n["col_open"], A_n["col"])}')
        P.append(cap_line)
        P.append(f'North America in {ly} (end-status): series members\' ordinary open starts per member '
                 f'{per(NA_o["mem_open"], NA_o["mem"])} → {per(NA_n["mem_open"], NA_n["mem"])}; working (part-time) '
                 f'amateur members, all starts per head {per(NA_o["mem_pt_events"], NA_o["mem_pt"])} → '
                 f'{per(NA_n["mem_pt_events"], NA_n["mem_pt"])} and ordinary open starts per head '
                 f'{per(NA_o["mem_pt_open"], NA_o["mem_pt"])} → {per(NA_n["mem_pt_open"], NA_n["mem_pt"])} '
                 f'(the part-time amateur schedule target is 8 events: season.target_events)')
        zs = []
        for lab, k, n in (('college players', 'col_zero', 'col'), ('series members', 'mem_zero', 'mem'),
                          ('working (part-time) amateur members', 'mem_pt_zero', 'mem_pt')):
            zs.append(f'{lab} {frac(A_o[k], A_o[n])} → {frac(A_n[k], A_n[n])}')
        incr = any((A_n[k] / A_n[n] if A_n[n] else 0) > (A_o[k] / A_o[n] if A_o[n] else 0)
                   for _, k, n in (('', 'col_zero', 'col'), ('', 'mem_zero', 'mem'), ('', 'mem_pt_zero', 'mem_pt')))
        P.append(f'zero-start seasons in {ly}, all regions (end-status): ' + '; '.join(zs)
                 + (' — no group\'s zero-start share increased' if not incr else ' — at least one group\'s share increased'))
        lines.append('**Capacity trade-off.** College players and series members compete for the same ordinary open '
                     'field capacity. How each group\'s open starts and shut-out weeks moved between the arms, computed '
                     'from the runs (old → new): ' + '; '.join(P) + '. '
                     'Design status (reviewer decision, recorded here): the open-access policy is retained; the cost in '
                     'members\' opportunities is disclosed, not offset by expanding fields.'
                     + ('' if ly == old['seasons'][-1] == new['seasons'][-1] else
                        f' (Partial: through {ly}, the last season both arms have committed.)'))
        lines.append('')
    lines.append('### END-STATUS denominators: all regions, per season (old → new)')
    lines.append('')
    lines.append('**Denominators: each season\'s college players and members at that season\'s end** — membership '
                 'is re-taken every season in each arm (who is in college or a member, and where they live, depends '
                 'on the arm), so these are arm-level per-season rates, not the same people.')
    lines.append('')
    cols = [('college players', lambda c: c['col']),
            ('college open starts / player', lambda c: per(c['col_open'], c['col'])),
            ('college players with any open start', lambda c: pct(c['col_any_open'], c['col'])),
            ('college tier-5 starts / player', lambda c: per(c['col_t5'], c['col'])),
            ('members', lambda c: c['mem']),
            ('member open starts / member', lambda c: per(c['mem_open'], c['mem'])),
            ('ordinary open events', lambda c: c['ev']),
            ('field fill (entrants / capacity)', lambda c: pct(c['ent'], c['cap'])),
            ('events full', lambda c: pct(c['full'], c['ev'])),
            ('college shut out (alt) / player', lambda c: f'{per(c["col_shut"], c["col"])} ({per(c["col_alt"], c["col"])})'),
            ('member shut out (alt) / member', lambda c: f'{per(c["mem_shut"], c["mem"])} ({per(c["mem_alt"], c["mem"])})')]
    rows = []
    for y in years:
        rows.append((f'{y} (yr {y - first + 1})', *[f'{cell(old, y, "ALL", f)} → {cell(new, y, "ALL", f)}' for _, f in cols]))
    lines.append(table(['season', *[c for c, _ in cols]], rows))
    lines.append('')
    if cap_line:
        lines.append(f'Capacity trade-off (end-status, see the paragraph above the table): {cap_line}.')
        lines.append('')
    lines.append('### END-STATUS denominators: by series region, per season (old → new)')
    lines.append('')
    rcols = [('college players', lambda c: c['col']),
             ('college open starts / player (home series)', lambda c: f'{per(c["col_open"], c["col"])} ({per(c["col_open_home"], c["col"])})'),
             ('college tier-5 / player', lambda c: per(c['col_t5'], c['col'])),
             ('members', lambda c: c['mem']),
             ('member open starts / member (home series)', lambda c: f'{per(c["mem_open"], c["mem"])} ({per(c["mem_open_home"], c["mem"])})'),
             ('member zero-start', lambda c: pct(c['mem_zero'], c['mem'])),
             ('events', lambda c: c['ev']),
             ('fill', lambda c: pct(c['ent'], c['cap'])),
             ('full', lambda c: pct(c['full'], c['ev'])),
             ('college shut out / player', lambda c: per(c['col_shut'], c['col'])),
             ('member shut out / member', lambda c: per(c['mem_shut'], c['mem']))]
    rows = []
    for t in OAR:
        for y in years:
            rows.append((t.replace('AM_', ''), y, *[f'{cell(old, y, t, f)} → {cell(new, y, t, f)}' for _, f in rcols]))
    lines.append(table(['series', 'season', *[c for c, _ in rcols]], rows))
    lines.append('')
    unpl = [(a['name'], y, cache[(a['name'], y)]['unplaced']['col']) for a in (old, new) for y in a['seasons']
            if cache[(a['name'], y)]['unplaced']['col']]
    if unpl:
        lines.append('College players with no recorded residence (not placed in a region): '
                     + ', '.join(f'{n} {y}: {c}' for n, y, c in unpl) + '.')
        lines.append('')


# ---- section 3: two-seed bounded metrics -------------------------------------------------------------------------
PATH_KIND = {'junior': 'juniors', 'late_entrant': 'new_pros'}


def allocation_check(arms, lines):
    """Cohort-share allocations (participation / population.entrant_rows) against the actual arrivals."""
    lines.append('### Entrant allocation check (all arms, all committed seasons)')
    lines.append('')
    lines.append('Source mapping: season Y\'s `prestige.nations` holds the entrants of season Y+1 (`entrant_year`): '
                 '`totals`, `allocated`, `existing` and `shares` per pathway (participation.record, filled by '
                 'population.entrant_rows). The actual arrivals of Y+1 are the next season file\'s `diagnostics.created` '
                 '(Season.note_creation: path "junior" from careers.add_juniors, "late_entrant" from '
                 'careers.add_new_professionals; "initial" is the starting world), joined to the people table\'s country '
                 '(nationality, never changed). Checks per arm-season and pathway: (1) shares sum to 1 within '
                 'n_nations × 0.5e-6 (each share rounded to 6 decimals; 57 nations: 2.85e-5); (2) allocations by nation '
                 'sum to the pathway\'s total; (3) arrivals by nation equal the allocation; (4) the total is the same in '
                 'arms with the same seed: population.entrant_rows takes it from `existing_rule(kind, year, seed, '
                 'baseline)` over the nation profiles the world began with (careers._cohort_args: '
                 '`participation.baseline`), so it depends on the pathway, year and seed only, not on the arm or the '
                 'world\'s state.')
    lines.append('')
    kinds = sorted({k for a in arms for y in a['seasons'] for k in a['summ'][y]['prestige'].get('totals', {})})
    cells, ok12, fail12 = Counter(), Counter(), []
    arr_cells = arr_ok = 0
    mism, terminal, totals_by = [], [], defaultdict(dict)
    agree_age = Counter()
    for a in arms:
        for y in a['seasons']:
            p = a['summ'][y]['prestige']
            ey = p.get('entrant_year')
            for kind in kinds:
                sh = p['shares'].get(kind, {})
                al = p['allocated'].get(kind, {})
                tot = p['totals'].get(kind)
                cells[kind] += 1
                tol = len(sh) * 0.5e-6
                e1 = abs(sum(sh.values()) - 1)
                good = bool(sh) and e1 <= tol and tot is not None and sum(al.values()) == tot
                ok12[kind] += good
                if not good:
                    fail12.append(f'{a["name"]} {y}→{ey} {kind}: |Σshares−1| = {e1:.2e} (tol {tol:.2e}), '
                                  f'Σallocated {sum(al.values())} vs total {tot}')
                totals_by[(kind, ey)][(a['seed'], a['name'])] = tot
                if ey in a['summ']:
                    cr = a['summ'][ey]['created']
                    act = Counter((a['people'].get(g) or {}).get('country', '?') for g, r in cr.items()
                                  if PATH_KIND.get(r[0]) == kind)
                    for g, r in (cr.items() if kind == kinds[0] else ()):     # (once per cohort)
                        if r[0] in PATH_KIND:
                            agree_age[(r[0], r[1] == 18 if r[0] == 'junior' else 21 <= r[1] <= 26)] += 1
                    arr_cells += 1
                    bad = [(c, al.get(c, 0), act.get(c, 0)) for c in sorted(set(al) | set(act)) if al.get(c, 0) != act.get(c, 0)]
                    if bad:
                        mism.append((a['name'], ey, kind, bad))
                    else:
                        arr_ok += 1
                else:
                    terminal.append((a['name'], y, ey, kind, al))
    lines.append(f'- (1)+(2) allocation cells: ' + '; '.join(f'{k} {ok12[k]}/{cells[k]} pass' for k in kinds)
                 + ('' if not fail12 else '. Failures: ' + '; '.join(fail12)) + '.')
    lines.append(f'- (3) arrival cells with a next archive season: {arr_ok}/{arr_cells} match by nation'
                 + ('' if not mism else '; mismatches (nation: allocated vs actual): ' + '; '.join(
                     f'{n} {ey} {k}: ' + ', '.join(f'{c} {x} vs {z}' for c, x, z in bad) for n, ey, k, bad in mism)) + '.')
    lines.append(f'- Terminal cohorts (an arm\'s last season: no next archive season, so no `diagnostics.created`): '
                 + ', '.join(f'{n} {y}→{ey} {k}' for n, y, ey, k, _ in terminal) + ' — not verified (the checkpoint '
                 'was not opened).')
    sup = []
    for n, y, ey, kind, al in terminal:
        a = next(x for x in arms if x['name'] == n)
        ids = [g for g, pp in a['people'].items() if pp.get('created') == ey and not pp.get('initial') and pp.get('born')]
        act = Counter(a['people'][g]['country'] for g in ids
                      if (kind == 'juniors' and ey - a['people'][g]['born'] == 18)
                      or (kind == 'new_pros' and 21 <= ey - a['people'][g]['born'] <= 26))
        if not ids:
            sup.append(f'{n} {ey} {kind}: no people-table rows created {ey}')
            continue
        bad = [(c, al.get(c, 0), act.get(c, 0)) for c in sorted(set(al) | set(act)) if al.get(c, 0) != act.get(c, 0)]
        sup.append(f'{n} {ey} {kind}: ' + ('matches' if not bad else 'differs (' + ', '.join(
            f'{c} {x} vs {z}' for c, x, z in bad[:6]) + (' …' if len(bad) > 6 else '') + ')'))
    agree = ', '.join(f'{p} {"agrees" if ok else "differs"}: {v}' for (p, ok), v in sorted(agree_age.items()))
    lines.append('- Supplementary, NOT counted as verified: the terminal cohorts from the people table\'s `created` '
                 'year and the arrival ages the code defines (juniors 18: population.junior_class; new professionals '
                 '21–26: population.NEW_PRO_AGES). On the verified cohorts the age rule and the recorded path: '
                 + agree + '. Terminal: ' + '; '.join(sup) + '.')
    same = []
    for (kind, ey), d in sorted(totals_by.items(), key=lambda kv: (kv[0][1] or 0, kv[0][0])):
        by_seed = defaultdict(dict)
        for (seed, name), t in d.items():
            by_seed[seed][name] = t
        for seed, m in by_seed.items():
            if len(m) > 1:
                same.append((kind, ey, seed, m, len(set(m.values())) == 1))
    nbad = [x for x in same if not x[4]]
    lines.append(f'- (4) totals across same-seed arms: {len(same) - len(nbad)}/{len(same)} (pathway, entrant year) '
                 'comparisons identical' + ('' if not nbad else '; differ: ' + '; '.join(
                     f'{k} {ey} seed {sd}: ' + ', '.join(f'{n} {t}' for n, t in m.items()) for k, ey, sd, m, _ in nbad)) + '.')
    lines.append('')


def venue_section(arms, lines):
    """Venue moves in the default arms: the rule's stages reconstructed from retained season data."""
    from golfsim import schedule as SCH, prestige as PR
    from golfsim.course_library import default_library, event_level
    lib = default_library(SCH.DEFAULT)
    cal = lib.calendar
    mw = cal.major_weeks() if callable(getattr(cal, 'major_weeks', None)) else cal.major_weeks
    total = sum(1 for a in arms for y in a['seasons'])
    moves = sum(a['summ'][a['seasons'][-1]]['prestige']['venue_moves_total'] for a in arms if a['seasons'])
    lines.append('**Venue moves: natural activation not exercised in these runs; calibration of the venue-move rule '
                 f'unexercised.** {moves} moves were decided over the {total} default-arm seed-seasons ('
                 + ', '.join(f'{a["name"]} {len(a["seasons"])}' for a in arms) + '). Positive regression evidence that '
                 'moves do happen under the rule: tests/test_venue_moves.py — '
                 '`test_sustained_gap_moves_two_seasons_later_and_never_touches_the_plan` (a gap held at three season '
                 'ends moves the event two seasons later to a physically better eligible course in the same city, '
                 'leaving the shared plan unchanged), `test_a_second_decision_is_added_not_overwritten` (two moves, '
                 'decided in 2029 and 2039, both kept and in force by effective year) and '
                 '`test_save_and_resume_keep_the_history` (two moves survive a save and resume).')
    lines.append('')
    lines.append(f'Trigger funnel per season, reconstructed from retained data and the build\'s static course plan '
                 f'(Season.review_venues; no simulation): eligible = held this season, single-site series, not a major '
                 f'or qualifying stage; gap = archived event prestige − archived course prestige of the course it was '
                 f'played on (both as set at the season end, which review_venues reads) ≥ {PR.VENUE_GAP:g}; sustained = '
                 f'that gap at {PR.VENUE_SUSTAIN} consecutive held season ends (counted from the world\'s first season, as '
                 f'`venue_watch` starts empty); cooldown = a move in the last {PR.VENUE_MIN_SEASONS} seasons (none were '
                 f'recorded, so it blocks nothing); candidate = a course in the same city that the event\'s level may '
                 f'use (course_library.LEVEL_LAYOUTS) and physically better (prestige.COURSE_QUALITY), not elite in a '
                 f'major week; free = not booked that week in season Y+{PR.VENUE_LAG} and the event still planned at its '
                 f'current course then (with no moves in force, the world\'s venues equal the library plan '
                 f'`CourseLibrary.venues`, so this is reconstructable). The edition\'s week in season Y+{PR.VENUE_LAG} '
                 'comes from the static calendar.')
    lines.append('')
    rows = []
    for a in arms:
        watch = {}
        for y in a['seasons']:
            p = a['summ'][y]['prestige']
            ev, co, vs = p.get('events', {}), p.get('courses', {}), a['summ'][y]['venue_sites']
            c = Counter()
            target = y + PR.VENUE_LAG
            plan = week_of = busy = None
            for sid in sorted(ev):
                s = cal.by_id.get(sid)
                if s is None or s.kind in ('major', 'qualifying') or s.sites != 1:
                    continue
                if sid not in vs:
                    continue                                 # not held this season: the count waits
                c['eligible'] += 1
                cur, lay, city = vs[sid][:3]
                gap = ev[sid] - (co.get(cur) or 0.0)
                n = watch[sid] = watch.get(sid, 0) + 1 if gap >= PR.VENUE_GAP else 0
                c['gap'] += gap >= PR.VENUE_GAP
                c['near'] += abs(gap - PR.VENUE_GAP) <= 0.01
                if n < PR.VENUE_SUSTAIN:
                    continue
                c['sustained'] += 1
                if plan is None:
                    plan = lib.venues(target)
                    week_of = {ed.event_id: ed.week for ed in cal.editions(target)}
                    busy = defaultdict(set)
                    for e2, vv in plan.items():
                        for v in vv:
                            busy[week_of.get(e2)].add(v.course_id)
                e_t = f'{target}:{sid}'
                pl = plan.get(e_t)
                if not pl or len(pl) != 1 or pl[0].course_id != cur or pl[0].city != city:
                    c['blocked: not at this course in Y+2'] += 1
                    continue
                wk = week_of[e_t]
                cur_q = PR.COURSE_QUALITY[(lib.sites[cur]['cls'], lay)]
                better = free = False
                for cid in lib.by_city.get(city, ()):
                    if cid == cur:
                        continue
                    ok = lib._eligible(cid, event_level(s))
                    if not ok:
                        continue
                    cls = lib.sites[cid]['cls']
                    if PR.COURSE_QUALITY[(cls, ok[1])] <= cur_q or (cls == 'elite' and wk in mw):
                        continue
                    better = True
                    free = free or cid not in busy[wk]
                if not better:
                    c['blocked: no better eligible course in the city'] += 1
                elif not free:
                    c['blocked: better course booked that week'] += 1
                else:
                    c['would move'] += 1
            rows.append((a['name'], y, c['eligible'], c['gap'], c['sustained'], 0,
                         c['blocked: not at this course in Y+2'], c['blocked: no better eligible course in the city'],
                         c['blocked: better course booked that week'], c['would move'],
                         len(p['venue_moves_decided']), c['near']))
    lines.append(table(['arm', 'season', 'eligible events held', f'gap ≥ {PR.VENUE_GAP:g}', f'sustained {PR.VENUE_SUSTAIN} season ends',
                        'blocked: cooldown', 'blocked: not at this course in Y+2', 'blocked: no better eligible course in the city',
                        'blocked: better course booked that week', 'reconstructed: would move', 'moves recorded',
                        f'gap within ±0.01 of {PR.VENUE_GAP:g} (unclassifiable)'], rows))
    lines.append('')
    near = sum(r[-1] for r in rows)
    lines.append('A nonzero "reconstructed: would move" alongside zero recorded moves would mean this reconstruction '
                 'differs from the rule as run; the two columns are shown side by side for that check. Rounding: the '
                 'archived event and course prestige are rounded to 0.01, so a gap within ±0.01 of the threshold cannot '
                 f'be classified with certainty; {near} eligible event-seasons fall in that band over these '
                 f'{len(rows)} seasons. Natural move frequency remains unvalidated; the positive fixtures in '
                 'tests/test_venue_moves.py remain valid.')
    lines.append('')



def section3(arms, lines, all_arms=()):
    lines.append('## 3. Two-seed bounded metrics: a18new (seed 4207) and seed2 (seed 5309), defaults')
    lines.append('')
    lines.append('Seasons: ' + '; '.join(seasons_label(a) for a in arms) + '.')
    lines.append('')
    # prestige
    lines.append('### National prestige and participation (season file `prestige.nations`)')
    lines.append('')
    lines.append('Multiplier for the entrants of season Y+1, decided at Y\'s end (participation.py: bounds 0.25–4 of '
                 'the starting value 1, at most ×1.10 or ÷1.10 a year). Step = this season\'s multiplier ÷ the previous '
                 '(1.0 before the first). Share ratio = a nation\'s share ÷ its baseline share (juniors / new pros).')
    lines.append('')
    rows = []
    for a in arms:
        prev = {}
        for y in a['seasons']:
            p = a['summ'][y]['prestige']
            m = p['multiplier']
            if not m:
                rows.append((a['name'], y, 'not recorded', '', '', '', '', '', ''))
                continue
            steps = [m[c] / prev.get(c, 1.0) for c in m]
            out_b = sum(1 for v in m.values() if v < 0.25 - 1e-9 or v > 4 + 1e-9)
            over = sum(1 for s in steps if s > 1.10 + 1e-3 or s < 1 / 1.10 - 1e-3)
            moved = sum(1 for v in m.values() if abs(v - 1) > 0.01)
            sr = {}
            for kind in ('juniors', 'new_pros'):
                sh, bs = p['shares'].get(kind, {}), p['baseline_shares'].get(kind, {})
                r = [sh[c] / bs[c] for c in sh if bs.get(c)]
                sr[kind] = f'{min(r):.2f}–{max(r):.2f}' if r else '—'
            rows.append((a['name'], y, len(m), f'{min(m.values()):.3f}–{max(m.values()):.3f}', moved,
                         f'{min(steps):.3f}–{max(steps):.3f}', f'{out_b} / {over}', sr['juniors'], sr['new_pros']))
            prev = m
    lines.append(table(['arm', 'season', 'nations', 'multiplier range', 'nations moved >1%', 'step range',
                        'outside 0.25–4 / step beyond 1.1', 'junior share ratio', 'new-pro share ratio'], rows))
    lines.append('')
    for a in arms:
        if not a['seasons']:
            continue
        last = a['summ'][a['seasons'][-1]]['prestige']
        m = last['multiplier']
        if m:
            top = sorted(m.items(), key=lambda kv: kv[1])
            lines.append(f'- {a["name"]} after {a["seasons"][-1]}: lowest multipliers '
                         + ', '.join(f'{c} {v:.3f}' for c, v in top[:3]) + '; highest '
                         + ', '.join(f'{c} {v:.3f}' for c, v in top[-3:][::-1]) + '.')
    lines.append('')
    rows = []
    for a in arms:
        for y in a['seasons']:
            p = a['summ'][y]['prestige']
            rows.append((a['name'], y, len(p['venue_moves_decided']), p['venue_moves_total']))
    lines.append('Venue moves (`prestige.venue_moves_decided` at the season\'s end; `venue_moves`: every move decided so far):')
    lines.append('')
    lines.append(table(['arm', 'season', 'decided this season', 'all decided so far'], rows))
    lines.append('')
    venue_section(arms, lines)
    allocation_check(all_arms, lines)
    # recruitment
    lines.append('### Recruitment (relations table: stints and refusals)')
    lines.append('')
    lines.append('Staff-initiated offers = stints started by a coach or caddie (accepted) + refusals asked by a coach or '
                 'caddie (turned down), by the year the approach was made, within the committed seasons (the winter '
                 'after a season is recorded in that season\'s year, week 53). Coach arrangement "share" = youth '
                 'scouting (a share of future prize money), "fee" = an approach to an established player. The first year '
                 'includes the approaches made as the world starts (week 1).')
    lines.append('')
    for a in arms:
        if not a['seasons']:
            continue
        ys = set(a['seasons'])
        acc = Counter()
        ref = Counter()
        acc_reason, ref_reason = Counter(), Counter()
        gol = Counter()
        for kind, staff, golfer, start, arr, by, rs, ra in a['relations']['stints']:
            if start[0] not in ys:
                continue
            if by in ('coach', 'caddie'):
                k = (start[0], kind, arr if kind == 'coach' else 'bag')
                acc[k] += 1
                acc_reason[(kind, (ra or '').split(' (')[0][:70])] += 1
            elif by == 'golfer':
                gol[(start[0], kind)] += 1
        for r in a['relations']['refusals']:
            kind, staff, golfer, yy, wk, asked, refused, why_asked, why_no = r[:9]
            if yy not in ys or asked not in ('coach', 'caddie'):
                continue
            ref[(yy, kind)] += 1
            ref_reason[(kind, why_no.split(' (')[0][:70])] += 1
        rows = []
        for y in a['seasons']:
            ca_s, ca_f = acc[(y, 'coach', 'share')], acc[(y, 'coach', 'fee')]
            cd = acc[(y, 'caddie', 'bag')]
            other = sum(v for (yy, k, ar), v in acc.items() if yy == y and k == 'coach' and ar not in ('share', 'fee'))
            rc, rk = ref[(y, 'coach')], ref[(y, 'caddie')]
            rows.append((y, ca_s + ca_f + other + rc, f'{ca_s} / {ca_f}' + (f' (+{other})' if other else ''),
                         frac(ca_s + ca_f + other, ca_s + ca_f + other + rc), rc, cd + rk, cd, frac(cd, cd + rk), rk,
                         gol[(y, 'coach')], gol[(y, 'caddie')]))
        lines.append(f'**{a["name"]}**')
        lines.append('')
        lines.append(table(['year', 'coach offers', 'coach accepted: share / fee', 'coach accepted / offers', 'coach refused',
                            'caddie offers', 'caddie accepted', 'caddie accepted / offers', 'caddie refused',
                            'golfer-initiated coach stints', 'golfer-initiated caddie stints'], rows))
        lines.append('')
        lines.append('Reasons accepted (top): ' + '; '.join(f'{k} — {r or "(none recorded)"}: {v}'
                                                          for (k, r), v in acc_reason.most_common(6)))
        lines.append('')
        lines.append('Reasons refused (top): ' + '; '.join(f'{k} — {r}: {v}' for (k, r), v in ref_reason.most_common(8)))
        lines.append('')
    # weather
    lines.append('### Weather (round conditions in the season files)')
    lines.append('')
    lines.append('Each round of each event site: [wind mph, wet 0/1, pins, wind from, gustiness] (weather.archived). '
                 'Climate group and hemisphere from the course\'s city (weather.climate_of, the build\'s course library; '
                 'the city recorded with the site otherwise); local month = the calendar month of the event week, '
                 'six months on for southern-hemisphere courses (the climate table\'s convention). All tiers.')
    lines.append('')
    MON = 'JFMAMJJASOND'
    for a in arms:
        if not a['seasons']:
            continue
        rowsw = [r for y in a['seasons'] for r in a['summ'][y]['weather']]
        if not rowsw:
            continue
        groups = sorted({r[0] for r in rowsw})
        cell = defaultdict(list)
        for g, cm, lm, coastal, south, wind, wet, gust, tier in rowsw:
            cell[(g, lm)].append((wind, wet, gust))
        nog = sum(1 for r in rowsw if r[7] is None)
        lines.append(f'**{a["name"]}**: {len(rowsw):,} rounds; wind mph {dist([r[5] for r in rowsw], 1)}; '
                     f'wet {pct(sum(r[6] for r in rowsw), len(rowsw))}; gustiness '
                     f'{dist([r[7] for r in rowsw if r[7] is not None], 2)}; gustiness not recorded on {nog} rounds.')
        lines.append('')
        for title, f in (('mean wind (mph)', lambda v: f'{S.mean(x[0] for x in v):.1f}'),
                         ('wet rounds (%)', lambda v: f'{100 * S.mean(x[1] for x in v):.0f}'),
                         ('mean gustiness', lambda v: f'{S.mean(x[2] for x in v if x[2] is not None):.2f}'
                          if any(x[2] is not None for x in v) else '—'),
                         ('rounds', lambda v: str(len(v)))):
            rows = [(g, *[f(cell[(g, m)]) if cell.get((g, m)) else '·' for m in range(12)]) for g in groups]
            lines.append(f'{title}, by climate group × local month:')
            lines.append('')
            lines.append(table(['climate', *MON], rows))
            lines.append('')
        cm_cell = defaultdict(list)
        for g, cm, lm, coastal, south, wind, wet, gust, tier in rowsw:
            cm_cell[cm].append((wind, wet))
        lines.append('By calendar month (all courses): ' + ', '.join(
            f'{MON[m]} {S.mean(x[0] for x in cm_cell[m]):.1f} mph/{100 * S.mean(x[1] for x in cm_cell[m]):.0f}% wet'
            for m in range(12) if cm_cell.get(m)) + '.')
        lines.append('')
    # familiarity
    lines.append('### Familiarity: regional baseline and home-club floor')
    lines.append('')
    lines.append('Baseline starts = season file `familiar_base` (starts where the regional baseline, home-club floor '
                 'included, exceeded the rounds played there: Season.course_baseline vs the golfer\'s familiarity). The '
                 'home-club floor is not recorded separately per start: "starts at a by-country home club" counts starts '
                 'at the golfer\'s home club of that date when the club was found by country (the only case where the '
                 'floor can add anything; it applies there only while fewer than 3 rounds were played) — an upper bound. '
                 'Golfers whose current home-club familiarity comes from the floor (`home_club_familiarity.from` = "home club") '
                 'are counted from the latest people table (state at the last committed season only).')
    lines.append('')
    rows = []
    for a in arms:
        for y in a['seasons']:
            s = a['summ'][y]
            tot = sum(s['all_starts'].values())
            fb = s['familiar_base']
            hf = s['home_floor_starts']
            rows.append((a['name'], y, f'{tot:,}', frac(sum(fb.values()), tot), f'{len(fb):,} of {len(s["all_starts"]):,}',
                         sum(hf.values()), len(hf)))
    lines.append(table(['arm', 'season', 'starts', 'baseline applied', 'golfers with any', 'starts at a by-country home club',
                        'golfers'], rows))
    lines.append('')
    for a in arms:
        if not a['seasons']:
            continue
        ppl = [p for p in a['people'].values() if p['hc_basis'] is not None]
        lines.append(f'- {a["name"]} (people table {a["people_file"]}): golfers with a home club recorded (retired '
                     f'included) {len(ppl):,}; found by '
                     f'country {frac(sum(1 for p in ppl if p["hc_basis"] == "country"), len(ppl))}; current home-club '
                     f'familiarity from: ' + ', '.join(f'{k} {v}' for k, v in Counter(p['hc_from'] for p in ppl).most_common()))
    lines.append('')


# ---- section 5: amateur return and re-block (D5.c) -----------------------------------------------------------------
RETURN_KIND = 'amateur returned to full-time golf'           # golfsim/amateur_return.KIND
BANDS5 = (('18–20', 18, 20), ('21–24', 21, 24), ('25–29', 25, 29), ('30+', 30, 999))


def band5(age):
    return next((b for b, lo, hi in BANDS5 if age is not None and lo <= age <= hi), 'unknown')


def section_return(arms, lines):
    lines.append('## 5. Amateur return and re-block (D5.c), all four arms')
    lines.append('')
    lines.append('Sources (the build\'s own records, read from the season files): **episodes** are the winter transitions '
                 f'"{RETURN_KIND}" in season Y\'s `transitions` (careers.decide: `note(AR.KIND, …)` after a successful '
                 'draw), effective in season Y+1, with the age recorded at the decision; **evaluations** are every '
                 '`amateur_return` row of decision evidence /2 (`careers` part): careers.decide records one for every '
                 'part-time non-college amateur it evaluates, including p = 0 (a blocking condition: work, funds or '
                 'results; no draw then). Return rates use all evaluations as the denominator, and separately the '
                 'eligible ones (p > 0); the denominator is never limited to former pathway entrants. For each episode '
                 'whose season Y+1 is archived: any cash-blocked week in Y+1 (season file `cash_blocked_max` ≥ 1: only '
                 'a genuinely unaffordable week adds to it), a work-pathway re-entry in Y+1 (`work_pathway`; entries '
                 'whose in-season count stayed below 8 used a count carried over), a winter "amateur took a job" '
                 'decision after Y+1, starts in Y+1 (`careers.events`), and the competing outcomes of the winter after '
                 'Y+1 (turned pro or comeback, retired, became coach or caddie, death in that winter from the people '
                 'table). Returns in an arm\'s last season have no archived Y+1: they are **censored**, counted '
                 'separately, never as successes. Episodes are not independent people: a golfer can return more than '
                 'once, so unique people are counted separately. Age bands by age at the decision.')
    lines.append('')
    head = ['band', 'evaluations (all, p = 0 included)', 'eligible (p > 0)', 'returns (episodes)', 'returns / all evaluations',
            'returns / eligible', 'unique people', 'censored (no archived Y+1)', 'any cash-blocked week in Y+1',
            'pathway re-entry in Y+1 (count carried)', 'winter "took a job" after Y+1', 'starts in Y+1 (min/q1/med/q3/max)',
            'turned pro / comeback', 'retired', 'became staff', 'died']
    pooled = defaultdict(Counter)
    pooled_starts = defaultdict(list)
    pooled_people = defaultdict(set)
    checks = []
    A1_missing, A2_fail, A3_fail = [], [], []
    A1_n = A2_n = A3_n = 0
    absent_zero = Counter()
    for a in arms:
        if not a['seasons'] or 'ar_ev' not in a['summ'][a['seasons'][0]]:
            continue
        for y in a['seasons']:                       # assertion 2: every season's inputs are present
            S_ = a['summ'][y]
            A2_n += 1
            why = []
            if S_.get('evidence_format') != 'golf-legacy-decision-evidence/2':
                why.append(f'format {S_.get("evidence_format")}')
            if not {'amateur_return', 'amateur_job'} <= set(S_.get('evidence_models') or ()):
                why.append('models ' + ','.join(S_.get('evidence_models') or ()))
            if not S_.get('cash_blocked_present'):
                why.append('cash_blocked_max missing')
            if not S_.get('work_pathway_present'):
                why.append('work_pathway missing')
            if why:
                A2_fail.append(f'{a["name"]} {y}: ' + '; '.join(why))
        tr = Counter((t['gid'], y) for y in a['seasons'] for t in a['summ'][y]['transitions'] if t.get('kind') == RETURN_KIND)
        evp = Counter((g, y) for y in a['seasons'] for g, r_ in a['summ'][y]['ar_ev'].items() if r_[2] == 1)
        A3_n += len(tr)
        for k in sorted(set(tr) | set(evp)):         # assertion 3: one-to-one per (arm, golfer, year)
            if tr.get(k, 0) != 1 or evp.get(k, 0) != 1:
                A3_fail.append(f'{a["name"]} golfer {k[0]} {k[1]}: transitions {tr.get(k, 0)}, positive evaluations {evp.get(k, 0)}')
        last = a['seasons'][-1]
        C = defaultdict(Counter)
        starts = defaultdict(list)
        people = defaultdict(set)
        n_ev_out = n_tr = 0
        for y in a['seasons']:
            S_ = a['summ'][y]
            for g, r_ in S_['ar_ev'].items():
                p, u, out, age, blocked = r_[:5]
                if age is None:
                    born = (a['people'].get(g) or {}).get('born')
                    age = y - born if born else None
                for b in (band5(age), 'all'):
                    C[b]['ev'] += 1
                    C[b]['elig'] += (p or 0) > 0
                n_ev_out += out == 1
            for t in S_['transitions']:
                if t.get('kind') != RETURN_KIND:
                    continue
                n_tr += 1
                g, age = t['gid'], t.get('age')
                bs = (band5(age), 'all')
                for b in bs:
                    C[b]['ret'] += 1
                    people[b].add(g)
                if y == last:
                    for b in bs:
                        C[b]['cens'] += 1
                    continue
                S1 = a['summ'][y + 1]
                A1_n += 1
                if g not in S1['careers']:                   # assertion 1: a Y+1 career row, never a silent zero
                    A1_missing.append(f'{a["name"]} golfer {g} return {y}')
                absent_zero['cash_blocked_max'] += g not in S1['cash_blocked_max']
                cb = S1['cash_blocked_max'].get(g, 0)        # (a present map without the golfer: zero, counted)
                re_ = [r for r in S1['work_pathway'] if r['gid'] == g]
                tj = any(t2.get('gid') == g and t2.get('kind') == 'amateur took a job' for t2 in S1['transitions'])
                kinds = {t2['kind'] for t2 in S1['transitions'] if t2.get('gid') == g}
                died = (a['people'].get(g) or {}).get('died')
                for b in bs:
                    C[b]['obs'] += 1
                    C[b]['blocked'] += cb >= 1
                    C[b]['reentry'] += bool(re_)
                    C[b]['carried'] += bool(re_) and cb < 8
                    C[b]['tookjob'] += tj
                    C[b]['pro'] += bool(kinds & {'turned pro', 'comeback'})
                    C[b]['retired'] += 'retired' in kinds
                    C[b]['staff'] += bool(kinds & {'became coach', 'became caddie'})
                    C[b]['died'] += died is not None and died in (y, y + 1)
                    if g in S1['careers']:
                        starts[b].append(S1['careers'][g]['events'])
        checks.append(f'{a["name"]}: {n_tr} return transitions, {n_ev_out} evaluations with outcome 1'
                      + ('' if n_tr == n_ev_out else ' (DIFFER)'))
        rows = []
        for b in [x for x, _, _ in BANDS5] + ['unknown', 'all']:
            c = C[b]
            if not c['ev'] and not c['ret']:
                continue
            rows.append(row5(b, c, len(people[b]), starts[b]))
            for k, v in c.items():
                pooled[b][k] += v
            pooled_starts[b] += starts[b]
            pooled_people[b] |= {(a['name'], g) for g in people[b]}
        lines.append(f'**{a["name"]}** ({seasons_label(a)}; censored = returns decided in {last})')
        lines.append('')
        lines.append(table(head, rows))
        lines.append('')
    rows = [row5(b, pooled[b], len(pooled_people[b]), pooled_starts[b]) for b in [x for x, _, _ in BANDS5] + ['unknown', 'all']
            if pooled[b]['ev'] or pooled[b]['ret']]
    lines.append('**POOLED over the four arms** — sums of episodes from different worlds (two seeds, three rule settings); '
                 'unique people are (arm, golfer) pairs; no causal reading.')
    lines.append('')
    lines.append(table(head, rows))
    lines.append('')
    lines.append('Consistency of the two sources: ' + '; '.join(checks) + '. Death counts a death in the winter of the '
                 'return or the winter after Y+1 (people table `died`).')
    lines.append('')
    obs = pooled['all']['obs']
    lines.append(f'**Two different events, reported separately (pooled, observed returns):** a winter "amateur took a '
                 f'job" career decision after Y+1: {frac(pooled["all"]["tookjob"], obs)}; a mid-season cash re-block '
                 f'or a work-pathway re-entry during Y+1: {frac(pooled["all"]["blocked"], obs)} with any cash-blocked '
                 f'week, {frac(pooled["all"]["reentry"], obs)} re-entries. Neither stands in for the other.')
    lines.append('')
    res = lambda fails: 'PASS' if not fails else f'FAIL ({len(fails)}): ' + '; '.join(fails[:20]) + (' …' if len(fails) > 20 else '')
    for msg in ([f'A1 {x}' for x in A1_missing] + [f'A2 {x}' for x in A2_fail] + [f'A3 {x}' for x in A3_fail]):
        print('FAIL', msg, flush=True)
    lines.append('**Completeness assertions** (analysis-only; a failure is printed with its ids):')
    lines.append('')
    lines.append(f'- A1, a season-(Y+1) career row for every observed return (starts are never defaulted to zero): '
                 f'{A1_n - len(A1_missing)}/{A1_n} — {res(A1_missing)}.'
                 + (f' Smallest Y+1 starts among them: {min(pooled_starts["all"])}.' if pooled_starts['all'] else ''))
    lines.append(f'- A2, inputs present in every season used (decision evidence format golf-legacy-decision-evidence/2 '
                 f'with the `amateur_return` and `amateur_job` models; `cash_blocked_max` and `work_pathway` present): '
                 f'{A2_n - len(A2_fail)}/{A2_n} seasons — {res(A2_fail)}. A present map without the golfer means zero '
                 f'(counted: {absent_zero["cash_blocked_max"]} observed returns absent from the Y+1 `cash_blocked_max`).')
    lines.append(f'- A3, return transitions and positive `amateur_return` evaluations matched one-to-one per (arm, golfer, '
                 f'year): {A3_n} transitions — {res(A3_fail)}.')
    lines.append('')
    section_return_jobs(arms, lines)


def section_return_jobs(arms, lines):
    """5.1: the job probability anticipated at return vs the decision faced the following winter."""
    lines.append('### 5.1 The job chance anticipated at return vs the next winter\'s job decision')
    lines.append('')
    lines.append('**What the rule discounts.** The return chance is `min(CAP, sig(x) × keep_up)` '
                 '(golfsim/amateur_return.py lines 142 and 147), where `keep_up` (lines 150–160) is `1 − '
                 'careers.p_amateur_job(season, g, row, year + 1)` evaluated in the return winter Y, after the turn-pro '
                 'draw and before the golfer\'s lifestyle changes (careers.py line 468), with cash and family money '
                 'reduced by the full-time season cost (savings first, then family money: line 155) and restored '
                 'afterwards. So it discounts the same decision function the next winter applies (careers.py lines '
                 '355–365: `x = −1.2 + 0.8 (age − 22) − 0.4 min(runway, 5) + 1[cash < 0]`, at age Y+1) — the same kind '
                 'of event, a full-time amateur taking a job in the winter after Y+1 (careers.decide lines 449–458) — '
                 'evaluated on projected rather than actual inputs, so it is a proxy for that draw, not the draw itself. '
                 'The runway is `runway_years` (careers.py 81–96, called with own_money False): funds `season.funds(g, '
                 'Y+2)` = cash + family money (backing) + backers\' funds + a credit line (season.py 3109–3113) over the '
                 'season\'s shortfall (`season_forecast`, season.py 3313–3338: events × trip cost + 52 × committed '
                 'weekly cost − income; amateurs take no prize money and have no sponsor income). The committed weekly '
                 'cost is `max(0, living − salary)` plus any coach fee (season.py 3123–3127; finance.weekly_living, '
                 'finance.py 197–203): zero living cost for a part-time amateur (living 40,000, salary 52,000) and for a '
                 'full-time amateur alike, so being part-time at the prediction makes no difference to committed costs. '
                 'Where the projected inputs can differ from the actual ones, per the code: (a) events = max(8, the '
                 'starts of season Y) at the prediction against max(8, the starts of Y+1) at the decision — this can '
                 'move p through the shortfall and so the runway (only while the runway is under the cap of 5); (b) '
                 'cash and family money at the prediction are the projected balances after the season cost with no other '
                 'money in or out, so the debt term cannot be on, while the decision uses the actual balances — this can '
                 'move p through the runway funds and the debt term; (c) the credit line: `season.funds(g, Y+2)` reads '
                 'the Y+1 ledger\'s earnings, which do not exist yet at the prediction (base limit); at the decision it '
                 'is the base limit plus a share of Y+1 earnings net of support — it can move p only if the golfer had '
                 'such earnings in Y+1, which was not extracted per golfer; (d) the trip cost is computed from where the '
                 'golfer lives and their caddie at each point (season.py 3297–3305), and residence moves and staff changes '
                 'in the winter after the return come after this decision (season.py 2647 then 2668) — this can move p '
                 'where they changed. The logged inputs do not separate these: the prediction\'s runway, funds and '
                 'shortfall are not logged (only `keep_up`), so the drift below is not attributed to any one of them. '
                 'The actual decision is reached only if the golfer did not retire (line 415) or turn professional '
                 '(line 433) first and is a full-time non-college amateur aged 19+. The other route to work in Y+1, '
                 'the mid-season work pathway, had 0 re-entries (above).')
    lines.append('')
    lines.append('**Data.** Prediction: the stored `keep_up` input of the return\'s decision evidence /2 '
                 '`amateur_return` row (rounded to 3 decimals by decision_evidence._input), so predicted p = 1 − '
                 'keep_up; not recomputed. Actual: the following winter\'s `amateur_job` row for that golfer (p, '
                 'its draw u, outcome, and inputs age, runway, cash), read as stored. Population: the observed '
                 'returns (season Y+1 archived; censored excluded). Episodes and unique (arm, golfer) pairs are shown '
                 'side by side: a golfer who returned twice contributes two episodes, which are not independent. '
                 'Denominators: "ALL" columns use every observed return (N); "MATCHED" columns use only the golfers '
                 'evaluated for a job in the winter after Y+1 (n; the others turned professional first, before any job '
                 'draw), so predicted and evaluated p are compared over the same people. '
                 'Money: two different recorded figures, not a measured change in one balance. The prediction\'s '
                 'logged figure is the projected funds (`funds_k − season_cost_k`: savings plus family money after the '
                 'season), shown for all N and for the matched n; the decision\'s stored `cash_k` is savings only, '
                 'logged only for the matched n. Family money enters p_amateur_job at the decision through the runway '
                 'funds, which are not logged. So comparing the two figures sets a funds projection against a '
                 'savings-only log, and it does not show the input the function actually used at the decision. Also shown: Overall and amateur rank at the end of Y and Y+1 '
                 '(season file `careers`), the age used at each point, and how often the debt term was on at the '
                 'decision.')
    lines.append('')
    head = ['arm', 'band', 'episodes (unique people)', 'not evaluated next winter (why)',
            'ALL observed returns (denominator N): predicted mean p', 'ALL: Σ predicted p vs took a job (n/N)',
            'MATCHED, evaluated next winter (denominator n): predicted mean p', 'MATCHED: Σ predicted p',
            'MATCHED: evaluated mean p', 'MATCHED: Σ evaluated p', 'MATCHED: took a job (n)',
            'money, two recorded figures (medians, $k): projected funds at prediction — all N / matched n; '
            'savings-only cash_k at decision — matched n',
            'Overall change, end Y → end Y+1 (median, all N)', 'amateur rank end Y; end Y+1 (medians, all N)',
            'age used by the prediction (age at Y + 1) / at the decision', 'debt term on at the decision (matched n)']
    rows, pool = [], defaultdict(lambda: defaultdict(list))
    for a in arms:
        if not a['seasons'] or 'aj_ev' not in a['summ'][a['seasons'][0]]:
            continue
        D = defaultdict(lambda: defaultdict(list))
        for y in a['seasons'][:-1]:
            S0, S1 = a['summ'][y], a['summ'][y + 1]
            for t in S0['transitions']:
                if t.get('kind') != RETURN_KIND:
                    continue
                g = t['gid']
                r = S0['ar_ev'].get(g)
                inp = r[5] if r and len(r) > 5 else {}
                ku = inp.get('keep_up')
                aj = S1['aj_ev'].get(g)
                kinds = {t2['kind'] for t2 in S1['transitions'] if t2.get('gid') == g}
                c0, c1 = S0['careers'].get(g) or {}, S1['careers'].get(g) or {}
                rec = {'gid': (a['name'], g), 'pred': None if ku is None else 1 - ku,
                       'took': 'amateur took a job' in kinds}
                if aj:
                    p, u, out, ain, terms = aj
                    rec.update(act=p, out=out, cash=ain.get('cash_k'), debt=(terms.get('debt') or 0) > 0, age1=ain.get('age'))
                else:
                    rec['why'] = ('turned pro / comeback' if kinds & {'turned pro', 'comeback'} else 'retired or staff'
                                  if kinds & {'retired', 'became coach', 'became caddie'} else
                                  f'{c1.get("status")} {c1.get("lifestyle")}' if c1 else 'no Y+1 row')
                if inp.get('funds_k') is not None and inp.get('season_cost_k') is not None:
                    rec['proj'] = inp['funds_k'] - inp['season_cost_k']
                rec['age0'] = None if inp.get('age') is None else inp['age'] + 1   # keep_up evaluates at Y+1's age
                if c0.get('overall') is not None and c1.get('overall') is not None:
                    rec['dov'] = c1['overall'] - c0['overall']
                rec['r0'], rec['r1'] = c0.get('am_end'), c1.get('am_end')
                for b in (band5(t.get('age')), 'all'):
                    D[b]['r'].append(rec)
                    pool[b]['r'].append(rec)
        for b in [x for x, _, _ in BANDS5] + ['all']:
            if D[b]['r']:
                rows.append(row51(a['name'], b, D[b]['r']))
    for b in [x for x, _, _ in BANDS5] + ['all']:
        if pool[b]['r']:
            rows.append(row51('POOLED (four arms; sums of episodes from different worlds)', b, pool[b]['r']))
    lines.append(table(head, rows))
    lines.append('')
    lines.append('Return-rate denominators (the table above section 5.1): "returns / all evaluations" counts every '
                 '`amateur_return` evaluation, including p = 0 (blocked by work, funds or results: the discount never '
                 'enters those); "returns / eligible" counts only p > 0, where the chance is already multiplied by the '
                 'anticipated keep-up factor (and capped at 0.6), so the discount lowers the eligible-rate numerator '
                 'directly and the all-evaluations rate only through the eligible ones. Differences between predicted '
                 'and evaluated p are described only by the recorded inputs above, which cannot separate their causes; '
                 'no tuning is recommended.')
    lines.append('')


def row51(name, b, R):
    md = lambda xs: f'{S.median(xs):.1f}' if xs else '—'
    pred = [r['pred'] for r in R if r['pred'] is not None]
    ev = [r for r in R if 'act' in r]
    evp = [r['pred'] for r in ev if r['pred'] is not None]
    why = Counter(r['why'] for r in R if 'act' not in r)
    took = sum(r['took'] for r in R)
    took_ev = sum(r['out'] for r in ev)
    return (name, b, f'{len(R)} ({len({r["gid"] for r in R})})',
            '; '.join(f'{k} {v}' for k, v in why.most_common()) or '—',
            f'{S.mean(pred):.3f}' if pred else '—', f'{sum(pred):.1f} vs {frac(took, len(R))}',
            f'{S.mean(evp):.3f}' if evp else '—', f'{sum(evp):.1f}',
            f'{S.mean([r["act"] for r in ev]):.3f}' if ev else '—', f'{sum(r["act"] for r in ev):.1f}',
            frac(took_ev, len(ev)),
            f'{md([r["proj"] for r in R if r.get("proj") is not None])} / '
            f'{md([r["proj"] for r in ev if r.get("proj") is not None])}; '
            f'{md([r["cash"] for r in ev if r.get("cash") is not None])}',
            f'{S.median([r["dov"] for r in R if "dov" in r]):+.1f}' if any('dov' in r for r in R) else '—',
            f'{md([r["r0"] for r in R if r["r0"]])}; {md([r["r1"] for r in R if r["r1"]])}',
            f'{md([r["age0"] for r in R if r.get("age0") is not None])} / {md([r["age1"] for r in ev if r.get("age1") is not None])}',
            frac(sum(r.get('debt', False) for r in ev), len(ev)))


def row5(b, c, people, starts):
    o = c['obs']
    return (b, c['ev'], c['elig'], c['ret'], frac(c['ret'], c['ev'], 2), frac(c['ret'], c['elig'], 1), people,
            frac(c['cens'], c['ret']), frac(c['blocked'], o), f'{frac(c["reentry"], o)} ({c["carried"]})',
            frac(c['tookjob'], o), dist(starts), frac(c['pro'], o), frac(c['retired'], o), frac(c['staff'], o),
            frac(c['died'], o))


# ---- section 6: upset snapshot cost ------------------------------------------------------------------------------
def section_upsets(lines, path):
    lines.append('## 6. Upset snapshot cost (a18new and seed2)')
    lines.append('')
    if not path.exists():
        lines += ['Not measured yet (run `upset_cost.py`).', '']
        return
    u = json.loads(path.read_text())
    lines.append('Bytes of each edition\'s archived `upset` record (golfsim/upsets.record), in the archive\'s own JSON '
                 'encoding (compact separators, archive._write). "gzip alone" compresses a season\'s upset records (or '
                 'their `inputs` snapshots) by themselves at the archive\'s level 6: an approximation of their '
                 'contribution inside the whole-file compression, not an exact share of the gzip file.')
    lines.append('')
    rows, tot = [], Counter()
    for name, arm in u['arms'].items():
        for r in arm['seasons']:
            rows.append((name, r['year'], r['with_upset'], f'{r["upset_json"] / 1e6:.2f} MB', f'{r["upset_json"] / r["with_upset"]:.0f}',
                         f'{r["inputs_json"] / 1e6:.2f} MB', f'{r["inputs_json"] / r["with_upset"]:.0f}',
                         pct(r['upset_json'], r['file_raw']), pct(r['inputs_json'], r['file_raw']),
                         f'{r["upset_gz_alone"] / 1e6:.2f} MB', f'{r["inputs_gz_alone"] / 1e6:.2f} MB',
                         pct(r['upset_gz_alone'], r['file_gz']), f'{r["file_gz"] / 1e6:.1f} MB'))
            for k in ('with_upset', 'upset_json', 'inputs_json', 'file_raw', 'upset_gz_alone', 'inputs_gz_alone', 'file_gz'):
                tot[k] += r[k]
    rows.append(('all', f'{sum(len(a["seasons"]) for a in u["arms"].values())} seasons', tot['with_upset'],
                 f'{tot["upset_json"] / 1e6:.1f} MB', f'{tot["upset_json"] / tot["with_upset"]:.0f}',
                 f'{tot["inputs_json"] / 1e6:.1f} MB', f'{tot["inputs_json"] / tot["with_upset"]:.0f}',
                 pct(tot['upset_json'], tot['file_raw']), pct(tot['inputs_json'], tot['file_raw']),
                 f'{tot["upset_gz_alone"] / 1e6:.1f} MB', f'{tot["inputs_gz_alone"] / 1e6:.1f} MB',
                 pct(tot['upset_gz_alone'], tot['file_gz']), f'{tot["file_gz"] / 1e6:.0f} MB'))
    lines.append(table(['arm', 'season', 'editions with a record', 'upset JSON', 'bytes / edition', 'inputs JSON',
                        'inputs bytes / edition', 'upset share of raw season file', 'inputs share of raw',
                        'upset gzip alone', 'inputs gzip alone', 'upset gzip alone / season .gz', 'season .gz'], rows))
    lines.append('')
    lines.append('**CPU: offline recomputation from stored inputs.** It excludes the fact capture at field-set time and '
                 'any engine-side bookkeeping, so it is not the in-engine overhead (the season engine has no per-phase '
                 'timing for upset estimates, and none is inferred from season run times). Each estimated record\'s '
                 '`inputs` snapshot (ids, Overall, rounds) is passed to `golfsim.upsets.reproduce`; only that call is '
                 'timed, with process CPU time, under `nice -n 19` while the test suite ran.')
    lines.append('')
    rows = [(c['arm'], c['year'], c['editions'], f'{c["equal"]}/{c["editions"]}', f'{c["max_abs_diff"]:g}', c['cpu_total_s'],
             c['cpu_per_edition_ms'], c['cpu_median_ms'], c['cpu_max_ms']) for c in u['cpu']]
    lines.append(table(['arm', 'season', 'estimated records recomputed', 'reproduced = stored (top 5, favourite, winner)',
                        'largest absolute difference', 'CPU per season (s)', 'CPU per edition, mean (ms)', 'median (ms)',
                        'max (ms)'], rows))
    lines.append('')


# ---- section 4: story timing -------------------------------------------------------------------------------------
def section4(lines, timing_path):
    lines.append('## 4. Story timing on the pinned long archive (run A, 45 seasons, build 473690a)')
    lines.append('')
    if not timing_path.exists():
        lines.append('Not measured yet (run `analyze.py --stories`).')
        lines.append('')
        return
    t = json.loads(timing_path.read_text())
    P = t['passes']
    sec = lambda k: [r['seconds'] for r in P[k]['rows'] if r.get('found', True)]
    c1, c2 = sec('1 cold, as first opened'), sec('2 cold facts, story index complete')
    lf, si = t.get('latest_first') or {}, t.get('side_index') or {}
    lines.append('**Scope and how it was measured.** This is evidence for indexed story assembly only: the benchmark '
                 'calls `observer_stories.tell` (facts assembly plus narration) through the observer\'s read-only '
                 'history; it does not cover full UI page rendering and was not run on the owner\'s hardware. "Cold" '
                 'means application-cache cold (an empty story cache and no decoded season in the process), not '
                 'filesystem cold: the season files may have been in the operating system\'s page cache. The sample is '
                 f'{len(c1)} majors spread over the legacy 473690a 45-season archive (run A), assembled by the candidate '
                 f'build\'s (c0d1ea5) assembler. Figures from story_timing.json: cold median {S.median(c1):.2f} s, max '
                 f'{max(c1):.2f} s; with the story index built, median {S.median(c2):.3f} s; the latest edition opened '
                 f'first: {lf.get("first_s", float("nan")):.2f} s with its facts marked pending, then '
                 f'{lf.get("indexer_s", float("nan")):.0f} s of background story indexing; the separate one-off read-only '
                 f'side index: {si.get("seconds", float("nan")):.0f} s, {si.get("bytes", 0) / 1e9:.2f} GB.')
    lines.append('')
    lines.append(f'**Memory.** The {t.get("peak_mb", 0) / 1000:.2f} GB RSS is the timing process\'s lifetime high-water '
                 'mark (ru_maxrss), reached as decoded seasons accumulated up to the archive\'s cache bound; it is not a '
                 'per-story allocation and does not show the absence of a leak. **Rounding:** a time shown as 0.000 s is '
                 'below the timer\'s displayed precision, not zero.')
    lines.append('')
    lines.append('**Missing estimates.** The missing pre-event win estimates (so no upset is claimed in these stories) '
                 'are a limit of the legacy archive, which predates them; upset-story behaviour in new worlds is covered '
                 'separately by the test suite (tests/test_upset_examples.py, e.g. '
                 '`test_no_upset_is_claimed_and_the_missing_estimate_is_named`; tests/test_stories.py, e.g. '
                 '`test_upset_only_with_a_recorded_estimate`, `test_upset_text_states_the_estimate`).')
    lines.append('')
    lines.append('**Not claimed.** This section does not claim instant cold opens in the UI, and does not claim the '
                 'local 120 s season target is verified.')
    lines.append('')
    lines.append(t.get('summary_md', ''))
    lines.append('')


# ---- main ----------------------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arms', nargs='*', default=[], help='name=folder (defaults: the four arms)')
    ap.add_argument('--build', default=str(DEFAULT_BUILD))
    ap.add_argument('--out', default=str(HERE / 'ARMS_COMPARISON.md'))
    ap.add_argument('--stories', action='store_true', help='(re)measure story timing on --story-archive first')
    ap.add_argument('--story-archive', default=str(DEFAULT_STORY_ARCHIVE))
    ap.add_argument('--story-args', default='', help='extra arguments for stories_timing.py')
    ap.add_argument('--publish', action='store_true', help='also refresh armsan/publish/ (scripts, report, timing)')
    ap.add_argument('--publish-only', action='store_true', help='refresh armsan/publish/ from the existing report '
                    'files without re-reading any run')
    a = ap.parse_args()
    if a.publish_only:
        publish(Path(a.out))
        return
    folders = dict(DEFAULT_ARMS)
    for kv in a.arms:
        k, v = kv.split('=', 1)
        folders[k] = Path(v)
    t0 = time.perf_counter()
    if a.stories:
        cmd = ['nice', '-n', '19', 'ionice', '-c3', sys.executable, '-B', str(HERE / 'stories_timing.py'), '--build', a.build,
               '--archive', a.story_archive, '--out', str(HERE / 'story_timing.json')] + a.story_args.split()
        print('story timing:', ' '.join(cmd), flush=True)
        subprocess.run(cmd, check=False)
    arms = {}
    for k in ('a21old', 'a18old', 'a18new', 'seed2'):
        f = folders[k]
        if not (f / 'manifest.json').exists():
            arms[k] = {'name': k, 'seasons': [], 'man': {}, 'folder': str(f), 'note': 'not started'}
            print(f'{k}: not started', flush=True)
            continue
        print(f'{k}: reading', flush=True)
        arms[k] = X.load_arm(f, a.build, keep=KEEP[k])
        arms[k]['name'] = k
        print(f'{k}: {len(arms[k]["seasons"])} seasons ({arms[k].get("state_source")})', flush=True)
    lines = ['# Arms comparison (pinned build c0d1ea5)', '']
    lines.append(f'Written {time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())} by armsan/analyze.py from the run '
                 'folders as committed at read time (read-only). Same build for every arm; seeds pinned. Partial arms '
                 'are labelled with the seasons included. No conclusions beyond the data; effects are noted, not tuned.')
    lines.append('')
    rows = []
    for k, arm in arms.items():
        man = arm.get('man') or {}
        rows.append((k, arm.get('seed', '—'), man.get('commit', '—')[:7] if man.get('commit') else '—',
                     json.dumps(arm.get('arm') or man.get('arm')), arm.get('pathway_min_age', '—'),
                     seasons_label(arm) if arm['seasons'] else arm.get('note', 'no committed season'),
                     arm.get('state_source', '—'), arm.get('archive_generation', '—')))
    lines.append(table(['arm', 'seed', 'build', 'arm recorded', 'pathway min age in force', 'seasons', 'run state read from',
                        'archive generation'], rows))
    lines.append('')
    if arms['a21old']['seasons'] and arms['a18old']['seasons']:
        section1(arms['a21old'], arms['a18old'], lines)
    else:
        lines += ['## 1. Pathway age', '', 'Not available yet (an arm has no committed season).', '']
    if arms['a18old']['seasons'] or arms['a18new']['seasons']:
        if arms['a18old']['seasons'] and arms['a18new']['seasons']:
            section2(arms['a18old'], arms['a18new'], lines)
        else:
            have = arms['a18old'] if arms['a18old']['seasons'] else arms['a18new']
            empty = {'name': 'a18new' if have is arms['a18old'] else 'a18old', 'seasons': [], 'summ': {}, 'man': {}}
            section2(have if have is arms['a18old'] else empty, have if have is arms['a18new'] else empty, lines)
    else:
        lines += ['## 2. College access', '', 'Not available yet.', '']
    two = [arms[k] for k in ('a18new', 'seed2') if arms[k]['seasons']]
    if two:
        section3(two, lines, [a for a in arms.values() if a['seasons']])
    else:
        lines += ['## 3. Two-seed bounded metrics', '', 'Not available yet (a18new and seed2 have no committed season).', '']
    section4(lines, HERE / 'story_timing.json')
    section_return([arms[k] for k in ('a21old', 'a18old', 'a18new', 'seed2')], lines)
    section_upsets(lines, HERE / 'upset_cost.json')
    lines.append('## What the runs do not record (and the workaround used)')
    lines.append('')
    lines += [
        '- The weekly access outcome of each week is not kept per week: only the last n plan weeks compatible with '
        'the recorded `weeks_blocked` are reconstructed, from the monthly plans\' recorded availability (decision '
        'evidence /2), not actual weekly access; no exact time from the first blocked week is claimed.',
        '- Starts after a pathway job: season starts include starts before the job; starts from the decision week on '
        'are counted from the editions\' weeks and finishes in the season file.',
        '- Whether the home-club floor (not the regional baseline) set a start\'s familiarity is not recorded per start; '
        'starts at a home club found by country are counted as an upper bound, and the end-state source of each '
        'golfer\'s home-club familiarity is read from the people table.',
        '- Per-week entrants who were refused by a full ordinary open field are recorded only as the golfer\'s week '
        '(`careers.denied`: first choice and what they played instead); counts above are golfer-weeks, not entries per event.',
        '- The run state (seed rows, extras) is checkpointed every season in seed_<s>.state.pkl; seed_<s>.json.gz only '
        'every 5 seasons. The report reads whichever lists more seasons, and only seasons also published in the archive.',
    ]
    lines.append('')
    lines.append(f'_Analysis time: {time.perf_counter() - t0:.0f} s._')
    text = sanitize('\n'.join(lines) + '\n')
    Path(a.out).write_text(text)
    print(f'wrote {a.out} in {time.perf_counter() - t0:.0f} s', flush=True)
    if a.publish:
        publish(Path(a.out))


def sanitize(text):
    """Machine-specific locations out of published text: paths are given relative to the v18 work folder."""
    for prefix in (str(V18) + '/', str(V18.resolve()) + '/'):
        text = text.replace(prefix, '')
    return text.replace(str(V18), '.')


def publish(report):
    """armsan/publish/: the three scripts, the report and the story timing (paths made relative); README.md is
    kept as written there. Nothing else (no caches, mirror or scratch files)."""
    import shutil
    out = HERE / 'publish'
    out.mkdir(exist_ok=True)
    for f in ('analyze.py', 'extract.py', 'stories_timing.py', 'upset_cost.py', 'g1e.py'):
        shutil.copyfile(HERE / f, out / f)
    shutil.copyfile(report, out / 'ARMS_COMPARISON.md')
    if (HERE / 'G1E_FAMILIARITY.md').exists():
        (out / 'G1E_FAMILIARITY.md').write_text(sanitize((HERE / 'G1E_FAMILIARITY.md').read_text()))
    for name in ('story_timing.json', 'upset_cost.json'):
        st = HERE / name
        if st.exists():
            (out / name).write_text(sanitize(st.read_text()))
    left = [str(p) for p in out.iterdir() if str(V18) in p.read_text(errors='ignore')]
    print(f'published to {out}' + (f'; WARNING machine paths remain in {left}' if left else ''), flush=True)


if __name__ == '__main__':
    main()
