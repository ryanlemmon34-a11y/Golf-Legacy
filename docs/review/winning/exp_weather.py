"""Component 4 (controlled): the same real field, course and golfer state; only the shared round conditions vary.

Usage: python exp_weather.py CAPDIR SAVE OUT --events E1,E2 --scen 12 --reps 40 [--procs 3]

Design:
  - Events: verified captured tasks (harness: both no-op checks pass first).
  - Scenarios s = 1..S: draw_conditions for the course and week with an independent weather seed gives each round
    a direction and gustiness (and the archived pin difficulty). Each scenario is then played at fixed wind
    speeds for every round:
      - calm 0 mph: seasonal model kept, so wind_from stays set (never the classic default Conditions());
      - 10, 20 and 28 mph;
    each dry and wet.
  - Shot seeds (s, r) are common to all arms (paired).
  - Disclosed: gusts are seeded from the conditions (weather.gust_seed), so each wind level has its own gust
    realisation. Calm air has no gusts and no per-hole wind terms. The shared shot stream diverges as soon as
    conditions change any outcome. "Same winner as calm" is therefore compared with a re-randomisation floor:
    calm (s, r) against calm (s, r+1), with the same conditions and an independent shot seed.

Measures per event and arm:
  - field: the finishers' mean score per round (common penalty), the SD of totals, the winning margin and
    playoffs;
  - winner: the winner's Overall rank, the best entrant's win rate, and the share of wins taken by the top 5 by
    Overall;
  - the win distribution's total-variation distance from calm, against the calm-half versus calm-half floor;
  - relative advantage: each golfer's mean finishing percentile (missed cut = the bottom), arm minus calm,
    related to their attributes (correlations), Overall and native archetype.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402
import exp_attrs as X  # noqa: E402
import harness as H  # noqa: E402
from golfsim.ratings import ATTRIBUTE_KEYS  # noqa: E402

ARMS = [(w, wet) for wet in (False, True) for w in (0, 10, 20, 28)]
RESEED = 'calm_reseeded'          # calm again with independent shot seeds: the re-randomisation floor


def arm_name(w, wet):
    return f'{w}mph{"_wet" if wet else ""}'


def job(args):
    name, s, r0, r1 = args
    t = X.task(name)
    base = H.conditions(t, seed=f'{t["seed"]}:wxscen:{s}')
    out = []
    for r in range(r0, r1):
        for w, wet in ARMS:
            cond = {k: c for k, c in H.scenario_conditions(t, w, wet).items()}
            for k in cond:                                  # this scenario's directions and gustiness
                cond[k].wind_from = base[k].wind_from
                cond[k].gust = base[k].gust
            for arm, seed in ((arm_name(w, wet), f'{t["seed"]}:wxrep:{s}:{r}'),) + (
                    ((RESEED, f'{t["seed"]}:wxrep2:{s}:{r}'),) if (w, wet) == (0, False) else ()):
                board, playoff, _ = H.play(t, seed=seed, cond=cond)
                fin = H.finish_of(board, t['golfers'])
                out.append((s, r, arm, playoff, [(x[0], x[1] or 0, x[2] if x[2] is not None else -1) for x in fin]))
    return name, out


def analyse(name, runs, t, arch):
    golfers = {g.id: g for g in t['golfers']}
    n = len(golfers)
    order = sorted(golfers.values(), key=lambda g: (-g.overall, g.id))
    ovr_rank = {}
    for i, g in enumerate(order):
        ovr_rank[g.id] = 1 + sum(1 for h in order if h.overall > g.overall)
    best = [g.id for g in order if g.overall == order[0].overall]
    top5 = {g.id for g in order[:5]}
    R = t['rounds']
    by = defaultdict(dict)
    for s, r, arm, playoff, fin in runs:
        by[arm][(s, r)] = (playoff, fin)
    rows = []
    calm = by['0mph']
    pct = {}
    for arm, d in by.items():
        winners, wr, sdv, mean_rd, margins, playoffs, same = [], [], [], [], [], [], []
        P = defaultdict(list)
        for key, (playoff, fin) in d.items():
            w = fin[0][0]
            winners.append(w)
            wr.append(ovr_rank[w])
            tots = [x[2] for x in fin if x[1] >= 1 and x[2] > 0]
            sdv.append(np.std(tots))
            mean_rd.append(np.mean(tots) / R - t['course'].par)
            others = sorted(x[2] for x in fin[1:] if x[1] >= 1 and x[2] > 0)
            margins.append(others[0] - fin[0][2] if others else np.nan)
            playoffs.append(playoff > 0)
            same.append(calm[key][1][0][0] == w)
            for gid, pos, tot in fin:
                P[gid].append((pos if pos >= 1 else n) / n)
        pct[arm] = {gid: float(np.mean(v)) for gid, v in P.items()}
        c = Counter(winners)
        rows.append({'event': name, 'arm': arm, 'runs': len(d), 'best_entrant_win': float(np.mean([w in best for w in winners])),
                     'top5_overall_win_share': float(np.mean([w in top5 for w in winners])),
                     'winner_overall_rank_median': float(np.median(wr)), 'winner_overall_rank_mean': float(np.mean(wr)),
                     'distinct_winners': len(c), 'field_mean_to_par_per_round': float(np.mean(mean_rd)),
                     'field_sd_total': float(np.mean(sdv)), 'margin': float(np.nanmean(margins)),
                     'playoff_rate': float(np.mean(playoffs)), 'same_winner_as_calm': float(np.mean(same)),
                     'win_counts': dict(c.most_common(10))})
    # win-distribution distance from calm vs a calm-half floor
    def dist(a, b):
        ca, cb = Counter(a), Counter(b)
        keys = set(ca) | set(cb)
        return 0.5 * sum(abs(ca[k] / len(a) - cb[k] / len(b)) for k in keys)
    calm_w = [v[1][0][0] for k, v in sorted(calm.items())]
    floor_tv = dist([v[1][0][0] for k, v in sorted(by[RESEED].items())], calm_w)
    floor_same = next(r_['same_winner_as_calm'] for r_ in rows if r_['arm'] == RESEED)
    for row in rows:
        aw = [v[1][0][0] for k, v in sorted(by[row['arm']].items())]
        row['tv_distance_win_distribution_vs_calm'] = dist(aw, calm_w)
        row['tv_floor_calm_vs_calm_reseeded'] = floor_tv
        row['same_winner_floor_calm_vs_calm_reseeded'] = floor_same
    # relative advantage: percentile change against calm, related to golfer attributes
    adv = []
    base = pct['0mph']
    for arm in pct:
        if arm in ('0mph', RESEED):
            continue
        d = pd.DataFrame({'gid': list(base)})
        d['delta_pct'] = [pct[arm][g] - base[g] for g in d.gid]
        d['overall'] = [golfers[g].overall for g in d.gid]
        for k in ATTRIBUTE_KEYS:
            d[k] = [golfers[g].attrs[k] for g in d.gid]
        d['aggression'] = [golfers[g].personality['aggression'] for g in d.gid]
        d['archetype'] = d.gid.map(arch)
        rec = {'event': name, 'arm': arm, 'corr_overall': float(d.delta_pct.corr(d.overall))}
        for k in list(ATTRIBUTE_KEYS) + ['aggression']:
            rec[f'corr_{k}'] = float(d.delta_pct.corr(d[k]))
        for a_, g_ in d.groupby('archetype'):
            rec[f'arch_{a_}'] = float(g_.delta_pct.mean())
        adv.append(rec)
    return rows, adv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cap')
    ap.add_argument('save')
    ap.add_argument('out')
    ap.add_argument('--events', required=True)
    ap.add_argument('--scen', type=int, default=12)
    ap.add_argument('--reps', type=int, default=40)
    ap.add_argument('--chunk', type=int, default=10)
    ap.add_argument('--procs', type=int, default=3)
    ap.add_argument('--data', default='/dev/shm/aw/data')
    a = ap.parse_args()
    X.CAP = a.cap
    names = [e if e.endswith('.pkl') else f'{e}_s0.pkl' for e in a.events.split(',')]
    years = C.year_files(a.save)
    for n in names:
        t = H.load_task(a.cap, n)
        arch_ev = {e['id']: e for e in C.load_year(years[int(n[:4])])['events']}
        H.noop_check(t, arch_ev[t['event_id']])
    archetypes = pd.read_csv(Path(a.data) / 'archetypes.csv.gz').set_index('gid').archetype.to_dict()
    jobs = [(n, s, r0, min(a.reps, r0 + a.chunk)) for n in names for s in range(1, a.scen + 1)
            for r0 in range(0, a.reps, a.chunk)]
    t0 = time.time()
    runs = defaultdict(list)
    with Pool(a.procs) as pool:
        for n, out in pool.imap_unordered(job, jobs, chunksize=1):
            runs[n].extend(out)
    rows, adv = [], []
    for n in names:
        r_, a_ = analyse(n, runs[n], H.load_task(a.cap, n), archetypes)
        rows += r_
        adv += a_
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / 'weather_cf.json').write_text(json.dumps({
        'design': __doc__, 'events': names, 'scenarios': a.scen, 'reps': a.reps, 'arms': [arm_name(*x) for x in ARMS],
        'seconds': round(time.time() - t0), 'rows': rows, 'advantage': adv,
        'provenance': C.provenance([Path(a.cap) / 'MANIFEST.json'] + [Path(a.cap) / 'tasks' / n for n in names]
                                   + [Path(a.data) / 'archetypes.csv.gz'])}, indent=1, default=float))
    pd.DataFrame([{k: v for k, v in r.items() if k != 'win_counts'} for r in rows]).to_csv(
        Path(a.out) / 'weather_cf.csv', index=False, float_format='%.4f')
    pd.DataFrame(adv).to_csv(Path(a.out) / 'weather_cf_advantage.csv', index=False, float_format='%.4f')
    print(f'{len(rows)} rows in {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
