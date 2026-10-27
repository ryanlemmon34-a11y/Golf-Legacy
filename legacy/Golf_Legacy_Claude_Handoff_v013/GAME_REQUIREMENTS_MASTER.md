# GOLF LEGACY — MASTER GAME REQUIREMENTS

**Document revision:** Consolidated handoff for external code/design review, 2026-10-26  
**Latest verified implementation:** Experimental Python **v0.13**  
**Primary priority:** An extraordinarily rich, believable, persistent global golf universe that can simulate decades and centuries without erasing history or reducing tournament fidelity.  
**Status terminology:** **IMPLEMENTED** = demonstrable in v0.13; **PARTIAL** = model/records exist but important rules are missing or uncalibrated; **PLANNED** = approved product direction, not in current engine; **OPEN** = precise calibration/UX value remains to be decided.

> **Critical for the reviewing AI:** This file defines the complete intended product; it is NOT a representation of what all source files currently do. Read `IMPLEMENTATION_STATUS.md` and `source/engine_v013.py` before asserting a feature works. Distinguish agreed direction from finalized tunable numerical parameters. The provided simulation is a functioning headless prototype, not a finished playable game.

---

## R01. Product identity and goals [APPROVED]

- Working name: **Golf Legacy**. Primarily a personal, offline, single-player **text-based golf career and history simulator**.
- Influences: Basketball GM's data-rich, fast simulation and history browser; Football Manager's autonomous careers and regional development; Crusader Kings III's decades-long persistent history and emergent stories.
- Human controls one golfer's **career decisions**, not clubs or individual swings/putts. Tournament golf is **fully simulated**.
- After retirement, remain in the same world as a new amateur, or enter **spectator mode** and advance time without a controlled golfer.
- Every world is a complete alternate golf history: independently developing AI golfers, staff, countries, courses, institutions, and event series. **World does not center on human player**.
- Successful career is not required. A never-won-a-major journeyman, failed college prospect, or part-time regional competitor can be an interesting playthrough.
- The user values **historical realism and completeness above raw speed**. Optimize code, caching, storage, and parallel execution; do not discard competitive holes or fabricate coarse scores for fast-forward.
- One-time modest development/PC expense is acceptable; avoid recurring cloud/API expenses. No commercial launch or multi-user service is required. Target Windows initially.

## R02. Time model and management UX [APPROVED / PLANNED]

- A **52-week, year-numbered global calendar** controls world events, tournament entry deadlines, birthdays, progression, finances and qualification. Important series have stable IDs and often stable week numbers.
- **Human planning cadence is monthly** (~12 decision windows per year); standing training/workload/strategy choices persist until changed.
- AI golfers, and the human golfer's assistant/planner, **re-evaluate upcoming opportunities weekly** using an 8–12-week rolling horizon; no requirement that user click weekly.
- Monthly plan includes: technical training focus, workload/rest, selected eligible tournaments or schedule policy, conservative/balanced/aggressive play tendency; later coaching/caddie/finance decisions.
- Ordinary simulation advances time automatically. Pause for **mandatory decisions** (important injury treatments, eligibility deadlines, nondelegated contracts), optional notifications for major debuts, sponsor offers, etc.; routine scoring/history appears in monthly recaps without interruption.
- Fast forward by month, year, end of season, multiple years/decades/century in spectator mode; **same chronological scoring/qualification engine regardless of speed**.
- Results locked once simulated: save RNG state, world state, qualification provenance, and tournament outcomes across interruptions; no invisible rerolls when resuming.
- December review/annual offseason: staff contracts, next-year focus, schedule, tour-status/qualification, finances and voluntary retirement.
- Dynamic monthly coach feedback and world news must come from actual underlying results, not fabricated explanations.

## R03. Golfer creation, archetypes and potential [APPROVED / PARTIAL]

