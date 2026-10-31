# Release evidence: candidate `integration/v16-rc1` at `c0d1ea5`

**Candidate:** `c0d1ea598bc784611e7e26cc414f754671965530`.
- Engine id (golfsim/ fingerprint): `1949ff63f33ce610a7cd4fe70c089b0b4fbf5b9e`.
- Every gate below ran on a clean detached checkout of this commit (0 uncommitted files).
- Main is **held** until the reviewer verifies this evidence.

The docs-only follow-up is `a2d56fb` (branch `build/v16-docs-final`, parent `c0d1ea5`).
- It changes six `docs/*.md` files only.
- It changes no code, test or config file, and its engine id is identical.
- The code and test evidence below therefore stays tied to `c0d1ea5`; the full suite was not rerun for prose.

## Two kinds of evidence (do not mix them)

| | Build | What it is |
|---|---|---|
| **Earlier baseline** | pinned `473690a` | Diagnostic runs A (seed 360013, 45 seasons), B, C (seed 2027, support on and off) and D (seed 3031), 10 seasons each. Report `docs/review/DIAGNOSTIC_RUNS_ABCD.md`. Read-only story timing on run A's archive, assembled with the candidate's code. **Not evidence about the candidate's engine.** |
| **Current candidate** | `c0d1ea5` | The gates below, plus the four comparison arms and their analysis in `docs/review/arms_comparison/` |

## Final gates on c0d1ea5

All commands ran from the checkout root, one job at a time. Scratch paths are relative to the session's work folder `v18/`.

| Gate | Command | When (UTC) | Exit | Result | Raw output |
|---|---|---|---|---|---|
| G1 full suite | `timeout 14400 nice -n 19 python -m unittest discover -s tests` | 11:48:11 to 13:55:14 | 0 | **Ran 998 tests in 7524.9 s, OK (skipped=4)** | `raw/final_suite_c0d1ea5.log` (unmodified; sha256 `ce37ad3b34d356a8cfd793506e849d17c9cb6a3725d6a2359d0ab399653c8ff7`) |
| Skip reasons (identification only) | `nice -n 19 python -m unittest -v <the 12 tests that can skip>` | 14:21:26 to 14:35:53 | 0 | 12 run, OK (skipped=4); the same 4 as G1 | `raw/skip_reasons_c0d1ea5.log` |
| G2 full-population smoke | `python3 scripts/full_pop_smoke.py <checkout> smoke/final_c0d1ea5 4207 2` | 13:55:14 to 14:05:27 | 0 | see below | `raw/smoke_c0d1ea5.log`, `raw/smoke_c0d1ea5.json` |
| G3 wide-screen navigation | `python3 tools/observer.py <copy of the smoke world> --port 8793`, then `BASE=http://localhost:8793 OUT=<dir> LIMIT=70 node scripts/nav_check.js` | 14:05:27 to 14:06:05 | 0 | **160 pages (80 at 1920 px, 80 at 1366 px), 0 failing, max horizontal overflow 0**; 8 Story views and 12 coaching tabs visited (a missing kind fails) | `raw/nav_results_c0d1ea5.json`, `raw/nav_c0d1ea5.out` |
| G4 evidence on/off equivalence | from G2 | -- | -- | outcome parts differing with the evidence off: **none** | `raw/smoke_c0d1ea5.json` |
| Save/reopen determinism | `python tools/long_world.py --session --seeds 4207 --years 2 --workers 2 --pathway-min-age 18 --college-open-access on --keep-after 1 --out det/det4207`, then `python tools/determinism_replay.py --out det/det4207 --seed 4207 --workers 2` | 14:06 to 14:17:39 | 0, 0 | season 2028 replayed from the copy saved after 2027 and reopened: **identical in all 16 recorded parts** | `raw/determinism_*` |
| Familiarity on/off season | `python3 scripts/fam_off.py <checkout> fam/out_c0d1ea5 4207 smoke/final_c0d1ea5/smoke.json` | 14:17:39 to 14:21:20 | 0 | every outcome part differs, as expected; analysis in `docs/review/arms_comparison/G1E_FAMILIARITY.md` | `raw/fam_off_c0d1ea5.*` |

