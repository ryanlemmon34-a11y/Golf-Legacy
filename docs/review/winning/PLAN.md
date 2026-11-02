# What decides who wins: attributes, archetypes and weather (read-only study plan)

Branch `research/attribute-winning-analysis`, cut from released main `18a8e23`. Research only. The study changes
no balance, engine, growth, scoring, weather or generation code, and it touches neither main nor the career
branch (that work is parked at `8354ea0` with three known defects queued for afterwards). Controlled experiments
are analysis, not deployment. No parameter edits are recommended until this audit has been reviewed.

Ryan's questions (2026-11-02):

1. How often does the golfer with the best Overall win?
2. Which archetypes win tournaments most?
3. Which attributes have the most and the least impact on winning?
4. How much did weather affect who won?

Out of scope: morning/afternoon (tee-wave) weather. Every golfer in a round shares one set of conditions. This
study analyses that model as it is and neither proposes nor tests a tee-wave model.

## 1. Sources and provenance

**The save.** Test2, the original 57-season save:

- world `386509-1793467568`, seed 386509;
- committed generation 70, at 2084 week 1 (start);
- checkpoint sha256 `c55bbd2f…`;
- calendar v2, rules `2026-11-11` in every season.

The save was written by engine `1949ff63…`, which is `engine_id(c0d1ea5)`. The scripts read only its JSON
history (`archive/`): the 57 season files, people and world. Every file's sha256 is recorded. The pickled
checkpoint is not opened.

**Engine identity for experiments.** These files are byte-identical between `c0d1ea5` and main `18a8e23`:
`engine.py`, `tournament.py`, `weather.py`, `course.py`, `golfer.py`, `ratings.py`, `baseline.py`,
`familiarity.py` and `upsets.py`. The v17 changes since `c0d1ea5` touched only:

- `archive.py`, `careers.py`, `decision_evidence.py` and `participation.py`;
- `population.py` (cohort carry), `rules.py` and `season.py`.

So controlled tests of the scoring engine on main measure the code that produced the save. Replays of the save's
own history run on a clean `c0d1ea5` checkout, the exact engine.

## 2. Data audit (done; `results/AUDIT.md` will hold the tables)

`extract.py` streams every season once:

| Item | Coverage |
|---|---|
| Editions | 83,181 in total |
| Primary editions | 81,871: one site, stroke play, not qualifying, with a stored pre-event estimate whose entrant list reconciles exactly with every starter (made cut, missed cut, withdrawn), and exactly one champion. All 81,871 eligible editions pass, with zero reconciliation failures. |
| Excluded editions | 1,139 qualifying (multi-site stages and Q-school); 171 match play |
| Primary starts | 7,794,527, each with a pre-event Overall |
| Pre-event Overall | Stored by the engine in each edition's estimate (`upsets.inputs`, rounded to 0.1). The worker computes it from the golfer objects that played, before any shot. |
| Pre-event full attributes | **Not archived.** The archive has only creation vectors (dated) and season-end ratings. The replay in section 3 recovers them exactly; until then any attribute-level use of archived ratings is a separately labelled proxy (previous season-end), never treated as pre-event. |
| Weather | Every one of the 228,604 recorded rounds carries all five seasonal values: wind mph, wet, pin difficulty, direction and gustiness. |
| Native archetype | **Not archived.** It is recovered by generation replay, see below. |

**Native archetypes, recovered and verified** (`recover_archetypes.py`). Each generated golfer draws from its own
stream: `{seed}:golfer:{id}`, `{seed}:j{year}:golfer:{id}` or `{seed}:p{year}:golfer:{id}`. The first draw is the
archetype; the next 21 draws are one noise value per attribute. A label is kept only when the archived creation
vector of all 21 attributes is reproduced: every unclamped attribute's residual (recorded minus offset, tilt, age
shift and replayed noise) equals one common shift to within the 0.1 rounding.

| Group | Golfers | Status |
|---|---|---|
| Initial | 6,550 | verified |
| Juniors | 16,810 | verified |
| Late entrants | 23,924 | verified |
| Cárdenas (19411) | 1 | verified_clamped |
| No creation record | 704 | unknown |

- **Verified.** The largest spread among verified golfers is 0.10. Every other archetype misses by at least 15.9
  points (Cárdenas: 10.0), so labels are unambiguous; Overall alone could never separate them.
- **Cárdenas.** He was created at 18 with an Overall of 96.1, with 10 attributes clamped at 99. His other 11
  reproduce exactly and the clamped ones are consistent with the clamp. Label: Power Hitter. He is reported as
  his own tier.
- **Unknown.** These 704 make up the 2084 class, which was created for a season that was never played. None of
  them has an archived start.
- **Coverage.** 100% of archived starts carry a verified native label. No label is ever inferred from results.

## 3. Exact replay of the save's history (validation first, then capture)

`replay.py` creates a world from seed 386509 and start year 2027 exactly as the observer does. It runs on
`c0d1ea5` and checks every played event against the archive: every site's complete finish list and every round's
recorded conditions. The first mismatch stops the replay.

