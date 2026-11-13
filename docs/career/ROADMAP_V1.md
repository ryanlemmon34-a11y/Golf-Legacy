# Golf Legacy Career Mode Roadmap: design target

**Authorization record (added on this branch, 2026-11-02).**
- Ryan asked for a detailed roadmap to the first version of career mode. HAL delivered the planning draft below
  (dated 1 November 2026).
- Ryan then replied (2026-11-02 01:06 UTC): "Great. Let's move forward with this as a branch."
- Career-mode development is therefore authorized on this separate branch, `build/career-v1-foundation`, cut from
  released main 18a8e23. The first assignment is roadmap Phases A and B only.
- Main stays unchanged. No merge or release is approved. Birth of Pro Golf stays planning-only.
- The draft's statements that career development "has not been authorized" are historical: they describe the moment
  it was written.
- Its recommended defaults remain provisional. Consequential open choices are surfaced, not silently locked in (see
  `PHASE_AB_PLAN.md`).

The draft follows. Page headers and footers from the PDF extraction have been removed; the wording is otherwise kept.

---

# Golf Legacy Career Mode Roadmap
From the current world simulation to a first playable career. Prepared for Ryan Lemmon. Planning draft, November 1 2026.

We are close enough to plan career mode in detail. My recommendation is to build it as a human decision layer over the
same world simulation, starting with a small playable season loop and expanding it into a complete career. We should
not wait for every possible world feature, but we should settle the simulation problems that would make player
decisions misleading or frustrating.

The first version succeeds when an ordinary golfer can have an interesting season: choosing events, training and rest;
reacting to opportunities; managing a modest budget; and deciding whether to keep playing that golfer next year.
Becoming the best player in the world is neither promised nor required.

## What Ryan has already decided

- The world comes first. Careers and memorable relationships should emerge from simulation, not scripted success or
  protagonist advantages.
- New Career assigns a genuinely new world entrant at the beginning of a season. Normal attributes are visible; hidden
  potential stays hidden.
- The player can name the golfer, choose where they are from, and choose among starting tours available to that golfer.
- At each season end, the player can continue or switch to a different new entrant. Previous golfers remain in the world
  under AI control and receive a special shortlist category.
- The player needs month-to-month or finer control, including tournament, training and rest decisions and prompts when
  opportunities or eligibility change.
- Former player-controlled golfers may later become coaches through normal world rules. Hiring one should be possible
  when the circumstances fit, never guaranteed.

## How to use this draft

The phase order and suggested defaults below are recommendations, not approved implementation instructions. Career mode
has not been authorized for development *(historical: see the authorization record above)*. The current starting-ability
experiment stays separate, and Birth of Pro Golf remains a separate world-start concept. This draft does not assign a
numeric release version or promise a delivery date.

## 1. Establish the starting point

### What the current release evidence supports

The reviewed v17 build was released to main at commit 18a8e23. Its final test run reported 1,136 tests, with four
documented skips. That is a useful foundation, not proof that a human-controlled career already exists or that all
balance and performance questions are closed.

The recent pass addressed tournament-history loading, global list sorting, national newcomer allocation, injury
eligibility and a top-15 amateur pathway. Whole-season speed did not show a meaningful improvement in the measured
comparison. The long-world history cache also retains a substantial cold-build cost. These limits should remain visible
in the career plan.

The first starting-ability study did not solve the frequency of nearly finished teenagers. A separate headroom experiment
is now approved and running. Its purpose is to reduce excessive readiness at entry without lowering eventual potential or
erasing rare teenage stars. No new tuning is approved for production yet.

### Reusable foundations verified in the code

The current Session already advances by week with stale-cursor checks, operation-key idempotence and atomic checkpoints.
The observer offers week, four-week, season and multi-season controls. AI planning already assigns play, train, rest and
work in four-week blocks. Eligibility, affordability, funding ledgers, staff approaches and stable person identities also
exist. These are reusable foundations, not a completed human-control layer.

### Prerequisites before career implementation

- Split the weekly boundary where necessary. Session currently executes fields and results before returning; week 52
  also processes winter decisions, aging and entrants. Career mode must stop before the player's consequential choice,
  not afterward.
