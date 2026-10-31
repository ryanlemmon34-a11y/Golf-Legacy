# v16 release evidence ledger

The candidate is `integration/v16-rc1` at `c0d1ea5` (c0d1ea598bc784611e7e26cc414f754671965530). Sections 1-4 record the package and merge history up to that head, in order, as it was run. Section 5 is the earlier **pinned 473690a baseline** (runs A-D), not the candidate. Sections 7-8 are the **current candidate's** evidence.

All serialized test commands run from a clean detached worktree of the named commit as
`timeout 3600 nice -n 19 python -m unittest <modules>`, one job at a time beside the pinned diagnostic runs.
"Commit tested" is the worktree's HEAD (some queue lines printed an older label; the worktree HEAD is authoritative).

## 1. Serialized queue: package and merged-commit tests

| Time (UTC) | Item | Commit tested | Modules | Result |
|---|---|---|---|---|
| 05:05 | return | 0c5cdd7 | test_amateur_return test_work_pathway test_amateur_support test_amateur_residence | Ran 39 OK |
| 05:07 | upsets (GOLF_HEAVY_TESTS=1) | 3291666 | test_upsets test_golf_stats | Ran 35 OK |
| 05:10 | geography | 63ad358 | test_familiarity_region test_aggression_visible test_residence test_engine | Ran 73 OK |
| 05:12 | weather | 1cbf7a4 | test_weather test_engine test_playoffs test_golf_stats | Ran 64 OK |
| 05:21 | death (label fa787d4) | c29f6b0 (build/v16 + death, merged) | test_mortality test_mortality_world test_cohort test_staff | Ran 51 OK |
| 05:35 | C2 merged observer | c29f6b0 | test_living_views test_observer_history test_history_consistency test_myworld test_myworld_events test_nation_links test_ratings_groups test_views test_observer_app test_amateur_residence | Ran 103 OK |
| 05:55 | recruitment (label a1b3aad) | **b7e835c** | test_recruitment test_staff test_living_views test_history test_history_consistency test_finance_integration test_observer_history test_myworld_events test_observer_profiles test_observer_app | **Ran 140 FAILED (failures=1, skipped=1)** -- see 3.2 |
| 06:05 | observer gaps (label 5f87e42) | d04fa5b | test_observer_gaps test_living_views test_observer_history test_myworld test_myworld_events test_observer_profiles test_complete_history test_views | Ran 105 OK (skipped=2) |
| 06:13 | prestige | d187a56 | test_venue_moves test_nation_shares test_world_prestige test_season test_population test_development test_amateur_residence test_history_consistency test_observer_history test_living_views | **Ran 111 FAILED (errors=1)** -- see 3.1 |
| 06:16 | return (funding fix) | 5c15e32 | test_amateur_return test_work_pathway test_amateur_support test_season | Ran 50 OK |
| ~06:15-06:30 | (worker restart) | -- | queue5 (weather2 onwards), queue6, queue7 killed mid-run | re-run in queue8 |
| 06:39 | weather (gusts) | e19fff3 | test_weather test_engine test_playoffs test_golf_stats test_observer_history test_amateur_residence test_season | Ran 113 OK |
| 06:57 | geography (home-club fix) | 7819114 | test_familiarity_region test_aggression_visible test_course_library test_residence test_session test_publication test_engine test_living_views test_observer_history | Ran 167 OK |
| 07:01 | upsets (snapshot) | e027e70 | test_upsets test_observer_history test_living_views | Ran 57 OK (skipped=1) |
| 07:01 | F2 | 3e58a7d | test_major_affordability_269 test_major_funding | Ran 20 OK |
| 07:05 | stories | 2306549 | test_stories test_myworld test_observer_history test_observer_app test_views | Ran 102 OK |
| 07:20 | rc1 fixes group | d70a725 | test_living_views test_population test_nation_shares test_world_prestige test_finance_integration test_recruitment test_staff test_history_consistency | Ran 113 OK (incl. the formerly failing living_views and finance PromotionTests) |
| 07:34 | rc1 observer group | d70a725 | test_observer_gaps test_observer_history test_observer_app test_observer_profiles test_observer_sync test_myworld test_myworld_events test_stories test_upsets test_upsets_stories_merge | **Ran 173 FAILED (failures=1, skipped=3)** -- see 3.6 |
| 07:38 | rc1 engine group | d70a725 | test_weather test_weather_geography_merge test_engine test_realism test_playoffs test_performance_equivalence test_course_library test_venue_moves test_familiarity_region test_aggression_visible | Ran 184 OK |
| 08:00 | rc1 season group | d70a725 (pre-fix) | test_season test_session test_history test_mortality test_mortality_world test_work_pathway test_amateur_return test_major_affordability_269 | Ran 116 OK |
| 08:01 | decision evidence world | d70a725 (pre-fix) | test_decision_evidence_world | Ran 5 OK (skipped=1: the parent-build check runs as its own item) |
| 08:02 | decision evidence vs parent build | d70a725 vs 16c83e8 (pre-fix) | test_decision_evidence_world...test_outcomes_are_identical_to_the_parent_build (GOLF_PARENT_CHECKOUT) | Ran 1 OK |
| 08:04 | evidence callers | d70a725 (pre-fix) | test_realism test_development test_decision_evidence test_diagnostic_report | Ran 87 OK |
| 10:12 | full suite (pre-final) | 0a05310 | python -m unittest discover -s tests | **Ran 972 in 7578.7 s: FAILED (failures=1, errors=4, skipped=4)** -- test_amateur_residence x3 (fixed 376c7a9), test_compare (fixed aa66095), test_goat_peaks (fixed 65d00e2); see 3.10 |
| 10:23 | full-population smoke (pre-final) | 0a05310 | full_pop_smoke.py seed 4207, 2 seasons on + 1 off | exit 0: outcomes identical evidence on/off (every part); season 1 200.5 s on / 188.4 s off; season file 13.04 / 12.21 MB; evidence 830 KB (6.8%), 901 KB in season 2 (7.2%); checkpoint 38.1 / 36.4 MB; bounds held (max 13 plans, 0 over, max 3 career rows) |
| (after arms) | **FINAL: full suite** | **c0d1ea5** | python -m unittest discover -s tests | pending |
| (after) | **FINAL: full-population smoke** | **c0d1ea5** | full_pop_smoke.py seed 4207, 2 seasons on + 1 off | pending |
| (after) | wide-screen navigation (pre-final) | 0a05310 | nav_check.js | pending |
| (after) | **FINAL: wide-screen navigation** | **c0d1ea5** | nav_check.js at 1920 and 1366 px on a copy of the smoke world | pending |

