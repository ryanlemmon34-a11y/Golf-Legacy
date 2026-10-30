# Seasons without a start: the explanation fixed, and the full-time amateur rate investigated

Roadmap v14: the Test1 10.29 review found the annual "no starts" label too definite -- all 16 full-time
zero-start cases labelled "chose not to play" had unaffordable or full-field weeks, and all 22 labelled "no
eligible event" had unaffordable weeks. Named examples: Kaito Ogawa (2035, Challenger Japan: 28 unaffordable
weeks, two full-field weeks, work, training and declines) and Agustin Sanchez (full-time amateur: 11 unaffordable
weeks, 41 with no suitable event). Neither is to be forced into a tournament.

## The fix (implemented)

- The old label came from thresholds on monthly planning flags. The explanation now comes from the season's
  weekly evidence (`golfsim/access.py`), which every season already records for every golfer and the archive
  keeps (`careers[...]['access']`): each week is classified once when played -- played; injured; **not
  admitted** (every acceptable field full, or not picked for the college lineup); **no suitable event**; **not
  eligible**; **unaffordable** (could not afford any event); **declined**; **trained, rested or worked** (the last
  two only when an affordable event they could enter existed that week).
- A zero-start season is explained by every contributing cause with its weeks, out of the weeks recorded, and
  classified as kept out by barriers, chose not to play (choices only), barriers and choices (mixed: never called
  voluntary) or mostly injured. Ogawa's season reads "barriers and choices: barriers 30 (not admitted 2,
  unaffordable 28); choices 22 ..."; Sanchez's "kept out by barriers: barriers 52 (no suitable event 41,
  unaffordable 11)".
- The season page ("the season as it was") shows the week-by-week ledger for every archived season -- older
  seasons included, read from the weeks they recorded -- with where each barrier was decided (entry, calendar,
  eligibility, money, the golfer's own choice or plan), and the weeks they were shut out or played an
  alternative with the event they wanted. The label an older engine recorded is shown beside it, marked as
  such. Nothing is reconstructed: the weekly counts are what was recorded.

## The full-time amateur rate (investigated, no change made)

`tools/zero_start_audit.py` (read-only) on the 50-season copy (engine 7334ffe; seasons 2066-2076) -- the Test1
archive could not be downloaded here (Google Drive is not reachable from this environment):

| Cohort | Person-seasons | No starts | Share |
|---|---|---|---|
| full-time amateur | 5,087 | 384 | 7.55 % (Test1: 8.8 %) |
| full-time Mini | 11,950 | 112 | 0.94 % |
| full-time Challenger | 9,125 | 36 | 0.39 % |
| college / full-time Premier | 12,347 / 3,211 | 0 / 0 | 0 % |

Every one of the 384 full-time amateur zero-start seasons was **kept out only by barriers**: 72 % of their weeks
"could not afford any event", 28 % "no suitable event scheduled"; none was a choice. By where they lived:
Europe 10.5 %, Asia 10.2 %, Africa 9.7 % against North America 1.0 %, Latin America 2.8 %, Oceania 0.8 %.

Reading: events they were eligible for existed, but not within their means, and the gap is regional -- the
large amateur circuits (Europe, Asia, Africa) cost more to travel than the denser North American and Oceania
ones, for golfers with no prize income (net 0: no trips, no prizes). This is an observation, not a defect
proven: the next step is to compare, per region, the cheapest eligible trip with a full-time amateur's funds
and support (family backing, school), which the archive does not keep per golfer (the live save does), before
proposing anything -- local event density, regional amateur entry costs, or support levels. No starts are
forced and no money is added.

Run it on any world: `python tools/zero_start_audit.py <world folder> --years 2040-2052 --out report.md`.

## By region and circuit, with affordability evidence (roadmap v14, build v15 -- investigated, no change made)

`python tools/zero_start_audit.py <world> --years 2066-2076 --save` on a disposable copy of the 50-season world
(engine 7334ffe; the original was only read). The archive gives every week's cause; `--save` reads the copy's
committed save (never written) for what the archive does not keep: each full-time amateur's funds, last season's
costs and family support, by the engine's own rules (`Season.spendable`, `Season.trip_cost`).

**Weeks of the zero-start seasons, by home region and circuit** (share of the weeks those seasons recorded):

| Region | Circuit | Seasons | No starts | Share | Injured | Not admitted | No suitable event | Not eligible | Unaffordable | Choices |
|---|---|---|---|---|---|---|---|---|---|---|
| Europe | AM_EUROPE | 1,854 | 195 | 10.5% | 0% | 0% | 29% | 0% | 71% | 0% |
| Asia | AM_ASIA | 1,428 | 145 | 10.2% | 0% | 0% | 17% | 0% | 83% | 0% |
| Africa | AM_AFRICA | 257 | 25 | 9.7% | 0% | 0% | 65% | 0% | 35% | 0% |
| Latin America | AM_LATAM | 246 | 7 | 2.8% | 0% | 0% | 79% | 0% | 21% | 0% |
| North America | AM_NORTH_AMERICA | 811 | 8 | 1.0% | 0% | 0% | 0% | 0% | 100% | 0% |
| Oceania | AM_OCEANIA | 482 | 4 | 0.8% | 0% | 0% | 65% | 0% | 35% | 0% |

**Every full-time amateur season's weeks** (those who played too): Europe played 25 % of weeks (not admitted
9 %, no suitable event 29 %, unaffordable 12 %, choices 25 %); Asia 24 % (not admitted 30 %, no suitable
event 17 %, unaffordable 11 %); North America 17 % (**not admitted 69 %**: full fields; unaffordable 2 %);
Oceania 16 %, Africa 22 %, Latin America 21 % (**no suitable event 63-74 %**: sparse calendars; unaffordable
1-5 %). Injuries are 0-1 % everywhere.

