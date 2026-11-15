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
| Visible current qualifications and placement unlocks | **partial** | HAL's `career_context` reads card reasons, winner exemptions, Premier rights. Engine canonical `qualifications` read model: **not implemented** (contract below). |
| Early invitation notices | **not implemented** | Selection is decided in the event week. Only routes already decided (e.g. a winner's exemption, a card) can be noticed early; anything else would be a prediction. Design needed with HAL. |
| Usable coach / caddie offers | **done (reworked)** | Market offers answered at the same point of the 1 January market as an AI golfer's (probe on a copy; same draw); the earlier holds were withdrawn after the parity audit. Paired human/AI tests. |
| Player choosing staff themselves (hire a coach/caddie) | **not implemented** | Today the player only answers offers; the AI "looking for a coach" step is skipped for them. |
| Thirteen fixed four-week periods; interruptions resume within the period, one recap | **done (verified)** | tests/test_period_cadence.py. |
| Editable four-week plan accepting coach advice | **done (UI); engine decision-comparison evidence not implemented** | HAL's reviewable advice (c36f17b); the engine plan command needs nothing new. |
| Season results / season review | **done** | `year_end.review` (YEAR_END.md), weekly recaps with entry evidence. |
| Factual inbox / calendar / recaps | **partial** | Engine: notices, log, decisions, recaps, planner, `week_entry`. Inbox/calendar presentation: HAL. |
| Trophies (majors, college, amateur championships) with engraving and multi-win history | **done (engine read model)** | From recorded winners only (`ctx.results` keeps every winner for good). Contract below. |
| Per-category fallible potential letter grades | **done (engine read model)** | `golfsim/scouting.py`: observations persisted in the career record at control start and each season review; the judge's seeded persistent error; never ceilings or potential. Grades A/B/C/D/F only. |
| Optional goals | **not implemented** | Player-set, persisted, progress derived from records. Contract below. |
| Relationships, timeline / living history | **partial** | Stints, staff relationship records, career log and notices exist; a canonical `timeline` read model: **not implemented** (contract below). |
| Distinctive fictional tournament names | **not implemented** — needs a scoped decision | Renaming series changes names in every world (and engine fingerprint); history must keep the names it was recorded with. Proposal: a new calendar version or display-name table keyed by series id with the old name kept for recorded years. Not started (kept out of the duplicate-label fix). |
| College qualifier overhaul (4 early-spring qualifiers, 39 each, all US college tours, heats) | **not implemented** (design ready) | `QUALIFIER_DESIGN` (fair heats, ~720 entrants, 5 heats 8/8/8/8/7). New calendar version v3 only; v1/v2 unchanged. |
| Same-year USA Open place for the college national champion (amateur) | **not implemented — flagged for scope accounting** | Authorized earlier by HAL; v3 only; to be confirmed in the final scope before enabling. |
| Finance trace | **partial** | Ledgers and money evidence exist per season (pruned after a season, archived); no career-facing trace read model. |
| Sponsor / backer explanations | **partial** | Backer reviews and sponsor offers are recorded with reasons in the AI; career-facing explanations not built. |
| Annual tracking | **partial** | Year-end review per season; stints; multi-season summary read model not built. |
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

### Qualifications — `career.qualifications(season, gid, year)` (proposed)
`[{event_id | series_id, label, route, source: "card" | "winner" | "rights" | "major" | "selected" | "qualifier",
 decided: [year, week], secured: bool}]` from recorded routes only; `secured: false` for a provisional route (e.g.
a qualifier finish before its target's field is decided).

### Timeline — `career.timeline(season, career)` (proposed)
`[{date: [year, week], kind, text, refs}]` from stints, decisions, notices, results, trophies, staff stints, moves;
nothing invented.

### Goals (proposed; persisted)
Command `{type: "set_goal", goal: {kind, target, by_year}}` (versioned, exactly-once); `career.view()['goals']`
with progress derived from records. Not built until the timeline exists.
