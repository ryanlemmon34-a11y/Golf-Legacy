"""Nation counts link to exactly the people they count: on the Nations page and a nation's page every count (people,
active golfers, world top 100 now, major champions in the archived seasons) opens a directory list with that many
rows, and the right people -- checked against the records directly (nationality, the running world's lifestyles and
ranking, the season files' major winners). Drawing them changes nothing the simulation keeps.

Run from the project folder:  python -m unittest tests.test_nation_links -v
"""
from __future__ import annotations

import hashlib
import html
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import equivalence_check as EQ                                        # noqa: E402
import observer as O                                                  # noqa: E402

COLUMNS = ('People', 'Active golfers', 'In world top 100 now', 'Major champions (archived)')


class NationLinks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.path = cls.tmp / 'w'
        s = Session.create(cls.path, seed=47, workers=1, world=generate_world(seed=47, scale=0.03))
        s.advance(52 + 4)                                               # one archived season, four weeks played
        s.close()
        cls.w = O.World(cls.path, workers=1)
        cls.w.reload()

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def page(self, path):
        u = urlparse(html.unescape(path))
        return O.render(self.w, u.path, parse_qs(u.query))[1]

    def listed(self, href):
        """[pid] of every row of a directory list, page by page, and the row total the pager states."""
        pids, url, total = [], href, None
        while url:
            body = self.page(url)
            tab = body[body.index('<table'):body.index('</table>')]
            rows = tab.split('<tr')[2:]                                 # (after the header row)
            for r in rows:
                got = re.findall(r'href="/golfer/(\d+)"', r)
                self.assertTrue(got, r)
                pids.append(int(got[0]))
            total = int(re.search(r'page \d+ of \d+ \(([\d,]+) rows\)', body).group(1).replace(',', ''))
            nxt = re.search(r'<a href="([^"]+)">Next →</a>', body)
            url = nxt.group(1) if nxt else None
            if url:
                self.assertTrue(url.startswith(urlparse(href).path + '?'), url)   # (paging stays on that list)
        return pids, total

    def expected(self):
        """{column: {nation: {pid}}} from the records themselves."""
        w = self.w
        out = {c: {} for c in COLUMNS}
        people = set(w.a.people) | set(w.live.people)
        country = lambda pid: (w.live.people.get(pid) or w.a.people.get(pid) or {}).get('country')
        champs = set()
        for y in w.a.years:
            for e in w.a.year(y)['events']:
                if w.a.world['series'][e['series']]['kind'] == 'major':
                    champs |= {g for site in e['finish'] for g, pos, _ in site if pos == 1}
        for pid in people:
            n = country(pid)
            lp = w.live.people.get(pid)
            golfer = lp if lp is not None and 'golfer' in lp['roles'] else (w.a.people.get(pid) or {}).get('golfer')
            add = lambda c: out[c].setdefault(n, set()).add(pid)
            add('People')
            if golfer and golfer.get('lifestyle') not in (None, 'retired'):
                add('Active golfers')
            if w.live.wr.get(pid, 10 ** 9) <= 100:
                add('In world top 100 now')
            if pid in champs:
                add('Major champions (archived)')
        return out

    def nations_table(self):
        """[(nation, [(count, href)])] of the Nations page."""
        body = self.page('/nations')
        out = []
        for r in body.split('<tr')[2:]:
            code = unquote(re.search(r'href="/nation/([^"]+)"', r).group(1))
            cells = re.findall(r'<a href="(/(?:search|golfers)\?[^"]+)">([\d,]+)</a>', r)
            out.append((code, [(int(n.replace(',', '')), h) for h, n in cells]))
        return out

    def test_the_world_has_something_to_count(self):
        want = self.expected()
        self.assertTrue(want['Major champions (archived)'])
        self.assertTrue(want['In world top 100 now'])

    def test_counts_are_the_records(self):
        want = self.expected()
        rows = self.nations_table()
        self.assertEqual({n for n, _ in rows}, set(want['People']))
        for n, cells in rows:
            self.assertEqual(len(cells), len(COLUMNS))
            for (count, _), c in zip(cells, COLUMNS):
                self.assertEqual(count, len(want[c].get(n, ())), (n, c))
        for i, c in enumerate(COLUMNS):                                # every nation together: the whole population
            self.assertEqual(sum(cells[i][0] for _, cells in rows), sum(len(x) for x in want[c].values()), c)

    def test_each_link_lists_exactly_those_people(self):
        want = self.expected()
        rows = self.nations_table()
        big = sorted(rows, key=lambda r: -r[1][0][0])[:3]              # the largest (several pages) and the smallest
        small = sorted(rows, key=lambda r: r[1][0][0])[:2]
        champs = [r for r in rows if r[1][3][0]][:2]
        self.assertGreater(big[0][1][0][0], O.PAGE_SIZE)               # (a list over several pages)
        checked = 0
        for n, cells in big + small + champs:
            for (count, href), c in zip(cells, COLUMNS):
                pids, total = self.listed(href)
                self.assertEqual(len(pids), count, (n, c, href))
                self.assertEqual(total, count, (n, c, href))
                self.assertEqual(set(pids), want[c].get(n, set()), (n, c))
                self.assertEqual(len(set(pids)), len(pids))
                checked += 1
        self.assertGreaterEqual(checked, 12)

    def test_a_nations_page_has_the_same_counts_and_links(self):
        for n, cells in self.nations_table()[:5]:
            body = self.page(f'/nation/{quote(n)}')
            for (count, href), c in zip(cells, COLUMNS):
                self.assertIn(f'{c} <a href="{href}">{count:,}</a>', body)
            self.assertIn('each count links to the list of exactly those people', html.unescape(body))

    def test_the_filters_are_on_the_directory(self):
        body = self.page('/golfers?active=1&top=100&champion=major')
        for name in ('active', 'top', 'champion'):
            self.assertIn(f'<select name="{name}">', body)
        self.assertIn('action="/search"', self.page('/search?nation=USA'))

    def test_drawing_changes_nothing(self):
        def state():
            files = {p.relative_to(self.path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(self.path.rglob('*')) if p.is_file() and not p.name.startswith('observer')}
            return EQ.parts(self.w.session, self.path), files
        before = state()
        rows = self.nations_table()
        for n, cells in rows[:3]:
            self.page(f'/nation/{quote(n)}')
            for _, href in cells:
                self.page(href)
        self.assertEqual(state(), before)


if __name__ == '__main__':
    unittest.main()
