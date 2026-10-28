"""The world golf calendar: every tour, from regional amateur series to the majors.

The calendar is a template of permanent *event series* (stable `series_id`, format, field, prestige,
purse, week, host country and venue policy). Each year produces *editions* (`event_id` =
"YEAR:SERIES_ID"); rotating series move to a different host city each year.

Scheduling follows a priority cascade:
  1. the four majors own their weeks at the top level: no Premier Tour event is played in a major
     week, but Challenger, Regional and Mini tours, college, amateur and club-professional golf go on
     (golfers in the major cannot also play elsewhere that week);
  2. fixed-week anchors: elite amateur championships, qualifying stages, college post-season,
     club-pro championship, Q-School stages and designated national opens;
  3. Premier Tour events (8 flagship / 20 standard / 8 opportunity);
  3c. each circuit's season-ending championship (CIRCUIT_FLAGSHIPS), in its last weeks;
  4. Challenger, Regional and Mini tours, and the regional club-professional circuits;
  5. College and amateur regular seasons.
Flexible events are placed only in weeks when the host city's climate supports golf.
Which events feed which majors (and how) lives in `qualification.py`.
"""
from __future__ import annotations

import hashlib
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field as dc_field, replace

from .geography import CITIES_BY_COUNTRY, CITY_BY_NAME, COUNTRIES, season_weeks

MAJORS = {
    18: ('TOUR_MASTERS', 'Tour Masters'),
    24: ('PREMIER_TOUR_CHAMPIONSHIP', 'Premier Tour Championship'),
    25: ('USA_OPEN', 'USA Open'),
    30: ('BRITANNIA_OPEN', 'Britannia Open'),
}
MAJOR_WEEKS = frozenset(MAJORS)
MAJOR_ID_BY_WEEK = {w: sid for w, (sid, _) in MAJORS.items()}

TIERS = {0: 'Major', 1: 'Premier', 2: 'Challenger', 3: 'Regional', 4: 'Mini', 5: 'College',
         6: 'Amateur', 7: 'Qualifying', 8: 'Club professional'}

# Which days of the week an event occupies. A golfer may play a Monday qualifier and a
# Thursday-Sunday tournament in the same week, as in real life, but never two overlapping events.
DAYS = {'Thu-Sun': {3, 4, 5, 6}, 'Fri-Sun': {4, 5, 6}, 'Sat-Sun': {5, 6}, 'Sat': {5}, 'Sun': {6},
        'Mon': {0}, 'Tue': {1}, 'Mon-Tue': {0, 1}, 'Mon-Wed': {0, 1, 2}, 'Mon-Sun': set(range(7)),
        'Tue-Fri': {1, 2, 3, 4}}
DEFAULT_DAYS = {18: 'Sat', 36: 'Sat-Sun', 54: 'Fri-Sun', 72: 'Thu-Sun'}


@dataclass(frozen=True)
class Series:
    series_id: str
    name: str
    tour: str                    # tour key
    tier: int
    kind: str                    # major / premier / pro / college / amateur / qualifying
    category: str                # major, flagship, standard, opportunity, national_open, regular, ...
    holes: int
    field: int
    week: int
    eligibility: str             # open / pro / members / amateur / college / club_pro / mid_amateur
    host_country: str
    cities: tuple                # fixed venue: one city; rotating: a pool
    venue_policy: str = 'rotating'
    cut_after_holes: int = 0
    cut_top: int = 0
    days: str = ''
    match_play: bool = False     # stroke-play qualifying followed by match play
    prestige: int = 50
    purse: int = 0
    sites: int = 1               # number of simultaneous sites (qualifying stages)
    anchored: bool = False       # fixed week every year

    @property
    def rounds(self):
        return self.holes // 18

    @property
    def day_set(self):
        return DAYS[self.days or DEFAULT_DAYS[self.holes]]


@dataclass(frozen=True)
class Edition:
    year: int
    series: Series
    city: str

    @property
    def event_id(self):
        return f'{self.year}:{self.series.series_id}'

    @property
    def week(self):
        return self.series.week

    @property
    def country(self):
        return CITY_BY_NAME[self.city].country


@dataclass(frozen=True)
class Tour:
    key: str
    name: str
    tier: int
    kind: str
    countries: tuple             # (country, weight) pairs
    weeks: tuple                 # allowed week window(s), inclusive (start, end) pairs
    events: int
    formats: tuple = ((72, 1.0),)
    field: int = 144
    per_week: int = 1            # simultaneous events the tour can run in one week
    prestige: int = 50
    purse: int = 0
    eligibility: str = 'members'
    cut: dict = dc_field(default_factory=dict)   # holes -> cut_top (cut after 36 holes)
    days: dict = dc_field(default_factory=dict)  # holes -> days of the week, when not the default


def _rng(*parts):
    digest = hashlib.blake2b(':'.join(map(str, parts)).encode(), digest_size=8).digest()
    return random.Random(int.from_bytes(digest, 'big'))


def _window(*pairs):
    return tuple(pairs)


def _in_window(week, windows):
    return any(a <= week <= b for a, b in windows)


# ---------------------------------------------------------------------------------------------
# Local golf: amateur series and club-professional circuits play in every golfing country of their
# region, with events in proportion to the size of each country's golf scene (its starting nation pool;
# see nations.py) and a floor so that no golfing country is without a season of local golf.
# ---------------------------------------------------------------------------------------------
# Club professionals are far fewer than amateurs (about one per unit of nation pool, each wanting ~12
# starts), so their circuits hold fewer, bigger events -- section events of 30-40 club pros, not a dozen --
# in the countries with a real club-pro scene; club pros from smaller golf countries cross a border in
# their region to play. LOCAL_MIN keeps every region's circuit a full season of choices (more events than
# any one club pro will play), topped up in proportion to each country's golf scene.
LOCAL_RATE = {'amateur': 0.9, 'club_pro': 0.3}                       # events per unit of nation pool
LOCAL_FLOOR = {'amateur': ((1.0, 4), (0.5, 3), (0.2, 2)), 'club_pro': ((5.0, 3), (3.0, 2))}
LOCAL_MIN = {'amateur': 0, 'club_pro': 16}                           # events per regional circuit at least
LOCAL_MIN_POOL = {'amateur': 0.0, 'club_pro': 3.0}                   # smaller golf countries travel
LOCAL_PER_WEEK = 14                    # simultaneous local events a regional circuit can hold (different countries)


def _local_countries(regions):
    from .nations import NATIONS
    return tuple((c, NATIONS[c].pool) for c, info in sorted(COUNTRIES.items()) if info.region in regions
                 and CITIES_BY_COUNTRY.get(c))


