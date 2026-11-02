"""Tee-shot planning against tee-shot play (engine._tee_plan / _tee_outcome / play_hole): the 2049 runaway hole, a
cached plan against a fresh one, ordinary holes unchanged, the dogleg priced as played, reloading after out of
bounds, and the runaway guard kept.

Run from the project folder:  python -m unittest tests.test_tee_plan -v
"""
from __future__ import annotations

import math
import pickle
import random
import statistics as S
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import engine as E                                        # noqa: E402
from golfsim.course import Course, Hole, ashford_ridge                 # noqa: E402
from golfsim.engine import Conditions, Player, RoundStats, play_hole, play_round, wind_distance  # noqa: E402
from golfsim.golfer import uniform_golfer                              # noqa: E402

FIXTURE = ROOT / 'tests' / 'fixtures' / 'runaway_2049_hole17.pkl'
WINDY = Conditions(wind_mph=16.0, wind_from=225.0, gust=0.3)


def old_tee_plan(pl, hole, rng, retee=False):
    """main 18a8e23's tee planner, verbatim but for its cache: one plan per hole and round, re-used on every re-tee;
    trouble through a dogleg priced as a narrower fairway with the two sides' average cost."""
    cache = pl.__dict__.setdefault('_old_plans', {})
    key = hole.number
    if key in cache:
        return cache[key]
    clubs = (('driver', 1.0, 1.0), ('3-wood', 0.92, 0.87), ('iron', 0.80, 0.72))
    best, best_v = None, 1e9
    dirf = pl.hw[hole.number][0] if pl.hw else 1.0
    dfac = wind_distance(pl, hole)
    wind_f = 1 + pl.wind * hole.wind_exposure * (0.55 - 0.40 * pl.bfc) * pl.wind_skill * dirf
    for name, df, sf in clubs:
        carry = pl.drive * df * pl.roll * dfac
        sigma = pl.sigma * sf * wind_f
        half = hole.fairway_width / 2
        extra_rough = 0.0
        if hole.landing_limit and carry > hole.landing_limit:
            over = carry - hole.landing_limit
            if hole.dogleg:
                half = max(4.0, half - over * hole.dogleg * (1 - 0.6 * pl.bfc))
                carry = hole.landing_limit + over * (1 - hole.dogleg) * 0.6
            else:
                extra_rough = min(0.7, over / 25)
                carry = hole.landing_limit + over * 0.35
        p_fw = math.erf(half / (sigma * 1.4142)) * (1 - extra_rough)
        p_out = 1 - math.erf((half + hole.rough_width) / (sigma * 1.4142))
        p_rough = max(0.0, 1 - p_fw - p_out)
        rem = max(5.0, hole.plays - carry)
        side = (E._SIDE_COST[hole.left] + E._SIDE_COST[hole.right]) / 2
        v = (p_fw * E.baseline('fairway', rem) + p_rough * E.baseline('rough', rem)
             + p_out * (E.baseline('rough', rem) + side))
        if name == 'driver':
            v -= 0.06 * pl.aggr + 0.10 * (1 - pl.mgmt) ** 2
        v += rng.gauss(0, pl.noise * 0.25)
        if v < best_v:
            best, best_v = (name, df, sf), v
    cache[key] = best
    return best


def fixture():
    d = pickle.load(open(FIXTURE, 'rb'))
    pl = d['pl']
    pl.plan_noise = {}                                    # (captured from a Player made before these fields)
    pl.plans = {(k, False): v for k, v in pl.plans.items()}
    pl._old_plans = {k[0]: v for k, v in pl.plans.items()}
    rng = random.Random()
    rng.setstate(d['rng'])
    return pl, d['hole'], d['hidx'], rng, d['st'], d['a'], d['k']


DOGLEG = Hole(17, 4, 359, fairway_width=32.6, rough_width=6.2, left='ob', right='trees', landing_limit=221,
              dogleg=0.67, bend='R')


def course_of(holes):
    holes = (list(holes) * 18)[:18]
    return Course('Probe', 'USA', 'Test', tuple(replace(h, number=i + 1) for i, h in enumerate(holes)))


