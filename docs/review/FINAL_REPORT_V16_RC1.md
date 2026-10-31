# v16 release candidate: final report (31 October 2026)

> **Status: HELD for review.** Nothing is merged to main.
> - **Candidate:** `integration/v16-rc1` at **`c0d1ea5`** (`c0d1ea598bc784611e7e26cc414f754671965530`).
> - **Docs-only follow-up for review:** branch `build/v16-docs-final`, two commits on top of `c0d1ea5`: `a2d56fb`, then `afb68f3`.
>   - It changes seven `docs/*.md` files and nothing else.
>   - The engine id is unchanged (`1949ff63…`), so the code and test evidence below stays tied to `c0d1ea5`.
> - Main is released only after the reviewer has checked the exact commit (D8). There is no self-approval and no force push.

Evidence, all on `origin/build/v16-report` unless stated:

| What | Where |
|---|---|
| Final gates, exact commands, exit codes, skip reasons, counts, raw logs | `docs/review/release_evidence/` (README, ledger, `raw/`, `scripts/`) |
| Comparison runs on the candidate: scripts and report (review closed at `dc41950`) | `docs/review/arms_comparison/` (`ARMS_COMPARISON.md`, `G1E_FAMILIARITY.md`) |
| Earlier baseline runs A-D (pinned `473690a`) | `docs/review/DIAGNOSTIC_RUNS_ABCD.md` and provenance (on rc1 at `0a05310`) |
| Review documents | `U21_AND_COLLEGE_REMEDY_OPTIONS.md`, `VAUGHAN_OUTLIER_DIAGNOSIS.md`, `F1_BASELINE_PRESSURE_AND_E1_SCOPE.md` |
| Roadmap traceability, every requirement against `c0d1ea5` | `docs/ROADMAP_TRACEABILITY.md` on `origin/build/v16-traceability` (`1a92d3d`) |

## 1. What the candidate contains

These are the packages merged into rc1 for the pre-career-mode expanded roadmap, in merge order. Rules versions are those in `golfsim/rules.py`. `RULES_VERSION` is `2026-11-11`.

| Package | Merge on rc1 | Rules |
|---|---|---|
| Qualification windows: the N most recent editions (D1) | `32a0a6f` | 2026-11-03 |
| Work pathway for cash-blocked adult amateurs (D2), with the support switch for the comparison arm | `3d3090e` | 2026-11-03 |
| Long-run harness: support-off arm, safeguards, determinism replay, diagnostic report | `473690a` (the pinned baseline build) | -- |
| Observer: My World injury, return and partnership items; rating groups; nation-count links | `ccddd36` | -- |
| C2 death after retirement (D6) | `a195dfe` | 2026-11-07 |
| Observer gaps: two-way directory sorts, Prestige parts, team news, round conditions | `17909f4` | -- |
| P2 five-year event, course and nation prestige; nation shares of a fixed cohort; venue moves (D7) | `787eda7`, `f5ac938` | 2026-11-05 |
| F2: all 269 recorded major-affordability declines covered through the real entry path (D11) | `2e08358` | -- |
| My World winter boundary (week 53) | `2516d86` | -- |
| Return from work to full-time amateur golf (D5, D5a) | `a90ea85` | 2026-11-06 |
| S2/S3 scouting and two-way recruitment | `7d8489f`, `16c83e8` | 2026-11-04 |
| G1/G2 regional familiarity, home clubs, local hosting (D12), visible Aggression | `b1158d8` | 2026-11-08 |
| G3 seasonal weather: wind direction, wet rounds, gusts | `1a0cb2f`, `d2a79ce` | 2026-11-09 |
| B1/B2 Biggest Upsets, with each estimate's input snapshot | `e4cc3db`; B2 fixtures `1c28d09`, `b287199` | -- |
| T1-T3 tournament stories | `fe04ab5` | -- |
| E1.f decision evidence, format /2 | `23701cf`; fix `376c7a9` | -- |
| Work pathway from age 18 (D13) | `f9bd765` | 2026-11-10 |
| College home-region open amateur access (D14) | `5664853` | 2026-11-11 |
| Coach and caddie pages, this season's partnerships, report fixes | `9cac183`, `697183c`, `d39d613`, `c2a1391`, `e759903` | -- |
| Long-run comparison arms with checks before writing | `9df86eb`, `88bf8a6` | -- |
| Suite fixture fixes found by the first final suite | `c0d1ea5` (`aa66095`, `65d00e2`) | -- |

Held to these constraints:
- No career mode, no mobile layout, and Hide Results stays removed.
- New worlds are fresh v2 worlds only; older saves are identified as unsupported and never continued.
- Weather temperature and firmness, and injury body-part and rate tuning, are out of scope (D17).

## 2. Tests and gates on the exact candidate

Every gate ran on a clean checkout of `c0d1ea5`, one at a time. Details and raw outputs are in `docs/review/release_evidence/`.

