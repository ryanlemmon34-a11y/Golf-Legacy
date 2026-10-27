"""Course generator: fictional courses, in real cities, in a style that fits the place.

Every course is a *site* (identity, city, style, class, architect, opening year) with one or more
*layouts* (sets of tees and set-ups over the same 18 holes). Records are kept per layout.

Classes:
    elite         the world's best; Premier Tour and majors only; ONE layout
    championship  hard; Championship + Club layouts
    standard      mid difficulty; Championship + Club layouts, some also Forward
    municipal     easy; Regular layout, some also Forward

Lower tours, college and amateur events play the easier layouts of the same courses: forward tees,
slower greens and lighter rough, but the same holes and the same hazards.
"""
from __future__ import annotations

import random
from dataclasses import replace

from .course import Course, Hole
from .geography import CITY_BY_NAME, COUNTRIES

CLASSES = ('elite', 'championship', 'standard', 'municipal')
# Overall difficulty range per class (0 = easiest, 1 = hardest).
CLASS_DIFFICULTY = {'elite': (0.82, 1.0), 'championship': (0.6, 0.82), 'standard': (0.32, 0.62), 'municipal': (0.05, 0.32)}

# ---------------------------------------------------------------------------------------------
# Styles: ranges for the hole features that matter. side = weights for open/trees/water/ob.
# ---------------------------------------------------------------------------------------------
STYLES = {
    'Links': dict(width=(32, 44), rough=(.45, .75), rough_w=(14, 24), side=(.62, .04, .04, .30), bunkers=(.45, .85),
                  gs_bunkers=(.4, .85), green_r=(12.5, 17), speed=-.6, slope=(.3, .7), firm=(.62, .82),
                  water_green=.02, wind=(.75, 1.0), elev=6, dogleg=.25, wind_mph=16),
    'Heathland': dict(width=(28, 36), rough=(.55, .8), rough_w=(9, 15), side=(.25, .65, .03, .07), bunkers=(.35, .7),
                      gs_bunkers=(.45, .8), green_r=(12, 15.5), speed=0, slope=(.35, .7), firm=(.55, .72),
                      water_green=.03, wind=(.3, .6), elev=8, dogleg=.35, wind_mph=9),
    'Parkland': dict(width=(29, 38), rough=(.4, .65), rough_w=(10, 16), side=(.18, .6, .14, .08), bunkers=(.2, .55),
                     gs_bunkers=(.4, .75), green_r=(12.5, 16), speed=0, slope=(.35, .75), firm=(.4, .58),
                     water_green=.12, wind=(.3, .55), elev=8, dogleg=.35, wind_mph=8),
    'Woodland': dict(width=(26, 33), rough=(.45, .7), rough_w=(7, 12), side=(.08, .82, .05, .05), bunkers=(.2, .5),
                     gs_bunkers=(.4, .75), green_r=(11.5, 15), speed=.2, slope=(.4, .8), firm=(.45, .62),
                     water_green=.06, wind=(.15, .35), elev=10, dogleg=.45, wind_mph=6),
    'Desert': dict(width=(32, 42), rough=(.15, .35), rough_w=(6, 12), side=(.05, .75, .1, .1), bunkers=(.3, .6),
                   gs_bunkers=(.45, .8), green_r=(12.5, 16), speed=.4, slope=(.4, .75), firm=(.6, .78),
                   water_green=.14, wind=(.45, .7), elev=10, dogleg=.3, wind_mph=10),
    'Mountain': dict(width=(27, 35), rough=(.4, .65), rough_w=(8, 13), side=(.1, .75, .08, .07), bunkers=(.2, .5),
                     gs_bunkers=(.35, .7), green_r=(11.5, 15), speed=-.2, slope=(.5, .9), firm=(.45, .65),
                     water_green=.08, wind=(.3, .6), elev=24, dogleg=.45, wind_mph=9),
    'Coastal': dict(width=(30, 39), rough=(.4, .7), rough_w=(10, 16), side=(.25, .3, .3, .15), bunkers=(.3, .65),
                    gs_bunkers=(.45, .8), green_r=(12, 15.5), speed=0, slope=(.4, .75), firm=(.5, .7),
                    water_green=.1, wind=(.6, .9), elev=10, dogleg=.3, wind_mph=13),
    'Tropical': dict(width=(32, 42), rough=(.3, .55), rough_w=(10, 16), side=(.2, .45, .25, .1), bunkers=(.25, .55),
                     gs_bunkers=(.4, .75), green_r=(13, 16.5), speed=-.8, slope=(.3, .65), firm=(.35, .5),
                     water_green=.2, wind=(.3, .6), elev=6, dogleg=.3, wind_mph=9),
    'Sandbelt': dict(width=(34, 44), rough=(.2, .4), rough_w=(10, 16), side=(.35, .55, .02, .08), bunkers=(.5, .8),
                     gs_bunkers=(.65, .95), green_r=(12, 15), speed=.6, slope=(.45, .8), firm=(.68, .85),
                     water_green=.01, wind=(.45, .7), elev=5, dogleg=.4, wind_mph=12),
    'Municipal': dict(width=(36, 48), rough=(.1, .35), rough_w=(14, 22), side=(.55, .25, .08, .12), bunkers=(.05, .3),
                      gs_bunkers=(.15, .45), green_r=(14, 17), speed=-1.5, slope=(.2, .45), firm=(.25, .45),
                      water_green=.06, wind=(.25, .5), elev=4, dogleg=.25, wind_mph=7),
}

