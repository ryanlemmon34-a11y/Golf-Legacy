import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import unittest,copy
from observer_career_estimates import growth,entry

class Estimates(unittest.TestCase):
    def test_room_uncertainty_and_observations(self):
        r={'growth_room':{'label':'some','uncertainty':'wide','basis':['age_curve','coach_read'],'explanation':'Limited < evidence'},'evidence':{'observations':2,'span_weeks':4,'trend_available':False}}
        old=copy.deepcopy(r);h=growth(r)
        for t in ['Some estimated room','Uncertainty: wide','2 recorded observations','No dependable development trend','Limited &lt; evidence','not a known limit']:
            self.assertIn(t,h)
        self.assertEqual(old,r);self.assertEqual(h,growth(r))
    def test_old_data_unknown_not_inferred(self):
        self.assertIn('not assessed',growth({'grade':'A'}))
        self.assertIn('not assessed',growth({'growth_room':{'label':'unknown'}}))
    def test_all_entry_statuses_preserve_limits(self):
        for status in ['injured','not_eligible','cannot_afford','holds_place','rule_selected','quota_limited','open_last_time','near_capacity_last_time','ahead_of_last_cutoff','at_last_cutoff','behind_last_cutoff','unknown']:
            r={'status':status,'label':status.replace('_',' '),'your_class_label':'home amateur','reason':'Recorded comparison','uncertainty':'Other applicants are not known'}
            old=copy.deepcopy(r);h=entry(r)
            self.assertIn('No numerical admission probability',h);self.assertIn('Other applicants',h)
            self.assertNotIn('%',h);self.assertEqual(old,r)
    def test_missing_entry_and_escaping(self):
        self.assertIn('unavailable',entry(None))
        self.assertIn('&lt;test&gt;',entry({'label':'<test>'}))
