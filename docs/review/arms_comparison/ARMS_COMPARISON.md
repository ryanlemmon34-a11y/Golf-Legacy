# Arms comparison (pinned build c0d1ea5)

Written 2026-10-31 12:36 UTC by armsan/analyze.py from the run folders as committed at read time (read-only). Same build for every arm; seeds pinned. Partial arms are labelled with the seasons included. No conclusions beyond the data; effects are noted, not tuned.

| arm | seed | build | arm recorded | pathway min age in force | seasons | run state read from | archive generation |
|---|---|---|---|---|---|---|---|
| a21old | 4207 | c0d1ea5 | {"work_pathway_min_age": 21, "college_open_access": false} | 21 | a21old: seasons 2027–2036 (10) | seed json | 10 |
| a18old | 4207 | c0d1ea5 | {"work_pathway_min_age": 18, "college_open_access": false} | 18 | a18old: seasons 2027–2036 (10) | seed json | 10 |
| a18new | 4207 | c0d1ea5 | {"work_pathway_min_age": 18, "college_open_access": true} | 18 | a18new: seasons 2027–2036 (10) | seed json | 10 |
| seed2 | 5309 | c0d1ea5 | {"work_pathway_min_age": 18, "college_open_access": true} | 18 | seed2: seasons 2027–2031 (5) | seed json | 5 |

## 1. Pathway age: a21old (minimum age 21) vs a18old (minimum age 18), seed 4207, college order old

Seasons: a21old: seasons 2027–2036 (10); a18old: seasons 2027–2036 (10).

### Where the arms diverge

Golfer rows of the run state (long_world `year_rows`: results, money, staff, activity counts) compared season by season between the two arms.

| season | rows a21old | rows a18old | in both | identical |
|---|---|---|---|---|
| 2027 | 6409 | 6409 | 6409 | 6409/6409 (100.0%) |
| 2028 | 6881 | 6881 | 6881 | 6879/6881 (100.0%) |
| 2029 | 7321 | 7320 | 7315 | 31/7315 (0.4%) |
| 2030 | 7750 | 7749 | 7483 | 8/7483 (0.1%) |
| 2031 | 8193 | 8202 | 7724 | 5/7724 (0.1%) |
| 2032 | 8642 | 8662 | 7961 | 2/7961 (0.0%) |
| 2033 | 9046 | 9068 | 8129 | 1/8129 (0.0%) |
| 2034 | 9396 | 9401 | 8273 | 1/8273 (0.0%) |
| 2035 | 9758 | 9763 | 8399 | 0/8399 (0.0%) |
| 2036 | 10027 | 10056 | 8428 | 0/8428 (0.0%) |

First pathway entry below 21 in a18old: season 2028, week 45 (golfer 5217, age 20).
First season with any differing row: 2028.
Rows differing in 2028: 2 (5217 (entered the pathway below 21 in a18old), 5493); rows in one arm only: 0.

The three fixed-cohort tables below each describe the same people under each arm's rule, as recorded. None of them shows a guaranteed rescue or a causal effect on any individual's career; differences between the columns are arm-level differences within the stated group (the worlds diverge from 2028, so other people and events differ too).

### PRETREATMENT COHORT: the shared 2027 baseline (fixed membership, the same people in both arms)

The arms are identical through all of 2027 (6409/6409 2027 rows identical), so a 2027 end-of-season state is pretreatment. Definition: golfers whose 2027 season row (identical in both arms, same person by id, name, birth year and country) shows an amateur on a non-college tour (2027 season file `careers.tour`), full-time, aged 17–20 in 2027 (2027 minus birth year). Left out: in college 628.

N = 241 (by age in 2027: 18: 68, 19: 92, 20: 81). Outcomes over seasons 2028–2036; denominator N in both columns (the same people).

| outcome (denominator: the fixed cohort, N = 241) | a21old | a18old |
|---|---|---|
| status at the end of 2036: pro, full-time | 11/241 (4.6%) | 18/241 (7.5%) |
| status at the end of 2036: pro, part-time | 6/241 (2.5%) | 13/241 (5.4%) |
| status at the end of 2036: club pro | 1/241 (0.4%) | 1/241 (0.4%) |
| status at the end of 2036: amateur, full-time | 9/241 (3.7%) | 8/241 (3.3%) |
| status at the end of 2036: amateur, part-time | 183/241 (75.9%) | 171/241 (71.0%) |
| status at the end of 2036: retired | 27/241 (11.2%) | 29/241 (12.0%) |
| status at the end of 2036: staff (coach or caddie) | 4/241 (1.7%) | 1/241 (0.4%) |
| starts, cumulative (min/q1/med/q3/max) | 26 / 94 / 112 / 124 / 233 (n=241) | 20 / 95 / 111 / 124 / 223 (n=241) |
| starts, total | 26,357 | 26,749 |
| golfers with any zero-start season | 4/241 (1.7%) | 1/241 (0.4%) |
| zero-start seasons / seasons with an active row | 4/2068 (0.2%) | 1/2061 (0.0%) |
| golfers who entered the pathway | 79/241 (32.8%) | 74/241 (30.7%) |
| pathway entries (ages at entry) | 79 (21: 22, 22: 25, 23: 16, 24: 14, 25: 2) | 75 (20: 11, 21: 15, 22: 21, 23: 15, 24: 9, 25: 2, 26: 2) |
| Overall at the end of 2036 (golfers with a 2036 row) | 26.2 / 36.8 / 47.5 / 59.4 / 75.5 (n=210) | 26.2 / 36.0 / 46.4 / 59.3 / 75.5 (n=211) |

Status at the end of 2036 is the golfer's 2036 season row before that winter's decisions; a golfer with no active row is classified by the exit recorded in an earlier winter (retired, became coach or caddie) or a recorded death. Starts and zero-start seasons count every season the golfer had an active row, whatever their status that season.

### ARRIVAL COHORT: juniors created for 2028 (fixed at creation, the same people in both arms)

Golfers who arrived for 2028 (first row in 2028), defined by their creation record, not their end-of-2028 row. Fields used: the 2028 season file's `diagnostics.created` (written by Season.note_creation at creation, week 0: path, age, Overall, attributes) and the arrival line of their history at week 1 (`log`, written by careers.add_juniors: "Arrived on the scene at 18 (<tour>)", the tour assigned by population.junior_class at creation); lifestyle at creation is the Golfer default, full-time (golfer.py). Verification: 295 junior arrivals in a21old, 711 creation records in a18old vs 711 in a21old; identical extracted creation fields (path, age, Overall, week), arrival line and identity (name, birth year, country) in both arms for 295/295 — PASSED (full attributes and ceilings were not compared). Kept: juniors (all aged 18 at creation) whose creation tour is not a college tour. Left out: in college at creation 232. Late entrants (new professionals, path "late_entrant", aged 21–26) are not amateurs and are not included.

N = 63 (by age in 2028: 18: 63). Outcomes over seasons 2028–2036; denominator N in both columns (the same people).

| outcome (denominator: the fixed cohort, N = 63) | a21old | a18old |
|---|---|---|
| status at the end of 2036: pro, full-time | 4/63 (6.3%) | 4/63 (6.3%) |
| status at the end of 2036: amateur, full-time | 5/63 (7.9%) | 3/63 (4.8%) |
| status at the end of 2036: amateur, part-time | 53/63 (84.1%) | 49/63 (77.8%) |
| status at the end of 2036: retired | 1/63 (1.6%) | 7/63 (11.1%) |
| starts, cumulative (min/q1/med/q3/max) | 65 / 109 / 121 / 134 / 225 (n=63) | 63 / 108 / 123 / 134 / 227 (n=63) |
| starts, total | 7,691 | 7,600 |
| golfers with any zero-start season | 1/63 (1.6%) | 0/63 (0.0%) |
| zero-start seasons / seasons with an active row | 1/566 (0.2%) | 0/550 (0.0%) |
| golfers who entered the pathway | 26/63 (41.3%) | 28/63 (44.4%) |
| pathway entries (ages at entry) | 26 (21: 11, 22: 8, 23: 4, 25: 3) | 28 (20: 3, 21: 9, 22: 9, 23: 2, 25: 3, 26: 2) |
| Overall at the end of 2036 (golfers with a 2036 row) | 28.3 / 37.4 / 47.1 / 56.8 / 79.5 (n=62) | 29.6 / 37.7 / 47.9 / 56.8 / 79.4 (n=56) |

Status at the end of 2036 is the golfer's 2036 season row before that winter's decisions; a golfer with no active row is classified by the exit recorded in an earlier winter (retired, became coach or caddie) or a recorded death. Starts and zero-start seasons count every season the golfer had an active row, whatever their status that season.

### FIXED COHORT selected by the control arm's (a21old) end-2028 status: the same people in both arms, chosen after week 45 of 2028, not pretreatment

Selected by a21old's end-of-2028 row, after the arms diverged in week 45 of 2028; the group is the same people in both columns, but its selection used a post-divergence state, so it is not a pretreatment group. Definition: golfers with a 2028 row in both arms, the same person in both, and in a21old's 2028 row an amateur on a non-college tour, full-time, aged 17–20. The 2028 rows differ between the arms for 2 golfers (5217, 5493). Left out: in college 645, part-time 2. Read every difference below as a descriptive arm difference within this selected group (for example in retirements), not as the pathway causing it.

N = 220 (by age in 2028: 18: 63, 19: 67, 20: 90). Outcomes over seasons 2028–2036; denominator N in both columns (the same people).

| outcome (denominator: the fixed cohort, N = 220) | a21old | a18old |
|---|---|---|
| status at the end of 2036: pro, full-time | 10/220 (4.5%) | 15/220 (6.8%) |
| status at the end of 2036: pro, part-time | 3/220 (1.4%) | 5/220 (2.3%) |
| status at the end of 2036: club pro | 0/220 (0.0%) | 1/220 (0.5%) |
| status at the end of 2036: amateur, full-time | 13/220 (5.9%) | 11/220 (5.0%) |
| status at the end of 2036: amateur, part-time | 179/220 (81.4%) | 162/220 (73.6%) |
| status at the end of 2036: retired | 13/220 (5.9%) | 26/220 (11.8%) |
| status at the end of 2036: staff (coach or caddie) | 2/220 (0.9%) | 0/220 (0.0%) |
| starts, cumulative (min/q1/med/q3/max) | 26 / 98 / 114 / 126 / 233 (n=220) | 20 / 102 / 115 / 127 / 227 (n=220) |
| starts, total | 25,116 | 25,108 |
| golfers with any zero-start season | 4/220 (1.8%) | 0/220 (0.0%) |
| zero-start seasons / seasons with an active row | 4/1938 (0.2%) | 0/1892 (0.0%) |
| golfers who entered the pathway | 85/220 (38.6%) | 85/220 (38.6%) |
| pathway entries (ages at entry) | 85 (21: 32, 22: 26, 23: 15, 24: 8, 25: 4) | 86 (20: 14, 21: 23, 22: 24, 23: 13, 24: 4, 25: 4, 26: 4) |
| Overall at the end of 2036 (golfers with a 2036 row) | 26.6 / 36.7 / 46.3 / 57.6 / 79.5 (n=205) | 26.6 / 36.2 / 46.0 / 57.1 / 79.4 (n=194) |

Status at the end of 2036 is the golfer's 2036 season row before that winter's decisions; a golfer with no active row is classified by the exit recorded in an earlier winter (retired, became coach or caddie) or a recorded death. Starts and zero-start seasons count every season the golfer had an active row, whatever their status that season.

### The first entry below 21 (season 2028), up to the point the worlds diverge

Season 2028 is the last season in which the arms are nearly identical (2027 is identical; in 2028 the rows of 2 golfers differ). From the next season fewer than 1% of rows are identical, so a golfer's later seasons in the other arm are not a counterfactual for that person and are not compared here.

- Golfer 5217 (born 2008, Norway): 2028 row columns that differ: lifestyle, net, cash, salary, living.
  - a21old: status amateur, lifestyle full_time, events 12, net -5355, cash -7750, salary 0, living 0; longest cash-blocked count 14.
  - a18old: status amateur, lifestyle part_time, events 12, net -3509, cash -5904, salary 8000, living 6154; longest cash-blocked count 11; took work by the pathway in week 45 at age 20 after 11 counted weeks.
- Golfer 5493 (born 2006, India): 2028 row columns that differ: support, moving, home.
  - a21old: status amateur, lifestyle full_time, events 24, support 1642, moving 0, home Japan; longest cash-blocked count —.
  - a18old: status amateur, lifestyle full_time, events 24, support 7642, moving 6000, home India; longest cash-blocked count —.

### END-STATUS denominators: tracked full-time non-college amateurs (golfer-seasons), by age band

**Denominator: end-status golfer-seasons.** Membership depends on each season's end status (or a pathway entry during the season), so the group's makeup differs between the arms from 2028 on; these tables compare arm-level rates, not the same people (see the ORIGINAL COHORT table for that). Tracked: amateur, not in college, full-time at the season end or took work by the pathway during it (extras `amateurs`). "Blocked" is the season's longest count of genuinely cash-blocked weeks (work_pathway.count: only "could not afford any event" adds).

**a21old** (END-STATUS denominators, pooled over 10 seasons)

| age band | tracked seasons | zero-start | any blocked week | count 8+ (in-season max) | pathway entries / tracked | count-8+ seasons that entered | entries with in-season max < 8 (count carried from the season before) |
|---|---|---|---|---|---|---|---|
| <18 | 0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0 |
| 18-20 | 2132 | 12/2132 (0.6%) | 87/2132 (4.1%) | 59/2132 (2.8%) | 0/2132 (0.0%) | 0/59 (0.0%) | 0 |
| 21+ | 2245 | 1/2245 (0.0%) | 255/2245 (11.4%) | 204/2245 (9.1%) | 242/2245 (10.8%) | 193/204 (94.6%) | 49 |

Zero-start reasons (run state rows, `zero_start_reason`): 18-20: kept out by barriers — 12; 21+: barriers and choices — 1

Per season (END-STATUS denominators) — tracked / zero-start / any blocked / count 8+ / entries:

| season | 18-20 | 21+ |
|---|---|---|
| 2027 | 241 / 0 / 0 / 0 / 0 | 133 / 0 / 0 / 0 / 0 |
| 2028 | 220 / 0 / 3 / 1 / 0 | 216 / 0 / 4 / 1 / 1 |
| 2029 | 193 / 3 / 13 / 10 / 0 | 269 / 0 / 18 / 16 / 15 |
| 2030 | 190 / 1 / 7 / 3 / 0 | 277 / 0 / 36 / 26 / 35 |
| 2031 | 214 / 3 / 15 / 10 / 0 | 240 / 0 / 38 / 28 / 28 |
| 2032 | 218 / 1 / 11 / 9 / 0 | 229 / 0 / 36 / 29 / 37 |
| 2033 | 229 / 0 / 9 / 7 / 0 | 210 / 1 / 26 / 22 / 29 |
| 2034 | 217 / 1 / 11 / 10 / 0 | 222 / 0 / 36 / 28 / 31 |
| 2035 | 203 / 2 / 10 / 5 / 0 | 219 / 0 / 32 / 26 / 34 |
| 2036 | 207 / 1 / 8 / 4 / 0 | 230 / 0 / 29 / 28 / 32 |

**a18old** (END-STATUS denominators, pooled over 10 seasons)

| age band | tracked seasons | zero-start | any blocked week | count 8+ (in-season max) | pathway entries / tracked | count-8+ seasons that entered | entries with in-season max < 8 (count carried from the season before) |
|---|---|---|---|---|---|---|---|
| <18 | 0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0 |
| 18-20 | 2160 | 0/2160 (0.0%) | 83/2160 (3.8%) | 62/2160 (2.9%) | 56/2160 (2.6%) | 56/62 (90.3%) | 0 |
| 21+ | 2243 | 0/2243 (0.0%) | 256/2243 (11.4%) | 191/2243 (8.5%) | 192/2243 (8.6%) | 184/191 (96.3%) | 8 |