LINKS_COUNTRIES = {'Scotland', 'Ireland', 'Northern Ireland', 'England', 'Wales'}
HEATH_COUNTRIES = {'England', 'Germany', 'Netherlands', 'Belgium', 'Denmark', 'Sweden'}


def pick_style(city, cls, rng):
    c = CITY_BY_NAME[city]
    if cls == 'municipal':
        return 'Municipal' if rng.random() < .75 else 'Parkland'
    if city == 'Melbourne' and rng.random() < .7:
        return 'Sandbelt'
    if c.country in LINKS_COUNTRIES and c.coastal and rng.random() < .8:
        return 'Links'
    if c.country in ('Denmark', 'Netherlands') and c.coastal and rng.random() < .3:
        return 'Links'
    if c.climate == 'desert':
        return 'Desert' if rng.random() < .85 else 'Coastal' if c.coastal else 'Parkland'
    if c.climate == 'alpine':
        return 'Mountain'
    if c.climate == 'tropical':
        return 'Tropical' if rng.random() < .7 else 'Parkland'
    if c.country in HEATH_COUNTRIES and rng.random() < .35:
        return 'Heathland'
    if c.coastal and c.climate in ('mediterranean', 'subtropical', 'oceanic') and rng.random() < .4:
        return 'Coastal'
    if c.climate == 'continental' and rng.random() < .15:
        return 'Mountain' if c.country in ('USA', 'Canada', 'Japan', 'Switzerland', 'Austria') else 'Woodland'
    return rng.choice(('Parkland', 'Parkland', 'Woodland'))


# ---------------------------------------------------------------------------------------------
# Names. Word banks per language; famous real courses are blocked so no name copies a real one.
# ---------------------------------------------------------------------------------------------
EN_A = ('Heron', 'Fox', 'Willow', 'Granite', 'Cedar', 'Hawk', 'Thistle', 'Briar', 'Kestrel', 'Copper', 'Silver',
        'Juniper', 'Larch', 'Holly', 'Wren', 'Stag', 'Raven', 'Sable', 'Amber', 'Falcon', 'Bramble', 'Elder',
        'Owl', 'Badger', 'Marten', 'Linden', 'Hazel', 'Rowan', 'Alder', 'Aspen', 'Sparrow', 'Lark', 'Osprey',
        'Bluestone', 'Ironwood', 'Redtail', 'Whitewater', 'Blackwater', 'Greystone', 'Goldfinch', 'Hartwell',
        'Ashcombe', 'Bellmoor', 'Carrick', 'Dunmore', 'Fernhill', 'Hollins', 'Kingsley', 'Langford', 'Mapleton',
        'Northcote', 'Pemberly', 'Quarry', 'Ravensworth', 'Stonebridge', 'Thornbury', 'Whitfield', 'Wolfe')
EN_SIMPLE = ('Fox', 'Willow', 'Holly', 'Wren', 'Elder', 'Hazel', 'Raven', 'Heron', 'Stag', 'Owl', 'Briar', 'Bramble',
             'Linden', 'Larch', 'Rowan', 'Alder', 'Marten', 'Hawk', 'Thistle', 'Lark', 'Badger', 'Cedar', 'Oak', 'Ash',
             'Birch', 'Elm', 'Thorn', 'Heather', 'Gorse', 'Broom', 'Fern', 'Moss', 'Kings', 'Queens', 'Mill')
