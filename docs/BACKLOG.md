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
- Nationality, birthplace, residence and dated moves (`docs/RESIDENCE.md`)
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

## Residence and finance pass (owner review of 5ecc75a)

Same status words as above.

1. **Owner decisions** — implemented, tested (5517c66, b335070). An injured professional who needs money
   does light paid work while recovering. The starting world and new professionals get no backing deal
   when their savings already cover three seasons of losses; an unbacked professional who runs low can
   find backers (not within two winters of a deal ending). Integration-checked: in the first winter only
   8 / 18 deals ended as "no longer needed" (339 / 284 before), and no golfer ended a season beyond their
   own credit in the gate run.
2. **Tier-aware earnings and evidence recency** — implemented, tested (9cc466a). A season's prize money is
   kept by the level it was won at; lower-tour money is never Premier evidence. Evidence halves for each
   full season away from a level.
3. **Session retry and publication** — implemented, tested (dda1e68). A retried key is checked only after
   syncing under the lock, so an operation recovery rolled back runs once more and never reports false
   success. Ordinary commits no longer republish unchanged tables.
4. **Overlapping exemptions** — implemented, tested (f7dac4b): an unconditional route is never hidden by an
   amateur one.
5. **Birthplace and residence** — implemented, tested, integration-checked (cbfb090, 188db30, 4dbcf03; see
   `docs/RESIDENCE.md`). Fixed nationality; fixed birthplace; residence changed only by dated, recorded
   moves; free college bases (initial world, arrivals, transfers); travel costs, appeal and proximity from
   residence, eligibility and memberships from nationality (each use audited); career moves (smooth odds,
   own money only, `MIN_STAY`), staff moves, one geography per person across roles, archive and observer.
   Legacy saves keep unknown geography. Gate (two seasons, seeds 2027 / 3031): about 91% of foreign
   college graduates went home and 8% stayed. **Owner decision open:** a graduate's new membership
   follows nationality (their home mini tour or amateur series), which is why most go home; letting a
   graduate start on a tour near where they live would be a route rule, not a residence rule.
6. **Long-run harness** — implemented (5ea63f1): `tools/long_world.py --session` runs a world through the
   persistent session and the observer, timing every season skip; `tools/long_run_report.py` writes the
   long-run report.
7. **Reviews** — the stop-chasing grid (`reports/STOP_CHASING_REVIEW.md`, b81a5e9): monotone, no cliffs,
   improving players accept losing seasons; debt below zero adds no pressure beyond an empty account
   (owner decision, unchanged). Second-season mini-tour money shortfalls (gate, `reports/gate_residence/`):
   23% of full-time mini-tour seasons lose 4+ weeks to money. Mostly a losing first season with no
   backers' money (56–65%) and new professionals (43%); living outside the tour's countries 7–8%; injury
   2–4%. Residence is not the main cause.

### 50-season run (seed 2027, `reports/long_run_2027/`)

Engine 7334ffe (clean), full population, every shot, through the persistent session and the observer; every
check passed in all 50 seasons (cash, family money, backers' money, staff payments, staff invariants, population).
- **Population** levels off: about 13,000 active golfers from season 25 (6,955 at the start); 42,947 people by
  season 50. Golfers arriving in season two or later won 131 of 200 majors; 12 reached world No. 1 in the weekly
  ranking (originally reported as 8, by year-end ranking).
- **High-potential golfers who left before developing**: originally reported as 5; corrected (see the next
  section): 20 full-time episodes ended young and undeveloped without a return, 3 more ended in a comeback.
- **Money**: no season failed to reconcile; one golfer ended a season beyond their own credit in 3 of the 50 seasons. **Open:**
  about 40% of full-time professionals end each season in debt (median about $7,000, within credit), and 45% of
  full-time mini-tour seasons lose 4+ weeks to money. Causes: a losing previous season (59%), beginning in debt
  (50%), no backers' money (41%), new professionals (40%), living outside the tour's countries (13%). The mini
  tours' economics (entry fees against purses) deserve an owner review; nothing was tuned.
- **Residence**: moves are rare and explained. Over 50 seasons there were 920 graduates going home, 484 other
  returns home, 143 career moves abroad (50 of those golfers later went home, counted in date order; originally 59), 2,626 caddies following their player and
  272 coaches following their players. 150–190 wanted moves a season were not made for lack of money.
- **Performance — missed.** Season skips took 108 s in season 1, then 122 s in season 2, rising to 280 s by
  season 50. In a clean process season 51 took 268 s: simulation 172 s, save 21 s, the observer's overview 69 s.
  - The overview builds the in-memory records, peaking at 9 GB, which probably caused one container restart
    during this pass.
  - **Next:** answer records from the archive index (SQLite) instead of holding every start in memory, and keep
    the overview off them. Simulation time grows with the active population; the target needs faster weekly
    work or the intended hardware. Season 100 is unmeasured.
- **Untested on Windows**: hard links between generations (`os.link`, falling back to a copy), the lock file,
  `os.replace` over files another process has open, fsync behaviour and network drives. All save and recovery
  tests ran on Linux.

## Preservation, accuracy and speed pass (owner review of 1f68691; the run on engine 7334ffe)

Same status words as above. No long simulation was started; no population, tournament, shot or history was
removed.

1. **Durable export of the 50-season world** — done, verified. `golf-legacy-world-2027-50y.tar.gz` (615 MB,
   two parts, `EXPORT_README.md`; delivered as files): world, data, reports, the engine as a git bundle and a
   tarball, `SHA256SUMS`. Verified: the parts rejoin to the checksum; the extracted copy is byte-identical; the
   archive reads; the session reopens from the bundle. GitHub hosting was blocked (releases not permitted for
   this session type; `lfs.github.com` denied by the network policy). The engine id now also derives from the
   files when there is no git (627ed1c), so an exported source tree opens its world.
2. **Winter move funding** — implemented, tested (75c135f). A move is paid at once, in its own year, by the
   weekly settlement's own rule (cash, then backers' money, then family money); never next season's backing.
   Tests: no cash + $10,000 backers' money + $6,000 move (and a $20,000 deal), family-funded, cash-funded,
   cash-then-backers-then-family, unaffordable (blocked); each really moves. College moves stay free.
