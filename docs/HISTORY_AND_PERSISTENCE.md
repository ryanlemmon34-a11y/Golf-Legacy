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
  (`session.settle_heap`, repeated after each archived season; full collections found no garbage); archive JSON is written with
  the C encoder at gzip level 6. Both are performance only: the same simulated state (fingerprinted) and
  the same archive text. Orphaned temporary files
  are removed on opening, but only when the opener can take the lock: opening a world while another
  process advances it leaves that process's work alone (all tested with simulated crashes).
- **History in the same transaction.** At season end the season's history (its season file, the people,
  relationships and records tables, the list of archived seasons) is staged inside the new generation
  (`gen_n/archive/`, hashed with it), not written to the archive. After the commit it is published to
  `archive/` (season file and index rows first, then the tables, the list of seasons last) and
  `archive/PUBLISHED` records the generation. A crash before the commit leaves the archive untouched; a
  crash after it is repaired by publishing the committed generation's staged history again (on opening or
  before the next advance; idempotent). The running world, the committed checkpoint and the visible history
  therefore agree after any failure, in the same process or after reopening (tested: failed final commits
  of long advances, failures at a season-end commit, a crash between commit and publication, in the first
  and second seasons, comparing seasons, index, people, relationships and records with an uninterrupted run).
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
  archive/             the history archive (below); PUBLISHED: the generation it shows
```

### The archive

```
world.json            format, seed, years written; tours, series, courses and layouts
people.json.gz        every person: name, country (nationality), born, hometown, birthplace, residence and
                      dated moves (docs/RESIDENCE.md), arrival, roles (golfer/coach/caddie)
relations.json.gz     every stint, and each pair's working relationship
records.json.gz       course records per layout, every mark with golfer id and event id
years/YYYY.json.gz    one season: every edition (venues, finishers per site, each golfer's team that
                      week), every golfer's season, career decisions with reasons, staff work, and
                      that season's narrative log lines (display text only)
```

**The query index** (`archive/index.sqlite`, `golfsim/archive_index.py`) is derived from the season files:
each archived season is indexed in one transaction that first removes that season's rows (so a retried
season never duplicates), and it can be rebuilt from the files at any time. A golfer's results, a
tournament's editions, a course's editions or an edition's leaderboard are each one indexed query
(`Archive.results` uses it when it covers every season). Since schema 2 it also holds each week's No. 1
and each golfer's season row (compressed), so records, recaps, careers, moments, course histories and weeks
at No. 1 never decode the season files. Every site's winner of a multi-site event is in `starts`
(`editions.winner` is only the first site's). An index from before schema 2 is completed once by the session
that owns the world, under its lock (about 70 s for 50 seasons); readers meanwhile fall back to the season
files. Size: about 10 MB a season, 18 MB with schema 2 (881 MB for the 50-season world).

**Memory.** `Archive.year` keeps only the `CACHE_SEASONS` (4) most recently decoded seasons (late seasons decode
to hundreds of MB). `HistoryStats` holds every start as one integer, edition rank and position (`Starts`), not a
tuple, and builds from the index one season at a time. On the 50-season world, opening the Overview fell from
76 s and 7.7 GB to under 1 s, and every Records board from 8.4 GB to 1.1 GB peak, with identical answers (all 28
boards, recaps, courses, moments, weeks at No. 1, careers).

Facts are stored once and referenced by id: a win lives in its edition; a coach's record is derived
from stints and editions. The archive grows by one season file a year instead of copying data into
every profile, so centuries stay manageable. Narrative log lines are kept for display, but nothing is
reconstructed from them.

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
