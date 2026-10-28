"""The weekly session (roadmap M1): cursor, rollover, idempotency, serialised advances, crash recovery,
and equality with an uninterrupted run.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import session as SES                                    # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.season import Season                                     # noqa: E402
from golfsim.session import Session, StaleCursor                      # noqa: E402

SCALE = 0.12                     # a small world: the mechanics, not the population, are under test


def small_world(seed=11):
    return generate_world(seed=seed, scale=SCALE)


def fingerprint(season):
    """Canonical outcome of a world: every result, every golfer's money, form and rankings."""
    parts = [sorted((k, r.finish) for k, r in season.results.items()),
             sorted((g.id, round(g.cash, 6), round(g.overall, 9), g.tour, g.status, g.lifestyle)
                    for g in season.world.golfers),
             sorted(season.wr_pos.items()), sorted(season.am_pos.items())]
    return hashlib.sha256(repr(parts).encode()).hexdigest()


def direct(weeks, seed=11):
    """The same world advanced without a session: start_year, then week by week."""
    s = Season(small_world(seed), seed=seed, development=True, workers=1)
    year = s.first_year
    for i in range(weeks):
        week = i % 52 + 1
        if week == 1:
            s.start_year(year)
        s.advance_week(year, week)
        if week == 52:
            s.finish_year(year)
            year += 1
    return s


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.dir = Path(self.tmp) / 'world'

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def new(self):
        return Session.create(self.dir, seed=11, workers=1, world=small_world())

    def test_weekly_advance_matches_an_uninterrupted_run_and_survives_reopening(self):
        s = self.new()
        self.assertEqual(s.cursor, {'year': 2027, 'week': 1, 'phase': 'start'})
        r = s.advance_one_week(expected=s.cursor)
        self.assertEqual(r['completed'], (2027, 1))
        self.assertEqual(r['cursor'], {'year': 2027, 'week': 2, 'phase': 'week'})
        s.advance_one_week()
        s.close()
        s = Session.open(self.dir, workers=1)                           # reload, then carry on
        self.assertEqual(s.cursor['week'], 3)
        s.advance_one_week()
        self.assertEqual(fingerprint(s.season), fingerprint(direct(3)))
        s.close()

    def test_repeated_operation_and_stale_requests_change_nothing(self):
        s = self.new()
        first = s.advance_one_week(op_key='click-1')
        gen = s.generation
        again = s.advance_one_week(op_key='click-1')                    # a double click or a retried request
        self.assertEqual(again, first)
        self.assertEqual(s.generation, gen)
        self.assertEqual(s.cursor['week'], 2)
        with self.assertRaises(StaleCursor):
            s.advance_one_week(expected={'year': 2027, 'week': 1, 'phase': 'start'})
        self.assertEqual((s.generation, s.cursor['week']), (gen, 2))
        s.close()

    def test_two_concurrent_advances_commit_exactly_one_week(self):
        s = self.new()
        cur = s.cursor
        out = []
        def go():
            try:
                out.append(s.advance_one_week(expected=cur)['completed'])
            except StaleCursor:
                out.append('stale')
        ts = [threading.Thread(target=go) for _ in range(2)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        self.assertEqual(sorted(map(str, out)), sorted(map(str, [(2027, 1), 'stale'])))
        self.assertEqual(s.cursor['week'], 2)
        s.close()

    def test_a_crash_before_the_commit_leaves_the_previous_world(self):
        s = self.new()
        s.advance_one_week()
        committed = s.cursor
        real_replace = os.replace
        def crash(src, dst):
            if str(dst).endswith('CURRENT'):
                raise OSError('power cut')                               # after writing, before the pointer moves
            return real_replace(src, dst)
        with mock.patch.object(SES.os, 'replace', crash):
            with self.assertRaises(OSError):
                s.advance_one_week()
        s.close()
        t = Session.open(self.dir, workers=1)
        self.assertEqual(t.cursor, committed)                           # the last committed world, intact
        self.assertFalse(list(self.dir.glob('*.tmp')))
        t.advance_one_week()                                            # and it carries on normally
        self.assertEqual(fingerprint(t.season), fingerprint(direct(2)))
        t.close()

    def test_a_crash_while_writing_leaves_no_trace(self):
        s = self.new()
        s.advance_one_week()
        with mock.patch.object(SES.pickle, 'dump', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                s.advance_one_week()
        self.assertTrue(list(self.dir.glob('gen_*.tmp')))               # an orphaned temporary generation
        s.close()
        t = Session.open(self.dir, workers=1)
        self.assertEqual(t.cursor['week'], 2)
        self.assertFalse(list(self.dir.glob('gen_*.tmp')))              # removed on opening
        t.close()

    def test_a_damaged_current_generation_falls_back_to_the_last_good_one(self):
        s = self.new()
        s.advance_one_week()
        s.advance_one_week()
        cur = json.loads((self.dir / 'CURRENT').read_text())
        with open(self.dir / cur['dir'] / 'state.pkl.gz', 'r+b') as f:
            f.seek(100)
            f.write(b'\x00' * 64)                                       # corrupted on disk
        s.close()
        t = Session.open(self.dir, workers=1)
        self.assertEqual(t.cursor['week'], 2)                           # the previous generation
        self.assertEqual(len([p for p in self.dir.glob('gen_[0-9]*') if p.is_dir()]), SES.KEEP_GENERATIONS)
        t.close()

    def test_a_long_advance_commits_once_and_can_be_cancelled_between_weeks(self):
        s = self.new()
        g0 = s.generation
        done = []
        s.advance(5, progress=done.append, cancel=lambda: len(done) >= 3)
        self.assertEqual(len(done), 3)
        self.assertEqual(s.generation, g0 + 1)                          # one commit for the whole advance
        self.assertEqual(s.cursor['week'], 4)
        s.close()
        t = Session.open(self.dir, workers=1)
        self.assertEqual(t.cursor['week'], 4)
        self.assertEqual(fingerprint(t.season), fingerprint(direct(3)))
        with mock.patch.object(t.season, 'advance_week', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):                    # interrupted mid-week: nothing commits
                t.advance(2)
        self.assertEqual(t.cursor['week'], 4)
        t.close()

    def test_season_rollover_runs_each_step_once(self):
        s = self.new()
        s.advance(52)
        self.assertEqual(s.cursor, {'year': 2028, 'week': 1, 'phase': 'start'})
        self.assertIn(2027, s.season.career_counts)
        self.assertEqual(s.state['archive_through'], 2027)
        world = json.loads((self.dir / 'archive' / 'world.json').read_text())
        self.assertEqual(world['years'], [2027])
        juniors = s.season.juniors_added[2028]
        population = len(s.season.world.golfers)
        r = s.advance_one_week()                                        # 1 January 2028 runs once, then week 1
        self.assertEqual(r['completed'], (2028, 1))
        self.assertEqual(s.season.juniors_added[2028], juniors)
        self.assertEqual(len(s.season.world.golfers), population)
        self.assertIn(2028, s.season.cash_start)
        self.assertEqual(fingerprint(s.season), fingerprint(direct(53)))
        # an archive season written by an advance that never committed is removed on opening
        (self.dir / 'archive' / 'years' / '2028.json.gz').write_bytes(b'x')
        world['years'].append(2028)
        (self.dir / 'archive' / 'world.json').write_text(json.dumps(world))
        s.close()
        t = Session.open(self.dir, workers=1)
        self.assertEqual(json.loads((self.dir / 'archive' / 'world.json').read_text())['years'], [2027])
        self.assertFalse((self.dir / 'archive' / 'years' / '2028.json.gz').exists())
        from golfsim.archive_index import ArchiveIndex
        self.assertEqual(ArchiveIndex(self.dir / 'archive' / 'index.sqlite').years(), [2027])
        t.close()


if __name__ == '__main__':
    unittest.main()
