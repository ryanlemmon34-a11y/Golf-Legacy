import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import observer
from observer_career_legacy import panels,trophy_case,trophy_art,scouting_panel,GRADE_COLORS
from tests.test_career_color import luminance

class LegacyPresentation(unittest.TestCase):
    def award(self,year=2030):
        return {'event_id':str(year)+':MAJOR','event_name':'Legacy <Cup>','year':year,'winner_name':'Reed & Mann','kind':'major'}
    def test_no_snapshot_means_no_invented_feature(self):
        self.assertEqual(panels({}),'')
        self.assertIn('not available',trophy_case(None))
        self.assertIn('No qualifying',trophy_case([]))
    def test_engraving_is_in_svg_and_repeat_wins_survive(self):
        a,b=self.award(),self.award(2031)
        html=trophy_case([a,b])
        self.assertEqual(html.count('<svg'),2)
        self.assertIn('Reed &amp; Mann',html.split('</svg>')[0])
        self.assertIn('2030</text>',html)
        self.assertIn('2031</text>',html)
        self.assertIn('Legacy &lt;Cup&gt;',html)
    def test_art_has_accessible_title_and_unique_gradients(self):
        a=self.award()
        self.assertNotEqual(trophy_art(a,0),trophy_art(a,1))
        self.assertIn('role="img"',trophy_art(a))
        self.assertIn('<title',trophy_art(a))
    def test_scouting_is_estimate_and_never_displays_hidden_values(self):
        html=scouting_panel([{'category':'Short game','grade':'B','ceiling':99.987,'explanation':'Observed play'}])
        self.assertIn('Estimated potential',html)
        self.assertIn('not a promise',html)
        self.assertNotIn('99.987',html)
        self.assertIn('Not yet assessed',scouting_panel([{'category':'Putting','grade':'INVALID'}]))
    def test_grade_palette_contrast_and_letters(self):
        for grade,(fg,bg) in GRADE_COLORS.items():
            a,b=sorted((luminance(fg),luminance(bg)))
            self.assertGreaterEqual((b+.05)/(a+.05),4.5)
            self.assertIn('>'+grade+'</div>',scouting_panel([{'category':'Test','grade':grade}]))

    def test_presentation_never_changes_recorded_input(self):
        import copy
        v={'trophies':[self.award()], 'potential_estimates':[{'category':'Putting','grade':'C','confidence':'Low confidence'}]}
        before=copy.deepcopy(v)
        self.assertEqual(panels(v),panels(v))
        self.assertEqual(v,before)

    def test_backend_scouting_contract_and_revision_history(self):
        html=panels({'scouting':{'source':'coach','judge':'Casey Coach','as_of':[2031,1],
            'categories':[{'category':'Putting','grade':'B','confidence':'medium','explanation':'Observed rounds',
                           'history':[{'year':2030,'week':1,'grade':'C'},{'year':2031,'week':1,'grade':'B'}]}]}})
        self.assertIn('Coach assessment',html)
        self.assertIn('Casey Coach',html)
        self.assertIn('week 1 of 2031',html)
        self.assertIn('Confidence: medium',html)
        self.assertIn('2030 · week 1: C',html)
        self.assertIn('No category assessments',panels({'scouting':None}))
