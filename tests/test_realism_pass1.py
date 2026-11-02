"""Realism pass 1 (golfsim/realism.py; docs/review/realism/PLAN.md): readiness at entry, attribute-specific aging and
the long-irons response. Paired, exact checks of what must not change, and property checks of what does.

Run from the project folder:  python -m unittest tests.test_realism_pass1 -v
"""
from __future__ import annotations

import copy
import math
import random
import statistics as S
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import development as D                                   # noqa: E402
from golfsim import population as P                                    # noqa: E402
from golfsim import ratings as R                                       # noqa: E402
from golfsim import realism as RZ                                      # noqa: E402
from golfsim.course import ashford_ridge                               # noqa: E402
from golfsim.engine import Conditions, Player, play_round              # noqa: E402
from golfsim.golfer import uniform_golfer                              # noqa: E402
from golfsim.nations import nations as starting_nations                # noqa: E402

COURSE = ashford_ridge()


def ident(g):
    return (g.id, g.name, g.country, g.born, g.peak_age, g.aging_rate, g.archetype, g.tour, g.status,
            tuple(sorted(g.personality.items())))


def age_year_dev1(g, age, rng, experience=1.0):
    """The 'dev-1' aging law exactly as released (main 18a8e23), kept here as the reference."""
    a, c = g.attrs, g.ceilings
    rate = g.aging_rate
    x_phys = age - (g.peak_age + 3)
    x_tech = age - (g.peak_age + 8)
    for k, cat in D.CATEGORY_OF.items():
        d = 0.0
        if cat == 'physical' and x_phys > 0:
            d = -0.30 * rate * x_phys ** 0.7
        elif cat in ('long_game', 'short_game', 'putting') and x_tech > 0:
            d = -0.15 * rate * x_tech ** 0.7
        elif cat == 'mental' or k == 'green_reading':
            if age < 48:
                d = 0.35 * (0.6 + 0.8 * rng.random()) * (1.0 if cat == 'mental' else 0.5) * \
                    (experience if cat == 'mental' else 0.5 + 0.5 * experience)
            elif age > 55:
                d = -0.2 * (age - 55) ** 0.7
        if d:
            a[k] = max(1.0, min(99.0, a[k] + d))
            c[k] = max(1.0, min(99.0, c[k] + d))
            if a[k] > c[k]:
                c[k] = a[k]


def golfer(gid=1, peak=27.0, aging=1.0, level=80.0, born=2000):
    g = uniform_golfer(level, work_ethic=60.0, coachability=60.0)
    g = replace(g, id=gid, born=born, peak_age=peak, aging_rate=aging, attrs=dict(g.attrs))
    g.ceilings = {k: min(99.0, v + 2.0) for k, v in g.attrs.items()}
    return g


