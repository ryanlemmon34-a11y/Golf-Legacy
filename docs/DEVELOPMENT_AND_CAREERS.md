# Golf Legacy — Development, the Monthly Plan, Money and Careers

Code: `golfsim/development.py`, `golfsim/finance.py`, `golfsim/careers.py`, and the planner and weekly
development in `golfsim/season.py` (`Season(..., development=True)`).
Tests: `python tools/history_test.py --years 20` → `reports/WORLD_HISTORY_REPORT.md` (one world's story);
`python tools/long_world.py` → a run directory with `REPORT.md` / `DEBUG.md` (whole worlds for decades,
checked every season); `python tools/development_audit.py` → `reports/DEVELOPMENT_AUDIT.md`.

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

**Competition teaches what practice cannot.** Composure, resilience, course management, focus and
tournament consistency (striking and putting) train only as far as a golfer's **competitive experience**
supports: their competitive rounds over the last 52 weeks, full at 40 rounds. With no recent competition,
practice builds a little consistency (15%) and no pressure skills at all; technique, the short game and
physical work train the same either way. Tournaments still teach every skill directly. So a golfer who
only trains falls short of their potential, one who only plays leaves technique on the table, and a mix
develops best — measured in `reports/DEVELOPMENT_AUDIT.md` (section 4: 18 to 30, the same golfers on
balanced, light, tournament-only, training-only and no-event schedules). Development sees what a golfer
did, not why: a season without events costs the same whether the fields were full or they chose to stay
home. (The starting world assumes everyone's season before it was typical for their lifestyle; new
juniors arrive with a junior season of competition behind them.)

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
with competitive experience into the late forties** — each year in proportion to the competitive rounds
actually played (none without competition; green reading half of it regardless) — which is how a journeyman can be a better competitor at 34
than at 24. Long injuries (10+ weeks) can take some power, stamina and injury resistance away for good —
the longer the injury, the likelier (about 15% at 10 weeks, 60% at 20, 85% at 30).

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

**Intended schedules** (owner): college golfers play a lot (about 24 starts a year: college events and
amateur events around them), other full-time amateurs a little less (16), part-time amateurs about 8
around a job, club professionals about 12 of the many local events open to them; professionals 19–27
by stamina. The monthly plan works towards them; the calendar is sized so they are reachable
(`docs/COMPETITION_ACCESS.md`).

## Money

| Income | Costs |
|---|---|
| Prize money (amateurs take none) | Each event: travel and accommodation by level (×1.3 in the home region, ×1.8 overseas) |
| Sponsors, from player prestige (paid weekly) | Mini-tour entry fees (their purses are paid by entry fees); Q-School fees |
| A salary for part-timers ($52k) and club professionals ($65k) | A caddie: 8% of prize money on the bigger tours |
| Paid work weeks ($900) for full-time pros who are short | Living costs: $32k a year for a touring pro, $40k for anyone with a job (none for college golfers and amateurs living at home) |
| Family / private backing drawn when savings run out | |

Money moves weekly when it is earned or spent, and every dollar passes through the golfer's ledger:
**cash at the end of a year = cash at the start + income − costs**, exactly.

**Money decides before it is spent.** Each golfer sees their *available funds*: savings, what is left of
any family or private backing, and a **limited** line of credit (it grows with their recent earned
income, up to $60k — nobody borrows without limit). The next four weeks of living costs are set aside
first. A trip they cannot pay for is not booked, however much they want to play — **one rule for
every entry, qualifier and invitation** (majors, elite and national amateur championships, the Tour
Finals): an invited golfer who cannot pay declines (recorded) and the next in line or the next alternate
takes the place. College events are paid by the school, never blocked by a golfer's debt, and the school
is recorded as the payer. Expected prize money
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
| **Runway** | Years their funds would last chasing golf on their tour: trips (with a caddie's fees) and committed costs (living, a contracted coach) against the prize money their own record says they keep (net of staff shares) and their sponsor contract. "Self-funding" if income covers costs. |
| **Progress** | Promotion, a rising world ranking, wins and top-10s. |
| **Opportunity** | The card they hold for next season (a Premier card is worth more than a mini tour's). |
| **Secured** | A significant event already secured for next season through a real route: a major title, a Premier Tour win, a world top-50 finish (Tour Masters invitation). |
| **Health** | Weeks lost to injury and lasting damage from serious injuries. |
| **Willingness** | Work ethic and appetite for the big stage. |
| **Life stage** | A smooth pull towards an ordinary life that grows through the mid-twenties and keeps creeping up — a curve, not a cut-off. |

| Decision | How it works |
|---|---|
| **Giving up the chase** (any tour) | Money pressure (1 / (1 + runway)) weighed against their **desire to continue** — progress, the card earned, a secured event, health, willingness and life stage. Desire is kept separate from funds: an improving golfer may willingly accept another losing season, but desire creates no money — what they can actually enter is still decided week by week by what they can afford, and their credit stays limited. Every decision is recorded with its reasons (probability, runway, progress, desire, what was secured). |
| **After stopping** | Some become **coaches or caddies** (see `docs/COACHES_AND_CADDIES.md`; rarely anyone who made a fortune). The rest take a job and keep playing a few local events as part-time pros, regain amateur status (more likely for those who never earned much from golf), or (with a strong mental game, from their mid-twenties) become club professionals. |
| **Comebacks** | A part-timer who wins or contends — often because their mental game has matured — may quit their job for another run. The odds come from those results, how much of a year on tour they could fund, age (smoothly) and willingness. No age limit and no savings threshold. |
| **Adult amateurs take jobs** | Amateurs outside college live at home on savings and family help, with no salary. Each year they may take a job and keep playing as part-time amateurs ($52k salary, $40k living): smooth in age (rare at 19-20, likely by the mid-twenties), likelier in debt or with a short runway, less likely with money to keep going. Recorded as a career transition ("amateur took a job"); their chance of turning professional is decided first. |
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
