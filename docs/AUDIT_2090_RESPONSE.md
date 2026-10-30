# The 2090 world audit: what changed, what is proposed, what stays unknown

Response to "Golf Legacy 2090 World Audit" and the roadmap "Fix genuine access defects and make history explain
itself" (both 30 October 2026), for the owner's 63-season world (seed 2027, 2027-2089, cursor 2090 week 1).
That world was not modified, re-run or migrated: it is the evidence baseline. Everything below was developed on
copies (the 50-season world of engine 7334ffe, a fresh world) and small test worlds.

**Engine change.** This increment changes simulation code (the confirmed fixes below), so the engine
fingerprint changes: worlds made by earlier versions -- the 63-season world included -- open read-only as
"another engine", or continue on this engine through a copy ("Copy" in the World library, with "continue with
this engine"). New worlds, and copies continued on this engine, record the new facts from their next season;
earlier seasons stay as recorded.

## Confirmed fixes (implemented and tested)

### 1. Winners without a Premier card (Jack H. Harris)
*Defect.* A winner's exemption (a major in the last five seasons, a Premier event in the last two) protected
only an existing Premier member's card. A Challenger member who won majors stayed a Challenger member (his
home tour's money list, which he no longer played, decided his card) and queued for every Premier field behind
every Premier member, conditional ones included (priority class 14 against 0-7). Reproduced in the 50-season
copy: of 197 Premier-event and major wins by golfers without a card, 100 were followed by another season
without one (93 on a Challenger tour). A
fixture with the old code: a Challenger member who won two majors and $5M of Premier money was demoted to a
Regional tour.

*Fix* (`golfsim/cards.py`, `golfsim/season.py`, `golfsim/careers.py`; rules `winner-exemption`,
`premier-cards`):
- `cards.winner_exemptions` is one rule for everyone: the exemption belongs to the winner, whatever their
  membership. A win during the season counts from that week (`Season.earned`, updated as each major or Premier
  event is recorded, rebuilt from results for older saves).
- Field priority: a professional holding an exemption without a card enters Premier events as exempt (class
  1, alongside exempt members of other circuits); a member who wins becomes exempt for the rest of the season.
  Eligibility for Premier events includes the exemption; lower-tour starts stay allowed.
- Accession: at season end a full-time professional without a card earns one with a winner's exemption, or
  with Premier money (majors and Premier events) above the last member to keep a card, and joins the Premier
  circuit their home Challenger tour promotes to. An amateur major champion who turns professional starts there.
  Part-time professionals are not carded (a recorded choice of life, not a card decision).
- Not done, deliberately: no promotion by ranking alone, no ban on lower-tour starts, no guaranteed field
  places beyond the exemption's priority.

*Tests* (`tests/test_entry_rights.py`, 12): exemption windows and expiry; non-member major champion accession and
exempt rights next season; accession by Premier money; ranking alone promotes no one; part-timers not carded;
amateur major champion turning professional; field priority against full and conditional members; in-season
win; save and reload; no duplicate card change; a major played in full records the exemption.

### 2. Amateur golf where an amateur lives (Jae-won T. Jung, Lukas Johansson)
*Defect.* After college an amateur's home circuit was assigned by nationality, and ordinary amateur events
admitted members, nationals and current college students -- not residents. A Korean graduate who stayed in New
York lost his local amateur golf (starts 9, 7, 1, 0, 0) without any move.

*Policy implemented* (rules `open-amateur`, `amateur-home-circuit`; `golfsim/season.py` `series_amateur`,
`golfsim/careers.py` `amateur_series`, `golfsim/residence.py`):
- Ordinary amateur events of a circuit admit amateurs who live in its countries, as well as members,
  nationals and college students there. National championships still follow nationality only.
- A graduate (or anyone becoming an amateur) takes the circuit of where they live; an amateur who later moves
  (once per winter at most, as before) takes up the circuit of their new home. Nationality never changes and
  still opens their own country's circuit. Professionals' eligibility and tour cards are unchanged.

*Tests* (`tests/test_amateur_residence.py`): a foreign graduate who stays keeps North American amateur golf and
no move is invented; residence opens local amateur golf but not professional events; returning home takes up the
home circuit with one recorded move; nationality fallback.

### 3. Name variety (74.8% of 2089 names with a middle initial)
*Cause.* Every new name had to differ from every name in the world's history (retired people included), so the
largest nations' banks ran out (USA: 14,320 golfers in 50 seasons for 10,080 first-and-family combinations;
South Korea 2,037 for 756) and the middle-initial fallback took over.

