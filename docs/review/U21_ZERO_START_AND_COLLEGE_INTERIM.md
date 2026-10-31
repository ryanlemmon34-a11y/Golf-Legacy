> **INTERIM -- read-only diagnosis for review.** Pinned simulation build **473690a**, runs B, C and D; none of the
> overnight packages are in these worlds, so every conclusion is about that build and is **not evidence about the
> final feature world**. Nothing in the run folders was changed. Extract scripts and intermediate tables stay in the
> session scratch folder (`diag_u21/`), not in the repository. No simulation change is proposed here: the two
> candidate findings below are design questions for the owner and reviewer.

# Under-21 zero-start seasons and the college-starts decline (runs B, C, D; build 473690a)

Read-only diagnosis of the pinned runs `runs/{B,C,D}` (B seed 2027 support on, C seed 2027 support off, D seed 3031
support on; 10 seasons, 2027-2036) with the pinned build `build_473690a`. Nothing under the run folders was opened
for writing: the seed/debug `.json.gz` files and the season files named by each `archive/MANIFEST.json` were read
with `gzip.open(..., 'rt')`; no `World`/`Archive` object and no `index.sqlite` was opened. Extracts and the scripts
that made them are in this folder (`x*.py`, `*.pkl`, `tables_*.md`).

## Answers in brief

**Q1. Every tracked zero-start season is the same case, in all three runs.** B 9, C 17 (16 under 21, plus one
21-year-old ranked inside the top 300), D 12: 38 golfer-seasons, 37 of them under 21.

- **Who.** Full-time, non-college amateurs who had **no family money left at any season end** and **never held
  support**, in their **third season** (36 of 37 under-21 cases are aged 20; the other is aged 19 in his second
  season and was then blocked a second year). **None** is in an arrival season, none turned amateur late, none
  changed lifestyle in-season: all were full-time amateurs from their first week (week-1 "Arrived on the scene at 18"
  line, or the seeded 2027 world).
- **What the weekly ledger records.** Every one of the 52 weeks is either *could not afford any event*
  (18-52 weeks) or *no suitable event scheduled* (0-34 weeks: the off-season gap of their amateur series). There are
  **zero** weeks of injury, full field / not selected, not eligible, declined, trained or rested in any case
  (`zero_start_kind` = "kept out by barriers" for all 38). So in every week an event they were eligible for existed,
  the only recorded reason was money. By the ledger's own rules this is not ambiguous for any case.
- **Why money, mechanically.** Each started the season with cash between -$7,977 and -$7,662 after the previous
  season's spending, i.e. at most $338 of the $8,000 credit line left. The cheapest event they could enter costs
  $350 (tier-6 amateur event at home; $455 in their region, $630 abroad). A full-time amateur has **no living cost
  and no income of any kind** (`finance.weekly_living` returns (0, 0); amateurs take no prize money; weekly paid
  work is open only to full-time professionals, `season.py:2595`, `:2616`), so the cash figure **does not move for the
  whole season** (e.g. -$7,959 at the end of 2028 and of 2029 for B 6342). The work pathway that would end this
  starts at 21 (`work_pathway.MIN_AGE`), the support bands reach only amateurs ranked 1-150 or in the top-150 recent
  form (every B and D case was ranked 380-4,431 when its season began), and the winter "took a job" decision is a
  smooth age curve (p ≈ 0.07 at 19, ≈ 0.14 at 20) that does not see a season without a start.
- **A rule, not a coincidence.** "Started the season at the floor" (previous season-end cash ≤ -$7,650 and no
  family money left) predicts the zero-start seasons **exactly**: 9/9 in B, 16/16 in C, 12/12 in D, with **no**
  under-21 tracked season that started at the floor playing even once, and no zero-start season that did not start
  there.
- **Concentration.** Not in arrival seasons (0 of 919/919/937 arrival seasons). Entirely in season 3 / age 20
  (B 9/739 age-20 seasons, C 15/746, D 12/751; ages 18-19: 0, 1, 0). Region: mostly Europe (5, 10, 9 of 9, 16, 12),
  which is also the largest group and the most expensive one: European full-timers aged 18-19 spend about
  $8,100-8,250 a season against $5,700-7,500 elsewhere (17.3 events a season, more cross-border travel), so more of
  them end a season at the floor (38-57 such season-ends per run vs 0-29 in any other region).
- **Support on vs off.** Support reaches this group only when the golfer is ranked. The clearest difference: C (off)
  has 4 zero-start seasons by 3 golfers who were ranked inside the top 300 when the season began (C 11938 ranked 7 in
  2033 and 159 in 2034, C 1422 ranked 50, C 1014 ranked 243); B and D (on) have none (their cases began at 380-4,431).
  Without those, C has 13 against B's 9 and D's 12. Golfer ids identify the same
  person in B and C only for the seeded world and the 2028 arrivals (from the 2029 arrivals on the id registries
  diverge: 186-314 different people per arrival class share an id), so only 7 of C's 17 cases can be paired. Of
  those, 4 are zero-start in B too (unranked for support in either arm), 1 (8660) played a single event in B (it
  started 2030 $71 above the floor, enough for one home trip), and 2 (1014, aged 20; 1422, aged 21) held Band C support
  in B, drew $5,000 each season and played 15-19 events. So **support prevented 2 of the 7 pairable C cases**; the
  rest of the 9-vs-16 difference involves different people and is consistent with arrival-cohort noise (D, support on,
  has 12).

**Q2. The college-starts decline (24.4 → 18.8, B) is crowding of the amateur (tier-6) series, not college
capacity and not a growing college population.** The figure is the "Events per amateur" table of the support
section (`diagnostic_report.support`, the `college` row: mean `events` of every amateur with `in_college`).
College golfers are flat (1,052 → 1,055; peak 1,116). Their **college (tier-5) starts are constant**, 10.5 → 11.0 each
(135 college events a season, 120 regular events with 10,560 places, already 94 % full in 2027 and 99-100 % from 2030).
All of the decline is in **tier-6 amateur starts, 13.4 → 7.5 each**. Those fields are a fixed calendar (394-397
regular events, about 54,900 places with the 1.5× open-amateur expansion) that series *members* enter ahead of college
golfers (priority class 10 vs 12, `season.priority`), and the members multiplied: part-time non-college amateurs
went from 1,185 to 3,340, mostly professionals reinstated as amateurs ("back to amateur", 1,917 in B), plus college
graduates (889) and full-timers taking jobs (619), against 1,270 leaving. North America, where the US colleges play
their amateur golf, saturated first: its 102 events were all filled to the expanded cap from 2034, and college
entries there fell from 6,260 to 670 a season. College golfers' "shut out: every acceptable field full" weeks
doubled (8.2 → 16.2 a season). C and D are the same to a decimal. So this is **a fixed capacity under an access rule
(members first), driven by a growing member population**.

**Q3. Scope.** These are pinned 473690a worlds (none of the newer packages); every conclusion is about that
build. See "Limitations".

## How the rules produce the zero-start seasons (build 473690a)

