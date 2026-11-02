"""Component 1: how often the best entrant (highest pre-event Overall) wins. Descriptive, from the archive tables.

Usage: python favourite.py DATA_DIR OUT_DIR [--boot 1000]

Inputs (from extract.py and recover_archetypes.py): editions.csv.gz, starts.npz, archetypes.csv.gz.
Population: primary editions only (one site, stroke play, not qualifying, field reconciled, one champion).
Best entrant: highest stored pre-event Overall (0.1 resolution). Ties at the top are a set: 'unique best' and
'tied best' are reported separately; for tied sets, the set's win rate and the per-member share.
Uncertainty: bootstrap clustered by the best entrant's identity (a golfer who is best in many editions is one
cluster), alongside the plain edition-level binomial interval. Both describe stability WITHIN this one world;
they are not seed-to-seed uncertainty and not a calibration against real golf.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

LEVEL = {0: 'Majors', 1: 'Premier', 2: 'Tier 2 tours', 3: 'Tier 3 tours', 4: 'Tier 4 tours', 5: 'College',
         6: 'Amateur', 8: 'Club pro'}


def load(data):
    e = pd.read_csv(Path(data) / 'editions.csv.gz', low_memory=False)
    e = e[e.primary == 1].copy()
    e = e[e.n >= 2].copy()          # a one-entrant edition has no contest (counted in the audit, excluded here)
    for c in ['n', 'n_max', 'w_rank', 'top_won', 'top_best_pos', 'tier', 'rounds', 'year', 'cardenas_in',
              'cardenas_won']:
        e[c] = e[c].astype(int)
    e['level'] = e.tier.map(LEVEL)
    e['era'] = ((e.year - 2027) // 10 * 10 + 2027).astype(str) + 's'
    e['top1'] = e.top_ids.astype(str).str.split(';').str[0].astype(int)
    s = np.load(Path(data) / 'starts.npz')
    st = pd.DataFrame({k: s[k] for k in s.files})
    mx = st.groupby('edition').ovr10.transform('max')            # exact integer tenths
    d2 = (st.ovr10 >= mx - 20).groupby(st.edition).sum()
    d5 = (st.ovr10 >= mx - 50).groupby(st.edition).sum()
    e['within2'] = e.idx.map(d2).astype(int)
    e['within5'] = e.idx.map(d5).astype(int)
    k = st.set_index(['edition', 'gid']).rounds_played
    e['top1_rp'] = [int(k.get((i, g), -1)) for i, g in zip(e.idx, e.top1)]
    a = pd.read_csv(Path(data) / 'archetypes.csv.gz').set_index('gid')
    e['top1_path'] = e.top1.map(a.path)
    return e, st, a


def cluster_boot(df, num, den, cluster, B, rng):
    """Ratio sum(num)/sum(den) with a bootstrap over clusters: (estimate, lo, hi)."""
    g = df.groupby(cluster)[[num, den]].sum()
    n, d = g[num].to_numpy(float), g[den].to_numpy(float)
    est = n.sum() / d.sum() if d.sum() else float('nan')
    if len(g) < 2:
        return est, float('nan'), float('nan')
    idx = rng.integers(0, len(g), size=(B, len(g)))
    bs = n[idx].sum(1) / np.maximum(d[idx].sum(1), 1e-12)
    return est, float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def wilson(k, n, z=1.96):
    if n == 0:
        return float('nan'), float('nan')
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def summary(e, B, rng, label):
    """The headline block for a subset of editions."""
    u = e[e.n_max == 1].copy()
    t = e[e.n_max > 1]
    u['one'] = 1
    est, lo, hi = cluster_boot(u, 'top_won', 'one', 'top1', B, rng) if len(u) else (np.nan,) * 3
    fin = u.top_best_pos
    out = {
        'subset': label, 'editions': int(len(e)), 'unique_best': int(len(u)), 'tied_best': int(len(t)),
        'unique_best_win': est, 'unique_best_win_ci_cluster': [lo, hi],
        'unique_best_win_ci_edition': list(wilson(int(u.top_won.sum()), len(u))),
        'unique_best_distinct_golfers': int(u.top1.nunique()),
        'unique_best_top3': float(((fin >= 1) & (fin <= 3)).mean()) if len(u) else np.nan,
        'unique_best_top5': float(((fin >= 1) & (fin <= 5)).mean()) if len(u) else np.nan,
        'unique_best_top10': float(((fin >= 1) & (fin <= 10)).mean()) if len(u) else np.nan,
        'unique_best_missed_cut_or_no_position': float((fin == 0).mean()) if len(u) else np.nan,
        'unique_best_missed_cut': float(((fin == 0) & (u.rounds > 2) & (u.top1_rp == 2)).mean()) if len(u) else np.nan,
        'unique_best_withdrew': float(((fin == 0) & ~((u.rounds > 2) & (u.top1_rp == 2))).mean()) if len(u) else np.nan,
        'tied_set_win': float(t.top_won.mean()) if len(t) else np.nan,
        'tied_set_mean_size': float(t.n_max.mean()) if len(t) else np.nan,
        'tied_per_member_share': float((t.top_won / t.n_max).mean()) if len(t) else np.nan,
        'winner_rank1': float((e.w_rank == 1).mean()),
        'winner_rank_le3': float((e.w_rank <= 3).mean()),
        'winner_rank_le5': float((e.w_rank <= 5).mean()),
        'winner_rank_le10': float((e.w_rank <= 10).mean()),
        'winner_rank_gt20': float((e.w_rank > 20).mean()),
        'winner_rank_median': float(e.w_rank.median()),
        'winner_gap_mean': float((e.max_ovr - e.w_ovr).mean()),
        'winner_gap_median': float((e.max_ovr - e.w_ovr).median()),
        'winner_gap_p90': float((e.max_ovr - e.w_ovr).quantile(0.9)),
        'playoff_share': float((e.playoff_holes > 0).mean()),
        'margin_median': float(e.margin.median()),
        'field_median': float(e.n.median()),
    }
    return out


def strata(e, col, B, rng, order=None):
    rows = []
    for k, g in e.groupby(col, observed=True):
        s = summary(g, B, rng, f'{col}={k}')
        rows.append(s)
    df = pd.DataFrame(rows)
    if order is not None:
        df['_o'] = df.subset.map({f'{col}={k}': i for i, k in enumerate(order)})
        df = df.sort_values('_o').drop(columns='_o')
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('data')
    ap.add_argument('out')
    ap.add_argument('--boot', type=int, default=1000)
    a = ap.parse_args()
    rng = np.random.default_rng(20261102)
    e, st, arch = load(a.data)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    B = a.boot
    d = Path(a.data)
    res = {'provenance': C.provenance([d / 'editions.csv.gz', d / 'starts.npz', d / 'archetypes.csv.gz'],
                                      {'boot': B, 'boot_seed': 20261102})}
    res['all'] = summary(e, B, rng, 'all primary editions')
    pro = e[e.tier <= 4]
    res['pro_tiers_0_4'] = summary(pro, B, rng, 'professional tiers 0-4')
    res['majors'] = summary(e[e.tier == 0], B, rng, 'majors')
    res['premier'] = summary(e[e.tier == 1], B, rng, 'Premier')
    # Cardenas: two distinct sensitivities
    e['card_best'] = e.top_ids.astype(str).str.split(';').apply(lambda ids: str(C.CARDENAS) in ids)
    res['excl_cardenas_as_best'] = summary(e[~e.card_best], B, rng, 'excluding editions where Cardenas is (or ties for) the best entrant')
    res['excl_cardenas_entered'] = summary(e[e.cardenas_in == 0], B, rng, 'excluding every edition Cardenas entered')
    res['majors_excl_cardenas_entered'] = summary(e[(e.tier == 0) & (e.cardenas_in == 0)], B, rng, 'majors without Cardenas in the field')
    res['majors_excl_cardenas_as_best'] = summary(e[(e.tier == 0) & ~e.card_best], B, rng, 'majors where Cardenas is not (and does not tie for) the best entrant')
    lv = [LEVEL[k] for k in sorted(LEVEL)]
    tabs = {
        'level': strata(e, 'level', B, rng, lv),
        'rounds': strata(e, 'rounds', B, rng, [1, 2, 3, 4]),
        'era': strata(e, 'era', B, rng, sorted(e.era.unique())),
        'era_pro': strata(pro, 'era', B, rng, sorted(e.era.unique())),
    }
    e['field_bin'] = pd.cut(e.n, [0, 30, 60, 100, 144, 1000], labels=['<=30', '31-60', '61-100', '101-144', '145+'])
    tabs['field_size'] = strata(e, 'field_bin', B, rng, ['<=30', '31-60', '61-100', '101-144', '145+'])
    gb = pd.cut(e.gap12, [-0.01, 0.0, 0.95, 1.95, 2.95, 4.95, 100],
                labels=['tied (0)', '0.1-0.9', '1.0-1.9', '2.0-2.9', '3.0-4.9', '5.0+'])
    e['gap_bin'] = gb      # gap12: true first-second gap (0 when the best are tied)
    tabs['gap_best_to_next'] = strata(e, 'gap_bin', B, rng, ['tied (0)', '0.1-0.9', '1.0-1.9', '2.0-2.9', '3.0-4.9', '5.0+'])
    pro = e[e.tier <= 4]
    tabs['gap_best_to_next_pro'] = strata(pro, 'gap_bin', B, rng, ['tied (0)', '0.1-0.9', '1.0-1.9', '2.0-2.9', '3.0-4.9', '5.0+'])
    e['depth2'] = pd.cut(e.within2, [0, 1, 2, 4, 8, 10000], labels=['1 (alone)', '2', '3-4', '5-8', '9+'])
    tabs['depth_within2'] = strata(e, 'depth2', B, rng, ['1 (alone)', '2', '3-4', '5-8', '9+'])
    pro = e[e.tier <= 4]
    tabs['depth_within2_pro'] = strata(pro, 'depth2', B, rng, ['1 (alone)', '2', '3-4', '5-8', '9+'])
    tabs['best_entrant_path'] = strata(e[e.n_max == 1], 'top1_path', B, rng, ['initial', 'junior', 'late_entrant'])
    # stored model (approximation) calibration for its favourite, majors+premier and all
    e['fav_won'] = (e.fav == e.winner).astype(int)
    e['fav_bin'] = pd.cut(e.fav_p, [0, .05, .1, .15, .2, .3, .4, .6, 1.0])
    cal = e.groupby('fav_bin', observed=True).agg(editions=('fav_won', 'size'), model_mean=('fav_p', 'mean'),
                                                  observed=('fav_won', 'mean')).reset_index()
    cal['fav_bin'] = cal.fav_bin.astype(str)
    tabs['model_calibration_favourite'] = cal
    e['fav_in_top'] = [str(int(f)) in str(t).split(';') for f, t in zip(e.fav, e.top_ids)]
    res['model_favourite_is_highest_overall'] = float(e.fav_in_top.mean())
    # the most frequent best entrants (clusters) and their records
    u = e[e.n_max == 1]
    top = u.groupby('top1').agg(times_best=('top_won', 'size'), won=('top_won', 'sum'),
                                majors_best=('tier', lambda x: int((x == 0).sum()))).sort_values('times_best', ascending=False)
    top['win_rate'] = top.won / top.times_best
    tabs['most_frequent_best_entrants'] = top.head(15).reset_index()
    res['share_of_unique_best_editions_from_top10_golfers'] = float(top.times_best.head(10).sum() / top.times_best.sum())
    for k, df in tabs.items():
        df.to_csv(out / f'fav_{k}.csv', index=False, float_format='%.4f')
    res['tables'] = sorted(f'fav_{k}.csv' for k in tabs)
    (out / 'favourite.json').write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: res[k] for k in ['all', 'pro_tiers_0_4', 'majors', 'premier']}, indent=1, default=float)[:4000])


if __name__ == '__main__':
    main()
