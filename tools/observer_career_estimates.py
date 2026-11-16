"""Presentation of recorded, uncertain scouting and entry assessments."""
from html import escape as esc

ROOM={'little':'Little estimated room','some':'Some estimated room','considerable':'Considerable estimated room','unknown':'Growth room not assessed'}
BASIS={'age_curve':'Typical age curve','observed_trend':'Recorded development trend','coach_read':'Coach assessment','self_read':'Self-assessment'}

def growth(row):
    room=row.get('growth_room')
    if not room:
        return '<p class="muted">Growth room not assessed in this record.</p>'
    label=ROOM.get(room.get('label'),ROOM['unknown'])
    h='<div class="growth-estimate"><strong>'+label+'</strong>'
    if room.get('uncertainty'):
        h+='<p>Uncertainty: '+esc(room['uncertainty'])+'.</p>'
    h+='<p>'+esc(room.get('explanation',''))+'</p>'
    evidence=row.get('evidence') or {}
    if 'observations' in evidence:
        h+='<p>'+str(evidence['observations'])+' recorded observations across '+str(evidence.get('span_weeks',0))+' weeks.'
        h+=(' A development trend is available.' if evidence.get('trend_available') else ' No dependable development trend is available.')+'</p>'
    basis=[BASIS.get(k,k.replace('_',' ')) for k in room.get('basis',[])]
    if basis:
        h+='<p class="muted">Based on: '+esc(', '.join(basis))+'.</p>'
    return h+'<p class="muted">An uncertain assessment, not a known limit or promised improvement.</p></div>'

def entry(row):
    if not row:
        return '<p class="muted">Entry assessment unavailable. Eligibility is not a confirmed place.</p>'
    h='<div class="entry-outlook"><strong>'+esc(row.get('label','Entry assessment unavailable'))+'</strong>'
    if row.get('your_class_label'):
        h+='<p>Your entry category: '+esc(row['your_class_label'])+'.</p>'
    h+='<p>'+esc(row.get('reason',''))+'</p>'
    if row.get('uncertainty'):
        h+='<p class="muted">'+esc(row['uncertainty'])+'</p>'
    return h+'<p class="muted">No numerical admission probability is implied. Historical comparisons do not guarantee this year’s field.</p></div>'
