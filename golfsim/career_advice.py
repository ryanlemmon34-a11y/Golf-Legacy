"""Coach's advice for the four-week period (read only; docs/career/COACH_ADVICE.md).

A starting suggestion for each open week -- play, train or rest -- from the evidence the planner already shows
(decision_support.week_compare), weighed by fixed, published rules:

* stakes and pathway: what a result there unlocks (opportunities still open to a result), the golfer's own tour;
* the entry outlook (entry_outlook: never a percentage), the course fit, the cost against the money there is;
* load: tournaments played in the last four weeks and those suggested in this period, the fatigue now and the engine's
  own rest / training fatigue formulas (career.readiness); fatigue after a tournament is not forecast;
* training: the visible weakness (the observed levels' order), the coach's (or own) perceived growth room
  (scouting: an opinion with uncertainty, never a ceiling) and the coach's public speciality.

It changes no rule and decides nothing: the player edits and saves the plan (which the engine validates as for any
plan), and the same evidence and rules apply to every golfer. No random draw, no hidden ratings.
"""
from __future__ import annotations

FATIGUE_LIMIT = 0.2               # the engine's season-fatigue performance threshold (career.readiness)
MAX_RECENT = 2                    # tournaments in any four consecutive weeks the advice suggests at most
WINDOW = 4                        # (the week itself and the three before it)
PLAY_BAR = 2.0                    # an event's advice score needed to suggest playing it

OUTLOOK_POINTS = {'open_last_time': 2.0, 'ahead_of_last_cutoff': 2.0, 'near_capacity_last_time': 1.0,
                  'at_last_cutoff': 0.5, 'unknown': 0.5, 'quota_limited': 0.0, 'behind_last_cutoff': -3.0}
ROOM_POINTS = {'little': 0.0, 'some': 1.0, 'considerable': 2.0, 'unknown': 0.5}


def _r(code, text):
    return {'code': code, 'text': text}


def train_pick(compare, scouting, coach):
    """(category, reasons, score table) for training: weakness rank, perceived growth room, coach speciality."""
    room = {x['category']: x.get('growth_room', {}) for x in (scouting or {}).get('categories', [])}
    table = []
    for t in compare['train']:
        cat = t['category']
        rank = t.get('weakest_rank')
        n = len(compare['train'])
        weak = (n - rank) if rank else 0.0                        # weakest = n - 1 points
        gr = room.get(cat, {})
        rp = ROOM_POINTS.get(gr.get('label'), 0.5)
        spec = 1.0 if coach is not None and coach.speciality == cat else 0.0
        table.append({'category': cat, 'score': round(weak + rp + spec, 2), 'weakest_rank': rank,
                      'growth_room': gr.get('label'), 'growth_room_uncertainty': gr.get('uncertainty'),
                      'coach_speciality': bool(spec)})
    table.sort(key=lambda x: (-x['score'], x['weakest_rank'] or 99, x['category']))
    if not table:
        return None, [], []
    top = table[0]
    name = top['category'].replace('_', ' ')
    reasons = []
    if top['weakest_rank'] == 1:
        reasons.append(_r('visible_weakness', f'{name.capitalize()} is the weakest area as last observed.'))
    elif top['weakest_rank']:
        reasons.append(_r('visible_weakness', f'{name.capitalize()} ranks {top["weakest_rank"]} of {len(table)} '
                                              'from the weakest as last observed.'))
    if top['growth_room'] in ('some', 'considerable'):
        reasons.append(_r('growth_room', f'Perceived room to grow here: {top["growth_room"]} '
                                         f'({top["growth_room_uncertainty"]} uncertainty; an opinion, not a limit).'))
    elif top['growth_room'] == 'unknown':
        reasons.append(_r('growth_room_unknown', 'No growth-room read yet for this area.'))
    if top['coach_speciality']:
        reasons.append(_r('coach_speciality', f'It is your coach\'s speciality.'))
    return top['category'], reasons, table