## 2. Quick unit tests run while merging and fixing (nice -n 19 timeout 600)

- rc1 winter fix 2516d86: UnitWinterBoundary UnitTeamNews UnitWinterDeathAndDeparture -- 14 OK (10 + 4 new).
- Merge a90ea85 (return): test_amateur_return.Conditions/WorkStart, test_amateur_residence.RulesTests, test_mortality.Curve, test_work_pathway.Counting/Deciding -- 25 OK.
- Merge 7d8489f (recruitment): test_recruitment.ObserverRefusalTests, test_mortality.Curve/WhoCanDie/WorkingStaff/Observer, test_amateur_residence.RulesTests -- 16 OK.
- Merge b1158d8 (geography): test_familiarity_region (11 classes), test_aggression_visible (3), test_mortality.Curve/Archive, test_amateur_residence.RulesTests -- 58 OK.
- Merge 1a0cb2f (weather): test_weather_geography_merge -- 6 OK; test_weather + aggression/observer_gaps.UnitRoundConditions/familiarity/mortality/residence -- 64 OK.
- Merge e4cc3db (upsets): test_upsets.ModelTests/NoHindsightTests/PageTests, test_weather.RecordTests/ControlTests -- 32 OK.
- Merge fe04ab5 (stories): test_upsets_stories_merge -- 2 OK; test_stories (9 unit classes) -- 44 OK; observer_gaps units + upsets + merge + recruitment refusals + mortality observer -- 49 OK.
- d2a79ce (conditions wording): UnitRoundConditions, test_weather_geography_merge, test_upsets_stories_merge -- 12 OK.
- f5ac938 (prestige fix merged): test_nation_shares.DrawCap/TotalsAndAllocation/TalentUnchanged -- 13 OK.
- 16c83e8 (recruitment fix merged): test_recruitment.WinterOrderTests/AssessmentTests/InitiativeTests/ObserverRefusalTests, test_mortality.WorkingStaff/Curve, test_amateur_residence.RulesTests -- 21 OK.
- Report branch: 6aa5f9c 6 OK; 5073485 10 OK; 5ad7a50 10 OK (tests.test_diagnostic_report).
- Stories 2306549 (package agent): 9 unit classes -- 44 OK.

