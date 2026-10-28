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
    debut        first start in the scope; uncertain (partial) for careers that began before the archive
    scope        'all' (every tour, college and amateur event), 'professional' (tiers 0-4), 'premier'
                 (Premier Tour events and majors), 'major', or a tour key ('CH_EUROPE', ...)
"""
from __future__ import annotations

from collections import defaultdict

DEFINITIONS = {
    'start': 'An appearance in a tournament field, whether or not the cut was made. Qualifying stages are not starts.',
    'win': 'Finishing first: after any playoff in stroke play, or as the match-play champion.',
    'runner-up': 'Finishing second, including a tie for second.',
    'major': 'An edition of the Tour Masters, Premier Tour Championship, USA Open or Britannia Open.',
    'made cut': 'A start with a finishing position; events without a cut count as made.',
    'age': 'Year of the event minus year of birth (birth dates are not recorded).',
    'debut': 'First start in the scope. Careers that began before the archive have uncertain debuts.',
    'scope': 'Which events count, by their classification when played: all, professional, premier, major '
             'or one tour.',
    'active': 'Still competing: the record may still change.',
    'partial': 'Career began before the archive, so earlier results are not included.',
}
SCOPES = ('all', 'professional', 'premier', 'major')


class HistoryStats:
    def __init__(self, archive):
        self.a = archive
        self.starts = defaultdict(list)          # pid -> [(year, week, event id, tour, tier, kind, pos)], in order
        for y, e in archive.events():
            meta = archive.world['series'].get(e['series'], {})
            tier = e.get('tier', meta.get('tier'))
            tour = e.get('tour', meta.get('tour'))
            kind = 'major' if e.get('category', meta.get('category')) == 'major' else meta.get('kind', '')
            if kind == 'qualifying':
                continue
            for site in e['finish']:
                for gid, pos, _ in site:
                    self.starts[gid].append((y, e['week'], e['id'], tour, tier, kind, pos))
        for rows in self.starts.values():
            rows.sort()

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
        return [s for s in self.starts[pid] if self.in_scope(s, scope)]

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
        """First start in the scope. Careers that began before the archive are left out unless asked for
        (their first archived start is not necessarily their debut) — and flagged when included."""
        rows = []
        for pid in self.starts:
            ss = self._scoped(pid, scope)
            if not ss:
                continue
            first = ss[0]
            partial = self.flags(pid)['partial'] and first[0] == self.a.world.get('first_year', self.a.years[0])
            if partial and not include_partial:
                continue
            a = self.age(pid, first[0])
            if a is not None:
                rows.append(self._row(pid, a, [first[2]], year=first[0], uncertain=partial))
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


def board(stats, name, n=25, **overrides):
    title, fn, kw = BOARDS[name]
    return title, getattr(stats, fn)(n=n, **{**kw, **overrides})
