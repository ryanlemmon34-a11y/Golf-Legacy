"""Observer: each archived season's prestige record, kept compact and persistent so the prestige histories of
tournaments, courses and nations never decode whole seasons on an ordinary page.

A season file decodes to tens of megabytes late in a long world; its `prestige` record (events, courses, venue moves,
nations) is a few tens of kilobytes. The record of every published season is kept, exactly as archived, in
`prestige.sqlite` beside the observer's other caches (observer_stats.cache_path), and in memory once read:

    identity   a stored season is used only if it still IS the season published: the world's identity (seed, first
               season, calendar version and, for a world the observer owns, its world id) is checked once per store,
               and each season's source identity -- the file name the manifest gives it (a season published again
               gets a new name), its size, modification and status-change times, inode and device -- once per read.
               A file replaced at the same path, even with the same size and modification time, has a new status-
               change time or inode, so it is read again; nothing is hashed on a request. SCHEMA (the store's layout)
               and RECORD_VERSION (what is kept of a season) are checked too.
    reuse      seasons already stored are reused after a new season is published (only the new one is read), after
               a roll-back (seasons published again have new files and are read again) and across observer sessions.
    lazily     a page asks only for what it shows. A missing season is read inline only when it is the newest one
               (a single season: what latest() and the directory pages need). Otherwise the store starts a separate
               process that reads the missing seasons one at a time (like the story index), and the page shows them
               as being indexed meanwhile -- never as missing, never decoded on the request.
    safety     a missing, unreadable or corrupt store file is set aside and rebuilt; if no store can be kept at all
               (a read-only folder with no temporary space) the newest season is still read inline and older seasons
               are read in the background into memory only. The memory kept is bounded (MEMORY seasons).

Read-only towards the world: nothing in the archive is written.

    python tools/observer_prestige_store.py index STORE JOBS     (the background reader; JOBS: a JSON file)
"""
from __future__ import annotations

import gzip
import json
import os
import sqlite3
import subprocess
import sys
import threading
import zlib
from collections import OrderedDict
from pathlib import Path

SCHEMA = 1
RECORD_VERSION = 1
MEMORY = 256                                  # seasons' records kept in memory (a few tens of kilobytes each)
PENDING = object()                            # a season being read in the background


def committed_world_id(w):
    """The world id of the committed generation (its meta.json), whether the world is opened live or to browse; None
    for a bare archive folder."""
    live = getattr(w, 'live', None)
    if live is not None and getattr(live, 'world_id', None):
        return live.world_id
    root = getattr(w, 'path', None)
    try:
        cur = json.loads((Path(root) / 'CURRENT').read_text())
        return json.loads((Path(root) / cur['dir'] / 'meta.json').read_text()).get('world_id')
    except (OSError, ValueError, KeyError, TypeError):
        return None


def world_identity(w):
    """What identifies the world this archive belongs to (checked once per store): seed, first season, calendar
    version and the world id given when it was created."""
    a = w.a
    wd = a.world if a is not None else {}
    cal = wd.get('calendar')
    cal = cal.get('version') if isinstance(cal, dict) else cal
    return json.dumps([wd.get('seed'), wd.get('first_year'), cal, committed_world_id(w)], sort_keys=True)


def source_identity(a, y):
    """A season's source identity: its published file name and the file's status (None: not readable now)."""
    try:
        p = a.year_path(y)
        st = os.stat(p)
    except (OSError, KeyError, TypeError):
        return None
    name = (a.files or {}).get('years', {}).get(y) if getattr(a, 'files', None) else None
    return json.dumps([str(name or Path(p).name), st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_ino, st.st_dev])


def read_record(path):
    """A season file's prestige record (None if the season has none), read on its own (not through the archive's
    decoded-season cache)."""
    with gzip.open(path, 'rt') as f:
        d = json.load(f)
    return d.get('prestige')