## 3. Failed, then fixed

### 3.1 Prestige / nation shares: season crash in new professionals
- Found: queue, d187a56, tests.test_living_views.RatingsOverTime.setUpClass:
  `RuntimeError: Czechia: 1 new_pros not reached in 1590 draws` (population.entrant_rows).
- Reproduce at d187a56: `python3 -c "from golfsim import population as P; from golfsim.nations import nations; P.entrant_rows('new_pros', 2029, 99, nations())"`.
- Cause: a draw cap assuming a 1-in-40 rarest pass rate; measured 1 in 316 (Czechia) to 1 in 658 (Turkey). Seed 99, 2029, Czechia: first passer at draw 2161.
- Fix 68676fd (build/v16-prestige): no cap; each nation's own stream continues until exactly its quota passes (negative-binomial termination); worlds that never reached the old cap are identical.
- Tests: tests.test_nation_shares.DrawCap (5; 3 fail on d187a56) + TotalsAndAllocation/TalentUnchanged/Baseline/SmoothingAndBounds: 19 OK; InTheWorld 1 OK.
- Merged into rc1: f5ac938. World re-test: queue9.

### 3.2 Recruitment: "paying their own way" below next season's costs
- Found: queue, b7e835c, tests.test_finance_integration.PromotionTests.test_a_new_card_does_not_prove_financial_independence:
  sponsor 141,099.05 < costs 142,631.16 (golfer 557).
- Reproduce: seed 11, scale 0.2, season 2027: `nice -n 19 timeout 600 python3 -m unittest tests.test_finance_integration.PromotionTests`.
- Cause (traced): caddie reputations (and fees, 800 + 25 x reputation) were updated after careers.decide in the same winter; caddie 2309 30 -> 34.4, $1,550 -> $1,660/week, +$2,052 over 18.652 events against a $520 margin. Not a staff offer (those run next January).
- Fix c0932d0 (build/v16-recruitment): staff.caddie_reputations runs before careers.decide (idempotent per year); all three own-way routes record the cash/income/costs used. Assertion unchanged. Changes winter ordering in every world.
- Tests: tests.test_recruitment.WinterOrderTests (2; fail before), recruitment unit classes 13 OK, PromotionTests 3 OK.
- Merged into rc1: 16c83e8 (season.py: close_prestige then caddie_reputations; rules 11-04 text). World re-test: queue9.

### 3.3 My World winter watermark (merged C2)
- Found by review at c29f6b0: death-ended departure clamped to week 52 and hidden after since=(Y,52).
- Fix 2516d86 (rc1): "now" between seasons is (Y,53); no clamping; ranking reads week 52 in winter.
- Tests: UnitWinterDeathAndDeparture (4 new) + updated expectations: 14 OK; independently 32 OK.

### 3.4 Diagnostic report provenance and denominators
- 6aa5f9c labelled resumed runs by inference; 5073485 neutral recorded-state wording, tests for final-season guard and ongoing resumed segment; 5ad7a50 golfer-season denominators, pathway conversions (B 224, C 247), B-vs-C caveat; provenance corrected (A segment 2 = 2034-2054, 21 seasons).

