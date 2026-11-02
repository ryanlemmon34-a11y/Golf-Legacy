"""Career mode pages (roadmap Phase B; docs/career/PHASE_AB_PLAN.md): the career home and the planner.

Pages only draw the committed snapshot (observer_live: the career view and planner models from golfsim/career.py)
and post commands; every rule and consequence lives in golfsim. Every form carries an operation key, the date it
was drawn at and the career's version, so a repeated or stale submission changes nothing. Hidden potential is never
shown.
"""
from __future__ import annotations

import uuid
from urllib.parse import quote

from observer import esc, table

CATS = (('physical', 'Physical'), ('long_game', 'Long game'), ('short_game', 'Short game'), ('putting', 'Putting'),
        ('mental', 'Mental game'))
LABEL = dict(CATS)


def money(x):
    return f'${x:,.0f}' if x is not None else '—'


def wk(year, week):
    return f'week {week} of {year}'


def hidden(w, version=None, extra=()):
    c = w.live.cursor
    items = [('world', w.live.world_id), ('year', c['year']), ('week', c['week']), ('phase', c['phase']),
             ('op', uuid.uuid4().hex)] + ([('version', version)] if version is not None else []) + list(extra)
    return ''.join(f'<input type="hidden" name="{k}" value="{esc(v)}">' for k, v in items)


def career_link(w):
    """The menu entry, with the number of decisions waiting."""
    v = getattr(w.live, 'career', None) if w is not None and getattr(w, 'live', None) else None
    n = len(v['pending']) if v and v['status'] == 'active' else 0
    return '<a href="/career">Career' + (f' <span class="tag">{n} to decide</span>' if n else '') + '</a>'


# ---- the career home ------------------------------------------------------------------------------------------------

def career_page(w, q):
    v = getattr(w.live, 'career', None)
    if v is None:
        return 'Career', no_career(w)
    g = v['golfer']
    y, wkn = v['date']
    state = ('<span class="tag">you control this golfer</span>' if v['status'] == 'active'
             else f'<span class="tag">under AI control since {esc(wk(*v["ended"]))}</span>')
    head = (f'<p>{state} <a href="/golfer/{g["id"]}"><strong>{esc(g["name"])}</strong></a> · {esc(g["country"])} · '
            f'age {g["age"]} · {esc(g["status"])}{" (part-time: working)" if g["lifestyle"] == "part_time" else ""} · '
            f'{esc(g["tour"])}. Started {esc(wk(*v["started"]))} as one of {v["entry"]["class_size"]} newcomers '
            f'(chosen by {esc(v["entry"]["rule"])}). The date is <strong>{esc(wk(y, wkn))}</strong>'
            + (' (1 January not yet played)' if v['cursor']['phase'] == 'start' else '')
            + (' (week prepared; not yet played)' if v['cursor']['phase'] == 'planned' else '')
            + (' (the season is over; the winter has not run)' if v['cursor']['phase'] == 'end' else '') + '.</p>')
    left = [golfer_card(g), plan_card(w, v)]
    right = [decisions_card(w, v), notices_card(v)]
    controls = advance_card(w, v) if v['status'] == 'active' else ''
    body = (head + controls + '<div style="display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:1.5rem">'
            f'<div>{"".join(left)}</div><div>{"".join(right)}</div></div>' + end_card(w, v) + scope_note())
    return 'Career', body


def no_career(w):
    can = getattr(w.live, 'career_can_start', None)
    out = ['<p>This world has no career. A career is played as one genuine newcomer in this world: a golfer from '
           'the junior class the world\'s own rules create for a season. Nobody is added to the world for you.</p>']
    if can and not w.read_only:
        out.append(f'<p>This world is at the start of {can["year"]}, its second season, and its first junior class '
                   f'({can["class_size"]} golfers) has just entered. The career takes one of them, chosen by a seeded draw '
                   '(not by ability).</p>'
                   f'<form method="post" action="/career/start">{hidden(w)}<button class="primary">Start the career</button>'
                   '</form>')
    else:
        out.append('<p>Start one from the <a href="/worlds">World library</a> with <strong>New Career</strong>: it creates a '
                   'world, plays its first season under AI so that the first newcomer class exists, and gives you one of '
                   'them at the start of the second season.</p>')
    return ''.join(out)


