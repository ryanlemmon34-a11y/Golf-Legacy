"""Where people come from and where they live (see docs/RESIDENCE.md).

    nationality   Golfer.country (a coach's or caddie's .country): fixed for life, never changed by a
                  move. Eligibility, memberships, qualifying pools and national representation use it.
    birthplace    (country, state / province / equivalent), fixed at birth; None when unknown (people
                  from saves made before birthplaces were kept).
    residence     where they live now, at the same detail; it changes only by a recorded, dated move.
                  Travel costs, the appeal and proximity of events, drives to section events, travel
                  fatigue and which open qualifier site suits them start from it.

`Places` is the one authoritative record for every person, whatever their roles: a golfer who becomes
a coach or caddie keeps the same person id, so the same birthplace, residence and moves (no copy is
kept on the golfer or staff objects, so neither can go stale).

Moves
    college       a college golfer lives at their college base (US Division I and small colleges: a US
                  state; the International University tour: their own country if it hosts university
                  golf, else one that does). The college base is an abstraction, a state or country, not
                  a named university. College moves (arrival, transfer) cost the golfer nothing and are
                  never refused for money: the school pays.
    career        each winter a professional may move closer to the events they have a route to enter
                  (their tour's countries), or return home, weighing the travel they would save over the
                  next STAY_YEARS seasons against what money means to them (finance.money_unit: a broke
                  player feels every flight, a wealthy one hardly notices), the pull of their own country
                  (stronger the less adaptable they are), and the cost of the move (MOVE_COST, paid from
                  their own money -- savings, family and backers', after the usual reserve -- never on
                  credit; a move they cannot pay for is not made). The odds are smooth; after a
                  move they stay at least MIN_STAY seasons (no back-and-forth). Graduates and golfers
                  changing their life this winter decide at once, from wherever they live: graduation
                  does not send anyone home automatically.
    staff         a caddie who has carried one player's bag for two seasons may move to where that player
                  lives (hiring itself ignores where people live: touring caddies travel); a coach to where
                  most of their players live. Staff have no household finances: their moves cost nothing.
Nothing here grants a tour card, a membership or a qualifying right: those follow nationality and
results, wherever a golfer lives.
"""
from __future__ import annotations

import math
import random

from . import finance as FIN
from .geography import CITIES_BY_COUNTRY, CITY_BY_NAME, COUNTRIES

