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
published to archive/: each file under a name carrying the generation that produced it, never rewritten,
then the index rows (each season's recorded with the file it came from), then one manifest
(archive/MANIFEST.json) naming exactly those files, replaced atomically -- the moment readers see the new
history, whole. A crash before the commit leaves the archive exactly as it was; a publisher stopped at any
step after it leaves readers the previous manifest's history, whole, and is repaired by publishing the
committed generation's history again (on opening, before the next advance, or when a committed operation
is retried). A generation with no new season carries the history it stands on (hard links to the files of
the generation before it) and every generation names the one that produced that history (history_gen; the
manifest names the one published). So when a damaged generation makes an earlier one current, the earlier
one's own history -- seasons, people, relationships and records -- is published as a new manifest and the
later seasons leave the index. An archive from before manifests is migrated by the first session that
owns it (its files adopted as they are). So the running world, the committed checkpoint and the visible history always agree. The live simulation keeps only recent seasons (Season.prune_history), so
a checkpoint does not carry the whole history.
"""
from __future__ import annotations

import contextlib
import gc
import gzip
import hashlib
import json
import os
import pickle
import re
import shutil
import socket
import threading
import time
from pathlib import Path

from .archive import (LEGACY_FILES, MANIFEST, MANIFEST_FORMAT, STATE_FILES, ArchiveWriter, GzipChunks, _read, _write,
                      legacy_files, parse_manifest, read_manifest)
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
    def create(cls, directory, seed=2027, workers=None, world=None, development=True, calendar=None):
        from .population import generate_world
        from .season import Season
        d = Path(directory)
        if (d / 'CURRENT').exists():
            raise FileExistsError(f'{d} already holds a session')
        d.mkdir(parents=True, exist_ok=True)
        season = Season(world or generate_world(seed=seed), seed=seed, development=development, workers=workers,
                        calendar=calendar)               # (None: the default for new worlds, schedule.DEFAULT)
        writer = ArchiveWriter(d / 'archive', season, touch=False)   # published with the first commit
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
        s.allow_other_engine = allow_other_engine
        if workers:
            s.season.workers = workers
        return s

    # ---- following other processes ------------------------------------------------------------------------
    def committed(self):
        """(generation, history generation) of the world committed on disk now (two small files)."""
        gen = _committed_generation(self.dir)
        h = _meta(self.dir, gen).get('history_gen')
        return gen, (gen if h is None else h)

    @property
    def history_generation(self):
        h = _meta(self.dir, self.generation).get('history_gen')
        return self.generation if h is None else h

    def refresh(self):
        """Bring this session to the world committed on disk, if another process committed since, together
        with its history: the committed world is loaded as committed (nothing is simulated or replayed).
        When the lock is free this is the same as starting an advance (`_sync`: a publication someone left
        unfinished is completed). When another process holds it, the committed world is taken only if its
        history is already published; otherwise nothing changes. Returns True when this session now holds
        the committed world with its history published."""
        gen, h = self.committed()
        if gen == self.generation and _published(self.dir) == h:
            return True
        try:
            with self._lock, _FileLock(self.dir / 'lock'):
                self._sync()
            return True
        except Busy:
            if _published(self.dir) != h:
                return False                            # being published by its owner: not yet
            if gen != self.generation:
                workers = self.season.workers
                gen, season, state = _load_committed(self.dir, getattr(self, 'allow_other_engine', False))
                self.season.close()
                Session.__init__(self, self.dir, season, state, gen)
                self.season.workers = workers
            return True

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
                    with _collector_paused():
                        for _ in range(weeks):
                            if cancel and cancel():
                                break                        # a clean stop between weeks: commit what is done
                            out.append(self._step())
                            if progress:
                                progress(out[-1])
                    if out:
                        n = _next_generation(self.dir, self.generation)
                        for r in out:
                            r['generation'] = n
                        if op_key is not None:
                            self.state['ops'] = (self.state['ops'] + [[op_key, out]])[-OPS_KEPT:]
                        self.state['last_op'] = {'key': op_key, 'result': out[-1]}
                        self._commit(n)
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
            workers = self.season.workers
            self.season.close()
            self.season, self.state = _load_generation(self.dir, gen, getattr(self, 'allow_other_engine', False))
            self.season.workers = workers                 # this process's choice, not the saved one
            Session.__init__(self, self.dir, self.season, self.state, gen)
        self._recover_archive()

    def _rollback(self):
        workers = self.season.workers
        self.season.close()
        self._pending = None
        gen = _committed_generation(self.dir)
        self.season, self.state = _load_generation(self.dir, gen, True)
        self.season.workers = workers                     # this process's choice, not the saved one
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

    def _history_years(self):
        """The archived seasons of the committed generation's history (from its staged or carried world
        table; an older generation without one: the published history's)."""
        p = self.dir / f'gen_{self.generation:06d}' / 'archive' / 'world.json'
        if p.exists():
            return json.loads(p.read_text())['years']
        m = read_manifest(self.dir / 'archive')
        return list(m['years']) if m is not None else sorted(legacy_files(self.dir / 'archive')['years'])

    def _stage_archive(self, year):
        """The season's history, held until the advance commits (then staged in its generation)."""
        s = self.season
        w = ArchiveWriter(self.dir / 'archive', s, touch=False)
        w.created = self.state['archive']['created']
        w.initial = set(self.state['archive']['initial'])
        if not self._pending:                       # the seasons of the history this world stands on
            w.world['years'] = self._history_years()
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
        if the manifest names anything else -- publication stopped part way, the committed generation is
        an earlier one because a newer one was damaged, or the archive predates manifests -- the committed
        generation's history is published (a new manifest; nothing already published is rewritten). Index
        tables added by later versions are then filled in, and files no manifest needs are removed."""
        a = self.dir / 'archive'
        meta = _meta(self.dir, self.generation)
        h = meta.get('history_gen')
        published = _published(self.dir)
        g = self.dir / f'gen_{self.generation:06d}' / 'archive'
        has_history = (g / 'world.json').exists() or (a / MANIFEST).exists() or (a / 'world.json').exists()
        if has_history and (not (a / MANIFEST).exists() or published != (self.generation if h is None else h)):
            _publish_archive(self.dir, self.generation)
        m = read_manifest(a)
        if m is not None and (a / 'index.sqlite').exists():
            from types import SimpleNamespace
            from .archive_index import ArchiveIndex
            with ArchiveIndex(a / 'index.sqlite') as idx:
                if set(idx.years()) - set(m['years']):  # rows of no published season (never visible: bounded)
                    idx.drop_years_after(m['years'][-1] if m['years'] else -1)
                # indexes from before the weekly No. 1 table: filled once, by the archive's owner, under its lock
                if m['years'] and not idx.derived_complete(m['years']):
                    idx.backfill_derived(SimpleNamespace(years=m['years'],
                                                         year_path=lambda y: a / m['files']['years'][y]))
        _collect_unpublished(a)

    # ---- committing ---------------------------------------------------------------------------------------
    def _commit(self, n=None):
        if n is None:
            n = _next_generation(self.dir, self.generation) if (self.dir / 'CURRENT').exists() else 0
        name = f'gen_{n:06d}'
        tmp = self.dir / f'{name}.tmp'
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir()
        pool = self.season.__dict__.pop('_pool', None)
        try:
            with GzipChunks(tmp / 'state.pkl.gz', 3) as f:     # compressed on threads while it is pickled
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
        _replace(tmp, final)                                            # (Windows: retried while a scanner holds it)
        _write_synced(self.dir / 'CURRENT.tmp', json.dumps({'generation': n, 'dir': name}).encode())
        _replace(self.dir / 'CURRENT.tmp', self.dir / 'CURRENT')       # the commit
        keep = {n, self.generation}                                     # and the last known good one
        self.generation = n
        self._pending = None
        for old in sorted(self.dir.glob('gen_[0-9]*')):                 # (and any damaged or abandoned)
            if old.is_dir() and not old.name.endswith('.tmp') and int(old.name[4:]) not in keep:
                shutil.rmtree(old, ignore_errors=True)
        if new_history:
            _publish_archive(self.dir, n)                               # committed: now the history shows it
            settle_heap(full=True)                                      # a season's garbage, once a season
        # (a generation that only carries the history it stands on publishes nothing: what is published
        # is already its history; recovery publishes again only when the manifest names another)

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
    """The generation whose history is published (the manifest's; PUBLISHED before manifests)."""
    try:
        m = read_manifest(d / 'archive')
        if m is not None:
            return m['generation']
        return int((d / 'archive' / 'PUBLISHED').read_text())
    except (OSError, ValueError, KeyError):
        return None


def _copy_synced(src, tmp):
    """Copy src to tmp and force the copy to disk through the handle that wrote it (Windows refuses to
    flush a file opened only for reading -- EBADF, "Bad file descriptor" -- which POSIX allows)."""
    with open(src, 'rb') as r, open(tmp, 'wb') as w:
        shutil.copyfileobj(r, w, 1 << 20)
        w.flush()
        os.fsync(w.fileno())


def _replace(src, dst, attempts=20):
    """os.replace, retried briefly on Windows, where replacing a file fails while another process (a
    reader of the old manifest, say) has it open; elsewhere, and after the retries, the error stands."""
    for i in range(attempts):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if os.name != 'nt' or i == attempts - 1:
                raise
            time.sleep(0.05 * (i + 1))


def _copy_atomic(src, dst):
    tmp = dst.with_name(dst.name + '.tmp')
    _copy_synced(src, tmp)
    _replace(tmp, dst)


def _publication_step(name):
    """Called between the steps of a publication (fault-injection tests stop a publisher here)."""


def _place(src, dst):
    """Put a published file in place, atomically, never changing one that exists: a hard link to the
    staged file where the file system allows (no copying), else a synced copy."""
    if dst.exists():
        return
    tmp = dst.with_name(dst.name + '.tmp')
    if tmp.exists():
        tmp.unlink()
    try:
        os.link(src, tmp)
    except OSError:
        _copy_synced(src, tmp)
    _replace(tmp, dst)


def _publish_archive(d, n):
    """Publish committed generation n's history as one new manifest (idempotent).

    1. each season file n staged, under a name carrying n (years/YYYY.gNNNNNN.json.gz);
    2. the index: those seasons' rows, each recorded with the file it came from, and any season whose
       recorded file is not the one published;
    3. the world, people, relationships and records tables of the history n stands on, under names
       carrying the generation that produced it (history_gen);
    4. the manifest, replaced atomically: only now do readers see the new history, whole;
    5. index rows of seasons no longer published (a rollback) are dropped, and files that neither this
       manifest nor the previous one names are removed.

    Nothing a manifest names is ever rewritten, so a publisher stopped at any step leaves readers the
    previous history, whole, and the next session to open the world publishes again. Seasons n did not
    stage keep the files already published for them (an archive from before manifests: its files as they
    are -- its index rows were indexed from exactly those files)."""
    from .archive_index import ArchiveIndex
    g = d / f'gen_{n:06d}'
    meta = json.loads((g / 'meta.json').read_text())
    h = meta.get('history_gen')
    h = n if h is None else h
    a = d / 'archive'
    (a / 'years').mkdir(parents=True, exist_ok=True)
    src = g / 'archive'
    old = read_manifest(a)
    legacy = old is None
    base = legacy_files(a) if legacy else old['files']
    world_src = src / 'world.json' if (src / 'world.json').exists() else a / base['world']
    years = sorted(json.loads(world_src.read_text())['years'])
    files = {'years': {}}
    for y in years:
        if y in meta.get('archive_staged', []):
            files['years'][y] = f'years/{y}.g{n:06d}.json.gz'
            _place(src / f'years/{y}.json.gz', a / files['years'][y])
        else:
            files['years'][y] = _published_season(a, y, h, base)
    _publication_step('season files')
    with ArchiveIndex(a / 'index.sqlite') as idx:
        if legacy:
            idx.adopt_sources({y: f for y, f in files['years'].items() if f == base['years'].get(y)})
        sources = idx.sources()
        for y in years:
            if sources.get(y) != files['years'][y]:
                idx.index_year(y, _read(a / files['years'][y]), source=files['years'][y])
                _publication_step('index')
    _publication_step('index done')
    stem = {'world': ('world', '.json'), 'people': ('people', '.json.gz'), 'relations': ('relations', '.json.gz'),
            'records': ('records', '.json.gz')}
    for key, (name, ext) in stem.items():
        files[key] = f'{name}.g{h:06d}{ext}'
        staged = src / LEGACY_FILES[key]
        _place(staged if staged.exists() else a / base[key], a / files[key])
    _publication_step('tables')
    manifest = {'format': MANIFEST_FORMAT, 'generation': h, 'published_by': n, 'years': years,
                'files': {**files, 'years': {str(y): f for y, f in files['years'].items()}}}
    if (a / MANIFEST).exists():
        _copy_atomic(a / MANIFEST, a / 'MANIFEST.prev.json')       # its files stay for readers opening it
    _write_synced(a / 'MANIFEST.tmp', json.dumps(manifest, indent=1).encode())
    _replace(a / 'MANIFEST.tmp', a / MANIFEST)                      # the publication
    _publication_step('manifest')
    with ArchiveIndex(a / 'index.sqlite') as idx:                   # rows of seasons no longer published
        if set(idx.years()) - set(years):                           # (a rollback): readers of the previous
            idx.drop_years_after(years[-1] if years else -1)        # manifest kept them until now
    _collect_unpublished(a)


def _published_season(a, y, h, base):
    """The published file of season y in the history of generation h: the one the manifest names if a
    generation no later than h produced it; else (a manifest lost or from a later, rolled-back generation)
    the latest file of season y produced by a generation no later than h; else the file of an archive from
    before manifests."""
    def gen_of(name):
        m = re.search(r'\.g(\d{6})\.json\.gz$', name)
        return int(m.group(1)) if m else -1
    named = base['years'].get(y)
    if named and (a / named).exists() and gen_of(named) <= h:
        return named
    found = sorted(((gen_of(p.name), p.name) for p in (a / 'years').glob(f'{y}.g*.json.gz') if gen_of(p.name) <= h))
    if found:
        return f'years/{found[-1][1]}'
    if (a / 'years' / f'{y}.json.gz').exists():
        return f'years/{y}.json.gz'
    raise IOError(f'season {y} of history generation {h} is neither staged nor published')


def _collect_unpublished(a):
    """Remove what no manifest needs: files neither the manifest nor the previous one names (the previous
    one's stay for a reader that read it just before), files of an archive from before manifests, and
    partial files. Never the index, the manifests or the lock."""
    m = read_manifest(a)
    if m is None:
        return
    keep = set()
    for path in (a / MANIFEST, a / 'MANIFEST.prev.json'):
        try:
            mm = parse_manifest(path.read_text())
        except (FileNotFoundError, ValueError):
            continue
        keep |= {f for k, f in mm['files'].items() if k != 'years'} | set(mm['files']['years'].values())
    for p in list(a.glob('*')) + list((a / 'years').glob('*')):
        rel = p.relative_to(a).as_posix()
        if p.is_dir() or rel in keep or rel.startswith(('index.sqlite', 'MANIFEST', 'lock')):
            continue
        if rel.endswith(('.json', '.json.gz', '.tmp')) or rel in ('PUBLISHED',):
            try:
                p.unlink()
            except OSError:                             # still open somewhere (Windows): removed next time
                pass


def _next_generation(d, current):
    """The number of the next generation: above every generation this world has ever used, not merely
    above the committed one. After a damaged generation made an earlier one current, the abandoned number
    is never given to different content -- not to a checkpoint, nor to the published files named after it
    (which readers and the index identify by name), nor to a live observer still holding the abandoned
    world. Evidence of a number lasts as long as anything can refer to it: CURRENT (it still names the
    abandoned generation until this commit replaces it), generation directories, the manifests, and the
    published files' names."""
    used = [current]
    try:
        used.append(int(json.loads((d / 'CURRENT').read_text())['generation']))
    except (OSError, ValueError, KeyError, TypeError):
        pass
    for p in d.glob('gen_[0-9]*'):
        m = re.match(r'gen_(\d+)', p.name)
        if m:
            used.append(int(m.group(1)))
    a = d / 'archive'
    for name in (MANIFEST, 'MANIFEST.prev.json'):
        try:
            m = json.loads((a / name).read_text())
            used += [int(m['generation']), int(m.get('published_by', m['generation']))]
        except (OSError, ValueError, KeyError, TypeError):
            pass
    for p in list(a.glob('*.g[0-9]*')) + list((a / 'years').glob('*.g[0-9]*')):
        m = re.search(r'\.g(\d{6})', p.name)
        if m:
            used.append(int(m.group(1)))
    return max(used) + 1


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


@contextlib.contextmanager
def _collector_paused():
    """The cyclic garbage collector paused while weeks are simulated (restored however they end). It
    cost about 17 s a season on the 50-season world (young collections over a high allocation rate, and
    full ones), and full collections found no garbage: the simulation's garbage is acyclic, freed by
    reference counting as before. Cycles are collected at the season end (settle_heap) or by the next
    ordinary collection. Performance only: no simulated value depends on when the collector runs."""
    was = gc.isenabled()
    gc.disable()
    try:
        yield
    finally:
        if was:
            gc.enable()


def settle_heap(full=False):
    """Keep the long-lived world out of the cyclic collector's full passes (`gc.freeze`): without it,
    full collections over the 50-season world (3.5 GB) took about 3 s of every 8 weeks and found no
    garbage. Balanced, not cumulative: everything frozen before is unfrozen first, and collected once
    (about 1 s on that world) whenever anything had been frozen, so nothing dropped since -- a replaced
    observer snapshot, a world reloaded after a failed advance -- stays out of the collector's reach. A
    first load in a fresh process holds no garbage and is simply frozen. Performance only: no simulated
    value depends on it."""
    had_frozen = gc.get_freeze_count() > 0
    gc.unfreeze()
    if full or had_frozen:
        gc.collect()
    gc.freeze()


def _lock_owner():
    """What a lock file holds: the advancing process's id and host."""
    return f'{os.getpid()} {socket.gethostname()}'


def _owner_gone(text):
    """True only when the lock's owner certainly no longer runs: same host and no such process (POSIX:
    signal 0; Windows: the process cannot be opened, or has exited). A lock from another host, or one
    whose owner cannot be checked, is never taken over."""
    parts = text.split()
    try:
        pid = int(parts[0])
    except (IndexError, ValueError):
        return False
    if len(parts) > 1 and parts[1] != socket.gethostname():
        return False
    if os.name == 'nt':
        return _windows_process_gone(pid)
    if os.name != 'posix':
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False                                  # it exists (another user's process)
    return False


def _windows_process_gone(pid):
    """Windows: True only if no process with this id is running (it cannot be opened because it does not
    exist, or it has exited). Never signals the process (os.kill would terminate it on Windows)."""
    try:
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL('kernel32', use_last_error=True)
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        h = k32.OpenProcess(0x1000, False, pid)          # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return ctypes.get_last_error() == 87          # ERROR_INVALID_PARAMETER: no such process
        try:
            code = wintypes.DWORD()
            if not k32.GetExitCodeProcess(h, ctypes.byref(code)):
                return False
            return code.value != 259                      # STILL_ACTIVE
        finally:
            k32.CloseHandle(h)
    except Exception:
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
