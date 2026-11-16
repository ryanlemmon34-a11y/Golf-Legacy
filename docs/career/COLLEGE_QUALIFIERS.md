# Calendar v3: the US college championship's qualifiers

Calendar `v3` (`schedule.V3`) is `v2` with the US college championship reached through four early-spring
qualifiers. **v1 and v2 are unchanged** (schedules, rules, goldens); a world's calendar is rebuilt from its own version
when it loads, so no existing world changes. `schedule.NEW_WORLD = 'v3'` is the calendar the app offers for new
worlds; `schedule.DEFAULT` (a world created through the API without naming a calendar) stays `v2`, so every
existing test and tool keeps its world.

## Events

| week | event | field |
|---|---|---|
| 10, 11, 12, 13 | College Championship Qualifier 1-4 (`COLLEGE_QUALIFIER_1..4`), 54 holes, no cut | every US college golfer not yet qualified, in heats |
| 17 | Conference championships (unchanged) | as v2 |
| 20 | Small College National Championship (unchanged) | small-college golfers, as v2 |
| 22 | College National Championship | the qualified golfers who can play (at most 156 = 4 x 39) |
| 28 | World University Championship (unchanged; CO_INTL) | as v2 |

No regionals in v3.

## Who may enter

Every golfer on a US college tour -- `CO_US_D1` and `CO_US_SMALL` -- whatever their nationality, not yet qualified
this season, and free that week (not injured, retired or committed to another event; those are recorded in
`stage_log[(year, qualifier, 'unavailable')]` and may enter a later qualifier). `CO_INTL` never. A player under
career control enters by the period's policy for rule-selected places (accept / decline), like any selected field.
Nobody is excluded by ranking: every entrant gets a heat.

## Heats and places

* Heats of at most `college_heat_size` (156): `H = ceil(entrants / 156)`, at most `college_qualifier_max_heats` (10);
  beyond 1,560 entrants every heat grows instead of anyone being left out.
* Entrants are ranked (amateur ranking, then observed form, then id) and dealt serpentine (1..H, H..1, ...), so each
  heat has the same spread of strength.
* Each qualifier awards `college_qualifier_places` (39) places, shared among its heats in proportion to their fields
  (largest remainder; equal remainders to the earlier heat). Measured pool: about 720 US college golfers at steady
  state (seed 11; junior classes do not depend on world scale), i.e. 5 heats of 144 with 8/8/8/8/7 places.
* Within a heat the best finishers take its places. A tie at the last place: countback (the final round, then the
  round before, ...), then id. Withdrawals and disqualifications never qualify. A heat with fewer finishers than
  places: the places lapse (they are not passed to another heat or qualifier).
* A qualified golfer does not enter the later qualifiers; the unqualified may try again.
* How each golfer qualified is recorded: `entry_routes[(year, 'COLLEGE_NATIONAL_CHAMPIONSHIP')][gid] =
  'QUALIFIER k, HEAT h (pos)'` (`T` for a tie); `Season.college_qualified(year)` gives `{gid: (k, h, finish)}`.
* At the championship a qualified golfer who cannot play withdraws (reason recorded in `nationals_withdrawn`); the
  place is not passed down.

## The champion's places

* Next season's Tour Masters for the college national champion (route M16, amateurs) -- as v2.
* The same season's USA Open for the college national champion if still an amateur (route `U2C`, after the USGA's 2026
  exemption list): **on in calendar v3** (`college_champion_usa_open = True`, enabled 2026-11-15 on the final-scope
  confirmation; the spec field defaults to False, so v1/v2 have no such route). The championship (week 22) is decided before the USA Open's field (final qualifying week 24, the Open
  week 25), and a golfer's status changes only in the winter.

## Read models

`career.view()['opportunities']` lists each upcoming qualifier with target `COLLEGE_NATIONAL_CHAMPIONSHIP`, route code
`COLLEGE_QUALIFYING`, condition "finish in your heat's share of the qualifier's 39 places", and status
`already_qualified` / `needs_result` / `not_eligible`. `event_labels.target` maps each qualifier to the championship.

## Tests

`tests/test_college_qualifiers.py`: v1/v2 unchanged; v3 calendar valid; heats, place shares, ties by countback,
withdrawals, short heats, no re-entry; a v3 season played through week 23 (unique qualification, US college tours
only, nationality-independent, championship field = qualified minus withdrawals, recorded routes, small-college
championship still played); the v3 golden digest (re-baselined for course fit, docs/career/COURSE_FIT.md); the USA Open route on in v3 (timing,
amateur status, no invented place) and absent from v2.
