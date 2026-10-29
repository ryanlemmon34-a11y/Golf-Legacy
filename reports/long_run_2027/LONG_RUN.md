# Long run: one world, every shot, seed 2027

- Engine commit `7334ffef1cc7405e5a837d510f8236b9e83ed5e1`, engine id `b62fd89718dc6df366ec1859e65b2b7382933b11`, Python 3.13.17.
- Hardware: Intel(R) Xeon(R) Processor @ 2.10GHz, 4 logical CPUs, Python 3.13.17, Linux.
- Seasons 2027–2076 (50), full population, every shot simulated; started 2026-10-29 00:11:14. Run through the persistent session and the observer (a season skip each year, committed, published and reloaded).
- Configuration: `{"careers": {"LIFE_AGE": 26.0}, "development": {"BASE_PLAY": 0.008, "BASE_TRAIN": 0.016, "MATURING": 0.004}, "finance": {"BACKER_SHARE": 0.25, "CADDIE_SHARE": 0.08, "CREDIT_BASE": 8000, "CREDIT_CAP": 60000, "CREDIT_SHARE": 0.25, "EVIDENCE_DECAY": 0.5, "LIVING": 32000, "LIVING_WORKING": 40000, "PRIOR_PRIZE_SHARE": 0.004, "PROVEN_EVENTS": 8, "RESERVE_WEEKS": 4, "SELF_FUNDED_SEASONS": 3, "WORK_WAGE": 900}, "population": {"CANDIDATES_PER_POOL": 900, "POTENTIAL_SD": 13.0, "SCOUTING_SD": 4.0}, "residence": {"CADDIE_FOLLOWS": 0.15, "COACH_FOLLOWS": 0.25, "HOME_PULL": 60.0, "HOME_STATE_COLLEGE": 0.55, "MIN_STAY": 3, "MOVE_COST": 6000.0, "MOVE_MARGIN": 15.0, "MOVE_SCALE": 8.0, "STAY_YEARS": 3}, "staff": {"CADDIE_OF_MEANS": 0.25, "CADDIE_TIERS": 2, "COACH_OF_MEANS": 0.1, "SCOUT_SHARE": 0.05, "SELF_CADDIE": 40.0, "SELF_TEACHING": 0.3}}`

## 2. Money

- **Reconciliation:** 50 seasons checked; seasons where cash, family money, backers' money or staff payments did not reconcile: 0.
- **Flagged, not reconstructed:** in runs made before 4754eed (this one: engine 7334ffe) a season's *annual net* is the figure taken before the winter, so a winter move's $6,000 is not in it, and before 75c135f a support-funded winter move was drawn in the *next* year's ledger. Cash still reconciled every year; the per-year split of those few moves cannot be rebuilt exactly from the saved data, so annual nets are reported as recorded.

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
- Golfers who moved abroad for their career and later returned home: 50.
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

## 5. High-potential golfers: how their full-time golf ended

**Definition.** High potential = the top 5% of hidden potential (debug data: the simulation never uses it for decisions; it only finds these golfers here). An episode is a run of consecutive full-time seasons (professional or amateur, college included). An episode **ended before developing** if it ended (the golfer was no longer full-time the next season) before they were 27 and with their best overall so far at least 6 points below their potential. Its reason is the career decision recorded at the end of *that* episode's last season. A golfer who later returned to full-time golf is a **comeback**, not a loss. These counts describe this one world; they are not the total of lost talent, and the recorded reasons (with the money and desire the decision weighed) are not proof that money alone caused a departure.

Top 5% of potential (≥ 70.7): 2,127 golfers. Each of their full-time episodes (a golfer can have several), and those never full-time:

- episode ended after developing or at 27+ (a completed episode): 1,654
- still full-time at the end of the run (an unfolding episode): 655
- ended young and undeveloped, not back by the end of the run: 20
- never full-time in the archive: 6
- ended young and undeveloped, then came back (comeback episode): 3

Episodes that ended young and undeveloped and did not come back, by the recorded decision: part-time pro 7; back to amateur 5; became caddie 2; college to amateur 2; became coach 2; amateur took a job 2.