### 3.6 Coach page: this season's partnerships not shown or explained until archived
- Found: queue, d70a725, tests.test_observer_profiles.ProfilesAndStatsTests.test_coach_clients_are_current_assignments:
  "'All partnerships' not found" -- the busiest coach's seven current clients all began this season; the page read
  only archived stints, so accepted partnerships showed no dates, initiator or reasons until the season was archived
  (refusals already merged the snapshot).
- First change 9cac183 (note + conditional assertion) was judged insufficient by review (S3 visibility gap).
- Fix 697183c: live_stints/merge_stints -- the snapshot's stints merged with the archive's by stint id (live end-state
  overrides), on staff pages and golfer team history; "this season" marked; read from the captured snapshot only.
- Tests: tests.test_observer_profiles.LivePartnerships (3, fixture of the reviewed seven-clients case; live override;
  golfer profile) OK; the world test OK (42 s); related observer unit classes 18 OK.

### 3.7 Consistency fixes with the approved policy changes
- e759903: the diagnostic report groups the pathway table by the age in force recorded per run (pinned runs stay 21);
  the work-pathway rule text names both ways back (turn professional; earned amateur return from 2026-11-06).
  tests.test_diagnostic_report.PathwayAgeInForce 2 OK.

### 3.8 Report tool out of memory on the 45-season run
- Found: generating the A-D report after run A completed: killed by the memory limit (12.6 GB resident) -- Run.season
  cached every decoded season file whole.
- Fix c2a1391: only the development diagnostics are kept, each file read and released in turn; the report completes.
  tests.test_diagnostic_report.SeasonFilesTrimmed; module 13 OK.

### 3.9 Smaller review fixes on the final head
- d39d613: run_world (default mode) records the pathway age in force like --session (WorldRulesRecorded, 3); golfer
  team-history footer with nothing archived no longer says "end of None".

### 3.10 Found by the full suite on 0a05310 (2 h 6 min, 972 tests)
- test_amateur_residence (3 errors, KeyError: None): stood-in career models left the decision-evidence model unnamed ->
  376c7a9 (record only a named model); regression WinterDecisions.test_models_stood_in_for_record_nothing_and_change_nothing.
- test_compare (error): the fixture's champion was also No. 1 (one column) -> aa66095; test-only.
- test_goat_peaks (failure): no retirements after the first archived season in the seed world now -> 65d00e2; test-only.
- Merged: c0d1ea5 (independently accepted: Compare + GOAT peaks 10/10 in 347 s). Golf-stats attribution withdrawn
  (mis-mapped progress mark; op-cache semantics verified unchanged).

### 3.5 Earlier review findings fixed on the package branches (found by review unless stated)

