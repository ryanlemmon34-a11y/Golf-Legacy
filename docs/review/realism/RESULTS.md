# Realism pass 1: results

**Status: final for this pass, code frozen. An experimental playtest build, not fully calibrated balance.** One
planned gate is unmet (the cliff check, section 2) and one is untested (injuries per start). Test from the branch
head, which carries the reviewed engine fix for the 2049 runaway (below), against main + the same fix (`46013a5`).
The plan and targets are in `PLAN.md`; how to test is in `TESTING.md`. Main `18a8e23` is unchanged.

## Provenance

**Code.**
- **Realism engine `d619dd6`:** every projection measurement, the paired seed-2027 world through 2048, and the realism
  branch's full suite.
- **Branch head:** carries `d619dd6` plus the reviewed engine fix `e99cb20` (`fix/engine-dogleg-retee`, head `46013a5`,
  merged at `c6ce161`). After that merge only `docs/review/realism/` files change.
- **Main:** `18a8e23`, unchanged.
- **Withdrawn and not used:**
  - `debb655` and earlier, and their world runs. `debb655` assigned the starting world's memberships on lowered
    teenage ratings (reviewer probe); those runs were stopped within their first season and deleted.
  - Projection calibrations m1–m3, made on earlier drafts.

**Projection measurement.**
- **Script and command:** `measure.py` at `d619dd6`, sha256 `e20445b5…fa53`, run as
  `python docs/review/realism/measure.py OUT.json --years 2028-2047 --procs 2`.
- **Deterministic:** re-running one cohort reproduced it exactly.
- **Raw output:** sha256 `e2693b415d2114e77fe760c95ce4c6cbee332642cbcf49207df81f89b51970e2` (46 MB, not committed;
  regenerate it with the command).
- **Tables:** made by `summarise.py` (sha256 `5ac74dd6…7a2d`, per-golfer cliff metric), in
  `results/projection_d619dd6.md`.

**Full-scale worlds** (`tools/long_world.py`, the whole population, 2 workers each, on a shared 4-CPU cloud machine).

| run | arms | what it supports |
|---|---|---|
| Seed 2027, clean | main `18a8e23` against realism `d619dd6`, 22 common single-version seasons (2027–2048) | **The primary comparison.** The realism run stopped in 2049 on the latent engine defect (section below). |
| Seed 2027, mixed version | main `18a8e23` (no fix) for 30 seasons, against the realism run continued from its verified 2048 checkpoint on realism + fix `c528575` for 2049–2056 (`results/runaway_2049/`) | Evidence that the fixed build crosses the failure point and completes. From 2049 the arms differ in the engine fix as well as the realism rules, so it is **not** a single-version causal comparison. |
| Seed 3031, same-fix pair | main + fix `46013a5` (engine `2abe4dc8`) against realism + fix `c528575` (engine `f0529419`), both carrying the identical engine fix; 30 single-version seasons each (2027–2056), no restarts | **A causal pair for the realism rules alone**, a second paired seed. Not the same engine as the seed-2027 clean pair (that pair has no fix). |

**Run data.** The run directories (saves, run states, analysis exports, history archives) were held in RAM and
were lost when the container restarted on 2026-11-02 at 12:06 UTC. Only the committed logs, manifests, provenance and
tables remain. They are listed with their SHA-256 hashes in `results/EVIDENCE_runs.md`, along with what was lost and
the disk gap.

**Scripts.**
- Comparison: `compare_worlds.py`, sha256 `dff42fc2…6bbf`. Both arms are always compared on the identical covered
  seasons.
- **Item 4:** `diag_access.py` (sha256 `65dea982…5f02`) on existing long-run outputs (read only):
  - commit `473690a`: seeds 360013 (45 seasons), 2027 and 3031 (10 each);
  - commit `c0d1ea5`: seeds 4207 (released configuration, 10) and 5309 (5).

## 1. Near-finished teenage starting ability

