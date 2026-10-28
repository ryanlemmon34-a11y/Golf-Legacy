"""The history archive: a durable, normalised record of everything that happened in a world.

Three different things are saved in Golf Legacy; this module is the second:

    analysis snapshot   tools/long_world.py: yearly statistics for testing (not a history)
    history archive     this module: the world's history as facts, appended season by season,
                        readable decades later (read-only: it cannot restart the simulation)
    simulation save     savegame.py: the full simulation state, to resume exactly where it stopped

Layout of an archive directory (JSON, gzip):

    world.json          format, seed, years written; catalogues of tours, event series, courses and
                        layouts (stable string ids)
    people.json.gz      every person ever (golfers and staff share one person-id space): name, country,
                        birth year, hometown, when they appeared, and their roles (playing career,
                        coaching career, caddying career)
    relations.json.gz   every coaching, caddying and school-team stint, and each pair's working
                        relationship
    records.json.gz     course records per layout; every mark carries golfer id and event id
    years/YYYY.json.gz  one season: every edition (series, week, venues, finishers per site, and the
                        coach and caddie each golfer had that week), each golfer's season (tour, events,
                        wins, money, rankings, injuries), career decisions with their reasons, staff work,
                        and that season's narrative log lines (display text only)

Facts are stored once and referenced by id (a win is in the edition; a coach's record is derived from
stints and editions), so the archive grows by one season file a year rather than copying data into
profiles. `Archive` reads it back and answers the questions a profile screen will ask.
"""
from __future__ import annotations

import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

from .calendar import TOUR_BY_KEY
from .history import Relations

FORMAT = 'golf-legacy-archive/1'


def _write(path, obj):
    tmp = path.with_suffix(path.suffix + '.tmp')
    with gzip.open(tmp, 'wt') as f:
        json.dump(obj, f, separators=(',', ':'))
    tmp.replace(path)


def _read(path):
    with gzip.open(path, 'rt') as f:
        return json.load(f)


# ---- writing ----------------------------------------------------------------------------------------------
class ArchiveWriter:
    """Writes a season's facts as it completes, and the slowly-changing tables (people, relations,
    records) whenever asked (they are rewritten whole: they hold no per-season copies)."""

    def __init__(self, directory, season):
        self.dir = Path(directory)
        (self.dir / 'years').mkdir(parents=True, exist_ok=True)
        self.created = {g.id: season.first_year for g in season.world.golfers}
        self.initial = {g.id for g in season.world.golfers}
        cal, lib = season.cal, season.lib
        world = {'format': FORMAT, 'seed': season.seed, 'first_year': season.first_year, 'years': [],
                 'tours': {k: {'name': t.name, 'tier': t.tier} for k, t in TOUR_BY_KEY.items()},
                 'series': {s.series_id: {'name': s.name, 'tour': s.tour, 'tier': s.tier, 'kind': s.kind,
                                          'category': s.category} for s in cal.series},
                 'courses': {cid: {'name': site['name'], 'city': site['city'], 'country': site['country'],
                                   'class': site['cls'], 'architect': site.get('architect'), 'opened': site.get('opened'),
                                   'layouts': {k: {'par': c.par, 'yards': c.yards} for k, c in site['layouts'].items()}}
                             for cid, site in lib.sites.items()}}
        p = self.dir / 'world.json'
        if p.exists():
            world['years'] = json.loads(p.read_text())['years']
        self.world = world
        p.write_text(json.dumps(world))

    def write_year(self, season, year):
        """Call after season.run_year(year), before the season's snapshot is discarded."""
        snap = season.snapshots.get(year, {})
        for g in season.world.golfers:
            self.created.setdefault(g.id, year + 1)
        events = []
        for r in season.results.values():
            if r.year != year:
                continue
            events.append({'id': r.event_id, 'series': r.series_id, 'week': r.week, 'sites': r.sites,
                           'prestige': round(r.prestige, 2), 'playoff': r.playoff, 'finish': r.finish,
                           'team': {str(g): list(t) for g, t in r.team.items()}})
        careers = {}
        for gid, row in snap.items():
            careers[gid] = {k: row.get(k) for k in ('tour', 'tier', 'status', 'lifestyle', 'events', 'wins', 'top10',
                                                    'cuts', 'majors', 'prize', 'net', 'wr_start', 'wr_end', 'am_start',
                                                    'am_end', 'injury_weeks', 'promoted', 'demoted', 'next_tour',
                                                    'zero_start_reason')}
            careers[gid]['prize'] = round(careers[gid]['prize'] or 0)
            careers[gid]['net'] = round(careers[gid]['net'] or 0)
        log = {gid: [(w, t) for y, w, t in h if y == year] for gid, h in season.history.items()}
        chunk = {'year': year, 'events': events, 'careers': careers,
                 'transitions': season.transitions.get(year, []),
                 'staff_year': {f'{k}:{i}': v for (k, i), v in season.staff_year.get(year, {}).items()},
                 'log': {g: v for g, v in log.items() if v}}
        _write(self.dir / 'years' / f'{year}.json.gz', chunk)
        if year not in self.world['years']:
            self.world['years'].append(year)
            (self.dir / 'world.json').write_text(json.dumps(self.world))

    def write_state(self, season):
        st = season.staff
        people = {}
        for g in season.world.golfers:
            people[g.id] = {'name': g.name, 'country': g.country, 'born': g.born, 'hometown': g.hometown,
                            'created': self.created.get(g.id), 'initial': g.id in self.initial,
                            'golfer': {'status': g.status, 'lifestyle': g.lifestyle, 'tour': g.tour,
                                       'turned_pro': g.turned_pro}}
        for c in st.coaches.values():
            p = people.setdefault(c.id, {'name': c.name, 'country': c.country, 'born': c.born, 'hometown': None})
            p['coach'] = {'speciality': c.speciality, 'youth': c.youth, 'reputation': c.reputation, 'clients': c.clients,
                          'background': c.background, 'status': c.status, 'earnings': round(c.earnings),
                          'history': c.history}
        for k in st.caddies.values():
            p = people.setdefault(k.id, {'name': k.name, 'country': k.country, 'born': k.born, 'hometown': None})
            p['caddie'] = {'reputation': k.reputation, 'background': k.background, 'status': k.status,
                           'earnings': round(k.earnings), 'seasons': k.seasons, 'history': k.history}
        _write(self.dir / 'people.json.gz', people)
        _write(self.dir / 'relations.json.gz', st.rel.export())
        _write(self.dir / 'records.json.gz', season.records.to_dict())


