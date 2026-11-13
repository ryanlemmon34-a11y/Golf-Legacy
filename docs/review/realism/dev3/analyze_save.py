"""Analyse an extract (extract_save.py): top-of-world snapshots, gaps, juniors, major winners.
usage: python -I analyze_save.py EXTRACT.json"""
import json
import statistics as st
import sys
from collections import Counter, defaultdict

d = json.load(open(sys.argv[1]))
born = d['born']
names = d['names']
seasons = {int(k): v for k, v in d['season'].items()}
years = sorted(seasons)

print('== annual snapshots (end-of-season Overall, every golfer with a career row) ==')
gaps, gaps12, tops = [], [], Counter()
for y in years:
    s = sorted(((v[0], g) for g, v in seasons[y].items()), reverse=True)
    (a, ga), (b, gb), (c, gc) = s[:3]
    gaps.append(a - b)
    tops[ga] += 1
    n99 = seasons[y][ga][2]
    if y % 3 == 0 or y < 2030:
        print(y, f'#1 {names[ga]} ({y - born[ga]}) {a:.1f} [{n99} attrs at 99]  #2 {names[gb]} {b:.1f}  gap {a - b:.2f}  #10 {s[9][0]:.1f}  n>=90 {sum(1 for v, _ in s if v >= 90)}')
print('gap #1-#2: median %.2f mean %.2f max %.2f; years with gap>3: %d of %d' % (
    st.median(gaps), st.mean(gaps), max(gaps), sum(g > 3 for g in gaps), len(gaps)))
print('most years at #1:', [(names[g], n) for g, n in tops.most_common(5)])

print('\n== majors ==')
wins = Counter(w for _, _, w in d['majors'] if w)
ages = [y - born[str(w)] for y, _, w in d['majors'] if w]
print('majors', len(d['majors']), 'mean winner age %.2f' % st.mean(ages))
print('top major winners', [(names[str(g)], n) for g, n in wins.most_common(6)])
print('winners aged <=21: %d, >=40: %d, >=45: %d' % (sum(a <= 21 for a in ages), sum(a >= 40 for a in ages),
                                                    sum(a >= 45 for a in ages)))

print('\n== juniors created (path junior, age 18) ==')
cr = {g: c for g, c in d['created'].items() if c.get('path') == 'junior'}
print('juniors with diagnostics:', len(cr))
pots = sorted(((c['potential'], c['overall'], g, c['year']) for g, c in cr.items()), reverse=True)
for p, o, g, y in pots[:12]:
    peak = max((seasons[yy][g][0] for yy in years if g in seasons[yy]), default=None)
    print(f'  pot {p:.1f} entry {o:.2f} {names[g]} {y} peak {peak}')
print('pot>=90: %d  >=95: %d  ==99: %d' % (sum(p >= 90 for p, *_ in pots), sum(p >= 95 for p, *_ in pots),
                                           sum(p >= 99 for p, *_ in pots)))
# first-season rating
first = []
for g, c in cr.items():
    y = c['year']
    if y in seasons and g in seasons[y]:
        first.append((seasons[y][g][0], g))
first.sort(reverse=True)
print('best end-of-first-season ratings:', [(round(v, 1), names[g]) for v, g in first[:5]])
