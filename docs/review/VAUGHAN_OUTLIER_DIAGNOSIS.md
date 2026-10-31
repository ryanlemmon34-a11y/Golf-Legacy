> **Read-only calibration diagnosis for review.** Pinned run A (build 473690a, seed 360013, 45 seasons) and the
> generator code at 473690a and at the candidate 0a05310; no code changed, nothing tuned, no seasons simulated (one
> 92-second generator-only sample). Scripts and intermediate outputs stay in the session scratch folder (`calib/`),
> not in the repository. A design question for the owner and reviewer, not a defect fix.

# Rupert Vaughan (run A, seed 360013): justified outlier or calibration defect?

Read-only diagnosis, 2026-10-31. Pinned diagnostic run A (build 473690a, 45 seasons 2027-2071). No code was changed
and no season was simulated. The only computations were reading the recorded data and drawing generator samples
(pure `junior_class` draws, about 100 s under `nice -n 19`, peak RSS about 1 GB).

## Verdict (summary)

**Vaughan is a rare outlier that the model's rules produce. These checks found no defect in generation or
development, and no early-maturation defect specific to him. Calibration is not validated: there are no agreed
target frequencies to validate against.**

Three model-wide calibration properties explain him. Whether they are acceptable is a design decision, not a
defect:

1. **Potential has a Gaussian tail up to the 99 cap.** Potential is drawn as N(mu ≈ 35, 13) for about 10,000
   juniors a year. Over 44 cohorts that gives an expected 0.29 juniors with potential ≥ 97 (25 % of worlds analytic,
   31/100 sampled) and 0.13 juniors at the 99 cap (12-14 % of worlds).

   That 25-31 % is the chance of a **potential-97+ junior** in 44 cohorts. It is **not** the chance of the full
   Vaughan phenotype (potential 97+, then 30 majors and about 25 seasons as the top-rated pro). The career outcome
   also needed a large lead over the next junior (11/100 sampled worlds) and a run of weak rival cohorts. That joint
   frequency was not measured and is lower.
2. **Development closes about 25-28 % of the remaining gap each year, whatever the golfer's drawn peak age.** The
   peak age is drawn but only used for aging. So high-potential juniors run about a year ahead of the generator's own
   age curve between 19 and 22. Vaughan runs further ahead because he has a top-decile rate (work ethic 71.8, a
   coach of quality about 0.7).
3. **Dominance comes from the gap between him and No. 2, not from fewer good pros.** His potential is 5.6 points
   above any other junior of the run, and the 2048-2067 cohorts produced no potential ≥ 90 rival. The model puts
   such a drought at P = 19 %, but that is a model figure and does not show the era is realistic.

   The number of pros at Overall ≥ 85 in his era (6.6 a season) matches the earlier eras (6.7, 7.5). Relative to a
   96-97 golfer, though, competition *was* thin: in all 21 seasons of his era no pro was within 3 points of him,
   and in 19 of 21 nobody was within 5.

   **His record:**

   | Event type | Wins / starts | Win rate |
   |---|---|---|
   | All professional events (career) | 123 / 399 | 31 % |
   | Premier Tour (tier-1) events | 89 / 293 | 30 % |
   | Majors | 30 / 100 | 30 % |
   | Majors, 2059-2069 | 18 / 44 | 41 % |

   Wei Fu at his peak (2038-2048) won 15 % of his tier-1 starts and 26 % of his major starts.