Per season (END-STATUS denominators) — tracked / zero-start / any blocked / count 8+ / entries:

| season | 18-20 | 21+ |
|---|---|---|
| 2027 | 241 / 0 / 0 / 0 / 0 | 133 / 0 / 0 / 0 / 0 |
| 2028 | 220 / 0 / 3 / 1 / 1 | 216 / 0 / 4 / 1 / 1 |
| 2029 | 193 / 0 / 13 / 10 / 10 | 271 / 0 / 19 / 16 / 16 |
| 2030 | 188 / 0 / 8 / 4 / 3 | 270 / 0 / 35 / 26 / 23 |
| 2031 | 215 / 0 / 11 / 10 / 10 | 244 / 0 / 37 / 30 / 31 |
| 2032 | 226 / 0 / 6 / 5 / 4 | 210 / 0 / 29 / 22 / 22 |
| 2033 | 237 / 0 / 10 / 7 / 6 | 210 / 0 / 30 / 25 / 25 |
| 2034 | 217 / 0 / 14 / 12 / 11 | 233 / 0 / 38 / 25 / 24 |
| 2035 | 209 / 0 / 13 / 9 / 7 | 226 / 0 / 30 / 24 / 26 |
| 2036 | 214 / 0 / 5 / 4 / 4 | 230 / 0 / 34 / 22 / 24 |

### Pathway entries by age (season file `work_pathway` records; counts of entries, no denominator)

| arm | entries | age 20 | age 21 | age 22 | age 23 | age 24 | age 25 | age 26 | age 28 |
|---|---|---|---|---|---|---|---|---|---|
| a21old | 242 | 0 | 121 | 62 | 32 | 19 | 7 | 0 | 1 |
| a18old | 248 | 56 | 73 | 58 | 36 | 14 | 7 | 4 | 0 |

### Reconstructed: the last n plan weeks compatible with the recorded count (monthly-plan availability, not actual weekly access); unknown weeks shown

The weekly access outcome is not stored week by week. This walks back from each entry's decision week over the availability the monthly plans recorded for each week (decision evidence /2, `schedule`), reading it as work_pathway.count reads access ("unaff" counts, "none"/"inelig"/injured pause, anything else resets). "Compatible" means the plan weeks contain the recorded `weeks_blocked` (n) counted weeks before any reset; it shows the plan data do not contradict the stored count, and does not validate it independently (the walk stops at n) nor give the golfer's actual weeks. "Span" is the calendar weeks from the earliest of those n plan weeks to the decision (pauses included); it is not a measured time from the first blocked week. "Longer run" scans on past n until a reset: entries whose plan-based compatible run is longer than the stored count. Plan-week availability and the weekly access ledger can differ, so a longer plan-based run is not evidence of a miscount.

| arm | age band | entries | compatible | entries with unknown plan weeks in the span | span, plan weeks (min/q1/med/q3/max) | recorded weeks_blocked | longer plan-based run than recorded | plan-based run, scanned to a reset |
|---|---|---|---|---|---|---|---|---|
| a21old | 21+ | 242 | 242/242 (100.0%) | 0 (0 weeks) | 8 / 9 / 12 / 21 / 72 (n=242) | 8 / 8 / 9 / 11 / 60 (n=242) | 2/242 (0.8%); 0 reach the data start | 8 / 8 / 9 / 11 / 60 (n=242) |
| a18old | 18-20 | 56 | 56/56 (100.0%) | 0 (0 weeks) | 8 / 9 / 12 / 12 / 32 (n=56) | 8 / 8 / 9 / 10 / 20 (n=56) | 1/56 (1.8%); 0 reach the data start | 8 / 8 / 9 / 10 / 20 (n=56) |
| a18old | 21+ | 192 | 192/192 (100.0%) | 0 (0 weeks) | 8 / 8 / 12 / 13 / 36 (n=192) | 8 / 8 / 8 / 10 / 12 (n=192) | 3/192 (1.6%); 0 reach the data start | 8 / 8 / 8 / 10 / 12 (n=192) |

### After the job (denominator: each arm's pathway entries; the entrants differ between arms)

Event-based groups: who enters depends on the arm, so these are arm-level descriptions, not a comparison of the same people. For each entry in season Y: season starts in Y (including starts made before the job), starts from the decision week on (the weeks of the editions whose finishes list the golfer, from the season file `events`), the weeks from the decision to the first such start, starts in Y+1 (season file `careers`), Overall change over Y+1 (ratings as each season ends), and the first career transition from the winter after Y on (within the committed seasons). Entries in the last committed season have no Y+1.

| arm | band | entries | season starts in Y (including before the job) | starts in Y from the decision week on | weeks from the decision to the first start after it | no start after the decision in Y | starts in Y+1 | Overall change over Y+1 |
|---|---|---|---|---|---|---|---|---|
| a21old | 21+ | 242 | 0 / 7 / 9 / 10 / 14 (n=242) | 0 / 1 / 4 / 8 / 13 (n=242) | 1 / 4 / 5 / 7 / 18 (n=202) | 40/242 (16.5%) | 0 / 6 / 10 / 11 / 17 (n=210) | 0.00 / 0.20 / 0.30 / 0.40 / 0.80 (n=203) |
| a18old | 18-20 | 56 | 3 / 7 / 10 / 11 / 13 (n=56) | 0 / 1 / 3 / 6 / 11 (n=56) | 2 / 4 / 5 / 7 / 13 (n=46) | 10/56 (17.9%) | 0 / 6 / 9 / 11 / 16 (n=52) | 0.20 / 0.40 / 0.50 / 0.65 / 1.20 (n=51) |
| a18old | 21+ | 192 | 1 / 6 / 9 / 10 / 13 (n=192) | 0 / 1 / 3 / 6 / 12 (n=192) | 0 / 4 / 5 / 7 / 27 (n=159) | 33/192 (17.2%) | 0 / 6 / 10 / 10 / 15 (n=168) | 0.00 / 0.20 / 0.30 / 0.40 / 0.80 (n=162) |

- a21old 21+: no transition: amateur part_time 170/242 (70.2%); amateur returned to full-time golf 43/242 (17.8%); retired 22/242 (9.1%); turned pro 5/242 (2.1%); became coach 1/242 (0.4%); became caddie 1/242 (0.4%)
- a18old 18-20: no transition: amateur part_time 41/56 (73.2%); amateur returned to full-time golf 10/56 (17.9%); retired 4/56 (7.1%); turned pro 1/56 (1.8%)
- a18old 21+: no transition: amateur part_time 138/192 (71.9%); retired 27/192 (14.1%); amateur returned to full-time golf 24/192 (12.5%); turned pro 3/192 (1.6%)

### END-STATUS denominators: tracked golfer-seasons with a count of 8+ that did not enter that season

Membership depends on end status and on not entering, both of which differ between arms; arm-level description only.

| arm | band | golfer-seasons | starts in Y | starts in Y+1 | Overall change over Y+1 | first transition after (top 4) |
|---|---|---|---|---|---|---|
| a21old | 18-20 | 59 | 0 / 1 / 5 / 8 / 12 (n=59) | 0 / 6 / 8 / 10 / 13 (n=55) | 0.10 / 0.40 / 0.50 / 0.70 / 1.80 (n=55) | no transition: amateur part_time 32; amateur returned to full-time golf 11; amateur took a job 7; retired 4 |
| a21old | 21+ | 11 | 5 / 10 / 12 / 13 / 14 (n=11) | 0 / 7 / 10 / 12 / 16 (n=11) | 0.00 / 0.10 / 0.20 / 0.30 / 0.60 (n=11) | amateur took a job 8; no transition: amateur part_time 2; amateur returned to full-time golf 1 |
| a18old | 18-20 | 6 | 4 / 8 / 9 / 11 / 14 (n=6) | 8 / 9 / 10 / 11 / 12 (n=6) | 0.20 / 0.30 / 0.35 / 0.63 / 1.00 (n=6) | no transition: amateur part_time 5; amateur took a job 1 |
| a18old | 21+ | 7 | 8 / 11 / 12 / 13 / 15 (n=7) | 5 / 10 / 11 / 11 / 12 (n=7) | 0.00 / 0.15 / 0.20 / 0.20 / 0.40 (n=7) | amateur took a job 4; no transition: amateur part_time 2; retired 1 |

## 2. College access: a18old (open access OFF) vs a18new (ON), seed 4207, pathway age 18

Seasons: a18old: seasons 2027–2036 (10); a18new: seasons 2027–2036 (10).

Definitions as the build has them (golfsim/season.py): an ordinary open amateur event is tier 6, category "regular", amateur eligibility, of a tour in `OPEN_AMATEUR_REGIONS` (AM_NORTH_AMERICA: North America, AM_EUROPE: Europe, AM_ASIA: Asia/Middle East, AM_OCEANIA: Oceania, AM_AFRICA: Africa, AM_LATAM: Latin America); field capacity = field × 1.5 (AMATEUR_OPEN_EXPANSION). College players: amateurs on a college tour (tier 5, `CO_*`), placed in the series region of where they lived that season (season file `careers.residence`, the residence `home_college_amateur` reads). Members: amateurs whose tour is that series. Shut out: weeks recorded in the access ledger (`careers.denied`) whose first choice was an ordinary open event and every acceptable field was full ("shut out"), or they played elsewhere ("alternative"). The two arms differ from the first season (the setting acts from week 1).

### COHORT fixed at creation (pretreatment): 2027 college players and series members, the same people in both arms

These two arms differ from week 1 of 2027, so no played season is shared. Membership comes from the 2027 season record's tour and residence, which are the creation values: a golfer's tour is assigned at world creation (golfsim/population.py `generate_world`: `_college_or_series` and the amateur series, lines 582, 676, 678) and is changed only after the season's snapshot is taken (golfsim/season.py `end_of_season`: snapshot at line 2621, then `apply_cards` 2628, `careers.decide` 2647, `residence.review_moves` 2668); the residence is set at creation by `residence.settle(first_year, 0)` (season.py line 559), and the only writer of a move, `residence._record` (residence.py line 278), is called at week 0 or week 53 (settle, review_moves, staff_moves), never during weeks 1–52; the season file's `careers.residence` is `residence_at(gid, year, 52)` (archive.py line 213). Data check: for all 2663 members kept, the 2027 residence equals the people table's `first_residence` dated (2027, week 0) in both arms — PASSED. Kept: amateurs whose 2027 tour and residence are the same in both arms and who are the same person (id, name, birth year, country); 0 differ and are left out. College players are placed by that residence, members by their series. Denominator: the fixed group's size, the same people in both arms.

