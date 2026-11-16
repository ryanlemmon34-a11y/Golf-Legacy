"""Career mode pages (roadmap Phase B; docs/career/PHASE_AB_PLAN.md): the career home and the planner.

Pages only draw the committed snapshot (observer_live: the career view and planner models from golfsim/career.py)
and post commands; every rule and consequence lives in golfsim. Every form carries an operation key, the date it
was drawn at and the career's version, so a repeated or stale submission changes nothing. Hidden potential is never
shown.
"""
from __future__ import annotations
from observer_course_context import panel as course_panel
from observer_career_estimates import entry as entry_panel
from observer_career_economy import comparison

import uuid
from urllib.parse import quote

from observer import esc, table

CATS = (('physical', 'Physical'), ('long_game', 'Long game'), ('short_game', 'Short game'), ('putting', 'Putting'),
        ('mental', 'Mental game'))
LABEL = dict(CATS)


STYLE = '''<style>
.career-hub { --career-gold:#b08a3e; }
.career-summary {display:flex;flex-wrap:wrap;gap:24px;margin:18px 0 8px}.career-summary strong,.career-summary small {display:block}.career-summary strong {font-size:22px}.career-summary small {font-size:11px}.career-calendar {max-height:420px;overflow:auto}.career-calendar li {padding:12px 0;border-bottom:1px solid var(--line)}
.career-hub h2 { margin:0 0 14px; } .career-hub h3 { margin:0 0 8px; }
.career-hero { display:flex; justify-content:space-between; align-items:center; gap:28px; padding:26px 30px;
 background:linear-gradient(110deg,var(--soft),var(--panel)); border:1px solid var(--line); border-top:4px solid var(--accent); border-radius:12px; }
.career-hero h2 { font-size:34px; letter-spacing:-.04em; margin:7px 0; }
.career-hero p { margin:6px 0 12px; color:var(--muted); }
.eyebrow { font-size:10px; font-weight:750; text-transform:uppercase; letter-spacing:.14em; color:var(--muted); margin-bottom:8px; }
.career-overall { display:flex; flex-direction:column; min-width:170px; text-align:center; border-left:1px solid var(--line); padding-left:24px; }
.career-overall > span { font-size:11px; text-transform:uppercase; letter-spacing:.1em; color:var(--muted); }
.career-overall strong { font-size:48px; line-height:1.2; color:var(--accent); font-variant-numeric:tabular-nums; }
.career-overall small { font-size:11px; color:var(--muted); }
.career-nav { display:flex; flex-wrap:wrap; gap:8px; margin:18px 0 24px; }
.career-nav a { font-size:13px; font-weight:650; padding:8px 14px; border-radius:6px; background:var(--panel); border:1px solid var(--line); }
.career-dashboard { display:grid; grid-template-columns:minmax(0,2.2fr) minmax(300px,1fr); align-items:start; gap:22px; }
.career-main, .career-aside { min-width:0; }
.career-panel { border:1px solid var(--line); background:var(--panel); border-radius:10px; padding:22px; margin:0 0 22px; scroll-margin-top:120px; }
.career-panel > p:first-of-type { margin-top:8px; }
.section-heading { display:flex; align-items:center; flex-wrap:wrap; justify-content:space-between; gap:12px; margin-bottom:16px; }
.section-heading h2 { margin:0; } .section-heading > a { font-size:12px; }
.status-pill { border:1px solid var(--line); padding:4px 9px; border-radius:20px; font-size:11px; color:var(--muted); }
.recap-stats { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:1px; background:var(--line); border:1px solid var(--line); border-radius:8px; overflow:hidden; margin:18px 0; }
.career-stat { background:var(--soft); padding:14px; display:flex; flex-direction:column; min-width:0; }
.career-stat > span { font-size:10px; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; }
.career-stat strong { font-size:22px; font-weight:650; margin:4px 0; font-variant-numeric:tabular-nums; white-space:normal; }
.career-stat small { font-size:10px; color:var(--muted); }
.week-review { display:flex; gap:16px; padding:18px 0; border-bottom:1px solid var(--line); }
.week-review:last-child { border-bottom:0; }
.week-stamp { flex:0 0 42px; height:42px; display:grid; place-items:center; border:1px solid var(--line); background:var(--soft); color:var(--accent); font-size:12px; font-weight:750; border-radius:8px; }
.week-story { min-width:0; flex:1; } .week-story h3 { font-size:15px; }
.week-story p { font-size:12px; margin:5px 0; }
.week-outcomes { font-variant-numeric:tabular-nums; } .week-outcomes > span { padding:0 5px; }
.result-row { display:flex; align-items:center; gap:14px; margin:9px 0; }
.result-row a { font-weight:650; } .result-place { background:var(--soft); border-radius:6px; padding:8px; color:var(--accent); font-size:20px; min-width:52px; text-align:center; }
.career-panel .fine-print { font-size:11px; padding-top:12px; border-top:1px solid var(--line); }
.career-empty { border:1px dashed var(--line); border-radius:8px; padding:35px 20px; margin:20px 0; text-align:center; color:var(--muted); background:var(--soft); }
.career-history { padding-top:16px; margin-top:16px; border-top:1px solid var(--line); }
.career-history > summary { color:var(--accent); font-weight:650; font-size:13px; }
.career-details { margin:18px 0; border:1px solid var(--line); border-radius:8px; padding:16px; background:var(--panel); }
.career-details > summary { font-size:13px; font-weight:650; } .career-details[open] > summary { margin-bottom:18px; }
.fatigue-number { font-size:38px; font-weight:650; font-variant-numeric:tabular-nums; }
.fatigue-number span { font-size:12px; font-weight:400; color:var(--muted); margin-left:6px; }
.readiness meter { display:block; width:100%; height:16px; margin:8px 0 3px; accent-color:var(--accent); }
.meter-labels { display:flex; justify-content:space-between; color:var(--muted); font-size:10px; }
.readiness p, .readiness details { font-size:12px; }
.recovery-options { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin:16px 0; }
.recovery-options .career-stat { border-radius:6px; padding:10px; }
.recovery-options strong { font-size:19px; }
.career-money { font-size:26px; font-weight:650; margin-top:18px; }
.career-money span { display:block; font-size:11px; color:var(--muted); font-weight:400; text-transform:uppercase; }
.career-aside .kv { font-size:12px; } .career-aside p.muted { font-size:11px; }
.career-aside .scroll table { min-width:0; width:100%; } .career-aside .scroll td { font-size:11px; padding:6px; }
.career-ratings { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:18px; }
.attribute-card { border:1px solid var(--line); border-radius:8px; padding:16px; background:var(--soft); }
.attribute-card h3 { font-size:11px; text-transform:uppercase; letter-spacing:.1em; color:var(--muted); padding-bottom:12px; border-bottom:1px solid var(--line); }
.attribute-row { display:grid; grid-template-columns:minmax(0,1fr) 40px 48px; gap:6px; padding:9px 0; align-items:center; font-size:12px; }
.attribute-row strong { text-align:right; font-size:14px; font-variant-numeric:tabular-nums; }
.attribute-delta { text-align:right; font-size:10px; }
.attribute-track { grid-column:1 / -1; height:4px; border-radius:4px; background:var(--line); overflow:hidden; }
.attribute-track i { display:block; height:100%; background:var(--accent); opacity:.65; border-radius:4px; }
.career-hub .filters { margin-bottom:0; }
.career-hub .scroll table { min-width:0; width:100%; }
.planner-intro { display:flex; align-items:center; justify-content:space-between; gap:20px; }
.planner-grid { display:grid; grid-auto-rows:1fr; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; margin:22px 0; }
.planner-week { border:1px solid var(--line); border-radius:10px; background:var(--panel); padding:20px; min-width:0; }
.planner-event-details { max-height:210px; overflow:auto; margin-top:10px; }
.planner-event-details li { margin:10px 0; font-size:12px; }
.planner-week select { max-width:100%; min-width:0; }
.planner-week legend { font-weight:750; padding:0 8px; color:var(--accent); }
.plan-option { display:block; border:1px solid var(--line); border-radius:7px; padding:11px; margin:8px 0; cursor:pointer; }
.plan-option:has(input:checked) { border-color:var(--accent); background:var(--hover); }
.plan-option input { min-height:0; accent-color:var(--accent); margin-right:6px; }
.plan-option small { display:block; margin:5px 0 0 23px; color:var(--muted); font-size:11px; }
.plan-option select { margin-top:8px; width:100%; }
.planner-fallback { border-top:1px solid var(--line); margin-top:14px; padding-top:14px; font-size:12px; }
.planner-fallback select { display:block; width:100%; margin-top:6px; }
.planner-policies { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
.planner-policies fieldset { border:1px solid var(--line); border-radius:8px; padding:15px; min-width:0; }
.planner-policies legend { font-size:12px; font-weight:650; } .planner-policies label { display:block; font-size:12px; margin:8px 0; }
.planner-policies input { min-height:0; }
.planner-save { display:flex; align-items:center; gap:18px; border-top:1px solid var(--line); padding-top:20px; margin-top:22px; }
@media(min-width:2100px){ .career-dashboard { grid-template-columns:minmax(0,3fr) minmax(340px,1fr); } .career-ratings { grid-template-columns:repeat(6,minmax(0,1fr)); } }
@media(max-width:1250px){ .career-dashboard { grid-template-columns:minmax(0,1fr) 300px; } .recap-stats { grid-template-columns:repeat(2,minmax(0,1fr)); } .career-ratings { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media(max-width:950px){ .career-dashboard { grid-template-columns:1fr; } .career-aside { display:grid; grid-template-columns:1fr 1fr; gap:18px; } .career-aside #career-inbox { grid-column:1 / -1; } }
@media(max-width:650px){ .career-hero { padding:20px; align-items:flex-start; } .career-hero h2 { font-size:24px; } .career-overall { min-width:95px; padding-left:12px; } .career-overall strong { font-size:32px; } .career-overall small { display:none; } .career-panel { padding:16px; } .career-ratings,.planner-grid,.planner-policies,.career-aside { grid-template-columns:1fr; } .career-aside #career-inbox { grid-column:auto; } .planner-intro { display:block; } }
</style>'''
from observer_career_color import STYLE as COLOR_STYLE
STYLE += COLOR_STYLE

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
        return 'Career', '<div class="career-hub">' + STYLE + no_career(w) + '</div>'
    g = v['golfer']
    y, week = v['date']
    recaps = current_recaps(v)
    latest = recaps[0] if recaps else None
    state = ('Your career' if v['status'] == 'active' else 'Choosing your next golfer' if v['status'] == 'choosing'
             else f'under AI control since {esc(wk(*v["ended"]))}' if v.get('ended') else 'Career history')
    from observer_career_progress import panels as progress_panels
    from observer_career_cycle import panel as cycle_panel
    from observer_career_legacy import panels as legacy_panels
    from observer_career_context import summary as season_summary, panels as context_panels
    from observer_career_yearend import panel as annual_panel, history as stint_history
    annual = annual_panel(w, v)
    hero = (f'<section class="career-hero"><div><div class="eyebrow">{state} · {y} season</div>'
            f'<h2>{esc(g["name"])}</h2><p>{esc(g["country"])} · Age {g["age"]} · {esc(g["tour"])}'
            f' · {esc(g["status"].title())}</p><a href="/golfer/{g["id"]}">Full player profile ↗</a>{season_summary(v)}</div>'
            f'<div class="career-overall"><span>Overall</span><strong>{g["overall"]:.1f}</strong>'
            '<small>Current ability · 0–100</small></div></section>')
    navigation = ('<div class="career-nav"><a href="#period-review">Period review</a><a href="#career-plan">Next period</a>'
                  '<a href="#career-calendar">Calendar &amp; rights</a><a href="#career-attributes">Attributes</a><a href="#career-inbox">Inbox</a></div>')
    inbox = '<section id="career-inbox" class="career-panel">' + decisions_card(w, v) + notices_card(v) + '</section>'
    body = (STYLE + '<div class="career-hub">' + hero + navigation
            + annual + cycle_panel(v, recaps) + '<div class="career-dashboard"><div class="career-main">' + recap_card(v)
            + '<section id="career-plan" class="career-panel">' + ('<h2>Next season planning</h2><p>Complete the season-transition choices above before making your next weekly plan.</p>' if annual else plan_card(w, v))
            + (advance_card(w, v) if v['status'] == 'active' and not v.get('year_end') else '') + '</section></div>'
            + '<aside class="career-aside">' + readiness_card(v) + support_card(g) + inbox + '</aside></div>'
            + context_panels(v) + progress_panels(w,v) + legacy_panels(v) + '<section id="career-attributes" class="career-panel">' + golfer_card(g, latest) + '</section>'
            + '<details class="career-details"><summary>Career details &amp; hand control back</summary>'
            + f'<p>Started {esc(wk(*v["started"]))}. Current date: {esc(wk(y, week))}.</p>'
            + stint_history(v) + end_card(w, v) + scope_note() + '</details></div>')
    return 'Career', body


