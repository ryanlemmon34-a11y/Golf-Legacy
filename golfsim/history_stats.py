"""Records and frivolities from the history archive, with one set of definitions (V1 UI baseline).

Every board here is computed from the archive's facts (editions, finishes, people, stints, rankings), so
the central Records section, a profile's contextual records and the Frivolities lists can never disagree:
they are the same functions with a different filter. Each row carries the evidence (the edition ids that
establish it) and two flags the UI must show:

    active    the career is unfinished (the person still competes): not a final lifetime outcome
    partial   the career began before the archive's first season, so its early results are unknown:
              counts are "since the archive began", and debuts or "starts before a first win" are not
              true career values (excluded from debut and first-win boards unless asked for)

Definitions (DEFINITIONS holds the wording shown to the user):

    start        an appearance in an edition's field (made the cut or not); qualifying stages are not
                 starts. Scope is decided by the edition's classification *when it was played*.
    win          finishing first (stroke play after any playoff; the match-play champion)
    runner-up    finishing second, including a tie for second
    major        an edition of one of the four majors
    made cut     a start with a finishing position (events without a cut count as made)
    age          the edition's year minus the birth year: the world records birth years, not dates,
                 so ages are in whole years and ties in age are broken by the earlier edition
    debut        first start in the scope, for careers that began in the archive; for earlier careers the
                 first archived start is only a "first tracked appearance" (any season, not just the first)
    scope        'all' (every tour, college and amateur event), 'professional' (tiers 0-4), 'premier'
                 (Premier Tour events and majors), 'major', or a tour key ('CH_EUROPE', ...)
"""
from __future__ import annotations

import os
import pickle
from array import array
from collections import defaultdict

DEFINITIONS = {
    'start': 'An appearance in a tournament field, whether or not the cut was made. Qualifying stages are not starts.',
    'win': 'Finishing first: after any playoff in stroke play, or as the match-play champion.',
    'runner-up': 'Finishing second, including a tie for second.',
    'major': 'An edition of the Tour Masters, Premier Tour Championship, USA Open or Britannia Open.',
    'made cut': 'A start with a finishing position; events without a cut count as made.',
    'age': 'Year of the event minus year of birth (birth dates are not recorded).',
    'debut': 'First start in the scope. For careers that began before the archive, the first start it shows is '
             'only the first tracked appearance, not the debut.',
    'scope': 'Which events count, by their classification when played: all, professional, premier, major '
             'or one tour.',
    'active': 'Still competing: the record may still change.',
    'partial': 'Career began before the archive, so earlier results are not included.',
}
SCOPES = ('all', 'professional', 'premier', 'major')


POS_BITS = 12                    # a start is one integer: (edition rank << POS_BITS) | (position + 1, 0 = no position)


class Starts:
    """Every archived start (qualifying stages excluded), compactly: each edition once, ranked in
    (year, week, event id) order, and per person an array of integers (edition rank, finishing position)
    in that order -- a few bytes a start instead of a tuple. Reading a person gives the same tuples, in the
    same order, as a list of (year, week, event id, tour, tier, kind, pos) would: made on demand."""

    def __init__(self):
        self.ed = []                             # rank -> (year, week, event id, tour, tier, kind)
        self.by = {}                             # pid -> array('q') of packed starts, ascending

    def add_editions(self, editions):
        """`editions`: [(year, week, event id, tour, tier, kind)] of seasons later than any already held;
        returns {event id: rank}."""
        self.__dict__.pop('flags', None)
        ranks = {}
        for e in sorted(editions, key=lambda e: (e[0], e[1], e[2])):
            ranks[e[2]] = len(self.ed)
            self.ed.append(e)
        return ranks

    def add(self, pid, rank, pos):
        a = self.by.get(pid)
        if a is None:
            a = self.by[pid] = array('q')
        a.append((rank << POS_BITS) | (0 if pos is None else pos + 1))

    def settle(self, pids):
        for pid in pids:                         # appended year by year: order each touched person once
            a = self.by[pid]
            if any(a[i] > a[i + 1] for i in range(len(a) - 1)):
                self.by[pid] = array('q', sorted(a))

    def __getitem__(self, pid):
        a = self.by.get(pid)
        if a is None:
            return []
        ed, mask = self.ed, (1 << POS_BITS) - 1
        return [ed[c >> POS_BITS] + (((c & mask) - 1) if c & mask else None,) for c in a]

    def __iter__(self):
        return iter(self.by)

    def __len__(self):
        return len(self.by)

    def __contains__(self, pid):
        return pid in self.by

    def items(self):
        return ((pid, self[pid]) for pid in self.by)

    def clear(self):
        self.ed.clear()
        self.by.clear()
        self.__dict__.pop('flags', None)

    def scoped(self, pid, scope, test):
        """self[pid] restricted to the starts whose edition passes test(start, scope) -- a test of the
        edition only (tour, tier, kind) -- worked out once per edition rather than once per start: the same
        tuples in the same order."""
        a = self.by.get(pid)
        if a is None:
            return []
        flags = self.__dict__.setdefault('flags', {})
        ok = flags.get(scope)
        if ok is None or len(ok) != len(self.ed):
            ok = flags[scope] = bytes(1 if test(e + (None,), scope) else 0 for e in self.ed)
        ed, mask = self.ed, (1 << POS_BITS) - 1
        return [ed[c >> POS_BITS] + (((c & mask) - 1) if c & mask else None,) for c in a if ok[c >> POS_BITS]]