def play_score(row, tour_name, money):
    """(score, for, against) for requesting entry to one ordinary event."""
    pro, con = [], []
    score = 0.0
    out = row.get('entry_outlook') or {}
    st = out.get('status')
    score += OUTLOOK_POINTS.get(st, 0.0)
    if st in ('open_last_time', 'ahead_of_last_cutoff'):
        pro.append(_r('entry_outlook', out.get('label', '')))
    elif st == 'behind_last_cutoff':
        con.append(_r('long_shot', f'A long shot to get in: {out.get("reason", "")}'))
    elif st:
        con.append(_r('entry_outlook', f'{out.get("label", "")}: {out.get("reason", "")}'))
    stakes = [o for o in row.get('opportunities', []) if o.get('status') == 'needs_result']
    if stakes:
        score += 2.0
        names = sorted({f"{o['target']['label']} ({o['target']['year']})" for o in stakes if o.get('target')})
        pro.append(_r('stakes', 'A result here can earn a place in: ' + '; '.join(names) + '.'))
    if row.get('tour') == tour_name:
        score += 1.5
        pro.append(_r('pathway', 'An event of your own tour.'))
    cf = row.get('course_fit')
    if cf and cf.get('points'):
        score += 0.5 * cf['points']
        (pro if cf['points'] > 0 else con).append(_r('course_fit', f'Course fit and familiarity: {cf["points"]:+.1f} '
                                                                   'points of appeal.'))
    cost = row.get('cost') or 0.0
    if cost > 0 and money > 0 and cost > 0.5 * money:
        score -= 1.0
        con.append(_r('cost', f'Costs ${cost:,.0f}, more than half of the ${money:,.0f} available for golf.'))
    con.append(_r('not_guaranteed', 'Entry is decided when the field is set; your fallback applies if not taken.'))
    return round(score, 2), pro, con


