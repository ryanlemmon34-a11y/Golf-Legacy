# Golf Legacy: Prioritized Roadmap and Test Gates

The major project risk is no longer 'can a golf round be simulated?' It is whether complete **global populations, tournament entry, ranking, finances and immutable history** work together in a large, performant world. Do not run two 60-year tests until basic gates pass.

| Gate | Current | Engineering work | Exit evidence |
|---|---|---|---|
| 0 Freeze/verify current implementation | **Done for handoff** | Source preserved, main tests pass, benchmark reports included | SHA-256 manifest, 8/8 v0.13 tests, sample DB auditable |
| 1 Mixed formats + major weeks | **Core done** | Add edge-case tests for field sizes, warmup weeks, cut thresholds and every course format | 100% completed hole sums; 4 blackout weeks; purse/source integrity |
| 2 Ranking model | **Partial** | Replace pre-event technical-ability field proxy with actual calibrated scoring-performance / field-strength model; world, tour, amateur rankings; full points methods | Deterministic fixtures + archived ranking replay; no ranking points from ordinary 18/36 local events |
| 3 Major qualification and eligibility | **Partial** | Amateur/college/club-pro populations, exemptions, direct vs staged qualifying, dated lock/priority/waitlist; Premier win conditional/full status | Full major fields without fabricated entrants; correct W13→14, W18→19, W23→24, W27→30; sample 18yo amateur major entrant |
| 4 Weekly AI schedule and calendar cascade | **Not yet** | rolling 8–12-week plans, travel/warmup/fatigue/course economics, prestige utility, late replacement, entries with lifecycle states | No duplicate starts; elite start selectively; conditional world #130 legitimately targets post-major event; new major qualifier displaces lower priority before lock |
| 5 Full amateur/college/part-time career continuum | **Not yet** | country-wide intake, college programs, amateurs, careers/inactive/pro return, Q-school, financial exit and younger/older crossover | Underfilled events rare, no artificial retirements, legitimate first-time major at 38 and no forced major storyline |
| 6 Safe durable archive + performance | **Partial** | SQLite transactions and periodic checkpoint/recovery, indexes, backup/reopen, scalable scoring core; Rust/Numba profiling if needed | normal **archived** full-size season <=120s target on reference PC, recover after forced midweek stop |
| 7 One-year full-world benchmark | **Not done** | ~6,000 active, ~40 circuits, 500–600 competitions (including actual amateur/local), all 52 weeks | All holes scored, fields funded, legitimate entries, memory/time/DB growth measured |
| 8 Five-year and ten-year stability | **Not done** | Run fixed seeds, cohort/withdrawal/economics and year-by-year time/storage | Proper card churn and career exits; Year 10 comparable cost to Year 1 normalized by holes |
| 9 Two independent 60-year worlds | **Not done in expanded v0.13** | Two seeds 1217/2601; no mid-run tuning; full archive and output comparisons | Age/country/rank/majors/qualification and career arc distributions, no integrity failures |
| 10 100–200-year depth tests | **Not done** | Continue from real persisted world with schema/checkpoint migration | Old results query correctly, no record loss, controlled performance degradation |
| 11 Player UI and personal career loop | **Not done** | Tauri + React + local simulation engine if justified; monthly interface, encyclopedia, restart/spectator | Golfer profiles/history navigable and true working personal manager save |

## Non-negotiable technical constraints

- Preserve real field, real golfer identity, real scheduled holes, real event length and pressure/pairings.
- Replaying the same world under different *UI playback speeds* must produce the same histories given the same decisions and seed.
- Never fix an underfilled major by inventing entrants without qualification; build the missing routes instead.
- No fake initial prestige gains, imaginary coach effects or results pasted in as storylines.
- Save and audit complete real scorecards and dated records. Lower overhead is acceptable by smaller **actual** event lengths and efficient storage, not result approximation.
- Do not overfit Tiger or Nicklaus 'quota' of major wins; long career tails can be rare and overlapping, with no guarantees.

## Realism assessment metrics for every 60-year run

1. Major winners by age, first win age, annual competitive ability distribution; separate founding veterans versus generated cohorts.
2. Major wins per golfer (1, 2–4, 5+, 10+, 15+), runner-up counts, top-fives and dominance windows.
3. Weeks ranked #1, turnover of top 10 and top 100, how much better top 1/10/50/100 actually score.
4. Breakdown of major entry reason: past winner, top ranking, college/amateur, club pro, national open, open qualifier, regular Premier victory.
5. Elite annual starts and rest near four majors; field-strength differences at post-major events; wins by outside top 100.
6. Country-level trajectories, supply, infrastructure, sponsors and lagged response to national heroes. Detect ceiling saturation.
7. Tour-card/qualification pathway, regional/part-time persistence, money and financed starts, exits and comeback outcomes.
8. Immutable course/hole records by layout, repeat wins, fixed-course versus rotating-course championship history.
9. Coach/caddie career histories and differences (when implemented); prevent staff overpowering skill.
10. Timing per year (including durable checkpoint), RAM, SQLite size/query speed and repeatable audit validation.

## Suggested immediate Claude assignment

Ask Claude to **perform a code architecture + correctness audit, then propose a small prioritized patch**, not to completely port everything to Rust or implement 6,000 golfers immediately. Most leverage: eliminate hidden performance bottlenecks from weekly ranking and history writes while preserving exact scoring, build data types for field eligibility/entry phases, and map 15 designed attributes to current code to find gaps. Require a before-and-after reproducible benchmark and tests. The enclosed `CLAUDE_REVIEW_PROMPT.md` is ready to paste.
