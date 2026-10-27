"""Nation golf profiles: how many golfers a country produces, how good they become, and their style.

Each country has
    pool          relative number of serious competitive golfers (amateur and professional)
    development   0-100: coaching, facilities, junior programmes, competition. Shifts how much of
                  their talent golfers realise. 60 = a strong golf nation.
    pathway       0-100: access to elite college golf and academies (the US college system, national
                  squads). Decides how many young players go to college, and where.
    style         playing tendencies that tilt attributes and archetypes (links golfers flight the
                  ball, Japanese golfers have precise short games, Americans hit it far...)

These are the STARTING values for 2027. The nation-improvement model (planned) will move
development, pool and pathway over time from the results of each country's golfers.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from .geography import COUNTRIES

# Attribute tilts (points added before the overall is set) and archetype weight multipliers.
STYLES = {
    'power': ({'power': 3, 'driving_accuracy': -1, 'recovery_play': 1},
              {'Power Hitter': 1.6, 'Effortless Power': 1.3}),
    'links': ({'ball_flight': 4, 'bunker': 2, 'recovery_play': 2, 'composure': 1, 'power': -1, 'lag_putting': 1},
              {'Strategic Technician': 1.4, 'Short-Game Artist': 1.2}),
    'precision': ({'driving_accuracy': 3, 'wedges': 2, 'short_putting': 2, 'chipping': 2, 'power': -4,
                   'striking_consistency': 1},
                  {'Precision Ball-Striker': 1.5, 'Short-Game Artist': 1.4, 'Elite Putter': 1.4, 'Power Hitter': .5}),
    'touch': ({'chipping': 4, 'recovery_play': 4, 'bunker': 2, 'management': -1, 'driving_accuracy': -1},
              {'Short-Game Artist': 1.8, 'Aggressive Shotmaker': 1.4}),
    'complete': ({'striking_consistency': 2, 'management': 2, 'driving_accuracy': 1, 'mid_irons': 1},
                 {'All-Rounder': 1.6, 'Strategic Technician': 1.3}),
    'striker': ({'long_irons': 2, 'mid_irons': 2, 'power': 1, 'chipping': -1},
                {'Precision Ball-Striker': 1.5, 'All-Rounder': 1.2}),
    'touch_sea': ({'chipping': 2, 'wedges': 2, 'short_putting': 1, 'power': -2},
                  {'Short-Game Artist': 1.4, 'Elite Putter': 1.2}),
    'raw': ({'management': -2, 'green_reading': -1, 'chipping': -1, 'power': 1},
            {'Aggressive Shotmaker': 1.3, 'Power Hitter': 1.2}),
}


@dataclass
class NationProfile:
    country: str
    pool: float
    development: float
    pathway: float
    style: str
    history: list = field(default_factory=list)      # (year, development, pool, pathway) snapshots

    @property
    def region(self):
        return COUNTRIES[self.country].region


_P = (
    # country,          pool, dev, pathway, style
    ('USA', 100, 64.3, 95, 'power'), ('Canada', 13, 59, 80, 'power'), ('Mexico', 3.5, 60, 55, 'touch'),
    ('Brazil', 1.5, 50, 35, 'touch'), ('Argentina', 3.0, 63, 45, 'touch'), ('Chile', 1.5, 61, 55, 'touch'),
    ('Colombia', 1.8, 60.5, 55, 'touch'), ('Peru', .6, 48, 30, 'touch'),
    ('England', 22, 64, 70, 'links'), ('Scotland', 8, 61.5, 60, 'links'), ('Ireland', 6, 60.5, 65, 'links'),
    ('Northern Ireland', 2.5, 64, 60, 'links'), ('Wales', 2.5, 58, 50, 'links'), ('Spain', 7, 63, 60, 'touch'),
    ('Portugal', 1.5, 52, 40, 'touch'), ('France', 9, 59, 55, 'complete'), ('Germany', 9, 56.5, 55, 'complete'),
    ('Netherlands', 3.5, 58, 50, 'complete'), ('Belgium', 2, 64, 55, 'complete'), ('Denmark', 4, 67, 65, 'complete'),
    ('Sweden', 7, 64.5, 70, 'complete'), ('Norway', 2.5, 66, 70, 'complete'), ('Finland', 2, 63, 60, 'complete'),
    ('Italy', 3.5, 60, 50, 'touch'), ('Austria', 2, 61, 50, 'complete'), ('Switzerland', 2, 54, 45, 'complete'),
    ('Czechia', 1.2, 50, 35, 'complete'), ('Poland', .8, 46, 30, 'raw'), ('Turkey', .6, 42, 25, 'raw'),
    ('United Arab Emirates', .8, 50, 30, 'raw'), ('Qatar', .3, 45, 20, 'raw'), ('Saudi Arabia', .5, 46, 25, 'raw'),
    ('Bahrain', .2, 44, 20, 'raw'), ('Oman', .2, 44, 20, 'raw'),
    ('South Africa', 10, 66, 55, 'striker'), ('Kenya', 1.2, 52, 25, 'raw'), ('Morocco', .8, 48, 25, 'raw'),
    ('Nigeria', .6, 45, 20, 'raw'), ('Egypt', .6, 44, 20, 'raw'), ('Zimbabwe', 1.0, 61, 35, 'striker'),
    ('Namibia', .4, 52, 30, 'striker'), ('Zambia', .4, 48, 20, 'raw'), ('Mauritius', .3, 48, 20, 'raw'),
    ('Japan', 40, 55.5, 35, 'precision'), ('South Korea', 18, 61, 50, 'precision'), ('China', 10, 56, 45, 'precision'),
    ('Taiwan', 3, 56.5, 45, 'precision'), ('India', 6, 55, 30, 'touch_sea'), ('Thailand', 5, 61, 40, 'touch_sea'),
    ('Malaysia', 2, 53, 35, 'touch_sea'), ('Singapore', 1, 52, 40, 'touch_sea'), ('Philippines', 2.2, 56, 35, 'touch_sea'),
    ('Indonesia', 1.5, 49, 25, 'touch_sea'), ('Vietnam', 1.2, 46, 25, 'touch_sea'),
    ('Australia', 16, 63, 70, 'striker'), ('New Zealand', 3, 62, 60, 'striker'), ('Fiji', .3, 52, 20, 'striker'),
)
NATIONS = {c: NationProfile(c, pool, dev, path, style) for c, pool, dev, path, style in _P}
assert set(NATIONS) == set(COUNTRIES), set(COUNTRIES) ^ set(NATIONS)

# Real-world reference: approximate nationality of the world top 200 men (mid-2020s rankings).
REAL_TOP200 = {
    'USA': 76, 'England': 15, 'Japan': 10, 'South Africa': 10, 'Australia': 9, 'South Korea': 8, 'Canada': 6,
    'Sweden': 6, 'Spain': 5, 'France': 5, 'Denmark': 5, 'Scotland': 4, 'Ireland': 3, 'Northern Ireland': 2,
    'Germany': 3, 'Norway': 3, 'China': 3, 'Thailand': 3, 'Belgium': 2, 'Italy': 2, 'Finland': 2, 'Argentina': 2,
    'Mexico': 2, 'New Zealand': 2, 'Austria': 1, 'Netherlands': 1, 'India': 1, 'Taiwan': 1, 'Philippines': 1,
    'Chile': 1, 'Colombia': 1, 'Zimbabwe': 1, 'Wales': 1,
}


def nations(overrides=None):
    """A fresh, editable copy of the starting nation profiles."""
    out = {c: replace(p, history=[]) for c, p in NATIONS.items()}
    for c, kw in (overrides or {}).items():
        out[c] = replace(out[c], **kw)
    return out
