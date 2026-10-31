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

## Current delivery order (owner roadmap, 29 October 2026: UI first)

This order supersedes the earlier milestone order and the pre-UI long-test gates. Simulation and history
requirements are unchanged; no new long run, spending or calibration change is authorised.

1. **Observer alpha now** -- *delivered in this pass* (below; `docs/OBSERVER_ALPHA.md`).
2. **The owner's playtests** -- launch with `RUN_OBSERVER_WINDOWS.bat`, the acceptance checklist in
   `docs/OBSERVER_ALPHA.md`; each reported world is preserved and arrives as a diagnostic package; we review
   a copy read-only first, reproduce with the engine commit it names, and never change the original.
3. **Parallel evidence work** (not gates for the alpha): performance measurement on the owner's machine; the
   existing-world realism audit (population by level, careers, winner ages, course geography and difficulty;
   measurement before any tuning, owner review first).
4. **Expand the observer from playtest feedback**: linked directories, staff histories, courses, nations,
   tournaments, records and frivolities; navigation and long-history queries.
5. **Complete the universe and release proof**: nation development, remaining autonomous pathway details,
   broad long-run validation. Nation-versus-nation events later; nationality and residence history kept.

## Roadmap v14 build (branch build/v14; report `docs/V14_BUILD_REPORT.md`)