*Fix* (`golfsim/names.py`, `golfsim/careers.py`): new arrivals draw from larger banks (US, UK, Australian,
Japanese, Korean, Thai, Danish, Swedish, Chinese, Norwegian, Italian and Indian names: 3-7 times the
combinations for the pressed ones); a name never used comes first, then a name no *active* person holds (a
retired person's name can recur, as in life; people are told apart by id, birth year and nationality), and a
middle initial only as the last resort. The starting world of a seed is unchanged (it keeps the original
banks), existing names are never rewritten.

*Measured* by replaying the 50-season copy's 35,784 arrivals through both rules (names only, nothing simulated):
old rule 46.6% of active golfers with a middle initial by the 50th season (the audit found 43.3% at 2070); new
rule 0.0%, no reused names, no two active golfers sharing a name. Over a century some names of retired people
will recur. *Tests*: `tests/test_names.py`.

### 4. Facts kept from now on (the history the views need)
Every season played on this engine records (`golfsim/archive.py`, index schema 3):
- each starter's **prize money as paid** (the index's `starts.prize`; editions' `prizes`), so per-tour and
  per-event money is recorded rather than recomputed;
- each golfer's **round scores** at every site, each round's **conditions** (wind, rain, pin difficulty), and for
  majors **hole-by-hole scores** with the holes' pars;
- the **rules version** the season was played under (`golfsim/rules.py`), each golfer's **winner's exemption**,
  the **reason they hold next season's card**, and the **college eligibility ledger** (each season enrolled,
  once);
- the initial residence (a college placement included) was already recorded (`first_residence`); the profile
  now shows it as an initial placement, not a move.

Checked on a fresh world: round scores reproduce every recorded total (5,220 of 5,220) and the missed cut;
recorded payouts match each golfer's season prize money (0 differences); the index carries a prize for every
start. Seasons played before this engine show "not recorded" -- rounds are never reconstructed from totals, old
per-event money stays the reconciled recomputation (or "unknown"), old card reasons show only promoted / lost.

## The observer (implemented, tested)
- **Rules page** (`/rules`), versioned; every "How they got in" reads in words with a link to its rule and the
  recorded code kept beside it; edition and season pages say which rules version applied.
- **Profiles**: a Status section (membership, level, lifestyle, Premier rights and why, a winner's exemption,
  why they hold their card, college eligibility) and every change of tour, status or lifestyle with its
  recorded reason and the decision's recorded inputs (chance, money runway, progress, desire, places secured,
  season net) -- never an invented story; each season links to **the season as it was** (that season's tour,
  rights, rankings, card, residence, ratings from recorded snapshots only, team, decisions, moves and history
  lines; the current season marked partial); missed cuts and **career totals** (overall and by tour) in the
  season table; **coaches and caddies in separate sections** with starts and wins together during each stint;
  **where they have lived** with birthplace, the initial placement and each dated move.