def change(value, precision=2, suffix=''):
    if value is None:
        return '<span class="muted">Not recorded</span>'
    cls = 'up' if value > 0 else 'down' if value < 0 else 'muted'
    return f'<span class="{cls}">{value:+.{precision}f}{suffix}</span>'


def summary_stat(label, value, note=''):
    return f'<div class="career-stat"><span>{esc(label)}</span><strong>{value}</strong><small>{note}</small></div>'


def support_card(g):
    college = (g.get('tour_key') or '').startswith('CO_')
    team = ('<dt>Team support</dt><dd>College team coaching</dd>' if college else '')
    note = ('<p class="muted">Your college provides coaching even without a personal coach. Team and personal coaching do not stack; the stronger instruction applies.</p>' if college else '')
    return ('<section class="career-panel"><div class="eyebrow">Your support team</div><h2>Off the course</h2>'
            + f'<dl class="kv"><dt>Personal coach</dt><dd>{esc(g["coach"] or "No personal coach")}</dd>'
            + team + f'<dt>Caddie</dt><dd>{esc(g["caddie"] or "No caddie")}</dd></dl>'
            + note + f'<div class="career-money">{money(g["spendable"])}<span>Available for golf</span></div>'
            + f'<p class="muted">Funds: {money(g["funds"])}. Available money accounts for committed costs and amateur support.</p></section>')


