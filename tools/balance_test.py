"""Golf Legacy engine balance test. Writes reports/BALANCE_REPORT.md.

    python tools/balance_test.py            # full run (~5 minutes on 4 cores)
    python tools/balance_test.py --quick    # smaller samples for a fast look

Sections
  1. Rating ladder: uniform golfers 10..95 on the mid course vs target scores
  2. Attribute value: what +/-15 points in each attribute is worth in strokes
  3. Archetypes: different golfer types with the SAME overall, on four courses
  4. Course difficulty: easy / mid / hard course ladder, course rating & slope
  5. Situations: caddies, familiarity, wind, pressure
  6. Upsets: 72-hole events with a realistic Premier field
"""
from __future__ import annotations

import argparse
import json
import random
import statistics as S
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import ratings as R                                              # noqa: E402
from golfsim.course import (ashford_ridge, easy_course, georgia_national, hard_course,  # noqa: E402
                            tight_classic, windy_links)
from golfsim.engine import Conditions, play_round                             # noqa: E402
from golfsim.golfer import (ARCHETYPES, OVERALL_WEIGHTS, Caddie, CADDIE_SKILLS, Golfer,  # noqa: E402
                            archetype_golfer, neutral_caddie, overall_rating, uniform_golfer)
from golfsim.stats import summarize                                           # noqa: E402
from golfsim.tournament import play_event                                     # noqa: E402

COURSES = {'easy': easy_course, 'mid': ashford_ridge, 'hard': hard_course,
           'tight': tight_classic, 'links': windy_links, 'georgia': georgia_national}
_COURSE_CACHE = {}


def course(key):
    if key not in _COURSE_CACHE:
        _COURSE_CACHE[key] = COURSES[key]()
    return _COURSE_CACHE[key]


# ---------------------------------------------------------------------------
# Worker: play N rounds with common random numbers (round i always uses seed+i)
# ---------------------------------------------------------------------------
def run_rounds(job):
    golfer, course_key, cond, caddie, round_no, pressure, n, seed = job
    c = course(course_key)
    pf = (lambda i, tp: pressure) if pressure else None
    out = []
    for i in range(n):
        rng = random.Random(seed * 1_000_003 + i)
        out.append(play_round(golfer, c, rng, cond, caddie, round_no, None, pf))
    return summarize(out)


def run_event_batch(job):
    field_spec, n_events, seed, course_key, prestige = job
    c = course(course_key)
    rng = random.Random(seed)
    wins, top10, made_cut, starts = Counter(), Counter(), Counter(), Counter()
    margins, playoffs, winning = [], 0, []
    for _ in range(n_events):
        field = [g for g in field_spec]
        board, po = play_event(field, c, rng, prestige=prestige)
        playoffs += po > 0
        for g in field:
            starts[g.name] += 1
        for pos, (g, total, _) in enumerate(board, 1):
            made_cut[g.name] += 1
            if pos <= 10:
                top10[g.name] += 1
        wins[board[0][0].name] += 1
        winning.append(board[0][1] - 4 * c.par)
    return dict(wins=wins, top10=top10, made_cut=made_cut, starts=starts,
                playoffs=playoffs, winning=winning)


def pmap(jobs, fn=run_rounds):
    with ProcessPoolExecutor() as ex:
        return list(ex.map(fn, jobs))


# ---------------------------------------------------------------------------
# Helpers for the report
# ---------------------------------------------------------------------------
def md_table(headers, rows):
    lines = ['| ' + ' | '.join(headers) + ' |', '|' + '|'.join('---' for _ in headers) + '|']
    for r in rows:
        lines.append('| ' + ' | '.join(str(x) for x in r) + ' |')
    return '\n'.join(lines)


