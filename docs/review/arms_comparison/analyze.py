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
KEEP = {'a21old': {'plans', 'careers', 'transitions', 'work_pathway', 'oo', 'open_starts', 't5_starts'},
        'a18old': {'plans', 'careers', 'transitions', 'work_pathway', 'oo', 'open_starts', 't5_starts'},
        'a18new': {'careers', 'transitions', 'work_pathway', 'oo', 'open_starts', 't5_starts', 'prestige', 'weather',
                   'all_starts', 'familiar_base', 'home_floor_starts'},
        'seed2': {'careers', 'prestige', 'weather', 'all_starts', 'familiar_base', 'home_floor_starts'}}
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
    """Walk back from the decision week over the recorded weekly availability, as work_pathway.count does: 'unaff'
    counts, 'none'/'inelig'/injured pause, anything else resets. Returns (weeks from the first counted week of the
    run to the job, reconstructed count, recorded count, weeks without a recorded plan inside the run)."""
    g, y, wk, n = rec['gid'], rec['year'], rec['week'], rec['weeks_blocked']
    j = (y - first) * 52 + wk
    t = tl.get(g, {})
    found, firstw, unknown = 0, None, 0
    a = j - 1
    lo = (arm['seasons'][0] - first) * 52 + 1
    while a >= lo and found < n:
        v = t.get(a)
        if v is None:
            unknown += 1
        else:
            av, inj = v
            if inj or av in ('none', 'inelig'):
                pass
            elif av == 'unaff':
                found += 1
                firstw = a
            else:
                break
        a -= 1
    return (j - firstw if firstw is not None else None), found, n, unknown


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