# State, province or equivalent of every city outside the USA and Canada (whose city names carry it).
_SUBDIVISION = {
    'Mexico City': 'Mexico City', 'Cancún': 'Quintana Roo', 'San José del Cabo': 'Baja California Sur',
    'Guadalajara': 'Jalisco', 'Monterrey': 'Nuevo León', 'São Paulo': 'São Paulo', 'Rio de Janeiro': 'Rio de Janeiro',
    'Florianópolis': 'Santa Catarina', 'Buenos Aires': 'Buenos Aires', 'Córdoba': 'Córdoba',
    'Mar del Plata': 'Buenos Aires Province', 'Santiago': 'Santiago Metropolitan', 'Viña del Mar': 'Valparaíso',
    'Bogotá': 'Bogotá', 'Medellín': 'Antioquia', 'Cartagena': 'Bolívar', 'Lima': 'Lima',
    'London': 'Greater London', 'Virginia Water': 'Surrey', 'Sunningdale': 'Berkshire', 'Southport': 'Merseyside',
    'Hoylake': 'Merseyside', 'Sandwich': 'Kent', 'Birmingham': 'West Midlands', 'Manchester': 'Greater Manchester',
    'Newcastle upon Tyne': 'Tyne and Wear', 'Bristol': 'Bristol', 'Woodhall Spa': 'Lincolnshire',
    'St Andrews': 'Fife', 'Edinburgh': 'City of Edinburgh', 'Glasgow': 'Glasgow', 'Carnoustie': 'Angus',
    'Troon': 'South Ayrshire', 'North Berwick': 'East Lothian', 'Gleneagles': 'Perth and Kinross',
    'Aberdeen': 'Aberdeen', 'Inverness': 'Highland', 'Dublin': 'County Dublin', 'Cork': 'County Cork',
    'Killarney': 'County Kerry', 'Galway': 'County Galway', 'Ballybunion': 'County Kerry',
    'Belfast': 'County Antrim', 'Portrush': 'County Antrim', 'Newcastle, County Down': 'County Down',
    'Cardiff': 'Cardiff', 'Newport': 'Newport', 'Tenby': 'Pembrokeshire', 'Madrid': 'Community of Madrid',
    'Barcelona': 'Catalonia', 'Marbella': 'Andalusia', 'Málaga': 'Andalusia', 'Valencia': 'Valencian Community',
    'Seville': 'Andalusia', 'Palma de Mallorca': 'Balearic Islands', 'Santa Cruz de Tenerife': 'Canary Islands',
    'Lisbon': 'Lisbon District', 'Faro': 'Faro District', 'Porto': 'Porto District', 'Paris': 'Île-de-France',
    'Bordeaux': 'Nouvelle-Aquitaine', 'Lyon': 'Auvergne-Rhône-Alpes', 'Nice': "Provence-Alpes-Côte d'Azur",
    'Biarritz': 'Nouvelle-Aquitaine', 'Munich': 'Bavaria', 'Hamburg': 'Hamburg', 'Berlin': 'Berlin',
    'Düsseldorf': 'North Rhine-Westphalia', 'Frankfurt': 'Hesse', 'Amsterdam': 'North Holland',
    'The Hague': 'South Holland', 'Antwerp': 'Antwerp', 'Brussels': 'Brussels-Capital',
    'Copenhagen': 'Capital Region of Denmark', 'Aarhus': 'Central Denmark', 'Stockholm': 'Stockholm County',
    'Gothenburg': 'Västra Götaland', 'Malmö': 'Skåne', 'Oslo': 'Oslo', 'Bergen': 'Vestland', 'Helsinki': 'Uusimaa',
    'Rome': 'Lazio', 'Milan': 'Lombardy', 'Turin': 'Piedmont', 'Vienna': 'Vienna', 'Salzburg': 'Salzburg',
    'Innsbruck': 'Tyrol', 'Geneva': 'Geneva', 'Zürich': 'Zürich', 'Crans-Montana': 'Valais', 'Prague': 'Prague',
    'Warsaw': 'Masovia', 'Gdańsk': 'Pomerania', 'Antalya': 'Antalya', 'Istanbul': 'Istanbul',
    'Dubai': 'Dubai', 'Abu Dhabi': 'Abu Dhabi', 'Ras Al Khaimah': 'Ras Al Khaimah', 'Doha': 'Doha',
    'Riyadh': 'Riyadh Province', 'Jeddah': 'Makkah Province', 'Manama': 'Capital Governorate',
    'Muscat': 'Muscat Governorate', 'Johannesburg': 'Gauteng', 'Pretoria': 'Gauteng', 'Cape Town': 'Western Cape',
    'Durban': 'KwaZulu-Natal', 'George': 'Western Cape', 'Sun City': 'North West', 'Gqeberha': 'Eastern Cape',
    'East London': 'Eastern Cape', 'Nairobi': 'Nairobi County', 'Mombasa': 'Mombasa County',
    'Nakuru': 'Nakuru County', 'Rabat': 'Rabat-Salé-Kénitra', 'Marrakesh': 'Marrakesh-Safi', 'Agadir': 'Souss-Massa',
    'Lagos': 'Lagos State', 'Abuja': 'Federal Capital Territory', 'Cairo': 'Cairo Governorate',
    'Sharm El Sheikh': 'South Sinai', 'Harare': 'Harare Province', 'Windhoek': 'Khomas', 'Lusaka': 'Lusaka Province',
    'Port Louis': 'Port Louis District', 'Tokyo': 'Tokyo', 'Chiba': 'Chiba', 'Yokohama': 'Kanagawa', 'Osaka': 'Osaka',
    'Kobe': 'Hyōgo', 'Nagoya': 'Aichi', 'Sapporo': 'Hokkaidō', 'Fukuoka': 'Fukuoka', 'Hiroshima': 'Hiroshima',
    'Sendai': 'Miyagi', 'Karuizawa': 'Nagano', 'Miyazaki': 'Miyazaki', 'Seoul': 'Seoul', 'Incheon': 'Incheon',
    'Busan': 'Busan', 'Jeju City': 'Jeju', 'Daegu': 'Daegu', 'Shanghai': 'Shanghai', 'Shenzhen': 'Guangdong',
    'Beijing': 'Beijing', 'Haikou': 'Hainan', 'Xiamen': 'Fujian', 'Kunming': 'Yunnan', 'Taipei': 'Taipei',
    'Taichung': 'Taichung', 'Kaohsiung': 'Kaohsiung', 'New Delhi': 'Delhi', 'Gurugram': 'Haryana',
    'Mumbai': 'Maharashtra', 'Bengaluru': 'Karnataka', 'Kolkata': 'West Bengal', 'Chandigarh': 'Chandigarh',
    'Bangkok': 'Bangkok', 'Pattaya': 'Chonburi', 'Hua Hin': 'Prachuap Khiri Khan', 'Phuket': 'Phuket',
    'Chiang Mai': 'Chiang Mai', 'Kuala Lumpur': 'Kuala Lumpur', 'George Town, Penang': 'Penang',
    'Johor Bahru': 'Johor', 'Singapore': 'Singapore', 'Manila': 'Metro Manila', 'Cebu City': 'Cebu',
    'Jakarta': 'Jakarta', 'Denpasar, Bali': 'Bali', 'Ho Chi Minh City': 'Ho Chi Minh City', 'Da Nang': 'Da Nang',
    'Hanoi': 'Hanoi', 'Melbourne': 'Victoria', 'Sydney': 'New South Wales', 'Brisbane': 'Queensland',
    'Gold Coast': 'Queensland', 'Perth': 'Western Australia', 'Adelaide': 'South Australia', 'Hobart': 'Tasmania',
    'Cairns': 'Queensland', 'Canberra': 'Australian Capital Territory', 'Auckland': 'Auckland',
    'Christchurch': 'Canterbury', 'Queenstown': 'Otago', 'Wellington': 'Wellington', 'Nadi': 'Western Division',
    'Suva': 'Central Division',
}


