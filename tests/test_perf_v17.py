"""v17 performance shortcuts give exactly what the code they replaced gave (outcome-identical by construction; the
whole-season equivalence on the Test2 world -- saved state and history byte for byte -- is in the review evidence).

- _seed remembers its hashes: the same integers as hashing every time, for repeated and new keys;
- eligible reads each tour's countries from TOUR_COUNTRIES: the same answer as building the set each call, for every
  golfer, event and week of a small world;
- event_value keeps a golfer's prize forecast per tier for the week: the same values (and the same random draws) as
  expected_prize every time;
- overall_rating's weight total is worked out once: the same float, bit for bit.

Run from the project folder:  python -m unittest tests.test_perf_v17 -v
"""
from __future__ import annotations

import hashlib
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import golfer as G                                          # noqa: E402
from golfsim import season as SE                                         # noqa: E402
from golfsim.calendar import TOUR_BY_KEY                                 # noqa: E402
from golfsim.population import generate_world                            # noqa: E402
from golfsim.season import Season                                        # noqa: E402

YEAR = 2027


def seed_before(*parts):
    return int.from_bytes(hashlib.blake2b(':'.join(map(str, parts)).encode(), digest_size=8).digest(), 'big')


def eligible_before(self, g, s, week):
    """Season.eligible as it was (afa5e4a): the tour's country set built on every call."""
    from golfsim.season import COUNTRIES, region_of
    tier, st = s.tier, g.status
    mt = TOUR_BY_KEY.get(g.tour)
    mtier = mt.tier if mt else 9
    countries = {c for c, _ in TOUR_BY_KEY[s.tour].countries} if s.tour in TOUR_BY_KEY else set()
    if s.category == 'national_open' and tier >= 2:
        return st == 'pro' or (st == 'amateur' and g.country == s.host_country and self.am_pos.get(g.id, 9999) <= 300)
    if tier == 1:
        if st == 'pro':
            return mtier <= 2 or self.wr_pos.get(g.id, 9999) <= 500 or g.id in self.winners_now()
        return st == 'amateur' and self.am_pos.get(g.id, 9999) <= 25
    if tier == 2:
        return st == 'pro' and (mtier <= 2 or (mtier <= 4 and g.country in countries))
    if tier == 3:
        return st == 'pro' and (mtier <= 3 or g.country in countries)
    if tier == 4:
        return st == 'pro' and (g.tour == s.tour or g.country in countries or mtier == 4 and region_of(g) ==
                                COUNTRIES[s.host_country].region)
    if tier == 5:
        return g.tour == s.tour
    if tier == 6:
        return self.series_amateur(g, s.tour)
    if tier == 8:
        return st == 'club_pro' and (g.country in countries or region_of(g) == COUNTRIES[s.host_country].region)
    return False


def overall_before(attrs, weights=None):
    w = weights or G.OVERALL_WEIGHTS
    total = sum(w.values())
    return sum(attrs[k] * w[k] for k in w) / total


class Shortcuts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = Season(generate_world(seed=83, scale=0.05), seed=83, development=True, workers=1)
        cls.s.start_year(YEAR)

    def test_seed(self):
        rnd = random.Random(1)
        keys = [(83, 'drive', f'Town {rnd.randrange(50)}', f'City {rnd.randrange(30)}') for _ in range(3000)]
        keys += [(83, YEAR, f'S{rnd.randrange(40)}', 'entry', rnd.randrange(500)) for _ in range(3000)]
        for k in keys + keys[::-1]:                                       # new keys, then remembered ones
            self.assertEqual(SE._seed(*k), seed_before(*k))
        self.assertEqual(SE._seed('a', 1, None, 2.5), seed_before('a', 1, None, 2.5))
        info = SE._seed_of.cache_info()
        self.assertGreater(info.hits, 0)
        self.assertLessEqual(info.currsize, 1 << 16)                     # bounded

    def test_eligible(self):
        s = self.s
        eds = [e for e in s.cal.editions(YEAR) if not s.is_special(e.series)]   # (what planning and entries ask)
        n = 0
        for g in s.active_golfers():
            for ed in eds[::3]:
                for week in (ed.week, 30):
                    self.assertEqual(s.eligible(g, ed.series, week), eligible_before(s, g, ed.series, week),
                                     (g.id, ed.event_id))
                    n += 1
        self.assertGreater(n, 10000)

    def test_event_value_with_the_forecast_kept(self):
        s = self.s
        eds = [e for e in s.cal.editions(YEAR) if e.series.purse][:60]
        venues = s.venues(YEAR)
        country = lambda ed: SE.CITY_BY_NAME[venues[ed.event_id][0].city].country
        checked = 0
        for g in [g for g in s.active_golfers() if g.status == 'pro'][:120]:
            gw = s.golfer_week(g, YEAR, 10)
            plain = dict(gw)
            plain.pop('forecast')                                           # (expected_prize every time)
            r1, r2 = random.Random(g.id), random.Random(g.id)
            for ed in eds:
                a = s.event_value(g, ed, 10, r1, country(ed), 1234.5, gw, None)
                b = s.event_value(g, ed, 10, r2, country(ed), 1234.5, plain, None)
                self.assertEqual(a, b)                                       # bit for bit, draws included
                checked += 1
            self.assertTrue(gw['forecast'])                                  # (the forecast was kept)
        self.assertGreater(checked, 1000)

    def test_overall_rating(self):
        rnd = random.Random(5)
        for _ in range(2000):
            attrs = {k: rnd.uniform(0, 100) for k in G.OVERALL_WEIGHTS}
            self.assertEqual(G.overall_rating(attrs), overall_before(attrs))
            w = {k: rnd.uniform(0.01, 1) for k in G.OVERALL_WEIGHTS}
            self.assertEqual(G.overall_rating(attrs, w), overall_before(attrs, w))
        self.assertEqual(G.overall_rating(attrs, {}), overall_before(attrs, {}))   # (empty: the default weights)


if __name__ == '__main__':
    unittest.main()
