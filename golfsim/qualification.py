"""How golfers get into the four majors, modelled on the real-life routes.

Each major has an ordered list of routes:

* **Exemption categories** (past champions, recent major winners, ranking cut-offs, amateur titles ...).
  Everyone who satisfies one is in. Every entrant records ALL the categories they satisfy; the first
  one in the list is their primary entry source.
* **Qualifying routes** (designated events and qualifying stages). Spots go to the best finishers who
  are not already in the field -- if an exempt player finishes in a qualifying place, the spot passes
  down to the next finisher, as in real life.
* **Fill** (USA Open, Britannia Open, Premier Tour Championship): alternates in order until the field
  size is reached. The Tour Masters is invitation-only and is never filled up.

Real-life analogues: Tour Masters = the Masters, Premier Tour Championship = the PGA Championship,
USA Open = the U.S. Open, Britannia Open = The Open Championship.

The rules only read facts from a `QualificationContext`: people, results, rankings and tour
standings. The season simulation will fill that context in; tests and demos can build one by hand.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from . import schedule as SCH

MAJOR_SERIES = ('TOUR_MASTERS', 'PREMIER_TOUR_CHAMPIONSHIP', 'USA_OPEN', 'BRITANNIA_OPEN')
MAJOR_WEEK = dict(SCH.V1.majors)          # the classic calendar's weeks (a context's own: ctx.major_week)
FIELD_SIZE = {'TOUR_MASTERS': None, 'PREMIER_TOUR_CHAMPIONSHIP': 156, 'USA_OPEN': 156, 'BRITANNIA_OPEN': 156}
OTHER_MAJORS = {m: tuple(x for x in MAJOR_SERIES if x != m) for m in MAJOR_SERIES}


# ---------------------------------------------------------------------------------------------
# Facts the rules read
# ---------------------------------------------------------------------------------------------
@dataclass
class Person:
    id: int
    name: str
    status: str = 'pro'           # 'pro', 'amateur' or 'club_pro'
    age: int = 30
    country: str = 'USA'
    active: bool = True


class FutureSnapshot(LookupError):
    """A rule asked for a ranking or points list not yet published at the moment it is applied (a cut-off
    snapshot is read only once its week is over: never a later list standing in for it, never an earlier one)."""


@dataclass
class QualificationContext:
    people: dict = field(default_factory=dict)                 # id -> Person
    results: dict = field(default_factory=dict)                # (series_id, year) -> {site: [(id, pos)]}
    event_weeks: dict = field(default_factory=dict)            # series_id -> week
    world_rankings: dict = field(default_factory=dict)         # (year, week) -> [ids in rank order]
    amateur_rankings: dict = field(default_factory=dict)       # (year, week) -> [ids in rank order]
    standings: dict = field(default_factory=dict)              # (tour, year) final, or (tour, year, week) in-season
    tour_of: dict = field(default_factory=dict)                # series_id -> tour key
    category_of: dict = field(default_factory=dict)            # series_id -> calendar category
    version: str = SCH.LEGACY                                  # the calendar (schedule.Spec) the rules follow
    horizon: tuple = None                                      # (year, week): facts from then on are unknown
    awards: dict = field(default_factory=dict)                 # ('amateur_award', year) -> gid (or None)
    edition_weeks: dict = field(default_factory=dict)          # (series_id, year) -> week it was played

    # -- recording ---------------------------------------------------------------------------
    def add_result(self, series_id, year, finishers, site=0, week=None):
        """finishers: [(id, position)] in finishing order; position None = missed cut. week: when the edition
        was played (its actual date, kept so a rule never reads a later calendar's week into the past)."""
        self.results.setdefault((series_id, year), {})[site] = list(finishers)
        if week is not None:
            self.__dict__.setdefault('edition_weeks', {})[(series_id, year)] = week

    def edition_week(self, series_id, year):
        """The week an edition was played (recorded), else its series' week in this calendar."""
        w = self.__dict__.get('edition_weeks', {}).get((series_id, year))
        return w if w is not None else self.event_weeks.get(series_id)

    def major_week(self, major):
        return SCH.spec(self.version).majors[major]

    def snapshot(self, year, week, amateur=False):
        """The ranking published at the end of `week` of `year` exactly (an immutable cut-off snapshot): [] if
        it was never recorded (before the world began), FutureSnapshot if it is not published yet in this view."""
        h = self.__dict__.get('horizon')
        if h is not None and (year, week) >= h:
            raise FutureSnapshot(f'ranking after week {week} of {year} is not published before week {h[1]} of {h[0]}')
        return (self.amateur_rankings if amateur else self.world_rankings).get((year, week), [])

    def standing_snapshot(self, tour_key, year, week):
        """A points list exactly as published after `week` (FutureSnapshot before then)."""
        h = self.__dict__.get('horizon')
        if h is not None and (year, week) >= h:
            raise FutureSnapshot(f'{tour_key} points after week {week} of {year} are not published before week '
                                 f'{h[1]} of {h[0]}')
        return self.standings.get((tour_key, year, week))

    def award(self, name, year):
        return self.__dict__.get('awards', {}).get((name, year))

    @classmethod
    def from_calendar(cls, calendar, **kw):
        ctx = cls(**kw)
        ctx.version = getattr(calendar, 'version', SCH.LEGACY)
        for s in calendar.series:
            ctx.event_weeks[s.series_id] = s.week
            ctx.tour_of[s.series_id] = s.tour
            ctx.category_of[s.series_id] = s.category
        return ctx

    # -- queries -----------------------------------------------------------------------------
    def finishers(self, series_id, year, site=None):
        sites = self.results.get((series_id, year), {})
        if site is not None:
            return sites.get(site, [])
        return sorted((x for rows in sites.values() for x in rows), key=lambda r: (r[1] is None, r[1] or 0))

    def placed(self, series_id, year, max_pos):
        return [gid for gid, pos in self.finishers(series_id, year) if pos is not None and pos <= max_pos]

    def winner(self, series_id, year):
        top = [gid for gid, pos in self.finishers(series_id, year) if pos == 1]
        return top[0] if top else None

    def ranking(self, year, week, amateur=False):
        table = self.amateur_rankings if amateur else self.world_rankings
        keys = [k for k in table if k <= (year, week)]
        return table[max(keys)] if keys else []

    def standing(self, tour_key, year, week=None):
        """Final standings of a season, or the latest in-season snapshot at or before `week`."""
        if week is None:
            return self.standings.get((tour_key, year), [])
        snaps = [k for k in self.standings if len(k) == 3 and k[0] == tour_key and k[1] == year and k[2] <= week]
        return self.standings[max(snaps)] if snaps else []

    def as_of(self, year, week):
        """A view containing only facts known before `week` of `year` (no hindsight)."""
        def known(y, wk):
            return y < year or (y == year and wk < week)
        h = self.__dict__.get('horizon')
        view = QualificationContext(self.people, {}, self.event_weeks, {}, {}, {}, self.tour_of, self.category_of,
                                    version=self.version, horizon=min(h, (year, week)) if h else (year, week),
                                    edition_weeks=self.__dict__.get('edition_weeks', {}))
        cut = SCH.spec(self.version).cutoffs                # an award is known once the week it follows is over
        view.awards = {k: v for k, v in self.__dict__.get('awards', {}).items() if known(k[1], cut.get(k[0], 52))}
        view.results = {k: v for k, v in self.results.items() if known(k[1], self.edition_week(k[0], k[1]) or 0)}
        view.world_rankings = {k: v for k, v in self.world_rankings.items() if known(*k)}
        view.amateur_rankings = {k: v for k, v in self.amateur_rankings.items() if known(*k)}
        view.standings = {k: v for k, v in self.standings.items()
                          if (len(k) == 2 and k[1] < year) or (len(k) == 3 and known(k[1], k[2]))}
        return view

    def available(self, gid):
        p = self.people.get(gid)
        return p is not None and p.active


# ---------------------------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Route:
    code: str
    label: str
    analogue: str                  # the real-life rule it mirrors
    select: object                 # function(ctx, year) -> ordered list of ids
    kind: str = 'exempt'           # exempt / qualifying / fill
    amateur_only: bool = False
    status: str = ''               # required status, e.g. 'club_pro'
    max_age: int = 0
    spots: int = 0                 # qualifying routes: places on offer (0 = all who qualify)
    site_spots: tuple = ()         # qualifying stages: places per site
    alternates: bool = False       # next finishers become first alternates for the field
    cutoff: bool = False           # decided by a ranking or points list published during the major's own
                                   # season: never a place secured in advance
    source: tuple = ()             # where the right comes from, for the rights ledger: ((series id, year
                                   # offset), ...) or (('ranking' | 'points' | 'award', week, year offset),)


def winners_of(series_ids, years_back, include_current=True):
    """Champions of any listed series in the last `years_back` editions (current year if already played)."""
    def select(ctx, year):
        out = []
        first = year - years_back + (0 if include_current else 1)
        for y in range(year, first - 1, -1):
            for sid in series_ids:
                if y == year and not include_current:
                    continue
                w = ctx.winner(sid, y)
                if w is not None and w not in out:
                    out.append(w)
        return out
    return select


def lifetime_winners(series_id):
    def select(ctx, year):
        ys = sorted({y for (sid, y) in ctx.results if sid == series_id and y < year}, reverse=True)
        out = []
        for y in ys:
            w = ctx.winner(series_id, y)
            if w is not None and w not in out:
                out.append(w)
        return out
    return select


def top_finishers(series_id, n, year_offset=-1):
    def select(ctx, year):
        return ctx.placed(series_id, year + year_offset, n)
    return select


def top_finishers_of(series_ids, n, year_offset=-1):
    def select(ctx, year):
        out = []
        for sid in series_ids:
            out += [g for g in ctx.placed(sid, year + year_offset, n) if g not in out]
        return out
    return select


def places(series_id, positions, year_offset=-1):
    """Winner (1) and/or runner-up (2) of an event, e.g. an amateur championship final."""
    def select(ctx, year):
        return [gid for gid, pos in ctx.finishers(series_id, year + year_offset) if pos in positions]
    return select


def ranking_top(n, week, year_offset=0, amateur=False):
    def select(ctx, year):
        return ctx.ranking(year + year_offset, week, amateur)[:n]
    return select


def standing_top(tour_key, n, year_offset=-1):
    def select(ctx, year):
        return ctx.standing(tour_key, year + year_offset)[:n]
    return select


def points_list(tour_key, week, start=0, stop=None):
    """This season's points list as of `week`, falling back to last season's final standings."""
    def select(ctx, year):
        rows = ctx.standing(tour_key, year, week) or ctx.standing(tour_key, year - 1)
        return rows[start:stop]
    return select


def standing_leaders(tour_keys, year_offset=-1):
    def select(ctx, year):
        return [ctx.standing(t, year + year_offset)[0] for t in tour_keys if ctx.standing(t, year + year_offset)]
    return select


def tour_winners_between(predicate, start, end):
    """Winners of events matching predicate(series_id, ctx) between (year offset, week) bounds."""
    def select(ctx, year):
        lo, hi = (year + start[0], start[1]), (year + end[0], end[1])
        out = []
        for (sid, y) in sorted(ctx.results, key=lambda k: (k[1], ctx.event_weeks.get(k[0], 0))):
            wk = ctx.event_weeks.get(sid)
            if wk is None or not (lo <= (y, wk) <= hi) or not predicate(sid, ctx):
                continue
            w = ctx.winner(sid, y)
            if w is not None and w not in out:
                out.append(w)
        return out
    return select


def qualifier_finishers(series_ids, year_offset=0):
    """Ordered finishers of designated events (best place first), for qualifying routes."""
    def select(ctx, year):
        return [[gid for gid, pos in ctx.finishers(sid, year + year_offset) if pos is not None] for sid in series_ids]
    return select


def stage_sites(series_ids, year_offset=0):
    def select(ctx, year):
        sites = []
        for sid in series_ids:
            for site, rows in sorted(ctx.results.get((sid, year + year_offset), {}).items()):
                sites.append([gid for gid, pos in rows if pos is not None])
        return sites
    return select


def ranking_fill(week, year_offset=0):
    def select(ctx, year):
        return ctx.ranking(year + year_offset, week)
    return select


def snapshot_top(n, week, year_offset=0, amateur=False):
    """The top n of the ranking published after `week` exactly (v2: an immutable cut-off snapshot)."""
    def select(ctx, year):
        return ctx.snapshot(year + year_offset, week, amateur)[:n]
    return select


def snapshot_fill(week, year_offset=0):
    def select(ctx, year):
        return ctx.snapshot(year + year_offset, week)
    return select


def points_snapshot(tour_key, week, start=0, stop=None):
    """This season's points list exactly as published after `week` (last season's final standings only if no
    list was recorded, e.g. a season played before in-season lists were kept)."""
    def select(ctx, year):
        rows = ctx.standing_snapshot(tour_key, year, week)
        if rows is None:
            rows = ctx.standing(tour_key, year - 1)
        return rows[start:stop]
    return select


def winners_since_major(predicate, major, through):
    """Winners of events matching predicate from the week after last season's edition of `major` (as it was
    actually played) through week `through` of this season."""
    def select(ctx, year):
        prior = ctx.edition_week(major, year - 1)
        lo, hi = (year - 1, (prior if prior is not None else ctx.major_week(major)) + 1), (year, through)
        out = []
        for (sid, y) in sorted(ctx.results, key=lambda k: (k[1], ctx.edition_week(*k) or 0)):
            wk = ctx.edition_week(sid, y)
            if wk is None or not (lo <= (y, wk) <= hi) or not predicate(sid, ctx):
                continue
            w = ctx.winner(sid, y)
            if w is not None and w not in out:
                out.append(w)
        return out
    return select


def amateur_award(year_offset=-1):
    """The annual amateur award winner of an earlier season (named after the USA Amateur, published the next
    week); nobody for a season with no recorded award (never an invented winner)."""
    def select(ctx, year):
        g = ctx.award('amateur_award', year + year_offset)
        return [g] if g is not None else []
    return select


def _is_premier_full_points(sid, ctx):
    return ctx.tour_of.get(sid) == 'PT_AMERICAS' and ctx.category_of.get(sid) != 'opportunity' or \
        (ctx.tour_of.get(sid, '').startswith('PT_') and ctx.category_of.get(sid) == 'flagship')


def _is_premier(sid, ctx):
    return ctx.tour_of.get(sid, '').startswith('PT_')


# ---------------------------------------------------------------------------------------------
# The four majors
# ---------------------------------------------------------------------------------------------
MAJOR_WINNER_SETS = {m: OTHER_MAJORS[m] for m in MAJOR_SERIES}

def _rules(sp):
    """Each major's routes under calendar specification `sp` (schedule.Spec). v1 is the classic rule set
    exactly as it always was; v2 reads the reference calendar's cut-offs from immutable snapshots, sends each
    amateur title to the edition its date allows, keeps champion and runner-up entitlements apart and adds
    the season's annual amateur award (after the USA Amateur) for next season's USA and Britannia Opens."""
    c = sp.cutoffs
    v2 = sp.snapshots
    top = snapshot_top if v2 else ranking_top
    fill = snapshot_fill if v2 else ranking_fill
    pts = points_snapshot if v2 else points_list
    since = (lambda pred, major, through: winners_since_major(pred, major, through)) if v2 else \
        (lambda pred, major, through: tour_winners_between(pred, (-1, c[{'TOUR_MASTERS': 'masters_wins_from',
                                                                         'PREMIER_TOUR_CHAMPIONSHIP': 'pga_wins_from'}[major]]),
                                                           (0, through)))
    if v2:
        usa_am = (Route('M4', 'USA Amateur champion', 'U.S. Amateur champion', places('USA_AMATEUR', (1,)),
                        amateur_only=True, source=(('USA_AMATEUR', -1),)),
                  Route('M4R', 'USA Amateur runner-up', 'U.S. Amateur runner-up', places('USA_AMATEUR', (2,)),
                        amateur_only=True, source=(('USA_AMATEUR', -1),)))
    else:
        usa_am = (Route('M4', 'USA Amateur champion and runner-up', 'U.S. Amateur champion and runner-up',
                        places('USA_AMATEUR', (1, 2)), amateur_only=True),)
    masters = (
        Route('M1', 'Past Tour Masters champions', 'Masters champions (lifetime)', lifetime_winners('TOUR_MASTERS'),
              source=(('wins', ('TOUR_MASTERS',), 0),)),
        Route('M2', 'Major champions, last 5 years', 'US Open, Open and PGA champions (5 years)',
              winners_of(OTHER_MAJORS['TOUR_MASTERS'], 5), source=(('wins', OTHER_MAJORS['TOUR_MASTERS'], 5),)),
        Route('M3', 'Premier Players Championship winners, last 3 years', 'Players Championship winners (3 years)',
              winners_of(('PT_PREMIER_PLAYERS_CHAMPIONSHIP',), 3), source=(('wins', ('PT_PREMIER_PLAYERS_CHAMPIONSHIP',), 3),)),
        *usa_am,
        Route('M5', 'Britannia Amateur champion', 'The Amateur Championship winner',
              places('BRITANNIA_AMATEUR', (1,)), amateur_only=True, source=(('BRITANNIA_AMATEUR', -1),)),
        Route('M6', 'Asia-Pacific Amateur champion', 'Asia-Pacific Amateur champion',
              places('ASIA_PACIFIC_AMATEUR', (1,)), amateur_only=True, source=(('ASIA_PACIFIC_AMATEUR', -1),)),
        Route('M7', 'Latin America Amateur champion', 'Latin America Amateur champion',
              places('LATIN_AMERICA_AMATEUR', (1,), year_offset=0), amateur_only=True,
              source=(('LATIN_AMERICA_AMATEUR', 0),)),
        Route('M8', 'USA Mid-Amateur champion', 'U.S. Mid-Amateur champion',
              places('USA_MID_AMATEUR', (1,)), amateur_only=True, source=(('USA_MID_AMATEUR', -1),)),
        *((Route('M16', 'College national champion (last season)', 'NCAA individual champion (previous season)',
                 places('COLLEGE_NATIONAL_CHAMPIONSHIP', (1,)), amateur_only=True,
                 source=(('COLLEGE_NATIONAL_CHAMPIONSHIP', -1),)),) if v2 else ()),
        Route('M9', 'Top 12 and ties, last Tour Masters', 'Top 12 and ties, previous Masters',
              top_finishers('TOUR_MASTERS', 12), source=(('TOUR_MASTERS', -1),)),
        Route('M10', 'Top 4 and ties, last year\'s other majors', 'Top 4 and ties, previous US Open / Open / PGA',
              top_finishers_of(OTHER_MAJORS['TOUR_MASTERS'], 4), source=tuple((m, -1) for m in OTHER_MAJORS['TOUR_MASTERS'])),
        Route('M11', 'Premier Tour winners since the last Tour Masters', 'PGA Tour winners (full-points events) since previous Masters',
              since(_is_premier_full_points, 'TOUR_MASTERS', c['masters_wins_through']), source=(('wins', None, 1),)),
        Route('M12', 'Last season\'s Premier Tour Finals qualifiers', 'Tour Championship qualifiers (previous season)',
              standing_top('PT_AMERICAS', 30), source=(('standing', 'PT_AMERICAS', -1),)),
        Route('M13', 'World top 50 at the end of last year', 'OWGR top 50, final ranking of previous year',
              top(50, 52, -1), source=(('ranking', 52, -1),)),
        Route('M14', 'World top 50 two weeks before' if not v2 else f'World top 50 after week {c["masters_ranking"]}',
              'OWGR top 50, ranking published before the Masters', top(50, c['masters_ranking']), cutoff=True,
              source=(('ranking', c['masters_ranking'], 0),)),
        Route('M15', 'International invitations', 'Special invitations to international players',
              (lambda ctx, year: [g for g in ctx.snapshot(year, c['masters_ranking'])[50:100]
                                  if ctx.people[g].country not in ('USA',)]) if v2 else
              (lambda ctx, year: [g for g in ctx.ranking(year, 16)[50:100] if ctx.people[g].country not in ('USA',)]),
              kind='qualifying', spots=4),
    )
    pga = (
        Route('P1', 'Past Premier Tour Championship champions', 'PGA champions (lifetime)',
              lifetime_winners('PREMIER_TOUR_CHAMPIONSHIP'), source=(('wins', ('PREMIER_TOUR_CHAMPIONSHIP',), 0),)),
        Route('P2', 'Major champions, last 5 years', 'Masters, US Open and Open champions (5 years)',
              winners_of(OTHER_MAJORS['PREMIER_TOUR_CHAMPIONSHIP'], 5),
              source=(('wins', OTHER_MAJORS['PREMIER_TOUR_CHAMPIONSHIP'], 5),)),
        Route('P3', 'Premier Players Championship winners, last 3 years', 'Players Championship winners (3 years)',
              winners_of(('PT_PREMIER_PLAYERS_CHAMPIONSHIP',), 3), source=(('wins', ('PT_PREMIER_PLAYERS_CHAMPIONSHIP',), 3),)),
        Route('P4', 'Top 15 and ties, last Premier Tour Championship', 'Top 15 and ties, previous PGA',
              top_finishers('PREMIER_TOUR_CHAMPIONSHIP', 15), source=(('PREMIER_TOUR_CHAMPIONSHIP', -1),)),
        Route('P5', 'Top 20, Club Professional Championship', 'Top 20, PGA Professional Championship (ties for the '
              'last places settled by playoff)', qualifier_finishers(('CLUB_PRO_CHAMPIONSHIP',)), kind='qualifying',
              status='club_pro', spots=20, source=(('CLUB_PRO_CHAMPIONSHIP', 0),)),
        Route('P6', 'Top 70, Premier Tour Americas points list', 'Top 70, PGA Tour points list',
              pts('PT_AMERICAS', c['pga_points'], 0, 70), cutoff=True, source=(('points', c['pga_points'], 0),)),
        Route('P7', 'Premier Tour winners since the last Premier Tour Championship', 'PGA Tour winners since previous PGA',
              since(_is_premier, 'PREMIER_TOUR_CHAMPIONSHIP', c['pga_wins_through']), source=(('wins', None, 1),)),
        Route('P8', 'Invitations: world top 100', 'PGA of America invitations (effectively the OWGR top 100)',
              top(100, c['pga_ranking']), cutoff=True, source=(('ranking', c['pga_ranking'], 0),)),
        Route('PF', 'Alternates from the points list', 'Field filled from the PGA Tour points list',
              pts('PT_AMERICAS', c['pga_points'], 70), kind='fill'),
    )
    if v2:
        usa_amateurs = (
            Route('U2', 'USA Amateur champion', 'U.S. Amateur champion', places('USA_AMATEUR', (1,)), amateur_only=True,
                  source=(('USA_AMATEUR', -1),)),
            Route('U2R', 'USA Amateur runner-up', 'U.S. Amateur runner-up', places('USA_AMATEUR', (2,)),
                  amateur_only=True, source=(('USA_AMATEUR', -1),)),
            Route('U3', 'USA Mid-Amateur champion', 'U.S. Mid-Amateur champion', places('USA_MID_AMATEUR', (1,)),
                  amateur_only=True, source=(('USA_MID_AMATEUR', -1),)),
            # played in week 26, after this season's USA Open: its champion is in next season's
            Route('U4', 'Britannia Amateur champion (last season)', 'The Amateur Championship winner',
                  places('BRITANNIA_AMATEUR', (1,)), amateur_only=True, source=(('BRITANNIA_AMATEUR', -1),)),
            Route('UA', 'Annual amateur award (last season)', 'Mark McCormack Medal (previous year)',
                  amateur_award(), amateur_only=True, source=(('award', c['amateur_award'], -1),)),
        )
    else:
        usa_amateurs = (
            Route('U2', 'USA Amateur champion and runner-up', 'U.S. Amateur champion and runner-up',
                  places('USA_AMATEUR', (1, 2)), amateur_only=True),
            Route('U3', 'USA Mid-Amateur champion', 'U.S. Mid-Amateur champion', places('USA_MID_AMATEUR', (1,)),
                  amateur_only=True),
            Route('U4', 'Britannia Amateur champion', 'The Amateur Championship winner',
                  places('BRITANNIA_AMATEUR', (1,), 0), amateur_only=True),
        )
    finals = tuple(sid for sid in ('USA_OPEN_FINAL_INTL', 'USA_OPEN_FINAL'))
    usa = (
        Route('U1', 'USA Open champions, last 10 years', 'US Open champions (10 years)', winners_of(('USA_OPEN',), 10, False),
              source=(('wins', ('USA_OPEN',), 10),)),
        *usa_amateurs,
        Route('U5', 'Major champions, last 5 years', 'Masters, Open and PGA champions (5 years)',
              winners_of(OTHER_MAJORS['USA_OPEN'], 5), source=(('wins', OTHER_MAJORS['USA_OPEN'], 5),)),
        Route('U6', 'Premier Players Championship winners, last 3 years', 'Players Championship winners (3 years)',
              winners_of(('PT_PREMIER_PLAYERS_CHAMPIONSHIP',), 3), source=(('wins', ('PT_PREMIER_PLAYERS_CHAMPIONSHIP',), 3),)),
        Route('U7', 'Top 10 and ties, last USA Open', 'Top 10 and ties, previous US Open', top_finishers('USA_OPEN', 10),
              source=(('USA_OPEN', -1),)),
        Route('U8', 'Last season\'s Premier Tour Finals qualifiers', 'Tour Championship qualifiers (previous season)',
              standing_top('PT_AMERICAS', 30), source=(('standing', 'PT_AMERICAS', -1),)),
        Route('U9', 'World top 60, first cut-off', 'OWGR top 60, mid-May ranking', top(60, c['usa_ranking_1']), cutoff=True,
              source=(('ranking', c['usa_ranking_1'], 0),)),
        Route('U10', 'World top 60, final cut-off', 'OWGR top 60, ranking the week before', top(60, c['usa_ranking_2']),
              cutoff=True, source=(('ranking', c['usa_ranking_2'], 0),)),
        Route('UQ', 'Final Qualifying', 'US Open Final Qualifying (36 holes, one day)',
              stage_sites(finals), kind='qualifying', site_spots=(6, 4, 8, 7, 6, 6, 8, 6, 7, 5),
              alternates=True, source=tuple((sid, 0) for sid in finals)),
        Route('UF', 'Alternates', 'Alternates from final qualifying, then the world ranking', fill(c['usa_fill']), kind='fill'),
    )
    if v2:
        award = (Route('B13', 'Annual amateur award (last season)', 'Mark McCormack Medal (previous year)',
                       amateur_award(), amateur_only=True, source=(('award', c['amateur_award'], -1),)),)
    else:
        award = (Route('B13', 'Leading amateur in the world amateur ranking', 'Mark McCormack Medal',
                       ranking_top(1, 26, amateur=True), amateur_only=True, cutoff=True),)
    britannia = (
        Route('B1', 'Past Britannia Open champions aged 60 or under', 'Open champions aged 60 or under',
              lifetime_winners('BRITANNIA_OPEN'), max_age=60, source=(('wins', ('BRITANNIA_OPEN',), 0),)),
        Route('B2', 'Top 10 and ties, last Britannia Open', 'Top 10 and ties, previous Open', top_finishers('BRITANNIA_OPEN', 10),
              source=(('BRITANNIA_OPEN', -1),)),
        Route('B3', 'Major champions, last 5 years', 'Masters, US Open and PGA champions (5 years)',
              winners_of(OTHER_MAJORS['BRITANNIA_OPEN'], 5), source=(('wins', OTHER_MAJORS['BRITANNIA_OPEN'], 5),)),
        Route('B4', 'Premier Players Championship winners, last 3 years', 'Players Championship winners (3 years)',
              winners_of(('PT_PREMIER_PLAYERS_CHAMPIONSHIP',), 3), source=(('wins', ('PT_PREMIER_PLAYERS_CHAMPIONSHIP',), 3),)),
        Route('B5', 'World top 50', 'OWGR top 50 (late-May ranking)', top(50, c['britannia_ranking']), cutoff=True,
              source=(('ranking', c['britannia_ranking'], 0),)),
        Route('B6', 'Last season\'s Premier Tour Finals qualifiers', 'Tour Championship qualifiers (previous season)',
              standing_top('PT_AMERICAS', 30), source=(('standing', 'PT_AMERICAS', -1),)),
        Route('B7', 'Top 30, last season\'s Premier Tour Europe standings', 'Top 30, Race to Dubai (previous season)',
              standing_top('PT_EUROPE', 30), source=(('standing', 'PT_EUROPE', -1),)),
        Route('B8', 'Order of Merit winners: Japan, Asia, Australasia, Southern Africa', 'Order of Merit winners (Japan, Asian, Australasian, Sunshine tours)',
              standing_leaders(('CH_JAPAN', 'CH_ASIA', 'RG_AUSTRALASIA', 'RG_SOUTHERN_AFRICA')),
              source=tuple(('standing', t, -1) for t in ('CH_JAPAN', 'CH_ASIA', 'RG_AUSTRALASIA', 'RG_SOUTHERN_AFRICA'))),
        Route('B9', 'Britannia Amateur champion', 'The Amateur Championship winner',
              places('BRITANNIA_AMATEUR', (1,), 0), amateur_only=True, source=(('BRITANNIA_AMATEUR', 0),)),
        Route('B10', 'USA Amateur champion', 'U.S. Amateur champion', places('USA_AMATEUR', (1,)), amateur_only=True,
              source=(('USA_AMATEUR', -1),)),
        Route('B11', 'European Amateur champion', 'European Amateur champion',
              places('EUROPEAN_AMATEUR', (1,), 0), amateur_only=True, source=(('EUROPEAN_AMATEUR', 0),)),
        Route('B12', 'Asia-Pacific, Latin America and Africa Amateur champions', 'Asia-Pacific, Latin America and Africa Amateur champions',
              lambda ctx, year: places('ASIA_PACIFIC_AMATEUR', (1,))(ctx, year) +
              places('LATIN_AMERICA_AMATEUR', (1,), 0)(ctx, year) + places('AFRICA_AMATEUR', (1,), 0)(ctx, year),
              amateur_only=True, source=(('ASIA_PACIFIC_AMATEUR', -1), ('LATIN_AMERICA_AMATEUR', 0), ('AFRICA_AMATEUR', 0))),
        *award,
        # Britannia Qualifying Series: leading finishers not already exempt.
        *[Route(f'BQ_{sid}', f'Britannia Qualifying Series: {label}', f'Open Qualifying Series: {real}',
                qualifier_finishers((sid,), off), kind='qualifying', spots=n, source=((sid, off),))
          for sid, label, real, off, n in BRITANNIA_SERIES],
        Route('BQ', 'Final Qualifying', 'Open Final Qualifying (36 holes, four venues)',
              stage_sites(('BRITANNIA_FINAL',)), kind='qualifying', site_spots=(4, 4, 4, 4), alternates=True,
              source=(('BRITANNIA_FINAL', 0),)),
        Route('BF', 'Reserves from the world ranking', 'Reserve list (OWGR)', fill(c['britannia_fill']), kind='fill'),
    )
    return {'TOUR_MASTERS': masters, 'PREMIER_TOUR_CHAMPIONSHIP': pga, 'USA_OPEN': usa, 'BRITANNIA_OPEN': britannia}


# The designated Britannia Qualifying Series: ten game allocations (source edition: last season's or this one's)
BRITANNIA_SERIES = (
    ('PT_AUSTRALIA_OPEN', 'Australia Open (December)', 'Australian Open', -1, 3),
    ('PT_SOUTH_AFRICA_OPEN', 'South Africa Open (December)', 'South African Open', -1, 3),
    ('NATIONAL_OPEN_JAPAN', 'Japan Open (October)', 'Japan Open / Mizuno Open', -1, 2),
    ('NATIONAL_OPEN_NEW_ZEALAND', 'New Zealand Open', 'New Zealand Open', 0, 1),
    ('PT_KENYA_OPEN', 'Kenya Open', 'African national-open route', 0, 1),
    ('PT_HEARTLAND_INVITATIONAL', 'Heartland Invitational', 'Memorial Tournament', 0, 3),
    ('PT_CANADA_OPEN', 'Canada Open', 'RBC Canadian Open', 0, 3),
    ('NATIONAL_OPEN_SOUTH_KOREA', 'Korea Open', 'Kolon Korea Open', 0, 2),
    ('PT_GREAT_LAKES_OPEN', 'Great Lakes Open', 'John Deere Classic', 0, 1),
    ('PT_SCOTLAND_OPEN', 'Scotland Open', 'Genesis Scottish Open', 0, 3))

RULES_BY_VERSION = {v: _rules(sp) for v, sp in SCH.SPECS.items()}
RULES = RULES_BY_VERSION[SCH.LEGACY]                 # (the classic rules: worlds saved before calendar versions)


def rules_for(version=None):
    return RULES_BY_VERSION[version or SCH.LEGACY]

# Every calendar series the rules refer to (checked against the calendar by the tests).
def referenced_series(version=None):
    sp = SCH.spec(version)
    return tuple(dict.fromkeys(
        ('TOUR_MASTERS', 'PREMIER_TOUR_CHAMPIONSHIP', 'USA_OPEN', 'BRITANNIA_OPEN', 'PT_PREMIER_PLAYERS_CHAMPIONSHIP',
         'USA_AMATEUR', 'BRITANNIA_AMATEUR', 'ASIA_PACIFIC_AMATEUR', 'LATIN_AMERICA_AMATEUR', 'USA_MID_AMATEUR',
         'EUROPEAN_AMATEUR', 'AFRICA_AMATEUR', 'CLUB_PRO_CHAMPIONSHIP', 'USA_OPEN_FINAL_INTL', 'USA_OPEN_FINAL',
         *(x[0] for x in sp.usa_local), 'BRITANNIA_FINAL', *(x[0] for x in sp.britannia_regional),
         *(x[0] for x in BRITANNIA_SERIES))
        + (('COLLEGE_NATIONAL_CHAMPIONSHIP',) if sp.snapshots else ())))


REFERENCED_SERIES = (
    'TOUR_MASTERS', 'PREMIER_TOUR_CHAMPIONSHIP', 'USA_OPEN', 'BRITANNIA_OPEN', 'PT_PREMIER_PLAYERS_CHAMPIONSHIP',
    'USA_AMATEUR', 'BRITANNIA_AMATEUR', 'ASIA_PACIFIC_AMATEUR', 'LATIN_AMERICA_AMATEUR', 'USA_MID_AMATEUR',
    'EUROPEAN_AMATEUR', 'AFRICA_AMATEUR', 'CLUB_PRO_CHAMPIONSHIP', 'USA_OPEN_FINAL_INTL', 'USA_OPEN_FINAL',
    'USA_OPEN_LOCAL_W19', 'USA_OPEN_LOCAL_W20', 'USA_OPEN_LOCAL_W21', 'BRITANNIA_FINAL', 'BRITANNIA_REGIONAL_W26',
    'BRITANNIA_REGIONAL_W27', 'PT_AUSTRALIA_OPEN', 'PT_SOUTH_AFRICA_OPEN', 'NATIONAL_OPEN_JAPAN',
    'NATIONAL_OPEN_NEW_ZEALAND', 'PT_KENYA_OPEN', 'PT_HEARTLAND_INVITATIONAL', 'PT_CANADA_OPEN',
    'NATIONAL_OPEN_SOUTH_KOREA', 'PT_GREAT_LAKES_OPEN', 'PT_SCOTLAND_OPEN',
)

# Earlier stages that feed the final qualifying events.
def stages(version=None):
    """{final stage: feeders, places per site, who skips the earlier stage} for a calendar version."""
    sp = SCH.spec(version)
    if sp.version == SCH.LEGACY:
        return STAGES
    return {'USA_OPEN_FINAL': dict(STAGES['USA_OPEN_FINAL'], feeders=tuple(x[0] for x in sp.usa_local)),
            'BRITANNIA_FINAL': dict(STAGES['BRITANNIA_FINAL'], feeders=tuple(x[0] for x in sp.britannia_regional))}


STAGES = {
    'USA_OPEN_FINAL': dict(feeders=('USA_OPEN_LOCAL_W19', 'USA_OPEN_LOCAL_W20', 'USA_OPEN_LOCAL_W21'),
                           per_site=5, exempt_from_earlier='World top 250, Premier Tour members, recent USA Amateur finalists'),
    'BRITANNIA_FINAL': dict(feeders=('BRITANNIA_REGIONAL_W26', 'BRITANNIA_REGIONAL_W27'), per_site=6,
                            exempt_from_earlier='World top 300, Premier and Challenger Tour members'),
}


@dataclass
class Entry:
    golfer_id: int
    primary: str                   # route code that got them in
    sources: list                  # every exempt category they also satisfy


@dataclass
class Field:
    major: str
    year: int
    entries: list
    alternates: list
    route_counts: dict

    def ids(self):
        return [e.golfer_id for e in self.entries]


def secured_places(ctx, year):
    """Places in next season's majors already earned by the end of `year`: every exemption route
    applied (with the same rules as build_field) to the facts known then, leaving out routes decided by
    rankings or points lists not yet published (cutoff) and qualifying stages still to be played.
    {gid: [(major, routes, condition)]}, one entry per major with every route that supports the place
    (routes: [(code, label, condition)], in the rules' order). The place is guaranteed (condition '')
    if any route is unconditional, however many amateur routes also lead there; it is conditional
    ('if still an amateur': it lapses if they turn professional) only if every route is an amateur's."""
    view = ctx.as_of(year + 1, 1)                     # everything of `year`, nothing of the next
    found = {}
    for major, rules in rules_for(ctx.version).items():
        for route in rules:
            if route.kind != 'exempt' or route.cutoff:
                continue
            for gid in route.select(view, year + 1):
                p = ctx.people.get(gid)
                if p is None or not p.active:
                    continue
                if route.amateur_only and p.status != 'amateur':
                    continue
                if (route.status and p.status != route.status) or (route.max_age and p.age + 1 > route.max_age):
                    continue
                routes = found.setdefault((gid, major), [])
                if all(code != route.code for code, _, _ in routes):
                    routes.append((route.code, route.label, 'if still an amateur' if route.amateur_only else ''))
    out = {}
    for (gid, major), routes in found.items():
        cond = '' if any(not c for _, _, c in routes) else 'if still an amateur'
        out.setdefault(gid, []).append((major, routes, cond))
    return out


def _eligible(ctx, gid, route, year):
    p = ctx.people.get(gid)
    if p is None or not p.active:
        return False
    if route.amateur_only and p.status != 'amateur':
        return False
    if route.status and p.status != route.status:
        return False
    if route.max_age and p.age > route.max_age:
        return False
    return True


def build_field(major, year, ctx):
    """Apply the major's routes in order and return the field with each entrant's sources."""
    rules = rules_for(ctx.version)
    if major not in rules:
        raise KeyError(major)
    ctx = ctx.as_of(year, ctx.major_week(major))
    entries, in_field = [], {}
    counts = defaultdict(int)
    alternates = []
    rules = rules[major]
    # Every exempt category is applied before any qualifying places are handed out, whatever order the
    # routes are listed in: a player who is exempt anyway (e.g. a club professional inside the world
    # top 100) never uses up a qualifying place; it passes to the next finisher.
    for route in [r for r in rules if r.kind == 'exempt'] + [r for r in rules if r.kind != 'exempt']:
        if route.kind == 'exempt':
            for gid in route.select(ctx, year):
                if not _eligible(ctx, gid, route, year):
                    continue
                if gid in in_field:
                    in_field[gid].sources.append(route.code)
                    continue
                e = Entry(gid, route.code, [route.code])
                in_field[gid] = e
                entries.append(e)
                counts[route.code] += 1
        elif route.kind == 'qualifying':
            groups = route.select(ctx, year)
            if groups and isinstance(groups[0], int):
                groups = [groups]
            per = route.site_spots or (route.spots,) * len(groups)
            for i, group in enumerate(groups):
                spots = per[i] if i < len(per) else per[-1]
                taken = 0
                for gid in group:
                    if taken >= spots:
                        if route.alternates and gid not in in_field and _eligible(ctx, gid, route, year):
                            alternates.append(gid)
                        continue
                    if gid in in_field or not _eligible(ctx, gid, route, year):
                        continue                      # exempt players do not use a qualifying spot
                    e = Entry(gid, route.code, [route.code])
                    in_field[gid] = e
                    entries.append(e)
                    counts[route.code] += 1
                    taken += 1
        else:  # fill
            target = FIELD_SIZE[major]
            if not target:
                continue
            pool = [g for g in alternates if g not in in_field] + [g for g in route.select(ctx, year) if g not in in_field]
            for gid in pool:
                if gid in in_field or not _eligible(ctx, gid, route, year):
                    continue
                if len(entries) >= target:
                    alternates.append(gid)            # the rest of the list stays on as ordered reserves
                    continue
                e = Entry(gid, route.code, [route.code])
                in_field[gid] = e
                entries.append(e)
                counts[route.code] += 1
    size = FIELD_SIZE[major]
    if size and len(entries) > size:
        # Too many exempt players: the last-added qualifying/fill entries become alternates.
        keep = entries[:size]
        alternates = [e.golfer_id for e in entries[size:]] + alternates
        for e in entries[size:]:
            counts[e.primary] -= 1
        entries = keep
    # Alternates who were promoted into the field are no longer alternates; keep the order, no repeats.
    entered = {e.golfer_id for e in entries}
    alternates = list(dict.fromkeys(g for g in alternates if g not in entered))
    return Field(major, year, entries, alternates, {k: v for k, v in counts.items() if v})


def wins_index(ctx):
    """{gid: [(series_id, year)]} of every recorded win (one pass over the results, for evidence())."""
    out = defaultdict(list)
    for (sid, y) in ctx.results:
        w = ctx.winner(sid, y)
        if w is not None:
            out[w].append((sid, y))
    return out


def evidence(route, gid, year, ctx, wins=None):
    """[(source, (year, week) awarded)] behind a golfer's place by `route` in the `year` edition: the edition(s)
    and result, ranking or points list, or award the route read (empty where the route names none). wins: a
    wins_index(ctx), when many golfers are looked up at once."""
    out = []
    for src in route.source:
        if src[0] == 'wins':                                 # a win: the latest one the route counts
            series, back = src[1], src[2]
            found = None
            mine = wins.get(gid, ()) if wins is not None else [k for k in ctx.results if ctx.winner(*k) == gid]
            for (sid, y) in mine:
                if (series is None and not ctx.tour_of.get(sid, '').startswith('PT_')) or \
                        (series is not None and sid not in series) or (back and y < year - back):
                    continue
                if found is None or (y, ctx.edition_week(sid, y) or 0) > found[1]:
                    found = (f'{y}:{sid} (won)', (y, ctx.edition_week(sid, y) or 0))
            if found:
                out.append(found)
        elif src[0] == 'standing':
            out.append((f'{src[1]} final standings {year + src[2]}', (year + src[2], 52)))
        elif src[0] in ('ranking', 'points', 'award'):
            what = {'ranking': 'world ranking', 'points': 'Premier Tour Americas points', 'award': 'annual amateur award'}
            out.append((f'{what[src[0]]} after week {src[1]} of {year + src[2]}', (year + src[2], src[1])))
        else:                                                # an edition: where the golfer finished
            sid, off = src
            y = year + off
            pos = next((p for g, p in ctx.finishers(sid, y) if g == gid), None)
            if pos is not None or any(g == gid for g, _ in ctx.finishers(sid, y)):
                out.append((f'{y}:{sid} ({"position " + str(pos) if pos else "missed cut"})',
                            (y, ctx.edition_week(sid, y) or 0)))
    return out


def _complete(route, ctx, year):
    """Whether every edition a qualifying route draws its places from has been played (in this view)."""
    eds = [src for src in route.source if src[0] not in ('wins', 'standing', 'ranking', 'points', 'award')]
    return bool(eds) and all((sid, year + off) in ctx.results for sid, off in eds)


def earned_exemptions(major, year, ctx):
    """({gid: [route codes]}, [pending route codes]): who already holds a place in `major` on the facts `ctx`
    holds (a view as of a qualifying stage) -- every exemption category whose facts are known, and every place a
    qualifying event already played has awarded (a qualifying-series event: its leading finishers not exempt
    otherwise, allocated exactly as the field will be: exemptions first, then the qualifying routes in the
    rules' order, a place passing down when its finisher is already in). A route decided by a cut-off not yet
    published is pending -- nobody holds it yet: a projected ranking never stands in for it, so it never takes
    away anyone's qualifying attempt. Places from qualifying events still to come are not counted either."""
    out, pending = {}, []
    rules = rules_for(ctx.version)[major]
    for route in rules:
        if route.kind != 'exempt':
            continue
        try:
            ids = route.select(ctx, year)
        except FutureSnapshot:
            pending.append(route.code)
            continue
        for gid in ids:
            if _eligible(ctx, gid, route, year):
                out.setdefault(gid, []).append(route.code)
    in_field = set(out)
    for route in rules:                                  # places already awarded by qualifying events played
        if route.kind != 'qualifying' or not route.source or not _complete(route, ctx, year):
            continue
        try:
            groups = route.select(ctx, year)
        except FutureSnapshot:
            pending.append(route.code)
            continue
        if groups and isinstance(groups[0], int):
            groups = [groups]
        per = route.site_spots or (route.spots,) * len(groups)
        for i, group in enumerate(groups):
            spots = per[i] if i < len(per) else per[-1]
            taken = 0
            for gid in group:
                if taken >= spots:
                    break
                if gid in in_field or not _eligible(ctx, gid, route, year):
                    continue                             # (as in build_field: the place passes down)
                out.setdefault(gid, []).append(route.code)
                in_field.add(gid)
                taken += 1
    return out, pending


def stage_entrants(stage_series, year, ctx, pool_ids):
    """Who may enter a qualifying stage: the open pool minus anyone already exempt into the major."""
    major = 'USA_OPEN' if stage_series.startswith('USA_OPEN') else 'BRITANNIA_OPEN'
    exempt = {e.golfer_id for e in build_field(major, year, ctx).entries if not e.primary.startswith(('UQ', 'BQ', 'UF', 'BF'))}
    return [g for g in pool_ids if g not in exempt and ctx.available(g)]


def describe(version=None):
    """Plain-language list of every route, for reports."""
    out = {}
    for major, routes in rules_for(version).items():
        out[major] = [(r.code, r.label, r.analogue, r.kind) for r in routes]
    return out
