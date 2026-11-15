import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import observer
from observer_career_cycle import panel

class CareerCycle(unittest.TestCase):
    def view(self):
        return {'status':'active','golfer':{'fatigue':.3,'injured_until':None},'pending':[],
                'plannable':[[2029,5]],'context':{'upcoming':[{'week':8,'tier':6,'event_id':'2029:A','name':'A <Cup>','status':'Selection rules apply'}]}}
    def test_factual_cycle_for_struggling_golfer(self):
        r={'start_week':1,'end_week':4,'weeks':[{'events':[{'position':None,'name':'Event'}]}]}
        html=panel(self.view(),[r])
        self.assertIn('1 recorded tournament starts',html)
        self.assertIn('Fatigue is above',html)
        self.assertIn('Selection rules apply',html)
        self.assertIn('A &lt;Cup&gt;',html)
        self.assertNotIn('qualified',html)
        self.assertIn('block=2029-5',html)
    def test_current_choice_not_assumed_at_annual_boundary(self):
        v=self.view();v['year_end']={'stage':'season_review'}
        self.assertEqual(panel(v,[]),'')
    def test_pending_choice_points_to_inbox(self):
        v=self.view();v['pending']=[{'kind':'coach_offer'}]
        html=panel(v,[])
        self.assertIn('1 decision awaiting you',html)
        self.assertIn('#career-inbox',html)
        self.assertNotIn('block=2029-5',html)

    def test_cycle_is_read_only_and_repeatable(self):
        import copy
        v=self.view();before=copy.deepcopy(v)
        self.assertEqual(panel(v,[]),panel(v,[]))
        self.assertEqual(v,before)
