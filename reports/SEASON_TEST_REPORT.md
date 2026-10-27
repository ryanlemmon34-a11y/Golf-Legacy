# Golf Legacy — Multi-Season World Test

5 full seasons (2027–2031) of the whole world: 6,101 golfers, 3,241 events, **16,131,247 holes, every shot simulated**, in 6.6 minutes (79 s per season on 4 cores). Attributes are held fixed, so every change below comes from the season system (entries, results, cards, rankings, prestige), not from players improving or aging.

## 1. Does the world sort players by ability?

Average overall rating at each level at the start of each season (the starting world was sorted by a noisy reputation; after that, only results move players), and how well the world ranking follows true ability (Spearman correlation, top 500 pros by overall).

| Season | Premier Tour | Challenger | Regional | Mini tour | College | Amateur | Ranking vs ability | Top-50 players on the Premier Tour |
|---|---|---|---|---|---|---|---|---|
| 2027 | 74.3 (300) | 65.8 (938) | 57.0 (516) | 54.0 (1594) | 49.9 (867) | 37.4 (1556) | 0.61 | 50 of 50 |
| 2028 | 74.1 (292) | 65.3 (992) | 56.4 (488) | 54.3 (1576) | 49.9 (867) | 37.4 (1556) | 0.67 | 49 of 50 |
| 2029 | 74.0 (301) | 65.3 (989) | 55.9 (492) | 54.4 (1566) | 49.9 (867) | 37.4 (1556) | 0.67 | 50 of 50 |
| 2030 | 74.0 (296) | 65.3 (990) | 56.0 (493) | 54.4 (1569) | 49.9 (867) | 37.4 (1556) | 0.69 | 50 of 50 |
| 2031 | 74.0 (300) | 65.2 (990) | 56.1 (491) | 54.4 (1567) | 49.9 (867) | 37.4 (1556) | 0.67 | 50 of 50 |

**Tour cards each off-season** (players moving between levels):

| After season | Premier → Challenger | Challenger → Premier | Challenger → lower | Lower → Challenger | Regional ↔ Mini |
|---|---|---|---|---|---|
| 2027 | 100 | 88 | 116 | 158 | 76 |
| 2028 | 84 | 89 | 146 | 148 | 79 |
| 2029 | 95 | 85 | 154 | 145 | 100 |
| 2030 | 86 | 89 | 142 | 145 | 81 |
| 2031 | 96 | 89 | 149 | 145 | 93 |

Examples of players earning Premier Tour cards after the last season: Spencer Young (USA, 77) — top 25 on Challenger Tour Americas; Zach Parker (USA, 76) — top 25 on Challenger Tour Americas; Armando Herrera (Argentina, 76) — top 5 on Latin America & Canada Tour; Harrison Easley (USA, 75) — top 25 on Challenger Tour Americas; Mark Caldwell (USA, 75) — top 25 on Challenger Tour Americas; Joseph Lewis (USA, 74) — top 25 on Challenger Tour Americas.

## 2. Who wins

| Level | Events | Different winners | Winners' average overall | Field average | Wins by the level's 10 best players | Lowest-rated winner |
|---|---|---|---|---|---|---|
| Major | 20 | 15 | 82.9 | 75.1 | 65% | 72 (Premier Tour Championship 2029) |
| Premier | 180 | 113 | 78.8 | 74.4 | 26% | 62 (Great Lakes Open 2029) |
| Challenger | 450 | 360 | 69.5 | 66.5 | 0% | 59 (Japan Open 2031) |
| Regional | 390 | 309 | 66.9 | 60.3 | 1% | 51 (China Open 2027) |
| Mini | 846 | 585 | 61.8 | 57.2 | 0% | 39 (Japan Challenge Circuit Event 3 2027) |
| College | 485 | 283 | 55.8 | 51.3 | 7% | 33 (US Small College Golf Event 22 2027) |
| Amateur | 780 | 431 | 55.1 | 43.9 | 5% | 22 (European Amateur Series Event 17 2031) |

**Most wins in a season (Premier Tour and majors):**

