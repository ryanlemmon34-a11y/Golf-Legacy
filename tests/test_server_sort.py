"""Server-sorted directories: a column heading sorts the whole filtered list before paging.

Courses, tournaments, golfers, coaches and caddies are paged lists (100 rows a page). Their headings are links that
sort the complete filtered list by that column on the server -- either direction, missing values last both ways,
ties by name then id -- keep the filters and search, return to page 1, and drop a browser sort of the page (tsort).
The page script never re-sorts those tables. Tables that are not server-sorted (bounded summaries) still sort the
rows they show in the browser and say so.

Synthetic fixtures (250 rows; no world is played). Run from the project folder:
    python -m unittest tests.test_server_sort -v
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import observer as O                                                      # noqa: E402
import observer_prestige as OP                                            # noqa: E402
import observer_views as OV                                               # noqa: E402

N = 250


def q(**kw):
    return {k: [str(v)] for k, v in kw.items()}


def links(html):
    return [h.replace('&amp;', '&') for h in re.findall(r'<th[^>]*data-href="([^"]+)"', html)]


def body_ids(html, pat):
    tb = html.split('<tbody>', 1)[1].split('</tbody>', 1)[0]
    return re.findall(pat, tb)


def prestige_values(keys, seed=5):
    """Distinct-ish values with ties and gaps; the global maximum sits deep in the default order."""
    rng = random.Random(seed)
    vals = {}
    for i, k in enumerate(keys):
        vals[k] = None if i % 17 == 3 else round(rng.uniform(1, 60), 1) if i % 9 else 33.3   # ties at 33.3
    vals[keys[230]] = 99.9                                                 # page 3 in the default order
    return vals


class CourseWorld:
    def __init__(self):
        self.ids = [f'C{i:03d}' for i in range(N)]
        self._courses = {cid: {'name': f'Course {(i * 37) % N:03d}', 'city': f'City {i % 13}', 'country':
                               ('USA', 'Japan', 'Spain')[i % 3], 'class': 'ABC'[i % 3], 'layouts': {'main': 1},
                               'subdivision': f'Sub {i % 5}'} for i, cid in enumerate(self.ids)}
        self.a, self.live = None, None
        self.pres = prestige_values(self.ids)

    def courses(self):
        return self._courses


class TourWorld:
    def __init__(self):
        self.ids = [f'S{i:03d}' for i in range(N)]
        series = {sid: {'name': f'Event {(i * 53) % N:03d}', 'tour': 'PT', 'tier': 1 + i % 6, 'kind': 'pro',
                        'category': 'regular'} for i, sid in enumerate(self.ids)}
        self.a = None
        self.live = NS(series=series, editions={})
        self.pres = prestige_values(self.ids, seed=9)

    def tours(self):
        return {'PT': {'name': 'Premier Tour'}}


class PeopleWorld:
    def __init__(self, role):
        self.role = role
        self.ids = list(range(1, N + 1))
        pres = prestige_values(self.ids, seed=13)
        self.pres = pres
        self._people = {}
        for pid in self.ids:
            p = {'name': f'Person {(pid * 61) % N:03d}', 'country': ('USA', 'ENG', 'JPN')[pid % 3], 'born': 1990 + pid % 20,
                 'roles': [role]}
            if role == 'golfer':
                p['golfer'] = {'tour': 'PT', 'lifestyle': 'full_time', 'status': 'pro', 'prestige': pres[pid]}
            else:
                p[role] = {'status': 'active', 'reputation': pres[pid]}
            self._people[pid] = p
        self.a = None
        self.live = NS(wr={pid: pid for pid in self.ids[:200]}, people={pid: {'prestige': pres[pid]} for pid in self.ids},
                       coach_of={}, caddie_of={})

    def all_people(self):
        return list(self.ids)

    def person(self, pid):
        return self._people.get(pid)

    def person_link(self, pid):
        return f'<a href="/golfer/{pid}">{self._people[pid]["name"]}</a>'

    def tours(self):
        return {'PT': {'name': 'Premier Tour'}}


def expected(rows, value, desc):
    """The reference order: by name then id, then by value (stable), missing values last."""
    rows = sorted(rows, key=lambda r: (r[1], r[0]))
    known = [r for r in rows if value(r) is not None]
    known.sort(key=value, reverse=desc)
    return [r[0] for r in known + [r for r in rows if value(r) is None]]


class Traversal:
    """Shared checks: the pages together are the whole list in the reference order, no row twice or missing."""

    def pages(self, render, pat, **kw):
        out, page, last = [], 1, 1
        while page <= last:
            html = render(q(page=page, **kw))
            out += body_ids(html, pat)
            last = int(re.search(r'page \d+ of (\d+)', html).group(1))
            page += 1
        return out


class CourseTests(unittest.TestCase, Traversal):
    def setUp(self):
        self.w = CourseWorld()
        p = mock.patch.object(OP, 'latest', lambda w: {'courses': self.w.pres, 'events': {}})
        p.start()
        self.addCleanup(p.stop)

    def render(self, query):
        return O.courses_page(self.w, query)[1]

    def ref(self, desc):
        rows = [(cid, self.w._courses[cid]['name']) for cid in self.w.ids]
        return expected(rows, lambda r: self.w.pres[r[0]], desc)

    def test_prestige_both_directions_over_every_page(self):
        pat = r'href="/course/([^"]+)"'
        for d, desc in (('desc', True), ('asc', False)):
            got = self.pages(self.render, pat, sort='prestige', dir=d)
            self.assertEqual(got, self.ref(desc), d)
            self.assertEqual(len(got), N)
            self.assertEqual(len(set(got)), N)                            # no duplicates, nothing missing
        self.assertEqual(self.pages(self.render, pat, sort='prestige', dir='desc')[0], self.w.ids[230])   # the max

    def test_missing_last_both_ways_and_ties_by_name(self):
        pat = r'href="/course/([^"]+)"'
        for d in ('desc', 'asc'):
            got = self.pages(self.render, pat, sort='prestige', dir=d)
            missing = [c for c in self.w.ids if self.w.pres[c] is None]
            self.assertEqual(set(got[-len(missing):]), set(missing))
        ties = [c for c in self.pages(self.render, pat, sort='prestige', dir='desc') if self.w.pres[c] == 33.3]
        self.assertEqual(ties, sorted(ties, key=lambda c: (self.w._courses[c]['name'], c)))

    def test_heading_links_keep_filters_reset_page_and_drop_tsort(self):
        html = self.render(q(country='USA', q='course', page=2, tsort='0.6.a', sort='prestige', dir='desc'))
        for h in links(html):
            a = parse_qs(urlsplit(h).query)
            self.assertEqual(a['country'], ['USA'])
            self.assertEqual(a['q'], ['course'])
            self.assertNotIn('page', a)
            self.assertNotIn('tsort', a)
        prestige = [h for h in links(html) if 'sort=prestige' in h][0]
        self.assertIn('dir=asc', prestige)                                # the sorted column turns the other way
        self.assertIn('aria-sort="descending"', html)
        self.assertIn('data-server-sort="1"', html)
        self.assertNotIn('tsort', html.split('</table>', 1)[1])           # the pager drops it too
        self.assertIn('<input type="hidden" name="sort" value="prestige">', html)   # the filter form keeps the sort
        self.assertIn('<input type="hidden" name="dir" value="desc">', html)

    def test_filtered_list_is_sorted_whole(self):
        pat = r'href="/course/([^"]+)"'
        got = self.pages(self.render, pat, sort='prestige', dir='desc', country='Japan')
        rows = [(c, self.w._courses[c]['name']) for c in self.w.ids if self.w._courses[c]['country'] == 'Japan']
        self.assertEqual(got, expected(rows, lambda r: self.w.pres[r[0]], True))

    def test_list_by_prestige_link_is_descending_without_tsort(self):
        html = self.render(q(tsort='0.6.a', country='USA'))
        link = re.search(r'<a href="(/courses\?[^"]+)">List by prestige', html).group(1).replace('&amp;', '&')
        a = parse_qs(urlsplit(link).query)
        self.assertEqual((a['sort'], a['dir'], a['country']), (['prestige'], ['desc'], ['USA']))
        self.assertNotIn('tsort', a)

    def test_default_order_unchanged(self):
        got = body_ids(self.render(q()), r'href="/course/([^"]+)"')
        want = [c for c, _ in sorted(((c, self.w._courses[c]) for c in self.w.ids),
                                    key=lambda x: (x[1]['country'], x[1]['name']))][:100]
        self.assertEqual(got, want)


class TournamentTests(unittest.TestCase, Traversal):
    def setUp(self):
        self.w = TourWorld()
        p = mock.patch.object(OP, 'latest', lambda w: {'events': self.w.pres, 'courses': {}})
        p.start()
        self.addCleanup(p.stop)

    def render(self, query):
        return O.tournaments(self.w, query)[1]

    def test_prestige_both_directions_over_every_page(self):
        pat = r'href="/series/([^"]+)"'
        rows = [(s, self.w.live.series[s]['name']) for s in self.w.ids]
        for d, desc in (('desc', True), ('asc', False)):
            got = self.pages(self.render, pat, sort='prestige', dir=d)
            self.assertEqual(got, expected(rows, lambda r: self.w.pres[r[0]], desc), d)
            self.assertEqual(len(set(got)), N)

    def test_tier_column_sorts_whole_list(self):
        pat = r'href="/series/([^"]+)"'
        rows = [(s, self.w.live.series[s]['name']) for s in self.w.ids]
        got = self.pages(self.render, pat, sort='tier', dir='desc')
        self.assertEqual(got, expected(rows, lambda r: self.w.live.series[r[0]]['tier'], True))


class PeopleTests(unittest.TestCase, Traversal):
    def check(self, role, path_fn, key):
        w = PeopleWorld(role)
        render = lambda query: path_fn(w, query)[1]
        pat = r'href="/golfer/(\d+)"'
        rows = [(pid, w._people[pid]['name']) for pid in w.ids]
        for d, desc in (('desc', True), ('asc', False)):
            got = [int(x) for x in self.pages(render, pat, sort=key, dir=d)]
            self.assertEqual(got, expected(rows, lambda r: w.pres[r[0]], desc), (role, d))
            self.assertEqual(len(set(got)), N)
        html = render(q(sort=key, dir='desc', nation='USA', tsort='0.4.a'))
        self.assertIn('data-server-sort="1"', html)
        for h in links(html):
            a = parse_qs(urlsplit(h).query)
            self.assertEqual(a['nation'], ['USA'])
            self.assertNotIn('tsort', a)
            self.assertNotIn('page', a)

    def test_golfers(self):
        self.check('golfer', O.golfers, 'reputation')

    def test_coaches(self):
        self.check('coach', lambda w, query: O.directory(w, query, 'coach'), 'reputation')

    def test_caddies(self):
        self.check('caddie', lambda w, query: O.directory(w, query, 'caddie'), 'reputation')

    def test_a_heading_sort_is_shown_in_the_sort_control(self):
        w = PeopleWorld('golfer')
        html = O.golfers(w, q(sort='nation', dir='asc'))[1]
        self.assertIn('<option value="nation" selected>nation</option>', html)


class StaleBrowserSortInViews(unittest.TestCase):
    """A browser column sort (tsort) is never part of a server-sorted list's view: not in the page's query, the last
    view, the trail ("Back to"), the Save view form, a saved view or a description -- also when it was persisted
    before. Other lists keep it."""

    def setUp(self):
        import tempfile
        import shutil
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.w = NS(read_only=False, path=self.dir)

    def test_opened_records_and_restores_without_tsort(self):
        got, _ = OV.opened(self.w, '/courses', q(sort='prestige', dir='desc', tsort='0.6.a'))
        self.assertNotIn('tsort', got)
        st = OV.state(self.w)
        self.assertEqual(st['last']['/courses'], 'dir=desc&sort=prestige')
        self.assertEqual(st['trail'], ['/courses', 'dir=desc&sort=prestige'])
        back = OV.back_link(self.w, '/course/C001')
        self.assertIn('sorted by prestige (descending)', back)
        self.assertNotIn('table sorted by column', back)
        self.assertNotIn('tsort', back)
        form = OV.bar(self.w, '/courses', q(sort='prestige', dir='desc', tsort='0.6.a'))
        self.assertIn('name="query" value="dir=desc&amp;sort=prestige"', form)

    def test_a_stale_persisted_view_is_cleaned_when_used(self):
        OV._save(self.w, {'last': {'/golfers': 'sort=reputation&dir=desc&tsort=0.6.a'},
                          'trail': ['/golfers', 'sort=reputation&dir=desc&tsort=0.6.a'],
                          'saved': [{'id': 'x', 'name': 'Old', 'path': '/golfers',
                                     'query': 'sort=reputation&dir=desc&tsort=0.6.a', 'added': ''}]})
        self.w.__dict__.pop('_views', None)
        restored, note = OV.opened(self.w, '/golfers', {})              # from the menu: the last view
        self.assertNotIn('tsort', restored)
        self.assertNotIn('tsort', note)
        self.assertNotIn('tsort', OV.state(self.w)['last']['/golfers'])
        page = OV.views_page(self.w, {})[1]
        self.assertNotIn('tsort', page)
        self.assertNotIn('table sorted by column', page)
        chips = OV.bar(self.w, '/golfers', q(sort='reputation', dir='desc'))
        self.assertIn('class="on"', chips)                                 # the saved view is the one shown

    def test_save_drops_tsort_on_server_lists_only(self):
        OV.save(self.w, 'A', '/caddies', 'sort=reputation&dir=asc&tsort=0.4.d')
        OV.save(self.w, 'B', '/nations', 'tsort=0.1.d')
        saved = {x['name']: x['query'] for x in OV.state(self.w)['saved']}
        self.assertEqual(saved['A'], 'dir=asc&sort=reputation')
        self.assertEqual(saved['B'], 'tsort=0.1.d')                        # a browser-sorted list keeps it
        self.assertIn('table sorted by column 2', OV.describe('/nations', 'tsort=0.1.d'))


class MissingSubdivision(unittest.TestCase):
    def test_missing_state_or_province_sorts_last_both_ways(self):
        w = CourseWorld()
        for i, cid in enumerate(w.ids):
            if i % 10 == 0:
                w._courses[cid]['subdivision'] = None                     # not recorded: shown as 'unknown'
        with mock.patch.object(OP, 'latest', lambda w_: {'courses': w.pres, 'events': {}}):
            for d in ('asc', 'desc'):
                got = []
                for page in (1, 2, 3):
                    got += body_ids(O.courses_page(w, q(sort='subdivision', dir=d, page=page))[1],
                                    r'href="/course/([^"]+)"')
                missing = [c for c in w.ids if w._courses[c]['subdivision'] is None]
                self.assertEqual(set(got[-len(missing):]), set(missing), d)
            html = O.courses_page(w, q(sort='subdivision', dir='asc', page=3))[1]
            self.assertIn('<td>unknown</td>', html)                          # still shown as before


class ClientSide(unittest.TestCase):
    def test_script_never_resorts_a_server_sorted_table_and_drops_a_stale_tsort(self):
        js = OV.SORT_JS
        self.assertIn("table.hasAttribute('data-server-sort')", js)
        self.assertIn("t.hasAttribute('data-server-sort')", js)
        self.assertIn("u0.searchParams.delete('tsort')", js)

    def test_bounded_tables_say_they_sort_the_rows_shown(self):
        html = O.table(['A', 'B'], [['1', '2']])
        self.assertIn('Sort the rows shown by this column', html)
        self.assertNotIn('data-server-sort', html)


if __name__ == '__main__':
    unittest.main()
