"""Round-to-round volatility in the archive (descriptive), majors and Premier editions (primary).

Usage: python volatility.py SAVE DATA_DIR OUT

Residual = a golfer's round score minus that round's field mean, taken over everyone who played the round
(course-round adjustment). Three variants per golfer-season:
  A. season: the SD of the residuals about the golfer's own season mean (rounds 1-4; needs at least 20 rounds);
  B. within-event (ability and time adjusted): the pooled SD of the residuals about the golfer's own mean in each
     event, with the degrees of freedom corrected (sum of squares / (n - events)); rounds 1-4, at least 20 rounds;
  C. pre-cut: rounds 1-2 only, so every starter is included and there is no cut-survivor selection; the
     within-event pooled SD, at least 16 rounds.
Each variant is given overall and by the golfer-season's mean pre-event Overall.

ROUGH COMPARISON ONLY, not a matching metric. Data Golf's residual (actual minus predicted) strokes-gained SDs
for PGA Tour players are 2.72 (skill > +0.8) and 2.75 (0 to +0.4), rising to 3.23 for the weakest group
(datagolf.com/model-talk/2026-offseason-tweaks, 2026-02-18). Their prediction adjusts ability, time and course
differently from these residuals, and longer drivers show more variance. This world's Overall bands do not map
onto their skill groups.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402


def pooled_sd(groups):
    ss = sum(((np.array(g) - np.mean(g)) ** 2).sum() for g in groups if len(g) > 1)
    dof = sum(len(g) - 1 for g in groups if len(g) > 1)
    return float(np.sqrt(ss / dof)) if dof > 0 else np.nan, sum(len(g) for g in groups)


def main():
    save, data, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    e = pd.read_csv(data / 'editions.csv.gz', low_memory=False)
    keep = set(e[(e.primary == 1) & (e.tier <= 1)].eid)
    s = np.load(data / 'starts.npz')
    st = pd.DataFrame({'edition': s['edition'], 'gid': s['gid'], 'ovr10': s['ovr10']})
    eid_of = dict(zip(e.idx, e.eid))
    st['eid'] = st.edition.map(eid_of)
    st = st[st.eid.isin(keep)]
    ovr = {(r.eid, int(r.gid)): r.ovr10 / 10 for r in st.itertuples()}
    per_event = defaultdict(list)            # (gid, year) -> [[residuals of one event, rounds 1-4]]
    per_event12 = defaultdict(list)
    ovrs = defaultdict(list)
    for y, p in C.year_files(save).items():
        for ev in C.load_year(p)['events']:
            if ev['id'] not in keep:
                continue
            sc = ev['scores'][0]
            R = max(len(v) for v in sc.values())
            means = [np.mean([v[r] for v in sc.values() if len(v) > r]) for r in range(R)]
            for g, v in sc.items():
                res = [v[r] - means[r] for r in range(len(v))]
                key = (int(g), y)
                per_event[key].append(res)
                per_event12[key].append(res[:2])
                ovrs[key].append(ovr.get((ev['id'], int(g)), np.nan))
    rows = []
    for key, evs in per_event.items():
        flat = [x for ev_ in evs for x in ev_]
        a = float(np.std(flat, ddof=1)) if len(flat) >= 20 else np.nan
        b, nb = pooled_sd(evs)
        c, nc = pooled_sd(per_event12[key])
        rows.append((key[0], key[1], np.nanmean(ovrs[key]), len(flat), a, b if nb >= 20 else np.nan,
                     c if nc >= 16 else np.nan))
    df = pd.DataFrame(rows, columns=['gid', 'year', 'mean_overall', 'rounds', 'A_season', 'B_within_event',
                                     'C_precut_within_event'])
    df['band'] = pd.cut(df.mean_overall, [0, 70, 75, 80, 85, 90, 100])
    summ = {'note': 'rough comparison only; see the docstring', 'golfer_seasons': {}}
    for v in ['A_season', 'B_within_event', 'C_precut_within_event']:
        d = df[df[v].notna()]
        summ[v] = {'golfer_seasons': int(len(d)), 'median': float(d[v].median()),
                   'p10': float(d[v].quantile(.1)), 'p90': float(d[v].quantile(.9)),
                   'by_overall_band': {str(k): [int(len(g)), float(g[v].median())]
                                       for k, g in d.groupby('band', observed=True)}}
    summ['provenance'] = C.provenance([data / 'editions.csv.gz', data / 'starts.npz'])
    out.mkdir(parents=True, exist_ok=True)
    (out / 'volatility.json').write_text(json.dumps(summ, indent=1))
    print(json.dumps({k: v for k, v in summ.items() if k != 'provenance'}, indent=1))


if __name__ == '__main__':
    main()
