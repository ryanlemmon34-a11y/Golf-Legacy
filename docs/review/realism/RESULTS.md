# Realism pass 1: results

**Status: experimental, ready to test, not validated as long-career balance. One planned gate is unmet (the cliff
check, section 2) and one is untested (injuries per start).** The plan and targets are in
`PLAN.md`; how to test is in `TESTING.md`. Main `18a8e23` is unchanged.

## Provenance

- **Engine.** Commit `d619dd6`, frozen in a detached checkout for every measurement and world run below.
  - Later commits on this branch change only `docs/review/realism/` files.
  - Earlier commits and their outputs (`debb655` and before) were withdrawn:
    - `debb655` assigned the starting world's memberships on lowered teenage ratings (reviewer probe).
    - The branch world runs started from it, and from one earlier draft, were stopped within their first season and
      deleted. Nothing from them is used.
  - The first projection measurements (m1–m3) were calibration on earlier drafts. They are superseded and not
    reported.
- **Projection measurement** (`measure.py` at `d619dd6`, sha256 `e20445b5…fa53`). Command:
  `python docs/review/realism/measure.py OUT.json --years 2028-2047 --procs 2`. It is deterministic: re-running one
  cohort reproduced it exactly.
  - Raw output: sha256 `e2693b415d2114e77fe760c95ce4c6cbee332642cbcf49207df81f89b51970e2` (46 MB, not
    committed; regenerate with the command).
  - Tables: `summarise.py` (sha256 `5ac74dd6…7a2d`, with the per-golfer cliff metric) in
    `results/projection_d619dd6.md`.
- **Full-scale worlds** (`tools/long_world.py`, seed 2027, 30 seasons, the whole population, 2 workers each, both
  runs at once on the same 4-CPU cloud machine):
  - main `18a8e23`, started 05:42 UTC;
  - branch `d619dd6`, started 06:00 UTC.

  Comparison: `compare_worlds.py` (sha256 `dff42fc2…6bbf` for the 20-season interim), both arms on identical
  covered seasons.
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

## Full-scale worlds (seed 2027): interim after 20 seasons, final at 30

Both runs are compared on the identical covered seasons, and the season times are for those seasons only. Ratings
are recorded after the season and its winter; ages are the age in the completed season (season minus birth year).
These definitions apply:
- **First observed rating:** a junior's first record comes after their first season and winter, so it is not their
  entry rating.
- **Highest observed:** the highest such record, not a complete-career peak.
- **Censoring:** careers still running at the end are censored, and the latest junior classes are early in their
  careers.
- **One paired world:** every count is descriptive, not a rate, and no significance is claimed.
- **Majors:** counted from the majors' winner ledger, which reconciles with the season snapshots (80 = 80 in each
  arm).
- **Exits:** taken from the recorded career transitions. Retired from play, became a coach or caddie when retiring,
  and became a coach or caddie when they stopped chasing are counted apart. Deaths are not in this export.

Tables: `results/world_seed2027_interim_s20.md`. The earlier 10-season interim (`…_s10.md`) used definitions since
corrected and is superseded.

| realized, seasons 2027–2046 (one paired seed) | main (dev-1) | branch (dev-2) |
|---|---|---|
| Yearly change of the post-winter rating at ages 35–39 / 40–44 / 45–49 | −0.49 / −0.78 / −0.99 | −0.58 / −0.94 / −1.13 |
| Careers seen from 28 or younger to 38 or older: rating at 40 / 45 relative to the highest observed (median) | −3.0 / −7.4 | −3.4 / −8.2 |
| Age at the highest observed rating, same careers: median (10th–90th percentile) | 30 (27–34) | 30 (27–34) |
| Golfer-seasons with starts that had an injury, ages 35–39 / 40–44 / 45–49 (a proxy, not per start) | 6.2% / 8.0% / 9.3% | 6.8% / 9.2% / 11.0% |
| Share of Premier wins (snapshots) / majors (ledger) won at 40+ | 10.6% / 10.0% (8 of 80) | 9.4% / 7.5% (6 of 80) |
| Top-20 mean age, all seasons / last 10 | 30.2 / 29.1 | 29.9 / 29.2 |
| Stock of golfers at 80+ / 85+ in the season snapshot, 2036 / 2046 (not eventual supply; may include that winter's retirees) | 39 / 5; 48 / 15 | 35 / 5; 45 / 14 |
| Juniors arriving 2028–2046: highest observed SO FAR at 75+ / 80+ / 85+ / 90+ (censored) | 107 / 40 / 11 / 1 | 106 / 39 / 10 / 2 |
| Most majors by one golfer; distinct major winners | 9; 42 | 7; 44 |
| Season time over the 20 common seasons: median (total) (cloud, two runs sharing 4 CPUs; relative only) | 304 s (6,005 s) | 308 s (6,129 s) |

**Recorded exits at ages 25–34** among each arm's golfers whose highest observed rating was 65+: retired from play
119 against 130; became a coach or caddie when retiring 15 against 15; when they stopped chasing 114 against 93.
These are descriptive counts, not rates, from one dependent paired world. The 10-season gap (22 against 46 from
play) has narrowed, and its mechanism is unresolved: no decision traces were examined that would establish one.

**The snapshot 80+ stock is lower in some seasons** (2036: 35 against 39; 2046: 45 against 48). This is a stock,
not eventual supply, and it may include golfers who retire that winter. No age or exit explanation is offered
without direct evidence.

## Regression

The full suite ran on `d619dd6` (frozen checkout), one module at a time at low priority. Logs and summary are in
`results/suite_d619dd6/`.
- **90 modules, 1,145 tests, 4 skipped, 0 failures.**
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
- **Full-scale worlds: one paired seed is evidence, not proof.** A second seed is added only if time allows.
  - It is one paired seed of 30 seasons, run against main.
  - Juniors entering in 2028–2056 are seen only up to age 46 at most; most are censored well before their decline.
  - Golfers in the starting world are seen from their starting age.
  - Lifelong elite supply and elite longevity across seeds are therefore **not established** by this run.
  - Decline is measured on survivors, who are a selected group.
- **Readiness changes only the entry level.** Who enters is the existing rule's choice, kept exactly. A junior whose
  readiness is lowered was still chosen on the existing rule's judgement of their level.
- **The long-irons table is engine-wide.** It also applies to worlds made before this branch if they are opened
  here. The development rules apply to new worlds only.
