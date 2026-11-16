"""Course fit and recorded familiarity in choosing events (calendar v3 worlds; docs/career/COURSE_FIT.md).

A small, bounded preference -- the same for AI golfers and the player's evidence:

* what a course asks for, from its actual characteristics (course.Hole / Course): length (long game, physical),
  fairway width and rough (long-game accuracy), green size and greenside bunkers (short game), green speed and
  contours (putting), water / out-of-bounds and wind (mental) -- each a z-score against the course library's
  measured means (seed-independent constants below), clipped to [-1, 1];
* the golfer's own profile from their CURRENT attributes (each category's level against their own average: their
  relative strengths), never ceilings or potential;
* recorded familiarity: competitive rounds the golfer has played on that course (Golfer.familiarity), through the
  engine's own curve (familiarity.value). The regional baseline is not counted here (it is a playing rule).
  Events played at several courses (qualifier heats) get no course term for anyone: the course is not known at entry.

`points` = FIT_WEIGHT x fit (fit in [-1, 1]) + FAM_WEIGHT x familiarity value (0..1): at most +-3 and +2 points of
an event's appeal (Season.event_value), against prestige, travel, costs, fatigue and stakes measured in tens of
points. It reorders close choices; it overrides no eligibility, budget or selection rule; it changes nothing in how
a tournament is played. No random draw.
"""
from __future__ import annotations

from statistics import mean

from . import familiarity as FAM

FIT_WEIGHT = 3.0
FAM_WEIGHT = 2.0
FIT_SCALE = 8.0           # attribute points of relative strength that make a full-strength match (with demand 1)
CATS = ('physical', 'long_game', 'short_game', 'putting', 'mental')

# measured on the course library (all 1,077 layouts, calendar v3, seed 11): mean, standard deviation
REF = {'yards': (6440.0, 470.0), 'fairway': (30.6, 4.0), 'rough': (0.41, 0.17), 'green': (14.2, 0.84),
       'gsb': (0.56, 0.10), 'speed': (10.5, 1.05), 'slope': (0.54, 0.10), 'hazard': (0.19, 0.09),
       'wind': (5.2, 4.0)}

_DEMAND = {}


def _z(key, x):
    m, sd = REF[key]
    return (x - m) / sd


def _clip(x):
    return max(-1.0, min(1.0, x))


def demand(course):
    """{category: -1..1} what this course asks for more (+) or less (-) than a typical course."""
    key = course.layout_id
    hit = _DEMAND.get(key)
    if hit is not None:
        return hit
    H = course.holes
    length = _z('yards', sum(h.plays for h in H))
    narrow = -_z('fairway', mean(h.fairway_width for h in H))
    rough = _z('rough', mean(h.rough_severity for h in H))
    small = -_z('green', mean(h.green_radius for h in H))
    bunkers = _z('gsb', mean(h.greenside_bunkers for h in H))
    speed = _z('speed', mean(h.green_speed for h in H))
    slope = _z('slope', mean(h.green_slope for h in H))
    hazard = _z('hazard', mean(((h.left in ('water', 'ob')) + (h.right in ('water', 'ob')) + (h.green_water != ''))
                               / 3 for h in H))
    wind = _z('wind', mean(h.wind_exposure for h in H) * course.typical_wind)
    out = {'physical': _clip(0.6 * length),
           'long_game': _clip(0.4 * length + 0.3 * narrow + 0.3 * rough),
           'short_game': _clip(0.5 * small + 0.5 * bunkers),
           'putting': _clip(0.5 * speed + 0.5 * slope),
           'mental': _clip(0.5 * hazard + 0.5 * wind)}
    _DEMAND[key] = out
    return out


def profile(g):
    """{category: level - the golfer's own average} from current attributes (relative strengths)."""
    from .development import CATEGORIES
    lv = {c: sum(g.attrs[k] for k in CATEGORIES[c]) / len(CATEGORIES[c]) for c in CATS}
    avg = sum(lv.values()) / len(lv)
    return {c: lv[c] - avg for c in CATS}, lv


def evaluate(g, course, prof=None):
    """{fit, familiarity_rounds, familiarity, points, factors} for golfer g at `course` (read only). `prof`: profile(g)
    already worked out for this golfer and week (the same numbers). factors: per category, what the course asks
    (demand, -1..1) and the points it gives before the overall fit is clipped to [-1, 1]; attribute levels are not
    shown (the player's own levels are seen through scouting)."""
    d = demand(course)
    rel, _ = prof or profile(g)
    fit = _clip(sum(d[c] * rel[c] for c in CATS) / (FIT_SCALE * len(CATS)) * 2)
    rounds = g.familiarity.get(course.familiarity_key, 0.0)
    fam = FAM.value(rounds)
    return {'fit': round(fit, 4), 'familiarity_rounds': round(rounds, 2), 'familiarity': round(fam, 4),
            'points': round(FIT_WEIGHT * fit + FAM_WEIGHT * fam, 4),
            'factors': [{'category': c, 'demand': round(d[c], 3),
                         'points': round(FIT_WEIGHT * d[c] * rel[c] / (FIT_SCALE * len(CATS)) * 2, 2)}
                        for c in CATS]}


def points(season, g, ed, gw=None):
    """The appeal points course fit and familiarity add to an event for this golfer (0 where it is off). `gw`: the
    golfer's week (Season.golfer_week), where the profile is kept for the week's other events."""
    if not season.cal.spec.course_fit:
        return 0.0
    vs = season.venues(ed.year)[ed.event_id]
    if len(vs) != 1:
        return 0.0                                           # several sites: the course is not known at entry
    v = vs[0]
    prof = None
    if gw is not None:
        prof = gw.get('fit_profile')
        if prof is None:
            prof = gw['fit_profile'] = profile(g)
    return evaluate(g, season.lib.course(v), prof)['points']


def evidence(season, g, ed):
    """The same evaluation for the player's planner (career.week_compare), with the course named; None when the
    world's rules do not weigh course fit (calendars before v3)."""
    if not season.cal.spec.course_fit:
        return None
    vs = season.venues(ed.year)[ed.event_id]
    if len(vs) != 1:
        return {'course': None, 'sites': len(vs), 'points': 0.0, 'fit': None, 'familiarity': None,
                'weights': {'fit': FIT_WEIGHT, 'familiarity': FAM_WEIGHT},
                'note': 'Played at several courses: the course is not known when entering, so course fit and '
                        'familiarity do not count for anyone.'}
    v = vs[0]
    course = season.lib.course(v)
    out = evaluate(g, course)
    out.update({'course': course.name, 'course_id': v.course_id, 'layout': v.layout,
                'weights': {'fit': FIT_WEIGHT, 'familiarity': FAM_WEIGHT},
                'note': 'How the course suits your current game and how well you know it: a small part of an '
                        'event\'s appeal for every golfer. Not a forecast of your result.', 'sites': 1})
    return out