Delivered and merged into `main` (30 October 2026, owner's decision): playoff display and per-site playoff evidence; the
multi-cause "no starts" ledger and the full-time amateur investigation (`docs/ZERO_START_REVIEW.md`); the Majors +
Premier scope; Overall sorting on Stats and Recorded Peak Overall; the spoiler-safe workflow (Hide results, Watch
from round 1, Reveal final); the reference calendar v2 for new worlds with its qualification rework
(`docs/CALENDAR_V2.md`, `docs/CALENDAR_MANIFEST.md`); the measured performance work (`docs/PERFORMANCE_REVIEW.md`).

Open after it: projections of who is inside a cut-off still to come; a per-tour standings-lock table; the
per-region amateur affordability comparison before any access change; a day-ordered engine (only if same-week
feeders are ever wanted). Decision pending (owner): the parent/child tour filter; migrating an existing world to
v2 (a copy, at a season boundary); the performance options in the review (per-golfer random streams,
incremental checkpoints, outcome-equivalent engines). Blocked: the Test1 archive on Google Drive (the host is
not reachable from the build environment).

## Build v15 (branch build/v15; report `docs/V15_BUILD_REPORT.md`; HAL's review of 07cecee)

Delivered for review, in order: the four review fixes (Britannia qualifying-series places, Hide results in
recaps and the Grand Slam, playoff par, restart vs resume); saved table views and navigation state; Where are
they now; My World; career comparisons; the GOAT Lab; qualification evidence (earned / pending / projected
views, `docs/STANDINGS_AND_RIGHTS.md`, the zero-start investigation by region and circuit with
recommendations); exact-result browsing speedups.

Stabilization pass (HAL's review of 0d4576b; report section in `docs/V15_BUILD_REPORT.md`): the global Hide
results setting removed (every view reads the complete history; ordinary replay and "Watch from round 1" kept;
old settings files ignored; a My World period possibly marked read while hidden offered for review); GOAT formula
arity rules and safe evaluation; one Recorded Peak (the profile's) for the GOAT Lab and cohorts over the whole
career, archive-only included; cohort prize money with the current season, counted once; My World ranking bands
from each week's own ranking; Save view saves the view as shown after a browser sort.

**Next priorities (owner roadmap, after the stabilization pass)**: believable career and financial decisions;
evolving nations; richer staff relationship history (and My World digesting staff relationship changes).

**Owner decision (30 October 2026): remove the classic calendar (v1) in the next updates.** It must not be used
again: the reference calendar (v2) is the only calendar. To settle when the work is specified: what happens to
worlds saved on v1 (the paused playthrough, the 50-season test world) -- browse their history only, or migrate a
copy at a season boundary -- and retiring the v1 code paths, the v1/v2 comparison tools and the v1 equivalence
tests. The owner's playthrough "Test 1 10.30" (v2, 57 seasons, release V1.10.30.26, seed 360013, saved by engine
55a2527f) replaces the 50-season world as the reference world for checks.

Awaiting the owner's decision: the zero-start recommendations (`docs/ZERO_START_REVIEW.md`: the full-time /
working decision when a full-time amateur cannot afford their cheapest event; amateur cost or event density by
region); the performance options (per-golfer random streams, incremental checkpoints, outcome-equivalent engines,
an upgraded index for older archives); the parent/child tour filter; migrating an existing world to v2.
Deferred (not in this increment): nation development and other large simulation expansions; a day-ordered
same-week feeder engine; season-100 timing (no checkpoint exists).

## Expanded roadmap: status after the pass of 31 October 2026 (branch build/v16)

The owner's expanded roadmap (`Golf_Legacy_Expanded_World_Roadmap_2026-10-30`) is the full pre-playthrough scope.
Where it and the owner's prompt of 31 October differ, the prompt wins: **old-world compatibility and resuming
previous saves are no longer required** (fresh worlds only; unsupported saves are identified, never deleted).
Status is what was built and tested, not what was proposed. Report: `docs/V17_PASS_REPORT.md`.

| Roadmap item | Status | Where |
|---|---|---|
| F1 Support successful amateurs | Built as an initial calibration (bands A/B/C, in kind, coaching included); measured over three seasons; work pathway for cash-blocked adult amateurs built as an initial calibration (rules 2026-11-03), minimum age lowered from 21 to 18 in rules 2026-11-10 (older worlds keep 21; nothing else changed); ten-season comparison in the diagnostic runs | `golfsim/amateur_support.py`, `docs/AMATEUR_WORK_PATHWAY_PROPOSAL.md` |
| F2 Earned major trip guarantee | Built and tested for all four majors, every status, inaugural Masters invitees, alternates, expired amateur places, injury; representative reconstructed scenarios (not each of the 269 cases) | `tests/test_major_funding.py` |
| F3 Rule and observer defects | Built (U1 tenth anniversary, one status rule, one retirement event, comparisons, cohort level) | v16 |
| E1 Evidence | Built (money behind major places, injury episodes, creation and development by source, dated aging); scheduling target components with fatigue / injury / money context per monthly plan, and every retire / stop-chasing / turn-pro / job / comeback / amateur-return evaluation's terms and draw and the winter's mortality draws (format /2), recorded from v16-schedule-evidence (`decision_evidence`; gaps listed in `docs/DECISION_EVIDENCE.md`) | v16 |
| E2 Wide-screen ratings | Built (fixed-width annual bars, levels and changes, retirement year); physical/technical/mental group views not yet; coach and caddie ratings shown | v16, this pass |
| E3 Injuries | Built (episodes, announced = actual from rules 2026-11-02, first appearance incl. qualifying, lasting losses); My World injury and return items **not yet** | this pass |
| P1 Prestige for every individual | Built (golfers, coaches, caddies; sortable; each role its own value) | this pass |
| P2 Five-year event, course and nation prestige | Planned | -- |
| S1 Staff careers and partnerships | Mostly built (stints both sides, reasons, recorded fit and rapport, abilities); My World team news **not yet** | this pass |
| S2 Scouting recognises upside | Existing observation-only scouting kept; richer assessment planned (design in `docs/COACHES_AND_CADDIES.md`) | -- |
| S3 Two-way recruitment, motivations | Planned (design note) | -- |
| G1 Geography, familiarity, course use | Built, unit-tested (rules 2026-11-08): course state/province, regional familiarity baseline, home clubs, local hosting for unused municipal courses (owner decision), top 10 familiar courses on profiles with the value the engine uses; seeded comparison runs pending | `docs/FAMILIARITY_AND_AGGRESSION.md`, `docs/COURSE_LIBRARY.md` |
| G2 Visible Aggression | Built, unit-tested: shown on profiles, stable, reach/aggression interaction tested; no second risk score | `docs/FAMILIARITY_AND_AGGRESSION.md` |
| G3 Seasonal weather | Built on branch build/v16-weather (rules 2026-11-09): seasonal climate by city and week, wind direction per hole, skill mitigation, conditions on scorecards and summaries; temperature/firmness open for the owner; season-scale runs pending | `golfsim/weather.py` |
| Record Book; nation count links | Record Book built; nation counts linked to their exact population **not yet** | -- |
| B1/B2 Biggest Upsets | Built: pre-event estimate recorded per edition (`upset-model-1`, recording only), observer page with a majors-only view and filters; whole-season equivalence and cost measurement pending the CPU release | `golfsim/upsets.py`, `tools/observer_upsets.py` |
| T1-T3 Tournament stories, linked history | Built (branch build/v16-stories): Story tab on every edition (majors and prestigious events first, with the lead line on the result), golfer view, inspection view of the facts; how the winner played from the recorded golf statistics (putts, fairways, greens, scrambling, sand saves, strokes gained against the engine table; margin over the runner-up split by strokes gained; personal bests to that date, same format, linked); profile and My World entry points; upset context only from the edition's recorded `upset` estimate, also inside a playoff story; per-season story index (golf weeks, edition formats) and story cache in `observer_cache/stories.sqlite`, the rest of the history indexed in the background; no engine change. World-level test and timing on a long history **pending the CPU hold** | `tools/observer_stories.py` |
| C1 Calibration | Waiting for the long runs (`docs/LONG_RUN_PLAN.md`, for approval) | -- |
| C2 Death after retirement | Built per D6 (rules 2026-11-07): winter processing at (Y, 53), never an active competitive golfer, provisional curve; awaiting review and the small-world runs | `golfsim/mortality.py` |
| Qualification windows | Decided 31 October: the N most recent editions for P2, U5, B3 and M3, P3, U6, B4 (rules 2026-11-03); others unchanged; boundary tests | `docs/QUALIFICATION_WINDOWS.md` |
| Long histories | Index validated/rebuilt, side index for read-only histories, exports include it; benchmarked | this pass |
| Mobile and small screens | Deferred | -- |
| Hide Results | Stays removed | -- |
| Career mode | Planning after the world systems are ready | -- |

## Build v16 (branch build/v16; report `docs/V16_BUILD_REPORT.md`; the prompt worked out with HAL, 30 October 2026)

Delivered for review, one commit per package: the wide desktop layout (no 1,150 px cap; tables sized to their
columns, reading width for text), Compare careers and GOAT Lab in the menu, the Record Book, retired status
everywhere, one retirement event in My World, comparison top 10s without qualifying, cohort level counting the
current season; USA Open champions exempt through the tenth anniversary (simulation change); the money behind
every major place recorded; an earned major place never lost for money alone (organizer-paid trips in kind,
recorded once; simulation change); development evidence (creation records, each season's change by source,
aging dated; measured cost under 1 % time, about +4.6 % archive); ratings over time on profiles; injury episodes
recorded and shown; coach and caddie profiles and partnership stories. Rules version 2026-11-01.

Waiting for the owner (listed in the report): the amateur sponsorship settings
(`docs/AMATEUR_SPONSORSHIP_PROPOSAL.md`); v1 worlds browse-only (blocks advancing the paused v1 playthrough);
the proposed simulation runs (seeds, lengths, times, questions); whether a coach's teaching and scouting stay
hidden; "last N years" routes that include the current year (six editions once it is played); injuries keeping
a golfer out of one more week of entries than announced; how exported histories without an index become
browsable (an index beside a read-only copy, or exports that include it). Next once approved: sponsorship, the
runs and calibration from their evidence, retiring v1; then My World injury and return items, and staff "fit"
(needs a definition). Deferred: small screens, the death system; geography, course usage, prestige and deeper
staff careers later. Hide results stays removed.

## The pretest review increment (owner roadmap, pinned review of 5bcc6ed, 29 October 2026)

Delivered (`docs/PRETEST_REVIEW_RESPONSE.md`): golf statistics captured per edition with versioned definitions
and kept in the archive; world ranking points per start, weekly top-200 averages and the seeded points, with a
profile breakdown that reproduces the engine exactly; largest stroke-play margins and match-play wins; driving
records (longest drive, event / season / career averages with proposed thresholds); a Golf statistics tab in
Stats and on profiles; the five pretest fixes (replay spoilers, live record status, starts scope, restore order,
no-index ids). Next, in order (observer-only, worlds stay resumable): saved table views and navigation; Where
Are They Now; My World; career comparisons; the GOAT Lab; then the owner's choice of immersion views. Open for
review: the qualification thresholds; whether strokes gained gets a validated baseline.

## The 2090 audit increment (owner roadmap "Fix genuine access defects and make history explain itself", 30 October 2026)

The owner's 63-season world (seed 2027, 2027-2089) was reviewed read-only by the audit and is kept unchanged as
the evidence baseline; this increment was developed on copies and small test worlds. It changes simulation code
(the engine fingerprint changes: earlier worlds open read-only or continue through a copy). Details, evidence and
the owner decisions still needed: `docs/AUDIT_2090_RESPONSE.md`.
- **Winner's exemptions whatever the membership** (Jack H. Harris): accession to a Premier card by a winner's
  exemption or Premier money, exempt field priority for non-members, in-season exemptions, amateur major
  champions turning professional -- implemented, tested (`tests/test_entry_rights.py`).
- **Amateur golf where an amateur lives** (Jung, Johansson): residence opens a circuit's ordinary amateur events;
  graduates take the circuit where they live, movers their new home's; national championships stay nationality
  -- implemented, tested (`tests/test_amateur_residence.py`).
- **Name variety**: larger banks for arrivals; names unique among active people, retired names may recur;
  initials last -- implemented, tested, measured by replaying 35,784 arrivals (initials 46.6% -> 0.0%).
- **Facts kept**: per-start prize money, round scores, round conditions, majors' hole-by-hole cards, rules
  version, winner's exemption, card reason, decisions per golfer, college eligibility ledger; index schema 3
  -- implemented, tested (round scores reproduce totals and cuts; payouts reconcile with money paid).
- **Observer**: rules page and readable entry routes; status and its changes with recorded reasons; season as
  it was; missed cuts and career totals; separate coach and caddie histories; residence timeline; tournament
  and course summaries; edition prize money and Rounds & replay with major scorecards; records with when and
  now; Career Grand Slam; year-end recap; sortable tables; money formatting -- implemented, tested
  (`tests/test_observer_history.py`).
- **Proposed, not built** (owner review): college ruleset options, Premier circuit choice, elite venues for
  curated amateur championships and venue assignment by event standing (the Kohler / USA Amateur cause), Hall
  of Fame criteria, prestige vs reputation and peaks, live round-by-round play.

## Observer playtest increment (owner roadmap "Next observer UI increment", 29 October 2026)

The owner runs the 100-year world himself, on its own folder and engine; this increment was developed on
copies (a fresh world and the 50-season world) and changes no simulation code: the engine fingerprint is
unchanged (e5c4c37e...), so worlds made by the previous version open and continue as "this engine".
- **Advance seasons** and **Stop simulation** (owner request) -- implemented, tested (see below).
- **Profiles**: ratings and archetype with signed changes (this season / last season against recorded
  snapshots, "unavailable" without one; potential hidden); age before birth year and in every season row
  (approximate, labelled); career honors by event-time classification; season-by-season with per-tour rows,
  each figure linked to its results; coaches' current clients as rows; staff season by season; moments with
  their course and layout -- implemented, tested.
- **Statistics**: Stats and Prize money pages (season or all-time, all tours or one, sortable, linked);
  per-tour prize money recomputed from each event's payouts and reconciled with the money paid (588,797 of
  588,797 golfer-seasons on the 50-season world; 627 of 627 on a new one); built in a separate process in the
  background (about 80 s for 50 seasons, once; then one season at a time) -- implemented, tested, measured.
