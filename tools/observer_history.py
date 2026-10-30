"""History views for the observer, as HTML fragments (observer.py frames them into pages): entry routes in
words with links to the rules, the rules page, a golfer's status and how it changed, a season as it was (the
as-of view), coach and caddie histories, where a person has lived, tournament and course summaries, round
by round results and their replay, record rows with dates and who is still pursuing them, the year-end
recap and the Career Grand Slam.

Everything is drawn from recorded facts. Where a fact was not recorded (seasons played before an engine
kept it), the page says so: nothing is reconstructed from today's values, and nothing is guessed.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from urllib.parse import quote, urlencode

from golfsim import rules as R

MAJOR_SERIES = ('TOUR_MASTERS', 'PREMIER_TOUR_CHAMPIONSHIP', 'USA_OPEN', 'BRITANNIA_OPEN')
LEVELS = {0: 'Majors', 1: 'Premier Tour', 2: 'Challenger tour', 3: 'Regional tour', 4: 'Mini tour', 5: 'College golf',
          6: 'Amateur golf', 7: 'Qualifying', 8: 'Club professional golf'}
STATUS = {'pro': 'professional', 'amateur': 'amateur', 'club_pro': 'club professional'}
LIFESTYLE = {'full_time': 'full time (chasing tour golf)', 'part_time': 'part time (a job comes first)',
             'retired': 'retired from competition'}
NOT_RECORDED = '<span class="muted">not recorded</span>'
DECISION_NOTE = ('Career decisions are modelled choices: the simulation records the inputs it weighed (the chance of the '
                 'decision that winter, how many seasons their money would last, recent progress, their desire to '
                 'continue, places already secured, the season\'s money), not a personal story. Nothing else is implied.')


def _o():
    import observer
    return observer


def _years_text(ys):
    """'2027–2030, 2033' from a list of years."""
    ys = sorted(set(ys))
    out, i = [], 0
    while i < len(ys):
        j = i
        while j + 1 < len(ys) and ys[j + 1] == ys[j] + 1:
            j += 1
        out.append(str(ys[i]) if i == j else f'{ys[i]}–{ys[j]}')
        i = j + 1
    return ', '.join(out) or 'none'


# ---- entry routes and the rules ------------------------------------------------------------------------------
def route_html(route, version=None):
    """How a golfer got into a field: the rule in words (as worded in the world's calendar version), a link to
    it, and the recorded code."""
    O = _o()
    if not route:
        return '<span class="muted">—</span>'
    rule, text = R.explain(route, version)
    code = f'<span class="tag" title="the code recorded with the start">{O.esc(route)}</span>'
    if text is None:
        return code
    return f'{O.esc(text)} <a href="/rules#{rule}" title="the rule this entry used">rule</a> {code}'


def rights_section(w, year, major):
    """A major edition's rights ledger: every place its rules gave -- with the categories behind it, the
    evidence and when it was earned -- and how each ended (entered, withdrawn, declined, expired); one place
    per golfer however many categories support it. Editions played before the ledger say so."""
    O = _o()
    book = w.major_rights(year, major)
    if not book:
        return ('<h2>Qualification ledger</h2><p class="muted">Not recorded for this edition (played before the '
                'rights ledger was kept): “How they got in” above gives each entrant\'s route.</p>')
    order = {'entered': 0}
    rows = sorted(book.items(), key=lambda kv: (order.get((kv[1].get('result') or '').split(':')[0], 1),
                                                kv[1].get('result') or '', kv[0]))
    from collections import Counter as _C
    tally = _C((r.get('result') or 'pending').split(':')[0] for _, r in rows)
    v = w.calendar_version
    body = []
    for gid, r in rows:
        cats = '; '.join(O.esc(R.explain(c, v)[1] or c) + f' <span class="tag">{O.esc(c)}</span>' for c in r['routes'])
        when = r.get('awarded')
        body.append([w.person_link(gid), O.esc(r.get('state') or ''), cats,
                     O.esc('; '.join(r.get('sources') or []) or '—'),
                     O.esc(f'{when[0]} week {when[1]}' if when else '—'), O.esc(r.get('result') or 'pending'),
                     _place_money(O, r)])
    return ('<h2>Qualification ledger</h2><p>' + ' · '.join(f'{n} {O.esc(k)}' for k, n in tally.most_common())
            + '</p>' + O.table(['Golfer', 'Place', 'Categories', 'Evidence', 'Earned', 'Outcome',
                                'Money when the field was set'], body)
            + '<p class="muted">Every place this edition\'s rules gave: earned, or conditional (an amateur\'s place, '
              'which lapses on turning professional). Outcome: entered; withdrawn (injured or retired); declined (could '
              'not pay the trip); expired. Alternates and invitations that took places given up are listed as entered. '
              'Evidence is the edition and result, ranking or award the category read, as recorded. Money: what the '
              'golfer could draw on (savings, backers, credit), what was set aside first (four weeks of living and '
              'coaching costs, and entries already accepted that week), what remained to spend, the trip\'s cost '
              '(travel and entry, and the caddie\'s week) and who paid it; "not recorded" for places decided '
              'before this was kept.</p>')


def _place_money(O, r):
    m = r.get('money')
    if not m:
        return NOT_RECORDED
    payer = {'golfer': 'the golfer', 'organizer': 'the organizer (travel and entry)', 'school': 'their school',
             'club': 'their club'}.get(m.get('paid_by'), m.get('paid_by') or '—')
    return (f'could draw {O.money(m["funds"])} · set aside {O.money(m["set_aside"])} · '
            f'to spend {O.money(m["spendable"])} · trip {O.money(m["trip"])} · paid by {O.esc(payer)}')


def rules_versions(w):
    """{season: rules version} for the archived seasons that recorded one."""
    if w.a and w.a.index is not None and hasattr(w.a.index, 'rules_versions'):
        try:
            return w.a.index.rules_versions()
        except Exception:                                  # an index from before versions: none recorded
            return {}
    return {}


def rules_note(w, year):
    """Which rules a season was played under, for an edition or season page."""
    O = _o()
    if w.live is not None and year == w.live.cursor['year']:
        v = getattr(w.live, 'rules_version', None)
    else:
        v = rules_versions(w).get(year)
    if v:
        return f'Played under rules version <a href="/rules">{O.esc(v)}</a>.'
    return ('Played before rules versions were recorded: see <a href="/rules">the rules</a> for what has changed '
            'since.')


def rules_page(w, q):
    O = _o()
    out = ['<p>How golfers get into fields, keep and earn tour cards, and which amateur and college golf they may '
           'play, in words. Every “How they got in” on a result links here. The simulation\'s code applies the '
           'rules; this page describes them.</p>']
    versions = rules_versions(w)
    by = defaultdict(list)
    for y in (w.a.years if w.a else []):
        by[versions.get(y)].append(y)
    live_v = getattr(w.live, 'rules_version', None) if w.live else None
    rows = []
    for v, summary in R.VERSIONS:
        seasons = _years_text(by.get(v, [])) if by.get(v) else ''
        if live_v == v:
            seasons = (seasons + ' and ' if seasons else '') + 'the current season'
        rows.append([O.esc(v), O.esc(summary), O.esc(seasons or 'none yet')])
    if by.get(None):
        rows.append(['earlier', O.esc(R.EARLIER), O.esc(_years_text(by[None]))])
    out.append('<h2>Versions</h2>' + O.table(['Version', 'What changed', 'Seasons of this world'], rows))
    import golfsim.schedule as SCH
    from golfsim.qualification import rules_for
    v = getattr(w, 'calendar_version', 'v1')
    sp = SCH.spec(v)
    out.append(f'<h2>This world\'s calendar</h2><p><strong>{O.esc(sp.label)}</strong> (version {O.esc(v)}). '
               f'{O.esc(sp.rules_note)} <a href="#calendar">The calendar rule</a>.</p>')
    for major, routes in rules_for(v).items():
        out.append(f'<details><summary>{O.esc(w.series_name(major))}: {len(routes)} categories (week '
                   f'{sp.majors[major]})</summary>' + O.table(['Code', 'Category', 'Real-life analogue', 'Kind'], [
                       [O.esc(r.code), O.esc(r.label), O.esc(r.analogue), O.esc(r.kind + (', amateurs only' if r.amateur_only
                                                                                      else ''))] for r in routes])
                   + '</details>')
    out.append('<h2>The rules</h2>')
    for rid, (title, text, since) in R.RULES.items():
        out.append(f'<div class="card" id="{rid}"><h3>{O.esc(title)}</h3><p>{O.esc(text)}</p><p class="muted">'
                   + (f'Introduced or changed in version {O.esc(since)}.' if since else
                      'Unchanged since before rules versions were recorded.') + '</p></div>')
    return 'Rules', ''.join(out)


# ---- status, and how it changed --------------------------------------------------------------------------------
def decision_text(t):
    """A recorded career decision in words, with the inputs the simulation recorded (never more)."""
    O = _o()
    kind = t.get('kind', '')
    parts = []
    if t.get('p') is not None:
        parts.append(f'chance that winter {100 * t["p"]:.1f}%')
    if t.get('runway') is not None:
        parts.append(f'money would last {t["runway"]:.1f} seasons')
    if t.get('progress') is not None:
        parts.append(f'progress {t["progress"]:+.1f}')
    if t.get('desire') is not None:
        parts.append(f'desire to continue {t["desire"]:+.1f}')
    if t.get('secured'):
        parts.append('places already secured: ' + '; '.join(t['secured']))
    if t.get('forecast'):                              # the figures a "paying their own way" decision used
        f = t['forecast']
        parts.append(f'savings {O.money(f["cash"])} against next season\'s forecast costs {O.money(f["costs"])} and '
                     f'income {O.money(f["income"])}')
    if t.get('net') is not None:
        parts.append(f'season net {O.money(t["net"])}')
    if t.get('events') is not None:
        parts.append(f'{t["events"]} starts')
    if t.get('am_rank'):
        parts.append(f'amateur ranking {t["am_rank"]}')
    if t.get('injury_weeks'):
        parts.append(f'{t["injury_weeks"]} weeks injured')
    if t.get('via'):
        parts.append(f'via {O.esc(t["via"])}')
    if t.get('graduating'):
        parts.append('college eligibility ended')
    return f'<strong>{O.esc(kind)}</strong>' + (' — ' + ' · '.join(parts) if parts else '')


def _season_file(w, y):
    try:
        return w.a.year(y)
    except Exception:
        return None


def decisions(w, pid, y):
    """This golfer's recorded career decisions in the winter after season y (from the season file)."""
    import observer_data as OD

    def by_golfer(d):
        out = defaultdict(list)
        for t in d.get('transitions', []):
            out[t.get('gid')].append(t)
        return dict(out)
    got = OD.season_extract(w, y, 'transitions', by_golfer) if w.a and y in w.a.years else None
    return list((got or {}).get(pid, []))


def _state(row):
    return (row.get('tour') or '', row.get('status'), row.get('lifestyle'))


def _describe_state(w, st):
    O = _o()
    tour, status, life = st
    if life == 'retired':
        return 'retired from competition'
    bits = [STATUS.get(status, status or '?'), (life or '').replace('_', '-')]
    return ', '.join(b for b in bits if b) + (f' · {O.tour_link(w, tour)}' if tour else '')


def card_reason_text(reason, tour):
    """A recorded card reason (cards.apply_cards) in words."""
    if reason == 'kept card':
        return ('kept their card: top 200 of the Premier money list' if (tour or '').startswith('PT_')
                else 'kept their card on the tour\'s money list')
    if reason == 'mini tour':
        return 'a mini tour member (mini tours are open)'
    if reason == 'no status':
        return 'no status elsewhere: their home mini tour'
    return reason


def status_section(w, pid, p):
    """Now: status, lifestyle, membership, level, Premier rights, a winner's exemption, why they hold their
    card, college eligibility; then every change of tour, status or lifestyle with its recorded reason."""
    O = _o()
    gs = p.get('golfer') or {}
    if not gs:
        return ''
    lv = w.live if (w.live is not None and pid in w.live.people) else None
    rows = []
    tour = gs.get('tour')
    tier = (w.tours().get(tour) or {}).get('tier') if tour else None
    import observer_data as OD
    rows.append(('Status', O.esc(OD.playing_status(gs)[1])))     # (retired, with the status last held)
    rows.append(('Lifestyle', O.esc(LIFESTYLE.get(gs.get('lifestyle'), gs.get('lifestyle') or '—'))))
    if gs.get('lifestyle') != 'retired':
        if tour:
            rows.append(('Membership', O.tour_link(w, tour)))
            rows.append(('Level', O.esc(LEVELS.get(tier, '—'))))
        elif gs.get('status') == 'club_pro':
            rows.append(('Membership', 'club professional: the section events of their region'))
    if lv is not None:
        r = getattr(lv, 'rights', {}).get(pid)
        if r:
            rows.append(('Premier playing rights', f'{O.esc(r[0])} — {O.esc(r[1])} <a href="/rules#premier-rights">rule</a>'))
        e = getattr(lv, 'earned', {}).get(pid)
        if e:
            rows.append(('Winner’s exemption', f'{O.esc(e)}: exempt into Premier fields whatever the membership '
                                                '<a href="/rules#winner-exemption">rule</a>'))
        why = getattr(lv, 'card_reasons', {}).get(pid)
        if why:
            rows.append(('Holds this card because', O.esc(card_reason_text(why, tour))
                         + f' <a href="/rules#{"premier-cards" if (tour or "").startswith("PT_") else "lower-cards"}">rules</a>'))
        col = getattr(lv, 'college', {}).get(pid) or []
        if tour and tour.startswith('CO_') and p.get('born'):
            text = f'college season {len(col) + 1} now'
            if w.a and pid in w.a.people and w.a.people[pid].get('initial'):
                text += ' (any seasons before the world began are not recorded)'
            rows.append(('College eligibility', f'{O.esc(text)}; eligible through {p["born"] + 22} (the season they '
                                                f'turn 22) <a href="/rules#college-eligibility">rule</a>'))
    out = ['<h2>Status</h2><dl class="kv">' + ''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in rows) + '</dl>']
    out.append(status_changes(w, pid))
    return ''.join(out)


