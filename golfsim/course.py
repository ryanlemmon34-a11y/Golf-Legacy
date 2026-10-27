"""Course and hole definitions, plus the hand-built calibration courses.

A hole is described by the features that actually change how shots end up:
length, fairway width, how severe the rough is, what lies beyond the rough
(trees, water, out of bounds, open ground), where the fairway runs out or
bends, bunkers, green size/speed/slope/firmness, water around the green and
exposure to wind. Difficulty is never a single number added to everyone's
score: weak players miss more fairways and greens, so hazards and fast greens
punish them far more than they punish strong players.
"""
from __future__ import annotations

from dataclasses import dataclass, replace, field

HAZARDS = ('open', 'trees', 'water', 'ob')
GREEN_WATER = ('', 'front', 'left', 'right', 'back')


@dataclass(frozen=True)
class Hole:
    number: int
    par: int
    yards: int
    fairway_width: float = 32.0      # yards
    rough_width: float = 12.0        # yards of rough before the side hazard
    rough_severity: float = 0.5      # 0 light .. 1 brutal
    left: str = 'trees'              # beyond the left rough
    right: str = 'trees'             # beyond the right rough
    landing_limit: int = 0           # yards from tee where fairway ends / bends (0 = none)
    dogleg: float = 0.0              # 0 straight .. 1 sharp bend at landing_limit
    bend: str = ''                   # 'L' or 'R': direction the dogleg turns
    fairway_bunkers: float = 0.3     # 0 none .. 1 heavily bunkered landing area
    green_radius: float = 14.0       # yards (14 ~ a 6,000 sq ft green)
    green_speed: float = 11.5        # stimpmeter feet
    green_slope: float = 0.5         # 0 flat .. 1 severe contours
    green_firmness: float = 0.5      # 0 soft/receptive .. 1 firm/fast
    greenside_bunkers: float = 0.5   # 0 none .. 1 surrounded
    green_water: str = ''            # side of the green guarded by water
    wind_exposure: float = 0.5       # 0 sheltered .. 1 fully exposed
    elevation: int = 0               # yards the hole plays longer (+) or shorter (-)
    note: str = ''
    name: str = ''

    def __post_init__(self):
        if self.par not in (3, 4, 5):
            raise ValueError('par must be 3, 4 or 5')
        if self.left not in HAZARDS or self.right not in HAZARDS:
            raise ValueError('unknown side hazard')
        if self.green_water not in GREEN_WATER:
            raise ValueError('unknown green water side')

    @property
    def plays(self):
        return self.yards + self.elevation


@dataclass(frozen=True)
class Course:
    name: str
    country: str
    style: str
    holes: tuple
    typical_wind: float = 9.0        # mph
    city: str = ''
    description: str = ''
    tags: tuple = field(default_factory=tuple)

    def __post_init__(self):
        if len(self.holes) != 18:
            raise ValueError('a course needs 18 holes')

    @property
    def par(self):
        return sum(h.par for h in self.holes)

    @property
    def yards(self):
        return sum(h.yards for h in self.holes)


def _h(n, par, yards, **kw):
    return Hole(n, par, yards, **kw)


