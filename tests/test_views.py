"""Saved table views and navigation state: a list page's season, scope, filters, sort, direction and page survive
opening a profile and coming back (the profile's "Back to" link, the menu, a new observer session), named views
are kept until removed, a browser-side column sort is kept in the address, and none of it is simulation state.

Run from the project folder:  python -m unittest tests.test_views -v
"""
from __future__ import annotations

import html
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
from golfsim import scopes as SC                                      # noqa: E402
import observer_app as OA                                             # noqa: E402
import observer_views as V                                            # noqa: E402


def files(d):
    return {p.relative_to(d).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns)
            for p in Path(d).rglob('*') if p.is_file()}


def table(page):
    return re.search(r'<table[ >].*?</table>', page, re.S).group(0)


class Views(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.lib = cls.tmp / 'lib'
        s = Session.create(cls.lib / 'demo', seed=29, workers=1, world=generate_world(seed=29, scale=0.03))
        s.advance(52 + 3)                                               # one archived season and three weeks
        s.close()
        cls.start()

    @classmethod
    def start(cls):
        cls.app = OA.App(cls.lib, workers=1)
        cls.httpd = OA.start_server(cls.app, 0)
        cls.base = f'http://127.0.0.1:{cls.httpd.server_address[1]}'
        cls.post('/worlds/open', {'name': 'demo'})
        cls.app.jobs.wait(120)
        w = cls.app.world                                               # (the store belongs to the renderer thread)
        if cls.app.renderer.call(lambda: w.statistics()[0]) is None:
            w._builder.wait(300)

    @classmethod
    def stop(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.app.shutdown()

    @classmethod
    def tearDownClass(cls):
        cls.stop()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def get(cls, p):
        return urlopen(cls.base + p, timeout=120).read().decode()

    @classmethod
    def post(cls, p, d, referer=None):
        r = Request(cls.base + p, data=urlencode(d, doseq=True).encode())
        if referer:
            r.add_header('Referer', cls.base + referer)
        return urlopen(r, timeout=120).read().decode()

    def view(self):
        y = self.app.world.a.years[-1]
        return {'year': str(y), 'tour': SC.MAJORS_PREMIER, 'sort': 'starts', 'dir': 'asc', 'page': '1'}

    def test_profile_back_link_returns_to_the_exact_view(self):
        q = urlencode(self.view())
        stats = self.get(f'/stats?{q}')
        first = re.search(r'href="/golfer/(\d+)"', table(stats)).group(1)
        prof = self.get(f'/golfer/{first}')
        back = re.search(r'<p class="back"><a href="([^"]+)">← Back to Stats</a>', prof)
        self.assertIsNotNone(back)
        target = html.unescape(back.group(1))
        self.assertEqual(parse_qs(urlparse(target).query), parse_qs(q))   # season, scope, sort, direction, page
        self.assertIn('Majors + Premier', prof)
        self.get(f'/golfer/{first}?tab=results')                       # still there after more pages
        self.assertIn(back.group(0), self.get(f'/golfer/{first}?tab=results'))
        cells = lambda p: re.sub(r'<[^>]+>', '|', table(p))            # (links may list the same view's keys
        self.assertEqual(cells(self.get(target)), cells(stats))           # in another order)

    def test_menu_restores_the_last_view_and_default_resets_it(self):
        self.get('/money?' + urlencode({'year': self.view()['year'], 'sort': 'wins', 'page': '2'}))
        again = self.get('/money')                                     # from the menu: no address of its own
        self.assertIn('Your last view of this page', again)
        self.assertIn('sorted by wins', again)
        self.assertIn('page 2 of', again)
        default = self.get('/money?default=1')
        self.assertNotIn('Your last view', default)
        self.assertIn('page 1 of', default)
        self.assertNotIn('Your last view', self.get('/money'))         # the default is now the last view

    def test_filters_clear_link_gives_the_default(self):
        page = self.get('/golfers?q=a')
        self.assertIn('href="/golfers?default=1">Clear</a>', page)

    def test_saved_views_and_a_new_session(self):
        q = urlencode(self.view())
        self.post('/views/save', {'name': 'Majors by starts', 'path': '/stats', 'query': q}, referer=f'/stats?{q}')
        page = self.get('/stats')
        self.assertIn('>Majors by starts</a>', page)
        listing = self.get('/views')
        self.assertIn('Majors by starts', listing)
        vid = V.state(self.app.world)['saved'][-1]['id']
        type(self).stop()                                              # a new observer session
        type(self).start()
        page = self.get('/stats')
        self.assertIn('>Majors by starts</a>', page)                   # saved views kept
        self.assertIn('Your last view of this page', page)             # and the last view
        self.post('/views/remove', {'id': vid}, referer='/views')
        self.assertNotIn('Majors by starts', self.get('/views'))

    def test_browser_sort_is_kept_in_the_address(self):
        self.post('/views/last', {'url': '/golfers?q=e&tsort=0.2.d'})
        page = self.get('/golfers')
        self.assertIn('table sorted by column 3 (descending)', page)
        self.assertIn("searchParams.get('tsort')", page)              # the page applies it when it opens
        prof = self.get('/golfer/1')
        self.assertIn('tsort=0.2.d', prof)

    def test_golf_statistics_sort_both_ways(self):
        import observer_golf as OG
        import observer_stats as ST
        w = self.app.world
        y = w.a.years[-1]
        data = self.app.renderer.call(lambda: ST.query(w.statistics()[0], [y], None, None, cols=ST.GOLF))
        best, worst = OG.stats_rows(w, data, 'scoring', 0), OG.stats_rows(w, data, 'scoring', 0, worst_first=True)
        value = lambda rows: [OG.GS.metric('scoring', r) for _, r in rows if OG.GS.metric('scoring', r) is not None]
        self.assertGreater(len(value(best)), 10)
        self.assertEqual(value(worst), value(best)[::-1])               # the same golfers, the other way round
        page = self.get('/stats?' + urlencode({'show': 'golf', 'year': y, 'sort': 'scoring', 'min': '0', 'dir': 'worst'}))
        self.assertIn('Sorted worst first', page)
        self.assertEqual(re.search(r'href="/golfer/(\d+)"', table(page)).group(1), str(worst[0][0]))
        self.assertIn('dir=worst', self.get('/stats?' + urlencode({'show': 'golf', 'sort': 'scoring'})))

    def test_views_are_not_simulation_state(self):
        before = files(self.lib / 'demo')
        gen = self.app.world.live.generation
        self.get('/stats?' + urlencode(self.view()))
        self.post('/views/save', {'name': 'x', 'path': '/stats', 'query': 'year=all'}, referer='/stats')
        after = files(self.lib / 'demo')
        changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
        self.assertTrue(changed)
        for k in changed:                                              # only browsing files beside the world
            self.assertTrue(k.startswith('observer'), k)                # (views, statistics cache, the log)
        self.assertEqual(self.app.world.live.generation, gen)


BROWSER_JS = r"""
const { chromium } = require('playwright');
(async () => {
  const base = process.argv[2], out = {};
  const b = await chromium.launch(), pg = await b.newPage();
  const names = () => pg.$$eval('table.sortable tbody tr td:first-child', c => c.map(x => x.textContent));
  await pg.goto(base + '/golfers?q=a');
  out.before = await names();
  await pg.click('table.sortable th:nth-child(1)');            // sort by the first column, then reverse it
  await pg.click('table.sortable th:nth-child(1)');
  out.url = pg.url();
  out.sorted = await names();
  await pg.click('table.sortable tbody tr:first-child a[href^="/golfer/"]');
  await pg.waitForURL('**/golfer/**');
  out.back_link = (await pg.content()).includes('Back to Golfers');
  await pg.goBack();
  await pg.waitForURL('**/golfers?**');
  out.after_back = await names();
  await pg.goto(base + '/golfers');                            // from the menu
  out.menu_url = pg.url();
  out.menu_aria = await pg.getAttribute('table.sortable th:nth-child(1)', 'aria-sort');
  out.menu = await names();
  await b.close();
  console.log(JSON.stringify(out));
})().catch(e => { console.error(e); process.exit(1); });
"""


def node_playwright():
    import subprocess
    try:
        return subprocess.run(['node', '-e', "require('playwright')"], capture_output=True, timeout=60).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


@unittest.skipUnless(node_playwright(), 'Node.js with Playwright not available')
class BrowserSort(unittest.TestCase):
    """In a real browser (Chromium): a column sort survives opening a profile and pressing Back, and the menu
    restores it (address and order)."""

    def test_sort_back_and_menu(self):
        import json
        import subprocess
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        s = Session.create(tmp / 'lib' / 'demo', seed=31, workers=1, world=generate_world(seed=31, scale=0.02))
        s.advance(3)
        s.close()
        app = OA.App(tmp / 'lib', workers=1)
        httpd = OA.start_server(app, 0)
        self.addCleanup(app.shutdown)
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        app.renderer.call(app._install, tmp / 'lib' / 'demo', None)
        script = tmp / 'browser.js'
        script.write_text(BROWSER_JS)
        r = subprocess.run(['node', str(script), f'http://localhost:{httpd.server_address[1]}'], capture_output=True,
                           text=True, timeout=300, cwd=tmp)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        out = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertIn('tsort=0.0.d', out['url'])
        self.assertEqual(out['sorted'], sorted(out['before'], key=str.lower, reverse=True))
        self.assertTrue(out['back_link'])
        self.assertEqual(out['after_back'], out['sorted'])            # Back: the same order
        self.assertIn('tsort=0.0.d', out['menu_url'])                   # the menu: the address and order restored
        self.assertEqual(out['menu_aria'], 'descending')
        self.assertEqual(out['menu'], out['sorted'])


if __name__ == '__main__':
    unittest.main()
