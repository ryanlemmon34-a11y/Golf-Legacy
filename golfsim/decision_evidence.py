"""Decision evidence (recording only): why golfers scheduled their seasons as they did, and what went into each
winter's career decisions. Nothing here takes part in a decision: the planner and the career rules compute their
figures exactly as before, and this module only keeps them -- it draws no random numbers, adds no keys to the
season's working tables and changes no iteration order (tests/test_decision_evidence.py; whole-season outcome
equivalence: tests.test_decision_evidence_world, tools/equivalence_check.py).

Archived in each season file under `decision_evidence` (format FORMAT; the block carries its own `definitions`, so
a reader never guesses a field). A season file without the key was played before this was kept: its evidence is
not recorded (never estimated). Format /2 (this build) adds the amateur return model and the winter's mortality
draws to /1's two parts; read() reads both. Three parts:

    schedule    each golfer the monthly planner evaluated (Season.plan_block, weeks 1, 5, ... 49), one compact row
                per plan -- at most PLAN_BLOCKS a season: starts so far, fatigue, the four weeks' availability and
                the plan chosen, the value of a training week; injury weeks and the planner's flags only for
                golfers who had any; the target number of starts with its named components, and the planner's
                slower-moving terms (bar, development value of playing, value of paid work, fatigue load and
                recovery, injury risk), these two kept only when they change.
    careers     each golfer the winter's career rules evaluated (careers.decide), one row per evaluation -- at most
                CAREER_ROWS a winter: the model, its probability, the uniform draw it was compared with, the
                outcome, each named term of the model's logit (they sum to logit(p)) and the inputs behind them
                that the season file does not already hold.
    mortality   the winter's mortality draws (mortality.winter): each death's risk and draw in full, and every
                person evaluated counted by ten-year age band (evaluated, expected deaths, deaths) -- a survivor's
                own draw is not kept (it is reproducible: mortality.draw(seed, year, person) against
                mortality.annual_risk(age)).

docs/DECISION_EVIDENCE.md defines every field and lists what is not recorded.
"""
from __future__ import annotations

from collections import defaultdict

FORMAT = 'golf-legacy-decision-evidence/2'
FORMATS = ('golf-legacy-decision-evidence/1', FORMAT)   # what read() understands (/1: no return model, no mortality)
PLAN_BLOCKS = 13                 # monthly plans a season (weeks 1, 5, ... 49): schedule rows per golfer-season, at most
PLAN_EVERY = 4                   # weeks between plans
CAREER_ROWS = 3                  # career evaluations per golfer-winter, at most (retire, then one or two more)
MORTALITY_BAND = 10              # years: survivors of the winter's mortality draws are counted by age band

# ---- the monthly schedule ---------------------------------------------------------------------------------------
TARGET_FIELDS = ('week', 'role', 'base', 'stamina', 'prestige', 'target')
TARGET_ROLES = {'retired': 'retired (no schedule)', 'part_time_pro': 'part-time professional (a job comes first)',
                'part_time_amateur': 'part-time amateur', 'club_pro': 'club professional', 'college': 'college golfer',
                'amateur': 'amateur', 'premier': 'Premier Tour member', 'pro': 'professional below the Premier Tour'}
TERM_FIELDS = ('week', 'bar', 'dev_play', 'work_value', 'load4', 'rest_keep', 'injury_risk')
TERM_SCALE = (1, 1, 10, 10, 1000, 1000, 10000)          # stored as round(value * scale)
# one column per field, one entry per plan (entry k: the plan made in week w + PLAN_EVERY * k); 'c' holds each plan's
# CODE_LEN characters (the weeks' availability, then the activity planned for each)
COLUMNS = {'n': ('started', 1), 'x': ('fatigue', 100), 'm': ('funds_k', 1), 'd': ('dev_train', 10),
           'i': ('injured_weeks', 1), 'f': ('flags', 1)}
CODE_LEN = 2 * PLAN_EVERY
AVAIL = {'ok': 'o', 'unaff': 'u', 'inelig': 'e', 'none': 'n'}
ACTS = {'play': 'P', 'train': 'T', 'rest': 'R', 'work': 'W'}
FLAGS = {1: 'can_work', 2: 'stuck', 4: 'major_caution', 8: 'no_affordable_plan'}


