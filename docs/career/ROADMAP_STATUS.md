# Career roadmap: implementation status, dependencies and engine contracts (2026-11-15)

Branch `integration/consolidated-career-update` (from `integration/caddie-ui-verify` 89a6d96, plus HAL's bd87022 →
bc753ef and 4bbcb2e → 747fbf7). **Not a complete build; not ready for Ryan's test.** HAL owns UI; Claude owns
engine, persisted decisions and evidence, and the read models below.

Status words: **done** (engine and tests on this branch), **partial**, **in progress** (this checkpoint),
**not implemented**, **blocked** (needs a decision or input), **deferred** (long-term, not to be raced).

## Inventory

| item | engine status | notes / owner |
|---|---|---|
| Truthful entry reasons, closeness only from decision-time data | **done** (355555d) | `career.week_entry`, `ENTRY_TEXT`; older weeks `recorded: false`. HAL renders (8d02cb7). |
| Truthful entry *chances* before deciding | **not implemented** | Only decision-time facts exist. A forward "chance" would be a prediction; proposal: show the entry order rule and last season's recorded cut-off for the same series, labelled as history, never as a promise. Needs Ryan's yes. |
| Default "yes" acceptance (selected / qualifying) | **partial** | Engine takes whatever policy is posted; the default is the form's (HAL). Engine default when a policy is omitted: not added (would change the command contract) — can add on request. |
| Visible current qualifications and placement unlocks | **done (engine read model, first version)** | `golfsim/opportunities.py`: `career.view()['opportunities']` from the implemented routes (major exemptions with their stated finish, qualifying stages, qualifier targets); status already_qualified / needs_result / awaiting_selection / not_eligible. Tour cards and winner exemptions held: HAL's `career_context`. US college qualifiers plug in when built. |
| Early invitation notices | **not implemented** | Selection is decided in the event week. Only routes already decided (e.g. a winner's exemption, a card) can be noticed early; anything else would be a prediction. Design needed with HAL. |
| Usable coach / caddie offers | **done (reworked)** | Market offers answered at the same point of the 1 January market as an AI golfer's (probe on a copy; same draw); the earlier holds were withdrawn after the parity audit. Paired human/AI tests. |
| Player choosing staff themselves (hire a coach/caddie) | **done (engine)** | `staff_policy` command: seek_coach / seek_caddie = 'no' (default, earlier behaviour) / 'yes' / 'ask'; coach_approaches / caddie_approaches = 'ask' (default) / 'decline' (every market approach answered no, as on the spot) (the 1 January market stops with a `market_choice` decision, yes/no). Looking runs the AI's own search: same ranking, same coaches' and caddies' answers. `career.view()['staff_policy']`. |
| Thirteen fixed four-week periods; interruptions resume within the period, one recap | **done (verified)** | tests/test_period_cadence.py. |
| Editable four-week plan accepting coach advice | **done (UI); engine decision evidence done (`golfsim/decision_support.week_compare`; committed hook `career.view()['week_compare']` = {week: comparison} for the current period's open weeks)** | HAL's reviewable advice (c36f17b); the engine plan command needs nothing new. |
| Season results / season review | **done** | `year_end.review` (YEAR_END.md), weekly recaps with entry evidence. |
| Factual inbox / calendar / recaps | **partial** | Engine: notices, log, decisions, recaps, planner, `week_entry`. Inbox/calendar presentation: HAL. |
| Trophies (majors, college, amateur championships) with engraving and multi-win history | **done (engine read model)** | From recorded winners only (`ctx.results` keeps every winner for good). Contract below. |
| Per-category fallible potential letter grades | **done (engine read model)** | `golfsim/scouting.py`: observations persisted in the career record at control start and each season review; the judge's seeded persistent error; never ceilings or potential. Grades A/B/C/D/F only. |
| Optional goals | **done (engine)** | `set_goal` / `drop_goal` commands (versioned, exactly-once), at most 5 active; kinds win / play_in / world_rank / amateur_rank; status derived from records; read by no rule (tested: world unchanged). `career.view()['goals']`. |
| Relationships, timeline / living history | **done (engine read model, first version)** | `career.view()['timeline']`: control stints, answered decisions, trophies, wins and top-10s, coach/caddie partnerships, from records only. |
| Distinctive fictional tournament names | **done (v3 new worlds)** | golfsim/event_names.py: the ordinary numbered events get place names (town + optional course feature + kind suffix), deterministic, unique, no real brands, places tied to famous real events avoided; ids, weeks, venues, Premier/anchor names unchanged; v1/v2 unchanged. |
| College qualifier overhaul (4 early-spring qualifiers, 39 each, all US college tours, heats) | **done (engine), calendar v3** | docs/career/COLLEGE_QUALIFIERS.md; `schedule.NEW_WORLD = 'v3'` for the app (HAL: observer_app new-world calendar); engine DEFAULT stays v2; v1/v2 unchanged. |
| Same-year USA Open place for the college national champion (amateur) | **done (v3), enabled 2026-11-15 on HAL's final-scope confirmation** | Route `U2C`: championship (week 22) before final qualifying (24) and the Open (25); amateurs only; tests for timing, status, no invented place, the World University champion not included. |
| Finance trace | **done (engine read model)** | `career.view()['money']`: funds now (cash, family backing, backers' money, spendable), this and last season's ledgers line by line (null when nothing was booked), golfsim/career_money.py. |
| Sponsor / backer explanations | **done (engine read model, first version)** | `money.sponsor` (contract, Prestige, the rule) and `money.backer` (deal, put up / returned this season, last deal ended). |
| Annual tracking | **done (engine read model)** | `career.view()['seasons_summary']`: one row per controlled season (events, wins, top 10s, prize money, ranks), from the recorded weeks. |
| Old-save continuation (Patrick / CareerTest saves) | **blocked** | Source engine 57c4719 is `rules_changed` (fatigue fix); migration proposal only (ENGINE_MIGRATION.md). Not enabled. |
| Encyclopedia entry | **deferred** | After career testing (BACKLOG item 6). |
| Performance target (120 s) | **deferred / unmeasured on this branch** | Needs a measured benchmark on the full world before any claim. |
| Commercial: Steam, Birth (origin) mode, mods | **deferred (long term)** | Not part of this update. |
| Automatic world prologue | **not approved** | Not built. |

## Dependency plan (engine)

1. Consolidate (this branch) — HAL's follow-ups on top of the engine fixes; focused tests.
2. **Trophies read model** (no new world state; recorded winners only). → HAL's trophy cabinet.
3. **Potential estimates**: persisted yearly observations in the career record + seeded per-coach view; read model.
   Depends on nothing else; must not touch world RNG streams.
4. **Qualifications read model** (canonical, from recorded routes) → early notices only for routes already decided.
5. **Timeline read model** (stints, results, trophies, staff, moves, decisions) → goals (persisted, versioned
   command) build on it.
6. College qualifier overhaul (calendar v3) — independent of 2-5; largest; needs the v3 default and golden
   re-baseline sign-off already given; same-year USA Open place confirmed in scope first.
7. Later: player staff hiring, finance trace, sponsor explanations, annual tracking, fictional names (decision).

## Engine contracts (agreed shapes, engine side)

All read only, in the committed career view (`career.view`) or callable on the committed snapshot; every key always
present; `null` = not available (e.g. an older save), `[]` = none.

### Trophies — `career.view()['trophies']` (HAL's shape, extended)

```
trophies: [ {event_id: "2029:USA_AMATEUR", series_id: "USA_AMATEUR", event_name: <contextual label>, year: 2029,
             winner_id: 8291, winner_name: "Reed Mann", kind: "major" | "college" | "amateur",
             times_won: 2,                       # this golfer's wins of this trophy up to and including this year
             during_control: true} ]             # won while the player controlled them (stints)
```
For the controlled golfer (all their recorded wins, before or during control). `null` only if the career is gone;
`[]` if none. Trophies: the four majors (`kind 'major'`); College National Championship, Small College National
Championship, World University Championship (`'college'`); elite and national amateur championships (`'amateur'`).
Regionals, conference events and qualifiers are not trophies. Engraving: `golfsim.awards.engraving(season,
series_id)` -> `[{year, winner_id, winner_name}]` oldest first (every recorded year of that trophy in this world).
Ties are decided by the event's own playoff (one winner per edition); multi-site events have no trophy.

### Potential estimates — `career.view()['scouting']` (implemented)

`as_of` is a list `[year, week]` (not an object); `grade` is one of `A`, `B`, `C`, `D`, `F` (no `E`) or `null`;
`history` is a list of `{year, week, grade}`.

```
scouting: { as_of: [year, week] | null, source: "coach" | "self",
            categories: [ {category: "putting", grade: "A".."F" | null, confidence: "low" | "medium" | "high" | null,
                           explanation: str | null, history: [{year, grade}]} ] }
```
Grade from a projected category level: the observed level (seen with error) + the typical growth for the age +
the observed recent improvement (from the persisted yearly observations), through the judging coach's scouting
error (a seeded, persistent per-coach view; firmer the more seasons watched) — the staff scouting model, per
category. Never reads ceilings or potential. `grade: null` with an explanation when nothing has been observed yet.
Grade colours are HAL's.

### Opportunities — `career.view()['opportunities']` (implemented)

`[{event: {id, series_id, label, week, year}, condition: {kind: 'win'|'finish'|'qualifying_place', text,
positions: [..]|null, top: n|null, places: n|null, site_places: [..]|null}, target: {id, series_id, label, week,
year}, route: {code, label, source}, status: 'already_qualified'|'needs_result'|'awaiting_selection'|'not_eligible',
restrictions: [str], decided: null}]`, for events from the current week to the season's end, sorted by week.
Only implemented routes (qualification._rules, qualification.stages, event_labels.target); `top` and `positions`
come from the route's own selector; a qualifier whose places the rule does not state as a number has
`places: null` and the text "finish in a qualifying place (the field rule)". `already_qualified` only on recorded
facts (`qualification.secured_places`, `earned_exemptions` as of now). Read only; no random draw.

### Week comparison — `golfsim.decision_support.week_compare(season, career, golfer, year, week)` (implemented)

`{week, year, play: [{event_id, name, eligible, why, cost, tour, selected_field?, opportunities: [...]}],
train: [{category, grade, confidence, observed_level, weakest_rank, observed_as_of}], rest: {fatigue_after},
load: {fatigue, performance_threshold, train_fatigue_after, rest_fatigue_after, played_last_4, played_last_8,
injured_until, recorded_weeks}}`. Grades and levels are the career's recorded observations (scouting), not
ceilings; fatigue forecasts are career.readiness's (the engine's own formulas).

### Timeline — `career.view()['timeline']` (implemented)
`[{date: [year, week], kind: 'control'|'decision'|'trophy'|'result'|'staff', text, golfer_id}]`, oldest first, from
records only (golfsim/career_story.py).

### Goals — `career.view()['goals']` (implemented)
Commands: `{schema: 1, type: 'set_goal', goal: {kind: 'win'|'play_in', series_id, by_year} | {kind: 'world_rank'|
'amateur_rank', top, by_year}, version}` -> `{ok, goal: 'G<n>'}`; `{schema: 1, type: 'drop_goal', goal_id}`.
View: `[{id, kind, series_id?, label?, top?, by_year, status: 'active'|'achieved'|'missed'|'dropped', achieved:
[year, week]|null, progress: {position}|null, set: [year, week], golfer_id}]`, newest first. No rule reads goals.
