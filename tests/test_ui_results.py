"""Results sorts the filtered dataset before paging and keeps profile context."""
import html
import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from urllib.parse import parse_qs, urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
import observer as O


class ResultsTests(unittest.TestCase):
    def setUp(self):
        self.rows = [dict(year=2030, week=i + 1, event=f'2030:event{i:03}', series=f'event{i:03}',
                          name=f'Event {i:03}', tour='tour', tier=1, category='tour', pos=i + 1,
                          site=0, coach=i + 1, caddie=i + 1, route=f'route{i:03}', prize=i,
                          live=False) for i in range(65)]
        self.w = SimpleNamespace(statistics=lambda: (None, False), calendar_version='v1',
                                 tours=lambda: {'tour': {'name': 'Tour'}},
                                 series_name=lambda sid: sid, name=lambda pid: f'Person {pid:03}',
                                 person_link=lambda pid: str(pid) if pid else '—')
        self.prize_calls = []
        def prizes(w, pid, rows, db):
            self.prize_calls.append(list(rows))
            return {(r['event'], r['site']): r['prize'] for r in rows if r['prize'] is not None}
        self.enterContext(mock.patch.object(O.OD, 'results', side_effect=lambda *_: list(self.rows)))
        self.enterContext(mock.patch.object(O.OD, 'start_prizes', side_effect=prizes))

    def render(self, **q):
        return O._results(self.w, {k: [str(v)] for k, v in q.items()}, 7)

    def events(self, page):
        return [unquote(e) for e in re.findall(r'href="/event/([^"]+)"', page)]

    def query(self, page, text):
        href = re.search(r'<a href="([^"]+)">' + text + r'</a>', page).group(1)
        return parse_qs(urlsplit(html.unescape(href)).query)

    def test_every_header_sorts_full_dataset_before_paging(self):
        for key in ('week', 'event', 'pos', 'prize', 'coach', 'caddie', 'route'):
            with self.subTest(key=key):
                page = self.render(sort=key, dir='asc')
                self.assertEqual(self.events(page), [r['event'] for r in self.rows[:50]])
                self.assertIn('data-server-sort="1"', page)
                page2 = self.render(sort=key, dir='asc', page=2)
                self.assertEqual(self.events(page2), [r['event'] for r in self.rows[50:]])
                self.assertEqual(self.events(self.render(sort=key, dir='desc')),
                                 [r['event'] for r in self.rows[::-1][:50]])

    def test_year_and_tour_sort_full_dataset(self):
        for i, r in enumerate(self.rows):
            r['year'] = 2000 + i
            r['tour'] = f'tour_{i:03}'
        for key in ('year', 'tour'):
            self.assertEqual(self.events(self.render(sort=key, dir='asc')),
                             [r['event'] for r in self.rows[:50]])

    def test_default_latest_first_and_invalid_sort_fallback(self):
        expected = [r['event'] for r in self.rows[::-1][:50]]
        self.assertEqual(self.events(self.render()), expected)
        self.assertEqual(self.events(self.render(sort='bogus', dir='bogus')), expected)

    def test_zero_prize_is_known_and_missing_stays_last_both_directions(self):
        self.rows = self.rows[:3]
        self.rows[0]['prize'], self.rows[1]['prize'], self.rows[2]['prize'] = None, 0, 100
        for direction, indexes in [('asc', [1, 2, 0]), ('desc', [2, 1, 0])]:
            page = self.render(sort='prize', dir=direction)
            self.assertEqual(self.events(page), [self.rows[i]['event'] for i in indexes])
            self.assertIn('$0', page)
            self.assertIn('—', page)

    def test_missing_position_staff_tour_and_route_stay_last(self):
        self.rows = self.rows[:3]
        for key, missing in [('pos', None), ('coach', 0), ('caddie', 0), ('tour', None), ('route', None)]:
            with self.subTest(key=key):
                old = self.rows[0][key]
                self.rows[0][key] = missing
                for direction in ('asc', 'desc'):
                    self.assertEqual(self.events(self.render(sort=key, dir=direction))[-1], self.rows[0]['event'])
                self.rows[0][key] = old

    def test_ties_keep_identity_order_independent_of_direction(self):
        self.rows = self.rows[:3]
        for r in self.rows:
            r.update(week=1, pos=1)
        self.rows.reverse()
        expected = sorted(r['event'] for r in self.rows)
        for direction in ('asc', 'desc'):
            self.assertEqual(self.events(self.render(sort='pos', dir=direction)), expected)

    def test_clear_stays_on_results_and_resets_saved_filter_state(self):
        page = self.render(year=2030, tour='tour', outcome='top10', sort='prize', dir='desc', page=2)
        self.assertEqual(self.query(page, 'Clear'), {'default': ['1'], 'tab': ['results']})

    def test_apply_and_header_preserve_context_without_page_sort(self):
        page = self.render(year=2030, series='event000', honor='premier', quals=1,
                           sort='prize', dir='desc', page=2, tsort='5:desc', back='/stats?year=2030')
        for key, val in [('tab', 'results'), ('series', 'event000'), ('honor', 'premier'),
                         ('quals', '1'), ('sort', 'prize'), ('dir', 'desc')]:
            self.assertIn(f'name="{key}" value="{val}"', page)
        query = self.query(page, 'Prize')
        self.assertEqual(query['dir'], ['asc'])
        self.assertEqual(query['tab'], ['results'])
        self.assertEqual(query['back'], ['/stats?year=2030'])
        self.assertNotIn('page', query)
        self.assertNotIn('tsort', query)

    def test_scope_clear_removes_only_selected_scope_and_resets_page(self):
        page = self.render(year=2030, series='event000', honor='premier', quals=1,
                           sort='prize', dir='desc', page=2)
        links = re.findall(r'<a href="([^"]+)">clear</a>', page)
        queries = [parse_qs(urlsplit(html.unescape(link)).query) for link in links]
        self.assertEqual(len(queries), 2)
        for query, removed, kept in zip(queries, ('honor', 'series'), ('series', 'honor')):
            self.assertNotIn(removed, query)
            self.assertIn(kept, query)
            self.assertNotIn('page', query)
            self.assertEqual(query['tab'], ['results'])
            self.assertEqual(query['year'], ['2030'])
            self.assertEqual(query['sort'], ['prize'])

    def test_pager_keeps_filters_sort_and_tab(self):
        page = self.render(year=2030, sort='prize', dir='asc', tsort='5:desc')
        self.assertEqual(self.query(page, 'Next →'),
                         {'year': ['2030'], 'sort': ['prize'], 'dir': ['asc'], 'tab': ['results'], 'page': ['2']})
        self.assertEqual(len(self.prize_calls[-1]), 65)
        self.render(sort='event')
        self.assertEqual(len(self.prize_calls[-1]), 50)

    def test_qualifiers_honors_and_empty_filters_preserved(self):
        self.rows[0].update(tier=7, category='qualifying', pos=1)
        self.rows[1]['pos'] = 1
        self.assertNotIn(self.rows[0]['event'], self.events(self.render(sort='event')))
        self.assertIn(self.rows[0]['event'], self.events(self.render(sort='event', quals=1)))
        self.assertEqual(self.events(self.render(quals=1, honor='premier')), [self.rows[1]['event']])
        self.assertEqual(self.events(self.render(year=1900)), [])
        self.assertIn('0 of 64 starts', self.render(year=1900))

    def test_cut_filter_uses_recorded_cut_flags_before_sort(self):
        self.rows = self.rows[:3]
        self.rows[0]['pos'] = None
        self.rows[1]['pos'] = None
        with mock.patch.object(O.OD, 'cut_flags', side_effect=lambda w, rows, db:
                               [dict(r, cut=r['event'] == self.rows[1]['event']) for r in rows]):
            self.assertEqual(self.events(self.render(outcome='missed-cut', sort='week', dir='asc')),
                             [self.rows[1]['event']])

    def test_qualifier_toggle_keeps_filters_and_drops_stale_page_sort(self):
        self.rows[0].update(tier=7, category='qualifying')
        page = self.render(year=2030, sort='prize', dir='asc', page=2, tsort='1:desc')
        query = self.query(page, 'include the 1 qualifying stages')
        self.assertEqual(query, {'year': ['2030'], 'sort': ['prize'], 'dir': ['asc'],
                                 'tab': ['results'], 'quals': ['1']})

    def test_no_starts_remains_distinct_from_no_filter_matches(self):
        self.rows = []
        self.assertEqual(self.render(), '<p class="muted">No starts yet.</p>')


if __name__ == '__main__':
    unittest.main()
