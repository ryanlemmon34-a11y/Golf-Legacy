"""Tables for the report from the experiment outputs (no simulation here).

Usage: python summarise.py EXP_DIR OUT_MD

Reads (any that exist): rounds_grid.json, fixed_*.json, events_validation*.json, weather_cf.json,
rounds_arch.json, rounds_sd.json, attr_sd_premier.json. Writes markdown tables:
  - per-attribute stroke effects of +5 / -5 points (paired, SE), by context (R1, R4, R4P), subject and event,
    with clipped arms flagged and the zero checks shown;
  - context-dependent rankings (never one universal list);
  - fixed-field win effects next to the full-event validation;
  - weather arms.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

EV = {'2027_BRITANNIA_OPEN_s0.pkl': 'Britannia Open (major, links)', '2027_USA_OPEN_s0.pkl': 'USA Open (major, parkland)',
      '2027_PT_FRANCE_OPEN_s0.pkl': 'France Open (Premier, woodland)',
      '2027_CH_EUROPE_01_s0.pkl': 'CH Europe 01 (tier 2, woodland)'}


def arm_parts(arm):
    for sign in ('+', '-'):
        if sign in arm and not arm.startswith('arch:'):
            k, d = arm.split(sign, 1)
            return k, float(d) * (1 if sign == '+' else -1)
    return arm, 0.0


def rounds_tables(d):
    df = pd.DataFrame(d['rows'])
    df['attr'], df['delta'] = zip(*df.arm.map(arm_parts))
    subj = d['subjects']
    df['base_value'] = [subj[f'{e}:{g}']['attrs'].get(a, np.nan) for e, g, a in zip(df.event, df.gid, df.attr)]
    df['actual_delta'] = np.clip(df.base_value + df.delta, 1, 99) - df.base_value
    clipped = df[df.clipped & (df.context == 'R1')][['event', 'rank', 'attr', 'delta', 'base_value', 'actual_delta']]
    df = df[~df.clipped]                 # clipped arms are excluded from every average and ranking below
    df['event_label'] = df.event.map(EV).fillna(df.event)
    out = []
    for delta in sorted(df.delta.unique()):
        if delta == 0:
            continue
        sub = df[df.delta == delta]
        piv = sub.pivot_table(index='attr', columns=['context'], values='d_mean', aggfunc='mean')
        piv_se = sub.pivot_table(index='attr', columns=['context'], values='d_se', aggfunc=lambda x: np.sqrt((x ** 2).mean()))
        piv = piv.sort_values('R1')
        cnt = sub[sub.context == 'R1'].groupby('attr').size()
        lines = [f'\n#### {delta:+g} points: Δ strokes per round, mean over the unclipped subject-event cells '
                 f'(of {d["n"]} paired samples each; negative = better; ± = RMS of the cells\' paired SEs)\n',
                 '| Attribute | R1 (no pressure) | R4 (in-week fatigue) | R4 + contention | cells |', '|---|---|---|---|---|']
        for attr, r in piv.iterrows():
            se = piv_se.loc[attr]
            lines.append(f'| {attr} | {r["R1"]:+.3f} ± {se["R1"]:.3f} | {r["R4"]:+.3f} ± {se["R4"]:.3f} | '
                         f'{r["R4P"]:+.3f} ± {se["R4P"]:.3f} | {cnt.get(attr, 0)} |')
        out.append('\n'.join(lines))
    # context-dependent ranking for +5: by subject rank and event (R1)
    sub = df[(df.delta == 5) & (df.context == 'R1')]
    lines = ['\n#### +5 points, R1: rank of each attribute within each event and subject (1 = largest gain; '
             'clipped arms omitted)\n']
    tab = sub.assign(col=sub.event_label.str.split(' \\(').str[0] + ' r' + sub['rank'].astype(str))
    tab['r'] = tab.groupby('col').d_mean.rank(method='min')
    p = tab.pivot_table(index='attr', columns='col', values='r')
    p['median'] = p.median(axis=1)
    p = p.sort_values('median')
    lines.append('| Attribute | ' + ' | '.join(p.columns) + ' |')
    lines.append('|---' * (len(p.columns) + 1) + '|')
    for attr, r in p.iterrows():
        lines.append(f'| {attr} | ' + ' | '.join('' if np.isnan(v) else f'{v:.0f}' for v in r.values) + ' |')
    out.append('\n'.join(lines))
    # variance: SD ratio
    sub = df[(df.delta == 5) & (df.context == 'R1')]
    sd = sub.groupby('attr').sd_ratio.mean().sort_values()
    out.append('\n#### +5 points, R1: SD of the round score relative to baseline (mean over subjects/events)\n\n' +
               ' · '.join(f'{k} {v:.3f}' for k, v in sd.items()))
    if len(clipped):
        out.append('\n#### Clipped arms (excluded above; the actual change applied was smaller than nominal)\n\n'
                   '| Event | Subject rank | Attribute | Nominal | Base value | Actual change |\n|---|---|---|---|---|---|\n' +
                   '\n'.join(f'| {EV.get(r.event, r.event)} | {r.rank} | {r.attr} | {r.delta:+g} | {r.base_value:.1f} | '
                             f'{r.actual_delta:+.1f} |' for r in clipped.itertuples()))
    return '\n'.join(out)


def arch_rounds(d):
    df = pd.DataFrame(d['rows'])
    df['event_label'] = df.event.map(EV).fillna(df.event)
    lines = ['| Profile (same Overall) | Context | Δ mean vs subject\'s own profile | SD ratio | beat base p10 | over base p90 | '
             'subjects × events |', '|---|---|---|---|---|---|---|']
    g = df[df.arm != 'base'].groupby(['arm', 'context']).agg(d=('d_mean', 'mean'), sd=('sd_ratio', 'mean'),
                                                            lo=('beat_base_p10', 'mean'), hi=('over_base_p90', 'mean'),
                                                            n=('d_mean', 'size')).reset_index()
    for r in g.sort_values(['context', 'd']).itertuples():
        lines.append(f'| {r.arm[5:]} | {r.context} | {r.d:+.3f} | {r.sd:.3f} | {r.lo:.3f} | {r.hi:.3f} | {r.n} |')
    return '\n'.join(lines)


def fixed_tables(exp):
    out = []
    for f in sorted(exp.glob('fixed_*.json')):
        d = json.loads(f.read_text())
        df = pd.DataFrame(d['rows'])
        out.append(f'\n#### {f.stem}: {d["design"]}; {d["reps"]} field replicates x {d["k"]} subject replays; '
                   f'production winner rate of each subject in the same replicates: {d["production_field_winner_rates"]}\n')
        out.append('| Subject rank | Arm | Win | Δ win (pp) ± SE | Δ top-10 (pp) ± SE | Δ made cut (pp) ± SE | clipped |')
        out.append('|---|---|---|---|---|---|---|')
        for r in df.sort_values(['rank', 'd_win']).itertuples():
            out.append(f'| {r.rank} | {r.arm} | {100 * r.win:.2f}% | {100 * r.d_win:+.2f} ± {100 * r.d_win_se:.2f} | '
                       f'{100 * r.d_top10:+.2f} ± {100 * r.d_top10_se:.2f} | {100 * r.d_made_cut:+.2f} ± '
                       f'{100 * r.d_made_cut_se:.2f} | {r.clipped} |')
    return '\n'.join(out)


def validation_tables(exp):
    out = []
    fixed = {}
    for f in exp.glob('fixed_*.json'):
        d = json.loads(f.read_text())
        for r in d['rows']:
            fixed[(d['event'], r['gid'], r['arm'])] = r
    for f in sorted(exp.glob('events_validation*.json')):
        d = json.loads(f.read_text())
        out.append(f'\n#### {f.stem}: full production events, {d["n"]} paired seeds per arm\n')
        out.append('| Arm | Full: win | Full: Δ win (pp) ± SE | Fixed-field: Δ win (pp) ± SE | |difference| / combined SE | '
                   'Full: made cut | Field totals changed |')
        out.append('|---|---|---|---|---|---|---|')
        for r in d['rows']:
            fx = fixed.get((r['event'], r['gid'], r['arm']))
            if fx:
                diff = abs(r['d_win'] - fx['d_win'])
                comb = np.sqrt((r['d_win_se'] or 0) ** 2 + fx['d_win_se'] ** 2)
                fxs = f'{100 * fx["d_win"]:+.2f} ± {100 * fx["d_win_se"]:.2f}'
                z = f'{diff / comb:.2f}' if comb > 0 else '—'
            else:
                fxs, z = '—', '—'
            out.append(f'| {r["arm"]} | {100 * r["win"]:.2f}% | {100 * r["d_win"]:+.2f} ± {100 * (r["d_win_se"] or 0):.2f} | '
                       f'{fxs} | {z} | {100 * r["made_cut"]:.1f}% | {100 * r["field_changed_share"]:.0f}% |')
    return '\n'.join(out)


def weather_tables(exp):
    f = exp / 'weather_cf.json'
    if not f.exists():
        return ''
    d = json.loads(f.read_text())
    df = pd.DataFrame(d['rows'])
    lines = [f'\n{d["scenarios"]} scenarios x {d["reps"]} paired shot seeds per arm and event; intervals bootstrap the '
             'scenarios (clusters)\n',
             '| Event | Arm | All starters R1-2: Δ strokes/round vs calm [CI] | 36-hole SD | Best entrant wins [CI] | '
             'Winner Overall rank (median) | Same winner as calm [CI] | Win-distribution distance vs calm |',
             '|---|---|---|---|---|---|---|---|']
    for r in df.itertuples():
        ci = getattr(r, 'all_starters_r1r2_vs_calm_ci_scen')
        bw = getattr(r, 'best_entrant_win_ci_scen')
        sw = getattr(r, 'same_winner_ci_scen')
        lines.append(f'| {EV.get(r.event, r.event)} | {r.arm} | {r.all_starters_r1r2_vs_calm:+.2f} [{ci[0]:+.2f}, {ci[1]:+.2f}] | '
                     f'{r.all_starters_36hole_sd:.2f} | {100 * r.best_entrant_win:.1f}% [{100 * bw[0]:.0f}, {100 * bw[1]:.0f}] | '
                     f'{r.winner_overall_rank_median:.0f} | {100 * r.same_winner_as_calm:.0f}% [{100 * sw[0]:.0f}, {100 * sw[1]:.0f}] | '
                     f'{r.tv_distance_win_distribution_vs_calm:.2f} (floor {r.tv_floor_calm_vs_calm_reseeded:.2f}) |')
    adv = pd.DataFrame(d['advantage'])
    keep = ['event', 'arm', 'corr_overall'] + [c for c in adv.columns if c.startswith('corr_') and c != 'corr_overall']
    top = []
    for r in adv.itertuples():
        cs = {c[5:]: getattr(r, c) for c in adv.columns if c.startswith('corr_') and c != 'corr_overall'}
        best = sorted(cs.items(), key=lambda kv: kv[1])[:3]
        top.append(f'| {EV.get(r.event, r.event)} | {r.arm} | {r.corr_overall:+.2f} | ' +
                   ', '.join(f'{k} {v:+.2f}' for k, v in best) + ' |')
    lines += ['\nRelative advantage (correlation across the field of the change in finishing percentile vs calm; negative = '
              'the attribute helps in that weather):\n', '| Event | Arm | Overall | Most helpful attributes |', '|---|---|---|---|'] + top
    return '\n'.join(lines)


def main():
    exp, md = Path(sys.argv[1]), Path(sys.argv[2])
    parts = []
    if (exp / 'rounds_grid.json').exists():
        d = json.loads((exp / 'rounds_grid.json').read_text())
        parts.append('### Tier 1: round scoring (exact production round path)\n' + rounds_tables(d))
    for tag, title in (('rounds_sd', 'Equal-SD perturbations (each attribute +1 Premier/major SD), rank-10 subjects'),):
        if (exp / f'{tag}.json').exists():
            parts.append(f'### {title}\n' + rounds_tables(json.loads((exp / f'{tag}.json').read_text())))
    if (exp / 'rounds_arch.json').exists():
        parts.append('### Fixed-Overall archetype profiles (round scoring)\n' +
                     arch_rounds(json.loads((exp / 'rounds_arch.json').read_text())))
    if list(exp.glob('fixed_*.json')):
        parts.append('### Tier 2: fixed-field conditional estimates (approximation; see validation)\n' + fixed_tables(exp))
    if list(exp.glob('events_validation*.json')):
        parts.append('### Tier 3: full-event validation\n' + validation_tables(exp))
    w = weather_tables(exp)
    if w:
        parts.append('### Weather counterfactuals\n' + w)
    md.write_text('\n\n'.join(parts) + '\n')
    print(md.read_text()[:6000])


if __name__ == '__main__':
    main()