| Rule | Where | Effect on a full-time non-college amateur |
|---|---|---|
| No living cost, no salary | `finance.weekly_living` (l. 197-203): "college golfers and teenagers living at home" pay (0, 0) for any non-pro full-timer | Cash moves only by event costs (and support, if held) |
| No income | amateurs take no prize money (`finance` header); weekly paid work only for `status == 'pro' and lifestyle == 'full_time'` (`season.py:2595`; fallback plan `:2616` is "train" for everyone else) | Nothing can raise cash in-season |
| Credit | `funds = cash + backing + backer_funds + credit_limit(last season's earned income)`; for an amateur `credit_limit(0) = $8,000` (`finance.py:162-175`, `season.py:2735-2739`) | Spendable = cash + $8,000 (+ support left) |
| Cheapest trip | `EVENT_COST[6] = 350` × travel 1.0 home / 1.3 region / 1.8 abroad (`finance.py:86-87`) | Below -$7,650 nothing is affordable |
| Weekly reason | `record_access`: eligible events exist, none affordable → "could not afford any event"; no event → "no suitable event scheduled" | The ledger the tables below count |
| Work pathway | `work_pathway.MIN_AGE = 21` (l. 35, checked l. 52); the blocked count is still kept under 21 and carries over the year end | At 21 it fires at the first monthly plan (week 1) with counts of 19-72 |
| Winter job decision | `careers.p_amateur_job`: `sig(-1.2 + 0.8(age-22) - 0.4 min(runway,5) + 1[cash<0])` (l. 309-316); no term for starts or blocked weeks | p = 0.069 at 19, 0.14 at 20 (as recorded in the transitions) |
| Support | `amateur_support`: Band C needs amateur rank 1-150 or top-150 26-week form | Ranks 650-4,600: out of reach by design |
| College | `population._college_or_series` (l. 360-367): a one-time draw at arrival (overall ≥ 30, then USA always / elsewhere nation pathway odds); no capacity limit, no later entry | None of the 38 ever had a college place; college is not a capacity question here |

A junior arrives with $5,000-25,000 (`initial_cash`) and family money in about 60 % of draws. One without family
money and with a low draw spends about $6,000-8,000 a season (16-17 events) and reaches the floor at the end of
season 2 (age 19); season 3 (age 20) is then a zero-start season, and the pathway takes them in week 1 of the season
they turn 21. Those with a little more money reach the floor during their age-20 season (B 74, C 86, D 77 age-20
seasons ended at the floor) and are taken by the pathway at 21 after eight blocked weeks: they are blocked-8+
seasons with starts, not zero-start seasons (the report's "under 21 / Blocked 8+" column: 53, 71, 60).

Every under-19/20 season that ended at the floor is accounted for: B 14 at 19 → 9 zero-start next season, 1 took
a job that winter (p = 0.069), 4 are in 2036 (no next season); C 21 → 15 zero-start (one of them Thomas Turner's
second blocked season), 1 job, 5 in 2036, plus Turner's floor at 18 → zero-start at 19; D 14 → 12 zero-start, 2 in 2036.

## Q1: every case

All amounts in dollars. "Cash at start" is the previous season's end (it is also the end of the zero-start season:
no ledger line moved). "Longest blocked count" is the work-pathway count (`cash_blocked_max`), which carries across
the year end. "Overall" is hidden (debug file), for context only.

### Run B: 9 tracked zero-start seasons

| Run | Season | gid | Golfer | Nation | Region | Age | Arrival | Am. rank start→end | Support band / drawn | Family money left | Cash at start (prev. end) | Spendable at start (cash + $8,000 credit) | Longest blocked count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B | 2029 | 6342 | Padraig Walsh | Ireland | Europe | 20 | seeded 2027, season 3 | 2681→2992 | none / $0 | no | $-7,959 | $41 | 38 |
| B | 2030 | 8590 | Rui Ito | Japan | Asia | 20 | arrived 2028, season 3 | 2310→2632 | none / $0 | no | $-7,795 | $205 | 43 |
| B | 2030 | 8596 | Colby Holloway | Canada | North America | 20 | arrived 2028, season 3 | 2865→3363 | none / $0 | no | $-7,863 | $137 | 72 |
| B | 2030 | 8597 | Håkon Mathisen | Norway | Europe | 20 | arrived 2028, season 3 | 2268→2697 | none / $0 | no | $-7,731 | $269 | 51 |
| B | 2033 | 11118 | Kristian Danielsen | Denmark | Europe | 20 | arrived 2031, season 3 | 939→1736 | none / $0 | no | $-7,911 | $89 | 40 |
| B | 2035 | 12889 | Stephen Sibanda | Zimbabwe | Africa | 20 | arrived 2033, season 3 | 380→812 | none / $0 | no | $-7,843 | $157 | 19 |
| B | 2035 | 13013 | Jelle de Wit | Belgium | Europe | 20 | arrived 2033, season 3 | 2274→3382 | none / $0 | no | $-7,747 | $253 | 44 |
| B | 2036 | 13714 | Tomohiro Shibata | Japan | Asia | 20 | arrived 2034, season 3 | 2730→3508 | none / $0 | no | $-7,742 | $258 | 46 |
| B | 2036 | 13874 | Reece Ramsden | England | Europe | 20 | arrived 2034, season 3 | 4431→4618 | none / $0 | no | $-7,951 | $49 | 41 |

Week-by-week reasons recorded that season (52 weeks each), with the season before and after:

| Run | Season | gid | Could not afford any event | No suitable event scheduled | Any other reason (weeks) | Injury weeks | Their amateur series that season | Season before | Overall (season end, hidden) | What happened next |
|---|---|---|---|---|---|---|---|---|---|---|
| B | 2029 | 6342 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 16 ev, 1 unaff wk, costs $7,070 | 30.7 | took work by the pathway, week 1 2030 at 21 (count 38); 6 events as part-time |
| B | 2030 | 8590 | 43 | 9 | 0 | 0 | AM_ASIA: 107 events in 44 wks | 16 ev, 0 unaff wk, costs $6,440 | 44.9 | took work by the pathway, week 1 2031 at 21 (count 43); 11 events as part-time |
| B | 2030 | 8596 | 52 | 0 | 0 | 0 | AM_NORTH_AMERICA: 103 events in 52 wks | 12 ev, 20 unaff wk, costs $5,570 | 44.2 | took work by the pathway, week 1 2031 at 21 (count 72); 11 events as part-time |
| B | 2030 | 8597 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 11 ev, 14 unaff wk, costs $4,690 | 44.4 | took work by the pathway, week 1 2031 at 21 (count 51); 5 events as part-time |
| B | 2033 | 11118 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 14 ev, 3 unaff wk, costs $6,265 | 60.2 | took work by the pathway, week 1 2034 at 21 (count 40); 5 events as part-time |
| B | 2035 | 12889 | 18 | 34 | 0 | 0 | AM_AFRICA: 32 events in 19 wks | 15 ev, 1 unaff wk, costs $8,065 | 56.4 | took work by the pathway, week 1 2036 at 21 (count 19); 7 events as part-time |
| B | 2035 | 13013 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 13 ev, 7 unaff wk, costs $5,495 | 44.4 | took work by the pathway, week 1 2036 at 21 (count 44); 5 events as part-time |
| B | 2036 | 13714 | 43 | 9 | 0 | 0 | AM_ASIA: 107 events in 44 wks | 15 ev, 3 unaff wk, costs $6,090 | 55.0 | run ended (2036 is the last season) |
| B | 2036 | 13874 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 12 ev, 7 unaff wk, costs $5,355 | 35.3 | run ended (2036 is the last season) |

### Run C: 17 tracked zero-start seasons

