# Golf Legacy — History, Identity and Persistence

Code: `golfsim/history.py` (relationships), `golfsim/archive.py` (the history archive),
`golfsim/savegame.py` (simulation saves), `golfsim/records.py` (course records),
`tools/history_query.py` (a debug view). Tests: `tests/test_history.py`.

The goal is a world whose history can be explored for decades or centuries — click a golfer, their
coaches and caddies, the other players those staff worked with, the tournaments, courses and records.
The screens come later; this is the data underneath them.

## Stable identities

| Entity | Id | Notes |
|---|---|---|
| Person | integer, one space for the whole world | Golfers, coaches and caddies. A former player who becomes a coach or caddie keeps their id: the playing career and the staff career are two views of the same person. Ids are never reused; nobody is deleted on retirement. Names are for display only and need not be unique. |
| Course / layout | `course_id` (slug) / `course_id:Layout` | Fixed by the course library. |
| Tour, event series | tour key / `series_id` | Fixed by the calendar. |
| Event edition | `YEAR:SERIES_ID` | One per series per year. |

## Relationships

Every coaching, caddying and school-team arrangement is a **stint** (`history.Stint`): both people's
ids, the kind (`coach`, `caddie`, `school`), the arrangement (`fee`, `share`, `tour bag`, `school team:
CO_US_D1`), start and end (year, week), who started it, who ended it and why, and how much they actually
worked together. Both profiles read the same record. A pair that separates and reunites has two stints.
Current assignments ("who coaches whom now") are an index kept only by opening and closing stints.

**At the time of each event:** every result keeps the coach and caddie each golfer had that week
(`EventResult.team`). So "coached this player during these years" (the stint) is distinct from "was
their coach for this victory" (the team recorded with the win), and nothing is reattributed when
assignments change later. Course records carry the golfer's id and the event id, not only a name.

## Three kinds of saved data

| | What it is | Use it for | Not for |
|---|---|---|---|
| **Analysis snapshot** (`tools/long_world.py` `seed_<s>.json.gz`, `REPORT.md`) | Yearly statistics and checks for a test run | Judging whether a world behaves believably | History browsing (it is a summary) |
| **History archive** (`golfsim/archive.py`) | The world's history as normalised facts, one file per season | Exploring and querying history, decades later | Restarting the simulation |
| **Simulation save** (`golfsim/savegame.py`) | The whole simulation state, pickled, tied to the engine commit | Resuming exactly where a run stopped (tested: identical results) | Long-term storage across engine versions |
| **Session checkpoint** (`golfsim/session.py`) | The live simulation and its weekly cursor, committed atomically each week | The observer's Advance Week: always resumable, crash-safe | Long-term storage across engine versions |

### The weekly session (`golfsim/session.py`, roadmap M1)

The one way the observer advances a world: `Session.create(dir, seed)` / `Session.open(dir)`, then
`advance_one_week(expected=cursor, op_key=...)`, which commits every week; longer advances
(`advance(n, progress, cancel)`) run the same weekly step and commit once, at the end or when cancelled
between weeks (an interruption mid-week commits nothing), so skipping to the end of a season does not pay
for 52 checkpoints. `tools/world.py` drives a world from the command line (create, status, advance,
board). It reuses the season's own steps
(`Season.start_year`, `advance_week`, `finish_year` — the same ones `run_year` uses), so a world advanced
week by week is the world a whole-season run produces (tested, fingerprint-equal).

- **Cursor** `{year, week, phase}`: 'start' means 1 January has not run (the next advance runs it, then
  week 1); after week 52 the same advance runs the end of the season and archives it; the cursor moves to
  the next year's 'start'. Year start and year end run once each.
