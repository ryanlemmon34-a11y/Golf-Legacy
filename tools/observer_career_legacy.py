"""Presentation-only trophies and fallible scouting estimates supplied by committed read models.
No awards, potential grades or simulation decisions are inferred here.
"""
import hashlib
import textwrap
from urllib.parse import quote
from observer import esc

GRADE_COLORS = {'A':('#175d91','#edf5ff'), 'B':('#17643d','#edf7ef'),
                'C':('#725000','#fff4b2'), 'D':('#8a3d00','#fff0dc'), 'F':('#a22c36','#fff0f1')}
STYLE = '''<style>
.trophy-grid,.scouting-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px}
.trophy-card{border:1px solid var(--career-frame,var(--line));border-top:3px solid var(--career-gold,var(--accent));border-radius:10px;background:var(--panel);box-shadow:var(--career-shadow);overflow:hidden}
.trophy-art{display:block;width:100%;height:240px;background:radial-gradient(ellipse at 50% 80%,#c3a65c26,transparent 65%)}
.trophy-caption{padding:14px 18px;border-top:1px solid var(--line)}.trophy-caption h3{font-size:14px}.trophy-caption p{font-size:12px;margin:5px 0}
.scouting-card{border:1px solid var(--career-frame,var(--line));border-radius:9px;padding:16px;background:var(--panel);display:grid;grid-template-columns:50px 1fr;gap:12px}
.scouting-card h3{font-size:14px;margin:0 0 8px}.scouting-card p{font-size:12px;margin:6px 0}.potential-grade{display:grid;place-items:center;width:46px;height:50px;border:1px solid currentColor;border-radius:8px;font-size:25px;font-weight:800}
@media(max-width:650px){.trophy-grid,.scouting-grid{grid-template-columns:1fr}}
</style>'''


def trophy_art(award, index=0):
    """Original vector trophy with actual winner/year text physically on its plinth."""
    winner = str(award['winner_name'])
    year = str(award['year'])
    ident = hashlib.sha256((str(award['event_id'])+year+str(index)).encode()).hexdigest()[:12]
    kind = award.get('kind')
    colors = ('#9b7026','#fff0b4','#b48a36') if kind == 'major' else ('#627e86','#e7f4f3','#8ea9ad') if kind == 'college' else ('#315c7b','#c3e8ff','#639db6')
    # Preserve the entire winner name on the plaque. Wrap rather than ellipsize it.
    lines = textwrap.wrap(winner, width=24, break_long_words=True) or ['Winner not recorded']
    size = min(10, 22/max(1,len(lines)))
    engraving = ''.join(f'<text x="130" y="{176 - (len(lines)-1)*size/2 + j*size:.2f}" text-anchor="middle" fill="#302714" font-size="{size:.2f}" font-weight="700">{esc(line)}</text>' for j,line in enumerate(lines))
    cup = ('<path d="M92 38h76l-8 57c-4 23-56 23-60 0z"/><path d="M93 48H72v15c0 24 19 30 30 30M167 48h21v15c0 24-19 30-30 30" fill="none" stroke-width="7"/><path d="M123 111h14v25h20v8h-54v-8h20z"/>' if kind == 'major' else
           '<path d="M79 64h102c-2 34-20 48-46 50v20h24v10h-58v-10h24v-20C99 112 81 98 79 64z"/><path d="M88 55h84v9H88z"/>' if kind == 'college' else
           '<path d="M130 30l34 65-34 43-34-43z"/><path d="M130 30v108M96 95h68" fill="none" stroke="#ffffff88" stroke-width="2"/><path d="M102 136h56v8h-56z"/>')
    return (f'<svg class="trophy-art" viewBox="0 0 260 230" role="img" aria-labelledby="trophy-{ident}"><title id="trophy-{ident}">{esc(award["event_name"])} trophy, {esc(winner)}, {esc(year)}</title>'
            f'<defs><linearGradient id="metal-{ident}"><stop stop-color="{colors[0]}"/><stop offset=".45" stop-color="{colors[1]}"/><stop offset="1" stop-color="{colors[2]}"/></linearGradient></defs>'
            '<ellipse cx="130" cy="212" rx="72" ry="8" fill="#00000018"/>'
            f'<g fill="url(#metal-{ident})" stroke="{colors[0]}" stroke-width="2">{cup}</g>'
            '<path d="M67 145h126l9 65H58z" fill="#213d2d" stroke="#52715c" stroke-width="2"/>'
            '<rect x="73" y="155" width="114" height="47" rx="3" fill="#eddb9d" stroke="#a98b47"/>'
            + engraving + f'<text x="130" y="195" text-anchor="middle" fill="#302714" font-size="12" font-weight="800">{esc(year)}</text></svg>')


