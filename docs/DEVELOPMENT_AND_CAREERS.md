# Golf Legacy — Development, the Monthly Plan, Money and Careers

Code: `golfsim/development.py`, `golfsim/finance.py`, `golfsim/careers.py`, and the planner and weekly
development in `golfsim/season.py` (`Season(..., development=True)`).
Tests: `python tools/history_test.py --years 20` → `reports/WORLD_HISTORY_REPORT.md` (one world's story);
`python tools/cohort_study.py` → `reports/COHORT_STUDY.md` (career distributions across several worlds).

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
| **Rest** | No skill growth; fatigue recovers fully. |
| **Work** | A paid work week (only for full-time pros who are genuinely short of money): earns a wage, no skill growth. |

A **coach** (see `docs/COACHES_AND_CADDIES.md`) makes training count for more — most in their
speciality, and for young players if that is their gift — and helps the golfer see what to work on.

Growth also scales with a **learning rate** that is highest in the teens (1.2 at 18, 0.9 at 25, 0.6 at
30, 0.25 at 40) and with **work ethic** (a hard worker realises far more of their potential). Teenagers
also mature physically on their own, **every week, whatever they are doing** — resting and working
included.

**Golfers don't know their ceilings.** What to train, and whether a tournament or a training week helps
more, is decided from a *perceived* gap: the true gap seen through a persistent personal misreading,
wider for golfers with poor judgement of their own game (course management and coachability). The
outcome always follows the true ceilings.

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
| Sponsors, from player prestige (paid weekly) | Mini-tour entry fees (their purses are paid by entry fees); Q-School fees |
| A salary for part-timers ($52k) and club professionals ($65k) | A caddie: 8% of prize money on the bigger tours |
| Paid work weeks ($900) for full-time pros who are short | Living costs: $32k a year for a touring pro, $40k for anyone with a job (none for college golfers and teenagers at home) |
| Family / private backing drawn when savings run out | |

Money moves weekly when it is earned or spent, and every dollar passes through the golfer's ledger:
**cash at the end of a year = cash at the start + income − costs**, exactly.

**Money decides before it is spent.** Each golfer sees their *available funds*: savings, what is left of
any family or private backing, and a **limited** line of credit (it grows with their recent earned
income, up to $60k — nobody borrows without limit). The next four weeks of living costs are set aside
first. A trip they cannot pay for is not booked, however much they want to play. Expected prize money
comes from their own record (the share of purses they have actually been winning, discounted for fields
above their usual level), never from hidden ability, and it is never spent before it is won. How much
a dollar matters scales with their funds: a broke mini-tour player weighs a long trip heavily, a
millionaire barely notices. When funds run short, full-time players take paid work weeks instead of
training; when they can't cover the next weeks' living costs, they must. No tour card makes anyone
financially immune.

## Careers

Every career decision is a **probability built from what the golfer can see about themselves**,
combined smoothly. There are no age cut-offs, debt cliffs or tour-level immunities. The evidence is the
completed season, snapshotted **before** tour cards change (see `docs/SEASON_SYSTEM.md`).

| Factor | What it is |
|---|---|
| **Runway** | Years their funds would last chasing golf on their tour: costs and living against what their own record says it earns, plus their sponsor contract. "Self-funding" if income covers costs. |
| **Progress** | Promotion, a rising world ranking, wins and top-10s. Progress buys time **only in proportion to how well next season is funded** (runway up to a year): hope pays no bills. |
| **Opportunity** | The card they hold for next season (a Premier card is worth more than a mini tour's). |
| **Health** | Weeks lost to injury and lasting damage from serious injuries. |
| **Willingness** | Work ethic and appetite for the big stage. |
| **Life stage** | A smooth pull towards an ordinary life that grows through the mid-twenties and keeps creeping up — a curve, not a cut-off. |

| Decision | How it works |
|---|---|
| **Giving up the chase** (any tour) | The odds rise with money pressure (1 / (1 + runway)), life stage, poor health and a weak card, and fall with funded progress and willingness. The log records the runway and progress behind every decision. |
| **After stopping** | Some become **coaches or caddies** (see `docs/COACHES_AND_CADDIES.md`; rarely anyone who made a fortune). The rest take a job and keep playing a few local events as part-time pros, regain amateur status (more likely for those who never earned much from golf), or (with a strong mental game, from their mid-twenties) become club professionals. |
| **Comebacks** | A part-timer who wins or contends — often because their mental game has matured — may quit their job for another run. The odds come from those results, how much of a year on tour they could fund, age (smoothly) and willingness. No age limit and no savings threshold. |
| **Turning pro** | College eligibility ends at 22 — a **rule**, so every graduate must choose; the choice weighs their amateur ranking (observed standing), wins, means and willingness. Other amateurs turn pro on the same evidence, less often the further they are from their early twenties. |
| **Retirement** | Smooth in age for everyone (club pros mostly in their sixties; touring pros later the better their standing and card). Part-timers and amateurs who play less often and less well stop competing sooner — work and family crowd competition out. |
| **New juniors** | Every year a class of 18-year-olds arrives from every nation (each nation's pool, development and pathway decide how many and how good), selected on what scouts can see, not on hidden potential. |

Competition rules stay separate from choices: college eligibility, Q-School and tour cards decide where
a golfer *may* play; the decisions above decide whether they *want* to and *can afford* to.

Tours keep their size: when members retire or give up, the next best players from the level below are
called up.

## Every golfer has a history

Each golfer's career is logged: arriving at 18, wins, injuries (and any lasting damage), tour cards
won and lost, turning pro, giving up, comebacks, retiring. The history report prints full careers.

## Not built yet (see `docs/BACKLOG.md`)

Caddies and coaches as people (failed pros with great minds become caddies and coaches), coach
recommendations for training, the nation-improvement model, a fuller finance model (contracts,
bonuses, family support, regional costs of living).
