# Roadmap traceability: release candidate `integration/v16-rc1` at `c0d1ea5`

This refresh replaces the matrix of 31 October 04:53 UTC (`b796c03`, read against `build/v16` at `87c2a21`). Every
row is read against the release candidate's exact final head, **`integration/v16-rc1` at `c0d1ea5`** (31 October
2026, 09:28 UTC).

**Revised after review.** The first revision read against `0a05310`, then added `376c7a9` (a decision-evidence fix
found by the final suite on `0a05310`: E1.f.8, X10). It recorded the independent acceptances of DL1, DL2, `d39d613`
and `c2a1391`, consolidated the open rows into distinct open items O1-O9 (section 7) and marked weather
temperature/firmness and injury tuning as excluded from this pass by decision.

**Revised to `c0d1ea5`.** This revision reads every row against `c0d1ea5`:
- It adds the rc1 commits after `0a05310`:
  - `376c7a9`, the decision-evidence fix;
  - `9df86eb` and `88bf8a6`, the long-run harness's comparison arms (the second independently accepted);
  - `0b55a2b`, the roadmap table and the decision log on rc1;
  - `1c28d09` and `b287199`, Biggest Upsets B2 and its truthfulness fixes (the second independently accepted);
  - `c0d1ea5`, the merge of two test-fixture fixes, `aa66095` and `65d00e2` (scoped acceptance).
- It records the first final suite on `0a05310` (972 tests; failures=1, errors=4; all five fixed: X10-X12) and the
  passing pre-final smoke and navigation on `0a05310`. The exact-head gates G1-G4 on `c0d1ea5` were then running
  (their results are filled in below).
- It folds in the reviewer's decisions and the measurements on `origin/build/v16-report` (latest `79b78d6`):
  - O8 is closed by decision (`ac310a8`);
  - O9 is done (`1c28d09`, `b287199`);
  - O2 is measured on the `c0d1ea5` comparison arms;
  - O3 and O4 are measured in part;
  - the F1 baseline pressure is documented (`ac310a8`, `1de4119`).
- Status changes:
  - DL1.m, DL2.m, E1.f.7, G3.g and T3.b move to `done with known limitation`;
  - B2.a moves to `done`;
  - P2.f and S3.g move to `open: design decision pending` (then to `done with known limitation`, below).
- Section 9 is updated: `0b55a2b` brought `docs/BACKLOG.md` and the decision log in step.

**Revised for HAL's decisions (31 October, after the arms report).**
- CQ1 / O6 decided: rare organic potential and the current maturation are kept for this playthrough, explicitly
  as provisional (with D16, `0b55a2b`); retention, not a mechanics change. CQ1 → `done with known limitation`.
- P2.f and S3.g: the current prestige and recruitment constants are kept as the baseline for this playtest, with
  the measured limitations. Both → `done with known limitation`.
- CQ2 / O7: the initialization size is kept as the baseline for this playtest; the seeded start sits below
  equilibrium. CQ2 → `done with known limitation`. Its figures are the harness's active counts after the tenth
  winter (10,337 / 10,343 / 10,339; `d8680ab`).
- CQ3 / O5: no target bands are invented and nothing is tuned without evidence. CQ3 → `excluded from this pass by
  decision`; the rows in sections 3 and 4 that point to O5 now read "see O5 (excluded)".
- Still open and being measured at the time: D5.c, N4.c, G1.e and B1.h (O3, O4); E1.f.5 and E1.f.6 pending G2/G4.
- No item is now `open: design decision pending`. Counts: `done` 175, `done with known limitation` 37,
  `open: not started` 5, excluded 3.

**Revised for the final results on `c0d1ea5`.**
- The final-head gates passed: G1, Ran 998 tests in 7524.9 s, OK (skipped=4); G2, the smoke (seed 4207, exit 0,
  613 s); G3, 160 pages, 0 failing; G4, no outcome part differs with the evidence off (section 1). O1 closes.
- N4.c → `done` (save/reopen replay of 2028 identical in all 16 recorded parts); E1.f.5 → `done` (G4).
- E1.f.6, D5.c, B1.h and G1.e → `done with known limitation` (`a2d56fb`, `dc41950`, `0061501`). O3 and O4 close.
- Section 9: `a2d56fb` brings `docs/BACKLOG.md`, the decision log (D18-D21) and `docs/DECISION_EVIDENCE.md` into
  step; it is not on rc1.
- Nothing remains open except what is excluded from this pass by decision. Counts: `done` 177,
  `done with known limitation` 40, `open: design decision pending` 0, `open: not started` 0, excluded 3.

Sources:
- the commits `473690a..c0d1ea5` and their merge messages, which give the packages, rules versions 2026-11-03 ..
  2026-11-11, conflict resolutions and quick tests;
- the documents on rc1: `docs/BACKLOG.md`, `docs/DECISIONS_2026-10-31.md`, `docs/LONG_RUN_PLAN.md`, `docs/review/*.md`,
  `docs/DECISION_EVIDENCE.md`, `docs/WORLD_PRESTIGE_PACKAGE.md`, `docs/RECRUITMENT_PACKAGE.md`,
  `docs/FAMILIARITY_AND_AGGRESSION.md`, `docs/AMATEUR_WORK_PATHWAY_PROPOSAL.md`, `docs/COMPETITION_ACCESS.md`,
  `docs/HISTORY_AND_PERSISTENCE.md` and `docs/QUALIFICATION_WINDOWS.md`;
- the review documents on `origin/build/v16-report` (latest `0061501`), none of which are on rc1:
  - the remedy options, `docs/review/U21_AND_COLLEGE_REMEDY_OPTIONS.md` (`9f2ac00`, `9baea7a`);
  - the Vaughan diagnosis, `docs/review/VAUGHAN_OUTLIER_DIAGNOSIS.md` (`b613b3b`, corrected `d13ad91`);
  - the F1 baseline and E1 scope, `docs/review/F1_BASELINE_PRESSURE_AND_E1_SCOPE.md` (`ac310a8`, `1de4119`);
  - the arms comparison, `docs/review/arms_comparison/ARMS_COMPARISON.md` with its scripts (`ee3fada`, `79b78d6`;
    read only, written 12:02 UTC; sections 5 and 6 added by `dc41950`), cited below as "the arms report";
  - the familiarity on/off season, `docs/review/arms_comparison/G1E_FAMILIARITY.md` (`0061501`, the branch head);
- the docs-only commit `a2d56fb` on `build/v16-docs-final` (from `c0d1ea5`; six `docs/*.md` files, engine id
  1949ff63 unchanged), which brings `docs/BACKLOG.md`, the decision log (D18-D21) and `docs/DECISION_EVIDENCE.md`
  into step;
- the test modules and classes in `tests/` at `c0d1ea5`;
- the release evidence ledger kept beside the candidate's test queue, to be published on `build/v16-report` under
  `docs/review/release_evidence/`. Its results are quoted as written.

**No test or simulation was run for this matrix.**

Scope:
- Section 2 covers the overnight roadmap scope set by the reviewer, requirement by requirement.
- Sections 3 and 4 carry the rest of the owner's expanded roadmap (`Golf_Legacy_Expanded_World_Roadmap_2026-10-30`)
  and its audit register N01-N23 forward from the 31 October matrix, with statuses updated to rc1.
- Item sub-ids are this document's numbering, not the roadmap's.

## 1. How to read it

### Status: one of five values

| Status | Meaning |
|---|---|
| `done` | Implemented on rc1, with named tests and recorded evidence; nothing requested in the row is left open |
| `done with known limitation` | Implemented on rc1; the stated limitation remains (anything requested that is unresolved has its own open row) |
| `open: design decision pending` | Requested and unresolved; closing it needs an owner or reviewer decision (calibration, constants, scope), usually after a measurement |
| `open: not started` | Requested and not done (often a measurement or analysis) |
| `excluded from this pass by decision` | Out of scope for this pass by the reviewer's decision; not a missing feature |

A row is not marked done because it is a design question rather than a crash. Nothing is called deferred or
excluded except what the owner deferred (section 2.17) or the reviewer excluded.

Open rows named the consolidated open item they belonged to (section 7). All items are now closed, and O5 is
excluded from this pass by decision. Several rows often share one question; for example, many audit rows share the
one calibration question (O5). So section 7, not the count of rows, is the list of distinct open work. Rows in
sections 3 and 4 that only restate a consolidated item point to it ("see O5 (excluded)", "see O6 (decided)") and
carry no status of their own.

### Commits

- "Merge" is the commit on rc1's first-parent line, either a merge or a direct commit.
- "Package" lists the commits the merge brings in.
- Rules versions are those in `golfsim/rules.py` (`VERSIONS`; `RULES_VERSION` is `2026-11-11` at `c0d1ea5`; no
  rules version was added after `0a05310`).
- Every SHA cited exists (checked with `git cat-file -e`). All are in the history of `c0d1ea5` except these:
  - `9f2ac00`, `9baea7a`, `b613b3b`, `d13ad91`, `ac310a8`, `1de4119`, `ee3fada`, `79b78d6`, `dc41950` and
    `0061501` (the branch head), on `origin/build/v16-report` only;
  - `a2d56fb`, the docs-only commit on `build/v16-docs-final` (its parent is `c0d1ea5`);
  - `b796c03`, the earlier matrix, which this branch merges.
  - `f086562`, `d8680ab` and `b2e6a5d`, earlier revisions of this matrix on this branch.
- 1949ff63 is the engine id, not a commit; `a2d56fb` leaves it unchanged.

### Evidence

- **Pre-final evidence** is a run on a named commit before `c0d1ea5`, listed in the register below. A pass there is
  not a final-head gate.
- **Pre-final gates on `0a05310`** (ledger sections 1 and 6):

  | Gate | Run | Result on `0a05310` |
  |---|---|---|
  | G1 | full suite (`python -m unittest discover -s tests`) | Ran 972, **FAILED (failures=1, errors=4)**. All five fixed: `tests.test_amateur_residence` ×3 by `376c7a9` (X10); `tests.test_compare` by `aa66095` (X11); `tests.test_goat_peaks` by `65d00e2` (X12). The two fixture fixes are merged at `c0d1ea5` |
  | G2 | fresh full-population smoke (seed 4207: 2 seasons with decision evidence, plus 1 season without) | passed: outcomes identical with the evidence on and off. Season 1: 200.5 s on, 188.4 s off; season file 13.04 MB against 12.21 MB; evidence 830 KB gzip, +6.8 % over the file without it (`docs/review/F1_BASELINE_PRESSURE_AND_E1_SCOPE.md`, `1de4119`) |
  | G3 | wide-screen navigation (`nav_check.js` at 1920 and 1366 px on a copy of the smoke world) | passed: 140 pages, 0 failing |

