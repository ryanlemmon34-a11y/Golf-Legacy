# Build v15: what is in it, how to try it, and what is left

**Reviewed**: HAL's read-only review of commit `07cecee` (`main`, the v14 build). **Build**: branch `build/v15`
from `07cecee`; `main` is unchanged. Each item below is its own commit with its tests. Your paused world, its
history and the original installation were not touched: everything was run on disposable test worlds or on a
copy of the 50-season world (`world_2027`, made by engine 7334ffe; the original was only read, and its files
are unchanged: same 71 files, sizes and modification times before and after). No long simulation was run and
no playthrough resumed; nothing was bought or sent anywhere.

## The four review findings

| Finding | Fix | Regression tests |
|---|---|---|
| **A.** Golfers already holding a Britannia place from a completed qualifying-series event entered regional/final qualifying again (`earned_exemptions` skipped qualifying routes) | A place won in a completed qualifying-series event now counts as earned, allocated exactly as the field will be (exemptions first, then the series in the rules' order; a place passes down when its finisher is already in). A ranking cut-off not yet published stays pending: a projection never removes an attempt. Only the reference calendar's stage selection uses this. | `tests/test_review_v15.py`: a Challenger golfer outside the top 50 with no other exemption, and a golfer who entered final qualifying as played, each given a Heartland Invitational place -- neither enters regional or final qualifying (so no entry, no cost: costs are booked per finisher), a full final's place goes to someone else, and the place is in the field; a projected top-60 golfer keeps their USA local qualifying attempt; the allocation passes places down. Both A tests fail without the fix. |
| **B.** Hide results leaked winners in season recaps and the Career Grand Slam | Edition-level reveal rules applied to recaps (majors and champions, leading winners, moments), the Grand Slam line and page, records set by one hidden result, golf records, ranking points, a golfer's season page and status lines naming a hidden win. Aggregate pages keep their note (the possibility of inferring results from totals, already disclosed). | `test_review_v15`: a hidden major winner (recap, profile moments, season page, youngest-champions record, margins list); a hidden fourth major completing a Career Grand Slam (line and page; revealed again once watched). |
| **C.** A playoff's tie was shown against one round's par (283 on par 72 → +211) | The par of every regulation round (−5); older archives use the edition's round count. Display only. | `test_review_v15`: four-round and two-round playoffs; an older archive without extra holes or round scores. |
| **D.** "Watch from round 1" resumed at the remembered round | A separate restart link always opens round 1; Resume returns to the round last watched; neither reveals anything. | `test_review_v15`: after watching round 3, restart opens round 1 while the event page still resumes at round 3. |

## Features, in the order asked (each a separate commit)

| Commit | Item | State |
|---|---|---|
| 7ca96ff | Review fixes A-D | complete |
| 7b2809f | **Saved table views and navigation state**: every list's season, scope, filters, sort, direction and page (and a column sorted in the browser) are its address; the menu restores the last view (default one click away); detail pages offer "Back to" the last list view; named saved views kept with the world across sessions; golf statistics sort both ways. Browsing state only (`observer_views.json`). | complete (checked in a real browser: a column sort survives a profile, Back and the menu) |
| dddac48 | **Where are they now**: an edition's field, a tour's golfers in a season, a turning-pro class or an age group, each member by id, with then / now / seasons / wins / majors / best ranking / highest level / prize money / peak; every outcome counted (retired, club professional, amateur, lower tours). | complete for the recorded facts; the Peak column is "not recorded" for histories that predate peaks (the 50-season world) |
| 3fe8c96 | **My World**: grouped shortlist, everything shortlisted followed, a digest of recorded facts since last read (or a window), Hide results respected (held back and counted), a quiet menu count. | complete; the digest covers results, status changes, moments, ranking bands and followed editions -- not staff relationship changes (coaches and caddies are followed as people: their own results only) |
| f879274 | **Career comparisons**: up to four golfers; now, current Overall, Peak Overall, totals, season by season and at the same age; current vs start-of-season snapshot vs Recorded Peak kept apart; missing history shown as unavailable. | complete; on older histories without per-season top 10s or rating snapshots those rows read "not recorded" |
| 16a5a2f | **GOAT Lab**: ten components reused from the Stats directory, the majors list, the Records list and season-end rankings; editable weights or a checked formula (invalid ones reported, never run); deterministic ties; components, definitions, scope and coverage shown; partial careers and missing figures marked. | complete; the Peak component is the engine's noted peak (a profile may also show start-of-season ratings from before peaks were kept) |
| 1a97b37 | **Qualification evidence**: this season's majors -- earned/conditional places (identical to the engine's own on the reference calendar), pending cut-offs with their weeks, qualifying to come, projections marked as information only; `docs/STANDINGS_AND_RIGHTS.md` (generated from the calendar and card rules, both calendars); the zero-start investigation by region and circuit with affordability evidence and recommendations. | views and document complete; the zero-start changes await your decision (nothing implemented) |
| 0297e84, 9a150cb | **Browsing speed**: per-season extracts and one weeks-at-No.1 count per reading (exact results). | complete |

