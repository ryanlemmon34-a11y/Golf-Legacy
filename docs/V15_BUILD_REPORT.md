# Build v15: what is in it, how to try it, and what is left

**Reviewed**: HAL's read-only review of commit `07cecee` (`main`, the v14 build), then HAL's review of `0d4576b`
(the stabilization pass, next section). **Build**: branch `build/v15` from `07cecee`, merged into `main` after
the stabilization pass with your approval. Each item below is its own commit with its tests. Your paused world, its
history and the original installation were not touched: everything was run on disposable test worlds or on a
copy of the 50-season world (`world_2027`, made by engine 7334ffe; the original was only read, and its files
are unchanged: same 71 files, sizes and modification times before and after). No long simulation was run and
no playthrough resumed; nothing was bought or sent anywhere.

## Stabilization pass (HAL's review of 0d4576b)

**Build**: `build/v15`, commits `9164d35` (Hide results removed), `8fb37c7` (the five findings) and the
commit carrying this report (a comparison total, an exact speedup of the peak read, the documents); merged
into `main` with your approval ("you can push all of the changes to the main"). No newer commits existed when the pass began. No simulation state, tournament outcome or archived history
was changed: every change is in the observer (`tools/observer*.py`), which only reads a world. Your paused
playthrough was not resumed, no long simulation was started, the original 50-season save was only read (same
files, sizes and modification times before and after) and its calendar was not migrated.

### Hide results: removed

**Removed** (code, tests and documentation): the header's *Hide results* control and its `/spoilers` route; the
`observer_spoilers` module (the per-world setting and its boundary, each event's reveal state and remembered round,
*Reveal final*, the resume-at-round link, the hidden-result counters, masking and redaction); every use of it --
season recaps (majors and champions, leading winners, moments), the Career Grand Slam line and page, records set
by a single result, golf records (longest drives, event driving averages, margins, match-play wins and their
"rows left out" counts), ranking-points rows, a golfer's season page and status lines naming a win, the
tournament summaries and calendar, course, nation and tour pages, the overview, a profile's results, cohorts,
comparisons, qualification projections, My World's held-back counts,
and the GOAT Lab's majors and Grand Slam components; the aggregate-page warnings; `tests/test_spoilers.py`; the
documentation of the setting. No other global spoiler mechanism replaces it.

**Every view uses the complete recorded results**: profiles, recaps, records, cohorts, comparisons,
qualification, My World and the GOAT Lab read the same history whatever an old setting said. The GOAT Lab's
majors and Career Grand Slam components count exactly the Grand Slam page's majors (tested with the old setting
planted, hiding everything).

**Replay kept**: an event page opens on its final result; *Rounds* shows the leaderboard after any round chosen
(nothing after that round: no winner, final places or later rounds), scorecards up to that round, a playoff at
the final round, and *Watch from round 1*, which always opens round one. The replay is now stateless (nothing is
remembered or written), so restart and the final result cannot disagree; "resume" existed only for hiding and
went with it.

**Old settings files** (`observer_spoilers.json` from earlier builds) are never applied, never written and never
deleted; a world with one opens normally (a malformed file is ignored). **My World**: the only use of the old file
is its date boundary. If the digest was marked read after hiding began, items in that period may never have been
seen, so My World shows one line -- "items from <week> to <week> may not have been shown" -- with *Review that
period* (the digest for exactly that window, every item in it) and *Dismiss*. The read marker is not rewritten,
nothing is flooded back as unread or counted again as new, and the shortlist is kept.

### The five findings