- At career creation, select **archetype**: **Power Hitter**, **Precision Ball-Striker**, **Short-Game Artist**, **Strategic Technician**, **Aggressive Shotmaker**, **All-Rounder**; optional all-random prospect for replayability.
- Archetype changes **probabilities** of generated attribute ceilings/personality, not predetermined outcomes or free scoring bonuses. Extraordinary combinations across archetypes remain possible.
- Each technical, mental and relevant physical skill has **current developed rating** and a **hidden numerical maximum ceiling**. Train toward ceiling with strong diminishing returns. Example: golfer with hidden Putting maximum 73 can practice indefinitely but gains eventually shrink to fractional points and cannot become a 95 putter via routine training.
- Visible **potential grade** categorizes range, while **exact ceiling stays permanently hidden**. User originally suggested A ≈ 90–100 and C ≈ 70–79. Previous sketches proposed A+/A subdivision. **OPEN:** final grade boundaries; preserve user intent that A covers elite 90–100 and C roughly 70–79, with a possible rare A+ subgrade only if approved.
- **First 1–2 amateur seasons:** potential grades are hidden. Player receives qualitative scouting feedback, then more precise grades after competitive and training observations, generally at transition toward professional status. Scouting reveals estimates of pre-existing ceilings; winning amateur events does NOT generate higher hidden potential.
- Hidden `early_readiness`, `development_rate`, `peak_age` profiles must be separate from ceiling. A once-in-a-generation 18–21-year-old can already possess elite **actual** skills and high mental ratings; no forced several-year waiting period for an extraordinary prospect.
- Upper-tail talent generation is extremely rare. Do not guarantee a Tiger/Jack-like player in each 30-year world, but allow zero, one, or overlapping legends. Rare ability does not guarantee winning 10+ majors.
- Normalize rarity to prospect volume: expanding population creates more potential outliers in absolute number, not arbitrarily increased per-golfer probability. Tune worldwide birth/entry odds using population and multiworld tests.

## R04. Golfer abilities and condition [APPROVED / PARTIAL]

### 15 rated attributes (proposed final design)

| Group | Rated skill | Intended meaning |
|---|---|---|
| Technical | Driving Power | Tee distance, reachable holes and scoring opportunities |
| Technical | Driving Accuracy | Missed fairways, penalty avoidance, course fit on narrow courses |
| Technical | Long Iron Play | Difficult long approaches and long par 3s / par 5s |
| Technical | Approach Accuracy | Hit greens and finish close to pin from approach range |
| Technical | Short Game | Standard chipping, pitching and greenside skills |
| Technical | Trouble Recovery | Bunkers, deep rough and awkward escape shots |
| Technical | Putting Ability | Average putting quality |
| Technical | Putting Consistency | Putting variability independent of average |
| Technical | Ball-Striking Consistency | Tee-to-green variability, not putting variability |
| Mental | Composure | Maintaining execution with a small lead, chasing closely, 72nd-hole putts, cut-line tension |
| Mental | Mental Resilience | Recovering after bad holes, poor events, prolonged slumps |
| Mental | Course Management | Selecting sensible risk/reward strategy and adapting to hole demands |
| Physical | Stamina | Sustainable training, travel, successive tournaments and round fatigue |
| Physical | Recovery Rate | Speed fatigue dissipates between events |
| Physical | Injury Resistance | Susceptibility to initial/recurring injuries; largely innate, not readily trainable |

**Personality:** Hidden or partly discoverable `Big-Stage Temperament` (largely innate, but experience/mental coaching modestly improves expression), risk/aggressiveness tendency, coachability, adaptability, ambition. Big-Stage Temperament is distinct from Composure and Mental Resilience. Personality should shape likelihoods and decisions, not become a large extra score multiplier stacked on top of skill.

**Dynamic states:** Current technical form, confidence, fatigue, injury, motivation, swing stability/technical faults; relationship-specific caddie synergy and coach synergy; golfer-course familiarity. These are NOT additional natural potential ceilings and can move quickly.

**Performance hierarchy:** Hidden ceiling → developed ability → situational effective ability after form/health/course/weather/staff/pressure → probabilistic hole result. Coaches/staff/mental factors cannot generate technical ability out of thin air.

