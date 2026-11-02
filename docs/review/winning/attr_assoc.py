"""Which attributes go with winning beyond Overall, in the actual history (association, not causation).

Usage: python attr_assoc.py CAPDIR DATA_DIR OUT

Data: pre-event attributes of every starter of every primary edition in the seasons the replay verified
(capture records bound to the archived finish; CAPDIR/MANIFEST.json), joined to the archived finishing position.
The compact capture is QUANTIZED: attributes and traits to 0.1, fatigue and familiarity as float32. It is not the
exact full pre-event state; the full task pickles kept for the selected events are exact.

Model, fitted per attribute (never all 21 with Overall): a within-edition conditional logit for the winner,
  P(i wins) ∝ exp(b1·x_i + b2·x_i² + c·z_i)
where x = the starter's Overall minus the field's best (points), and z = (attribute - the starter's own Overall)/10.
z is the attribute's deviation from the golfer's Overall, i.e. the profile's shape. c > 0: at the same Overall,
golfers relatively strong in this attribute win more often than Overall alone predicts. The same is done for
aggression, big_stage (personality), season fatigue and course familiarity (z = value - the edition mean, scaled
to typical units).

Caveats:
  - z is correlated with archetype (shape) and with other attributes' deviations;
  - c mixes an attribute's own shot effect with whatever goes with it (personality, career path);
  - early seasons only (the verified replay);
  - within this one world.
The controlled experiments give the mechanisms.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))
import common as C  # noqa: E402
from golfsim.golfer import OVERALL_WEIGHTS  # noqa: E402
from golfsim.ratings import ATTRIBUTE_KEYS, PERSONALITY_KEYS  # noqa: E402
from replay import read_capture  # noqa: E402

W = np.array([OVERALL_WEIGHTS[k] for k in ATTRIBUTE_KEYS])


def clogit(ed_starts, X, w):
    b = np.zeros(X.shape[1])
    seg = np.diff(np.r_[ed_starts, len(w)])
    for _ in range(60):
        f = X @ b
        fmax = np.maximum.reduceat(f, ed_starts)
        ef = np.exp(f - np.repeat(fmax, seg))
        p = ef / np.repeat(np.add.reduceat(ef, ed_starts), seg)
        g = X.T @ (w - p)
        px = X * p[:, None]
        spx = np.add.reduceat(px, ed_starts)
        H = -(X.T @ px) + spx.T @ spx
        step = np.linalg.solve(H, -g)
        b += step
        if np.abs(step).max() < 1e-10:
            break
    se = np.sqrt(np.diag(np.linalg.inv(-H)))
    return b, se


def main():
    cap, data, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    man = json.loads((cap / 'MANIFEST.json').read_text())
    years = sorted(int(y) for y, v in man['years'].items() if v['verified'])
    e = pd.read_csv(data / 'editions.csv.gz', low_memory=False)
    e = e[(e.primary == 1) & (e.n >= 2)]
    tier = dict(zip(e.eid, e.tier))
    rows = []
    for y in years:
        for fn in man['years'][str(y)]['files']:
            for rec in read_capture(cap / fn):
                eid, fin = rec[0], rec[-1]
                if eid not in tier:
                    continue
                pos = {x[0]: (x[1] or 0) for x in fin}
                A = rec[4] / 10.0
                ovr = A @ W / W.sum()
                for i, gid in enumerate(rec[3]):
                    rows.append((eid, int(gid), tier[eid], pos[int(gid)], ovr[i], *A[i], *(rec[5][i] / 10.0),
                                 float(rec[6][i]), float(rec[7][i])))
    cols = ['eid', 'gid', 'tier', 'pos', 'ovr'] + list(ATTRIBUTE_KEYS) + list(PERSONALITY_KEYS) + ['fatigue', 'fam']
    df = pd.DataFrame(rows, columns=cols).sort_values('eid', kind='stable').reset_index(drop=True)
    df['x'] = df.ovr - df.groupby('eid').ovr.transform('max')
    res = {'years': years, 'starts': int(len(df)), 'editions': int(df.eid.nunique()),
           'provenance': C.provenance([cap / 'MANIFEST.json', data / 'editions.csv.gz']), 'models': {}}
    for lab, sub in (('all', df), ('pro_tiers_0_4', df[df.tier <= 4])):
        sub = sub.reset_index(drop=True)
        ed = np.r_[0, np.flatnonzero(sub.eid.to_numpy()[1:] != sub.eid.to_numpy()[:-1]) + 1]
        w = (sub.pos == 1).to_numpy(float)
        base = np.column_stack([sub.x, sub.x ** 2])
        out_rows = []
        for k in list(ATTRIBUTE_KEYS) + ['aggression', 'big_stage', 'fatigue', 'fam']:
            if k in ATTRIBUTE_KEYS:
                z = (sub[k] - sub.ovr) / 10.0
                unit = '10 attribute points above own Overall'
            elif k in ('aggression', 'big_stage'):
                z = (sub[k] - 50) / 10.0
                unit = '10 trait points'
            elif k == 'fatigue':
                z = sub[k] / 0.1
                unit = '0.1 season fatigue'
            else:
                z = (sub[k] - sub.groupby('eid')[k].transform('mean')) / 10.0
                unit = '10 rounds of course familiarity vs field mean'
            b, se = clogit(ed, np.column_stack([base, z]), w)
            out_rows.append({'variable': k, 'unit': unit, 'coef': float(b[2]), 'se': float(se[2]),
                             'odds_ratio': float(np.exp(b[2])), 'z_sd': float(z.std()),
                             'overall_weight': float(OVERALL_WEIGHTS.get(k, np.nan) / W.sum()) if k in OVERALL_WEIGHTS else None})
        res['models'][lab] = sorted(out_rows, key=lambda r: -r['coef'])
    out.mkdir(parents=True, exist_ok=True)
    (out / 'attr_assoc.json').write_text(json.dumps(res, indent=1))
    print(res['years'], res['starts'], res['editions'])
    for lab, rows_ in res['models'].items():
        print('==', lab)
        for r in rows_:
            print(f"  {r['variable']:22s} OR {r['odds_ratio']:.3f}  coef {r['coef']:+.3f} ± {r['se']:.3f}   (z sd {r['z_sd']:.2f})")


if __name__ == '__main__':
    main()
