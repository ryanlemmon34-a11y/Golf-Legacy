"""National prestige: visible achievement first, ability-relative overperformance second (rules 2026-11-14).

Each starter earns the fame of their finish (A) and is credited with two baselines: what they were expected to take
given current ability (E, unchanged) and an even share of the site's fame, ability ignored (P). Over five seasons:
    Q = (A5 + 150) / (P5 + 150)       visible achievement: fame won per fame on offer in the starts made
    R = (A5 + 150) / (E5 + 150)       overperformance: against an ability-based expectation
    prestige = 50 + 25 x (2/3 log2 Q + 1/3 log2 R), within 0-100
The components are tested separately here, then together; the population rule, the multiplier bounds and the
yearly step are untouched. Worlds saved before the rule keep R alone.

Run from the project folder:  python -m unittest tests.test_nation_achievement -v
"""
from __future__ import annotations

import math
import pickle
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import participation as PT                                   # noqa: E402
from golfsim import rules as R                                            # noqa: E402
from golfsim.nations import nations                                       # noqa: E402

W = PT.ACHIEVEMENT_WEIGHT


def q_only(a, p):
    return (a + PT.NATION_PSEUDO) / (p + PT.NATION_PSEUDO)


class Components(unittest.TestCase):
    def test_even_share_is_ability_free_and_sums_to_the_fame_on_offer(self):
        pt = PT.Participation(nations(), 2027)
        rows = [('Argentina', 96.0, 100.0), ('USA', 70.0, 5.0), ('USA', 65.0, 1.0), ('Fiji', 60.0, 0.0)]
        pt.note_site(2030, rows)
        b = pt.success[2030]
        self.assertAlmostEqual(sum(v[2] for v in b.values()), 106.0)         # P totals the fame handed out
        self.assertAlmostEqual(b['USA'][2], 2 * 106.0 / 4)                   # two starts: two even shares
        self.assertAlmostEqual(b['Argentina'][2], 106.0 / 4)                 # the favourite: the same even share
        self.assertGreater(b['Argentina'][1], b['Argentina'][2])             # E: ability made him the favourite
        self.assertAlmostEqual(sum(v[0] for v in b.values()), sum(v[1] for v in b.values()))   # A and E: zero-sum

    def test_achievement_alone_and_overperformance_alone(self):
        # visible achievement with nothing beyond expectation: Q > 1, R = 1
        p, r, q = PT.nation_prestige_achievement([(900.0, 900.0, 300.0)] * 5)
        self.assertAlmostEqual(r, 1.0)
        self.assertAlmostEqual(q, q_only(900 * 4, 300 * 4))
        self.assertAlmostEqual(p, 50 + 25 * W * math.log2(q))
        # overperformance with only an even share of fame won: Q = 1, R > 1
        p, r, q = PT.nation_prestige_achievement([(300.0, 100.0, 300.0)] * 5)
        self.assertAlmostEqual(q, 1.0)
        self.assertAlmostEqual(p, 50 + 25 * (1 - W) * math.log2(r))
        # neither: exactly 50
        self.assertAlmostEqual(PT.nation_prestige_achievement([(50.0, 50.0, 50.0)] * 5)[0], 50.0)
        self.assertEqual(PT.nation_prestige_achievement([])[0], 50.0)

    def test_volume_alone_does_not_raise_achievement(self):
        """Twice the starters of the same quality: twice the fame and twice the fame on offer -- Q stays put
        (up to the pseudo-count, which only steadies small samples)."""
        _, _, q1 = PT.nation_prestige_achievement([(2000.0, 2000.0, 1000.0)] * 5)
        _, _, q2 = PT.nation_prestige_achievement([(4000.0, 4000.0, 2000.0)] * 5)
        self.assertAlmostEqual(q1, q2, delta=0.06)
        self.assertLess(abs(math.log2(q2) - math.log2(q1)), 0.05)
        # and an average nation entering more stays average
        self.assertAlmostEqual(PT.nation_prestige_achievement([(3000.0, 3000.0, 3000.0)] * 5)[0], 50.0)

    def test_historic_champion_is_not_cancelled_by_an_unattainable_expectation(self):
        """Argentina 2055 (all four majors): actual 920.93 against an expected 939.10. R alone sits just below 50;
        visible achievement lifts it well above."""
        a, e, p_on_offer = 920.93, 939.10, 250.0          # (on offer: a few dozen starts; the replay has the real figure)
        old = PT.nation_prestige([(a, e)] * 5)[0]
        new = PT.nation_prestige_achievement([(a, e, p_on_offer)] * 5)[0]
        self.assertLess(old, 50.0)
        self.assertGreater(new, 70.0)

    def test_small_breakthrough_and_ordinary_decline(self):
        # one major win from a handful of starts (fame ~86 won from ~3 on offer), the rest of the window quiet
        brk = PT.nation_prestige_achievement([(86.0, 4.0, 3.0), (0.5, 1.0, 2.0), (0.0, 1.0, 2.0)])
        self.assertGreater(brk[0], 55.0)
        self.assertLess(brk[0], 75.0)                     # steadied by the pseudo-count: not an instant maximum
        # a nation taking well under an even share of what it enters, as expected for its ability: declines
        dec = PT.nation_prestige_achievement([(200.0, 220.0, 600.0)] * 5)
        self.assertLess(dec[0], 45.0)
        # and one falling short of a realistic expectation too: declines further
        self.assertLess(PT.nation_prestige_achievement([(200.0, 600.0, 600.0)] * 5)[0], dec[0])

    def test_bounds(self):
        self.assertEqual(PT.nation_prestige_achievement([(1e9, 1.0, 1.0)])[0], 100.0)
        self.assertEqual(PT.nation_prestige_achievement([(0.0, 1e9, 1e9)])[0], 0.0)


