"""Saved table views and navigation state (roadmap v14, browsing).

A list page's view is its address: season, scope (tour), filters, sort column and direction, page, and the
column a table was sorted by in the browser (``tsort``). The observer remembers, per world:

* the **last view** of every list page: opening that page again from the menu (no address of its own) shows
  the view left, with a one-click way back to the default;
* the **trail**: the last list view opened, so a profile or event page opened from it offers "Back to" that
  exact view (any number of pages later);
* **saved views**: named views, kept until removed, listed on their page and on the Saved views page.

All of it is browsing state only: a file beside the world (``observer_views.json``, like the shortlist; a
temporary file for a history browsed read-only). The simulation never reads it, and nothing here changes a
result or the world (a saved view is only an address).
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from html import escape as esc
from pathlib import Path
from urllib.parse import parse_qs, quote, urlencode

FILE = 'observer_views.json'
FORMAT = 'golf-legacy-views/1'
MAX_SAVED = 200

# list pages whose view is remembered (exact paths) and list pages under a prefix (each remembered by its path)
LISTS = {'/rankings': 'World ranking', '/golfers': 'Golfers', '/coaches': 'Coaches', '/caddies': 'Caddies',
         '/records': 'Records', '/moments': 'Moments', '/tournaments': 'Tournaments', '/calendar': 'Calendar',
         '/courses': 'Courses', '/nations': 'Nations', '/tours': 'Tours', '/seasons': 'Seasons', '/stats': 'Stats',
         '/money': 'Prize money', '/grand-slam': 'Career Grand Slam', '/cohort': 'Where are they now',
         '/goat': 'GOAT Lab', '/compare': 'Compare careers'}
PREFIXES = {'/records/': 'Record', '/golf-records/': 'Golf record'}
TRANSIENT = ('default',)                     # never part of a view
LABELS = {'year': 'season', 'tour': 'tour', 'q': 'search', 'sort': 'sorted by', 'page': 'page', 'show': 'showing',
          'min': 'minimum rounds', 'nation': 'nation', 'status': 'status', 'role': 'role', 'kind': 'kind',
          'rounds': 'rounds', 'field': 'field', 'decade': 'decade'}


def is_list(path):
    return path in LISTS or any(path.startswith(p) and len(path) > len(p) for p in PREFIXES)


def page_name(path):
    if path in LISTS:
        return LISTS[path]
    for p, label in PREFIXES.items():
        if path.startswith(p):
            return f'{label}: {path[len(p):].replace("-", " ")}'
    return path


def canonical(q):
    """The view part of a query ({key: [values]} or {key: value}) as a stable query string."""
    items = []
    for k, v in sorted((q or {}).items()):
        v = v[0] if isinstance(v, (list, tuple)) else v
        if k in TRANSIENT or v in (None, ''):
            continue
        items.append((k, str(v)))
    return urlencode(items)


def _path(w):
    if not w.read_only:
        return Path(w.path) / FILE
    h = hashlib.sha1(str(Path(w.archive_dir).resolve()).encode()).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / 'golf-legacy-observer' / f'{h}.views.json'


def state(w):
    """{'last': {path: query}, 'trail': [path, query] or None, 'saved': [{'id', 'name', 'path', 'query', 'added'}]}."""
    if w is None:
        return {'last': {}, 'trail': None, 'saved': []}
    st = w.__dict__.get('_views')
    if st is None:
        try:
            raw = json.loads(_path(w).read_text())
            st = {'last': {str(k): str(v) for k, v in (raw.get('last') or {}).items()},
                  'trail': raw.get('trail') if isinstance(raw.get('trail'), list) else None,
                  'saved': [dict(x) for x in raw.get('saved') or [] if isinstance(x, dict) and x.get('path')]}
        except (OSError, ValueError, AttributeError, TypeError):
            st = {'last': {}, 'trail': None, 'saved': []}
        w._views = st
    return st


def _save(w, st):
    p = _path(w)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name(p.name + '.tmp')
        tmp.write_text(json.dumps({'format': FORMAT, **st}, indent=1))
        os.replace(tmp, p)
    except OSError:
        pass                                         # (browsing state only: a read-only folder just forgets it)
    w._views = st


def opened(w, path, q):
    """A list page was drawn with query q: (query to draw it with, note html). With no address of its own, the
    page's last view is restored (said so, with the default one click away); otherwise q becomes its last view.
    Either way it becomes the trail a detail page's "Back to" link returns to."""
    asked = bool(q)                                  # (?default=1 asks for the default: nothing restored)
    q = {k: v for k, v in (q or {}).items() if k not in TRANSIENT}
    if w is None or not is_list(path):
        return q, ''
    st = state(w)
    note = ''
    if not asked and st['last'].get(path):
        query = st['last'][path]
        q = parse_qs(query)
        note = (f'<p class="muted viewnote">Your last view of this page: {describe(path, query)} · '
                f'<a href="{esc(path)}?default=1">default view</a></p>'      # (the address becomes the view's:
                f'<script>try {{ history.replaceState(history.state, "", {json.dumps(href(path, query))}); }}'
                ' catch (e) {}</script>')                                    # Back, bookmarks, a browser sort)
    query = canonical(q)
    if st['last'].get(path, '') != query or st['trail'] != [path, query]:
        st = dict(st, last={**st['last'], path: query}, trail=[path, query])
        _save(w, st)
    return q, note


