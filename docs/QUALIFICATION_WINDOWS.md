# Qualification windows: what "last N years" means, route by route

Every major qualification route that counts past seasons, with the sporting rule it stands for, whether the
current year's edition counts, and exactly which editions a champion holds. Reference calendar (v2): the
Premier Players Championship is in week 11, the majors in weeks 15 (Tour Masters), 20 (Premier Tour
Championship), 25 (USA Open) and 30 (Britannia Open). A field is set from what had been played by its cut-off,
so "the current edition counts" only when it was played earlier in the same season.

Boundary tests: `tests/test_exemption_window.py` (every route below, with the editions listed here).

## Settled

| Route | Rule | Current edition | A champion of year X holds |
|---|---|---|---|
| U1 USA Open champions, last 10 years | The ten USA Opens after the win | Never (it is this year's event) | X+1 .. X+10; gone in X+11 unless they win again (rules 2026-11-01) |
| M2 Major champions, last 5 years (at the Tour Masters) | The five most recent editions of the other three majors | Never played yet (the Masters is the season's first major) | X+1 .. X+5 (five Masters) |
| Premier winner exemptions (cards) | A major: the rest of that season and the next five; a Premier event: the rest of that season and the next two | From the week of the win | Major: X (from the win) .. X+5; Premier event: X .. X+2 |
| M1, P1 past champions | Lifetime | — | Every later edition |
| B1 past Britannia champions aged 60 or under | Lifetime, while 60 or under (age = season minus birth year) | — | Every later edition up to age 60 |
| Single-edition routes (M9, P4, U7, B2: top finishers of the event's previous edition; M10: of the other three majors' previous editions) | The previous season's edition | No | X+1 only |
| M11, P7 Premier winners since the last edition | Wins after last year's edition of this major, up to the cut-off | — | The next edition only |
| Amateur titles and the annual amateur award | The next edition each title's date allows, while still an amateur | — | Listed per route on the Rules page |

## Decided 31 October 2026 (rules 2026-11-03): the N most recent editions

The other majors' champions (P2, U5, B3: "last 5 years") and the Premier Players Championship winners (M3, P3,
U6, B4: "last 3 years") count the **N most recent editions as of the field**: this season's edition is one of the
N only when the calendar plays it before the field is set (it has then been played), otherwise the N editions
before this season's. This mirrors the real categories: the 2022 U.S. Open took Masters champions of 2018-22 (five
editions) ([PGA TOUR, how the 2022 U.S. Open field qualified](https://pgatour.com/inside-the-field/2022/06/10/how-the-field-qualified-us-open-the-country-club-brookline.html)),
and the Masters invites the last three winners of the Players ([Golf News Net, Masters invitation
categories](https://thegolfnewsnet.com/ryan_ballengee/2018/04/01/19-ways-how-to-earn-masters-invitation-exemption-109013/)).
Until 2026-11-03 these routes counted N + 1 editions once the current one was played.

Whether this season's edition is one of the N is read from the calendar (the series' week against the major's),
not from whether a result happens to be known, so a place secured at the end of a season (`secured_places`) and
the field itself use the same window. Only these seven routes changed: U1, M2, lifetime and age-limited past
champions, the single-edition routes and card durations are as listed above. The classic calendar (v1) keeps its
rules unchanged (it is browse-only).

| Route | Edition of year X counted | A champion of year X holds |
|---|---|---|
| P2 at the Premier Tour Championship (wk 20): Masters champions | Masters X counts in X (played week 15) | X .. X+4 (five) |
| P2: USA Open and Britannia champions (not yet played that season) | from X+1 | X+1 .. X+5 (five) |
| U5 at the USA Open (wk 25): Masters and Premier Tour Championship champions | in X | X .. X+4 |
| U5: Britannia champions | from X+1 | X+1 .. X+5 |
| B3 at the Britannia Open (wk 30): Masters, Premier Tour Championship and USA Open champions | in X | X .. X+4 |
| M3, P3, U6, B4: Players winners (week 11, always played first) | in X | X .. X+2 (three) |

Boundary tests (`tests/test_exemption_window.py`): the first and last edition held and the first missed for every
route, a current edition not yet played (the window never reaches back an extra year to make up for it), the
evidence a place shows, and v1 unchanged.
