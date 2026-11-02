**Seed 3031, same-fix pair.** Both arms carry the identical reviewed engine fix: baseline main + fix `46013a5` (engine `2abe4dc8`) against realism + fix `c528575` (engine `f0529419`); 30 seasons each, full scale, run together on one 4-CPU cloud machine (2 workers each, alongside other jobs: season times are relative only). Single-version runs, no restarts.

Seed 3031, full scale. Both arms compared on the identical covered seasons 2027-2056 (30). Ratings are recorded after the season and its winter; ages are the age in the completed season (season minus birth year). A golfer's "highest observed" rating is the highest such record, not a complete-career peak; careers still running at the end are censored. One paired world: counts are descriptive, not rates.

### Stock of golfers at 80+ / 85+ / 90+ Overall in each season's snapshot (not eventual supply; a snapshot may include golfers who retire that winter)

| season | main + fix (dev-1) | realism + fix (dev-2) |
|---|---|---|
| 2031 | 33/9/2 | 31/8/2 |
| 2036 | 33/8/2 | 26/7/2 |
| 2041 | 24/6/1 | 24/5/2 |
| 2046 | 28/5/1 | 26/4/1 |
| 2051 | 30/5/1 | 27/4/1 |
| 2056 | 28/4/1 | 29/4/1 |

### Juniors arriving from the second season: first observed rating and highest observed rating SO FAR (censored: the latest classes are early in their careers; the first record is after their first season and winter, not their entry rating)

| arm | juniors | mean first observed | first observed 75+ | 80+ | 85+ | largest first observed | highest observed 75+ | 80+ | 85+ | 90+ |
|---|---|---|---|---|---|---|---|---|---|---|
| main + fix (dev-1) | 8576 | 48.84 | 33 | 8 | 1 | 85.38 | 175 | 37 | 5 | 2 |
| realism + fix (dev-2) | 8576 | 48.64 | 29 | 6 | 1 | 85.37 | 176 | 40 | 5 | 2 |

### Top of the world by Overall (season-end averages)

| arm | seasons | top-20 mean age | top-50 mean age | top-50 aged 40+ | 45+ | best Overall |
|---|---|---|---|---|---|---|
| main + fix (dev-1) | all | 32.17 | 31.69 | 7.37 | 2.83 | 92.31 |
| main + fix (dev-1) | last 10 | 30.80 | 30.69 | 5.20 | 2.00 | 90.88 |
| realism + fix (dev-2) | all | 31.48 | 31.17 | 6.17 | 1.87 | 92.60 |
| realism + fix (dev-2) | last 10 | 29.96 | 30.05 | 3.70 | 0.80 | 91.73 |

### Wins by age (season snapshots) and majors by age (the majors' winner ledger)


all wins (snapshots):

| arm | <25 | 25-29 | 30-34 | 35-39 | 40-44 | 45-49 | 50+ | share 40+ |
|---|---|---|---|---|---|---|---|---|
| main + fix (dev-1) | 14059 | 10567 | 8466 | 5762 | 2911 | 1071 | 415 | 10.2% |
| realism + fix (dev-2) | 14535 | 10676 | 8766 | 5568 | 2544 | 878 | 269 | 8.5% |

Premier wins (snapshots):

| arm | <25 | 25-29 | 30-34 | 35-39 | 40-44 | 45-49 | 50+ | share 40+ |
|---|---|---|---|---|---|---|---|---|
| main + fix (dev-1) | 90 | 258 | 317 | 241 | 117 | 48 | 9 | 16.1% |
| realism + fix (dev-2) | 100 | 296 | 301 | 243 | 102 | 34 | 4 | 13.0% |

majors (winner ledger):

| arm | <25 | 25-29 | 30-34 | 35-39 | 40-44 | 45-49 | 50+ | share 40+ |
|---|---|---|---|---|---|---|---|---|
| main + fix (dev-1) | 12 | 26 | 28 | 30 | 19 | 5 | 0 | 20.0% |
| realism + fix (dev-2) | 14 | 28 | 31 | 24 | 18 | 5 | 0 | 19.2% |
- main + fix (dev-1): majors in the ledger 120, counted in season snapshots 120 (reconciled)
- realism + fix (dev-2): majors in the ledger 120, counted in season snapshots 120 (reconciled)

### Careers observed from 28 or younger to 38 or older (highest observed 70+): age at the highest observed rating, and the rating at 40 and 45 relative to it; last observed age at 85+ (censored at the run's end)

| arm | n | age at highest observed: median (p10-p90) | at 40 vs highest | at 45 vs highest | last observed age at 85+: median (p90) | golfers observed at 85+ |
|---|---|---|---|---|---|---|
| main + fix (dev-1) | 545 | 30 (28-34) | -2.8 | -6.7 | 41 (45) | 17 |
| realism + fix (dev-2) | 553 | 30 (28-33) | -3.3 | -7.9 | 40 (44) | 17 |

### Year-on-year season-end Overall change of golfers in consecutive snapshots (highest observed 65+), by age

