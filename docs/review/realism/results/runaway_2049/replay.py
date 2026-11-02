"""Replay the hole that stopped the branch's seed-2027 world in 2049 (runaway guard), on any checkout, instrumenting
the actual execution only: a pass-through spy records each tee plan play_hole uses (it draws nothing and caches
nothing itself), and the hole's penalties come from its RoundStats.

Usage: python replay.py CHECKOUT    (e.g. a main 18a8e23 checkout, the branch d619dd6, or the fix)
The state (player before the hole, the hole, the round's random state, hole state, pin) was captured at entry to
engine.play_hole in a re-run of season 2049 from the branch run's 2048 save (d619dd6). Trusted local fixture.
"""
import pickle
import random
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from golfsim import engine as E  # noqa: E402

d = pickle.load(open(Path(__file__).with_name('hole17_state.pkl'), 'rb'))
h, pl, st = d['hole'], d['pl'], d['st']
if 'plan_noise' in E.Player.__init__.__code__.co_names or hasattr(E, 'TEE_CLUBS'):
    pl.plan_noise = {}                                     # (a fixed build: the Player predates its new fields)
    pl.plans = {(k, False): v for k, v in pl.plans.items()}
print('hole', h.number, 'par', h.par, h.plays, 'yd, left', h.left, 'right', h.right, 'landing limit', h.landing_limit,
      'dogleg', h.dogleg, h.bend, '| player drive', round(pl.drive, 1), 'aggression', pl.aggr,
      'management', round(pl.mgmt, 2), 'ball flight', round(pl.bfc, 2))
plans = []
real = E._tee_plan


def spy(*a, **k):
    r = real(*a, **k)
    plans.append(r[0])
    return r


E._tee_plan = spy
rng = random.Random()
rng.setstate(d['rng'])
pen0 = st.penalties
try:
    print('strokes', E.play_hole(pl, h, d['hidx'], rng, st, *d['a'], **d['k']))
except RuntimeError as e:
    print('RuntimeError:', e)
print('tee shots', len(plans), 'clubs', sorted(set(plans)), '| penalties on the hole', st.penalties - pen0)
