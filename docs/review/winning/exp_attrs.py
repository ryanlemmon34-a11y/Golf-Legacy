"""Attribute experiments on verified captured events (production engine, main 18a8e23; scoring code identical to
the save's c0d1ea5). Research only: no engine code is changed; only deep copies of a task are perturbed.

Usage:
  python exp_attrs.py rounds  CAPDIR SAVE OUT --events E1,E2 --ranks 1,10,40 --n 20000 [--deltas 5] [--procs 3]
  python exp_attrs.py events  CAPDIR SAVE OUT --events E1 --ranks 1 --n 2000 --arms base,power+5,... [--procs 3]

Tier 1, 'rounds' (exact production round path, one golfer).
  Each sample i draws:
    - the event's seasonal conditions for that course and week from a sample seed (as play_site would for a
      new seed: weather.draw_conditions);
    - the golfer's week form;
    - one production play_round with the golfer's own captured caddie, familiarity and season fatigue.
  Contexts:
    - R1: round 1, no pressure;
    - R4: round 4, no pressure (in-week fatigue: stamina and recovery act);
    - R4P: round 4 under final-round contention pressure (play_event's 0.5/0.95 x prestige).
  Every arm uses the same sample seeds (common random numbers). Draws are conditional on outcomes, so an arm's
  path diverges from the baseline at the first decision or shot the change affects. Reported: the paired mean
  difference and its SE; SD and tails (shares beating the baseline's 10th percentile and missing its 90th) as
  distribution comparisons.

Tier 3, 'events' (full production event, the whole field, paired seeds).
  harness.play on the perturbed task with seed s, for s in 1..n. Conditions are drawn from s as in production,
  so the weather varies across replicates as it would for this course and week. Reported for the subject:
    - win, top-5, top-10, made cut, total and position;
  and for the field: the share of other golfers whose total changed (stream divergence).

Tier 2 ('fixed-field', conditional approximation) lives in exp_fixed.py and is validated against tier 3.

Both sanity checks run through the same code:
  - injury_resistance has no shot effect, so its arm must be identical sample for sample;
  - a long_irons change inside the flat 25-60 band must also be identical.
"""
from __future__ import annotations

import argparse
import copy
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
import harness as H  # noqa: E402
from golfsim.engine import WeekForm, play_round  # noqa: E402
from golfsim.ratings import ATTRIBUTE_KEYS  # noqa: E402
from golfsim.tournament import _pressure_fn  # noqa: E402

CAP = None
_TASKS = {}


def task(name):
    if name not in _TASKS:
        _TASKS[name] = H.load_task(CAP, name)
    return _TASKS[name]


def subject_ids(t, ranks):
    order = sorted(t['golfers'], key=lambda g: (-g.overall, g.id))
    return {r: order[r - 1].id for r in ranks}


def arm_task(t, gid, arm):
    """arm: 'base', '<attr><+|-><d>', '<attr>=<v>' (set: for the flat-band check), 'arch:<Archetype>' (the
    subject's 21 attributes replaced by that native archetype's profile at exactly the subject's Overall, with the
    archetype's aggression/big_stage) or 'arch:<Archetype>:neutral' (the same attributes, aggression and big_stage
    50), or 'arch:Uniform' (every attribute equal to the Overall). Everything else about the subject (id, caddie,
    familiarity, fatigue, other traits) is unchanged. Clipped = any profile attribute at the 1/99 bound."""
    if arm == 'base':
        return t, False
    if arm.startswith('arch:'):
        from golfsim.golfer import ARCHETYPES, archetype_golfer, uniform_golfer
        parts = arm.split(':')
        t2 = copy.deepcopy(t)
        g = next(g for g in t2['golfers'] if g.id == gid)
        ov = g.overall
        prof = uniform_golfer(ov) if parts[1] == 'Uniform' else archetype_golfer(parts[1], ov)
        g.attrs = dict(prof.attrs)
        traits = {} if parts[1] == 'Uniform' else ARCHETYPES[parts[1]][1]
        for k in ('aggression', 'big_stage'):
            g.personality[k] = 50.0 if (len(parts) > 2 or parts[1] == 'Uniform') else float(traits.get(k, 50.0))
        assert abs(g.overall - ov) < 1e-6, (arm, g.overall, ov)
        return t2, any(v in (1.0, 99.0) for v in g.attrs.values())
    if '=' in arm:
        k, v = arm.split('=')
        t2 = copy.deepcopy(t)
        g = next(g for g in t2['golfers'] if g.id == gid)
        g.attrs[k] = float(v)
        return t2, False
    for sign in ('+', '-'):
        if sign in arm:
            k, d = arm.split(sign)
            return H.perturbed(t, gid, k, float(d) * (1 if sign == '+' else -1))
    raise ValueError(arm)