def readiness_card(v):
    g = v['golfer']
    r = v.get('readiness', {})
    f = r.get('fatigue', g['fatigue'])
    pct = max(0, min(100, f * 100))
    label = r.get('label', 'Fresh' if pct <= 20 else 'Fatigue is affecting play')
    detail = r.get('detail', 'Fatigue above 20% reduces playing performance. Rest recovers more fatigue than practice.')
    state_class = ' readiness-caution' if pct > 20 or g['injured_until'] else ''
    out = (f'<section class="career-panel readiness{state_class}"><div class="eyebrow">Before you plan</div>'
           f'<h2>{esc(label)}</h2><div class="fatigue-number">{pct:.1f}<span>% fatigue</span></div>'
           f'<meter min="0" max="100" value="{pct}" aria-label="Fatigue: {pct:.1f} percent"></meter>'
           '<div class="meter-labels"><span>Fresh</span><span>Exhausted</span></div>'
           f'<p>{esc(detail)}</p>')
    if g['injured_until']:
        out += '<p class="banner warn">Injured: recovery comes first. The planner shows which weeks are unavailable.</p>'
    if 'rest_after' in r and 'train_after' in r and not g['injured_until']:
        out += ('<div class="recovery-options">'
                + summary_stat('After one rest week', f'{r["rest_after"] * 100:.1f}%', 'Estimated fatigue')
                + summary_stat('After one training week', f'{r["train_after"] * 100:.1f}%', 'Estimated fatigue') + '</div>')
    if r.get('forecast_note'):
        out += f'<p class="muted fine-print">{esc(r["forecast_note"])}</p>'
    if r.get('training_note'):
        out += f'<p class="muted">{esc(r["training_note"])}</p>'
    out += ('<details><summary>How to choose training or rest</summary><p>Rest clears fatigue faster. When development is enabled, training develops a selected skill group, '
            'but changes can be small. Competition also develops your game, particularly mental skills. '
            'Compare the recorded training gains below rather than judging a single week by rounded ratings.</p></details></section>')
    return out



