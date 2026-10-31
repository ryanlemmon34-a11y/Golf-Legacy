"""Seasonal weather (rules 2026-11-09) meets visible Aggression (rules 2026-11-08): the go-for-it decision on a
par 5 (engine._go_or_lay_up) reads the reach and effective distance in this hole's steady wind (the weather
model's distance factor, engine.wind_distance), not the still-air ones. A headwind shortens reach, so a marginal
go-for-it becomes a lay-up; a tailwind lengthens it, so a shot just out of still-air reach can be attempted.
Aggression still only tilts choices that are possible. Pure unit tests: fixed seeds, no world.

Run from the project folder:  python -m unittest tests.test_weather_geography_merge -v
"""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import engine as E                                         # noqa: E402
from golfsim import weather as WX                                       # noqa: E402
from golfsim.course import ashford_ridge                                # noqa: E402
from golfsim.golfer import uniform_golfer                               # noqa: E402

COURSE = ashford_ridge()
HOLE_NO = 2                                       # Ashford Ridge 2: a par 5, half exposed to the wind
HOLE = COURSE.holes[HOLE_NO - 1]
WIND = 20.0


def golfer(aggression=100, power=85):
    g = uniform_golfer(75, aggression=float(aggression))
    g.attrs['power'] = float(power)
    return g


def player(g, wind_from, seed=0, wind=WIND):
    """A player in a steady seasonal wind blowing from `wind_from` degrees (None: still air, classic model)."""
    cond = E.Conditions(wind_mph=wind if wind_from is not None else 0.0, wind_from=wind_from, gust=0.0)
    return E.Player(g, COURSE, cond, None, random.Random(seed))


def head():
    return WX.hole_bearings(COURSE)[HOLE_NO]       # wind from where the hole points: straight into the face


def tail():
    return (head() + 180) % 360


def go_rate(pl, dist, dfac, n=300, seed=11):
    """Share of second shots on the par 5 from `dist` yards where the golfer goes for the green, with the
    distance factor `dfac` handed to the decision exactly as play_hole hands it (de divided by dfac)."""
    rng = random.Random(seed)
    de = dist * (E.TOUR_DRIVE / pl.drive) ** 0.5 / dfac
    return sum(not E._go_or_lay_up(pl, HOLE, 5, 2, 'fairway', dist, de, rng, dfac)[0] for _ in range(n)) / n


class WindReachesTheDecision(unittest.TestCase):
    def setUp(self):
        self.assertEqual(HOLE.par, 5)
        self.assertGreater(HOLE.wind_exposure, 0)

    def test_headwind_and_tailwind_factors(self):
        g = golfer()
        self.assertEqual(E.wind_distance(player(g, None), HOLE), 1.0)
        self.assertLess(E.wind_distance(player(g, head()), HOLE), 0.95)
        self.assertGreater(E.wind_distance(player(g, tail()), HOLE), 1.02)

    def test_headwind_turns_a_marginal_go_into_a_lay_up(self):
        g = golfer(aggression=100)
        calm, into = player(g, None), player(g, head())
        dfac = E.wind_distance(into, HOLE)
        still, windy = E._reach(into, 'fairway'), E._reach(into, 'fairway', dfac)
        dist = (still + windy) / 2                                  # reachable in still air, not into this wind
        self.assertGreater(dist, 200)
        self.assertGreater(go_rate(calm, dist, 1.0), 0.0)           # still air: an attacking golfer goes for it
        self.assertEqual(go_rate(into, dist, dfac), 0.0)            # headwind: always a lay-up
        self.assertTrue(E._go_or_lay_up(into, HOLE, 5, 2, 'fairway', dist, dist, random.Random(1), dfac)[0])

    def test_tailwind_brings_a_shot_into_reach(self):
        g = golfer(aggression=100)
        calm, down = player(g, None), player(g, tail())
        dfac = E.wind_distance(down, HOLE)
        still, windy = E._reach(down, 'fairway'), E._reach(down, 'fairway', dfac)
        dist = (still + windy) / 2                                  # out of still-air reach, reachable downwind
        self.assertEqual(go_rate(calm, dist, 1.0), 0.0)             # still air: always a lay-up
        self.assertGreater(go_rate(down, dist, dfac), 0.0)          # tailwind: an attacking golfer goes for it

    def test_aggression_only_tilts_what_the_wind_leaves_possible(self):
        into = player(golfer(aggression=100), head())
        dfac = E.wind_distance(into, HOLE)
        dist = E._reach(into, 'fairway', dfac) + 5                  # just beyond reach into this wind
        self.assertEqual(go_rate(into, dist, dfac), 0.0)
        bold, shy = player(golfer(aggression=100), tail()), player(golfer(aggression=0), tail())
        dfac = E.wind_distance(bold, HOLE)
        dist = E._reach(bold, 'fairway', dfac) - 10                 # within reach downwind
        self.assertGreater(go_rate(bold, dist, dfac), go_rate(shy, dist, dfac))


class PlayHolePassesTheWind(unittest.TestCase):
    """play_hole hands _go_or_lay_up the hole's steady-wind factor (not 1.0) and the wind-adjusted effective
    distance, and lays up or goes as that decision says."""

    def calls(self, wind_from, seed):
        g = golfer(aggression=100)
        rng = random.Random(seed)
        pl = player(g, wind_from, seed)
        seen = []
        real = E._go_or_lay_up

        def spy(pl_, hole, par, strokes, lie, dist, de, rng_, dfac=1.0):
            out = real(pl_, hole, par, strokes, lie, dist, de, rng_, dfac)
            seen.append((lie, dist, de, dfac, out))
            return out
        with mock.patch.object(E, '_go_or_lay_up', spy):
            E.play_hole(pl, HOLE, HOLE_NO - 1, rng, E.RoundStats(), 0.0, E.HoleState(), (0.0, 0.0))
        return pl, seen

    def test_the_decision_reads_this_holes_wind(self):
        for wind_from, check in ((head(), self.assertLess), (tail(), self.assertGreater), (None, self.assertEqual)):
            for seed in range(5):
                pl, seen = self.calls(wind_from, seed)
                self.assertTrue(seen)
                expected = E.wind_distance(pl, HOLE)
                check(expected, 1.0)
                for lie, dist, de, dfac, (lay_up, reach) in seen:
                    self.assertEqual(dfac, expected)
                    self.assertAlmostEqual(de, dist * (E.TOUR_DRIVE / pl.drive) ** 0.5 / expected)
                    self.assertEqual(reach, E._reach(pl, lie, expected))      # the reach in this wind
                    if dist > reach:
                        self.assertTrue(lay_up)                    # out of reach in this wind: a lay-up

    def test_same_seed_same_hole(self):
        a = self.calls(head(), 3)[1]
        b = self.calls(head(), 3)[1]
        self.assertEqual(a, b)


if __name__ == '__main__':
    unittest.main()