def status_changes(w, pid, cap=2):
    """Every change of tour, status or lifestyle between seasons, with why: the card reason recorded with the
    season (since rules 2026-10-30), and for a change of status or lifestyle the recorded decision."""
    O = _o()
    import observer_data as OD
    career = OD.career_rows(w, pid)
    if not career:
        return ''
    states = [(y, _state(row), row) for y, row in career]
    now = None
    if w.live is not None and pid in w.live.people:
        lp = w.live.people[pid]
        now = (lp.get('tour') or '', lp.get('status'), lp.get('lifestyle'))
    elif w.a and pid in w.a.people and w.a.years and states[-1][0] < w.a.years[-1]:
        gs = w.a.people[pid].get('golfer') or {}
        now = (gs.get('tour') or '', gs.get('status'), gs.get('lifestyle'))
    rows, reads = [], 0
    for (y, st, row), nxt in zip(states, [s[1] for s in states[1:]] + [now]):
        if nxt is None or nxt == st:
            continue
        why = []
        if row.get('card_reason') and nxt[0] != st[0] and nxt[1] == st[1]:
            why.append(O.esc(card_reason_text(row['card_reason'], nxt[0])))
        elif nxt[0] != st[0] and nxt[1] == st[1] and nxt[2] == st[2]:
            why.append('promoted' if row.get('promoted') else 'lost their card' if row.get('demoted') else 'moved tour')
        if nxt[1:] != st[1:]:
            if 'decisions' in row or 'exemption' in row or reads < cap:
                if 'decisions' in row:                 # recorded with the season (since rules 2026-10-30)
                    ts = row['decisions']
                elif 'exemption' in row:               # a season recorded since then: no decision of theirs
                    ts = []
                else:                                  # older seasons: that season's file
                    reads += 1
                    ts = decisions(w, pid, y)
                why += [decision_text(t) for t in ts]
                if not ts:
                    why.append('<span class="muted">no decision recorded</span>')
            else:
                why.append(f'<a href="/golfer/{pid}?tab=season&year={y}">see the {y} season</a>')
        rows.append([f'<a href="/golfer/{pid}?tab=season&year={y}">after {y}</a>', _describe_state(w, st),
                     _describe_state(w, nxt), '<br>'.join(why)])
    if not rows:
        return '<p class="muted">No change of tour, status or lifestyle in the recorded seasons.</p>'
    return ('<h3>How their status changed</h3>' + O.table(['When', 'From', 'To', 'Why (as recorded)'], rows)
            + f'<p class="muted">{DECISION_NOTE} Card reasons are recorded from rules 2026-10-30; for earlier seasons '
              'a tour change shows only whether it was a promotion, and the season page has that season\'s history '
              'lines.</p>')


