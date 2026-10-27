"""Golfers, caddies and the archetype profiles used for balance testing."""
from __future__ import annotations

from dataclasses import dataclass, field

from .ratings import ATTRIBUTE_KEYS, PERSONALITY_KEYS

# Weight of each attribute in the OVERALL rating. Overall is meant to predict
# scoring, so these weights are set from the measured stroke value of each
# attribute (see tools/balance_test.py, "attribute value" section). Injury
# resistance has no effect on a round, so it carries no weight.
OVERALL_WEIGHTS = {
    'power': .146, 'stamina': .045, 'recovery_rate': .012, 'injury_resistance': 0.0,
    'driving_accuracy': .114, 'long_irons': .068, 'mid_irons': .098, 'wedges': .051,
    'ball_flight': .035, 'chipping': .064, 'bunker': .025, 'recovery_play': .020,
    'short_putting': .068, 'lag_putting': .045, 'green_reading': .050,
    'striking_consistency': .028, 'putting_consistency': .016,
    'composure': .035, 'resilience': .015, 'management': .038, 'focus': .026,
}
assert set(OVERALL_WEIGHTS) == set(ATTRIBUTE_KEYS)

CADDIE_SKILLS = ('strategy', 'green_reading', 'yardage', 'course_knowledge', 'mental_support', 'communication')


@dataclass
class Golfer:
    name: str
    attrs: dict
    personality: dict = field(default_factory=lambda: {k: 50.0 for k in PERSONALITY_KEYS})
    familiarity: dict = field(default_factory=dict)   # course name -> competitive rounds played
    archetype: str = ''

    def __post_init__(self):
        missing = set(ATTRIBUTE_KEYS) - set(self.attrs)
        if missing:
            raise ValueError(f'missing attributes: {sorted(missing)}')
        for k in PERSONALITY_KEYS:
            self.personality.setdefault(k, 50.0)

    @property
    def overall(self):
        return overall_rating(self.attrs)


@dataclass
class Caddie:
    name: str
    skills: dict
    familiarity: dict = field(default_factory=dict)   # course name -> rounds caddied there

    def __post_init__(self):
        missing = set(CADDIE_SKILLS) - set(self.skills)
        if missing:
            raise ValueError(f'missing caddie skills: {sorted(missing)}')


def overall_rating(attrs, weights=None):
    w = weights or OVERALL_WEIGHTS
    total = sum(w.values())
    return sum(attrs[k] * w[k] for k in w) / total


def uniform_golfer(rating, name=None, **personality):
    """Every attribute at the same rating: the cleanest calibration subject."""
    return Golfer(name or f'All-{rating:g}', {k: float(rating) for k in ATTRIBUTE_KEYS},
                  dict(personality), archetype='Uniform')


def neutral_caddie(rating=50, name='Average caddie'):
    return Caddie(name, {k: float(rating) for k in CADDIE_SKILLS})


ARCHETYPES = {
    'All-Rounder': ({}, {}),
    'Power Hitter': ({'power': 14, 'long_irons': 6, 'driving_accuracy': -10, 'wedges': -4,
                      'chipping': -5, 'short_putting': -3, 'management': -4, 'ball_flight': -3},
                     {'aggression': 65}),
    'Precision Ball-Striker': ({'driving_accuracy': 12, 'mid_irons': 9, 'long_irons': 6,
                                'striking_consistency': 8, 'power': -10, 'chipping': -4,
                                'bunker': -4, 'short_putting': -4, 'lag_putting': -3}, {}),
    'Short-Game Artist': ({'chipping': 14, 'bunker': 12, 'recovery_play': 10, 'short_putting': 8,
                           'lag_putting': 6, 'green_reading': 6, 'power': -10,
                           'driving_accuracy': -6, 'long_irons': -8, 'mid_irons': -6}, {}),
    'Strategic Technician': ({'management': 15, 'focus': 10, 'composure': 8, 'green_reading': 6,
                              'lag_putting': 6, 'driving_accuracy': 6, 'power': -12,
                              'ball_flight': -4, 'recovery_play': -6, 'long_irons': -6},
                             {'aggression': 35}),
    'Aggressive Shotmaker': ({'ball_flight': 12, 'recovery_play': 10, 'long_irons': 8, 'power': 6,
                              'management': -10, 'striking_consistency': -8,
                              'driving_accuracy': -6, 'focus': -4}, {'aggression': 85}),
    'Effortless Power': ({'power': 8, 'ball_flight': 12, 'long_irons': 10, 'mid_irons': 4, 'composure': 8,
                          'short_putting': -7, 'lag_putting': -4, 'chipping': -6, 'bunker': -6,
                          'stamina': -6, 'focus': -4}, {'aggression': 45, 'big_stage': 70}),
    'Elite Putter': ({'short_putting': 15, 'lag_putting': 12, 'green_reading': 12,
                      'putting_consistency': 8, 'mid_irons': -8, 'long_irons': -8, 'power': -8,
                      'driving_accuracy': -6}, {}),
}


def archetype_golfer(archetype, overall, name=None):
    """Build an archetype profile whose OVERALL rating equals `overall` exactly."""
    offsets, personality = ARCHETYPES[archetype]
    attrs = {k: overall + offsets.get(k, 0.) for k in ATTRIBUTE_KEYS}
    for _ in range(8):  # shift until clamping no longer moves the overall
        shift = overall - overall_rating(attrs)
        attrs = {k: max(1., min(99., v + shift)) for k, v in attrs.items()}
    return Golfer(name or f'{archetype} {overall:g}', attrs, dict(personality), archetype=archetype)
