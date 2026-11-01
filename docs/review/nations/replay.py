"""Fixed-input replay of national prestige on the Test2 world (seed 386509): the archived actual and expected fame
(A, E) of every nation and season, plus the fame on offer in its starts (P, recomputed from the archived finishes,
ability ignored), are held fixed; national prestige, multipliers and shares are worked out under the earlier rule
(R alone) and under rules 2026-11-14 (2/3 Q + 1/3 R). Nothing is simulated: the same results feed both rules, so
this isolates the measure, not what a re-simulated world would do.

    python3 -I replay.py <checkout> <tests/data/test2_nation_shares.json.gz> <test2_fame_by.json.gz> <out.md>
"""
import gzip
import json
import math
import sys

sys.path.insert(0, sys.argv[1])
from golfsim import participation as PT  # noqa: E402

fx = json.load(gzip.open(sys.argv[2], 'rt'))
fame = json.load(gzip.open(sys.argv[3], 'rt'))
OUT = sys.argv[4]
base = fx['baseline_shares']['juniors']
nations = sorted(base)
years = sorted(int(y) for y in fame)                       # decided seasons 2027..2083


def season(c, y):
    """(A, E, P) of nation c in season y; A and E as archived, P recomputed."""
    rec = fx['years'].get(str(y + 1), {}).get('season', {}).get(c)
    a, e = (rec[0], rec[1]) if rec else (0.0, 0.0)
    p = fame.get(str(y), {}).get(c, {}).get('P', 0.0)
    return a, e, p


def replay(rule, mutate=None):
    mult = {c: 1.0 for c in nations}
    out = {}
    for y in years:
        row = {}
        for c in nations:
            win = []
            for k in range(PT.NATION_YEARS):
                if y - k < years[0]:
                    break
                s = season(c, y - k)
                if mutate:
                    s = mutate(c, y - k, s)
                win.append(s)
            if rule == 'old':
                pr, r = PT.nation_prestige([s[:2] for s in win])
                q = None
            else:
                pr, r, q = PT.nation_prestige_achievement(win)
            mult[c] = PT.next_multiplier(mult[c], pr)
            row[c] = {'prestige': pr, 'r': r, 'q': q, 'mult': mult[c]}
        tot = sum(base[c] * row[c]['mult'] for c in nations)
        for c in nations:
            row[c]['share'] = base[c] * row[c]['mult'] / tot
        out[y] = row
    return out


old, new = replay('old'), replay('new')
L = ['# National prestige: fixed-input replay, R alone (before) and 2/3 Q + 1/3 R (rules 2026-11-14)', '',
     'Inputs held fixed: every nation-season\'s archived actual and expected fame (A, E) and the fame on offer in its '
     'starts (P: each site\'s fame split evenly among its starters, ability ignored), recomputed from the archived '
     'finishes. Shares are the juniors\' (starting share x multiplier, normalised). A re-simulated world would also '
     'change the results; this isolates the measure. Weights are provisional.', '']

# 1. validation
d = []
for y in years:
    arch = fx['years'].get(str(y + 1), {}).get('prestige', {})
    for c in nations:
        if c in arch:
            d.append(abs(old[y][c]['prestige'] - arch[c]))
L += ['## 1. The "before" replay reproduces the archive', '',
      f'Old-rule prestige against the archived prestige, {len(d)} nation-seasons: largest difference {max(d):.3f} '
      f'(rounding of the archived A and E), mean {sum(d) / len(d):.4f}.', '']