**Created Overall vs season-end Overall.** The "89.1 at 18" is the season-end Overall of his first season (after
the winter's aging). His **created (generated) Overall was 85.31**, with potential 97.0116 (shown as 97.1) and peak
age 28.5434. This confirms the reviewer's exact reproduction.

## Data and definitions

- **Season-end Overall** is the debug row of the season (`tools/long_world.py` `year_rows`). It is taken after the
  winter's aging: it equals the development evidence's `overall_after_aging` (Vaughan 2046: 89.08 = OV_POST).
- **Created Overall** is `diagnostics.created[gid].overall` in the archived season file of the arrival year. It is
  the rating at generation, before any week is played. Every created record of run A was read: 38,406, one season
  file at a time, about 370 MB each.
- **Potential** is `g.potential` = ceil(max(drawn pot, attribute Overall)·10)/10, fixed for life
  (`build_473690a/golfsim/population.py:240`). The development cap is the ceilings' Overall, which is 97.03 for
  Vaughan.
- **Procedural** golfers are those who arrived after 2027: 12,982 juniors created at 18 and 18,768 new
  professionals aged 21-26. **Seeded** golfers are the 6,656 golfers present in the 2027 world.

## 1. Frequencies with denominators

### Created (generated) Overall, procedural arrivals (run A)

| Group | Created | Median | Max | >=75 | >=80 | >=85 | >=88 | >=89 | >=90 | >=92 |
|---|---|---|---|---|---|---|---|---|---|---|
| Juniors (created at 18) | 12,982 | 47.2 | **85.31 (Vaughan)** | 22 (0.17%) | 5 (0.04%) | 1 (0.008%) | 0 | 0 | 0 | 0 |
| New professionals (21-26) | 18,768 | 54.9 | 77.02 | 5 (0.03%) | 0 | 0 | 0 | 0 | 0 | 0 |
| Seeded world, aged 18-19 in 2027 | 634 | 47.6 | 73.28 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

**Reviewer cross-check.** All of the reviewer's figures are confirmed:

- 443,652 raw draws (10,083 a cohort × 44 cohorts) and 12,982 kept juniors, from my exact reproduction and from
  the archive's created records.
- 5 juniors created ≥ 80, 1 created ≥ 85, none created ≥ 89.
- Vaughan's draw: created 85.315, potential 97.0116, peak age 28.5434.

### Season-end Overall at exactly 18 and exactly 19

| Group | Age | Recorded (denominator) | Max | >=75 | >=80 | >=85 | >=88 | >=89 | >=90 | >=92 |
|---|---|---|---|---|---|---|---|---|---|---|
| Seeded | 18 | 295 | 74.2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Seeded | 19 | 634 | 76.5 | 2 (0.32%) | 0 | 0 | 0 | 0 | 0 | 0 |
| Procedural | 18 | 12,982 | **89.08** | 44 (0.34%) | 11 (0.08%) | 1 (0.008%) | 1 | 1 | 0 | 0 |
| Procedural | 19 | 12,689 | **92.03** | 84 (0.66%) | 16 (0.13%) | 3 (0.02%) | 1 | 1 | 1 | 1 |

All procedural golfers recorded at 18 or 19 are juniors; new professionals arrive at 21 or older.

### Potential (hidden)

| Group | Golfers | Max | >=85 | >=90 | >=92 | >=95 | >=97 |
|---|---|---|---|---|---|---|---|
| Procedural juniors | 12,982 | 97.1 | 15 (0.12%) | 3 (0.02%) | 1 | 1 | 1 |
| Procedural new professionals | 18,768 | 80.9 | 0 | 0 | 0 | 0 | 0 |
| Seeded world (all ages) | 6,656 | 92.9 (Kincaid, 33 in 2027) | 12 (0.18%) | 1 | 1 | 0 | 0 |
| Seeded world, aged ≤ 22 in 2027 | 1,545 | 86.8 | 1 | 0 | 0 | 0 | 0 |

The new-professional maximum (potential 80.9, created 77.0) is the **observed sample only, not a structural
bound**. The new-professional pathway excludes candidates the junior filter would have kept (`population.py:341-345`).
That filter judges current Overall at 18 plus scouting noise, not potential. A very-high-potential candidate with
an exceptionally late peak, and so a low Overall at 18, can fail it and arrive later as a new professional. At these
potentials it is very rare, but the code does not prohibit it.

**Where Vaughan sits.** He is rank 1 of the procedural juniors on all four measures:

| Measure | Value | Rank | z | Next highest |
|---|---|---|---|---|
| Created Overall | 85.31 | 1 of 12,982 | 3.60 | 84.11 (Parker Walton, potential 86.6) |
| Potential | 97.1 | 1 of 12,982 | 3.94 | 91.5 (Weston Wolfe) |
| Season-end at 18 | 89.08 | 1 of 12,982 | 3.78 | 84.90 (Wei Fu) |
| Season-end at 19 | 92.03 | 1 of 12,689 | 3.91 | 86.74 |

His potential draw is z = 4.75 within England (mu 35.2, P = 9.9e-7 per candidate). His career luck was +2.17
(z +1.08). His peak age of 28.5 is *later* than average (z +0.77), which *lowered* his created Overall by about
3 points compared with a peak at 27.

### By arrival decade (procedural juniors)

| Arrived | Juniors | Max created | Created ≥80 | Max s-e 18 | S-e 18 ≥80 | S-e 18 ≥85 | Recorded at 19 | Max s-e 19 | S-e 19 ≥85 | Max potential | Pot ≥90 | Pot ≥95 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2028-2037 | 2948 | 84.1 | 2 | 84.9 | 5 | 0 | 2948 | 86.7 | 2 | 91.5 | 2 | 0 |
| 2038-2047 | 2957 | 85.3 | 1 | 89.1 | 3 | 1 | 2957 | 92.0 | 1 | 97.1 | 1 | 1 |
| 2048-2057 | 2962 | 80.5 | 1 | 82.5 | 2 | 0 | 2962 | 84.4 | 0 | 88.6 | 0 | 0 |
| 2058-2067 | 2924 | 82.8 | 1 | 83.0 | 1 | 0 | 2924 | 83.2 | 0 | 85.9 | 0 | 0 |
| 2068-2071 | 1191 | 74.3 | 0 | 76.4 | 0 | 0 | 898 | 77.2 | 0 | 87.0 | 0 | 0 |

The decades show no drift. The tail sits in one cohort, and the two decades after Vaughan were unusually thin at
the top.

### Other runs, 10 seasons each

| Run | Seed | Procedural recorded at 18 | Max s-e 18 | ≥80 | ≥85 | At 19 | Max s-e 19 | ≥85 | Procedural | Max potential | ≥90 | ≥95 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B | 2027 | 2628 | 78.2 | 0 | 0 | 2357 | 79.9 | 0 | 6605 | 87.3 | 0 | 0 |
| C | 2027 (same arrivals as B) | 2628 | 77.9 | 0 | 0 | 2356 | 80.3 | 0 | 6605 | 87.3 | 0 | 0 |
| D | 3031 | 2593 | 85.8 | 2 | 1 | 2308 | 81.9 | 0 | 6408 | 92.2 | 1 | 0 |

D's junior with 85.8 at 18 was recorded in the run's last season, so there is no age-19 row for him. The runs are
consistent with run A's rates.

### Expected count implied by the generator, versus observed

The expectations below are analytic, derived from the code in
`build_473690a/golfsim/population.py:38-44, 87-98, 284-310`:

- potential pot ~ N(mu_c, 13), with mu_c = 33 + 0.55·(development − 60) for each nation c;
- created Overall = pot − 0.36·(peak − 18)^1.55 + N(0, 2), with peak ~ N(27, 2);
- each nation draws 900·pool/31.25 candidates a year;
- every candidate at these levels is kept.

For season-end at 18, the first-season share s of the creation gap that closes is taken from run A's evidence:
s = 0.25 is the all-junior median, 0.28 the median for juniors created ≥ 70, and 0.32 is Vaughan's own value.

| Threshold | Expected per cohort | Expected in 44 cohorts | P(at least one in 44) | Observed run A |
|---|---|---|---|---|
| Potential ≥ 90 | 0.084 | 3.68 | 97% | 3 |
| Potential ≥ 95 | 0.014 | 0.61 | 46% | 1 |
| Potential ≥ 97 | 0.0065 | **0.29** | **25%** | 1 |
| Potential ≥ 99 (cap) | 0.0030 | 0.13 | 12% | 0 |
| Created ≥ 80 | 0.138 | 6.05 | 100% | 5 |
| Created ≥ 85.31 | 0.023 | **1.01** | **64%** | 1 |
| Created ≥ 89 | 0.0061 | 0.27 | 23% | 0 |
| Season-end 18 ≥ 85 (s = 0.28) | 0.049 | 2.15 | 88% | 1 |
| Season-end 18 ≥ 89 (s = 0.25 / 0.28 / 0.32) | 0.011-0.013 | 0.48-0.57 | 38-44% | 1 |

Seeded world (315,000 candidates of all ages): expected potential ≥ 90 is 2.62 (observed 1) and ≥ 97 is 0.20,
mostly among older golfers. For ages ≤ 22 the expected count at ≥ 97 is only about 0.03.

USA supplies 39 % of the expected potential ≥ 95 juniors and England 10 %. An English superstar is not
surprising.

**Pure-generator sample.** 100 other seeds × 44 cohorts, about 1.31 M kept juniors, 92 s. This uses the verbatim
draw loop of the pinned `junior_class`.

| Measure | Worlds (of 100) |
|---|---|
| A junior with potential ≥ 95 | 42 |
| A junior with potential ≥ 97 (Vaughan's 97.1 or higher) | 31 |
| Best potential at the 99 cap | 14 |
| Max-to-second potential gap ≥ 5.6 (Vaughan 97.1 vs 91.5) | **11** (all among worlds whose best is ≥ 95) |
| A junior created ≥ 85.3 | 66 |
| Estimated season-end at 18 ≥ 89.1 (s = 0.28) | 37 |

The median best potential per world is 94.2 (range 89.0-99.0), and the median gap from best to second is 1.9.
Some sampled worlds have created Overall 90-92 at 18. Vaughan is not even at the generator's extreme.

**Section 1 conclusion.** The created 85.3 is about what one 44-cohort world produces (expected 1.0). A
potential-97.1 junior is about a 1-in-4 world event. That is the chance of the *junior*, not of his 30-major,
25-season career. A gap of 5.6 or more to the next junior is about a 1-in-9 world event. The joint frequency of
the whole phenotype was not measured. The observed
tail rates of run A (3 juniors ≥ 90 against 3.68 expected, 15 ≥ 85 against 19.3) are, if anything, slightly
*below* expectation. The tail is not fatter than the code specifies.

## 2. Development path

### Vaughan, season by season

Values are from the debug rows and the development evidence. The evidence holds ages 18-26 (`extract_A.py`
keeps them); later seasons show "—".

| Season | Age | Season-end Overall | Potential | Mean attribute gap | Overall moved by source: maturing / training / tournaments / injury / aging | Status | Tier | Events | Wins | Majors | World rank |
|---|---|---|---|---|---|---|---|---|---|---|---|
| created | 18 | **85.31** | 97.1 (ceilings 97.03; 12 of 21 attribute ceilings at 99) | — | — | amateur | — | — | — | — | — |
| 2046 | 18 | 89.08 | 97.1 | 8.04 | +0.59 / +2.11 / +1.04 / 0 / +0.04 | amateur | 6 | 18 | 5 | 0 | 1030 |
| 2047 | 19 | 92.03 | 97.1 | 5.13 | +0.38 / +1.25 / +1.28 / 0 / +0.05 | pro | 2 | 24 | 6 | 1 | 3 |
| 2048 | 20 | 93.78 | 97.1 | 3.32 | +0.23 / +0.87 / +0.61 / 0 / +0.04 | pro | 1 | 17 | 5 | 1 | 2 |
| 2049 | 21 | 94.91 | 97.1 | 2.17 | +0.16 / +0.51 / +0.42 / 0 / +0.03 | pro | 1 | 19 | 3 | 0 | 1 |
| 2050 | 22 | 95.65 | 97.1 | 1.44 | +0.10 / +0.38 / +0.23 / 0 / +0.03 | pro | 1 | 18 | 4 | 0 | 1 |
| 2051 | 23 | 96.04 | 97.1 | 1.01 | 0 / +0.21 / +0.14 / 0 / +0.03 | pro | 1 | 17 | 7 | 2 | 1 |
| 2052 | 24 | 96.29 | 97.1 | 0.74 | 0 / +0.13 / +0.09 / 0 / +0.03 | pro | 1 | 17 | 6 | 1 | 1 |
| 2054 | 26 | 96.54 | 97.1 | 0.47 | 0 / +0.07 / +0.04 / 0 / 0 | pro | 1 | 17 | 5 | 1 | 1 |
| 2058 | 30 | 96.74 (peak) | 97.1 | 0.27 | — | pro | 1 | 16 | 8 | 0 | 1 |
| 2064 | 36 | 96.06 | 97.1 | 0.18 | — | pro | 1 | 16 | 6 | 3 | 1 |
| 2071 | 43 | 92.33 | 97.1 | 0.14 | — | pro | 1 | 13 | 2 | 0 | 1 |

`analyze_A.out.md` has every season. Wins include amateur and lower-tier events.

His peak stays at 96.74, below the ceilings' 97.03, and decline starts at about 31. That matches his peak age of
28.5 plus 3 years for physical decline (`development.py:300-305`, aging rate 0.93). **Growth never exceeds the
ceiling, and potential is never raised.**

### Created 85.3 to season-end 89.1 in one season: typical for potential about 97?

Yes, within the development rules. Growth is proportional to the gap (`development.py:151-185`), so the absolute
gain scales with the gap.

| Gap at creation | Juniors | Median first-season change | 90th pct change | Median share of gap closed | 90th pct share |
|---|---|---|---|---|---|
| 0-4 | 1201 | +0.69 | +1.00 | 26% | 32% |
| 4-8 | 4140 | +1.54 | +2.05 | 25% | 30% |
| 8-10 | 2550 | +2.23 | +2.76 | 25% | 30% |
| 10-12 | 2238 | +2.71 | +3.32 | 25% | 30% |
| 12-15 | 1929 | +3.28 | +4.02 | 25% | 30% |
| 15-40 | 924 | +4.08 | +5.21 | 25% | 30% |

- Juniors created ≥ 70 (n = 117) closed a median 28 % of the gap in their first season (10th-90th percentile
  23-32 %). Juniors created ≥ 75 (n = 22) closed 28 % (22-33 %).
- **Vaughan closed 32 %: +3.77 on a gap of 11.8.** Wei Fu and Reid Parker also closed 32 % (+2.88 on 9.1 and
  +2.89 on 9.0).
- Vaughan's sources of growth were maturing +0.59, training +2.11 (32 training weeks, all coached, coach quality
  0.66) and tournaments +1.04 (18 events). For juniors with a gap of 10-14 (n = 3,703) the median sources were
  +0.51 / +1.55 / +0.77.

Top 12 created juniors and their first season:

| Golfer | Nation | Arrived | Created | Potential | Gap | S-e 18 | Change | Share closed | S-e 19 | Peak |
|---|---|---|---|---|---|---|---|---|---|---|
| Rupert Vaughan | England | 2046 | 85.31 | 97.1 | 11.8 | 89.08 | +3.77 | 32% | 92.03 | 96.7 |
| Parker Walton | USA | 2035 | 84.11 | 86.6 | 2.5 | 84.79 | +0.68 | 27% | 85.33 | 86.8 |
| Mason Coburn | Australia | 2067 | 82.80 | 83.4 | 0.6 | 83.00 | +0.20 | 33% | 83.15 | 83.5 |
| Wei Fu | China | 2034 | 82.02 | 91.1 | 9.1 | 84.90 | +2.88 | 32% | 86.74 | 91.1 |
| Benedict Chapman | South Africa | 2056 | 80.49 | 88.3 | 7.8 | 82.26 | +1.77 | 23% | 84.05 | 88.0 |
| Reid Parker | USA | 2053 | 79.59 | 88.6 | 9.0 | 82.48 | +2.89 | 32% | 84.41 | 88.7 |
| Reid Martin | USA | 2043 | 79.24 | 82.4 | 3.2 | 80.16 | +0.92 | 29% | 80.76 | 82.4 |
| Lucas Holm | Denmark | 2030 | 79.01 | 84.1 | 5.1 | 80.60 | +1.59 | 31% | 81.60 | 83.9 |
| Ryan Goodwin | USA | 2047 | 78.38 | 83.8 | 5.4 | 79.85 | +1.47 | 27% | 80.88 | 83.8 |
| William Malone | USA | 2037 | 77.99 | 83.1 | 5.1 | 79.32 | +1.33 | 26% | 80.38 | 83.2 |
| Genki Ueda | Japan | 2042 | 77.62 | 87.1 | 9.5 | 80.43 | +2.81 | 30% | 82.27 | 87.2 |
| Terrell Stroud | USA | 2058 | 77.38 | 83.9 | 6.5 | 79.20 | +1.82 | 28% | 80.48 | 83.8 |

### Growth curves: Vaughan vs high-potential juniors

The comparison group is the 14 procedural juniors with potential ≥ 85, other than Vaughan.

| Age | Vaughan share of remaining gap closed | Vaughan training wks / coached wks / coach quality / events | Pot ≥ 85: median share closed (p10-p90) | Their median training wks / coached wks / events | All juniors median |
|---|---|---|---|---|---|
| 18 | 32% | 32 / 32 / 0.66 / 18 | 27% (21-32%) | 30 / 30 / 20 | 25% |
| 19 | 37% | 25 / 25 / 0.68 / 24 | 27% (23-30%) | 31 / 31 / 18 | 24% |
| 20 | 35% | 33 / 33 / 0.70 / 17 | 27% (23-30%) | 31 / 31 / 18 | 24% |
| 21 | 34% | 29 / 29 / 0.69 / 19 | 26% (23-30%) | 35 / 35 / 15 | 24% |
| 22 | 34% | 32 / 32 / 0.82 / 18 | 25% (20-33%) | 37 / 37 / 14 | 23% |
| 23 | 27% | 33 / 33 / 0.75 / 17 | 25% (19-37%) | 25 / 25 / 23 | 10% |

**Why he is faster from 19 to 22.** Vaughan closes 34-37 % a year at 19-22, above the comparison group's 90th
percentile. The archive does not keep personality, so I re-derived it: the generator draws it from
`Random('360013:j2046:golfer:23546')` before the name (`population.py:229-235`). That reproduces his attribute
Overall of 85.309 exactly. His **work ethic is 71.8** (z ≈ +1.6 against the mean of 50), so his learning multiplier
(0.5 + work ethic/100, at `development.py:161`) is **1.22**. His coachability of 52.9 gives a training multiplier of
1.02. With a coach of quality about 0.7, `coach_multiplier` (`development.py:126-132`) is about 1.2. Together these
explain a rate about 30 % above the median. That is a top-decile draw, inside the rules.

### Generator age curve vs development

This is the early-maturation question.

| Season-end age | Vaughan actual | Generator curve for him, no luck | With his luck (+2.17) | Actual − curve (no luck / luck) | Pot ≥ 85 juniors: share of creation gap left | Generator ratio age_deficit(a+1, 27) / age_deficit(18, 27) |
|---|---|---|---|---|---|---|
| 18 | 89.08 | 85.13 | 87.30 | +3.95 / +1.78 | 73% | 83% |
| 19 | 92.03 | 87.00 | 89.17 | +5.03 / +2.86 | 54% | 68% |
| 20 | 93.78 | 88.76 | 90.93 | +5.02 / +2.85 | 39% | 53% |
| 21 | 94.91 | 90.39 | 92.56 | +4.52 / +2.35 | 29% | 40% |
| 22 | 95.65 | 91.89 | 94.06 | +3.76 / +1.59 | 21% | 28% |
| 23 | 96.04 | 93.25 | 95.42 | +2.79 / +0.62 | 16% | 18% |
| 24 | 96.29 | 94.45 | 96.62 | +1.84 / −0.33 | 11% | 10% |
| 26 | 96.54 | 96.31 | 98.47 | +0.23 / −1.93 | 7% | 0% |

The "generator curve" is the Overall the pinned generator would give this same golfer at that age
(`population.py:87-98`, `age_deficit(age, 28.54, 0.93)`). For high-potential juniors the gap left at
season-end 19-21 is about 0.7-0.75 of what the generator's own curve leaves (54/68, 39/53, 29/40), about one year
ahead.

**Section 2 finding.** The model has a mild, model-wide early-maturation inconsistency.

- Development closes a roughly constant 25-28 % of the gap each year from age 18 (`learning_rate`, 1.2 at 18-21,
  `development.py:98-105`). Growth never reads `peak_age`. The peak age only enters the generator's created Overall
  and `age_year` decline.
- So juniors run about one year ahead of the generator's age curve from 19 to 22, then approach the ceiling slowly
  (7 % of the gap is still open at 26, where the generator expects 0).
- For Vaughan this is amplified: his peak age of 28.5 *should* make him a late maturer, but development ignores
  it, and his work ethic and coaching add about 30 %. He runs 3-5 points above the generator's curve at 19-22.
- This is what produced "92 at 19, 95 at 21". It does not change his peak (96.7 ≤ ceiling 97.03) or his potential.

Nothing is broken:

- The starting Overall is not set too close to potential: the created gap of 11.8 is larger than the generator's
  10.85 for a peak at 27.
- `init_ceilings` keeps the ceilings' Overall at potential: 97.03 against 97.01 drawn.
- Mental maturing in `age_year` (`development.py:308-321`) raises ceilings by only about 0.04 Overall a year.
  Vaughan's ceilings Overall stayed at 97.03 through age 26.
- No nation-share or rare-nation effect is involved. The pinned build has no shares, and England is a big,
  high-development nation that supplies about 10 % of the expected elite juniors.

## 3. Elite competitive depth (run A)

Per season, among active professionals ranked by season-end Overall. The full table is in `depth_A.out.md`.

**Labelling note.** The "tier-1 wins / all" columns below divide the top golfer's wins by **all tier-1 events
played**: the 36 Premier Tour events of a season, majors excluded (`wins_by_tier[1]`). They are *not* his win rate
per start. His actual starts and win rates are in the record tables further down.

Selected seasons:

| Season | Pros ≥85 | Pros ≥90 | Top Overall | No.2 | No.10 | Gap 1-2 | Gap 1-10 | Top golfer's majors | Top golfer's tier-1 wins / all tier-1 events played |
|---|---|---|---|---|---|---|---|---|---|
| 2027 | 8 | 1 | 92.3 Kincaid | 89.4 Haskins | 84.9 | 2.9 | 7.4 | 0 | 5/36 |
| 2032 | 7 | 0 | 88.8 Mthembu | 88.7 | 83.4 | 0.1 | 5.4 | 0 | 0/36 |
| 2038 | 4 | 0 | 88.2 Mthembu | 87.3 | 83.5 | 0.9 | 4.7 | 0 | 0/36 |
| 2042 | 9 | 1 | 90.7 Wei Fu | 88.6 Wolfe | 84.9 | 2.1 | 5.8 | 1 | 1/36 |
| 2046 | 7 | 2 | 91.1 Wei Fu | 90.2 Wolfe | 83.7 | 0.9 | 7.4 | 1 | 0/36 |
| 2047 | 9 | 3 | 92.0 Vaughan | 91.1 Wei Fu | 84.5 | 0.9 | 7.5 | 1 | 1/36 |
| 2049 | 9 | 3 | 94.9 Vaughan | 91.0 Wei Fu | 84.8 | 4.0 | 10.1 | 0 | 3/36 |
| 2053 | 8 | 2 | 96.4 Vaughan | 90.7 Wolfe | 84.1 | 5.7 | 12.3 | 2 | 3/36 |
| 2058 | 8 | 1 | 96.7 Vaughan | 89.4 Healy | 84.0 | 7.3 | 12.7 | 0 | 8/36 |
| 2062 | 5 | 1 | 96.4 Vaughan | 88.7 Healy | 84.0 | 7.7 | 12.5 | 1 | 3/36 |
| 2066 | 5 | 1 | 95.3 Vaughan | 88.4 Parker | 83.0 | 6.9 | 12.4 | 0 | 1/36 |
| 2071 | 4 | 1 | 92.3 Vaughan (age 43) | 87.6 Chapman | 82.8 | 4.8 | 9.6 | 0 | 2/36 |

### Eras

| Era | Seasons | Mean pros ≥85 | Mean pros ≥90 | Mean top Overall | Mean gap 1-2 | Mean gap 1-10 | Top golfer's share of all majors played | Top golfer's share of all tier-1 events played |
|---|---|---|---|---|---|---|---|---|
| Seeded stars (Beaumont, Haskins, Kincaid) | 2027-2037 | 6.7 | 0.3 | 89.6 | 1.05 | 5.94 | 2% | 4% |
| Wei Fu | 2038-2048 | 7.5 | 1.4 | 90.9 | 1.76 | 6.61 | 25% | 5% |
| Vaughan | 2049-2069 | 6.6 | 1.6 | 96.0 | **6.50** | **12.11** | 33% | 10% |
| End of the run | 2066-2071 | 4.7 | 1.0 | 93.9 | 5.94 | 11.00 | 25% | 8% |

Rolling 5-season windows, as shares of **all events played**:

- Wei Fu peaked at 6 of 20 majors (30 %) and at most 6 % of all tier-1 events played.
- Vaughan held 4-9 of 20 majors (20-45 %, peak 2060-2064 and 2064-2068) and 8-13 % of all tier-1 events played
  (peak 23 of 180 in 2056-2060 and 2057-2061).
- During his windows the mean gap from No. 1 to No. 2 was 5-7.5 points; in all earlier windows it was 0.4-2.3.

### Actual record: starts, wins and win rate

Taken from the archived event results of every season (`record_A.py`). Professional events are those of kind
pro, premier and major. Tier-1 means the Premier Tour events, majors excluded. A win is position 1. All 180 major
winners agree with the run data.

| Span | Golfer | Professional wins / starts | Tier-1 wins / starts | Major wins / starts |
|---|---|---|---|---|
| Career 2046-2071 | **Rupert Vaughan** | 123/399 (31%) | 89/293 (30%) | **30/100 (30%)** |
| Career 2035-2071 | Wei Fu | 52/553 (9%) | 36/416 (9%) | 16/137 (12%) |
| Career 2041-2069 | Weston Wolfe | 48/549 (9%) | 37/418 (9%) | 6/112 (5%) |
| Career 2040-2069 | Taj Healy | 51/441 (12%) | 41/336 (12%) | 9/98 (9%) |
| Career 2027-2036 | Carson Kincaid (seeded) | 18/187 (10%) | 16/147 (11%) | 2/40 (5%) |
| Career 2027-2044 | Colby Haskins (seeded) | 31/319 (10%) | 25/248 (10%) | 6/71 (8%) |
| Career 2027-2043 | Romain Beaumont (seeded) | 19/308 (6%) | 11/240 (5%) | 8/68 (12%) |
| 2038-2048 (his era) | Wei Fu | 31/180 (17%) | 20/137 (15%) | 11/43 (26%) |
| 2047-2048 (ages 19-20) | Vaughan | 11/41 (27%) | 5/28 (18%) | 2/7 (29%) |
| 2049-2069 (his era) | Vaughan | 107/330 (32%) | 79/246 (32%) | 28/84 (33%) |
| 2049-2058 | Vaughan | 51/168 (30%) | 41/128 (32%) | 10/40 (25%) |
| 2059-2069 | Vaughan | 56/162 (35%) | 38/118 (32%) | 18/44 (41%) |
| 2066-2071 (ages 38-43) | Vaughan | 24/84 (29%) | 18/60 (30%) | 6/24 (25%) |

- In rolling 5-season windows Vaughan won 24-40 % of his tier-1 starts and 20-45 % of his major starts. The peak
  was 23/57-58 tier-1 (40 %) in 2056-2061 and 9/20 majors in 2060-2064 and 2064-2068.
- He plays about 10-13 tier-1 events and 4 majors a season.
- **The rule-of-thumb win shares of about 10-13 % (of all tier-1 events played) understate his per-start
  dominance.** Per start he wins about 3 times as often as Wei Fu or the seeded stars at their best (about 30 %
  against 9-15 %).

### Competition close to No. 1

Active professionals other than the top-Overall pro, within a given number of points of the top season-end Overall
(`depth_close.py`):

| Era | Seasons | Mean top Overall | Mean pros within 3 of No.1 | Within 5 | Within 8 | Seasons with nobody within 3 | Seasons with nobody within 5 | Mean pros ≥ 88 |
|---|---|---|---|---|---|---|---|---|
| Seeded stars | 2027-2037 | 89.6 | 3.5 | 6.5 | 19.0 | 0 of 11 | 0 of 11 | 2.5 |
| Wei Fu | 2038-2048 | 90.9 | 1.3 | 4.4 | 14.3 | 0 of 11 | 0 of 11 | 2.0 |
| Vaughan | 2049-2069 | 96.0 | **0.0** | **0.2** | 2.3 | **21 of 21** | **19 of 21** | 3.3 |
| End of run | 2066-2071 | 93.9 | 0.0 | 0.2 | 2.7 | 6 of 6 | 5 of 6 | 1.8 |

Stars:

| Golfer | Potential | Peak | Seasons as top-Overall pro | Majors | Tier-1 wins | Best season gap over No. 2 |
|---|---|---|---|---|---|---|
| Rupert Vaughan | 97.1 | 96.7 | 25 | 30 | 89 | 7.7 |
| Wei Fu | 91.1 | 91.1 | 8 | 16 | 36 | 2.8 |
| Carson Kincaid (seeded) | 92.9 | 92.3 | 4 | 2 | 16 | 2.9 |
| Colby Haskins (seeded) | 89.5 | 89.4 | 1 | 6 | 25 | 0.2 |

The top-Overall golfer's share of all tier-1 events played (not per start) rises with his gap over No. 2: 2 % at a
gap of 0-1 (11 seasons), 6 % at 1-2 (4 seasons), 8 % at 2-3 (7 seasons) and 8 % at 3-5 (3 seasons). At a gap of
5-7.7 it is about 10-13 %, which is Vaughan alone.

**Is dominance a consequence of thin depth at the top?** It depends on what "depth" means.

- **Measured by an absolute level, depth was not thinner.** His era had 6.6 pros ≥ 85, 1.6 ≥ 90 and a No. 10 of
  about 84, the same as the earlier eras.
- **Measured relative to him, competition was very thin.** No pro was within 3 points of him in any of the 21
  seasons, and nobody was within 5 in 19 of them. Earlier eras always had someone within 3: 3.5 pros a season in the
  seeded era, 1.3 in Wei Fu's. The 6.5-point gap from No. 1 to No. 2 (against 1-1.8 before) means the unchanged
  count at ≥ 85 does **not** rule out thin competition for a 96.7 golfer.
- **Where the gap comes from:** his own potential, 5.6 points above anyone else's, plus a drought of rivals. The 20
  cohorts from 2048 to 2067 produced no junior with potential ≥ 90 (1.67 expected). The model gives P = 19 % for no
  such junior in 20 *fixed* cohorts. This is a model-based figure for a window chosen after seeing it, so it is no
  independent evidence that this era is realistic.
- Depth also thins at the end of the run (4-5 pros ≥ 85 in 2066-2071). This is why he is still No. 1 at 43 with
  92.3. The seeded era showed a similar dip (4 pros ≥ 85 in 2038).
- **Per start he is dominant:** 30 % of tier-1 starts and 30 % of major starts (41 % of major starts in 2059-2069),
  against Wei Fu's 15 % and 26 % at his peak. The 30 majors come from about 4 major starts a season over 25 seasons
  at a 30 % win rate. Whether a 5-7.7-point Overall lead *should* convert into about a 30 % win rate per start is an
  engine/outcome calibration question this diagnosis did not assess.

## 4. Pinned (473690a) vs candidate (0a05310)

**Unchanged.** `golfsim/development.py` is byte-identical (`cmp`), and `golfer.py`, `ratings.py` and `nations.py`
are unchanged. Growth, ceilings, learning rate, maturing and aging are therefore unchanged.

**The junior draw itself is unchanged.** The candidate's `_junior_draw`
(`wt_final/golfsim/population.py:328-341`) is the pinned `junior_class` loop body (`build_473690a/...:292-302`). It
uses the same random stream (`{seed}:juniors:{year}:{country}`, `_Stream` at `:364-383`), the same constants and
the same `_keep_young` filter. The same holds for `_new_pro_draw` (`:343-361`) against the pinned `:336-351`.

**What changed is how many juniors come from each nation** (rules 2026-11-05):

- `entrant_rows` (`:414-448`) fixes the cohort's total from the existing rule.
- `allocate` (`:395-406`) splits that total by shares. Each share is the nation's expected share (`expected_shares`
  `:566`, computed from `pass_chance` `:545-558`) times its prestige multiplier (`participation.py:143-146`). The
  multiplier is bounded to 0.25-4 (`:53`) and moves at most ×1.10 a year (`:54`).
