"""Fallible potential estimates for the controlled golfer: a letter grade per training category (A-F) for the level
the golfer looks able to reach, as their coach (or, without one, the golfer themselves) reads it.

Built like a coach's scouting of a young player (staff.scouting_estimate), per category, from what can be watched:

* the category level as OBSERVED -- the career records an observation (with observation error) when control starts,
  at the start of each four-week period, the first week after a change of coach, and at each season's end
  (`observe`, called by the career's gate as the world advances, never by a page view), and keeps them
  (career.observations); the level read is the mean of the looks of the last WINDOW weeks;
* the growth typical for the golfer's age (the population's public aging curve);
* the improvement actually observed over at least TREND_MIN weeks (the look nearest a season back, annualised),
  against that typical growth -- none until such a span has been watched (and the read says so);
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
WINDOW = 12                       # weeks of looks averaged into the level read
TREND_MIN, TREND_MAX = 26, 104    # weeks: the span an observed trend needs (and the longest one used)
REASONS = ('start', 'period', 'coach_change', 'season_end')
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


def _abs(o):
    return o['year'] * 52 + o['week']


def observe(season, c, gid, year, week, reason='period'):
    """Record one observation of golfer `gid` (once per (year, week)): each category level seen with error, who
    judged it (their coach then, or None), why it was made (REASONS) and the read it gives. Returns the observation."""
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
    o = {'year': year, 'week': week, 'age': g.age(year), 'levels': levels, 'reason': reason,
         'coach': coach.id if coach is not None else None, 'coach_name': coach.name if coach is not None else None}
    rows.append(o)
    rows.sort(key=_abs)
    o['estimates'] = _estimate(season, c, gid, rows[:rows.index(o) + 1])
    return o


def due(season, c, gid, year, week):
    """Why an observation is due at this week's gate (a REASONS code), or None: the start of a period, or the first
    week after the golfer's coach changed since the last look."""
    from .career import block_start
    rows = getattr(c, 'observations', {}).get(gid, [])
    if any((o['year'], o['week']) == (year, week) for o in rows):
        return None
    if week == block_start(week):
        return 'period'
    coach = season.staff.coach(gid)
    if rows and rows[-1]['coach'] != (coach.id if coach is not None else None):
        return 'coach_change'
    return None


def _seasons_watched(season, coach_id, gid, year):
    st = season.staff
    starts = [s.start[0] for s in st.rel.of_golfer(gid, 'coach') if s.staff == coach_id]
    return max(1, year - min(starts) + 1) if starts else 1


def _seen(rows, upto):
    """The level read at observation index `upto`: the mean of the looks of the WINDOW weeks up to it."""
    t = _abs(rows[upto])
    near = [r for r in rows[:upto + 1] if t - _abs(r) < WINDOW]
    return {cat: sum(r['levels'][cat] for r in near) / len(near) for cat in CATS}, len(near)


def _estimate(season, c, gid, rows):
    """The read at the last observation in `rows` (chronological, all earlier looks of this golfer)."""
    from .population import age_deficit
    from .staff import firming
    from .development import judgement
    i = len(rows) - 1
    o = rows[i]
    g = season.g[gid]
    age, year = o['age'], o['year']
    typical = age_deficit(age, 27.0) - age_deficit(age + 1, 27.0)
    seen, n_near = _seen(rows, i)
    back = [j for j in range(i) if TREND_MIN <= _abs(o) - _abs(rows[j]) <= TREND_MAX]
    j = min(back, key=lambda k: (abs(_abs(o) - _abs(rows[k]) - 52), -k)) if back else None
    if j is not None:
        then, _ = _seen(rows, j)
        gap = _abs(o) - _abs(rows[j])
    years = len({r['year'] for r in rows})
    if o['coach'] is not None:
        coach = season.staff.coaches.get(o['coach'])
        scout = coach.scouting if coach is not None else 50.0
        sd = 3 + 12 * (1 - scout / 100)
        firm = firming(_seasons_watched(season, o['coach'], gid, year))
        judge = f'c{o["coach"]}'
    else:
        sd = 3 + 12 * (1 - judgement(g))
        firm = firming(years)
        judge = 'self'
    span = _abs(o) - _abs(rows[0])
    spread = sd * firm
    out = {}
    for cat in CATS:
        if j is not None:
            recent = (seen[cat] - then[cat]) * 52 / gap
            trend = 1.5 * (recent - typical)
        else:
            recent, trend = None, 0.0
        view = random.Random(f'{season.seed}:catview:{judge}:{gid}:{cat}').gauss(0, sd)
        gain = age_deficit(age, 27.0) + trend + firm * view
        projected = seen[cat] + gain
        confidence = ('high' if span >= 104 and spread <= 6 else 'medium' if recent is not None else 'low')
        out[cat] = {'grade': grade(projected), 'confidence': confidence, 'seen': round(seen[cat], 1),
                    'recent': None if recent is None else round(recent, 1), 'typical': round(typical, 1),
                    'gain': round(gain, 2), 'spread': round(spread, 2), 'looks': n_near,
                    'trend_weeks': gap if j is not None else None}
    return out


