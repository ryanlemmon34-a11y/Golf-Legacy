# Diagnostic run provenance (pinned simulation checkout: 473690a, clean)

| Run | Segment | Started (UTC) | Ended | Seasons committed | How it ended |
|---|---|---|---|---|---|
| A seed 360013, 45 seasons, support on, workers 2 | 1 | 2026-10-31 03:57:28 | 04:27:4x | 2027-2033 (7) | Harness safeguard: season 2033 took 487 s > 420 s, caused by CPU contention from implementation agents (load ~6 on 4 CPUs); all reconciliations clean |
| B seed 2027, 10 seasons, support on, keep-after 4, workers 2 | 1 | 2026-10-31 03:57:28 | 04:28:0x | 2027-2033 (7) | Harness safeguard: season 2033 took 491 s > 420 s, same cause; all reconciliations clean; season-5 determinism digests recorded |
| C seed 2027, 10 seasons, support off, workers 2 | 1 | 2026-10-31 04:28:0x | | | started by the launch script after B ended (fresh world, not a restart) |

Resumed segments (HAL's instruction of 04:3x UTC: identical checkout 473690a, seed, support-on setting, committed
checkpoint and saved run state; --resume; the 420 s safeguard and external watchdog unchanged; at most two
diagnostic jobs at once; original processes confirmed gone and no implementation test or measurement running):
| B | 2 (resume) | 2026-10-31 04:34:11 | about 04:45 (the resume script then started A) | 2034-2036 (3 more; 10 committed in all) | resumed after season 2033 (the guard stops a run after the season that tripped it is committed); completed |
| A | 2 (resume) | 2026-10-31 04:45:47 | | from 2034 | (its end is the next row) |
| D seed 3031, 10 seasons, support on, workers 2 | 1 | 2026-10-31 05:03:04 | 05:39 (approx.) | 2027-2036 (10) | Completed; all reconciliations clean; started by the launch script after C (fresh world) |
| Replay of B season 5 (2031) | 1 | after D (launch script) | | 1 season | Completed, exit 0: identical in all 15 recorded parts (results, performance, rounds_and_holes, development, familiarity, finances, staff, fatigue_injuries, rankings, records, moments, history, cursor, diagnostics, published); the B copy world_2027_after4 was advanced in place as designed |
| A | 2 (resume) ended | 2026-10-31 04:45:47 | about 06:14-06:30 | 2034-2054 inclusive (21 more; 28 committed in all) | Ended when this session's worker process was restarted (a host-side restart during a usage-limit pause, not a safeguard): every process stopped mid-season 2055; nothing of 2055 was committed (checkpoint generation 28 = state 28 seasons, no pending season file); the dead process's lock (pid 28127) is taken over by the session's stale-lock rule |
| A | 3 (resume) | 2026-10-31 06:33:07 | | from 2055 | identical checkout 473690a (clean), seed 360013, support on, workers 2, --resume from committed generation 28; 420 s safeguard and watchdog unchanged |

Correction (2026-10-31 ~06:50 UTC, from review): the resume rows of A and B said "from 2033" and A's second segment
"2033-2054 (22 more)". Season 2033 was committed by the first segment (the guard stops a run after the season that
tripped it); the second segments began at 2034: A's covered 2034-2054 inclusive (21 seasons), B's 2034-2036 (3). The
uncorrected text is kept in PROVENANCE.before-correction-0650.md.
| A | 3 (resume) ended | 2026-10-31 06:33:07 | about 07:51 | 2055-2071 inclusive (17 more; 45 committed in all) | Completed: all 45 requested seasons; every season reconciled (errors 0+0), staff violations 0; no safeguard stop in this segment (slowest season 278 s); the population flag (+22% to +98% from the start) recorded each season, accounting reconciling |
