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
| Family help, and for professionals **backers**, drawn when savings run out | Backers' share: 25% of prize money while a backing deal lasts |

**Backers.** As in real life (about three in four players trying to make it are backed by family,
friends or investors), professionals chasing the game can have a backing deal: backers put up
$15k–50k a season (topped up each 1 January, drawn only when the golfer's own cash runs out, before
any family money) for 25% of their prize money while the deal lasts. Backers' money is kept apart from
family money: when a deal ends, what is left of the backers' money goes back to them together with their
share of winnings; family money stays the golfer's. About three in four find backers when they turn
professional (more often with a better amateur ranking); in the starting world, professionals below the
Premier Tour are backed in the same proportion for their age. Backers are less willing the older the
golfer, smoothly (half as willing at 31 as at 22, never a cut-off; an uncalibrated assumption). Each
winter backers decide with bounded odds from what they can see (`careers.p_backers_continue`): progress
(promotion, a rising world ranking, wins, top-10s), places already secured, how far the season's losses
outrun the deal, their own patience (drawn with each deal), seasons in a row without progress, and age.
Progress almost always renews a deal; flat seasons make withdrawal likelier, never certain. A deal also
ends when the golfer pays their own way — judged without the support being withdrawn
(`careers.own_way`): their own cash must pay for the first quarter of the season's costs before any
winnings arrive, and then either their winnings *proven at that level* (eight or more events there,
counted cautiously) and sponsors cover a season, or their sponsor contract alone does, or their own savings
(not family money, not the backers', not credit) cover three seasons of losses with no winnings counted
at a level they have not proven; the history says which. A new card raises the golfer's desire to
continue and their opportunities, but is not yet an income. A professional
without backers can attract them with a breakthrough season (a win, promotion or a big ranking jump; the
younger, the likelier), or once they need them: with less than a season of their own money, odds grow
with their world ranking and youth (not within two winters of a deal ending). The starting world gives
no deal to a professional whose savings already cover three seasons of losses: backers come when needed.
Every deal, renewal and withdrawal is in the golfer's history. Club professionals' own events (section
events, their championships and sectionals) are paid for by their club.

Money moves weekly when it is earned or spent, and every dollar passes through the golfer's ledger:
**cash at the end of a year = cash at the start + income − costs**, exactly.

**Money decides before it is spent.** Each golfer sees their *available funds*: savings, what is left of
any family or private backing, and a **limited** line of credit (it grows with their recent earned
income, up to $60k — nobody borrows without limit). The next four weeks of living costs are set aside
first. A trip they cannot pay for is not booked, however much they want to play — **one rule for
every entry, qualifier and invitation** (majors, elite and national amateur championships, the Tour
Finals): an invited golfer who cannot pay declines (recorded) and the next in line or the next alternate
takes the place. College events are paid by the school, never blocked by a golfer's debt, and the school
is recorded as the payer (a club professional's section golf likewise, by the club). A week has one
budget: every entry accepted books its cost at once, so a Monday qualifier and that weekend's
tournament are not both paid from the same money, and a qualifier is priced at the site the golfer is
sent to (England or Japan for the USA Open's international final qualifying). A caddie's weekly fee is
paid once a week, however many events.

**Debt.** The credit limit bounds what a golfer *chooses* to spend. Living costs and a contracted
coach's fee are charged weekly whatever their funds, so a golfer with no income can go past their
credit. An injured touring professional who needs money does light paid work while recovering (the
same wage as any work week; the injury heals no slower), so injury alone no longer runs up debt. Debt is
kept exactly (never erased), nobody new pays it, it blocks every chosen cost until it is repaid, and it
weighs smoothly on the end-of-season decision through the runway; no debt threshold forces retirement
or a change of life, and careers change only at the end of a season. Expected prize money
comes from their own record, kept by level of competition (the share of purses they have actually won
against Premier, Challenger, regional or mini-tour fields, and in how many events): at a level they have
not played, their record elsewhere is translated (half the share one level up, twice one level down) and
counts for less, so a promotion forecast is uncertain until they have played there. A season's
prize money is kept by the level it was won at: a Premier member's winnings on a Challenger tour are
Challenger evidence, never proof of what they earn on the Premier Tour. **Evidence recency:** a
level's evidence halves for every full season the golfer has not played there, so after years away an
old record (however many events) no longer counts as proven, and on a comeback the recent events decide
(the share they win is mostly the last five events' anyway). Never from hidden
ability, never for amateurs (who take no prize money and have no sponsor contracts), and never spent
before it is won. Forecasts, the caddie budget, affordability and payments use the same definitions
(`Season.season_forecast`, `sponsor_income`, `tour_trip_cost` over `finance.event_cost`, which knows
when a school or club pays). How much
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
| **Secured** | Places in next season's majors already earned, by the majors' own rules (`qualification.secured_places`: every exemption route of `qualification.RULES` applied to what is known at the end of the season) — past champions' exemptions while they last, a top-10 finish in the USA Open, a Premier Tour win inside a major's window, the year-end world top 50. Routes decided by a ranking or points list not yet published (`cutoff`) and qualifying stages still to be played never count; an amateur title's place is kept apart with its condition ("if still an amateur") and does not count — unless the same golfer also earned that major outright (a top-ten USA Open, say): then the place is guaranteed and the amateur title is listed as support. Each place is in the golfer's history and in the backer and career decisions' evidence. |
| **Health** | Weeks lost to injury and lasting damage from serious injuries. |
| **Willingness** | Work ethic and appetite for the big stage. |
| **Life stage** | A smooth pull towards an ordinary life that grows through the mid-twenties and keeps creeping up — a curve, not a cut-off. |

| Decision | How it works |
|---|---|
| **Giving up the chase** (any tour) | Money pressure (1 / (1 + runway)) weighed against their **desire to continue** — progress, the card earned, a secured event, health, willingness and life stage. The runway counts only savings and backers' money (next season's deal included), not the line of credit, which pays for a few weeks, not another season: with less than a season of money of their own, the pressure rises (smoothly, no cliff), so a broke player without backers usually stops chasing rather than lingering unable to afford events. Desire is kept separate from funds: an improving golfer may willingly accept another losing season, but desire creates no money — what they can actually enter is still decided week by week by what they can afford, and their credit stays limited. Every decision is recorded with its reasons (probability, runway, progress, desire, what was secured). |
| **After stopping** | Some become **coaches or caddies** (see `docs/COACHES_AND_CADDIES.md`; rarely anyone who made a fortune). The rest take a job and keep playing a few local events as part-time pros, regain amateur status (more likely for those who never earned much from golf), or (with a strong mental game, from their mid-twenties) become club professionals. |
| **Comebacks** | A part-timer who wins or contends — often because their mental game has matured — may quit their job for another run. The odds come from those results, how much of a year on tour they could fund, age (smoothly) and willingness. No age limit and no savings threshold. |
| **Adult amateurs take jobs** | Amateurs outside college live at home on savings and family help, with no salary. Each year they may take a job and keep playing as part-time amateurs ($52k salary, $40k living): smooth in age (rare at 19-20, likely by the mid-twenties), likelier in debt or with a short runway, less likely with money to keep going. Recorded as a career transition ("amateur took a job"); their chance of turning professional is decided first. |
| **Turning pro** | College eligibility ends at 22 — a **rule**, so every graduate must choose; the choice weighs their amateur ranking (observed standing), wins, means and willingness. Other amateurs turn pro on the same evidence, less often the further they are from their early twenties. |
| **Retirement** | Smooth in age for everyone (touring pros later the better their standing and card). Golfers with a job (part-timers, adult amateurs, club pros) stop competing for their own reasons: age, health, willingness, progress, and whether they still play. Choosing not to play when events were there (drifting away) counts strongly; finding nothing they could enter counts a little (frustration), never as lost interest. *Uncalibrated assumptions*, roughly: a regular part-timer of 30 stops about 4-5% a year, one who plays nothing though events were there about 45%, one who found nothing to enter about 15%; club pros under 1% a year until their mid-forties, about 5% at 55, 12% at 60 (`careers.p_retire`, `careers.participation`). Not tuned to hold the population or runtime down. |
| **New juniors** | Every year a class of 18-year-olds arrives from every nation (each nation's pool, development and pathway decide how many and how good), selected on what scouts can see, not on hidden potential. |
| **New professionals** | Every year about 450 golfers aged 21-26 turn professional from outside the tracked amateur game (small colleges, academies, club and late-developing golfers, countries without college golf) and start on their home mini tour, with savings and perhaps backers (`population.new_professionals`). Each nation sends them in proportion to its golf scene, drawn exactly as the starting world draws its young professionals; golfers the junior class would have kept are left out. It is a steady flow (`NEW_PRO_SCALE`), not a top-up: real lower tours churn, and without it they empty within a decade because their players stop chasing within a few years. |

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
