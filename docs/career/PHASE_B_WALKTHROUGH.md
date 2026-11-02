# Career mode first slice (Phases A and B): walkthrough, tests and limits

This branch (`build/career-v1-foundation`) adds a playable four-week career slice to the wide-screen observer. It is
not merged and not released; `main` is unchanged. The plan and its boundaries are in `PHASE_AB_PLAN.md`.

## Try it

From the project folder:

```
python tools/observer_app.py --worlds <an empty or test library folder> --open
```

1. **Library → Start a new career.** Give a name, a starting year (default 2027) and a seed. A background job creates
   the world and plays its first season under AI (a few minutes on a desktop; the progress bar shows the weeks). It
   then gives you one of that world's own new juniors, chosen by a seeded draw, at the start of the second season.
   Nobody is added to the world for you.
   - Faster for testing: open any world that is at the start of a season (for example a copy of the test fixture,
     `tests/career_fixture.py`, seed 11, scale 0.05) and use **Career → Start the career** there.
2. **Career home** (`/career`): the golfer, date, money, path, injury and fatigue, ordinary ratings (potential is never
   shown), decisions with deadlines, notices, and the current four-week block.
3. **Advance to next decision.** The first stop is the plan for the block (and any staff offers, which are decisions).
4. **Planner** (`/career/plan`): for each week, the events the golfer can enter now (date, place, tier, cost), the
   events they cannot enter with the reason, training (with a category) and rest; a fallback for event weeks; the
   selected-entry and qualifying policies. An ineligible or stale submission comes back with the reason and changes
   nothing.
5. **Advance through planned period** plays the four weeks. One advance request is one save (the session's existing
   transaction rule): weeks are played in memory and committed together when the request ends.
   - **Stop** (cancel) takes effect between weeks: the request ends normally and the completed weeks are saved.
   - **An error** (or the observer being killed) during the request rolls the whole request back to the last save,
     in memory and on disk: none of its weeks are kept, and the world is never half-written. The job says so and
     names the date the world is at.
   - Re-submitting the same form says "Already applied"; a form from an older page is refused.
6. **Return golfer to AI control** (asks for confirmation). The AI plans the rest of the current block for the golfer
   and the world continues normally.

Reloading the page, restarting the observer, or reopening the world at any point shows the same committed state.

## What changed in this checkpoint

- Defect fixes (commit `0237ba8`):
  1. `Session.advance_one_week` and `advance(commit_every_week=True)` return a stopped result at a career gate
     instead of failing on an empty list.
  2. Handing the golfer back mid-block gives the rest of that block to the AI (`Season.replan_after_handback`,
     private RNG, no staff, money, statistics or evidence side effects). A prepared week keeps its plan; a block
     start is left to the normal planner.
  3. A keyed request blocked by a pending choice is recorded, so replaying it later returns the recorded outcome
     instead of advancing; commands carry an expected career version and are refused if it moved.
- Review fixes (after `f486c1f`): the transaction rule above is described as it is and tested; career posts are
  refused unless they come from this observer's own pages (an `Origin` of another site or `null`, or
  `Sec-Fetch-Site: cross-site`, is refused for every POST) and carry the full command identity (world id, date,
  phase, career version except when starting, operation key); pages send `Referrer-Policy: same-origin` and
  `X-Frame-Options: DENY`.
- Engine fix (merged at `da4075e`; reviewed, test branches only): `fix/engine-dogleg-retee`, engine `e99cb20`.
  - Tee plans price a dogleg run-through where play puts the ball, and a reload after out of bounds re-plans.
  - It fixes a runaway hole found in a long realism-branch world; the defect is latent on main too.
  - The all-AI equivalence reference is now main + fix (`8a2b92a`).
- Phase B observer routes: `/career`, `/career/plan`, `/career/start`, plan submission (POST `/career/plan`), `/career/decide`,
  `/career/end`, `/career/advance` (background job), `/career/new` (background job). Each POST carries world, date,
  phase, career version and an operation key; the page is always redrawn from the committed generation. Forms are
  accepted only from the local observer origin.

## Tests

```
python -m unittest tests.test_career_foundation      # 25 tests: Phase A + the three defects (ParkedDefects)
python -m unittest tests.test_observer_career        # 9 tests: the slice over HTTP, guards, rollback
python -m unittest tests.test_session tests.test_development tests.test_access_ledger   # regressions
python -m unittest tests.test_tee_plan                # 11 tests: the engine fix
```

- `ParkedDefects`: stopped result from `advance_one_week` and `advance(commit_every_week=True)`; mid-block handback
  plans the remaining weeks with no side effects and survives reload; prepared-week handback keeps that week;
  block-start handback leaves planning to `plan_block`; a blocked keyed request is recorded, replays identically
  after reload, and a stale version is refused.
- `AllAI` (in `test_career_foundation`): with no career, the season digests are unchanged from main (all-AI
  equivalence after the planner refactor).
- `test_observer_career`: the four-week slice through the pages (ineligible event refused with its reason, event,
  training and rest planned and played, repeated and stale submits, confirmed handback); save and reload between
  requests and across an observer restart; an interrupted advance keeps the completed weeks on disk; refusals (other
  world, second career, unknown decision); no placeholder or disabled controls and no potential or ceiling on the
  pages; views change nothing. `Guards`: posts from another origin, a `null` origin or a cross-site fetch are
  refused (403) on start, end, advance and new career, and the observer's own page still works; a form missing
  any identity field, with a malformed date or phase, a stale version or a stale date changes nothing and starts
  no job; an error in week 3 of a planned period leaves memory and disk at the last save.

## Limits (by design for this slice)

- Stops before the winter: turn pro, residence, retirement, college moves and the season review are Phase C. Hand
  the golfer back to let the world continue.
- No customization, choice of newcomer, rerolls, entry into an existing world, golfer-initiated staff hiring, paid
  work weeks, sponsorship, full finance ledger, separate inbox, mobile layout or Birth of Pro Golf.
- Performance is measured on Ryan's machine; the cloud timings in the test logs are not the target.