## R05. Age, career variation, injuries and rare exceptional golfers [APPROVED / PARTIAL]

- Physical growth generally rapid around **18–22**, slower through 20s, individual physical peak around **30–35** (not one universal birthday); gradual earlier decline for some, later for others.
- Technical ability can peak or remain strong after physical power starts dropping; skilled putting and iron play remain valuable late in life.
- Mental abilities generally accumulate more slowly from ~18–40, may start extremely high in a prodigy, plateau, then decline more gradually than physical skills.
- Different hidden peak ages and development multipliers for each golfer/skill; setbacks and training affect outcomes.
- Injuries, repeated fatigue, technical swing changes, equipment adaptation, poor confidence and burnout can cause temporary or long-term declines; causes are generated **before** news/report explanations. Avoid random unexplained 15-point losses without internal causal mechanics.
- Developed technical skill and **effective temporary performance** are separate; a slump can drastically impair performance without resetting permanent potential. Recoveries and partial second peaks possible.
- Pressure depends on **real-time event prestige/spotlight** and **real-time position**: Friday golfer near the projected cut, and Sunday golfer within reach of the lead need different calculations from golfers safely distant. Near-cut golfers can recover or collapse based on composure and resilience.
- Baseline technical ability should matter far more than mental ratings overall; elite composure/major affinity may reduce pressure penalties but must not make mediocre skills reliably defeat world-class players.
- AI careers must emerge from mechanisms, never from fixed assigned scripts like “future 15-major legend” or “collapses at 29”. Most careers should be ordinary; rare long dominance, overlapping champions, early explosions, injury collapses, and late career breakthroughs should occur stochastically.

## R06. Golfer career paths and population [APPROVED / PLANNED]

- Broad active populations: Premier professionals; Challenger/Regional professionals; mini-tour and part-time pros; competitive college/amateur golfers; local/occasional competitors. Lifetime archive retains retired people and career changes.
- First human career normally begins ~18 as an amateur. Alternative later professional start is future option, not core.
- **US college pathway** (program prestige, Division I/II/III-like levels, tournaments, scholarships, competing for lineup, conference/national individual championships), plus national amateur, international university, junior/academy, regional amateurs, club/county and foreign-college routes worldwide. Nationality influences home pathways and cost, not permanent eligibility elsewhere.
- Local amateur events may be 18, 36, 54 or 72 holes with separate prestige, rankings and records; even obscure club events have permanent champions.
- Amateur/pro status is legally meaningful: a professional who quits cannot arbitrarily start winning amateur-only events without modeled reinstatement eligibility.
- Turning professional does **not** hand the golfer a top-tour membership. Qualification school, local pro events, regional pathways, developmental tours and invited starts must be earned.
- Golfers may stay amateurs, try qualifying, go part-time, teach or work outside golf, pause/reenter, or retire. No fixed failure age: decisions depend on finances, opportunities, ambition, progress, physical health and other career prospects.
- Crucial late bloomer possibility: a player gives up full-time professional golf, works/competes locally for years, then earns a national-open/qualifier berth, grows into a tour player and perhaps wins a major near 38. This must be uncommon but mechanically feasible, not scripted.
- New amateur after each retirement joins **current world year**; all previous careers, event histories and nation changes remain.
- Midscale target: **~6,000 active golfers / ~40 circuits / 500–600 competitive events/year**, with approximate distribution previously proposed: 500 Premier, 900 Challenger, 1,400 Regional, 1,200 mini/part-time, 2,000 college/amateurs (flexible, not fixed slots). Long term **15k–25k active**, 60–100 circuits, 1,000–2,000 events/year, 200+ year worlds; not performance-validated.
- Field capacities and tour membership matter; many golfers should never qualify for a Premier start. Populate lower tiers with **more eligible entrants than available field places** so cancellations are uncommon, but never fabricate identities or override eligibility to fill fields.

## R07. Global nations and development [APPROVED / PARTIAL]

