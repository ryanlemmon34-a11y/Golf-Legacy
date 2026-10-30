"""The world course library: 520 fictional courses in the real cities where the calendar plays.

How the library is sized
    The calendar is replayed for ten seasons. Every edition (and every site of a multi-site
    qualifier) needs a free course of the right standard in its host city that week; when none
    exists, one is built there. That gives the minimum set. The rest of the 380 are added where golf
    is busiest, as extra clubs and municipal courses, so the busiest cities have a choice of venue.

Classes and layouts (see `course_gen`)
    elite         majors and Premier Tour only, one layout (Championship)
    championship  Championship + Club
    standard      Championship + Club, nearly half also Forward
    municipal     Regular, about half also Forward

Which layout an event plays
    level of event      layouts it may use (most preferred first)
    major               elite Championship
    premier             elite / championship Championship
    top                 championship / standard Championship  (Challenger tours, national opens,
                        elite amateurs, final qualifying, Q-School finals, national championships)
    mid                 standard Championship, championship Club, standard Club  (regional & mini
                        tours, college, national amateurs, earlier qualifying stages)
    low                 standard Club / Forward, municipal Regular / Forward, championship Club
                        (mini events, small-college golf, 54-72 hole amateur events)
    entry               standard Forward, municipal Regular, standard Club, municipal Forward
                        (18-36 hole regional amateur events)

A series returns to the same course whenever it is in the same city (a stable "home course"), so
event history and course records build up the way they do in real life. Records are kept per
layout (`Course.layout_id`) in `records.py`.
"""
from __future__ import annotations

import hashlib
import random
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, replace

from .calendar import MAJOR_VENUES, WorldCalendar
from . import schedule as SCH
from .course import cedar_creek_municipal, georgia_national
from .course_gen import generate_site, CLASS_DIFFICULTY
from .geography import CITIES_BY_COUNTRY, CITY_BY_NAME, COUNTRIES, season_weeks

TARGET_COURSES = 520
PLAN_YEARS = 10

LEVEL_LAYOUTS = {
    'major': (('elite', 'Championship'),),
    'premier': (('championship', 'Championship'), ('elite', 'Championship')),
    'opportunity': (('championship', 'Championship'), ('standard', 'Championship'), ('elite', 'Championship')),
    'flagship': (('elite', 'Championship'), ('championship', 'Championship')),
    'top': (('championship', 'Championship'), ('standard', 'Championship')),
    'mid': (('standard', 'Championship'), ('championship', 'Club'), ('standard', 'Club'),
            ('championship', 'Championship')),
    'low': (('standard', 'Club'), ('standard', 'Forward'), ('municipal', 'Regular'), ('municipal', 'Forward'),
            ('championship', 'Club'), ('standard', 'Championship')),
    'entry': (('standard', 'Forward'), ('municipal', 'Regular'), ('standard', 'Club'), ('municipal', 'Forward'),
              ('championship', 'Club')),
}
TOP_QUALIFIERS = {'USA_OPEN_FINAL', 'USA_OPEN_FINAL_INTL', 'BRITANNIA_FINAL', 'CLUB_PRO_CHAMPIONSHIP',
                  'PT_QSCHOOL_FINAL', 'EU_QSCHOOL_FINAL', 'JP_QSCHOOL_FINAL', 'ASIA_QSCHOOL_FINAL',
                  'COLLEGE_NATIONAL_CHAMPIONSHIP'}


def event_level(s):
    """How good a course an event series needs (see module docstring)."""
    if s.kind == 'major':
        return 'major'
    if s.tier == 1:
        return s.category if s.category in ('flagship', 'opportunity') else 'premier'
    if (s.tier == 2 or s.category in ('elite_amateur', 'national_open') or s.series_id in TOP_QUALIFIERS
            or s.category == 'national_amateur' and COUNTRIES[s.host_country].golf >= 1):
        return 'top'
    if s.tier == 3 or s.holes >= 54 and s.tier in (4, 5, 6, 7) and s.tour not in ('CO_US_SMALL', 'CO_INTL'):
        return 'mid'
    if s.tier == 7:
        return 'mid'
    if s.tier == 6 and s.holes <= 36:
        return 'entry'
    return 'low'