| Run | Season | gid | Golfer | Nation | Region | Age | Arrival | Am. rank start→end | Support band / drawn | Family money left | Cash at start (prev. end) | Spendable at start (cash + $8,000 credit) | Longest blocked count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C | 2029 | 1014 | Nathan Garside | England | Europe | 20 | seeded 2027, season 3 | 243→656 | none / $0 | no | $-7,831 | $169 | 51 |
| C | 2029 | 1422 | Sergio Etxeberria | Spain | Europe | 21 | seeded 2027, season 3 | 50→172 | none / $0 | no | $-7,830 | $170 | 40 |
| C | 2029 | 6342 | Padraig Walsh | Ireland | Europe | 20 | seeded 2027, season 3 | 2464→2913 | none / $0 | no | $-7,959 | $41 | 38 |
| C | 2030 | 8590 | Rui Ito | Japan | Asia | 20 | arrived 2028, season 3 | 2622→3115 | none / $0 | no | $-7,690 | $310 | 46 |
| C | 2030 | 8596 | Colby Holloway | Canada | North America | 20 | arrived 2028, season 3 | 2500→2876 | none / $0 | no | $-7,963 | $37 | 56 |
| C | 2030 | 8597 | Håkon Mathisen | Norway | Europe | 20 | arrived 2028, season 3 | 2395→2809 | none / $0 | no | $-7,941 | $59 | 51 |
| C | 2030 | 8660 | Kasper Kofoed | Denmark | Europe | 20 | arrived 2028, season 3 | 2692→3138 | none / $0 | no | $-7,789 | $211 | 40 |
| C | 2032 | 10477 | Kota Shimizu | Japan | Asia | 20 | arrived 2030, season 3 | 3695→3959 | none / $0 | no | $-7,682 | $318 | 46 |
| C | 2033 | 11142 | Lewis Dunbar | Northern Ireland | Europe | 20 | arrived 2031, season 3 | 1735→2695 | none / $0 | no | $-7,884 | $116 | 40 |
| C | 2033 | 11938 | Thomas Turner | South Africa | Africa | 19 | arrived 2032, season 2 | 7→159 | none / $0 | no | $-7,960 | $40 | 46 |
| C | 2034 | 11938 | Thomas Turner | South Africa | Africa | 20 | arrived 2032, season 3 | 159→unr. | none / $0 | no | $-7,960 | $40 | 64 |
| C | 2034 | 11970 | Guido Costa | Italy | Europe | 20 | arrived 2032, season 3 | 650→1138 | none / $0 | no | $-7,771 | $229 | 40 |
| C | 2035 | 12849 | Samuel Chege | Zimbabwe | Africa | 20 | arrived 2033, season 3 | 857→3194 | none / $0 | no | $-7,943 | $57 | 24 |
| C | 2035 | 12973 | Maarten de Graaf | Belgium | Europe | 20 | arrived 2033, season 3 | 2654→3451 | none / $0 | no | $-7,712 | $288 | 44 |
| C | 2036 | 13615 | Callum Spencer | England | Europe | 20 | arrived 2034, season 3 | 1986→3375 | none / $0 | no | $-7,915 | $85 | 44 |
| C | 2036 | 13773 | Floris Jansen | Netherlands | Europe | 20 | arrived 2034, season 3 | 3445→4341 | none / $0 | no | $-7,931 | $69 | 37 |
| C | 2036 | 13855 | Hugo Mills | England | Europe | 20 | arrived 2034, season 3 | 4281→4561 | none / $0 | no | $-7,951 | $49 | 41 |

Week-by-week reasons recorded that season (52 weeks each), with the season before and after:

| Run | Season | gid | Could not afford any event | No suitable event scheduled | Any other reason (weeks) | Injury weeks | Their amateur series that season | Season before | Overall (season end, hidden) | What happened next |
|---|---|---|---|---|---|---|---|---|---|---|
| C | 2029 | 1014 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 12 ev, 14 unaff wk, costs $5,690 | 69.1 | took work by the pathway, week 1 2030 at 21 (count 51); 14 events as part-time |
| C | 2029 | 1422 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 12 ev, 3 unaff wk, costs $6,665 | 70.1 | took work by the pathway, week 13 2030 at 22 (count 45); 5 events as part-time |
| C | 2029 | 6342 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 16 ev, 1 unaff wk, costs $7,070 | 30.9 | took work by the pathway, week 1 2030 at 21 (count 38); 6 events as part-time |
| C | 2030 | 8590 | 43 | 9 | 0 | 0 | AM_ASIA: 107 events in 44 wks | 15 ev, 3 unaff wk, costs $5,775 | 44.7 | took work by the pathway, week 1 2031 at 21 (count 46); 11 events as part-time |
| C | 2030 | 8596 | 52 | 0 | 0 | 0 | AM_NORTH_AMERICA: 103 events in 52 wks | 16 ev, 4 unaff wk, costs $6,230 | 44.4 | took work by the pathway, week 1 2031 at 21 (count 56); 11 events as part-time |
| C | 2030 | 8597 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 11 ev, 16 unaff wk, costs $4,900 | 44.1 | took work by the pathway, week 1 2031 at 21 (count 51); 5 events as part-time |
| C | 2030 | 8660 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 14 ev, 3 unaff wk, costs $6,265 | 31.7 | took work by the pathway, week 1 2031 at 21 (count 40); 5 events as part-time |
| C | 2032 | 10477 | 43 | 9 | 0 | 0 | AM_ASIA: 107 events in 44 wks | 14 ev, 3 unaff wk, costs $5,740 | 32.2 | took work by the pathway, week 1 2033 at 21 (count 46); 10 events as part-time |
| C | 2033 | 11142 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 15 ev, 3 unaff wk, costs $6,615 | 52.6 | took work by the pathway, week 1 2034 at 21 (count 40); 5 events as part-time |
| C | 2033 | 11938 | 32 | 20 | 0 | 0 | AM_AFRICA: 32 events in 19 wks | 11 ev, 14 unaff wk, costs $13,690 | 68.6 | still full-time, no start again in 2034 (age 20) |
| C | 2034 | 11938 | 18 | 34 | 0 | 0 | AM_AFRICA: 33 events in 19 wks | 0 ev, 32 unaff wk, costs $0 | 69.4 | took work by the pathway, week 1 2035 at 21 (count 64); 10 events as part-time |
| C | 2034 | 11970 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 14 ev, 3 unaff wk, costs $6,160 | 66.4 | took work by the pathway, week 1 2035 at 21 (count 40); 5 events as part-time |
| C | 2035 | 12849 | 18 | 34 | 0 | 0 | AM_AFRICA: 33 events in 19 wks | 10 ev, 7 unaff wk, costs $5,580 | 56.3 | took work by the pathway, week 1 2036 at 21 (count 24); 6 events as part-time |
| C | 2035 | 12973 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 13 ev, 7 unaff wk, costs $5,705 | 45.6 | winter: amateur took a job at 20 (p=0.138); next season part_time, 5 events |
| C | 2036 | 13615 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 13 ev, 7 unaff wk, costs $5,915 | 61.2 | winter: amateur took a job at 20 (p=0.1407); run ended (2036 is the last season) |
| C | 2036 | 13773 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 17 ev, 0 unaff wk, costs $7,420 | 45.3 | winter: amateur took a job at 20 (p=0.1409); run ended (2036 is the last season) |
| C | 2036 | 13855 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 13 ev, 5 unaff wk, costs $5,810 | 35.0 | run ended (2036 is the last season) |

