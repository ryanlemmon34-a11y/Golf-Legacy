# Population over ten seasons (seed 2027)

One world, every shot simulated, after club-paid club-pro events, backers, the new-professional flow and realistic stop-competing rates (commits 82a7689..acc58cf). Generated with a scratch diagnostic over `Season.run_year`; 4-core container.

| Season | Full-time Premier / Challenger / Regional / Mini | Part-time pros | Active golfers | New pros (juniors turned pro + arrivals) | Mini: median starts, 10+ wks unaffordable, backed | Avg field: Challenger / Regional / Mini | Seconds |
|---|---|---|---|---|---|---|---|
| 2027 | 300 / 940 / 515 / 1505 | 237 | 6783 | 129 + 458 | 21, 3%, 34% | 145 / 133 / 80 | 100 |
| 2028 | 286 / 942 / 393 / 1581 | 420 | 7062 | 141 + 462 | 21, 9%, 37% | 144 / 126 / 82 | 109 |
| 2029 | 290 / 915 / 387 / 1493 | 611 | 7267 | 141 + 399 | 22, 16%, 46% | 144 / 123 / 78 | 123 |
| 2030 | 293 / 870 / 386 / 1398 | 780 | 7540 | 135 + 450 | 21, 18%, 46% | 143 / 119 / 75 | 124 |
| 2031 | 296 / 887 / 375 / 1346 | 927 | 7741 | 112 + 443 | 21, 22%, 51% | 143 / 119 / 74 | 125 |
| 2032 | 293 / 871 / 386 / 1335 | 1036 | 7911 | 128 + 422 | 20, 22%, 50% | 143 / 118 / 74 | 127 |
| 2033 | 294 / 875 / 369 / 1282 | 1134 | 8062 | 146 + 464 | 20, 23%, 52% | 143 / 118 / 75 | 133 |
| 2034 | 290 / 867 / 341 / 1309 | 1240 | 8210 | 150 + 438 | 20, 21%, 55% | 143 / 117 / 76 | 131 |
| 2035 | 289 / 856 / 371 / 1335 | 1303 | 8350 | 138 + 441 | 20, 21%, 53% | 144 / 120 / 77 | 145 |
| 2036 | 292 / 859 / 370 / 1331 | 1359 | 8478 | 140 + 439 | 19, 22%, 53% | 143 / 119 / 78 | 148 |

## Findings

- **Tours hold steady.** Premier ~290, Challenger ~860, Regional ~370 (from 515), Mini ~1,300 (from 1,505)
  after the first two seasons. About 440 new professionals arrive a year from outside the amateur game, plus
  ~140 juniors who turn pro.
- **Mini-tour money.** Median starts 19-22; 16-23% of full-time mini pros cannot afford any event for 10+
  weeks (53% by season three before backers); about half are backed.
- **The active world still grows, more slowly:** 6,783 -> 8,478 in ten seasons, +128 a year by the end and
  falling (part-time amateurs and pros, club pros). Before the stop-competing change: +400 a year.
- **Season time grows faster than the population:** 100 s -> 148 s while professional starts stay flat
  (~72,000). Retired golfers stay in the world list (393 -> 5,312, ~500 more a year) and every weekly loop
  walks past them; by season 100 that would be ~50,000. Next: keep an active list for the weekly work.