NOT_UK = {'Redtail', 'Ironwood', 'Bluestone', 'Whitewater', 'Blackwater', 'Goldfinch', 'Osprey', 'Juniper', 'Aspen',
          'Mesa', 'Canyon', 'Springs', 'Landing', 'Farm', 'Run', 'Hollow', 'Creek', 'Bluff', 'Harbor', 'Copper', 'Sable'}
DESERT_WORDS = {'Mesa', 'Canyon'}
WATER_WORDS = {'Dunes', 'Shore', 'Cove', 'Harbor', 'Bay', 'Point'}
EN_B = ('Ridge', 'Hollow', 'Creek', 'Bluff', 'Glen', 'Brook', 'Moor', 'Downs', 'Point', 'Crest', 'Bend', 'Run', 'Ford',
        'Vale', 'Heath', 'Dunes', 'Shore', 'Cove', 'Harbor', 'Canyon', 'Mesa', 'Springs', 'Meadows', 'Woods',
        'Lakes', 'Rock', 'Park', 'Farm', 'Fields', 'Knoll', 'Landing', 'Pines', 'Oaks', 'Valley', 'Bay', 'Wood')
SCOT = ('Kinmuir', 'Balcreggan', 'Inverlaidh', 'Glenmorrie', 'Dunlarig', 'Craigdarroch', 'Ardnacross', 'Kilbrannan',
        'Lochanside', 'Strathbeg', 'Auchterbrae', 'Torrisdale', 'Murrayfield', 'Corriemuir', 'Benlarig', 'Achmore')
IRISH = ('Ballyroe', 'Kilcarra', 'Rathmoyle', 'Dunmanus', 'Clonbeg', 'Ballinacor', 'Kilmurray', 'Derrylane',
         'Glencarrig', 'Inishmore', 'Carrowkeel', 'Athmore')
ES = ('Las Encinas Altas', 'Los Almendros', 'La Herradura', 'El Bosque', 'Las Praderas', 'Los Cipreses', 'La Ribera',
      'El Robledal', 'Las Acacias', 'Los Laureles', 'Altos del Río', 'La Estancia', 'Los Molinos', 'El Castillo',
      'La Torre', 'Las Higueras', 'Los Sauces', 'El Lago Azul', 'Sierra Blanca Alta', 'Los Fresnos', 'Los Álamos', 'Los Olivos', 'Las Lomas', 'Los Pinares', 'Las Arenas', 'Los Robles',
      'Las Colinas del Sol', 'Las Brisas', 'Las Cumbres', 'La Sierra', 'El Valle', 'El Mirador', 'La Cañada',
      'Los Naranjos del Norte', 'La Alameda', 'El Pinar', 'La Dehesa Alta', 'Las Palmeras', 'El Encinar',
      'Monte Verde', 'Los Cerros', 'La Quinta Real', 'Río Claro', 'Valle Hermoso', 'Puerta del Mar')
PT = ('Quinta da Serra', 'Quinta das Palmeiras', 'Vale do Lobo Novo', 'Mata Atlântica', 'Bosque Real', 'Campo Belo',
      'Recanto das Águas', 'Morro Verde', 'Quinta do Moinho', 'Pinhal Grande', 'Lagoa Azul', 'Vale do Sol', 'Quinta dos Pinheiros', 'Serra Verde',
      'Monte Alegre', 'Quinta da Ribeira', 'Praia Dourada', 'Vale das Oliveiras')
FR = ('Les Bruyères', 'Les Saules', 'Le Moulin', 'Les Cèdres', 'La Bergerie', 'Les Tilleuls', 'Le Prieuré',
      'Les Hêtres', 'La Garenne', 'Les Genêts', 'Le Château Blanc', 'Les Mimosas', 'La Roseraie', 'Les Chênes', 'Les Pins', 'Les Étangs', 'Les Hauts Bois', 'Les Vignes',
      'La Fontaine', 'Le Domaine du Lac', 'La Forêt Noire', 'Les Dunes Blanches', 'Le Clos Fleuri', 'Les Châtaigniers')
DE = ('Lindenhof', 'Am Weiher', 'Eschenhof', 'Hohenstein', 'Fichtenhain', 'Gut Erlenbach', 'Wiesental', 'Eichenwald', 'Buchenwald', 'Tannenhain', 'Seeblick', 'Waldsee', 'Bergblick', 'Heidegrund',
      'Schlossgarten', 'Sonnenhalde', 'Kiefernhain', 'Mühlenbach', 'Birkenhof', 'Rosenau')
