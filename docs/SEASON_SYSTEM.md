# Golf Legacy — Season System and Prestige

Code: `golfsim/season.py` (the weekly engine), `golfsim/prestige.py` (event and player prestige,
ranking points, prize money, sponsors), `golfsim/cards.py` (end-of-season tour cards).
Test: `python tools/season_test.py --years 5` → `reports/SEASON_TEST_REPORT.md`.

## A season

Every one of the ~650 events in the world is played every season, every shot simulated: about 3.2
million holes, in about 70 seconds on 4 cores (the week's events run in parallel; results are identical
however many cores are used).

Each week:

1. **Special fields** are set first: the major (built by its real-life qualification rules from
   everything that has happened, with no hindsight), the Premier Tour Finals (top 30 on the points
   list), college post-season (conference championships → regionals → national championship), elite
   and national amateur championships (by amateur ranking and region), the Club Professional
   sectionals and Championship (from the sectional results), the Q-School stages, and the USA Open and Britannia Open qualifiers.
2. **Everyone else chooses where to play** (see "How golfers choose" below).
3. **All of the week's events are played in parallel.** Weather (wind, rain) is drawn per round around
   each course's typical wind, and hole locations get harder as event prestige rises.
4. **Results update everything:** world ranking and amateur ranking, money lists, prize money, fame and
   player prestige, the event's prestige, course records per layout (rounds, holes, aces, albatrosses,
   including match-play and playoff holes), familiarity with the course, champions' history, and
   season statistics for every player (driving distance, fairways, greens, putts, strokes gained).

At the end of the season, the completed season's evidence is **snapshotted first** — for every golfer:
the tour they played on, events, wins, top-10s, cuts, prize money, money and rank on their own tour
(ties share the average rank; ordering never depends on how the population happens to be listed: ties
break by world ranking, then id), world and amateur ranking at the start and end of the season, injury
weeks and the year's net money. Only then do players move between tours (see "Tour cards"), and
promotion or relegation is added to the snapshot as a separate fact. Career decisions read the snapshot,
never the post-card tour.

## Event prestige (owner requirement)

Every event has a prestige from 0 to 100, recomputed after each edition:

| Factor | Weight | Measured as |
|---|---|---|
| Tour | 35% | The series' standing: majors 100, Premier flagship 93, standard 81, opportunity 64, Challenger ~55–62, Regional ~38–48, Mini ~24, college, amateur and qualifying events lower |
| Field | 30% | How good last year's field was: its best 30 players' world ranking (amateur ranking for amateur events) |
| Prize money | 20% | Purse on a log scale ($10k = 0, $25M = 100) |
| Course | 15% | Elite course 100; championship course's Championship tees 80; standard course 62 (Club tees 45, Forward 32); municipal 25 |

Prestige is the weighted average of every factor over the **last five calendar years** (rules 2026-11-05;
weights 1.0, 0.9, 0.8, 0.7, 0.6 by age; it had been the last 4 editions), so an event's reputation moves
slowly: one great or poor field shifts it by a quarter of the change, and at most 6 points in a year. A year
without an edition is left out. Before an event has history, its expected values fill the four years before
the world began. See docs/WORLD_PRESTIGE_PACKAGE.md (also course and national prestige).
**Every event is on the same week every year** (only rotating host cities change), so an opportunity
event is the same event every season and builds its own identity.

Typical levels: majors ~98, Premier flagship ~92, standard ~83, Premier national opens ~87, opportunity
~65–75, Challenger ~56, Regional ~41, Mini ~22, college ~24, amateur series ~16, elite amateur
championships ~50, national amateur championships ~35.

## How golfers choose where to play

Each golfer scores every event they may enter that week:

    value = event prestige
          + 6 if it is in their home country (+2 home region, −6 overseas for lower tours)
          − fatigue after two or more weeks in a row, − 8 the week after playing a major
          − their season fatigue (good course managers rest more wisely)
          + catching up on (or easing off) their season plan (about 19–27 events by stamina;
            Premier players about 15–23 and stars about 4 fewer)
          + 5 when defending their title, ± a little randomness