def current_recaps(v):
    """Never compare a newly selected golfer with their predecessor's recorded ratings."""
    gid = (v.get('golfer') or {}).get('id')
    rows = v.get('recaps', [])
    if gid is None:
        return rows
    original = (v.get('stints') or [{'golfer_id': gid}])[0]['golfer_id']
    return [r for r in rows if all(w.get('golfer_id', original) == gid for w in r.get('weeks', []))]


def recap_card(v):
    recaps = current_recaps(v)
    if not recaps:
        return ('<section id="period-review" class="career-panel recap"><div class="eyebrow">Your story this season</div>'
                '<h2>Your next chapter starts here</h2><p>Plan a period, then play it. Your tournament finishes, training gains and recovery '
                'will appear here after each completed week.</p><div class="career-empty">No recorded period yet</div>'
                '<p class="muted">Older saves cannot show before-and-after details from weeks played before this update. New weeks will be recorded.</p></section>')
    out = '<section id="period-review" class="career-panel recap">' + render_recap(recaps[0], True)
    if len(recaps) > 1:
        out += '<details class="career-history"><summary>Earlier periods (' + str(len(recaps)-1) + ')</summary>'
        for r in recaps[1:]:
            out += '<details class="career-details"><summary>' + f'{r["year"]} · Weeks {r["start_week"]}–{r["end_week"]}' + '</summary>' + render_recap(r) + '</details>'
        out += '</details>'
    return out + '</section>'


