# Golf Legacy — Competition Access

The aim: abundant ordinary opportunities at every level, scarce prestigious ones, and real alternatives
when a golfer misses the field they wanted. Golfers can still fail, decline events, work, get hurt or
retire; they should not fail because the world forgot to give them a pathway.

## Every week is accounted for

Each active golfer's week gets exactly one outcome (`season.ACCESS`, recorded in `Season.week_access`
and archived per golfer-season):

| Outcome | Meaning |
|---|---|
| played: first choice / alternative / selected field | played the event they wanted most; or another after missing it; or a field chosen by the event (major, invitation, qualifier, college post-season, circuit championship) |
| injured | |
| shut out: every acceptable field full | wanted to play, tried every event worth playing to them, all full |
| not selected for the college lineup | the same for a college golfer whose college event was full |
| no suitable event scheduled | nothing at their level in their region that week |
| not eligible for the events scheduled | events at their level existed, none open to them |
| could not afford any event | |
| declined the events on offer | planned to play, but nothing that week was worth it to them |
| chose to train / rest / work | the monthly plan's choice |

Shut-out weeks are also counted **while behind the pace of their intended schedule** (a real shortage)
separately from extra starts wanted by golfers already on pace, and the longest run of denied weeks is
kept. Each denied or alternative week is logged with the event wanted and the event played
(`Season.access_log`), and every entrant's route into every field — with their status at entry — is kept
with the event (`Season.event_routes`, `Season.entry_routes`; archive `Archive.results()` gives the route
per start, `Archive.access()` the season). `tools/access_audit.py` reports all of it by status, circuit,
region and career stage, with a capacity table (places offered against starts intended, region by level).
See `reports/access/`.

## Intended schedules (owner)

`Season.target_events`: college golfers play a lot (24 starts: college events plus amateur events around
them); full-time amateurs a little less (16); part-time amateurs 8 around a job; club professionals have
plenty of local events and choose about 12 around their job; professionals 19–27 by stamina (Premier
members pick their spots). These shape the monthly plan; nobody is forced to a quota.

## Major weeks

A major owns its week **at the top level only**: no Premier Tour event is scheduled against it, but the
Challenger, Regional and mini tours, college, amateur and club-professional golf go on. Golfers in the
major cannot play anything else that week (fields chosen by events are committed first and no golfer is
ever placed in two events on the same days); the others play where the calendar has something for them.

## Premier Tour playing rights

The marquee calendar stays at 36 Premier events and four majors. Its capacity: 29 weeks with a Premier
event, 22 of them with only one in the world (144–156 places), 5,108 places a year — for 300 members who
would each like about 21 starts (6,300). It cannot promise everyone a full season, so rights say who gets
what (`Season.premier_rights`, fixed on 1 January from recorded facts, kept with each season's history):

| Rights | Who | Priority in Premier events |
|---|---|---|
| exempt | won a Premier event this season or last, or a major in the last five | first |
| full | top 125 on last season's Premier money list (`FULL_STATUS`) | next |
| graduate | earned the card on a Challenger tour or at a Q-School | then, reshuffled by this season's Premier money |
| conditional | kept the card from lower on the money list | last, reshuffled by this season's Premier money |

Within a class, members of the event's own circuit go first. Full status is sized so every fully exempt
member fits the smallest ordinary Premier field (144) in the weeks with a single Premier event; in the
first season (no money list yet) members are seeded by world ranking. Measured in season one: full
members a median 23 starts (99% reach three-quarters of their intended schedule, almost never shut out);
conditional members a median 16 and uncertain access, as intended.

**Alternatives.** Conditional and graduate members judge events against their home Challenger tour's
level (uncertain access makes a Challenger event a real alternative), so when the Premier field is full
they play a Challenger event that week. **Residents are protected:** Premier visitors take at most
`PREMIER_VISITOR_SHARE` (10%) of a Challenger event's places alongside the members (by world ranking);
beyond that they cannot displace residents. In Regional and mini events visitors rank behind the members.
National opens stay open to all professionals.

## Ordinary competition below the Premier Tour

The calendar was sized from the capacity audit (`reports/access/BASELINE.md`): where members could not
reach their intended schedules, events were added at a realistic field size rather than letting fields
grow without limit.

- **Challenger tours** 22–26 events each, **Regional tours** 14–26 (as their real counterparts run).
- **Mini tours** run most weeks in their seasons, the US circuits two events a week (they are paid for by
  entry fees, so money, not the calendar, is what limits most mini-tour players).
- **Local golf in every golfing country.** Amateur series and the new club-professional circuits play in
  every golfing country of their region with events in proportion to the size of its golf scene (its
  starting nation pool) and a floor, so no country depends on one national championship
  (`calendar.local_allocation`). Club professionals' events are one-day section events and pro-ams on
  Mondays and Tuesdays. Club pros are far fewer than amateurs (about one per unit of nation pool, ~350
  in the starting world), so their circuits hold fewer, bigger events: 0.3 per unit of pool, in the
  countries with a club-pro scene (pool 3 or more), and at least 16 a season in every region; club pros
  from smaller golf countries cross a border in their region to play (a section event over the border
  counts as a drive, not a flight). About 150 events a season, against ~470 when every country had
  its own: fields of a few dozen club pros rather than a dozen, so a win means beating a real field,
  while every club pro still has more events within reach than the ~12 they want to play.
- **College.** More college events, and college golfers can play amateur events around their college
  schedule (in the USA, the country they study in). Not making a lineup is recorded as such
  (`not selected for the college lineup`), separately from a shortage of golf.
- **Open amateur events** take up to 1.5× their usual field when more want to play (club, county and
  regional amateur golf), with lineups rotating by starts so newcomers get in.

The course library grows with the calendar (520 courses; the calendar needs 443, the rest give the
busiest cities a choice of venue).

## Flagships

See `docs/CIRCUIT_FLAGSHIPS.md`: every circuit's flagship and how its field is made.

## Limits and assumptions

- Calendar density follows the **starting** nation pools; when nations evolve (roadmap M5) local
  calendars should follow them.
- Tunable: the intended schedules, `FULL_STATUS`, `PREMIER_VISITOR_SHARE`, the local-golf rates and floors,
  event counts and field sizes, the 1.5× amateur expansion.
- The monthly plan does not learn from being shut out: a golfer repeatedly denied keeps planning to play
  and trains instead that week. Most such weeks are extra starts by golfers already on pace (see the audit).
