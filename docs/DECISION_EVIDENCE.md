# Decision evidence (E1): scheduling and career-decision inputs

Recording only. The monthly planner (`Season.plan_block`) and the winter career rules (`careers.decide`)
computed their targets, terms and probabilities and then threw them away; from this build each season file
keeps them, so a report can say *why* a golfer played, trained, rested or worked, and what went into a
retirement, a stop, or turning professional. Nothing is decided differently: no random number is drawn, no
draw moves, no working table gains a key, no iteration order changes, and the rules version
(`golfsim/rules.py`) is unchanged. Seasons played before this build (the pinned A-D runs among them) have no
evidence: their season files have no `decision_evidence` key, and readers return "not recorded" -- the
evidence is never estimated for them.

Code: `golfsim/decision_evidence.py` (record, archive block, reader); recording calls in
`golfsim/season.py` (`plan_block`) and `golfsim/careers.py` (`decide`, and an optional `ev` dict on
`runway_years`, `desire_to_continue`, `p_stop_chasing`, `p_retire`, `p_turn_pro`, `p_amateur_job`,
`p_comeback` that receives each term exactly as computed), `golfsim/amateur_return.py` (`chance` takes the
same `ev`) and `golfsim/mortality.py` (`winter`). Switch: `Season.record_decisions` (on in every
new or loaded world; off keeps nothing and is the previous build's behaviour). Reader:
`Archive.decision_evidence(person, year)` or `decision_evidence.read(season_file, person)`.

## Season file: `decision_evidence`

    {"format": "golf-legacy-decision-evidence/2",
     "definitions": {...every field name, code and scale below...},
     "schedule": {"<person id>": {...one golfer's season of monthly plans...}},
     "careers":  {"<person id>": [[...one career evaluation...], ...]},
     "mortality": {"bands": {...}, "died": {...}}}

`definitions` repeats the field lists, codes and scales, so a reader takes them from the file it reads.

Formats: `/1` (build/v16-schedule-evidence, 9e0b042) has `schedule` and `careers` with the six models below
other than `amateur_return`; `/2` (integration/v16-rc1-e1) adds the `amateur_return` model (rules 2026-11-06)
and the `mortality` part (rules 2026-11-07). The schedule and the career row shape are unchanged, and
`decision_evidence.read` reads both (`mortality` is None for a `/1` file).

### `schedule`: the monthly plans

Every active golfer is planned for at weeks 1, 5, ... 49 (13 plans; `plan_blocks`), each plan covering four
weeks (`plan_every`). One record per golfer evaluated, holding columns with one entry per plan (entry k is the
plan made in week `w + 4k`):

| key | field | unit / scale | meaning |
|---|---|---|---|
| `w` | first plan week | week | the week of the first plan recorded (1 for a whole season) |
| `n` | started | starts | events already played this season when the plan was made (pace = target x week / 52 - started; the starts of the previous four weeks = this entry minus the one before) |
| `x` | fatigue | x100 | season fatigue at the plan (0 fresh .. 100 exhausted; the planner rests any week it starts above 25 -- a recorded 25 may be just over or under) |
| `m` | funds_k | $1000s, two significant figures (whole thousands below 100) | spendable funds at the plan (`Season.spendable`: what trips are paid from; may be negative) |
| `c` | weeks | 8 characters a plan | the four weeks' availability (`o` an affordable eligible event, `u` eligible events but none affordable, `e` events at their level in their region but none they may enter, `n` no suitable event), then the activity planned for each week (`P` play, `T` train, `R` rest, `W` paid work); `-` x 8: plan not recorded |
| `d` | dev_train | x10 | the planner's value of a training week this month (development value of training the chosen category, with coaching; scaled down for part-timers) |
| `i` | injured_weeks | weeks | weeks from the plan's first week until they may enter again (0 fit); only present for golfers injured at some plan |
| `f` | flags | bits | 1 `can_work` (paid work was an option: money genuinely short), 2 `stuck` (cannot cover committed costs, or could afford nothing eligible), 4 `major_caution` (a top-100 player with a major in the next weeks), 8 `no_affordable_plan` (no combination was affordable: the fallback plan); only present for golfers with any |
| `t` | target | list, kept when it changes | `[week, role, base, stamina, prestige, target]`: `Season.target_events` by its parts -- `target = base + stamina + prestige`. Roles: `part_time_pro` 6, `part_time_amateur` 8, `club_pro` 12, `college` 24, `amateur` 16 (base only); `premier` 15 + 8 x stamina/100 - 4 when their prestige is 65 or more; `pro` 19 + 8 x stamina/100 |
| `s` | terms | list, kept when any changes | `[week, bar, dev_play, work_value, load4, rest_keep, injury_risk]`, stored as round(value x `term_scale` = 1, 10, 10, 1000, 1000, 10000): `bar` the least event value worth playing (`Season.bar`), `dev_play` the development value of a tournament week, `work_value` the value of a paid work week (-1: not an option), `load4` the fatigue a four-round week adds, `rest_keep` the share of fatigue kept after a rest week (recovery), `injury_risk` the injury base x resistance x age x stamina factors the planner charges a playing week (times 1 + 6 x fatigue squared, x 400) |
| `over` | -- | count | plans not kept by the bound (a plan made twice in a week, or beyond 13); absent normally |

The planner's choice for a week to play is `event value - bar + dev_play - fatigue cost - injury cost - net
trip cost`, against `dev_train` (or `work_value`, or a forced rest when fatigue starts above 0.25); the event
values themselves are not kept (see the gaps below), but availability, fatigue, the bar, development values,
injury and money are.

### `careers`: the winter's career evaluations

Each golfer the winter's rules evaluated (`careers.decide`; college golfers are not evaluated for retirement --
the rules give them no chance -- so they have rows only when they graduate). One row per evaluation, at most
three a winter (`career_rows`):

    [model, p, u, outcome, *terms, *inputs]

`p` the probability (4 decimals), `u` the uniform draw it was compared with (the decision happened when
`u < p`), `outcome` 1/0, then the model's logit terms (2 decimals; they sum to logit(p); `None` when the term is
not part of the model in that case) and the inputs behind them that the season file does not already hold
(`None`: not available at the decision). Terms are signed as they enter the logit.

**Stored figures are rounded; the recorded outcome is authoritative.** The decision was made with the unrounded
`p` and `u` (and the model's unrounded terms); the row keeps them rounded (`p` and `u` to 4 decimals here, terms to
2, mortality's `p` and `u` to 5). So a row can show `p` and `u` equal, or even `u` just above `p`, with outcome 1:
for example p = 0.250049 and u = 0.250041 decide yes (u < p) and are stored as 0.25 and 0.25 with outcome 1. Read
`outcome` (and the transitions and `deaths`, which record what happened) as the fact; recomputing `u < p` from the
stored, rounded values is not, and the rounded terms sum to logit(p) only to within their rounding.

| model | when | terms | inputs |
|---|---|---|---|
| `retire_tour` | full-time professionals and full-time amateurs outside college | `base` -6.5, `age` 0.22 x (age - 30), `standing` 1.2 x (1 - money-list standing), `opportunity` -1.0 x the tier's opportunity, `injury` (0.06 x injury weeks + 0.8 x lasting-damage injuries) | age, tier, money_rank_pct (None for non-professionals: standing 0.5), lasting_damage |
| `retire_job` | part-timers and club professionals | `base` (-4.4 club pro, -2.2 otherwise), `age`, `engaged` (-0.6 x share of target played + top 10s), `drift` (2.4 x chose not to play), `blocked` (0.8 x could not play), `standing` (-1.5 x ranking standing), `progress`, `willingness`, `injury` | age, target, drift, blocked, rank, lasting_damage |
| `stop_chasing` | full-time professionals (after the backers' review) | `base` -4.5, `pressure` 4 / (1 + runway), `short_runway` 2.2 x max(0, 1 - runway), then minus each part of the desire to continue: `progress`, `opportunity`, `secured`, `willingness`, `life` (the pull of an ordinary life by age), `injury`, `lasting_damage` | age, tier, runway (years), shortfall_k (season cost beyond income, $1000s), own_funds_k (None when the season pays for itself), target, lasting, and when they stopped and did not join the staff: p_club, p_amateur, u_where (where they went) |
| `turn_pro` | amateurs graduating from college or outside it | `base`, `standing` (amateur ranking), `means` (savings and family money), `willingness`, `wins`, `age` (None when graduating) | age, graduating, am_rank |
| `amateur_job` | full-time amateurs outside college, 19 or over, who did not turn professional | `base`, `age`, `runway`, `debt` | age, runway, cash_k |
| `comeback` | part-time professionals | `base`, `results`, `funded`, `age`, `injury`, `willingness` | age, top3, progress |
| `amateur_return` (/2) | part-time (working) amateurs outside college who did not turn professional (`amateur_return.chance`) | `base` -3.0, `results` 2.0 x the results signal, `funds` 0.6 x min(2, funds / season cost), `willingness` 1.5 x (will - 0.5), `age` -0.12 x max(0, age - 23); **here p = min(0.6, sig(sum of the terms) x keep_up)**, not sig(sum); all None when a condition blocked the chance (p 0, no draw: `u` None) | age, seasons_in_work (None: working before the records began), season_cost_k (a full-time amateur season with committed staff), funds_k (savings + family money), signal, keep_up (1 - the chance they would take a job again next winter, p_amateur_job at next season's age after paying for the season), capped (1 when the 0.6 cap applied), blocked (`work`, `funds` or `results`; None when not blocked) |

The return's draw is its own stream per golfer and season (`amateur_return.draw`), taken only when p > 0, as
the rules always took it.

The season's results the models read (events, wins, top 10s, rankings, injury weeks, money) are in the same
file's `careers` rows; age is the season year minus the birth year (`people.json.gz`).

### `mortality` (/2): the winter's mortality draws

Every person who can die (`mortality.eligible`: anyone not an active competitive golfer, with a known birth
year) is evaluated once in the winter after each season: their annual risk q(age) against their own draw u (a
hash of world seed, season and person). Kept, bounded:

| key | content |
|---|---|
| `bands` | `{"<age band>": [evaluated, expected, died]}` by ten-year band (`band_years`; "60" = ages 60-69): people evaluated, the sum of their risks (expected deaths, 3 decimals), deaths |
| `died` | `{"<person id>": [age, p, u]}` for each death: the age (as frozen in `deaths`), the risk q(age) and the draw (5 decimals) |

A survivor's own draw is not stored: it is reproducible exactly from the rule (`mortality.draw(seed, year,
person)` against `mortality.annual_risk(age)`), so storing it for every retired person and staff member -- a
number that grows every season -- would add nothing. The deaths themselves stay in the season file's
`deaths`.

## Bound and size

Rows are bounded by structure: 13 plans per golfer-season (one per monthly plan; a plan made twice, or a 14th,
is counted in `over`, never kept), at most 3 career rows per golfer-winter (retirement, then turning
professional and a job or a return, or a comeback, or stopping the chase), each a fixed width of small
integers, rounded floats and short codes; mortality is a dozen age bands plus one row per death. Measured (one
archived season, seed 97, gzip as written):

| build | world | golfers | season file without | evidence | growth | per golfer-season |
|---|---|---|---|---|---|---|
| /1 on v16 | scale 0.03 | 200 | 533,140 B | 28,469 B | 5.3% | 142 B |
| /1 on v16 | scale 0.10 | 639 | 1,543,866 B | 84,884 B | 5.5% | 133 B |
| /2 on rc1 | scale 0.10 | 639 | 1,691,703 B | 88,544 B | 5.2% | 139 B |

On rc1 the parts alone (gzip each): schedule 62,071 B, careers 24,552 B (1,239 rows, 129 of them
`amateur_return`), mortality 161 B (2 deaths in the first winter of a new world; a mature world has more
retired people and deaths, still a dozen bands plus about 20 B a death).

A mature full world's season file is about 13.5 MB for about 13,200 golfers (about 1 kB each; 2083 in the
50-season world), so at roughly 115-140 bytes a golfer-season the evidence would add about 1.5-1.8 MB a season
(about 11-13%; the reviewer decides whether that is acceptable). Most of it is the per-plan columns (fatigue, funds, plan codes, the bar and development
values); the career rows are about a quarter.

## Not recorded (remaining gaps)

- The weekly entry choice: which event a golfer entered among those on offer, the per-event values
  (`Season.event_value`: prestige, travel, streak, pace, major caution, tiredness, defending champion) and
  trip costs. The monthly plan and the week's access outcome (`careers[...]['access']`, `denied`) are kept;
  the event-by-event comparison is not.
- The planner's per-week event values, trip costs, expected prizes and the chosen plan's total value (only
  availability codes, funds and the terms above).
- The coach / caddie career draw when a golfer retires or stops chasing (`staff.former_golfer_role`: its two
  probabilities and draw); the outcome is in the transitions.
- The backers' review (`careers.review_backers`, `p_backers_continue` terms and its draws). Its outcome is in
  the transitions with backing, progress and places secured; when the golfer pays their own way, the figures
  `careers.own_way` used (cash, income, costs, on all three routes since the recruitment fix) are kept there
  as `forecast` -- not duplicated here.
- Mortality: a survivor's own draw (reproducible, see above).
- Inputs a model does not use are not inputs of that decision and are not recorded: turning professional
  reads amateur standing, means, willingness, wins and age -- not earnings against costs or places secured;
  retirement from a tour reads money-list standing, not savings.