### Run D: 12 tracked zero-start seasons

| Run | Season | gid | Golfer | Nation | Region | Age | Arrival | Am. rank start→end | Support band / drawn | Family money left | Cash at start (prev. end) | Spendable at start (cash + $8,000 credit) | Longest blocked count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D | 2029 | 4335 | Alessandro Mariani | Italy | Europe | 20 | seeded 2027, season 3 | 1455→2051 | none / $0 | no | $-7,707 | $293 | 37 |
| D | 2029 | 6077 | Rui Song | China | Asia | 20 | seeded 2027, season 3 | 2396→2959 | none / $0 | no | $-7,714 | $286 | 49 |
| D | 2030 | 8525 | Gabriel Johnson | South Africa | Africa | 20 | arrived 2028, season 3 | 750→2656 | none / $0 | no | $-7,920 | $80 | 25 |
| D | 2033 | 11131 | Struan Wallace | Scotland | Europe | 20 | arrived 2031, season 3 | 2702→3453 | none / $0 | no | $-7,852 | $148 | 37 |
| D | 2033 | 11291 | Leo Mottram | England | Europe | 20 | arrived 2031, season 3 | 3261→3446 | none / $0 | no | $-7,662 | $338 | 44 |
| D | 2034 | 12077 | Jamie Yardley | England | Europe | 20 | arrived 2032, season 3 | 2894→3337 | none / $0 | no | $-7,848 | $152 | 40 |
| D | 2035 | 12709 | Callum Llewellyn | England | Europe | 20 | arrived 2033, season 3 | 1577→2422 | none / $0 | no | $-7,977 | $23 | 38 |
| D | 2035 | 12734 | Stuart Galbraith | Scotland | Europe | 20 | arrived 2033, season 3 | 1573→2374 | none / $0 | no | $-7,702 | $298 | 40 |
| D | 2035 | 12835 | Ki-hoon Jeon | South Korea | Asia | 20 | arrived 2033, season 3 | 2198→2936 | none / $0 | no | $-7,913 | $87 | 46 |
| D | 2035 | 12944 | Eirik Berge | Norway | Europe | 20 | arrived 2033, season 3 | 3772→4035 | none / $0 | no | $-7,892 | $108 | 38 |
| D | 2035 | 12947 | Jamie Fenwick | England | Europe | 20 | arrived 2033, season 3 | 3936→4427 | none / $0 | no | $-7,915 | $85 | 41 |
| D | 2036 | 13599 | Tristan Parker | England | Europe | 20 | arrived 2034, season 3 | 2694→3856 | none / $0 | no | $-7,759 | $241 | 40 |

Week-by-week reasons recorded that season (52 weeks each), with the season before and after:

| Run | Season | gid | Could not afford any event | No suitable event scheduled | Any other reason (weeks) | Injury weeks | Their amateur series that season | Season before | Overall (season end, hidden) | What happened next |
|---|---|---|---|---|---|---|---|---|---|---|
| D | 2029 | 4335 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 17 ev, 0 unaff wk, costs $7,525 | 53.4 | took work by the pathway, week 1 2030 at 21 (count 37); 5 events as part-time |
| D | 2029 | 6077 | 43 | 9 | 0 | 0 | AM_ASIA: 107 events in 44 wks | 14 ev, 6 unaff wk, costs $5,740 | 37.3 | winter: amateur took a job at 20 (p=0.1382); next season part_time, 9 events |
| D | 2030 | 8525 | 18 | 34 | 0 | 0 | AM_AFRICA: 32 events in 19 wks | 10 ev, 7 unaff wk, costs $5,475 | 55.5 | took work by the pathway, week 1 2031 at 21 (count 25); 8 events as part-time |
| D | 2033 | 11131 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 17 ev, 0 unaff wk, costs $7,210 | 56.4 | winter: amateur took a job at 20 (p=0.1399); next season part_time, 8 events |
| D | 2033 | 11291 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 14 ev, 7 unaff wk, costs $6,160 | 34.7 | winter: amateur took a job at 20 (p=0.1372); next season part_time, 9 events |
| D | 2034 | 12077 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 15 ev, 3 unaff wk, costs $6,615 | 48.5 | took work by the pathway, week 1 2035 at 21 (count 40); 9 events as part-time |
| D | 2035 | 12709 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 16 ev, 1 unaff wk, costs $7,175 | 59.7 | took work by the pathway, week 1 2036 at 21 (count 38); 9 events as part-time |
| D | 2035 | 12734 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 15 ev, 3 unaff wk, costs $6,405 | 59.7 | took work by the pathway, week 1 2036 at 21 (count 40); 9 events as part-time |
| D | 2035 | 12835 | 43 | 9 | 0 | 0 | AM_ASIA: 107 events in 44 wks | 15 ev, 3 unaff wk, costs $6,615 | 56.1 | winter: amateur took a job at 20 (p=0.1407); next season part_time, 11 events |
| D | 2035 | 12944 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 15 ev, 1 unaff wk, costs $6,720 | 34.2 | took work by the pathway, week 1 2036 at 21 (count 38); 5 events as part-time |
| D | 2035 | 12947 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 14 ev, 5 unaff wk, costs $6,160 | 34.6 | took work by the pathway, week 1 2036 at 21 (count 41); 9 events as part-time |
| D | 2036 | 13599 | 37 | 15 | 0 | 0 | AM_EUROPE: 115 events in 37 wks | 15 ev, 3 unaff wk, costs $6,720 | 55.8 | run ended (2036 is the last season) |


### Classification

