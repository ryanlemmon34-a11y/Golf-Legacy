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
- **Golf statistics** (golfsim.golfstats, from the golf-statistics update on): each start's counters are summed per
  person, season and tour, so any figure over any scope is a sum of counts over a sum of opportunities;
  `golf_starts` counts the starts that carry them (coverage). Qualifying stages are not included.
- **Records kept here** (per season, bounded): the longest drives and the best event driving averages
  (top RECORD_KEEP per season and tour), every stroke-play winning margin and every match-play result.

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

from golfsim import golfstats as GS                                      # noqa: E402

SCHEMA = 4
COLUMNS = ('starts', 'wins', 'runner_ups', 'top2', 'top5', 'top10', 'cut_events', 'cuts_made', 'qualifiers')
GOLF = ('golf_starts',) + GS.FIELDS            # summed golf statistics counters (and the starts carrying them)
ALL = COLUMNS + GOLF
RECORD_KEEP = 100                              # longest drives / event driving averages kept per season and tour
EVENT_DRIVE_TIERS = (8, 20, 30, 40)            # event driving averages: the top RECORD_KEEP among the editions with
EVENT_MIN_DRIVES = EVENT_DRIVE_TIERS[0]        # at least this many measured drives, kept for each tier (qualified
                                               # before limited: a record list never loses a qualified leader)
TABLES = ('agg', 'season_prize', 'money', 'staff_year', 'long_drives', 'event_drives', 'margins', 'matches')
ALL_TIME = ('agg_all', 'prize_all')            # every season summed (for all-time pages), with the seasons they hold
DDL = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS years(year INT PRIMARY KEY, source TEXT);
CREATE TABLE IF NOT EXISTS agg(person INT, year INT, tour TEXT, starts INT, wins INT, runner_ups INT, top2 INT,
    top5 INT, top10 INT, cut_events INT, cuts_made INT, qualifiers INT, prize REAL, """ + ', '.join(
    f'{c} INT' for c in GOLF) + """, PRIMARY KEY(person, year, tour));
CREATE TABLE IF NOT EXISTS agg_all(person INT, tour TEXT, """ + ', '.join(f'{c} INT' for c in ALL) + """,
    prize REAL, prize_unknown INT, PRIMARY KEY(person, tour));
CREATE TABLE IF NOT EXISTS prize_all(person INT PRIMARY KEY, prize REAL);
CREATE TABLE IF NOT EXISTS long_drives(year INT, tour TEXT, person INT, event_id TEXT, week INT, tenths INT, round INT,
    hole INT);
CREATE TABLE IF NOT EXISTS event_drives(year INT, tour TEXT, person INT, event_id TEXT, week INT, tenths INT, drives INT,
    tier INT);
CREATE TABLE IF NOT EXISTS margins(year INT, tour TEXT, event_id TEXT, series TEXT, week INT, major INT, rounds INT,
    winner INT, win_total INT, runner_total INT, margin INT, runners_up TEXT, playoff INT, field INT);
CREATE TABLE IF NOT EXISTS matches(year INT, tour TEXT, event_id TEXT, series TEXT, week INT, stage TEXT, winner INT,
    loser INT, result TEXT, holes INT, up INT, remaining INT);
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
    agg = defaultdict(lambda: dict.fromkeys(ALL, 0) | {'prize': 0.0})
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
        golf = e.get('golf')                         # golf statistics counters (when they were kept)
        for k, site in enumerate(e['finish']):
            counters = golf[k] if golf and k < len(golf) else {}
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
                c = counters.get(str(gid), counters.get(gid))
                if c:
                    a['golf_starts'] += 1
                    for f, v in zip(GS.FIELDS, c):
                        a[f] += v
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


def _match_margin(text):
    """(holes up, holes remaining) of a match result: '7&6' -> (7, 6), '2 up' -> (2, 0), '19 holes' (won at an
    extra hole) -> (1, 0)."""
    if '&' in text:
        a, b = text.split('&')
        return int(a), int(b)
    if text.endswith(' up'):
        return int(text[:-3]), 0
    return 1, 0