- 2027: Jordan Pratt (USA, 87) 5, Jaime Moreno (Spain, 87) 3, Thongchai Boonma (Thailand, 79) 2
- 2028: Jaime Moreno (Spain, 87) 3, Ryan Murphy (USA, 86) 2, Adrián Sánchez (Spain, 83) 2
- 2029: Ryan Murphy (USA, 86) 3, Jaime Moreno (Spain, 87) 2, Max Northcott (Scotland, 84) 2
- 2030: Jaime Moreno (Spain, 87) 4, Tucker Roberts (Canada, 87) 2, Rhenzo Ocampo (Philippines, 79) 2
- 2031: Brad Robinson (Australia, 86) 5, Jaime Moreno (Spain, 87) 3, Max Northcott (Scotland, 84) 2

## 3. The majors

| Year | Major | Champion | Overall | World rank before | Score | Field | Amateurs | Club pros | Via qualifying |
|---|---|---|---|---|---|---|---|---|---|
| 2027 | Tour Masters | Takashi Okada (Japan) | 81 | 26 | -5 | 90 | 1 | 0 | 0 |
| 2027 | Premier Tour Championship | Dean Coburn (New Zealand) | 84 | 16 | +1 | 156 | 0 | 20 | 52 |
| 2027 | USA Open | Harrison Allen (USA) | 73 | 112 | -4 | 156 | 2 | 0 | 90 |
| 2027 | Britannia Open | Kittipong Charoensuk (Thailand) | 75 | 281 | +1 | 156 | 5 | 0 | 63 |
| 2028 | Tour Masters | Duncan Sinclair (Scotland) | 86 | 17 | -2 | 90 | 5 | 0 | 0 |
| 2028 | Premier Tour Championship | Ryan Murphy (USA) | 86 | 7 | -12 | 156 | 0 | 20 | 45 |
| 2028 | USA Open | Adrián Sánchez (Spain) | 83 | 22 | -5 | 156 | 4 | 0 | 85 |
| 2028 | Britannia Open | Brad Robinson (Australia) | 86 | 3 | -5 | 156 | 7 | 0 | 89 |
| 2029 | Tour Masters | Dean Coburn (New Zealand) | 84 | 19 | -1 | 90 | 6 | 0 | 0 |
| 2029 | Premier Tour Championship | Shih-chang Hsu (Taiwan) | 72 | 145 | -1 | 156 | 0 | 20 | 43 |
| 2029 | USA Open | Jaime Moreno (Spain) | 87 | 4 | +5 | 156 | 5 | 1 | 84 |
| 2029 | Britannia Open | Max Northcott (Scotland) | 84 | 8 | -3 | 156 | 8 | 0 | 82 |
| 2030 | Tour Masters | Max Northcott (Scotland) | 84 | 6 | -3 | 90 | 6 | 0 | 0 |
| 2030 | Premier Tour Championship | Brad Robinson (Australia) | 86 | 9 | -5 | 156 | 0 | 20 | 47 |
| 2030 | USA Open | Matthew Pruitt (USA) | 82 | 19 | +4 | 156 | 5 | 0 | 83 |
| 2030 | Britannia Open | Tucker Roberts (Canada) | 87 | 2 | -6 | 156 | 10 | 0 | 84 |
| 2031 | Tour Masters | Jaime Moreno (Spain) | 87 | 1 | -5 | 90 | 6 | 0 | 0 |
| 2031 | Premier Tour Championship | Sam Wilson (Australia) | 80 | 67 | -12 | 156 | 0 | 20 | 41 |
| 2031 | USA Open | Brad Robinson (Australia) | 86 | 2 | -6 | 156 | 4 | 0 | 83 |
| 2031 | Britannia Open | Clay Yates (USA) | 84 | 11 | -17 | 156 | 7 | 0 | 78 |

## 4. Event prestige and where the stars play

Event prestige is a rolling average of the last 4 editions of each factor (tour, field, purse, course). Average per event: prestige going into the event, field strength (0–100, from the world ranking of the best 30 entrants) and how many of the world's 20 best players entered.