| | B | C | D |
|---|---|---|---|
| Tracked zero-start seasons | 9 | 17 | 12 |
| Under 21 | 9 | 16 | 12 |
| Money the only reason in every week with an eligible event (unaffordable + calendar gap, nothing else) | 9 | 17 | 12 |
| …of which every week unaffordable (no calendar gap: North American series, events all 52 weeks) | 1 | 1 | 0 |
| Any injured, full-field/lineup, not-eligible or choice week | 0 | 0 | 0 |
| Started the season at the floor (cash ≤ -$7,650, no family money, no support) | 9 | 17 | 12 |
| Arrival season | 0 | 0 | 0 |
| Ranked inside the top 300 when the season began | 0 | 4 (3 golfers) | 0 |
| Next: work pathway at 21, week 1 of the next season | 7 | 11 | 7 |
| Next: winter "took a job" at 20 (p ≈ 0.14; two of C's in the 2036 winter) | 0 | 3 | 4 |
| Next: still blocked the next season (C 11938, aged 19 → 20) | 0 | 1 | 0 |
| Next: work pathway at 22, week 13 (C 1422: inside the top 300 until then) | 0 | 1 | 0 |
| Next: 2036 case with no winter change (no next season recorded) | 2 | 1 | 1 |

What the ledger cannot say: an "unaffordable" week never tested admission (they could not enter, so no field was
tried). Their earlier seasons show some full fields in the same series (Asia 5-9 shut-out weeks a season, North
America 5-6, Europe 0-3), so in a world where they could pay, some of those weeks might have been full instead; but
with 18-52 eligible weeks each and the series filled to cap in only part of its events, the conclusion that money,
not capacity, kept them out all season stands for every case. No case is genuinely ambiguous between money and
injury, eligibility or choice; the C 1422 case (21, ranked 50 → 172) is the only one where a pathway exclusion other
than age (the top-300 ranking) applied.

Calendar: their series held 115 events in 37 weeks (Europe), 107 in 44 (Asia), 103 in 52 (North America) and 32-33
in 19 (Africa) in each zero-start season, which matches the "no suitable event" weeks (15, 9, 0; Africa 34, with
national and continental events in some weeks outside the series).

## Q1: denominators and concentration

Tracked = season-end full-time, non-college amateur (v[1] == 'full_time' and not v[2]); under 21 = v[0] < 21;
zero-start = v[4] == 0. "Season" counts from arrival (seeded golfers: from 2027, so a seeded 19- or 20-year-old is in
"season 1" in 2027).

| Run | Under-21 tracked seasons | Zero-start | Age 18 | Age 19 | Age 20 | Arrival season (1) | Season 2 | Season 3 | Started the season at the floor (prev. cash ≤ -$7,650, no family money) | …of which zero-start | Zero-start NOT at the floor |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B | 2271 | 9 | 0/774 | 0/758 | 9/739 | 0/919 | 0/757 | 9/595 | 9 | 9 | 0 |
| C | 2280 | 16 | 0/774 | 1/760 | 15/746 | 0/919 | 1/760 | 15/601 | 16 | 16 | 0 |
| D | 2282 | 12 | 0/769 | 0/762 | 12/751 | 0/937 | 0/759 | 12/586 | 12 | 12 | 0 |

| Run | Europe | Asia | North America | Africa | Oceania | Latin America | Middle East |
|---|---|---|---|---|---|---|---|
| B | 5/816 | 2/668 | 1/362 | 1/167 | 0/151 | 0/96 | 0/11 |
| C | 10/818 | 2/668 | 1/366 | 3/168 | 0/156 | 0/92 | 0/12 |
| D | 9/924 | 2/623 | 0/340 | 1/140 | 0/157 | 0/89 | 0/9 |

Reading the denominators:

- **Ages / seasons.** Zero-start rates are 0 % at 18, 0-0.13 % at 19 and 1.2-2.0 % at 20 (9/739, 15/746, 12/751).
  Arrival seasons: 0 of 919, 919 and 937. Every case is in season 3 except C 11938 (season 2, then season 3 too).
  This follows from the arithmetic above, not from an age rule acting at 20: the floor is reached after two
  seasons of spending for the low-cash, no-family-money arrivals, and the work pathway's age gate (21) is what makes
  the third season a whole lost season instead of eight weeks.
- **Regions.** Europe 5/816, 10/818, 9/924 (0.6-1.2 %); Asia 2/668, 2/668, 2/623 (0.3 %); North America 1/362, 1/366,
  0/340; Africa 1/167, 3/168, 1/140 (0.6-1.8 %, small numbers); none in Oceania, Latin America or the Middle East.
  Europe's excess matches its higher spending per season (see above); Latin America's under-19 amateurs play about 12
  events a season and almost never reach the floor (0-1 per run).
- **Family money / support.** All 38 cases had no family money at every season end they were recorded, and none ever
  held support (C: none exists).
- **Who in the age-20 cohort ends up at zero.** Not the weakest golfers: hidden Overall at season end ranges 30.7 to
  70.1 (C 1014 69.1, C 11938 69.4, C 1422 70.1). Money decides it, not ability.

## Q1: B against C (the support comparison)

- From the 2029 arrival class on, the same gid is a **different person** in B and C (same identity by name, nation and
  birth year: 2,854 of the seeded amateurs and all 323 of the 2028 arrivals; then only 25-46 per arrival class,
  against 186-314 different). The reports' paired cohort (amateurs ranked 1-150 at the end of 2027) is unaffected; any
  per-golfer B-vs-C comparison of a later arrival is not valid.
- Pairable C cases (seeded or 2028 arrivals): 1014, 1422, 6342, 8590, 8596, 8597, 8660.
  - 6342, 8590, 8596, 8597: zero-start in both arms, same mechanism, near-identical cash (ranked 2,268-2,865: no
    support in B either).
  - 8660: B played 1 event in 2030 (began at -$7,579, $421 spendable, one home trip, then -$7,929 and blocked).
  - 1014 (C, age 20 in 2029): in B held Band C each season 2027-2029, drew $5,000 each season, played 19/16/16 events
    and ended 2029 at -$756.
  - 1422 (C, age 21 in 2029, ranked 50 at the start): in B held Band C in 2027 and 2029, played 17/18/15 events.
- So, where it can be measured, support turned 2 zero-start seasons into normal ones, both for ranked golfers. The
  other differences between 9 (B), 16-17 (C) and 12 (D) are between different arrivals and need no support effect to
  explain them; C's four ranked cases are the support-sensitive part.

## Candidate defects and gaps (evidence only; no code change proposed)

1. **Under-21 full-time amateurs at the credit floor are frozen for whole seasons.** Evidence: 37 of 37 under-21
   zero-start seasons started at cash ≤ -$7,650 with no family money, 0 of those that started there played, and the
   cash figure is identical at both ends of the zero-start season (no living cost, no income, no work for amateurs,
   pathway from 21, support for ranked amateurs only, winter job odds 7-14 % that ignore the lost season). The
   pathway docstring says the under-21 group is left out on purpose and measured; what is not stated anywhere is that
   leaving it out means a guaranteed full season (sometimes two: C 11938) with no starts and no change of state. Whether
   that is intended is an owner decision. Evidence that would separate "intended" from "gap": (a) the rules text for
   teenagers living at home (whether family is meant to cover any trip), (b) whether any under-21 route to work or to
   part-time golf was meant to exist besides the winter decision, (c) a count of age-19/20 floor season-ends against
   later outcomes in run A (45 seasons) once it finishes.
2. **Ranked amateurs at the floor without support (C only).** C 1422 (ranked 50 at the start of 2029) was excluded from
   the pathway by the top-300 rule while unable to afford a trip all season; the ranking decayed (172 at the end) and
   the pathway took him at 22 in week 13 of 2030. C 11938 (ranked 7 at 18) reached the floor in his arrival season (11
   events, -$7,960) and lost two seasons. With support on these are covered (Band A-C), so this matters only for
   support-off worlds.
3. **Report tool -- checked, not a defect of the current tool.** The pinned build's copy of
   `tools/diagnostic_report.py` (473690a) read `archive/years/<year>.json.gz`; manifest archives name the files
   `years/<year>.g<generation>.json.gz`, so that copy's `Run.season()` returned `{}`. The report tool used for the
   published reports (branch build/v16-report, since a11f29a) resolves season files through the archive manifest;
   checked: `Run('B', runs/B, 2027).season(2030)` returns the full season record (23 keys).
4. Not a defect, for clarity: the seed rows show `train_wk` 52 for the zero-start seasons while the access ledger says
   "could not afford any event"; this is the designed split (activity = what they did; access = why they did not play).

## Q2: the college-starts decline

**Where the figure comes from.** `tools/diagnostic_report.py`, `support()` → "Events per amateur and seasons without a
start", row `college`: for every amateur with `in_college` (v[2]) the season's `events` (v[4]), averaged. In B it
falls 24.4 (2027) → 18.8 (2036); C 24.5 → 18.6; D 24.4 → 18.9 (computed here from the same tuples). Splitting each
college golfer's starts by event tier (from every archived edition's field):