- **Final-head gates on `c0d1ea5`** (the exact head; ledger: `docs/review/release_evidence/` on `build/v16-report`). All four passed:

  | Gate | Run | State |
  |---|---|---|
  | **G1** | full suite (`python -m unittest discover -s tests`) | **passed.** Clean checkout `c0d1ea5` (c0d1ea598bc7), `python -m unittest discover -s tests` at nice 19, 11:48:11-13:55:14 UTC, exit 0: **Ran 998 tests in 7524.9 s, OK (skipped=4)**. The skips, identified by a separate verbose run of the 12 tests that can skip (the same 4 skipped): 2 environment-gated, `test_decision_evidence_world.DecisionEvidenceWorld.test_outcomes_are_identical_to_the_parent_build` (GOLF_PARENT_CHECKOUT) and `test_upsets.HeavyEquivalenceTests.test_recording_changes_no_outcome` (GOLF_HEAVY_TESTS=1); 2 data-conditional, no golfer became staff in the small test world: `test_observer_gaps.WorldGaps.test_retirement_into_a_staff_role_each_once` and `test_observer_profiles.ProfilesAndStatsTests.test_a_golfer_who_became_staff_keeps_one_identity` |
  | **G2** | fresh full-population smoke (seed 4207: 2 seasons with decision evidence, plus 1 season without) | **passed.** Seed 4207, exit 0, 613 s. 2027 with the evidence on: 201.5 s, season file 13,039,656 B (+6.8 % over 12,208,596 B off), evidence 830,379 B gzip (6.4 %); 2028: 197.2 s, 12,567,224 B, evidence 901,302 B (7.2 %). Bounds held: at most 13 plans, 0 over, at most 3 career rows. Golfers: 6,409 created and scheduled in 2027, 6,878 scheduled in 2028 (active); everyone in the world, retired included, 7,120 after 2027 and 7,802 after 2028 |
  | **G3** | wide-screen navigation (`nav_check.js` at 1920 and 1366 px on a copy of the smoke world) | **passed.** Exit 0: 160 pages (80 at 1920 px, 80 at 1366 px), 0 failing, largest horizontal overflow 0; 8 Story views and 12 coaching tabs visited |
  | **G4** | E1.f outcome equivalence on the exact final head (from G2's evidence on/off comparison) | **passed.** From G2: the outcome parts that differ with the evidence off: **none** |

  Rows write "G1 passed" for this full-suite pass on `c0d1ea5` and do not repeat it further.
- **Pinned-run evidence** comes from runs A-D on the frozen build `473690a`. It describes that build only, not the
  final feature world (section 6).

### Evidence register (ledger, quoted as written)

All queue runs used a clean detached worktree of the named commit:
`timeout 3600 nice -n 19 python -m unittest <modules>`.

**Serialized queue (ledger section 1)**

| Id | Time (UTC) | Item | Commit tested | Modules | Result |
|---|---|---|---|---|---|
| L01 | 05:05 | return | `0c5cdd7` | test_amateur_return test_work_pathway test_amateur_support test_amateur_residence | Ran 39 OK |
| L02 | 05:07 | upsets (GOLF_HEAVY_TESTS=1) | `3291666` | test_upsets test_golf_stats | Ran 35 OK |
| L03 | 05:10 | geography | `63ad358` | test_familiarity_region test_aggression_visible test_residence test_engine | Ran 73 OK |
| L04 | 05:12 | weather | `1cbf7a4` | test_weather test_engine test_playoffs test_golf_stats | Ran 64 OK |
| L05 | 05:21 | death | `c29f6b0` | test_mortality test_mortality_world test_cohort test_staff | Ran 51 OK |
| L06 | 05:35 | C2 merged observer | `c29f6b0` | test_living_views test_observer_history test_history_consistency test_myworld test_myworld_events test_nation_links test_ratings_groups test_views test_observer_app test_amateur_residence | Ran 103 OK |
| L07 | 05:55 | recruitment | `b7e835c` | test_recruitment test_staff test_living_views test_history test_history_consistency test_finance_integration test_observer_history test_myworld_events test_observer_profiles test_observer_app | **Ran 140 FAILED (failures=1, skipped=1)**: X2 |
| L08 | 06:05 | observer gaps | `d04fa5b` | test_observer_gaps test_living_views test_observer_history test_myworld test_myworld_events test_observer_profiles test_complete_history test_views | Ran 105 OK (skipped=2) |
| L09 | 06:13 | prestige | `d187a56` | test_venue_moves test_nation_shares test_world_prestige test_season test_population test_development test_amateur_residence test_history_consistency test_observer_history test_living_views | **Ran 111 FAILED (errors=1)**: X1 |
| L10 | 06:16 | return (funding fix) | `5c15e32` | test_amateur_return test_work_pathway test_amateur_support test_season | Ran 50 OK |
| L11 | 06:39 | weather (gusts) | `e19fff3` | test_weather test_engine test_playoffs test_golf_stats test_observer_history test_amateur_residence test_season | Ran 113 OK |
| L12 | 06:57 | geography (home-club fix) | `7819114` | test_familiarity_region test_aggression_visible test_course_library test_residence test_session test_publication test_engine test_living_views test_observer_history | Ran 167 OK |
| L13 | 07:01 | upsets (snapshot) | `e027e70` | test_upsets test_observer_history test_living_views | Ran 57 OK (skipped=1) |
| L14 | 07:01 | F2 | `3e58a7d` | test_major_affordability_269 test_major_funding | Ran 20 OK |
| L15 | 07:05 | stories | `2306549` | test_stories test_myworld test_observer_history test_observer_app test_views | Ran 102 OK |
| L16 | 07:20 | rc1 fixes group | `d70a725` | test_living_views test_population test_nation_shares test_world_prestige test_finance_integration test_recruitment test_staff test_history_consistency | Ran 113 OK (incl. the formerly failing living_views and finance PromotionTests) |
| L17 | 07:34 | rc1 observer group | `d70a725` | test_observer_gaps test_observer_history test_observer_app test_observer_profiles test_observer_sync test_myworld test_myworld_events test_stories test_upsets test_upsets_stories_merge | **Ran 173 FAILED (failures=1, skipped=3)**: X6 |
| L18 | 07:38 | rc1 engine group | `d70a725` | test_weather test_weather_geography_merge test_engine test_realism test_playoffs test_performance_equivalence test_course_library test_venue_moves test_familiarity_region test_aggression_visible | Ran 184 OK |
| L19 | 08:00 | rc1 season group | `d70a725` (pre-fix) | test_season test_session test_history test_mortality test_mortality_world test_work_pathway test_amateur_return test_major_affordability_269 | Ran 116 OK |
| L20 | 08:01 | decision evidence world | `d70a725` (pre-fix) | test_decision_evidence_world | Ran 5 OK (skipped=1: the parent-build check runs as its own item) |
| L21 | 08:02 | decision evidence vs parent build | `d70a725` vs `16c83e8` (pre-fix) | test_decision_evidence_world ... test_outcomes_are_identical_to_the_parent_build | Ran 1 OK |
| L22 | 08:04 | evidence callers | `d70a725` (pre-fix) | test_realism test_development test_decision_evidence test_diagnostic_report | Ran 87 OK |

**Quick unit tests (ledger section 2)**, all run with `nice -n 19 timeout 600`:

| Id | Commit | Tests | Result |
|---|---|---|---|
| U1 | `2516d86` | UnitWinterBoundary, UnitTeamNews, UnitWinterDeathAndDeparture | 14 OK |
| U2 | merge `a90ea85` | return Conditions/WorkStart, residence RulesTests, mortality Curve, pathway Counting/Deciding | 25 OK |
| U3 | merge `7d8489f` | recruitment ObserverRefusalTests, mortality Curve/WhoCanDie/WorkingStaff/Observer, residence RulesTests | 16 OK |
| U4 | merge `b1158d8` | test_familiarity_region (11 classes), test_aggression_visible (3), mortality Curve/Archive, residence RulesTests | 58 OK |
| U5 | merge `1a0cb2f` | test_weather_geography_merge | 6 OK |
| U5 | merge `1a0cb2f` | test_weather + aggression, observer_gaps UnitRoundConditions, familiarity, mortality, residence | 64 OK |
| U6 | merge `e4cc3db` | upsets ModelTests/NoHindsightTests/PageTests, weather RecordTests/ControlTests | 32 OK |
| U7 | merge `fe04ab5` | test_upsets_stories_merge | 2 OK |
| U7 | merge `fe04ab5` | test_stories (9 unit classes) | 44 OK |
| U7 | merge `fe04ab5` | observer_gaps units + upsets + merge + recruitment refusals + mortality observer | 49 OK |
| U8 | `d2a79ce` | UnitRoundConditions, test_weather_geography_merge, test_upsets_stories_merge | 12 OK |
| U9 | `f5ac938` | nation_shares DrawCap/TotalsAndAllocation/TalentUnchanged | 13 OK |
| U10 | `16c83e8` | recruitment WinterOrderTests/AssessmentTests/InitiativeTests/ObserverRefusalTests, mortality WorkingStaff/Curve, residence RulesTests | 21 OK |
| U11 | `6aa5f9c` | tests.test_diagnostic_report | 6 OK |
| U11 | `5073485` | tests.test_diagnostic_report | 10 OK |
| U11 | `5ad7a50` | tests.test_diagnostic_report | 10 OK |

**Failed, then fixed (ledger section 3)**

| Id | Defect and where it was found | Fix | Tests after the fix |
|---|---|---|---|
| X1 | Prestige / nation shares: a season crashed in new professionals (`RuntimeError: Czechia: 1 new_pros not reached in 1590 draws`). Found in L09 at `d187a56` | `68676fd`, merged `f5ac938` | `test_nation_shares` DrawCap (5; 3 fail on `d187a56`) + TotalsAndAllocation/TalentUnchanged/Baseline/SmoothingAndBounds: 19 OK; InTheWorld 1 OK. World re-test: L16 |
| X2 | Recruitment: a golfer "paying their own way" was below next season's costs, because caddie fees were updated after the winter's decisions (`PromotionTests`, seed 11, scale 0.2). Found in L07 at `b7e835c` | `c0932d0`, merged `16c83e8` | WinterOrderTests (2; fail before), recruitment unit classes 13 OK, PromotionTests 3 OK. World re-test: L16 |
| X3 | My World winter watermark: a death-ended departure was clamped to week 52 and hidden. Found by review at `c29f6b0` | `2516d86` | UnitWinterDeathAndDeparture (4 new) + updated expectations: 14 OK; independently 32 OK |
| X4 | Diagnostic report: provenance labelled by inference; denominators | `6aa5f9c`, `5073485`, `5ad7a50` | U11 |
| X6 | Coach page did not show this season's partnerships until archived (`test_coach_clients_are_current_assignments`). Found in L17 at `d70a725` | `9cac183` (judged insufficient by review), then `697183c` | LivePartnerships (3) OK; the world test OK (42 s); related observer unit classes 18 OK |
| X7 | Report and rule text inconsistent with the approved pathway age | `e759903` | PathwayAgeInForce 2 OK |
| X8 | Report tool killed by the memory limit (12.6 GB) on the 45-season run | `c2a1391` | SeasonFilesTrimmed; module 13 OK |
| X9 | `run_world` (default mode) did not record the pathway age in force; team-history footer said "end of None" | `d39d613` | WorldRulesRecorded (3) |
| X10 | Decision evidence: an evaluation without a named model crashed the winter. Found by the final suite (G1) on `0a05310`: `tests.test_amateur_residence`, 3 errors, `KeyError: None` in `decision_evidence.record_career`. The tests stand in mocks for `careers.p_retire` and `p_turn_pro` | `376c7a9` (rc1) | `test_decision_evidence.WinterDecisions.test_models_stood_in_for_record_nothing_and_change_nothing`; tests.test_decision_evidence + tests.test_amateur_residence: 24 OK (commit message) |
| X11 | Compare test fixture: `Compare.test_totals_come_from_the_records` errored (IndexError) because the seed world's first major winner is now also the No. 1, so the page compared one golfer with himself. A fixture assumption, not a product defect. Found by G1 on `0a05310` | `aa66095`, merged `c0d1ea5` | tests.test_compare 7 OK (commit message) |
| X12 | GOAT peaks test fixture: `ArchiveOnlyPeaks.test_a_retired_golfers_peak_survives_later_seasons` failed (`[] is not true`): nobody retires after the first season in the seed-59 world now that the merged packages move the random streams. Not a defect; the retirement model is unchanged. Found by G1 on `0a05310` | `65d00e2`, merged `c0d1ea5` | tests.test_goat_peaks 3 OK (commit message) |

The ledger has no section 3.5 item numbered X5. Its section 3.5 table (package-branch review fixes) is cited by
commit in the rows below. X11 and X12 are this document's numbering, from the commit messages.

**Independent reviews (ledger section 4)**

| Id | Review |
|---|---|
| R1 | Prestige `68676fd`: 8 focused tests, including exact Czechia/99/2029 and 27 rare quota/stream scenarios |
| R2 | Recruitment `c0932d0` on `16c83e8`: original PromotionTests + WinterOrderTests 5/5 |
| R3 | Report `5ad7a50`: accepted after 10 independent tests; report `5073485`: arithmetic passes |
| R4 | `2516d86` winter boundary: 32 tests pass (scoped acceptance; rerun on final head) |
| R5 | Stories `2306549`: accepted, 47 story tests + cache/version/qualifier checks |
| R6 | Integration `fe04ab5`: 116 weather/geography/engine/familiarity/playoff tests and 216 classic-round exact comparisons; conditions/replay/match-play/gust display; 49 story/merge + 24 upset tests; simulated-edition story/data/save-reopen. No new in-scope blockers |
| R7 | College open access `459322c` (reviewer's correction to this matrix): independently accepted. 10 tests plus an actual 5 % world (weeks 17-18: 145 open-amateur starts by 112 golfers); exact counter/result match; nonzero save/reopen priority equality; next-year counter reset |
| R8 | Pathway from 18 `c848952` (reviewer's correction): independently tested, including a real monthly in-season transition (age 18, rank 301; unchanged cutoff; no cash grant) |
| R9 | `d39d613` (both harness modes record the pathway age; the no-archive footer) and `c2a1391` (report memory reduced, not constant: each year's development section is retained): independently accepted (reviewer's correction) |
| R10 | 89-at-18 diagnosis `b613b3b`, corrected per independent review in `d13ad91` (`docs/review/VAUGHAN_OUTLIER_DIAGNOSIS.md`, on `origin/build/v16-report`, not on rc1). Verdict: a rare organic tail the rules produce (created Overall 85.31, potential 97.01). The independent calibration review recommends keeping rare organic potential for the next test and investigating individualized maturation separately (learning rate relative to the drawn peak age), rather than flattening talent |
| R11 | Harness arm checks `88bf8a6` (the three blockers found in review of `9df86eb`): independently accepted |
| R12 | Biggest Upsets truthfulness fixes `b287199` (unranked estimates keep their own reason; unsupported models never ranked): independently accepted |
| R13 | Suite-fix merge `c0d1ea5` (`aa66095`, `65d00e2`): scoped acceptance (test fixtures only) |
| R14 | F1 baseline pressure and E1 scope (`ac310a8`, denominators corrected `1de4119`; `docs/review/F1_BASELINE_PRESSURE_AND_E1_SCOPE.md`, on `origin/build/v16-report`): accepted. Records the reviewer's settlements: the F1 baseline is described, not calibrated (bands stay O5); format /2 fulfils E1 and its listed gaps are disclosed limitations, not missing features (O8 closed) |
| R15 | Arms report (`79b78d6`, on `origin/build/v16-report`): review in progress. Section 4 (story timing) independently reviewed. The reviewer judged the college-access trade-off (section 2) consistent with the design: the policy is retained and its cost to members disclosed |

**Results stated in commit messages only (M)**

| Commit | Result in its message |
|---|---|
| `5664853` | Age18Tests, Counting, Deciding, test_college_open_access, weather RecordTests, mortality Curve, familiarity RuleTextTests, residence RulesTests, test_decision_evidence, recruitment WinterOrderTests: 56 OK |
| `e759903` | PathwayAgeInForce with Age18Tests, Deciding, residence RulesTests: 29 OK; test_long_run_safeguards 7 OK |
| `697183c` | LivePartnerships 3 OK; world test 1 OK (42 s); related observer classes 18 OK |
| `d39d613` | WorldRulesRecorded (3) and the extended LivePartnerships case, with test_diagnostic_report: 25 OK |
| `9cac183` | 1 test OK (46 s) |
| `c2a1391` | module 13 OK |
| `376c7a9` | tests.test_decision_evidence + tests.test_amateur_residence: 24 OK |
| `9df86eb` | tests.test_long_run_safeguards.ComparisonArms (3); module 13 OK; end to end at scale 0.01 for one season |
| `88bf8a6` | tests.test_long_run_safeguards.ArmChecksBeforeWriting (5); module 18 OK; end to end at scale 0.01 (a refused resume left all 35 files byte-identical) |
| `1c28d09` | tests.test_upset_examples 12 OK; tests.test_upsets 25 OK (1 heavy skipped); tests.test_upsets_stories_merge 2 OK; test_stories Fact/Pattern/Text/LiveView 25 OK |
| `b287199` | tests.test_upset_examples 17 OK (10 of the 17 fail on the previous code); tests.test_upsets 25 OK (1 heavy skipped); tests.test_upsets_stories_merge 2 OK; tests.test_stories 9 classes 44 OK; tests.test_golf_stats.CountingTests 5 OK |
| `aa66095` | tests.test_compare 7 OK |
| `65d00e2` | tests.test_goat_peaks 3 OK |
| `c0d1ea5` | on `0b55a2b`: test_compare 7 OK; test_goat_peaks 3 OK |

## 2. The overnight roadmap scope (reviewer)

Columns: Merge / package (rules) · Tests · Evidence (latest pre-final run, then the final head) · Review · Remaining.

### 2.1 N1-N5

| Id | Requirement | Status | Merge / package (rules) | Tests | Evidence | Review | Remaining |
|---|---|---|---|---|---|---|---|
| N1 | Qualification windows: the N most recent editions for P2, U5, B3 (five majors) and M3, P3, U6, B4 (three Players); this season's edition only when played before the field (D1) | `done` | `32a0a6f` (direct, before `473690a`; boundary tests from `c28bf77`); rules 2026-11-03; `docs/QUALIFICATION_WINDOWS.md` | `test_exemption_window` (Windows, USAOpenChampions) | No ledger run; in the pinned build, so runs A-D played it; G1 passed | D1 records it done | -- |
| N2 | Work pathway for persistently cash-blocked adult amateurs: 8 counted weeks, no support, no family money, outside the amateur top 300, full-time non-college, monthly decision (D2) | `done with known limitation` | `3d3090e`; rules 2026-11-03; age 18 from rules 2026-11-10 (DL1); rule text names both ways back `e759903` | `test_work_pathway` (Golfer, Counting, Deciding, InASeason) | L01, L10, L19 (`d70a725`, 116 OK); pinned A-D "took work by the pathway" seasons: A 1224, B 224, C 247, D 246; G1 passed | D2 approved it as an initial calibration; R8 for the age-18 change | Calibration is provisional (D2); the age-18 outcomes are measured descriptively only (DL1.m) |
| N3 | Amateur-support switch for a comparison arm on the same build; frozen, pinned diagnostic builds | `done` | `3d3090e` (`Season(amateur_support=False)`, `Session.create(amateur_support=False)`); `473690a` (`tools/long_world.py --no-amateur-support`, `--keep-after`, stopping safeguards, `tools/determinism_replay.py`); `43bf2c4` (a resume refuses a mismatched support setting); `e759903`, `d39d613` (the run records the pathway age in force, both run modes); `9df86eb` (`--pathway-min-age`, `--college-open-access`: comparison arms for new session worlds), `88bf8a6` (arm checks before anything is written; session worlds only; no arm on an existing world) | `test_long_run_safeguards` (Safeguards, ResumedSupportSetting, WorldRulesRecorded, ComparisonArms, ArmChecksBeforeWriting) | M `e759903` (7 OK), M `d39d613` (25 OK), X9; M `9df86eb` (13 OK), M `88bf8a6` (18 OK); every A-D segment ran on a clean `473690a` checkout (provenance); the four comparison arms ran on `c0d1ea5` (section 6); G1 passed | D4 (one build for both arms); `d39d613` accepted (R9); `88bf8a6` accepted (R11) | -- |
| N4.a | Long runs A (seed 360013, 45 seasons), B and C (2027, 10 seasons, support on and off), D (3031, 10 seasons) | `done with known limitation` | Runs on `473690a`; report and provenance `0a05310` (`docs/review/DIAGNOSTIC_RUNS_ABCD.md`, `docs/review/DIAGNOSTIC_RUNS_PROVENANCE.md`) | `test_diagnostic_report`, `test_long_run_safeguards` | Ledger section 5: B, C, D complete (10 seasons each), reconcile errors 0; A complete 45/45 (segments 2027-2033, 2034-2054, 2055-2071), reconcile errors 0 every season. Guard stops at season 2033 (A 487 s, B 491 s; CPU contention) are recorded | Report tool accepted at `5ad7a50` (R3); the A-D report at `0a05310` has no recorded review | Evidence about the pinned build only (section 6). The calibration questions are settled for this playtest by decision (section 2.16: CQ1, CQ2 kept with limitations; CQ3 excluded) |
| N4.b | Determinism spot check (run B) | `done` | `tools/determinism_replay.py` (`473690a`) | -- | B season 5 (2031) replayed from the copy kept after season 4: identical in all 15 recorded parts (ledger section 5, provenance) | -- | Pinned build only; see N4.c |
| N4.c | Determinism of the final feature world on a full population | `done` | -- | Small-world determinism per package: `test_recruitment.WorldTests`, `test_mortality_world.SmallWorld.test_saved_and_resumed_the_same`, `test_nation_shares.InTheWorld`, `test_decision_evidence_world.DecisionEvidenceWorld` | `tools/long_world.py --session --seeds 4207 --years 2 --workers 2 --pathway-min-age 18 --college-open-access on --keep-after 1` on `c0d1ea5`, exit 0: reconcile errors 0 and staff violations 0 in both seasons; 6,878 then 7,300 active. `tools/determinism_replay.py`, exit 0: season 2028 replayed from the copy saved after 2027 and reopened, **identical in all 16 recorded parts** | -- | -- |
| N5.a | My World: injury, return and partnership items for followed people (E3.c, E3.d, S1.d) | `done` | `ccddd36` / `81cae53`, `b07b072` | `test_myworld_events` (MyWorldEvents) | L06 (`c29f6b0`, 103 OK); also in L17; G1 passed | HAL reviewed at `b07b072` (21 new tests, compileall, targeted synthetic assertions; `ccddd36`) | -- |
| N5.b | Ratings over time: Physical, Technical and Mental group views (E2.c) | `done` | `ccddd36` / `a9e5e98` | `test_ratings_groups` (RatingsGroups) | L06; G1 passed | As N5.a | -- |
| N5.c | Nation counts link to exactly the people they count (R9.d, N08) | `done` | `ccddd36` / `3f0c036` (kept through the prestige merge `787eda7`) | `test_nation_links` (NationLinks) | L06; G1 passed | As N5.a | -- |

### 2.2 S2/S3: two-way recruitment, staff-initiated (rules 2026-11-04)

The package merged at `7d8489f` (package `cab6e45`, `6ada329`, `a1b3aad`, `b7e835c`) and its fix at `16c83e8`
(`c0932d0`). Its merge records "Reviewed and accepted at b7e835c". Evidence for the whole package:
- L07 failed at `b7e835c` (fixed by X2);
- L16 (`d70a725`) Ran 113 OK, including test_recruitment, test_staff and test_finance_integration;
- U3 and U10 quick tests;
- reviewer R2.

| Id | Requirement | Status | Merge / package | Tests | Evidence | Remaining |
|---|---|---|---|---|---|---|
| S2.a | Scouting firms up with seasons watched and partly recognises upside from observed development; never reads potential or ceilings; error, late bloomers and disappointments kept | `done` | `7d8489f` / `cab6e45` | `test_recruitment` (AssessmentTests, HiddenTests) | L16; U10; G1 passed | Constants kept as the playtest baseline (S3.g) |
| S3.a | Staff pursue golfers; development and established coaches and caddies weigh different things | `done` | `7d8489f` / `cab6e45`, `b7e835c` | MotivationTests, TwoWayTests | L16; G1 passed | -- |
| S3.b | Staff-initiated recruitment: established coaches court established golfers; idle caddies offer to carry bags | `done` | `7d8489f` / `b7e835c` | InitiativeTests | InitiativeTests 5 OK at `b7e835c` (ledger section 3.5); U10; L16; G1 passed | -- |
| S3.c | Loyalty and shared history; a better offer does not dissolve a good partnership | `done` | `7d8489f` / `cab6e45` | LoyaltyTests | L16; G1 passed | -- |
| S3.d | Approach, acceptance, refusal and departure reasons visible on both sides, including refusals with no archived stint and this season's refusals | `done` | `7d8489f` / `cab6e45`, `a1b3aad` | ObserverRefusalTests | U3, U10; G1 passed | Accepted partnerships shown live: LP1 |
| S3.e | Winter order: caddie reputations and fees move before the career decisions; own-way decisions keep their figures | `done` | `16c83e8` / `c0932d0` | WinterOrderTests; `test_finance_integration.PromotionTests` | X2; L16; U10; G1 passed | R2. This changes winter ordering in every world (merge message) |
| S3.f | Deterministic, capacity- and money-safe in a world; old saves load | `done` | `7d8489f` | WorldTests; HiddenTests | L16 (the test_recruitment module); G1 passed | -- |
| S3.g | Compare offer rates, retention, quality distribution and development across seeds, then confirm the proposed constants (scouting error model, recruitment and retention weights) | `done with known limitation` | `tools/staff_market_measure.py`, `tools/staff_market_compare.py`; `docs/RECRUITMENT_PACKAGE.md` (proposed constants) | -- | Measured descriptively on the final build, two seeds (arms report section 3, "Recruitment": a18new seed 4207, 10 seasons; seed2 seed 5309, 5 seasons): staff-initiated offers, acceptances and refusals with reasons by year. For example, coach offers accepted 79 % in 2027 (both seeds), then 40-60 %; caddie offers accepted 7-18 % after 2027; the leading refusal is "could not afford their fee". No before/after (staff initiative off) comparison; quality and development by recruitment not reported. `docs/RECRUITMENT_PACKAGE.md` at `c0d1ea5` still says "NOT yet run" (an update note in `a2d56fb`) | The current recruitment constants are kept as the baseline for this playtest (HAL's decision (31 October, after the arms report)). Limitation: recruitment is measured descriptively only (no staff-initiative off comparison; quality and development by recruitment not reported); the constants are not validated |

### 2.3 P2: five-year event, course and nation prestige; nation shares; venue moves (rules 2026-11-05)

The package merged at `787eda7` (package `7ac03c4`, `2a2820d`, `ace3b2e`, `d187a56`; "Reviewed and accepted at
d187a56") and its fix at `f5ac938` (`68676fd`).

| Id | Requirement | Status | Merge / package | Tests | Evidence | Remaining |
|---|---|---|---|---|---|---|
| P2.a | Event prestige over the last five calendar years, recency-weighted, with an annual limit | `done` | `787eda7` / `7ac03c4` | `test_world_prestige` (EventWindow, InASession) | L16 (`d70a725`); G1 passed | Constants: P2.g |
| P2.b | Course prestige apart from quality, from events hosted, lagged | `done` | `787eda7` / `7ac03c4` | CourseLag | L16; G1 passed | -- |
| P2.c | Nation prestige from success beyond expectation; each nation's share of the fixed new-golfer cohort, normalised, smoothed, bounded, future entrants only, talent unchanged (D7) | `done` | `787eda7` / `7ac03c4`; `f5ac938` / `68676fd` (no draw cap) | `test_nation_shares` (TotalsAndAllocation, SmoothingAndBounds, TalentUnchanged, Baseline, DrawCap, InTheWorld) | L09 failed, fixed by X1; U9; L16 (113 OK); G1 passed | R1 |
| P2.d | Events that outgrow their venue move to a better course in the same city; effective-dated history | `done` | `787eda7` / `ace3b2e`, `d187a56` | `test_venue_moves` (Stand, VenueMoves, SeasonSave) | VenueMoves 7 OK at `d187a56` (ledger section 3.5); L18 (184 OK); G1 passed | -- |
| P2.e | Sortable Prestige columns and dated history bars on tournament, course and nation pages; share history | `done` | `787eda7` / `7ac03c4` (`tools/observer_prestige.py`); Nations page conflict resolved in `787eda7` | InASession (one season and three weeks, every observer view); `test_observer_gaps.UnitDirectorySort` | L16; L17; G1 passed | -- |
| P2.f | Measure on two seeds at scale 0.05 (cohort totals, prestige moves and limit hits, share movers, expectation calibration table, how often venues move), then settle the constants (expectation blend, share bounds 0.25-4, 10 % step, venue-move thresholds) | `done with known limitation` | script ready (`docs/WORLD_PRESTIGE_PACKAGE.md` sections 5 and 7) | `test_venue_moves` (regression: `test_sustained_gap_moves_two_seasons_later_and_never_touches_the_plan`, `test_a_second_decision_is_added_not_overwritten`, `test_save_and_resume_keep_the_history`) | Measured on two seeds of the final build at full population (arms report section 3: a18new seed 4207, 10 seasons; seed2 seed 5309, 5 seasons): national multipliers within 0.25-4 and steps within ×1.1 every season; allocation shares and sums 35/35 per pathway; arrivals match the quotas 62/62, with 8 terminal cells not verified; same-seed totals identical 20/20. Venue moves: 0 in 15 seed-seasons, so the rule's natural activation is unexercised; the trigger funnel is reconstructed (sustained gaps blocked by "not at this course in Y+2" or "no better eligible course in the city"); the regression tests stand. No expectation calibration table | The current prestige constants are kept as the baseline for this playtest (HAL's decision (31 October, after the arms report)). Limitations: the venue-move rule's natural activation is unexercised (0 moves in 15 seed-seasons; a ±0.01 rounding band around the gap threshold of 5); 8 terminal arrival cells are not verified; no expectation calibration table |

### 2.4 G1-G3: geography, familiarity, Aggression, seasonal weather

G1 and G2 merged at `b1158d8` (rules 2026-11-08; "Reviewed and accepted at 7819114"). Evidence: L03, L12 (167 OK),
L18 (`d70a725`, 184 OK), U4.

G3 merged at `1a0cb2f` (rules 2026-11-09; "Reviewed and accepted at e19fff3"). Evidence: L04, L11 (113 OK), L18, U5,
U8; reviewer R6.

| Id | Requirement | Status | Merge / package | Tests | Evidence | Remaining |
|---|---|---|---|---|---|---|
| G1.a | State or province on every course; venue roles; why some courses host nothing | `done` | `b1158d8` / `e1669ea` | `test_familiarity_region` (CoursePlaceTests, VenueRoleTests) | L12, L18; G1 passed | -- |
| G1.b | Bounded regional baseline inside the existing familiarity mechanism (a floor, never added, counted once) | `done` | `b1158d8` / `39c8cf3` | BaselineTests, SeasonBaselineTests, EngineInputTests | L12, L18; G1 passed | Seeded comparison: G1.e |
| G1.c | Top 10 familiar courses on profiles with the value the engine uses | `done` | `b1158d8` / `172b787`, `23e288c` | TopCoursesTests, ProfileTests | L12; G1 passed | -- |
| G1.d | Home clubs, recorded explicitly; local hosting of unused municipal courses (D12) | `done` | `b1158d8` / `23e288c`, `7819114` | HomeClubTests, LocalHostingTests (Southport Brook, Wren Dunes, Fjordby Helsinki), CoursePageTests | L12 (`7819114`); G1 passed | -- |
| G1.e | Seeded season with and without the baseline: starts affected, scoring change for local golfers, timings; home clubs over a season | `done with known limitation` | `docs/FAMILIARITY_AND_AGGRESSION.md` "To run after the CPU hold" | -- | Same-seed season on `c0d1ea5` (seed 4207, 2027), baseline on and off (`docs/review/arms_comparison/G1E_FAMILIARITY.md`, `0061501`): with it on, the baseline set 6,799 of 124,224 starts (5.5 %), 3,899 golfers; with it off, none. Week 1 (identical fields): baseline-applied starts ON − OFF round-1 strokes −0.857 (n 56) against −0.044 for the reference starts. Before it, the arms report (section 3, "Familiarity") gives only baseline-applied shares with the baseline on: 5.5 % of starts in 2027 falling to 2.2 % in 2036 (a18new; seed2 5.4 % to 2.8 % by 2031), and home clubs found by country (0.1 %) | The week-1 field-matched comparison is exploratory only (a shared random stream, naive standard errors, cut-dependent later rounds); no causal or significance claim. Later weeks are descriptive across diverged worlds. Home clubs over a season are not measured separately (the floor is not recorded per start) |
| G2.a | Show the 0-100 Aggression trait as a style, not an ability grade | `done` | `b1158d8` / `63ad358` | `test_aggression_visible` (ProfileTests) | L03, L12, L18; G1 passed | -- |
| G2.b | Trait stable; reach constraints kept and take the conditions' distance factor; no second risk score | `done` | `b1158d8` / `63ad358`, `f50d8da`; wind wired into the go-for-it decision in `1a0cb2f` | ReachTests, StabilityTests; `test_weather_geography_merge` (WindReachesTheDecision, PlayHolePassesTheWind) | L18; U5; G1 passed | -- |
| G3.a | Seasonal climate by place and week; wind direction per hole; bundled offline | `done` | `1a0cb2f` / `96dff24`, `1cbf7a4` | `test_weather` (ClimateTests, WindDirectionTests) | L11, L18; G1 passed | -- |
| G3.b | Gusts: per-round gustiness, per-shot strength, archived; mean damage preserved | `done` | `1a0cb2f` / `e19fff3` | GustTests | L11 (113 OK); G1 passed | -- |
| G3.c | Skill, caddie and familiarity mitigation without immunity | `done` | `1a0cb2f` / `96dff24` | MitigationTests | L11, L18; G1 passed | -- |
| G3.d | Match-play sites and knockout days | `done` | `1a0cb2f` / `ed5ebaf` | `test_weather`; UnitRoundConditions (match-play case, `d2a79ce`) | L11; U8; G1 passed | -- |
| G3.e | Conditions recorded and shown; no rainouts, cancellations or delays; older saves keep the classic draws | `done` | `1a0cb2f`; `d2a79ce` ("wet"/"dry", never "rain") | RecordTests, ControlTests; UnitRoundConditions | U6, U8; G1 passed | -- |
| G3.f | Scope of temperature and firmness effects | `excluded from this pass by decision` | -- | -- | D17 (`0b55a2b`, decision log on rc1): out of scope for this pass | Excluded from this pass (reviewer); not a missing feature |
| G3.g | Season-scale runs with seasonal weather | `done with known limitation` | `1a0cb2f` | -- | Arms report section 3, "Weather", from the round conditions in the season files of two full-population worlds of the final build: a18new (seed 4207, 10 seasons) 40,133 rounds, wind median 9.0 mph (max 44.6), 16.1 % wet; seed2 (seed 5309, 5 seasons) 20,033 rounds, median 9.1 mph, 15.0 % wet; gustiness recorded on every round. Mean wind, wet share and gustiness by climate group and local month follow the climates (for example Mediterranean courses 15-21 % wet in winter, 1-4 % in summer; tropical wettest at mid-year) | Descriptive conditions only: no scoring effect of the weather and no weather on/off comparison reported; the arms report's review is in progress (R15) |

### 2.5 B1/B2: Biggest Upsets (recording only; no rules version)

Merged at `e4cc3db` (package `483c0b1`, `3291666`, `a36af60`, `e027e70`; "Reviewed and accepted at e027e70").
Evidence: L02, L13, L17 (`d70a725`; that run's one failure was in test_observer_profiles, X6), U6; reviewer R6
(24 upset tests). B2 and the truthfulness fixes are direct rc1 commits after `0a05310`: `1c28d09` and `b287199`
(independently accepted, R12); evidence M `1c28d09`, M `b287199`.

| Id | Requirement | Status | Merge / package | Tests | Evidence | Remaining |
|---|---|---|---|---|---|---|
| B1.a | Pre-event win estimate (`upset-model-1`), worked out before any shot with no random numbers, recorded per edition with the facts as the field was set | `done` | `e4cc3db` / `483c0b1` | `test_upsets` (ModelTests, NoHindsightTests) | L13; U6; G1 passed | -- |
| B1.b | Biggest Upsets page with a majors-only view and filters, reached from the Record Book; panel on the event page | `done` | `e4cc3db` / `3291666` | PageTests | L13; L17; G1 passed | -- |
| B1.c | Equal chances rank equal (competition ranking 1, 2, 2, 4) | `done` | `e4cc3db` / `a36af60` | `test_upsets` tied-chance test | tests.test_upsets 22 OK + tied-chance test (ledger section 3.5); G1 passed | -- |
| B1.d | Inputs persisted so every stored chance can be reproduced | `done` | `e4cc3db` / `e027e70` | `test_upsets` (`upsets.reproduce` for fields 156/80/30/6) | 24 OK at `e027e70` (ledger section 3.5); L13; G1 passed | -- |
| B1.e | Editions without an estimate show "not recorded"; no hindsight proxy | `done` | `tools/observer_upsets.py` (`3291666`); each recorded reason with its count (`1c28d09`); one status rule and wording for page, panel and story, `tools/upset_status.py` (`b287199`) | NoHindsightTests, PageTests; `test_upset_examples` (BiggestUpsetsPageTests, EventPanelTests, UnusableEstimateTests) | L13; M `1c28d09`, M `b287199`; R12; G1 passed | -- |
| B1.f | Recording changes no outcome | `done with known limitation` | `483c0b1` | HeavyEquivalenceTests (GOLF_HEAVY_TESTS=1; `GOLF_HEAVY_WEEKS` defaults to 8) | L02 (`3291666`, 35 OK); G1 passed | Shown over 8 weeks of one world; see B1.h |
| B1.g | Each upset row links to its edition's story | `done` | `fe04ab5` (merge change) | `test_upsets_stories_merge` (UpsetRowsLinkToStories) | U7, U8; L17; G1 passed | -- |
| B1.h | Whole-season equivalence and cost measurement | `done with known limitation` | -- | -- | `docs/BACKLOG.md` (`0b55a2b`): "whole-season cost measurement open"; arms report section 6 (`0061501`), a18new and seed2, 15 seasons, 21,577 editions: the upset records are 3.4 % of the raw season file (inputs 2.3 %), about 1.3 kB an edition. Offline recomputation from the stored inputs: about 2.9 s CPU a season, about 2 ms an edition, reproducing every stored estimate exactly | The in-engine overhead is not instrumented and is not inferred from total runtime; no whole-season on/off comparison was run. Outcome equivalence rests on B1.f (8 weeks) and the per-record reproduction |
| B2.a | Audited examples as regression and presentation cases, in no forced order | `done` | `1c28d09` (the audited examples, Ashcroft 2041 Australia Open, Slater 2035 USA Open, Kinnear 2042 Britannia, Jefferson 2034 Masters, Ellison 2038 major, Egger 2068 USA Open, Carroll over Harper in France, and a generic legacy edition, as fixtures with no `upset` record: only the documents' facts, no odds anywhere); `b287199` (an estimate naming no matching winner, or of an unsupported model, is never ranked and keeps its own reason; statistics store schema 7, story FACT_VERSION 4) | `test_upset_examples`: ExampleDataTests (`test_fixtures_hold_the_recorded_facts_and_no_estimate`, `test_statistics_rows_record_no_model_and_no_chance`), BiggestUpsetsPageTests (`test_examples_are_left_out_of_the_ranked_list`, `test_coverage_counts_them_as_not_recorded`, `test_not_estimated_shows_the_recorded_reason`, `test_the_same_list_with_the_examples_present_or_not`), EventPanelTests (`test_each_example_says_not_recorded`, `test_not_estimated_panel_gives_the_recorded_reason`, `test_an_estimated_edition_still_shows_its_estimate`), StoryTests (`test_no_upset_is_claimed_and_the_missing_estimate_is_named`, `test_jefferson_story_keeps_the_recorded_facts`), EventPageTests (`test_edition_page_story_tab_and_upsets_page`), UnusableEstimateTests (`test_supported_models_include_the_recording_model`, `test_rows_carry_the_model_and_the_reason_but_no_chance`, `test_not_ranked_and_not_counted_as_not_recorded`, `test_one_reason_in_the_coverage_line_the_panel_and_the_story`), StoreRebuildTests (`test_old_schema_store_is_rebuilt_with_only_the_corrections`) | M `1c28d09` (12 OK), M `b287199` (17 OK; 10 of 17 fail on the previous code); R12; G1 passed | -- (O9 done: truthful no-estimate fixtures; no odds invented) |

### 2.6 T1-T3: tournament stories (observer only; NARRATIVE_VERSION 3)

Merged at `fe04ab5` (package `d851d91`, `623d193`, `159cffa`, `4f9a294`, `aafe369`, `92405d9`, `696a72a`, `2306549`;
"Reviewed and accepted at 2306549"). Evidence: L15 (102 OK), L17, U7; reviewers R5 and R6.

| Id | Requirement | Status | Merge / package | Tests | Evidence | Remaining |
|---|---|---|---|---|---|---|
| T1.a | Local generation (no AI service); written on open, cached | `done` | `fe04ab5` / `d851d91` | `test_stories` (StoryTextTests, StoryCacheTests) | L15; U7; G1 passed | -- |
| T1.b | Story tab on every edition (majors and prestigious events first, lead line on the result); profile and My World entry points | `done` | `fe04ab5` / `623d193` | StoryLiveViewTests, StoryWorldTests | L15; G1 passed | -- |
| T1.c | Fact record first, then patterns (upset, runaway, comeback, playoff) | `done` | `fe04ab5` / `d851d91` | StoryFactTests, StoryPatternTests | L15; G1 passed | -- |
| T1.d | How the winner played from recorded golf statistics; strokes gained against the engine table | `done` | `fe04ab5` / `92405d9` | StoryGolfTests | L15; G1 passed | -- |
| T2.a | Upset context only from the edition's recorded estimate | `done` | `fe04ab5` / `aafe369`; `b287199` (the story names the missing or unusable estimate and its reason and claims no upset; FACT_VERSION 4 rebuilds cached facts) | `test_stories` story unit classes; `test_upset_examples` (StoryTests, UnusableEstimateTests) | L15; M `b287199`; G1 passed | -- |
| T2.b | Nothing invented; qualified career bests (same format and sample); pending comparisons rechecked; old cached stories rebuilt | `done` | `fe04ab5` / `696a72a`, `2306549` | StoryDefectTests | L15; R5 (independent 47 OK); G1 passed | -- |
| T2.c | A rolled-back history redraws | `done` | `fe04ab5` / `4f9a294` | `test_stories` non-simulation tests | 31 non-simulation story tests (ledger section 3.5); G1 passed | -- |
| T3.a | Prose kept out of simulation loops; per-season index for long histories; cache in `observer_cache/stories.sqlite` | `done` | `fe04ab5` / `159cffa` | StoryArchiveIndexTests, StoryIsolationTests | L15; G1 passed | -- |
| T3.b | Measure throughput, latency, memory, and save and index growth on a long history | `done with known limitation` | `docs/review/arms_comparison/stories_timing.py`, `story_timing.json` (`79b78d6`) | StoryWorldTests (L15) | Arms report section 4, independently reviewed (R15): 20 majors from run A's 45-season archive (legacy `473690a`) assembled by the candidate's assembler (`c0d1ea5`), with `nice -n 19` beside two simulations. Cold median 7.44 s, max 11.85 s; with the story index built, median 0.103 s; latest edition opened first 3.08 s (facts pending), then 102 s of background story indexing; the one-off read-only side index 218 s, 1.05 GB; story cache 115.8 MB after the sample | Indexed story assembly only (`observer_stories.tell`), not full UI rendering or the owner's hardware; "cold" is application-cache cold, not filesystem cold; a legacy `473690a` archive with the candidate assembler; the 2.65 GB RSS is the process's lifetime high-water mark, not a per-story figure. No claim of instant cold UI opens or of a verified 120 s target |

### 2.7 C2: death after retirement (rules 2026-11-07; decision D6)

Merged at `a195dfe` (`c29f6b0` = `build/v16@2325d50` + `build/v16-death@fa787d4`, package `6979f86`, `fa787d4`).
The merge records "Reviewed package integration/v16-c2 at c29f6b0". Evidence: L05 (51 OK), L06 (103 OK), L19
(`d70a725`), U1-U3, X3.

| Id | Requirement | Status | Merge / package | Tests | Evidence | Remaining |
|---|---|---|---|---|---|---|
| C2.a | Death processed in the winter after each season at (Y, 53), with rising annual risk; age frozen at death | `done with known limitation` | `a195dfe` / `6979f86` | `test_mortality` (Curve, Archive) | L05, L19; G1 passed | The curve is a provisional game calibration (D6), not validated |
| C2.b | No active competitive golfer dies; retired golfers working as coaches or caddies can (D6) | `done` | `a195dfe` / `6979f86` | WhoCanDie, WorkingStaff; SmallWorld.test_deaths_only_in_the_winter_and_never_an_active_golfer | L05; G1 passed | -- |
| C2.c | Identity, results, records and relationships preserved; staff partnerships end with the reason; nothing after a death | `done` | `a195dfe` / `6979f86`, `fa787d4` | SmallWorld (test_dead_staff_stop_working_and_their_partnerships_end_with_the_reason, test_no_result_or_team_after_a_death, test_season_files_and_people_table) | L05; G1 passed | -- |
| C2.d | Idempotent, reproducible annual processing; save and resume | `done` | `a195dfe` | Reproducible; SmallWorld.test_saved_and_resumed_the_same | L05; G1 passed | -- |
| C2.e | Observer: profiles, the living/deceased directory filter, archive-only browsing, My World death item and departure cleared together | `done` | `a195dfe`; `17909f4` (alive filter kept); `2516d86` | Observer; SmallWorld.test_profile_directory_and_filters, test_archive_only_browsing_shows_deaths; UnitWinterDeathAndDeparture | L06; U1; X3; R4; G1 passed | -- |

### 2.8 D5/D5a: return from work to full-time amateur golf (rules 2026-11-06)

Merged at `a90ea85` (package `0c5cdd7`, `5c15e32`; "Reviewed and accepted at 5c15e32, including the review fix").
Evidence: L01, L10 (50 OK), L19, U2.

| Id | Requirement | Status | Merge / package | Tests | Evidence | Remaining |
|---|---|---|---|---|---|---|
| D5.a | A working amateur can return when finances and results support it, never guaranteed; no hard age cut-off, a smooth decline with age; avoid lifestyle flipping (D5, D5a) | `done with known limitation` | `a90ea85` / `0c5cdd7` | `test_amateur_return` (Golfer, Conditions, WorkStart) | L01, L10, L19; G1 passed | Thresholds are provisional (D5a) |
| D5.b | The season budget includes committed coach and caddie costs | `done` | `a90ea85` / `5c15e32` | `test_amateur_return` regression (a 23-year-old with $8,000, 8 trips $4,000, a $12,500 coach: no return) | L10; G1 passed | -- |
| D5.c | Validate return and re-block rates on a full population (D5a) | `done with known limitation` | -- | -- | A 5 % world over three seasons, 3, 2 and 1 returns (`docs/AMATEUR_WORK_PATHWAY_PROPOSAL.md`). The arms report (section 1, "After the job") gives, per pathway entry, the first career transition by age band: "returned to full-time golf" a21old 21+ 43/242 (17.8 %); a18old 18-20 10/56 (17.9 %), 21+ 24/192 (12.5 %). Arms report section 5 (`dc41950`): return and re-block by age band over the four arms, from the season files' transitions and every `amateur_return` evaluation. 1,166 returns (1,125 people); 157 censored (no archived next season). Of the 1,009 observed: 0 with any cash-blocked week and 0 pathway re-entries in the next season; 505/1,009 took a job the following winter, a separate event. Section 5.1: on the matched 989, the job chance anticipated at return sums to 431.9, the next winter's evaluated chance to 525.2, realised 505. Completeness assertions A1-A3 pass | Accepted provisionally by the reviewer. The predicted-against-realised comparison is a proxy (recorded inputs cannot separate the causes of the difference); return is described by age band, across diverged worlds; no tuning (D5a thresholds stay provisional) |

### 2.9 F1.c, F1.h and F2

| Id | Requirement | Status | Merge / package | Tests | Evidence | Review | Remaining |
|---|---|---|---|---|---|---|---|
| F1.c | Support form: restricted in-kind golf expenses only; no unrestricted cash or living costs; amateur prize eligibility unchanged; caps $25k / $12k / $5k as the initial test calibration (D10) | `done` | `138ce06` (before `473690a`); decision `2325d50` | `test_amateur_support` (Rules, Seasons, Shown) | L10 (`5c15e32`, 50 OK); pinned B vs C comparison (A-D report); G1 passed | D10 | Changing the caps needs evidence and a decision (D10); keeping them does not |
| F1.h | Affordability and zero-start seasons by region, age, status and standing; seeded and procedural development apart | `done` | `23701cf` (brings `15374c9`) | `test_diagnostic_report` | L22 (`d70a725`, 87 OK); "By age and by amateur standing (runs B and C)" in the A-D report; G1 passed | -- | Pinned-build figures only |
| F2 | All 269 recorded major-affordability declines covered through the real entry path; admission and booking repeated on the same state (D11) | `done with known limitation` | `2e08358` / `5848655`, `6c23aca`, `d51ad9a`, `3e58a7d` | `test_major_affordability_269` (Coverage269); `test_major_funding` | L14 (`3e58a7d`, 20 OK); L19; G1 passed | "Reviewed and accepted at 3e58a7d"; accepted narrowly (ledger section 3.5) | Synthetic golfers under today's rules: not a historical replay and not a post-settlement retry proof |

### 2.10 E1.f: decision evidence

Merged at `23701cf` (`9e0b042` plus the format /2 extension made in the merge). The documentation fix is `72ab740`; the robustness fix found by G1 is `376c7a9` (E1.f.8).
Evidence:
- L20 (`d70a725`, 5 OK);
- L21 (outcomes identical to the parent build `16c83e8`, 1 OK);
- L22 (test_decision_evidence in 87 OK);
- M `5664853` (56 OK);
- the pre-final smoke on `0a05310` (G2 there): outcomes identical with the evidence on and off;
- G4 on `c0d1ea5`: passed, no outcome part differs with the evidence off.

Review: `72ab740` is "From review of d70a725". The ledger records no acceptance of the package. The reviewer
settled its scope in `ac310a8` (R14): format /2 fulfils E1.

| Id | Requirement | Status | Merge / package | Tests | Evidence | Remaining |
|---|---|---|---|---|---|---|
| E1.f.1 | Scheduling: each monthly plan's target by its parts, starts, fatigue, funds, four weeks' availability and activities, training value, injury weeks, flags, and the slower terms | `done` | `23701cf` / `9e0b042` | `test_decision_evidence` (TargetParts, RecordShape, ArchiveRoundTrip) | L22; L20; G1 passed | -- |
| E1.f.2 | Career decisions (retire from a tour or a job, stop chasing, turn professional, amateur job, comeback): probability, draw, outcome, logit terms, inputs | `done with known limitation` | `23701cf` / `9e0b042`; `72ab740` | CareerTerms, WinterDecisions | L22; L20; G1 passed | Stored figures are rounded and the recorded outcome is authoritative (`72ab740`) |
| E1.f.3 | Amateur-return evaluations (format /2) | `done` | `23701cf` | AmateurReturn | M `5664853`; L22; G1 passed | -- |
| E1.f.4 | Mortality: evaluations by age band and every death's risk and draw (format /2); a survivor's draw is reproducible from the rule | `done` | `23701cf` | Mortality | L22; G1 passed | -- |
| E1.f.5 | Recording changes no outcome (on and off; against the parent build) | `done` | `23701cf` | `test_decision_evidence_world.DecisionEvidenceWorld` (test_outcomes_are_identical_with_recording_on_and_off, test_outcomes_are_identical_to_the_parent_build) | L20, L21 at `d70a725`: pre-final, before rules 2026-11-10 and 2026-11-11 were merged; the pre-final smoke on `0a05310`: outcomes identical with the evidence on and off; G4 on `c0d1ea5` passed: no outcome part differs with the evidence off | -- |
| E1.f.6 | Full-world size and time of the richer evidence (07:24 decision: keep it, measure it) | `done with known limitation` | -- | test_growth_is_small (small world only) | Estimate 11-13 % of a mature season file, from scale 0.10 measurements (`docs/DECISION_EVIDENCE.md`). Pre-final, measured on `0a05310` (smoke, seed 4207): season-file growth +6.8 %, evidence 830 KB gzip in season 1 (13.04 MB against 12.21 MB; 200.5 s against 188.4 s; checkpoint 38.1 MB against 36.4 MB), 901 KB in season 2 (`docs/review/F1_BASELINE_PRESSURE_AND_E1_SCOPE.md`, `1de4119`); measured on `c0d1ea5` by G2 (seed 4207): 2027, season file 13,039,656 B with the evidence against 12,208,596 B without (+6.8 %), evidence 830,379 B gzip (6.4 %), 201.5 s with it; 2028, 12,567,224 B, evidence 901,302 B (7.2 %), 197.2 s; bounds held (at most 13 plans, 0 over, at most 3 career rows) | Measured on a new world's first two seasons only; a mature world of about 13k golfers is not measured. The time difference is one pair of runtimes on a shared machine, not an isolated overhead. Written into `docs/DECISION_EVIDENCE.md` by the docs-only commit `a2d56fb` (`build/v16-docs-final`, from `c0d1ea5`; not on rc1) |
| E1.f.8 | An evaluation without a named model records nothing and decides exactly as with recording off (a stood-in model had crashed the winter) | `done` | `376c7a9` (rc1, after `0a05310`) | `test_decision_evidence.WinterDecisions.test_models_stood_in_for_record_nothing_and_change_nothing`; `test_amateur_residence` | X10: found by G1 on `0a05310` (3 errors); M `376c7a9` (24 OK); G1 on `c0d1ea5` passed | -- |
| E1.f.7 | Remaining recording gaps: the weekly entry choice and per-event values and trip costs; the planner's per-week values; the coach/caddie career draw; the backers' review terms and draws | `done with known limitation` | `docs/DECISION_EVIDENCE.md` "Not recorded (remaining gaps)"; decision `ac310a8` (`docs/review/F1_BASELINE_PRESSURE_AND_E1_SCOPE.md` section 2, on `origin/build/v16-report`) | -- | Reviewer's decision (R14): format /2 fulfils E1; no format /3 in this pass and no further instrumentation | The listed gaps are disclosed limitations, not missing features (O8 closed by decision) |

### 2.11 Observer gaps

Merged at `17909f4` (package `1cc69a7`, `ad5be31`, `7f661b0`, `5f87e42`, `571fa72`, `d04fa5b`; "Reviewed and accepted
package build/v16-observer-gaps at d04fa5b"). Later rc1 commits: `2516d86`, `d2a79ce`. Evidence: L08 (105 OK),
L17 (`d70a725`), U1, U7, U8.

| Id | Requirement | Status | Merge / package | Tests | Evidence | Remaining |
|---|---|---|---|---|---|---|
| OG1 | Directory sorts in both directions (Prestige and every sort), missing values last (P1.f) | `done` | `17909f4` / `1cc69a7` | `test_observer_gaps.UnitDirectorySort` | L08; G1 passed | -- |
| OG2 | A golfer's Prestige with its two parts, current achievement and lasting legacy (P1.d) | `done with known limitation` | `17909f4` / `ad5be31` | UnitPrestigeParts | L08; G1 passed | Parts are shown for now; the history alone says "not recorded" |
| OG3 | My World team news: first shared major; retirement into a staff role (S1.e) | `done` | `17909f4` / `7f661b0` | UnitTeamNews | L08; U1; G1 passed | -- |
| OG4 | Round conditions: one line per round, "not recorded" when absent; wind direction and gusts where recorded; knockout days; "wet"/"dry"; weather never cancels | `done` | `17909f4` / `5f87e42`; `1a0cb2f` (merge resolution); `d2a79ce` | UnitRoundConditions, WorldGaps | L08; U5, U8; G1 passed | -- |
| OG5 | Winter boundary: winter retirements, tour and status changes and deaths dated (Y, 53); Mark all as read covers the winter | `done with known limitation` | `17909f4` / `571fa72`, `d04fa5b`; `2516d86` | UnitWinterBoundary, UnitWinterDeathAndDeparture | L08; U1 (14 OK); X3; R4 (32 tests, scoped acceptance, "rerun on final head": G1 passed) | A watermark saved before `2516d86` at (Y, 52) shows that winter's items once more (`2516d86` message) |

### 2.12 Diagnostic report fixes

`build/v16-report` (`8fcf2a5`) merged at `d70a725`; later direct rc1 commits followed. Review: R3 covers `5ad7a50`
and `5073485`. `d39d613` is the review of `697183c` and `e759903`. No review is recorded for `c2a1391`.

| Id | Requirement | Status | Commits | Tests | Evidence | Remaining |
|---|---|---|---|---|---|---|
| DR1 | Recorded state in neutral wording; how resumed runs ended; season time over segments; guard marks | `done` | `6aa5f9c`, `5073485` (in `d70a725`) | `test_diagnostic_report` (RunEndings) | U11; L22; G1 passed | -- |
| DR2 | Denominators: no start and financial exclusion apart; golfer-season denominators | `done` | `5073485`, `5ad7a50` | ExclusionByGroup | U11; R3; L22; G1 passed | -- |
| DR3 | Conversions: pathway conversions shown (B 224, C 247); B-vs-C caveat | `done` | `5ad7a50` | `test_diagnostic_report` | U11; R3 | -- |
| DR4 | Provenance: section in the report; A's segment 2 corrected to 2034-2054 (21 seasons); final provenance | `done` | `6aa5f9c`, `5ad7a50`; `0a05310` | `test_diagnostic_report` | X4; R3 | -- |
| DR5 | Age in force: the pathway table grouped by the age recorded per run (pinned runs stay 21); both run modes record it | `done` | `e759903`, `d39d613` | PathwayAgeInForce; `test_long_run_safeguards.WorldRulesRecorded` | X7, X9; M `e759903`, M `d39d613`; G1 passed | `d39d613` independently accepted (R9) |
| DR6 | Memory: only the development diagnostics of each season file kept | `done with known limitation` | `c2a1391` | SeasonFilesTrimmed | X8; M `c2a1391` (13 OK); the A-D report completed; independently accepted (R9) | Memory is reduced, not constant: each year's development section is retained |
| DR7 | "Overall at 19" from the exact season; season files read through the manifest; seeded and procedural apart | `done` | `43bf2c4`, `a11f29a`, `15374c9` | AtNineteen | L22; G1 passed | -- |

### 2.13 Review-document deliverables

| Id | Requirement | Status | Commits | Evidence | Remaining |
|---|---|---|---|---|---|
| RD1 | Interim B/C/D report and its provenance | `done` | `5073485`, `5ad7a50` (merged `d70a725`); `docs/review/DIAGNOSTIC_RUNS_BCD_INTERIM.md`, `docs/review/DIAGNOSTIC_RUNS_PROVENANCE_INTERIM.md` | R3; labelled pinned `473690a`, not final-feature-world evidence | -- |
| RD2 | Under-21 zero-start and college-starts diagnosis | `done` | `8fcf2a5` (merged `d70a725`); `docs/review/U21_ZERO_START_AND_COLLEGE_INTERIM.md` | Read-only, pinned `473690a`, runs B-D | Its two candidate findings were acted on by DL1 and DL2 |
| RD3 | Remedy options (U1-U4, K1-K4, proposals P1-P3, the required tests, the validation plan) | `done with known limitation` | `9f2ac00`, `9baea7a` on `origin/build/v16-report` (not on rc1); `docs/review/U21_AND_COLLEGE_REMEDY_OPTIONS.md` | -- | Not on the candidate. P1 and P2 were implemented as DL1 and DL2; its validation plan (paired fresh runs) was run as the `c0d1ea5` comparison arms (DL1.m, DL2.m) |
| RD4 | The A-D diagnostic report (all four runs complete) and the runs' final provenance | `done` | `0a05310`; `docs/review/DIAGNOSTIC_RUNS_ABCD.md`, `docs/review/DIAGNOSTIC_RUNS_PROVENANCE.md` | Generated read-only at this head; labelled pinned `473690a` | No review recorded yet |

### 2.14 The delegated decisions of 07:24 UTC (reviewer, under the owner's delegation)

| Id | Requirement | Status | Merge / package (rules) | Tests | Evidence | Review | Remaining |
|---|---|---|---|---|---|---|---|
| DL1 | Work pathway minimum age 18 in new worlds; older saves keep 21; every other safeguard unchanged; no grants or guaranteed starts | `done` | `f9bd765` / `c848952`; rules 2026-11-10; rule text `e759903` | `test_work_pathway.Age18Tests` (the reviewer's boundary cases), Counting, Deciding | M `5664853` (56 OK); M `e759903` (29 OK); in no serialized queue group (merged after `d70a725`); G1 passed | R8: independently tested, including a real monthly in-season transition (age 18, rank 301; unchanged cutoff; no cash grant) | Full-population outcomes: DL1.m |
| DL1.m | Measured outcomes of the pathway from 18: under-21 floor seasons and zero starts, time to a first start, job, return and turn-pro outcomes by age against 21+ | `done with known limitation` | Arms a21old against a18old on `c0d1ea5` (seed 4207, 10 seasons each; `9df86eb`, `88bf8a6`) | -- | Arms report section 1 (`79b78d6`). The arms are identical through 2027 and diverge from week 45 of 2028 (the first entry below 21). Pretreatment 2027 cohort, N 241 (full-time non-college amateurs aged 17-20), a21old against a18old, by 2036: golfers with any zero-start season 4 against 1; retired 27 against 29; pro full-time 11 against 18; pathway entrants 79 against 74. All pathway entries: 242 against 248, 56 of them at age 20 in a18old. End-status 18-20 zero-start seasons 12/2,132 against 0/2,160. Time to a first start after the job, and return and turn-pro shares by band, are reported (section 1, "After the job"). Previously: pinned runs, 37 of 37 under-21 zero-start seasons at the credit floor (RD2) | Descriptive only: the worlds diverge (fewer than 1 % of rows identical from 2029), so no individual counterfactual. Time to the job is reconstructed from monthly plans, not actual weekly access. Review of the arms report in progress (R15) |
| DL2 | College amateurs at the members' class in their home region's ordinary open amateur events; rotation by open-amateur starts; everything else unchanged; older saves keep the old order | `done` | `5664853` / `459322c`; rules 2026-11-11 | `test_college_open_access` (OrdinaryOpenTests, ClassAndRotationTests, FieldFillingTests, SavedWorldTests, RulesTests); `test_access` | M `5664853` (56 OK); R7: an actual 5 % world, weeks 17-18, 145 open-amateur starts by 112 golfers; G1 passed | R7: independently accepted (10 tests, the 5 % world, exact counter/result match, nonzero save/reopen priority equality, next-year counter reset) | Full-population effect: DL2.m |
| DL2.m | Paired fresh full-population runs (on and off, same seed): college and open-amateur starts by region, field fill, members' starts lost | `done with known limitation` | Arms a18old against a18new on `c0d1ea5` (seed 4207, 10 seasons each) | -- | Arms report section 2 (`79b78d6`), by region and season, with field fill and shut-out weeks. Fixed creation cohort, North America series members (N 479): cumulative 2027-2036 open starts per head 81.8 → 72.1, cumulative shut-out weeks per head 74.6 → 136.6. End-status 2036: college open starts per player, all regions, 6.58 → 9.15; North America members' open starts per member 9.40 → 7.76 (the part-time schedule target is 8); no group's zero-start share increased (0 % in both arms). `docs/BACKLOG.md` at `c0d1ea5` still says "pending" (updated in `a2d56fb`) | Reviewer: the trade-off is consistent with the design; the policy is retained and the cost to members disclosed, not offset by larger fields (R15). Descriptive only: the arms differ from week 1 of 2027 and the worlds diverge, so no individual counterfactual. Shut-outs are golfer-weeks, not entries per event |
| DL3 | Keep the richer decision evidence despite the estimated growth; measure the full-world impact | `done` | `23701cf` (kept on rc1); D15 (`0b55a2b`) | -- | -- | -- | The measurement is E1.f.6 (O3) |

### 2.15 Live partnership history

| Id | Requirement | Status | Commits | Tests | Evidence | Review | Remaining |
|---|---|---|---|---|---|---|---|
| LP1 | This season's partnerships shown at once on coach and caddie pages and in golfer team history: merged with the archive by stint id, live end-state overriding, marked "this season", dated, with initiator and reasons | `done with known limitation` | `697183c` (after `9cac183`); `d39d613` (footer with nothing archived) | `test_observer_profiles` (LivePartnerships; ProfilesAndStatsTests.test_coach_clients_are_current_assignments) | X6; M `697183c`; M `d39d613` (25 OK); G1 passed | `9cac183` judged insufficient; `697183c` reviewed, findings fixed in `d39d613`; `d39d613` independently accepted (R9) | Time worked together and result counts appear only once the season is archived (`697183c` message) |

### 2.16 Calibration questions raised by the pinned runs (C1)

Three rows. Each consolidates the audit and roadmap rows that ask the same question (sections 3 and 4 point
here). All three are settled for this playtest by HAL's decision (31 October, after the arms report): CQ1 and CQ2
are kept with their limitations, and CQ3 is excluded from this pass.

| Id | Requirement | Status | Evidence | Remaining |
|---|---|---|---|---|
| CQ1 | The 89-at-18 outlier. Run A: Rupert Vaughan (England, arrived 2046), 89.1 at 18 (season end), 92.0 at 19, potential 97.1, peak 96.7 at 30, 128 wins, 30 majors, still active. Investigate the extreme tail and first-year gains before any cap (C1.c) | `done with known limitation` | Diagnosis published: `docs/review/VAUGHAN_OUTLIER_DIAGNOSIS.md` (`b613b3b`, `origin/build/v16-report`, not on rc1). A rare organic tail the rules produce: created Overall 85.31, potential 97.01; no generation or development bug found (R10). The decision log on rc1 (`0b55a2b`) records D16: no simulation tuning in this pass, keep rare organic potential, maturation timing a design consideration for the next playthrough | Decided (HAL's decision (31 October, after the arms report), with D16 `0b55a2b`): rare organic potential and the current maturation are kept for this playthrough, explicitly as provisional. This is retention, not a mechanics change. Limitation: provisional, and the calibration is unvalidated; individualized maturation (learning rate relative to the drawn peak age) stays a design consideration for the next playthrough (O6 closed) |
| CQ2 | Assess initialization to steady state: the seeded world starts below the population's equilibrium. A calibration assessment, not a defect or a runaway | `done with known limitation` | Run A plateaus near 13.1k active for its final ~17 seasons (13,253 at the end), with arrivals and exits about level; it starts at 6,656. B, C and D (10 seasons) are still rising (to 10,619, 10,638, 10,446). Accounting reconciles every season. The ">20 % from start" flag (A 39 of 45 seasons) measures distance from the seeded start, not growth at equilibrium. The final build's comparison arms on `c0d1ea5` rise the same way: from 6,409 golfers at the start to 10,337 (a21old), 10,343 (a18old) and 10,339 (a18new) active after the tenth season, as the long-run harness counts them after that winter's arrivals and exits (the arms report's 2036 season-file golfer rows, before that winter, are a21old 10,027 and a18old 10,056) | Decided (HAL's decision (31 October, after the arms report)): the initialization size is kept as the baseline for this playtest. Limitation, as measured: the seeded start sits below equilibrium (run A plateaus at about 13.1k; the 10-season worlds are still rising) (O7 closed) |
| CQ3 | Calibration assessment against tolerance bands. First the owner sets bands (C1.f). Then the run evidence is assessed against them: peaks and win counts, decline timing and rate by part of the game, starting distributions and the influence of potential and coaches, prodigy and slow-burn careers, late and age-26 entrants, injury frequency, stamina and recovery, superstar scheduling and starts (C1.e), and amateur financial pressure (F1.i) | `excluded from this pass by decision` | Seeds, lengths and time approved (D4, D9); no bands. The A-D report has the tables (peaks, development and aging by part of the game, B against C); nothing has been assessed against bands. The F1 baseline pressure is documented and accepted (`ac310a8`, `1de4119`; R14): on the pinned runs, 0/87 tracked top-50 golfer-seasons and 136/3,368 (4.0 %) tracked golfer-seasons ranked beyond 300 were cash-blocked; 224 pathway conversions in B. It describes the baseline only, not a calibration verdict | Tolerance bands not set for this playtest; baseline retained with measured limitations; not a missing feature (HAL's decision (31 October, after the arms report): no target bands are invented and nothing is tuned without evidence). The measured limitations are documented in the F1 baseline (`ac310a8`, `1de4119`), the A-D report and the arms report (O5) |

### 2.17 Constraints

| Id | Constraint | Status | Where | Evidence |
|---|---|---|---|---|
| CN1 | No career mode | `done` | Deferred by the owner. Nothing in `473690a..c0d1ea5` adds a career mode | `docs/BACKLOG.md` ("Planning after the world systems are ready") |
| CN2 | No mobile or small-screen work | `done` | Deferred by the owner | `docs/BACKLOG.md` ("Mobile and small screens: Deferred") |
| CN3 | Hide Results stays removed | `done` | Legacy settings are read for compatibility only (F3.f) | `test_myworld`, `test_cohort`; L06; G1 passed |
| CN4 | Fresh v2 worlds only; unsupported saves browse or copy only | `done` | `dd0bb27`. Each overnight rule is gated so older saves keep the old behaviour: `work_pathway_min_age` 21, `college_open_access` off, weather "classic", amateur return off (`__setstate__` defaults in `golfsim/season.py`) | `test_observer_app`; `test_college_open_access.SavedWorldTests`; `test_calendar_v2.ClassicWorldsStayClassic`; G1 passed |

## 3. The rest of the expanded roadmap

Rows carried from the 31 October matrix (`b796c03`). Code from before `473690a` was last full-suite tested at
`e615b2e` (573 tests, `docs/V17_PASS_REPORT.md`), cited below as "V17". G1 passed on `c0d1ea5` for every row. Rows covered in
section 2 point there.

| Id | Requirement | Status | Where | Tests | Evidence / notes |
|---|---|---|---|---|---|
| F1.a | Sponsorship for amateurs who show success (observable results, ranking, invitations, uncertain signals) | `done` | `138ce06` | `test_amateur_support` | L10. "Scouting" here is results-based (top 150 by ranking points in 26 weeks) |
| F1.b | Modest versus elite support; no unlimited funding; does not force turning professional | `done` | `138ce06` | `test_amateur_support` | L10. Bands A/B/C |
| F1.c | Cash, equipment, restricted coverage and prize eligibility distinguished | `done` | section 2.9 | | D10 |
| F1.d | Eligibility, amounts, payment timing, renewal, discontinuation | `done` | `138ce06` | `test_amateur_support` | L10. Week-1 budget, in-season upgrades, renewal one band down, ends on turning pro |
| F1.e | A once-only advance is not counted twice | `done` | `138ce06` | `test_amateur_support` | No advance by design: costs drawn as incurred against one season cap |
| F1.f | Credible response to persistent exclusion of adult non-college amateurs | `done with known limitation` | sections 2.1 (N2) and 2.14 (DL1) | | Effect of the age-18 change measured descriptively only (DL1.m) |
| F1.g | Return from work to full-time amateur golf | `done with known limitation` | section 2.8 | | Validated descriptively on the full population, provisionally accepted (D5.c) |
| F1.h | Report affordability and zero-start spells by region, age, status, standing | `done` | section 2.9 | | |
| F1.i | Keep financial pressure below the supported elite | see O5 (excluded) | A-D report, "Amateur support: run B (with) against run C (without)"; `docs/review/F1_BASELINE_PRESSURE_AND_E1_SCOPE.md` (`ac310a8`, `1de4119`) | -- | Baseline pressure documented and accepted (R14): it falls on lower-ranked amateurs, not the elite; a description, not a calibration verdict. Tolerance bands stay O5 (CQ3) |
| F1.j | Test cash identities, renewals, duplicate processing, family and backer interactions | `done with known limitation` | `138ce06` | `test_amateur_support`, `test_finance_integration` | L10, L16. No backer-specific interaction test found |
| F1.k | Sponsor values proposed and approved | `done` | `docs/AMATEUR_SPONSORSHIP_PROPOSAL.md`; D10 | -- | D10: the caps are the chosen initial test calibration |
| F2.a | Every earned major place funded; money never the sole rejection | `done` | `45151e1` | `test_major_funding` (Guarantee, AllMajors) | L14 |
| F2.b | Injury, retirement, expired eligibility and voluntary refusal stay distinct | `done with known limitation` | `45151e1` | `test_major_funding` | L14. No dedicated voluntary-refusal test found in `test_major_funding` or `test_major_affordability_269` |
| F2.c | Restricted in-kind organiser support, recorded, counts as coverage not cash | `done` | `45151e1`, `289a0c9` | `test_major_funding` (MoneyFacts) | L14 |
| F2.d | Ordinary events and qualifying keep normal finance | `done` | `45151e1` | `test_major_funding` | L14 |
| F2.e | All 269 recorded declines as reconstructed scenarios | `done with known limitation` | section 2.9 | | |
| F2.f | No duplicate reimbursement, double funding or windfall | `done` | `45151e1`; `3e58a7d` (repeat on the same state) | `test_major_funding`, `test_major_affordability_269` | L14 |
| F3.a | USA Open U1 through the tenth anniversary | `done` | `2ab1176` | `test_exemption_window` (USAOpenChampions) | V17 |
| F3.b | One current playing-status rule; historical status kept | `done with known limitation` | `tools/observer_data.py` | `test_myworld` | L06, L17. Keeping old seasons' status has no dedicated test |
| F3.c | Retirement emitted once at the recorded transition; stable identity | `done with known limitation` | `26df0bf`, `tools/observer_myworld.py` | `test_myworld` | L06, L17. Reload not separately tested |
| F3.d | Comparison top 10s exclude qualifying | `done` | `tools/observer_compare.py` | `test_compare` | V17; the fixture fixed after G1 on `0a05310` (X11, `aa66095`, 7 OK) |
| F3.e | Cohort Highest level includes live appearances | `done` | `tools/observer_cohort.py` | `test_cohort` | L05 |
| F3.f | Hide Results only as compatibility | `done` | `tools/observer_myworld.py`, `tools/observer_cohort.py` | `test_myworld`, `test_cohort` | L05, L06 |
| E1.a | Cash, reserves, support, trip costs, final entry reasons | `done` | `289a0c9` | `test_major_funding` (MoneyFacts), `test_access_ledger` | L14; V17 |
| E1.b | Injury episodes and lifecycle transition dates | `done` | `7d63213`, `5fdc76b` | `test_living_views`, `test_injury_timing` | L16 |
| E1.c | Creation time, path, attributes; diagnostic potential, ceilings, peak age, aging rate | `done` | `d7dacfc` | `test_development_evidence` | V17 |
| E1.d | Dated aging snapshots that reconcile by source | `done` | `92b3925` | `test_development_evidence` | V17; reconciled every season in runs A-D (pinned) |
| E1.e | Staff exposure and coach-quality summaries | `done` | `d7dacfc` | `test_development_evidence` | V17 |
| E1.f | Target components, fatigue/recovery, retirement and turn-pro inputs | see section 2.10 | | | |
| E1.g | Instrumentation changes no result | `done` | `tools/equivalence_check.py`; per package: DecisionEvidenceWorld, HeavyEquivalenceTests | -- | L02, L20, L21; the pre-final smoke on `0a05310` (outcomes identical on and off); G4 on `c0d1ea5` passed (no outcome part differs) |
| E1.h | "Not recorded" for old data; hidden fields not exposed; versioned schema; storage measured | `done` | `golf-legacy-development/1`; `golf-legacy-decision-evidence/2` | `test_development_evidence`, `test_decision_evidence` | L22. Full-world size of the decision evidence: E1.f.6 |
| E2.a | Data pages use desktop width; wide viewports tested and recorded | `done with known limitation` | `26df0bf` | `test_myworld` | Measured by hand at 3,440 and 2,560 px (V16 report); pre-final navigation on `0a05310` at 1920 and 1366 px passed (140 pages, 0 failing); G3 on `c0d1ea5` passed (160 pages, 0 failing, overflow 0) |
| E2.b | Overall and single attributes | `done` | `e2e60f4` | `test_living_views` | L16 |
| E2.c | Physical, technical, mental group views | `done` | section 2.1 (N5.b) | | |
| E2.d | Annual levels and changes | `done` | `e2e60f4` | `test_living_views` | L16 |
| E2.e | Charts persist through retirement | `done` | `e2e60f4` | `test_living_views` | L16 |
| E2.f | Coach and caddie Ratings sections | `done with known limitation` | `32bc43d`, `eba01e1` | `test_living_views` | L16. No staff-skill history chart |
| E3.a | Current injury, onset, expected and actual return, time missed, lasting losses | `done` | `7d63213`, `5fdc76b` | `test_living_views`, `test_injury_timing` | L16 |
| E3.b | Announced duration apart from actual absence | `done` | rules 2026-11-02 | `test_injury_timing` | V17 |
| E3.c | Injury and return notifications | `done` | section 2.1 (N5.a) | | |
| E3.d | Profiles, summaries and My World agree on episodes | `done` | section 2.1 (N5.a) | | |
| E3.e | Missed events linked to injury only by a recorded reason | `done` | `tools/observer.py` | `test_living_views` | L16 |
| E3.f | No fabricated past medical detail | `done` | `tools/observer.py` | `test_living_views` | L16 |
| E3.g | Body-part damage or injury-rate tuning | `excluded from this pass by decision` | -- | -- | Excluded from this pass (reviewer; D17, `0b55a2b`). Assessing injury frequency falls under O5, also excluded (N19.01) |
| P1.a | Prestige on profiles; sortable directories including retired and deceased people | `done` | `32bc43d`; `17909f4` (alive filter) | `test_living_views`, `test_mortality_world` | L05, L16 |
| P1.b | Staff reputation under the Prestige label | `done` | `32bc43d` | `test_living_views` | L16 |
| P1.c | Each role's value, never combined | `done with known limitation` | `32bc43d` | `test_living_views` | L16. An implemented choice; no owner decision in the decision log |
| P1.d | Current achievement against lasting legacy | `done with known limitation` | section 2.11 (OG2) | | |
| P1.e | Prestige, skill and experience kept distinct | `done` | `32bc43d` | `test_living_views` | L16 |
| P1.f | Numeric sort both ways; consistent missing values | `done` | section 2.11 (OG1) | | |
| P1.g | Every score dated; archived views never substitute current values | `done with known limitation` | `32bc43d` | `test_living_views` | L16. The role-switch case has no dedicated test |
| P2.a-h | Five-year event, course, nation prestige | see section 2.3 | | | |
| S1.a | Specialty, youth expertise, ratings, prestige, experience, capacity | `done` | `eba01e1`, `32bc43d` | `test_living_views` | L16 |
| S1.b | One shared timeline with initiator, reasons, time, rapport | `done` | `eba01e1`; this season's partnerships: LP1 | `test_living_views`, `test_observer_profiles` | L16; X6 |
| S1.c | Shared achievements only from event records | `done` | `eba01e1` | `test_living_views` | L16 |
| S1.d | My World team news: new partnership, reunion, split | `done` | section 2.1 (N5.a) | | |
| S1.e | My World team news: first shared major, retirement into a staff role | `done` | section 2.11 (OG3) | | |
| S2, S3 | Scouting and two-way recruitment | see section 2.2 | | | |
| G1-G3 | Geography, Aggression, weather | see section 2.4 | | | |
| R9.a | "Record Book" name; routes and bookmarks preserved | `done` | `26df0bf` | `test_myworld` | L06 |
| R9.b | Desktop GOAT and Compare links | `done` | `26df0bf` | `test_myworld` | L06 |
| R9.c | Active/retired on Career Grand Slam and One Major Short | `done` | `tools/observer_history.py` | `test_myworld` | L06 |
| R9.d | Nation counts link to the exact population | `done` | section 2.1 (N5.c) | | |
| B1, B2 | Biggest Upsets | see section 2.5 | | | |
| T1-T3 | Tournament stories | see section 2.6 | | | |
| C1.a | Procedural entrants for principal conclusions, including retired and censored careers | `done with known limitation` | `473690a`, `15374c9` | `test_diagnostic_report` | The A-D report separates seeded and procedural careers and counts still-active (censored) golfers; pinned build only |
| C1.b | Initial attributes, ceilings, coach exposure, prodigies, slow-burn, late wins and entry ages examined separately | see O5 (excluded) | E1 records in run A | -- | CQ3 |
| C1.c | Extreme starting tail and first-year gains before any cap | see O6 (decided) | section 2.16 (CQ1) | | |
| C1.d | Peak duration, decline by part of the game, competitiveness across cohorts | see O5 (excluded) | A-D report (peaks; aging by part of the game) | -- | CQ3; competitiveness across cohorts is not yet reported |
| C1.e | Superstar scheduling | see O5 (excluded) | section 2.16 (CQ3) | | |
| C1.f | Tolerance bands before tuning | see O5 (excluded) | section 2.16 (CQ3) | | Bands not set for this playtest; nothing tuned |
| C2.a-f | Death after retirement | see section 2.7 | | | |
| CAL | v2 for new worlds, v1 history browse-only, nothing deleted | `done` | `dd0bb27` | `test_observer_app`, `test_calendar_v2` | L06 |

## 4. Audit register N01-N23 (88 subrequirements)

"Audit answered" rows were questions the roadmap's audit answered from retained data. They are `done`, and any
follow-up has its own row.

| Id | Requirement | Status | Where / evidence |
|---|---|---|---|
| N01.01 | Explain low-probability retirement | `done` | Chance and inputs shown (`decision_text`); new worlds also keep the draw and every term (E1.f.2) |
| N01.02 | Display retired status | `done` | `test_myworld` (L06) |
| N01.03 | Explain 16 starts and the deciding window | `done` | Audit answered |
| N02.01 | Annual ratings-change bar graph | `done` | `e2e60f4`; `test_living_views` (L16) |
| N02.02 | Fixed readable bar size | `done with known limitation` | 38 px at both widths measured by hand; G3 on `c0d1ea5` passed (overflow 0) |
| N02.03 | Horizontal scrolling, not compression | `done with known limitation` | Checked by hand in the browser; G3 on `c0d1ea5` passed (largest horizontal overflow 0) |
| N03.01 | Caddie Ratings section | `done` | `test_living_views` (L16) |
| N03.02 | Coach Ratings section | `done` | `test_living_views` (L16) |
| N04.01 | Course Prestige column | `done` | `7ac03c4` (section 2.3) |
| N04.02 | Sortable course Prestige | `done` | `7ac03c4`, `1cc69a7` |
| N04.03 | State/Province column | `done` | `e1669ea` (G1.a) |
| N04.04 | Home-state familiarity | `done` | `39c8cf3` (G1.b): the region where they were born or live |
| N04.05 | Current-residence-state familiarity | `done` | `39c8cf3` (G1.b) |
| N04.06 | No independent home advantage beyond familiarity | `done` | Rules 2026-11-08: a floor, never added, counted once; BaselineTests |
| N04.07 | Profile course familiarity | `done` | `172b787`, `23e288c` (G1.c) |
| N04.08 | Top 10 familiar courses | `done` | `172b787` (G1.c) |
| N05.01 | Tournament Prestige column | `done` | `7ac03c4` |
| N05.02 | Sortable event Prestige | `done` | `7ac03c4`, `1cc69a7` |
| N05.03 | Sustained strong fields affect prestige | `done` | EventWindow (P2.a) |
| N05.04 | Better prestige enables better host venues | `done` | Venue moves (P2.d); thresholds kept as the playtest baseline, natural activation unexercised (P2.f) |
| N05.05 | Five-year rolling factor history | `done` | Rules 2026-11-05 (P2.a) |
| N05.06 | No big jumps | `done` | Annual limit (P2.a); constants kept as the playtest baseline (P2.f) |
| N06.01 | Nation Prestige | `done` | P2.c |
| N06.02 | Sortable nation Prestige | `done` | P2.e, `1cc69a7` |
| N06.03 | Success beyond expectation in prestigious events | `done with known limitation` | P2.c; the expectation model is kept as the playtest baseline, without a calibration table (P2.f) |
| N06.04 | Increased future golfer quantity | `done` | D7: a share of a fixed cohort, not more golfers (P2.c) |
| N06.05 | No arbitrary direct quality boosts | `done` | TalentUnchanged (P2.c) |
| N06.06 | Five-year rolling average | `done` | `golfsim/participation.py` (`NATION_YEARS = 5`) |
| N07.01 | Course prestige history chart | `done` | `tools/observer_prestige.py` (P2.e) |
| N07.02 | Tournament prestige history chart | `done` | `tools/observer_prestige.py` (P2.e) |
| N07.03 | Nation prestige history chart | `done` | `tools/observer_prestige.py` (national prestige and share bars) |
| N08.01 | Link nation counts | `done` | N5.c |
| N08.02 | Destination lists match the count's scope | `done` | N5.c |
| N09.01 | Verify the amateur major win and qualification | `done` | Audit answered |
| N09.02 | Research the real Masters, last 50 years | `done` | Audit answered |
| N09.03 | Explain the college player's attributes without suppressing the story | see O5 (excluded) | C1.b |
| N10.01 | Late non-college entry distribution | see O5 (excluded) | E1 creation records exist; no distribution reported yet |
| N10.02 | Entry age and pathway of the audited case | `done` | Audit answered |
| N10.03 | Repeated runner-up case | `done` | Audit answered |
| N10.04 | Age-26 entrants plausible and intentional | see O5 (excluded) | Intentional but uncalibrated |
| N11.01 | Starting attribute distributions | see O5 (excluded) | C1.b |
| N11.02 | Potential influence | see O5 (excluded) | C1.b |
| N11.03 | Coach influence | see O5 (excluded) | C1.b |
| N11.04 | Fast prodigy trajectory | see O6 (decided) | CQ1: kept for this playthrough, provisional; individualized maturation a design consideration for the next |
| N11.05 | Slow-burn later greatness | see O5 (excluded) | C1.b |
| N11.06 | Exclude the initialization cohort | `done with known limitation` | `15374c9` (seeded and procedural apart); the filter itself has no dedicated unit test |
| N11.07 | All procedural entrants, not survivors | `done with known limitation` | Retirement coverage counts every cohort member, including the still active; the peaks table is completed careers only |
| N12.01 | Active/retired on Grand Slam | `done` | `test_myworld` |
| N12.02 | Active/retired on One Major Short | `done` | `test_myworld` |
| N13.01 | Southport Brook Public Golf Course | `done` | D12; `test_familiarity_region.LocalHostingTests` |
| N13.02 | Wren Dunes Golf Club | `done` | D12; LocalHostingTests |
| N13.03 | Fjordby Helsinki Golfklub | `done` | D12; LocalHostingTests |
| N13.04 | 2057 no-host observation | `done` | Audit answered |
| N14.01 | The audited high peak | `done` | Audit answered |
| N14.02 | Why no professional career | `done` | Audit answered; follow-up F1 |
| N15.01 | 441 elite starts without a win | `done` | Audit answered |
| N15.02 | Equivalent real-world record | `done` | Audit answered |
| N15.03 | Explain the 1.4 % retirement | `done` | Audit answered |
| N16.01 | Chart persists after retirement | `done` | `test_living_views` |
| N16.02 | Last chart year is the retirement year | `done` | `test_living_views` |
| N17.01 | Complete development record | `done` | E1.c-E1.e (new worlds) |
| N17.02 | Age-18 starting Overall | `done` | Audit answered; recorded in new worlds |
| N17.03 | Peak plausibility | see O5 (excluded) | A-D peaks table; CQ3 |
| N17.04 | 94 at age 41 | see O5 (excluded) | A-D aging tables; CQ3 |
| N17.05 | Decline still slow at 52 | see O5 (excluded) | A-D aging by part of the game (50-54, 55+); CQ3 |
| N17.06 | Win count plausibility | see O5 (excluded) | CQ3; Vaughan's 128 wins and 30 majors in O6 |
| N17.07 | No huge change from one outlier | `done` | A constraint, respected: no calibration change was made in `473690a..c0d1ea5`; D16 (`0b55a2b`): no tuning in this pass |
| N17.08 | Annual starts fewer than 20 | see O5 (excluded) | CQ3 (scheduling) |
| N17.09 | Scope-correct comparison | `done` | Audit answered |
| N18.01 | Explain the 55.8 % turn-pro decision | `done` | Audit answered; terms and draw now recorded (E1.f.2) |
| N18.02 | Assess about 98 %, not an automatic constant | `done` | Audit answered; not adopted |
| N18.03 | Research top amateurs declining professional careers | `done` | Audit answered |
| N19.01 | Injury frequency believable | see O5 (excluded) | CQ3; injury-rate tuning itself is excluded from this pass (E3.g) |
| N19.02 | Stamina functioning as intended | see O5 (excluded) | CQ3; E1.f.1 fatigue columns on a fresh world |
| N19.03 | Recovery functioning as intended | see O5 (excluded) | CQ3; the `rest_keep` term is now recorded |
| N19.04 | Declining starts and their causes | `done` | Audit answered; weekly reasons recorded (`test_access_ledger`) |
| N20.01 | Age-55 physical attributes | `done` | Audit answered |
| N20.02 | Decline timing | see O5 (excluded) | A-D aging tables; CQ3 |
| N20.03 | Decline rate | see O5 (excluded) | A-D aging tables; CQ3 |
| N21.01 | Locate the GOAT route | `done` | Audit answered |
| N21.02 | Make the entry discoverable | `done` | `26df0bf`; mobile menu deferred by owner |
| N22.01 | Death stage | `done` | C2.a |
| N22.02 | Rising annual mortality after retirement | `done with known limitation` | C2.a (provisional curve) |
| N22.03 | No death while active | `done` | C2.b |
| N22.04 | No implausible living ages | `done` | C2.a-C2.c |
| N22.05 | Explicit playing-versus-staff policy | `done` | D6; C2.b |
| N23.01 | Retirement notification at the first transition only | `done` | `test_myworld` |
| N23.02 | No repeated annual retirement message | `done` | `test_myworld` |

## 5. Merges on rc1 since `473690a`, with rules versions

| Merge | Package | Rules | Ledger evidence | Review recorded |
|---|---|---|---|---|
| `ccddd36` | `build/v16-observer` (`b07b072`) | -- | L06 | HAL at `b07b072` |
| `a195dfe` | `integration/v16-c2` (`c29f6b0`) | 2026-11-07 | L05, L06 | At `c29f6b0`; X3 |
| `17909f4` | `build/v16-observer-gaps` (`d04fa5b`) | -- | L08 | At `d04fa5b` |
| `787eda7` | `build/v16-prestige` (`d187a56`) | 2026-11-05 | L09 (failed), X1 | At `d187a56`; R1 |
| `2e08358` | `build/v16-f2-coverage` (`3e58a7d`) | -- | L14 | At `3e58a7d` |
| `2516d86` | rc1 commit | -- | U1 | R4 |
| `a90ea85` | `build/v16-amateur-return` (`5c15e32`) | 2026-11-06 | L01, L10, U2 | At `5c15e32` |
| `7d8489f` | `build/v16-recruitment` (`b7e835c`) | 2026-11-04 | L07 (failed), X2, U3 | At `b7e835c` |
| `b1158d8` | `build/v16-geography` (`7819114`) | 2026-11-08 | L03, L12, U4 | At `7819114` |
| `1a0cb2f` | `build/v16-weather` (`e19fff3`) | 2026-11-09 | L04, L11, U5 | At `e19fff3`; R6 |
| `e4cc3db` | `build/v16-upsets` (`e027e70`) | -- | L02, L13, U6 | At `e027e70`; R6 |
| `fe04ab5` | `build/v16-stories` (`2306549`) | -- | L15, U7 | At `2306549`; R5, R6 |
| `d2a79ce` | rc1 commit | -- | U8 | -- |
| `f5ac938` | `build/v16-prestige` (`68676fd`) | -- | U9, L16 | R1 |
| `16c83e8` | `build/v16-recruitment` (`c0932d0`) | 2026-11-04 text | U10, L16 | R2 |
| `23701cf` | `build/v16-schedule-evidence` (`9e0b042`) | -- (recording only) | L20-L22 | Doc finding `72ab740` |
| `d70a725` | `build/v16-report` (`8fcf2a5`) | -- | U11, L16-L22 | R3 |
| `72ab740` | rc1 commit (docs) | -- | -- | From review of `d70a725` |
| `f9bd765` | `build/v16-pathway18` (`c848952`) | 2026-11-10 | M `5664853`, M `e759903` | R8 |
| `5664853` | `build/v16-college-access` (`459322c`) | 2026-11-11 | M `5664853`; R7's 5 % world | R7 |
| `9cac183`, `697183c`, `d39d613` | rc1 commits | -- | X6, X9 | `697183c` reviewed (findings fixed in `d39d613`); `d39d613` accepted (R9) |
| `e759903`, `c2a1391` | rc1 commits | -- | X7, X8 | `c2a1391` accepted (R9) |
| `0a05310` | rc1 commit (review docs) | -- | -- | -- |
| `376c7a9` | rc1 commit after `0a05310` (decision-evidence fix, E1.f.8) | -- (recording only) | X10; M `376c7a9` | -- |
| `9df86eb` | rc1 commit (long-run harness: comparison arms for new session worlds; tool only) | -- | M `9df86eb` | Reviewed: three blockers, fixed in `88bf8a6` |
| `0b55a2b` | rc1 commit (docs: `docs/BACKLOG.md` roadmap table; decision log D13-D17) | -- | -- (docs only) | -- |
| `88bf8a6` | rc1 commit (harness: arm checks before anything is written; session only; no arm on an existing world) | -- | M `88bf8a6` | Accepted (R11) |
| `1c28d09` | rc1 commit (Biggest Upsets B2: audited examples as no-estimate fixtures, O9) | -- (observer only) | M `1c28d09` | Fixes from review in `b287199` |
| `b287199` | rc1 commit (upset truthfulness: unranked estimates keep their own reason; unsupported models never ranked) | -- (observer only; statistics store schema 7, FACT_VERSION 4) | M `b287199` | Accepted (R12) |
| `c0d1ea5` | `build/v16-suite-fixes` (`65d00e2`; brings `aa66095`) | -- (tests only) | X11, X12; M `aa66095`, M `65d00e2`, M `c0d1ea5` | Scoped acceptance (R13). The exact final head |

## 6. Pinned-run evidence (A-D, `473690a`) and final-feature-world evidence

### Pinned runs, frozen build `473690a`

These worlds contain none of the overnight packages: recruitment, prestige and nation shares, amateur return,
death, geography, weather, upsets, stories, decision evidence, the pathway from 18 and college open access.

| Run | Seed | Support | Seasons | Ended | Reconciliation | Notes |
|---|---|---|---|---|---|---|
| A | 360013 | on | 45 (2027-2071), segments 2027-2033, 2034-2054, 2055-2071 | Complete | errors 0 every season; staff violations 0 | Guard stop at 2033 (487 s, CPU contention); segment 2 ended by a host-side worker restart, nothing of 2055 committed; resumed on the same clean checkout |
| B | 2027 | on | 10 (2027-2036), segments 2027-2033, 2034-2036 | Complete | errors 0 | Guard stop at 2033 (491 s); season 5 (2031) replay identical in all 15 parts |
| C | 2027 | off | 10 | Complete | errors 0 | Comparison arm for B, same build (D4) |
| D | 3031 | on | 10 | Complete | errors 0 | -- |

What these runs support:
- the report tables in `docs/review/DIAGNOSTIC_RUNS_ABCD.md`: performance on this machine, population, retirement
  coverage, peaks, development by age and source, B against C, and the work pathway's groups;
- the interim B/C/D documents and the under-21/college diagnosis;
- the F1 baseline pressure (B-D; `docs/review/F1_BASELINE_PRESSURE_AND_E1_SCOPE.md`).

What they do not support: any statement about the final feature world.

### Comparison arms, final build `c0d1ea5`

Full-population session worlds of the exact final head, run with the harness's arm settings (`9df86eb`, `88bf8a6`).
Report and scripts: `docs/review/arms_comparison/` (`79b78d6`, then `dc41950` and `0061501`, on
`origin/build/v16-report`, read only; R15).

| Arm | Seed | Seasons | Pathway minimum age | College open access | Ended | Reconciliation |
|---|---|---|---|---|---|---|
| a21old | 4207 | 10 (2027-2036) | 21 | off | Complete | errors 0 |
| a18old | 4207 | 10 (2027-2036) | 18 | off | Complete | errors 0 |
| a18new | 4207 | 10 (2027-2036) | 18 | on (the build's defaults) | Complete | errors 0 |
| seed2 | 5309 | 5 (2027-2031) | 18 | on (the build's defaults) | Complete | errors 0 |

What they support, descriptively: DL1.m (section 1 of the report), DL2.m (section 2), P2.f, S3.g and G3.g on two
seeds (section 3), and the familiarity baseline's applied share (section 3, not the on/off comparison G1.e). Section 4
times story assembly on run A's pinned archive (T3.b). The worlds diverge between arms (from week 45 of 2028 for the
pathway arms, from week 1 of 2027 for the college arms), so no table is an individual counterfactual.

Later additions on the same branch: amateur return and re-block by age band over the four arms (report section 5,
D5.c, `dc41950`); the upset snapshot cost (section 6, B1.h); and a same-seed season with the familiarity baseline on
and off (`G1E_FAMILIARITY.md`, G1.e, `0061501`). The decision evidence's exact-head size is from G2 (E1.f.6), and the
determinism replay is its own run (N4.c, below).

### Final-feature-world evidence (rc1)

- **Pre-final, small worlds and unit tests only:** every package's serialized queue run (L01-L15) and the grouped
  runs on the rc1 commit `d70a725` (L16-L22). L17 failed once; the failure was fixed by `697183c` (X6).
- **Merged after `d70a725`, quick tests only:** the commits `72ab740`, `f9bd765` (pathway 18), `5664853` (college
  access), `9cac183`, `e759903`, `697183c`, `d39d613`, `c2a1391`, `0a05310`, `376c7a9`, `9df86eb`, `88bf8a6`,
  `1c28d09`, `b287199`, `aa66095` and `65d00e2` (merged `c0d1ea5`). Their evidence is in the M and X rows and the
  independent reviews R7-R9 and R11-R13. R7's actual 5 % world exercised college access in weeks 17-18. R8's test
  made a real monthly in-season pathway transition at age 18.
- **On `0a05310` (pre-final gates):** G1 ran 972 tests, FAILED (failures=1, errors=4), all five fixed (X10-X12); the
  smoke passed (outcomes identical with the evidence on and off); navigation passed (140 pages, 0 failing).
- **Full-population, multi-season worlds of the final build:** the four comparison arms on `c0d1ea5` (above).
- **On `c0d1ea5` (final-head gates), all passed:** G1, Ran 998 tests in 7524.9 s, OK (skipped=4: 2
  environment-gated, 2 data-conditional); G2, the smoke (seed 4207, exit 0, 613 s; season file +6.8 %, evidence
  830,379 B, 6.4 %; bounds held); G3, 160 pages at 1920 and 1366 px, 0 failing, overflow 0; G4, no outcome part
  differs with the evidence off. Section 1 has the detail.
- **Determinism of the final build (N4.c):** a fresh full-population session world on `c0d1ea5` (seed 4207, 2
  seasons, 0 reconcile errors, 0 staff violations); season 2028 replayed from the copy saved after 2027 and reopened:
  identical in all 16 recorded parts.

## 7. Open items and what closes them

No item is open. The gate O1 passed on `c0d1ea5`, and O3 and O4 were measured and closed. O2 and O6-O9 are closed,
and O5 is excluded from this pass by decision; all are kept here for the record. Three rows are excluded from this
pass by decision (G3.f, E3.g, CQ3).

| Item | Question | Status | Rows it covers | What closed it |
|---|---|---|---|---|
| O1 | Final-head gates | closed: passed on `c0d1ea5` | G1-G4 on `c0d1ea5`; E1.f.5 (`done`) | G1: Ran 998 tests in 7524.9 s, OK (skipped=4: 2 environment-gated, 2 data-conditional); the run on `0a05310` had failed 1 and errored 4, all fixed (X10-X12). G2: the smoke passed (seed 4207, exit 0, 613 s; bounds held). G3: 160 pages at 1920 and 1366 px, 0 failing, overflow 0. G4: no outcome part differs with the evidence off |
| O2 | Full-population effect of the two 07:24 rule changes | closed: measured, policy retained | DL1.m, DL2.m (both `done with known limitation`) | Measured on the `c0d1ea5` comparison arms (a21old, a18old, a18new: seed 4207, 10 seasons each; seed2: seed 5309, 5 seasons; all complete, 0 reconcile errors; arms report `79b78d6`). The reviewer judged the college-access trade-off consistent with the design: policy retained, the cost to members disclosed. Descriptive, diverged worlds; no individual counterfactual. Review of the report in progress |
| O3 | Full-population and long-history measurements of the final build | closed: measured | N4.c (`done`); E1.f.6, D5.c, B1.h, G3.g, T3.b (`done with known limitation`) | N4.c: the save/reopen replay of season 2028 on `c0d1ea5`, identical in all 16 recorded parts. E1.f.6: G2's figures, a new world's first two seasons (a mature ~13k world not measured; `docs/DECISION_EVIDENCE.md` in `a2d56fb`). D5.c: return and re-block by age band over the four arms (`dc41950`; 0 cash re-blocks and 0 pathway re-entries among 1,009 observed returns; accepted provisionally). B1.h: upset records 3.4 % of the raw season file, offline recomputation about 2.9 s CPU a season, exact; the in-engine overhead not instrumented and not inferred |
| O4 | Package measurements, then the constants they inform | closed: measured; constants kept by decision | G1.e, S3.g, P2.f (`done with known limitation`) | G1.e: the same-seed season on `c0d1ea5` with the baseline on and off (`0061501`): 6,799 of 124,224 starts (5.5 %), 3,899 golfers, none when off; the week-1 comparison exploratory only. P2.f and S3.g: constants kept as the playtest baseline (HAL's decision; D21 in `a2d56fb`), with venue-move activation unexercised (0 moves in 15 seed-seasons; a ±0.01 band at the gap threshold of 5), 8 terminal arrival cells not verified, and recruitment descriptive only |
| O5 | Calibration assessment against tolerance bands | `excluded from this pass by decision` | CQ3; C1.b, C1.d, C1.e, C1.f, F1.i; N09.03, N10.01, N10.04, N11.01-N11.03, N11.05, N17.03-N17.06, N17.08, N19.01-N19.03, N20.02, N20.03 | Tolerance bands not set for this playtest; baseline retained with measured limitations; not a missing feature (HAL's decision (31 October, after the arms report): no target bands are invented and nothing is tuned without evidence). The measured limitations are documented: the F1 baseline (`ac310a8`, `1de4119`), the A-D report and the arms report (`79b78d6`) |
| O6 | The 89-at-18 outlier | closed by decision | CQ1 (`done with known limitation`); C1.c, N11.04 | Diagnosis published (`b613b3b`, corrected `d13ad91`, not on rc1): a rare organic tail the rules produce (created 85.31, potential 97.01). Decided (HAL's decision (31 October, after the arms report), with D16 `0b55a2b`): rare organic potential and the current maturation are kept for this playthrough, explicitly as provisional; retention, not a mechanics change. The calibration is unvalidated |
| O7 | Initialization to steady state: the seeded world starts below the population's equilibrium (a calibration assessment, not a defect) | closed by decision | CQ2 (`done with known limitation`) | Decided (HAL's decision (31 October, after the arms report)): the initialization size is kept as the baseline for this playtest. Measured limitation: the seeded start sits below equilibrium; run A plateaus near 13.1k active for its final ~17 seasons (from 6,656 at the start), and the comparison arms on `c0d1ea5` rise from 6,409 to 10,337-10,343 active (harness count, after the tenth winter) in 10 seasons |
| O8 | E1.f remaining recording gaps | closed by decision | E1.f.7 (`done with known limitation`) | The reviewer's decision (`ac310a8`, `docs/review/F1_BASELINE_PRESSURE_AND_E1_SCOPE.md`): format /2 fulfils E1; the listed gaps are disclosed limitations, not missing features; no format /3 in this pass |
| O9 | Audited upset examples as regression cases | closed: done | B2.a (`done`) | `1c28d09` plus `b287199` (accepted, R12): truthful no-estimate fixtures in `tests/test_upset_examples.py`; no odds invented; unsupported or unusable estimates never ranked |

**Excluded from this pass by decision, not open:**
- weather temperature and firmness effects (G3.f; D17 in the decision log, `0b55a2b`);
- injury body-part damage and injury-rate tuning (E3.g; D17). Assessing injury frequency falls under O5;
- the calibration assessment against tolerance bands (CQ3, O5; HAL's decision): bands not set for this playtest,
  baseline retained with measured limitations.

## 8. Counts by status

What is counted:
- every row in sections 2-4 that has one of the five statuses, once;
- not the 13 section-3 rows that point to a section-2 row and repeat its status (9 `done`, 4
  `done with known limitation`);
- not the 24 rows in sections 3 and 4 that only point to a consolidated item ("see O5 (excluded)" or "see O6
  (decided)"): 6 in section 3 and 18 in section 4;
- not the evidence, merge and open-items tables (sections 1, 5 and 7).

| Status | Section 2 (overnight scope) | Section 3 (expanded roadmap) | Section 4 (N01-N23) | All |
|---|---|---|---|---|
| `done` | 76 | 37 | 64 | 177 |
| `done with known limitation` | 25 | 9 | 6 | 40 |
| `open: design decision pending` | 0 | 0 | 0 | 0 |
| `open: not started` | 0 | 0 | 0 | 0 |
| `excluded from this pass by decision` | 2 | 1 | 0 | 3 |
| **Rows** | **103** | **47** | **70** | **220** |

Changed since the reading at `0a05310` (all in section 2):
- `open: not started` → `done`: B2.a, N4.c;
- `open: not started` → `done with known limitation`: DL1.m, DL2.m, G3.g, T3.b, CQ2, E1.f.6, D5.c, B1.h, G1.e;
- `open: design decision pending` → `done with known limitation`: E1.f.7, CQ1;
- `open: not started` → `done with known limitation` (by way of `open: design decision pending` in `f086562`):
  P2.f, S3.g;
- `done with known limitation` → `done`: E1.f.5 (G4 on the final head);
- `open: design decision pending` → `excluded from this pass by decision`: CQ3.

No row is open. Nothing remains open except what is excluded from this pass by decision (G3.f, E3.g, CQ3 and the O5
rows that point to it). All items are closed: O1 (gates passed), O2 (measured; policy retained), O3 and O4
(measured; P2.f and S3.g constants kept by decision), O6 and O7 (by decision; kept with limitations), O8 (by
decision), O9 (done). O5 is excluded from this pass by decision.

## 9. Documents out of step with rc1 (no change made here)

`0b55a2b` (on rc1) brought `docs/BACKLOG.md`'s roadmap table and the decision log (D13-D17) into step with rc1 as it
was at `0a05310`.

The docs-only commit `a2d56fb` (`build/v16-docs-final`, from `c0d1ea5`; six `docs/*.md` files; engine id 1949ff63
unchanged) brings the rest into step:
- **`docs/BACKLOG.md`**: the P2, S3, G1, G3, B1/B2, T1-T3, C1 and college-access rows now give the measured results
  on `c0d1ea5`, with their limitations and the decisions (D21).
- **`docs/DECISIONS_2026-10-31.md`**: D18 (format /2 fulfils E1; O8), D19 (college open access retained, its cost
  disclosed), D20 (the outlier's organic potential and current maturation kept, provisional; CQ1), D21 (prestige
  and recruitment constants and the seeded size kept as the playtest baseline; tolerance bands not set for this
  playtest; P2.f, S3.g, CQ2, CQ3).
- **`docs/DECISION_EVIDENCE.md`**: the full-world size measured on `c0d1ea5` (E1.f.6), replacing the 11-13 %
  estimate for a new world's first seasons.
- **The package documents** (`docs/WORLD_PRESTIGE_PACKAGE.md`, `docs/RECRUITMENT_PACKAGE.md`,
  `docs/FAMILIARITY_AND_AGGRESSION.md`): an update note with the measured results ahead of their "not run" text, which
  is kept as written.

Still out of step:
- **The docs-only branch `build/v16-docs-final` (`a2d56fb`, then `afb68f3`) is not on rc1.** Until it is merged, the documents on `integration/v16-rc1` (`c0d1ea5`) read as
  described above for `c0d1ea5`: `docs/BACKLOG.md` with T1-T3 timing "pending the CPU hold", the college-access
  paired runs "pending" and the P2, S3, G1, G3 and C1 measurements open; the decision log without D18-D21; and
  `docs/DECISION_EVIDENCE.md` with the estimate only.
- **`docs/AMATEUR_WORK_PATHWAY_PROPOSAL.md`**: brought into step by the second docs-only commit `afb68f3` (the D5.c
  full-population return and re-block results, `dc41950`); on rc1 it still gives only the 5 % world.
- **`docs/BACKLOG.md`** (also at `a2d56fb`) points to this matrix on `build/v16-traceability`, which is not on rc1.
- **The review documents and the ledger are on `origin/build/v16-report` only** (latest `6b6d2f0`, with the release evidence in `docs/review/release_evidence/`), not on rc1:
  - the remedy options, `docs/review/U21_AND_COLLEGE_REMEDY_OPTIONS.md` (`9f2ac00`, `9baea7a`; RD3);
  - the Vaughan diagnosis, `docs/review/VAUGHAN_OUTLIER_DIAGNOSIS.md` (`b613b3b`, `d13ad91`; CQ1);
  - the F1 baseline and E1 scope, `docs/review/F1_BASELINE_PRESSURE_AND_E1_SCOPE.md` (`ac310a8`, `1de4119`; F1.i,
    E1.f.7);
  - the arms comparison, `docs/review/arms_comparison/` (`ee3fada`, `79b78d6`, `dc41950`, `0061501`; DL1.m, DL2.m,
    P2.f, S3.g, G3.g, T3.b, D5.c, B1.h, G1.e);
  - the release evidence ledger, to be published under `docs/review/release_evidence/`.