class HistoryStats:
    """Records from the archive. Starts are held compactly (Starts) and read from the archive's index
    when it has one (one query per season, no season file decoded), otherwise from the season files;
    prize totals and coaches' major champions are index aggregates when there is an index. The record
    definitions, ties and evidence are the same either way (tested against each other)."""

    def __init__(self, archive):
        self.a = archive
        self.complete = True
        self.starts = Starts()                   # pid -> [(year, week, event id, tour, tier, kind, pos)], in order
        self.seen = set()                        # seasons already read
        self.sig = {}                            # season -> its file's signature when read
        self.extend(archive)

    def extend(self, archive):
        """Bring the statistics up to date with `archive` (a newer reading of the same world): only the
        seasons not seen before are read, and people, relationships and records come from it. If the
        history did not simply grow -- a season read before is gone or was published again (a recovery
        fell back to an earlier checkpoint) -- everything is read again, so no removed result stays.
        Recoverable: if reading fails part way, the statistics are marked incomplete and the next call
        reads everything again (no season is half-counted or counted twice)."""
        sign = getattr(archive, 'signature', lambda y: None)
        if not getattr(self, 'complete', True) or \
                any(y not in archive.years or sign(y) != self.sig.get(y) for y in self.seen):
            self.starts.clear()
            self.seen.clear()
            self.sig.clear()
        new = [y for y in archive.years if y not in self.seen]
        if new and self.seen and min(new) < max(self.seen):   # a gap filled in: start again, in order
            self.starts.clear()
            self.seen.clear()
            self.sig.clear()
            new = list(archive.years)
        idx = getattr(archive, 'index', None)
        touched = set()
        self.complete = False                        # until every new season is in
        for y in new:                                # season by season: nothing more than one season in memory
            if idx is not None:
                editions, rows = self._from_index(archive, idx, y)
            else:
                editions, rows = self._from_files(archive, y)
            ranks = self.starts.add_editions(editions)
            for gid, eid, pos in rows:
                self.starts.add(gid, ranks[eid], pos)
                touched.add(gid)
        self.starts.settle(touched)
        self.seen.update(new)
        self.sig.update((y, sign(y)) for y in new)
        self.a = archive
        self.complete = True
        self.boards = {}                             # (record lists worked out again from this reading)
        self.dirty = getattr(self, 'dirty', False) or bool(new)
        return new

    # ---- a cache beside the world (derived: rebuilt from the archive whenever it does not match) ------------
    CACHE_FORMAT = 1

    def dump(self, path):
        """Write the starts read so far, with each season's signature, for a later reading of this world."""
        if not self.complete:
            return
        path = os.fspath(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + '.tmp'
        with open(tmp, 'wb') as f:
            pickle.dump({'format': self.CACHE_FORMAT, 'ed': self.starts.ed, 'by': self.starts.by,
                         'seen': sorted(self.seen), 'sig': self.sig, 'sizes': _sizes(self.a, self.seen),
                         'boards': dict(getattr(self, 'boards', {}))}, f,
                        protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp, path)
        self.dirty = False

    @classmethod
    def from_cache(cls, path, archive):
        """The statistics from a cache written by dump, brought up to date with `archive`; None if there is no
        usable cache (missing, another format, or any season in it no longer published exactly as it was:
        then nothing of it is trusted and everything is read again)."""
        sign = getattr(archive, 'signature', None)
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
        except Exception:
            return None
        if sign is None or not isinstance(data, dict) or data.get('format') != cls.CACHE_FORMAT:
            return None
        if any(y not in archive.years or sign(y) != data['sig'].get(y) for y in data['seen']):
            return None
        if data.get('sizes') != _sizes(archive, data['seen']):   # (season files are named alike in every world)
            return None
        st = cls.__new__(cls)
        st.a, st.complete, st.dirty = archive, True, False
        st.starts = Starts()
        st.starts.ed, st.starts.by = data['ed'], data['by']
        st.seen, st.sig = set(data['seen']), dict(data['sig'])
        if not st.extend(archive):                   # no season published since: the lists worked out then hold
            st.boards = dict(data.get('boards') or {})
        return st

    @staticmethod
    def _classify(archive, series, tour, tier, category):
        meta = archive.world['series'].get(series, {})
        tier = meta.get('tier') if tier is None else tier
        tour = meta.get('tour') if tour is None else tour
        kind = 'major' if (category if category is not None else meta.get('category')) == 'major' else meta.get('kind', '')
        return tour, tier, kind

    def _from_files(self, archive, y):
        editions, rows = [], []
        for _, e in archive.events([y]):
            tour, tier, kind = self._classify(archive, e['series'], e.get('tour'), e.get('tier'), e.get('category'))
            if kind == 'qualifying':
                continue
            editions.append((y, e['week'], e['id'], tour, tier, kind))
            rows += [(gid, e['id'], pos) for site in e['finish'] for gid, pos, _ in site]
        return editions, rows

    def _from_index(self, archive, idx, y):
        editions, keep = [], set()
        for eid, week, series, tour, tier, category in idx.db.execute(
                'SELECT event_id, week, series, tour, tier, category FROM editions WHERE year = ?', (y,)):
            tour, tier, kind = self._classify(archive, series, tour, tier, category)
            if kind != 'qualifying':
                editions.append((y, week, eid, tour, tier, kind))
                keep.add(eid)
        rows = [r for r in idx.db.execute('SELECT s.person, e.event_id, s.pos FROM starts s JOIN editions e USING(eid) '
                                          'WHERE s.year = ?', (y,)) if r[1] in keep]
        return editions, rows

    # ---- the shared vocabulary ------------------------------------------------------------------------
    @staticmethod
    def in_scope(start, scope):
        y, w, eid, tour, tier, kind, pos = start
        if scope == 'all':
            return True
        if scope == 'professional':
            return tier is not None and tier <= 4
        if scope == 'premier':
            return tier in (0, 1)
        if scope == 'major':
            return kind == 'major'
        return tour == scope

    def flags(self, pid):
        p = self.a.people.get(pid, {})
        golfer = p.get('golfer', {})
        return {'active': golfer.get('lifestyle') not in (None, 'retired'), 'partial': bool(p.get('initial'))}

    def age(self, pid, year):
        born = self.a.people.get(pid, {}).get('born')
        return year - born if born else None

    def _row(self, pid, value, evidence=(), **extra):
        return {'person': pid, 'name': self.a.name(pid), 'value': value, 'evidence': list(evidence),
                **self.flags(pid), **extra}

    @staticmethod
    def _top(rows, n, reverse=True, key=None):
        key = key or (lambda r: r['value'])
        return sorted(rows, key=lambda r: ((-key(r) if reverse else key(r)), r['person']))[:n]

    def _scoped(self, pid, scope):
        return self.starts.scoped(pid, scope, self.in_scope)

    # ---- career totals ------------------------------------------------------------------------------------
    def most_wins(self, scope='all', n=25):
        rows = []
        for pid in self.starts:
            wins = [s[2] for s in self._scoped(pid, scope) if s[6] == 1]
            if wins:
                rows.append(self._row(pid, len(wins), wins))
        return self._top(rows, n)

    def most_majors(self, n=25):
        return self.most_wins('major', n)

    def most_starts(self, scope='all', n=25):
        rows = [self._row(pid, len(ss)) for pid in self.starts if (ss := self._scoped(pid, scope))]
        return self._top(rows, n)

    def most_prize(self, n=25):
        total = defaultdict(int)
        idx = getattr(self.a, 'index', None)
        if idx is not None:                          # an aggregate over the index's season rows
            for pid, prize in idx.db.execute('SELECT person, SUM(COALESCE(prize, 0)) FROM seasons WHERE 1=1'
                                             + idx.upto() + ' GROUP BY person'):
                total[pid] = prize
        else:
            for y in self.a.years:
                for pid, row in self.a.year(y)['careers'].items():
                    total[pid] += row.get('prize') or 0
        return self._top([self._row(pid, v) for pid, v in total.items() if v > 0], n)

    # ---- age -----------------------------------------------------------------------------------------------
    def winners_by_age(self, scope='all', youngest=True, n=25):
        """Each win is a row (a golfer can appear more than once); the evidence is the edition."""
        rows = []
        for pid, ss in self.starts.items():
            for s in ss:
                if s[6] == 1 and self.in_scope(s, scope):
                    a = self.age(pid, s[0])
                    if a is not None:
                        rows.append(self._row(pid, a, [s[2]], year=s[0], week=s[1]))
        return sorted(rows, key=lambda r: ((r['value'] if youngest else -r['value']), r['year'], r['week'],
                                           r['person']))[:n]

    def debuts_by_age(self, scope='premier', youngest=True, n=25, include_partial=False):
        """First start in the scope: a career debut only for careers that began in the archive. For a
        career that began before it, the first archived start is only the first *tracked* appearance,
        whichever season it falls in (a veteran back in year two may have played the scope long before):
        left out unless asked for, and then marked (kind 'first tracked appearance', uncertain)."""
        rows = []
        for pid in self.starts:
            ss = self._scoped(pid, scope)
            if not ss:
                continue
            first = ss[0]
            partial = self.flags(pid)['partial']
            if partial and not include_partial:
                continue
            a = self.age(pid, first[0])
            if a is not None:
                rows.append(self._row(pid, a, [first[2]], year=first[0], uncertain=partial,
                                      kind='first tracked appearance' if partial else 'career debut'))
        return sorted(rows, key=lambda r: ((r['value'] if youngest else -r['value']), r['year'], r['person']))[:n]

    # ---- persistence -----------------------------------------------------------------------------------------
    def starts_before_first_win(self, scope='all', n=25, include_partial=False):
        rows = []
        for pid in self.starts:
            ss = self._scoped(pid, scope)
            i = next((k for k, s in enumerate(ss) if s[6] == 1), None)
            if i is None or (self.flags(pid)['partial'] and not include_partial):
                continue
            rows.append(self._row(pid, i, [ss[i][2]], first_win_year=ss[i][0]))
        return self._top(rows, n)

    def most_starts_without_win(self, scope='all', n=25, status='all'):
        """status: 'active' (has not won yet), 'retired' (retired without a win) or 'all' — kept apart
        because an active career is unfinished, not failed."""
        rows = []
        for pid in self.starts:
            ss = self._scoped(pid, scope)
            if not ss or any(s[6] == 1 for s in ss):
                continue
            f = self.flags(pid)
            if status == 'active' and not f['active'] or status == 'retired' and f['active']:
                continue
            rows.append(self._row(pid, len(ss)))
        return self._top(rows, n)

    def longest_wait_between_wins(self, scope='all', n=25):
        """In starts between two consecutive wins in the scope (years noted)."""
        rows = []
        for pid in self.starts:
            ss = self._scoped(pid, scope)
            wins = [k for k, s in enumerate(ss) if s[6] == 1]
            best = None
            for a, b in zip(wins, wins[1:]):
                gap = b - a - 1
                if best is None or gap > best[0]:
                    best = (gap, ss[a], ss[b])
            if best:
                rows.append(self._row(pid, best[0], [best[1][2], best[2][2]], years=(best[1][0], best[2][0])))
        return self._top(rows, n)

    def most_runner_ups_without_win(self, scope='all', n=25):
        rows = []
        for pid in self.starts:
            ss = self._scoped(pid, scope)
            if ss and not any(s[6] == 1 for s in ss):
                seconds = [s[2] for s in ss if s[6] == 2]
                if seconds:
                    rows.append(self._row(pid, len(seconds), seconds))
        return self._top(rows, n)

    def major_droughts_ended(self, n=25):
        """Major starts before a first major win (or between two major wins), for droughts that ended."""
        rows = []
        for pid in self.starts:
            ss = self._scoped(pid, 'major')
            last, best = -1, None
            for k, s in enumerate(ss):
                if s[6] == 1:
                    gap = k - last - 1
                    if gap > 0 and (best is None or gap > best[0]):
                        best = (gap, s)
                    last = k
            if best and not (last == -1):
                rows.append(self._row(pid, best[0], [best[1][2]], ended=best[1][0]))
        return self._top(rows, n)

    # ---- unusual careers and dominance ------------------------------------------------------------------------
    def wins_on_most_tours(self, n=25):
        rows = []
        for pid, ss in self.starts.items():
            tours = {}
            for s in ss:
                if s[6] == 1 and s[3] not in ('AMATEUR', 'QUALIFYING'):
                    tours.setdefault(s[3], s[2])
            if tours:
                rows.append(self._row(pid, len(tours), list(tours.values()), tours=sorted(tours)))
        return self._top(rows, n)

    def _longest_run(self, test, scope, n):
        rows = []
        for pid in self.starts:
            ss = self._scoped(pid, scope)
            best, cur, start = 0, 0, None
            best_ev = []
            for s in ss:
                if test(s):
                    cur += 1
                    start = start if cur > 1 else s
                    if cur > best:
                        best, best_ev = cur, [start[2], s[2]]
                else:
                    cur = 0
            if best:
                rows.append(self._row(pid, best, best_ev))
        return self._top(rows, n)

    def consecutive_wins(self, scope='all', n=25):
        return self._longest_run(lambda s: s[6] == 1, scope, n)

    def consecutive_cuts_made(self, scope='professional', n=25):
        return self._longest_run(lambda s: s[6] is not None, scope, n)

    def most_moments(self, kind='hole-in-one', n=25):
        """Most holes-in-one (or albatrosses, playoff wins, course records) — moments recorded as facts."""
        got = defaultdict(list)
        for m in self.a.moments(kind=kind) if hasattr(self.a, 'moments') else ():
            got[m['person']].append(m['event'])
        return self._top([self._row(pid, len(ev), ev) for pid, ev in got.items()], n)

    def weeks_at_number_one(self, n=25):
        return self._top([self._row(pid, w) for pid, w in self.a.weeks_at_number_one().items()], n)

    # ---- relationships ---------------------------------------------------------------------------------------
    def longest_partnerships(self, kind='coach', n=25):
        """Stints by length in weeks (an unfinished stint counts to the archive's last season)."""
        last = (self.a.years[-1], 52)
        rows = []
        for s in self.a.rel.stints:
            if s.kind != kind or not s.staff:
                continue
            end = s.end or last
            weeks = (end[0] - s.start[0]) * 52 + end[1] - s.start[1]
            r = self._row(s.golfer, weeks, staff=s.staff, staff_name=self.a.name(s.staff), start=s.start, end=s.end,
                          current=s.end is None)
            rows.append(r)
        return self._top(rows, n)

    def coaches_with_most_major_champions(self, n=25):
        """Distinct golfers who won a major while this person coached them (the coach recorded with the
        result). Association, not causation."""
        champs = defaultdict(dict)
        idx = getattr(self.a, 'index', None)
        if idx is not None:                          # winners at every site of every major, in archive order
            series = self.a.world['series']
            for gid, coach, eid, ser, cat in idx.db.execute(
                    'SELECT s.person, s.coach, e.event_id, e.series, e.category FROM starts s JOIN editions e USING(eid) '
                    'WHERE s.pos = 1 AND s.coach' + idx.upto('e.year') + ' ORDER BY e.year, e.eid, s.site'):
                if (cat if cat is not None else series.get(ser, {}).get('category')) == 'major':
                    champs[coach].setdefault(gid, eid)
        else:
            for y, e in self.a.events():
                if e.get('category', self.a.world['series'].get(e['series'], {}).get('category')) != 'major':
                    continue
                for site in e['finish']:
                    for gid, pos, _ in site:
                        if pos == 1:
                            coach = e['team'].get(gid, (0, 0))[0]
                            if coach:
                                champs[coach].setdefault(gid, e['id'])
        rows = [dict(self._row(c, len(g), list(g.values())), golfers=sorted(g)) for c, g in champs.items()]
        return self._top(rows, n)


BOARDS = {   # name -> (title, function name, keyword arguments): the lists the UI can open
    'most-wins': ('Most professional wins', 'most_wins', {'scope': 'professional'}),
    'most-wins-all-events': ('Most wins in any event (college, amateur and club-professional included)', 'most_wins', {}),
    'most-premier-wins': ('Most Premier Tour and major wins', 'most_wins', {'scope': 'premier'}),
    'most-majors': ('Most majors', 'most_majors', {}),
    'most-starts': ('Most starts', 'most_starts', {}),
    'most-prize': ('Most prize money', 'most_prize', {}),
    'youngest-winners': ('Youngest winners', 'winners_by_age', {'youngest': True}),
    'oldest-winners': ('Oldest winners', 'winners_by_age', {'youngest': False}),
    'youngest-major-champions': ('Youngest major champions', 'winners_by_age', {'scope': 'major', 'youngest': True}),
    'oldest-major-champions': ('Oldest major champions', 'winners_by_age', {'scope': 'major', 'youngest': False}),
    'youngest-premier-debuts': ('Youngest Premier debutants', 'debuts_by_age', {'youngest': True}),
    'oldest-premier-debuts': ('Oldest Premier debutants', 'debuts_by_age', {'youngest': False}),
    'starts-before-first-win': ('Most starts before a first win', 'starts_before_first_win', {}),
    'not-won-yet': ('Most starts, has not won yet', 'most_starts_without_win', {'status': 'active'}),
    'retired-without-a-win': ('Most starts, retired without a win', 'most_starts_without_win', {'status': 'retired'}),
    'longest-wait-between-wins': ('Longest wait between wins', 'longest_wait_between_wins', {}),
    'runner-ups-without-a-win': ('Most runner-up finishes without a win', 'most_runner_ups_without_win', {}),
    'major-droughts-ended': ('Longest major droughts ended', 'major_droughts_ended', {}),
    'wins-on-most-tours': ('Wins on the most different tours', 'wins_on_most_tours', {}),
    'consecutive-wins': ('Most consecutive professional wins', 'consecutive_wins', {'scope': 'professional'}),
    'consecutive-cuts': ('Most consecutive cuts made (professional events)', 'consecutive_cuts_made', {}),
    'weeks-at-number-one': ('Weeks at world No. 1', 'weeks_at_number_one', {}),
    'most-holes-in-one': ('Most holes-in-one', 'most_moments', {'kind': 'hole-in-one'}),
    'most-playoff-wins': ('Most playoff wins', 'most_moments', {'kind': 'playoff'}),
    'most-course-records': ('Most course records set', 'most_moments', {'kind': 'course record'}),
    'longest-coach-partnerships': ('Longest coach partnerships', 'longest_partnerships', {'kind': 'coach'}),
    'longest-caddie-partnerships': ('Longest caddie partnerships', 'longest_partnerships', {'kind': 'caddie'}),
    'coaches-major-champions': ('Coaches who worked with the most major champions', 'coaches_with_most_major_champions', {}),
}


def _sizes(archive, years):
    """Each season file's size: with the signatures, what tells this world's history from another's."""
    out = {}
    for y in sorted(years):
        try:
            out[y] = archive.year_path(y).stat().st_size
        except (OSError, AttributeError):
            out[y] = None
    return out


def board(stats, name, n=25, **overrides):
    """A record list, worked out once per reading of the history (stats.extend starts again)."""
    title, fn, kw = BOARDS[name]
    memo = stats.__dict__.setdefault('boards', {})
    key = (name, n, tuple(sorted(overrides.items())))
    if key not in memo:
        memo[key] = getattr(stats, fn)(n=n, **{**kw, **overrides})
        stats.dirty = True                           # (kept with the cache next time it is written)
    return title, [dict(r) for r in memo[key]]
