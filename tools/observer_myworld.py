"""My World: the shortlist in groups, and a digest of what the history recorded for what you follow.

Everything shortlisted is followed: people, tournaments, editions, courses, nations and tours, each in a group
you name ("Prospects", "Rivals", ...; ungrouped by default). The digest lists only recorded facts, plainly
worded, since you last marked it read (or over a window you choose):

* a followed person's wins (any event), top-10 finishes in majors and Premier events, missed cuts in majors,
  season-end changes of tour or status (from the archived seasons; the current season's status against the last
  archived one), recorded moments (course records and the like), and a change of world-ranking band (No. 1, top
  10, top 50, top 100) between the start of the window and now;
* a followed tournament's or tour's editions played (with their winners); a course's editions and course records
  set there; a nation's golfers' wins in majors and Premier events; a followed edition once played.

Every recorded result is included. Earlier builds had a "Hide results" setting that held back items naming a
hidden result; if this world used it, items dated after the hiding began and before the digest was last marked
read may never have been shown: a one-line notice offers that period to review (the read marker is not moved,
and nothing is shown twice in the unread count). There are no pop-ups or banners: the menu shows a quiet count
of new items. Nothing here is simulation state: the groups and the "read up to" week live in the shortlist file.
"""
from __future__ import annotations

from collections import defaultdict
from urllib.parse import quote

import observer_stories as STORY

BANDS = ((1, 'No. 1'), (10, 'the top 10'), (50, 'the top 50'), (100, 'the top 100'))
WINDOWS = {'new': 'since last read', '4': 'the last 4 weeks', '13': 'the last 13 weeks', 'season': 'this season',
           '52': 'the last 52 weeks'}
LIMIT = 300                                          # the digest's most recent items (the rest counted)


def _o():
    import observer as O
    return O


def now(w):
    """(year, week) of the latest week played (the snapshot's), or the history's last season end."""
    if w.live is not None:
        c = w.live.cursor
        return (c['year'], c['week'] - 1) if c['week'] > 1 else (c['year'] - 1, 52)
    return (w.a.years[-1], 52) if w.a else (0, 0)


def _yw(text):
    """'2030.17' -> (2030, 17), or None."""
    try:
        y, wk = (int(x) for x in str(text).split('.'))
        return (y, wk)
    except (TypeError, ValueError):
        return None


