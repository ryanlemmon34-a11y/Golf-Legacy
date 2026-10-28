# Competition access pass: before / after

What changed is described in `docs/COMPETITION_ACCESS.md` and `docs/CIRCUIT_FLAGSHIPS.md`. Files here:

- `BASELINE.md` — the access audit of the calendar before this pass (seeds 2027 and 3031, season one).
- `AFTER.md` — the same audit after it, three seasons per seed (2027-2029), with Premier members by rights.
- `COMPARE_SEASON1.md` — season one before → after, by playing status, both seeds pooled.
- `long_world_3y/` — the integration check (`tools/long_world.py --seeds 2027 3031 --years 3 --strict`):
  every season's cash reconciled, staff payments matched receipts, no staff violations, the population
  reconciled.

Short runs only: three seasons, two seeds. Nothing here is evidence about decades or centuries.

## Season one, before → after (both seeds)

| Status | Weeks played | Weeks blocked (full / no event / ineligible) | Starts p10 / p25 / p50 | Reaching ¾ of intended |
|---|---|---|---|---|
| College | 21% → 45% | 59% → 21% | 8/10/12 → 23/23/25 | 53% → 99% |
| Amateur, full-time | 21% → 33% | 69% → 29% | 9/10/11 → 16/17/18 | 100% → 99% |
| Amateur, part-time | 11% → 19% | 67% → 24% | 1/2/6 → 5/8/11 | 55% → 88% |
| Club professional | 1% → 24% | 99% → 21% | 0/0/0 → 8/9/14 | 6% → 88% |
| Mini-tour pro | 17% → 39% | 82% → 44% | 4/6/8 → 16/19/21 | 2% → 85% |
| Regional-tour pro | 31% → 44% | 60% → 37% | 11/13/16 → 16/21/24 | 35% → 88% |
| Challenger pro | 39% → 47% | 49% → 33% | 10/19/23 → 21/24/26 | 77% → 96% |
| Premier member | 33% → 44% | 23% → 14% | 12/15/18 → 21/22/23 | 69% → 99% |

"Intended" is each golfer's own target number of starts (owner: college ~24, other full-time amateurs
16, part-time amateurs 8, club professionals ~12, professionals 19-27). Blocked weeks still include
many weeks golfers *wanted* an extra start beyond their schedule; `AFTER.md` separates the weeks shut out
while behind schedule (a real shortage).

Premier playing rights, seasons two and three: exempt (31-59 members) and full (75-90) median 22-23
starts, essentially never shut out; graduates (86-93) median 24-25 and conditional members (68-80)
median 23-24, reaching them by taking Challenger alternatives (capped at 10% of a Challenger field).

## Representative careers (seed 2027, from the history archive)


### Blake Whitlock (USA) — conditional Premier member using Challenger alternatives
- 2027: pro/full_time on PT_AMERICAS (full): 23 starts, 1 wins, $659,314 prize, world 341 / amateur —; weeks: 22 played, 0 alternatives, 1 shut out, 21 training, 0 with nothing scheduled; routes: PREMIER FULL 20, ? 1, PF 1
- 2028: pro/full_time on PT_AMERICAS (conditional): 25 starts, 0 wins, $1,512,840 prize, world 120 / amateur —; weeks: 24 played, 6 alternatives, 11 shut out, 9 training, 0 with nothing scheduled; routes: PREMIER CONDITIONAL 11, PREMIER MEMBER (visitor places) 7, PREMIER TOUR AMERICAS MEMBER 4
- 2029: pro/full_time on PT_AMERICAS (full): 22 starts, 0 wins, $1,880,551 prize, world 102 / amateur —; weeks: 21 played, 0 alternatives, 1 shut out, 21 training, 0 with nothing scheduled; routes: PREMIER FULL 19, ? 1, P6 1