def local_allocation(regions, kind):
    """Events per country for a local circuit: max(floor for the country's size, rate x pool), topped
    up to the circuit's minimum (LOCAL_MIN) one event at a time, each to the country with the most golf
    per event it already has."""
    out = {}
    countries = [(c, pool) for c, pool in _local_countries(regions) if pool >= LOCAL_MIN_POOL[kind]]
    for c, pool in countries:
        floor = next((n for size, n in LOCAL_FLOOR[kind] if pool >= size), 0)
        n = max(floor, round(LOCAL_RATE[kind] * pool))
        if n:
            out[c] = n
    while countries and sum(out.values()) < LOCAL_MIN[kind]:
        c = max(countries, key=lambda cp: (cp[1] / (out.get(cp[0], 0) + 1), cp[0]))[0]
        out[c] = out.get(c, 0) + 1
    return out


# ---------------------------------------------------------------------------------------------
# Tours. Fictional names; the real-life analogue is noted for reference.
# ---------------------------------------------------------------------------------------------
PRO_CUTS = {72: 65, 54: 60}
TOURS = (
    # Tier 1 -- Premier Tour circuits (PGA Tour / DP World Tour level). Their 36 events are designed
    # individually below (8 flagship, 20 standard, 8 opportunity).
    Tour('PT_AMERICAS', 'Premier Tour Americas', 1, 'premier', (('USA', 9), ('Canada', 1), ('Mexico', .6)),
         _window((1, 47)), 16, field=144, prestige=81, purse=10_000_000, cut=PRO_CUTS),
    Tour('PT_EUROPE', 'Premier Tour Europe', 1, 'premier',
         (('England', 3), ('Scotland', 2), ('Ireland', 1.5), ('Spain', 2), ('Germany', 1.5), ('France', 1.2),
          ('Italy', 1), ('Denmark', .8), ('Netherlands', .8), ('United Arab Emirates', 1.5), ('Qatar', .5),
          ('Saudi Arabia', .5), ('South Africa', 1), ('Kenya', .5)), _window((2, 47)), 13,
         field=144, prestige=80, purse=8_000_000, cut=PRO_CUTS),
    Tour('PT_ASIA_PACIFIC', 'Premier Tour Asia-Pacific', 1, 'premier',
         (('Australia', 2), ('Japan', 1.5), ('South Korea', 1), ('China', 1), ('Singapore', .6), ('India', .8)),
         _window((8, 14), (36, 50)), 7, field=144, prestige=78, purse=7_000_000, cut=PRO_CUTS),
    # Tier 2 -- Challenger / developmental (Korn Ferry, Challenge Tour, Asian Tour, PGA Tour Americas, JGTO)
    Tour('CH_AMERICAS', 'Challenger Tour Americas', 2, 'pro', (('USA', 9), ('Canada', .5), ('Colombia', .5), ('Mexico', .5)),
         _window((4, 45)), 26, field=156, prestige=61, purse=1_000_000, cut=PRO_CUTS),
    Tour('CH_EUROPE', 'Challenger Tour Europe', 2, 'pro',
         (('Spain', 2), ('France', 1.2), ('Germany', 1.2), ('Sweden', 1), ('Denmark', .8), ('Italy', 1),
          ('Czechia', .5), ('Austria', .6), ('Netherlands', .6), ('England', 1), ('Scotland', .6), ('Kenya', .5),
          ('South Africa', .5), ('Oman', .4)), _window((10, 46)), 26, field=156, prestige=59, purse=400_000, cut=PRO_CUTS),
    Tour('CH_ASIA', 'Asian Challenger Tour', 2, 'pro',
         (('Thailand', 2), ('Malaysia', 1), ('Philippines', 1), ('Indonesia', .8), ('Taiwan', .8), ('Vietnam', .6),
          ('Singapore', .4), ('Saudi Arabia', .5)), _window((1, 52)), 22, field=144, prestige=58, purse=1_000_000, cut=PRO_CUTS),
    Tour('CH_LATAM_CANADA', 'Latin America & Canada Tour', 2, 'pro',
         (('Mexico', 1), ('Argentina', 1), ('Brazil', .8), ('Chile', .6), ('Colombia', .6), ('Peru', .3), ('Canada', 2)),
         _window((6, 42)), 20, field=144, prestige=55, purse=250_000, cut=PRO_CUTS),
    Tour('CH_JAPAN', 'Japan Golf Tour', 2, 'pro', (('Japan', 1),), _window((14, 49)), 24, field=132,
         prestige=62, purse=1_200_000, cut=PRO_CUTS),
    # Tier 3 -- Regional tours (Sunshine, Australasia, KPGA, PGTI, China Tour, MENA Tour)
    Tour('RG_SOUTHERN_AFRICA', 'Southern Africa Tour', 3, 'pro',
         (('South Africa', 6), ('Zimbabwe', .5), ('Namibia', .4), ('Zambia', .4), ('Mauritius', .4), ('Kenya', .4)),
         _window((1, 14), (30, 52)), 26, formats=((72, .6), (54, .4)), field=144, prestige=45, purse=200_000, cut=PRO_CUTS),
    Tour('RG_AUSTRALASIA', 'Australasia Tour', 3, 'pro', (('Australia', 5), ('New Zealand', 1.2), ('Fiji', .3)),
         _window((1, 12), (38, 52)), 18, field=144, prestige=46, purse=300_000, cut=PRO_CUTS),
    Tour('RG_KOREA', 'Korea Tour', 3, 'pro', (('South Korea', 1),), _window((14, 44)), 20, field=144,
         prestige=48, purse=600_000, cut=PRO_CUTS),
    Tour('RG_INDIA', 'India Tour', 3, 'pro', (('India', 1),), _window((1, 14), (40, 52)), 20,
         formats=((72, .7), (54, .3)), field=126, prestige=40, purse=150_000, cut=PRO_CUTS),
    Tour('RG_CHINA', 'China Tour', 3, 'pro', (('China', 1),), _window((10, 46)), 16, field=120,
         prestige=40, purse=200_000, cut=PRO_CUTS),
    Tour('RG_MENA', 'Middle East & North Africa Tour', 3, 'pro',
         (('United Arab Emirates', 1), ('Morocco', 1), ('Egypt', .8), ('Oman', .5), ('Bahrain', .4), ('Qatar', .4)),
         _window((1, 16), (42, 52)), 14, formats=((54, .7), (72, .3)), field=120, prestige=38, purse=75_000, cut=PRO_CUTS),
    # Tier 4 -- Mini tours (independent pro circuits; open entry for a fee)
    *[Tour(k, n, 4, 'pro', c, w, e, formats=((54, .5), (36, .35), (72, .15)), field=f, per_week=pw,
           prestige=24, purse=60_000, eligibility='pro', cut={72: 50, 54: 40})
      for k, n, c, w, e, f, pw in (
          ('MN_US_SUNBELT', 'Sunbelt Mini Tour', (('USA', 1),), _window((1, 46)), 72, 96, 2),
          ('MN_US_DESERT', 'Desert Mini Tour', (('USA', 1),), _window((1, 16), (42, 52)), 44, 90, 2),
          ('MN_US_MIDWEST', 'Midwest Mini Tour', (('USA', 1),), _window((18, 40)), 40, 90, 2),
          ('MN_US_NORTHEAST', 'Northeast Mini Tour', (('USA', 1),), _window((20, 38)), 34, 90, 2),
          ('MN_CANADA', 'Canadian Pro Circuit', (('Canada', 1),), _window((20, 38)), 14, 78, 1),
          ('MN_UK_IRELAND', 'UK & Ireland Pro Circuit', (('England', 3), ('Scotland', 1.5), ('Ireland', 1), ('Wales', .6)),
           _window((14, 40)), 36, 96, 2),
          ('MN_NORDIC', 'Nordic Pro League', (('Sweden', 2), ('Denmark', 1.5), ('Norway', .8), ('Finland', .8)),
           _window((18, 38)), 24, 90, 2),
          ('MN_ALPS', 'Alps Pro Tour', (('Austria', 1), ('Switzerland', 1), ('Italy', 1.5), ('France', 1), ('Spain', .5)),
           _window((10, 42)), 28, 96, 1),
          ('MN_IBERIA', 'Iberian Pro Tour', (('Spain', 2), ('Portugal', 1)), _window((1, 52)), 16, 90, 1),
          ('MN_GERMANY', 'German Pro Tour', (('Germany', 3), ('Netherlands', 1), ('Czechia', .6), ('Poland', .5), ('Turkey', .5)),
           _window((10, 44)), 24, 90, 1),
          ('MN_SE_ASIA', 'Southeast Asia Pro Series', (('Thailand', 2), ('Malaysia', 1), ('Philippines', 1), ('Vietnam', .6)),
           _window((1, 52)), 16, 90, 1),
          ('MN_EAST_AFRICA', 'East Africa Pro Circuit', (('Kenya', 2), ('Zambia', .5), ('Zimbabwe', .5)),
           _window((1, 52)), 8, 72, 1),
          ('MN_AUSTRALIA', 'Australian State Pro Series', (('Australia', 1),), _window((1, 14), (38, 52)), 10, 90, 1),
          ('MN_SOUTHERN_CONE', 'Southern Cone Pro Series', (('Argentina', 2), ('Chile', 1), ('Brazil', 1)),
           _window((1, 16), (40, 52)), 8, 78, 1),
          ('MN_MEXICO_CARIBBEAN', 'Mexico & Caribbean Pro Circuit', (('Mexico', 2), ('Colombia', .6)),
           _window((1, 52)), 8, 78, 1),
          ('MN_JAPAN', 'Japan Challenge Circuit', (('Japan', 1),), _window((14, 46)), 20, 96, 1),
      )],
    # Tier 5 -- College (regular seasons; post-season events are anchors)
    Tour('CO_US_D1', 'US College Division I', 5, 'college', (('USA', 1),), _window((36, 46), (6, 16)), 64,
         formats=((54, .85), (36, .15)), field=84, per_week=4, prestige=34, eligibility='college'),
    Tour('CO_US_SMALL', 'US Small College Golf', 5, 'college', (('USA', 1),), _window((36, 45), (6, 16)), 32,
         formats=((54, .6), (36, .4)), field=72, per_week=2, prestige=22, eligibility='college'),
    Tour('CO_INTL', 'International University Golf', 5, 'college',
         (('England', 1), ('Scotland', .6), ('Spain', .6), ('France', .5), ('Japan', 1), ('South Korea', .8),
          ('Australia', .8), ('Canada', .6)), _window((10, 22), (36, 46)), 24, formats=((54, .6), (36, .4)),
         field=120, per_week=2, prestige=24, eligibility='college'),
    # Tier 6 -- Amateur regional series: local club, county, state and regional events in every golfing
    # country of the region, in proportion to the size of its golf scene (local_allocation)
    *[Tour(k, n, 6, 'amateur', _local_countries(r), _window((1, 52)), sum(local_allocation(r, 'amateur').values()),
           formats=((18, .4), (36, .4), (54, .17), (72, .03)), field=f, per_week=LOCAL_PER_WEEK, prestige=18,
           eligibility='amateur', cut={72: 50, 54: 50})
      for k, n, r, f in (
          ('AM_NORTH_AMERICA', 'North American Amateur Series', ('North America',), 96),
          ('AM_EUROPE', 'European Amateur Series', ('Europe',), 96),
          ('AM_ASIA', 'Asian Amateur Series', ('Asia', 'Middle East'), 90),
          ('AM_OCEANIA', 'Oceania Amateur Series', ('Oceania',), 90),
          ('AM_AFRICA', 'African Amateur Series', ('Africa',), 84),
          ('AM_LATAM', 'Latin American Amateur Series', ('Latin America',), 84),
      )],
    # Tier 8 -- Club professionals' regional circuits: one-day section events and pro-ams on Mondays and
    # Tuesdays (club pros work weekends) in every golfing country of the region, for its club professionals
    *[Tour(k, n, 8, 'club_pro', _local_countries(r), _window((1, 52)), sum(local_allocation(r, 'club_pro').values()),
           formats=((18, .7), (36, .3)), field=f, per_week=LOCAL_PER_WEEK, prestige=22, purse=p,
           eligibility='club_pro', days={18: 'Mon', 36: 'Mon-Tue'})
      for k, n, r, f, p in (
          ('CP_NORTH_AMERICA', 'North American Club Professional Series', ('North America',), 84, 25_000),
          ('CP_EUROPE', 'European Club Professional Series', ('Europe',), 72, 20_000),
          ('CP_ASIA', 'Asian Club Professional Series', ('Asia', 'Middle East'), 72, 15_000),
          ('CP_OCEANIA', 'Oceania Club Professional Series', ('Oceania',), 72, 15_000),
          ('CP_AFRICA', 'African Club Professional Series', ('Africa',), 60, 10_000),
          ('CP_LATAM', 'Latin American Club Professional Series', ('Latin America',), 60, 10_000),
      )],
)
TOUR_BY_KEY = {t.key: t for t in TOURS}
LOCAL_CIRCUITS = {'AM_NORTH_AMERICA': (('North America',), 'amateur'), 'AM_EUROPE': (('Europe',), 'amateur'),
                  'AM_ASIA': (('Asia', 'Middle East'), 'amateur'), 'AM_OCEANIA': (('Oceania',), 'amateur'),
                  'AM_AFRICA': (('Africa',), 'amateur'), 'AM_LATAM': (('Latin America',), 'amateur'),
                  'CP_NORTH_AMERICA': (('North America',), 'club_pro'), 'CP_EUROPE': (('Europe',), 'club_pro'),
                  'CP_ASIA': (('Asia', 'Middle East'), 'club_pro'), 'CP_OCEANIA': (('Oceania',), 'club_pro'),
                  'CP_AFRICA': (('Africa',), 'club_pro'), 'CP_LATAM': (('Latin America',), 'club_pro')}

