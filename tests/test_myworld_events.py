"""My World injury, return and team items: a followed golfer's injuries and returns (the first appearance once they
could enter again, and the first main event back when that was a qualifying stage, as the profile works them out),
and partnerships with coaches and caddies begun, resumed and ended. Each recorded fact is one item: whoever of the
pair is followed, across overlapping windows, and across the boundary where the current season is archived; an
archived item matches the season file and the relations table, a current one the running world; and drawing them
changes nothing the simulation keeps.

Run from the project folder:  python -m unittest tests.test_myworld_events -v
"""
from __future__ import annotations

import hashlib
import re
import shutil
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.archive import _read, read_manifest                      # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import equivalence_check as EQ                                        # noqa: E402
import observer as O                                                  # noqa: E402
import observer_data as OD                                            # noqa: E402
import observer_myworld as MW                                         # noqa: E402

NEW = ('injury', 'return', 'partnership', 'reunion', 'departure')


def text(h):
    return re.sub(r'<[^>]+>', '', h)


def kept(root, p):
    """Whether a file in the world folder belongs to the simulation: not the observer's own (its shortlist, views
    and caches), nor an index reader's SQLite shared memory or empty write-ahead log (SQLite's bookkeeping, not
    writes: a log with anything in it is compared)."""
    return (p.is_file() and not p.relative_to(root).parts[0].startswith('observer') and not p.name.endswith('-shm')
            and not (p.name.endswith('-wal') and not p.stat().st_size))


