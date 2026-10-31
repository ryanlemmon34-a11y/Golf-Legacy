"""Simulated seasonal climate: each round's wind and wetness from where a course is and the time of year.

This is bundled, offline, simulated climate -- general climatology by climate group, not a forecast, not
observed weather and not a live service. Every city in geography.py already carries a climate group and a
hemisphere; the tables below give, for each group and each local month (northern-hemisphere convention,
January first), how windy the month is relative to the course's typical wind and the chance that a round is
played wet (rain heavy enough to change how the course plays). Southern-hemisphere courses read the table
six months on (their January is a northern July), so seasons are opposite. Sources: textbook climatology of
each group (westerly storm tracks windiest and wettest in winter for oceanic coasts; dry Mediterranean
summers; summer thunderstorms in humid subtropical and continental interiors; tropical wet seasons in local
summer with stronger dry-season trades; spring winds and near-rainless deserts). The values are rounded,
plausible tendencies chosen for a game, not station data.

How a course's climate is set (all from the course itself, never from who is playing):
  - climate group and hemisphere: the course's city (geography.CITY_BY_NAME); a course with no city uses its
    country's most common group (hand-built test courses);
  - mean wind: the course's typical wind (its style plus coastal exposure: course_gen) times the month's
    factor; coastal courses swing more through the year (onshore gales in the stormy months, sea breezes
    otherwise): the month's deviation from average is 1.3 times larger;
  - wetness: the month's wet-round chance, the same for every course in that climate and month; how much a
    wet round softens the course depends on its style (sand-based links, sandbelt and heathland drain fast;
    municipal parkland holds water: STYLE_SOAK).

Each event draws a weather "system" for its week (its wind level, prevailing direction and how unsettled it
is) and each round draws its own wind, direction and whether it is wet, all from hashes of the event's seed,
so the same seed always gives the same conditions and a resumed save replays them exactly. Conditions
never cancel, shorten or delay a round: wet rounds are played, they only change how the ball behaves.

Holes have no surveyed orientation, so every course gets a stable routing: each hole's bearing (the compass
direction from tee to green) is derived from the course's identity alone (`hole_bearings`), the same for all
its layouts. Links run out and back (front nine one way, back nine the other); other courses turn freely.
Temperature and turf firmness by season are NOT modelled (an open decision for the owner).
"""
from __future__ import annotations

import hashlib
import math
import random
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache

from .geography import CITIES, CITY_BY_NAME, COUNTRIES

MODEL = 'seasonal-1'            # Season.weather for worlds using this model ('classic': flat draws, no direction)