Per-head columns are CUMULATIVE 2027–2036 values per member of N (the fixed group's size): ordinary open starts / tier-5 (college) starts / weeks shut out of a full ordinary open field (in brackets: weeks they played elsewhere instead).

| group | series region | N (fixed) | a18old: cumulative 2027–2036 per member of N — open starts / tier-5 starts / open shut-out weeks (alt) | a18new: cumulative 2027–2036 per member of N — same | a18old status end 2036 (top 3) | a18new status end 2036 (top 3) |
|---|---|---|---|---|---|---|
| college | ASIA | 153 | 74.8 / 24.3 / 32.5 (13.0) | 74.8 / 23.9 / 26.2 (8.3) | amateur, part-time 77/153 (50%), pro, part-time 27/153 (18%), pro, full-time 22/153 (14%) | amateur, part-time 82/153 (54%), pro, part-time 25/153 (16%), pro, full-time 21/153 (14%) |
| college | EUROPE | 188 | 62.7 / 19.3 / 18.3 (12.2) | 68.2 / 18.4 / 12.6 (7.2) | amateur, part-time 82/188 (44%), pro, part-time 45/188 (24%), retired 30/188 (16%) | amateur, part-time 99/188 (53%), retired 33/188 (18%), pro, part-time 25/188 (13%) |
| college | NORTH_AMERICA | 672 | 58.3 / 39.8 / 84.3 (15.3) | 57.3 / 38.4 / 92.1 (14.7) | amateur, part-time 330/672 (49%), pro, part-time 137/672 (20%), retired 76/672 (11%) | amateur, part-time 331/672 (49%), pro, part-time 141/672 (21%), pro, full-time 77/672 (11%) |
| college | OCEANIA | 52 | 61.3 / 22.4 / 6.8 (3.5) | 68.2 / 22.4 / 9.4 (2.2) | amateur, part-time 23/52 (44%), pro, part-time 10/52 (19%), pro, full-time 7/52 (13%) | amateur, part-time 28/52 (54%), pro, full-time 9/52 (17%), pro, part-time 7/52 (13%) |
| members | AFRICA | 69 | 54.6 / 0.0 / 0.0 (0.0) | 59.8 / 0.0 / 0.0 (0.0) | amateur, part-time 34/69 (49%), retired 27/69 (39%), amateur, full-time 3/69 (4%) | amateur, part-time 39/69 (57%), retired 22/69 (32%), pro, full-time 2/69 (3%) |
| members | ASIA | 405 | 71.1 / 0.0 / 14.2 (1.7) | 67.5 / 0.0 / 21.2 (2.8) | amateur, part-time 207/405 (51%), retired 174/405 (43%), staff (coach or caddie) 8/405 (2%) | amateur, part-time 201/405 (50%), retired 184/405 (45%), staff (coach or caddie) 8/405 (2%) |
| members | EUROPE | 487 | 59.9 / 0.0 / 5.5 (1.4) | 56.6 / 0.0 / 8.2 (4.7) | amateur, part-time 248/487 (51%), retired 206/487 (42%), pro, full-time 10/487 (2%) | amateur, part-time 229/487 (47%), retired 220/487 (45%), staff (coach or caddie) 13/487 (3%) |
| members | LATAM | 49 | 34.6 / 0.0 / 0.0 (0.0) | 34.7 / 0.0 / 0.0 (0.0) | amateur, part-time 30/49 (61%), retired 15/49 (31%), pro, part-time 2/49 (4%) | amateur, part-time 28/49 (57%), retired 18/49 (37%), pro, part-time 1/49 (2%) |
| members | NORTH_AMERICA | 479 | 81.8 / 0.0 / 74.6 (23.5) | 72.1 / 0.0 / 136.6 (22.8) | amateur, part-time 265/479 (55%), retired 196/479 (41%), staff (coach or caddie) 6/479 (1%) | amateur, part-time 245/479 (51%), retired 218/479 (46%), staff (coach or caddie) 8/479 (2%) |
| members | OCEANIA | 109 | 76.4 / 0.0 / 3.0 (0.0) | 76.1 / 0.0 / 11.0 (0.4) | amateur, part-time 56/109 (51%), retired 45/109 (41%), pro, full-time 4/109 (4%) | amateur, part-time 52/109 (48%), retired 46/109 (42%), pro, full-time 5/109 (5%) |

**Capacity trade-off.** College players and series members compete for the same ordinary open field capacity. How each group's open starts and shut-out weeks moved between the arms, computed from the runs (old → new): North America members (fixed, N = 479): cumulative 2027–2036 open starts per head 81.8 → 72.1 (-12%), cumulative open shut-out weeks per head 74.6 → 136.6; North America college players (fixed, N = 672): cumulative open starts per head 58.3 → 57.3 (-2%), cumulative open shut-out weeks per head 84.3 → 92.1; All regions, end-status 2036 (yr 10): member open starts per member 8.80 → 8.08; member shut-out weeks per member 9.49 → 12.54; college open starts per player 6.58 → 9.15; North America in 2036 (end-status): series members' ordinary open starts per member 9.40 → 7.76; working (part-time) amateur members, all starts per head 9.77 → 8.26 and ordinary open starts per head 9.21 → 7.75 (the part-time amateur schedule target is 8 events: season.target_events); zero-start seasons in 2036, all regions (end-status): college players 0/1024 (0.0%) → 0/1028 (0.0%); series members 0/3671 (0.0%) → 0/3608 (0.0%); working (part-time) amateur members 0/3255 (0.0%) → 0/3180 (0.0%) — no group's zero-start share increased. Design status (reviewer decision, recorded here): the open-access policy is retained; the cost in members' opportunities is disclosed, not offset by expanding fields.

### END-STATUS denominators: all regions, per season (old → new)

**Denominators: each season's college players and members at that season's end** — membership is re-taken every season in each arm (who is in college or a member, and where they live, depends on the arm), so these are arm-level per-season rates, not the same people.

| season | college players | college open starts / player | college players with any open start | college tier-5 starts / player | members | member open starts / member | ordinary open events | field fill (entrants / capacity) | events full | college shut out (alt) / player | member shut out (alt) / member |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2027 (yr 1) | 1065 → 1065 | 11.47 → 12.11 | 99.9% → 100.0% | 10.51 → 10.26 | 1598 → 1598 | 10.35 → 10.01 | 391 → 393 | 53.0% → 53.0% | 34.5% → 33.3% | 7.45 (3.02) → 4.26 (2.15) | 1.49 (1.09) → 5.16 (1.51) |
| 2028 (yr 2) | 1089 → 1087 | 11.07 → 11.89 | 98.1% → 99.7% | 10.43 → 10.26 | 1911 → 1883 | 10.30 → 9.87 | 394 → 394 | 58.0% → 57.6% | 38.6% → 39.3% | 9.08 (3.30) → 4.91 (2.63) | 2.34 (1.25) → 6.19 (1.72) |
| 2029 (yr 3) | 1068 → 1064 | 10.42 → 11.13 | 97.4% → 98.6% | 10.71 → 10.61 | 2201 → 2180 | 9.94 → 9.52 | 397 → 395 | 60.0% → 59.5% | 39.8% → 41.0% | 10.41 (3.32) → 5.86 (2.88) | 3.27 (1.33) → 7.12 (1.56) |
| 2030 (yr 4) | 1063 → 1060 | 9.79 → 10.55 | 94.2% → 96.0% | 10.73 → 10.70 | 2402 → 2416 | 9.74 → 9.23 | 393 → 395 | 62.0% → 61.1% | 44.0% → 43.3% | 10.85 (3.16) → 6.18 (2.87) | 3.89 (1.27) → 7.74 (1.44) |
| 2031 (yr 5) | 1075 → 1072 | 9.21 → 10.32 | 90.8% → 93.5% | 10.76 → 10.64 | 2658 → 2671 | 9.50 → 8.96 | 396 → 397 | 64.0% → 63.5% | 46.0% → 46.1% | 11.76 (3.39) → 6.86 (2.86) | 4.67 (1.18) → 8.50 (1.40) |
| 2032 (yr 6) | 1090 → 1088 | 8.91 → 10.17 | 92.8% → 93.8% | 10.59 → 10.46 | 2885 → 2880 | 9.26 → 8.74 | 394 → 396 | 66.6% → 66.0% | 48.5% → 49.5% | 12.54 (3.45) → 7.65 (3.13) | 5.86 (1.18) → 9.40 (1.37) |
| 2033 (yr 7) | 1061 → 1062 | 8.39 → 9.82 | 89.9% → 93.9% | 10.90 → 10.81 | 3100 → 3101 | 9.15 → 8.58 | 394 → 396 | 68.2% → 67.5% | 52.3% → 51.0% | 13.20 (3.26) → 7.89 (3.18) | 6.82 (1.25) → 10.33 (1.38) |
| 2034 (yr 8) | 1033 → 1032 | 7.72 → 9.43 | 88.8% → 92.6% | 11.16 → 11.04 | 3339 → 3310 | 8.99 → 8.36 | 394 → 396 | 69.5% → 68.1% | 53.8% → 52.0% | 13.59 (3.11) → 7.70 (3.11) | 8.20 (1.19) → 11.21 (1.26) |
| 2035 (yr 9) | 1037 → 1044 | 7.11 → 9.40 | 88.4% → 93.2% | 11.21 → 11.01 | 3499 → 3457 | 8.88 → 8.13 | 395 → 396 | 70.1% → 69.1% | 53.9% → 53.3% | 14.52 (3.25) → 8.59 (3.34) | 8.86 (1.17) → 11.97 (1.26) |
| 2036 (yr 10) | 1024 → 1028 | 6.58 → 9.15 | 85.8% → 94.1% | 11.35 → 11.11 | 3671 → 3608 | 8.80 → 8.08 | 396 → 395 | 71.1% → 70.4% | 56.1% → 55.4% | 15.16 (3.39) → 8.86 (3.51) | 9.49 (1.18) → 12.54 (1.27) |

Capacity trade-off (end-status, see the paragraph above the table): All regions, end-status 2036 (yr 10): member open starts per member 8.80 → 8.08; member shut-out weeks per member 9.49 → 12.54; college open starts per player 6.58 → 9.15.

### END-STATUS denominators: by series region, per season (old → new)

| series | season | college players | college open starts / player (home series) | college tier-5 / player | members | member open starts / member (home series) | member zero-start | events | fill | full | college shut out / player | member shut out / member |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NORTH_AMERICA | 2027 | 672 → 672 | 9.88 (8.48) → 10.59 (9.39) | 12.69 → 12.48 | 479 → 479 | 12.08 (12.08) → 11.27 (11.27) | 0.0% → 0.0% | 101 → 102 | 78.9% → 79.7% | 66.3% → 65.7% | 9.06 → 5.18 | 4.03 → 14.09 |
| NORTH_AMERICA | 2028 | 679 → 683 | 9.10 (7.68) → 10.11 (9.02) | 12.78 → 12.56 | 608 → 596 | 11.76 (11.76) → 10.83 (10.83) | 0.0% → 0.0% | 102 → 102 | 84.2% → 85.9% | 72.5% → 75.5% | 11.23 → 5.86 | 5.98 → 16.22 |
| NORTH_AMERICA | 2029 | 693 → 700 | 8.76 (7.18) → 9.66 (8.45) | 12.68 → 12.49 | 733 → 721 | 11.28 (11.28) → 10.30 (10.30) | 0.0% → 0.0% | 102 → 102 | 90.2% → 90.8% | 78.4% → 82.4% | 12.83 → 7.16 | 8.35 → 18.22 |
| NORTH_AMERICA | 2030 | 687 → 692 | 8.15 (6.42) → 9.23 (8.04) | 12.76 → 12.57 | 811 → 817 | 11.05 (11.05) → 9.91 (9.91) | 0.0% → 0.0% | 102 → 102 | 91.0% → 93.0% | 82.4% → 85.3% | 13.68 → 7.55 | 9.67 → 19.59 |
| NORTH_AMERICA | 2031 | 697 → 699 | 7.51 (5.52) → 8.96 (7.72) | 12.72 → 12.50 | 922 → 924 | 10.77 (10.77) → 9.42 (9.42) | 0.0% → 0.0% | 102 → 102 | 93.8% → 96.0% | 86.3% → 90.2% | 14.92 → 8.38 | 11.30 → 20.95 |
| NORTH_AMERICA | 2032 | 698 → 705 | 6.92 (5.05) → 8.70 (7.47) | 12.73 → 12.37 | 1033 → 1024 | 10.32 (10.32) → 8.91 (8.91) | 0.0% → 0.1% | 102 → 102 | 96.5% → 97.9% | 90.2% → 94.1% | 16.10 → 9.29 | 13.93 → 22.41 |
| NORTH_AMERICA | 2033 | 690 → 692 | 6.41 (4.43) → 8.43 (7.04) | 12.84 → 12.67 | 1141 → 1133 | 10.06 (10.06) → 8.58 (8.58) | 0.0% → 0.0% | 102 → 102 | 99.0% → 99.4% | 97.1% → 96.1% | 16.61 → 9.50 | 15.70 → 23.98 |
| NORTH_AMERICA | 2034 | 662 → 666 | 5.42 (3.55) → 8.00 (6.64) | 13.26 → 12.98 | 1255 → 1228 | 9.75 (9.74) → 8.24 (8.24) | 0.0% → 0.1% | 102 → 102 | 99.2% → 99.0% | 98.0% → 97.1% | 17.12 → 9.25 | 18.57 → 25.74 |
| NORTH_AMERICA | 2035 | 675 → 689 | 4.67 (2.64) → 8.06 (6.46) | 13.15 → 12.72 | 1338 → 1296 | 9.57 (9.57) → 7.90 (7.90) | 0.1% → 0.0% | 102 → 102 | 99.3% → 100.0% | 98.0% → 100.0% | 18.33 → 10.35 | 19.53 → 27.18 |
| NORTH_AMERICA | 2036 | 665 → 678 | 3.94 (1.97) → 7.62 (6.13) | 13.38 → 12.89 | 1424 → 1357 | 9.40 (9.40) → 7.76 (7.76) | 0.0% → 0.0% | 102 → 102 | 100.0% → 100.0% | 100.0% → 100.0% | 19.25 → 10.69 | 20.32 → 28.11 |
| EUROPE | 2027 | 188 → 188 | 14.54 (14.01) → 15.28 (14.86) | 5.88 → 5.57 | 487 → 487 | 9.25 (9.25) → 9.01 (9.01) | 0.0% → 0.0% | 113 → 114 | 46.9% → 46.3% | 27.4% → 23.7% | 4.36 → 2.59 | 0.09 → 0.95 |
| EUROPE | 2028 | 193 → 193 | 14.73 (14.16) → 15.46 (15.06) | 5.77 → 5.44 | 579 → 585 | 9.24 (9.24) → 9.01 (9.01) | 0.0% → 0.0% | 114 → 113 | 52.6% → 52.7% | 29.8% → 31.9% | 5.00 → 3.04 | 0.19 → 1.12 |
| EUROPE | 2029 | 173 → 174 | 13.66 (13.14) → 13.99 (13.66) | 6.51 → 6.40 | 676 → 675 | 8.87 (8.87) → 8.68 (8.68) | 0.0% → 0.0% | 114 → 114 | 54.6% → 53.2% | 31.6% → 32.5% | 5.01 → 2.78 | 0.34 → 1.07 |
| EUROPE | 2030 | 169 → 172 | 12.65 (12.25) → 13.16 (12.86) | 6.91 → 6.49 | 749 → 749 | 8.66 (8.66) → 8.39 (8.39) | 0.0% → 0.0% | 113 → 113 | 57.7% → 55.6% | 38.1% → 35.4% | 4.96 → 2.59 | 0.60 → 1.15 |
| EUROPE | 2031 | 182 → 191 | 12.14 (11.70) → 12.84 (12.46) | 7.02 → 6.70 | 819 → 825 | 8.46 (8.46) → 8.28 (8.28) | 0.0% → 0.0% | 114 → 114 | 60.4% → 59.5% | 40.4% → 40.4% | 5.57 → 3.37 | 0.91 → 1.53 |
| EUROPE | 2032 | 197 → 200 | 13.10 (12.52) → 13.07 (12.71) | 6.14 → 6.43 | 876 → 881 | 8.31 (8.31) → 8.17 (8.17) | 0.0% → 0.0% | 114 → 114 | 64.0% → 62.4% | 43.9% → 43.9% | 6.39 → 4.33 | 1.12 → 1.89 |
| EUROPE | 2033 | 188 → 191 | 13.09 (12.49) → 12.58 (12.16) | 6.33 → 6.81 | 935 → 947 | 8.24 (8.24) → 8.07 (8.07) | 0.0% → 0.0% | 114 → 114 | 65.9% → 64.1% | 47.4% → 43.9% | 6.72 → 4.41 | 1.30 → 2.04 |
| EUROPE | 2034 | 188 → 189 | 12.95 (12.40) → 12.49 (12.10) | 6.28 → 6.72 | 994 → 997 | 8.04 (8.04) → 7.95 (7.95) | 0.1% → 0.0% | 114 → 114 | 67.4% → 65.1% | 49.1% → 43.0% | 6.77 → 4.51 | 1.59 → 2.12 |
| EUROPE | 2035 | 187 → 186 | 12.26 (11.70) → 12.11 (11.69) | 6.91 → 7.00 | 1029 → 1040 | 7.94 (7.94) → 7.73 (7.73) | 0.0% → 0.0% | 114 → 114 | 68.7% → 65.6% | 50.0% → 43.9% | 6.90 → 4.62 | 1.68 → 2.20 |
| EUROPE | 2036 | 185 → 179 | 12.26 (11.86) → 12.79 (12.36) | 6.84 → 6.58 | 1074 → 1076 | 7.83 (7.83) → 7.78 (7.78) | 0.0% → 0.0% | 114 → 114 | 70.3% → 67.8% | 52.6% → 47.4% | 6.49 → 4.63 | 2.03 → 2.36 |
| ASIA | 2027 | 153 → 153 | 13.78 (13.56) → 14.33 (14.21) | 8.01 → 7.39 | 405 → 405 | 10.51 (10.51) → 10.41 (10.41) | 0.0% → 0.0% | 104 → 104 | 47.9% → 47.9% | 27.9% → 28.8% | 6.49 → 3.63 | 1.00 → 2.52 |
| ASIA | 2028 | 165 → 162 | 14.21 (14.00) → 14.44 (14.30) | 7.32 → 7.49 | 464 → 444 | 10.54 (10.54) → 10.40 (10.40) | 0.0% → 0.0% | 105 → 106 | 53.6% → 50.8% | 32.4% → 31.1% | 7.24 → 4.43 | 1.55 → 2.92 |
| ASIA | 2029 | 151 → 144 | 13.77 (13.47) → 14.25 (14.15) | 7.50 → 7.67 | 506 → 489 | 10.23 (10.23) → 10.13 (10.13) | 0.0% → 0.0% | 106 → 106 | 52.9% → 51.0% | 30.2% → 29.2% | 8.15 → 4.89 | 1.70 → 3.23 |
| ASIA | 2030 | 156 → 149 | 13.87 (13.57) → 13.80 (13.69) | 6.85 → 7.43 | 545 → 519 | 9.99 (9.99) → 9.94 (9.94) | 0.0% → 0.0% | 106 → 106 | 54.9% → 52.1% | 34.0% → 32.1% | 7.37 → 5.54 | 1.94 → 3.24 |
| ASIA | 2031 | 144 → 138 | 14.12 (13.82) → 13.54 (13.40) | 6.45 → 7.33 | 583 → 551 | 9.79 (9.79) → 9.76 (9.76) | 0.0% → 0.0% | 105 → 106 | 57.1% → 52.4% | 36.2% → 33.0% | 7.02 → 5.67 | 2.17 → 3.47 |
| ASIA | 2032 | 141 → 138 | 13.46 (13.23) → 13.31 (13.04) | 6.65 → 7.17 | 618 → 588 | 9.48 (9.48) → 9.64 (9.64) | 0.3% → 0.0% | 105 → 106 | 57.5% → 54.3% | 37.1% → 34.9% | 6.54 → 5.98 | 2.37 → 3.65 |
| ASIA | 2033 | 133 → 135 | 12.60 (12.32) → 12.92 (12.72) | 7.66 → 7.73 | 649 → 612 | 9.54 (9.54) → 9.73 (9.73) | 0.3% → 0.0% | 105 → 105 | 58.7% → 56.4% | 40.0% → 37.1% | 7.61 → 6.31 | 2.90 → 3.85 |
| ASIA | 2034 | 131 → 134 | 12.00 (11.73) → 12.23 (12.01) | 8.14 → 8.29 | 680 → 645 | 9.59 (9.59) → 9.65 (9.65) | 0.0% → 0.2% | 105 → 106 | 59.5% → 57.2% | 40.0% → 37.7% | 8.88 → 5.86 | 3.27 → 4.08 |
| ASIA | 2035 | 126 → 126 | 12.68 (12.21) → 12.46 (12.23) | 7.82 → 8.37 | 705 → 676 | 9.45 (9.45) → 9.52 (9.52) | 0.0% → 0.0% | 106 → 105 | 60.0% → 59.3% | 38.7% → 39.0% | 8.64 → 6.42 | 3.90 → 4.63 |
| ASIA | 2036 | 126 → 124 | 12.29 (11.68) → 12.22 (11.90) | 7.89 → 8.77 | 726 → 710 | 9.51 (9.51) → 9.51 (9.51) | 0.0% → 0.0% | 106 → 105 | 61.2% → 61.1% | 42.5% → 41.0% | 9.54 → 6.55 | 4.37 → 5.14 |
| OCEANIA | 2027 | 52 → 52 | 14.10 (12.92) → 13.77 (12.75) | 6.46 → 6.96 | 109 → 109 | 11.07 (11.07) → 11.14 (11.14) | 0.0% → 0.0% | 20 → 20 | 71.6% → 70.6% | 40.0% → 35.0% | 0.65 → 0.29 | 0.00 → 0.05 |
| OCEANIA | 2028 | 52 → 49 | 13.27 (11.44) → 14.12 (12.94) | 6.87 → 6.43 | 125 → 123 | 11.08 (11.08) → 11.05 (11.05) | 0.0% → 0.0% | 20 → 20 | 75.5% → 75.2% | 50.0% → 45.0% | 2.02 → 0.67 | 0.00 → 0.36 |
| OCEANIA | 2029 | 51 → 46 | 12.06 (9.94) → 12.89 (11.65) | 7.65 → 7.07 | 136 → 136 | 10.93 (10.93) → 10.85 (10.85) | 0.0% → 0.0% | 20 → 20 | 76.4% → 75.6% | 50.0% → 50.0% | 2.69 → 0.80 | 0.00 → 0.59 |
| OCEANIA | 2030 | 51 → 47 | 10.02 (8.51) → 10.06 (9.19) | 7.98 → 8.87 | 140 → 156 | 10.99 (10.99) → 10.50 (10.50) | 0.0% → 0.0% | 20 → 20 | 75.2% → 77.5% | 50.0% → 50.0% | 2.88 → 1.15 | 0.00 → 0.92 |
| OCEANIA | 2031 | 52 → 44 | 8.21 (6.60) → 10.75 (9.86) | 9.37 → 8.55 | 155 → 169 | 10.53 (10.53) → 10.09 (10.09) | 0.0% → 0.0% | 20 → 20 | 75.6% → 80.5% | 50.0% → 50.0% | 4.17 → 1.61 | 0.00 → 1.03 |
| OCEANIA | 2032 | 54 → 45 | 7.46 (6.04) → 10.69 (9.78) | 9.52 → 8.53 | 170 → 176 | 10.31 (10.31) → 10.15 (10.15) | 0.0% → 0.0% | 20 → 20 | 79.1% → 83.6% | 50.0% → 60.0% | 4.67 → 1.96 | 0.38 → 1.84 |
| OCEANIA | 2033 | 50 → 44 | 6.86 (5.66) → 10.27 (9.23) | 9.88 → 8.45 | 184 → 193 | 10.08 (10.08) → 9.60 (9.60) | 0.0% → 0.0% | 20 → 20 | 81.2% → 84.7% | 55.0% → 70.0% | 5.34 → 2.55 | 0.74 → 2.86 |
| OCEANIA | 2034 | 52 → 43 | 7.27 (5.71) → 9.56 (8.44) | 9.73 → 8.70 | 198 → 207 | 10.07 (10.07) → 9.03 (9.03) | 0.0% → 0.0% | 20 → 20 | 85.9% → 83.6% | 70.0% → 70.0% | 5.17 → 3.44 | 1.40 → 3.71 |
| OCEANIA | 2035 | 49 → 43 | 6.76 (4.84) → 10.09 (9.00) | 9.45 → 8.79 | 208 → 201 | 9.83 (9.83) → 9.09 (9.09) | 0.0% → 0.0% | 20 → 20 | 85.8% → 83.0% | 70.0% → 70.0% | 6.10 → 4.02 | 1.87 → 3.59 |
| OCEANIA | 2036 | 48 → 47 | 6.15 (3.88) → 9.26 (7.96) | 9.60 → 9.02 | 218 → 214 | 9.74 (9.74) → 8.76 (8.76) | 0.0% → 0.0% | 20 → 20 | 86.6% → 84.2% | 70.0% → 70.0% | 6.69 → 4.57 | 2.57 → 4.28 |
| AFRICA | 2027 | 0 → 0 | — (—) → — (—) | — → — | 69 → 69 | 7.90 (7.90) → 7.80 (7.80) | 0.0% → 0.0% | 30 → 30 | 18.1% → 17.4% | 0.0% → 0.0% | — → — | 0.00 → 0.00 |
| AFRICA | 2028 | 0 → 0 | — (—) → — (—) | — → — | 77 → 79 | 8.31 (8.31) → 7.99 (7.99) | 0.0% → 0.0% | 30 → 30 | 20.4% → 18.9% | 0.0% → 0.0% | — → — | 0.00 → 0.00 |
| AFRICA | 2029 | 0 → 0 | — (—) → — (—) | — → — | 88 → 94 | 7.88 (7.88) → 8.23 (8.23) | 0.0% → 0.0% | 32 → 30 | 21.3% → 22.9% | 0.0% → 0.0% | — → — | 0.00 → 0.00 |
| AFRICA | 2030 | 0 → 0 | — (—) → — (—) | — → — | 92 → 105 | 7.32 (7.32) → 8.10 (8.10) | 0.0% → 0.0% | 29 → 31 | 22.6% → 23.4% | 0.0% → 0.0% | — → — | 0.00 → 0.00 |
| AFRICA | 2031 | 0 → 0 | — (—) → — (—) | — → — | 102 → 123 | 7.28 (7.28) → 7.93 (7.93) | 0.0% → 0.0% | 32 → 32 | 23.5% → 26.6% | 0.0% → 0.0% | — → — | 0.00 → 0.00 |
| AFRICA | 2032 | 0 → 0 | — (—) → — (—) | — → — | 109 → 128 | 7.80 (7.80) → 8.27 (8.27) | 0.0% → 0.0% | 30 → 31 | 27.8% → 30.4% | 0.0% → 3.2% | — → — | 0.00 → 0.00 |
| AFRICA | 2033 | 0 → 0 | — (—) → — (—) | — → — | 106 → 132 | 7.49 (7.49) → 8.10 (8.10) | 0.0% → 0.8% | 30 → 32 | 25.7% → 30.6% | 0.0% → 3.1% | — → — | 0.00 → 0.00 |
| AFRICA | 2034 | 0 → 0 | — (—) → — (—) | — → — | 114 → 144 | 7.58 (7.58) → 7.94 (7.94) | 0.0% → 0.7% | 30 → 31 | 28.2% → 33.3% | 0.0% → 12.9% | — → — | 0.00 → 0.00 |
| AFRICA | 2035 | 0 → 0 | — (—) → — (—) | — → — | 122 → 150 | 7.87 (7.87) → 7.89 (7.89) | 0.0% → 0.0% | 30 → 32 | 30.4% → 33.8% | 3.3% → 12.5% | — → — | 0.00 → 0.01 |
| AFRICA | 2036 | 0 → 0 | — (—) → — (—) | — → — | 129 → 156 | 8.09 (8.09) → 7.95 (7.95) | 0.0% → 0.0% | 31 → 31 | 30.8% → 35.0% | 3.2% → 19.4% | — → — | 0.00 → 0.04 |
| LATAM | 2027 | 0 → 0 | — (—) → — (—) | — → — | 49 → 49 | 4.96 (4.96) → 4.86 (4.86) | 0.0% → 0.0% | 23 → 23 | 10.2% → 9.9% | 0.0% → 0.0% | — → — | 0.00 → 0.00 |
| LATAM | 2028 | 0 → 0 | — (—) → — (—) | — → — | 58 → 56 | 4.53 (4.53) → 4.46 (4.46) | 0.0% → 0.0% | 23 → 23 | 11.0% → 10.2% | 0.0% → 0.0% | — → — | 0.00 → 0.00 |
| LATAM | 2029 | 0 → 0 | — (—) → — (—) | — → — | 62 → 65 | 4.21 (4.21) → 4.22 (4.22) | 0.0% → 0.0% | 23 → 23 | 11.0% → 11.3% | 0.0% → 0.0% | — → — | 0.00 → 0.00 |
| LATAM | 2030 | 0 → 0 | — (—) → — (—) | — → — | 65 → 70 | 4.22 (4.22) → 4.01 (4.01) | 0.0% → 0.0% | 23 → 23 | 11.2% → 11.0% | 0.0% → 0.0% | — → — | 0.00 → 0.00 |
| LATAM | 2031 | 0 → 0 | — (—) → — (—) | — → — | 77 → 79 | 4.05 (4.05) → 4.06 (4.06) | 0.0% → 0.0% | 23 → 23 | 13.3% → 12.8% | 0.0% → 0.0% | — → — | 0.00 → 0.00 |
| LATAM | 2032 | 0 → 0 | — (—) → — (—) | — → — | 79 → 83 | 3.96 (3.96) → 4.18 (4.18) | 0.0% → 0.0% | 23 → 23 | 13.9% → 14.1% | 0.0% → 0.0% | — → — | 0.00 → 0.00 |
| LATAM | 2033 | 0 → 0 | — (—) → — (—) | — → — | 85 → 84 | 3.98 (3.98) → 4.29 (4.29) | 0.0% → 0.0% | 23 → 23 | 14.8% → 14.1% | 0.0% → 0.0% | — → — | 0.00 → 0.00 |
| LATAM | 2034 | 0 → 0 | — (—) → — (—) | — → — | 98 → 89 | 4.14 (4.14) → 4.22 (4.22) | 0.0% → 0.0% | 23 → 23 | 17.6% → 14.6% | 0.0% → 0.0% | — → — | 0.00 → 0.00 |
| LATAM | 2035 | 0 → 0 | — (—) → — (—) | — → — | 97 → 94 | 4.25 (4.25) → 4.20 (4.20) | 0.0% → 0.0% | 23 → 23 | 17.3% → 15.8% | 0.0% → 0.0% | — → — | 0.00 → 0.00 |
| LATAM | 2036 | 0 → 0 | — (—) → — (—) | — → — | 100 → 95 | 4.40 (4.40) → 4.24 (4.24) | 0.0% → 0.0% | 23 → 23 | 17.8% → 15.9% | 0.0% → 0.0% | — → — | 0.00 → 0.00 |

## 3. Two-seed bounded metrics: a18new (seed 4207) and seed2 (seed 5309), defaults

Seasons: a18new: seasons 2027–2036 (10); seed2: seasons 2027–2031 (5).

### National prestige and participation (season file `prestige.nations`)

Multiplier for the entrants of season Y+1, decided at Y's end (participation.py: bounds 0.25–4 of the starting value 1, at most ×1.10 or ÷1.10 a year). Step = this season's multiplier ÷ the previous (1.0 before the first). Share ratio = a nation's share ÷ its baseline share (juniors / new pros).

| arm | season | nations | multiplier range | nations moved >1% | step range | outside 0.25–4 / step beyond 1.1 | junior share ratio | new-pro share ratio |
|---|---|---|---|---|---|---|---|---|
| a18new | 2027 | 57 | 0.909–1.100 | 43 | 0.909–1.100 | 0 / 0 | 0.92–1.11 | 0.92–1.11 |
| a18new | 2028 | 57 | 0.826–1.210 | 45 | 0.909–1.100 | 0 / 0 | 0.83–1.21 | 0.83–1.21 |
| a18new | 2029 | 57 | 0.822–1.222 | 43 | 0.909–1.100 | 0 / 0 | 0.82–1.23 | 0.83–1.23 |
| a18new | 2030 | 57 | 0.799–1.344 | 44 | 0.909–1.100 | 0 / 0 | 0.80–1.34 | 0.80–1.34 |
| a18new | 2031 | 57 | 0.811–1.295 | 45 | 0.909–1.100 | 0 / 0 | 0.81–1.29 | 0.81–1.29 |
| a18new | 2032 | 57 | 0.850–1.360 | 43 | 0.930–1.095 | 0 / 0 | 0.85–1.36 | 0.85–1.36 |
| a18new | 2033 | 57 | 0.811–1.496 | 43 | 0.919–1.100 | 0 / 0 | 0.81–1.50 | 0.81–1.50 |
| a18new | 2034 | 57 | 0.825–1.376 | 42 | 0.909–1.100 | 0 / 0 | 0.83–1.38 | 0.83–1.38 |
| a18new | 2035 | 57 | 0.876–1.251 | 41 | 0.909–1.100 | 0 / 0 | 0.88–1.26 | 0.88–1.26 |
| a18new | 2036 | 57 | 0.868–1.262 | 40 | 0.944–1.100 | 0 / 0 | 0.87–1.27 | 0.87–1.27 |
| seed2 | 2027 | 57 | 0.909–1.100 | 44 | 0.909–1.100 | 0 / 0 | 0.91–1.10 | 0.91–1.10 |
| seed2 | 2028 | 57 | 0.826–1.210 | 49 | 0.909–1.100 | 0 / 0 | 0.83–1.21 | 0.83–1.21 |
| seed2 | 2029 | 57 | 0.849–1.177 | 50 | 0.909–1.100 | 0 / 0 | 0.85–1.18 | 0.85–1.18 |
| seed2 | 2030 | 57 | 0.795–1.112 | 46 | 0.917–1.100 | 0 / 0 | 0.80–1.12 | 0.80–1.12 |
| seed2 | 2031 | 57 | 0.802–1.115 | 51 | 0.909–1.100 | 0 / 0 | 0.80–1.12 | 0.80–1.12 |

- a18new after 2036: lowest multipliers Mexico 0.868, Brazil 0.881, Czechia 0.882; highest Italy 1.262, Denmark 1.169, Malaysia 1.153.
- seed2 after 2031: lowest multipliers Italy 0.802, Netherlands 0.817, India 0.847; highest Germany 1.115, Vietnam 1.108, Scotland 1.106.

Venue moves (`prestige.venue_moves_decided` at the season's end; `venue_moves`: every move decided so far):

| arm | season | decided this season | all decided so far |
|---|---|---|---|
| a18new | 2027 | 0 | 0 |
| a18new | 2028 | 0 | 0 |
| a18new | 2029 | 0 | 0 |
| a18new | 2030 | 0 | 0 |
| a18new | 2031 | 0 | 0 |
| a18new | 2032 | 0 | 0 |
| a18new | 2033 | 0 | 0 |
| a18new | 2034 | 0 | 0 |
| a18new | 2035 | 0 | 0 |
| a18new | 2036 | 0 | 0 |
| seed2 | 2027 | 0 | 0 |
| seed2 | 2028 | 0 | 0 |
| seed2 | 2029 | 0 | 0 |
| seed2 | 2030 | 0 | 0 |
| seed2 | 2031 | 0 | 0 |

**Venue moves: natural activation not exercised in these runs; calibration of the venue-move rule unexercised.** 0 moves were decided over the 15 default-arm seed-seasons (a18new 10, seed2 5). Positive regression evidence that moves do happen under the rule: tests/test_venue_moves.py — `test_sustained_gap_moves_two_seasons_later_and_never_touches_the_plan` (a gap held at three season ends moves the event two seasons later to a physically better eligible course in the same city, leaving the shared plan unchanged), `test_a_second_decision_is_added_not_overwritten` (two moves, decided in 2029 and 2039, both kept and in force by effective year) and `test_save_and_resume_keep_the_history` (two moves survive a save and resume).

Trigger funnel per season, reconstructed from retained data and the build's static course plan (Season.review_venues; no simulation): eligible = held this season, single-site series, not a major or qualifying stage; gap = archived event prestige − archived course prestige of the course it was played on (both as set at the season end, which review_venues reads) ≥ 5; sustained = that gap at 3 consecutive held season ends (counted from the world's first season, as `venue_watch` starts empty); cooldown = a move in the last 10 seasons (none were recorded, so it blocks nothing); candidate = a course in the same city that the event's level may use (course_library.LEVEL_LAYOUTS) and physically better (prestige.COURSE_QUALITY), not elite in a major week; free = not booked that week in season Y+2 and the event still planned at its current course then (with no moves in force, the world's venues equal the library plan `CourseLibrary.venues`, so this is reconstructable). The edition's week in season Y+2 comes from the static calendar.

