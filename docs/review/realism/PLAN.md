# Realism pass 1: plan, measured targets and acceptance

Branch `build/realism-youth-aging-longirons`, from released main `18a8e23`. It is kept apart from the career branch;
main is unchanged; nothing is merged or released. Ryan approved items 1–3, with item 4 as a diagnostic only.

Out of scope: tee waves (morning/afternoon), blanket randomness, consistency nerfs, major-count caps, boosting the
opposition, weather, scoring tables other than long irons.

**Rules flag.** A world records the development rules it was created with (`World.dev_rules`, `Season.dev_rules`):
`dev-2` for new worlds, `dev-1` for earlier saves and for the paired baseline. It is a small flag for reproducibility
and paired testing, not a migration. The long-irons table (item 3) is engine-wide.

Baselines below are measured on `dev-1` (main) with the harness `measure.py`: five seeds (11, 2027, 386509, 7, 99),
20 production junior classes each (2028–2047, 30,087 juniors). Projections use the production `develop_week` and
`age_year` on a fixed schedule to age 50. Each row gives the measured baseline, the target and the reason for it.

## 1. Near-finished teenage starting ability

**Measured (dev-1).**
- Entrants with potential 80+:
  - headroom (potential minus entry Overall): median 10.3, 10th percentile 5.8;
  - 2.6% enter within 3 points of their potential, 7.9% within 5.
- All juniors: 15.5% enter within 5 points of their potential. The scouts' rule keeps early developers
  preferentially: it adds a typical growth to the observed level.
- Largest entry: 96.07, a seed-386509 prodigy with potential 99 and peak age 20.9.

**Rule.** After the existing selection, a teenager keeps at least about 4.5 points of headroom at 18 and 2.25 at 19.
The floor is a smooth softplus: typical juniors move by about 0.01, a junior with 5 points of headroom by about 0.6,
one already at potential by 4.5. Potential, peak age, aging rate and all draws are untouched. `age_deficit`, the
scouts' rule, new-professional exclusion and the cohort-share calculations are untouched.
- Scouts and colleges read the exact dev-1 level, so who enters and where they go is unchanged.
- This is not the rejected headroom transform (B2, −2.65% juniors): selection never sees the new level.

| measure | target | why |
|---|---|---|
| Cohort counts per nation and year; identities (id, name, nation, archetype, path, personality, peak, aging) | exactly equal | Approved constraint; no lost juniors |
| New professionals (ages 21–26) | exactly equal, including attributes | Not teenagers |
| Stored potential | equal to the 0.1 rounding | "Preserve exceptional potential" |
| Potential 80+: share within 3 / within 5 of potential | 0% / ≤ 3% (from 2.6% / 7.9%) | The near-finished tail is the target |
| Potential 80+: median headroom | within ±0.3 of 10.3 | Ordinary readiness is not the target |
| Eventual supply, readiness alone (projection: reach 80+, 85+, 90+) | within −3% | "Preserve eventual elite supply" |
| Prodigies (potential 92+) | still reach their projected maximum within 1 point of dev-1, by about the same age | Prodigies remain possible; they now develop |

## 2. Individualized, attribute-specific aging

**Inspected first.**
- Each golfer already has their own `peak_age ~ N(27, 2)` and `aging_rate ~ lognormal(0, 0.3)`, drawn at generation.
- dev-1 ages by category only: physical from peak + 3, `0.30·rate·x^0.7`; technique from peak + 8, `0.15·rate·x^0.7`.
- **The reviewer's green-reading point is confirmed.** In `age_year`, the putting decline branch is tested before
  the experience branch. So from peak + 8, green reading declines like a putting stroke, its experience growth is
  shadowed, and its after-55 rule is unreachable.

**Measured (dev-1 projection; golfers whose maximum is 70+; aging-rate terciles).**
- Median age at maximum: 32 (80+ golfers: 29–35).
- Decline from maximum to ages 40 / 45 / 50:
  - low tercile: −1.6 / −4.3 / −8.1;
  - middle tercile: −2.3 / −6.1 / −11.4;
  - high tercile: −3.6 / −8.9 / −16.2.
- Per seed: 9.0 golfers reach 85+, with 17.7 years at 85+ each; the last 85+ season is at 39 (median) and 48
  (90th percentile).
- Realized in Test2 (survivors): −3.6 from 30 to 40 and −9.6 from 40 to 50. Cárdenas won his last major at 47 and his
  last Premier event at 52.

