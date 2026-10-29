"""The history archive: a durable, normalised record of everything that happened in a world.

Three different things are saved in Golf Legacy; this module is the second:

    analysis snapshot   tools/long_world.py: yearly statistics for testing (not a history)
    history archive     this module: the world's history as facts, appended season by season,
                        readable decades later (read-only: it cannot restart the simulation)
    simulation save     savegame.py: the full simulation state, to resume exactly where it stopped

Layout of an archive directory (JSON, gzip):

    world.json          format, seed, years written; catalogues of tours, event series, courses and
                        layouts (stable string ids)
    people.json.gz      every person ever (golfers and staff share one person-id space): name, country
                        (nationality, fixed for life), birth year, hometown, birthplace and residence
                        (country and state / province; None when unknown), every dated move (from, to,
                        reason), when they appeared, and their roles (playing career, coaching career,
                        caddying career)
    relations.json.gz   every coaching, caddying and school-team stint, and each pair's working
                        relationship
    records.json.gz     course records per layout; every mark carries golfer id and event id
    years/YYYY.json.gz  one season: every edition (series, week, venues, finishers per site, and the
                        coach and caddie each golfer had that week), each golfer's season (tour, events,
                        wins, money -- net, income and costs as finally settled after winter expenses,
                        with net_at_decision, the figure the career decisions saw -- rankings, injuries,
                        where they lived that season), career decisions
                        with their reasons, that winter's moves, staff work, and that season's narrative
                        log lines (display text only)

Facts are stored once and referenced by id (a win is in the edition; a coach's record is derived from
stints and editions), so the archive grows by one season file a year rather than copying data into
profiles. `Archive` reads it back and answers the questions a profile screen will ask.
"""
from __future__ import annotations

import gzip
import json
import sqlite3
import time
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

from .calendar import TOUR_BY_KEY
from .history import Relations

FORMAT = 'golf-legacy-archive/1'


def _write(path, obj):
    tmp = path.with_suffix(path.suffix + '.tmp')
    text = json.dumps(obj, separators=(',', ':'))        # the C encoder (json.dump streams through the slow
    with gzip.open(tmp, 'wt', compresslevel=6) as f:    # pure-Python one); the same text, a little larger file
        f.write(text)
    tmp.replace(path)


def _read(path):
    with gzip.open(path, 'rt') as f:
        return json.load(f)