- Each nation then takes the first k passers of its own stream (`:444`). If it needs more, the stream simply
  continues: this is the no-cap loop (`:440-443`).

Wiring is in `wt_final/golfsim/careers.py:570-574` (`_cohort_args`), `:577-606` (`add_new_professionals`) and
`:608-626` (`add_juniors`).

| Effect on Vaughan-class frequency | Expected potential ≥ 90 in 44 cohorts | ≥ 95 | ≥ 97 | P(≥1 at ≥97) | England share |
|---|---|---|---|---|---|
| Baseline shares (= pinned existing rule) | 3.68 | 0.61 | 0.288 | 25% | 7.7% |
| England ×2 (sustained prestige 75) | 3.75 | 0.62 | 0.293 | 25% | 14.2% |
| England ×4 (its long-run maximum, e.g. after a Vaughan era) | 3.85 | 0.64 | 0.302 | 26% | 24.9% |
| USA ×4 | 3.98 | 0.67 | 0.313 | 27% | 3.8% |
| Extreme: the 10 highest-development nations ×4, the rest ×0.25 | 4.44 | 0.75 | 0.355 | 30% | 13.2% |
| Extreme reverse | 2.77 | 0.45 | 0.206 | 19% | 1.0% |

1. **Nation shares can change the frequency only slightly.** A share changes how many golfers a nation sends,
   never their talent. A nation's chance of an elite junior per passer varies little among the nations that
   matter: potential ≥ 95 per 1,000 passers is 0.09 for Denmark, 0.06 for England and 0.05 for the world average.
   Even the extreme bounds move the 44-cohort chance of a potential ≥ 97 junior only from 25 % to 19-30 %.

   Prestige can feed back: a dominant English star raises England's share. That gives more English juniors, but not
   more superstars per junior, so there is **no runaway superstar loop**. The realistic effect is +2-5 % in
   frequency.
