"""Career event participation on a FULL-SIZE world (model/API, through Session): plan genuinely eligible, affordable
events under the normal rules, play, and find one the golfer actually entered, with its recorded result. No entry is
forced and no rule is changed: if the field fills, the fallback applies and the next attempt is a later week.
usage: python career_event_full.py ROOT BOUNDARY_DIR WORKDIR"""
import shutil
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve(); BOUND = Path(sys.argv[2]); WORK = Path(sys.argv[3])
sys.path.insert(0, str(ROOT))
from golfsim import career as CA                                         # noqa: E402
from golfsim.season import Season                                        # noqa: E402
from golfsim.session import Session                                      # noqa: E402

if WORK.exists(): shutil.rmtree(WORK)
shutil.copytree(BOUND, WORK / 'w')
d = WORK / 'w'
s = Session.open(d)
s.career_action({'schema': CA.SCHEMA, 'type': 'new_career'}, op_key='new')
c = s.season.career; gid = c.golfer_id; g = s.season.g[gid]
print(f'controlled golfer {g.name} ({g.country}), status {g.status}, tour {g.tour}, rating {g.overall:.1f}')
# the normal entry priority is computed for the controlled golfer like everyone (spy, no change to its value)
seen = []
real = Season.priority
def spy(self, x, ser):
    if x.id == gid: seen.append(ser.id if hasattr(ser, 'id') else str(ser))
    return real(self, x, ser)
Season.priority = spy
planned, played = [], []
n = 0
while not played and n < 60:
    out = s.advance_career('next', op_key=f'n{n}'); n += 1
    pend = c.pending()
    if any(x['kind'] == 'season_end' for x in pend):
        break
    for x in pend:
        if x['kind'] in ('coach_offer', 'caddie_offer', 'job'):
            s.career_action({'schema': CA.SCHEMA, 'type': 'decide', 'decision': x['id'], 'answer': 'decline',
                             'version': c.version}, op_key=f'd{x["id"]}')
    for x in c.pending(('plan',)):
        y, w0 = x['payload']['block']
        pl = CA.planner(s.season, s.cursor, y, w0)
        weeks = {}
        for wk in pl['weeks']:
            evs = [e for e in wk['events'] if e['eligible'] and e.get('affordable')]
            if evs:
                e = sorted(evs, key=lambda e: (-e['tier'], e['event_id']))[0]     # the least prestigious open event
                weeks[str(wk['week'])] = {'kind': 'event', 'event_id': e['event_id'],
                                          'fallback': {'kind': 'train', 'category': 'putting'}}
                planned.append((y, wk['week'], e['event_id'], e['name'], e['tier']))
            else:
                weeks[str(wk['week'])] = {'kind': 'train', 'category': 'putting'}
        s.career_action({'schema': CA.SCHEMA, 'type': 'plan_block', 'block': [y, w0], 'version': c.version,
                         'weeks': weeks, 'policy': {'selected': 'accept', 'qualifying': 'skip'}}, op_key=f'p{y}-{w0}')
    out = s.advance_career('period', op_key=f'per{n}')
    for (y, w, eid, name, tier) in planned:
        r = s.season.results.get(eid)
        if r and any(row[0] == gid for site in r.finish for row in site) and (y, w, eid) not in [p[:3] for p in played]:
            row = next(row for site in r.finish for row in site if row[0] == gid)
            played.append((y, w, eid, name, tier, row[1], row[2], len([1 for site in r.finish for _ in site])))
Season.priority = real
print('planned events:', len(planned), planned[:6])
notes = [n_ for n_ in c.notices if n_['kind'] == 'entry']
print('entry notices:', len(notes)); [print('  ', n_['text'][:160]) for n_ in notes[:6]]
print('priority computed for the golfer in', len(seen), 'entry orderings')
if played:
    y, w, eid, name, tier, pos, total, field = played[0]
    print(f'PLAYED: {name} ({eid}), week {w} of {y}, tier {tier}: finished {pos} with {total} in a field of {field}')
    cur = dict(s.cursor); s.close(); s = Session.open(d)
    r = s.season.results.get(eid)
    kept = r is not None and any(row[0] == gid for site in r.finish for row in site)
    car_rows = s.season.career
    print('after save and reopen: result kept', kept, '| cursor', s.cursor == cur, '| activity of that week recorded:',
          getattr(s.season, 'week_activity', {}).get(gid))
    starts = sum(1 for e in s.season.results.values() if any(row[0] == gid for site in e.finish for row in site))
    print('golfer starts this season so far:', starts)
else:
    print('NO EVENT ENTERED in', n, 'stops')
s.close()
