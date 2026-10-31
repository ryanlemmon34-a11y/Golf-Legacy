# Roadmap traceability: the expanded pre-career-mode roadmap, requirement by requirement

Source: the owner's expanded roadmap (`Golf_Legacy_Expanded_World_Roadmap_2026-10-30`: items F1-F3, E1-E3, P1-P2,
S1-S3, G1-G3, the Record Book section, B1-B2, T1-T3, C1-C2, and the audit register N01-N23 with 88
subrequirements). Read against `build/v16` at `87c2a21` and the branches on `origin` on 31 October 2026. Where the
roadmap and the owner's prompt of 31 October differ, the prompt wins (fresh worlds only; `docs/BACKLOG.md`).

Compiled by reading code, tests and documents only: **no test or simulation was run for this matrix**. "Built"
means code on `build/v16` and a test module that exercises it, as named; it does not mean the full suite was re-run
here (last full run: 573 tests on `e615b2e`, `docs/V17_PASS_REPORT.md`). Anything without both is marked
*verification pending*. Item sub-ids (F1.a, F1.b ...) split each roadmap item into its own sentences; they are
this document's numbering, not the roadmap's.

## Status key

| Status | Meaning |
|---|---|
| Built | On `build/v16`, with code and a named test |
| Partly built | Some of it on `build/v16`; the rest named in the notes |
| Branch v16-observer | On `origin/build/v16-observer` (`b07b072`, based on `32a0a6f`), not yet integrated |
| Branch v16-recruitment | On `origin/build/v16-recruitment` (`cab6e45`, based on `a11f29a`), not yet integrated |
| In progress: v16-X (not pushed) | Assigned to branch `build/v16-X`, which is not on `origin` yet; nothing to inspect |
| Not started | No code, no branch |
| Decided Dn | Settled by owner decision Dn (`docs/DECISIONS_2026-10-31.md`); implementation in the notes |
| Deferred by owner | Outside this roadmap's scope by the owner's choice |
| Open decision | Waiting for the owner |
| Audit answered | A question the roadmap's own audit answered from retained data; any follow-up work is a separate row |

## 1. Feature items

### F1 Support successful amateurs

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| F1.a | Extend sponsorship to amateurs who show success, from observable results, ranking, earned invitations, uncertain scouting signals | Built | `golfsim/amateur_support.py`, `golfsim/season.py` (`138ce06`) | `test_amateur_support` | Initial calibration (D3). "Scouting" is results-based (top 150 by ranking points in 26 weeks), not a coach's assessment |
| F1.b | Modest versus elite support; no unlimited funding; do not force turning pro | Built | same | `test_amateur_support` (exhausted budget, turning pro ends it) | Bands A/B/C $25k/$12k/$5k. Turn-pro effect measured over 3 seasons, one seed only (81 vs 72 of the top 150) |
| F1.c | Separate cash sponsorship, equipment support, restricted trip coverage and prize-money eligibility | Partly built | `golfsim/amateur_support.py` | `test_amateur_support` (only golf costs) | Only restricted in-kind cover (events, caddie, coaching) exists. No cash sponsorship, no equipment support; amateur prize-money eligibility not addressed |
| F1.d | Eligibility, amounts, payment timing, renewal, discontinuation defined | Built | same; rules 2026-11-02 | `test_amateur_support` (upgrade, renewal one band down, ends on pro) | Week-1 budget, in-season upgrades, never cut mid-season. Amounts are interim (D3) |
| F1.e | A once-only advance reduces the remaining balance, not counted twice | Built | same | `test_amateur_support` (no trip paid twice, books reconcile) | No advance exists by design: costs are drawn as incurred against one season cap |
| F1.f | Credible response to persistent ordinary-event exclusion of adult non-college amateurs (work, reserves) | Built | `golfsim/work_pathway.py` (`3d3090e`, rules 2026-11-03) | `test_work_pathway` | D2 initial calibration (21+, outside top 300, no support or family money, 8 counted weeks) |
| F1.g | Return from work to full-time amateur golf (D5) | In progress: v16-amateur-return (not pushed) | -- | -- | Direction decided (D5); thresholds open (D5a) |
| F1.h | Report affordability and zero-start spells by region, age, status, standing | Partly built | `tools/diagnostic_report.py`, `tools/zero_start_audit.py` | `test_zero_start_regions`, `test_diagnostic_report` | Region and group tables exist; age and standing splits verification pending; figures wait for long runs B/C |
| F1.i | Keep financial pressure below the supported elite | Partly built | -- | -- | Three seasons, one seed: amateurs overall 15.0 vs 14.9 events. Verification pending (runs B/C) |
| F1.j | Test cash identities, renewals, duplicate processing, family/backer interactions | Partly built | -- | `test_amateur_support`, `test_finance_integration` | Payment order school/club, support, golfer, organizer tested; a backer-specific interaction test not found |
| F1.k | Sponsor values proposed and approved | Decided D3 | `docs/AMATEUR_SPONSORSHIP_PROPOSAL.md` | -- | Caps kept for the measurements only; final values open after runs B/C. Drawn $1.07-1.25 m a season, about twice the estimate |

