# Under-21 zero-start seasons and college access: remedy options (proposal only, nothing implemented)

> **Proposal for the owner and reviewer: no rule, eligibility or support change is made here.** The evidence is
> the read-only diagnosis of the pinned 473690a runs B, C and D (`U21_ZERO_START_AND_COLLEGE_INTERIM.md`, with every
> case listed there). Rule anchors below are given at the release candidate **d70a725** (integration/v16-rc1), where
> any remedy would be made; the diagnosis's own anchors are at 473690a. Any option chosen would be a new dated rules
> version, measured on fresh worlds, and would not alter the pinned runs.

## 1. What the evidence says (exact counts)

| | B (support on) | C (support off) | D (support on) |
|---|---|---|---|
| Tracked zero-start seasons (season-end full-time, non-college amateur, 0 events) | 9 | 17 (16 under 21 + one 21-year-old ranked inside the top 300) | 12 |
| ... of which aged 20 | 9 / 739 age-20 tracked seasons | 15 / 746 | 12 / 751 |
| ... aged 18-19 | 0 | 1 (C 11938, at 19, then again at 20) | 0 |
| ... in an arrival season | 0 / 919 | 0 / 919 | 0 / 937 |
| Started the season at the credit floor (cash <= -$7,650), no family money | 9 / 9 | 16 / 16 under 21 | 12 / 12 |
| Zero-start seasons that did **not** start at the floor | 0 | 0 | 0 |
| Weeks recorded as "could not afford any event" (each case) | 18-52 | 18-52 | 18-52 |
| Weeks recorded as injured, field full, not eligible, declined, trained or rested | 0 | 0 | 0 |
| Next: work pathway at 21, week 1 / winter job at 20 / blocked again / 2036 (no next season) | 7 / 0 / 0 / 2 | 11 / 3 / 1 / 1 (+ C 1422 pathway at 22, week 13) | 7 / 4 / 0 / 1 |

College starts per college player (report row "college"): 24.4 (2027) -> 18.8 (2036) in B; C and D within 0.3.
College (tier-5) starts are flat at 10.5-11.0 each (135 events, 10,560 regular places, 99-100 % full from 2030). The
fall is in open amateur (tier-6) starts, 13.4 -> 7.5 each: about 395 events, about 54,900 places with the 1.5x
expansion, fill 52 % -> 71 %, non-college entries 16,152 -> 32,075 as part-time non-college amateurs grew 1,185 ->
3,340 (B sources: reinstated pros 1,917, college graduates 889, full-timers taking jobs 619, against 1,270 leaving).
North America: every amateur event full to its expanded cap from 2034; college entries there 6,260 -> 670 a season;
US Small College 24.6 -> 16.2, Division I 24.9 -> 18.2, international university 23.7 -> 20.8. College players' weeks
"shut out, every field full": 8.2 -> 16.2 each.

## 2. The rules that produce them (anchors at d70a725)

| Rule | Where | Effect here |
|---|---|---|
| Spendable = cash + family backing + backer funds + credit; credit = min(60,000, 8,000 + 25 % of last income) | `golfsim/finance.py:162-175`, `golfsim/season.py:3075` | a teenager with no income has $8,000 of credit; at -$7,650 or below, spendable < the cheapest trip ($350) |
| Paid work weeks only for full-time **professionals** | `golfsim/season.py:2925-2927` (`can_work`) | a full-time amateur's cash cannot move all season |
| Work pathway: full-time, non-college amateur, **aged 21+** (`MIN_AGE`), **outside the amateur top 300** (`OUTSIDE_TOP`), no support, no family money; 8 counted weeks (`WEEKS`) | `golfsim/work_pathway.py:37-39, 46-60` | under-21s are left out by design ("measured, not served") |
| Winter decision to take a job: `p_amateur_job` = sig(-1.2 + 0.8 (age-22) - 0.4 min(runway,5) + 1.0 if in debt) | `golfsim/careers.py:355-365` | about 0.07 at 19 and 0.14 at 20 at the floor; it does not read the season's blocked weeks or zero starts |
| Amateur support: rank 1-150 or the top 150 by recent form (Band A/B/C) | `golfsim/amateur_support.py:34-41, 57, 91-95` | the floor cases were ranked 380-4,431 (B, D) |
| Entry priority: own-series members class 10, other circuits 12-14; fewest-starts rotation **within** a class | `golfsim/season.py:846-899` (classes at :880-889, rotation at :892-897; `ROTATION_RANK_STARTS` :261) | open amateur fields fill with members before college players |
| Open amateur fields take 1.5x their usual field | `golfsim/season.py:262` (`AMATEUR_OPEN_EXPANSION`), `:1145` | the fixed calendar's capacity |

## 3. Options for the under-21 floor (smallest first)