def _h(*parts):
    return int.from_bytes(hashlib.blake2b(':'.join(map(str, parts)).encode(), digest_size=8).digest(), 'big')


def _slug(name):
    s = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


@dataclass(frozen=True)
class Venue:
    """Where one edition (or one site of a multi-site qualifier) is played."""
    event_id: str
    site: int
    course_id: str
    layout: str
    city: str

    @property
    def layout_id(self):
        return f'{self.course_id}:{self.layout}'


class CourseLibrary:
    """All courses in the world, plus the venue for every edition of every event."""

    def __init__(self, calendar=None, seed=2027, target=TARGET_COURSES, first_year=2027, plan_years=PLAN_YEARS):
        self.calendar = calendar or WorldCalendar(seed)
        self.seed = seed
        self.first_year = first_year
        self.sites = {}                       # course_id -> site dict (see course_gen.generate_site)
        self.by_city = defaultdict(list)      # city -> [course_id]
        self._names = set()
        self._home = {}                       # (series_id, city) -> course_id last used
        self._venues = {}                     # year -> {event_id: [Venue per site]}
        self._seed_hand_built()
        self._grow_to_demand(plan_years)
        self._fill_to(target)
        self._venues.clear()
        self._home.clear()

    # -- building ------------------------------------------------------------------------------
    def _register(self, site):
        cid = base = _slug(site['name'])
        n = 2
        while cid in self.sites:
            cid = f'{base}-{n}'
            n += 1
        site['course_id'] = cid
        site['layouts'] = {k: replace(c, course_id=cid) for k, c in site['layouts'].items()}
        self.sites[cid] = site
        self.by_city[site['city']].append(cid)
        self._names.update((site['name'], 'core:' + site['name'].lower()))
        return cid

    def _seed_hand_built(self):
        for build, city, cls, arch, opened, style in (
                (georgia_national, 'Athens, Georgia', 'elite', 'Samuel Kittredge', 1931, 'Woodland'),
                (cedar_creek_municipal, 'Muncie, Indiana', 'municipal', 'William Ashdown', 1928, 'Municipal')):
            c = build()
            layout = 'Championship' if cls == 'elite' else 'Regular'
            c = replace(c, city=city, tags=(cls,), layout=layout)
            self._register(dict(course_id='', name=c.name, city=city, country=c.country,
                                region=COUNTRIES[c.country].region, style=style, cls=cls,
                                difficulty=1.0 if cls == 'elite' else 0.0, architect=arch, opened=opened,
                                layouts={layout: c}, hand_built=True))

    def _new_site(self, city, cls):
        n = len(self.by_city[city])
        rng = random.Random(_h(self.seed, 'course', city, n, cls))
        # the Britannia Open is only ever played on links
        style = 'Links' if cls == 'elite' and city in MAJOR_VENUES['BRITANNIA_OPEN'][1] else None
        return self._register(generate_site('', city, cls, rng, self._names, style))

    @staticmethod
    def _class_for_level(level, rng):
        if level in ('major', 'flagship'):
            return 'elite'
        if level == 'premier':
            return 'championship'
        if level == 'opportunity':
            return 'championship' if rng.random() < .5 else 'standard'
        if level == 'top':
            return 'championship' if rng.random() < .25 else 'standard'
        if level == 'mid':
            return 'standard'
        if level == 'entry':
            return 'municipal' if rng.random() < .6 else 'standard'
        return 'municipal' if rng.random() < .75 else 'standard'

    def _grow_to_demand(self, years):
        for year in range(self.first_year, self.first_year + years):
            self._assign_year(year, grow=True)

    def _fill_to(self, target):
        """Add clubs where golf is busiest until the library reaches `target` courses."""
        if len(self.sites) > target:
            raise ValueError(f'calendar needs {len(self.sites)} courses, more than the target {target}')
        load = Counter()
        for year in range(self.first_year, self.first_year + PLAN_YEARS):
            for ed in self.calendar.editions(year):
                load[ed.city] += 1
        rng = random.Random(_h(self.seed, 'fill'))
        while len(self.sites) < target:
            city = max(load, key=lambda c: (load[c] / (len(self.by_city[c]) + 1), c))
            cls = rng.choices(('championship', 'standard', 'municipal'), (1, 4, 3))[0]
            self._new_site(city, cls)

    # -- venues --------------------------------------------------------------------------------
    def _candidate_cities(self, ed, site_no):
        s = ed.series
        pool = list(s.cities)
        start = pool.index(ed.city) if ed.city in pool else 0
        ordered = pool[start:] + pool[:start]
        if s.sites > 1:
            # site k of a multi-site stage starts k places further round the pool
            ordered = ordered[site_no % len(ordered):] + ordered[:site_no % len(ordered)]
        others = [c.name for c in CITIES_BY_COUNTRY[s.host_country]
                  if s.week in season_weeks(c) and c.name not in ordered]
        others.sort(key=lambda c: _h(s.series_id, c))
        return ordered, others

    def _eligible(self, cid, level):
        site = self.sites[cid]
        for rank, (cls, layout) in enumerate(LEVEL_LAYOUTS[level]):
            if site['cls'] == cls and layout in site['layouts']:
                return rank, layout
        return None

    def _pick(self, city, ed, level, busy):
        best = None
        home = self._home.get((ed.series.series_id, city))
        for cid in self.by_city.get(city, ()):
            if cid in busy:
                continue
            ok = self._eligible(cid, level)
            if not ok:
                continue
            rank, layout = ok
            key = (cid != home, rank, _h(ed.series.series_id, cid))
            if best is None or key < best[0]:
                best = (key, cid, layout)
        return best

    def _assign_year(self, year, grow=False):
        eds = sorted(self.calendar.editions(year), key=lambda e: (e.week, e.series.tier, -e.series.prestige,
                                                                   e.series.series_id))
        busy = defaultdict(set)                    # week -> course ids in use
        out = {}
        rng = random.Random(_h(self.seed, 'grow', year))
        for ed in eds:
            level = event_level(ed.series)
            venues = []
            for site_no in range(ed.series.sites):
                ordered, others = self._candidate_cities(ed, site_no)
                pick = None
                if ed.series.sites > 1:
                    # each site in its own city where possible
                    used = {v.city for v in venues}
                    ordered = [c for c in ordered if c not in used] + [c for c in ordered if c in used]
                if grow:
                    # build where the event is meant to be unless that city already has a suitable
                    # course that is simply booked; then the event may move round its pool
                    has_any = any(self._eligible(c, level) for c in self.by_city.get(ordered[0], ()))
                    tries = ordered if has_any or level in ('mid', 'low', 'entry') else ordered[:1]
                else:
                    tries = ordered + others
                for city in tries:
                    p = self._pick(city, ed, level, busy[ed.week])
                    if p:
                        pick = (city,) + p[1:]
                        break
                if pick is None and grow:
                    city = ordered[0]
                    cid = self._new_site(city, self._class_for_level(level, rng))
                    pick = (city, cid, self._eligible(cid, level)[1])
                if pick is None:
                    raise RuntimeError(f'no course available for {ed.event_id} site {site_no + 1}')
                city, cid, layout = pick
                busy[ed.week].add(cid)
                self._home[(ed.series.series_id, city)] = cid
                venues.append(Venue(ed.event_id, site_no, cid, layout, city))
            out[ed.event_id] = venues
        return out

    def venues(self, year):
        """{event_id: [Venue, ...one per site]} for every edition that year."""
        if year not in self._venues:
            # history matters for home courses: assign earlier seasons first
            for y in range(min(self._venues, default=self.first_year), year + 1):
                if y not in self._venues:
                    self._venues[y] = self._assign_year(y)
        return self._venues[year]

    def course(self, layout_id_or_venue):
        """The playable Course for a layout id ('course-id:Layout') or a Venue."""
        lid = layout_id_or_venue.layout_id if isinstance(layout_id_or_venue, Venue) else layout_id_or_venue
        cid, layout = lid.split(':')
        return self.sites[cid]['layouts'][layout]

    def layouts(self):
        for cid, site in self.sites.items():
            for key, course in site['layouts'].items():
                yield site, key, course

    # -- checks --------------------------------------------------------------------------------
    def validate(self, years=3):
        errors = []
        if len(self.sites) != TARGET_COURSES:
            errors.append(f'{len(self.sites)} courses, expected {TARGET_COURSES}')
        for site in self.sites.values():
            if site['cls'] == 'elite' and list(site['layouts']) != ['Championship']:
                errors.append(f'{site["name"]}: elite course with layouts {list(site["layouts"])}')
            if site['city'] not in CITY_BY_NAME:
                errors.append(f'{site["name"]}: unknown city')
        for year in range(self.first_year, self.first_year + years):
            per_week = defaultdict(Counter)
            for ed in self.calendar.editions(year):
                vs = self.venues(year)[ed.event_id]
                if len(vs) != ed.series.sites:
                    errors.append(f'{ed.event_id}: {len(vs)} venues for {ed.series.sites} sites')
                for v in vs:
                    site = self.sites[v.course_id]
                    per_week[ed.week][v.course_id] += 1
                    if site['cls'] == 'elite' and ed.series.tier > 1:
                        errors.append(f'{ed.event_id}: elite course {site["name"]} used below the Premier Tour')
                    if ed.week not in season_weeks(CITY_BY_NAME[v.city]):
                        errors.append(f'{ed.event_id}: {v.city} out of season')
                    if CITY_BY_NAME[v.city].country != ed.series.host_country and v.city not in ed.series.cities:
                        errors.append(f'{ed.event_id}: played outside its host country')
            for w, c in per_week.items():
                for cid, n in c.items():
                    if n > 1:
                        errors.append(f'{year} week {w}: {self.sites[cid]["name"]} hosts {n} events')
                if w in self.calendar.major_weeks and sum(1 for cid in c if self.sites[cid]['cls'] == 'elite') != 1:
                    errors.append(f'{year} week {w}: a major week must use exactly one elite course (the major\'s)')
        return errors


