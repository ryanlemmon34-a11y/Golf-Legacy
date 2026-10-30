"""GOAT Lab: rank careers by your own weighting of recorded achievements and statistics (in the spirit of
Basketball GM's GOAT Lab).

Each component is a career figure the observer already works out elsewhere -- the Stats directory's totals
(statistics store, current season included, in the chosen scope), the majors list behind the Career Grand Slam
page, the Records page's weeks at world No. 1, the archived season-end world rankings and the Recorded Peak
Overall -- with its definition, scope and coverage stated. A career's score is the weighted sum of its components,
or a formula of them you write (numbers, the component names, + - * / ** and parentheses, min, max, sqrt, log;
nothing else is evaluated). An invalid formula is reported and the weighted sum is used instead. Ties are broken
by majors, then wins, then the golfer's id (deterministic). Partial careers (begun before the world's records) and
missing figures are marked on every row; a missing figure counts as 0 in the score and says so.
"""
from __future__ import annotations

import ast
import math
import operator
from urllib.parse import urlencode

# name: (label, definition, source, scope note, default weight)
COMPONENTS = {
    'majors': ('Majors', 'Major championships won', 'the editions (as the Career Grand Slam page)',
               'majors only, whatever the scope; current season included; hidden results left out', 8.0),
    'wins': ('Wins', 'Events won', 'the Stats directory (statistics store)', 'the chosen scope; current season included',
             3.0),
    'top10': ('Top 10s', 'Top-10 finishes (wins included)', 'the Stats directory', 'the chosen scope', 0.5),
    'runner_ups': ('Runner-ups', 'Recorded second places (ties included)', 'the Stats directory', 'the chosen scope', 0.0),
    'starts': ('Starts', 'Starts (qualifying stages excluded)', 'the Stats directory', 'the chosen scope', 0.0),
    'prize_m': ('Prize money ($m)', 'Prize money in millions', 'the Stats directory',
                'all tours: money paid; a scope: recomputed payouts, missing where they could not be reconciled', 0.0),
    'weeks_no1': ('Weeks at No. 1', 'Weeks at world No. 1', 'the Records page', 'archived seasons', 0.2),
    'top10_seasons': ('Top-10 seasons', 'Seasons ending inside the world top 10', 'the archived season-end rankings',
                      'archived seasons', 1.0),
    'peak': ('Peak Overall', 'Recorded Peak Overall (the highest base Overall the engine noted)',
             'the current snapshot, else the last archived season', 'missing where not recorded', 0.0),
    'slam': ('Career Grand Slam', '1 if all four majors won, else 0', 'the Career Grand Slam page',
             'hidden results left out', 10.0),
}
FUNCS = {'min': min, 'max': max, 'sqrt': math.sqrt, 'log': math.log}
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
       ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}
MAX_FORMULA = 400
SHOW = 100


class FormulaError(ValueError):
    pass


def compile_formula(text):
    """A checked expression tree, or FormulaError saying what is wrong (only the allowed syntax is accepted)."""
    text = (text or '').strip()
    if len(text) > MAX_FORMULA:
        raise FormulaError(f'the formula is longer than {MAX_FORMULA} characters')
    try:
        tree = ast.parse(text, mode='eval')
    except SyntaxError as e:
        raise FormulaError(f'not a formula ({e.msg})') from None

    def check(n):
        if isinstance(n, ast.Expression):
            return check(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return
        if isinstance(n, ast.Name):
            if n.id not in COMPONENTS:
                raise FormulaError(f'unknown name “{n.id}” (use: {", ".join(COMPONENTS)})')
            return
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            check(n.left)
            check(n.right)
            return
        if isinstance(n, ast.UnaryOp) and type(n.op) in OPS:
            check(n.operand)
            return
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in FUNCS and not n.keywords
                and 1 <= len(n.args) <= 8):
            for a in n.args:
                check(a)
            return
        raise FormulaError('only numbers, component names, + - * / **, parentheses and min, max, sqrt, log are allowed')
    check(tree)
    return tree


def evaluate(tree, values):
    """The formula's value for one career (None if it cannot be worked out: a division by zero, a log of 0...)."""
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant):
            return float(n.value)
        if isinstance(n, ast.Name):
            return float(values.get(n.id) or 0.0)
        if isinstance(n, ast.BinOp):
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Pow) and (abs(b) > 10 or abs(a) > 1e6):
                raise ArithmeticError('power too large')
            return OPS[type(n.op)](a, b)
        if isinstance(n, ast.UnaryOp):
            return OPS[type(n.op)](ev(n.operand))
        return FUNCS[n.func.id](*[ev(a) for a in n.args])
    try:
        v = ev(tree)
    except (ArithmeticError, ValueError, OverflowError):
        return None
    return v if isinstance(v, float) and math.isfinite(v) else None


def weights(q):
    O = _o()
    out = {}
    for k, (_, _, _, _, d) in COMPONENTS.items():
        raw = O.one(q, f'w_{k}')
        try:
            out[k] = float(raw) if raw not in (None, '') else d
        except ValueError:
            out[k] = d
        if not math.isfinite(out[k]):
            out[k] = d
    return out


