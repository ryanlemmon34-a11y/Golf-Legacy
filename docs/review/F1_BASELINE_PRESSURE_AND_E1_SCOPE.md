# F1 baseline amateur financial pressure, and the E1 decision-evidence scope

> Review document (read only; nothing in the simulation changes). It records two items the reviewer settled on
> 31 October 2026 so the traceability matrix can close them: the **baseline** amateur financial-pressure assessment
> (F1.i, part of CQ3) and the **scope of the decision evidence** (E1.f.7, open item O8).

## 1. F1: baseline amateur financial pressure (pinned build 473690a)

Source: `docs/review/DIAGNOSTIC_RUNS_BCD_INTERIM.md`, "Amateur standing" table and the work-pathway table. These are
runs B (seed 2027, amateur support on), C (the same seed, support off) and D (seed 3031, support on). They are
10 seasons each on the **pinned build 473690a**: the pathway starts at age 21 there and the old college access
applies.

"Tracked" means a full-time amateur outside college at season end. "Cash-blocked" means at least one week in the
season when the golfer was eligible for an event and could afford none of them. "Count 8+" means 8 or more such
weeks counted, with injury and calendar gaps pausing the count.

| Measure (run B, support on) | Value |
|---|---|
| Amateur top 50: tracked golfer-seasons (season-end full-time, not college; pathway conversions excluded) cash-blocked 1+ week | **0 / 87** (0.0 %). Separately, of all 500 top-50 amateur golfer-seasons, 500 were supported |
| Ranked beyond 300: tracked golfer-seasons cash-blocked 1+ week | **136 / 3,368** (4.0 %) |
| Ranked beyond 300: tracked, count 8+ | 62 / 3,368 (1.8 %) |
| Ranked beyond 300: tracked, no start all season and cash-blocked | 9 / 3,368 (0.3 %) |
| Ranked beyond 300: supported | 454 / 34,232 amateur golfer-seasons, all statuses (1.3 %); 290 / 454 drew 98 % or more of their cap (not necessarily all of it) |
| Golfer-seasons converted to work by the pathway (age 21+; not in the tracked denominators above) | **224** (C 247, D 246) |

**Assessment, as settled by the reviewer.**
- At the baseline, financial pressure falls on the **lower-ranked** amateurs, not the elite.
  - None of the 87 tracked top-50 golfer-seasons was cash-blocked. This covers season-end full-time non-college
    amateurs only, not every top-50 amateur and not the golfers converted to work.
  - 136 of the 3,368 tracked golfer-seasons ranked beyond 300 (4.0 %) were.
  - The pathway turned 224 golfer-seasons into working amateurs.
- Turning support off (C) puts pressure on the elite (17 / 72 tracked top-50 golfer-seasons blocked) but changes little beyond
  300 (154 / 3,360 tracked, 4.6 %).
- In the reported B and C breakdown, every tracked golfer-season with no start was cash-blocked: the "no start, never
  cash-blocked" column is 0 in every row. The weekly ledger covers only tracked golfers (full-time, not college).
  Part-time and other untracked amateurs do have no-start seasons, and this statement says nothing about them.

**Before calibration.**
- This is a description of the baseline, not a calibration verdict. Tolerance bands for F1.i await the owner (CQ3, O5).
- The effect of the new policies has not been measured here: the pathway from age 18 (rules 2026-11-10) and college
  open access (2026-11-11). That effect comes from the paired fresh full-population comparison runs on `c0d1ea5`
  (a21old against a18old for the age; a18old against a18new for college access), reported separately.

## 2. E1: scope of the decision evidence (O8)

Reviewer's clarification (31 October 2026): the format **/2** decision evidence fulfils the original E1
requirement.
- `docs/DECISION_EVIDENCE.md` lists what /2 does not record (its "remaining gaps"):
  - the weekly entry choice, with per-event values and trip costs;
  - the planner's values for each week;
  - the coach and caddie career draw;
  - the backers' review terms and draws.
- These gaps are **disclosed limitations, not missing features**. No format /3 is planned in this pass, and the
  instrumentation is not to be expanded.
- In the traceability matrix, E1.f.7 moves from "design decision pending" to "done with known limitation" (the
  disclosed gaps). O8 closes as decided.

The full-world size and time of the evidence are measured on the full-population smoke. Pre-final figures, from
`0a05310`, seed 4207, evidence on against off:

| Measure | Season 1 | Season 2 |
|---|---|---|
| Season time | 200.5 s (on) vs 188.4 s (off) | 213.6 s (on) |
| Season file | 13.04 MB vs 12.21 MB | 12.57 MB (on) |
| Evidence, gzip | 830 KB: 6.4 % of the file, +6.8 % over the file without it | 901 KB: 7.2 % of the file |

- Outcomes were identical with the evidence on and off.
- The checkpoint was 38.1 MB on against 36.4 MB off.
- Bounds held: at most 13 plans, 0 over the limit, at most 3 career rows.

The exact-head figures (`c0d1ea5`) replace these in the final report.
