"""The observer's compact prestige store (tools/observer_prestige_store.py): prestige histories of tournaments, courses
and nations without decoding whole seasons on a page.

A synthetic archive of real gzip season files (a dozen seasons, each with a bulky `events` list standing in for the rest
of a season file) and a minimal world; no season is played. Covered: cold (the newest season inline, the rest in the
background, shown as being read), warm (no season file opened), across pages, reopening (a new process), advancing (only
the new season read), a roll-back (seasons published again read again), a source changed at the same path with the same
size and modification time, another world at the same path, a missing or corrupt store, an interrupted background
reader, the bounded memory, and no store at all. Every chart value equals the archived record.

Run from the project folder:  python -m unittest tests.test_prestige_store -v
"""
from __future__ import annotations

import gzip
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
import zlib
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import observer_prestige as OP                                            # noqa: E402
import observer_prestige_store as PS                                      # noqa: E402

FIRST, LAST = 2040, 2051
NATIONS = ('Argentina', 'Fiji', 'USA')


def record(y, bump=0.0):
    return {'format': 'golf-legacy-prestige/1',
            'events': {'TOUR_MASTERS': round(80 + (y - FIRST) * 0.5 + bump, 2), 'SMALL_OPEN': 40.0},
            'courses': {'augusta-like': round(70 + (y - FIRST) * 0.25 + bump, 2)},
            'venue_moves': [],
            'nations': {'prestige': {c: 50.0 + i + (y - FIRST) * 0.1 for i, c in enumerate(NATIONS)},
                        'multiplier': {c: 1.0 for c in NATIONS},
                        'shares': {'juniors': {c: 1 / 3 for c in NATIONS}, 'new_pros': {c: 1 / 3 for c in NATIONS}},
                        'allocated': {'juniors': {c: 2 for c in NATIONS}, 'new_pros': {c: 1 for c in NATIONS}},
                        'baseline_shares': {'juniors': {c: 1 / 3 for c in NATIONS}, 'new_pros': {c: 1 / 3 for c in NATIONS}}}}


