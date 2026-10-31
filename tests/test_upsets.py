"""Biggest Upsets (roadmap B1/B2): the pre-event estimate model (upset-model-1), its recording in the simulation
and the archive, and the observer's Upsets page.

Quick unit tests (no world, no season): run from the project folder
    python -m unittest tests.test_upsets -v
The whole-season check that recording changes no outcome is HeavyEquivalenceTests, run only when asked:
    GOLF_HEAVY_TESTS=1 python -m unittest tests.test_upsets.HeavyEquivalenceTests -v
"""
from __future__ import annotations

import copy
import json
import math
import os
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import upsets as UP                                      # noqa: E402
from golfsim.course import ashford_ridge                               # noqa: E402
from golfsim.golfer import ARCHETYPES, archetype_golfer, uniform_golfer   # noqa: E402


def balance_field():
    """The balance report's upset-test field (tools/balance_test.py section 6), rebuilt from its seed."""
    rng = random.Random(77)
    field, names, idx = [], list(ARCHETYPES), 0
    for ov, count in [(88, 2), (84, 4), (80, 14), (77, 30), (74, 44), (71, 30), (67, 20)]:
        for _ in range(count):
            o = ov + rng.uniform(-1.5, 1.5)
            g = archetype_golfer(names[idx % len(names)], round(o, 1), name=f'P{idx:03d}')
            g.personality['big_stage'] = rng.uniform(20, 80)
            field.append(g)
            idx += 1
    return field


class ModelTests(unittest.TestCase):
    def test_version_and_sum(self):
        self.assertEqual(UP.VERSION, 'upset-model-1')
        ps = UP.win_probabilities([70, 75, 80, 60, 72.5], 4)
        self.assertAlmostEqual(sum(ps), 1.0, places=12)
        self.assertTrue(all(p > 0 for p in ps))

    def test_deterministic(self):
        rng = random.Random(3)
        ovs = [rng.uniform(40, 85) for _ in range(150)]
        a = UP.estimate(list(enumerate(ovs, 1)), 4)
        b = UP.estimate(list(enumerate(ovs, 1)), 4)
        self.assertEqual(a, b)
        # the field's order does not change anyone's chance
        rev = UP.estimate(list(reversed(list(enumerate(ovs, 1)))), 4)
        self.assertEqual(a['p'], rev['p'])

    def test_uses_no_random_numbers(self):
        state = random.getstate()
        UP.estimate([(1, 70.0), (2, 75.0), (3, 80.0)], 4)
        self.assertEqual(random.getstate(), state)

    def test_monotonic_in_overall(self):
        ps = UP.win_probabilities([60, 65, 70, 75, 80, 85], 4)
        self.assertEqual(ps, sorted(ps))

    def test_ties_share_a_chance_and_rank(self):
        pre = UP.estimate([(5, 75.0), (2, 75.0), (9, 70.0)], 4)
        self.assertEqual(pre['p'][5], pre['p'][2])
        facts = lambda g: {'status': 'pro', 'age': 30, 'wr': None, 'ar': None}
        rec = UP.record(pre, 5, facts)
        self.assertEqual(rec['rank'], 1)
        self.assertEqual(rec['favourite'], 2)                   # equal chances: the lower person id first
        self.assertEqual([g for g, _ in rec['top']], [2, 5, 9])

    def test_missing_overall_is_the_fields_lowest(self):
        a = UP.estimate([(1, 80.0), (2, None), (3, 60.0)], 4)
        b = UP.estimate([(1, 80.0), (2, 60.0), (3, 60.0)], 4)
        self.assertEqual(a['p'], b['p'])
        self.assertIsNone(a['overall'][2])
        rec = UP.record(a, 2, lambda g: {})
        self.assertEqual(rec['overall_rank'], 3)                # unknown Overall ranks last

    def test_degenerate_fields(self):
        self.assertEqual(UP.win_probabilities([], 4), [])
        self.assertEqual(UP.win_probabilities([42.0], 4), [1.0])
        self.assertFalse(UP.estimate([], 4)['estimated'])
        mp = UP.estimate([(1, 70.0), (2, 71.0)], 0, match_play=True)
        self.assertFalse(mp['estimated'])
        self.assertIn('match play', mp['why'])
        self.assertEqual(UP.record(mp, 1, lambda g: {}), {'model': UP.VERSION, 'estimated': False, 'why': mp['why']})

    def test_large_and_weak_fields(self):
        # one 75 among 155 others of 75: about 1 in 156; the same golfer against a field of 45s: a strong favourite
        big = UP.win_probabilities([75.0] * 156, 4)
        self.assertAlmostEqual(big[0], 1 / 156, delta=1e-9)
        weak = UP.win_probabilities([75.0] + [45.0] * 30, 4)
        self.assertGreater(weak[0], 0.85)
        self.assertGreater(weak[0], 100 * max(weak[1:]))
        # a 60 beating a field of 80s is a huge upset; a 60 beating 40s is not
        self.assertLess(UP.win_probabilities([60.0] + [80.0] * 40, 4)[0], 1e-4)        # (an even chance: 1 in 41)
        self.assertGreater(UP.win_probabilities([60.0] + [40.0] * 40, 4)[0], 0.3)        # (over 12 times an even share)
        # more rounds favour the better golfer
        self.assertGreater(UP.win_probabilities([80.0, 75.0], 4)[0], UP.win_probabilities([80.0, 75.0], 1)[0])
        # very small chances stay representable (an extreme upset is ranked, not lost as zero)
        tiny = UP.win_probabilities([20.0] + [85.0] * 100, 4)[0]
        self.assertGreater(tiny, 0.0)
        self.assertLess(tiny, 1e-12)

    def test_calibration_against_the_balance_report(self):
        """Model 1 against the engine's measured upset test (reports/BALANCE_REPORT.md section 6): per-start win
        chances by Overall band within a factor that allows for its sampling noise."""
        field = balance_field()
        ovs = [g.overall for g in field]
        ps = UP.win_probabilities(ovs, 4)
        measured = {(86, 100): 0.1545, (82, 86): 0.0430, (78, 82): 0.0123, (75, 78): 0.0046, (72, 75): 0.0020}
        for (lo, hi), m in measured.items():
            got = [p for o, p in zip(ovs, ps) if lo <= o < hi]
            mean = sum(got) / len(got)
            self.assertLess(abs(math.log(mean / m)), math.log(1.25), (lo, hi, mean, m))

    def test_odds_text(self):
        self.assertEqual(UP.odds_text(0.123), '12.3%')
        self.assertEqual(UP.odds_text(0.0004), '1 in 2,500')
        self.assertEqual(UP.odds_text(None), 'not recorded')