2. **The no-cap stream has no effect on the talent distribution.** It only continues the same independent stream
   until the quota is met (`:284-309` block comment, step 5). It changes behaviour only where the pinned code would
   have raised RuntimeError.
3. **Reproducibility.** Even at starting shares (every multiplier 1), the candidate's allocation differs from the
   existing rule's realized counts: in 2046, 33 nations differ, Σ|difference| = 56 (`vaughan_candidate.out.md`).
   So a candidate world with seed 360013 will not reproduce run A's cohorts. The test case is:
   - **Vaughan himself survives at starting shares**: he is England passer #18 of 20, and England's allocation is
     24.
   - He also survives at multipliers down to about 0.75, but not at 0.5 (allocation 13).
   - In any case the *frequency* of such golfers is what matters, and it is essentially unchanged.
4. **Other candidate changes do not touch arrival creation.**
   - Weather (`weather.py`), course familiarity (`familiarity.py`) and the playoff/match-play conditions in
     `tournament.py` change results variance. They could slightly change how a 7-point gap converts into wins;
     this was not measured.
   - The staff and recruitment changes (`staff.py`) can change which juniors get strong coaches. That moves the
     growth speed by at most the coach multiplier (1.0-1.35, `development.py:126-132`), never the ceiling.
   - Upsets (`upsets.py`) are an observer-side estimate that uses no random numbers.