def season_records(events, year):
    """The season's record rows: (long_drives, event_drives, margins, matches), from the editions' recorded
    golf statistics, finishes and match results. Qualifying stages are left out; winning margins are for
    single-site stroke-play editions (a multi-site edition has no single field to lead)."""
    longs, avgs = defaultdict(list), defaultdict(list)
    margins, matches = [], []
    for e in events:
        if e.get('kind') == 'qualifying' or e.get('tier') == 7:
            continue
        tour = e.get('tour') or ''
        for k, site in enumerate(e.get('golf') or []):
            for g, c in site.items():
                if len(c) > GS.N and c[GS.N]:
                    longs[tour].append((year, tour, int(g), e['id'], e['week'], c[GS.N], c[GS.N + 1], c[GS.N + 2]))
                drives = c[GS.IDX['drives']]
                if drives >= EVENT_MIN_DRIVES:
                    avgs[tour].append((year, tour, int(g), e['id'], e['week'], c[GS.IDX['drive_tenths']], drives))
        if e.get('match_play'):
            for site in e.get('matches') or []:
                for stage, win, lose, text, holes in site:
                    up, rem = _match_margin(text)
                    matches.append((year, tour, e['id'], e['series'], e['week'], stage, win, lose, text, holes, up, rem))
            continue
        if len(e['finish']) != 1:
            continue
        site = e['finish'][0]
        win = next(((g, t) for g, p, t in site if p == 1 and t is not None), None)
        rest = [(g, t) for g, p, t in site if t is not None and (win is None or g != win[0])]
        if win is None or not rest:
            continue
        runner = min(t for _, t in rest)
        margins.append((year, tour, e['id'], e['series'], e['week'], int(e.get('category') == 'major'), e.get('rounds'),
                        win[0], win[1], runner, runner - win[1], json.dumps([g for g, t in rest if t == runner]),
                        e.get('playoff') or 0, len(site)))
    keep_long = [r for rows in longs.values() for r in sorted(rows, key=lambda r: (-r[5], r[2]))[:RECORD_KEEP]]
    keep_avg = []
    for rows in avgs.values():
        ranked = sorted(rows, key=lambda r: (-r[5] / r[6], r[2]))
        for tier in EVENT_DRIVE_TIERS:                   # filter by the tier first, then keep its leaders
            keep_avg += [r + (tier,) for r in [r for r in ranked if r[6] >= tier][:RECORD_KEEP]]
    return keep_long, keep_avg, margins, matches


