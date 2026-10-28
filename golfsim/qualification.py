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

MAJOR_SERIES = ('TOUR_MASTERS', 'PREMIER_TOUR_CHAMPIONSHIP', 'USA_OPEN', 'BRITANNIA_OPEN')
MAJOR_WEEK = {'TOUR_MASTERS': 18, 'PREMIER_TOUR_CHAMPIONSHIP': 24, 'USA_OPEN': 25, 'BRITANNIA_OPEN': 30}
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

    # -- recording ---------------------------------------------------------------------------
    def add_result(self, series_id, year, finishers, site=0):
        """finishers: [(id, position)] in finishing order; position None = missed cut."""
        self.results.setdefault((series_id, year), {})[site] = list(finishers)

    @classmethod
    def from_calendar(cls, calendar, **kw):
        ctx = cls(**kw)
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
        view = QualificationContext(self.people, {}, self.event_weeks, {}, {}, {}, self.tour_of, self.category_of)
        view.results = {k: v for k, v in self.results.items() if known(k[1], self.event_weeks.get(k[0], 0))}
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


def _is_premier_full_points(sid, ctx):
    return ctx.tour_of.get(sid) == 'PT_AMERICAS' and ctx.category_of.get(sid) != 'opportunity' or \
        (ctx.tour_of.get(sid, '').startswith('PT_') and ctx.category_of.get(sid) == 'flagship')


def _is_premier(sid, ctx):
    return ctx.tour_of.get(sid, '').startswith('PT_')


# ---------------------------------------------------------------------------------------------
# The four majors
# ---------------------------------------------------------------------------------------------
MAJOR_WINNER_SETS = {m: OTHER_MAJORS[m] for m in MAJOR_SERIES}