def advise(season, c, g, cursor, compare):
    """{block, judge, weeks: {"w": {recommended, reasons, alternatives}}, policy, basis, note} or None."""
    from . import career as CA
    from . import scouting
    if not compare or g is None:
        return None
    y = cursor['year']
    weeks = sorted(int(w) for w in compare)
    coach = season.staff.coach(g.id)
    sc = scouting.view(season, c, g.id)
    ready = CA.readiness(season, g, y, weeks[0])
    training = ready['training_enabled']
    from .calendar import TOUR_BY_KEY
    t = TOUR_BY_KEY.get(g.tour)
    tour_name = t.name if t else g.tour
    money = season.spendable(g, y)
    fatigue = ready['fatigue']
    fatigue_known = True
    recover = 0.40 + 0.30 * (1 - g.attrs['recovery_rate'] / 100)
    train_load = 0.02 * (1.4 - 0.8 * g.attrs['stamina'] / 100)
    recent = [w for (yy, w), r in getattr(c, 'weekly_recaps', {}).items()
              if yy == y and r.get('activity') == 'play' and r.get('golfer_id', g.id) == g.id]
    planned_play = []
    by = season.cal.by_id

    def series(row):
        return by.get(row['event_id'].split(':', 1)[1])
    sel_all = [r for w in weeks for r in compare[str(w)]['play'] if r.get('selected_field')]
    # qualifying (the entrant decides: career.entrant_decides, the engine's own test) is worth entering when a result
    # there can still earn a place and the rules do not already rule the golfer out
    quals = [r for r in sel_all if series(r) is not None and CA.entrant_decides(series(r))
             and any(o.get('status') == 'needs_result' for o in r.get('opportunities', []))]
    policy = {'selected': 'accept', 'qualifying': 'enter' if quals else 'skip'}
    cat, cat_reasons, table = train_pick(compare[str(weeks[0])], sc, coach)
    train_choice = {'kind': 'train', 'category': cat} if training and cat else {'kind': 'rest'}
    out = {}

    def committed_rows(wc):
        sel = [r for r in wc['play'] if r.get('selected_field')]
        st = lambda r: (r.get('entry_outlook') or {}).get('status')
        held = [r for r in sel if st(r) in ('holds_place', 'assured_by_rules')]
        unless = [r for r in sel if st(r) == 'unless_qualified_earlier']   # entered unless qualified before it
        trying = [r for r in sel if r in quals] if policy['qualifying'] == 'enter' else []
        return sel, st, held, unless, trying
    # weeks the rules (or the suggested policy) already fill with a competition: counted in every load window
    committed_weeks = [w for w in weeks if not compare[str(w)]['load'].get('injured_until')
                       and any(committed_rows(compare[str(w)])[2:])]

    def window_room(w):
        """Whether one more tournament in week w keeps every four consecutive weeks around it within MAX_RECENT,
        counting recorded, suggested and committed weeks."""
        busy = set(recent) | set(planned_play) | set(committed_weeks)
        return all(sum(1 for x in busy if start <= x < start + WINDOW and x != w) + 1 <= MAX_RECENT
                   for start in range(w - WINDOW + 1, w + 1))
    for w in weeks:
        wc = compare[str(w)]
        inj = wc['load'].get('injured_until')
        plays_4 = sum(1 for x in recent + planned_play if w - (WINDOW - 1) <= x < w)   # the three weeks before
        near = sorted(x for x in committed_weeks if abs(x - w) < WINDOW and x != w)
        sel, st, held, unless, trying = committed_rows(wc)
        maybe = [r for r in sel if r not in held and r not in trying and r not in unless
                 and st(r) not in ('not_eligible', 'injured')
                 and not (series(r) is not None and CA.entrant_decides(series(r)))]
        cands = []
        for row in wc['play']:
            if row.get('selected_field') or not row.get('eligible') or row.get('cost') is None:
                continue
            if (row.get('entry_outlook') or {}).get('status') in ('cannot_afford', 'not_eligible', 'injured'):
                continue
            if (row.get('cost') or 0) > money:
                continue
            s, pro, con = play_score(row, tour_name, money)
            cands.append((s, row['event_id'], row, pro, con))
        cands.sort(key=lambda x: (-x[0], x[1]))
        best = cands[0] if cands else None
        rest_after = fatigue * recover if fatigue else 0.0
        train_after = 0.85 * fatigue + train_load
        rest_txt = f'about {rest_after:.0%}' if fatigue_known else 'not forecast (after the suggested tournament)'
        train_txt = f'about {train_after:.0%}' if fatigue_known else 'not forecast (after the suggested tournament)'
        alts = []
        if inj:
            rec = {'kind': 'rest'}
            reasons = [_r('injured', 'Injured: the golfer cannot enter events; rest through the recovery window.')]
        elif held or trying or unless:
            rec = dict(train_choice)
            names = ', '.join(r.get('name') or r['event_id'] for r in held + trying + unless)
            if held:
                why = ('you hold a place' if st(held[0]) == 'holds_place' else 'the rules enter you') + \
                      ' and the suggested policy accepts it'
            elif trying:
                why = 'the suggested policy enters qualifying'
            else:
                why = ('the rules enter you unless you qualify in an earlier qualifier first (not certain: counted '
                       'in the load to be safe)')
            reasons = [_r('committed', f'{names}: {why}; that competition comes first this week (counted in the '
                          'load). The planned ' + ('training' if rec['kind'] == 'train' else 'rest')
                          + ' applies if it does not happen.')]
        elif fatigue_known and fatigue > FATIGUE_LIMIT:
            rec = {'kind': 'rest'}
            reasons = [_r('fatigue', f'Fatigue {fatigue:.0%} is above the {FATIGUE_LIMIT:.0%} threshold where '
                                     f'performance suffers; rest brings it to about {rest_after:.0%}.')]
        elif best and best[0] >= PLAY_BAR and window_room(w):   # (a long shot only with enough else for it)
            rec = {'kind': 'event', 'event_id': best[1], 'fallback': dict(train_choice)}
            reasons = best[3] + [_r('load', f'{plays_4} tournament(s) recorded or suggested in the three weeks before: '
                                            f'at most {MAX_RECENT} in any four consecutive weeks.')]
            if (best[2].get('entry_outlook') or {}).get('status') == 'behind_last_cutoff':
                reasons = [r for r in best[4] if r['code'] == 'long_shot'] + reasons
        elif training and cat:
            rec = dict(train_choice)
            reasons = list(cat_reasons)
            if best and best[0] >= PLAY_BAR and near and plays_4 < MAX_RECENT:
                reasons.append(_r('load', 'Competitions the rules already give you in week'
                                  f'{"s" if len(near) > 1 else ""} {", ".join(map(str, near))} fill the load (at most '
                                  f'{MAX_RECENT} in any four consecutive weeks): a development week instead.'))
            elif best and plays_4 >= MAX_RECENT:
                reasons.append(_r('load', f'{plays_4} tournaments in the three weeks before (at most {MAX_RECENT} in '
                                          f'any four consecutive weeks): a development week instead.'))
            elif not best or best[0] < PLAY_BAR:
                reasons.append(_r('no_strong_event', 'No event this week stands out on stakes, pathway and entry '
                                                     'outlook.'))
        else:
            rec = {'kind': 'rest'}
            reasons = [_r('no_training', 'Training is not available to this golfer in this world; rest between '
                                         'events.')]
        if maybe and not inj:
            reasons.append(_r('possible_selection', 'If ' + ', '.join(r.get('name') or r['event_id'] for r in maybe)
                              + ' selects you, the suggested policy accepts and you play it this week instead: '
                                'not counted in the load, because selection is not known in advance.'))
        # the alternatives, each with what speaks for and against it
        if best and rec.get('kind') != 'event' and not inj:
            alts.append({'choice': {'kind': 'event', 'event_id': best[1], 'fallback': dict(train_choice)},
                         'name': best[2].get('name'), 'for': best[3], 'against': best[4] + (
                             [_r('load', f'{plays_4} tournament(s) in the three weeks before; at most {MAX_RECENT} in '
                                         f'any four consecutive weeks.')] if plays_4 else [])})
        if rec.get('kind') != 'train' and training and cat and not inj:
            alts.append({'choice': dict(train_choice), 'for': cat_reasons,
                         'against': [_r('no_results', 'No prize money, ranking points or qualifying results.'),
                                     _r('fatigue_train', f'Fatigue next week {train_txt}.')]})
        if rec.get('kind') != 'rest':
            alts.append({'choice': {'kind': 'rest'},
                         'for': [_r('fatigue_rest', f'Fatigue next week {rest_txt}.')],
                         'against': [_r('no_development', 'No training gains and no results.')]})
        out[str(w)] = {'recommended': rec, 'reasons': reasons, 'alternatives': alts,
                       'events_considered': [{'event_id': e, 'score': s} for s, e, *_ in cands]}
        if (held or trying or unless) and not inj:
            planned_play.append(w)                           # a held place or qualifying: a competition this week
            fatigue_known = False
        elif rec['kind'] == 'event':
            planned_play.append(w)
            money -= best[2].get('cost') or 0.0
            fatigue_known = False                             # (fatigue after a tournament is not forecast)
        elif rec['kind'] == 'train':
            fatigue = train_after
        else:
            fatigue = rest_after
    return {'block': [y, CA.block_start(weeks[0])], 'judge': coach.name if coach else None,
            'source': 'coach' if coach else 'self', 'weeks': out, 'policy': policy,
            'training_table': table,
            'basis': ['entry_outlook', 'opportunities', 'own_tour', 'course_fit', 'cost', 'recent_load',
                      'fatigue_formulas', 'visible_weakness', 'perceived_growth_room', 'coach_speciality'],
            'note': 'A starting suggestion from the evidence shown, by fixed rules: not a forecast, not a guaranteed '
                    'best route. Held places, places the rules give you (counted even when they depend on not qualifying '
                    'earlier) and qualifying the policy enters are counted in the load, and those alone can exceed it; '
                    'places an event may still offer you are not (selection is not known in advance), so the real '
                    'load can be higher. '
                    'Fatigue after a tournament is not forecast, so later weeks after a suggested event are judged '
                    'without it. Edit freely; saving validates the plan as always.'}