### F2 Guarantee an earned major trip

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| F2.a | Every active, otherwise-eligible earned major place is funded; money never the sole rejection, every status and country | Built | `golfsim/season.py` (major field; `45151e1`) | `test_major_funding` (no place lost for money, every status every major, first Masters invitees) | Full-world grant counts and cost unmeasured until the long runs |
| F2.b | Injury, retirement, expired eligibility, voluntary refusal stay distinct; projected rights not earned | Built | same | `test_major_funding` (injury, retirement, expired places) | Voluntary refusal: no dedicated test found (verification pending) |
| F2.c | Restricted in-kind organizer support, payer and costs recorded, counts as coverage not cash | Built | same; grant ledger archived | `test_major_funding` (paid in kind once, one payer) | The caddie's week stays the golfer's cost |
| F2.d | Ordinary events and qualifying keep normal finance rules | Built | same | `test_major_funding` (ordinary events keep their costs) | |
| F2.e | All 269 recorded declines used as reconstructed scenarios, Harper's six included | Partly built | `tests/test_major_funding.py` | `test_major_funding` | Representative scenarios per status and major, not one per case; Harper's six not individually reconstructed |
| F2.f | No duplicate reimbursement, double funding or cash windfall; old results preserved | Built | same | `test_major_funding` (same week same save identical; grants survive a save) | |

### F3 Repair verified rule and observer defects

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| F3.a | USA Open U1: Y+1..Y+10, expires Y+11 unless renewed; no needless qualifying; other routes unchanged | Built | `golfsim/qualification.py` (`2ab1176`) | `test_exemption_window` | Other routes were later changed on purpose by D1 (rules 2026-11-03, `docs/QUALIFICATION_WINDOWS.md`) |
| F3.b | One current playing-status rule across profiles, lists, Grand Slam; historical status kept | Built | `tools/observer_data.py` (`playing_status`) | `test_myworld` (retired status shown one way) | Keeping old seasons' status: no dedicated test (verification pending) |
| F3.c | Retirement emitted once at the recorded transition; stable identity across live, archive, reload, My World | Built | `tools/observer_myworld.py` | `test_myworld` (a retirement is one dated event, live and history-only) | Reload not separately tested |
| F3.d | Comparison top 10s exclude qualifying, current and archived | Built | `tools/observer_compare.py` | `test_compare` | |
| F3.e | Cohort Highest level includes live appearances | Built | `tools/observer_cohort.py` | `test_cohort` | |
| F3.f | Legacy Hide Results recovery only as compatibility; feature stays removed | Built | `tools/observer_myworld.py`, `tools/observer_cohort.py` | `test_myworld`, `test_cohort` (old hiding settings) | |

### E1 Evidence to explain careers

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| E1.a | Record cash, reserves, support, trip costs, final entry reasons | Built | `golfsim/season.py`, rights ledger (`289a0c9`) | `test_major_funding` (money facts), `test_access_ledger` | Money breakdown kept for major places; other weeks keep the reason only |
| E1.b | Injury episodes and lifecycle transition dates | Built | `golfsim/season.py`, `golfsim/careers.py` | `test_living_views`, `test_injury_timing` | Career decisions archived since rules 2026-10-30 |
| E1.c | Immutable creation time, path, attributes; diagnostic potential, ceilings, peak age, aging rate | Built | `golfsim/archive.py` diagnostics (`d7dacfc`) | `test_development_evidence` | Hidden; never read by the observer |
| E1.d | Dated pre/post-aging snapshots; training, tournaments, maturation, decline, injury reconcile | Built | same (`92b3925`) | `test_development_evidence` | Reconciles within 0.015 Overall |
| E1.e | Actual staff exposure and coach-quality summaries | Built | same | `test_development_evidence` | Coached weeks and coaching-quality sum |
| E1.f | Target-event components, fatigue/recovery context, retirement and turn-pro inputs | Partly built | `golfsim/careers.py` (decision notes) | `test_finance_integration` | Decisions keep chance and some inputs; the random draw, target-event components and fatigue/recovery context are not recorded |
| E1.g | Instrumentation changes no result and consumes no randomness | Built | `tools/equivalence_check.py` | equivalence runs in `docs/V16_BUILD_REPORT.md` | Shown over 10-16 weeks of small worlds; not a unit test |
| E1.h | Missing old data "Not recorded"; hidden fields not exposed; versioned schema; storage measured | Built | `golf-legacy-development/1` | `test_development_evidence`, `test_major_funding` (older places) | About +4.6 % archive, under 1 % time |

### E2 Readable ratings on a wide screen

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| E2.a | Data pages use desktop width; text readable; horizontal scroll; wide viewports tested and recorded | Built | `tools/observer.py` (`26df0bf`) | `test_myworld` (no width cap) | Chromium at 3,440x1,440 and 2,560x1,440 (V16 report), not automated, not re-measured in the V17 pass |
| E2.b | Overall and selectable single attributes | Built | `tools/observer.py`, `tools/observer_data.py` (`e2e60f4`) | `test_living_views` | |
| E2.c | Physical, technical and mental group views | Branch v16-observer | `a9e5e98` | `test_ratings_groups` | Group value = plain mean of recorded attributes |
| E2.d | Annual levels and changes, snapshot dates and phases | Built | same | `test_living_views` | |
| E2.e | Charts persist through retirement; last year is the retirement year; no invented aging | Built | same | `test_living_views` | |
| E2.f | Distinct coach and caddie Ratings sections with real role skills | Built | `tools/observer.py` (`32bc43d`, `eba01e1`) | `test_living_views` (coach and caddie profiles) | Staff skills archived per season from 2026-11-02; no staff-skill history chart yet |

