"""Observer-only frame behavior; no simulation or saved-world mutation."""
import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import observer as O
import observer_views as V


class ShellTests(unittest.TestCase):
    def test_people_search_targets_every_role(self):
        w = NS(live=None, session=None, label='Demo', read_only=True, a=None)
        html = O.page(w, 'People', '', path='/search')
        self.assertRegex(html, r'<form[^>]+role="search"[^>]+action="/search"')
        self.assertIn('Search golfers, coaches and caddies', html)
        self.assertIn('href="/search" class="active" aria-current="page"', html)

    def test_search_is_a_remembered_list(self):
        self.assertTrue(V.is_list('/search'))
        self.assertEqual(V.canonical({'q':['Rojas'], 'sort':['name'], 'tsort':['0.0.a']}, '/search'), 'q=Rojas&sort=name')

    def test_all_people_search_includes_staff_only_people(self):
        people = {1: {'name':'Alex Golfer', 'roles':['golfer'], 'country':'USA', 'born':1990,
                      'golfer':{'status':'pro', 'lifestyle':'full_time'}},
                  2: {'name':'Alex Coach', 'roles':['coach'], 'country':'USA', 'born':1980, 'coach':{'status':'active'}},
                  3: {'name':'Alex Caddie', 'roles':['caddie'], 'country':'USA', 'born':1985, 'caddie':{'status':'active'}}}
        w = NS(a=None, live=None, all_people=lambda:list(people), person=lambda pid:people[pid],
               person_link=lambda pid:f'<a href="/golfer/{pid}">{people[pid]["name"]}</a>', tours=lambda:{})
        _, results = O.search(w, {'q':['Alex']})
        for name in ['Alex Golfer','Alex Coach','Alex Caddie']:
            self.assertIn(name, results)
        _, golfers = O.golfers(w, {'q':['Alex']})
        self.assertNotIn('Alex Coach', golfers)
        self.assertNotIn('Alex Caddie', golfers)

    def test_golf_stat_totals_are_not_sortable_rows(self):
        row = dict(starts=1, golf_starts=1, rounds=4)
        data = {2027: {'all':row, 'tours':{'PT':row}, 'live':False}}
        with patch.object(O.OG, 'person_golf', return_value=data), \
             patch.object(O.OG, 'figure_cells', return_value=['1'] * len(O.OG.SHOWN)):
            body = O.OG.golf_section(NS(tours=lambda:{'PT':{'tier':1}}), 1)
        self.assertNotIn('Career', body.split('<tbody>')[1].split('</tbody>')[0])
        self.assertIn('Career', body.split('<tfoot>')[1].split('</tfoot>')[0])

    def test_navigation_sections_include_detail_pages(self):
        for path, section in [('/', '/'), ('/event/2027:test', '/tournaments'), ('/series/test','/tournaments'),
                              ('/course/1','/courses'), ('/nation/USA','/nations'), ('/tour/PT','/tours'),
                              ('/season/2027','/seasons'), ('/records/most-wins','/records'),
                              ('/golf-records/putting','/records'), ('/standings','/qualification')]:
            self.assertEqual(O.navigation_section(path), section)
        for roles, section in [(['golfer','coach'],'/golfers'), (['coach'],'/coaches'), (['caddie'],'/caddies')]:
            self.assertEqual(O.navigation_section('/golfer/1', NS(person=lambda pid: {'roles':roles})), section)

    def test_advance_actions_keep_same_cursor_and_one_time_token(self):
        w = NS(read_only=False, live=NS(world_id='world-1', cursor={'year':2027,'week':4,'phase':'week'}))
        html = O.advance_controls(w)
        for name, value in [('world','world-1'),('year','2027'),('week','4'),('phase','week')]:
            self.assertIn(f'name="{name}" value="{value}"', html)
        self.assertRegex(html, r'name="op" value="[0-9a-f]{32}"')
        for value in ['1','4','season','seasons']:
            self.assertIn(f'name="weeks" value="{value}"', html)
        self.assertIn('<summary>Longer advance</summary>', html)
        self.assertIn('aria-label="Number of seasons"', html)
        self.assertEqual(O.advance_controls(NS(read_only=True)), '')

    def test_normal_and_career_advance_have_safe_stop(self):
        job = dict(state='running', id='j1', kind='advance', title='Advance', cancellable=True,
                   cancel_requested=False, total=4, done=1, phase='Playing', elapsed=1)
        for kind in ['advance','career-advance']:
            html = O.advance_controls(None, dict(job, kind=kind))
            self.assertIn('action="/cancel"', html)
            self.assertIn('Stop simulation', html)
            self.assertIn('aria-label="Simulation progress"', html)
            self.assertNotIn(' disabled', html)
            self.assertIn(' disabled', O.advance_controls(None, dict(job, kind=kind, cancel_requested=True)))
        self.assertNotIn('Stop simulation', O.advance_controls(None, dict(job, kind='create', cancellable=False)))

    def test_keyboard_sort_buttons_and_pinned_totals(self):
        html = O.table(['Season','Wins'], [['2027','2'], ['2028','3']], numeric=(1,), footer_rows=[['Career','5']])
        self.assertIn('class="sort-button" type="button"', html)
        self.assertIn('scope="col"', html)
        self.assertIn('<tfoot>', html)
        self.assertNotIn('Career', html.split('<tbody>')[1].split('</tbody>')[0])
        self.assertIn('Career', html.split('<tfoot>')[1])
        self.assertIn("ev.target.closest('button.sort-button')", V.SORT_JS)

    def test_clear_can_keep_navigation_without_sort_or_filters(self):
        html = O.filters('/golfer/4', {'tab':['results'], 'year':['2027'], 'sort':['prize']},
                         [('year','Season',None)], carry=('tab','sort'), clear_keep=('tab',))
        self.assertIn('href="/golfer/4?default=1&amp;tab=results">Clear', html)
        self.assertIn('name="tab" value="results"', html)


