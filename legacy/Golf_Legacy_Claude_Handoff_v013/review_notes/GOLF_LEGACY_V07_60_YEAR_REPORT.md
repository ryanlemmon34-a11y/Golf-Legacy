# Golf Legacy v0.7: Two 60-year tests of national opens

**Source:** User-supplied and reviewed v0.6 engine, extended by `working/engine_v07.py` in a separate working copy. **Simulated years:** 2027–2086 inclusive. **Seeds:** 1217 and 2601.

## Why this experiment exists

We want a famous golfer to sometimes return to their home country's important open championship, even when the event belongs to a less prestigious professional circuit. Participation needs to be earned and financially feasible, not guaranteed, and the host country / rotating golf courses should accumulate permanent historical results.

National opens in this experiment **replace existing challenger/regional events**, and operate with the underlying tour's purse and point rules. Hosting courses are selected within the named country, favoring a different venue from the preceding edition. A small invitation lane (up to four golfers) allows home-country players from higher tours to accept an appearance even across a two-tier gap, if they are free that week and can fund the start. Lower-tier golfers still enter through the ordinary system. Important national opens preferentially occur in weeks without simultaneous premier/major events.

## Honest scale qualification

For runtime practicality, each world uses **450 active golfer slots and 25% of the normal circuit-event calendar**, with the four majors, 240 courses, hole-by-hole tournament scoring, pressure-sensitive pairings/cuts/playoffs, golfer development, and cash restrictions retained. This is not the same competitive environment as the full v0.6 1,700-active-golfer 100%-calendar tests. National opens represent about 20 of the ~49 scheduled events per year in these reduced runs, an intentionally high ratio that **overstresses** home-open attendance. Do not read the invitation and home-win rates as final calibration targets.

## Historical outcomes

| Metric | World 1217 | World 2601 |
|---|---:|---:|
| Tournament editions completed | 2,927 | 2,936 |
| Majors completed | 240 | 240 |
| Unique major champions | 109 | 109 |
| Most majors, one golfer | 16 | 14 |
| Average major champion age | 33.88 | 33.79 |
| Major victories by under-30 golfers | 49 | 50 |
| Major victories by 40+ golfers | 32 | 40 |
| Countries producing major winners | 24 | 22 |
| Explicit rare-prodigy flags | 0 | 0 |
| National open editions | 1,200 | 1,200 |
| Higher-tour hometown invitee starts | 2,639 | 2,553 |
| Returns by **already-established major champions** | 661 | 612 |
| Host-country champions of national opens | 167 | 147 |
| National opens won by higher-tour invitees | 132 | 102 |
| National opens won by a visitor with a previous major | 63 | 46 |
| Countries with national opens hosted at multiple courses | 28 / 28 | 28 / 28 |
| Individual competitive hole scores | 17,756,856 | 17,790,588 |
| Canceled/underfilled field warnings | 13 | 6 |
| Prize conservation errors | 0 | 0 |
| General export audit errors | 0 | 0 |
| Economics ledger audit errors | 0 | 0 |

**Combined:** 120 world-years, 5,863 completed tournament editions, 480 majors, 35,547,444 scored competitive holes, 2,400 national-open editions and 5,192 higher-tour hometown guest starts. A further **591,719 total funded tournament starts** were verified across the two cash ledgers.

## Emergent careers

**World 1217:** Marcus Brooks (Scotland) won 16 majors and 89 professional events *across all levels*; Chris Walker (Canada) won 10 majors; Peter Evans (Japan) and Peter Taylor (Canada) each won nine. Brooks accepted a hometown invitation to the Scotland National Open in 2064 while already holding ten majors and normally playing Tier 1; the host event was Tier 2. Kenya's Ethan Ito won his national open in 2032 and 2033 as an already established major champion, with different host courses in those two editions.

**World 2601:** Leo Carter (Sweden) won 14 majors and 60 events across levels, and Kai Carter (South Africa) won 11 majors. Leo Carter returned to the lower-tier Sweden National Open in both 2057 and 2058 having won 13 majors already. Not every returning star won their national championship, as intended.

These are retrospective descriptions of actual generated events, **not** diagnoses of why any golfer was successful or evidence that a national open caused talent growth.

## Country trajectories

In world 1217, Turkey's infrastructure index changed from 0.678 after the first simulated season to 1.850 after the 60th; Turkey produced 15 major victories. In world 2601, Thailand changed from 0.873 to 1.850 and produced ten majors. These are fictional development indices, not empirical measures of national participation or investment.

**Problem:** 10 of 28 countries in world 1217, and 9 of 28 in world 2601, reached the 1.85 infrastructure maximum (13 and 10 respectively reached at least 1.75). The inherited national-feedback system appears prone to **long-run saturation**, so we should revisit country-level investment, junior development, role models and mean reversion rather than treating all gains as plausible.

## Issues surfaced

1. **Multiple exceptional careers without rare-prodigy flags.** World 1217 had a 16-major winner and a ten-major winner; world 2601 had a 14-major winner and an 11-major winner. These are possible outcomes, but we cannot assume the tail frequency is correct. None of the two worlds generated a golfer flagged as an early-ready prodigy. At this small population, a zero count is unsurprising.
2. **Too many national opens relative to the scaled calendar.** These intentionally dense tests establish mechanical feasibility, not final prevalence. At full scale, expect a much lower fraction of national opens among all tournaments.
3. **Feeder-tour attendance warnings.** Thirteen and six events, primarily Africa Mini Circuit in early seasons, failed to attract a viable field. These are canceled/unplayed editions, not scoring-integrity violations. They reflect an undersized low-tier playing population at this test scale.
4. **Age realism still needs work.** Mean major winner age was nearly 34 in both worlds. Cohort-separated analysis and full-size tests are needed before tuning physical decline or forcing early retirement.
5. **Home identity is too simplistic.** A national-open affinity should eventually include birthplace, family, nationality, and regional/island affiliation, not only a single stored country string (important for Rory McIlroy and the Irish Open).
6. **Record book depth:** Venue rotation and current course records are persisted, but the engine does not yet preserve a dated log of every occasion a course record was broken. Keep that as a high-priority history feature.
7. **National-event prestige:** There is not yet a separate event prestige, purse, or ranking-points modifier beyond the host tour. This should be explicitly calibrated rather than silently boosted.
8. **Full-size tests are outstanding.** The experiment uses 450 active slots, not 1,700, and 25% of the regular event calendar. It cannot establish the normal long-run distribution of opportunities, finances, or prodigies at release scale.

## Next recommendation

Do not tune the scoring engine to force a desired number of 10- or 15-major champions. First normalize the number and schedule of national opens for the full circuit calendar, and create a country-affiliation system. Then run age/cohort and major-concentration diagnostics at wider scale, followed by a more careful national development model that doesn't saturate every successful country.

## Source files and reproduction

`working/engine_v07.py`, `working/test_v07.py`, and `README_V07.md` explain the implementation and how to rerun it. The archive includes final season summaries, historical event/results files, courses, country histories, annual golfer histories, and national-open attendance/winners. `general_audit.json` and `economics_audit.json` are independently computed from final exports; both report zero integrity errors for both worlds. Financial amounts and national development rules remain fictional assumptions.
