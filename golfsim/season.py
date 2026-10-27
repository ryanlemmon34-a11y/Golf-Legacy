"""The season engine: every event in the world, every week, every shot.

Each week:
  1. Special fields are set first: the major (by its qualification rules), the Premier Tour Finals
     (top 30 on the points list), college post-season, elite and national amateur championships, the
     Club Professional Championship and the Q-School stages.
  2. Everyone else chooses where to play. Each golfer scores every event they may enter:
         event prestige + home country / region - travel - fatigue + catching up on their schedule
     and only enters events worth more than their own bar, which rises with their prestige (a star
     skips an "opportunity" event an average tour player is glad to play). Events take entries in
     priority order (members first, then by world ranking), golfers who miss out try their next
     choice (deferred acceptance), and spare places are filled by willing players from lower levels.
  3. Monday/Tuesday qualifiers (USA Open local and final, Britannia regional and final) run alongside.
  4. All events of the week are played in parallel, every shot simulated.
  5. Results update: world and amateur rankings, money lists, fame and player prestige, event
     prestige, course records per layout, familiarity, and the champions' history.

At the end of the season `cards.py` moves players between tours (promotion, relegation, Q-School).
`development=False` keeps every golfer's attributes fixed (for testing the world's machinery).
"""
from __future__ import annotations

import hashlib
import math
import os
import random
import statistics as S
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field

from . import development as D
from . import finance as FIN
from . import prestige as PR
from . import qualification as Q
from .calendar import MAJOR_WEEKS, TOUR_BY_KEY, _in_window
from .course_library import default_library
from .engine import Conditions
from .geography import CITY_BY_NAME, COUNTRIES
from .population import CHALLENGER_BY_COUNTRY, CHALLENGER_BY_REGION
from .records import Mark, RecordBook
from .tournament import play_event, play_stroke_and_match

PREMIER_TOURS = ('PT_AMERICAS', 'PT_EUROPE', 'PT_ASIA_PACIFIC')
FATIGUE_PER_ROUND = 0.03          # a four-round week adds ~0.12 for an average-stamina golfer
INJURY_BASE = 0.0045              # chance of an injury per four-round event for a fresh, average golfer
INJURIES = ('back', 'wrist', 'shoulder', 'elbow', 'knee', 'hip', 'neck', 'rib', 'hand', 'ankle', 'thumb',
            'oblique')
STAT_KEYS = ('drive_yards', 'drives', 'fairways', 'fairway_att', 'gir', 'putts', 'sg_ott', 'sg_app', 'sg_arg',
             'sg_putt')
AMATEUR_CAP = {1: 4, 2: 8, 3: 8, 4: 8}          # most amateurs (sponsor invitations) in a pro event
COLLEGE_WINDOWS = {k: TOUR_BY_KEY[k].weeks for k in ('CO_US_D1', 'CO_US_SMALL', 'CO_INTL')}
ELITE_AMATEUR_REGIONS = {'LATIN_AMERICA_AMATEUR': ('Latin America',), 'AFRICA_AMATEUR': ('Africa',),
                         'EUROPEAN_AMATEUR': ('Europe',), 'ASIA_PACIFIC_AMATEUR': ('Asia', 'Oceania')}
QS_AMERICAS = ('North America', 'Latin America')
QS_EUROPE = ('Europe', 'Africa', 'Middle East')


def _seed(*parts):
    return int.from_bytes(hashlib.blake2b(':'.join(map(str, parts)).encode(), digest_size=8).digest(), 'big')


def region_of(g):
    return COUNTRIES[g.country].region


# ---------------------------------------------------------------------------------------------
# Worker: plays one event site. Top-level so it can run in another process.
# ---------------------------------------------------------------------------------------------
def play_site(task):
    rng = random.Random(task['seed'])
    course, golfers = task['course'], task['golfers']
    rounds_data, holes_data = [], []
    def on_round(g, rd, st):
        rounds_data.append((g.id, rd, st.score, tuple(st.holes),
                            (sum(st.drives), len(st.drives), st.fairways, st.fairway_att, st.gir, st.putts,
                             st.sg_ott, st.sg_app, st.sg_arg, st.sg_putt)))
    def on_hole(g, idx, strokes, stage=''):
        holes_data.append((g.id, idx, strokes, stage))
    out = {'event_id': task['event_id'], 'site': task['site'], 'rounds': rounds_data, 'holes': holes_data}
    if not golfers:
        out.update(finish=[], playoff=0)
        return out
    if task['match_play']:
        res = play_stroke_and_match(golfers, course, rng, stroke_holes=36, bracket=64, final_holes=36,
                                    on_round=on_round, on_hole=on_hole)
        out.update(finish=[(g.id, pos, None) for g, pos in res], playoff=0)
        return out
    wind = max(0.0, rng.gauss(course.typical_wind, 3.0))
    pins = 0.3 + 0.4 * task['prestige'] / 100
    cond = {r: Conditions(wind_mph=max(0.0, wind + rng.gauss(0, 2.5)), rain=rng.random() < 0.08,
                          pin_difficulty=pins) for r in range(1, task['rounds'] + 1)}
    cut_after = 2 if task['cut_top'] and task['rounds'] > 2 else None
    board, playoff = play_event(golfers, course, rng, cut_top=task['cut_top'] or len(golfers),
                                prestige=task['prestige'] / 100, cond_by_round=cond, rounds_n=task['rounds'],
                                cut_after=cut_after, on_round=on_round, on_hole=on_hole)
    finish, totals = [], [t for _, t, _ in board]
    for i, (g, total, rds) in enumerate(board):
        pos = 1 if i == 0 else 1 + sum(1 for t in totals if t < total)
        if i > 0 and total == totals[0]:
            pos = 2                                              # lost the playoff
        finish.append((g.id, pos, total))
    made = {gid for gid, _, _ in finish}
    finish += [(g.id, None, None) for g in golfers if g.id not in made]
    out.update(finish=finish, playoff=playoff)
    return out


@dataclass
class EventResult:
    event_id: str
    series_id: str
    year: int
    week: int
    sites: list                      # [(course_id, layout, city)]
    finish: list                     # per site: [(gid, pos, total)]
    prestige: float
    field_strength: float = 0.0
    playoff: int = 0

    def winner(self, site=0):
        rows = self.finish[site] if self.finish else []
        return next((g for g, p, _ in rows if p == 1), None)