RULES = {
    'TOUR_MASTERS': (
        Route('M1', 'Past Tour Masters champions', 'Masters champions (lifetime)', lifetime_winners('TOUR_MASTERS')),
        Route('M2', 'Major champions, last 5 years', 'US Open, Open and PGA champions (5 years)',
              winners_of(OTHER_MAJORS['TOUR_MASTERS'], 5)),
        Route('M3', 'Premier Players Championship winners, last 3 years', 'Players Championship winners (3 years)',
              winners_of(('PT_PREMIER_PLAYERS_CHAMPIONSHIP',), 3)),
        Route('M4', 'USA Amateur champion and runner-up', 'U.S. Amateur champion and runner-up',
              places('USA_AMATEUR', (1, 2)), amateur_only=True),
        Route('M5', 'Britannia Amateur champion', 'The Amateur Championship winner',
              places('BRITANNIA_AMATEUR', (1,)), amateur_only=True),
        Route('M6', 'Asia-Pacific Amateur champion', 'Asia-Pacific Amateur champion',
              places('ASIA_PACIFIC_AMATEUR', (1,)), amateur_only=True),
        Route('M7', 'Latin America Amateur champion', 'Latin America Amateur champion',
              places('LATIN_AMERICA_AMATEUR', (1,), year_offset=0), amateur_only=True),
        Route('M8', 'USA Mid-Amateur champion', 'U.S. Mid-Amateur champion',
              places('USA_MID_AMATEUR', (1,)), amateur_only=True),
        Route('M9', 'Top 12 and ties, last Tour Masters', 'Top 12 and ties, previous Masters',
              top_finishers('TOUR_MASTERS', 12)),
        Route('M10', 'Top 4 and ties, last year\'s other majors', 'Top 4 and ties, previous US Open / Open / PGA',
              top_finishers_of(OTHER_MAJORS['TOUR_MASTERS'], 4)),
        Route('M11', 'Premier Tour winners since the last Tour Masters', 'PGA Tour winners (full-points events) since previous Masters',
              tour_winners_between(_is_premier_full_points, (-1, 19), (0, 17))),
        Route('M12', 'Last season\'s Premier Tour Finals qualifiers', 'Tour Championship qualifiers (previous season)',
              standing_top('PT_AMERICAS', 30)),
        Route('M13', 'World top 50 at the end of last year', 'OWGR top 50, final ranking of previous year',
              ranking_top(50, 52, -1)),
        Route('M14', 'World top 50 two weeks before', 'OWGR top 50, ranking published before the Masters',
              ranking_top(50, 16), cutoff=True),
        Route('M15', 'International invitations', 'Special invitations to international players',
              lambda ctx, year: [g for g in ctx.ranking(year, 16)[50:100]
                                 if ctx.people[g].country not in ('USA',)], kind='qualifying', spots=4),
    ),
    'PREMIER_TOUR_CHAMPIONSHIP': (
        Route('P1', 'Past Premier Tour Championship champions', 'PGA champions (lifetime)',
              lifetime_winners('PREMIER_TOUR_CHAMPIONSHIP')),
        Route('P2', 'Major champions, last 5 years', 'Masters, US Open and Open champions (5 years)',
              winners_of(OTHER_MAJORS['PREMIER_TOUR_CHAMPIONSHIP'], 5)),
        Route('P3', 'Premier Players Championship winners, last 3 years', 'Players Championship winners (3 years)',
              winners_of(('PT_PREMIER_PLAYERS_CHAMPIONSHIP',), 3)),
        Route('P4', 'Top 15 and ties, last Premier Tour Championship', 'Top 15 and ties, previous PGA',
              top_finishers('PREMIER_TOUR_CHAMPIONSHIP', 15)),
        Route('P5', 'Top 20, Club Professional Championship', 'Top 20, PGA Professional Championship (ties for the '
              'last places settled by playoff)', qualifier_finishers(('CLUB_PRO_CHAMPIONSHIP',)), kind='qualifying',
              status='club_pro', spots=20),
        Route('P6', 'Top 70, Premier Tour Americas points list', 'Top 70, PGA Tour points list',
              points_list('PT_AMERICAS', 22, 0, 70), cutoff=True),
        Route('P7', 'Premier Tour winners since the last Premier Tour Championship', 'PGA Tour winners since previous PGA',
              tour_winners_between(_is_premier, (-1, 25), (0, 23))),
        Route('P8', 'Invitations: world top 100', 'PGA of America invitations (effectively the OWGR top 100)',
              ranking_top(100, 22), cutoff=True),
        Route('PF', 'Alternates from the points list', 'Field filled from the PGA Tour points list',
              points_list('PT_AMERICAS', 22, 70), kind='fill'),
    ),
    'USA_OPEN': (
        Route('U1', 'USA Open champions, last 10 years', 'US Open champions (10 years)', winners_of(('USA_OPEN',), 10, False)),
        Route('U2', 'USA Amateur champion and runner-up', 'U.S. Amateur champion and runner-up',
              places('USA_AMATEUR', (1, 2)), amateur_only=True),
        Route('U3', 'USA Mid-Amateur champion', 'U.S. Mid-Amateur champion', places('USA_MID_AMATEUR', (1,)), amateur_only=True),
        Route('U4', 'Britannia Amateur champion', 'The Amateur Championship winner',
              places('BRITANNIA_AMATEUR', (1,), 0), amateur_only=True),
        Route('U5', 'Major champions, last 5 years', 'Masters, Open and PGA champions (5 years)',
              winners_of(OTHER_MAJORS['USA_OPEN'], 5)),
        Route('U6', 'Premier Players Championship winners, last 3 years', 'Players Championship winners (3 years)',
              winners_of(('PT_PREMIER_PLAYERS_CHAMPIONSHIP',), 3)),
        Route('U7', 'Top 10 and ties, last USA Open', 'Top 10 and ties, previous US Open', top_finishers('USA_OPEN', 10)),
        Route('U8', 'Last season\'s Premier Tour Finals qualifiers', 'Tour Championship qualifiers (previous season)',
              standing_top('PT_AMERICAS', 30)),
        Route('U9', 'World top 60, first cut-off', 'OWGR top 60, mid-May ranking', ranking_top(60, 21), cutoff=True),
        Route('U10', 'World top 60, final cut-off', 'OWGR top 60, ranking the week before', ranking_top(60, 23), cutoff=True),
        Route('UQ', 'Final Qualifying', 'US Open Final Qualifying (36 holes, one day)',
              stage_sites(('USA_OPEN_FINAL_INTL', 'USA_OPEN_FINAL')), kind='qualifying', site_spots=(6, 4, 8, 7, 6, 6, 8, 6, 7, 5),
              alternates=True),
        Route('UF', 'Alternates', 'Alternates from final qualifying, then the world ranking', ranking_fill(23), kind='fill'),
    ),
    'BRITANNIA_OPEN': (
        Route('B1', 'Past Britannia Open champions aged 60 or under', 'Open champions aged 60 or under',
              lifetime_winners('BRITANNIA_OPEN'), max_age=60),
        Route('B2', 'Top 10 and ties, last Britannia Open', 'Top 10 and ties, previous Open', top_finishers('BRITANNIA_OPEN', 10)),
        Route('B3', 'Major champions, last 5 years', 'Masters, US Open and PGA champions (5 years)',
              winners_of(OTHER_MAJORS['BRITANNIA_OPEN'], 5)),
        Route('B4', 'Premier Players Championship winners, last 3 years', 'Players Championship winners (3 years)',
              winners_of(('PT_PREMIER_PLAYERS_CHAMPIONSHIP',), 3)),
        Route('B5', 'World top 50', 'OWGR top 50 (late-May ranking)', ranking_top(50, 21), cutoff=True),
        Route('B6', 'Last season\'s Premier Tour Finals qualifiers', 'Tour Championship qualifiers (previous season)',
              standing_top('PT_AMERICAS', 30)),
        Route('B7', 'Top 30, last season\'s Premier Tour Europe standings', 'Top 30, Race to Dubai (previous season)',
              standing_top('PT_EUROPE', 30)),
        Route('B8', 'Order of Merit winners: Japan, Asia, Australasia, Southern Africa', 'Order of Merit winners (Japan, Asian, Australasian, Sunshine tours)',
              standing_leaders(('CH_JAPAN', 'CH_ASIA', 'RG_AUSTRALASIA', 'RG_SOUTHERN_AFRICA'))),
        Route('B9', 'Britannia Amateur champion', 'The Amateur Championship winner',
              places('BRITANNIA_AMATEUR', (1,), 0), amateur_only=True),
        Route('B10', 'USA Amateur champion', 'U.S. Amateur champion', places('USA_AMATEUR', (1,)), amateur_only=True),
        Route('B11', 'European Amateur champion', 'European Amateur champion',
              places('EUROPEAN_AMATEUR', (1,), 0), amateur_only=True),
        Route('B12', 'Asia-Pacific, Latin America and Africa Amateur champions', 'Asia-Pacific, Latin America and Africa Amateur champions',
              lambda ctx, year: places('ASIA_PACIFIC_AMATEUR', (1,))(ctx, year) +
              places('LATIN_AMERICA_AMATEUR', (1,), 0)(ctx, year) + places('AFRICA_AMATEUR', (1,), 0)(ctx, year),
              amateur_only=True),
        Route('B13', 'Leading amateur in the world amateur ranking', 'Mark McCormack Medal',
              ranking_top(1, 26, amateur=True), amateur_only=True, cutoff=True),
        # Britannia Qualifying Series: leading finishers not already exempt.
        *[Route(f'BQ_{sid}', f'Britannia Qualifying Series: {label}', f'Open Qualifying Series: {real}',
                qualifier_finishers((sid,), off), kind='qualifying', spots=n)
          for sid, label, real, off, n in (
              ('PT_AUSTRALIA_OPEN', 'Australia Open (December)', 'Australian Open', -1, 3),
              ('PT_SOUTH_AFRICA_OPEN', 'South Africa Open (December)', 'South African Open', -1, 3),
              ('NATIONAL_OPEN_JAPAN', 'Japan Open (October)', 'Japan Open / Mizuno Open', -1, 2),
              ('NATIONAL_OPEN_NEW_ZEALAND', 'New Zealand Open', 'New Zealand Open', 0, 1),
              ('PT_KENYA_OPEN', 'Kenya Open', 'African national-open route', 0, 1),
              ('PT_HEARTLAND_INVITATIONAL', 'Heartland Invitational', 'Memorial Tournament', 0, 3),
              ('PT_CANADA_OPEN', 'Canada Open', 'RBC Canadian Open', 0, 3),
              ('NATIONAL_OPEN_SOUTH_KOREA', 'Korea Open', 'Kolon Korea Open', 0, 2),
              ('PT_GREAT_LAKES_OPEN', 'Great Lakes Open', 'John Deere Classic', 0, 1),
              ('PT_SCOTLAND_OPEN', 'Scotland Open', 'Genesis Scottish Open', 0, 3))],
        Route('BQ', 'Final Qualifying', 'Open Final Qualifying (36 holes, four venues)',
              stage_sites(('BRITANNIA_FINAL',)), kind='qualifying', site_spots=(4, 4, 4, 4), alternates=True),
        Route('BF', 'Reserves from the world ranking', 'Reserve list (OWGR)', ranking_fill(26), kind='fill'),
    ),
}

# Every calendar series the rules refer to (checked against the calendar by the tests).
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
    for major, rules in RULES.items():
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
    if major not in RULES:
        raise KeyError(major)
    ctx = ctx.as_of(year, MAJOR_WEEK[major])
    entries, in_field = [], {}
    counts = defaultdict(int)
    alternates = []
    rules = RULES[major]
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


def stage_entrants(stage_series, year, ctx, pool_ids):
    """Who may enter a qualifying stage: the open pool minus anyone already exempt into the major."""
    major = 'USA_OPEN' if stage_series.startswith('USA_OPEN') else 'BRITANNIA_OPEN'
    exempt = {e.golfer_id for e in build_field(major, year, ctx).entries if not e.primary.startswith(('UQ', 'BQ', 'UF', 'BF'))}
    return [g for g in pool_ids if g not in exempt and ctx.available(g)]


def describe():
    """Plain-language list of every route, for reports."""
    out = {}
    for major, routes in RULES.items():
        out[major] = [(r.code, r.label, r.analogue, r.kind) for r in routes]
    return out
