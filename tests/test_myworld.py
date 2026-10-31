"""My World: the shortlist in groups and a digest of recorded facts for what is followed -- complete and only what
the history recorded, a quiet count in the menu, "mark as read", older shortlist files still read, no simulation
state, ranking bands read from the ranking recorded for each week (never today's ranking in an earlier week's
place), and for a world that used the removed Hide results setting: nothing held back, and the period that may
have been marked read unseen offered for review (the read marker untouched, nothing counted twice).

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
from unittest import mock
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer as O                                                  # noqa: E402
import observer_myworld as MW                                         # noqa: E402


def plant_old_hiding(world_dir, since=(0, 0)):
    """The removed Hide results setting as an earlier build wrote it (everything hidden, nothing revealed)."""
    (Path(world_dir) / 'observer_spoilers.json').write_text(json.dumps(
        {'format': 'golf-legacy-spoilers/1', 'hide': True, 'from': list(since), 'revealed': {}}))


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
        inside = {r[0] for rows in lv.rank_top.values() for r in rows}  # a professional outside every recorded top
        cls.mover = min(g for g, p in lv.people.items() if g not in inside and p.get('status') == 'pro'   # 200
                        and p.get('lifestyle') != 'retired')

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        (self.path / O.SHORTLIST).unlink(missing_ok=True)
        (self.path / MW.OLD_SPOILERS).unlink(missing_ok=True)

    def page(self, path):
        u = urlparse(path)
        return O.render(self.w, u.path, parse_qs(u.query))[1]

    def follow(self, *items):
        for kind, ident, *g in items:
            self.assertTrue(O.set_shortlist(self.w, kind, ident, True, g[0] if g else None))

    def test_digest_is_complete_and_only_recorded_facts(self):
        self.follow(('person', self.winner))
        start = (self.w.live.cursor['year'], 0)
        got = MW.digest(self.w, O.shortlist(self.w), start)
        wins = [x for x in got if x[2] == 'win']
        want = [r for r in self.w.results(self.winner) if r['pos'] == 1 and (r['year'], r['week']) > start
                and (self.w.edition(r['event']) or {}).get('category') not in ('qualifier', 'q_school')]
        self.assertTrue(want)
        self.assertEqual(len(wins), len(want))                         # every win, nothing invented
        for r in want:
            self.assertTrue(any(f'/event/{r["event"].replace(":", "%3A")}"' in h for _, _, _, h in wins), r)
        html = self.page('/my-world?since=season')
        self.assertIn(f'{len(got):,} recorded item', html)

    def test_followed_tour_series_nation_course_and_edition(self):
        lv = self.w.live
        course = lv.editions[self.eid]['sites'][0][0]
        self.follow(('tour', 'PT_AMERICAS'), ('series', self.eid.split(':', 1)[1]), ('edition', self.eid),
                    ('course', course), ('nation', (self.w.person(self.winner) or {}).get('country')))
        got = MW.digest(self.w, O.shortlist(self.w), (lv.cursor['year'], 0))
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

    def test_old_hiding_settings_hold_nothing_back(self):
        self.follow(('person', self.winner), ('tour', 'PT_AMERICAS'))
        start = (self.w.live.cursor['year'], 0)
        before = MW.digest(self.w, O.shortlist(self.w), start)
        plant_old_hiding(self.path)
        self.assertEqual(MW.digest(self.w, O.shortlist(self.w), start), before)
        wins = [r for r in self.w.results(self.winner) if r['pos'] == 1 and (r['year'], r['week']) > start]
        for r in wins:                                                  # every win named, none held back
            self.assertTrue(any(f'/event/{r["event"].replace(":", "%3A")}"' in h for _, _, _, h in before))
        self.assertNotIn('held back', self.page('/my-world?since=season'))

    def test_a_period_marked_read_while_hidden_is_offered_for_review(self):
        self.follow(('tour', 'PT_AMERICAS'))
        y = self.w.live.cursor['year']
        plant_old_hiding(self.path, since=(y, 1))                       # hiding began in week 1 of this season
        O.mark_read(self.w)                                             # ... and the digest was marked read since
        seen = tuple(O.shortlist_seen(self.w))
        self.assertEqual(MW.hidden_period(self.w, seen), ((y, 1), seen))
        html = self.page('/my-world')
        self.assertIn('may not have been shown', html)
        link = f'/my-world?since={y}.1&amp;until={seen[0]}.{seen[1]}'
        self.assertIn(link, html)
        review = self.page(link.replace('&amp;', '&'))
        got = MW.digest(self.w, O.shortlist(self.w), (y, 1), seen)
        self.assertTrue(got)
        self.assertIn(f'{len(got):,} recorded item', review)            # the period, everything in it
        self.assertTrue(all((a, b) > (y, 1) and (a, b) <= seen for a, b, _, _ in got))
        self.assertEqual(MW.new_count(self.w), 0)                       # not counted again as new
        self.assertEqual(tuple(O.shortlist_seen(self.w)), seen)         # the read marker untouched
        O.dismiss_hidden_period(self.w)
        self.assertNotIn('may not have been shown', self.page('/my-world'))
        self.assertEqual(tuple(O.shortlist_seen(self.w)), seen)
        self.assertEqual(O.shortlist(self.w)[0][:2], ('tour', 'PT_AMERICAS'))   # (the shortlist kept)

    def test_an_unreadable_old_settings_file_is_ignored(self):
        self.follow(('tour', 'PT_AMERICAS'))
        O.mark_read(self.w)
        seen = O.shortlist_seen(self.w)
        for text in ('{not json', '[]', '{"hide": true}', '{"from": "all"}', '{"from": [2030]}', '{"from": null}',
                     '{"from": ["a", 1]}'):
            (self.path / MW.OLD_SPOILERS).write_text(text)
            self.assertIsNone(MW.hidden_period(self.w, seen), text)
            html = self.page('/my-world')                               # the page opens, nothing held back
            self.assertNotIn('may not have been shown', html)
            self.assertIn('recorded items since last read', html)

    def test_no_notice_without_old_hiding_or_before_it(self):
        self.follow(('tour', 'PT_AMERICAS'))
        O.mark_read(self.w)
        self.assertNotIn('may not have been shown', self.page('/my-world'))
        y, wk = self.w.live.cursor['year'], self.w.live.cursor['week']
        plant_old_hiding(self.path, since=(y, wk + 5))                  # hiding began after the last read
        self.assertIsNone(MW.hidden_period(self.w, O.shortlist_seen(self.w)))

    # ---- ranking bands: each end of the window from that week's own ranking ----------------------------------------
    def ranked(self, places, pid=None):
        """The current season's weekly rankings as recorded, with one golfer moved to the place given for each week
        (None: that week's ranking left out, as if it had not been recorded)."""
        lv = self.w.live
        pid = pid or self.mover
        top = {wk: [list(r) for r in rows if r[0] != pid] for wk, rows in lv.rank_top.items()}
        for wk, at in places.items():
            if at is None:
                top.pop(wk, None)
            else:
                top.setdefault(wk, [list(r) for r in lv.rank_top[max(lv.rank_top)] if r[0] != pid])
                top[wk].insert(at - 1, [pid, 0.0, 0])
        return mock.patch.object(lv, 'rank_top', top)

    def bands(self, start, until=None, pid=None):
        """The digest's ranking items for a followed golfer: [(year, week, text)]."""
        pid = pid or self.mover
        got = MW.digest(self.w, [('person', pid, '', '')], start, until)
        return [(y, wk, re.sub(r'<[^>]+>', '', h)) for y, wk, k, h in got if k == 'ranking']

    def test_entering_and_leaving_the_top_10_and_reaching_no_1_within_a_season(self):
        y = self.w.live.cursor['year']
        self.assertEqual(MW.now(self.w), (y, 8))
        name = self.w.name(self.mover)
        with self.ranked({2: 12, 4: 8, 6: 1, 8: 15}):
            self.assertEqual(self.bands((y, 2), (y, 4)),                # No. 12 -> No. 8
                             [(y, 4, f'{name} is now in the top 10 of the world ranking (No. 8)')])
            self.assertEqual(self.bands((y, 4), (y, 6)), [(y, 6, f'{name} is now world No. 1')])
            self.assertEqual(self.bands((y, 6)), [(y, 8, f'{name} is no longer world No. 1 (now No. 15)')])
            self.assertEqual(self.bands((y, 4)),
                             [(y, 8, f'{name} dropped out of the top 10 of the world ranking (now No. 15)')])
            self.assertEqual(self.bands((y, 2)), [])                    # in and out again: no change over the window
            self.assertEqual(self.bands((y, 4), (y, 4)), [])

    def test_a_missing_ranking_is_not_replaced_by_another_weeks(self):
        y = self.w.live.cursor['year']
        with self.ranked({2: None, 4: 8, 8: 60}):
            self.assertEqual(self.bands((y, 2), (y, 4)), [])            # week 2 not recorded: nothing claimed
            self.assertEqual(self.bands((y, 2)), [])
            self.assertEqual(len(self.bands((y, 4))), 1)                # both weeks recorded: the change
        with self.ranked({8: None, 4: 8}):                              # the latest week: the live table itself
            now = self.w.live.wr.get(self.mover)
            got = self.bands((y, 4))
            self.assertEqual(len(got), 1)
            self.assertIn('dropped out of the top 10', got[0][2])
            self.assertIn(f'(now No. {now})' if now else '(now outside the top 100)', got[0][2])

    def test_a_season_boundary_reads_the_archived_ranking(self):
        import observer_golf as OG
        y = self.w.live.cursor['year']
        last = OG._rankings(self.w, y - 1)['ranking_points']['52']
        champ = last[0][0]                                              # No. 1 when last season ended
        name = self.w.name(champ)
        self.assertEqual(MW._rank_at(self.w, y, 0, champ), (True, 1))   # week 0: last season's final ranking
        self.assertEqual(MW._rank_at(self.w, y - 1, 52, champ), (True, 1))
        with self.ranked({8: 30}, pid=champ):
            self.assertEqual(self.bands((y, 0), pid=champ), [(y, 8, f'{name} is no longer world No. 1 (now No. 30)')])
        with self.ranked({8: 1}, pid=champ):
            self.assertEqual(self.bands((y, 0), pid=champ), [])         # No. 1 then and now: nothing

    def test_marking_the_digest_read_then_a_later_week(self):
        y = self.w.live.cursor['year']
        lv = self.w.live
        self.follow(('person', self.mover))
        with self.ranked({8: 12}):
            O.mark_read(self.w)
            self.assertEqual(tuple(O.shortlist_seen(self.w)), (y, 8))
            self.assertEqual(MW.new_count(self.w), 0)
        with self.ranked({8: 12, 9: 8}), mock.patch.object(lv, 'cursor', {**lv.cursor, 'year': y, 'week': 10}):
            self.assertEqual(MW.now(self.w), (y, 9))                    # a week later: No. 12 -> No. 8
            self.assertEqual(MW.new_count(self.w), 1)
            name = self.w.name(self.mover)
            self.assertIn(f'{name} is now in the top 10 of the world ranking (No. 8)',
                          re.sub(r'<[^>]+>', '', self.page('/my-world')))
            O.mark_read(self.w)
            self.assertEqual(MW.new_count(self.w), 0)                   # read: not offered again
        with self.ranked({8: 12, 9: 8}):
            self.assertEqual(MW.new_count(self.w), 0)

    def test_a_retirement_is_one_dated_event(self):
        lv = self.w.live
        y = lv.cursor['year']                                           # retired in the winter after last season
        gone = sorted(g for g, p in lv.people.items() if p.get('lifestyle') == 'retired'
                      and any(r['year'] == y - 1 and r.get('lifestyle') != 'retired' for r in self.w.a.index.seasons(g)))
        self.assertTrue(gone)
        pid = gone[0]
        items = lambda start: [(a, b, re.sub(r'<[^>]+>', '', h)) for a, b, k, h in
                               MW.digest(self.w, [('person', pid, '', '')], start) if k == 'status']
        once = [(y, 1, f'{self.w.name(pid)}: retired after the {y - 1} season')]
        self.assertEqual(items((y, 0)), once)
        self.assertEqual(items((y, 1)), [])                             # read since: not announced again
        with mock.patch.object(lv, 'cursor', {**lv.cursor, 'year': y + 1, 'week': 5}):
            self.assertEqual(items((y, 30)), [])                        # a season later: still not again
            self.assertEqual(items((y, 0)), once)                       # the same event, the same date
        with mock.patch.object(self.w, 'live', None):                   # the history alone shows it too
            self.assertEqual(items((y, 0)), once)

    def test_retired_status_is_shown_one_way(self):
        import observer_data as OD
        self.assertEqual(OD.playing_status({'status': 'pro', 'lifestyle': 'retired'}),
                         ('retired', 'retired, last a professional'))
        self.assertEqual(OD.playing_status({'status': 'amateur', 'lifestyle': 'retired'}),
                         ('retired', 'retired, last an amateur'))
        self.assertEqual(OD.playing_status({'status': 'pro', 'lifestyle': 'full_time'}), ('active', 'professional'))
        lv = self.w.live
        pid = min(g for g, p in lv.people.items() if p.get('lifestyle') == 'retired')   # (whatever status they held)
        html = self.page(f'/golfer/{pid}')
        self.assertIn('<span class="tag">retired</span>', html)
        self.assertIn(f'<dt>Status</dt><dd>{OD.playing_status(lv.people[pid])[1]}</dd>', html)
        self.assertTrue(OD.playing_status(lv.people[pid])[1].startswith('retired, last a'))
        import observer_history as OH
        eid = next(iter(lv.editions))                                   # a completed slam and one major short
        active = min(g for g, p in lv.people.items() if p.get('lifestyle') == 'full_time' and p.get('status') == 'pro')
        firsts = {sid: (lv.cursor['year'], eid) for sid in OH.MAJOR_SERIES}
        fake = {pid: {'complete': (lv.cursor['year'], eid), 'firsts': firsts},
                active: {'complete': None, 'firsts': dict(list(firsts.items())[:3])}}
        with mock.patch.object(OH, 'grand_slams', lambda w: fake):
            slam = self.page('/grand-slam')
        done, short = slam.split('<h2>One major short</h2>')
        self.assertIn('<th title="Sort by this column">Now</th>', done)
        self.assertRegex(done, rf'href="/golfer/{pid}">[^<]*</a></td><td>retired</td>')
        self.assertIn('<th title="Sort by this column">Now</th>', short)
        self.assertRegex(short, rf'href="/golfer/{active}">[^<]*</a></td><td>active</td>')

    def test_desktop_menu_and_record_book(self):
        html = O.page(self.w, 'Overview', '')                          # the page shell, with its menu
        nav = html.split('<nav')[1].split('</nav>')[0]
        for href, label in (('/goat', 'GOAT Lab'), ('/compare', 'Compare careers'), ('/my-world', 'My World'),
                            ('/records', 'Record Book')):
            self.assertIn(f'href="{href}"', nav)
            self.assertIn(label, nav)
        self.assertNotIn('frivolities', nav)
        self.assertEqual(O.render(self.w, '/records', {})[0], 'Record Book')   # the page's title
        import observer_views as V
        self.assertEqual(V.page_name('/records'), 'Record Book')
        self.assertIn('main { padding:16px 32px; flex:1; min-width:0; }', html)   # no content-width cap

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
        got = MW.digest(w, O.shortlist(w), seen)
        self.assertTrue(got)
        self.assertTrue(all((y, wk) > seen for y, wk, _, _ in got))
        self.assertEqual(MW.new_count(w), len(got))


if __name__ == '__main__':
    unittest.main()
