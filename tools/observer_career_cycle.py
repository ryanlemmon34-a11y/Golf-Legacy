"""Join factual outcomes to the next player decision. No generated narrative or assumed goals."""
from urllib.parse import quote
from observer import esc

STYLE='''<style>
.career-cycle{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0;border:1px solid var(--career-frame,var(--line));border-radius:10px;overflow:hidden;margin:20px 0;background:var(--panel);box-shadow:var(--career-shadow)}
.cycle-step{padding:18px;border-right:1px solid var(--line);border-top:3px solid var(--career-green,var(--accent));min-width:0}.cycle-step:last-child{border-right:0;border-top-color:var(--career-blue,var(--accent))}.cycle-step:first-child{border-top-color:var(--career-gold,var(--accent))}
.cycle-step h3{font-size:14px;margin:6px 0}.cycle-step p{font-size:12px;margin:8px 0}.cycle-step a{font-size:12px;font-weight:650}
@media(max-width:800px){.career-cycle{grid-template-columns:1fr}.cycle-step{border-right:0;border-bottom:1px solid var(--line)}}
</style>'''

def panel(v,recaps):
    if v.get('status')!='active' or v.get('year_end'):
        return ''
    past='<h3>Your story starts here</h3><p>Your first completed period will record competition, development and recovery here.</p>'
    if recaps:
        r=recaps[0];weeks=r.get('weeks',[])
        events=[e for w in weeks for e in w.get('events',[])]
        placed=[e for e in events if e.get('position') is not None]
        best=min(placed,key=lambda e:e['position']) if placed else None
        past='<h3>Weeks '+str(r['start_week'])+'–'+str(r['end_week'])+'</h3><p>'+str(len(events))+' recorded tournament starts. '
        if best:
            past+='Best finish: '+('T' if best.get('tied') else '')+str(best['position'])+' in '+esc(best['name'])+'.'
        else:
            past+='Review training, recovery and any competition below.'
        if not r.get('complete'):
            past+=' In progress: '+str(len({w.get("week") for w in weeks if w.get("week") is not None}))+' of 4 weeks recorded; this period continues after the decision.'
        past+='</p><a href="#period-review">See what changed →</a>'
    pending=v.get('pending',[])
    middle='<h3>'+str(len(pending))+' decision'+('s' if len(pending)!=1 else '')+' awaiting you</h3>' if pending else '<h3>Choose your next focus</h3>'
    date=v.get('date') or (v.get('plannable') or [None])[0]
    if date:
        first=1+4*((date[1]-1)//4)
        middle='<span class="status-pill">Period '+str((first-1)//4+1)+' of 13 · weeks '+str(first)+'–'+str(first+3)+'</span>'+middle
    g=v['golfer'];fatigue=g.get('fatigue',0)
    if g.get('injured_until'):
        middle+='<p>Recovery comes first while the recorded injury keeps you out.</p>'
    elif fatigue>.2:
        middle+='<p>Fatigue is above the performance threshold. Consider recovery before adding competition.</p>'
    else:
        middle+='<p>Balance a chance to compete against practice time, travel cost and recovery.</p>'
    if pending:
        middle+='<a href="#career-inbox">Review decisions and deadlines →</a>'
    elif v.get('plannable'):
        y,w=v['plannable'][0]
        middle+='<a href="/career/plan?block='+str(y)+'-'+str(w)+'">Build the next plan →</a>'
    upcoming=v.get('context',{}).get('upcoming',[])
    if upcoming:
        e=min(upcoming,key=lambda e:(e['week'],e.get('tier',99),e['event_id']))
        nxt='<h3>Week '+str(e['week'])+' · On the calendar</h3><p><a href="/event/'+quote(str(e['event_id']))+'">'+esc(e['name'])+'</a></p><p>'+esc(e['status'])+'</p><a href="#career-calendar">Compare upcoming opportunities →</a>'
    else:
        nxt='<h3>Look beyond this period</h3><p>No relevant events are listed in the current watchlist window. Training and recovery can still move your career forward.</p>'
    return STYLE+'<section class="career-cycle" aria-label="Your next four-week cycle">'+''.join('<div class="cycle-step"><div class="eyebrow">'+label+'</div>'+body+'</div>' for label,body in [('What happened',past),('Your decision',middle),('What comes next',nxt)])+'</section>'