NL = ('De Hooge Duinen', 'De Heidevelden', 'Het Bosch', 'De Lindenhorst', 'De Zandheuvels', 'Het Rietveld',
      'De Wildbaan', 'De Eikenhorst')
SC = ('Ekbacken', 'Björkudden', 'Sjövik', 'Lundsberg', 'Strandvik', 'Fjordby', 'Mossebo', 'Granlunda',
      'Tallbacka', 'Ljungdala', 'Havsbo', 'Kärrby')
IT = ('Le Querce', 'Le Colline', 'I Pini', 'Gli Ulivi', 'La Rocca', 'Il Lago', 'Le Betulle Nuove', 'La Pineta Alta')
JP = ('Matsugaoka', 'Kasugadai', 'Fujimidai', 'Yamabuki', 'Minamigaoka', 'Kaedenomori', 'Sengen', 'Hanamizuki', 'Sakuradai', 'Kazehara', 'Morinoyama', 'Takigawa', 'Hoshinomori', 'Tsurumidai', 'Aobagaoka',
      'Midorigahara', 'Shirasagi', 'Kiritani', 'Hinokiyama', 'Isoharu', 'Momijidai', 'Kumanodai', 'Suzukake')
KR = ('Haneul', 'Sorak Valley', 'Namu Hills', 'Bada', 'Sangrok', 'Hanbit', 'Eunbit', 'Pureun', 'Seorak Pines',
      'Gureum')
ZH = ('Jinlong', 'Yunshan', 'Songlin', 'Baihe', 'Tianhu', 'Qingshan', 'Lanxi', 'Feicui', 'Xinghai', 'Longquan')
SEA = ('Bukit Tinggi', 'Tasik Biru', 'Taman Sari', 'Seri Alam', 'Phu Khao', 'Suan Son', 'Nam Sai', 'Danau Hijau',
       'Song Xanh', 'Hoa Sen', 'Gunung Indah', 'Chang Rai')
IN = ('Kesar Bagh', 'Neem Valley', 'Amrit Greens', 'Vana Vihar', 'Chandni Lakes', 'Saffron Hills')
AR = ('Al Waha', 'Al Rimal', 'Al Qamar', 'Al Bahr', 'Al Noor', 'Al Sahil', 'Al Wadi', 'Al Jazira Sands', 'Al Fanar')

LANG = {
    'USA': 'en', 'Canada': 'en', 'England': 'en', 'Wales': 'en', 'Australia': 'en', 'New Zealand': 'en',
    'South Africa': 'en', 'Kenya': 'en', 'Nigeria': 'en', 'Zimbabwe': 'en', 'Zambia': 'en', 'Namibia': 'en',
    'Mauritius': 'en', 'Fiji': 'en', 'Singapore': 'en', 'Philippines': 'en', 'Scotland': 'scot',
    'Ireland': 'irish', 'Northern Ireland': 'irish', 'Spain': 'es', 'Mexico': 'es', 'Argentina': 'es', 'Chile': 'es',
    'Colombia': 'es', 'Peru': 'es', 'Portugal': 'pt', 'Brazil': 'pt', 'France': 'fr', 'Morocco': 'fr',
    'Germany': 'de', 'Austria': 'de', 'Switzerland': 'de', 'Netherlands': 'nl', 'Belgium': 'nl', 'Sweden': 'sc',
    'Denmark': 'sc', 'Norway': 'sc', 'Finland': 'sc', 'Italy': 'it', 'Japan': 'jp', 'South Korea': 'kr',
    'China': 'zh', 'Taiwan': 'zh', 'Thailand': 'sea', 'Malaysia': 'sea', 'Indonesia': 'sea', 'Vietnam': 'sea',
    'India': 'in', 'United Arab Emirates': 'ar', 'Qatar': 'ar', 'Saudi Arabia': 'ar', 'Bahrain': 'ar', 'Oman': 'ar',
    'Egypt': 'ar', 'Czechia': 'en', 'Poland': 'en', 'Turkey': 'en',
}

