"""The weekly session: the one way an observer advances a world (roadmap M1).

    s = Session.create('worlds/my_world', seed=2027)      # a new world, committed at its first week
    s = Session.open('worlds/my_world')                   # or reopen one (recovering if needed)
    r = s.advance_one_week(expected=s.cursor)             # play the next week and commit it
    s.advance(52)                                         # longer advances: the same weekly step, one commit

**The cursor** says exactly what happens next: `{'year', 'week', 'phase'}` with phase 'start' (1 January
has not run yet: the next advance runs it, then week 1), or 'week' (the next advance plays that week).
After week 52 the same advance runs the end of the season and archives it, and the cursor moves to the
next year's 'start'. Year start and year end therefore run exactly once, in order, whatever the calls.

**Idempotent, serialised advances.** An advance may name the cursor it expects (a stale request is
refused with StaleCursor and changes nothing) and an operation key (repeating a committed key returns
its stored result without simulating again). The key is looked up only after the committed world has
been synchronised under the lock, so an operation that recovery rolled back (its generation was
damaged) is applied again rather than reported as done. Advances are serialised: a lock inside the process,
and a lock file across processes (Busy if another advance holds it).

Operation keys are remembered for the last OPS_KEPT committed advances (not only the last), and are
checked against the committed world on disk, so a request retried through another handle or resubmitted
after later advances is recognised.

**One coherent world per generation.** Each advance writes a new checkpoint generation: the whole
simulation and the session's state go to a temporary directory, are hashed and read back, the
directory is renamed into place and only then is the CURRENT pointer replaced (an atomic rename). A
crash before that leaves the previous generation current; after it, the new one. If anything fails
before the commit, the session goes back to the committed world, so memory never runs ahead of disk.
The previous generation is kept as the last known good one; older ones and orphaned temporary
directories are removed (only by whoever holds the lock: opening a session while another process is
advancing never touches its work).

**History in the same transaction.** At season end, the season's history (its season file, and the
people, relationships and records tables, and the list of archived seasons) is staged inside the new
checkpoint generation, not written to the archive. Only once the generation is committed is it
published to archive/ (season file and index first, the list of seasons last) and the published
generation recorded (archive/PUBLISHED). A crash before the commit leaves the archive exactly as it was;
a crash after it is repaired by publishing the committed generation's staged history again (on opening,
before the next advance, or when a committed operation is retried), which is idempotent. A generation
with no new season carries the history it stands on (hard links to the files of the generation before
it) and every generation names the one that produced that history (history_gen; archive/PUBLISHED holds
the one published). So when a damaged generation makes an earlier one current, the earlier one's own
history -- seasons, people, relationships and records -- is published again and the later seasons are
removed. So the running world, the committed checkpoint and the visible history always agree. The live simulation keeps only recent seasons (Season.prune_history), so
a checkpoint does not carry the whole history.
"""
from __future__ import annotations

import gc
import gzip
import hashlib
import json
import os
import pickle
import shutil
import socket
import threading
import time
from pathlib import Path

from .archive import STATE_FILES, ArchiveWriter, _read, _write, index_season
from .savegame import engine_commit, engine_id

FORMAT = 'golf-legacy-session/1'
SCHEMA = 1
KEEP_GENERATIONS = 2                 # the current generation and the last known good one before it
OPS_KEPT = 32                        # committed operation keys remembered (retries, resubmitted forms)


class StaleCursor(Exception):
    """The request expected a different cursor: the world has moved on (or not yet reached it)."""


class Busy(Exception):
    """Another advance holds the session's lock."""