| Package | Defect found | Fix commit | Regression / tests at the fix |
|---|---|---|---|
| Stories | Story facts still waiting for the story index were cached (memory and disk) and never rechecked | 696a72a | same-cache pending -> complete test; 9 unit classes 44 OK; independently 47 OK |
| Stories | Putting personal bests compared against an unqualified sample (a 3-round +30 week could count) | 696a72a; NARRATIVE_VERSION 3 in 2306549 so v2-cached stories are rebuilt | reviewer's 3-round +30 / 4-round +1.00/+0.50/+0.80/+7.10 fixture and the "both" variant; v2 -> v3 invalidation (independent) |
| Stories | Earlier review defects (golf-statistics wording, same-format bests, margin split) | 92405d9 | non-simulation story classes |
| Stories | Tolerant multi-key reading of the upset record could claim an upset from the wrong data | aafe369 (exact upset-model-1 reader; honest omissions) | story unit classes |
| Stories | A story failure on the result page swallowed ArchiveChanged (no redraw after a rollback) | 4f9a294 | 31 non-simulation story tests |
| Geography | Profiles showed rounds-based familiarity, not the engine's (a local golfer with 1 round: 6.4% shown, 18.1% used) | 23e288c | familiarity tests |
| Geography | Home-club familiarity inferred from the top-ten list (club outside it shown as 0 rounds / 18.1% where the engine used 48.66%) | 7819114 (recorded explicitly: home_clubs.familiarity_at_club, archived) | test_familiarity_region 38 OK incl. c0-c9 + home club c10 fixture -> 48.7%; queue 7819114 (pending) |
| Prestige | A second venue move overwrote the first (seasons between the moves fell back to the planned course) | d187a56 (effective-dated history per series and planned course; migration from ace3b2e saves) | VenueMoves 7 OK (A->B 2029/2031 then B->C 2039/2041, lag, pickled history, no double-booking) |
| Upsets | Tied chances numbered 1, 2 although the page says equal chances rank equal | a36af60 (competition ranking 1, 2, 2, 4; "tied") | tests.test_upsets 22 OK + tied-chance test |
| Upsets | Stored chances not reproducible (no input snapshot) | e027e70 (entrant ids + Overall persisted; upsets.reproduce) | every stored chance recomputed identically for fields 156/80/30/6; size bounds; 24 OK |
| Weather | Gusts missing from G3 (one steady wind per round) | e19fff3 (per-round gustiness, per-shot strength, own stream, archived; mean damage preserved) | queue e19fff3: 113 OK |
| Amateur return | Funding test counted only trips, not committed coach/caddie costs | 5c15e32 | regression: 23-year-old, $8,000, 8 trips $4,000, $12,500 coach -> no return (was 11.75%); 11 unit + queue 50 OK |
| Recruitment | Refusals not shown for a golfer with no archived stint; staff needed an archived person; live refusals missing | a1b3aad | ObserverRefusalTests |
| Recruitment | Initiation one-sided (only golfers/scouting): established coaches and idle caddies never made offers | b7e835c | InitiativeTests 5 OK (then 3.2 found in the queue) |
| Observer gaps | Winter retirements dated next season's week 1, outside the read cutoff | 571fa72 | boundary fixture |
| Observer gaps | Tour/status changes dated next week 1, outside the read cutoff | d04fa5b | UnitWinterBoundary; queue d04fa5b 105 OK (then 3.3 refined to week 53 in rc1) |
| F2 | Coverage of the 269 recorded major-affordability declines only by sample | d51ad9a (all 269 through the real entry path), 3e58a7d (repeat admission/booking on the same state) | table-driven 269 rows; 10 repeat rows; accepted narrowly (not a post-settlement retry proof) |
| Diagnostic report | "Overall at 19" took the first season at 19 or over | 43bf2c4 | late-entrant fixture |
| Long-run harness | A resume could relabel the amateur-support setting | 43bf2c4 (refused on mismatch) | ResumedSupportSetting |
| Diagnostic report | Development aggregates mixed seeded initial golfers with procedural ones; F1.h breakdowns missing | 15374c9 | diagnostic report tests |

## 4. Independent reviews reported (reviewer)
- Prestige 68676fd: 8 focused tests incl. exact Czechia/99/2029, 27 rare quota/stream scenarios, both pathways, conditional-distribution/prefix equality; population and dependencies match merged 16c83e8.
- Recruitment c0932d0 on 16c83e8: original PromotionTests + WinterOrderTests 5/5, incl. the previously failing seed 11 scale 0.2 season.
- Report 5ad7a50: accepted after 10 independent tests (labels, conversion totals, provenance).
- 2516d86 winter boundary: 32 tests pass (scoped acceptance; rerun on final head).
- Stories 2306549: accepted, 47 story tests + cache/version/qualifier checks.
- fe04ab5 integration: 116 weather/geography/engine/familiarity/playoff tests, 216 classic-round exact comparisons, conditions/replay/match-play/gust display; 49 story/merge + 24 upset tests; simulated-edition story/data/save-reopen. No new in-scope blockers.
- Report 5073485 arithmetic passes.

