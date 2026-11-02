"""Experiment harness: the production event path on verified captured tasks, with controlled changes.

Every task comes from a season the replay verified (replay.py: CAPDIR/MANIFEST.json) and must pass two no-op
checks before use:
  1. season.play_site(task) reproduces the archived edition exactly (finish and every round's conditions);
  2. play(task, task['seed'], None) below, which is the same call with the conditions made explicit,
     reproduces it too.
Changes are made only to deep copies of the task: one golfer's attributes (+d points, nothing rebalanced, no
development ceilings involved), or the rounds' conditions (seasonal model kept: wind_from always set, never the
classic default Conditions()). The engine code is not modified.

Random streams (disclosed in the report):
  - one shot stream per event site, seeded by the task seed and shared by the whole field in tee order; draws
    are conditional on outcomes, so a change to one golfer shifts every later draw (paired seeds are matched
    designs, not identical paths);
  - weather in production is drawn from the task seed: replicates with new seeds also draw new conditions,
    unless conditions are injected;
  - each golfer's gusts come from weather.gust_seed(course, conditions, golfer, round), which does NOT include
    the shot seed: replicates under the same conditions reuse one gust sequence per golfer and round.
"""
from __future__ import annotations

import copy
import hashlib
import json
import pickle
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from golfsim import season as SEA  # noqa: E402
from golfsim import weather as WX  # noqa: E402
from golfsim.engine import Conditions  # noqa: E402
from golfsim.tournament import play_event  # noqa: E402


class Unverified(RuntimeError):
    pass


def _sha(p):
    h = hashlib.sha256()
    h.update(Path(p).read_bytes())
    return h.hexdigest()


def load_task(capdir, name):
    """A captured task, only from a verified season and only if its file matches the manifest's hash."""
    capdir = Path(capdir)
    man = json.loads((capdir / 'MANIFEST.json').read_text())
    y = name.split('_')[0]
    rec = man['years'].get(y)
    if not rec or not rec['verified'] or rec.get('first_bad_week') is not None:
        raise Unverified(f'{name}: season {y} is not verified')
    want = rec.get('tasks', {}).get(name)
    p = capdir / 'tasks' / name
    if want is None or _sha(p) != want:
        raise Unverified(f'{name}: not in the manifest or its hash differs')
    with open(p, 'rb') as f:                       # written by this study's own replay process
        return pickle.load(f)


def verified_tasks(capdir):
    man = json.loads((Path(capdir) / 'MANIFEST.json').read_text())
    return sorted(n for y, r in man['years'].items() if r['verified'] for n in r.get('tasks', {}))


def conditions(task, seed=None):
    """The rounds' conditions exactly as play_site draws them (seasonal model), for `seed` (default the task's)."""
    pins = 0.3 + 0.4 * task['prestige'] / 100
    return WX.draw_conditions(task['course'], task['week'], task['rounds'], pins,
                              task['seed'] if seed is None else seed)


def play(task, seed=None, cond=None, on_round=None):
    """play_site's stroke-play path with the shot seed and (optionally) the conditions made explicit.
    Returns (board [(golfer, total, rounds)], playoff holes, conditions used)."""
    rng = random.Random(task['seed'] if seed is None else seed)
    golfers = task['golfers']
    caddies = {id(g): k for g, k in zip(golfers, task.get('caddies') or ())}
    if cond is None:
        assert task.get('weather') == WX.MODEL, 'seasonal weather expected'
        cond = conditions(task, seed)
    cut_after = 2 if task['cut_top'] and task['rounds'] > 2 else None
    board, playoff = play_event(golfers, task['course'], rng, cut_top=task['cut_top'] or len(golfers),
                                prestige=task['prestige'] / 100, cond_by_round=cond, rounds_n=task['rounds'],
                                cut_after=cut_after, on_round=on_round, caddies=caddies)
    return board, playoff, cond


def finish_of(board, golfers):
    """The archived finish format (gid, position, total) with non-finishers last, as play_site builds it."""
    finish, totals = [], [t for _, t, _ in board]
    for i, (g, total, rds) in enumerate(board):
        pos = 1 if i == 0 else 1 + sum(1 for t in totals if t < total)
        if i > 0 and total == totals[0]:
            pos = 2
        finish.append([g.id, pos, total])
    made = {x[0] for x in finish}
    finish += [[g.id, None, None] for g in golfers if g.id not in made]
    return finish


def noop_check(task, archived_event):
    """Both no-op checks against the archived edition; raises AssertionError on any difference."""
    site = task['site']
    out = SEA.play_site(copy.deepcopy(task))
    assert [list(x) for x in out['finish']] == archived_event['finish'][site], 'play_site differs from archive'
    want_c = [[float(v) for v in c] for c in archived_event['conditions'][site]]
    assert [[float(v) for v in c] for c in out['conditions']] == want_c, 'conditions differ from archive'
    board, _, cond = play(copy.deepcopy(task))
    assert finish_of(board, task['golfers']) == archived_event['finish'][site], 'harness play differs'
    assert [[float(v) for v in WX.archived(cond[r])] for r in sorted(cond)] == want_c
    return True


def perturbed(task, gid, attr, delta):
    """A deep copy with one golfer's one attribute changed by `delta` points. Returns (task, clipped?)."""
    t = copy.deepcopy(task)
    g = next(g for g in t['golfers'] if g.id == gid)
    v = g.attrs[attr] + delta
    clipped = not (1.0 <= v <= 99.0)
    g.attrs[attr] = max(1.0, min(99.0, v))
    return t, clipped


def scenario_conditions(task, wind, wet, wind_from=None, gust=None):
    """Seasonal-model conditions for every round: the given wind (mph) and wetness, the archived pin difficulty,
    the course's usual direction (or `wind_from`) and the archived gustiness (or `gust`). Never the classic
    model: wind_from is always set."""
    base = conditions(task)
    out = {}
    for r, c in base.items():
        out[r] = Conditions(wind_mph=round(float(wind), 1), rain=bool(wet), pin_difficulty=c.pin_difficulty,
                            wind_from=c.wind_from if wind_from is None else wind_from,
                            gust=c.gust if gust is None else gust)
    return out
