"""Junior classes dev-2 vs dev-3 (same seeds and years) and controlled projections of the elite juniors to 50.
Projection = the production develop_week/age_year on measure.py's fixed schedule: NOT a played career.
usage: python junior_proj.py ROOT OUT.json SEEDS(comma) Y0 Y1"""
import copy, json, random, sys
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[1] + '/docs/review/realism')
from golfsim import population as P, development as D
from golfsim.nations import nations
from measure import project, ident
seeds = [int(s) for s in sys.argv[3].split(',')]
y0, y1 = int(sys.argv[4]), int(sys.argv[5])
prof = nations()
out = {'classes': [], 'elite': []}
for seed in seeds:
    for year in range(y0, y1 + 1):
        built = {}
        for r in ('dev-2', 'dev-3'):
            js = P.junior_class(year, seed, prof, 1, set(), rules=r)
            rng = random.Random(f'{seed}:juniors:{year}')
            for g in js:
                D.init_ceilings(g, 18, rng); rng.random(); rng.random(); rng.random()
            built[r] = js
        a, b = built['dev-2'], built['dev-3']
        same = [(x.id, x.name, x.country, x.tour, x.peak_age, x.aging_rate) for x in a] == \
               [(x.id, x.name, x.country, x.tour, x.peak_age, x.aging_rate) for x in b]
        out['classes'].append([seed, year, len(a), same, sum(x.attrs != y.attrs for x, y in zip(a, b)),
                               sorted((round(x.overall, 2) for x in a), reverse=True)[:3],
                               sorted((round(x.overall, 2) for x in b), reverse=True)[:3]])
        for x, y in zip(a, b):
            if x.potential < 84:
                continue
            rec = {'seed': seed, 'year': year, 'id': x.id, 'peak_age': x.peak_age, 'aging': x.aging_rate}
            for r, g in (('dev-2', x), ('dev-3', y)):
                g = copy.deepcopy(g)
                e = dict(entry=round(g.overall, 2), pot=g.potential,
                         ceil99=sum(v >= 98.95 for v in g.ceilings.values()))
                traj = project(g, r, f'{seed}:{year}:{x.id}')
                e['traj'] = [round(traj[a], 2) for a in range(18, 51)]
                e['attr99_50'] = sum(v >= 98.95 for v in g.attrs.values())
                rec[r] = e
            out['elite'].append(rec)
    print(seed, len(out['elite']), flush=True)
json.dump(out, open(sys.argv[2], 'w'))
