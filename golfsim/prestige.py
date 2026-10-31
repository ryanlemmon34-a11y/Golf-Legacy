"""Prestige: of events and of players, plus the ranking-point and prize-money scales built on them.

Event prestige (0-100), from a recency-weighted average over the last five calendar years of every factor
(rules 2026-11-05; it had been the plain average of the last four editions):
    tour        the series' standing: majors 100, Premier flagship 93, a mini-tour event ~24...  35%
    field       how good last year's field was: its best 30 players by world ranking (amateur
                ranking for amateur events)                                                         30%
    purse       prize money, on a log scale ($10k = 0, $25M = 100)                                   20%
    course      the venue: an elite course 100, a championship course's Championship tees 80,
                a standard course's Forward tees 32, a municipal course 25                          15%
    so an event's reputation moves slowly: this year's edition carries a quarter of the weight (weights
    1.0, 0.9, 0.8, 0.7, 0.6 for this year and the four before), a calendar year without an edition (not
    held: nobody entered) is left out and the other years' weights renormalised, and an event's prestige
    moves at most EVENT_MAX_MOVE points in a calendar year either way. The field factor is the field as it
    was ranked the week it played (world or amateur ranking then): never what its players later became.
    Warm-up: a new world assumes each event's four years before the first season were played at its
    expected starting factors, so the first real edition carries a quarter of the weight (as before) and
    the assumed years leave the window one a year; from the fifth season the window is all real editions.

Course prestige (0-100) is a separate value from a course's physical class and layout (those stay the
`course` factor above): the prestige of the events it hosted, lagged one season (see `course_prestige`).
Event prestige never reads it, so a strong field cannot raise its own venue's prestige and feed back.

Player prestige (0-100) comes from fame over the last 52 weeks (a one-year rolling window): every
finish earns fame in proportion to the event's prestige (cubed: a major is worth far more than a
mini-tour win). Big titles also add a lasting legacy that barely fades. Sponsors pay on player prestige.

Event prestige drives where AI golfers choose to play (see season.py): stars only bother with the
big events, so weaker "opportunity" events get weaker fields, which in turn lowers their prestige.
"""
from __future__ import annotations

import math

WEIGHTS = {'tour': 0.35, 'field': 0.30, 'purse': 0.20, 'course': 0.15}

# ---- PROPOSED calibration (rules 2026-11-05): five-year prestige of events and courses --------------------------
# Starting values to measure, not proven ones (docs/WORLD_PRESTIGE_PACKAGE.md).
EVENT_YEARS = 5                       # calendar years in an event's window (this year and the four before)
YEAR_WEIGHTS = (1.0, 0.9, 0.8, 0.7, 0.6)   # by age in years; the newest edition keeps the old model's quarter
WARMUP_YEARS = 4                      # years before the first season assumed played at the expected factors
EVENT_MAX_MOVE = 6.0                  # most an event's prestige moves in one calendar year, either way
COURSE_YEARS = 5                      # completed seasons a course's prestige reads (never the current one)
COURSE_FADE = 0.9                     # hosted nothing in those seasons: its prestige x 0.9 a season
COURSE_MAX_MOVE = 10.0                # most a course's prestige moves from one season to the next
WINDOW = EVENT_YEARS                  # (the old name, kept for tools that read it)
# Better host venues for events that have outgrown theirs (Season.review_venues; a per-world overlay on the shared
# course plan, never a change to the course library):
VENUE_GAP = 5.0                       # event prestige at least this far above its venue's course prestige ...
VENUE_SUSTAIN = 3                     # ... at this many consecutive season ends
VENUE_LAG = 2                         # decided at the end of season Y, played from season Y + VENUE_LAG
VENUE_MIN_SEASONS = 10                # tradition: at most one move per event in this many seasons

COURSE_QUALITY = {('elite', 'Championship'): 100, ('championship', 'Championship'): 80,
                  ('standard', 'Championship'): 62, ('championship', 'Club'): 55, ('standard', 'Club'): 45,
                  ('standard', 'Forward'): 32, ('municipal', 'Regular'): 25, ('municipal', 'Forward'): 15}