- **College (tier-5) starts are flat**: B 10.5 → 11.0 each, C 10.5 → 11.0, D 10.6 → 10.8. The college calendar is fixed
  (135 events every season: 120 regular, 15 post-season), regular college places are fixed (10,560) and already
  94 % filled in 2027, 99-100 % from 2030. College golfers per season are flat too (B 1,042-1,116; 1,052 in 2027 and
  1,055 in 2036). College is a fixed draw at arrival from a fixed-size junior class, so college numbers do not grow
  with the world. Capacity in college events is binding but constant; it explains no decline.
- **Amateur (tier-6) starts fall**: B 13.4 → 7.5 each (C 13.5 → 7.3, D 13.3 → 7.8). That is the whole decline
  (24.4 - 18.8 = 5.6 ≈ 13.4 - 7.5 = 5.9, with other starts 0.5 → 0.3 and college starts +0.5).
- **Why**: the regular tier-6 calendar is fixed (394-397 events, about 54,900 places at 1.5 × field for open-amateur
  events, `season.py:213`, `:920`) while the non-college amateurs entering it double: B 16,152 → 32,075 entries (part-time
  non-college amateurs 1,185 → 3,340; full-time 378 → 375). Series members (`g.tour == s.tour`) sort ahead of college
  golfers (lower tier membership: class 10 against class 12, `season.priority` l. 654-659); the "fewest starts first"
  rotation (l. 672) works only within a class. So college golfers get only the places members leave. Overall the
  tier-6 fields are 52 % → 71 % full, but North America (where US college golfers play their amateur golf) is
  saturated: B 69 of 101 events full at the expanded cap in 2027, all 102 from 2034, and college entries there fall
  6,260 → 670 a season while non-college entries rise 5,570 → 14,018. US college golfers lose most (Small College
  24.6 → 16.2, Division I 24.9 → 18.2) and international university golfers least (23.7 → 20.8).
- **Access ledger of college golfers** (weeks per golfer per season, B): "shut out: every acceptable field full"
  8.2 → 16.2; "not selected for the college lineup" 2.1 → 4.0 (more weeks in which a college event was their first
  choice and the lineup was full); "could not afford any event" 0.0 → 2.1 (tier-6 trips are theirs to pay; only college
  events are school-paid); choices (declined/trained/rested) 14.1 → 7.2 — they are not choosing to play less.
- **Where the extra members come from** (B, new part-time non-college amateurs 2028-2036): professionals reinstated as
  amateurs ("back to amateur") 1,917, college graduates ("college to amateur") 889, full-time amateurs taking a job
  (winter decision or work pathway) 619; leaving: 1,270 (retired/exit only; 0-2 turned pro). C and D: 1,871/1,846
  reinstated, 909/861 graduates, 631/653 from full-time, 1,255/1,298 leaving.

**Interpretation.** A capacity limit (fixed amateur-series calendar and fields) combined with an access rule (members
before college visitors), driven not by "population growth" in general but by the accumulation of part-time
amateurs, most of them reinstated professionals. Support does not change it (B and C agree to 0.1-0.3 events per
season). Evidence that would test this further: the same split in run A (does college tier-6 access keep falling,
or level off when part-time amateur exits catch up?), and the North American series' entry queue (who was ahead of
each shut-out college golfer: class and starts), which the archive keeps only as `denied` week/event pairs, not
the queue itself.

#### Run B: college golfers, their starts and their weeks

| Season | College golfers | Events each (report figure) | College (tier-5) starts each | Amateur (tier-6) starts each | Other starts each | Weeks shut out: every field full | Weeks not selected for the lineup | Weeks could not afford | Weeks no suitable event | Weeks declined/trained/rested | Full-time non-college amateurs | Part-time non-college amateurs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2027 | 1052 | 24.4 | 10.5 | 13.4 | 0.51 | 8.2 | 2.1 | 0.0 | 3.1 | 14.1 | 378 | 1185 |
| 2028 | 1042 | 23.8 | 10.8 | 12.5 | 0.51 | 9.2 | 2.2 | 0.1 | 3.1 | 13.5 | 424 | 1481 |
| 2029 | 1055 | 23.2 | 10.8 | 12.0 | 0.44 | 10.5 | 2.5 | 0.5 | 3.2 | 12.1 | 450 | 1755 |
| 2030 | 1063 | 22.3 | 10.8 | 11.1 | 0.36 | 11.4 | 2.8 | 1.4 | 3.2 | 10.8 | 412 | 2085 |
| 2031 | 1080 | 21.7 | 10.7 | 10.6 | 0.33 | 11.8 | 3.0 | 2.2 | 3.2 | 9.8 | 379 | 2345 |
| 2032 | 1106 | 21.1 | 10.5 | 10.2 | 0.33 | 12.6 | 3.5 | 2.4 | 3.3 | 8.9 | 361 | 2570 |
| 2033 | 1116 | 20.3 | 10.4 | 9.6 | 0.29 | 14.1 | 3.9 | 2.4 | 3.3 | 7.7 | 368 | 2763 |
| 2034 | 1112 | 19.5 | 10.5 | 8.7 | 0.31 | 15.1 | 4.4 | 2.5 | 3.2 | 7.0 | 384 | 2968 |
| 2035 | 1085 | 19.0 | 10.7 | 8.0 | 0.27 | 16.0 | 4.1 | 2.3 | 3.3 | 7.1 | 392 | 3131 |
| 2036 | 1055 | 18.8 | 11.0 | 7.5 | 0.29 | 16.2 | 4.0 | 2.1 | 3.5 | 7.2 | 375 | 3340 |

#### Run B: capacity, season by season

| Season | College events (incl. post-season) | Regular college events | Their places | Filled | Fill | Regular amateur (tier-6) events | Their places (1.5 × field, open-amateur expansion) | Filled | Fill | Events filled to the expanded cap | College entries in them | Non-college amateur entries | North American series: events full | College entries (N. Am.) | Non-college entries (N. Am.) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2027 | 135 | 120 | 10560 | 9948 | 94% | 394 | 54621 | 28191 | 52% | 123 | 12039 | 16152 | 69/101 | 6260 | 5570 |
| 2028 | 135 | 120 | 10560 | 10159 | 96% | 395 | 54783 | 30448 | 56% | 140 | 11212 | 19236 | 73/102 | 5332 | 7183 |
| 2029 | 135 | 120 | 10560 | 10322 | 98% | 395 | 54792 | 32643 | 60% | 153 | 10975 | 21668 | 80/102 | 5031 | 8245 |
| 2030 | 135 | 120 | 10560 | 10430 | 99% | 395 | 54792 | 33915 | 62% | 166 | 10343 | 23572 | 87/102 | 4342 | 9309 |
| 2031 | 135 | 120 | 10560 | 10495 | 99% | 396 | 54918 | 34777 | 63% | 175 | 10007 | 24770 | 89/102 | 3871 | 10043 |
| 2032 | 135 | 120 | 10560 | 10483 | 99% | 397 | 55044 | 36063 | 66% | 191 | 9883 | 26180 | 92/102 | 3452 | 10851 |
| 2033 | 135 | 120 | 10560 | 10523 | 100% | 396 | 54918 | 37112 | 68% | 206 | 9315 | 27797 | 101/102 | 2852 | 11758 |
| 2034 | 135 | 120 | 10560 | 10548 | 100% | 396 | 54918 | 38133 | 69% | 210 | 8392 | 29741 | 102/102 | 1838 | 12850 |
| 2035 | 135 | 120 | 10560 | 10475 | 99% | 396 | 54918 | 38431 | 70% | 212 | 7479 | 30952 | 102/102 | 1209 | 13479 |
| 2036 | 135 | 120 | 10560 | 10534 | 100% | 397 | 55044 | 38843 | 71% | 218 | 6768 | 32075 | 102/102 | 670 | 14018 |

