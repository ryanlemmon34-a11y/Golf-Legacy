# Build v16: what is in it, what was tested, and what needs your decision

**Asked for**: the prompt worked out with HAL (roadmap and review as the foundation; wide-screen desktop; access
and correctness first; development evidence; ratings histories, injuries and staff profiles; calibration only
after evidence and approved runs). **Build**: branch `build/v16` from `main` at `33e1fa2`; one commit per
package (below). **Not merged into `main`**: that needs your approval for this pass.

What was not touched: the Test 1 10.30 download (only copies were read), the 50-season world (not opened),
your paused playthrough (not resumed), every past result (nothing in an archive is rewritten). No long
simulation was run: the simulation runs below are proposals waiting for your approval. Nothing was bought or
sent anywhere.

## Packages, in the order built

| # | Package | Commits | Changes simulation behaviour? |
|---|---|---|---|
| 0 | Order and decisions; sponsorship proposal | `0cbfebf` | no (a document) |
| 1 | Wide desktop layout, menu, Record Book, retirement and comparison fixes | `26df0bf` | no (observer only) |
| 2 | USA Open champions through the tenth anniversary | `2ab1176` | **yes**, from the first USA Open field set with this code |
| 3 | Why golfers enter or miss a major: the money facts | `289a0c9` | no: records only, outcomes shown identical |
| 4 | An earned major place is never lost for money alone | `45151e1` | **yes**: golfers who would have declined now play |
| 5 | Development evidence (creation, sources, aging) | `d7dacfc`, `92b3925` | no: records only, outcomes shown identical |
| 6 | Ratings over time, injuries and recovery, coach and caddie profiles | `e2e60f4`, `7d63213`, `eba01e1`, `70ed2d5` | no: records and observer, outcomes shown identical |
| - | Two tests made independent of who won what | `fd72973` | no |
| 7 | Validation, this report, backlog | `caf1247`, `e7c7ad6` and this commit | no |

Packages 2 and 4 change the engine's fingerprint and its rules version (`2026-11-01`, on the Rules page). A world
saved by an earlier engine (Test 1 10.30, the 50-season world) is therefore never resumed in place by this
build: it can be browsed, or *copied with an explicit engine-change acceptance* (recorded in the copy's
`ENGINE_ACCEPTED.json`), and only that copy continues. Results already played keep the rules they were played
under.

## 1. Observer: wide screen, menu, Record Book, retirement and comparisons (`26df0bf`)

**Changed**
- **Wide screen**: the 1,150 px cap is gone. Tables size to their columns (at least 760 px or the width
  available) instead of stretching across a 3,440 px screen; the big data tables (directories, statistics,
  comparisons, GOAT Lab, cohorts) and the new ratings chart scroll sideways inside their box rather than
  squeezing columns; paragraphs keep a reading width (110 characters) and table text cells 80 characters.
- **Menu**: *Compare careers* and *GOAT Lab* added. *My World* was checked first: it was already in the menu and
  is unchanged.
- **Record Book**: "Records & frivolities" is the Record Book in the menu, its page title and saved-view names.
  The `/records` address, every list on it and every saved view still work.
- **Retired golfers** are shown as retired, with the status they last held ("retired, last a professional"), on
  the profile and in the Career Grand Slam and one-major lists (new *Now* column). One rule decides it everywhere.
- **My World** announces a retirement once, dated the season after the last one played (it was repeated every
  season), with or without a live world.
- **Compare careers**: the current season's top 10s and wins leave qualifying stages out, as archived seasons do.
- **Where are they now**: *Highest level* now counts the current season's tour.