class Readiness(unittest.TestCase):
    def test_the_floor_is_smooth_monotone_and_only_for_teenagers(self):
        for age in (18, 19):
            prev = None
            for h10 in range(0, 200):
                h = h10 / 10
                e = RZ.entry_overall(60 - h, 60, age)
                self.assertLessEqual(e, 60 - h)                          # never raises anyone
                if prev is not None:
                    self.assertLessEqual(e, prev + 1e-12)               # less headroom stays the higher level
                prev = e
            for pot in range(40, 99):                                    # a higher potential stays higher
                self.assertLess(RZ.entry_overall(pot - 3, pot, age), RZ.entry_overall(pot - 2, pot + 1, age))
        self.assertAlmostEqual(60 - RZ.entry_overall(60, 60, 18), 4.5, delta=0.05)   # at potential: ~4.5 to grow
        self.assertAlmostEqual(RZ.entry_overall(50, 60, 18), 50, delta=0.01)         # typical (10): untouched
        for age in (20, 21, 25, 40):
            self.assertEqual(RZ.entry_overall(59.5, 60, age), 59.5)

    def test_cohorts_counts_and_identities_are_exact(self):
        """The production junior class and new professionals under both rules: the same golfers (count, id, name,
        nation, peak age, aging rate, archetype, college or series, personality), exactly the same potential, new
        professionals entirely unchanged; only juniors' entry level moves, down,
        and only where headroom was short."""
        nations = starting_nations()
        for seed, year in ((11, 2031), (386509, 2036), (7, 2031), (11, 2044)):     # (incl. formerly-flipped routes)
            a = P.junior_class(year, seed, nations, 1, set(), rules=RZ.LEGACY)
            b = P.junior_class(year, seed, nations, 1, set(), rules=RZ.CURRENT)
            self.assertEqual([ident(g) for g in a], [ident(g) for g in b], (seed, year))
            for x, y in zip(a, b):
                self.assertEqual(x.potential, y.potential)
                self.assertLessEqual(y.overall, x.overall + 0.15)        # (attribute rounding)
                if x.potential - x.overall >= 9:
                    self.assertLess(abs(y.overall - x.overall), 0.15)
            short = [(x, y) for x, y in zip(a, b) if x.potential - x.overall < 1]
            self.assertTrue(short)
            for x, y in short:
                self.assertGreater(y.potential - y.overall, 3.5)
            na = P.new_professionals(year, seed, nations, 1, set(), rules=RZ.LEGACY)
            nb = P.new_professionals(year, seed, nations, 1, set(), rules=RZ.CURRENT)
            self.assertEqual([(ident(g), g.potential, g.attrs) for g in na], [(ident(g), g.potential, g.attrs) for g in nb])

    def test_a_full_size_new_world_keeps_every_initial_decision(self):
        """The full-size starting world (seed 2027) under both rules: every golfer keeps their identity, status, tour
        or college, lifestyle, money, backing, potential and personality, and everyone aged 20 or more keeps every
        attribute and ceiling, so the shared membership and career random streams are unchanged (an earlier draft
        assigned memberships on the lowered teenage ratings and moved four paths: reviewer probe of debb655).
        Only teenagers' attributes (lower entry, same potential) and their ceilings differ."""
        a = P.generate_world(seed=2027, dev_rules=RZ.LEGACY)
        b = P.generate_world(seed=2027)
        self.assertEqual((a.dev_rules, b.dev_rules), (RZ.LEGACY, RZ.CURRENT))
        self.assertEqual(len(a.golfers), len(b.golfers))
        self.assertGreater(len(a.golfers), 5000)

        def path(g):
            return (ident(g), g.status, g.tour, g.lifestyle, round(g.cash, 6), g.backing, g.backer,
                    getattr(g, 'backer_patience', None), g.potential, g.turned_pro, g.height_cm, g.hand, g.hometown)
        teens = 0
        for x, y in zip(a.golfers, b.golfers):
            self.assertEqual(path(x), path(y), x.name)
            if x.age(2027) >= 20:
                self.assertEqual((x.attrs, x.ceilings), (y.attrs, y.ceilings), x.name)
            else:
                teens += 1
                self.assertLessEqual(y.overall, x.overall + 0.15)
        self.assertGreater(teens, 100)
        named = {g.name: g for g in b.golfers}
        for name in ('Brett King', 'Stewart Whitaker', 'Syafiq Fernandez', 'Tariq Al Thani'):
            if name in named:                                                 # (the reviewer's four)
                old = next(g for g in a.golfers if g.id == named[name].id)
                self.assertEqual(named[name].tour, old.tour, name)

    def test_saves_from_before_play_the_rules_they_had(self):
        from golfsim.season import Season
        w = P.generate_world(seed=5, scale=0.02, dev_rules=RZ.LEGACY)
        del w.__dict__['dev_rules']                                       # a world pickled before the flag
        self.assertEqual(w.dev_rules, RZ.LEGACY)                         # (the class default)
        s = Season(w, seed=5, development=True, workers=1)
        self.assertEqual(s.dev_rules, RZ.LEGACY)
        state = dict(s.__getstate__())
        state.pop('dev_rules')
        t = Season.__new__(Season)
        t.__setstate__(state)
        self.assertEqual(t.dev_rules, RZ.LEGACY)
        self.assertEqual(Season(P.generate_world(seed=5, scale=0.02), seed=5, workers=1).dev_rules, RZ.CURRENT)