def ashford_ridge():
    """Mid-difficulty calibration course: a solid, fair championship parkland.

    Par 72, 7,174 yards. Tournament set-up (11.5 stimp, medium rough). Designed
    so that every attribute gets tested: long and short par 4s, a drivable
    hole, reachable and three-shot par 5s, water carries, tight tree-lined
    holes, doglegs, fast sloping greens and heavily bunkered greens.
    """
    holes = (
        _h(1, 4, 412, fairway_width=36, rough_severity=.4, left='open', right='trees',
           fairway_bunkers=.2, green_radius=15, greenside_bunkers=.4, green_slope=.4,
           note='Gentle opener: wide fairway, generous green.'),
        _h(2, 5, 548, fairway_width=33, left='trees', right='open', fairway_bunkers=.4,
           green_radius=13, green_water='left', greenside_bunkers=.4,
           note='Reachable par 5; pond guards the left side of the green.'),
        _h(3, 3, 178, green_radius=13, greenside_bunkers=.85, green_slope=.55,
           note='Mid-length par 3, bunkers on both sides.'),
        _h(4, 4, 455, fairway_width=30, rough_severity=.6, left='ob', right='trees',
           fairway_bunkers=.3, green_radius=14, greenside_bunkers=.5,
           note='Long, demanding par 4. Out of bounds left.'),
        _h(5, 4, 322, fairway_width=30, left='trees', right='open', fairway_bunkers=.6,
           green_radius=12, greenside_bunkers=.9, green_slope=.6, green_firmness=.6,
           note='Short par 4, drivable for long hitters, green ringed by sand.'),
        _h(6, 3, 214, green_radius=16, greenside_bunkers=.4, green_slope=.4, wind_exposure=.7,
           note='Long par 3 to a large green.'),
        _h(7, 4, 441, fairway_width=31, left='trees', right='trees', landing_limit=290,
           dogleg=.7, bend='R', fairway_bunkers=.4, green_radius=14, greenside_bunkers=.5,
           note='Dogleg right at 290; driving through the corner finds the trees.'),
        _h(8, 4, 398, fairway_width=26, rough_severity=.65, left='trees', right='trees',
           fairway_bunkers=.2, green_radius=11.5, greenside_bunkers=.6, green_slope=.6,
           wind_exposure=.2, note='Narrow, tree-lined, small green.'),
        _h(9, 5, 592, fairway_width=34, left='open', right='trees', fairway_bunkers=.6,
           green_radius=14, greenside_bunkers=.6, elevation=8,
           note='True three-shot par 5, uphill.'),
        _h(10, 4, 427, fairway_width=31, left='trees', right='water', fairway_bunkers=.3,
           green_radius=14, greenside_bunkers=.5, note='Water all down the right.'),
        _h(11, 3, 156, green_radius=11, greenside_bunkers=.9, green_slope=.8, green_speed=12.0,
           green_firmness=.65, elevation=-6, note='Short par 3 to a small, steeply contoured green.'),
        _h(12, 4, 468, fairway_width=35, rough_severity=.45, left='open', right='open',
           fairway_bunkers=.4, green_radius=15, greenside_bunkers=.5, wind_exposure=.75,
           note='Longest par 4: open, exposed, long.'),
        _h(13, 5, 528, fairway_width=30, left='trees', right='trees', landing_limit=285,
           dogleg=.5, bend='L', fairway_bunkers=.3, green_radius=13, green_water='front',
           greenside_bunkers=.3, note='Dogleg left; creek in front of the green tempts the long hitter.'),
        _h(14, 4, 372, fairway_width=29, left='trees', right='open', landing_limit=275,
           fairway_bunkers=.8, green_radius=13, greenside_bunkers=.6, green_slope=.6,
           note='Positional: fairway bunkers and a run-out at 275.'),
        _h(15, 4, 445, fairway_width=32, left='open', right='trees', fairway_bunkers=.3,
           green_radius=14, greenside_bunkers=.5, wind_exposure=.8, elevation=12,
           note='Uphill and exposed to the wind.'),
        _h(16, 3, 192, green_radius=13, green_water='front', greenside_bunkers=.35,
           green_slope=.5, wind_exposure=.7, note='All carry over water.'),
        _h(17, 5, 565, fairway_width=32, left='trees', right='ob', fairway_bunkers=.5,
           green_radius=14, greenside_bunkers=.6, note='Reachable for long hitters; OB right.'),
        _h(18, 4, 461, fairway_width=31, rough_severity=.6, left='water', right='trees',
           fairway_bunkers=.4, green_radius=14, greenside_bunkers=.6, green_slope=.55,
           note='Strong finisher, lake left.'),
    )
    return Course('Ashford Ridge Golf Club', 'USA', 'Parkland', holes, typical_wind=9.0,
                  description='Mid-difficulty championship parkland used to calibrate the engine.',
                  tags=('calibration', 'mid'))


