"""Replay the hole that stopped the branch's seed-2027 world in 2049 (runaway guard), on any checkout.

Usage: python replay.py CHECKOUT    (e.g. a main 18a8e23 checkout, or the branch)
The state (player before the hole, the hole, the round's random state, hole state, pin) was captured at entry to
engine.play_hole in a re-run of season 2049 from the branch run's 2048 save (d619dd6). Trusted local fixture.
"""
import copy
import pickle
import random
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from golfsim import engine as E  # noqa: E402

d = pickle.load(open(Path(__file__).with_name('hole17_state.pkl'), 'rb'))
h, pl = d['hole'], d['pl']
print('hole', h.number, 'par', h.par, h.plays, 'yd, left', h.left, 'right', h.right, 'landing limit', h.landing_limit,
      'dogleg', h.dogleg, getattr(h, 'bend', None), '| player drive', round(pl.drive, 1), 'aggression', pl.aggr,
      'management', round(pl.mgmt, 2), 'ball flight', round(pl.bfc, 2))
rng = random.Random()
rng.setstate(d['rng'])
probe = random.Random()
probe.setstate(d['rng'])
print('cached plans at entry:', dict(pl.plans), '| plan this hole draws:', E._tee_plan(copy.deepcopy(pl), h, probe))
try:
    print('strokes', E.play_hole(pl, h, d['hidx'], rng, d['st'], *d['a'], **d['k']))
except RuntimeError as e:
    print('RuntimeError:', e)
