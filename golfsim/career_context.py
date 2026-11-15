"""Read-only career context. Published facts, never predicted invitations or hidden ratings."""
def relevant_selected(season, g, series, year):
    """Broad watchlist scope, not eligibility or a prediction of an eventual place."""
    from .season import ELITE_AMATEUR_REGIONS, region_of
    from .geography import COUNTRIES
    if series.tour == g.tour or series.tier == 1:
        return True
    if g.status != 'amateur':
        return False
    if series.series_id in ('USA_AMATEUR', 'USA_AMATEUR_QUALIFYING'):
        return True
    if series.category == 'elite_amateur':
        if series.eligibility == 'mid_amateur':
            return g.age(year) >= 25
        regions = ELITE_AMATEUR_REGIONS.get(series.series_id)
        return not regions or region_of(g) in regions
    if series.category == 'national_amateur':
        return g.country == series.host_country or region_of(g) == COUNTRIES[series.host_country].region
    if series.category == 'circuit_championship' and series.tier == 6:
        return season.series_amateur(g, series.tour)
    return False


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
            if not (ed.series.tour == g.tour or row.get('eligible') or ed.series.tier == 1
                    or ('rule' in row and relevant_selected(season, g, ed.series, year))):
                continue
            row = dict(row, week=w, purse=ed.series.purse)
            row['status'] = (row.get('why') or 'Eligible to request entry; place not guaranteed') if 'eligible' in row else row['rule']
            if options['injured_until']:
                row['status'] = 'Unavailable during the recorded injury window'
            upcoming.append(row)
    return {'summary': summary, 'qualifications': qualifications, 'upcoming': upcoming,
            'through_week': min(52, week + 11)}
