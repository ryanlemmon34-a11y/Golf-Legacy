"""Opportunities (what upcoming results unlock, by implemented rules) and the week comparison read model.

On the career fixture world (seed 11, scale 0.05); each test on its own temporary copy.

Run from the project folder:  python -m unittest tests.test_opportunities -v
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
from test_careertest2_fixes import Copy, started                       # noqa: E402
from golfsim import career as CA                                       # noqa: E402
from golfsim import decision_support as DS                             # noqa: E402
from golfsim import opportunities as O                                 # noqa: E402
from golfsim import qualification as Q                                 # noqa: E402

STATUSES = ('already_qualified', 'needs_result', 'awaiting_selection', 'not_eligible')


def find(opps, event, target):
    return [o for o in opps if o['event']['series_id'] == event and o['target']['series_id'] == target]


class Opportunities(unittest.TestCase):
    def test_routes_come_from_the_rules(self):
        with Copy() as s:
            g = started(s)
            se = s.season
            s.advance_career('next', op_key='a')
            opps = O.opportunities(se, g.id, 2028, 1)
            self.assertTrue(opps)
            codes = {r.code for rs in Q.rules_for(se.ctx.version).values() for r in rs}
            for o in opps:
                self.assertIn(o['status'], STATUSES)
                self.assertLess(o['event']['week'] + 0, 53)
                self.assertGreaterEqual((o['target']['year'], o['target']['week']),
                                        (o['event']['year'], o['event']['week']))   # unlocks something later
                rc = o['route']['code']
                self.assertTrue(rc in codes or rc.startswith(('STAGE_', 'TARGET_')), rc)
                for k in ('event', 'condition', 'target', 'route', 'status', 'restrictions', 'decided'):
                    self.assertIn(k, o)
            # the college champion's Tour Masters place (M16), next season, amateurs only, a win
            m16 = find(opps, 'COLLEGE_NATIONAL_CHAMPIONSHIP', 'TOUR_MASTERS')
            self.assertEqual(len(m16), 1)
            self.assertEqual((m16[0]['condition']['positions'], m16[0]['target']['year'], m16[0]['route']['code']),
                             ([1], 2029, 'M16'))
            self.assertTrue(any('amateur' in r for r in m16[0]['restrictions']))
            # the USA Amateur qualifier feeds the USA Amateur (week 33), not the national championship
            q = find(opps, 'USA_AMATEUR_QUALIFYING', 'USA_AMATEUR')
            self.assertEqual(len(q), 1)
            self.assertEqual(q[0]['target']['week'], 33)
            self.assertFalse(find(opps, 'USA_AMATEUR_QUALIFYING', 'NATIONAL_AMATEUR_USA'))
            # a top-N route states its N; ties included
            usa = find(opps, 'USA_OPEN', 'USA_OPEN')
            self.assertEqual((usa[0]['condition']['top'], usa[0]['target']['year']), (10, 2029))
            # selected fields are never claimed as entered
            self.assertEqual(m16[0]['status'] if g.tour.startswith('CO_US_D1') else 'awaiting_selection',
                             'awaiting_selection')
            self.assertEqual(find(opps, 'CLUB_PRO_SECTIONALS', 'CLUB_PRO_CHAMPIONSHIP')[0]['status'], 'not_eligible')

    def test_a_held_place_is_already_qualified(self):
        with Copy() as s:
            g = started(s)
            se = s.season
            s.advance_career('next', op_key='a')
            before = find(O.opportunities(se, g.id, 2028, 1), 'COLLEGE_NATIONAL_CHAMPIONSHIP', 'TOUR_MASTERS')
            self.assertNotEqual(before[0]['status'], 'already_qualified')
            se.ctx.results[('TOUR_MASTERS', 2027)] = {0: [(g.id, 1)]}     # (test set-up: a recorded Masters win:
            opps = O.opportunities(se, g.id, 2028, 1)                     # past champions are exempt for life)
            m = find(opps, 'COLLEGE_NATIONAL_CHAMPIONSHIP', 'TOUR_MASTERS')
            self.assertEqual(m[0]['status'], 'already_qualified')       # next season's Masters place already held

    def test_reads_change_nothing_and_draw_nothing(self):
        with Copy() as s:
            g = started(s)
            se, c = s.season, s.season.career
            s.advance_career('next', op_key='a')
            before, state = F.digest(s), random.getstate()
            a = O.opportunities(se, g.id, 2028, 1)
            w1 = DS.week_compare(se, c, g, 2028, 1)
            v = CA.view(se, s.cursor)
            for _ in range(2):
                self.assertEqual(O.opportunities(se, g.id, 2028, 1), a)
                self.assertEqual(DS.week_compare(se, c, g, 2028, 1), w1)
                self.assertEqual(CA.view(se, s.cursor)['opportunities'], v['opportunities'])
            self.assertEqual(F.digest(s), before)
            self.assertEqual(random.getstate(), state)


class WeekCompare(unittest.TestCase):
    def test_the_three_choices_side_by_side(self):
        with Copy() as s:
            g = started(s)
            se, c = s.season, s.season.career
            s.advance_career('next', op_key='a')
            w = DS.week_compare(se, c, g, 2028, 1)
            self.assertEqual({x['category'] for x in w['train']}, set(CA.CATEGORIES))
            ranks = sorted(x['weakest_rank'] for x in w['train'])
            self.assertEqual(ranks, [1, 2, 3, 4, 5])
            for x in w['train']:
                self.assertIn(x['grade'], ('A', 'B', 'C', 'D', 'F'))
            for k in ('fatigue', 'train_fatigue_after', 'rest_fatigue_after', 'played_last_4', 'played_last_8'):
                self.assertIn(k, w['load'])
            self.assertEqual(w['load']['played_last_4'], 0)
            for p in w['play']:
                self.assertIn('opportunities', p)
                for o in p['opportunities']:
                    self.assertEqual(o['event']['id'], p['event_id'])


if __name__ == '__main__':
    unittest.main()


class CommittedHook(unittest.TestCase):
    def test_the_view_carries_the_periods_comparisons(self):
        with Copy() as s:
            g = started(s)
            se, c = s.season, s.season.career
            s.advance_career('next', op_key='a')
            v = CA.view(se, s.cursor)['week_compare']
            self.assertEqual(list(v), [str(w) for w in CA.open_weeks(s.cursor, 1)])
            for w, x in v.items():
                self.assertEqual(x, DS.week_compare(se, c, g, 2028, int(w)))