| arm | season | eligible events held | gap ≥ 5 | sustained 3 season ends | blocked: cooldown | blocked: not at this course in Y+2 | blocked: no better eligible course in the city | blocked: better course booked that week | reconstructed: would move | moves recorded | gap within ±0.01 of 5 (unclassifiable) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| a18new | 2027 | 1434 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| a18new | 2028 | 1432 | 104 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| a18new | 2029 | 1432 | 103 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| a18new | 2030 | 1436 | 103 | 29 | 0 | 23 | 6 | 0 | 0 | 0 | 0 |
| a18new | 2031 | 1437 | 94 | 38 | 0 | 32 | 6 | 0 | 0 | 0 | 0 |
| a18new | 2032 | 1437 | 100 | 47 | 0 | 38 | 9 | 0 | 0 | 0 | 0 |
| a18new | 2033 | 1436 | 93 | 42 | 0 | 34 | 8 | 0 | 0 | 0 | 0 |
| a18new | 2034 | 1437 | 100 | 46 | 0 | 38 | 8 | 0 | 0 | 0 | 1 |
| a18new | 2035 | 1436 | 91 | 49 | 0 | 39 | 10 | 0 | 0 | 0 | 0 |
| a18new | 2036 | 1437 | 102 | 53 | 0 | 43 | 10 | 0 | 0 | 0 | 0 |
| seed2 | 2027 | 1429 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| seed2 | 2028 | 1429 | 102 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| seed2 | 2029 | 1435 | 105 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| seed2 | 2030 | 1434 | 101 | 28 | 0 | 22 | 6 | 0 | 0 | 0 | 1 |
| seed2 | 2031 | 1436 | 85 | 37 | 0 | 31 | 6 | 0 | 0 | 0 | 0 |