| Option | Change | Expected effect (from the evidence) | Trade-offs / risks |
|---|---|---|---|
| **U1. Evidence-triggered pathway from 18** (recommended) | `work_pathway.MIN_AGE` 21 -> 18 (only the age gate; the 8 counted blocked weeks, no support, no family money and outside-top-300 conditions stay). One constant and the rule text. | Every one of the 37 under-21 cases had 18-52 counted weeks, so each would have qualified at a monthly plan once 8 were counted, instead of a lost season. Uses the existing, already-measured mechanism; the trigger is the golfer's own recorded evidence, not age alone. | Young golfers move to part-time (job, living costs, fewer practice weeks) and may develop more slowly; whether they can then afford trips needs measuring (the 21+ pathway golfers' outcomes are the comparison). Changes outcomes in every world that has such a case (new rules version). |
| U2. Winter job decision reads the blocked season | add a term to `p_amateur_job` for the season's counted blocked weeks (or zero starts) | Faster exit after a lost season | Does **not** prevent the first lost season; a second calibrated term. |
| U3. Paid work weeks for stuck full-time amateurs | extend `can_work` to full-time amateurs who are `stuck` (no affordable plan) | Cash moves; some trips become affordable within the season | Blurs full-time vs part-time for every stuck amateur, not only the floor; wage and amateur-status design questions; broader behavioural change. |
| U4. Family help for teenagers living at home | a small, recorded home-region trip allowance under 21 with no family money left | Restores some starts | Introduces money the model does not have; needs an owner decision on what a family covers (design question (a) in the diagnosis). |

Support-off only: a ranked amateur at the floor is excluded from the pathway by `OUTSIDE_TOP` (C 1422 ranked 50
waited until 22; C 11938 ranked 7 lost two seasons). With support on these golfers are Band A-C and covered, so this
affects only the comparison arm; **recommendation: document, no change** (or, if wanted, apply `OUTSIDE_TOP` only
when amateur support is switched on).

## 4. Options for college access to open amateur events (smallest first)

| Option | Change | Expected effect | Trade-offs / risks |
|---|---|---|---|
| **K1. A bounded college share in open amateur fields** (recommended) | in tier-6 events, college players hold up to a share of places (e.g. 20 %) at the members' class, ordered by the existing fewest-starts rotation; the bound kept by `_bump`, as the Premier visitor share already is (`season.py:876-879`) | Restores college players' open-amateur starts where fields fill (North America) without changing fields elsewhere; bounded and explicit | One new constant to calibrate; members (largely reinstated pros playing part-time) lose some starts in full fields. |
| K2. College players at the members' class | class 12 -> 10 for college players in tier-6 events | Rotation then shares starts between members and college players by starts-so-far | Unbounded: could displace members heavily where college programmes are dense; a larger behavioural change than K1. |
| K3. More capacity where fields fill | raise `AMATEUR_OPEN_EXPANSION` (1.5 -> 2.0) for regions at the cap, or add events | More starts for everyone | Changes the field-size contract and simulation cost; the versioned calendar (v2) would need a new version for added events. |
| K4. Address the source | revisit how reinstated pros and part-time amateurs choose open amateur events (or their reinstatement rate) | Lowers demand rather than rationing | A career-model change with wide effects; slowest to validate. |

Also possible: **no change**. College tier-5 starts are steady (10.5-11 a season); the decline is in optional open
amateur starts as the population grows. If 18-19 starts a season for college players is acceptable, the finding is
a calibration note, not a defect.

## 5. Proposals put to the owner (decision window 07:08:39-07:23:39 UTC, 31 October) -- NOT implemented

Recorded as proposed by the reviewer; nothing is changed until the reviewer confirms the window's outcome.

| # | Proposal | Closest option above | What implementing it would touch (at d70a725) | Points to settle or measure |
|---|---|---|---|---|
| P1 | Lower the persistent cash-blocked adult amateur work-pathway minimum age to 18; keep the eight counted weeks, no family money, no support, the rank rule and every other safeguard; no grants, no guaranteed starts | U1 | `work_pathway.MIN_AGE` (`golfsim/work_pathway.py:37`) and its rule text; a new dated rules version; the pathway's docs ("Who") | outcomes after the job (starts, development, return/turn-pro) for 18-20-year-olds against the 21+ comparison; no other eligibility rule moves |
| P2 | Eligible college amateurs get equal home-region access to ordinary open amateur events, with the rotation counting amateur-event starts rather than school starts; closed, national and championship qualification unchanged; no universal field expansion, no forcing of target counts | between K1 and K2 (equal class, but limited to home-region ordinary open events) | the entry class in `Season.priority` for tier-6 ordinary open events when a college player's home region is the event's region (class 12 -> the members' class 10, `season.py:880-889`); the rotation key at `season.py:892-897`, which now counts every start this season (`self.played`), would count only open-amateur starts for those events; the 1.5x expansion and calendar unchanged | "home region": the college's region or the golfer's residence (the diagnosis' North America cases are both); which series count as "ordinary open" (excluding closed, national and championship); members' starts lost in full fields (to be reported); the same rotation for members, so their key would also count open-amateur starts |
| P3 | Keep the current richer decision evidence despite the estimated 11-13 % archive growth; measure the actual full-world impact | -- (E1, d70a725) | nothing to change; the full-population smoke on the exact candidate measures season-file size with and without the evidence key, season time, save size and the 13-plan / 3-row bounds | the measured numbers replace the estimate in DECISION_EVIDENCE.md |

## 6. How a chosen option would be validated
New dated rules version; fresh v2 worlds only; focused unit tests; then paired fresh full-population runs (option
on/off, same seed) of 10 seasons with: under-21 floor seasons and zero-start counts, time to first start after the
floor, pathway and job outcomes by age, development by age, college and open-amateur starts per player by region,
field fill, members' starts; and the full suite. The pinned A-D runs stay as they are.
