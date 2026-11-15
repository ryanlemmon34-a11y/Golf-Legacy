import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from tests.test_career_foundation import started
from golfsim import career as CA
import career_fixture as F
from observer_career_context import summary, panels

class CareerContext(unittest.TestCase):
    def test_committed_context_is_read_only_and_hides_potential(self):
        s = started('career_context')
        try:
            before = F.digest(s)
            v = CA.view(s.season, s.cursor)
            self.assertEqual(before, F.digest(s))
            self.assertEqual(v['context'], CA.view(s.season, s.cursor)['context'])
            raw = json.dumps(v['context'])
            self.assertNotIn('ceilings', raw)
            self.assertNotIn('potential', raw)
            self.assertEqual(v['context']['summary']['recorded_weeks'], 0)
            self.assertIn('0 recorded weeks', summary(v))
            html = panels(v)
            self.assertIn('not a confirmed entry', html)
            self.assertIn('Current playing rights', html)
            for row in v['context']['upcoming']:
                self.assertLessEqual(row['week'], v['context']['through_week'])
                self.assertIn(row['event_id'], {e.event_id for e in s.season.cal.editions(s.cursor['year'])})
        finally:
            s.close()

    def test_missing_context_is_not_invented(self):
        self.assertEqual(summary({}), '')
        self.assertEqual(panels({}), '')

    def test_display_escapes_and_labels_total_purse(self):
        v = {'golfer':{'tour':'<Tour>'}, 'context':{'through_week':12,'qualifications':[],
            'upcoming':[{'week':3,'event_id':'E','name':'<Event>','tour':'T','purse':1000,'status':'Eligible <maybe>'}]}}
        html = panels(v)
        self.assertIn('&lt;Event&gt;', html)
        self.assertIn('total purse; not your payout', html)
        self.assertIn('does not mean you are ineligible', html)

    def test_planner_defaults_and_saved_policy_are_distinct(self):
        from types import SimpleNamespace as NS
        from unittest.mock import patch
        import observer_career as UI
        p = {'weeks':[], 'policy':None, 'version':1}
        v = {'status':'active','plannable':[[2028,1]], 'golfer':{}, 'readiness':{}}
        w = NS(live=NS(career=v,career_planner={(2028,1):p}))
        with patch.object(UI, 'hidden', return_value=''), patch.object(UI,'readiness_card',return_value=''):
            _, html = UI.plan_page(w,{})
            self.assertIn('name="selected" value="accept" checked',html)
            self.assertIn('name="qualifying" value="enter" checked',html)
            p['policy'] = {'selected':'decline','qualifying':'skip'}
            _, html = UI.plan_page(w,{})
            self.assertIn('name="selected" value="decline" checked',html)
            self.assertIn('name="qualifying" value="skip" checked',html)
            self.assertNotIn('name="selected" value="accept" checked',html)

    def test_entry_evidence_is_visible_without_inventing_cutoff(self):
        from observer_career_context import entry_note, target_note
        html = entry_note({'recorded':True,'text':'Field full','event_label':'Test <event>',
                           'position':145,'applicants':180,'admitted':144,'capacity':144})
        self.assertIn('145 of 180 applicants',html)
        self.assertIn('144 admitted',html)
        self.assertIn('Test &lt;event&gt;',html)
        old = entry_note({'recorded':False,'text':'School lineup','position':999})
        self.assertNotIn('999',old)
        self.assertIn('were not recorded',old)
        route = target_note({'event_id':'2029:USA_AMATEUR_QUALIFYING',
                             'target':{'id':'USA_AMATEUR','label':'Open amateur','week':33}})
        self.assertIn('week 33',route)
        self.assertIn('not a confirmed',route)
