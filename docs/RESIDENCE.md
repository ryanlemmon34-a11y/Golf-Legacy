# Birthplace and residence

Every person has three pieces of geography, kept in one place (`golfsim/residence.py`, `Season.places`):

| | What | Changes? |
|---|---|---|
| **Nationality** | `Golfer.country` (a coach's or caddie's `.country`) | Never. Moving never changes it; future national-team golf will use it. |
| **Birthplace** | (country, state / province / equivalent), from their hometown | Never. `None` when unknown. |
| **Residence** | where they live now, at the same detail | Only by a recorded, dated move (from, to, reason). |

Each city in the geography has its state, province or equivalent (US and Canadian city names carry it;
the others are listed in `residence._SUBDIVISION`). No city is stored for a person, only the region.

**One record per person.** Golfers, coaches and caddies share one person id; birthplace, residence and
moves are kept only in `Season.places`, never copied onto the golfer or staff objects. A golfer who
becomes a coach keeps the same record, and a later move as a coach is that person's move (no stale golfer
copy can hide it).

## College

A college golfer lives at a **college base**: for the US Division I and small-college tours, a US state
(their own state with chance `HOME_STATE_COLLEGE` when it has college golf, otherwise a draw weighted by
`COLLEGE_STATES`, an uncalibrated spread over 33 states roughly by how much college golf each has); for
the International University tour, their own country if it hosts university golf, otherwise one that does
(three times likelier in their own region). It is a stable draw per golfer and college tour: an
abstraction, **not a named university**.

- Initial world: college golfers already live at their base (they arrived before the world began; no
  dated move is invented).
- Arrivals (each winter's juniors) and transfers between college tours: the base is assigned and, for
  people already in the world, recorded as a move. **College moves cost the golfer nothing**: no cash,
  family money, backers' money or credit is used and nothing can refuse them; the school pays.
- **Graduation sends nobody home automatically.** A graduate decides that winter (no waiting period) like
  any career move below, from wherever their college was.

## Career moves

Each winter (`review_moves`), a full-time professional who has lived where they are for at least
`MIN_STAY` (3) seasons — or anyone whose golfing life changed this winter (turning professional, taking a
job, graduating) — weighs where to live: where they live now, their own country, and the countries of
their tour's events (where they have a legitimate route to play: their membership, unchanged by moving).

- **Value** of living in a country (event-value points, `move_value`): the travel to their tour's events
  over `STAY_YEARS` (3) seasons from there, plus the cost of moving there (`MOVE_COST` $6,000, paid from
  their own funds; a move they cannot pay for is not made and is counted in `move_blocked`), both divided
  by what a dollar means to them (`finance.money_unit`: a broke player feels every flight, a wealthy one
  hardly notices); minus the pull of their own country, `HOME_PULL` (60) × (1.6 − 1.2 × adaptability/100)
  points when they live abroad. Adaptability is an existing personality trait.
- **Odds** (`move_odds`): a smooth chance that grows with how much more the best country is worth than
  staying (an even chance at `MOVE_MARGIN` 15 points, scale 8). Nothing is scripted: moving, staying and
  returning are all possible, none certain.
- **Returning home**: a successful expatriate's travel savings matter little against the pull of home,
  so they may return — not automatically, and only after `MIN_STAY` seasons (no back-and-forth).
- A West African professional on the Southern Africa Tour (Nigeria in this world; Ghana is not one of its
  countries) saves about $6,000 a season of travel by living in South Africa: likely to move if broke and
  adaptable, unlikely if wealthy or strongly attached to home (`tests/test_residence.py`).
- Part-time professionals, club professionals and amateurs living at home do not make career moves (a
  job, a club or a family home keeps them there) unless their life changed this winter.

**Staff moves** (`staff_moves`): a caddie may move to where the player whose bag they carry lives
(`CADDIE_FOLLOWS` 0.35 a winter); a coach to where at least 60% of two or more players live
(`COACH_FOLLOWS` 0.25, after `MIN_STAY`). Staff have no household finances in the model, so their moves
cost nothing.

No immigration, tax or property systems. **Moving never grants a tour card, a membership or a
qualifying right.**

## What residence changes (the audit)

Every use of a person's country, region or hometown was reviewed one by one:

| Use | Follows | Where |
|---|---|---|
| Travel cost of an event (home / region / abroad) | residence | `finance.event_cost(..., home)` via `Season.trip_cost`, `regular_entries` fees, the payment in `record_event`, `tour_trip_cost` |
| Event appeal: home and regional bonus, part-timers' local events | residence | `Season.base_value` |
| A club professional's drive to a section event | residence (hometown while they still live where they were born) | `Season.drive` |
| Travel fatigue | residence | `record_event` → `load` |
| Which open qualifier they choose to enter, and the international final qualifying site (England / Japan) | residence (open to all: proximity decides) | sectionals, USA Open and Britannia local and final qualifying |
| The Challenger tour that is a conditional Premier member's alternative | residence | `Season.bar` |
| Coaches and caddies: who is near, who scouts whom, same-country bonus, unmet demand | residence of both | `staff.start_of_season`, `staff.end_of_season` |
| Entry eligibility (`Season.eligible`), national opens' home players, amateur invitations | **nationality** | unchanged |
| National and elite amateur championships, their regions | **nationality** | unchanged |
| Q-School entrant pools (a route to a card) | **nationality** | unchanged |
| Tour memberships, cards, promotions, home tours given on career changes | **nationality** | unchanged |
| Masters international invitations, qualification `Person.country` | **nationality** | unchanged |
| Course style (the course's city) | the course | unrelated |

Legacy people whose residence is unknown are priced from their nationality (the only honest default;
they are still exported as unknown).

**Caches.** Every cache whose value depends on where a golfer lives is keyed by the country of residence:
the weekly fees (`fk`) and appeal (`bk`) caches in `regular_entries`, the monthly plan's option cache
(`plan_block`, keyed by nationality *and* residence), and `tour_trip_cost` (keyed by the country travelled
from). Golfers of one nationality living in different places never share an entry, whatever the order
they are processed in (tested through real weeks of play).

## History

- Each move is a dated fact `(year, week, from, to, reason)` in `Season.places.moves`, in the golfer's
  (and staff member's) history, and in that winter's `move_log`.
- The archive's people table carries nationality, birthplace, current residence, the first residence (with
  when, and a note such as "at college") and every move; each season's careers rows carry where the golfer
  lived that season; each season file lists that winter's moves. `Archive.residence_at(pid, year, week)`
  answers from the dated moves (never today's address for an earlier season); `Archive.geography(pid)`
  gives the whole record. The observer's profile page shows nationality, birthplace, current home and the
  residence history.
- Moves happen inside the season-end step, so they are part of the same committed generation as the rest
  of the season: an interrupted save, recovery and replay neither lose nor duplicate them (tested).

## Compatibility

Saves from before residence load with every existing person's geography **unknown** (`Places.legacy`):
no birthplace, residence or moves are invented for them; they travel from their nationality for costs. New
people (juniors, new professionals, new staff) get full records. Ledgers gain a `moving` line (0 for old
ledgers). The long test uses a fresh world.
