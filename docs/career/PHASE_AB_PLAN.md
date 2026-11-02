# Career mode, Phases A and B: plan and exact boundaries

**Authorization.** Ryan, 2026-11-02 01:06 UTC (see `ROADMAP_V1.md`).
- Branch `build/career-v1-foundation`, cut from released main 18a8e23. Main stays unchanged; no merge or release.
- This assignment covers roadmap Phase A (the human-control foundation) and Phase B (a minimal playable New Career
  four-week slice) only.
- The headroom experiment stays on its own branch; nothing of it is in this branch.

## 1. Inventory: what exists, what is missing (main 18a8e23)

| need | exists today | missing for career mode |
|---|---|---|
| world clock and safe advance | `Session`: weekly cursor (`start` / `week`), StaleCursor, operation keys, atomic checkpoint generations | the step is atomic: 1 January runs with week 1, and week 52 runs the winter (`finish_year`: careers, aging, entrants) inside the same step, so there is no place to stop before a decision |
| plans | `Season.plan_block` every four weeks (13 blocks): play / train / rest / work per week, for every golfer | no owner: it plans every golfer, so it would overwrite a human plan |
| event entry | `regular_entries`: eligibility (`eligible`), affordability, travel and day clashes, deferred acceptance by priority | the golfer's choice is AI (`event_value` against a bar), with no way to state "this event" |
| rule-selected events | `special_field`: majors, invitations, championships, college postseason; qualifiers by a random "keenness" draw | selection ignores the golfer's plan, so a human golfer could be placed somewhere they did not choose |
| development | `develop_week` from the plan: play / train (category) / rest / work, injury rules | when an entry fails, the golfer trains in the AI-chosen category |
| staff | `staff.start_of_season` at 1 January: coach scouting approaches, fee approaches, golfer-initiated hires, caddie approaches and hires | every answer is drawn on the spot (`golfer_answers` / `golfer_takes_caddie` plus a random coin), with no pending offer |
| newcomers | the junior class and new professionals are generated at each winter (`careers.add_juniors`), with stable ids and creation records | no career record, and no rule for which newcomer a player takes |
| observer | wide-screen pages from a committed snapshot (`observer_live`); background jobs; POST forms | no career pages, actions or interruption handling |
| privacy | the observer never shows potential | career pages must keep that boundary |

## 2. Design (Phase A)

**Where the career lives.**
- One object, `season.career` (`golfsim/career.py`), is pickled inside the same checkpoint as the world, the clock and
  the session state, so it is saved together and atomically.
- `None` means an all-AI world: every engine hook is a no-op, and behaviour must equal main bit for bit (tested).

**The record.**
- Career id, golfer id (stable person id), control state (`active` / `ended`), start date.
- Plans per block, each week's choice and fallback.
- Decisions with stable ids: kind, created, deadline, payload, and state (`pending` / `accepted` / `declined` /
  `expired` / `resolved`).
- Notices: a bounded list.
- Processed operation keys: a bounded list, so a repeated submit returns the stored result.

**Actions.** Each one is validated by the same rule services the AI uses, and returns a result or a plain reason:
- `plan_block`: choose each week's event, training category or rest, the fallback if an entry is not accepted, and
  the block's policy for rule-selected events and qualifying;
- `decide`: accept or decline an offer; re-plan an invalidated week;
- `end_control`: return the golfer to AI control;
- advancing time.

Actions go through a new `Session.career_action`: the lock, sync, the operation-key check, a stale check (cursor and
career version), apply, then commit a new generation, exactly like an advance.

**Shared validation and consequences.** The human path calls the same code as the AI.

| | how the human golfer is treated |
|---|---|
| eligibility | `Season.eligible` |
| costs | `FIN.event_cost` / trip cost against `spendable` |
| day and travel clashes | the existing checks |
| field acceptance | the same deferred acceptance and priority: no guaranteed entry |
| development | `develop_week` |
| coach offers | answered through the same `assign_coach` / `refuse` code as the AI, and revalidated when accepted (coach still active, room, fee affordable) |
| caddie offers | the same, through `assign_caddie` / `refuse` |

To keep random streams aligned, the engine still consumes, for the human golfer, the random numbers the AI path
would have drawn. It then uses the human's choice in place of the AI's answer. (Outcomes may still diverge once
choices differ; that is expected.)

**Stops before consequences: the split boundary.**
- When a career is active, the session steps in parts: `start` (1 January only), `week` (one week) and a new `end`
  phase (the winter, after week 52).
- Before each part it asks the career gate whether anything must be decided first. A blocked gate stops the advance
  with the reason; nothing of that part has run. The gates:
  1. **No plan for the block.** The week about to be played has no human plan.
  2. **Plan invalid now.** The week's planned event is no longer valid when it becomes effective: eligibility, money,
     injury or a clash. This is checked again with the same functions; the player re-plans the week.
  3. **Offer deadline.** A pending offer would expire before the next part.
  4. **Winter.** The winter is not playable in this build (see boundaries). The golfer can be returned to AI control.
- Without a career, the parts run exactly as today's single step: the same order and the same results.

**Rule-selected events and qualifying.**
- The block plan carries the player's explicit policy:
  - "if selected or invited this period: accept / decline" (majors, invitations, championships, college postseason);
  - "qualifying events: enter if eligible / don't enter".
