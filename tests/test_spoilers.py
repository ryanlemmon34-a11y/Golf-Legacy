"""Hide results (roadmap v14, spoiler-safe entry): a persistent Hide results setting; lists show hidden editions
without their winners; an event opens on the replay at round one (or the round last watched) with no winner, final
places or playoff result until an explicit Reveal final result; the watched round and the reveal are the same on
every page and after a restart; Show results shows everything again. Replays read recorded rounds only: nothing
is simulated and the saved world is never touched.

Run from the project folder:  python -m unittest tests.test_spoilers -v
"""
from __future__ import annotations

import hashlib
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
from golfsim.population import generate_world                            # noqa: E402
from golfsim.session import Session                                       # noqa: E402
import observer as O                                                      # noqa: E402
import observer_spoilers as SP                                            # noqa: E402


def digest(folder):
    """Every file of the saved world except the observer's own (spoiler setting, shortlist, caches) and the
    archive's derived index (a SQLite cache rebuilt from the season files, which opening a world touches)."""
    out = {}
    for p in sorted(Path(folder).rglob('*')):
        rel = p.relative_to(folder).as_posix()
        if (p.is_file() and not rel.startswith('observer_') and 'observer_cache' not in rel
                and not rel.endswith('.lock') and not rel.startswith('archive/index.sqlite')):
            out[rel] = hashlib.sha1(p.read_bytes()).hexdigest()
    return out


class Spoilers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=61, workers=1, world=generate_world(seed=61, scale=0.03))
        s.advance(52 + 10)
        s.close()
        cls.before = digest(cls.tmp / 'w')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        (self.tmp / 'w' / SP.FILE).unlink(missing_ok=True)
        self.w = O.World(self.tmp / 'w', workers=1)
        self.w.reload()
        self.addCleanup(self.w.close)
        if self.w.statistics()[0] is None:
            self.w._builder.wait(300)

    def header(self):
        return O.page(self.w, 'x', '')

    def page(self, path, w=None):
        u = urlparse(path)
        return O.render(w or self.w, u.path, parse_qs(u.query))[1]

    def edition(self, rounds=2, playoff=None):
        """A current-season stroke-play edition with at least `rounds` recorded rounds (with a playoff if asked)."""
        for e in sorted(self.w.live.editions.values(), key=lambda e: (-(e.get('rounds') or 0), e['id'])):
            if e.get('match_play') or (e.get('rounds') or 0) < rounds or len(e['sites']) != 1:
                continue
            if playoff is not None and bool(e.get('playoff')) != playoff:
                continue
            return e
        self.skipTest('no such edition in this small world')

    def test_hidden_lists_and_the_event_entry(self):
        e = self.edition()
        eid, winner = e['id'], O._winner(e)
        cal = self.page('/calendar?status=played')
        self.assertIn(self.w.person_link(winner), cal)                     # off by default
        SP.set_hide(self.w, True, 'season')
        cal = self.page('/calendar?status=played')
        self.assertIn('Results hidden', self.header())
        row = re.search(rf'href="/event/{re.escape(eid.replace(":", "%3A"))}".*?</tr>', cal, re.S).group(0)
        self.assertIn('hidden', row)
        self.assertIn('view=rounds&amp;round=1', row)                      # the entry is the replay at round one
        self.assertNotIn('/golfer/', row)
        for path in ('/', f'/series/{e["series"]}', f'/tour/{e["tour"]}'):
            body = self.page(path)
            for m in re.finditer(rf'/event/{re.escape(eid.replace(":", "%3A"))}"[^<]*</a></td>.*?</tr>', body, re.S):
                self.assertNotIn(self.w.person_link(winner), m.group(0), path)
        ev = self.page(f'/event/{eid}')
        self.assertIn('Results hidden', ev)
        self.assertNotIn('Winner:', ev)
        self.assertIn('Replay', ev)
        self.assertIn('<strong>after round 1</strong>', ev)
        self.assertIn('Reveal final result', ev)
        for view in ('final', 'stats'):
            gate = self.page(f'/event/{eid}?view={view}')
            self.assertIn('are hidden', gate)
            self.assertNotIn('Winner:', gate)
            self.assertNotIn('How they got in', gate)                      # no final table
        self.assertEqual(digest(self.tmp / 'w'), self.before)              # nothing in the world was touched

    def test_watching_is_remembered_and_the_final_needs_a_reveal(self):
        e = self.edition(rounds=2)
        eid, n = e['id'], e['rounds']
        SP.set_hide(self.w, True, 'season')
        self.page(f'/event/{eid}?view=rounds&round=2')
        self.assertEqual(SP.watched(self.w, eid), 2)
        self.assertIn('<strong>after round 2</strong>', self.page(f'/event/{eid}'))   # resumes where they left off
        self.assertIn('Resume at round 2', self.page('/calendar?status=played'))
        w2 = O.World(self.tmp / 'w', workers=1)                             # after a restart: the same
        w2.reload()
        self.addCleanup(w2.close)
        self.assertTrue(SP.hidden(w2, eid))
        self.assertEqual(SP.watched(w2, eid), 2)
        last = self.page(f'/event/{eid}?view=rounds&round={n}')
        self.assertIn('After regulation', last)
        self.assertNotIn('Won playoff', last)
        self.assertNotIn('Lost playoff', last)
        self.assertNotIn('players tied', last)
        self.assertTrue(SP.hidden(self.w, eid))                            # watching the last round is not a reveal
        SP.reveal(self.w, eid)
        self.assertFalse(SP.hidden(self.w, eid))
        final = self.page(f'/event/{eid}')
        self.assertIn('Winner:', final)
        self.assertIn(self.w.person_link(O._winner(e)), self.page('/calendar?status=played'))
        self.assertEqual(digest(self.tmp / 'w'), self.before)

    def test_a_playoff_stays_hidden_until_revealed(self):
        e = self.edition(rounds=2, playoff=True)
        eid, n = e['id'], e['rounds']
        SP.set_hide(self.w, True, 'season')
        last = self.page(f'/event/{eid}?view=rounds&round={n}')
        self.assertNotIn('playoff', last.split('<tbody>')[1].split('</tbody>')[0].lower())
        self.assertNotIn('extra hole', last)
        SP.reveal(self.w, eid)
        self.assertIn('Won playoff', self.page(f'/event/{eid}'))

    def test_profiles_hide_places_and_disclose_totals(self):
        e = self.edition()
        winner = O._winner(e)
        SP.set_hide(self.w, True, 'season')
        res = self.page(f'/golfer/{winner}?tab=results')
        self.assertIn('results hidden', res)
        row = re.search(rf'/event/{re.escape(e["id"].replace(":", "%3A"))}".*?</tr>', res, re.S).group(0)
        self.assertIn('hidden', row)
        wins = self.page(f'/golfer/{winner}?tab=results&outcome=win')      # a finish filter leaves hidden ones out
        self.assertNotIn(f'/event/{e["id"].replace(":", "%3A")}"', wins)
        prof = self.page(f'/golfer/{winner}')
        self.assertIn('Results are hidden', prof)
        self.assertIn('Results are hidden', self.page('/stats'))           # totals say what they include
        self.assertIn('Results are hidden', self.page('/rankings'))

    def test_boundaries_and_show_results(self):
        e = self.edition()
        SP.set_hide(self.w, True, 'now')                                    # only results played from now on
        self.assertFalse(SP.hidden(self.w, e['id'], e['week']))
        self.assertEqual(SP.unrevealed(self.w), 0)
        SP.set_hide(self.w, True, 'all')                                    # every result, archived ones too
        old = next(iter(self.w.a.index.db.execute('SELECT event_id, week FROM editions LIMIT 1')))
        self.assertTrue(SP.hidden(self.w, old[0], old[1]))
        self.assertGreater(SP.unrevealed(self.w), len(self.w.live.editions))
        SP.set_hide(self.w, True, 'season')
        self.page(f'/event/{e["id"]}?view=rounds&round=2')
        SP.set_hide(self.w, False)
        self.assertFalse(SP.hidden(self.w, e['id']))
        self.assertIn('>Hide results</button>', self.header())
        self.assertEqual(SP.watched(self.w, e['id']), 2)                    # what was watched is kept