3. **Annual finances in the archive** — implemented, tested (4754eed). Careers rows carry the final ledger
   (after winter expenses) and `net_at_decision`, the evidence the career decision used; decision timing
   unchanged. Tests: cash-funded and support-funded moves, save/resume, interrupted season end. The 50-season
   run predates this: its reports flag the pre-winter net (not reconstructable exactly).
4. **Residence before the first record is unknown** — implemented, tested (f205bfa), live and archived:
   before, at and after arrival, college transfers, later moves, golfer to staff.
5. **Diagnostic reports** — implemented, tested (b9af53f, `tests/test_reports.py`); regenerated from the saved
   data, originals kept (`reports/long_run_2027/*_original.md`, changes listed in its README). Changed
   conclusions: high-potential golfers whose full-time golf ended young and undeveloped, by episode: 20 not
   back (was "5 left"), 3 comebacks; weekly No. 1 among later juniors 12 (was 8 by year-end, all cohorts
   lumped); moved abroad and later returned 50 (was 59); the seeded "late bloomer" replaced.
6. **History reading at scale** — implemented, tested (e8aef18). Index schema 2 (weekly No. 1, careers rows);
   recap, careers, weeks at No. 1, moments, course histories and professional winners (any site of a
   multi-site event) from the index; records built from a compact per-person store; the decoded-season
   cache is bounded (4). Old and new answers on the 50-season world identical (28 boards, 1,370 rows, 8 other
   answers). An older index is completed once, under the session's lock (about 90 s for 50 seasons).
7. **Simulation and save profiling** — implemented, tested (37d9edf): archive JSON through the C encoder,
   the cyclic collector kept off the loaded world, the planner's per-golfer invariants worked out once.
   Fingerprint: the simulated state after 8 weeks of 2078 is the same hash before and after.

**Season 51, clean process, copy of the final world** (Intel Xeon @ 2.10 GHz, 4 logical CPUs, 15 GB, Python
3.13, Linux; both measured the same day, `tools/benchmark_skip.py --from-world`):

| | Skip | Simulate | Save | Publish | Observer reload + overview | First Records page | Peak memory |
|---|---|---|---|---|---|---|---|
| Before (1f68691) | 335.8 s | 205.1 s | 25.2 s | 6.9 s | 98.6 s | 21.7 s | 11.0 GB |
| After (two runs) | 216.6–224.0 s | 189.7–190.0 s | 16.3–19.4 s | 6.0–8.0 s | 4.2–6.9 s | 26.4–28.5 s | 3.6 GB |

The first Records page now builds the records itself (before, the overview had already built them in 94 s).
Runs on this container vary by about 5%; an earlier sample of the old code gave 267.6 s (simulate 171.6 s).

**Remaining blockers to 120 s** (profiled): simulation is about 190 s. In the profile, playing the weeks (the
workers playing every shot on 3 processes, plus sending each site's field and course to them and receiving
every hole back) was 48% of the weekly work; profiling inflates the main process's own Python, so the real
share is probably larger. The rest is serial weekly work in the main process: monthly planning (13 blocks,
about 4 s each unprofiled), weekly entries, development, recording results and rankings. Next, in order:
cache each plan block's event values by what they depend on; send courses to workers once instead of with
every site; cut per-hole result transfer to what is archived; then measure on the intended hardware (more
cores shorten the workers' share only). Season 100 is unmeasured.

**Executed / inspected / untested.** Executed: the full suite (270 tests; one failure found — a finance test
that compared pre-winter pots with the post-winter ledger, fixed in cafea33 — then the affected modules
re-run), the focused regressions above, the fingerprint, the old-versus-new history comparison, the export
verification, both benchmarks and a two-season strict integration check. Inspected only: the Windows code
paths. **Untested on Windows**: hard links between generations (falls back to a copy), the lock file and
taking over a dead owner's lock (never on Windows), `os.replace` over files another process holds open, fsync
behaviour, network drives, and `benchmark_skip.py` memory figures (no `resource` module there).

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