Paired projection layer: five seeds × 20 production junior classes, 30,087 juniors. A0 is dev-1 (main); B is
dev-2 (this branch).

| measure | target | dev-1 | dev-2 | met |
|---|---|---|---|---|
| Junior classes with equal counts and identities (id, name, nation, peak, aging, archetype, path, status, personality) | exact | — | 100 / 100 | yes |
| Stored potential | exact | — | largest difference 0.0 | yes |
| New professionals, rows and entry Overall | exact | — | 100 / 100 | yes |
| Starting world, full size (seed 2027): every golfer's path, money, backing, potential; attributes of everyone 20+ | exact | — | test passes (fails on `debb655`) | yes |
| Potential 80+: share within 3 / within 5 of potential | 0% / ≤ 3% | 2.6% / 7.9% | **0.0% / 2.6%** | yes |
| Potential 80+: median headroom (10th percentile) | median ±0.3 | 10.28 (5.79) | 10.28 (6.09) | yes |
| Entrants per seed at 80+ / 85+ / 90+ | (lower at the top, by design) | 3.2 / 0.6 / 0.2 | 2.8 / 0.6 / 0.2 | — |
| Largest entry | — | 96.07 | 94.25 | — |
| Eventual supply, readiness alone (arm R; controlled projection): reach 80+ / 85+ / 90+ per seed | within −3% | 39.6 / 9.0 / 2.2 | 39.4 / 9.0 / 2.2 | yes |
| The 99-potential prodigy (seed 386509): entry → maximum | within 1 point | 96 → 97.7 at 26 | 94 → 97.2 at 27 | yes |

All juniors: the share entering within 5 points of potential goes from 15.5% to 8.4%. The entry Overall change has
mean −0.33 and median −0.03; the largest change is −4.55, for a junior who was at potential.

## 2. Individualized, attribute-specific aging

The shipped rules are arm **B**, readiness and aging together. Arm **G** (aging only) is shown for attribution.
Everything here is a controlled projection: one schedule, no access, money, injuries or retirement. It is not
realized supply. Full tables are in `results/projection_d619dd6.md`.

| measure (projection) | target | dev-1 (A0) | dev-2 shipped (B) | aging only (G) | met |
|---|---|---|---|---|---|
| Decline from maximum to 40 / 45 / 50, low tercile | ×1.1–1.4 | −1.6 / −4.3 / −8.1 | −1.8 / −5.0 / −9.5 | same as B | yes |
| … middle tercile | ×1.1–1.4 | −2.3 / −6.1 / −11.4 | −2.8 / −7.2 / −13.6 (×1.22 / 1.18 / 1.19) | same | yes |
| … high tercile | ×1.1–1.4 | −3.6 / −8.9 / −16.2 | −4.1 / −10.4 / −19.1 (×1.14 / 1.17 / 1.18) | same | yes |
| Age at maximum, golfers reaching 80+: median (10th–90th percentile) | within 1 year | 32 (29–35) | 32 (29–34) | 31 (29–34) | yes |
| Reach 80+ / 85+ / 90+ per seed (20 classes a seed) | within −3% | 39.6 / 9.0 / 2.2 | 39.2 / 9.0 / 2.2 (−1.0% / 0 / 0) | 39.4 / 9.0 / 2.2 | yes |
| Golfer-years at 85+ per seed | −3% to −15% | 159.2 | 150.0 (−5.8%) | 150.4 (−5.5%) | yes |
| Last season at 85+: median age (90th percentile) | median −1 to −3 years | 39 (48) | 38 (46) | 38 (46) | yes |
| Low aging-rate golfers last longest; ordering by tercile kept | kept | yes | yes | yes | yes |
| Physical attributes at 45, aging rate 1: power / stamina | −25 to −30 / −28 to −34 | −19 / −19 | −27 / −31 (power about −13 yards from 85) | same | yes |
| Green reading after peak + 8 | matures to 48 | declined (shadowed) | matures (unit test) | same | yes |

