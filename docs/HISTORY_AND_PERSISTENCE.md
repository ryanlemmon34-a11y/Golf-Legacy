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

### The archive

```
world.json            format, seed, years written; tours, series, courses and layouts
people.json.gz        every person: name, country, born, hometown, arrival, roles (golfer/coach/caddie)
relations.json.gz     every stint, and each pair's working relationship
records.json.gz       course records per layout, every mark with golfer id and event id
years/YYYY.json.gz    one season: every edition (venues, finishers per site, each golfer's team that
                      week), every golfer's season, career decisions with reasons, staff work, and
                      that season's narrative log lines (display text only)
```

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

## Not yet

Profile screens; special moments (aces, playoffs) as their own linked facts beyond course records;
archive indexes for very long histories (queries scan season files); migration of old saves across
engine versions (saves are for resuming, the archive is for history).
