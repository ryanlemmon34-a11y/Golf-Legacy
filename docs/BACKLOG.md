# Golf Legacy — Backlog

Owner requirements and planned work, in rough order. "Built" items link to where they live.

## Built

- Shot-by-shot engine, 21 attributes, archetypes, calibration (`docs/ENGINE_DESIGN.md`)
- World calendar with the four fixed majors and real-life qualifying (`docs/CALENDAR_AND_QUALIFYING.md`)
- 520-course library with layouts and per-layout records (`docs/COURSE_LIBRARY.md`)
- Nations and the world population (`docs/WORLD_POPULATION.md`)
- Season system v1 with event and player prestige (`docs/SEASON_SYSTEM.md`)
- Development, monthly planning, money and careers v1 (`docs/DEVELOPMENT_AND_CAREERS.md`)
- Coaches and caddies as people, with dated relationships (`docs/COACHES_AND_CADDIES.md`)
- Persistent identities, the history archive and resumable saves (`docs/HISTORY_AND_PERSISTENCE.md`)

## Prestige (owner, recorded for the backlog; first version built in the season system)

- **Every event has a prestige level** from: the quality of the course, the tour playing it, the quality
  of last year's field, and the prize money. *Built:* `golfsim/prestige.py`, updated after every edition.
- **Every tournament stays on the same week every year**, so the "opportunity" events that most great
  pros skip are the same events every season and build their own identity. *Built:* calendar weeks are
  fixed per series (tested); only rotating host cities change.
- **Prestige drives AI decisions on where to play.** *Built (v1):* golfers score each event by prestige,
  home country, travel, fatigue and their season plan; stars set a higher bar, so they skip opportunity
  events. Later: plan whole schedules around majors and favourite courses, play-in-form, defending
  titles, appearance fees, team events.
- **Winning higher-prestige events raises a player's prestige.** *Built (v1):* fame from every finish,
  scaled by event prestige; lasting legacy from majors and flagship wins.
- **Sponsors are driven by player prestige.** *Built (v1):* yearly sponsor income from prestige
  (paid weekly). Player money and expenses (travel, caddie, coach) and money as a constraint on
  schedules are built. Deferred: complex sponsorship contracts (brands, bonuses, lengths) and agents.
- **Coaches:** hiring depends on what a golfer can afford and what coaches see in them. *Built.*

## Owner principles

- **The world evolves over time, with ups and downs over centuries.** No artificial ceilings or floors
  on talent: a weak era (best player 83) and a golden one (two players at 95) are both fine.
- Event prestige moves slowly (rolling 3–5 years); player prestige over about a year.
- Stamina matters across a season: tiredness affects mostly physical attributes and raises injury risk,
  especially with low injury resistance or older age.

## Careers, money and the people of golf (owner)

- **Finances shape careers, but are not the only reason.** A 22-year-old earning a few thousand a
  year keeps chasing the dream; by 26-27, still only making $10-20k, it often stops making sense —
  unless they are improving, have earned a better card or secured a big event, in which case many
  accept another losing season. They take a job but, still good enough, play a few events near home.
  *Built: funds (savings, backing, limited credit) gate what they can enter; the decision to continue
  weighs money pressure against a separate desire to continue (progress, the card earned, secured
  events, health, willingness, a smooth life-stage curve) — no age or debt cliffs
  (`docs/DEVELOPMENT_AND_CAREERS.md`).*
- **Rare comebacks:** a part-timer whose mental game has matured naturally may make another run at
  34 — qualify for a big event or win a tour card. Very rare, but possible and part of the history.
- **Every individual has a history** — players, caddies and coaches: careers, results, moves, injuries,
  money, milestones. *Built as data: stable person ids, dated stints, event-time teams, per-season
  archive files and query functions (`docs/HISTORY_AND_PERSISTENCE.md`). Profile screens: a later UI
  milestone.*
- **Caddies and coaches as people:** *Built, see `docs/COACHES_AND_CADDIES.md`.* Former players with the
  right minds (rarely anyone wealthy) become caddies or coaches as the same person; staff have skills,
  careers, reputations, client relationships (dated, two-sided, with working familiarity) and histories.
- **Monthly planning (owner):** each month a golfer juggles training a category of attributes, a full
  rest week, and tournaments — a risk/reward balance of fatigue and injury against development and
  career. Playing tournaments develops raw golfers (far from their potential) the most.
  *First version built.*

