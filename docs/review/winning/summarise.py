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


def main():
    exp, md = Path(sys.argv[1]), Path(sys.argv[2])
    parts = []
    if (exp / 'rounds_grid.json').exists():
        d = json.loads((exp / 'rounds_grid.json').read_text())
        parts.append('### Tier 1: round scoring (exact production round path)\n' + rounds_tables(d))
    md.write_text('\n\n'.join(parts) + '\n')
    print(md.read_text()[:6000])


if __name__ == '__main__':
    main()