| | Finding | Fix | Regression tests (each fails on the previous code) |
|---|---|---|---|
| A | `sqrt(1,2)` and `min(1)` passed validation, then raised a TypeError | Per-function value counts (sqrt and log one; min and max 2-8), checked before anything is evaluated, with a message naming the function and the count ("sqrt() takes exactly 1 value (given 2)"); evaluation errors (division by zero, log of 0 or a negative, square root of a negative, complex powers, overflow, non-finite results) leave that career out and are counted. The restricted evaluator is unchanged. | `test_goat`: wrong counts (8 formulas, nested ones included), 15 impossible values, valid formulas with exact results; the page with wrong counts, with every career impossible and with some careers impossible -- it always renders. |
| B | GOAT peaks read only the last archived season and the live snapshot | `observer_data.recorded_peaks`: the profile's `recorded_peak` for many golfers at once (every archived season's noted peak and start-of-season rating, the current snapshot; the highest value, its earliest date), read in bulk and kept per reading of the history. The GOAT Lab and cohorts both use it; nothing is invented. | `test_goat_peaks`: four archived seasons; golfers whose last season was the first, reopened archive-only (no live snapshot): the GOAT value and its contribution to a custom score (weight 2 on Peak only) equal the profile's peak; the same with a live world; the batch helper equals the profile's for 400 golfers, live and archive-only. `test_cohort`: an older index shows no peak, as the profile does. |
| C | Cohort prize money ignored the current season | The current season so far is added once; once that season is archived it is counted from its row only. A season row without prize money makes the figure "partial", never a silent $0. | `test_cohort`: a first-season paid winner (field of a current-season event), amateurs paid nothing ($0, known), a multi-season career (archived rows + this season), a season without prize money (partial), a refresh (identical), and a real season end (week 51 -> 52 -> archived: counted once, the same after a reload, and not added again if the snapshot still names the archived season). |
| D | My World used today's ranking for any current-season week | Each end of the window reads the ranking published that week: the current season's weekly snapshots or the archived season (week 0 = the previous season's final ranking). If a week's ranking was not recorded, nothing is claimed (never another week's ranking in its place). | `test_myworld`: No. 12 -> No. 8 ("now in the top 10"), reaching No. 1, losing No. 1, leaving the top 10, in and out within the window (no item), a missing week, the season boundary (last season's No. 1 now No. 30), marking the digest read and a later week bringing exactly one new item. |
| E | Save view kept the query from before a browser column sort | The sort script updates the form with the address it writes. | `test_views` (Chromium via Node Playwright): Golfers filtered (name, status), server-sorted, page 2; sort a column in the browser; name and save without reloading; leave; reopen from *Saved views*: same order, filters, sort and page; refresh, Back and Forward keep it. |

**Also fixed in this pass**: a golfer with no finance ledger in the current season has been paid nothing (the
archive records $0 when the season ends); profiles, comparisons and the season page said "not recorded" and now
say $0, as cohorts do. A comparison's career prize total with a season that did not record prize money now
reads "unknown" (as the profile's career total does) instead of counting it as $0. The statistics store could
raise a UNIQUE error when two readers opened a new store at the same moment (seen once in the suite); its schema
row is now written idempotently.

### Validation

- **Whole suite** (every module, six at a time, 18 minutes): **47 modules, 509 tests, all passed** (1 skipped by
  design, as before: `test_observer_profiles`). It ran on `8fb37c7` plus the comparison's prize total (its new
  test ran in it). After it, one exact speedup went into the batch peak read (a career row containing neither a
  noted peak nor ratings is not decoded); the four modules that use it were run again on the final code:
  `test_goat_peaks` 3, `test_cohort` 10, `test_goat` 11 and `test_compare` 6 tests, all passed.
- **The new tests fail on the previous code** (a separate checkout of `9164d35` with the new test files): A 3 of 3
  (`sqrt(wins, 2)` broke the page with a TypeError; complex values escaped), B 3 of 3 (the retired golfer's
  archive-only peak was missing instead of 46.7; the GOAT row said "missing"), C 5 of 5 (a first-season winner
  showed $0; this season's money was missing; an older index showed another season's peak), D 4 of 4 (no band
  change within a season; today's No. 2 used for last season's final week, where the golfer was No. 1), E 1 of 1
  (the saved query lacked the browser sort).
- **Kept working** (in the passing suite): the Britannia qualifying-series places and the playoff par
  (`test_review_v15`), every playoff participant in the records (`test_playoffs`), the replay and *Watch from
  round 1* (`test_complete_history`, which plants an old setting hiding everything and checks 18 pages).
- **The 50-season copy** (disposable copies only), browsed read-only (whole world, and its archive alone) and with
  the live snapshot (a second copy opened as a session, which upgrades that copy's index: 243 s before the first
  page): 18 pages each -- overview, a champion's profile, the GOAT Lab (default, Peak weighted, retired careers,
  wrong value counts, every career impossible, some impossible), two cohorts, a comparison, My World, a recap,
  the Grand Slam page, a records list and a replay -- with an old Hide results file planted: no page failed and
  none hides or mentions hiding. For 250 careers (the GOAT top 150 and 100 from the middle), majors (Grand Slam
  page, GOAT Lab, comparison, cohort), wins (Stats, comparison, cohort), prize money (Stats, comparison, cohort)
  and peak (profile, GOAT Lab, cohort) agree in all three modes. The batch peak equals the profile's for every
  golfer sampled (400 per mode, and 500 of all 49,378 people). That world's engine recorded neither peaks nor round
  scores, so Peak reads "not recorded" for its retired golfers everywhere (active golfers have the current
  rating, as their profiles show) and its replay says round scores were not recorded.
- **Your original world**: only read; its 71 files have the same sizes and modification times as before the pass.

### Remaining discrepancies and limitations

