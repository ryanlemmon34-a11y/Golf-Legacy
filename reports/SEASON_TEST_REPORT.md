# Golf Legacy — Multi-Season World Test

5 full seasons (2027–2031) of the whole world: 6,178 golfers, 3,234 events, **16,251,053 holes, every shot simulated**, in 7.0 minutes (83 s per season on 4 cores). Attributes are held fixed, so every change below comes from the season system (entries, results, cards, rankings, prestige), not from players improving or aging.

## 1. Does the world sort players by ability?

Average overall rating at each level at the start of each season (the starting world was sorted by a noisy reputation; after that, only results move players), and how well the world ranking follows true ability (Spearman correlation, top 500 pros by overall).

| Season | Premier Tour | Challenger | Regional | Mini tour | College | Amateur | Ranking vs ability | Top-50 players on the Premier Tour |
|---|---|---|---|---|---|---|---|---|
| 2027 | 74.3 (300) | 65.8 (938) | 57.0 (516) | 54.1 (1594) | 46.7 (877) | 36.8 (1623) | 0.61 | 50 of 50 |
| 2028 | 74.1 (293) | 65.6 (953) | 56.7 (496) | 54.3 (1606) | 46.7 (877) | 36.8 (1623) | 0.65 | 50 of 50 |
| 2029 | 73.9 (301) | 65.7 (957) | 56.2 (485) | 54.3 (1605) | 46.7 (877) | 36.8 (1623) | 0.67 | 50 of 50 |
| 2030 | 74.1 (292) | 65.6 (964) | 56.1 (478) | 54.4 (1614) | 46.7 (877) | 36.8 (1623) | 0.66 | 50 of 50 |
| 2031 | 74.0 (296) | 65.7 (966) | 56.0 (470) | 54.4 (1616) | 46.7 (877) | 36.8 (1623) | 0.69 | 50 of 50 |

**Tour cards each off-season** (players moving between levels):

| After season | Premier → Challenger | Challenger → Premier | Challenger → lower | Lower → Challenger | Regional ↔ Mini |
|---|---|---|---|---|---|
| 2027 | 98 | 88 | 116 | 121 | 61 |
| 2028 | 85 | 88 | 108 | 115 | 68 |
| 2029 | 93 | 81 | 116 | 111 | 69 |
| 2030 | 88 | 91 | 109 | 114 | 73 |
| 2031 | 90 | 89 | 119 | 110 | 74 |

Examples of players earning Premier Tour cards after the last season: Chris Rutledge (USA, 76) — top 25 on Challenger Tour Americas; Zach Parker (USA, 76) — top 25 on Challenger Tour Americas; Harrison Easley (USA, 75) — top 25 on Challenger Tour Americas; Sander Smits (Netherlands, 74) — top 20 on Challenger Tour Europe; Jared Murphy (USA, 74) — top 25 on Challenger Tour Americas; Tom Powell (England, 74) — top 20 on Challenger Tour Europe.

## 2. Who wins

| Level | Events | Different winners | Winners' average overall | Field average | Wins by the level's 10 best players | Lowest-rated winner |
|---|---|---|---|---|---|---|
| Major | 20 | 16 | 83.8 | 75.0 | 65% | 73 (USA Open 2027) |
| Premier | 180 | 110 | 79.2 | 74.4 | 32% | 68 (Desert Tour Championship 2029) |
| Challenger | 450 | 346 | 69.6 | 66.6 | 0% | 59 (Japan Golf Tour Event 2 2031) |
| Regional | 390 | 313 | 66.9 | 60.3 | 0% | 50 (China Open 2029) |
| Mini | 839 | 575 | 61.5 | 57.0 | 0% | 43 (Southeast Asia Pro Series Event 10 2028) |
| College | 485 | 279 | 54.4 | 49.7 | 7% | 31 (US Small College Golf Event 9 2031) |
| Amateur | 780 | 448 | 53.2 | 43.5 | 6% | 30 (Peru Amateur Championship 2028) |

**Most wins in a season (Premier Tour and majors):**