# climate group: (wind factor by local month Jan..Dec, normalised below to an annual mean of 1.0;
#                 wet-round probability by local month)
_RAW = {
    'oceanic':       ((1.22, 1.18, 1.12, 1.00, 0.92, 0.86, 0.84, 0.86, 0.94, 1.04, 1.12, 1.20),
                      (.30, .26, .25, .21, .20, .18, .18, .20, .22, .27, .30, .31)),
    'continental':   ((1.08, 1.10, 1.18, 1.16, 1.04, 0.94, 0.86, 0.86, 0.92, 1.00, 1.08, 1.08),
                      (.12, .12, .15, .17, .20, .20, .18, .16, .15, .14, .14, .13)),
    'temperate':     ((1.10, 1.14, 1.16, 1.10, 1.00, 0.92, 0.88, 0.88, 0.94, 0.96, 1.00, 1.06),
                      (.10, .12, .15, .16, .18, .22, .20, .18, .20, .15, .12, .10)),
    'mediterranean': ((1.10, 1.08, 1.08, 1.02, 0.98, 0.96, 0.96, 0.94, 0.92, 0.94, 1.00, 1.08),
                      (.20, .18, .15, .11, .07, .03, .02, .02, .05, .11, .17, .20)),
    'subtropical':   ((1.02, 1.08, 1.16, 1.12, 1.00, 0.92, 0.88, 0.90, 0.94, 0.98, 1.00, 1.00),
                      (.10, .11, .12, .12, .15, .21, .24, .23, .18, .11, .09, .10)),
    'tropical':      ((1.10, 1.12, 1.10, 1.00, 0.94, 0.98, 1.00, 0.98, 0.92, 0.90, 0.94, 1.04),
                      (.08, .07, .09, .14, .22, .28, .30, .30, .28, .22, .14, .10)),
    'desert':        ((0.94, 1.00, 1.10, 1.16, 1.12, 1.06, 1.00, 0.98, 0.92, 0.88, 0.90, 0.94),
                      (.05, .05, .04, .03, .02, .01, .02, .02, .01, .02, .03, .05)),
    'alpine':        ((1.12, 1.12, 1.14, 1.08, 1.00, 0.92, 0.88, 0.88, 0.94, 1.00, 1.06, 1.10),
                      (.10, .10, .12, .15, .18, .21, .21, .19, .14, .12, .11, .10)),
}
CLIMATE = {k: (tuple(f * 12 / sum(w) for f in w), wet) for k, (w, wet) in _RAW.items()}
COASTAL_SWING = 1.3             # a coastal course's monthly wind deviation from average, scaled
# prevailing direction the wind blows FROM (compass degrees) by climate group; each city turns it by a stable
# amount (up to +/-40 degrees) and each week and round vary around it. Tropical trades blow from the
# north-east north of the equator and the south-east south of it.
PREVAILING = {'oceanic': 250, 'continental': 270, 'temperate': 250, 'mediterranean': 300, 'subtropical': 200,
              'tropical': 60, 'desert': 330, 'alpine': 270}
PREVAILING_SOUTH = {'tropical': 120}
# how much a wet round softens and slows the course, by style (1 = an ordinary parkland)
STYLE_SOAK = {'Links': 0.7, 'Sandbelt': 0.7, 'Heathland': 0.8, 'Desert': 0.8, 'Coastal': 0.9, 'Mountain': 0.9,
              'Parkland': 1.0, 'Woodland': 1.0, 'Tropical': 1.0, 'Municipal': 1.1}
MAX_WET = 0.85                  # a round is never certain to be wet


def _h(*parts):
    return int.from_bytes(hashlib.blake2b(':'.join(map(str, parts)).encode(), digest_size=8).digest(), 'big')


