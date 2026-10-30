"""The calendar contract: one versioned specification of each season's fixed structure (roadmap v14,
"Calendar and qualification rework").

Every week-dependent fact the calendar, the qualification rules and the season engine rely on is declared
here, per calendar version: the major anchors, the 36 Premier events' weeks, the fixed-week anchors
(elite amateur championships, college post-season, qualifying stages, Q-Schools), the qualifying waves,
the ranking and points cut-offs each major reads, the opportunity weeks after the majors and the city
pools of venue-bound events. calendar.py builds the series from it; qualification.py builds each major's
routes from it; the season engine reads the cut-offs and stage waves from it.

Versions
--------
- **v1**: the calendar every world used before calendar versions (majors in weeks 18, 24, 25 and 30). It is
  frozen: a world saved without a version keeps it for good, and nothing here may change what it builds
  (the tests compare it with the series the engine built before this file existed).
- **v2**: the reference calendar of roadmap v14 (majors in weeks 15, 20, 25 and 30, five weeks apart; the
  36 Premier events at their reference weeks; post-major opportunity events in weeks 16, 21, 26 and 31;
  USA Open local waves 17/19/21, international final 22, domestic final 24; Britannia regional waves 26 and
  27, final 28, Scotland 29; club professionals' sectionals 12 and championship 18; Asian Challenger
  Q-School in week 51 for the next season). New worlds use it.

A season's version is kept with the season (the archive records it), so a season is always read with the
calendar it was played under; an old world is never moved to a new version except by a separately approved
migration of a copy at a season boundary (not implemented: see docs/CALENDAR_V2.md).

Stable identities: series keep their ids across versions. The qualifying waves are the one place the old
ids named a week ("USA_OPEN_LOCAL_W19"); v2 names waves instead ("USA_OPEN_LOCAL_1"), and ALIASES maps one
scheme onto the other so a manifest or a comparison can line them up.
"""
from __future__ import annotations

from dataclasses import dataclass, field

LEGACY = 'v1'                  # worlds saved before calendar versions
DEFAULT = 'v2'                 # new worlds


@dataclass(frozen=True)
class Spec:
    version: str
    label: str
    majors: dict                         # series id -> week (Tour Masters, Premier Tour Championship, USA, Britannia)
    premier_weeks: dict                  # Premier event name -> fixed week (None: placed by the generator)
    anchors: dict                        # fixed-week anchor series id -> week (amateur, college, club pro)
    usa_local: tuple                     # ((series id, week, label), ...) USA Open local qualifying waves
    usa_final_intl: int                  # USA Open international final qualifying (direct entries only)
    usa_final: int                       # USA Open domestic final qualifying (local advancers and direct entries)
    britannia_regional: tuple            # ((series id, week, label), ...) Britannia regional qualifying waves
    britannia_final: int
    qschool: dict                        # Q-School stage series id -> week
    qschool_next_season: frozenset       # stages played late in a season whose cards are for the next one
    cutoffs: dict                        # cut-off name -> week its snapshot is taken (end of that week)
    opportunity_after_majors: tuple      # weeks that must hold a Premier opportunity event
    city_pools: dict = field(default_factory=dict)   # Premier event name -> host city pool (venue-bound events)
    major_spacing: int = 0               # weeks between consecutive majors (0: not enforced)
    travel: bool = False                 # day-level travel check between events in one week
    snapshots: bool = False              # cut-off rules read their own immutable snapshot (never a later one)
    amateur_award: tuple = ()            # (week after which the season's leading amateur is named, routes)
    rules_note: str = ''

    @property
    def major_weeks(self):
        return frozenset(self.majors.values())

    def major_week(self, sid):
        return self.majors[sid]

    def week_of(self, sid):
        """The fixed week of a series this specification places (None for generated events)."""
        if sid in self.majors:
            return self.majors[sid]
        if sid in self.anchors:
            return self.anchors[sid]
        if sid in self.qschool:
            return self.qschool[sid]
        for sid_, wk, _ in self.usa_local + self.britannia_regional:
            if sid_ == sid:
                return wk
        return {'USA_OPEN_FINAL_INTL': self.usa_final_intl, 'USA_OPEN_FINAL': self.usa_final,
                'BRITANNIA_FINAL': self.britannia_final}.get(sid)


