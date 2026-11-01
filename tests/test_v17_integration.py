"""Where the v17 branches meet (build/v17-integration): the prestige store's pending and fallback values on the
server-sorted Tournaments and Courses lists, and the nation page with seasons still being read in a world settled
with visible achievement (rules 2026-11-14) -- pending seasons are never taken for records, and every row is as wide
as the table.

Run from the project folder:  python -m unittest tests.test_v17_integration -v
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tests'))
import observer as O                                                      # noqa: E402
import observer_prestige as OP                                            # noqa: E402
import observer_prestige_store as PS                                      # noqa: E402
from test_server_sort import CourseWorld, TourWorld, body_ids, q           # noqa: E402

PENDING_LT = {'events': {}, 'courses': {}, 'venue_moves': [], 'nations': {}, 'pending': True, 'year': None,
              'newest': 2051}


def rows_of(html):
    tb = html.split('<tbody>', 1)[1].split('</tbody>', 1)[0]
    return [re.findall(r'<td[^>]*>(.*?)</td>', r) for r in re.findall(r'<tr>(.*?)</tr>', tb)]


class ListsWithTheStore(unittest.TestCase):
    def test_sorted_lists_while_values_are_being_read(self):
        for w, page, col in ((TourWorld(), O.tournaments, 'S'), (CourseWorld(), O.courses_page, 'C')):
            with mock.patch.object(OP, 'latest', lambda w_: PENDING_LT):
                html = page(w, q(sort='prestige', dir='desc'))[1]
            self.assertIn('being read from the history in the background', html)
            self.assertIn('sorts the whole list', html)                       # the sorting branch's text kept
            ids = body_ids(html, r'/(?:series|course)/(' + col + r'\d+)')
            self.assertTrue(ids)                                               # rows still listed (no values yet)

    def test_sorted_lists_say_which_older_season_they_show(self):
        for w, page, key in ((TourWorld(), O.tournaments, 'events'), (CourseWorld(), O.courses_page, 'courses')):
            lt = {'events': {}, 'courses': {}, 'venue_moves': [], 'nations': {}, 'pending': False, 'year': 2049,
                  'newest': 2051, key: w.pres}
            with mock.patch.object(OP, 'latest', lambda w_: lt):
                html = page(w, q(sort='prestige', dir='desc'))[1]
            self.assertIn('recorded at the end of 2049', html)
            self.assertIn('(2051)', html)
            first = body_ids(html, r'/(?:series|course)/([SC]\d+)')[0]
            self.assertEqual(w.pres[first], max(v for v in w.pres.values() if v is not None))   # whole list sorted
            lt_now = dict(lt, year=2051)
            with mock.patch.object(OP, 'latest', lambda w_: lt_now):
                self.assertNotIn('recorded at the end of', page(w, q(sort='prestige', dir='desc'))[1])

    def test_nations_list_wording_while_pending(self):
        with mock.patch.object(OP, 'latest', lambda w: PENDING_LT), \
                mock.patch.object(O, 'nation_counts', lambda w: {'Fiji': [1, 1, 0, 0]}):
            html = O.nations(None, {})[1]
        self.assertIn('50 = as expected; rules: national prestige', html)
        self.assertNotIn('settled before rules 2026-11-14', html)


class NationPageWithPendingSeasons(unittest.TestCase):
    NEW = {'prestige': {'Fiji': 61.0}, 'ratio': {'Fiji': 0.9}, 'achievement': {'Fiji': 1.7},
           'multiplier': {'Fiji': 1.1}, 'shares': {'juniors': {'Fiji': 0.01}, 'new_pros': {'Fiji': 0.02}},
           'allocated': {'juniors': {'Fiji': 1}, 'new_pros': {'Fiji': 0}},
           'rules': {'achievement': True, 'achievement_weight': 0.666667, 'carry': True}}

    def page(self, recs, live=None):
        years = sorted(recs)
        with mock.patch.object(OP, '_years', lambda w: years), \
                mock.patch.object(OP, '_records', lambda w, ys: {y: recs[y] for y in ys}), \
                mock.patch.object(OP, '_live', lambda w: live):
            return OP.nation_section(object(), 'Fiji')

    def test_pending_seasons_are_not_records_and_rows_are_as_wide_as_the_table(self):
        recs = {2040: PS.PENDING, 2041: {'nations': self.NEW}, 2042: None, 2043: PS.PENDING}
        html = self.page(recs)                                                 # (no AttributeError on PENDING)
        self.assertIn('>Achievement</th>', html)
        self.assertIn('Visible success first', html)
        self.assertIn('being read', html)
        widths = {len(r) for r in rows_of(html)}
        self.assertEqual(widths, {9})                                          # read, pending, not recorded alike
        cells = {r[0]: r for r in rows_of(html)}
        self.assertIn('being read', cells['2044'][1])
        self.assertIn('not recorded', cells['2043'][1])
        self.assertEqual(cells['2042'][2:4], ['1.700', '0.900'])

    def test_all_pending_new_world_with_its_live_season(self):
        live = {'nations': dict(self.NEW, closed=2043, baseline_shares={'juniors': {'Fiji': 0.01}, 'new_pros': {}})}
        html = self.page({2040: PS.PENDING, 2041: PS.PENDING, 2042: PS.PENDING}, live=live)
        self.assertIn('>Achievement</th>', html)                              # from the live view's own fields
        self.assertEqual({len(r) for r in rows_of(html)}, {9})

    def test_an_old_world_with_pending_seasons_keeps_seven_columns(self):
        old = {k: v for k, v in self.NEW.items() if k not in ('achievement', 'rules')}
        html = self.page({2040: PS.PENDING, 2041: {'nations': old}, 2042: None})
        self.assertNotIn('>Achievement</th>', html)
        self.assertEqual({len(r) for r in rows_of(html)}, {7})


if __name__ == '__main__':
    unittest.main()