class FakeArchive:
    """What the store reads of an archive: years, the manifest's file names, the files, the world."""

    def __init__(self, d, seed=7):
        self.dir = Path(d)
        self.years = []
        self.files = {'years': {}}
        self.world = {'seed': seed, 'first_year': FIRST, 'calendar': {'version': 2}}
        self.decoded = 0

    def publish(self, y, gen, rec, pad=0, body=None, members=1):
        name = f'years/{y}.g{gen:06d}.json.gz'
        p = self.dir / name
        p.parent.mkdir(parents=True, exist_ok=True)
        if body is None:
            body = {'year': y, 'prestige': rec, 'events': [{'id': f'{y}:E{i}', 'filler': 'x' * 200} for i in range(400)],
                    'pad': 'p' * pad}
        raw = json.dumps(body).encode()
        k = -(-len(raw) // members)                     # (several gzip members, as the archive writes them)
        p.write_bytes(b''.join(gzip.compress(raw[i:i + k], mtime=0) for i in range(0, len(raw), k)))
        self.files['years'][y] = name
        if y not in self.years:
            self.years.append(y)
            self.years.sort()
        return p

    def year_path(self, y):
        return self.dir / self.files['years'][y]

    def year(self, y):                    # a whole-season decode: the store must never need it
        self.decoded += 1
        raise AssertionError('a whole season was decoded through the archive')


class StoreCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.a = FakeArchive(self.tmp / 'archive')
        for y in range(FIRST, LAST + 1):
            self.a.publish(y, y - FIRST + 1, record(y))
        self.store_path = self.tmp / 'cache' / 'prestige.sqlite'
        self.w = self.world()
        self.reads = []
        real = PS.read_season

        def counted(p):
            self.reads.append(Path(p).name)
            return real(p)
        patch = mock.patch.object(PS, 'read_season', counted)
        patch.start()
        self.addCleanup(patch.stop)

    def world(self, a=None):
        w = NS(a=a or self.a, live=None, session=None, archive_dir=str(self.tmp / 'archive'))
        w._prestige_store = PS.PrestigeStore(self.store_path, PS.world_identity(w))
        self.addCleanup(w._prestige_store.stop_indexer)
        return w

    def wait(self, w):
        st = w._prestige_store
        t = time.time()
        while st.indexing() and time.time() - t < 60:
            time.sleep(0.05)
        self.assertFalse(st.indexing())

    def stored_sources(self):
        """{year: source identity} as kept in the store file (written by the background process)."""
        import sqlite3
        db = sqlite3.connect(self.store_path)
        try:
            return dict(db.execute('SELECT year, source FROM seasons').fetchall())
        finally:
            db.close()

    def warm_partial(self, w=None):
        """Every season read or settled (some may be unreadable: None)."""
        w = w or self.w
        PS.records(w, list(self.a.years))
        self.wait(w)
        return PS.records(w, list(self.a.years))

    def warm(self, w=None):
        w = w or self.w
        PS.records(w, list(self.a.years))
        self.wait(w)
        got = PS.records(w, list(self.a.years))
        self.assertTrue(all(v is not PS.PENDING for v in got.values()))
        return got


class Cold(StoreCase):
    def test_newest_inline_rest_in_the_background_then_every_value_exact(self):
        got = PS.records(self.w, list(self.a.years))
        self.assertEqual(got[LAST], record(LAST))                            # the newest: read now
        self.assertEqual(self.w._prestige_store.reads_inline, 1)
        self.assertTrue(all(got[y] is PS.PENDING for y in range(FIRST, LAST)))   # the rest: being read
        self.wait(self.w)
        got = PS.records(self.w, list(self.a.years))
        self.assertEqual(got, {y: record(y) for y in self.a.years})          # every value as archived
        self.assertEqual(self.a.decoded, 0)

    def test_the_page_says_being_read_never_missing(self):
        html = OP.event_section(self.w, 'TOUR_MASTERS')
        self.assertIn('being read from the history in the background', html)
        self.assertIn('<span class="rv">…</span>', html)
        self.assertNotIn('<span class="rv">—</span>', html)                  # never shown as not recorded
        self.assertIn('<span class="rv">85.5</span>', html)                  # the newest season, shown at once

    def test_latest_reads_one_season_only(self):
        self.assertEqual(OP.latest(self.w)['events']['TOUR_MASTERS'], record(LAST)['events']['TOUR_MASTERS'])
        self.assertEqual(len(self.reads), 1)


class Warm(StoreCase):
    def test_no_season_file_opened_and_every_page_complete(self):
        self.warm()
        self.reads.clear()
        idx = self.w._prestige_store.indexer
        ev = OP.event_section(self.w, 'TOUR_MASTERS')
        co = OP.course_section(self.w, 'augusta-like')
        na = OP.nation_section(self.w, 'Fiji')
        self.assertEqual(self.reads, [])                                     # across pages: nothing read
        self.assertIs(self.w._prestige_store.indexer, idx)                   # and no background reader started
        self.assertEqual(self.a.decoded, 0)
        for html in (ev, co, na):
            self.assertNotIn('being read', html)
            self.assertNotIn('…', html)
        for y in self.a.years:
            self.assertIn(f'<span class="rv">{record(y)["events"]["TOUR_MASTERS"]:.1f}</span>', ev)

    def test_reopen_in_a_new_process_reads_nothing(self):
        self.warm()
        self.reads.clear()
        w2 = self.world()                                                    # a new store object on the same file
        self.assertEqual(PS.records(w2, list(self.a.years)), {y: record(y) for y in self.a.years})
        self.assertEqual(self.reads, [])

    def test_memory_is_bounded(self):
        self.warm()
        with mock.patch.object(PS, 'MEMORY', 4):
            st = PS.PrestigeStore(self.store_path, PS.world_identity(self.w))
            st.stored({y: (PS.source_identity(self.a, y), str(self.a.year_path(y))) for y in self.a.years})
            self.assertEqual(len(st.mem), 4)


class Changes(StoreCase):
    def test_advance_reads_only_the_new_season(self):
        self.warm()
        self.reads.clear()
        self.a.publish(LAST + 1, 99, record(LAST + 1))
        got = PS.records(self.w, list(self.a.years))
        self.assertEqual(self.reads, [f'{LAST + 1}.g000099.json.gz'])
        self.assertEqual(got, {y: record(y) for y in self.a.years})

    def test_roll_back_republished_seasons_are_read_again(self):
        self.warm()
        self.reads.clear()
        for y in (LAST - 1, LAST):                                           # published again: new files
            self.a.publish(y, 500 + y - FIRST, record(y, bump=3.0))
        got = self.warm()
        self.assertEqual(self.reads, [f'{LAST}.g{500 + LAST - FIRST:06d}.json.gz'])   # the newest, inline
        src = self.stored_sources()
        self.assertEqual(src[LAST - 1], PS.source_identity(self.a, LAST - 1))   # the other: re-read in the background
        self.assertIn(f'{LAST - 1}.g{500 + LAST - 1 - FIRST:06d}', src[LAST - 1])
        self.assertEqual(got[LAST - 1], record(LAST - 1, bump=3.0))
        self.assertEqual(got[LAST], record(LAST, bump=3.0))
        self.assertEqual(got[FIRST], record(FIRST))

    def replace_same_size_and_mtime(self, y, rewrite):
        """Season y's file given other content at the same path, with the same size and modification time;
        rewrite=True writes the file's own bytes in place (same inode), else a new file is renamed over it."""
        p = self.a.year_path(y)
        st = os.stat(p)
        raw = gzip.decompress(p.read_bytes())
        changed = raw.replace(b'"SMALL_OPEN": 40.0', b'"SMALL_OPEN": 41.0')
        self.assertEqual(len(changed), len(raw))
        blob = gzip.compress(changed, mtime=0)
        if len(blob) < st.st_size:                       # the same size: pad the gzip member's name field
            pad = st.st_size - len(blob)
            blob = gzip.compress(changed, mtime=0)       # (rebuild with an FNAME of the right length)
            hdr, body = blob[:10], blob[10:]
            name = b'x' * (pad - 1) + b'\0'
            blob = hdr[:3] + bytes([hdr[3] | 0x08]) + hdr[4:] + name + body
        self.assertEqual(len(blob), st.st_size, 'could not keep the size (test setup)')
        time.sleep(0.02)
        if rewrite:
            with open(p, 'r+b') as f:
                f.seek(0)
                f.write(blob)
        else:
            tmp = p.with_suffix('.tmp')
            tmp.write_bytes(blob)
            os.replace(tmp, p)
        os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns))
        st2 = os.stat(p)
        self.assertEqual((st2.st_size, st2.st_mtime_ns), (st.st_size, st.st_mtime_ns))
        self.assertEqual(gzip.decompress(p.read_bytes()), changed)
        return p, st, st2

    def test_same_path_same_size_and_mtime_new_file(self):
        self.warm()
        y = FIRST + 3
        p, st, st2 = self.replace_same_size_and_mtime(y, rewrite=False)
        before = self.stored_sources()[y]
        self.assertNotEqual(PS.source_identity(self.a, y), before)          # not trusted: read again
        got = self.warm()
        self.assertEqual(self.stored_sources()[y], PS.source_identity(self.a, y))
        self.assertEqual(got[y]['events']['SMALL_OPEN'], 41.0)
        self.assertEqual({k: v for k, v in got.items() if k != y}, {k: record(k) for k in self.a.years if k != y})

    def test_same_path_same_size_and_mtime_rewritten_in_place(self):
        """The file's own bytes rewritten (the inode kept), size and modification time restored: the status-change
        time moves, so the season is read again."""
        self.warm()
        y = FIRST + 5
        p, st, st2 = self.replace_same_size_and_mtime(y, rewrite=True)
        self.assertEqual(st2.st_ino, st.st_ino)
        self.assertNotEqual(st2.st_ctime_ns, st.st_ctime_ns)
        self.assertNotEqual(PS.source_identity(self.a, y), self.stored_sources()[y])
        got = self.warm()
        self.assertEqual(self.stored_sources()[y], PS.source_identity(self.a, y))
        self.assertEqual(got[y]['events']['SMALL_OPEN'], 41.0)

    def test_another_world_at_the_same_path_starts_again(self):
        self.warm()
        b = FakeArchive(self.tmp / 'archive', seed=8)                        # same folder, another world's identity
        b.years, b.files = list(self.a.years), {'years': dict(self.a.files['years'])}
        w2 = self.world(b)
        self.reads.clear()
        got = PS.records(w2, list(b.years))
        self.assertEqual(self.reads, [b.files['years'][LAST].split('/')[-1]])   # only the newest, inline
        self.assertTrue(all(got[y] is PS.PENDING for y in range(FIRST, LAST)))