They enter events worth more than their own **bar**: the larger of (their tour's typical event − 20) and
(0.9 × their prestige + 3). An average Premier Tour player (prestige ~45) has a bar of ~63 and happily
plays opportunity events; a star (prestige 85+) has a bar of ~80 and skips them for the bigger events.
Events take entries in priority order: members of the event's tour, then members of other circuits or
higher tours, then lower tours, then amateurs (limited to a few sponsor invitations), each group by
world ranking. Premier Tour events order their members by **playing rights** (exempt, full, graduate,
conditional; the last two reshuffled by the season's Premier money) and Challenger events give Premier
visitors at most 10% of their places (`docs/COMPETITION_ACCESS.md`). Within a group, mini tours (paid by entry fees) take entries by a fair draw; college and
open amateur events rotate their lineups: golfers with fewer starts this season go first, amateur
ranking counting for about three starts' head start, so the best still play most but a squad's depth
gets starts too. Open amateur events (club, county, regional) take up to 1.5× their usual field when
more want to play.

**College amateurs in ordinary open amateur events (rules 2026-11-11, new worlds).** An *ordinary open
amateur event* is a regular event of one of the six regional amateur series (tier 6, category `regular`,
open amateur entry: `ordinary_open_amateur` in `golfsim/season.py`); circuit championships, national and
elite amateur championships, qualifiers, college (tier 5) and professional events are not. In those events
a college amateur (on a college tour) whose *home region* is the series' region enters at the members'
class (10, where college golfers had been class 12, after the members). Home region is where the golfer
lives (`Season.home_region`: residence, which for a college golfer is their college base; nationality only
for legacy golfers whose residence was never recorded), the same residence the amateur series' eligibility
already uses; the series' region is the region its circuit covers (`OPEN_AMATEUR_REGIONS`, from
`calendar.LOCAL_CIRCUITS`: the Asian series covers Asia and the Middle East). Within that class, members
and these college players rotate by their **amateur (tier 6) starts this season** (`Season.open_am_starts`,
a per-season counter kept as events are played), not every start, so college-event starts never push a
college player back; whoever has fewer goes first, ranking keeping its head start, and the seeded entry
draw breaks ties. Everyone else in those events (college players from outside the region, other amateurs)
keeps their class and the rotation by every start; field sizes (1.5×), eligibility, the calendar and every
other event's entry are unchanged. No place is reserved or guaranteed, and members can lose places in full
fields. Worlds saved before 2026-11-11 keep the previous order (`Season.college_open_access` is off for
them). Golfers who miss out try their next choice (deferred acceptance), and spare places go
to willing players who were just below their bar. Every week records who wanted to play, who was placed
and who was shut out of every field they tried, by tour (`entry_stats`), so blocked access is reported
apart from choice, injury, money and having no eligible event.

## Player prestige and sponsors (owner requirement)

Players earn **fame** from every finish: event prestige cubed (a major is worth 6× a Challenger event)
times their finish (win 100%, 2nd 45%, 3rd 30%, top 5 20%, top 10 10%, top 25 3%, made cut 1%).
Fame counts over a **rolling 52 weeks** (owner: about a one-year window). Wins also add lasting
**legacy** (major 40, flagship 10, other Premier 4) that fades only 3% a year. Player prestige (0–100) = a curve of fame + half the legacy: about 85 for a dominant world No.1,
~41 for an average Premier Tour player, ~20 on the Challenger tours, single digits below.

**Sponsor income** is driven by player prestige: ~$20M+ a year for the biggest stars, ~$1–5M for top-30
players, a few thousand for mini-tour players. (Reported now; a full finance model is on the backlog.)

## Fatigue and injuries (owner requirement)

Every golfer carries a **season fatigue** level (0 fresh, 1 exhausted):

- Each event adds fatigue by rounds played, more for **low stamina**, travel to another region, and age
  (over 30). A week off recovers it, faster with a high **recovery rate**.
- Tiredness is mostly **physical**: shorter drives and a body that tires sooner in the round (wider
  dispersion, more mishits). A tour-average player at fatigue 0.6 loses about 0.8 strokes a round.
- **Injuries:** after every event there is a chance of injury that rises steeply with fatigue, and with
  low **injury resistance**, age and low stamina. Injuries (back, wrist, shoulder, knee...) keep a player
  out for a median of about 4 weeks, sometimes much longer (longer when older). Injured players cannot
  enter any event, including majors. Timing (rules 2026-11-02): an injury at an event in week W announced as
  n weeks keeps the golfer out of the entries of weeks W+1 to W+n, counted on across the year end (next
  season's week 1 follows week 52); they can enter again from week W+n+1. Earlier rules kept them out one
  week longer than announced (`tests/test_injury_timing.py`).
- Golfers see their own fatigue when choosing events, so tired players skip weeks.

## World ranking, money, points lists

- **World ranking:** points per finish from event prestige (a major winner 100, a standard Premier winner
  ~60, a Challenger winner ~12), full value for 13 weeks then fading to zero over two years, divided by
  events played (40 to 52). The amateur ranking works the same way for amateurs.
- **Prize money:** Premier Tour-style payout table (winner 18%), shared on ties; amateurs take no money
  and the professionals behind them move up. The table is sized by the event's intended paid places (the cut,
  within the intended field size — even when fewer start; every starter in a no-cut event); places no
  professional fills are not paid out and are recorded (`Season.unpaid`), so a small or undersized field
  never inflates anyone's share.
- **Points lists:** money lists per tour; majors count for all three Premier circuits; a combined
  Premier list decides cards. The majors' rules read these lists (e.g. "top 70 on the points list").

## Tour cards (end of season)

| Tour | Keep | Move up | Move down |
|---|---|---|---|
| Premier (300) | Top 200 on the Premier money list; Premier winners this season or last; major champions of the last 5 years | — | Everyone else, to their region's Challenger tour |
| Challenger (5 tours) | Enough of the best members to stay at full size (at least half) | Americas top 25, Europe top 20, Asia and Japan top 8, Latin America & Canada top 5 → Premier | The rest, to their regional or mini tour |
| Regional (6 tours) | Enough to keep their size (at least 60%) | Top 8 → Challenger | The rest, to a mini tour |
| Mini (16 tours) | Open | Top 4 → Challenger; next 6 → regional | — |
| Q-School | — | Premier Q-School final top 5 → Premier, 6th–45th → Challenger Americas; Europe final top 20 → Premier Europe, 21st–60th → Challenger Europe; Japan top 30, Asia top 35 → their Challenger tours | — |

Premier Tour Europe's top 10 and Asia-Pacific's top 5 move to the Americas circuit (as DP World Tour
players earn PGA Tour cards).

## What the multi-season test shows

See `reports/SEASON_TEST_REPORT.md`: tours keep their sizes and sort players by ability over the
seasons; stars play the flagship events and mostly skip the opportunity events; the major fields come
out at real-life sizes and mixes (20 club pros at the Premier Tour Championship, ~85 qualifiers at the
USA Open, 5–9 amateurs at the Britannia Open); and attributes show up in the season statistics
(power ↔ driving distance ~0.97, overall ↔ scoring against the field ~−0.8 on the Premier Tour).

## Not built yet

See `docs/BACKLOG.md`: player development, nation improvement, history generation, finances, Monday
qualifiers, team college golf.
