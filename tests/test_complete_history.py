"""The global Hide results setting is gone: every page reads the complete recorded history, a world that still
carries the old setting's file opens and shows everything, and ordinary replay remains -- the round-by-round
leaderboard (nothing after the round shown), scorecards, playoffs at the final round, and "Watch from round 1",
which always opens round one.

Run from the project folder:  python -m unittest tests.test_complete_history -v
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer as O                                                  # noqa: E402
import observer_app as OA                                             # noqa: E402
import observer_history as OH                                         # noqa: E402

OLD = {'format': 'golf-legacy-spoilers/1', 'hide': True, 'from': [0, 0],
       'revealed': {}}                                                 # (everything hidden, as an earlier build wrote it)


def text(html):
    """The page's words (markup and form fields removed)."""
    return re.sub(r'<[^>]+>', ' ', html)


class CompleteHistory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.path = cls.tmp / 'lib' / 'w'
        s = Session.create(cls.path, seed=103, workers=1, world=generate_world(seed=103, scale=0.03))
        s.advance(52 + 30)                                              # one archived season; this season to week 31
        s.close()
        (cls.path / 'observer_spoilers.json').write_text(json.dumps(OLD))
        cls.w = O.World(cls.path, workers=1)
        cls.w.reload()
        if cls.w.statistics()[0] is None:
            cls.w._builder.wait(300)
        cls.y = cls.w.a.years[0]

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def page(self, path):
        u = urlparse(path)
        return O.render(self.w, u.path, parse_qs(u.query))[1]

    def test_every_view_shows_the_complete_history(self):
        majors = OH.major_wins(self.w)
        idx = self.w.a.index
        archived = [r for r in idx.db.execute("SELECT year, week, event_id, series, winner FROM editions WHERE "
                                              "category = 'major' AND winner IS NOT NULL ORDER BY year, week")]
        live = [e for e in self.w.live.editions.values() if e.get('category') == 'major']
        self.assertEqual(len(majors), len(archived) + len(live))       # every major, archived and this season
        season = self.page(f'/season/{self.y}')
        table = season.split('<h2>Majors</h2>')[1].split('</table>')[0]
        for y, wk, eid, sid, win in archived:
            self.assertIn(f'/golfer/{win}"', table)                    # the season recap names its champions
        champ = archived[0][4]
        prof = self.page(f'/golfer/{champ}')
        self.assertIn(f'/event/{quote(archived[0][2])}"', prof)        # wins and moments on the profile
        stab = self.page(f'/golfer/{champ}?tab=season&year={self.y}')
        self.assertIn(f'/event/{quote(archived[0][2])}"', stab)        # the season page names the win
        self.assertIn(f'won the {self.w.series_name(archived[0][3])}'.lower(), text(stab).lower())
        rec = self.page('/records/youngest-major-champions')
        self.assertIn(f'/event/{quote(archived[0][2])}"', rec)
        ev = self.page(f'/event/{quote(archived[0][2])}')
        self.assertIn(f'Winner: <a href="/golfer/{champ}">', ev)        # an event opens on its final result
        for path in ('/', f'/season/{self.y}', f'/golfer/{champ}', f'/golfer/{champ}?tab=results', '/records',
                     '/records/most-wins', '/moments', '/calendar', '/grand-slam', '/stats', '/goat', '/qualification',
                     f'/cohort?event={quote(archived[0][2])}', f'/compare?ids={champ}', '/rankings?kind=points',
                     '/golf-records/largest-margin', f'/series/{archived[0][3]}', f'/event/{quote(live[0]["id"])}'):
            html = self.page(path)
            words = text(html).lower()
            for phrase in ('results hidden', 'hide results', 'unrevealed', 'reveal final', 'held back',
                           'hidden results', 'are hidden'):
                self.assertNotIn(phrase, words, (path, phrase))
        self.assertNotIn('Hide results', O.page(self.w, 't', 'b'))      # no toggle in the header

    def test_grand_slam_and_goat_read_the_same_majors(self):
        import observer_goat as G
        slams = OH.grand_slams(self.w)
        vals, _ = G.careers(self.w, '')
        for pid, d in slams.items():
            self.assertEqual(vals[pid]['majors'], sum(1 for m in OH.major_wins(self.w) if m[4] == pid))
            self.assertEqual(vals[pid]['slam'], 1 if d['complete'] else 0)

    def test_replay_and_watch_from_round_one(self):
        e = next(e for e in sorted(self.w.live.editions.values(), key=lambda e: e['id'])
                 if (e.get('rounds') or 0) >= 3 and not e.get('match_play') and len(e['sites']) == 1)
        eid = quote(e['id'])
        final = self.page(f'/event/{eid}')
        restart = re.search(r'href="([^"]*)">Watch from round 1</a>', final).group(1)
        self.assertEqual(parse_qs(urlparse(restart.replace('&amp;', '&')).query), {'view': ['rounds'], 'round': ['1']})
        r3 = self.page(f'/event/{eid}?view=rounds&round=3')
        self.assertIn('<strong>after round 3</strong>', r3)
        self.assertNotIn('Winner:', r3)                                 # nothing after the round shown
        self.assertIn('Watch from round 1', r3)
        again = self.page(restart.replace('&amp;', '&'))                # after round 3, restart opens round one
        self.assertIn('<strong>after round 1</strong>', again)
        self.assertEqual(self.page(f'/event/{eid}'), final)             # nothing remembered, nothing changed
        n = e['rounds']
        last = self.page(f'/event/{eid}?view=rounds&round={n}')
        self.assertIn(f'<strong>after round {n}</strong>', last)

    def test_old_settings_file_is_left_alone_and_never_written(self):
        p = self.path / 'observer_spoilers.json'
        before = p.read_bytes(), p.stat().st_mtime_ns
        for path in ('/', f'/event/{quote(next(iter(self.w.live.editions)))}?view=rounds&round=2', '/my-world'):
            self.page(path)
        self.assertEqual((p.read_bytes(), p.stat().st_mtime_ns), before)

    def test_the_old_route_is_gone(self):
        lib = self.tmp / 'lib'
        app = OA.App(lib, workers=1)
        httpd = OA.start_server(app, 0)
        self.addCleanup(app.shutdown)
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        base = f'http://127.0.0.1:{httpd.server_address[1]}'
        urlopen(Request(base + '/worlds/browse', data=urlencode({'name': 'w'}).encode()), timeout=120).read()
        with self.assertRaises(HTTPError) as cm:
            urlopen(Request(base + '/spoilers', data=urlencode({'hide': '1', 'from': 'all'}).encode()), timeout=60)
        self.assertEqual(cm.exception.code, 404)
        self.assertNotIn('Hide results', urlopen(base + '/', timeout=120).read().decode())


if __name__ == '__main__':
    unittest.main()
