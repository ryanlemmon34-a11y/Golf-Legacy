"""Fingerprint of generation and aging under given rules, for a repo root. usage: python dev2_fingerprint.py ROOT RULES"""
import hashlib, random, sys
sys.path.insert(0, sys.argv[1])
from golfsim import population as P, development as D
from golfsim.nations import nations
rules = sys.argv[2]
h = hashlib.sha256()
def eat(g):
    h.update(repr((g.id, g.name, g.country, g.status, g.tour, g.potential, sorted(g.attrs.items()),
                   sorted(g.ceilings.items()), round(g.cash, 6), g.lifestyle)).encode())
for seed in (416342, 2027, 11):
    w = P.generate_world(seed=seed, dev_rules=rules)
    for g in w.golfers: eat(g)
    rng = random.Random(1)
    for g in w.golfers[:3000]:
        for age in range(g.age(2027), g.age(2027) + 15):
            D.age_year(g, age + 1, rng, 0.8, rules=rules)
        eat(g)
for seed, year in ((416342, 2040), (7, 2031), (11, 2044)):
    for fn in (P.junior_class, P.new_professionals):
        gs = fn(year, seed, nations(), 1, set(), rules=rules)
        r = random.Random(3)
        for g in gs:
            D.init_ceilings(g, g.age(year), r); eat(g)
print(rules, h.hexdigest())
