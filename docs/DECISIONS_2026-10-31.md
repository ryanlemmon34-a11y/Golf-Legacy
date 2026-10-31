# Owner decisions, 31 October 2026 (relayed by HAL)

Each package cites the decision it implements. Proposals still open are marked as such.

## Decided

| # | Decision | Applies to |
|---|---|---|
| D1 | Qualification windows: the N most recent editions for P2, U5, B3 (five majors) and M3, P3, U6, B4 (three Players); this season's edition only when played before the field; everything else unchanged | Done: `32a0a6f` (rules 2026-11-03) |
| D2 | Work pathway for cash-blocked adult amateurs, initial calibration (21+, outside the top 300, no support, no family money, 8 counted weeks, monthly decision) | Done: `3d3090e` |
| D3 | Amateur support caps stay $25k / $12k / $5k for the measurements; evaluate access, exhaustion, participation, conversion, region/status; no contract ceiling | Diagnostic runs |
| D4 | The support comparison runs the same build with support off; every run pinned to its recorded commit | `473690a` runs |
| D5 | Return from work to full-time amateur golf is approved in direction: allowed when finances and results support it, never guaranteed | Package pending (thresholds: D5a) |
| D6 | C2 death after retirement: active competitive golfers never die; golfers retired from competition who work as coaches or caddies CAN be eligible. Identity, records and relationships are preserved; affected staff partnerships end clearly; no death is ever dated before recorded work or play (one consistent processing date, not a week drawn inside a completed season). The mortality curve is documented as a provisional game calibration, not a validated demographic fact | C2 package |
| D7 | P2 national participation: no extra golfers because of prestige. Each nation has a share of the fixed new-golfer cohort (the cohort-size rule is unchanged); successful nations gain share at others' expense as national prestige changes; shares normalised to 100 %, smoothed and bounded; future entrants only; no change to existing golfers' countries or to per-golfer talent. Starting shares derived from the existing documented baseline and shown; allocation reproducible; share history shown | P2 package |
| D8 | Releases to main are allowed for reviewed, passing packages after HAL has checked the exact commit and confirmed readiness; no self-approval, no force pushes | All |
| D9 | Ryan's local long tests begin around 17:00 UTC (noon Central) on 31 October | Final readiness |

## Open (proposed, waiting for the owner)

| # | Question | Proposal |
|---|---|---|
| D5a | Return-to-full-time thresholds | First proposal used a hard age-30 gate; HAL's refinement under review: a sustainable season budget, a meaningful period in work, results, and a probability declining with age instead of a cut-off |
