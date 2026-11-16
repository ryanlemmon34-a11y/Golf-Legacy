import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import unittest
import copy
from observer_course_context import cue,panel

class CourseContext(unittest.TestCase):
    def test_absent_and_multisite(self):
        self.assertEqual(panel(None),'');self.assertEqual(cue(None),'')
        h=panel({'fit':None,'sites':4,'note':'Assigned later'})
        self.assertIn('not assigned',h);self.assertNotIn('Current-game fit',h)
    def test_actual_evidence_safe_and_repeatable(self):
        c={'course':'A < B','layout':'Championship','fit':.25,'familiarity_rounds':4.0,'familiarity':.2,'points':1.15,'factors':[{'category':'putting','demand':.8,'points':.25}],'note':'Not a forecast.'}
        before=copy.deepcopy(c);h=panel(c)
        for text in ['A &lt; B','+0.25','4</strong>','not tournament scoring','not predicted strokes']:
            self.assertIn(text,h)
        self.assertIn('4 course rounds',cue(c));self.assertEqual(c,before);self.assertEqual(h,panel(c))
    def test_planner_option_and_details_use_same_snapshot(self):
        import observer
        from observer_career import event_choice
        c={'course':'Test Links','layout':'Main','fit':.25,'familiarity_rounds':4,'familiarity':.2,'points':1.15,'factors':[],'note':'Not a forecast.'}
        o={'week':1,'injured_until':None,'events':[{'event_id':'2030:OPEN','name':'Open','eligible':True,'affordable':True,'cost':50,'city':'A','country':'B','tour':'Tour'}]}
        before=copy.deepcopy(o)
        h=event_choice(o,{}, {'play':[{'event_id':'2030:OPEN','course_fit':c}]})
        self.assertIn('fit +0.25',h);self.assertIn('Test Links',h)
        self.assertIn('4 course rounds',h);self.assertEqual(o,before)
