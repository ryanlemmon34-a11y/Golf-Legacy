# Arms comparison (build c0d1ea5): scripts and results

This folder holds a controlled same-seed comparison of the golf world simulator on one pinned build. All runs use build
`c0d1ea598bc7` (c0d1ea5; engine 1949ff6) with pinned seeds:

| arm | seed | seasons | work-pathway minimum age | college open access |
|---|---|---|---|---|
| `a21old` | 4207 | 10 | 21 | off (old member-first order, total-start rotation) |
| `a18old` | 4207 | 10 | 18 | off |
| `a18new` | 4207 | 10 | 18 | on (the build's defaults) |
| `seed2`  | 5309 | 5  | 18 | on (defaults) |

`ARMS_COMPARISON.md` is the report. `story_timing.json` holds the story-assembly timing on the pinned 45-season run A
archive (`runs/A/world_360013`, built by 473690a). In that file, paths are given relative to the work folder.

## Commands

From the folder that holds `arms/` and `runs/` (the default inputs), in `armsan/`:

    nice -n 19 ionice -c3 python3 -B analyze.py --publish          # report + this folder
    nice -n 19 ionice -c3 python3 -B analyze.py --arms a21old=DIR a18old=DIR a18new=DIR seed2=DIR --out FILE
    nice -n 19 ionice -c3 python3 -B analyze.py --stories          # also re-time stories (about 8 min, 2.7 GB peak, ~1.2 GB disk while running)

- `extract.py` reads each season file once and keeps a small summary in `armsan/cache/` (not published). A rerun only
  reads seasons added since the last run.
- `stories_timing.py` runs in its own process when `--stories` is given. Without that flag, the report uses the existing
  `story_timing.json`.

## Read-only method

- **Arm folders.** The scripts only read `manifest.json`, the run state (`seed_<s>.state.pkl`, saved every season, or
  `seed_<s>.json.gz`, saved every 5 seasons — whichever lists more seasons), `world_<s>/archive/MANIFEST.json`, and the
  season, people and relations files that manifest names.
- **Nothing is opened as a live world.** No World, Session or Archive object is opened on an arm, and nothing is written
  into an arm folder.
- **Committed seasons only.** A season is used only when it is both merged in the run state and published in the
  archive.
- **Story timing on run A.** The archive's own `index.sqlite` is never opened. That index is a database with an
  uncheckpointed write-ahead log, so opening it would mean writing a shared-memory file beside it. Instead, a mirror
  folder holds a copy of the run's MANIFEST and symbolic links to the files it names. The build's own
  `golfsim.archive.build_index_at` then builds a separate side index in a temporary folder, as the observer does for a
  history it does not own. That index is removed afterwards.

## Denominators

The report keeps two kinds of denominator apart, and never mixes them in one table:

- **ORIGINAL COHORT** tables follow a fixed set of the same people in both arms, chosen before the arms diverge. The
  denominator is the cohort's size.
  - Section 1 uses full-time, non-college amateurs aged 17–20 in 2028 (the 2028 rows are identical across the two arms
    except for two golfers, which the report names).
  - Section 2 uses the 2027 college players and series members. Those two arms differ from week 1, so membership comes
    from the 2027 season record, assigned when the world was created.
- **END-STATUS** tables re-take membership each season from end-of-season status (or a pathway entry during the
  season). Their makeup therefore differs between arms. They describe arm-level rates, not the same people.

From 2029 on, fewer than 1% of rows are identical between `a21old` and `a18old`. The same id in the other arm is
therefore not a counterfactual for that person, and the report makes no individual comparisons after 2028.

## Known limitations

- **Time to the job.** The weekly access outcome is not stored week by week. The time from the first counted blocked
  week to the job is rebuilt from the weekly availability recorded in the monthly plans (decision evidence /2). It is
  checked against the recorded `weeks_blocked`, and matched in every entry so far.
- **Home-club floor.** Whether the home-club floor (rather than the regional baseline) set a start's familiarity is not
  recorded per start. Starts at a home club found by country are counted as an upper bound. Each golfer's current
  home-club familiarity source is read from the people table, at the last season only.
- **Shut-outs.** Shut-outs from full ordinary open fields are golfer-weeks from the access ledger (`careers.denied`),
  not entries per event.
- **Run A's archive.** Run A was built by 473690a and predates some facts the candidate records. Every sampled story
  lists the pre-event win estimate as not recorded, so no upset is claimed, and some list results before 2027 as not in
  the retained history.
- **Story timing conditions.** The timing was measured with `nice -n 19` while two simulations ran on the same 4-CPU
  machine, so the times include that contention. The cold passes open the sample oldest first, so each story indexed
  at most two seasons inline. A latest-first open is timed separately.