**Tested**: in Chromium (Playwright) at **3,440 x 1,440 and 2,560 x 1,440** on 18 pages (Stats with and without
golf statistics, a profile and its season tab, an event and its round replay, Record Book, rankings, a season
recap, GOAT Lab, a comparison, qualification, rules, standings, Grand Slam, a cohort, the calendar, the golfer
directory): no page wider than the window; the longest line in any table cell 741 px; the widest table
2,178 px (a major's qualification ledger). Re-measured on the final build with the new profile sections: see
*Validation*. Unit tests:
`test_myworld` (one retirement event; menu; Record Book), `test_compare` (top 10s without qualifying),
`test_cohort` (current season's level). All five new tests fail on the previous code.

**Not verified**: small screens and phones (deferred, as asked: nothing was changed for them); browsers other
than Chromium; the measurement used a small test world (5 % population), whose names and numbers are no longer
than a full world's but whose tables are shorter.

## 2. USA Open champions through the tenth anniversary (`2ab1176`)

**Changed**: route U1 ("USA Open champions, last 10 years") counted only nine editions, so a champion of year Y
lost the place in Y+10 and had to qualify (HAL's audit of Test 1: six tenth-year champions entered qualifying,
two missed the major). A champion now holds Y+1 through Y+10 and the place expires in Y+11 unless they win again.
The evidence shown for a place names the win behind it. Both calendars.

**Tested**: `test_exemption_window` (Y+1 and Y+10 held, Y+11 expired, a new win renews it, the evidence, other
routes' windows unchanged; two of the four fail on the previous code), and the calendar and qualification
modules.

**Simulation**: changes, from the first USA Open field set with this code. Past fields are not rewritten.

**Decision flagged (not changed)**: routes that *include* the current year ("other majors' champions, last 5
years") cover six editions once this year's edition has been played: this year's and the five before. HAL asked
for that window to be kept; it is, and a test pins it. See *Decisions*.

## 3. Why golfers enter or miss a major (`289a0c9`)

**Changed**: every golfer already had a weekly reason recorded (played, rested, trained, worked, fields full,
could not afford it, injured, not eligible, no suitable event). Major places now also keep the money they were
decided on, in the rights ledger archived with the season: what the golfer could draw on (savings, backers,
credit), what was set aside first (four weeks of living and coaching costs, and entries already accepted that
week), what remained, the trip's cost (cheapest site: travel, entry and the caddie's week) and who paid. The
qualification ledger shows it as *Money when the field was set*; older places say "not recorded".

**Tested**: `test_major_funding.MoneyFacts` (every decided place has its facts and they add up; a decline shows
its reason in numbers; the ledger page; older places). **Outcomes identical**: ten weeks of a reference-calendar
world through its first two majors (94 events) on the previous commit and on this one give identical digests in
every outcome part (`tools/equivalence_check.py`).

## 4. An earned major place is never lost for money alone (`45151e1`)

**Changed**: when a golfer holding an earned major place, or a called-up alternate, cannot pay the trip, the
organizer pays its travel and entry **in kind**. The cost never passes through the golfer's books, so it cannot
be reimbursed twice; each trip is recorded once in its own ledger (week, event, golfer, amount, what it covers,
who paid: "organizer: an earned major place"), archived with the season. The place's money facts say "paid by
the organizer". The caddie's week stays the golfer's own cost. Every status and country is covered. Injury,
retirement and an expired amateur place still end a place. Qualifying stages, invitations and every other event
are paid exactly as before, so ordinary events and qualifying still matter financially. The rules page states
it (rules `2026-11-01`).

**Tested**: `test_major_funding.Guarantee`, **reconstructed scenarios, not replays**. The archive keeps the 269
major places Test 1 lost for money (221 amateurs, 42 professionals, 6 club professionals), but not each golfer's
balance at the time. So the money positions behind them (no savings, deep debt, no backers) are given to golfers
holding Masters places in a test world: professionals, amateurs and club professionals all play, each trip paid
in kind once; an injured broke golfer still withdraws; a golfer who can pay, pays; cash moves only by what the
golfer's books show; regular and qualifying events stay unaffordable to the broke golfer; the same week from the
same save gives identical grants and results; grants survive a save. On the previous code the scenarios fail
(see *Validation*).

**Simulation**: changes. Golfers who would have declined now play, which changes fields, results, rankings and
everything after them.

**Not verified**: how many grants a full world makes each season and what they cost, and the effect on
amateurs' careers: that needs the runs proposed below.

## 5. Development evidence (`d7dacfc`, `92b3925`)

**Changed** (diagnostics only, kept in each season file's `diagnostics` section; the observer never reads it, so
potential and ceilings stay hidden in the game):
- **How each golfer starts in the records**: the world's own golfers at its first season ("initial": their
  careers began before the world did), each new 18-year-old ("junior") and each new professional from outside
  the amateur game ("late entrant"): exact age, the 21 attributes, Overall, potential, ceilings, peak age and
  aging rate.
- **Each season, for every golfer**: the points moved by maturing, training, tournaments, injury (lasting
  losses) and the winter's aging, by category and in Overall; training weeks by category; coached weeks and the
  coach's quality; Overall before and after aging (dated: the season's end, then after the winter), and the
  ceilings' Overall after aging. Nothing is capped: these are records of what the existing rules did.
- No random draws are added: the totals are noted where the rules already change an attribute.

**Tested**: `test_development_evidence` (creation records by path; every golfer-season's change reconciles with
its parts within 0.015 Overall, over 1,000 checked; the sources behave as the rules say; the observer never
reads the section). **Outcomes identical**: 16 weeks across a season end (154 events, aging, retirements, new
juniors) on the previous commit and on this one: identical digests in all 14 outcome parts; only the new
section differs.

**Cost (measured)**: a quarter-population world (1,656 golfers), one season, the code before and after
alternated twice on 4 CPUs: **84.8 / 83.7 s before, 85.2 / 84.4 s after** (under 1 %, within noise). Season file:
about 42 bytes per golfer-season for the yearly summaries and about 100 bytes per golfer for the one-time
creation record. For Test 1's 2083 season (13,212 golfers, 13.5 MB) that is **about 0.6 MB a season (+4.6 %)**.

**On Harper's 89.0**: Test 1 was saved by an engine that recorded none of this. Harper's first retained rating,
89.0, is from the start of the age-19 season, after a first year and winter; the age-18 creation rating is
unknown and is not inferred. New worlds record creation exactly, so the runs below can show how a golfer of that
kind starts. No cap was added.

## 6. Ratings over time, injuries, coaches and caddies (`e2e60f4`, `7d63213`, `eba01e1`, `70ed2d5`)

**Changed**
- **Ratings over time** (profile, under Ratings): Overall or any attribute, as levels or as changes from the
  season before; one fixed-width bar per season, and the chart scrolls sideways on long careers rather than
  thinning the bars. Each bar is dated by what it is: the start of a season, "now" for the current season, and
  for a retired golfer the final playing ratings at the end of the season they retired after (no aging added,
  never a season they did not start). A season with no record is a gap, never filled in.
- **Injuries** (profile): "injured now" with when entries reopen; one row per episode (when, what, weeks
  announced, entries actually missed, when the golfer could enter again, their first start back, lasting
  effects, where it happened). Seasons archived before episodes were recorded show their announced injury weeks
  only ("episodes not recorded"). A skipped event is never attributed to an injury.
- **Coaches and caddies**: a coach's speciality, whether they specialise in young players and how many clients
  they take on; a caddie's six working skills, archived from now on ("not recorded" before). Every partnership
  shows who began it and why, the arrangement (a fee a year, a share of winnings, a tour bag), the time actually
  worked together, who ended it and why, and the starts, wins and majors together. These come from the stint
  records that already existed; nothing is reconstructed. A coach's teaching and scouting stay hidden, as the
  game is designed (decision below). No "fit" is shown: there is no recorded measure of it, and inventing
  thresholds would present a guess as a fact.

**Tested**: `test_living_views`, 10 tests, 11 with the fix below (an active golfer's bars and current ratings; a
retired golfer ends at their retirement season; a missing season is a gap; levels and signed changes; each injury
episode adds up to the season's injury weeks and no start falls while the golfer is out; the profile; older
seasons; injured now; the coach card with hidden facts absent from the archive; partnership rows from the recorded
stints; the golfer's team page names the same coach; caddie skills; older worlds say "not recorded"). **Outcomes
identical**: the final build against `d7dacfc`, 16 weeks across a season end: identical in every outcome part and
in the published history once the two new records (injury episodes, caddie skills) are left out; only the
development section differs (its precision changed in `92b3925`).

**Found and reported, not changed**: an injury announced as *n* weeks keeps a golfer out of *n + 1* weeks of
entries (an injury after week W with *n* weeks returns them for week W+n+2). The profile shows both numbers
separately. See *Decisions*.

**Found in validation and fixed** (`70ed2d5`): a history exported without its index (the Test 1 download is
one) and browsed read-only answers every career from the season files. The new sections read a golfer's career
several times per profile, each read decoding all 57 seasons. A career is now read once per golfer and kept with
that reading of the history (the same rows; worlds with an index are unaffected). Test: two profile views of an
exported copy read the career once (twelve times before).

**Not built in this pass**: My World does not yet announce injuries and returns (one item per episode is the
plan); "fit" between golfer and staff (needs a definition from you first).

## Validation

- **Whole suite** (on `eba01e1`): **51 modules, 539 tests, all passed**, 1 skipped by design
  (`test_observer_profiles`, as before); six modules at a time, 19 minutes, 4 CPUs. After the fix found on the
  Test 1 copy (`70ed2d5`, one observer function), the modules that read careers were run again on it:
  `test_living_views` (11, with its new test), `test_compare`, `test_goat_peaks`, `test_history_index`,
  `test_history_consistency`, `test_observer_history`, `test_observer_app`, `test_peak_overall`, `test_cohort`
  and `test_myworld` (100 tests): all passed.
- **The new tests fail on the code before each change** (a separate checkout with the new test files):
  package 1, 5 of 5 (on `0cbfebf`); package 2, 2 of 4 (the other two pin windows that were already right);
  package 3, 3 of 3 (on `2ab1176`); package 4, the 4 guarantee scenarios (on `289a0c9`: a broke golfer's place
  ends "declined: could not pay the trip" and there is no grant ledger); package 6, 10 of 10 (on `d7dacfc`).
  Package 5's tests read a section that did not exist before; they were not run on the old code.
- **Outcomes unchanged where they should be** (`tools/equivalence_check.py`, the same saved test world advanced
  on two checkouts): package 3 (`2ab1176` -> `289a0c9`, 10 weeks, 94 events) and package 5 (`45151e1` ->
  `d7dacfc`, 16 weeks across a season end, 154 events, 13 playoffs): identical in every outcome part. The final
  build against `d7dacfc` over the same 16 weeks: identical in all 14 outcome parts and in the published history
  once the two new records (injury episodes, caddie skills) are left out; only the development section differs
  (its precision changed in `92b3925`).
- **Wide desktop, final build**: Chromium (Playwright) at **3,440 x 1,440 and 2,560 x 1,440**, a fresh 5 %
  test world made by this build (2030, week 21), 24 pages: the 18 measured in package 1 plus a profile's ratings
  chart (levels and changes), injuries, a coach, a caddie and a team page. No page is wider than the window;
  paragraphs are at most 1,110 px wide; the longest line in any table cell is 738 px. At 3,440 the widest table
  is a major's qualification ledger on its event page (7 columns with the new money column, 2,828 px; every cell
  wraps at its reading width, checked on a screenshot); at 2,560 wide tables fit the content width (2,296 px)
  and wrap. Ratings bars are 38 px at both widths. *Correction*: package 1's commit message said data tables
  reach 1,880 px; its own measurement had the same ledger (6 columns then) at 2,178 px.
- **A copy of Test 1 10.30**, browsed read-only (archive only: it was saved by another engine, and the download
  carries no index): Harper's profile shows **37 bars ending "final ratings: retired after the 2082 season"**
  (no season after it); his injuries say "episodes not recorded" with each season's announced weeks; caddie
  skills say "not recorded (recorded from rules 2026-11-01)" (none of its 8,844 caddies has them); coach cards
  show speciality, youth focus and capacity, with teaching and scouting not shown; nothing is reconstructed.
  **Speed without an index is poor**: Harper's profile took 651 s on `eba01e1` and 243 s after `70ed2d5` (166 s
  for a second view); the rest is reading results and other facts from 57 season files, which was already so
  before this pass, and a coach's partnership page (starts, wins and majors together, columns that already
  existed) had not finished after 34 minutes. These times include the statistics store being built alongside,
  as it is on first opening. With an index (any world you play, or a copy opened once as a session) these are
  single queries. See *Not verified*.
