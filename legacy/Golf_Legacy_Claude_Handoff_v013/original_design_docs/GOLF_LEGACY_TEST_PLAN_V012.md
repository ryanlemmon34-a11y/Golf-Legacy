# Golf Legacy — v0.12 Test and Integration Plan

**Status:** Design specification and test plan only. No simulation-engine code, existing save data, scoring probabilities, or historical test results have been modified by this plan.

**Foundation:** v0.7 detailed chronological hole-by-hole scoring and tournament audit rules; v0.10 cascading calendar/weekly scheduling and prestige design; v0.11 variable tournament formats and fixed major weeks. Existing package versions are separate; integration must be verified before another 60-year simulation.

**Overall goal:** A large, evolving, fully auditable golf world. All competitive events resolve real simulated holes in causal order. Rich history is retained permanently. Target <=120 seconds per full season on the chosen Windows test PC with realistic field sizes, while preserving realism. This is a performance goal, not a verified capability.

## A. Ranking systems: keep FOUR concepts separate

1. **Global professional ranking (OWGR-style):** recent *eligible* professional results across approved circuits, using relative field strength and placements. Used for world standing and *some* entry exemptions; not interchangeable with a tour card.
2. **Tour season points / Order of Merit:** season-long, tour-specific results and purse or points system; controls retaining membership, conditional status, promotion, Q-school opportunities, and some invitational positions.
3. **Amateur rankings:** collegiate/national/international amateur competitions, used for amateur exemptions, recruiting, and professional development opportunities. No routine professional prize money.
4. **Player prestige and hype:** career reputation and current popularity, used primarily for sponsorship, appearance invitations where permitted, and attracting coaches/caddies; never substitute for earned qualification or world-ranking points.

### OWGR-inspired core (2026 reference; fictional implementation may differ)

Reference: https://www.owgr.com/how-the-ranking-works and https://www.owgr.com/faq

- Ranking updated once weekly **after all sanctioned events for the previous week are final**, before the next week's normal field assessments. Preserve each week's archived rankings.
- Rolling **104-week** window; points kept at full weight for **13 weeks** then gradually reduced over the following **91 weeks**.
- Divide adjusted points by eligible starts, with a **minimum divisor of 40 and maximum of 52 eligible tournaments** over the period.
- Event ranking-point pools depend on **field strength calculated from competitors' observed adjusted scoring performance** (not solely prestige, name recognition, or purse). Field strength snapshots are locked before scoring; do not use the final winner to retroactively recalculate field strength.
- Competition points follow finishing positions, ties and cut/eligible-completion rules; distinguish a 54-hole eligible event's reduced points allocation (**75%** reference) from a 72-hole event (**100%** reference). Majors receive separately defined peak winner points; OWGR specifies **100 winner points** for each of four majors. Treat exact field-rating curves as a calibration task rather than pretend to reproduce the proprietary/performance curve by multiplying prestige.
- 18- and 36-hole local/mini/qualifying events **normally do not award world-ranking points**. They may count toward local rankings, tour points, qualification, earnings where legal, and historical course records. Model any recognized exception explicitly, not automatically based on purse or length.
- Repeat-winner bonus within 52 weeks exists in current OWGR; implement/test as a separate toggle and calibrate for our fictional circuits.
- Preserve a clear distinction between *world ranking points*, *tour season points*, *money*, and *personal prestige*. A title can grant a tour-card exemption independent of all four.

### Tour membership and event qualification

Maintain durable typed eligibility: full tour card; conditional status; prior-winner exemption with expiry; world-ranking exemption as of a published cutoff; tour-standings exemption; qualifying-event result; amateur champion exemption; national-open series exemption; club-professional allocation; tournament discretionary invitation. Every granted exemption stores `source_type`, `source_id`, `target_event_or_tour`, `earned_week`, `expires_week`, `priority`, `amateur_conditions`, and `status`.

