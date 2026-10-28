"""The weekly session: the one way an observer advances a world (roadmap M1).

    s = Session.create('worlds/my_world', seed=2027)      # a new world, committed at its first week
    s = Session.open('worlds/my_world')                   # or reopen one (recovering if needed)
    r = s.advance_one_week(expected=s.cursor)             # play the next week and commit it
    s.advance(52)                                         # longer advances repeat the same command

**The cursor** says exactly what happens next: `{'year', 'week', 'phase'}` with phase 'start' (1 January
has not run yet: the next advance runs it, then week 1), or 'week' (the next advance plays that week).
After week 52 the same advance runs the end of the season and archives it, and the cursor moves to the
next year's 'start'. Year start and year end therefore run exactly once, in order, whatever the calls.

**Idempotent, serialised advances.** An advance may name the cursor it expects (a stale request is
refused with StaleCursor and changes nothing) and an operation key (repeating the last committed key
returns its stored result without simulating again). Advances are serialised: a lock inside the process,
and a lock file across processes (Busy if another advance holds it).

**One coherent world per generation.** Each advance writes a new checkpoint generation: the whole
simulation and the session's state go to a temporary directory, are hashed and read back, the
directory is renamed into place and only then is the CURRENT pointer replaced (an atomic rename). A
crash before that leaves the previous generation current; after it, the new one. The previous generation
is kept as the last known good one; older ones and orphaned temporary directories are removed. The
history archive (archive.py) is written only at season end, by the advance that commits that season;
the committed generation records which seasons the archive holds, and opening a session removes any
archived season beyond it (written by an advance that crashed before committing; the retry rewrites it
identically). The live simulation keeps only recent seasons (Season.prune_history), so a checkpoint
does not carry the whole history.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import pickle
import shutil
import threading
import time
from pathlib import Path

from .archive import ArchiveWriter
from .savegame import engine_commit, engine_id

FORMAT = 'golf-legacy-session/1'
SCHEMA = 1
KEEP_GENERATIONS = 2                 # the current generation and the last known good one before it


class StaleCursor(Exception):
    """The request expected a different cursor: the world has moved on (or not yet reached it)."""


class Busy(Exception):
    """Another advance holds the session's lock."""


