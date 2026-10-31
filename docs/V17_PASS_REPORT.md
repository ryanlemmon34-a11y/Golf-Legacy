# Pass of 31 October 2026: HAL's review of 324e263, the expanded roadmap, fresh worlds only

**Asked for**: the owner's prompt of 31 October (HAL's review of `build/v16` at `324e263`; the expanded roadmap as the
full pre-playthrough scope; where they differ, the prompt wins: no old-world compatibility, no resuming previous
saves). **Branch**: `build/v16` (no merge: that needs a separate approval). Nothing was deleted; no old world was
continued; no multi-hour run was started.

## Completed (each package its own commit, with its tests)

| Package | Commit | Changes simulation? | What |
|---|---|---|---|
| 1. Review fixes | `5fdc76b` | **Yes** (injury length) | Staff seasons end-exclusive (week-1 ends, reunions, archive bounds); first appearance back counts qualifying, first main event shown apart; an injury announced as n weeks keeps a golfer out of exactly n weeks of entries (across the year end too); the recorded per-pair fit and rapport shown on both profiles (the v16 report's claim corrected); inaugural Masters invitees documented under the major-trip guarantee; all-majors funding tests |
| 3. Qualification windows | `c28bf77` | No | Every windowed route's rule, current-edition handling and exact expiries (`docs/QUALIFICATION_WINDOWS.md`), boundary tests for today's definitions, one policy choice flagged |
| 2. Fresh worlds only | `dd0bb27` | No | Unsupported saves (earlier engine, older format, classic calendar) named with reasons: browse and copy only, never continued, changed or deleted; new worlds always v2; checkpoints record their calendar |
| 4. Long histories | `17c673b` | No | A world's index validated and missing or stale seasons rebuilt on opening; a side index outside the folder for read-only histories; exports include the index by default |
| 5. Coaches and Prestige | `32bc43d` | No (shown identical) | Coach teaching and scouting shown and recorded each season; Prestige for every golfer (profile, season rows, sortable directory) and for coaches and caddies (their reputation, by role); recruitment design note |
| 6. Amateur support | `138ce06` | **Yes** | Bands A/B/C ($25k/$12k/$5k) as an initial calibration, in kind for events, caddie and coaching; observable eligibility; week-1 budget, in-season A/B upgrades, one-band renewal decline; ends on turning pro or retiring; payment order school/club, support, golfer, organizer; every payment recorded; measured over three seasons |
| 7. Reconciliation and validation | `9f8525b`, `6a9e065`, `e615b2e`, this commit | No (`e615b2e`: archive fix) | Roadmap status (`docs/BACKLOG.md`), long-run plan for approval (`docs/LONG_RUN_PLAN.md`), this report |

## Amateur support, measured (initial calibration)

The same full-population world (seed 2027, reference calendar) played three seasons on the baseline (`32bc43d`,
the build just before amateur support) and on this build. Seasons took 157-172 s either way (4 CPUs, two worker
processes each, both runs side by side).

| Season | Recipients (A / B / C) | Drawn | Events / coaching | Upgraded in season | Renewed a band lower | Ended: turned pro |
|---|---|---|---|---|---|---|
| 2027 | 189 (18 / 68 / 103) | $1.07 m | $1.01 m / $0.07 m | 34 | 0 | 35 |
| 2028 | 214 (32 / 77 / 105) | $1.25 m | $1.13 m / $0.12 m | 49 | 2 | 32 |
| 2029 | 229 (27 / 76 / 126) | $1.23 m | $1.14 m / $0.09 m | 45 | 15 | 41 |

- **More recipients and more money than estimated**: 189-229 contracts (estimate about 150: titles, places,
  scouting and renewals add recipients, as expected) and about $1.1-1.25 m drawn a season (estimate $0.4-0.7 m).
  Recipients use most of their cap. Nothing was paid for caddies (amateurs rarely employ one).
- **Career effects so far, the 150 amateurs ranked 1-150 when the world began**: by the end of 2029, 81 had turned
  professional with support against 72 without; 97 were still amateurs against 103; those still amateur played
  19.2 events in 2029 against 17.7, and none had a season without a start against 3.
- **Everyone else**: amateurs as a whole played the same (15.0 events a season against 14.9).
- **Unranked full-time adult amateurs**: none yet in a three-season-old world; the work pathway evidence is Test 1's
  (`docs/AMATEUR_WORK_PATHWAY_PROPOSAL.md`).
- Three seasons and one seed: early effects only. The funding comparison runs B and C of `docs/LONG_RUN_PLAN.md`
  measure ten seasons.

## Long histories, measured (Test 1 10.30 copy, 57 seasons, read-only, with this build)

Built once, in the background, separately from page loads: the side index 246 s (1,351 MB), the statistics store
268 s. Then, first load / repeat: Harper's profile 1.1 s / 0.02 s (651 s without an index on `eba01e1`, 243 s after
`70ed2d5`); ratings changes 0.03 s; results 0.04 s; team 0.01 s; the coach with the most partnerships (59) 0.11 s /
1.27 s; a caddie 0.02 s; a comparison 0.01 s; Record Book under 0.01 s; Stats 2.5 s; GOAT Lab 10.8 s / 0.3 s; Career
Grand Slam under 0.01 s. The index is about 1.6 times the size of the season files; exports that include it are
larger accordingly.