# ---- a season as it was ----------------------------------------------------------------------------------------
def season_view(w, q, pid, p):
    """The profile as of one season: that season's facts, never today's."""
    import observer_data as OD
    from golfsim.ratings import ATTRIBUTE_KEYS, ATTRIBUTE_LABELS
    O = _o()
    try:
        y = int(O.one(q, 'year'))
    except (TypeError, ValueError):
        return '<p class="muted">Choose a season from the season-by-season table.</p>'
    cur = w.live.cursor['year'] if w.live else None
    career = dict(OD.career_rows(w, pid))
    live = y == cur and w.live is not None and pid in w.live.people
    row = career.get(y)
    if row is None and not live:
        return f'<p class="muted">No season {y} is recorded for this golfer.</p>'
    born = p.get('born')
    years = sorted(set(career) | ({cur} if w.live is not None and pid in w.live.people else set()))
    i = years.index(y)
    nav = ' · '.join(x for x in (
        f'<a href="/golfer/{pid}?tab=season&year={years[i - 1]}">← {years[i - 1]}</a>' if i > 0 else '',
        f'<a href="/golfer/{pid}?tab=playing">whole career</a>',
        f'<a href="/golfer/{pid}?tab=season&year={years[i + 1]}">{years[i + 1]} →</a>' if i + 1 < len(years) else '') if x)
    out = [f'<p>{nav}</p>']
    if live:
        lp = w.live.people[pid]
        out.append(f'<div class="banner warn">{y} is in progress (to {O.date_text(w.live.cursor)}): a partial season.</div>')
        facts = [('Age*', O.age_text(w, born, y)), ('Tour', O.tour_link(w, lp.get('tour'))),
                 ('Status', O.esc(STATUS.get(lp.get('status'), lp.get('status')))),
                 ('Lifestyle', O.esc(LIFESTYLE.get(lp.get('lifestyle'), lp.get('lifestyle'))))]
        r = getattr(w.live, 'rights', {}).get(pid)
        if r:
            facts.append(('Premier rights at entry', f'{O.esc(r[0])} — {O.esc(r[1])}'))
        e = getattr(w.live, 'earned', {}).get(pid)
        if e:
            facts.append(('Winner’s exemption', O.esc(e)))
        if pid in w.live.wr:
            facts.append(('World ranking now', O.esc(w.live.wr[pid])))
        facts.append(('Prize money so far', O.money(w.live.prize.get(pid, 0.0))))   # (no ledger: paid nothing)
    else:
        facts = [('Age*', O.age_text(w, born, y)), ('Tour', O.tour_link(w, row.get('tour'))),
                 ('Status', O.esc(STATUS.get(row.get('status'), row.get('status')))),
                 ('Lifestyle', O.esc(LIFESTYLE.get(row.get('lifestyle'), row.get('lifestyle'))))]
        r = row.get('rights')
        if r:
            facts.append(('Premier rights at entry', f'{O.esc(r[0])} — {O.esc(r[1])}'))
        if row.get('exemption'):
            facts.append(('Winner’s exemption held', O.esc(row['exemption'])))
        rank = lambda a, b: f'{O.esc(a or "—")} → {O.esc(b or "—")}'
        facts.append(('World ranking (start → end)', rank(row.get('wr_start'), row.get('wr_end'))))
        if row.get('status') == 'amateur' or row.get('am_end'):
            facts.append(('Amateur ranking (start → end)', rank(row.get('am_start'), row.get('am_end'))))
        nt = row.get('next_tour')
        facts.append(('Card for the next season', (O.tour_link(w, nt) if nt else '—')
                      + (f' — {O.esc(card_reason_text(row["card_reason"], nt))}' if row.get('card_reason') else '')))
        facts.append(('Prize money (gross)', O.money(row.get('prize'))))
        if row.get('net') is not None:
            facts.append(('Season net (after costs)', O.money(row.get('net'))))
        res = row.get('residence')
        facts.append(('Lived in', O.esc(', '.join(reversed([x for x in res if x])) if res else 'unknown')))
        if row.get('college'):
            c = row['college']
            facts.append(('College eligibility', f'season {c["season"]} recorded (from {c["first_recorded"]}); '
                                                 f'eligible through {c.get("final") or "?"}'))
        if row.get('injury_weeks'):
            facts.append(('Weeks injured', O.esc(row['injury_weeks'])))
        if row.get('events') == 0 and row.get('access'):
            from golfsim import access as ACC
            kind, text = ACC.zero_start_summary(row['access'], row.get('injury_weeks') or 0, row.get('lifestyle'))
            old = row.get('zero_start_reason')
            facts.append(('No starts', O.esc(text) + (f' <span class="muted">(the label recorded then, by an older '
                                                     f'engine: “{O.esc(old)}”)</span>' if old and old != text else '')))
        elif row.get('zero_start_reason'):
            facts.append(('No starts', O.esc(row['zero_start_reason'])))
    facts.append(('Rules', rules_note(w, y)))
    out.append('<dl class="kv">' + ''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in facts) + '</dl>')
    if row and row.get('access'):
        out.append(week_ledger(w, row, pid, y))
    # results that season
    rows = [r for r in OD.results(w, pid) if r['year'] == y]
    db, _ = w.statistics()
    OD.cut_flags(w, rows, db)
    agg = OD.season_rollup(rows).get(y, {'all': dict.fromkeys(OD.ST.COLUMNS, 0)})['all']
    link = lambda label, outcome=None: O.results_link(pid, label, year=y, outcome=outcome)
    out.append('<h2>Results</h2>' + O.table(['Starts', 'Wins', 'Runner-up', 'Top 5', 'Top 10', 'Cuts made', 'Missed cuts'], [[
        link(str(agg['starts'])), link(str(agg['wins']), 'win'), link(str(agg['runner_ups']), 'runner-up'),
        link(str(agg['top5']), 'top5'), link(str(agg['top10']), 'top10'),
        f'{agg["cuts_made"]}/{agg["cut_events"]}' if agg['cut_events'] else '—',
        link(str(agg['cut_events'] - agg['cuts_made']), 'missed-cut') if agg['cut_events'] else '—']],
        numeric=tuple(range(7))))
    best = sorted((r for r in rows if r['pos'] and not OD.is_qualifying(r)), key=lambda r: (r['pos'], r['week']))[:10]
    if best:
        out.append(O.table(['Week', 'Event', 'Pos'], [[O.esc(r['week']), O.event_link(w, r['event']), O.esc(r['pos'])]
                                                    for r in best], numeric=(0, 2)))
    # ratings at the start and the end of the season (recorded snapshots only)
    keys = (w.a.world.get('rating_keys') if w.a else None) or ['overall', *ATTRIBUTE_KEYS]
    snaps = OD.rating_snapshots(w, pid)
    start = dict(zip(keys, snaps[y])) if y in snaps else None
    if live:
        cur_r = w.live.people[pid].get('ratings')
        end = dict(zip(['overall', *ATTRIBUTE_KEYS], cur_r)) if cur_r else None
        end_label = 'Now'
    else:
        end = dict(zip(keys, snaps[y + 1])) if (y + 1) in snaps else None
        end_label = 'End of season'
    if start or end:
        lab = {'overall': 'Overall', **ATTRIBUTE_LABELS}
        def cell(d, k):
            return f'{d[k]:.1f}' if d and d.get(k) is not None else 'unavailable'
        def change(k):
            if not (start and end) or start.get(k) is None or end.get(k) is None:
                return '<span class="muted">unavailable</span>'
            d = round(end[k] - start[k], 1)
            return f'<span class="{"up" if d > 0 else "down" if d < 0 else "muted"}">{d:+.1f}</span>'
        out.append('<h2>Ratings</h2>' + O.table(['', f'Start of {y}', end_label, 'Change'],
                                                [[O.esc(lab.get(k, k)), cell(start, k), cell(end, k), change(k)]
                                                 for k in ['overall', *ATTRIBUTE_KEYS]], numeric=(1, 2, 3))
                   + '<p class="muted">Recorded snapshots only (ratings at the start of a season are recorded when the '
                     'season before it is archived): “unavailable” where none was recorded. Potential is never shown.</p>')
    else:
        out.append('<h2>Ratings</h2><p class="muted">Not recorded for this season (seasons archived before ratings were '
                   'kept, or the world\'s first season): today\'s ratings are not shown in their place.</p>')
    # the team that season
    if w.a and pid in w.a.people:
        team = [s for s in w.a.golfer_staff(pid) if s.start <= (y, 53) and (s.end is None or s.end > (y, 1))]
        if team:
            out.append('<h2>Team that season</h2>' + O.table(['Role', 'Who', 'From', 'To'], [
                [O.esc(s.kind), w.person_link(s.staff) if s.staff else O.esc(s.arrangement), O.when(s.start),
                 O.when(s.end) if s.end else 'still together'] for s in team]))
    # that winter: decisions, moves and the season's history lines (the season file)
    if not live and w.a and y in w.a.years:
        d = _season_file(w, y) or {}
        ts = [t for t in d.get('transitions', []) if t.get('gid') == pid]
        mv = [m for m in d.get('moves', []) if m.get('person') == pid]
        log = d.get('log', {}).get(str(pid)) or d.get('log', {}).get(pid) or []
        if ts:
            out.append('<h2>Decisions that winter</h2><ul>' + ''.join(f'<li>{decision_text(t)}</li>' for t in ts)
                       + f'</ul><p class="muted">{DECISION_NOTE}</p>')
        if mv:
            out.append('<h2>Moves</h2><ul>' + ''.join(
                f'<li>{O.esc(O.where(_place(m.get("from"))))} → {O.esc(O.where(_place(m.get("to"))))}: '
                f'{O.esc(m.get("reason"))}</li>' for m in mv) + '</ul>')
        if log:
            out.append('<h2>History lines</h2><ul>' + ''.join(
                f'<li>{O.esc("end of season" if wk >= 53 else f"week {wk}")}: {O.esc(t)}</li>' for wk, t in log) + '</ul>')
    return ''.join(out)


