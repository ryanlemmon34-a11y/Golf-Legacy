"""Presentation and forms for committed opportunities, goals, timeline and staff-search policy."""
from urllib.parse import quote
from observer import esc

STATUS={'already_qualified':'Already qualified','needs_result':'Result required','awaiting_selection':'Awaiting selection','not_eligible':'Not eligible'}

def opportunities(rows):
    if rows is None:
        return ''
    out=[]
    for r in rows:
        e,t=r['event'],r['target']
        restrictions=''.join('<li>'+esc(x)+'</li>' for x in r.get('restrictions',[]))
        out.append('<article class="career-details"><span class="status-pill">'+esc(STATUS.get(r['status'],'Status not recorded'))+'</span><h3><a href="/event/'+quote(str(e['id']))+'">'+esc(e['label'])+'</a> · week '+str(e['week'])+' of '+str(e['year'])+'</h3><p><strong>'+esc(r['condition']['text'])+'</strong> → <a href="/event/'+quote(str(t['id']))+'">'+esc(t['label'])+'</a> · week '+str(t['week'])+' of '+str(t['year'])+'</p>'+('<ul>'+restrictions+'</ul>' if restrictions else '')+'<small>Rule: '+esc(r['route']['label'])+'</small></article>')
    return '<section id="career-pathways" class="career-panel"><div class="eyebrow">Choose events for what they unlock</div><h2>Qualification pathways</h2><p class="muted">Requirements below come from the implemented rules. An upcoming route is not an earned place. Follow the recorded status and restrictions.</p>'+(''.join(out) if out else '<p>No upcoming placement-based routes are recorded for this golfer.</p>')+'</section>'


def timeline(rows):
    if rows is None:
        return ''
    return '<details class="career-details"><summary>Career timeline · recorded history</summary><ol>'+''.join('<li><strong>'+str(r['date'][0])+' · week '+str(r['date'][1])+'</strong> · '+esc(r['text'])+'</li>' for r in reversed(rows))+'</ol></details>'


def goals(w,v):
    if 'goals' not in v:
        return ''
    from observer_career import hidden
    editable=v['status']=='active' and not getattr(w,'read_only',False)
    out='<section id="career-goals" class="career-panel"><h2>Your goals</h2><p class="muted">Optional targets you choose. Goals do not change ability, eligibility, odds or outcomes.</p>'
    for g in v['goals']:
        title=g.get('label') or (('World' if g['kind']=='world_rank' else 'Amateur')+' top '+str(g.get('top'))) if g['kind'] in ('world_rank','amateur_rank') else g.get('label',g.get('series_id','Event goal'))
        out+='<article class="career-details"><strong>'+esc(g['kind'].replace('_',' ').title()+': '+title)+'</strong><p>By '+str(g['by_year'])+' · '+esc(g['status'].title())+'</p>'
        if g.get('progress') and g['progress'].get('position') is not None:
            out+='<p>Current rank: '+str(g['progress']['position'])+'</p>'
        if editable and g['status']=='active':
            out+='<form method="post" action="/career/drop_goal">'+hidden(w,v['version'],(('goal_id',g['id']),))+'<button>Drop this goal</button></form>'
        out+='</article>'
    if not v['goals']:
        out+='<p>No goals set. You can still play normally.</p>'
    if editable:
        y=v['date'][0];events={}
        for r in v.get('opportunities') or []:
            for e in (r['event'],r['target']):
                events[e['series_id']]=e['label']
        for e in v.get('context',{}).get('upcoming',[]):
            events[str(e['event_id']).split(':',1)[-1]]=e['name']
        opts=''.join('<option value="'+esc(k)+'">'+esc(label)+'</option>' for k,label in sorted(events.items(),key=lambda p:p[1]))
        out+='<details><summary>Set an optional goal</summary><form method="post" action="/career/set_goal">'+hidden(w,v['version'])+'<p><label>Goal <select name="kind"><option value="world_rank">World ranking</option><option value="amateur_rank">Amateur ranking</option><option value="play_in">Play in an event</option><option value="win">Win an event</option></select></label></p><p><label>Event, for play/win goals <select name="series_id">'+opts+'</select></label></p><p><label>Top rank, for ranking goals <input name="top" type="number" min="1" max="1000" value="100"></label></p><p><label>Target year <input name="by_year" type="number" min="'+str(y)+'" max="'+str(y+10)+'" value="'+str(y)+'" required></label></p><button class="primary">Set goal</button></form></details>'
    return out+'</section>'


def staff_search(w,v):
    if 'staff_policy' not in v or v['status']!='active' or getattr(w,'read_only',False):
        return ''
    from observer_career import hidden
    out='<section class="career-panel"><h2>Staff search preferences</h2><p>At the next applicable January staff market, search using the same rules as AI golfers. Availability and acceptance are not guaranteed.</p><form method="post" action="/career/staff_policy">'+hidden(w,v['version'])
    for key,label in [('seek_coach','Look for a coach'),('seek_caddie','Look for a caddie')]:
        out+='<p><label>'+label+' <select name="'+key+'">'+''.join('<option value="'+k+'"'+(' selected' if v['staff_policy'].get(key,'no')==k else '')+'>'+text+'</option>' for k,text in [('no','No search'),('yes','Search'),('ask','Ask me at the market')])+'</select></label></p>'
    return out+'<button>Save search preferences</button></form></section>'


def panels(w,v):
    return opportunities(v.get('opportunities'))+goals(w,v)+staff_search(w,v)+timeline(v.get('timeline'))