# Famous real courses: a generated name containing any of these phrases is rejected.
REAL_NAME_BLOCKLIST = (
    'pine valley', 'oak hill', 'oakmont', 'augusta', 'pebble beach', 'cypress point', 'shinnecock', 'merion',
    'winged foot', 'baltusrol', 'olympic club', 'muirfield', 'riviera', 'bethpage', 'medinah', 'whistling straits',
    'valhalla', 'southern hills', 'quail hollow', 'torrey pines', 'harbour town', 'bay hill', 'colonial', 'sawgrass',
    'kiawah', 'pinehurst', 'carnoustie', 'turnberry', 'birkdale', 'hoylake', 'troon', 'portrush', 'st andrews',
    'sunningdale', 'wentworth', 'valderrama', 'royal melbourne', 'kingston heath', 'county down', 'ballybunion',
    'lahinch', 'portmarnock', 'golf national', 'kasumigaseki', 'hirono', 'cabot', 'bandon', 'pacific dunes',
    'sand valley', 'erin hills', 'chambers bay', 'hazeltine', 'inverness', 'congressional', 'east lake', 'tpc ',
    'firestone', 'doral', 'sea island', 'lytham', "st george's", 'gleneagles', 'castle stuart', 'kingsbarns',
    'leopard creek', 'fancourt', 'emirates', 'yas links', 'jumeirah', 'seminole', 'national golf links',
    'fishers island', 'prairie dunes', 'crystal downs', 'sand hills', "friar's head", 'oak tree', 'aronimink',
    'cherry hills', 'olympia fields', 'interlachen', 'scioto', 'peachtree', 'old elm', 'chicago golf',
    'garden city', 'los angeles country', 'royal portrush', 'royal dornoch', 'dornoch', 'prestwick', 'loch lomond',
    'woodhall', 'walton heath', 'royal st', 'swinley', 'ganton', 'royal birkdale', 'el saler', 'morfontaine',
    'les bordes', 'kennemer', 'falsterbo', 'barsebäck', 'bro hof', 'royal adelaide', 'new south wales',
    'barnbougle', 'cape kidnappers', 'kauri cliffs', 'tara iti', 'nine bridges', 'mission hills', 'sheshan',
    'jack nicklaus', 'arnold palmer', 'gary player', 'las colinas', 'eichenried', 'quinta do lago', 'monte rei',
    'la quinta', 'pga west', 'tiburon', 'mayakoba', 'el camaleón', 'liberty national', 'medalist', 'muirfield village',
)


def _blocked(name):
    n = name.lower()
    return any(b in n for b in REAL_NAME_BLOCKLIST)


