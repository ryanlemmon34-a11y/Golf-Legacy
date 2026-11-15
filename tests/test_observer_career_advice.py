import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from observer_career_advice import enrich_plan, render_advice


def fixtures():
    g = {'coach': 'Coach <script>', 'tour': 'College', 'fatigue': .1,
         'attrs_exact': {'power': 65, 'stamina': 60, 'recovery_rate': 60,
                         'wedges': 30, 'chipping': 35, 'putting_consistency': 60}}
    p = {'weeks': [{'week': n, 'money': 100, 'injured_until': None, 'events': [
        {'event_id': str(n)+'a', 'name': 'College tournament', 'tour': 'College',
         'eligible': True, 'affordable': True, 'cost': 60},
        {'event_id': str(n)+'b', 'name': 'Other event', 'tour': 'Other',
         'eligible': True, 'affordable': True, 'cost': 20}], 'selected': [], 'current': None}
        for n in range(1, 5)], 'policy': {'selected': 'decline', 'qualifying': 'skip'}}
    return p, g


class AdviceTests(unittest.TestCase):
    def test_pure_deterministic_and_no_secret_inputs(self):
        p,g=fixtures(); before=copy.deepcopy((p,g))
        a=enrich_plan(p,g)
        self.assertEqual((p,g),before)
        self.assertEqual(a,enrich_plan(p,g))
        g['ceilings']={'power':100}; g['hidden_temperament']=0
        self.assertEqual(a,enrich_plan(p,g))

    def test_budget_and_nonconsecutive_competition(self):
        p,g=fixtures(); a=enrich_plan(p,g)['advice']
        self.assertEqual(a['weeks'][0]['choice']['event_id'],'1a')
        self.assertEqual(a['weeks'][1]['choice'],{'kind':'train','category':'short_game'})
        self.assertEqual(a['weeks'][2]['choice']['event_id'],'3b')
        self.assertEqual(a['weeks'][3]['choice']['kind'],'train')

    def test_injury_and_fatigue(self):
        p,g=fixtures(); p['weeks'][0]['injured_until']=[2029,2]; g['fatigue']=.5
        a=enrich_plan(p,g)['advice']
        self.assertEqual(a['weeks'][0]['choice']['kind'],'rest')
        self.assertEqual(a['weeks'][1]['choice']['kind'],'rest')

    def test_no_coach_or_ratings_no_fictional_advice(self):
        p,g=fixtures(); g['coach']=None
        self.assertIsNone(enrich_plan(p,g)['advice'])
        g['coach']='A'; g['attrs_exact']={}
        self.assertIsNone(enrich_plan(p,g)['advice'])

    def test_entry_status_never_probability(self):
        p,g=fixtures(); p['weeks'][0]['events'][0].update(eligible=False,why='Not in college')
        out=enrich_plan(p,g)
        self.assertEqual(out['weeks'][0]['events'][0]['access']['label'],'Not in college')
        self.assertIsNone(out['weeks'][0]['events'][1]['access']['probability'])
        self.assertIn('not guaranteed',out['weeks'][0]['events'][1]['access']['label'])

    def test_preview_does_not_overwrite_saved_choices(self):
        p,g=fixtures(); p['weeks'][0]['current']={'kind':'rest'}
        out=enrich_plan(p,g)
        self.assertEqual(out['policy'],p['policy'])
        self.assertEqual(out['weeks'][0]['current'],{'kind':'rest'})

    def test_renderer_safe_and_explicit_no_submit(self):
        p,g=fixtures(); out=render_advice(enrich_plan(p,g))
        self.assertIn('type="button"',out)
        self.assertIn('Coach &lt;script&gt;',out)
        self.assertNotIn('Coach <script>',out)
        self.assertIn('Nothing has been saved yet.',out)
        self.assertNotIn('.submit(',out)
        self.assertNotIn('fetch(',out)

    def test_disabled_development_does_not_recommend_training(self):
        p,g=fixtures(); a=enrich_plan(p,g,training_enabled=False)['advice']
        for row in a['weeks']:
            self.assertNotEqual(row['choice']['kind'],'train')
            self.assertNotEqual(row['choice'].get('fallback',{}).get('kind'),'train')

    def test_future_block_empty(self):
        p,g=fixtures();p['weeks']=[]
        self.assertIsNone(enrich_plan(p,g)['advice'])

if __name__=='__main__':unittest.main()
