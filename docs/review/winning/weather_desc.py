"""Component 4 (descriptive): recorded weather, where and when it falls, and how outcomes differ with it.
Read-only, from the archive tables. Associations only: weather is not randomised across courses, levels or fields.

Usage: python weather_desc.py DATA_DIR SAVE OUT

Course metadata (style, typical wind, coast, climate group, hemisphere) comes from the v2 course library code
(course_library.default_library('v2'), the calendar the save plays). It is used only after every course id in
the save's world file matches it by name, city and each layout's par and yardage; a mismatch stops the script.

Weather per edition: every round's recorded seasonal conditions (wind mph, wet, pins, direction, gustiness), all
golfers in a round sharing one set. Outcomes per primary edition:
  - whether the unique best entrant won;
  - the winner's Overall rank;
  - the winning margin;
  - playoffs;
  - the finishers' mean score to par per round (the common penalty);
  - the finishers' SD of totals (dispersion).
Confounding is shown, not assumed away:
  - by level and by links versus other courses;
  - within-course comparisons: course-demeaned regressions of each outcome on mean wind and wet rounds, with
    field depth (true first-second gap), field size, rounds, year (era), mean field Overall and the top-10
    mean Overall (absolute ability) as covariates. These are still associations, not causal effects:
    weather is not randomised. The finishers' scoring measures are cut survivors, whose identities can
    change with conditions.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))
import common as C  # noqa: E402
from golfsim import weather as WX  # noqa: E402
from golfsim.course_library import default_library  # noqa: E402


def course_table(save):
    w = json.loads(C.archive_file(save, 'world').read_text())
    lib = default_library('v2')
    rows, bad = [], []
    for cid, c in w['courses'].items():
        s = lib.sites.get(cid)
        if s is None:
            bad.append((cid, 'missing'))
            continue
        lay = s['layouts']
        same = (s['name'] == c['name'] and s['city'] == c['city'] and set(lay) == set(c['layouts'])
                and all(lay[k].par == v['par'] and round(lay[k].yards) == round(v['yards'])
                        for k, v in c['layouts'].items()))
        if not same:
            bad.append((cid, 'differs'))
            continue
        any_layout = next(iter(lay.values()))
        cl = WX.climate_of(any_layout)
        rows.append({'course': cid, 'style': s['style'], 'class': c.get('class'), 'country': c.get('country'),
                     'typical_wind': any_layout.typical_wind, 'coastal': cl.coastal, 'climate': cl.group,
                     'south': cl.south})
    if bad:
        raise SystemExit(f'course library does not match the save: {bad[:5]} ({len(bad)})')
    return pd.DataFrame(rows).set_index('course')


def within(df, y, xs, group='course'):
    """OLS of y on xs after demeaning everything by `group` (fixed effects). Returns coefficients and
    cluster-robust (by group) SEs."""
    d = df[[y, group] + xs].dropna()
    g = d.groupby(group)
    Y = (d[y] - g[y].transform('mean')).to_numpy()
    X = np.column_stack([(d[x] - g[x].transform('mean')).to_numpy() for x in xs])
    XtX = X.T @ X
    b = np.linalg.solve(XtX, X.T @ Y)
    e = Y - X @ b
    inv = np.linalg.inv(XtX)
    meat = np.zeros_like(XtX)
    for _, idx in d.groupby(group).indices.items():
        s = X[idx].T @ e[idx]
        meat += np.outer(s, s)
    V = inv @ meat @ inv
    return {x: (float(b[i]), float(np.sqrt(V[i, i]))) for i, x in enumerate(xs)} | {'n': int(len(d)),
                                                                                    'groups': int(d[group].nunique())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('data')
    ap.add_argument('save')
    ap.add_argument('out')
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ct = course_table(a.save)
    e = pd.read_csv(Path(a.data) / 'editions.csv.gz', low_memory=False)
    e = e[(e.primary == 1) & (e.n >= 2)].copy()
    for c in ['style', 'typical_wind', 'coastal', 'climate', 'south']:
        e[c] = e.course.map(ct[c])
    e['links'] = e['style'].eq('Links')
    e['month'] = ((e.week - 1) * 12 // 52).clip(0, 11)
    e['local_month'] = np.where(e.south.astype(bool), (e.month + 6) % 12, e.month)
    s = np.load(Path(a.data) / 'starts.npz')
    st = pd.DataFrame({k: s[k] for k in s.files})
    fin = st[(st.pos >= 1) & (st.total > 0)]
    e['finisher_mean_total'] = e.idx.map(fin.groupby('edition').total.mean())
    e['to_par_per_round'] = e.finisher_mean_total / e.rounds - e.par
    e['win_to_par_per_round'] = e.win_total / e.rounds - e.par
    e['best_won'] = np.where(e.n_max == 1, e.top_won, np.nan)
    e['w_rank_log'] = np.log(e.w_rank)
    e['wind_band'] = pd.cut(e.wind_mean, [-0.1, 6, 10, 14, 18, 22, 100],
                            labels=['<6', '6-10', '10-14', '14-18', '18-22', '22+'])
    e['wet_any'] = (e.wet_rounds > 0).astype(int)
    e['pro'] = e.tier <= 4
    e['gap12'] = e.gap12.fillna(0)
    res = {'provenance': C.provenance([Path(a.data) / 'editions.csv.gz', Path(a.data) / 'starts.npz',
                                       C.archive_file(a.save, 'world')], {'course_library': 'v2'}),
           'courses_matched': int(len(ct)), 'editions': int(len(e))}
    tabs = {}
    # coverage
    tabs['coverage_climate_month'] = e.groupby(['climate', 'local_month']).agg(
        editions=('idx', 'size'), wind=('wind_mean', 'mean'), wet_rounds_share=('wet_rounds', 'sum'),
        rounds=('rounds', 'sum'), gust=('gust_mean', 'mean')).reset_index()
    tabs['coverage_climate_month']['wet_round_rate'] = (tabs['coverage_climate_month'].wet_rounds_share /
                                                        tabs['coverage_climate_month'].rounds)
    tabs['coverage_style'] = e.groupby('style').agg(
        editions=('idx', 'size'), courses=('course', 'nunique'), typical_wind=('typical_wind', 'mean'),
        wind=('wind_mean', 'mean'), wind_p90=('wind_mean', lambda x: x.quantile(.9)),
        wet_round_rate=('wet_rounds', lambda x: x.sum()), rounds=('rounds', 'sum'),
        gust=('gust_mean', 'mean'), pro_share=('pro', 'mean')).reset_index()
    tabs['coverage_style']['wet_round_rate'] /= tabs['coverage_style'].rounds
    tabs['coverage_level_wind'] = pd.crosstab(e.tier, e.wind_band, normalize='index').reset_index()
    tabs['coverage_level_wind'].columns = tabs['coverage_level_wind'].columns.astype(str)
    # descriptive outcomes by band, pro tiers, links vs other
    def band(df, by):
        return df.groupby(by, observed=True).agg(
            editions=('idx', 'size'), best_won=('best_won', 'mean'), winner_rank_median=('w_rank', 'median'),
            winner_rank1=('w_rank', lambda x: (x == 1).mean()), winner_top5=('w_rank', lambda x: (x <= 5).mean()),
            margin=('margin', 'mean'), playoff=('playoff_holes', lambda x: (x > 0).mean()),
            to_par_per_round=('to_par_per_round', 'mean'), win_to_par_per_round=('win_to_par_per_round', 'mean'),
            sd_made=('sd_made', 'mean'), gap12=('gap12', 'mean'), field=('n', 'mean'),
            depth_sd_ovr=('sd_ovr', 'mean')).reset_index()
    pro = e[e.pro]
    tabs['outcome_wind_pro'] = band(pro, ['wind_band'])
    tabs['outcome_wind_pro_links'] = band(pro, ['links', 'wind_band'])
    tabs['outcome_wet_pro'] = band(pro, ['wet_rounds', 'rounds'])
    tabs['outcome_wind_all'] = band(e, ['wind_band'])
    for k in tabs:
        tabs[k].to_csv(out / f'wx_{k}.csv', index=False, float_format='%.4f')
    # within-course regressions (associations; course fixed effects)
    covs = ['wind_mean', 'wet_rounds', 'gap12', 'n', 'rounds', 'year', 'mean_ovr', 'top10_mean_ovr']
    reg = {}
    for lab, df in (('pro', pro), ('all', e), ('pro_links', pro[pro.links]), ('pro_other', pro[~pro.links])):
        reg[lab] = {y: within(df, y, covs) for y in ['best_won', 'w_rank_log', 'margin', 'to_par_per_round',
                                                       'sd_made']}
    res['within_course'] = reg
    res['tables'] = sorted(f'wx_{k}.csv' for k in tabs)
    (out / 'weather_desc.json').write_text(json.dumps(res, indent=1, default=float))
    pd.set_option('display.width', 250)
    for k in ['coverage_style', 'outcome_wind_pro', 'outcome_wind_pro_links', 'outcome_wet_pro']:
        print('==', k)
        print(tabs[k].to_string(index=False, float_format=lambda v: f'{v:.3f}'))
    for lab in reg:
        print('== within-course', lab)
        for y, r in reg[lab].items():
            print(f'  {y:20s} n={r["n"]} groups={r["groups"]} wind {r["wind_mean"][0]:+.4f}±{r["wind_mean"][1]:.4f}'
                  f'  wet {r["wet_rounds"][0]:+.4f}±{r["wet_rounds"][1]:.4f}')


if __name__ == '__main__':
    main()