class StatsStore:
    """The SQLite store (one connection per thread: open one where it is used)."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=30)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript(DDL)
        have = self.db.execute("SELECT value FROM meta WHERE key='schema'").fetchone()
        if have is not None and have[0] != str(SCHEMA):    # derived: an older store is rebuilt from the history
            with self.db:
                for t in TABLES + ALL_TIME + ('years', 'meta'):
                    self.db.execute(f'DROP TABLE IF EXISTS {t}')
            self.db.executescript(DDL)
            have = None
        if have is None:
            self.db.execute("INSERT INTO meta VALUES ('schema', ?)", (str(SCHEMA),))
        self.db.commit()

    def close(self):
        self.db.close()

    def sources(self):
        return {y: s for y, s in self.db.execute('SELECT year, source FROM years')}

    def sum_all_time(self):
        """agg_all / prize_all: every season held, summed per person (and tour), recorded with the seasons
        and sources they were summed from (query uses them only when those are exactly the seasons asked)."""
        cols = ', '.join(f'SUM({c})' for c in ALL)
        with self.db:
            self.db.execute('DELETE FROM agg_all')
            self.db.execute('DELETE FROM prize_all')
            self.db.execute(f'INSERT INTO agg_all SELECT person, tour, {cols}, SUM(prize), COUNT(*) - COUNT(prize) '
                            'FROM agg GROUP BY person, tour')
            self.db.execute('INSERT INTO prize_all SELECT person, SUM(prize) FROM season_prize GROUP BY person')
            self.db.execute("INSERT OR REPLACE INTO meta VALUES ('all_time', ?)",
                            (json.dumps(sorted(self.sources().items())),))

    def drop(self, year):
        with self.db:
            for t in TABLES:
                self.db.execute(f'DELETE FROM {t} WHERE year = ?', (year,))
            self.db.execute('DELETE FROM years WHERE year = ?', (year,))

    def put(self, year, source, agg, reconciled, paid, money, staff=(), records=((), (), (), ())):
        with self.db:
            for t in TABLES:
                self.db.execute(f'DELETE FROM {t} WHERE year = ?', (year,))
            self.db.executemany('INSERT INTO staff_year VALUES (?,?,?,?,?,?,?)', staff)
            self.db.executemany(
                f'INSERT INTO agg VALUES ({",".join("?" * (4 + len(ALL)))})',
                [(gid, year, tour, *(a[c] for c in COLUMNS), a['prize'] if reconciled.get(gid) else None,
                  *(a[c] for c in GOLF)) for (gid, tour), a in agg.items()])
            for t, rows in zip(('long_drives', 'event_drives', 'margins', 'matches'), records):
                if rows:
                    self.db.executemany(f'INSERT INTO {t} VALUES ({",".join("?" * len(rows[0]))})', rows)
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
            changed = set(have) - set(want)
            for y in [y for y in a.years if have.get(y) != want[y]]:
                changed.add(y)
                d = a.year(y)
                careers = d['careers']
                status = {int(g): r.get('status') for g, r in careers.items()}
                paid = {int(g): r.get('prize') or 0 for g, r in careers.items()}
                agg, rec, money = season_tables(d['events'], status, paid)
                staff = [(int(k.split(':')[1]), y, k.split(':')[0], v.get('rounds'), v.get('weeks'),
                          v.get('reputation'), v.get('earnings_total')) for k, v in d.get('staff_year', {}).items()]
                store.put(y, want[y], agg, rec, paid, money, staff, season_records(d['events'], y))
                a._years.clear()                         # (one decoded season at a time)
            if changed or store.db.execute("SELECT 1 FROM meta WHERE key = 'all_time'").fetchone() is None:
                store.sum_all_time()
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


def _all_time(db, years):
    """Whether the all-time sums hold exactly these seasons, as the store now holds them."""
    if years is None or not years:
        return False
    try:
        row = db.execute("SELECT value FROM meta WHERE key = 'all_time'").fetchone()
    except Exception:
        return False
    if row is None:
        return False
    held = dict(map(tuple, json.loads(row[0])))
    if set(held) != set(years):
        return False
    now = dict(db.execute(f'SELECT year, source FROM years WHERE year IN ({",".join("?" * len(years))})', list(years)))
    return all(now.get(y) == s for y, s in held.items())


def query(db, years=None, tour=None, live=None, live_year=None, cols=ALL):
    """{person: {col: n, 'prize': x | None, 'prize_known': bool}} over archived `years` (None: all) and the
    live season's tables if given, for the columns `cols` (all by default). Overall (no tour): prize money
    actually paid; a tour: recomputed payouts (None where they could not be reconciled). Every archived
    season at once reads the store's all-time sums when they hold exactly those seasons (the same sums)."""
    cols = tuple(cols)
    out = defaultdict(lambda: dict.fromkeys(cols, 0) | {'prize': 0.0, 'prize_known': True})
    if db is None or (years is not None and not years):
        db = _EMPTY
    whole = db is not _EMPTY and _all_time(db, years)
    where, args = [], []
    if years is not None and not whole:
        where.append(f'year IN ({",".join("?" * len(years))})')
        args += list(years)
    from golfsim.scopes import tours_for
    tours = tours_for(tour)                              # one tour, or every tour of a shared scope (Majors + Premier)
    if tours:
        where.append(f'tour IN ({",".join("?" * len(tours))})')
        args += list(tours)
    w = (' WHERE ' + ' AND '.join(where)) if where else ''
    sums = ', '.join(f'SUM({c})' for c in cols)
    if whole:
        q = f'SELECT person, {sums}, SUM(prize), SUM(prize_unknown) FROM agg_all{w} GROUP BY person'
    else:
        q = f'SELECT person, {sums}, SUM(prize), COUNT(*) - COUNT(prize) FROM agg{w} GROUP BY person'
    n = len(cols)
    for row in db.execute(q, args):
        r = out[row[0]]
        for c, v in zip(cols, row[1:n + 1]):
            r[c] += v or 0
        if tour:
            r['prize'] += row[-2] or 0.0
            r['prize_known'] &= row[-1] == 0
    if not tour:
        if whole:
            prizes = db.execute('SELECT person, prize FROM prize_all')
        else:
            pw = (' WHERE ' + where[0]) if years is not None else ''
            prizes = db.execute(f'SELECT person, SUM(prize) FROM season_prize{pw} GROUP BY person',
                                args[:len(years)] if years is not None else [])
        for pid, prize in prizes:
            out[pid]['prize'] += prize or 0.0
    if live is not None:
        agg, rec = live[0], live[1]
        for (gid, t), a in agg.items():
            if tours and t not in tours:
                continue
            r = out[gid]
            for c in cols:
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
    for row in db.execute(f'SELECT year, tour, {", ".join(COLUMNS)}, prize, {", ".join(GOLF)} FROM agg WHERE person = ?',
                          (pid,)):
        y, t = row[0], row[1]
        n = 2 + len(COLUMNS)
        out.setdefault(y, {'tours': {}, 'prize': None, 'reconciled': False})['tours'][t] = (
            dict(zip(COLUMNS, row[2:n])) | {'prize': row[n]} | dict(zip(GOLF, row[n + 1:])))
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
