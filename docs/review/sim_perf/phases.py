"""Wall-clock time per phase of one season's skip (no profiler), and how busy the workers were.

    python phases.py CODE_DIR WORLD_DIR [--workers 4] [--create SEED]

WORLD_DIR is a disposable copy (or created here with --create). Advances to the end of the current season
through Session.advance, as the observer's skip does (one commit at the end).
"""
import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('code')
ap.add_argument('world')
ap.add_argument('--workers', type=int, default=4)
ap.add_argument('--create', type=int)
ap.add_argument('--out')
ap.add_argument('--profile', help='directory: a cProfile per main-process phase (each phase alone)')
a = ap.parse_args()
sys.path.insert(0, a.code)

from golfsim import season as SEA                  # noqa: E402
from golfsim import session as SES                 # noqa: E402
from golfsim import archive as ARC                 # noqa: E402

T = defaultdict(float)
N = defaultdict(int)


PROF = {}
PROFILED = {'plan_block', 'regular_entries', 'develop_week', 'record_event', 'update_rankings', 'weekly_finances',
            'update_fame', 'special_field', 'record_access', 'update_fatigue', 'end_of_season', 'start_year',
            '_stage_archive', '_commit', 'snapshot_standings'}
ACTIVE = [False]


def timed(owner, name, label=None):
    fn = getattr(owner, name)
    label = label or name

    def run(*args, **kw):
        t = time.perf_counter()
        if a.profile and label in PROFILED and not ACTIVE[0]:
            import cProfile
            p = PROF.setdefault(label, cProfile.Profile())
            ACTIVE[0] = True
            try:
                return p.runcall(fn, *args, **kw)
            finally:
                ACTIVE[0] = False
                T[label] += time.perf_counter() - t
                N[label] += 1
        try:
            return fn(*args, **kw)
        finally:
            T[label] += time.perf_counter() - t
            N[label] += 1
    setattr(owner, name, run)


real_play_site = SEA.play_site


def play_site(task):                                # runs in the workers (patched before they fork)
    t = time.perf_counter()
    out = real_play_site(task)
    out['_busy'] = time.perf_counter() - t
    return out


SEA.play_site = play_site
busy = [0.0]
real_record = SEA.Season.record_event


def record_event(self, ed, year, week, site_out, venue_list):
    for o in site_out.values():
        busy[0] += o.pop('_busy', 0.0)
    return real_record(self, ed, year, week, site_out, venue_list)


SEA.Season.record_event = record_event
for name in ('run_week', 'play_week', 'record_event', 'plan_block', 'regular_entries', 'special_field', 'pay_at_sites',
             'develop_week', 'record_access', 'weekly_finances', 'update_rankings', 'update_fame', 'snapshot_standings',
             'update_fatigue', 'start_year', 'end_of_season', 'prune_history'):
    timed(SEA.Season, name)
for name in ('_step', '_stage_archive', '_commit', '_sync'):
    timed(SES.Session, name)
timed(SES, '_publish_archive')
timed(ARC.ArchiveWriter, 'year_chunk')
timed(ARC.ArchiveWriter, 'state_tables')

# the pool's wall time inside play_week: patch ProcessPoolExecutor.map
from concurrent.futures import ProcessPoolExecutor   # noqa: E402
timed(ProcessPoolExecutor, 'map', 'pool.map (dispatch)')
real_chain = None

t0 = time.perf_counter()
if a.create is not None:
    s = SES.Session.create(Path(a.world), seed=a.create, workers=a.workers)
    T.clear(); N.clear()
    create = time.perf_counter() - t0
else:
    create = None
t = time.perf_counter()
s = SES.Session.open(Path(a.world), workers=a.workers, allow_other_engine=True) if a.create is None else s
s.season.workers = a.workers
opened = time.perf_counter() - t
T.clear(); N.clear(); busy[0] = 0.0
c = s.cursor
weeks = 52 - c['week'] + 1 + (0 if c['phase'] != 'start' else 0)
active = len(s.season.active_golfers())
people = len(s.season.world.golfers)
t = time.perf_counter()
s.advance(weeks)
total = time.perf_counter() - t
s.close()

# the pool's real wall time: play_week minus building tasks and recording results is not separable here,
# so report play_week, record_event and the rest
pw = T['play_week']
rows = {k: (round(v, 2), N[k]) for k, v in sorted(T.items(), key=lambda kv: -kv[1])}
res = {'code': a.code, 'world': a.world, 'year': c['year'], 'active': active, 'people': people,
       'workers': a.workers, 'open_s': round(opened, 1), 'advance_s': round(total, 2),
       'worker_busy_s': round(busy[0], 1),
       'play_week_minus_record_s': round(pw - T['record_event'], 1),
       'worker_utilisation': round(busy[0] / (a.workers * max(1e-9, pw - T['record_event'])), 3),
       'phases': rows}
print(json.dumps(res, indent=1))
if a.out:
    Path(a.out).write_text(json.dumps(res, indent=1))
if a.profile:
    Path(a.profile).mkdir(parents=True, exist_ok=True)
    for k, p in PROF.items():
        p.dump_stats(str(Path(a.profile) / f'{k}.prof'))