def target_parts(season, g):
    """Season.target_events(g) by its named parts: (role, base, stamina, prestige); base + stamina + prestige is
    the target. Mirrors target_events (tests check every role); reads fame and legacy without adding keys."""
    from .season import PREMIER_TOURS
    from . import prestige as PR
    if g.lifestyle == 'retired':
        return 'retired', 0, 0.0, 0
    if g.lifestyle == 'part_time' and g.status in ('pro', 'amateur'):
        return ('part_time_pro', 6, 0.0, 0) if g.status == 'pro' else ('part_time_amateur', 8, 0.0, 0)
    if g.status == 'club_pro':
        return 'club_pro', 12, 0.0, 0
    if g.tour.startswith('CO_'):
        return 'college', 24, 0.0, 0
    if g.status == 'amateur':
        return 'amateur', 16, 0.0, 0
    stam = 8 * g.attrs['stamina'] / 100
    if g.tour in PREMIER_TOURS:
        pp = PR.player_prestige(season.fame.get(g.id, 0.0), season.legacy.get(g.id, 0.0))
        return 'premier', 15, stam, (-4 if pp >= 65 else 0)
    return 'pro', 19, stam, 0


def _two_figures(k):
    """$1000s to two significant figures (whole thousands below 100): 1234.5 -> 1200, 37.2 -> 37, -0.4 -> 0."""
    v = round(k)
    return v if abs(v) < 100 else int(round(v, 2 - len(str(abs(v)))))


def _r(x, n=2):
    v = round(x, n)
    return int(v) if v == int(v) else v


def record_plan(season, g, year, week0, *, target, weeks, avail, acts, inj_until, now, f0, played0, money0, bar, dp,
                dt, work_v, load4, rest_rec, risk, can_work, stuck, major, fallback):
    """Keep one golfer's monthly plan (called by Season.plan_block once the plan is chosen, with figures the planner
    already computed; reads nothing else)."""
    book = season.plan_ev[year]
    rec = book.get(g.id)
    if rec is None:
        rec = book[g.id] = {'w': week0, 't': [], 's': [], 'n': [], 'x': [], 'm': [], 'c': '', 'd': []}
    k = (week0 - rec['w']) // PLAN_EVERY                # this plan's place in the season's columns
    if k < len(rec['n']) or k >= PLAN_BLOCKS:           # (a plan made twice, or beyond the bound: not kept)
        rec['over'] = rec.get('over', 0) + 1
        return
    while len(rec['n']) < k:                            # a plan not recorded (recording was off): null
        for key in ('n', 'x', 'm', 'd'):
            rec[key].append(None)
        rec['c'] += '-' * CODE_LEN
    role, base, stam, pres = target_parts(season, g)
    t = [role, base, _r(stam), pres, _r(target)]
    if not rec['t'] or rec['t'][-1][1:] != t:
        rec['t'].append([week0] + t)
    s = [round(v * sc) for v, sc in zip((bar, dp, work_v, load4, rest_rec, risk), TERM_SCALE[1:])]
    if not rec['s'] or rec['s'][-1][1:] != s:
        rec['s'].append([week0] + s)
    code = ''.join(AVAIL.get(avail.get(w), '-') for w in weeks) + ''.join(ACTS.get(a, '?') for a in acts)
    rec['n'].append(played0)
    rec['x'].append(round(f0 * 100))
    rec['m'].append(_two_figures(money0 / 1000))
    rec['c'] += code
    rec['d'].append(round(dt * 10))
    inj = min(99, max(0, inj_until - (now + week0)))
    flags = (1 if can_work else 0) | (2 if stuck else 0) | (4 if major else 0) | (8 if fallback else 0)
    for key, v in (('i', inj), ('f', flags)):           # kept only for golfers who had any
        if v or key in rec:
            col = rec.setdefault(key, [])
            col.extend([0] * (k - len(col)))
            col.append(v)


