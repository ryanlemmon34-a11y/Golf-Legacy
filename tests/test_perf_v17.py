"""v17 performance: the one shortcut kept gives exactly what the code it replaced gave, checked here against a copy of the
replaced code (these tests do not play a season; the Test2 season evidence, the A/B timings and the three shortcuts
measured and not kept are in docs/review/sim_perf/PERF_V17.md).

- Season.eligible reads each tour's countries from TOUR_COUNTRIES (built once per tour) instead of building the set
  on every call: the same answer for every golfer, regular event and week of a small world.

Run from the project folder:  python -m unittest tests.test_perf_v17 -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import season as SE                                         # noqa: E402
from golfsim.calendar import TOUR_BY_KEY                                 # noqa: E402
from golfsim.population import generate_world                            # noqa: E402
from golfsim.season import Season                                        # noqa: E402

YEAR = 2027


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


class Shortcuts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = Season(generate_world(seed=83, scale=0.05), seed=83, development=True, workers=1)
        cls.s.start_year(YEAR)

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


if __name__ == '__main__':
    unittest.main()
