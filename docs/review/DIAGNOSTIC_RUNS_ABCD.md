> **Pinned diagnostic runs A, B, C and D -- simulation build 473690a (clean checkout).** Not evidence about the final
> feature world: none of the overnight packages (recruitment, prestige/nation shares, amateur return, death,
> geography, weather, upsets, stories, decision evidence, the pathway from 18, college open access) are in these
> worlds. Run A: seed 360013, 45 seasons (2027-2071), support on; B/C: seed 2027, 10 seasons, support on/off; D: seed
> 3031, 10 seasons. Determinism: B season 5 (2031) replayed from the copy kept after season 4 -- identical in all 15
> recorded parts. Segments, stops and resumes are as the Provenance section (the runs' log) records them.
>
> Generated read-only from the runs' saved files with this branch's tools/diagnostic_report.py:
> `python tools/diagnostic_report.py --run A=<runs>/A:360013 --run B=<runs>/B:2027 --run C=<runs>/C:2027
> --run D=<runs>/D:3031 --provenance docs/review/DIAGNOSTIC_RUNS_PROVENANCE.md --out <file>`

# Diagnostic runs

## The runs

| Run | Seed | Commit | Amateur support | Seasons | Season time (sum) | Recorded state |
|---|---|---|---|---|---|---|
| A | 360013 | `473690a154` | on | 45 (2027-2071) | 190 min | 45 of 45 requested seasons recorded; a guard stop is recorded in the saved state (season 2033 took 487 s (limit 420 s)) |
| B | 2027 | `473690a154` | on | 10 (2027-2036) | 40 min | 10 of 10 requested seasons recorded; a guard stop is recorded in the saved state (season 2033 took 491 s (limit 420 s)) |
| C | 2027 | `473690a154` | off | 10 (2027-2036) | 35 min | 10 of 10 requested seasons recorded |
| D | 3031 | `473690a154` | on | 10 (2027-2036) | 36 min | 10 of 10 requested seasons recorded |

Season time is the sum of the recorded season skips, whichever segment played them (a resumed run's wall clock covers its last segment only). The recorded state says how many seasons are recorded and whether a guard stop is kept in the saved state; it does not say whether the run was resumed or is still running -- the Provenance section, when included, records each segment.

Machine: "Intel(R) Xeon(R) Processor @ 2.10GHz, 4 logical CPUs, Python 3.13.17, Linux-6.18.44-fc-v185-x86_64-with-glibc2.39; memory 15.7 GB, 15.2 GB available at the start"

## Performance on this machine

Each season is the observer's season skip (simulate, save the checkpoint, publish the history, reload). Two worker processes per run; two runs side by side on 4 CPUs while other work shared the machine, so these are this machine's timings, not the 120-second acceptance measurement (that uses the owner's machine and workload).

| Run | First season s | Median s | Slowest s | Last s | Median simulate s | Median save+publish s | Archive MB at end | Checkpoint MB |
|---|---|---|---|---|---|---|---|---|
| A | 187 | 257 | 487 (above the guard) | 271 | 226 | 22.2 | 3004 | 110 |
| B | 183 | 215 | 490 (above the guard) | 248 | 197 | 14.1 | 422 | 64 |
| C | 158 | 210 | 263 | 224 | 192 | 14.2 | 592 | 64 |
| D | 175 | 221 | 237 | 232 | 202 | 15.4 | 588 | 63 |

Seasons above the 420 s guard: A 2033 (487 s), B 2033 (490 s). The guard stops a run after such a season; which segment it was, and what the machine was doing, is recorded under Provenance, when given.

## Population

| Run | Active at start | Active at end | Arrivals | Exits | Seasons reconciling | Seasons | Seasons flagged (>20 % from start) |
|---|---|---|---|---|---|---|---|
| A | 6656 | 13253 | 32521 | 25924 | 45 | 45 | 39 |
| B | 6449 | 10619 | 7341 | 3171 | 10 | 10 | 6 |
| C | 6449 | 10638 | 7341 | 3152 | 10 | 10 | 7 |
| D | 6449 | 10446 | 7086 | 3089 | 10 | 10 | 7 |
- A 2030: active population 8433 is +27% from its start (6656); accounting reconciles (arrivals 764, exits 306)
- A 2031: active population 8792 is +32% from its start (6656); accounting reconciles (arrivals 722, exits 363)
- A 2032: active population 9206 is +38% from its start (6656); accounting reconciles (arrivals 754, exits 340)
- A 2034: active population 9874 is +48% from its start (6656); accounting reconciles (arrivals 656, exits 354)
- A 2035: active population 10238 is +54% from its start (6656); accounting reconciles (arrivals 733, exits 369)
- A 2036: active population 10528 is +58% from its start (6656); accounting reconciles (arrivals 722, exits 432)
- A 2037: active population 10781 is +62% from its start (6656); accounting reconciles (arrivals 662, exits 409)
- A 2038: active population 11063 is +66% from its start (6656); accounting reconciles (arrivals 736, exits 454)
- A 2039: active population 11264 is +69% from its start (6656); accounting reconciles (arrivals 694, exits 493)
- A 2040: active population 11533 is +73% from its start (6656); accounting reconciles (arrivals 705, exits 436)
- A 2041: active population 11765 is +77% from its start (6656); accounting reconciles (arrivals 734, exits 502)
- A 2042: active population 11950 is +80% from its start (6656); accounting reconciles (arrivals 704, exits 519)
- A 2043: active population 12115 is +82% from its start (6656); accounting reconciles (arrivals 723, exits 558)
- A 2044: active population 12276 is +84% from its start (6656); accounting reconciles (arrivals 709, exits 548)
- A 2045: active population 12437 is +87% from its start (6656); accounting reconciles (arrivals 750, exits 589)
- A 2046: active population 12561 is +89% from its start (6656); accounting reconciles (arrivals 719, exits 595)
- A 2047: active population 12662 is +90% from its start (6656); accounting reconciles (arrivals 742, exits 641)
- A 2048: active population 12752 is +92% from its start (6656); accounting reconciles (arrivals 702, exits 612)
- A 2049: active population 12796 is +92% from its start (6656); accounting reconciles (arrivals 683, exits 639)
- A 2050: active population 12852 is +93% from its start (6656); accounting reconciles (arrivals 694, exits 638)
- A 2051: active population 12918 is +94% from its start (6656); accounting reconciles (arrivals 740, exits 674)
- A 2052: active population 12951 is +95% from its start (6656); accounting reconciles (arrivals 742, exits 709)
- A 2053: active population 13039 is +96% from its start (6656); accounting reconciles (arrivals 750, exits 662)
- A 2055: active population 13109 is +97% from its start (6656); accounting reconciles (arrivals 706, exits 653)
- A 2056: active population 13093 is +97% from its start (6656); accounting reconciles (arrivals 701, exits 717)
- A 2057: active population 13105 is +97% from its start (6656); accounting reconciles (arrivals 757, exits 745)
- A 2058: active population 13125 is +97% from its start (6656); accounting reconciles (arrivals 719, exits 699)
- A 2059: active population 13144 is +97% from its start (6656); accounting reconciles (arrivals 744, exits 725)
- A 2060: active population 13137 is +97% from its start (6656); accounting reconciles (arrivals 707, exits 714)
- A 2061: active population 13112 is +97% from its start (6656); accounting reconciles (arrivals 717, exits 742)
- A 2062: active population 13093 is +97% from its start (6656); accounting reconciles (arrivals 721, exits 740)
- A 2063: active population 13089 is +97% from its start (6656); accounting reconciles (arrivals 724, exits 728)
- A 2064: active population 13108 is +97% from its start (6656); accounting reconciles (arrivals 767, exits 748)
- A 2065: active population 13087 is +97% from its start (6656); accounting reconciles (arrivals 704, exits 725)
- A 2066: active population 13147 is +98% from its start (6656); accounting reconciles (arrivals 761, exits 701)
- A 2067: active population 13193 is +98% from its start (6656); accounting reconciles (arrivals 729, exits 683)
- A 2068: active population 13195 is +98% from its start (6656); accounting reconciles (arrivals 743, exits 741)
- A 2069: active population 13193 is +98% from its start (6656); accounting reconciles (arrivals 720, exits 722)
- A 2070: active population 13166 is +98% from its start (6656); accounting reconciles (arrivals 726, exits 753)
- B 2029: active population 7892 is +22% from its start (6449); accounting reconciles (arrivals 694, exits 255)
- B 2030: active population 8378 is +30% from its start (6449); accounting reconciles (arrivals 753, exits 267)
- B 2031: active population 8815 is +37% from its start (6449); accounting reconciles (arrivals 740, exits 303)
- B 2032: active population 9223 is +43% from its start (6449); accounting reconciles (arrivals 717, exits 309)
- B 2034: active population 9985 is +55% from its start (6449); accounting reconciles (arrivals 724, exits 373)
- B 2035: active population 10315 is +60% from its start (6449); accounting reconciles (arrivals 712, exits 382)
- C 2029: active population 7930 is +23% from its start (6449); accounting reconciles (arrivals 694, exits 246)
- C 2030: active population 8367 is +30% from its start (6449); accounting reconciles (arrivals 753, exits 316)
- C 2031: active population 8798 is +36% from its start (6449); accounting reconciles (arrivals 740, exits 309)
- C 2032: active population 9182 is +42% from its start (6449); accounting reconciles (arrivals 717, exits 333)
- C 2033: active population 9582 is +49% from its start (6449); accounting reconciles (arrivals 774, exits 374)
- C 2034: active population 9953 is +54% from its start (6449); accounting reconciles (arrivals 724, exits 353)
- C 2035: active population 10301 is +60% from its start (6449); accounting reconciles (arrivals 712, exits 364)
- D 2029: active population 7826 is +21% from its start (6449); accounting reconciles (arrivals 709, exits 292)
- D 2030: active population 8263 is +28% from its start (6449); accounting reconciles (arrivals 722, exits 285)
- D 2031: active population 8648 is +34% from its start (6449); accounting reconciles (arrivals 684, exits 299)
- D 2032: active population 9046 is +40% from its start (6449); accounting reconciles (arrivals 738, exits 340)
- D 2033: active population 9448 is +47% from its start (6449); accounting reconciles (arrivals 721, exits 319)
- D 2034: active population 9773 is +52% from its start (6449); accounting reconciles (arrivals 719, exits 394)
- D 2035: active population 10104 is +57% from its start (6449); accounting reconciles (arrivals 701, exits 370)

## Retirement coverage (run A, 45 seasons)

Cohorts by the season a golfer entered (the seeded world, then procedural arrivals). Retired = left competitive golf (retired, or became a coach or caddie).

| Cohort | Golfers | Retired by the end | Share | Median retirement age | 10th-90th pct age | Still active | Their median age | Oldest active |
|---|---|---|---|---|---|---|---|---|
| seeded world | 6656 | 6652 | 100% | 43 | 30-55 | 4 | 64 | 64 |
| arrived in seasons 2-6 | 3592 | 3565 | 99% | 37 | 26-51 | 27 | 58 | 69 |
| arrived in seasons 7-11 | 3580 | 3472 | 97% | 36 | 26-50 | 108 | 55 | 63 |
| arrived in seasons 12-21 | 7136 | 6239 | 87% | 35 | 26-47 | 897 | 47 | 59 |
| arrived in seasons 22-31 | 7203 | 4481 | 62% | 31 | 25-40 | 2722 | 39 | 49 |
| arrived in seasons 32-46 | 11010 | 2378 | 22% | 27 | 24-32 | 8632 | 26 | 39 |

## Peaks of completed procedural careers (run A)

17615 golfers who arrived after the world began and have left competitive golf (five or more seasons recorded).

| Peak Overall | Golfers | Median peak age | Median seasons within 2 of peak | Median seasons recorded |
|---|---|---|---|---|
| 0-49 | 4853 | 28 | 11 | 14 |
| 50-59 | 7881 | 29 | 11 | 14 |
| 60-69 | 4400 | 29 | 13 | 17 |
| 70-79 | 455 | 30 | 15 | 27 |
| 80-100 | 26 | 30 | 16 | 32 |

The ten highest peaks among golfers who arrived during the run:

| Golfer | Nation | Arrived | Overall at 19 | First recorded (Overall at age) | Potential | Peak | Peak age | Wins | Majors | Now |
|---|---|---|---|---|---|---|---|---|---|---|
| Rupert Vaughan | England | 2046 | 92.0 | 89.1 at 18 | 97.1 | 96.7 | 30 | 128 | 30 | active |
| Wei Fu | China | 2034 | 86.7 | 84.9 at 18 | 91.1 | 91.1 | 30 | 68 | 16 | retired at 55 |
| Weston Wolfe | USA | 2036 | 82.6 | 80.2 at 18 | 91.5 | 90.8 | 33 | 73 | 6 | retired at 51 |
| Taj Healy | Australia | 2039 | 79.1 | 75.1 at 18 | 89.6 | 89.5 | 35 | 67 | 9 | retired at 48 |
| Reid Parker | USA | 2053 | 84.4 | 82.5 at 18 | 88.6 | 88.7 | 28 | 43 | 1 | active |
| Benedict Chapman | South Africa | 2056 | 84.0 | 82.3 at 18 | 88.3 | 88.0 | 29 | 22 | 0 | active |
| Ollie Townsend | New Zealand | 2037 | 82.8 | 80.8 at 18 | 87.7 | 87.7 | 31 | 32 | 4 | retired at 51 |
| Genki Ueda | Japan | 2042 | 82.3 | 80.4 at 18 | 87.1 | 87.2 | 31 | 47 | 4 | retired at 46 |
| Parker Walton | USA | 2035 | 85.3 | 84.8 at 18 | 86.6 | 86.8 | 27 | 38 | 4 | retired at 44 |
| Trevor Pace | USA | 2035 | 78.5 | 76.0 at 18 | 86.7 | 86.3 | 31 | 33 | 0 | retired at 51 |

"Overall at 19" is the season-end rating of the season they were exactly 19; "—" when no such season was recorded (they arrived older, or it is not played yet).

## Development by age and source (run A)

Mean change in Overall per golfer-season, by the source the development evidence records (all levels; the development evidence of each archived season). The seeded world and procedural arrivals are shown apart.

**Procedural arrivals (joined during the run)**

| Age | Golfer-seasons | Maturing | Training | Tournaments | Injury | Aging | Total |
|---|---|---|---|---|---|---|---|
| 18-20 | 38072 | 0.296 | 0.886 | 0.481 | -0.001 | 0.044 | 1.707 |
| 21-23 | 47651 | 0.081 | 0.277 | 0.202 | -0.001 | 0.037 | 0.597 |
| 24-26 | 70286 | 0.000 | 0.088 | 0.084 | -0.001 | 0.028 | 0.200 |
| 27-29 | 69284 | 0.000 | 0.042 | 0.041 | -0.000 | -0.002 | 0.080 |
| 30-32 | 55635 | 0.000 | 0.025 | 0.024 | -0.000 | -0.093 | -0.044 |
| 33-35 | 43994 | 0.000 | 0.017 | 0.016 | -0.001 | -0.255 | -0.222 |
| 36-38 | 33879 | 0.000 | 0.011 | 0.011 | -0.001 | -0.471 | -0.450 |
| 39-41 | 25251 | 0.000 | 0.008 | 0.007 | -0.001 | -0.662 | -0.648 |
| 42-44 | 17773 | 0.000 | 0.006 | 0.005 | -0.002 | -0.816 | -0.807 |
| 45-47 | 11802 | 0.000 | 0.004 | 0.004 | -0.002 | -0.941 | -0.935 |
| 48-50 | 7267 | 0.000 | 0.003 | 0.002 | -0.002 | -1.020 | -1.017 |
| 51+ | 7051 | 0.000 | 0.002 | 0.002 | -0.002 | -1.048 | -1.047 |

Aging after 30 by part of the game (mean change per golfer-season, attribute points summed over the category's attributes):

| Age | Golfer-seasons | Physical | Technical (long, short, putting) | Mental |
|---|---|---|---|---|
| 30-34 | 86165 | -2.636 | -0.448 | 0.677 |
| 35-39 | 56647 | -5.133 | -4.156 | 0.663 |
| 40-44 | 33720 | -6.959 | -8.055 | 0.628 |
| 45-49 | 17075 | -8.075 | -10.765 | 0.293 |
| 50-54 | 6855 | -7.885 | -12.519 | 0.000 |
| 55+ | 2190 | -5.966 | -13.339 | -1.244 |

**Seeded world (present at the start)**

| Age | Golfer-seasons | Maturing | Training | Tournaments | Injury | Aging | Total |
|---|---|---|---|---|---|---|---|
| 18-20 | 1850 | 0.295 | 0.706 | 0.583 | -0.001 | 0.047 | 1.630 |
| 21-23 | 4544 | 0.094 | 0.288 | 0.264 | -0.001 | 0.042 | 0.688 |
| 24-26 | 6333 | 0.000 | 0.085 | 0.096 | -0.001 | 0.031 | 0.211 |
| 27-29 | 8080 | 0.000 | 0.040 | 0.044 | -0.001 | 0.000 | 0.083 |
| 30-32 | 9596 | 0.000 | 0.023 | 0.024 | -0.001 | -0.087 | -0.040 |
| 33-35 | 10721 | 0.000 | 0.015 | 0.016 | -0.001 | -0.246 | -0.217 |
| 36-38 | 11194 | 0.000 | 0.011 | 0.011 | -0.002 | -0.461 | -0.440 |
| 39-41 | 10935 | 0.000 | 0.009 | 0.010 | -0.002 | -0.651 | -0.633 |
| 42-44 | 9984 | 0.000 | 0.010 | 0.010 | -0.002 | -0.798 | -0.781 |
| 45-47 | 8387 | 0.000 | 0.010 | 0.010 | -0.003 | -0.929 | -0.912 |
| 48-50 | 6566 | 0.000 | 0.008 | 0.008 | -0.003 | -1.010 | -0.997 |
| 51+ | 10714 | 0.000 | 0.008 | 0.006 | -0.003 | -1.027 | -1.015 |

Aging after 30 by part of the game (mean change per golfer-season, attribute points summed over the category's attributes):

| Age | Golfer-seasons | Physical | Technical (long, short, putting) | Mental |
|---|---|---|---|---|
| 30-34 | 16640 | -2.726 | -0.483 | 0.856 |
| 35-39 | 18580 | -5.177 | -4.177 | 0.821 |
| 40-44 | 17210 | -6.910 | -7.994 | 0.763 |
| 45-49 | 12983 | -7.967 | -10.684 | 0.311 |
| 50-54 | 7894 | -7.748 | -12.538 | 0.000 |
| 55+ | 4790 | -5.381 | -13.174 | -1.482 |

## Amateur support: run B (with) against run C (without)

The same seed, build and rules; support is the only intended difference. Outcomes diverge as the seasons go on (different fields, rankings and money), so these are aggregate comparisons.

Recipients and spending (run B; counted, no ceiling on contracts):

| Season | Recipients | A / B / C | Drawn | Used 98 %+ of their cap | Mean drawn |
|---|---|---|---|---|---|
| 2027 | 189 | 18 / 68 / 103 | $1.07 m | 81 (43%) | $5,674 |
| 2028 | 214 | 32 / 77 / 105 | $1.25 m | 88 (41%) | $5,821 |
| 2029 | 233 | 24 / 81 / 128 | $1.25 m | 97 (42%) | $5,371 |
| 2030 | 214 | 23 / 82 / 109 | $1.17 m | 79 (37%) | $5,472 |
| 2031 | 214 | 26 / 71 / 117 | $1.11 m | 83 (39%) | $5,192 |
| 2032 | 215 | 25 / 83 / 107 | $1.14 m | 68 (32%) | $5,281 |
| 2033 | 215 | 24 / 81 / 110 | $1.12 m | 72 (33%) | $5,211 |
| 2034 | 218 | 23 / 86 / 109 | $1.17 m | 78 (36%) | $5,364 |
| 2035 | 220 | 24 / 73 / 123 | $1.18 m | 94 (43%) | $5,386 |
| 2036 | 215 | 20 / 77 / 118 | $1.11 m | 86 (40%) | $5,180 |

Events per amateur and seasons without a start (season by season, both arms):

| Season | Amateurs | B: n | B: events | B: no start | C: n | C: events | C: no start |
|---|---|---|---|---|---|---|---|
| 2027 | college | 1052 | 24.4 | 0 | 1052 | 24.5 | 0 |
| 2027 | full-time non-college | 378 | 17.5 | 0 | 378 | 17.5 | 0 |
| 2027 | part-time non-college | 1185 | 10.0 | 0 | 1185 | 10.0 | 0 |
| 2028 | college | 1042 | 23.8 | 0 | 1042 | 23.8 | 0 |
| 2028 | full-time non-college | 424 | 17.0 | 0 | 427 | 17.0 | 0 |
| 2028 | part-time non-college | 1481 | 10.0 | 0 | 1465 | 9.9 | 0 |
| 2029 | college | 1055 | 23.2 | 0 | 1055 | 23.1 | 0 |
| 2029 | full-time non-college | 450 | 16.6 | 1 | 448 | 16.4 | 3 |
| 2029 | part-time non-college | 1755 | 9.8 | 0 | 1793 | 9.8 | 0 |
| 2030 | college | 1063 | 22.3 | 0 | 1063 | 22.3 | 0 |
| 2030 | full-time non-college | 412 | 16.2 | 3 | 397 | 16.1 | 4 |
| 2030 | part-time non-college | 2085 | 9.7 | 1 | 2109 | 9.6 | 2 |
| 2031 | college | 1080 | 21.7 | 0 | 1080 | 21.6 | 0 |
| 2031 | full-time non-college | 379 | 16.0 | 0 | 364 | 15.9 | 0 |
| 2031 | part-time non-college | 2345 | 9.4 | 1 | 2361 | 9.5 | 0 |
| 2032 | college | 1106 | 21.1 | 0 | 1106 | 21.1 | 0 |
| 2032 | full-time non-college | 361 | 15.8 | 0 | 342 | 15.7 | 1 |
| 2032 | part-time non-college | 2570 | 9.3 | 0 | 2581 | 9.3 | 1 |
| 2033 | college | 1116 | 20.3 | 0 | 1116 | 20.3 | 0 |
| 2033 | full-time non-college | 368 | 15.7 | 1 | 353 | 15.4 | 2 |
| 2033 | part-time non-college | 2763 | 9.3 | 0 | 2756 | 9.3 | 1 |
| 2034 | college | 1112 | 19.5 | 0 | 1112 | 19.7 | 0 |
| 2034 | full-time non-college | 384 | 15.7 | 0 | 372 | 15.3 | 2 |
| 2034 | part-time non-college | 2968 | 9.2 | 2 | 2940 | 9.2 | 1 |
| 2035 | college | 1085 | 19.0 | 0 | 1085 | 18.9 | 0 |
| 2035 | full-time non-college | 392 | 15.2 | 2 | 382 | 15.3 | 2 |
| 2035 | part-time non-college | 3131 | 9.2 | 1 | 3142 | 9.2 | 1 |
| 2036 | college | 1055 | 18.8 | 0 | 1055 | 18.6 | 0 |
| 2036 | full-time non-college | 375 | 14.8 | 2 | 371 | 14.9 | 3 |
| 2036 | part-time non-college | 3340 | 9.1 | 1 | 3339 | 9.2 | 1 |

Amateurs turning professional each season:

| Season | B | C |
|---|---|---|
| 2027 | 149 | 139 |
| 2028 | 134 | 128 |
| 2029 | 136 | 147 |
| 2030 | 155 | 130 |
| 2031 | 122 | 124 |
| 2032 | 132 | 135 |
| 2033 | 140 | 149 |
| 2034 | 147 | 140 |
| 2035 | 165 | 145 |
| 2036 | 162 | 161 |

The amateurs ranked 1-150 at the end of 2027 (150 in B, 150 in C), season by season after:

| Season | B pro | B amateur | B events | B no start | B gone | C pro | C amateur | C events | C no start | C gone |
|---|---|---|---|---|---|---|---|---|---|---|
| 2027 | 0 | 150 | 22.2 | 0 | 0 | 0 | 150 | 21.8 | 0 | 0 |
| 2028 | 30 | 120 | 21.0 | 0 | 0 | 27 | 123 | 20.2 | 0 | 0 |
| 2029 | 49 | 101 | 19.9 | 0 | 0 | 46 | 104 | 17.8 | 2 | 0 |
| 2030 | 78 | 71 | 16.6 | 0 | 1 | 68 | 78 | 15.3 | 0 | 3 |
| 2031 | 96 | 53 | 13.9 | 0 | 1 | 86 | 59 | 13.5 | 0 | 4 |
| 2032 | 102 | 45 | 11.6 | 0 | 3 | 90 | 51 | 12.4 | 0 | 8 |
| 2033 | 99 | 46 | 11.7 | 0 | 3 | 88 | 51 | 12.2 | 0 | 10 |
| 2034 | 94 | 46 | 11.5 | 0 | 7 | 86 | 48 | 11.9 | 0 | 14 |
| 2035 | 95 | 42 | 11.3 | 0 | 10 | 85 | 46 | 11.3 | 0 | 17 |
| 2036 | 94 | 42 | 11.1 | 0 | 11 | 82 | 46 | 11.5 | 0 | 19 |

By region (all seasons): events per amateur and the share of amateur seasons without a start:

| Region | B amateur-seasons | B events | B no start | C amateur-seasons | C events | C no start |
|---|---|---|---|---|---|---|
| Africa | 1918 | 13.8 | 0.1% | 1921 | 13.6 | 0.2% |
| Asia | 7437 | 13.5 | 0.1% | 7528 | 13.3 | 0.1% |
| Europe | 11217 | 12.6 | 0.0% | 11089 | 12.7 | 0.1% |
| Latin America | 1276 | 11.6 | 0.1% | 1245 | 11.5 | 0.1% |
| Middle East | 114 | 10.9 | 0.0% | 132 | 10.5 | 0.0% |
| North America | 14294 | 14.1 | 0.0% | 14233 | 14.1 | 0.0% |
| Oceania | 2056 | 14.6 | 0.0% | 2123 | 14.3 | 0.0% |

### By age and by amateur standing (runs B and C)

Every amateur golfer-season of every recorded season (golfer-seasons, not unique people), grouped by age and by the amateur ranking at the season's end. Starting no event is not the same as being priced out, so the two are counted apart:

- **No start**: no event entered all season (any reason), of all amateur golfer-seasons (including those who took work by the pathway during the season).
- **Cash-blocked** (financial exclusion): at least one week counted as "could not afford any event" -- eligible for an event that week and not one of them affordable from spendable funds, support included. Counted only for full-time amateurs outside college (the work pathway's ledger), so its denominator is **tracked**: golfer-seasons that ended full-time and outside college. A golfer who took work by the pathway during the season ended it part-time, so is not tracked; those conversions are counted in their own column (and in total below).
- **Count 8+**: the cash-blocked count reached 8 during the season (injury and calendar gaps pause it, an affordable week resets it; it can carry weeks over from the winter before).
- **No start, cash-blocked** / **no start, never cash-blocked**: tracked seasons with no start, split by whether any week was counted as unaffordable.
- Support columns are run B's (run C has none by design).

Reading B against C: the same seed and rules with support the only intended difference, but support can change a golfer's results, amateur rank and status, so a group (by year-end rank especially) need not hold comparable golfers in the two runs. The differences are supportive evidence about support, not a paired-person causal estimate.

**Age**

| Age | Run | Amateur golfer-seasons | No start | Tracked (season-end full-time, not college) | Took work by the pathway (not tracked) | Cash-blocked 1+ week | Count 8+ | No start, cash-blocked | No start, never cash-blocked | Supported | Mean drawn | Cap used up (of supported) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| under 21 | B | 8,734 | 9 / 8,734 (0.1%) | 2,271 | 0 | 86 / 2,271 (3.8%) | 53 / 2,271 (2.3%) | 9 / 2,271 (0.4%) | 0 / 2,271 (0.0%) | 700 / 8,734 (8.0%) | $4,994 | 230 / 700 (32.9%) |
| under 21 | C | 8,742 | 16 / 8,742 (0.2%) | 2,280 | 0 | 111 / 2,280 (4.9%) | 71 / 2,280 (3.1%) | 16 / 2,280 (0.7%) | 0 / 2,280 (0.0%) | — | — | — |
| 21-22 | B | 5,759 | 0 / 5,759 (0.0%) | 1,030 | 165 | 49 / 1,030 (4.8%) | 11 / 1,030 (1.1%) | 0 / 1,030 (0.0%) | 0 / 1,030 (0.0%) | 731 / 5,759 (12.7%) | $5,362 | 272 / 731 (37.2%) |
| 21-22 | C | 5,764 | 3 / 5,764 (0.1%) | 994 | 190 | 59 / 994 (5.9%) | 16 / 994 (1.6%) | 1 / 994 (0.1%) | 0 / 994 (0.0%) | — | — | — |
| 23-25 | B | 4,975 | 1 / 4,975 (0.0%) | 589 | 58 | 21 / 589 (3.6%) | 6 / 589 (1.0%) | 0 / 589 (0.0%) | 0 / 589 (0.0%) | 273 / 4,975 (5.5%) | $5,502 | 119 / 273 (43.6%) |
| 23-25 | C | 5,074 | 1 / 5,074 (0.0%) | 533 | 57 | 22 / 533 (4.1%) | 5 / 533 (0.9%) | 0 / 533 (0.0%) | 0 / 533 (0.0%) | — | — | — |
| 26-29 | B | 6,488 | 4 / 6,488 (0.1%) | 33 | 1 | 1 / 33 (3.0%) | 1 / 33 (3.0%) | 0 / 33 (0.0%) | 0 / 33 (0.0%) | 212 / 6,488 (3.3%) | $5,952 | 94 / 212 (44.3%) |
| 26-29 | C | 6,631 | 1 / 6,631 (0.0%) | 27 | 0 | 3 / 27 (11.1%) | 0 / 27 (0.0%) | 0 / 27 (0.0%) | 0 / 27 (0.0%) | — | — | — |
| 30+ | B | 12,356 | 1 / 12,356 (0.0%) | 0 | 0 | — | — | — | — | 231 / 12,356 (1.9%) | $6,045 | 111 / 231 (48.1%) |
| 30+ | C | 12,060 | 3 / 12,060 (0.0%) | 0 | 0 | — | — | — | — | — | — | — |

**Amateur standing**

| Amateur standing | Run | Amateur golfer-seasons | No start | Tracked (season-end full-time, not college) | Took work by the pathway (not tracked) | Cash-blocked 1+ week | Count 8+ | No start, cash-blocked | No start, never cash-blocked | Supported | Mean drawn | Cap used up (of supported) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| amateur top 50 | B | 500 | 0 / 500 (0.0%) | 87 | 0 | 0 / 87 (0.0%) | 0 / 87 (0.0%) | 0 / 87 (0.0%) | 0 / 87 (0.0%) | 500 / 500 (100.0%) | $6,877 | 31 / 500 (6.2%) |
| amateur top 50 | C | 500 | 0 / 500 (0.0%) | 72 | 1 | 17 / 72 (23.6%) | 4 / 72 (5.6%) | 0 / 72 (0.0%) | 0 / 72 (0.0%) | — | — | — |
| 51-150 | B | 1,000 | 0 / 1,000 (0.0%) | 163 | 0 | 8 / 163 (4.9%) | 5 / 163 (3.1%) | 0 / 163 (0.0%) | 0 / 163 (0.0%) | 672 / 1,000 (67.2%) | $5,378 | 216 / 672 (32.1%) |
| 51-150 | C | 1,000 | 0 / 1,000 (0.0%) | 135 | 4 | 8 / 135 (5.9%) | 5 / 135 (3.7%) | 0 / 135 (0.0%) | 0 / 135 (0.0%) | — | — | — |
| 151-300 | B | 1,499 | 0 / 1,499 (0.0%) | 219 | 1 | 10 / 219 (4.6%) | 3 / 219 (1.4%) | 0 / 219 (0.0%) | 0 / 219 (0.0%) | 521 / 1,499 (34.8%) | $4,780 | 289 / 521 (55.5%) |
| 151-300 | C | 1,500 | 2 / 1,500 (0.1%) | 180 | 5 | 15 / 180 (8.3%) | 10 / 180 (5.6%) | 2 / 180 (1.1%) | 0 / 180 (0.0%) | — | — | — |
| ranked beyond 300 | B | 34,232 | 9 / 34,232 (0.0%) | 3,368 | 217 | 136 / 3,368 (4.0%) | 62 / 3,368 (1.8%) | 9 / 3,368 (0.3%) | 0 / 3,368 (0.0%) | 454 / 34,232 (1.3%) | $4,476 | 290 / 454 (63.9%) |
| ranked beyond 300 | C | 34,118 | 17 / 34,118 (0.0%) | 3,360 | 232 | 154 / 3,360 (4.6%) | 72 / 3,360 (2.1%) | 14 / 3,360 (0.4%) | 0 / 3,360 (0.0%) | — | — | — |
| unranked | B | 1,081 | 6 / 1,081 (0.6%) | 86 | 6 | 3 / 86 (3.5%) | 1 / 86 (1.2%) | 0 / 86 (0.0%) | 0 / 86 (0.0%) | 0 / 1,081 (0.0%) | — | — |
| unranked | C | 1,153 | 5 / 1,153 (0.4%) | 87 | 5 | 1 / 87 (1.1%) | 1 / 87 (1.1%) | 1 / 87 (1.1%) | 0 / 87 (0.0%) | — | — | — |

Pathway conversions excluded from the tracked denominators: B 224, C 247 golfer-seasons.

## The work pathway and the amateurs it leaves out

Full-time non-college amateur seasons, by why the pathway does or does not apply (as each season ended). "Blocked 8+" = a count of 8 or more genuinely cash-blocked weeks during the season (injury and calendar gaps pause the count, an affordable week resets it).

| Run | Group | Seasons | No start all season | Blocked 8+ | Both |
|---|---|---|---|---|---|
| A | eligible (21+, outside the top 300, no support, no family money) | 2661 | 0 | 41 | 0 |
| A | family money left | 4155 | 0 | 0 | 0 |
| A | holds support | 54 | 0 | 2 | 0 |
| A | ranked in the top 300 | 640 | 0 | 9 | 0 |
| A | under 21 | 10395 | 33 | 254 | 33 |
| A | **took work by the pathway** | 1224 |  |  |  |
| B | eligible (21+, outside the top 300, no support, no family money) | 477 | 0 | 11 | 0 |
| B | family money left | 911 | 0 | 0 | 0 |
| B | holds support | 22 | 0 | 0 | 0 |
| B | ranked in the top 300 | 242 | 0 | 7 | 0 |
| B | under 21 | 2271 | 9 | 53 | 9 |
| B | **took work by the pathway** | 224 |  |  |  |
| C | eligible (21+, outside the top 300, no support, no family money) | 516 | 0 | 10 | 0 |
| C | family money left | 853 | 0 | 0 | 0 |
| C | ranked in the top 300 | 185 | 1 | 11 | 1 |
| C | under 21 | 2280 | 16 | 71 | 16 |
| C | **took work by the pathway** | 247 |  |  |  |
| D | eligible (21+, outside the top 300, no support, no family money) | 492 | 0 | 8 | 0 |
| D | family money left | 931 | 0 | 0 | 0 |
| D | holds support | 25 | 0 | 1 | 0 |
| D | ranked in the top 300 | 263 | 0 | 2 | 0 |
| D | under 21 | 2282 | 12 | 60 | 12 |
| D | **took work by the pathway** | 246 |  |  |  |

## Provenance

## Diagnostic run provenance (pinned simulation checkout: 473690a, clean)

| Run | Segment | Started (UTC) | Ended | Seasons committed | How it ended |
|---|---|---|---|---|---|
| A seed 360013, 45 seasons, support on, workers 2 | 1 | 2026-10-31 03:57:28 | 04:27:4x | 2027-2033 (7) | Harness safeguard: season 2033 took 487 s > 420 s, caused by CPU contention from implementation agents (load ~6 on 4 CPUs); all reconciliations clean |
| B seed 2027, 10 seasons, support on, keep-after 4, workers 2 | 1 | 2026-10-31 03:57:28 | 04:28:0x | 2027-2033 (7) | Harness safeguard: season 2033 took 491 s > 420 s, same cause; all reconciliations clean; season-5 determinism digests recorded |
| C seed 2027, 10 seasons, support off, workers 2 | 1 | 2026-10-31 04:28:0x | | | started by the launch script after B ended (fresh world, not a restart) |

Resumed segments (HAL's instruction of 04:3x UTC: identical checkout 473690a, seed, support-on setting, committed
checkpoint and saved run state; --resume; the 420 s safeguard and external watchdog unchanged; at most two
diagnostic jobs at once; original processes confirmed gone and no implementation test or measurement running):
| B | 2 (resume) | 2026-10-31 04:34:11 | about 04:45 (the resume script then started A) | 2034-2036 (3 more; 10 committed in all) | resumed after season 2033 (the guard stops a run after the season that tripped it is committed); completed |
| A | 2 (resume) | 2026-10-31 04:45:47 | | from 2034 | (its end is the next row) |
| D seed 3031, 10 seasons, support on, workers 2 | 1 | 2026-10-31 05:03:04 | 05:39 (approx.) | 2027-2036 (10) | Completed; all reconciliations clean; started by the launch script after C (fresh world) |
| Replay of B season 5 (2031) | 1 | after D (launch script) | | 1 season | Completed, exit 0: identical in all 15 recorded parts (results, performance, rounds_and_holes, development, familiarity, finances, staff, fatigue_injuries, rankings, records, moments, history, cursor, diagnostics, published); the B copy world_2027_after4 was advanced in place as designed |
| A | 2 (resume) ended | 2026-10-31 04:45:47 | about 06:14-06:30 | 2034-2054 inclusive (21 more; 28 committed in all) | Ended when this session's worker process was restarted (a host-side restart during a usage-limit pause, not a safeguard): every process stopped mid-season 2055; nothing of 2055 was committed (checkpoint generation 28 = state 28 seasons, no pending season file); the dead process's lock (pid 28127) is taken over by the session's stale-lock rule |
| A | 3 (resume) | 2026-10-31 06:33:07 | | from 2055 | identical checkout 473690a (clean), seed 360013, support on, workers 2, --resume from committed generation 28; 420 s safeguard and watchdog unchanged |

Correction (2026-10-31 ~06:50 UTC, from review): the resume rows of A and B said "from 2033" and A's second segment
"2033-2054 (22 more)". Season 2033 was committed by the first segment (the guard stops a run after the season that
tripped it); the second segments began at 2034: A's covered 2034-2054 inclusive (21 seasons), B's 2034-2036 (3). The
uncorrected text is kept in PROVENANCE.before-correction-0650.md.
| A | 3 (resume) ended | 2026-10-31 06:33:07 | about 07:51 | 2055-2071 inclusive (17 more; 45 committed in all) | Completed: all 45 requested seasons; every season reconciled (errors 0+0), staff violations 0; no safeguard stop in this segment (slowest season 278 s); the population flag (+22% to +98% from the start) recorded each season, accounting reconciling |

