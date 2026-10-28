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
from bisect import insort
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field, replace

from . import development as D
from . import finance as FIN
from . import staff as ST
from . import prestige as PR
from . import qualification as Q
from .calendar import MAJOR_WEEKS, TOUR_BY_KEY, _in_window
from .course_library import default_library
from .engine import Conditions
from .golfer import Caddie
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
# golfers at college in the USA (wherever they are from) can play that country's amateur events
COLLEGE_AMATEUR_SERIES = {'CO_US_D1': 'AM_NORTH_AMERICA', 'CO_US_SMALL': 'AM_NORTH_AMERICA'}
ELITE_AMATEUR_REGIONS = {'LATIN_AMERICA_AMATEUR': ('Latin America',), 'AFRICA_AMATEUR': ('Africa',),
                         'EUROPEAN_AMATEUR': ('Europe',), 'ASIA_PACIFIC_AMATEUR': ('Asia', 'Oceania')}
QS_AMERICAS = ('North America', 'Latin America')
QS_EUROPE = ('Europe', 'Africa', 'Middle East')


def _seed(*parts):
    return int.from_bytes(hashlib.blake2b(':'.join(map(str, parts)).encode(), digest_size=8).digest(), 'big')


CLUB_PRO_DRIVING_REGIONS = ('Europe', 'North America')   # neighbouring countries' section events are a drive


def region_of(g):
    return COUNTRIES[g.country].region


# What happened in each golfer's week (Season.week_access), most to least successful
ACCESS = ('played: first choice', 'played: alternative', 'played: selected field', 'injured',
          'shut out: every acceptable field full', 'not selected for the college lineup', 'no suitable event scheduled',
          'not eligible for the events scheduled', 'could not afford any event', 'declined the events on offer',
          'chose to train', 'chose to rest', 'chose to work')
# Premier Tour playing rights (Season.premier_rights), in priority order for Premier events. Full status
# is sized so every fully exempt member fits the smallest ordinary Premier field (144) in the weeks with
# only one Premier event in the world; conditional members get the places left and look elsewhere too.
RIGHTS = ('exempt', 'full', 'graduate', 'conditional')
FULL_STATUS = 125                 # top of last season's Premier money list with full status
PREMIER_VISITOR_SHARE = 0.10      # places in a Challenger event Premier members may take ahead of residents
COURSE_RECORD_ROUNDS = 300       # a new course record is a moment once the layout had this many earlier rounds
ROTATION_RANK_STARTS = 3          # college/amateur lineups: ranking is worth a head start of this many starts
AMATEUR_OPEN_EXPANSION = 1.5      # open amateur events can take this many times their usual field


# named factories (not lambdas) so a Season can be saved and resumed (savegame.py)
def _dd_float():
    return defaultdict(float)


def _dd_list():
    return defaultdict(list)


def _dd_counter():
    return defaultdict(Counter)


# ---------------------------------------------------------------------------------------------
# Worker: plays one event site. Top-level so it can run in another process.
# ---------------------------------------------------------------------------------------------
def _for_course(x, fk):
    """What a worker needs of a golfer or caddie to play one course: the same person with only that
    course's familiarity (and no hidden ceilings), so what is sent to the worker stays small however
    long the career."""
    fam = x.familiarity.get(fk)
    if isinstance(x, Caddie):
        return x if not x.familiarity else Caddie(x.name, x.skills, {fk: fam} if fam else {})
    return replace(x, familiarity={fk: fam} if fam else {}, ceilings={})

