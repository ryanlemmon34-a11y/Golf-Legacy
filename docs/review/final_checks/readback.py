"""Focused saved-state readback for the nation rules (a continuation of FRESH_AB, which read in-memory history only):
a fresh full-population world on the final integration build, played through WINTERS winters, then
  1. the golfers actually generated each winter, counted by pathway and nationality, against the allocation recorded
     (totals and every nation), and against juniors_added / new_pros_added;
  2. the saved state reopened (Session.open) -- nation flags, prestige, multipliers, achievement, carry and history
     equal to what the running session held;
  3. the archive read back (Archive.year(y)['prestige']['nations']) -- achievement, carry and the rules block present
     and equal to the session's history (or absent / false in the 'off' arm).
    python3 readback.py CHECKOUT WORLD_DIR SEED WINTERS ARM OUT.json      (ARM: on | off)"""
import json, sys
from collections import Counter
from pathlib import Path
code, wdir, seed, winters, arm, out = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], sys.argv[6]
sys.path.insert(0, code)
from golfsim.session import Session
from golfsim.archive import Archive

res = {'code': code, 'seed': seed, 'arm': arm, 'winters': winters, 'checks': {}, 'problems': []}
bad = res['problems'].append
s = Session.create(wdir, seed=seed, workers=4)
if arm == 'off':
    pt = s.season.participation
    assert not any(h.get('allocated') for h in pt.history.values())
    pt.carry_on, pt.achievement_on = False, False
s.advance(53 + 52 * (winters - 1))                       # through WINTERS winters
se, pt = s.season, s.season.participation
by_id = {g.id: g for g in se.world.golfers}
years = sorted(y for y, h in pt.history.items() if h.get('allocated'))
recon = {}
for E in years:
    h = pt.history[E]
    made = se.creations.get(E, {})
    for kind, path, added in (('juniors', 'junior', se.juniors_added), ('new_pros', 'late_entrant', se.new_pros_added)):
        got = Counter(by_id[gid].country for gid, c in made.items() if c['path'] == path)
        alloc = {c: n for c, n in h['allocated'].get(kind, {}).items() if n}
        ok = (dict(got) == alloc and sum(got.values()) == h['totals'].get(kind) == added.get(E))
        recon[f'{E} {kind}'] = {'generated': sum(got.values()), 'allocated': sum(alloc.values()),
                                'total': h['totals'].get(kind), 'added': added.get(E), 'by_nation_equal': dict(got) == alloc}
        if not ok:
            bad(f'reconciliation {E} {kind}: generated {dict(got)} vs allocated {alloc}')
res['checks']['generated_vs_allocated'] = recon
held = {'carry_on': pt.carry_on, 'achievement_on': pt.achievement_on, 'prestige': dict(pt.prestige),
        'multiplier': dict(pt.multiplier), 'achievement': dict(getattr(pt, 'achievement', {})),
        'carry': json.loads(json.dumps(getattr(pt, 'carry', {}))), 'history': json.loads(json.dumps(pt.history, default=str))}
cursor = s.cursor
s.close()

again = Session.open(wdir, workers=1)                    # 2. the saved state
p2 = again.season.participation
re = {'carry_on': p2.carry_on, 'achievement_on': p2.achievement_on, 'prestige': dict(p2.prestige),
      'multiplier': dict(p2.multiplier), 'achievement': dict(getattr(p2, 'achievement', {})),
      'carry': json.loads(json.dumps(getattr(p2, 'carry', {}))), 'history': json.loads(json.dumps(p2.history, default=str))}
res['checks']['reopen'] = {k: held[k] == re[k] for k in held}
res['checks']['reopen_cursor'] = [cursor, again.cursor]
for k, v in res['checks']['reopen'].items():
    if not v:
        bad(f'reopen: {k} differs')
if (p2.carry_on, p2.achievement_on) != ((arm == 'on'),) * 2:
    bad(f'flags after reopen: {(p2.carry_on, p2.achievement_on)}')
again.close()

a = Archive(wdir / 'archive')                             # 3. the archive
arch = {}
for y in a.years:
    n = (a.year(y).get('prestige') or {}).get('nations') or {}
    h = held['history'].get(str(y + 1)) or held['history'].get(y + 1) or {}
    rules = n.get('rules') or {}
    row = {'has_achievement': 'achievement' in n, 'has_carry': 'carry' in n, 'rules': rules,
           'prestige_equal': n.get('prestige') == h.get('prestige'),
           'achievement_equal': n.get('achievement') == h.get('achievement'),
           'carry_equal': n.get('carry') == h.get('carry'),
           'allocated_equal': n.get('allocated') == h.get('allocated')}
    arch[y] = row
    want = arm == 'on'
    if rules.get('achievement') is not want or rules.get('carry') is not want:
        bad(f'archive {y}: rules {rules}')
    if want and not (row['has_achievement'] and row['has_carry'] and row['achievement_equal'] and row['carry_equal']):
        bad(f'archive {y}: achievement/carry missing or different')
    if not want and row['has_achievement']:
        bad(f'archive {y}: achievement present in the off arm')
    if not (row['prestige_equal'] and row['allocated_equal']):
        bad(f'archive {y}: prestige/allocated differ from the session history')
res['checks']['archive'] = arch
a.close()
res['ok'] = not res['problems']
Path(out).write_text(json.dumps(res, indent=1, default=str))
print(json.dumps({k: res[k] for k in ('seed', 'arm', 'ok', 'problems')}, indent=1))
