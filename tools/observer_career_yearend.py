"""Presentation of committed annual career snapshots. No simulation calls or default decisions."""
from observer import esc, table

STYLE = '''<style>
.annual-panel { border-top:3px solid var(--accent); }
.annual-steps { display:flex; flex-wrap:wrap; gap:8px; margin:12px 0 22px; padding:0; list-style:none; }
.annual-steps li { font-size:11px; padding:6px 10px; border:1px solid var(--line); border-radius:20px; color:var(--muted); }
.annual-steps [aria-current=step] { background:var(--soft); border-color:var(--accent); color:var(--accent); font-weight:700; }
.annual-options,.newcomer-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; margin:16px 0; }
.annual-choice,.newcomer-card { padding:18px; border:1px solid var(--line); border-radius:8px; background:var(--soft); min-width:0; }
.annual-choice form { margin-top:14px; } .annual-choice p,.newcomer-card p { font-size:12px; }
.annual-choice h3,.newcomer-card h3 { font-size:16px; }
.newcomer-heading { display:flex; align-items:start; justify-content:space-between; gap:14px; }
.newcomer-rating { font-size:25px; color:var(--accent); font-weight:700; }
.newcomer-rating small { display:block; font-size:10px; color:var(--muted); font-weight:400; }
.newcomer-card .kv { font-size:12px; } .newcomer-card details { margin:14px 0; }
.annual-decision { padding-top:20px; border-top:1px solid var(--line); margin-top:20px; }
.annual-facts { font-size:12px; margin:10px 0; } .annual-facts dt { color:var(--muted); }
.annual-facts dd { margin:0 0 9px; }
@media(max-width:650px){ .annual-options,.newcomer-grid { grid-template-columns:1fr; } }
</style>'''


def known(value, money=False):
    if value is None:
        return 'Not recorded'
    return f'${value:,.0f}' if money else esc(str(value))


def button(w, v, decision, choice, disabled=False):
    from observer_career import hidden
    key, label = choice['key'], choice['label']
    destructive = key in ('end_career', 'retire')
    confirm = ('<label><input type="checkbox" required> I understand this ends my player-controlled career.</label><br>' if key == 'end_career' else
               '<label><input type="checkbox" required> I understand this retires this golfer from competition.</label><br>'
               if destructive else '')
    return (f'<form method="post" action="/career/decide">'
            + hidden(w, v['version'], (('decision', decision['id']), ('answer', key)))
            + confirm + f'<button{" class=primary" if key in ("keep", "continue", "stay_in_college") else ""}'
            + (' disabled' if disabled else '') + f'>{esc(label)}</button></form>')


def facts_html(facts):
    labels = {'tour':'Next tour', 'amateur_rank':'Amateur rank', 'reason':'Eligibility',
              'results':'Recent results', 'season_cost':'Estimated season cost',
              'cannot_return_full_time':'Full-time return unavailable', 'cost':'Moving cost',
              'travel_saved':'Estimated travel savings (negative means higher costs)', 'own':'Own-country move'}
    out = ''
    if facts.get('detail'):
        out += '<p>' + esc(facts['detail']) + '</p>'
    pairs = []
    for key, label in labels.items():
        if key in facts:
            val = facts[key]
            text = ('Yes' if val else 'No') if isinstance(val, bool) else known(val, key in ('cost','travel_saved','season_cost'))
            pairs.append(f'<dt>{esc(label)}</dt><dd>{text}</dd>')
    return out + ('<dl class="annual-facts">' + ''.join(pairs) + '</dl>' if pairs else '')


def candidate_card(w, v, decision, choice):
    from golfsim.ratings import ATTRIBUTE_LABELS
    g = choice['facts']
    attrs = []
    for group, rows in g['attrs']:
        attrs.append('<h4>' + esc(group) + '</h4><dl class="kv">' + ''.join(
            f'<dt>{esc(ATTRIBUTE_LABELS.get(key,key))}</dt><dd>{known(value)}</dd>' for key,value in rows) + '</dl>')
    return ('<article class="newcomer-card"><div class="newcomer-heading"><div><h3>' + esc(g['name']) + '</h3>'
            + f'<p>{esc(g["country"])} · Age {g["age"]}</p></div><div class="newcomer-rating">{known(g["overall"])}<small>Overall · 0–100</small></div></div>'
            + f'<p>{esc(g["tour"])} · {esc(g["status"])} · {esc(g["lifestyle"].replace("_"," "))}</p>'
            + '<p>Funds: ' + known(g['funds'],True) + '</p><details><summary>View attributes</summary>' + ''.join(attrs) + '</details>'
            + button(w,v,decision,{'key':choice['key'],'label':'Play as ' + g['name']}) + '</article>')