- **Prize money precision**: an archived season is kept in whole dollars, the current season's ledger in cents,
  so a cohort or profile figure can drop by less than $1 when its season is archived (seen in the season-end
  test: $11,874,635.18 so far, $11,874,635 archived).
- **Unknown prize money is presented two ways**: a cohort shows the partial sum marked "partial"; a profile's and a
  comparison's career totals show "unknown". The same fact, worded differently. (Every season row written so far
  records prize money; this arises only for an incomplete archive.)
- **GOAT score rounding**: the score and each contribution are rounded to one decimal separately, so they can
  differ by 0.1 (1.5 x 46.7: score 70.0, contribution +70.1). Display only; the ranking uses the exact values.
- **Peak cost on long histories**: the first all-tours GOAT ranking that uses Peak reads every career row once
  per reading of the history: 8.8 s on the 50-season copy (no peaks to decode), about 40 s estimated for a
  50-season world from the current engine (63 microseconds per row measured on a four-season world). The default
  weights do not use Peak; repeat views take milliseconds.
- **My World ranking bands**: a world's first season has no start-of-season ranking kept (the seeded ranking is
  not a snapshot), so its "this season" window shows no band changes; an archived season from before ranking
  points were kept uses its top-100 order. A save from before weekly snapshots were kept compares only against
  the current table.
- **Replay on old histories**: *Watch from round 1* is still offered where round scores were not recorded; the
  page then says so (nothing is reconstructed).
- **Tests** use small worlds (2-5 % population); the four-season archive test takes 5-9 minutes. The 50-season
  checks were run by hand (above), not as unit tests.
- **Not in this pass** (no interface features were added): My World still does not digest staff relationship
  changes; it is on the roadmap with richer staff relationship history. Next priorities: believable career and
  financial decisions, evolving nations, richer staff relationship history (`docs/BACKLOG.md`).

## The four review findings

| Finding | Fix | Regression tests |
|---|---|---|
| **A.** Golfers already holding a Britannia place from a completed qualifying-series event entered regional/final qualifying again (`earned_exemptions` skipped qualifying routes) | A place won in a completed qualifying-series event now counts as earned, allocated exactly as the field will be (exemptions first, then the series in the rules' order; a place passes down when its finisher is already in). A ranking cut-off not yet published stays pending: a projection never removes an attempt. Only the reference calendar's stage selection uses this. | `tests/test_review_v15.py`: a Challenger golfer outside the top 50 with no other exemption, and a golfer who entered final qualifying as played, each given a Heartland Invitational place -- neither enters regional or final qualifying (so no entry, no cost: costs are booked per finisher), a full final's place goes to someone else, and the place is in the field; a projected top-60 golfer keeps their USA local qualifying attempt; the allocation passes places down. Both A tests fail without the fix. |
| **B.** Hide results leaked winners in season recaps and the Career Grand Slam | Edition-level reveal rules applied to recaps (majors and champions, leading winners, moments), the Grand Slam line and page, records set by one hidden result, golf records, ranking points, a golfer's season page and status lines naming a hidden win. Aggregate pages keep their note (the possibility of inferring results from totals, already disclosed). | `test_review_v15`: a hidden major winner (recap, profile moments, season page, youngest-champions record, margins list); a hidden fourth major completing a Career Grand Slam (line and page; revealed again once watched). |
| **C.** A playoff's tie was shown against one round's par (283 on par 72 → +211) | The par of every regulation round (−5); older archives use the edition's round count. Display only. | `test_review_v15`: four-round and two-round playoffs; an older archive without extra holes or round scores. |
| **D.** "Watch from round 1" resumed at the remembered round | A separate restart link always opens round 1; Resume returns to the round last watched; neither reveals anything. | `test_review_v15`: after watching round 3, restart opens round 1 while the event page still resumes at round 3. |

*Superseded by the stabilization pass*: Hide results (finding B) and the remembered round behind "Resume"
(finding D) have been removed; every view shows the complete history, and "Watch from round 1" still always
opens round one. Findings A and C stand, with their tests.

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

1. Open a **copy** of your paused world in v15 read-only: recaps, the Grand Slam page, My World (if the world
   used the old Hide results setting, the one-line review notice) and an event's replay with *Watch from round
   1*; sort a list in the browser, *Save view*, reopen it; use "Back to" while browsing; open a college
   championship's "where is this field now?"; in the GOAT Lab try a formula with a wrong number of values.
2. On a new reference-calendar world, play to week 27 and check one Britannia qualifying-series winner's
   profile: no regional or final qualifying entry, the place in the field.
3. Decide on the zero-start recommendations and the performance options; a measured season on your laptop with
   `RUN_BENCHMARK_WINDOWS.bat` would give the first real numbers from your machine for this build.