def trophy_case(trophies):
    if trophies is None:
        return '<section class="career-panel"><h2>Trophy case</h2><p>Verified trophy records are not available in this snapshot.</p></section>'
    cards=[]
    for i,a in enumerate(trophies):
        cards.append('<article class="trophy-card">'+trophy_art(a,i)+'<div class="trophy-caption"><h3><a href="/event/'+quote(str(a['event_id']))+'">'+esc(a['event_name'])+'</a></h3><p>'+esc(str(a['year']))+' · '+esc(a['winner_name'])+'</p><small>Recorded championship win</small></div></article>')
    return '<section id="career-trophies" class="career-panel"><h2>Your trophy case</h2><p class="muted">Earned championships, with each winning year preserved.</p>'+('<div class="trophy-grid">'+''.join(cards)+'</div>' if cards else '<div class="career-empty">No qualifying championship trophies recorded yet.</div>')+'</section>'


def scouting_panel(estimates, assessment=None):
    cards=[]
    for row in estimates or []:
        grade=row.get('grade')
        fg,bg=GRADE_COLORS.get(grade,('#5c6660','#f0f4ef'))
        letter=grade if grade in GRADE_COLORS else '?'
        detail=''
        if row.get('confidence'):
            detail+='<p>Confidence: '+esc(str(row['confidence']))+'</p>'
        if row.get('explanation'):
            detail+='<p>'+esc(str(row['explanation']))+'</p>'
        history=row.get('history') or []
        if history:
            detail+='<details><summary>Assessment history</summary><ul>'+''.join('<li>'+esc(str(h['year']))+' · week '+esc(str(h['week']))+': '+esc(h['grade'] if h.get('grade') in GRADE_COLORS else 'Not assessed')+'</li>' for h in history)+'</ul></details>'
        cards.append('<article class="scouting-card"><div class="potential-grade" style="color:'+fg+';background:'+bg+'" aria-label="Estimated potential '+esc(letter)+'">'+esc(letter)+'</div><div><h3>'+esc(row['category'])+'</h3><small>'+('Estimated potential' if letter!='?' else 'Not yet assessed')+'</small>'+detail+'</div></article>')
    metadata=''
    if assessment:
        source={'coach':'Coach assessment','self':'Self-assessment'}.get(assessment.get('source'),'Recorded assessment')
        judge=assessment.get('judge')
        if isinstance(judge,dict):
            judge=judge.get('name')
        when=assessment.get('as_of')
        if isinstance(when,(list,tuple)) and len(when)==2:
            when='week '+str(when[1])+' of '+str(when[0])
        elif isinstance(when,dict):
            when=('week '+str(when['week'])+' of '+str(when['year'])) if 'week' in when and 'year' in when else None
        metadata='<p>'+esc(source)+((' · '+esc(str(judge))) if judge else '')+((' · As of '+esc(str(when))) if when else '')+'</p>'
    return '<section id="career-scouting" class="career-panel"><h2>Scouted potential</h2>'+metadata+'<p class="muted">An assessment, not a promise. Grades can move up or down as more is learned. A revised estimate does not mean underlying potential changed. Actual ceilings remain hidden.</p>'+('<div class="scouting-grid">'+''.join(cards)+'</div>' if cards else '<p>No category assessments are recorded yet.</p>')+'</section>'


def panels(view):
    out=''
    if 'trophies' in view:
        out+=trophy_case(view['trophies'])
    if 'scouting' in view:
        assessment=view['scouting']
        out+=scouting_panel(assessment.get('categories',[]) if assessment else [],assessment)
    elif 'potential_estimates' in view:
        out+=scouting_panel(view['potential_estimates'])
    return STYLE+out if out else ''
