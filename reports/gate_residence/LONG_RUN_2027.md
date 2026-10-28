# Long run: one world, every shot, seed 2027

- Engine commit `b81a5e9e1ed6d281b5191e1ccd5cd6d6e9e69808`, engine id `9fd335f50997fbedc74b00d19607d5c818703c65`, Python 3.13.17.
- Hardware: Intel(R) Xeon(R) Processor @ 2.10GHz, 4 logical CPUs, Python 3.13.17, Linux.
- Seasons 2027–2028 (2), full population, every shot simulated; started 2026-10-28 23:26:58. Run through the persistent session and the observer (a season skip each year, committed, published and reloaded).
- Configuration: `{"careers": {"LIFE_AGE": 26.0}, "development": {"BASE_PLAY": 0.008, "BASE_TRAIN": 0.016, "MATURING": 0.004}, "finance": {"BACKER_SHARE": 0.25, "CADDIE_SHARE": 0.08, "CREDIT_BASE": 8000, "CREDIT_CAP": 60000, "CREDIT_SHARE": 0.25, "EVIDENCE_DECAY": 0.5, "LIVING": 32000, "LIVING_WORKING": 40000, "PRIOR_PRIZE_SHARE": 0.004, "PROVEN_EVENTS": 8, "RESERVE_WEEKS": 4, "SELF_FUNDED_SEASONS": 3, "WORK_WAGE": 900}, "population": {"CANDIDATES_PER_POOL": 900, "POTENTIAL_SD": 13.0, "SCOUTING_SD": 4.0}, "residence": {"CADDIE_FOLLOWS": 0.15, "COACH_FOLLOWS": 0.25, "HOME_PULL": 60.0, "HOME_STATE_COLLEGE": 0.55, "MIN_STAY": 3, "MOVE_COST": 6000.0, "MOVE_MARGIN": 15.0, "MOVE_SCALE": 8.0, "STAY_YEARS": 3}, "staff": {"CADDIE_OF_MEANS": 0.25, "CADDIE_TIERS": 2, "COACH_OF_MEANS": 0.1, "SCOUT_SHARE": 0.05, "SELF_CADDIE": 40.0, "SELF_TEACHING": 0.3}}`

## 2. Money

- **Reconciliation:** 2 seasons checked; seasons where cash, family money, backers' money or staff payments did not reconcile: 0.

