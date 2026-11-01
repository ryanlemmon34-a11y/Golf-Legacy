# Nations: carried quota fractions and visible achievement (Test2 fixed-input evidence)

Two changes approved in direction by the owner (31 October, 23:46 UTC, via HAL). Both are in `build/v17-nations`. The
weights are provisional and easy to iterate; nothing here is an empirical calibration. Everything below holds the
archived inputs of the Test2 world (seed 386509, engine 1949ff63, 57 seasons) fixed. It isolates each measure, and
does not show what a re-simulated world would do.

## 1. Carrying each nation's fraction forward (rules 2026-11-13)

**The defect.** Each year's fixed cohort total was split by shares with largest-remainder rounding, and the fractions
were thrown away every year.
- 14 nations with positive shares never received a newcomer in 57 seasons. Their combined entitlement was 251.11
  golfers.
- Some mid-sized nations were over-allocated year after year. Kenya received 112 juniors against 67.6 entitled.

**The change** (`population.allocate_with_carry`).
- A nation's entitlement is its quota plus its carry. It gets the whole part, then the largest remaining fractions.
  Ties go to the larger quota, then by name.
- The carry after a year is the entitlement minus the places given.
- The total is exact. The carries keep their sum (zero from a world's start) and each stays within (−1, 2).
- There is no minimum place, no extra golfers, and talent is untouched.
- A ledger that would break those postconditions is rejected before anything is generated or recorded
  (`CarryLedgerError`, from the review's exact-fraction repro).

**Replay** (`carry_replay.py`, output in `CARRY_REPLAY.md`):

| | Year-by-year rounding | Carry-forward |
|---|---|---|
| Nations never given a newcomer | 14 | 0 |
| Worst cumulative gap (quota against places) | 26.09 (Kenya juniors) | 0.592 |

Examples: Morocco 0 → 34, Poland 0 → 28, Peru 0 → 25, Fiji 0 → 18; Kenya 112 → 68, Brazil 111 → 68.

## 2. Visible achievement first (rules 2026-11-14)

**The defect.** National prestige was R = (A + 150) / (E + 150): actual fame against an expectation built from each
starter's current ability. A dominant champion is expected to win, so winning everything earns nothing.
- Argentina in 2055 won all four majors. A was 920.93 against E of 939.10, and its prestige was 41.5.
- During the Cárdenas era Argentina's share shrank.

**The change** (`participation.nation_prestige_achievement`).
- Each starter is also credited with an even share of the site's fame, ignoring ability (P). P is what a start there is
  worth on average.
- Q = (A5 + 150) / (P5 + 150) is fame won per fame on offer in the starts made. The 5-season window and its weights
  (1.0 … 0.6) are unchanged.
- prestige = 50 + 25 × (⅔ log2 Q + ⅓ log2 R), within 0–100.
- Unchanged: the multiplier's bounds (0.25–4), its step (×1.1 a year) and the total population rule.

**Why this normalisation.**
- Q is per start. Twice as many golfers of the same quality bring twice the fame and twice the fame on offer, so a
  nation cannot snowball through volume. A test checks this.
- A major counts in proportion to its fame (prestige cubed). Argentina 2055: majors 374.72 won against 13.34 on offer;
  in all, 920.93 against 231.32.
- R stays at a third of the weight, so beating or missing a realistic expectation still counts.
- The pseudo-count of 150 steadies small samples.

**Replay** (`replay.py`, output in `REPLAY.md`). The "before" replay reproduces the archived prestige to within 0.008
across 3,249 nation-seasons.

- **Argentina.** Prestige 53–74 during 2043–2070, against 35–54 before; the multiplier peaks at 1.92 in 2055.
  - It fades to neutral within about 7 seasons of its last major in 2070 (61.0 → 49.5 by 2077).
  - 2055 broken down: Q part +26.4, R part −2.8 → 73.6 (before: 41.5).
  - 2055 counterfactual without the four majors: 69.5. Its tier-1 events that season (373.7 won against 30.7 on
    offer, 13 starts) and the rest of the 5-season window still carry it.
- **Lower-tier volume.** Starts won at an even share are neutral on their own, but they dilute Q toward 1. Argentina
  2055 with +1×, +2× and +5× such starts: 66.3, 62.5, 57.4.
- **Small breakthroughs (limitation).** A lone Premier-tour win by a nation with hundreds of below-par lower-tier
  starts does not lift its prestige. Norway 2030 goes 50.0 → 47.5; India and Belgium also end slightly lower than
  before.
  - A major moves a nation more: Mexico 2029 stays at 53.6 under both rules.
  - Restricting Q to majors and tier-1 events made this worse (Norway 43.2) and concentrated shares more (USA 36.1%).
    That variant was rejected.
- **Concentration and bounds.** USA's starting juniors share is 33.59%.

  | | USA share 2084 | USA share max | Top-5 share 2084 | Nation-seasons at cap / floor | Multipliers 2084 | Nations below 45 |
  |---|---|---|---|---|---|---|
  | Before | 34.00% | 35.75% | 60.6% | 0 / 0 | 0.845–1.202 | 3 |
  | Now | 34.96% | 36.58% | 60.8% | 0 / 0 | 0.743–1.200 | 8 |

**Still to measure.** A bounded fresh-world run with both rules on would show the re-simulated effect, for example two
seeds over a few seasons. It is not part of this fixed-input evidence.

## Files

| File | What it is |
|---|---|
| `carry_replay.py`, `CARRY_REPLAY.md` | the rounding replay |
| `extract_fame.py` | recomputes A, P, starts, wins, and fame by class per nation-season from the archived finishes, read only |
| `test2_fame_by.json.gz` | its output |
| `replay.py`, `REPLAY.md` | the prestige replay |
| `tests/data/test2_nation_shares.json.gz` (on the nations branch) | the archived shares, totals and A, E |