class NoHindsightTests(unittest.TestCase):
    def test_record_leaves_the_estimate_unchanged(self):
        pre = UP.estimate([(1, 80.0), (2, 70.0), (3, 65.0)], 4)
        before = copy.deepcopy(pre)
        rec = UP.record(pre, 3, lambda g: {'status': 'amateur', 'age': 19, 'wr': None, 'ar': 4})
        self.assertEqual(pre, before)
        self.assertEqual(rec['p'], pre['p'][3])
        self.assertEqual(rec['rank'], 3)
        self.assertEqual(rec['winner_facts']['status'], 'amateur')
        # the same estimate whoever wins: only the lookup differs
        self.assertEqual(UP.record(pre, 1, lambda g: {})['top'], rec['top'])

    def test_play_site_estimate_is_made_before_play_and_changes_nothing(self):
        """The worker's estimate is computed from the field before any shot, uses no random numbers and leaves
        the result exactly as without it (a tiny one-round event: a unit test, not a simulation run)."""
        from golfsim.season import play_site
        golfers = []
        for i, ov in enumerate((80, 74, 68, 62), 1):
            g = uniform_golfer(ov, name=f'G{i}')
            g.id = i
            golfers.append(g)
        task = {'event_id': '2027:TEST', 'site': 0, 'course': ashford_ridge(), 'golfers': golfers,
                'match_play': False, 'caddies': [], 'rounds': 1, 'cut_top': 0, 'prestige': 50, 'seed': 12345}
        ratings = [dict(g.attrs) for g in golfers]
        off = play_site(dict(task, estimate=False))
        on = play_site(dict(task, estimate=True))
        est = on.pop('estimate')
        self.assertNotIn('estimate', off)
        self.assertEqual(json.dumps(on, sort_keys=True, default=str), json.dumps(off, sort_keys=True, default=str))
        self.assertEqual(est, UP.estimate([(g.id, g.overall) for g in golfers], 1))
        self.assertEqual([dict(g.attrs) for g in golfers], ratings)
        self.assertEqual(est['rounds'], 1)


@unittest.skipUnless(os.environ.get('GOLF_HEAVY_TESTS') == '1', 'whole-season run: set GOLF_HEAVY_TESTS=1')
class HeavyEquivalenceTests(unittest.TestCase):
    """Same seed, recording on and off: every outcome identical (results, statistics, rankings, money, records)."""

    def test_recording_changes_no_outcome(self):
        from golfsim.population import generate_world
        from golfsim.season import Season
        import equivalence_check as EQ
        weeks = int(os.environ.get('GOLF_HEAVY_WEEKS', '8'))

        def run(on):
            s = Season(generate_world(seed=2027), seed=2027, workers=2)
            s.upset_estimates = on
            eds = s.cal.editions(2027)
            for w in range(1, weeks + 1):
                s.run_week(2027, w, [e for e in eds if e.week == w])
            s.close()
            return s

        a, b = run(True), run(False)
        self.assertEqual([(e, r.finish, r.playoff) for e, r in sorted(a.results.items())],
                         [(e, r.finish, r.playoff) for e, r in sorted(b.results.items())])
        for part in ('pstats', 'records', 'moments', 'history', 'wr_pos', 'am_pos', 'ledgers'):
            x, y = getattr(a, part), getattr(b, part)
            x, y = (x.to_dict(), y.to_dict()) if hasattr(x, 'to_dict') else (x, y)
            self.assertEqual(EQ.digest(EQ.canon(x)), EQ.digest(EQ.canon(y)), part)
        self.assertEqual([(g.id, sorted(g.attrs.items()), g.cash) for g in a.world.golfers],
                         [(g.id, sorted(g.attrs.items()), g.cash) for g in b.world.golfers])
        got = [r.upset for r in a.results.values() if r.upset and r.upset.get('estimated')]
        self.assertTrue(got)
        self.assertTrue(all(r.upset is None for r in b.results.values()))


if __name__ == '__main__':
    unittest.main()