class Session:
    def __init__(self, directory, season, state, generation):
        self.dir = Path(directory)
        self.season = season
        self.state = state                 # cursor, recent operations, archive writer state, world id
        state.setdefault('ops', [[state['last_op']['key'], [state['last_op']['result']]]]   # (older saves)
                         if state.get('last_op') and state['last_op'].get('key') is not None else [])
        self.generation = generation
        self._pending = None               # season history staged by uncommitted weeks
        self._lock = threading.Lock()
        # diagnostics only (tools/long_world.py): called as f(season, year) after a season's end-of-season
        # step, before its snapshot is archived; it must only read the season
        self.on_season_end = getattr(self, 'on_season_end', None)

    # ---- creating and opening -------------------------------------------------------------------------
    @classmethod
    def create(cls, directory, seed=2027, workers=None, world=None, development=True):
        from .population import generate_world
        from .season import Season
        d = Path(directory)
        if (d / 'CURRENT').exists():
            raise FileExistsError(f'{d} already holds a session')
        d.mkdir(parents=True, exist_ok=True)
        season = Season(world or generate_world(seed=seed), seed=seed, development=development, workers=workers)
        writer = ArchiveWriter(d / 'archive', season)
        pending = {'chunks': {}, 'world': writer.world, 'tables': writer.state_tables(season)}
        state = {'format': FORMAT, 'schema': SCHEMA, 'world_id': f'{seed}-{int(time.time())}', 'seed': seed,
                 'cursor': {'year': season.first_year, 'week': 1, 'phase': 'start'}, 'last_op': None,
                 'archive_through': None, 'archive': {'created': writer.created, 'initial': sorted(writer.initial)},
                 'weeks_played': 0, 'ops': []}
        s = cls(d, season, state, 0)
        s._pending = pending                 # the history as it begins: no seasons, everyone who exists
        s._commit()
        return s

    @classmethod
    def open(cls, directory, workers=None, allow_other_engine=False):
        """Open the committed world, recovering from an interrupted advance if there was one. Recovery
        (removing an uncommitted advance's files, publishing committed history) needs the lock: if
        another process is advancing, the committed world is opened as it is and its work left alone."""
        d = Path(directory)
        try:
            with _FileLock(d / 'lock'):
                for tmp in d.glob('gen_*.tmp'):               # an advance that never committed
                    shutil.rmtree(tmp, ignore_errors=True)
                if (d / 'CURRENT.tmp').exists():
                    (d / 'CURRENT.tmp').unlink()
                gen = _committed_generation(d)
                season, state = _load_generation(d, gen, allow_other_engine)
                s = cls(d, season, state, gen)
                s._recover_archive()
        except Busy:
            gen, season, state = _load_committed(d, allow_other_engine)
            s = cls(d, season, state, gen)
        if workers:
            s.season.workers = workers
        return s

    @property
    def cursor(self):
        return dict(self.state['cursor'])

    # ---- advancing --------------------------------------------------------------------------------------
    def advance_one_week(self, expected=None, op_key=None):
        """Play the next week (running 1 January first, or the end of the season after week 52) and commit
        the world. Returns {'completed': (year, week), 'events': [...], 'changes': {...}, 'cursor': {...},
        'generation': n}. `expected`: the cursor the caller believes is next (StaleCursor otherwise).
        `op_key`: repeating a recently committed key returns its result without simulating again."""
        return self._advance(1, expected, op_key)[0]

    def advance(self, weeks, progress=None, cancel=None, commit_every_week=False, expected=None, op_key=None):
        """Advance several weeks with the same weekly step. By default the world is committed once, at
        the end (or when `cancel()` returns true between weeks): a skip to the end of the
        season does not pay for 52 checkpoints. `commit_every_week` commits after each week instead.
        `progress(result)` after every week. `expected` and `op_key` as for advance_one_week (a
        resubmitted key returns the stored results). Returns the results."""
        if commit_every_week:
            out = []
            for _ in range(weeks):
                if cancel and cancel():
                    break
                out.append(self.advance_one_week(expected=self.cursor))
                if progress:
                    progress(out[-1])
            return out
        return self._advance(weeks, expected, op_key, progress, cancel)

    def _advance(self, weeks, expected, op_key, progress=None, cancel=None):
        with self._lock:
            with _FileLock(self.dir / 'lock'):
                # first the committed world (another process may have committed meanwhile, or recovery
                # may fall back to an earlier generation) with its history repaired; only then is an
                # operation recognised as done -- if it is still in what is committed
                self._sync()
                done = self._done(op_key)
                if done is not None:
                    return done
                if expected is not None and dict(expected) != self.state['cursor']:
                    raise StaleCursor(f'expected {expected}, the world is at {self.state["cursor"]}')
                out = []
                try:
                    for _ in range(weeks):
                        if cancel and cancel():
                            break                            # a clean stop between weeks: commit what is done
                        out.append(self._step())
                        if progress:
                            progress(out[-1])
                    if out:
                        for r in out:
                            r['generation'] = self.generation + 1
                        if op_key is not None:
                            self.state['ops'] = (self.state['ops'] + [[op_key, out]])[-OPS_KEPT:]
                        self.state['last_op'] = {'key': op_key, 'result': out[-1]}
                        self._commit()
                except BaseException:
                    # an error, an interrupt or a failed commit: go back to what is committed, so memory
                    # never runs ahead of disk (a commit that succeeded but could not publish its history
                    # is committed: reloading it is the same world, and the history is published next time)
                    self._rollback()
                    raise
                return out

    def _done(self, op_key):
        if op_key is None:
            return None
        return next((r for k, r in reversed(self.state['ops']) if k == op_key), None)

    def _sync(self):
        """Under the lock: work from the committed world, with its history published."""
        gen = _committed_generation(self.dir)
        if gen != self.generation:
            self.season.close()
            self.season, self.state = _load_generation(self.dir, gen, False)
            Session.__init__(self, self.dir, self.season, self.state, gen)
        self._recover_archive()

    def _rollback(self):
        self.season.close()
        self._pending = None
        gen = _committed_generation(self.dir)
        self.season, self.state = _load_generation(self.dir, gen, True)
        self.generation = gen
        self.state.setdefault('ops', [])

    def _step(self):
        s, c = self.season, self.state['cursor']
        year, week = c['year'], c['week']
        if c['phase'] == 'start':
            s.start_year(year)
            c['phase'] = 'week'
        before = set(s.results)
        top = s.ctx.ranking(year, week - 1)[:1] if week > 1 else []
        s.advance_week(year, week)
        events = sorted(k for k in s.results if k not in before)
        winners = {eid: s.results[eid].winner() for eid in events if s.results[eid].winner() is not None}
        now_top = s.ctx.ranking(year, week)[:1]
        changes = {'events': len(events), 'winners': winners,
                   'injuries': sum(1 for w, *_ in s.injuries.get(year, []) if w == week),
                   'number_one': now_top[0] if now_top else None,
                   'new_number_one': bool(top) and now_top != top}
        self.state['weeks_played'] += 1
        if week == 52:
            s.finish_year(year)
            if self.on_season_end:
                self.on_season_end(s, year)
            changes['season_end'] = {'career_decisions': dict(s.career_counts.get(year, {})),
                                     'juniors': s.juniors_added.get(year + 1, 0)}
            self._stage_archive(year)
            self.state['cursor'] = {'year': year + 1, 'week': 1, 'phase': 'start'}
        else:
            self.state['cursor'] = {'year': year, 'week': week + 1, 'phase': 'week'}
        return {'completed': (year, week), 'events': events, 'changes': changes, 'cursor': dict(self.state['cursor'])}

    def _stage_archive(self, year):
        """The season's history, held until the advance commits (then staged in its generation)."""
        s = self.season
        w = ArchiveWriter(self.dir / 'archive', s, touch=False)
        w.created = self.state['archive']['created']
        w.initial = set(self.state['archive']['initial'])
        p = self._pending or {'chunks': {}, 'world': w.world}
        p['chunks'][year] = w.year_chunk(s, year)
        p['tables'] = w.state_tables(s)
        p['world']['years'] = sorted(set(p['world']['years']) | {year})
        self._pending = p
        self.state['archive_through'] = year
        s.snapshots.pop(year, None)

    def _recover_archive(self):
        """Under the lock: make the published history the committed generation's. Every generation holds
        (or carries) the history it stands on and names the generation that produced it (history_gen):
        if what is published is anything else -- a crash interrupted publishing, or the committed
        generation is an earlier one because a newer one was damaged -- it is published again; then
        seasons beyond the committed generation are removed."""
        meta = _meta(self.dir, self.generation)
        h = meta.get('history_gen')
        if h is None:                                   # generations from before histories were carried
            if meta.get('archive_staged') and _published(self.dir) != self.generation:
                _publish_archive(self.dir, self.generation)
        elif _published(self.dir) != h:
            _publish_archive(self.dir, self.generation)
        self._trim_archive()

    def _trim_archive(self):
        """Seasons in the archive beyond the committed generation came from an advance that crashed before
        committing: remove them (the retry writes them again, identically)."""
        p = self.dir / 'archive' / 'world.json'
        if not p.exists():
            return
        world = json.loads(p.read_text())
        through = self.state['archive_through']
        idx_path = self.dir / 'archive' / 'index.sqlite'
        if idx_path.exists():
            from .archive_index import ArchiveIndex
            idx = ArchiveIndex(idx_path)
            idx.drop_years_after(through if through is not None else -1)
            idx.close()
        beyond = lambda y: through is None or y > through
        for f in (self.dir / 'archive' / 'years').glob('*.json.gz'):
            if beyond(int(f.name.split('.')[0])):          # listed or not (world.json may be republished)
                f.unlink()
        extra = [y for y in world.get('years', []) if beyond(y)]
        if extra:
            world['years'] = [y for y in world['years'] if y not in extra]
            p.write_text(json.dumps(world))
        if idx_path.exists() and world.get('years'):       # indexes from before the weekly No. 1 table:
            from types import SimpleNamespace               # filled once, by the archive's owner, under its lock
            idx = ArchiveIndex(idx_path)
            if not idx.derived_complete(world['years']):
                idx.backfill_derived(SimpleNamespace(years=world['years'], dir=self.dir / 'archive'))
            idx.close()

    # ---- committing ---------------------------------------------------------------------------------------
    def _commit(self):
        n = self.generation + 1 if (self.dir / 'CURRENT').exists() else 0
        name = f'gen_{n:06d}'
        tmp = self.dir / f'{name}.tmp'
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir()
        pool = self.season.__dict__.pop('_pool', None)
        try:
            with gzip.open(tmp / 'state.pkl.gz', 'wb', compresslevel=3) as f:
                pickle.dump({'season': self.season, 'state': self.state}, f, protocol=pickle.HIGHEST_PROTOCOL)
        finally:
            if pool is not None:
                self.season._pool = pool
        digest = _sha256(tmp / 'state.pkl.gz')
        staged = {}
        new_history = bool(self._pending)
        if self._pending:                                             # the season history, staged
            a = tmp / 'archive'
            (a / 'years').mkdir(parents=True)
            files = {f'years/{y}.json.gz': c for y, c in self._pending['chunks'].items()}
            files.update(self._pending['tables'])
            for f, obj in files.items():
                _write(a / f, obj)
            _write_synced(a / 'world.json', json.dumps(self._pending['world']).encode())
            staged = {f: _sha256(a / f) for f in list(files) + ['world.json']}
            history = n
        else:                                                         # carry the history it stands on
            history, staged = self._carry_history(tmp)
        meta = {'format': FORMAT, 'schema': SCHEMA, 'generation': n, 'world_id': self.state['world_id'],
                'cursor': self.state['cursor'], 'engine': engine_id(), 'commit': engine_commit(),
                'archive_through': self.state['archive_through'], 'weeks_played': self.state['weeks_played'],
                'sha256': digest, 'archive_staged': sorted(self._pending['chunks']) if self._pending else [],
                'archive_files': staged, 'history_gen': history, 'written': time.strftime('%Y-%m-%d %H:%M:%S')}
        _write_synced(tmp / 'meta.json', json.dumps(meta, indent=1).encode())
        if _sha256(tmp / 'state.pkl.gz') != digest:                    # read back: what was written is whole
            raise IOError('checkpoint did not read back intact')
        final = self.dir / name
        if final.exists():
            shutil.rmtree(final)
        os.replace(tmp, final)
        _write_synced(self.dir / 'CURRENT.tmp', json.dumps({'generation': n, 'dir': name}).encode())
        os.replace(self.dir / 'CURRENT.tmp', self.dir / 'CURRENT')     # the commit
        self.generation = n
        self._pending = None
        for old in sorted(self.dir.glob('gen_[0-9]*')):
            if old.is_dir() and not old.name.endswith('.tmp') and int(old.name[4:]) <= n - KEEP_GENERATIONS:
                shutil.rmtree(old, ignore_errors=True)
        if new_history:
            _publish_archive(self.dir, n)                               # committed: now the history shows it
            settle_heap()                                               # a season's garbage, once a season
        # (a generation that only carries the history it stands on publishes nothing: what is published
        # is already its history; recovery republishes only when PUBLISHED names another)

    def _carry_history(self, tmp):
        """A generation with no new season carries the committed generation's history files (hard links:
        no copying), so any generation can restore exactly the history it stands on."""
        prev = self.dir / f'gen_{self.generation:06d}'
        meta = _meta(self.dir, self.generation) if prev.exists() else {}
        if meta.get('history_gen') is None:
            return None, {}
        a = tmp / 'archive'
        a.mkdir()
        names = list(STATE_FILES) + ['world.json']
        for f in names:
            try:
                os.link(prev / 'archive' / f, a / f)
            except OSError:
                shutil.copyfile(prev / 'archive' / f, a / f)
        return meta['history_gen'], {f: meta['archive_files'][f] for f in names}

    def close(self):
        self.season.close()