def world_state(w):
    """Everything the simulation keeps: the running world's parts (tools/equivalence_check) and every file of it."""
    files = {p.relative_to(w.path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(w.path.rglob('*')) if kept(w.path, p)}
    return EQ.parts(w.session, w.path), files


def followed(w, n=30):
    """Golfers with recorded injuries and both sides of coaching and caddying stints (as shortlist items)."""
    hurt = set()
    for y in w.a.years:
        hurt |= {int(g) for g, r in w.a.year(y)['careers'].items() if r.get('injuries')}
    hurt |= set(w.live.injuries)
    stints = [s for s in w.a.rel.stints if s.kind != 'school' and s.staff and s.end is not None]
    stints += [s for s in w.session.season.staff.rel.stints if s.kind != 'school' and s.staff
               and s.start[0] == w.live.cursor['year']]
    people = sorted(hurt)[:n] + [x for s in stints[:n] for x in (s.golfer, s.staff)]
    return [('person', p, '', None) for p in dict.fromkeys(people)]


def new_items(got):
    return [x for x in got if x[2] in NEW]


class MyWorldEvents(unittest.TestCase):
    """One world, seen in the last weeks of its second season and again a few weeks into its third (the second
    season archived in between)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.path = cls.tmp / 'w'
        s = Session.create(cls.path, seed=41, workers=1, world=generate_world(seed=41, scale=0.03))
        s.advance(52 + 47)                                              # one season archived, 47 weeks of the next
        s.close()
        w = O.World(cls.path, workers=1)
        w.reload()
        cls.before_year = w.live.cursor['year']
        cls.before_now = MW.now(w)
        cls.items = followed(w)
        cls.before = MW.digest(w, cls.items, (cls.before_year - 1, 0))
        w.close()
        s = Session.open(cls.path, workers=1)
        s.advance(8)                                                   # through the season's end: now archived
        s.close()
        cls.w = O.World(cls.path, workers=1)
        cls.w.reload()

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        (self.path / O.SHORTLIST).unlink(missing_ok=True)

    def page(self, path):
        u = urlparse(path)
        return O.render(self.w, u.path, parse_qs(u.query))[1]

    def start(self):
        return (self.w.a.years[0], 0)

    def test_the_world_is_as_expected(self):
        self.assertEqual(self.w.a.years, [self.before_year - 1, self.before_year])
        self.assertEqual(self.w.live.cursor['year'], self.before_year + 1)
        got = Counter(k for _, _, k, _ in MW.digest(self.w, self.items, self.start()))
        for k in ('injury', 'return', 'partnership', 'departure'):
            self.assertTrue(got[k], (k, got))

    def test_each_recorded_fact_is_one_item(self):
        got = new_items(MW.digest(self.w, self.items, self.start()))
        self.assertEqual(len(got), len({h for *_, h in got}))          # nothing twice
        # every injury episode of the followed golfers, from the season files and the running world, once
        pids = {int(i) for _, i, *_ in self.items}
        want = []
        for y in self.w.a.years:
            for g, r in self.w.a.year(y)['careers'].items():
                if int(g) in pids:
                    want += [(int(g), y, e['week']) for e in r.get('injuries') or ()]
        season = self.w.session.season
        for g, es in season.injury_episodes(self.w.live.cursor['year']).items():
            if g in pids:
                want += [(g, self.w.live.cursor['year'], e['week']) for e in es]
        injuries = [x for x in got if x[2] == 'injury']
        self.assertEqual(len(injuries), len(want))
        self.assertEqual(Counter((y, wk) for y, wk, *_ in injuries), Counter((y, wk) for _, y, wk in want))
        # every stint begun or ended with a followed person on either side, from the relations table (as the
        # archive wrote it) and the running world, once each
        a = self.path / 'archive'
        rel = _read(a / read_manifest(a)['files']['relations'])['stints']
        live = {s.id: s for s in season.staff.rel.stints}
        ids = {d['id'] for d in rel} | set(live)
        starts = ends = 0
        for i in ids:
            s = live.get(i)
            kind, staff, golfer = (s.kind, s.staff, s.golfer) if s else next((d['kind'], d['staff'], d['golfer'])
                                                                              for d in rel if d['id'] == i)
            if kind == 'school' or not staff or not ({staff, golfer} & pids):
                continue
            starts += 1
            ends += bool(s.end if s else next(d['end'] for d in rel if d['id'] == i))
        self.assertEqual(sum(1 for x in got if x[2] in ('partnership', 'reunion')), starts)
        self.assertEqual(sum(1 for x in got if x[2] == 'departure'), ends)

    def test_following_both_sides_gives_one_item(self):
        s = next(s for s in self.w.a.rel.stints if s.kind == 'coach' and s.staff and s.end is not None)
        one_side = [x for x in MW.digest(self.w, [('person', s.golfer, '', None)], self.start())
                    if x[2] in ('partnership', 'reunion', 'departure') and f'/golfer/{s.staff}"' in x[3]]
        both = [x for x in MW.digest(self.w, [('person', s.golfer, '', None), ('person', s.staff, '', None)],
                                     self.start())
                if x[2] in ('partnership', 'reunion', 'departure') and f'/golfer/{s.golfer}"' in x[3]
                and f'/golfer/{s.staff}"' in x[3]]
        self.assertEqual(one_side, both)
        self.assertEqual(sum(1 for x in both if x[2] == 'departure' and O.when(s.end) in text(x[3])
                             and O.when(s.start) in text(x[3])), 1)

    def test_overlapping_windows(self):
        y = self.w.live.cursor['year'] - 1
        full = new_items(MW.digest(self.w, self.items, self.start()))
        a = new_items(MW.digest(self.w, self.items, self.start(), (y, 20)))
        b = new_items(MW.digest(self.w, self.items, (y, 20)))
        self.assertEqual(sorted(a + b), sorted(full))                  # adjoining windows: each item in one of them
        c = new_items(MW.digest(self.w, self.items, (y, 10)))          # overlapping: the shared weeks' items are the
        shared = [x for x in a if (x[0], x[1]) > (y, 10)]              # same items, never a second copy
        self.assertTrue(set(shared) <= set(c))
        merged = {x[3] for x in a} | {x[3] for x in c}
        self.assertEqual(len(merged), len(full))

    def test_the_archived_season_reads_as_it_did_live(self):
        until = self.before_now
        after = new_items(MW.digest(self.w, self.items, (self.before_year - 1, 0), until))
        self.assertEqual(sorted(after), sorted(new_items(self.before)))
        self.assertTrue(any(y == self.before_year for y, *_ in after))  # (items of the season now archived)

    def test_items_match_the_records(self):
        y0 = self.w.a.years[-1]
        careers = self.w.a.year(y0)['careers']
        g, r = next((int(g), r) for g, r in careers.items() if r.get('injuries'))
        e = r['injuries'][0]
        got = [x for x in MW.digest(self.w, [('person', g, '', None)], (y0, 0)) if x[2] == 'injury']
        mine = next(x for x in got if (x[0], x[1]) == (y0, e['week']))
        n = e['announced']
        self.assertIn(f'({e["kind"]}): announced as {n} week{"s" if n != 1 else ""}; can enter events again from '
                      f'{e["available"][0]} week {e["available"][1]}', text(mine[3]))
        if e.get('event'):
            self.assertIn(f'/event/{e["event"].replace(":", "%3A")}"', mine[3])
        # the current season: as the running world has it
        lv_year = self.w.live.cursor['year']
        cur = self.w.session.season.injury_episodes(lv_year)
        if cur:
            g, es = next(iter(cur.items()))
            got = [x for x in MW.digest(self.w, [('person', g, '', None)], (lv_year, 0)) if x[2] == 'injury']
            self.assertEqual(sorted((x[0], x[1]) for x in got), sorted((lv_year, e['week']) for e in es))
        # a stint from the relations table and one begun this season, as recorded
        s = next(s for s in self.w.a.rel.stints if s.kind != 'school' and s.staff and s.end is not None)
        got = [x for x in MW.digest(self.w, [('person', s.golfer, '', None)], self.start()) if x[2] == 'departure'
               and f'/golfer/{s.staff}"' in x[3]]
        self.assertTrue(any(text(O._ended(s)) in text(x[3]) and (x[0], x[1]) == MW._dated(s.end) for x in got))
        s = next(s for s in self.w.session.season.staff.rel.stints if s.kind != 'school' and s.staff
                 and s.start[0] == lv_year)
        got = [x for x in MW.digest(self.w, [('person', s.staff, '', None)], (lv_year, 0))
               if x[2] in ('partnership', 'reunion') and f'/golfer/{s.golfer}"' in x[3]]
        self.assertEqual(len(got), 1)
        self.assertEqual((got[0][0], got[0][1]), s.start)
        self.assertIn(text(O._began(s)), text(got[0][3]))

    def test_returns_are_the_profiles(self):
        """Each return item names the appearance the profile's Injuries section shows as the first one back (and
        the first main event back, when that differs)."""
        checked = 0
        for _, pid, *_ in self.items:
            eps, _ = O.injury_episodes(self.w, pid)
            if not eps:
                continue
            got = [x for x in MW.digest(self.w, [('person', pid, '', None)], self.start()) if x[2] == 'return']
            played = O.appearances(OD.results(self.w, pid))
            want = set()
            for y, e in eps:
                ret, main = O.injury_return(played, e)
                if ret:
                    want.add((ret[0], ret[2]))
                if main and main != ret:
                    want.add((main[0], main[2]))
            self.assertEqual(len(got), len(want), pid)
            for (yy, wk), eid in want:
                self.assertTrue(any((x[0], x[1]) == (yy, wk) and f'/event/{eid.replace(":", "%3A")}"' in x[3]
                                    for x in got), (pid, eid))
                self.assertIn(f'{yy} week {wk}: {O.event_link(self.w, eid)}', self.page(f'/golfer/{pid}'))
            checked += len(want)
        self.assertTrue(checked)

    def test_a_reunion_is_one_item(self):
        s = next(s for s in self.w.a.rel.stints if s.kind != 'school' and s.staff and s.end is not None)
        later = (s.end[0] + 2, 5)
        again = {'id': 10 ** 7, 'kind': s.kind, 'staff': s.staff, 'golfer': s.golfer, 'start': later, 'end': None,
                 'arrangement': 'share', 'started_by': 'coach', 'reason_start': 'saw their potential',
                 'reason_end': '', 'ended_by': '', 'terms': 0.0}
        with mock.patch.object(self.w.live, 'stints', list(self.w.live.stints) + [again]):
            for who in ([s.golfer], [s.staff], [s.golfer, s.staff]):
                got = [x for x in MW.digest(self.w, [('person', p, '', None) for p in who], self.start())
                       if (x[0], x[1]) == later]
                self.assertEqual([x[2] for x in got], ['reunion'], who)
                self.assertIn(f'after their earlier partnership from {O.when(s.start)} to {O.when(s.end)}',
                              text(got[0][3]))
        # the same stint in both places (the snapshot's later record of an archived stint): one start, one end
        open_ = next(x for x in self.w.a.rel.stints if x.kind != 'school' and x.staff and x.end is None
                     and x.start < (self.w.live.cursor['year'], 0))
        keep = ('id', 'kind', 'staff', 'golfer', 'start', 'arrangement', 'started_by', 'reason_start', 'terms')
        ended = {**{n: getattr(open_, n) for n in keep},
                 'end': (self.w.live.cursor['year'], 2), 'reason_end': 'moved on', 'ended_by': 'staff'}
        with mock.patch.object(self.w.live, 'stints', [d for d in self.w.live.stints if d['id'] != open_.id] + [ended]):
            got = [x for x in MW.digest(self.w, [('person', open_.golfer, '', None)], (open_.start[0] - 1, 0))
                   if f'/golfer/{open_.staff}"' in x[3]]
            self.assertEqual(sorted(x[2] for x in got), ['departure', 'partnership'])
            gone = next(x for x in got if x[2] == 'departure')
            self.assertIn('ended by the coach or caddie: moved on', text(gone[3]))

    def test_the_page_lists_them_and_changes_nothing(self):
        before = world_state(self.w)
        for _, p, *_ in self.items[:12]:
            self.assertTrue(O.set_shortlist(self.w, 'person', p, True))
        html = text(self.page('/my-world?since=52'))
        self.assertIn('injuries and returns', html)
        people = [p for _, p, *_ in self.items[:12]]
        for path in (['/my-world', '/my-world?since=season', f'/my-world?since={self.w.a.years[0]}.0']
                     + [f'/golfer/{p}' for p in people] + [f'/golfer/{p}?tab=coaching' for p in people]):
            self.page(path)
        MW.new_count(self.w)
        self.assertEqual(world_state(self.w), before)


if __name__ == '__main__':
    unittest.main()