## Validation (staged)

1. **Focused tests per package**, each run before its commit: injury timing 3, major funding 11, living views 15,
   qualification windows 10, observer app 12, history access 4, amateur support 12, plus the modules each package
   touched (season, finance, development evidence, access ledger, realism, zero-start regions, comparisons, GOAT
   peaks, history index and consistency, observer history, peak Overall, cohorts, My World). Outcome identity for
   package 5: identical digests in every outcome part over 16 weeks across a season end (153 events).
2. **Full suite on `27e92b4`** (54 modules): 50 passed, 4 failed. Two were tests tied to the old behaviour (the major
   places' money identity now includes amateur support; a test world no longer holding a retired professional),
   fixed in `9f8525b` and `6a9e065`. Two (`test_session`, `test_residence`) found a real defect introduced by
   `138ce06`: a misplaced line split an if/else in the archive, so a season row's settled net lost a winter move's
   cost for golfers without support. Bisected across this pass's commits (only `138ce06` failed) and fixed in
   `e615b2e` (archive only).
3. **Full suite on `e615b2e`** (the last commit with code; later commits change documents only): **54 modules,
   573 tests, all passed, 1 skipped by design** (`test_observer_profiles`, as before); 18 minutes on 4 CPUs.

**Not tested**: browsers other than Chromium, and no wide-screen re-measure this pass (the new Prestige, coach
and support rows are table and list rows on pages measured last pass); small screens (deferred); the long runs.

## Remaining defects and gaps (not claimed as done)

- My World does not yet announce injuries, returns or team news (partnerships, splits, reunions).
- Ratings over time has single attributes and Overall, not yet physical / technical / mental group views.
- Nation counts are not yet linked to the exact population they count.
- The GOAT Lab's first load on a 57-season history takes 10.8 s (repeat 0.3 s).
- A read-only history's side index is left in the temporary folder (about 1.6 times its season files); nothing
  removes old ones yet.
- The classic calendar's code paths remain in the engine for its tests; no new world can use it. Removing them is
  cleanup for a later pass.
- The major-trip guarantee is tested with representative reconstructed scenarios across every status and major,
  not one scenario for each of Test 1's 269 lost places.
- Full careers, aging and the support's long-run effect are unmeasured until the long runs.

## Decisions needed

1. **"Last N years" routes that include the current edition** (`docs/QUALIFICATION_WINDOWS.md`): keep N + 1
   editions (today) or count the N most recent (the real-world reading; a simulation change).
2. **The work / part-time pathway** (`docs/AMATEUR_WORK_PATHWAY_PROPOSAL.md`): approve or change the thresholds
   (age 21+, outside the amateur top 300, no support, 8 weeks cash-blocked, from the next monthly block).
3. **Amateur support amounts**: recipients draw about $1.1-1.25 m a season, about twice the estimate. Keep the
   starting values for the long runs (recommended: measure ten seasons first), or lower the caps now.
4. **The long runs** (`docs/LONG_RUN_PLAN.md`): seeds 360013 (45 seasons), 2027 with and without support (10 each),
   3031 (10); about 3 h 30 min - 4 h 15 min; the stopping conditions listed there.

## Proposed next batch

After approval: the long runs, then their report (no calibration before it). Then, in order: the work pathway if
approved; My World injury, return and team items; ratings group views and nation-count links; richer scouting and
two-way recruitment (S2/S3); five-year event, course and nation prestige (P2); then geography, Aggression and
weather (G1-G3), Biggest Upsets (B1/B2) and tournament stories (T1-T3); death after retirement (C2) once the
identity foundations are settled. Career-mode planning after these world systems are ready.
