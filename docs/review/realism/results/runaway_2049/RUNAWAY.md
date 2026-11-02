# Runaway hole that stopped the branch's seed-2027 world in 2049: a latent engine defect, also on main

**What happened.** The branch's full-scale world (`d619dd6`, seed 2027) stopped in its 23rd season (2049) with
`RuntimeError: Runaway hole: 60 strokes on hole 17 (engine bug)`. That is the engine's own guard; it refuses to
invent a score, so the season stops. The run's 22 completed seasons (2027–2048) are intact and are what the
comparison uses. The main run (`18a8e23`, same seed) was not affected.

**Reproduced exactly.** The season was re-run from the branch run's 2048 save with `engine.play_hole` wrapped, and
the state at hole entry was captured in `hole17_state.pkl` (a trusted local fixture):
- the player before the hole;
- the hole;
- the round's random state;
- the hole state and the pin.

`python replay.py <checkout>` replays it and gives the same `RuntimeError` on **main `18a8e23`** and on the
**branch `d619dd6`**. This code path is identical on both, so the defect is latent on main and is not caused by the
realism changes. The branch world's different history simply produced this player on this hole.

**The situation.**
- **The hole:** a 359-yard par 4 bending right (dogleg 0.67) with a 221-yard landing limit, out of bounds left and
  trees right.
- **The player:** a 25-year-old amateur who carries the driver about 302 yards, aggression 0.82, ball flight 0.62.
- **The plan:** with only the actual execution instrumented (a pass-through spy on the tee plans play_hole uses,
  and the hole's penalties), the player hit **the driver on all 30 tee attempts, with 30 out-of-bounds
  penalties**, before the guard stopped the hole.
- **Correction:** an earlier version of this note said "a 3-wood, 29 re-tees". That was wrong. It came from
  calling the planner before play_hole had made its mishit draw, which changed the random stream and the plan cache.
  `replay.py` now instruments the execution only.

**The mechanism (engine code, both builds).**
1. **The plan model** (`_tee_plan`) prices a tee shot that runs through the dogleg as a *narrower* fairway, and it
   prices leaving the corridor at the *average* of the two sides' costs (OB 1.9 and trees 0.8).
2. **The execution** instead *shifts* the ball toward the dogleg's outside, here the OB side, by
   over × dogleg × (1 − 0.6 × ball flight):
   - on a right bend the outside is the left;
   - for a long hitter the shift (25–35 yards) exceeds the corridor (half fairway plus rough, 22.5 yards), so most
     tee shots go out of bounds.
3. **The plan is cached** for the hole and the round (`pl.plans`), so every stroke-and-distance re-tee hits the same
   club again. Here 30 tee shots with the driver all went out of bounds and reached the 60-stroke guard.

**The fix (separate branch, for review before it is integrated anywhere).**
- **Branch:** `fix/engine-dogleg-retee` at `e99cb20`, from main `18a8e23`.
- **The planner:** it now prices a run-through the way play puts the ball, with trouble costed on its own side.
- **A reload re-plans:** no driver bonus, and a lay-up short of the corner (down to 25% of a driver) is available.
- **Noise:** the hole's judgement noise is drawn once, with the same draws as before, and kept. A cached plan and a
  fresh one therefore agree, and a reload draws nothing.
- **The guard:** 60 strokes, unchanged.

Replayed with `replay.py`:

| build | outcome on this hole |
|---|---|
| main `18a8e23` | runaway: 30 tee shots, all driver, 30 penalties |
| realism `d619dd6` | runaway: 30 tee shots, all driver, 30 penalties |
| fix `e99cb20` | 4 strokes: one iron tee shot, no penalty |

Tests: `tests/test_tee_plan.py` on the fix branch.

Until the fix is integrated, a long world on either build can stop this way, rarely: once in 22 full-scale seasons
of this run, and not in the main run's 30 seasons of the same seed.