- Map shared rule services for eligibility, costs, training, injury and staff. Reuse them for human choices; do not grant
  guaranteed field entry by bypassing selection.
- Assign ownership of turn-pro, work, retirement, residence and staff decisions, including winter actions. The current AI
  planner and instant offer responses must not silently overwrite human choices.
- Record a reproducible baseline on Ryan's computer: world size and age, seed, simulation interval, cold and warm page
  timings, save/load time and memory. Apply the 120-second target only to the agreed benchmark scenario, not every
  operation.
- Choose whether the headroom experiment is ready to ship, should be revised, or should remain unchanged for the first
  career test. Do not hide an unsettled balance change inside the career branch.

### What should not delay the first career build

Birth of Pro Golf, a full economic history model, mobile layouts and preservation of every old development save should
not be prerequisites. Ryan's wide-screen experience comes first. Compatibility within the released career build still
matters: a player must be able to save and resume a season reliably.

**Exit test.** A short implementation inventory identifies existing reusable systems, missing control points, unresolved
blockers and the exact baseline commit. A career test is not declared ready merely because older simulation tests passed.

## 2. Define the first playable scope

### Included in Career Mode V1

- One controlled golfer at a time in a persistent world, with a clear current date and a visible player-control state.
- New Career setup, eligible starting-path selection and the ability to resume a saved career without recreating the
  golfer.
- A calendar that supports event entry, training and rest, plus safe advancement to the next decision or chosen planning
  horizon.
- Actionable notifications for important offers, deadlines, failed entry plans and material injury or financial changes.
- Readable finances and an explanation of what prevents an action, with realistic support opportunities using the
  world's rules.
- Meaningful coach and caddie choices where those systems support offers and contracts, plus clear sponsorship and
  support information.
- Tournament participation through the existing simulation, linked results and a short factual explanation of what
  happened.
- Season review, continue-or-switch choice, persistent former-player tracking and normal AI continuation of previous
  golfers.

### Deliberately outside the first release

Direct shot control, a new match engine, mandatory detailed negotiation, lifestyle management, elaborate media
interviews, scripted rivalries and a guaranteed route to elite golf would add scope without establishing the core
career loop. They should not be assumed part of V1.

Birth of Pro Golf can later supply another starting world for career mode. It should use the same control layer, but its
population growth, institutions, calendar and economy require their own design and validation. It is not simply a
small-world switch that we can assume works automatically.

### The smallest useful first slice

Start with one new golfer, one planning period, a few eligible events, training/rest choices, an entry failure and a
save/reload. The world should continue normally around that golfer. This deliberately small slice tests the architecture
before we invest in attractive screens or a full year of content.

### Dependency order

Stable simulation boundary → explicit human control → new-golfer setup → planning and advancement → interruptions and
finances → staff choices and support → season handoff and legacy → full-world testing and release.

Screen design and test fixtures can proceed alongside the control work. Financial and notification requirements should
be designed early, even if their full interfaces arrive later. Do not build separate interim rule systems that will have
to be replaced.

**Exit test.** We can explain V1 in one sentence: play a golfer's season through meaningful decisions, then continue their
career or join the next generation without leaving the world behind.

## 3. Build the control foundation

### Phase A: Separate player decisions from world simulation

Introduce a durable career record referencing a golfer by stable identity. Keep attributes, results and relationships in
normal world data. Store control spans, plans and pending decisions in authoritative saved state. The existing observer
shortlist is a separate UI file, not a safe home for career ownership or unresolved offers.

- Create explicit action types for enter or withdraw, choose training, rest, accept or decline an offer and advance time.
  Each action returns a valid result or an understandable reason it cannot proceed.
- Give the controlled golfer a human decision provider. AI golfers continue using their existing provider. Both call the
  same validation and consequence logic.
- Make an advancement request stop before consequential unresolved decisions. Never consume a deadline while the
  interface is still asking the player what to do.
- Persist the world date, pending decisions and random state together. Reopening a save must not regenerate offers,
  duplicate an entry, reroll an injury or pay the same reward twice.
- Use stable event, golfer, offer and decision identifiers so links and decisions survive navigation and saving.
  Dismissed or completed decisions remain distinguishable from pending ones.