def _place(x):
    if x is None:
        return None
    if isinstance(x, dict):
        return x
    return {'country': x[0], 'region': x[1] if len(x) > 1 else None}


# ---- coaches and caddies -----------------------------------------------------------------------------------------
def week_ledger(w, row, pid, y):
    """The season's weeks by what happened (golfsim.access): played, injured, barriers (with the stage that
    kept them out) and choices, each with its weeks out of the weeks recorded, and the weeks they were shut
    out or played an alternative with the event they wanted."""
    from golfsim import access as ACC
    O = _o()
    lg = ACC.ledger(row['access'])
    n = lg['weeks'] or 1
    pct = lambda k: f'{100 * k / n:.0f}%'
    rows = [['played', '', str(lg['played']), pct(lg['played'])]] if lg['played'] else []
    if lg['injured']:
        rows.append(['injured', '', str(lg['injured']), pct(lg['injured'])])
    for name in list(ACC.BARRIERS) + list(ACC.CHOICES):
        k = lg['groups'].get(name)
        if k:
            kind = 'barrier' if name in ACC.BARRIERS else 'choice'
            detail = ', '.join(f'{d.replace("chose to ", "")} {lg["detail"][d]}' for d in
                               (ACC.BARRIERS.get(name) or ACC.CHOICES.get(name)) if lg['detail'].get(d))
            rows.append([f'{kind}: {name}', O.esc(ACC.STAGE[name]) + (f' ({O.esc(detail)})' if ',' in detail else ''),
                         str(k), pct(k)])
    out = ['<h2>The season week by week</h2>' + O.table(['What happened', 'Where it was decided', 'Weeks', 'Share'],
                                                        rows, numeric=(2, 3))]
    out.append(f'<p class="muted">{lg["weeks"]} weeks recorded. Each week is classified once, when it is played, '
               'in this order: played; injured; not admitted (every acceptable field full, or not picked for the '
               'college lineup); no suitable event scheduled; not eligible; could not afford any event; declined; '
               'trained, rested or worked. Choices are counted only when an affordable event they could enter '
               'existed that week, so a season with barrier weeks is never called voluntary.</p>')
    denied = row.get('denied') or []
    if denied:
        out.append('<h3>Weeks shut out or playing an alternative</h3>' + O.table(['Week', 'What happened', 'Wanted',
                                                                                   'Played instead'], [
            [O.esc(d[0]), O.esc(d[1]), O.event_link(w, d[2]) if d[2] else '—', O.event_link(w, d[3]) if d[3] else '—']
            for d in denied], numeric=(0,)))
    return ''.join(out)


def team_history(w, pid):
    """Coaches and caddies in separate sections: dated stints with the starts and wins they shared (from the
    team recorded with each result, never from today's assignments)."""
    import observer_data as OD
    O = _o()
    out = []
    lv = w.live if (w.live is not None and pid in w.live.people) else None
    if lv is not None:
        coach, caddie = lv.coach_of.get(pid), lv.caddie_of.get(pid)
        out.append(f'<p>Now: coach {w.person_link(coach) if coach else "none"} · caddie '
                   f'{w.person_link(caddie) if caddie else "none"}.</p>')
    stints = w.a.golfer_staff(pid) if w.a and pid in w.a.people else []
    if not stints:
        out.append('<p class="muted">Dated stints are archived when a season ends.</p>' if not w.a else
                   '<p class="muted">No coaches or caddies recorded.</p>')
        return ''.join(out)
    rows = OD.results(w, pid)
    through = w.a.years[-1]
    for kind, title in (('coach', 'Coaches'), ('caddie', 'Caddies'), ('school', 'School teams')):
        ss = [s for s in stints if s.kind == kind]
        if not ss:
            continue
        table_rows = []
        for s in ss:
            if kind == 'school':
                during = [r for r in rows if (r['year'], r['week']) >= s.start and (s.end is None or (r['year'], r['week']) < s.end)]
            else:
                during = [r for r in rows if r[kind] == s.staff and (r['year'], r['week']) >= s.start
                          and (s.end is None or (r['year'], r['week']) < s.end)]
            wins = sum(1 for r in during if r['pos'] == 1 and not OD.is_qualifying(r))
            table_rows.append([w.person_link(s.staff) if s.staff else O.esc(s.arrangement), O.esc(s.arrangement),
                               O.when(s.start), O.when(s.end) if s.end else 'still together',
                               str(len(during)), str(wins), O.esc(s.reason_end or '')])
        out.append(f'<h2>{title}</h2>' + O.table(['Who', 'Arrangement', 'From', 'To', 'Starts together', 'Wins together',
                                                  'Why it ended'], table_rows, numeric=(4, 5)))
    out.append(f'<p class="muted">Stints as recorded at the end of {through}; starts and wins together are this golfer\'s '
               'results with that person recorded on their team that week (their achievements, not the coach\'s or '
               'caddie\'s own wins). Changes since then show under “Now” and in each result.</p>')
    return ''.join(out)


# ---- where a person has lived ----------------------------------------------------------------------------------
def residence_section(w, pid, p, geo):
    """Birthplace and nationality (fixed), the residence they had on entering the world (an initial placement,
    not a move: a college base is placed free by the school), then each dated move with its reason."""
    O = _o()
    if not geo:
        return ''
    first_year = (w.a.world.get('first_year') if w.a else None) or (w.live.history_years[0] if w.live and w.live.history_years else None)
    rows = [['born', O.esc(O.where(geo.get('birthplace'))),
             f'birthplace; nationality {O.esc(p.get("country"))} (neither ever changes)']]
    f = geo.get('first_residence')
    if f:
        note = f.get('note') or ('lived there when the world began' if f.get('week') == 0 else 'on arrival')
        rows.append([O.esc(f['year']), O.esc(O.where(f.get('place'))), O.esc(note) + ' <span class="tag">initial placement, not a move</span>'])
    elif geo.get('residence') is None:
        rows.append(['—', 'unknown', 'from a save made before residences were recorded'])
    for m in geo.get('moves') or ():
        rows.append([O.esc(m['year']) + ('' if m.get('week', 53) >= 53 else f' wk {m["week"]}'),
                     f'{O.esc(O.where(m.get("from")))} → {O.esc(O.where(m.get("to")))}', O.esc(m.get('reason'))])
    return ('<h2>Where they have lived</h2>' + O.table(['When', 'Where', 'Why'], rows)
            + '<p class="muted">Region and country (no cities). College bases are placed by the school at no cost; '
              'other moves are their own choice, at most one each winter.</p>')


