"""Career smoke test on a FULL-SIZE fresh world (model/API level, through Session; no browser, no HTTP).
usage: python career_smoke_full.py ROOT SEED WORKDIR"""
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve(); SEED = int(sys.argv[2]); WORK = Path(sys.argv[3])
sys.path.insert(0, str(ROOT))
from golfsim import career as CA                                         # noqa: E402
from golfsim import realism as RZ                                        # noqa: E402
from golfsim.population import generate_world                            # noqa: E402
from golfsim.session import Session, StaleCursor                         # noqa: E402

checks = []
def check(name, ok, detail=''):
    checks.append((name, bool(ok), detail)); print(('PASS ' if ok else 'FAIL ') + name + (f' -- {detail}' if detail else ''), flush=True)

def act(s, body, key, **kw):
    return s.career_action(dict({'schema': CA.SCHEMA}, **body), op_key=key, **kw)

t0 = time.time()
BOUND = Path(str(WORK) + '_boundary') / 'w'
d = WORK / 'w'
if WORK.exists(): shutil.rmtree(WORK)
if not BOUND.exists():
    s = Session.create(BOUND, seed=SEED, world=generate_world(year=2027, seed=SEED), workers=1)
    check('fresh full-size world uses dev-3', s.season.dev_rules == RZ.DEV3, s.season.dev_rules)
    s.advance(52); s.close()
    print(f'first season played in {time.time() - t0:.0f} s', flush=True)
shutil.copytree(BOUND, d)
s = Session.open(d)
check('at the second season start', s.cursor == {'year': 2028, 'week': 1, 'phase': 'start'}, str(s.cursor))
# --- start
r = act(s, {'type': 'new_career'}, 'new')
c = s.season.career; g = s.season.g[c.golfer_id]
rec = s.season.creations[2028][c.golfer_id]
check('career controls a genuine 2028 junior', rec.get('path') == 'junior' and g.age(2028) == 18, f'{g.name}, entry {rec.get("overall")}')
check('the junior was generated under dev-3 (potential within the elite tail)', g.potential < 95.0, f'potential {g.potential}')
try:
    act(s, {'type': 'new_career'}, 'new2'); check('second career refused', False)
except CA.CareerError as e:
    check('second career refused', True, str(e)[:60])
v = CA.view(s.season, s.cursor)
txt = json.dumps(v, default=str)
check('no hidden potential or ceilings in the career view', 'potential' not in txt.lower() and 'ceiling' not in txt.lower())
# --- to the first plan, then plan event / train / rest
out = s.advance_career('next', op_key='a1')
pend = c.pending()
check('stops for the first plan', any(x['kind'] == 'plan' for x in pend), str([x['kind'] for x in pend]))
y, w0 = 2028, 1
pl = CA.planner(s.season, s.cursor, y, w0)
weeks = {}
evt = None
for wk in pl['weeks']:
    ev = next((e for e in wk['events'] if e['eligible'] and e.get('affordable')), None)
    if ev and evt is None:
        weeks[wk['week']] = {'kind': 'event', 'event_id': ev['event_id'], 'fallback': {'kind': 'train', 'category': 'putting'}}
        evt = (wk['week'], ev['event_id'])
inel = next(((wk['week'], e) for wk in pl['weeks'] for e in wk['events'] if not e['eligible']), None)
open_w = CA.open_weeks(s.cursor, w0)
for wk in open_w:
    if wk not in weeks:
        weeks[wk] = {'kind': 'train', 'category': 'short_game'} if len(weeks) % 2 else {'kind': 'rest'}
check('the planner offers an enterable event in the first block', evt is not None, str(evt))
if inel:
    bad = dict(weeks); bad[inel[0]] = {'kind': 'event', 'event_id': inel[1]['event_id'], 'fallback': {'kind': 'rest'}}
    ver = c.version
    try:
        act(s, {'type': 'plan_block', 'block': [y, w0], 'version': c.version, 'weeks': {str(k): v for k, v in bad.items()},
                'policy': {'selected': 'accept', 'qualifying': 'skip'}}, 'bad')
        check('an ineligible event is refused with its reason', False)
    except CA.CareerError as e:
        check('an ineligible event is refused with its reason', c.version == ver, str(e)[:90])
r = act(s, {'type': 'plan_block', 'block': [y, w0], 'version': c.version, 'weeks': {str(k): v for k, v in weeks.items()},
            'policy': {'selected': 'accept', 'qualifying': 'skip'}}, 'p1')
check('plan accepted', r.get('ok', True) is not False, str(r)[:80])
old_version = c.version - 1
try:
    act(s, {'type': 'plan_block', 'block': [y, w0], 'version': old_version, 'weeks': {}, 'policy': {}}, 'stale')
    check('a stale career version is refused', False)
except CA.StaleCareer:
    check('a stale career version is refused', True)
try:
    s.advance_career('period', expected={'year': 2031, 'week': 9, 'phase': 'week'}, op_key='wrongcursor')
    check('a request for another date is refused', False)
except StaleCursor:
    check('a request for another date is refused', True)
starts_before = s.season.starts_count(c.golfer_id) if hasattr(s.season, 'starts_count') else None
out = s.advance_career('period', op_key='b1')
check('the planned period played', s.cursor['week'] >= 4 or s.cursor['phase'] != 'start', str(s.cursor))
again = s.advance_career('period', op_key='b1')
check('a repeated request is not run twice', again == out)
# --- save and reopen
cur, ver, gid = dict(s.cursor), c.version, c.golfer_id
s.close(); s = Session.open(d); c = s.season.career
check('reopened with the same career and date', c is not None and c.golfer_id == gid and c.version == ver and s.cursor == cur)
# --- through the season to the winter stop
n = 0; decided = []
while True:
    out = s.advance_career('next', op_key=f'n{n}'); n += 1
    pend = c.pending()
    if any(x['kind'] == 'season_end' for x in pend):
        break
    for x in pend:
        if x['kind'] == 'plan':
            b = tuple(x['payload']['block'])
            wk = {str(w): ({'kind': 'train', 'category': 'long_game'} if w % 2 else {'kind': 'rest'}) for w in CA.open_weeks(s.cursor, b[1])}
            act(s, {'type': 'plan_block', 'block': list(b), 'version': c.version, 'weeks': wk,
                    'policy': {'selected': 'accept', 'qualifying': 'skip'}}, f'p{b}')
        elif x['kind'] in ('coach_offer', 'caddie_offer', 'job'):
            act(s, {'type': 'decide', 'decision': x['id'], 'answer': 'decline', 'version': c.version}, f'd{x["id"]}')
            decided.append(x['kind'])
    if n > 80:
        break
check('stops safely before the winter', s.cursor == {'year': 2028, 'week': 52, 'phase': 'end'} and 2029 not in s.season.juniors_added, str(s.cursor))
print('offers answered on the way:', decided, flush=True)
e = next(x for x in c.pending() if x['kind'] == 'season_end')
act(s, {'type': 'decide', 'decision': e['id'], 'answer': 'return_to_ai', 'version': c.version}, 'ai')
check('returned to AI control', c.status == 'ended')
s.advance(2)
check('the world continues under AI past the winter', s.cursor['year'] == 2029 and 2029 in s.season.juniors_added, str(s.cursor))
s.close(); s = Session.open(d)
check('reopened after the handback', s.season.career is not None and s.season.career.status == 'ended' and s.cursor['year'] == 2029)
s.close()
print(f'total {time.time() - t0:.0f} s; {sum(ok for _, ok, _ in checks)}/{len(checks)} checks passed', flush=True)