## Qualification and participation evidence

- **Projected vs earned** (`/qualification`): see above. A projection is never a place: the engine never reads
  the view; the test shows projected golfers keep their qualifying attempt.
- **Standings locks and rights** (`docs/STANDINGS_AND_RIGHTS.md`, also `/standings`): each money list's events,
  first week and lock week; what it decides (cards decided after week 52, effective week 1 next season); the
  Q-Schools (the classic calendar's week-2 Asian final waits 51 weeks for its cards; the reference calendar's week
  51 final, one week); major cut-offs; late-season lists (Premier Tour Europe locks in week 50, Asia-Pacific 49,
  Japan 48, several regional and mini tours in week 52). A test regenerates it and fails if it drifts.
- **Full-time amateur zero starts** (`docs/ZERO_START_REVIEW.md`, new section): Europe and Asia are
  affordability (71-83 % of the zero-start weeks; every golfer with a zero-start 2076 season starts 2077 in debt
  with no family money left; their circuits cost $6.4-6.7k a season against $3.4-3.6k in North America and
  Oceania); Africa, Latin America and Oceania are mostly "no suitable event"; North America's barrier is full
  fields (69 % of all weeks) but almost nobody plays nothing; injuries and choices play no part; 42 % of these
  seasons repeat because the move to working comes a season late. Recommendations are recorded for your decision.

## Performance (measured; simulation, saving and browsing reported separately)

Machine: Intel Xeon @ 2.10 GHz, 4 logical CPUs, 15.7 GB, Python 3.13 (not your laptop). Worlds: disposable
copies of the 50-season world (13,152 active golfers, 43,683 people); nothing was run on your world.