# ---- writing ----------------------------------------------------------------------------------------------
class ArchiveWriter:
    """Writes a season's facts as it completes, and the slowly-changing tables (people, relations,
    records) whenever asked (they are rewritten whole: they hold no per-season copies)."""

    def __init__(self, directory, season, touch=True):
        """`touch=False`: read the archive's state without writing anything (the session stages a
        season's files in its checkpoint and publishes them only once the checkpoint is committed)."""
        self.dir = Path(directory)
        if touch:
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
        if touch:
            p.write_text(json.dumps(world))

    def write_year(self, season, year):
        """Call after season.run_year(year), before the season's snapshot is discarded."""
        chunk = self.year_chunk(season, year)
        _write(self.dir / 'years' / f'{year}.json.gz', chunk)
        index_season(self.dir, year, chunk)
        if year not in self.world['years']:
            self.world['years'].append(year)
            (self.dir / 'world.json').write_text(json.dumps(self.world))

    def year_chunk(self, season, year):
        """One season's facts, as written to years/YYYY.json.gz (nothing is written here)."""
        snap = season.snapshots.get(year, {})
        for g in season.world.golfers:
            self.created.setdefault(g.id, year + 1)
        events = []
        for r in season.results.values():
            if r.year != year:
                continue
            routes = season.event_routes.get(year, {}).get(r.event_id) or season.entry_routes.get((year, r.series_id), {})
            ser = season.cal.by_id[r.series_id]
            events.append({'id': r.event_id, 'series': r.series_id, 'week': r.week, 'sites': r.sites,
                           # classification when it was played: later calendar changes never rewrite it
                           'name': ser.name, 'tour': ser.tour, 'tier': ser.tier, 'category': ser.category,
                           'prestige': round(r.prestige, 2), 'playoff': r.playoff, 'finish': r.finish,
                           'team': {str(g): list(t) for g, t in r.team.items()},
                           'routes': {str(g): v for g, v in routes.items()}})
        careers = {}
        for gid, row in snap.items():
            careers[gid] = {k: row.get(k) for k in ('tour', 'tier', 'status', 'lifestyle', 'events', 'wins', 'top10',
                                                    'cuts', 'majors', 'prize', 'net', 'wr_start', 'wr_end', 'am_start',
                                                    'am_end', 'injury_weeks', 'promoted', 'demoted', 'next_tour',
                                                    'zero_start_reason')}
            careers[gid]['rights'] = season.rights.get(year, {}).get(gid)          # Premier status at entry, why
            careers[gid]['access'] = dict(season.week_access.get(year, {}).get(gid, {}))
            careers[gid]['denied'] = season.access_log.get(year, {}).get(gid, [])   # (week, outcome, wanted, played)
            home = season.places.residence_at(gid, year, 52)                     # where they lived that season
            careers[gid]['residence'] = list(home) if home else None
            careers[gid]['prize'] = round(careers[gid]['prize'] or 0)
            # the season's money as finally settled (after winter expenses such as a move, and the support
            # drawn for them); the figure the career decisions saw, before the winter, is kept beside it
            careers[gid]['net_at_decision'] = round(careers[gid]['net'] or 0)
            led = season.ledgers.get(year, {}).get(gid)
            if led is not None:
                careers[gid].update({'net': round(led.net), 'income': round(led.income), 'costs': round(led.costs),
                                     'support': round(led.support), 'backer_support': round(led.backer_support),
                                     'moving': round(led.moving)})
            else:
                careers[gid]['net'] = careers[gid]['net_at_decision']
        log = {gid: [(w, t) for y, w, t in h if y == year] for gid, h in season.history.items()}
        chunk = {'year': year, 'events': events, 'careers': careers,
                 'transitions': season.transitions.get(year, []),
                 'moves': [dict(m, **{'from': list(m['from']) if m['from'] else None, 'to': list(m['to'])})
                           for m in season.move_log.get(year, [])],
                 'unheld': list(season.unheld.get(year, [])),          # scheduled, but nobody entered
                 'moments': list(season.moments.get(year, [])),        # aces, albatrosses, playoffs, course records
                 # each week's top 100 of the world and amateur rankings (No. 1 = first): weeks at No. 1,
                 # as-of views
                 'rankings': {kind: {str(w): table.get((year, w), [])[:100] for w in range(1, 53)
                                     if (year, w) in table}
                              for kind, table in (('world', season.ctx.world_rankings),
                                                  ('amateur', season.ctx.amateur_rankings))},
                 'staff_year': {f'{k}:{i}': v for (k, i), v in season.staff_year.get(year, {}).items()},
                 'log': {g: v for g, v in log.items() if v}}
        return chunk

    def write_state(self, season):
        for name, table in self.state_tables(season).items():
            _write(self.dir / name, table)

    def state_tables(self, season):
        """The slowly-changing tables: {file name: contents} (nothing is written here)."""
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
        places = getattr(season, 'places', None)
        for pid, p in people.items():                 # one geography per person, whatever their roles
            p['nationality'] = p['country']
            p.update(places.export(pid) if places else {'birthplace': None, 'residence': None,
                                                        'first_residence': None, 'moves': []})
        return {'people.json.gz': people, 'relations.json.gz': st.rel.export(),
                'records.json.gz': season.records.to_dict()}


STATE_FILES = ('people.json.gz', 'relations.json.gz', 'records.json.gz')


def index_season(directory, year, chunk):
    """Index one season (idempotent: the season's rows are replaced), exactly as it reads back from disk."""
    from .archive_index import ArchiveIndex
    with ArchiveIndex(Path(directory) / 'index.sqlite') as idx:
        idx.index_year(year, json.loads(json.dumps(chunk)))


def write_archive(season, directory, years=None):
    """Write a whole archive from a season that still holds its snapshots (tests, short runs)."""
    w = ArchiveWriter(directory, season)
    for y in sorted(years or season.snapshots):
        w.write_year(season, y)
    w.write_state(season)
    return Path(directory)


# ---- reading ----------------------------------------------------------------------------------------------
class ArchiveChanged(RuntimeError):
    """A season file this snapshot refers to was removed or republished since it was opened (recovery
    rolled the history back): open a new Archive (the observer does, and draws the page again)."""


def published_stamp(directory):
    """What identifies the published history: the PUBLISHED generation and the season list (a session
    publishes season files and index rows, then the tables, then the season list, then PUBLISHED;
    recovery trims the index, then the season list)."""
    d = Path(directory)
    try:
        pub = (d / 'PUBLISHED').read_text()
    except FileNotFoundError:
        pub = None
    try:
        years = json.loads((d / 'world.json').read_text()).get('years')
    except FileNotFoundError:
        years = None
    return pub, tuple(sorted(years or ()))