## Known limitations from the realism audit

- Career odds are hand-set logistic weights, checked for shape (smooth, monotone, counterfactual) but
  not fitted to real career data; the long-world test (`tools/long_world.py`) shows what they produce. The
earlier cohort report predated the debt-trap fix and coaches/caddies and was removed.
- The world is a selected sample of competitive golfers; its rates are not population-wide rates.
- No pre-history: the first season's rankings and standings are seeded from reputation, and the first
  Tour Masters uses inaugural invitations (route `INIT`).
- Finance is simple: one credit rule, one work wage, family money and backers' money as two pots; no
  regional costs of living or contract lengths; staff have no household finances. Debt from living
  costs can pass the credit limit (an injured touring professional: see "Debt" in `golfsim/finance.py`).
- Relationship continuity, capacity and departure odds are first-version tuning assumptions (e.g. ~6
  individual clients per coach), to be checked against long-run evidence.

## Done in the P0 pass (roadmap V1: competition access, development mix, amateur livelihood)

- **Competition access:** college and open amateur lineups rotate by starts (ranking worth a head
  start), open amateur fields can expand ×1.5, the International University tour's field matches its
  membership; every week's wanted / placed / shut out is recorded and reported by level, separately
  from injury, money, no eligible event and choice (`tools/long_world.py`, section 3b).
- **Development needs competition:** pressure skills and tournament consistency train only with recent
  competitive rounds; the mental game matures with rounds played (`docs/DEVELOPMENT_AND_CAREERS.md`,
  `reports/DEVELOPMENT_AUDIT.md` section 4).
- **Amateur livelihood:** adult non-college amateurs take jobs (a recorded, smooth transition), and every
  invitation, qualified place and championship uses the same affordability rule as regular entries
  (declines recorded, the next in line replaces them; school-paid events recorded with the school as
  payer). No loans or credit system.
- Still open: thin local amateur calendars (e.g. part-time amateurs in parts of Europe have no event
  near home for months — a calendar gap, reported as "no event they were eligible for" or choice, not
  as full fields).

## Done in the access pass (P0 continued)

- Every golfer-week classified (played, alternative, blocked by full fields / no event / eligibility /
  money, or chosen), audited by status, circuit, region and career stage (`tools/access_audit.py`,
  `reports/access/`).
- Major weeks closed to Premier events only; Premier playing rights (exempt / full / graduate /
  conditional) with Challenger alternatives and bounded visitor places; Challenger, Regional and mini
  calendars sized to their members; local amateur and club-professional golf in every golfing country;
  college golfers play amateur events around college; every circuit has a flagship with recorded routes
  (`docs/COMPETITION_ACCESS.md`, `docs/CIRCUIT_FLAGSHIPS.md`). The course library grew to 520.
- Still open: calendars follow the starting nation pools (they should follow nation evolution, M5); the
  monthly plan does not learn from being shut out; the 10% Premier visitor share and full-status size are
  owner decisions to confirm.

## Correctness and realism pass (owner review of commit 0a98843)

Status words: **implemented** (in the code), **tested** (regression tests that failed before the fix
pass after it, plus the full suite), **integration-checked** (short multi-seed runs), **unverified**
(not yet measured at the scale or duration that would prove it).

1. **Arrival experience** — implemented, tested, integration-checked (4c0ff7a). Assumed pre-entry
   experience is `Season.prior_rounds`, a previous season that fades through the first; `season_rounds`
   holds only rounds played; year-end maturing follows them. Old saves migrate on loading. Unverified: the
   effect on arrivals' development over decades (needs a long run).
2. **Saves and history in one transaction** — implemented, tested, integration-checked (892d148).
   Rollback on every failed commit; season-end history staged in the checkpoint and published after the
   commit (repaired on opening); recent operation keys checked against the committed world; recovery only
   under the lock; dead-process locks taken over on POSIX. Unverified: behaviour on Windows file systems
   (renames over open files) and on network drives; a real power cut (simulated by failing writes).
3. **Championship field selection** — implemented, tested (0f3f62f). Exact USA Amateur places with a
   fair remainder draw; one amateur-series rule for ordinary events, flagships and USA Amateur residency;
   mini championships open to everyone recorded as playing. Integration-checked (3 seasons, 2 seeds).