def subdivision(city):
    """A city's state, province or equivalent."""
    c = CITY_BY_NAME[city]
    if c.country in ('USA', 'Canada'):
        return city.split(', ', 1)[1]
    return _SUBDIVISION[city]


def place_of_city(city):
    return (CITY_BY_NAME[city].country, subdivision(city))


assert all(c.country in ('USA', 'Canada') and ', ' in c.name or c.name in _SUBDIVISION
           for c in CITY_BY_NAME.values()), 'every city needs a state, province or equivalent'

# Where US college golf is played, roughly by how many programmes each state has (uncalibrated: a
# spread over the states the geography knows, so college golfers are not all in one place).
COLLEGE_STATES = {
    'Texas': 10, 'California': 10, 'Florida': 9, 'North Carolina': 7, 'Georgia': 6, 'Arizona': 5, 'Ohio': 5,
    'Pennsylvania': 5, 'New York': 5, 'South Carolina': 4, 'Tennessee': 4, 'Alabama': 4, 'Oklahoma': 4,
    'Illinois': 4, 'Indiana': 4, 'Michigan': 4, 'Virginia': 4, 'Kentucky': 3, 'Louisiana': 3, 'Missouri': 3,
    'Colorado': 3, 'Washington': 3, 'Wisconsin': 3, 'Minnesota': 3, 'Massachusetts': 3, 'Utah': 2, 'Oregon': 2,
    'Nebraska': 2, 'Nevada': 2, 'Connecticut': 2, 'Maryland': 2, 'Idaho': 1, 'Hawaii': 1,
}
assert all(any(subdivision(c.name) == s for c in CITIES_BY_COUNTRY['USA']) for s in COLLEGE_STATES)
HOME_STATE_COLLEGE = 0.55        # chance a US golfer's college base is their own state (when it has college golf)

MOVE_COST = 6000.0               # a career move to another country, paid from the golfer's own funds
MIN_STAY = 3                     # seasons in a place before another career move (graduation, life changes excepted)
STAY_YEARS = 3                   # seasons a move's travel savings are weighed over
HOME_PULL = 60.0                 # value points of living in one's own country, at adaptability 50
MOVE_MARGIN, MOVE_SCALE = 15.0, 8.0   # a move is an even chance when it is worth this much more than staying
CADDIE_FOLLOWS, COACH_FOLLOWS = 0.15, 0.25   # a season's chance a caddie / coach moves to their players