- **Global ranking is not tour membership.** A top-ranked golfer still needs an actual membership/exemption/qualifier path for an event. Tour card status is calculated from tour-specific season standings and explicit winner/Q-school exemptions.
- Each event specifies its own field size, exemption categories/quotas, cut rules, lock time, reserve/waitlist policy and eligibility cutoff date.
- Field allocation is a cascade: majors first, then important fixed-week feeders and flagship tournaments, then ordinary Premier, Challenger, Regional, Mini, College/Amateur.
- Major week locks: Week **14** Legends Masters, **19** Premier Championship, **24** American Open, **30** Brittania Open; globally exactly one competitive event in each week. Reserved feeder weeks: **13, 18, 23, 29**; additional national and amateur qualifying must occur before its target event's lock.
- Preserve **40 combined Tier 0/1 championships** annually: four Tier 0 majors plus 36 Tier 1 events consisting initially of eight flagship, 20 standard and eight opportunity events. Four opportunity events immediately follow majors in Weeks 15/20/25/31.
- Distinguish event fixed prestige (history/brand), **actual field strength**, prize purse, OWGR-type points and personal golfer prestige. Weaker post-major fields typically produce fewer ranking points without stripping the winner's title or future tour-card exemption.
- Winning *any eligible Premier tournament* provisionally earns a multi-season card (initial target: two following seasons), while specific major invitations must be checked against that major's published qualification categories. Some event titles provide direct invitations and others only influence rank. Do not assume all Premier winners qualify for all majors.
- Weekly AI plans should re-evaluate eligibility, goals, fatigue, travel, opportunity, tournament similarity/warm-up, finances and confirmed commitments. Legitimate late qualifying results trigger immediate replanning before field lock. Golfers cannot start two same-week events. Major invitations often supersede rest plans or non-locked commitments; audit any withdrawal and waitlist replacement.
- Preserve all historical exemption source links (e.g., Kenya National Open winner -> Brittania Open participant). Current reference models include Masters amateur and rankings categories and The Open's national-open qualification series.

Sources for comparison (rules will be adapted to the fictional world):
- https://www.pgatour.com/article/news/inside-the-field/2026/03/30/masters-tournament-how-they-qualified-who-is-playing-augusta-national-field-eligibility-status-scheffler-mcilroy
- https://www.usopen.com/2026/articles/current-exempt-players-126th-us-open-shinnecock.html
- https://www.theopen.com/qualification/pathways-and-exemptions
- https://www.pgatour.com/article/news/latest/2025/11/17/what-is-at-stake-2026-status-on-line-as-pga-tour-concludes-at-the-rsm-classic-top-100-aon-next-10-fedexcup-fall

## B. Step-by-step implementation and test gates

### Gate 0 — Freeze the reference and establish measurable baselines

- Preserve untouched copies of v0.7 scoring, v0.10 design, and v0.11 calendar. Record source hashes, seed list, hardware, simulator version and calibration constants.
- Measure CPU time, peak RAM, database size and write duration for existing 1,700/191 and 4,500/341 year runs; distinguish observed benchmarks from projections.
- **Pass:** repeatable baseline reports with old scoring/historical validations still passing.

### Gate 1 — Calendar and mixed tournament formats (1-year unit/integration test)

- Implement v0.11 18/36/54/72-hole formats in the actual detailed scoring engine (currently only implemented in calendar metadata); preserve chronological tee-time/pairing order, live cut-line and contender pressure, proper cuts, playoffs, payouts and course records.
- Integrate week-number priority calendar and global blackout weeks 14,19,24,30; majors fixed, other events assigned around them.
- **Pass:** 100% events have correct scorecard length; round totals equal hole sums; correct cut/ties and pairings for all four lengths; no major-week conflict; no duplicated course/time or golfer/week; money reconciles; qualifiers happen before their target major.

### Gate 2 — World ranking and tour ranking system (controlled short tests)

- Implement weekly global professional ranking, world-adjusted performance measure, field-strength snapshots, finish-based point distribution, two-year decay/divisor, 54-hole adjustments and major point rules. Add tour points/Orders of Merit and separate amateur ranking.
- Validate ranking math in deterministic fixtures: rank order, equal adjusted points, ties, old-point decay at weeks 13/14/104/105, starts divisor limits 40/52, duplicate entries, 54 vs 72 field-equivalent events, cut outcomes, points for 18/36 local events normally zero.
- **Pass:** rankings reproducible from archived tournament facts; weekly standings update precisely once at intended boundary; no prestige/purse leakage into world points; rankings follow skill/performance across many events rather than becoming a proxy for tour branding.

### Gate 3 — Eligibility, field allocator, and weekly AI scheduling (1–3 season tests)

- Integrate membership statuses, earned exemption ledgers, event priority categories, qualifying stages, cutoff dates, waitlists and post-result replanning. Set explicit independent eligibility models for each major.
- Test a Week 13 feeder winner entering Week 14; a Week 23 American Open finalist; a national-open winner qualifying for Week 30; an amateur invited without turning pro; a teaching professional entering Week 19; a lower-ranked conditional golfer winning Week 20 and obtaining next-year full card.
- **Pass:** every entrant has traceable eligibility; no unqualified entries, silent displacements, later-than-lock qualifications, duplicate same-week starts or retroactive pairings; higher-priority earned entry is respected while non-eligible golfers cannot bypass criteria by reputation alone.

### Gate 4 — Expanded active population and one-season scale test