class PrestigeStore:
    def __init__(self, path, identity):
        self.path = Path(path) if path else None
        self.identity = identity
        self.mem = OrderedDict()              # year -> (source identity, record)
        self.lock = threading.Lock()
        self.indexer = None
        self.jobs = {}                        # year -> source identity given to the background reader
        self.failed = {}                      # year -> source identity it could not read (not tried again here)
        self.start_lock = threading.Lock()
        self.stopped = False                  # the reader was stopped on purpose (not a failure)
        self.crashes = 0                      # readers that ended abnormally in a row
        self.reads_inline = 0
        self._checked = False
        self._broken = False

    # -- the store file ------------------------------------------------------------------------------------------
    def _open(self):
        """A connection to the store file, its layout and world checked once (another world or layout at this path:
        its seasons are dropped). Raises sqlite3.DatabaseError or OSError on a file that cannot be used."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=5)
        try:
            db.execute('PRAGMA journal_mode=WAL')       # (the background reader writes while pages read)
            db.execute('CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS seasons(year INT PRIMARY KEY, source TEXT, version INT, '
                       'record BLOB)')
            if not self._checked:
                meta = dict(db.execute('SELECT k, v FROM meta').fetchall())
                if meta.get('schema') != str(SCHEMA) or meta.get('world') != self.identity:
                    db.execute('DELETE FROM seasons')
                    db.execute('INSERT OR REPLACE INTO meta VALUES (?, ?)', ('schema', str(SCHEMA)))
                    db.execute('INSERT OR REPLACE INTO meta VALUES (?, ?)', ('world', self.identity))
                    db.commit()
                self._checked = True
            return db
        except BaseException:
            db.close()
            raise

    def _db(self):
        if self.path is None or self._broken:
            return None
        try:
            return self._open()
        except (sqlite3.DatabaseError, OSError):
            return self._set_aside()

    def _set_aside(self):
        """The store file cannot be used: move it aside once and start a new one (else run without one)."""
        if self.path is None:
            return None
        try:
            for suffix in ('', '-wal', '-shm'):
                p = Path(str(self.path) + suffix)
                if p.exists():
                    os.replace(p, Path(str(p) + '.corrupt'))
            self._checked = False
            return self._open()
        except (sqlite3.DatabaseError, OSError):
            self._broken = True                  # (no store: memory only)
            return None

    def _remember(self, y, source, rec):
        with self.lock:
            self.mem[y] = (source, rec)
            self.mem.move_to_end(y)
            while len(self.mem) > MEMORY:
                self.mem.popitem(last=False)

    def stored(self, sources):
        """{year: record} for the seasons whose stored source identity is the one given ({year: source})."""
        out = {}
        need = {}
        with self.lock:
            for y, src in sources.items():
                got = self.mem.get(y)
                if got is not None and got[0] == src:
                    self.mem.move_to_end(y)
                    out[y] = got[1]
                elif src is not None:
                    need[y] = src
        if not need:
            return out
        db = self._db()
        if db is None:
            return out
        try:
            ys = sorted(need)
            for i in range(0, len(ys), 500):
                chunk = ys[i:i + 500]
                for y, src, ver, blob in db.execute(f'SELECT year, source, version, record FROM seasons WHERE year IN '
                                                    f'({",".join("?" * len(chunk))})', chunk):
                    if src == need[y] and ver == RECORD_VERSION:
                        rec = json.loads(zlib.decompress(blob))
                        self._remember(y, src, rec)
                        out[y] = rec
        except (sqlite3.DatabaseError, zlib.error, ValueError):
            db.close()
            self._set_aside()
            return out
        db.close()
        return out

    def put(self, y, source, rec):
        self._remember(y, source, rec)
        db = self._db()
        if db is None:
            return
        try:
            db.execute('INSERT OR REPLACE INTO seasons VALUES (?, ?, ?, ?)',
                       (y, source, RECORD_VERSION, zlib.compress(json.dumps(rec, separators=(',', ':')).encode(), 6)))
            db.commit()
        except sqlite3.DatabaseError:
            pass
        finally:
            db.close()

    # -- the background reader ---------------------------------------------------------------------------------------
    def start_indexer(self, jobs):
        """Read these seasons ([year, season file, source identity]) in a separate process, one at a time (one reader
        per store; a request while it runs only waits for it)."""
        with self.start_lock:
            if not jobs or self.indexing():
                return
            self.jobs = {y: src for y, _, src in jobs}
            self.stopped = False
            if self.path is None or self._broken:        # no store file: read them in a thread into memory only
                def run():
                    for y, p, src in jobs:
                        try:
                            self._remember(y, src, read_record(p))
                        except (OSError, ValueError, EOFError):
                            pass
                self.indexer = threading.Thread(target=run, daemon=True, name='prestige-index')
                self.indexer.start()
                return
            self.path.parent.mkdir(parents=True, exist_ok=True)
            jobfile = self.path.with_suffix('.jobs.json')
            jobfile.write_text(json.dumps({'identity': self.identity, 'jobs': jobs}))
            with open(self.path.with_suffix('.log'), 'w') as err:
                self.indexer = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), 'index',
                                                 str(self.path), str(jobfile)], stdout=subprocess.DEVNULL, stderr=err)

    CRASHES = 3

    def settle(self, have):
        """After a reader ended: if it went through its list, the seasons it was given but did not store ({year:
        record} `have` = what is stored now) could not be read; they are shown as not recorded and not tried again by
        this observer (the next observer, or a changed file, tries again). A reader stopped on purpose is simply
        started again; one that ended abnormally is started again up to CRASHES times in a row."""
        if not self.jobs or self.indexing():
            return
        p = self.indexer
        done = isinstance(p, threading.Thread) or (p is not None and p.returncode == 0)
        if not done and not self.stopped:
            self.crashes += 1
        if done:
            self.crashes = 0
        if done or self.crashes >= self.CRASHES:
            for y, src in self.jobs.items():
                if y not in have:
                    self.failed[y] = src
        self.jobs = {}

    def indexing(self):
        p = self.indexer
        if p is None:
            return False
        return p.is_alive() if isinstance(p, threading.Thread) else p.poll() is None

    def stop_indexer(self):
        self.stopped = True
        p = self.indexer
        if p is not None and not isinstance(p, threading.Thread) and p.poll() is None:
            p.terminate()
            try:
                p.wait(5)
            except Exception:
                p.kill()


def store_for(w):
    """The world's prestige store (one per opened history; a new history -- republished -- keeps it, since stored
    seasons are checked one by one)."""
    st = w.__dict__.get('_prestige_store')
    ident = world_identity(w)
    if st is None or st.identity != ident:
        path = None
        try:
            import observer_stats as ST
            p = ST.cache_path(w)
            path = p.with_name(p.name.replace('stats.sqlite', 'prestige.sqlite'))
        except Exception:
            path = None
        if st is not None:
            st.stop_indexer()
        st = w._prestige_store = PrestigeStore(path, ident)
    return st


def records(w, years, inline_newest=True):
    """{year: record or None (none archived) or PENDING (being read)} for the archived `years`. Stored seasons come
    from the store; the newest archived season, if asked for and missing, is read now (one season); any other
    missing season starts the background reader and is PENDING."""
    a = w.a
    if a is None or not years:
        return {}
    st = store_for(w)
    sources = {y: source_identity(a, y) for y in years if y in a.years}
    out = dict(st.stored(sources))
    missing = [y for y in sources if y not in out]
    newest = max(a.years) if a.years else None
    if inline_newest and newest in missing and sources[newest] is not None:
        try:                                            # (read from the file itself, never from a decoded copy
            rec = read_record(a.year_path(newest))      #  that might predate a same-path replacement)
            st.reads_inline += 1
            st.put(newest, sources[newest], rec)
        except (OSError, ValueError, EOFError):
            rec = None                                  # (unreadable now: not stored, tried again next time)
        out[newest] = rec
        missing.remove(newest)
    for y in list(missing):                             # unreadable files (vanished: no source) are not recorded
        if sources[y] is None or st.failed.get(y) == sources[y]:
            out[y] = None
            missing.remove(y)
    if missing:
        every = {y: source_identity(a, y) for y in a.years}
        have = st.stored(every)
        st.settle(have)
        todo = [[y, str(a.year_path(y)), every[y]] for y in sorted(set(every) - set(have), reverse=True)
                if every[y] is not None and st.failed.get(y) != every[y]]
        st.start_indexer(todo)
        for y in missing:
            out[y] = None if st.failed.get(y) == sources[y] else PENDING
    return out


# ---- the background reader (a separate process) -------------------------------------------------------------------
def index_seasons(store, jobfile):
    try:
        os.nice(10)                                     # (behind the pages and any advance)
    except (OSError, AttributeError):
        pass
    spec = json.loads(Path(jobfile).read_text())
    s = PrestigeStore(store, spec['identity'])
    for y, path, src in spec['jobs']:
        if y in s.stored({y: src}):
            continue
        try:
            rec = read_record(path)
        except (OSError, ValueError, EOFError):
            continue                                    # (left out: the observer shows it as not recorded)
        s.put(y, src, rec)
        s.mem.clear()
        release_memory()                                # (one season decoded at a time: give it back each time)


def release_memory():
    """Hand freed memory back to the system between seasons (a late season decodes to hundreds of megabytes; without
    this the reader's footprint creeps up season by season). Linux only; elsewhere a collection alone."""
    import gc
    gc.collect()
    try:
        import ctypes
        ctypes.CDLL('libc.so.6').malloc_trim(0)
    except (OSError, AttributeError):
        pass


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == 'index':
        index_seasons(Path(sys.argv[2]), Path(sys.argv[3]))
