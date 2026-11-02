"""Component 2: archetypes and winning, by exposure and at comparable ability. Descriptive, from the archive tables.

Usage: python archetypes.py DATA_DIR SAVE_DIR OUT_DIR [--boot 500]

Labels: native generated archetypes recovered and verified by recover_archetypes.py (all 21 creation attributes
reproduced). No label is inferred from results.

Per archetype:
  - population share (verified golfers);
  - golfers with a start;
  - starts and start share;
  - wins, win share, wins per 100 starts, top-10 per 100 and cuts per 100;
  - field exposure E_equal = sum over editions of n_archetype / field size (the wins expected if every entrant
    were equally likely: opportunity only);
  - E_ovr, the wins expected from each starter's pre-event Overall within the field. This comes from a
    within-edition conditional logit on Overall, fitted on every primary edition and blind to archetype, with
    separate coefficients per round count (1-4) on (Overall - field best) and its square;
  - E_std, a non-parametric cross-check: indirect standardisation by Overall rank in the field x level x rounds.

O/E_ovr > 1 means the archetype won more than the Overall-only model predicts for its starters. It is an
ASSOCIATION, not a fully controlled causal comparison: the model is a pooled gap-to-best quadratic per round
count (not per level, field depth or course), it over-predicts the strongest favourites (see
arch_clogit_calibration.csv), and archetypes also differ in development, access and personality. The
controlled fixed-Overall profiles (experiments) address mechanism. The model never holds Overall and all 21
components at once. Made-cut rates count only editions with a genuine cut (more than two rounds, a cut size
below the field size).

Uncertainty: golfer-clustered bootstrap (resampling golfers within the archetype, keeping each golfer's whole
record), which measures stability WITHIN this one world, not seed-to-seed variation.

Splits:
  - level: all; majors; Premier; tiers 2-4; college; amateur; club pro;
  - initial seeded golfers versus later entrants;
  - age at the event: 25-35 (prime) versus all;
  - without Cardenas.
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

LEVELS = {'Majors': [0], 'Premier': [1], 'Tiers 2-4': [2, 3, 4], 'College': [5], 'Amateur': [6], 'Club pro': [8]}


def load(data, save):
    e = pd.read_csv(Path(data) / 'editions.csv.gz', low_memory=False)
    e = e[(e.primary == 1) & (e.n >= 2)].copy()
    s = np.load(Path(data) / 'starts.npz')
    st = pd.DataFrame({k: s[k] for k in s.files})
    st = st[st.edition.isin(e.idx)].copy()
    ei = e.set_index('idx')
    for c in ['tier', 'rounds', 'year', 'n']:
        st[c] = st.edition.map(ei[c]).astype(int)
    a = pd.read_csv(Path(data) / 'archetypes.csv.gz').set_index('gid')
    st['arch'] = st.gid.map(a.archetype)
    st['path'] = st.gid.map(a.path)
    people = C.load_json_gz(C.archive_file(save, 'people'))
    born = pd.Series({int(g): v['born'] for g, v in people.items() if 'golfer' in v})
    st['age'] = st.year - st.gid.map(born)
    st['win'] = (st.pos == 1).astype(np.int8)
    st['top10'] = ((st.pos >= 1) & (st.pos <= 10)).astype(np.int8)
    ei_cut = ((ei.rounds > 2) & (ei.cut_top.fillna(0) > 0) & (ei.cut_top.fillna(0) < ei.n))
    st['cut_event'] = st.edition.map(ei_cut).astype(bool)          # a genuine cut was made in this edition
    st['cut'] = (st.pos >= 1).astype(np.int8)                     # (made the cut; read only where cut_event)
    st['x'] = (st.ovr10 - st.groupby('edition').ovr10.transform('max')) / 10.0
    st['rank'] = st.groupby('edition').ovr10.rank(ascending=False, method='min').astype(int)
    return e, st, a


def fit_clogit(st):
    """Conditional logit P(i wins edition) = exp(f_i) / sum_j exp(f_j), f = b1[r] x + b2[r] x^2 (r = rounds).
    Newton on the exact likelihood (one winner per edition). Returns per-start probabilities and coefficients."""
    st = st.sort_values(['edition']).copy()
    ed = st.edition.to_numpy()
    starts = np.r_[0, np.flatnonzero(np.diff(ed)) + 1]
    r = st.rounds.to_numpy()
    x = st.x.to_numpy()
    X = np.zeros((len(st), 8))
    for k in range(4):
        m = r == k + 1
        X[m, 2 * k] = x[m]
        X[m, 2 * k + 1] = x[m] ** 2
    w = st.win.to_numpy().astype(float)
    b = np.zeros(8)
    for it in range(50):
        f = X @ b
        fmax = np.maximum.reduceat(f, starts)
        ef = np.exp(f - np.repeat(fmax, np.diff(np.r_[starts, len(f)])))
        den = np.add.reduceat(ef, starts)
        p = ef / np.repeat(den, np.diff(np.r_[starts, len(f)]))
        g = X.T @ (w - p)
        # Hessian: -sum_e [sum p x x' - (sum p x)(sum p x)']
        px = X * p[:, None]
        spx = np.add.reduceat(px, starts)
        H = -(X.T @ px) + spx.T @ spx
        step = np.linalg.solve(H, -g)
        b = b + step
        if np.abs(step).max() < 1e-9:
            break
    st['p_ovr'] = p
    ll = float(np.sum(np.log(p[w == 1])))
    return st, b, ll, it


def indirect(st):
    """Expected wins/top10/cuts by indirect standardisation over (Overall rank bin x level x rounds)."""
    rb = pd.cut(st['rank'], [0, 1, 2, 3, 5, 10, 20, 50, 100000], labels=False)
    lv = st.tier.map({0: 0, 1: 1, 2: 2, 3: 2, 4: 2, 5: 3, 6: 4, 8: 5})
    key = rb.astype(int) * 100 + lv * 10 + st.rounds
    for c in ['win', 'top10', 'cut']:
        st[f'e_{c}'] = key.map(st.groupby(key)[c].mean())
    return st


def table(st, B, rng, pop=None):
    rows = []
    tot_starts, tot_wins = len(st), st.win.sum()
    for arch, g in st.groupby('arch'):
        per = g.groupby('gid').agg(win=('win', 'sum'), n=('win', 'size'), eqv=('eq', 'sum'), pov=('p_ovr', 'sum'),
                                   ew=('e_win', 'sum'), t10=('top10', 'sum'), et10=('e_top10', 'sum'))
        W, Eq, P, Ew = per.win.to_numpy(float), per.eqv.to_numpy(float), per.pov.to_numpy(float), per.ew.to_numpy(float)
        idx = rng.integers(0, len(per), size=(B, len(per)))
        oe = W[idx].sum(1) / P[idx].sum(1)
        oq = W[idx].sum(1) / Eq[idx].sum(1)
        rows.append({
            'archetype': arch, 'population_share': (pop or {}).get(arch, np.nan), 'golfers_with_starts': len(per),
            'starts': len(g), 'start_share': len(g) / tot_starts, 'wins': int(W.sum()),
            'win_share': W.sum() / tot_wins if tot_wins else np.nan, 'wins_per_100': 100 * W.sum() / len(g),
            'top10_per_100': 100 * g.top10.mean(),
            'cut_events_starts': int(g.cut_event.sum()),
            'made_cut_per_100_in_cut_events': 100 * g.cut[g.cut_event].mean() if g.cut_event.any() else np.nan,
            'mean_pre_event_overall': g.ovr10.mean() / 10, 'mean_rank_in_field': g['rank'].mean(),
            'E_equal': Eq.sum(), 'O_over_E_equal': W.sum() / Eq.sum(),
            'O_over_E_equal_ci': [float(np.percentile(oq, 2.5)), float(np.percentile(oq, 97.5))],
            'E_ovr': P.sum(), 'O_over_E_ovr': W.sum() / P.sum(),
            'O_over_E_ovr_ci': [float(np.percentile(oe, 2.5)), float(np.percentile(oe, 97.5))],
            'O_over_E_std': W.sum() / Ew.sum(),
            'top10_O_over_E_std': per.t10.sum() / per.et10.sum(),
        })
    return pd.DataFrame(rows).sort_values('O_over_E_ovr', ascending=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('data')
    ap.add_argument('save')
    ap.add_argument('out')
    ap.add_argument('--boot', type=int, default=500)
    a = ap.parse_args()
    rng = np.random.default_rng(20261102)
    e, st, arch = load(a.data, a.save)
    unl = int(st.arch.isna().sum())
    st = st[st.arch.notna()].copy()
    st['eq'] = 1.0 / st.n
    st, b, ll, it = fit_clogit(st)
    st = indirect(st)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ver = arch[arch.status.str.startswith('verified')]
    pop_all = (ver.archetype.value_counts(normalize=True)).to_dict()
    d = Path(a.data)
    res = {'provenance': C.provenance([d / 'editions.csv.gz', d / 'starts.npz', d / 'archetypes.csv.gz',
                                       C.archive_file(a.save, 'people')], {'boot': a.boot, 'boot_seed': 20261102}),
           'starts_without_label': unl, 'clogit': {'coef': b.tolist(), 'loglik': ll, 'iterations': it,
                                                   'terms': 'per rounds 1..4: (x, x^2), x = Overall - field best'},
           'population_share': pop_all}
    tabs = {'all': table(st, a.boot, rng, pop_all)}
    for name, tiers in LEVELS.items():
        tabs[f'level_{name}'] = table(st[st.tier.isin(tiers)], a.boot, rng, pop_all)
    tabs['initial_golfers'] = table(st[st.path == 'initial'], a.boot, rng,
                                    ver[ver.path == 'initial'].archetype.value_counts(normalize=True).to_dict())
    tabs['later_entrants'] = table(st[st.path != 'initial'], a.boot, rng,
                                   ver[ver.path != 'initial'].archetype.value_counts(normalize=True).to_dict())
    tabs['age_25_35'] = table(st[(st.age >= 25) & (st.age <= 35)], a.boot, rng, pop_all)
    tabs['without_cardenas'] = table(st[st.gid != C.CARDENAS], a.boot, rng, pop_all)
    tabs['majors_premier_without_cardenas'] = table(st[(st.tier <= 1) & (st.gid != C.CARDENAS)], a.boot, rng, pop_all)
    # Overall distribution of each archetype's starts (exposure by ability) and calibration of the Overall model
    st['ovr_bin'] = pd.cut(st.ovr10 / 10, [0, 50, 60, 65, 70, 75, 80, 85, 90, 100])
    mix = pd.crosstab(st.arch, st.ovr_bin, normalize='index')
    mix.columns = mix.columns.astype(str)
    tabs['overall_mix_of_starts'] = mix.reset_index()
    st['pbin'] = pd.cut(st.p_ovr, [0, .001, .005, .01, .02, .05, .1, .2, .4, 1])
    cal = st.groupby('pbin', observed=True).agg(starts=('win', 'size'), model=('p_ovr', 'mean'), observed=('win', 'mean'))
    cal.index = cal.index.astype(str)
    tabs['clogit_calibration'] = cal.reset_index()
    for k, df in tabs.items():
        df.to_csv(out / f'arch_{k}.csv', index=False, float_format='%.4f')
    res['tables'] = sorted(f'arch_{k}.csv' for k in tabs)
    (out / 'archetypes.json').write_text(json.dumps(res, indent=1, default=float))
    pd.set_option('display.width', 250)
    cols = ['archetype', 'population_share', 'start_share', 'win_share', 'wins_per_100', 'mean_pre_event_overall',
            'O_over_E_equal', 'O_over_E_ovr', 'O_over_E_ovr_ci', 'O_over_E_std', 'top10_O_over_E_std']
    for k in ['all', 'level_Majors', 'level_Premier', 'level_Tiers 2-4', 'without_cardenas',
              'majors_premier_without_cardenas']:
        print('==', k)
        print(tabs[k][cols].to_string(index=False, float_format=lambda v: f'{v:.3f}'))
    print(json.dumps(res['clogit']))


if __name__ == '__main__':
    main()
