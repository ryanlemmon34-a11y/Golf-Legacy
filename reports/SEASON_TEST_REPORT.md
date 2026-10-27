# Golf Legacy — Multi-Season World Test

5 full seasons (2027–2031) of the whole world: 5,694 golfers, 3,233 events, **16,194,676 holes, every shot simulated**, in 5.9 minutes (70 s per season on 4 cores). Attributes are held fixed, so every change below comes from the season system (entries, results, cards, rankings, prestige), not from players improving or aging.

## 1. Does the world sort players by ability?

Average overall rating at each level at the start of each season (the starting world was sorted by a noisy reputation; after that, only results move players), and how well the world ranking follows true ability (Spearman correlation, top 500 pros by overall).

| Season | Premier Tour | Challenger | Regional | Mini tour | College | Amateur | Ranking vs ability | Top-50 players on the Premier Tour |
|---|---|---|---|---|---|---|---|---|
| 2027 | 78.8 (300) | 67.7 (930) | 57.7 (455) | 54.3 (1291) | 48.9 (960) | 38.0 (1455) | 0.61 | 50 of 50 |
| 2028 | 78.3 (294) | 67.7 (953) | 56.9 (440) | 54.6 (1289) | 48.9 (960) | 38.0 (1455) | 0.69 | 50 of 50 |
| 2029 | 78.2 (300) | 67.6 (957) | 56.4 (432) | 54.7 (1287) | 48.9 (960) | 38.0 (1455) | 0.68 | 49 of 50 |
| 2030 | 78.2 (293) | 67.7 (955) | 56.4 (424) | 54.8 (1304) | 48.9 (960) | 38.0 (1455) | 0.67 | 50 of 50 |
| 2031 | 78.3 (299) | 67.5 (952) | 56.7 (417) | 54.7 (1308) | 48.9 (960) | 38.0 (1455) | 0.66 | 50 of 50 |

**Tour cards each off-season** (players moving between levels):

| After season | Premier → Challenger | Challenger → Premier | Challenger → lower | Lower → Challenger | Regional ↔ Mini |
|---|---|---|---|---|---|
| 2027 | 98 | 90 | 103 | 118 | 62 |
| 2028 | 92 | 95 | 101 | 108 | 63 |
| 2029 | 94 | 86 | 120 | 110 | 76 |
| 2030 | 84 | 86 | 107 | 106 | 81 |
| 2031 | 90 | 87 | 108 | 109 | 70 |

Examples of players earning Premier Tour cards after the last season: Parker Brooks (USA, 82) — top 25 on Challenger Tour Americas; Josh Taylor (USA, 80) — top 25 on Challenger Tour Americas; Yusaku Fujii (Japan, 80) — top 8 on Japan Golf Tour; Rupert Hebden (England, 80) — top 20 on Challenger Tour Europe; Joseph Holloway (USA, 79) — top 25 on Challenger Tour Americas; Tadhg Kavanagh (Ireland, 79) — top 20 on Challenger Tour Europe.

## 2. Who wins

| Level | Events | Different winners | Winners' average overall | Field average | Wins by the level's 10 best players | Lowest-rated winner |
|---|---|---|---|---|---|---|
| Major | 20 | 18 | 87.4 | 79.5 | 45% | 78 (Premier Tour Championship 2030) |
| Premier | 180 | 92 | 85.2 | 79.1 | 34% | 71 (Nordic Masters 2028) |
| Challenger | 450 | 345 | 73.3 | 69.0 | 1% | 58 (Japan Golf Tour Event 15 2030) |
| Regional | 390 | 298 | 70.5 | 62.0 | 2% | 53 (Zambia Open 2028) |
| Mini | 838 | 551 | 62.5 | 57.1 | 0% | 41 (Australian State Pro Series Event 2 2028) |
| College | 485 | 269 | 57.3 | 52.3 | 9% | 33 (US Small College Golf Event 6 2028) |
| Amateur | 780 | 431 | 56.1 | 45.6 | 7% | 27 (African Amateur Series Event 1 2027) |

**Most wins in a season (Premier Tour and majors):**

- 2027: Jack Kelly (Australia, 88) 4, Duncan Sinclair (Scotland, 92) 3, Hunter Baker (USA, 92) 3
- 2028: Manuel Muñoz (Spain, 92) 3, Rafael Gallego (Spain, 89) 2, Ji-ho Jeon (South Korea, 88) 2
- 2029: Nate Tremayne (Australia, 90) 3, Jordan Pratt (USA, 92) 3, Sam Hextall (Australia, 86) 2
- 2030: Jiahao Xie (China, 91) 3, Carlo Torres (Philippines, 86) 2, Chase Richardson (USA, 84) 2
- 2031: Hunter Baker (USA, 92) 4, Michael Sheehan (Ireland, 90) 3, Nate Tremayne (Australia, 90) 3