- **Idempotent and serialised.** A stale `expected` cursor is refused (`StaleCursor`) and changes
  nothing; repeating any of the last 32 committed `op_key`s (one-week or longer advances) returns its
  stored result without simulating. Keys are checked against the committed world on disk, under the lock,
  so a retry through a second handle, or a form resubmitted after later advances, is recognised (the
  observer's forms carry the cursor they were drawn at and a one-time key). Advances are serialised in the
  process (a lock) and across processes (a lock file holding the owner's process id and host; `Busy`). A
  lock left by a process that has died is taken over on POSIX, same host only. Two concurrent requests for
  the same week commit exactly one (tested).
- **One coherent world per checkpoint generation.** Each advance writes a new generation (the whole live
  simulation plus the session state) to a temporary directory, hashes it and reads it back, renames it
  into place, then atomically replaces the `CURRENT` pointer. A crash before the pointer moves leaves the
  previous world; after, the new one. Any failure before the commit, one-week or multi-week, an error, an
  interrupt or a failed save, reloads the committed world in memory, so memory never runs ahead of disk.
  The last known good generation is kept; a damaged current one falls back to it. Loading runs with the
  cyclic garbage collector paused, then freezes the loaded world out of later full collections
  (`session.settle_heap`). Freezing is balanced, not cumulative: after each archived season, and on any
  load after the first, everything is unfrozen and collected once (about 1 s on the 50-season world) before
  the rest is frozen again, so nothing dropped since (a replaced observer snapshot, a world reloaded after
  a failed advance) stays out of the collector's reach for more than a season. Archive JSON is written with
  the C encoder at gzip level 6. Both are performance only: the same simulated state (fingerprinted) and
  the same archive text. Orphaned temporary files
  are removed on opening, but only when the opener can take the lock: opening a world while another
  process advances it leaves that process's work alone (all tested with simulated crashes).
- **History in the same transaction.** At season end the season's history (its season file, the people,
  relationships and records tables, the list of archived seasons) is staged inside the new generation
  (`gen_n/archive/`, hashed with it), not written to the archive. After the commit it is published to
  `archive/`: each file under a name carrying the generation that produced it, never rewritten (season
  files `years/YYYY.gNNNNNN.json.gz`; `world`, `people`, `relations`, `records` `.gNNNNNN.json[.gz]`), then
  the index rows (each season's recorded with the file it came from), then `archive/MANIFEST.json`, which
  names exactly those files and is replaced atomically: the moment readers see the new history, whole.
  Afterwards rows of seasons no longer published (a rollback) and files neither this manifest nor the
  previous one (`MANIFEST.prev.json`, kept for readers that opened it a moment before) names are removed.
  A crash before the commit leaves the archive untouched; a publisher stopped at any step after it leaves
  readers the previous manifest's history, whole, and the next session to open the world (or its next
  advance, or an observer finding the lock free) publishes the committed generation's history again. After
  a rollback, recovery publishes the earlier generation's history as a new manifest; a lost manifest is
  rebuilt from the committed generation (each season's latest file from a generation no later than its
  history). An archive from before manifests (`world.json`, `people.json.gz`, ..., `PUBLISHED`) is read as
  before, read-only, and migrated by the first session that owns it: its season files are adopted as they
  are, with the index rows already indexed from them (tested: `tests/test_publication.py` stops a
  publisher after every step, for a season end and for a rollback, and checks people, residence,
  relationships, records, starts, prizes, rankings and index use all belong to one generation; files are
  never rewritten; migration keeps the index).
- **Bounded checkpoints.** The live simulation keeps only this season and last of its per-season tables,
  older results reduced to their winners (`Season.prune_history`), and is saved without the standard
  course library (rebuilt from its seed), so a weekly checkpoint does not grow with the world's history.

```
world/
  CURRENT              {"generation": n, "dir": "gen_00000n"}  (replaced atomically: the commit)
  gen_00000n/          state.pkl.gz (simulation + session state), meta.json (cursor, engine, sha256 ...),
                       archive/ (a season end's staged history, until the next generations replace it)
  gen_00000(n-1)/      the last known good generation
  lock                 present while an advance runs (process id and host)
  archive/             the history archive (below); MANIFEST.json: the history it shows
```

### The archive

```
MANIFEST.json                 the published history: its generation, seasons and the file of each part
                              (replaced atomically; MANIFEST.prev.json: the previous one)
world.gNNNNNN.json            format, seed, years written; tours, series, courses and layouts
people.gNNNNNN.json.gz        every person: name, country (nationality), born, hometown, birthplace,
                              residence and dated moves (docs/RESIDENCE.md), arrival, roles
relations.gNNNNNN.json.gz     every stint, and each pair's working relationship
records.gNNNNNN.json.gz       course records per layout, every mark with golfer id and event id; lowest
                              36/54/72-hole tournament totals (since `totals_since`)
years/YYYY.gNNNNNN.json.gz    one season: every edition (venues, its format then -- rounds, match play --,
                              finishers per site, each golfer's team that week), every golfer's season,
                              career decisions with reasons, staff work, and that season's narrative log
                              lines (display text only)
index.sqlite                  the query index (below)
```

Files are never rewritten; `gNNNNNN` is the generation that produced them. Archives written by
`ArchiveWriter` alone (tests, short runs) and by versions before manifests use fixed names (`world.json`,
`people.json.gz`, `years/YYYY.json.gz`, ...) and are read the same way.

**The query index** (`archive/index.sqlite`, `golfsim/archive_index.py`) is derived from the season files:
each archived season is indexed in one transaction that first removes that season's rows (so a retried
season never duplicates), and it can be rebuilt from the files at any time. A golfer's results, a
tournament's editions, a course's editions or an edition's leaderboard are each one indexed query
(`Archive.results` uses it when it covers every season). Since schema 2 it also holds each week's No. 1
and each golfer's season row (compressed), so records, recaps, careers, moments, course histories and weeks
at No. 1 never decode the season files. Every site's winner of a multi-site event is in `starts`
(`editions.winner` is only the first site's). An index from before schema 2 is completed once by the session
that owns the world, under its lock (about 70 s for 50 seasons); readers meanwhile fall back to the season
files, also when the backfill was interrupted (tested). The large tables (starts, seasons, careers) are also
indexed by season, so reading one season's starts or replacing one season touches that season's rows only
(chosen with EXPLAIN QUERY PLAN: one season's starts 362 -> 133 ms, replacing a season 4.9 -> 3.5 s on the
50-season index). Size: about 10 MB a season, 18 MB with schema 2, about 19.5 MB with the season indexes (881
MB for the 50-season world before them, 972 MB after re-indexing a season with them, part of it free pages).

**Consistent snapshots.** An `Archive` is one snapshot of one published history: it reads the manifest
once and only the files it names, which never change, so its people, relationships, records and seasons all
belong to one generation wherever a publisher is. It holds a read transaction on the index for its lifetime
(WAL mode, so the session keeps publishing meanwhile) and uses the index only if, in that snapshot, every
season's rows were indexed from exactly the file its manifest names; otherwise the season files of the same
manifest answer. Every index query is also limited to the snapshot's own seasons. A season file collected
after two newer publications raises `ArchiveChanged` rather than mixing two generations. `Archive.close()`
(or `with Archive(...)`) releases the connection; index writers always close, also on errors. Without shared
memory (network drives) SQLite cannot use WAL: then no read transaction is held and only the season limit
and the per-season source check apply (untested there).

**The live observer** (`tools/observer.py` on a session directory) shows the committed world and its history
as one generation. Every page and advance starts with `World.reload`: if another process committed since (an
ordinary week, a season's end, a recovery to an earlier generation), the committed world is loaded as
committed -- never simulated or replayed -- together with that generation's published history
(`Session.refresh`); a publication someone left unfinished is completed when the lock is free; while its
owner is still publishing, the page keeps the previous generation, live world and history alike, and says
so. Stale forms stay refused (the cursor they were drawn at), resubmitted ones apply once (their key). A
changed history becomes a new snapshot only after the records took it in; a failure on the way keeps the
previous snapshot and rebuilds the records when next needed (`HistoryStats` marks itself incomplete until
an extension finishes). Tested in `tests/test_observer_sync.py`.

**Memory.** `Archive.year` keeps only the `CACHE_SEASONS` (4) most recently decoded seasons (late seasons decode
to hundreds of MB). `HistoryStats` holds every start as one integer, edition rank and position (`Starts`), not a
tuple, and builds from the index one season at a time. On the 50-season world, opening the Overview fell from
76 s and 7.7 GB to under 1 s, and every Records board from 8.4 GB to 1.1 GB peak, with identical answers (all 28
boards, recaps, courses, moments, weeks at No. 1, careers).

Facts are stored once and referenced by id: a win lives in its edition; a coach's record is derived
from stints and editions. The archive grows by one season file a year instead of copying data into
every profile, so centuries stay manageable. Narrative log lines are kept for display, but nothing is
reconstructed from them.

**Recorded since the observer's profile pass (29 October 2026; older archives lack them, and readers say
so):** each season's career rows carry the golfer's ratings as the next season starts (`ratings`: overall,
then the attributes in the order the world table's `rating_keys` gives; recorded after the season-end aging);
each edition carries its kind and the money and cut it was played for (`kind`, `purse`, `cut_top`,
`field_size`); each coach's and caddie's season row carries their career earnings so far (`earnings_total`).
These are written by `archive.py` only (not simulation code: the engine fingerprint is unchanged). The
observer's statistics (`tools/observer_stats.py`) recompute each event's payouts from these facts (older
archives: the calendar's purses) and check them against every golfer's season prize money as paid: on the
50-season world all 588,797 golfer-seasons reconcile.

**Recorded since rules 2026-10-30 (the 2090 world audit; `docs/AUDIT_2090_RESPONSE.md`):** each season file
names the rules version it was played under (`rules`, also in the index's meta as `rules:YYYY`); each edition
carries every golfer's stroke-play round scores per site (`scores`), the prize money each golfer was paid
(`prizes`), each round's conditions (`conditions`: wind mph, rain, pin difficulty) and, for majors, every
hole's score (`holes`) with the holes' pars (`pars`); each career row carries the winner's exemption held that
season (`exemption`), the reason for next season's card (`card_reason`), that winter's decisions
(`decisions`, the same records as the season's `transitions`) and, for college golfers, the eligibility
ledger (`college`: season number, first season recorded, last eligible season). The index (schema 3) carries
each start's prize money (`starts.prize`, NULL for seasons played before it was kept; an older index gains the
column when its own session next opens it). Seasons archived before these facts show them as not recorded:
rounds are never reconstructed from totals, money splits stay the reconciled recomputation, ratings history
starts where snapshots start.

**Recorded since the golf-statistics update (`docs/PRETEST_REVIEW_RESPONSE.md`):** each edition carries every
golfer's golf statistics counters per site (`golf`: `golfsim.golfstats.FIELDS` in order, then the longest drive
in tenths of a yard, its round and hole), each counted start's world ranking points (`points`) and, for match
play, every match (`matches`: stage, winner, loser, result, holes scheduled); each season file carries the
definitions it used (`definitions`: golf statistics version, ranking rule) and each week's world ranking top 200
with average and counted starts (`ranking_points`); the first season also keeps the points seeded when the world
began (`ranking_seed`). The index (schema 4) adds each start's points (`starts.points`). The observer's
statistics store (schema 2, derived and rebuilt from the season files) sums the counters per golfer, season and
tour and keeps per-season record rows (longest drives, event driving averages, winning margins, match results).

### Queries (`archive.Archive`)

| Question | Call |
|---|---|
| Who is person 1234? Playing and staff careers | `people[1234]`, `roles()`, `playing_career()`; staff roles from `people[...]['coach']` |
| Everyone who coached or caddied for a golfer | `golfer_staff(pid)` |
| A coach's or caddie's clients, with the results *while they were on the team* | `staff_clients(pid)` |
| Who was on a golfer's team at a given event | `team_at(pid, event_id)` |
| Every result a golfer had (with the team that week) | `results(pid)` |
| A course: editions, winners, layout records with golfer ids | `course(course_id)` |
| A season's headline facts (majors with coach and caddie, new No.1, staff moves, counts) | `recap(year)` |
| People with a given name | `find(name)` |

`python tools/history_query.py ARCHIVE examples` finds real linked histories in an archive (a former
player who became staff and later worked with players, a major winner's team, golfers with several
coaches, the busiest coach's clients, the last season's recap).

## Working relationships

Each golfer–coach and golfer–caddie pair keeps `work` (coaching weeks actually used, rounds on the bag)
and a fixed `fit`. Rapport = 1 − e^(−work / scale) (coaching scale 30 weeks, caddie 60 rounds): it rises
with actual work, with diminishing returns, never reaches 1, and fades with years apart (a reunion keeps
some of it). Effectiveness = (0.75 + 0.25 × rapport) × (1 + 0.05 × fit) scales how much of the staff
member's ability reaches the golfer — it never changes attributes, and a long-familiar average coach
never outperforms a clearly better new one.

**Special moments** are archived as facts with each season (`Archive.moments`): every hole-in-one and
albatross (golfer, edition, layout, hole, round or stage), every playoff (winner, who lost it, holes) and
every new course record once the layout had 300 earlier rounds (score, previous record and holder).
**Records and frivolities** are computed from the archive with one set of definitions
(`golfsim/history_stats.py`).

## Not yet

Profile screens; migration of old saves across engine versions (saves are for resuming, the archive is
for history).