- Every nationality/region has dynamic golf infrastructure, junior participation/aspiration, available coaches/facilities, investment, access cost and talent pipeline quality.
- Powerful golf nations generally generate more prospects and stronger average support, but any country can produce a rare all-time great (e.g. Kenya). National icon's success can inspire attendance, funding, youth development and a new generation decades later.
- Feedback must have multi-year lags, saturation controls, mean reversion and occasional setbacks. Early 60-year tests saturated too many countries at the infrastructure maximum: **known calibration issue**.
- Track national amateur champs, national opens, country firsts, sponsor exposure, national heroes, first major winners and country ranking history. These should be queryable centuries later.
- National identity can include birthplace, multiple associations/heritage, affiliation and home market (more nuanced than one country code). This also matters for stars returning to home-country opens.
- Goal is emergent national transformation, not predetermined story events or “Kenya guaranteed first major by 2050.”

## R08. Tours, levels and membership [APPROVED / PARTIAL]

- **Tier 0 = four global major championships** (event category, not a tour membership). **Tier 1 = Premier Tours** (36 regular events across geographic circuits). Below: Challenger/Developmental, Regional, Mini and amateur/college circuits; tier prestige ratings distinct from event prestige, field strength and world ranking.
- Permanent international interconnected routes, not one linear promotion ladder. Golfers can move region, enter qualifying schools, retain more than one membership when calendar/fees allow, accept or decline earned advancement, move down strategically and return through qualifying.
- Planned tour-card statuses: Full, Conditional, Limited Exemption, Nonmember Qualifying/Invitation, Ineligible. Current `tier` participation is NOT a proven tour card; **full statuses and retention remain planned**.
- Elite access from tour standings, Q-school, major and tournament winner exemptions, previous champion exemptions, world ranks, college/national amateur titles, sponsor invitations, national-open qualifying routes.
- Premier victory should offer a meaningful membership exemption (proposed two seasons) and reputation gain. Major eligibility may follow from *specific* criteria, not generic all-major entry.
- Earned promotion gives **option** to move up, not automatic forced acceptance. Lost card/conditional status governed by tour rules and existing exemptions. No unlimited card hoarding.
- Promotion development trade-off: matching stronger fields can improve skills/resources while poor performances, cash pressure and fatigue may make moving up premature. Lower tiers offer confidence and sustainable competition; success doesn't automatically award technical points.

## R09. The calendar: global 52-week priority cascade [APPROVED / IMPLEMENTED in part]

- Global event planning priority: (1) four major blackout weeks; (2) fixed annual historic major feeders, prestigious national opens and qualifying series; (3) flagship/standard/opportunity Premier events; (4) Challenger and Regional; (5) Mini; (6) college/amateur/local. Then **global weekly golfer registration/field allocator**. Fixed anchors have stable `(series_id, week)`; ordinary event weeks and courses can move when needed.
- **Absolutely no competitive tournaments anywhere in the world in major weeks:** Week **14** Legends of Golf Masters Event, Week **19** Premier Tour Championship, Week **24** American Open, Week **30** Brittania Open.
- **Masters course fixed across years**; other three majors rotate venues. Calendar year 1 can have multiple regional/mini events and no Premier, and full 52-week schedule can have several simultaneous lower-tier events.
- Annual Tier 0 + Tier 1 target **40**: 4 majors and 36 Premier events (8 flagship, 20 standard, 8 opportunity). Prestige/purses vary by category and field strength; four opportunity events intentionally in **Weeks 15, 20, 25, 31**, immediately after majors, with elite golfers normally resting but not prohibited from entering.
- Important feeder weeks: Week 13 Legends Masters Final Qualifier → W14; W18 professional/club-pro championship → W19; W23 American Open final qualifier → W24; W29 Brittania Open final qualifier → W30. Important national opens hosted Scotland W21, Kenya W22, Japan W25, Australia W27, each offering specified route into W30 (pilot fixtures; broader worldwide national open ecosystem remains planned).
- **Series identity permanent:** `series_id` survives changes of venue and edition year; `event_id` distinct for each annual edition. Format, historical prestige and purse typically stable by series, except explicit dated policy change. Course configurations may change with renovated layout and require versioned records.
- Major access only through actual results, prior exemptions, published qualification rules and eligibility; no auto-filling majors with arbitrary high-stat golfers.