def _scale_hole(h, *, yards, width, rough, hazard_map, green_radius, speed, slope, firm,
                bunkers, water, exposure):
    return replace(h, yards=round(h.yards * yards), fairway_width=h.fairway_width * width,
                   rough_severity=min(1., max(0., h.rough_severity + rough)),
                   left=hazard_map.get(h.left, h.left), right=hazard_map.get(h.right, h.right),
                   landing_limit=round(h.landing_limit * yards) if h.landing_limit else 0,
                   green_radius=h.green_radius * green_radius, green_speed=h.green_speed + speed,
                   green_slope=min(1., max(0., h.green_slope + slope)),
                   green_firmness=min(1., max(0., h.green_firmness + firm)),
                   greenside_bunkers=min(1., max(0., h.greenside_bunkers + bunkers)),
                   green_water=water(h), wind_exposure=min(1., max(0., h.wind_exposure + exposure)))


def easy_course():
    """Short, wide, soft, slow-green resort/municipal course."""
    base = ashford_ridge()
    holes = tuple(_scale_hole(h, yards=.90, width=1.35, rough=-.3, hazard_map={'trees': 'open', 'ob': 'open'},
                              green_radius=1.2, speed=-2.0, slope=-.25, firm=-.25, bunkers=-.3,
                              water=lambda h: h.green_water if h.number == 16 else '', exposure=-.2)
                  for h in base.holes)
    return Course('Meadowbrook Links (easy)', 'USA', 'Parkland', holes, typical_wind=6.0,
                  description='Short, wide and forgiving.', tags=('calibration', 'easy'))


def hard_course():
    """Long, narrow, firm, fast, water-heavy championship brute."""
    base = ashford_ridge()
    def water(h):
        return h.green_water or ('front' if h.par == 3 else 'right' if h.number in (4, 15) else '')
    holes = tuple(_scale_hole(h, yards=1.065, width=.80, rough=.3, hazard_map={'open': 'trees'},
                              green_radius=.85, speed=2.0, slope=.2, firm=.25, bunkers=.2,
                              water=water, exposure=.15)
                  for h in base.holes)
    return Course('Blackthorn National (hard)', 'USA', 'Championship', holes, typical_wind=14.0,
                  description='Long, narrow, water everywhere, fast contoured greens.',
                  tags=('calibration', 'hard'))


def tight_classic():
    """Short, narrow, tree-lined old classic with small, fast, sloping greens."""
    base = ashford_ridge()
    holes = tuple(_scale_hole(h, yards=.94, width=.78, rough=.15, hazard_map={'open': 'trees', 'water': 'trees'},
                              green_radius=.82, speed=1.0, slope=.2, firm=.15, bunkers=.1,
                              water=lambda h: h.green_water, exposure=-.3)
                  for h in base.holes)
    holes = tuple(replace(h, rough_width=min(h.rough_width, 8.0)) for h in holes)
    return Course('Old Elm Club (tight)', 'USA', 'Woodland', holes, typical_wind=5.0,
                  description='Short but narrow: trees everywhere, tiny fast greens.', tags=('calibration', 'tight'))


def windy_links():
    """Open, firm seaside links: no trees, deep pot bunkers, wind exposure everywhere."""
    base = ashford_ridge()
    holes = tuple(_scale_hole(h, yards=.99, width=1.05, rough=.2, hazard_map={'trees': 'open', 'water': 'open'},
                              green_radius=1.05, speed=-1.0, slope=.1, firm=.3, bunkers=.15,
                              water=lambda h: '', exposure=.45)
                  for h in base.holes)
    holes = tuple(replace(h, rough_width=h.rough_width + 10) for h in holes)
    return Course('Saltcliff Links (windy)', 'Scotland', 'Links', holes, typical_wind=20.0,
                  description='Firm, open, fully exposed seaside links.', tags=('calibration', 'links'))