- **Tournaments**: a summary (most wins, most starts, most-used courses, youngest and oldest winners, counted
  over every edition and linked to the golfer's results in that tournament) and each edition's course.
  **Courses**: the tournament mix and total starts. **Editions**: winner, field, prize money paid, and **Rounds
  & replay** (the leaderboard after each round, labelled as a replay of recorded rounds, conditions, missed cuts;
  majors' hole-by-hole scorecards).
- **Records**: every row shows when (the date or the first and latest dates of its evidence) and whether the
  person is still pursuing it -- currently extending (a live streak, world No. 1 now, a partnership still going),
  competing (can add to a count), fixed (a single result) or closed (retired); evidence beyond three events
  counted. **Career Grand Slam** page (four distinct majors; completion at the first win of the fourth; age;
  partial careers flagged) and a line on the profile.
- **Year-end recap**: majors with coach and caddie, most professional wins, prize money leaders, world No. 1s,
  Premier cards earned (non-member accessions named), career changes that winter (major champions named),
  Grand Slams completed, moments and course records, the year-end ranking.
- **Every table sorts** in the browser (numbers as numbers, missing values last; on paged lists, the page
  shown); coaches and caddies sort by reputation or current clients; money is shown as dollars throughout,
  unknown kept apart from zero.

## Proposals for the owner's review (not implemented)

**College eligibility.** Implemented as an explicit, recorded rule unchanged in effect ("Golf Legacy ruleset 1":
every season from enrolment through the season the golfer turns 22, so five for an 18-year-old). Options:
(a) keep it (close to the NCAA's 2026 age-based five-year window); (b) four competitive seasons within five
years (the older NCAA model: needs a redshirt notion); (c) by cohort, if the world should change rules at a date.
Lachlan Whitbread's five seasons are valid under (a) and stay recorded either way.

**Premier circuits.** The Europe top 10 and Asia-Pacific top 5 move to Americas each year: a fixed hierarchy,
now explained on the rules page. Options: keep; or let leading players choose a circuit by preference and
residence, with a minimum number of starts on the chosen circuit (needs a choice model and obligations).

**Elite venues and the USA Amateur.** Northcote Park National (elite) hosts only the Premier Tour Championship,
every eight years: lower and amateur events may not use elite courses, and series keep home courses. The
"Kohler is a USA Amateur host but never hosts" mismatch has a precise cause: in Kohler's turns (2029, 2037,
2045...) a Sunbelt mini tour event is assigned Kohler's only eligible course (Pemberly Bluff) first, because
venues are assigned in order of tier, and Northcote is elite; the championship goes to Omaha (6 of the first 20
editions). Options: assign venues by event standing (majors, flagships, national championships before ordinary
events) rather than tier; allow a curated list (USA Amateur, Britannia Amateur, selected flagships) to use elite
courses on rotation with rest years. Either changes future schedules for every world.

**Profitable exits.** The rare voluntary stop by a solvent, successful professional (0.6% per season among
qualifying Premier seasons in the audit) is a modelled choice; its recorded inputs are now shown. Calibrate only
with multi-seed evidence.

**Hall of Fame (proposal).** Golfers eligible three seasons after their last start (or at 50); inducted when a
transparent points total reaches a threshold (e.g. major 10, Premier win 2, weeks at No. 1 0.1 each, Career Grand
Slam 10, Premier money titles 3), evaluated each season end and recorded with the evidence; coaches and caddies
in a separate category by their clients' recorded results during actual partnerships. No quotas, no ballots, no
effect on the simulation.

**Prestige and reputation.** Keep them apart: *prestige* is standing earned by results (players: the engine's
player prestige from fame and legacy; tournaments: event prestige; courses: class and hosting history);
*reputation* is a coach's or caddie's professional standing. A sortable "current and peak" for each needs the
peak recorded each season from now on (no historical peaks invented).

**Watching a tournament live.** Delivered: replay of recorded rounds. True round-by-round advancement of a
tournament in progress would need the tournament's phase and random state saved in the checkpoint, exactly-once
round steps, a new session format and interruption tests -- a separate deliverable, to be agreed first.

## Still unknown, or later evidence
- The 63-season world's old seasons keep what they recorded: no ratings history before ratings were kept, no
  round scores, payouts or rules version (old per-tour money is the reconciled recomputation).
- Calibration questions (winner ages, development timing, retention, course difficulty, geography) need
  several worlds on one recorded engine; nothing here tunes them.
- Restore and compatibility of the 63-season world's pickled state were not tested here (not supplied).
