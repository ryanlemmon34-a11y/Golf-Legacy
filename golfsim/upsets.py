"""Biggest Upsets (roadmap B1/B2): each winner's estimated chance of winning, worked out before the event from
facts known then, with a documented and versioned model.

The model -- ``upset-model-1``
------------------------------
Inputs, per entrant, all read when the field is set and before any shot is struck: the golfer's Overall at that
moment (the base rating the profile shows, before this week's development), the number of stroke-play rounds and
the field itself. Nothing later enters: no result, no later rating, no later career. The event's own random
numbers are never touched (the estimate uses no random numbers at all).

1. Expected strokes per round and the round-to-round spread come from the engine's measured rating ladder
   (reports/BALANCE_REPORT.md section 1: golfers with every attribute at one rating, 4,000 rounds each), linearly
   interpolated in Overall (continued along the end segments below 10 and above 95; the spread is kept >= 2.5).
   Differences from the Overall-75 golfer's expected score are multiplied by STRETCH (the ladder is measured on
   a mid-difficulty course in calm conditions; tournament set-ups and pressure widen the gaps between levels).
2. Each entrant's total over R rounds is taken as Normal(R * mean, R * sd^2 + (R * TAU)^2): TAU is a per-event
   offset shared by an entrant's rounds (week form, and the spread between golfers of one Overall but different
   strengths).
3. STRETCH and TAU were fitted once against the engine's own upset measurement (balance report section 6: 1,000
   major-style 72-hole events with a fixed 144-player field), win chance per start by Overall band, measured
   (model 1): 86+ 15.45% (14.99%), 82-86 4.30% (4.14%), 78-82 1.23% (1.21%), 75-78 0.46% (0.50%), 72-75 0.20%
   (0.22%), 69-72 0.11% (0.09%), 60-69 0.01% (0.02%). tests/test_upsets.py keeps that comparison.
4. The lowest total wins: P(i wins) = integral of f_i(x) * prod_{j != i} P(T_j > x) dx, by Simpson's rule on a
   grid from min(mean - 6.5 sd) to min(mean + 8 sd) with a step of a quarter of the narrowest spread (at most
   GRID_MAX points; relative error about 3e-4 against a fine grid), the products summed as logs so that very
   small chances stay representable; the chances are then scaled to add up to exactly 1.
5. Stored values are rounded to 6 significant figures (so that a ranking does not depend on the last bit of a
   platform's maths library). Equal chances share a rank (1, 2, 2, 4); tied rows are listed by date, then event id.

What it leaves out (so a reader does not over-read it): recent form, course fit and familiarity, fatigue,
caddies, weather, pressure, the cut (a missed cut is simply a high total) and the discreteness of scores (ties
and playoffs are not modelled). It is an estimate from ratings, not calibrated betting odds. Match play is not
estimated by model 1 (a bracket is not a lowest-total contest): such editions are recorded as not estimated.

What is stored (archive: an edition's ``upset``): the model version, the site (0: the edition's winner), the
field size, the winner's chance, the winner's rank in the field by the model and by Overall, their Overall,
status, age and world (or amateur) ranking at the event, the favourite and their chance, and the top TOP_K
entrants' chances. Every entrant's chance is worked out but not stored (TOP_K plus the winner's are).
"""
from __future__ import annotations

import math

VERSION = 'upset-model-1'
# (Overall, mean strokes per round, round standard deviation): reports/BALANCE_REPORT.md section 1
LADDER = ((10, 101.49, 8.07), (25, 86.35, 6.21), (40, 80.35, 4.98), (50, 77.87, 4.32), (60, 75.65, 3.91),
          (65, 74.54, 3.65), (71, 73.07, 3.40), (75, 72.24, 3.21), (80, 71.14, 3.08), (85, 70.18, 3.04),
          (90, 68.87, 2.90), (95, 67.78, 2.79))
SD_FLOOR = 2.5
STRETCH = 1.15                 # differences in expected strokes from the Overall-75 golfer are multiplied by this
TAU = 0.85                     # shared per-round offset, strokes (see CALIBRATION)
TOP_K = 5
GRID_MAX = 81
_DIV = 4.0                     # grid step: the narrowest spread / _DIV
CALIBRATION = 'balance report section 6 (see the module notes, point 3)'
_SQRT2 = math.sqrt(2.0)
_M75 = 72.24
_LOG_SQRT_2PI = 0.5 * math.log(2 * math.pi)


def round_mean_sd(overall):
    """(expected strokes per round, round standard deviation) for an Overall, from LADDER."""
    lad = LADDER
    if overall <= lad[0][0]:
        a, b = lad[0], lad[1]
    elif overall >= lad[-1][0]:
        a, b = lad[-2], lad[-1]
    else:
        i = next(k for k in range(1, len(lad)) if overall <= lad[k][0])
        a, b = lad[i - 1], lad[i]
    t = (overall - a[0]) / (b[0] - a[0])
    return a[1] + t * (b[1] - a[1]), max(SD_FLOOR, a[2] + t * (b[2] - a[2]))


