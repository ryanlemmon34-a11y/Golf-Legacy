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
| **Teaching** (hidden) | How much their coaching helps. |
| **Scouting** (hidden) | How well they judge a young player's potential. |
| **Reputation** (seen) | What golfers can see when choosing; it follows their students' success (fame, progress). It sets the fee: about $15k a year at 50, $45k at 80, $70k at 95. |
| **Capacity** | 3 + teaching / 12 students. |

**One coach at a time.** Coaching quality for a week of training = teaching, +0.15 in their speciality,
+0.15 for a young player if that is their gift (at most 1). Without a coach a golfer teaches themselves
(0.3). The training multiplier is 0.7 + 0.6 × quality, so a strong specialist makes a week of training
count for roughly a third more than teaching yourself. A coach also helps a golfer **read their own
game**: the golfer's misreading of where their room to improve lies narrows to the coach's teaching
level, so they pick better things to work on.

**Getting a coach** (every season, before it starts):

1. **Scouting.** Each coach with room looks at up to 60 young players (23 and under) near them (their
   country; well-known coaches their whole region). They estimate potential through the noise of their
   own scouting skill and approach young, *raw* players they believe in (the better the coach, the
   higher their bar). Players usually accept, and switch only to a clearly better-known coach. The coach
   works for free in return for **5% of future prize money**.
2. **Hiring.** Golfers who want a coach (coachability, and almost every tour professional) hire the
   best-looking coach they can afford: the fee must fit 10% of their spendable funds plus 8% of last
   year's earned income. They see reputation, not teaching skill, and look for a speciality matching
   what *they believe* is their weakest area. The best-known players choose first. Many college players
   and most amateurs therefore have no coach.
3. **Leaving.** Golfers who can no longer afford the fee leave; a difficult season (falling ranking,
   relegation) sometimes ends the relationship; coaches retire (smoothly with age, from the late sixties).

## Caddies

A caddie has the six skills the shot engine has always modelled: **strategy** and **yardage** (decision
quality — course management), **mental support** (how much pressure costs and how long a bad hole
lingers — composure), **green reading** (putting reads), **course knowledge**, and **communication**
(how much of it reaches the player). A caddie builds **familiarity with every course they work**, round
by round, exactly as players do; in the engine the player benefits from the caddie's familiarity on top
of their own. Caddies gain a little skill with experience until about 50 and stop caddying smoothly
with age (around 60).

Full-time professionals on the Premier and Challenger tours hire a caddie each season: the best-known
players first, each taking the best available caddie they can afford (a weekly fee of $800 + $25 per
reputation point, plus 8% of prize money). A caddie's reputation follows their employer's prize money.
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

The world has no recorded past, so the starting coaches (~325, by each nation's golf pool) and caddies
(~1,450, by where tour players come from) are generated with a background ("a teaching professional",
"a club caddie"). When demand outgrows the profession (more tour players wanting caddies than caddies,
or coaching capacity running short), outside recruits are generated and labelled "(outside recruit)".

## Money

Coaching fees are paid weekly from the golfer's ledger (`coaching`), a scouting coach's share comes out
of prize money, and a caddie's weekly fee is part of the cost of every trip — so planners and entry
decisions see it before money is spent. Coaches and caddies record their earnings. Ledgers still
reconcile exactly.

## Not modelled yet

Club professionals as teachers of amateurs; academies and college coaches; coaches changing a
player's swing (short-term dip, long-term gain); caddies' own finances and family life; agents.
