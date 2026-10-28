"""Performance-only change: the weekly work walks the active golfers, not everyone who ever lived in the
world. The world must be exactly the same either way, and retired golfers keep their identity.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim.population import generate_world                         # noqa: E402
from golfsim.season import Season                                     # noqa: E402


def run(weeks_into_second_season, everyone=False):
    s = Season(generate_world(seed=13, scale=0.12), seed=13, development=True, workers=1)
    patch = mock.patch.object(Season, 'active_golfers', lambda self: self.world.golfers) if everyone else None
    if patch:
        patch.start()
    try:
        s.run_year(2027)
        s.start_year(2028)
        for w in range(1, weeks_into_second_season + 1):
            s.advance_week(2028, w)
    finally:
        if patch:
            patch.stop()
    parts = [sorted((k, r.finish) for k, r in s.results.items()),
             sorted((g.id, round(g.cash, 6), round(g.overall, 9), g.tour, g.status, g.lifestyle, round(g.fatigue, 9))
                    for g in s.world.golfers),
             sorted(s.wr_pos.items()), sorted(s.am_pos.items()),
             sorted((y, sorted(c.items())) for y, c in s.week_access.items())]
    return s, hashlib.sha256(repr(parts).encode()).hexdigest()


class ActiveGolferTests(unittest.TestCase):
    def test_same_world_whether_the_weekly_work_walks_everyone_or_the_active(self):
        fast, a = run(10)
        _, b = run(10, everyone=True)
        retired = [g for g in fast.world.golfers if g.lifestyle == 'retired']
        self.assertTrue(retired)                                          # retirements happened
        self.assertEqual(a, b)
        self.assertNotIn(retired[0], fast.active_golfers())
        self.assertIs(fast.g[retired[0].id], retired[0])                  # still in the world, with history
        self.assertTrue(fast.history[retired[0].id])


if __name__ == '__main__':
    unittest.main()
