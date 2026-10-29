# Long run: one world, every shot, seed 2027

- Engine commit `7334ffef1cc7405e5a837d510f8236b9e83ed5e1`, engine id `b62fd89718dc6df366ec1859e65b2b7382933b11`, Python 3.13.17.
- Hardware: Intel(R) Xeon(R) Processor @ 2.10GHz, 4 logical CPUs, Python 3.13.17, Linux.
- Seasons 2027–2076 (50), full population, every shot simulated; started 2026-10-29 00:11:14. Run through the persistent session and the observer (a season skip each year, committed, published and reloaded).
- Configuration: `{"careers": {"LIFE_AGE": 26.0}, "development": {"BASE_PLAY": 0.008, "BASE_TRAIN": 0.016, "MATURING": 0.004}, "finance": {"BACKER_SHARE": 0.25, "CADDIE_SHARE": 0.08, "CREDIT_BASE": 8000, "CREDIT_CAP": 60000, "CREDIT_SHARE": 0.25, "EVIDENCE_DECAY": 0.5, "LIVING": 32000, "LIVING_WORKING": 40000, "PRIOR_PRIZE_SHARE": 0.004, "PROVEN_EVENTS": 8, "RESERVE_WEEKS": 4, "SELF_FUNDED_SEASONS": 3, "WORK_WAGE": 900}, "population": {"CANDIDATES_PER_POOL": 900, "POTENTIAL_SD": 13.0, "SCOUTING_SD": 4.0}, "residence": {"CADDIE_FOLLOWS": 0.15, "COACH_FOLLOWS": 0.25, "HOME_PULL": 60.0, "HOME_STATE_COLLEGE": 0.55, "MIN_STAY": 3, "MOVE_COST": 6000.0, "MOVE_MARGIN": 15.0, "MOVE_SCALE": 8.0, "STAY_YEARS": 3}, "staff": {"CADDIE_OF_MEANS": 0.25, "CADDIE_TIERS": 2, "COACH_OF_MEANS": 0.1, "SCOUT_SHARE": 0.05, "SELF_CADDIE": 40.0, "SELF_TEACHING": 0.3}}`

## 2. Money

- **Reconciliation:** 50 seasons checked; seasons where cash, family money, backers' money or staff payments did not reconcile: 0.