### Skip reasons (G1's 4 skips)
- **Environment-gated (2):**
  - `test_decision_evidence_world.DecisionEvidenceWorld.test_outcomes_are_identical_to_the_parent_build` ("set GOLF_PARENT_CHECKOUT to the parent build"). The same on/off outcome equivalence is shown on the full population by G4.
  - `test_upsets.HeavyEquivalenceTests.test_recording_changes_no_outcome` ("whole-season run: set GOLF_HEAVY_TESTS=1").
- **Data-conditional (2), because no golfer became staff in the small test world:**
  - `test_observer_gaps.WorldGaps.test_retirement_into_a_staff_role_each_once`;
  - `test_observer_profiles.ProfilesAndStatsTests.test_a_golfer_who_became_staff_keeps_one_identity`.
- The other 8 tests that can skip ran and passed.

### Full-population counts (seed 4207)

| | Golfers | Season time | Season file | Evidence (gzip) | Checkpoint |
|---|---|---|---|---|---|
| G2 2027, evidence on | 6,409 created; 6,409 scheduled; 7,120 at season end | 201.5 s | 13,039,656 B | 830,379 B (6.4 %) | 38,109,556 B |
| G2 2028, evidence on | 6,878 scheduled; 7,802 at season end | 197.2 s | 12,567,224 B | 901,302 B (7.2 %) | 55,410,492 B |
| G2 2027, evidence off | 7,120 at season end | 177.6 s | 12,208,596 B | -- | 36,363,871 B |
| Determinism run | 6,878 then 7,300 active | 204 s, 430 s cumulative | -- | -- | -- |

- Bounds held in G2: at most 13 plans a golfer, 0 over, at most 3 career rows.
- Reconcile errors and staff violations were 0 in every season of the determinism run.
- The season-time differences are single pairs of total runtimes on a shared 4-CPU machine. They are **not** isolated overhead measurements.

## Comparison arms on c0d1ea5 (current candidate)

Run with `python tools/long_world.py --session --seeds S --years N --workers 2 --pathway-min-age A --college-open-access X --out arms/<arm>`. Each arm used a new directory and the harness's 420 s and 3 GB safeguards.

| Arm | Seed | Seasons | Pathway age / college access | Exit | Final active |
|---|---|---|---|---|---|
| a21old | 4207 | 10 | 21 / off | 0 | 10,337 |
| a18old | 4207 | 10 | 18 / off | 0 | 10,343 |
| a18new | 4207 | 10 | 18 / on (build defaults) | 0 | 10,339 |
| seed2 | 5309 | 5 | 18 / on | 0 | 8,826 |

Reconcile errors were 0 in every season of every arm. The read-only analysis, its scripts and its review history are in `docs/review/arms_comparison/` (reviewed and closed at `dc41950`; G1.e at `0061501`).

## Performance caveats to keep in the final report

- **Story timing** is indexed-assembly evidence only. It calls `observer_stories.tell` with an application-cache cold start (the filesystem cache was not cleared).
  - Sample: 20 majors on the legacy 473690a 45-season archive, using the candidate's assembler.
  - Cold: median 7.44 s, max 11.85 s. Indexed: 0.103 s. Latest edition first: 3.08 s, then 102 s of background indexing. The separate read-only index build took 218 s and 1.05 GB.
  - RSS of 2.65 GB is the lifetime high-water mark.
- Nothing here measures full UI rendering, the owner's hardware, an instant cold UI or the local 120 s season target.
- **Upset estimates:** the in-engine cost is not instrumented. The offline recomputation (about 2.9 s CPU a season) is not the in-engine overhead.

## Disk handling

Only disposable generated scratch whose source remains was removed:
- the observer-check copy of the smoke world, after navigation;
- the analysis extraction cache, which can be rebuilt from the arm archives.

Arm runs, run A-D outputs, checkpoints, manifests and logs are all kept. The 3 GB guard was kept, and the queue stopped below 3.4 GB.

## Files

- `RELEASE_EVIDENCE_LEDGER.md`: the running ledger, covering the serialized queue, quick tests, failed-then-fixed items, reviews, the baseline runs and the final gates.
- `raw/`: the gate outputs, unmodified. Absolute paths in them refer to the session's work folder.
- `scripts/`: the smoke, familiarity and navigation scripts and the queue scripts that ran them.
