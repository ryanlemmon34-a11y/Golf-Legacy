# Golf Legacy — Global Scheduling, Golfer Prestige & World Archives

**Design version:** v0.10  
**Status:** Approved direction / proposed mechanics. This document is a **design addendum** and does **not** claim these systems are implemented in the game engine.  
**Baseline:** v0.7 detailed hole-by-hole engine, v0.8 capacity experiment, v0.9 standalone calendar preview. Preserve the simulation and historical outcomes unless an explicitly documented change is being tested.  
**Primary design goals:** Rich persistent world over centuries; historically faithful, hole-by-hole simulation; predictable scheduling; fast full seasons without discarding historical records. User target: approximately 120 seconds per full season on the intended PC, to be measured rather than assumed.

## Decisions and principles recorded

1. **Calendar cascade:** Schedule in global descending order of importance: fixed major weeks -> historic/prestige championships and qualification routes -> premier tours -> challenger tours -> regional and mini-tours -> college/amateur/local competition. The entire world reserves four exclusive major weeks.
2. **Static historical anchors:** Important event *series* get stable week numbers annually. In particular, their winners must be able to enter the associated major in a subsequent week; this means the qualifying event must end before the major field locks. Regular events can shift weeks; historical series retain identity despite course rotation and date changes when explicitly allowed.
3. **Weekly golfer planning:** Every AI golfer maintains an intended rolling schedule and reevaluates options each week. Monthly human-player management sets standing priorities; the agent performs routine weekly planning without demanding weekly UI decisions.
4. **New earned opportunities can supersede plans:** A newly earned major berth normally overrides training/travel and lower-priority commitments. The system must cancel or replace registrations correctly, refund or charge eligible expenses according to clear rules, and fill released spots from waitlists **before** field lock.
5. **Elite players compete selectively:** They seek important and financially valuable tournaments, schedule deliberate warm-ups, and protect stamina. Selectivity must follow incentives, event access and readiness, not a hard-coded low tournament count by reputation.
6. **Golfer prestige:** A dynamic reputation/hype variable separate from current golf ability, world ranking, or tournament prestige. Performance, major wins, historical milestones, media exposure, setbacks, and decay influence it. Prestige drives sponsorship *opportunities* and market access to staff, but does not replace ability or money.
7. **Connected world encyclopedia:** Dedicated **Golfers, Caddies, Coaches, Courses, Tours** directories, each with search/filter, current detail pages, all-time histories, records and cross-links. Tournament series and countries should also be directly browsable as first-class pages.
8. **Preserve the record:** Every tournament edition has a stable ID, qualification provenance, entries, round/hole results, pairings, records, and prize information. Keep dated historical event changes and retired careers, not just current record holders.

## 1 — Scheduling model

### 1.1 Time coordinate and immutable majors

Primary calendar coordinate is `(year, week)` with weeks 1 through 52. Within each week use actual round days, tee times and hole sequence; do not reduce the tournament engine to week- or round-level random outcomes.

| Week | Major championship | Calendar rule | Venue rule |
|---:|---|---|---|
| 14 | Legends of Golf Masters Event | Only sanctioned competitive event worldwide | Fixed course series, versioned layouts |
| 19 | Premier Tour Championship | Only sanctioned competitive event worldwide | Rotating |
| 24 | American Open | Only sanctioned competitive event worldwide | Rotating US hosts |
| 30 | Brittania Open | Only sanctioned competitive event worldwide | Rotating Britain/Ireland links |

No lower-tier, college, amateur, qualifying, junior, or overlapping sanctioned competition may be assigned to weeks 14, 19, 24, or 30. Noncompetitive practice, rehab, preparation and travel continue.

### 1.2 Cascade stages

1. **Reserve majors**, with provisional field quotas and the latest possible entry confirmation time.
2. **Place anchored historic/prestige tournaments**, especially feeder events whose winning route or qualifying points lead to a major. These use stable `series_id`, preferred annual `week`, and explicit `qualifies_for_series_id`/`qualifies_for_edition_id` where applicable.
3. **Place qualification stages** and ensure all results are finalized before their target event field lock.
4. **Place premier events** around major weeks and other anchors; avoid counterprogramming major weeks (hard ban), otherwise represent true opposite-field events explicitly if ever introduced.
5. **Place challenger, regional, mini-tour, college, amateur and local events** by location, typical season, venue availability and field opportunity. Lower tiers adapt rather than displacing higher-tier anchors.
6. **Run a global validation**: no duplicate course/layout bookings, no golfer overlaps, no tour conflicts, and no competition on major blackout weeks.

