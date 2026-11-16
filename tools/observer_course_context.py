"""Course-choice evidence from the committed snapshot; no simulation access."""
from html import escape

def cue(c):
    if not c:
        return ''
    if c.get('fit') is None:
        return ' · course assigned later'
    return f" · fit {c['fit']:+.2f} · {c['familiarity_rounds']:g} course rounds"

def panel(c):
    if not c:
        return ''
    if c.get('fit') is None:
        return '<div class="course-context"><strong>Course not assigned at entry</strong><p>'+escape(c.get('note',''))+'</p></div>'
    labels={'physical':'Physical','long_game':'Long game','short_game':'Short game','putting':'Putting','mental':'Mental'}
    rows=''.join('<tr><th scope="row">'+labels.get(f['category'],escape(f['category']))+'</th><td>'+f"{f['demand']:+.2f}"+'</td><td>'+f"{f['points']:+.2f}"+'</td></tr>' for f in c.get('factors',[]))
    return ('<div class="course-context"><strong>'+escape(c['course'])+' · '+escape(c.get('layout',''))+'</strong>'
        f'<p>Current-game fit <strong>{c["fit"]:+.2f}</strong> on −1 to +1. Recorded competitive rounds here: <strong>{c["familiarity_rounds"]:g}</strong>. Familiarity index: {c["familiarity"]:.2f} on 0 to 1.</p>'
        f'<p>Small event-appeal contribution: {c["points"]:+.2f} points. This influences choice, not tournament scoring or admission.</p>'
        '<details><summary>Why this course fits your game</summary><table><thead><tr><th>Skill group</th><th>Relative course demand</th><th>Fit contribution</th></tr></thead><tbody>'+rows+'</tbody></table>'
        '<p>Demand compares this course with the course library. Contributions use your current relative strengths, before the fit limit is applied. They are not predicted strokes.</p></details>'
        '<p class="muted">'+escape(c.get('note',''))+'</p></div>')