#### Run B: by college circuit (golfers / events each)

| Season | US Division I | US Small College | International University |
|---|---|---|---|
| 2027 | 512 / 24.9 | 171 / 24.6 | 369 / 23.7 |
| 2028 | 484 / 24.2 | 187 / 24.1 | 371 / 23.2 |
| 2029 | 462 / 23.7 | 214 / 23.2 | 379 / 22.7 |
| 2030 | 440 / 22.9 | 245 / 22.0 | 378 / 21.9 |
| 2031 | 454 / 22.3 | 233 / 20.8 | 393 / 21.5 |
| 2032 | 457 / 21.5 | 242 / 19.8 | 407 / 21.4 |
| 2033 | 469 / 20.4 | 234 / 18.8 | 413 / 21.0 |
| 2034 | 487 / 19.2 | 218 / 17.8 | 407 / 20.7 |
| 2035 | 482 / 18.3 | 200 / 17.0 | 403 / 20.7 |
| 2036 | 441 / 18.2 | 209 / 16.2 | 405 / 20.8 |

#### Run C: college golfers, their starts and their weeks

| Season | College golfers | Events each (report figure) | College (tier-5) starts each | Amateur (tier-6) starts each | Other starts each | Weeks shut out: every field full | Weeks not selected for the lineup | Weeks could not afford | Weeks no suitable event | Weeks declined/trained/rested | Full-time non-college amateurs | Part-time non-college amateurs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2027 | 1052 | 24.5 | 10.5 | 13.5 | 0.52 | 8.1 | 2.1 | 0.0 | 3.1 | 14.2 | 378 | 1185 |
| 2028 | 1042 | 23.8 | 10.8 | 12.5 | 0.47 | 9.2 | 2.2 | 0.1 | 3.1 | 13.6 | 427 | 1465 |
| 2029 | 1055 | 23.1 | 10.9 | 11.8 | 0.40 | 10.4 | 2.5 | 0.8 | 3.2 | 12.0 | 448 | 1793 |
| 2030 | 1063 | 22.3 | 10.8 | 11.1 | 0.36 | 11.4 | 2.8 | 1.6 | 3.2 | 10.5 | 397 | 2109 |
| 2031 | 1080 | 21.6 | 10.7 | 10.6 | 0.31 | 11.7 | 2.9 | 2.5 | 3.3 | 9.6 | 364 | 2361 |
| 2032 | 1106 | 21.1 | 10.5 | 10.3 | 0.31 | 12.3 | 3.5 | 2.8 | 3.3 | 8.7 | 342 | 2581 |
| 2033 | 1116 | 20.3 | 10.4 | 9.6 | 0.29 | 14.0 | 3.9 | 2.9 | 3.4 | 7.4 | 353 | 2756 |
| 2034 | 1112 | 19.7 | 10.5 | 8.9 | 0.29 | 14.8 | 4.2 | 2.7 | 3.3 | 7.2 | 372 | 2940 |
| 2035 | 1085 | 18.9 | 10.7 | 7.9 | 0.28 | 15.6 | 4.3 | 2.6 | 3.3 | 7.1 | 382 | 3142 |
| 2036 | 1055 | 18.6 | 11.0 | 7.3 | 0.29 | 16.1 | 4.1 | 2.5 | 3.4 | 7.1 | 371 | 3339 |

#### Run C: capacity, season by season

| Season | College events (incl. post-season) | Regular college events | Their places | Filled | Fill | Regular amateur (tier-6) events | Their places (1.5 × field, open-amateur expansion) | Filled | Fill | Events filled to the expanded cap | College entries in them | Non-college amateur entries | North American series: events full | College entries (N. Am.) | Non-college entries (N. Am.) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2027 | 135 | 120 | 10560 | 9913 | 94% | 392 | 54342 | 28287 | 52% | 124 | 12177 | 16110 | 70/100 | 6308 | 5582 |
| 2028 | 135 | 120 | 10560 | 10163 | 96% | 392 | 54369 | 30367 | 56% | 140 | 11270 | 19097 | 73/101 | 5391 | 7081 |
| 2029 | 135 | 120 | 10560 | 10357 | 98% | 396 | 54918 | 32610 | 59% | 156 | 10825 | 21785 | 82/102 | 5006 | 8337 |
| 2030 | 135 | 120 | 10560 | 10420 | 99% | 397 | 55044 | 33783 | 61% | 166 | 10345 | 23438 | 85/102 | 4391 | 9302 |
| 2031 | 135 | 120 | 10560 | 10487 | 99% | 397 | 55044 | 34801 | 63% | 178 | 10150 | 24651 | 92/102 | 4030 | 10049 |
| 2032 | 135 | 120 | 10560 | 10510 | 100% | 396 | 54918 | 35828 | 65% | 185 | 10060 | 25768 | 93/102 | 3804 | 10571 |
| 2033 | 135 | 120 | 10560 | 10523 | 100% | 396 | 54918 | 36715 | 67% | 198 | 9377 | 27338 | 98/102 | 3090 | 11446 |
| 2034 | 135 | 120 | 10560 | 10538 | 100% | 397 | 55044 | 37784 | 69% | 209 | 8673 | 29111 | 102/102 | 2258 | 12430 |
| 2035 | 135 | 120 | 10560 | 10501 | 99% | 397 | 55044 | 38245 | 69% | 211 | 7474 | 30771 | 102/102 | 1362 | 13326 |
| 2036 | 135 | 120 | 10560 | 10522 | 100% | 396 | 54918 | 38736 | 71% | 217 | 6585 | 32151 | 102/102 | 600 | 14088 |

#### Run C: by college circuit (golfers / events each)

| Season | US Division I | US Small College | International University |
|---|---|---|---|
| 2027 | 512 / 25.0 | 171 / 24.7 | 369 / 23.8 |
| 2028 | 484 / 24.2 | 187 / 24.1 | 371 / 23.2 |
| 2029 | 462 / 23.6 | 214 / 23.1 | 379 / 22.4 |
| 2030 | 440 / 22.9 | 245 / 22.0 | 378 / 21.8 |
| 2031 | 454 / 22.4 | 233 / 21.0 | 393 / 21.2 |
| 2032 | 457 / 21.7 | 242 / 20.1 | 407 / 21.0 |
| 2033 | 469 / 20.4 | 234 / 19.0 | 413 / 20.8 |
| 2034 | 487 / 19.6 | 218 / 18.3 | 407 / 20.6 |
| 2035 | 482 / 18.4 | 200 / 17.3 | 403 / 20.4 |
| 2036 | 441 / 18.0 | 209 / 15.9 | 405 / 20.5 |

#### Run D: college golfers, their starts and their weeks

