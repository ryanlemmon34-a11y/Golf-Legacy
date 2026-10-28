# Golf Legacy — Each Circuit's Flagship and How to Get In

Every tour, college circuit, amateur series and club-professional circuit has one event that matters
most at its level. Where the calendar already had one (the Premier Tour Finals, the college national
championships, the USA Amateur, the Club Professional Championship) it is kept; the others are each
circuit's **season-ending championship** (`category = 'circuit_championship'`, `calendar.CIRCUIT_FLAGSHIPS`),
played in the circuit's last weeks, in its main country when that country is in season. Flagships are
aspirational, not the only way to compete: the ordinary season around them is unchanged.

All fields are chosen by facts already recorded (results, money lists, rankings, membership,
qualifying), each entrant's **route is recorded** (`Season.entry_routes`, archived with the event), and the
same affordability rule as every other entry applies: a golfer who cannot pay the trip declines (recorded
in `Season.declined`) and the next on the list takes the place.

## Inventory

| Circuit | Flagship | Week | Field | Holes | How the field is made |
|---|---|---|---|---|---|
| Premier Tour Americas | Premier Tour Finals | 45 | 30 | 72 | Top 30 on the Premier points list (existing) |
| Premier Tour Europe | Desert Tour Championship | 47 | 50 | 72 | Members (existing) |
| Premier Tour Asia-Pacific | Australia Open | 49 | 156 | 72 | Premier event, open to members first (existing) |
| Five Challenger tours | *Tour* Championship | 41–47 | 70 | 72, no cut | Past champions (3 years), then the tour's money list |
| Six Regional tours | *Tour* Championship | 43–47 | 60 | 72, no cut | Past champions (3 years), then the tour's money list |
| Sixteen mini tours | *Tour* Championship | 38–47 | 50 | 54 | Past champions (3 years), then the circuit's order of merit — **everyone who played it**, member or not (open circuits) |
| US College Division I | College National Championship | 21 | 156 | 72 | Conference championships → regionals → nationals (existing) |
| US Small College | Small College National Championship | 20 | 120 | 72 | Amateur ranking among members (existing) |
| International University | World University Championship | 28 | 96 | 72 | Amateur ranking among members (existing) |
| North American amateurs | **USA Amateur** | 33 | 156 | 36 + match play | Exempt players, then **open qualifying** (below) |
| Britain & Ireland amateurs | Britannia Amateur | 23 | 144 | 36 + match play | Amateur ranking (existing) |
| Regional amateurs | European, Asia-Pacific, Latin America, Africa Amateur Championships | various | 96–144 | 72 | Amateur ranking in the region (existing) |
| Every country with golf | National amateur championship | its summer | 96–120 | 54–72 | Home amateurs, then the region's (existing) |
| Six amateur series | *Series* Championship | 43–48 | 72 | 54 | Past champions, then the **amateur ranking** among the series' amateurs (no prize money involved) |
| North American club pros | Club Professional Championship | 16 | 156 | 72 | US sectional qualifying (existing) |
| Five other club-pro circuits | *Region* Club Professional Championship | 43–48 | 60 | 36 (Mon–Tue) | Past champions, then the circuit's order of merit (prize money in its section events) |

## The rules, field by field

- **Eligibility.** Members of the tour; for open mini circuits, members and any professional recorded
  as starting one of its events this season (`Season.circuit_players`), whether or not they won money;
  for amateur series, exactly the amateurs its ordinary events take (`Season.series_amateur`: members,
  amateurs from its countries, and college golfers studying there, so a Swede at a US college is a North
  American amateur for the championship too); for club-pro circuits, the region's club professionals.
- **Order of merit and cut-off.** As it stood after the previous week's events. Professional circuits rank
  by prize money on the circuit; amateur series by amateur ranking (amateur standing never depends on prize
  money).
- **Ties at the cut-off.** Money lists break ties by world ranking, then person id; amateur lists by
  observed form (strokes against the field), then id. No coin tosses, and the order never depends on how
  the population happens to be listed.
- **Exemptions and their length.** A champion is exempt into the next three editions while still on the
  circuit (`Season.CHAMPION_YEARS`).
- **Duplicates.** A champion who is also high on the order of merit takes one place; the next name on the
  list fills the field.
- **Alternates.** Anyone injured, already committed that week, or unable to pay is passed over for the next
  on the list.
- **Rewards.** A larger purse that counts on the money list (so it can decide promotion), prestige, a
  recorded title. The championship needs no special card rules: the existing promotion rules read the
  final money list.
- **No circular rules.** Every flagship can be reached from an ordinary season that is itself open: open
  mini circuits, open amateur series events, club-pro section events and the USA Amateur's open
  qualifying. Rankings are earned there.

## The USA Amateur: exemptions, then open qualifying

- **Exempt** (deduplicated, in order): the last three champions and last year's runner-up who are still
  amateurs, then the top 64 of the amateur ranking (`Season.USA_AMATEUR_EXEMPT`).
- **USA Amateur Qualifying** (week 30, 36 holes in one day at eight sites, 78 per site): open to any
  amateur who is not exempt and meets the **entry standard** of three events played this season — a
  record of play, not a ranking, so an unranked newcomer can enter — playing North American amateur golf
  (`series_amateur`, college students there included) or travelling from abroad with a top-300 amateur
  ranking; a fair draw decides entries when oversubscribed.
- **Places.** The rest of the 156 go to qualifiers, exactly: the places are split between the sites in
  proportion to their entrants by largest remainders, and equal remainders (eight equal sites sharing 91
  or 92 places) go by a fair draw seeded by the world, year and site, never by the order the sites are
  listed in (`season.allocate_places`). At each site the places go to its best finishers; ties for the last
  place go by the recorded finishing order (countback). A finisher who has become exempt since qualifying
  does not use a place; one who cannot take it up (busy, injured, unable to pay: recorded) is replaced by
  the next finisher at that site (route `QUALIFYING SITE n (alternate)`); places a site cannot fill go to
  the other sites by the same rule.

## Evidence and assumptions

Evidence-backed patterns (from the real circuits used as references): season-ending championships for the
top of a money list (Korn Ferry Tour Championship), exemptions for past champions, open qualifying with an
entry standard for the national amateur (U.S. Amateur), regional club-professional series with their own
championship (PGA of GB&I Open Series and PGA Professional Championship).

Tunable design assumptions: field sizes (70 / 60 / 50 / 72 / 60), the purse multiples and prestige
bonuses in `CIRCUIT_FLAGSHIPS`, three years of champion exemptions, the USA Amateur's 64 exemptions and
three-event entry standard, and the eight-week window for playing in the main country.