### Phase B: Prove one planning period

The first internal build should include a minimal New Career flow that assigns one genuine newcomer and shows a legal
starting path. That golfer can enter an event, schedule training/rest and advance through a planning period. Keep setup
plain; full customization follows in Phase C. Use a fixture for repeatability, then repeat in a normal world. This must
be playable, not only backend infrastructure.

Recommended controls are Advance to next decision and Advance through planned period. The engine currently uses thirteen
four-week blocks, not twelve calendar months. Label this honestly in the first build; decide separately whether to add
real calendar months. Weekly detail and automatic stops must protect deadlines within each planning period.

### Required foundation tests

- The same committed action applied twice produces only one entry, charge, acceptance or reward.
- Closing the game during an interruption and reloading restores the same valid choice at the same date.
- The same actions and saved RNG state replay deterministically, and all-AI operation remains equivalent to the baseline.
  Different human choices may change later random draws and outcomes; do not promise identical future worlds after
  decisions diverge.
- Switching views or reading history has no effect on simulation outcomes. A missing UI choice cannot strand the world
  permanently.

**Exit test.** One planning period can be played, interrupted, saved and resumed with no duplicate consequences, skipped
mandatory decisions or AI overwrite of the human plan.

## 4. Create a golfer who belongs in the world

### Phase C: Build New Career and setup

Use the normal newcomer-generation system, not an arbitrary member of the seeded initial population. Define a creation
boundary that reserves a genuinely new entrant from the ordinary cohort without adding a bonus player. Annual juniors and
new professionals already have separate generation paths and a shared ID registry; the initial New Career bootstrap
needs explicit design.

- Show age, ordinary attributes, visible prestige or reputation where applicable, amateur/professional status and an
  explanation of available starting paths.
- Allow a name and origin choice before finalizing the eligible-tour list. Revalidate nationality, residency or other
  access consequences after a change rather than preserving an invalid route.
- Build a service that lists genuinely available tours or pathways and explains exclusions. Existing stochastic
  college/series assignment is not already an API for every legal starting choice.
- Confirm the chosen golfer and starting path once. Starting or reloading must not duplicate that person or create
  another cohort.
- Provide an understandable initial budget, commitments, staff situation and calendar. Starting finances must match the
  selected pathway, not automatically resemble a premier-tour professional.

### Recommended defaults to decide with Ryan

Keep generated ability, potential and personality fixed during customization. Origin should change identity and
applicable access rules, not secretly reroll talent. If origin affects the cohort's national allocation, use a
documented reassignment policy rather than adding a new golfer or pretending no allocation changed.

For V1, recommend one candidate at a time, with annual switching as the main retry. Decide whether the pool includes only
18-year-old amateurs or also ordinary late-entry professionals. Setup rerolls and entry into an existing world remain
open. Separate nationality, hometown and residence where their rule effects differ.

### Setup acceptance tests

- Hidden potential stays absent from every user-visible surface, including comparisons, notifications and exported career
  summaries. Public performance is allowed to provide imperfect clues.
- Customization cannot grant an ineligible tour, bypass amateur status, create extra newcomers or reuse an existing
  identity incorrectly.
- No available tour produces a helpful pathway explanation rather than an empty screen or a forced elite placement.
- The same confirmed save opens the same golfer with the same identity and commitments.

**Exit test.** Ryan can create a believable ordinary entrant, understand their opportunities and begin a season without
special treatment or hidden-data leakage.

## 5. Make the season worth playing

### Phase D: Build the planning calendar

The calendar should answer three questions quickly: what can I enter, what should I prepare for, and what will this cost
me? Show confirmed entries separately from tentative plans. A plan is an intention, not proof of qualification or
payment.

- For each event, show date, location, status, entry deadline, qualification route and known costs or estimated cost
  ranges. Make uncertainty explicit.
- Expose the consequences of training and rest without promising exact attribute gains. Show fatigue, current injury
  limitations and the relevant coaching input.
- Validate overlapping events, travel feasibility, commitments and recovery restrictions at planning time and again when
  the action becomes effective.
