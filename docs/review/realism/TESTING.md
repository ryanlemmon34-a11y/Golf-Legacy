# Realism pass 1: how to test this branch

Branch `build/realism-youth-aging-longirons`, from main `18a8e23`, plus the reviewed engine fix for the runaway
hole (`fix/engine-dogleg-retee`, merged at `c6ce161`). Experimental, ready to test, not validated as long-career
balance. Main is unchanged.

## Try it in the observer

```
git checkout build/realism-youth-aging-longirons
python tools/observer_app.py --worlds <a new library folder> --open
```

Create a new world in the library. New worlds use the new development rules (`dev-2`), and Rules shows version
`2026-11-16`. Worlds created on main keep `dev-1` if opened here, but they get the long-irons table, which is
engine-wide.

What to look at:
- **Juniors (from the first winter):** few 18-year-olds start within 3–5 points of their potential. Prodigies still
  enter very high (in the 90s) and climb within a few seasons. On their profiles, potential stays hidden.
- **Ageing (from the late 30s):** distance, stamina and recovery fall away more steeply than on main, and differently
  for each golfer. There are no age thresholds and no forced retirement. Green reading keeps improving with
  experience into the 40s.
- **Long irons:** weak golfers' long-iron ratings between 25 and 60 now matter a little. From 60 up nothing changes.

## Tests

```
python -m unittest tests.test_realism_pass1 -v      # 12 tests
python -m unittest tests.test_tee_plan -v           # 11 tests (the engine fix)
python docs/review/realism/measure.py OUT.json --years 2028-2047 --procs 4      # paired projections, five seeds
python docs/review/realism/summarise.py OUT.json
python tools/long_world.py --seeds 2027 --years 30 --out DIR                    # full-scale world (compare with main)
python docs/review/realism/compare_worlds.py MAIN_DIR BRANCH_DIR 2027
```

Results, provenance and limits are in `RESULTS.md`; targets and rationale are in `PLAN.md`.