class Places:
    """Birthplace, residence and dated moves for every person (one record per person id)."""

    def __init__(self):
        self.birth = {}          # pid -> (country, subdivision) | None (unknown)
        self.home = {}           # pid -> (country, subdivision)
        self.first = {}          # pid -> (year, week, place, note): their residence when they entered the world
        self.since = {}          # pid -> year they started living where they live now
        self.moves = {}          # pid -> [(year, week, from, to, reason)]
        self.college = {}        # pid -> (college tour, base) while at college
        self.legacy = set()      # people from a save made before places were kept: their geography is unknown

    def known(self, pid):
        return pid in self.home

    def country(self, pid, default):
        """Where they live (the country): `default` (their nationality) only for legacy people whose
        residence was never recorded."""
        h = self.home.get(pid)
        return h[0] if h else default

    def arrive(self, pid, birth, home, year, week, note='', settled=False):
        """A person enters the world. `settled`: they already lived there before it began (the world
        starts mid-history), so no recent move holds them in place."""
        self.birth[pid] = birth
        self.home[pid] = home
        self.first[pid] = (year, week, home, note)
        self.since[pid] = year - MIN_STAY if settled else year

    def move(self, pid, year, week, to, reason):
        """Record a move (nothing if they already live there). Returns the record or None."""
        frm = self.home.get(pid)
        if frm == to:
            return None
        rec = (year, week, frm, to, reason)
        self.moves.setdefault(pid, []).append(rec)
        self.home[pid] = to
        self.since[pid] = year
        return rec

    def residence_at(self, pid, year, week=53):
        """Where they lived at (year, week), from their record: None if unknown -- a legacy person, or a date
        before their first known residence (before they entered the world)."""
        first = self.first.get(pid)
        if first is None or (year, week) < (first[0], first[1]):
            return None
        place = first[2]
        for y, w, _, to, _ in self.moves.get(pid, ()):
            if (y, w) <= (year, week):
                place = to
        return place

    def export(self, pid):
        """A person's geography for the archive (None = unknown)."""
        f = self.first.get(pid)
        return {'birthplace': _p(self.birth.get(pid)), 'residence': _p(self.home.get(pid)),
                'first_residence': {'year': f[0], 'week': f[1], 'place': _p(f[2]), 'note': f[3]} if f else None,
                'moves': [{'year': y, 'week': w, 'from': _p(a), 'to': _p(b), 'reason': r}
                          for y, w, a, b, r in self.moves.get(pid, ())]}


def _p(place):
    return {'country': place[0], 'region': place[1]} if place else None


def describe(place):
    return f'{place[1]}, {place[0]}' if place and place[1] else (place[0] if place else 'unknown')


# ---- registering people ---------------------------------------------------------------------------------
def _birthplace(g):
    return place_of_city(g.hometown) if g.hometown in CITY_BY_NAME else (g.country, None)


def _staff_birthplace(seed, pid, country):
    cities = CITIES_BY_COUNTRY.get(country)
    if not cities:
        return (country, None)
    return place_of_city(random.Random(f'{seed}:staffhome:{pid}').choice(cities).name)


def college_base(seed, g, tour, birth, attempt=0):
    """Where a college golfer's college is: a state (US colleges) or a country hosting university golf
    (International University tour) -- a stable draw per golfer and college tour, not a named school."""
    rng = random.Random(f'{seed}:college:{g.id}:{tour}:{attempt}')
    from .calendar import TOUR_BY_KEY
    if tour in ('CO_US_D1', 'CO_US_SMALL'):
        own = birth[1] if birth and birth[0] == 'USA' else None
        if own in COLLEGE_STATES and rng.random() < HOME_STATE_COLLEGE:
            return ('USA', own)
        states = sorted(COLLEGE_STATES)
        return ('USA', rng.choices(states, [COLLEGE_STATES[s] for s in states])[0])
    hosts = dict(TOUR_BY_KEY[tour].countries) if tour in TOUR_BY_KEY else {}
    if g.country in hosts:
        if birth and birth[0] == g.country and birth[1]:
            return birth
        country = g.country
    else:
        region = COUNTRIES[g.country].region
        names = sorted(hosts)
        weights = [hosts[c] * (3.0 if COUNTRIES[c].region == region else 1.0) for c in names]
        country = rng.choices(names, weights)[0]
    return place_of_city(rng.choice(CITIES_BY_COUNTRY[country]).name)