def month_of(week):
    """Calendar month (0 = January) of a week of the year (1-52)."""
    return max(0, min(11, (int(week) - 1) * 12 // 52))


_COUNTRY_CLIMATE = {c: Counter(x.climate for x in CITIES if x.country == c).most_common(1)[0][0]
                    for c in {x.country for x in CITIES}}


@dataclass(frozen=True)
class Climate:
    group: str
    south: bool
    coastal: bool
    prevailing: float           # degrees the wind usually blows from


@lru_cache(maxsize=4096)
def _climate(city, country, style):
    c = CITY_BY_NAME.get(city)
    if c is not None:
        group, country, coastal = c.climate, c.country, c.coastal
    else:
        group = _COUNTRY_CLIMATE.get(country, 'temperate')
        coastal = style in ('Links', 'Coastal')
    south = bool(COUNTRIES[country].south) if country in COUNTRIES else False
    base = PREVAILING_SOUTH.get(group, PREVAILING[group]) if south else PREVAILING[group]
    turn = (_h('prevailing', city or country) % 81) - 40
    return Climate(group, south, coastal, float((base + turn) % 360))


def climate_of(course):
    """The course's climate: from its city (its country's usual climate if it has none), never from a golfer."""
    return _climate(course.city or '', course.country or '', course.style or '')


def local_month(month, south):
    return (month + 6) % 12 if south else month


def seasonal(course, week):
    """(mean wind in mph, wet-round probability) for this course in this week of the year."""
    cl = climate_of(course)
    m = local_month(month_of(week), cl.south)
    wind, wet = CLIMATE[cl.group]
    f = wind[m]
    if cl.coastal:
        f = 1 + COASTAL_SWING * (f - 1)
    return course.typical_wind * f, wet[m]


def soak(course):
    """How much a wet round changes this course (by style; 1 = ordinary parkland)."""
    return STYLE_SOAK.get(course.style, 1.0)


def draw_conditions(course, week, rounds, pin_difficulty, seed):
    """{round: Conditions} for one event site: deterministic in (seed, round), seed being the site's own.

    Values are rounded before they are used (wind to 0.1 mph, direction to the degree, pins to 0.01), so
    what is archived is exactly what was played."""
    from .engine import Conditions
    mean, p_wet = seasonal(course, week)
    cl = climate_of(course)
    ev = random.Random(_h('weather', seed, 'event'))
    wind = max(0.0, ev.gauss(mean, 0.25 * mean + 1.0))        # the week's weather system
    unsettled = math.exp(ev.gauss(0.0, 0.6) - 0.18)            # mean 1: settled or unsettled week
    heading = cl.prevailing + ev.gauss(0.0, 40.0)
    pins = round(pin_difficulty, 2)
    out = {}
    for r in range(1, rounds + 1):
        rr = random.Random(_h('weather', seed, 'round', r))
        w = round(max(0.0, wind + rr.gauss(0.0, 0.2 * mean + 1.0)), 1)
        rain = rr.random() < min(MAX_WET, p_wet * unsettled)
        frm = int(round(heading + rr.gauss(0.0, 35.0))) % 360
        out[r] = Conditions(wind_mph=w, rain=rain, pin_difficulty=pins, wind_from=frm)
    return out


def archived(cond):
    """A round's conditions as archived: [wind mph, wet 0/1, pin difficulty, wind direction (from, degrees)];
    the classic model (no direction) keeps its three values."""
    row = [round(cond.wind_mph, 1), int(cond.rain), round(cond.pin_difficulty, 2)]
    if cond.wind_from is not None:
        row.append(int(cond.wind_from))
    return row


# ---- routing ------------------------------------------------------------------------------------------------
@lru_cache(maxsize=2048)
def _bearings(key, style, numbers):
    rng = random.Random(_h('routing', key))
    out = {}
    if style == 'Links':                                       # out and back
        base = rng.random() * 360
        for i, n in enumerate(numbers):
            out[n] = (base + (0 if i < len(numbers) // 2 else 180) + rng.gauss(0, 30)) % 360
    else:
        b = rng.random() * 360
        for n in numbers:
            out[n] = b % 360
            b += (1 if rng.random() < 0.5 else -1) * rng.uniform(50, 180)
    return out


def hole_bearings(course):
    """{hole number: compass bearing from tee to green}: a stable routing from the course's identity (shared by
    all its layouts), since no hole has a surveyed orientation."""
    return _bearings(course.familiarity_key, course.style or '', tuple(h.number for h in course.holes))


_GEO = {}


def hole_geometry(course, wind_from):
    """{hole number: (along, cross)} for a wind blowing from `wind_from`: along +1 straight into the golfer's
    face (headwind), -1 straight behind (tailwind); cross 0..1 the share across the line of play."""
    key = (course.familiarity_key, course.style, wind_from)
    geo = _GEO.get(key)
    if geo is None:
        if len(_GEO) > 512:
            _GEO.clear()
        geo = {}
        for n, b in hole_bearings(course).items():
            rel = math.radians(wind_from - b)
            geo[n] = (math.cos(rel), abs(math.sin(rel)))
        _GEO[key] = geo
    return geo


_POINTS = ('N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW')


def compass(deg):
    return _POINTS[int((deg % 360) / 22.5 + 0.5) % 16]


def describe(row):
    """Readable text of an archived round's conditions (3 values: classic model; 4: with direction)."""
    if not row:
        return 'not recorded'
    wind, wet, pins = row[0], row[1], row[2]
    frm = f' from the {compass(row[3])}' if len(row) > 3 and row[3] is not None else ''
    return f'wind {wind} mph{frm}, {"wet" if wet else "dry"}, pin difficulty {pins}'