- **Shortlists** per world for every entity type; **world removal** to a trash with restore and deliberate
  permanent deletion; **starting year** separate from a random or explicit seed -- implemented, tested.
- New archive facts (archive.py only): season-start ratings, event-time purse/cut/field/kind, staff earnings
  totals; worlds archived before them show "unavailable" for rating changes and use the calendar's purses
  (checked by reconciliation).
- Measured on the 50-season copy (this container): person pages 0.08-0.22 s, all-time Stats 2-2.5 s, one
  season's Stats 0.2-0.3 s; pages stay fast while the statistics are built.
- Open: rollups for courses, tours, nations and tournament series beyond their current pages; as-of views;
  the comparative realism audit waits for the owner's multi-seed gameplay saves.

## Observer alpha pass (owner roadmap of 29 October 2026; review pin 832c55a)

Status words: **implemented**, **tested** (automated tests, full suite), **measured** (timed on copies of
saves in this container), **unverified** (not run where it matters, e.g. Windows).

**R1 -- a generation number reused after a rollback** -- reproduced, fixed, tested (7cf6d20). Reproduced
exactly as reviewed: generation 1 ends 2027, generation 2 publishes 2028-29 and is damaged, recovery returns
to generation 1, a one-season replay commits generation 2 again; the abandoned `world.g000002.json` (years
2027-29) stayed on disk and was kept by `_place`, so the new manifest (2027-28) named it and the reader refused
the archive ("manifest and world table disagree"); an observer holding the abandoned world also saw the same
number and kept it. Now a generation number is never reused (above every number the world has used); a test
does a rollback then a shorter replay (fails before, passes after).