## 5. Verdict and what would settle it

**Verdict: a rare outlier that the model's rules produce. No defect was found in these checks. Calibration is not
validated, because there are no agreed target frequencies to validate it against.**

- His created Overall of 85.3 matches what one 44-cohort world produces (expected 1.01).
- A potential-97+ junior occurs in 25-31 % of 44-cohort worlds. That is the chance of the junior, not of the full
  Vaughan phenotype (97+ potential, 30 majors, about 25 seasons as the top-rated pro). The phenotype's frequency was
  not measured and is lower.
- His first-season +3.77 (32 % of the gap) and his later 34-37 % a year are upper-decile but explained by work
  ethic 71.8 and coaching.
- His era's dominance comes from a 5.6-point potential lead plus a rival drought. The drought's P ≈ 19 % is a model
  figure for a window chosen after the fact. Measured by an absolute level (pros ≥ 85), elite depth was unchanged.
  Relative to him, competition was thin: nobody within 3 points in 21 of 21 seasons, and nobody within 5 in 19 of
  21. Per start he won 30 % of tier-1 events and 30 % of majors.

The corrections above (phenotype vs junior frequency, per-start record, thinness relative to No. 1, the model-based
drought figure, new-professional maximum as an observation) **do not reverse the rarity result**.

**Recommendation (agreed with the independent calibration review): no tuning now.**

