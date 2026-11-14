# Initial player selection — engine contract

Branch `feature/career-initial-selection` from `feature/career-year-end` 5a94dbe. HAL owns the pages (the annual
newcomer cards can be reused unchanged: same keys, same facts).

## What the player chooses from

At a season's 1 January (cursor `{week: 1, phase: 'start'}`), in a world with no career and a junior class for that
season: ten juniors of that class, `career.candidates(season, year)` — the **same** seeded sample
(`{seed}:career:candidates:{year}`) and the same public facts (`candidate_facts`) as the annual newcomer choice;
the whole class when it has ten or fewer. They are ordinary members of the class the normal entrant rules created,
whoever is chosen; nobody is created or rerolled; the list is a pure function of the committed world (stable across
refreshes and reloads); building it draws nothing from the world's random streams. No potential, ceilings, peak age
or aging rate is shown.

## Read model (committed)

`golfsim.career.start_view(season, cursor)`, captured into the observer's committed snapshot as
`LiveView.career_start` (tools/observer_live.py, one line beside `career_can_start`). `null` when no career can start
here: a career exists, the cursor is not a season's 1 January, or there is no class yet.

```
career_start = {
  "year": 2028,
  "cursor": {"year": 2028, "week": 1, "phase": "start"},   # post it back as the expected cursor
  "class_size": 287,
  "text": "Choose who to play as from 2028: ...",
  "options": ["1009", "1019", ...],                        # the answer keys: golfer ids as strings
  "choices": [{"key": "1009", "label": "Nick Marsh", "facts": {...}}, ...],
  "candidates": [{...}, ...]                               # = choices[i].facts
}
```

`facts` (identical to the annual `choose_newcomer` candidates): `id, name, country, age, status, lifestyle, tour,
overall, attrs [[group, [[key, value], ...]], ...], funds`. Every key is always present (`tour` may be null).
There is no `end_career` choice here (not starting is simply not posting).

Fixtures: `docs/career/initial_selection_fixtures/`.

## Command

`{"schema": 1, "type": "new_career", "golfer": "<id as a string>"}` with the session's `expected` cursor and an
`op_key` (the existing `/career/start` path; it needs only the extra `golfer` field).

* Refused (nothing changed): a golfer not among `options`, a non-string id, a world that already has a career, a
  cursor that is not a season's 1 January, no class.
* A stale cursor raises `StaleCursor`; an `op_key` replay returns the first result.
* Result `{"ok": true, "golfer": id, "name": str}`. The career's entry (and first stint) records
  `{"kind": "junior", "class": y, "class_size": n, "candidates": 10, "rule": "chosen by the player from a seeded
  sample of the season's junior class"}`.
* The original command **without** `golfer` keeps its old meaning (a seeded uniform draw over the whole class), so
  existing tools and tests are unchanged. The launcher should stop at the picker and always send `golfer`.

## Compatibility

* No world state changes until the command: all-AI worlds and their goldens are unaffected; choosing different
  candidates leaves identical worlds until the season runs (test).
* Existing active and ended careers load as before; `start_view` is null for them.
* Note for HAL: the observer's `career_can_start` currently offers a start only in a world's second season
  (`first_year + 1`); `start_view` itself is available at any season's 1 January with a class. Which to use is a UI
  decision.
* No prologue or auto-simulation is added.