**Observer alpha** -- implemented and tested unless marked:
- *Background advances* (week, 4 weeks, to season end): one job at a time; progress bar and `/api/status`;
  forms carry the world, the date drawn at and a one-time key (double clicks, refreshes, retries,
  reconnects and old forms never advance twice); **Stop after this week** keeps every completed week; a
  failure shows its error, keeps the last committed week and goes to the world's `observer.log`; an advance
  cut short by the observer stopping (window closed, crash) is reported on the next open, nothing
  half-written. Tested, including a process killed mid-advance.
- *Pages from one committed generation*: a snapshot of the committed world (`tools/observer_live.py`) with
  the history published with it; pages never read the world being advanced (tested: identical pages during
  an advance). SQLite reads stay on one renderer thread.
- *World library*: create (name, seed), open, browse read-only, copy (original unchanged, tested by
  checksums), close, quit; date, seed, engine and save-format compatibility. Worlds saved by another engine
  are never resumed in place: browse, or copy with "continue with this engine" (recorded in the copy's
  `ENGINE_ACCEPTED.json`); measured on a copy of the 50-season world (7334ffe). A lock left by a dead
  process is taken over (POSIX tested; Windows check implemented, **unverified**); a manual release with
  confirmation as a fallback.
- *Connected history*: directories with filters for golfers, coaches, caddies, courses, nations, tours,
  tournaments, the current calendar; person pages with Playing / Results / Coaches & caddies / Coaching /
  Caddying tabs; editions separate from tournaments, layouts from courses; current-season editions use the
  archive's own edition record (tested: an edition, a golfer's results and the leaderboard read the same
  before and after the season is archived, no double counting); records "Start here" lists (youngest and
  oldest major champions and Premier debutants, most starts without a win, any tour) with partial/active
  flags and the age precision stated.
