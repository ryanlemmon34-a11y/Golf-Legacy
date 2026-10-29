"""The observer's long operations (advance, create, open, copy, export), one at a time, in the background.

A job runs in its own thread; the pages keep being drawn meanwhile (from the committed snapshot, never
from the world being advanced) and `/api/status` reports its progress. Only one job runs at a time: a
second request while one runs is refused, except a repeat of the running request (same operation key:
a double click, a retry, a reconnect), which is simply shown the running job.

A stop request is honoured at the next safe boundary: an advance finishes the week it is playing,
commits every completed week, and reports the last committed week. A job that fails reports its error and
leaves the world at its last committed state (the session goes back to it before reporting), and the
error with its traceback goes to the world's log.

Each advance is recorded in the world's folder while it runs (observer_job.json). If the observer stops
during an advance (closed window, crash, power loss), nothing of that advance was committed unless it
finished; the next time the world is opened the record is found, reported ("did not finish: the world is
at its last committed week ..."), and removed.

Everything that touches the history snapshot or its SQLite index runs on one thread (`Renderer`):
SQLite connections belong to the thread that opened them, and pages are drawn one at a time.
"""
from __future__ import annotations

import json
import os
import queue
import threading
import time
import traceback
import uuid
from pathlib import Path

JOB_FILE = 'observer_job.json'
LOG_FILE = 'observer.log'


def log(directory, text):
    """Append to a world's log (the diagnostic package includes it)."""
    if directory is None:
        return
    try:
        with open(Path(directory) / LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} {text}\n')
    except OSError:
        pass


class Job:
    def __init__(self, kind, title, op_key=None, world_dir=None, cancellable=False):
        self.id = uuid.uuid4().hex[:12]
        self.kind, self.title, self.op_key = kind, title, op_key
        self.world_dir = Path(world_dir) if world_dir else None
        self.cancellable = cancellable
        self.state = 'running'                 # running / done / stopped / failed / refused
        self.message = ''
        self.phase = 'starting'
        self.done, self.total = 0, None
        self.last = None                       # (year, week) last completed
        self.started, self.finished = time.time(), None
        self.cancel_requested = False
        self.seasons, self.season = None, None   # a multi-season advance: how many, which one now
        self.result = None
        self._lock = threading.Lock()

    def update(self, **kw):
        with self._lock:
            self.__dict__.update(kw)

    def finish(self, state, message):
        with self._lock:
            self.state, self.message, self.finished = state, message, time.time()
            self.phase = state

    def as_dict(self):
        with self._lock:
            elapsed = (self.finished or time.time()) - self.started
            return {'id': self.id, 'kind': self.kind, 'title': self.title, 'state': self.state,
                    'message': self.message, 'phase': self.phase, 'done': self.done, 'total': self.total,
                    'last': list(self.last) if self.last else None, 'elapsed': round(elapsed, 1),
                    'cancellable': self.cancellable and self.state == 'running',
                    'cancel_requested': self.cancel_requested, 'op': self.op_key,
                    'seasons': self.seasons, 'season': self.season}


class Jobs:
    """At most one running job for the whole observer."""

    def __init__(self):
        self.current = None
        self._lock = threading.Lock()

    def running(self):
        j = self.current
        return j if j is not None and j.state == 'running' else None

    def start(self, job, fn):
        """Run fn(job) in the background. Returns (job, True) if started; (the running job, False) if
        one is already running (the same op key: the request is a repeat of it)."""
        with self._lock:
            run = self.running()
            if run is not None:
                return run, False
            self.current = job
        t = threading.Thread(target=self._run, args=(job, fn), name=f'job-{job.kind}', daemon=True)
        job.thread = t
        t.start()
        return job, True

    def _run(self, job, fn):
        log(job.world_dir, f'job {job.id} {job.kind} started: {job.title}')
        try:
            fn(job)
            if job.state == 'running':
                job.finish('done', job.message or 'Finished.')
        except Exception as e:
            log(job.world_dir, f'job {job.id} {job.kind} FAILED: {e!r}\n{traceback.format_exc()}')
            job.finish('failed', f'{type(e).__name__}: {e}')
        log(job.world_dir, f'job {job.id} {job.kind} {job.state}: {job.message}')

    def cancel(self, job_id):
        j = self.running()
        if j is not None and j.id == job_id and j.cancellable:
            j.update(cancel_requested=True, phase='stopping at the end of this week')
            return True
        return False

    def wait(self, timeout=None):
        j = self.current
        t = getattr(j, 'thread', None)
        if t is not None:
            t.join(timeout)


def record_job(world_dir, job, cursor, generation):
    """The advance being run, recorded in the world's folder until it ends."""
    data = {'id': job.id, 'kind': job.kind, 'title': job.title, 'op': job.op_key, 'pid': os.getpid(),
            'started': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(job.started)),
            'cursor_before': cursor, 'generation_before': generation}
    tmp = Path(world_dir) / (JOB_FILE + '.tmp')
    tmp.write_text(json.dumps(data, indent=1))
    os.replace(tmp, Path(world_dir) / JOB_FILE)


def clear_job(world_dir):
    try:
        (Path(world_dir) / JOB_FILE).unlink()
    except FileNotFoundError:
        pass


def interrupted_job(world_dir):
    """An advance recorded as running when the observer that ran it stopped (None if there is none)."""
    try:
        return json.loads((Path(world_dir) / JOB_FILE).read_text())
    except (OSError, ValueError):
        return None


def watch_parent(ppid):
    """Worker initializer: the worker exits when the observer that started it is gone. An observer killed
    outright (no time to shut its pool down) would otherwise leave its workers waiting forever: each holds
    both ends of its task queue, so it never sees the end of it."""
    def watch():
        while True:
            time.sleep(2)
            if os.getppid() != ppid:
                os._exit(0)
    threading.Thread(target=watch, name='watch-parent', daemon=True).start()


def ensure_pool(season):
    """Give the season the worker pool it would create for itself (same size, same work), started fresh
    ('spawn', as on Windows) and watching this process. Results do not depend on how workers start."""
    if season.workers > 1 and '_pool' not in season.__dict__:
        import multiprocessing
        from concurrent.futures import ProcessPoolExecutor
        season._pool = ProcessPoolExecutor(season.workers, mp_context=multiprocessing.get_context('spawn'),
                                           initializer=watch_parent, initargs=(os.getpid(),))


class Renderer:
    """One thread that runs everything touching the history snapshot (pages, reloads, opening)."""

    def __init__(self):
        self.q = queue.Queue()
        self.thread = threading.Thread(target=self._loop, name='renderer', daemon=True)
        self.thread.start()

    def _loop(self):
        while True:
            fn, args, box, done = self.q.get()
            if fn is None:
                return
            try:
                box['value'] = fn(*args)
            except BaseException as e:            # handed back to the caller
                box['error'] = e
            done.set()

    def call(self, fn, *args):
        if threading.current_thread() is self.thread:
            return fn(*args)
        box, done = {}, threading.Event()
        self.q.put((fn, args, box, done))
        done.wait()
        if 'error' in box:
            raise box['error']
        return box.get('value')

    def stop(self):
        self.q.put((None, None, None, None))