**Rule (dev-2).** Each attribute has its own onset after the golfer's own peak age, rate and shape, times the
golfer's own aging rate and a per-golfer, per-category factor (lognormal, sd 0.25, mean 1). Golfers also differ in
which parts of their game age first.
- Physical:
  - power and stamina start at the same onset as before; recovery and injury resistance start a year sooner;
  - decline steepens with the years (shape 0.9);
  - 30% of each year's physical loss is conditioning that physical training can win back. That is harder with age,
    through the learning rate.
- Technique: the dev-1 average, redistributed:
  - speed-dependent long irons and recovery play start a year sooner;
  - chipping, lag putting and wedges start later.
- Green reading follows its intended experience path.
- Mental attributes are unchanged. There are no age thresholds and no change to retirement.

**Calibration (projection only, recorded in `RESULTS.md`).** Steeper or earlier physical decline (shape 1.0, or
onset at peak + 2) cut eventual elite supply by about 10%, or took power to the floor by 60. At shape 1.0 a golfer
would be about 57 yards shorter by 50. The power to distance table (`DRIVE_DISTANCE`) says dev-1's −19 power by 45
is already about −10 yards. The final table keeps power realistic (about −13 yards by 45) and puts the extra decline
into stamina, recovery and injury resistance: the maintenance side. Their effects (fatigue, injuries) appear only
in played worlds.

| measure (projection unless stated) | target | why |
|---|---|---|
| Decline from maximum at 40 / 45 / 50, each tercile | ×1.1–1.4 of dev-1 | Stronger, not a cliff; realistic distance loss |
| Median age at maximum | within 1 year of dev-1 (32; 80+ golfers 29–35) | Peaks are not moved |
| Reach 80+ / 85+ / 90+ | within −3% | Eventual elite supply |
| Golfer-years at 85+; last 85+ age | −3% to −15%; median −1 to −3 years | Elite longevity shortened, not removed |
| Low aging-rate golfers | still the longest-lasting; ordering by aging rate kept | Organic outliers kept |
| Largest one-year drop before 50 (99th percentile) | ≤ 2.5 (dev-1 2.0) | No cliffs |
| Physical attributes at 45, aging rate 1 | power −25 to −30, stamina −28 to −34 (dev-1 −19 / −19) | "Stronger physical decline" |
| Realized (full-scale worlds) | top-20 average age, share of wins and majors at 40+ and 45+ no higher than main; 80+ / 85+ supply within run-to-run noise; injuries per start rise with age | Realized careers, access, money, injuries |

## 3. Long irons, 25–60

**Measured.** The shared approach table is flat at 1.05 from 25 to 60. In the winning study, a +5 change wholly
inside 25–60 changed no shot parameter at all, an exact zero, although Overall moved.

**Rule.** Long irons get their own table:
- equal to the shared table at 10 and below and at 60 and above;
- in 25–60, 0.001 better per point (1.085 at 25, 1.05 at 60).

Mid irons and wedges keep the shared table.

| measure | target |
|---|---|
| Rounds with long irons 60+ | identical shot for shot to dev-1 (same seeds) |
| Slope inside 25–60 | 0.001 per point, monotone over 0–100 |
| Mid irons, wedges | table and parameters unchanged |
| Weak golfer, long irons 30 vs 58 | measurably different mean score (dev-1: identical) |

## 4. Diagnostic only (no change)

The diagnostic reads only; it changes nothing and boosts no opposition:
- access of high-Overall golfers who are not on the Premier Tour: promotion, qualification and money;
- Overall gaps between the top player and the 10th–20th in Premier fields and majors.

It covers the full-scale runs (main and branch) and the existing long-run archives, across seeds.

## Acceptance

1. `tests/test_realism_pass1.py`:
   - exact cohorts and identities;
   - new professionals unchanged;
   - new-world rules flag, and earlier saves keep dev-1;
   - dev-1 aging bit-identical to a frozen copy;
   - onsets, monotonicity in aging rate, no cliffs, factor mean 1;
   - green reading, and the conditioning gap that training can win back;
   - the long-irons table, parameters, identical rounds from 60 up, and response below 60.
2. `measure.py` / `summarise.py`: the paired five-seed projection tables, arms A0 (dev-1), R (readiness only),
   G (aging only) and B (both).
3. **Full-scale worlds** (Ryan's preference): seed 2027, 30 seasons, main `18a8e23` against this branch, the whole
   population. More seeds only if time allows. Reduced-scale runs are only supplementary.
4. Regression: the focused suites, then the full suite. Season time is compared with main in the same runs. This is
   a cloud timing, so relative only; the 120 s target is for Ryan's machine.

## Limits

- Projections are controlled: no access, money, injuries, coaching or retirement.
- One or two full-scale seeds are evidence, not a validation of long-career balance.
- Until the full-scale comparison is read, this branch is **experimental: ready to test, not validated**.