4. **Records and backing** — implemented, tested (c1f8a9a). Debuts only for careers that began in the
   archive; independence judged without the support being withdrawn; backers' money kept apart and
   returned when a deal ends. Integration-checked.
5. **Bounded career decisions** — implemented, tested (e04f50f). No backer age cliff or universal
   two-season rule; part-timers and club pros stop for their own reasons (drift vs being shut out).
   The weights are **uncalibrated assumptions** (labelled). Integration-checked: active golfers now grow
   ~450-500 a season early on (they are not tuned out); whether that settles needs a long run.
6. **Performance without deleting golf or history** — implemented, tested (this pass). Weekly work over
   active golfers only (identical results), observer reads only new history. Measured (container, see
   `docs/ENGINE_DESIGN.md`): Skip to end of Season 109-118 s in season 1, 126 s in season 2, 118 s with
   50,000 synthetic retired people. **Unverified:** season 100 (needs a long run) and the intended
   hardware (`tools/benchmark_skip.py`). Season time grows with the active population.

## Finance and recovery pass (owner review of ad504fe)

Same status words as above.

1. **Forecasts match earnings** — implemented, tested (79d8c7c). Prize evidence is kept by level of
   competition, with an event count. Other levels are translated and counted for less, and a new card is
   not an income. Independence needs cash for the start of the season plus proven earnings, a sponsor
   contract or three seasons of savings. Amateurs forecast no prize or sponsorship. One set of income
   and cost definitions serves forecasts, the caddie budget, affordability and payments.
   Integration-checked: "backers no longer needed" fell from 525 / 517 to 406 / 337 over two seasons
   (seeds 2027 / 3031); withdrawals are about the same.
2. **Secured places from the qualification rules** — implemented, tested (76ba17d). Every exemption
   route applies to a no-hindsight view: earned invitations such as a USA Open top ten, and continuing
   exemptions while they last. Ranking cut-offs still to come never count, and an amateur's place keeps
   its condition. The places feed career and backer decisions and appear in the history.
3. **One budget per week** — implemented, tested (68522dc). Accepted entries reserve their cost; a
   qualifier is priced at the assigned site; the caddie fee is paid once a week. The school or club is
   labelled as payer. Family and backers' money are kept apart, with backer flows recorded, and every pot
   reconciles each season (`tools/long_world.py`). Integration-checked: no reconcile errors in either
   seed; season-1 weeks with no affordable event rose about 17% (2,075 / 1,910 against 1,771 / 1,614),
   because a golfer can no longer spend the same money twice.
4. **Debt rule** — documented, tested (34fb8ca); no change to behaviour. Credit limits chosen spending;
   living costs continue, so a long injury can pass the limit. The debt is kept, blocks spending and
   weighs smoothly on the season-end decision. In the two-season check only one golfer per run (or
   none) ended beyond their own credit, each after a long injury. **Owner decision open:** whether an
   injured professional may do light paid work, or change their life mid-season.
5. **Recovery** — implemented, tested (1b0c814). Each generation carries its own history: a damaged
   season-end checkpoint falls back with the right people, relationships and records. A retried
   committed operation repairs unfinished publication. Observer records rebuild when a season they read
   is removed or republished. Unverified: Windows hard links on network drives (it falls back to copying).
6. **Performance** — measured, unchanged by this pass (`tools/benchmark_skip.py --seasons 2`, the
   development container: Intel Xeon @ 2.10 GHz, 4 logical CPUs, Python 3.13): skip to end of season
   110.9 s in season 1 and 120.5 s in season 2, including saving, publishing and the observer. No
   golfers, events, shots or history were removed. **Unverified:** season 100 and the intended hardware.
   Season time still grows with the active population (6,956 → 7,469).
7. **Still open:** the starting world gives backing deals regardless of savings, so the first winter
   ends many deals ("savings now cover N seasons": 214 / 183 in season 1, 34 / 32 in season 2). This is
   a seeding artifact for the owner to decide on. Weeks with no affordable event roughly double in season
   2 (already true before this pass), mostly mini-tour professionals in their second losing season. A
   long run will show whether careers resolve that or it builds up.

## V1 observer UI (owner baseline, `docs/UI_REQUIREMENTS_V1.md`)