# ---------------------------------------------------------------------------------------------
# Major venues
# ---------------------------------------------------------------------------------------------
MAJOR_VENUES = {
    'TOUR_MASTERS': ('USA', ('Athens, Georgia',), 'fixed'),          # Georgia National, every year
    'PREMIER_TOUR_CHAMPIONSHIP': ('USA', ('Kiawah Island, South Carolina', 'Rochester, New York', 'Tulsa, Oklahoma',
                                          'Louisville, Kentucky', 'Kohler, Wisconsin', 'San Francisco, California',
                                          'Charlotte, North Carolina', 'Bethesda, Maryland'), 'rotating'),
    'USA_OPEN': ('USA', ('Pinehurst, North Carolina', 'Southampton, New York', 'Pittsburgh, Pennsylvania',
                         'Monterey, California', 'Philadelphia, Pennsylvania', 'Boston, Massachusetts',
                         'Los Angeles, California', 'Seattle, Washington', 'Bandon, Oregon'), 'rotating'),
    'BRITANNIA_OPEN': ('Scotland', ('St Andrews', 'Carnoustie', 'Troon', 'North Berwick', 'Southport', 'Hoylake',
                                    'Sandwich', 'Portrush'), 'rotating'),
}
MAJOR_FIELDS = {'TOUR_MASTERS': (90, 50), 'PREMIER_TOUR_CHAMPIONSHIP': (156, 70), 'USA_OPEN': (156, 60),
                'BRITANNIA_OPEN': (156, 70)}