## R10. Tournament formats, scheduling details and simulation [APPROVED / IMPLEMENTED]

- **Every actual competitive hole** is simulated chronologically (not one score drawn per 18/36/54/72 holes), with live scoring state. Even fast-forward must simulate events at full fidelity.
- **18-hole** local/mini events: one competitive round, usually no cut. **36-hole** regional/qualifiers: two rounds, generally no cut. **54-hole:** three rounds, optional 36-hole cut. **72-hole:** four rounds with typical 36-hole cut unless designated no-cut. Cuts include ties, and event policy controls thresholds.
- Pairings and tee times must be plausible. Thu/Fri four-round events typically three-player groups, opposite AM/PM waves and tee starts; after cut pair by running scores with leaders teeing off last, generally pairs. One-day/two-day formats adapt grouping and no-cut rules appropriately.
- Scores must incorporate golfer skill, course/hole demands, weather, pressure and individual round/hole variability. Key pressures include projected Friday cut and live Sunday contention, not final hindsight.
- Equal scores at first resolved by configured playoffs, with their own holes and consistent recorded champion. Ties for other positions handled correctly in points and prize distribution.
- **Event format usually correlates positively with prestige, prize money and advancement within comparable tour levels**; long prestigious events can grant major entry and better tour eligibility. Formal short qualifying events (e.g. 36-hole American Open final qualifier) are intentional exceptions.
- Tour-prestige ranking separate from tournament series prestige and *actual current* field strength. Fixed course may have history beyond that year's event quality. Major 72-hole prize/premier category configured in v0.13; purse sizes are game balance assumptions.
- All scorecards, rankings, cuts, pairings, hole-level results, payouts and course record milestones persist.

## R11. Weekly AI planning, entry priority and selectivity [APPROVED / PLANNED]

- Weekly rolling 8–12-week plan for every AI golfer, using event eligibility, prestige, expected earnings **minus** travel/entry/staff costs, course fit, stamina, recovery, tour-card needs, opportunity to improve ranking, calendar travel, country loyalty, personal ambition, competitive sharpness and other goals.
- Entry states: `targeted → requested → confirmed → locked → completed` or `withdrawn`, with dated status and reasons. Hard lock deadlines; waitlists and priority categories. No silent displacement or retroactive entry.
- On qualification/major invitation (e.g. win Week 13, enter Week 14), immediately replan: higher opportunity supersedes lower event/travel/rest; free spot passed to eligible waitlisted golfer before lock. Human can be prompted unless standing automation policy delegates acceptance.
- World #1 often plays fewer starts than world #150 **because** prizes, prestige, preparation, fatigue and opportunity cost differ; **no artificial top-rank start cap**. Week-after-major opportunity events have weaker fields naturally, not because top players are hard-banned.
- Competitive sharpness/rust accumulates from time away and is replenished through limited warm-up starts; excessive starts increase fatigue, which is modulated by stamina and recovery rate. Warm-up value should depend on major prep and course similarity; no universally optimal schedule.
- AI schedule must support home-country national open loyalty even when tour tier is weaker, if calendar/health/budget permit.

## R12. Rankings, major qualification and tour-card advancement [APPROVED / PARTIAL]

Four separate systems: **world professional ranking** (recent results), **tour-season standings** (membership/order of merit), **amateur/college rankings** (distinct competitive pool), **personal prestige/hype** (marketability). Do not conflate them.

