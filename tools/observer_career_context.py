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
        rows.append('<li><span class="status-pill">Week ' + str(e['week']) + '</span> <a href="/event/' + quote(e['event_id']) + '">' + esc(e['name']) + '</a><br><small>' + esc(e['tour']) + ' · ' + esc(purse) + '</small><p>' + esc(e['status']) + '</p>' + target_note(e) + '</li>')
    calendar = ('<section id="career-calendar" class="career-panel"><h2>Upcoming opportunities</h2><p class="muted">Watchlist through week ' + str(c['through_week']) + '. An event appearing here is not a confirmed entry or invitation.</p><div class="career-calendar"><ul>' + ''.join(rows) + '</ul></div></section>')
    return calendar + qual


def target_note(e):
    t = e.get('target')
    if not t:
        return ''
    year = str(e['event_id']).split(':', 1)[0]
    return ('<p class="muted">Qualifying route to <a href="/event/' + quote(year + ':' + t['id']) + '">' +
            esc(t['label']) + '</a> (week ' + str(t['week']) + '). A qualifying result is not a confirmed target-event entry.</p>')


def entry_note(e):
    if not e or not (e.get('text') or e.get('declined') or e.get('clashed')):
        return ''
    out = '<div class="entry-evidence"><strong>Entry decision</strong>'
    if e.get('event_label'):
        out += '<p>' + esc(e['event_label']) + '</p>'
    if e.get('text'):
        out += '<p>' + esc(e['text']) + '</p>'
    if e.get('recorded') and e.get('position') is not None:
        out += '<p>Entry-order position: ' + str(e['position'])
        if e.get('applicants') is not None:
            out += ' of ' + str(e['applicants']) + ' applicants'
        if e.get('admitted') is not None:
            out += ' · ' + str(e['admitted']) + ' admitted'
        if e.get('capacity') is not None:
            out += ' · field capacity ' + str(e['capacity'])
        out += '. These are recorded entry facts, not a forecast.</p>'
    if e.get('declined'):
        out += '<p>Your saved invitation or qualifying policy declined an opportunity this week.</p>'
    if e.get('clashed'):
        out += '<p>A selection-only event was lost to a schedule clash.</p>'
    if not e.get('recorded'):
        out += '<small>Historical access log only. Entry-order position and cutoff were not recorded.</small>'
    return out + '</div>'
