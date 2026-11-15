"""Read-only practice comparisons from visible skills and recorded outcomes, never true ceilings."""
from observer import esc
from observer_career_advice import GROUPS
from observer_career_legacy import GRADE_COLORS

LABELS={'physical':'Physical','long_game':'Long game','short_game':'Short game','putting':'Putting','mental':'Mental game'}
STYLE='''<style>
.training-compare{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:16px 0}
.training-compare article{border:1px solid var(--career-frame,var(--line));border-top:3px solid var(--career-violet,var(--accent));border-radius:8px;padding:14px;background:var(--panel)}
.training-compare h3{font-size:14px}.training-current{font-size:25px;font-weight:750;color:var(--career-green,var(--accent))}.training-compare p{font-size:12px}.training-estimate{display:inline-block;padding:3px 8px;border:1px solid currentColor;border-radius:5px;font-weight:700;font-size:12px}
</style>'''

def panel(v):
    g=v.get('golfer',{});attrs=g.get('attrs_exact',{})
    means={k:sum(attrs[a] for a in keys if a in attrs)/sum(a in attrs for a in keys)
           for k,keys in GROUPS.items() if any(a in attrs for a in keys)}
    if not means:
        return ''
    estimates={str(r['category']).lower().replace(' ','_'):r for r in (v.get('scouting') or {}).get('categories',[])}
    weeks={}
    for recap in v.get('recaps',[]):
        for w in recap.get('weeks',[]):
            if w.get('golfer_id') is not None and w.get('golfer_id')==g.get('id'):
                weeks[(recap['year'],w['week'])]=w
    recent=[w for _,w in sorted(weeks.items())[-4:]]
    competition=sum(w.get('activity')=='play' for w in recent)
    training=sum(w.get('activity')=='train' for w in recent)
    recovery=sum(w.get('activity')=='rest' for w in recent)
    recent_text=(f'Last {len(recent)} recorded weeks: {competition} competition, {training} training and {recovery} recovery.' if recent else 'No recent controlled-week history is recorded yet.')
    weakest=min(means,key=lambda k:(means[k],k));strongest=max(means,key=lambda k:(means[k],k))
    rows=[]
    for k in GROUPS:
        if k not in means:
            continue
        r=estimates.get(k,{})
        grade=r.get('grade');fg,bg=GRADE_COLORS.get(grade,('#5c6660','#f0f4ef'))
        potential=(f'<span class="training-estimate" style="color:{fg};background:{bg}">Estimated potential {esc(grade)}</span>' if grade in GRADE_COLORS else '<span class="muted">Potential not assessed</span>')
        facts=''
        if r.get('confidence'):
            facts+='<p>Confidence: '+esc(str(r['confidence']))+'</p>'
        if r.get('explanation'):
            facts+='<p>'+esc(str(r['explanation']))+'</p>'
        # Headroom is not inferred by subtracting a letter grade from a present rating.
        observed=[w for w in recent if w.get('activity')=='train' and w.get('training_category')==k and w.get('development_recorded') and 'overall' in w.get('development',{}).get('training',{})]
        if observed:
            gain=sum(w.get('development',{}).get('training',{}).get('overall',0) for w in observed)
            facts+=f'<p>Recorded training contribution: {gain:+.3f} overall across {len(observed)} recent practice week(s). Not a forecast.</p>'
        else:
            facts+='<p>No recent recorded practice outcome for this focus.</p>'
        rows.append(f'<article><h3>{LABELS[k]}</h3><div class="training-current">{means[k]:.1f}</div><small>Current training-group average</small><p>{potential}</p>'+facts+'</article>')
    return (STYLE+'<section class="career-panel"><div class="eyebrow">Make the practice choice informed</div><h2>What should I work on?</h2><p>'+esc(recent_text)+'</p><p>Current relative strength: <strong>'+LABELS[strongest]+'</strong>. Lowest current group: <strong>'+LABELS[weakest]+'</strong>. A weaker group is not automatically the best investment.</p><div class="training-compare">'+''.join(rows)+'</div><p class="muted">Potential grades describe a fallible future-level assessment, not exact remaining growth. Recent improvement is evidence, not a promised gain. We do not reveal hidden ceilings or manufacture a headroom estimate.</p><details><summary>Competition, practice or recovery?</summary><ul><li>Compete for recorded results, earnings and event-specific opportunities, with entry uncertainty, travel costs and fatigue.</li><li>Practice one focus and review its actual effect afterward. Giving up an event buys practice time, not guaranteed improvement.</li><li>Rest to reduce fatigue faster, especially above the 20% performance threshold. No direct skill training is performed.</li></ul></details></section>')
