# Final-head checks: nation saved-state readback and wide-screen UI smoke

**Build.** build/v17-integration b249c01cc0344fc0a2c09dfd370c3721aaa05d1c for the readback (golfsim and tools identical in 18a8e23fb06c241892a73af29124c168c2018467, which adds only perf docs and a test; the UI smoke was run on 18a8e23). Worlds in RAM-backed /dev/shm (disposable), results here.

## 1. Nation rules: saved state, generated golfers, archive (`readback.py`)

**Scope.** A focused continuation of FRESH_AB (which read in-memory history only): one fresh full-population world per arm, seed 11, two winters, on the final integration build. Arm "off" clears only the nation flags (carry_on, achievement_on) before any cohort is allocated. Not a re-run of the 16-season A/B.

**Arm on:** ok = True, problems = none.

| entrant year, pathway | golfers generated | allocated | recorded total | added | every nation equal |
|---|---|---|---|---|---|
| 2028 juniors | 287 | 287 | 287 | 287 | True |
| 2028 new_pros | 419 | 419 | 419 | 419 | True |
| 2029 juniors | 301 | 301 | 301 | 301 | True |
| 2029 new_pros | 467 | 467 | 467 | 467 | True |

Reopened saved state equal to the running session: carry_on True, achievement_on True, prestige True, multiplier True, achievement True, carry True, history True; cursor {'year': 2029, 'week': 2, 'phase': 'week'} -> {'year': 2029, 'week': 2, 'phase': 'week'}.

| archived season | achievement kept | carry kept | rules block | prestige, achievement, carry, allocated equal to the session |
|---|---|---|---|---|
| 2027 | True | True | {"achievement": true, "achievement_weight": 0.666667, "carry": true} | True, True, True, True |
| 2028 | True | True | {"achievement": true, "achievement_weight": 0.666667, "carry": true} | True, True, True, True |

**Arm off:** ok = True, problems = none.

| entrant year, pathway | golfers generated | allocated | recorded total | added | every nation equal |
|---|---|---|---|---|---|
| 2028 juniors | 287 | 287 | 287 | 287 | True |
| 2028 new_pros | 419 | 419 | 419 | 419 | True |
| 2029 juniors | 301 | 301 | 301 | 301 | True |
| 2029 new_pros | 467 | 467 | 467 | 467 | True |

Reopened saved state equal to the running session: carry_on True, achievement_on True, prestige True, multiplier True, achievement True, carry True, history True; cursor {'year': 2029, 'week': 2, 'phase': 'week'} -> {'year': 2029, 'week': 2, 'phase': 'week'}.

| archived season | achievement kept | carry kept | rules block | prestige, achievement, carry, allocated equal to the session |
|---|---|---|---|---|
| 2027 | False | False | {"achievement": false, "achievement_weight": null, "carry": false} | True, True, True, True |
| 2028 | False | False | {"achievement": false, "achievement_weight": null, "carry": false} | True, True, True, True |

## 2. Wide-screen UI smoke (`smoke.js`, Chromium 1920x1080, full-page screenshots in `shots/`)

The observer (build 18a8e23) serving the arm-on world (2 archived seasons, live 2029), its prestige store removed first so the run starts cold. Tables are found by their exact header text (`textContent`: the page uppercases headers in CSS, so `innerText` reads them in capitals). Every check below is an assertion (a failure is listed under problems); value lists must be non-empty, so no ordering check can pass on an empty column.

Result: ok = True, problems = none.

| page | path | seconds | width px | asserted |
|---|---|---|---|---|
| series_first | `/series/TOUR_MASTERS` | 1.389 | 1920 | cold store: pending = True (asserted); ready 2.117 s later (polled every 2 s, limit 120 s) |
| series_after | `/series/TOUR_MASTERS` | 0.093 | 1920 | pending = False (asserted false); 3 prestige bars (at least 2 asserted) |
| tournaments_by_prestige | `/tournaments?sort=prestige&dir=desc` | 0.324 | 1920 | 100 values (non-empty asserted), descending: [97.5, 97.5, 97.5, 97.5, 93.7, 93.7, 93.6, 93.6] |
| tournaments_page2 | `/tournaments?sort=prestige&dir=desc&page=2` | 0.596 | 1920 | 100 values (non-empty asserted), descending: [56.5, 56.1, 56.1, 56, 55.9, 55.6, 55.5, 55.4]; boundary page 1 min / page 2 max [56.5, 56.5] (page 2 never above page 1) |
| courses_by_prestige | `/courses?sort=prestige&dir=desc` | 0.101 | 1920 | 100 values (non-empty asserted), descending: [97.4, 97.4, 97.4, 97.3, 97.3, 97.3, 97.3, 93.2] |
| courses_page2 | `/courses?sort=prestige&dir=desc&page=2` | 0.102 | 1920 | 100 values (non-empty asserted), descending: [51.2, 50.9, 50.7, 50.6, 50.5, 50.5, 49.9, 49.8]; boundary [51.2, 51.2] |
| nations | `/nations` | 0.16 | 1920 | measure: 50 = as expected: visible success against an even share of the fame on offer, and success against what its golfers' ability predicted; rules: national prestige |
| nation | `/nation/USA` | 0.178 | 1920 | Achievement columns True; prestige rows [9] cells wide (asserted [9]) |
| early_pro_golfer | `/golfer/365` | 0.115 | 1920 | status table names the early decision: True |
| early_pro_season_stayed | `/golfer/365?tab=season&year=2027` | 1.209 | 1920 | line: Could have turned professional from college at 20 (amateur ranking 12); stayed in college on the US College Division I |
| early_pro_season_turned | `/golfer/365?tab=season&year=2028` | 0.101 | 1920 | line (ranking exactly once, asserted): Turned professional from college at 21, before their eligibility ended (amateur ranking 13), starting on the Challenger Tour Americas, with backers putting up $46,000 a season for a share of winnings |
| rules | `/rules` | 0.09 | 1920 | early-pro rule True; versions ['2026-11-12', '2026-11-13', '2026-11-14', '2026-11-15'] |

