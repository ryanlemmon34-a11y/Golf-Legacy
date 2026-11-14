# Explicit, copy-only engine migration — proposal (NOT enabled)

Status: proposal with evidence. No code in this branch migrates or unlocks any world. Ryan's original saves are never
touched; nothing here was run on them.

## The problem

A save records the engine fingerprint (`savegame.engine_id`: a hash of the golfsim simulation code). Any golfsim
change gives a new fingerprint, and `Session.open` refuses a world saved by another engine unless
`allow_other_engine=True` (the observer then offers it browse-only). Upgrading the *career record* (format 1 → 2) is a
separate, smaller matter: it happens in memory when a world is read, but it does not make an old world continuable.

## Evidence so far

Two all-AI worlds (career fixture: seed 11, scale 0.05), each built by an old engine to 2027 week 50, then continued
6 weeks across the 2027→2028 winter by (a) the engine that saved it and (b) this branch's engine
(`allow_other_engine=True`), compared by the fixture digest (every golfer's status, tour, lifestyle, ratings,
money, staff; every winner; the world top 100; the cursor):

| saved by | engine id | old engine continues | this branch continues | verdict |
|---|---|---|---|---|
| 30b9fed (ui/career-experience-v2) | `1b5da4a4…` | `a919eee8…` | `a919eee8…` | **identical** |
| 18d6524 / d2554f5 (integration) | `50c43358…` | `439e73aa…` | `ecb4d9a6…` | **differs** (expected) |

The 18d6524 difference is the approved training-fatigue fix (27fdf93: practice accrues fatigue from zero), which
changes AI outcomes by design; its all-AI goldens were regenerated then. So:

* **30b9fed worlds**: this engine continues them exactly as their own engine would (on this evidence: one small
  world, one winter). Migration changes nothing in the simulation.
* **18d6524 worlds**: continuing them under this engine continues them *under the fatigue fix* from the migration
  point on. Not deception if it is explicit and recorded, but the future is not what 18d6524 would have produced.

Also checked: the career record upgrade keeps an ended format-1 career ended (tests), the staged winter only applies
with an active career (an ended career's winter runs atomically, as before), and a legacy pending `season_end` stop
still answers `return_to_ai` only.

## Proposal

A separate command, run only on request, e.g. `python tools/migrate_world.py <source world> <new copy>`:

1. **Copy only.** Refuses if the destination exists or is the source; copies the committed generation; records the
   source's checksum before and after (unchanged), and never opens the source for writing.
2. **Known engines only.** An allowlist of engine ids with their class: `equivalent` (30b9fed: evidence above,
   to be strengthened) or `rules_changed` (18d6524/d2554f5: the fatigue fix), with the changes listed. Unknown
   engines are refused.
3. **At a committed boundary**, not mid-operation; a world in an in-flight archive is refused.
4. **Recorded, not rewritten.** The copy's state gains `migrations: [{from_engine, from_commit, to_engine, to_commit,
   at_cursor, class, changes, when}]`; the new generation is stamped with this engine. The history before the
   migration (archives, records, career log, notices, stints) is kept as it was; the observer can say "continued by
   engine X from 2029 week 2".
5. **Careers.** The format-1 record is upgraded (history = one stint). An ended career stays ended; nothing is
   resurrected. Taking control of a golfer in the migrated copy would be a separate, user-confirmed command (a new
   stint), not part of the migration; not proposed here.
6. **Confirmation.** For a `rules_changed` source the command requires an explicit acknowledgement naming the
   changes.

For Patrick Newton's CareerTest1 (career ended at 2028's end, cursor 2029 week 2, golfer under AI): the migrated copy
would be an all-AI world continuable from 2029 week 2, Patrick an AI golfer, his career record unchanged except the
format upgrade.

**Its source engine, from evidence:** HAL read the extracted save's `CareerTest1/gen_000032/meta.json`
(not modified): engine `02da83dd49b7d16d5c06dd3da719a6a65e17aeed`, commit `unknown`, cursor 2029 week 2 'week',
generation 32. The git engine-id history matches it exactly to commit
`57c47193bf605c2bb71ea953aea6e3d37969c11a` ("Overhaul career experience with factual period reviews, readiness and
injury feedback"), computed independently here:

| commit | engine id |
|---|---|
| 57c4719 | `02da83dd49b7d16d5c06dd3da719a6a65e17aeed` (= CareerTest1) |
| 27fdf93 (training-fatigue fix), 999d83e | `3a6dd75218b90c90b94c2c9f78f3350cc4f450a0` |
| 30b9fed | `1b5da4a4d1f0a8bf637eeb156522b1311fc62a71` |
| 18d6524 / d2554f5 | `50c433588f5ce93bbc658f01b42664ad150c59f0` |

So CareerTest1 is **rules_changed**, not equivalent: between 57c4719 and this branch the simulation gained the
training-fatigue zero-boundary fix (27fdf93; practice accrues fatigue from zero, an approved AI-outcome change),
then engine edits that the all-AI goldens show do not change outcomes (30b9fed: attribute group names, career
view text; 999d83e changed no engine file), then this branch. A migrated copy would continue under the fatigue fix from 2029 week 2. Still to do before enabling:
build a world with 57c4719, continue it with 57c4719 and with this engine, and confirm the only difference is the
fatigue rule (e.g. identical with the fix reverted).

## Risks and open points

* The equivalence evidence is one small world over one winter: before enabling, run several seeds and full scale
  over multiple seasons, and a career-ended world, against the source engine.
* Pickled classes: new attributes must have defaults when read (the winter progress uses `__dict__.setdefault`;
  the career upgrade adds stints/winter). Any future field must follow the same rule.
* Every later engine change needs its own allowlist entry and evidence; the tool must never wave a world through.
* A `rules_changed` world's later history mixes two rule sets; analyses across the migration point should say so.
