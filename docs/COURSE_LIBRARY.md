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

## State / province and venue roles (rules 2026-11-08)

Every course records its **state / province or equivalent** (`subdivision`), normalised from its city with
the same table people's birthplaces and residences use (`residence.subdivision`; US and Canadian city names
carry it, the rest are listed). A course whose city is not in the geography (hand-built test courses) has an
honest `None`, shown as "unknown", never a guess. All 520 library courses have one. It is exported with the
course (`world.json` `courses`, the live view) and shown on the course page and the course list.

Each course also records **how it came to be built** (`origin`): `calendar` (the ten-season sizing needed a
course there), `club` (one of the extra clubs added where golf is busiest) or `hand-built`. The course page
calls a course an **event venue** once it has hosted an edition, and otherwise a **local club**, with the
reason given by the venue policy itself (`course_library.venue_role`).

## Courses that host no events

Measured without simulating golf: the reference calendar's (v2) course library, with venues assigned for 30
seasons by `CourseLibrary.venues` (the same assignment worlds use). 502 of the 520 courses host at least one
edition; **18 never do, all municipal**. On the classic calendar (v1) the count is 16 (15 municipal and one
standard course in Singapore).

### Why

1. **Eligibility.** A municipal course's layouts (Regular, Forward) are eligible only for **low-level**
   events (mini events, small-college golf, 54-72 hole amateur events) and **entry-level** events (18-36 hole
   regional amateur events) (`LEVEL_LAYOUTS`).
2. **Selection.** Within the host city an event takes the free course whose layout ranks highest for its
   level. For low-level events a standard course's Club or Forward tees rank ahead of a municipal course; for
   entry-level events a standard course's Forward tees rank ahead of municipal Regular tees.
3. **Succession.** A tournament returns to the course it first used in a city (its home course) whenever
   that course is free. So once a standard course has become an event's home, a municipal course in the same
   city is chosen only when every course it ranks behind is already booked that week.

In the cities concerned, the events that visit are spread over different weeks, so the preferred standard
course is never double-booked and the municipal course is never needed.

### The three courses the roadmap names

| Course | City (state / province) | Class, layouts | Built as | Why it hosts nothing |
|---|---|---|---|---|
| Southport Brook Public Golf Course | Southport (Merseyside) | municipal, Regular | sized for the calendar | Southport's low- and entry-level events (European Amateur Series events on Forward tees, UK & Ireland Pro Circuit and club-professional events on Club tees) prefer Carrick Fields Links and Lark Bend Club (standard, both with Club tees; Carrick Fields also Forward) and keep returning to them. Southport's other events (Britannia Open on Royal Holly Rock, Britannia qualifying, national open) need higher classes. On both calendars. |
| Wren Dunes Golf Club | Newcastle upon Tyne (Tyne and Wear) | municipal, Regular + Forward | extra club | Every Newcastle event (European Amateur Series, UK & Ireland Pro Circuit, club-professional events, the International University event, Britannia regional qualifying, England Amateur) uses Thistle Pines Golf Links (standard, Championship + Club + Forward), which is never booked twice in a week. Reference calendar only (the classic library has no such course). |
| Fjordby Helsinki Golfklub | Helsinki (Uusimaa) | municipal, Regular + Forward | extra club | Helsinki hosts ten series (Finland Open, Finland Amateur Championship, Nordic Pro League events 11 and 22, European Amateur Series events 77-80), each in its own week, and all of them use Strandvik Golf (standard) every year. Granlunda Helsinki Golf, the city's other municipal course, is unused for the same reason. Reference calendar only. |

The other unused courses (reference calendar): seven in Miyazaki (Aobagaoka, Hinokiyama Miyazaki,
Hoshinomori Miyazaki, Momijidai Miyazaki, Sengen, Takigawa Miyazaki, Yamabuki Miyazaki: Miyazaki has many
courses and few events), Bada (Jeju City), East London Farm (East London), Golf Las Cumbres (Mexico City),
Granlunda Helsinki, Lahaina Oaks (Lahaina, Hawaii), Rowanfield Municipal (Atlanta), Sacramento Ridge
(Sacramento), Tampa Ridge Municipal (Tampa). The course page gives each its reason.

### Review: low-level events, succession and selection policy

- **Nothing is broken.** Event identity rests on the home course: a series keeps its venue in a city, its
  records and history build there. Forcing unused courses into rotations would break that, so it is not done.
- **Local clubs still matter.** They are where local golfers play: the regional familiarity baseline
  (docs/FAMILIARITY_AND_AGGRESSION.md) treats courses in a golfer's own state or province as partly known,
  local clubs included. They are also the natural venues for the junior and high-school golf the library
  was planned for (see "Not built yet").
- **Proposal (not implemented; for the owner).** If municipal courses should host some events, the
  smallest change that keeps every established identity: when a *new* entry-level series (18-36 hole
  regional amateur event) first comes to a city -- in a fresh world, or a series added later -- prefer a
  free municipal Regular layout to a standard course's Forward tees for its first edition only; succession
  then keeps it there. Established series keep their homes. This changes fresh worlds' venues (and
  difficulty: municipal Regular plays about as easy as standard Forward), so it would need its own rules
  version and a library rebuild check (`CourseLibrary.validate`).
- **Not proposed:** rotating series between a city's courses, removing unused courses, or making the
  library smaller (the extra clubs give busy cities a choice of venue and absorb same-week clashes).

## Not built yet

- Thousands more courses (home clubs, practice venues, high-school venues).
- Hole names and hand-written notes for every elite course (Georgia National has them).
- Renovations, lengthening and new courses opening over time, as new layouts with their own records.
- Weather-adjusted ratings (the ratings are calm-weather; links defend themselves with wind).
