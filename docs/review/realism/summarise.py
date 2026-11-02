"""Tables for docs/review/realism/RESULTS.md from measure.py's output. Usage: python summarise.py M.json > OUT.md"""
from __future__ import annotations

import json
import statistics as S
import sys
from collections import defaultdict

ARMS = ('A0', 'R', 'G', 'B')
NAMES = {'A0': 'A0 dev-1', 'R': 'R readiness only', 'G': 'G aging only', 'B': 'B dev-2 (both)'}


def q(xs, p):
    xs = sorted(xs)
    if not xs:
        return float('nan')
    i = min(len(xs) - 1, max(0, int(round(p * (len(xs) - 1)))))
    return xs[i]


def wq(pairs, p):
    """Weighted quantile of (value, weight) pairs."""
    pairs = sorted(pairs)
    tot = sum(w for _, w in pairs)
    acc = 0.0
    for v, w in pairs:
        acc += w
        if acc >= p * tot:
            return v
    return pairs[-1][0] if pairs else float('nan')


def main(path):
    d = json.load(open(path))
    res = d['results']
    n_seeds = len(d['seeds'])
    out = []
    p = out.append
    p(f"Seeds {d['seeds']}, junior classes {d['years'][0]}-{d['years'][1]} ({len(res)} cohorts), "
      f"projection to age {d['to_age']}; run {d['seconds']} s.\n")
    # ---- layer 1: cohorts
    same_n = same_id = same_np = same_np_entry = 0
    pot_diff = 0
    ent = {'dev-1': [], 'dev-2': []}
    head80 = {'dev-1': [], 'dev-2': []}
    head_all = {'dev-1': [], 'dev-2': []}
    changed = []
    for r in res:
        a, b = r['rows']['dev-1'], r['rows']['dev-2']
        same_n += len(a['juniors']) == len(b['juniors'])
        ida = [x[:4] + x[5:] for x in a['juniors']]
        idb = [x[:4] + x[5:] for x in b['juniors']]
        same_id += ida == idb
        pot_diff = max(pot_diff, max((abs(x[4] - y[4]) for x, y in zip(a['juniors'], b['juniors'])), default=0))
        same_np += a['new_pros'] == b['new_pros']
        same_np_entry += a['np_entry'] == b['np_entry']
        for rules, rr in (('dev-1', a), ('dev-2', b)):
            for row, e in zip(rr['juniors'], rr['entry']):
                pot = row[4]
                ent[rules].append(e)
                head_all[rules].append(pot - e)
                if pot >= 80:
                    head80[rules].append(pot - e)
        changed += [y - x for x, y in zip(a['entry'], b['entry'])]
    N = len(res)
    p('## Layer 1: cohorts (production junior_class / new_professionals, both rules)\n')
    p(f'- Junior class counts equal in {same_n}/{N} cohorts; identities (id, name, nation, birth year, peak age, aging '
      f'rate, archetype, path, status, personality) equal in {same_id}/{N}; largest stored-potential difference '
      f'{pot_diff:.1f} (rounding where the entry level had been at potential).')
    p(f'- New professionals: identical rows in {same_np}/{N} cohorts and identical entry Overall in {same_np_entry}/{N}.')
    p(f'- Entry Overall changed for {sum(1 for c in changed if c < -0.05)} of {len(changed)} juniors '
      f'({100 * sum(1 for c in changed if c < -0.05) / len(changed):.1f}%) by more than 0.05; mean change '
      f'{S.mean(changed):+.3f}, median {S.median(changed):+.3f}, largest {min(changed):+.2f}.\n')
    p('| juniors | per seed | mean entry | 99th pct | max | 75+ /seed | 80+ /seed | 85+ /seed | 90+ /seed | '
      'headroom pot 80+: median | p10 | share < 3 | share < 5 | all juniors: share headroom < 3 | < 5 |')
    p('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for rules in ('dev-1', 'dev-2'):
        e = ent[rules]
        h = head80[rules]
        ha = head_all[rules]
        p(f'| {rules} | {len(e) / n_seeds:.0f} | {S.mean(e):.2f} | {q(e, .99):.2f} | {max(e):.2f} | '
          + ' | '.join(f'{sum(1 for x in e if x >= t) / n_seeds:.1f}' for t in (75, 80, 85, 90))
          + f' | {S.median(h):.2f} | {q(h, .1):.2f} | {100 * sum(1 for x in h if x < 3) / len(h):.1f}% | '
          f'{100 * sum(1 for x in h if x < 5) / len(h):.1f}% | {100 * sum(1 for x in ha if x < 3) / len(ha):.2f}% | '
          f'{100 * sum(1 for x in ha if x < 5) / len(ha):.2f}% |')
    # ---- layer 2: projections
    recs = [(r['seed'], x) for r in res for x in r['proj']]
    p('\n## Layer 2: controlled projections (same candidates, same schedule; not realized careers)\n')
    bands = (('pot < 60 (20% sample, x5)', 0, 60), ('60-70', 60, 70), ('70-80', 70, 80), ('80-90', 80, 90),
             ('90+', 90, 101))
    p('Median projected Overall by age (10th-90th percentile) per potential band.\n')
    show = (18, 21, 25, 30, 35, 40, 45, 50)
    p('| band | n | arm | ' + ' | '.join(str(a) for a in show) + ' | age at max: median (p10-p90) |')
    p('|---|---|---|' + '---|' * (len(show) + 1))
    for name, lo, hi in bands:
        grp = [x for _, x in recs if lo <= x['pot'] < hi]
        for arm in ARMS:
            cells = []
            for a in show:
                v = [x[arm][a - 18] for x in grp]
                cells.append(f'{S.median(v):.1f} ({q(v, .1):.1f}-{q(v, .9):.1f})')
            amax = [18 + max(range(len(x[arm])), key=lambda i: x[arm][i]) for x in grp]
            p(f'| {name} | {len(grp)} | {arm} | ' + ' | '.join(cells)
              + f' | {S.median(amax):.0f} ({q(amax, .1):.0f}-{q(amax, .9):.0f}) |')
    p('\nElite supply and longevity, per seed (weighted: the 20% sample counts x5).\n')
    p('| arm | reach 75+ | reach 80+ | reach 85+ | reach 90+ | golfer-years 80+ | 85+ | 90+ | 85+ reached by 23 '
      '| first 85+: median age | last 85+: median age (p90) | last 80+: median age (p90) | years at 85+ per 85+ golfer '
      '| age at max, 80+ golfers: median (p10-p90) |')
    p('|---|' + '---|' * 14)
    for arm in ARMS:
        reach = {t: 0.0 for t in (75, 80, 85, 90)}
        yrs = {t: 0.0 for t in (80, 85, 90)}
        early85 = 0.0
        first85, last85, last80, y85, amax80 = [], [], [], [], []
        for _, x in recs:
            tr, w = x[arm], x['w']
            for t in reach:
                if max(tr) >= t:
                    reach[t] += w
            for t in yrs:
                yrs[t] += w * sum(1 for v in tr if v >= t)
            if max(tr) >= 85:
                ages85 = [18 + i for i, v in enumerate(tr) if v >= 85]
                first85.append((ages85[0], w)); last85.append((ages85[-1], w)); y85.append((len(ages85), w))
                early85 += w * (ages85[0] <= 23)
            if max(tr) >= 80:
                ages80 = [18 + i for i, v in enumerate(tr) if v >= 80]
                last80.append((ages80[-1], w))
                amax80.append((18 + max(range(len(tr)), key=lambda i: tr[i]), w))
        p(f'| {NAMES[arm]} | ' + ' | '.join(f'{reach[t] / n_seeds:.1f}' for t in reach) + ' | '
          + ' | '.join(f'{yrs[t] / n_seeds:.1f}' for t in yrs)
          + f' | {early85 / n_seeds:.1f} | {wq(first85, .5)} | {wq(last85, .5)} ({wq(last85, .9)}) | '
          f'{wq(last80, .5)} ({wq(last80, .9)}) | {sum(v * w for v, w in y85) / max(1e-9, sum(w for _, w in y85)):.1f} '
          f'| {wq(amax80, .5)} ({wq(amax80, .1)}-{wq(amax80, .9)}) |')
    # decline from own max
    p('\nDecline from the projected maximum, golfers whose maximum is 70+ (median; by aging-rate tercile).\n')
    p('Cliff check: each golfer\'s own largest one-year loss before 50, then its 99th percentile and maximum across '
      'golfers (a rare severe drop cannot hide among ordinary years); the pooled 99th percentile of every annual '
      'change is shown separately.\n')
    p('| arm | aging rate | n | max | max to 40 | max to 45 | max to 50 | Overall at 45: p90 | per-golfer largest '
      'one-year loss before 50: p99 across golfers | largest of all | pooled annual losses: p99 |')
    p('|---|---|---|---|---|---|---|---|---|---|---|')
    top = [x for _, x in recs if max(x['A0']) >= 70]
    rates = sorted(x['aging'] for x in top)
    cuts = (rates[len(rates) // 3], rates[2 * len(rates) // 3])
    for arm in ARMS:
        for tname, f in (('low (< %.2f)' % cuts[0], lambda r: r < cuts[0]),
                         ('mid', lambda r: cuts[0] <= r < cuts[1]), ('high (>= %.2f)' % cuts[1], lambda r: r >= cuts[1])):
            grp = [x for x in top if f(x['aging'])]
            mx = [max(x[arm]) for x in grp]
            d40 = [x[arm][40 - 18] - max(x[arm][:40 - 18 + 1]) for x in grp]
            d45 = [x[arm][45 - 18] - max(x[arm][:45 - 18 + 1]) for x in grp]
            d50 = [x[arm][50 - 18] - max(x[arm]) for x in grp]
            o45 = [x[arm][45 - 18] for x in grp]
            drops = [x[arm][i] - x[arm][i + 1] for x in grp for i in range(len(x[arm]) - 1)]   # ages 18-49 -> 19-50
            own = [max(x[arm][i] - x[arm][i + 1] for i in range(len(x[arm]) - 1)) for x in grp]
            p(f'| {arm} | {tname} | {len(grp)} | {S.median(mx):.1f} | {S.median(d40):+.1f} | {S.median(d45):+.1f} | '
              f'{S.median(d50):+.1f} | {q(o45, .9):.1f} | {q(own, .99):.2f} | {max(own):.2f} | {q(drops, .99):.2f} |')
    # rare careers
    p('\nRare careers (each golfer listed, all four arms: Overall at 18 / 20 / 23 / 27 / 35 / 40 / 45, max at age).\n')
    rare = [(s, x) for s, x in recs if x['pot'] >= 92 or (x['pot'] >= 80 and x['aging'] <= 0.62)
            or (x['pot'] >= 82 and x['peak'] >= 30.5)]
    p('| seed | id | potential | peak age | aging | kind | ' + ' | '.join(ARMS) + ' |')
    p('|---|---|---|---|---|---|' + '---|' * len(ARMS))
    for s, x in sorted(rare, key=lambda t: -t[1]['pot'])[:40]:
        kind = 'prodigy' if x['pot'] >= 92 else 'slow ager' if x['aging'] <= 0.62 else 'late peak'
        cells = []
        for arm in ARMS:
            tr = x[arm]
            i = max(range(len(tr)), key=lambda k: tr[k])
            cells.append('/'.join(f'{tr[a - 18]:.0f}' for a in (18, 20, 23, 27, 35, 40, 45)) + f'; {tr[i]:.1f}@{18 + i}')
        p(f"| {s} | {x['id']} | {x['pot']:.1f} | {x['peak']:.1f} | {x['aging']:.2f} | {kind} | " + ' | '.join(cells) + ' |')
    print('\n'.join(out))


if __name__ == '__main__':
    main(sys.argv[1])