| Season | Flagship prestige / field / top-20 | Standard prestige / field / top-20 | National_Open prestige / field / top-20 | Opportunity prestige / field / top-20 |
|---|---|---|---|---|
| 2027 | 91.7 / 86 / 15.8 | 83.5 / 83 / 8.9 | 87.7 / 91 / 14.6 | 70.8 / 68 / 2.6 |
| 2028 | 91.5 / 87 / 16.1 | 83.4 / 84 / 9.4 | 87.6 / 91 / 13.6 | 70.5 / 67 / 2.5 |
| 2029 | 91.5 / 88 / 16.6 | 83.3 / 83 / 9.1 | 87.5 / 91 / 13.4 | 70.1 / 66 / 2.5 |
| 2030 | 91.5 / 88 / 16.6 | 83.2 / 83 / 8.9 | 87.4 / 91 / 12.4 | 69.5 / 65 / 2.5 |
| 2031 | 91.5 / 87 / 16.2 | 83.1 / 82 / 8.6 | 87.3 / 91 / 12.7 | 69.1 / 66 / 2.2 |

**Prestige of every Premier Tour event over the test** (same week every year):

| Week | Event | Category | 2027 | 2028 | 2029 | 2030 | 2031 | Next year |
|---|---|---|---|---|---|---|---|---|
| 2 | Island Championship | opportunity | 72 | 74 | 75 | 77 | 79 | 79 |
| 4 | Texas Open | standard | 83 | 84 | 85 | 86 | 86 | 86 |
| 6 | Pacific Coast Pro-Am | flagship | 93 | 93 | 94 | 94 | 95 | 95 |
| 8 | Desert Classic | standard | 83 | 84 | 85 | 85 | 86 | 86 |
| 8 | Gulf Desert Classic | standard | 83 | 83 | 83 | 82 | 82 | 82 |
| 9 | Mexico Open | national_open | 88 | 88 | 88 | 88 | 88 | 88 |
| 10 | Kenya Open | opportunity | 69 | 68 | 68 | 67 | 67 | 67 |
| 11 | Premier Players Championship | flagship | 93 | 93 | 94 | 94 | 95 | 95 |
| 12 | India Open | national_open | 88 | 88 | 88 | 88 | 88 | 88 |
| 13 | Mid-Atlantic Championship | standard | 83 | 84 | 84 | 84 | 84 | 85 |
| 13 | Italian Championship | standard | 83 | 84 | 83 | 83 | 83 | 83 |
| 14 | Korea Championship | standard | 83 | 83 | 82 | 81 | 80 | 80 |
| 15 | Carolina Championship | standard | 83 | 84 | 85 | 85 | 86 | 86 |
| 18 | Tour Masters | major | 97 | 97 | 98 | 98 | 98 | 98 |
| 19 | Gulf Coast Classic | opportunity | 69 | 69 | 68 | 69 | 68 | 69 |
| 20 | Southern Invitational | standard | 83 | 84 | 86 | 86 | 87 | 87 |
| 22 | Heartland Invitational | flagship | 93 | 93 | 94 | 94 | 95 | 95 |
| 23 | Canada Open | national_open | 88 | 88 | 88 | 87 | 87 | 87 |
| 24 | Premier Tour Championship | major | 97 | 97 | 98 | 98 | 98 | 98 |
| 25 | USA Open | major | 97 | 97 | 98 | 98 | 98 | 98 |
| 26 | Great Lakes Open | opportunity | 69 | 69 | 68 | 66 | 65 | 65 |
| 26 | Nordic Masters | opportunity | 72 | 71 | 70 | 68 | 67 | 66 |
| 28 | German Masters | standard | 83 | 84 | 84 | 85 | 85 | 85 |
| 29 | Scotland Open | flagship | 93 | 93 | 93 | 94 | 94 | 94 |
| 30 | Britannia Open | major | 97 | 97 | 98 | 98 | 98 | 98 |
| 31 | Pacific Northwest Open | standard | 83 | 82 | 81 | 81 | 80 | 79 |
| 31 | Netherlands Open | opportunity | 69 | 69 | 69 | 67 | 67 | 66 |
| 37 | Ireland Open | national_open | 88 | 88 | 88 | 88 | 88 | 88 |
| 37 | Sandbelt Championship | standard | 83 | 82 | 81 | 80 | 79 | 79 |
| 38 | European Championship | flagship | 93 | 93 | 94 | 94 | 95 | 95 |
| 39 | France Open | national_open | 88 | 87 | 87 | 86 | 86 | 86 |
| 39 | China Masters | standard | 83 | 82 | 81 | 80 | 78 | 77 |
| 40 | Spain Open | national_open | 88 | 87 | 87 | 87 | 86 | 87 |
| 41 | Autumn Classic | opportunity | 72 | 72 | 71 | 70 | 69 | 67 |
| 41 | Japan Premier Championship | standard | 83 | 84 | 84 | 84 | 84 | 84 |
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
| Premier Tour | 300 | 18 | 24 |
| Challenger | 990 | 23 | 26 |
| Regional | 491 | 17 | 24 |
| Mini tour | 1230 | 12 | 18 |
| College | 848 | 14 | 18 |
| Amateur | 1390 | 6 | 12 |