# Expected field strength before an event has any history, by tier (0 = majors ... 8 = club pros),
# set from where fields settle in the multi-season test so prestige starts near its long-run level.
DEFAULT_FIELD = {0: 92, 1: 85, 2: 33, 3: 18, 4: 1, 5: 22, 6: 12, 7: 8, 8: 2}
DEFAULT_FIELD_CATEGORY = {'flagship': 88, 'opportunity': 72, 'elite_amateur': 50, 'national_amateur': 28,
                          'college_postseason': 32, 'national_open': None}


def purse_score(purse):
    if purse <= 0:
        return 0.0
    return max(0.0, min(100.0, (math.log10(purse) - 4.0) / 3.4 * 100))


def rank_value(rank, amateur=False):
    """How much a player at this world (or amateur) ranking position adds to a field's strength."""
    if rank is None:
        return 0.0
    return 60 * math.exp(-rank / 150) if amateur else 100 * math.exp(-rank / 250)


def field_strength(ranks, amateur=False, top=30):
    """Strength of a field (0-100) from its entrants' ranking positions (None = unranked)."""
    vals = sorted((rank_value(r, amateur) for r in ranks), reverse=True)[:top]
    vals += [0.0] * (top - len(vals))
    return sum(vals) / top


def factors(series, field, course_quality):
    """One edition's factors: (tour standing, field strength, purse score, course quality)."""
    return (series.prestige, field, purse_score(series.purse), course_quality)


def initial_factors(series, course_quality):
    """Factors before an event's first simulated edition (expected field for its level)."""
    field = DEFAULT_FIELD_CATEGORY.get(series.category)
    if field is None:
        field = DEFAULT_FIELD[series.tier]
    if series.tier == 1 and series.category == 'national_open':
        field = 92
    return factors(series, field, course_quality)


def combine(f):
    """Prestige of one set of (tour, field, purse, course) factors."""
    tour, field, purse, course = f
    return WEIGHTS['tour'] * tour + WEIGHTS['field'] * field + WEIGHTS['purse'] * purse + WEIGHTS['course'] * course


def prestige_from(rows):
    """Prestige of the plain average of some editions' factors (one edition: its own prestige)."""
    n = len(rows)
    return combine(tuple(sum(r[i] for r in rows) / n for i in range(4)))


def initial_prestige(series, course_quality):
    return prestige_from([initial_factors(series, course_quality)])


def seeded_years(f0, first_year):
    """An event's assumed history as the world begins ({year: [factors of that year's editions]}): the
    WARMUP_YEARS years before the first season, each at the expected starting factors f0."""
    return {first_year - k: [tuple(f0)] for k in range(1, WARMUP_YEARS + 1)}


def window_factors(by_year, year):
    """The recency-weighted mean factors over the calendar years year-4 .. year (YEAR_WEIGHTS by age). A year
    with no edition is left out and the other years' weights renormalised; several editions in one year count
    as their mean. None when no year of the window had an edition."""
    num, den = [0.0, 0.0, 0.0, 0.0], 0.0
    for age, w in enumerate(YEAR_WEIGHTS):
        rows = by_year.get(year - age)
        if not rows:
            continue
        for i in range(4):
            num[i] += w * sum(r[i] for r in rows) / len(rows)
        den += w
    return None if den == 0 else tuple(x / den for x in num)


def event_prestige_after(by_year, year, start):
    """An event's prestige after its edition in `year`: the five-year window's prestige, moved at most
    EVENT_MAX_MOVE from `start` (its prestige as that calendar year began). No edition in the window: `start`."""
    f = window_factors(by_year, year)
    if f is None:
        return start
    return max(start - EVENT_MAX_MOVE, min(start + EVENT_MAX_MOVE, combine(f)))


def course_prestige(hosted, year, before):
    """A course's prestige for season `year`, read from the completed seasons year-COURSE_YEARS .. year-1 only
    (a lag: what it hosts this season counts from the next). hosted: {season: the highest prestige, as played,
    of an event it hosted that season}. The recency-weighted mean (YEAR_WEIGHTS by age, the latest completed
    season first) over the seasons in which it hosted anything, moved at most COURSE_MAX_MOVE from `before`;
    with no hosting in the window, `before` x COURSE_FADE. `before` None (never rated): the window's value as
    it is, or None when it has hosted nothing."""
    num = den = 0.0
    for age, w in enumerate(YEAR_WEIGHTS[:COURSE_YEARS]):
        v = hosted.get(year - 1 - age)
        if v is None:
            continue
        num += w * v
        den += w
    if den == 0:
        return None if before is None else before * COURSE_FADE
    raw = num / den
    if before is None:
        return raw
    return max(before - COURSE_MAX_MOVE, min(before + COURSE_MAX_MOVE, raw))