- Keep organic extreme potential for the next test.
- Treat maturation timing as a specific design consideration for the next playthrough, not a proven bug: growth does
  not read the drawn peak age (property (b) below).

Two **calibration properties** to keep in view. Both are design choices with documented effects, not bugs:

- **(a) Potential tail and the 99 cap.** POTENTIAL_SD = 13 around mu ≈ 35 for about 10k juniors a year puts a
  potential ≥ 97 junior in about a quarter of 45-year worlds, and a capped 99 in about 1 in 8. Some worlds create
  juniors at Overall 90-92. If "about 89 at 18" should be essentially impossible, the lever is the tail (for example
  a compression above about 90 or a lower cap), not development.
- **(b) Growth ignores `peak_age`.** Juniors mature about one year ahead of the generator's own curve at 19-22, and
  fast learners 2-3 years ahead. Late-peak golfers like Vaughan (28.5) do not mature late. This is model-wide and
  mild. Making the learning rate depend on age relative to `peak_age` would align the two.

Not covered by these checks:

- The personality and coach effect on his growth rate is inferred from a re-derived personality (exact attribute
  Overall match) and the recorded coaching quality. The archive does not keep personality.
- The outcome side was not assessed: whether a 5-7.7-point Overall lead should win about 30 % of starts.
- The joint frequency of the full phenotype (junior, lead and rival drought, career) was not measured.

