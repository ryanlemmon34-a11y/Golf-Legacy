"""Attribute definitions and the rating scale.

Every rated attribute uses the same 0-100 scale. The scale is anchored to
real playing levels (see TARGET_SCORE below):

    10  high-school golfer, 12-15 handicap
    25  good enough to enter amateur events
    40  winning amateur events
    50  mini-tour professional
    60  Challenger tour regular
    75  Premier Tour average
    90  world number one level
    95+ generational

Attribute ratings are translated into physical shot behaviour through the
anchor tables in this module (e.g. "a 75 Power golfer averages ~298 yards
off the tee"). Tables are interpolated linearly between anchor points.
"""
from __future__ import annotations

from bisect import bisect_right

# key, display label, group, what it does on the course
ATTRIBUTES = (
    ('power', 'Power', 'Physical', 'Clubhead speed: driving distance and the club hit into greens'),
    ('stamina', 'Stamina', 'Physical', 'Holding sharpness late in a round and late in a week'),
    ('recovery_rate', 'Recovery', 'Physical', 'How quickly fatigue clears between rounds and events'),
    ('injury_resistance', 'Injury Resistance', 'Physical', 'Injury risk (career system, no direct shot effect)'),
    ('driving_accuracy', 'Driving Accuracy', 'Long Game', 'Fairways hit, avoiding trouble and penalties'),
    ('long_irons', 'Long Irons', 'Long Game', 'Approaches from ~200+ yards, long par 3s, par 5s in two'),
    ('mid_irons', 'Mid/Short Irons', 'Long Game', 'Approaches from ~125-200 yards'),
    ('wedges', 'Wedge Play', 'Long Game', 'Distance control inside ~125 yards'),
    ('ball_flight', 'Ball-Flight Control', 'Long Game', 'Shaping shots, playing in wind, doglegs'),
    ('chipping', 'Chipping/Pitching', 'Short Game', 'Getting up and down from around the green'),
    ('bunker', 'Bunker Play', 'Short Game', 'Greenside and fairway sand'),
    ('recovery_play', 'Recovery Play', 'Short Game', 'Trees, thick rough, awkward lies, escaping trouble'),
    ('short_putting', 'Short Putting', 'Putting', 'Holing putts inside ~10 feet'),
    ('lag_putting', 'Lag Putting', 'Putting', 'Speed control from long range, avoiding three-putts'),
    ('green_reading', 'Green Reading', 'Putting', 'Reading break; matters most on sloped, fast greens'),
    ('striking_consistency', 'Ball-Striking Consistency', 'Consistency', 'How much full shots vary day to day and shot to shot'),
    ('putting_consistency', 'Putting Consistency', 'Consistency', 'Day-to-day putting form and short-putt lapses'),
    ('composure', 'Composure', 'Mental', 'How much pressure costs: cut line, Sunday lead, final holes'),
    ('resilience', 'Resilience', 'Mental', 'Bouncing back after bad holes'),
    ('management', 'Course Management', 'Mental', 'Choosing smart targets, when to attack or lay up'),
    ('focus', 'Focus', 'Mental', 'Avoiding mental errors over 18 and 72 holes'),
)
ATTRIBUTE_KEYS = tuple(a[0] for a in ATTRIBUTES)
ATTRIBUTE_LABELS = {a[0]: a[1] for a in ATTRIBUTES}
ATTRIBUTE_GROUPS = {a[0]: a[2] for a in ATTRIBUTES}

# Hidden personality traits (0-100). They shape decisions and pressure
# response; they are not trained like skills.
PERSONALITY_KEYS = ('big_stage', 'aggression', 'adaptability', 'coachability', 'work_ethic')

# Target expected 18-hole score of a golfer with EVERY attribute at the given
# rating, on the mid-difficulty test course in calm conditions, no pressure.
# Amateur targets use handicap math for Ashford Ridge's measured tournament set-up
# (course rating ~78, slope ~147).
TARGET_SCORE = ((0, 108.0), (10, 98.5), (25, 85.0), (32, 82.0), (40, 79.5), (50, 77.0),
                (60, 75.0), (65, 73.9), (70, 72.95), (75, 72.0), (80, 71.1),
                (85, 70.2), (90, 69.15), (95, 68.1), (100, 67.1))

LEVELS = ((0, 'Beginner'), (10, 'High school / 12-15 handicap'), (25, 'Amateur event entrant'),
          (40, 'Amateur event winner'), (50, 'Mini-tour professional'), (60, 'Challenger regular'),
          (68, 'Fringe Premier professional'), (75, 'Premier Tour average'),
          (82, 'Premier Tour star'), (88, 'World No.1 contender'), (95, 'Generational'))


def interp(table, x):
    """Piecewise-linear interpolation through sorted (x, y) anchor points."""
    xs = [p[0] for p in table]
    if x <= xs[0]:
        return table[0][1]
    if x >= xs[-1]:
        return table[-1][1]
    i = bisect_right(xs, x) - 1
    (x0, y0), (x1, y1) = table[i], table[i + 1]
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def norm(rating):
    """0-100 rating as a 0-1 fraction (used for blending effects)."""
    return max(0.0, min(1.0, rating / 100.0))


def level_name(overall):
    name = LEVELS[0][1]
    for threshold, label in LEVELS:
        if overall >= threshold:
            name = label
    return name