def georgia_national():
    """The hardest test in the world: a fictional major-championship course near Athens, Georgia.

    7,615 yards, par 72. Big elevation changes, pines lining every hole, a creek and ponds through the
    second nine, and the fastest, most contoured greens in golf (13.5-14 stimp, false fronts, tiers).
    The rough is only a short second cut: the course defends itself with angles, trees, water and
    greens, so a miss on the wrong side is punished far more than a miss into grass.
    """
    G = dict(green_speed=12.5, green_firmness=.62, rough_severity=.25, rough_width=9, left='trees', right='trees')
    def h(n, par, yards, name, note, **kw):
        return Hole(n, par, yards, name=name, note=note, **{**G, **kw})
    holes = (
        h(1, 4, 450, 'Sweetgum', 'Uphill opener; deep bunker right of the landing area, green falls off on all sides.',
          fairway_width=35, fairway_bunkers=.6, green_radius=14, green_slope=0.765, greenside_bunkers=.4, elevation=10),
        h(2, 5, 590, 'Red Clay', 'Plunges downhill and doglegs left; reachable with a draw, bunkers guard the front.',
          fairway_width=37, landing_limit=305, dogleg=.5, bend='L', fairway_bunkers=.5, green_radius=14.5,
          green_slope=0.72, greenside_bunkers=.6, elevation=-15),
        h(3, 4, 355, 'Tabletop', 'Short par 4 to a tiny, raised, sloping green; bunkers at 290 punish the greedy.',
          fairway_width=33, landing_limit=285, fairway_bunkers=.8, green_radius=11.5, green_slope=0.855,
          greenside_bunkers=.3, green_firmness=.85),
        h(4, 3, 240, 'Long Leaf', 'Brutally long downhill par 3 to a two-tier green.', green_radius=14.5,
          green_slope=0.765, greenside_bunkers=.6, elevation=-10, wind_exposure=.6),
        h(5, 4, 500, 'Magnolia Rise', 'Long, uphill, dogleg left; deep fairway bunkers at the corner.',
          fairway_width=34, landing_limit=315, dogleg=.4, bend='L', fairway_bunkers=.8, green_radius=14,
          green_slope=0.81, greenside_bunkers=.3, elevation=12),
        h(6, 3, 185, 'Cliffside', 'Plays well downhill to a green with a severe back-left plateau.', green_radius=13.5,
          green_slope=0.9, greenside_bunkers=.5, elevation=-18),
        h(7, 4, 455, 'Pine Chute', 'Narrow chute through the pines to a small green ringed by sand.',
          fairway_width=29, rough_width=6, fairway_bunkers=.2, green_radius=12.5, green_slope=0.72, greenside_bunkers=.95,
          wind_exposure=.2),
        h(8, 5, 575, 'Summit', 'Long uphill par 5, blind second, a mound-guarded green.', fairway_width=36,
          fairway_bunkers=.6, green_radius=14.5, green_slope=0.765, greenside_bunkers=.2, elevation=22),
        h(9, 4, 465, 'False Front', 'Downhill dogleg left; anything short of the pin rolls 40 yards back down.',
          fairway_width=35, landing_limit=310, dogleg=.4, bend='L', fairway_bunkers=.3, green_radius=13.5,
          green_slope=0.855, greenside_bunkers=.5, elevation=-12),
        h(10, 4, 500, 'Cathedral', 'Huge downhill dogleg left through towering pines.', fairway_width=37,
          landing_limit=320, dogleg=.5, bend='L', fairway_bunkers=.3, green_radius=14.5, green_slope=0.765,
          greenside_bunkers=.4, elevation=-25),
        h(11, 4, 525, 'Long Water', 'Longest par 4 on the course; a pond guards the left of the green.',
          fairway_width=34, fairway_bunkers=.2, green_radius=14, green_water='left', green_slope=0.72,
          greenside_bunkers=.3, wind_exposure=.6),
        h(12, 3, 160, 'Swirl', 'Short but terrifying: all carry over a creek to a shallow green in swirling wind.',
          green_radius=11, green_water='front', green_slope=0.675, greenside_bunkers=.7, wind_exposure=.95),
        h(13, 5, 545, 'Azalea Bend', 'Sharp dogleg left; creek in front of the green tempts the long hitter.',
          fairway_width=35, landing_limit=290, dogleg=.6, bend='L', fairway_bunkers=.2, green_radius=14.5,
          green_water='front', green_slope=0.765, greenside_bunkers=.5),
        h(14, 4, 445, 'Rollercoaster', 'No bunkers at all, and the wildest green on the property.',
          fairway_width=36, fairway_bunkers=0, green_radius=14.5, green_slope=0.9, greenside_bunkers=0),
        h(15, 5, 555, 'Second Chance', 'Pond in front of a green that runs away from you; eagle or disaster.',
          fairway_width=36, fairway_bunkers=.2, green_radius=13, green_water='front', green_slope=0.765,
          greenside_bunkers=.1, green_firmness=.85),
        h(16, 3, 175, 'Mirror Pond', 'Water down the entire left; the green funnels toward it.', green_radius=14,
          green_water='left', green_slope=0.81, greenside_bunkers=.5, wind_exposure=.6),
        h(17, 4, 445, 'Old Oak', 'Tee shot must avoid the great oak; a crowned green rejects poor approaches.',
          fairway_width=32, fairway_bunkers=.2, green_radius=13.5, green_slope=0.81, greenside_bunkers=.5),
        h(18, 4, 470, 'The Climb', 'Uphill through a narrow chute; bunkers in the landing area, a severe two-tier green.',
          fairway_width=30, rough_width=6, fairway_bunkers=.8, green_radius=13.5, green_slope=0.855,
          greenside_bunkers=.6, elevation=15),
    )
    return Course('Georgia National Golf Club', 'USA', 'Championship Parkland', holes, typical_wind=8.0,
                  city='Athens, Georgia',
                  description='The hardest course in the world. Home of the Legends of Golf Masters Event.',
                  tags=('major', 'fixed-venue', 'extreme'))


