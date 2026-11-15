# CareerTest2 fixes — engine side (branch `fix/careertest2-coach-entry-labels`, from `fix/retired-fatigue-guard` 5582e27)

Engine only. No change to `tools/observer_career.py`, `tools/observer_career_context.py` or
`golfsim/career_context.py` (HAL's). `career.view()` is not touched (HAL's hook stays free).

## 1. Coach offers hold a place in the coach's book

**Defect (CareerTest2):** coach Hunter Long (9894) offered to coach the player's golfer Reed Mann (8291) in 2029 week 1;
accepting in week 5 was withdrawn, "their book is now full". `staff.approach` queued the player's offer and returned without counting it,
so the rest of the same 1 January market filled the coach's book (capacity 8; all eight stints began week 1).

**Fix:**
* `staff.offer_reservations(season) -> {coach id: (places, share places)}`: the places held by the controlled
  golfer's open coach offers. Derived from the open decisions (so a save is covered as soon as it is read); not held
  for a coach who has stopped working, nor for the golfer's own current coach (no double count).
* The market counts them as taken from its start (client total and the one-third share quota), and an offer made
  inside the market (`approach`) adds its place at once — so neither scouting, established-player approaches nor
  golfers looking for a coach can take it.
* Released when the offer is answered (declined, accepted — the place becomes the stint —, withdrawn) or the coach
  stops working. Open offers are due by the end of their planning period (the game stops for them), so nothing is
  locked for longer.
* Acceptance re-checks the real book; a failed acceptance changes nothing (the current coach is kept) and says why.
  An offer created by an earlier build (no `reserved` flag in its payload) that fails for capacity says so:
  "their book is now full (an offer made by an earlier build, which held no place for it)". Recorded history
  (resolved and withdrawn decisions, stints) is never rewritten.
* All-AI worlds: no career, no reservations, identical (goldens).

The caddie market had the analogous race; fixed in the follow-on `fix/caddie-offer-reservation` (section 1b).

## 1b. Caddie offers hold the caddie (follow-on)

**Defect:** a caddie without a bag who offered to carry the player's bag went on making offers to other golfers in
the same market (`caddie_approaches`), and stayed in the pool AI golfers hire from, so they could be taken before
the player answered; acceptance then failed with "they now carry another bag".

**Fix:**
* `staff.caddie_reservations(season) -> {caddie id}`: caddies held by the controlled golfer's open caddie offers.
  Derived from the open decisions (old saves covered when read); not for a caddie who stopped working, nor for the
  golfer's own current caddie.
* A caddie whose offer goes to the player makes no further offer that market (`caddie_offer` returns `'held'`), and
  held caddies are neither free to make offers nor hireable by AI golfers.
* Released when the offer is answered (accepted: the stint; declined; withdrawn) or the caddie stops working;
  offers are due by the end of their planning period.
* Acceptance re-checks (no double bag: a caddie carries one bag); a failed acceptance keeps the current caddie; a
  successful one ends the old stint and opens the new one in one step. An old offer (no `reserved` flag) that
  fails because the caddie was taken says so: "they now carry another bag (an offer made by an earlier build, which
  did not hold them for you)". History is not rewritten.
* All-AI worlds: no career, nothing held, identical (goldens).

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
* Career record: `entry_evidence` is a new optional attribute (absent → `{}`), `reserved` a new optional payload
  key; nothing existing is rewritten. Career format unchanged (2).
