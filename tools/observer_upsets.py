"""Biggest Upsets (roadmap B1/B2): the observer's list of winners ranked by their pre-event estimated chance, with a
majors-only view, and the estimate's panel on an edition's page.

The ranking is the recorded pre-event estimate only (golfsim/upsets.py: worked out in the simulation before any
shot, from facts known then, with its model version). The result's drama -- winning margin, playoff, strokes behind
before the final round -- is shown beside it and never enters the ranking. Editions played before estimates were
kept say "not recorded": nothing is reconstructed from ratings afterwards (B2). Status and age are the winner's at
the event, as recorded with the estimate. Reads only: nothing here changes the world.
"""
from __future__ import annotations

import json
from urllib.parse import quote, urlencode

from golfsim import scopes as SC
from golfsim import upsets as UP

PATH = '/upsets'
PAGE = 50
LEVELS = (('0', 'Major'), ('1', 'Premier'), ('2', 'Challenger'), ('3', 'Regional'), ('4', 'Mini tour'),
          ('5', 'College'), ('6', 'Amateur'), ('8', 'Club professional'))
STATUS = (('pro', 'professional'), ('amateur', 'amateur'), ('club_pro', 'club professional'))
COLUMNS = ('year', 'week', 'event_id', 'series', 'name', 'tour', 'tier', 'major', 'winner', 'model', 'p', 'status',
           'age', 'field', 'margin', 'playoff', 'back', 'rounds', 'match_play', 'detail')
B2_NOTE = ('Pre-event estimates are recorded from the Biggest Upsets update on, edition by edition, with the model '
           'version that made them. Editions played before then show “not recorded”: no estimate is worked out '
           'afterwards from later ratings, because that would let hindsight in. The earlier retrospective screen '
           '(228 majors and 2,052 Premier events, rated with start-of-season snapshots, 42 winners without prior '
           'ratings) was a rough screen, not calibrated win probabilities or a definitive upset ranking, and is not '
           'shown here as odds.')
MODEL_NOTE = ('How the estimate is made (' + UP.VERSION + '): before the first shot, each entrant\'s Overall at that '
              'moment gives an expected score and spread (the engine\'s measured rating ladder); every entrant\'s '
              'chance of the lowest total is worked out for that exact field and number of rounds, adding up to 100%. '
              'It leaves out form, course fit, familiarity, fatigue, weather and pressure, and it is an estimate from '
              'ratings, not calibrated betting odds. Match play is not estimated by this model. Equal chances share a '
              'rank (competition ranking: 1, 2, 2, 4), marked tied; tied rows are listed by date, then event. The world ranking is the one published before the event (amateurs also show '
              'their amateur ranking).')


def _o():
    import observer
    return observer


def _o_attr(name):
    return getattr(_o(), name)


def rows_for(w):
    """Every Upsets row: the statistics store's archived seasons, then the current season's editions (not yet
    archived), as dicts. (None, progress) while the store is being built."""
    import observer_stats as ST
    db, building = w.statistics()
    if db is None and getattr(w, 'a', None):
        return None, building
    rows = []
    if db is not None:
        rows = [dict(zip(COLUMNS, r)) for r in db.execute(f'SELECT {", ".join(COLUMNS)} FROM upsets')]
    live = getattr(w, 'live', None)
    if live is not None:
        archived = set(w.a.years) if getattr(w, 'a', None) else set()
        y = live.cursor['year']
        if y not in archived:
            rows += [dict(zip(COLUMNS, r)) for r in ST.upset_rows(list(live.editions.values()), y)]
    for r in rows:
        r['detail'] = json.loads(r['detail']) if r['detail'] else {}
    return rows, None


def rank_key(r):
    """The stable row order: the lowest recorded chance first, then date, then event id."""
    return (r['p'], r['year'], r['week'], r['event_id'])


