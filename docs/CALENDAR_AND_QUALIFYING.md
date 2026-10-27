# Golf Legacy — World Calendar and Major Qualifying

Code: `golfsim/calendar.py`, `golfsim/geography.py`, `golfsim/qualification.py`.
Reports: `reports/CALENDAR_REPORT.md` (full week-by-week calendar), `reports/QUALIFYING_DEMO_REPORT.md`.

## The majors (owner decision)

| Week | Major | Real-life analogue | Venue |
|---|---|---|---|
| 18 | Tour Masters | The Masters | Georgia National, Athens, Georgia — every year |
| 24 | Premier Tour Championship | PGA Championship | Rotates around US championship courses |
| 25 | USA Open | U.S. Open | Rotates around classic US venues |
| 30 | Britannia Open | The Open Championship | Rotates around links in Scotland, England and Northern Ireland |

**No other competitive golf is played anywhere in the world in weeks 18, 24, 25 or 30** — no tour,
college, amateur or qualifying event.

## The calendar

A permanent list of event *series* (stable identity, format, field size, prestige, purse, week, host
country and a pool of real host cities). Each year produces *editions*; rotating series move city each
year. The scheduler fills the year in priority order: majors → fixed-week anchors (amateur
championships, qualifying stages, college post-season, Q-School, designated national opens) →
Premier Tour → Challenger, Regional and Mini tours → college and amateur seasons. Flexible events are
only placed where the host city's climate supports golf that week (Australia and South Africa in the
southern summer, the Middle East and Arizona in winter, Scotland in summer, the tropics all year).

| Level | Tours | Real-life analogue | Typical format |
|---|---|---|---|
| Premier (36 events: 8 flagship, 20 standard, 8 opportunity) | Premier Tour Americas, Europe, Asia-Pacific | PGA Tour, DP World Tour | 72 holes, cut |
| Challenger | Americas, Europe, Asia, Latin America & Canada, Japan | Korn Ferry, Challenge Tour, Asian Tour, PGA Tour Americas, JGTO | 72 holes, cut |
| Regional | Southern Africa, Australasia, Korea, India, China, Middle East & North Africa | Sunshine, Australasia, KPGA, PGTI, China Tour, MENA | 54-72 holes |
| Mini | 16 circuits worldwide | Mini tours (incl. the Japan Challenge Circuit, the ABEMA Tour's place) | 36-72 holes |
| College | US Division I, US Small College, International University | NCAA D1, D2/D3/NAIA, university golf | 36-54 holes; post-season to 72 |
| Amateur | Elite championships, 50 national amateur championships, 6 regional amateur series | US Amateur, The Amateur, Asia-Pacific Amateur; state/county events | 18-72 holes; two use match play |
| Qualifying | USA Open local/final, Britannia regional/final, Club Professional sectionals and Championship, Q-Schools | The same stages in real life | 18-72 holes |

Opportunity Premier events (weaker fields, the Barbasol / John Deere kind) sit in the weeks straight
after majors: weeks 19, 26 and 31, plus a few others. Because weeks 24 and 25 are back-to-back majors,
week 26 hosts two opportunity events. High-school golf is not in the calendar yet (owner decision).

## How players get into the majors

Every entrant records **every** category they satisfy; the first is their primary route. Qualifying
places go to the best finishers *not already exempt* — if an exempt player finishes in a qualifying
place, the spot passes to the next finisher. Fields are built "as of" the major's week: nothing that
happens later can count. Amateur categories are lost on turning professional.

**Every entrant's route is recorded** (`Season.entry_routes`). An entrant who is injured or retired
withdraws; their place goes to the next recorded alternate (route `ALT`), and an event without
alternates plays with a smaller field. Nobody is added from the world ranking to make up numbers.

**Tour Masters (Masters):** invitation only, about 90 players, never filled to a number. (The world's
very first Tour Masters is the one explicit exception: with no past champions or results yet, the best
of the seeded world ranking receive inaugural invitations, recorded as route `INIT`. This happens only
in the world's first season.) Past
champions (lifetime); other majors' champions (5 years); Premier Players Championship winners (3 years);
USA Amateur champion and runner-up, Britannia Amateur, Asia-Pacific Amateur, Latin America Amateur and
USA Mid-Amateur champions; top 12 at last year's Masters; top 4 at last year's other majors; winners of
full-points Premier Tour events since the last Masters (not opportunity events); last season's Premier
Tour Finals qualifiers; world top 50 at year end and two weeks before; up to four international
invitations.

**Premier Tour Championship (PGA Championship):** 156 players. Past champions; recent major and Players
champions; top 15 last year; **the top 20 from the Club Professional Championship (week 16)**, whose field itself comes from
36-hole **sectional qualifying** (week 12, four sites, played shot by shot: each site's places in
proportion to its entrants go to its best finishers); top 70 on
the Premier Tour Americas points list; Premier Tour winners since last year; world top 100 invitations;
filled from the points list — and the rest of that list stays on, in order, as reserves for later
withdrawals, so the field is back to 156 when anyone pulls out.

**USA Open (U.S. Open):** 156 players, open to professionals and good amateurs. About half the field is
exempt: champions (10 years), USA Amateur finalists, Mid-Amateur and Britannia Amateur champions, recent
major champions, top 10 last year, last season's Tour Finals qualifiers, world top 60 at two cut-offs.
The rest come through **local qualifying** (18 holes, weeks 19-21) and **final qualifying** (36 holes in
one day: England and Japan in week 22, eight North American sites in week 23), with alternates from
final qualifying.

**Britannia Open (The Open):** 156 players. Past champions aged 60 or under; top 10 last year; recent
major champions; world top 50; Tour Finals qualifiers and the top 30 in Premier Tour Europe; the
order-of-merit winners of the Japan, Asian, Australasian and Southern Africa tours; amateur champions
(Britannia, USA, European, Asia-Pacific, Latin America, Africa) and the leading world-ranked amateur;
the **Britannia Qualifying Series** (top finishers not already exempt at the Australia, South Africa,
Japan, New Zealand, Kenya, Korea, Canada and Scotland Opens, the Heartland Invitational and the Great
Lakes Open); **regional qualifying** (18 holes, weeks 26-27) and **final qualifying** (36 holes, four
venues, week 28, four places each); reserves from the world ranking.

## Verified by tests and the demonstration

- Majors fixed and alone in their weeks for every generated world; 36 Premier events split 8/20/8;
  every event in season for its city; all qualifying stages before their targets; every series named
  by the rules exists.
- Rules tested on hand-built cases: lifetime and age-limited past champions, amateurs who turn pro,
  no-hindsight fields, international invitations, exactly 20 club pros, qualifying spots passing down
  past exempt players, alternates filling to 156.
- `tools/qualifying_demo.py` plays two seasons at the top of the calendar (every shot) and builds the
  2027 fields purely from the rules: e.g. 1,080 players through 12 local qualifiers to 63 USA Open final
  qualifiers; 16 Britannia final qualifiers from four venues plus 25 through the Qualifying Series.

## Not built yet (next steps)

- **Season system:** each golfer's weekly schedule and entries, prioritising the biggest events they are
  eligible for; tour memberships and cards (Q-School results, promotion/relegation, winner exemptions).
- **World ranking and points lists:** the demo uses simple stand-ins.
- **Populations:** college players, amateurs, club professionals and lower-tour pros as real careers.
- **High-school golf** (later, owner decision).
- ~~Course library~~ — built: 380 courses, venue for every edition; see `docs/COURSE_LIBRARY.md`.
