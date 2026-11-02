# runaway_2049_hole17.pkl

This is the state at entry to `engine.play_hole` for the hole that stopped the realism branch's full-scale seed-2027
world in its 2049 season (`build/realism-youth-aging-longirons` at `d619dd6`):
- the player before the hole;
- the hole;
- the round's random state;
- the hole state and the pin.

It was captured by re-running that season from the run's 2048 save with `play_hole` wrapped. Under the tee planner
of main `18a8e23` (which `d619dd6` shares), this state reaches the runaway guard: 29 consecutive tee shots out of
bounds through the dogleg. Diagnosis: `docs/review/realism/results/runaway_2049/RUNAWAY.md` on the realism branch.

It is a trusted local fixture (a pickle written by this project), and is used by `tests/test_tee_plan.py`.