- **Originals**: the Test 1 10.30 download is unchanged (SHA-256 `df90dd2f...e515`, as when it was fetched);
  its extracted copy unchanged (names, sizes and modification times); checks used a further copy. The 50-season
  world was not opened in this pass.

## Decisions needed from you

1. **Amateur sponsorship settings**: approve, change or reject `docs/AMATEUR_SPONSORSHIP_PROPOSAL.md` (three
   bands: up to $25,000 / $12,000 / $5,000 a season, earned only by observable results, rankings and results-based
   scouting; in kind; budget opens in week 1, raised in-season by new achievements, never cut mid-season; drops at
   most one band a winter; about 150 contracts and $0.4-0.7 m drawn a season expected, to be measured). Not built
   until you decide. It does not address zero-start seasons among unranked full-time amateurs (8.5 %), which need
   their own decision.
2. **The classic calendar (v1)**: proposed: new worlds use v2 only; worlds saved on v1 stay browse-only (history
   and their last snapshot open; they cannot be advanced); only what is needed to read them is kept; nothing is
   deleted or migrated. This blocks advancing the earlier paused v1 playthrough: is that acceptable? Removing the
   v1 code paths, the v1/v2 comparison tools and the v1 equivalence tests follows once you agree.
3. **The simulation runs below**: seeds, durations and questions, for approval before anything runs.
4. **A coach's teaching and scouting**: keep them hidden (the current design: you judge a coach by results), or
   show them?