A tournament's **series prestige**, **tour prestige**, and **event entry priority** are distinct concepts; no single scalar should decide everything. Fixed-week priority must be an explicit calendar property, so a high-prestige one-off does not accidentally displace a centuries-old anchored competition.

### 1.3 Immediate pre-major examples (PROPOSED, not yet implemented)

| Week | Candidate anchored qualifier | Route |
|---:|---|---|
| 13 | Legends Masters Final Invitational Qualifier | Winner / eligible top finishers enter Week 14 |
| 18 | Premier Professional Qualification Championship | Eligible professional finishers enter Week 19 |
| 23 | American Open Final Qualifying | Eligible finishers enter Week 24 |
| 29 | Brittania Open Final Qualifying | Eligible finishers enter Week 30 |

These are candidate series names and rules, not automatically the only route to a major. Prior-year amateur winners, college individual champions, historic major champions, rankings, national opens and regional open-qualification routes remain important. Qualification from **an event must be based on an actual result**, and the route is recorded in the entrant's permanent tournament history. The final qualifier must not itself be booked on the major week.

National opens can be tied to fixed weeks if historic/feeder importance warrants it; others rotate dates/venues according to tour and region. Winning a designated national open could feed a future Brittania Open even if it is hosted on a low-tier circuit. Host-tour tier does not erase the event's historic prestige.

## 2 — Weekly AI schedule and entry resolver

The human controls broad monthly settings (workload, priorities, training, selected must-play events). Each AI golfer runs an autonomous **weekly evaluation**, with an 8–12-week lookahead and provisional season-level target list. The human golfer also has a planner that can automatically handle routine decisions under persistent rules.

### 2.1 Candidate utility (not a flat prestige sort)

Evaluate each event only if eligible or realistically able to qualify, and consider:
- championship and series prestige, expected ranking impact, sponsorship exposure;
- purse and expected payout **net** of entry, staff, travel and lodging;
- realistic competitiveness, course fit, rest and recovery, current fatigue/injury;
- timing relative to major events and targeted **warm-up value**;
- standing tour membership, card obligations and minimum starts;
- personal goals, home-country importance, historical ties and risk preference;
- likelihood that an event is actually available through priority categories/waitlist.

Risk-adjusted expected value matters. A lower-tier national open can be worth attending for a home-country icon; a premier golfer may skip a routine event while preparing for a major. Top golfers should trend toward fewer total starts **because their opportunity costs are higher**, not due to a hard rule such as `if prestige>85 play<=17`.

### 2.2 Schedule states and entry timing

Suggested workflow:
- `targeted` — on wish list; no entry guaranteed;
- `requested` — filed entry / waiting on priority or eligibility;
- `confirmed` — field allocator has awarded a place, still subject to cutoff rules;
- `locked` — accepted field after deadline; changes only under explicit withdrawal/replacement policy;
- `withdrawn` — withdrew with a reason and possible refund/penalty;
- `completed` — scoring/historical record closed.

Before scoring a week, resolve entrants globally, highest-priority overlapping commitments first. A golfer occupies no more than one competition that week. Once fields lock, attendance cannot be silently changed retroactively. A qualification result committed on Sunday of Week 13 can create a Week 14 major entry before its lock cutoff. Pre-reserve qualifying spots so a late earned exemption does not inexplicably overflow the field. A displaced conditional entrant receives an explicit recorded status, not a vanished start.

### 2.3 Unexpected high-priority invitation flow

1. End the relevant event and **commit** its results, winner, qualifiers, purse, and course records.
2. Produce an earned exemption with `source_event_id`, `earned_at`, `target_event_id`, status requirements and expiry.
3. Re-evaluate the qualifying golfer's upcoming schedule immediately (not only at month-end).
4. For a major invitation, recommend acceptance; for the human golfer, offer user choice unless their standing automation preferences delegate it. An eligible AI normally accepts unless medically or logistically impossible.
5. Cancel conflicting registrations or incompatible travel/training, calculate refunds and costs, release any reserved lower-priority spot to the proper waitlist.
6. Lock the major field at its deadline and audit that every start has exactly one legitimate entry path.

For example, a golfer wins a Week 13 feeder and earns the Week 14 Legends Masters. Week 14 has no conflicting tournament by design; however, the golfer's planned Week 14 rest/travel and Week 15 event may be revised. Other last-minute non-major invitations may displace a conflicting registered tournament **before its field locks**.

