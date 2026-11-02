"""Realism pass 1 (docs/review/realism/PLAN.md): paired measurements of the development rules, 'dev-1' against
'dev-2' (golfsim/realism.py), on the same generated junior classes.

Layer 1, cohorts (exact): for each seed and year the production junior_class and new_professionals under both
rules: counts, identities (id, name, nation, potential, peak age, aging rate, path), entry Overall, youth headroom.
Layer 2, projections (controlled): every junior with potential >= 60, and a fixed 20% sample of the rest, developed
from 18 to 50 with the production develop_week / age_year on one fixed schedule (13 blocks a year: one four-round
event, two training weeks in the category choose_category picks, one rest week; self-coached; no injuries, money,
access limits or retirement). Arms: A0 = dev-1; R = readiness only; G = aging only; B = dev-2 (both). These are
controlled projections, not realized careers.

Usage: python measure.py OUT.json [--seeds 11,2027,386509,7,99] [--years 2028-2037] [--procs 4]
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from golfsim import development as D                     # noqa: E402
from golfsim import population as P                      # noqa: E402
from golfsim import realism as RZ                        # noqa: E402
from golfsim.nations import nations as starting_nations  # noqa: E402

ARMS = {'A0': (RZ.LEGACY, RZ.LEGACY), 'R': (RZ.CURRENT, RZ.LEGACY), 'G': (RZ.LEGACY, RZ.CURRENT),
        'B': (RZ.CURRENT, RZ.CURRENT)}          # arm: (readiness rules, aging rules)
AGES = (18, 19, 20, 21, 22, 23, 25, 27, 30, 33, 35, 38, 40, 42, 45, 48, 50)
TO_AGE = 50


def cohort(seed, year, rules, kind='juniors'):
    profiles = starting_nations()
    start = (abs(hash((seed, year, kind))) % 1000) * 10 ** 6 if False else 1   # ids as a fresh class would get
    fn = P.junior_class if kind == 'juniors' else P.new_professionals
    return fn(year, seed, profiles, start, set(), rules=rules)


def ident(g):
    return (g.id, g.name, g.country, g.born, g.potential, g.peak_age, g.aging_rate, g.archetype, g.tour, g.status,
            tuple(sorted(g.personality.items())))


def project(g, aging_rules, key):
    """Overall by age from 18 to TO_AGE under the fixed schedule (one four-round event, two training weeks, one
    rest week, 13 times a year)."""
    rng = random.Random(f'{key}:develop')
    exp = D.experience_factor(4 * 13)
    out = {18: g.overall}
    for age in range(18, TO_AGE):
        for _ in range(13):
            cat = D.choose_category(g, rng)
            D.develop_week(g, 'play', age, None, 4.0, gain=False)
            D.develop_week(g, 'train', age, cat, 0.0, coach=0.3, experience=exp, gain=False)
            D.develop_week(g, 'train', age, cat, 0.0, coach=0.3, experience=exp, gain=False)
            D.develop_week(g, 'rest', age, gain=False)
        D.age_year(g, age + 1, rng, exp, rules=aging_rules)
        out[age + 1] = g.overall
    return out


def _work(args):
    seed, year = args
    rows = {}
    built = {}
    for rules in (RZ.LEGACY, RZ.CURRENT):
        js = cohort(seed, year, rules)
        rng = random.Random(f'{seed}:juniors:{year}')            # as careers.add_juniors
        for g in js:
            D.init_ceilings(g, 18, rng)
            rng.random(); rng.random(); rng.random()            # (cash and backing draws, as add_juniors)
        built[rules] = js
        nps = cohort(seed, year, rules, 'new_pros')
        rows[rules] = {'juniors': [ident(g) for g in js], 'new_pros': [ident(g) for g in nps],
                       'entry': [round(g.overall, 3) for g in js], 'np_entry': [round(g.overall, 3) for g in nps]}
    import copy
    leg, cur = built[RZ.LEGACY], built[RZ.CURRENT]
    proj = []
    pick = random.Random(f'realism-sample:{seed}:{year}')
    for g0, g1 in zip(leg, cur):
        if g0.potential < 60 and pick.random() >= 0.2:
            continue
        rec = {'id': g0.id, 'pot': g0.potential, 'peak': g0.peak_age, 'aging': g0.aging_rate,
               'w': 1.0 if g0.potential >= 60 else 5.0}
        for arm, (ready, aging) in ARMS.items():
            g = copy.deepcopy(g1 if ready == RZ.CURRENT else g0)
            traj = project(g, aging, f'{seed}:{year}:{g0.id}')
            rec[arm] = [round(traj[a], 2) for a in range(18, TO_AGE + 1)]
        proj.append(rec)
    return {'seed': seed, 'year': year, 'rows': rows, 'proj': proj}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--seeds', default='11,2027,386509,7,99')
    ap.add_argument('--years', default='2028-2035')
    ap.add_argument('--procs', type=int, default=4)
    a = ap.parse_args()
    seeds = [int(x) for x in a.seeds.split(',')]
    y0, y1 = (int(x) for x in a.years.split('-'))
    tasks = [(s, y) for s in seeds for y in range(y0, y1 + 1)]
    t = time.time()
    with Pool(a.procs) as pool:
        res = pool.map(_work, tasks, chunksize=1)
    json.dump({'seeds': seeds, 'years': [y0, y1], 'to_age': TO_AGE, 'results': res,
               'seconds': round(time.time() - t, 1)}, open(a.out, 'w'))
    print('done', len(res), 'cohorts', round(time.time() - t), 's')


if __name__ == '__main__':
    main()
