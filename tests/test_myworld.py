"""My World: the shortlist in groups and a digest of recorded facts for what is followed -- complete and only what
the history recorded, held back where Hide results says so, a quiet count in the menu, "mark as read", older
shortlist files still read, and no simulation state.

Run from the project folder:  python -m unittest tests.test_myworld -v
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer as O                                                  # noqa: E402
import observer_myworld as MW                                         # noqa: E402
import observer_spoilers as SP                                        # noqa: E402


class MyWorld(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.path = cls.tmp / 'w'
        s = Session.create(cls.path, seed=41, workers=1, world=generate_world(seed=41, scale=0.03))
        s.advance(52 + 8)                                               # one archived season, eight weeks played
        s.close()
        cls.w = O.World(cls.path, workers=1)
        cls.w.reload()
        lv = cls.w.live
        cls.no1 = min(lv.wr, key=lv.wr.get)
        winners = [g for e in lv.editions.values() for g, p, _ in (e['finish'][0] if e['finish'] else []) if p == 1]
        cls.winner = max(set(winners), key=winners.count)              # someone with wins this season
        cls.eid = next(e['id'] for e in lv.editions.values() if e.get('tour') == 'PT_AMERICAS')

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        (self.path / O.SHORTLIST).unlink(missing_ok=True)
        SP.set_hide(self.w, False)

    def page(self, path):
        u = urlparse(path)
        return O.render(self.w, u.path, parse_qs(u.query))[1]

    def follow(self, *items):
        for kind, ident, *g in items:
            self.assertTrue(O.set_shortlist(self.w, kind, ident, True, g[0] if g else None))

    def test_digest_is_complete_and_only_recorded_facts(self):
        self.follow(('person', self.winner))
        start = (self.w.live.cursor['year'], 0)
        got, held = MW.digest(self.w, O.shortlist(self.w), start)
        wins = [x for x in got if x[2] == 'win']
        want = [r for r in self.w.results(self.winner) if r['pos'] == 1 and (r['year'], r['week']) > start
                and (self.w.edition(r['event']) or {}).get('category') not in ('qualifier', 'q_school')]
        self.assertTrue(want)
        self.assertEqual(len(wins), len(want))                         # every win, nothing invented
        for r in want:
            self.assertTrue(any(f'/event/{r["event"].replace(":", "%3A")}"' in h for _, _, _, h in wins), r)
        self.assertEqual(held, 0)
        html = self.page('/my-world?since=season')
        self.assertIn(f'{len(got):,} recorded item', html)

    def test_followed_tour_series_nation_course_and_edition(self):
        lv = self.w.live
        course = lv.editions[self.eid]['sites'][0][0]
        self.follow(('tour', 'PT_AMERICAS'), ('series', self.eid.split(':', 1)[1]), ('edition', self.eid),
                    ('course', course), ('nation', (self.w.person(self.winner) or {}).get('country')))
        got, _ = MW.digest(self.w, O.shortlist(self.w), (lv.cursor['year'], 0))
        played = [e for e in lv.editions.values() if e.get('tour') == 'PT_AMERICAS']
        for e in played:                                               # every edition of the followed tour
            self.assertTrue(any(f'/event/{e["id"].replace(":", "%3A")}"' in h for _, _, _, h in got), e['id'])
        self.assertTrue(any('was played: won by' in h for _, _, _, h in got))

    def test_groups_and_older_files(self):
        (self.path / O.SHORTLIST).write_text(json.dumps({'format': 'golf-legacy-shortlist/1', 'items': [
            ['person', str(self.no1), '2026-10-01 10:00']]}))          # a file from before groups
        self.assertEqual(O.shortlist(self.w), [('person', str(self.no1), '2026-10-01 10:00', '')])
        self.follow(('person', self.no1, 'Rivals'), ('tour', 'PT_EUROPE', 'Tours I watch'))
        items = {(k, i): g for k, i, _, g in O.shortlist(self.w)}
        self.assertEqual(items[('person', str(self.no1))], 'Rivals')
        self.assertEqual(O.shortlist(self.w)[0][2], '2026-10-01 10:00')   # moving keeps when it was added
        html = self.page('/my-world')
        self.assertIn('<h3>Rivals (1)</h3>', html)
        self.assertIn('<h3>Tours I watch (1)</h3>', html)
        self.assertIn('<h4>People</h4>', html)

    def test_mark_read_and_the_quiet_count(self):
        self.follow(('tour', 'PT_AMERICAS'))
        self.assertTrue(MW.new_count(self.w) > 0)                      # nothing read yet: this season's items
        self.assertRegex(O.my_world_link(self.w), r'My World <span class="muted">\(\d+ new\)</span>')
        O.mark_read(self.w)
        self.assertEqual(MW.new_count(self.w), 0)
        self.assertEqual(O.my_world_link(self.w), '<a href="/my-world">My World</a>')
        self.assertIn('0 recorded items since last read', self.page('/my-world'))
        self.assertNotIn('banner', self.page('/my-world'))             # no pop-ups or banners

    def test_hide_results_holds_items_back(self):
        self.follow(('person', self.winner), ('tour', 'PT_AMERICAS'))
        start = (self.w.live.cursor['year'], 0)
        shown, _ = MW.digest(self.w, O.shortlist(self.w), start)
        SP.set_hide(self.w, True, 'season')
        got, held = MW.digest(self.w, O.shortlist(self.w), start)
        self.assertGreater(held, 0)
        self.assertEqual(len(got) + held, len(shown))                  # held back, not dropped
        for _, _, kind, h in got:                                      # nothing naming a hidden result
            for e in self.w.live.editions.values():
                if SP.hidden(self.w, e['id'], e['week']):
                    self.assertNotIn(f'/event/{e["id"].replace(":", "%3A")}"', h)
        html = self.page('/my-world?since=season')
        self.assertIn('naming a hidden result held back', html)

    def test_not_simulation_state(self):
        before = {p.relative_to(self.path).as_posix(): p.stat().st_mtime_ns for p in self.path.rglob('*') if p.is_file()}
        self.follow(('person', self.no1, 'Rivals'))
        O.mark_read(self.w)
        self.page('/my-world')
        after = {p.relative_to(self.path).as_posix(): p.stat().st_mtime_ns for p in self.path.rglob('*') if p.is_file()}
        changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
        self.assertTrue(changed)
        self.assertTrue(all(k.startswith('observer') for k in changed), changed)


class MyWorldNewWeeks(unittest.TestCase):
    """After "mark as read", weeks played later bring new items (and only those)."""

    def test_new_weeks_bring_new_items(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        s = Session.create(tmp / 'w', seed=43, workers=1, world=generate_world(seed=43, scale=0.02))
        s.advance(6)
        s.close()
        w = O.World(tmp / 'w', workers=1)
        w.reload()
        O.set_shortlist(w, 'tour', 'PT_AMERICAS', True)
        O.mark_read(w)
        seen = tuple(O.shortlist_seen(w))
        self.assertEqual(MW.new_count(w), 0)
        w.close()
        s = Session.open(tmp / 'w', workers=1)
        s.advance(4)
        s.close()
        w = O.World(tmp / 'w', workers=1)
        self.addCleanup(w.close)
        w.reload()
        got, _ = MW.digest(w, O.shortlist(w), seen)
        self.assertTrue(got)
        self.assertTrue(all((y, wk) > seen for y, wk, _, _ in got))
        self.assertEqual(MW.new_count(w), len(got))


if __name__ == '__main__':
    unittest.main()
