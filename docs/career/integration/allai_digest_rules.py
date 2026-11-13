"""The career fixture's all-AI digests (tests/career_fixture.py procedure, copied) for the code at ROOT.
usage: python allai_digest.py ROOT"""
import hashlib, shutil, sys, tempfile
from pathlib import Path
ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT))
from golfsim.population import generate_world
from golfsim.session import Session

def digest(session):
    s = session.season
    h = hashlib.sha256()
    for g in sorted(s.world.golfers, key=lambda g: g.id):
        c = s.staff.coach(g.id); k = s.staff.caddie(g.id)
        h.update(repr((g.id, g.name, g.status, g.tour, g.lifestyle, round(g.overall, 6),
                       tuple(round(v, 6) for _, v in sorted(g.attrs.items())), round(g.cash, 4), round(g.backing, 4),
                       c.id if c else None, k.id if k else None)).encode())
    for eid in sorted(s.results):
        h.update(repr((eid, s.results[eid].winner())).encode())
    year, week = session.cursor['year'], session.cursor['week']
    h.update(repr(s.ctx.ranking(year, max(1, week - 1))[:100]).encode())
    h.update(repr(sorted(session.cursor.items())).encode())
    return h.hexdigest()

d = Path(tempfile.mkdtemp(prefix='allai_')) / 'w'
s = Session.create(d, seed=11, world=generate_world(year=2027, seed=11, scale=0.05, dev_rules=sys.argv[2]), workers=1)
print('rules', s.season.dev_rules)
s.advance(52); s.close()
s = Session.open(d)
a = digest(s)
for _ in range(12):
    s.advance_one_week(expected=s.cursor)
b = digest(s)
print(ROOT.name, 'SEASON1', a); print(ROOT.name, '2028_W12', b)
print('career', getattr(s.season, 'career', 'n/a'))
s.close()
