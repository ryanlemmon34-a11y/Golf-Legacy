# Realism pass 1: how to test this branch

**What this is:** branch `build/realism-youth-aging-longirons`, from main `18a8e23`, plus the reviewed engine fix for
the runaway hole (`fix/engine-dogleg-retee`, merged at `c6ce161`). It is an **experimental playtest build**, not
calibrated balance; see `RESULTS.md`. Main is unchanged.

**The baseline to compare against is main + the same engine fix:** `fix/engine-dogleg-retee` at `46013a5`. Plain
main lacks the fix, so on doglegs it plays differently from both test builds.

## Try it in the observer, in separate folders (your current checkout and local work are untouched)

From your existing clone of the repository:

```
git fetch origin build/realism-youth-aging-longirons fix/engine-dogleg-retee
git worktree add ../golf-realism-test origin/build/realism-youth-aging-longirons
git worktree add ../golf-mainfix-test origin/fix/engine-dogleg-retee
```

The realism build:

```
cd ../golf-realism-test
git log --oneline -1
python tools/observer_app.py --worlds worlds-realism-test --workers 1 --open
```

The baseline (main + fix), side by side on another port:

```
cd ../golf-mainfix-test
python tools/observer_app.py --worlds worlds-mainfix-test --workers 1 --port 8766 --open
```

Each command uses its own new library folder (`worlds-realism-test`, `worlds-mainfix-test`) inside its worktree, so
no existing world is touched. `--workers 1` keeps memory low; leave it out to use all cores.

**Make the comparison like for like:** in each library, create a new world with the same seed and starting year.
- New worlds on the realism build use the new development rules (`dev-2`), and Rules shows version `2026-11-16`.
- Worlds created earlier on main keep `dev-1` if opened here. They do get both engine-wide changes: the long-irons
  table and the dogleg tee-plan fix.

## What to look at

- **Juniors (from the first winter):**
  - few 18-year-olds start within 3–5 points of their potential;
  - prodigies still enter very high (in the 90s) and climb within a few seasons;
  - potential stays hidden on profiles.
- **Aging (from the late 30s):**
  - distance, stamina and recovery fall away more steeply than on the baseline, and differently for each golfer;
  - there is no forced retirement and no universal age cliff;
  - green reading keeps improving with experience into the 40s.
- **Long irons:**
  - weak golfers' long-iron ratings between 25 and 60 now matter a little;
  - from 60 up the long-irons table is unchanged. Rounds there are bit-identical only where the dogleg fix does not
    trigger.
- **Doglegs, both builds:** a long hitter no longer reloads the same club after hitting out of bounds through a
  corner.

## Tests (from the realism worktree)

```
python -m unittest tests.test_realism_pass1 -v
python -m unittest tests.test_tee_plan -v
python docs/review/realism/measure.py measure-out.json --years 2028-2047 --procs 4
python docs/review/realism/summarise.py measure-out.json
```

- `tests.test_realism_pass1`: 12 tests.
- `tests.test_tee_plan`: 11 tests, the engine fix.
- `measure.py`: the paired projections over five seeds; about 10–20 minutes.

A full-scale paired world, the slow check (about 2–3 hours per 30 seasons on a 4-core machine):

```
python tools/long_world.py --seeds 2027 --years 30 --workers 2 --out long-realism-2027
cd ../golf-mainfix-test
python tools/long_world.py --seeds 2027 --years 30 --workers 2 --out long-mainfix-2027
cd ../golf-realism-test
python docs/review/realism/compare_worlds.py ../golf-mainfix-test/long-mainfix-2027 long-realism-2027 2027
```

Results, provenance and limits are in `RESULTS.md`; targets and rationale are in `PLAN.md`.