| Season | College golfers | Events each (report figure) | College (tier-5) starts each | Amateur (tier-6) starts each | Other starts each | Weeks shut out: every field full | Weeks not selected for the lineup | Weeks could not afford | Weeks no suitable event | Weeks declined/trained/rested | Full-time non-college amateurs | Part-time non-college amateurs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2027 | 1043 | 24.4 | 10.6 | 13.3 | 0.49 | 8.3 | 2.1 | 0.0 | 3.2 | 14.0 | 393 | 1222 |
| 2028 | 1026 | 23.8 | 11.0 | 12.4 | 0.44 | 9.2 | 2.2 | 0.0 | 3.4 | 13.3 | 452 | 1497 |
| 2029 | 1035 | 23.1 | 11.0 | 11.7 | 0.41 | 10.3 | 2.2 | 0.7 | 3.6 | 12.2 | 475 | 1756 |
| 2030 | 1035 | 22.2 | 11.0 | 10.8 | 0.36 | 10.9 | 2.2 | 1.7 | 3.8 | 11.0 | 446 | 2020 |
| 2031 | 1040 | 21.4 | 11.1 | 10.0 | 0.34 | 12.3 | 2.7 | 2.3 | 3.5 | 9.5 | 410 | 2295 |
| 2032 | 1059 | 20.8 | 10.9 | 9.5 | 0.32 | 13.3 | 3.4 | 2.4 | 3.4 | 8.4 | 374 | 2531 |
| 2033 | 1070 | 20.4 | 10.8 | 9.3 | 0.30 | 14.3 | 3.7 | 2.3 | 3.4 | 7.7 | 368 | 2728 |
| 2034 | 1082 | 20.0 | 10.8 | 8.9 | 0.29 | 15.2 | 3.9 | 2.0 | 3.3 | 7.3 | 360 | 2943 |
| 2035 | 1096 | 19.2 | 10.6 | 8.3 | 0.26 | 16.1 | 4.1 | 1.9 | 3.3 | 7.2 | 361 | 3113 |
| 2036 | 1078 | 18.9 | 10.8 | 7.8 | 0.28 | 15.9 | 4.2 | 2.4 | 3.4 | 6.9 | 354 | 3284 |

#### Run D: capacity, season by season

| Season | College events (incl. post-season) | Regular college events | Their places | Filled | Fill | Regular amateur (tier-6) events | Their places (1.5 × field, open-amateur expansion) | Filled | Fill | Events filled to the expanded cap | College entries in them | Non-college amateur entries | North American series: events full | College entries (N. Am.) | Non-college entries (N. Am.) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2027 | 135 | 120 | 10560 | 9940 | 94% | 393 | 54513 | 28764 | 53% | 129 | 12023 | 16741 | 70/102 | 6050 | 5859 |
| 2028 | 135 | 120 | 10560 | 10148 | 96% | 391 | 54252 | 30855 | 57% | 146 | 11107 | 19748 | 74/101 | 5318 | 7081 |
| 2029 | 135 | 120 | 10560 | 10259 | 97% | 397 | 55044 | 32556 | 59% | 156 | 10578 | 21978 | 79/102 | 4797 | 8186 |
| 2030 | 135 | 120 | 10560 | 10367 | 98% | 395 | 54783 | 33366 | 61% | 166 | 9855 | 23511 | 84/102 | 4045 | 9128 |
| 2031 | 135 | 120 | 10560 | 10463 | 99% | 397 | 55044 | 34143 | 62% | 173 | 9096 | 25047 | 88/102 | 3985 | 9839 |
| 2032 | 135 | 120 | 10560 | 10462 | 99% | 397 | 55044 | 35296 | 64% | 175 | 8845 | 26451 | 90/102 | 3439 | 10744 |
| 2033 | 135 | 120 | 10560 | 10506 | 99% | 396 | 54918 | 36736 | 67% | 192 | 8735 | 28001 | 95/102 | 2981 | 11502 |
| 2034 | 135 | 120 | 10560 | 10553 | 100% | 397 | 55044 | 37745 | 69% | 210 | 8507 | 29238 | 101/102 | 2565 | 12111 |
| 2035 | 135 | 120 | 10560 | 10531 | 100% | 397 | 55044 | 38384 | 70% | 217 | 7938 | 30446 | 102/102 | 1921 | 12767 |
| 2036 | 135 | 120 | 10560 | 10559 | 100% | 397 | 55044 | 38904 | 71% | 221 | 7330 | 31574 | 102/102 | 1386 | 13302 |

#### Run D: by college circuit (golfers / events each)

| Season | US Division I | US Small College | International University |
|---|---|---|---|
| 2027 | 509 / 24.9 | 167 / 24.5 | 367 / 23.8 |
| 2028 | 480 / 24.2 | 182 / 24.1 | 364 / 23.3 |
| 2029 | 460 / 23.6 | 189 / 23.0 | 386 / 22.5 |
| 2030 | 432 / 22.9 | 201 / 21.9 | 402 / 21.7 |
| 2031 | 443 / 22.2 | 221 / 20.7 | 376 / 21.0 |
| 2032 | 464 / 21.1 | 206 / 19.8 | 389 / 20.9 |
| 2033 | 461 / 20.6 | 214 / 19.1 | 395 / 21.0 |
| 2034 | 471 / 19.8 | 223 / 18.4 | 388 / 21.1 |
| 2035 | 484 / 18.7 | 222 / 17.2 | 390 / 20.9 |
| 2036 | 463 / 18.6 | 215 / 17.0 | 400 / 20.4 |

## Limitations

- **Build.** All runs are pinned commit 473690a1541c (engine b73a4f08), with none of the newer packages; every rule
  cited is that build's code in `build_473690a`, and every conclusion is about that build only.
- **Runs.** Three 10-season worlds (two seeds); B's seasons from 2033 were played by a resumed segment after the
  420 s guard stopped it (the report's provenance); `B/world_2027_after4` and run A were not touched. The 2036 cases
  have no recorded next season.
- **Week order.** The archive keeps each golfer's season as counts per weekly outcome (`careers[gid]['access']`), plus
  week numbers only for shut-out / not-selected / alternative weeks (`denied`) and history log lines. "Week by week"
  above means those weekly outcomes counted, not a week-numbered sequence; the zero-start seasons have no `denied`
  entries (they never entered).
- **Event costs.** Trip costs in unaffordable weeks are not recorded; the $350/$455/$630 figures and "spendable =
  cash + $8,000" come from the build's cost and credit rules applied to the recorded cash (no case had family money,
  backers or support left; a paid coach's fee would only lower spendable further).
- **Cross-run pairing.** Golfer ids match between B and C only for the seeded world and the 2028 arrivals.
- **Field capacity.** "Full" uses the 1.5 × field expansion that applies to tier-6 events; editions with several sites
  are counted at field × sites.
- **Read-only method.** Season files were read directly by the paths in each `archive/MANIFEST.json` (the archive's own
  `_read` does the same: gzip + json). Nothing in `runs/` was written; no index, cache or lock was opened.

## Files

- Scripts: `x1_seed.py` (seed rows, amateur tuples), `x4_archive.py` (season files), `x5_cases.py`, `x6_college.py`,
  `x7_u21.py`, `x8_more.py`, `x9_cross.py`, `x10_ids.py`, `x11_dbg.py`, `x12_series.py`, `x13_ptsrc.py`, `x14_other.py`,
  `x15_full.py`, `x16_tables.py`, `x17_coltables.py`, `x18_hist.py`.
- Extracts: `{B,C,D}_seed.pkl`, `{B,C,D}_arch.pkl`, `{B,C,D}_dbg.pkl`, `u21.pkl`, `college.pkl`, `full.pkl`, `series.pkl`.
