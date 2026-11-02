# Realism pass 1: results

**Status: experimental, ready to test, not validated as long-career balance.** The plan and targets are in
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

  Comparison: `compare_worlds.py` (below, when complete).
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
| Eventual supply, readiness alone (arm R): reach 80+ / 85+ / 90+ per seed | within −3% | 39.6 / 9.0 / 2.2 | 39.4 / 9.0 / 2.2 | yes |
| The 99-potential prodigy (seed 386509): entry → maximum | within 1 point | 96 → 97.7 at 26 | 94 → 97.2 at 27 | yes |

All juniors: the share entering within 5 points of potential goes from 15.5% to 8.4%. The entry Overall change has
mean −0.33 and median −0.03; the largest change is −4.55, for a junior who was at potential.

## 2. Individualized, attribute-specific aging

Projection, arm G (aging only), golfers whose maximum is 70+, by aging-rate tercile. Full tables are in
`results/projection_d619dd6.md`.

| measure | target | dev-1 | dev-2 | met |
|---|---|---|---|---|
| Decline from maximum to 40 / 45 / 50, low tercile | ×1.1–1.4 | −1.6 / −4.3 / −8.1 | −1.8 / −5.0 / −9.5 (×1.13 / 1.16 / 1.17) | yes |
| … middle tercile | ×1.1–1.4 | −2.3 / −6.1 / −11.4 | −2.8 / −7.2 / −13.6 (×1.22 / 1.18 / 1.19) | yes |
| … high tercile | ×1.1–1.4 | −3.6 / −8.9 / −16.2 | −4.1 / −10.4 / −19.1 (×1.14 / 1.17 / 1.18) | yes |
| Age at maximum, 80+ golfers: median (10th–90th percentile) | within 1 year | 32 (29–35) | 31 (29–34); with readiness too: 32 (29–34) | yes |
| Reach 80+ / 85+ / 90+ per seed | within −3% | 39.6 / 9.0 / 2.2 | 39.4 / 9.0 / 2.2 | yes |
| Golfer-years at 85+ per seed | −3% to −15% | 159.2 | 150.4 (−5.5%) | yes |
| Last season at 85+: median age (90th percentile) | median −1 to −3 years | 39 (48) | 38 (46) | yes |
| Low aging-rate golfers last longest; ordering by tercile kept | kept | yes | yes | yes |
| Physical attributes at 45, aging rate 1: power / stamina | −25 to −30 / −28 to −34 | −19 / −19 | −27 / −31 (power about −13 yards from 85) | yes |
| Green reading after peak + 8 | matures to 48 | declined (shadowed) | matures (test) | yes |

**Cliff check, corrected.** `PLAN.md` set "largest one-year drop before 50, 99th percentile ≤ 2.5". The first
summary pooled every annual change, which can hide one golfer's rare severe drop. The corrected metric takes each
golfer's own largest one-year loss before 50, then the 99th percentile and the maximum across golfers:

| tercile | dev-1: per-golfer p99 / largest | dev-2 (G): per-golfer p99 / largest | pooled p99, dev-1 → dev-2 |
|---|---|---|---|
| low | 1.14 / 1.22 | 1.67 / 1.81 | 1.00 → 1.32 |
| middle | 1.46 / 1.56 | 1.98 / 2.09 | 1.30 → 1.67 |
| high | 2.51 / 2.89 | 2.57 / 2.88 | 2.03 → 2.19 |

No golfer's worst year is worse than dev-1's worst (2.88 against 2.89). The high-tercile per-golfer p99 is 2.57,
just above the 2.5 written in the plan; dev-1 itself is 2.51 on this metric. The yearly loss grows smoothly with
age, and a unit test bounds its year-to-year change.

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

## 4. Diagnostic only: access and field gaps (no change made)

**Off-Premier counts are not defects.** The table counts high-Overall golfers who are not on the Premier Tour. That
count is a diagnostic only. Amateur status, college, an alternative or senior tour, eligibility and scheduling
choices are ordinary reasons to be elsewhere, so none of them is automatically an access defect. No field-strength
tuning or opposition boost is proposed or authorized.

Read-only, existing long runs (`results/item4_existing_seeds.md`):

| run | seeds (seasons) | world top-100 by Overall not on Premier (mean per season) | where | Premier best − 10th / − 20th |
|---|---|---|---|---|
| 473690a | 360013 (45) | 18.5 | amateur 11.5, Challenger 4.8, mini 1.9 | 9.2 / 11.5 (second half 11.9 / 14.3) |
| 473690a | 2027 (10), 3031 (10) | 11.5, 11.9 | mostly amateurs, about 4 Challenger, about 2 mini | 4.9–10.2 / 7.6–12.4 |
| c0d1ea5 released configuration | 4207 (10) | 13.4 | amateur 6.9, Challenger 4.1, mini 1.3, club pro 1.0 | 6.2 / 10.3 |
| c0d1ea5 | 5309 (5) | 6.0 | Challenger 4.2, amateur 1.8 | 9.2 / 11.9 |

What the readings show:
- The top of Premier fields can sit 10–14 Overall points above the 20th-best member, most in the oldest run's
  second half. That is a dominance signal, and the right next step is a separate study of field strength; this pass
  makes no change for it.
- A handful of mini-tour professionals in the world top 100 each season is the one group worth following up. Their
  recorded reasons (money, schedule, entry) would need checking before calling anything a defect.

The same diagnostic for the two full-scale runs is in the world comparison below.

## Full-scale worlds (seed 2027, 30 seasons): pending

They run, and are monitored, through completion. The comparison will be added from `compare_worlds.py`:
- elite supply over time and realized maxima of juniors;
- top-20 and top-50 ages;
- wins, Premier wins and majors by age;
- age at maximum and decline;
- year-on-year change by age;
- injuries and retirements by age;
- the item-4 diagnostic;
- dominance;
- season times.

## Regression

The full suite runs one module at a time at low priority on `d619dd6` (results when complete).
`tests/test_realism_pass1.py` has 12 tests, all passing.

Cost of the new code: up to about 0.5 s more to generate a full world (about 1.8 s against 2.1–2.3 s), and at most
about 0.1 s for one winter's aging of 6,449 golfers (noisy timings). Season time is compared in the paired world
runs; it is a cloud figure, relative only. The 120 s target refers to Ryan's machine.

## Limits and censoring

- **Projections are controlled.** One fixed schedule, self-coached, no injuries, money, access limits or
  retirement. They isolate the development laws and are not realized careers.
- **One full-scale seed is evidence, not proof.**
  - It is one paired seed of 30 seasons, run against main.
  - Juniors entering in 2028–2056 are seen only up to age 46 at most; most are censored well before their decline.
  - Golfers in the starting world are seen from their starting age.
  - Lifelong elite supply and elite longevity across seeds are therefore **not established** by this run.
  - Decline is measured on survivors, who are a selected group.
- **Readiness changes only the entry level.** Who enters is the existing rule's choice, kept exactly. A junior whose
  readiness is lowered was still chosen on the existing rule's judgement of their level.
- **The long-irons table is engine-wide.** It also applies to worlds made before this branch if they are opened
  here. The development rules apply to new worlds only.