**Simulation and saving: no change, and none intended.** This build's speed work is in history browsing; the
simulation code the classic calendar runs is unchanged (finding A's fix is used only by the reference
calendar's qualifying stages). Season 51 skipped end to end (`tools/benchmark_skip.py`), `main` and this branch
alternated, two runs each:

| Season 51 | Skip (s) | Simulate (s) | Save (s) | Publish, settle, reload, overview (s) |
|---|---|---|---|---|
| `main` 07cecee | 231.7 / 231.7 | 194.8 / 194.5 | 18.0 / 18.3 | 18.9 / 18.9 |
| `build/v15` | 228.6 / 225.6 | 193.5 / 189.7 | 16.9 / 17.7 | 18.2 / 18.2 |

The differences (1-3 %) are within run-to-run noise. The same skip measured 202.6 / 204.4 s on this machine
earlier on 30 October (v14 report): the shared machine is slower today, which is why the two builds were run in
pairs. Season 1 was not re-measured in this build. **The two-minute goal is not achieved** (about 230 s at season
51 here), and **season 100 remains unmeasured**: no season-100 checkpoint exists and none was made; no
extrapolation is given as a benchmark.

**Equivalence.** A classic-calendar world (seed 73, 3 % population, fixed hash seed) played 112 weeks (two season
ends) on `main` and on this branch: identical results, round scores, prizes, golfers (ratings, status, tour,
money), entry routes, cards and world ranking.

**History browsing** (exact results: 23 pages, each drawn twice, byte-identical before and after the change on
the 50-season copy). Times in seconds, first view / repeat view, with the statistics store and the records cache
already built:

| Page | Before | After |
|---|---|---|
| a long career's profile (6 seasons read) | 3.7 / 6.4 (every view) | 5.1 / 0.05 |
| other profiles of long careers | 0.7-5.6 (every view) | 0.6-2.6 / 0.01-0.03 |
| GOAT Lab, after the weeks-at-No.1 list | 41.6 / 0.4 | 0.25 / 0.25 |
| Standings locks | 0.9 / 1.7 | 0.65 / 0.001 |
| Where are they now (field / tour class / age group) | -- | 0.06-0.79 / 0.02-0.15 |
| Compare careers (three) | -- | 0.01 / 0.01 |
| Stats, Prize money, Moments, Golfers, Season | 0.01-1.6 (not changed by this build) | same |

**First opening of an older history** (the 50-season world's archive was written by an engine whose index has no
No. 1 table; each cost is paid once and then cached beside the world, or in a temporary folder for a history
browsed read-only): the statistics store 127 s (in the background; pages say so), the records statistics 41 s,
weeks at world No. 1 36-53 s (it reads all 50 season files). A world copied and continued on this build upgrades
its own index once (113 s on the copy, before its first page). Worlds made by the current engine have the table
and answer in one query.

**What remains, and needs your decision** (unchanged from `docs/PERFORMANCE_REVIEW.md`): per-golfer random
streams (parallel planning; results differ from that point on: a new engine for new worlds), an incremental
checkpoint format (the season-end save, about 17 s here, grows with the world), or declaring outcome-equivalent
engines (a guard relaxation). An exact-result candidate that needs no decision: build the newer index for an older
history in the read-only cache too, so its first Records or GOAT Lab opening does not read every season file.

## Tests

**Whole suite** on the final code (9a150cb; every module, six at a time): **46 modules, 495 tests, all passed**
(1 skipped by design, as before: `test_observer_profiles`). Nothing failed or was re-run.

New in this build (58 tests): `test_review_v15` 10, `test_views` 8 (one drives Chromium through Node's
Playwright: a column sort survives opening a profile, Back and the menu), `test_cohort` 7, `test_myworld` 7,
`test_compare` 5, `test_goat` 8, `test_qualification_views` 9, `test_zero_start_regions` 2,
`test_browse_extracts` 2. Two existing tests changed with the code they test: `test_observer_profiles` reads the
shortlist's new four-field entries; `test_golf_stats` patches the rankings reader the position lookup now uses
(same assertion).

**Limits.** The tests use small worlds (2-5 % population; finding A's Challenger case needs 15 %, the smallest
population with Challenger tours). The 50-season checks (cohorts, comparisons, the GOAT Lab, the zero-start
investigation, browsing times) were run by hand on a disposable copy, with the results above. The reference
calendar is still unproven at full size over many seasons (not run: no long simulation in this increment).

## Roadmap status

- **Completed in this build**: the four review fixes; saved views and navigation state; Where are they now; My
  World; career comparisons; the GOAT Lab; projected vs earned qualification views; the standings-lock
  document; the zero-start investigation by region and circuit (investigation only).
- **Partially complete**: My World does not yet digest staff relationship changes; Where are they now and the
  comparisons show peaks and rating snapshots only where the history recorded them; the first opening of an
  older archive's Records and GOAT Lab is slow (below).
- **Awaiting your decision**: the zero-start recommendations (career decision timing; amateur costs or event
  density by region); the performance options (per-golfer random streams, an incremental checkpoint format,
  outcome-equivalent engines, upgrading an older archive's index); the parent/child tour filter; migrating an
  existing world to the reference calendar.
- **Deferred** (not part of this increment, still on the roadmap): nation development and other large
  simulation expansions; a day-ordered same-week feeder engine; season-100 timing.
- **Blocked**: the Test1 archive on Google Drive (not reachable from the build environment).

## How to try it safely

`docs/OBSERVER_ALPHA.md`, "Trying the v15 build": download the `build/v15` branch into a **new folder**, copy
(never move) a world into its `worlds` folder or create a small one, and open it there. v15 changes the engine
fingerprint (the qualifying fix and the records counter are engine files), so a world from `main` shows as
"another engine": browse it read-only, or Copy it with "continue with this engine" (classic-calendar results
are identical to `main`: tested over two season ends). Your current installation and world are untouched.

## Recommended next validation pass

1. Open a **copy** of your paused world in v15 read-only: check Hide results on recaps, the Grand Slam page and
   My World; use saved views and "Back to" while browsing; open a college championship's "where is this field
   now?".
2. On a new reference-calendar world, play to week 27 and check one Britannia qualifying-series winner's
   profile: no regional or final qualifying entry, the place in the field.
3. Decide on the zero-start recommendations and the performance options; a measured season on your laptop with
   `RUN_BENCHMARK_WINDOWS.bat` would give the first real numbers from your machine for this build.
