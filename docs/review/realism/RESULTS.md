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

  Comparison: `compare_worlds.py` as committed alongside each results file (both arms on identical covered seasons).
- **Item 4:** `diag_access.py` (sha256 `0e584dbd…1e38`) on existing long-run outputs (read only):
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

## Full-scale worlds (seed 2027): interim after 10 seasons, final at 30

Both runs are compared on the identical covered seasons. Ratings are season-end values, after the season and its
winter, and these definitions apply:
- **First observed rating:** a junior's first record comes after their first season and winter, so it is not their
  entry rating.
- **Maximum:** the highest observed season-end rating, not a complete-career peak.
- **Censoring:** "last observed age at 85+" is cut off at the run's end.
- **Majors:** counted from the majors' winner ledger, which reconciles with the season snapshots (40 = 40 in each
  arm).
- **Retirements:** taken from the recorded career transitions, from play and into staff jobs separately. Deaths are
  not in this export.

Interim tables after 10 seasons are in `results/world_seed2027_interim_s10.md`. They are one seed, paired against
main, early and censored:

| realized, seasons 2027–2036 | main (dev-1) | branch (dev-2) |
|---|---|---|
| Yearly season-end Overall change at ages 35–39 / 40–44 / 45–49 | −0.47 / −0.73 / −0.89 | −0.57 / −0.90 / −1.11 |
| Golfer-seasons with starts that had an injury, ages 35–39 / 40–44 (a proxy, not per start) | 7.5% / 8.2% | 8.3% / 9.4% |
| Share of Premier wins / majors won at 40+ | 11.9% / 10.0% (4 of 40) | 9.2% / 5.0% (2 of 40) |
| Top-20 mean age | 31.3 | 30.6 |
| Golfers at 80+ / 85+ at season end, 2036 | 39 / 5 | 35 / 5 |
| Juniors (2028–2036): highest observed 75+ / 80+ | 45 / 9 | 46 / 8 |
| Retirements from play at 25–34, golfers whose highest observed rating was 65+ | 22 | 46 |
| Season time, median (cloud, two runs sharing 4 CPUs; relative only) | 284 s | 283 s |

Watch items:
- **Fewer golfers at 80+ in 2036 (35 against 39).** The older 80+ golfers decline sooner. This is the
  longevity-for-supply trade-off, seen in one seed and early.
- **Early retirements doubled (22 → 46).** These are marginal golfers, highest observed rating about 66.5, with no
  injury link (median 0 injury weeks). Their retirement chance is slightly higher, 0.067 against 0.058, consistent
  with faster decline feeding the career decision's progress input. That is about 2.8 standard errors on one seed.
  It is checked again at 30 seasons and on the second seed before any conclusion.

## Regression

The full suite runs one module at a time at low priority on `d619dd6` (results when complete).
`tests/test_realism_pass1.py` has 12 tests, all passing.

Cost of the new code: up to about 0.5 s more to generate a full world (about 1.8 s against 2.1–2.3 s), and at most
about 0.1 s for one winter's aging of 6,449 golfers (noisy timings). Season time is compared in the paired world
runs; it is a cloud figure, relative only. The 120 s target refers to Ryan's machine.

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
