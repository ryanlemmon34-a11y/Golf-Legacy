"""Prestige: of events and of players, plus the ranking-point and prize-money scales built on them.

Event prestige (0-100), from a rolling average of the last 4 editions of every factor:
    tour        the series' standing: majors 100, Premier flagship 93, a mini-tour event ~24...  35%
    field       how good last year's field was: its best 30 players by world ranking (amateur
                ranking for amateur events)                                                         30%
    purse       prize money, on a log scale ($10k = 0, $25M = 100)                                   20%
    course      the venue: an elite course 100, a championship course's Championship tees 80,
                a standard course's Forward tees 32, a municipal course 25                          15%
    so an event's reputation moves slowly: one strong or weak year shifts it by a quarter.

Player prestige (0-100) comes from fame over the last 52 weeks (a one-year rolling window): every
finish earns fame in proportion to the event's prestige (cubed: a major is worth far more than a
mini-tour win). Big titles also add a lasting legacy that barely fades. Sponsors pay on player prestige.

Event prestige drives where AI golfers choose to play (see season.py): stars only bother with the
big events, so weaker "opportunity" events get weaker fields, which in turn lowers their prestige.
"""
from __future__ import annotations

import math

WEIGHTS = {'tour': 0.35, 'field': 0.30, 'purse': 0.20, 'course': 0.15}
WINDOW = 4                            # editions in the rolling average

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


def prestige_from(history):
    """Event prestige from the rolling average of the last WINDOW editions' factors."""
    rows = history[-WINDOW:]
    n = len(rows)
    tour, field, purse, course = (sum(r[i] for r in rows) / n for i in range(4))
    return WEIGHTS['tour'] * tour + WEIGHTS['field'] * field + WEIGHTS['purse'] * purse + WEIGHTS['course'] * course


def initial_prestige(series, course_quality):
    return prestige_from([initial_factors(series, course_quality)])


# ---- what results are worth --------------------------------------------------------------------
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