class Damage(StoreCase):
    def test_deleted_store_is_rebuilt(self):
        self.warm()
        for s in ('', '-wal', '-shm'):
            Path(str(self.store_path) + s).unlink(missing_ok=True)
        w2 = self.world()
        got = self.warm(w2)
        self.assertEqual(got, {y: record(y) for y in self.a.years})
        self.assertEqual(self.stored_sources(), {y: PS.source_identity(self.a, y) for y in self.a.years})

    def test_corrupt_store_is_set_aside_and_rebuilt(self):
        self.warm()
        self.w._prestige_store.stop_indexer()
        for s in ('-wal', '-shm'):
            Path(str(self.store_path) + s).unlink(missing_ok=True)
        self.store_path.write_bytes(b'not a database' * 100)
        w2 = self.world()
        got = self.warm(w2)
        self.assertEqual(got, {y: record(y) for y in self.a.years})
        self.assertTrue(Path(str(self.store_path) + '.corrupt').exists())

    def test_an_interrupted_reader_resumes(self):
        PS.records(self.w, list(self.a.years))
        self.w._prestige_store.stop_indexer()                                # stopped part-way (or at once)
        got = PS.records(self.w, list(self.a.years))
        self.assertTrue(any(v is PS.PENDING for v in got.values()) or not self.w._prestige_store.indexing())
        got = self.warm()
        self.assertEqual(got, {y: record(y) for y in self.a.years})

    def test_an_unreadable_season_is_not_recorded_and_not_retried_in_a_loop(self):
        y = FIRST + 2
        self.a.year_path(y).write_bytes(b'\x1f\x8b broken')                  # a damaged season file
        got = self.warm_partial()
        self.assertIsNone(got[y])                                            # shown as not recorded
        self.assertEqual({k: v for k, v in got.items() if k != y}, {k: record(k) for k in self.a.years if k != y})
        idx = self.w._prestige_store.indexer
        PS.records(self.w, list(self.a.years))
        self.assertIs(self.w._prestige_store.indexer, idx)                   # no new reader for it
        self.a.publish(y, 700, record(y))                                    # published again: read again
        got = self.warm()
        self.assertEqual(got[y], record(y))

    def test_one_reader_at_a_time(self):
        import threading
        PS.records(self.w, list(self.a.years))
        first = self.w._prestige_store.indexer
        ts = [threading.Thread(target=PS.records, args=(self.w, list(self.a.years))) for _ in range(8)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        if self.w._prestige_store.indexing():
            self.assertIs(self.w._prestige_store.indexer, first)
        self.assertEqual(self.warm(), {y: record(y) for y in self.a.years})

    def test_a_reader_that_keeps_crashing_is_given_up_on(self):
        with mock.patch.object(PS.sys, 'executable', '/bin/false'):          # a reader that dies at once
            for _ in range(PS.PrestigeStore.CRASHES + 1):
                got = PS.records(self.w, list(self.a.years))
                self.wait(self.w)
            got = PS.records(self.w, list(self.a.years))
        self.assertEqual(got[LAST], record(LAST))
        self.assertTrue(all(got[y] is None for y in range(FIRST, LAST)))    # not recorded, no endless restarts
        self.assertEqual(self.w._prestige_store.crashes, PS.PrestigeStore.CRASHES)

    def test_no_store_at_all_still_works_in_memory(self):
        w = NS(a=self.a, live=None, session=None, archive_dir='x')
        w._prestige_store = PS.PrestigeStore(None, PS.world_identity(w))
        got = PS.records(w, list(self.a.years))
        self.assertEqual(got[LAST], record(LAST))
        t = time.time()
        while w._prestige_store.indexing() and time.time() - t < 30:
            time.sleep(0.05)
        self.assertEqual(PS.records(w, list(self.a.years)), {y: record(y) for y in self.a.years})


class ReviewFindings(StoreCase):
    """Review of b777fdf: Windows file semantics, an unwritable job file, stopping the memory-only reader, eviction,
    records of the wrong shape, latest()'s fallback."""

    def windows_stat(self, frozen):
        """os.stat as Windows reports it after a rewrite in place: creation time (where POSIX has the status-change
        time) and file index unchanged."""
        real = os.stat

        def stat(p, *a, **k):
            st = real(p, *a, **k)
            f = frozen.get(str(p))
            if f is None:
                return st
            return NS(st_size=st.st_size, st_mtime_ns=st.st_mtime_ns, st_ctime_ns=f.st_ctime_ns, st_ino=f.st_ino,
                      st_dev=f.st_dev)
        return stat

    def test_windows_rewrite_in_place_same_size_and_mtime_is_read_again(self):
        self.warm()
        y = FIRST + 5
        p = self.a.year_path(y)
        frozen = {str(p): os.stat(p)}
        with mock.patch.object(PS, '_stat', self.windows_stat(frozen)):
            before = PS.source_identity(self.a, y)
            Changes.replace_same_size_and_mtime(self, y, rewrite=True)
            self.assertEqual(PS.source_identity(self.a, y), before)        # the stat identity cannot tell
            got = PS.records(self.w, list(self.a.years))                     # warm, in memory: still caught
            self.assertIs(got[y], PS.PENDING)
            got = self.warm()
            self.assertEqual(got[y]['events']['SMALL_OPEN'], 41.0)
            w2 = self.world()                                                # and from the store file, next session
            self.assertEqual(PS.records(w2, [y])[y]['events']['SMALL_OPEN'], 41.0)

    def test_windows_rewrite_of_one_member_of_several(self):
        y = FIRST + 2
        self.a.publish(y, y - FIRST + 1, record(y), members=7)
        self.warm()
        p = self.a.year_path(y)
        frozen = {str(p): os.stat(p)}
        data = bytearray(p.read_bytes())
        raw = gzip.decompress(bytes(data))
        changed = raw.replace(b'"SMALL_OPEN": 40.0', b'"SMALL_OPEN": 49.0')
        k = -(-len(raw) // 7)
        blob = b''.join(gzip.compress(changed[i:i + k], mtime=0) for i in range(0, len(changed), k))
        self.assertEqual(len(blob), len(data))                              # (same size: one digit changed)
        st = os.stat(p)
        with open(p, 'r+b') as f:
            f.write(blob)
        os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns))
        with mock.patch.object(PS, '_stat', self.windows_stat(frozen)):
            self.assertEqual(self.warm()[y]['events']['SMALL_OPEN'], 49.0)

    def test_an_unwritable_job_file_falls_back_to_a_thread(self):
        jobs = self.store_path.with_suffix('.jobs.json')
        jobs.parent.mkdir(parents=True, exist_ok=True)
        jobs.mkdir()                                                         # (cannot be written as a file)
        got = PS.records(self.w, list(self.a.years))                          # no exception through the page
        self.assertIsInstance(self.w._prestige_store.indexer, __import__('threading').Thread)
        self.assertEqual(got[LAST], record(LAST))
        self.assertEqual(self.warm(), {y: record(y) for y in self.a.years})
        self.assertEqual(self.stored_sources(), {y: PS.source_identity(self.a, y) for y in self.a.years})

    def test_the_memory_only_reader_stops_when_asked(self):
        w = NS(a=self.a, live=None, session=None, archive_dir='x')
        w._prestige_store = PS.PrestigeStore(None, PS.world_identity(w))
        real = PS.read_season

        def slow(p):
            time.sleep(0.1)
            return real(p)
        with mock.patch.object(PS, 'read_season', slow):
            PS.records(w, list(self.a.years))
            time.sleep(0.15)
            w._prestige_store.stop_indexer()
            self.assertFalse(w._prestige_store.indexing())
            n = len(w._prestige_store.mem)
            time.sleep(0.3)
            self.assertEqual(len(w._prestige_store.mem), n)                  # nothing read after the stop
            self.assertLess(n, len(self.a.years))

    def test_eviction_is_not_missing_history(self):
        with mock.patch.object(PS, 'MEMORY', 2):
            self.assertEqual(self.warm(), {y: record(y) for y in self.a.years})   # with a store: read back from it
            self.assertLessEqual(len(self.w._prestige_store.mem), 2)
            w = NS(a=self.a, live=None, session=None, archive_dir='x')
            w._prestige_store = PS.PrestigeStore(None, PS.world_identity(w))  # memory only: the whole history kept
            PS.records(w, list(self.a.years))
            t = time.time()
            while w._prestige_store.indexing() and time.time() - t < 30:
                time.sleep(0.05)
            got = PS.records(w, list(self.a.years))
            self.assertEqual(got, {y: record(y) for y in self.a.years})
            self.assertFalse(w._prestige_store.failed)

    def test_records_of_the_wrong_shape_are_not_recorded(self):
        bad = {FIRST + 1: {'prestige': ['not', 'a', 'record']},
               FIRST + 2: {'prestige': {'events': {'TOUR_MASTERS': 'high'}}},
               FIRST + 3: {'prestige': {'nations': {'prestige': [1, 2]}}},
               FIRST + 4: ['a', 'list'],
               LAST: {'prestige': {'courses': None}}}
        for y, body in bad.items():
            self.a.publish(y, 300 + y - FIRST, None, body=body)
        got = PS.records(self.w, list(self.a.years))                          # the newest (inline): no exception
        self.assertIsNone(got[LAST])
        got = self.warm_partial()
        for y in bad:
            self.assertIsNone(got[y], y)
        for y in set(self.a.years) - set(bad):
            self.assertEqual(got[y], record(y))
        html = OP.event_section(self.w, 'TOUR_MASTERS') + OP.nation_section(self.w, 'Fiji')
        self.assertIn('not recorded', html)

    def test_latest_falls_back_to_the_most_recent_recorded_season(self):
        self.a.publish(LAST, 900, None)                                      # the newest season: no prestige record
        first = OP.latest(self.w)
        self.assertTrue(first['pending'])                                    # older seasons still being read
        self.assertEqual(first['events'], {})
        self.wait(self.w)
        got = OP.latest(self.w)
        self.assertFalse(got['pending'])
        self.assertEqual(got['year'], LAST - 1)
        self.assertEqual(got['events'], record(LAST - 1)['events'])
        self.assertEqual(got['nations']['prestige'], record(LAST - 1)['nations']['prestige'])

    def test_latest_with_a_recorded_newest_season_reads_only_it(self):
        got = OP.latest(self.w)
        self.assertEqual((got['year'], got['pending']), (LAST, False))
        self.assertEqual(self.reads, [f'{LAST}.g{LAST - FIRST + 1:06d}.json.gz'])
        self.assertIsNone(self.w._prestige_store.indexer)                    # nothing else started


