"""Read-only, explainable planning suggestions from public career-view facts.

No Season, RNG, hidden ceilings, field construction or AI planning calls. Suggestions
are not an optimal solution or a forecast of entry/development. Save still validates.
"""
import copy
import html
import json

GROUPS = {
    'physical': ('power', 'stamina', 'recovery_rate', 'injury_resistance'),
    'long_game': ('driving_accuracy', 'long_irons', 'mid_irons', 'ball_flight', 'striking_consistency'),
    'short_game': ('wedges', 'chipping', 'bunker', 'recovery_play'),
    'putting': ('short_putting', 'lag_putting', 'green_reading', 'putting_consistency'),
    'mental': ('composure', 'resilience', 'management', 'focus'),
}


def enrich_plan(plan, golfer, training_enabled=True):
    """Copy and enrich an existing planner. Does not change it or the golfer."""
    p = copy.deepcopy(plan)
    for w in p['weeks']:
        for e in w.get('events', []):
            if w.get('injured_until'):
                label = 'Unavailable while injured'
            elif not e.get('eligible'):
                label = e.get('why') or 'Not eligible'
            elif not e.get('affordable'):
                label = e.get('why') or 'Not affordable now'
            else:
                label = 'Eligible to request; place not guaranteed'
            e['access'] = {'label': label, 'probability': None,
                           'detail': 'A reliable entry percentage is not available. Final entry depends on the event rules and other entrants.'}
        for e in w.get('selected', []):
            e['access'] = {'label': 'Selection/qualification rules apply', 'probability': None,
                           'detail': 'Being listed here does not mean you are selected or qualified.'}
    p['advice'] = None
    if not golfer.get('coach') or not p['weeks']:
        return p
    attrs = golfer.get('attrs_exact', {})
    means = {k: sum(attrs[a] for a in names if a in attrs) / sum(a in attrs for a in names)
             for k, names in GROUPS.items() if any(a in attrs for a in names)}
    if not means:
        return p
    focus = min(means, key=lambda k: (means[k], k))
    fatigue = float(golfer.get('fatigue', 0))
    funds = max(0, float(p['weeks'][0].get('money', 0)))
    stamina = max(0, min(100, attrs.get('stamina', 50))) / 100
    recovery = max(0, min(100, attrs.get('recovery_rate', 50))) / 100
    rows, competitions, last_event = [], 0, False
    for w in p['weeks']:
        n = w['week']
        fallback = {'kind': 'train', 'category': focus} if training_enabled else {'kind': 'rest'}
        candidates = [e for e in w.get('events', []) if e.get('eligible') and e.get('affordable')
                      and float(e.get('cost', 0)) <= funds]
        # Prefer this golfer's pathway, then lower cost, then stable ID. Not a win/entry probability.
        candidates.sort(key=lambda e: (e.get('tour') != golfer.get('tour'), float(e.get('cost', 0)), e['event_id']))
        if w.get('injured_until'):
            choice, reason = {'kind': 'rest'}, 'Rest through the recorded injury window.'
        elif fatigue > .2:
            choice, reason = {'kind': 'rest'}, 'Current/estimated fatigue is above the 20% performance threshold.'
        elif candidates and competitions < 2 and not last_event:
            e = candidates[0]
            choice = {'kind': 'event', 'event_id': e['event_id'], 'fallback': fallback}
            reason = 'Request ' + e['name'] + ': an affordable competition option, preferring your pathway. Entry is not guaranteed.'
            funds -= float(e.get('cost', 0))
            competitions += 1
        else:
            choice = fallback
            reason = ('Train ' + focus.replace('_', ' ') + ', your lowest current visible category average; balance competition with development.'
                      if training_enabled else 'Rest between competitions; attribute development is disabled in this world.')
        if choice['kind'] == 'rest':
            fatigue *= .4 + .3 * (1 - recovery)
        elif choice['kind'] == 'train':
            fatigue = .85 * fatigue + .02 * (1.4 - .8 * stamina)
        # Event fatigue cannot be predicted accurately from this view; never invent it.
        last_event = choice['kind'] == 'event'
        rows.append({'week': n, 'choice': choice, 'reason': reason})
    p['advice'] = {'coach': golfer['coach'], 'weeks': rows,
                   'policy': {'selected': 'accept', 'qualifying': 'enter'},
                   'note': 'A starting suggestion, not a guaranteed best route. Based on current visible ratings, fatigue, eligibility and costs. '
                           'Competition fatigue, future income, selection and qualifying outcomes are not forecast; review after each period. '
                           'Invitations or qualifying can replace the suggested activity. No hidden potential is used. Accept fills this form only; Save commits it.'}
    return p


def render_advice(plan):
    a = plan.get('advice')
    if not a:
        return '<p class="muted">Coach advice is unavailable: a private coach, visible ratings and an open planning period are required.</p>'
    esc = html.escape
    payload = json.dumps(a, separators=(',', ':')).replace('<', '\\u003c').replace('&', '\\u0026')
    items = ''.join(f'<li><strong>Week {r["week"]}:</strong> {esc(r["reason"])}</li>' for r in a['weeks'])
    return (f'<section class="career-panel coach-advice"><h3>{esc(a["coach"])}’s suggested period</h3><ul>{items}</ul>'
            f'<p class="muted">{esc(a["note"])}</p><button type="button" id="accept-coach-advice">Accept coach advice</button>'
            '<p id="coach-advice-status" role="status" aria-live="polite"></p></section>'
            '<script>(function(){const advice=' + payload + ';'
            'document.getElementById("accept-coach-advice").addEventListener("click",function(){'
            'const form=document.querySelector(\'form[action="/career/plan"]\');if(!form)return;'
            'const radio=(name,value)=>Array.from(form.querySelectorAll("input[type=radio]")).find(x=>x.name===name&&x.value===value&&!x.disabled);'
            'let changes=[];for(const row of advice.weeks){const n=row.week,c=row.choice,r=radio("w"+n,c.kind);if(!r)return;'
            'let updates=[];if(c.kind==="train")updates.push(["c"+n,c.category]);'
            'if(c.kind==="event"){updates.push(["e"+n,c.event_id]);updates.push(["f"+n,c.fallback.kind==="train"?"train:"+c.fallback.category:"rest"]);}'
            'for(const [name,val] of updates){const select=form.elements.namedItem(name);if(!select||select.disabled||!Array.from(select.options).some(o=>o.value===val))return;}'
            'changes.push([r,updates]);}'
            'for(const [r,updates] of changes){r.checked=true;for(const [name,val] of updates)form.elements.namedItem(name).value=val;}'
            'for(const [name,val] of Object.entries(advice.policy)){const r=radio(name,val);if(r)r.checked=true;}'
            'document.getElementById("coach-advice-status").textContent="Advice applied to the form. Review it, then Save the plan. Nothing has been saved yet.";'
            '});})();</script>')
