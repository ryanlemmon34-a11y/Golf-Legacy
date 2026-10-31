"""Injury timing (rules 2026-11-02): an injury at an event in week W announced as n weeks keeps the golfer out of
the entries of weeks W+1 .. W+n and they can enter again from week W+n+1, counted on across the year end (next
season's week 1 follows week 52). The weekly entry check (`is_injured` when entries are taken), the end-of-week
recovery (`update_fatigue`), the season planner's first playable week and the archived episode all agree.

Run from the project folder:  python -m unittest tests.test_injury_timing -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim.population import generate_world                         # noqa: E402
from golfsim.season import Season                                     # noqa: E402


def next_week(y, w):
    return (y, w + 1) if w < 52 else (y + 1, 1)


class Timing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = Season(generate_world(seed=95, scale=0.02), seed=95, development=True, workers=1, calendar='v2')
        cls.s.start_year(2027)
        cls.gid = min(g.id for g in cls.s.active_golfers() if g.lifestyle != 'retired')

    @classmethod
    def tearDownClass(cls):
        cls.s.close()

    def out_weeks(self, year, week, n):
        """Inject an injury at the end of (year, week) announced as n weeks, then walk the weeks: [(year, week)
        whose entries it kept the golfer out of], and the first week they could enter again."""
        s, gid = self.s, self.gid
        s.injured.clear()
        s._week_load.clear()                                        # (nobody played: no new injuries)
        s.injure(gid, year, week, n, 'test')
        out, (y, w) = [], next_week(year, week)
        while s.is_injured(gid):                                    # entries for (y, w) are taken here
            out.append((y, w))
            s.update_fatigue(y, w)                                  # the end of that week
            y, w = next_week(y, w)
            self.assertLess(len(out), 60)
        return out, (y, w)

    def test_n_weeks_announced_is_n_weeks_out(self):
        for n in (1, 2, 3, 7, 15):
            out, back = self.out_weeks(2027, 10, n)
            self.assertEqual(out, [(2027, 10 + k) for k in range(1, n + 1)], n)
            self.assertEqual(back, (2027, 11 + n))

    def test_across_the_year_end(self):
        out, back = self.out_weeks(2027, 51, 3)
        self.assertEqual(out, [(2027, 52), (2028, 1), (2028, 2)])
        self.assertEqual(back, (2028, 3))
        out, back = self.out_weeks(2027, 52, 1)                     # hurt in the season's last week
        self.assertEqual((out, back), ([(2028, 1)], (2028, 2)))
        out, back = self.out_weeks(2027, 50, 2)                     # back in time for the last week
        self.assertEqual((out, back), ([(2027, 51), (2027, 52)], (2028, 1)))

    def test_the_episode_and_the_planner_agree(self):
        s, gid = self.s, self.gid
        for week, n in ((10, 3), (51, 3), (52, 1), (40, 15)):
            s.injured.clear()
            s.injuries[2027].clear()
            s.injure(gid, 2027, week, n, 'test')
            (e,) = s.injury_episodes(2027)[gid]
            out, back = self.out_weeks(2027, week, n)
            self.assertEqual((e['announced'], e['out'], tuple(e['available'])), (n, n, back), (week, n))
            s.injure(gid, 2027, week, n, 'test')                   # the planner's first playable week (season.plan)
            first = s.injured[gid][0]
            self.assertEqual(first, s.abs_week(*back))
        s.injured.clear()
        s.injuries[2027].clear()


if __name__ == '__main__':
    unittest.main()