The 20 best players averaged **21.4 events** in 2031 (range 18–24; real-life top players play about 18–24 including majors). Stamina sets each golfer's plan (Premier players about 15–23 events, stars about 4 fewer; lower tours 19–27), tiredness makes them skip weeks, and good course managers rest more wisely.

**Injuries:** 1400 over 5 seasons (280 a year; about 6% of professionals a year). Median time out 3 weeks; longest 40 weeks.

Injury risk by group, per 1,000 events played by professionals (so golfers who play more are compared fairly with those who play less):

| Group | Professionals | Events played | Injuries per 1,000 events |
|---|---|---|---|
| Age under 30 | 464 | 34,612 | 2.7 |
| Age 30-39 | 1851 | 132,087 | 3.5 |
| Age 40+ | 1033 | 69,642 | 5.7 |
| Injury resistance under 40 | 152 | 4,546 | 8.8 |
| Injury resistance 40-60 | 1760 | 95,273 | 4.5 |
| Injury resistance over 60 | 1436 | 136,522 | 3.6 |
| Stamina under 40 | 210 | 5,883 | 5.9 |
| Stamina over 70 | 425 | 45,446 | 3.2 |

Injuries to the world's 20 best: Andrea Barbieri — shoulder, 2 weeks (4); Dean Coburn — wrist, 1 weeks (22); Beau Pratt — ankle, 7 weeks (22); Jaime Moreno — elbow, 4 weeks (6); Andrea Barbieri — rib, 4 weeks (25); Colm Burke — ankle, 7 weeks (37).

**What tiredness costs** (tour-average golfer, strokes per round at Ashford Ridge versus fresh):

| Stamina | Fatigue 0.3 | Fatigue 0.6 | Fatigue 0.9 |
|---|---|---|---|
| 30 | +0.10 | +0.57 | +1.09 |
| 60 | +0.23 | +0.74 | +1.06 |
| 90 | +0.34 | +0.55 | +1.23 |

## 6. Player prestige, money and sponsors (2031)

| # | Player | Overall | World rank | Wins (all seasons) | Majors | Prize money (season) | Prestige | Sponsor income |
|---|---|---|---|---|---|---|---|---|
| 1 | Brad Robinson (Australia) | 86 | 1 | 9 | 3 | $17,525,080 | 91 | $37,765,141 |
| 2 | Jaime Moreno (Spain) | 87 | 2 | 15 | 2 | $11,568,586 | 87 | $22,491,716 |
| 3 | Max Northcott (Scotland) | 84 | 6 | 6 | 2 | $8,716,068 | 82 | $13,649,819 |
| 4 | Ryan Murphy (USA) | 86 | 7 | 6 | 1 | $10,131,310 | 81 | $12,224,232 |
| 5 | Jordan Pratt (USA) | 87 | 3 | 8 | 0 | $8,241,414 | 79 | $9,615,701 |
| 6 | Tucker Roberts (Canada) | 87 | 5 | 6 | 1 | $8,379,184 | 79 | $9,580,378 |
| 7 | Dean Coburn (New Zealand) | 84 | 9 | 3 | 2 | $7,289,421 | 78 | $9,124,322 |
| 8 | Clay Yates (USA) | 84 | 4 | 3 | 1 | $9,006,915 | 78 | $8,982,082 |
| 9 | Duncan Sinclair (Scotland) | 86 | 8 | 1 | 1 | $8,514,496 | 77 | $7,749,156 |
| 10 | Grant Bell (USA) | 85 | 10 | 3 | 0 | $6,991,864 | 74 | $5,434,540 |
| 11 | Ole Karlsen (Norway) | 83 | 11 | 2 | 0 | $6,704,482 | 73 | $5,063,785 |
| 12 | Andrea Barbieri (Italy) | 81 | 12 | 1 | 0 | $7,340,255 | 72 | $4,234,083 |
| 13 | Rizal Krishnan (Malaysia) | 78 | 15 | 1 | 0 | $5,571,219 | 71 | $4,060,905 |
| 14 | Takashi Okada (Japan) | 81 | 13 | 3 | 1 | $5,543,894 | 71 | $3,986,235 |
| 15 | Sam Wilson (Australia) | 80 | 23 | 1 | 1 | $5,138,791 | 68 | $2,999,016 |

