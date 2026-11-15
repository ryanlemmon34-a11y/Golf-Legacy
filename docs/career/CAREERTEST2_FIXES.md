# CareerTest2 fixes — engine side (branch `fix/careertest2-coach-entry-labels`, from `fix/retired-fatigue-guard` 5582e27)

Engine only. No change to `tools/observer_career.py`, `tools/observer_career_context.py` or
`golfsim/career_context.py` (HAL's). `career.view()` is not touched (HAL's hook stays free).

## 1. Coach and caddie offers: answered at the same point of the market (supersedes 355555d / 61330b3)

**Defect (CareerTest2):** coach Hunter Long (9894) offered to coach the player's golfer Reed Mann (8291) in 2029
week 1; accepting in week 5 was withdrawn, "their book is now full": the offer held nothing and the rest of the same
1 January market filled the coach's book.

**First fix (355555d, 61330b3), withdrawn after a parity audit:** open offers held a coach place / a caddie until the
player answered (up to the end of the period). An AI golfer answers an approach on the spot, and its no frees the
place for the rest of the same market; the player's hold kept a declined place empty for a whole year and let the
player hold several offers at once -- option value and denied places no AI golfer has. Removed
(`offer_reservations`, `caddie_reservations`, the `'held'` return, the payload `reserved` flag).

**Rule now (equal decision timing):** the 1 January staff market (staff.start_of_season) runs in a fixed order and
an AI golfer answers each approach on the spot. For the controlled golfer:

1. Before 1 January runs, the engine runs 1 January on a throwaway copy of the world (`Season.market_probe`); the
   copy stops at the first approach to the player not yet answered (`staff.MarketQuestion`). The real world has not
   moved: the cursor stays at 1 January 'start'.
2. That approach becomes a decision (`coach_offer` / `caddie_offer`, payload `market: <year>`), due at once
   (deadline = 1 January: the market waits for it; no later deadline is shown). One at a time.
3. The answer is recorded (`career.market_answers[year]`). When the real market reaches the same approach
   (`staff.market_answer`) it is applied there, with the same random draw an AI golfer's answer takes: a yes takes
   the place then; a no leaves it to the next golfer in the same market. The next approach to the player, if any,
   is found the same way.
4. A coach approaches only with room (total and share quota, the market's own counts) and nothing is allocated
   between the approach and the answer, so every market offer is capacity-backed when answered. A fee the golfer
   cannot commit to is refused by the AI's own rule (chance 0) without asking.
5. Paired tests (tests/test_market_parity.py): the same world and the same choice, answered by the player and by an
   AI golfer forced to that choice, give identical worlds -- coach accept/decline in both orders, caddie
   accept/decline -- and reloading between answers changes nothing.

Offers left pending by an earlier build (made outside a probed market) are still answered later and re-checked
(an honest "their book is now full" if so; the current coach kept). Recorded history is never rewritten.
All-AI worlds: unchanged (goldens).

Still a capability gap, not an advantage: the player never *looks for* a coach or caddie themselves (the AI's own
search step is skipped for them, its draw still taken). If built, it must use the same search rule.

## 2. Truthful entry reasons

Evidence is recorded for the controlled golfer **when each decision is made** (`Season._career_evidence`, kept in
`career.entry_evidence[(year, week)]`), and read through one canonical API:

`career.week_entry(season, career, year, week) -> dict` (keys always present; unknown facts are `None`):

| key | meaning |
|---|---|
| `recorded` | True when the evidence was recorded at decision time (this build on); False for older weeks |
| `choice` | the player's plan for the week: `{kind, event}` |
| `access`, `access_code` | the season's own week classification (`Season.ACCESS`) and its code (`career.ACCESS_CODES`) |
| `event`, `event_label` | the event the player's entry was for; contextual label (item 3) |
| `code`, `text` | why the entry stood or not: `career.ENTRY_TEXT` (one canonical text per code) |
| `position`, `applicants`, `capacity`, `admitted` | the player's place in that event's entry order, how many asked, the field size, how many were taken — **as decided that week**; `None` when no entry order was decided (or for older weeks) |
| `by` | for `superseded`: the rule-selected event that came first |
| `entered` | what they played: `{event, how ('entry' / 'selected'), label}` |
| `declined` | rule-selected series not taken because of the period's policy (`selected: decline` / `qualifying: skip`) — no hypothetical selection rank is ever computed |
| `clashed` | rule-selected series the golfer was dropped from by a clash that week |

Codes (`ENTRY_TEXT`): `entered`; `school_lineup` (a college golfer's tier-5 school event: the lineup rotation, not
capacity); `field_full` (behind the field's last place in its entry order); `quota` (inside the field's size but an
amateur/visitor limit was reached); `not_eligible`; `clash`; `cost`; `superseded` (a rule-selected place came first,
e.g. CareerTest2 2029 W17). The player's note for a failed entry now uses the same text (no longer "field full"
for a college lineup, e.g. 2028 W7 CO_US_D1_05).

Older saves: weeks before this build return `recorded: False`, with only what the season's `access_log` holds
(`school_lineup` / `field_full` and the wanted event; never a position or cut-off). Each weekly recap now also keeps
`entry` (the same dict) from this build on.

For HAL's "provisional vs secured" (item 4): `week_entry` only reports what was decided; a qualifier finish is not a
place in the target event until that event's field is decided (its own `week_entry` / `entry_routes`).

## 3. Contextual labels and qualifier targets

`golfsim/event_labels.py` (read only; series ids, names, schedules and recorded history unchanged):

* `label(cal, series_id)`: the name, or for names shared within the calendar the name with what tells them apart,
  e.g. `USA Amateur Championship (72-hole stroke play, national amateur championship, week 29)` (NATIONAL_AMATEUR_USA;
  its week varies by world) vs `USA Amateur Championship (match play, open amateur championship, week 33)`
  (USA_AMATEUR). Every label in a calendar is unique; unique names are returned unchanged.
* `target(cal, series_id) -> {id, label, week} | None`: the event a qualifier feeds, from the field rules —
  USA Amateur Qualifying (W30) → USA Amateur (W33), not the national championship; USA Open local → final → USA
  Open; Britannia regional → final → Britannia Open; club professional sectionals → championship; Q-school stages
  in order; college regionals → national championship. Always earlier than its target (tested on v1/v2).
* `context(cal, series_id) -> {id, name, label, week, target}`.

## Save compatibility

* golfsim changed, so the engine fingerprint changes: worlds saved by 5582e27 open browse-only in this build (as
  for every engine change); no migration is enabled. Original saves are never written.
* Career record: `entry_evidence` is a new optional attribute (absent → `{}`), `market_answers` / `market_probe` new optional attributes (absent → none), `market` an optional payload
  key; nothing existing is rewritten. Career format unchanged (2).
