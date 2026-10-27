"""Engine correctness and balance guard-rails.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import random
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import ratings as R                                       # noqa: E402
from golfsim.course import (ashford_ridge, easy_course, georgia_national, hard_course,  # noqa: E402
                            tight_classic, windy_links)
from golfsim.engine import Conditions, Player, play_round              # noqa: E402
from golfsim.golfer import (ARCHETYPES, CADDIE_SKILLS, OVERALL_WEIGHTS, Caddie,  # noqa: E402
                            archetype_golfer, neutral_caddie, uniform_golfer)
from golfsim.tournament import play_event                              # noqa: E402

MID = ashford_ridge()


def avg(golfer, n, seed=1, course=MID, **kw):
    """Mean score over n rounds; round i always uses the same seed (common random numbers)."""
    return sum(play_round(golfer, course, random.Random(seed * 100_003 + i), **kw).score
               for i in range(n)) / n


class CourseTests(unittest.TestCase):
    def test_courses_are_valid(self):
        for c in (easy_course(), MID, hard_course(), tight_classic(), windy_links(), georgia_national()):
            self.assertEqual(len(c.holes), 18)
            self.assertEqual(c.par, 72)
            self.assertEqual([h.number for h in c.holes], list(range(1, 19)))
        self.assertEqual(MID.yards, 7174)
        self.assertLess(easy_course().yards, MID.yards)
        self.assertLess(MID.yards, hard_course().yards)


class ScoringIntegrityTests(unittest.TestCase):
    def test_round_totals_and_hole_counts(self):
        rng = random.Random(3)
        for rating in (0, 5, 40, 75, 98):
            for _ in range(200):
                st = play_round(uniform_golfer(rating), MID, rng)
                self.assertEqual(len(st.holes), 18)
                self.assertEqual(sum(st.holes), st.score)
                self.assertTrue(all(1 <= s <= 12 for s in st.holes))
                self.assertEqual(st.to_par, st.score - 72)
                self.assertEqual(sum(v[1] for v in st.par_scores.values()), 18)
                self.assertEqual(st.eagles + st.birdies + st.pars + st.bogeys + st.doubles + st.worse, 18)
                self.assertLessEqual(st.gir, 18)
                self.assertGreaterEqual(st.putts, 0)

    def test_same_seed_same_round(self):
        g = archetype_golfer('Power Hitter', 80)
        a = play_round(g, MID, random.Random(42))
        b = play_round(g, MID, random.Random(42))
        self.assertEqual(a.holes, b.holes)
        self.assertEqual(a.drives, b.drives)


class AttributeWiringTests(unittest.TestCase):
    def test_every_rated_attribute_changes_the_compiled_player(self):
        """Each attribute must feed at least one shot parameter (injury resistance is career-only)."""
        base = uniform_golfer(70)
        def snapshot(g):
            p = Player(g, MID, Conditions(), neutral_caddie(), random.Random(0), round_no=4)
            return {k: v for k, v in vars(p).items() if isinstance(v, float)}
        ref = snapshot(base)
        for key in R.ATTRIBUTE_KEYS:
            changed = snapshot(replace(base, attrs={**base.attrs, key: 90.0}))
            if key == 'injury_resistance':
                self.assertEqual(changed, ref)
            else:
                self.assertNotEqual(changed, ref, f'{key} has no effect on play')

    def test_overall_weights_cover_attributes(self):
        self.assertEqual(set(OVERALL_WEIGHTS), set(R.ATTRIBUTE_KEYS))
        self.assertAlmostEqual(sum(OVERALL_WEIGHTS.values()), 1.0, places=2)
        for name in ARCHETYPES:
            self.assertAlmostEqual(archetype_golfer(name, 77).overall, 77, places=1)


class BalanceTests(unittest.TestCase):
    def test_better_golfers_score_better(self):
        scores = [avg(uniform_golfer(r), 300) for r in (25, 50, 75, 95)]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertGreater(scores[0] - scores[-1], 12)

    def test_pro_calibration_within_tolerance(self):
        for rating in (60, 75, 90):
            target = R.interp(R.TARGET_SCORE, rating)
            self.assertAlmostEqual(avg(uniform_golfer(rating), 1200, seed=7), target, delta=1.0)

    def test_hard_courses_punish_weak_players_more(self):
        weak, strong = uniform_golfer(25), uniform_golfer(85)
        gap_easy = avg(weak, 400, course=easy_course()) - avg(strong, 400, course=easy_course())
        gap_hard = avg(weak, 400, course=hard_course()) - avg(strong, 400, course=hard_course())
        self.assertGreater(gap_hard, gap_easy + 5)

    def test_georgia_national_is_brutal_for_weak_players_only(self):
        gn = georgia_national()
        weak, star = uniform_golfer(10), uniform_golfer(92)
        weak_extra = avg(weak, 300, course=gn) - avg(weak, 300)
        star_extra = avg(star, 600, course=gn) - avg(star, 600)
        self.assertGreater(weak_extra, star_extra + 3)
        self.assertGreater(avg(weak, 300, course=gn) - 72, 25)
        self.assertLess(avg(star, 600, course=gn) - 72, 1.0)

    def test_pressure_never_helps_and_composure_limits_it(self):
        def cost(comp):
            g = replace(uniform_golfer(75), attrs={**uniform_golfer(75).attrs, 'composure': comp})
            calm = avg(g, 1500, seed=9, round_no=4)
            tense = avg(g, 1500, seed=9, round_no=4, pressure_fn=lambda i, tp: 1.0)
            return tense - calm
        low, high = cost(40), cost(99)
        self.assertGreater(high, -0.05)
        self.assertGreater(low, high + 0.5)

    def test_caddie_matters_but_is_bounded(self):
        g = uniform_golfer(75)
        elite = Caddie('elite', {k: 95.0 for k in CADDIE_SKILLS})
        gain = avg(g, 2000, seed=4) - avg(g, 2000, seed=4, caddie=elite)
        self.assertGreater(gain, 0.1)
        self.assertLess(gain, 0.8)

    def test_wind_hurts_and_ball_flight_helps(self):
        g = uniform_golfer(75)
        shaper = replace(g, attrs={**g.attrs, 'ball_flight': 95})
        windy = Conditions(wind_mph=25)
        loss_avg = avg(g, 800, seed=5, cond=windy) - avg(g, 800, seed=5)
        loss_shaper = avg(shaper, 800, seed=5, cond=windy) - avg(shaper, 800, seed=5)
        self.assertGreater(loss_avg, 0.5)
        self.assertLess(loss_shaper, loss_avg)


class TournamentTests(unittest.TestCase):
    def test_event_leaderboard_and_cut(self):
        field = [archetype_golfer(list(ARCHETYPES)[i % 7], 66 + i % 20, name=f'G{i}') for i in range(90)]
        board, playoff_holes = play_event(field, MID, random.Random(11), cut_top=50)
        totals = [t for _, t, _ in board]
        self.assertEqual(totals[0], min(totals))
        self.assertGreaterEqual(len(board), 50)
        self.assertTrue(all(len(r) == 4 for _, _, r in board))
        self.assertTrue(all(sum(r) == t for _, t, r in board))


if __name__ == '__main__':
    unittest.main()