def settle(season, year, week):
    """Give everyone without a record one (birthplace from their hometown; residence where they were
    born, or their college base), and keep college golfers at their college base: arrival or transfer is
    a recorded move that costs the golfer nothing. Legacy people stay unknown."""
    P = season.places
    from .calendar import TOUR_BY_KEY
    for g in season.world.golfers:
        if g.id in P.legacy:
            continue
        college = g.tour if g.tour.startswith('CO_') and g.lifestyle != 'retired' else None
        if not P.known(g.id):
            birth = _birthplace(g)
            if college:
                base = college_base(season.seed, g, college, birth)
                P.arrive(g.id, birth, base, year, week, f'at college ({TOUR_BY_KEY[college].name})')
                P.college[g.id] = (college, base)
            else:
                P.arrive(g.id, birth, birth, year, week, settled=week == 0 and year == season.first_year)
            continue
        if college and P.college.get(g.id, (None,))[0] != college:
            prior = P.college.get(g.id)
            base = college_base(season.seed, g, college, P.birth.get(g.id))
            P.college[g.id] = (college, base)
            why = (f'college transfer ({TOUR_BY_KEY[college].name}; paid by the school)' if prior
                   else f'college ({TOUR_BY_KEY[college].name}; paid by the school)')
            _record(season, g.id, year, week, base, why)
        elif not college and g.id in P.college:
            del P.college[g.id]                      # left college: where they live is now their own choice
    st = season.staff
    for person in list(st.coaches.values()) + list(st.caddies.values()):
        if person.id not in P.legacy and not P.known(person.id):
            place = _staff_birthplace(season.seed, person.id, person.country)
            P.arrive(person.id, place, place, year, week, settled=week == 0 and year == season.first_year)


def _record(season, pid, year, week, to, reason):
    rec = season.places.move(pid, year, week, to, reason)
    if rec is None:
        return None
    text = f'Moved from {describe(rec[2])} to {describe(to)} ({reason})'
    if pid in season.g:
        season.log(pid, year, week, text)
    st = season.staff
    person = st.coaches.get(pid) or st.caddies.get(pid)
    if person is not None and person.status == 'active':
        person.history.append((year, text))
    season.move_log.setdefault(year, []).append({'person': pid, 'from': rec[2], 'to': to, 'reason': reason,
                                                 'week': week})
    return rec


# ---- career moves -----------------------------------------------------------------------------------------
def _homeland(season, g):
    b = season.places.birth.get(g.id)
    return b[0] if b else g.country


def _destination(season, g, country, tour):
    """Where in `country` they would live: their birthplace if they were born there, else where most of
    the tour's events in that country are, else its first golfing city."""
    b = season.places.birth.get(g.id)
    if b and b[0] == country and b[1]:
        return b
    subs = {}
    for x in season.cal.series:
        if x.tour == tour:
            for city in x.cities:
                if CITY_BY_NAME[city].country == country:
                    s = subdivision(city)
                    subs[s] = subs.get(s, 0) + 1
    if subs:
        return (country, max(sorted(subs), key=subs.get))
    return place_of_city(CITIES_BY_COUNTRY[country][0].name)


def move_value(season, g, year, country, tour, events, current, home_pull):
    """What living in `country` is worth to a golfer, in event-value points: the travel to their tour's
    events over STAY_YEARS seasons and the cost of getting there (both against what a dollar means to
    them), and being away from their own country."""
    unit = season.money_unit(g, year)
    travel = STAY_YEARS * events * season.tour_trip_cost(g, tour, home=country, caddie=False)
    cost = 0.0 if country == current else MOVE_COST
    return -(travel + cost) / unit - (home_pull if country != _homeland(season, g) else 0.0)


def move_odds(season, g, year, changed=False):
    """(best country, chance they move there this winter) for a golfer who may move: the country of
    residence worth most to them among where they live, their own country and the countries of their
    tour's events (move_value), and a smooth chance that grows with how much more it is worth than
    staying (an even chance at MOVE_MARGIN points). (current country, 0) if nothing beats staying."""
    from .calendar import TOUR_BY_KEY
    current = season.places.home[g.id][0]
    events = season.target_events(g)
    pull = HOME_PULL * (1.6 - 1.2 * g.personality['adaptability'] / 100)
    options = {current, _homeland(season, g)} | {c for c, _ in TOUR_BY_KEY[g.tour].countries if c in COUNTRIES}
    value = {c: move_value(season, g, year, c, g.tour, events, current, pull) for c in sorted(options)}
    best = max(sorted(value), key=value.get)
    if best == current:
        return current, 0.0
    return best, _sig((value[best] - value[current] - MOVE_MARGIN) / MOVE_SCALE)


