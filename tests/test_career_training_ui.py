import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import observer
from observer_career_training import panel
class TrainingUI(unittest.TestCase):
    def test_comparison_is_visible_evidence_not_ceiling(self):
        v={'golfer':{'id':1,'attrs_exact':{'power':60,'short_putting':45},'ceilings':{'short_putting':99.999}},
           'scouting':{'categories':[{'category':'putting','grade':'B','confidence':'low','explanation':'Limited observations'}]},
           'recaps':[{'year':2030,'weeks':[{'week':1,'golfer_id':1,'activity':'train','training_category':'putting',
             'development_recorded':True,'development':{'training':{'overall':.03}}}]}]}
        before=copy.deepcopy(v);html=panel(v)
        self.assertEqual(v,before)
        self.assertIn('45.0',html);self.assertIn('Estimated potential B',html)
        self.assertIn('+0.030 overall',html);self.assertNotIn('99.999',html)
        self.assertIn('not automatically the best investment',html)
        self.assertIn('not exact remaining growth',html)
    def test_missing_data_does_not_invent_comparison(self):
        self.assertEqual(panel({'golfer':{}}),'')
    def test_former_golfer_training_not_attributed_to_current(self):
        v={'golfer':{'id':2,'attrs_exact':{'power':50}},'recaps':[{'year':2030,'weeks':[{'week':1,'golfer_id':1,'activity':'train'}]}]}
        self.assertIn('No recent controlled-week history',panel(v))
