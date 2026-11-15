import unittest
from types import SimpleNamespace as N
from unittest.mock import patch
from golfsim.career_context import relevant_selected

class CareerCalendarScope(unittest.TestCase):
    def setUp(self):
        self.g=N(status='amateur',tour='CO_US_D1',country='USA',age=lambda y:20)
        self.s=N(series_amateur=lambda g,t:t=='AM_NORTH_AMERICA')
    def event(self,sid,category='elite_amateur',host='USA',eligibility='amateur',tier=6,tour='AMATEUR'):
        return N(series_id=sid,category=category,host_country=host,eligibility=eligibility,tier=tier,tour=tour)
    def test_college_amateur_sees_usa_championship_and_qualifier(self):
        for sid in ('USA_AMATEUR','USA_AMATEUR_QUALIFYING'):
            self.assertTrue(relevant_selected(self.s,self.g,self.event(sid),2029))
    def test_regional_age_and_national_scope_are_not_worldwide(self):
        with patch('golfsim.season.region_of',return_value='North America'):
            self.assertTrue(relevant_selected(self.s,self.g,self.event('NATIONAL_AMATEUR_USA','national_amateur'),2029))
            self.assertFalse(relevant_selected(self.s,self.g,self.event('NATIONAL_AMATEUR_JAPAN','national_amateur','Japan'),2029))
            self.assertTrue(relevant_selected(self.s,self.g,self.event('BRITANNIA_AMATEUR'),2029))
            self.assertFalse(relevant_selected(self.s,self.g,self.event('EUROPEAN_AMATEUR'),2029))
            self.assertFalse(relevant_selected(self.s,self.g,self.event('USA_MID_AMATEUR',eligibility='mid_amateur'),2029))
    def test_professionals_do_not_get_amateur_opportunities(self):
        self.g.status='pro'
        self.assertFalse(relevant_selected(self.s,self.g,self.event('USA_AMATEUR'),2029))

    def test_real_calendar_context_retains_target_pair(self):
        from tests.test_career_foundation import started
        from golfsim.career_context import context
        s=started('calendar_scope')
        try:
            g=s.season.g[s.season.career.golfer_id]
            g.status='amateur';g.tour='CO_US_D1';g.country='USA'
            year=s.cursor['year']
            rows=context(s.season,g,year,25)['upcoming']
            ids={r['event_id'].split(':',1)[-1] for r in rows}
            self.assertIn('USA_AMATEUR_QUALIFYING',ids)
            self.assertIn('USA_AMATEUR',ids)
            for r in rows:
                if r['event_id'].endswith(':USA_AMATEUR_QUALIFYING'):
                    self.assertEqual(r['target']['id'],'USA_AMATEUR')
                    self.assertIn('policy',r['status'])
        finally:
            s.close()