**Debt at the end of each season** (full-time professionals; beyond credit = below minus their own credit limit, which grows with last season's earnings):

| Season | Full-time pros | In debt | Beyond own credit | Of those injured | Median debt |
|---|---|---|---|---|---|
| 2027 | 3,260 | 413 | 0 | 0 | $3,064 |
| 2030 | 2,760 | 1,044 | 0 | 0 | $7,890 |
| 2035 | 2,584 | 1,082 | 0 | 0 | $7,748 |
| 2040 | 2,524 | 1,026 | 0 | 0 | $7,364 |
| 2045 | 2,427 | 995 | 0 | 0 | $7,552 |
| 2050 | 2,519 | 1,020 | 0 | 0 | $7,501 |
| 2055 | 2,495 | 996 | 0 | 0 | $6,848 |
| 2060 | 2,551 | 1,004 | 0 | 0 | $7,062 |
| 2065 | 2,565 | 1,008 | 1 | 0 | $6,802 |
| 2070 | 2,622 | 1,054 | 0 | 0 | $7,168 |
| 2075 | 2,530 | 976 | 0 | 0 | $6,966 |
| 2076 | 2,557 | 989 | 0 | 0 | $7,075 |

**Backing changes per season** (seeded = professional when the world began; new = a career that began in the world):

| Season | Found backers | Withdrew (seeded / new) | No longer needed (seeded / new) |
|---|---|---|---|
| 2027 | 104 | 145 / 0 | 8 / 0 |
| 2028 | 140 | 137 / 26 | 19 / 1 |
| 2030 | 114 | 67 / 113 | 16 / 5 |
| 2035 | 120 | 12 / 198 | 6 / 22 |
| 2040 | 114 | 3 / 184 | 0 / 37 |
| 2045 | 91 | 0 / 193 | 0 / 28 |
| 2050 | 96 | 0 / 207 | 0 / 29 |
| 2055 | 97 | 0 / 193 | 0 / 39 |
| 2060 | 129 | 0 / 194 | 0 / 43 |
| 2065 | 98 | 0 / 203 | 0 / 39 |
| 2070 | 88 | 0 / 228 | 0 / 34 |
| 2075 | 105 | 0 / 207 | 0 / 35 |
| 2076 | 106 | 0 / 212 | 0 / 34 |

**Funding-related missed starts by career stage** (golfer-weeks with no affordable event, and invitations or qualified places declined for cost), whole run:

| Stage | Golfer-weeks | No affordable event | Declined for cost |
|---|---|---|---|
| college | 2,834,364 | 90,214 (3.2%) | 10,956 |
| amateur | 11,584,716 | 107,344 (0.9%) | 3,043 |
| new pro | 3,269,604 | 315,826 (9.7%) | 7,285 |
| established pro | 3,451,708 | 101,228 (2.9%) | 1,944 |
| part-time pro | 7,409,272 | 21,690 (0.3%) | 14 |
| club pro | 2,067,780 | 0 (0.0%) | 8 |

Tours with the most weeks lost to money: AM_EUROPE 48,943; CO_INTL 47,799; MN_US_SUNBELT 42,500; AM_ASIA 41,558; MN_US_DESERT 39,215; CH_LATAM_CANADA 36,894; MN_US_MIDWEST 33,571; MN_US_NORTHEAST 33,236; MN_UK_IRELAND 31,723; RG_SOUTHERN_AFRICA 30,980.

## 3. Competition access, apart from money, injury and choice

Every golfer-week of the whole run, by career stage: played; blocked by access (full fields, college lineup, no event, not eligible); blocked by money; injured; chose not to play.

| Stage | Weeks | Played | Access | Money | Injured | Chose not to |
|---|---|---|---|---|---|---|
| college | 2,834,364 | 33.8% | 48.9% | 3.2% | 0.7% | 13.4% |
| amateur | 11,584,716 | 16.3% | 44.3% | 0.9% | 0.4% | 38.1% |
| new pro | 3,269,604 | 31.9% | 41.2% | 9.7% | 0.7% | 16.6% |
| established pro | 3,451,708 | 43.4% | 25.4% | 2.9% | 1.5% | 26.7% |
| part-time pro | 7,409,272 | 16.1% | 44.8% | 0.3% | 0.5% | 38.2% |
| club pro | 2,067,780 | 19.7% | 57.4% | 0.0% | 0.6% | 22.2% |

## 4. Where people live

| Season | caddie followed their player | closer to their events | closer to their events (after college) | coach followed their players | returned home | returned home (after college) | Not made (money) |
|---|---|---|---|---|---|---|---|
| 2027 | 0 | 9 | 1 | 4 | 0 | 66 | 37 |
| 2030 | 69 | 4 | 0 | 3 | 11 | 27 | 125 |
| 2035 | 66 | 3 | 0 | 4 | 11 | 18 | 172 |
| 2040 | 49 | 3 | 0 | 6 | 10 | 12 | 154 |
| 2045 | 53 | 1 | 0 | 6 | 13 | 7 | 186 |
| 2050 | 57 | 2 | 0 | 4 | 10 | 20 | 166 |
| 2055 | 38 | 3 | 0 | 7 | 15 | 9 | 158 |
| 2060 | 51 | 1 | 0 | 9 | 11 | 19 | 149 |
| 2065 | 56 | 1 | 0 | 4 | 8 | 25 | 162 |
| 2070 | 48 | 2 | 0 | 2 | 5 | 23 | 171 |
| 2075 | 39 | 4 | 0 | 4 | 15 | 19 | 162 |
| 2076 | 47 | 2 | 0 | 5 | 3 | 15 | 162 |

Whole run: caddie followed their player 2,626; returned home (after college) 920; returned home 484; coach followed their players 272; closer to their events 143; closer to their events (after college) 4.

- Travel and entry costs per event, full-time professionals: living in their own country median $1,957 (125,176 seasons); living abroad median $1,988 (3,556 seasons).
- Golfers who moved abroad for their career and later returned home: 59.
  - **Alfie Bennett (South Africa)**, born 2005: 2027: North Carolina, USA → Andalusia, Spain (closer to the Challenger Tour Europe events (about $26,586 a season less travel; the move cost $6,000); after college); 2030: Andalusia, Spain → Gauteng, South Africa (returned home (travel $19,699 a season dearer, no longer a burden))
  - **Richard Henderson (Canada)**, born 2007: 2030: California, USA → Antioquia, Colombia (closer to the Latin America & Canada Tour events (about $17,030 a season less travel; the move cost $6,000)); 2033: Antioquia, Colombia → British Columbia, Canada (returned home (closer to their events too: $18,596 a season less travel))
  - **Brandon Anderson (USA)**, born 2007: 2027: Nevada, USA → Antioquia, Colombia (closer to the Latin America & Canada Tour events (about $17,017 a season less travel; the move cost $6,000)); 2030: Antioquia, Colombia → Nevada, USA (returned home (closer to their events too: $52,058 a season less travel))
  - **Laurie Rawlinson (South Africa)**, born 2000: 2031: Gauteng, South Africa → Surrey, England (closer to the Premier Tour Europe events (about $19,269 a season less travel; the move cost $6,000)); 2034: Surrey, England → Gauteng, South Africa (returned home (travel $19,313 a season dearer, no longer a burden))
  - **Riaan Naudé (South Africa)**, born 2006: 2027: Gauteng, South Africa → Andalusia, Spain (closer to the Challenger Tour Europe events (about $25,430 a season less travel; the move cost $6,000); after a change of status); 2030: Andalusia, Spain → Gauteng, South Africa (returned home (travel $25,498 a season dearer, no longer a burden))

## 3b. Mini-tour seasons cut short by money, by cause

Full-time mini-tour professional seasons (2028–2076): 53,030; with 4+ weeks unable to afford any event: 23,835 (44.9%). Causes that applied (a season can have several):

- took 8+ weeks of paid work: 21,397 (89.8%)
- last season golf cost more than it won: 14,050 (58.9%)
- began the season in debt: 11,890 (49.9%)
- no backers' money this season or last: 9,676 (40.6%)
- new professional this season: 9,473 (39.7%)
- lives outside their tour's countries: 3,135 (13.2%)
- began the season with under $5,000: 1,604 (6.7%)
- backers withdrew last winter: 1,593 (6.7%)
- injured 4+ weeks last season: 306 (1.3%)
- injured 4+ weeks this season: 303 (1.3%)

## 5. High-potential golfers who left before developing

Found with debug data (hidden potential); the simulation never uses it for decisions. "Left" = their last full-time season was before 27 and they were still at least 6 points of overall below their potential.

Top 5% of potential (≥ 70.7): 2,127 golfers; left before developing: 5. Reasons: became caddie 2; became coach 2; back to amateur 1.

| Golfer | Potential | Best overall | Left at | Starts | Reason (recorded) |
|---|---|---|---|---|---|
| Darcy Jardine (Australia) | 72 | 66.4 | 21 (2049) | 21 | back to amateur (p 0.3058, runway 0.0, progress 1.02, desire 2.52) |
| Kaito Shimizu (Japan) | 72 | 61.7 | 21 (2031) | 7 | became coach (p 0.4759, runway 0.0, progress 0.48, desire 1.8) |
| George Venables (England) | 72 | 60.3 | 21 (2057) | 10 | became caddie (p 0.5766, runway 0.0, progress 0.42, desire 1.39) |
| Gavin Ross (USA) | 71 | 64.2 | 22 (2030) | 21 | became caddie (p 0.6213, runway 0.0, progress 0.3, desire 1.2) |
| Yusaku Kimura (Japan) | 71 | 63.8 | 25 (2036) | 28 | became coach (p 0.627, runway 0.0, progress -0.2, desire 1.18) |

## 6. Generations

- Golfers who arrived in season two or later: 36,498; of them world No. 1 at some point: 8, top 10: 53; major champions: 69.
- Major wins by arrival: starting world 69; arrived later 131.

**Most major titles:**

- Hyeon-jun U. Yoo (South Korea), born 2019, arrived 2037: 10 majors, 70 wins, best world ranking 1
- Landon Long (USA), born 2027, arrived 2045: 9 majors, 43 wins, best world ranking 1
- Calum Fraser (Scotland), born 2009, arrived 2027: 8 majors, 54 wins, best world ranking 1
- Sam Whitaker (USA), born 2006, arrived 2027: 8 majors, 45 wins, best world ranking 1
- Felix Moore (South Africa), born 2019, arrived 2037: 8 majors, 48 wins, best world ranking 2
- Brian Sullivan (USA), born 2020, arrived 2038: 7 majors, 39 wins, best world ranking 2
- Kobus Oosthuizen (South Africa), born 2000, arrived 2027: 5 majors, 19 wins, best world ranking 4
- Jaco Venter (South Africa), born 2019, arrived 2037: 5 majors, 66 wins, best world ranking 1

**Interesting careers** (picked by rules on recorded results):

- **Most majors — Hyeon-jun U. Yoo (South Korea)**, born 2019:
  - 2037: Arrived on the scene at 18 (International University Golf)
  - 2037: Won the Asian Amateur Series Event 95 (Saudi Arabia) at -10 (Al Rimal Golf Links)
  - 2037: Won the Singapore Amateur Championship at -8 (Sparrow Bay Golf Club)
  - 2038: Won the Asian Amateur Series Event 54 (China) at -8 (Jinlong Xiamen International Golf Club)
  - 2038: Won the India Amateur Championship at -3 (Kesar Bagh New Delhi Golf & Country Club)
  - 2039: Coaching with Si-hyun Moon ended (joined Yuto Saito)
  - 2039: Won the Asian Amateur Series Event 12 (Japan) at -9 (Hanamizuki Golf Links)
  - 2039: Won the China Amateur Championship at +3 (Jinlong Xiamen International Golf Club)
  - 2039: Won the Asia-Pacific Amateur Championship at -12 (Xinghai International Golf Club)
  - 2039: Won the Asian Amateur Series Championship at -16 (Takigawa Miyazaki Golf Links)
  - 2040: Won the Indonesia Amateur Championship at -18 (Tasik Biru Golf Club)
  - 2040: Won the China Amateur Championship at -9 (Yunshan Lakes Golf Club)
  - 2040: Won the Malaysia Amateur Championship at -16 (Bukit Tinggi Golf Resort)
  - 2040: Won the India Amateur Championship at -18 (Vana Vihar Mumbai Golf & Country Club)
- **From the mini tours to the Premier Tour — Martín García (Argentina)**, born 2004:
  - 2028: Turned professional at 24, starting on the Southern Cone Pro Series, paying their own way
  - 2028: Southern Cone Pro Series → Latin America & Canada Tour (called up to fill the Latin America & Canada Tour)
  - 2029: Won the Latin America & Canada Tour Event 3 at -23 (Golfe Quinta da Ribeira)
  - 2029: Won the Latin America & Canada Tour Event 4 at -13 (Pemberly Run Golf Club)
  - 2029: Latin America & Canada Tour → Premier Tour Americas (top 5 on Latin America & Canada Tour)
  - 2031: Premier Tour Americas → Latin America & Canada Tour (lost Premier card)
  - 2032: Won the Latin America & Canada Tour Event 4 at -8 (Blackwater Woods Golf Club)
  - 2032: Latin America & Canada Tour → Premier Tour Americas (top 5 on Latin America & Canada Tour)
  - 2034: Coaching with Rodrigo Paz ended (coach retired)
  - 2038: Won the Chile Open at -13 (Golf La Cañada)
  - 2040: Won the Argentina Open at -22 (Golf Las Encinas Altas)
  - 2041: Won the Pacific Northwest Open at +6 (Heron Park Golf Club)
  - 2044: Won the Peru Open at -17 (Club de Campo La Estancia)
  - 2046: Won the Argentina Open at -19 (Golf Las Encinas Altas)
- **Late bloomer (first Premier season at 31+) — Hunter Baker (USA)**, born 1992:
  - 2027: Won the Desert Tour Championship at -15 (Al Bahr Golf Resort)
  - 2027: Won the Australia Open at -14 (Royal Juniper Brook National)
  - 2028: Won the Tour Masters at -11 (Georgia National Golf Club)
  - 2031: Injured (elbow), out for 4 weeks
  - 2031: Won the Korea Championship at -22 (Pureun Golf Club)
  - 2031: Won the USA Open at -10 (Marten Hollow Golf Club)
  - 2033: Won the Pacific Coast Pro-Am at -5 (Rowan Vale Club)
  - 2033: Won the Mid-Atlantic Championship at -11 (Badgerbrook Club)
  - 2033: Injured (ankle), out for 3 weeks
  - 2034: Won the Desert Classic at -22 (Northcote Cove Club)
  - 2035: Caddie Robert Rutledge off the bag (caddie retired)
  - 2038: Won the Carolina Championship at -27 (Holly Ridge Golf Club)
  - 2039: Caddie Nick Pruitt off the bag (the golfer wanted a change)
  - 2043: Retired from competitive golf at 51
- **A comeback that went further than before — Rory Holroyd (Australia)**, born 2001:
  - 2027: Won the Philippines Open at -13 (Linden Downs Resort Course)
  - 2027: Injured (oblique), out for 2 weeks
  - 2028: Won the Australasia Tour Event 5 at -17 (Bramble Fields Country Club)
  - 2029: Stopped chasing the tour at 28; took a job and plays a few local events (runway 10.0 yrs, progress -0.1, desire +0.3)
  - 2030: Caddie Gonzalo Rojas off the bag (no longer on a tour that needs one)
  - 2030: Won the Australian State Pro Series Event 2 at -1 (Cedar Point Golf Club)
  - 2030: Won the Australian State Pro Series Event 7 at -11 (Whitewater Moor Golf Resort)
  - 2030: Won the Australasia Tour Event 13 at -19 (Marten Glen Country Club)
  - 2030: Quit their job to make another run at it, aged 29
  - 2031: Won the Australasia Tour Event 14 at -2 (Badger Crest Golf Club)
  - 2031: Australian State Pro Series → Asian Challenger Tour (top 4 on Australian State Pro Series)
  - 2032: Injured (thumb), out for 3 weeks
  - 2034: Won the Asian Challenger Tour Event 2 at -16 (Gunung Indah Golf Club)
  - 2034: Won the Japan Golf Tour Event 16 at -4 (Kumanodai Golf Links)
- **Longest full-time career — Cédric Laurent (France)**, born 2008:
  - 2028: Caddie Tanner James off the bag (caddie retired)
  - 2029: Coaching with Alfred Olsson ended (joined Hugo Michel)
  - 2029: Won the Italian Championship at -23 (Golf Club Le Querce)
  - 2030: Injured (back), out for 3 weeks
  - 2030: Won the Heartland Invitational at -11 (Dunmore Wood Golf Club)
  - 2031: Won the Canada Open at -14 (Pemberly Run Golf Club)
  - 2032: Won the German Masters at -22 (Golfpark Waldsee)
  - 2033: Won the Texas Open at -12 (Hartwell Landing Club)
  - 2034: Won the Island Championship at -25 (Ashcombe Harbor Golf Club)
  - 2034: Won the Australia Open at -10 (Wolfe Crest Golf Club)
  - 2035: Won the Pacific Coast Pro-Am at +2 (Rowan Vale Club)
  - 2035: Won the Tour Masters at -11 (Georgia National Golf Club)
  - 2037: Won the Carolina Championship at -13 (Hartwell Landing Club)
  - 2037: Won the Japan Premier Championship at -10 (Suzukake Golf Club)

## 7. Population, archive and the season skip

The owner's target: a season skip within 120 s including save, publication and a usable observer. A 50-season run does not prove season 100.

| Season | Active | People | Archive MB | Checkpoint MB | Skip s | Simulate | Save | Publish | Observer | First Records |
|---|---|---|---|---|---|---|---|---|---|---|
| 2027 (#1) | 6,955 | 7,176 | 12.5 | 14.7 | 108.5 | 101.9 | 4.4 | 1.8 | 0.4 | 0.44 |
| 2031 (#5) | 8,775 | 10,127 | 59.9 | 26.2 | 147.1 | 130.3 | 8.6 | 4.0 | 4.2 | 0.23 |
| 2036 (#10) | 10,576 | 13,790 | 123.0 | 33.5 | 179.4 | 151.9 | 12.7 | 5.8 | 9.0 | 0.48 |
| 2041 (#15) | 11,679 | 17,413 | 190.4 | 40.1 | 203.6 | 170.1 | 11.7 | 7.6 | 14.2 | 1.75 |
| 2046 (#20) | 12,456 | 20,956 | 260.9 | 46.2 | 215.8 | 181.9 | 13.2 | 3.8 | 16.8 | 2.97 |
| 2051 (#25) | 12,833 | 24,570 | 334.0 | 52.2 | 227.6 | 175.9 | 14.4 | 11.3 | 26.0 | 2.48 |
| 2056 (#30) | 12,914 | 28,212 | 408.8 | 57.8 | 253.4 | 191.1 | 16.1 | 13.7 | 32.6 | 3.58 |
| 2061 (#35) | 12,941 | 31,854 | 484.3 | 63.5 | 262.8 | 189.8 | 19.0 | 3.7 | 50.4 | 2.36 |
| 2066 (#40) | 13,083 | 35,625 | 560.6 | 68.9 | 276.8 | 193.4 | 20.4 | 4.0 | 59.0 | 3.2 |
| 2071 (#45) | 13,217 | 39,365 | 637.8 | 74.6 | 276.2 | 201.6 | 23.2 | 4.1 | 47.4 | 3.87 |
| 2076 (#50) | 13,187 | 42,947 | 715.1 | 80.1 | 279.5 | 201.2 | 22.9 | 4.4 | 51.0 | 4.42 |

Seasons over 120 s: 49 of 50 (first: 2028).

