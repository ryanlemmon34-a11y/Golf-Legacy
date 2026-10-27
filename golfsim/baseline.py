"""Expected strokes to hole out, by lie and distance, for a tour-average player.

Values approximate the published PGA Tour shot-level baseline popularised by
Mark Broadie ("Every Shot Counts"). They serve two purposes:

1. Strokes-gained reporting (driving / approach / short game / putting).
2. Giving AI golfers a sensible way to compare strategic options.

They are a reference curve, not a source of randomness: no score is ever
drawn from this table.
"""
from __future__ import annotations

from .ratings import interp

TEE = ((100, 2.92), (120, 2.99), (140, 2.97), (160, 2.99), (180, 3.05), (200, 3.12),
       (220, 3.17), (240, 3.25), (260, 3.45), (280, 3.65), (300, 3.71), (320, 3.79),
       (340, 3.86), (360, 3.92), (380, 3.96), (400, 3.99), (420, 4.02), (440, 4.08),
       (460, 4.17), (480, 4.28), (500, 4.41), (520, 4.54), (540, 4.65), (560, 4.74),
       (580, 4.79), (600, 4.82), (650, 5.0))
FAIRWAY = ((5, 2.10), (10, 2.18), (20, 2.40), (30, 2.52), (40, 2.60), (50, 2.66), (60, 2.70),
           (80, 2.75), (100, 2.80), (120, 2.85), (140, 2.91), (160, 2.98), (180, 3.08),
           (200, 3.19), (220, 3.32), (240, 3.45), (260, 3.58), (280, 3.69), (300, 3.78),
           (350, 3.92), (400, 4.11), (450, 4.25), (500, 4.53), (550, 4.82), (600, 4.94))
ROUGH = ((5, 2.20), (10, 2.34), (20, 2.59), (30, 2.70), (40, 2.78), (60, 2.91), (80, 2.96),
         (100, 3.02), (120, 3.08), (140, 3.15), (160, 3.23), (180, 3.31), (200, 3.42),
         (220, 3.53), (240, 3.64), (260, 3.74), (280, 3.83), (300, 3.90), (350, 4.08),
         (400, 4.25), (450, 4.40), (500, 4.65), (550, 4.90), (600, 5.05))
SAND = ((5, 2.30), (10, 2.43), (20, 2.53), (30, 2.66), (40, 2.82), (60, 3.15), (80, 3.24),
        (100, 3.23), (120, 3.21), (140, 3.22), (160, 3.28), (180, 3.40), (200, 3.55),
        (220, 3.70), (240, 3.84), (260, 3.93), (280, 4.00), (300, 4.04), (400, 4.40),
        (500, 4.80), (600, 5.10))
RECOVERY = ((10, 2.80), (20, 3.00), (50, 3.40), (100, 3.80), (120, 3.78), (140, 3.80),
            (160, 3.81), (180, 3.82), (200, 3.87), (220, 3.92), (240, 3.97), (260, 4.03),
            (280, 4.10), (300, 4.20), (400, 4.50), (500, 4.90), (600, 5.20))
GREEN_FT = ((0.5, 1.0), (1, 1.0), (2, 1.01), (3, 1.04), (4, 1.13), (5, 1.23), (6, 1.34),
            (7, 1.42), (8, 1.50), (9, 1.56), (10, 1.61), (12, 1.70), (15, 1.78), (20, 1.87),
            (25, 1.93), (30, 1.98), (40, 2.06), (50, 2.14), (60, 2.21), (70, 2.27),
            (80, 2.31), (90, 2.40), (100, 2.45), (150, 2.65))

_TABLES = {'tee': TEE, 'fairway': FAIRWAY, 'rough': ROUGH, 'sand': SAND,
           'fairway_bunker': SAND, 'trees': RECOVERY, 'fringe': ROUGH}


def expected(lie, distance):
    """Expected strokes to hole out. distance in yards, except 'green' in feet."""
    if lie == 'green':
        return interp(GREEN_FT, distance)
    if lie == 'fringe':
        # Fringe plays close to a long putt.
        return min(interp(ROUGH, distance), interp(GREEN_FT, distance * 3) + 0.05)
    return interp(_TABLES[lie], distance)