# ---------------------------------------------------------------------------------------------
# v1: the calendar as it was (frozen)
# ---------------------------------------------------------------------------------------------
V1 = Spec(
    version='v1', label='Classic calendar (majors weeks 18, 24, 25, 30)',
    majors={'TOUR_MASTERS': 18, 'PREMIER_TOUR_CHAMPIONSHIP': 24, 'USA_OPEN': 25, 'BRITANNIA_OPEN': 30},
    premier_weeks={
        'Pacific Coast Pro-Am': 6, 'Premier Players Championship': 11, 'Heartland Invitational': 22,
        'Premier Tour Finals': 45, 'Gulf Coast Classic': 19, 'Great Lakes Open': 26, 'Island Championship': 2,
        'Autumn Classic': 41, 'Canada Open': 23, 'Mexico Open': 9,
        'Desert Classic': None, 'Texas Open': None, 'Carolina Championship': None, 'Southern Invitational': None,
        'Pacific Northwest Open': None, 'Mid-Atlantic Championship': None,
        'Scotland Open': 29, 'European Championship': 38, 'Desert Tour Championship': 47, 'Nordic Masters': 26,
        'Netherlands Open': 31, 'Kenya Open': 10, 'South Africa Open': 50, 'Ireland Open': 37, 'Spain Open': 40,
        'France Open': 39, 'Gulf Desert Classic': None, 'German Masters': None, 'Italian Championship': None,
        'Australia Open': 49, 'Singapore Classic': 44, 'India Open': 12, 'Japan Premier Championship': None,
        'Korea Championship': None, 'China Masters': None, 'Sandbelt Championship': None},
    anchors={'LATIN_AMERICA_AMATEUR': 3, 'AFRICA_AMATEUR': 9, 'CLUB_PRO_SECTIONALS': 12, 'CLUB_PRO_CHAMPIONSHIP': 16,
             'BRITANNIA_AMATEUR': 23, 'EUROPEAN_AMATEUR': 27, 'USA_AMATEUR_QUALIFYING': 30, 'USA_AMATEUR': 33,
             'USA_MID_AMATEUR': 38, 'ASIA_PACIFIC_AMATEUR': 43, 'CONFERENCE_CHAMPIONSHIP': 17,
             'COLLEGE_REGIONAL': 20, 'COLLEGE_NATIONAL_CHAMPIONSHIP': 21, 'SMALL_COLLEGE_CHAMPIONSHIP': 20,
             'INTL_UNIVERSITY_CHAMPIONSHIP': 28},
    usa_local=(('USA_OPEN_LOCAL_W19', 19, 'week 19'), ('USA_OPEN_LOCAL_W20', 20, 'week 20'),
               ('USA_OPEN_LOCAL_W21', 21, 'week 21')),
    usa_final_intl=22, usa_final=23,
    britannia_regional=(('BRITANNIA_REGIONAL_W26', 26, 'week 26'), ('BRITANNIA_REGIONAL_W27', 27, 'week 27')),
    britannia_final=28,
    qschool={'PT_QSCHOOL_PRE': 40, 'PT_QSCHOOL_FIRST': 42, 'PT_QSCHOOL_SECOND': 46, 'PT_QSCHOOL_FINAL': 50,
             'EU_QSCHOOL_FIRST': 37, 'EU_QSCHOOL_SECOND': 44, 'EU_QSCHOOL_FINAL': 48, 'JP_QSCHOOL_FINAL': 48,
             'ASIA_QSCHOOL_FINAL': 2},
    qschool_next_season=frozenset({'PT_QSCHOOL_PRE', 'PT_QSCHOOL_FIRST', 'PT_QSCHOOL_SECOND', 'PT_QSCHOOL_FINAL',
                                   'EU_QSCHOOL_FIRST', 'EU_QSCHOOL_SECOND', 'EU_QSCHOOL_FINAL', 'JP_QSCHOOL_FINAL',
                                   'ASIA_QSCHOOL_FINAL'}),
    cutoffs={'masters_ranking': 16, 'masters_wins_through': 17, 'masters_wins_from': 19,
             'pga_points': 22, 'pga_ranking': 22, 'pga_wins_through': 23, 'pga_wins_from': 25,
             'usa_ranking_1': 21, 'usa_ranking_2': 23, 'usa_fill': 23,
             'britannia_ranking': 21, 'britannia_fill': 26, 'britannia_amateur': 26},
    opportunity_after_majors=(19, 26, 31),
    rules_note='The calendar every world used before calendar versions; kept unchanged for those worlds.',
)


