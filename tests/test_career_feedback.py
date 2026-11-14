"""Recorded career feedback is factual, persistent, and never changes simulation decisions."""
from __future__ import annotations
import json
import unittest
from unittest import mock
from tests.test_career_foundation import started, plan, golfer
import career_fixture as F
from golfsim import career as CA
from golfsim.session import Session


class CareerFeedback(unittest.TestCase):
    def test_record_training_rest_and_persist_without_changing_world(self):
        a = started('feedback')
        b = Session.open(F.copy_of(a.dir))
        year = a.cursor['year']
        weeks = {1: {'kind': 'train', 'category': 'putting'}, 2: {'kind': 'rest'},
                 3: {'kind': 'train', 'category': 'long_game'}, 4: {'kind': 'rest'}}
        for s in (a, b):
            plan(s, (year, 1), weeks)
            # Give feedback something observable without depending on random initial fatigue.
            s.season.fatigue[golfer(s).id] = golfer(s).fatigue = .4
        a.advance_career('period')
        with mock.patch.object(CA, 'begin_week_feedback', return_value=None):
            b.advance_career('period')
        self.assertEqual(F.digest(a), F.digest(b))
        v = CA.view(a.season, a.cursor)
        self.assertEqual(len(v['recaps']), 1)
        recap = v['recaps'][0]
        self.assertTrue(recap['complete'])
        self.assertEqual([r['activity'] for r in recap['weeks']], ['train', 'rest', 'train', 'rest'])
        self.assertEqual(recap['weeks'][0]['training_category'], 'putting')
        self.assertGreater(recap['development']['training']['overall'], 0)
        self.assertGreater(recap['development']['maturing']['overall'], 0)
        self.assertLess(recap['after']['fatigue'], recap['before']['fatigue'])
        self.assertAlmostEqual(recap['weeks'][1]['before']['overall'], recap['weeks'][0]['after']['overall'])
        self.assertNotIn('ceilings', json.dumps(recap))
        self.assertNotIn('potential', json.dumps(recap))
        path = a.dir
        saved = v['recaps']
        a.close()
        a = Session.open(path)
        self.assertEqual(saved, CA.view(a.season, a.cursor)['recaps'])
        a.close(); b.close()

    def test_old_career_has_no_fabricated_recap(self):
        s = started('old-feedback')
        del s.season.career.weekly_recaps
        self.assertEqual(CA.view(s.season, s.cursor)['recaps'], [])
        plan(s, (s.cursor['year'], 1))
        s.advance_one_week()
        r = CA.view(s.season, s.cursor)['recaps'][0]
        self.assertFalse(r['complete'])
        self.assertEqual(r['recorded_weeks'], [1])
        s.close()

    def test_event_evidence_preserves_rounds_and_unknown_old_values(self):
        from golfsim.season import EventResult
        s = started('event-feedback')
        g, y = golfer(s), s.cursor['year']
        ser = s.season.cal.series[0]
        before = CA.begin_week_feedback(s.season, y, 1)
        r = EventResult('feedback-event', ser.series_id, y, 1, [], [[(g.id, 2, 278)]], 40,
                        scores=[{g.id: [70, 69, 71, 68]}], prizes=[{g.id: 1234.5}])
        s.season.results[r.event_id] = r
        s.season.week_activity[g.id] = 'play'
        CA.finish_week_feedback(s.season, y, 1, before, [r.event_id])
        e = CA.period_recaps(s.season.career)[0]['weeks'][0]['events'][0]
        self.assertEqual((e['position'], e['score'], e['rounds'], e['prize']),
                         (2, 278, [70, 69, 71, 68], 1234.5))
        r.scores = []; r.prizes = []
        CA.finish_week_feedback(s.season, y, 1, before, [r.event_id])
        rows = CA.period_recaps(s.season.career)[0]['weeks']
        self.assertEqual(len(rows), 1)  # repeat records replace, never duplicate
        self.assertIsNone(rows[0]['events'][0]['rounds'])
        self.assertIsNone(rows[0]['events'][0]['prize'])
        rows[0]['after']['overall'] = -1
        self.assertNotEqual(CA.period_recaps(s.season.career)[0]['after']['overall'], -1)
        s.close()

    def test_readiness_uses_real_fatigue_formulas(self):
        s = started('readiness')
        g = golfer(s)
        s.season.fatigue[g.id] = .3
        r = CA.readiness(s.season, g, s.cursor['year'], 1)
        self.assertEqual(r['label'], 'Rest would help')
        self.assertAlmostEqual(r['rest_after'], .3 * (.4 + .3 * (1 - g.attrs['recovery_rate'] / 100)), places=3)
        self.assertAlmostEqual(r['train_after'], .85 * .3 + .02 * (1.4 - .8 * g.attrs['stamina'] / 100), places=3)
        self.assertLess(r['rest_after'], r['train_after'])
        s.season.fatigue[g.id] = 0
        r = CA.readiness(s.season, g, s.cursor['year'], 1)
        self.assertEqual(r['train_after'], 0)
        s.close()

if __name__ == '__main__':
    unittest.main()