def cedar_creek_municipal():
    """The easiest test in the world: a fictional municipal course in Muncie, Indiana.

    Par 72, 6,180 yards. Wide, flat, open fairways with light rough, very few trees, one pond,
    big slow flat greens and little sand: the kind of course that hosts high-school tournaments.
    """
    E = dict(rough_severity=.15, rough_width=18, left='open', right='open', fairway_bunkers=.1,
             green_radius=14.5, green_speed=9.0, green_slope=.25, green_firmness=.3, greenside_bunkers=.2,
             wind_exposure=.3)
    def h(n, par, yards, note, **kw):
        return Hole(n, par, yards, note=note, **{**E, **kw})
    holes = (
        h(1, 4, 365, 'Straightaway opener; houses (out of bounds) down the right.', fairway_width=43, right='ob'),
        h(2, 4, 330, 'Short par 4, one bunker left of the green.', fairway_width=40, greenside_bunkers=.3),
        h(3, 3, 150, 'Short par 3 to a huge green.', green_radius=16),
        h(4, 5, 495, 'Short par 5, reachable for long hitters.', fairway_width=41),
        h(5, 4, 380, 'Gentle dogleg, trees on the right.', fairway_width=37, right='trees', left='trees'),
        h(6, 4, 345, 'Open and flat.', fairway_width=45),
        h(7, 3, 165, 'Over a shallow dip to a flat green.', green_radius=16),
        h(8, 4, 395, 'Longest par 4 on the front; out of bounds left along the road.', fairway_width=39, left='ob'),
        h(9, 5, 480, 'Par 5 back to the clubhouse.', fairway_width=42),
        h(10, 4, 360, 'Wide and downhill.', fairway_width=43, elevation=-6),
        h(11, 4, 340, 'Short par 4; creek runs down the left.', fairway_width=39, left='water'),
        h(12, 3, 175, 'The one water hole: a pond left of the green.', green_water='left', green_radius=16),
        h(13, 5, 505, 'Reachable par 5, out of bounds far right.', fairway_width=39, right='ob'),
        h(14, 4, 370, 'Tree-lined both sides.', fairway_width=37, left='trees', right='trees'),
        h(15, 4, 355, 'Short; houses (out of bounds) left.', fairway_width=43, left='ob'),
        h(16, 3, 140, 'Shortest hole on the course.', green_radius=16),
        h(17, 5, 490, 'Short par 5, bunker in front of the green.', fairway_width=40, greenside_bunkers=.35),
        h(18, 4, 340, 'Easy finisher, big green.', fairway_width=43, green_radius=16),
    )
    return Course('Cedar Creek Municipal Golf Course', 'USA', 'Municipal', holes, typical_wind=7.0,
                  city='Muncie, Indiana', description='The easiest course in the world: a high-school tournament venue.',
                  tags=('municipal', 'easiest'))