# ---- tier 1 ---------------------------------------------------------------------------------------------------
def rounds_job(args):
    name, gid, arm, i0, i1 = args
    t = task(name)
    ta, clipped = arm_task(t, gid, arm)
    g = next(x for x in ta['golfers'] if x.id == gid)
    cad = dict(zip([x.id for x in ta['golfers']], ta.get('caddies') or ())).get(gid)
    p = ta['prestige'] / 100
    out = {'R1': [], 'R4': [], 'R4P': []}
    for i in range(i0, i1):
        cond = H.conditions(ta, seed=f'{ta["seed"]}:wx:{i}')
        for ctx in out:
            rng = random.Random(f'A:{name}:{ctx}:{i}')
            wf = WeekForm.draw(rng, g)
            rd = 1 if ctx == 'R1' else 4
            pf = _pressure_fn(0.5 * p, 0.95 * p) if ctx == 'R4P' else None
            st = play_round(g, ta['course'], rng, cond[min(rd, len(cond))], cad, rd, wf, pf, None)
            out[ctx].append(st.score)
    return name, gid, arm, i0, clipped, {k: np.array(v, np.int16) for k, v in out.items()}


def summarise_rounds(res):
    """res: {(name, gid, arm): {ctx: scores}} -> rows with paired differences against 'base'."""
    rows = []
    for (name, gid, arm), d in sorted(res.items()):
        base = res.get((name, gid, 'base'))
        for ctx, s in d.items():
            b = base[ctx]
            diff = s.astype(float) - b
            q10, q90 = np.percentile(b, 10), np.percentile(b, 90)
            rows.append({'event': name, 'gid': gid, 'arm': arm, 'context': ctx, 'n': len(s),
                         'mean': float(s.mean()), 'sd': float(s.std(ddof=1)), 'd_mean': float(diff.mean()),
                         'd_se': float(diff.std(ddof=1) / np.sqrt(len(diff))),
                         'identical_share': float((diff == 0).mean()),
                         'sd_ratio': float(s.std(ddof=1) / b.std(ddof=1)),
                         'beat_base_p10': float((s < q10).mean()), 'base_beat_p10': float((b < q10).mean()),
                         'over_base_p90': float((s > q90).mean()), 'base_over_p90': float((b > q90).mean())})
    return rows


# ---- tier 3 ---------------------------------------------------------------------------------------------------
def events_job(args):
    name, gid, arm, s0, s1 = args
    t = task(name)
    ta, clipped = arm_task(t, gid, arm)
    out = []
    for s in range(s0, s1):
        board, playoff, _ = H.play(ta, seed=f'{ta["seed"]}:rep:{s}')
        fin = H.finish_of(board, ta['golfers'])
        pos = {x[0]: x[1] for x in fin}
        tot = {x[0]: x[2] for x in fin}
        out.append((s, pos[gid] or 0, tot[gid] if tot[gid] is not None else -1, playoff,
                    tuple(sorted((k, v if v is not None else -1) for k, v in tot.items()))))
    return name, gid, arm, s0, clipped, out


def summarise_events(res):
    rows = []
    for (name, gid, arm), reps in sorted(res.items()):
        base = {r[0]: r for r in res.get((name, gid, 'base'), [])}
        pos = np.array([r[1] for r in reps])
        win, top5, top10, cut = (pos == 1), (pos >= 1) & (pos <= 5), (pos >= 1) & (pos <= 10), pos >= 1
        b = [base.get(r[0]) for r in reps]
        paired = [x for x in zip(reps, b) if x[1] is not None]
        bw = np.array([(p[1][1] == 1) for p in paired], float)
        aw = np.array([(p[0][1] == 1) for p in paired], float)
        dw = aw - bw
        ft = []
        for a_, b_ in paired:
            other_a = {k: v for k, v in a_[4] if k != gid}
            other_b = {k: v for k, v in b_[4] if k != gid}
            ft.append(np.mean([other_a[k] != other_b[k] for k in other_b]))
        made = np.array([r[2] for r in reps if r[1] >= 1], float)
        rows.append({'event': name, 'gid': gid, 'arm': arm, 'n': len(reps), 'win': float(win.mean()),
                     'top5': float(top5.mean()), 'top10': float(top10.mean()), 'made_cut': float(cut.mean()),
                     'd_win': float(dw.mean()) if len(dw) else np.nan,
                     'd_win_se': float(dw.std(ddof=1) / np.sqrt(len(dw))) if len(dw) > 1 else np.nan,
                     'mean_total_made_cut': float(made.mean()) if len(made) else np.nan,
                     'field_changed_share': float(np.mean(ft)) if ft else np.nan})
    return rows