| Golfer | Potential | Best overall then | Episode | Age at end | Starts in it | Decision (recorded) |
|---|---|---|---|---|---|---|
| Brady Morgan (USA) | 75 | 65.2 | ends 2043 | 22 | 19 | part-time pro (p 0.5386, runway 0.0, progress 0.6, desire 1.55) |
| Gabriele Romano (Italy) | 74 | 67.4 | ends 2065 | 22 | 39 | part-time pro (p 0.4643, runway 0.0, progress 0.48, desire 1.84) |
| Louis Aubert (France) | 74 | 68.3 | ends 2041 | 25 | 73 | part-time pro (p 0.2991, runway 0.34, progress -0.27, desire 0.79) |
| Owen Fairchild (USA) | 74 | 67.2 | ends 2039 | 23 | 24 | part-time pro (p 0.6458, runway 0.0, progress 0.09, desire 1.1) |
| Zach Taylor (USA) | 74 | 64.0 | ends 2047 | 23 | 12 | part-time pro (p 0.7132, runway 0.0, progress -0.08, desire 0.79) |
| Chanachok F. Chaiyaporn (Thailand) | 73 | 65.6 | ends 2071 | 19 | 30 | amateur took a job (p 0.012) |
| Logan Q. Ogden (USA) | 73 | 66.7 | ends 2066 | 23 | 32 | back to amateur (p 0.6493, runway 0.0, progress 0.15, desire 1.08) |
| Shota Ito (Japan) | 73 | 66.5 | ends 2035 | 22 | 104 | college to amateur (p 0.598) |
| Darcy Jardine (Australia) | 72 | 65.2 | ends 2049 | 21 | 4 | back to amateur (p 0.3058, runway 0.0, progress 1.02, desire 2.52) |
| Baptiste Dupont (France) | 72 | 64.7 | ends 2036 | 22 | 114 | college to amateur (p 0.4458) |
| Kaito Shimizu (Japan) | 72 | 61.7 | ends 2031 | 21 | 7 | became coach (p 0.4759, runway 0.0, progress 0.48, desire 1.8) |
| George Venables (England) | 72 | 60.3 | ends 2057 | 21 | 10 | became caddie (p 0.5766, runway 0.0, progress 0.42, desire 1.39) |
| Kevin K. Calloway (USA) | 72 | 63.0 | ends 2059 | 23 | 9 | part-time pro (p 0.6827, runway 0.0, progress 0.36, desire 0.93) |
| Gavin Ross (USA) | 71 | 64.2 | ends 2030 | 22 | 21 | became caddie (p 0.6213, runway 0.0, progress 0.3, desire 1.2) |
| Cole Campbell (USA) | 71 | 63.8 | ends 2050 | 24 | 14 | back to amateur (p 0.0744, runway 0.67, progress 0.42, desire 1.14) |

## 6. Generations

Reaching No. 1 and the top ten is by **weekly world ranking**. Cohorts: the starting world's professionals and its amateurs (college included) are separate; later arrivals are 18-year-old juniors or new professionals from outside the tracked amateur game. Starting-world careers began before the archive (their early results are unknown).

| Cohort | Golfers | Reached No. 1 | Reached top 10 | Major champions | Majors won |
|---|---|---|---|---|---|
| starting world: professional | 3,834 | 8 | 43 | 27 | 64 |
| starting world: amateur | 2,615 | 0 | 2 | 3 | 5 |
| later: junior (18) | 14,880 | 12 | 65 | 67 | 129 |
| later: new professional | 21,618 | 0 | 0 | 2 | 2 |

**Most major titles:**

- Hyeon-jun U. Yoo (South Korea), born 2019, later: junior (18) (arrived 2037): 10 majors, 70 wins at every level (amateur and college included), best weekly world ranking 1
- Landon Long (USA), born 2027, later: junior (18) (arrived 2045): 9 majors, 43 wins at every level (amateur and college included), best weekly world ranking 1
- Calum Fraser (Scotland), born 2009, starting world: professional (arrived 2027): 8 majors, 54 wins at every level (amateur and college included), best weekly world ranking 1
- Sam Whitaker (USA), born 2006, starting world: professional (arrived 2027): 8 majors, 45 wins at every level (amateur and college included), best weekly world ranking 1
- Felix Moore (South Africa), born 2019, later: junior (18) (arrived 2037): 8 majors, 48 wins at every level (amateur and college included), best weekly world ranking 1
- Brian Sullivan (USA), born 2020, later: junior (18) (arrived 2038): 7 majors, 39 wins at every level (amateur and college included), best weekly world ranking 1
- Kobus Oosthuizen (South Africa), born 2000, starting world: professional (arrived 2027): 5 majors, 19 wins at every level (amateur and college included), best weekly world ranking 2
- Jaco Venter (South Africa), born 2019, later: junior (18) (arrived 2037): 5 majors, 66 wins at every level (amateur and college included), best weekly world ranking 1