# 2. Argentina
L += ['## 2. Argentina, 2040-2083', '',
      '| season | majors | A | E | P | R (5 yr) | Q (5 yr) | prestige before | prestige now | of which Q part | R part | multiplier before | now | juniors share before | now |',
      '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
W = PT.ACHIEVEMENT_WEIGHT
for y in range(2040, 2084):
    if y not in old:
        continue
    a, e, p = season('Argentina', y)
    o, n = old[y]['Argentina'], new[y]['Argentina']
    mj = fame.get(str(y), {}).get('Argentina', {}).get('wins', {}).get('major', 0)
    L.append(f'| {y} | {mj} | {a:.1f} | {e:.1f} | {p:.1f} | {o["r"]:.3f} | {n["q"]:.3f} | {o["prestige"]:.1f} | '
             f'{n["prestige"]:.1f} | {25 * W * math.log2(n["q"]):+.1f} | {25 * (1 - W) * math.log2(n["r"]):+.1f} | '
             f'{o["mult"]:.3f} | {n["mult"]:.3f} | {100 * o["share"]:.2f}% | {100 * n["share"]:.2f}% |')
L.append('')

# 3. decomposition and counterfactuals for Argentina 2055
by = fame['2055']['Argentina']['by']
am, pm = by.get('major', [0, 0, 0])[:2]
L += ['## 3. Argentina 2055: what the four majors contribute, and lower-tier volume', '',
      f'Season 2055 alone: A {season("Argentina", 2055)[0]:.2f}, P {season("Argentina", 2055)[2]:.2f}; from the majors '
      f'A {am:.2f} against P {pm:.2f}; by class (A / P / starts): '
      + '; '.join(f'{k} {v[0]:.1f} / {v[1]:.1f} / {v[2]}' for k, v in sorted(by.items())) + '.', '']


def no_majors(c, y, s):
    if c == 'Argentina' and y == 2055:
        a, e, p = s
        return a - am, e, p - pm                     # (E unchanged: the expectation was set before the events)
    return s


def neutral_lower(x):
    def f(c, y, s):
        if c != 'Argentina':
            return s
        b = fame.get(str(y), {}).get('Argentina', {}).get('by', {})
        lo = b.get('tier5_8', [0, 0])[1] + b.get('tier2_4', [0, 0])[1]
        a, e, p = s
        return a + x * lo, e + x * lo, p + x * lo   # x times more lower-tier fame on offer, won at an even share
    return f


L += ['| case (2055 window) | Q | R | prestige now | prestige before |', '|---|---|---|---|---|']
for label, m in (('as played', None), ('without the four majors\' fame (counterfactual)', no_majors),
                 ('+1x neutral lower-tier entries (won at an even share)', neutral_lower(1)),
                 ('+2x neutral lower-tier entries', neutral_lower(2)), ('+5x neutral lower-tier entries', neutral_lower(5))):
    n, o = replay('new', m)[2055]['Argentina'], replay('old', m)[2055]['Argentina']
    L.append(f'| {label} | {n["q"]:.3f} | {n["r"]:.3f} | {n["prestige"]:.1f} | {o["prestige"]:.1f} |')
L += ['', 'Lower-tier starts won at an even share are neutral in themselves but dilute Q toward 1 (they add to the fame '
      'and to the fame on offer alike); the majors\' fame still dominates because a major carries prestige cubed.', '']

# 4. breakthroughs: a major or Premier win by a nation with few starts
L += ['## 4. Small breakthroughs (a major or tier-1 win from fewer than 1,500 starts that season)', '',
      '| season | nation | starts | majors | tier-1 wins | prestige before (that season) | now |', '|---|---|---|---|---|---|---|']
rows = []
for y in years:
    for c, b in fame.get(str(y), {}).items():
        if c not in nations:
            continue
        w = b.get('wins', {})
        if (w.get('major', 0) or w.get('tier1', 0)) and b['starts'] < 1500:
            rows.append((y, c, b['starts'], w.get('major', 0), w.get('tier1', 0)))
for y, c, st, mj, t1 in rows[:40]:
    L.append(f'| {y} | {c} | {st} | {mj} | {t1} | {old[y][c]["prestige"]:.1f} | {new[y][c]["prestige"]:.1f} |')
L.append(f'\n{len(rows)} such nation-seasons in all (first 40 shown).\n')

# 5. concentration, bounds and declines
def summary(rep, label):
    caps = sum(1 for y in years for c in nations if rep[y][c]['mult'] >= PT.MULT_MAX - 1e-9)
    floors = sum(1 for y in years for c in nations if rep[y][c]['mult'] <= PT.MULT_MIN + 1e-9)
    last = rep[years[-1]]
    top5 = sorted(nations, key=lambda c: -last[c]['share'])[:5]
    low = sum(1 for c in nations if last[c]['prestige'] < 45)
    return (f'| {label} | {100 * last["USA"]["share"]:.2f}% | {max(100 * rep[y]["USA"]["share"] for y in years):.2f}% | '
            f'{100 * sum(last[c]["share"] for c in top5):.1f}% ({", ".join(top5)}) | {caps} | {floors} | '
            f'{min(last[c]["mult"] for c in nations):.3f}-{max(last[c]["mult"] for c in nations):.3f} | {low} |')


L += ['## 5. Concentration, bounds and ordinary declines', '',
      f'USA starting juniors share: {100 * base["USA"]:.2f}%.', '',
      '| rule | USA share 2084 | USA share max | top-5 share 2084 | nation-seasons at the 4x cap | at the 0.25x floor | multipliers 2084 | nations below 45 in 2084 |',
      '|---|---|---|---|---|---|---|---|', summary(old, 'before (R alone)'), summary(new, 'now (2/3 Q + 1/3 R)'), '']

# 6. sustained success and fade-out: Argentina after its last major
last_major = max((y for y in years if fame.get(str(y), {}).get('Argentina', {}).get('wins', {}).get('major')),
                 default=None)
if last_major:
    L += [f'## 6. Fade-out: Argentina\'s last major in this world was in {last_major}', '',
          '| season | prestige before | now | multiplier now |', '|---|---|---|---|']
    for y in range(last_major, min(years[-1], last_major + 10) + 1):
        L.append(f'| {y} | {old[y]["Argentina"]["prestige"]:.1f} | {new[y]["Argentina"]["prestige"]:.1f} | '
                 f'{new[y]["Argentina"]["mult"]:.3f} |')
    L.append('')
open(OUT, 'w').write('\n'.join(L) + '\n')
print('written', OUT)
