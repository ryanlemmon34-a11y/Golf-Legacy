# Golf Legacy — Coaches and Caddies

Code: `golfsim/staff.py` (the people, the yearly market, former golfers joining the profession), hooked
into `golfsim/season.py` (fees, caddies on the bag, coaching in development and planning),
`golfsim/careers.py` (golfers becoming coaches or caddies) and `golfsim/development.py`.
Tests: `tests/test_staff.py`.

## Coaches

| | |
|---|---|
| **Speciality** | One of the training categories: physical, long game, short game, putting or mental. |
| **Young players** | About a quarter of coaches specialise in developing golfers aged 22 and under. |
| **Teaching** (shown from rules 2026-11-02) | How much their coaching helps (0-100). |
| **Scouting** (shown from rules 2026-11-02) | How well they read a young player's prospects from what can be watched (0-100); it never reveals the player's hidden potential. |
| **Reputation** (seen) | What golfers can see when choosing; it follows their students' success (fame, progress). It sets the fee: about $15k a year at 50, $45k at 80, $70k at 95. |
| **Clients** | How many players they coach individually: about 6 (4-8) by their availability and how intensively they work — separate from how well they teach. A tuning assumption to check against long runs, not a real-world limit. |

**One coach at a time.** Coaching quality for a week of training = teaching, +0.15 in their speciality,
+0.15 for a young player if that is their gift (at most 1). Without a coach a golfer teaches themselves
(0.3). The training multiplier is 1 + 0.5 × max(0, quality − 0.3): teaching yourself keeps the 1.0 the
world's development rates were calibrated on, an ordinary coach adds about 10%, a strong specialist in
their speciality (or a youth specialist with a teenager) about 30%; a weak coach is no worse than none.
Because tournaments and maturation drive much of a young golfer's growth, a whole season's development
differs by about 5-12% between no coach and a strong specialist (`reports/DEVELOPMENT_AUDIT.md`). (The
first version used 0.7 + 0.6 × quality, which quietly slowed every uncoached golfer to 0.88; corrected.) A coach also helps a golfer **read their own
game**: the golfer's misreading of where their room to improve lies narrows to the coach's teaching
level, so they pick better things to work on.

**Getting a coach** (every season, before it starts):

1. **Scouting.** Each coach with room looks at up to 60 young players (23 and under) near them (their
   country; well-known coaches their whole region). They judge where a player is heading from what they
   can watch — current level (seen with some error), the growth typical for the player's age, and how
   much the player really improved over the last year — through the noise of their own scouting skill,
   **never the player's hidden potential**. A coach's opinion of a player persists (a fixed personal
   misjudgement plus a small yearly wobble) rather than being re-rolled every winter, and **firms up with the
   seasons they have watched that player** (from rules 2026-11-04: the error × 1/√(1 + 0.5 × (seasons − 1)),
   at most six seasons); a coach keeps following up to 20 promising players from earlier winters among the 60.
   They approach young, *raw* players they believe can reach about Challenger standard (where a share of prize
   money is worth something), and no more than a third of a coach's book is unpaid share deals (the better
   the coach, the higher their bar). **Development coaches** (the youth specialists) rank those prospects by
   the room to grow they see and last year's rise; **coaches of established players** by achievement anyone
   can see (Prestige, a world or amateur ranking), a known fit from working together before and earned major
   places — never potential. The player answers: most accept a share deal (it costs nothing now), fewer while
   a college team coaches them or when last season's prize money makes a share costly; a player who already
   has a coach weighs the newcomer's extra reputation against the partnership's **loyalty** (below). The coach
   works for free in return for **5% of future prize money**.
