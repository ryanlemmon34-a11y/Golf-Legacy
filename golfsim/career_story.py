"""The career's story and the player's own goals (read models and one persisted, optional command).

* `timeline(season, career)`: a dated list of what happened to the golfers the player controlled -- control stints,
  every decision the player answered, trophies, wins and top-ten finishes from the weekly recaps, coach and caddie
  partnerships begun and ended -- from records only; nothing invented, nothing inferred.
* Goals: the player may set optional goals (`set_goal`, `drop_goal`: versioned, exactly-once commands through
  career.apply). They change nothing in the simulation: no rule reads them. Progress is derived from records:
  - `win`: win a series (a recorded winner) by the end of `by_year`;
  - `play_in`: be in a series' field (a recorded finish line) by the end of `by_year`;
  - `world_rank` / `amateur_rank`: be in the top `top` of that ranking (the current published position) by
    the end of `by_year`.
  Status: 'active', 'achieved' (with the date it was first recorded), 'missed' (the year ended), 'dropped'.
"""
from __future__ import annotations

GOAL_KINDS = ('win', 'play_in', 'world_rank', 'amateur_rank')
MAX_GOALS = 5


class GoalError(ValueError):
    pass


def _goals(c):
    if not hasattr(c, 'goals'):
        c.goals = []
    return c.goals


def set_goal(season, c, cursor, action):
    """Add one goal for the controlled golfer: action['goal'] = {kind, by_year, series_id? | top?}."""
    from .career import CareerError
    g = action.get('goal') or {}
    kind = g.get('kind')
    y = cursor['year']
    if kind not in GOAL_KINDS:
        raise CareerError(f'Choose a goal kind: {", ".join(GOAL_KINDS)}.')
    by = g.get('by_year')
    if not isinstance(by, int) or not y <= by <= y + 10:
        raise CareerError(f'Choose a year from {y} to {y + 10}.')
    goal = {'id': None, 'kind': kind, 'by_year': by, 'golfer_id': c.golfer_id, 'set': [y, cursor['week']],
            'status': 'active', 'dropped': None}
    if kind in ('win', 'play_in'):
        sid = g.get('series_id')
        if sid not in season.cal.by_id:
            raise CareerError('Choose an event of this world\'s calendar.')
        goal['series_id'] = sid
    else:
        top = g.get('top')
        if not isinstance(top, int) or not 1 <= top <= 1000:
            raise CareerError('Choose a ranking position from 1 to 1000.')
        goal['top'] = top
    active = [x for x in _goals(c) if x['status'] == 'active' and x['golfer_id'] == c.golfer_id]
    if len(active) >= MAX_GOALS:
        raise CareerError(f'At most {MAX_GOALS} goals at a time: drop one first.')
    c.seq += 1
    goal['id'] = f'G{c.seq}'
    _goals(c).append(goal)
    c._bump()
    return {'ok': True, 'goal': goal['id']}


def drop_goal(season, c, cursor, action):
    from .career import CareerError
    gid = action.get('goal_id')
    goal = next((x for x in _goals(c) if x['id'] == gid), None)
    if goal is None or goal['status'] != 'active':
        raise CareerError('No such active goal.')
    goal['status'] = 'dropped'
    goal['dropped'] = [cursor['year'], cursor['week']]
    c._bump()
    return {'ok': True}


def _achieved(season, goal):
    """(year, week) the goal was first met on the records, or None."""
    gid, sid = goal['golfer_id'], goal.get('series_id')
    start = goal['set'][0]
    if goal['kind'] == 'win':
        for (s, y), sites in sorted(season.ctx.results.items(), key=lambda kv: kv[0][1]):
            if s == sid and start <= y <= goal['by_year'] and any(p == 1 and x == gid for rows in sites.values()
                                                                  for x, p in rows):
                return [y, season.cal.by_id[sid].week]
        return None
    if goal['kind'] == 'play_in':
        for (s, y), sites in sorted(season.ctx.results.items(), key=lambda kv: kv[0][1]):
            if s == sid and start <= y <= goal['by_year'] and any(x == gid for rows in sites.values() for x, _ in rows):
                return [y, season.cal.by_id[sid].week]
        return None
    return None


def goals_view(season, c, cursor):
    """[{id, kind, series_id?, label?, top?, by_year, status, achieved, progress}] for every goal set (newest first).
    Status is derived: an active goal is 'achieved' once the records show it, 'missed' once its year has ended."""
    from . import event_labels as EL
    y, w = cursor['year'], cursor['week']
    out = []
    for goal in reversed(_goals(c)):
        st, ach, progress = goal['status'], None, None
        if goal['kind'] in ('win', 'play_in'):
            ach = _achieved(season, goal)
        else:
            pos = (season.wr_pos if goal['kind'] == 'world_rank' else season.am_pos).get(goal['golfer_id'])
            progress = {'position': pos}
            if pos is not None and pos <= goal['top'] and y <= goal['by_year']:
                ach = [y, w]
        if st == 'active':
            if ach is not None:
                st = 'achieved'
            elif y > goal['by_year']:
                st = 'missed'                        # (its last season has ended)
        row = {'id': goal['id'], 'kind': goal['kind'], 'by_year': goal['by_year'], 'status': st, 'achieved': ach,
               'progress': progress, 'set': list(goal['set']), 'golfer_id': goal['golfer_id']}
        if 'series_id' in goal:
            row['series_id'] = goal['series_id']
            row['label'] = EL.label(season.cal, goal['series_id'])
        if 'top' in goal:
            row['top'] = goal['top']
        out.append(row)
    return out