- **Pilot.** Weeks 1–3 of 2027 reproduced all 47 events exactly in 17 s.
- **Plan.** Replay season by season with the same check, stopping at the first mismatching season. While
  replaying, record every starter's exact pre-event state: 21 attributes, personality, season fatigue, effective
  course familiarity and caddie.
- **Full tasks.** For a bounded set of editions, the exact task the worker played is also kept:
  - every major;
  - Premier events in sampled years;
  - representative lower-tour, links and sheltered events.

  These files are written and read only by this study's processes, stay in RAM scratch and are never committed;
  the committed results are compact tables.
- **Divergence.** Python versions and platforms differ (Windows/3.15 for the save, Linux/3.13 here). If the replay
  diverges, the seasons verified up to that point are used, and the divergence is reported, not hidden.

## 4. Component 1: favourite versus winner (descriptive, archive)

**Population.** Primary editions, with denominators shown for every cut. Analyses that use the stored estimate's
probabilities also label them model approximations (`upset-model-1`, Overall only), not calibrated truth.

**Best entrant.** The highest pre-event Overall, with ties at the stored 0.1 resolution treated as a set:

- unique best versus tied best, reported separately;
- the win rate of the unique best;
- for tied sets, the win rate of the set and a per-member share.

**Measures:**

- the winner's Overall rank (competition ranking) and gap to the best;
- top-1, top-3 and top-5 rates;
- the best entrant's finishing distribution (win, top 3, top 10, missed cut);
- the winning margin and playoffs.

**Strata:**

- field size and rounds (1–4);
- level: majors, Premier, tiers 2–4, college, amateur, club pro;
- era (decades) and the gap between the best and next-best entrant (bins);
- field depth (the top-10 mean Overall, and the number within 2 or 5 of the best).

**Sensitivities:**

- excluding Cárdenas's own starts and wins;
- excluding every edition he entered (a distinct test);
- initial seeded golfers versus later entrants.

**Uncertainty.** Golfers and seasons repeat, so the bootstrap is clustered by golfer (the best entrant's
identity), with an edition-level bootstrap alongside.

**Scoring.** On the replayed seasons, the same measures using exact full attributes.

## 5. Component 2: archetypes (exposure, not raw counts)

**Labels.** Native verified labels only. Both measures are reported, pooled across levels and by level (majors,
Premier, tiers 2–4, amateur, college, club pro):

- population share at creation;
- start share.

**Rates:**

- wins, wins per 100 starts, and top-10 and cut rates;
- field exposure, the sum over editions of n_archetype/field size, so expected wins under equal skill can be
  compared with observed wins (separating opportunity from superiority).

**Comparable ability.** Win rates by pre-event Overall bin and by Overall rank within the field, stratified
(Mantel–Haenszel style) or with a within-edition conditional logit on Overall plus archetype. The model never
holds Overall and all 21 components at once.

**Further splits:**

- initial seeded golfers versus later entrants;
- prime (ages 25–35) versus full careers, compared on the same footing;
- excluding Cárdenas.

**Uncertainty.** A golfer-clustered bootstrap.

**Mechanism.** A separate controlled fixed-Overall comparison of the eight archetype profiles
(`golfer.archetype_golfer`, the same Overall exactly) in identical fields, courses and conditions (section 6).

## 6. Component 3: attribute impact (code map, then controlled experiments)

**Code map** (`ATTRIBUTE_MAP.md`). Every one of the 21 attributes, plus personality (aggression, big_stage),
caddie, familiarity, week/day form, pressure, tilt, round and week fatigue, and season fatigue, is traced to the
lines that use it. Each is classified as:

- a **direct shot-level effect**;
- a **conditional effect** (pressure, wind, wet, rounds 2–4); or
- an **indirect effect** (development, availability, injury, access).

Known checks:

- `injury_resistance` has no direct shot effect and only affects availability. It is the zero-direct-effect
  sanity check, so its result is labelled as such, not "worthless".
- `long_irons`' approach multiplier is flat over 25–60 (`APPROACH_MULT`). A perturbation wholly inside that
  interval must give exactly zero direct score change even though Overall moves. Mid irons and wedges also feed
  `CONTACT_FLOOR`, so that flatness is not generalised to them.
- `OVERALL_WEIGHTS` are not winning-contribution percentages, and they are reported as such.

**Harness** (`experiments.py`). It calls the production event function (`season.play_site`) on captured real tasks
and on constructed fields. The harness changes no code: perturbations are made on copies of golfer objects in the
task.

1. **No-op baselines.**
   - `play_site` on a captured task reproduces the archived edition exactly.
   - Running an arm with a zero perturbation reproduces the baseline exactly.