2. **Hiring.** Golfers who want a coach (coachability, and almost every tour professional) hire the
   best-looking coach they can afford: the fee must fit 10% of their **means** (spendable funds plus 80% of
   last year's earned income — money they have, not winnings they hope for). They see reputation, not teaching skill, and look for a speciality matching
   what *they believe* is their weakest area. The best-known players choose first, asking the coaches they
   like best in turn. **A coach may say no** (from rules 2026-11-04): rarely while their book has room; as it
   fills they keep the places for the players they look for (a development coach: young players with
   promising growth; the others: established results and major places), and a known poor fit counts against.
   Many college players and most amateurs therefore have no coach.
3. **Leaving.** Golfers who can no longer afford the fee leave; a difficult season (falling ranking,
   relegation) sometimes ends the relationship; coaches retire (smoothly with age, from the late sixties).

## Caddies

A caddie has the six skills the shot engine has always modelled: **strategy** and **yardage** (decision
quality — course management), **mental support** (how much pressure costs and how long a bad hole
lingers — composure), **green reading** (putting reads), **course knowledge**, and **communication**
(how much of it reaches the player). A caddie builds **familiarity with every course they work** — stroke-play rounds, match-play holes and
playoff holes alike (in rounds' worth) — exactly as players do; in the engine the player benefits from the caddie's familiarity on top
of their own. Caddies gain a little skill with experience — in proportion to the rounds they actually worked that
season (none for an idle year), growing towards 95 and never pulling a higher skill down — until about 50 and stop caddying smoothly
with age (around 60).

Full-time professionals on the Premier and Challenger tours hire a caddie each season: the best-known
players first, each offering the bag to a caddie they worked well with before, then to the best-looking
caddies they can afford (a weekly fee of $800 + $25 per reputation point, plus 8% of prize money). **A
caddie may say no** (from rules 2026-11-04): they weigh expected earnings (the golfer's last season's prize
money or Prestige, on the scale their own reputation follows), compatibility (the pair's fit and time
together, where they worked together before) and stability (a Premier card), and grow readier to accept
with each bag they turn down that winter. A caddie's reputation follows their employer's prize money.
A difficult season can cost a caddie the bag. **Everyone else carries their own bag** (or a friend
does): skills of 40 — weaker help than any professional caddie, where before everyone silently had an
average (50) caddie.

## Former golfers become coaches and caddies

When a professional gives up the chase or retires, they may join the profession instead of leaving the
game:

- **Coach:** more likely with a teaching mind (course management, green reading, coachability, work
  ethic); speciality = the strongest part of their own game; reputation starts from how good they were.
- **Caddie:** more likely with course management, composure and green reading, and when younger.
- **The best players rarely do it:** both chances fall away with savings (×e^(−savings / $1.5M)) — a
  golfer who made a fortune does not need the money.

Their history says so ("Became a caddie"), and the new coach or caddie keeps the golfer's name and a
link to their playing career.

## Initialization and outside recruits (explicit)

The world has no recorded past, so the starting coaches (~480, by each nation's golf pool, sized so the
first season's paying demand largely finds room) and caddies (~1,450, by where tour players come from)
are generated with a background ("a teaching professional", "a club caddie"). Outside recruits are
generated and labelled "(outside recruit)" only for real unmet demand: caddies where tour players
outnumber caddies, and coaches where golfers who could pay found every coach they could afford full
(one recruit per six such golfers). Scouting does not create coaches.



## Relationships, continuity and changes

Every arrangement is a dated **stint** shared by both profiles (`docs/HISTORY_AND_PERSISTENCE.md`), and
every result keeps the coach and caddie the golfer had that week.

**Working relationship.** Each pair keeps the time they actually worked together (coaching weeks used,
rounds on the bag) and a fixed fit. It grows with real work, with diminishing returns, fades with
years apart (a reunion keeps some), and *scales* the staff member's ability: a new pairing gets about
75% of a coach's or caddie's edge, a long one all of it (±5% for fit). It never changes a golfer's
attributes, so hiring or firing costs no rating — only the speed of improvement and the help on the
course. A familiar average coach never outperforms a clearly better one.

**What profiles show (rules 2026-11-02).** A coach's teaching and scouting, a caddie's skills and each
pairing's fit are shown and archived; each season's staff record keeps a coach's teaching and scouting and a
caddie's skills, so later views can chart them. **Prestige** is shown apart for every person: a golfer's public
standing (the last 52 weeks' results plus a slowly fading legacy of majors and big wins; recorded at every
season's end and as each history is published), and for a coach or caddie their reputation in that role. Each
role keeps its own value and directories sort by the one they list; unlike measures are never combined. A
famous coach is not necessarily the best teacher or scout, and a golfer's potential is never shown.

**Two-way recruitment (rules 2026-11-04; roadmap S2/S3).** Scouting still reads only what can be watched --
the level seen with error, the growth typical for the age, the last year's real improvement -- through an error
that shrinks with scouting skill, with each coach's view of a player persisting; now the error also shrinks with
the seasons that coach has watched that player (kept per coach and player in `Staff.watched`), so good scouts
tend to spot real improvers, are sometimes wrong, firm up their view the longer they follow someone, and still
miss late bloomers. Development coaches pursue promising growth; coaches of established players weigh Prestige,
rankings, a known fit and earned major places (never potential); caddies weigh earnings, compatibility and
stability; golfers, coaches and caddies can each turn an approach down. **Loyalty** comes from the record --
rapport (time actually worked together), fit and results together (evidence-weighted progress) -- and stands
against a better-known coach's approach, so a better-known offer alone rarely dissolves a working partnership;
departures still follow the winter odds above (progress, rapport, fit, money) and retirement. **Reasons are
recorded**: why each partnership was proposed (`reason_start`) and why the other side said yes
(`reason_accept`) on the stint both people share; every refusal (both people, who asked and why, who said no
and why) in `Relations.refusals`, and on the partnership a golfer kept when they said no out of loyalty
(`declined`); all archived in `relations.json.gz` and shown on both profiles (how each partnership began, and
the approaches turned down, also for someone no partnership ever began with, and this season's before it is
archived). The weights are proposed starting values awaiting approval
(`docs/RECRUITMENT_PACKAGE.md`).

**Fit is recorded and shown.** Each pairing's fit is drawn once (normal, clipped to −2..+2) and saved with the
relationship history (`Relations.pairs`: kind, staff member, golfer, work together, last year worked, fit), so
it survives saves, reunions and archiving. Both profiles show it beside each partnership, with the rapport as it
stood at the end of the archive (`tools/observer.py: pair_cells`), the same values the engine uses. There is no
second compatibility score. Recruitment and retention read these: a known fit (when a golfer goes back to a
coach or caddie they worked with, and in what a coach or caddie answers), rapport and shared results (loyalty);
motivations and loyalty read the same dated stints and pair records rather than new state.

**School and local instruction.** Young amateurs (22 and under) have local or school instruction
(quality 0.38, against 0.3 for teaching yourself); college golfers have their team's coaching (0.48),
recorded as a school stint that ends — as an ordinary recorded transition, with no loss of ability —
when they graduate, turn professional or retire. A private coach does not stack with it: the better
applies. College events are school-paid, and a golfer's personal debt never blocks them.

**Changes.** In the off-season either side may end a relationship, from smooth odds:

| Who | More likely when | Less likely when |
|---|---|---|
| Golfer leaves a coach | a poor run of observed progress, a poor fit, a fee that has outgrown their means | strong rapport, real progress |
| Golfer leaves for another coach's approach (winter market) | a clearly better-known coach, little yet built together | loyalty: rapport, a good fit, progress together |
| Coach who backed a prospect moves on | several seasons of evidence of stagnation | little evidence yet (one season, or seasons with few events or a long injury count for little), progress |
| Coach drops a paying client | a poor fit (rare) | — |
| Golfer changes caddie | a poor run, a poor fit | strong rapport |
| Caddie leaves a bag | it paid them little for their reputation | strong rapport |

Observed progress combines professional results and ranking movement, amateur ranking movement and
observed development; it never reads hidden potential, and there is no birthday cut-off. Mid-season
changes happen only when someone genuinely cannot continue (a golfer who can no longer pay a coach; a
caddie whose player has had no affordable event for two months) or retires. Staff retirement is its own
gradual, age-based decision (plus leaving after long spells without clients or a bag), and closes their
stints with the reason recorded.

## Money

One set of definitions serves hiring, the monthly plan, entries, weekly settlement and career runway:

| Term | Definition |
|---|---|
| Committed (weekly) | Living costs net of salary, plus a contracted coach's fee / 52 |
| Spendable | Funds (savings + backing + limited credit) − 4 weeks of committed costs: the money for travel |
| Trip cost | Travel and fees + the caddie's weekly fee (a caddie is paid only in weeks the golfer plays, once a week however many events: a Monday qualifier and that week's tournament cost one fee and count one week worked; the 8% share is paid per event from that event's winnings) |
| Prize kept | Expected prize × (1 − 8% caddie share − 5% scouting-coach share, where they apply); it informs decisions but is never spent before it is won |
| Means | Spendable + 80% of what last year's earned income left after living costs: what a contracted coach must fit into |

A caddie's commitment may also weigh expected winnings at half weight (a caddie is paid only for trips
that are themselves affordable when booked); a coach's fee may not (it is owed every week).

**When the money runs out mid-season:** a golfer who can no longer cover their committed costs stops
paying their coach that month and carries on alone (logged); a scouting coach's share deal costs nothing
up front and continues. A caddie whose player cannot afford a single trip for two months in a row leaves
the bag.

Every payment goes through one step that takes it out of the golfer's ledger (`coaching`,
`coach_share`, `caddie`, `caddie_share`) and adds it to the person's receipts, so player payments
equal staff receipts every season (checked in tests and in every long-world season).

## Not modelled yet

Club professionals as teachers of amateurs; academies and college coaches; coaches changing a
player's swing (short-term dip, long-term gain); caddies' own finances and family life; agents.