def remember(w, url):
    """The browser re-sorted a table on a list page (its address now carries tsort): remember that view too."""
    from urllib.parse import urlparse
    u = urlparse(url or '')
    if w is None or not is_list(u.path):
        return False
    q = parse_qs(u.query)
    st = state(w)
    query = canonical(q)
    _save(w, dict(st, last={**st['last'], u.path: query}, trail=[u.path, query]))
    return True


def describe(path, query):
    """'season 2040 · Majors + Premier · sorted by wins (descending) · page 3' for a view's address."""
    q = {k: v[0] for k, v in parse_qs(query).items()}
    parts = []
    for k, v in q.items():
        if k in ('dir', 'tsort'):
            continue
        if k == 'tour':
            from golfsim.scopes import LABEL, MAJORS_PREMIER
            parts.append(LABEL if v == MAJORS_PREMIER else f'tour {v.replace("_", " ").title()}')
        elif k == 'sort':
            d = q.get('dir')
            parts.append(f'sorted by {v.replace("_", " ")}' + (f' ({"ascending" if d == "asc" else "descending"})'
                                                                 if d else ''))
        elif k == 'year':
            parts.append('all-time' if v == 'all' else f'season {v}')
        else:
            parts.append(f'{LABELS.get(k, k.replace("_", " "))} {v}')
    if q.get('tsort'):
        try:
            _, col, d = q['tsort'].split('.')
            parts.append(f'table sorted by column {int(col) + 1} ({"ascending" if d == "a" else "descending"})')
        except ValueError:
            pass
    return esc(' · '.join(parts) or 'default view')


def href(path, query):
    return path + (f'?{query}' if query else '?default=1')


def back_link(w, path):
    """On a detail page: "Back to <the list view last opened>", whatever was opened since."""
    if w is None or is_list(path) or path in ('/', '/worlds', '/views'):
        return ''
    tr = state(w).get('trail')
    if not tr:
        return ''
    lp, query = tr
    return (f'<p class="back"><a href="{esc(href(lp, query))}">← Back to {esc(page_name(lp))}</a> '
            f'<span class="muted">({describe(lp, query)})</span></p>')


def save(w, name, path, query):
    if w is None or not is_list(path):
        return False
    name = (name or '').strip()[:80] or f'{page_name(path)} ({time.strftime("%Y-%m-%d %H:%M")})'
    st = state(w)
    saved = [x for x in st['saved'] if not (x['path'] == path and x['name'] == name)]
    vid = hashlib.sha1(f'{path}?{query}#{name}#{time.time()}'.encode()).hexdigest()[:10]
    saved.append({'id': vid, 'name': name, 'path': path, 'query': canonical(parse_qs(query)),
                  'added': time.strftime('%Y-%m-%d %H:%M')})
    _save(w, dict(st, saved=saved[-MAX_SAVED:]))
    return True


def remove(w, vid):
    st = state(w)
    saved = [x for x in st['saved'] if x['id'] != vid]
    if len(saved) == len(st['saved']):
        return False
    _save(w, dict(st, saved=saved))
    return True


def bar(w, path, q):
    """The views strip on a list page: its saved views, and a form to save the view shown."""
    if w is None or not is_list(path):
        return ''
    query = canonical(q)
    mine = [x for x in state(w)['saved'] if x['path'] == path]
    chips = ''.join(f'<a href="{esc(href(x["path"], x["query"]))}" class="{"on" if x["query"] == query else ""}" '
                    f'title="{describe(x["path"], x["query"])}">{esc(x["name"])}</a>' for x in mine)
    form = (f'<form method="post" action="/views/save" class="inline viewsave"><input type="hidden" name="path" '
            f'value="{esc(path)}"><input type="hidden" name="query" value="{esc(query)}">'
            '<input name="name" placeholder="Name this view" aria-label="Name this view" maxlength="80">'
            '<button>Save view</button></form>')
    return (f'<div class="views"><span class="muted">Saved views:</span> {chips or "<span class=muted>none</span>"} '
            f'{form} <a href="/views">all saved views</a></div>')