**What would settle it.** None of these need full seasons.

1. **Generator-only study, done here in miniature** (100 worlds × 44 cohorts, 92 s). Scale it to about
   2,000 worlds using the candidate's `entrant_rows` at starting shares and at stress multipliers.
   - Report: the distribution of the best potential, the best created Overall, the best-to-second gap among juniors
     born within ±6 years of each other, and the share of worlds with potential ≥ 97 or a gap ≥ 5.
   - The owner then sets a target, for example "a Vaughan-class player in ≤ 10 % of 45-year worlds", and the tail
     parameters are judged against it.
2. **Development-only replay.** Take the created records (attributes, ceilings, personality) of the top juniors from
   the sampled worlds. Apply `develop_week` and `age_year` offline with run A's median weekly schedule by age (about
   30 training weeks with a coach of quality about 0.65, about 18 events). Vary work ethic, coachability and coach
   quality.
   - This gives the season-end distribution at 18-22 for a given created Overall and potential. It would confirm
     that 32-37 % a year is the upper decile and quantify (b), with and without a `peak_age`-relative learning rate.
3. **Outcome check** (optional, small). From existing run data only, map each top golfer's win rate per start
   (tier-1 and majors) against his Overall gap over No. 2 across all saved runs. That would judge whether about 30 %
   per start at a 5-7.7-point gap is the intended conversion.