## 3. The majors

| Year | Major | Champion | Overall | World rank before | Score | Field | Amateurs | Club pros | Via qualifying |
|---|---|---|---|---|---|---|---|---|---|
| 2027 | Tour Masters | Kobus Uys (South Africa) | 85 | 35 | -9 | 90 | 1 | 0 | 0 |
| 2027 | Premier Tour Championship | Duncan Sinclair (Scotland) | 92 | 8 | -5 | 156 | 0 | 20 | 53 |
| 2027 | USA Open | Shane Ingram (New Zealand) | 86 | 41 | -7 | 156 | 2 | 0 | 92 |
| 2027 | Britannia Open | Jack Kelly (Australia) | 88 | 9 | -10 | 156 | 6 | 0 | 64 |
| 2028 | Tour Masters | Kobus Uys (South Africa) | 85 | 24 | -9 | 90 | 6 | 0 | 0 |
| 2028 | Premier Tour Championship | Ryan Murphy (USA) | 90 | 11 | -13 | 156 | 0 | 20 | 47 |
| 2028 | USA Open | Hunter James (USA) | 85 | 33 | -6 | 156 | 4 | 2 | 85 |
| 2028 | Britannia Open | Rafael Gallego (Spain) | 89 | 18 | -11 | 156 | 7 | 0 | 90 |
| 2029 | Tour Masters | Juan Navarro (Philippines) | 86 | 16 | -8 | 90 | 6 | 0 | 0 |
| 2029 | Premier Tour Championship | Tomoya Matsumoto (Japan) | 84 | 32 | -3 | 156 | 0 | 20 | 46 |
| 2029 | USA Open | Robert James (USA) | 84 | 30 | +0 | 156 | 4 | 0 | 85 |
| 2029 | Britannia Open | Sam Hextall (Australia) | 86 | 13 | -13 | 156 | 8 | 0 | 89 |
| 2030 | Tour Masters | Jiahao Xie (China) | 91 | 9 | -14 | 90 | 7 | 0 | 0 |
| 2030 | Premier Tour Championship | Jaime Navarro (Spain) | 78 | 101 | -8 | 156 | 0 | 20 | 47 |
| 2030 | USA Open | Hunter Baker (USA) | 92 | 6 | -3 | 156 | 5 | 1 | 87 |
| 2030 | Britannia Open | Sam Whitaker (USA) | 89 | 8 | -8 | 156 | 8 | 0 | 95 |
| 2031 | Tour Masters | Reed Anderson (USA) | 84 | 43 | -15 | 90 | 6 | 0 | 0 |
| 2031 | Premier Tour Championship | Michael Sheehan (Ireland) | 90 | 14 | -22 | 156 | 0 | 20 | 50 |
| 2031 | USA Open | Nate Tremayne (Australia) | 90 | 6 | -8 | 156 | 3 | 0 | 88 |
| 2031 | Britannia Open | Jiahao Xie (China) | 91 | 2 | -18 | 156 | 6 | 0 | 91 |

## 4. Event prestige and where the stars play

Average per event: prestige going into the event, field strength (0–100, from the world ranking of the best 30 entrants) and how many of the world's 20 best players entered.

| Season | Flagship prestige / field / top-20 | Standard prestige / field / top-20 | National_Open prestige / field / top-20 | Opportunity prestige / field / top-20 |
|---|---|---|---|---|
| 2027 | 91.7 / 86 / 17.2 | 83.5 / 84 / 9.2 | 87.7 / 93 / 16.7 | 70.8 / 74 / 1.9 |
| 2028 | 91.4 / 87 / 17.2 | 83.4 / 84 / 9.8 | 87.8 / 93 / 16.4 | 71.0 / 74 / 2.5 |
| 2029 | 91.4 / 87 / 17.5 | 83.4 / 84 / 9.9 | 87.8 / 93 / 16.7 | 71.1 / 74 / 2.9 |
| 2030 | 91.4 / 87 / 17.5 | 83.4 / 84 / 10.0 | 87.9 / 93 / 17.3 | 71.1 / 75 / 3.8 |
| 2031 | 91.4 / 87 / 17.1 | 83.4 / 84 / 10.1 | 87.9 / 93 / 17.1 | 71.5 / 76 / 3.8 |

**Prestige of every Premier Tour event over the test** (same week every year):