class Aging(unittest.TestCase):
    def test_dev1_is_unchanged(self):
        rng = random.Random(3)
        for _ in range(60):
            g = golfer(peak=rng.gauss(27, 2), aging=math.exp(rng.gauss(0, .3)), level=rng.uniform(40, 90))
            h = copy.deepcopy(g)
            for age in range(18, 70):
                D.age_year(g, age, random.Random(age), 0.7, rules=RZ.LEGACY)
                age_year_dev1(h, age, random.Random(age), 0.7)
                self.assertEqual((g.attrs, g.ceilings), (h.attrs, h.ceilings))
            g2 = copy.deepcopy(h)
            D.age_year(g2, 50, random.Random(1))                          # rules omitted: dev-1
            age_year_dev1(h, 50, random.Random(1))
            self.assertEqual(g2.attrs, h.attrs)

    def test_each_attribute_waits_for_its_own_onset(self):
        g = golfer(peak=27.0)
        before = dict(g.attrs)
        for age in range(19, 30):                                        # through peak + 2
            D.age_year(g, age, random.Random(age), 1.0, rules=RZ.CURRENT)
        for k in D.CATEGORY_OF:
            if k not in RZ.EXPERIENCE_KEYS and RZ.AGING[k][0] >= 3:
                self.assertEqual(g.attrs[k], before[k], k)                # nothing physical or technical lost yet
        D.age_year(g, 31, random.Random(31), 1.0, rules=RZ.CURRENT)       # peak + 4: physical only
        self.assertLess(g.attrs['power'], before['power'])
        self.assertEqual(g.attrs['chipping'], before['chipping'])

    def test_decline_is_stronger_individual_and_without_cliffs(self):
        """Physical decline beyond the prime is stronger than dev-1; a higher aging rate always costs more; the
        yearly decline grows smoothly with age (no step); the per-golfer factors average 1."""
        def run(rules, aging, gid=7):
            g = golfer(gid=gid, aging=aging, level=85)
            path = []
            for age in range(26, 61):
                D.age_year(g, age, random.Random(age), 1.0, rules=rules)
                path.append(dict(g.attrs))
            return path
        prof = RZ.profile(golfer(gid=7))
        new, old = run(RZ.CURRENT, 1.0 / prof['physical']), run(RZ.LEGACY, 1.0)   # (this golfer's factor removed)
        for at in (40, 45, 50):
            self.assertLess(new[at - 26]['power'], old[at - 26]['power'] - 1.0, at)
        for lo, hi in ((0.6, 0.8), (0.8, 1.0), (1.0, 1.4)):
            a, b = run(RZ.CURRENT, lo), run(RZ.CURRENT, hi)
            self.assertGreater(a[50 - 26]['power'], b[50 - 26]['power'])            # (at 50: above the 1.0 floor)
            self.assertGreater(a[50 - 26]['short_putting'], b[50 - 26]['short_putting'])
        drops = [new[i]['power'] - new[i + 1]['power'] for i in range(len(new) - 1)]
        steps = [drops[i + 1] - drops[i] for i in range(len(drops) - 1) if new[i + 2]['power'] > 1.5]
        self.assertLess(max(abs(s) for s in steps), 0.6)                  # the yearly loss changes gradually
        f = [RZ.profile(golfer(gid=i, born=1990 + i % 7))['physical'] for i in range(1, 4001)]
        self.assertAlmostEqual(S.mean(f), 1.0, delta=0.02)
        self.assertGreater(S.pstdev(f), 0.2)

    def test_green_reading_matures_with_experience_as_intended(self):
        """dev-1's putting branch shadowed green reading's experience growth after peak + 8 (it declined like a
        stroke); dev-2 lets it mature until 48 and decline only after 55, like the mental game."""
        g, h = golfer(peak=27.0, level=70), golfer(peak=27.0, level=70)
        for age in range(36, 48):
            D.age_year(g, age, random.Random(age), 1.0, rules=RZ.CURRENT)
            D.age_year(h, age, random.Random(age), 1.0, rules=RZ.LEGACY)
        self.assertGreater(g.attrs['green_reading'], 70.0)
        self.assertLess(h.attrs['green_reading'], 70.0)

    def test_part_of_physical_decline_is_conditioning_training_can_win_back(self):
        g = golfer(peak=27.0, level=80)
        g.ceilings = dict(g.attrs)
        D.age_year(g, 40, random.Random(1), 1.0, rules=RZ.CURRENT)
        gap = g.ceilings['power'] - g.attrs['power']
        lost = 80.0 - g.attrs['power']
        self.assertAlmostEqual(gap, RZ.MAINTAIN * lost, places=6)
        self.assertEqual(g.ceilings['chipping'], g.attrs['chipping'])    # technique: no conditioning gap
        was = g.attrs['power']
        for _ in range(10):
            D.develop_week(g, 'train', 40, 'physical', experience=1.0, gain=False)
        self.assertGreater(g.attrs['power'], was)
        self.assertLessEqual(g.attrs['power'], g.ceilings['power'])