class Session:
    def __init__(self, directory, season, state, generation):
        self.dir = Path(directory)
        self.season = season
        self.state = state                 # cursor, last operation, archive writer state, world id
        self.generation = generation
        self._lock = threading.Lock()

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
        state = {'format': FORMAT, 'schema': SCHEMA, 'world_id': f'{seed}-{int(time.time())}', 'seed': seed,
                 'cursor': {'year': season.first_year, 'week': 1, 'phase': 'start'}, 'last_op': None,
                 'archive_through': None, 'archive': {'created': writer.created, 'initial': sorted(writer.initial)},
                 'weeks_played': 0}
        s = cls(d, season, state, 0)
        s._commit()
        return s

    @classmethod
    def open(cls, directory, workers=None, allow_other_engine=False):
        """Open the committed world, recovering from an interrupted advance if there was one."""
        d = Path(directory)
        for tmp in d.glob('gen_*.tmp'):                       # an advance that never committed
            shutil.rmtree(tmp, ignore_errors=True)
        for stray in (d / 'CURRENT.tmp',):
            if stray.exists():
                stray.unlink()
        gen = _committed_generation(d)
        season, state = _load_generation(d, gen, allow_other_engine)
        if workers:
            season.workers = workers
        s = cls(d, season, state, gen)
        s._trim_archive()
        return s

    @property
    def cursor(self):
        return dict(self.state['cursor'])

    # ---- advancing --------------------------------------------------------------------------------------
    def advance_one_week(self, expected=None, op_key=None):
        """Play the next week (running 1 January first, or the end of the season after week 52) and commit
        the world. Returns {'completed': (year, week), 'events': [...], 'changes': {...}, 'cursor': {...},
        'generation': n}. `expected`: the cursor the caller believes is next (StaleCursor otherwise).
        `op_key`: repeating the last committed key returns its result without simulating again."""
        with self._lock:
            last = self.state['last_op']
            if op_key is not None and last and last['key'] == op_key:
                return last['result']
            if expected is not None and dict(expected) != self.state['cursor']:
                raise StaleCursor(f'expected {expected}, the world is at {self.state["cursor"]}')
            with _FileLock(self.dir / 'lock'):
                # another process may have advanced and committed meanwhile: work from what is committed
                gen = _committed_generation(self.dir)
                if gen != self.generation:
                    self.season, self.state = _load_generation(self.dir, gen, False)
                    self.generation = gen
                    if expected is not None and dict(expected) != self.state['cursor']:
                        raise StaleCursor(f'expected {expected}, the world is at {self.state["cursor"]}')
                try:
                    result = self._step()
                    self.state['last_op'] = {'key': op_key, 'result': result}
                    self._commit()
                except BaseException:
                    # nothing was committed: go back to the committed world, so memory never runs ahead of disk
                    self.season.close()
                    self.season, self.state = _load_generation(self.dir, _committed_generation(self.dir), True)
                    self.generation = _committed_generation(self.dir)
                    raise
                result['generation'] = self.generation
                return result

    def advance(self, weeks, progress=None, cancel=None):
        """Advance several weeks with the same weekly command (committing after each). `progress(result)`
        after every week; `cancel()` is checked between weeks. Returns the results."""
        out = []
        for _ in range(weeks):
            if cancel and cancel():
                break
            out.append(self.advance_one_week(expected=self.cursor))
            if progress:
                progress(out[-1])
        return out

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
            changes['season_end'] = {'career_decisions': dict(s.career_counts.get(year, {})),
                                     'juniors': s.juniors_added.get(year + 1, 0)}
            self._archive_year(year)
            self.state['cursor'] = {'year': year + 1, 'week': 1, 'phase': 'start'}
        else:
            self.state['cursor'] = {'year': year, 'week': week + 1, 'phase': 'week'}
        return {'completed': (year, week), 'events': events, 'changes': changes, 'cursor': dict(self.state['cursor'])}

    def _archive_year(self, year):
        s = self.season
        w = ArchiveWriter(self.dir / 'archive', s)
        w.created = self.state['archive']['created']
        w.initial = set(self.state['archive']['initial'])
        w.write_year(s, year)
        w.write_state(s)
        self.state['archive']['created'] = w.created
        self.state['archive_through'] = year
        s.snapshots.pop(year, None)

    def _trim_archive(self):
        """Seasons in the archive beyond the committed generation came from an advance that crashed before
        committing: remove them (the retry writes them again, identically)."""
        p = self.dir / 'archive' / 'world.json'
        if not p.exists():
            return
        world = json.loads(p.read_text())
        through = self.state['archive_through']
        extra = [y for y in world.get('years', []) if through is None or y > through]
        if extra:
            for y in extra:
                f = self.dir / 'archive' / 'years' / f'{y}.json.gz'
                if f.exists():
                    f.unlink()
            world['years'] = [y for y in world['years'] if y not in extra]
            p.write_text(json.dumps(world))

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
        meta = {'format': FORMAT, 'schema': SCHEMA, 'generation': n, 'world_id': self.state['world_id'],
                'cursor': self.state['cursor'], 'engine': engine_id(), 'commit': engine_commit(),
                'archive_through': self.state['archive_through'], 'weeks_played': self.state['weeks_played'],
                'sha256': digest, 'written': time.strftime('%Y-%m-%d %H:%M:%S')}
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
        for old in sorted(self.dir.glob('gen_[0-9]*')):
            if old.is_dir() and not old.name.endswith('.tmp') and int(old.name[4:]) <= n - KEEP_GENERATIONS:
                shutil.rmtree(old, ignore_errors=True)

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
        return meta if meta.get('format') == FORMAT and _sha256(g / 'state.pkl.gz') == meta['sha256'] else None
    except (OSError, ValueError, KeyError):
        return None


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


def _load_generation(d, n, allow_other_engine):
    name = f'gen_{n:06d}'
    meta = _valid(d, name)
    if meta is None:
        raise IOError(f'{d / name} is not an intact checkpoint')
    if not allow_other_engine and meta['engine'] != engine_id():
        raise ValueError(f'world saved by engine {meta["engine"]} (commit {meta["commit"]}); this engine is {engine_id()}')
    with gzip.open(d / name / 'state.pkl.gz', 'rb') as f:
        blob = pickle.load(f)
    return blob['season'], blob['state']


class _FileLock:
    """A lock file created exclusively (works on Windows and POSIX); Busy if it already exists."""

    def __init__(self, path):
        self.path = Path(path)

    def __enter__(self):
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise Busy(f'{self.path} is held by another advance (remove it if no advance is running)') from None
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return self

    def __exit__(self, *exc):
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