def golfer_card(g):
    ranks = []
    if g['world_rank']:
        ranks.append(f'world ranking {g["world_rank"]}')
    if g['amateur_rank']:
        ranks.append(f'amateur ranking {g["amateur_rank"]}')
    inj = (f'<dt>Health</dt><dd>injured (absolute week {g["injured_until"]})</dd>' if g['injured_until']
           else '<dt>Health</dt><dd>fit</dd>')
    act = ', '.join(f'{k} {n}' for k, n in sorted(g['activity'].items())) or 'nothing yet'
    kv = ('<dl class="kv">'
          f'<dt>Overall</dt><dd>{g["overall"]}</dd><dt>Prestige</dt><dd>{g["prestige"]}</dd>'
          f'<dt>Ranking</dt><dd>{esc(", ".join(ranks) or "not ranked yet")}</dd>{inj}'
          f'<dt>Fatigue</dt><dd>{g["fatigue"]}</dd>'
          f'<dt>Money for golf</dt><dd>{money(g["spendable"])} (funds {money(g["funds"])}, less the next weeks\' '
          'committed costs, plus any amateur support)</dd>'
          f'<dt>Coach</dt><dd>{esc(g["coach"] or "none")}</dd><dt>Caddie</dt><dd>{esc(g["caddie"] or "none")}</dd>'
          f'<dt>This season</dt><dd>{esc(act)} (weeks)</dd></dl>')
    attrs = table(['Group', 'Ratings'], [[esc(label), esc(', '.join(f'{k.replace("_", " ")} {x}' for k, x in vals))]
                                         for label, vals in g['attrs']])
    return f'<h2>Golfer</h2>{kv}<h3>Ratings now</h3>{attrs}<p class="muted">Potential is never shown.</p>'


def plan_card(w, v):
    out = ['<h2>Plan</h2><p class="muted">Planning is in four-week periods (the engine\'s thirteen blocks a season, '
           'not calendar months). A plan is an intention: entry, selection and payment are decided by the same rules as '
           'for every golfer when the week comes.</p>']
    for b in v['blocks']:
        y, w0 = b['block']
        rows = [[str(x['week']), esc(x['text']), 'played' if x['played'] else 'planned'] for x in b['weeks']]
        pol = b['policy']
        out.append(f'<h3>Weeks {w0}–{w0 + len(b["weeks"]) - 1} of {y}</h3>' + table(['Week', 'Plan', ''], rows)
                   + f'<p class="muted">If selected or invited: {esc(pol["selected"])}. Qualifying: {esc(pol["qualifying"])}.</p>')
    for (py, p0) in v['plannable']:
        out.append(f'<p><a class="button" href="/career/plan?block={py}-{p0}">Plan weeks {p0}–{min(52, p0 + 3)} of {py}</a></p>')
    return ''.join(out)


