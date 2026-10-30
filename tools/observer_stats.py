"""Statistics for the observer: per person, season and tour, from the recorded results (Stats, Prize money,
the profile's season history). Derived, rebuildable, never part of the world.

Definitions (shown on the pages):
- A **start** is an appearance in a tournament field (qualifying stages are counted apart, not as starts).
  The engine never withdraws a golfer once an event has begun (an injured golfer withdraws beforehand and
  is replaced: not a start), so every start ends with a finishing position or a missed cut.
- **Wins** finish first (after any playoff, or as match-play champion). **Runner-up**: recorded position 2,
  ties included. **Top 2 / 5 / 10** are inclusive (a win is also a top 2, 5 and 10): never add them up.
  Match play records places by round reached (1, 2, 3 semi-finalists, 5 quarter-finalists, 9, 17, 33...).
- **Cuts**: stroke-play events with a cut only; "made / cut events". Events without a cut and match play
  have no cut to make.
- **Prize money** is gross tournament prize money (not net, sponsorship, job or staff income). Each event's
  payouts are those recorded when it was paid (since rules 2026-10-30); for seasons played before payouts
  were recorded they are recomputed from its purse, cut and field (as recorded when it was played; older
  archives: the calendar's) and the finishing order, with the engine's payout table (ties share, amateurs
  take nothing). Either way they are checked against every golfer's season prize money as actually paid:
  where they disagree the per-tour figure is shown as unknown, never guessed. Season and all-time totals
  use the money actually paid.
- Each edition counts once, under the tour it belonged to when it was played (majors under Majors).

The store is a small SQLite file next to the world (observer_cache/), built one season at a time from the
season files (in the background), and rebuilt for a season whose published file changes (a rollback).
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import threading
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SCHEMA = 1
COLUMNS = ('starts', 'wins', 'runner_ups', 'top2', 'top5', 'top10', 'cut_events', 'cuts_made', 'qualifiers')
DDL = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS years(year INT PRIMARY KEY, source TEXT);
CREATE TABLE IF NOT EXISTS agg(person INT, year INT, tour TEXT, starts INT, wins INT, runner_ups INT, top2 INT,
    top5 INT, top10 INT, cut_events INT, cuts_made INT, qualifiers INT, prize REAL, PRIMARY KEY(person, year, tour));
CREATE TABLE IF NOT EXISTS season_prize(person INT, year INT, prize REAL, reconciled INT, PRIMARY KEY(person, year));
CREATE TABLE IF NOT EXISTS money(event_id TEXT PRIMARY KEY, year INT, purse INT, cut_top INT, field_size INT,
    match_play INT);
CREATE TABLE IF NOT EXISTS staff_year(person INT, year INT, kind TEXT, rounds REAL, weeks INT, reputation REAL,
    earnings_total REAL, PRIMARY KEY(person, year, kind));
CREATE INDEX IF NOT EXISTS agg_year ON agg(year, tour);
CREATE INDEX IF NOT EXISTS agg_tour ON agg(tour);
"""


def _calendar():
    from golfsim.course_library import default_library
    return default_library().calendar.by_id


def payouts(purse, cut_top, field_size, finish, amateur):
    """{gid: prize} for one site's finish [(gid, pos, total)], as the engine pays it (season.pay_out):
    professionals with a position, in finishing order; the table sized by the intended paid places; ties
    share their places' money. `amateur(gid)` -> True / False / None (unknown: raises KeyError)."""
    from golfsim.prestige import payout_shares
    won = {}
    if not purse:
        return won
    paid = []
    for gid, pos, _ in finish:
        if pos is None:
            continue
        a = amateur(gid)
        if a is None:
            raise KeyError(gid)
        if not a:
            paid.append((gid, pos))
    places = min(cut_top, field_size) if cut_top else len(finish)
    shares = payout_shares(max(places, len(paid)))
    i = 0
    while i < len(paid):
        pos = paid[i][1]
        j = i
        while j < len(paid) and paid[j][1] == pos:
            j += 1
        each = sum(shares[i:j]) / (j - i) * purse
        for gid, _ in paid[i:j]:
            won[gid] = each
        i = j
    return won