| Week | Event | Category | 2027 | 2028 | 2029 | 2030 | 2031 | Next year |
|---|---|---|---|---|---|---|---|---|
| 2 | Island Championship | opportunity | 72 | 74 | 76 | 77 | 77 | 78 |
| 4 | Texas Open | standard | 83 | 85 | 85 | 86 | 86 | 86 |
| 6 | Pacific Coast Pro-Am | flagship | 93 | 94 | 94 | 94 | 94 | 94 |
| 8 | Desert Classic | standard | 83 | 84 | 85 | 85 | 85 | 85 |
| 8 | Gulf Desert Classic | standard | 83 | 83 | 83 | 82 | 82 | 82 |
| 9 | Mexico Open | national_open | 88 | 88 | 88 | 88 | 88 | 88 |
| 10 | Kenya Open | opportunity | 69 | 70 | 71 | 72 | 73 | 73 |
| 11 | Premier Players Championship | flagship | 93 | 94 | 94 | 94 | 94 | 94 |
| 12 | India Open | national_open | 88 | 88 | 88 | 88 | 88 | 88 |
| 13 | Mid-Atlantic Championship | standard | 83 | 84 | 84 | 84 | 84 | 84 |
| 13 | Italian Championship | standard | 83 | 83 | 83 | 83 | 83 | 83 |
| 14 | Korea Championship | standard | 83 | 84 | 84 | 85 | 85 | 85 |
| 15 | Carolina Championship | standard | 83 | 84 | 85 | 85 | 85 | 85 |
| 18 | Tour Masters | major | 97 | 98 | 98 | 98 | 98 | 98 |
| 19 | Gulf Coast Classic | opportunity | 69 | 70 | 70 | 72 | 72 | 72 |
| 20 | Southern Invitational | standard | 83 | 84 | 86 | 86 | 86 | 86 |
| 22 | Heartland Invitational | flagship | 93 | 94 | 94 | 94 | 94 | 94 |
| 23 | Canada Open | national_open | 88 | 88 | 88 | 88 | 88 | 88 |
| 24 | Premier Tour Championship | major | 97 | 98 | 98 | 98 | 98 | 98 |
| 25 | USA Open | major | 97 | 98 | 98 | 98 | 98 | 98 |
| 26 | Great Lakes Open | opportunity | 69 | 68 | 68 | 67 | 67 | 68 |
| 26 | Nordic Masters | opportunity | 72 | 71 | 70 | 69 | 69 | 68 |
| 28 | German Masters | standard | 83 | 84 | 85 | 85 | 85 | 86 |
| 29 | Scotland Open | flagship | 93 | 94 | 94 | 94 | 94 | 94 |
| 30 | Britannia Open | major | 97 | 98 | 98 | 98 | 98 | 98 |
| 31 | Pacific Northwest Open | standard | 83 | 82 | 81 | 82 | 81 | 81 |
| 31 | Netherlands Open | opportunity | 69 | 69 | 69 | 68 | 68 | 68 |
| 37 | Ireland Open | national_open | 88 | 88 | 88 | 88 | 88 | 88 |
| 37 | Sandbelt Championship | standard | 83 | 81 | 80 | 79 | 79 | 78 |
| 38 | European Championship | flagship | 93 | 94 | 94 | 94 | 94 | 94 |
| 39 | France Open | national_open | 88 | 88 | 88 | 88 | 88 | 88 |
| 39 | China Masters | standard | 83 | 81 | 80 | 79 | 78 | 78 |
| 40 | Spain Open | national_open | 88 | 87 | 87 | 87 | 87 | 87 |
| 41 | Autumn Classic | opportunity | 72 | 71 | 71 | 69 | 70 | 69 |
| 41 | Japan Premier Championship | standard | 83 | 83 | 83 | 82 | 83 | 83 |
| 44 | Singapore Classic | opportunity | 72 | 74 | 75 | 76 | 77 | 77 |
| 45 | Premier Tour Finals | flagship | 90 | 90 | 91 | 91 | 91 | 91 |
| 47 | Desert Tour Championship | flagship | 90 | 83 | 80 | 78 | 76 | 76 |
| 49 | Australia Open | flagship | 90 | 91 | 91 | 91 | 91 | 93 |
| 50 | South Africa Open | national_open | 88 | 88 | 88 | 88 | 88 | 88 |

Average prestige by level now: Major 98, Amateur 21, Qualifying 27, College 25, Premier 83, Challenger 56, Regional 41, Mini 22.

## 5. Player prestige, money and sponsors (2031)

