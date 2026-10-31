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
- `upset_cost.py` measures the upset records' bytes (a18new, seed2) and the offline recomputation CPU, and writes
  `upset_cost.json`, which the report reads. Run it separately (about 30 s):

      nice -n 19 ionice -c3 python3 -B upset_cost.py

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

- **Fixed cohorts** follow a set of the same people in both arms; the denominator is the cohort's size. Section 1 has
  three, never pooled:
  - **PRETREATMENT:** full-time, non-college amateurs aged 17–20 in the shared 2027 baseline. The two arms' 2027 rows are
    identical.
  - **ARRIVAL:** juniors created for 2028, defined by their creation record: the season file's `diagnostics.created`
    plus their arrival history line. Verified identical in both arms for the extracted creation fields (path, age,
    Overall, week), the arrival line and identity (name, birth year, country). Full attributes and ceilings were not
    compared.
  - **FIXED COHORT selected by the control arm's (a21old) end-2028 status:** the same people in both arms, but chosen
    after the divergence in week 45 of 2028, so not pretreatment.
  - Section 2's cohort is fixed at creation (pretreatment): the 2027 college players and series members. Their tour and
    residence are the creation values; the report cites the code for this and checks it against the people table's
    `first_residence`.
- **END-STATUS** tables re-take membership each season from end-of-season status (or a pathway entry during the
  season). Their makeup therefore differs between arms. They describe arm-level rates, not the same people.

No table is a causal claim about an individual. Differences between arms within a fixed group are descriptive, arm-level
differences: the worlds diverge, so other people and events differ too. From 2029 on, fewer than 1% of rows are
identical between `a21old` and `a18old`, so the report makes no individual comparisons after 2028.

## Known limitations

- **Pathway timing.** The weekly access outcome is not stored week by week. The report reconstructs only the last n plan
  weeks compatible with each entry's recorded `weeks_blocked`. It uses the monthly plans' recorded availability (decision
  evidence /2), not actual weekly access.
  - "Compatible" means the plan data do not contradict the stored count. It is not an independent check, because the
    walk stops at n.
  - The span is not a measured time from the first blocked week, and no exact timing is claimed.
  - A plan-based scan past n is reported separately.
- **Starts after the job.** "Season starts in Y" includes starts made before the job. Starts from the decision week on
  are counted from the weeks of the editions whose finishes list the golfer.
- **Home-club floor.** Whether the home-club floor (rather than the regional baseline) set a start's familiarity is not
  recorded per start. Starts at a home club found by country are counted as an upper bound. Each golfer's current
  home-club familiarity source is read from the people table, at the last season only.
- **Shut-outs.** Shut-outs from full ordinary open fields are golfer-weeks from the access ledger (`careers.denied`),
  not entries per event.
- **Entrant allocations.** For each arm's last season there is no next archive season, so its arrivals are "not
  verified". A supplementary check from the people table's `created` year and the arrival ages the code defines is
  shown separately and is not counted as verified.
- **Venue moves.** None were decided in the default arms, so natural activation and the rule's calibration are not
  exercised by these runs. The trigger funnel is reconstructed from retained prestige data and the build's static course
  plan. The positive evidence that moves happen is the regression tests in tests/test_venue_moves.py.
- **Story timing (section 4)** is evidence for indexed story assembly only.
  - It calls `observer_stories.tell`, and does not cover full UI rendering or the owner's hardware.
  - "Cold" means application-cache cold, not filesystem cold.
  - The sample is 20 majors from the legacy 473690a archive (run A), assembled by the candidate build.
  - The 2.65 GB RSS is a lifetime high-water mark, not a per-story allocation, and does not show the absence of a leak.
  - Times shown as 0.000 s are below the timer's displayed precision.
  - Pre-event upset estimates are missing because the legacy archive predates them; new-world upset stories are covered
    by tests/test_upset_examples.py and tests/test_stories.py.
  - The timing was measured with `nice -n 19` while two simulations ran on the same machine.
  - Neither instant cold UI opens nor the local 120 s season target are claimed.
- **Venue-move gaps.** Archived prestige values are rounded to 0.01, so a gap within ±0.01 of the 5-point threshold
  cannot be classified with certainty. The report counts those event-seasons. Natural move frequency remains
  unvalidated.
- **Amateur return (section 5).** Episodes come from the winter transitions; evaluations, p = 0 included, come from
  decision evidence /2 (`amateur_return` rows).
  - Returns in an arm's last season are censored, not successes.
  - Episodes are not independent people; unique people are counted separately.
  - Pooled tables sum episodes from different worlds and carry no causal reading.
- **Upset cost (section 6).**
  - "gzip alone" compresses the upset records by themselves, an approximation of their share inside the whole-file
    compression.
  - The CPU figure is an offline recomputation from the stored inputs (`golfsim.upsets.reproduce`). It excludes the
    fact capture at field-set time and any engine-side bookkeeping, so it is not the in-engine overhead.
