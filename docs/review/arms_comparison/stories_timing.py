#!/usr/bin/env python3
"""Time the candidate build's story assembly (tools/observer_stories.py) on a pinned long archive, read-only.

    nice -n 19 python3 -B stories_timing.py --build BUILD --archive RUN/world_<s>/archive --out story_timing.json

Nothing is written into the archive's folder. A mirror folder in armsan/story_mirror holds a copy of the archive's
MANIFEST.json and symbolic links to the (immutable, generation-named) files it lists -- never to its index.sqlite, so
the archive's own index (a WAL database another reader would have to write a shared-memory file beside) is never
opened. The observer then treats the mirror as a history browsed read-only: its side index and every cache go to
TMPDIR (armsan/story_tmp). The side index is built once by the build's own archive.build_index_at, in a child process
that is stopped if free disk space falls below --min-free-gb (two simulations are writing on the same disk); it is
timed separately (a one-off cost of a read-only history, not of a story).

Passes over the sample (by default 20 majors spread over the archive's seasons, the four majors in turn):
  1 cold, as first opened: an empty story cache; the story index of earlier seasons is built in the background as
    the observer does (facts that wait for it say "still being indexed" and are not kept)
  2 cold facts, story index complete: after the background indexer finished; facts and stories cleared
  3 warm (disk): a new cache object on the same file (nothing in memory)
  4 warm (memory): the same cache object again
Memory: the process's peak RSS after each pass, and the background indexer's peak (children).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import shutil
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
MAJORS = ('TOUR_MASTERS', 'PREMIER_TOUR_CHAMPIONSHIP', 'USA_OPEN', 'BRITANNIA_OPEN')


def rss_mb():
    try:
        for line in open('/proc/self/status'):
            if line.startswith('VmRSS:'):
                return int(line.split()[1]) / 1024
    except OSError:
        pass
    return float('nan')


def peak_mb(who=resource.RUSAGE_SELF):
    return resource.getrusage(who).ru_maxrss / 1024


def free_gb(p):
    return shutil.disk_usage(p).free / 1e9


def make_mirror(archive, mirror):
    """mirror/archive: MANIFEST.json copied, every file it names linked (read-only use)."""
    archive = Path(archive).resolve()
    m = json.loads((archive / 'MANIFEST.json').read_text())
    files = [m['files']['world'], m['files']['people'], m['files']['relations'], m['files']['records']]
    files += list(m['files']['years'].values())
    d = Path(mirror) / 'archive'
    (d / 'years').mkdir(parents=True, exist_ok=True)
    for f in files:
        dst = d / f
        if not dst.is_symlink():
            dst.symlink_to(archive / f)
    (d / 'MANIFEST.json').write_text((archive / 'MANIFEST.json').read_text())
    return d, m


def build_side_index(build, mirror_archive, side, min_free, log):
    """archive.build_index_at in a child process, stopped if free disk space falls below min_free GB."""
    side = Path(side)
    if side.exists():
        return {'built': False, 'seconds': 0.0, 'bytes': side.stat().st_size}
    side.parent.mkdir(parents=True, exist_ok=True)
    code = ('import sys; sys.dont_write_bytecode=True; sys.path.insert(0, sys.argv[1]); '
            'from golfsim.archive import build_index_at; from pathlib import Path; '
            'build_index_at(Path(sys.argv[2]), Path(sys.argv[3]), report=lambda d, t: print(d, t, flush=True))')
    t = time.perf_counter()
    p = subprocess.Popen(['nice', '-n', '19', sys.executable, '-B', '-c', code, str(build), str(mirror_archive), str(side)],
                         stdout=subprocess.PIPE, text=True)
    stopped = None
    last = ''
    os.set_blocking(p.stdout.fileno(), False)
    while p.poll() is None:
        time.sleep(2)
        try:
            chunk = p.stdout.read()
            if chunk:
                last = chunk.strip().splitlines()[-1]
                log(f'  side index: {last} seasons')
        except (TypeError, OSError):
            pass
        if free_gb(side.parent) < min_free:
            stopped = f'stopped: free disk space below {min_free} GB'
            p.terminate()
            p.wait(30)
            break
    secs = time.perf_counter() - t
    child_peak = peak_mb(resource.RUSAGE_CHILDREN)
    if stopped or p.returncode != 0:
        for q in side.parent.glob(side.name + '.part*'):
            q.unlink()
        return {'built': False, 'error': stopped or f'exit {p.returncode}', 'seconds': secs}
    return {'built': True, 'seconds': secs, 'bytes': side.stat().st_size, 'child_peak_mb': child_peak}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', required=True)
    ap.add_argument('--archive', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--n', type=int, default=20)
    ap.add_argument('--min-free-gb', type=float, default=3.0)
    ap.add_argument('--keep-caches', action='store_true',
                    help='keep the side index (~1 GB) and story caches in story_tmp (default: removed at the end, the '
                         'disk is shared with running simulations; a rerun rebuilds them)')
    ap.add_argument('--wait-index', type=float, default=3600, help='seconds to wait for the background story index')
    a = ap.parse_args()
    log = lambda s: print(time.strftime('%H:%M:%S'), s, flush=True)
    build = Path(a.build).resolve()
    key = hashlib.sha1(str(Path(a.archive).resolve()).encode()).hexdigest()[:12]
    mirror = HERE / 'story_mirror' / key
    tmp = HERE / 'story_tmp'
    tmp.mkdir(exist_ok=True)
    os.environ['TMPDIR'] = str(tmp)
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'          # (the background indexer imports the build: no __pycache__)
    import tempfile
    tempfile.tempdir = str(tmp)
    sys.path.insert(0, str(build))
    sys.path.insert(0, str(build / 'tools'))
    marc, man = make_mirror(a.archive, mirror)
    years = sorted(int(y) for y in man['files']['years'])
    result = {'archive': str(Path(a.archive).resolve()), 'mirror': str(marc), 'build': str(build),
              'archive_generation': man.get('generation'), 'seasons': [years[0], years[-1], len(years)],
              'started': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}
    try:
        rm = json.loads((Path(a.archive).resolve().parents[1] / 'manifest.json').read_text())
        result['archive_build'] = rm.get('commit')
    except (OSError, ValueError):
        result['archive_build'] = None
    import observer_stats as ST
    import observer
    import observer_stories as OS

    class _W:                                            # (index_path needs only these)
        session = None
        archive_dir = marc
    side = ST.index_path(_W)
    log(f'side index {side} (free {free_gb(tmp):.1f} GB)')
    result['side_index'] = build_side_index(build, marc, side, a.min_free_gb, log)
    log(f'side index: {result["side_index"]}')
    if not side.exists():
        result['error'] = 'no side index (see side_index); story timing not run'
        Path(a.out).write_text(json.dumps(result, indent=1))
        return
    t = time.perf_counter()
    w = observer.World(marc, read_only=True)
    result['world_open_s'] = round(time.perf_counter() - t, 2)
    result['world_open_rss_mb'] = round(rss_mb())
    if w.a is None or w.a.index is None:
        result['error'] = 'the side index was not usable'
        Path(a.out).write_text(json.dumps(result, indent=1))
        return
    # the sample: n majors spread over the seasons, the majors in turn
    n = min(a.n, len(years))
    picks = []
    for i in range(n):
        y = years[round(i * (len(years) - 1) / max(1, n - 1))]
        picks.append(f'{y}:{MAJORS[i % len(MAJORS)]}')
    src_cache_path = OS.cache_for(w).path
    for p in (src_cache_path, *src_cache_path.parent.glob(src_cache_path.name + '-*')):
        if Path(p).exists():
            Path(p).unlink()
    w.__dict__.pop('_story_cache', None)
    cache = OS.cache_for(w)
    src = OS.WorldSource(w, cache)
    missing = Counter()
    patterns = Counter()
    passes = {}

    def run(label, c, keep_missing=False):
        s = OS.WorldSource(w, c)
        rows = []
        for eid in picks:
            t0 = time.perf_counter()
            rec, st = OS.tell(s, eid, cache=c)
            dt = time.perf_counter() - t0
            if rec is None:
                rows.append({'event': eid, 'seconds': round(dt, 3), 'found': False})
                continue
            pend = OS._pending(rec)
            rows.append({'event': eid, 'seconds': round(dt, 3), 'pending': pend, 'rss_mb': round(rss_mb())})
            if keep_missing:
                for m in rec.get('missing') or []:
                    missing[m[:160]] += 1
                patterns.update(st.get('patterns') or [])
        passes[label] = {'rows': rows, 'peak_mb': round(peak_mb()), 'total_s': round(sum(r['seconds'] for r in rows), 2)}
        log(f'{label}: total {passes[label]["total_s"]} s, peak {passes[label]["peak_mb"]} MB, '
            f'pending {sum(1 for r in rows if r.get("pending"))}')

    # pass 0: the latest edition opened first in an empty story cache -- every earlier season unindexed, so the
    # background indexer starts and the facts that wait for it are not kept (a separate cache file, removed after)
    p0 = cache.path.with_name(cache.path.name.replace('stories.sqlite', 'stories_latest_first.sqlite'))
    for q in p0.parent.glob(p0.name + '*'):
        q.unlink()
    c0 = OS.StoryCache(p0)
    s0 = OS.WorldSource(w, c0)
    t0 = time.perf_counter()
    rec0, _ = OS.tell(s0, picks[-1], cache=c0)
    first_s = time.perf_counter() - t0
    pend0 = bool(rec0 and OS._pending(rec0))
    t1 = time.perf_counter()
    while c0.indexing() and time.perf_counter() - t1 < a.wait_index:
        time.sleep(2)
    idx_s = time.perf_counter() - t1
    t2 = time.perf_counter()
    rec0b, _ = OS.tell(s0, picks[-1], cache=c0)
    again_s = time.perf_counter() - t2
    result['latest_first'] = {'event': picks[-1], 'first_s': round(first_s, 3), 'pending': pend0,
                              'indexer_s': round(idx_s, 1), 'indexer_done': not c0.indexing(),
                              'reopened_s': round(again_s, 3), 'reopened_pending': bool(rec0b and OS._pending(rec0b)),
                              'children_peak_mb': round(peak_mb(resource.RUSAGE_CHILDREN)), 'rss_mb': round(rss_mb())}
    c0.stop_indexer()
    log(f'latest first: {result["latest_first"]}')
    for q in p0.parent.glob(p0.name.replace('.sqlite', '') + '*'):
        q.unlink()
    w.a._years.clear()                                   # (pass 1 starts with no decoded season, as on opening)
    run('1 cold, as first opened', cache)
    t = time.perf_counter()
    while cache.indexing() and time.perf_counter() - t < a.wait_index:
        time.sleep(5)
    result['background_story_index_wait_s'] = round(time.perf_counter() - t, 1)
    result['background_story_index_done'] = not cache.indexing()
    result['children_peak_mb'] = round(peak_mb(resource.RUSAGE_CHILDREN))
    # pass 2: facts and stories cleared, the story index (seasons, edition rounds, golf weeks) kept
    db = sqlite3.connect(cache.path)
    db.execute('DELETE FROM facts')
    db.execute('DELETE FROM stories')
    db.commit()
    db.close()
    cache.mem.clear()
    cold2 = OS.StoryCache(cache.path)
    run('2 cold facts, story index complete', cold2, keep_missing=True)
    warm_disk = OS.StoryCache(cache.path)
    run('3 warm (disk)', warm_disk)
    run('4 warm (memory)', warm_disk)
    cache.stop_indexer()
    result['passes'] = passes
    result['missing'] = dict(missing.most_common())
    result['patterns'] = dict(patterns.most_common())
    result['story_cache_bytes'] = sum(p.stat().st_size for p in cache.path.parent.glob(cache.path.name + '*'))
    result['peak_mb'] = round(peak_mb())
    result['finished'] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    result['summary_md'] = summary(result)
    Path(a.out).write_text(json.dumps(result, indent=1))
    if not a.keep_caches:
        w.a.close()
        for q in (tmp / 'golf-legacy-observer').glob('*'):
            q.unlink()
        log('caches removed')
    log('done')


def summary(r):
    import statistics as S
    L = []
    L.append(f'Archive: `{r["archive"]}` (seasons {r["seasons"][0]}–{r["seasons"][1]}, {r["seasons"][2]} seasons, '
             f'archive build {str(r.get("archive_build"))[:7]}); story code: the candidate build `{r["build"]}`. '
             f'Read through a mirror of its MANIFEST and links to the files it names (`{r["mirror"]}`); its own '
             f'index.sqlite was never opened. Measured {r["started"]}–{r["finished"]} UTC with `nice -n 19` while two '
             'simulations ran on the same 4-CPU machine (times include that contention).')
    L.append('')
    si = r['side_index']
    L.append(f'- One-off side index of the read-only history (golfsim.archive.build_index_at, as the observer builds for '
             f'a history it does not own): {"built in " + format(si["seconds"], ".0f") + " s, " if si.get("built") else "already present, "}'
             f'{si.get("bytes", 0) / 1e9:.2f} GB' + (f', child peak {si["child_peak_mb"]:.0f} MB' if si.get('child_peak_mb') else '') + '.')
    L.append(f'- Opening the history read-only (observer.World): {r["world_open_s"]} s, RSS {r["world_open_rss_mb"]} MB.')
    L.append(f'- After pass 1 a background story indexer was {"still running and waited for " + str(r["background_story_index_wait_s"]) + " s" if r["background_story_index_wait_s"] else "not running (none was needed)"}; '
             f'largest child process peak so far {r["children_peak_mb"]} MB.')
    lf = r.get('latest_first')
    if lf:
        L.append(f'- Latest edition opened first in an empty story cache ({lf["event"]}): {lf["first_s"]} s, facts '
                 f'{"waiting for the story index (not kept)" if lf["pending"] else "complete"}; the background story '
                 f'indexer then took {lf["indexer_s"]} s (finished: {lf["indexer_done"]}; largest child peak '
                 f'{lf["children_peak_mb"]} MB); reopened afterwards: {lf["reopened_s"]} s'
                 f'{" (still pending)" if lf["reopened_pending"] else ""}.')
    L.append('- Passes 1–4 below open the sample oldest first, so each cold story found at most two seasons '
             'unindexed and indexed them inline (INLINE_SEASONS = 2); the observer keeps up to 4 decoded seasons '
             'in memory (archive.Archive.CACHE_SEASONS), which is what the process RSS climbs to.')
    L.append('')
    rows = []
    for label, p in r['passes'].items():
        secs = [x['seconds'] for x in p['rows'] if x.get('found', True)]
        pend = sum(1 for x in p['rows'] if x.get('pending'))
        rows.append((label, len(secs), f'{min(secs):.3f}', f'{S.median(secs):.3f}', f'{max(secs):.3f}', f'{sum(secs):.1f}',
                     pend, p['peak_mb']))
    L.append('| pass | editions | min s | median s | max s | total s | facts pending (not cached) | process peak RSS MB |')
    L.append('|---|---|---|---|---|---|---|---|')
    L += ['| ' + ' | '.join(map(str, x)) + ' |' for x in rows]
    L.append('')
    L.append('Per edition (seconds: pass 1 / 2 / 3 / 4):')
    L.append('')
    L.append('| edition | ' + ' | '.join(f'pass {k[0]}' for k in r['passes']) + ' | RSS after pass 1 (MB) |')
    L.append('|---|' + '---|' * (len(r['passes']) + 1))
    first = list(r['passes'].values())[0]['rows']
    for i, x in enumerate(first):
        L.append(f'| {x["event"]} | ' + ' | '.join(f'{p["rows"][i]["seconds"]:.3f}' + (' (pending)' if p['rows'][i].get('pending') else '')
                                                  for p in r['passes'].values()) + f' | {x.get("rss_mb", "")} |')
    L.append('')
    L.append(f'Story cache on disk after the sample: {r["story_cache_bytes"] / 1e6:.1f} MB. Patterns of the sampled stories: '
             + ', '.join(f'{k} {v}' for k, v in r['patterns'].items()) + '.')
    L.append('')
    L.append('Facts the sampled stories list as not recorded (`missing`, pass 2; editions of the 45-season archive '
             'built by 473690a, which predates some facts the candidate records):')
    L.append('')
    L += [f'- {k}: {v} of {len(first)} editions' for k, v in r['missing'].items()] or ['- none']
    return '\n'.join(L)


if __name__ == '__main__':
    main()