def course_name(city, cls, style, rng, taken):
    """A fictional club name in the local language. `taken` holds full names and core names, so no two
    clubs in the world share the same core name (no "Los Olivos" in both Madrid and Lima)."""
    country = CITY_BY_NAME[city].country
    lang = LANG.get(country, 'en')
    town = city.split(',')[0]
    uk = country in ('England', 'Scotland', 'Wales', 'Ireland', 'Northern Ireland')
    first = [w for w in EN_A if not (uk and w in NOT_UK)]
    second = [w for w in EN_B if not (uk and w in NOT_UK)
              and (w not in DESERT_WORDS or style in ('Desert', 'Mountain'))
              and (w not in WATER_WORDS or CITY_BY_NAME[city].coastal or style in ('Links', 'Coastal'))]
    for attempt in range(400):
        local = attempt >= 150          # word banks exhausted: tie the name to the town
        if lang in ('en', 'scot', 'irish'):
            if lang == 'scot' and rng.random() < .6:
                core = rng.choice(SCOT)
            elif lang == 'irish' and rng.random() < .6:
                core = rng.choice(IRISH)
            elif rng.random() < .7:
                core = f'{rng.choice(first)} {rng.choice(second)}'
            else:
                core = f'{rng.choice(EN_SIMPLE)}{rng.choice(("brook", "wood", "field", "mere", "ley", "stead", "ton"))}'
            if local or cls == 'municipal' and rng.random() < .5:
                core = f'{town} {rng.choice(second)}'
            if style == 'Links':
                kind = rng.choice(('Links', 'Golf Links', 'Golf Club'))
            elif cls == 'elite':
                kind = rng.choice(('National', 'Golf Club', 'Club'))
            elif cls == 'municipal':
                kind = rng.choice(('Golf Course', 'Municipal Golf Course', 'Public Golf Course', 'Golf Club'))
            elif style in ('Tropical', 'Desert', 'Coastal') and rng.random() < .4:
                kind = rng.choice(('Golf Resort', 'Resort Course', 'Golf Club'))
            else:
                kind = rng.choice(('Golf Club', 'Country Club', 'Golf Club', 'Club'))
            royal = cls == 'elite' and country in ('England', 'Scotland', 'Ireland', 'Northern Ireland', 'Wales',
                                                   'Australia') and rng.random() < .35
            name = f'{"Royal " if royal else ""}{core} {kind}'
        else:
            bank, kinds, before = {
                'es': (ES, ('Club de Golf', 'Golf', 'Club de Campo'), True),
                'pt': (PT, ('Clube de Golfe', 'Golfe'), True),
                'fr': (FR, ('Golf de', 'Golf du Domaine de'), True),
                'de': (DE, ('Golfclub', 'Golf- und Landclub', 'Golfpark'), True),
                'nl': (NL, ('Golfclub', 'Golfbaan'), True),
                'sc': (SC, ('Golfklubb', 'Golfklub', 'Golf'), False),
                'it': (IT, ('Golf Club',), True),
                'jp': (JP, ('Country Club', 'Golf Club', 'Golf Links'), False),
                'kr': (KR, ('Country Club', 'Golf Club'), False),
                'zh': (ZH, ('Golf Club', 'International Golf Club', 'Lakes Golf Club'), False),
                'sea': (SEA, ('Golf & Country Club', 'Golf Club', 'Golf Resort'), False),
                'in': (IN, ('Golf Club', 'Golf & Country Club'), False),
                'ar': (AR, ('Golf Club', 'Golf Resort', 'Golf Links'), False),
            }[lang]
            core = rng.choice(bank)
            if local:
                core = f'{core} de {town}' if lang in ('es', 'pt', 'fr') else f'{core} {town}'
            kind = rng.choice(kinds)
            if lang == 'es' and cls == 'elite' and country == 'Spain':
                kind = 'Real Club de Golf'
            name = f'{kind} {core}' if before else f'{core} {kind}'
            if lang == 'fr':
                name = name.replace('de Les ', 'des ').replace('de Le ', 'du ').replace('de La ', 'de la ')
        key = 'core:' + core.lower()
        if name not in taken and key not in taken and not _blocked(name):
            taken.update((name, key))
            return name
    raise RuntimeError(f'could not name a course in {city}')


# ---------------------------------------------------------------------------------------------
# Fictional architects: (name, first year, last year, favourite styles)
# ---------------------------------------------------------------------------------------------
ARCHITECTS = (
    ('Alistair Grieve', 1885, 1925, ('Links', 'Heathland')), ('Harold Penrose', 1900, 1935, ('Heathland', 'Parkland')),
    ('Duncan Fairlie', 1895, 1930, ('Links',)), ('Thomas Whitcombe', 1910, 1940, ('Parkland', 'Woodland')),
    ('Samuel Kittredge', 1915, 1950, ('Parkland', 'Woodland', 'Coastal')), ('Arthur Bellamy', 1920, 1955, ('Heathland', 'Links')),
    ('Robert Tarrant', 1925, 1965, ('Parkland', 'Sandbelt')), ('Ian McCrae', 1930, 1970, ('Sandbelt', 'Links', 'Coastal')),
    ('Pierre Lavallée', 1930, 1975, ('Parkland', 'Heathland')), ('Hans Brenner', 1950, 1990, ('Parkland', 'Mountain')),
    ('Jack Nevin', 1955, 1995, ('Parkland', 'Desert', 'Tropical')), ('Kenji Morita', 1955, 2000, ('Woodland', 'Mountain', 'Parkland')),
    ('Diego Salvatierra', 1965, 2005, ('Coastal', 'Parkland', 'Desert')), ('Lars Eklund', 1965, 2005, ('Parkland', 'Woodland')),
    ('Eleanor Marsh', 1975, 2015, ('Links', 'Heathland', 'Coastal')), ('Gavin Thorne', 1980, 2020, ('Desert', 'Tropical', 'Coastal')),
    ('Peter Okonkwo', 1985, 2025, ('Parkland', 'Tropical')), ('Mei Lin Zhao', 1990, 2026, ('Tropical', 'Parkland', 'Mountain')),
    ('Rafael Mendes', 1990, 2026, ('Coastal', 'Tropical')), ('Grant Holloway', 1995, 2026, ('Desert', 'Parkland', 'Links')),
    ('Fiona Garvie', 2000, 2026, ('Links', 'Sandbelt', 'Heathland')), ('Noah Caldwell', 2005, 2026, ('Sandbelt', 'Coastal', 'Links')),
    ('William Ashdown', 1905, 1940, ('Municipal', 'Parkland')), ('Michael Strand', 1960, 2010, ('Municipal', 'Parkland', 'Woodland')),
)


