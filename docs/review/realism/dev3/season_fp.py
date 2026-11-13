"""Played-season fingerprint: a small world under RULES, two seasons with development, winters included.
usage: python season_fp.py ROOT RULES SEED SCALE YEARS"""
import hashlib, sys
sys.path.insert(0, sys.argv[1])
from golfsim.population import generate_world
from golfsim.season import Season
rules, seed, scale, years = sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
s = Season(generate_world(seed=seed, scale=scale, dev_rules=rules), seed=seed, development=True, workers=1)
for y in range(2027, 2027 + years):
    s.run_year(y)
h = hashlib.sha256()
for g in sorted(s.world.golfers, key=lambda g: g.id):
    h.update(repr((g.id, g.name, g.status, g.tour, g.lifestyle, round(g.cash, 4), sorted(g.attrs.items()),
                   sorted(g.ceilings.items()), g.potential, round(s.player_prestige(g.id), 6))).encode())
print(rules, seed, scale, years, len(s.world.golfers), h.hexdigest())