def render_recap(r, latest=False):
    from observer_career_context import entry_note
    weeks = r.get('weeks', [])
    before = r.get('before') or (weeks[0].get('before', {}) if weeks else {})
    after = r.get('after') or (weeks[-1].get('after', {}) if weeks else {})
    events = [e for w in weeks for e in w.get('events', [])]
    train = sum(w.get('activity') == 'train' for w in weeks)
    rest = sum(w.get('activity') == 'rest' for w in weeks)
    delta = after.get('overall', 0) - before.get('overall', 0) if 'overall' in before and 'overall' in after else None
    f0, f1 = before.get('fatigue'), after.get('fatigue')
    fatigue = f'{f0*100:.1f}% → {f1*100:.1f}%' if f0 is not None and f1 is not None else 'Not recorded'
    out = (f'<div class="eyebrow">{"Latest period" if latest else "Period review"} · {r["year"]}</div>'
           f'<div class="section-heading"><h2>Weeks {r["start_week"]}–{r["end_week"]}</h2>'
           f'<span class="status-pill">{"Complete" if r.get("complete") else "Partial record"}</span></div>'
           '<div class="recap-stats">' + summary_stat('Tournament starts', str(len(events)), 'Recorded appearances')
           + summary_stat('Training / rest', f'{train} / {rest}', 'Weeks in this period')
           + summary_stat('Overall change', change(delta, 3), 'All recorded sources combined')
           + summary_stat('Fatigue', fatigue, 'Start → latest completed week') + '</div>')
    dev = r.get('development', {})
    if dev and any(w.get('development_recorded') for w in weeks):
        out += '<div class="development-summary"><strong>Where the growth came from</strong><p>'
        out += ' · '.join(f'{esc(k.title())} {change(x["overall"], 3)} OVR' for k, x in dev.items() if abs(x['overall']) > 0.00001)
        if not any(abs(x['overall']) > 0.00001 for x in dev.values()):
            out += 'No measurable development recorded.'
        out += '</p></div>'
    if not r.get('complete'):
        out += '<p class="muted">Recorded weeks: ' + ', '.join(str(w['week']) for w in weeks) + '. This is not a full-period comparison yet.</p>'
    out += '<div class="week-reviews">'
    for w in weeks:
        activity = w.get('activity', 'unknown')
        activity_label = {'play':'Competition', 'train':'Training', 'rest':'Recovery', 'work':'Work'}.get(activity, activity.title())
        out += f'<article class="week-review"><div class="week-stamp">W{w["week"]}</div><div class="week-story"><h3>{esc(activity_label)}</h3>'
        for e in w.get('events', []):
            pos = e.get('position')
            place = (('T' if e.get('tied') else '') + ('1st' if pos == 1 else str(pos))) if pos is not None else e.get('finish_label', 'Unplaced')
            result_class = ' result-win' if pos == 1 else ' result-top10' if pos is not None and pos <= 10 else ''
            out += f'<div class="result-row{result_class}"><strong class="result-place">{esc(place)}</strong><div><a href="/event/{quote(str(e["id"]))}">{esc(e["name"])}</a>'
            rounds = e.get('rounds') or []
            out += '<p class="muted">' + (f'Rounds: {esc(" · ".join(map(str, rounds)))}' if rounds else 'Round scores not recorded')
            if e.get('prize') is not None:
                out += f' · Prize {money(e["prize"])}'
            out += '</p></div></div>'
        out += entry_note(w.get('entry'))
        if activity == 'train':
            out += f'<p>Focus: <strong>{esc(LABEL.get(w.get("training_category"), w.get("training_category") or "Recorded training"))}</strong></p>'
        if w.get('planned'):
            out += f'<p class="muted">Planned: {esc(w["planned"])}</p>'
        for injury in w.get('injuries', []):
            available = injury.get('available')
            when = f' Eligible to return {esc(wk(*available))}.' if available else ''
            out += f'<p class="banner warn">Injury: {esc(injury.get("kind", "Recorded injury"))}. Out for {injury.get("out", "unrecorded")} weeks.{when} Low fatigue does not mean the injury has healed.</p>'
        b, a = w.get('before', {}), w.get('after', {})
        if 'fatigue' in b and 'fatigue' in a:
            out += f'<p class="week-outcomes">Fatigue {b["fatigue"]*100:.1f}% → {a["fatigue"]*100:.1f}%'
            if 'overall' in b and 'overall' in a:
                out += ' <span>·</span> Overall ' + change(a['overall']-b['overall'], 3)
            out += '</p>'
        development = w.get('development', {})
        if w.get('development_recorded') and any(abs(x['overall']) > 0.00001 for x in development.values()):
            out += '<p class="development-line">' + ' · '.join(f'{esc(k.title())}: {change(x["overall"], 3)} OVR' for k,x in development.items() if abs(x['overall']) > 0.00001) + '</p>'
        elif activity == 'train':
            out += ('<p class="muted">No measurable training gain recorded this week.</p>' if w.get('development_recorded') else '<p class="muted">Training-specific contribution is not recorded for this week.</p>')
        out += '</div></article>'
    return out + '</div><p class="muted fine-print">Rating changes are observations, not a prediction of potential. Total growth can include competition and natural maturation as well as training.</p>'