def views_page(w, q):
    saved = state(w)['saved']
    if not saved:
        body = ('<p class="muted">No saved views yet. On any list (Stats, Prize money, Golfers, Records, Moments and '
                'others) choose a season, scope, filters, sort and page, then <em>Save view</em>.</p>')
    else:
        rows = []
        for x in sorted(saved, key=lambda x: (page_name(x['path']), x['name'])):
            rows.append(f'<tr><td><a href="{esc(href(x["path"], x["query"]))}">{esc(x["name"])}</a></td>'
                        f'<td>{esc(page_name(x["path"]))}</td><td>{describe(x["path"], x["query"])}</td>'
                        f'<td>{esc(x["added"])}</td><td><form method="post" action="/views/remove" class="inline">'
                        f'<input type="hidden" name="id" value="{esc(x["id"])}"><button>Remove</button></form></td></tr>')
        body = ('<div class="scroll"><table class="sortable"><thead><tr><th>View</th><th>Page</th><th>What it shows</th>'
                '<th>Saved</th><th></th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>')
    last = state(w)['last']
    if last:
        body += ('<h2>Last view of each page</h2><p class="muted">Opening a page from the menu shows the view you '
                 'left it in.</p><ul>' + ''.join(
                     f'<li><a href="{esc(href(p, v))}">{esc(page_name(p))}</a>: {describe(p, v)}</li>'
                     for p, v in sorted(last.items(), key=lambda x: page_name(x[0]))) + '</ul>')
    return 'Saved views', body + (f'<p class="muted">Kept with this world ({esc(FILE)}): browsing state only, never '
                                  'read by the simulation.</p>')


# Browser-side column sorts are kept in the address (tsort=table.column.a|d, replaced in place, so Back and
# the trail return to them), applied again when the page opens, and reported so the page's last view has them.
SORT_JS = """<script>
(function () {
  function key(c) {
    if (!c) return null;
    var t = (c.getAttribute('data-sort') !== null ? c.getAttribute('data-sort') : c.textContent).trim();
    if (t === '' || t === '\\u2014' || /^(unknown|unavailable|not recorded|n\\/a)$/i.test(t)) return null;
    var m = t.replace(/[$,*%+]/g, '').replace(/^T(?=\\d)/, '').replace(/\\u2212/g, '-').match(/^-?\\d+(\\.\\d+)?/);
    return m ? [0, parseFloat(m[0])] : [1, t.toLowerCase()];
  }
  function sortBy(table, i, dir) {
    var tb = table.tBodies[0], th = table.tHead && table.tHead.rows[0] && table.tHead.rows[0].cells[i];
    if (!tb || !th) return;
    Array.prototype.forEach.call(table.querySelectorAll('th'), function (h) { h.removeAttribute('aria-sort'); });
    th.setAttribute('aria-sort', dir);
    var rows = Array.prototype.slice.call(tb.rows).map(function (r, n) { return [key(r.cells[i]), n, r]; });
    rows.sort(function (a, b) {
      var x = a[0], y = b[0];
      if (x === null || y === null) return x === y ? a[1] - b[1] : (x === null ? 1 : -1);
      var r = x[0] - y[0] || (x[0] === 0 ? x[1] - y[1] : x[1].localeCompare(y[1]));
      return (dir === 'ascending' ? r : -r) || a[1] - b[1];
    });
    rows.forEach(function (r) { tb.appendChild(r[2]); });
  }
  var tables = function () { return Array.prototype.slice.call(document.querySelectorAll('table.sortable')); };
  document.addEventListener('click', function (ev) {
    var th = ev.target.closest('table.sortable th'); if (!th || ev.target.closest('a,button,input,select')) return;
    var table = th.closest('table'), i = Array.prototype.indexOf.call(th.parentNode.children, th);
    var dir = th.getAttribute('aria-sort') === 'ascending' ? 'descending' : 'ascending';
    sortBy(table, i, dir);
    try {
      var u = new URL(location.href);
      u.searchParams.set('tsort', tables().indexOf(table) + '.' + i + '.' + (dir === 'ascending' ? 'a' : 'd'));
      u.searchParams.delete('default');
      history.replaceState(history.state, '', u.pathname + u.search + u.hash);
      fetch('/views/last', {method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                            body: 'url=' + encodeURIComponent(u.pathname + u.search), keepalive: true});
    } catch (e) {}
  });
  try {
    var s = new URL(location.href).searchParams.get('tsort');
    if (s) { var p = s.split('.'), t = tables()[+p[0]];
             if (t) sortBy(t, +p[1], p[2] === 'a' ? 'ascending' : 'descending'); }
  } catch (e) {}
})();
</script>"""