def review_moves(season, year, snap):
    """Each winter: professionals (and anyone whose golfing life changed, graduates included) may move
    closer to the events they have a route to enter, or back home (see the module notes)."""
    from .calendar import TOUR_BY_KEY
    P = season.places
    rng = random.Random(f'{season.seed}:moves:{year}')
    for g in sorted(season.active_golfers(), key=lambda g: g.id):
        if g.lifestyle == 'retired' or g.tour.startswith('CO_') or not P.known(g.id) or g.tour not in TOUR_BY_KEY:
            continue
        row = snap.get(g.id)
        changed = row is not None and (row['status'] != g.status or row['lifestyle'] != g.lifestyle
                                       or row['tour'].startswith('CO_'))
        chasing = g.status == 'pro' and g.lifestyle == 'full_time'
        if not (chasing or changed):
            continue                                 # a job, a club or a family home keeps them where they are
        if not changed and year - P.since.get(g.id, year) < MIN_STAY:
            continue
        current = P.home[g.id][0]
        events = season.target_events(g)
        best, p = move_odds(season, g, year, changed)
        if best == current or rng.random() >= p:
            continue
        cost = MOVE_COST
        own = g.cash + g.backing + g.backer_funds - FIN.RESERVE_WEEKS * season.committed_weekly(g)
        if own < cost:                               # paid from their own money (family and backers'
            season.move_blocked[year] = season.move_blocked.get(year, 0) + 1   # included), never on credit
            continue                                 # cannot pay for the move: they stay
        season.spend(g, year, 'moving', cost)
        season.cover_shortfall(g, year)              # funded now, from this year's pots, in this year's
                                                     # ledger (not after January's backer top-up)
        saved = (season.tour_trip_cost(g, g.tour, home=current, caddie=False)
                 - season.tour_trip_cost(g, g.tour, home=best, caddie=False)) * events
        to = _destination(season, g, best, g.tour)
        if best == _homeland(season, g):
            why = 'returned home' + (f' (travel ${-saved:,.0f} a season dearer, no longer a burden)' if saved < -500
                                     else f' (closer to their events too: ${saved:,.0f} a season less travel)'
                                     if saved > 500 else '')
        else:
            why = (f'closer to the {TOUR_BY_KEY[g.tour].name} events (about ${saved:,.0f} a season less '
                   f'travel; the move cost ${cost:,.0f})')
        if changed and row['tour'].startswith('CO_'):
            why += '; after college'
        elif changed and g.lifestyle != row['lifestyle']:
            why += '; after giving up the chase for a job' if g.lifestyle == 'part_time' else '; a new start'
        elif changed:
            why += '; after a change of status'
        _record(season, g.id, year, 53, to, why)


def staff_moves(season, year):
    """Each winter a caddie may move to where the player they caddie for lives, and a coach to where most
    of their players live (their careers, not their own golf; no cost: staff have no household finances)."""
    P = season.places
    st = season.staff
    rng = random.Random(f'{season.seed}:staffmoves:{year}')
    for gid, kid in sorted(st.caddie_of.items()):
        k = st.caddies.get(kid)
        if k is None or k.status != 'active' or not P.known(kid) or not P.known(gid):
            continue
        settled = all(season.assignments.get(y, {}).get('caddie_of', {}).get(gid) == kid for y in (year - 1, year))
        if settled and P.home[gid][0] != P.home[kid][0] and year - P.since.get(kid, year) >= MIN_STAY \
                and rng.random() < CADDIE_FOLLOWS:              # two seasons on this bag: a partnership
            _record(season, kid, year, 53, P.home[gid], f'to be near {season.g[gid].name}, whose bag they carry')
    clients = {}
    for gid, cid in st.coach_of.items():
        if P.known(gid):
            clients.setdefault(cid, []).append(P.home[gid])
    for cid, homes in sorted(clients.items()):
        c = st.coaches.get(cid)
        if c is None or c.status != 'active' or not P.known(cid) or len(homes) < 2:
            continue
        counts = {}
        for h in homes:
            counts[h[0]] = counts.get(h[0], 0) + 1
        top = max(sorted(counts), key=counts.get)
        if top != P.home[cid][0] and counts[top] >= 0.6 * len(homes) and year - P.since.get(cid, year) >= MIN_STAY \
                and rng.random() < COACH_FOLLOWS:
            subs = {}
            for h in homes:
                if h[0] == top:
                    subs[h] = subs.get(h, 0) + 1
            _record(season, cid, year, 53, max(sorted(subs, key=str), key=subs.get),
                    f'to where most of their players live ({counts[top]} of {len(homes)})')


def _sig(x):
    return 1 / (1 + math.exp(-x))
