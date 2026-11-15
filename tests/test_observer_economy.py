import copy
import unittest
import observer_career_economy as E

class Evidence(unittest.TestCase):
    def test_missing_and_unknown_remain_missing(self):
        self.assertEqual(E.economy({}),'')
        self.assertEqual(E.comparison({},1),'')
        self.assertEqual(E.dollars(None),'Not recorded')
    def test_weekly_forecasts_not_plan_guarantee(self):
        v={'week_compare':{'1':{'load':{'fatigue':.1,'performance_threshold':.2,'train_fatigue_after':.11,'rest_fatigue_after':.05,'played_last_4':2,'played_last_8':3},'play':[{'name':'A < B','eligible':None,'selected_field':True,'cost':None,'why':'ranking','opportunities':[]}]}}}
        before=copy.deepcopy(v);h=E.comparison(v,1)
        for text in ('10.0%','20.0%','independent previews','Selection required','Not recorded','A &lt; B','not estimated'):
            self.assertIn(text,h)
        self.assertEqual(v,before);self.assertEqual(h,E.comparison(v,1))
    def test_finance_does_not_treat_formula_as_contract(self):
        v={'money':{'funds':{'spendable':100,'cash':30,'family_backing':40,'backer_funds':30},'sponsor':{'contract':10,'rule':'set at January','prestige':2,'at_this_prestige_now':20},'backer':{'deal':30,'put_up':30,'returned':0},'seasons':{'2030':None},'labels':{}}}
        before=copy.deepcopy(v);h=E.economy(v)
        self.assertIn('not a new contract',h);self.assertIn('No ledger recorded',h);self.assertEqual(v,before)
    def test_partial_season_label(self):
        h=E.seasons({'seasons_summary':[{'year':2030,'name':'A','recorded_weeks':4,'events':1,'wins':0,'top10':0,'missed_cuts':0,'prize_money':0}]})
        self.assertIn('incomplete season',h);self.assertIn('4 recorded weeks',h)