def no_career(w):
    from observer_career_yearend import STYLE as CHOICE_STYLE, candidate_card
    start = getattr(w.live, 'career_start', None)
    if start and not w.read_only:
        cards = []
        for choice in start['choices']:
            submit = (f'<form method="post" action="/career/start">{hidden(w, extra=(("golfer",choice["key"]),))}'
                      f'<button class="primary">Start career as {esc(choice["label"])}</button></form>')
            cards.append(candidate_card(w, {}, None, choice, submit_html=submit))
        return (CHOICE_STYLE + '<section class="career-panel annual-panel"><div class="eyebrow">Start the career</div>'
                '<h2>Choose your golfer</h2>' + f'<p>{esc(start["text"])}</p>'
                '<p>Everyone here already exists in this world. The list stays the same when you refresh or reopen '
                'the save. The golfers you do not choose continue their careers under AI control.</p>'
                '<p class="muted">Compare current ability, playing pathway, funds and attributes. These are current '
                'ratings, not a promise of future growth. No golfer is chosen until you press their start button.</p>'
                '<div class="newcomer-grid">' + ''.join(cards) + '</div></section>')
    return ('<p>This world has no player-controlled career.</p>'
            '<p>Start one from the <a href="/worlds">World library</a> with <strong>New Career</strong>: it creates a '
            'world and plays its first season under AI so that the first newcomer class exists. At the start of '
            'the second season, choose from up to ten of those existing golfers. Nobody is added just for the picker.</p>'
            + ('<p class="banner warn">This world is open for browsing only. Player selection cannot change this save.</p>' if w.read_only else ''))


def golfer_card(g, recap=None):
    from golfsim.ratings import ATTRIBUTE_LABELS
    weeks = (recap or {}).get('weeks', [])
    before = (recap or {}).get('before') or (weeks[0].get('before', {}) if weeks else {})
    base = before.get('attrs', {})
    cards = []
    for label, attrs in g['attrs']:
        rows = []
        for key, value in attrs:
            delta = g.get('attrs_exact', {}).get(key, value) - base[key] if key in base else None
            rows.append(f'<div class="attribute-row"><span>{esc(ATTRIBUTE_LABELS.get(key, key.replace("_", " ").title()))}</span>'
                        f'<strong>{value:.1f}</strong><span class="attribute-delta">{change(delta, 2) if delta is not None else "—"}</span>'
                        f'<div class="attribute-track"><i style="width:{max(0,min(100,value)):.1f}%"></i></div></div>')
        cards.append(f'<div class="attribute-card"><h3>{esc(label)}</h3>' + ''.join(rows) + '</div>')
    return ('<div class="eyebrow">Player development</div><div class="section-heading"><h2>Your attributes</h2>'
            f'<a href="/golfer/{g["id"]}?tab=playing#career-ratings">Full development history ↗</a></div>'
            '<p class="muted">Current ratings on the same 0–100 scale as player profiles. Change is since the start of the latest recorded period, '
            'not training alone. These are profile groups, not training categories. Potential stays hidden.</p><div class="career-ratings">' + ''.join(cards) + '</div>')

def plan_card(w, v):
    out = ['<div class="eyebrow">Look ahead</div><h2>Your next period</h2><p class="muted">Planning is in four-week periods (the engine\'s thirteen blocks a season, '
           'not calendar months). A plan is an intention: entry, selection and payment are decided by the same rules as '
           'for every golfer when the week comes.</p>']
    for b in v['blocks']:
        y, w0 = b['block']
        rows = [[str(x['week']), esc(x['text']), 'played' if x['played'] else 'planned'] for x in b['weeks']]
        pol = b['policy']
        out.append(f'<h3>Period {(w0 - 1) // 4 + 1} of 13 · Weeks {w0}–{w0 + 3} of {y}</h3>' + table(['Week', 'Plan', ''], rows)
                   + f'<p class="muted">If selected or invited: {esc(pol["selected"])}. Qualifying: {esc(pol["qualifying"])}.</p>')
    for (py, p0) in v['plannable']:
        out.append(f'<p><a class="button" href="/career/plan?block={py}-{p0}">Plan weeks {p0}–{min(52, p0 + 3)} of {py}</a></p>')
    return ''.join(out)


