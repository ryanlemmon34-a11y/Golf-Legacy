"""Compact profile presentation preserves career evidence and explicit data coverage."""
import re
import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import observer as O


class ProfileSummaryTests(unittest.TestCase):
    def world(self, live=None):
        return SimpleNamespace(live=live, a=None, tours=lambda: {'PT': {'name': 'Premier'}},
                               person_link=lambda pid: f'<a href="/golfer/{pid}">Person {pid}</a>')

    def summary(self, world, person, snapshots=None, peak=None, rows=None):
        with patch.object(O.OD, 'results', return_value=rows or []), \
             patch.object(O.OD, 'rating_snapshots', return_value=snapshots or {}), \
             patch.object(O.OD, 'recorded_peak', return_value=peak):
            return O._profile_summary(world, 1, person)

    def test_current_facts_and_team_have_scope(self):
        live = SimpleNamespace(people={1: {'ratings': [78.25], 'prestige': 60}}, wr={1: 7},
                               cursor={'year': 2030}, prize={1: 1200}, coach_of={1: 2}, caddie_of={1: 3})
        html = self.summary(self.world(live), {'golfer': {'status': 'pro', 'tour': 'PT'}},
                            peak={'value': 81.2, 'complete': False})
        for value in ['World ranking · now', 'No. 7', 'Overall · now', '78.2', 'Recorded Peak Overall',
                      '2030 so far', '$1,200', 'Team now', '/golfer/2', '/golfer/3', 'Prestige · now']:
            self.assertIn(value, html)
        self.assertNotIn('Career earnings', html)

    def test_archive_and_retired_values_never_claim_to_be_current(self):
        html = self.summary(self.world(), {'golfer': {'status': 'pro', 'lifestyle': 'retired',
                                                      'tour': 'PT', 'prestige': 34}},
                            snapshots={2028: [70], 2029: [69]}, peak={'value': 80, 'complete': True})
        for value in ['retired', 'Tour · last recorded', 'Overall · final · end of 2028', '69.0',
                      'Peak Overall', 'Prestige · last recorded']:
            self.assertIn(value, html)
        self.assertNotIn('· now', html)
        self.assertNotIn('Prize money', html)
        self.assertNotIn('World ranking', html)

    def test_recorded_wins_exclude_qualifying_and_link_to_results(self):
        rows = [{'pos': 1, 'category': 'major'}, {'pos': 1, 'category': 'tour'},
                {'pos': 2, 'category': 'major'}, {'pos': 1, 'category': 'qualifying', 'tier': 7}]
        html = self.summary(self.world(), {'golfer': {}}, rows=rows)
        self.assertIn('Recorded wins · all tours', html)
        self.assertIn('outcome=win">2</a>', html)
        self.assertIn('honor=major">1</a>', html)
        self.assertIn('recorded events only', html)

    def test_archived_rating_order_is_respected(self):
        world = self.world()
        world.a = SimpleNamespace(world={'rating_keys': ['putting', 'overall']})
        html = self.summary(world, {'golfer': {}}, snapshots={2029: [55, 72]})
        self.assertIn('72.0', html)
        self.assertNotIn('55.0', html)

    def test_current_injury_is_visible_above_disclosures(self):
        live = SimpleNamespace(people={1: {}}, wr={}, cursor={'year': 2030}, prize={},
                               coach_of={}, caddie_of={}, injured_now=[1])
        html = self.summary(self.world(live), {'golfer': {}})
        self.assertIn('Availability · now', html)
        self.assertIn('Injured now', html)

    def test_missing_data_is_not_invented_and_status_is_escaped(self):
        html = self.summary(self.world(), {'golfer': {'status': '<unknown>'}})
        self.assertIn('&lt;unknown&gt;', html)
        for absent in ['Overall', 'Prestige', 'Prize money', 'World ranking']:
            self.assertNotIn(absent, html)