class Season:
    """The living world: population, calendar, courses and everything that has happened."""

    def __init__(self, world, library=None, seed=2027, first_year=None, development=False, workers=None):
        self.world = world
        self.lib = library or default_library()
        self.cal = self.lib.calendar
        self.seed = seed
        self.development = development
        self.first_year = first_year or world.year
        self.g = world.by_id
        self.workers = workers or os.cpu_count() or 2
        self.ctx = Q.QualificationContext.from_calendar(self.cal)
        self.refresh_people(self.first_year)
        self.records = RecordBook()
        self.results = {}                                    # event_id -> EventResult
        self.champions = defaultdict(list)                   # series_id -> [(year, gid, to_par)]
        self.event_prestige = {}                             # series_id -> prestige now
        self.prestige_history = defaultdict(list)            # series_id -> [(year, prestige, field)]
        self.fame = {}                                       # gid -> fame over the last 52 weeks
        self.fame_log = defaultdict(list)                    # gid -> [(abs_week, fame points)]
        self.legacy = defaultdict(float)
        self.event_factors = {}                              # series_id -> [(tour, field, purse, course)]
        self.fatigue = defaultdict(float)                    # gid -> season fatigue, 0 (fresh) .. 1 (exhausted)
        self.injured = {}                                    # gid -> (abs week fit again, injury, weeks)
        self.injuries = defaultdict(list)                    # year -> [(week, gid, injury, weeks out, event_id)]
        self._week_load = defaultdict(float)
        self._week_event = {}
        self.wr = defaultdict(list)                          # gid -> [(abs_week, points)]
        self.am = defaultdict(list)
        self.wr_pos, self.am_pos = {}, {}
        self.money = defaultdict(lambda: defaultdict(float))  # (tour key, year) -> gid -> $
        self.earnings = defaultdict(lambda: defaultdict(float))  # year -> gid -> $ prize money
        self.played = defaultdict(lambda: defaultdict(list))     # year -> gid -> [weeks]
        self.stage_log = defaultdict(list)
        self.card_log = defaultdict(list)                    # year -> [(gid, from, to, reason)]
        self.holes_played = Counter()                        # year -> holes
        self.stats = defaultdict(Counter)
        self.pstats = defaultdict(lambda: defaultdict(Counter))  # year -> gid -> summed round stats
        self.plans = {}                                      # gid -> {week: (action, training category)}
        self.week_rounds = defaultdict(float)                # gid -> rounds played this week
        self.week_activity = {}                              # gid -> 'play' / 'train' / 'rest' this week
        self.ledgers = defaultdict(dict)                     # year -> gid -> finance.Ledger
        self.history = defaultdict(list)                     # gid -> [(year, week, text)]: career log
        self.career_counts = {}                              # year -> {decision: count}
        self.juniors_added = {}                              # year -> number of new golfers
        self.year = self.first_year
        from .cards import tour_target
        for k, t in TOUR_BY_KEY.items():
            if t.tier in (2, 3):
                tour_target(self, k)                         # remember each tour's starting size
        self._seed_world()

    # ---- people and starting state --------------------------------------------------------------
    def refresh_people(self, year):
        for g in self.world.golfers:
            self.ctx.people[g.id] = Q.Person(g.id, g.name, g.status, g.age(year), g.country,
                                             g.lifestyle != 'retired')

    def abs_week(self, year, week):
        return (year - self.first_year) * 52 + week

    def _seed_world(self):
        """Pre-history: world/amateur ranking points, fame and last season's standings, from reputation."""
        rng = random.Random(_seed(self.seed, 'seed-world'))
        for g in self.world.golfers:
            u = rng.random()
            last_year = PR.seeded_fame(g.overall, u) * (1.0 if g.status == 'pro' else 0.2)
            for k in range(6):
                self.fame_log[g.id].append((-k * 9, last_year / 6))
            for k in range(16):
                aw = -rng.randint(1, 100)
                if g.status == 'pro':
                    self.wr[g.id].append((aw, 0.08 * math.exp((g.overall - 60) / 6) * (0.5 + u)))
                elif g.status == 'amateur':
                    self.am[g.id].append((aw, 0.3 * math.exp((g.overall - 40) / 9) * (0.5 + u)))
        self.update_rankings(self.first_year - 1, 52)
        for t in TOUR_BY_KEY:
            members = [g for g in self.world.golfers if g.tour == t]
            members.sort(key=lambda g: self.wr_pos.get(g.id, 10 ** 6))
            self.ctx.standings[(t, self.first_year - 1)] = [g.id for g in members]
        prem = [g for g in self.world.golfers if g.tour in PREMIER_TOURS]
        prem.sort(key=lambda g: self.wr_pos.get(g.id, 10 ** 6))
        self.ctx.standings[('PREMIER', self.first_year - 1)] = [g.id for g in prem]
        self.update_fame(self.first_year - 1, 52)
        for ed in self.cal.editions(self.first_year):
            f0 = PR.initial_factors(ed.series, self.course_quality(ed, 0))
            self.event_factors[ed.series.series_id] = [f0] * PR.WINDOW   # no history yet: expected values
            self.event_prestige[ed.series.series_id] = PR.prestige_from(self.event_factors[ed.series.series_id])
        tours = defaultdict(list)
        for s in self.cal.series:
            if s.category == 'regular' or s.tier == 1:
                tours[s.tour].append(self.event_prestige[s.series_id])
        self.home_level = {t: S.median(v) for t, v in tours.items()}

    def course_quality(self, ed, site):
        v = self.lib.venues(ed.year)[ed.event_id][site]
        return PR.COURSE_QUALITY[(self.lib.sites[v.course_id]['cls'], v.layout)]

    # ---- rankings -------------------------------------------------------------------------------
    def update_rankings(self, year, week):
        now = self.abs_week(year, week)
        def table(entries, lo, hi):
            out = {}
            for gid, rows in entries.items():
                tot, n = 0.0, 0
                keep = []
                for aw, pts in rows:
                    age = now - aw
                    if age >= 104:
                        continue
                    keep.append((aw, pts))
                    n += 1
                    tot += pts * (1.0 if age < 13 else 1 - (age - 13) / 91)
                rows[:] = keep
                if tot > 0:
                    out[gid] = tot / min(hi, max(lo, n))
            return out
        wr = table(self.wr, 40, 52)
        am = table(self.am, 12, 40)
        am = {g: v for g, v in am.items() if self.g[g].status == 'amateur'}
        wr_ids = sorted(wr, key=wr.get, reverse=True)
        am_ids = sorted(am, key=am.get, reverse=True)
        self.wr_avg = wr
        self.wr_pos = {g: i + 1 for i, g in enumerate(wr_ids)}
        self.am_pos = {g: i + 1 for i, g in enumerate(am_ids)}
        self.ctx.world_rankings[(year, week)] = wr_ids[:2000]
        self.ctx.amateur_rankings[(year, week)] = am_ids[:1000]

    def update_fame(self, year, week):
        now = self.abs_week(year, week)
        for gid, rows in self.fame_log.items():
            rows[:] = [(aw, pts) for aw, pts in rows if now - aw < PR.FAME_WEEKS]
            self.fame[gid] = sum(pts for _, pts in rows)

    def player_prestige(self, gid):
        return PR.player_prestige(self.fame.get(gid, 0.0), self.legacy[gid])

    # ---- eligibility and priority ---------------------------------------------------------------
    def eligible(self, g, s, week):
        tier, st = s.tier, g.status
        mt = TOUR_BY_KEY.get(g.tour)
        mtier = mt.tier if mt else 9
        countries = {c for c, _ in TOUR_BY_KEY[s.tour].countries} if s.tour in TOUR_BY_KEY else set()
        if s.category == 'national_open' and tier >= 2:
            return st == 'pro' or (st == 'amateur' and g.country == s.host_country and self.am_pos.get(g.id, 9999) <= 300)
        if tier == 1:
            if st == 'pro':
                return mtier <= 2 or self.wr_pos.get(g.id, 9999) <= 500
            return st == 'amateur' and self.am_pos.get(g.id, 9999) <= 25
        if tier == 2:
            return st == 'pro' and (mtier <= 2 or (mtier <= 4 and g.country in countries))
        if tier == 3:
            return st == 'pro' and (mtier <= 3 or g.country in countries)
        if tier == 4:
            return st == 'pro' and (g.tour == s.tour or g.country in countries or mtier == 4 and region_of(g) ==
                                    COUNTRIES[s.host_country].region)
        if tier == 5:
            return g.tour == s.tour
        if tier == 6:
            if st != 'amateur':
                return False
            if g.tour in COLLEGE_WINDOWS and _in_window(week, COLLEGE_WINDOWS[g.tour]):
                return False                                  # in college season
            return g.tour == s.tour or g.country in countries
        return False

    def priority(self, g, s):
        """Lower sorts first: (class, strength)."""
        mt = TOUR_BY_KEY.get(g.tour)
        mtier = mt.tier if mt else 9
        amateur_event = s.tier >= 5
        strength = self.am_pos.get(g.id, 99999) if amateur_event or g.status == 'amateur' else self.wr_pos.get(g.id, 99999)
        if g.status == 'amateur' and s.tier <= 4:
            return (9, strength)
        if g.tour == s.tour:
            cls = 0
        elif s.tier == 1 and g.tour in PREMIER_TOURS:
            cls = 1
        elif s.category == 'national_open' and g.country == s.host_country:
            cls = 1
        elif mtier < s.tier:
            cls = 2
        elif mtier == s.tier:
            cls = 3
        else:
            cls = 4
        return (cls, strength)

    # ---- the AI's choice of events --------------------------------------------------------------
    def log(self, gid, year, week, text):
        """Add a line to a golfer's career history."""
        self.history[gid].append((year, week, text))

    def ledger(self, year, gid):
        led = self.ledgers[year].get(gid)
        if led is None:
            led = self.ledgers[year][gid] = FIN.Ledger()
        return led

    def target_events(self, g):
        if g.lifestyle == 'retired':
            return 0
        if g.lifestyle == 'part_time' and g.status in ('pro', 'amateur'):
            return 4 if g.status == 'pro' else 6               # a job comes first
        if g.status == 'club_pro':
            return 4
        if g.tour.startswith('CO_'):
            return 15
        if g.status == 'amateur':
            return 10
        if g.tour in PREMIER_TOURS:                             # Premier players pick their spots
            return 15 + 8 * g.attrs['stamina'] / 100 - (4 if self.player_prestige(g.id) >= 65 else 0)
        return 19 + 8 * g.attrs['stamina'] / 100

    def bar(self, g):
        """The minimum event value worth playing for this golfer."""
        if g.status == 'club_pro':
            return 55.0
        if g.lifestyle == 'part_time':
            return 12.0
        home = self.home_level.get(g.tour, 20.0)
        return max(home - 20, 0.9 * self.player_prestige(g.id) + 3, 8.0)

    def base_value(self, g, ed, venue_country):
        """An event's appeal before personal circumstances: prestige, home country, travel."""
        v = self.event_prestige[ed.series.series_id]
        if venue_country == g.country:
            v += 6
        elif COUNTRIES[venue_country].region == region_of(g):
            v += 2
        else:
            v -= 6 if ed.series.tier >= 2 else 2
        if g.lifestyle == 'part_time':                       # they have a job: local events only
            v += 8 if venue_country == g.country else -40
        return v

    def event_value(self, g, ed, week, rng, venue_country):
        s = ed.series
        v = self.base_value(g, ed, venue_country)
        weeks = self.played[ed.year][g.id]
        streak = 0
        w = week - 1
        while w in weeks:
            streak += 1
            w -= 1
        if streak >= 2:
            v -= 5 * (streak - 1) ** 1.4
        # catching up or easing off against the season plan
        pace = self.target_events(g) * week / 52 - len(weeks)
        v += max(-25.0, min(6.0, 3.5 * pace))
        if week + 1 in MAJOR_WEEKS and self.wr_pos.get(g.id, 9999) <= 100:
            v -= 6                                           # resting before a major
        if week - 1 in MAJOR_WEEKS and week - 1 in weeks:
            v -= 8                                           # resting after a major
        # tired golfers rest; good course managers plan their rest better
        v -= (8 + 10 * g.attrs["management"] / 100) * 2 * max(0.0, self.fatigue[g.id] - 0.1)
        champs = self.champions.get(s.series_id)
        if champs and champs[-1][1] == g.id:
            v += 5                                           # defending champion
        return v + rng.gauss(0, 3)

    # ---- the week ------------------------------------------------------------------------------
    def run_year(self, year, progress=None):
        self.year = year
        self.refresh_people(year)
        eds = self.cal.editions(year)
        for week in range(1, 53):
            self.run_week(year, week, [e for e in eds if e.week == week])
            if progress:
                progress(year, week)
        self.end_of_season(year)

    def run_week(self, year, week, eds):
        rng = random.Random(_seed(self.seed, year, week, 'entries'))
        venues = self.lib.venues(year)
        busy = defaultdict(set)                              # gid -> days committed this week
        fields = {}                                          # event_id -> [per-site golfer lists]

        def commit(ed, ids_by_site):
            fields[ed.event_id] = ids_by_site
            for ids in ids_by_site:
                for gid in ids:
                    busy[gid] |= ed.series.day_set

        if self.development and (week - 1) % 4 == 0:
            self.plan_block(year, week)
        special = [e for e in eds if self.is_special(e.series)]
        regular = [e for e in eds if not self.is_special(e.series)]
        for ed in sorted(special, key=lambda e: (e.series.tier, e.series.series_id)):
            sites = self.special_field(ed, year, week, rng, busy)
            if sites is not None:
                commit(ed, sites)
        # Regular events: golfers choose, events accept in priority order (deferred acceptance)
        if regular:
            self.regular_entries(regular, year, week, rng, venues, busy, commit)
        self.play_week(year, week, [e for e in eds if e.event_id in fields], fields, venues)
        self.develop_week(year, week)
        self.update_rankings(year, week)
        self.update_fame(year, week)
        self.snapshot_standings(year, week)
        self.update_fatigue(year, week)

    def is_special(self, s):
        return (s.kind in ('major', 'qualifying') or s.category in ('elite_amateur', 'national_amateur',
                                                                    'college_postseason')
                or s.series_id == 'PT_PREMIER_TOUR_FINALS')

    def regular_entries(self, regular, year, week, rng, venues, busy, commit):
        cap = {ed.event_id: ed.series.field for ed in regular}
        country = {ed.event_id: CITY_BY_NAME[venues[ed.event_id][0].city].country for ed in regular}
        by_id = {ed.event_id: ed for ed in regular}
        prefs = {}
        for g in self.world.golfers:
            if (not g.tour and g.status != 'club_pro') or g.id in self.injured or g.lifestyle == 'retired':
                continue
            if self.development and self.plans.get(g.id, {}).get(week, ('play',))[0] != 'play':
                continue                                     # a training or rest week in their plan
            opts = []
            bar = self.bar(g)
            for ed in regular:
                if busy[g.id] & ed.series.day_set or not self.eligible(g, ed.series, week):
                    continue
                v = self.event_value(g, ed, week, rng, country[ed.event_id])
                opts.append((v, ed.event_id))
            if not opts:
                continue
            opts.sort(reverse=True)
            want = [eid for v, eid in opts if v >= bar]
            spare = [eid for v, eid in opts if bar - 15 <= v < bar]   # would fill a place if asked
            prefs[g.id] = (want, spare)
        held = defaultdict(list)                             # event_id -> [(priority, gid)]
        nxt = {gid: 0 for gid in prefs}
        free = [gid for gid, (want, _) in prefs.items() if want]
        while free:
            gid = free.pop()
            want = prefs[gid][0]
            if nxt[gid] >= len(want):
                continue
            eid = want[nxt[gid]]
            nxt[gid] += 1
            s = by_id[eid].series
            held[eid].append((self.priority(self.g[gid], s), gid))
            if len(held[eid]) > cap[eid] or self._amateurs_over(held[eid], s):
                held[eid].sort()
                bumped = self._bump(held[eid], s, cap[eid])
                if bumped is not None:
                    free.append(bumped)
        placed = {gid for v in held.values() for _, gid in v}
        for eid, ed in by_id.items():
            s = ed.series
            if len(held[eid]) < cap[eid]:
                extra = sorted((self.priority(self.g[gid], s), gid) for gid, (_, spare) in prefs.items()
                               if gid not in placed and eid in spare)
                for pr, gid in extra:
                    if len(held[eid]) >= cap[eid]:
                        break
                    held[eid].append((pr, gid))
                    if self._amateurs_over(held[eid], s):
                        held[eid].pop()
                        continue
                    placed.add(gid)
            ids = [gid for _, gid in sorted(held[eid])]
            if ids:
                commit(ed, [ids])

    def _amateurs_over(self, rows, s):
        lim = AMATEUR_CAP.get(s.tier)
        return lim is not None and sum(1 for _, gid in rows if self.g[gid].status == 'amateur') > lim

    def _bump(self, rows, s, capacity):
        lim = AMATEUR_CAP.get(s.tier)
        if lim is not None:
            ams = [i for i, (_, gid) in enumerate(rows) if self.g[gid].status == 'amateur']
            if len(ams) > lim:
                return rows.pop(ams[-1])[1]
        if len(rows) > capacity:
            return rows.pop()[1]
        return None

    # ---- special fields --------------------------------------------------------------------------
    def available(self, gid, s, busy):
        return not (busy[gid] & s.day_set) and gid not in self.injured and self.g[gid].lifestyle != 'retired'

    def ranked_amateurs(self, pred):
        ams = [g for g in self.world.golfers if g.status == 'amateur' and pred(g)]
        return sorted(ams, key=lambda g: (self.am_pos.get(g.id, 99999), -g.overall))

    def special_field(self, ed, year, week, rng, busy):
        s = ed.series
        sid = s.series_id
        free = lambda g: self.available(g.id, s, busy)
        if s.kind == 'major':
            f = Q.build_field(sid, year, self.ctx)
            ids = [gid for gid in f.ids() if gid in self.g and gid not in self.injured
                   and self.g[gid].lifestyle != 'retired']
            target = s.field
            if len(ids) < (90 if sid == 'TOUR_MASTERS' else target):
                # The world's first year has no qualifying history: fill from the world ranking.
                fill = [gid for gid in self.ctx.ranking(year, week - 1) if gid not in ids and gid in self.g
                        and gid not in self.injured and self.g[gid].lifestyle != 'retired']
                ids += fill[:(90 if sid == 'TOUR_MASTERS' else target) - len(ids)]
            self.stage_log[(year, sid, 'field')] = f
            return [ids]
        if sid == 'PT_PREMIER_TOUR_FINALS':
            rows = self.ctx.standing('PREMIER', year, week - 1)
            return [[gid for gid in rows if self.g[gid].status == 'pro' and gid not in self.injured][:s.field]]
        if s.category == 'elite_amateur':
            regions = ELITE_AMATEUR_REGIONS.get(sid)
            pred = (lambda g: free(g) and region_of(g) in regions) if regions else (lambda g: free(g))
            if s.eligibility == 'mid_amateur':
                pred = lambda g: free(g) and g.age(year) >= 25
            return [[g.id for g in self.ranked_amateurs(pred)[:s.field]]]
        if s.category == 'national_amateur':
            home = self.ranked_amateurs(lambda g: free(g) and g.country == s.host_country)
            rest = self.ranked_amateurs(lambda g: free(g) and g.country != s.host_country and
                                        region_of(g) == COUNTRIES[s.host_country].region)
            take = home[:s.field]
            take += rest[:max(0, min(s.field - len(take), s.field // 4))]
            return [[g.id for g in take]]
        if s.category == 'college_postseason':
            return self.college_postseason(ed, year, free)
        if sid == 'CLUB_PRO_CHAMPIONSHIP':
            clubs = [g for g in self.world.golfers if g.status == 'club_pro' and free(g)]
            clubs.sort(key=lambda g: (g.country != 'USA', -(g.overall + rng.gauss(0, 4))))   # sectional qualifying
            return [[g.id for g in clubs[:s.field]]]
        if s.category == 'q_school':
            return self.qschool_field(ed, year, week, free)
        if s.category == 'qualifier':
            return self.qualifier_field(ed, year, week, rng, free)
        return None

    def college_postseason(self, ed, year, free):
        s = ed.series
        sid = s.series_id
        d1 = [g for g in self.world.golfers if g.tour == 'CO_US_D1' and free(g)]
        rank = lambda gs: sorted(gs, key=lambda g: (self.am_pos.get(g.id, 99999), -g.overall))
        if sid.startswith('CONFERENCE_CHAMPIONSHIP_'):
            k = int(sid.rsplit('_', 1)[1]) - 1
            return [[g.id for g in rank([g for g in d1 if g.id % 8 == k])[:s.field]]]
        if sid.startswith('COLLEGE_REGIONAL_'):
            k = int(sid.rsplit('_', 1)[1]) - 1
            top = rank(d1)[:300]
            return [[g.id for i, g in enumerate(top) if (i // 4 % 2 == 0 and i % 4 == k) or
                     (i // 4 % 2 == 1 and 3 - i % 4 == k)]]
        if sid == 'COLLEGE_NATIONAL_CHAMPIONSHIP':
            ids = []
            for k in range(1, 5):
                ids += [gid for gid, pos in self.ctx.finishers(f'COLLEGE_REGIONAL_{k}', year) if pos is not None][:39]
            return [ids[:s.field]]
        if sid == 'SMALL_COLLEGE_CHAMPIONSHIP':
            return [[g.id for g in rank([g for g in self.world.golfers if g.tour == 'CO_US_SMALL' and free(g)])[:s.field]]]
        if sid == 'INTL_UNIVERSITY_CHAMPIONSHIP':
            return [[g.id for g in rank([g for g in self.world.golfers if g.tour == 'CO_INTL' and free(g)])[:s.field]]]
        return None

    # ---- Q-School ----------------------------------------------------------------------------------
    def _money_rank(self, tour, year):
        m = self.money[(tour, year)]
        members = [g for g in self.world.golfers if g.tour == tour]
        members.sort(key=lambda g: -m.get(g.id, 0.0))
        return [g.id for g in members]

    def _qs_pool(self, regions, exclude, year, free):
        pool = [g for g in self.world.golfers if g.status == 'pro' and free(g) and g.id not in exclude
                and g.tour not in PREMIER_TOURS and region_of(g) in regions and g.lifestyle == 'full_time']
        pool.sort(key=lambda g: self.wr_pos.get(g.id, 99999))
        return pool

    def qschool_field(self, ed, year, week, free):
        s = ed.series
        sid = s.series_id
        n = s.field * s.sites
        log = self.stage_log
        def split(ids):
            return [ids[i::s.sites] for i in range(s.sites)]
        def advanced(prev, per_site):
            out = []
            for site, rows in sorted(self.ctx.results.get((prev, year), {}).items()):
                out += [gid for gid, pos in rows if pos is not None][:per_site]
            return out
        if sid.startswith('PT_'):
            ch = self._money_rank('CH_AMERICAS', year)
            prem = self._money_rank_premier(year)
            exclude = set(ch[:25])
            pool = [g.id for g in self._qs_pool(QS_AMERICAS, exclude, year, free)]
            final_direct = [gid for gid in ch[25:75] + prem[200:250] if free(self.g[gid])]
            rest = [gid for gid in pool if gid not in final_direct]
            tiers = {'PT_QSCHOOL_SECOND': rest[:100], 'PT_QSCHOOL_FIRST': rest[100:400], 'PT_QSCHOOL_PRE': rest[400:712]}
            if sid == 'PT_QSCHOOL_PRE':
                ids = tiers[sid]
            elif sid == 'PT_QSCHOOL_FIRST':
                ids = advanced('PT_QSCHOOL_PRE', 20) + tiers[sid]
            elif sid == 'PT_QSCHOOL_SECOND':
                ids = advanced('PT_QSCHOOL_FIRST', 22) + tiers[sid]
            else:
                ids = advanced('PT_QSCHOOL_SECOND', 18) + final_direct
        elif sid.startswith('EU_'):
            ch = self._money_rank('CH_EUROPE', year)
            pe = [gid for gid in self._money_rank('PT_EUROPE', year)]
            exclude = set(ch[:45])
            final_direct = [gid for gid in ch[45:90] + pe[60:]]
            final_direct = [gid for gid in final_direct if free(self.g[gid])]
            rest = [g.id for g in self._qs_pool(QS_EUROPE, exclude, year, free) if g.id not in final_direct]
            if sid == 'EU_QSCHOOL_FIRST':
                ids = rest[150:150 + n]
            elif sid == 'EU_QSCHOOL_SECOND':
                ids = advanced('EU_QSCHOOL_FIRST', 20) + rest[:150]
            else:
                ids = advanced('EU_QSCHOOL_SECOND', 18) + final_direct
        elif sid == 'JP_QSCHOOL_FINAL':
            keep = set(self._money_rank('CH_JAPAN', year)[:60])
            ids = [g.id for g in self._qs_pool(('Asia',), keep, year, free) if g.country in ('Japan', 'South Korea')]
        else:  # ASIA_QSCHOOL_FINAL (week 2: last season's standings)
            keep = set(self.ctx.standing('CH_ASIA', year - 1)[:60])
            ids = [g.id for g in self._qs_pool(('Asia', 'Oceania'), keep, year, free)]
        ids = list(dict.fromkeys(ids))[:n]
        log[(year, sid)] = ids
        return split(ids) if s.sites > 1 else [ids]

    def _money_rank_premier(self, year):
        m = self.money[('PREMIER', year)]
        members = [g for g in self.world.golfers if g.tour in PREMIER_TOURS]
        members.sort(key=lambda g: -m.get(g.id, 0.0))
        return [g.id for g in members]

    # ---- USA Open and Britannia Open qualifying ----------------------------------------------------
    def qualifier_field(self, ed, year, week, rng, free):
        s = ed.series
        sid = s.series_id
        major = 'USA_OPEN' if sid.startswith('USA_OPEN') else 'BRITANNIA_OPEN'
        key = (year, major)
        if key not in self.stage_log:
            f = Q.build_field(major, year, self.ctx.as_of(year, week))
            exempt = {e.golfer_id for e in f.entries if e.primary[1:] not in ('Q', 'F')}
            limit = 250 if major == 'USA_OPEN' else 300
            tiers_ok = PREMIER_TOURS if major == 'USA_OPEN' else PREMIER_TOURS + tuple(
                k for k, t in TOUR_BY_KEY.items() if t.tier == 2)
            direct = {g.id for g in self.world.golfers if g.id not in exempt and g.status != 'club_pro' and
                      g.lifestyle != 'retired' and (self.wr_pos.get(g.id, 9999) <= limit or g.tour in tiers_ok)}
            home = QS_AMERICAS if major == 'USA_OPEN' else QS_EUROPE
            pool = []
            for g in self.world.golfers:
                if g.id in exempt or g.id in direct or g.status == 'club_pro' and major == 'BRITANNIA_OPEN' \
                        or g.lifestyle == 'retired':
                    continue
                good = g.status in ('pro', 'club_pro') or self.am_pos.get(g.id, 9999) <= 400
                keen = 0.75 if region_of(g) in home else 0.08
                if good and rng.random() < keen:
                    pool.append(g.id)
            pool.sort(key=lambda gid: (self.wr_pos.get(gid, 9999) if self.g[gid].status != 'amateur'
                                       else self.am_pos.get(gid, 9999) * 3))
            self.stage_log[key] = {'exempt': exempt, 'direct': direct, 'pool': pool, 'advanced': [], 'entered': set()}
        st = self.stage_log[key]
        n = s.field * s.sites
        if sid.startswith(('USA_OPEN_LOCAL', 'BRITANNIA_REGIONAL')):
            ids = [gid for gid in st['pool'] if gid not in st['entered'] and free(self.g[gid])][:n]
            rng.shuffle(ids)
            st['entered'] |= set(ids)
        else:
            per = Q.STAGES['USA_OPEN_FINAL' if major == 'USA_OPEN' else 'BRITANNIA_FINAL']['per_site']
            if not st['advanced']:
                for feeder in Q.STAGES['USA_OPEN_FINAL' if major == 'USA_OPEN' else 'BRITANNIA_FINAL']['feeders']:
                    for site, rows in sorted(self.ctx.results.get((feeder, year), {}).items()):
                        st['advanced'] += [gid for gid, pos in rows if pos is not None][:per]
            direct = [gid for gid in st['direct'] if free(self.g[gid]) and gid not in st['entered']]
            direct.sort(key=lambda gid: self.wr_pos.get(gid, 9999))
            if sid == 'USA_OPEN_FINAL_INTL':
                ids = [gid for gid in direct if region_of(self.g[gid]) not in QS_AMERICAS and rng.random() < 0.6][:n]
            elif sid == 'USA_OPEN_FINAL':
                ids = [gid for gid in st['advanced'] if free(self.g[gid])]
                ids += [gid for gid in direct if region_of(self.g[gid]) in QS_AMERICAS and rng.random() < 0.7]
                ids = ids[:n]
            else:
                ids = [gid for gid in st['advanced'] if free(self.g[gid])]
                ids += [gid for gid in direct if rng.random() < 0.5]
                ids = ids[:n]
            st['entered'] |= set(ids)
            rng.shuffle(ids)
        if s.sites == 1:
            return [ids]
        if sid == 'USA_OPEN_FINAL_INTL':                        # England site for Europe, Japan for Asia
            eu = [gid for gid in ids if region_of(self.g[gid]) in QS_EUROPE]
            asia = [gid for gid in ids if gid not in set(eu)]
            return [eu[:s.field], asia[:s.field]]
        return [ids[i::s.sites] for i in range(s.sites)]

    # ---- playing and recording ----------------------------------------------------------------------
    def play_week(self, year, week, eds, fields, venues):
        tasks = []
        for ed in eds:
            s = ed.series
            for site, ids in enumerate(fields[ed.event_id]):
                v = venues[ed.event_id][min(site, len(venues[ed.event_id]) - 1)]
                tasks.append({'event_id': ed.event_id, 'site': site, 'course': self.lib.course(v),
                              'golfers': [self.g[gid] for gid in ids], 'match_play': s.match_play,
                              'rounds': s.rounds, 'cut_top': s.cut_top,
                              'prestige': self.event_prestige[s.series_id],
                              'seed': _seed(self.seed, ed.event_id, site)})
        if not tasks:
            return
        tasks.sort(key=lambda t: -len(t['golfers']) * t['rounds'])
        if self.workers > 1 and len(tasks) > 1:
            if not hasattr(self, '_pool'):
                self._pool = ProcessPoolExecutor(self.workers)
            outs = list(self._pool.map(play_site, tasks))
        else:
            outs = [play_site(t) for t in tasks]
        by_event = defaultdict(dict)
        for o in outs:
            by_event[o['event_id']][o['site']] = o
        for ed in eds:
            self.record_event(ed, year, week, by_event[ed.event_id], venues[ed.event_id])

    def close(self):
        if hasattr(self, '_pool'):
            self._pool.shutdown()
            del self._pool

    def record_event(self, ed, year, week, site_out, venue_list):
        s = ed.series
        sid = s.series_id
        p = self.event_prestige[sid]
        res = EventResult(ed.event_id, sid, year, week,
                          [(v.course_id, v.layout, v.city) for v in venue_list], [], p)
        amateur_event = s.tier >= 5
        all_ids = []
        for site in sorted(site_out):
            o = site_out[site]
            v = venue_list[min(site, len(venue_list) - 1)]
            course = self.lib.course(v)
            finish = o['finish']
            res.finish.append(finish)
            res.playoff = max(res.playoff, o['playoff'])
            self.ctx.add_result(sid, year, [(gid, pos) for gid, pos, _ in finish], site=site)
            rec = self.records.get(course)
            pars = [h.par for h in course.holes]
            # scoring relative to the field in the same round (the fair way to compare across courses)
            by_round = defaultdict(list)
            for gid, rd, score, holes, _ in o['rounds']:
                by_round[rd].append(score)
            round_avg = {rd: sum(v) / len(v) for rd, v in by_round.items()}
            for gid, rd, score, holes, st in o['rounds']:
                ps = self.pstats[year][gid]
                ps['rounds'] += 1
                ps['strokes'] += score
                ps['vs_field'] += score - round_avg[rd]
                for k, val in zip(STAT_KEYS, st):
                    ps[k] += val
                rec.add_round(Mark(score, score - course.par, self.g[gid].name, ed.event_id, year, week, rd, s.tier),
                              holes, pars)
                self.holes_played[year] += len(holes)
                self.g[gid].familiarity[course.familiarity_key] = self.g[gid].familiarity.get(course.familiarity_key, 0) + 1
            for gid, idx, strokes, stage in o['holes']:
                rec.add_hole(idx, strokes, pars[idx], self.g[gid].name, ed.event_id, year, stage)
                self.holes_played[year] += 1
            rounds = Counter(gid for gid, *_ in o['rounds'])
            for gid, n in Counter(gid for gid, *_ in o['holes']).items():
                rounds[gid] += n / 18
            host_region = COUNTRIES[CITY_BY_NAME[v.city].country].region
            for gid, n in rounds.items():
                self._week_load[gid] += self.load(self.g[gid], n, region_of(self.g[gid]) != host_region, year)
                self._week_event[gid] = ed.event_id
                self.week_rounds[gid] += n
            for gid, _, _ in finish:
                self.ledger(year, gid).events += FIN.event_cost(self.g[gid], s, v.city)
            if s.kind != 'qualifying' and finish and finish[0][1] == 1:
                w = finish[0][0]
                tp = '' if finish[0][2] is None else f' at {finish[0][2] - course.par * s.rounds:+d}'
                self.log(w, year, week, f'Won the {s.name}{tp} ({self.lib.sites[v.course_id]["name"]})')
            if s.rounds and finish and finish[0][2] is not None and site == 0:
                win_total = finish[0][2]
                self.champions[sid].append((year, finish[0][0], win_total - course.par * s.rounds))
            elif s.match_play and site == 0:
                self.champions[sid].append((year, res.winner(0), None))
            self.pay_out(s, finish, year)
            for gid, pos, _ in finish:
                all_ids.append(gid)
                self.played[year][gid].append(week)
                aw = self.abs_week(year, week)
                if s.kind != 'qualifying':
                    g = self.g[gid]
                    if g.status == 'amateur':
                        self.am[gid].append((aw, PR.amateur_points(p, pos)))
                    if s.tier <= 4:
                        self.wr[gid].append((aw, PR.world_points(p, pos)))
                    self.fame_log[gid].append((aw, PR.fame_points(p, pos)))
                    if pos == 1:
                        kind = 'major' if s.kind == 'major' else 'flagship' if s.category == 'flagship' else \
                            'premier' if s.tier == 1 else None
                        if kind:
                            self.legacy[gid] += PR.LEGACY[kind]
        # field strength and the event's prestige for next year
        ranks = [self.am_pos.get(gid) if amateur_event else self.wr_pos.get(gid) for gid in all_ids]
        res.field_strength = PR.field_strength(ranks, amateur=amateur_event)
        quality = S.mean(PR.COURSE_QUALITY[(self.lib.sites[v.course_id]['cls'], v.layout)] for v in venue_list)
        if s.kind not in ('qualifying',):
            self.event_factors[sid].append(PR.factors(s, res.field_strength, quality))
            self.event_prestige[sid] = PR.prestige_from(self.event_factors[sid])
        self.prestige_history[sid].append((year, p, res.field_strength))
        self.results[ed.event_id] = res
        self.stats[year]['events'] += 1

    # ---- fatigue and injuries ------------------------------------------------------------------
    def load(self, g, rounds, travelled, year):
        """Fatigue from playing: rounds, travel and age, eased by stamina."""
        stam = g.attrs['stamina'] / 100
        return (rounds * FATIGUE_PER_ROUND * (1.4 - 0.8 * stam) * (1.15 if travelled else 1.0)
                * (1 + 0.02 * max(0, g.age(year) - 30)))

    def injury_chance(self, g, rounds, year, f=None):
        """Chance of an injury from one event: tiredness, injury resistance, age and stamina."""
        f = self.fatigue[g.id] if f is None else f
        return (INJURY_BASE * rounds / 4 * (1 + 6 * f * f) * (1.8 - 1.6 * g.attrs['injury_resistance'] / 100)
                * (1 + 0.05 * max(0, g.age(year) - 30)) * (1 + 0.5 * (1 - g.attrs['stamina'] / 100)))

    def update_fatigue(self, year, week):
        """After the week: players who played get more tired (and may get hurt); the rest recover."""
        rng = random.Random(_seed(self.seed, year, week, 'injury'))
        now = self.abs_week(year, week)
        for gid in [gid for gid, (back, _, _) in self.injured.items() if back <= now]:
            del self.injured[gid]
        played = set(self._week_load)
        for g in self.world.golfers:
            f = self.fatigue[g.id]
            if g.id in played:
                load = self._week_load[g.id]
                rounds = load / max(1e-9, self.load(g, 1, False, year))
                if rng.random() < self.injury_chance(g, rounds, year):
                    weeks = max(1, min(40, round(math.exp(rng.gauss(math.log(3), 0.9))
                                                 * (1 + 0.03 * max(0, g.age(year) - 30)))))
                    kind = rng.choice(INJURIES)
                    self.injured[g.id] = (now + weeks + 1, kind, weeks)
                    self.injuries[year].append((week, g.id, kind, weeks, self._week_event.get(g.id)))
                    text = f'Injured ({kind}), out for {weeks} week{"s" if weeks > 1 else ""}'
                    if self.development:
                        lost = D.serious_injury(g, weeks, rng)
                        if lost:
                            text += ' — lasting damage: ' + ', '.join(f'{k.replace("_", " ")} −{v}' for k, v in lost.items())
                    self.log(g.id, year, week, text)
                    f = 0.0                                  # the time off rests them
                else:
                    f = 1 - (1 - 0.9 * f) * (1 - min(0.9, load))
            elif f and self.week_activity.get(g.id) == 'train':
                f = 0.85 * f + 0.02 * (1.4 - 0.8 * g.attrs['stamina'] / 100)    # practice is lighter work
            elif f:
                f *= 0.40 + 0.30 * (1 - g.attrs['recovery_rate'] / 100)
            self.fatigue[g.id] = f if f > 0.005 else 0.0
            g.fatigue = self.fatigue[g.id]
        self._week_load.clear()
        self._week_event.clear()
        self.week_rounds.clear()

    def is_injured(self, gid):
        return gid in self.injured

    def pay_out(self, s, finish, year):
        if not s.purse:
            return
        paid = [(gid, pos) for gid, pos, _ in finish if pos is not None and self.g[gid].status != 'amateur']
        if not paid:
            return
        shares = PR.payout_shares(len(paid))
        i = 0
        while i < len(paid):
            pos = paid[i][1]
            j = i
            while j < len(paid) and paid[j][1] == pos:
                j += 1
            each = sum(shares[i:j]) / (j - i) * s.purse
            for gid, _ in paid[i:j]:
                self.earnings[year][gid] += each
                led = self.ledger(year, gid)
                led.prize += each
                if s.tier <= 2:
                    led.caddie += FIN.CADDIE_SHARE * each
                keys = [s.tour] if s.tour in TOUR_BY_KEY else []
                if s.kind == 'major':
                    keys = list(PREMIER_TOURS)
                if s.tier <= 1:
                    keys.append('PREMIER')
                for k in keys:
                    self.money[(k, year)][gid] += each
            i = j

    def snapshot_standings(self, year, week):
        for (tour, y), m in self.money.items():
            if y == year:
                self.ctx.standings[(tour, year, week)] = sorted(m, key=m.get, reverse=True)

    # ---- end of season -----------------------------------------------------------------------------
    def end_of_season(self, year):
        for (tour, y), m in list(self.money.items()):
            if y != year:
                continue
            if tour == 'PREMIER':
                members = [g.id for g in self.world.golfers if g.tour in PREMIER_TOURS]
            else:
                members = [g.id for g in self.world.golfers if g.tour == tour]
            order = sorted(set(members) | set(m), key=lambda gid: -m.get(gid, 0.0))
            self.ctx.standings[(tour, year)] = order
        for t in TOUR_BY_KEY:
            if (t, year) not in self.ctx.standings:
                self.ctx.standings[(t, year)] = []
        for gid in self.legacy:
            self.legacy[gid] *= PR.LEGACY_DECAY
        self.settle_finances(year)
        from .cards import apply_cards
        apply_cards(self, year)
        for gid, frm, to, why in self.card_log[year]:
            self.log(gid, year, 53, f'{TOUR_BY_KEY[frm].name if frm in TOUR_BY_KEY else "—"} → {TOUR_BY_KEY[to].name} ({why})')
        if self.development:
            from . import careers
            self.career_counts[year] = careers.decide(self, year)
            rng = random.Random(_seed(self.seed, year, 'aging'))
            for g in self.world.golfers:
                if g.lifestyle != 'retired':
                    D.age_year(g, g.age(year + 1), rng)
            self.juniors_added[year + 1] = careers.add_juniors(self, year + 1)
            for g in self.world.golfers:
                self.fatigue[g.id] = g.fatigue = 0.0         # the off-season rests everyone

    def settle_finances(self, year):
        """Sponsors, salaries and living costs for the year; savings carry over."""
        for g in self.world.golfers:
            if g.lifestyle == 'retired' and g.id not in self.ledgers[year]:
                continue
            led = self.ledger(year, g.id)
            if g.status == 'pro':
                led.sponsors = PR.endorsements(self.player_prestige(g.id))
            if g.lifestyle == 'part_time':
                led.salary = FIN.SALARY['club_pro' if g.status == 'club_pro' else 'part_time']
                led.living = FIN.LIVING_WORKING
            elif g.status == 'pro' and g.lifestyle == 'full_time':
                led.living = FIN.LIVING
            g.cash += led.net

    def season_results(self, year):
        """Per golfer this season: wins, top-3 finishes, whether they moved up a level, money rank."""
        out = defaultdict(dict)
        for r in self.results.values():
            if r.year != year or self.cal.by_id[r.series_id].kind == 'qualifying':
                continue
            for site in r.finish:
                for gid, pos, _ in site:
                    if pos == 1:
                        out[gid]['wins'] = out[gid].get('wins', 0) + 1
                    if pos is not None and pos <= 3:
                        out[gid]['top3'] = out[gid].get('top3', 0) + 1
        for gid, frm, to, _ in self.card_log[year]:
            if frm in TOUR_BY_KEY and to in TOUR_BY_KEY and TOUR_BY_KEY[to].tier < TOUR_BY_KEY[frm].tier:
                out[gid]['moved_up'] = True
        by_tour = defaultdict(list)
        for g in self.world.golfers:
            if g.status == 'pro' and g.tour in TOUR_BY_KEY:
                by_tour[g.tour].append(g.id)
        for tour, ids in by_tour.items():
            m = self.money[(tour, year)]
            ids.sort(key=lambda gid: -m.get(gid, 0.0))
            for i, gid in enumerate(ids):
                out[gid]['money_rank_pct'] = (i + 1) / len(ids)
        return out

    # ---- development and the monthly plan ------------------------------------------------------
    def plan_block(self, year, week0):
        """Each golfer plans the next four weeks: which weeks to play, which to train, which to rest.

        For every combination of weeks to play they weigh what the events are worth to their career
        against what playing or training does for their game (raw golfers learn a lot from
        tournaments), the cost of playing tired, and the risk of injury; a week not played is a
        training week, or a full rest week when they are tired."""
        weeks = [w for w in range(week0, week0 + 4) if w <= 52]
        eds = [e for e in self.cal.editions(year) if e.week in weeks and not self.is_special(e.series)]
        venues = self.lib.venues(year)
        country = {e.event_id: CITY_BY_NAME[venues[e.event_id][0].city].country for e in eds}
        by_week = {w: [e for e in eds if e.week == w] for w in weeks}
        rng = random.Random(_seed(self.seed, year, week0, 'plan'))
        cache = {}
        now = self.abs_week(year, 0)
        for g in self.world.golfers:
            if g.lifestyle == 'retired':
                continue
            key = (g.tour, g.country, g.status, g.lifestyle, self.wr_pos.get(g.id, 9999) <= 500,
                   self.am_pos.get(g.id, 9999) <= 25, self.am_pos.get(g.id, 9999) <= 300)
            if key not in cache:
                row = []
                for w in weeks:
                    best = None
                    for e in by_week[w]:
                        if self.eligible(g, e.series, w):
                            v = self.base_value(g, e, country[e.event_id])
                            best = v if best is None or v > best else best
                    row.append(best)
                cache[key] = row
            base = cache[key]
            age = g.age(year)
            cat = D.choose_category(g, rng)
            work = 0.3 if g.lifestyle == 'part_time' else 1.0
            gamma = 60.0
            dp = gamma * D.development_value(g, 'play', age)
            dt = gamma * D.development_value(g, 'train', age, cat) * work
            bar = self.bar(g)
            target = self.target_events(g)
            played0 = len(self.played[year][g.id])
            inj_until = self.injured.get(g.id, (0,))[0]
            stam = g.attrs['stamina'] / 100
            load4 = 4 * FATIGUE_PER_ROUND * (1.4 - 0.8 * stam) * (1 + 0.02 * max(0, age - 30))
            rest_rec = 0.40 + 0.30 * (1 - g.attrs['recovery_rate'] / 100)
            top100 = self.wr_pos.get(g.id, 9999) <= 100
            playable = [i for i, w in enumerate(weeks) if base[i] is not None and now + w >= inj_until]
            best_val, best_mask = None, 0
            for mask in range(1 << len(playable)):
                f = self.fatigue[g.id]
                val, n = 0.0, played0
                for i, w in enumerate(weeks):
                    if now + w < inj_until:
                        f *= rest_rec
                        continue
                    j = playable.index(i) if i in playable else -1
                    if j >= 0 and mask >> j & 1:
                        pace = target * w / 52 - n
                        v = base[i] + max(-25.0, min(6.0, 3.5 * pace)) - (6 if w + 1 in MAJOR_WEEKS and top100 else 0)
                        eff = max(0.0, f - 0.2) * 1.25
                        val += (v - bar) + dp - 12 * eff - 400 * self.injury_chance(g, 4, year, f)
                        f = 1 - (1 - 0.9 * f) * (1 - load4)
                        n += 1
                    elif f > 0.25:
                        f *= rest_rec
                    else:
                        val += dt
                        f = 0.85 * f + 0.02
                if best_val is None or val > best_val:
                    best_val, best_mask = val, mask
            plan = {}
            f = self.fatigue[g.id]
            for i, w in enumerate(weeks):
                j = playable.index(i) if i in playable else -1
                if j >= 0 and best_mask >> j & 1:
                    plan[w] = ('play', cat)
                    f = 1 - (1 - 0.9 * f) * (1 - load4)
                elif f > 0.25 or now + w < inj_until:
                    plan[w] = ('rest', cat)
                    f *= rest_rec
                else:
                    plan[w] = ('train', cat)
                    f = 0.85 * f + 0.02
            self.plans[g.id] = plan

    def develop_week(self, year, week):
        """What each golfer did this week, and how it changed their game."""
        for g in self.world.golfers:
            if g.lifestyle == 'retired':
                continue
            rounds = self.week_rounds.get(g.id, 0.0)
            action, cat = self.plans.get(g.id, {}).get(week, ('rest', None))
            if rounds:
                act = 'play'
            elif g.id in self.injured:
                act = 'rest'
            else:
                act = 'train' if action in ('play', 'train') and self.development else 'rest'
            self.week_activity[g.id] = act
            if self.development and g.ceilings:
                scale = 0.3 if g.lifestyle == 'part_time' and act == 'train' else 1.0
                D.develop_week(g, act, g.age(year), cat, rounds, scale=scale)
