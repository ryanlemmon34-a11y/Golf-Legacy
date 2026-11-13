import json, sys
def load(p):
    d = json.load(open(p)); d['season'] = {int(k): v for k, v in d['season'].items()}; return d
A, B = load(sys.argv[1]), load(sys.argv[2])
years = sorted(set(A['season']) & set(B['season']))
for lab, d in (('Test3 dev-2', A), ('dev-3 run', B)):
    print('==', lab)
    for y in years:
        s = sorted(((v[0], g) for g, v in d['season'][y].items()), reverse=True)
        n = d['names']
        print(f'  {y} #1 {n[s[0][1]]} {s[0][0]:.1f} ({d["season"][y][s[0][1]][2]} attrs@99) #2 {n[s[1][1]]} {s[1][0]:.1f} gap {s[0][0]-s[1][0]:.2f} #10 {s[9][0]:.1f} n>=90 {sum(v>=90 for v,_ in s)}')
    maj = [(y, w) for y, _, w in d['majors'] if y in years]
    from collections import Counter
    c = Counter(d['names'][str(w)] for _, w in maj)
    ages = [y - d['born'][str(w)] for y, w in maj]
    print('  majors', len(maj), 'winners', c.most_common(5), 'mean age %.1f' % (sum(ages) / len(ages)))
    prem = [w for y, _, w, cat in d['premier_wins'] if y in years and w]
    print('  Premier-tier wins by most frequent winners', Counter(d['names'][str(w)] for w in prem).most_common(3))