**Debt at the end of each season** (full-time professionals; beyond credit = below minus their own credit limit, which grows with last season's earnings):

| Season | Full-time pros | In debt | Beyond own credit | Of those injured | Median debt |
|---|---|---|---|---|---|
| 2027 | 3,260 | 422 | 0 | 0 | $3,080 |
| 2028 | 3,033 | 810 | 0 | 0 | $5,618 |

**Backing changes per season** (seeded = professional when the world began; new = a career that began in the world):

| Season | Found backers | Withdrew (seeded / new) | No longer needed (seeded / new) |
|---|---|---|---|
| 2027 | 104 | 145 / 0 | 8 / 0 |
| 2028 | 150 | 129 / 24 | 24 / 0 |

**Funding-related missed starts by career stage** (golfer-weeks with no affordable event, and invitations or qualified places declined for cost), whole run:

| Stage | Golfer-weeks | No affordable event | Declined for cost |
|---|---|---|---|
| college | 108,888 | 79 (0.1%) | 14 |
| amateur | 181,532 | 138 (0.1%) | 8 |
| new pro | 61,360 | 2,266 (3.7%) | 67 |
| established pro | 265,876 | 4,745 (1.8%) | 115 |
| part-time pro | 40,352 | 0 (0.0%) | 0 |
| club pro | 39,000 | 0 (0.0%) | 0 |

Tours with the most weeks lost to money: MN_US_SUNBELT 864; MN_US_MIDWEST 723; MN_US_DESERT 692; MN_JAPAN 530; MN_UK_IRELAND 513; CH_LATAM_CANADA 403; MN_US_NORTHEAST 397; RG_KOREA 328; RG_CHINA 300; RG_SOUTHERN_AFRICA 298.

## 3. Competition access, apart from money, injury and choice

Every golfer-week of the whole run, by career stage: played; blocked by access (full fields, college lineup, no event, not eligible); blocked by money; injured; chose not to play.

| Stage | Weeks | Played | Access | Money | Injured | Chose not to |
|---|---|---|---|---|---|---|
| college | 108,888 | 45.0% | 27.7% | 0.1% | 0.8% | 26.5% |
| amateur | 181,532 | 22.2% | 26.4% | 0.1% | 0.6% | 50.7% |
| new pro | 61,360 | 41.0% | 38.7% | 3.7% | 0.8% | 15.8% |
| established pro | 265,876 | 43.5% | 34.7% | 1.8% | 1.3% | 18.8% |
| part-time pro | 40,352 | 18.8% | 34.4% | 0.0% | 0.6% | 46.2% |
| club pro | 39,000 | 24.6% | 43.7% | 0.0% | 0.7% | 31.0% |

## 4. Where people live

| Season | caddie followed their player | closer to their events | closer to their events (after college) | coach followed their players | returned home | returned home (after college) | Not made (money) |
|---|---|---|---|---|---|---|---|
| 2027 | 0 | 19 | 1 | 4 | 0 | 78 | 15 |
| 2028 | 108 | 9 | 0 | 5 | 5 | 62 | 33 |

Whole run: returned home (after college) 140; caddie followed their player 108; closer to their events 28; coach followed their players 9; returned home 5; closer to their events (after college) 1.

- Travel and entry costs per event, full-time professionals: living in their own country median $1,735 (6,245 seasons); living abroad median $2,055 (47 seasons).
- Golfers who moved abroad for their career and later returned home: 3.
  - **Troy Evans (USA)**, born 2001: 2027: South Carolina, USA → Antioquia, Colombia (closer to the Latin America & Canada Tour events (about $16,826 a season less travel; the move cost $6,000)); 2028: Antioquia, Colombia → South Carolina, USA (returned home (closer to their events too: $2,880 a season less travel))
  - **Albin Eklund (Sweden)**, born 2004: 2027: Skåne, Sweden → Gauteng, South Africa (closer to the Southern Africa Tour events (about $19,862 a season less travel; the move cost $6,000)); 2028: Gauteng, South Africa → Skåne, Sweden (returned home (closer to their events too: $2,242 a season less travel))
  - **Robert Coleman (Canada)**, born 1999: 2027: Ontario, Canada → Antioquia, Colombia (closer to the Latin America & Canada Tour events (about $13,067 a season less travel; the move cost $6,000)); 2028: Antioquia, Colombia → Ontario, Canada (returned home (closer to their events too: $2,880 a season less travel))

## 3b. Mini-tour seasons cut short by money, by cause

Full-time mini-tour professional seasons (2028–2028): 1,449; with 4+ weeks unable to afford any event: 334 (23.1%). Causes that applied (a season can have several):

- took 8+ weeks of paid work: 315 (94.3%)
- no backers' money this season or last: 195 (58.4%)
- last season golf cost more than it won: 187 (56.0%)
- new professional this season: 146 (43.7%)
- began the season with under $5,000: 74 (22.2%)
- began the season in debt: 52 (15.6%)
- lives outside their tour's countries: 27 (8.1%)
- injured 4+ weeks last season: 12 (3.6%)
- backers withdrew last winter: 10 (3.0%)
- injured 4+ weeks this season: 5 (1.5%)

## 5. High-potential golfers who left before developing

Found with debug data (hidden potential); the simulation never uses it for decisions. "Left" = their last full-time season was before 27 and they were still at least 6 points of overall below their potential.

Top 5% of potential (≥ 73.5): 361 golfers; left before developing: 0. Reasons: .

| Golfer | Potential | Best overall | Left at | Starts | Reason (recorded) |
|---|---|---|---|---|---|

## 6. Generations

- Golfers who arrived in season two or later: 1,491; of them world No. 1 at some point: 0, top 10: 0; major champions: 0.
- Major wins by arrival: starting world 8; arrived later 0.

**Most major titles:**

- Schalk Olivier (South Africa), born 1996, arrived 2027: 2 majors, 7 wins, best world ranking 1
- Arnaud Bernard (Canada), born 2001, arrived 2027: 1 majors, 2 wins, best world ranking 13
- Calum Fraser (Scotland), born 2009, arrived 2027: 1 majors, 1 wins, best world ranking 4
- Jayden Bramwell (New Zealand), born 1994, arrived 2027: 1 majors, 1 wins, best world ranking 9
- Clay Yates (USA), born 1990, arrived 2027: 1 majors, 2 wins, best world ranking 12
- Grant Bell (USA), born 1998, arrived 2027: 1 majors, 2 wins, best world ranking 6
- Yuki Abe (Japan), born 1997, arrived 2027: 1 majors, 2 wins, best world ranking 6

**Interesting careers** (picked by rules on recorded results):

- **Most majors — Schalk Olivier (South Africa)**, born 1996:
  - 2027: Won the Mexico Open at -7 (Club de Campo El Mirador)
  - 2027: Won the Tour Masters at -5 (Georgia National Golf Club)
  - 2027: Won the Scotland Open at -3 (Stagfield Golf Club)
  - 2027: Won the Premier Tour Finals at -20 (Hartwell Landing Club)
  - 2028: Won the Korea Championship at -24 (Hanbit Country Club)
  - 2028: Won the Tour Masters at -10 (Georgia National Golf Club)
  - 2028: Won the Scotland Open at -15 (Quarry Brook Links)
- **Most wins — Joseph Fairchild (USA)**, born 2005:
  - 2027: Won the US College Division I Event 27 at -11 (Whitewater Knoll Golf Club)
  - 2027: Injured (elbow), out for 6 weeks
  - 2027: Won the North American Amateur Series Event 95 (Canada) at -7 (Bluestone Wood Club)
  - 2027: Won the US College Division I Event 39 at -10 (Ashmere Golf Club)
  - 2027: Won the US College Division I Event 44 at -10 (Granite Crest Golf Club)
  - 2027: Won the US College Division I Event 54 at -6 (Holly Park Golf Club)
  - 2027: Won the US College Division I Event 56 at -11 (Martenley Golf Club)
  - 2027: Turned professional after college (amateur ranking 16), starting on the Desert Mini Tour, with backers putting up $34,800 a season for a share of winnings
  - 2028: Won the Desert Mini Tour Event 27 at -18 (Holly Point Club)
  - 2028: Won the Northeast Mini Tour Event 31 at -16 (Sparrow Park Golf Club)
  - 2028: Won the Desert Mini Tour Championship at -13 (Langford Brook Country Club)
  - 2028: Won the Desert Mini Tour Event 38 at -12 (Larkton Golf Club)
  - 2028: Desert Mini Tour → Challenger Tour Americas (top 4 on Desert Mini Tour)
  - 2028: Their backers withdrew
- **Late bloomer (first Premier season at 31+) — Hunter Baker (USA)**, born 1992:
  - 2027: Won the Desert Tour Championship at -15 (Al Bahr Golf Resort)
  - 2027: Won the Australia Open at -14 (Royal Juniper Brook National)
  - 2028: Won the Australia Open at -10 (Wolfe Crest Golf Club)
  - 2028: Caddie Robert Rutledge off the bag (caddie retired)

## 7. Population, archive and the season skip

The owner's target: a season skip within 120 s including save, publication and a usable observer. A 50-season run does not prove season 100.

| Season | Active | People | Archive MB | Checkpoint MB | Skip s | Simulate | Save | Publish | Observer | First Records |
|---|---|---|---|---|---|---|---|---|---|---|
| 2027 (#1) | 6,955 | 7,176 | 12.5 | 14.7 | 107.8 | 101.4 | 4.2 | 1.8 | 0.5 | 0.37 |
| 2028 (#2) | 7,461 | 7,940 | 24.3 | 21.8 | 121.6 | 112.8 | 6.0 | 1.4 | 1.4 | 0.09 |

Seasons over 120 s: 1 of 2 (first: 2028).