def long_hitter(aggr=82.0, level=72.0):
    g = uniform_golfer(level, aggression=aggr)
    return replace(g, attrs={**g.attrs, 'power': 92.0, 'driving_accuracy': 55.0, 'management': 68.0})


class RunawayHole(unittest.TestCase):
    def test_the_2049_hole_ran_away_under_the_old_planner_and_finishes_now(self):
        pl, hole, hidx, rng, st, a, k = fixture()
        with mock.patch.object(E, '_tee_plan', old_tee_plan):
            with self.assertRaisesRegex(RuntimeError, 'Runaway hole: 60 strokes on hole 17'):
                play_hole(pl, hole, hidx, rng, st, *a, **k)
        pl, hole, hidx, rng, st, a, k = fixture()
        strokes = play_hole(pl, hole, hidx, rng, st, *a, **k)
        self.assertLessEqual(strokes, 8)
        self.assertEqual(E.RUNAWAY_GUARD, 60)                                # the guard itself is unchanged

    def test_the_guard_still_stops_a_hole_that_never_ends(self):
        """No score is invented: a hole that cannot finish (here every tee shot out of bounds) still raises."""
        g = long_hitter()
        pl = Player(g, course_of([DOGLEG] * 18), Conditions(), None, random.Random(1))
        with mock.patch.object(E, '_side_hazard', lambda hole, lat, beyond, rng: (None, 1, True)), \
                mock.patch.object(E, '_tee_outcome', wraps=E._tee_outcome):
            with self.assertRaisesRegex(RuntimeError, 'Runaway hole'):
                for i in range(200):
                    st = RoundStats()
                    play_hole(Player(g, course_of([DOGLEG] * 18), Conditions(), None, random.Random(i)),
                              replace(DOGLEG, fairway_width=2.0, rough_width=0.0), 0, random.Random(i), st)


class CacheAndOrdinaryHoles(unittest.TestCase):
    def test_a_cached_plan_and_a_fresh_evaluation_agree(self):
        """The plan cache changes nothing: whole rounds played with every tee plan recomputed from scratch (its noise
        kept, as drawn at the hole's first tee shot) are identical shot for shot."""
        course = ashford_ridge()
        real = E._tee_plan

        def fresh(pl, hole, rng, retee=False):
            pl.plans.clear()
            return real(pl, hole, rng, retee)
        for gi, g in enumerate((long_hitter(), long_hitter(aggr=40.0, level=60.0), uniform_golfer(85),
                                uniform_golfer(45, aggression=70.0))):
            for seed in range(30):
                a = play_round(g, course, random.Random(seed * 101 + gi), cond=WINDY)
                with mock.patch.object(E, '_tee_plan', fresh):
                    b = play_round(g, course, random.Random(seed * 101 + gi), cond=WINDY)
                self.assertEqual(vars(a), vars(b), (gi, seed))

    def test_ordinary_holes_choose_and_draw_exactly_as_before(self):
        """Away from a dogleg the tee shot can run through (no landing limit, or every club short of it, or a straight
        landing limit), and before any reload, the plan and the random draws are main 18a8e23's."""
        holes = [h for h in ashford_ridge().holes]
        holes += [Hole(1, 4, 430, landing_limit=260, dogleg=0.0, left='ob', right='water'),
                  Hole(2, 5, 560, left='trees', right='ob'), Hole(3, 4, 330, landing_limit=320, dogleg=0.5, bend='L')]
        checked = 0
        for gi in range(40):
            r = random.Random(gi)
            g = uniform_golfer(r.uniform(30, 95), aggression=r.uniform(10, 95))
            g = replace(g, attrs={**g.attrs, 'power': r.uniform(20, 99)})
            course = course_of(holes)
            for h in course.holes:
                if h.par < 4:
                    continue
                pl = Player(g, course, Conditions(), None, random.Random(gi))
                dfac = wind_distance(pl, h)
                if h.dogleg and h.landing_limit and pl.drive * pl.roll * dfac > h.landing_limit:
                    continue                                                   # (a dogleg a club can run through)
                r1, r2 = random.Random(gi * 7 + h.number), random.Random(gi * 7 + h.number)
                self.assertEqual(E._tee_plan(pl, h, r1), old_tee_plan(pl, h, r2), (gi, h.number))
                self.assertEqual(r1.getstate(), r2.getstate())
                checked += 1
        self.assertGreater(checked, 300)

    def test_rounds_without_a_dogleg_to_run_through_or_a_reload_are_identical(self):
        """Identity holds only on paths where the fix never triggers: no dogleg a tee shot can run through and no
        out-of-bounds side (so no reload). Anywhere it does trigger, the shots and the random draws after it differ."""
        straight = course_of([replace(h, landing_limit=0, dogleg=0.0, bend='',
                                      left='trees' if h.left == 'ob' else h.left,
                                      right='trees' if h.right == 'ob' else h.right) for h in ashford_ridge().holes])
        for gi, g in enumerate((long_hitter(), uniform_golfer(60), uniform_golfer(90, aggression=90.0))):
            for seed in range(25):
                a = play_round(g, straight, random.Random(seed + 1000 * gi))
                with mock.patch.object(E, '_tee_plan', old_tee_plan):
                    b = play_round(g, straight, random.Random(seed + 1000 * gi))
                self.assertEqual(vars(a), vars(b), (gi, seed))