# ---- what results are worth --------------------------------------------------------------------
RANK_WEEKS = 104              # ranking points count for 104 weeks (rules: world-ranking)
RANK_FULL = 13               # in full for 13 weeks, then falling in a straight line to nothing
WORLD_DIVISOR = (40, 52)     # the average divides by the starts in the window, but by at least 40, at most 52
AMATEUR_DIVISOR = (12, 40)


def ranking_weight(age):
    """How much of a start's points count `age` weeks later (age < RANK_WEEKS)."""
    return 1.0 if age < RANK_FULL else 1 - (age - RANK_FULL) / (RANK_WEEKS - RANK_FULL)


def ranking_total(rows, now):
    """(weighted points, starts) of the rows [(absolute week, points)] still in the window at week `now`,
    summed in the rows' order (the order they were earned) so the result is exactly the engine's."""
    tot, n = 0.0, 0
    for aw, pts in rows:
        age = now - aw
        if age >= RANK_WEEKS:
            continue
        n += 1
        tot += pts * (1.0 if age < RANK_FULL else 1 - (age - RANK_FULL) / (RANK_WEEKS - RANK_FULL))
    return tot, n


def ranking_divisor(n, divisor=WORLD_DIVISOR):
    lo, hi = divisor
    return min(hi, max(lo, n))


def finish_share(pos):
    """Share of the winner's points for a finishing position (world ranking style)."""
    if pos is None:
        return 0.0
    if pos == 1:
        return 1.0
    return 0.6 * (pos - 1) ** -0.73 if pos <= 60 else 0.0


def world_points(prestige, pos):
    """World ranking points: a major winner earns 100, a standard Premier winner ~60, Challenger ~12."""
    return 100 * max(0.0, (prestige - 20) / 80) ** 2.2 * finish_share(pos)


def amateur_points(prestige, pos):
    """Amateur ranking points (amateur and college events, and amateurs in professional events)."""
    return (prestige / 10) ** 2 * finish_share(pos)


FAME_FINISH = ((1, 1.0), (2, .45), (3, .3), (5, .2), (10, .1), (25, .03))


def fame_points(prestige, pos, made_cut=True):
    """Fame from one finish: the event's prestige cubed, times how high they finished."""
    if pos is None:
        return 0.0
    share = 0.01 if made_cut else 0.0
    for limit, s in FAME_FINISH:
        if pos <= limit:
            share = s
            break
    return 100 * (prestige / 100) ** 3 * share


FAME_WEEKS = 52            # player prestige: fame earned in the last year
LEGACY = {'major': 40.0, 'flagship': 10.0, 'premier': 4.0}
LEGACY_DECAY = 0.97        # per year
FAME_SCALE = 100.0


def player_prestige(fame, legacy):
    """0-100. ~88 for a dominant world No.1, ~47 for an average Premier Tour player, ~20 Challenger."""
    return 100 * (1 - math.exp(-math.sqrt(max(0.0, fame + 0.5 * legacy) / FAME_SCALE)))


def endorsements(prestige):
    """Yearly sponsor income in dollars, driven by player prestige."""
    return 1500 * math.exp(prestige / 9.0) if prestige > 0 else 0.0


def seeded_fame(overall, u):
    """Last year's fame for a golfer at the start of the world (no simulated history yet), from what a
    player of this ability earns in a typical year; u in [0, 1) spreads careers apart."""
    annual = math.exp(3.69 + 0.186 * (overall - 79))
    return annual * (0.6 + 0.8 * u)


# ---- prize money -------------------------------------------------------------------------------
_TOP = (18.0, 10.9, 6.9, 4.9, 4.1, 3.625, 3.375, 3.125, 2.925, 2.725)


def payout_shares(n_paid):
    """Percent of the purse for positions 1..n_paid (Premier Tour style), normalised to 100%."""
    raw = [(_TOP[i] if i < len(_TOP) else max(0.2, 2.725 * 0.955 ** (i - 9))) for i in range(n_paid)]
    total = sum(raw)
    return [r / total for r in raw]
