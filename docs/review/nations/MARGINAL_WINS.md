# A single big win against a nation's whole season (Test2, fixed inputs)

**Question.** NATIONS.md says that under rules 2026-11-14, a lone Premier-tour win by a nation with many below-par starts
does not lift that nation's prestige. That sentence mixes two different things:
- the **marginal** effect of the win: the same season with and without it;
- the nation's **net** prestige, set by all of its starts.

This note separates them. Each season is the five-season window ending that year, with A and E as archived and P
recomputed. Expectations E stay as they were set before the event. The counterfactual season replaces the win with an
even-share result for that start: the site's fame divided by its starters. Removing the win's fame entirely gives
almost the same figures.

| season | nation (win) | case | before (R alone) | now (2/3 Q + 1/3 R) | Q | R |
|---|---|---|---|---|---|---|
| 2030 | Norway (Nordic Masters, prestige 68.2: 31.7 fame) | as played | 49.96 | 47.46 | 0.900 | 0.999 |
| 2030 | Norway | the win replaced by an even-share result | 48.34 | 45.85 | 0.861 | 0.955 |
| 2030 | India (Netherlands Open, 68.5: 32.1) | as played | 48.24 | 45.74 | 0.859 | 0.952 |
| 2030 | India | the win replaced | 47.05 | 44.55 | 0.831 | 0.921 |
| 2031 | Belgium (Canada Open, 86.5: 64.7) | as played | 46.69 | 44.72 | 0.841 | 0.912 |
| 2031 | Belgium | the win replaced | 42.46 | 40.49 | 0.747 | 0.811 |
| 2029 | Mexico (USA Open, a major, 97.5: 92.8) | as played | 53.63 | 53.57 | 1.103 | 1.106 |
| 2029 | Mexico | the win replaced | 50.64 | 50.58 | 1.015 | 1.018 |

**What the win adds** (as played minus the win replaced):

| | before | now |
|---|---|---|
| Norway's Nordic Masters | +1.62 | +1.61 |
| India's Netherlands Open | +1.19 | +1.19 |
| Belgium's Canada Open | +4.23 | +4.23 |
| Mexico's USA Open | +2.99 | +2.99 |

So the marginal effect of a big win is essentially **the same under both rules**: the new rule does not count wins for
less.

**Why the levels differ.** The gap between the rules is in the nation's level, before any win: Norway sits about 2.5
points lower under the new rule. That comes from its other 1,175 starts in 2030. Across all of them it won
less than an even share of the fame on offer (Q 0.90), and visible achievement now carries two thirds of the
weight. Under R alone, that shortfall was largely excused by the modest ability-based expectations of the same
golfers (R about 1.0).

So the earlier note's limitation describes Norway's **net** standing: a nation whose golfers mostly fall short in
the events they enter stays below 50 even in a season with a Premier win. It is not a smaller reward for the
win. No design change is proposed here; this is for review.