class DoglegAsPlayed(unittest.TestCase):
    def test_the_planner_prices_the_corner_where_play_puts_the_ball(self):
        """For a club that runs through the dogleg, the planner's chance of leaving the corridor on the outside
        matches how often play_hole's tee shot does (out of bounds here, so a reload follows)."""
        g = long_hitter()
        course = course_of([DOGLEG] * 18)
        for club in E.TEE_CLUBS[:2]:
            pl0 = Player(g, course, Conditions(), None, random.Random(0))
            rem, p_fw, p_rough, p_out, p_in = E._tee_outcome(pl0, DOGLEG, club[1], club[2], wind_distance(pl0, DOGLEG), 1.0)
            reloads = 0
            n = 3000
            for i in range(n):
                pl = Player(g, course, Conditions(), None, random.Random(i))
                pl.plans[(DOGLEG.number, False)] = club
                calls = []
                real = E._tee_plan

                def spy(p, h, r, retee=False):
                    calls.append(retee)
                    return real(p, h, r, retee)
                with mock.patch.object(E, '_tee_plan', spy):
                    play_hole(pl, DOGLEG, 0, random.Random(i + 7), RoundStats())
                reloads += bool(len(calls) > 1)
            self.assertGreater(p_out, 0.3, club)                              # (a real risk for this player)
            self.assertAlmostEqual(reloads / n, p_out, delta=0.06, msg=club)

    def test_the_old_model_hid_that_risk(self):
        g = long_hitter()
        pl = Player(g, course_of([DOGLEG] * 18), Conditions(), None, random.Random(0))
        rem, p_fw, p_rough, p_out, p_in = E._tee_outcome(pl, DOGLEG, 1.0, 1.0, wind_distance(pl, DOGLEG), 1.0)
        half = max(4.0, DOGLEG.fairway_width / 2 - (pl.drive * pl.roll - DOGLEG.landing_limit) * DOGLEG.dogleg
                   * (1 - 0.6 * pl.bfc))
        old_p_out = 1 - math.erf((half + DOGLEG.rough_width) / (pl.sigma * 1.4142))
        self.assertGreater(p_out, old_p_out / 2 + 0.1)        # the old model spread it over both sides (OB at 1.35)