Average player prestige by level: Premier Tour 40, Challenger 19, College 8, Amateur 3, Mini tour 3, Club professional 0, Regional 9.

## 7. Do the attributes show up in the statistics?

Professionals with 30+ rounds in 2031. Correlation between an attribute and the season statistic it should drive (−1 to 1; strokes-gained per round and scoring relative to the field in the same round, so different courses are comparable).

| Attribute | Statistic | Correlation | Expect |
|---|---|---|---|
| Power | Driving distance | +0.96 | strong + |
| Driving Accuracy | Fairways hit % | +0.58 | strong + |
| Mid Irons | Strokes gained: approach | +0.71 | + |
| Chipping | Strokes gained: around the green | +0.67 | + |
| Short Putting | Strokes gained: putting | +0.69 | + |
| Green Reading | Strokes gained: putting | +0.63 | + |
| Power | Strokes gained: off the tee | +0.50 | + |
| Overall | Scoring vs field, Premier Tour players (lower is better) | -0.84 | strong − |

(2116 professionals.)

**Premier Tour statistics leaders 2031:**

- Driving distance: Freddie Sowerby 309 yds (Power Hitter; power 99, accuracy 73, short putting 68, overall 79)
- Fairway accuracy: Do-yun Ahn 63% (Precision Ball-Striker; power 47, accuracy 95, short putting 74, overall 76)
- Strokes gained putting: Jackson Richardson +0.72 (Elite Putter; power 72, accuracy 77, short putting 94, overall 78)
- Scoring vs field: Brad Robinson -2.95 (Aggressive Shotmaker; power 94, accuracy 75, short putting 79, overall 86)

## 8. Lowest rounds and course records

| Round | Course (layout) | Golfer | Event |
|---|---|---|---|
| 56 (-16) | Cork Ridge Municipal Golf Course (Regular) | Iain McAllister | 2031:MN_UK_IRELAND_08 round 1 |
| 58 (-14) | Vana Vihar Golf & Country Club (Championship) | Seung-ho Son | 2029:RG_INDIA_08 round 4 |
| 58 (-14) | Golf Las Cumbres (Regular) | Rafael Medina | 2031:MN_MEXICO_CARIBBEAN_01 round 1 |
| 57 (-14) | Tallbacka Golfklubb (Championship) | Aksel Kristiansen | 2031:CH_EUROPE_04 round 4 |
| 58 (-14) | Matsugaoka Golf Links (Regular) | Taiga Saito | 2028:CO_INTL_02 round 2 |
| 57 (-14) | Adelaide Springs Golf Course (Regular) | Keita Matsumoto | 2027:CO_INTL_08 round 2 |
| 57 (-14) | Granlunda Golfklubb (Club) | Esben Hansen | 2030:MN_NORDIC_06 round 2 |
| 58 (-14) | Bellmoor Wood Club (Club) | Kota Saito | 2028:INTL_UNIVERSITY_CHAMPIONSHIP round 1 |

Holes-in-one: 2,253; albatrosses: 303 across 5 seasons.