2. **Random streams.** In production, one shot stream per site is shared by the whole field in tee order, and draws
   are conditional (club choice, lies, putts). Changing one golfer therefore shifts the stream for everyone after
   them; it is not a matched pair. Two designs are reported:
   - **(a) Production-stream pairs:** the same seeds, unbiased but noisier. The study measures and reports how far
     the field's outcomes diverge.
   - **(b) An isolated-stream harness** that gives every golfer, every round, its own stream derived from (seed,
     golfer, round). It calls the same `play_round`/`Player`/`play_hole` code, so only the perturbed golfer's own
     shots change, apart from genuine interactions through cut and pressure, which are counted.

   Design (b) is first shown to be distributionally equivalent to (a) on no-op runs (score mean, SD and tails;
   favourite win rate) before it is used. The perturbed golfer's own stream diverges at their first conditional
   draw; that is disclosed, and estimates come from replicated paired seeds, never from one changed winner.
3. **Perturbations.**
   - +5 attribute points to one attribute; nothing else changes, Overall is not rebalanced, and development
     ceilings are not rebuilt. Base values are chosen so +5 never clips at 99; any clipping is reported.
   - Nonlinearity sensitivity: −5 and +10 for all 21 attributes on one subject, and +5 at a lower base level.
4. **Stage A (scoring, cheap and precise).**
   - Subject golfers at several levels (a top favourite, a contender, a mid-tour player) on representative courses
     (links, open coastal, sheltered parkland/woodland) in calm, moderate and strong seasonal conditions.
   - Δ strokes per round and per 72 holes, SD, tails (rounds ≥ +5 over the mean, best-round rate), cut and top-10
     rate.
   - Rounds 2–4 are separated so `recovery_rate` (week fatigue) and pressure-dependent `composure` can show.
5. **Stage B (winning).** Full-event paired replicates in real captured fields: a major, a Premier event and a
   lower-tour event. Δ win probability (pp), Δ top-5/10, Δ cut, with bootstrap CIs. A variance reduction can raise
   a favourite's win chance while lowering an underdog's, so subjects at different field ranks are shown.
6. **Equal-Overall and equal-SD comparisons.** These are separate experiments, never mixed with +5-point effects.
   - Equal-Overall: the eight archetype profiles at the same Overall.
   - Equal-SD: perturbations scaled to each attribute's population SD.
7. **Rankings.** Context-dependent tables (by subject level, course and conditions), not one universal
   strongest-to-weakest list.
8. **Budget.** A pilot first reports runtime per event and per round and the achieved standard errors. The grid is
   then sized for chosen precision (for example SE ≤ 0.03 strokes/round in Stage A, SE ≤ 0.5 pp on Δwin for the
   favourite in Stage B) within a few CPU-hours on 3 worker processes. Depth of attribution takes priority over a
   giant grid.

## 7. Component 4: weather

1. **Coverage.** Recorded weather by month, region and climate, and by course style (links, coastal, parkland…;
   course style from the course library, matched to world.json by id). The relation of wind and wetness to
   geography, season and course.
2. **Descriptive.** Favourite win rate, the winner's Overall rank, scoring dispersion and margins by wind band and
   wet rounds, with course, level and field depth shown as confounders (within-course and within-series
   comparisons where enough editions exist). This part is descriptive only.
3. **Matched counterfactuals** on captured real tasks: identical field, golfer state and course; only the
   conditions change, all in the seasonal model.
   - The comparator is calm seasonal weather (`wind_from` kept, wind 0, dry). It is never the default
     `Conditions()`, which switches to the classic model. Arms: calm, moderate and strong wind, dry and wet.
   - Gust streams are seeded from the conditions (`weather.gust_seed`), so a changed condition also changes each
     golfer's gust realisation, and wind > 0 adds per-hole wind terms; these are disclosed.
   - The shot stream draws are conditional on outcomes, so a weather change shifts the shared stream (as in
     section 6). Estimates come from replicated paired seeds in both stream designs.
   - Measures:
     - the same-winner versus changed-winner rate;
     - favourite win rate, the winner's Overall rank, scoring mean (the common penalty) and dispersion;
     - margins;
     - which attributes and archetypes gain relative to the field (rank change, not raw strokes).

   Links versus sheltered courses where the library supports it. For an actual historic event a counterfactual is
   claimed only when its exact complete pre-event state was replayed and verified (section 3).

## 8. Deliverables

`docs/review/winning/`:

- `PLAN.md` (this file);
- scripts: `common.py`, `extract.py`, `recover_archetypes.py`, `replay.py`, the analyses and `experiments.py`;
- `ATTRIBUTE_MAP.md`;
- `results/`: compact CSV/JSON tables, the audit, the archetype label table, validation logs and the
  experiment manifest (commit, engine id, seeds, config);
- `REPORT.md`: findings, limitations and the questions answered.

Large intermediates (the per-start table, captured tasks, replay sessions) stay in RAM scratch and are rebuilt by
the scripts. Tests: the scripts' own self-checks (no-op baselines, reconciliation counts, the label validation and
the long-irons and injury-resistance zero checks) are recorded in `results/`. Parent reviewers audit the code and
methods independently.