# ---- helpers ------------------------------------------------------------------------------------------------
def _sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _write_synced(path, data):
    with open(path, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def _valid(d, name):
    g = d / name
    try:
        meta = json.loads((g / 'meta.json').read_text())
        if meta.get('format') != FORMAT or _sha256(g / 'state.pkl.gz') != meta['sha256']:
            return None
        if any(_sha256(g / 'archive' / f) != h for f, h in meta.get('archive_files', {}).items()):
            return None                                             # its staged history is damaged
        return meta
    except (OSError, ValueError, KeyError):
        return None


def _meta(d, n):
    try:
        return json.loads((d / f'gen_{n:06d}' / 'meta.json').read_text())
    except (OSError, ValueError):
        return {}


def _published(d):
    try:
        return int((d / 'archive' / 'PUBLISHED').read_text())
    except (OSError, ValueError):
        return None


def _copy_atomic(src, dst):
    tmp = dst.with_name(dst.name + '.tmp')
    shutil.copyfile(src, tmp)
    with open(tmp, 'rb') as f:
        os.fsync(f.fileno())
    os.replace(tmp, dst)


def _publish_archive(d, n):
    """Publish a committed generation's staged season history to the archive (idempotent): season
    files and their index rows, the people, relationships and records tables, then the list of seasons
    (readers see the new seasons only once everything they refer to is in place), then PUBLISHED."""
    g = d / f'gen_{n:06d}'
    meta = json.loads((g / 'meta.json').read_text())
    a = d / 'archive'
    (a / 'years').mkdir(parents=True, exist_ok=True)
    for y in meta['archive_staged']:
        f = f'years/{y}.json.gz'
        _copy_atomic(g / 'archive' / f, a / f)
        index_season(a, y, _read(a / f))
    for name in STATE_FILES:
        _copy_atomic(g / 'archive' / name, a / name)
    _copy_atomic(g / 'archive' / 'world.json', a / 'world.json')
    h = meta.get('history_gen')
    _write_synced(a / 'PUBLISHED.tmp', str(n if h is None else h).encode())
    os.replace(a / 'PUBLISHED.tmp', a / 'PUBLISHED')


def _committed_generation(d):
    """The generation CURRENT points at; if that is unreadable, the newest intact generation (the last
    known good one)."""
    try:
        cur = json.loads((d / 'CURRENT').read_text())
        if _valid(d, cur['dir']):
            return cur['generation']
    except (OSError, ValueError, KeyError):
        pass
    gens = sorted((int(p.name[4:]) for p in d.glob('gen_[0-9]*') if p.is_dir() and not p.name.endswith('.tmp')),
                  reverse=True)
    for n in gens:
        if _valid(d, f'gen_{n:06d}'):
            return n
    raise FileNotFoundError(f'no intact checkpoint generation in {d}')


def _load_committed(d, allow_other_engine, attempts=5):
    """The committed world, read without the lock (another process may be committing: a generation can
    be replaced while it is read, so try again)."""
    for i in range(attempts):
        try:
            gen = _committed_generation(d)
            season, state = _load_generation(d, gen, allow_other_engine)
            return gen, season, state
        except (OSError, EOFError, pickle.UnpicklingError):
            if i == attempts - 1:
                raise
            time.sleep(0.2 * (i + 1))


def _load_generation(d, n, allow_other_engine):
    name = f'gen_{n:06d}'
    meta = _valid(d, name)
    if meta is None:
        raise IOError(f'{d / name} is not an intact checkpoint')
    if not allow_other_engine and meta['engine'] != engine_id():
        raise ValueError(f'world saved by engine {meta["engine"]} (commit {meta["commit"]}); this engine is {engine_id()}')
    with gzip.open(d / name / 'state.pkl.gz', 'rb') as f:
        gc.disable()                                    # millions of objects: no collections while loading
        try:
            blob = pickle.load(f)
        finally:
            gc.enable()
    settle_heap()
    return blob['season'], blob['state']


def settle_heap():
    """Collect once, then leave the long-lived world out of the cyclic collector's full passes
    (`gc.freeze`): a full collection over a multi-gigabyte world took seconds and found nothing. Done on
    loading and after each archived season (objects frozen then and later dropped wait until the next
    one). Performance only: no simulated value depends on it."""
    gc.unfreeze()
    gc.collect()
    gc.freeze()


def _lock_owner():
    """What a lock file holds: the advancing process's id and host."""
    return f'{os.getpid()} {socket.gethostname()}'


def _owner_gone(text):
    """True only when the lock's owner certainly no longer runs: same host, POSIX, no such process.
    (Elsewhere, or on Windows, a lock is never taken over.)"""
    if os.name != 'posix':
        return False
    parts = text.split()
    try:
        pid = int(parts[0])
    except (IndexError, ValueError):
        return False
    if len(parts) > 1 and parts[1] != socket.gethostname():
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False                                  # it exists (another user's process)
    return False


class _FileLock:
    """A lock file created exclusively (works on Windows and POSIX); Busy if it is held. A lock left by
    a process that has died (POSIX, same host) is taken over: it is renamed aside first, and given back
    if it turns out to belong to a live advance after all."""

    def __init__(self, path):
        self.path = Path(path)

    def __enter__(self):
        for attempt in range(2):
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError:
                try:
                    text = self.path.read_text()
                except FileNotFoundError:
                    continue                          # released meanwhile: try again
                if attempt or not _owner_gone(text):
                    raise Busy(f'{self.path} is held by another advance (process {text.strip()})') from None
                aside = self.path.with_name(f'{self.path.name}.stale.{os.getpid()}')
                try:
                    os.rename(self.path, aside)
                except FileNotFoundError:
                    continue
                if aside.read_text() != text:         # not the dead owner's lock: give it back
                    os.rename(aside, self.path)
                    raise Busy(f'{self.path} is held by another advance') from None
                aside.unlink()
        else:
            raise Busy(f'{self.path} is held by another advance') from None
        os.write(fd, _lock_owner().encode())
        os.close(fd)
        return self

    def __exit__(self, *exc):
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