def original_cohort(a21, a18, lines):
    common = [y for y in a21['seasons'] if y in a18['seasons']]
    if len(common) < 2:
        lines += ['### ORIGINAL COHORT (fixed membership)', '', 'Needs two committed seasons in both arms.', '']
        return
    y0 = common[1]
    ROW = row_fields()
    r21, r18 = a21['data']['rows'][y0], a18['data']['rows'][y0]
    diff = sorted(g for g in set(r21) & set(r18) if list(r21[g]) != list(r18[g]))
    c21 = a21['summ'][y0]['careers']
    ids, excluded = [], Counter()
    for g, row in r21.items():
        d = dict(zip(ROW, row))
        p = a21['people'].get(g) or {}
        if d['status'] != 'amateur' or not p.get('born'):
            continue
        age = y0 - p['born']
        if not 17 <= age <= 20:
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
    seasons = [y for y in common if y >= y0]
    N, last = len(ids), seasons[-1]
    lines.append('### ORIGINAL COHORT (fixed membership: the same people in both arms)')
    lines.append('')
    lines.append(f'Membership is fixed before the arms diverge and never changes, so the two columns describe the same '
                 f'people and the denominator is the cohort size in both arms. Definition: golfers with a {y0} season row '
                 f'in both arms, the same person in both (id, name, birth year, country), and in {y0} an amateur on a '
                 f'non-college tour, full-time, aged 17–20 ({y0} minus birth year). The {y0} rows are identical in the '
                 f'two arms except for {len(diff)} golfer(s) ({", ".join(map(str, diff))}); status and lifestyle are taken '
                 f'from the a21old row, where no pathway entry below 21 can change a 17–20-year-old\'s lifestyle during '
                 f'the season (in a18old golfer 5217 is part-time by the end of {y0}, having taken work in week 45; '
                 f'their full-time status at the start of {y0} is the same in both arms). Amateurs aged 17–20 left '
                 f'out: ' + (', '.join(f'{k} {v}' for k, v in excluded.items()) or 'none') + '.')
    lines.append('')
    lines.append(f'N = {N} (by age in {y0}: ' + ', '.join(f'{a}: {n}' for a, n in sorted(Counter(
        y0 - a21['people'][g]['born'] for g in ids).items())) + f'). Outcomes over seasons {seasons[0]}–{last}.')
    lines.append('')
    out = {'a21old': cohort_outcomes(a21, ids, seasons), 'a18old': cohort_outcomes(a18, ids, seasons)}
    lines.append(cohort_table(out, N, last))
    lines.append('')
    lines.append(f'Status "{last}" is the golfer\'s {last} season row before that winter\'s decisions; a golfer with no '
                 'active row is classified by the exit recorded in an earlier winter (retired, became coach or caddie) '
                 'or a recorded death. Starts and zero-start seasons count every season the golfer had an active row, '
                 'whatever their status that season.')
    lines.append('')
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
    lines.append('### Time from the first counted blocked week to the job (denominator: each arm\'s entries)')
    lines.append('')
    lines.append('Reconstructed from the monthly plans\' recorded weekly availability (decision evidence /2, '
                 '`schedule`: "unaff" counts, "none"/"inelig"/injured pause, anything else resets), walking back from '
                 'the decision week until the recorded `weeks_blocked` is reached; "agrees" = the walk found exactly '
                 'the recorded count before a reset. Weeks are calendar weeks (the winter between seasons adds none).')
    lines.append('')
    rows = []
    for arm in (a21, a18):
        tl, first = weeks_timeline(arm)
        by = defaultdict(list)
        agree = defaultdict(Counter)
        for y in arm['seasons']:
            for r in arm['summ'][y]['work_pathway']:
                span, found, n, unknown = time_to_job(arm, tl, first, r)
                b = band(r['age'])
                agree[b]['n'] += 1
                agree[b]['ok'] += found == n
                agree[b]['unknown'] += unknown > 0
                if span is not None and found == n:
                    by[b].append(span)
                by[b + ' recorded count'].append(n)
        for b in ('18-20', '21+'):
            if agree[b]['n']:
                rows.append((arm['name'], b, agree[b]['n'], frac(agree[b]['ok'], agree[b]['n']),
                             dist(by[b]), dist(by[b + ' recorded count'])))
    lines.append(table(['arm', 'age band', 'entries', 'walk agrees', 'weeks first counted → job (min/q1/med/q3/max)',
                        'recorded weeks_blocked'], rows))
    lines.append('')
    # what happened after
    lines.append('### After the job (denominator: each arm\'s pathway entries; the entrants differ between arms)')
    lines.append('')
    lines.append('Event-based groups: who enters depends on the arm, so these are arm-level descriptions, not a '
                 'comparison of the same people. For each entry in season Y: starts in Y and in Y+1 (season file `careers`), Overall change over Y+1 '
                 '(ratings as each season ends), and the first career transition from the winter after Y on '
                 '(within the committed seasons). Entries in the last committed season have no Y+1 yet.')
    lines.append('')
    rows, outs = [], {}
    for arm in (a21, a18):
        for b in ('18-20', '21+'):
            st0, st1, dev, oc = [], [], [], Counter()
            n = 0
            for y in arm['seasons']:
                for r in arm['summ'][y]['work_pathway']:
                    if band(r['age']) != b:
                        continue
                    n += 1
                    a0, a1, d, o = follow(arm, r['gid'], y)
                    st0.append(a0)
                    if (y + 1) in arm['summ']:
                        st1.append(a1)
                        dev.append(d)
                    oc[outcome_kind(o)] += 1
            if n:
                rows.append((arm['name'], b, n, dist(st0), dist(st1), dist(dev, 2)))
                outs[(arm['name'], b)] = (n, oc)
    lines.append(table(['arm', 'band', 'entries', 'starts in Y', 'starts in Y+1', 'Overall change over Y+1'], rows))
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
    lines.append('### ORIGINAL COHORT (fixed membership: the same people in both arms)')
    lines.append('')
    common = [y for y in old['seasons'] if y in new['seasons']]
    if not common:
        lines += ['Needs a committed season in both arms.', '']
        return
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
    lines.append(f'These two arms differ from week 1 of {y0} (the setting acts from the first week), so no later '
                 f'season is shared; membership is fixed by the {y0} season record, whose tour (a college tour or an '
                 f'amateur series) and residence were assigned when the world was created, before any week was played. '
                 f'Kept: amateurs whose {y0} tour and residence are the same in both arms and who are the same person '
                 f'(id, name, birth year, country); {mismatch} differ and are left out. College players are placed by '
                 f'their {y0} residence, members by their series. Outcomes are cumulative over the seasons both arms '
                 f'have committed ({common[0]}–{common[-1]}); status at the end of {common[-1]} as in section 1. '
                 'Denominator: the fixed group\'s size, the same people in both arms.')
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

    rows = []
    for kind in ('college', 'members'):
        for key in sorted(groups[kind]):
            ids = groups[kind][key]
            N = len(ids)
            oo, so = outcomes(old, ids)
            on, sn = outcomes(new, ids)
            f = lambda o: f'{per(o["open"], N, 1)} / {per(o["t5"], N, 1)} / {per(o["shut"], N, 1)} ({per(o["alt"], N, 1)})'
            top = lambda st: ', '.join(f'{k} {frac(v, N, 0)}' for k, v in st.most_common(3))
            rows.append((kind, key.replace('AM_', ''), N, f(oo), f(on), top(so), top(sn)))
    lines.append(table(['group', 'series region', 'N (fixed)',
                        'a18old: open / tier-5 starts / open shut-out weeks (alt) per member of N',
                        'a18new: same', f'a18old status end {common[-1]} (top 3)', f'a18new status end {common[-1]} (top 3)'],
                       rows))
    lines.append('')


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
            elif c['tour'] in OAR:
                os_ = s['open_starts'].get(g, {})
                for k in (c['tour'], 'ALL'):
                    st[k]['mem'] += 1
                    st[k]['mem_open'] += sum(os_.values())
                    st[k]['mem_open_home'] += os_.get(c['tour'], 0)
                    st[k]['mem_shut'] += c.get('oo_shut', 0)
                    st[k]['mem_alt'] += c.get('oo_alt', 0)
                    st[k]['mem_zero'] += c['events'] == 0
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

    college_cohort(old, new, lines, defs, reg2series)
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
def section3(arms, lines):
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