- Allow a player to revise uncommitted plans and explain any consequence of withdrawing from committed ones.
- After an event, show the result, earnings or costs, ranking and eligibility changes, and links to the golfer, tournament
  and rounds that the summary references.

### Phase E: Add decision interruptions and notifications

The Notifications sidebar should separate required decisions, approaching deadlines and information. The existing My
World view is a retrospective digest, not an actionable inbox. Add explicit pending, accepted, declined and expired
states, with funds and staff capacity revalidated at acceptance.

- Pause for an offer that would expire before the next planned stop, loss of eligibility for a planned event, an
  important new invitation, or a health/financial change that invalidates the plan.
- Show why the prompt appeared, available actions, expiry and the consequence of ignoring it. Revalidate the choice if
  circumstances changed while it was open.
- Use stable links to supporting facts. A stale invitation should explain that it expired instead of failing silently or
  being accepted twice.
- Group ordinary results and world news into a readable digest. Let the player inspect more detail without being forced
  to acknowledge everything.

### Tests for a believable season

Run a planning period containing qualification gained, qualification lost, an injury, an overlapping event and an
expiring invitation. Verify that each genuinely necessary decision arrives before its deadline and that routine news
does not stop time repeatedly. Repeat after save/reload and after changing a tentative plan.

**Exit test.** The player can make and revise a coherent season plan, and the game interrupts only when a meaningful
decision or invalidated commitment requires attention.

## 6. Connect money, staff and opportunity

### Phase F: Make affordability understandable

Career mode exposes financial frustration more sharply than observer mode. A player should see the budget, committed
costs, expected timing of income and available support. Do not confuse projected winnings with spendable funds.

- Reuse the simulation's fee, travel, income and sponsorship rules. Make every charge and receipt traceable to an event
  or agreement.
- Support strong amateurs through the appropriate existing or approved funding routes. A player qualifying for a major
  should receive a credible way to attend under Ryan's design goal, rather than an unexplained affordability lockout.
- Do not solve that access problem with silent unlimited money. Design the support mechanism explicitly, disclose its
  terms and test it for AI golfers as well as the player.
- If a plan becomes unaffordable, explain the shortfall and available choices before commitment. Never discard an entry
  or silently choose a different tournament.

### Phase G: Give coaches and caddies useful roles

Staff should affect decisions and form relationships within the existing world. Show a staff member's relevant
strengths, public prestige, cost, availability and reasons for interest. Good scouting can produce an imperfect
assessment of development evidence, but it should not expose the exact hidden potential value.

- Support inbound approaches through Notifications and a simple comparison and accept/decline flow. Availability,
  affordability and suitability must still apply.
- Make the impact legible through advice and factual progress reporting. Avoid attributing an entire win or injury
  recovery to a staff member without evidence.
- Use the same contract and separation rules for human and AI golfers. Replacing a caddie or coach must not leave
  duplicate active contracts or charge twice.

### Phase H: Explain sponsorship and support

Current sponsor income is automatic and prestige-based. V1 should first explain that income, support and eligibility in
the finance view; do not invent a brand-negotiation system merely to populate the inbox. Interactive sponsor offers can
wait unless required by an approved funding design. Staff offers already provide genuine decisions. Prestige must not
guarantee a lucrative sponsor for every talented entrant.

**Exit test.** An ordinary player can understand their finances, accept a valid support or staff offer, and see its
actual consequences. A qualified major entrant has the approved attendance pathway, and AI golfers receive equivalent
access rules.

## 7. Carry the story across generations

### Phase I: Finish the season and hand control back

At season end, show results, finances, development, injuries, ranking or tour access changes and important relationships.
Compare outcomes with the player's chosen goals, not only with world number one.

- Offer Continue with this golfer and Start next season with a new entrant. Explain that switching does not retire,
  delete or reset the former golfer.
- Before switching, resolve or explicitly transfer any pending obligations. Contracts, health, money and career history
  remain attached to the golfer.
- Return the former golfer to the normal AI decision system. The new golfer gets a separate career chapter and their own
  starting circumstances, without inheriting money or prestige.
- Keep an ordered list of all player-controlled golfers, seasons controlled and major personal milestones. One person can
  have many roles over time without becoming several duplicate records.