class Archive:
    """A world's history, read back: one consistent snapshot of what was published when it was opened.
    Its files and its index agree on one published generation, and every answer is limited to its
    seasons, however much the session publishes meanwhile (a newer generation is a new Archive). Every
    answer refers to people, events and courses by id. Close it when replaced (`close`, or `with`)."""

    OPEN_ATTEMPTS = 10

    def __init__(self, directory):
        self.dir = Path(directory)
        self.index = None
        for attempt in range(self.OPEN_ATTEMPTS):
            index = None
            try:
                stamp = published_stamp(self.dir)
                self._load_files()
                index = self._open_index()
                sigs = {y: self._signature(y) for y in self.years}    # the season files of this snapshot
                same = published_stamp(self.dir) == stamp and tuple(self.years) == stamp[1]
            except (OSError, ValueError, EOFError):     # a table replaced or the list rewritten as it was read
                same = False
                if attempt == self.OPEN_ATTEMPTS - 1:
                    raise
            if same and (index is not None or attempt >= 3):
                break                                   # nothing was published while it was read (an index
                #                                         that does not match is retried, then not used)
            if index is not None:
                index.close()
            if attempt == self.OPEN_ATTEMPTS - 1:
                raise RuntimeError(f'{self.dir}: the history kept changing while it was read')
            time.sleep(0.05 * (attempt + 1))
        self.stamp = stamp
        self.index = index
        self._sigs = sigs

    def _load_files(self):
        self.world = json.loads((self.dir / 'world.json').read_text())
        if self.world.get('format') != FORMAT:
            raise ValueError(f'archive format {self.world.get("format")} is not {FORMAT}')
        self.people = {int(k): v for k, v in _read(self.dir / 'people.json.gz').items()}
        self.rel = Relations.load(_read(self.dir / 'relations.json.gz'))
        self.records = _read(self.dir / 'records.json.gz')
        self.years = sorted(self.world['years'])
        self._years = OrderedDict()                     # the few seasons decoded most recently (CACHE_SEASONS)

    def _open_index(self):
        """The index as a reader pinned to this snapshot, if it covers exactly these seasons (else the
        season files answer)."""
        if not (self.dir / 'index.sqlite').exists():
            return None
        from .archive_index import ArchiveIndex
        idx = ArchiveIndex(self.dir / 'index.sqlite', reader=True)
        try:
            idx.snapshot()
            if self.years and idx.years() == self.years:
                idx.through = self.years[-1]
                return idx
        except sqlite3.Error:                            # e.g. an index still being created
            pass
        idx.close()
        return None

    def close(self):
        """Release the index connection (and its snapshot) and the decoded seasons."""
        if self.index is not None:
            self.index.close()
            self.index = None
        self._years.clear()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def signature(self, y):
        """What identifies a season file as written (size, modification time, inode): a season published
        again (after a recovery fell back to an earlier checkpoint) has a new one. This snapshot's own."""
        return self._sigs[y] if y in getattr(self, '_sigs', {}) else self._signature(y)

    def _signature(self, y):
        try:
            st = (self.dir / 'years' / f'{y}.json.gz').stat()
        except FileNotFoundError:
            return None
        return st.st_size, st.st_mtime_ns, st.st_ino

    CACHE_SEASONS = 4                # decoded seasons kept in memory (a season decodes to hundreds of MB late on)

    def year(self, y):
        """One season, decoded (a bounded cache keeps the most recently used few)."""
        if y in self._years:
            self._years.move_to_end(y)
            return self._years[y]
        if y in self._sigs and self._signature(y) != self._sigs[y]:
            raise ArchiveChanged(f'season {y} was removed or republished after this history was opened')
        d = _read(self.dir / 'years' / f'{y}.json.gz')
        if y in self._sigs and self._signature(y) != self._sigs[y]:       # replaced while it was read
            raise ArchiveChanged(f'season {y} was republished while it was read')
        d['careers'] = {int(k): v for k, v in d['careers'].items()}
        for e in d['events']:
            e['team'] = {int(k): tuple(v) for k, v in e['team'].items()}
            e['routes'] = {int(k): v for k, v in e.get('routes', {}).items()}
        self._years[y] = d
        while len(self._years) > self.CACHE_SEASONS:
            self._years.popitem(last=False)
        return d

    def events(self, years=None):
        """(year, edition) for every edition, or only those of `years` (only those seasons are read)."""
        for y in (self.years if years is None else years):
            for e in self.year(y)['events']:
                yield y, e

    # -- people -------------------------------------------------------------------------------------------
    def name(self, pid):
        p = self.people.get(pid)
        return f'{p["name"]} ({p["country"]})' if p else f'#{pid}'

    def find(self, name):
        """Person ids with this name (names are not unique; ids are)."""
        return sorted(pid for pid, p in self.people.items() if p['name'] == name)

    def residence_at(self, pid, year, week=53):
        """Where a person lived at (year, week), from their dated moves (None if unknown): never today's
        address for an earlier season."""
        p = self.people.get(pid) or {}
        first = p.get('first_residence')
        if first is None or (year, week) < (first['year'], first['week']):
            return None                                 # unknown: before their first known residence
        place = first['place']
        for m in p.get('moves', ()):
            if (m['year'], m['week']) <= (year, week):
                place = m['to']
        return place

    def geography(self, pid):
        """Nationality, birthplace, current residence and residence history (None = unknown)."""
        p = self.people[pid]
        return {'nationality': p.get('nationality', p.get('country')), 'birthplace': p.get('birthplace'),
                'residence': p.get('residence'), 'first_residence': p.get('first_residence'),
                'moves': p.get('moves', [])}

    def roles(self, pid):
        p = self.people[pid]
        return [r for r in ('golfer', 'coach', 'caddie') if r in p]

    def playing_career(self, pid):
        """Season by season: [(year, row)] for every season they competed (the index says which seasons,
        so only those are read)."""
        if self.index is not None and self.index.derived_complete(self.years):
            return self.index.career(pid)               # one query (rows exactly as in the season files)
        return [(y, self.year(y)['careers'][pid]) for y in self.years if pid in self.year(y)['careers']]

    def results(self, pid):
        """Every event they played, with the team they had that week:
        [{year, week, event, series, pos (None = missed cut), coach, caddie, route}]; route is how they
        got in, with their status at entry (e.g. 'PREMIER CONDITIONAL', 'ORDER OF MERIT 12', 'COLLEGE LINEUP').
        Answered from the index when there is one (one query), otherwise by reading every season."""
        if self.index is not None:
            return self.index.results(pid)
        out = []
        for y, e in self.events():
            for site in e['finish']:
                for gid, pos, _ in site:
                    if gid == pid:
                        coach, caddie = e['team'].get(pid, (0, 0))
                        out.append({'year': y, 'week': e['week'], 'event': e['id'], 'series': e['series'],
                                    'pos': pos, 'coach': coach, 'caddie': caddie, 'route': e['routes'].get(pid)})
        return out

    def ranking(self, year, week, amateur=False):
        """The top 100 of the world (or amateur) ranking after that week: [person ids], No. 1 first."""
        return self.year(year).get('rankings', {}).get('amateur' if amateur else 'world', {}).get(str(week), [])

    def weeks_at_number_one(self, amateur=False):
        """{person id: weeks at No. 1} over the archive's coverage."""
        out = {}
        kind = 'amateur' if amateur else 'world'
        if self.index is not None and self.index.derived_complete(self.years):
            for pid, n in self.index.db.execute('SELECT person, COUNT(*) FROM number_one WHERE kind = ?'
                                                + self.index.upto() + ' GROUP BY person', (kind,)):
                out[pid] = n
            return out
        for y in self.years:
            for top in self.year(y).get('rankings', {}).get(kind, {}).values():
                if top:
                    out[top[0]] = out.get(top[0], 0) + 1
        return out

    def moments(self, year=None, kind=None, person=None):
        """Special moments as facts: holes-in-one, albatrosses, playoffs (with who lost them), course records
        set or equalled — each with the golfer, the edition, the week and the layout."""
        out = []
        if self.index is not None:                       # the index holds every moment, in archive order
            q, args = 'SELECT year, detail, kind, person, event_id, layout, week FROM moments WHERE 1=1' + self.index.upto(), []
            if year:
                q, args = q + ' AND year = ?', args + [year]
            if kind:
                q, args = q + ' AND kind = ?', args + [kind]
            for y, d, k, p, e, lay, w in self.index.db.execute(q + ' ORDER BY year, rowid', args):
                m = dict(json.loads(d), kind=k, person=p, event=e, layout=lay, week=w)
                if person is None or p == person or person in m.get('beat', ()):
                    out.append(dict(m, year=y))
            return out
        for y in ([year] if year else self.years):
            for m in self.year(y).get('moments', []):
                if (kind is None or m['kind'] == kind) and (person is None or m['person'] == person
                                                           or person in m.get('beat', ())):
                    out.append(dict(m, year=y))
        return out

    def access(self, pid, year):
        """A golfer's season of access: Premier playing rights at entry (and why), weeks by outcome, and
        each week they were shut out, not selected or played an alternative: [(week, outcome, the event
        they wanted most, the event they played instead)]."""
        row = self.year(year)['careers'].get(pid, {})
        return {'rights': row.get('rights'), 'weeks': row.get('access', {}),
                'denied': [tuple(x) for x in row.get('denied', [])]}

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
        if self.index is not None:                       # each site's own winner (not the edition's first)
            q = ('SELECT si.year, e.event_id, si.layout, (SELECT st.person FROM starts st WHERE st.eid = si.eid '
                 'AND st.site = si.site AND st.pos = 1 ORDER BY st.rowid LIMIT 1) FROM sites si JOIN editions e '
                 'USING(eid) WHERE si.course = ?' + self.index.upto('si.year') + ' ORDER BY si.year, e.eid, si.site')
            held = [{'year': y, 'event': eid, 'layout': lay, 'winner': w}
                    for y, eid, lay, w in self.index.db.execute(q, (course_id,))]
        else:
            for y, e in self.events():
                for i, (cid, layout, city) in enumerate(e['sites']):
                    if cid == course_id:
                        winner = next((g for g, p, _ in e['finish'][i] if p == 1), None) if i < len(e['finish']) else None
                        held.append({'year': y, 'event': e['id'], 'layout': layout, 'winner': winner})
        recs = {lid: r for lid, r in self.records.items() if lid.split(':')[0] == course_id}
        return {'course': self.world['courses'].get(course_id), 'editions': held, 'records': recs}

    # -- a season, from facts -----------------------------------------------------------------------------
    def professional_winners(self, people, through):
        """Which of `people` won an event of a series classified tier 1-3 (any site's winner counts) in
        a season up to `through`: one index query for just those people, else the season files."""
        people = set(people)
        if not people:
            return set()
        series = [sid for sid, m in self.world['series'].items() if m.get('tier') is not None and m['tier'] <= 3]
        through = min(through, self.years[-1]) if self.years else through
        if self.index is not None:
            ids, found = sorted(people), set()
            for i in range(0, len(ids), 500):
                chunk = ids[i:i + 500]
                q = ('SELECT DISTINCT s.person FROM starts s JOIN editions e USING(eid) WHERE s.pos = 1 AND s.year <= ? '
                     f'AND s.person IN ({",".join("?" * len(chunk))}) AND e.series IN ({",".join("?" * len(series))})')
                found |= {r[0] for r in self.index.db.execute(q, [through, *chunk, *series])}
            return found
        tiers = set(series)
        return {g for yy in self.years if yy <= through for e in self.year(yy)['events'] if e['series'] in tiers
                for site in e['finish'] for g, p, _ in site if p == 1 and g in people}

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
            if y - 1 not in self.years:
                prev = []
            elif self.index is not None:
                prev = [g for (g,) in self.index.db.execute(
                    'SELECT person FROM seasons WHERE year = ? AND wr_end = 1 ORDER BY rowid', (y - 1,))]
            else:
                prev = [g for g, r in self.year(y - 1)['careers'].items() if r.get('wr_end') == 1]
            if no1 != prev:
                facts.append({'fact': 'number one', 'golfer': no1[0], 'text': f'New world No.1: {self.name(no1[0])}'})
        kinds = Counter(t['kind'] for t in d['transitions'])
        asked = {t['gid'] for t in d['transitions'] if t['kind'] in ('became coach', 'became caddie')}
        winners = self.professional_winners(asked, y)
        for t in d['transitions']:
            if t['kind'] in ('became coach', 'became caddie') and t['gid'] in winners:   # notable ones by name
                facts.append({'fact': t['kind'], 'golfer': t['gid'],
                              'text': f'{self.name(t["gid"])}, a professional tournament winner, {t["kind"]} at {t["age"]}'})
            if t['kind'] == 'comeback':
                facts.append({'fact': 'comeback', 'golfer': t['gid'], 'text': f'{self.name(t["gid"])} came back at {t["age"]}'})
        facts.append({'fact': 'counts', 'counts': dict(kinds),
                      'text': ', '.join(f'{n} {k}' for k, n in sorted(kinds.items()))})
        return facts