Earlier smoke runs found one real defect, fixed in build/v17-early-pro dcc0c64: the early decision's history line repeated the amateur ranking, and the status table did not name the early decision. Independent review also ran a 148-case ordering matrix on the sorted lists (passing).

## 3. Full test suite on the final head

**Build.** build/v17-integration 18a8e23fb06c241892a73af29124c168c2018467, clean checkout (worktree in /dev/shm, `TMPDIR` in /dev/shm).

    (TMPDIR=/dev/shm/v17/tmp timeout 10800 python3 -m unittest discover -s tests 2>&1; echo "rc=$?")

**Result** (`full_suite_18a8e23.log`, unittest's own summary, copied verbatim):

    Ran 1136 tests in 7048.262s

    OK (skipped=4)
    rc=0

The run finished inside the 10,800 s wrapper, and the wrapper itself exited 0.

**The 4 skips (labelled static reconstruction).** The run was not verbose, so the log has one progress symbol per test
(1,132 `.` and 4 `s`) but no skip reasons. The skips below were reconstructed without rerunning any test:

- alphabetic discovery of the 89 test files at 18a8e23 collects exactly 1,136 test methods, one for each of the 1,136 progress symbols;
- each `s` is matched by its position in that order to a test;
- the reason comes from that test's definition.

HAL's independent review got the same four, and so did `skipmap.py` (here; collection only, no test run; output in
`skipmap_18a8e23.json`).

| position | test | kind | why it skipped in this run |
|---|---|---|---|
| 207 | `test_decision_evidence_world.DecisionEvidenceWorld.test_outcomes_are_identical_to_the_parent_build` | static, `skipUnless` | `GOLF_PARENT_CHECKOUT` is not set (the comparison needs a parent build checked out) |
| 634 | `test_observer_gaps.WorldGaps.test_retirement_into_a_staff_role_each_once` | `skipTest` in the body | the small-world fixture has no golfer moving into a coach or caddie role |
| 655 | `test_observer_profiles.ProfilesAndStatsTests.test_a_golfer_who_became_staff_keeps_one_identity` | `skipTest` in the body | the same fixture limitation: no golfer became staff in the short world (the test notes the case was checked on the 50-season copy) |
| 1014 | `test_upsets.HeavyEquivalenceTests.test_recording_changes_no_outcome` | static, class `skipUnless` | `GOLF_HEAVY_TESTS` is not `1` (a whole-season run) |

No browser test was skipped: the `test_views` Node Playwright tests ran.

**Previous full run on 4018797, for the record** (`full_suite_4018797.log` and `full_suite_4018797.NOTE.txt`, kept
outside the repository):

- The run was started under a 7,000 s `timeout` wrapper. The run before it had taken 7,524.9 s, so at 4,514 s the
  wrapper alone was paused (SIGSTOP). The test process kept running and reached unittest's own summary:
  `Ran 1132 tests in 6975.263s` / `FAILED (errors=6, skipped=4)`.
- The wrapper was then resumed (SIGCONT) only so it could be reaped. Its alarm had passed while it was paused, so the
  `rc=124` it appended is the wrapper's timeout code, not the test result.
- The run was not cut off; its result is the summary above.
- The 6 errors were stale mocks in `test_nation_achievement` (ObserverProjections 4, ObserverText 2), all
  `AttributeError: 'object' object has no attribute 'a'`. Those tests stubbed `OP._record` only, but on the integrated
  build the nation page reads through the prestige store's `OP._records`.
- The fix stubs `_records` as well (4 lines in that test file), and the 6 tests pass in the run above. No production
  change was made for it.
- The 4 tests added since are `test_perf_v17` (+1), `test_college_early_pro` (+1) and `test_prestige_store` (+2):
  1,132 + 4 = 1,136.