## Scripts and outputs

All scripts are in `/tmp/claude-0/-home-user-golf-legacy/dd633163-5093-57b8-a35e-3e668bc4257e/scratchpad/v18/calib/`
and were run with `nice -n 19`. They read only the run folders and the two checkouts.

| Script | Purpose | Output |
|---|---|---|
| `extract_A.py` | Builds the compact run-A dataset: rows trimmed to 7 columns, debug rows via `long_world.load_debug`, every archived season's `diagnostics.created` and development evidence for procedural golfers ≤ 26, one file at a time (about 100 s, RSS about 1 GB) | `A_compact.pkl.gz` |
| `peek_season.py`, `probe_A.py` | Structure checks of one season file and of Vaughan's rows | stdout |
| `analyze_A.py` | Frequencies at 18/19, created distribution, potentials, ranks and z, by decade, growth curves, Vaughan by season | `analyze_A.out.md` |
| `growth_rates.py` | Annual share of the remaining gap closed, training and coached weeks | `growth_rates.out.md` |
| `gen_curve_vs_actual.py` | Vaughan vs the generator's age curve | `gen_curve_vs_actual.out.md` |
| `vaughan_personality.py` | Re-derives his generated personality (work ethic 71.8, coachability 52.9) | `vaughan_personality.out.md` |
| `depth_A.py` | Elite depth per season, rolling 5-season dominance, eras | `depth_A.out.md` |
| `record_A.py` | Starts, wins and win rates (professional, tier-1, majors) from the archived event results; major winners cross-checked (180/180) | `record_A.out.md` |
| `depth_close.py` | Pros within 3 / 5 / 8 points of No. 1, per season and by era | `depth_close.out.md` |
| `bcd_freq.py` | Runs B, C, D frequencies | `bcd_freq.out.md` |
| `gen_expect.py` | Analytic expectations, exact reproduction of seed 360013's 44 cohorts, pure-generator sample of 100 worlds (pinned code) | `gen_expect.out.md` |
| `shares_effect.py` | Candidate nation-share effect on the elite tail (candidate `pass_chance`/`expected_shares`) | `shares_effect.out.md` |
| `vaughan_candidate.py` | Whether Vaughan's draw survives the candidate's allocation | `vaughan_candidate.out.md` |
