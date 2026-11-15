"""Read-only career context. Published facts, never predicted invitations or hidden ratings."""
def context(season, g, year, week):
    from .career import season_review, week_options
    summary = season_review(season, season.career, g.id, year)
    qualifications = []
    for key, label in [('card_reasons', 'Tour card'), ('earned', 'Winner exemption')]:
        reason = getattr(season, key, {}).get(year, {}).get(g.id)
        if reason:
            qualifications.append({'label': label, 'reason': str(reason), 'year': year})
    rights = getattr(season, 'rights', {}).get(year, {}).get(g.id)
    if rights:
        qualifications.append({'label': 'Premier playing rights: ' + rights[0], 'reason': rights[1], 'year': year})
    upcoming = []
    editions = {e.event_id: e for e in season.cal.editions(year)}
    for w in range(week, min(52, week + 11) + 1):
        options = week_options(season, g, year, w)
        for row in options['events'] + options['selected']:
            ed = editions[row['event_id']]
            # Calendar is a watchlist, not a claim the player has earned a place.
            if not (ed.series.tour == g.tour or row.get('eligible') or ed.series.tier == 1):
                continue
            row = dict(row, week=w, purse=ed.series.purse)
            row['status'] = (row.get('why') or 'Eligible to request entry; place not guaranteed') if 'eligible' in row else row['rule']
            upcoming.append(row)
    return {'summary': summary, 'qualifications': qualifications, 'upcoming': upcoming,
            'through_week': min(52, week + 11)}