- *Diagnostic package*: the committed save, every history file it depends on, log (local folder names
  removed), versions, seed, date, generations, file hashes, an issue note; index and previous checkpoint
  optional; tested to reopen as the same world. Never uploaded.
- *Windows launcher*: `RUN_OBSERVER_WINDOWS.bat` -- **unverified on Windows**.
- *Local only*: 127.0.0.1; posts from other web sites and foreign Host headers refused.
- *Worker processes*: started fresh ('spawn', as on Windows) and exiting when the observer is gone. Found in
  the demonstration: forked workers outlived a killed observer and held its port. Measured identical world
  (every part) with the engine's pool and the observer's over six full-population weeks.
- *Demonstration* (full population, in a browser; `reports/OBSERVER_ALPHA_DEMO.md`): create 4.9 s; a
  double-clicked week advanced once; four weeks 6 s with browsing during; observer killed mid-season and
  reopened at its last saved week; the remaining 47 weeks 94.4 s (95.1 s click to overview); quit, resume,
  copy, export.

**Measured** (this container: 4 CPUs, Python 3.13, Linux; copies of saves; see `docs/OBSERVER_ALPHA.md`):
the 50-season world (49,378 people): first open of an older-engine copy 102.9 s (one-time migration and index
upgrade), later opens 16 s; pages 0.06-0.26 s (golfers directory 1.2 s first time; Records' first list
13.8 s while the statistics are built, then 2-3 s; Seasons 36 s before it was moved to the index, 0.0 s
after); the per-page check of the committed checkpoint hashes 80 MB in 71-81 ms (not optimised: acceptable
now, and recovery depends on it); browsing during an advance 0.19 s; the first page after an advance 0.64 s;
main process peak RSS 3.06 GB; a diagnostic package 282 MB required + 973 MB optional index (811 MB zipped
with the index). A one-week advance from 1 January took 33 s (the year start runs with that week, then the
save).

**The owner's first Windows playtest** (29 October 2026; diagnostic report "First Observer Try", seed 2027,
Windows 11, Python 3.15): the first season end could not be published -- `OSError: [Errno 9] Bad file
descriptor` from `os.fsync` on a file opened only for reading (copying the previous manifest), which Windows
refuses and Linux allows; every later page retried the publication and failed the same way. The season itself
was committed (the world at 2028, week 1, with 2027 staged in its checkpoint): nothing was lost, but the
observer's message wrongly said "nothing of this advance was kept". Fixed: copies are flushed through the
handle that wrote them (also the hard-link fallback for drives without hard links); replacing the manifest or
CURRENT retries briefly while Windows has the old file open; collection skips files still open; the observer
says an advance was saved when only publication failed, and pages keep working (last published history,
labelled) until publication succeeds. Tested by emulating Windows' fsync rule, missing hard links and a file
still open (the test fails before the fix with the owner's exact error). Opening the world with the fixed code
publishes 2027. Evidence from the same log: weeks 11-28 took 16 s and weeks 35-52 with the season end about
19 s on the owner's computer -- much faster than this container (not a benchmark).

**The target machine** (owner, 29 October 2026): ASUS ROG Zephyrus G14 (GA403UV), AMD Ryzen 9 8945HS (8
cores, 16 logical CPUs), 16 GB RAM (15.3 GB usable; 3.0 GB available when the owner looked), Windows 11
(10.0.26100), Python 3.15. The 120 s season target is measured on it. By default the engine starts one worker
per logical CPU (16 here); whether 8 is as fast, and how much memory 16 Windows workers take beside a
long world in 16 GB, is what `RUN_BENCHMARK_WINDOWS.bat` measures (season 1 with 16 and 8 workers; drag a
world folder onto it for that world). The benchmark now also measures memory on Windows (working set and
private memory per process) and writes `benchmark_result.txt`.

**Measured on the target machine** (owner's run, 29 October 2026, `RUN_BENCHMARK_WINDOWS.bat`; plugged in;
season 1 of a new full world, seed 2027, 6,449 active golfers; preparation excluded: create about 3 s):

| Workers | Click to overview | Simulate | Save | Publish | Settle | Reload + overview | First Records | Memory (main peak working set / all processes private) |
|---|---|---|---|---|---|---|---|---|
| 16 | **47.9 s** | 44.6 s | 1.5 s | 1.0 s | 0.2 s | 0.5 s | 0.2 s | 459 MB / 817 MB (each worker 24 MB private) |
| 8 | **49.9 s** | 46.6 s | 1.5 s | 1.0 s | 0.3 s | 0.5 s | 0.2 s | 458 MB / 625 MB |

Season 1 meets the 120 s target on the target machine with room to spare (about 2.5 times faster than this
container: 100-109 s). 8 workers are almost as fast as 16: in season 1 the main process's serial work, not
the shot simulation in the workers, sets the time. Windows memory measurement verified by this run. **Still
unmeasured on it: a mature world** (the 50-season world: drag `world_2027` onto the launcher) **and season
100** (no such save exists; making one is a long run, an owner decision).

**Advance seasons** (owner request, 29 October 2026): a number of seasons from the header; the rest of the
current season, then whole seasons, each one segment committed and published as its season ends (a long
run never holds more than one season in memory or at risk); the pages' snapshot moves on between seasons;
**Stop simulation** stops after the current week; every segment names the cursor it must start from, so the
same form resubmitted later advances nothing however many seasons ago it ran. Tested (two seasons to the
end; three seasons stopped in the second, then resubmitted).

**Unverified / open**: Windows beyond the paths above (launcher, lock takeover); network drives;
season 100 performance; as-of views; records over the current season (archived seasons only); dated
partnerships during a season come from the archive (through the last season end).

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
3.13, Linux; both measured the same day, `tools/benchmark_skip.py --from-world`; superseded by the corrected
benchmark in the next section: these runs kept the preparation world in the measured process and read worker
memory from exited processes):

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