# ---- the winter's career decisions -------------------------------------------------------------------------------
# Each evaluation is a row [model, p, u, outcome, *terms, *inputs]: the probability, the uniform draw compared with
# it (u < p: the outcome happened), outcome 1/0, the model's logit terms (summing to logit(p); None: not a term of
# the model in this case) and the inputs behind them that the season file does not already hold (money in $1000s).
CAREER_MODELS = {
    'retire_job': {
        'terms': ('base', 'age', 'engaged', 'drift', 'blocked', 'standing', 'progress', 'willingness', 'injury'),
        'inputs': ('age', 'target', 'drift', 'blocked', 'rank', 'lasting_damage')},
    'retire_tour': {
        'terms': ('base', 'age', 'standing', 'opportunity', 'injury'),
        'inputs': ('age', 'tier', 'money_rank_pct', 'lasting_damage')},
    'stop_chasing': {
        'terms': ('base', 'pressure', 'short_runway', 'progress', 'opportunity', 'secured', 'willingness', 'life',
                  'injury', 'lasting_damage'),
        'inputs': ('age', 'tier', 'runway', 'shortfall_k', 'own_funds_k', 'target', 'lasting', 'p_club', 'p_amateur',
                   'u_where')},
    'turn_pro': {
        'terms': ('base', 'standing', 'means', 'willingness', 'wins', 'age'),
        'inputs': ('age', 'graduating', 'am_rank')},
    'amateur_job': {
        'terms': ('base', 'age', 'runway', 'debt'),
        'inputs': ('age', 'runway', 'cash_k')},
    'comeback': {
        'terms': ('base', 'results', 'funded', 'age', 'injury', 'willingness'),
        'inputs': ('age', 'top3', 'progress')},
    # (format /2) a working amateur's return to full-time golf (amateur_return.chance): p = min(cap, sig(sum of the
    # terms) x keep_up), 0 when a condition blocks it (blocked: 'work', 'funds' or 'results'; no draw then)
    'amateur_return': {
        'terms': ('base', 'results', 'funds', 'willingness', 'age'),
        'inputs': ('age', 'seasons_in_work', 'season_cost_k', 'funds_k', 'signal', 'keep_up', 'capped', 'blocked')},
}
_MONEY = {'shortfall_k': 'shortfall', 'own_funds_k': 'own_funds', 'cash_k': 'cash', 'season_cost_k': 'season_cost',
          'funds_k': 'funds'}


def _input(ev, k):
    v = ev.get('in_' + _MONEY.get(k, k))
    if v is None:
        return None
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, str):
        return v
    if k in _MONEY:
        return round(v / 1000)
    return _r(v, 3)


def record_career(season, year, g, model, p, u, ev):
    """Keep one evaluation of a career model (called by careers.decide right after its draw). `ev`: the terms and
    inputs the model filled in while computing p (careers.p_* with ev=); absent ones are stored as None."""
    rows = season.career_ev[year].setdefault(g.id, [])
    if len(rows) >= CAREER_ROWS:                        # (the bound: never reached by the rules as written)
        return
    spec = CAREER_MODELS[model]
    rows.append([model, _r(p, 4), None if u is None else _r(u, 4), int(u is not None and u < p)]
                + [None if ev.get(k) is None else _r(ev[k], 2) for k in spec['terms']]
                + [_input(ev, k) for k in spec['inputs']])


