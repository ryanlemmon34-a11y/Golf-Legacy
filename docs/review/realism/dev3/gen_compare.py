"""Starting worlds dev-2 vs dev-3 over many seeds: top of the world, gaps, saturation, and that every path is kept.
usage: python gen_compare.py ROOT OUT.json SEED..."""
import json, statistics as st, sys
sys.path.insert(0, sys.argv[1])
from golfsim import population as P
out = {}
for seed in map(int, sys.argv[3:]):
    res = {}
    worlds = {r: P.generate_world(seed=seed, dev_rules=r) for r in ('dev-2', 'dev-3')}
    a, b = worlds['dev-2'], worlds['dev-3']
    same = all((x.id, x.name, x.country, x.status, x.tour, x.lifestyle, x.peak_age, x.aging_rate, x.archetype,
                x.personality) == (y.id, y.name, y.country, y.status, y.tour, y.lifestyle, y.peak_age, y.aging_rate,
                                   y.archetype, y.personality) for x, y in zip(a.golfers, b.golfers))
    changed = sum(x.attrs != y.attrs for x, y in zip(a.golfers, b.golfers))
    for r, w in worlds.items():
        top = sorted(w.golfers, key=lambda g: -g.overall)
        res[r] = {'top': [round(g.overall, 2) for g in top[:10]], 'gap12': round(top[0].overall - top[1].overall, 2),
                  'top_age': top[0].age(2027), 'n90': sum(g.overall >= 90 for g in w.golfers),
                  'n95': sum(g.overall >= 95 for g in w.golfers),
                  'attr99_top': sum(v >= 98.95 for v in top[0].attrs.values()),
                  'ceil99_top': sum(v >= 98.95 for v in top[0].ceilings.values()),
                  'attr99_all': sum(v >= 98.95 for g in w.golfers for v in g.attrs.values()),
                  'pot_max': max(g.potential for g in w.golfers)}
    res['paths_same'] = same and len(a.golfers) == len(b.golfers)
    res['golfers_changed'] = changed
    out[seed] = res
    print(seed, res['paths_same'], changed, res['dev-2']['top'][:2], res['dev-3']['top'][:2], flush=True)
json.dump(out, open(sys.argv[2], 'w'))