def pct(x):
    return f'{100 * x:.0f}%'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--quick', action='store_true')
    ap.add_argument('--weights-only', action='store_true',
                    help='only measure attribute values and print suggested overall weights')
    a = ap.parse_args()
    q = a.quick
    N_LADDER = 1500 if q else 4000
    N_ATTR = 2500 if q else 8000
    N_SIT = 2000 if q else 6000
    N_EVENTS = 60 if q else 250        # per worker batch, 4 batches
    t0 = time.perf_counter()
    report = []
    data = {}
    calm = Conditions(wind_mph=6)

    # ------------------------------------------------------------ 1. ladder
    ladder = (10, 25, 40, 50, 60, 65, 71, 75, 80, 85, 90, 95)
    res = pmap([(uniform_golfer(r), 'mid', calm, None, 1, 0, N_LADDER, 11) for r in ladder])
    data['ladder'] = dict(zip(ladder, res))
    rows = []
    for r, s in zip(ladder, res):
        tgt = R.interp(R.TARGET_SCORE, r)
        rows.append((r, R.level_name(r), f'{s["scoring_avg"]:.2f}', f'{tgt:.1f}', f'{s["scoring_avg"] - tgt:+.1f}',
                     f'{s["score_sd"]:.2f}', f'{s["driving_distance"]:.0f}', pct(s['fairways_pct']), pct(s['gir_pct']),
                     pct(s['scrambling_pct']), pct(s['sand_save_pct']), f'{s["putts_per_round"]:.1f}',
                     f'{s["three_putts_per_round"]:.2f}', f'{s["birdies"] + s["eagles"]:.1f}',
                     f'{s["doubles_plus"]:.2f}', f'{s["penalties"]:.2f}'))
    rows.append(('—', '**Real PGA Tour average (reference)**', '~71.0–72.0*', '', '', '~2.8', '~299', '~60%',
                 '~65%', '~58%', '~50%', '~29.0', '~0.5', '~3.8', '~0.3', '~0.2–0.3'))
    report.append('## 1. Rating ladder — every attribute at the same rating, mid course\n')
    report.append('Each row is a golfer with all 21 attributes at that rating, playing '
                  f'{N_LADDER:,} rounds at Ashford Ridge in calm conditions.\n')
    report.append(md_table(['Rating', 'Level', 'Avg', 'Target', 'Diff', 'SD', 'Drive', 'Fairways', 'Greens',
                            'Scrambling', 'Sand saves', 'Putts', '3-putts', 'Birdies+', 'Doubles+', 'Penalties'], rows))
    report.append('\n\\*Real tour courses average slightly easier than Ashford Ridge, which is '
                  'set up as a mid-difficulty championship test.\n')

    # ------------------------------------------------------------ 2. attribute value
    base = uniform_golfer(75)
    jobs, keys = [], []
    for ctx, rnd, press in (('normal', 1, 0), ('sunday', 4, 0.8)):
        jobs.append((base, 'mid', calm, None, rnd, press, N_ATTR, 23))
        keys.append((ctx, 'base', 0))
        for k in R.ATTRIBUTE_KEYS:
            for d in (+15, -15):
                g = replace(base, attrs={**base.attrs, k: 75 + d}, name=f'{k}{d}')
                jobs.append((g, 'mid', calm, None, rnd, press, N_ATTR, 23))
                keys.append((ctx, k, d))
    res = pmap(jobs)
    av = {key: s['scoring_avg'] for key, s in zip(keys, res)}
    sg = {key: s for key, s in zip(keys, res)}
    data['attribute_value'] = {f'{c}|{k}|{d}': v for (c, k, d), v in av.items()}
    rows, measured = [], {}
    for k in R.ATTRIBUTE_KEYS:
        up = av[('normal', 'base', 0)] - av[('normal', k, 15)]
        down = av[('normal', k, -15)] - av[('normal', 'base', 0)]
        up_s = av[('sunday', 'base', 0)] - av[('sunday', k, 15)]
        down_s = av[('sunday', k, -15)] - av[('sunday', 'base', 0)]
        per_point = ((up + down) / 30 * 0.75 + (up_s + down_s) / 30 * 0.25)
        measured[k] = max(0.0, per_point)
        rows.append((R.ATTRIBUTE_LABELS[k], R.ATTRIBUTE_GROUPS[k], f'{up:+.2f}', f'{down:+.2f}',
                     f'{up_s:+.2f}', f'{down_s:+.2f}'))
    total_w = sum(measured.values())
    suggested = {k: round(v / total_w, 3) for k, v in measured.items()}
    data['measured_weights'] = suggested
    report.append('## 2. What each attribute is worth\n')
    report.append(f'Start from an all-75 golfer (Premier Tour average). Raise ONE attribute to 90, or lower it '
                  f'to 60, and measure the change in average score ({N_ATTR:,} rounds each, same random '
                  'shots for every version so only the attribute differs). Positive = strokes saved per round '
                  'by +15, or strokes lost by −15. "Sunday" = final round, in contention, high pressure.\n')
    report.append(md_table(['Attribute', 'Group', '+15 normal', '−15 normal', '+15 Sunday', '−15 Sunday'], rows))
    group_tot = defaultdict(float)
    for k, v in measured.items():
        group_tot[R.ATTRIBUTE_GROUPS[k]] += v * 30
    report.append('\nTotal value of a 30-point swing across each group (sum of its attributes): ' +
                  ', '.join(f'{g} {v:.2f}' for g, v in sorted(group_tot.items(), key=lambda x: -x[1])) + ' strokes.\n')
    report.append('Measured weight of each attribute in the OVERALL rating (share of total stroke value):\n')
    report.append(md_table(['Attribute', 'Current weight', 'Measured weight'],
                           [(R.ATTRIBUTE_LABELS[k], f'{OVERALL_WEIGHTS[k]:.3f}', f'{suggested[k]:.3f}')
                            for k in R.ATTRIBUTE_KEYS]))

    if a.weights_only:
        print(json.dumps(suggested, indent=1))
        return

    # ------------------------------------------------------------ 3. archetypes
    windy = Conditions(wind_mph=22)
    arch_rows, jobs, keys = [], [], []
    for ov in (75, 85):
        for name in ARCHETYPES:
            g = archetype_golfer(name, ov)
            for ck, cond in (('easy', calm), ('mid', calm), ('hard', calm), ('tight', calm), ('links', windy),
                             ('georgia', calm)):
                jobs.append((g, ck, cond, None, 1, 0, N_SIT, 31))
                keys.append((ov, name, ck))
    res = pmap(jobs)
    arch = {k: s for k, s in zip(keys, res)}
    data['archetypes'] = {f'{o}|{n}|{c}': s['scoring_avg'] for (o, n, c), s in arch.items()}
    report.append('## 3. Golfer types with the same overall rating\n')
    report.append('Each archetype is built so its OVERALL rating is exactly the same. On the balanced mid '
                  'course they should score similarly; on other courses their strengths should show.\n')
    for ov in (75, 85):
        rows = []
        for name in ARCHETYPES:
            s_mid = arch[(ov, name, 'mid')]
            rows.append((name, f'{arch[(ov, name, "easy")]["scoring_avg"]:.2f}', f'{s_mid["scoring_avg"]:.2f}',
                         f'{arch[(ov, name, "hard")]["scoring_avg"]:.2f}', f'{arch[(ov, name, "tight")]["scoring_avg"]:.2f}',
                         f'{arch[(ov, name, "links")]["scoring_avg"]:.2f}', f'{arch[(ov, name, "georgia")]["scoring_avg"]:.2f}',
                         f'{s_mid["driving_distance"]:.0f}', pct(s_mid['fairways_pct']), pct(s_mid['gir_pct']),
                         pct(s_mid['scrambling_pct']), f'{s_mid["putts_per_round"]:.1f}',
                         f'{s_mid["sg_ott"]:+.2f} / {s_mid["sg_app"]:+.2f} / {s_mid["sg_arg"]:+.2f} / {s_mid["sg_putt"]:+.2f}'))
        report.append(f'\n**Overall {ov}**\n')
        # Best archetype on each course, relative to the all-rounder.
        report.append(md_table(['Archetype', 'Easy', 'Mid', 'Hard', 'Tight classic', 'Links, 22 mph', 'Georgia National', 'Drive', 'Fairways', 'Greens',
                                'Scrambling', 'Putts', 'Strokes gained (drive / approach / short game / putt), mid'], rows))

    # ------------------------------------------------------------ 4. course difficulty
    levels = (10, 25, 40, 60, 75, 90)
    jobs, keys = [], []
    for ck in ('easy', 'mid', 'hard', 'georgia'):
        for r in levels + (4,):
            jobs.append((uniform_golfer(r), ck, calm, None, 1, 0, N_SIT, 41))
            keys.append((ck, r))
    res = pmap(jobs)
    cd = {k: s for k, s in zip(keys, res)}
    data['course_difficulty'] = {f'{c}|{r}': s['scoring_avg'] for (c, r), s in cd.items()}
    rows = []
    for ck in ('easy', 'mid', 'hard', 'georgia'):
        c = course(ck)
        scratch = cd[(ck, 40)]['scoring_avg']
        bogey = cd[(ck, 4)]['scoring_avg']
        slope = (bogey - scratch) * 5.381
        rows.append((c.name, f'{c.yards:,}', c.par, *[f'{cd[(ck, r)]["scoring_avg"]:.1f}' for r in levels],
                     f'{scratch:.1f}', f'{slope:.0f}'))
    report.append('## 4. Course difficulty: easy, mid, hard and Georgia National\n')
    report.append('Same golfers, three courses. Difficulty is not a flat penalty: it punishes weak players far '
                  'more than strong ones. "Scratch score" = expected score of a scratch-level amateur (rating 40); '
                  '"slope" uses the real USGA formula (bogey golfer, rating 4, vs scratch): 113 is standard, '
                  'real courses run 55-155.\n')
    report.append(md_table(['Course', 'Yards', 'Par'] + [f'Rating {r}' for r in levels] + ['Scratch score', 'Slope'], rows))
    gap = {ck: cd[(ck, 10)]['scoring_avg'] - cd[(ck, 90)]['scoring_avg'] for ck in ('easy', 'mid', 'hard', 'georgia')}
    report.append(f'\nGap between a rating-10 amateur and a rating-90 star: easy {gap["easy"]:.1f}, '
                  f'mid {gap["mid"]:.1f}, hard {gap["hard"]:.1f}, Georgia National {gap["georgia"]:.1f} strokes per round.\n')

    # ------------------------------------------------------------ 5. situations
    report.append('## 5. Caddies, familiarity, wind and pressure\n')
    g75 = uniform_golfer(75)
    jobs, keys = [], []
    def caddie(**sk):
        return Caddie('c', {k: float(sk.get(k, 50)) for k in CADDIE_SKILLS})
    caddies = {'Poor (all 25)': caddie(**{k: 25 for k in CADDIE_SKILLS}),
               'Average (all 50)': neutral_caddie(),
               'Elite (all 90)': caddie(**{k: 90 for k in CADDIE_SKILLS}),
               'Green reader (reading 95)': caddie(green_reading=95, communication=70),
               'Strategist (strategy 95)': caddie(strategy=95, communication=70),
               'Motivator (mental 95)': caddie(mental_support=95, communication=70)}
    for cname, cad in caddies.items():
        for ck in ('mid', 'hard'):
            for press in (0, 0.8):
                jobs.append((g75, ck, calm, cad, 4 if press else 1, press, N_SIT, 51))
                keys.append(('caddie', cname, ck, press))
    for rounds_played in (0, 3, 10, 25, 60):
        g = replace(g75, familiarity={'Ashford Ridge Golf Club': rounds_played})
        jobs.append((g, 'mid', calm, None, 1, 0, N_SIT, 52))
        keys.append(('fam', rounds_played))
    for bfc in (40, 75, 95):
        g = replace(g75, attrs={**g75.attrs, 'ball_flight': bfc})
        for wind in (5, 15, 25):
            jobs.append((g, 'mid', Conditions(wind_mph=wind), None, 1, 0, N_SIT, 53))
            keys.append(('wind', bfc, wind))
    for comp in (40, 75, 95):
        g = replace(g75, attrs={**g75.attrs, 'composure': comp})
        for press in (0, 0.5, 1.0):
            jobs.append((g, 'mid', calm, None, 4, press, N_SIT, 54))
            keys.append(('press', comp, press))
    res = dict(zip(keys, pmap(jobs)))
    base_c = {(ck, p): res[('caddie', 'Average (all 50)', ck, p)]['scoring_avg'] for ck in ('mid', 'hard') for p in (0, 0.8)}
    rows = [(cname, *[f'{base_c[(ck, p)] - res[("caddie", cname, ck, p)]["scoring_avg"]:+.2f}'
                      for ck in ('mid', 'hard') for p in (0, 0.8)]) for cname in caddies]
    report.append('**Caddies** — strokes saved per round vs an average caddie (all-75 golfer):\n')
    report.append(md_table(['Caddie', 'Mid course', 'Mid, Sunday pressure', 'Hard course', 'Hard, Sunday pressure'], rows))
    f0 = res[('fam', 0)]['scoring_avg']
    report.append('\n**Course familiarity** — strokes saved vs a first visit: ' +
                  ', '.join(f'{n} rounds {f0 - res[("fam", n)]["scoring_avg"]:+.2f}' for n in (3, 10, 25, 60)) + '\n')
    rows = [(f'Ball-flight {b}', *[f'{res[("wind", b, w)]["scoring_avg"]:.2f}' for w in (5, 15, 25)]) for b in (40, 75, 95)]
    report.append('**Wind** — average score by wind speed (all-75 golfer, ball-flight control varied):\n')
    report.append(md_table(['Golfer', '5 mph', '15 mph', '25 mph'], rows))
    rows = [(f'Composure {c}', *[f'{res[("press", c, p)]["scoring_avg"] - res[("press", c, 0)]["scoring_avg"]:+.2f}'
                                 for p in (0.5, 1.0)]) for c in (40, 75, 95)]
    report.append('\n**Pressure** — extra strokes over 18 holes played under pressure (0.5 = in contention, '
                  '1.0 = leading a major on Sunday). Pressure always costs something; composure limits the damage.\n')
    report.append(md_table(['Golfer', 'Moderate pressure', 'Maximum pressure'], rows))
    data['situations'] = {'|'.join(map(str, k)): v['scoring_avg'] for k, v in res.items()}

    # ------------------------------------------------------------ 6. upsets
    rng = random.Random(77)
    field = []
    names = list(ARCHETYPES)
    bands = [(88, 2), (84, 4), (80, 14), (77, 30), (74, 44), (71, 30), (67, 20)]
    idx = 0
    for ov, count in bands:
        for _ in range(count):
            arch_name = names[idx % len(names)]
            o = ov + rng.uniform(-1.5, 1.5)
            g = archetype_golfer(arch_name, round(o, 1), name=f'P{idx:03d}')
            g.personality['big_stage'] = rng.uniform(20, 80)
            field.append(g)
            idx += 1
    batches = pmap([(field, N_EVENTS, 900 + b, 'mid', 1.0) for b in range(4)], run_event_batch)
    wins, top10, cuts, starts = Counter(), Counter(), Counter(), Counter()
    winning, playoffs = [], 0
    for b in batches:
        wins.update(b['wins']); top10.update(b['top10']); cuts.update(b['made_cut']); starts.update(b['starts'])
        winning += b['winning']; playoffs += b['playoffs']
    events = 4 * N_EVENTS
    by_name = {g.name: g for g in field}
    band_rows = []
    for lo, hi in ((86, 100), (82, 86), (78, 82), (75, 78), (72, 75), (69, 72), (60, 69)):
        members = [g for g in field if lo <= g.overall < hi]
        if not members:
            continue
        w = sum(wins[g.name] for g in members)
        t = sum(top10[g.name] for g in members)
        c = sum(cuts[g.name] for g in members)
        st = sum(starts[g.name] for g in members)
        band_rows.append((f'{lo}–{hi if hi < 100 else "+"}', len(members), pct(w / events),
                          f'{100 * w / st:.2f}%', f'{100 * t / st:.1f}%', pct(c / st)))
    best = max(field, key=lambda g: g.overall)
    low_winners = sum(wins[g.name] for g in field if g.overall < 72)
    distinct = len([n for n in wins if wins[n]])
    report.append('## 6. Upsets — can a 71 win a major?\n')
    report.append(f'{events} major-style 72-hole events (cut top 65 and ties, Friday cut-line pressure, Sunday '
                  f'contention pressure) with a fixed {len(field)}-player field shaped like a Premier Tour major: '
                  'a couple of stars around 88, a deep middle, and a tail of 66–72 players. Every golfer gets '
                  'fresh week form and daily form each event.\n')
    report.append(md_table(['Overall band', 'Golfers', 'Share of all wins', 'Win % per start', 'Top-10 % per start',
                            'Made cut'], band_rows))
    report.append(f'\n- Best player in the field (overall {best.overall:.1f}, {best.archetype}) won '
                  f'{wins[best.name]} of {events} ({100 * wins[best.name] / events:.1f}%).')
    report.append(f'- Golfers rated under 72 won {low_winners} of {events} events '
                  f'({100 * low_winners / events:.1f}%).')
    report.append(f'- {distinct} different winners; average winning score {S.mean(winning):+.1f}; '
                  f'{playoffs} playoffs ({100 * playoffs / events:.0f}%).')
    data['upsets'] = dict(events=events, band_rows=band_rows, best=wins[best.name],
                          low_winners=low_winners, distinct=distinct, winning_avg=S.mean(winning))

    # ------------------------------------------------------------ write
    elapsed = time.perf_counter() - t0
    header = ['# Golf Legacy — Engine Balance Report', '',
              f'Generated by `tools/balance_test.py`{" --quick" if q else ""} in {elapsed / 60:.1f} minutes. '
              'Fully reproducible: same code + same seeds = same numbers.', '']
    out = ROOT / 'reports'
    out.mkdir(exist_ok=True)
    (out / 'BALANCE_REPORT.md').write_text('\n'.join(header + report) + '\n', encoding='utf8')
    (out / 'balance_results.json').write_text(json.dumps(data, indent=1, default=str), encoding='utf8')
    print('\n'.join(header + report))


if __name__ == '__main__':
    main()