def review_html(review):
    from observer_career import summary_stat, change
    if not review:
        return '<p>No season summary was recorded.</p>'
    delta = (review['overall_now'] - review['overall_start']
             if review.get('overall_now') is not None and review.get('overall_start') is not None else None)
    out = f'<h3>{esc(review["name"])} · {review["year"]} season</h3><div class="recap-stats">'
    for label, key in (('Starts','events'),('Wins','wins'),('Top 10s','top10'),('Missed cuts','missed_cuts')):
        out += summary_stat(label, known(review.get(key)))
    out += '</div><div class="recap-stats">' + summary_stat('Prize money',known(review.get('prize_money'),True))
    out += summary_stat('Recorded income',known(review.get('income'),True),'Not profit or net earnings')
    out += summary_stat('Overall change',change(delta,3),'All development sources')
    out += summary_stat('Available funds',known(review.get('funds'),True)) + '</div>'
    best = review.get('best_finish')
    if best:
        out += '<p><strong>Best finish:</strong> ' + ('T' if best.get('tied') else '') + known(best['position']) + ' · ' + esc(best['event']) + '</p>'
    out += '<p>World rank: ' + known(review.get('world_rank')) + ' · Amateur rank: ' + known(review.get('amateur_rank')) + '</p>'
    out += '<p class="muted">Recorded activity: ' + esc(' · '.join(f'{k.title()} {n} weeks' for k,n in review.get('activity',{}).items()) or 'None recorded') + '</p>'
    if not review.get('complete'):
        out += f'<p class="banner warn">Partial record: {review.get("recorded_weeks",0)} weeks recorded. Missing history is not reconstructed.</p>'
    return out


def panel(w, v):
    ye = v.get('year_end')
    if not ye:
        return ''
    stage = ye['stage']
    titles = {'season_review':'Your season. Your next chapter.', 'winter_choices':'Shape next season',
              'winter_residence':'Choose your home base', 'choose_newcomer':'Choose your next golfer',
              'winter_running':'Ready for the next winter stage', 'winter_ai':'The world moves into a new season'}
    current = 0 if stage == 'season_review' else 2 if stage == 'choose_newcomer' else 1
    out = STYLE + '<section id="annual-review" class="career-panel annual-panel"><div class="eyebrow">Season transition</div><h2>' + titles.get(stage,'Season review') + '</h2><ol class="annual-steps">'
    out += ''.join(f'<li{" aria-current=step" if i == current else ""}>{i+1}. {name}</li>' for i,name in enumerate(('Review & intent','Winter decisions','Next season')))
    out += '</ol>'
    review = review_html(ye.get('review'))
    out += review if stage == 'season_review' else '<details class="career-details"><summary>Review the completed season</summary>' + review + '</details>'
    blocked = bool(ye.get('offers'))
    if blocked:
        out += '<p class="banner warn">Answer the pending offers in your inbox before choosing the next chapter.</p>'
    for d in ye.get('decisions',[]):
        out += '<section class="annual-decision"><h3>' + esc(d['text']) + '</h3>'
        if d['kind'] == 'choose_newcomer':
            out += '<p>These golfers already exist in this season’s newcomer class. The list is fixed, not rerolled when you refresh. Everyone you do not choose continues under AI control.</p><div class="newcomer-grid">'
            out += ''.join(candidate_card(w,v,d,c) for c in d['choices'] if 'id' in c['facts']) + '</div>'
            for c in d['choices']:
                if 'id' not in c['facts']:
                    out += facts_html(c['facts']) + button(w,v,d,c)
        else:
            out += '<div class="annual-options">' + ''.join('<article class="annual-choice"><h3>' + esc(c['label']) + '</h3>' + facts_html(c.get('facts',{})) + button(w,v,d,c,blocked) + '</article>' for c in d['choices']) + '</div>'
        out += '</section>'
    if not ye.get('decisions') and not blocked:
        from observer_career import hidden
        out += '<p>Your answers are saved. Continue to the next stage; the simulation stops if another choice is needed.</p>'
        out += f'<form method="post" action="/career/advance">{hidden(w,v["version"],(("mode","next"),))}<button class="primary">Continue winter</button></form>'
    return out + '</section>'


def history(v):
    from observer_career import wk
    rows = [[esc(x['name']),esc(wk(*x['from'])),esc(wk(*x['to'])) if x.get('to') else 'Current golfer'] for x in v.get('stints',[])]
    if not rows:
        return ''
    out = '<h3>Your golfers</h3>' + table(['Golfer','Control began','Control ended'],rows)
    from observer_career import render_recap
    for stint in v.get('stints', []):
        if not stint.get('to'):
            continue
        recaps = [r for r in v.get('recaps', []) if r.get('weeks') and
                  all(w.get('golfer_id',v['stints'][0]['golfer_id']) == stint['golfer_id'] for w in r['weeks'])]
        if recaps:
            out += '<details class="career-details"><summary>Recorded periods: ' + esc(stint['name']) + '</summary>'
            out += ''.join(render_recap(r) for r in recaps) + '</details>'
    return out