5. **"Last N years" routes that include the current year**: keep the six-edition window once this year's edition
   is played (as now, per HAL), or count exactly N editions?
6. **Injury length**: keep "n weeks announced, n + 1 weeks of entries missed" (as now, both shown), or make the
   missed entries match the announcement? The second changes simulation behaviour.
7. **Browsing exported histories**: build an index beside a read-only copy when it has none (minutes once, then
   pages are quick; the original is never written), or include the index in exports by default? Either makes
   Test 1-sized downloads browsable; neither changes the simulation.

## Proposed simulation runs (nothing runs until you approve)

Every run is full population, on the reference calendar (v2), from a fresh world; none of them replays Test 1.
Times are estimates from the last measurements on this machine (4 CPUs, `docs/PERFORMANCE_REVIEW.md`): about
112 s for a fresh world's first season, rising to about 203 s by season 51; this build adds under 1 % (package 5).
The ranges allow for this build's newer features costing more than measured there.

| Run | Seeds | Length | Estimated time | Questions it answers |
|---|---|---|---|---|
| A. Major-trip guarantee, paired | 360013 and 2027, each played twice from the same start: once on `289a0c9` (the USA Open fix and the money facts, before the guarantee) and once on this build | 5 seasons each (20 seasons) | 40-75 min | How many earned places would have been lost for money, by status and region, and how many the guarantee saved; what the grants cost a season; whether amateurs who now play majors turn professional or stay amateur differently; whether ordinary and qualifying events lose entrants (they should not) |
| B. Development, full careers | 360013 | 30 seasons | 1 h 10 min - 1 h 55 min | Where development comes from (maturing, training, tournaments, injury, aging) by age and level; how far golfers get toward their ceilings and when they peak; how new juniors start compared with the world's first golfers; whether the top of the ratings (Harper-like 89s) is reached by plausible paths |
| C. Development, other seeds | 2027 and 3031 | 10 seasons each | 40-75 min | Whether run B's patterns hold across seeds, or are one world's accident |