class ProfileHierarchyTests(unittest.TestCase):
    def playing(self, query=None, wins=False):
        rows = [{'pos': 1, 'year': 2029, 'event': 'event1', 'tour': 'PT'}] if wins else []
        with ExitStack() as stack:
            stack.enter_context(patch.object(O.OD, 'results', return_value=rows))
            stack.enter_context(patch.object(O.OD, 'is_qualifying', return_value=False))
            stack.enter_context(patch.object(O, 'event_link', return_value='event1'))
            stack.enter_context(patch.object(O, 'tour_link', return_value='Premier'))
            for module, names in [(O, ['_honors', '_season_history', '_ratings', 'ratings_history', 'injuries_section']),
                                  (O.OH, ['status_section', 'aggression_section', 'grand_slam_line']),
                                  (O.OG, ['golf_section', 'ranking_section']), (O.STORY, ['profile_section'])]:
                for name in names:
                    stack.enter_context(patch.object(module, name, return_value=f'<p>{name}</p>'))
            return O._playing(SimpleNamespace(), query or {}, 1, {'golfer': {'lifestyle': 'full_time'}})

    def test_honors_lead_with_sections_and_no_information_removed(self):
        html = self.playing(wins=True)
        self.assertLess(html.index('<p>_honors'), html.index('<p>_season_history'))
        self.assertLess(html.index('<p>_season_history'), html.index('<p>_ratings'))
        for name in ['_honors', '_season_history', '_ratings', 'ratings_history', 'injuries_section',
                     'status_section', 'aggression_section', 'grand_slam_line', 'golf_section',
                     'ranking_section', 'profile_section']:
            self.assertEqual(html.count(f'<p>{name}</p>'), 1)
        for section in ['honors', 'seasons', 'status', 'ratings', 'performance', 'story']:
            self.assertIn(f'href="#career-{section}"', html)
            self.assertEqual(html.count(f'id="career-{section}"'), 1)
        self.assertIn('All recorded wins (1)', html)
        self.assertEqual(html.count('<details '), html.count('</details>'))
        self.assertIn('aria-label="Playing career sections"', html)

    def test_rating_filter_keeps_relevant_disclosure_open(self):
        self.assertNotRegex(self.playing(), r'id="career-ratings" open')
        self.assertRegex(self.playing({'rh': ['overall']}), r'id="career-ratings" open')
        self.assertRegex(self.playing({'rm': ['change']}), r'id="career-ratings" open')

    def test_season_totals_are_fixed_and_definitions_are_collapsed(self):
        live = SimpleNamespace(cursor={'year': 2030}, prize={1: 500}, wr={1: 10})
        world = SimpleNamespace(a=None, live=live, statistics=lambda: (None, None),
                                live_statistics=lambda: ({}, {}),
                                tours=lambda: {'PT': {'name': 'Premier', 'tier': 1}})
        rows = [{'year': 2030, 'tour': 'PT', 'pos': 1, 'tier': 1, 'cut': 1}]
        with patch.object(O.OD, 'cut_flags'):
            html = O._season_history(world, {}, 1, {'born': 2000, 'golfer': {'status': 'pro'}}, rows)
        self.assertIn('<tfoot>', html)
        footer = html.split('<tfoot>', 1)[1].split('</tfoot>', 1)[0]
        self.assertIn('<strong>Career</strong>', footer)
        body = html.split('<tbody>', 1)[1].split('</tbody>', 1)[0]
        self.assertNotIn('<strong>Career</strong>', body)
        self.assertIn('All tours · recorded seasons only.', html)
        self.assertIn('<details class="help"><summary>How to read season statistics</summary>', html)
        self.assertIn('runner-up is a recorded second', html)

    def test_empty_career_has_no_empty_win_disclosure(self):
        self.assertNotIn('All recorded wins', self.playing())


class ProfileSecondPassTests(unittest.TestCase):
    def test_retired_rating_details_use_final_date_and_recorded_key_order(self):
        w = SimpleNamespace(a=SimpleNamespace(world={'rating_keys':['putting','overall']}), live=None)
        with patch.object(O.OD, 'rating_snapshots', return_value={2029:[55,72]}), \
             patch.object(O, 'now_year', return_value=2030), patch.object(O, 'peak_line', return_value=''):
            body = O._ratings(w, 1, {'golfer':{'lifestyle':'retired'}})
        self.assertIn('Final playing ratings at the end of 2028: overall 72', body)
        self.assertNotIn('start of 2029', body)

    def test_historical_profile_keeps_current_metrics_out(self):
        person = {'name':'Alex', 'roles':['golfer'], 'born':1990, 'country':'USA',
                  'golfer':{'status':'pro','lifestyle':'retired'}}
        w = SimpleNamespace(a=None, live=SimpleNamespace(cursor={'year':2030}),
                            person=lambda pid:person, name=lambda pid:'Alex',
                            geography=lambda pid:{'birthplace':{'country':'USA'}, 'residence':{'country':'Canada'}})
        with patch.object(O, 'shortlist_button', return_value=''), \
             patch.object(O, '_profile_summary') as summary, \
             patch.object(O.OD, 'results') as results, \
             patch.object(O.OH, 'season_view', return_value='<h2>2027 facts</h2>'):
            _, body = O.golfer(w, {'tab':['season'],'year':['2027']}, '1')
        summary.assert_not_called()
        results.assert_not_called()
        self.assertIn('Historical season 2027', body)
        self.assertIn('2027 facts', body)
        self.assertNotIn('lives in', body)
        self.assertNotIn('class="tag">retired', body)
        self.assertNotIn('Age 40', body)
        self.assertIn('View full career and latest profile', body)

    def test_ratings_form_returns_to_chart(self):
        series = [('2027','start of 2027',{'overall':70}),('2028','start of 2028',{'overall':72})]
        with patch.object(O, 'ratings_series', return_value=series):
            body=O.ratings_history(SimpleNamespace(), {'tab':['playing']}, 1, {})
        self.assertIn('action="/golfer/1#career-ratings"', body)
        self.assertIn('name="tab" value="playing"', body)

    def test_expanded_tour_rows_keep_year_when_sorted(self):
        live=SimpleNamespace(cursor={'year':2030},prize={1:500},wr={1:10})
        world=SimpleNamespace(a=None,live=live,statistics=lambda:(None,None),live_statistics=lambda:({},{}),
                              tours=lambda:{'PT':{'name':'Premier','tier':1}, 'CH':{'name':'Challenger','tier':2}})
        rows=[{'year':y,'tour':t,'pos':1,'tier':1,'cut':1} for y in (2029,2030) for t in ('PT','CH')]
        with patch.object(O.OD,'cut_flags'):
            body=O._season_history(world,{'tours':['1']},1,{'born':2000,'golfer':{'status':'pro'}},rows)
        season_rows=body.split('<tbody>')[1].split('</tbody>')[0].split('<tr>')[1:]
        self.assertEqual(len(season_rows),6)
        for row in season_rows:
            self.assertRegex(row.split('</td>')[0],r'tab=season&year=20(29|30)')
        self.assertIn('Tour rows repeat their season',body)
        self.assertIn('#career-seasons',body)


if __name__ == '__main__':
    unittest.main()
