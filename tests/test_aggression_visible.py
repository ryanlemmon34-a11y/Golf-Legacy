"""Aggression made visible and kept stable (roadmap G2, rules 2026-11-08).

- Aggression is shown on profiles (0-100, cautious / balanced / attacking) with what it means, as a style and
  not an ability grade;
- the trait does not decline with age, injury or anything else: no simulation code writes it;
- reach is physical: an out-of-reach shot is a lay-up however aggressive the golfer, so an aging attacking
  golfer still attacks, at what they can still reach (the existing reach-based lay-up constraint);
- no second risk score exists; decisions are deterministic for a seed.

Quick unit tests only: no season is simulated and no world is generated.
Run from the project folder:  python -m unittest tests.test_aggression_visible -v
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import development as D                                      # noqa: E402
from golfsim import engine as E                                           # noqa: E402
from golfsim.course import Hole, ashford_ridge                            # noqa: E402
from golfsim.golfer import Golfer, uniform_golfer                         # noqa: E402
from golfsim.ratings import ATTRIBUTE_KEYS, PERSONALITY_KEYS              # noqa: E402

COURSE = ashford_ridge()
PAR5 = Hole(2, 5, 560)


def golfer(power, aggression, rating=70):
    g = uniform_golfer(rating, aggression=float(aggression))
    g.attrs['power'] = float(power)
    return g


def player(g, seed=0):
    return E.Player(g, COURSE, E.Conditions(), None, random.Random(seed))


def go_rate(g, dist, lie='fairway', n=400):
    """Share of second shots on a par 5 from `dist` yards where the golfer goes for the green."""
    pl = player(g)
    rng = random.Random(7)
    de = dist * (E.TOUR_DRIVE / pl.drive) ** 0.5
    return sum(not E._go_or_lay_up(pl, PAR5, 5, 2, lie, dist, de, rng)[0] for _ in range(n)) / n


YOUNG, OLD = 85, 25            # Power in a golfer's prime, and after years of decline


class ReachTests(unittest.TestCase):
    def test_reach_follows_power_not_aggression(self):
        self.assertGreater(E._reach(player(golfer(YOUNG, 50)), 'fairway'), 250)
        self.assertLess(E._reach(player(golfer(OLD, 50)), 'fairway'), 250)
        for p in (YOUNG, OLD):
            reaches = {round(E._reach(player(golfer(p, a)), lie), 6) for a in (0, 50, 100)
                       for lie in ('fairway',)}
            self.assertEqual(len(reaches), 1)                        # aggression never lengthens a club
        pl = player(golfer(YOUNG, 50))
        self.assertLess(E._reach(pl, 'rough'), E._reach(pl, 'fairway'))
        self.assertLess(E._reach(pl, 'fairway_bunker'), E._reach(pl, 'rough'))

    def test_out_of_reach_is_always_a_lay_up(self):
        old_attacker = golfer(OLD, 100)
        self.assertEqual(go_rate(old_attacker, 250), 0.0)           # beyond reach: never goes, at 100
        self.assertEqual(go_rate(golfer(YOUNG, 100), 250, lie='fairway_bunker'), 0.0)
        pl = player(old_attacker)
        rng = random.Random(1)
        for dist in (240, 260, 300):                               # par 4s too: out of reach is a lay-up
            de = dist * (E.TOUR_DRIVE / pl.drive) ** 0.5
            self.assertTrue(E._go_or_lay_up(pl, Hole(1, 4, 480), 4, 2, 'fairway', dist, de, rng)[0])

    def test_young_attacker_goes_more_than_young_cautious(self):
        self.assertGreater(go_rate(golfer(YOUNG, 95), 250), go_rate(golfer(YOUNG, 5), 250))

    def test_aging_attacker_still_attacks_what_is_reachable(self):
        old_reach = E._reach(player(golfer(OLD, 50)), 'fairway')
        dist = old_reach - 10                                       # still reachable for the older golfer
        self.assertGreater(dist, 200)                               # (a real go-or-lay-up decision)
        attack, cautious = go_rate(golfer(OLD, 95), dist), go_rate(golfer(OLD, 5), dist)
        self.assertGreater(attack, 0.0)
        self.assertGreater(attack, cautious)
        # the same attacking golfer, shorter now: goes from where he still can, lays up where he cannot
        self.assertEqual(go_rate(golfer(OLD, 95), old_reach + 15), 0.0)
        self.assertGreater(go_rate(golfer(YOUNG, 95), old_reach + 15), 0.0)

    def test_attacking_pins_and_driver_do_not_depend_on_age(self):
        def pins(g):
            pl, rng = player(g), random.Random(3)
            return sum(E._attack_pin(pl, COURSE.holes[2], 20.0, rng) for _ in range(400))
        self.assertGreater(pins(golfer(OLD, 95)), pins(golfer(OLD, 5)))
        self.assertEqual(pins(golfer(OLD, 95)), pins(golfer(YOUNG, 95)))   # same choice where both can play it

    def test_decisions_are_deterministic(self):
        self.assertEqual(go_rate(golfer(YOUNG, 70), 255), go_rate(golfer(YOUNG, 70), 255))
        a = [E.play_round(golfer(OLD, 90), COURSE, random.Random(s)).score for s in range(5)]
        b = [E.play_round(golfer(OLD, 90), COURSE, random.Random(s)).score for s in range(5)]
        self.assertEqual(a, b)


class StabilityTests(unittest.TestCase):
    def test_aging_never_changes_personality(self):
        g = Golfer('Veteran', {k: 75.0 for k in ATTRIBUTE_KEYS},
                   {'big_stage': 60.0, 'aggression': 90.0, 'adaptability': 40.0, 'coachability': 55.0,
                    'work_ethic': 70.0})
        g.peak_age, g.aging_rate, g.born = 30.0, 1.4, 1990
        g.ceilings = {k: 80.0 for k in ATTRIBUTE_KEYS}
        before = dict(g.personality)
        rng = random.Random(5)
        for age in range(30, 66):
            D.age_year(g, age, rng, experience=0.5)
            if age in (45, 58):
                D.serious_injury(g, 30, rng)
        self.assertEqual(g.personality, before)                    # still 90: an attacking 65-year-old
        self.assertLess(g.attrs['power'], 60)                      # while the body declined
        self.assertLess(E._reach(player(g), 'fairway'), E._reach(player(golfer(75, 90)), 'fairway'))

    def test_no_simulation_code_writes_a_personality_trait(self):
        write = re.compile(r"personality\[['\"]\w+['\"]\]\s*(?:[-+*/]?=)(?!=)|personality\.update\(|"
                           r"personality\.setdefault\(['\"]aggression")
        offenders = []
        for path in sorted((ROOT / 'golfsim').glob('*.py')):
            for no, line in enumerate(path.read_text(encoding='utf8').splitlines(), 1):
                if write.search(line):
                    offenders.append(f'{path.name}:{no}: {line.strip()}')
        # Golfer.__post_init__ fills a missing trait with the neutral 50 once, at creation: the only write
        self.assertEqual([o for o in offenders if 'golfer.py' not in o or 'setdefault(k, 50.0)' not in o], [])

    def test_no_second_risk_score(self):
        self.assertEqual(PERSONALITY_KEYS, ('big_stage', 'aggression', 'adaptability', 'coachability', 'work_ethic'))
        self.assertFalse([k for k in (*ATTRIBUTE_KEYS, *PERSONALITY_KEYS) if 'risk' in k])
        fields = set(Golfer.__dataclass_fields__)
        self.assertFalse([f for f in fields if 'risk' in f or 'aggress' in f])


class ProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import observer_history as OH
        cls.OH = OH

    def test_styles(self):
        self.assertEqual([self.OH.aggression_style(v) for v in (0, 34, 35, 50, 65, 66, 100)],
                         ['cautious', 'cautious', 'balanced', 'balanced', 'balanced', 'attacking', 'attacking'])

    def test_shown_with_explanation_not_a_grade(self):
        w = SimpleNamespace(live=SimpleNamespace(people={5: {'aggression': 82}}))
        html = self.OH.aggression_section(w, 5, {'roles': ['golfer'], 'golfer': {}})
        self.assertIn('Aggression <b>82</b> / 100', html)
        self.assertIn('attacking', html)
        self.assertIn('not an ability', html)
        self.assertIn('higher is not better', html)
        self.assertIn('/rules#aggression', html)

    def test_archived_and_missing(self):
        w = SimpleNamespace(live=None)
        html = self.OH.aggression_section(w, 5, {'golfer': {'aggression': 20}})
        self.assertIn('cautious', html)
        self.assertEqual(self.OH.aggression_section(w, 5, {'golfer': {}}), '')

    def test_rule_text_matches_the_bands(self):
        from golfsim import rules
        title, text, since = rules.RULES['aggression']
        self.assertEqual(since, '2026-11-08')
        for fact in ('never changed afterwards', 'not an ability', 'below 35', '35-65', 'above 65',
                     'always a lay-up', 'no other risk score'):
            self.assertIn(fact, text)


if __name__ == '__main__':
    unittest.main()
