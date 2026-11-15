import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from observer_career_color import PALETTES, STYLE
import observer
import observer_career as UI

def luminance(color):
    rgb=[int(color[i:i+2],16)/255 for i in (1,3,5)]
    rgb=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb]
    return sum(a*b for a,b in zip(rgb,(.2126,.7152,.0722)))

class CareerColor(unittest.TestCase):
    def test_semantic_text_pairs_meet_wcag_aa_normal_text(self):
        for mode,palette in PALETTES.items():
            for role,(fg,bg) in palette.items():
                a,b=sorted((luminance(fg),luminance(bg)))
                self.assertGreaterEqual((b+.05)/(a+.05),4.5,(mode,role))

    def test_palette_loaded_and_keyboard_high_contrast_kept(self):
        self.assertIn(STYLE,UI.STYLE)
        self.assertIn('focus-visible',STYLE)
        self.assertIn('forced-colors:active',STYLE)
        self.assertIn('prefers-color-scheme:dark',STYLE)

    def test_fatigue_caution_retains_text_and_value(self):
        v={'golfer':{'fatigue':.3,'injured_until':None},'readiness':{}}
        html=UI.readiness_card(v)
        self.assertIn('readiness-caution',html)
        self.assertIn('Fatigue is affecting play',html)
        self.assertIn('30.0',html)
        v['golfer']['fatigue']=.1
        self.assertNotIn('readiness-caution',UI.readiness_card(v))

    def test_signed_growth_is_not_color_only(self):
        self.assertIn('+0.20',UI.change(.2))
        self.assertIn('-0.20',UI.change(-.2))