- 2027: Duncan Sinclair (Scotland, 86) 3, Ryan Murphy (USA, 86) 3, Drew Dixon (USA, 73) 2
- 2028: Jaime Moreno (Spain, 87) 4, Duncan Sinclair (Scotland, 86) 3, Max Northcott (Scotland, 84) 2
- 2029: Nate Rowley (Australia, 80) 3, Jordan Pratt (USA, 87) 3, Tucker Roberts (Canada, 87) 2
- 2030: Tucker Roberts (Canada, 87) 4, Ryan Murphy (USA, 86) 3, Grant Bell (USA, 85) 2
- 2031: Brad Robinson (Australia, 86) 4, Grant Bell (USA, 85) 2, Tucker Roberts (Canada, 87) 2

## 3. The majors

| Year | Major | Champion | Overall | World rank before | Score | Field | Amateurs | Club pros | Via qualifying |
|---|---|---|---|---|---|---|---|---|---|
| 2027 | Tour Masters | Duncan Sinclair (Scotland) | 86 | 2 | -3 | 90 | 1 | 0 | 0 |
| 2027 | Premier Tour Championship | Jordan Pratt (USA) | 87 | 21 | +1 | 156 | 0 | 20 | 51 |
| 2027 | USA Open | Drew Dixon (USA) | 73 | 36 | -7 | 156 | 1 | 0 | 88 |
| 2027 | Britannia Open | Clay Yates (USA) | 84 | 20 | +2 | 156 | 6 | 0 | 63 |
| 2028 | Tour Masters | Duncan Sinclair (Scotland) | 86 | 2 | +0 | 90 | 6 | 0 | 0 |
| 2028 | Premier Tour Championship | Max Northcott (Scotland) | 84 | 8 | -8 | 156 | 0 | 20 | 47 |
| 2028 | USA Open | Rizal Krishnan (Malaysia) | 78 | 38 | +1 | 156 | 4 | 0 | 88 |
| 2028 | Britannia Open | Tucker Roberts (Canada) | 87 | 5 | -11 | 156 | 7 | 0 | 91 |
| 2029 | Tour Masters | Ricardo Carrasco (Mexico) | 82 | 43 | -11 | 90 | 5 | 0 | 0 |
| 2029 | Premier Tour Championship | Henry Brackley (Australia) | 81 | 14 | +1 | 156 | 0 | 20 | 48 |
| 2029 | USA Open | Josh Ramsey (USA) | 82 | 28 | +6 | 156 | 4 | 0 | 85 |
| 2029 | Britannia Open | Ryan Murphy (USA) | 86 | 8 | -10 | 156 | 7 | 0 | 91 |
| 2030 | Tour Masters | Tucker Roberts (Canada) | 87 | 5 | -11 | 90 | 6 | 0 | 0 |
| 2030 | Premier Tour Championship | Jaime Moreno (Spain) | 87 | 4 | -5 | 156 | 0 | 20 | 39 |
| 2030 | USA Open | Grant Bell (USA) | 85 | 6 | +2 | 156 | 6 | 0 | 84 |
| 2030 | Britannia Open | Brad Robinson (Australia) | 86 | 5 | -6 | 156 | 8 | 0 | 88 |
| 2031 | Tour Masters | Grant Bell (USA) | 85 | 6 | -6 | 90 | 6 | 0 | 0 |
| 2031 | Premier Tour Championship | Ole Karlsen (Norway) | 83 | 19 | -18 | 156 | 0 | 20 | 44 |
| 2031 | USA Open | Brad Robinson (Australia) | 86 | 2 | -4 | 156 | 5 | 0 | 85 |
| 2031 | Britannia Open | Nate Rowley (Australia) | 80 | 37 | -9 | 156 | 9 | 0 | 88 |

## 4. Event prestige and where the stars play

Event prestige is a rolling average of the last 4 editions of each factor (tour, field, purse, course). Average per event: prestige going into the event, field strength (0–100, from the world ranking of the best 30 entrants) and how many of the world's 20 best players entered.

| Season | Flagship prestige / field / top-20 | Standard prestige / field / top-20 | National_Open prestige / field / top-20 | Opportunity prestige / field / top-20 |
|---|---|---|---|---|
| 2027 | 91.7 / 87 / 15.9 | 83.5 / 83 / 8.6 | 87.7 / 90 / 14.0 | 70.8 / 68 / 2.4 |
| 2028 | 91.6 / 88 / 16.4 | 83.4 / 83 / 8.5 | 87.6 / 91 / 14.3 | 70.5 / 67 / 2.4 |
| 2029 | 91.6 / 88 / 16.2 | 83.3 / 83 / 8.6 | 87.5 / 90 / 13.4 | 70.0 / 66 / 2.5 |
| 2030 | 91.5 / 88 / 16.1 | 83.2 / 83 / 9.1 | 87.4 / 91 / 13.1 | 69.5 / 66 / 2.6 |
| 2031 | 91.5 / 87 / 16.5 | 83.1 / 82 / 8.7 | 87.3 / 90 / 12.9 | 69.2 / 66 / 2.5 |

