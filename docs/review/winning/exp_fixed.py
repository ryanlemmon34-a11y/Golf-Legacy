"""Tier 2: subject against FIXED field results, a CONDITIONAL APPROXIMATION of winning impact. It is validated
against full production events (exp_attrs.py events) before any ranking.

Usage: python exp_fixed.py CAPDIR SAVE OUT --event E --ranks 1,10 --reps 600 --k 20 [--deltas 5,-5 | --arms ...]

1. Field replicates (production). For seed s = 1..reps the whole event is played by harness.play: the
   production play_event, with conditions drawn from s as play_site would. Every golfer's round scores, the
   round pin sheets (recorded by wrapping tournament.pin_sheet, which changes no draw) and the conditions are
   kept. The subject plays at baseline in these replicates.
2. Subject re-simulation. For each replicate and k = 1..K (common seeds across arms), the subject's own week is
   replayed with the production round code (WeekForm.draw, then play_round per round with the round's real
   conditions and pin sheet, the subject's caddie and fatigue). The pressure and cut follow play_event's rules,
   computed from the subject's running total against the replicate's fixed field totals.
3. Outcomes against the fixed field:
   - a win: lower than every other finisher; a tie for first counts as 1/(number tied), an equal-chance playoff
     that is NOT simulated;
   - position (competition ranking), top 5 and top 10;
   - the cut: the subject's 36-hole total against the cut line recomputed with the subject included.

What is frozen, so this is not complete tournament causality:
  - the other golfers' scores, including their pressure and cut responses to the subject's position (in
    production a leading subject changes rivals' pressure);
  - which rivals made the cut (from the production run);
  - playoffs, which are not simulated.
Validation (report): the baseline arm's win/top-10/cut rates and a few arms' differences are compared with full
production paired events of the same subject and event, and the difference is bounded before any ranking uses
these numbers.

SE: over field replicates (each replicate's K-sample mean difference against the baseline arm), i.e. within this
world and these events.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402
import exp_attrs as X  # noqa: E402
import harness as H  # noqa: E402
from golfsim import tournament as TM  # noqa: E402
from golfsim.engine import WeekForm, play_round  # noqa: E402
from golfsim.ratings import ATTRIBUTE_KEYS  # noqa: E402

FIELDS = {}


def field_job(args):
    name, s = args
    t = X.task(name)
    pins = []
    orig = TM.pin_sheet

    def rec(course, cond, rng):
        p = orig(course, cond, rng)
        pins.append(p)
        return p
    rounds = {}

    def on_round(g, rd, st):
        rounds.setdefault(g.id, []).append(st.score)
    TM.pin_sheet = rec
    try:
        board, playoff, cond = H.play(t, seed=f'{t["seed"]}:rep:{s}', on_round=on_round)
    finally:
        TM.pin_sheet = orig
    return name, s, {'rounds': rounds, 'pins': pins[:t['rounds']], 'cond': cond,
                     'winner': board[0][0].id, 'playoff': playoff}


def subject_week(t, g, cad, f, rng, cut_after):
    """One replay of the subject's week against fixed field replicate f. Returns (win share, position or 0,
    made cut, total or -1)."""
    R = t['rounds']
    p = t['prestige'] / 100
    cut_top = t['cut_top'] or len(t['golfers'])
    others = {gid: sc for gid, sc in f['rounds'].items() if gid != g.id}
    wf = WeekForm.draw(rng, g)
    tot, alive = 0, True
    for rd in range(1, R + 1):
        before = [sum(sc[:rd - 1]) for sc in others.values() if len(sc) >= rd]
        board = sorted(before + [tot])
        leader = board[0]
        cut_est = board[min(cut_top, len(board)) - 1]
        final = rd == R
        pf = None
        if rd == 2 and cut_after == 2 and R > 2:
            if abs(tot - cut_est) <= 2:
                pf = TM._pressure_fn(0.15, 0.45 * p)
        elif rd == 3 and not final and tot - leader <= 3:
            pf = TM._pressure_fn(0.25 * p, 0.35 * p)
        elif final and rd > 1:
            gap = tot - leader
            if gap <= 3:
                pf = TM._pressure_fn(0.5 * p, 0.95 * p)
            elif gap <= 6:
                pf = TM._pressure_fn(0.2 * p, 0.4 * p)
        st = play_round(g, t['course'], rng, f['cond'][rd], cad, rd, wf, pf, f['pins'][rd - 1])
        tot += st.score
        if cut_after and rd == cut_after and rd < R:
            totals = sorted([sum(sc[:rd]) for sc in others.values() if len(sc) >= rd] + [tot])
            line = totals[min(cut_top, len(totals)) - 1]
            if tot > line:
                alive = False
                break
    if not alive:
        return 0.0, 0, 0, -1
    fin = [sum(sc) for sc in others.values() if len(sc) == R]
    best = min(fin) if fin else 10 ** 6
    if tot < best:
        win = 1.0
    elif tot == best:
        win = 1.0 / (1 + sum(1 for x in fin if x == best))
    else:
        win = 0.0
    pos = 1 + sum(1 for x in fin if x < tot)
    return win, pos, 1, tot


def subject_job(args):
    name, gid, arm, reps, K = args
    t = X.task(name)
    ta, clipped = X.arm_task(t, gid, arm)
    g = next(x for x in ta['golfers'] if x.id == gid)
    cad = dict(zip([x.id for x in ta['golfers']], ta.get('caddies') or ())).get(gid)
    cut_after = 2 if ta['cut_top'] and ta['rounds'] > 2 else None
    out = np.zeros((len(reps), K, 4))
    for i, s in enumerate(reps):
        f = FIELDS[(name, s)]
        for k in range(K):
            rng = random.Random(f'F:{name}:{gid}:{s}:{k}')
            out[i, k] = subject_week(ta, g, cad, f, rng, cut_after)
    return name, gid, arm, clipped, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cap')
    ap.add_argument('save')
    ap.add_argument('out')
    ap.add_argument('--event', required=True)
    ap.add_argument('--ranks', default='1,10')
    ap.add_argument('--reps', type=int, default=600)
    ap.add_argument('--k', type=int, default=20)
    ap.add_argument('--deltas', default='5,-5')
    ap.add_argument('--arms', default='')
    ap.add_argument('--procs', type=int, default=3)
    ap.add_argument('--tag', default='')
    a = ap.parse_args()
    X.CAP = a.cap
    name = a.event if a.event.endswith('.pkl') else f'{a.event}_s0.pkl'
    t = H.load_task(a.cap, name)
    arch = {e['id']: e for e in C.load_year(C.year_files(a.save)[int(name[:4])])['events']}
    H.noop_check(t, arch[t['event_id']])
    t0 = time.time()
    reps = list(range(1, a.reps + 1))
    with Pool(a.procs) as pool:
        for n, s, f in pool.imap_unordered(field_job, [(name, s) for s in reps], chunksize=10):
            FIELDS[(n, s)] = f
    t_field = time.time() - t0
    arms = a.arms.split(',') if a.arms else ['base'] + [f'{k}{"+" if not d.startswith("-") else ""}{d}'
                                                        for d in a.deltas.split(',') for k in ATTRIBUTE_KEYS]
    subj = X.subject_ids(t, [int(r) for r in a.ranks.split(',')])
    jobs = [(name, gid, arm, reps, a.k) for gid in subj.values() for arm in arms]
    res, clip = {}, {}
    with Pool(a.procs) as pool:                       # forked after FIELDS is filled: the workers inherit it
        for n, gid, arm, clipped, data in pool.imap_unordered(subject_job, jobs, chunksize=1):
            res[(gid, arm)] = data
            clip[(gid, arm)] = clipped
    rows = []
    for (gid, arm), d in sorted(res.items()):
        b = res[(gid, 'base')]
        per = d.mean(axis=1)                         # per replicate: means over K
        pb = b.mean(axis=1)
        row = {'gid': gid, 'rank': next(r for r, x in subj.items() if x == gid), 'arm': arm, 'clipped': clip[(gid, arm)],
               'reps': len(reps), 'k': a.k}
        for j, m in enumerate(['win', 'pos', 'made_cut', 'total']):
            if m in ('pos', 'total'):
                continue
            row[m] = float(per[:, j].mean())
            diff = per[:, j] - pb[:, j]
            row[f'd_{m}'] = float(diff.mean())
            row[f'd_{m}_se'] = float(diff.std(ddof=1) / np.sqrt(len(diff)))
        top10 = ((d[:, :, 1] >= 1) & (d[:, :, 1] <= 10)).mean(axis=1)
        top10b = ((b[:, :, 1] >= 1) & (b[:, :, 1] <= 10)).mean(axis=1)
        row['top10'] = float(top10.mean())
        row['d_top10'] = float((top10 - top10b).mean())
        row['d_top10_se'] = float((top10 - top10b).std(ddof=1) / np.sqrt(len(reps)))
        made = d[:, :, 3][d[:, :, 2] == 1]
        row['mean_total_made_cut'] = float(made.mean()) if made.size else np.nan
        rows.append(row)
    tag = a.tag or f'fixed_{name[:-4]}'
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / f'{tag}.json').write_text(json.dumps({
        'design': 'subject vs fixed production field replicates (conditional approximation)', 'event': name,
        'reps': a.reps, 'k': a.k, 'arms': arms, 'subjects': subj, 'seconds_fields': round(t_field),
        'seconds': round(time.time() - t0), 'rows': rows,
        'production_field_winner_rates': {str(gid): float(np.mean([FIELDS[(name, s)]['winner'] == gid for s in reps]))
                                          for gid in subj.values()},
        'provenance': C.provenance([Path(a.cap) / 'MANIFEST.json', Path(a.cap) / 'tasks' / name])},
        indent=1, default=float))
    print(f'{len(rows)} rows, fields {t_field:.0f}s, total {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
