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

    def publish(self, y, gen, rec, pad=0):
        name = f'years/{y}.g{gen:06d}.json.gz'
        p = self.dir / name
        p.parent.mkdir(parents=True, exist_ok=True)
        body = {'year': y, 'prestige': rec, 'events': [{'id': f'{y}:E{i}', 'filler': 'x' * 200} for i in range(400)],
                'pad': 'p' * pad}
        with gzip.open(p, 'wt') as f:
            json.dump(body, f)
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
        real = PS.read_record

        def counted(p):
            self.reads.append(Path(p).name)
            return real(p)
        patch = mock.patch.object(PS, 'read_record', counted)
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
            st.stored({y: PS.source_identity(self.a, y) for y in self.a.years})
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


if __name__ == '__main__':
    unittest.main()
