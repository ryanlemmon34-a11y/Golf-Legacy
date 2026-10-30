# The pretest review: what changed before the next long playtest

Response to the roadmap's *pinned pretest code review* (29 October 2026, reviewed head 5bcc6ed), which asked
for durable golf-performance history, ranking-point transparency, largest-victory records and five specific
correctness fixes before the next long run, and staged the approved history explorers after them. Nothing
here touched the owner's 63-season world or launched a long run; development used small fresh worlds.

**Engine.** The capture is bookkeeping inside the simulation (`golfsim/`), so the engine fingerprint changes:
earlier worlds open as "another engine" (browse read-only, or Copy with "continue with this engine"). It
does not change a single shot, result or decision: one season of seed 21 (scale 0.03) played on the reviewed
engine (5bcc6ed) and on this one gives identical results for all 345 editions and identical season rows for
every golfer (compared from the two archives).

## Done before the long run

### 1. Access fixes verified, not rebuilt
The Harris accession/rights and residence-aware amateur access fixes were left as they were and their focused
regressions run: `tests.test_entry_rights` (12 tests) and `tests.test_amateur_residence` (8) pass, as does the
whole suite (see *Tests* below).

### 2. Golf-performance history (`golfsim/golfstats.py`, rules `golf-statistics`)
- **Captured during the existing simulation**: each golfer's counters for each edition, summed from their
  completed 18-hole stroke-play rounds: rounds, holes, strokes; measured drives and their yards; fairways and
  fairway opportunities; greens in regulation; putts and putts on GIR holes; three-putts; scrambling chances
  and saves; sand-save chances and saves; penalty strokes; eagles or better, birdies, pars, bogeys, doubles,
  worse; strokes and holes on par 3s, 4s and 5s; strokes gained (four categories, against the engine's own
  table); and the longest measured drive with its round and hole. Integers (yards in tenths, strokes gained in
  hundredths), definitions version 1.
- **Definitions** (in the code, on the rules page and under every table): driving distance is the first tee
  shot on a par 4 or 5 hit with a driver, carry and roll to where it finished, misses included, a re-tee after
  out of bounds not measured again (the engine previously counted a re-tee as another fairway attempt: fixed in
  the counter, not in play); fairways hit are first tee shots on par 4s and 5s finishing on the fairway (a
  fairway bunker or a driven green is not the fairway; par 3s never count); GIR is the putting surface in par
  - 2 strokes or fewer, penalties included, the fringe excluded; putts are strokes on the putting surface (a
  stroke from the fringe is not a putt); scrambling is par or better after a missed GIR, kept apart from sand
  saves (up and down from a greenside bunker); scoring average is raw strokes per completed round. Match-play
  and playoff holes are not rounds and are not in these statistics (matches stop when decided: no invented
  stroke totals for unplayed holes).
- **Kept for good**: each edition's counters go into the season file (`golf`), so they survive the live
  tables' pruning; the observer's statistics store sums them per golfer, season and tour (`agg`), and every
  season, career, tour or filtered figure is a sum of counts over a sum of opportunities -- never an average
  of averages (1/2 plus 8/10 is 9/12 = 75%). A zero denominator shows N/A. The store also keeps, per season,
  the longest drives and best event driving averages (top 100 per tour), every stroke-play winning margin and
  every match-play result.
- **Coverage**: every figure shows its sample (rounds, drives) and a profile shows "starts with recorded
  statistics / starts"; seasons played before this version show "not recorded" and are never estimated from
  ratings, scores or rankings. Qualifying stages are left out.
- **Verified** on a fresh world played across two season ends, a reload and a repeated advance request:
  counters reproduce each start's rounds and strokes, the store's sums equal the editions' counters start for
  start, the live season merges without double counting, and one request key plays one week
  (`tests.test_golf_stats`). Engine-level checks on 120 simulated rounds: one measured tee shot per par 4 / 5,
  GIR + scrambling chances = 18 holes, putts on GIR holes ≤ putts, scores by type add to 18.

### 3. World ranking points (rules `world-ranking`)
- The engine's scheme is now written down and versioned (world-ranking-1): points = 100 × ((prestige − 20) /
  80)^2.2 × the finish's share (1 for a win, 0.6 × (position − 1)^−0.73 to 60th); 104-week window, full weight
  for 13 weeks then a straight-line decline; average = weighted points / starts in the window, the divisor
  at least 40 and at most 52. The formula itself is unchanged (moved to `golfsim/prestige.py` so the engine and
  the observer use the same code).
- **Recorded**: each counted start's points (`points` in the edition; index schema 4: `starts.points`), each
  week's top 200 with average and counted starts (`ranking_points`), and the points seeded when the world began
  (`ranking_seed`, first season only).
