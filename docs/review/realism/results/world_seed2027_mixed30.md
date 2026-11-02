**Mixed-version comparison, labelled.** Branch arm: realism `d619dd6` for 2027-2048, then realism + engine fix `c528575` for 2049-2056 (resumed from the verified 2048 checkpoint; one restart from the 2053 checkpoint after an out-of-memory kill; results/runaway_2049/PROVENANCE_mixed.json). Main arm: `18a8e23` without the fix for all 30 seasons. From 2049 the arms differ in the engine fix as well as the realism rules, so seasons 2049-2056 are not a single-version causal comparison; the 22-season tables (world_seed2027_s22.md) are the primary comparison. The branch season-time line below is not comparable: its log covers only the continuation, across a restart (cumulative times reset) and on 1 worker after it.

Seed 2027, full scale. Both arms compared on the identical covered seasons 2027-2056 (30). Ratings are recorded after the season and its winter; ages are the age in the completed season (season minus birth year). A golfer's "highest observed" rating is the highest such record, not a complete-career peak; careers still running at the end are censored. One paired world: counts are descriptive, not rates.

### Stock of golfers at 80+ / 85+ / 90+ Overall in each season's snapshot (not eventual supply; a snapshot may include golfers who retire that winter)

| season | main (dev-1) | branch (dev-2) |
|---|---|---|
| 2031 | 40/10/0 | 38/9/0 |
| 2036 | 39/5/1 | 35/5/1 |
| 2041 | 46/11/0 | 44/12/0 |
| 2046 | 48/15/1 | 45/14/2 |
| 2051 | 46/15/2 | 43/13/2 |
| 2056 | 46/12/1 | 41/11/1 |

### Juniors arriving from the second season: first observed rating and highest observed rating SO FAR (censored: the latest classes are early in their careers; the first record is after their first season and winter, not their entry rating)

| arm | juniors | mean first observed | first observed 75+ | 80+ | 85+ | largest first observed | highest observed 75+ | 80+ | 85+ | 90+ |
|---|---|---|---|---|---|---|---|---|---|---|
| main (dev-1) | 8549 | 49.01 | 45 | 8 | 1 | 86.10 | 165 | 63 | 15 | 2 |
| branch (dev-2) | 8549 | 48.76 | 39 | 8 | 1 | 85.44 | 167 | 62 | 14 | 2 |

### Top of the world by Overall (season-end averages)

| arm | seasons | top-20 mean age | top-50 mean age | top-50 aged 40+ | 45+ | best Overall |
|---|---|---|---|---|---|---|
| main (dev-1) | all | 30.67 | 30.59 | 4.53 | 1.07 | 90.16 |
| main (dev-1) | last 10 | 31.64 | 31.13 | 4.90 | 1.30 | 91.12 |
| branch (dev-2) | all | 30.40 | 30.42 | 4.30 | 1.00 | 90.48 |
| branch (dev-2) | last 10 | 31.36 | 30.98 | 5.20 | 1.50 | 91.78 |

### Wins by age (season snapshots) and majors by age (the majors' winner ledger)


all wins (snapshots):

| arm | <25 | 25-29 | 30-34 | 35-39 | 40-44 | 45-49 | 50+ | share 40+ |
|---|---|---|---|---|---|---|---|---|
| main (dev-1) | 14104 | 10449 | 8472 | 5800 | 2853 | 1146 | 418 | 10.2% |
| branch (dev-2) | 14540 | 10803 | 8688 | 5662 | 2468 | 816 | 265 | 8.2% |

Premier wins (snapshots):

| arm | <25 | 25-29 | 30-34 | 35-39 | 40-44 | 45-49 | 50+ | share 40+ |
|---|---|---|---|---|---|---|---|---|
| main (dev-1) | 111 | 275 | 325 | 249 | 96 | 21 | 3 | 11.1% |
| branch (dev-2) | 135 | 300 | 308 | 225 | 94 | 14 | 4 | 10.4% |

majors (winner ledger):

| arm | <25 | 25-29 | 30-34 | 35-39 | 40-44 | 45-49 | 50+ | share 40+ |
|---|---|---|---|---|---|---|---|---|
| main (dev-1) | 14 | 29 | 40 | 24 | 9 | 3 | 1 | 10.8% |
| branch (dev-2) | 15 | 30 | 32 | 32 | 8 | 2 | 1 | 9.2% |
- main (dev-1): majors in the ledger 120, counted in season snapshots 120 (reconciled)
- branch (dev-2): majors in the ledger 120, counted in season snapshots 120 (reconciled)

### Careers observed from 28 or younger to 38 or older (highest observed 70+): age at the highest observed rating, and the rating at 40 and 45 relative to it; last observed age at 85+ (censored at the run's end)

| arm | n | age at highest observed: median (p10-p90) | at 40 vs highest | at 45 vs highest | last observed age at 85+: median (p90) | golfers observed at 85+ |
|---|---|---|---|---|---|---|
| main (dev-1) | 563 | 31 (27-34) | -2.8 | -7.2 | 37 (43) | 26 |
| branch (dev-2) | 552 | 30 (28-34) | -3.4 | -8.3 | 37 (43) | 24 |