def season_tables(events, status, paid, calendar=None):
    """Aggregate one season's editions.
    events: edition records (archive.edition_record form); status: {gid: 'pro'|'amateur'|...} in-season;
    paid: {gid: season prize money actually paid}. Returns (agg {(gid, tour): {col: n, 'prize': x}},
    reconciled {gid: bool}, money {event_id: (purse, cut_top, field_size, match_play)})."""
    agg = defaultdict(lambda: dict.fromkeys(COLUMNS, 0) | {'prize': 0.0})
    computed = defaultdict(float)
    unknown = set()
    money = {}
    cal = None
    for e in events:
        if 'purse' in e:
            purse, cut_top, field_size = e['purse'], e['cut_top'], e['field_size']
        else:                                            # archived before event-time money was recorded
            cal = cal or calendar or _calendar()
            ser = cal.get(e['series'])
            purse, cut_top, field_size = (ser.purse, ser.cut_top, ser.field) if ser else (None, 0, 0)
        mp = bool(e.get('match_play'))
        money[e['id']] = (purse, cut_top, field_size, mp)
        qualifying = e.get('kind') == 'qualifying' or e.get('tier') == 7
        tour = e.get('tour') or ''
        recorded = e.get('prizes')                   # paid as recorded (since rules 2026-10-30)
        for k, site in enumerate(e['finish']):
            if recorded and k < len(recorded):
                won = {int(g): x for g, x in recorded[k].items()}
            else:
                try:
                    won = payouts(purse, cut_top, field_size, site, lambda g: None if g not in status
                                  else status[g] == 'amateur') if purse is not None else None
                except KeyError:
                    won = None
            for gid, pos, _ in site:
                if won is None:
                    unknown.add(gid)
                else:
                    computed[gid] += won.get(gid, 0.0)
                a = agg[(gid, tour)]
                if qualifying:
                    a['qualifiers'] += 1
                    continue
                a['starts'] += 1
                if pos is not None:
                    a['wins'] += pos == 1
                    a['runner_ups'] += pos == 2
                    a['top2'] += pos <= 2
                    a['top5'] += pos <= 5
                    a['top10'] += pos <= 10
                if cut_top and not mp:
                    a['cut_events'] += 1
                    a['cuts_made'] += pos is not None
                if won is not None:
                    a['prize'] += won.get(gid, 0.0)
    reconciled = {}
    for gid in {g for g, _ in agg} | set(paid):
        ok = gid not in unknown and abs(computed.get(gid, 0.0) - (paid.get(gid) or 0.0)) <= 1.0
        reconciled[gid] = ok
    return dict(agg), reconciled, money