**Prestige of every Premier Tour event over the test** (same week every year):

| Week | Event | Category | 2027 | 2028 | 2029 | 2030 | 2031 | Next year |
|---|---|---|---|---|---|---|---|---|
| 2 | Island Championship | opportunity | 72 | 74 | 75 | 77 | 78 | 79 |
| 4 | Texas Open | standard | 83 | 84 | 85 | 86 | 86 | 86 |
| 6 | Pacific Coast Pro-Am | flagship | 93 | 93 | 94 | 94 | 95 | 95 |
| 8 | Desert Classic | standard | 83 | 84 | 84 | 85 | 86 | 86 |
| 8 | Gulf Desert Classic | standard | 83 | 83 | 83 | 83 | 82 | 82 |
| 9 | Mexico Open | national_open | 88 | 88 | 88 | 88 | 88 | 88 |
| 10 | Kenya Open | opportunity | 69 | 68 | 68 | 67 | 67 | 67 |
| 11 | Premier Players Championship | flagship | 93 | 93 | 94 | 94 | 95 | 95 |
| 12 | India Open | national_open | 88 | 88 | 88 | 88 | 88 | 88 |
| 13 | Mid-Atlantic Championship | standard | 83 | 84 | 84 | 84 | 84 | 84 |
| 13 | Italian Championship | standard | 83 | 83 | 83 | 83 | 83 | 83 |
| 14 | Korea Championship | standard | 83 | 83 | 81 | 80 | 79 | 79 |
| 15 | Carolina Championship | standard | 83 | 84 | 85 | 85 | 86 | 86 |
| 18 | Tour Masters | major | 97 | 97 | 98 | 98 | 98 | 98 |
| 19 | Gulf Coast Classic | opportunity | 69 | 69 | 69 | 69 | 69 | 69 |
| 20 | Southern Invitational | standard | 83 | 84 | 85 | 86 | 87 | 87 |
| 22 | Heartland Invitational | flagship | 93 | 93 | 94 | 94 | 95 | 95 |
| 23 | Canada Open | national_open | 88 | 88 | 87 | 87 | 87 | 87 |
| 24 | Premier Tour Championship | major | 97 | 97 | 98 | 98 | 98 | 98 |
| 25 | USA Open | major | 97 | 97 | 98 | 98 | 98 | 98 |
| 26 | Great Lakes Open | opportunity | 69 | 69 | 67 | 66 | 65 | 65 |
| 26 | Nordic Masters | opportunity | 72 | 71 | 70 | 69 | 68 | 67 |
| 28 | German Masters | standard | 83 | 84 | 84 | 85 | 85 | 85 |
| 29 | Scotland Open | flagship | 93 | 93 | 93 | 94 | 94 | 94 |
| 30 | Britannia Open | major | 97 | 97 | 98 | 98 | 98 | 98 |
| 31 | Pacific Northwest Open | standard | 83 | 83 | 82 | 81 | 80 | 80 |
| 31 | Netherlands Open | opportunity | 69 | 69 | 68 | 67 | 67 | 66 |
| 37 | Ireland Open | national_open | 88 | 88 | 88 | 88 | 88 | 88 |
| 37 | Sandbelt Championship | standard | 83 | 82 | 82 | 80 | 79 | 79 |
| 38 | European Championship | flagship | 93 | 93 | 94 | 94 | 95 | 95 |
| 39 | France Open | national_open | 88 | 87 | 87 | 86 | 86 | 86 |
| 39 | China Masters | standard | 83 | 83 | 81 | 80 | 79 | 78 |
| 40 | Spain Open | national_open | 88 | 87 | 87 | 87 | 86 | 86 |
| 41 | Autumn Classic | opportunity | 72 | 72 | 71 | 70 | 69 | 67 |
| 41 | Japan Premier Championship | standard | 83 | 83 | 83 | 84 | 84 | 84 |
| 44 | Singapore Classic | opportunity | 72 | 72 | 72 | 72 | 72 | 72 |
| 45 | Premier Tour Finals | flagship | 90 | 90 | 91 | 91 | 91 | 91 |
| 47 | Desert Tour Championship | flagship | 90 | 86 | 83 | 80 | 77 | 77 |
| 49 | Australia Open | flagship | 90 | 90 | 91 | 91 | 92 | 92 |
| 50 | South Africa Open | national_open | 88 | 88 | 88 | 88 | 88 | 88 |