class LocksAndBytes(StoreCase):
    """Review of the follow-up: a store file locked by another connection, malformed compression, and the background
    check of every stored season's bytes; the lists' pending note."""

    def test_a_locked_store_is_busy_not_corrupt(self):
        import sqlite3
        self.warm()
        self.w._prestige_store.stop_indexer()
        before = self.store_path.read_bytes()
        hold = sqlite3.connect(self.store_path, timeout=1)
        hold.execute('PRAGMA locking_mode=EXCLUSIVE')                        # another connection holds it
        hold.execute('BEGIN EXCLUSIVE')
        hold.execute('INSERT OR REPLACE INTO meta VALUES (?, ?)', ('held', '1'))
        try:
            w2 = self.world()                                                # a new session: nothing in memory
            t = time.perf_counter()
            got = PS.records(w2, list(self.a.years))
            took = time.perf_counter() - t
            self.assertLess(took, 3.0)                                       # waited a moment, not 5 s a connection
            self.assertEqual(got[LAST], record(LAST))                        # the newest: read now
            self.assertTrue(all(got[y] is PS.PENDING for y in range(FIRST, LAST)))   # the rest: being read
            self.assertFalse(Path(str(self.store_path) + '.corrupt').exists())
            self.assertFalse(w2._prestige_store._broken)
            html = OP.event_section(w2, 'TOUR_MASTERS')                      # the page renders, pending
            self.assertIn('being read', html)
        finally:
            hold.rollback()
            hold.close()
        self.assertEqual(self.store_path.read_bytes()[:100], before[:100])  # the same file, kept
        w2._prestige_store.skip_until = 0.0
        w2._prestige_store.retry_after = 0.0
        self.assertEqual(self.warm(w2), {y: record(y) for y in self.a.years})
        self.assertFalse(Path(str(self.store_path) + '.corrupt').exists())

    def test_the_reader_waits_out_a_lock_and_is_retried_later(self):
        import sqlite3
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        hold = sqlite3.connect(self.store_path, timeout=1)
        hold.execute('PRAGMA locking_mode=EXCLUSIVE')
        hold.execute('BEGIN EXCLUSIVE')
        hold.execute('CREATE TABLE IF NOT EXISTS x(a)')
        try:
            with mock.patch.object(PS, 'READER_TIMEOUT', 0.3), mock.patch.object(PS, 'BUSY_RETRY', 0.5):
                st = PS.PrestigeStore(self.store_path, PS.world_identity(self.w))
                self.w._prestige_store = st
                PS.records(self.w, list(self.a.years))
                self.wait(self.w)
                PS.records(self.w, list(self.a.years))
                self.assertFalse(st.failed)                                  # a lock is no failure
                self.assertGreater(st.retry_after, 0)
        finally:
            hold.rollback()
            hold.close()
        self.assertFalse(Path(str(self.store_path) + '.corrupt').exists())
        st.retry_after = 0.0
        st.skip_until = 0.0
        self.assertEqual(self.warm(), {y: record(y) for y in self.a.years})

    def test_malformed_compression_of_the_newest_season(self):
        p = self.a.publish(LAST, 950, record(LAST))
        data = bytearray(p.read_bytes())
        data[20:60] = b'\xff' * 40                                          # the deflate stream damaged
        p.write_bytes(bytes(data))
        got = PS.records(self.w, list(self.a.years))                          # no zlib.error through the request
        self.assertIsNone(got[LAST])
        html = OP.event_section(self.w, 'TOUR_MASTERS')                      # renders: the rest being read
        self.assertIn('being read', html)
        self.assertIsNotNone(OP.latest(self.w))                              # the lists fall back (pending first)
        got = self.warm_partial()
        self.assertIsNone(got[LAST])
        self.assertIn('<span class="rv">—</span><span class="rb"></span><span class="ry">2051</span>',
                      OP.event_section(self.w, 'TOUR_MASTERS'))              # the newest: not recorded
        self.assertEqual(got[LAST - 1], record(LAST - 1))
        self.assertEqual(OP.latest(self.w)['year'], LAST - 1)

    def test_damage_that_keeps_the_trailers_is_found_by_the_sessions_bytes_check(self):
        """Not seen on a request (trailers as they were): the next session's background check finds it."""
        self.warm()
        y = FIRST + 4
        p = self.a.year_path(y)
        st = os.stat(p)
        data = bytearray(p.read_bytes())
        data[40:48] = bytes(b ^ 0x5a for b in data[40:48])                   # inside the deflate data
        p.write_bytes(bytes(data))
        os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns))
        frozen = {str(p): st}
        with mock.patch.object(PS, '_stat', ReviewFindings.windows_stat(self, frozen)):
            self.assertEqual(PS.records(self.w, [y])[y], record(y))          # this session: as stored (documented)
            w2 = self.world()                                                # the next session
            PS.records(w2, list(self.a.years))
            self.wait(w2)
            got = PS.records(w2, list(self.a.years))
        self.assertIsNone(got[y])                                            # found, read again: not readable now
        self.assertEqual({k: v for k, v in got.items() if k != y}, {k: record(k) for k in self.a.years if k != y})

    def test_the_lists_say_when_prestige_is_being_read(self):
        lt = {'events': {}, 'courses': {}, 'venue_moves': [], 'nations': {}, 'pending': True, 'year': None}
        self.assertIn('being read', OP.latest_note(lt))
        self.assertEqual(OP.latest_note({'pending': False, 'year': LAST}), '')
        self.assertEqual(OP.latest_note(None), '')
        import observer as O
        w = NS(live=None, a=None)
        with mock.patch.object(O.OP, 'latest', lambda w: lt), \
                mock.patch.object(O, 'nation_counts', lambda w: {'Fiji': [1, 1, 0, 0]}):
            self.assertIn('being read', O.nations(w, {})[1])