# ---------------------------------------------------------------------------------------------
# v2: the roadmap v14 reference calendar
# ---------------------------------------------------------------------------------------------
V2 = Spec(
    version='v2', label='Reference calendar (majors weeks 15, 20, 25, 30)',
    majors={'TOUR_MASTERS': 15, 'PREMIER_TOUR_CHAMPIONSHIP': 20, 'USA_OPEN': 25, 'BRITANNIA_OPEN': 30},
    premier_weeks={
        # Americas: 4 flagship, 8 standard (2 national opens), 4 opportunity
        'Island Championship': 2, 'Desert Classic': 4, 'Pacific Coast Pro-Am': 6, 'Mexico Open': 9,
        'Premier Players Championship': 11, 'Southern Invitational': 13, 'Texas Open': 14, 'Gulf Coast Classic': 16,
        'Carolina Championship': 19, 'Heartland Invitational': 23, 'Canada Open': 24, 'Great Lakes Open': 26,
        'Pacific Northwest Open': 34, 'Mid-Atlantic Championship': 36, 'Autumn Classic': 41, 'Premier Tour Finals': 45,
        # Europe: 3 flagship, 7 standard (4 national opens), 3 opportunity
        'Gulf Desert Classic': 5, 'Kenya Open': 10, 'Italian Championship': 18, 'Nordic Masters': 21,
        'Scotland Open': 29, 'Netherlands Open': 31, 'German Masters': 35, 'Ireland Open': 37,
        'European Championship': 38, 'France Open': 39, 'Spain Open': 40, 'Desert Tour Championship': 47,
        'South Africa Open': 50,
        # Asia-Pacific: 1 flagship, 5 standard (1 national open), 1 opportunity
        'India Open': 12, 'Japan Premier Championship': 13, 'Korea Championship': 36, 'China Masters': 42,
        'Singapore Classic': 44, 'Sandbelt Championship': 46, 'Australia Open': 49},
    anchors={'LATIN_AMERICA_AMATEUR': 3, 'AFRICA_AMATEUR': 9, 'CLUB_PRO_SECTIONALS': 12, 'CLUB_PRO_CHAMPIONSHIP': 18,
             'BRITANNIA_AMATEUR': 26, 'EUROPEAN_AMATEUR': 27, 'USA_AMATEUR_QUALIFYING': 30, 'USA_AMATEUR': 33,
             'USA_MID_AMATEUR': 38, 'ASIA_PACIFIC_AMATEUR': 43, 'CONFERENCE_CHAMPIONSHIP': 17,
             'COLLEGE_REGIONAL': 21, 'COLLEGE_NATIONAL_CHAMPIONSHIP': 22, 'SMALL_COLLEGE_CHAMPIONSHIP': 20,
             'INTL_UNIVERSITY_CHAMPIONSHIP': 28},
    usa_local=(('USA_OPEN_LOCAL_1', 17, 'wave 1, week 17'), ('USA_OPEN_LOCAL_2', 19, 'wave 2, week 19'),
               ('USA_OPEN_LOCAL_3', 21, 'wave 3, week 21')),
    usa_final_intl=22, usa_final=24,
    britannia_regional=(('BRITANNIA_REGIONAL_1', 26, 'wave 1, week 26'), ('BRITANNIA_REGIONAL_2', 27, 'wave 2, week 27')),
    britannia_final=28,
    qschool={'PT_QSCHOOL_PRE': 40, 'PT_QSCHOOL_FIRST': 42, 'PT_QSCHOOL_SECOND': 46, 'PT_QSCHOOL_FINAL': 50,
             'EU_QSCHOOL_FIRST': 37, 'EU_QSCHOOL_SECOND': 44, 'EU_QSCHOOL_FINAL': 48, 'JP_QSCHOOL_FINAL': 48,
             'ASIA_QSCHOOL_FINAL': 51},
    qschool_next_season=frozenset({'PT_QSCHOOL_PRE', 'PT_QSCHOOL_FIRST', 'PT_QSCHOOL_SECOND', 'PT_QSCHOOL_FINAL',
                                   'EU_QSCHOOL_FIRST', 'EU_QSCHOOL_SECOND', 'EU_QSCHOOL_FINAL', 'JP_QSCHOOL_FINAL',
                                   'ASIA_QSCHOOL_FINAL'}),
    # Each cut-off is the ranking or points list published at the end of that week (an immutable snapshot)
    cutoffs={'masters_ranking': 13, 'masters_wins_through': 14, 'masters_wins_from': 16,
             'pga_points': 18, 'pga_ranking': 18, 'pga_wins_through': 19, 'pga_wins_from': 21,
             'usa_ranking_1': 20, 'usa_ranking_2': 24, 'usa_fill': 24,
             'britannia_ranking': 21, 'britannia_fill': 29, 'amateur_award': 33},
    opportunity_after_majors=(16, 21, 26, 31),
    # events named for a place are played there (the classic calendar drew them from any US city in season)
    city_pools={'Texas Open': ('Dallas, Texas', 'Fort Worth, Texas', 'Houston, Texas', 'San Antonio, Texas',
                               'Austin, Texas'),
                'Gulf Coast Classic': ('Houston, Texas', 'New Orleans, Louisiana', 'Tampa, Florida', 'Naples, Florida'),
                'Desert Classic': ('Scottsdale, Arizona', 'Phoenix, Arizona', 'Tucson, Arizona', 'Las Vegas, Nevada',
                                   'Palm Springs, California'),
                'Carolina Championship': ('Pinehurst, North Carolina', 'Charlotte, North Carolina',
                                          'Greensboro, North Carolina', 'Myrtle Beach, South Carolina',
                                          'Hilton Head Island, South Carolina', 'Kiawah Island, South Carolina'),
                'Southern Invitational': ('Atlanta, Georgia', 'Savannah, Georgia', 'Birmingham, Alabama',
                                          'Nashville, Tennessee', 'Memphis, Tennessee'),
                'Great Lakes Open': ('Chicago, Illinois', 'Detroit, Michigan', 'Grand Rapids, Michigan',
                                     'Cleveland, Ohio', 'Milwaukee, Wisconsin', 'Minneapolis, Minnesota'),
                'Pacific Northwest Open': ('Portland, Oregon', 'Bandon, Oregon', 'Seattle, Washington'),
                'Mid-Atlantic Championship': ('Bethesda, Maryland', 'Richmond, Virginia', 'Philadelphia, Pennsylvania')},
    major_spacing=5, travel=True, snapshots=True,
    amateur_award=(33, ('USA_OPEN', 'BRITANNIA_OPEN')),
    rules_note=('Roadmap v14 reference calendar: majors five weeks apart; qualification read from immutable '
                'cut-off snapshots; amateur titles feed the edition their dates allow; the season\'s leading '
                'amateur (after the USA Amateur, week 33) earns conditional places in next season\'s USA and '
                'Britannia Opens.'),
)

SPECS = {'v1': V1, 'v2': V2}
# The qualifying waves were named by week in v1, by wave in v2: one identity map for both
ALIASES = {'USA_OPEN_LOCAL_W19': 'USA_OPEN_LOCAL_1', 'USA_OPEN_LOCAL_W20': 'USA_OPEN_LOCAL_2',
           'USA_OPEN_LOCAL_W21': 'USA_OPEN_LOCAL_3', 'BRITANNIA_REGIONAL_W26': 'BRITANNIA_REGIONAL_1',
           'BRITANNIA_REGIONAL_W27': 'BRITANNIA_REGIONAL_2'}


def spec(version=None):
    return SPECS[version or LEGACY]


def canonical(series_id):
    """The series id under the wave naming (identity for every other series)."""
    return ALIASES.get(series_id, series_id)