## 5. Diagnostic runs: the EARLIER BASELINE, pinned build 473690a (not the candidate)
- B, C, D complete (10 seasons each), reconcile errors 0; B season-5 replay identical in all 15 parts.
- A: complete, 45/45 (segments 2027-2033, 2034-2054, 2055-2071; reconcile errors 0 every season); report: docs/review/DIAGNOSTIC_RUNS_ABCD.md (0a05310).

## 6. Final-head checks (planned before the arms; all done, see section 8)
- Full suite, a fresh full-population smoke, wide-screen navigation and the E1.f equivalence: all run on c0d1ea5 (section 8).

## 7. Comparison arms and review notes (after 11:48)
- Arms on c0d1ea5 complete: a21old, a18old, a18new (seed 4207, 10/10) and seed2 (5309, 5/5); exit 0, reconcile errors 0 every season. Report and scripts first published at ee3fada (build/v16-report); corrected through dc41950 (review closed) and G1.e 0061501.
- HAL accepted: F1 precision 1de4119; E1 scope; story timing as indexed-assembly evidence only.
- Final report MUST keep these performance caveats:
  - Story timing calls `observer_stories.tell`, and it is application-cache cold, not filesystem cold.
  - It covers 20 majors on the legacy 473690a 45-season archive with the candidate assembler.
  - Figures: cold median 7.44 s, max 11.85 s; indexed 0.103 s; latest-first 3.08 s partial, then 102 s in the background; read-only index build 218 s, 1.05 GB.
  - RSS 2.65 GB is the lifetime high-water mark, not per story and not evidence against a leak. A time shown as 0.000 s is below precision.
  - Do NOT claim instant cold UI, full UI rendering, Ryan's hardware, or a verified local 120 s target.
- Analysis fixes, all done and published (review branch up to 0061501):
  - section 1 cohort renamed, plus a pretreatment 2027 cohort and the 2028 arrivals;
  - creation check for the college cohort;
  - capacity trade-off paragraph (NA members 81.8→72.1 starts per head, 74.6→136.6 shut-out weeks, cumulative; NA working amateurs 9.40→7.76);
  - prestige allocation and arrival checks (35 allocation cells per pathway, 62 arrival cells, 4 terminal cohorts);
  - venue moves 0 in 15 seed-seasons (rule unexercised) plus the funnel;
  - time-to-job relabelled as plan-based, last n compatible;
  - starts after the job.

## 8. FINAL exact-head gates on c0d1ea5 (c0d1ea598bc784611e7e26cc414f754671965530, clean checkout)
- G1 full suite: `python -m unittest discover -s tests` (nice 19), 11:48:11 -> 13:55:14 UTC: **Ran 998 tests in 7524.9 s, OK (skipped=4)**, exit 0, 0 ERROR/FAIL lines. Log: queue/final2_suite.log.
- G2 full-population smoke: `python3 smoke/full_pop_smoke.py <wt_final2 @ c0d1ea5> smoke/final_c0d1ea5 4207 2`, 13:55:14 -> 14:05:27 UTC, exit 0 (613 s).
  - World created with 6,409 golfers. Everyone in the world, retired included: 7,120 after season 1 and 7,802 after season 2 (active and scheduled: 6,409 in 2027, 6,878 in 2028).
  - Evidence on, 2027: season 201.5 s; season file 13,039,656 B; evidence 830,379 B gzip (3,981,616 B JSON). That is 6.4 % of the file, and the file is +6.8 % over the evidence-off file (12,208,596 B). Checkpoint 38,109,556 B (off: 36,363,871 B).
  - Evidence on, 2028: season 197.2 s; file 12,567,224 B; evidence 901,302 B gzip (7.2 %); checkpoint 55,410,492 B.
  - Bounds held in both seasons: max 13 plans, 0 over, max 3 career rows. 6,409 then 6,878 golfers scheduled; 7 then 5 deaths recorded.
  - Evidence off, 2027: 177.6 s.
