"""Fresh full-size world fingerprint (generation + season seeding: fame, rankings) for the code at ROOT.
usage: python fresh_fp.py ROOT SEED..."""
import hashlib, sys
sys.path.insert(0, sys.argv[1])
from golfsim.population import generate_world
from golfsim.season import Season
for seed in map(int, sys.argv[2:]):
    w = generate_world(seed=seed, year=2027)
    h = hashlib.sha256()
    for g in w.golfers:
        h.update(repr((g.id, g.name, g.country, g.status, g.tour, g.lifestyle, g.potential, sorted(g.attrs.items()),
                       sorted(g.ceilings.items()), round(g.cash, 4), round(g.backing, 4), g.peak_age, g.aging_rate)).encode())
    gen = h.hexdigest()
    s = Season(w, seed=seed, workers=1)
    h2 = hashlib.sha256()
    for g in sorted(s.world.golfers, key=lambda g: g.id):
        h2.update(repr((g.id, [round(v, 6) for _, v in s.fame_log.get(g.id, [])], round(s.player_prestige(g.id), 6))).encode())
    top = max(w.golfers, key=lambda g: g.overall)
    print(seed, w.dev_rules, 'generation', gen[:16], 'seeding', h2.hexdigest()[:16], f'#1 {top.name} {top.overall:.2f} ${top.cash/1e6:.1f}M')