def pick_architect(style, rng, cls=''):
    fits = [a for a in ARCHITECTS if style in a[3]] or list(ARCHITECTS)
    if cls == 'elite' and rng.random() < .75:
        # most of the world's great courses are old: the golden age of design
        fits = [a for a in fits if a[1] < 1960] or [a for a in ARCHITECTS if a[1] < 1960 and a[3][0] != 'Municipal']
    name, start, end, _ = rng.choice(fits)
    return name, rng.randint(start, end)


# ---------------------------------------------------------------------------------------------
# Holes and layouts
# ---------------------------------------------------------------------------------------------
def _u(rng, lo_hi):
    lo, hi = lo_hi
    return lo + (hi - lo) * rng.random()


def _par_sequence(par, rng):
    n5 = par - 68
    front = [3, 3] + [5] * (n5 // 2 + n5 % 2) + [4] * (7 - n5 // 2 - n5 % 2)
    back = [3, 3] + [5] * (n5 // 2) + [4] * (7 - n5 // 2)
    for nine in (front, back):
        while True:
            rng.shuffle(nine)
            if nine[0] != 3 and not (nine[-1] == 3 and rng.random() < .7):
                break
    return front + back


def _note(h):
    bits = []
    if h.par == 4 and h.yards < 345:
        bits.append('Short par 4, drivable for the longest hitters.')
    if h.dogleg >= .3:
        bits.append(f'Dogleg {"left" if h.bend == "L" else "right"} at {h.landing_limit} yards.')
    sides = {s for s in (h.left, h.right) if s != 'open'}
    if 'water' in sides:
        bits.append(f'Water down the {"left" if h.left == "water" else "right"}.')
    if 'ob' in sides:
        bits.append(f'Out of bounds {"left" if h.left == "ob" else "right"}.')
    if h.green_water:
        bits.append({'front': 'Water in front of the green.', 'left': 'Water left of the green.',
                     'right': 'Water right of the green.', 'back': 'Water behind the green.'}[h.green_water])
    if h.greenside_bunkers > .75:
        bits.append('Green ringed by bunkers.')
    if h.green_slope > .8:
        bits.append('Severely contoured green.')
    if h.elevation >= 12:
        bits.append('Plays uphill.')
    elif h.elevation <= -12:
        bits.append('Plays downhill.')
    if h.fairway_width <= 27:
        bits.append('Narrow driving area.')
    return ' '.join(bits) or 'A straightforward hole.'


def make_holes(style, d, par, rng):
    S = STYLES[style]
    pars = _par_sequence(par, rng)
    length = 6150 + 1350 * d - 140 * (72 - par) + rng.gauss(0, 110)
    if style == 'Municipal':
        length -= 150
    yards = []
    short_four = rng.random() < .6
    for p in pars:
        if p == 3:
            yards.append(rng.gauss(180, 24))
        elif p == 5:
            yards.append(rng.gauss(555, 26))
        elif short_four:
            yards.append(rng.uniform(300, 345))
            short_four = False
        else:
            yards.append(rng.gauss(425, 38))
    scale = length / sum(yards)
    yards = [max({3: 120, 4: 290, 5: 470}[p], min({3: 260, 4: 520, 5: 640}[p], y * scale)) for p, y in zip(pars, yards)]
    holes = []
    sides = ('open', 'trees', 'water', 'ob')
    for i, (p, y) in enumerate(zip(pars, yards), 1):
        width = _u(rng, S['width']) - 7 * d + rng.gauss(0, 1.5)
        dog = p >= 4 and rng.random() < S['dogleg']
        h = Hole(i, p, int(round(y)),
                 fairway_width=round(max(22, min(50, width)), 1),
                 rough_width=round(_u(rng, S['rough_w']), 1),
                 rough_severity=round(max(0, min(1, _u(rng, S['rough']) + 0.25 * (d - .5))), 2),
                 left=rng.choices(sides, S['side'])[0], right=rng.choices(sides, S['side'])[0],
                 landing_limit=int(rng.uniform(255, 315)) if dog else 0,
                 dogleg=round(rng.uniform(.3, .7), 2) if dog else 0.0,
                 bend=rng.choice('LR') if dog else '',
                 fairway_bunkers=round(max(0, min(1, _u(rng, S['bunkers']) + .2 * (d - .5))), 2),
                 green_radius=round(max(10, min(18, _u(rng, S['green_r']) - 2.0 * (d - .5))), 1),
                 green_speed=round(max(8.5, min(14.5, 9.6 + 3.2 * d + S['speed'] + rng.gauss(0, .25))), 1),
                 green_slope=round(max(0, min(1, _u(rng, S['slope']) + .2 * (d - .5))), 2),
                 green_firmness=round(max(0, min(1, _u(rng, S['firm']) + .1 * (d - .5))), 2),
                 greenside_bunkers=round(max(0, min(1, _u(rng, S['gs_bunkers']) + .1 * (d - .5))), 2),
                 green_water=rng.choice(('front', 'left', 'right', 'back')) if rng.random() < S['water_green'] * (.6 + d) else '',
                 wind_exposure=round(_u(rng, S['wind']), 2),
                 elevation=int(rng.gauss(0, S['elev'] / 2)))
        holes.append(replace(h, note=_note(h)))
    return tuple(holes)


ELITE_MIN_YARDS = 7250


def championship_setup(holes):
    """The world's best courses are set up as major-championship tests: long, tight, firm and fast."""
    total = sum(h.yards for h in holes)
    k = max(1.0, ELITE_MIN_YARDS / total)
    return tuple(replace(h, yards=int(round(h.yards * k)),
                         fairway_width=round(max(22.0, h.fairway_width - 3), 1),
                         rough_severity=round(min(1.0, h.rough_severity + 0.10), 2),
                         green_speed=round(min(14.5, h.green_speed + 0.4), 1)) for h in holes)


LAYOUT_SETUPS = {
    # name: (yardage factor, green speed change, rough change, firmness change)
    'Championship': (1.0, 0.0, 0.0, 0.0),
    'Club': (0.93, -1.0, -0.15, -0.1),
    'Forward': (0.86, -1.5, -0.25, -0.15),
    'Regular': (1.0, 0.0, 0.0, 0.0),
}


def derive_layout(holes, key):
    yf, speed, rough, firm = LAYOUT_SETUPS[key]
    if key in ('Championship', 'Regular'):
        return holes
    return tuple(replace(h, yards=int(round(h.yards * yf)),
                         landing_limit=int(round(h.landing_limit * yf)) if h.landing_limit else 0,
                         green_speed=round(max(8.0, h.green_speed + speed), 1),
                         rough_severity=round(max(0.0, h.rough_severity + rough), 2),
                         green_firmness=round(max(0.0, h.green_firmness + firm), 2)) for h in holes)


def layouts_for(cls, rng):
    if cls == 'elite':
        return ('Championship',)
    if cls == 'championship':
        return ('Championship', 'Club')
    if cls == 'standard':
        return ('Championship', 'Club', 'Forward') if rng.random() < .45 else ('Championship', 'Club')
    return ('Regular', 'Forward') if rng.random() < .5 else ('Regular',)


def generate_site(course_id, city, cls, rng, taken_names, style=None):
    """Generate one course site with its layouts (Course objects sharing the same holes)."""
    style = style or pick_style(city, cls, rng)
    lo, hi = CLASS_DIFFICULTY[cls]
    d = lo + (hi - lo) * rng.random()
    par = rng.choices((72, 71, 70), (6, 2.5, 1.5) if cls != 'municipal' else (5, 3, 2))[0]
    if style == 'Links' and par == 72 and rng.random() < .4:
        par = 71
    holes = make_holes(style, d, par, rng)
    if cls == 'elite':
        holes = championship_setup(holes)
    name = course_name(city, cls, style, rng, taken_names)
    architect, opened = pick_architect(style, rng, cls)
    country = CITY_BY_NAME[city].country
    wind = STYLES[style]['wind_mph'] + (3 if CITY_BY_NAME[city].coastal else 0)
    layouts = {}
    for key in layouts_for(cls, rng):
        layouts[key] = Course(name, country, style, derive_layout(holes, key), typical_wind=wind,
                              description=f'{style} course in {city}, designed by {architect} ({opened}).',
                              tags=(cls,), city=city, course_id=course_id, layout=key)
    return dict(course_id=course_id, name=name, city=city, country=country, region=COUNTRIES[country].region,
                style=style, cls=cls, difficulty=round(d, 3), architect=architect, opened=opened, layouts=layouts)