def total_params(overall, rounds):
    m, sd = round_mean_sd(overall)
    m = _M75 + STRETCH * (m - _M75)
    return rounds * m, math.sqrt(rounds * sd * sd + (rounds * TAU) ** 2)


def _log_q(z):
    """log P(Z > z) for a standard normal Z, accurate in the far upper tail."""
    if z < 8.0:
        return math.log(0.5 * math.erfc(z / _SQRT2))
    z2 = z * z
    return -0.5 * z2 - math.log(z) - _LOG_SQRT_2PI + math.log1p(-1 / z2 + 3 / (z2 * z2))


def sig(x, n=6):
    return float(f'{x:.{n}g}')


def win_probabilities(overalls, rounds):
    """Each entrant's chance of the lowest total (list, same order as `overalls`), adding up to 1. Overall None
    (not known) is taken as the field's lowest known Overall (a stable, conservative rule: an unknown entrant is
    never made the favourite). Deterministic: no random numbers."""
    n = len(overalls)
    if n == 0:
        return []
    if n == 1:
        return [1.0]
    known = [o for o in overalls if o is not None]
    floor = min(known) if known else 50.0
    params = [total_params(floor if o is None else o, max(1, rounds)) for o in overalls]
    lo = min(m - 6.5 * s for m, s in params)
    hi = min(m + 8.0 * s for m, s in params)
    step = min(s for _, s in params) / _DIV
    g = int((hi - lo) / step) + 1
    g = max(21, min(GRID_MAX, g + (g % 2 == 0)))        # odd, for Simpson's rule
    h = (hi - lo) / (g - 1)
    xs = [lo + k * h for k in range(g)]
    wts = [(1 if k in (0, g - 1) else 4 if k % 2 else 2) * h / 3 for k in range(g)]
    logq = []
    total = [0.0] * g
    for m, s in params:
        row = [_log_q((x - m) / s) for x in xs]
        logq.append(row)
        for k in range(g):
            total[k] += row[k]
    out = []
    exp = math.exp
    for (m, s), row in zip(params, logq):
        c = -math.log(s) - _LOG_SQRT_2PI
        acc = 0.0
        for k in range(g):
            z = (xs[k] - m) / s
            e = c - 0.5 * z * z + total[k] - row[k]
            if e > -700:
                acc += wts[k] * exp(e)
        out.append(acc)
    tot = sum(out)
    if tot <= 0:
        return [1.0 / n] * n
    return [p / tot for p in out]


def estimate(entrants, rounds, match_play=False):
    """The pre-event estimate for one site's field. entrants: [(gid, Overall or None)] in field order.
    Returns {'model', 'rounds', 'p': {gid: chance (6 s.f.)}, 'by_overall': {gid: rank by Overall}} or a
    not-estimated marker for match play / an empty field."""
    if match_play:
        return {'model': VERSION, 'estimated': False, 'why': 'match play (model 1 covers stroke play only)'}
    if not entrants:
        return {'model': VERSION, 'estimated': False, 'why': 'no field'}
    ps = win_probabilities([o for _, o in entrants], rounds)
    ov = {gid: o for gid, o in entrants}
    return {'model': VERSION, 'estimated': True, 'rounds': rounds,
            'p': {gid: sig(p) for (gid, _), p in zip(entrants, ps)}, 'overall': ov}


def _rank(values, key):
    """1 + the number of values strictly better than `key`'s (ties share a rank)."""
    v = values[key]
    return 1 + sum(1 for x in values.values() if x > v)


def record(pre, winner, facts):
    """The archived record of an edition, from its pre-event estimate and its winner (looked up after the event:
    the estimate itself is not changed). facts(gid) -> {'status', 'age', 'wr', 'ar'} as at the event."""
    if not pre.get('estimated'):
        return {'model': pre['model'], 'estimated': False, 'why': pre.get('why')}
    p = pre['p']
    order = sorted(p, key=lambda g: (-p[g], g))          # favourite first; equal chances by person id
    ov = {g: (o if o is not None else -1.0) for g, o in pre['overall'].items()}
    out = {'model': pre['model'], 'estimated': True, 'site': 0, 'field': len(p), 'rounds': pre['rounds'],
           'top': [[g, p[g]] for g in order[:TOP_K]],
           'favourite': order[0], 'favourite_p': p[order[0]],
           'favourite_overall': _r1(pre['overall'][order[0]]), 'favourite_facts': facts(order[0])}
    if winner is None or winner not in p:
        out['winner'] = None
        return out
    out.update({'winner': winner, 'p': p[winner], 'rank': _rank(p, winner), 'overall_rank': _rank(ov, winner),
                'overall': _r1(pre['overall'][winner]), 'winner_facts': facts(winner)})
    return out


def _r1(x):
    return None if x is None else round(x, 1)


def odds_text(p):
    """'12.3%' or '1 in 2,345' (a chance under 1% as one in N, rounded to 3 significant figures)."""
    if p is None:
        return 'not recorded'
    if p >= 0.01:
        return f'{100 * p:.1f}%'
    if p <= 0:
        return 'below 1 in 10^300'
    n = 1 / p
    return f'1 in {sig(n, 3):,.0f}'