class ObserverText(unittest.TestCase):
    """The nation page says what prestige measures: achievement and expectation when the season recorded them, the
    earlier wording for seasons settled before rules 2026-11-14."""

    def page(self, nations):
        from unittest import mock
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
        import observer_prestige as OP
        recs = {2030: {'nations': nations}}
        with mock.patch.object(OP, '_years', lambda w: [2030]), mock.patch.object(OP, '_record', lambda w, y: recs[y]), \
                mock.patch.object(OP, '_live', lambda w: None):
            return OP.nation_section(object(), 'Argentina')

    def test_achievement_shown_with_its_explanation(self):
        n = {'prestige': {'Argentina': 73.6}, 'ratio': {'Argentina': 0.789}, 'achievement': {'Argentina': 3.002},
             'multiplier': {'Argentina': 1.92}, 'shares': {'juniors': {'Argentina': 0.0187}, 'new_pros': {}},
             'allocated': {'juniors': {'Argentina': 6}}}
        html = self.page(n)
        self.assertIn('>Achievement</th>', html)
        self.assertIn('>Against expectation</th>', html)
        self.assertIn('<td class=n>3.002</td><td class=n>0.789</td>', html)
        self.assertIn('Visible success first', html)
        self.assertNotIn('exactly the success expected', html)

    def test_a_season_settled_before_keeps_the_earlier_wording(self):
        n = {'prestige': {'Argentina': 41.5}, 'ratio': {'Argentina': 0.789}, 'multiplier': {'Argentina': 0.79},
             'shares': {'juniors': {'Argentina': 0.0076}, 'new_pros': {}}}
        html = self.page(n)
        self.assertNotIn('>Achievement</th>', html)
        self.assertIn('exactly the success expected', html)


class InTheWorld(unittest.TestCase):
    def test_close_season_uses_achievement_and_records_it(self):
        pt = PT.Participation(nations(), 2027)
        pt.note_site(2027, [('Argentina', 96.0, 400.0)] + [('USA', 70.0, 1.0)] * 9)
        pt.close_season(2027)
        h = pt.history[2028]
        self.assertGreater(h['achievement']['Argentina'], 1.0)
        self.assertLess(h['achievement']['USA'], 1.0)
        self.assertEqual(len(h['season']['Argentina']), 3)                  # [actual, expected, on offer]
        self.assertIn('achievement', pt.view())
        self.assertGreater(pt.prestige['Argentina'], pt.prestige['USA'])
        # bounds and the yearly step unchanged
        self.assertLessEqual(pt.multiplier['Argentina'], PT.MULT_STEP + 1e-12)
        self.assertGreaterEqual(pt.multiplier['USA'], 1 / PT.MULT_STEP - 1e-12)

    def test_saves_from_before_keep_the_ratio_alone(self):
        pt = PT.Participation(nations(), 2027)
        st = dict(pt.__dict__)
        for k in ('achievement_on', 'achievement'):
            st.pop(k)
        old = PT.Participation.__new__(PT.Participation)
        old.__setstate__(st)
        self.assertFalse(old.achievement_on)
        old.success[2027] = {'Argentina': [920.93, 939.10]}                 # a season recorded before the rule
        old.close_season(2027)
        self.assertAlmostEqual(old.prestige['Argentina'], PT.nation_prestige([(920.93, 939.10)])[0])
        self.assertNotIn('achievement', old.history[2028])
        self.assertTrue(pickle.loads(pickle.dumps(pt)).achievement_on)

    def test_a_season_begun_before_the_rule_is_read_with_its_expectation(self):
        pt = PT.Participation(nations(), 2027)
        pt.success[2027] = {'Fiji': [500.0, 50.0]}                          # two values: no fame on offer kept
        pt.close_season(2027)
        p, r, q = PT.nation_prestige_achievement([(500.0, 50.0, 50.0)])
        self.assertAlmostEqual(pt.prestige['Fiji'], p)

    def test_versioned(self):
        self.assertGreaterEqual(R.RULES_VERSION, '2026-11-14')
        self.assertIn('2026-11-14', dict(R.VERSIONS))


if __name__ == '__main__':
    unittest.main()