| # | Player | Overall | World rank | Wins (all seasons) | Majors | Prize money (season) | Prestige | Sponsor income |
|---|---|---|---|---|---|---|---|---|
| 1 | Hunter Baker (USA) | 92 | 1 | 10 | 1 | $19,084,757 | 87 | $23,882,812 |
| 2 | Manuel Muñoz (Spain) | 92 | 6 | 6 | 0 | $9,212,371 | 84 | $16,809,411 |
| 3 | Jiahao Xie (China) | 91 | 2 | 6 | 2 | $11,499,245 | 83 | $15,935,053 |
| 4 | Duncan Sinclair (Scotland) | 92 | 8 | 8 | 1 | $8,088,515 | 83 | $15,353,898 |
| 5 | Jordan Pratt (USA) | 92 | 3 | 10 | 0 | $12,851,076 | 83 | $15,267,182 |
| 6 | Nate Tremayne (Australia) | 90 | 4 | 8 | 1 | $13,550,232 | 82 | $14,335,217 |
| 7 | Michael Sheehan (Ireland) | 90 | 5 | 7 | 1 | $12,147,451 | 81 | $11,869,295 |
| 8 | Sam Whitaker (USA) | 89 | 7 | 6 | 1 | $9,215,288 | 79 | $10,230,267 |
| 9 | Ryan Murphy (USA) | 90 | 12 | 4 | 1 | $6,343,573 | 77 | $7,917,093 |
| 10 | Jack Kelly (Australia) | 88 | 14 | 6 | 1 | $5,366,693 | 76 | $6,608,837 |
| 11 | Ji-ho Jeon (South Korea) | 88 | 9 | 4 | 0 | $6,304,809 | 75 | $6,508,730 |
| 12 | Santiago Martínez (Mexico) | 89 | 15 | 4 | 0 | $5,882,517 | 74 | $5,410,571 |
| 13 | Rafael Gallego (Spain) | 89 | 16 | 5 | 1 | $5,631,441 | 72 | $4,538,822 |
| 14 | Seung-ho Moon (South Korea) | 86 | 10 | 4 | 0 | $6,557,137 | 71 | $3,911,451 |
| 15 | Carlo Torres (Philippines) | 86 | 17 | 4 | 0 | $2,974,970 | 70 | $3,739,012 |

Average player prestige by level: Premier Tour 41, Challenger 21, Amateur 3, College 7, Mini tour 6, Club professional 1, Regional 9.

## 6. Do the attributes show up in the statistics?

Professionals with 30+ rounds in 2031. Correlation between an attribute and the season statistic it should drive (−1 to 1; strokes-gained per round and scoring relative to the field in the same round, so different courses are comparable).

| Attribute | Statistic | Correlation | Expect |
|---|---|---|---|
| Power | Driving distance | +0.97 | strong + |
| Driving Accuracy | Fairways hit % | +0.63 | strong + |
| Mid Irons | Strokes gained: approach | +0.79 | + |
| Chipping | Strokes gained: around the green | +0.70 | + |
| Short Putting | Strokes gained: putting | +0.72 | + |
| Green Reading | Strokes gained: putting | +0.71 | + |
| Power | Strokes gained: off the tee | +0.56 | + |
| Overall | Scoring vs field, Premier Tour players (lower is better) | -0.85 | strong − |

(2068 professionals.)

**Premier Tour statistics leaders 2031:**

- Driving distance: Corey Parker 311 yds (Power Hitter; power 99, accuracy 57, short putting 74, overall 76)
- Fairway accuracy: Amir Subramaniam 63% (Precision Ball-Striker; power 57, accuracy 96, short putting 78, overall 80)
- Strokes gained putting: Torbjørn Hansen +0.84 (Elite Putter; power 76, accuracy 73, short putting 99, overall 81)
- Scoring vs field: Hunter Baker -3.68 (Elite Putter; power 87, accuracy 91, short putting 99, overall 92)

## 7. Lowest rounds and course records

| Round | Course (layout) | Golfer | Event |
|---|---|---|---|
| 56 (-16) | Holly Bluff Country Club (Championship) | Santiago Martínez | 2031:PT_TEXAS_OPEN round 2 |
| 56 (-16) | Cork Ridge Municipal Golf Course (Regular) | Luis Medina | 2027:AM_EUROPE_06 round 1 |
| 56 (-16) | Kesar Bagh Golf & Country Club (Club) | Zhi Luo | 2030:RG_INDIA_05 round 1 |
| 57 (-15) | Fox Valley Club (Championship) | Bryce Carter | 2030:CH_AMERICAS_03 round 3 |
| 57 (-15) | Pemberly Bluff Country Club (Championship) | Clay Yates | 2029:MN_US_NORTHEAST_06 round 1 |
| 57 (-15) | Golf du Château Blanc (Championship) | Ricardo Almeida | 2031:CH_EUROPE_08 round 1 |
| 57 (-14) | Golf Los Fresnos (Championship) | Luke Griffiths | 2028:MN_IBERIA_09 round 1 |
| 58 (-14) | Golf Las Cumbres (Regular) | Julián Luna | 2030:AM_LATAM_02 round 2 |

Holes-in-one: 2,281; albatrosses: 301 across 5 seasons.