class NestedAndRepaired(StoreCase):
    """Review of 1c1ab53: nested values the pages cannot show, a failed season repaired in place, and the lists'
    note when the values are an older season's."""

    def bad(self, y, mutate):
        rec = record(y)
        mutate(rec)
        self.a.publish(y, 400 + y - FIRST, rec)

    def test_nested_values_the_pages_cannot_show_are_not_recorded(self):
        cases = {
            FIRST + 1: lambda r: r['nations']['shares']['juniors'].__setitem__('Fiji', 'high'),
            FIRST + 2: lambda r: r.__setitem__('venue_moves', [{'series': 'TOUR_MASTERS'}]),
            FIRST + 3: lambda r: r['events'].__setitem__('TOUR_MASTERS', float('nan')),
            FIRST + 4: lambda r: r['nations']['prestige'].__setitem__('Fiji', float('inf')),
            FIRST + 5: lambda r: r['nations']['allocated']['juniors'].__setitem__('USA', 'two'),
            FIRST + 6: lambda r: r['courses'].__setitem__('augusta-like', True),
            LAST: lambda r: r['nations']['baseline_shares']['new_pros'].__setitem__('USA', None) or
            r['nations']['multiplier'].__setitem__('USA', float('-inf')),
        }
        for y, f in cases.items():
            self.bad(y, f)
        got = PS.records(self.w, list(self.a.years))                          # the newest (inline): no exception
        self.assertIsNone(got[LAST])
        got = self.warm_partial()
        for y in cases:
            self.assertIsNone(got[y], y)
        for y in set(self.a.years) - set(cases):
            self.assertEqual(got[y], record(y))
        for html in (OP.event_section(self.w, 'TOUR_MASTERS'), OP.course_section(self.w, 'augusta-like'),
                     OP.nation_section(self.w, 'Fiji'), OP.nation_section(self.w, 'USA')):
            self.assertIn('not recorded', html)
        self.assertEqual(OP.latest(self.w)['year'], LAST - 1)

    def test_a_valid_venue_move_is_kept(self):
        move = {'series': 'TOUR_MASTERS', 'from': 2045, 'course': 'augusta-like', 'layout': 'main', 'replaces': 'old-club',
                'city': 'Augusta', 'decided': 2044, 'event_prestige': 81.0, 'course_prestige_before': 60.5}
        self.bad(LAST, lambda r: r.__setitem__('venue_moves', [move]))
        self.assertEqual(PS.records(self.w, [LAST])[LAST]['venue_moves'], [move])
        self.assertIn('Venue moves: from 2045', OP.event_section(self.w, 'TOUR_MASTERS'))

    def write_same_size(self, p, raw, size):
        blob = gzip.compress(raw, mtime=0)
        if len(blob) < size:
            hdr, body = blob[:10], blob[10:]
            blob = hdr[:3] + bytes([hdr[3] | 0x08]) + hdr[4:] + b'x' * (size - len(blob) - 1) + b'\0' + body
        self.assertEqual(len(blob), size, 'test setup: sizes')
        with open(p, 'r+b') as f:                                            # in place: the same file
            f.seek(0)
            f.write(blob)
            f.truncate(size)

    def test_a_failed_season_repaired_in_place_is_read_again(self):
        y = FIRST + 7
        p = self.a.year_path(y)
        good = gzip.decompress(p.read_bytes())
        broken = good.replace(b'"SMALL_OPEN": 40.0', b'"SMALL_OPEN": "40"')   # same length, not a number
        self.assertEqual(len(broken), len(good))
        size = max(len(gzip.compress(good, mtime=0)), len(gzip.compress(broken, mtime=0))) + 40
        self.write_same_size(p, broken, size)
        got = self.warm_partial()
        self.assertIsNone(got[y])                                            # unreadable: not recorded
        st0 = os.stat(p)
        frozen = {str(p): st0}
        idx = self.w._prestige_store.indexer
        for _ in range(3):                                                   # an unchanged failure: never retried
            self.assertIsNone(PS.records(self.w, list(self.a.years))[y])
        self.assertIs(self.w._prestige_store.indexer, idx)
        with mock.patch.object(PS, '_stat', ReviewFindings.windows_stat(self, frozen)):
            before = PS.source_identity(self.a, y)
        self.write_same_size(p, good, size)                                  # repaired in place ...
        os.utime(p, ns=(st0.st_atime_ns, st0.st_mtime_ns))                   # ... same size and modification time
        with mock.patch.object(PS, '_stat', ReviewFindings.windows_stat(self, frozen)):
            self.assertEqual(PS.source_identity(self.a, y), before)          # the stat identity cannot tell
            w2 = self.world()                                                # reopened (the store file's row)
            PS.records(w2, list(self.a.years))
            self.wait(w2)
            self.assertEqual(PS.records(w2, [y])[y], record(y))
            got = PS.records(self.w, list(self.a.years))                      # and the session that saw it fail
            if got[y] is PS.PENDING:
                self.wait(self.w)
                got = PS.records(self.w, list(self.a.years))
            self.assertEqual(got[y], record(y))

    def test_the_lists_name_the_older_season_shown(self):
        self.a.publish(LAST, 900, None)                                      # the newest season: no record
        self.warm_partial()
        lt = OP.latest(self.w)
        self.assertEqual((lt['year'], lt['newest'], lt['pending']), (LAST - 1, LAST, False))
        note = OP.latest_note(lt)
        self.assertIn(f'recorded at the end of {LAST - 1}', note)
        self.assertIn(f'({LAST})', note)
        self.assertEqual(OP.latest_note(dict(lt, year=LAST)), '')           # the newest itself: nothing to say
        import observer as O
        with mock.patch.object(O.OP, 'latest', lambda w: lt), \
                mock.patch.object(O, 'nation_counts', lambda w: {'Fiji': [1, 1, 0, 0]}):
            self.assertIn(f'recorded at the end of {LAST - 1}', O.nations(NS(live=None, a=None), {})[1])