The 90+ tail is tiny: 11 golfers over five seeds reach 90+ in the projection. It is a controlled projection, not
realized supply.

**Cliff check: the planned gate is not met.**
- `PLAN.md` set "largest one-year drop before 50, 99th percentile ≤ 2.5".
- The first summary pooled every annual change. The corrected metric takes each golfer's own largest one-year loss
  over the ages 18→19 through 49→50 (so through 50), then the 99th percentile across golfers.
- On that metric the high tercile under dev-2 is **2.57, against the ≤ 2.5 gate (dev-1 2.51): unmet.**

| tercile | dev-1: per-golfer p99 / sample maximum | dev-2 (B): per-golfer p99 / sample maximum | pooled p99, dev-1 → dev-2 |
|---|---|---|---|
| low | 1.14 / 1.22 | 1.68 / 1.82 | 1.00 → 1.32 |
| middle | 1.46 / 1.56 | 1.98 / 2.10 | 1.30 → 1.67 |
| high | 2.51 / 2.89 | 2.57 / 2.88 | 2.03 → 2.19 |

The sample maxima (2.88 against 2.89) are the largest single values among the selected controlled projections.
They do not show that no individual golfer gets a worse year, and the per-golfer p99 rises in every tercile. What
holds is the absence of steps: the yearly loss grows smoothly with age and a unit test bounds its year-to-year
change. The gate is reported as unmet, for Ryan to decide whether to:
- accept 2.57;
- soften the steepest physical shape;
- restate the gate on the new metric.

**Injuries per start: untested.** The planned realized gate, "injuries per start rise with age", cannot be computed
from the long-run export, which has weeks injured per golfer-season but not injury episodes per start. The world
comparison shows weeks injured per golfer-season with starts as a proxy only.

## 3. Long irons, 25–60

Paired rounds: 2,500 per cell, same seeds, Ashford Ridge, golfers with every attribute at the stated level except
long irons. Values are mean strokes per round.

| golfer | long irons | dev-1 | dev-2 | difference (standard error) |
|---|---|---|---|---|
| all 40 | 25 / 40 / 50 | 80.321 / 80.321 / 80.321 (identical: the dead zone) | 80.477 / 80.394 / 80.351 | +0.156 (0.037) / +0.073 (0.030) / +0.030 (0.020) |
| all 50 | 35 / 50 / 60 | 77.827 each | 77.872 / 77.833 / 77.827 | +0.045 / +0.006 / 0.000 |
| all 60 | 45 / 60 / 70 | 75.622 / 75.622 / 75.582 | 75.668 / 75.622 / 75.582 | +0.045 / 0.000 / 0.000 |
| all 75 | 60 / 75 / 85 | 72.147 / 72.032 / 71.894 | identical | 0.000 |

Within 25–60, each point of long irons now helps a little: about 0.13 strokes a round from 25 to 50. From 60 up,
rounds are identical shot for shot (tested). Mid irons and wedges keep the shared table (tested).

## 4. Diagnostic only, partial: access and Premier membership gaps (no change made)

- **No change is proposed or authorized.** This section makes no field-strength tuning or opposition boost.
- **Off-Premier counts are not access defects.** The table counts high-Overall golfers who are not on the Premier
  Tour. Being off it (amateur, college, an alternative or senior tour, eligibility, scheduling choices) does not
  establish blocked access.
- **Membership gaps, not field gaps.** The gaps are between Premier Tour members (membership), not tournament fields
  or majors.
- **Later seasons are not proof the starting population has gone.** A run's later seasons do not establish that.
- **Item 4 is partial.**

Read-only, existing long runs (`results/item4_existing_seeds.md`):

