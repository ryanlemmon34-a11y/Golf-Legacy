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
- **The plan:** the club plan drawn for this hole is a 3-wood (about 278 yards).

**The mechanism (engine code, both builds).**
1. **The plan model** (`_tee_plan`) prices a tee shot that runs through the dogleg as a *narrower* fairway, and it
   prices leaving the corridor at the *average* of the two sides' costs (OB 1.9 and trees 0.8).
2. **The execution** instead *shifts* the ball toward the dogleg's outside, here the OB side, by
   over × dogleg × (1 − 0.6 × ball flight):
   - on a right bend the outside is the left;
   - for a long hitter the shift (25–35 yards) exceeds the corridor (half fairway plus rough, 22.5 yards), so most
     tee shots go out of bounds.
3. **The plan is cached** for the hole and the round (`pl.plans`), so every stroke-and-distance re-tee hits the same
   club again. Here 29 consecutive re-tees went out of bounds and reached the 60-stroke guard.

**Proposed minimal fix, not applied (`d619dd6` stays frozen), for review.**
- **The change:** after an out-of-bounds tee shot, the re-tee uses the most conservative club ('iron'). Real
  players reload with less club.
- **What it changes:** only tee shots after an OB on the same hole. It takes no extra random draws, so every other
  shot and hole is unchanged.
- **Tests it needs:**
  - this fixture finishes the hole;
  - rounds without an OB re-tee are identical shot for shot.
- **A broader fix, a separate balance question:** price the outside-of-the-dogleg shift in `_tee_plan` itself.
  Either fix also applies to main, which has the same latent defect.

Until a fix is approved, a long world on either build can stop this way, rarely: once in 22 full-scale seasons of
this run, and never in the main run's seasons so far.