## Correctness and measurement pass (owner review of ba94d2f)

Same status words as above. No long simulation was started, nothing was removed from the world, and no
gameplay rule or probability changed: two seasons (seed 2027, quarter population, strict checks) simulated by
ba94d2f and by this pass's code give identical diagnostic data, archived seasons and people / relationship /
records tables, every reconciliation passing.

**Completed**
1. **Observer history consistency** — reproduced (an observer's Archive listed [2027] while its index answers
   already included a season published by another Session), fixed, tested (e2d341c). An Archive is one
   snapshot of a published generation (files, then an index read transaction in WAL mode, a stamp check and
   retry; every index query limited to its seasons; a removed or republished season file raises
   `ArchiveChanged`). The observer refreshes at every page and advance and closes replaced snapshots.
   `tests/test_history_consistency.py`: another Session publishing (profiles, starts, all boards, prize totals,
   weeks at No. 1, moments, overview), an Archive opened mid-publication, rollback and replay, an interrupted
   index backfill, repeated reloads.
2. **Connections and heap freezing** — measured, fixed, tested (e2d341c). Each reload left its SQLite connection
   open: index file descriptors 1 -> 21 over 20 reloads, held by cycles `gc.freeze` had put out of reach
   (the old Archives themselves were freed). Now 2 at most (one close deferred by SQLite) and 0 once closed;
   20 session reopen cycles: no growth (2), memory flat after the first few (206 -> 214 MB on a small world).
   Freezing is balanced: unfreeze and one collection (about 1 s on the 50-season world; 1.8 s measured in the
   benchmark) before each re-freeze. In the tests, only test code left Archives unclosed (now closed).
3. **Benchmark** — fixed (d86a3c8): preparation in its own process, `--workers` on the measured session,
   live-worker memory (RSS and PSS, sampled), every part separate, the user-visible skip explicit.
4. **Majors in calendar order** — reproduced, fixed, tested (5169e9f); reports regenerated (ea7b508), marked as
   corrected analysis of the 7334ffe world, originals kept.
5. **Season indexes** — measured with EXPLAIN QUERY PLAN, implemented (bc77c74): reading one season's starts
   scanned all 7.0 M rows; season indexes on starts, seasons and careers (one season 362 -> 133 ms; first
   Records page on the 50-season world 29.9 -> 16.2 s; re-indexing a season 4.9 -> 3.5 s; index +10%).
6. **Preservation** — the original world still matches the export's checksums; a full restore drill from the
   two delivered parts passed (both checksums, history read, session reopened); the archive's README had a
   `history_query.py` line without its command (corrected steps in `reports/long_run_2027/README.md`).