# ---- tournaments and courses --------------------------------------------------------------------------------------
def series_summary(w, sid):
    """A tournament's history in brief: editions, most-used courses, most wins, most starts, youngest and
    oldest winners -- every figure counted from its editions, with links to them."""
    O = _o()
    idx = w.a.index if w.a else None
    wins, starts, courses, winners = Counter(), Counter(), Counter(), []
    formats = set()
    if idx is not None:
        for eid, y, wk, winner in idx.db.execute('SELECT event_id, year, week, winner FROM editions WHERE series = ?'
                                                 + idx.upto(), (sid,)):
            if winner:
                wins[winner] += 1
                winners.append((y, eid, winner))
        for c, n in idx.db.execute('SELECT si.course, COUNT(*) FROM sites si JOIN editions e USING(eid) WHERE e.series = ?'
                                   + idx.upto('e.year') + ' GROUP BY si.course', (sid,)):
            courses[c] += n
        for person, n in idx.db.execute('SELECT s.person, COUNT(*) FROM starts s JOIN editions e USING(eid) WHERE e.series = ?'
                                        + idx.upto('e.year') + ' GROUP BY s.person', (sid,)):
            starts[person] += n
    if w.live is not None:
        for e in w.live.editions.values():
            if e['series'] != sid:
                continue
            formats.add((e.get('rounds'), bool(e.get('match_play'))))
            win = next((g for g, pp, _ in (e['finish'][0] if e['finish'] else []) if pp == 1), None)
            if win:
                wins[win] += 1
                winners.append((int(e['id'].split(':')[0]), e['id'], win))
            for c, _, _ in e['sites']:
                courses[c] += 1
            for site in e['finish']:
                for g, _, _ in site:
                    starts[g] += 1
    if not winners and not starts:
        return ''
    born = lambda g: (w.person(g) or {}).get('born')
    aged = [(y - born(g), y, eid, g) for y, eid, g in winners if born(g)]
    youngest = sorted(aged, key=lambda x: (x[0], x[1]))[:3]
    oldest = sorted(aged, key=lambda x: (-x[0], x[1]))[:3]
    rl = lambda g, n, outcome=None: O.results_link(g, str(n), series=sid, outcome=outcome)
    cards = []
    cards.append('<div class="card"><h4>Most wins</h4>' + (O.table(['Golfer', 'Wins'], [
        [w.person_link(g), rl(g, n, 'win')] for g, n in sorted(wins.items(), key=lambda x: (-x[1], x[0]))[:5]], numeric=(1,))
        if wins else '<p class="muted">—</p>') + '</div>')
    cards.append('<div class="card"><h4>Most starts</h4>' + (O.table(['Golfer', 'Starts'], [
        [w.person_link(g), rl(g, n)] for g, n in sorted(starts.items(), key=lambda x: (-x[1], x[0]))[:5]], numeric=(1,))
        if starts else '<p class="muted">—</p>') + '</div>')
    cards.append('<div class="card"><h4>Most-used courses</h4>' + (O.table(['Course', 'Editions'], [
        [O.course_link(w, c), str(n)] for c, n in sorted(courses.items(), key=lambda x: (-x[1], x[0]))[:5]], numeric=(1,))
        if courses else '<p class="muted">—</p>') + '</div>')
    cards.append('<div class="card"><h4>Youngest and oldest winners*</h4>' + (O.table(['', 'Age*', 'Golfer', 'Edition'], [
        [label, str(a), w.person_link(g), O.event_link(w, eid)] for label, rows_ in (('youngest', youngest), ('oldest', oldest))
        for a, y, eid, g in rows_], numeric=(1,)) if aged else '<p class="muted">—</p>') + '</div>')
    n_eds = len({eid for _, eid, _ in winners})
    return (f'<h2>The {O.esc(w.series_name(sid))} in brief</h2><p>{n_eds} edition{"s" if n_eds != 1 else ""} won · '
            f'{len(starts):,} golfers have played it · {sum(starts.values()):,} starts in all</p><div class="rgrid">' + ''.join(cards) + '</div>'
            + '<p class="muted">Counted over every edition played (series-wide), each edition once; a course hosting '
              'several sites of one edition counts once per site. Wins and starts link to the golfer\'s results in this '
              f'tournament. * {O.AGE_NOTE}</p>')


def course_use(w, cid):
    """A course's tournament mix and total starts (2090 audit: an elite venue's use should be visible)."""
    O = _o()
    idx = w.a.index if w.a else None
    mix = {}
    total = 0
    if idx is not None:
        for sid, n, lo, hi in idx.db.execute('SELECT e.series, COUNT(*), MIN(e.year), MAX(e.year) FROM sites si JOIN '
                                             'editions e USING(eid) WHERE si.course = ?' + idx.upto('e.year')
                                             + ' GROUP BY e.series', (cid,)):
            mix[sid] = [n, lo, hi]
        total = idx.db.execute('SELECT COUNT(*) FROM starts st JOIN sites si ON st.eid = si.eid AND st.site = si.site '
                               'WHERE si.course = ?' + idx.upto('si.year'), (cid,)).fetchone()[0]
    if w.live is not None:
        for e in w.live.editions.values():
            y = int(e['id'].split(':')[0])
            for k, (c, _, _) in enumerate(e['sites']):
                if c != cid:
                    continue
                m = mix.setdefault(e['series'], [0, y, y])
                m[0] += 1
                m[1], m[2] = min(m[1], y), max(m[2], y)
                total += len(e['finish'][k]) if k < len(e['finish']) else 0
    if not mix:
        return ''
    rows = sorted(mix.items(), key=lambda x: (-x[1][0], x[0]))
    return ('<h2>Tournament mix</h2>' + O.table(['Tournament', 'Editions here', 'First', 'Latest'], [
        [f'<a href="/series/{quote(sid)}">{O.esc(w.series_name(sid))}</a>', str(n), str(lo), str(hi)]
        for sid, (n, lo, hi) in rows], numeric=(1, 2, 3))
        + f'<p>{total:,} starts played here in all.</p>')


# ---- rounds, replay and scorecards ------------------------------------------------------------------------------
def full_edition(w, e):
    """The edition as recorded in full (round scores, prizes, conditions, a major's holes), or None."""
    if e.get('source') == 'current season':
        return w.live.editions.get(e['id'])
    if not w.a or e['year'] not in w.a.years:
        return None
    d = _season_file(w, e['year'])
    return next((x for x in (d or {}).get('events', []) if x['id'] == e['id']), None)


def _layout_par(w, site):
    c = w.courses().get(site[0], {})
    return (c.get('layouts', {}).get(site[1]) or {}).get('par')


def playoff_at(full, site):
    """A site's playoff: {'players', 'winner', 'holes' (None when the extra holes were not recorded), 'length'
    (extra holes, None when not recorded for this site)}, or None if the site had no playoff. Editions played
    before playoffs were kept give the players from the recorded finish (everyone tied for first after
    regulation: the winner, and the runners-up on the same total) and the length only for a single site."""
    rec = (full.get('playoffs') or [None] * (site + 1))
    if full.get('playoffs') is not None and site < len(rec):
        p = rec[site]
        if p is None:
            return None
        return {'players': list(p['players']), 'winner': p['winner'],
                'holes': [(n, h, {int(g): v for g, v in sc.items()}) for n, h, sc in p['holes']],
                'length': len(p['holes'])}
    if not full.get('playoff') or site >= len(full.get('finish') or []):
        return None
    fin = full['finish'][site]
    if not fin or fin[0][2] is None:
        return None
    best = fin[0][2]
    players = [g for g, p, t in fin if t == best and p in (1, 2)]
    if len(players) < 2:
        return None
    return {'players': players, 'winner': fin[0][0], 'holes': None,
            'length': full['playoff'] if len(full['finish']) == 1 else None}


def regulation_rounds(full, site, gid):
    """How many regulation rounds a golfer's total covers: their recorded round scores, else the event's rounds."""
    sc = full.get('scores') or []
    by = sc[site] if site < len(sc) and sc[site] else {}
    rs = by.get(str(gid)) or by.get(gid)
    return len(rs) if rs else full.get('rounds')