# ---------------------------------------------------------------------------------------------
# The 36 Premier Tour events: (tour, week or None, category, name, country, city or None, field)
# Flagship 8, standard 20, opportunity 8 (four of them in the weeks straight after majors).
# ---------------------------------------------------------------------------------------------
PREMIER_EVENTS = (
    # Americas: 4 flagship, 8 standard, 4 opportunity
    ('PT_AMERICAS', 6, 'flagship', 'Pacific Coast Pro-Am', 'USA', 'Monterey, California', 156),
    ('PT_AMERICAS', 11, 'flagship', 'Premier Players Championship', 'USA', 'Jacksonville, Florida', 144),
    ('PT_AMERICAS', 22, 'flagship', 'Heartland Invitational', 'USA', 'Columbus, Ohio', 120),
    ('PT_AMERICAS', 45, 'flagship', 'Premier Tour Finals', 'USA', 'Atlanta, Georgia', 30),
    ('PT_AMERICAS', 19, 'opportunity', 'Gulf Coast Classic', 'USA', None, 156),
    ('PT_AMERICAS', 26, 'opportunity', 'Great Lakes Open', 'USA', None, 156),
    ('PT_AMERICAS', 2, 'opportunity', 'Island Championship', 'USA', 'Honolulu, Hawaii', 144),
    ('PT_AMERICAS', 41, 'opportunity', 'Autumn Classic', 'USA', None, 144),
    ('PT_AMERICAS', 23, 'national_open', 'Canada Open', 'Canada', None, 156),
    ('PT_AMERICAS', 9, 'national_open', 'Mexico Open', 'Mexico', None, 144),
    *[('PT_AMERICAS', None, 'standard', n, 'USA', None, 144) for n in (
        'Desert Classic', 'Texas Open', 'Carolina Championship', 'Southern Invitational', 'Pacific Northwest Open',
        'Mid-Atlantic Championship')],
    # Europe: 3 flagship, 7 standard, 3 opportunity
    ('PT_EUROPE', 29, 'flagship', 'Scotland Open', 'Scotland', None, 156),
    ('PT_EUROPE', 38, 'flagship', 'European Championship', 'England', 'Virginia Water', 156),
    ('PT_EUROPE', 47, 'flagship', 'Desert Tour Championship', 'United Arab Emirates', 'Dubai', 50),
    ('PT_EUROPE', 26, 'opportunity', 'Nordic Masters', 'Sweden', None, 156),
    ('PT_EUROPE', 31, 'opportunity', 'Netherlands Open', 'Netherlands', None, 156),
    ('PT_EUROPE', 10, 'opportunity', 'Kenya Open', 'Kenya', None, 156),
    ('PT_EUROPE', 50, 'national_open', 'South Africa Open', 'South Africa', None, 156),
    ('PT_EUROPE', 37, 'national_open', 'Ireland Open', 'Ireland', None, 156),
    ('PT_EUROPE', 40, 'national_open', 'Spain Open', 'Spain', None, 156),
    ('PT_EUROPE', 39, 'national_open', 'France Open', 'France', None, 144),
    *[('PT_EUROPE', None, 'standard', n, c, None, 144) for n, c in (
        ('Gulf Desert Classic', 'United Arab Emirates'), ('German Masters', 'Germany'), ('Italian Championship', 'Italy'))],
    # Asia-Pacific: 1 flagship, 5 standard, 1 opportunity
    ('PT_ASIA_PACIFIC', 49, 'flagship', 'Australia Open', 'Australia', None, 156),
    ('PT_ASIA_PACIFIC', 44, 'opportunity', 'Singapore Classic', 'Singapore', 'Singapore', 144),
    ('PT_ASIA_PACIFIC', 12, 'national_open', 'India Open', 'India', None, 144),
    *[('PT_ASIA_PACIFIC', None, 'standard', n, c, None, 144) for n, c in (
        ('Japan Premier Championship', 'Japan'), ('Korea Championship', 'South Korea'),
        ('China Masters', 'China'), ('Sandbelt Championship', 'Australia'))],
)
PREMIER_CLASS = {'flagship': 'flagship', 'standard': 'standard', 'national_open': 'standard', 'opportunity': 'opportunity'}
PREMIER_TERMS = {'flagship': (93, 16_000_000), 'standard': (81, 10_000_000), 'opportunity': (64, 5_500_000)}