def competition_ranks(ranked):
    """Standard competition ranks of rows already in rank_key order ("1, 2, 2, 4"): a row's rank is 1 + the number
    of rows with a strictly lower chance, so equal chances share a rank. Returns [(rank, tied)]."""
    out, n = [], len(ranked)
    for i, r in enumerate(ranked):
        if i and ranked[i - 1]['p'] == r['p']:
            rank = out[-1][0]
        else:
            rank = i + 1
        tied = (i and ranked[i - 1]['p'] == r['p']) or (i + 1 < n and ranked[i + 1]['p'] == r['p'])
        out.append((rank, bool(tied)))
    return out


def select(w, rows, q):
    """The rows chosen by the page's filters (any order)."""
    one = _o().one
    scope = one(q, 'scope', '') or ''
    lo, hi = _int(one(q, 'from')), _int(one(q, 'to'))
    level, nation, status = one(q, 'level', '') or '', one(q, 'nation', '') or '', one(q, 'status', '') or ''
    series, text = one(q, 'series', '') or '', (one(q, 'event', '') or '').strip().lower()
    min_field = _int(one(q, 'field')) or 0
    within = set(SC.tours_for(scope)) if scope and scope != 'major' else set()
    out = []
    for r in rows:
        if scope == 'major' and not r['major']:
            continue
        if within and r['tour'] not in within:
            continue
        if lo and r['year'] < lo or hi and r['year'] > hi:
            continue
        if level and str(r['tier']) != level:
            continue
        if series and r['series'] != series:
            continue
        if text and text not in (r['name'] or w.series_name(r['series']) or '').lower():
            continue
        if min_field and (r['field'] or 0) < min_field:
            continue
        if status and r['status'] != status:                  # status at the event (recorded with the estimate)
            continue
        if nation and ((w.person(r['winner']) or {}).get('country') or '') != nation:
            continue
        out.append(r)
    return out


def _int(x):
    try:
        return int(x) if x not in (None, '') else None
    except ValueError:
        return None


def ordinal(n):
    if n is None:
        return '—'
    suffix = 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f'{n}{suffix}'


def ranking_text(f):
    """The pre-event ranking: world ranking (amateur ranking too for an amateur)."""
    wr, ar = f.get('wr'), f.get('ar')
    out = f'world No. {wr}' if wr else 'unranked (world)'
    if f.get('status') == 'amateur' and ar:
        out += f' · amateur No. {ar}'
    return out


def first_wins(rows):
    """{event_id: True} for each row that is its winner's first win among the recorded editions (every won,
    single-site, non-qualifying edition: the order is by date)."""
    seen, out = set(), {}
    for r in sorted(rows, key=lambda r: (r['year'], r['week'], r['event_id'])):
        out[r['event_id']] = r['winner'] not in seen
        seen.add(r['winner'])
    return out


def tags(w, r, first):
    """Story tags, only from recorded facts."""
    out = []
    if first.get(r['event_id']):
        initial = bool(((w.a.people.get(r['winner']) or {}) if getattr(w, 'a', None) else {}).get('initial'))
        out.append('first win in the recorded history' if initial else 'first win')
    if r['playoff']:
        out.append(f'playoff ({r["playoff"]} extra holes)')
    if r['back']:
        out.append(f'came from {r["back"]} back')
    elif r['back'] == 0 and r['rounds'] and r['rounds'] >= 2:
        out.append(f'led or shared the lead after {r["rounds"] - 1} rounds')
    if r['status'] == 'amateur':
        out.append('amateur winner')
    f = r['detail'].get('winner_facts') or {}
    if r['status'] in ('pro', 'club_pro') and not f.get('wr') and r['tier'] is not None and r['tier'] <= 4:
        out.append('unranked')
    return out


def drama(r):
    """The result's margin and playoff, kept apart from the estimate."""
    if r['match_play']:
        return 'match play'
    if r['playoff']:
        return f'tied, won a {r["playoff"]}-hole playoff'
    if r['margin'] is None:
        return '—'
    return f'by {r["margin"]} stroke{"s" if r["margin"] != 1 else ""}'


