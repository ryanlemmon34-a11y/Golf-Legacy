"""Hide results: browsing a world without spoilers (roadmap v14, spoiler-safe entry).

With "Hide results" on, every edition played from a chosen boundary (this season, from now on, or every
edition) is hidden until it is revealed: lists show it without its winner, its event page opens on the
round-by-round replay at round one (or the round last watched), the final round shows the leaderboard after
regulation without who won a playoff, and the final result, statistics and winner appear only after an
explicit "Reveal final result". The state (on or off, the boundary, and each edition's watched round or reveal)
is kept with the world (observer_spoilers.json beside the shortlist; a temporary file for a history browsed
read-only), so it is the same on every page and after a restart.

Nothing here touches the simulation: a replay reads the recorded rounds; it never plays, draws or changes
anything. Pages that add results up (statistics, rankings, records, career totals) still count every result:
they say so while results are hidden rather than leaving anything out silently.
"""
from __future__ import annotations

import json
import os
from html import escape as esc
from pathlib import Path
from urllib.parse import quote

FILE = 'observer_spoilers.json'
FORMAT = 'golf-legacy-spoilers/1'
BOUNDARIES = {'season': 'this season’s results', 'now': 'results from now on', 'all': 'every result'}


def _path(w):
    if not w.read_only:
        return Path(w.path) / FILE
    import hashlib
    import tempfile
    h = hashlib.sha1(str(Path(w.archive_dir).resolve()).encode()).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / 'golf-legacy-observer' / f'{h}.spoilers.json'


def state(w):
    """{'hide': bool, 'from': [year, week] or None, 'revealed': {event id: watched round (int) or 'final'}}."""
    if w is None:
        return {'hide': False, 'from': None, 'revealed': {}}
    st = w.__dict__.get('_spoilers')
    if st is None:
        try:
            st = json.loads(_path(w).read_text())
            st = {'hide': bool(st.get('hide')), 'from': st.get('from'), 'revealed': dict(st.get('revealed') or {})}
        except (OSError, ValueError, AttributeError):
            st = {'hide': False, 'from': None, 'revealed': {}}
        w._spoilers = st
    return st


def _save(w, st):
    p = _path(w)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.tmp')
    tmp.write_text(json.dumps({'format': FORMAT, **st}, indent=1))
    os.replace(tmp, p)
    w._spoilers = st


def set_hide(w, on, boundary='season'):
    """Turn hiding on (from `boundary`: 'season', 'now' or 'all') or off. Turning it off keeps what was watched."""
    if w is None:
        return False
    st = dict(state(w))
    if on:
        cur = w.live.cursor if w.live else None          # (the week about to be played)
        year = cur['year'] if cur else (w.a.years[-1] if w.a else 0)   # (a history only: its latest season)
        if boundary == 'all':
            st['from'] = [0, 0]
        elif boundary == 'now':
            st['from'] = [cur['year'], cur['week']] if cur else [year + 1, 1]
        else:
            st['from'] = [year, 1]
    st['hide'] = bool(on)
    _save(w, st)
    return True


def _week(w, eid):
    e = w.edition(eid)
    return e['week'] if e else 53


def hidden(w, eid, week=None):
    """Whether an edition's outcome is hidden now (hiding on, played at or after the boundary, not revealed)."""
    st = state(w)
    if not st['hide'] or st['revealed'].get(eid) == 'final':
        return False
    by, bw = st['from'] or (0, 0)
    year = int(eid.split(':')[0])
    if year != by:
        return year > by
    return (week if week is not None else _week(w, eid)) >= bw


def watched(w, eid):
    """The last round watched in the replay (0 if none), or 'final' once revealed."""
    return state(w)['revealed'].get(eid, 0)


def note_round(w, eid, k):
    """The replay reached round k (kept only while hiding is on, and only forward)."""
    st = state(w)
    if not st['hide']:
        return
    was = st['revealed'].get(eid, 0)
    if was == 'final' or (isinstance(was, int) and was >= k):
        return
    st = {**st, 'revealed': {**st['revealed'], eid: k}}
    _save(w, st)