def _o():
    import observer as O
    return O


def careers(w, scope):
    """{pid: {component: value or None}}, plus {pid: [missing component names]}: every golfer with a recorded start."""
    import observer_history as OH
    import observer_stats as ST
    db, _ = w.statistics()
    live = w.live_statistics()
    years = list(w.a.years) if w.a else []
    data = ST.query(db, years, scope or None, live, cols=('starts', 'wins', 'runner_ups', 'top10'))
    majors = {}
    for m in OH.major_wins(w):
        majors[m[4]] = majors.get(m[4], 0) + 1
    slams = {g for g, s in OH.grand_slams(w).items() if s.get('complete')}
    no1 = {}
    if w.a:
        from golfsim.history_stats import board
        if w.stats is not None:                        # (the Records page's list, worked out once and cached)
            for r in board(w.stats, 'weeks-at-number-one', n=10 ** 6)[1]:
                no1[r['person']] = r['value']
    top10s = {}
    if w.a and w.a.index is not None:
        idx = w.a.index
        for pid, n in idx.db.execute('SELECT person, COUNT(*) FROM seasons WHERE wr_end BETWEEN 1 AND 10'
                                     + idx.upto() + ' GROUP BY person'):
            top10s[pid] = n
    peaks = _peaks(w)
    out, missing = {}, {}
    for pid, r in data.items():
        if not r.get('starts') and not majors.get(pid):
            continue
        v = {'majors': majors.get(pid, 0), 'wins': r['wins'], 'top10': r['top10'], 'runner_ups': r['runner_ups'],
             'starts': r['starts'], 'prize_m': (r['prize'] / 1e6) if r['prize_known'] else None,
             'weeks_no1': no1.get(pid, 0), 'top10_seasons': top10s.get(pid, 0), 'peak': peaks.get(pid),
             'slam': 1 if pid in slams else 0}
        out[pid] = v
        missing[pid] = [k for k, x in v.items() if x is None]
    return out, missing


def _peaks(w):
    """{pid: Recorded Peak Overall value} as the engine noted it: the current snapshot, else the last archived season."""
    out = {}
    if w.a:
        last = w.a.year(w.a.years[-1])['careers']
        for pid, r in last.items():
            if r.get('peak'):
                out[pid] = r['peak'][0]
    if w.live is not None:
        for pid, p in w.live.people.items():
            if p.get('peak'):
                out[pid] = p['peak'][0]
    return out


def goat_page(w, q):
    O = _o()
    import observer_spoilers as SP
    from golfsim import scopes as SC
    if not w.a and w.live is None:
        return 'GOAT Lab', O.no_history()
    db, building = w.statistics()
    if building:
        return 'GOAT Lab', (f'<p>Working out the statistics from the history: {building["done"]} of {building["total"]} '
                            'seasons. This page refreshes by itself.</p><meta http-equiv="refresh" content="3">')
    scope = O.one(q, 'tour', SC.MAJORS_PREMIER)
    scope = SC.MAJORS_PREMIER if scope == SC.MAJORS_PREMIER else ''
    wt = weights(q)
    text = (O.one(q, 'formula', '') or '').strip()
    error, tree = None, None
    if text:
        try:
            tree = compile_formula(text)
        except FormulaError as e:
            error = str(e)
    status = O.one(q, 'status', '') or ''
    vals, missing = careers(w, scope)
    rows, failed = [], 0
    for pid, v in vals.items():
        if status:
            g = (w.person(pid) or {}).get('golfer') or {}
            retired = g.get('lifestyle') == 'retired'
            if (status == 'active') == retired:
                continue
        if tree is not None:
            s = evaluate(tree, v)
            if s is None:
                failed += 1
                continue
        else:
            s = sum(wt[k] * (v[k] or 0.0) for k in COMPONENTS)
        rows.append((pid, round(s, 6), v))
    rows.sort(key=lambda r: (-r[1], -(r[2]['majors'] or 0), -(r[2]['wins'] or 0), r[0]))   # deterministic ties
    chunk, pager = O.paged(rows, q, '/goat')
    start = (max(1, int(O.one(q, 'page', '1') or 1)) - 1) * O.PAGE_SIZE
    used = [k for k in COMPONENTS if (tree is not None and _uses(tree, k)) or (tree is None and wt[k])]
    head = ('<tr><th class="n">#</th><th>Golfer</th><th class="n">Score</th>'
            + ''.join(f'<th class="n" title="{O.esc(COMPONENTS[k][1])}">{O.esc(COMPONENTS[k][0])}'
                      + (f'<br><span class="muted">×{wt[k]:g}</span>' if tree is None else '') + '</th>' for k in used)
            + '<th>Coverage</th></tr>')
    body = []
    for i, (pid, s, v) in enumerate(chunk, start + 1):
        cells = []
        for k in used:
            x = v[k]
            if x is None:
                cells.append('<td class="n"><span class="muted">missing</span></td>')
            else:
                shown = f'{x:,.1f}' if k in ('prize_m', 'peak') else f'{x:,}'
                contrib = f'<br><span class="muted">{wt[k] * x:+,.1f}</span>' if tree is None else ''
                cells.append(f'<td class="n">{shown}{contrib}</td>')
        body.append(f'<tr><td class="n">{i}</td><td>{w.person_link(pid)}</td><td class="n"><strong>{s:,.1f}</strong></td>'
                    + ''.join(cells) + f'<td>{_coverage(w, pid, [k for k in missing.get(pid, []) if k in used])}</td></tr>')
    form = _form(w, q, wt, text, scope, status)
    err = (f'<div class="banner warn" role="status">Formula not used: {O.esc(error)}. The weighted sum is shown '
           'instead.</div>' if error else '')
    note = (f'<p class="muted">{failed} career{"s" if failed != 1 else ""} left out: the formula could not be worked '
            'out for them (a division by zero or a log of 0, for example).</p>' if failed else '')
    how = (f'Score: <code>{O.esc(text)}</code>' if tree is not None else
           'Score: the weighted sum of the components (weight × value; the small figure under each value is its '
           'contribution)')
    return 'GOAT Lab', (SP.aggregate_note(w, 'these career figures') + err + form
                        + f'<p>{how} · {SC.LABEL if scope else "all tours"} · {len(rows):,} careers · ties broken by '
                          'majors, then wins, then id.</p>' + note
                        + f'<div class="scroll"><table>{head}{"".join(body)}</table></div>' + pager
                        + _definitions(w, scope))