# ---- the winter's mortality draws --------------------------------------------------------------------------------
def record_mortality(book, pid, age, q, u):
    """Keep one mortality evaluation (called by mortality.winter with the risk and draw it compared): a death in
    full, and every evaluation in its age band's counts."""
    band = book.setdefault('bands', {}).setdefault(age // MORTALITY_BAND * MORTALITY_BAND, [0, 0.0, 0])
    band[0] += 1
    band[1] += q
    if u < q:
        band[2] += 1
        book.setdefault('died', {})[pid] = [age, _r(q, 5), _r(u, 5)]


# ---- the archive -------------------------------------------------------------------------------------------------
def definitions():
    return {'plan_blocks': PLAN_BLOCKS, 'plan_every': PLAN_EVERY, 'career_rows': CAREER_ROWS,
            'target': list(TARGET_FIELDS), 'target_roles': TARGET_ROLES,
            'terms': list(TERM_FIELDS), 'term_scale': list(TERM_SCALE),
            'columns': {k: {'field': f, 'scale': sc} for k, (f, sc) in COLUMNS.items()}, 'code_len': CODE_LEN,
            'avail': {v: k for k, v in AVAIL.items()}, 'acts': {v: k for k, v in ACTS.items()},
            'flags': {str(k): v for k, v in FLAGS.items()},
            'careers': {'row': ['model', 'p', 'u', 'outcome', '*terms', '*inputs'],
                        'models': {m: {'terms': list(s['terms']), 'inputs': list(s['inputs'])}
                                   for m, s in CAREER_MODELS.items()}},
            'mortality': {'band_years': MORTALITY_BAND, 'band': ['evaluated', 'expected', 'died'],
                          'died': ['age', 'p', 'u']}}


def season_block(season, year):
    """The season file's `decision_evidence` block, or None when nothing was recorded."""
    plans = getattr(season, 'plan_ev', {}).get(year, {})
    careers = getattr(season, 'career_ev', {}).get(year, {})
    deaths = getattr(season, 'mortality_ev', {}).get(year, {})
    if not plans and not careers and not deaths:
        return None
    return {'format': FORMAT, 'definitions': definitions(),
            'schedule': {str(g): r for g, r in sorted(plans.items())},
            'careers': {str(g): rows for g, rows in sorted(careers.items())},
            'mortality': {'bands': {str(b): [n, round(e, 3), k]
                                    for b, (n, e, k) in sorted(deaths.get('bands', {}).items())},
                          'died': {str(p): r for p, r in sorted(deaths.get('died', {}).items())}}}


def read(chunk, gid):
    """A golfer's decision evidence from a season file's contents (as decoded): {'recorded': False} for a season
    played before it was kept; else {'recorded': True, 'schedule': [one dict per plan, with the target and terms
    in force, values in their own units], 'careers': [one dict per evaluation], 'mortality': this person's death
    draw {age, p, u} if they died that winter, else None (format /1: no mortality part, None)}."""
    blk = chunk.get('decision_evidence')
    if not blk or blk.get('format') not in FORMATS:
        return {'recorded': False}
    d = blk['definitions']
    key = str(gid)
    out = {'recorded': True, 'schedule': [], 'careers': []}
    rec = blk['schedule'].get(key)
    if rec:
        acts, avail, flags, cols, n = d['acts'], d['avail'], d['flags'], d['columns'], d['code_len']
        col = lambda key, k: rec[key][k] if k < len(rec.get(key, ())) else 0     # (optional columns: 0 if absent)
        prev = None
        for k in range(len(rec['n'])):
            w = rec['w'] + d['plan_every'] * k
            started = rec['n'][k]
            if started is None:                           # a plan not recorded
                prev = None
                continue
            t = ([x for x in rec['t'] if x[0] <= w] or rec['t'])[-1]
            s = ([x for x in rec['s'] if x[0] <= w] or rec['s'])[-1]
            code = rec['c'][k * n:(k + 1) * n]
            row = {'week': w, 'started': started, 'last4': started - prev if prev is not None else None,
                   'fatigue': rec['x'][k] / cols['x']['scale'], 'funds_k': col('m', k), 'injured_weeks': col('i', k),
                   'availability': [avail.get(c) for c in code[:n // 2]], 'plan': [acts.get(c) for c in code[n // 2:]],
                   'dev_train': rec['d'][k] / cols['d']['scale'],
                   'flags': [name for bit, name in flags.items() if col('f', k) & int(bit)],
                   'target': dict(zip(d['target'], t)),
                   'terms': {name: v / sc for name, v, sc in zip(d['terms'][1:], s[1:], d['term_scale'][1:])}}
            row['pace'] = round(row['target']['target'] * w / 52 - started, 2)   # behind (+) or ahead (-) of target
            out['schedule'].append(row)
            prev = started
    for r in blk['careers'].get(key, []):
        spec = d['careers']['models'][r[0]]
        n = len(spec['terms'])
        out['careers'].append({'model': r[0], 'p': r[1], 'u': r[2], 'outcome': r[3],
                               'terms': dict(zip(spec['terms'], r[4:4 + n])),
                               'inputs': dict(zip(spec['inputs'], r[4 + n:]))})
    died = blk.get('mortality', {}).get('died', {}).get(key)
    out['mortality'] = dict(zip(d.get('mortality', {}).get('died', ()), died)) if died else None
    return out


def new_tables():
    """The season's evidence tables: year -> gid -> record (plans) / [evaluations] (careers)."""
    return defaultdict(dict), defaultdict(dict)