def write_archive(season, directory, years=None):
    """Write a whole archive from a season that still holds its snapshots (tests, short runs)."""
    w = ArchiveWriter(directory, season)
    for y in sorted(years or season.snapshots):
        w.write_year(season, y)
    w.write_state(season)
    return Path(directory)


# ---- reading ----------------------------------------------------------------------------------------------
class Archive:
    """A world's history, read back. Every answer refers to people, events and courses by id."""

    def __init__(self, directory):
        self.dir = Path(directory)
        self.world = json.loads((self.dir / 'world.json').read_text())
        if self.world.get('format') != FORMAT:
            raise ValueError(f'archive format {self.world.get("format")} is not {FORMAT}')
        self.people = {int(k): v for k, v in _read(self.dir / 'people.json.gz').items()}
        self.rel = Relations.load(_read(self.dir / 'relations.json.gz'))
        self.records = _read(self.dir / 'records.json.gz')
        self.years = sorted(self.world['years'])
        self._years = {}

    def year(self, y):
        if y not in self._years:
            d = _read(self.dir / 'years' / f'{y}.json.gz')
            d['careers'] = {int(k): v for k, v in d['careers'].items()}
            for e in d['events']:
                e['team'] = {int(k): tuple(v) for k, v in e['team'].items()}
            self._years[y] = d
        return self._years[y]

    def events(self):
        for y in self.years:
            for e in self.year(y)['events']:
                yield y, e

    # -- people -------------------------------------------------------------------------------------------
    def name(self, pid):
        p = self.people.get(pid)
        return f'{p["name"]} ({p["country"]})' if p else f'#{pid}'

    def find(self, name):
        """Person ids with this name (names are not unique; ids are)."""
        return sorted(pid for pid, p in self.people.items() if p['name'] == name)

    def roles(self, pid):
        p = self.people[pid]
        return [r for r in ('golfer', 'coach', 'caddie') if r in p]

    def playing_career(self, pid):
        """Season by season: [(year, row)] for every season they competed."""
        return [(y, self.year(y)['careers'][pid]) for y in self.years if pid in self.year(y)['careers']]

    def results(self, pid):
        """Every event they played, with the team they had that week:
        [{year, week, event, series, pos (None = missed cut), coach, caddie}]."""
        out = []
        for y, e in self.events():
            for site in e['finish']:
                for gid, pos, _ in site:
                    if gid == pid:
                        coach, caddie = e['team'].get(pid, (0, 0))
                        out.append({'year': y, 'week': e['week'], 'event': e['id'], 'series': e['series'],
                                    'pos': pos, 'coach': coach, 'caddie': caddie})
        return out

    def golfer_staff(self, pid):
        """Everyone who coached or caddied for this golfer (and school teams), in order."""
        return sorted(self.rel.of_golfer(pid), key=lambda s: (s.start, s.id))

    def staff_clients(self, pid, kind=None):
        """Each stint this person worked as a coach or caddie, with the client's results *while this
        person was on their team* (from the team recorded with each result, not from current
        assignments)."""
        out = []
        cache = {}
        for s in sorted(self.rel.of_staff(pid, kind), key=lambda s: (s.start, s.id)):
            if s.golfer not in cache:
                cache[s.golfer] = self.results(s.golfer)
            role = 'coach' if s.kind == 'coach' else 'caddie'
            during = [r for r in cache[s.golfer] if r[role] == pid and (r['year'], r['week']) >= s.start
                      and (s.end is None or (r['year'], r['week']) < s.end)]
            wins = [r for r in during if r['pos'] == 1]
            out.append({'stint': s, 'starts': len(during), 'wins': [r['event'] for r in wins],
                        'majors': [r['event'] for r in wins if self.world['series'][r['series']]['kind'] == 'major']})
        return out

    def team_at(self, pid, event_id):
        """(coach, caddie) on this golfer's team at that event."""
        y = int(event_id.split(':')[0])
        e = next(e for e in self.year(y)['events'] if e['id'] == event_id)
        return e['team'].get(pid, (0, 0))

    # -- courses ------------------------------------------------------------------------------------------
    def course(self, course_id):
        """Editions played at a course (with winners) and its layouts' records (with golfer ids)."""
        held = []
        for y, e in self.events():
            for i, (cid, layout, city) in enumerate(e['sites']):
                if cid == course_id:
                    winner = next((g for g, p, _ in e['finish'][i] if p == 1), None) if i < len(e['finish']) else None
                    held.append({'year': y, 'event': e['id'], 'layout': layout, 'winner': winner})
        recs = {lid: r for lid, r in self.records.items() if lid.split(':')[0] == course_id}
        return {'course': self.world['courses'].get(course_id), 'editions': held, 'records': recs}

    # -- a season, from facts -----------------------------------------------------------------------------
    def recap(self, y):
        """The season's headline facts, each with the ids it refers to."""
        d = self.year(y)
        facts = []
        for e in sorted(d['events'], key=lambda e: e['week']):
            meta = self.world['series'][e['series']]
            if meta['kind'] == 'major' and e['finish'] and e['finish'][0]:
                w = next((g for g, p, _ in e['finish'][0] if p == 1), None)
                if w:
                    coach, caddie = e['team'].get(w, (0, 0))
                    facts.append({'fact': 'major', 'event': e['id'], 'golfer': w, 'coach': coach, 'caddie': caddie,
                                  'text': f'{meta["name"]}: {self.name(w)}'
                                          + (f', coached by {self.name(coach)}' if coach else '')
                                          + (f', caddie {self.name(caddie)}' if caddie else '')})
        no1 = [g for g, r in d['careers'].items() if r.get('wr_end') == 1]
        if no1:
            prev = [g for g, r in self.year(y - 1)['careers'].items() if r.get('wr_end') == 1] if y - 1 in self.years else []
            if no1 != prev:
                facts.append({'fact': 'number one', 'golfer': no1[0], 'text': f'New world No.1: {self.name(no1[0])}'})
        kinds = Counter(t['kind'] for t in d['transitions'])
        for t in d['transitions']:
            if t['kind'] in ('became coach', 'became caddie'):
                facts.append({'fact': t['kind'], 'golfer': t['gid'], 'text': f'{self.name(t["gid"])} {t["kind"]} at {t["age"]}'})
            if t['kind'] == 'comeback':
                facts.append({'fact': 'comeback', 'golfer': t['gid'], 'text': f'{self.name(t["gid"])} came back at {t["age"]}'})
        facts.append({'fact': 'counts', 'counts': dict(kinds),
                      'text': ', '.join(f'{n} {k}' for k, n in sorted(kinds.items()))})
        return facts