**Corrected benchmark** (season 51 on a copy of the 50-season world, Intel Xeon @ 2.10 GHz, 4 logical CPUs, 15
GB, Python 3.13, Linux; clean measured process; the one-time first open of the copy, about 100-120 s for index
upgrades, done beforehand in its own process and excluded):

| Code, workers | Skip (click to overview) | Simulate | Save | Publish | Settle | Reload + overview | First Records page | Peak memory (main RSS / all PSS) |
|---|---|---|---|---|---|---|---|---|
| ba94d2f, 4 | 237.7 s | 208.6 s | 17.6 s | 7.1 s | 0.0 s | 4.4 s | 29.9 s | 2.36 GB / 3.8 GB |
| this pass, 4 | 239.6 s | 209.2 s | 17.2 s | 6.7 s | 1.8 s | 4.7 s | 16.2 s | 2.36 GB / 3.8 GB |
| this pass, 3 | 244.2 s | 214.5 s | 16.5 s | 6.9 s | 1.9 s | 4.5 s | 15.1 s | 2.36 GB / 3.8 GB |
| this pass, 4: season 1 of a new world (seed 2027) | 121.0 s | 114.7 s | 2.6 s | 2.8 s | 0.3 s | 0.7 s | 0.3 s | 0.56 GB / 0.73 GB |

The earlier "3.6 GB" main-process figures included the preparation world kept alive in the same process, and
the earlier worker figure was from exited processes; earlier timings ran with the world's saved 4 workers.
Simulation time on this container also drifts between sessions (190 s earlier, 209 s now for the same
work), so only same-session comparisons are meaningful.