def decisions_card(w, v):
    if not v['pending']:
        return '<h2>Decisions</h2><p class="muted">Nothing to decide now.</p>' + resolved_list(v)
    out = ['<h2>Decisions</h2>']
    annual_ids = {d['id'] for d in (v.get('year_end') or {}).get('decisions', [])}
    if annual_ids:
        out.append('<p><a href="#annual-review">Make your season-transition choices above</a></p>')
    for d in v['pending']:
        if d['id'] in annual_ids:
            continue
        due = ('before ' + wk(*d['deadline']) + ' is played') if d['deadline'] else 'now'
        acts = ''
        if d['kind'] in ('plan', 'replan'):
            b = d['payload'].get('block') or [d['payload']['week'][0], ((d['payload']['week'][1] - 1) // 4) * 4 + 1]
            acts = f'<a class="button primary" href="/career/plan?block={b[0]}-{b[1]}">Open the planner</a>'
        elif d['kind'] in ('coach_offer', 'caddie_offer', 'job', 'market_choice'):
            acts = ''.join(f'<form method="post" action="/career/decide" style="display:inline">'
                           f'{hidden(w, v["version"], (("decision", d["id"]), ("answer", a)))}'
                           f'<button{" class=primary" if a == "accept" else ""}>{dict(accept="Accept",decline="Decline",yes="Yes",no="No").get(a,a)}'
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
    return (f'<div class="filters"><form method="post" action="/career/advance">{hidden(w, v["version"], (("mode", "next"),))}'
            '<button title="Plays on until something needs your decision">Advance to next decision</button>'
            f'</form><form method="post" action="/career/advance">{hidden(w, v["version"], (("mode", "period"),))}'
            '<button class="primary" title="Plays to the end of the current four-week period, stopping earlier only if a decision is due">'
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
            'pathway, saving and annual decisions. At the season review, continue this golfer, switch to a newcomer next year, or end player control. '
            'Existing saves from earlier engines may be browse-only; an ended career is not automatically resumed.</p>')


# ---- the planner ----------------------------------------------------------------------------------------------------


def training_categories_help():
    from golfsim.development import CATEGORIES
    from golfsim.ratings import ATTRIBUTE_LABELS
    rows = ''.join('<dt>' + esc(LABEL[k]) + '</dt><dd>' +
                   esc(', '.join(ATTRIBUTE_LABELS[a] for a in attrs)) + '</dd>'
                   for k, attrs in CATEGORIES.items())
    return ('<details class="career-details"><summary>What each training focus covers</summary>'
            '<p>Profile groups describe shot skills. Training groups describe practice sessions and differ: '
            'short-game practice includes wedge play; long-game practice includes ball-striking consistency. '
            'Choosing a focus does not guarantee an equal gain in every skill.</p><dl class="kv">' + rows + '</dl></details>')



def event_choice(o, cur, evidence=None):
    """A bounded event selector; all details remain readable without JavaScript."""
    from observer_course_context import cue
    course_by_id = {e["event_id"]: e.get("course_fit") for e in (evidence or {}).get("play", [])}
    outlook_by_id = {e["event_id"]: e.get("entry_outlook") for e in (evidence or {}).get("play", [])}
    from observer_career_context import target_note
    n = o['week']
    events = [e for e in o['events'] if e['eligible'] and e.get('affordable')]
    available = bool(events) and not o['injured_until']
    disabled = '' if available else ' disabled'
    chosen = cur.get('event_id') if cur.get('kind') == 'event' else None
    selected = ' checked' if chosen and available else ''
    options = ['<option value=""' + (' selected' if chosen not in {e['event_id'] for e in events} else '') +
               '>' + ('Choose a tournament' if available else 'No tournament available to enter') + '</option>']
    for e in events:
        pick = ' selected' if e['event_id'] == chosen else ''
        options.append(f'<option value="{esc(e["event_id"])}"{pick}>{esc(e["name"])} · {money(e["cost"])} estimated{esc(cue(course_by_id.get(e["event_id"])))}</option>')
    details = []
    for e in o['events']:
        reason = ('Unavailable while injured' if o['injured_until'] else
                  'Eligible to request entry' if e['eligible'] and e.get('affordable') else e['why'])
        cost_label = f'Estimated cost {money(e["cost"])}' if e.get('cost') is not None else 'Cost not quoted'
        details.append(f'<li><a href="/event/{quote(e["event_id"])}">{esc(e["name"])}</a><br>'
                       f'{esc(e["city"])}, {esc(e["country"])} · {esc(e["tour"])} · {cost_label}<br>{esc(reason)}<br>{entry_panel(outlook_by_id.get(e["event_id"]))}{target_note(e)}{course_panel(course_by_id.get(e["event_id"]))}</li>')
    return (f'<div class="plan-option"><label><input type="radio" name="w{n}" value="event"{selected}{disabled} required> '
            f'Enter a tournament</label><select name="e{n}" aria-label="Tournament for week {n}"{disabled}>' + ''.join(options) +
            '</select><small>Choose this activity and a tournament. Request an entry. Your fallback applies if it is not accepted.</small></div>'
            '<details><summary>Event details &amp; eligibility</summary><div class="planner-event-details">' +
            ('<ul>' + ''.join(details) + '</ul>' if details else '<p>No events are listed for this week.</p>') + '</div></details>')


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
    from observer_career_context import target_note
    from observer_career_training import panel as training_comparison
    from observer_career_advice import committed_plan, render_advice
    p = committed_plan(p, v)
    cats = ''.join(f'<option value="{k}">{esc(label)}</option>' for k, label in CATS)
    rows = []
    for o in p['weeks']:
        n = o['week']
        course_by_id = {e['event_id']: e.get('course_fit') for e in v.get('week_compare', {}).get(str(n), {}).get('play', [])}
        outlook_by_id = {e['event_id']: e.get('entry_outlook') for e in v.get('week_compare', {}).get(str(n), {}).get('play', [])}
        cur = o['current'] or {}
        opts = [event_choice(o, cur, v.get("week_compare", {}).get(str(n)))]
        train_disabled = ' disabled' if o['injured_until'] else ''
        tsel = ' checked' if cur.get('kind') == 'train' and not o['injured_until'] else ''
        rsel = ' checked' if cur.get('kind') == 'rest' else ''
        csel = cur.get('category') if cur.get('kind') == 'train' else None
        catsel = ''.join(f'<option value="{k}"{" selected" if k == csel else ""}>{esc(label)}</option>' for k, label in CATS)
        opts.append(f'<label class="plan-option"><input type="radio" name="w{n}" value="train"{tsel}{train_disabled} required> Focused training '
                    f'<small>Develop one part of your game. Changes are recorded in your period review.</small><select name="c{n}" aria-label="Training for week {n}"{train_disabled}>{catsel}</select></label>')
        opts.append(f'<label class="plan-option"><input type="radio" name="w{n}" value="rest"{rsel} required> Rest &amp; recover<small>Clear fatigue faster. No direct skill training this week.</small></label>')
        work = o.get('work', {})
        if work.get('available'):
            work_selected = ' checked' if cur.get('kind') == 'work' else ''
            opts.append(f'<label class="plan-option"><input type="radio" name="w{n}" value="work"{work_selected} required> Paid work '
                        f'<small>Weekly wage: {money(work.get("wage"))}. No direct skill training this week.</small></label>')
        fb = cur.get('fallback') or {}
        fsel = lambda val: ' selected' if (fb.get('kind') == 'train' and val == f'train:{fb.get("category")}') or \
            (fb.get('kind') == 'rest' and val == 'rest') else ''
        fallback = (f'<select name="f{n}" aria-label="If the entry is not accepted in week {n}">'
                    + ''.join(f'<option value="train:{k}"{fsel("train:" + k)}>train {esc(label.lower())}</option>' for k, label in CATS)
                    + f'<option value="rest"{fsel("rest")}>rest</option></select>')
        sel_ev = ('<ul>' + ''.join(f'<li>{esc(e["name"])} ({esc(e["rule"])}){entry_panel(outlook_by_id.get(e["event_id"]))}{target_note(e)}{course_panel(course_by_id.get(e["event_id"]))}</li>' for e in o['selected']) + '</ul>'
                  if o['selected'] else '<span class="muted">none</span>')
        inj = f'<p class="banner warn">Injured this week: only rest is possible.</p>' if o['injured_until'] else ''
        rows.append(f'<fieldset class="planner-week"><legend>Week {n}</legend>' + inj + comparison(v,n) + ''.join(opts)
                    + '<div class="planner-fallback"><strong>If your event entry is not accepted</strong>' + fallback
                    + '</div><details><summary>Selection-only events</summary>' + sel_ev + '</details></fieldset>')
    pol = p['policy'] if p['policy'] is not None else {'selected': 'accept', 'qualifying': 'enter'}
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
            + money_line + '<div class="planner-grid">' + ''.join(rows) + '</div>'
            + '<div class="planner-policies">' + policy + '</div><div class="planner-save"><button class="primary">Save the plan</button> <a href="/career">Cancel</a></div></form>')
    note = ('<p class="muted">Events you can enter are listed with their cost; the others are folded under each week with '
            'the rule that keeps you out. An entry is not a place: fields fill in each event\'s entry order, and if yours '
            'is not accepted the week falls back to what you choose here. Events that choose their own fields are covered '
            'by the period\'s policy below.</p>')
    return f'Plan weeks {w0}–{min(52, w0 + 3)} of {y}', STYLE + '<div class="career-hub"><p class="back"><a href="/career">← Career overview</a></p><div class="planner-intro"><p>Build a period that balances competition, development and recovery.</p></div>' + readiness_card(v) + '<details><summary>How event entry works</summary>' + note + '</details>' + training_categories_help() + training_comparison(v) + render_advice(p) + form + '</div>'


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
        if val == 'event':
            event_id = one(form, f'e{n}')
            if not event_id:
                return None  # Let the existing incomplete-form path refuse without changing the world.
            val = 'event:' + event_id
        if val.startswith('event:'):
            fb = one(form, f'f{n}') or ''
            weeks[str(n)] = {'kind': 'event', 'event_id': val[6:],
                             'fallback': ({'kind': 'train', 'category': fb[6:]} if fb.startswith('train:') else {'kind': 'rest'})}
        elif val == 'train':
            weeks[str(n)] = {'kind': 'train', 'category': one(form, f'c{n}')}
        elif val in ('rest', 'work'):
            weeks[str(n)] = {'kind': val}
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