Average prestige by level now: Major 98, Amateur 21, Qualifying 27, College 24, Premier 83, Challenger 55, Regional 40, Mini 22.

## 5. Schedules, fatigue and injuries

Events played in 2031 by level (median / 90th percentile), and the world's 20 best players.

| Level | Golfers | Events (median) | Events (90th pct) |
|---|---|---|---|
| Premier Tour | 296 | 19 | 24 |
| Challenger | 966 | 24 | 27 |
| Regional | 470 | 17 | 23 |
| Mini tour | 1276 | 12 | 18 |
| College | 855 | 13 | 19 |
| Amateur | 1342 | 10 | 13 |

The 20 best players averaged **21.8 events** in 2031 (range 18–25; real-life top players play about 18–24 including majors). Stamina sets each golfer's plan (Premier players about 15–23 events, stars about 4 fewer; lower tours 19–27), tiredness makes them skip weeks, and good course managers rest more wisely.

**Injuries:** 1436 over 5 seasons (287 a year; about 6% of professionals a year). Median time out 3 weeks; longest 40 weeks.

Injury risk by group, per 1,000 events played by professionals (so golfers who play more are compared fairly with those who play less):

| Group | Professionals | Events played | Injuries per 1,000 events |
|---|---|---|---|
| Age under 30 | 464 | 34,363 | 2.8 |
| Age 30-39 | 1851 | 132,734 | 3.8 |
| Age 40+ | 1033 | 69,932 | 5.8 |
| Injury resistance under 40 | 144 | 4,132 | 6.3 |
| Injury resistance 40-60 | 1762 | 95,918 | 5.0 |
| Injury resistance over 60 | 1442 | 136,979 | 3.6 |
| Stamina under 40 | 193 | 6,247 | 6.4 |
| Stamina over 70 | 426 | 45,671 | 3.4 |

Injuries to the world's 20 best: Andrea Barbieri — shoulder, 2 weeks (4); Dean Coburn — wrist, 1 weeks (22); Beau Pratt — ankle, 7 weeks (22); Dean Coburn — wrist, 2 weeks (40); Jaime Moreno — elbow, 4 weeks (6); Andrea Barbieri — rib, 4 weeks (25); Ole Karlsen — ankle, 6 weeks (37).

**What tiredness costs** (tour-average golfer, strokes per round at Ashford Ridge versus fresh):

| Stamina | Fatigue 0.3 | Fatigue 0.6 | Fatigue 0.9 |
|---|---|---|---|
| 30 | +0.10 | +0.57 | +1.09 |
| 60 | +0.23 | +0.74 | +1.06 |
| 90 | +0.34 | +0.55 | +1.23 |

## 6. Player prestige, money and sponsors (2031)