- World ranking **inspired by OWGR**, not guaranteed exact current OWGR reproduction: rolling **104 weeks**; first **13 weeks at full weight**, remaining 91 weeks decay; average of adjusted points with minimum divisor **40**, maximum **52** starts; major allocations and 54-hole allocations handled separately. 18/36 local events generally no ordinary world points.
- Field strength should ultimately derive from actual recent **adjusted scoring performance**, not pre-event static technical ratings. v0.13 currently uses a **provisional ability proxy**, which must be replaced/validated before claiming fidelity.
- Rank and standing tie procedures, field rating snapshots and weekly rankings must be reconstructible from archived event results. No double counting, no extra world points because of event purse alone.
- Major-specific exemption tables (stable for each championship edition and season), separate from tour card, with explicit field limits/priority and duplicate exemption spillover:
  - **Legends Masters W14:** past champions, elite world ranking, invited nationally/internationally significant amateur winners, previous high finishers, specific W13 qualifier. Traditionally smaller field.
  - **Premier Championship W19:** leading professionals and invited top club/teaching professionals via W18 professional championship.
  - **American Open W24:** open regional/final qualifying, selected American and international amateurs/college individual champions, rank exemptions and past champions.
  - **Brittania Open W30:** international and national-open winners, Tour standings, selected global amateurs and qualifying paths, W29 final qualifiers. National open pathways from multiple countries are central to this identity.
- Every major entrant has a recorded dated *entry source*. Winning low-tier events can open qualification pathways, not magically grant elite cards without rule-specific source.
- Win an opportunity Premier event and possibly secure a two-year Premier membership, ranking points, sponsorship prestige and majors as expressly defined; the two-year membership policy remains proposed/partly represented by provisional exemption, not yet a complete tour card framework.

## R13. Golfer prestige, hype and financing [APPROVED / PLANNED/PARTIAL]

- Playing skill, world ranking, **personal prestige**, and **hype** are different values. High past major success may sustain legacy prestige long after ranking falls. National-icon reputation can be very strong at home. Teenage amateur prodigy can have high hype but no world professional ranking.
- Prestige climbs meaningfully after majors, landmark records, national opens, significant success; marketability/hype decay faster during slumps; legacy prestige decays much more slowly.
- Prestige affects **sponsorship offers, appearance fees, demand for coaches/caddies** and brand marketability. No direct magical score bonus.
- Finances: tournament earnings, sponsorship where eligible, work income for part-timers, expenses for travel, fees, coaches, caddies, fitness, equipment/rehab, housing/overhead. Tour level influences winnings and operating expenses; moving up can temporarily reduce net earnings.
- No artificial subsidy to pay for unearned starts. Entry must be funded; expense and purse ledgers balance exactly. Amateurs and qualifying fixtures have distinct prize eligibility rules; amateur-only cash earnings should not silently imitate professional purses.
- Personal spending policies: conservative, balanced, development-investment. Status and opportunity allow retention/relegation and a viable way to recover from hardship, but not guaranteed income.
- v0.13 inherits substantial earlier cash/economics machinery, but full contracts, prestige-powered sponsorship and weekly finances/exit rules still need integration and long-run validation.

## R14. Caddies and coaches as full historical characters [APPROVED / PARTIAL]

- Every caddie/coach has stable identity, nationality, age, career chronology, staff archetype, skill ratings with individual hidden ceilings, personality, staff prestige, compensation expectation and contract relationships.
- **Caddie skills:** Course Strategy, Green Reading, Yardage & Preparation, Course Knowledge, Mental Support, Communication; plus risk tolerance. Suggested types Strategist, Green Reader, Motivator, Veteran Course Expert, All-Rounder.
- **Coach skills:** Driving Instruction, Approach Instruction, Short-Game Instruction, Putting Instruction, Mental Development, Technical Diagnosis, Talent Evaluation, Communication; suggested Technical Specialist, Putting Guru, Mental Coach, Developmental Coach, Swing Rebuilder.
- Talent Evaluation distinct from Teaching skill. A coach may discover a player's C ceiling accurately but teach poorly, or teach excellently but forecast potential imprecisely.
- Four dimensions of partnership: natural communication/personality compatibility, evolving trust, shared experience and course knowledge, actual professional fit to golfer needs. Complementary risk styles may help; identical personalities are not guaranteed best synergy.
- Moderate scoring/development influence: good caddie should help selected situations, good coach should modestly speed development toward **existing potential**, not make random mediocre golfer into a major favorite. Provisional caddie benchmark ~0.1–0.3 strokes/round, extraordinary under ~0.5; coaching development efficiency examples ~5–15%, rare specific specialty ~20% (gameplay balance proposals **not real-world measured facts**).
- Stacking must be bounded: Composure + major temperament + mental coach + caddie mental skill cannot independently add four large scoring boosts.
- Staff can change employer, improve, age, struggle and retire; retain histories of all engagements and **wins/majors associated while employed**, not causal credit claims. Former golfers can potentially become coaches/caddies later (long-term vision).
- v0.13 generates some named staff and tracks linked major wins; comprehensive autonomous staff hiring markets, potential growth, contracts, career histories and detailed partnership effects are **not fully implemented**.

