# Golf Legacy V1 — UI Requirements (baseline)

Summary of the owner's *Golf Legacy V1 UI Requirements — History exploration baseline* (version 1.0,
27 October 2026), the companion to the V1 Universe Simulation Roadmap. It describes the intended
experience; individual golfer control remains V2. **The observer alpha** (`tools/observer.py`,
`docs/OBSERVER_ALPHA.md`; owner roadmap of 29 October 2026: UI first) covers part of it now -- see
"Observer alpha: what exists" at the end; the rest is still to build.

## The experience

An interactive golf encyclopedia that keeps making new history: the player advances the world week by
week and explores it through linked pages. A major winner leads naturally to their caddie, the caddie's
former players, an old rival and a memorable tournament: connections, not a wall of statistics.

- **Sidebar.** World (Overview, Calendar, Rankings) · Explore (Golfers, Coaches, Caddies, Courses,
  Nations, Tours, Tournaments) · History (Seasons, Records, Frivolities). Tours are distinct from
  tournaments. A university directory is a possible later addition, not a reason for college management.
- **Always available.** Universal search and the simulation date at the top; Advance Week and longer
  simulation without leaving the page being read.

## Profiles (the heart of V1)

Every person, year, result, tournament and course links to its page; a consistent structure adapted to
the subject.

- **Golfer:** overview (status, highlights, recent news); career (season by season: results, tour
  progression, rankings, development); results (searchable, linked to editions); team history (coaches
  and caddies with dates and results during each partnership); timeline (debuts, breakthroughs,
  injuries, major wins, career changes, retirement); records and frivolities lists they appear on.
- **One person, several careers:** a golfer who becomes a coach or caddie keeps one identity, with
  Playing, Coaching and Caddying sections; becoming staff never hides the playing career.
- **Reciprocal staff relationships:** each stint on both histories, same dates, current or ended,
  achievements during it; a coach's concurrent players stay understandable; association is not
  causation.
- **Courses** (hosted tournaments, editions, course records, standout performances), **Nations**
  (champions, major wins, tour representation, development over time), **Tours** (membership,
  graduates, champions, debuts, starts, progression), **Tournaments** (a permanent page across editions
  *and* an edition page: leaderboard, course, staff involved).

## Records

One central Records section and contextual records in profiles — views of the same facts and
definitions. Ranked lists (not only the holder), filterable by season/era, tour and all time, every
row linked to its supporting results. Classifications that applied when a result happened are kept (an
event changing tour or prestige later must not rewrite its history); course records keep enough context
not to compare different course versions or set-ups. Definitions to agree before building: start, win,
major, debut, age at achievement, ties, qualifying scope, tour-specific vs all-tour, individual vs
staff-linked achievements, no double counting.

## Frivolities

Real, unusual patterns from the simulated history (inspired by Basketball GM), never scripted:
youngest/oldest winners and major champions; youngest/oldest Premier debutants; most starts before a
first win; most starts without a win on a tour; longest wait between wins; most runner-up finishes
without a win; late debuts and comebacks after losing a card; wins on the most different tours; longest
coach–player partnership; coaches with the most major champions; former players who later caddied for a
rival (where the record supports it); consecutive wins, cuts made and weeks at No. 1; longest major
droughts ended. Each opens into a ranked, filterable list with evidence. "Has not won yet", "retired
without a win" and "starts before a first win" are separate; active careers are unfinished, not failed;
scope is stated (first Premier start ≠ first professional start); ages use the real event date only
where that precision exists.

## Seasons and historical truth

- A readable recap per season linking to champions, breakthroughs, rivalries, declines, retirements,
  staff changes and records broken — only from recorded events; a "rivalry" must have an inspectable
  factual basis.
- Eventually an **as-of-year view**: rankings, records and relationships as they stood then, with no
  future leaking in; the simulation date distinct from the date browsed.
- **Incomplete starting careers:** golfers who began before the simulation have unknown earlier results.
  Records say whether they use a complete observed career or only the archive's coverage; uncertain
  debuts are excluded or labelled; a missing result is not proof an event never happened; active players
  are not final lifetime outcomes.