### E3 Injuries and their consequences

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| E3.a | Current injury, type, onset, expected recovery, actual return, time missed, lasting losses | Built | `golfsim/season.py`, `tools/observer.py` (`7d63213`, `5fdc76b`) | `test_living_views`, `test_injury_timing` | First return counts qualifying |
| E3.b | Announced duration separate from actual absence | Built | same | `test_injury_timing` | n weeks announced = n weeks of entries since rules 2026-11-02 |
| E3.c | One-time injury and return notifications for followed golfers | Branch v16-observer | `81cae53` | `test_myworld_events` | |
| E3.d | Profiles, season summaries, My World agree on episode identity and dates | Branch v16-observer | `81cae53` | `test_myworld_events` (returns are the profile's; items match records) | Profile side is Built on `build/v16` |
| E3.e | Missed events linked to injury only by a recorded reason | Built | `tools/observer.py` | `test_living_views` | |
| E3.f | No fabricated past medical detail | Built | same | `test_living_views` (older seasons: episodes not recorded) | |
| E3.g | Body-part damage or injury-rate tuning | Open decision | -- | -- | Roadmap: a separate design decision, not implied |

### P1 Visible prestige for every individual

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| P1.a | Prestige on golfer, coach, caddie profiles; sortable directories including retired people | Built | `tools/observer.py`, `tools/observer_history.py` (`32bc43d`) | `test_living_views` | Deceased people do not exist until C2 |
| P1.b | Staff reuse reputation under the Prestige label with a role explanation | Built | same | `test_living_views` (coach profile) | |
| P1.c | Multiple roles: each role's value, never combined | Built | `tools/observer.py` (directories, "Also" column) | `test_living_views` | Implemented choice; owner sign-off not in the decision log (open decisions below) |
| P1.d | Explain current achievement versus lasting legacy | Partly built | `tools/observer_history.py` | `test_living_views` | One value with an explanatory line; the 52-week and legacy parts are not shown separately |
| P1.e | Prestige, skill and experience kept distinct | Built | same | `test_living_views` ("not a rating of ability", "not a measure of skill") | |
| P1.f | Numeric sort in both directions; consistent missing values | Partly built | `tools/observer.py` directories | `test_living_views` (descending only) | Directories sort Prestige highest-first only; missing values last |
| P1.g | Every score dated; archived views never substitute current values | Built | same | `test_living_views` (season-end values recorded) | "now" or "as the published history ends"; role-switch case verification pending |

### P2 Five-year event, course and nation prestige

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| P2.a | Five-year history for event, course, nation; golfer model unchanged | In progress: v16-prestige (not pushed) | -- | -- | `golfsim/prestige.py` today: event prestige over the last 4 editions |
| P2.b | Four editions to five calendar years; warm-up, skipped editions, smoothing, annual limits | In progress: v16-prestige (not pushed) | -- | -- | Factors are an open decision |
| P2.c | Sustained field quality, ability known at the time | In progress: v16-prestige (not pushed) | -- | -- | |
| P2.d | Sortable Prestige columns and dated history bars on tournament, course, nation pages | In progress: v16-prestige (not pushed) | -- | -- | None of the three pages has a Prestige column on `build/v16` |
| P2.e | Course prestige apart from quality; sustained prestige reaches better hosts, lagged | In progress: v16-prestige (not pushed) | -- | -- | Host-quality relationship open |
| P2.f | Nation prestige from success beyond expectation, smoothed, small samples stabilised | In progress: v16-prestige (not pushed) | -- | -- | |
| P2.g | Participation multiplier, not talent; not through `nation.development` | Decided D7 | -- | -- | Share of the fixed new-golfer cohort, reallocated between nations; implementation in v16-prestige |
| P2.h | No future leakage, single-result jumps, circular feedback, talent bonus; unknown history stays unknown | In progress: v16-prestige (not pushed) | -- | -- | |

### S1 Staff careers and partnerships

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| S1.a | Specialty, youth expertise, ratings, prestige, experience, availability, capacity | Built | `tools/observer.py` (`eba01e1`, `32bc43d`) | `test_living_views` | |
| S1.b | One shared timeline from both sides: initiator, why joined, agreement, time, rapport, why separated | Built | `golfsim/history.py` stints, `tools/observer.py` | `test_living_views` (coach profile, recorded fit, staff seasons) | "Why they stayed" (loyalty) is added on v16-recruitment |
| S1.c | Shared achievements only from event records | Built | `tools/observer.py` (`_staff_seasons`) | `test_living_views` | Starts, wins, majors together from per-result staff |
| S1.d | My World team news: new partnership, reunion, split | Branch v16-observer | `81cae53` | `test_myworld_events` | |
| S1.e | My World team news: first shared major, retirement into a staff role | Not started | -- | -- | Role change is not a My World item |

### S2 Scouting that recognises upside

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| S2.a | Better scouts partly recognise high potential, from development speed, building on existing assessment | Branch v16-recruitment | `golfsim/staff.py` | `test_recruitment` (assessment) | Observation-only; reads no potential |
| S2.b | Confidence improves with observation; error, late bloomers, disappointments kept | Branch v16-recruitment | same (`Staff.watched`) | `test_recruitment` (firming, seasons watched) | Error x 1/sqrt(1 + 0.5 (seasons - 1)), max six seasons; a proposal |
| S2.c | No exact potential, not infallible; any noisy-glimpse option compared before choosing | Branch v16-recruitment | same | `test_recruitment` (never reads potential or ceilings) | No glimpse option proposed, so no comparison |
| S2.d | Teaching and scouting separate; youth versus elite specialists | Branch v16-recruitment | same | `test_recruitment` (motivations) | Teaching and scouting already shown apart on `build/v16` |

### S3 Two-way recruitment and motivations

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| S3.a | Staff pursue golfers; development coaches, elite coaches and caddies weigh different things | Branch v16-recruitment | `golfsim/staff.py`, rules 2026-11-04 | `test_recruitment` (motivations, caddie weighs earnings, fit, stability) | |
| S3.b | Loyalty and shared history; a better offer does not dissolve a good partnership | Branch v16-recruitment | same | `test_recruitment` (loyalty) | |
| S3.c | Approach, acceptance, refusal, retention, departure reasons visible on both sides | Branch v16-recruitment | `golfsim/history.py`, `tools/observer.py`, `tools/observer_history.py` | `test_recruitment` (refusals recorded) | |
| S3.d | Capacity, affordability, geography, one caddie a bag, career progression; lightweight | Branch v16-recruitment | `golfsim/staff.py` | `test_recruitment` (money and capacity, same seed same outcome, old saves load) | |
| S3.e | Compare offer rates, retention, quality distribution, development across seeds | Not started | -- | -- | Weights are proposals; the branch cites `docs/RECRUITMENT_PACKAGE.md`, which is not in its commit |
| S3.f | Record staff skills prospectively | Built | `golfsim/archive.py` (`staff_year`) | `test_living_views` (coach profile) | From rules 2026-11-02 |

### G1 Familiarity and course use

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| G1.a | State/province on courses; dated birthplace/home and residence regions | In progress: v16-geography (not pushed) | -- | -- | Country-level residence history exists (`golfsim/residence.py`, `test_residence`) |
| G1.b | Bounded regional baseline in the existing familiarity mechanism; no stacking or double counting | In progress: v16-geography (not pushed) | -- | -- | Today familiarity is rounds played (`golfsim/engine.py`) |
| G1.c | Top 10 familiar courses with values and links on profiles | In progress: v16-geography (not pushed) | -- | -- | |
| G1.d | Explain unused venues; event versus local/home clubs; review selection without forced rotation | In progress: v16-geography (not pushed) | -- | -- | |

### G2 Visible, largely stable Aggression

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| G2.a | Show the 0-100 Aggression trait with an explanation, not as an ability grade | In progress: v16-geography (not pushed) | -- | -- | Trait exists (`golfsim/engine.py`); not shown in the observer |
| G2.b | Trait stays stable; decline and conditions change choices; reach constraints kept and tested; no second risk score | In progress: v16-geography (not pushed) | -- | -- | |

### G3 Geographic seasonal conditions

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| G3.a | Climate by location and time of year, hemispheres, coastal exposure; bundled offline profiles | In progress: v16-weather (not pushed) | -- | -- | Today: wind ~ N(course typical wind, 3) per event, rain 8 % per round (`golfsim/season.py`) |
| G3.b | Wind distributions, direction, gusts, wetness; coherent across days; hole direction | In progress: v16-weather (not pushed) | -- | -- | |
| G3.c | Material shot effects; exposed links harder in wind; no blanket UK penalty | In progress: v16-weather (not pushed) | -- | -- | |
| G3.d | Skill, caddie and familiarity mitigation without immunity | In progress: v16-weather (not pushed) | -- | -- | |
| G3.e | Round conditions on scorecards and tournament summaries | Partly built | `tools/observer_history.py` | -- | Event pages already list each round's wind, rain, pin difficulty; no test found (verification pending) |
| G3.f | No rainouts, cancellations or delays | Built | `golfsim/season.py` | -- | No such mechanism exists; no test pins it (verification pending) |
| G3.g | Scope of temperature or firmness effects | Open decision | -- | -- | |
| G3.h | Plausible, reproducible conditions; archived weather does not drift | In progress: v16-weather (not pushed) | -- | -- | |

### Record Book (roadmap section 9)

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| R9.a | Name "Record Book"; records, routes, bookmarks preserved | Built | `tools/observer.py`, `tools/observer_views.py` (`26df0bf`) | `test_myworld` (menu and Record Book) | `/records` kept |
| R9.b | Desktop GOAT and Compare links; My World not duplicated | Built | same | `test_myworld` | |
| R9.c | Active/retired on Career Grand Slam and One Major Short | Built | `tools/observer_history.py` | `test_myworld` | |
| R9.d | Nation counts link to the exact population and time scope | Branch v16-observer | `3f0c036` | `test_nation_links` | |

### B1 and B2 Biggest Upsets

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| B1.a | Biggest Upsets with a major-only view | In progress: v16-upsets (not pushed) | -- | -- | |
| B1.b | Pre-event win probability against the field, documented and versioned; not ranking alone; drama kept apart | In progress: v16-upsets (not pushed) | -- | -- | Model is an open decision |
| B1.c | Persist inputs and model version, field strength known at the time | In progress: v16-upsets (not pushed) | -- | -- | |
| B1.d | Validate; unknown or separately labelled proxy; never mixed | In progress: v16-upsets (not pushed) | -- | -- | |
| B1.e | Existing filters; status and age at the event; entry content and links | In progress: v16-upsets (not pushed) | -- | -- | |
| B1.f | No future data; stable ties and missing values; reachable result | In progress: v16-upsets (not pushed) | -- | -- | |
| B2.a | Audited examples as regression and presentation cases, no forced order | In progress: v16-upsets (not pushed) | -- | -- | |
| B2.b | The retrospective screen is never relabelled as exact odds | In progress: v16-upsets (not pushed) | -- | -- | |

### T1-T3 Tournament stories and linked history

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| T1.a | Local generation; no AI service, subscription or per-story charge | In progress: v16-stories (not pushed) | -- | -- | |
| T1.b | Majors and Upsets first, then other prestigious events; profile and My World entry points | In progress: v16-stories (not pushed) | -- | -- | |
| T1.c | Fact record first, then varied patterns (upset, runaway, comeback, playoff) | In progress: v16-stories (not pushed) | -- | -- | |
| T1.d | Saved counters and scorecards only; strokes gained is the game's own baseline | In progress: v16-stories (not pushed) | -- | -- | Per-edition golf statistics and majors' hole-by-hole cards are already archived |
| T2.a | Stable links to people, courses, events, performances and rounds | In progress: v16-stories (not pushed) | -- | -- | |
| T2.b | Contemporaneous versus retrospective; frozen or regenerated policy | In progress: v16-stories (not pushed) | -- | -- | Policy is an open decision |
| T2.c | Nothing invented; qualified career bests; a source reference per claim | In progress: v16-stories (not pushed) | -- | -- | |
| T3.a | Prose out of simulation loops; bounded facts; incremental indexes; generate on open, cache | In progress: v16-stories (not pushed) | -- | -- | |
| T3.b | Measure throughput, latencies, memory, save/index growth on the same workload | In progress: v16-stories (not pushed) | -- | -- | |

### C1 Calibration without flattening rare careers

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| C1.a | Procedural entrants for principal conclusions, including retired and censored careers | Partly built | `tools/diagnostic_report.py`, `tools/long_world.py` (`473690a`) | `test_diagnostic_report`, `test_long_run_safeguards` | Seeded world kept apart; runs A-D approved and running; no conclusions yet |
| C1.b | Initial attributes, ceilings, coach exposure, prodigies, slow-burn, late wins, entry ages examined separately | Partly built | same, plus E1 records | `test_diagnostic_report` | Analysis waits for the runs |
| C1.c | Investigate the extreme starting tail and first-year gains before any cap | Partly built | same (`43bf2c4`: Overall at 19 only at exactly 19) | `test_diagnostic_report` | No cap added |
| C1.d | Peak duration, decline by part of the game, competitiveness across cohorts | Partly built | same | `test_diagnostic_report` | |
| C1.e | Superstar scheduling and its interactions; no forced 20 starts, 98 %, retirement age | Not started | -- | -- | Waits for run evidence |
| C1.f | Tolerance bands before tuning; independent seeds; runtime budgets proposed first | Partly built | `docs/LONG_RUN_PLAN.md` | -- | Seeds, lengths, time approved (D4, D9); tolerance bands open |

### C2 Death after retirement

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| C2.a | Death stage with rising annual risk, recorded date and age, stable identity | In progress: v16-death (not pushed) | -- | -- | |
| C2.b | No active competitive golfer dies; staff eligibility decided | Decided D6 | -- | -- | Retired golfers working as coaches or caddies can be eligible |
| C2.c | Staff retirement coordinated so implausible ages do not move into staff | In progress: v16-death (not pushed) | -- | -- | D6: affected partnerships end clearly |
| C2.d | Age frozen at death; results, relationships, records, profiles, links preserved | In progress: v16-death (not pushed) | -- | -- | Required by D6 |
| C2.e | Honest policy for very old people; no invented past death dates | In progress: v16-death (not pushed) | -- | -- | D6: no death dated before recorded work or play |
| C2.f | Idempotent, reproducible annual processing; explicit curve | In progress: v16-death (not pushed) | -- | -- | D6: curve is a provisional calibration |

### Calendar compatibility (roadmap section 12)

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| CAL | v2 for new worlds, v1 history browse-only, nothing deleted | Built | `tools/observer_worlds.py`, `tools/observer_app.py`, `golfsim/session.py` (`dd0bb27`) | `test_observer_app` | Settled by the owner's prompt of 31 October (not a numbered decision). v1 code paths remain for their tests |

## 2. Audit register N01-N23

| Id | Requirement | Status | Where | Tests | Notes |
|---|---|---|---|---|---|
| N01.01 | Explain low-probability retirement | Built | `golfsim/careers.py`, `tools/observer_history.py` (`decision_text`) | `test_finance_integration` (decisions recorded) | Chance and inputs shown; the draw is not retained. Display test: verification pending |
| N01.02 | Display retired status | Built | `tools/observer_data.py` | `test_myworld` | |
| N01.03 | Explain 16 starts and the deciding window | Audit answered | -- | -- | Starts are context, not the retirement formula |
| N02.01 | Annual ratings-change bar graph | Built | `tools/observer.py` | `test_living_views` | |
| N02.02 | Fixed readable bar size | Built | same | `test_living_views` | 38 px at both measured widths (browser, not automated) |
| N02.03 | Horizontal scrolling, not compression | Built | same | `test_living_views` | Scroll behaviour checked in the browser only |
| N03.01 | Caddie Ratings section | Built | `tools/observer.py` | `test_living_views` | |
| N03.02 | Coach Ratings section | Built | same | `test_living_views` | |
| N04.01 | Course Prestige column | In progress: v16-prestige (not pushed) | -- | -- | |
| N04.02 | Sortable course Prestige | In progress: v16-prestige (not pushed) | -- | -- | |
| N04.03 | State/Province column | In progress: v16-geography (not pushed) | -- | -- | |
| N04.04 | Home-state familiarity | In progress: v16-geography (not pushed) | -- | -- | |
| N04.05 | Current-residence-state familiarity | In progress: v16-geography (not pushed) | -- | -- | |
| N04.06 | No independent home advantage beyond familiarity | In progress: v16-geography (not pushed) | -- | -- | No home bonus exists today (verification pending) |
| N04.07 | Profile course familiarity | In progress: v16-geography (not pushed) | -- | -- | |
| N04.08 | Top 10 familiar courses | In progress: v16-geography (not pushed) | -- | -- | |
| N05.01 | Tournament Prestige column | In progress: v16-prestige (not pushed) | -- | -- | |
| N05.02 | Sortable event Prestige | In progress: v16-prestige (not pushed) | -- | -- | |
| N05.03 | Sustained strong fields affect prestige | In progress: v16-prestige (not pushed) | -- | -- | Field strength already a factor over 4 editions |
| N05.04 | Better prestige enables better host venues | In progress: v16-prestige (not pushed) | -- | -- | |
| N05.05 | Five-year rolling factor history | In progress: v16-prestige (not pushed) | -- | -- | |
| N05.06 | No big jumps | In progress: v16-prestige (not pushed) | -- | -- | |
| N06.01 | Nation Prestige | In progress: v16-prestige (not pushed) | -- | -- | |
| N06.02 | Sortable nation Prestige | In progress: v16-prestige (not pushed) | -- | -- | |
| N06.03 | Success beyond expectation in prestigious events | In progress: v16-prestige (not pushed) | -- | -- | |
| N06.04 | Increased future golfer quantity | Decided D7 | -- | -- | Reallocation of a fixed cohort, not more golfers |
| N06.05 | No arbitrary direct quality boosts | Decided D7 | -- | -- | |
| N06.06 | Five-year rolling average | In progress: v16-prestige (not pushed) | -- | -- | |
| N07.01 | Course prestige history chart | In progress: v16-prestige (not pushed) | -- | -- | |
| N07.02 | Tournament prestige history chart | In progress: v16-prestige (not pushed) | -- | -- | |
| N07.03 | Nation prestige history chart | In progress: v16-prestige (not pushed) | -- | -- | |
| N08.01 | Link nation counts | Branch v16-observer | `3f0c036` | `test_nation_links` | |
| N08.02 | Destination lists match the count's scope | Branch v16-observer | `3f0c036` | `test_nation_links` | Counted with the list's own filter |
| N09.01 | Verify Jefferson's amateur major win and qualification | Audit answered | -- | -- | |
| N09.02 | Research the real Masters, last 50 years | Audit answered | -- | -- | No amateur has won the real Masters |
| N09.03 | Explain the college player's attributes without suppressing the story | Not started | -- | -- | C1; waits for the runs |
| N10.01 | Late non-college entry distribution | Partly built | E1 creation records ("late entrant") | `test_development_evidence` | Measured by the runs; not calibrated |
| N10.02 | Barrett's entry age and pathway | Audit answered | -- | -- | |
| N10.03 | Repeated runner-up case | Audit answered | -- | -- | All ten seconds were mini-tour events |
| N10.04 | Age-26 entrants plausible and intentional | Not started | -- | -- | C1: intentional but uncalibrated |
| N11.01 | Starting attribute distributions | Partly built | E1 records, `tools/diagnostic_report.py` | `test_development_evidence` | Analysis waits for the runs |
| N11.02 | Potential influence | Partly built | same | `test_development_evidence` | |
| N11.03 | Coach influence | Partly built | same | `test_development_evidence` | |
| N11.04 | Fast prodigy trajectory | Partly built | same | `test_diagnostic_report` | |
| N11.05 | Slow-burn later greatness | Partly built | same | `test_diagnostic_report` | |
| N11.06 | Exclude the initialization cohort | Partly built | `tools/diagnostic_report.py` | `test_diagnostic_report` | Seeded world reported apart; filter itself not unit-tested (verification pending) |
| N11.07 | All procedural entrants, not survivors | Partly built | same | -- | Retirement coverage counts every cohort member; verification pending |
| N12.01 | Active/retired on Grand Slam | Built | `tools/observer_history.py` | `test_myworld` | |
| N12.02 | Active/retired on One Major Short | Built | same | `test_myworld` | |
| N13.01 | Southport Brook Public Golf Course | In progress: v16-geography (not pushed) | -- | -- | |
| N13.02 | Wren Dunes Golf Club | In progress: v16-geography (not pushed) | -- | -- | |
| N13.03 | Fjordby Helsinki Golfklub | In progress: v16-geography (not pushed) | -- | -- | |
| N13.04 | 2057 no-host observation checked separately | Audit answered | -- | -- | Unused through 2083 |
| N14.01 | Lenihan's high peak | Audit answered | -- | -- | |
| N14.02 | Why no professional career | Audit answered | -- | -- | Follow-up is F1 (amateur support built) |
| N15.01 | Cooper's 441 elite starts without a win | Audit answered | -- | -- | |
| N15.02 | Equivalent real-world record | Audit answered | -- | -- | Quigley, a near comparison |
| N15.03 | Explain the 1.4 % retirement | Audit answered | -- | -- | |
| N16.01 | Chart persists after retirement | Built | `tools/observer.py` | `test_living_views` | |
| N16.02 | Last chart year is the retirement year | Built | same | `test_living_views` | |
| N17.01 | Complete Harper-type development record | Partly built | E1 | `test_development_evidence` | New worlds record it; Test 1 cannot be reconstructed |
| N17.02 | Age-18 starting Overall | Audit answered | -- | -- | Not retained in Test 1; new worlds record it (E1.c) |
| N17.03 | Peak plausibility | Not started | -- | -- | C1 |
| N17.04 | 94 at age 41 | Not started | -- | -- | C1 |
| N17.05 | Decline still slow at 52 | Not started | -- | -- | C1 |
| N17.06 | Win count plausibility | Not started | -- | -- | C1 |
| N17.07 | No huge change from one outlier | Not started | -- | -- | C1 constraint; no change has been made |
| N17.08 | Annual starts fewer than 20 | Not started | -- | -- | C1 scheduling review |
| N17.09 | Scope-correct Scheffler comparison | Audit answered | -- | -- | |
| N18.01 | Explain the 55.8 % turn-pro decision | Audit answered | -- | -- | Chances now recorded per decision (E1) |
| N18.02 | Assess ~98 %, not an automatic constant | Audit answered | -- | -- | Not adopted |
| N18.03 | Research top amateurs declining pro careers | Audit answered | -- | -- | |
| N19.01 | Injury frequency believable | Not started | -- | -- | C1; any tuning is a separate decision (E3.g) |
| N19.02 | Stamina functioning as intended | Not started | -- | -- | C1 |
| N19.03 | Recovery functioning as intended | Not started | -- | -- | C1 |
| N19.04 | Harper's declining starts and causes | Audit answered | -- | -- | Weekly reasons recorded in new worlds (`test_access_ledger`) |
| N20.01 | Shi's age-55 physical attributes | Audit answered | -- | -- | |
| N20.02 | Decline timing | Partly built | `tools/diagnostic_report.py` (decline by part of the game) | `test_diagnostic_report` | Waits for run A |
| N20.03 | Decline rate | Partly built | same | `test_diagnostic_report` | Waits for run A |
| N21.01 | Locate the GOAT route | Audit answered | -- | -- | |
| N21.02 | Make the entry discoverable | Built | `tools/observer.py` | `test_myworld` | Mobile menu deferred |
| N22.01 | Death stage | In progress: v16-death (not pushed) | -- | -- | |
| N22.02 | Rising annual mortality after retirement | In progress: v16-death (not pushed) | -- | -- | |
| N22.03 | No death while active | Decided D6 | -- | -- | |
| N22.04 | No implausible living ages | In progress: v16-death (not pushed) | -- | -- | |
| N22.05 | Explicit playing-versus-staff policy | Decided D6 | -- | -- | |
| N23.01 | Retirement notification at the first transition only | Built | `tools/observer_myworld.py` | `test_myworld` | |
| N23.02 | No repeated annual retirement message | Built | same | `test_myworld` | |

## 3. Cross-cutting rules (roadmap sections 1 and 12)

| Rule | How it stands |
|---|---|
| Wide desktop first | Built (E2.a). **Mobile and small screens: deferred by owner** |
| Hide Results stays removed | Kept removed; legacy settings are read as compatibility only (F3.f) |
| Full-population worlds for validation | Three-season full-population measurement done; long runs A-D approved (D4, D9) and running |
| Preserve original saves and outcomes | Unsupported saves are browse/copy only, never continued or changed (`dd0bb27`, `test_observer_app`); old-world continuation dropped by the owner's prompt of 31 October |
| Local, offline, no subscription | Applies to G3 and T1; neither started on `build/v16` |
| Extend existing mechanics | Followed so far (staff Prestige reuses reputation; recruitment reuses stints and pair records; trip support uses the entry ledger) |
| Determinism and no repeated annual processing | `tools/equivalence_check.py`, `tools/determinism_replay.py`, `test_long_run_safeguards`; per-package checks in the V16 and V17 reports |
| Performance measured on representative workloads | Long histories measured on a 57-season copy (V17 report); story and weather costs not yet measurable |
| Career mode | **Deferred by owner**: planning follows the readiness review |

## 4. Summary by roadmap item

| Item | State | Built | Partly | On a pushed branch | In progress (not pushed) | Not started | Decided | Open |
|---|---|---|---|---|---|---|---|---|
| F1 | Initial calibration built; values and categories open | 5 | 4 | 0 | 1 | 0 | 1 | 0 |
| F2 | Built; per-case reconstruction partial | 5 | 1 | 0 | 0 | 0 | 0 | 0 |
| F3 | Built | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| E1 | Built except target, fatigue and draw inputs | 7 | 1 | 0 | 0 | 0 | 0 | 0 |
| E2 | Built; group views on branch | 5 | 0 | 1 | 0 | 0 | 0 | 0 |
| E3 | Built; My World items on branch | 4 | 0 | 2 | 0 | 0 | 0 | 1 |
| P1 | Built; two-way sort and legacy split missing | 5 | 2 | 0 | 0 | 0 | 0 | 0 |
| P2 | Not on build/v16 | 0 | 0 | 0 | 7 | 0 | 1 | 0 |
| S1 | Built; team news on branch, two news kinds not started | 3 | 0 | 1 | 0 | 1 | 0 | 0 |
| S2 | On branch v16-recruitment | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| S3 | On branch; cross-seed comparison not started | 1 | 0 | 4 | 0 | 1 | 0 | 0 |
| G1 | Not on build/v16 | 0 | 0 | 0 | 4 | 0 | 0 | 0 |
| G2 | Not on build/v16 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| G3 | Not on build/v16 (round conditions already shown) | 1 | 1 | 0 | 5 | 0 | 0 | 1 |
| Record Book | Built; nation links on branch | 3 | 0 | 1 | 0 | 0 | 0 | 0 |
| B1/B2 | Not on build/v16 | 0 | 0 | 0 | 8 | 0 | 0 | 0 |
| T1-T3 | Not on build/v16 | 0 | 0 | 0 | 9 | 0 | 0 | 0 |
| C1 | Instruments and harness built; runs in progress; no calibration | 0 | 5 | 0 | 0 | 1 | 0 | 0 |
| C2 | Policy decided (D6); not on build/v16 | 0 | 0 | 0 | 5 | 0 | 1 | 0 |
| Calendar | Built | 1 | 0 | 0 | 0 | 0 | 0 | 0 |

Totals (rows in sections 1 and 2; the cross-cutting rules in section 3 are not counted):

| Status | Item rows (122) | Register rows N01-N23 (88) | All (210) |
|---|---|---|---|
| Built | 46 | 14 | 60 |
| Partly built | 14 | 11 | 25 |
| On a pushed branch (v16-observer 7, v16-recruitment 8) | 13 | 2 | 15 |
| In progress, branch not pushed (prestige 22, geography 15, stories 9, upsets 8, death 8, weather 5, amateur-return 1) | 41 | 27 | 68 |
| Not started | 3 | 11 | 14 |
| Decided (D3, D6, D7) | 3 | 4 | 7 |
| Open decision | 2 | 0 | 2 |
| Audit answered | 0 | 19 | 19 |

## 5. Decisions

Settled (`docs/DECISIONS_2026-10-31.md`): D1 qualification windows (done, `32a0a6f`); D2 work pathway (done,
`3d3090e`); D3 amateur support caps kept for the measurements; D4 support comparison on one build; D5 return to
full-time golf in direction; D6 death policy (C2); D7 national participation by share of a fixed cohort (P2); D8
releases to main after HAL's check; D9 long tests from 17:00 UTC on 31 October. Also settled by the owner's prompt
of 31 October: fresh worlds only, v2 calendar, unsupported saves browse-only.

Open (waiting for the owner):

1. **D5a** return-to-full-time thresholds (hard age gate or HAL's sustainable-budget refinement).
2. **Final amateur sponsor values** after runs B/C (D3 is interim), and whether cash sponsorship, equipment support
   and amateur prize-money eligibility are wanted at all (F1.c).
3. **P2 settings**: five-year factors, warm-up and skipped editions, smoothing, lag and caps, and the event-to-host
   quality relationship (the population rule is D7).
4. **Multi-role Prestige** display and sort, and **staff-skill visibility** (teaching and scouting shown since rules
   2026-11-02): both implemented as choices in the V17 pass; neither is recorded as an owner decision.
5. **Scouting method and recruitment/retention weights** (v16-recruitment's proposed starting values).
6. **Weather**: climate profile source and licence, granularity, wind units and direction model, gusts, bounded
   wetness effects; whether temperature or firmness are in scope (G3.g).
7. **Upsets and stories**: probability model and calibration, legacy proxy handling, significance thresholds,
   narrative perspective (frozen or regenerated recaps) and cache policy.
8. **Lifecycle**: the mortality curve (D6 calls it provisional), handling of very old people, staff retirement
   interaction.
9. **Testing**: cohort tolerance bands before calibration (C1.f), hardware baseline and performance tolerance
   bands.
10. **Unused municipal courses**: competition venue or local/home club role (N13, G1.d).
11. **Injury body-part damage or rate tuning** (E3.g; optional, not implied by the roadmap).