def playoff_lines(w, full, site, round_par=None):
    """HTML: who was in the playoff (every player, won or lost), its length and, where recorded, each extra hole.
    round_par: the course's par for one round; the tie is shown against the par of all the regulation rounds."""
    O = _o()
    po = playoff_at(full, site)
    if po is None:
        return ''
    win = po['winner']
    losers = [g for g in po['players'] if g != win]
    length = (f'{po["length"]} extra hole{"s" if po["length"] != 1 else ""}' if po['length'] is not None
              else 'its length was not recorded for this site')
    total = next((t for g, p, t in full['finish'][site] if g == win), None)
    rounds = regulation_rounds(full, site, win)
    to_par = f' ({total - round_par * rounds:+d})' if round_par and total is not None and rounds else ''
    tie = f' at {total}{to_par}' if total else ''
    out = [f'<p><strong>Playoff</strong>: {len(po["players"])} players tied{tie} after regulation; {length}. '
           f'{w.person_link(win)} won the playoff; lost the playoff: '
           + ', '.join(w.person_link(g) for g in losers) + '.</p>']
    if po['holes']:
        rows = [[str(n), str(h)] + [O.esc(sc.get(g, '—')) for g in po['players']] for n, h, sc in po['holes']]
        out.append(O.table(['Extra hole', 'Course hole'] + [w.name(g) for g in po['players']], rows,
                           numeric=tuple(range(0, 2 + len(po['players'])))))
        out.append('<p class="muted">Strokes on each extra hole (sudden death: “—” once a player was beaten).</p>')
    else:
        out.append('<p class="muted">The extra holes\' scores were not recorded for this edition (played before '
                   'playoff holes were kept); the players, the winner and the final places are as recorded.</p>')
    return ''.join(out)


def playoff_status(full, site, gid):
    """'Won playoff' / 'Lost playoff' (with the extra hole they went out at, when recorded) or ''."""
    po = playoff_at(full, site)
    if po is None or gid not in po['players']:
        return ''
    if gid == po['winner']:
        return 'Won playoff'
    out = [n for n, h, sc in (po['holes'] or ()) if gid in sc]
    return 'Lost playoff' + (f' (out at extra hole {max(out)})' if out else '')


def rounds_view(w, q, e):
    """The replay of an edition's recorded rounds: the leaderboard after each round (nothing after the round shown:
    no later rounds, final places or winner until the final round, which shows any playoff), each round's
    conditions, and for majors each golfer's hole-by-hole scorecard."""
    O = _o()
    eid = e['id']
    full = full_edition(w, e)
    base = f'/event/{quote(eid)}'
    if not full or not full.get('scores'):
        return ('<p class="muted">Round scores were not recorded for this edition (played before rules 2026-10-30): '
                'only final positions and totals are kept, and rounds are never reconstructed from a total.</p>')
    site = int(O.one(q, 'site', '0') or 0)
    scores = full['scores'][site] if site < len(full['scores']) else {}
    n = max((len(v) for v in scores.values()), default=0)
    if not n:
        return '<p class="muted">No stroke-play rounds at this site (match play keeps final places only).</p>'
    k = max(1, min(n, int(O.one(q, 'round', '1') or 1)))    # a replay starts at round one: nothing ahead shown
    player = O.one(q, 'player')
    if player and full.get('holes'):
        return scorecard(w, full, int(player), base, k, n)
    par = _layout_par(w, full['sites'][site]) if site < len(full['sites']) else None
    board = []
    for g, rs in scores.items():
        if len(rs) >= k:
            board.append((sum(rs[:k]), int(g), rs))
    board.sort(key=lambda x: (x[0], x[1]))
    if k == n:                                         # the final round: who missed the cut, below the rest
        board += sorted(((sum(rs), int(g), rs) for g, rs in scores.items() if len(rs) < n), key=lambda x: (x[0], x[1]))
    totals = [b[0] for b in board if len(b[2]) >= k]
    rank = {}
    for i, t in enumerate(totals):
        rank.setdefault(t, i + 1)
    count = Counter(totals)
    cond = (full.get('conditions') or [None] * (site + 1))[site] if full.get('conditions') else None
    final = {r[0]: r for r in (full['finish'][site] if site < len(full['finish']) else [])}
    step = lambda i: f'after round {i}'
    steps = ' · '.join((f'<strong>{step(i)}</strong>' if i == k else f'<a href="{base}?{urlencode({"view": "rounds", "round": i, "site": site})}">{step(i)}</a>')
                       for i in range(1, n + 1))
    out = [f'<p><span class="tag">Replay</span> The recorded rounds, revealed one at a time: the event is already '
           f'complete and nothing is simulated here. {steps}</p>']
    if len(full['sites']) > 1:
        out.append('<p>Site: ' + ' · '.join((f'<strong>{i + 1}</strong>' if i == site else
                                             f'<a href="{base}?{urlencode({"view": "rounds", "site": i, "round": k})}">{i + 1}</a>')
                                            for i in range(len(full['sites']))) + '</p>')
    if cond and k - 1 < len(cond):
        wind, rain, pins = cond[k - 1]
        out.append(f'<p class="muted">Round {k}: wind {wind} mph{", rain" if rain else ""}, pin difficulty {pins}.</p>')
    has_holes = bool(full.get('holes'))
    rows = []
    for t, g, rs in board:
        if len(rs) < k:                                # missed the cut: the rounds they played
            rows.append(['MC', w.person_link(g)] + [str(x) for x in rs] + ['' for _ in range(k - len(rs))]
                        + [str(t), f'{t - len(rs) * par:+d}' if par else '—', 'missed cut'])
            continue
        pos = rank[t]
        label = ('T' if count[t] > 1 else '') + str(pos)
        name = w.person_link(g) + (f' <a href="{base}?{urlencode({"view": "rounds", "player": g, "site": site, "round": k})}" '
                                   'class="muted">card</a>' if has_holes else '')
        status = ''
        if k < n and len(rs) == k and len(rs) < n:
            status = '<span class="muted">missed the cut after this round</span>'
        fin = final.get(g)
        if k == n:
            status = playoff_status(full, site, g) or (f'final {fin[1]}' if fin and fin[1] is not None
                                                         and fin[1] != pos else status)
        rows.append([label, name] + [str(x) for x in rs[:k]] + [str(t), f'{t - k * par:+d}' if par else '—', status])
    out.append(O.table(['Pos', 'Golfer'] + [f'R{i}' for i in range(1, k + 1)] + ['Total', 'To par', ''], rows,
                       numeric=tuple(range(2, 2 + k + 2))))
    if k == n:
        out.append(playoff_lines(w, full, site, par))
    out.append('<p class="muted">Positions after a round are by total so far (ties share a place, “T”); nothing after the '
               'round shown is revealed (no final places, winner or later rounds) until the final round, where any '
               'playoff decides the winner. Missed-cut players have only the rounds before the cut.'
               + (' “card”: a major\'s hole-by-hole scorecard.' if has_holes else '') + '</p>')
    return ''.join(out)


def scorecard(w, full, gid, base, through=None, n=None):
    """A major's hole-by-hole card, through round `through` of the replay (no later round is shown)."""
    O = _o()
    site = next((i for i, s in enumerate(full.get('holes') or []) if str(gid) in s), None)
    if site is None:
        return '<p class="muted">No scorecard recorded for this golfer here.</p>'
    holes = full['holes'][site][str(gid)][:through]
    pars = (full.get('pars') or [None])[site] if full.get('pars') else None
    head = ['Round'] + [str(i) for i in range(1, 19)] + ['Total']
    rows = []
    if pars:
        rows.append(['Par'] + [str(p) for p in pars] + [str(sum(pars))])
    for r, hs in enumerate(holes, 1):
        cells = []
        for i, s in enumerate(hs):
            cls = '' if not pars else ('up' if s < pars[i] else 'down' if s > pars[i] else '')
            cells.append(f'<span class="{cls}">{s}</span>' if cls else str(s))
        rows.append([f'R{r}'] + cells + [str(sum(hs))])
    back = f'{base}?{urlencode({"view": "rounds", "round": through, "site": site})}' if through else f'{base}?view=rounds'
    shown = (f'<p class="muted">Through round {through} of the replay.</p>'
             if through and n and through < n else '')
    return (f'<p><a href="{back}">← leaderboard</a></p><h2>Scorecard: {w.person_link(gid)}</h2>' + shown
            + O.table(head, rows, numeric=tuple(range(1, 20)))
            + '<p class="muted">Strokes per hole as played (under par in green, over par in red). Hole-by-hole scores are '
              'kept for majors only.</p>')


# ---- records: dates and who is still pursuing them --------------------------------------------------------------
COUNTS = {'most-wins', 'most-wins-all-events', 'most-premier-wins', 'most-majors', 'most-starts', 'most-prize',
          'most-holes-in-one', 'most-playoff-wins', 'most-course-records', 'wins-on-most-tours',
          'runner-ups-without-a-win', 'not-won-yet', 'retired-without-a-win', 'coaches-major-champions'}
