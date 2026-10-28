# P0 check: 5 seasons, seeds 2027 and 3031 (full population, every shot simulated)

A short integration check of the P0 pass (competition access, development needs competition, adult
amateur livelihood and invitation costs), run with `tools/long_world.py --seeds 2027 3031 --years 5
--mature 5 --strict` on engine commit `4b92c94`. Every season passed the in-run checks (cash reconciles,
staff payments = receipts, no staff invariant violations, population reconciles). This is not a long
run and not evidence about decades or centuries.

## Before / after (the first five seasons of the earlier 25-season worlds vs this run)

"Before" is the 25-season runs at `5954216` (`reports/long_world_25y`), seasons 2028-2031 (season two on).
Zero-start = share of golfer-seasons at that level with no event.

| | 2027 before | 2027 after | 3031 before | 3031 after |
|---|---|---|---|---|
| College: no start | 6.1% | 0.0% | 8.2% | 0.0% |
| Amateur (full-time): no start | 1.2% | 0.8% | 3.3% | 0.4% |
| Amateur (part-time): no start | 20.2% | 0.2% | 19.3% | 0.0% |
| Mini / Challenger / Regional: no start | 0.8 / 1.0 / 1.0% | 1.0 / 1.1 / 0.8% | 0.8 / 0.7 / 1.1% | 0.7 / 0.8 / 0.9% |
| New 18-year-olds: no start in their first season | 10.2% | 0.0% | 12.9% | 0.0% |
| New 18-year-olds: ranked by the end of it | 84.7% | 97.3% | 82.0% | 96.3% |
| New 18-year-olds: median events in their first season | 4 | 10 | 5 | 10 |
| Amateurs more than $20k in debt (golfer-seasons) | 10 | 0 | 7 | 0 |
| Lowest amateur savings | −$29,961 | −$12,669 | −$37,235 | −$17,236 |
| Adult amateurs who took a job | — | 178 | — | 167 |
| Change in overall per season, 18-21 / 22-25 / 26-30 | +1.23 / +0.41 / +0.09 | +1.20 / +0.37 / +0.06 | +1.28 / +0.42 / +0.08 | +1.25 / +0.38 / +0.06 |
| Top-10 / top-100 mean overall after five seasons | 86.9 / 79.6 | 87.0 / 79.6 | 88.2 / 80.0 | 88.2 / 80.0 |
| Majors / different winners (5 seasons) | 20 / 17 | 20 / 14 | 20 / 15 | 20 / 12 |

(Over 25 seasons the earlier runs reached −$167k for an amateur through invitation fields that skipped the
affordability check; that path is closed.)

## What the new diagnostics show (REPORT.md section 3b, DEBUG.md)

- **Blocked vs choice.** No level has more than ~2% of seasons with no start because fields were full.
- **Rationing below the top.** Of the weeks golfers planned to play a regular event, the share in which every
  field they tried was full: Premier 36%, Challenger and Regional ~41%, amateurs 37-49%, college 64%, mini tours
  ~70%. Everyone gets starts (median rounds a season: college 33, mini 19-20, Challenger ~72, Premier 52-54),
  but at the lower levels many planned weeks become training weeks. On the Premier Tour it comes from weeks
  with a single Premier event in the world (144-156 places for 300 members). Mini tours are paid for by
  entry fees, so their fixed fields are the likeliest candidate to revisit.
- **Club professionals outside North America** have almost no events (87-91% of their seasons without a
  start): the club-pro sectionals and championship are in the USA only. A calendar gap, unchanged by this
  pass.
- **Development by competitive rounds** (ages 18-30 with room to grow): more rounds go with more growth,
  most clearly at 24-30 (+0.15 a season with none, +0.26 with 1-20 rounds, +0.6 with 41+). Selection is mixed in:
  golfers who play more also have cards, money and form.
