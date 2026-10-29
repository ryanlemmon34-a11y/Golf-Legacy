"""Time a full "Skip to end of Season", as the observer does it, part by part, on this machine.

    python tools/benchmark_skip.py                       # a new world, season 1 (writes into a temp dir)
    python tools/benchmark_skip.py --seasons 2           # also time season 2
    python tools/benchmark_skip.py --retired 50000       # SYNTHETIC: pad with retired people first
    python tools/benchmark_skip.py --from-world <dir>    # a disposable COPY of an existing world (never the original)
    python tools/benchmark_skip.py --workers 3           # worker processes for the measured simulation

The owner's target is a skip to the end of a season within 120 s, in season 1 and in season 100, on the
intended hardware, including saving the world and the observer being usable again.

Preparation (creating the world, or copying one and letting a session do its one-time recovery and index
upgrades) runs in a separate process that exits before anything is measured; it is timed and reported
apart, never included. The measured process then opens the observer on the world (`--workers` applies to
this session) and skips. Parts reported:

    simulate     the weeks of golf (every shot), the year end and career decisions, staging the season's
                 history (everything in the skip that is not one of the parts below)
    save         the checkpoint: the whole simulation written, hashed, read back, committed
    publish      the season's history copied into the archive (+ index)
    settle       the season-end heap settling (one garbage collection)
    reload       the observer opening the newly published history
    overview     the overview page drawn again
    = skip       what the player waits for: the click to the overview shown again
    records      the first Records page after it (a separate click; built lazily)

Memory (Linux): sampled once a second for this process and each live worker, as resident (RSS) and
proportional (PSS: shared pages divided among the processes sharing them, so the PSS of all processes
adds up to the memory really used), plus this process's exact peak RSS (ru_maxrss). Elsewhere: not
measured.

`--retired N` adds N retired people with expired ranking and fame points to the starting world, an
approximation of the people a world accumulates over a century: it measures what retired people cost
the weekly work, not the archive a century of seasons would hold (that needs a long run).
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))


def machine():
    cpu = platform.processor() or platform.machine()
    try:
        for line in open('/proc/cpuinfo'):
            if line.startswith('model name'):
                cpu = line.split(':', 1)[1].strip()
                break
    except OSError:
        pass
    return f'{cpu}, {os.cpu_count()} logical CPUs, Python {platform.python_version()}, {platform.system()}'


def padded_world(seed, retired):
    from golfsim.population import generate_world
    w = generate_world(seed=seed)
    base = list(w.golfers)
    nid = max(g.id for g in base) + 1
    for i in range(retired):
        g = copy.copy(base[i % len(base)])
        g.attrs, g.personality, g.ceilings, g.familiarity = dict(g.attrs), dict(g.personality), dict(g.ceilings), {}
        g.id, g.lifestyle, g.tour = nid + i, 'retired', ''
        w.golfers.append(g)
    w.next_id = nid + retired
    w.by_id = {g.id: g for g in w.golfers}
    return w


class MemorySampler(threading.Thread):
    """Peak RSS / PSS of this process and of every live child process (the workers), sampled."""

    def __init__(self, every=1.0):
        super().__init__(daemon=True)
        self.every, self.stop_flag = every, threading.Event()
        self.peak = {'main_rss': 0, 'main_pss': 0, 'worker_rss': 0, 'worker_pss': 0, 'total_pss': 0, 'workers': 0}
        self.ok = os.path.exists('/proc/self/smaps_rollup')

    @staticmethod
    def _mem(pid):
        rss = pss = 0
        try:
            for line in open(f'/proc/{pid}/smaps_rollup'):
                if line.startswith('Rss:'):
                    rss = int(line.split()[1]) // 1024
                elif line.startswith('Pss:'):
                    pss = int(line.split()[1]) // 1024
        except OSError:
            pass
        return rss, pss

    @staticmethod
    def _children():
        me, out = os.getpid(), []
        for d in os.listdir('/proc'):
            if d.isdigit():
                try:
                    if int(open(f'/proc/{d}/stat').read().rsplit(')', 1)[1].split()[1]) == me:
                        out.append(int(d))
                except (OSError, IndexError, ValueError):
                    pass
        return out

    def sample(self):
        p = self.peak
        rss, pss = self._mem(os.getpid())
        kids = [self._mem(c) for c in self._children()]
        p['main_rss'], p['main_pss'] = max(p['main_rss'], rss), max(p['main_pss'], pss)
        p['worker_rss'] = max([p['worker_rss']] + [r for r, _ in kids])
        p['worker_pss'] = max([p['worker_pss']] + [q for _, q in kids])
        p['total_pss'] = max(p['total_pss'], pss + sum(q for _, q in kids))
        p['workers'] = max(p['workers'], len(kids))

    def run(self):
        while not self.stop_flag.wait(self.every):
            self.sample()

    def stop(self):
        """Stop sampling (idempotent) and return the peaks."""
        if not self.stop_flag.is_set():
            self.stop_flag.set()
            if self.is_alive():
                self.join()
            self.sample()
        return self.peak


def prepare(a):
    """In its own process: create the world (or copy one and open it once: recovery, index upgrades)."""
    from golfsim.session import Session
    d = Path(a.dir)
    t = time.perf_counter()
    if a.from_world:
        shutil.copytree(a.from_world, d)
        copied = time.perf_counter() - t
        t = time.perf_counter()
        Session.open(d, workers=a.workers, allow_other_engine=True).close()
        out = {'copy': copied, 'first_open': time.perf_counter() - t}
    else:
        world = padded_world(a.seed, a.retired) if a.retired else None
        s = Session.create(d, seed=a.seed, workers=a.workers, world=world)
        if a.retired:
            for g in s.season.world.golfers[-a.retired:]:
                s.season.wr[g.id], s.season.am[g.id], s.season.fame_log[g.id] = [], [], []
                s.season.fame.pop(g.id, None)
            s._commit()                                          # the world the observer opens is this one
        s.close()
        out = {'create': time.perf_counter() - t}
    print(json.dumps(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=2027)
    ap.add_argument('--seasons', type=int, default=1)
    ap.add_argument('--retired', type=int, default=0, help='SYNTHETIC: retired people added to the start')
    ap.add_argument('--workers', type=int, default=None, help='worker processes for the measured simulation '
                    '(default: the number the world was saved with)')
    ap.add_argument('--dir', help='world directory (default: a temporary one, removed afterwards)')
    ap.add_argument('--from-world', help='copy this existing world (session directory) and time skips on the copy; '
                    'a world from another engine is opened with allow_other_engine (the copy only)')
    ap.add_argument('--profile', help='write a cProfile of the first season\'s skip (main process) to this file')
    ap.add_argument('--prepare', action='store_true', help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.prepare:
        return prepare(a)
    d = Path(a.dir) if a.dir else Path(tempfile.mkdtemp()) / 'world'
    w = None
    try:
        print(f'machine: {machine()}', flush=True)
        args = [sys.executable, __file__, '--prepare', '--dir', str(d), '--seed', str(a.seed), '--retired', str(a.retired)]
        args += ['--from-world', a.from_world] if a.from_world else []
        args += ['--workers', str(a.workers)] if a.workers else []
        prep = json.loads(subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip().splitlines()[-1])
        print('preparation, in its own process (not measured): ' + ', '.join(f'{k} {v:.1f} s' for k, v in prep.items())
              + (' (first open: recovery and one-time index upgrades of the copy)' if a.from_world else ''), flush=True)

        from golfsim import session as SES
        from golfsim.session import Session
        import observer
        try:
            import resource                               # POSIX only
        except ImportError:
            resource = None
        t = time.perf_counter()
        try:
            w = observer.World(d, allow_other_engine=bool(a.from_world), workers=a.workers)
        except TypeError:                                 # an older observer (comparisons on older code)
            w = observer.World(d, allow_other_engine=True) if a.from_world else observer.World(d)
            if a.workers:
                w.session.season.workers = a.workers
        print(f'cold open of the observer {time.perf_counter() - t:.1f} s; active golfers '
              f'{len(w.session.season.active_golfers()):,}, people {len(w.session.season.world.golfers):,}; '
              f'workers {w.session.season.workers}', flush=True)
        _skips(a, w, observer, Session, SES, resource)
    finally:                                              # the whole observer (session, workers, history
        if w is not None:                                 # snapshot and its index connection), before any
            (w.close if hasattr(w, 'close') else w.session.close)()   # temporary directory is removed
        if not a.dir:
            shutil.rmtree(d.parent, ignore_errors=True)


def _skips(a, w, observer, Session, SES, resource):
    for n in range(a.seasons):
        parts = {}
        real_commit, real_publish = Session._commit, SES._publish_archive
        real_settle = getattr(SES, 'settle_heap', None)

        def timed(name, fn):
            def run(*args, **kw):
                t = time.perf_counter()
                try:
                    return fn(*args, **kw)
                finally:
                    parts[name] = parts.get(name, 0.0) + time.perf_counter() - t
            return run

        c = w.session.cursor
        form = {'weeks': ['season'], 'year': [str(c['year'])], 'week': [str(c['week'])], 'phase': [c['phase']],
                'op': [f'bench-{n}']}
        prof = None
        if a.profile and n == 0:
            import cProfile
            prof = cProfile.Profile()
            prof.enable()
        sampler = MemorySampler()
        patches = [mock.patch.object(Session, '_commit', timed('commit', real_commit)),
                   mock.patch.object(SES, '_publish_archive', timed('publish', real_publish))]
        if real_settle is not None:
            patches.append(mock.patch.object(SES, 'settle_heap', timed('settle', real_settle)))
        mem = None
        with contextlib.ExitStack() as stack:             # everything undone however the skip ends
            if sampler.ok:
                sampler.start()
                stack.callback(sampler.stop)
            if prof:
                stack.callback(prof.disable)
            for patch in patches:
                stack.enter_context(patch)
            real_reload = w.reload
            w.reload = timed('reload', real_reload)
            stack.callback(setattr, w, 'reload', real_reload)
            t0 = time.perf_counter()
            w.submit(form)
            t1 = time.perf_counter()
            if prof:
                prof.disable()
                prof.dump_stats(a.profile)
            w.reload = real_reload
            observer.overview(w, {})                          # the page the observer returns to
            t2 = time.perf_counter()
            observer.record(w, {}, 'most-wins')               # the first Records page (stats built lazily)
            t3 = time.perf_counter()
            mem = sampler.stop() if sampler.ok else None
        submit = t1 - t0
        publish, settle, reload_ = parts.get('publish', 0.0), parts.get('settle', 0.0), parts.get('reload', 0.0)
        save = parts.get('commit', 0.0) - publish - settle
        sim = submit - parts.get('commit', 0.0) - reload_
        print(f'season {c["year"]}: skip (click to overview shown) {submit + (t2 - t1):.1f} s = simulate {sim:.1f} + '
              f'save {save:.1f} + publish {publish:.1f} + settle {settle:.1f} + reload {reload_:.1f} + overview '
              f'{t2 - t1:.1f}; then first Records page {t3 - t2:.1f} s; active golfers '
              f'{len(w.session.season.active_golfers()):,}, people {len(w.session.season.world.golfers):,}; '
              f'workers {w.session.season.workers}', flush=True)
        if mem:
            print(f'  memory peaks (sampled each second): this process RSS {mem["main_rss"]:,} MB / PSS '
                  f'{mem["main_pss"]:,} MB (exact peak RSS {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024:,} MB); '
                  f'largest worker RSS {mem["worker_rss"]:,} MB / PSS {mem["worker_pss"]:,} MB; all processes PSS '
                  f'{mem["total_pss"]:,} MB; live workers seen {mem["workers"]}', flush=True)
        else:
            print('  memory: not measured on this platform', flush=True)


if __name__ == '__main__':
    main()