### Former players and the shortlist

Add a Formerly played category that is easy to filter and sort. Show where those golfers are now and let the player
follow notable events without flooding the main decision inbox. Ordinary retirement, decline, death and staff transitions
remain governed by the world.

Ryan's example of hiring a former golfer as a coach is a strong acceptance story. Test the underlying identity and role
transition with a fixture, then let live worlds determine whether it actually happens. Do not force that person to
become a coach just because the player once controlled them.

### The story record

Store facts and stable references, not a duplicate copy of every tournament. A career summary should link to its source
round, event, relationship or season. Narrative text must distinguish recorded evidence from uncertain interpretation. A
summary cannot invent lucky bounces, detailed putting or fairway statistics the simulation never recorded.

### Handoff tests

- After five annual switches, all six golfers exist once, only one is human-controlled, and the first five continue under
  AI rules.
- A later coach role retains the same historical person and can be hired only if normal availability and contract rules
  permit it.
- Save/reload preserves the active golfer, former-player category and links even after retirement or death.

**Exit test.** The player can change protagonists while the same golf world keeps its history, obligations and
relationships intact.

## 8. Build the interface and protect performance

### Wide screen first

Use the available width for decisions rather than stretching text. The recommended career home shows current golfer and
date, upcoming commitments, budget/health and the next meaningful action together. Keep global world browsing available
so career mode does not isolate the player from the wider game.

- Calendar: a broad planning view with an event-details panel and clear confirmed versus tentative states.
- Notifications: decision queue beside supporting information, with visible expiry and action status.
- Golfer and staff pages: sortable visible prestige, useful attributes and history links. Retain hidden-potential
  boundaries.
- Season review: concise outcomes with optional deeper detail, followed by the continue-or-switch decision.

Do not prioritize mobile rearrangement now. Still prevent clipped controls, unreachable actions and broken dialogs on
Ryan's actual browser and display configuration. A very wide monitor does not guarantee an equally wide browser content
area.

### Performance work that supports the loop

Measure simulation time separately from page-opening time. Read-only browsing must not repeatedly decompress or rescan a
century of history. Prefer indexed data and caches that can be rebuilt safely, while preserving the full historical
record.

- Benchmark an early world and the supplied long world, with cold and warm caches. Record hardware, world size, date range
  and exact commit.
- Measure one planning period, one season, a career decision interruption, tournament opening, career history, saving
  and loading. Keep comparable inputs between builds.
- Prevent background history work from blocking an urgent decision. Show a clear loading state and allow safe navigation
  or cancellation where appropriate.
- Keep notifications and summaries bounded and deduplicated. Do not copy the full world into each career chapter or
  regenerate every summary at each screen visit.
- Test memory growth and long-lived identifiers after many seasons and switches. Retaining rich history is a requirement,
  not a performance bug to solve by deleting it.

### Budget and acceptance

Use Ryan's computer for the agreed 120-second simulation benchmark. Establish separate page-response and save/load
budgets from measured baseline behavior before setting numbers. Claude's slower environment can reveal relative
regressions, but cannot decide whether Ryan's target has been met.

**Exit test.** The full career loop remains responsive on Ryan's machine in both a fresh world and a mature world, with no
unexplained history loss or accumulating duplicate work.

## 9. Test and release the first career version

### Test ladder

1. **Rule tests.** Validate actions, dates, eligibility, costs, offers, identity, control ownership and hidden-data
   boundaries. Exercise invalid actions and repeated submissions, not only valid plans.
2. **Interrupted-flow tests.** Close and reopen at setup, an offer, an entry deadline, an injury prompt, a result screen
   and season handoff. Try Back, Cancel, repeated clicks and stale notifications. Verify no date advance or duplicate
   consequence slips through.
3. **Full-season scenarios.** Play an ordinary amateur, a club professional pursuing one major, a lower-tour professional
   and a rare precocious entrant. Include financial pressure, injury, qualification changes and staff offers without
   scripting the outcomes.
4. **Multi-season tests.** Continue one golfer for several seasons; switch annually through five new golfers; then
   simulate ahead and inspect former-player careers, role changes, records and links.