## R15. Courses, course variants and permanent records [APPROVED / PARTIAL]

- Large worldwide course library, hundreds initially and thousands later. Diverse geography: links, parkland, desert, mountain, tropical, etc. Weather and seasons matter.
- Course includes **18 individually parameterized holes**, par, length, fairway width, hazards, green speed/contours, bunker/rough severity, wind exposure, elevation and condition.
- Golfer-course and caddie-course familiarity grows through appearances/practice, but the advantage is bounded and less transferable after major renovations.
- Individual tournament series has course policy **fixed** (Legends Masters) or **rotating** (other majors, most national opens, many regular tour events). Course database prevents double bookings.
- Permanent records: lowest competitive rounds, 18/36/54/72 tournament totals by configuration, records at individual holes, repeat winners, lowest amateur/pro scores, dated record progression, every hosted event and notable moments.
- **Versioned layouts** for real redesigns/length/par changes; do not compare incomparable configurations as if identical. Dates, tee category and holes played stored with records.
- Records remain accessible centuries later, including local amateur courses. v0.13 stores dated course/hole changes and full scored rounds, but versioned layouts and many derived browsing views are future work.

## R16. World archive and eventual UI [APPROVED / PLANNED]

The interface should be a richly linked golf encyclopedia first, graphics optional. **Five main directories**: **Golfers**, **Caddies**, **Coaches**, **Courses**, **Tours**. Additional views: **Countries**, **Tournament series and annual editions**, **52-week calendar**, **World records**, **Your careers**, **Global historical timeline**, rankings, major qualification routes, monthly dashboard.

- Search, filter by country/era/rank/tier/status, compare careers, see every major champion and runner-up, oldest/youngest national/major champions, tournament records and development by country.
- Every permanent ID links across identities: golfer → college/national amateur event → qualifying route → major scorecard → host course/hole records → caddie/coach → other clients/tours → country history.
- Player can inspect live 30–60-second animated leaderboard replay from actual hole events, but ordinary managerial gameplay never asks user to pick clubs or shots.
- Monthly dashboard emphasizes form, training, schedule, health, rank, money, staff feedback; annual review and retirement legacy recap; spectator fast-forward controls.
- History timelines and automatically generated headlines must be based on recorded results and authentic causal events; no fictional text attributing outcomes to a coach or injury without data provenance.
- Personal history tracks each human-controlled golfer in save without replacing or deleting old characters.

## R17. Data fidelity, runtime and architecture [APPROVED / PARTIAL]

