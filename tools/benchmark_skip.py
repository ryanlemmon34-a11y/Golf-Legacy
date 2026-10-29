"""Time a full "Skip to end of Season", as the observer does it, part by part, on this machine.

    python tools/benchmark_skip.py                       # a new world, season 1 (writes into a temp dir)
    python tools/benchmark_skip.py --seasons 2           # also time season 2
    python tools/benchmark_skip.py --retired 50000       # SYNTHETIC: pad with retired people first
    python tools/benchmark_skip.py --from-world <dir>    # a disposable COPY of an existing world (never the original)

The owner's target is a skip to the end of a season within 120 s, in season 1 and in season 100, on the
intended hardware, including saving the world and the observer being usable again. Parts reported:

    simulate     the weeks of golf (every shot), the year end and career decisions
    save         the checkpoint: the whole simulation written, hashed, read back, committed
    publish      the season's history staged in the checkpoint copied into the archive (+ index)
    observer     the observer reloading what changed and drawing its overview again
    records      the first Records page after the skip (lazy, then extended season by season)

`--retired N` adds N retired people with expired ranking and fame points to the starting world, an
approximation of the people a world accumulates over a century: it measures what retired people cost
the weekly work, not the archive a century of seasons would hold (that needs a long run).
"""
from __future__ import annotations

import argparse
import copy
import os
import platform
import shutil
import sys
import tempfile
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=2027)
    ap.add_argument('--seasons', type=int, default=1)
    ap.add_argument('--retired', type=int, default=0, help='SYNTHETIC: retired people added to the start')
    ap.add_argument('--workers', type=int, default=None)
    ap.add_argument('--dir', help='world directory (default: a temporary one, removed afterwards)')
    ap.add_argument('--from-world', help='copy this existing world (session directory) and time skips on the copy; '
                    'a world from another engine is opened with allow_other_engine (the copy only)')
    ap.add_argument('--profile', help='write a cProfile of the first season\'s skip (main process) to this file')
    a = ap.parse_args()
    from golfsim import session as SES
    from golfsim.session import Session
    import observer
    try:
        import resource                                   # POSIX only
    except ImportError:
        resource = None
    d = Path(a.dir) if a.dir else Path(tempfile.mkdtemp()) / 'world'
    print(f'machine: {machine()}')
    if a.from_world:
        t = time.perf_counter()
        shutil.copytree(a.from_world, d)
        print(f'copied {a.from_world} to {d} in {time.perf_counter() - t:.0f} s (the original is not opened)')
        t = time.perf_counter()
        s = Session.open(d, workers=a.workers, allow_other_engine=True)     # recovery / index upgrade, once
        print(f'first open (one-time index completion if needed) {time.perf_counter() - t:.1f} s')
        s.close()
        t = time.perf_counter()
        w = observer.World(d, allow_other_engine=True)
        print(f'cold open of the observer {time.perf_counter() - t:.1f} s; active golfers '
              f'{len(w.session.season.active_golfers()):,}, people {len(w.session.season.world.golfers):,}')
        _skips(a, w, observer, Session, SES, resource)
        return
    world = padded_world(a.seed, a.retired) if a.retired else None
    s = Session.create(d, seed=a.seed, workers=a.workers, world=world)
    if a.retired:
        for g in s.season.world.golfers[-a.retired:]:
            s.season.wr[g.id], s.season.am[g.id], s.season.fame_log[g.id] = [], [], []
            s.season.fame.pop(g.id, None)
        s._commit()                                          # the world the observer opens is this one
        print(f'SYNTHETIC: {a.retired:,} retired people added (expired points)')
    s.close()
    w = observer.World(d)
    _skips(a, w, observer, Session, SES, resource)
    if not a.dir:
        shutil.rmtree(d.parent, ignore_errors=True)


def _skips(a, w, observer, Session, SES, resource):
    for n in range(a.seasons):
        parts = {}
        real_commit, real_publish = Session._commit, SES._publish_archive

        def timed_commit(self):
            t = time.perf_counter()
            real_commit(self)
            parts['save+publish'] = time.perf_counter() - t

        def timed_publish(dd, gen):
            t = time.perf_counter()
            real_publish(dd, gen)
            parts['publish'] = time.perf_counter() - t

        c = w.session.cursor
        form = {'weeks': ['season'], 'year': [str(c['year'])], 'week': [str(c['week'])], 'phase': [c['phase']],
                'op': [f'bench-{n}']}
        prof = None
        if a.profile and n == 0:
            import cProfile
            prof = cProfile.Profile()
            prof.enable()
        t0 = time.perf_counter()
        with mock.patch.object(Session, '_commit', timed_commit), mock.patch.object(SES, '_publish_archive', timed_publish):
            t_reload = [0.0]
            real_reload = w.reload

            def timed_reload():
                t = time.perf_counter()
                real_reload()
                t_reload[0] = time.perf_counter() - t
            w.reload = timed_reload
            w.submit(form)
            w.reload = real_reload
        t1 = time.perf_counter()
        if prof:
            prof.disable()
            prof.dump_stats(a.profile)
        observer.overview(w, {})                              # the page the observer returns to
        t2 = time.perf_counter()
        observer.record(w, {}, 'most-wins')                   # the first Records page (stats built lazily)
        t3 = time.perf_counter()
        total = t1 - t0
        save = parts.get('save+publish', 0.0) - parts.get('publish', 0.0)
        sim = total - parts.get('save+publish', 0.0) - t_reload[0]
        print(f'season {c["year"]}: skip to end of season {total + (t2 - t1):.1f} s = simulate {sim:.1f} + save '
              f'{save:.1f} + publish {parts.get("publish", 0.0):.1f} + observer reload {t_reload[0]:.1f} + overview '
              f'{t2 - t1:.1f}; first Records page {t3 - t2:.1f} s; active golfers '
              f'{len(w.session.season.active_golfers()):,}, people in the world {len(w.session.season.world.golfers):,}; '
              + (f'peak memory not measured (no resource module)' if resource is None else f'peak memory {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024:,} MB (this process; the '
              f'largest worker {resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss // 1024:,} MB resident, '
              f'mostly pages shared with it when forked)'), flush=True)
    w.session.close()


if __name__ == '__main__':
    main()