| run | seeds (seasons) | world top-100 by Overall not on Premier (mean per season) | where | Premier members: best − 10th / − 20th |
|---|---|---|---|---|
| 473690a | 360013 (45) | 18.5 | amateur 11.5, Challenger 4.8, mini 1.9 | 9.2 / 11.5 (second half 11.9 / 14.3) |
| 473690a | 2027 (10), 3031 (10) | 11.5, 11.9 | mostly amateurs, about 4 Challenger, about 2 mini | 4.9–10.2 / 7.6–12.4 |
| c0d1ea5 released configuration | 4207 (10) | 13.4 | amateur 6.9, Challenger 4.1, mini 1.3, club pro 1.0 | 6.2 / 10.3 |
| c0d1ea5 | 5309 (5) | 6.0 | Challenger 4.2, amateur 1.8 | 9.2 / 11.9 |

Two readings worth a separate look (not acted on):
- the spread among the top Premier members, widest in the oldest run;
- the few mini-tour professionals in the world top 100 each season, whose recorded reasons (money, schedule,
  entry) would need checking before anything is called a defect.

## Full-scale worlds (seed 2027): 22 common seasons (the branch run stopped in 2049)

**Provenance.**
- **main `18a8e23`:** completed 30 seasons (2027–2056).
- **branch `d619dd6`:** stopped in its 23rd season (2049) at the engine's runaway guard. The cause is a latent defect
  in the engine's tee planning, identical on main (`results/runaway_2049/RUNAWAY.md`). Its 22 completed seasons were
  exported from the run's per-season state (`seed_2027.state.pkl` and save after 2048) without re-running anything.
- **Comparison:** the two arms are compared on the identical covered seasons 2027–2048.
- **No mixed-version data:** nothing in this section comes from a mixed-version run. The branch's seasons from 2049
  onward were played later on realism + fix, as a separately labelled mixed-version continuation (section below,
  `results/world_seed2027_mixed30.md`).

**Definitions.**
- Ratings are recorded after the season and its winter; ages are the age in the completed season.
- "Highest observed" is the highest such record, not a complete-career peak.
- Careers still running at the end are censored.
- Counts are descriptive, from one dependent paired world, not rates.
- Majors come from the winner ledger, which reconciles with the snapshots (88 = 88 in each arm).
- Exits come from the recorded transitions, by kind.

Tables: `results/world_seed2027_s22.md`. The 10- and 20-season interims are superseded.