5. **World-scale comparison.** Compare human-enabled worlds with baseline worlds using paired seeds where valid.
   Investigate population, pathway, finance and ranking differences instead of assuming the interface cannot affect them.
6. **Ryan's acceptance run.** Use the full intended world, not a permanently reduced population. Capture decisions that
   felt unclear or uninteresting as well as bugs and timings.

### Release gates

- No known blocker that corrupts a save, loses a player-controlled identity, skips a required decision or applies a
  financial/contract action twice.
- No exact hidden potential exposed through UI, narrative or scouting advice. No unexplained human-only eligibility or
  outcome advantage.
- The complete season and annual switch work after save/reload. Former golfers continue normally.
- The current headroom/balance decision is documented separately, with evidence and remaining uncertainty. Realism is
  not inferred from one exceptional career.
- Performance budgets are checked on the intended machine and world size. Focused tests are not described as a
  full-suite pass.
- A release note records the exact commit, test evidence, known limits and any save-version restrictions. Main
  publication requires a separate go-ahead.

### What happens after the first release

Refine the decisions Ryan actually enjoys and the points where he feels powerless or confused. Then consider deeper staff
relationships, richer sponsorships, career-specific world summaries and Birth of Pro Golf compatibility. Add breadth
after the core loop has proved that an ordinary season is worth playing.

**Exit test.** Ryan can finish a meaningful season and confidently begin another, with no requirement to become an elite
player for the experience to feel successful.

## 10. Decisions and the next build request

### Decisions worth resolving before implementation

- **Starting candidate:** recommended one newly generated entrant, with no bonus talent. Confirm the allowed ages and
  whether amateur/professional status is chosen or determined by the entrant.
- **Origin customization:** recommended before eligibility is finalized, with fixed talent and a documented effect on
  national cohort allocation. Decide whether nationality and home base are separate.
- **Rerolls:** confirm whether setup rerolls are allowed, or whether trying a different golfer is mainly the season-end
  mechanism. Recommended no punitive ironman requirement for V1.
- **World entry:** recommended fresh-world New Career first, while designing identities to permit later entry into an
  existing world. This is a scope suggestion, not a decision already made.
- **Advancement:** recommended four-week planning with weekly detail and automatic stops before consequential decisions.
  Decide how much voluntary event-level detail Ryan wants to see.
- **Financial support:** approve the rule that makes major attendance realistically possible and clarify its limits.
  Apply it consistently to AI and player golfers.
- **Retirement or death while controlled:** recommended preserve the person's history and offer a clear transition at
  the next valid newcomer boundary. Decide what the player does until that boundary.

### Recommended first implementation assignment

Once Ryan approves beginning career development, ask Claude for the control foundation and one planning-period vertical
slice only. Include minimal New Career assignment of a genuine newcomer, a stable career identity, shared human/AI
validation, interrupted advancement, a plain planning interface and save/reload tests. Full customization, negotiations
and Birth of Pro Golf stay outside that first assignment.

Review that slice before authorizing full New Career customization and the full-season loop. This order reduces the
chance of building attractive screens on top of a simulation that cannot safely stop and ask the player what to do.

### Evidence and status notes

- **User design source:** Ryan's career-mode discussions in this conversation, including annual protagonist switching, AI
  continuation, customization, former-player shortlist, organic relationships and realism. All proposed defaults in this
  document remain open for discussion.
- **Release baseline:** main commit 18a8e23fb06c241892a73af29124c168c2018467. The release test result is evidence for
  that simulation build, not career-mode coverage.
- **Starting-ability study:** build/v17-readiness-study commit 5c7dce938f4510c180555d987a59ef26c0b9deb5,
  docs/review/readiness/study/STUDY.md and results/RESULTS.md. The newer headroom experiment is in progress and has no
  approved production result.
- **Source-only feasibility review on main 18a8e23:**
  - golfsim/session.py (weekly advancement/checkpoints);
  - golfsim/season.py (planning, fields, funding);
  - golfsim/staff.py (approaches and identities);
  - golfsim/careers.py and population.py (new entrants);
  - tools/observer.py and observer_myworld.py (observer controls and digest).

  No new tests were run for this roadmap. Proposed career interfaces are not claims of existing implementation.