- Durable safeguards: stable identities through retirement, staff transitions, renaming and rebranding;
  dated relationships and event-time attribution; old links keep working; historical nationality, tour
  classification and course version where the simulation supports changes.

## First usable slice (recommended)

Overview, a Golfer profile, a Tournament edition and a Course profile, plus one working Records or
Frivolities list, tested as complete journeys: advance a week and see what changed without losing
context; follow a result to its edition, course and other players; open a staff relationship from both
sides with the same dates and achievements; open a record and verify its evidence; reopen a saved
universe and find profiles, dates and links coherent. Usability: searchable, sortable, paginated tables;
incremental loading of long timelines and century archives; filters and back-navigation preserved;
readable, keyboard-accessible, sufficient contrast, colour never the only signal; clear empty states
(unavailable vs not recorded vs zero); useful density over decoration.

**Open decisions:** framework, desktop packaging and component library; visual theme, typography,
portraits, course art, layouts; exact record definitions and the first frivolities lists; when to
deliver as-of views and a university directory; measured performance budgets and accessibility checks.

## Data readiness (what the history archive already supports)

Assessed against `golfsim/archive.py` and `docs/HISTORY_AND_PERSISTENCE.md` as of this commit.

| Requirement | Today | Gap to close before the UI |
|---|---|---|
| Stable person ids across golfer / coach / caddie careers | Yes (one id space; roles in `people`) | — |
| Dated staff stints, both directions, results during them | Yes (`relations`, team recorded with every result) | — |
| Tournament identity vs editions; edition leaderboard, course, staff | Yes (series id, event id, sites, finish, team) | — |
| Entry route and status at entry per start | Yes (this access pass) | — |
| Course records with golfer and event | Yes, per layout | Course version ids if layouts are ever changed |
| Classification at event time (tour, tier, category, prestige) | Yes: every archived edition carries its name, tour, tier, category and prestige when played | — |
| Coverage of careers that began before the world | `initial` and `created` flags per person | Use them in every record definition |
| Ages at achievement | Birth year and event week | Event dates are weeks, not days: age precision is annual unless dates are added |
| Weekly No. 1 and weekly rankings (weeks at No. 1, as-of views) | Yes: each week's world and amateur top 100 (`Archive.ranking`, `weeks_at_number_one`) | Deeper ranking history if as-of views need it |
| Cuts made, runner-ups, droughts, starts before first win | Yes, from finishes, in `history_stats` | — |
| Central records and frivolities from one set of definitions | First version: `golfsim/history_stats.py` (definitions, 25 boards with evidence and active/partial flags; `tools/history_query.py ARCHIVE board NAME`) | Owner's choice of the first lists; more scopes and filters (era, nation) |
| Century-scale browsing | Yes: `archive/index.sqlite` (person → starts and seasons, series → editions, course → editions, edition → leaderboard; ~8 MB a season), one query per page | Pagination in the UI |
| Season recaps from recorded facts | `Archive.recap` and the narrative log | Richer recap selection rules |

## Observer alpha: what exists (and what does not yet)

Built on the session and archive (no second engine); standard-library web pages, local only. Status words as
in the backlog: implemented, tested (automated), measured, unverified.