# National opens hosted by Challenger / Regional tours: (tour, week or None, country, holes)
NATIONAL_OPENS = (
    ('CH_JAPAN', 42, 'Japan', 72), ('RG_KOREA', 26, 'South Korea', 72), ('RG_AUSTRALASIA', 10, 'New Zealand', 72),
    ('CH_ASIA', None, 'Thailand', 72), ('CH_ASIA', None, 'Malaysia', 72), ('CH_ASIA', None, 'Philippines', 72),
    ('CH_ASIA', None, 'Indonesia', 72), ('CH_ASIA', None, 'Taiwan', 72), ('CH_ASIA', None, 'Vietnam', 72),
    ('RG_CHINA', None, 'China', 72), ('CH_EUROPE', None, 'Portugal', 72), ('CH_EUROPE', None, 'Czechia', 72),
    ('CH_EUROPE', None, 'Austria', 72), ('CH_EUROPE', None, 'Italy', 72), ('CH_EUROPE', None, 'Germany', 72),
    ('CH_EUROPE', None, 'Denmark', 72), ('CH_EUROPE', None, 'Sweden', 72), ('CH_EUROPE', None, 'Wales', 72),
    ('CH_EUROPE', None, 'England', 72), ('MN_NORDIC', None, 'Norway', 54), ('MN_NORDIC', None, 'Finland', 54),
    ('MN_GERMANY', None, 'Poland', 54), ('MN_GERMANY', None, 'Turkey', 54), ('MN_ALPS', None, 'Switzerland', 54),
    ('MN_GERMANY', None, 'Belgium', 54), ('MN_UK_IRELAND', None, 'Northern Ireland', 72),
    ('CH_LATAM_CANADA', None, 'Argentina', 72), ('CH_LATAM_CANADA', None, 'Brazil', 72),
    ('CH_LATAM_CANADA', None, 'Chile', 72), ('CH_LATAM_CANADA', None, 'Colombia', 72), ('CH_LATAM_CANADA', None, 'Peru', 72),
    ('RG_SOUTHERN_AFRICA', None, 'Zimbabwe', 72), ('RG_SOUTHERN_AFRICA', None, 'Namibia', 72),
    ('RG_SOUTHERN_AFRICA', None, 'Zambia', 72), ('RG_SOUTHERN_AFRICA', None, 'Mauritius', 72),
    ('RG_MENA', None, 'Morocco', 72), ('RG_MENA', None, 'Egypt', 72), ('RG_MENA', None, 'Qatar', 72),
    ('RG_MENA', None, 'Saudi Arabia', 72), ('RG_MENA', None, 'Oman', 72), ('RG_MENA', None, 'Bahrain', 72),
    ('MN_EAST_AFRICA', None, 'Nigeria', 54), ('RG_INDIA', None, 'Singapore', 72),
    ('RG_AUSTRALASIA', None, 'Fiji', 72), ('CH_AMERICAS', None, 'Canada', 72),
)


# Each circuit's season-ending championship (see docs/CIRCUIT_FLAGSHIPS.md), by tier:
# (field, holes, purse multiple of the tour's typical purse, prestige above the tour's events).
# Fields come from the circuit's own order of merit (Season.circuit_championship); circuits that already
# have their championship elsewhere in the calendar are listed in CIRCUIT_FLAGSHIP_ELSEWHERE.
CIRCUIT_FLAGSHIPS = {2: (70, 72, 2.0, 14), 3: (60, 72, 1.8, 14), 4: (50, 54, 2.0, 12), 6: (72, 54, 0.0, 16),
                     8: (60, 36, 2.0, 16)}
CIRCUIT_FLAGSHIP_ELSEWHERE = {'CP_NORTH_AMERICA': 'CLUB_PRO_CHAMPIONSHIP'}
FLAGSHIP_LAST_WEEK = 48                 # year-round circuits finish their season before the holidays