# ---------------------------------------------------------------------------
# Anchor tables: rating -> physical behaviour. "Tour average" means rating 75.
# ---------------------------------------------------------------------------

# Power -> total driver distance (yards) in calm air on an average-firm fairway.
DRIVE_DISTANCE = ((0, 205), (10, 228), (25, 252), (40, 272), (50, 283), (60, 290),
                  (75, 298), (85, 302), (90, 305), (100, 313))

# Driving accuracy -> lateral standard deviation of a driver (yards).
DRIVE_SIGMA = ((0, 34), (10, 30), (25, 24.5), (40, 21.5), (50, 20.2), (60, 19.0),
               (75, 17.5), (90, 16.2), (100, 15.3))

# Iron/wedge skill -> multiplier on tour-average proximity to the hole.
APPROACH_MULT = ((0, 1.30), (10, 1.16), (25, 1.05), (40, 1.05), (50, 1.05), (60, 1.05),
                 (75, 1.0), (85, 0.945), (90, 0.905), (100, 0.84))

# Chipping / bunker skill -> multiplier on tour-average proximity.
SHORT_MULT = ((0, 1.55), (10, 1.36), (25, 1.18), (40, 1.14), (50, 1.12), (60, 1.09),
              (75, 1.0), (85, 0.95), (90, 0.91), (100, 0.85))

# Chance a chip is duffed or thinned (fails to finish near the hole).
CHIP_FAIL = ((0, 0.085), (10, 0.065), (25, 0.046), (40, 0.034), (50, 0.028), (60, 0.023),
             (75, 0.016), (90, 0.011), (100, 0.008))

# Chance a greenside bunker shot fails to get out / is badly thinned.
BUNKER_FAIL = ((0, 0.16), (10, 0.12), (25, 0.085), (40, 0.058), (50, 0.048), (60, 0.038),
               (75, 0.025), (90, 0.016), (100, 0.012))

# Chance a "go for it" escape from trees/deep trouble comes off.
RECOVERY_SUCCESS = ((0, 0.10), (10, 0.18), (25, 0.28), (40, 0.36), (50, 0.41), (60, 0.46),
                    (75, 0.54), (90, 0.62), (100, 0.67))

# Short putting -> shift in make-probability log-odds vs tour average.
PUTT_SHORT_SHIFT = ((0, -0.54), (10, -0.42), (25, -0.27), (40, -0.21), (50, -0.17),
                    (60, -0.12), (75, 0.0), (85, 0.05), (90, 0.10), (100, 0.18))

# Lag putting -> multiplier on how far long putts finish from the hole.
LAG_MULT = ((0, 1.30), (10, 1.22), (25, 1.15), (40, 1.12), (50, 1.10), (60, 1.08),
            (75, 1.0), (90, 0.91), (100, 0.87))

# Green reading -> log-odds shift on breaking putts (scaled by green slope).
READ_SHIFT = ((0, -0.25), (10, -0.21), (25, -0.15), (40, -0.10), (50, -0.08),
              (60, -0.05), (75, 0.0), (90, 0.05), (100, 0.08))

# Ball-striking consistency -> chance a full shot is a mishit.
MISHIT_RATE = ((0, 0.033), (10, 0.026), (25, 0.020), (40, 0.017), (50, 0.016), (60, 0.014),
               (75, 0.0105), (90, 0.008), (100, 0.007))

# Ball-striking consistency -> day-to-day form spread (log dispersion).
STRIKE_FORM_SD = ((0, 0.14), (10, 0.13), (40, 0.10), (60, 0.08), (75, 0.06), (90, 0.05), (100, 0.045))

# Putting consistency -> day-to-day putting form spread (log-odds).
PUTT_FORM_SD = ((0, 0.28), (10, 0.25), (40, 0.20), (60, 0.15), (75, 0.12), (90, 0.10), (100, 0.09))

# Focus -> extra chance of a mental error on any full shot.
MENTAL_ERROR = ((0, 0.026), (10, 0.022), (25, 0.017), (40, 0.015), (60, 0.013), (75, 0.010),
                (90, 0.0065), (100, 0.005))

# Putting consistency -> chance of a lapse (misread, yip) on a short putt.
PUTT_LAPSE = ((0, 0.055), (10, 0.045), (25, 0.035), (40, 0.028), (60, 0.022), (75, 0.016),
              (90, 0.009), (100, 0.006))

# Recovery play -> multiplier on the extra difficulty of rough and awkward lies.
ROUGH_SKILL = ((0, 1.45), (10, 1.35), (25, 1.22), (40, 1.14), (60, 1.07), (75, 1.0),
               (90, 0.90), (100, 0.84))

# Approach contact error (feet added to proximity) for weaker ball-strikers: poor contact does not
# shrink much with a shorter club. Uses the average of iron skills and ball-striking consistency.
CONTACT_FLOOR = ((0, 22), (10, 16.5), (25, 8), (40, 4), (50, 2.5), (60, 1.2), (75, 0), (100, 0))

# Course management -> noise when judging strategic options (strokes).
DECISION_NOISE = ((0, 0.60), (10, 0.50), (40, 0.32), (60, 0.22), (75, 0.15), (90, 0.08), (100, 0.05))
