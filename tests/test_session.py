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


def archive_view(d):
    """Everything the visible history holds: seasons listed and on disk, their contents, the index, and
    the people, relationships and records tables."""
    from golfsim.archive import _read
    from golfsim.archive_index import ArchiveIndex
    a = Path(d) / 'archive'
    view = {'years': json.loads((a / 'world.json').read_text())['years'],
            'seasons': {p.name: _read(p) for p in sorted((a / 'years').glob('*.json.gz'))}}
    for f in ('people.json.gz', 'relations.json.gz', 'records.json.gz'):
        view[f] = _read(a / f) if (a / f).exists() else None
    if (a / 'index.sqlite').exists():
        idx = ArchiveIndex(a / 'index.sqlite')
        view['index'] = (idx.years(), idx.db.execute('SELECT COUNT(*) FROM starts').fetchone()[0],
                         idx.db.execute('SELECT COUNT(*) FROM seasons').fetchone()[0])
        idx.close()
    return view


def fail_publication(path_end='CURRENT'):
    """os.replace that fails when the commit pointer would move (everything before it is written)."""
    real = os.replace
    def replace(src, dst):
        if str(dst).endswith(path_end):
            raise OSError('power cut')
        return real(src, dst)
    return mock.patch.object(SES.os, 'replace', replace)


class EngineIdTests(unittest.TestCase):
    def test_a_source_copy_without_git_has_the_same_engine_id(self):
        """An exported source tarball (no .git) fingerprints itself exactly as git would, so the worlds it
        made reopen without overriding the engine check."""
        from golfsim import savegame as SG
        gid = SG.engine_id()
        if gid in ('unknown',) or gid.endswith('+dirty'):
            self.skipTest('needs a clean git checkout to compare against')
        self.assertEqual(SG._files_engine_id(), gid)