def window_start(w, q, seen):
    """(year, week) after which items count, and the window's label."""
    O = _o()
    win = O.one(q, 'since', 'new') or 'new'
    y, wk = now(w)
    if _yw(win):
        return _yw(win), 'the period chosen', win
    if win == 'season':
        return (y, 0), WINDOWS[win], win
    if win.isdigit():
        n = int(win)
        k = y * 52 + wk - n
        return (k // 52, k % 52), WINDOWS.get(win, f'the last {n} weeks'), win
    if seen:
        return tuple(seen), WINDOWS['new'], 'new'
    return (y, 0), 'this season (nothing marked read yet)', 'new'


def _after(start, year, week):
    return (year, week or 0) > tuple(start)


def _ed_info(w, eid, cache):
    if eid not in cache:
        e = w.edition(eid) or {}
        cache[eid] = {'tier': e.get('tier'), 'category': e.get('category'), 'week': e.get('week'),
                      'series': e.get('series'), 'tour': e.get('tour')}
    return cache[eid]


def digest(w, items, start, until=None):
    """[(year, week, kind, html)]: recorded facts for the followed items after `start` (and up to `until`, when
    given), newest first."""
    O = _o()
    out, cache = [], {}

    def add(y, wk, kind, html, eid=None):
        if until is None or (y, wk or 0) <= tuple(until):
            out.append((y, wk or 0, kind, html))
    by = defaultdict(list)
    for kind, ident, *_ in items:
        by[kind].append(ident)
    major = lambda info: info['category'] == 'major' or info['tour'] == 'MAJORS'
    for pid in map(int, by.get('person', ())):
        link = w.person_link(pid)
        for r in w.results(pid):
            if not _after(start, r['year'], r['week']):
                continue
            info = _ed_info(w, r['event'], cache)
            ev = O.event_link(w, r['event'])
            story = ''
            if STORY.notable({**info, 'pos': r['pos']}):  # a notable performance: its story, from their side
                story = (f' · <a href="{O.esc(STORY.story_href(r["event"], None if r["pos"] == 1 else pid))}">'
                         'story</a>')
            if r['pos'] == 1 and info['category'] not in ('qualifier', 'q_school'):
                add(r['year'], r['week'], 'win', f'{link} won the {ev}{story}', r['event'])
            elif r['pos'] is not None and r['pos'] <= 10 and (major(info) or info['tier'] == 1):
                add(r['year'], r['week'], 'top10', f'{link} finished {r["pos"]} at the {ev}{story}', r['event'])
            elif r['pos'] is None and major(info):
                add(r['year'], r['week'], 'cut', f'{link} missed the cut at the {ev}', r['event'])
        _status_changes(w, pid, start, add)
        if w.a and w.a.index is not None:
            for m in w.a.index.moments(person=pid):
                if _after(start, m['year'], m['week']):
                    add(m['year'], m['week'], 'moment', f'{link}: {O.esc(m["kind"])} at the {O.event_link(w, m["event"])}'
                        if m.get('event') else f'{link}: {O.esc(m["kind"])}', m.get('event'))
        _ranking_band(w, pid, start, add, until)
    for sid in by.get('series', ()):
        for e in w.editions_of(sid):
            if _after(start, e['year'], e['week']):
                add(e['year'], e['week'], 'edition', f'{O.event_link(w, e["event"])}: won by {w.person_link(e["winner"])}',
                    e['event'])
    for key in by.get('tour', ()):
        for y, wk, eid, win in _tour_editions(w, key, start):
            add(y, wk, 'edition', f'{O.event_link(w, eid)} ({O.esc(w.tours().get(key, {}).get("name", key))}): won by '
                f'{w.person_link(win)}', eid)
    for cid in by.get('course', ()):
        for e in w.course_editions(cid):
            y = e.get('year')
            wk = e.get('week') or _ed_info(w, e['event'], cache)['week']
            if y is not None and _after(start, y, wk):
                add(y, wk, 'edition', f'{O.event_link(w, e["event"])} at {O.course_link(w, cid)}: won by '
                    f'{w.person_link(e.get("winner"))}', e['event'])
        if w.a and w.a.index is not None:
            for m in w.a.index.moments(kind='course record'):
                if _after(start, m['year'], m['week']) and str(m.get('layout') or '').startswith(f'{cid}:'):
                    add(m['year'], m['week'], 'moment', f'Course record at {O.course_link(w, cid)}: '
                        f'{w.person_link(m["person"])}' + (f' ({O.esc(m["score"])})' if m.get('score') else ''),
                        m.get('event'))
    for code in by.get('nation', ()):
        for y, wk, eid, win in _nation_wins(w, code, start):
            add(y, wk, 'win', f'{w.person_link(win)} ({O.esc(code)}) won the {O.event_link(w, eid)}', eid)
    for eid in by.get('edition', ()):
        e = w.edition(eid)
        if e is not None and _after(start, e['year'], e.get('week')):
            win = next((r['person'] for r in e['rows'] if r['pos'] == 1), None)
            add(e['year'], e.get('week'), 'edition', f'{O.event_link(w, eid)} was played: won by {w.person_link(win)}', eid)
    seen, uniq = set(), []
    for x in sorted(out, key=lambda x: (x[0], x[1]), reverse=True):
        if x[3] not in seen:
            seen.add(x[3])
            uniq.append(x)
    return uniq


def _status_changes(w, pid, start, add):
    """Season-end changes of tour or status (archived seasons), and the current season's against the last one."""
    O = _o()
    rows = w.a.index.seasons(pid) if (w.a and w.a.index is not None) else []
    tours = w.tours()
    name = lambda t: tours.get(t, {}).get('name', t or 'no tour')
    def say(a, b):
        if (a.get('lifestyle') != 'retired') and b.get('lifestyle') == 'retired':
            return 'retired'
        if a.get('status') != b.get('status'):
            return f'{a.get("status")} → {b.get("status")}' + (f' ({name(b.get("tour"))})' if b.get('tour') else '')
        if a.get('tour') != b.get('tour'):
            return f'{name(a.get("tour"))} → {name(b.get("tour"))}'
        return None
    for a, b in zip(rows, rows[1:]):
        if _after(start, b['year'], 1) and (s := say(a, b)):
            add(b['year'], 1, 'status', f'{w.person_link(pid)}: {O.esc(s)} (season {b["year"]})')
    if not rows:
        return
    live = w.live.people.get(pid) if w.live else None
    last = rows[-1]                                    # (a season row: their status before that winter)
    now_ = live or ((w.person(pid) or {}).get('golfer'))
    if now_ and now_.get('lifestyle') == 'retired' and last.get('lifestyle') != 'retired':
        y = last['year'] + 1                           # one dated event: retired in the winter after their last
        if _after(start, y, 1):                        # season, whenever (and however often) it is read
            add(y, 1, 'status', f'{w.person_link(pid)}: retired after the {last["year"]} season')
        return
    if live and w.live.cursor['year'] > last['year'] and _after(start, w.live.cursor['year'], 1):
        if s := say(last, live):
            add(w.live.cursor['year'], 1, 'status', f'{w.person_link(pid)}: {O.esc(s)} (season {w.live.cursor["year"]})')


def _ranking_week(w, y, wk):
    """[pid, ...] in rank order: the world ranking published after week `wk` of season `y` (week 0: the end of the
    season before), from the current season's weekly snapshots or the archived season; None if none was recorded
    for that week (never another week's ranking in its place)."""
    if wk <= 0:
        y, wk = y - 1, 52
    if w.live is not None and y == w.live.cursor['year'] and not (w.a and y in w.a.years):
        top = getattr(w.live, 'rank_top', None) or {}
        rows = top.get(wk) or top.get(str(wk))
        if rows:
            return [r[0] for r in rows]
        if (y, wk) == now(w):                          # (the latest week's ranking is the live table itself)
            return sorted(w.live.wr, key=w.live.wr.get)
        return None
    if w.a and y in w.a.years:
        import observer_golf as OG
        got = OG._rankings(w, y) or {}
        snap = (got.get('ranking_points') or {}).get(str(wk))   # (top 200, in rank order)
        if snap:
            return [r[0] for r in snap]
        order = (got.get('rankings') or {}).get('world', {}).get(str(wk))   # (top 100: older seasons)
        return list(order) if order else None
    return None


def _rank_at(w, y, wk, pid):
    """(known, rank or None): a golfer's place in the ranking published after that week -- (True, None) when the
    ranking is recorded and they are not in it, (False, None) when no ranking was recorded for that week."""
    lst = _ranking_week(w, y, wk)
    if lst is None:
        return False, None
    return True, (lst.index(pid) + 1 if pid in lst else None)


def _band(r):
    return next((i for i, (n, _) in enumerate(BANDS) if r is not None and r <= n), len(BANDS))


def _ranking_band(w, pid, start, add, until=None):
    """A change of world-ranking band between the start of the window and its end (now, or `until`), each from the
    ranking published that week (bands: No. 1, top 10, 50, 100); nothing when either week's ranking was not
    recorded."""
    y, wk = min(tuple(until), now(w)) if until else now(w)
    (ka, a), (kb, b) = _rank_at(w, start[0], start[1], pid), _rank_at(w, y, wk, pid)
    if not (ka and kb):
        return
    ba, bb = _band(a), _band(b)
    if ba == bb or (y, wk) <= tuple(start):
        return
    if bb < ba:
        add(y, wk, 'ranking', f'{w.person_link(pid)} is now world No. 1' if bb == 0 else
            f'{w.person_link(pid)} is now in {BANDS[bb][1]} of the world ranking (No. {b})')
    else:
        add(y, wk, 'ranking', (f'{w.person_link(pid)} is no longer world No. 1' if ba == 0 else
                               f'{w.person_link(pid)} dropped out of {BANDS[ba][1]} of the world ranking')
            + (f' (now No. {b})' if b else ' (now outside the top 100)'))


def _tour_editions(w, key, start):
    out = []
    if w.a and w.a.index is not None:
        idx = w.a.index
        out += [tuple(r) for r in idx.db.execute(
            'SELECT year, week, event_id, winner FROM editions WHERE tour = ? AND (year > ? OR (year = ? AND week > ?))'
            + idx.upto(), (key, start[0], start[0], start[1]))]
    if w.live is not None:
        for e in w.live.editions.values():
            if e.get('tour') == key and _after(start, int(e['id'].split(':')[0]), e['week']):
                win = next((g for g, p, _ in (e['finish'][0] if e['finish'] else []) if p == 1), None)
                out.append((int(e['id'].split(':')[0]), e['week'], e['id'], win))
    return out


def _nation_wins(w, code, start):
    """Wins by the nation's golfers in majors and Premier events after `start`."""
    out = []
    country = lambda pid: (w.person(pid) or {}).get('country')
    if w.a and w.a.index is not None:
        idx = w.a.index
        for y, wk, eid, win in idx.db.execute(
                "SELECT year, week, event_id, winner FROM editions WHERE (tier <= 1 OR category = 'major') AND "
                '(year > ? OR (year = ? AND week > ?))' + idx.upto(), (start[0], start[0], start[1])):
            if win and country(win) == code:
                out.append((y, wk, eid, win))
    if w.live is not None:
        for e in w.live.editions.values():
            if ((e.get('tier') or 9) <= 1 or e.get('category') == 'major') and _after(start, int(e['id'].split(':')[0]), e['week']):
                win = next((g for g, p, _ in (e['finish'][0] if e['finish'] else []) if p == 1), None)
                if win and country(win) == code:
                    out.append((int(e['id'].split(':')[0]), e['week'], e['id'], win))
    return out


OLD_SPOILERS = 'observer_spoilers.json'          # (the removed Hide results setting, from earlier builds)


def hidden_period(w, seen):
    """((year, week), (year, week)) when the digest may have been marked read while the removed Hide results setting
    held items back: from when hiding began (the old setting's boundary) to the read marker. None when the world
    never used it, the digest was never marked read inside that period, or the notice was dismissed. The old setting
    is only read, never applied."""
    import json
    O = _o()
    if w is None or w.read_only or not seen:
        return None
    try:
        old = json.loads((w.path / OLD_SPOILERS).read_text())
    except (OSError, ValueError):
        return None
    try:                                               # (a file it cannot read as a date is ignored)
        since = tuple(int(x) for x in old['from'])
    except (TypeError, ValueError, KeyError):
        return None
    if len(since) != 2 or O.shortlist_flags(w).get('hidden_period_dismissed'):
        return None
    start = since if since != (0, 0) else ((min(w.a.years) if w.a else now(w)[0]), 0)
    if tuple(seen) <= start:
        return None
    return start, tuple(seen)


def _hidden_period_notice(w, seen):
    O = _o()
    got = hidden_period(w, seen)
    if got is None:
        return ''
    (a, b), (c, d) = got
    return (f'<p class="notice">An earlier version could hide results, and this world used it: items from {a} week {b} '
            f'to {c} week {d} (when you last marked this digest read) may not have been shown. '
            f'<a href="/my-world?since={a}.{b}&amp;until={c}.{d}">Review that period</a> '
            '<form method="post" action="/my-world/dismiss" class="inline"><button>Dismiss</button></form></p>')


def new_count(w):
    """How many digest items are new since last read (for the menu; 0 when nothing is followed)."""
    O = _o()
    items = O.shortlist(w)
    if not items:
        return 0
    seen = O.shortlist_seen(w)
    try:
        got = digest(w, items, tuple(seen) if seen else (now(w)[0], 0))
    except Exception:                                    # (a count only: never stop a page over it)
        return 0
    return len(got)


def page(w, q):
    O = _o()
    if w.read_only:
        return 'My World', '<p class="muted">Open the world (not only its history) to follow people and events.</p>'
    items = O.shortlist(w)
    groups = defaultdict(list)
    for kind, ident, added, group in items:
        groups[group or ''].append((kind, ident, added))
    seen = O.shortlist_seen(w)
    start, label, win = window_start(w, q, seen)
    out = []
    if not items:
        return 'My World', ('<p class="muted">Nothing followed yet: use ☆ Shortlist on a person, course, nation, tour, '
                            'tournament or edition. Everything shortlisted is followed here.</p>')
    until = _yw(O.one(q, 'until'))
    got = digest(w, items, start, until)
    y, wk = now(w)
    if until:
        y, wk = until
    tabs = '<div class="tabs">' + ''.join(
        f'<a href="/my-world?since={k}" class="{"on" if k == win else ""}">{O.esc(v)}</a>' for k, v in WINDOWS.items()) + '</div>'
    mark = ('<form method="post" action="/my-world/read" class="inline"><button>Mark all as read</button></form>'
            if got and win == 'new' else '')
    out.append('<h2>Digest</h2>' + _hidden_period_notice(w, seen) + tabs + f'<p>{len(got):,} recorded item{"s" if len(got) != 1 else ""} {O.esc(label)} '
               f'(after {start[0]} week {start[1]}; up to {y} week {wk}){mark}</p>')
    if got:
        out.append(O.table(['Season', 'Week', 'What'], [[str(a), str(b) if b else '—', h] for a, b, _, h in got[:LIMIT]],
                           numeric=(0, 1))
                   + (f'<p class="muted">{len(got) - LIMIT:,} older items not shown: choose a shorter window.</p>'
                      if len(got) > LIMIT else ''))
    else:
        out.append('<p class="muted">Nothing recorded for what you follow in this window.</p>')
    out.append('<h2>What you follow</h2>' + _groups_html(w, groups))
    return 'My World', ''.join(out) + (
        '<p class="muted">Only recorded facts: wins; top-10s in majors and Premier events; missed cuts in majors; '
        'season-end changes of tour or status; recorded moments; world-ranking band changes (No. 1, top 10, 50, '
        '100); followed tournaments’, tours’ and courses’ editions; a nation’s wins in majors and Premier events. '
        'Kept with this world in the shortlist file; never read by the simulation.</p>')


def _groups_html(w, groups):
    """Each group (ungrouped last), its items by type, each with where it stands now and a control to move it."""
    O = _o()
    names = sorted(groups, key=lambda g: (g == '', g.lower()))
    known = [g for g in names if g]
    out = []
    for g in names:
        parts = []
        for kind, (label, _) in O.SHORT_TYPES.items():
            rows = [[_name(w, k, i), _line(w, k, i), O.esc(added), _group_form(k, i, g, known) + O.shortlist_button(w, k, i)]
                    for k, i, added in sorted(groups[g], key=lambda x: str(x[1])) if k == kind]
            if rows:
                parts.append(f'<h4>{O.esc(label)}</h4>' + O.table(['', 'Now', 'Added', ''], rows))
        out.append(f'<h3>{O.esc(g) if g else "Ungrouped"} ({len(groups[g])})</h3>' + ''.join(parts))
    return ''.join(out)


def _group_form(kind, ident, group, known):
    from html import escape as esc
    opts = ''.join(f'<option value="{esc(g)}">' for g in known)
    return (f'<form method="post" action="/shortlist/group" class="inline"><input type="hidden" name="kind" '
            f'value="{esc(kind)}"><input type="hidden" name="id" value="{esc(str(ident))}"><input name="group" '
            f'value="{esc(group)}" list="groups-{esc(kind)}-{esc(str(ident))}" placeholder="group" aria-label="Group" '
            f'size="10"><datalist id="groups-{esc(kind)}-{esc(str(ident))}">{opts}</datalist><button>Move</button></form>')


def _name(w, kind, i):
    O = _o()
    if kind == 'person':
        return w.person_link(int(i))
    if kind == 'course':
        return O.course_link(w, i)
    if kind == 'nation':
        return O.nation_link(i)
    if kind == 'tour':
        return O.tour_link(w, i)
    if kind == 'series':
        return f'<a href="/series/{quote(i)}">{O.esc(w.series_name(i))}</a>'
    return O.event_link(w, i)


def _line(w, kind, i):
    """One line on where a followed item stands now (recorded facts only)."""
    O = _o()
    if kind == 'person':
        p = w.person(int(i)) or {}
        g = p.get('golfer') or {}
        bits = []
        if g:
            if g.get('lifestyle') == 'retired':
                bits.append('retired')
            else:
                bits.append(f'{g.get("status") or ""} · {w.tours().get(g.get("tour"), {}).get("name", g.get("tour") or "no tour")}')
        r = w.live.wr.get(int(i)) if w.live else None
        if r:
            bits.append(f'world No. {r}')
        roles = [x for x in p.get('roles', []) if x != 'golfer']
        if roles:
            bits.append(', '.join(roles))
        return O.esc(' · '.join(bits))
    if kind == 'edition':
        e = w.edition(i)
        if e is None:
            return '<span class="muted">not played yet</span>'
        return O.esc(f'played (week {e.get("week")})')
    if kind == 'series':
        eds = w.editions_of(i)
        return O.esc(f'{len(eds)} editions recorded' + (f', latest {eds[-1]["year"]}' if eds else ''))
    return ''
