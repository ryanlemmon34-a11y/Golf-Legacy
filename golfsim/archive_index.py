"""A query index over the history archive, for browsing a century without reading every season.

The archive's season files stay the record of facts; this is a derived index beside them
(`archive/index.sqlite`, SQLite from Python's standard library), rebuilt from them at any time
(`ArchiveIndex.rebuild`). Each archived season is indexed in one transaction that first removes that
season's rows, so indexing is idempotent: writing a season again (a retried advance) never duplicates
anything, and dropping seasons beyond a committed point (session recovery) is one statement.

Tables: editions (one per event played, with its classification when played and its first site's
winner), sites (course and layout of each site), starts (one per golfer per edition and site: position,
total, the coach and caddie that week, the entry route -- every site's winner is here), seasons (one per
golfer per season), moments (holes-in-one, albatrosses, playoffs, course records); since schema 2,
number_one (each week's No. 1, world and amateur) and careers (each golfer's season row, compressed).
An index written before schema 2 is completed once by the session that owns it (backfill_derived). Indexed by person, event,
series and course, so a profile, a tournament's history or a course's history is one query; the large
tables (starts, seasons, careers) are also indexed by season, so reading one season's starts (records)
or replacing one season (publishing, recovery) touches that season's rows, not the whole history. The
small tables (sites, moments: under 100,000 rows after 50 seasons) are scanned. A writer opening an index
from before these season indexes adds them once (a few seconds for 50 seasons).
"""
from __future__ import annotations

import json
import sqlite3
import zlib
from pathlib import Path

SCHEMA = 2
DDL = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS editions(eid INTEGER PRIMARY KEY, event_id TEXT UNIQUE, year INT, week INT, series TEXT,
    name TEXT, tour TEXT, tier INT, category TEXT, prestige REAL, playoff INT, winner INT, field INT);
CREATE TABLE IF NOT EXISTS sites(eid INT, site INT, year INT, course TEXT, layout TEXT, city TEXT,
    PRIMARY KEY(eid, site));