FIXED = {'youngest-winners', 'oldest-winners', 'youngest-major-champions', 'oldest-major-champions',
         'youngest-premier-debuts', 'oldest-premier-debuts', 'starts-before-first-win', 'major-droughts-ended'}
STREAKS = {'consecutive-wins': 'professional', 'consecutive-cuts': 'professional'}
UNITS = {'most-starts': 'starts', 'most-prize': 'dollars', 'consecutive-wins': 'wins in consecutive starts (inclusive)',
         'consecutive-cuts': 'cuts in consecutive starts (inclusive)', 'weeks-at-number-one': 'weeks',
         'longest-wait-between-wins': 'starts between two wins (exclusive)', 'major-droughts-ended': 'major starts without a win',
         'starts-before-first-win': 'starts before the first win (exclusive)', 'longest-coach-partnerships': 'weeks',
         'longest-caddie-partnerships': 'weeks'}


def _has_table(idx, name):
    """Whether an index has a table (an index from before schema 2, opened read-only, lacks the later ones)."""
    return idx is not None and idx.db.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                                              (name,)).fetchone() is not None


def _year_of(eid):
    try:
        return int(str(eid).split(':')[0])
    except ValueError:
        return None


def record_context(w, name, rows):
    """[(when html, now html)] for each row: the date or interval the record covers, and whether the person
    is still pursuing it -- currently extending, competing (could add to it), fixed, or closed (retired).
    'Now' is as of the snapshot; the record itself counts the archived seasons."""
    O = _o()
    out = []
    lv = w.live
    for r in rows:
        pid = r['person']
        active = r.get('active')
        years = [y for y in (_year_of(e) for e in r.get('evidence', ())) if y]
        if name in ('longest-coach-partnerships', 'longest-caddie-partnerships'):
            together = _together_now(w, name, r)
            when = f'{O.when(tuple(r["start"]))} – ' + (O.when(tuple(r['end'])) if r.get('end') else
                                                         'now' if together else 'this season')
            now = ('<span class="up">together now: extending</span>' if together else
                   'ended this season (after the archived count)' if r.get('current') else 'ended')
        elif name == 'weeks-at-number-one':
            span_ = _no1_span(w, pid)
            when = span_ or '—'
            if lv is not None and lv.wr.get(pid) == 1:
                now = '<span class="up">world No. 1 now: adding weeks</span>'
            else:
                now = 'competing, not No. 1 now' if active else 'closed (retired)'
        elif name in STREAKS:
            when = f'{min(years)}–{max(years)}' if years else '—'
            state = _streak_open(w, pid, STREAKS[name], r.get('evidence', []), name) if active else False
            if state:
                now = '<span class="up">currently extending</span>' + (
                    f' <span class="muted">(+{state - 1} this season, not yet counted)</span>' if state > 1 else '')
            else:
                now = 'ended' + ('' if active else ' · retired')
        elif name in FIXED:
            y = r.get('year') or r.get('first_win_year') or r.get('ended') or (years[0] if years else None)
            when = O.esc(y or '—')
            now = 'fixed (a single result)'
        elif name == 'longest-wait-between-wins':
            ys = r.get('years') or years
            when = f'{ys[0]}–{ys[-1]}' if ys else '—'
            now = 'fixed interval' + (' · still competing' if active else '')
        else:                                                   # career counts
            when = (f'{min(years)}–{max(years)}' if len(set(years)) > 1 else str(years[0])) if years else 'career'
            if name == 'coaches-major-champions':
                st = ((w.person(pid) or {}).get('coach') or {}).get('status')
                now = 'coaching: can add to it' if st == 'active' else 'closed (no longer coaching)'
            elif name == 'retired-without-a-win':
                now = 'closed (retired)'
            else:
                now = 'competing: can add to it' if active else 'closed (retired)'
        out.append((when, now))
    return out


def _no1_span(w, pid):
    idx = w.a.index if w.a else None
    if not _has_table(idx, 'number_one'):
        return None
    r = idx.db.execute("SELECT MIN(year * 100 + week), MAX(year * 100 + week) FROM number_one WHERE kind = 'world' "
                       'AND person = ?' + idx.upto(), (pid,)).fetchone()
    if not r or r[0] is None:
        return None
    a, b = divmod(r[0], 100), divmod(r[1], 100)
    return f'{a[0]} wk {a[1]} – {b[0]} wk {b[1]}'


def _streak_open(w, pid, scope, evidence, name):
    """Whether the record run is still alive at the snapshot: it ends at the golfer's latest archived start
    in the scope, and every start in the scope since (this season's, not yet archived) continues it.
    Returns False, or 1 + the number of this season's starts that extended it."""
    st = w.stats
    if st is None or not evidence:
        return False
    ss = [s for s in st.starts[pid] if st.in_scope(s, scope)]
    if not ss or ss[-1][2] != evidence[-1]:
        return False
    keeps = (lambda pos: pos == 1) if name == 'consecutive-wins' else (lambda pos: pos is not None)
    more = 0
    for pos in _live_positions(w, pid, scope, st):
        if not keeps(pos):
            return False
        more += 1
    return 1 + more


def _live_positions(w, pid, scope, st):
    """The golfer's finishing positions this season (not yet archived) in a HistoryStats scope, in order."""
    lv = w.live
    if lv is None or (w.a and lv.year in w.a.years):
        return []
    out = []
    for e in sorted(lv.editions.values(), key=lambda e: (e['week'], e['id'])):
        kind = 'major' if e.get('category') == 'major' else e.get('kind', '')
        if kind == 'qualifying' or not st.in_scope((lv.year, e['week'], e['id'], e.get('tour'), e.get('tier'), kind, None),
                                                   scope):
            continue
        for site in e['finish']:
            for g, pos, _ in site:
                if g == pid:
                    out.append(pos)
    return out


def _together_now(w, name, r):
    """Whether an archived partnership still open at the last archived season is still going at the snapshot."""
    if not r.get('current'):
        return False
    lv = w.live
    if lv is None:
        return True
    now = lv.coach_of if name == 'longest-coach-partnerships' else lv.caddie_of
    return now.get(r['person']) == r.get('staff')


# ---- Career Grand Slam ------------------------------------------------------------------------------------------
def major_wins(w):
    """[(year, week, event id, series, winner)] of every major, oldest first (archive and current season)."""
    out = []
    idx = w.a.index if w.a else None
    if idx is not None:
        q = (f'SELECT year, week, event_id, series, winner FROM editions WHERE series IN ({",".join("?" * len(MAJOR_SERIES))})'
             + idx.upto() + ' ORDER BY year, week')
        out = [tuple(r) for r in idx.db.execute(q, MAJOR_SERIES) if r[4]]
    elif w.a:
        for y, e in w.a.events():
            if e['series'] in MAJOR_SERIES:
                win = next((g for g, p, _ in (e['finish'][0] if e['finish'] else []) if p == 1), None)
                if win:
                    out.append((y, e['week'], e['id'], e['series'], win))
    if w.live is not None:
        for e in sorted(w.live.editions.values(), key=lambda e: e['week']):
            if e['series'] in MAJOR_SERIES:
                win = next((g for g, p, _ in (e['finish'][0] if e['finish'] else []) if p == 1), None)
                if win:
                    out.append((int(e['id'].split(':')[0]), e['week'], e['id'], e['series'], win))
    return sorted(out)


def grand_slams(w, wins=None):
    """{golfer: {'firsts': {series: (year, event)}, 'complete': (year, event) or None}} for every major
    champion: completion is the first win of the fourth distinct major."""
    out = {}
    for y, wk, eid, sid, g in (wins if wins is not None else major_wins(w)):
        d = out.setdefault(g, {'firsts': {}, 'complete': None})
        if sid not in d['firsts']:
            d['firsts'][sid] = (y, eid)
            if len(d['firsts']) == len(MAJOR_SERIES):
                d['complete'] = (y, eid)
    return out


def grand_slam_line(w, pid):
    O = _o()
    d = grand_slams(w).get(pid)
    if not d:
        return ''
    born = (w.person(pid) or {}).get('born')
    if d['complete']:
        y, eid = d['complete']
        return (f'<p><strong>Career Grand Slam</strong>: completed at the {O.event_link(w, eid)}, age {O.age_text(w, born, y)} '
                f'— first wins: ' + ', '.join(O.event_link(w, e) for _, e in sorted(d['firsts'].values())) + '</p>')
    missing = [w.series_name(s) for s in MAJOR_SERIES if s not in d['firsts']]
    return (f'<p class="muted">Majors won: {len(d["firsts"])} of the four (not yet: {O.esc(", ".join(missing))}).</p>'
            if len(d['firsts']) >= 2 else '')