- **Shown**: Rankings → *World: points by week* (any recorded week); each profile's *World ranking points*
  lists every counted start with its points, its age, the weight it carries now and what it counts. The
  recomputation equals the engine's average **exactly** for every ranked golfer at the live week and for every
  archived weekly snapshot checked (including seeded points and a season boundary). Ranking points are not
  prize money and not a lifetime sum.

### 4. Largest victories
- **Stroke play**: the winner's regulation strokes ahead of the next finisher, with the winning and next totals,
  **every** tied runner-up, the field size, age, course and date. A playoff winner's regulation margin is zero
  (the playoff shown apart). Lengths (72/54/36/18 holes) are kept apart, single-site editions only, qualifying
  excluded, filters for tour, majors and minimum field. Built from the recorded final totals, so it covers every
  archived season (no rerun, nothing rewritten).
- **Match play**: holes up and holes to play (7&6), "2 up", or won at an extra hole; scheduled length and the
  round; finals apart ("finals only"); never converted to strokes. Match results are recorded from this
  version on.

### 5. The five specific fixes (`tests.test_pretest_fixes`)
1. **Replay spoilers**: before the final round the replay shows no winner, final places or playoff, and a
   scorecard shows only the rounds revealed; the final round shows the result (and any playoff).
2. **Live record status**: a streak is "currently extending" only if every in-scope start this season (not yet
   archived) continued it; a partnership is current only if the pair is still together now.
3. **Starts drilldown**: a profile's starts exclude qualifying stages, and so does the list its links open;
   qualifying stages are a separate, labelled toggle.
4. **Restore**: the world is moved out of the trash before its marker is removed (a failed move -- a file held
   open on Windows -- leaves it listed and restorable); a removal that cannot write its marker puts the world back.
5. **No-index fallback**: per-golfer entries (team, route, prize) are looked up by integer or string id alike, so
   results without the index keep their coach, caddie and route; tested against the indexed results.

## Proposed for review (not rules of the world)
- **Qualification thresholds** (observer only, editable on the pages): Stats -- 20 recorded rounds for a season,
  100 all-time; event driving average -- 20 measured drives (about two rounds); season -- 200; career -- 1,000.
  Proposals, not real-world rules.
- **Strokes gained** is shown labelled as the engine's own expected-strokes table; it is not a validated
  real-world baseline and should not be used for cross-era claims until one is agreed.

## Staged next (approved, not in this increment)
The data contracts they need now exist (versioned per-edition counters, ranking inputs, stable person ids,
dated stints, as-of snapshots). In order, as observer-only updates that keep worlds resumable:
1. Saved table views and dependable navigation (named per-world views of columns, filters, sort, scope).
2. Where Are They Now (cohort explorer with Then / Now / as-of columns; retrospective views labelled).
3. My World (tagged shortlists and a "since last viewed" feed kept apart from the simulation clock).
4. Career comparisons (two to four golfers, same definitions and scopes, coverage shown).
5. GOAT Lab (whitelisted metrics and a safe expression builder; presets; contributions per golfer; missing
   coverage never treated as zero).
The immersion proposals (what is at stake before an event, record succession, breakthroughs, rivalries,
droughts, how a tournament unfolded) are for the owner to choose from; the last needs the round data now kept.

## Storage and speed (measured)
On the development machine (Intel Xeon 2.1 GHz, 4 logical CPUs, 15.7 GB; Python 3.13), full population, seed
2027, season 1 with 4 workers (`tools/benchmark_skip.py`), two runs of each engine, alternating order:

| | previous engine (5bcc6ed) | this engine |
|---|---|---|
| season-1 skip | 110.0 s, 106.7 s | 123.1 s, 116.3 s |
| of which simulate / save / publish | 103.2 / 3.1 / 2.2 s (first run) | 112.6 / 5.0 / 3.4 s (first run) |
| main process peak memory | 564 MB | 730 MB |
| season file (2027) | 4.4 MB | 10.4 MB |
| history index after season 1 | 16.7 MB | 17.1 MB |
| observer statistics store, one season | 4.1 MB, 1.5 s to build | 5.6 MB, 2.8 s to build |

So the capture costs about 10% of a season-1 skip here (about 11 s of 108 s), about 166 MB of peak memory and
about 6 MB of history per season (roughly 0.6 GB more over 100 seasons, before the index's own growth). On the
owner's laptop season 1 took 47.9 s before this increment; we have not measured it there. Season 100 was not
measured (no long run). Page times on that one-season world: every page under 0.5 s except the weekly ranking
view (1.0 s: it reads the season file); ranking reproduction checked exact for 600 golfer-weeks (weeks 5, 26,
52, top 200).

## Tests
The whole suite, one module per process with ResourceWarnings shown: 30 modules pass (no warnings); one
module (`test_history_consistency`) first failed because a profile now includes golf statistics, which read
"working out the statistics" until the background store is built -- the test now starts from a built store and
passes. New: `tests.test_golf_stats` (9) and `tests.test_pretest_fixes` (7).