**Interesting careers** (picked by rules on recorded results):

- **Most majors — Hyeon-jun U. Yoo (South Korea)**, born 2019:
  - 2037: Arrived on the scene at 18 (International University Golf)
  - 2037: First win, at Amateur level (2 that season)
  - 2041: College eligibility ended; kept playing as an amateur alongside a job
  - 2041: First win at College level (4 that season)
  - 2042: Turned professional from the amateur ranks (amateur ranking 3), starting on the Asian Challenger Tour, with backers putting up $47,800 a season for a share of winnings
  - 2043: First full-time season at Challenger level
  - 2043: First win at Premier level
  - 2043: First win at Challenger level (4 that season)
  - 2043: Won the Britannia Open (major No. 1)
  - 2043: Won the Premier Tour Championship (major No. 2)
  - 2044: First full-time season at Premier level
  - 2045: Won the Premier Tour Championship (major No. 3)
  - 2045: Won the Tour Masters (major No. 4)
  - 2045: World No. 1 at a season's end for the first time (4 season ends in all)
  - 2047: Won the Britannia Open (major No. 5)
  - … 4 more milestones
  - 2068: Won the Premier Tour Championship (major No. 10)
  - In all: 34 full-time professional seasons in the archive, 70 wins at every level (amateur and college included), 10 majors, best weekly world ranking 1
- **From the mini tours to the Premier Tour — Martín García (Argentina)**, born 2004:
  - 2028: Turned professional at 24, starting on the Southern Cone Pro Series, paying their own way
  - 2028: First full-time season at Mini level
  - 2029: First full-time season at Challenger level
  - 2029: First win, at Challenger level (2 that season)
  - 2030: First full-time season at Premier level
  - 2041: First win at Premier level
  - 2053: Retired from competitive golf at 49
  - In all: 26 full-time professional seasons in the archive, 9 wins at every level (amateur and college included), 0 majors
- **Late bloomer (arrived in the world, first Premier season at 31+) — Rupert Gillard (England)**, born 2010:
  - 2028: Arrived on the scene at 18 (US College Division I)
  - 2028: First win, at Amateur level (2 that season)
  - 2031: First win at College level (2 that season)
  - 2032: College eligibility ended; kept playing as an amateur alongside a job
  - 2038: Turned professional late, after years as an amateur (amateur ranking 9), starting on the Challenger Tour Europe, paying their own way
  - 2039: First full-time season at Challenger level
  - 2041: First win at Challenger level
  - 2042: First full-time season at Premier level
  - 2061: Retired from competitive golf at 51
  - In all: 23 full-time professional seasons in the archive, 12 wins at every level (amateur and college included), 0 majors
- **A comeback that went further than before — Rory Holroyd (Australia)**, born 2001:
  - 2027: In the starting world (career before the archive unknown)
  - 2027: First full-time season at Challenger level
  - 2027: First win, at Challenger level
  - 2028: First win at Regional level
  - 2029: Stopped chasing the tour at 28; took a job and plays a few local events (runway 10.0 yrs, progress -0.1, desire +0.3)
  - 2030: First win at Mini level (2 that season)
  - 2030: Came back to full-time golf at 29
  - 2035: First full-time season at Premier level
  - 2043: First win at Premier level
  - 2052: Retired from competitive golf at 51
  - In all: 25 full-time professional seasons in the archive, 14 wins at every level (amateur and college included), 0 majors
- **Longest full-time career — Cédric Laurent (France)**, born 2008:
  - 2027: In the starting world (career before the archive unknown)
  - 2027: First full-time season at Premier level
  - 2029: First win, at Premier level
  - 2035: Won the Tour Masters (major No. 1)
  - 2038: Won the USA Open (major No. 2)
  - 2042: World No. 1 at a season's end for the first time (2 season ends in all)
  - 2051: Won the USA Open (major No. 3)
  - 2066: Retired from competitive golf at 58
  - In all: 40 full-time professional seasons in the archive, 31 wins at every level (amateur and college included), 3 majors, best weekly world ranking 1

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