| realized, seasons 2027–2048 (one paired seed) | main (dev-1) | branch (dev-2) |
|---|---|---|
| Yearly change of the post-winter rating at ages 35–39 / 40–44 / 45–49 | −0.49 / −0.78 / −0.99 | −0.58 / −0.93 / −1.13 |
| Careers seen from 28 or younger to 38 or older: rating at 40 / 45 relative to the highest observed (median) | −3.0 / −7.4 (n 341) | −3.5 / −8.3 (n 332) |
| Age at the highest observed rating, same careers: median (10th–90th percentile) | 30 (27–34) | 30 (27–34) |
| Last observed age at 85+, median (90th percentile), censored | 33 (41) | 33 (42) |
| Share of Premier wins (snapshots) / majors (ledger) won at 40+ | 10.9% / 9.1% (8 of 88) | 10.0% / 9.1% (8 of 88) |
| Stock of golfers at 80+ / 85+ in the season snapshot, 2036 / 2048 (not eventual supply; may include that winter's retirees) | 39 / 5; 49 / 15 | 35 / 5; 47 / 14 |
| Juniors arriving 2028–2048: highest observed SO FAR at 75+ / 80+ / 85+ / 90+ (censored) | 119 / 46 / 12 / 2 | 117 / 45 / 11 / 2 |
| Most majors by one golfer; distinct major winners | 10; 44 | 7; 47 |
| Season time over the 22 common seasons: median (total) (cloud, two runs sharing 4 CPUs; relative only) | 307 s (6,729 s) | 312 s (6,801 s) |

**Recorded exits** are in the tables as descriptive counts by kind. Their mechanism is unresolved: no decision
traces were examined. The snapshot 80+ stock is a stock, not eventual supply, and no age or exit explanation is
offered for its differences.

## The 2049 runaway: engine fix, integration and the completed seed-2027 run

- **The defect** (`results/runaway_2049/RUNAWAY.md`): the branch's run stopped in 2049 at the engine's runaway guard,
  on a latent tee-planning defect that is identical on main.
- **The fix:** `fix/engine-dogleg-retee`, engine `e99cb20`, head `46013a5` (from main `18a8e23`). It was reviewed
  and accepted for test branches only.
- **Its tests:** `tests/test_tee_plan.py` (11).
- **The fixture, replayed with execution-only instrumentation:**

  | build | outcome |
  |---|---|
  | main `18a8e23` | runaway: 30 tee shots, all driver, 30 penalties |
  | `d619dd6` | runaway: 30 tee shots, all driver, 30 penalties |
  | fix | 4 strokes |

- **The fix's full suite:** 90 modules, 1,147 tests run, 4 skipped (1,143 non-skipped), 0 failures
  (`results/suite_fix_46013a5/`).
- **Integrated into the test branches only; main is untouched.**
  - Realism: `c6ce161` (merge), `c528575` (the resume driver).
  - Career: `da4075e` (merge), `8a2b92a`. Its all-AI equivalence reference is now main + fix: main alone reproduced
    its old digests, and main + fix and career + fix give identical new ones.
- **Combined-branch checks** (`results/combined_checks/`): realism + fix 148 tests and career + fix 90 tests, all
  passing.

**The failed seed, continued: a mixed-version run, labelled as such.** Provenance:
`results/runaway_2049/PROVENANCE_mixed.json` (`resume_mixed.py`).

| part | seasons | engine |
|---|---|---|
| first | 2027–2048 | `d619dd6` (engine `b62c9c83`) |
| second | 2049–2056 | realism + fix `c528575` (engine `f0529419`) |

- **Checkpoint:** the run resumed from the verified 2048 checkpoint, whose save and run-state hashes are recorded.
- **Restart:** one restart, from the 2053 checkpoint on the same engine, after the continuation process was killed by
  the memory limit while saving after 2054. Season 2054 was replayed deterministically.
- **Completion:** it crossed 2049, the failure season, and completed 2056. That is 30 contiguous seasons, every one
  logged with no reconciliation errors or staff violations.
- **Tables:** `results/world_seed2027_mixed30.md`, against main without the fix. From 2049 the arms differ in the
  engine fix as well as the realism rules, so those seasons are not a single-version causal comparison. The 22
  common single-version seasons above remain the primary comparison.

**Second seed, a causal pair with the identical fix in both arms.** Seed 3031, main + fix `46013a5` (engine
`2abe4dc8`) against realism + fix `c528575` (engine `f0529419`).
- **Completed:** both arms, 30 single-version seasons (2027–2056), no restarts. Every season logged reconciliation
  errors 0+0, staff violations 0, population ok, with no tracebacks and no runaway.
- **Evidence:** `results/seed3031_logs/` holds the run logs and manifests. Tables are in
  `results/world_seed3031_samefix30.md` (`compare_worlds.py`, sha256 `dff42fc2…6bbf`).
- **Causal reading:** this pair differs only in the realism rules, because both arms carry the same engine fix. It is
  still one paired world, so the counts are descriptive.

| realized, seasons 2027–2056 (one paired seed, same fix in both arms) | main + fix (dev-1) | realism + fix (dev-2) |
|---|---|---|
| Yearly change of the post-winter rating at ages 35–39 / 40–44 / 45–49 | −0.49 / −0.78 / −0.97 | −0.57 / −0.92 / −1.10 |
| Careers seen from 28 or younger to 38 or older: rating at 40 / 45 relative to the highest observed (median) | −2.8 / −6.7 (n 545) | −3.3 / −7.9 (n 553) |
| Age at the highest observed rating, same careers: median (10th–90th percentile) | 30 (28–34) | 30 (28–33) |
| Last observed age at 85+, median (90th percentile), censored | 41 (45) | 40 (44) |
| Share of Premier wins (snapshots) / majors (ledger) won at 40+ | 16.1% / 20.0% (24 of 120) | 13.0% / 19.2% (23 of 120) |
| Top 50 by Overall: mean number aged 40+ / 45+, all seasons (last 10) | 7.37 / 2.83 (5.20 / 2.00) | 6.17 / 1.87 (3.70 / 0.80) |
| Stock of golfers at 80+ / 85+ in the season snapshot, 2036 / 2056 (not eventual supply) | 33 / 8; 28 / 4 | 26 / 7; 29 / 4 |
| Juniors arriving 2028–2056: highest observed SO FAR at 75+ / 80+ / 85+ / 90+ (censored) | 175 / 37 / 5 / 2 | 176 / 40 / 5 / 2 |
| Most majors by one golfer; distinct major winners | 18; 50 | 14; 55 |
| Season time over the 30 seasons: median (total) (cloud, two runs sharing 4 CPUs; relative only) | 330 s (10,075 s) | 324 s (9,983 s) |

**Both seeds read the same way.** Decline from the late 30s is a little steeper on the realism rules (about 0.1 a
year more at 35–49), and fewer golfers aged 40+ hold top-50 places and Premier wins. Majors at 40+ are about level,
and top junior supply is about level. With one world per seed these are descriptive differences, not established
effects.

## Regression

The full suite ran on `d619dd6` (frozen checkout), one module at a time at low priority. Logs and summary are in
`results/suite_d619dd6/`.
- **90 modules. On each module's final successful run: 1,148 tests run, 4 skipped (1,144 non-skipped), 0 failures.**
  (An earlier total of 1,145 missed the three single-test modules, "Ran 1 test".)
- `test_long_run_safeguards` first errored twice (2 of 18). The harness's own 3 GB free-disk safeguard tripped
  because its temporary folder was on the main disk, which had 2.3 GB free. Re-run with the temporary folder in RAM
  (`TMPDIR=/dev/shm/...`), it passed 18 of 18. Both runs are in the summary.
- The four skips, with their messages as the tests print them, are listed in `results/suite_d619dd6/SKIPS.md`.
- `tests/test_realism_pass1.py`: 12 tests, all passing.

Cost of the new code: up to about 0.5 s more to generate a full world (about 1.8 s against 2.1–2.3 s), and at most
about 0.1 s for one winter's aging of 6,449 golfers (noisy timings). Season time in the paired world runs is in the
table above; it is a cloud figure, relative only. The 120 s target refers to Ryan's machine.

## Limits and censoring

- **Projections are controlled.** One fixed schedule, self-coached, no injuries, money, access limits or
  retirement. They isolate the development laws and are not realized careers.
- **Full-scale worlds are evidence, not proof.**
  - **Seed 2027:** 22 clean single-version paired seasons, then a labelled mixed-version continuation to 30.
  - **Seed 3031:** a 30-season same-fix pair, differing only in the realism rules. No further seeds are planned
    for this pass.
  - Juniors entering from 2028 are seen at most to their mid-40s; most are censored before their decline.
  - Golfers in the starting world are seen from their starting age.
  - Lifelong elite supply and elite longevity across seeds are therefore **not established**.
  - Decline is measured on survivors, who are a selected group.
- **Readiness changes only the entry level.** Who enters is the existing rule's choice, kept exactly. A junior whose
  readiness is lowered was still chosen on the existing rule's judgement of their level.
- **Two changes are engine-wide:** the long-irons table and the dogleg tee-plan fix. Both apply to worlds made before
  this branch if they are opened here; the development rules apply to new worlds only.
  - Rounds with long irons 60+ are bit-identical only for the isolated long-irons change. Where the dogleg fix
    triggers, later shots differ.
