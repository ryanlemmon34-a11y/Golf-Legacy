"""Career feedback presentation is explicit, escaped and honest about missing evidence."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import observer
import observer_career as UI

class CareerPresentation(unittest.TestCase):
    def test_empty_history_does_not_invent_results(self):
        html = UI.recap_card({'recaps': []})
        self.assertIn('No recorded period yet', html)
        self.assertIn('Older saves cannot show', html)
        self.assertNotIn('+0.00', html)

    def test_partial_period_reports_sources_and_escapes_labels(self):
        before = {'overall': 50, 'fatigue': .25}
        after = {'overall': 50.02, 'fatigue': .15}
        r = {'year':2028, 'start_week':1, 'end_week':4, 'complete':False,
             'before':before, 'after':after, 'development':{'training':{'overall':.01}, 'maturing':{'overall':.01}},
             'weeks':[{'week':1,'activity':'train','planned':'<script>bad</script>', 'training_category':'putting',
                       'before':before,'after':after, 'development_recorded':True, 'injuries':[{'kind':'sprain','out':2,'available':[2028,4]}],
                       'development':{'training':{'overall':.01}, 'maturing':{'overall':.01}},
                       'events':[{'id':'test','name':'<unsafe>','position':2,'tied':True,'rounds':None,'prize':None}]}]}
        html = UI.render_recap(r)
        self.assertIn('Partial record', html)
        self.assertIn('not a full-period comparison', html)
        self.assertIn('Training:', html)
        self.assertIn('Maturing:', html)
        self.assertIn('T2', html)
        self.assertIn('Injury: sprain', html)
        self.assertIn('Eligible to return week 4 of 2028', html)
        self.assertIn('25.0% → 15.0%', html)
        self.assertIn('Round scores not recorded', html)
        self.assertNotIn('Prize $0', html)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;unsafe&gt;', html)

    def test_readiness_labels_estimates_and_disabled_growth(self):
        v = {'golfer':{'fatigue':.3,'injured_until':None},
             'readiness':{'fatigue':.3,'rest_after':.15,'train_after':.27,
                          'forecast_note':'No tournament.', 'training_enabled':False,
                          'training_note':'Development disabled.'}}
        html = UI.readiness_card(v)
        self.assertIn('30.0', html)
        self.assertIn('Estimated fatigue', html)
        self.assertIn('No tournament.', html)
        self.assertIn('Development disabled.', html)
        self.assertIn('When development is enabled', html)

    def test_injured_golfer_has_no_impossible_training_forecast(self):
        v = {'golfer': {'fatigue': 0, 'injured_until': 100}, 'readiness': {'rest_after':0, 'train_after':0}}
        html = UI.readiness_card(v)
        self.assertIn('Injured', html)
        self.assertNotIn('After one training week', html)

    def test_college_coaching_is_not_mistaken_for_no_support(self):
        g = {'tour_key':'CO_TEST','coach':None,'caddie':None,'spendable':100,'funds':100}
        html = UI.support_card(g)
        self.assertIn('College team coaching', html)
        self.assertIn('No personal coach', html)
        self.assertIn('do not stack', html)
        g['coach'] = 'Named coach'
        self.assertIn('Named coach', UI.support_card(g))
        g['tour_key'] = 'PRO'
        self.assertNotIn('College team coaching', UI.support_card(g))

    def test_profile_and_career_share_display_groups_not_training_groups(self):
        from golfsim import career as CA, development as D
        from golfsim.ratings import ATTRIBUTE_GROUPS, ATTRIBUTE_KEYS
        flattened = {key: label for label, keys in CA.ATTR_GROUPS for key in keys}
        self.assertEqual(flattened, ATTRIBUTE_GROUPS)
        self.assertEqual(sum(len(keys) for _, keys in CA.ATTR_GROUPS), len(ATTRIBUTE_KEYS))
        self.assertEqual(flattened['wedges'], 'Driving & Approach')
        self.assertEqual(flattened['mid_irons'], 'Driving & Approach')
        self.assertEqual(flattened['power'], 'Physical')
        self.assertEqual(flattened['striking_consistency'], 'Consistency')
        self.assertIn('wedges', D.CATEGORIES['short_game'])
        self.assertNotIn('wedges', D.CATEGORIES['long_game'])
        html = UI.training_categories_help()
        self.assertIn('short-game practice includes wedge play', html)
        for keys in D.CATEGORIES.values():
            from golfsim.ratings import ATTRIBUTE_LABELS
            for key in keys:
                self.assertIn(ATTRIBUTE_LABELS[key], html)

    def test_event_dropdown_is_one_control_with_details_for_any_field_size(self):
        def event(i, eligible=True):
            return {'event_id':f'2028:{i}','name':f'Event <{i}>','eligible':eligible,'affordable':eligible,
                    'city':'City','country':'Country','tour':'Tour','cost':123,'why':'Not eligible'}
        for count in (0, 1, 30):
            o = {'week':2,'events':[event(i) for i in range(count)],'injured_until':None}
            html = UI.event_choice(o, {})
            self.assertEqual(html.count('type="radio"'), 1)
            self.assertEqual(html.count('<select'), 1)
            self.assertIn('name="e2"', html)
            self.assertIn('Event details &amp; eligibility', html)
            if count:
                self.assertIn('Event &lt;0&gt;', html)
                self.assertIn('$123 estimated', html)
                self.assertIn('City, Country', html)
            else:
                self.assertIn('No tournament available to enter', html)
        o = {'week':2,'events':[event(1),event(2,False)],'injured_until':None}
        del o['events'][1]['cost']
        html = UI.event_choice(o, {'kind':'event','event_id':'2028:1'})
        self.assertIn('value="2028:1" selected', html)
        self.assertNotIn('<option value="2028:2"', html)
        self.assertIn('Not eligible', html)
        self.assertIn('Cost not quoted', html)
        o['injured_until'] = 100
        self.assertIn('value="event" disabled', UI.event_choice(o, {}))

    def test_dropdown_form_maps_to_existing_command_and_requires_event(self):
        form = {'block':'2028-1','w1':'event','e1':'2028:TEST','f1':'train:putting',
                'w2':'train','c2':'long_game','w3':'rest','w4':'rest','selected':'accept','qualifying':'skip'}
        one = lambda f,k:f.get(k)
        command = UI.plan_command(form,one)
        self.assertEqual(command['weeks']['1'], {'kind':'event','event_id':'2028:TEST',
                                               'fallback':{'kind':'train','category':'putting'}})
        self.assertEqual(command['weeks']['2'], {'kind':'train','category':'long_game'})
        legacy = dict(form,w1='event:2028:TEST')
        self.assertEqual(command,UI.plan_command(legacy,one))
        self.assertIsNone(UI.plan_command(dict(form,e1=''),one))
