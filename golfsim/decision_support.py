"""Evidence for one week's choice -- play, train or rest -- side by side (read only; HAL presents it).

Only facts the engine's rules use or the career itself recorded: the events the golfer may enter that week (cost,
the field rule, what a result there unlocks -- golfsim.opportunities), the training categories (the career's own
fallible scouting grades and observed levels -- golfsim.scouting -- never ceilings, perceived gaps or promised
gains), and the load: recent weeks played (the career's weekly recaps) and the engine's fatigue forecasts
(career.readiness). Nothing here changes the world or draws a random number.
"""
from __future__ import annotations


def week_compare(season, c, g, year, week, opp=None):
    """{week, play: [...], train: [...], rest: {...}, load: {...}} for the controlled golfer's week."""
    from . import career as CA
    from . import opportunities as O
    from . import scouting
    opts = CA.week_options(season, g, year, week)
    opp = O.opportunities(season, g.id, year, week) if opp is None else opp
    by_event = {}
    for o in opp:
        if o['event']['week'] == week:
            by_event.setdefault(o['event']['id'], []).append(o)
    from . import entry_outlook as EO
    held = O.held_places(season, g.id, year, week)
    inj = opts.get('injured_until')
    play = []
    for row in opts['events']:
        play.append({'event_id': row['event_id'], 'name': row.get('name'), 'eligible': row.get('eligible'),
                     'why': row.get('why'), 'cost': row.get('cost'), 'tour': row.get('tour'),
                     'opportunities': by_event.get(row['event_id'], []),
                     'last_edition': O.field_history(season, row['event_id'].split(':', 1)[1], year),
                     'course_fit': _course_fit(season, g, row['event_id']),
                     'entry_outlook': EO.outlook(season, g, year, week, row, held, inj), 'route': 'entry'})
    for row in opts['selected']:
        play.append({'event_id': row['event_id'], 'name': row.get('name'), 'eligible': None,
                     'why': row.get('rule'), 'cost': None, 'tour': row.get('tour'), 'selected_field': True,
                     'opportunities': by_event.get(row['event_id'], []),
                     'course_fit': _course_fit(season, g, row['event_id']),
                     'entry_outlook': EO.outlook(season, g, year, week, row, held, inj),
                     'route': EO.route(season, row)})
    sc = scouting.view(season, c, g.id)
    obs = getattr(c, 'observations', {}).get(g.id, [])
    levels = obs[-1]['levels'] if obs else {}
    order = sorted(levels, key=lambda k: (levels[k], k))
    train = []
    for cat in sc['categories']:
        k = cat['category']
        train.append({'category': k, 'grade': cat['grade'], 'confidence': cat['confidence'],
                      'observed_level': round(levels[k], 1) if k in levels else None,
                      'weakest_rank': order.index(k) + 1 if k in levels else None,
                      'observed_as_of': list(sc['as_of']) if sc['as_of'] else None})
    recent = [(w, r) for (y, w), r in sorted(getattr(c, 'weekly_recaps', {}).items())
              if y == year and w < week and r.get('golfer_id', g.id) == g.id]
    last = lambda n: sum(1 for w, r in recent if w >= week - n and r['activity'] == 'play')
    ready = CA.readiness(season, g, year, week)
    return {'week': week, 'year': year, 'play': play, 'train': train,
            'rest': {'fatigue_after': ready['rest_after']},
            'load': {'fatigue': ready['fatigue'], 'performance_threshold': ready['performance_threshold'],
                     'train_fatigue_after': ready['train_after'], 'rest_fatigue_after': ready['rest_after'],
                     'played_last_4': last(4), 'played_last_8': last(8), 'injured_until': ready['injured_until'],
                     'recorded_weeks': len(recent)}}


def _course_fit(season, g, event_id):
    """course_fit.evidence for one edition id ('<year>:<series id>'; None where the world does not weigh course fit)."""
    from . import course_fit as CF
    year = int(event_id.split(':', 1)[0])
    ed = next((e for e in season.cal.editions(year) if e.event_id == event_id), None)
    return None if ed is None else CF.evidence(season, g, ed)


def block_compare(season, c, g, cursor):
    """{week: week_compare(...)} for the open weeks of the current four-week period (the planner's weeks), with the
    opportunities worked out once; {} outside a season's weeks."""
    from . import career as CA
    from . import opportunities as O
    y, w = cursor['year'], cursor['week']
    if cursor['phase'] == 'end' or g is None or g.lifestyle == 'retired':
        return {}
    weeks = CA.open_weeks(cursor, CA.block_start(w))
    if not weeks:
        return {}
    opp = O.opportunities(season, g.id, y, min(weeks))
    return {str(x): week_compare(season, c, g, y, x, opp) for x in weeks}
