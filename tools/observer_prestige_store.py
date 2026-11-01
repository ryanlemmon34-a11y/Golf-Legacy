"""Observer: each archived season's prestige record, kept compact and persistent so the prestige histories of
tournaments, courses and nations never decode whole seasons on an ordinary page.

A season file decodes to hundreds of megabytes late in a long world; its `prestige` record (events, courses, venue
moves, nations) is a few tens of kilobytes. The record of every published season is kept, exactly as archived, in
`prestige.sqlite` beside the observer's other caches (observer_stats.cache_path), and in memory once read:

    identity   a stored season is used only if it still IS the season published. The world's identity (seed, first
               season, calendar version and the world id of the committed generation) is checked once per store.
               Each season is checked on every use, cheaply and on every system:
                 - its source: the file name the manifest gives it (a season published again gets a new name), its
                   size and modification time (and, where the system keeps them, status-change time, inode and
                   device -- not relied on: Windows keeps a creation time there and the same file index after a
                   rewrite in place);
                 - its gzip members' trailers (each member's CRC-32 and length of the data it holds), recorded when
                   the season was read and read back on every use -- eight bytes a member, a few dozen members a
                   season. A file rewritten in place as valid gzip with other content, even with the same size and
                   modification time, has other trailers and is read again. This is not an integrity check: damage
                   that leaves every trailer as it was (or a rewrite reproducing them) is not seen on a request.
               The whole file's bytes are checked in the background instead: the SHA-256 of the bytes each season was
               read from is kept with it, and once per observer session (per store object) the background reader
               hashes every stored season's file again and reads again any that differ. Until that pass reaches a
               season, a page may show what was stored for it. Nothing is hashed on a request. (An authoritative
               digest written into the manifest at publication would let new archives be checked without the pass:
               a change to the archive writer, proposed separately.)
               SCHEMA (the store's layout) and RECORD_VERSION (what is kept of a season) are checked too.
    reuse      seasons already stored are reused after a new season is published (only the new one is read), after
               a roll-back (seasons published again have new files and are read again) and across observer sessions.
    lazily     a page asks only for what it shows. A missing season is read inline only when it is the newest one
               (a single season: what latest() and the directory pages need). Otherwise one background reader at a
               time reads the missing seasons, newest first, in a separate process at lower priority (like the story
               index), and the page shows them as being read meanwhile -- never as missing, never decoded on the
               request. If the reader's process cannot be started (no writable job file), it runs as a thread.
    failures   a season the reader could not read is reported by the reader itself (never inferred from what is no
               longer in memory): a file that is not a readable season of the expected shape is shown as not
               recorded until its file changes; one that could not be opened (locked, vanished) is tried again,
               READ_TRIES times in this observer. A reader that keeps dying is given up on after CRASHES.
    locking    the store file is shared (pages read while the background reader writes). A page waits for it at most
               PAGE_TIMEOUT; if it is busy or locked the page shows the seasons not in memory as being read, and the
               file is left as it is -- a lock is never taken for damage. The reader waits up to READER_TIMEOUT, then
               stops (EXIT_BUSY) and is not started again for BUSY_RETRY seconds.
    safety     a store file that SQLite reports corrupt or not a database is set aside (renamed .corrupt) and rebuilt; one
               that cannot be opened or written for another reason (read-only folder, no space) is left as it is and
               this observer keeps the seasons in memory only. If no store can be kept at all
               the newest season is still read inline and the others are read by a thread into memory only (then
               every season of the history is kept in memory: a few tens of kilobytes each). With a store, memory
               keeps at most MEMORY seasons; one evicted is read back from the store, never treated as missing.

Read-only towards the world: nothing in the archive is written.

    python tools/observer_prestige_store.py index STORE JOBS     (the background reader; JOBS: a JSON file)
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
import zlib
from collections import OrderedDict
from pathlib import Path

SCHEMA = 2
RECORD_VERSION = 1
MEMORY = 256                                  # seasons' records kept in memory with a store (tens of kilobytes each)
READ_TRIES = 3                                # readers given a season that could not be opened, in one observer
PAGE_TIMEOUT = 0.25                           # seconds a page waits for a busy store file
READER_TIMEOUT = 30.0                         # seconds the background reader waits for it
BUSY_RETRY = 30.0                             # seconds before a reader that found the store busy is started again
EXIT_BUSY = 75                                # the reader's exit status when the store stayed busy
PENDING = object()                            # a season being read in the background
_stat = os.stat                               # (tests give it another system's semantics)


class UnreadableSeason(ValueError):
    """A season file that is not a readable season with a prestige record of the expected shape."""


class StoreBusy(Exception):
    """The store file stayed busy or locked (another connection holds it)."""


def sqlite_problem(e):
    """'busy' (locked by another connection: wait, never repair), 'corrupt' (not a database, or damaged: set it aside)
    or 'unavailable' (cannot be opened or written for another reason: leave it, keep seasons in memory)."""
    code = getattr(e, 'sqlite_errorcode', None)
    if code is not None:
        primary = code & 0xff
        if primary in (5, 6):                           # SQLITE_BUSY, SQLITE_LOCKED
            return 'busy'
        if primary in (11, 26):                         # SQLITE_CORRUPT, SQLITE_NOTADB
            return 'corrupt'
        return 'unavailable'
    msg = str(e).lower()
    if 'locked' in msg or 'busy' in msg:
        return 'busy'
    if 'not a database' in msg or 'malformed' in msg or 'corrupt' in msg:
        return 'corrupt'
    return 'unavailable'


def file_digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


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
    """A season's source: its published file name and the file's status (None: not there now)."""
    try:
        p = a.year_path(y)
        st = _stat(p)
    except (OSError, KeyError, TypeError):
        return None
    name = (a.files or {}).get('years', {}).get(y) if getattr(a, 'files', None) else None
    return json.dumps([str(name or Path(p).name), st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_ino, st.st_dev])


# ---- a season file: its record and its members' trailers ----------------------------------------------------------
def _number(v):
    return v is None or (isinstance(v, (int, float)) and not isinstance(v, bool))


def check_record(rec):
    """The record as archived if it has the shape the pages read (None: the season has none); else UnreadableSeason."""
    if rec is None:
        return None
    ok = isinstance(rec, dict)
    if ok:
        for k in ('events', 'courses'):
            v = rec.get(k, {})
            ok = ok and isinstance(v, dict) and all(_number(x) for x in v.values())
        moves = rec.get('venue_moves', [])
        ok = ok and isinstance(moves, list) and all(isinstance(m, dict) for m in moves)
        n = rec.get('nations', {})
        ok = ok and isinstance(n, dict)
        if ok:
            for k in ('prestige', 'multiplier', 'ratio', 'achievement'):
                v = n.get(k, {})
                ok = ok and isinstance(v, dict) and all(_number(x) for x in v.values())
            for k in ('shares', 'allocated', 'baseline_shares'):
                v = n.get(k, {})
                ok = ok and isinstance(v, dict) and all(isinstance(x, dict) for x in v.values())
    if not ok:
        raise UnreadableSeason('a prestige record of an unexpected shape')
    return rec


def read_season(path):
    """(record or None, members, digest) of a season file, read on its own (not through the archive's decoded-season
    cache): members are [end offset, the member's 8-byte trailer (CRC-32 and length) in hex], digest the SHA-256 of
    the bytes read. Raises OSError if the file cannot be opened or read, UnreadableSeason if it is not a readable
    season (malformed compression included)."""
    with open(path, 'rb') as f:
        data = f.read()
    digest = hashlib.sha256(data).hexdigest()
    view, pos, parts, members = memoryview(data), 0, [], []
    try:
        while pos < len(data):
            if data[pos:pos + 2] != b'\x1f\x8b':
                if not data[pos:].strip(b'\0'):           # (zero padding after the last member, as gzip allows)
                    break
                raise UnreadableSeason('not a gzip member')
            d = zlib.decompressobj(16 + zlib.MAX_WBITS)
            parts.append(d.decompress(view[pos:]))
            if not d.eof:
                raise UnreadableSeason('a truncated gzip member')
            end = len(data) - len(d.unused_data)
            members.append([end, data[end - 8:end].hex()])
            pos = end
        if not members:
            raise UnreadableSeason('an empty file')
        doc = json.loads(b''.join(parts))
    except UnreadableSeason:
        raise
    except (zlib.error, ValueError, UnicodeDecodeError) as e:
        raise UnreadableSeason(str(e)) from None
    finally:
        view.release()
    if not isinstance(doc, dict):
        raise UnreadableSeason('not a season')
    return check_record(doc.get('prestige')), members, digest


def read_record(path):
    """A season file's prestige record (None if the season has none)."""
    return read_season(path)[0]


def same_content(path, members):
    """Whether the file still has the members recorded when it was read (their trailers at the same places)."""
    if not members:
        return False
    try:
        with open(path, 'rb') as f:
            for end, trailer in members:
                f.seek(end - 8)
                if f.read(8).hex() != trailer:
                    return False
            return True
    except (OSError, ValueError, TypeError):
        return False


# ---- the store ----------------------------------------------------------------------------------------------------
class PrestigeStore:
    CRASHES = 3

    def __init__(self, path, identity, timeout=PAGE_TIMEOUT, session=None, raise_busy=False):
        self.path = Path(path) if path else None
        self.identity = identity
        self.timeout = timeout
        self.session = session or uuid.uuid4().hex   # (this observer's session: the bytes check runs once per session)
        self.raise_busy = raise_busy              # (the background reader stops on a busy store; a page carries on)
        self.unchecked = set()                    # seasons served from the file not yet bytes-checked this session
        self.verifying = False
        self.retry_after = 0.0
        self.skip_until = 0.0                     # (a page found the file busy: not asked again until then)
        self.mem = OrderedDict()              # year -> (source identity, record, members)
        self.lock = threading.Lock()
        self.indexer = None
        self.stop_event = threading.Event()
        self.jobs = {}                        # year -> source identity given to the running (or last) reader
        self.failed = {}                      # year -> source identity: not readable (shown as not recorded)
        self.tries = {}                       # (year, source) -> readers that could not open it, in this observer
        self.start_lock = threading.Lock()
        self.stopped = False                  # the reader was stopped on purpose (not a failure)
        self.crashes = 0                      # readers that ended abnormally in a row
        self.history_size = 0                 # seasons in the history (memory bound without a store file)
        self.reads_inline = 0
        self._checked = False
        self._broken = False

    # -- the store file ------------------------------------------------------------------------------------------
    def _open(self):
        """A connection to the store file, its layout and world checked once (another world or layout at this path:
        its seasons are dropped). Raises sqlite3.DatabaseError or OSError on a file that cannot be used."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=self.timeout)
        try:
            db.execute('PRAGMA journal_mode=WAL')       # (the background reader writes while pages read)
            db.execute('CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)')
            if not self._checked:
                meta = dict(db.execute('SELECT k, v FROM meta').fetchall())
                if meta.get('schema') != str(SCHEMA) or meta.get('world') != self.identity:
                    db.execute('DROP TABLE IF EXISTS seasons')
                    db.execute('INSERT OR REPLACE INTO meta VALUES (?, ?)', ('schema', str(SCHEMA)))
                    db.execute('INSERT OR REPLACE INTO meta VALUES (?, ?)', ('world', self.identity))
            # status: 'ok' (record, possibly null: none archived), 'content' (not a readable season), 'io' (could not
            # be opened); members: the gzip trailers read with it; digest: SHA-256 of the bytes read; checked: the
            # observer session whose background pass last found the file's bytes unchanged
            db.execute('CREATE TABLE IF NOT EXISTS seasons(year INT PRIMARY KEY, source TEXT, version INT, '
                       'status TEXT, members TEXT, digest TEXT, checked TEXT, record BLOB)')
            db.commit()
            self._checked = True
            return db
        except BaseException:
            db.close()
            raise

    def has_file(self):
        return self.path is not None and not self._broken

    def _db(self):
        """A connection, or None: no store file, or it is busy now (StoreBusy for the background reader)."""
        if not self.has_file() or (not self.raise_busy and time.monotonic() < self.skip_until):
            return None
        try:
            return self._open()
        except sqlite3.DatabaseError as e:
            return self._problem(e)
        except OSError:
            self._broken = True                     # (cannot be made here: memory only, nothing renamed)
            return None

    def _problem(self, e):
        kind = sqlite_problem(e)
        if kind == 'busy':
            if self.raise_busy:
                raise StoreBusy(str(e)) from None
            self.skip_until = time.monotonic() + 2 * self.timeout + 1.0
            return None                             # (busy now: nothing from the file this time, nothing touched)
        if kind == 'corrupt':
            return self._set_aside()
        self._broken = True                         # (read-only, full, ...: left as it is; memory only)
        return None

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

    def _remember(self, y, source, rec, members):
        limit = MEMORY if self.has_file() else max(MEMORY, self.history_size)
        with self.lock:
            self.mem[y] = (source, rec, members)
            self.mem.move_to_end(y)
            while len(self.mem) > limit:
                self.mem.popitem(last=False)

    def stored(self, sources):
        """{year: record} for the seasons given ({year: (source identity, season file)}) that are stored with that
        source and still have the content they were read with; a season known to be unreadable with that source
        gives None (not recorded)."""
        out, need = {}, {}
        with self.lock:
            hits = {y: self.mem.get(y) for y in sources}
        for y, (src, path) in sources.items():
            got = hits[y]
            if src is None:
                continue
            if self.failed.get(y) == src:
                out[y] = None
            elif got is not None and got[0] == src and same_content(path, got[2]):
                with self.lock:
                    if y in self.mem:
                        self.mem.move_to_end(y)
                out[y] = got[1]
            else:
                need[y] = (src, path)
        if not need:
            return out
        db = self._db()
        if db is None:
            return out
        try:
            ys = sorted(need)
            for i in range(0, len(ys), 500):
                chunk = ys[i:i + 500]
                for y, src, ver, status, members, checked, blob in db.execute(
                        f'SELECT year, source, version, status, members, checked, record FROM seasons WHERE year IN '
                        f'({",".join("?" * len(chunk))})', chunk).fetchall():
                    if src != need[y][0] or ver != RECORD_VERSION:
                        continue
                    if status == 'content':
                        self.failed[y] = src
                        out[y] = None
                    elif status == 'ok':
                        members = json.loads(members)
                        if same_content(need[y][1], members):
                            rec = check_record(json.loads(zlib.decompress(blob)))
                            self._remember(y, src, rec, members)
                            out[y] = rec
                            if checked != self.session:
                                self.unchecked.add(y)
        except sqlite3.DatabaseError as e:
            db.close()
            self._problem(e)
            return out
        except (zlib.error, ValueError, TypeError):
            db.close()
            self._set_aside()                       # (rows that do not decode: the file is not ours to trust)
            return out
        db.close()
        return out

    def put(self, y, source, rec, members, digest=None):
        self._remember(y, source, rec, members)
        self._write(y, source, 'ok', members, zlib.compress(json.dumps(rec, separators=(',', ':')).encode(), 6),
                    digest, self.session)

    def put_failure(self, y, source, status):
        """The reader could not read this season: 'content' (not a readable season: not recorded until the file
        changes) or 'io' (could not be opened: tried again)."""
        if status == 'content':
            self.failed[y] = source
        else:
            self.tries[(y, source)] = self.tries.get((y, source), 0) + 1   # (a thread's own count; see settle)
        self._write(y, source, status, None, None, None, None)

    def _write(self, y, source, status, members, blob, digest, checked):
        db = self._db()
        if db is None:
            return
        try:
            db.execute('INSERT OR REPLACE INTO seasons VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                       (y, source, RECORD_VERSION, status, None if members is None else json.dumps(members), digest,
                        checked, blob))
            db.commit()
        except sqlite3.DatabaseError as e:
            db.close()
            db = None
            self._problem(e)
        finally:
            if db is not None:
                db.close()

    def stored_digest(self, y, source):
        """(digest, checked) of a stored readable season with this source, else None."""
        db = self._db()
        if db is None:
            return None
        try:
            row = db.execute('SELECT digest, checked FROM seasons WHERE year = ? AND source = ? AND status = ? '
                             'AND version = ?', (y, source, 'ok', RECORD_VERSION)).fetchone()
            return row
        except sqlite3.DatabaseError as e:
            db.close()
            db = None
            self._problem(e)
            return None
        finally:
            if db is not None:
                db.close()

    def mark_checked(self, y, source):
        db = self._db()
        if db is None:
            return
        try:
            db.execute('UPDATE seasons SET checked = ? WHERE year = ? AND source = ?', (self.session, y, source))
            db.commit()
        except sqlite3.DatabaseError as e:
            db.close()
            db = None
            self._problem(e)
        finally:
            if db is not None:
                db.close()

    def io_failures(self, years):
        """{year: source} the reader reported as not opened (status 'io') among `years`."""
        db = self._db()
        if db is None or not years:
            if db is not None:
                db.close()
            return {}
        try:
            ys = sorted(years)
            out = {}
            for i in range(0, len(ys), 500):
                chunk = ys[i:i + 500]
                out.update(db.execute(f'SELECT year, source FROM seasons WHERE status = ? AND year IN '
                                      f'({",".join("?" * len(chunk))})', ['io'] + chunk).fetchall())
            return out
        except sqlite3.DatabaseError as e:
            db.close()
            db = None
            self._problem(e)
            return {}
        finally:
            if db is not None:
                db.close()

    # -- the background reader ---------------------------------------------------------------------------------------
    def start_indexer(self, jobs):
        """Work through these seasons ([year, season file, source identity, 'read' or 'verify']) one at a time: in a
        separate process, or a thread when the process cannot be started or there is no store file. One reader per
        store; a request while it runs only waits for it; after a busy store, none for BUSY_RETRY seconds."""
        with self.start_lock:
            if not jobs or self.indexing() or time.time() < self.retry_after:
                return
            self.jobs = {y: src for y, _, src, mode in jobs if mode == 'read'}
            self.verifying = any(mode == 'verify' for *_, mode in jobs)
            self.stopped = False
            self.stop_event.clear()
            if self.has_file():
                try:
                    jobfile = self.path.with_suffix('.jobs.json')
                    jobfile.write_text(json.dumps({'identity': self.identity, 'session': self.session, 'jobs': jobs}))
                    with open(self.path.with_suffix('.log'), 'w') as err:
                        self.indexer = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), 'index',
                                                         str(self.path), str(jobfile)],
                                                        stdout=subprocess.DEVNULL, stderr=err)
                    return
                except OSError:
                    pass                                 # (no job file or process: a thread instead)
            self.indexer = threading.Thread(target=self._read_jobs, args=(jobs,), daemon=True, name='prestige-index')
            self.indexer.start()

    def _read_jobs(self, jobs):
        run_jobs(self, jobs, self.stop_event)

    def indexing(self):
        p = self.indexer
        if p is None:
            return False
        return p.is_alive() if isinstance(p, threading.Thread) else p.poll() is None

    def settle(self, have):
        """After a reader ended. Seasons it reported unreadable are known (stored as such); one it could not open is
        given to READ_TRIES readers before it is shown as not recorded in this observer; a season merely no longer in
        memory is never taken for a failure. A reader stopped on purpose is simply started again; one that ended
        abnormally is started again up to CRASHES times in a row, then the seasons it left are not recorded here."""
        if not self.jobs or self.indexing():
            return
        p = self.indexer
        thread = isinstance(p, threading.Thread)
        busy = (not thread and p is not None and p.returncode == EXIT_BUSY)
        done = thread or (p is not None and p.returncode == 0)
        if busy:
            self.retry_after = time.time() + BUSY_RETRY      # (the store was locked: not a failure, wait a little)
        elif not done and not self.stopped:
            self.crashes += 1
        if done:
            self.crashes = 0
        left = {y: src for y, src in self.jobs.items() if y not in have}
        if thread:                                       # (counted by the thread itself, store file or not)
            for y, src in left.items():
                if self.tries.get((y, src), 0) >= READ_TRIES:
                    self.failed[y] = src
        else:
            for y, src in self.io_failures(left).items():
                if left.get(y) == src:
                    n = self.tries[(y, src)] = self.tries.get((y, src), 0) + 1
                    if n >= READ_TRIES:
                        self.failed[y] = src
        if self.crashes >= self.CRASHES:
            for y, src in left.items():
                self.failed[y] = src
        self.jobs = {}

    def after_reader(self):
        """After a reader that checked bytes: what memory holds is taken from the store again (a season it found
        changed was read again there)."""
        if self.verifying and not self.indexing():
            with self.lock:
                self.mem.clear()
            self.verifying = False

    def stop_indexer(self):
        self.stopped = True
        self.stop_event.set()
        p = self.indexer
        if p is None:
            return
        if isinstance(p, threading.Thread):
            if p is not threading.current_thread():
                p.join(5)
        elif p.poll() is None:
            p.terminate()
            try:
                p.wait(5)
            except Exception:
                p.kill()


def read_into(store, y, path, src):
    """Read one season into the store (or record why it could not be)."""
    try:
        rec, members, digest = read_season(path)
    except UnreadableSeason:
        store.put_failure(y, src, 'content')
        return
    except OSError:
        store.put_failure(y, src, 'io')
        return
    store.put(y, src, rec, members, digest)


def run_jobs(store, jobs, stop=None, between=None):
    """The background reader's work: 'read' a missing season; 'verify' a stored one (its file hashed again: read again
    if the bytes are not those it was read from, else marked checked for this session)."""
    for y, path, src, mode in jobs:
        if stop is not None and stop.is_set():
            return
        if mode == 'verify':
            row = store.stored_digest(y, src)
            if row is None or row[1] == store.session:
                continue                                # (gone, changed since, or already checked this session)
            try:
                same = file_digest(path) == row[0]
            except OSError:
                continue
            if same:
                store.mark_checked(y, src)
                continue
        elif y in store.stored({y: (src, path)}):
            continue
        read_into(store, y, path, src)
        if between is not None:
            between()


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
    """{year: record or None (none archived, or not readable) or PENDING (being read)} for the archived `years`.
    Stored seasons come from the store; the newest archived season, if asked for and missing, is read now (one
    season); any other missing season starts the background reader and is PENDING."""
    a = w.a
    if a is None or not years:
        return {}
    st = store_for(w)
    st.history_size = len(a.years)
    st.after_reader()
    path = lambda y: str(a.year_path(y))
    sources = {y: (source_identity(a, y), path(y)) for y in years if y in a.years}
    out = dict(st.stored(sources))
    missing = [y for y in sources if y not in out]
    newest = max(a.years) if a.years else None
    if inline_newest and newest in missing and sources[newest][0] is not None:
        try:                                            # (read from the file itself, never from a decoded copy)
            rec, members, digest = read_season(sources[newest][1])
            st.reads_inline += 1
            st.put(newest, sources[newest][0], rec, members, digest)
        except UnreadableSeason:
            st.put_failure(newest, sources[newest][0], 'content')
            rec = None
        except OSError:
            rec = None                                  # (could not be opened now: tried again next time)
        out[newest] = rec
        missing.remove(newest)
    for y in list(missing):                             # a season whose file is not there: not recorded
        if sources[y][0] is None:
            out[y] = None
            missing.remove(y)
    verify = sorted((st.unchecked & set(a.years)) if st.has_file() and not st.indexing() else (), reverse=True)
    if missing or verify:
        todo = []
        if missing:                                     # (the reader takes every missing season, newest first)
            every = {y: (source_identity(a, y), path(y)) for y in a.years}
            have = st.stored(every)
            st.settle(have)
            todo = [[y, every[y][1], every[y][0], 'read'] for y in sorted(set(every) - set(have), reverse=True)
                    if every[y][0] is not None and st.failed.get(y) != every[y][0]]
        for y in verify:                                # (seasons served from the store, bytes not yet checked
            src = sources[y][0] if y in sources else source_identity(a, y)   # this session: behind the reads)
            if src is not None:
                todo.append([y, path(y), src, 'verify'])
        st.start_indexer(todo)
        if st.indexing():
            st.unchecked -= set(verify)
        for y in missing:
            out[y] = None if st.failed.get(y) == sources[y][0] else PENDING
    return out


# ---- the background reader (a separate process) -------------------------------------------------------------------
def index_seasons(store, jobfile):
    try:
        os.nice(10)                                     # (behind the pages and any advance)
    except (OSError, AttributeError):
        pass
    spec = json.loads(Path(jobfile).read_text())
    s = PrestigeStore(store, spec['identity'], timeout=READER_TIMEOUT, session=spec.get('session'), raise_busy=True)

    def between():
        s.mem.clear()
        release_memory()                                # (one season decoded at a time: give it back each time)
    try:
        run_jobs(s, spec['jobs'], between=between)
    except StoreBusy:
        sys.exit(EXIT_BUSY)


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
