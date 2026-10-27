"""World population report: writes reports/WORLD_POPULATION_REPORT.md.

    python tools/world_report.py [--seed 2027] [--seeds 20] [--validate 200]

Generates the starting world, compares it with the real world ranking and checks (by simulating
rounds) that generated golfers score like their overall rating says they should.
"""
from __future__ import annotations

import argparse
import random
import statistics as S
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import ratings as R                                        # noqa: E402
from golfsim.calendar import TOUR_BY_KEY                                # noqa: E402
from golfsim.course import ashford_ridge                                # noqa: E402
from golfsim.engine import play_round                                   # noqa: E402
from golfsim.golfer import ARCHETYPES                                   # noqa: E402
from golfsim.nations import REAL_TOP200, STYLES, nations                # noqa: E402
from golfsim.population import candidates, generate_world, level_of     # noqa: E402
from golfsim.ratings import ATTRIBUTE_KEYS                              # noqa: E402

LEVELS = ('Premier Tour', 'Challenger', 'Regional', 'Mini tour', 'College', 'Amateur', 'Club professional')
_W = {}


def _score(args):
    seed, gid, rounds = args
    if seed not in _W:
        _W[seed] = generate_world(seed=seed)
    g = _W[seed].by_id[gid]
    rng = random.Random(gid)
    course = ashford_ridge()
    return gid, S.mean(play_round(g, course, rng).score for _ in range(rounds))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=2027)
    ap.add_argument('--seeds', type=int, default=20, help='worlds averaged for the nation comparison')
    ap.add_argument('--validate', type=int, default=200, help='golfers simulated for the scoring check')
    a = ap.parse_args()
    t0 = time.perf_counter()
    w = generate_world(seed=a.seed)
    t_gen = time.perf_counter() - t0
    year = w.year
    gs = w.golfers
    pros = w.ranked(w.pros())
    out = ['# Golf Legacy — World Population', '',
           f'Starting world for {year} (seed {a.seed}): **{len(gs):,} competitive golfers** from '
           f'{len({g.country for g in gs})} countries, generated in {t_gen:.1f} s. Every golfer has a name, nationality, '
           'hometown, age, height, handedness, archetype, all 21 attributes, personality, status and tour membership, '
           'plus a hidden potential and prime age for the development system.', '']

    # ---- levels ------------------------------------------------------------------------------------
    out += ['## Levels', '', '| Level | Golfers | Average overall | Range | Average age | Rating scale says |',
            '|---|---|---|---|---|---|']
    for lv in LEVELS:
        xs = [g for g in gs if level_of(g) == lv]
        ov = [g.overall for g in xs]
        mid = R.level_name(S.median(ov))
        out.append(f'| {lv} | {len(xs):,} | {S.mean(ov):.1f} | {min(ov):.0f}–{max(ov):.0f} | '
                   f'{S.mean(g.age(year) for g in xs):.1f} | median golfer: {mid} |')
    out.append(f'\nProfessionals: {len(pros):,}. World ranking by overall: No.1 {pros[0].overall:.1f}, No.10 '
               f'{pros[9].overall:.1f}, No.50 {pros[49].overall:.1f}, No.100 {pros[99].overall:.1f}, No.200 '
               f'{pros[199].overall:.1f}, No.300 {pros[299].overall:.1f}, No.1000 {pros[999].overall:.1f}.')

    # ---- world top 25 -------------------------------------------------------------------------------
    out += ['', '## World top 25 (by overall)', '',
            '| # | Golfer | Country | Age | Overall | Potential | Archetype | Tour | Height | Hand |',
            '|---|---|---|---|---|---|---|---|---|---|']
    for i, g in enumerate(pros[:25], 1):
        out.append(f'| {i} | {g.name} | {g.country} | {g.age(year)} | {g.overall:.1f} | {g.potential:.1f} | '
                   f'{g.archetype} | {TOUR_BY_KEY[g.tour].name} | {g.height_cm} cm | {g.hand} |')

    # ---- nations vs the real world -----------------------------------------------------------------
    tot = Counter()
    eras = []
    for s in range(a.seeds):
        c = candidates(year, a.seed + 1000 + s, nations())
        ps = [r for r in c if r[5] == 'pro']
        tot.update(r[0] for r in ps[:200])
        eras.append((ps[0][4], ps[1][4], ps[9][4], sum(1 for r in ps if r[4] >= 90)))
    out += ['', '## Eras: nothing caps the best players', '',
            f'The best players in {a.seeds} other generated worlds. Talent is drawn naturally from each nation\'s pool, '
            'with no ceiling, so some worlds start in a weak era and some in a golden one.', '',
            f'- World No.1: from **{min(e[0] for e in eras):.1f}** to **{max(e[0] for e in eras):.1f}** '
            f'(median {S.median(e[0] for e in eras):.1f}); this world: {pros[0].overall:.1f}.',
            f'- World No.2: {min(e[1] for e in eras):.1f} to {max(e[1] for e in eras):.1f}; No.10: '
            f'{min(e[2] for e in eras):.1f} to {max(e[2] for e in eras):.1f}.',
            f'- Players rated 90 or more: from {min(e[3] for e in eras)} to {max(e[3] for e in eras)} '
            f'(median {S.median(e[3] for e in eras):.0f}).']
    this = Counter(g.country for g in pros[:200])
    out += ['', '## Nations: world top 200 compared with the real world', '',
            f'Average over {a.seeds} generated worlds, this world, and the approximate real world top 200 (mid-2020s).', '',
            '| Country | Pool | Development | Pathway | Style | Golfers | Pros | Premier | Top 200 (avg) | This world | Real | Best player |',
            '|---|---|---|---|---|---|---|---|---|---|---|---|']
    by_c = defaultdict(list)
    for g in gs:
        by_c[g.country].append(g)
    rows = sorted(w.nations.values(), key=lambda p: -(tot[p.country] + REAL_TOP200.get(p.country, 0)))
    for p in rows:
        cg = by_c.get(p.country, [])
        best = max(cg, key=lambda g: g.overall) if cg else None
        out.append(f'| {p.country} | {p.pool:g} | {p.development:g} | {p.pathway:g} | {p.style} | {len(cg)} | '
                   f'{sum(g.status == "pro" for g in cg)} | {sum(level_of(g) == "Premier Tour" for g in cg)} | '
                   f'{tot[p.country] / a.seeds:.1f} | {this[p.country]} | {REAL_TOP200.get(p.country, 0)} | '
                   + (f'{best.name} ({best.overall:.0f})' if best else '—') + ' |')

    # ---- tours ------------------------------------------------------------------------------------
    out += ['', '## Tour memberships', '', '| Tour | Level | Members | Average overall | Best | Main nationalities |',
            '|---|---|---|---|---|---|']
    members = defaultdict(list)
    for g in gs:
        if g.tour:
            members[g.tour].append(g)
    for key, t in TOUR_BY_KEY.items():
        m = members.get(key, [])
        if not m:
            continue
        nat = Counter(g.country for g in m).most_common(3)
        out.append(f'| {t.name} | {level_of(m[0])} | {len(m)} | {S.mean(g.overall for g in m):.1f} | '
                   f'{max(g.overall for g in m):.0f} | {", ".join(f"{c} {n}" for c, n in nat)} |')
    d1 = members.get('CO_US_D1', [])
    out.append(f'\nUS Division I college golf: {len(d1)} players, {sum(g.country != "USA" for g in d1)} of them from outside '
               'the USA (the college pathway: Sweden, England, Canada, Australia, Spain...). '
               f'Club professionals: {sum(g.status == "club_pro" for g in gs)}, '
               f'{sum(g.status == "club_pro" and g.country == "USA" for g in gs)} in the USA.')

    # ---- styles -----------------------------------------------------------------------------------
    out += ['', '## National styles', '',
            'Attributes relative to each golfer\'s own overall (average of attribute − overall), by national style. '
            'Shows the tendencies each style creates.', '',
            '| Style | Golfers | Power | Driving acc. | Irons (mid) | Wedges | Ball flight | Chipping | Bunker | Short putting | Most common archetypes |',
            '|---|---|---|---|---|---|---|---|---|---|---|']
    by_s = defaultdict(list)
    for g in gs:
        by_s[w.nations[g.country].style].append(g)
    for style in STYLES:
        xs = by_s.get(style, [])
        if not xs:
            continue
        def rel(k):
            return f'{S.mean(g.attrs[k] - g.overall for g in xs):+.1f}'
        arch = Counter(g.archetype for g in xs).most_common(2)
        out.append(f'| {style} | {len(xs)} | {rel("power")} | {rel("driving_accuracy")} | {rel("mid_irons")} | '
                   f'{rel("wedges")} | {rel("ball_flight")} | {rel("chipping")} | {rel("bunker")} | {rel("short_putting")} | '
                   f'{", ".join(f"{k} {n / len(xs):.0%}" for k, n in arch)} |')

    # ---- age ---------------------------------------------------------------------------------------
    out += ['', '## Age and the physical / mental balance', '',
            '| Age | Pros | Average overall | Power − overall | Stamina − overall | Composure − overall | Management − overall |',
            '|---|---|---|---|---|---|---|']
    for lo, hi in ((18, 22), (23, 26), (27, 30), (31, 35), (36, 40), (41, 45), (46, 55)):
        xs = [g for g in pros if lo <= g.age(year) <= hi]
        if not xs:
            continue
        def rel(k):
            return f'{S.mean(g.attrs[k] - g.overall for g in xs):+.1f}'
        out.append(f'| {lo}–{hi} | {len(xs)} | {S.mean(g.overall for g in xs):.1f} | {rel("power")} | {rel("stamina")} | '
                   f'{rel("composure")} | {rel("management")} |')

    # ---- scoring validation ------------------------------------------------------------------------
    if a.validate:
        rng = random.Random(1)
        sample = rng.sample(gs, min(a.validate, len(gs)))
        t1 = time.perf_counter()
        with ProcessPoolExecutor() as ex:
            res = dict(ex.map(_score, [(a.seed, g.id, 200) for g in sample], chunksize=4))
        diffs = [(res[g.id] - R.interp(R.TARGET_SCORE, g.overall), g) for g in sample]
        out += ['', '## Do generated golfers score like their rating?', '',
                f'{len(sample)} random golfers, 200 rounds each at Ashford Ridge ({time.perf_counter() - t1:.0f} s). '
                'Difference = their average score − the target score for their overall rating. For reference, uniform '
                'golfers (every attribute equal) run +1.6 at 25, +1.0 at 40, +0.6 at 60 and +0.1 at 75 on this course '
                '(see the balance report), so the same pattern here means the generated profiles are sound.', '',
                '| Overall | Golfers | Average difference | Spread (sd) |', '|---|---|---|---|']
        for lo, hi in ((20, 40), (40, 55), (55, 70), (70, 100)):
            xs = [d for d, g in diffs if lo <= g.overall < hi]
            if xs:
                out.append(f'| {lo}–{hi} | {len(xs)} | {S.mean(xs):+.2f} | {S.pstdev(xs):.2f} |')
        by_a = defaultdict(list)
        for d, g in diffs:
            by_a[g.archetype].append(d)
        out.append('\nBy archetype: ' + ', '.join(f'{k} {S.mean(v):+.2f} ({len(v)})' for k, v in sorted(by_a.items())) + '.')

    text = '\n'.join(out) + '\n'
    (ROOT / 'reports').mkdir(exist_ok=True)
    (ROOT / 'reports' / 'WORLD_POPULATION_REPORT.md').write_text(text, encoding='utf8')
    print(text[:4000])
    print(f'... {time.perf_counter() - t0:.0f} s')


if __name__ == '__main__':
    main()
