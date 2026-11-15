"""Compact, factual career summary and upcoming-event watchlist."""
from urllib.parse import quote
from observer import esc

def summary(v):
    s = v.get('context', {}).get('summary')
    if not s:
        return ''
    stats = [('Starts', s['events']), ('Wins', s['wins']), ('Top 10', s['top10']),
             ('Prize money', '$' + format(s['prize_money'], ',.0f'))]
    return ('<div class="career-summary" aria-label="Current season results">' + ''.join(
        '<div><strong>' + esc(str(value)) + '</strong><small>' + esc(label) + '</small></div>' for label, value in stats)
        + '</div><small class="muted">This season, while under your control · ' + str(s['recorded_weeks']) + ' recorded weeks</small>')

def panels(v):
    c = v.get('context')
    if not c:
        return ''
    quals = ''.join('<li><strong>' + esc(q['label']) + '</strong><br>' + esc(q['reason']) +
                    ' <small>(' + str(q['year']) + ' season)</small></li>' for q in c['qualifications'])
    qual = ('<section class="career-panel"><h2>Current playing rights</h2><p>' + esc(v['golfer']['tour']) +
            '</p>' + ('<ul>' + quals + '</ul>' if quals else '<p class="muted">No additional card or winner exemption is recorded here. This does not mean you are ineligible for all events.</p>') +
            '<small>Event-specific invitations and qualifying places are decided by their own rules.</small></section>')
    rows = []
    for e in c['upcoming']:
        purse = ('$' + format(e['purse'], ',.0f') + ' total purse; not your payout') if e['purse'] else 'No cash purse listed'
        rows.append('<li><span class="status-pill">Week ' + str(e['week']) + '</span> <a href="/event/' + quote(e['event_id']) + '">' + esc(e['name']) + '</a><br><small>' + esc(e['tour']) + ' · ' + esc(purse) + '</small><p>' + esc(e['status']) + '</p></li>')
    calendar = ('<section id="career-calendar" class="career-panel"><h2>Upcoming opportunities</h2><p class="muted">Watchlist through week ' + str(c['through_week']) + '. An event appearing here is not a confirmed entry or invitation.</p><div class="career-calendar"><ul>' + ''.join(rows) + '</ul></div></section>')
    return calendar + qual