Total about 2 h 30 min to 4 h 15 min of machine time, one run after another. Each run keeps its world and
archive in the scratchpad. The first season of each is timed; a run more than 50 % slower than its estimate is
stopped and reported. The results come back as a report with the evidence before any calibration is proposed.
Optional, only with your explicit engine-change acceptance: a *copy* of Test 1 10.30 continued for 3 seasons on
this build, to see the guarantee and the USA Open window in a mature world (about 13,000 active golfers;
estimated 3.5-5 min a season, not measured on this build).

## Not verified

- **The two simulation changes at full scale**: how many major trips the guarantee pays for each season, what
  they cost and what they change in careers; the USA Open window over many seasons. Shown on small test
  worlds and reconstructed scenarios only, until the runs above.
- **Development evidence over whole careers**: checked over two to three seasons of small worlds (every
  golfer-season reconciles); full careers need run B.
- **Outcome identity** was shown over 10-16 weeks of small worlds (one season end), not over long runs.
- **Wide screens**: Chromium only, on a small test world. Long-history pages of Test 1 were checked for content,
  not measured in the browser: without an index they take minutes to render (below).
- **Browsing a long exported history without its index** (a diagnostic package or a download like Test 1's,
  opened read-only): profiles take minutes and a coach's partnership table did not finish. This was already
  so before this pass; the fix above removes this pass's share. A remedy to decide: build an index for a
  read-only copy beside it (the original untouched), or include the index in exports (an option the export
  already has, off by default).
- **Small screens and phones**: not built or checked, as asked.

## Not done in this pass (and why)

- **Amateur sponsorship**: waiting for decision 1.
- **Calibration**: waiting for the runs above.
- **Retiring v1**: waiting for decision 2.
- **My World injury and return items; staff "fit"**: next (fit needs a definition).
- **Deferred, as asked**: small screens and phones, the death system; geography, course usage, prestige and
  deeper staff careers later. Hide results was not restored.
