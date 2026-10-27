# Golf Legacy — gates remaining before another 60-year historical realism run

Current result: **v0.13 has materially advanced the engine, but the next 6,000-golfer/60-year test is not ready.** Pass each gate before escalating.

| Gate | State | Verification required |
| --- | --- | --- |
| 1. Calendar and variable rounds | **Working, targeted tests passed** | 18/36/54/72, cut/no-cut, 4 majors, 40 Tier 0/1; pairing, payout and archive audits |
| 2. Weekly world rankings | **Provisional only** | 104-week decay passes; now build calibrated adjusted scoring field-strength method, ranking categories, ranking snapshots, stable ranking test cases |
| 3. Complete major qualification | **Partial** | Run legitimate amateur-only/college/club professional qualifying; enforce sponsor entries, exemptions, qualifying stage deadlines; fully populate but never fabricate major fields |
| 4. Weekly AI scheduling | **Not complete** | Proper entry deadlines, higher-prestige priority, post-major rests, fatigue, international travel, promote/drop conflicts, waitlists and calendar cascade |
| 5. Population/pathways | **Not complete** | ~6,000 meaningful active people incl. genuine amateurs, college, part-time, professionals; ~40 circuits; 500–600 competitions/year; no empty/underfilled lower-tier tournaments |
| 6. Long-term finance and history | **Partial** | No negative balance/duplicated payments; fully durable crash-safe periodic SQLite checkpoints; independent audit, indexes and replay; benchmark years 1/5/10/60/100 |
| 7. One-year 6,000-person test | **Not run** | Complete all calendar weeks without fake participants; every recorded hole, cut, payout, ranking and historic championship valid; measure duration, peak memory and storage |
| 8. Five- and ten-year tests | **Not run** | Stable fields/eligibility and career exit, no growing per-season runtime purely from accumulating retired-history records |
| 9. Two independent 60-year tests | **Not run** | Analyze completed careers with cohort censoring, exceptional careers, national growth, opportunity winners, qualification journeys, scorecards and course records |
| 10. Century-scale stress | **Not run** | 100–200 years persistent and queryable, age of records must not degrade year simulation materially |

**Preserve non-negotiable fidelity:** every actual competitive hole simulated chronologically, live field/cut/lead pressure, correct pairings and cuts, actual tournament lengths, contemporaneous legal qualification sources, and immutable full historical event scorecards. Optimize implementations and archiving, not the gameplay mathematics merely to hit the speed target.

**Benchmark goal:** two minutes or less per full-size season on the chosen local machine; only a target until measured with durable archival. No recurring cloud costs required by this architecture.

## Immediate next engineering work

1. Implement a genuine amateur and collegiate golfer population and qualifying competitions, then check complete entry-source provenance.
2. Implement weekly tour membership and scheduling (including eligibility, major blackout weeks, fixed feeders and last-minute invitations).
3. Replace the ranking field-strength proxy with a historical-performance model and calibrate point awards for top/low tours.
4. Make the archive safe against mid-season crash and benchmark persistence with realistic populations; port hot scoring loops only if benchmarks justify it.
5. After these pass, escalate 1-year → 5-year → 10-year → 2 × 60-year tests without disabling fidelity.