def decisions_card(w, v):
    if not v['pending']:
        return '<h2>Decisions</h2><p class="muted">Nothing to decide now.</p>' + resolved_list(v)
    out = ['<h2>Decisions</h2>']
    for d in v['pending']:
        due = ('before ' + wk(*d['deadline']) + ' is played') if d['deadline'] else 'now'
        acts = ''
        if d['kind'] in ('plan', 'replan'):
            b = d['payload'].get('block') or [d['payload']['week'][0], ((d['payload']['week'][1] - 1) // 4) * 4 + 1]
            acts = f'<a class="button primary" href="/career/plan?block={b[0]}-{b[1]}">Open the planner</a>'
        elif d['kind'] in ('coach_offer', 'caddie_offer', 'job'):
            acts = ''.join(f'<form method="post" action="/career/decide" style="display:inline">'
                           f'{hidden(w, v["version"], (("decision", d["id"]), ("answer", a)))}'
                           f'<button{" class=primary" if a == "accept" else ""}>{"Accept" if a == "accept" else "Decline"}'
                           '</button></form> ' for a in d['options'])
        elif 'return_to_ai' in d['options']:
            acts = (f'<form method="post" action="/career/decide">{hidden(w, v["version"], (("decision", d["id"]), ("answer", "return_to_ai")))}'
                    '<button class="primary">Return the golfer to AI control</button></form>')
        out.append(f'<div class="banner warn"><p>{esc(d["text"])}</p><p class="muted">Answer {esc(due)}.</p>{acts}</div>')
    return ''.join(out) + resolved_list(v)


def resolved_list(v):
    if not v['resolved']:
        return ''
    rows = [[esc(d['kind'].replace('_', ' ')), esc(d['status']), esc(wk(*d['resolved']['at'])) if d['resolved'] else '',
             esc(d['text'][:140] + ('…' if len(d['text']) > 140 else ''))] for d in reversed(v['resolved'])]
    return '<h3>Recent decisions</h3>' + table(['Kind', 'Outcome', 'When', 'About'], rows)


def notices_card(v):
    if not v['notices']:
        return ''
    rows = [[esc(wk(n['year'], n['week'])), esc(n['text'])] for n in reversed(v['notices'])]
    return '<h2>Notices</h2>' + table(['When', 'What'], rows)


def advance_card(w, v):
    due = [d for d in v['pending'] if d['deadline'] is None or tuple(d['deadline']) <= tuple(v['date'])]
    note = (f'<p class="muted">{len(due)} decision{"s" if len(due) != 1 else ""} must be answered before the next week '
            'can be played: advancing stops at once until then.</p>') if due else ''
    return (f'<div class="filters"><form method="post" action="/career/advance">{hidden(w, None, (("mode", "next"),))}'
            '<button class="primary" title="Plays on until something needs your decision">Advance to next decision</button>'
            f'</form><form method="post" action="/career/advance">{hidden(w, None, (("mode", "period"),))}'
            '<button title="Plays to the end of the current four-week period, stopping earlier only if a decision is due">'
            'Advance through planned period</button></form></div>' + note)


def end_card(w, v):
    if v['status'] != 'active':
        return ''
    return (f'<h2>Hand the golfer back</h2><form method="post" action="/career/end" class="filters">{hidden(w, v["version"])}'
            '<label class="muted"><input type="checkbox" name="confirm" value="yes" required> the AI decides for this '
            'golfer from now on (pending offers must be answered first)</label><button>Return golfer to AI control</button>'
            '</form>')


def scope_note():
    return ('<p class="muted">This first career build covers planning, entries, training and rest, offers, the work '
            'pathway and saving. Season-end decisions, customization, switching golfers and hiring staff yourself come in '
            'later builds: the career stops at the end of a season, where the golfer can be returned to AI control.</p>')


# ---- the planner ----------------------------------------------------------------------------------------------------

def plan_page(w, q):
    v = getattr(w.live, 'career', None)
    if v is None or v['status'] != 'active':
        return 'Planner', '<p>No career is being played in this world. <a href="/career">Career</a></p>'
    raw = (q.get('block') or [''])[0]
    plans = getattr(w.live, 'career_planner', {}) or {}
    try:
        y, w0 = (int(x) for x in raw.split('-'))
    except ValueError:
        y, w0 = (v['plannable'][0] if v['plannable'] else (None, None))
    p = plans.get((y, w0))
    if p is None:
        return 'Planner', ('<p>That period cannot be planned now (only the current four-week period and the next).</p>'
                           '<p><a href="/career">Back to the career</a></p>')
    cats = ''.join(f'<option value="{k}">{esc(label)}</option>' for k, label in CATS)
    rows = []
    for o in p['weeks']:
        n = o['week']
        cur = o['current'] or {}
        opts = []
        for e in o['events']:
            if not e['eligible'] or not e.get('affordable'):
                continue
            sel = ' checked' if cur.get('kind') == 'event' and cur.get('event_id') == e['event_id'] else ''
            opts.append(f'<label><input type="radio" name="w{n}" value="event:{esc(e["event_id"])}"{sel} required> '
                        f'<a href="/event/{quote(e["event_id"])}">{esc(e["name"])}</a> · {esc(e["city"])}, {esc(e["country"])} · '
                        f'{esc(e["tour"])} · cost {money(e["cost"])}</label>')
        tsel = ' checked' if cur.get('kind') == 'train' else ''
        rsel = ' checked' if cur.get('kind') == 'rest' else ''
        csel = cur.get('category') if cur.get('kind') == 'train' else None
        catsel = ''.join(f'<option value="{k}"{" selected" if k == csel else ""}>{esc(label)}</option>' for k, label in CATS)
        opts.append(f'<label><input type="radio" name="w{n}" value="train"{tsel} required> Train: '
                    f'<select name="c{n}" aria-label="Training for week {n}">{catsel}</select></label>')
        opts.append(f'<label><input type="radio" name="w{n}" value="rest"{rsel} required> Rest</label>')
        fb = cur.get('fallback') or {}
        fsel = lambda val: ' selected' if (fb.get('kind') == 'train' and val == f'train:{fb.get("category")}') or \
            (fb.get('kind') == 'rest' and val == 'rest') else ''
        fallback = (f'<select name="f{n}" aria-label="If the entry is not accepted in week {n}">'
                    + ''.join(f'<option value="train:{k}"{fsel("train:" + k)}>train {esc(label.lower())}</option>' for k, label in CATS)
                    + f'<option value="rest"{fsel("rest")}>rest</option></select>')
        closed = [e for e in o['events'] if not e['eligible'] or not e.get('affordable')]
        why = ('<details><summary>' + f'{len(closed)} event{"s" if len(closed) != 1 else ""} you cannot enter</summary><ul>'
               + ''.join(f'<li>{esc(e["name"])}: {esc(e["why"])}</li>' for e in closed) + '</ul></details>') if closed else ''
        sel_ev = ('<ul>' + ''.join(f'<li>{esc(e["name"])} ({esc(e["rule"])})</li>' for e in o['selected']) + '</ul>'
                  if o['selected'] else '<span class="muted">none</span>')
        inj = f'<p class="banner warn">Injured this week: only rest is possible.</p>' if o['injured_until'] else ''
        rows.append([f'<strong>{n}</strong>', inj + '<div style="display:grid;gap:.25rem">' + ''.join(opts) + '</div>' + why,
                     fallback, sel_ev])
    pol = p['policy'] or {}
    chk = lambda k, val: ' checked' if pol.get(k) == val else ''
    policy = ('<fieldset><legend>Selections and invitations in this period (majors, championships, invitations, '
              'college postseason)</legend>'
              f'<label><input type="radio" name="selected" value="accept"{chk("selected", "accept")} required> accept a place if '
              'the event\'s rules give me one</label> '
              f'<label><input type="radio" name="selected" value="decline"{chk("selected", "decline")} required> decline</label>'
              '</fieldset><fieldset><legend>Qualifying in this period</legend>'
              f'<label><input type="radio" name="qualifying" value="enter"{chk("qualifying", "enter")} required> enter qualifying I '
              'am eligible for</label> '
              f'<label><input type="radio" name="qualifying" value="skip"{chk("qualifying", "skip")} required> do not enter</label>'
              '</fieldset>')
    money_line = (f'<p>Money for golf now: <strong>{money(p["weeks"][0]["money"])}</strong>. Costs are this week\'s '
                  'estimate (travel and fees); they are checked again when the week comes.</p>') if p['weeks'] else ''
    form = (f'<form method="post" action="/career/plan">{hidden(w, p["version"], (("block", f"{y}-{w0}"),))}'
            + money_line + table(['Week', 'Choose', 'If the entry is not accepted', 'Fields chosen by the event\'s rules'], rows)
            + policy + '<p><button class="primary">Save the plan</button> <a href="/career">Cancel</a></p></form>')
    note = ('<p class="muted">Events you can enter are listed with their cost; the others are folded under each week with '
            'the rule that keeps you out. An entry is not a place: fields fill in each event\'s entry order, and if yours '
            'is not accepted the week falls back to what you choose here. Events that choose their own fields are covered '
            'by the period\'s policy below.</p>')
    return f'Plan weeks {w0}–{min(52, w0 + 3)} of {y}', note + form


# ---- reading forms into commands ------------------------------------------------------------------------------------

def plan_command(form, one):
    """The plan_block command from a submitted planner form (validated again by golfsim)."""
    try:
        y, w0 = (int(x) for x in (one(form, 'block') or '').split('-'))
    except ValueError:
        return None
    weeks = {}
    for n in range(w0, min(52, w0 + 3) + 1):
        val = one(form, f'w{n}')
        if val is None:
            continue
        if val.startswith('event:'):
            fb = one(form, f'f{n}') or ''
            weeks[str(n)] = {'kind': 'event', 'event_id': val[6:],
                             'fallback': ({'kind': 'train', 'category': fb[6:]} if fb.startswith('train:') else {'kind': 'rest'})}
        elif val == 'train':
            weeks[str(n)] = {'kind': 'train', 'category': one(form, f'c{n}')}
        elif val == 'rest':
            weeks[str(n)] = {'kind': 'rest'}
    return {'schema': 1, 'type': 'plan_block', 'block': [y, w0], 'weeks': weeks,
            'policy': {'selected': one(form, 'selected'), 'qualifying': one(form, 'qualifying')},
            'version': int(one(form, 'version')) if one(form, 'version') not in (None, '') else None}


def stop_text(stop, view=None):
    if not stop:
        return ''
    if stop['kind'] == 'decision':
        n = len(stop.get('ids', ()))
        return f'Stopped: {n} decision{"s" if n != 1 else ""} to make (see Career).'
    return 'Stopped: ' + stop.get('text', stop['kind'])