CREATE TABLE IF NOT EXISTS routes(rid INTEGER PRIMARY KEY, text TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS starts(person INT, eid INT, year INT, week INT, site INT, pos INT, total INT,
    coach INT, caddie INT, rid INT);
CREATE TABLE IF NOT EXISTS seasons(person INT, year INT, tour TEXT, status TEXT, lifestyle TEXT, events INT,
    wins INT, prize INT, wr_end INT, am_end INT, PRIMARY KEY(person, year));
CREATE TABLE IF NOT EXISTS moments(year INT, week INT, kind TEXT, person INT, event_id TEXT, layout TEXT,
    detail TEXT);
CREATE TABLE IF NOT EXISTS number_one(year INT, week INT, kind TEXT, person INT, PRIMARY KEY(year, week, kind));
CREATE TABLE IF NOT EXISTS careers(person INT, year INT, row BLOB, PRIMARY KEY(person, year));
CREATE INDEX IF NOT EXISTS moments_person ON moments(person);
CREATE INDEX IF NOT EXISTS moments_kind ON moments(kind, year);
CREATE INDEX IF NOT EXISTS starts_person ON starts(person, year, week);
CREATE INDEX IF NOT EXISTS starts_event ON starts(eid);
CREATE INDEX IF NOT EXISTS starts_year ON starts(year);
CREATE INDEX IF NOT EXISTS seasons_year ON seasons(year);
CREATE INDEX IF NOT EXISTS careers_year ON careers(year);
CREATE INDEX IF NOT EXISTS editions_series ON editions(series, year);
CREATE INDEX IF NOT EXISTS editions_year ON editions(year, week);
CREATE INDEX IF NOT EXISTS sites_course ON sites(course, year);
"""


class ArchiveIndex:
    """A connection to the index. A writer (the session publishing or recovering) creates the tables and
    keeps the database in WAL mode. A reader (`reader=True`, used by Archive) writes nothing: it holds
    one read transaction for its lifetime (`snapshot`), so it sees the index exactly as it was when its
    Archive was opened while the session goes on publishing, and every query is limited to its
    Archive's seasons (`through`). Close it (`close`, or use it as a context manager): an open reader
    keeps its connection and its WAL snapshot."""

    def __init__(self, path, reader=False):
        self.path = Path(path)
        self.reader = reader
        self.through = None                             # readers: the last season their Archive holds
        self.snapshot_held = False
        self.db = sqlite3.connect(self.path, timeout=30, isolation_level=None if reader else '')
        try:
            if reader:
                return
            self.db.execute('PRAGMA journal_mode=WAL')    # (refused without shared memory: see snapshot)
            self.db.executescript(DDL)
            self.db.execute("INSERT OR IGNORE INTO meta VALUES ('schema', ?)", (str(SCHEMA),))
            self.db.commit()
        except BaseException:
            self.db.close()
            raise

    def snapshot(self):
        """Readers: begin the read transaction that pins what this connection sees (WAL only; in
        another journal mode a held read would block the session's writes, so none is held and only
        the season bound applies)."""
        if self.db.execute('PRAGMA journal_mode').fetchone()[0].lower() == 'wal':
            self.db.execute('BEGIN')
            self.db.execute('SELECT COUNT(*) FROM meta').fetchone()
            self.snapshot_held = True
        return self.snapshot_held

    def upto(self, col='year'):
        """The readers' season bound, as SQL ('' for writers)."""
        return '' if self.through is None else f' AND {col} <= {int(self.through)}'

    def close(self):
        if self.db is None:
            return
        try:
            if self.db.in_transaction and self.reader:
                self.db.rollback()
        finally:
            self.db.close()
            self.db = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # ---- writing --------------------------------------------------------------------------------------------
    def index_year(self, year, chunk):
        """Index one archived season (its file's contents), replacing anything indexed for that year."""
        with self.db:
            self._delete(year, '=')
            rid = dict(self.db.execute('SELECT text, rid FROM routes'))
            site_rows, start_rows = [], []
            for e in chunk['events']:
                winner = next((g for site in e['finish'] for g, p, _ in site if p == 1), None)
                field = sum(len(site) for site in e['finish'])
                eid = self.db.execute('INSERT INTO editions VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?)',
                                      (e['id'], year, e['week'], e['series'], e.get('name'), e.get('tour'), e.get('tier'),
                                       e.get('category'), e.get('prestige'), e.get('playoff'), winner, field)).lastrowid
                for k, v in enumerate(e.get('sites', [])):
                    site_rows.append((eid, k, year, v[0], v[1], v[2]))
                team, routes = e.get('team', {}), e.get('routes', {})
                for k, site in enumerate(e['finish']):
                    for g, p, total in site:
                        coach, caddie = team.get(str(g), team.get(g, (0, 0)))
                        route = routes.get(str(g), routes.get(g))
                        if route is not None and route not in rid:
                            rid[route] = self.db.execute('INSERT INTO routes VALUES (NULL, ?)', (route,)).lastrowid
                        start_rows.append((g, eid, year, e['week'], k, p, total, coach, caddie, rid.get(route)))
            self.db.executemany('INSERT INTO sites VALUES (?,?,?,?,?,?)', site_rows)
            self.db.executemany('INSERT INTO starts VALUES (?,?,?,?,?,?,?,?,?,?)', start_rows)
            self.db.executemany('INSERT INTO moments VALUES (?,?,?,?,?,?,?)', [
                (year, m.get('week'), m['kind'], m['person'], m['event'], m.get('layout'),
                 json.dumps({k: v for k, v in m.items() if k not in ('kind', 'person', 'event', 'layout', 'week')}))
                for m in chunk.get('moments', [])])
            self._derived(year, chunk)
            self.db.executemany('INSERT INTO seasons VALUES (?,?,?,?,?,?,?,?,?,?)', [
                (int(g), year, r.get('tour'), r.get('status'), r.get('lifestyle'), r.get('events'), r.get('wins'),
                 r.get('prize'), r.get('wr_end'), r.get('am_end')) for g, r in chunk['careers'].items()])

    def _derived(self, year, chunk):
        """The tables added after the first index (schema 2): each week's No. 1 of the world and amateur
        rankings, and each golfer's season row (compressed), so a career is one query."""
        for t in ('number_one', 'careers'):
            self.db.execute(f'DELETE FROM {t} WHERE year = ?', (year,))
        self.db.executemany('INSERT INTO number_one VALUES (?,?,?,?)', [
            (year, int(w), kind, top[0]) for kind, table in chunk.get('rankings', {}).items()
            for w, top in table.items() if top])
        self.db.executemany('INSERT INTO careers VALUES (?,?,?)', [
            (int(g), year, zlib.compress(json.dumps(r).encode(), 6)) for g, r in chunk['careers'].items()])
        self.db.execute('INSERT OR REPLACE INTO meta VALUES (?, ?)', (f'derived:{year}', str(year)))

    def derived_complete(self, years):
        """Whether the schema-2 tables cover these seasons (an index written before them does not)."""
        done = {int(r[0]) for r in self.db.execute("SELECT value FROM meta WHERE key LIKE 'derived:%'")}
        return set(years) <= done

    def backfill_derived(self, archive):
        """Fill the schema-2 tables for seasons indexed before they existed, one season file at a time
        (derived data only: the season files are never touched). Run by the session that owns the archive,
        under its lock."""
        from .archive import _read
        for y in archive.years:
            if not self.derived_complete([y]):
                with self.db:
                    self._derived(y, _read(archive.dir / 'years' / f'{y}.json.gz'))

    def career(self, pid):
        """[(year, season row)] for every season a golfer competed (as in the season files)."""
        return [(y, json.loads(zlib.decompress(row))) for y, row in
                self.db.execute('SELECT year, row FROM careers WHERE person = ?' + self.upto() + ' ORDER BY year', (pid,))]

    def drop_years_after(self, year):
        with self.db:
            self._delete(year, '>')

    def _delete(self, year, op):
        for t in ('editions', 'sites', 'starts', 'seasons', 'moments', 'number_one', 'careers'):
            self.db.execute(f'DELETE FROM {t} WHERE year {op} ?', (year,))
        self.db.execute(f"DELETE FROM meta WHERE key LIKE 'derived:%' AND CAST(value AS INT) {op} ?", (year,))
        # (the routes table is a shared dictionary of route texts; unused entries are harmless)

    @classmethod
    def rebuild(cls, archive):
        """Build the index from an archive's season files (e.g. for an archive written before indexes)."""
        path = archive.dir / 'index.sqlite'
        for p in (path, path.with_name(path.name + '-wal'), path.with_name(path.name + '-shm')):
            if p.exists():
                p.unlink()
        idx = cls(path)
        from .archive import _read
        try:
            for y in archive.years:
                idx.index_year(y, _read(archive.dir / 'years' / f'{y}.json.gz'))
        except BaseException:
            idx.close()
            raise
        return idx

    # ---- reading ----------------------------------------------------------------------------------------------
    def years(self):
        """Every season indexed (in a reader's snapshot; not limited by `through`)."""
        return [r[0] for r in self.db.execute('SELECT DISTINCT year FROM editions ORDER BY year')]

    def results(self, pid):
        """The same rows as Archive.results, from the index."""
        q = ('SELECT s.year, s.week, e.event_id, e.series, s.pos, s.coach, s.caddie, r.text FROM starts s '
             'JOIN editions e USING(eid) LEFT JOIN routes r USING(rid) WHERE s.person = ?' + self.upto('s.year') +
             ' ORDER BY s.year, s.week, e.event_id, s.site')
        return [{'year': y, 'week': w, 'event': eid, 'series': ser, 'pos': p, 'coach': c, 'caddie': k, 'route': r}
                for y, w, eid, ser, p, c, k, r in self.db.execute(q, (pid,))]

    def editions(self, series):
        """A tournament's history: every edition with its year, week, winner and field size."""
        q = ('SELECT event_id, year, week, winner, field, prestige, tour, tier FROM editions WHERE series = ?'
             + self.upto() + ' ORDER BY year')
        return [dict(zip(('event', 'year', 'week', 'winner', 'field', 'prestige', 'tour', 'tier'), r))
                for r in self.db.execute(q, (series,))]

    def course_editions(self, course_id):
        q = ('SELECT s.year, e.event_id, s.layout, e.winner FROM sites s JOIN editions e USING(eid) '
             'WHERE s.course = ?' + self.upto('s.year') + ' ORDER BY s.year, e.event_id')
        return [{'year': y, 'event': eid, 'layout': lay, 'winner': w} for y, eid, lay, w in self.db.execute(q, (course_id,))]

    def leaderboard(self, event_id):
        q = ('SELECT s.person, s.site, s.pos, s.total, s.coach, s.caddie, r.text FROM starts s JOIN editions e USING(eid) '
             'LEFT JOIN routes r USING(rid) WHERE e.event_id = ?' + self.upto('e.year') +
             ' ORDER BY s.site, s.pos IS NULL, s.pos')
        return [dict(zip(('person', 'site', 'pos', 'total', 'coach', 'caddie', 'route'), r))
                for r in self.db.execute(q, (event_id,))]

    def moments(self, kind=None, person=None):
        q, args = 'SELECT year, week, kind, person, event_id, layout, detail FROM moments WHERE 1=1' + self.upto(), []
        if kind:
            q, args = q + ' AND kind = ?', args + [kind]
        if person is not None:
            q, args = q + ' AND person = ?', args + [person]
        return [dict(json.loads(d), year=y, week=w, kind=k, person=p, event=e, layout=lay)
                for y, w, k, p, e, lay, d in self.db.execute(q + ' ORDER BY year, week', args)]

    def seasons(self, pid):
        q = ('SELECT year, tour, status, lifestyle, events, wins, prize, wr_end, am_end FROM seasons WHERE person = ?'
             + self.upto() + ' ORDER BY year')
        return [dict(zip(('year', 'tour', 'status', 'lifestyle', 'events', 'wins', 'prize', 'wr_end', 'am_end'), r))
                for r in self.db.execute(q, (pid,))]