- G4 equivalence (from G2): outcome parts differing with the evidence off: **none**.
- Timing caveat: the on/off difference in season time (201.5 vs 177.6 s) is from a single pair of total runtimes. It is not an isolated measurement of the evidence's overhead.
- The sizes are byte-identical to the pre-final 0a05310 smoke (same engine outcome).
- 14:06 Disk: removed armsan/cache (522 MB). It is the analysis's extraction cache, regenerable read-only from the arm archives, which are kept. This keeps the familiarity season above the 3.4 GB stop line. Navigation copy of the smoke world removed by queue14 (source kept).
- G3 wide-screen navigation: `BASE=http://localhost:8793 OUT=ui/final_c0d1ea5 LIMIT=70 node ui/nav_check.js`. It was run against `python3 tools/observer.py <copy of smoke world_on>` from the c0d1ea5 checkout. Exit 0. **160 pages at 1920 and 1366 px (80 each), 0 failing, max horizontal overflow 0.** It visited 8 Story views and 12 coaching tabs; a missing kind would fail the check. Results and 1920 px screenshots are in ui/final_c0d1ea5/.
- N4.c full-population save/reopen determinism on c0d1ea5 (arms/build_c0d1ea5, clean):
  - Run: `python tools/long_world.py --session --seeds 4207 --years 2 --workers 2 --pathway-min-age 18 --college-open-access on --keep-after 1 --out det/det4207`, exit 0, 455 s.
    - 2027: 6,878 active, reconcile errors 0+0, staff violations 0, population ok.
    - 2028: 7,300 active, reconcile errors 0+0, staff violations 0, population ok.
  - Replay: `python tools/determinism_replay.py --out det/det4207 --seed 4207 --workers 2`, exit 0, 238 s. It replays season 2028 from the copy saved after 2027 and reopened from disk.
  - Result: **identical: true** in all 16 recorded parts (results, performance, rounds_and_holes, development, familiarity, finances, staff, fatigue_injuries, rankings, records, moments, history, cursor, diagnostics, decision_evidence, published). Report: det/det4207/determinism_4207.json.
- G1.e familiarity-off season on c0d1ea5:
  - Command: `python3 fam/fam_off.py <arms/build_c0d1ea5> fam/out_c0d1ea5 4207 smoke/final_c0d1ea5/smoke.json`, exit 0, 221 s.
  - Setup: a fresh full-population world, seed 4207, evidence off, `Season.familiar_base_on = False`, one season (2027).
  - Compared with the G2 smoke's evidence-off season (baseline ON, the default).
  - Every outcome part differs, as expected, because the switch changes scoring.
  - Season time 203.0 s (off) against 177.6 s (on): one pair of total runtimes, not an overhead measurement.
  - Analysis of starts affected and scoring: read-only, in progress.
- Skip reasons (identification run, not a gate):
  - Command: `python -m unittest -v <the 12 tests that can skip>` on wt_final2 @ c0d1ea5, exit 0, 861.7 s. Log: queue/skip_reasons.log.
  - Result: 12 ran, OK (skipped=4), the same count as the full suite's 4 (the suite's small test worlds are seeded, so the same cases skip).
  - The 4 skips are:
    1. `test_decision_evidence_world.DecisionEvidenceWorld.test_outcomes_are_identical_to_the_parent_build`: 'set GOLF_PARENT_CHECKOUT to the parent build'. Environment-gated; the same on/off outcome equivalence is covered on the full population by G2/G4.
    2. `test_upsets.HeavyEquivalenceTests.test_recording_changes_no_outcome`: 'whole-season run: set GOLF_HEAVY_TESTS=1'. Environment-gated.
    3. `test_observer_gaps.WorldGaps.test_retirement_into_a_staff_role_each_once`: 'no golfer became a coach or caddie in this small world'. Data-conditional.
    4. `test_observer_profiles.ProfilesAndStatsTests.test_a_golfer_who_became_staff_keeps_one_identity`: 'no golfer became staff in this short world (checked on the 50-season copy)'. Data-conditional.
  - The other 8 conditional tests ran and passed.
