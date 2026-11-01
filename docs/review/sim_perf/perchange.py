"""Per-change cost/benefit of the v17 shortcuts on the Test2 world (a fresh copy, afa5e4a code for the counts; the
replaced and new functions timed side by side on the world's own inputs).
    PYTHONHASHSEED=0 python3 perchange.py BASE_CODE PERF_CODE WORLD WEEKS OUT.json"""
import gc, hashlib, json, sys, time, timeit, tracemalloc
from collections import OrderedDict, Counter
from pathlib import Path
base, perf, world, weeks, out = sys.argv[1], sys.argv[2], Path(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
sys.path.insert(0, base)
from golfsim import season as SE, golfer as G
from golfsim.session import Session

counts = Counter()
keys = []                                                 # the _seed key stream, in order
pairs = []                                                # (golfer, series) eligibility questions (a sample)
distinct_fc = set()                                       # (week, golfer, tier) forecasts event_value needed
real = {'seed': SE._seed, 'elig': SE.Season.eligible, 'ep': SE.Season.expected_prize, 'pf': SE.Season.prize_forecast,
        'ov': G.overall_rating, 'ev': SE.Season.event_value}


def seed(*parts):
    counts['_seed'] += 1
    keys.append(':'.join(map(str, parts)))
    return real['seed'](*parts)


def elig(self, g, s, week):
    counts['eligible'] += 1
    if counts['eligible'] % 50 == 0 and len(pairs) < 100000:
        pairs.append((g.id, s.series_id, week))
    return real['elig'](self, g, s, week)


def ep(self, g, s):
    counts['expected_prize'] += 1
    if getattr(self, '_in_ev', 0):
        counts['expected_prize_in_event_value'] += 1
        if g.status != 'amateur' and s.purse:
            counts['forecasts_needed_in_event_value'] += 1
            distinct_fc.add((self._in_ev, g.id, s.tier))
    return real['ep'](self, g, s)


def ev(self, g, ed, *a, **k):
    self._in_ev = ('w', a[0] if a else k.get('week'))
    try:
        return real['ev'](self, g, ed, *a, **k)
    finally:
        self._in_ev = 0


def ov(attrs, weights=None):
    counts['overall_rating'] += 1
    return real['ov'](attrs, weights)


SE._seed, SE.Season.eligible, SE.Season.expected_prize, SE.Season.event_value = seed, elig, ep, ev
G.overall_rating = ov
import golfsim.golfer
for mod in list(sys.modules.values()):                    # (modules that imported overall_rating by name)
    if mod and getattr(mod, 'overall_rating', None) is real['ov']:
        mod.overall_rating = ov
s = Session.open(world, workers=4, allow_other_engine=True)
t = time.perf_counter()
s.advance(weeks)
res = {'weeks': weeks, 'seconds': round(time.perf_counter() - t, 1), 'calls': dict(counts)}
# distinct (golfer, tier) forecasts per golfer-week inside event_value: the memo saves the rest
# (estimated from the forecast need count and the share of repeats; measured directly below on the world)
season = s.season
# ---- _seed: LRU of 65,536 on the real key stream
lru, hits = OrderedDict(), 0
for k in keys:
    if k in lru:
        hits += 1
        lru.move_to_end(k)
    else:
        lru[k] = 1
        if len(lru) > 1 << 16:
            lru.popitem(last=False)
res['seed'] = {'calls': len(keys), 'distinct': len(set(keys)), 'lru_hits': hits,
               'hit_rate': round(hits / max(1, len(keys)), 4)}
blake = lambda k: int.from_bytes(hashlib.blake2b(k.encode(), digest_size=8).digest(), 'big')
sample = keys[:200000]
t_old = timeit.timeit(lambda: [blake(k) for k in sample], number=3) / (3 * len(sample))
import functools
cached = functools.lru_cache(maxsize=1 << 16)(blake)
for k in sample:
    cached(k)
t_hit = timeit.timeit(lambda: [cached(k) for k in sample[:50000]], number=3) / (3 * 50000)
res['seed']['ns_per_call_old'] = round(t_old * 1e9, 1)
res['seed']['ns_per_call_hit'] = round(t_hit * 1e9, 1)
tracemalloc.start()
c2 = functools.lru_cache(maxsize=1 << 16)(blake)
for k in keys[-(1 << 16) * 2:]:
    c2(k)
cur, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
res['seed']['cache_bytes_full'] = cur
# ---- eligible: old (set built per call) vs new (TOUR_COUNTRIES)
sys.path.insert(0, perf)
import importlib.util
spec = importlib.util.spec_from_file_location('perf_season', Path(perf) / 'golfsim' / 'season.py',
                                              submodule_search_locations=None)
by_series = {e.series.series_id: e.series for e in season.cal.editions(season.year)}
qs = [(season.g[g], by_series[sid], w) for g, sid, w in pairs if g in season.g and sid in by_series]
src_new = SE.Season.eligible.__code__ if False else None
def elig_new(self, g, s, week, _TC=SE.TOUR_COUNTRIES):
    countries = _TC.get(s.tour, frozenset())
    return countries                                   # (only the changed line: the set lookup itself)
def elig_old_part(self, g, s, week):
    return {c for c, _ in SE.TOUR_BY_KEY[s.tour].countries} if s.tour in SE.TOUR_BY_KEY else set()
n = len(qs)
t1 = timeit.timeit(lambda: [elig_old_part(season, g, s_, w) for g, s_, w in qs], number=3) / (3 * n)
t2 = timeit.timeit(lambda: [elig_new(season, g, s_, w) for g, s_, w in qs], number=3) / (3 * n)
res['eligible'] = {'calls': counts['eligible'], 'sample': n, 'ns_old_set': round(t1 * 1e9, 1),
                   'ns_new_lookup': round(t2 * 1e9, 1)}
# ---- overall_rating
attrs = [g.attrs for g in list(season.world.golfers)[:5000]]
W = G.OVERALL_WEIGHTS
def ov_old(a, w=None):
    w = w or W
    total = sum(w.values())
    return sum(a[k] * w[k] for k in w) / total
TOT = sum(W.values())
def ov_new(a, w=None):
    w = w or W
    total = TOT if w is W else sum(w.values())
    return sum(a[k] * w[k] for k in w) / total
t1 = timeit.timeit(lambda: [ov_old(a) for a in attrs], number=5) / (5 * len(attrs))
t2 = timeit.timeit(lambda: [ov_new(a) for a in attrs], number=5) / (5 * len(attrs))
res['overall_rating'] = {'calls': counts['overall_rating'], 'ns_old': round(t1 * 1e9, 1), 'ns_new': round(t2 * 1e9, 1)}
# ---- prize forecasts inside event_value
gs = [g for g in season.active_golfers() if g.status == 'pro'][:3000]
tiers = sorted({e.series.tier for e in season.cal.editions(season.year) if e.series.purse})
t1 = timeit.timeit(lambda: [season.prize_forecast(g, t_) for g in gs for t_ in tiers], number=3) / (3 * len(gs) * len(tiers))
res['forecast'] = {'calls_needed_in_event_value': counts['forecasts_needed_in_event_value'],
                   'distinct_golfer_week_tier': len(distinct_fc),
                   'ns_per_prize_forecast': round(t1 * 1e9, 1), 'tiers_with_purses': len(tiers)}
s.close()
Path(out).write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