**Affordability at the start of 2077** (the copy's save; full-time amateurs, college golfers aside):

| Region | Last season | Golfers | Median spendable | Cannot afford their cheapest own-circuit trip | No family support left | In debt | Median event costs last season |
|---|---|---|---|---|---|---|---|
| Europe | no starts | 8 | $101 | 8 (100 %) | 8 (100 %) | 8 (100 %) | — |
| Europe | played | 117 | $13,124 | 12 (10 %) | 55 (47 %) | 39 (33 %) | $6,720 |
| Asia | no starts | 2 | $253 | 2 (100 %) | 2 (100 %) | 2 (100 %) | — |
| Asia | played | 93 | $13,482 | 6 (6 %) | 45 (48 %) | 30 (32 %) | $6,405 |
| Africa | played | 27 | $18,886 | 2 (7 %) | 11 (41 %) | 4 (15 %) | $5,705 |
| Latin America | played | 15 | $23,483 | 0 | 2 (13 %) | 2 (13 %) | $4,795 |
| North America | played | 58 | $21,924 | 1 (2 %) | 13 (22 %) | 3 (5 %) | $3,622 |
| Oceania | no starts | 1 | $282 | 1 (100 %) | 1 (100 %) | 1 (100 %) | — |
| Oceania | played | 32 | $15,765 | 0 | 12 (38 %) | 2 (6 %) | $3,430 |

The cheapest trip on their own circuit is $350 (a home-country amateur event) in every region.

**Persistence** (2066-2076): of the 384 zero-start full-time amateur seasons, 162 (42 %) were the second or
later in a row; the season after, 205 became part-time amateurs (working), 148 had another zero-start full-time
season, 29 left the records, 2 turned professional. Median age 23 (20-26).

**What the evidence says**

1. *Affordability* (Europe, Asia): a full-time amateur has no living costs and **no income at all** (no prize
   money, no work): every trip is paid from a family pot granted once at 18 (40 % get none) and a credit line.
   Europe's and Asia's circuits cost almost twice as much a season as North America's or Oceania's ($6.4-6.7k
   against $3.4-3.6k: their events are spread across more countries, and travel costs 1.3x within the region,
   1.8x abroad), so the pot runs out sooner -- 47-48 % of those still playing have none left and a third are in
   debt, against 22 % and 5 % in North America. Every golfer who played nothing in 2076 starts 2077 in debt, with
   no family money, unable to afford even a $350 home event.
2. *Unavailable events* (Africa, Latin America, Oceania): most of their weeks have no suitable event (63-74 %);
   zero-start seasons there are rarer because the events that exist are cheap and nearby.
3. *Admission* (North America): full fields are the main barrier (69 % of weeks), but almost every golfer gets
   some starts; it is not a zero-start cause.
4. *Injuries* and *genuine choices* play no part in full-time amateur zero-start seasons (0 % of their weeks).
5. *The career decision lags*: the move to working (part-time amateur) usually happens, but only after a whole
   season without a start, and 39 % stay full-time for another empty season.

**Recommendations (for your decision; none implemented, no starts forced, no money added)**

- **Career decision first** (believable careers, no new money): let the full-time / working decision see the
  same evidence the week ledger records -- a full-time amateur who cannot afford their cheapest event (no family
  money left, at the credit limit) should weigh taking work then (in the monthly plan), not only at the season's
  end. Expected effect: most stuck seasons become part-time seasons with local starts; it changes outcomes, so a
  new engine version for new worlds (or a copy you choose).
- **Then, if wanted, the cost of amateur golf by region**: either more home-country amateur events on the
  European, Asian and African circuits (calendar density; the reference calendar is the place), or modest
  national-federation support for amateurs' entry travel within their own country. Both change the economy and
  are your call; the tables above are the baseline to measure them against.
- **Not recommended**: forcing entries, waiving costs or topping up funds to remove zero-start seasons.