class ReaderLifecycle(StoreCase):
    """Review of fa78bc7: a reader that only checks bytes keeps the busy back-off, and a failure repaired in a way the
    cheap mark cannot see is shown as soon as the session's bytes check has read it again."""

    def busy_reader(self):
        script = self.tmp / 'busy.sh'
        script.write_text(f'#!/bin/sh\nexit {PS.EXIT_BUSY}\n')
        script.chmod(0o755)
        return str(script)

    def test_a_verification_only_reader_keeps_the_busy_back_off(self):
        self.warm()
        w2 = self.world()                                                    # a new session: everything unchecked
        st = w2._prestige_store
        starts = []
        real = PS.subprocess.Popen

        def counted(*a, **k):
            starts.append(a[0])
            return real(*a, **k)
        with mock.patch.object(PS.sys, 'executable', self.busy_reader()), \
                mock.patch.object(PS.subprocess, 'Popen', counted), mock.patch.object(PS, 'BUSY_RETRY', 0.6):
            for _ in range(3):                                               # three requests, three busy exits ...
                got = PS.records(w2, list(self.a.years))
                self.wait(w2)
                self.assertEqual(got, {y: record(y) for y in self.a.years})   # (pages served from the store)
            self.assertEqual(len(starts), 1)                                 # ... but one start: the back-off holds
            self.assertEqual(st.last_exit, 'busy')
            self.assertGreater(st.retry_after, time.time())
            self.assertTrue(st.unchecked)                                    # the checks are queued again
            time.sleep(0.7)
            PS.records(w2, list(self.a.years))                               # after the wait: started again
            self.wait(w2)
            self.assertEqual(len(starts), 2)
            PS.records(w2, list(self.a.years))                               # (its busy exit dealt with)
            self.assertEqual(len(starts), 2)
        self.assertEqual((st.crashes, st.failed), (0, {}))                   # a lock is never a failure
        st.retry_after = 0.0                                                 # (the wait over)
        PS.records(w2, list(self.a.years))                                   # a real reader now: the checks done
        self.wait(w2)
        PS.records(w2, list(self.a.years))
        self.assertEqual(st.last_exit, 'done')
        self.assertFalse(st.unchecked)

    def padded_member(self, raw, extra, size):
        """A gzip member with an FEXTRA field (fixed bytes at the head) and zero padding to `size` bytes (zeros at the
        tail): two such files share their size and first and last 32 bytes whatever they hold."""
        comp = zlib.compressobj(9, zlib.DEFLATED, -15)
        body = comp.compress(raw) + comp.flush()
        head = b'\x1f\x8b\x08\x04' + b'\0\0\0\0' + b'\x00\xff' + len(extra).to_bytes(2, 'little') + extra
        member = head + body + zlib.crc32(raw).to_bytes(4, 'little') + (len(raw) & 0xffffffff).to_bytes(4, 'little')
        self.assertGreaterEqual(size - len(member), 64, 'test setup: padding')
        return member + b'\0' * (size - len(member))

    def test_a_repair_the_mark_cannot_see_is_shown_after_the_bytes_check(self):
        y = FIRST + 6
        p = self.a.year_path(y)
        good = gzip.decompress(p.read_bytes())
        broken = good.replace(b'"SMALL_OPEN": 40.0', b'"SMALL_OPEN": "40"')
        extra = b'GL' + (20).to_bytes(2, 'little') + b'x' * 20                 # (one FEXTRA subfield)
        size = len(gzip.compress(good)) + 400
        p.write_bytes(self.padded_member(broken, extra, size))
        self.assertIsNone(gzip.decompress(p.read_bytes()) and None)          # (valid gzip: decodes)
        got = self.warm_partial()
        self.assertIsNone(got[y])                                            # unreadable (a string, not a number)
        st0 = os.stat(p)
        mark = PS.file_mark(p)
        with open(p, 'r+b') as f:                                            # repaired in place ...
            f.write(self.padded_member(good, extra, size))
        os.utime(p, ns=(st0.st_atime_ns, st0.st_mtime_ns))                   # ... same size, mtime, first/last 32
        self.assertEqual(PS.file_mark(p), mark)
        with mock.patch.object(PS, '_stat', ReviewFindings.windows_stat(self, {str(p): st0})):
            w2 = self.world()                                                # the next session
            first = PS.records(w2, list(self.a.years))
            self.assertIsNone(first[y])                                      # (still the stored failure, for now)
            self.wait(w2)                                                    # its bytes check finds the change ...
            got = PS.records(w2, list(self.a.years))                         # ... and the same session shows it
            self.assertEqual(got[y], record(y))
            self.assertNotIn(y, w2._prestige_store.failed)


if __name__ == '__main__':
    unittest.main()