class StatsStore:
    """The SQLite store (one connection per thread: open one where it is used)."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=30)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript(DDL)
        if self.db.execute("SELECT value FROM meta WHERE key='schema'").fetchone() is None:
            self.db.execute("INSERT INTO meta VALUES ('schema', ?)", (str(SCHEMA),))
        self.db.commit()

    def close(self):
        self.db.close()

    def sources(self):
        return {y: s for y, s in self.db.execute('SELECT year, source FROM years')}

    def drop(self, year):
        with self.db:
            for t in ('agg', 'season_prize', 'money', 'staff_year'):
                self.db.execute(f'DELETE FROM {t} WHERE year = ?', (year,))
            self.db.execute('DELETE FROM years WHERE year = ?', (year,))

    def put(self, year, source, agg, reconciled, paid, money, staff=()):
        with self.db:
            for t in ('agg', 'season_prize', 'money', 'staff_year'):
                self.db.execute(f'DELETE FROM {t} WHERE year = ?', (year,))
            self.db.executemany('INSERT INTO staff_year VALUES (?,?,?,?,?,?,?)', staff)
            self.db.executemany(
                'INSERT INTO agg VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                [(gid, year, tour, *(a[c] for c in COLUMNS), a['prize'] if reconciled.get(gid) else None)
                 for (gid, tour), a in agg.items()])
            self.db.executemany('INSERT INTO season_prize VALUES (?,?,?,?)',
                                [(gid, year, paid.get(gid), int(bool(ok))) for gid, ok in reconciled.items()])
            self.db.executemany('INSERT OR REPLACE INTO money VALUES (?,?,?,?,?,?)',
                                [(eid, year, *m[:3], int(m[3])) for eid, m in money.items()])
            self.db.execute('INSERT OR REPLACE INTO years VALUES (?, ?)', (year, source))


def season_source(archive, y):
    """What identifies a season as published (its file name under a manifest; size, time and inode before)."""
    return json.dumps(archive.signature(y))


def build(archive_dir, store_path):
    """Bring the store up to date with the published history (one season at a time; a season whose
    published file changed is rebuilt, one no longer published is dropped)."""
    from golfsim.archive import Archive
    with Archive(archive_dir) as a:
        store = StatsStore(store_path)
        try:
            have = store.sources()
            want = {y: season_source(a, y) for y in a.years}
            for y in set(have) - set(want):
                store.drop(y)
            for y in [y for y in a.years if have.get(y) != want[y]]:
                d = a.year(y)
                careers = d['careers']
                status = {int(g): r.get('status') for g, r in careers.items()}
                paid = {int(g): r.get('prize') or 0 for g, r in careers.items()}
                agg, rec, money = season_tables(d['events'], status, paid)
                staff = [(int(k.split(':')[1]), y, k.split(':')[0], v.get('rounds'), v.get('weeks'),
                          v.get('reputation'), v.get('earnings_total')) for k, v in d.get('staff_year', {}).items()]
                store.put(y, want[y], agg, rec, paid, money, staff)
                a._years.clear()                         # (one decoded season at a time)
        finally:
            store.close()


class Builder:
    """Brings a world's store up to date in a separate process (decoding season files would otherwise hold
    up the pages), with its own snapshot of the history. One per world; progress is read from the store."""

    def __init__(self, archive_dir, store_path):
        self.archive_dir, self.store_path = Path(archive_dir), Path(store_path)
        self.proc = None
        self.state = {'running': False, 'done': 0, 'total': 0, 'error': None}

    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def start(self):
        if self.running():
            return
        import subprocess
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        log = self.store_path.with_suffix('.log')
        with open(log, 'w') as err:
            self.proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), 'build', str(self.archive_dir),
                                          str(self.store_path)], stdout=subprocess.DEVNULL, stderr=err)
        self.state.update(running=True, error=None)

    def poll(self, want, have):
        """Update and return the progress dict, given the seasons wanted and those already built."""
        self.state['total'] = len(want)
        self.state['done'] = sum(1 for y, v in want.items() if have.get(y) == v)
        self.state['running'] = self.running()
        if self.proc is not None and not self.state['running'] and self.proc.returncode:
            try:
                tail = self.store_path.with_suffix('.log').read_text().strip().splitlines()[-1:]
            except OSError:
                tail = []
            self.state['error'] = tail[0] if tail else f'exit code {self.proc.returncode}'
        return self.state

    def wait(self, timeout=None):
        if self.proc is not None:
            self.proc.wait(timeout)

    def stop(self):
        if self.running():
            self.proc.terminate()
            self.wait(10)


def cache_path(world):
    """observer_cache/stats.sqlite inside a world folder this observer owns; a temporary folder for
    archives browsed read-only (never written into)."""
    if world.session is not None:
        return Path(world.path) / 'observer_cache' / 'stats.sqlite'
    import hashlib
    import tempfile
    h = hashlib.sha1(str(Path(world.archive_dir).resolve()).encode()).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / 'golf-legacy-observer' / f'{h}.stats.sqlite'


def live_tables(view):
    """The current season's (agg, reconciled, money, paid) from the snapshot (partial: weeks played so far)."""
    paid = view.prize
    agg, rec, money = season_tables(list(view.editions.values()),
                                    {g: p.get('status') for g, p in view.people.items()}, paid)
    return agg, rec, money, paid