### Year-on-year season-end Overall change of golfers in consecutive snapshots (highest observed 65+), by age

| age | main (dev-1) | branch (dev-2) |
|---|---|---|
| 15-19 | +1.61 (n 2646) | +1.65 (n 2674) |
| 20-24 | +0.54 (n 7985) | +0.55 (n 8077) |
| 25-29 | +0.14 (n 11838) | +0.14 (n 11884) |
| 30-34 | -0.12 (n 10690) | -0.17 (n 10756) |
| 35-39 | -0.49 (n 9052) | -0.59 (n 9048) |
| 40-44 | -0.79 (n 6789) | -0.94 (n 6755) |
| 45-49 | -1.00 (n 4088) | -1.12 (n 3853) |
| 50-54 | -1.09 (n 1545) | -1.07 (n 1457) |
| 55+ | -1.12 (n 421) | -0.94 (n 438) |

### Injuries by age: weeks injured per golfer-season with starts, and the share of those golfer-seasons with any injury (not a per-start injury rate: injury episodes per start are not in this export)

| age | main (dev-1) | branch (dev-2) |
|---|---|---|
| 15-19 | 0.31 / 7.0% | 0.33 / 7.1% |
| 20-24 | 0.24 / 5.3% | 0.24 / 5.4% |
| 25-29 | 0.19 / 4.1% | 0.19 / 4.1% |
| 30-34 | 0.19 / 3.8% | 0.20 / 4.1% |
| 35-39 | 0.31 / 5.5% | 0.35 / 6.0% |
| 40-44 | 0.45 / 7.2% | 0.53 / 8.3% |
| 45-49 | 0.65 / 9.0% | 0.75 / 10.6% |
| 50-54 | 0.74 / 9.6% | 0.80 / 10.7% |
| 55+ | 0.76 / 9.8% | 0.90 / 10.2% |

### Recorded career exits by age at the transition (descriptive counts among each arm's golfers whose highest observed rating was 65+; not rates): retired from play; became a coach or caddie when retiring; became a coach or caddie when they stopped chasing. Deaths are not in this export.

| age | main (dev-1): play / staff retiring / staff stopped chasing | branch (dev-2): play / staff retiring / staff stopped chasing |
|---|---|---|
| 20-24 | 11 / 4 / 26 | 12 / 4 / 23 |
| 25-29 | 80 / 7 / 101 | 85 / 11 / 85 |
| 30-34 | 136 / 20 / 74 | 144 / 11 / 48 |
| 35-39 | 154 / 27 / 30 | 152 / 31 / 28 |
| 40-44 | 236 / 25 / 35 | 256 / 32 / 28 |
| 45-49 | 339 / 25 / 14 | 370 / 34 / 14 |
| 50-54 | 302 / 17 / 3 | 254 / 24 / 4 |
| 55-59 | 95 / 6 / 0 | 106 / 4 / 1 |
| 60-64 | 24 / 1 / 0 | 22 / 2 / 0 |
| 65+ | 0 / 0 / 0 | 4 / 0 / 0 |

### Item 4 diagnostic (partial): world top-100 by Overall not on the Premier Tour; Premier MEMBERS' Overall gaps

Diagnostic only: being off the Premier Tour (amateur, college, another tour, eligibility, scheduling) does not establish blocked access, and member gaps are not tournament-field gaps.

| arm | seasons | top-100 not on Premier (mean) | where they are (mean per season) | Premier members: best minus 10th | best minus 20th |
|---|---|---|---|---|---|
| main (dev-1) | all | 14.6 | amateur 6.4, pro tier 2 5.6, pro tier 4 1.3, club pro 1.1, pro tier 3 0.2 | 5.24 | 7.74 |
| main (dev-1) | last 10 | 15.2 | amateur 5.8, pro tier 2 5.4, pro tier 4 2.3, club pro 1.6, pro tier 3 0.1 | 4.92 | 7.87 |
| branch (dev-2) | all | 13.6 | amateur 7.1, pro tier 2 5.1, pro tier 4 0.8, club pro 0.4, pro tier 3 0.1 | 5.49 | 8.26 |
| branch (dev-2) | last 10 | 15.0 | amateur 7.8, pro tier 2 5.6, club pro 0.8, pro tier 4 0.7, pro tier 3 0.1 | 5.83 | 9.35 |

### Dominance: seasons ending at world No. 1, and majors per winner (winner ledger)

- main (dev-1): season-end No. 1 held by 9 golfers (most 9 seasons); 120 majors, 54 winners, most by one golfer: 12 (born 2008), 9 (born 2006), 9 (born 2009)
- branch (dev-2): season-end No. 1 held by 8 golfers (most 8 seasons); 120 majors, 58 winners, most by one golfer: 8 (born 2019), 7 (born 2008), 7 (born 2027)
- season time, main (dev-1), the 30 common seasons (cloud, 2 workers, two runs sharing 4 CPUs; relative only): median 327 s, max 369 s, total 9466 s
- season time, branch (dev-2), the 8 common seasons (cloud, 2 workers, two runs sharing 4 CPUs; relative only): median 354 s, max 452 s, total 1304 s
