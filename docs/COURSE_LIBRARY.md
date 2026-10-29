# Golf Legacy — World Course Library

Code: `golfsim/course_gen.py` (generator), `golfsim/course_library.py` (library, venues, ratings),
`golfsim/records.py` (records per layout). Build: `python tools/build_course_library.py`.
Report: `reports/COURSE_LIBRARY_REPORT.md`. Data: `data/course_library.json`, `data/layout_ratings.json`.

## What it is

520 fictional courses, each in a real city the calendar plays in, in a style that fits the place:
links on the coasts of Scotland, England and Ireland, sandbelt in Melbourne, desert in Arizona and the
Gulf, mountain courses in the Alps and Colorado, tropical courses in Southeast Asia and Hawaii, parkland
and woodland across Europe, North America and Japan. Every course has a local-language name (checked
against a list of famous real courses so none is copied), a fictional architect, an opening year and 18
holes with par, yardage, hazards, greens and notes.

## Classes and layouts (owner decisions)

| Class | Count | Layouts | Who plays there |
|---|---|---|---|
| Elite | 34 | Championship only | **Majors and the Premier Tour only** |
| Championship | ~124 | Championship + Club | Premier, Challenger, national opens; Club tees for regional, mini and college |
| Standard (mid difficulty) | ~200 | Championship + Club, nearly half also Forward | Most of the world's tour, college and amateur golf |
| Municipal | ~22 | Regular, half also Forward | Small amateur events; future junior and high-school golf |

The easier layouts are the same holes and hazards played from shorter tees with a softer set-up:

| Layout | Length | Greens | Rough | Firmness |
|---|---|---|---|---|
| Championship / Regular | 100% | as built | as built | as built |
| Club | 93% | 1 foot slower | lighter (−0.15) | softer |
| Forward | 86% | 1.5 feet slower | lighter (−0.25) | softer |

Which layout an event uses depends on its level: majors on elite Championship tees; Premier Tour on
elite or championship Championship tees; Challenger tours, national opens, elite amateur events, final
qualifying and Q-School finals on Championship tees; regional, mini, college and national amateur golf
on Standard Championship or Club tees; 18–36-hole amateur events on Forward tees. No Premier or
Challenger event ever plays a shortened layout.

## How many courses, where

Ten seasons of the calendar are replayed. Every edition — and every site of a multi-site qualifier —
needs a free course of the right standard in its host city that week (no course hosts two events in a
week). Where none exists, one is built there; the result (about 360) is the minimum the calendar needs.
The rest of the 520 are added as extra clubs where golf is busiest. Major venues are fixed: Georgia
National for the Tour Masters every year, an elite course in every city of the other three majors' rotas
(Britannia Open venues are always links).

A series returns to the same course whenever it is in the same city, so events build history at a home
venue. If all suitable courses in that city are booked, the event moves to another city in its pool
(about 2–3% of event-sites).

## How difficult each layout is

Every layout is rated by simulation: the average score of a tour pro (75), an amateur event winner (40),
an amateur (25) and a high schooler (10). Roughly, for tour pros: elite about +3 over par (every elite course gets a championship set-up: at least 7,250 yards, tighter fairways, heavier rough, faster greens; Georgia
National +3.5), championship +1, standard −1.5 (Club −4, Forward −6), municipal −6.5. Amateurs are
punished far more on hard courses: an amateur (25) is about +19 on an elite course and +6 on a
municipal one. See the report for full ranges by class and layout.

## Records (per layout)

`RecordBook` keeps, for every layout: the course record (first to shoot it holds it; equalling it is
noted) and its full history, the record at each level of golf (Premier, Challenger, college...), lowest
36/54/72-hole totals, the highest round, the best score on every hole, every hole-in-one, rounds played
and scoring average. `play_event(..., on_round=book.round_recorder(course, event_id, year, week, tier))`
feeds it every competitive round; `book.add_event(...)` records tournament totals (the course-library
builder and tests). In the universe, `Season.record_event` records each layout's lowest totals itself (since
d0b0576): every golfer who played every round of a stroke-play event of two rounds or more at that site --
never a missed cut, a match-play event, playoff holes or a one-round event; a total equal to the record does
not take it. The book notes the season it began (`totals_since`): worlds simulated earlier have none for
their earlier seasons, and `tools/reconstruct_totals.py` rebuilds them from an archive's evidence as a
report, exact when the editions carry their format (or the calendar is unchanged since the world's engine).

## Familiarity

Familiarity is with the course, not the tees: rounds on any layout of a course count
(`Course.familiarity_key`).

## Not built yet

- Thousands more courses (home clubs, practice venues, high-school venues).
- Hole names and hand-written notes for every elite course (Georgia National has them).
- Renovations, lengthening and new courses opening over time, as new layouts with their own records.
- Weather-adjusted ratings (the ratings are calm-weather; links defend themselves with wind).