def query(db, years=None, tour=None, live=None, live_year=None):
    """{person: {col: n, 'prize': x | None, 'prize_known': bool}} over archived `years` (None: all) and the
    live season's tables if given. Overall (no tour): prize money actually paid; a tour: recomputed payouts
    (None where they could not be reconciled)."""
    out = defaultdict(lambda: dict.fromkeys(COLUMNS, 0) | {'prize': 0.0, 'prize_known': True})
    where, args = [], []
    if years is not None:
        where.append(f'year IN ({",".join("?" * len(years))})')
        args += list(years)
    if tour:
        where.append('tour = ?')
        args.append(tour)
    w = (' WHERE ' + ' AND '.join(where)) if where else ''
    cols = ', '.join(f'SUM({c})' for c in COLUMNS)
    if db is None or (years is not None and not years):
        db = _EMPTY
    for row in db.execute(f'SELECT person, {cols}, SUM(prize), COUNT(*) - COUNT(prize) FROM agg{w} GROUP BY person', args):
        r = out[row[0]]
        for c, v in zip(COLUMNS, row[1:]):
            r[c] += v or 0
        if tour:
            r['prize'] += row[-2] or 0.0
            r['prize_known'] &= row[-1] == 0
    if not tour:
        pw = (' WHERE ' + where[0]) if years is not None else ''
        for pid, prize in db.execute(f'SELECT person, SUM(prize) FROM season_prize{pw} GROUP BY person',
                                     args[:len(years)] if years is not None else []):
            out[pid]['prize'] += prize or 0.0
    if live is not None:
        agg, rec = live[0], live[1]
        for (gid, t), a in agg.items():
            if tour and t != tour:
                continue
            r = out[gid]
            for c in COLUMNS:
                r[c] += a[c]
            if tour:
                if rec.get(gid):
                    r['prize'] += a['prize']
                else:
                    r['prize_known'] = False
        if not tour:
            for gid, prize in live[3].items():
                if gid in out or prize:
                    out[gid]['prize'] += prize
    return out


class _Empty:
    """No archived seasons selected: no rows."""

    def execute(self, *a):
        return []


_EMPTY = _Empty()


def tours_in(db):
    return [t for (t,) in db.execute('SELECT DISTINCT tour FROM agg')] if db is not None else []


def person_seasons(db, pid):
    """{year: {'tours': {tour: row}, 'prize': paid, 'reconciled': bool}} for one person (archived seasons)."""
    out = {}
    for row in db.execute(f'SELECT year, tour, {", ".join(COLUMNS)}, prize FROM agg WHERE person = ?', (pid,)):
        y, t = row[0], row[1]
        out.setdefault(y, {'tours': {}, 'prize': None, 'reconciled': False})['tours'][t] = (
            dict(zip(COLUMNS, row[2:-1])) | {'prize': row[-1]})
    for y, prize, ok in db.execute('SELECT year, prize, reconciled FROM season_prize WHERE person = ?', (pid,)):
        s = out.setdefault(y, {'tours': {}, 'prize': None, 'reconciled': False})
        s['prize'], s['reconciled'] = prize, bool(ok)
    return out


def edition_money(db, event_id):
    r = db.execute('SELECT purse, cut_top, field_size, match_play FROM money WHERE event_id = ?', (event_id,)).fetchone()
    return r


def staff_seasons(db, pid, kind):
    """{year: {'rounds', 'weeks', 'reputation', 'earnings'}}: a coach's or caddie's recorded seasons; earnings
    for a season only where its own and the previous season's career totals were both recorded."""
    rows = {y: (r, wk, rep, tot) for y, r, wk, rep, tot in db.execute(
        'SELECT year, rounds, weeks, reputation, earnings_total FROM staff_year WHERE person = ? AND kind = ? ORDER BY year',
        (pid, kind))}
    out = {}
    for y, (r, wk, rep, tot) in rows.items():
        prev = rows.get(y - 1)
        out[y] = {'rounds': r, 'weeks': wk, 'reputation': rep,
                  'earnings': (tot - prev[3]) if tot is not None and prev and prev[3] is not None else None}
    return out


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == 'build':
        build(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit('usage: observer_stats.py build ARCHIVE_DIR STORE_PATH')