def _uses(tree, name):
    return any(isinstance(n, ast.Name) and n.id == name for n in ast.walk(tree))


def _coverage(w, pid, missing):
    O = _o()
    bits = []
    p = (w.a.people.get(pid) if w.a else None) or {}
    if p.get('initial'):
        bits.append('<span class="tag">partial</span> career began before the world’s records')
    g = (w.person(pid) or {}).get('golfer') or {}
    if g.get('lifestyle') not in (None, 'retired'):
        bits.append('active: career continuing')
    if missing:
        bits.append('missing: ' + ', '.join(O.esc(COMPONENTS[k][0]) for k in missing) + ' (counted as 0)')
    return '<br>'.join(bits) or '<span class="muted">complete, retired</span>'


def _form(w, q, wt, text, scope, status):
    O = _o()
    from golfsim import scopes as SC
    inputs = ''.join(f'<label title="{O.esc(COMPONENTS[k][1])}">{O.esc(COMPONENTS[k][0])}'
                     f'<input name="w_{k}" value="{wt[k]:g}" size="4" inputmode="decimal"></label>' for k in COMPONENTS)
    sopts = ''.join(f'<option value="{v}"{" selected" if v == scope else ""}>{t}</option>'
                    for v, t in ((SC.MAJORS_PREMIER, SC.LABEL), ('', 'all tours')))
    stopts = ''.join(f'<option value="{v}"{" selected" if v == status else ""}>{t}</option>'
                     for v, t in (('', 'everyone'), ('active', 'still playing'), ('retired', 'retired')))
    defaults = urlencode({'tour': scope} if scope else {'tour': ''})
    return (f'<form class="filters goat" action="/goat"><fieldset><legend>Weights</legend>{inputs}</fieldset>'
            f'<label>Formula (optional)<input name="formula" value="{O.esc(text)}" size="48" '
            f'placeholder="e.g. 8*majors + 3*wins + max(weeks_no1, 10)"></label>'
            f'<label>Scope<select name="tour">{sopts}</select></label><label>Careers<select name="status">{stopts}'
            f'</select></label><button>Rank</button> <a href="/goat?{defaults}">default weights</a></form>')


def _definitions(w, scope):
    O = _o()
    years = w.a.years if w.a else []
    cov = (f'archived seasons {years[0]}–{years[-1]}' if years else 'no archived seasons') + (
        f' and {w.live.cursor["year"]} so far' if w.live else '')
    rows = ''.join(f'<tr><td><code>{k}</code></td><td>{O.esc(c[0])}</td><td>{O.esc(c[1])}</td><td>{O.esc(c[2])}</td>'
                   f'<td>{O.esc(c[3])}</td><td class="n">{c[4]:g}</td></tr>' for k, c in COMPONENTS.items())
    return ('<h2>Components</h2><div class="scroll"><table><thead><tr><th>Name</th><th>Component</th><th>Definition</th>'
            '<th>Worked out by</th><th>Scope</th><th class="n">Default weight</th></tr></thead><tbody>' + rows
            + f'</tbody></table></div><p class="muted">Coverage: {O.esc(cov)}. “Wins” in all tours counts college, '
              'amateur and club-professional events too; Majors + Premier counts every major and Premier event. '
              'A career that began before the world’s records is partial: its earlier achievements are not in any '
              'figure. Peak Overall: the engine’s noted peak (a profile may also show start-of-season ratings from '
              'before peaks were kept). Formula functions: min, max, sqrt, log; a formula that cannot be worked '
              'out for a career leaves that career out (counted above the table).</p>')
