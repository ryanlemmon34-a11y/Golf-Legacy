"""Entry outlook (golfsim/entry_outlook.py; docs/career/ENTRY_OUTLOOK.md): qualitative guidance from the golfer's entry
class now and how the field closed last edition -- never a percentage, never this year's entrants; `unknown` with a
reason when the facts do not support a judgement. Read only.

On the career fixture world (seed 11, scale 0.05) at 1 January 2028 (2027's field history recorded).

Run from the project folder:  python -m unittest tests.test_entry_outlook -v
"""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import career_fixture as F                                             # noqa: E402
from test_careertest2_fixes import Copy                                # noqa: E402
from golfsim import entry_outlook as EO                                # noqa: E402


class Outlook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cm = Copy()
        cls.s = cls.cm.__enter__()
        cls.se = se = cls.s.season
        se.year = 2028
        cls.g = next(g for g in se.active_golfers() if g.status == 'pro' and g.tour and any(
            se.eligible(g, e.series, e.week) and not se.is_special(e.series) and se.priority(g, e.series)[0] not in (19,)
            and e.series.series_id in se.field_cutoffs.get(2027, {}) for e in se.cal.editions(2028)))
        # an ordinary event of 2028 the golfer may enter, not a quota case, with a 2027 record
        for ed in se.cal.editions(2028):
            s = ed.series
            if (not se.is_special(s) and se.eligible(cls.g, s, ed.week) and s.series_id in se.field_cutoffs.get(2027, {})
                    and se.priority(cls.g, s)[0] != 19 and not se._visitor(cls.g.id, s)):
                cls.ed = ed
                break
        cls.sid = cls.ed.series.series_id
        cls.cls = se.priority(cls.g, cls.ed.series)[0]

    @classmethod
    def tearDownClass(cls):
        cls.cm.__exit__(None, None, None)

    def ask(self, row=None, **kw):
        row = dict({'event_id': self.ed.event_id, 'eligible': True, 'affordable': True}, **(row or {}))
        return EO.outlook(self.se, self.g, 2028, self.ed.week, row, **kw)

    def with_record(self, **rec):
        fc = self.se.field_cutoffs[2027]
        old = fc[self.sid]
        fc[self.sid] = dict(old, **rec)
        try:
            return self.ask()
        finally:
            fc[self.sid] = old

    def test_rule_facts_first(self):
        self.assertEqual(self.ask(injured=(2028, 9))['status'], 'injured')
        self.assertEqual(self.ask({'eligible': False, 'why': 'members only'})['status'], 'not_eligible')
        self.assertEqual(self.ask({'affordable': False, 'why': 'costs $900'})['status'], 'cannot_afford')
        r = self.ask({'rule': 'field chosen by the event\'s rules'}, held={})
        self.assertEqual(r['status'], 'rule_selected')
        self.assertIn('does not mean being selected', r['reason'])
        held = {(self.sid, 2028): [{'code': 'X1', 'label': 'Test exemption', 'amateur_only': False}]}
        r = self.ask({'rule': 'field chosen by the event\'s rules'}, held=held)
        self.assertEqual((r['status'], r['reason']), ('holds_place', 'Recorded: Test exemption.'))

    def test_against_last_edition(self):
        cap = self.se.field_cutoffs[2027][self.sid]['capacity']
        self.assertEqual(self.with_record(full=False, asked=cap // 4)['status'], 'open_last_time')
        self.assertEqual(self.with_record(full=False, asked=cap)['status'], 'near_capacity_last_time')
        for cut, want in ((self.cls + 1, 'ahead_of_last_cutoff'), (self.cls, 'at_last_cutoff'),
                          (self.cls - 1, 'behind_last_cutoff')):
            r = self.with_record(full=True, asked=2 * cap, admitted=cap, last_class=cut)
            self.assertEqual(r['status'], want)
            self.assertEqual(r['your_class'], self.cls)
            self.assertEqual(r['last_edition']['year'], 2027)
        r = self.with_record(full=True, last_class=None)
        self.assertEqual(r['status'], 'unknown')
        self.assertIn('not recorded', r['reason'])

    def test_unknown_without_history(self):
        fc = self.se.field_cutoffs
        saved = fc.pop(2027)
        try:
            r = self.ask()
        finally:
            fc[2027] = saved
        self.assertEqual(r['status'], 'unknown')
        self.assertIn('No previous edition', r['reason'])

    def test_quota_cases_give_no_judgement(self):
        se = self.se
        am = next(g for g in se.active_golfers() if g.status == 'amateur')
        ed = next(e for e in se.cal.editions(2028) if e.series.tier in (2, 3) and not se.is_special(e.series))
        r = EO.outlook(se, am, 2028, ed.week, {'event_id': ed.event_id, 'eligible': True, 'affordable': True})
        self.assertEqual(r['status'], 'quota_limited')

    def test_read_only_no_percentages(self):
        before = (F.digest(self.s), copy.deepcopy(self.se.field_cutoffs))
        out = []
        for g in self.se.active_golfers()[:150]:
            for ed in [e for e in self.se.cal.editions(2028) if e.week == self.ed.week][:6]:
                r = EO.outlook(self.se, g, 2028, ed.week, {'event_id': ed.event_id, 'eligible': True,
                                                           'affordable': True})
                self.assertIn(r['status'], EO.STATUSES)
                self.assertEqual(r['label'], EO.LABELS[r['status']])
                out.append(r)
        self.assertEqual((F.digest(self.s), self.se.field_cutoffs), before)
        for r in out:
            self.assertNotIn('%', r['reason'] + (r['uncertainty'] or ''))
            self.assertNotIn('probab', r['reason'].lower())


class InPlanner(unittest.TestCase):
    def test_every_play_row_has_an_outlook(self):
        from test_careertest2_fixes import started
        from golfsim import career as CA
        with Copy() as s:
            started(s)
            s.advance_career('next', op_key='a')
            v = CA.view(s.season, s.cursor)['week_compare']
            rows = [r for wk in v.values() for r in wk['play']]
            self.assertTrue(rows)
            for r in rows:
                self.assertIn(r['entry_outlook']['status'], EO.STATUSES)
                if r.get('selected_field'):
                    self.assertIn(r['entry_outlook']['status'], ('holds_place', 'rule_selected', 'injured'))


if __name__ == '__main__':
    unittest.main()