A nonzero "reconstructed: would move" alongside zero recorded moves would mean this reconstruction differs from the rule as run; the two columns are shown side by side for that check. Rounding: the archived event and course prestige are rounded to 0.01, so a gap within ±0.01 of the threshold cannot be classified with certainty; 2 eligible event-seasons fall in that band over these 15 seasons. Natural move frequency remains unvalidated; the positive fixtures in tests/test_venue_moves.py remain valid.

### Entrant allocation check (all arms, all committed seasons)

Source mapping: season Y's `prestige.nations` holds the entrants of season Y+1 (`entrant_year`): `totals`, `allocated`, `existing` and `shares` per pathway (participation.record, filled by population.entrant_rows). The actual arrivals of Y+1 are the next season file's `diagnostics.created` (Season.note_creation: path "junior" from careers.add_juniors, "late_entrant" from careers.add_new_professionals; "initial" is the starting world), joined to the people table's country (nationality, never changed). Checks per arm-season and pathway: (1) shares sum to 1 within n_nations × 0.5e-6 (each share rounded to 6 decimals; 57 nations: 2.85e-5); (2) allocations by nation sum to the pathway's total; (3) arrivals by nation equal the allocation; (4) the total is the same in arms with the same seed: population.entrant_rows takes it from `existing_rule(kind, year, seed, baseline)` over the nation profiles the world began with (careers._cohort_args: `participation.baseline`), so it depends on the pathway, year and seed only, not on the arm or the world's state.