The V1 interface is an interactive golf encyclopedia over a world the player only advances: linked
profiles (golfers with one identity across playing, coaching and caddying careers; reciprocal staff
stints; courses, nations, tours, tournaments and their editions), central and contextual records from one
set of definitions, a Frivolities section of real unusual patterns, season recaps from recorded facts,
and eventually as-of-year views. Not built. Before it, close the archive gaps listed in that document:

1. ~~Record each edition's tour, tier and category at the time~~ — done (archive events carry them).
2. ~~Archive the weekly No. 1 and ranking snapshots~~ — done: each week's top 100 of the world and
   amateur rankings (`Archive.ranking`, `Archive.weeks_at_number_one`).
3. ~~A records/definitions module over the archive~~ — first version: `golfsim/history_stats.py`
   (definitions; boards for wins, majors, starts, prize, ages, debuts, starts before a first win,
   not-won-yet vs retired-without-a-win, waits between wins, runner-ups, major droughts, wins across
   tours, streaks, weeks at No. 1, partnerships, coaches of major champions; evidence and active/partial
   flags on every row). Still to choose: the owner's first lists and their filters (era, nation).
4. ~~Archive indexes~~ — done: a SQLite index beside the season files (`golfsim/archive_index.py`),
   updated idempotently with each archived season and trimmed with session recovery.
5. ~~Special moments as linked facts~~ — done: holes-in-one, albatrosses, playoffs (with who lost them) and
   course records set after a fair sample (300 earlier rounds on the layout) are archived each season with
   golfer, edition, week and layout (`Archive.moments`, indexed; boards for most holes-in-one, playoff
   wins, course records).
6. A throwaway observer prototype to try the browsing journeys before the framework decision:
   `tools/observer.py` (standard library web server; Overview with Advance week / 4 weeks / to end of
   season through the session, golfer profiles with career, team history, results with entry routes and
   moments, tournament histories and edition leaderboards with coach and caddie, course pages, records and
   frivolities with evidence, moments, search). Not the chosen framework.
7. First usable slice: Overview, Golfer profile, Tournament edition, Course profile and one Records or
   Frivolities list, tested as complete browsing journeys (see the document).

Open owner decisions: framework and desktop packaging, visual design, the first record definitions and
frivolities lists, when to deliver as-of views and a university directory, performance budgets and
accessibility checks.

## Next (in order)

1. **Historical identity and persistence** — *done in this pass*: person ids, stints, event-time teams,
   the archive, saves (`docs/HISTORY_AND_PERSISTENCE.md`). Next: archive the narrative of special
   moments (aces, playoffs) as linked facts too, and query performance over centuries.
2. **Staff relationships** — *first version done*: capacity, two-sided departures, continuity. Next:
   tune against long-run evidence (coaching coverage by level, relationship lengths).
3. **Integration validation** — staged gates (unit suite, short full-population run with archive and
   linked-history demonstration) before every long run.
4. **The next full-world test** — several seeds for decades, with the archive and resumable saves, so
   its history can be explored afterwards.
5. **Navigable profiles and richer season recaps** (owner; a later UI milestone): click through golfers,
   their coaches and caddies, the other players those staff worked with, tournaments, courses and
   records — built on the archive's queries, not on narrative text.
6. **Nation development** (owner; a future simulation milestone): participation, infrastructure and
   pathways improve or weaken over time and affect *later generations*, with delays and diminishing
   returns. National success must not instantly boost current golfers or guarantee the next champion.
   The archive already keeps what it needs (each person's country, birth year and arrival; each
   season's results), so the model can be added without losing history.
7. **History generation**: decades simulated before the game starts, so there are past champions and
   records from day one.
8. **More courses** (hundreds to thousands; owner) and hand-designed elite courses with named holes.

Deferred on purpose: complex sponsorship contracts, agents, and extensive junior management (an under-18
competition system, academies, high-school golf). Junior support is a simple baseline for now.

## Known gaps in the season system v1

- Fields: no Monday qualifiers for regular tour events, no team college golf (players enter as
  individuals), no sponsor invitations beyond a few amateurs.
- The US Open final qualifying draws fewer entrants than real life (about 160 instead of ~900).
- World ranking uses a simplified OWGR formula; amateur ranking a simplified WAGR.
- Weather: wind and rain per round, no per-wave tee times or seasonal weather patterns.