class SpoilersOverHttp(unittest.TestCase):
    def test_hide_reveal_and_show_over_http(self):
        import observer_app as OA
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        lib = tmp / 'lib'
        lib.mkdir()
        s = Session.create(lib / 'demo', seed=67, workers=1, world=generate_world(seed=67, scale=0.02))
        s.advance(12)
        s.close()
        app = OA.App(lib, workers=1)
        self.addCleanup(app.shutdown)
        app.renderer.call(app._install, lib / 'demo', None)
        httpd = OA.start_server(app, 0)
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        base = f'http://127.0.0.1:{httpd.server_address[1]}'
        get = lambda p: urlopen(base + p, timeout=60).read().decode()
        post = lambda p, d, ref='/': urlopen(Request(base + p, data=urlencode(d).encode(),
                                                     headers={'Referer': base + ref}), timeout=60)
        self.assertIn('>Hide results</button>', get('/'))
        post('/spoilers', {'hide': '1', 'from': 'season'}, '/calendar')
        cal = get('/calendar?status=played')
        self.assertIn('Results hidden', cal)
        eid = re.search(r'href="/event/([^"?]+)\?view=rounds', cal).group(1).replace('%3A', ':')
        r = post('/spoilers', {'reveal': eid}, f'/event/{eid}')
        self.assertIn('/event/', r.geturl())
        self.assertIn('view=final', r.geturl())
        self.assertIn('Winner:', r.read().decode())
        post('/spoilers', {'hide': '0'})
        self.assertNotIn('Results hidden</span>', get('/calendar?status=played'))


if __name__ == '__main__':
    unittest.main()