def grand_slam_page(w, q):
    O = _o()
    gs = grand_slams(w)
    done = sorted(((d['complete'], pid, d) for pid, d in gs.items() if d['complete']), key=lambda x: (x[0][0], x[0][1]))
    import observer_data as OD
    now = lambda pid: OD.playing_status((w.person(pid) or {}).get('golfer'))[0]
    rows = []
    for (y, eid), pid, d in done:
        born = (w.person(pid) or {}).get('born')
        partial = w.a and pid in w.a.people and w.a.people[pid].get('initial')
        rows.append([w.person_link(pid), now(pid), O.event_link(w, eid), O.age_text(w, born, y),
                     ', '.join(O.event_link(w, e) for _, e in sorted(d['firsts'].values()))
                     + (' <span class="tag">partial: majors before the archive unknown</span>' if partial else '')])
    three = sorted(((len(d['firsts']), pid, d) for pid, d in gs.items() if len(d['firsts']) == 3), key=lambda x: x[1])
    body = (O.table(['Golfer', 'Now', 'Completed at', 'Age*', 'First win of each major'], rows, numeric=(3,)) if rows
            else '<p class="muted">Nobody has won all four majors yet.</p>')
    body += '<h2>One major short</h2>' + (O.table(['Golfer', 'Now', 'Missing'], [
        [w.person_link(pid), now(pid), O.esc(', '.join(w.series_name(s) for s in MAJOR_SERIES if s not in d['firsts']))]
        for _, pid, d in three]) if three else '<p class="muted">Nobody.</p>')
    return 'Career Grand Slam', ('<p>Winners of all four majors (Tour Masters, Premier Tour Championship, USA Open, '
                                 'Britannia Open): completed by the first win of the fourth different major. Observed '
                                 'completion: careers that began before the archive may have earlier majors it does not '
                                 f'hold. The current season counts as played.</p>{body}<p class="muted">* {O.AGE_NOTE}</p>')


# ---- the year-end recap -----------------------------------------------------------------------------------------
def recap(w, y):
    """A season's story from its facts: majors with their teams, the year's leading winners and money, world
    No. 1s, Premier cards earned, career changes, Grand Slams completed, records and moments -- each linked."""
    O = _o()
    a = w.a
    idx = a.index
    out = [f'<p>{rules_note(w, y)} <a href="/seasons">All seasons</a></p>']
    facts = a.recap(y)
    majors = [f for f in facts if f.get('fact') == 'major']
    if majors:
        out.append('<h2>Majors</h2>' + O.table(['Major', 'Champion', 'Coach', 'Caddie'], [
            [O.event_link(w, f['event']), w.person_link(f['golfer']), w.person_link(f.get('coach')),
             w.person_link(f.get('caddie'))] for f in majors]))
    others = [f for f in facts if f.get('fact') not in ('major', 'number one', 'counts')]
    if others:
        out.append('<h2>Notable career moves</h2><ul>' + ''.join(
            f'<li>{O.esc(f["text"])}' + (f' (<a href="/golfer/{f["golfer"]}">profile</a>)' if f.get('golfer') else '')
            + '</li>' for f in others) + '</ul>')
    if idx is not None:
        top = list(idx.db.execute('SELECT s.person, COUNT(*) FROM starts s JOIN editions e USING(eid) WHERE e.year = ? '
                                  'AND s.pos = 1 AND e.tier BETWEEN 0 AND 4 GROUP BY s.person ORDER BY 2 DESC, s.person '
                                  'LIMIT 8', (y,)))
        if top:
            out.append('<h2>Most professional wins</h2>' + O.table(['Golfer', 'Wins'], [
                [w.person_link(g), O.results_link(g, str(n), year=y, outcome='win')] for g, n in top], numeric=(1,)))
        money_ = list(idx.db.execute('SELECT person, prize, tour FROM seasons WHERE year = ? ORDER BY prize DESC, person '
                                     'LIMIT 10', (y,)))
        if money_:
            out.append('<h2>Prize money leaders</h2>' + O.table(['Golfer', 'Tour (membership)', 'Prize money'], [
                [w.person_link(g), O.tour_link(w, t), O.money(p)] for g, p, t in money_], numeric=(2,))
                + f'<p class="muted">Gross tournament prize money for the season; <a href="/money?year={y}">full list</a>.</p>')
        no1, new = [], []
        if _has_table(idx, 'number_one'):
            no1 = [r[0] for r in idx.db.execute("SELECT DISTINCT person FROM number_one WHERE kind = 'world' AND year = ?",
                                                (y,))]
            new = [g for g in no1 if not idx.db.execute("SELECT 1 FROM number_one WHERE kind = 'world' AND person = ? "
                                                        "AND year < ?", (g, y)).fetchone()]
        end = a.ranking(y, 52)[:1]
        if end or no1:
            out.append('<h2>World No. 1</h2><p>' + (f'At the end of the season: {w.person_link(end[0])}. ' if end else '')
                       + (f'No. 1 for the first time: {", ".join(w.person_link(g) for g in new)}.' if new else '') + '</p>')
    d = _season_file(w, y) or {}
    careers = {int(k): v for k, v in d.get('careers', {}).items()}
    earned = [(g, r) for g, r in careers.items() if (r.get('card_reason') or '').startswith('Premier card earned')
              and not (r.get('tour') or '').startswith('PT_')]
    promoted = [(g, r) for g, r in careers.items() if (r.get('next_tour') or '').startswith('PT_')
                and not (r.get('tour') or '').startswith('PT_')]
    if promoted:
        out.append(f'<h2>Premier cards for {y + 1}</h2><p>{len(promoted)} golfers move up to the Premier Tour'
                   + (f', {len(earned)} of them non-members who earned a card by winning or with Premier money' if earned else '')
                   + '.</p>' + (O.table(['Golfer', 'From', 'Why'], [
                       [w.person_link(g), O.tour_link(w, r.get('tour')), O.esc(r.get('card_reason'))] for g, r in earned])
                       if earned else ''))
    trans = d.get('transitions', [])
    if trans:
        kinds = Counter(t.get('kind') for t in trans)
        majors_won = {g for _, _, _, _, g in major_wins(w)}
        notable = [t for t in trans if t.get('gid') in majors_won and t.get('kind') not in ('turned pro',)]
        out.append('<h2>Career changes that winter</h2><p>' + ', '.join(f'{O.esc(k)}: {n}' for k, n in kinds.most_common())
                   + '</p>' + (('<p>Major champions among them:</p><ul>' + ''.join(
                       f'<li>{w.person_link(t["gid"])} — {decision_text(t)}</li>' for t in notable) + '</ul>') if notable else ''))
    slams = [(pid, dd['complete']) for pid, dd in grand_slams(w).items() if dd['complete'] and dd['complete'][0] == y]
    if slams:
        out.append('<h2>Career Grand Slams completed</h2><ul>' + ''.join(
            f'<li>{w.person_link(pid)} at the {O.event_link(w, eid)}</li>' for pid, (_, eid) in slams) + '</ul>')
    if idx is not None:
        ms = a.moments(year=y)
        kinds = Counter(m['kind'] for m in ms)
        crs = [m for m in ms if m['kind'] == 'course record']
        if ms:
            out.append('<h2>Moments</h2><p>' + ', '.join(f'{O.esc(k)}: {n}' for k, n in kinds.most_common())
                       + f' · <a href="/moments">all moments</a></p>' + (O.table(['Course record', 'Golfer', 'Event', 'Venue'], [
                           [O.esc(f'{m.get("score")} ({m.get("to_par"):+d})' if m.get('to_par') is not None else m.get('score')),
                            w.person_link(m['person']), O.event_link(w, m['event']), O.venue_link(w, m.get('layout'))]
                           for m in crs[:10]]) if crs else ''))
    top = a.ranking(y, 52)[:10]
    if top:
        out.append('<h2>World ranking at the end of the season</h2>' + O.table(['#', 'Golfer'], [
            [str(i), w.person_link(g)] for i, g in enumerate(top, 1)], numeric=(0,)))
    return ''.join(out)


# ---- sortable tables ----------------------------------------------------------------------------------------------
from observer_views import SORT_JS                      # noqa: E402  (the sort script now lives with the saved views)