_DEFAULT = {}


def default_library(version=SCH.LEGACY):
    """The standard world (seed 2027) for a calendar version, built once per process. The courses follow the
    calendar (each event's host cities), so each version has its own library; v1's is the one every world
    used before calendar versions."""
    lib = _DEFAULT.get(version)
    if lib is None:
        lib = _DEFAULT[version] = CourseLibrary(WorldCalendar(2027, version))
    return lib


def library_version(lib):
    """The calendar version of a library (None for a library that is not a standard one)."""
    return next((v for v, x in _DEFAULT.items() if x is lib), None)


# ---------------------------------------------------------------------------------------------
# Layout ratings: how each layout plays for each level of golfer, measured by simulation.
# ---------------------------------------------------------------------------------------------
RATING_LEVELS = (('tour', 75), ('amateur_winner', 40), ('amateur', 25), ('high_school', 10))
RATINGS_FILE = 'data/layout_ratings.json'


def fingerprint(course):
    """Changes whenever the holes change, so stale ratings are never used."""
    return hashlib.blake2b(repr(course.holes).encode(), digest_size=6).hexdigest()


def rate_layout(course, rounds=100, seed=0):
    """Average score for golfers at each level in RATING_LEVELS (calm, standard set-up)."""
    from .engine import play_round
    from .golfer import uniform_golfer
    out = {'par': course.par, 'yards': course.yards, 'fingerprint': fingerprint(course)}
    for key, rating in RATING_LEVELS:
        rng = random.Random(_h(seed, course.layout_id, rating))
        g = uniform_golfer(rating)
        out[key] = round(sum(play_round(g, course, rng).score for _ in range(rounds)) / rounds, 2)
    out['difficulty'] = round(out['tour'] - course.par, 2)          # tour average vs par
    out['spread'] = round(out['amateur'] - out['tour'], 2)          # how much harder for weaker players
    return out


def load_ratings(root='.'):
    import json
    import os
    path = os.path.join(root, RATINGS_FILE)
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf8') as f:
        return json.load(f)