| age | main + fix (dev-1) | realism + fix (dev-2) |
|---|---|---|
| 15-19 | +1.61 (n 2588) | +1.66 (n 2566) |
| 20-24 | +0.54 (n 7847) | +0.56 (n 7865) |
| 25-29 | +0.14 (n 11539) | +0.13 (n 11549) |
| 30-34 | -0.12 (n 10531) | -0.16 (n 10613) |
| 35-39 | -0.49 (n 8969) | -0.57 (n 8909) |
| 40-44 | -0.78 (n 6658) | -0.92 (n 6580) |
| 45-49 | -0.97 (n 3846) | -1.10 (n 3744) |
| 50-54 | -1.07 (n 1561) | -1.06 (n 1310) |
| 55+ | -1.10 (n 525) | -0.95 (n 337) |

### Injuries by age: weeks injured per golfer-season with starts, and the share of those golfer-seasons with any injury (not a per-start injury rate: injury episodes per start are not in this export)

| age | main + fix (dev-1) | realism + fix (dev-2) |
|---|---|---|
| 15-19 | 0.32 / 7.0% | 0.33 / 7.1% |
| 20-24 | 0.24 / 5.2% | 0.25 / 5.4% |
| 25-29 | 0.19 / 4.1% | 0.19 / 4.1% |
| 30-34 | 0.20 / 3.9% | 0.19 / 4.1% |
| 35-39 | 0.32 / 5.6% | 0.34 / 6.0% |
| 40-44 | 0.44 / 7.3% | 0.52 / 8.2% |
| 45-49 | 0.61 / 9.0% | 0.71 / 10.3% |
| 50-54 | 0.71 / 9.5% | 0.89 / 10.9% |
| 55+ | 0.73 / 9.0% | 0.75 / 9.5% |

### Recorded career exits by age at the transition (descriptive counts among each arm's golfers whose highest observed rating was 65+; not rates): retired from play; became a coach or caddie when retiring; became a coach or caddie when they stopped chasing. Deaths are not in this export.

| age | main + fix (dev-1): play / staff retiring / staff stopped chasing | realism + fix (dev-2): play / staff retiring / staff stopped chasing |
|---|---|---|
| 15-19 | 1 / 0 / 0 | 0 / 0 / 0 |
| 20-24 | 15 / 2 / 27 | 7 / 1 / 26 |
| 25-29 | 76 / 8 / 74 | 66 / 15 / 83 |
| 30-34 | 140 / 20 / 46 | 121 / 14 / 39 |
| 35-39 | 143 / 25 / 24 | 176 / 25 / 30 |
| 40-44 | 249 / 23 / 31 | 251 / 26 / 28 |
| 45-49 | 362 / 27 / 17 | 353 / 26 / 17 |
| 50-54 | 233 / 22 / 2 | 273 / 20 / 3 |
| 55-59 | 119 / 8 / 0 | 81 / 9 / 1 |
| 60-64 | 27 / 1 / 0 | 21 / 1 / 0 |
| 65+ | 4 / 0 / 0 | 1 / 0 / 0 |

### Item 4 diagnostic (partial): world top-100 by Overall not on the Premier Tour; Premier MEMBERS' Overall gaps

Diagnostic only: being off the Premier Tour (amateur, college, another tour, eligibility, scheduling) does not establish blocked access, and member gaps are not tournament-field gaps.

| arm | seasons | top-100 not on Premier (mean) | where they are (mean per season) | Premier members: best minus 10th | best minus 20th |
|---|---|---|---|---|---|
| main + fix (dev-1) | all | 14.9 | pro tier 2 6.1, amateur 5.5, pro tier 4 3.1, club pro 0.2, pro tier 3 0.1 | 8.66 | 11.00 |
| main + fix (dev-1) | last 10 | 19.0 | amateur 7.8, pro tier 2 7.0, pro tier 4 4.0, pro tier 3 0.1, club pro 0.1 | 7.16 | 9.65 |
| realism + fix (dev-2) | all | 13.8 | pro tier 2 5.7, amateur 5.4, pro tier 4 2.1, club pro 0.4, pro tier 3 0.1 | 9.05 | 11.50 |
| realism + fix (dev-2) | last 10 | 17.1 | amateur 8.3, pro tier 2 6.6, pro tier 4 1.9, club pro 0.2, pro tier 3 0.1 | 7.96 | 10.81 |

### Dominance: seasons ending at world No. 1, and majors per winner (winner ledger)

- main + fix (dev-1): season-end No. 1 held by 5 golfers (most 11 seasons); 120 majors, 50 winners, most by one golfer: 18 (born 2003), 14 (born 2018), 10 (born 1986)
- realism + fix (dev-2): season-end No. 1 held by 6 golfers (most 12 seasons); 120 majors, 55 winners, most by one golfer: 14 (born 2006), 11 (born 2003), 10 (born 2018)
- season time, main + fix (dev-1), the 30 common seasons (cloud, 2 workers, two runs sharing 4 CPUs; relative only): median 330 s, max 435 s, total 10075 s
- season time, realism + fix (dev-2), the 30 common seasons (cloud, 2 workers, two runs sharing 4 CPUs; relative only): median 324 s, max 434 s, total 9983 s