### Yuto Ota (Japan) — Challenger graduate in his first Premier season
- 2027: pro/full_time on CH_JAPAN: 25 starts, 2 wins, $1,749,446 prize, world 39 / amateur —; weeks: 25 played, 11 alternatives, 14 shut out, 7 training, 0 with nothing scheduled; routes: MEMBER 12, JAPAN GOLF TOUR MEMBER 8, ? 2
- 2028: pro/full_time on PT_ASIA_PACIFIC (graduate): 24 starts, 0 wins, $1,876,526 prize, world 56 / amateur —; weeks: 24 played, 3 alternatives, 5 shut out, 12 training, 0 with nothing scheduled; routes: PREMIER GRADUATE 15, PREMIER MEMBER (visitor places) 5, M13 1
- 2029: pro/full_time on PT_AMERICAS (full): 22 starts, 0 wins, $1,933,955 prize, world 72 / amateur —; weeks: 21 played, 0 alternatives, 1 shut out, 22 training, 0 with nothing scheduled; routes: PREMIER FULL 17, ? 2, M15 1

### Andreas Gottschalk (Austria) — mini-tour professional who stopped chasing (unsuccessful)
- 2027: pro/full_time on CH_EUROPE: 24 starts, 0 wins, $33,670 prize, world 1244 / amateur —; weeks: 24 played, 15 alternatives, 19 shut out, 2 training, 0 with nothing scheduled; routes: MEMBER 14, CHALLENGER TOUR EUROPE MEMBER 8, ? 2
- 2028: pro/full_time on MN_ALPS: 23 starts, 0 wins, $33,970 prize, world 1411 / amateur —; weeks: 23 played, 18 alternatives, 8 shut out, 0 training, 6 with nothing scheduled; routes: ALPS PRO TOUR MEMBER 12, MEMBER (draw) 10, ? 1
- 2029: amateur/part_time on AM_EUROPE: 10 starts, 2 wins, $0 prize, world 1840 / amateur 4; weeks: 10 played, 0 alternatives, 7 shut out, 20 training, 12 with nothing scheduled; routes: ? 6, OPEN AMATEUR ENTRY 2, AMATEUR RANKING 3 1
  - decision: back to amateur at 38 p=0.0529, runway=10.0, progress=0.26, desire=-1.25, net=-50421

### Thorbjørn Hansen (Denmark) — arrived unranked at 18 in 2028
- 2028: amateur/full_time on CO_US_D1: 21 starts, 2 wins, $0 prize, world 1399 / amateur 3; weeks: 21 played, 1 alternatives, 10 shut out, 16 training, 0 with nothing scheduled; routes: ? 8, OPEN AMATEUR ENTRY 5, COLLEGE LINEUP 4
- 2029: amateur/full_time on CO_US_D1: 20 starts, 1 wins, $0 prize, world 1662 / amateur 32; weeks: 18 played, 0 alternatives, 4 shut out, 22 training, 0 with nothing scheduled; routes: ? 12, COLLEGE LINEUP 5, OPEN AMATEUR ENTRY 1

### Jesper Björk (Sweden) — club professional outside North America
- 2027: club_pro/part_time on —: 9 starts, 2 wins, $12,641 prize, world — / amateur —; weeks: 9 played, 0 alternatives, 0 shut out, 25 training, 17 with nothing scheduled; routes: CLUB PROFESSIONAL 8, ORDER OF MERIT 45 1
- 2028: club_pro/part_time on —: 9 starts, 1 wins, $11,338 prize, world — / amateur —; weeks: 9 played, 0 alternatives, 0 shut out, 25 training, 17 with nothing scheduled; routes: CLUB PROFESSIONAL 8, ORDER OF MERIT 47 1
- 2029: club_pro/part_time on —: 8 starts, 1 wins, $9,709 prize, world — / amateur —; weeks: 8 played, 0 alternatives, 0 shut out, 26 training, 17 with nothing scheduled; routes: CLUB PROFESSIONAL 8

### Axel Berglund (Sweden) — international university golfer
- 2027: amateur/full_time on CO_INTL: 22 starts, 2 wins, $0 prize, world — / amateur 16; weeks: 22 played, 9 alternatives, 16 shut out, 7 training, 5 with nothing scheduled; routes: ? 8, OPEN AMATEUR ENTRY 7, COLLEGE LINEUP 5
- 2028: amateur/full_time on CO_INTL: 20 starts, 3 wins, $0 prize, world — / amateur 17; weeks: 19 played, 9 alternatives, 15 shut out, 11 training, 5 with nothing scheduled; routes: ? 9, OPEN AMATEUR ENTRY 6, COLLEGE LINEUP 3
- 2029: pro/full_time on MN_NORDIC: 27 starts, 3 wins, $185,270 prize, world 753 / amateur —; weeks: 26 played, 12 alternatives, 11 shut out, 2 training, 8 with nothing scheduled; routes: NORDIC PRO LEAGUE MEMBER 15, MEMBER (draw) 4, ? 4
  - decision: turned pro at 22 p=0.8983

