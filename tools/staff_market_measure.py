"""Staff-market measurements for the recruitment package: run a small world a few seasons (workers=1) and
report partnership counts, churn, lengths, coached share by level, refusals, offer-only endings and
development by coaching status (docs/RECRUITMENT_PACKAGE.md).
Usage: python tools/staff_market_measure.py ROOT SEED SCALE YEARS OUT.json (ROOT: the checkout to measure)"""
import json
import statistics as S
import sys
import time
from collections import Counter, defaultdict

root, seed, scale, years, out = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
sys.path.insert(0, root)
sys.path.insert(0, root + '/tools')
from golfsim import development as D                     # noqa: E402
from golfsim.calendar import TOUR_BY_KEY                  # noqa: E402
from golfsim.population import generate_world             # noqa: E402
from golfsim.season import Season                         # noqa: E402
import long_world as LW                                   # noqa: E402
from golfsim import staff as ST                           # noqa: E402

# the starting coaches are not scaled with the population (480 for any scale); scale them so a small world has
# the full world's coaches per golfer (same patch for both builds)
ST.INITIAL_COACHES = round(ST.INITIAL_COACHES * scale)


def level(g):
    if g.tour.startswith('CO_'):
        return 'college'
    if g.status == 'amateur':
        return 'amateur'
    t = TOUR_BY_KEY.get(g.tour)
    if g.lifestyle != 'full_time':
        return 'pro part-time'
    return {1: 'Premier', 2: 'Challenger'}.get(t.tier if t else 9, 'pro other')


def cause(s):
    r = s.reason_end
    if s.ended_by == 'retirement':
        return 'retirement'
    if r.startswith('left for an approach') or r.startswith('joined '):
        return 'offer'
    if 'afford' in r or 'pay' in r:
        return 'money'
    if s.ended_by == 'golfer':
        return 'golfer change'
    return 'staff moved on'


t0 = time.perf_counter()
s = Season(generate_world(seed=seed, scale=scale), seed=seed, development=True, workers=1)
first = s.first_year
rows = {}
for y in range(first, first + years):
    active_before = sum(1 for g in s.world.golfers if g.lifestyle != 'retired')
    lv = {g.id: level(g) for g in s.world.golfers if g.lifestyle != 'retired'}
    age = {g.id: g.age(y) for g in s.world.golfers if g.lifestyle != 'retired'}
    s.run_year(y)
    snap = s.snapshots.get(y, {})
    chk = LW.checks(s, y, snap, active_before)
    a = s.assignments[y]
    st = s.staff
    by_level = defaultdict(lambda: [0, 0])
    for gid, l in lv.items():
        by_level[l][0] += 1
        by_level[l][1] += gid in a['coach_of']
    ended = [x for x in st.rel.stints if x.kind in ('coach', 'caddie') and x.end and (y, 1) <= x.end <= (y, 53)]
    began = [x for x in st.rel.stints if x.kind in ('coach', 'caddie') and (y, 1) <= x.start <= (y, 53)]
    causes = Counter((x.kind, cause(x)) for x in ended)
    length = {k: [((x.end[0] - x.start[0]) * 52 + x.end[1] - x.start[1]) / 52 for x in ended if x.kind == k]
              for k in ('coach', 'caddie')}
    refusals = Counter()
    for r in getattr(st.rel, 'refusals', ()):
        if r[3] == y:
            refusals[f'{r[0]} refused by {r[6]}'] += 1
    dev = defaultdict(list)
    for gid, acc in s.dev_acc.get(y, {}).items():
        o0 = s.overall_start.get(y, {}).get(gid)
        o1 = acc[D.OV_POST] or acc[D.OV_PRE]
        if o0 is None or not o1 or gid not in age:
            continue
        band = '<=23' if age[gid] <= 23 else '24-30' if age[gid] <= 30 else '31+'
        status = a['deal'].get(gid, 'none') if gid in a['coach_of'] else 'none'
        dev[f'{band} {status}'].append(o1 - o0)
    rows[y] = {'coach_pairs': len(a['coach_of']), 'share_deals': sum(1 for d in a['deal'].values() if d == 'share'),
               'caddie_pairs': len(a['caddie_of']), 'active': active_before,
               'coaches_active': sum(1 for c in st.coaches.values() if c.status == 'active'),
               'caddies_active': sum(1 for k in st.caddies.values() if k.status == 'active'),
               'began': dict(Counter(x.kind for x in began)), 'ended': dict(Counter(x.kind for x in ended)),
               'causes': {f'{k} {c}': n for (k, c), n in causes.items()},
               'mean_len': {k: round(S.mean(v), 2) if v else None for k, v in length.items()},
               'coached_share': {l: round(c / n, 3) for l, (n, c) in sorted(by_level.items())},
               'level_n': {l: n for l, (n, c) in sorted(by_level.items())},
               'refusals': dict(refusals),
               'dev': {k: [round(S.mean(v), 3), len(v)] for k, v in sorted(dev.items())},
               'checks': {k: chk[k] for k in ('reconcile_errors', 'staff_violations', 'coach_paid', 'coach_received',
                                              'caddie_paid', 'caddie_received')}}
    print(y, json.dumps(rows[y]), f'{time.perf_counter() - t0:.0f}s', flush=True)
    s.snapshots.pop(y, None)
# lengths of every partnership still open or ended, at the end
allst = [x for x in s.staff.rel.stints if x.kind in ('coach', 'caddie')]
summary = {'seed': seed, 'scale': scale, 'years': years, 'rows': rows,
           'stints_total': dict(Counter(x.kind for x in allst)), 'seconds': round(time.perf_counter() - t0)}
json.dump(summary, open(out, 'w'), indent=1)
s.close()
