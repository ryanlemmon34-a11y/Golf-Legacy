"""What the observer's pages read of the running world: a snapshot of one committed generation, as plain
data, captured from the session while nothing is advancing it.

The session's Season is the simulation itself: an advance mutates it week by week, so a page drawn
during an advance must not read it. Instead, every time the world is at a committed point (opened,
refreshed, an advance finished or failed and went back to what is committed), the observer captures
this view and draws every page from it and from the published history of the same generation. During
an advance the pages keep showing that snapshot, which names its generation and date.

The current season's editions are captured with `archive.edition_record`, the same record the season
file keeps, so an edition reads the same before and after its season is archived; only seasons the
published history does not hold yet are captured (nothing is counted twice).
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LiveView:
    """The committed world, as plain data (never mutated after capture)."""

    def __init__(self, **kw):
        self.__dict__.update(kw)

    # people ------------------------------------------------------------------------------------------------
    def name(self, pid):
        p = self.people.get(pid)
        return f'{p["name"]} ({p["country"]})' if p else None

    def geography(self, pid):
        """Like Archive.geography, as of the snapshot (None if the person's places were never recorded)."""
        if pid not in self.home:
            return None
        f = self.first.get(pid)
        return {'nationality': self.people.get(pid, {}).get('country'), 'birthplace': _p(self.birth.get(pid)),
                'residence': _p(self.home.get(pid)),
                'first_residence': {'year': f[0], 'week': f[1], 'place': _p(f[2]), 'note': f[3]} if f else None,
                'moves': [{'year': y, 'week': w, 'from': _p(a), 'to': _p(b), 'reason': r}
                          for y, w, a, b, r in self.moves.get(pid, ())]}

    def results(self, pid):
        """The person's starts in the captured editions, in Archive.results' form."""
        out = []
        for eid, site, pos in self.by_person.get(pid, ()):
            e = self.editions[eid]
            coach, caddie = e['team'].get(str(pid), (0, 0))
            out.append({'year': int(eid.split(':')[0]), 'week': e['week'], 'event': eid, 'series': e['series'],
                        'pos': pos, 'coach': coach, 'caddie': caddie, 'route': e['routes'].get(str(pid))})
        return out


def _p(place):
    return {'country': place[0], 'region': place[1]} if place else None


def capture(session):
    """The view of `session` as it stands (call only while nothing advances it: it is read whole). Its
    editions are those of seasons the generation's own history does not hold yet (that history -- the
    one published with it -- holds the rest)."""
    from golfsim.archive import edition_record
    t0 = time.perf_counter()
    s = session.season
    st = s.staff
    archived = set(session._history_years())
    people = {}
    from golfsim.ratings import ATTRIBUTE_KEYS
    for g in s.world.golfers:
        people[g.id] = {'name': g.name, 'country': g.country, 'born': g.born, 'status': g.status,
                        'lifestyle': g.lifestyle, 'tour': g.tour, 'turned_pro': g.turned_pro, 'roles': ['golfer']}
        if g.lifestyle != 'retired':                 # current ratings (overall, then the attributes)
            people[g.id]['ratings'] = (round(g.overall, 1),) + tuple(round(g.attrs[k], 1) for k in ATTRIBUTE_KEYS)
            people[g.id]['archetype'] = g.archetype
    for kind, table in (('coach', st.coaches), ('caddie', st.caddies)):
        for c in table.values():
            p = people.setdefault(c.id, {'name': c.name, 'country': c.country, 'born': c.born, 'roles': []})
            p['roles'].append(kind)
            p[kind] = {'status': c.status, 'reputation': round(c.reputation, 1), 'background': c.background}
    editions, by_person = {}, defaultdict(list)
    for r in s.results.values():
        if r.year in archived:
            continue
        e = edition_record(s, r)
        e = {**e, 'sites': [list(x) for x in e['sites']], 'finish': [[list(row) for row in site] for site in e['finish']]}
        editions[r.event_id] = e
        for k, site in enumerate(e['finish']):
            for gid, pos, _ in site:
                by_person[gid].append((r.event_id, k, pos))
    for rows in by_person.values():
        rows.sort(key=lambda x: (editions[x[0]]['week'], x[0]))
    year = session.cursor['year']
    held = {eid for eid in editions}
    unheld = set(s.unheld.get(year, []))
    schedule = []
    for ed in s.cal.editions(year):
        ser = ed.series
        status = 'played' if ed.event_id in held else 'not held' if ed.event_id in unheld else 'scheduled'
        schedule.append({'id': ed.event_id, 'series': ser.series_id, 'week': ser.week, 'name': ser.name,
                         'tour': ser.tour, 'tier': ser.tier, 'kind': ser.kind, 'category': ser.category,
                         'city': ed.city, 'country': ed.country, 'rounds': ser.rounds,
                         'match_play': bool(ser.match_play), 'status': status})
    series = {x.series_id: {'name': x.name, 'tour': x.tour, 'tier': x.tier, 'kind': x.kind, 'category': x.category}
              for x in s.cal.series}
    pl = s.places
    meta = _generation_meta(session)
    from golfsim.calendar import TOUR_BY_KEY
    courses = {cid: {'name': site['name'], 'city': site['city'], 'country': site['country'], 'class': site['cls'],
                     'architect': site.get('architect'), 'opened': site.get('opened'),
                     'layouts': {k: {'par': c.par, 'yards': c.yards} for k, c in site['layouts'].items()}}
               for cid, site in s.lib.sites.items()}
    tours = {k: {'name': t.name, 'tier': t.tier} for k, t in TOUR_BY_KEY.items()}
    records = json.loads(json.dumps(s.records.to_dict()))
    view = LiveView(
        world_id=session.state.get('world_id'), seed=session.state.get('seed', getattr(s, 'seed', None)),
        cursor=session.cursor, generation=session.generation, history_generation=session.history_generation,
        history_years=sorted(archived), weeks_played=session.state.get('weeks_played'), engine=meta.get('engine'), commit=meta.get('commit'),
        written=meta.get('written'), year=year, people=people, wr=dict(s.wr_pos), am=dict(s.am_pos),
        editions=editions, by_person=dict(by_person), schedule=schedule, series=series,
        coach_of=dict(st.coach_of), caddie_of=dict(st.caddie_of),
        birth=dict(pl.birth), home=dict(pl.home), first=dict(pl.first),
        moves={k: list(v) for k, v in pl.moves.items()}, courses=courses, tours=tours, records=records,
        prize={gid: led.prize for gid, led in s.ledgers.get(year, {}).items()},
        captured=time.time())
    view.capture_seconds = round(time.perf_counter() - t0, 2)
    return view


def _generation_meta(session):
    try:
        return json.loads((session.dir / f'gen_{session.generation:06d}' / 'meta.json').read_text())
    except (OSError, ValueError):
        return {}
