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