| Requirement | Alpha | Status |
|---|---|---|
| Create a seeded world, open, copy without overwriting, read-only browsing vs resuming | World library: create (name, seed), open, browse history, copy, close; date, seed, engine and save-format compatibility per world | implemented, tested |
| Worlds saved by another engine (the 50-season world, 7334ffe) | Never resumed in place: browse read-only, or copy with an explicit "continue with this engine" (recorded in the copy) | implemented, tested; measured on a copy of the 50-season world |
| Advance one week, four weeks, to season end; one at a time; no double application | Background jobs; forms carry world, date and a one-time key; a second request while one runs is refused, a repeat is shown the running one | implemented, tested |
| Progress, busy state, errors, browsing during an advance | Progress bar and status endpoint; pages drawn from the last committed week (named in the footer); errors shown with the world at its last committed week and written to its log | implemented, tested |
| Stop at a safe boundary; server restart or crash mid-advance | Stop after the current week keeps every completed week; an advance cut short by the observer stopping is reported on the next open and nothing half-written is kept | implemented, tested (POSIX); Windows unverified |
| Easy Windows launcher, stop/reopen instructions | `RUN_OBSERVER_WINDOWS.bat`; Quit button; `docs/OBSERVER_ALPHA.md` | implemented; unverified on Windows |
| Overview, rankings, results, golfer profiles, records, moments | Kept and extended | implemented |
| Browse/filter golfers, coaches, caddies, courses, nations, tours, tournaments, calendar | Directories with filters, sorting and pages; calendar of the current season | implemented, smoke-tested |
| Current-season and first-season events linked like archived ones; no double counting or future leakage | The current season's editions use the archive's own edition record; only seasons the published history does not hold are drawn from the snapshot | implemented, tested (an edition reads the same before and after its season is archived) |
| Event -> golfer, event-time coach and caddie, course, tournament; Back keeps filters | Links everywhere; filters are in the URL | implemented |
| Coach and caddie stints both ways; separate playing and staff tabs under one identity | Person page tabs: Playing, Results, Coaches & caddies, Coaching, Caddying | implemented (stints as archived at the last season end; current coach/caddie from the snapshot) |
| Layouts distinct from courses, editions from tournaments | Course page lists layouts and per-layout records; edition and tournament pages are separate | implemented |
| First records/frivolities: youngest/oldest major winner, youngest/oldest Premier debut, most starts without a win by tour; label incomplete history and age precision | "Start here" lists; scope filter (all, professional, Premier, major, any tour); partial/active flags; age = season year minus birth year, stated | implemented (archived seasons only) |
| Diagnostic copy of a saved world | Zip with the committed save and every history file it needs, log, versions, seed, date, generations, file hashes and an issue note; optional index and previous checkpoint; local paths removed from the log; never uploaded | implemented, tested (the package reopens as the same world) |

### Playtest increment (owner roadmap of 29 October 2026)

| Requirement | Observer | Status |
|---|---|---|
| Current ratings, archetype, signed changes against an explicit baseline, unavailable without one, potential hidden | Ratings cards on the person page: now, this season (since its start), last season (start to start); recorded snapshots from the archive | implemented, tested |
| Age before birth year; year and age in career rows; approximate labelled | "Age N*" with the note; season rows show year and age | implemented, tested |
| Coach clients as linked rows with tour/status; history separate | Current clients table (tour, status, world rank, since); all partnerships; staff season by season (clients, starts served, client wins, weeks, reputation, earnings) | implemented, tested |
| One person id through role changes; separate tabs | Playing / Results / Coaches & caddies / Coaching / Caddying tabs on one page | implemented; checked on the 50-season copy (5,233 people with both careers) |
| Shortlists for every entity type, per world, persistent | ☆ Shortlist on people, courses, nations, tours, tournaments, editions; Shortlist page; kept in the world folder | implemented, tested |
| Remove world with confirmation, reversible, guarded | Remove… to the trash; restore; delete permanently only by typing the name; refused for the open world or during an operation | implemented, tested |
| Prize money leaderboard (year / all-time, tours) | Prize money page: gross tournament prize money; per tour recomputed and reconciled ("unknown" otherwise) | implemented, tested; reconciled on the 50-season copy |
| Stats directory (year / all-time, tour / overall, sortable, linked) | Stats page with inclusive top-N, runner-up, cuts made of cut events, prize money; each figure opens its results | implemented, tested |
| Moments show the course and layout | Venue column on moments (layout link), "not applicable" without one | implemented, tested |
| Starting year separate from seed; random by default; both recorded | Create: starting year and seed (random suggested); shown in the library, recorded beside the world and in problem reports | implemented, tested |
| Career honors (text trophy case) | Categories by each edition's classification when played; count, first, latest, links | implemented, tested |
| Season and tour history, expandable, linked, partial current season | Season by season with *show each tour*; current season marked "so far" | implemented, tested |

Not yet: as-of-year views, the university directory, nation development, era filters on records, charts and
art, a packaged desktop app; course / tour / nation season rollups beyond their existing pages.