- Target approximately **6,000 active golfers, 40 circuits, 500–600 championships/qualifiers annually**, with actual college/amateur and part-time participants, new entrants, low-success dropouts, financing and regional calendars. Keep population targets flexible (sufficient entrants, not rigid slots).
- Do not globally allow professional world-ranking points from one-day local starts. Track all local event histories and separate amateur rankings.
- **Pass:** fields full at realistic rates without fabricated entrants; no duplicate starts; no widespread insolvency exploits; full integrity/finance audits; performance reported for normal and archive-writing modes.
- **Performance gate:** ideally <=120 seconds/season on target PC; if not, optimize scoring/core and memory/SQLite access before proceeding to a 60-year test; never drop tournament holes to meet performance.

### Gate 5 — Five-year population / ranking stability test

- Check yearly prospect intake, active populations by tier, amateur-to-pro transitions, card turnovers, conditional categories, forced/voluntary retirements, part-time careers, tour financial sustainability, blocked/double-booked fields and ranking diversity.
- Check that post-major opportunities are actually weaker fields on average because elite golfers strategically rest—not because of forced bans.
- **Pass:** no runaway count inflation, systematic underfilled event weeks, perpetual card hoarding, artificially guaranteed promotion, or predictable schedule exploit.

### Gate 6 — Ten-year history-depth and career mechanics test

- Compare Year 1 and Year 10 sim time per comparable event-hole workload. Measure database size, historical query latency, rank replay accuracy and retroactive history correctness.
- Track ranking trajectories, age distributions, attrition rates, budget and staff access, changes in national talent supply, and qualification source representation.
- **Pass:** records reconstruct exactly; no drift in old event scores or source links; acceptable performance scaling; if Year 10 materially slower solely because history grew, optimize indexes/caching/write batches before 60 years.

### Gate 7 — Two independent, FULL 60-year worlds

- Run two fixed seeds, preferably 1217 and 2601 for *distributional* comparison with older worlds. Preserve the same rules during both worlds. Do not interpret individual same-seed careers as directly comparable once event systems change.
- Record every competitive hole for sanctioned events (compactly); archive complete scorecards, hole/venue/layout records, pairs/tee-time details, world rankings each week, tour season points, earned exemptions, amateur/college titles, staff contracts, national development and financial events.
- Compare distribution of: unique major winners; 5/10/15-major careers and overlapping legends; winners' ages and peak spans; major contention without victories; ranking #1 weeks and turnover; world top-100 entrants to majors; Premier wins by world #101+ entering the week; post-major weaker field strength; tour-card rescues and career longevity; Q-school, amateur, college, national-open and club-pro qualification routes; return of homeland stars; underrepresented-country breakthroughs; history storage/performance degradation.
- **Pass:** no integrity failures; historical outcomes evaluated as plausible ranges and distributions rather than scripted result quotas. Document suspicious outputs even if no hard gate exists.

### Gate 8 — Centuries-long archive stress test

- Preserve a snapshot from a 60-year world, then run to **100 and 200 years** with one fixed seed (and a second only if performance allows). Check save/reopen integrity, historical queries, archived rankings and country storylines, staff relationships and course records; measure Year 1/10/30/60/100/200 sim time normalized by holes/events.
- **Pass:** no loss of history and no material slowdowns *solely due to archive depth*; eventual query benchmarks and player-facing responsiveness established on target hardware.

## C. Example qualification rules to parameterize, not hardcode inside ranking

- Legends Masters W14: previous champions (policy-defined), high finishers, top-50 year-end and Week 13 global ranking cutoff, selected national/international amateur winners, Week 13 specific feeder, other explicitly defined invitations. Smaller field (e.g. 90–100).
- Premier Championship W19: elite professional categories, tour winners/rankings, qualified top club/teaching professionals from Week 18, relevant prior major champions. Larger field (~156).
- American Open W24: rolling world ranking cutoff (illustratively top 60), selected national amateur/college winners, open regional/final qualifying, prior champions and selected tour standings. Larger field (~156).
- Brittania Open W30: ranking/previous champions, leading tour season standings, regional qualifying, designated national opens (e.g. Scotland/Kenya/Japan/Australia), qualified amateur champions from multiple continents; late Week 29 final qualifier. Larger field (~156).
- **Every quota/cutoff is event-specific and dated.** Duplicate-exempt players free an entry to the next eligible category according to an explicit fill order. No fabricated winner-only major invitation when a source event did not grant one.

## D. Acceptance data exported at every test stage

`weekly_world_rankings`, `weekly_world_strokes_gained`, `tour_season_standings`, `amateur_rankings`, `field_rating_snapshots`, `tournament_point_awards`, `qualification_exemptions`, `membership_history`, `entry_priority_audit`, `tournament_scorecards`, `weekly_golfer_plans`, `course_record_history`, `financial_ledger`, `country_development`, `run_performance_metrics`, `invariant_test_results`.

**Bottom line:** build and validate ranking/qualification before running our next giant world. Do not conflate ranking, tour cards, money, prestige, event strength or tournament length. A lower-prestige Premier victory is meaningful, especially for a conditional golfer, while stronger fields and majors still drive world-ranking and sponsorship outcomes.