**Partial / open**
- The two-minute target is **not met**: about 240 s at season 51 and 121 s in season 1 (4 workers; 164 s with 2).
  Simulation is about 87% of the skip. Next, in order: send each course to the workers once rather than with
  every site, and return only the hole data that is archived (both cut pickling and pipe traffic in the main
  process); cache each monthly plan's event values by what they depend on; then measure on the intended
  hardware (more cores shorten the shot simulation; the main process's weekly work is serial).
- **Season 100 is unmeasured**: no season-100 save exists; producing one needs a long run (not started).

**Untested assumptions**
- WAL needs shared memory: on network drives SQLite cannot use it, no read transaction is held there, and a
  rollback could still mix into an open snapshot's index answers.
- Windows: hard links, the lock file, `os.replace` over open files, fsync, WAL files, deleting a test's
  temporary directory while a connection is open, and the restore steps' Windows commands.

## History correctness and measured performance pass (owner review of 45c2dee)

Status words: **implemented**, **tested** (regression tests, full suite), **measured** (benchmarks or
equivalence on copies of saves), **unverified** (not shown at the scale or on the platform that matters).
No long simulation was started; no population, event, shot or history was removed; no gameplay rule changed.

**Correctness** (each reproduced first, then fixed; separate from the performance commits)
1. **Publication as one atomic manifest** — implemented, tested (fa72a8e). Reproduced: a publisher stopped
   between the tables and the season list left readers 463 course records, 632 stints and 14 moves from a season
   they did not have. Now immutable generation-named files selected by `archive/MANIFEST.json` (atomic); index
   rows carry their source file; recovery and migration publish whole manifests. `tests/test_publication.py`
   stops a publisher after every step (season end and rollback) and compares people, residence, relationships,
   records, starts, prizes, rankings and index use with clean references.
2. **Live observer follows committed generations** — implemented, tested (fa72a8e). Reproduced: after another
   process ended the season, the observer showed week 51 beside the 2028 history. `tests/test_observer_sync.py`:
   another process playing a week, ending a season, recovering to an earlier generation, still publishing;
   stale forms refused, resubmitted ones applied once, nothing replayed.
3. **Recoverable records refresh** — implemented, tested (fa72a8e): a failure after one new season keeps the
   previous snapshot, drops the partial statistics, and the retry equals a fresh reader.
4. **Tournament totals** — implemented, tested (d0b0576). Confirmed: no world had ever recorded them (the call
   was missing). Recorded per site and layout from completed stroke-play events of 2+ rounds; editions now keep
   their format; `totals_since` marks the first season recorded. For the 50-season world: 1,285 totals
   reconstructed exactly from its evidence, as a report (`reports/long_run_2027/TOTALS_RECONSTRUCTED.md`);
   the world is unchanged.
5. **Benchmark cleanup** — implemented, tested (d7af5aa): the whole observer closed in `finally`, sampler and
   instrumentation undone however a skip ends.

**Performance** (profiled first; each checked with `tools/equivalence_check.py`: every result, statistic,
development, familiarity, finance and ledger, staff relationship and work, fatigue and injury, ranking,
record, moment, history line and the published archive identical to d7af5aa, over a full small-world season
with match play, playoffs, missed cuts and a publication, and weeks of the 50-season world)
- Measured season 51 (52 weeks, 4 workers): workers playing every shot about 60-65 s; main process monthly
  plans 27-30 s, weekly entries 23 s, development 12 s, recording results 10 s, rankings / fame / finances /
  access about 15 s; garbage collection about 17 s; data to and from workers 84-86 MB and 38-39 MB a season
  (pickled in about a second). **Not done, by measurement:** caching courses in workers and shrinking worker
  payloads (courses are a small part of 86 MB a season; the whole transfer is about 1% of the skip). The
  monthly planning cache was profiled: it is about 11% of planning; the rest is per-golfer work, so it was
  not extended.
- **Collector paused while weeks are simulated** — implemented, measured (d3f8da3): identical results.
- **Derived self-misreadings saved with the world** — implemented, measured (a706722): identical results; the
  first monthly plan in a new process 4.29 -> 1.64 s on a world saved by this code (no effect on worlds
  saved before it until their first save, such as the 50-season run).

**Benchmark** (copies of the same saves, this container: Intel Xeon @ 2.10 GHz, 4 logical CPUs, 15 GB,
Python 3.13, Linux; 4 workers; clean measured process; the copy's one-time first open -- recovery, index
upgrades, migration to a manifest: 92-96 s -- done beforehand in its own process and excluded):

| Code | Season | Click to overview | Simulate | Save | Publish | Settle | Reload + overview | First Records page | Peak memory (main RSS / all PSS) |
|---|---|---|---|---|---|---|---|---|---|
| d7af5aa | 51 (13,187 active) | 197.4 s | 175.4 s | 11.5 s | 5.0 s | 1.7 s | 3.7 s | 15.6 s | 2.36 GB / 3.8 GB |
| a706722 | 51 | 189.6 s | 165.4 s | 13.8 s | 4.4 s | 1.8 s | 4.2 s | 15.0 s | 2.37 GB / 3.8 GB |
| d7af5aa | 1 (6,449 active) | 117.0 s | 112.1 s | 2.4 s | 1.8 s | 0.2 s | 0.6 s | 0.3 s | 0.47 GB / 0.57 GB |
| a706722 | 1 | 108.8 s | 103.7 s | 2.7 s | 1.5 s | 0.3 s | 0.6 s | 0.4 s | 0.47 GB / 0.57 GB |

This container ran the same work faster than in the previous session (season 51 at d7af5aa-equivalent code:
about 240 s then), so only same-session rows compare. **Season 1 is under 120 s here; season 51 is not
(about 190 s); season 100 is unmeasured** (no season-100 save; making one needs a long run).

**Remaining blockers to 120 s at season 51+** (measured): the workers' share (60-65 s on 4 CPUs) shrinks
only with more cores; the main process's serial weekly work (about 105 s) is spread over per-golfer
planning, entries, development and recording. Making it substantially faster means doing per-golfer work in
parallel, which changes the order random numbers are drawn in -- an engine change with different (equally
valid) outcomes, not a performance-only one: an owner decision. Measure on the intended hardware first.

**Unverified:** Windows (hard links for published files fall back to copies; WAL; replacing the manifest
while a reader holds the old one; the lock), network drives (no WAL: no pinned snapshot), season 100.

**Measuring on the intended hardware** (Python 3.11 or later, nothing to install; it never changes the world it
copies): `python tools/benchmark_skip.py --workers N` (season 1 of a new world, about 2 minutes), and with the
50-season export extracted (2 GB free), `python tools/benchmark_skip.py --from-world <extracted>/world_2027
--workers N` (season 51 on a copy). Try N = the number of logical CPUs, and one fewer. The printed lines are
the whole result.

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
6. ~~A throwaway observer prototype~~ -- superseded by the observer alpha (above), which grew from it:
   `tools/observer.py` (standard library web server; Overview with Advance week / 4 weeks / to end of
   season through the session, golfer profiles with career, team history, results with entry routes and
   moments, tournament histories and edition leaderboards with coach and caddie, course pages, records and
   frivolities with evidence, moments, search). Not the chosen framework.
7. First usable slice: Overview, Golfer profile, Tournament edition, Course profile and one Records or
   Frivolities list, tested as complete browsing journeys (see the document).

Open owner decisions: framework and desktop packaging, visual design, the first record definitions and
frivolities lists, when to deliver as-of views and a university directory, performance budgets and
accessibility checks.

## Earlier "Next" list (superseded by the current delivery order at the top; kept for its notes)

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
- Weather: simulated seasonal climate (weather.py: climate group, hemisphere, coast, style), wind direction per
  hole, wet rounds; no per-wave tee times, no temperature or seasonal firmness (open decision).
