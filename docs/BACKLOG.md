# Golf Legacy — Backlog

Owner requirements and planned work, in rough order. "Built" items link to where they live.

## Built

- Shot-by-shot engine, 21 attributes, archetypes, calibration (`docs/ENGINE_DESIGN.md`)
- World calendar with the four fixed majors and real-life qualifying (`docs/CALENDAR_AND_QUALIFYING.md`)
- 380-course library with layouts and per-layout records (`docs/COURSE_LIBRARY.md`)
- Nations and the world population (`docs/WORLD_POPULATION.md`)
- Season system v1 with event and player prestige (`docs/SEASON_SYSTEM.md`)
- Development, monthly planning, money and careers v1 (`docs/DEVELOPMENT_AND_CAREERS.md`)

## Prestige (owner, recorded for the backlog; first version built in the season system)

- **Every event has a prestige level** from: the quality of the course, the tour playing it, the quality
  of last year's field, and the prize money. *Built:* `golfsim/prestige.py`, updated after every edition.
- **Every tournament stays on the same week every year**, so the "opportunity" events that most great
  pros skip are the same events every season and build their own identity. *Built:* calendar weeks are
  fixed per series (tested); only rotating host cities change.
- **Prestige drives AI decisions on where to play.** *Built (v1):* golfers score each event by prestige,
  home country, travel, fatigue and their season plan; stars set a higher bar, so they skip opportunity
  events. Later: plan whole schedules around majors and favourite courses, play-in-form, defending
  titles, appearance fees, team events.
- **Winning higher-prestige events raises a player's prestige.** *Built (v1):* fame from every finish,
  scaled by event prestige; lasting legacy from majors and flagship wins.
- **Sponsors are driven by player prestige.** *Built (v1):* yearly sponsor income from prestige
  (reported). Next: a real finance model — contracts with brands (clubs, ball, apparel), bonuses for
  wins and majors, contract lengths, a player's money and expenses (travel, caddie, coach), and money as
  a constraint on mini-tour players' schedules.
- **Coaches:** hiring the best coaches depends on money and prestige (owner, career phase).

## Owner principles

- **The world evolves over time, with ups and downs over centuries.** No artificial ceilings or floors
  on talent: a weak era (best player 83) and a golden one (two players at 95) are both fine.
- Event prestige moves slowly (rolling 3–5 years); player prestige over about a year.
- Stamina matters across a season: tiredness affects mostly physical attributes and raises injury risk,
  especially with low injury resistance or older age.

## Careers, money and the people of golf (owner)

- **Finances drive careers.** A 22-year-old earning a few thousand a year keeps chasing the dream; by
  26-27, if they are still only making $10-20k, it stops making sense to travel the world for it.
  They take a full-time job but, still good enough, play a couple of events a year on a low tour near
  home. *First version: see `docs/DEVELOPMENT_AND_CAREERS.md`.*
- **Rare comebacks:** a part-timer whose mental game has matured naturally may make another run at
  34 — qualify for a big event or win a tour card. Very rare, but possible and part of the history.
- **Every individual has a history** — players, caddies and coaches: careers, results, moves, injuries,
  money, milestones. *Players: first version built (career log).*
- **Caddies and coaches as people (not built yet):** players who never make the Premier Tour but have
  great mental attributes can become caddies or coaches; caddies and coaches have their own skills,
  careers, reputations, employers and histories; the best players hire the best of them (money and
  prestige).
- **Monthly planning (owner):** each month a golfer juggles training a category of attributes, a full
  rest week, and tournaments — a risk/reward balance of fatigue and injury against development and
  career. Playing tournaments develops raw golfers (far from their potential) the most.
  *First version built.*

## Next

1. **Coaches and caddies as people**, with coach recommendations driving training choices and the
   money/prestige market for the best of them. Re-injury risk after serious injuries.
2. **Finance v2**: contracts and bonuses, family support for young players, cost of living by country,
   appearance fees.
3. **Nation improvement** (owner): nations' pool, development and pathway move with their golfers'
   results (a nation that wins majors grows more and better juniors a decade later).
4. **History generation**: simulate decades before the game starts so there are past champions,
   records and storylines from day one.
5. **High-school golf** (owner: later) and junior events.
6. **Storylines and the viewable history** (owner): season reviews, rivalries, streaks, records,
   player career pages.
7. **More courses** (hundreds to thousands; owner) and hand-designed elite courses with named holes.

## Known gaps in the season system v1

- Fields: no Monday qualifiers for regular tour events, no team college golf (players enter as
  individuals), no sponsor invitations beyond a few amateurs.
- The US Open final qualifying draws fewer entrants than real life (about 160 instead of ~900).
- World ranking uses a simplified OWGR formula; amateur ranking a simplified WAGR.
- Weather: wind and rain per round, no per-wave tee times or seasonal weather patterns.