class SecondPassShellTests(unittest.TestCase):
    def test_short_advances_ignore_unrelated_hidden_season_validation(self):
        w=NS(read_only=False,live=NS(world_id='w',cursor={'year':2027,'week':1,'phase':'start'}))
        body=O.advance_controls(w)
        for value in ('1','4','season'):
            self.assertRegex(body, rf'<button[^>]*name="weeks" value="{value}"[^>]*formnovalidate')
        seasons=re.search(r'<button[^>]*name="weeks" value="seasons"[^>]*>',body).group()
        self.assertNotIn('formnovalidate',seasons)

    def test_saved_views_use_keyboard_sort_controls(self):
        state={'saved':[{'id':'v1','name':'Test','path':'/search','query':'q=Alex','added':'2027-01-01'}], 'last':{}}
        with patch.object(V,'state',return_value=state):
            _,body=V.views_page(NS(),{})
        self.assertEqual(body.count('class="sort-button"'),5)
        self.assertEqual(body.count('scope="col"'),5)
        self.assertIn('/views/remove',body)

    def test_nation_prestige_uses_keyboard_sort_controls(self):
        import observer_prestige as OP
        record={'nations':{'prestige':{'USA':50},'multiplier':{'USA':1},
                           'shares':{'juniors':{'USA':.5},'new_pros':{'USA':.5}}}}
        with patch.object(OP,'_live',return_value=None), patch.object(OP,'_years',return_value=[2027]), \
             patch.object(OP,'_records',return_value={2027:record}):
            body=OP.nation_section(NS(),'USA')
        self.assertEqual(body.count('class="sort-button"'),7)
        self.assertEqual(body.count('scope="col"'),7)


    def test_wide_golf_stats_have_sticky_header_and_truthful_sort_direction(self):
        for key in ('scoring','putts_round','putts_gir','bogeys','distance','rounds'):
            for worst in (False, True):
                query={'sort':[key], **({'dir':['worst']} if worst else {})}
                body=O.OG.golf_table(NS(),query,{},'/stats',{},'all-time',False)
                self.assertIn('<table data-identity="second"><thead>',body)
                self.assertIn('</thead><tbody>',body)
                higher=O.OG.GS.METRICS[key][3] if key in O.OG.GS.METRICS else True
                expected='ascending' if worst == higher else 'descending'
                self.assertIn(f'aria-sort="{expected}"',body)
                self.assertIn('<summary>Golf statistics and sort directions</summary>',body)


if __name__ == '__main__':
    unittest.main()
