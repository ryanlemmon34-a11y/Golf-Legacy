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


def _by_person(d, pid, default=None):
    """(as observer_data.by_person: integer or string keys alike)"""
    v = d.get(pid)
    if v is None:
        v = d.get(str(pid))
    return default if v is None else v

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
            coach, caddie = _by_person(e['team'], pid, (0, 0))
            out.append({'year': int(eid.split(':')[0]), 'week': e['week'], 'event': eid, 'series': e['series'],
                        'pos': pos, 'coach': coach, 'caddie': caddie, 'route': _by_person(e['routes'], pid)})
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
    from golfsim import familiarity as FAM
    peaks = getattr(s, 'peak_overall', {})
    initial = set((session.state.get('archive') or {}).get('initial') or ())   # golfers who were there at the start
    for g in s.world.golfers:
        people[g.id] = {'name': g.name, 'country': g.country, 'born': g.born, 'status': g.status,
                        'lifestyle': g.lifestyle, 'tour': g.tour, 'turned_pro': g.turned_pro, 'roles': ['golfer'],
                        'initial': g.id in initial}
        if g.lifestyle != 'retired':                 # current ratings (overall, then the attributes)
            people[g.id]['ratings'] = (round(g.overall, 1),) + tuple(round(g.attrs[k], 1) for k in ATTRIBUTE_KEYS)
            people[g.id]['archetype'] = g.archetype
        pk = peaks.get(g.id)
        if pk is not None:                            # highest Overall so far: (value, year, week reached by)
            people[g.id]['peak'] = (round(pk[0], 1), pk[1], pk[2])
        people[g.id]['prestige'] = round(s.player_prestige(g.id), 1)   # public standing now (not ability)
        # the ten courses they have played most (course, competitive rounds), most first (rules 2026-11-08)
        people[g.id]['familiar'] = [(k, round(r, 1)) for k, r in FAM.top_courses(g.familiarity)]
        people[g.id]['aggression'] = round(g.personality['aggression'])   # a style, not a grade (rules 2026-11-08)
        people[g.id]['home_club'] = [list(r) for r in getattr(s, 'home_clubs', {}).get(g.id, ())]   # dated
    for kind, table in (('coach', st.coaches), ('caddie', st.caddies)):
        for c in table.values():
            p = people.setdefault(c.id, {'name': c.name, 'country': c.country, 'born': c.born, 'roles': []})
            p['roles'].append(kind)
            p[kind] = {'status': c.status, 'reputation': round(c.reputation, 1), 'background': c.background}
            if kind == 'coach':
                p[kind].update(teaching=round(c.teaching, 1), scouting=round(c.scouting, 1), speciality=c.speciality,
                               youth=c.youth, clients=c.clients)
            elif getattr(c, 'skills', None):
                p[kind]['skills'] = {k: round(v, 1) for k, v in c.skills.items()}
    am_support = {gid: {'band': c['band'], 'cap': c['cap'], 'drawn': round(c['drawn'], 2), 'basis': list(c['basis'])}
                  for gid, c in getattr(s, 'am_support', {}).items()}
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
    from golfsim.course_library import course_place
    courses = {cid: {'name': site['name'], 'city': site['city'], 'country': site['country'], 'class': site['cls'],
                     'subdivision': course_place(site)[1], 'origin': site.get('origin'),
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
        wr_avg=dict(getattr(s, 'wr_avg', {})), first_year=s.first_year, peak_since=getattr(s, 'peak_since', None),
        calendar_version=getattr(s, 'calendar_version', 'v1'),
        major_rights={m: dict(book) for m, book in getattr(s, 'major_rights', {}).get(year, {}).items()},
        rank_top={w_: list(rows) for w_, rows in getattr(s, 'rank_top', {}).get(year, {}).items()},
        wr_seed=dict(getattr(s, 'wr_seed', {})),          # (seeded points: the world's first two seasons only)
        editions=editions, by_person=dict(by_person), schedule=schedule, series=series,
        local_hosting=bool(getattr(s.lib, 'local_first', False)),
        coach_of=dict(st.coach_of), caddie_of=dict(st.caddie_of), am_support=am_support,
        birth=dict(pl.birth), home=dict(pl.home), first=dict(pl.first),
        moves={k: list(v) for k, v in pl.moves.items()}, courses=courses, tours=tours, records=records,
        prize={gid: led.prize for gid, led in s.ledgers.get(year, {}).items()},
        injuries=dict(s.injury_episodes(year)) if hasattr(s, 'injury_episodes') else {},   # this season's, by golfer
        injured_now=sorted(getattr(s, 'injured', {})),
        qual=_qual(s, year, session.cursor),
        **_status(s, year),
        captured=time.time())
    view.capture_seconds = round(time.perf_counter() - t0, 2)
    return view


def _qual(s, year, cursor):
    """This season's majors' qualification as it stands (observer_qual.standing; never stops a capture)."""
    try:
        import observer_qual as OQ
        return OQ.standing(s, year, cursor['week'] if cursor.get('year') == year else 53)
    except Exception:                                    # (a view only)
        return None


def _status(s, year):
    """This season's standing facts (worlds from engines that kept them; empty otherwise): Premier playing
    rights and why, winner's exemptions held (wins so far included), why each holds this season's card,
    the college eligibility ledger, and the rules version the engine plays by."""
    from golfsim.cards import winner_exemptions
    from golfsim.rules import RULES_VERSION
    earned = s.__dict__.get('earned', {}).get(year)
    if earned is None:                                   # computed here, never stored: capture only reads
        earned = winner_exemptions(s, year, through=year)
    return {'rights': {g: tuple(r) for g, r in s.rights.get(year, {}).items()}, 'earned': dict(earned),
            'card_reasons': dict(s.card_reasons.get(year, {})),
            'college': {g: list(v) for g, v in s.__dict__.get('college', {}).items()},
            'rules_version': RULES_VERSION}


def _generation_meta(session):
    try:
        return json.loads((session.dir / f'gen_{session.generation:06d}' / 'meta.json').read_text())
    except (OSError, ValueError):
        return {}