### 2.4 Warm-up planning

Add a persistent target-event and readiness planner. A golfer may schedule one or more warm-up starts before an important championship, depending on:
- their form/match sharpness after inactivity;
- fatigue and recovery (competing too much becomes counterproductive);
- similarity of warm-up course demands and weather to the target major;
- proximity to the major and travel burden;
- confidence and availability of training-only preparation.

A warm-up provides **readiness and course-specific preparation**, not a permanent attribute bonus or an automatic major victory boost. The optimal warm-up schedule must vary by stamina, age, goals and existing form. Simulate and test elite starts per season, pre-major starts, recovery and win probabilities; ensure no universal optimal routine emerges.

## 3 — Dynamic golfer prestige, sponsorship and staff access (future feature)

### 3.1 Keep four concepts distinct

1. **Playing ability**: developed skills, effective form and injury state, used to simulate shots/holes.
2. **World ranking**: results-derived measure of recent competitive performance.
3. **Personal prestige**: recognized reputation, historical legacy and current public relevance, likely 0–100 internal scale initially.
4. **Hype/momentum**: volatile shorter-term publicity expectation, distinct from lasting prestige (could be a component rather than a second fully visible attribute).

Examples: a long-retired 15-major champion retains high **legacy prestige** but has no current competitive ranking; an 18-year-old college sensation can have high **hype** and still be unproven professionally. A consistent tour player may have excellent ranking with modest public prestige. Avoid prestige automatically adding strokes to results; allow only plausible indirect effects (sponsorship/expectations/pressure).

### 3.2 Prestige movement

Major wins have a large durable effect. Important national titles, records, historically notable streaks and repeated elite finishes add prestige. Long droughts, poor results and elapsed time affect **current marketability** faster than legacy esteem. Rare landmark achievements generate lasting prominence; minor publicity slowly decays. National celebrities may enjoy stronger home-country prestige than international recognition.

Possible layered state: `career_legacy`, `current_reputation`, `hype`, `home_market_appeal`. A single player-facing prestige number can summarize these without discarding the factors internally. Calibrate via test worlds rather than inventing fixed +15 or -4 event awards.

### 3.3 Consequences

Prestige unlocks sponsorship interest, appearance fees and opportunities for better coaches/caddies, while actual **cash and fit** still determine whether the partnership can occur. Coaches and caddies have their own career stage, ambition, professional prestige, salary expectations, preferences and current contracts. The player's prestigious name can attract top staff who might decline a wealthy unknown prospect; conversely, money can fund excellent staff even before fame. Neither prestige nor staffing should override hidden talent ceilings. Funding support should help underrepresented countries and late-blooming professionals when credible opportunities arise.

Historical records must store prestige snapshots and contract dates, not just the latest prestige number.

## 4 — UI: World encyclopedia / historical browser (future feature)

**Primary top-level navigation (five categories):**

- **Golfers** — searchable current/retired/amateur lists; profiles; attributes and discovered potential; tour/country/age; career timeline; every season, tournament entry, victory, scorecard, staff partnership; records, rivals and national heroes.
- **Caddies** — active/retired caddies; skills, archetype, relationships, courses known; total starts/wins/majors **while caddying**; partnership timelines; career honors and caddie records.
- **Coaches** — specialties, evaluation skill, clients, progression and retirement; coaching partnerships; associated wins and titles; reputations and records. “Coached a champion” is a factual association, **not proof of causation**.
- **Courses** — geography, layouts/renovations, each hole's identity, historical round records, amateur/pro records by layout, record progression by date, hosted tournaments, notable moments and course specialists.
- **Tours** — member lists, prestige history, season tables, promotions/relegations, qualification routes, calendars, tour records, money and championship archives.

**Supporting discoverable categories:** **Tournaments/Majors**, **Countries/Nations**, **Calendar**, **World Records**, **Your Careers**, **History Timeline**. These can have top-level shortcuts while preserving the requested five main directories.

Every entity has a stable ID and hyperlink to relevant entities: course -> championship edition -> scores -> golfer -> staff -> their other wins; country -> national open -> emerging local players -> later generations. Add full-text search, date-range filters, current/retired filters, historic record-holder filtering, and bookmarked stories. Responsive query targets should be separately benchmarked with 100–200 years of retained results.

## 5 — Data architecture and performance safeguards

**Do not discard historical detail to make it faster.** Optimize repeated computation and access patterns instead.