ROOM = (('little', 1.5), ('some', 5.0), ('considerable', float('inf')))


def growth_room(e, source):
    """The judge's qualitative growth-room estimate for one category from its read `e`: their projected gain (the
    age curve, the observed trend if any, their own persistent error), never a ceiling and never a grade minus a
    level. Uncertainty from the judge's remaining error, one step wider without an observed trend."""
    gain = e.get('gain')
    if gain is None:                                  # (a read from before this was kept)
        return {'label': 'unknown', 'uncertainty': None, 'basis': [],
                'explanation': 'Not assessed in this read: the next look will say.'}
    label = next(name for name, bar in ROOM if gain <= bar)
    steps = ('narrow', 'moderate', 'wide')
    k = 0 if e['spread'] <= 3 else 1 if e['spread'] <= 6 else 2
    if e['recent'] is None:
        k = min(2, k + 1)
    basis = ['age_curve'] + (['observed_trend'] if e['recent'] is not None else []) + [f'{source}_read']
    who = 'Your coach' if source == 'coach' else 'You'
    trend = (f'what they have seen over {e["trend_weeks"]} weeks' if e['recent'] is not None
             else 'no observed trend yet (needs at least 26 weeks of looks)')
    return {'label': label, 'uncertainty': steps[k], 'basis': basis,
            'explanation': f'{who} see {label} room to grow here, judged from age and {trend}. An opinion with '
                           f'{steps[k]} uncertainty, not a limit.'}


def view(season, c, gid):
    """The read model (career.view()['scouting']): {as_of, source, judge, categories: [{category, grade, confidence,
    explanation, history: [{year, week, grade}]}]}; grades None before the first observation."""
    rows = getattr(c, 'observations', {}).get(gid, [])
    if not rows:
        return {'as_of': None, 'source': None, 'judge': None,
                'categories': [{'category': cat, 'grade': None, 'confidence': None,
                                'growth_room': {'label': 'unknown', 'uncertainty': None, 'basis': [],
                                                'explanation': 'No evidence yet: nobody has watched this golfer.'},
                                'evidence': {'observations': 0, 'looks_in_read': 0, 'span_weeks': 0,
                                             'trend_available': False, 'trend_weeks': None},
                                'explanation': 'Not scouted yet: the first look is taken when control starts, then '
                                               'at each period.', 'history': []} for cat in CATS]}
    o = rows[-1]
    who = f'Coach {o["coach_name"]}' if o['coach'] is not None else 'Your own'
    cats = []
    for cat in CATS:
        e = o['estimates'][cat]
        trend = ('' if e['recent'] is None else
                 f', {"up" if e["recent"] >= 0 else "down"} {abs(e["recent"]):.1f} a season over the last '
                 f'{e.get("trend_weeks")} weeks of looks')
        src = 'coach' if o['coach'] is not None else 'self'
        cats.append({'category': cat, 'grade': e['grade'], 'confidence': e['confidence'],
                     'growth_room': growth_room(e, src),
                     'evidence': {'observations': len(rows), 'looks_in_read': e.get('looks', 1),
                                  'span_weeks': _abs(o) - _abs(rows[0]), 'trend_available': e['recent'] is not None,
                                  'trend_weeks': e.get('trend_weeks')},
                     'explanation': (f'{who} read ({o["year"]}, week {o["week"]}): {cat.replace("_", " ")} looks about '
                                     f'{e["seen"]:.0f}{trend}; at {o["age"]} a golfer typically still gains about '
                                     f'{e["typical"]:.1f} a year. An estimate, not a certainty.'),
                     'history': [{'year': r['year'], 'week': r['week'], 'grade': r['estimates'][cat]['grade'],
                                  'reason': r.get('reason')} for r in rows]})
    return {'as_of': [o['year'], o['week']], 'source': 'coach' if o['coach'] is not None else 'self',
            'judge': o['coach_name'], 'categories': cats}