- **Non-negotiable** all scored tournament holes simulated under one chronological model, even during 100-year fast-forward. Pairings, live scores, cut pressure, Sunday contention, playoffs and eligibility cannot be thrown away for speed.
- Local-first; no required server/subscription. Current engine: **Python standard library** + SQLite. Possible eventual high-performance release: **Rust simulation core**, **Tauri desktop shell**, **React/TypeScript web-style UI**, **SQLite** historical archive. These technology choices are recommendations and benchmarking-dependent, NOT committed code.
- Active world/near-term schedules in RAM; historical immutable results persisted efficiently to indexed SQLite. Maintain compact 18-hole scoring encoding while storing real pairing/tee and dated record changes; archived records must never be garbage-collected simply for speed.
- Optimize by caching fixed skill/course computations, batching SQL within safe transactions and potentially multithreading independent simultaneous tournaments **after deterministic global entry allocation**; parallel execution must retain event causality, proper rankings/exemption handoff and reproducibility.
- v0.13 one 1,700-golfer, 358-event full-calendar test took ~29 sec **with no persistent archive writes**; does NOT prove full archival speed or a 6,000-player target. Prior 4,500-golfer/341-event v0.8 test ~123 sec for one year; not directly comparable after engine changes.
- Target: approximately **120 seconds or less per full-size season** on chosen PC **including durable storage**. More important than an absolute guarantee: year 200 should not slow drastically from history growth alone; test normalized runtime, memory, writes and query latency at years 1/5/10/30/60/100/200.
- Save atomicity/crash recovery: **weekly or monthly SQLite WAL/checkpoints**, record RNG states and committed historical editions. Year-end-only commits unacceptable for player-facing saves. v0.13 durable SQLite currently needs this enhancement and longer benchmark.
- File/DB portability and full offline operation; snapshot version/schema migration will be needed in long-lived saves.

## R18. Realism validation principles [APPROVED]

- Use repeated **independently seeded 60-year worlds** (not just 30 years) to assess emergence, era transitions, national evolution, rare prodigies and fully completed career arcs. Also test 100–200-year archive persistence. Use multiple seeds, baseline comparisons and age/cohort censoring.
- Do not fit to quotas like “exactly one 15-major golfer per world.” Compare statistical distributions and tail events to historical golf appropriately controlling for era, worldwide volume and field strength.
- Track: winner ages, first/win-after-35, multi-major dominance, runner-up finishes, weekly #1 rankings and turnover, top-100 major qualifying, elite selected starts, lower-ranked post-major opportunity winners, retired/reinstated careers, tour mobility, financial sustainability, country breakthrough and role models.
- Record national open hometown returns and victories, late major debut paths, course and hole records by layout, timeline of staff partnerships and associated major victories.
- Integrity checks before realism interpretation: round score = sum of recorded 18 holes; cuts (ties) and pairings correct; no double-booking/week conflicts; prizes conserved; tournament format correct; exemption source chronological; no duplicate ranks/points; durable database reopens with same history.
- **Preserve previous simulation distributions as frozen baselines** but do not claim current v0.13 has validated them with the integrated new calendar. Historic v0.7 two 60-year tests had 16/14-major leaders under reduced 450-golfer/quarter-calendar conditions, so they prove possibilities, not final global rarity.

## R19. Known unresolved decisions / risks

- Exact A/A+ potential-grade thresholds; precise archetype probability weights and upper-tail talent frequency.
- Realistic model of international university/amateur structure and amateur-status transition/reinstatement.
- Proper Adjusted Strokes Gained / field strength and real OWGR-style ranking model rather than ability proxy; empirically calibrate 54-hole points and top/bottom fields.
- Whether all national opens have fixed weeks or selected historically anchored ones; country affiliations and national-open prestige outside host-tour tier.
- Full field priority, standby lists, refunds and last-minute entry lock timing; historic qualification-specific quotas and exemptions.
- Exact purse economy and player prestige/hype changes. Current amounts are fictional tuning values.
- Staff supply/compensation/synergy/growth without overpowering talent.
- Country investment model avoiding many nations saturating at a ceiling and allowing both emergence and regression.
- Data footprint, schema migrations, crash-safe save progress and archival growth at 200 years.
- UI design and text/news generation beyond static report templates.
- End-to-end performance at 6,000+ golfers / 500–600 annual events **with complete scorecards saved**.

## R20. Implementation requirement for any future contributor

1. Preserve the latest runnable source and run tests before modifying anything.
2. Propose changes with clear files/functions, verification plan, expected risks, and impact on old seed runs.
3. Never equate planned features in this spec with present implementation.
4. Keep user-focused gameplay/realism decisions authoritative over speculative complexity; ask only for genuinely blocking design choices.
5. Do not claim statistical realism from one 60-year world or one extreme result.
6. Preserve complete tournament and golfer histories and their source provenance.
7. Produce runnable code, audits, and updated README for every engine release.