Active golfer/staff states, upcoming calendar, entries and latest rankings live in RAM. Authoritative completed facts live in indexed SQLite with batched commits. Distinguish static event series from annual editions, and record schedule dates/week numbers and amendments with reason. Historical scorecards store all competitive hole scores and tee pairings compactly; preserve dated course-record changes, earned exemptions, player prestige milestones and staff contracts. Use explicit versions for course layouts.

**Scheduling performance:** Preindex courses by region/type, calendar week availability, event anchor priority, and golfer membership. Weekly candidate shortlist is preferable to every golfer evaluating every event worldwide every week. Cache eligibility and target-event readiness, invalidating on results, injury, entry deadline, tour-card changes or new qualification. Event-scoring workers operate on isolated competition data after a deterministic week-level entry resolution, and results are committed in causal order.

**Integrity invariants**:
- exactly one global sanctioned event on each locked major week;
- zero field entrants who also start another event in that week;
- no qualification earned after its target field lock;
- winner-based qualification explicitly links source and destination editions;
- entry/waitlist/displacement history preserved;
- no impossible overlap of travel, field membership or duplicate course use;
- world record summaries reconcile to underlying hole scores and dated event records;
- yearly simulated scorecard completeness and financial ledger reconciliation unchanged by calendar revisions.

**Performance acceptance:** Full season target ~120 seconds on the target PC at realistic golfer/venue/calendar scale. Measure at history depths 1, 10, 30, 60, 100, 200 years, with fixed workload to identify historical database slowdown. Continue 60-year independently seeded tests for career arc realism. This addendum has not benchmarked or changed the engine.

## 6 — Proposed acceptance tests before gameplay integration

| Test | Expected behavior |
|---|---|
| All 52 weeks | No reserved-major-week conflict worldwide; Week 1 allows regional/mini but no premier |
| Anchor weeks | Historic series repeat preferred weeks each year; qualifiers always precede destination major |
| Last-minute major berth | A Week 13 event winner receives a Week 14 berth with recorded qualification path and no duplicate registration |
| Non-major schedule override | A newly invited player withdraws before field lock; next eligible waitlisted player is admitted |
| Staff and fatigue | Elite golfer's frequency of starts responds to prestige, money, form, recovery and meaningful warm-up options |
| 15-year legend | High legacy prestige persists after decline, but current sponsorship offers can fall |
| College prodigy | Hype can precede professional world ranking and help attract interest without boosting underlying shot skill |
| National icon | Home-country market appeal and national open incentive can coexist with lower-tier host-tour prestige |
| History | Long-lived series, qualified entries, staff partnerships, archived scorecards and dated course records query correctly 200 years later |
| Speed | Measured comparable workload across years 1 and 200 without material history-driven slowdown; no lost data |

## 7 — Prioritized implementation backlog

**Now / next engineering milestone**
1. Integrate priority-aware calendar builder + major blackout invariants into the live engine.
2. Implement weekly deterministic global entry allocator with waitlists, deadlines, confirmed/locked states and provenance.
3. Add weekly AI plans and event-invitation override rules while preserving monthly player management.
4. Verify full hole-by-hole events, season finances, national opens and records with focused tests.

**After scheduling is stable**
5. Add major lead-in anchored qualifiers and richer national/amateur pipelines; ensure real source-to-destination exemptions.
6. Add elite selective scheduling and warm-up/competitive-sharpness mechanics with counterfactual balance tests.
7. Add evolving golfer prestige, sponsorship and staff market access; separate hype from legacy.
8. Build five primary world-encyclopedia directories and cross-linked records/history.
9. Optimize compiled/parallel scoring core and SQLite persistence while preserving every result.
10. Run at least two full-population 60-year worlds, plus long-history performance probes; review career distributions and underfilled fields.

## 8 — Open tuning choices (not blockers)

- Which qualifying series besides the four immediate lead-in events deserves a permanent week anchor (national opens, college championships, top amateur titles)?
- How far in advance should major fields provisionally reserve qualifying slots, and what are final entry cutoffs?
- Which non-major commitments can be displaced after field confirmation, and what are penalties/refunds?
- How much prestige is national rather than global, and how quickly does current hype decay?
- How to value warm-up fit, competitive sharpness, and fatigue so that neither overplaying nor extreme selectivity becomes optimal?

**Note:** This is a design artifact and implementation plan only. It is not a tested v0.10 game engine and does not supersede the v0.9 calendar preview's test status or v0.7/v0.8 simulation results.