class LongIrons(unittest.TestCase):
    def test_table_is_the_shared_one_except_inside_its_flat_range(self):
        self.assertEqual(R.APPROACH_MULT, ((0, 1.30), (10, 1.16), (25, 1.05), (40, 1.05), (50, 1.05), (60, 1.05),
                                           (75, 1.0), (85, 0.945), (90, 0.905), (100, 0.84)))   # mid irons, wedges
        for v10 in range(0, 1001):
            v = v10 / 10
            new, old = R.interp(R.LONG_IRON_MULT, v), R.interp(R.APPROACH_MULT, v)
            if v <= 10 or v >= 60:
                self.assertEqual(new, old, v)
            if 25 <= v < 60:
                step = new - R.interp(R.LONG_IRON_MULT, v + 0.1)
                self.assertAlmostEqual(step, 0.0001, delta=0.00002, msg=v)  # each point counts, by a little
        for v in range(1, 101):
            self.assertGreaterEqual(R.interp(R.LONG_IRON_MULT, v - 1), R.interp(R.LONG_IRON_MULT, v))

    def test_only_the_long_irons_parameter_moves(self):
        g = uniform_golfer(45)
        p = Player(g, COURSE, Conditions(), None, random.Random(0))
        self.assertEqual(p.m_mid, R.interp(R.APPROACH_MULT, g.attrs['mid_irons']))
        self.assertEqual(p.m_wedge, R.interp(R.APPROACH_MULT, g.attrs['wedges']))
        self.assertEqual(p.m_long, R.interp(R.LONG_IRON_MULT, g.attrs['long_irons']))

    def test_rounds_from_60_up_are_identical_and_below_60_respond(self):
        def rounds(g, table, n, seed):
            keep = R.LONG_IRON_MULT
            R.LONG_IRON_MULT = table
            try:
                return [play_round(g, COURSE, random.Random(seed * 100_003 + i)).score for i in range(n)]
            finally:
                R.LONG_IRON_MULT = keep
        new = R.LONG_IRON_MULT
        for li in (60, 68, 80, 95):
            g = replace(uniform_golfer(70), attrs={**uniform_golfer(70).attrs, 'long_irons': float(li)})
            self.assertEqual(rounds(g, new, 40, li), rounds(g, R.APPROACH_MULT, 40, li))
        base = uniform_golfer(50)
        weak = replace(base, attrs={**base.attrs, 'long_irons': 30.0})
        good = replace(base, attrs={**base.attrs, 'long_irons': 58.0})
        self.assertEqual(rounds(weak, R.APPROACH_MULT, 300, 1), rounds(good, R.APPROACH_MULT, 300, 1))   # dev-1: no
        self.assertGreater(S.mean(rounds(weak, new, 3000, 2)), S.mean(rounds(good, new, 3000, 2)))  # now: yes


if __name__ == '__main__':
    unittest.main()