def explanation(w, r):
    """Why this is classified as an upset, in one line, from the recorded estimate."""
    d = r['detail']
    if r['p'] is None:
        return '<span class="muted">' + ('not estimated: ' + _o().esc(d.get('why')) if d.get('why') else
                                         'not recorded (played before estimates were kept)') + '</span>'
    O = _o()
    fav = d.get('favourite')
    favtxt = ('they were the favourite' if fav == r['winner'] else
              f'favourite {w.person_link(fav)} (Overall {O.esc(d.get("favourite_overall"))}, '
              f'{UP.odds_text(d.get("favourite_p"))})')
    return (f'Overall {O.esc(d.get("overall"))} at the event, {ordinal(d.get("overall_rank"))} of {r["field"]} by '
            f'Overall; the model put them {ordinal(d.get("rank"))} of {r["field"]} at {UP.odds_text(r["p"])}; {favtxt}.')


def page(w, q):
    O = _o()
    title = 'Biggest Upsets'
    if not getattr(w, 'a', None) and getattr(w, 'live', None) is None:
        return title, O.no_history()
    rows, building = rows_for(w)
    if rows is None:
        return title, '<p>Working out the statistics from the history…</p><meta http-equiv="refresh" content="3">'
    scope = O.one(q, 'scope', '') or ''
    chosen = select(w, rows, q)
    ranked = sorted((r for r in chosen if r['p'] is not None), key=rank_key)
    unrecorded = [r for r in chosen if r['p'] is None and not r['model']]
    not_estimated = [r for r in chosen if r['p'] is None and r['model']]
    first = first_wins(rows)
    tours = sorted(((k, t.get('name', k)) for k, t in w.tours().items()), key=lambda x: x[1])
    nations = sorted({(w.person(r['winner']) or {}).get('country') or '' for r in rows} - {''})
    years = sorted({r['year'] for r in rows})
    keep = {k: v[0] for k, v in q.items() if k not in ('scope', 'page') and v and v[0]}
    def button(value, label):
        on = scope == value
        href = f'{PATH}?{urlencode({**keep, **({"scope": value} if value else {})})}'
        return f'<a href="{href}" class="{"on" if on else ""}" aria-pressed="{"true" if on else "false"}">{O.esc(label)}</a>'
    views = ('<div class="tabs scope" title="Which events count">' + button('major', 'Majors only')
             + button(SC.MAJORS_PREMIER, SC.LABEL) + button('', 'All events') + '</div>')
    f = O.filters(PATH, q, [
        ('scope', 'Events', [('', 'all'), ('major', 'majors only'), (SC.MAJORS_PREMIER, SC.LABEL)]
         + [(k, f'tour: {t}') for k, t in tours]),
        ('from', 'From season', [('', 'first')] + [(str(y), str(y)) for y in years]),
        ('to', 'To season', [('', 'latest')] + [(str(y), str(y)) for y in years]),
        ('level', 'Level', [('', 'any')] + list(LEVELS)),
        ('event', 'Event name contains', None),
        ('nation', 'Winner\'s nation', [('', 'any')] + [(n, n) for n in nations]),
        ('status', 'Status at the event', [('', 'any')] + list(STATUS)),
        ('field', 'Field at least', [('', 'any'), ('20', '20'), ('60', '60'), ('100', '100')])])
    series = O.one(q, 'series', '') or ''
    if series:
        f += (f'<p>Tournament: <a href="/series/{quote(series)}">{O.esc(w.series_name(series))}</a> · '
              f'<a href="{PATH}?{urlencode({k: v for k, v in keep.items() if k != "series"})}">all tournaments</a></p>')
    rec_years = sorted({r['year'] for r in chosen if r['model']})
    cov = (f'{len(ranked):,} winners with a recorded estimate'
           + (f' (seasons {rec_years[0]}–{rec_years[-1]})' if rec_years else '')
           + f'; {len(unrecorded):,} not recorded (played before estimates were kept)'
           + (f'; {len(not_estimated):,} not estimated (match play)' if not_estimated else '') + '.')
    chunk, pager = O.paged(ranked, q, PATH, size=PAGE)
    start = (max(1, min(_int(O.one(q, 'page')) or 1, (len(ranked) + PAGE - 1) // PAGE or 1)) - 1) * PAGE
    ranks = competition_ranks(ranked)                     # over the whole list, not only this page
    body = []
    for i, r in enumerate(chunk, start):
        rank, tied = ranks[i]
        f_ = r['detail'].get('winner_facts') or {}
        status = dict(STATUS).get(r['status'], r['status'] or '—')
        body.append([
            f'{rank}' + (' <span class="tag" title="the same pre-event chance as the row beside it">tied</span>'
                         if tied else ''), w.person_link(r['winner']) + ' · ' + O.results_link(r['winner'], 'results', year=r['year']),
            f'{O.esc(r["age"]) if r["age"] is not None else "—"}* · {O.esc(status)}',
            O.event_link(w, r['event_id']) + f' <span class="muted">{r["year"]} wk {r["week"]}</span>',
            O.esc(dict(LEVELS).get(str(r['tier']), r['tier'])), O.esc(ranking_text(f_)),
            f'<strong>{UP.odds_text(r["p"])}</strong>', str(r['field']),
            O.esc(', '.join(tags(w, r, first))) or '<span class="muted">—</span>', O.esc(drama(r)),
            explanation(w, r)])
    table = (O.table(['#', 'Winner', 'Age* · status then', 'Event', 'Level', 'Pre-event ranking',
                      'Pre-event chance', 'Field', 'Story', 'Result (not ranked)', 'Why it is an upset'], body,
                     numeric=(0, 7)) + pager) if body else '<p class="muted">No winner with a recorded estimate matches.</p>'
    return title, (views + f + f'<p class="muted">{O.esc(cov)}</p>' + table
                   + f'<p class="muted">Ranked by the pre-event chance only (lowest first). Result: the winning margin '
                     f'or playoff, shown apart and never part of the ranking. {MODEL_NOTE} *{O.AGE_NOTE} Status: as '
                     f'recorded at the event. Story tags come from the recorded results: first win (among recorded '
                     f'editions, qualifying stages aside), playoff, strokes behind before the final round, amateur '
                     f'winner, unranked professional.</p><p class="muted">{B2_NOTE}</p>')


def event_panel(w, full):
    """The edition's pre-event estimate, for its page (or that it was not recorded)."""
    O = _o()
    if not full or 'id' not in full or full.get('kind') == 'qualifying' or len(full.get('finish') or ()) != 1:
        return ''
    up = full.get('upset')
    if not up:
        return ('<p class="muted">Pre-event estimate: not recorded (this edition was played before estimates were '
                'kept; none is worked out afterwards).</p>')
    if not up.get('estimated'):
        return f'<p class="muted">Pre-event estimate: not estimated ({O.esc(up.get("why"))}).</p>'
    top = ', '.join(f'{w.person_link(g)} {UP.odds_text(p)}' for g, p in up.get('top') or [])
    line = ''
    if up.get('winner') is not None:
        r = {'winner': up['winner'], 'p': up['p'], 'field': up['field'], 'detail': up}
        line = f'Winner: {w.person_link(up["winner"])}, {UP.odds_text(up["p"])} before the event. ' + explanation(w, r)
    return (f'<h3>Pre-event estimate</h3><p>{line}</p><p class="muted">Top {len(up.get("top") or [])} by the model: '
            f'{top}. Model {O.esc(up.get("model"))}, worked out from the field before the first shot; see '
            f'<a href="{PATH}">Biggest Upsets</a>.</p>')