def _anchor_specs():
    """Fixed-week anchors outside the Premier Tour: (series_id, name, tour, tier, kind, category, holes,
    field, week, eligibility, country, cities, policy, days, match_play, prestige, sites, cut_top)."""
    UK_LINKS = ('St Andrews', 'Carnoustie', 'Troon', 'North Berwick', 'Southport', 'Hoylake', 'Sandwich',
                'Portrush', 'Newcastle, County Down', 'Ballybunion', 'Tenby', 'Aberdeen')
    US_AM = ('Pinehurst, North Carolina', 'Southampton, New York', 'Bandon, Oregon', 'Chicago, Illinois',
             'Kohler, Wisconsin', 'Omaha, Nebraska', 'Bethesda, Maryland', 'San Francisco, California')
    yield ('LATIN_AMERICA_AMATEUR', 'Latin America Amateur Championship', 'AMATEUR', 6, 'amateur', 'elite_amateur',
           72, 108, 3, 'amateur', 'Argentina', ('Buenos Aires', 'Santiago', 'Mexico City', 'Bogotá', 'Lima',
                                                  'São Paulo', 'Cancún'), 'rotating', 'Thu-Sun', False, 72, 1, 50)
    yield ('AFRICA_AMATEUR', 'Africa Amateur Championship', 'AMATEUR', 6, 'amateur', 'elite_amateur', 72, 96, 9,
           'amateur', 'South Africa', ('Johannesburg', 'Cape Town', 'Nairobi', 'Rabat', 'Durban', 'Windhoek'),
           'rotating', 'Thu-Sun', False, 62, 1, 50)
    # Club professionals qualify for their championship through 36-hole sectionals (a competition)
    yield ('CLUB_PRO_SECTIONALS', 'Club Professional Championship Sectional Qualifying', 'QUALIFYING', 7, 'qualifying',
           'qualifier', 36, 90, 12, 'club_pro', 'USA', None, 'rotating', 'Mon', False, 25, 4, 0)
    yield ('CLUB_PRO_CHAMPIONSHIP', 'Club Professional Championship', 'QUALIFYING', 7, 'qualifying', 'qualifier',
           72, 156, 16, 'club_pro', 'USA', ('Austin, Texas', 'Palm Springs, California', 'Myrtle Beach, South Carolina',
                                           'Tucson, Arizona', 'Fort Worth, Texas'), 'rotating', 'Thu-Sun', False, 50, 1, 70)
    yield ('BRITANNIA_AMATEUR', 'Britannia Amateur Championship', 'AMATEUR', 6, 'amateur', 'elite_amateur', 36, 144, 23,
           'amateur', 'Scotland', UK_LINKS, 'rotating', 'Mon-Sun', True, 78, 1, 0)
    yield ('EUROPEAN_AMATEUR', 'European Amateur Championship', 'AMATEUR', 6, 'amateur', 'elite_amateur', 72, 144, 27,
           'amateur', 'Spain', ('Madrid', 'Copenhagen', 'Prague', 'Vienna', 'Stockholm', 'Lisbon', 'Hamburg', 'Milan'),
           'rotating', 'Tue-Fri', False, 66, 1, 60)
    # The USA Amateur's open route: 36-hole qualifying at eight sites three weeks before (USA_AMATEUR_EXEMPT
    # are exempt; Season.usa_amateur_field fills the rest of the field from here)
    yield ('USA_AMATEUR_QUALIFYING', 'USA Amateur Qualifying', 'QUALIFYING', 7, 'qualifying', 'qualifier', 36, 78, 30,
           'amateur', 'USA', None, 'rotating', 'Mon', False, 30, 8, 0)
    yield ('USA_AMATEUR', 'USA Amateur Championship', 'AMATEUR', 6, 'amateur', 'elite_amateur', 36, 156, 33,
           'amateur', 'USA', US_AM, 'rotating', 'Mon-Sun', True, 80, 1, 0)
    yield ('USA_MID_AMATEUR', 'USA Mid-Amateur Championship', 'AMATEUR', 6, 'amateur', 'elite_amateur', 36, 132, 38,
           'mid_amateur', 'USA', ('Atlanta, Georgia', 'Denver, Colorado', 'Hartford, Connecticut', 'Nashville, Tennessee',
                                  'Scottsdale, Arizona'), 'rotating', 'Mon-Sun', True, 55, 1, 0)
    yield ('ASIA_PACIFIC_AMATEUR', 'Asia-Pacific Amateur Championship', 'AMATEUR', 6, 'amateur', 'elite_amateur', 72, 120,
           43, 'amateur', 'Japan', ('Tokyo', 'Melbourne', 'Singapore', 'Seoul', 'Shanghai', 'Bangkok', 'Auckland', 'Dubai'),
           'rotating', 'Thu-Sun', False, 70, 1, 60)
    # College post-season (US)
    for i in range(8):
        yield (f'CONFERENCE_CHAMPIONSHIP_{i + 1}', f'Conference Championship {i + 1}', 'CO_US_D1', 5, 'college',
               'college_postseason', 54, 60, 17, 'college', 'USA', None, 'rotating', 'Fri-Sun', False, 40, 1, 0)
    for i in range(4):
        yield (f'COLLEGE_REGIONAL_{i + 1}', f'College Regional {i + 1}', 'CO_US_D1', 5, 'college', 'college_postseason',
               54, 75, 20, 'college', 'USA', None, 'rotating', 'Mon-Wed', False, 48, 1, 0)
    yield ('COLLEGE_NATIONAL_CHAMPIONSHIP', 'College National Championship', 'CO_US_D1', 5, 'college',
           'college_postseason', 72, 156, 21, 'college', 'USA', ('Scottsdale, Arizona', 'Fort Worth, Texas',
                                                                 'Atlanta, Georgia', 'San Diego, California'),
           'rotating', 'Thu-Sun', False, 62, 1, 75)
    yield ('SMALL_COLLEGE_CHAMPIONSHIP', 'Small College National Championship', 'CO_US_SMALL', 5, 'college',
           'college_postseason', 72, 120, 20, 'college', 'USA', None, 'rotating', 'Tue-Fri', False, 38, 1, 60)
    yield ('INTL_UNIVERSITY_CHAMPIONSHIP', 'World University Championship', 'CO_INTL', 5, 'college',
           'college_postseason', 72, 96, 28, 'college', 'England', None, 'rotating', 'Thu-Sun', False, 42, 1, 0)
    # USA Open qualifying: 18-hole local qualifying, then 36-hole final qualifying (one day)
    for wk in (19, 20, 21):
        yield (f'USA_OPEN_LOCAL_W{wk}', f'USA Open Local Qualifying (week {wk})', 'QUALIFYING', 7, 'qualifying',
               'qualifier', 18, 90, wk, 'open', 'USA', None, 'rotating', 'Mon', False, 30, 4, 0)
    yield ('USA_OPEN_FINAL_INTL', 'USA Open Final Qualifying (England & Japan)', 'QUALIFYING', 7, 'qualifying',
           'qualifier', 36, 90, 22, 'open', 'England', ('Virginia Water', 'Tokyo'), 'fixed', 'Mon', False, 45, 2, 0)
    yield ('USA_OPEN_FINAL', 'USA Open Final Qualifying', 'QUALIFYING', 7, 'qualifying', 'qualifier', 36, 96, 23,
           'open', 'USA', ('Columbus, Ohio', 'Dallas, Texas', 'Atlanta, Georgia', 'Rochester, New York',
                           'Seattle, Washington', 'Charlotte, North Carolina', 'Boston, Massachusetts', 'Toronto, Ontario'),
           'fixed', 'Mon', False, 45, 8, 0)
    # Britannia Open qualifying: 18-hole regional qualifying, then 36-hole final qualifying (one day)
    for wk in (26, 27):
        yield (f'BRITANNIA_REGIONAL_W{wk}', f'Britannia Open Regional Qualifying (week {wk})', 'QUALIFYING', 7,
               'qualifying', 'qualifier', 18, 84, wk, 'open', 'England', None, 'rotating', 'Mon', False, 30, 4, 0)
    yield ('BRITANNIA_FINAL', 'Britannia Open Final Qualifying', 'QUALIFYING', 7, 'qualifying', 'qualifier', 36, 72, 28,
           'open', 'England', ('Southport', 'Woodhall Spa', 'Troon', 'Sandwich'), 'fixed', 'Tue', False, 45, 4, 0)
    # Tour qualifying schools
    for sid, name, wk, cc, sites, field_n in (
            ('PT_QSCHOOL_PRE', 'Premier Tour Q-School Pre-Qualifying', 40, 'USA', 4, 78),
            ('PT_QSCHOOL_FIRST', 'Premier Tour Q-School First Stage', 42, 'USA', 6, 78),
            ('PT_QSCHOOL_SECOND', 'Premier Tour Q-School Second Stage', 46, 'USA', 4, 78),
            ('PT_QSCHOOL_FINAL', 'Premier Tour Q-School Final Stage', 50, 'USA', 1, 156),
            ('EU_QSCHOOL_FIRST', 'Premier Tour Europe Q-School First Stage', 37, 'Spain', 4, 84),
            ('EU_QSCHOOL_SECOND', 'Premier Tour Europe Q-School Second Stage', 44, 'Spain', 4, 78),
            ('EU_QSCHOOL_FINAL', 'Premier Tour Europe Q-School Final Stage', 48, 'Spain', 1, 156),
            ('JP_QSCHOOL_FINAL', 'Japan Golf Tour Q-School', 48, 'Japan', 1, 120),
            ('ASIA_QSCHOOL_FINAL', 'Asian Challenger Tour Q-School', 2, 'Thailand', 1, 156)):
        yield (sid, name, 'QUALIFYING', 7, 'qualifying', 'q_school', 72, field_n, wk, 'pro', cc, None, 'rotating',
               'Thu-Sun', False, 52, sites, 0)