### Richard Henderson (Canada) — reached the USA Amateur through open qualifying
- 2027: amateur/full_time on CO_US_D1: 24 starts, 0 wins, $0 prize, world — / amateur 91; weeks: 24 played, 2 alternatives, 6 shut out, 14 training, 0 with nothing scheduled; routes: COLLEGE LINEUP 15, ? 4, OPEN AMATEUR ENTRY 3
- 2028: amateur/full_time on CO_US_D1: 22 starts, 2 wins, $0 prize, world — / amateur 25; weeks: 22 played, 0 alternatives, 1 shut out, 23 training, 0 with nothing scheduled; routes: COLLEGE LINEUP 12, ? 4, OPEN AMATEUR ENTRY 3
- 2029: amateur/full_time on CO_US_D1: 21 starts, 1 wins, $0 prize, world — / amateur 81; weeks: 21 played, 0 alternatives, 3 shut out, 23 training, 0 with nothing scheduled; routes: COLLEGE LINEUP 16, ? 4, ORDER OF MERIT 21 1
  - decision: turned pro at 22 p=0.741

### Si-hyun Park (South Korea) — the most shut-out weeks in 2028
- 2027: pro/full_time on CH_ASIA: 24 starts, 2 wins, $544,195 prize, world 190 / amateur —; weeks: 23 played, 18 alternatives, 13 shut out, 3 training, 0 with nothing scheduled; routes: ASIAN CHALLENGER TOUR MEMBER 12, MEMBER 11, ? 1
- 2028: pro/part_time on MN_SE_ASIA: 8 starts, 1 wins, $369,187 prize, world 271 / amateur —; weeks: 8 played, 1 alternatives, 30 shut out, 5 training, 5 with nothing scheduled; routes: SOUTHEAST ASIA PRO SERIES MEMBER 4, HOME PLAYER 1, ? 1
- 2029: pro/full_time on MN_SE_ASIA: 24 starts, 9 wins, $1,323,693 prize, world 84 / amateur —; weeks: 24 played, 13 alternatives, 19 shut out, 1 training, 5 with nothing scheduled; routes: SOUTHEAST ASIA PRO SERIES MEMBER 16, ? 3, MEMBER (draw) 3
  - decision: part-time pro at 24 p=0.0035, runway=10.0, progress=0.99, desire=1.52, net=358066
  - decision: comeback at 25 p=0.0818

## Performance

Every shot is still simulated. Season one on this machine (4 worker processes): about 5.5 million holes
(3.3 million before the pass), 123-147 s for a full season including archive writes and checks
(103 s before). Speed-ups made in this pass with identical results: interpolation tables, faster
entries (eligible events prepared once per kind of golfer; fields kept sorted with running counts),
smaller worker payloads. Seasons two and three took 135-158 s. **The 120 s target is not yet met here**;
whether the intended hardware meets it is untested. The earlier 25-season runs slowed about 17% by season
25; this pass stops the weekly ranking and standings snapshots from accumulating, and the weekly session
now keeps only recent seasons in memory, but season 100 is untested.

## Remaining shortages and assumptions

- **Repeated denials** remain common for mini, Challenger and Regional professionals (wanting more weeks
  than their schedule): most of them reach their intended schedule, and the planner does not learn from
  being shut out.
- **Conditional Premier members** depend on Challenger alternatives, limited by the 10% visitor cap
  (owner: keep a limit).
- **Club professionals**: options in every golfing country; smaller countries hold only their floor of
  local events (3-8 a year).
- **Calendar density follows the starting nation pools**, not the nations as they evolve (M5).
- Evidence-backed patterns (real circuits): ranked priority categories with reshuffles, conditional
  status, season-ending tour championships, open qualifying with an entry standard for a national
  amateur, regional club-professional series. Tunable assumptions: full status 125, the 10% visitor
  share, event counts and field sizes, the local-golf rates and floors, the 1.5× open amateur expansion,
  the intended schedules, the flagship field sizes.
