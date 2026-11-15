"""Fallible potential estimates for the controlled golfer: a letter grade per training category (A-F) for the level
the golfer looks able to reach, as their coach (or, without one, the golfer themselves) reads it.

Built like a coach's scouting of a young player (staff.scouting_estimate), per category, from what can be watched:

* the category level as OBSERVED -- the career records an observation (with observation error) when control starts
  and at each season's end (`observe`), and keeps them (career.observations);
* the growth typical for the golfer's age (the population's public aging curve);
* the improvement actually observed between the last two observations, against that typical growth;
* through the judge's error: a persistent, seeded view per judge, golfer and category (a coach does not re-roll their
  opinion), wider for a poor scout (or a poor judge of their own game), firming with the seasons they have watched.

Never reads ceilings, potential, peak age or aging rate, and is not the current level: grades can be wrong in both
directions, and they move only when a new observation is made. Each observation's grades are kept (history).
All draws use their own seeded generators: no random stream of the world is touched.

Grades are for the projected category level against the world's standards (medians measured on generated worlds,
seed 11, full scale): A Premier standard (73+), B Challenger (65+), C regional / mini tour (56+), D college / club
(48+), F below.
"""
from __future__ import annotations

import random

from .development import CATEGORIES

GRADES = (('A', 73.0), ('B', 65.0), ('C', 56.0), ('D', 48.0), ('F', float('-inf')))
OBSERVE_SD = 2.0                  # how far an observed category level can be from the true one
CATS = tuple(CATEGORIES)


def grade(level):
    return next(g for g, bar in GRADES if level >= bar)


def _level(g, cat):
    ks = CATEGORIES[cat]
    return sum(g.attrs[k] for k in ks) / len(ks)


def _obs(c):
    if not hasattr(c, 'observations'):
        c.observations = {}
    return c.observations


def observe(season, c, gid, year, week):
    """Record one observation of golfer `gid` (once per (year, week)): each category level seen with error, who
    judged it (their coach then, or None), and the grades it gives. Returns the observation."""
    g = season.g.get(gid)
    if g is None:
        return None
    rows = _obs(c).setdefault(gid, [])
    for o in rows:
        if (o['year'], o['week']) == (year, week):
            return o
    coach = season.staff.coach(gid)
    levels = {cat: round(_level(g, cat) + random.Random(f'{season.seed}:observe:{gid}:{cat}:{year}:{week}')
                         .gauss(0, OBSERVE_SD), 2) for cat in CATS}
    o = {'year': year, 'week': week, 'age': g.age(year), 'levels': levels,
         'coach': coach.id if coach is not None else None, 'coach_name': coach.name if coach is not None else None}
    rows.append(o)
    o['estimates'] = _estimate(season, c, gid, rows)
    return o


def _seasons_watched(season, coach_id, gid, year):
    st = season.staff
    starts = [s.start[0] for s in st.rel.of_golfer(gid, 'coach') if s.staff == coach_id]
    return max(1, year - min(starts) + 1) if starts else 1


def _estimate(season, c, gid, rows):
    """The grades from the observations so far (the last one and the one before it)."""
    from .population import age_deficit
    from .staff import firming
    from .development import judgement
    o = rows[-1]
    prev = rows[-2] if len(rows) > 1 else None
    g = season.g[gid]
    age, year = o['age'], o['year']
    typical = age_deficit(age, 27.0) - age_deficit(age + 1, 27.0)
    if o['coach'] is not None:
        coach = season.staff.coaches.get(o['coach'])
        scout = coach.scouting if coach is not None else 50.0
        sd = 3 + 12 * (1 - scout / 100)
        firm = firming(_seasons_watched(season, o['coach'], gid, year))
        judge = f'c{o["coach"]}'
    else:
        sd = 3 + 12 * (1 - judgement(g))
        firm = firming(len(rows))
        judge = 'self'
    out = {}
    for cat in CATS:
        seen = o['levels'][cat]
        if prev is not None and prev['year'] < year:
            recent = (seen - prev['levels'][cat]) / (year - prev['year'])
            trend = 1.5 * (recent - typical)
        else:
            recent, trend = None, 0.0
        view = random.Random(f'{season.seed}:catview:{judge}:{gid}:{cat}').gauss(0, sd)
        projected = seen + age_deficit(age, 27.0) + trend + firm * view
        n = len(rows)
        confidence = 'high' if n >= 3 and sd * firm <= 6 else 'medium' if n >= 2 else 'low'
        out[cat] = {'grade': grade(projected), 'confidence': confidence, 'seen': round(seen, 1),
                    'recent': None if recent is None else round(recent, 1), 'typical': round(typical, 1)}
    return out


def view(season, c, gid):
    """The read model (career.view()['scouting']): {as_of, source, judge, categories: [{category, grade, confidence,
    explanation, history: [{year, week, grade}]}]}; grades None before the first observation."""
    rows = getattr(c, 'observations', {}).get(gid, [])
    if not rows:
        return {'as_of': None, 'source': None, 'judge': None,
                'categories': [{'category': cat, 'grade': None, 'confidence': None,
                                'explanation': 'Not scouted yet: the first assessment is made at the end of a season '
                                               'played under your control.', 'history': []} for cat in CATS]}
    o = rows[-1]
    who = f'Coach {o["coach_name"]}' if o['coach'] is not None else 'Your own'
    cats = []
    for cat in CATS:
        e = o['estimates'][cat]
        trend = ('' if e['recent'] is None else
                 f', {"up" if e["recent"] >= 0 else "down"} {abs(e["recent"]):.1f} a season since the last look')
        cats.append({'category': cat, 'grade': e['grade'], 'confidence': e['confidence'],
                     'explanation': (f'{who} read ({o["year"]}, week {o["week"]}): {cat.replace("_", " ")} looks about '
                                     f'{e["seen"]:.0f}{trend}; at {o["age"]} a golfer typically still gains about '
                                     f'{e["typical"]:.1f} a year. An estimate, not a certainty.'),
                     'history': [{'year': r['year'], 'week': r['week'], 'grade': r['estimates'][cat]['grade']}
                                 for r in rows]})
    return {'as_of': [o['year'], o['week']], 'source': 'coach' if o['coach'] is not None else 'self',
            'judge': o['coach_name'], 'categories': cats}