| Gate | Result |
|---|---|
| Full suite (`python -m unittest discover -s tests`) | **998 tests, OK (skipped=4)**, 7,525 s, exit 0 |
| Skipped tests | 2 environment-gated (the parent-build equivalence, which G4 covers on the full population, and a heavy whole-season upset check); 2 data-conditional (no golfer became staff in the small test world) |
| Full-population smoke, seed 4207, 2 seasons with the decision evidence on and 1 off | Exit 0; **outcomes identical with the evidence on and off**; bounds held |
| Wide-screen navigation, 1920 and 1366 px | **160 pages, 0 failing, no horizontal overflow**; Story views and coaching tabs visited |
| Save and reopen determinism, full population | Season 2028 replayed from the copy saved after 2027 and reopened: **identical in all 16 recorded parts** |

The first final suite, run on `0a05310`, found 5 defects: 3 errors in `test_amateur_residence` and 2 fixtures that depended on seed outcomes. All 5 were fixed (`376c7a9`, `aa66095`, `65d00e2`) and reviewed before the run on `c0d1ea5`. The full list of failures found and then fixed during the pass is in the ledger, section 3.

## 3. Diagnostics: two kinds, kept apart

**Earlier baseline (pinned `473690a`; not the candidate's engine).**
- Runs: A (seed 360013, 45 seasons), B and C (seed 2027, support on and off) and D (seed 3031), 10 seasons each.
- Reconciliation errors were 0 in every season.
- B's season-5 replay was identical in all 15 parts.
- Findings:
  - Under-21 zero-start seasons all began at the credit floor. This led to D13.
  - College open starts fell. This led to D14.
  - The 89-at-18 outlier is a rare tail the rules produce; no generation defect was found.
  - The seeded world starts below the population's equilibrium (run A plateaus near 13.1k).

**Current candidate (`c0d1ea5`).**
- Four comparison runs: a21old, a18old, a18new (seed 4207, 10 seasons each) and seed2 (seed 5309, 5 seasons). All exited 0 with 0 reconciliation errors in every season. The analysis is read only, and the review closed at `dc41950`.
- **Pathway from 18.** Measured on the pretreatment cohort: 241 people in the shared 2027 baseline.

  | Outcome | Age 21 rule | Age 18 rule |
  |---|---|---|
  | Golfers with any zero-start season | 4 | 1 |
  | Full-time pros at the end of 2036 | 11 | 18 |
  | Retired | 27 | 29 |

  These are descriptive, arm-level figures, with no individual counterfactual claimed.
- **College open access (retained, D19).**
  - College open starts per player in year 10: 6.58 → 9.15.
  - North America members' cumulative open starts per head: 81.8 → 72.1, with shut-out weeks 74.6 → 136.6.
  - In 2036, all-region end-status groups had zero-start shares of 0 % in both arms. Earlier regional years show small increases, for example North America in 2032 and 2034 and Africa in 2033 and 2034. The cost to members is disclosed; fields were not expanded.
- **Return and re-block (D5.c).**
  - 1,166 returns by 1,125 people; 157 are censored.
  - Of the 1,009 observed, none was cash-blocked again or re-entered the pathway in the next season.
  - 505 took a job again the following winter. This is a separate decision, which the return rule anticipates only by proxy: 431.9 anticipated against 505 realised on the matched 989.
  - No tuning.
- **Prestige.**
  - Multipliers stayed within bounds.
  - Allocations were consistent in 35 of 35 season-pathways.
  - Arrivals equalled their quotas in 62 of 62 cells; 8 terminal cells are not verified.
  - There were 0 venue moves in 15 seed-seasons, so the rule's natural activation is unexercised; its regression tests stand.
- **Familiarity on and off, one season.**
  - The baseline set 6,799 of 124,224 starts (5.5 %).
  - The week-1 comparison is field-matched and exploratory only.
- **Decision evidence on the full world.**
  - The season file grows by +6.8 %; the evidence is 6.4 % of the file in season 1 and 7.2 % in season 2.
  - Outcomes were identical with it on and off.

## 4. Performance (this machine: 4 logical CPUs, Xeon at 2.10 GHz, Python 3.13)

- **Season time:**
  - Full-population seasons took about 200 s each in the smoke test (201.5 s and 197.2 s with the decision evidence on).
  - In the comparison runs they took 197–266 s, with two simulations running at once; the longer seasons came later in each run.
  - These are single-machine measurements under shared load. **The local 120 s season target has not been verified**, on this machine or on the owner's.
- **Story timing:** read only, on run A's 45-season archive.
  - This is indexed assembly only, with the application cache cold (not the filesystem cache).
  - Cold: median 7.44 s, max 11.85 s.
  - With the story index built: 0.103 s.
  - Latest edition first: 3.08 s, then 102 s of background indexing.
  - 2.65 GB RSS is the process's lifetime high-water mark.
  - This is not full UI rendering, not the owner's hardware, and not an instant cold open.
- **Upset estimates:**
  - The stored records are 3.4 % of the raw season file.
  - Recomputing them offline takes about 2.9 s of CPU a season. That is not the in-engine overhead, which is not instrumented.

## 5. Decisions recorded (D13-D21)

| # | Decision |
|---|---|
| D13 | Work-pathway minimum age 18 (older worlds keep 21) |
| D14 | College home-region open amateur access |
| D15 | Keep the richer decision evidence and measure it (measured: section 3) |
| D16 | No simulation tuning in this pass |
| D17 | Weather temperature/firmness and injury tuning out of scope |
| D18 | Decision evidence /2 fulfils E1; its gaps are disclosed limitations |
| D19 | College access retained; the cost to members disclosed |
| D20 | The outlier's organic potential and current maturation kept, provisionally |
| D21 | Prestige and recruitment constants and the seeded size kept as the playtest baseline; tolerance bands not set |

D13-D17 are on rc1. D18-D21 are on the docs-only branch.

## 6. Remaining issues and limitations, disclosed

Roadmap traceability at `c0d1ea5`, 220 rows:

| Status | Rows |
|---|---|
| `done` | 177 |
| `done with known limitation` | 40 |
| `excluded from this pass by decision` | 3 (calibration bands; weather temperature/firmness; injury tuning) |
| Open | **0** |

The known limitations, each recorded on its traceability row:
- **Calibration.** It is unvalidated, and no tolerance bands are set (D21). Every constant is a provisional baseline for this playtest.
- **The return rule** discounts the next winter's job decision by proxy. A realised 51 % against 44 % anticipated is disclosed, with no tuning.
- **Venue moves** never fired naturally in 15 seed-seasons.
- **Decision-evidence size** is measured on a new world's first two seasons only; a mature world of about 13,000 golfers is not measured.
- **The familiarity effect** is exploratory evidence from one season and one seed.
- **Story timing and the 120 s target** are not verified on the owner's hardware.
- **Windows** behaviour and local timing are **forthcoming**: nothing ran on Windows or on the owner's machine. All gates here ran on Linux.
- **Some documents on rc1** read as they did at `c0d1ea5` until the docs-only branch is merged: BACKLOG, the decision log, DECISION_EVIDENCE and the package notes.
- **The review documents and the evidence ledger** live on `build/v16-report`, not on rc1.

## 7. Instructions for Ryan's local long tests

Use the build the reviewer approves: `c0d1ea5`, or `c0d1ea5` plus the docs-only branch, which plays identically.

1. **Get the build.**
   ```
   git fetch origin
   git checkout --detach c0d1ea5        (or the approved main commit)
   ```
   Install Python 3.11 or newer; nothing else is needed.
2. **Check it on your machine.** Double-click `RUN_TESTS_WINDOWS.bat`, or run `python -m unittest discover -s tests`.
   - On this Linux run: 998 tests, OK, with 4 skipped (2 environment-gated, 2 data-conditional). Windows counts are not promised and may differ; please send the result line.
   - The run takes about 2 hours here; your machine may be faster or slower.
   - `RUN_BENCHMARK_WINDOWS.bat` times a season skip and writes `benchmark_result.txt`. Please send it: it is the first measurement of the 120 s target on your hardware.
3. **Play through the observer.** Double-click `RUN_OBSERVER_WINDOWS.bat`, or run `python tools/observer.py --open`.
   - **Create a new world.** Only fresh v2 worlds are supported. Older saves are listed as unsupported and are never continued or migrated, so start a new one.
   - Advance a week, four weeks or a season at a time.
   - **Report a problem** packages the saved world for us.
   - The acceptance checklist is in `docs/OBSERVER_ALPHA.md`.
4. **Optional unattended long run**, the same harness as here. Use a new, empty folder for each run:
   ```
   python tools/long_world.py --session --seeds 4207 --years 25 --workers 2 --out <new folder>
   ```
   - It plays through the same persistent session the observer uses.
   - It stops by itself if a season takes longer than 420 s or free disk falls below 3 GB. Resume with the identical command plus `--resume`.
   - Every season is checked for reconciliation errors.
   - The run can be opened in the observer afterwards (`python tools/observer.py <new folder>/world_4207 --open`; add `--read-only` to browse it without advancing it).
5. **What to send back:**
   - the test result line;
   - `benchmark_result.txt`;
   - season times from the long run's log;
   - any **Report a problem** package;
   - anything that reads wrong in the observer, with the page address.

## 8. Branch map

| Branch | Head | Role |
|---|---|---|
| `integration/v16-rc1` | `c0d1ea5` | The candidate (held) |
| `build/v16-docs-final` | `afb68f3` | Docs-only follow-up for review (parent `c0d1ea5`) |
| `build/v16-report` | this commit | Review documents, comparison analysis, release evidence, this report |
| `build/v16-traceability` | `1a92d3d` | Roadmap traceability matrix against `c0d1ea5` |
| `main` | unchanged | Waits for the reviewer's check of the exact commit |