class TransactionTests(unittest.TestCase):
    """The running world, the committed checkpoint and the visible history always agree."""

    @classmethod
    def setUpClass(cls):
        """One uninterrupted session, kept at the last week of each of its first two seasons (copied for
        each test), and the history and world it shows after each season end."""
        cls.base = Path(tempfile.mkdtemp())
        d = cls.base / 'reference'
        s = Session.create(d, seed=11, workers=1, world=small_world())
        cls.before_end, cls.after_end = {}, {}
        for year, weeks in ((2027, 51), (2028, 51)):
            s.advance(weeks)
            s.close()
            shutil.copytree(d, cls.base / f'at_week52_{year}')
            s = Session.open(d, workers=1)
            s.advance(1)
            cls.after_end[year] = (archive_view(d), fingerprint(s.season))
        s.close()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base, ignore_errors=True)

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.dir = Path(self.tmp) / 'world'

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def new(self, d=None):
        return Session.create(d or self.dir, seed=11, workers=1, world=small_world())

    def at_season_end(self, year):
        """A copy of the reference world about to play the last week of `year`."""
        shutil.copytree(self.base / f'at_week52_{year}', self.dir)
        return Session.open(self.dir, workers=1)

    def test_a_failed_final_commit_of_a_long_advance_rolls_back(self):
        s = self.new()
        s.advance(2)
        committed = s.cursor
        with fail_publication(), self.assertRaises(OSError):
            s.advance(3)
        self.assertEqual(s.cursor, committed)                           # memory is not ahead of disk
        self.assertEqual(fingerprint(s.season), fingerprint(direct(2)))
        s.advance(1)                                                    # and it carries on from there
        self.assertEqual(fingerprint(s.season), fingerprint(direct(3)))
        s.close()

    def test_a_failed_year_end_commit_leaves_the_history_as_committed(self):
        ref_view, ref_print = self.after_end[2028]
        s = self.at_season_end(2028)                                     # 2027 archived, 2028 about to end
        before = archive_view(self.dir)
        self.assertEqual(before['years'], [2027])
        with fail_publication(), self.assertRaises(OSError):
            s.advance_one_week()                                        # season 2028 ends, the commit fails
        self.assertEqual(archive_view(self.dir), before)                 # history as committed, in this process
        self.assertEqual(s.cursor, {'year': 2028, 'week': 52, 'phase': 'week'})
        t = Session.open(self.dir, workers=1)                            # and as another process sees it
        self.assertEqual(archive_view(self.dir), before)
        t.close()
        s.advance_one_week()                                            # continuing in the same process
        self.assertEqual(archive_view(self.dir), ref_view)
        self.assertEqual(fingerprint(s.season), ref_print)
        s.close()

    def test_a_crash_after_the_commit_but_before_the_history_is_published_is_repaired(self):
        for year in (2027, 2028):
            with self.subTest(year=year):
                self._crash_before_publication(year)
                shutil.rmtree(self.dir)

    def _crash_before_publication(self, year):
        ref_view, ref_print = self.after_end[year]
        s = self.at_season_end(year)
        with mock.patch.object(SES, '_publish_archive', side_effect=OSError('power cut')), \
                self.assertRaises(OSError):
            s.advance_one_week()                                        # committed; history not yet updated
        s.close()
        t = Session.open(self.dir, workers=1)                            # reopening publishes it
        self.assertEqual(t.cursor, {'year': year + 1, 'week': 1, 'phase': 'start'})
        self.assertEqual(archive_view(self.dir), ref_view)
        self.assertEqual(fingerprint(t.season), ref_print)
        t.close()

    def test_a_damaged_year_end_checkpoint_falls_back_to_its_own_history(self):
        """The season-end generation is damaged after its history was published: the generation before it
        becomes current, and the history goes back to exactly what that generation stands on -- the
        later season's file and index rows and its people, relationships and records tables."""
        s = self.at_season_end(2028)
        s.advance_one_week()                                            # 2028 ends and is published
        self.assertEqual(archive_view(self.dir), self.after_end[2028][0])
        gen = s.generation
        s.close()
        (self.dir / f'gen_{gen:06d}' / 'state.pkl.gz').write_bytes(b'damaged')
        t = Session.open(self.dir, workers=1)
        self.assertEqual((t.generation, t.cursor), (gen - 1, {'year': 2028, 'week': 52, 'phase': 'week'}))
        self.assertEqual(archive_view(self.dir), self.after_end[2027][0])   # nothing from the future
        t.advance_one_week()                                            # the season end again, identically
        self.assertEqual(archive_view(self.dir), self.after_end[2028][0])
        self.assertEqual(fingerprint(t.season), self.after_end[2028][1])
        t.close()

    def test_retrying_a_committed_operation_repairs_its_unpublished_history(self):
        s = self.at_season_end(2027)
        with mock.patch.object(SES, '_publish_archive', side_effect=OSError('power cut')), \
                self.assertRaises(OSError):
            s.advance_one_week(op_key='end-2027')                       # committed; history not published
        self.assertEqual(archive_view(self.dir)['years'], [])
        r = s.advance_one_week(op_key='end-2027')                       # the retry: not simulated again ...
        self.assertEqual(r['completed'], (2027, 52))
        self.assertEqual(s.cursor, {'year': 2028, 'week': 1, 'phase': 'start'})
        self.assertEqual(archive_view(self.dir), self.after_end[2027][0])   # ... but the history is repaired
        s.close()

    def test_the_observer_rebuilds_records_after_a_fallback_removes_a_season(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
        import observer
        from golfsim import archive as A
        from golfsim.history_stats import HistoryStats
        s = self.at_season_end(2028)
        s.close()
        w = observer.World(self.dir)
        w.session.advance_one_week()                                    # 2028 published ...
        w.reload()
        self.assertEqual(sorted(w.stats.seen), [2027, 2028])            # ... and read into the records
        gen = w.session.generation
        w.session.close()
        (self.dir / f'gen_{gen:06d}' / 'state.pkl.gz').write_bytes(b'damaged')
        w.session = Session.open(self.dir, workers=1)                   # falls back: 2028 is gone
        w.reload()
        a = A.Archive(self.dir / 'archive')
        self.assertEqual(sorted(w.stats.seen), [2027])
        for board in ('most_wins', 'most_starts'):
            self.assertEqual(getattr(w.stats, board)(), getattr(HistoryStats(a), board)())
        editions = {e['id'] for _, e in a.events()}
        for row in w.stats.most_wins(n=1000):                           # every piece of evidence exists
            self.assertTrue(set(row['evidence']) <= editions, row)
        w.session.advance_one_week()                                    # 2028 again
        w.reload()
        self.assertEqual(sorted(w.stats.seen), [2027, 2028])
        self.assertEqual(w.stats.most_wins(), HistoryStats(A.Archive(self.dir / 'archive')).most_wins())
        w.session.close()

    def test_a_retry_after_recovery_rolled_the_operation_back_applies_it_once(self):
        """The season-end advance commits, then its generation is damaged. Retried through the same live
        handle, the operation is not reported as done from memory: the committed world (the generation
        before) is loaded first, the operation is no longer in it, so it runs again -- once."""
        ref_view, ref_print = self.after_end[2028]
        s = self.at_season_end(2028)
        first = s.advance_one_week(op_key='end-2028')
        gen = s.generation
        (self.dir / f'gen_{gen:06d}' / 'state.pkl.gz').write_bytes(b'damaged')
        again = s.advance_one_week(op_key='end-2028')                   # the same handle, the same key
        self.assertEqual(again['completed'], first['completed'])
        self.assertEqual(s.cursor, {'year': 2029, 'week': 1, 'phase': 'start'})
        t = Session.open(self.dir, workers=1)                            # what is really committed
        self.assertEqual(t.cursor, {'year': 2029, 'week': 1, 'phase': 'start'})
        self.assertEqual(fingerprint(t.season), ref_print)              # applied exactly once
        self.assertEqual(archive_view(self.dir), ref_view)
        self.assertEqual(t.advance_one_week(op_key='end-2028')['completed'], (2028, 52))   # now recognised
        self.assertEqual(t.cursor, {'year': 2029, 'week': 1, 'phase': 'start'})
        t.close()
        s.close()

    def test_ordinary_advances_leave_published_history_untouched(self):
        """Weeks that add no season do not rewrite the published tables; a publication left unfinished
        is still repaired by the next advance."""
        s = self.at_season_end(2027)
        s.advance_one_week()                                            # 2027 published
        a = self.dir / 'archive'
        names = ('people.json.gz', 'relations.json.gz', 'records.json.gz', 'world.json', 'PUBLISHED')
        stamp = lambda: {f: ((a / f).stat().st_mtime_ns, (a / f).stat().st_ino) for f in names}
        before, view = stamp(), archive_view(self.dir)
        s.advance(3)                                                    # 1 January and two weeks
        self.assertEqual(stamp(), before)
        (a / 'people.json.gz').unlink()                                 # an interrupted publication
        (a / 'PUBLISHED').write_text('-1')
        s.advance_one_week()
        self.assertEqual(archive_view(self.dir), view)                  # repaired, exactly
        s.close()

    def test_moves_and_money_survive_an_interrupted_season_end(self):
        """The winter's moves (and their cost) are in the committed world and the published history
        exactly once after a crash before publication, a reopening and a replay."""
        ref_view, ref_print = self.after_end[2027]
        ref_moves = {pid: p['moves'] for pid, p in ref_view['people.json.gz'].items() if p['moves']}
        self.assertTrue(ref_moves)                                          # the reference winter had moves
        s = self.at_season_end(2027)
        with mock.patch.object(SES, '_publish_archive', side_effect=OSError('power cut')), \
                self.assertRaises(OSError):
            s.advance_one_week()
        s.close()
        t = Session.open(self.dir, workers=1)                            # recovery publishes it
        view = archive_view(self.dir)
        self.assertEqual({pid: p['moves'] for pid, p in view['people.json.gz'].items() if p['moves']}, ref_moves)
        P = t.season.places
        self.assertEqual({str(pid): len(m) for pid, m in P.moves.items()}, {pid: len(m) for pid, m in ref_moves.items()})
        for pid, ms in P.moves.items():
            self.assertEqual(len(ms), len(set(ms)))                     # none twice
        self.assertEqual(fingerprint(t.season), ref_print)               # cash (moving costs included)
        led = t.season.ledgers[2027]
        for g in t.season.world.golfers:                                 # and every golfer reconciles
            c0 = t.season.cash_start[2027].get(g.id)
            if c0 is not None:
                self.assertAlmostEqual(g.cash, c0 + (led[g.id].net if g.id in led else 0.0), delta=0.01)
        t.close()

    def test_archived_annual_money_is_settled_after_an_interrupted_season_end(self):
        """A move paid at the winter is in the archived year (net, moving cost) exactly once after a
        crash before publication, reopening and recovery -- and matches the committed ledger."""
        from golfsim import residence as RES
        from golfsim.archive import _read
        s = self.at_season_end(2027)
        g = next(g for g in s.season.active_golfers() if g.status == 'pro' and g.lifestyle == 'full_time'
                 and g.age(2027) < 30 and s.season.places.known(g.id) and g.tour.startswith(('MN_', 'RG_', 'CH_')))
        g.cash += 100000.0
        dest = 'England' if s.season.places.home[g.id][0] != 'England' else 'Japan'
        odds = lambda season, x, year, changed=False: (dest, 1.0) if x.id == g.id else (season.places.home[x.id][0], 0.0)
        with mock.patch.object(RES, 'move_odds', odds), \
                mock.patch.object(SES, '_publish_archive', side_effect=OSError('power cut')), self.assertRaises(OSError):
            s.advance_one_week()
        s.close()
        t = Session.open(self.dir, workers=1)
        led = t.season.ledgers[2027][g.id]
        row = _read(self.dir / 'archive' / 'years' / '2027.json.gz')['careers'][str(g.id)]
        self.assertEqual(t.season.places.home[g.id][0], dest)
        self.assertEqual((row['moving'], row['net']), (RES.MOVE_COST, round(led.net)))
        self.assertEqual(row['net_at_decision'] - row['net'], RES.MOVE_COST)
        self.assertEqual(len(t.season.places.moves[g.id]), 1)
        t.close()

    def test_a_retry_through_another_handle_is_recognised(self):
        a = self.new()
        b = Session.open(self.dir, workers=1)                            # a second, independently opened handle
        ra = a.advance_one_week(op_key='submit-1')
        rb = b.advance_one_week(op_key='submit-1')                       # the same request, retried elsewhere
        self.assertEqual(rb['completed'], ra['completed'])
        self.assertEqual(b.cursor['week'], 2)
        self.assertEqual(json.loads((self.dir / 'CURRENT').read_text())['generation'], a.generation)
        a.close()
        b.close()

    def test_repeated_submissions_are_recognised_after_later_operations(self):
        s = self.new()
        first = s.advance_one_week(op_key='k1')
        s.advance_one_week(op_key='k2')
        gen = s.generation
        self.assertEqual(s.advance_one_week(op_key='k1')['completed'], first['completed'])   # a late resubmission
        out = s.advance(2, op_key='skip-1')
        self.assertEqual(s.advance(2, op_key='skip-1'), out)            # a refreshed form: no second skip
        self.assertEqual((s.generation, s.cursor['week']), (gen + 1, 5))
        s.close()

    def test_opening_leaves_another_process_checkpoint_work_alone(self):
        s = self.new()
        s.advance_one_week()
        s.close()
        lock = self.dir / 'lock'
        lock.write_text(str(os.getpid()))                               # a live advance elsewhere holds the lock
        work = self.dir / 'gen_000099.tmp'
        work.mkdir()
        (self.dir / 'CURRENT.tmp').write_text('{}')
        t = Session.open(self.dir, workers=1)
        self.assertTrue(work.exists() and (self.dir / 'CURRENT.tmp').exists())
        self.assertEqual(t.cursor['week'], 2)                           # it still reads the committed world
        t.close()
        lock.unlink()                                                   # the other advance finished (or died)
        Session.open(self.dir, workers=1).close()
        self.assertFalse(work.exists() or (self.dir / 'CURRENT.tmp').exists())

    def test_observer_resubmissions_and_stale_forms_advance_nothing(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
        import observer
        s = self.new()
        s.close()
        w = observer.World(self.dir)
        form = lambda c, op, weeks='1': {'weeks': [weeks], 'year': [str(c['year'])], 'week': [str(c['week'])],
                                         'phase': [c['phase']], 'op': [op]}
        c0 = w.session.cursor
        w.submit(form(c0, 'a'))
        gen = w.session.generation
        w.submit(form(c0, 'a'))                                         # the same form posted twice
        w.submit(form(c0, 'b'))                                         # an old page's form, new key
        self.assertEqual((w.session.generation, w.session.cursor['week']), (gen, 2))
        w.submit(form(w.session.cursor, 'c', '4'))
        self.assertEqual(w.session.cursor['week'], 6)
        w.session.close()

    def test_observer_reads_only_new_history_after_an_advance(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
        import observer
        from golfsim import archive as A
        from golfsim.history_stats import HistoryStats
        s = self.at_season_end(2028)                                     # 2027 archived, 2028 about to end
        s.close()
        w = observer.World(self.dir)
        before = w.stats.most_wins()
        reads = []
        real = A._read
        def counting(path):
            reads.append(Path(path).name)
            return real(path)
        with mock.patch.object(A, '_read', counting):
            w.session.advance_one_week()                                 # season end: 2028 published
            w.reload()
            stats = w.stats
            self.assertNotIn('2027.json.gz', reads)                       # unchanged history is not reread
            self.assertNotIn('2028.json.gz', reads)                       # the new season comes from the index
            self.assertEqual(sorted(stats.seen), [2027, 2028])
            fresh = HistoryStats(A.Archive(self.dir / 'archive'))
            self.assertEqual(stats.most_wins(), fresh.most_wins())       # the same answers as a full rebuild
            self.assertNotEqual(stats.most_wins(), before)
            reads.clear()
            a = w.a
            w.session.advance_one_week()                                 # 1 January 2029 and week 1: nothing new
            w.reload()
            self.assertIs(w.a, a)
            self.assertEqual(reads, [])
        w.session.close()

    @unittest.skipUnless(os.name == 'posix', 'detecting a dead process needs POSIX')
    def test_a_lock_left_by_a_dead_process_is_released(self):
        import subprocess
        s = self.new()
        p = subprocess.Popen([sys.executable, '-c', 'pass'])
        p.wait()                                                        # a process id that no longer runs
        (self.dir / 'lock').write_text(f'{p.pid} {SES._lock_owner().split(" ", 1)[1]}')
        s.advance_one_week()
        self.assertEqual(s.cursor['week'], 2)
        s.close()


if __name__ == '__main__':
    unittest.main()
