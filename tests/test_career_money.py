"""The career's money read model (golfsim.career_money) and the annual summary: records and the engine's formulas.

Run from the project folder:  python -m unittest tests.test_career_money -v
"""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import career_fixture as F                                             # noqa: E402
from test_careertest2_fixes import Copy, act, started                 # noqa: E402
from golfsim import career as CA                                       # noqa: E402
from golfsim import career_money as CM                                 # noqa: E402


class Money(unittest.TestCase):
    def test_trace_and_rules(self):
        with Copy() as s:
            g = started(s)
            se = s.season
            s.advance_career('next', op_key='a')
            for d in se.career.pending(CA.OFFER_KINDS):
                act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, f'o{d["id"]}')
            act(s, {'type': 'plan_block', 'block': [2028, 1], 'version': se.career.version,
                    'weeks': {str(w): {'kind': 'rest'} for w in CA.open_weeks(s.cursor, 1)},
                    'policy': {'selected': 'accept', 'qualifying': 'skip'}}, 'p')
            s.advance_career('period', op_key='b')
            before, state = F.digest(s), random.getstate()
            m = CA.view(se, s.cursor)['money']
            self.assertEqual(F.digest(s), before)
            self.assertEqual(random.getstate(), state)
            self.assertEqual(m['funds']['spendable'], round(se.spendable(g, 2028), 2))
            led = m['seasons']['2028']
            if se.ledgers.get(2028, {}).get(g.id) is None:
                self.assertIsNone(led)                                  # nothing booked: null, not zeros invented
                se.spend(g, 2028, 'living', 100.0)                       # (test set-up: one booked cost)
                led = CA.view(se, s.cursor)['money']['seasons']['2028']
            self.assertAlmostEqual(sum(led['income'].values()), led['total_income'], places=1)
            self.assertAlmostEqual(sum(led['costs'].values()), led['total_costs'], places=1)
            self.assertAlmostEqual(led['total_income'] - led['total_costs'], led['net'], places=1)
            self.assertGreater(led['total_costs'], 0)
            self.assertEqual(set(m['labels']), set(CM.LINES_IN) | set(CM.LINES_OUT))
            if g.status != 'pro':
                self.assertEqual(m['sponsor']['contract'], 0.0)
                self.assertIn('amateurs', m['sponsor']['rule'])
            self.assertEqual(m['backer']['deal'], round(g.backer or 0.0, 2))
            rows = CA.view(se, s.cursor)['seasons_summary']
            self.assertEqual([(r['year'], r['recorded_weeks']) for r in rows], [(2028, 4)])


if __name__ == '__main__':
    unittest.main()