class WorldCalendar:
    """Builds the permanent series list once; `editions(year)` gives that year's events."""

    def __init__(self, seed=2027):
        self.seed = seed
        self.series = []
        self._tour_weeks = defaultdict(Counter)        # tour -> week -> events
        self._build()
        self.by_id = {s.series_id: s for s in self.series}
        if len(self.by_id) != len(self.series):
            raise AssertionError('duplicate series id')

    # -- helpers ---------------------------------------------------------------------------------
    def _cities_for(self, country, week=None, n=6, key=''):
        cities = [c for c in CITIES_BY_COUNTRY[country] if week is None or week in season_weeks(c)]
        if not cities:
            raise ValueError(f'No city in {country} can host golf in week {week}')
        r = _rng(self.seed, 'cities', key)
        r.shuffle(cities)
        return tuple(c.name for c in cities[:n])

    def _add(self, s):
        in_season = tuple(c for c in s.cities if s.week in season_weeks(CITY_BY_NAME[c]))
        if not in_season:
            raise ValueError(f'{s.name}: no host city in season in week {s.week}')
        if in_season != s.cities:
            s = replace(s, cities=in_season)
        if s.week in MAJOR_WEEKS and s.tier == 1:
            raise AssertionError(f'{s.name} scheduled in major week {s.week}')
        self.series.append(s)
        self._tour_weeks[s.tour][s.week] += 1

    def _free_weeks(self, tour, windows, per_week, countries):
        out = []
        for w in range(1, 53):
            if (w in MAJOR_WEEKS and TOUR_BY_KEY[tour].tier == 1 or not _in_window(w, windows)
                    or self._tour_weeks[tour][w] >= per_week):
                continue
            if any(w in season_weeks(c) for country, _ in countries for c in CITIES_BY_COUNTRY[country]):
                out.append(w)
        return out

    def _pick_country(self, countries, week, key):
        ok = [(c, wt) for c, wt in countries if any(week in season_weeks(x) for x in CITIES_BY_COUNTRY[c])]
        r = _rng(self.seed, 'country', key)
        return r.choices([c for c, _ in ok], weights=[wt for _, wt in ok])[0]

    def _spread(self, weeks, n, key):
        """Choose n weeks spread evenly through `weeks` (deterministic, small jitter)."""
        if n > len(weeks):
            raise ValueError(f'{key}: needs {n} weeks, only {len(weeks)} available')
        r = _rng(self.seed, 'spread', key)
        step = len(weeks) / n
        picks = sorted({weeks[min(len(weeks) - 1, int(i * step + r.random() * step * 0.6))] for i in range(n)})
        rest = [w for w in weeks if w not in picks]
        while len(picks) < n:
            picks.append(rest.pop(r.randrange(len(rest))))
        return sorted(picks)

    def _local_events(self, tour, regions, kind):
        """A local circuit's events: each country's allocation spread through the weeks its golf season
        allows, country by country (largest first), within the circuit's weekly capacity."""
        alloc = local_allocation(regions, kind)
        free = self._free_weeks(tour.key, tour.weeks, tour.per_week, tour.countries)
        room = {w: tour.per_week - self._tour_weeks[tour.key][w] for w in free}
        r = _rng(self.seed, 'formats', tour.key)
        i = 0
        for country in sorted(alloc, key=lambda c: (-alloc[c], c)):
            weeks = [w for w in free if room[w] > 0 and any(w in season_weeks(c) for c in CITIES_BY_COUNTRY[country])]
            if not weeks:
                continue
            if kind == 'club_pro':
                # the region's club pros share one circuit: a week the circuit already uses only when
                # the country's season has no emptier ones left
                for load in sorted({tour.per_week - room[w] for w in weeks}):
                    spread = [w for w in weeks if tour.per_week - room[w] <= load]
                    if len(spread) >= alloc[country]:
                        weeks = spread
                        break
            per = -(-alloc[country] // len(weeks))           # a busy golf country can hold several a week
            slots = [w for w in weeks for _ in range(min(room[w], per))]
            n = min(alloc[country], len(slots))
            for week in (slots[int((j + 0.5) * len(slots) / n)] for j in range(n)):
                room[week] -= 1
                i += 1
                holes = r.choices([h for h, _ in tour.formats], weights=[w for _, w in tour.formats])[0]
                cut_top = tour.cut.get(holes, 0)
                if kind == 'club_pro':                        # one-day pro-ams and two-day section events
                    prestige = tour.prestige + {18: -3, 36: -2}[holes]
                    purse = int(tour.purse * {18: .6, 36: .7}[holes])
                else:
                    prestige = tour.prestige + {18: -6, 36: -2, 54: 3, 72: 6}[holes]
                    purse = int(tour.purse * {18: .45, 36: .7, 54: 1.0, 72: 1.35}[holes]) if tour.purse else 0
                sid = f'{tour.key}_{i:03d}'
                self._add(Series(sid, f'{tour.name} Event {i} ({country})', tour.key, tour.tier, tour.kind,
                                 'regular', holes, tour.field, week, tour.eligibility, country,
                                 self._cities_for(country, week, n=4, key=sid), 'rotating',
                                 36 if cut_top else 0, cut_top, days=tour.days.get(holes, ''),
                                 prestige=prestige, purse=purse))

    # -- the cascade -----------------------------------------------------------------------------
    def _build(self):
        # 1. Majors
        for week, (sid, name) in MAJORS.items():
            country, cities, policy = MAJOR_VENUES[sid]
            field_n, cut = MAJOR_FIELDS[sid]
            self._add(Series(sid, name, 'MAJORS', 0, 'major', 'major', 72, field_n, week, 'invitation', country,
                             cities, policy, 36, cut, 'Thu-Sun', prestige=100, purse=22_000_000, anchored=True))
        # 2. Fixed-week anchors
        for (sid, name, tour, tier, kind, cat, holes, field_n, week, elig, country, cities, policy, days, match,
             prestige, sites, cut_top) in _anchor_specs():
            cities = cities or self._cities_for(country, week, key=sid)
            self._add(Series(sid, name, tour, tier, kind, cat, holes, field_n, week, elig, country, cities, policy,
                             36 if cut_top else 0, cut_top, days, match, prestige, 0, sites, anchored=True))
        # 3. Premier Tour
        for tour_key, week, cat, name, country, city, field_n in PREMIER_EVENTS:
            tour = TOUR_BY_KEY[tour_key]
            if week is None:
                free = [w for w in self._free_weeks(tour_key, tour.weeks, 1, ((country, 1),))]
                week = self._spread(free, 1, f'{tour_key}:{name}')[0]
            if self._tour_weeks[tour_key][week]:
                raise AssertionError(f'{tour_key} already has an event in week {week}')
            prestige, purse = PREMIER_TERMS[PREMIER_CLASS[cat]]
            if cat == 'national_open':
                prestige = min(97, prestige + 6)
            cities = (city,) if city else self._cities_for(country, week, key=name)
            sid = 'PT_' + name.upper().replace(' ', '_').replace('-', '_')
            self._add(Series(sid, name, tour_key, 1, 'premier', cat, 72, field_n, week, 'members', country, cities,
                             'fixed' if city else 'rotating', 36 if field_n > 80 else 0,
                             tour.cut[72] if field_n > 80 else 0, 'Thu-Sun', prestige=prestige, purse=purse,
                             anchored=cat in ('flagship', 'opportunity') or week is not None))
        # 3b. National opens on lower tours (fixed week where given, otherwise flexible)
        for tour_key, week, country, holes in NATIONAL_OPENS:
            tour = TOUR_BY_KEY[tour_key]
            if week is None:
                free = self._free_weeks(tour_key, tour.weeks, tour.per_week, ((country, 1),))
                week = self._spread(free, 1, f'NO:{country}')[0]
            sid = 'NATIONAL_OPEN_' + country.upper().replace(' ', '_')
            prestige = min(90, tour.prestige + 10)
            self._add(Series(sid, f'{country} Open', tour_key, tour.tier, 'pro', 'national_open', holes,
                             max(tour.field, 120), week, 'open_pro', country, self._cities_for(country, week, key=sid),
                             'rotating', 36, tour.cut.get(holes, 60), prestige=prestige,
                             purse=int(tour.purse * 1.4), anchored=True))
        # 3c. Each circuit's championship, in the last weeks of its season
        for tour in TOURS:
            spec = CIRCUIT_FLAGSHIPS.get(tour.tier)
            if spec is None or tour.key in CIRCUIT_FLAGSHIP_ELSEWHERE:
                continue
            field_n, holes, purse_x, bonus = spec
            # professional circuits finish before (or between) the Q-School stages their players need
            qs = {x.week for x in self.series if x.category == 'q_school'} if tour.tier in (2, 3, 4) else set()
            free = [w for w in self._free_weeks(tour.key, tour.weeks, tour.per_week, tour.countries)
                    if w <= FLAGSHIP_LAST_WEEK and w not in qs]
            lead = max(tour.countries, key=lambda c: c[1])[0]
            at_home = [w for w in free if any(w in season_weeks(c) for c in CITIES_BY_COUNTRY[lead])]
            # the last week of the season, in the circuit's main country when it is in season there
            # within the last two months; otherwise wherever the circuit is playing then
            if at_home and at_home[-1] >= free[-1] - 8:
                week, country = at_home[-1], lead
            else:
                week = free[-1]
                country = self._pick_country(tour.countries, week, f'{tour.key}:championship')
            sid = f'{tour.key}_CHAMPIONSHIP'
            name = (f'{tour.name.replace(" Series", "")} Championship' if tour.tier == 8 else
                    f'{tour.name} Championship')
            self._add(Series(sid, name, tour.key, tour.tier, tour.kind, 'circuit_championship', holes, field_n, week,
                             tour.eligibility, country, self._cities_for(country, week, n=4, key=sid), 'rotating',
                             prestige=min(90, tour.prestige + bonus), purse=int(tour.purse * purse_x),
                             days=tour.days.get(holes, ''), anchored=True))
        # 4-5. Remaining tour events
        for tour in TOURS:
            if tour.tier == 1:
                continue
            if tour.key in LOCAL_CIRCUITS:
                self._local_events(tour, *LOCAL_CIRCUITS[tour.key])
                continue
            already = sum(1 for s in self.series if s.tour == tour.key and s.category == 'national_open')
            n = tour.events - (already if tour.tier <= 4 else 0)
            free = self._free_weeks(tour.key, tour.weeks, tour.per_week, tour.countries)
            slots = [w for w in free for _ in range(tour.per_week - self._tour_weeks[tour.key][w])]
            weeks = self._spread(slots, n, tour.key) if tour.per_week == 1 else sorted(
                _rng(self.seed, 'slots', tour.key).sample(slots, n))
            r = _rng(self.seed, 'formats', tour.key)
            for i, week in enumerate(weeks, 1):
                holes = r.choices([h for h, _ in tour.formats], weights=[w for _, w in tour.formats])[0]
                country = self._pick_country(tour.countries, week, f'{tour.key}:{i}')
                cut_top = tour.cut.get(holes, 0)
                if tour.tier == 4 and cut_top and holes == 54:
                    cut_top = round(tour.field * 0.45)
                if kind == 'club_pro':                        # one-day pro-ams and two-day section events
                    prestige = tour.prestige + {18: -3, 36: -2}[holes]
                    purse = int(tour.purse * {18: .6, 36: .7}[holes])
                else:
                    prestige = tour.prestige + {18: -6, 36: -2, 54: 3, 72: 6}[holes]
                    purse = int(tour.purse * {18: .45, 36: .7, 54: 1.0, 72: 1.35}[holes]) if tour.purse else 0
                self._add(Series(f'{tour.key}_{i:02d}', f'{tour.name} Event {i}', tour.key, tour.tier, tour.kind,
                                 'regular', holes, tour.field, week, tour.eligibility, country,
                                 self._cities_for(country, week, n=4, key=f'{tour.key}{i}'), 'rotating',
                                 36 if cut_top else 0, cut_top, days=tour.days.get(holes, ''),
                                 prestige=prestige, purse=purse))
        # National amateur championships: one per country in its golf season
        for country, info in COUNTRIES.items():
            if info.golf < 0.3:
                continue
            weeks = sorted(set.union(*(season_weeks(c) for c in CITIES_BY_COUNTRY[country])))
            summer = [w for w in weeks if (2 <= w <= 9) == info.south and (26 <= w <= 36 or 2 <= w <= 9)]
            week = self._spread(summer or weeks, 1, f'NA:{country}')[0]
            sid = 'NATIONAL_AMATEUR_' + country.upper().replace(' ', '_')
            holes = 72 if info.golf >= 1 else 54
            self._add(Series(sid, f'{country} Amateur Championship', 'AMATEUR', 6, 'amateur', 'national_amateur',
                             holes, 120 if info.golf >= 2 else 96, week, 'amateur', country,
                             self._cities_for(country, week, key=sid), 'rotating', 36, 60,
                             prestige=45 + min(15, int(info.golf * 2)), anchored=True))

    # -- output ----------------------------------------------------------------------------------
    def editions(self, year):
        out = []
        for s in sorted(self.series, key=lambda s: (s.week, s.tier, s.series_id)):
            if s.venue_policy == 'fixed' or len(s.cities) == 1:
                city = s.cities[0]
            else:
                start = _rng(self.seed, 'rotation', s.series_id).randrange(len(s.cities))
                city = s.cities[(start + year) % len(s.cities)]
            out.append(Edition(year, s, city))
        return out

    def validate(self, year=2027):
        errors = []
        eds = self.editions(year)
        for w in range(1, 53):
            week_eds = [e for e in eds if e.week == w]
            if w in MAJOR_WEEKS:
                if sum(1 for e in week_eds if e.series.kind == 'major') != 1:
                    errors.append(f'Week {w}: major week must contain its major')
                if any(e.series.tier == 1 for e in week_eds):
                    errors.append(f'Week {w}: Premier Tour event in a major week')
        regular = Counter((s.tour, s.week) for s in self.series if s.category not in ('college_postseason',
                                                                                    'circuit_championship'))
        for (tour_key, w), n in regular.items():
            tour = TOUR_BY_KEY.get(tour_key)
            if tour and tour.tier == 1 and n > 1:
                errors.append(f'{tour_key} has {n} events in week {w}')
            elif tour and tour.tier > 1 and n > tour.per_week + 1:
                errors.append(f'{tour_key} overloaded in week {w} ({n} events)')
        for e in eds:
            if e.week not in season_weeks(CITY_BY_NAME[e.city]):
                errors.append(f'{e.series.name} in {e.city} out of season (week {e.week})')
            if e.series.holes not in (18, 36, 54, 72):
                errors.append(f'{e.series.name}: invalid length')
            if e.series.cut_top and e.series.holes < 54:
                errors.append(f'{e.series.name}: short event with a cut')
        prem = Counter(PREMIER_CLASS[s.category] for s in self.series if s.tier == 1)
        if prem != Counter(flagship=8, standard=20, opportunity=8):
            errors.append(f'Premier categories wrong: {dict(prem)}')
        for w in (19, 26, 31):
            if not any(s.week == w and s.category == 'opportunity' for s in self.series):
                errors.append(f'No opportunity event the week after a major (week {w})')
        return errors