| # | Player | Overall | World rank | Wins (all seasons) | Majors | Prize money (season) | Prestige | Sponsor income |
|---|---|---|---|---|---|---|---|---|
| 1 | Brad Robinson (Australia) | 86 | 3 | 9 | 2 | $12,339,476 | 88 | $26,820,589 |
| 2 | Tucker Roberts (Canada) | 87 | 1 | 11 | 2 | $12,055,395 | 87 | $22,637,604 |
| 3 | Jaime Moreno (Spain) | 87 | 2 | 11 | 1 | $13,614,239 | 86 | $22,211,805 |
| 4 | Duncan Sinclair (Scotland) | 86 | 4 | 10 | 2 | $9,958,710 | 83 | $15,210,208 |
| 5 | Grant Bell (USA) | 85 | 6 | 6 | 2 | $8,323,958 | 80 | $11,003,041 |
| 6 | Max Northcott (Scotland) | 84 | 5 | 5 | 1 | $9,215,188 | 78 | $8,962,240 |
| 7 | Matthew Pruitt (USA) | 82 | 7 | 2 | 0 | $8,022,311 | 78 | $8,543,059 |
| 8 | Ole Karlsen (Norway) | 83 | 11 | 2 | 1 | $6,826,843 | 73 | $5,274,448 |
| 9 | Nate Rowley (Australia) | 80 | 13 | 4 | 1 | $6,278,961 | 72 | $4,674,185 |
| 10 | Ryan Murphy (USA) | 86 | 8 | 9 | 1 | $5,251,360 | 70 | $3,569,607 |
| 11 | Young-soo Yoon (South Korea) | 80 | 18 | 2 | 0 | $5,264,972 | 70 | $3,525,881 |
| 12 | Adrián Sánchez (Spain) | 83 | 9 | 4 | 0 | $6,954,585 | 69 | $3,323,821 |
| 13 | Andrea Barbieri (Italy) | 81 | 10 | 0 | 0 | $6,907,977 | 69 | $3,247,043 |
| 14 | Gustavo Paz (Mexico) | 79 | 17 | 1 | 0 | $5,133,564 | 67 | $2,658,463 |
| 15 | Jordan Pratt (USA) | 87 | 12 | 5 | 1 | $3,904,106 | 67 | $2,654,572 |

Average player prestige by level: Premier Tour 41, Challenger 20, College 8, Amateur 3, Mini tour 3, Club professional 0, Regional 9.

## 7. Do the attributes show up in the statistics?

Professionals with 30+ rounds in 2031. Correlation between an attribute and the season statistic it should drive (−1 to 1; strokes-gained per round and scoring relative to the field in the same round, so different courses are comparable).

| Attribute | Statistic | Correlation | Expect |
|---|---|---|---|
| Power | Driving distance | +0.96 | strong + |
| Driving Accuracy | Fairways hit % | +0.60 | strong + |
| Mid Irons | Strokes gained: approach | +0.72 | + |
| Chipping | Strokes gained: around the green | +0.62 | + |
| Short Putting | Strokes gained: putting | +0.67 | + |
| Green Reading | Strokes gained: putting | +0.62 | + |
| Power | Strokes gained: off the tee | +0.48 | + |
| Overall | Scoring vs field, Premier Tour players (lower is better) | -0.83 | strong − |

(2122 professionals.)

**Premier Tour statistics leaders 2031:**

- Driving distance: Freddie Sowerby 310 yds (Power Hitter; power 99, accuracy 73, short putting 68, overall 79)
- Fairway accuracy: Alex Hebden 62% (Precision Ball-Striker; power 59, accuracy 91, short putting 65, overall 74)
- Strokes gained putting: Sam Pickering +0.58 (Elite Putter; power 78, accuracy 62, short putting 97, overall 79)
- Scoring vs field: Tucker Roberts -3.19 (Aggressive Shotmaker; power 94, accuracy 83, short putting 83, overall 87)

## 8. Lowest rounds and course records

| Round | Course (layout) | Golfer | Event |
|---|---|---|---|
| 57 (-15) | Haneul Country Club (Championship) | Ryan Benton | 2030:RG_KOREA_01 round 4 |
| 58 (-14) | Amrit Greens Gurugram Golf Club (Club) | Reece Robinson | 2029:RG_INDIA_07 round 3 |
| 58 (-14) | Club de Campo Las Praderas (Club) | Facundo Flores | 2029:MN_MEXICO_CARIBBEAN_06 round 2 |
| 58 (-14) | Chandni Lakes Golf Club (Championship) | Kai Weber | 2027:RG_INDIA_04 round 1 |
| 58 (-14) | Cork Ridge Municipal Golf Course (Regular) | Rhys Wright | 2031:MN_UK_IRELAND_08 round 2 |
| 58 (-14) | Eunbit Golf Club (Championship) | Steven Henderson | 2027:RG_KOREA_06 round 4 |
| 57 (-14) | Adelaide Springs Golf Course (Regular) | Matt Paxton | 2028:MN_AUSTRALIA_10 round 2 |
| 59 (-13) | Golf Las Cumbres (Regular) | Felipe Pérez | 2028:MN_MEXICO_CARIBBEAN_06 round 1 |

Holes-in-one: 2,340; albatrosses: 305 across 5 seasons.
