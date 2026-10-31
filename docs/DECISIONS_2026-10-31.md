# Owner decisions, 31 October 2026 (relayed by HAL)

Each package cites the decision it implements. Proposals still open are marked as such.

## Decided

| # | Decision | Applies to |
|---|---|---|
| D1 | Qualification windows: the N most recent editions for P2, U5, B3 (five majors) and M3, P3, U6, B4 (three Players); this season's edition only when played before the field; everything else unchanged | Done: `32a0a6f` (rules 2026-11-03) |
| D2 | Work pathway for cash-blocked adult amateurs, initial calibration (21+, outside the top 300, no support, no family money, 8 counted weeks, monthly decision) | Done: `3d3090e` |
| D3 | Amateur support caps stay $25k / $12k / $5k for the measurements; evaluate access, exhaustion, participation, conversion, region/status; no contract ceiling | Diagnostic runs |
| D4 | The support comparison runs the same build with support off; every run pinned to its recorded commit | `473690a` runs |
| D5 | Return from work to full-time amateur golf is approved in direction: allowed when finances and results support it, never guaranteed | `build/v16-amateur-return` (rules 2026-11-06) |
| D5a | (HAL's delegated decision, 04:31 UTC window) No hard age-30 cut-off: sustainable funding, relevant results, a meaningful period in work, a smooth probability declining with age; avoid lifestyle-flipping advantages; thresholds provisional; validate return and re-block rates | `golfsim/amateur_return.py` |
| D6 | C2 death after retirement: active competitive golfers never die; golfers retired from competition who work as coaches or caddies CAN be eligible. Identity, records and relationships are preserved; affected staff partnerships end clearly; no death is ever dated before recorded work or play (one consistent processing date, not a week drawn inside a completed season). The mortality curve is documented as a provisional game calibration, not a validated demographic fact | C2 package |
| D7 | P2 national participation: no extra golfers because of prestige. Each nation has a share of the fixed new-golfer cohort (the cohort-size rule is unchanged); successful nations gain share at others' expense as national prestige changes; shares normalised to 100 %, smoothed and bounded; future entrants only; no change to existing golfers' countries or to per-golfer talent. Starting shares derived from the existing documented baseline and shown; allocation reproducible; share history shown | P2 package |
| D8 | Releases to main are allowed for reviewed, passing packages after HAL has checked the exact commit and confirmed readiness; no self-approval, no force pushes | All |
| D9 | Ryan's local long tests begin around 17:00 UTC (noon Central) on 31 October | Final readiness |
| D10 | F1.c amateur support form (relayed by HAL): the roadmap asks to distinguish cash sponsorship, equipment, restricted coverage and prize eligibility, not to build all four. The chosen policy is restricted in-kind golf expenses only; no unrestricted cash or living costs; amateur prize eligibility unchanged. The $25k / $12k / $5k caps are the chosen initial test calibration (changing them needs evidence and a decision; keeping them does not) | Built (`golfsim/amateur_support.py`); not a missing feature |
| D11 | F2 coverage (HAL, in preparation): table-driven reconstructed eligible / cannot-pay fixtures from an independently revalidated manifest of all 269 historical affordability declines -- coverage of the cases, not a historical replay (exact past balances are unknown) | F2 test package (pending the manifest) |
| D5a | (HAL's delegated decision, 04:31 UTC window) Return-to-full-time thresholds: no hard age-30 cut-off; sustainable funding, relevant results, a meaningful period in work, a smooth probability declining with age; avoid lifestyle-flipping advantages; provisional; validate return and re-block rates | `build/v16-amateur-return` |
| D12 | G1 unused municipal courses (Ryan replied "I agree!" at 05:08 UTC to HAL's proposal): meaningful local/home-course roles and suitable lower-level hosting where eligible, without forcing every course into rotation | `build/v16-geography` follow-up |

## Open (proposed, waiting for the owner)

None at present.