# ---- section 4: story timing -------------------------------------------------------------------------------------
def section4(lines, timing_path):
    lines.append('## 4. Story timing on the pinned long archive (run A, 45 seasons, build 473690a)')
    lines.append('')
    if not timing_path.exists():
        lines.append('Not measured yet (run `analyze.py --stories`).')
        lines.append('')
        return
    t = json.loads(timing_path.read_text())
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
    a = ap.parse_args()
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
        section3(two, lines)
    else:
        lines += ['## 3. Two-seed bounded metrics', '', 'Not available yet (a18new and seed2 have no committed season).', '']
    section4(lines, HERE / 'story_timing.json')
    lines.append('## What the runs do not record (and the workaround used)')
    lines.append('')
    lines += [
        '- The weekly access outcome of each week is not kept per week; the time from the first counted blocked week '
        'to the job is reconstructed from the monthly plans\' recorded weekly availability (decision evidence /2), '
        'checked against the recorded `weeks_blocked` ("walk agrees").',
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
    for f in ('analyze.py', 'extract.py', 'stories_timing.py'):
        shutil.copyfile(HERE / f, out / f)
    shutil.copyfile(report, out / 'ARMS_COMPARISON.md')
    st = HERE / 'story_timing.json'
    if st.exists():
        (out / 'story_timing.json').write_text(sanitize(st.read_text()))
    left = [str(p) for p in out.iterdir() if str(V18) in p.read_text(errors='ignore')]
    print(f'published to {out}' + (f'; WARNING machine paths remain in {left}' if left else ''), flush=True)


if __name__ == '__main__':
    main()