class Stress(unittest.TestCase):
    def test_short_narrow_doglegs_and_extreme_hitters_always_finish(self):
        """Corners from 140 to 240 yards, fairways from 14 to 34, doglegs 0.4 to 0.95 either way with out of bounds on
        the outside, power 5 to 99, aggression up to 99: every hole finishes well inside the guard, and the reload
        recovers (a lay-up short of even the shortest corner)."""
        worst, holes = 0, 0
        r = random.Random(7)
        for limit in (140, 170, 200, 240):
            for width in (14.0, 24.0, 34.0):
                for dog, bend in ((0.4, 'L'), (0.7, 'R'), (0.95, 'R')):
                    outside, inside = ('ob', 'trees') if bend == 'R' else ('trees', 'ob')
                    hole = Hole(5, 4, max(limit + 120, 300), fairway_width=width, rough_width=5.0, left=outside,
                                right=inside, landing_limit=limit, dogleg=dog, bend=bend)
                    course = course_of([hole])
                    for power in (5.0, 60.0, 99.0):
                        g = uniform_golfer(r.uniform(40, 90), aggression=99.0)
                        g = replace(g, attrs={**g.attrs, 'power': power, 'driving_accuracy': r.uniform(10, 60),
                                              'management': 20.0})
                        for i in range(40):
                            pl = Player(g, course, WINDY, None, random.Random(i))
                            pl.plans[(hole.number, False)] = E.TEE_CLUBS[0]        # the worst start: driver
                            worst = max(worst, play_hole(pl, hole, 0, random.Random(i + 99), RoundStats()))
                            holes += 1
        self.assertEqual(holes, 4 * 3 * 3 * 3 * 40)
        self.assertLess(worst, 20)

    def test_the_lay_up_stops_short_of_any_corner(self):
        for limit in (120, 150, 200):
            for power in (80.0, 99.0):
                g = replace(uniform_golfer(70), attrs={**uniform_golfer(70).attrs, 'power': power})
                hole = Hole(5, 4, 380, landing_limit=limit, dogleg=0.8, bend='R', left='ob', right='trees')
                pl = Player(g, course_of([hole]), Conditions(), None, random.Random(0))
                E._tee_plan(pl, hole, random.Random(0))
                clubs = []
                real = E._tee_value

                def spy(p, h, df, sf, dfac, wind_f):
                    clubs.append(df)
                    return real(p, h, df, sf, dfac, wind_f)
                with mock.patch.object(E, '_tee_value', spy):
                    E._tee_plan(pl, hole, random.Random(0), retee=True)
                lay = min(clubs)
                self.assertLessEqual(pl.drive * lay * pl.roll * wind_distance(pl, hole), limit - 10 + 1e-6)


class Reloading(unittest.TestCase):
    def test_a_reload_needs_no_new_draws_and_drops_the_driver_bonus(self):
        g = long_hitter(aggr=95.0)
        pl = Player(g, course_of([DOGLEG] * 18), Conditions(), None, random.Random(0))
        rng = random.Random(5)
        first = E._tee_plan(pl, DOGLEG, rng)
        state = rng.getstate()
        again = E._tee_plan(pl, DOGLEG, rng, retee=True)
        self.assertEqual(rng.getstate(), state)                               # pure: the hole's noise is kept
        self.assertNotEqual(again[0], 'driver')
        self.assertEqual(E._tee_plan(pl, DOGLEG, rng), first)

    def test_aggressive_long_hitters_recover_on_the_2049_hole(self):
        """The 2049 player type on that hole, driver forced for the first tee shot: every hole finishes, and reloads
        rarely repeat (under the old planner the reload repeated the club that ran out of bounds)."""
        g = long_hitter(aggr=95.0, level=75.0)
        course = course_of([DOGLEG] * 18)
        strokes, chains = [], 0
        for i in range(2000):
            pl = Player(g, course, Conditions(), None, random.Random(i))
            pl.plans[(DOGLEG.number, False)] = E.TEE_CLUBS[0]
            calls = []
            real = E._tee_plan

            def spy(p, h, r, retee=False):
                calls.append(retee)
                return real(p, h, r, retee)
            with mock.patch.object(E, '_tee_plan', spy):
                strokes.append(play_hole(pl, DOGLEG, 0, random.Random(10_000 + i), RoundStats()))
            chains += len(calls) > 2
        self.assertLess(max(strokes), 15)
        self.assertLess(chains / 2000, 0.05)                                  # a second reload is rare
        self.assertLess(S.mean(strokes), 7.0)


if __name__ == '__main__':
    unittest.main()