def play_site(task):
    rng = random.Random(task['seed'])
    course, golfers = task['course'], task['golfers']
    caddies = {id(g): k for g, k in zip(golfers, task.get('caddies') or ())}
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
                                    on_round=on_round, on_hole=on_hole, caddies=caddies)
        out.update(finish=[(g.id, pos, None) for g, pos in res], playoff=0)
        return out
    wind = max(0.0, rng.gauss(course.typical_wind, 3.0))
    pins = 0.3 + 0.4 * task['prestige'] / 100
    cond = {r: Conditions(wind_mph=max(0.0, wind + rng.gauss(0, 2.5)), rain=rng.random() < 0.08,
                          pin_difficulty=pins) for r in range(1, task['rounds'] + 1)}
    cut_after = 2 if task['cut_top'] and task['rounds'] > 2 else None
    board, playoff = play_event(golfers, course, rng, cut_top=task['cut_top'] or len(golfers),
                                prestige=task['prestige'] / 100, cond_by_round=cond, rounds_n=task['rounds'],
                                cut_after=cut_after, on_round=on_round, on_hole=on_hole, caddies=caddies)
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
    team: dict = field(default_factory=dict)   # gid -> (coach id, caddie id) that week (0 = none)

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
        self.money = defaultdict(_dd_float)                  # (tour key, year) -> gid -> $
        self.earnings = defaultdict(_dd_float)               # year -> gid -> $ prize money
        self.career_prize = Counter()                        # gid -> $ prize money over the whole career
        self.played = defaultdict(_dd_list)                  # year -> gid -> [weeks]
        self.stage_log = defaultdict(list)
        self.card_log = defaultdict(list)                    # year -> [(gid, from, to, reason)]
        self.holes_played = Counter()                        # year -> holes
        self.stats = defaultdict(Counter)
        self.pstats = defaultdict(_dd_counter)               # year -> gid -> summed round stats
        self.plans = {}                                      # gid -> {week: (action, training category)}
        self.week_rounds = defaultdict(float)                # gid -> rounds played this week
        self.week_activity = {}                              # gid -> 'play' / 'train' / 'rest' this week
        self.ledgers = defaultdict(dict)                     # year -> gid -> finance.Ledger
        self.history = defaultdict(list)                     # gid -> [(year, week, text)]: career log
        self.career_counts = {}                              # year -> {decision: count}
        self.contracts = {}                                  # gid -> this season's sponsor income
        self.cash_start = {}                                 # year -> gid -> cash on 1 January
        self.prize_share = {}                                # gid -> share of a purse they tend to win
        self.snapshots = {}                                  # year -> gid -> completed-season evidence
        self.rank_start, self.am_start = {}, {}              # year -> world / amateur ranking on 1 January
        self.unpaid = Counter()                              # year -> purse money not paid out (small fields)
        self.juniors_added = {}                              # year -> number of new golfers
        self.new_pros_added = {}                             # year -> new professionals from outside the amateur game
        self.entry_routes = {}                               # (year, series) -> {gid: route code}
        self.staff = ST.initial_staff(world, seed)           # coaches and caddies
        self.staff_receipts = defaultdict(Counter)            # year -> ('coach'|'caddie', id) -> $ received
        self.overall_start = {}                              # year -> gid -> overall on 1 January
        self._teams = {}                                     # event id -> {gid: (coach, caddie)} this week
        self.entry_misses = defaultdict(Counter)             # year -> gid -> weeks shut out of full fields
        self.entry_wants = defaultdict(Counter)              # year -> gid -> weeks they wanted to play
        self.season_rounds = defaultdict(Counter)            # year -> gid -> competitive rounds played
        self.declined = defaultdict(_dd_list)                # year -> gid -> [series they could not pay to play]
        self.school_trips = defaultdict(Counter)             # year -> gid -> events their school paid for
        for g in world.golfers:                              # the world starts mid-history: assume the season
            if g.lifestyle != 'retired':                     # before it was a typical one for their lifestyle
                self.season_rounds[self.first_year - 1][g.id] = D.EXPERIENCE_ROUNDS * (1.0 if g.lifestyle == 'full_time' else 0.5)
        self.entry_stats = defaultdict(_dd_counter)          # year -> first-choice tour -> wanted/placed/shut out
        self.card_reasons = {}                               # year -> gid -> why they hold that season's card
        self.unheld = defaultdict(list)                      # year -> event ids with no entrants
        self.moments = defaultdict(list)                     # year -> special moments (aces, playoffs, records)
        self.rights = {}                                     # year -> gid -> (Premier playing rights, why)
        self.week_access = defaultdict(_dd_counter)          # year -> gid -> weeks by access outcome (ACCESS)
        self.denied_run = Counter()                          # gid -> consecutive weeks shut out of full fields
        self.max_denied_run = defaultdict(Counter)           # year -> gid -> longest such run
        self.denied_behind = defaultdict(Counter)            # year -> gid -> shut-out weeks while behind schedule
        self.week_avail = {}                                 # gid -> {week: 'ok'|'none'|'inelig'|'unaff'} (plan)
        self.access_log = defaultdict(_dd_list)              # year -> gid -> [(week, outcome, wanted, played)]
        self.event_routes = defaultdict(dict)                # year -> event id -> {gid: entry route} (regular)
        self._week_entered = {}                              # gid -> (event id, how) this week
        self._week_first = {}                                # gid -> first-choice event id this week
        self._week_shut = set()                              # gids shut out of every field they tried
        self.transitions = {}                                # year -> [career decisions with their reasons]
        self.activity_counts = defaultdict(_dd_counter)      # year -> gid -> weeks per activity
        self.assignments = {}                                # year -> staff assignments at the season's start
        self.staff_year = {}                                 # year -> staff id -> that season's work
        self.stuck_blocks = Counter()                        # gid -> consecutive months unable to afford a trip
        self.block_flags = defaultdict(_dd_counter)          # year -> gid -> monthly money state
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
        if tier == 6:                                         # college golfers too, around their college events
            return st == 'amateur' and (g.tour == s.tour or g.country in countries
                                        or COLLEGE_AMATEUR_SERIES.get(g.tour) == s.tour)
        if tier == 8:                                         # club professionals of the circuit's region
            return st == 'club_pro' and (g.country in countries or region_of(g) == COUNTRIES[s.host_country].region)
        return False

    def entry_ticket(self, g, s):
        """A golfer's place in the entry queue for this season's edition of an event (a fair draw: it
        never depends on how the population happens to be numbered)."""
        return _seed(self.seed, self.year, s.series_id, 'entry', g.id)

    def priority(self, g, s):
        """Lower sorts first: (class, strength, entry draw). Mini tours are open entry: their members
        get in by the draw, not by world ranking. Elsewhere ranking decides and the draw breaks ties
        (so unranked golfers are not ordered by id)."""
        mt = TOUR_BY_KEY.get(g.tour)
        mtier = mt.tier if mt else 9
        amateur_event = s.tier >= 5
        strength = self.am_pos.get(g.id, 99999) if amateur_event or g.status == 'amateur' else self.wr_pos.get(g.id, 99999)
        if g.status == 'amateur' and s.tier <= 4:
            return (19, strength)
        if s.tier == 1 and g.tour in PREMIER_TOURS:
            # Premier events: playing rights first, home circuit next; the conditional categories are
            # reordered by this season's Premier money (a reshuffle), the exempt ones by world ranking
            r = self.rights.get(self.year, {}).get(g.id, ('conditional',))[0]
            cls = 2 * RIGHTS.index(r) + (0 if g.tour == s.tour else 1)
            if r in ('graduate', 'conditional'):
                m = self.money.get(('PREMIER', self.year), {})
                strength = (-m.get(g.id, 0.0), strength)
            else:
                strength = (0.0, strength)
            return (cls, strength, self.entry_ticket(g, s))
        if self._visitor(g.id, s):
            # a Premier member not in a Premier field: a bounded number of places alongside the residents
            # (PREMIER_VISITOR_SHARE; _bump keeps the bound), by world ranking
            return (10, strength, self.entry_ticket(g, s))
        if g.tour == s.tour:
            cls = 10
        elif s.category == 'national_open' and g.country == s.host_country:
            cls = 11
        elif mtier < s.tier:
            cls = 12
        elif mtier == s.tier:
            cls = 13
        else:
            cls = 14
        if s.tier == 4:
            strength = 0
        elif s.tier >= 5:
            # college and amateur fields rotate like team lineups: who has had fewest starts this
            # season goes first, with ranking a head start of a few starts — so the best play most,
            # and an unranked newcomer still gets starts (and with them, a ranking)
            starts = len(self.played.get(self.year, {}).get(g.id, ()))
            rank = self.am_pos.get(g.id)
            strength = starts + ROTATION_RANK_STARTS * (min(1.0, rank / 1500) if rank else 1.0)
        if s.tier == 1:
            strength = (0.0, strength)                      # comparable with the Premier members' keys
        return (cls, strength, self.entry_ticket(g, s))

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
        # intended schedules (owner): college golfers play a lot, other amateurs a little less; club
        # professionals have plenty of local events and choose a handful around their job
        if g.lifestyle == 'part_time' and g.status in ('pro', 'amateur'):
            return 6 if g.status == 'pro' else 8               # a job comes first
        if g.status == 'club_pro':
            return 12
        if g.tour.startswith('CO_'):
            return 24                                         # college events plus amateur events around them
        if g.status == 'amateur':
            return 16
        if g.tour in PREMIER_TOURS:                             # Premier players pick their spots
            return 15 + 8 * g.attrs['stamina'] / 100 - (4 if self.player_prestige(g.id) >= 65 else 0)
        return 19 + 8 * g.attrs['stamina'] / 100

    def bar(self, g):
        """The minimum event value worth playing for this golfer."""
        if g.status == 'club_pro':
            # their section events are all worth playing; the job decides how many: a bar near the
            # events' value keeps them close to their intended pace through the year (a low bar would
            # have every club pro play every early-season event, then sit out the rest of the year)
            return 19.0
        if g.lifestyle == 'part_time':
            return 12.0
        home = self.home_level.get(g.tour, 20.0)
        if g.tour in PREMIER_TOURS and self.rights_of(g.id, self.year) in ('graduate', 'conditional'):
            # uncertain access: a Challenger event is a real alternative when the Premier field is full
            home = self.home_level.get(CHALLENGER_BY_COUNTRY.get(g.country, CHALLENGER_BY_REGION[region_of(g)])[0], home)
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
            if venue_country == g.country:
                v += 8
            elif g.status == 'club_pro' and ed.series.tier == 8 and COUNTRIES[venue_country].region == region_of(g):
                # a section event over the border: a drive in Europe and North America, a flight elsewhere
                v += 9 if region_of(g) in CLUB_PRO_DRIVING_REGIONS else 4
            else:
                v -= 40
        if g.status == 'club_pro' and ed.series.tier == 8:
            v -= self.drive(g, self.lib.venues(ed.year)[ed.event_id][0].city) + self.club_diary(g, ed.year, ed.week)
        return v

    def club_diary(self, g, year, week):
        """How hard a week is to take off from a club professional's job (lessons, member events, the
        shop), against a typical week: a fixed draw per golfer and week, so club pros' free Mondays
        differ instead of the whole section choosing the same ones."""
        return -3.0 + 6.0 * (_seed(self.seed, 'diary', g.id, year, week) % 1000 / 1000)

    def drive(self, g, city):
        """How far a club professional's club is from a section event, against the circuit's typical
        trip (so positive is a longer drive than usual): least from their own town, little in their own
        state or province, a fixed draw per (hometown, venue) pair otherwise, standing in for distance
        (the geography has no coordinates). It only ranks venues: club pros near one venue favour it
        together, and the events of a big country do not all draw the same crowd from everywhere."""
        if city == g.hometown:
            return -3.0
        near = ', ' in city and city.split(', ', 1)[1] == g.hometown.split(', ', 1)[-1]
        u = _seed(self.seed, 'drive', g.hometown, city) % 1000 / 1000
        return -3.0 + 2.0 * u if near else -2.0 + 5.0 * u

    def golfer_week(self, g, year, week):
        """The parts of an event's value that depend only on the golfer and the week (worked out once
        per golfer, not once per event)."""
        weeks = self.played[year][g.id]
        streak = 0
        w = week - 1
        while w in weeks:
            streak += 1
            w -= 1
        # catching up or easing off against the season plan
        pace = self.target_events(g) * week / 52 - len(weeks)
        return {'streak': 5 * (streak - 1) ** 1.4 if streak >= 2 else None,
                'pace': max(-25.0, min(6.0, 3.5 * pace)),
                'before_major': week + 1 in MAJOR_WEEKS and self.wr_pos.get(g.id, 9999) <= 100,
                'after_major': week - 1 in MAJOR_WEEKS and week - 1 in weeks,
                # tired golfers rest; good course managers plan their rest better
                'tired': (8 + 10 * g.attrs["management"] / 100) * 2 * max(0.0, self.fatigue[g.id] - 0.1),
                'kept': self.prize_kept(g), 'unit': FIN.money_unit(self.funds(g, year))}

    def event_value(self, g, ed, week, rng, venue_country, cost=None, gw=None, base=None):
        s = ed.series
        gw = gw or self.golfer_week(g, ed.year, week)
        v = self.base_value(g, ed, venue_country) if base is None else base
        if gw['streak'] is not None:
            v -= gw['streak']
        v += gw['pace']
        if gw['before_major']:
            v -= 6                                           # resting before a major
        if gw['after_major']:
            v -= 8                                           # resting after a major
        v -= gw['tired']
        champs = self.champions.get(s.series_id)
        if champs and champs[-1][1] == g.id:
            v += 5                                           # defending champion
        if cost is None:
            cost = self.trip_cost(g, s, self.lib.venues(ed.year)[ed.event_id][0].city)
        v -= (cost - self.expected_prize(g, s) * gw['kept']) / gw['unit']
        return v + rng.gauss(0, 3)

    # ---- the week ------------------------------------------------------------------------------
    # The season's three steps. A whole season (run_year) and the weekly session (session.py) both use
    # exactly these, so a world advanced week by week is the same world as one run a season at a time.
    def start_year(self, year):
        """1 January: people refreshed, sponsor contracts, the staff market, playing rights."""
        self.year = year
        self.refresh_people(year)
        self.start_finances(year)

    def advance_week(self, year, week):
        """One week of the season (1-52)."""
        self.year = year
        self.run_week(year, week, [e for e in self.cal.editions(year) if e.week == week])

    def finish_year(self, year):
        """After week 52: the season's evidence, tour cards, careers, aging, new juniors."""
        self.year = year
        self.end_of_season(year)

    def run_year(self, year, progress=None):
        self.start_year(year)
        for week in range(1, 53):
            self.advance_week(year, week)
            if progress:
                progress(year, week)
        self.finish_year(year)

    def run_week(self, year, week, eds):
        rng = random.Random(_seed(self.seed, year, week, 'entries'))
        venues = self.lib.venues(year)
        busy = defaultdict(set)                              # gid -> days committed this week
        fields = {}                                          # event_id -> [per-site golfer lists]

        def commit(ed, ids_by_site, how='selected'):
            fields[ed.event_id] = ids_by_site
            for ids in ids_by_site:
                for gid in ids:
                    busy[gid] |= ed.series.day_set
                    self._week_entered.setdefault(gid, (ed.event_id, how))

        if self.development and (week - 1) % 4 == 0:
            self.plan_block(year, week)
        special = [e for e in eds if self.is_special(e.series)]
        regular = [e for e in eds if not self.is_special(e.series)]
        for ed in sorted(special, key=lambda e: (e.series.tier, e.series.series_id)):
            sites = self.special_field(ed, year, week, rng, busy)
            if sites is not None:
                # never two events on the same days, whatever a selection rule produced
                seen = set()
                sites = [[gid for gid in site if not (busy[gid] & ed.series.day_set) and not (gid in seen or seen.add(gid))]
                         for site in sites]
                self._default_routes(ed.series, year, sites)
                commit(ed, sites)
        # Regular events: golfers choose, events accept in priority order (deferred acceptance)
        if regular:
            self.regular_entries(regular, year, week, rng, venues, busy, commit)
        for e in eds:
            if e.event_id not in fields or not any(fields[e.event_id]):
                fields.pop(e.event_id, None)
                self.unheld[year].append(e.event_id)          # nobody entered: not held this year (recorded)
        self.play_week(year, week, [e for e in eds if e.event_id in fields], fields, venues)
        self.develop_week(year, week)
        self.record_access(year, week)
        self.weekly_finances(year, week)
        self.update_rankings(year, week)
        self.update_fame(year, week)
        self.snapshot_standings(year, week)
        self.update_fatigue(year, week)

    def is_special(self, s):
        return (s.kind in ('major', 'qualifying') or s.category in ('elite_amateur', 'national_amateur',
                                                                    'college_postseason', 'circuit_championship')
                or s.series_id == 'PT_PREMIER_TOUR_FINALS')

    def regular_entries(self, regular, year, week, rng, venues, busy, commit):
        # open amateur events (club, county, regional) take more entrants when more want to play
        cap = {ed.event_id: int(ed.series.field * (AMATEUR_OPEN_EXPANSION if ed.series.tier == 6 else 1))
               for ed in regular}
        country = {ed.event_id: CITY_BY_NAME[venues[ed.event_id][0].city].country for ed in regular}
        by_id = {ed.event_id: ed for ed in regular}
        city = {ed.event_id: venues[ed.event_id][0].city for ed in regular}
        prefs = {}
        open_to = {}                                         # who may enter which events this week (by kind)
        fees = {}                                            # (paid by school?, home country, event) -> cost
        bases = {}                                           # (home country, lifestyle, event) -> base value
        for g in self.world.golfers:
            if (not g.tour and g.status != 'club_pro') or g.id in self.injured or g.lifestyle == 'retired':
                continue
            if self.development and self.plans.get(g.id, {}).get(week, ('play',))[0] != 'play':
                continue                                     # a training or rest week in their plan
            key = (g.status, g.tour, g.country, self.wr_pos.get(g.id, 9999) <= 500,
                   self.am_pos.get(g.id, 9999) <= 25, self.am_pos.get(g.id, 9999) <= 300,
                   g.id if g.status == 'club_pro' else 0)      # club pros: their own diary and drives
            evs = open_to.get(key)
            if evs is None:
                evs = open_to[key] = [ed for ed in regular if self.eligible(g, ed.series, week)]
            if not evs:
                continue
            opts = []
            bar = self.bar(g)
            money = self.spendable(g, year)
            days = busy[g.id]
            k = self.staff.caddie(g.id)
            caddie_fee = k.weekly_fee if k is not None else 0.0
            gw = self.golfer_week(g, year, week)
            for ed in evs:
                if days & ed.series.day_set:
                    continue
                eid = ed.event_id
                fk = (g.tour.startswith('CO_'), g.status == 'club_pro', g.country, eid)
                fee = fees.get(fk)
                if fee is None:
                    fee = fees[fk] = FIN.event_cost(g, ed.series, city[eid])
                cost = fee + caddie_fee                      # = trip_cost: the can_afford rule
                if not (cost <= 0 or cost <= money):
                    continue                                 # cannot pay for the trip (school-paid trips cost 0)
                bk = (g.country, g.lifestyle, eid, g.id if g.status == 'club_pro' else 0)
                base = bases.get(bk)
                if base is None:
                    base = bases[bk] = self.base_value(g, ed, country[eid])
                v = self.event_value(g, ed, week, rng, country[eid], cost, gw, base)
                opts.append((v, eid))
            if not opts:
                continue
            opts.sort(reverse=True)
            want = [eid for v, eid in opts if v >= bar]
            spare = [eid for v, eid in opts if bar - 15 <= v < bar]   # would fill a place if asked
            prefs[g.id] = (want, spare)
        held = defaultdict(list)                             # event_id -> sorted [(priority, gid)]
        limits = {eid: self._limits(by_id[eid].series) for eid in by_id}   # (amateurs, visitors) allowed
        counts = defaultdict(lambda: [0, 0])                 # event_id -> [amateurs, visitors] held
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
            insort(held[eid], (self.priority(self.g[gid], s), gid))
            self._count(counts[eid], gid, s, 1)
            if len(held[eid]) > cap[eid] or self._over(counts[eid], limits[eid]):
                bumped = self._bump(held[eid], s, cap[eid], counts[eid], limits[eid])
                if bumped is not None:
                    free.append(bumped)
        placed = {gid for v in held.values() for _, gid in v}
        late_entries = defaultdict(list)                     # took a spare place below their own bar
        for eid, ed in by_id.items():
            s = ed.series
            if len(held[eid]) < cap[eid]:
                extra = sorted((self.priority(self.g[gid], s), gid) for gid, (_, spare) in prefs.items()
                               if gid not in placed and eid in spare)
                for pr, gid in extra:
                    if len(held[eid]) >= cap[eid]:
                        break
                    self._count(counts[eid], gid, s, 1)
                    if self._over(counts[eid], limits[eid]):
                        self._count(counts[eid], gid, s, -1)
                        continue
                    insort(held[eid], (pr, gid))
                    placed.add(gid)
                    late_entries[eid].append(gid)
            ids = [gid for _, gid in sorted(held[eid])]
            if ids:
                commit(ed, [ids], 'entry')
                late = set(late_entries.get(eid, ()))
                self.event_routes[year][eid] = {gid: self.entry_route(self.g[gid], s, gid in late) for gid in ids}
        stats = self.entry_stats[year]
        for gid, (want, _) in prefs.items():
            if not want:
                continue
            tour = by_id[want[0]].series.tour                # where they most wanted to play
            self._week_first[gid] = want[0]
            self.entry_wants[year][gid] += 1
            stats[tour]['wanted'] += 1
            if gid in placed:
                stats[tour]['placed'] += 1
            else:
                stats[tour]['shut out'] += 1
                self.entry_misses[year][gid] += 1           # wanted to play; every field they tried was full
                self._week_shut.add(gid)

    def _default_routes(self, s, year, sites):
        """Every selected field explains each entrant: fields whose rule records no routes of its own are
        given the rule's name, with the entrant's standing where a ranking decided it."""
        routes = self.entry_routes.setdefault((year, s.series_id), {})
        for site in sites:
            for gid in site:
                if gid in routes:
                    continue
                g = self.g[gid]
                if s.category == 'national_amateur':
                    routes[gid] = ('HOME AMATEUR' if g.country == s.host_country else 'REGIONAL AMATEUR') + \
                        (f' (amateur ranking {self.am_pos[gid]})' if gid in self.am_pos else ' (unranked)')
                elif s.category == 'elite_amateur':
                    routes[gid] = f'AMATEUR RANKING {self.am_pos[gid]}' if gid in self.am_pos else 'AMATEUR (unranked, by form)'
                elif s.category == 'college_postseason':
                    routes[gid] = 'COLLEGE POST-SEASON'
                elif s.category == 'q_school':
                    routes[gid] = 'Q-SCHOOL ENTRY'
                elif s.series_id == 'PT_PREMIER_TOUR_FINALS':
                    routes[gid] = 'PREMIER POINTS LIST'
                elif s.kind == 'qualifying':
                    routes[gid] = 'QUALIFYING ENTRY'
                else:
                    routes[gid] = 'SELECTED'

    def entry_route(self, g, s, late=False):
        """How a golfer got into a regular event, with their status at entry (kept in history)."""
        if s.tier == 1 and g.tour in PREMIER_TOURS:
            r = f'PREMIER {self.rights_of(g.id, self.year).upper() or "MEMBER"}'
        elif self._visitor(g.id, s):
            r = 'PREMIER MEMBER (visitor places)'
        elif g.status == 'amateur' and s.tier <= 4:
            r = 'AMATEUR INVITATION'
        elif s.tier == 5:
            r = 'COLLEGE LINEUP'
        elif s.tier == 6:
            r = 'OPEN AMATEUR ENTRY'
        elif s.tier == 8:
            r = 'CLUB PROFESSIONAL'
        elif g.tour == s.tour:
            r = 'MEMBER' + (' (draw)' if s.tier == 4 else '')
        elif s.category == 'national_open' and g.country == s.host_country:
            r = 'HOME PLAYER'
        else:
            r = f'{TOUR_BY_KEY[g.tour].name.upper()} MEMBER' if g.tour in TOUR_BY_KEY else 'OPEN ENTRY'
        return r + (' — late entry' if late else '')

    def _visitor(self, gid, s):
        """A Premier member in a Challenger tour's own event (national opens are open to all pros)."""
        return s.tier == 2 and s.category != 'national_open' and self.g[gid].tour in PREMIER_TOURS

    def _limits(self, s):
        """(amateurs, Premier visitors) an event takes at most: sponsor invitations for amateurs in
        professional events (AMATEUR_CAP) and the visitor places in Challenger events; None = no limit."""
        visitors = int(PREMIER_VISITOR_SHARE * s.field) if s.tier == 2 and s.category != 'national_open' else None
        return AMATEUR_CAP.get(s.tier), visitors

    def _count(self, c, gid, s, d):
        if self.g[gid].status == 'amateur':
            c[0] += d
        if self._visitor(gid, s):
            c[1] += d

    @staticmethod
    def _over(c, limits):
        return (limits[0] is not None and c[0] > limits[0]) or (limits[1] is not None and c[1] > limits[1])

    def _bump(self, rows, s, capacity, c, limits):
        """Who loses their place when an event is over a limit: the lowest-priority amateur over the
        sponsor-invitation limit, the lowest-ranked Premier visitor over the visitor places, or else the
        lowest priority entrant over the field size. `rows` is sorted; `c` counts amateurs and visitors."""
        if limits[0] is not None and c[0] > limits[0]:
            i = max(i for i, (_, gid) in enumerate(rows) if self.g[gid].status == 'amateur')
        elif limits[1] is not None and c[1] > limits[1]:
            i = max(i for i, (_, gid) in enumerate(rows) if self._visitor(gid, s))
        elif len(rows) > capacity:
            i = len(rows) - 1
        else:
            return None
        gid = rows.pop(i)[1]
        self._count(c, gid, s, -1)
        return gid

    # ---- special fields --------------------------------------------------------------------------
    def available(self, gid, s, busy):
        return not (busy[gid] & s.day_set) and gid not in self.injured and self.g[gid].lifestyle != 'retired'

    def observed_form(self, gid):
        """Strokes per round against the field over this and last season (lower is better): what
        selectors can actually see. Golfers with no recorded rounds sort last."""
        rounds = vs = 0.0
        for y in (self.year, self.year - 1):
            ps = self.pstats.get(y, {}).get(gid)
            if ps:
                rounds += ps['rounds']
                vs += ps['vs_field']
        return vs / rounds if rounds else 99.0

    def ranked_amateurs(self, pred):
        ams = [g for g in self.world.golfers if g.status == 'amateur' and pred(g)]
        return sorted(ams, key=lambda g: (self.am_pos.get(g.id, 99999), self.observed_form(g.id), g.id))

    def special_field(self, ed, year, week, rng, busy):
        """Fields chosen by the event: majors, invitations, championships and qualifiers. Everyone in
        them pays their own way under the same rule as a regular entry (can_afford: school-paid trips
        are free); a golfer who cannot pay declines (recorded in `declined`) and the next in line, or
        the next alternate, takes the place."""
        s = ed.series
        sid = s.series_id
        city0 = self.lib.venues(year)[ed.event_id][0].city
        pays = lambda g: self.can_afford(g, s, city0, self.spendable(g, year))
        free = lambda g: self.available(g.id, s, busy)
        if s.kind == 'qualifying' or sid == 'CLUB_PRO_SECTIONALS':   # entrants decide, and pay, for themselves
            can_go = free
            free = lambda g: can_go(g) and pays(g)

        def invite(ranked, n):
            """The first `n` of `ranked` (golfers, in order) who can pay their way."""
            take = []
            for g in ranked:
                if len(take) >= n:
                    break
                if pays(g):
                    take.append(g.id)
                else:
                    self.declined[year][g.id].append(sid)
            return take
        if s.kind == 'major':
            return [self.major_field(sid, year, week, pays)]
        if sid == 'PT_PREMIER_TOUR_FINALS':
            rows = self.ctx.standing('PREMIER', year, week - 1)
            return [invite([self.g[gid] for gid in rows if self.g[gid].status == 'pro' and gid not in self.injured],
                           s.field)]
        if sid == 'USA_AMATEUR_QUALIFYING':
            return self.usa_amateur_qualifying(ed, year, week, free)
        if sid == 'USA_AMATEUR':
            return self.usa_amateur_field(ed, year, week, free, invite)
        if s.category == 'elite_amateur':
            regions = ELITE_AMATEUR_REGIONS.get(sid)
            pred = (lambda g: free(g) and region_of(g) in regions) if regions else (lambda g: free(g))
            if s.eligibility == 'mid_amateur':
                pred = lambda g: free(g) and g.age(year) >= 25
            return [invite(self.ranked_amateurs(pred), s.field)]
        if s.category == 'national_amateur':
            take = invite(self.ranked_amateurs(lambda g: free(g) and g.country == s.host_country), s.field)
            take += invite(self.ranked_amateurs(lambda g: free(g) and g.country != s.host_country and
                                                region_of(g) == COUNTRIES[s.host_country].region),
                           max(0, min(s.field - len(take), s.field // 4)))
            return [take]
        if s.category == 'circuit_championship':
            return self.circuit_championship(ed, year, week, free, invite)
        if s.category == 'college_postseason':                  # the school pays: never out of reach
            return self.college_postseason(ed, year, lambda g: free(g) and pays(g))
        if sid == 'CLUB_PRO_SECTIONALS':
            return self.club_pro_sectionals(ed, year, rng, free)
        if sid == 'CLUB_PRO_CHAMPIONSHIP':
            return self.club_pro_championship(ed, year, free)
        if s.category == 'q_school':
            return self.qschool_field(ed, year, week, free)
        if s.category == 'qualifier':
            return self.qualifier_field(ed, year, week, rng, free)
        return None

    # ---- circuit championships ----------------------------------------------------------------------
    CHAMPION_YEARS = 3              # a circuit champion is exempt into the next three editions

    def circuit_order(self, s, year, week, pool):
        """A circuit's order of merit as it stood after last week: prize money on the circuit (ties: world
        ranking, then id); amateur circuits by amateur ranking (ties: observed form, then id) — amateur
        standing never depends on prize money."""
        if s.tier == 6:
            return sorted(pool, key=lambda g: (self.am_pos.get(g.id, 99999), self.observed_form(g.id), g.id))
        m = self.money[(s.tour, year)]
        return sorted(pool, key=lambda g: self.standing_key(m, g.id))

    def circuit_championship(self, ed, year, week, free, invite):
        """A circuit's season-ending championship (see docs/CIRCUIT_FLAGSHIPS.md): the champions of its
        last CHAMPION_YEARS editions who are still on the circuit, then its order of merit as it stood
        after last week, to the field size. Members (amateur series: the series' amateurs; club-pro
        circuits: the region's club professionals) only; anyone injured, busy or unable to pay is passed
        over for the next on the list (declines recorded). Each entrant's route is recorded."""
        s = ed.series
        if s.tier == 6:
            countries = {c for c, _ in TOUR_BY_KEY[s.tour].countries}
            pool = [g for g in self.world.golfers if g.status == 'amateur' and g.lifestyle != 'retired'
                    and (g.tour == s.tour or g.country in countries) and free(g)]
        elif s.tier == 8:
            pool = [g for g in self.world.golfers if g.lifestyle != 'retired' and self.eligible(g, s, week) and free(g)]
        elif s.tier == 4:                                    # open circuits: everyone who played them this season
            m = self.money[(s.tour, year)]
            pool = [g for g in self.world.golfers if g.lifestyle != 'retired' and g.status == 'pro' and free(g)
                    and (g.tour == s.tour or m.get(g.id, 0) > 0)]
        else:
            pool = [g for g in self.world.golfers if g.tour == s.tour and g.lifestyle != 'retired' and free(g)]
        in_pool = {g.id for g in pool}
        past = [gid for y, gid, _ in reversed(self.champions.get(s.series_id, []))
                if y >= year - self.CHAMPION_YEARS and gid in in_pool]
        order = self.circuit_order(s, year, week, pool)
        ranked = list(dict.fromkeys(past + [g.id for g in order]))
        take = invite([self.g[gid] for gid in ranked], s.field)
        pos = {g.id: i + 1 for i, g in enumerate(order)}
        self.entry_routes[(year, s.series_id)] = {gid: 'PAST CHAMPION' if gid in past else f'ORDER OF MERIT {pos[gid]}'
                                                  for gid in take}
        return [take]

    # ---- the USA Amateur: exemptions, then open qualifying --------------------------------------------
    USA_AMATEUR_EXEMPT = 64          # leading amateurs exempt from qualifying (amateur ranking)
    USA_AMATEUR_ENTRY_STARTS = 3     # the entry standard: an active competitive record this season

    def usa_amateur_exempt(self, year):
        """Exempt from qualifying, deduplicated, in order: the last three champions and last year's
        runner-up (still amateurs), then the top USA_AMATEUR_EXEMPT of the amateur ranking."""
        out = {}
        for y, gid, _ in reversed(self.champions.get('USA_AMATEUR', [])):
            if y >= year - 3 and self.g[gid].status == 'amateur' and self.g[gid].lifestyle != 'retired':
                out.setdefault(gid, f'USA AMATEUR CHAMPION {y}')
        for gid, pos in self.ctx.finishers('USA_AMATEUR', year - 1):
            if pos == 2 and self.g[gid].status == 'amateur':
                out.setdefault(gid, f'RUNNER-UP {year - 1}')
        ranked = [g for g in self.world.golfers if g.status == 'amateur' and g.lifestyle != 'retired'
                  and g.id in self.am_pos]
        ranked.sort(key=lambda g: (self.am_pos[g.id], g.id))
        for g in ranked[:self.USA_AMATEUR_EXEMPT]:
            out.setdefault(g.id, f'AMATEUR RANKING {self.am_pos[g.id]}')
        return out

    def usa_amateur_qualifying(self, ed, year, week, free):
        """Open to any amateur who is not exempt and meets the entry standard (USA_AMATEUR_ENTRY_STARTS
        events this season — a record of play, not a ranking, so a newcomer can enter), living in North
        America or travelling from abroad with a world amateur ranking in the top 300; places by a fair
        draw when oversubscribed; split round the sites."""
        s = ed.series
        exempt = self.usa_amateur_exempt(year)
        pool = [g for g in self.world.golfers if g.status == 'amateur' and g.lifestyle != 'retired'
                and g.id not in exempt and free(g) and len(self.played[year][g.id]) >= self.USA_AMATEUR_ENTRY_STARTS
                and (region_of(g) == 'North America' or self.am_pos.get(g.id, 99999) <= 300)]
        pool.sort(key=lambda g: self.entry_ticket(g, s))
        ids = [g.id for g in pool[:s.field * s.sites]]
        self.entry_routes[(year, s.series_id)] = {gid: 'OPEN QUALIFYING ENTRY' for gid in ids}
        return [ids[i::s.sites] for i in range(s.sites)]

    def usa_amateur_field(self, ed, year, week, free, invite):
        """Exempt players first (declines recorded), then qualifiers: each qualifying site's places in
        proportion to its entrants, to its best finishers; ties for the last place go by the recorded
        finishing order (countback). A qualifier who cannot take up the place is replaced by the next
        finisher at that site (an alternate)."""
        s = ed.series
        exempt = self.usa_amateur_exempt(year)
        take = invite([self.g[gid] for gid in exempt if free(self.g[gid])], s.field)
        routes = {gid: exempt[gid] for gid in take}
        sites = [[gid for gid, pos in rows if pos is not None]
                 for _, rows in sorted(self.ctx.results.get(('USA_AMATEUR_QUALIFYING', year), {}).items())]
        total = sum(len(x) for x in sites)
        spots = s.field - len(take)
        for k, rows in enumerate(sites):
            n = round(spots * len(rows) / total) if total else 0
            got = skipped = 0
            for i, gid in enumerate(rows):
                if got >= n or len(routes) >= s.field:
                    break
                if gid in routes or not free(self.g[gid]):
                    skipped += gid not in routes
                    continue
                if not self.can_afford(self.g[gid], s, self.lib.venues(year)[ed.event_id][0].city,
                                       self.spendable(self.g[gid], year)):
                    self.declined[year][gid].append(s.series_id)
                    skipped += 1
                    continue
                routes[gid] = f'QUALIFYING SITE {k + 1}' + (' (alternate)' if i >= n and skipped else '')
                got += 1
        self.entry_routes[(year, s.series_id)] = routes
        return [list(routes)]

    # ---- majors: every entrant has a recorded route ------------------------------------------------
    INAUGURAL_MASTERS = 90           # the world's first Masters has no past champions or results to draw on

    def major_field(self, sid, year, week, pays=lambda g: True):
        """The major's field from its qualification routes. Each entrant's route is recorded in
        `entry_routes`. Golfers who are injured or retired withdraw and the next alternates (recorded
        as 'ALT') take their places; an invitation-only event without alternates simply plays with a
        smaller field. The only exception is explicit and limited to the world's first season, when
        no past results exist: the Tour Masters then invites the best of the seeded world ranking
        (route 'INIT', 'Inaugural invitation'). Qualified golfers who cannot pay the trip decline
        (`declined`) and alternates replace them in the same way."""
        f = Q.build_field(sid, year, self.ctx)
        self.stage_log[(year, sid, 'field')] = f
        can_play = lambda gid: gid in self.g and gid not in self.injured and self.g[gid].lifestyle != 'retired'

        def ok(gid):
            if not can_play(gid):
                return False
            if not pays(self.g[gid]):
                self.declined[year][gid].append(sid)
                return False
            return True
        routes = {}
        for e in f.entries:
            if ok(e.golfer_id):
                routes[e.golfer_id] = e.primary
        withdrawn = len(f.entries) - len(routes)
        for gid in f.alternates:
            if withdrawn <= 0:
                break
            if ok(gid) and gid not in routes:
                routes[gid] = 'ALT'
                withdrawn -= 1
        if year == self.first_year and sid == 'TOUR_MASTERS':
            for gid in self.ctx.ranking(year, week - 1):
                if len(routes) >= self.INAUGURAL_MASTERS:
                    break
                if ok(gid) and gid not in routes:
                    routes[gid] = 'INIT'
        self.entry_routes[(year, sid)] = routes
        return list(routes)

    # ---- club professionals: sectional qualifying, then their championship --------------------------
    def club_pro_sectionals(self, ed, year, rng, free):
        """36-hole sectionals, open to club professionals who choose to (and can afford to) enter:
        most home-country club pros do, a few from abroad travel. Played and recorded like any event."""
        s = ed.series
        keen = lambda g: 0.9 if g.country == s.host_country else 0.4 if region_of(g) in QS_AMERICAS else 0.08
        ids = [g.id for g in sorted(self.world.golfers, key=lambda x: x.id)
               if g.status == 'club_pro' and free(g) and rng.random() < keen(g)]
        rng.shuffle(ids)
        ids = ids[:s.field * s.sites]
        self.entry_routes[(year, s.series_id)] = {gid: 'ENTRY' for gid in ids}
        return [site for site in (ids[i::s.sites] for i in range(s.sites)) if site]

    def club_pro_championship(self, ed, year, free):
        """The field comes from the sectionals: each site's places in proportion to its entrants,
        to its best finishers (ties broken by the recorded finishing order)."""
        s = ed.series
        sites = [[gid for gid, pos in rows if pos is not None]
                 for _, rows in sorted(self.ctx.results.get(('CLUB_PRO_SECTIONALS', year), {}).items())]
        total = sum(len(x) for x in sites)
        routes = {}
        if total:
            for k, rows in enumerate(sites):
                spots = round(s.field * len(rows) / total)
                taken = 0
                for gid in rows:
                    if taken >= spots or len(routes) >= s.field:
                        break
                    if free(self.g[gid]) and gid not in routes:
                        routes[gid] = f'SECTIONAL {k + 1}'
                        taken += 1
        self.entry_routes[(year, s.series_id)] = routes
        return [list(routes)]

    def college_postseason(self, ed, year, free):
        s = ed.series
        sid = s.series_id
        d1 = [g for g in self.world.golfers if g.tour == 'CO_US_D1' and free(g)]
        rank = lambda gs: sorted(gs, key=lambda g: (self.am_pos.get(g.id, 99999), self.observed_form(g.id), g.id))
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
        members.sort(key=lambda g: self.standing_key(m, g.id))
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
        ids = [gid for gid in dict.fromkeys(ids) if free(self.g[gid])][:n]   # advanced players may be elsewhere
        log[(year, sid)] = ids
        return split(ids) if s.sites > 1 else [ids]

    def _money_rank_premier(self, year):
        m = self.money[('PREMIER', year)]
        members = [g for g in self.world.golfers if g.tour in PREMIER_TOURS]
        members.sort(key=lambda g: self.standing_key(m, g.id))
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
            # who was in each golfer's team this week (kept with the result: history never relies on
            # later assignments)
            self._teams[ed.event_id] = {gid: self.staff.team(gid) for ids in fields[ed.event_id] for gid in ids}
            for site, ids in enumerate(fields[ed.event_id]):
                v = venues[ed.event_id][min(site, len(venues[ed.event_id]) - 1)]
                course = self.lib.course(v)
                fk = course.familiarity_key
                tasks.append({'event_id': ed.event_id, 'site': site, 'course': course,
                              'golfers': [_for_course(self.g[gid], fk) for gid in ids], 'match_play': s.match_play,
                              'caddies': [_for_course(self.staff.bag(self.g[gid], year), fk) for gid in ids],
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

    def __getstate__(self):
        """Saved without the worker pool, and without the standard course library (rebuilt identically
        from its seed on loading; 40% of a fresh save)."""
        state = self.__dict__.copy()
        state.pop('_pool', None)
        if state.get('lib') is default_library():
            state['lib'] = 'default'
            state.pop('cal', None)
        return state

    def __setstate__(self, state):
        state.setdefault('new_pros_added', {})              # saves from before new professionals arrived
        if state.get('lib') == 'default':
            state['lib'] = default_library()
            state['cal'] = state['lib'].calendar
        self.__dict__.update(state)

    def close(self):
        if hasattr(self, '_pool'):
            self._pool.shutdown()
            del self._pool

    def _moments_from(self, rec, aces, albs, year, week, event_id, layout):
        """Holes-in-one and albatrosses just added to a layout's records become the season's moments."""
        for kind, rows, before in (('hole-in-one', rec.aces, aces), ('albatross', rec.albatrosses, albs)):
            for hole, _, _, _, stage, gid in rows[before:]:
                self.moments[year].append({'kind': kind, 'person': gid, 'event': event_id, 'week': week,
                                           'layout': layout, 'hole': hole, 'stage': stage})

    def record_event(self, ed, year, week, site_out, venue_list):
        s = ed.series
        sid = s.series_id
        p = self.event_prestige[sid]
        res = EventResult(ed.event_id, sid, year, week,
                          [(v.course_id, v.layout, v.city) for v in venue_list], [], p,
                          team=self._teams.pop(ed.event_id, {}))
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
            prior = rec.rounds                               # rounds on this layout before this event
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
                aces, albs, cr = len(rec.aces), len(rec.albatrosses), rec.course_record
                mark = Mark(score, score - course.par, self.g[gid].name, ed.event_id, year, week, rd, s.tier, gid)
                rec.add_round(mark, holes, pars)
                self._moments_from(rec, aces, albs, year, week, ed.event_id, course.layout_id)
                if prior >= COURSE_RECORD_ROUNDS and cr is not None and score < cr.score:
                    self.moments[year].append({'kind': 'course record',
                                               'person': gid, 'event': ed.event_id, 'week': week, 'layout': course.layout_id,
                                               'score': score, 'to_par': score - course.par, 'round': rd,
                                               'previous': cr.score, 'previous_holder': cr.golfer_id})
                self.holes_played[year] += len(holes)
                self.g[gid].familiarity[course.familiarity_key] = self.g[gid].familiarity.get(course.familiarity_key, 0) + 1
                k = self.staff.caddie(gid)
                if k is not None:                            # caddies learn the course too
                    k.familiarity[course.familiarity_key] = k.familiarity.get(course.familiarity_key, 0) + 1
            for gid, idx, strokes, stage in o['holes']:
                aces, albs = len(rec.aces), len(rec.albatrosses)
                rec.add_hole(idx, strokes, pars[idx], self.g[gid].name, ed.event_id, year, stage, gid)
                self._moments_from(rec, aces, albs, year, week, ed.event_id, course.layout_id)
                self.holes_played[year] += 1
            if o['playoff'] and finish and site == 0:
                losers = [gid for gid, pos, total in finish if pos == 2 and total == finish[0][2]]
                self.moments[year].append({'kind': 'playoff', 'person': finish[0][0], 'event': ed.event_id, 'week': week,
                                           'layout': course.layout_id, 'holes': o['playoff'], 'beat': losers})
            rounds = Counter(gid for gid, *_ in o['rounds'])
            fk = course.familiarity_key
            for gid, n in Counter(gid for gid, *_ in o['holes']).items():
                rounds[gid] += n / 18
                # match-play and playoff holes teach the course too (in rounds' worth)
                g_ = self.g[gid]
                g_.familiarity[fk] = g_.familiarity.get(fk, 0) + n / 18
                k = self.staff.caddie(gid)
                if k is not None:
                    k.familiarity[fk] = k.familiarity.get(fk, 0) + n / 18
            for gid, n in rounds.items():
                self.season_rounds[year][gid] += n                   # competitive experience
                k = self.staff.caddie(gid)
                if k is not None:
                    k.rounds_worked += n
                    self.staff.rel.add_work('caddie', gid, n, year)     # time on the bag together
            host_region = COUNTRIES[CITY_BY_NAME[v.city].country].region
            for gid, n in rounds.items():
                self._week_load[gid] += self.load(self.g[gid], n, region_of(self.g[gid]) != host_region, year)
                self._week_event[gid] = ed.event_id
                self.week_rounds[gid] += n
            for gid, _, _ in finish:
                cost = FIN.event_cost(self.g[gid], s, v.city)
                if cost:
                    self.spend(self.g[gid], year, 'events', cost)
                else:
                    self.school_trips[year][gid] += 1                    # the payer: their school
                k = self.staff.caddie(gid)
                if k is not None:
                    self.pay_staff(self.g[gid], year, 'caddie', k, k.weekly_fee)
                    k.weeks_worked += 1
            if s.kind != 'qualifying' and finish and finish[0][1] == 1:
                w = finish[0][0]
                tp = '' if finish[0][2] is None else f' at {finish[0][2] - course.par * s.rounds:+d}'
                self.log(w, year, week, f'Won the {s.name}{tp} ({self.lib.sites[v.course_id]["name"]})')
            if s.rounds and finish and finish[0][2] is not None and site == 0:
                win_total = finish[0][2]
                self.champions[sid].append((year, finish[0][0], win_total - course.par * s.rounds))
            elif s.match_play and site == 0:
                self.champions[sid].append((year, res.winner(0), None))
            won = self.pay_out(s, finish, year)
            if s.purse:
                for gid, pos, _ in finish:
                    if self.g[gid].status == 'pro':           # learn what this player tends to win
                        old = self.prize_share.get(gid, FIN.PRIOR_PRIZE_SHARE)
                        self.prize_share[gid] = 0.8 * old + 0.2 * won.get(gid, 0.0) / s.purse
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
            elif f and self.week_activity.get(g.id) == 'work':
                f *= 0.8
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
        """Pay the purse to professionals who made the cut, by the payout table (ties share the
        positions' money). Amateurs take nothing; the professionals behind them move up the table.

        The table is sized by the event's intended paid places (the cut within the intended field, or
        every starter in a no-cut event), not by however many professionals happen to be paid: when
        amateurs, a small cut or an undersized field leave places without a professional to fill them,
        the money for those places is not paid out (it is recorded in `unpaid`) rather than inflating
        everyone else's share.
        Returns {gid: prize}."""
        won = {}
        if not s.purse:
            return won
        paid = [(gid, pos) for gid, pos, _ in finish if pos is not None and self.g[gid].status != 'amateur']
        # cut events pay their intended places (the cut, within the intended field size) even when fewer
        # start; a no-cut event pays every starter
        places = min(s.cut_top, s.field) if s.cut_top else len(finish)
        shares = PR.payout_shares(max(places, len(paid)))
        i = 0
        while i < len(paid):
            pos = paid[i][1]
            j = i
            while j < len(paid) and paid[j][1] == pos:
                j += 1
            each = sum(shares[i:j]) / (j - i) * s.purse
            for gid, _ in paid[i:j]:
                g = self.g[gid]
                won[gid] = each
                self.earnings[year][gid] += each
                self.career_prize[gid] += each
                self.earn(g, year, 'prize', each)
                k = self.staff.caddie(gid)
                if k is not None:
                    self.pay_staff(g, year, 'caddie_share', k, FIN.CADDIE_SHARE * each)
                if self.staff.deal.get(gid) == 'share':      # the coach who approached them
                    self.pay_staff(g, year, 'coach_share', self.staff.coach(gid), ST.SCOUT_SHARE * each)
                if g.backer:                                  # the backers' share
                    self.spend(g, year, 'backer_share', FIN.BACKER_SHARE * each)
                keys = [s.tour] if s.tour in TOUR_BY_KEY else []
                if s.kind == 'major':
                    keys = list(PREMIER_TOURS)
                if s.tier <= 1:
                    keys.append('PREMIER')
                for k in keys:
                    self.money[(k, year)][gid] += each
            i = j
        self.unpaid[year] += s.purse - sum(won.values())
        return won

    def snapshot_standings(self, year, week):
        for (tour, y), m in self.money.items():
            if y == year:
                self.ctx.standings[(tour, year, week)] = sorted(m, key=lambda gid: self.standing_key(m, gid))

    # ---- end of season -----------------------------------------------------------------------------
    def prune_history(self, year):
        """Weekly detail older than last season leaves the live simulation (the archive keeps it), so what
        the simulation holds week by week does not grow with the years."""
        for d in (self.week_access, self.max_denied_run, self.access_log, self.event_routes, self.denied_behind):
            for y in [y for y in d if y < year - 1]:
                del d[y]
        # weekly ranking and in-season standings snapshots: the rules look back at most a season (the
        # archive keeps each week's top of the rankings); final standings and every result stay
        for table in (self.ctx.world_rankings, self.ctx.amateur_rankings):
            for k in [k for k in table if k[0] < year - 1]:
                del table[k]
        for k in [k for k in self.ctx.standings if len(k) == 3 and k[1] < year - 1]:
            del self.ctx.standings[k]
        # Per-season working tables: the rules read this season and last at most; older seasons are in the
        # archive. Results older than last season keep only their winners (champions, exemptions and the
        # Masters' lifetime winners are the only rules that look further back).
        old = lambda y: y < year - 1
        for d in (self.earnings, self.played, self.pstats, self.ledgers, self.season_rounds, self.entry_wants,
                  self.entry_misses, self.entry_stats, self.declined, self.school_trips, self.activity_counts,
                  self.block_flags, self.cash_start, self.overall_start, self.rank_start, self.am_start,
                  self.staff_receipts, self.injuries, self.card_log, self.career_counts, self.transitions,
                  self.assignments, self.staff_year, self.unheld, self.rights, self.card_reasons, self.snapshots,
                  self.juniors_added, self.new_pros_added, self.stats, self.moments):
            for y in [y for y in d if isinstance(y, int) and old(y)]:
                del d[y]
        for k in [k for k in self.money if old(k[1])]:
            del self.money[k]
        for k in [k for k in self.entry_routes if old(k[0])]:
            del self.entry_routes[k]
        for k in [k for k in self.stage_log if old(k[0])]:
            del self.stage_log[k]
        for eid in [eid for eid, r in self.results.items() if old(r.year)]:
            del self.results[eid]
        for (sid, y), sites in self.ctx.results.items():
            if old(y):
                for site, rows in sites.items():
                    if any(pos != 1 for _, pos in rows):
                        sites[site] = [(gid, pos) for gid, pos in rows if pos == 1]

    def end_of_season(self, year):
        self.prune_history(year)
        for (tour, y), m in list(self.money.items()):
            if y != year:
                continue
            if tour == 'PREMIER':
                members = [g.id for g in self.world.golfers if g.tour in PREMIER_TOURS]
            else:
                members = [g.id for g in self.world.golfers if g.tour == tour]
            order = sorted(set(members) | set(m), key=lambda gid: self.standing_key(m, gid))
            self.ctx.standings[(tour, year)] = order
        for t in TOUR_BY_KEY:
            if (t, year) not in self.ctx.standings:
                self.ctx.standings[(t, year)] = []
        for gid in self.legacy:
            self.legacy[gid] *= PR.LEGACY_DECAY
        self.snapshots[year] = snap = self.season_snapshot(year)
        from .cards import apply_cards
        apply_cards(self, year)
        for gid, row in snap.items():                        # promotion: a separate fact from money rank
            g = self.g[gid]
            new_tier = TOUR_BY_KEY[g.tour].tier if g.tour in TOUR_BY_KEY else 9
            row['next_tour'] = g.tour
            row['promoted'] = new_tier < row['tier']
            row['demoted'] = new_tier > row['tier'] and row['tier'] <= 4
        for gid, frm, to, why in self.card_log[year]:
            self.log(gid, year, 53, f'{TOUR_BY_KEY[frm].name if frm in TOUR_BY_KEY else "—"} → {TOUR_BY_KEY[to].name} ({why})')
        if self.development:
            from . import careers
            self.career_counts[year] = careers.decide(self, year, snap)
            rng = random.Random(_seed(self.seed, year, 'aging'))
            for g in self.world.golfers:
                if g.lifestyle != 'retired':
                    D.age_year(g, g.age(year + 1), rng, D.experience_factor(self.season_rounds[year][g.id]))
            self.juniors_added[year + 1] = careers.add_juniors(self, year + 1)
            self.new_pros_added[year + 1] = careers.add_new_professionals(self, year + 1)
            for g in self.world.golfers:
                self.fatigue[g.id] = g.fatigue = 0.0         # the off-season rests everyone
        ST.end_of_season(self, year, snap)                   # coaches' and caddies' year

    def start_finances(self, year):
        """Sponsor contracts for the season, from each professional's prestige at its start
        (paid weekly), and the cash each golfer starts the year with (for reconciliation)."""
        self.contracts = {g.id: PR.endorsements(self.player_prestige(g.id)) for g in self.world.golfers
                          if g.status == 'pro' and g.lifestyle != 'retired'}
        self.rank_start[year] = dict(self.wr_pos)
        self.am_start[year] = dict(self.am_pos)
        for g in self.world.golfers:                         # backers put up this season's money
            if g.backer and g.lifestyle != 'retired':
                g.backing = max(g.backing, g.backer)
        self.cash_start[year] = {g.id: g.cash for g in self.world.golfers}
        self.premier_rights(year)
        self.overall_start[year] = {g.id: g.overall for g in self.world.golfers if g.lifestyle != 'retired'}
        ST.start_of_season(self, year)                       # coaches scout, golfers hire coaches and caddies
        self.assignments[year] = {'coach_of': dict(self.staff.coach_of), 'deal': dict(self.staff.deal),
                                  'caddie_of': dict(self.staff.caddie_of)}

    def premier_rights(self, year):
        """Each Premier member's playing rights for the season (RIGHTS), with the reason, fixed on
        1 January from facts already recorded: exempt = a Premier event won this season or last, or a
        major in the last five; full = top FULL_STATUS on last season's Premier money list; graduate =
        earned the card from a Challenger tour or a Q-School; conditional = everyone else who kept a
        card. The world's first season has no money list: members are seeded by world ranking."""
        rights = self.rights[year] = {}
        members = [g for g in self.world.golfers if g.tour in PREMIER_TOURS and g.lifestyle == 'full_time']
        exempt = {}
        for (sid, y), _ in self.ctx.results.items():
            s = self.cal.by_id.get(sid)
            w = self.ctx.winner(sid, y) if s else None
            if w is None:
                continue
            if s.kind == 'major' and year - 5 <= y < year:
                exempt[w] = f'won the {y} {s.name}'
            elif s.tier == 1 and year - 2 <= y < year and w not in exempt:
                exempt[w] = f'won the {y} {s.name}'
        reasons = self.card_reasons.get(year, {})
        m = self.money.get(('PREMIER', year - 1))
        if m is not None:
            ranked = sorted((g.id for g in self.world.golfers if g.id in m), key=lambda gid: self.standing_key(m, gid))
            pos = {gid: i + 1 for i, gid in enumerate(ranked)}
        else:
            ranked = sorted((g.id for g in members), key=lambda gid: self.wr_pos.get(gid, 10 ** 6))
            pos = {gid: i + 1 for i, gid in enumerate(ranked)}
        for g in members:
            p = pos.get(g.id)
            why = reasons.get(g.id, '')
            if g.id in exempt:
                rights[g.id] = ('exempt', exempt[g.id])
            elif p is not None and p <= FULL_STATUS:
                rights[g.id] = ('full', f'{p} on the {year - 1} Premier money list' if m is not None
                                else f'{p} among Premier members by world ranking (first season)')
            elif m is not None and ('Challenger' in why or 'Tour Americas' in why or 'Q-School' in why
                                    or why.startswith('top ') and 'Premier' not in why):
                rights[g.id] = ('graduate', why)
            else:
                rights[g.id] = ('conditional', f'{p} on the {year - 1} Premier money list' if m is not None and p
                                else why or 'no money-list place')

    def rights_of(self, gid, year):
        r = self.rights.get(year, {}).get(gid)
        return r[0] if r else ''

    def standing_key(self, money, gid):
        """Order on a money list: more money first; ties broken by world ranking, then by id, so the
        order never depends on how the population happens to be listed."""
        return (-money.get(gid, 0.0), self.wr_pos.get(gid, 10 ** 6), gid)

    def season_snapshot(self, year):
        """Evidence from the completed season, taken BEFORE tour cards change anyone's membership.

        Per golfer: the tour they played the season on, events, wins, top-3 / top-10 finishes, made
        cuts, prize money, money on their own tour and their rank on it (ties share the average
        rank), world / amateur ranking at the start and end of the season, injury weeks, and the
        year's money (net). Promotion is added after the cards, as a separate fact."""
        snap = {}
        for g in self.world.golfers:
            if g.lifestyle == 'retired':
                continue
            led = self.ledgers[year].get(g.id)
            snap[g.id] = {'tour': g.tour, 'tier': TOUR_BY_KEY[g.tour].tier if g.tour in TOUR_BY_KEY else 9,
                          'status': g.status, 'lifestyle': g.lifestyle, 'events': len(self.played[year][g.id]),
                          'wins': 0, 'top3': 0, 'top10': 0, 'cuts': 0, 'wins_by_tier': {}, 'majors': 0,
                          'secured': [],
                          'prize': led.prize if led else 0.0, 'net': led.net if led else 0.0,
                          'wr_start': self.rank_start.get(year, {}).get(g.id), 'wr_end': self.wr_pos.get(g.id),
                          'am_start': self.am_start.get(year, {}).get(g.id), 'am_end': self.am_pos.get(g.id),
                          'injury_weeks': 0}
        for r in self.results.values():
            if r.year != year or self.cal.by_id[r.series_id].kind == 'qualifying':
                continue
            for site in r.finish:
                for gid, pos, _ in site:
                    row = snap.get(gid)
                    if row is None or pos is None:
                        continue
                    row['cuts'] += 1
                    row['wins'] += pos == 1
                    if pos == 1:
                        ser = self.cal.by_id[r.series_id]
                        row['wins_by_tier'][ser.tier] = row['wins_by_tier'].get(ser.tier, 0) + 1
                        row['majors'] += ser.kind == 'major'
                    row['top3'] += pos <= 3
                    row['top10'] += pos <= 10
        for week, gid, kind, weeks, _ in self.injuries[year]:
            if gid in snap:
                snap[gid]['injury_weeks'] += weeks
        for gid, row in snap.items():                        # places already secured for next season
            if row['majors']:
                row['secured'].append('major champion (5-year exemptions)')
            if row['wins_by_tier'].get(1, 0) and row['status'] == 'pro':
                row['secured'].append('Premier Tour winner (Masters and other invitations)')
            if row['wr_end'] and row['wr_end'] <= 50:
                row['secured'].append('world top 50 (Tour Masters invitation)')
        for gid, row in snap.items():
            row['zero_start_reason'] = self.zero_start_reason(gid, year, row) if row['events'] == 0 else ''
        by_tour = defaultdict(list)
        for gid, row in snap.items():
            if row['status'] == 'pro' and row['tier'] <= 4:
                by_tour[row['tour']].append(gid)
        for tour, ids in by_tour.items():
            m = self.money[(tour, year)]
            ids.sort(key=lambda gid: self.standing_key(m, gid))
            i = 0
            while i < len(ids):                              # ties share the average of their ranks
                j = i
                while j < len(ids) and m.get(ids[j], 0.0) == m.get(ids[i], 0.0):
                    j += 1
                avg = (i + 1 + j) / 2
                for gid in ids[i:j]:
                    snap[gid]['money_on_tour'] = m.get(gid, 0.0)
                    snap[gid]['money_rank'] = avg
                    snap[gid]['money_rank_pct'] = avg / len(ids)
                i = j
        return snap

    def zero_start_reason(self, gid, year, row):
        """Why a golfer played no event all season, from what was recorded in their monthly plans."""
        f = self.block_flags[year].get(gid, Counter())
        months = sum(f.values()) or 1
        if row['injury_weeks'] >= 40:
            return 'injured'
        if f['stuck'] >= months / 2:
            return 'could not afford any trip'
        if self.entry_misses[year][gid] >= 4:
            return 'wanted to play but every field they tried was full'
        if f['no event'] >= months / 2:
            return 'no event they were eligible for'
        if self.g[gid].lifestyle == 'part_time':
            return 'part-timer: chose not to play'
        return 'chose not to play (training, rest or work)'

    # ---- development and the monthly plan ------------------------------------------------------
    def plan_block(self, year, week0):
        """Each golfer plans the next four weeks: which weeks to play, train, rest or (if they need the
        money) work.

        For every combination of weeks to play they weigh what the events are worth to their career
        against what playing or training does for their game (raw golfers learn a lot from
        tournaments), the cost of playing tired, the risk of injury, and money: a trip is only
        possible if they can pay for it from available funds after setting aside living costs, and
        its net cost (against the prize they expect from their own record) counts for more the
        tighter their funds. A week not played is a training week, a full rest week when tired, or
        a paid work week when money is short."""
        weeks = [w for w in range(week0, week0 + 4) if w <= 52]
        eds = [e for e in self.cal.editions(year) if e.week in weeks and not self.is_special(e.series)]
        venues = self.lib.venues(year)
        city = {e.event_id: venues[e.event_id][0].city for e in eds}
        by_week = {w: [e for e in eds if e.week == w] for w in weeks}
        rng = random.Random(_seed(self.seed, year, week0, 'plan'))
        cache = {}
        now = self.abs_week(year, 0)
        # (region, tier) pairs with a regular event in each week: 'no suitable event' vs 'not eligible'
        level_weeks = {w: {(COUNTRIES[CITY_BY_NAME[city[e.event_id]].country].region, e.series.tier)
                           for e in by_week[w]} for w in weeks}
        for g in self.world.golfers:
            if g.lifestyle == 'retired':
                continue
            key = (g.tour, g.country, g.status, g.lifestyle, self.wr_pos.get(g.id, 9999) <= 500,
                   self.am_pos.get(g.id, 9999) <= 25, self.am_pos.get(g.id, 9999) <= 300,
                   g.id if g.status == 'club_pro' else 0)      # club pros: their own diary and drives
            if key not in cache:                             # every eligible event, best first
                cache[key] = [sorted(((self.base_value(g, e, CITY_BY_NAME[city[e.event_id]].country), e.event_id, e)
                                      for e in by_week[w] if self.eligible(g, e.series, w)), reverse=True)
                              for w in weeks]
            options = cache[key]
            money0 = self.spendable(g, year)
            # each week: the most valuable event they can actually pay for (a cheaper local event is
            # still an option when the one they would prefer is out of reach)
            base, costs = [], []
            for opts in options:
                pick = self.best_affordable(g, opts, city, money0)
                base.append(pick[0] if pick else None)
                costs.append(pick[1] if pick else 0.0)
            avail = {}
            for i, w in enumerate(weeks):
                if base[i] is not None:
                    avail[w] = 'ok'
                elif options[i]:
                    avail[w] = 'unaff'
                else:
                    avail[w] = 'inelig' if (region_of(g), self.level_tier(g)) in level_weeks[w] else 'none'
            self.week_avail[g.id] = avail
            eligible_any = any(options)
            stuck = (money0 < 0 and self.committed_weekly(g) > 0) or (eligible_any and not any(base))
            self.stuck_blocks[g.id] = self.stuck_blocks[g.id] + 1 if stuck else 0
            self.block_flags[year][g.id]['stuck' if stuck else 'no event' if not eligible_any else 'ok'] += 1
            self.staff_midseason(g, year, week0, money0)
            age = g.age(year)
            insight = self.staff.insight(g, year)
            gaps = D.perceived_gaps(g, insight)
            cat = D.choose_category(g, rng, insight, gaps)
            work_scale = 0.3 if g.lifestyle == 'part_time' else 1.0
            gamma = 60.0
            dp = gamma * D.development_value(g, 'play', age, insight=insight, gaps=gaps)
            dt = gamma * D.development_value(g, 'train', age, cat, insight, self.staff.coaching(g, cat, age, year),
                                             self.experience(g.id, year, week0), gaps) * work_scale
            bar = self.bar(g)
            target = self.target_events(g)
            played0 = len(self.played[year][g.id])
            inj_until = self.injured.get(g.id, (0,))[0]
            stam = g.attrs['stamina'] / 100
            load4 = 4 * FATIGUE_PER_ROUND * (1.4 - 0.8 * stam) * (1 + 0.02 * max(0, age - 30))
            rest_rec = 0.40 + 0.30 * (1 - g.attrs['recovery_rate'] / 100)
            top100 = self.wr_pos.get(g.id, 9999) <= 100
            unit = FIN.money_unit(self.funds(g, year))
            prizes = [self.expected_kept(g, b[1].series) if b else 0.0 for b in base]
            # Paid work only makes sense when money is genuinely short: funds would not last three
            # months and their own results are not paying for their golf.
            burn = FIN.weekly_living(g)[1] + (sum(costs) / max(1, sum(1 for b in base if b)))
            # ... and they must earn if they cannot cover the next weeks' committed costs, or cannot
            # afford any trip this month (otherwise a golfer just short of a trip would wait for ever).
            can_work = (g.status == 'pro' and g.lifestyle == 'full_time'
                        and (stuck or money0 < 13 * burn and sum(prizes) <= sum(costs)))
            work_v = min(20.0, FIN.WORK_WAGE / unit) if can_work else -1.0
            if can_work and stuck:
                work_v = 40.0
            playable = [i for i, w in enumerate(weeks) if base[i] is not None and now + w >= inj_until]
            slot = {i: j for j, i in enumerate(playable)}
            best_val, best_acts = None, None
            for mask in range(1 << len(playable)):
                f = self.fatigue[g.id]
                val, n, money, acts = 0.0, played0, money0, []
                for i, w in enumerate(weeks):
                    if now + w < inj_until:
                        f *= rest_rec
                        acts.append('rest')
                        continue
                    j = slot.get(i, -1)
                    if j >= 0 and mask >> j & 1:
                        if costs[i] > 0 and costs[i] > money:
                            val = None                       # they cannot pay for this trip (school-paid: free)
                            break
                        money -= costs[i]
                        pace = target * w / 52 - n
                        v = base[i][0] + max(-25.0, min(6.0, 3.5 * pace)) - (6 if w + 1 in MAJOR_WEEKS and top100 else 0)
                        eff = max(0.0, f - 0.2) * 1.25
                        val += ((v - bar) + dp - 12 * eff - 400 * self.injury_chance(g, 4, year, f)
                                - (costs[i] - prizes[i]) / unit)
                        f = 1 - (1 - 0.9 * f) * (1 - load4)
                        n += 1
                        acts.append('play')
                    elif f > 0.25:
                        f *= rest_rec
                        acts.append('rest')
                    elif work_v > dt:
                        val += work_v
                        money += FIN.WORK_WAGE
                        f *= 0.8
                        acts.append('work')
                    else:
                        val += dt
                        f = 0.85 * f + 0.02
                        acts.append('train')
                if val is not None and (best_val is None or val > best_val):
                    best_val, best_acts = val, acts
            if best_acts is None:                            # nothing affordable: work if they can
                best_acts = ['work' if g.status == 'pro' and g.lifestyle == 'full_time' else 'train'
                             for _ in weeks]
            self.plans[g.id] = {w: (a, cat) for w, a in zip(weeks, best_acts)}

    def level_tier(self, g):
        """The tier of ordinary events a golfer's status is built around (club pros: none)."""
        if g.status == 'club_pro':
            return 8
        if g.status == 'amateur':
            return 5 if g.tour.startswith('CO_') else 6
        t = TOUR_BY_KEY.get(g.tour)
        return t.tier if t else 4

    def record_access(self, year, week):
        """Classify every active golfer's week (see ACCESS): what they played, or why they did not."""
        acc = self.week_access[year]
        for g in self.world.golfers:
            if g.lifestyle == 'retired':
                continue
            gid = g.id
            entered = self._week_entered.get(gid)
            if entered and self.week_rounds.get(gid, 0) > 0:
                eid, how = entered
                if how == 'selected':
                    why = 'played: selected field'
                elif self._week_first.get(gid) in (None, eid):
                    why = 'played: first choice'
                else:
                    why = 'played: alternative'
            elif gid in self.injured:
                why = 'injured'
            elif gid in self._week_shut:
                first = self._week_first.get(gid, '')
                why = ('not selected for the college lineup' if g.tour.startswith('CO_') and
                       self.cal.by_id[first.split(':', 1)[1]].tier == 5 else 'shut out: every acceptable field full')
            else:
                av = self.week_avail.get(gid, {}).get(week, 'ok')
                act = self.week_activity.get(gid, 'rest')
                if av == 'none':
                    why = 'no suitable event scheduled'
                elif av == 'inelig':
                    why = 'not eligible for the events scheduled'
                elif av == 'unaff':
                    why = 'could not afford any event'
                elif self.plans.get(gid, {}).get(week, ('rest',))[0] == 'play':
                    why = 'declined the events on offer'
                else:
                    why = {'train': 'chose to train', 'work': 'chose to work'}.get(act, 'chose to rest')
            acc[gid][why] += 1
            if why in ('played: alternative', 'shut out: every acceptable field full', 'not selected for the college lineup'):
                self.access_log[year][gid].append((week, why, self._week_first.get(gid),
                                                   entered[0] if entered and why.startswith('played') else None))
            if why.startswith(('shut out', 'not selected')):
                if len(self.played[year][gid]) < self.target_events(g) * week / 52:
                    self.denied_behind[year][gid] += 1      # a real shortage, not an extra start wanted
                self.denied_run[gid] += 1
                self.max_denied_run[year][gid] = max(self.max_denied_run[year][gid], self.denied_run[gid])
            elif why.startswith('played'):
                self.denied_run[gid] = 0
        self._week_entered.clear()
        self._week_first.clear()
        self._week_shut.clear()

    def best_affordable(self, g, opts, city, money):
        """The most valuable of a week's eligible events (`opts`, best first) whose trip the golfer can
        pay for: ((value, edition), trip cost), or None."""
        for v, _, e in opts:
            c = self.trip_cost(g, e.series, city[e.event_id])
            if c <= money or c == 0:                          # a school-paid event is never out of reach
                return (v, e), c
        return None

    def staff_midseason(self, g, year, week, money0):
        """Monthly: a golfer who can no longer cover their committed costs stops paying their coach
        (the fee stops from this week); a caddie whose player has been unable to afford a single trip
        for two months in a row looks for another bag."""
        st = self.staff
        c = st.coach(g.id)
        if c is not None and st.deal.get(g.id) == 'fee' and money0 < 0:
            st.end_coach(self, g.id, (year, week), 'could no longer pay the fee', 'golfer')
        k = st.caddie(g.id)
        if k is not None and self.stuck_blocks[g.id] >= 2:
            st.end_caddie(self, g.id, (year, week), 'no events the golfer could afford', 'staff')

    # ---- money --------------------------------------------------------------------------------
    def earn(self, g, year, field, amount):
        """Income: recorded in the ledger and added to cash in the same step (exact accounting)."""
        led = self.ledger(year, g.id)
        setattr(led, field, getattr(led, field) + amount)
        g.cash += amount

    def spend(self, g, year, field, amount):
        led = self.ledger(year, g.id)
        setattr(led, field, getattr(led, field) + amount)
        g.cash -= amount

    def pay_staff(self, g, year, field, person, amount):
        """A payment from a golfer to their coach or caddie: out of the golfer's ledger and into the
        person's receipts in the same step, so the two always reconcile."""
        self.spend(g, year, field, amount)
        person.earnings += amount
        key = ('coach' if field.startswith('coach') else 'caddie', person.id)
        self.staff_receipts[year][key] += amount

    def funds(self, g, year):
        """What a golfer could draw on right now: savings, backers, and a limited line of credit."""
        last = self.ledgers.get(year - 1, {}).get(g.id)
        earned = last.income - last.support if last else 0.0    # lenders look at earnings, not handouts
        return g.cash + g.backing + FIN.credit_limit(earned)

    # The money definitions every decision shares (hiring, the monthly plan, entries, settlement and
    # career runway):
    #   committed     what goes out every week whatever they do: living costs net of salary, and a
    #                 contracted coach's fee
    #   spendable     funds after setting aside RESERVE_WEEKS of committed costs: the money for travel
    #   trip cost     travel and fees, plus a caddie's weekly fee (paid only in weeks they play)
    #   prize kept    expected prize money net of the caddie's, a scouting coach's and backers' shares;
    #                 it informs decisions but is never spent before it is won
    def committed_weekly(self, g):
        salary, living = FIN.weekly_living(g)
        c = self.staff.coach(g.id)
        coach = self.staff.agreed_fee(g.id) / 52 if c is not None else 0.0
        return max(0.0, living - salary) + coach

    def spendable(self, g, year):
        """Funds left for golf after setting aside the next few weeks of committed costs."""
        return self.funds(g, year) - FIN.RESERVE_WEEKS * self.committed_weekly(g)

    def can_afford(self, g, series, city, money):
        """The one affordability rule for every entry, qualifier and invitation: the trip is free (the
        school pays) or within the golfer's spendable funds `money`."""
        cost = self.trip_cost(g, series, city)
        return cost <= 0 or cost <= money

    def trip_cost(self, g, series, city):
        """What playing an event costs a golfer: travel and fees, plus their caddie's weekly fee."""
        k = self.staff.caddie(g.id)
        return FIN.event_cost(g, series, city) + (k.weekly_fee if k is not None else 0.0)

    def prize_kept(self, g):
        """Share of prize money a golfer keeps after their caddie's and a scouting coach's shares."""
        return (1.0 - (FIN.CADDIE_SHARE if self.staff.caddie(g.id) is not None else 0.0)
                - (ST.SCOUT_SHARE if self.staff.deal.get(g.id) == 'share' else 0.0)
                - (FIN.BACKER_SHARE if g.backer else 0.0))

    def earned_income(self, g, year):
        """Income earned in a year (prize money kept, sponsors, salary, work): not family support."""
        led = self.ledgers.get(year, {}).get(g.id)
        if led is None:
            return 0.0
        return (led.prize - led.caddie_share - led.coach_share - led.backer_share + led.sponsors + led.salary
                + led.work)

    def means(self, g, year):
        """What a golfer can commit to staff from: spendable funds plus most of what last year's earnings
        left after living costs (a salary that pays the rent is not spare money)."""
        led = self.ledgers.get(year - 1, {}).get(g.id)
        disposable = self.earned_income(g, year - 1) - (led.living if led else 0.0)
        return max(0.0, self.spendable(g, year)) + 0.8 * max(0.0, disposable)

    def expected_prize(self, g, series):
        """The prize a golfer expects from an event, from the share of purses they have actually won
        (halved for each level the field is above their own tour's)."""
        if g.status == 'amateur' or not series.purse:
            return 0.0
        own = TOUR_BY_KEY[g.tour].tier if g.tour in TOUR_BY_KEY else 4
        stronger = max(0, own - series.tier)                 # a field above their usual level
        return self.prize_share.get(g.id, FIN.PRIOR_PRIZE_SHARE) * series.purse * 0.5 ** stronger

    def expected_kept(self, g, series):
        return self.expected_prize(g, series) * self.prize_kept(g)

    def weekly_finances(self, year, week):
        """Salaries, living costs, sponsor contracts and paid work for the week; backers cover shortfalls."""
        for g in self.world.golfers:
            if g.lifestyle == 'retired':
                continue
            salary, living = FIN.weekly_living(g)
            if salary:
                self.earn(g, year, 'salary', salary)
            if living:
                self.spend(g, year, 'living', living)
            contract = self.contracts.get(g.id)
            if contract:
                self.earn(g, year, 'sponsors', contract / 52)
            if self.week_activity.get(g.id) == 'work':
                self.earn(g, year, 'work', FIN.WORK_WAGE)
            if self.staff.deal.get(g.id) == 'fee':
                c = self.staff.coach(g.id)
                self.pay_staff(g, year, 'coaching', c, self.staff.agreed_fee(g.id) / 52)
            if g.cash < 0 and g.backing > 0:
                draw = min(g.backing, -g.cash)
                g.backing -= draw
                self.earn(g, year, 'support', draw)

    def experience(self, gid, year, week):
        """Competitive experience over the last 52 weeks (0-1), from rounds actually played."""
        rounds = self.season_rounds[year][gid] + self.season_rounds.get(year - 1, {}).get(gid, 0) * max(0, 52 - week) / 52
        return D.experience_factor(rounds)

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
            elif action == 'work':
                act = 'work'
            else:
                act = 'train' if action in ('play', 'train') and self.development else 'rest'
            self.week_activity[g.id] = act
            self.activity_counts[year][g.id][act] += 1
            if self.development and g.ceilings:
                scale = 0.3 if g.lifestyle == 'part_time' and act == 'train' else 1.0
                D.develop_week(g, 'rest' if act == 'work' else act, g.age(year), cat, rounds,
                               coach=self.staff.coaching(g, cat, g.age(year), year), scale=scale,
                               experience=self.experience(g.id, year, week))
            if act in ('train', 'play') and g.id in self.staff.coach_of:
                self.staff.rel.add_work('coach', g.id, 1.0, year)        # a week actually worked together