def reveal(w, eid):
    st = state(w)
    _save(w, {**st, 'revealed': {**st['revealed'], eid: 'final'}})


def watch_link(w, eid, label=None):
    """Resume: the replay at the round last watched (round one if none)."""
    k = watched(w, eid)
    r = k if isinstance(k, int) and k > 0 else 1
    text = label or ('Watch' if r == 1 else f'Resume at round {r}')
    return f'<a href="/event/{quote(eid)}?view=rounds&amp;round={r}">{esc(text)}</a>'


def restart_link(w, eid, label='Watch from round 1'):
    """Restart: the replay at round one, whatever was watched before (what was watched stays remembered, so
    Resume still returns to it; going back reveals nothing)."""
    return f'<a href="/event/{quote(eid)}?view=rounds&amp;round=1">{esc(label)}</a>'


def mask(w, eid, week, html):
    """`html` (a winner, a place, a result) unless the edition is hidden: then a hidden marker and a watch link."""
    if not hidden(w, eid, week):
        return html
    return f'<span class="muted">hidden</span> · {watch_link(w, eid)}'


def unrevealed(w):
    """How many played editions are hidden now (the current season's, and archived ones if the boundary is earlier)."""
    st = state(w)
    if not st['hide']:
        return 0
    n = 0
    if w.live:
        n += sum(1 for e in w.live.editions.values() if hidden(w, e['id'], e['week']))
    if w.a and w.a.index is not None and st['from'] and st['from'][0] <= w.a.years[-1]:
        by, bw = st['from']
        for eid, y, wk in w.a.index.db.execute('SELECT event_id, year, week FROM editions WHERE year >= ?'
                                              + w.a.index.upto(), (by,)):
            n += hidden(w, eid, wk)
    return n


def header(w):
    """The header control: Hide results (with its boundary) or, while hiding, what is hidden and Show results."""
    if w is None:
        return ''
    st = state(w)
    if st['hide']:
        by, bw = st['from'] or (0, 0)
        since = 'every edition' if by == 0 else f'{by} week {bw} on'
        return ('<form method="post" action="/spoilers" class="inline spoilers"><span class="tag">Results hidden</span> '
                f'<span class="muted">{esc(since)} · {unrevealed(w)} unrevealed</span>'
                '<input type="hidden" name="hide" value="0"><button title="Show every result again (what you watched '
                'is kept)">Show results</button></form>')
    opts = ''.join(f'<option value="{k}">{esc(v)}</option>' for k, v in BOUNDARIES.items())
    return ('<form method="post" action="/spoilers" class="inline spoilers"><input type="hidden" name="hide" value="1">'
            f'<select name="from" aria-label="Which results to hide">{opts}</select>'
            '<button title="Hide winners and final results until you reveal them">Hide results</button></form>')


def hidden_wins(w, pid):
    """[(year, tournament name)] of a golfer's wins whose results are hidden now."""
    if not state(w)['hide'] or w is None:
        return []
    import observer_data as OD
    return [(r['year'], w.series_name(r['series'])) for r in OD.results(w, pid)
            if r.get('pos') == 1 and hidden(w, r['event'], r['week'])]


def redact(w, pid, text, wins=None):
    """`text` (a status line, a card reason, a decision) unless it names one of the golfer's hidden wins ("won the
    2030 Texas Open"): then 'hidden'."""
    for year, name in (hidden_wins(w, pid) if wins is None else wins):
        if text and f'{year} {name}' in str(text):
            return '<span class="muted">hidden (names a result you have not revealed)</span>'
    return text


def aggregate_note(w, what='These figures'):
    """A note for pages that add results up, while results are hidden."""
    n = unrevealed(w)
    if not n:
        return ''
    return (f'<div class="banner warn" role="status">Results are hidden ({n} unrevealed edition'
            f'{"" if n == 1 else "s"}), but {esc(what)} count every result played, hidden ones included: '
            'they can give results away. Calendar, events, tournament and course lists keep them hidden.</div>')


def reveal_button(eid, label='Reveal final result'):
    return (f'<form method="post" action="/spoilers" class="inline"><input type="hidden" name="reveal" '
            f'value="{esc(eid)}"><button>{esc(label)}</button></form>')
