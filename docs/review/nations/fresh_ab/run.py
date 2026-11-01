"""Bounded fresh-world nation check: a new world played for SEASONS seasons with a given build, and per season the
nation measures (cohort totals, carries, nations without newcomers, prestige/multiplier ranges, shares, achievement).
    python3 run.py CHECKOUT WORLD_DIR SEED SEASONS OUT.json [on|off]
on (default): the build's nation rules as they are; off: the same build with only the nation flags off (carry_on,
achievement_on), set right after the world is created, before any cohort is allocated -- so the two arms differ in
the nation rules alone."""
import json, sys, time
from pathlib import Path
code, wdir, seed, seasons, out = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
arm = sys.argv[6] if len(sys.argv) > 6 else 'on'
sys.path.insert(0, code)
from golfsim.session import Session
from golfsim import rules as R
t0 = time.perf_counter()
s = Session.create(wdir, seed=seed, workers=4)
if arm == 'off':
    pt = s.season.participation
    assert not pt.history or all(not h.get('allocated') for h in pt.history.values()), 'allocated before the toggle'
    pt.carry_on, pt.achievement_on = False, False
rows = []
got = {}                                                    # nation -> newcomers so far (juniors + new pros)
for k in range(seasons):
    s.advance(53 if k == 0 else 52)                         # through each winter
    pt = s.season.participation
    y = max(pt.history)
    h = pt.history[y]
    pres = h.get('prestige', {}) or pt.prestige
    mult = h.get('multiplier', {}) or pt.multiplier
    alloc = h.get('allocated', {})
    totals = h.get('totals', {})
    for kind, a in alloc.items():
        for c, n in a.items():
            got[c] = got.get(c, 0) + n
    carry = h.get('carry', {})
    flat = [v for d in carry.values() for v in d.values()] if carry else []
    sh = pt.shares('juniors')
    top5 = sorted(sh.values(), reverse=True)[:5]
    ach = h.get('achievement', {})
    rows.append({
        'entrant_year': y, 'seconds_so_far': round(time.perf_counter() - t0, 1),
        'totals': totals, 'allocated_sums': {k_: sum(v.values()) for k_, v in alloc.items()},
        'totals_exact': all(sum(alloc.get(k_, {}).values()) == totals.get(k_) for k_ in alloc) if totals else None,
        'carry_min': min(flat) if flat else None, 'carry_max': max(flat) if flat else None,
        'carry_sum': round(sum(flat), 9) if flat else None,
        'prestige_min': min(pres.values()), 'prestige_max': max(pres.values()),
        'mult_min': min(mult.values()), 'mult_max': max(mult.values()),
        'at_cap': sum(1 for v in mult.values() if v >= 4 - 1e-9), 'at_floor': sum(1 for v in mult.values() if v <= .25 + 1e-9),
        'usa_share': round(sh.get('USA', 0), 5), 'top5_share': round(sum(top5), 5),
        'below_45': sum(1 for v in pres.values() if v < 45),
        'achievement_min': min(ach.values()) if ach else None, 'achievement_max': max(ach.values()) if ach else None,
        'nations_with_share': sum(1 for v in sh.values() if v > 0),
        'nations_never_given_newcomer': sum(1 for c, v in sh.items() if v > 0 and got.get(c, 0) == 0),
    })
res = {'code': code, 'arm': arm, 'seed': seed, 'rules': R.RULES_VERSION, 'carry_on': getattr(s.season.participation, 'carry_on', None),
       'achievement_on': getattr(s.season.participation, 'achievement_on', None), 'seasons': rows,
       'seconds': round(time.perf_counter() - t0, 1)}
s.close()
Path(out).write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