def main():
    global CAP
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['rounds', 'events'])
    ap.add_argument('cap')
    ap.add_argument('save')
    ap.add_argument('out')
    ap.add_argument('--events', required=True)
    ap.add_argument('--ranks', default='1,10,40')
    ap.add_argument('--n', type=int, default=2000)
    ap.add_argument('--deltas', default='5')
    ap.add_argument('--arms', default='')
    ap.add_argument('--chunk', type=int, default=500)
    ap.add_argument('--procs', type=int, default=3)
    ap.add_argument('--tag', default='')
    a = ap.parse_args()
    CAP = a.cap
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    names = [e if e.endswith('.pkl') else f'{e}_s0.pkl' for e in a.events.split(',')]
    ranks = [int(r) for r in a.ranks.split(',')]
    # no-op checks before anything is measured
    years = C.year_files(a.save)
    for n in names:
        t = H.load_task(a.cap, n)
        arch = {e['id']: e for e in C.load_year(years[int(n[:4])])['events']}
        H.noop_check(t, arch[t['event_id']])
    if a.arms:
        arms = a.arms.split(',')
    else:
        arms = ['base'] + [f'{k}+{d}' for d in a.deltas.split(',') for k in ATTRIBUTE_KEYS]
    jobs = []
    meta = {}
    for n in names:
        t = H.load_task(a.cap, n)
        for r, gid in subject_ids(t, ranks).items():
            g = next(x for x in t['golfers'] if x.id == gid)
            meta[f'{n}:{gid}'] = {'rank': r, 'overall': round(g.overall, 2), 'attrs': g.attrs,
                                  'personality': g.personality, 'fatigue': g.fatigue,
                                  'archetype_note': 'see archetypes.csv.gz for the native label'}
            for arm in arms:
                for i0 in range(0, a.n, a.chunk):
                    jobs.append((n, gid, arm, i0, min(a.n, i0 + a.chunk)))
    t0 = time.time()
    fn = rounds_job if a.mode == 'rounds' else events_job
    res, clip = {}, {}
    with Pool(a.procs) as pool:
        for name, gid, arm, i0, clipped, data in pool.imap_unordered(fn, jobs, chunksize=1):
            key = (name, gid, arm)
            clip[key] = clipped
            if a.mode == 'rounds':
                cur = res.setdefault(key, {})
                for ctx, v in data.items():
                    cur.setdefault(ctx, {})[i0] = v
            else:
                res.setdefault(key, {})[i0] = data
    if a.mode == 'rounds':
        res = {k: {ctx: np.concatenate([v[i] for i in sorted(v)]) for ctx, v in d.items()} for k, d in res.items()}
        rows = summarise_rounds(res)
    else:
        res = {k: [r for i in sorted(d) for r in d[i]] for k, d in res.items()}
        rows = summarise_events(res)
    for r in rows:
        r['clipped'] = clip[(r['event'], r['gid'], r['arm'])]
        r['rank'] = meta[f'{r["event"]}:{r["gid"]}']['rank']
    tag = a.tag or a.mode
    (out / f'{tag}.json').write_text(json.dumps({
        'mode': a.mode, 'n': a.n, 'events': names, 'ranks': ranks, 'arms': arms, 'seconds': round(time.time() - t0),
        'subjects': meta, 'rows': rows,
        'provenance': C.provenance([Path(a.cap) / 'MANIFEST.json'] + [Path(a.cap) / 'tasks' / n for n in names],
                                   {'engine_checkout': str(C.ROOT)})}, indent=1, default=float))
    print(f'{len(rows)} rows in {time.time() - t0:.0f}s -> {out / (tag + ".json")}')


if __name__ == '__main__':
    main()
