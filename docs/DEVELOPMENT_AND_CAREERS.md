# Golf Legacy — Development, the Monthly Plan, Money and Careers

Code: `golfsim/development.py`, `golfsim/finance.py`, `golfsim/careers.py`, and the planner and weekly
development in `golfsim/season.py` (`Season(..., development=True)`).
Test: `python tools/history_test.py --years 20` → `reports/WORLD_HISTORY_REPORT.md`.

The world now evolves: golfers improve toward their potential, age, get injured, earn and spend
money, turn professional, give up the chase, sometimes come back, and retire; a new class of juniors
arrives every year.

## Potential and development

Every attribute has a hidden **ceiling**; together the ceilings make the golfer's potential. Each week a
golfer does one thing:

| Week | What it does |
|---|---|
| **Play a tournament** | Every skill grows a little, the mental game most (×1.6). Growth is proportional to the gap to the ceiling, so **the more raw a golfer is, the more a tournament teaches them** (owner). |
| **Train a category** | Physical, long game, short game, putting or mental: that category grows fastest. Coachability makes training count for more; the mental game is harder to train away from competition. Part-timers with a job train at 30%. |
| **Rest** | No growth; fatigue recovers fully. |

Growth also scales with a **learning rate** that is highest in the teens (1.2 at 18, 0.9 at 25, 0.6 at
30, 0.25 at 40) and with **work ethic** (a hard worker realises far more of their potential). Teenagers
also mature physically on their own.

**Aging (yearly):** strength, stamina and recovery fade from about 3 years after a golfer's prime
(faster with a high aging rate), technique from about 8 years after; the **mental game keeps maturing
with experience into the late forties** — which is how a journeyman can be a better competitor at 34
than at 24. Long injuries (10+ weeks) can take some power, stamina and injury resistance away for good.

The development rates are calibrated so a typical golfer follows the age curve the starting world was
built on (improving fast to the mid-twenties, peaking around 27-33, declining from the mid-thirties).

## The monthly plan (owner)

At the start of every four-week block, each golfer plans the month. For every combination of weeks to
play they weigh:

- what each event is worth to their career (its prestige, home country, travel, their season plan),
- what playing or training does for their game (raw young golfers learn a lot from tournaments),
- the cost of playing tired (over a normal-schedule level) and the risk of injury, which climbs
  steeply with fatigue, low injury resistance, age and low stamina.

A week they don't play is a **training week** (in the category with most to gain — good course managers
and coachable golfers read their game better), or a **full rest week** when they are tired. Majors,
qualifiers and championships they are selected for are commitments and override the plan.

## Money

| Income | Costs |
|---|---|
| Prize money (amateurs take none) | Each event: travel and accommodation by level (×1.3 in the home region, ×1.8 overseas) |
| Sponsors, from player prestige | Mini-tour entry fees (their purses are paid by entry fees); Q-School fees |
| A salary for part-timers ($52k) and club professionals ($65k) | A caddie: 8% of prize money on the bigger tours |
| College golfers are on scholarship | Living costs: $32k a year for a touring pro, $40k for anyone with a job (none for college golfers and teenagers at home) |

Savings carry over and can go negative (debt). Typical year: a Premier Tour player nets ~$800k with
millions saved; a Challenger player roughly breaks even; mini-tour and regional players lose money —
which is what eventually makes them stop.

## Careers (owner)

| Decision | How it works |
|---|---|
| **Turning pro** | College golfers graduate at 22; most decent graduates try (the best by amateur ranking almost always), the very best starting on a Challenger tour, the rest on regional or mini tours. Young amateurs outside college turn pro when they are ranked highly or play well enough. |
| **Giving up the chase** | Full-time pros below the Challenger tours weigh money against hope. Young players keep chasing whatever it costs; from about 25-27, losing money year after year (and running out of savings) makes them stop. Hard workers hold on longer, and so does anyone who is climbing. A regional card is a living for many, so they stop less often — unless they are in debt. Anyone over 23 more than $50k in debt usually stops. |
| **After stopping** | They take a job and either keep playing a few local events as part-time pros, regain amateur status, or (with a strong mental game) become club professionals. Part-timers only play events near home. |
| **Comebacks (rare)** | A part-timer aged 25-40 who wins or contends locally — often because their mental game has matured — and has some savings may quit their job and make another run at it. A few a year in a world of thousands. |
| **Retirement** | Full-time pros from their mid-forties (earlier without a good card), club pros in their early sixties, amateurs and part-timers around sixty. |
| **New juniors** | Every year about 175 18-year-olds arrive from every nation (each nation's pool, development and pathway decide how many and how good) and go to college or amateur golf. |

Tours keep their size: when members retire or give up, the next best players from the level below are
called up.

## Every golfer has a history

Each golfer's career is logged: arriving at 18, wins, injuries (and any lasting damage), tour cards
won and lost, turning pro, giving up, comebacks, retiring. The history report prints full careers.

## Not built yet (see `docs/BACKLOG.md`)

Caddies and coaches as people (failed pros with great minds become caddies and coaches), coach
recommendations for training, the nation-improvement model, a fuller finance model (contracts,
bonuses, family support, regional costs of living).