- (1)+(2) allocation cells: juniors 35/35 pass; new_pros 35/35 pass.
- (3) arrival cells with a next archive season: 62/62 match by nation.
- Terminal cohorts (an arm's last season: no next archive season, so no `diagnostics.created`): a21old 2036→2037 juniors, a21old 2036→2037 new_pros, a18old 2036→2037 juniors, a18old 2036→2037 new_pros, a18new 2036→2037 juniors, a18new 2036→2037 new_pros, seed2 2031→2032 juniors, seed2 2031→2032 new_pros — not verified (the checkpoint was not opened).
- Supplementary, NOT counted as verified: the terminal cohorts from the people table's `created` year and the arrival ages the code defines (juniors 18: population.junior_class; new professionals 21–26: population.NEW_PRO_AGES). On the verified cohorts the age rule and the recorded path: junior agrees: 8831, late_entrant agrees: 13225. Terminal: a21old 2037 juniors: matches; a21old 2037 new_pros: matches; a18old 2037 juniors: matches; a18old 2037 new_pros: matches; a18new 2037 juniors: matches; a18new 2037 new_pros: matches; seed2 2032 juniors: matches; seed2 2032 new_pros: matches.
- (4) totals across same-seed arms: 20/20 (pathway, entrant year) comparisons identical.

### Recruitment (relations table: stints and refusals)

Staff-initiated offers = stints started by a coach or caddie (accepted) + refusals asked by a coach or caddie (turned down), by the year the approach was made, within the committed seasons (the winter after a season is recorded in that season's year, week 53). Coach arrangement "share" = youth scouting (a share of future prize money), "fee" = an approach to an established player. The first year includes the approaches made as the world starts (week 1).

**a18new**

| year | coach offers | coach accepted: share / fee | coach accepted / offers | coach refused | caddie offers | caddie accepted | caddie accepted / offers | caddie refused | golfer-initiated coach stints | golfer-initiated caddie stints |
|---|---|---|---|---|---|---|---|---|---|---|
| 2027 | 534 | 331 / 93 | 424/534 (79.4%) | 110 | 1043 | 312 | 312/1043 (29.9%) | 731 | 1709 | 865 |
| 2028 | 255 | 118 / 17 | 135/255 (52.9%) | 120 | 502 | 57 | 57/502 (11.4%) | 445 | 675 | 148 |
| 2029 | 280 | 125 / 7 | 132/280 (47.1%) | 148 | 528 | 56 | 56/528 (10.6%) | 472 | 589 | 137 |
| 2030 | 315 | 133 / 10 | 143/315 (45.4%) | 172 | 506 | 58 | 58/506 (11.5%) | 448 | 712 | 122 |
| 2031 | 296 | 126 / 11 | 137/296 (46.3%) | 159 | 540 | 82 | 82/540 (15.2%) | 458 | 725 | 111 |
| 2032 | 340 | 154 / 8 | 162/340 (47.6%) | 178 | 526 | 39 | 39/526 (7.4%) | 487 | 724 | 143 |
| 2033 | 361 | 145 / 4 | 149/361 (41.3%) | 212 | 530 | 97 | 97/530 (18.3%) | 433 | 792 | 100 |
| 2034 | 345 | 138 / 6 | 144/345 (41.7%) | 201 | 514 | 87 | 87/514 (16.9%) | 427 | 743 | 105 |
| 2035 | 333 | 139 / 5 | 144/333 (43.2%) | 189 | 487 | 63 | 63/487 (12.9%) | 424 | 880 | 116 |
| 2036 | 323 | 144 / 3 | 147/323 (45.5%) | 176 | 460 | 76 | 76/460 (16.5%) | 384 | 872 | 103 |

Reasons accepted (top): coach — a share deal costs nothing now: 1123; caddie — a caddie they could afford: 865; coach — a share deal costs nothing now; a well-known coach: 357; coach — a well-known coach: 122; coach — a coach who sought them out: 27; caddie — had worked well together before: 16

Reasons refused (top): caddie — could not afford their fee: 1728; coach — happy with their college team's coaching: 278; caddie — stayed with Ryo Fujita: a strong working relationship, progress togeth: 256; coach — the coach was not well known: 215; caddie — expected a better-known caddie: 211; coach — could not afford the fee: 188; caddie — stayed with Ryo Fujita: a strong working relationship, a good fit, pro: 108; caddie — stayed with Steven Price: a strong working relationship, progress toge: 84

**seed2**

| year | coach offers | coach accepted: share / fee | coach accepted / offers | coach refused | caddie offers | caddie accepted | caddie accepted / offers | caddie refused | golfer-initiated coach stints | golfer-initiated caddie stints |
|---|---|---|---|---|---|---|---|---|---|---|
| 2027 | 526 | 327 / 89 | 416/526 (79.1%) | 110 | 1154 | 348 | 348/1154 (30.2%) | 806 | 1719 | 850 |
| 2028 | 247 | 134 / 13 | 147/247 (59.5%) | 100 | 511 | 69 | 69/511 (13.5%) | 442 | 688 | 131 |
| 2029 | 317 | 138 / 11 | 149/317 (47.0%) | 168 | 533 | 94 | 94/533 (17.6%) | 439 | 595 | 110 |
| 2030 | 367 | 143 / 3 | 146/367 (39.8%) | 221 | 557 | 73 | 73/557 (13.1%) | 484 | 740 | 119 |
| 2031 | 378 | 153 / 14 | 167/378 (44.2%) | 211 | 519 | 79 | 79/519 (15.2%) | 440 | 748 | 102 |

Reasons accepted (top): caddie — a caddie they could afford: 633; coach — a share deal costs nothing now: 610; coach — a share deal costs nothing now; a well-known coach: 260; coach — a well-known coach: 104; coach — a coach who sought them out: 22; caddie — had worked well together before: 7

Reasons refused (top): caddie — could not afford their fee: 1593; coach — happy with their college team's coaching: 166; caddie — stayed with Blake Ashby: a strong working relationship, progress toget: 116; coach — could not afford the fee: 104; coach — the coach was not well known: 88; caddie — expected a better-known caddie: 84; caddie — stayed with Chang-min Son: a strong working relationship, progress tog: 69; caddie — stayed with Sadom Srisuk: a strong working relationship, progress toge: 64

### Weather (round conditions in the season files)

Each round of each event site: [wind mph, wet 0/1, pins, wind from, gustiness] (weather.archived). Climate group and hemisphere from the course's city (weather.climate_of, the build's course library; the city recorded with the site otherwise); local month = the calendar month of the event week, six months on for southern-hemisphere courses (the climate table's convention). All tiers.

**a18new**: 40,133 rounds; wind mph 0.0 / 5.8 / 9.0 / 12.8 / 44.6 (n=40133); wet 16.1%; gustiness 0.05 / 0.08 / 0.13 / 0.18 / 0.45 (n=40133); gustiness not recorded on 0 rounds.

mean wind (mph), by climate group × local month:

| climate | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alpine | · | · | · | · | · | 9.0 | 8.3 | 8.8 | 8.6 | · | · | · |
| continental | · | · | · | 9.1 | 7.8 | 7.5 | 6.5 | 6.6 | 7.3 | 7.5 | · | · |
| desert | 9.9 | 10.6 | 12.1 | 13.1 | 13.0 | · | 12.3 | 12.5 | · | 8.8 | 10.0 | 9.2 |
| mediterranean | 12.1 | 12.1 | 10.3 | 10.3 | 10.8 | 10.1 | 10.1 | 10.1 | 9.8 | 8.8 | 10.0 | 10.6 |
| oceanic | · | · | · | 11.0 | 10.7 | 10.0 | 10.2 | 10.3 | 10.8 | 12.9 | · | · |
| subtropical | 9.7 | 10.2 | 11.8 | 11.6 | 9.2 | 8.9 | 8.0 | 8.8 | 8.9 | 9.2 | 9.5 | 10.5 |
| temperate | · | · | 10.1 | 10.2 | 8.5 | 8.0 | 7.8 | 7.4 | 8.4 | 8.7 | 8.5 | · |
| tropical | 11.7 | 12.9 | 12.0 | 11.2 | 9.9 | 10.7 | 11.4 | 10.3 | 9.9 | 9.6 | 9.6 | 11.2 |

wet rounds (%), by climate group × local month:

| climate | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alpine | · | · | · | · | · | 16 | 23 | 16 | 12 | · | · | · |
| continental | · | · | · | 18 | 21 | 19 | 21 | 17 | 16 | 11 | · | · |
| desert | 5 | 6 | 5 | 3 | 1 | · | 3 | 2 | · | 3 | 5 | 9 |
| mediterranean | 21 | 20 | 17 | 10 | 9 | 4 | 3 | 2 | 6 | 13 | 16 | 19 |
| oceanic | · | · | · | 20 | 21 | 20 | 17 | 22 | 22 | 26 | · | · |
| subtropical | 13 | 11 | 13 | 12 | 15 | 25 | 24 | 21 | 17 | 12 | 9 | 11 |
| temperate | · | · | 13 | 17 | 18 | 22 | 22 | 22 | 20 | 14 | 11 | · |
| tropical | 8 | 8 | 9 | 13 | 24 | 32 | 26 | 30 | 32 | 22 | 15 | 8 |

mean gustiness, by climate group × local month:

| climate | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alpine | · | · | · | · | · | 0.08 | 0.08 | 0.08 | 0.08 | · | · | · |
| continental | · | · | · | 0.15 | 0.12 | 0.10 | 0.09 | 0.08 | 0.09 | 0.10 | · | · |
| desert | 0.12 | 0.14 | 0.16 | 0.17 | 0.15 | · | 0.18 | 0.15 | · | 0.10 | 0.12 | 0.12 |
| mediterranean | 0.19 | 0.18 | 0.18 | 0.15 | 0.16 | 0.15 | 0.15 | 0.14 | 0.15 | 0.14 | 0.16 | 0.18 |
| oceanic | · | · | · | 0.14 | 0.13 | 0.11 | 0.11 | 0.12 | 0.13 | 0.15 | · | · |
| subtropical | 0.14 | 0.15 | 0.18 | 0.17 | 0.13 | 0.12 | 0.10 | 0.11 | 0.12 | 0.13 | 0.14 | 0.14 |
| temperate | · | · | 0.16 | 0.17 | 0.13 | 0.11 | 0.11 | 0.11 | 0.12 | 0.12 | 0.13 | · |
| tropical | 0.19 | 0.21 | 0.19 | 0.16 | 0.15 | 0.17 | 0.15 | 0.16 | 0.14 | 0.13 | 0.14 | 0.16 |

rounds, by climate group × local month:

| climate | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alpine | · | · | · | · | · | 25 | 44 | 75 | 34 | · | · | · |
| continental | · | · | · | 706 | 894 | 1017 | 1099 | 931 | 971 | 472 | · | · |
| desert | 308 | 473 | 226 | 429 | 163 | · | 38 | 138 | · | 306 | 295 | 96 |
| mediterranean | 207 | 425 | 517 | 352 | 444 | 296 | 583 | 245 | 275 | 499 | 444 | 145 |
| oceanic | · | · | · | 925 | 717 | 1017 | 1356 | 871 | 731 | 753 | · | · |
| subtropical | 770 | 1240 | 1016 | 1010 | 904 | 709 | 1037 | 773 | 804 | 1175 | 1006 | 445 |
| temperate | · | · | 365 | 710 | 597 | 461 | 611 | 372 | 629 | 787 | 429 | · |
| tropical | 373 | 541 | 396 | 346 | 307 | 253 | 651 | 455 | 326 | 473 | 396 | 224 |

By calendar month (all courses): J 10.1 mph/15% wet, F 10.8 mph/12% wet, M 10.9 mph/14% wet, A 10.6 mph/14% wet, M 9.3 mph/17% wet, J 8.8 mph/21% wet, J 8.8 mph/19% wet, A 8.9 mph/20% wet, S 9.1 mph/18% wet, O 9.8 mph/15% wet, N 9.6 mph/12% wet, D 10.4 mph/13% wet.

**seed2**: 20,033 rounds; wind mph 0.0 / 5.9 / 9.1 / 12.9 / 38.9 (n=20033); wet 15.0%; gustiness 0.05 / 0.08 / 0.13 / 0.17 / 0.45 (n=20033); gustiness not recorded on 0 rounds.

mean wind (mph), by climate group × local month:

| climate | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alpine | · | · | · | · | · | 7.6 | 6.0 | 6.5 | 11.1 | · | · | · |
| continental | · | · | · | 9.4 | 8.6 | 7.3 | 6.8 | 6.9 | 7.1 | 7.8 | · | · |
| desert | 11.1 | 11.1 | 13.3 | 12.1 | 11.0 | · | 14.9 | 11.1 | · | 9.5 | 11.4 | 10.5 |
| mediterranean | 11.5 | 11.1 | 11.8 | 9.6 | 10.7 | 10.0 | 9.8 | 9.8 | 9.0 | 9.1 | 10.2 | 13.9 |
| oceanic | · | · | · | 10.7 | 11.4 | 10.9 | 10.1 | 10.4 | 11.4 | 13.1 | · | · |
| subtropical | 9.9 | 9.9 | 11.5 | 11.2 | 9.2 | 8.8 | 8.5 | 8.4 | 9.0 | 9.5 | 9.9 | 10.4 |
| temperate | · | · | 9.8 | 9.9 | 8.2 | 8.1 | 7.1 | 8.1 | 8.2 | 8.5 | 7.8 | · |
| tropical | 13.2 | 12.5 | 11.2 | 11.4 | 10.9 | 11.4 | 11.0 | 11.2 | 10.7 | 10.2 | 9.4 | 10.1 |

wet rounds (%), by climate group × local month:

| climate | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alpine | · | · | · | · | · | 33 | 10 | 8 | 23 | · | · | · |
| continental | · | · | · | 21 | 19 | 14 | 17 | 16 | 18 | 15 | · | · |
| desert | 4 | 4 | 5 | 2 | 2 | · | 11 | 1 | · | 3 | 3 | 7 |
| mediterranean | 21 | 20 | 17 | 13 | 5 | 3 | 1 | 2 | 6 | 12 | 17 | 15 |
| oceanic | · | · | · | 21 | 18 | 18 | 19 | 20 | 23 | 29 | · | · |
| subtropical | 8 | 12 | 14 | 10 | 12 | 21 | 22 | 20 | 18 | 12 | 9 | 7 |
| temperate | · | · | 13 | 13 | 22 | 16 | 19 | 12 | 17 | 14 | 12 | · |
| tropical | 5 | 4 | 9 | 16 | 25 | 26 | 25 | 27 | 23 | 19 | 14 | 12 |

mean gustiness, by climate group × local month:

| climate | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alpine | · | · | · | · | · | 0.11 | 0.07 | 0.07 | 0.10 | · | · | · |
| continental | · | · | · | 0.15 | 0.12 | 0.09 | 0.08 | 0.08 | 0.09 | 0.12 | · | · |
| desert | 0.12 | 0.13 | 0.16 | 0.17 | 0.16 | · | 0.20 | 0.15 | · | 0.10 | 0.12 | 0.15 |
| mediterranean | 0.21 | 0.18 | 0.18 | 0.16 | 0.14 | 0.15 | 0.15 | 0.14 | 0.15 | 0.14 | 0.16 | 0.20 |
| oceanic | · | · | · | 0.14 | 0.13 | 0.11 | 0.10 | 0.11 | 0.13 | 0.15 | · | · |
| subtropical | 0.14 | 0.15 | 0.18 | 0.17 | 0.13 | 0.11 | 0.10 | 0.11 | 0.12 | 0.12 | 0.13 | 0.14 |
| temperate | · | · | 0.16 | 0.17 | 0.13 | 0.11 | 0.10 | 0.10 | 0.12 | 0.12 | 0.13 | · |
| tropical | 0.19 | 0.20 | 0.19 | 0.17 | 0.14 | 0.17 | 0.16 | 0.15 | 0.13 | 0.13 | 0.13 | 0.16 |

rounds, by climate group × local month:

| climate | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alpine | · | · | · | · | · | 12 | 20 | 40 | 13 | · | · | · |
| continental | · | · | · | 347 | 440 | 517 | 549 | 473 | 488 | 221 | · | · |
| desert | 159 | 234 | 111 | 207 | 81 | · | 19 | 69 | · | 152 | 140 | 46 |
| mediterranean | 104 | 208 | 257 | 171 | 208 | 143 | 292 | 124 | 138 | 245 | 218 | 71 |
| oceanic | · | · | · | 468 | 356 | 498 | 675 | 429 | 375 | 381 | · | · |
| subtropical | 383 | 627 | 519 | 507 | 466 | 359 | 511 | 379 | 401 | 580 | 513 | 217 |
| temperate | · | · | 189 | 363 | 302 | 230 | 305 | 187 | 304 | 403 | 204 | · |
| tropical | 187 | 270 | 184 | 167 | 154 | 125 | 335 | 231 | 166 | 248 | 198 | 120 |

By calendar month (all courses): J 10.5 mph/12% wet, F 10.5 mph/11% wet, M 11.1 mph/14% wet, A 10.5 mph/14% wet, M 9.7 mph/16% wet, J 9.1 mph/16% wet, J 8.8 mph/17% wet, A 9.0 mph/18% wet, S 9.2 mph/18% wet, O 10.0 mph/16% wet, N 9.7 mph/12% wet, D 10.6 mph/13% wet.

### Familiarity: regional baseline and home-club floor

Baseline starts = season file `familiar_base` (starts where the regional baseline, home-club floor included, exceeded the rounds played there: Season.course_baseline vs the golfer's familiarity). The home-club floor is not recorded separately per start: "starts at a by-country home club" counts starts at the golfer's home club of that date when the club was found by country (the only case where the floor can add anything; it applies there only while fewer than 3 rounds were played) — an upper bound. Golfers whose current home-club familiarity comes from the floor (`home_club_familiarity.from` = "home club") are counted from the latest people table (state at the last committed season only).

| arm | season | starts | baseline applied | golfers with any | starts at a by-country home club | golfers |
|---|---|---|---|---|---|---|
| a18new | 2027 | 124,224 | 6799/124224 (5.5%) | 3,899 of 6,405 | 10 | 6 |
| a18new | 2028 | 126,488 | 5139/126488 (4.1%) | 3,291 of 6,878 | 9 | 6 |
| a18new | 2029 | 126,529 | 4497/126529 (3.6%) | 2,971 of 7,299 | 11 | 7 |
| a18new | 2030 | 127,650 | 3950/127650 (3.1%) | 2,751 of 7,738 | 14 | 6 |
| a18new | 2031 | 129,189 | 3612/129189 (2.8%) | 2,592 of 8,190 | 10 | 5 |
| a18new | 2032 | 131,156 | 3383/131156 (2.6%) | 2,432 of 8,632 | 8 | 5 |
| a18new | 2033 | 133,196 | 3468/133196 (2.6%) | 2,443 of 9,050 | 12 | 6 |
| a18new | 2034 | 133,874 | 3160/133874 (2.4%) | 2,302 of 9,359 | 10 | 6 |
| a18new | 2035 | 135,673 | 3428/135673 (2.5%) | 2,463 of 9,726 | 9 | 5 |
| a18new | 2036 | 136,868 | 3007/136868 (2.2%) | 2,229 of 10,008 | 12 | 6 |
| seed2 | 2027 | 124,319 | 6665/124319 (5.4%) | 3,829 of 6,389 | 6 | 5 |
| seed2 | 2028 | 126,945 | 5261/126945 (4.1%) | 3,405 of 6,913 | 15 | 6 |
| seed2 | 2029 | 128,414 | 4423/128414 (3.4%) | 2,961 of 7,426 | 14 | 6 |
| seed2 | 2030 | 129,178 | 4081/129178 (3.2%) | 2,841 of 7,861 | 10 | 6 |
| seed2 | 2031 | 130,506 | 3658/130506 (2.8%) | 2,608 of 8,333 | 4 | 2 |

- a18new (people table people.g000010.json.gz): golfers with a home club recorded (retired included) 13,465; found by country 16/13465 (0.1%); current home-club familiarity from: region 8506, played 4956, home club 3
- seed2 (people table people.g000005.json.gz): golfers with a home club recorded (retired included) 10,132; found by country 14/10132 (0.1%); current home-club familiarity from: region 7171, played 2958, home club 3

## 4. Story timing on the pinned long archive (run A, 45 seasons, build 473690a)

**Scope and how it was measured.** This is evidence for indexed story assembly only: the benchmark calls `observer_stories.tell` (facts assembly plus narration) through the observer's read-only history; it does not cover full UI page rendering and was not run on the owner's hardware. "Cold" means application-cache cold (an empty story cache and no decoded season in the process), not filesystem cold: the season files may have been in the operating system's page cache. The sample is 20 majors spread over the legacy 473690a 45-season archive (run A), assembled by the candidate build's (c0d1ea5) assembler. Figures from story_timing.json: cold median 7.44 s, max 11.85 s; with the story index built, median 0.103 s; the latest edition opened first: 3.08 s with its facts marked pending, then 102 s of background story indexing; the separate one-off read-only side index: 218 s, 1.05 GB.

**Memory.** The 2.65 GB RSS is the timing process's lifetime high-water mark (ru_maxrss), reached as decoded seasons accumulated up to the archive's cache bound; it is not a per-story allocation and does not show the absence of a leak. **Rounding:** a time shown as 0.000 s is below the timer's displayed precision, not zero.

**Missing estimates.** The missing pre-event win estimates (so no upset is claimed in these stories) are a limit of the legacy archive, which predates them; upset-story behaviour in new worlds is covered separately by the test suite (tests/test_upset_examples.py, e.g. `test_no_upset_is_claimed_and_the_missing_estimate_is_named`; tests/test_stories.py, e.g. `test_upset_only_with_a_recorded_estimate`, `test_upset_text_states_the_estimate`).

**Not claimed.** This section does not claim instant cold opens in the UI, and does not claim the local 120 s season target is verified.

Archive: `runs/A/world_360013/archive` (seasons 2027–2071, 45 seasons, archive build 473690a); story code: the candidate build `arms/build_c0d1ea5`. Read through a mirror of its MANIFEST and links to the files it names (`armsan/story_mirror/60e05d28ff57/archive`); its own index.sqlite was never opened. Measured 2026-10-31 11:03:14–2026-10-31 11:11:10 UTC with `nice -n 19` while two simulations ran on the same 4-CPU machine (times include that contention).

- One-off side index of the read-only history (golfsim.archive.build_index_at, as the observer builds for a history it does not own): built in 218 s, 1.05 GB, child peak 402 MB.
- Opening the history read-only (observer.World): 6.04 s, RSS 502 MB.
- After pass 1 a background story indexer was not running (none was needed); largest child process peak so far 758 MB.
- Latest edition opened first in an empty story cache (2071:BRITANNIA_OPEN): 3.079 s, facts waiting for the story index (not kept); the background story indexer then took 102.0 s (finished: True; largest child peak 758 MB); reopened afterwards: 0.076 s.
- Passes 1–4 below open the sample oldest first, so each cold story found at most two seasons unindexed and indexed them inline (INLINE_SEASONS = 2); the observer keeps up to 4 decoded seasons in memory (archive.Archive.CACHE_SEASONS), which is what the process RSS climbs to.

| pass | editions | min s | median s | max s | total s | facts pending (not cached) | process peak RSS MB |
|---|---|---|---|---|---|---|---|
| 1 cold, as first opened | 20 | 1.973 | 7.442 | 11.850 | 143.7 | 0 | 2646 |
| 2 cold facts, story index complete | 20 | 0.072 | 0.103 | 0.273 | 2.3 | 0 | 2646 |
| 3 warm (disk) | 20 | 0.001 | 0.001 | 0.002 | 0.0 | 0 | 2646 |
| 4 warm (memory) | 20 | 0.000 | 0.000 | 0.000 | 0.0 | 0 | 2646 |

Per edition (seconds: pass 1 / 2 / 3 / 4):

| edition | pass 1 | pass 2 | pass 3 | pass 4 | RSS after pass 1 (MB) |
|---|---|---|---|---|---|
| 2027:TOUR_MASTERS | 1.973 | 0.082 | 0.001 | 0.000 | 684 |
| 2029:PREMIER_TOUR_CHAMPIONSHIP | 5.052 | 0.089 | 0.001 | 0.000 | 1170 |
| 2032:USA_OPEN | 7.263 | 0.074 | 0.001 | 0.000 | 1518 |
| 2034:BRITANNIA_OPEN | 6.209 | 0.082 | 0.001 | 0.000 | 1574 |
| 2036:TOUR_MASTERS | 4.035 | 0.072 | 0.001 | 0.000 | 1746 |
| 2039:PREMIER_TOUR_CHAMPIONSHIP | 8.525 | 0.077 | 0.001 | 0.000 | 1783 |
| 2041:USA_OPEN | 5.752 | 0.182 | 0.001 | 0.000 | 1909 |
| 2043:BRITANNIA_OPEN | 6.292 | 0.128 | 0.001 | 0.000 | 1941 |
| 2046:TOUR_MASTERS | 9.300 | 0.078 | 0.001 | 0.000 | 2059 |
| 2048:PREMIER_TOUR_CHAMPIONSHIP | 6.751 | 0.109 | 0.001 | 0.000 | 2087 |
| 2050:USA_OPEN | 5.177 | 0.092 | 0.001 | 0.000 | 2141 |
| 2052:BRITANNIA_OPEN | 7.621 | 0.124 | 0.001 | 0.000 | 2182 |
| 2055:TOUR_MASTERS | 10.983 | 0.109 | 0.001 | 0.000 | 2196 |
| 2057:PREMIER_TOUR_CHAMPIONSHIP | 7.980 | 0.137 | 0.001 | 0.000 | 2234 |
| 2059:USA_OPEN | 8.101 | 0.126 | 0.001 | 0.000 | 2263 |
| 2062:BRITANNIA_OPEN | 10.036 | 0.096 | 0.001 | 0.000 | 2319 |
| 2064:TOUR_MASTERS | 4.914 | 0.125 | 0.001 | 0.000 | 2345 |
| 2066:PREMIER_TOUR_CHAMPIONSHIP | 8.220 | 0.118 | 0.001 | 0.000 | 2392 |
| 2069:USA_OPEN | 11.850 | 0.273 | 0.002 | 0.000 | 2428 |
| 2071:BRITANNIA_OPEN | 7.681 | 0.094 | 0.001 | 0.000 | 2472 |

Story cache on disk after the sample: 115.8 MB. Patterns of the sampled stories: comeback 10, close_finish 5, playoff 3, wire_to_wire 3, runaway 2.

Facts the sampled stories list as not recorded (`missing`, pass 2; editions of the 45-season archive built by 473690a, which predates some facts the candidate records):

- a pre-event win estimate (not recorded: played before estimates were kept, and none is worked out afterwards), so no upset is claimed: 20 of 20 editions
- results before the world began in 2027 (counts are of the retained history): 5 of 20 editions

## 5. Amateur return and re-block (D5.c), all four arms

Sources (the build's own records, read from the season files): **episodes** are the winter transitions "amateur returned to full-time golf" in season Y's `transitions` (careers.decide: `note(AR.KIND, …)` after a successful draw), effective in season Y+1, with the age recorded at the decision; **evaluations** are every `amateur_return` row of decision evidence /2 (`careers` part): careers.decide records one for every part-time non-college amateur it evaluates, including p = 0 (a blocking condition: work, funds or results; no draw then). Return rates use all evaluations as the denominator, and separately the eligible ones (p > 0); the denominator is never limited to former pathway entrants. For each episode whose season Y+1 is archived: any cash-blocked week in Y+1 (season file `cash_blocked_max` ≥ 1: only a genuinely unaffordable week adds to it), a work-pathway re-entry in Y+1 (`work_pathway`; entries whose in-season count stayed below 8 used a count carried over), a winter "amateur took a job" decision after Y+1, starts in Y+1 (`careers.events`), and the competing outcomes of the winter after Y+1 (turned pro or comeback, retired, became coach or caddie, death in that winter from the people table). Returns in an arm's last season have no archived Y+1: they are **censored**, counted separately, never as successes. Episodes are not independent people: a golfer can return more than once, so unique people are counted separately. Age bands by age at the decision.

**a21old** (a21old: seasons 2027–2036 (10); censored = returns decided in 2036)

| band | evaluations (all, p = 0 included) | eligible (p > 0) | returns (episodes) | returns / all evaluations | returns / eligible | unique people | censored (no archived Y+1) | any cash-blocked week in Y+1 | pathway re-entry in Y+1 (count carried) | winter "took a job" after Y+1 | starts in Y+1 (min/q1/med/q3/max) | turned pro / comeback | retired | became staff | died |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 18–20 | 11 | 4 | 2 | 2/11 (18.18%) | 2/4 (50.0%) | 2 | 0/2 (0.0%) | 0/2 (0.0%) | 0/2 (0.0%) (0) | 0/2 (0.0%) | 17 / 17 / 18 / 18 / 18 (n=2) | 0/2 (0.0%) | 0/2 (0.0%) | 0/2 (0.0%) | 0/2 (0.0%) |
| 21–24 | 2977 | 809 | 213 | 213/2977 (7.15%) | 213/809 (26.3%) | 213 | 23/213 (10.8%) | 0/190 (0.0%) | 0/190 (0.0%) (0) | 77/190 (40.5%) | 11 / 15 / 17 / 17 / 19 (n=190) | 5/190 (2.6%) | 0/190 (0.0%) | 0/190 (0.0%) | 0/190 (0.0%) |
| 25–29 | 7247 | 2324 | 128 | 128/7247 (1.77%) | 128/2324 (5.5%) | 125 | 18/128 (14.1%) | 0/110 (0.0%) | 0/110 (0.0%) (0) | 76/110 (69.1%) | 12 / 15 / 16 / 17 / 20 (n=110) | 5/110 (4.5%) | 0/110 (0.0%) | 0/110 (0.0%) | 0/110 (0.0%) |
| 30+ | 11408 | 1372 | 3 | 3/11408 (0.03%) | 3/1372 (0.2%) | 3 | 1/3 (33.3%) | 0/2 (0.0%) | 0/2 (0.0%) (0) | 2/2 (100.0%) | 17 / 17 / 17 / 17 / 17 (n=2) | 0/2 (0.0%) | 0/2 (0.0%) | 0/2 (0.0%) | 0/2 (0.0%) |
| all | 21643 | 4509 | 346 | 346/21643 (1.60%) | 346/4509 (7.7%) | 333 | 42/346 (12.1%) | 0/304 (0.0%) | 0/304 (0.0%) (0) | 155/304 (51.0%) | 11 / 15 / 16 / 17 / 20 (n=304) | 10/304 (3.3%) | 0/304 (0.0%) | 0/304 (0.0%) | 0/304 (0.0%) |

**a18old** (a18old: seasons 2027–2036 (10); censored = returns decided in 2036)

| band | evaluations (all, p = 0 included) | eligible (p > 0) | returns (episodes) | returns / all evaluations | returns / eligible | unique people | censored (no archived Y+1) | any cash-blocked week in Y+1 | pathway re-entry in Y+1 (count carried) | winter "took a job" after Y+1 | starts in Y+1 (min/q1/med/q3/max) | turned pro / comeback | retired | became staff | died |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 18–20 | 66 | 1 | 1 | 1/66 (1.52%) | 1/1 (100.0%) | 1 | 0/1 (0.0%) | 0/1 (0.0%) | 0/1 (0.0%) (0) | 0/1 (0.0%) | 17 / 17 / 17 / 17 / 17 (n=1) | 0/1 (0.0%) | 0/1 (0.0%) | 0/1 (0.0%) | 0/1 (0.0%) |
| 21–24 | 2989 | 802 | 189 | 189/2989 (6.32%) | 189/802 (23.6%) | 189 | 20/189 (10.6%) | 0/169 (0.0%) | 0/169 (0.0%) (0) | 54/169 (32.0%) | 10 / 16 / 17 / 17 / 19 (n=169) | 6/169 (3.6%) | 0/169 (0.0%) | 0/169 (0.0%) | 0/169 (0.0%) |
| 25–29 | 7216 | 2366 | 136 | 136/7216 (1.88%) | 136/2366 (5.7%) | 136 | 14/136 (10.3%) | 0/122 (0.0%) | 0/122 (0.0%) (0) | 84/122 (68.9%) | 11 / 14 / 16 / 17 / 18 (n=122) | 1/122 (0.8%) | 0/122 (0.0%) | 0/122 (0.0%) | 0/122 (0.0%) |
| 30+ | 11457 | 1280 | 2 | 2/11457 (0.02%) | 2/1280 (0.2%) | 2 | 0/2 (0.0%) | 0/2 (0.0%) | 0/2 (0.0%) (0) | 2/2 (100.0%) | 16 / 16 / 16 / 17 / 17 (n=2) | 0/2 (0.0%) | 0/2 (0.0%) | 0/2 (0.0%) | 0/2 (0.0%) |
| all | 21728 | 4449 | 328 | 328/21728 (1.51%) | 328/4449 (7.4%) | 314 | 34/328 (10.4%) | 0/294 (0.0%) | 0/294 (0.0%) (0) | 140/294 (47.6%) | 10 / 15 / 16 / 17 / 19 (n=294) | 7/294 (2.4%) | 0/294 (0.0%) | 0/294 (0.0%) | 0/294 (0.0%) |

**a18new** (a18new: seasons 2027–2036 (10); censored = returns decided in 2036)

| band | evaluations (all, p = 0 included) | eligible (p > 0) | returns (episodes) | returns / all evaluations | returns / eligible | unique people | censored (no archived Y+1) | any cash-blocked week in Y+1 | pathway re-entry in Y+1 (count carried) | winter "took a job" after Y+1 | starts in Y+1 (min/q1/med/q3/max) | turned pro / comeback | retired | became staff | died |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 18–20 | 54 | 4 | 1 | 1/54 (1.85%) | 1/4 (25.0%) | 1 | 0/1 (0.0%) | 0/1 (0.0%) | 0/1 (0.0%) (0) | 0/1 (0.0%) | 16 / 16 / 16 / 16 / 16 (n=1) | 0/1 (0.0%) | 0/1 (0.0%) | 0/1 (0.0%) | 0/1 (0.0%) |
| 21–24 | 2923 | 739 | 206 | 206/2923 (7.05%) | 206/739 (27.9%) | 206 | 24/206 (11.7%) | 0/182 (0.0%) | 0/182 (0.0%) (0) | 71/182 (39.0%) | 8 / 14 / 16 / 17 / 19 (n=182) | 2/182 (1.1%) | 0/182 (0.0%) | 0/182 (0.0%) | 0/182 (0.0%) |
| 25–29 | 7206 | 2412 | 154 | 154/7206 (2.14%) | 154/2412 (6.4%) | 152 | 19/154 (12.3%) | 0/135 (0.0%) | 0/135 (0.0%) (0) | 101/135 (74.8%) | 8 / 11 / 15 / 17 / 18 (n=135) | 0/135 (0.0%) | 0/135 (0.0%) | 0/135 (0.0%) | 0/135 (0.0%) |
| 30+ | 11236 | 1344 | 1 | 1/11236 (0.01%) | 1/1344 (0.1%) | 1 | 0/1 (0.0%) | 0/1 (0.0%) | 0/1 (0.0%) (0) | 1/1 (100.0%) | 15 / 15 / 15 / 15 / 15 (n=1) | 0/1 (0.0%) | 0/1 (0.0%) | 0/1 (0.0%) | 0/1 (0.0%) |
| all | 21419 | 4499 | 362 | 362/21419 (1.69%) | 362/4499 (8.0%) | 350 | 43/362 (11.9%) | 0/319 (0.0%) | 0/319 (0.0%) (0) | 173/319 (54.2%) | 8 / 13 / 16 / 17 / 19 (n=319) | 2/319 (0.6%) | 0/319 (0.0%) | 0/319 (0.0%) | 0/319 (0.0%) |

**seed2** (seed2: seasons 2027–2031 (5); censored = returns decided in 2031)

| band | evaluations (all, p = 0 included) | eligible (p > 0) | returns (episodes) | returns / all evaluations | returns / eligible | unique people | censored (no archived Y+1) | any cash-blocked week in Y+1 | pathway re-entry in Y+1 (count carried) | winter "took a job" after Y+1 | starts in Y+1 (min/q1/med/q3/max) | turned pro / comeback | retired | became staff | died |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 18–20 | 32 | 0 | 0 | 0/32 (0.00%) | 0/0 | 0 | 0/0 | 0/0 | 0/0 (0) | 0/0 | — | 0/0 | 0/0 | 0/0 | 0/0 |
| 21–24 | 1098 | 360 | 88 | 88/1098 (8.01%) | 88/360 (24.4%) | 88 | 25/88 (28.4%) | 0/63 (0.0%) | 0/63 (0.0%) (0) | 16/63 (25.4%) | 11 / 14 / 16 / 17 / 18 (n=63) | 1/63 (1.6%) | 0/63 (0.0%) | 0/63 (0.0%) | 0/63 (0.0%) |
| 25–29 | 2129 | 562 | 42 | 42/2129 (1.97%) | 42/562 (7.5%) | 42 | 13/42 (31.0%) | 0/29 (0.0%) | 0/29 (0.0%) (0) | 21/29 (72.4%) | 11 / 16 / 16 / 17 / 18 (n=29) | 0/29 (0.0%) | 0/29 (0.0%) | 0/29 (0.0%) | 0/29 (0.0%) |
| 30+ | 4903 | 479 | 0 | 0/4903 (0.00%) | 0/479 (0.0%) | 0 | 0/0 | 0/0 | 0/0 (0) | 0/0 | — | 0/0 | 0/0 | 0/0 | 0/0 |
| all | 8162 | 1401 | 130 | 130/8162 (1.59%) | 130/1401 (9.3%) | 128 | 38/130 (29.2%) | 0/92 (0.0%) | 0/92 (0.0%) (0) | 37/92 (40.2%) | 11 / 15 / 16 / 17 / 18 (n=92) | 1/92 (1.1%) | 0/92 (0.0%) | 0/92 (0.0%) | 0/92 (0.0%) |

**POOLED over the four arms** — sums of episodes from different worlds (two seeds, three rule settings); unique people are (arm, golfer) pairs; no causal reading.

| band | evaluations (all, p = 0 included) | eligible (p > 0) | returns (episodes) | returns / all evaluations | returns / eligible | unique people | censored (no archived Y+1) | any cash-blocked week in Y+1 | pathway re-entry in Y+1 (count carried) | winter "took a job" after Y+1 | starts in Y+1 (min/q1/med/q3/max) | turned pro / comeback | retired | became staff | died |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 18–20 | 163 | 9 | 4 | 4/163 (2.45%) | 4/9 (44.4%) | 4 | 0/4 (0.0%) | 0/4 (0.0%) | 0/4 (0.0%) (0) | 0/4 (0.0%) | 16 / 17 / 17 / 17 / 18 (n=4) | 0/4 (0.0%) | 0/4 (0.0%) | 0/4 (0.0%) | 0/4 (0.0%) |
| 21–24 | 9987 | 2710 | 696 | 696/9987 (6.97%) | 696/2710 (25.7%) | 696 | 92/696 (13.2%) | 0/604 (0.0%) | 0/604 (0.0%) (0) | 218/604 (36.1%) | 8 / 15 / 16 / 17 / 19 (n=604) | 14/604 (2.3%) | 0/604 (0.0%) | 0/604 (0.0%) | 0/604 (0.0%) |
| 25–29 | 23798 | 7664 | 460 | 460/23798 (1.93%) | 460/7664 (6.0%) | 455 | 64/460 (13.9%) | 0/396 (0.0%) | 0/396 (0.0%) (0) | 282/396 (71.2%) | 8 / 14 / 16 / 17 / 20 (n=396) | 6/396 (1.5%) | 0/396 (0.0%) | 0/396 (0.0%) | 0/396 (0.0%) |
| 30+ | 39004 | 4475 | 6 | 6/39004 (0.02%) | 6/4475 (0.1%) | 6 | 1/6 (16.7%) | 0/5 (0.0%) | 0/5 (0.0%) (0) | 5/5 (100.0%) | 15 / 16 / 17 / 17 / 17 (n=5) | 0/5 (0.0%) | 0/5 (0.0%) | 0/5 (0.0%) | 0/5 (0.0%) |
| all | 72952 | 14858 | 1166 | 1166/72952 (1.60%) | 1166/14858 (7.8%) | 1125 | 157/1166 (13.5%) | 0/1009 (0.0%) | 0/1009 (0.0%) (0) | 505/1009 (50.0%) | 8 / 15 / 16 / 17 / 20 (n=1009) | 20/1009 (2.0%) | 0/1009 (0.0%) | 0/1009 (0.0%) | 0/1009 (0.0%) |

Consistency of the two sources: a21old: 346 return transitions, 346 evaluations with outcome 1; a18old: 328 return transitions, 328 evaluations with outcome 1; a18new: 362 return transitions, 362 evaluations with outcome 1; seed2: 130 return transitions, 130 evaluations with outcome 1. Death counts a death in the winter of the return or the winter after Y+1 (people table `died`).

**Two different events, reported separately (pooled, observed returns):** a winter "amateur took a job" career decision after Y+1: 505/1009 (50.0%); a mid-season cash re-block or a work-pathway re-entry during Y+1: 0/1009 (0.0%) with any cash-blocked week, 0/1009 (0.0%) re-entries. Neither stands in for the other.

**Completeness assertions** (analysis-only; a failure is printed with its ids):

- A1, a season-(Y+1) career row for every observed return (starts are never defaulted to zero): 1009/1009 — PASS. Smallest Y+1 starts among them: 8.
- A2, inputs present in every season used (decision evidence format golf-legacy-decision-evidence/2 with the `amateur_return` and `amateur_job` models; `cash_blocked_max` and `work_pathway` present): 35/35 seasons — PASS. A present map without the golfer means zero (counted: 1009 observed returns absent from the Y+1 `cash_blocked_max`).
- A3, return transitions and positive `amateur_return` evaluations matched one-to-one per (arm, golfer, year): 1166 transitions — PASS.

### 5.1 The job chance anticipated at return vs the next winter's job decision

**What the rule discounts.** The return chance is `min(CAP, sig(x) × keep_up)` (golfsim/amateur_return.py lines 142 and 147), where `keep_up` (lines 150–160) is `1 − careers.p_amateur_job(season, g, row, year + 1)` evaluated in the return winter Y, after the turn-pro draw and before the golfer's lifestyle changes, with cash reduced by the full-time season cost (savings first, then family money: line 155) and restored afterwards. So it discounts the same decision function the next winter applies (careers.py lines 355–365: `x = −1.2 + 0.8 (age − 22) − 0.4 min(runway, 5) + 1[cash < 0]`, at age Y+1) — the same kind of event, a full-time amateur taking a job in the winter after Y+1 (careers.decide lines 449–458) — but evaluated on PROJECTED inputs, so it is a proxy, not that exact future draw: (i) the golfer is still part-time when it is computed, so `runway_years` (careers.py 81–96, called with row None) costs the season with a working amateur's committed costs (season.committed_weekly: living 40,000 less salary 52,000, i.e. none, plus any coach fee) where the actual decision costs it as a full-time amateur (no living cost); (ii) events = max(8, events of season Y, as a part-timer) rather than of Y+1; (iii) cash is the savings after paying the season cost, with no other money in or out during Y+1, so the debt term is never on at the prediction; (iv) `season.funds(g, Y+2)` has no Y+1 ledger yet, so the credit line is the base limit. The actual decision (careers.py 449–454) uses the golfer's real end-of-Y+1 cash, row and credit, and is reached only if the golfer did not retire (line 415) or turn professional (line 433) first and is a full-time non-college amateur aged 19+. The other route to work in Y+1, the mid-season work pathway, had 0 re-entries (above).

**Data.** Prediction: the stored `keep_up` input of the return's decision evidence /2 `amateur_return` row (rounded to 3 decimals by decision_evidence._input), so predicted p = 1 − keep_up; not recomputed. Actual: the following winter's `amateur_job` row for that golfer (p, its draw u, outcome, and inputs age, runway, cash), read as stored. Population: the observed returns (season Y+1 archived; censored excluded). Episodes and unique (arm, golfer) pairs are shown side by side: a golfer who returned twice contributes two episodes, which are not independent. Drift medians compare the prediction's projected funds (`funds_k − season_cost_k`, savings plus family money after the season) with the decision's `cash_k` (savings only: family money is not an input of p_amateur_job), Overall and amateur rank at the end of Y and Y+1 (season file `careers`), and the age used at each point.

| arm | band | episodes (unique people) | with a next-winter job evaluation | not evaluated (why) | predicted mean p at return | evaluated mean p next winter | realised: took a job | Σ predicted p vs observed | Σ evaluated p vs observed (evaluated only) | projected funds → cash at decision, $k (medians) | Overall change (median) | amateur rank end Y → end Y+1 (medians) | age used by the prediction (age at Y + 1) / at the decision | debt term on at the decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a21old | 18–20 | 2 (2) | 2/2 (100.0%) | — | 0.048 (n=2) | 0.053 | 0/2 (0.0%) | 0.1 vs 0 | 0.1 vs 0 | 6.0 → 9.5 | +1.2 | 182.0 → 273.5 | 21.0 / 21.0 | 0/2 (0.0%) |
| a21old | 21–24 | 190 (190) | 185/190 (97.4%) | turned pro / comeback 5 | 0.298 (n=190) | 0.418 | 77/190 (40.5%) | 56.7 vs 77 | 77.4 vs 77 | 15.0 → 8.0 | +0.4 | 938.5 → 1068.0 | 24.0 / 24.0 | 6/185 (3.2%) |
| a21old | 25–29 | 110 (108) | 105/110 (95.5%) | turned pro / comeback 5 | 0.664 (n=110) | 0.754 | 76/110 (69.1%) | 73.0 vs 76 | 79.2 vs 76 | 20.0 → 14.0 | +0.3 | 994.5 → 1132.5 | 26.0 / 26.0 | 1/105 (1.0%) |
| a21old | 30+ | 2 (2) | 2/2 (100.0%) | — | 0.982 (n=2) | 0.994 | 2/2 (100.0%) | 2.0 vs 2 | 2.0 vs 2 | 24.5 → 18.5 | +0.0 | 556.0 → 1370.0 | 31.0 / 31.0 | 0/2 (0.0%) |
| a21old | all | 304 (295) | 294/304 (96.7%) | turned pro / comeback 10 | 0.433 (n=304) | 0.540 | 155/304 (51.0%) | 131.8 vs 155 | 158.7 vs 155 | 17.0 → 10.0 | +0.3 | 949.0 → 1110.5 | 25.0 / 25.0 | 7/294 (2.4%) |
| a18old | 18–20 | 1 (1) | 1/1 (100.0%) | — | 0.026 (n=1) | 0.045 | 0/1 (0.0%) | 0.0 vs 0 | 0.0 vs 0 | 13.0 → 13.0 | +1.1 | 420.0 → 502.0 | 21.0 / 21.0 | 0/1 (0.0%) |
| a18old | 21–24 | 169 (169) | 163/169 (96.4%) | turned pro / comeback 6 | 0.279 (n=169) | 0.381 | 54/169 (32.0%) | 47.2 vs 54 | 62.1 vs 54 | 17.0 → 8.0 | +0.4 | 947.0 → 1052.0 | 24.0 / 24.0 | 5/163 (3.1%) |
| a18old | 25–29 | 122 (122) | 121/122 (99.2%) | turned pro / comeback 1 | 0.658 (n=122) | 0.745 | 84/122 (68.9%) | 80.3 vs 84 | 90.2 vs 84 | 19.0 → 13.0 | +0.2 | 964.0 → 1096.0 | 26.0 / 26.0 | 0/121 (0.0%) |
| a18old | 30+ | 2 (2) | 2/2 (100.0%) | — | 0.982 (n=2) | 0.993 | 2/2 (100.0%) | 2.0 vs 2 | 2.0 vs 2 | 32.0 → 16.0 | -0.2 | 1094.5 → 1704.0 | 31.0 / 31.0 | 0/2 (0.0%) |
| a18old | all | 294 (280) | 287/294 (97.6%) | turned pro / comeback 7 | 0.440 (n=294) | 0.538 | 140/294 (47.6%) | 129.5 vs 140 | 154.3 vs 140 | 18.0 → 11.0 | +0.3 | 942.0 → 1069.5 | 25.0 / 25.0 | 5/287 (1.7%) |
| a18new | 18–20 | 1 (1) | 1/1 (100.0%) | — | 0.054 (n=1) | 0.054 | 0/1 (0.0%) | 0.1 vs 0 | 0.1 vs 0 | 6.0 → 7.0 | +0.5 | 331.0 → 152.0 | 21.0 / 21.0 | 0/1 (0.0%) |
| a18new | 21–24 | 182 (182) | 180/182 (98.9%) | turned pro / comeback 2 | 0.291 (n=182) | 0.395 | 71/182 (39.0%) | 52.9 vs 71 | 71.0 vs 71 | 13.5 → 8.0 | +0.4 | 983.0 → 1193.0 | 25.0 / 25.0 | 3/180 (1.7%) |
| a18new | 25–29 | 135 (134) | 135/135 (100.0%) | — | 0.668 (n=135) | 0.734 | 101/135 (74.8%) | 90.2 vs 101 | 99.1 vs 101 | 19.0 → 14.0 | +0.2 | 1206.0 → 1311.0 | 26.0 / 26.0 | 0/135 (0.0%) |
| a18new | 30+ | 1 (1) | 1/1 (100.0%) | — | 0.982 (n=1) | 0.982 | 1/1 (100.0%) | 1.0 vs 1 | 1.0 vs 1 | 25.0 → 24.0 | +0.0 | 693.0 → 1685.0 | 31.0 / 31.0 | 0/1 (0.0%) |
| a18new | all | 319 (309) | 317/319 (99.4%) | turned pro / comeback 2 | 0.452 (n=319) | 0.540 | 173/319 (54.2%) | 144.2 vs 173 | 171.1 vs 173 | 16.0 → 10.0 | +0.3 | 1044.0 → 1269.0 | 25.0 / 25.0 | 3/317 (0.9%) |
| seed2 | 21–24 | 63 (63) | 62/63 (98.4%) | turned pro / comeback 1 | 0.249 (n=63) | 0.316 | 16/63 (25.4%) | 15.7 vs 16 | 19.6 vs 16 | 16.0 → 12.0 | +0.4 | 748.0 → 1075.0 | 24.0 / 24.0 | 1/62 (1.6%) |
| seed2 | 25–29 | 29 (29) | 29/29 (100.0%) | — | 0.649 (n=29) | 0.744 | 21/29 (72.4%) | 18.8 vs 21 | 21.6 vs 21 | 22.0 → 17.0 | +0.2 | 936.0 → 1777.0 | 26.0 / 26.0 | 0/29 (0.0%) |
| seed2 | all | 92 (92) | 91/92 (98.9%) | turned pro / comeback 1 | 0.375 (n=92) | 0.452 | 37/92 (40.2%) | 34.5 vs 37 | 41.1 vs 37 | 18.5 → 13.0 | +0.3 | 875.0 → 1117.0 | 24.0 / 24.0 | 1/91 (1.1%) |
| POOLED (four arms; sums of episodes from different worlds) | 18–20 | 4 (4) | 4/4 (100.0%) | — | 0.044 (n=4) | 0.052 | 0/4 (0.0%) | 0.2 vs 0 | 0.2 vs 0 | 8.0 → 9.5 | +1.1 | 329.0 → 313.5 | 21.0 / 21.0 | 0/4 (0.0%) |
| POOLED (four arms; sums of episodes from different worlds) | 21–24 | 604 (604) | 590/604 (97.7%) | turned pro / comeback 14 | 0.286 (n=604) | 0.390 | 218/604 (36.1%) | 172.5 vs 218 | 230.0 vs 218 | 15.5 → 8.5 | +0.4 | 935.5 → 1082.0 | 24.0 / 24.0 | 15/590 (2.5%) |
| POOLED (four arms; sums of episodes from different worlds) | 25–29 | 396 (393) | 390/396 (98.5%) | turned pro / comeback 6 | 0.662 (n=396) | 0.744 | 282/396 (71.2%) | 262.3 vs 282 | 290.0 vs 282 | 19.0 → 14.0 | +0.2 | 1021.5 → 1232.0 | 26.0 / 26.0 | 1/390 (0.3%) |
| POOLED (four arms; sums of episodes from different worlds) | 30+ | 5 (5) | 5/5 (100.0%) | — | 0.982 (n=5) | 0.991 | 5/5 (100.0%) | 4.9 vs 5 | 5.0 vs 5 | 25.0 → 17.0 | -0.1 | 667.0 → 1478.0 | 31.0 / 31.0 | 0/5 (0.0%) |
| POOLED (four arms; sums of episodes from different worlds) | all | 1009 (976) | 989/1009 (98.0%) | turned pro / comeback 20 | 0.436 (n=1009) | 0.531 | 505/1009 (50.0%) | 439.9 vs 505 | 525.2 vs 505 | 17.0 → 11.0 | +0.3 | 968.0 → 1140.0 | 25.0 / 25.0 | 16/989 (1.6%) |

Return-rate denominators (the table above section 5.1): "returns / all evaluations" counts every `amateur_return` evaluation, including p = 0 (blocked by work, funds or results: the discount never enters those); "returns / eligible" counts only p > 0, where the chance is already multiplied by the anticipated keep-up factor (and capped at 0.6), so the discount lowers the eligible-rate numerator directly and the all-evaluations rate only through the eligible ones. Differences between predicted and evaluated p are described only by the recorded inputs above; no tuning is proposed.

## 6. Upset snapshot cost (a18new and seed2)

Bytes of each edition's archived `upset` record (golfsim/upsets.record), in the archive's own JSON encoding (compact separators, archive._write). "gzip alone" compresses a season's upset records (or their `inputs` snapshots) by themselves at the archive's level 6: an approximation of their contribution inside the whole-file compression, not an exact share of the gzip file.

| arm | season | editions with a record | upset JSON | bytes / edition | inputs JSON | inputs bytes / edition | upset share of raw season file | inputs share of raw | upset gzip alone | inputs gzip alone | upset gzip alone / season .gz | season .gz |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a18new | 2027 | 1438 | 1.81 MB | 1260 | 1.19 MB | 828 | 3.3% | 2.2% | 0.62 MB | 0.47 MB | 4.8% | 13.0 MB |
| a18new | 2028 | 1436 | 1.83 MB | 1277 | 1.21 MB | 844 | 3.5% | 2.3% | 0.63 MB | 0.48 MB | 5.0% | 12.6 MB |
| a18new | 2029 | 1436 | 1.84 MB | 1279 | 1.21 MB | 846 | 3.5% | 2.3% | 0.64 MB | 0.49 MB | 5.0% | 12.7 MB |
| a18new | 2030 | 1440 | 1.87 MB | 1297 | 1.24 MB | 863 | 3.5% | 2.3% | 0.65 MB | 0.50 MB | 5.0% | 12.9 MB |
| a18new | 2031 | 1441 | 1.90 MB | 1319 | 1.27 MB | 884 | 3.4% | 2.3% | 0.65 MB | 0.50 MB | 5.0% | 13.1 MB |
| a18new | 2032 | 1441 | 1.93 MB | 1342 | 1.31 MB | 906 | 3.4% | 2.3% | 0.67 MB | 0.51 MB | 5.0% | 13.4 MB |
| a18new | 2033 | 1440 | 1.97 MB | 1365 | 1.34 MB | 929 | 3.3% | 2.3% | 0.68 MB | 0.53 MB | 4.9% | 13.8 MB |
| a18new | 2034 | 1441 | 1.98 MB | 1377 | 1.35 MB | 940 | 3.3% | 2.2% | 0.68 MB | 0.53 MB | 4.9% | 13.9 MB |
| a18new | 2035 | 1440 | 2.01 MB | 1396 | 1.38 MB | 958 | 3.2% | 2.2% | 0.69 MB | 0.54 MB | 4.9% | 14.2 MB |
| a18new | 2036 | 1441 | 2.03 MB | 1410 | 1.40 MB | 971 | 3.2% | 2.2% | 0.70 MB | 0.55 MB | 4.8% | 14.4 MB |
| seed2 | 2027 | 1433 | 1.81 MB | 1263 | 1.19 MB | 831 | 3.3% | 2.2% | 0.62 MB | 0.47 MB | 4.8% | 13.0 MB |
| seed2 | 2028 | 1433 | 1.84 MB | 1282 | 1.22 MB | 849 | 3.5% | 2.3% | 0.64 MB | 0.49 MB | 5.0% | 12.6 MB |
| seed2 | 2029 | 1439 | 1.86 MB | 1290 | 1.23 MB | 857 | 3.5% | 2.3% | 0.65 MB | 0.50 MB | 5.0% | 12.9 MB |
| seed2 | 2030 | 1438 | 1.88 MB | 1309 | 1.26 MB | 875 | 3.4% | 2.3% | 0.65 MB | 0.50 MB | 5.0% | 13.1 MB |
| seed2 | 2031 | 1440 | 1.91 MB | 1329 | 1.29 MB | 894 | 3.4% | 2.3% | 0.66 MB | 0.51 MB | 5.0% | 13.3 MB |
| all | 15 seasons | 21577 | 28.5 MB | 1320 | 19.1 MB | 885 | 3.4% | 2.3% | 9.8 MB | 7.6 MB | 4.9% | 199 MB |

**CPU: offline recomputation from stored inputs.** It excludes the fact capture at field-set time and any engine-side bookkeeping, so it is not the in-engine overhead (the season engine has no per-phase timing for upset estimates, and none is inferred from season run times). Each estimated record's `inputs` snapshot (ids, Overall, rounds) is passed to `golfsim.upsets.reproduce`; only that call is timed, with process CPU time, under `nice -n 19` while the test suite ran.

| arm | season | estimated records recomputed | reproduced = stored (top 5, favourite, winner) | largest |difference| | CPU per season (s) | CPU per edition, mean (ms) | median (ms) | max (ms) |
|---|---|---|---|---|---|---|---|---|
| a18new | 2027 | 1435 | 1435/1435 | 0 | 2.898 | 2.019 | 1.813 | 9.078 |
| a18new | 2036 | 1438 | 1438/1438 | 0 | 2.804 | 1.95 | 1.832 | 5.615 |

## What the runs do not record (and the workaround used)

- The weekly access outcome of each week is not kept per week: only the last n plan weeks compatible with the recorded `weeks_blocked` are reconstructed, from the monthly plans' recorded availability (decision evidence /2), not actual weekly access; no exact time from the first blocked week is claimed.
- Starts after a pathway job: season starts include starts before the job; starts from the decision week on are counted from the editions' weeks and finishes in the season file.
- Whether the home-club floor (not the regional baseline) set a start's familiarity is not recorded per start; starts at a home club found by country are counted as an upper bound, and the end-state source of each golfer's home-club familiarity is read from the people table.
- Per-week entrants who were refused by a full ordinary open field are recorded only as the golfer's week (`careers.denied`: first choice and what they played instead); counts above are golfer-weeks, not entries per event.
- The run state (seed rows, extras) is checkpointed every season in seed_<s>.state.pkl; seed_<s>.json.gz only every 5 seasons. The report reads whichever lists more seasons, and only seasons also published in the archive.

_Analysis time: 136 s._