- The engine applies the policy where the AI would accept automatically or draw its keenness. There is no default:
  the planner requires the choice.

**Entry failures.** If a valid entry is not accepted (field full, priority, college lineup), the week's declared
fallback applies (train a chosen category, or rest), and a notice says why. Failures that can be known before the
week (eligibility, money, injury) stop the advance first, as gate 2.

## 3. New Career bootstrap (Phase B, a simple fixed rule, provisional)

- New Career creates a fresh world (seed and starting year as in the library) and plays its first season under AI,
  with progress shown, so the world's own junior class for the second season exists. It then takes one golfer from
  that class.
- **The pick** is a uniform draw keyed by the world seed over the class's ids, in id order. Nothing hidden or
  ability-based is used, so no protagonist advantage.
- **Control** starts at the second season's 1 January, before the staff market runs, so offers to the golfer become
  decisions.
- **One newcomer, no extra golfer.** No golfer is created and none is duplicated; the person already exists in the
  world. Re-running New Career on the same world is refused.
- **The starting path** is the one the normal entrant rules gave the golfer (college division or amateur series),
  shown with its reason. Choosing among paths is Phase C.

## 4. Interface (Phase B, in the existing wide-screen observer)

- **New Career form.** World name, seed, starting year. A background job shows its progress.
- **Career home** (`/career`):
  - the golfer and the date, plus control state and ordinary attributes, with no potential;
  - money available, the tour or college path, injury and fatigue;
  - required decisions with their deadlines and actions; recent notices; the current block's plan and its status;
  - the controls "Advance to next decision" and "Advance through planned period" (labelled as four-week blocks,
    not months), and "Return golfer to AI control".
- **Planner** (`/career/plan`):
  - each week of the block lists the events the golfer can enter now, with date, place, tier and cost;
  - events the golfer cannot enter are shown with the reason;
  - training categories and rest; the fallback for event weeks; the two policies.
  - Invalid submissions come back with reasons and nothing changes.
- **Pages.** Ordinary world pages stay available. The standard observer advance buttons respect the same gates.
  Every career form carries an operation key and the expected date, so a repeated or stale submit changes nothing.

## 5. Exact boundaries: not in this assignment

These are left for Phase C and later, after review. Each is shown honestly in the UI where the player would meet it;
there are no placeholder buttons.

| item | Phase B behaviour |
|---|---|
| customization (name, origin, starting path choice) | not offered |
| entry into an existing world; choice of newcomer; rerolls | not offered |
| winter (turn pro, residence, retirement, college moves, staff year end) and season review | stops before the winter. "Return golfer to AI control" lets the world continue, with the golfer then decided by the AI |
| annual switching; former-player category | not offered |
| golfer-initiated hiring of coaches and caddies | not offered. The AI step that would have the golfer look for a coach or caddie is skipped for the human golfer; offers *to* them are decisions. This is a disadvantage, not an advantage; it is documented |
| paid work weeks | not offered. The work pathway for cash-blocked adult amateurs is skipped for the human golfer; the newcomer is 18 |
| finances | a summary (funds, costs of planned trips); no full ledger page |
| inbox | the career home lists decisions and notices; no separate inbox |
| sponsorship, negotiation | none |
| per-event invitation dialogs | a per-period policy instead |
| mobile layout; Birth of Pro Golf | none |

## 6. Open choices surfaced, provisional and not locked in

1. The newcomer pool: juniors only (18-year-olds) here; late-entry professionals are not included.
2. The pick: a uniform seeded draw, against letting the player choose from several candidates (Phase C).
3. Whether New Career needs a fresh world with one AI season first (here), or may start in an existing world at a
   season boundary.
4. Plan granularity: four-week blocks (engine), labelled honestly; whether to add calendar months is undecided.
5. Offer deadlines: offers made at 1 January stay open until the end of the first block (provisional).
6. The policy for rule-selected events is per period, against per event (Phase E).
7. Season end: stop and return to AI control is a stop-gap until Phase I.

## 7. Tests and evidence (before publication)

- **All-AI equivalence.** A digest of a fixture world after a season on this branch equals main 18a8e23's.
- **Gates.** Advancing stops before every gate. The standard observer advance obeys the gates. Season-end stop and
  return to AI.
- **Idempotence and staleness.** The same action applied twice or resubmitted produces one plan, acceptance or
  assignment. A stale submit is refused. Accepting an offer twice assigns one coach.
- **Reload.** Close at an interruption and reload: the same decision at the same date.
- **Determinism.** The same actions from the same save give identical states.
- **No AI overwrite.** After `plan_block` runs, the human plan is intact.
- **Validation.** Entry-failure paths: ineligible, unaffordable, clash, shut-out fallback, injury.
- **Genuine newcomer.** One per career, no duplicate person, identical golfer after reload.
- **Privacy.** No potential or ceilings in career data or pages.
- **No player-only advantage.** Same eligibility and priority functions; no guaranteed entry.
- **UI.** A Playwright walkthrough of the observer flow: New Career → plan → eligibility failure → advance →
  interruption → reload.
- **Regression.** The focused session, season and observer suites. Any full-suite run is reported as such.
- **Performance.** Relative to main, in this environment: action commit, advance overhead with a career, and page
  times. This is not Ryan's 120-second target.
