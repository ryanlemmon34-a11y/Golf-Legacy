"""Read-only presentation of the committed career financial and weekly evidence."""
from html import escape as esc
from observer_course_context import panel as course_panel

def dollars(x):
    return 'Not recorded' if x is None else f'${x:,.0f}'

def economy(v):
    m=v.get('money')
    if not m:
        return ''
    funds=m['funds'];s=m['sponsor'];b=m['backer']
    out='<section class="career-panel"><h2>Career finances</h2><p>Available for golf: <strong>'+dollars(funds['spendable'])+'</strong></p><details><summary>Cash, backing and sponsor explanation</summary><p>Personal cash: '+dollars(funds['cash'])+' · Family backing: '+dollars(funds['family_backing'])+' · Backer funds: '+dollars(funds['backer_funds'])+'</p><p>Season sponsor contract: '+dollars(s['contract'])+'. '+esc(s['rule'])+'. Current Prestige: '+str(s['prestige'])+'.</p><p>Formula at current Prestige: '+dollars(s['at_this_prestige_now'])+'; this is not a new contract or additional payment.</p><p>Annual backing deal: '+dollars(b['deal'])+' · Put up this season: '+dollars(b['put_up'])+' · Returned: '+dollars(b['returned'])+'</p></details>'
    for year,ledger in sorted(m['seasons'].items(),reverse=True):
        out+='<details><summary>'+esc(year)+' ledger</summary>'
        if ledger is None:
            out+='<p>No ledger recorded here.</p>'
        else:
            out+='<p>Income '+dollars(ledger['total_income'])+' · Costs '+dollars(ledger['total_costs'])+' · Net '+dollars(ledger['net'])+'</p>'
            for group in ('income','costs'):
                out+='<h3>'+group.title()+'</h3><ul>'+''.join('<li>'+esc(m['labels'].get(k,k))+': '+dollars(amount)+'</li>' for k,amount in ledger[group].items())+'</ul>'
            out+='<p class="muted">Ledger includes in-kind amateur support. Net is not necessarily the change in personal cash.</p>'
        out+='</details>'
    return out+'</section>'

def seasons(v):
    rows=v.get('seasons_summary')
    if rows is None:
        return ''
    out='<details class="career-details"><summary>Season-by-season career record</summary><p>Recorded controlled weeks only; an incomplete season is not a full-year total.</p>'
    for r in rows:
        out+='<article><h3>'+str(r['year'])+' · '+esc(r['name'])+'</h3><p>'+str(r['recorded_weeks'])+' recorded weeks · '+str(r['events'])+' events · '+str(r['wins'])+' wins · '+str(r['top10'])+' top tens · '+str(r['missed_cuts'])+' missed cuts · Prize '+dollars(r['prize_money'])+'</p></article>'
    return out+('</details>' if rows else '<p>No controlled seasons recorded yet.</p></details>')

def comparison(v,week):
    r=v.get('week_compare',{}).get(str(week))
    if not r:
        return ''
    load=r['load']
    pct=lambda n:'Not recorded' if n is None else f'{100*n:.1f}%'
    out='<details class="week-evidence"><summary>Compare this week’s tradeoffs</summary><p>Current fatigue '+pct(load['fatigue'])+' · Performance penalty begins above '+pct(load['performance_threshold'])+'.</p>'
    if load.get('injured_until'):
        out+='<p>Injury restricts this week to recovery.</p>'
    else:
        out+='<p>One training week from the current state: '+pct(load['train_fatigue_after'])+' fatigue. One rest week: '+pct(load['rest_fatigue_after'])+'. These are independent previews, not a forecast of the whole plan.</p>'
    out+='<p>Recorded competition: '+str(load['played_last_4'])+' in the preceding four weeks; '+str(load['played_last_8'])+' in eight.</p>'
    for e in r['play']:
        state='Selection required' if e.get('selected_field') else ('Eligible to attempt entry' if e['eligible'] else 'Not eligible')
        out+='<p><strong>'+esc(e['name'])+'</strong>: '+state+'; cost '+dollars(e.get('cost'))+'. '+esc(e.get('why') or '')+'</p>'
        out+=course_panel(e.get('course_fit'))
        history=e.get('last_edition')
        if history:
            out+='<p class="muted"><strong>Previous edition ('+str(history['year'])+')</strong>: '+str(history['asked'])+' applications; '+str(history['admitted'])+' admitted from '+str(history['capacity'])+' places. '+('Field filled.' if history['full'] else 'Field did not fill.')+' Late fills: '+str(history['late_fills'])+'.</p>'
            if history.get('closed_at'):
                out+='<p class="muted">Last recorded entry class: '+esc(history['closed_at'])+'.</p>'
            out+='<p class="muted">Historical context only, not a forecast or your chance of entry.</p>'
        for route in e.get('opportunities',[]):
            t=route['target']
            out+='<p>'+esc(route['condition']['text'])+' → '+esc(t['label'])+' · week '+str(t['week'])+' of '+str(t['year'])+'. '+esc(route['status'].replace('_',' '))+'.</p>'
    return out+'<p class="muted">Eligibility is not admission. Entry probability is not estimated. Training grades are fallible assessments, not promised gains.</p></details>'