def _tour_name(key):
    from .calendar import TOUR_BY_KEY
    t = TOUR_BY_KEY.get(key)
    return t.name if t else (key or 'no tour')


def status_text(a, b):
    """One logged change of status / tour / lifestyle, in words."""
    if a['status'] == 'amateur' and b['status'] == 'pro':
        return f'Turned professional ({_tour_name(b["tour"])}).'
    if b['status'] == 'club_pro' and a['status'] != 'club_pro':
        return 'Became a club professional.'
    if b['status'] == 'amateur' and a['status'] != 'amateur':
        return f'Regained amateur status ({_tour_name(b["tour"])}).'
    if a['tour'] != b['tour']:
        return f'Moved from {_tour_name(a["tour"])} to {_tour_name(b["tour"])}.'
    if a['lifestyle'] != b['lifestyle']:
        return f'Now playing {b["lifestyle"].replace("_", " ")}.'
    return 'Status changed.'


def timeline(season, c):
    """[{date: [year, week], kind, text, golfer_id}] oldest first, from records only."""
    from . import awards
    out = []
    for st in getattr(c, 'stints', []):
        g = season.g.get(st['golfer_id'])
        name = g.name if g else str(st['golfer_id'])
        out.append({'date': list(st['from']), 'kind': 'control', 'text': f'You took control of {name}.',
                    'golfer_id': st['golfer_id']})
        if st['to']:
            out.append({'date': list(st['to']), 'kind': 'control', 'text': f'{name} returned to AI control.',
                        'golfer_id': st['golfer_id']})
    for d in c.decisions.values():
        if d['status'] in ('accepted', 'declined', 'resolved', 'withdrawn') and d.get('resolved'):
            out.append({'date': list(d['resolved']['at']), 'kind': 'decision',
                        'text': f'{d["text"].split(". ")[0]}: {d["resolved"]["text"]}.', 'golfer_id': c.controlled_at(
                            *d['resolved']['at']) if hasattr(c, 'controlled_at') else c.golfer_id})
    for st in getattr(c, 'stints', []):
        for t in awards.trophies(season, st['golfer_id'], c):
            if t['during_control']:
                out.append({'date': [t['year'], season.cal.by_id[t['series_id']].week], 'kind': 'trophy',
                            'text': f'Won the {t["event_name"]} ({t["year"]}).', 'golfer_id': st['golfer_id']})
    for (y, w), r in sorted(getattr(c, 'weekly_recaps', {}).items()):
        for e in r.get('events', []):
            if e.get('position') is not None and e['position'] <= 10 and e['position'] != 1:
                out.append({'date': [y, w], 'kind': 'result', 'golfer_id': r.get('golfer_id', c.golfer_id),
                            'text': f'{"T" if e.get("tied") else ""}{e["position"]} at the {e["name"]}.'})
            elif e.get('position') == 1 and not any(x['kind'] == 'trophy' and x['date'] == [y, w] for x in out):
                out.append({'date': [y, w], 'kind': 'result', 'golfer_id': r.get('golfer_id', c.golfer_id),
                            'text': f'Won the {e["name"]}.'})
    for x in getattr(c, 'status_log', []):
        out.append({'date': list(x['date']), 'kind': 'tour', 'golfer_id': x['golfer_id'],
                    'text': status_text(x['from'], x['to'])})
    for (y, w), r in sorted(getattr(c, 'weekly_recaps', {}).items()):
        for inj in r.get('injuries', []):            # onset episodes only: recorded in the onset week's recap
            where = f' at the {inj["event"]}' if inj.get('event') else ''
            out.append({'date': [y, w], 'kind': 'injury', 'golfer_id': r.get('golfer_id', c.golfer_id),
                         'text': f'Injured ({str(inj.get("kind", "injury")).replace("_", " ")}){where}: out '
                                 f'{inj.get("announced")} week{"s" if inj.get("announced") != 1 else ""}.'})
    st = season.staff
    ids = {s['golfer_id'] for s in getattr(c, 'stints', [])}
    for gid in sorted(ids):
        for kind in ('coach', 'caddie'):
            for s in st.rel.of_golfer(gid, kind):
                who = (st.coaches if kind == 'coach' else st.caddies).get(s.staff)
                name = who.name if who else str(s.staff)
                out.append({'date': list(s.start), 'kind': 'staff', 'golfer_id': gid,
                            'text': f'{kind.capitalize()} {name} began working with you.'})
                if getattr(s, 'end', None):
                    out.append({'date': list(s.end), 'kind': 'staff', 'golfer_id': gid,
                                'text': f'{kind.capitalize()} {name} stopped working with you'
                                        + (f' ({s.reason_end})' if s.reason_end else '') + '.'})
    out.sort(key=lambda x: (tuple(x['date']), x['kind'], x['text']))
    return out
