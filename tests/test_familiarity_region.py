"""Geography, familiarity and course use (roadmap G1): every course's state / province normalised from its
city (unknown, never guessed, when the geography lacks the city), how each course came to be built, why a
course hosts no events (a local club, explained by the venue policy, never forced into a rotation), and the
regional familiarity baseline (rules 2026-11-08): bounded, a floor never a sum, counted once for identical
birthplace and residence, honest about unknown places, deterministic; home clubs (recorded, dated, the same
floor once); local hosting of unused municipal courses (venue assignment only, bounded, no rotation); and the
profile showing rounds played and, separately, the familiarity the engine uses.

Quick unit tests only: no season is simulated and no world is generated.
Run from the project folder:  python -m unittest tests.test_familiarity_region -v
"""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import familiarity as FAM                                         # noqa: E402
from golfsim.course import ashford_ridge                                        # noqa: E402
from golfsim.engine import play_round                                           # noqa: E402
from golfsim.golfer import uniform_golfer                                       # noqa: E402
from golfsim.residence import Places                                            # noqa: E402
from golfsim.season import Season, _for_course                                  # noqa: E402
from golfsim import home_clubs as HC                                            # noqa: E402
from golfsim.calendar import WorldCalendar                                      # noqa: E402
from golfsim.course_library import (LOCAL_LEVELS, CourseLibrary, course_place, default_library,   # noqa: E402
                                    event_level, venue_role)
from golfsim.residence import subdivision                                       # noqa: E402


def _course(name, city, cls, layouts):
    return {'name': name, 'city': city, 'country': 'England', 'class': cls, 'layouts': {k: {} for k in layouts}}


class CoursePlaceTests(unittest.TestCase):
    def test_subdivision_from_city(self):
        self.assertEqual(course_place({'city': 'Southport', 'country': 'England'}), ('England', 'Merseyside'))
        self.assertEqual(course_place({'city': 'Athens, Georgia', 'country': 'USA'}), ('USA', 'Georgia'))
        self.assertEqual(course_place({'city': 'Helsinki', 'country': 'Finland'}), ('Finland', 'Uusimaa'))

    def test_unknown_city_is_honestly_unknown(self):
        self.assertEqual(course_place({'city': 'Nowhere Town', 'country': 'England'}), ('England', None))
        self.assertEqual(course_place({'city': '', 'country': ''}), (None, None))
        # a hand-built Course object without a city
        c = ashford_ridge()
        self.assertEqual(course_place(c), (c.country, None))

    def test_every_library_course_has_a_place_and_origin(self):
        lib = default_library()
        for cid, site in lib.sites.items():
            self.assertEqual(site['subdivision'], subdivision(site['city']), cid)
            self.assertIn(site['origin'], ('calendar', 'club', 'hand-built'), cid)
        self.assertEqual(sum(1 for s in lib.sites.values() if s['origin'] == 'hand-built'), 2)


class VenueRoleTests(unittest.TestCase):
    COURSES = {
        'std': _course('Carrick Fields Links', 'Southport', 'standard', ('Championship', 'Club', 'Forward')),
        'muni': _course('Southport Brook Public Golf Course', 'Southport', 'municipal', ('Regular',)),
        'elite': _course('Royal Holly Rock Golf Links', 'Southport', 'elite', ('Championship',)),
        'lone': _course('Lone Municipal', 'Sandwich', 'municipal', ('Regular',)),
    }

    def test_hosted_course_is_an_event_venue(self):
        self.assertEqual(venue_role(self.COURSES, 'std', 3), ('event venue', ''))
        self.assertEqual(venue_role(self.COURSES, 'muni', 3, local_first=False), ('event venue', ''))
        role, why = venue_role(self.COURSES, 'muni', 3)
        self.assertEqual(role, 'local club and event venue')
        self.assertIn('Local hosting (rules 2026-11-08)', why)

    def test_unused_municipal_under_local_hosting(self):
        role, why = venue_role(self.COURSES, 'muni', 0)
        self.assertEqual(role, 'local club')
        self.assertIn('none has come to it yet', why)
        self.assertIn('for the first time', why)
        self.assertIn('nothing rotates', why)

    def test_unused_municipal_behind_a_standard_course_before_local_hosting(self):
        role, why = venue_role(self.COURSES, 'muni', 0, local_first=False)
        self.assertEqual(role, 'local club')
        self.assertIn('Carrick Fields Links', why)
        self.assertIn('low-level', why)
        self.assertIn('entry-level', why)
        self.assertNotIn('Royal Holly Rock', why)          # an elite course is no competitor at these levels

    def test_unused_course_that_ranks_first_before_local_hosting(self):
        role, why = venue_role(self.COURSES, 'lone', 0, local_first=False)
        self.assertEqual(role, 'local club')
        self.assertIn('ranks first in Sandwich', why)


MERSEY, SURREY = ('England', 'Merseyside'), ('England', 'Surrey')


class BaselineTests(unittest.TestCase):
    def test_same_state_gets_the_region_baseline(self):
        self.assertEqual(FAM.baseline(MERSEY, [MERSEY]), (FAM.REGION_ROUNDS, 'region'))
        self.assertEqual(FAM.baseline(MERSEY, [None, MERSEY]), (FAM.REGION_ROUNDS, 'region'))

    def test_other_state_or_country_gets_nothing(self):
        self.assertEqual(FAM.baseline(MERSEY, [SURREY]), (0.0, None))
        self.assertEqual(FAM.baseline(MERSEY, [('Scotland', 'Fife')]), (0.0, None))
        self.assertEqual(FAM.baseline(MERSEY, []), (0.0, None))
        self.assertEqual(FAM.baseline(MERSEY, [None, None]), (0.0, None))

    def test_identical_birthplace_and_residence_count_once(self):
        once = FAM.baseline(MERSEY, [MERSEY])
        self.assertEqual(FAM.baseline(MERSEY, [MERSEY, MERSEY]), once)
        # a region match and a country-only match: the larger, never the sum
        self.assertEqual(FAM.baseline(MERSEY, [MERSEY, ('England', None)]), once)
        self.assertEqual(FAM.baseline(MERSEY, [('England', None), MERSEY]), once)

    def test_unknown_state_falls_back_to_country_honestly(self):
        self.assertEqual(FAM.baseline(MERSEY, [('England', None)]), (FAM.COUNTRY_ROUNDS, 'country'))
        self.assertEqual(FAM.baseline(('England', None), [SURREY]), (FAM.COUNTRY_ROUNDS, 'country'))
        self.assertEqual(FAM.baseline((None, None), [MERSEY]), (0.0, None))       # a course nowhere known
        self.assertEqual(FAM.baseline(('England', None), [('Wales', None)]), (0.0, None))

    def test_bounded_and_a_floor_never_a_sum(self):
        self.assertLess(FAM.COUNTRY_ROUNDS, FAM.REGION_ROUNDS)
        self.assertLess(FAM.value(FAM.REGION_ROUNDS), 0.2)                      # a few rounds' worth at most
        self.assertLess(FAM.value(FAM.REGION_ROUNDS), FAM.value(FAM.REGION_ROUNDS + 1))
        self.assertEqual(FAM.effective_rounds(0, FAM.REGION_ROUNDS), FAM.REGION_ROUNDS)
        self.assertEqual(FAM.effective_rounds(1, FAM.REGION_ROUNDS), FAM.REGION_ROUNDS)
        self.assertEqual(FAM.effective_rounds(20, FAM.REGION_ROUNDS), 20)          # experience counts in full
        self.assertEqual(FAM.effective_rounds(None, 0.0), 0.0)
        self.assertAlmostEqual(FAM.value(15), 1 - 1 / 2.718281828459045, places=6)


def _season(places, sites):
    """Just what Season.course_baseline reads: places and a library's sites."""
    return SimpleNamespace(places=places, lib=SimpleNamespace(sites=sites))


class SeasonBaselineTests(unittest.TestCase):
    SITES = {'southport-brook': {'city': 'Southport', 'country': 'England'},
             'thistle-pines': {'city': 'Newcastle upon Tyne', 'country': 'England'}}

    def setUp(self):
        P = self.P = Places()
        P.arrive(1, MERSEY, MERSEY, 2027, 0)                       # born and living in Merseyside
        P.arrive(2, ('England', 'Tyne and Wear'), MERSEY, 2027, 0)  # born in Newcastle, lives in Merseyside
        P.arrive(3, ('England', None), SURREY, 2027, 0)            # birthplace known by country only
        P.legacy.add(4)                                            # places never recorded
        self.s = _season(P, self.SITES)

    def base(self, gid, cid):
        return Season.course_baseline(self.s, gid, cid)

    def test_birthplace_and_residence(self):
        self.assertEqual(self.base(1, 'southport-brook'), (FAM.REGION_ROUNDS, 'region'))
        self.assertEqual(self.base(1, 'thistle-pines'), (0.0, None))
        self.assertEqual(self.base(2, 'southport-brook'), (FAM.REGION_ROUNDS, 'region'))   # where they live
        self.assertEqual(self.base(2, 'thistle-pines'), (FAM.REGION_ROUNDS, 'region'))     # where they were born

    def test_unknowns(self):
        self.assertEqual(self.base(3, 'thistle-pines'), (FAM.COUNTRY_ROUNDS, 'country'))
        self.assertEqual(self.base(4, 'southport-brook'), (0.0, None))       # legacy: no baseline
        self.assertEqual(self.base(99, 'southport-brook'), (0.0, None))      # never placed
        self.assertEqual(self.base(1, 'not-a-course'), (0.0, None))

    def test_switch_off_for_a_comparison_arm(self):
        self.s.familiar_base_on = False
        self.assertEqual(self.base(1, 'southport-brook'), (0.0, None))

    def test_residence_is_current(self):
        self.P.move(1, 2028, 53, ('England', 'Tyne and Wear'), 'test move')
        self.assertEqual(self.base(1, 'thistle-pines'), (FAM.REGION_ROUNDS, 'region'))
        self.assertEqual(self.base(1, 'southport-brook'), (FAM.REGION_ROUNDS, 'region'))   # still their birthplace


class EngineInputTests(unittest.TestCase):
    def test_for_course_floor_not_sum_and_record_unchanged(self):
        g = uniform_golfer(60)
        g.familiarity = {'c': 1.0, 'other': 40.0}
        x = _for_course(g, 'c', FAM.REGION_ROUNDS)
        self.assertEqual(x.familiarity, {'c': FAM.REGION_ROUNDS})
        self.assertEqual(g.familiarity, {'c': 1.0, 'other': 40.0})                # the record is untouched
        self.assertEqual(_for_course(g, 'other', FAM.REGION_ROUNDS).familiarity, {'other': 40.0})
        self.assertEqual(_for_course(g, 'new', 0.0).familiarity, {})
        self.assertEqual(_for_course(g, 'new', FAM.COUNTRY_ROUNDS).familiarity, {'new': FAM.COUNTRY_ROUNDS})

    def test_engine_sees_the_baseline_exactly_as_rounds_and_is_deterministic(self):
        course = ashford_ridge()
        fk = course.familiarity_key
        g = uniform_golfer(55)
        floor = _for_course(g, fk, FAM.REGION_ROUNDS)
        played = uniform_golfer(55)
        played.familiarity = {fk: FAM.REGION_ROUNDS}
        a = [play_round(floor, course, random.Random(s)).score for s in range(6)]
        b = [play_round(played, course, random.Random(s)).score for s in range(6)]
        c = [play_round(_for_course(g, fk, FAM.REGION_ROUNDS), course, random.Random(s)).score for s in range(6)]
        self.assertEqual(a, b)
        self.assertEqual(a, c)


class TopCoursesTests(unittest.TestCase):
    def test_top_ten_most_first_ties_stable(self):
        fam = {f'c{i:02d}': float(i) for i in range(1, 15)}
        fam.update({'tie-b': 7.0, 'tie-a': 7.0, 'zero': 0.0})
        top = FAM.top_courses(fam)
        self.assertEqual(len(top), 10)
        self.assertEqual(top[:3], [('c14', 14.0), ('c13', 13.0), ('c12', 12.0)])
        self.assertEqual([k for k, r in top if r == 7.0], ['c07', 'tie-a', 'tie-b'])
        self.assertEqual(FAM.top_courses(fam), top)                                 # deterministic
        self.assertEqual(FAM.top_courses({'zero': 0.0}), [])
        self.assertEqual(FAM.top_courses({'a': 2.5}, n=10), [('a', 2.5)])


class ProfileTests(unittest.TestCase):
    """The playing tab's familiar courses: top ten, values, links, the baseline line (no world needed)."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
        import observer_history as OH
        cls.OH = OH

    def world(self, live_familiar=None, home_club=None, club_familiarity=None):
        courses = {f'c{i}': {'name': f'Course {i}', 'city': 'Southport' if i % 2 else 'Helsinki',
                             'country': 'England' if i % 2 else 'Finland', 'class': 'standard', 'layouts': {}}
                   for i in range(0, 13)}
        courses['far'] = {'name': 'Far Club', 'city': 'Nowhere Town', 'country': 'England', 'class': 'municipal',
                          'layouts': {}}
        people = {}
        if live_familiar is not None:
            people[7] = {'familiar': live_familiar, 'home_club': home_club or []}
            if club_familiarity is not None:
                people[7]['home_club_familiarity'] = club_familiarity
        return SimpleNamespace(live=SimpleNamespace(people=people), a=None, courses=lambda: courses)

    GEO = {'birthplace': {'country': 'England', 'region': 'Merseyside'},
           'residence': {'country': 'England', 'region': 'Merseyside'}}
    P = {'roles': ['golfer'], 'golfer': {}}

    def test_top_ten_with_values_and_links(self):
        rows = [(f'c{i}', float(13 - i)) for i in range(1, 11)]
        html = self.OH.familiar_section(self.world(rows), 7, self.P, self.GEO)
        self.assertEqual(html.count('href="/course/'), 10)
        self.assertIn('<a href="/course/c1">Course 1</a>', html)
        self.assertIn('<td class=n>12</td><td class=n>55.1%</td><td>rounds played</td>', html)
        self.assertIn('Rounds played (actual)', html)
        self.assertIn('Familiarity the engine uses', html)
        self.assertEqual(html.count('Merseyside, England'), 1)                    # identical places named once
        self.assertIn('/rules#course-familiarity', html)
        self.assertLess(html.index('Course 1<'), html.index('Course 2<'))         # most first

    def test_sub_baseline_local_course_shows_the_effective_value(self):
        """Review fixture: 1 actual round at a course in their own region -- the engine uses max(1, 3) rounds,
        18.13%; the profile shows the 1 round played and, separately, that effective value (one decimal)."""
        eff, src = FAM.engine_rounds(1.0, FAM.baseline(MERSEY, [MERSEY, MERSEY]))
        self.assertEqual((eff, src), (FAM.REGION_ROUNDS, 'region'))
        self.assertAlmostEqual(100 * FAM.value(eff), 18.13, places=2)
        self.assertAlmostEqual(100 * FAM.value(1.0), 6.45, places=2)               # what was wrongly shown
        html = self.OH.familiar_section(self.world([('c1', 1.0), ('c2', 1.0)]), 7, self.P, self.GEO)
        row1 = html[html.index('Course 1<'):html.index('Course 2<')]
        self.assertIn('<td class=n>1</td><td class=n>18.1%</td><td>regional baseline (own state / province)</td>', row1)
        self.assertNotIn('6.4%', row1)
        row2 = html[html.index('Course 2<'):]                                      # Helsinki: not their region
        self.assertIn('<td class=n>1</td><td class=n>6.4%</td><td>rounds played</td>', row2)

    def test_home_club_line_and_floor(self):
        clubs = [[2027, 0, 'c3', 'region', ['England', 'Merseyside']]]
        rec = {'course': 'c3', 'rounds': 0.0, 'engine_rounds': 3.0, 'value': round(FAM.value(3.0), 4), 'from': 'region'}
        html = self.OH.familiar_section(self.world([('c1', 5.0)], clubs, rec), 7, self.P, self.GEO)
        self.assertIn('Home club: <a href="/course/c3">Course 3</a> since 2027 (in their state / province)', html)
        self.assertIn('rounds played there 0; familiarity the engine uses there 18.1% '
                      '(regional baseline (own state / province))', html)
        clubs = [[2027, 0, 'c3', 'region', ['England', 'Merseyside']], [2030, 53, 'far', 'country', ['England', None]]]
        geo = {'birthplace': None, 'residence': {'country': 'Wales', 'region': 'Cardiff'}}
        html = self.OH.familiar_section(self.world([('far', 1.0)], clubs), 7, self.P, geo)
        self.assertIn('home-club floor', html)                                     # the floor, from the club alone
        self.assertIn('18.1%', html)
        self.assertIn('Earlier home clubs: <a href="/course/c3">Course 3</a> from 2027', html)

    def test_home_club_outside_the_top_ten_uses_its_recorded_rounds(self):
        """Review fixture: home club c10 has 10 rounds, c0-c9 have 20 each, so the club is not in the top ten.
        The engine uses 10 rounds there (48.6583%); the profile must show that, never 18.1% from an assumed 0."""
        rows = [(f'c{i}', 20.0) for i in range(10)]
        clubs = [[2027, 0, 'c10', 'region', ['England', 'Merseyside']]]
        eff, src = FAM.engine_rounds(10.0, FAM.home_floor(FAM.baseline(('Finland', 'Uusimaa'), [MERSEY]), True))
        self.assertEqual((eff, src), (10.0, 'played'))
        self.assertAlmostEqual(100 * FAM.value(eff), 48.6583, places=4)
        rec = {'course': 'c10', 'rounds': 10.0, 'engine_rounds': 10.0, 'value': round(FAM.value(10.0), 4),
               'from': 'played'}
        html = self.OH.familiar_section(self.world(rows, clubs, rec), 7, self.P, self.GEO)
        self.assertNotIn('/course/c10">Course 10</a></td>', html)                 # not in the table
        self.assertIn('Home club: <a href="/course/c10">Course 10</a>', html)
        self.assertIn('rounds played there 10; familiarity the engine uses there 48.7% (rounds played)', html)
        self.assertNotIn('18.1%', html.split('Home club:')[1].split('</p>')[0])

    def test_home_club_without_a_record_claims_no_value(self):
        rows = [(f'c{i}', 20.0) for i in range(10)]
        clubs = [[2027, 0, 'c10', 'region', ['England', 'Merseyside']]]
        html = self.OH.familiar_section(self.world(rows, clubs), 7, self.P, self.GEO)
        line = html.split('Home club:')[1].split('</p>')[0]
        self.assertNotIn('%', line)
        self.assertNotIn('rounds played there', line)
        stale = {'course': 'c3', 'rounds': 4.0, 'engine_rounds': 4.0, 'value': 0.2341, 'from': 'played'}
        html = self.OH.familiar_section(self.world(rows, clubs, stale), 7, self.P, self.GEO)
        self.assertNotIn('%', html.split('Home club:')[1].split('</p>')[0])        # another club's record: ignored

    def test_season_records_the_club_figures_explicitly(self):
        P = Places()
        P.arrive(1, MERSEY, MERSEY, 2027, 0)
        s = _hc_season(P, (1,))
        s.course_baseline = lambda gid, cid: Season.course_baseline(s, gid, cid)
        HC.assign(s, 2027, 0)
        club = HC.current(s, 1)
        g = SimpleNamespace(id=1, familiarity={club: 10.0, 'merse-std': 20.0})
        self.assertEqual(HC.familiarity_at_club(s, g), {'course': club, 'rounds': 10.0, 'engine_rounds': 10.0,
                                                        'value': round(FAM.value(10.0), 4), 'from': 'played'})
        g = SimpleNamespace(id=1, familiarity={})
        self.assertEqual(HC.familiarity_at_club(s, g)['engine_rounds'], FAM.REGION_ROUNDS)
        self.assertEqual(HC.familiarity_at_club(s, g)['from'], 'region')
        self.assertIsNone(HC.familiarity_at_club(s, SimpleNamespace(id=2, familiarity={})))

    def test_archived_history_and_unrecorded(self):
        w = self.world()
        p = {'roles': ['golfer'], 'golfer': {'familiar': [['c3', 4.0]]}}
        html = self.OH.familiar_section(w, 7, p, None)
        self.assertIn('as the history ends', html)
        self.assertIn('Birthplace and residence unknown', html)
        html = self.OH.familiar_section(w, 7, {'roles': ['golfer'], 'golfer': {}}, None)
        self.assertIn('Not recorded for this history', html)
        self.assertEqual(self.OH.familiar_section(w, 7, {'roles': ['coach']}, None), '')


SITES = {
    'merse-muni-a': {'name': 'A', 'city': 'Southport', 'country': 'England', 'cls': 'municipal'},
    'merse-muni-b': {'name': 'B', 'city': 'Hoylake', 'country': 'England', 'cls': 'municipal'},
    'merse-std': {'name': 'S', 'city': 'Southport', 'country': 'England', 'cls': 'standard'},
    'merse-elite': {'name': 'E', 'city': 'Southport', 'country': 'England', 'cls': 'elite'},
    'kent-std': {'name': 'K', 'city': 'Sandwich', 'country': 'England', 'cls': 'standard'},
    'fife-elite': {'name': 'F', 'city': 'St Andrews', 'country': 'Scotland', 'cls': 'elite'},
}


def _hc_season(places, golfers=(1, 2, 3)):
    return SimpleNamespace(places=places, seed=2027, lib=SimpleNamespace(sites=SITES),
                           world=SimpleNamespace(golfers=[SimpleNamespace(id=i) for i in golfers]))


class HomeClubTests(unittest.TestCase):
    def setUp(self):
        self.index = HC.club_index(SITES)

    def test_pick_prefers_a_municipal_course_in_their_state(self):
        for gid in range(40):
            cid, basis = HC.pick(self.index, 2027, gid, MERSEY)
            self.assertIn(cid, ('merse-muni-a', 'merse-muni-b'))
            self.assertEqual(basis, 'region')
        picks = {HC.pick(self.index, 2027, gid, MERSEY)[0] for gid in range(40)}
        self.assertEqual(len(picks), 2)                                # spread over the local clubs

    def test_other_non_elite_course_then_country_then_none(self):
        self.assertEqual(HC.pick(self.index, 2027, 1, ('England', 'Kent')), ('kent-std', 'region'))
        cid, basis = HC.pick(self.index, 2027, 1, SURREY)              # no course in Surrey
        self.assertEqual(basis, 'country')
        self.assertIn(cid, ('merse-muni-a', 'merse-muni-b'))           # municipal first, by country
        self.assertEqual(HC.pick(self.index, 2027, 1, ('England', None))[1], 'country')
        self.assertEqual(HC.pick(self.index, 2027, 1, ('Scotland', 'Fife')), (None, None))   # only an elite venue
        self.assertEqual(HC.pick(self.index, 2027, 1, None), (None, None))

    def test_pick_is_stable(self):
        a = [HC.pick(HC.club_index(SITES), 2027, g, MERSEY) for g in range(20)]
        b = [HC.pick(HC.club_index(dict(reversed(list(SITES.items())))), 2027, g, MERSEY) for g in range(20)]
        self.assertEqual(a, b)                                         # not order-dependent

    def test_assign_records_dated_clubs_and_moves(self):
        P = Places()
        P.arrive(1, MERSEY, MERSEY, 2027, 0)
        P.arrive(2, SURREY, SURREY, 2027, 0)
        P.legacy.add(3)
        s = _hc_season(P)
        HC.assign(s, 2027, 0)
        self.assertEqual(set(s.home_clubs), {1, 2})                    # legacy: no home club
        first = s.home_clubs[1][-1]
        self.assertEqual(first[:2] + first[3:], [2027, 0, 'region', list(MERSEY)])
        self.assertEqual(s.home_clubs[2][-1][3], 'country')
        HC.assign(s, 2027, 53)                                         # no move: nothing new
        self.assertEqual(len(s.home_clubs[1]), 1)
        P.move(1, 2028, 53, ('England', 'Kent'), 'test move')
        HC.assign(s, 2028, 53)
        self.assertEqual(s.home_clubs[1][-1][:4], [2028, 53, 'kent-std', 'region'])
        self.assertEqual(HC.current(s, 1), 'kent-std')
        P.move(1, 2031, 53, ('Scotland', 'Fife'), 'test move')        # nowhere to belong: recorded as none
        HC.assign(s, 2031, 53)
        self.assertIsNone(HC.current(s, 1))
        self.assertEqual(len(s.home_clubs[1]), 3)

    def test_home_club_floor_counted_once(self):
        P = Places()
        P.arrive(1, MERSEY, MERSEY, 2027, 0)
        P.arrive(2, SURREY, SURREY, 2027, 0)
        s = _hc_season(P, (1, 2))
        HC.assign(s, 2027, 0)
        s.lib = SimpleNamespace(sites=SITES)
        club1, club2 = HC.current(s, 1), HC.current(s, 2)
        self.assertEqual(Season.course_baseline(s, 1, club1), (FAM.REGION_ROUNDS, 'region'))   # already local
        self.assertEqual(Season.course_baseline(s, 2, club2), (FAM.REGION_ROUNDS, 'home club'))  # found by country
        other = next(c for c in ('merse-muni-a', 'merse-muni-b') if c != club2)
        self.assertEqual(Season.course_baseline(s, 2, other), (0.0, None))
        self.assertEqual(FAM.home_floor((FAM.REGION_ROUNDS, 'region'), True), (FAM.REGION_ROUNDS, 'region'))
        self.assertEqual(FAM.home_floor((FAM.COUNTRY_ROUNDS, 'country'), True), (FAM.REGION_ROUNDS, 'home club'))
        self.assertEqual(FAM.home_floor((0.0, None), False), (0.0, None))


class LocalHostingTests(unittest.TestCase):
    """Venue assignment only (no golf is simulated): the reference calendar, with and without local hosting."""
    YEARS = 10

    @classmethod
    def setUpClass(cls):
        cls.new = default_library('v2')
        cls.old = CourseLibrary(WorldCalendar(2027, 'v2'), local_first=False)
        cls.homes, cls.use = {}, {}
        for key, lib in (('new', cls.new), ('old', cls.old)):
            homes, use = {}, {}
            for y in range(lib.first_year, lib.first_year + cls.YEARS):
                vs = lib.venues(y)
                for ed in lib.calendar.editions(y):
                    for v in vs[ed.event_id]:
                        homes.setdefault((ed.series.series_id, v.city), v.course_id)   # first course used there
                        use[v.course_id] = use.get(v.course_id, 0) + 1
            cls.homes[key], cls.use[key] = homes, use

    def test_same_courses_and_venue_rules_hold(self):
        self.assertEqual(list(self.new.sites), list(self.old.sites))    # sizing untouched: same 520 courses
        self.assertEqual(self.new.validate(self.YEARS), [])            # eligibility, season, no double-booking

    def test_only_new_low_and_entry_events_change_and_onto_municipal_courses(self):
        series = {x.series_id: x for x in self.new.calendar.series}
        changed = [k for k, cid in self.homes['old'].items() if self.homes['new'].get(k) != cid]
        self.assertTrue(changed)
        self.assertLess(len(changed), 0.02 * len(self.homes['old']))
        onto_municipal = 0
        for sid, city in changed:
            self.assertIn(event_level(series[sid]), LOCAL_LEVELS)          # no higher level is ever affected
            onto_municipal += self.new.sites[self.homes['new'][(sid, city)]]['cls'] == 'municipal'
        # nearly all onto a municipal course; the rest are same-week knock-ons (a municipal course another new
        # event took that week is booked, so the next one takes the usual ranking's choice)
        self.assertGreaterEqual(onto_municipal, 0.9 * len(changed))

    def test_each_adopted_municipal_course_has_one_adopting_series_per_city(self):
        adopters = {}
        for (sid, city), cid in self.homes['new'].items():
            if self.new.sites[cid]['cls'] == 'municipal' and self.homes['old'].get((sid, city)) != cid:
                adopters.setdefault(cid, []).append(sid)
        self.assertTrue(all(len(v) == 1 for v in adopters.values()), adopters)

    def test_named_courses_now_host(self):
        named = {s['name']: cid for cid, s in self.new.sites.items()}
        for name in ('Southport Brook Public Golf Course', 'Wren Dunes Golf Club', 'Fjordby Helsinki Golfklub'):
            cid = named[name]
            self.assertFalse(self.use['old'].get(cid))
            self.assertTrue(self.use['new'].get(cid), name)

    def test_reproducible(self):
        again = CourseLibrary(WorldCalendar(2027, 'v2'))
        for y in range(again.first_year, again.first_year + 3):
            self.assertEqual(again.venues(y), self.new.venues(y))


class RuleTextTests(unittest.TestCase):
    def test_rule_and_version(self):
        from golfsim import rules
        self.assertIn('2026-11-08', [v for v, _ in rules.VERSIONS])   # (later versions may follow it)
        self.assertGreaterEqual(rules.RULES_VERSION, '2026-11-08')
        self.assertEqual(rules.VERSIONS[-1][0], rules.RULES_VERSION)
        title, text, since = rules.RULES['course-familiarity']
        self.assertEqual(since, '2026-11-08')
        for fact in ('1 - exp(-rounds / 15)', 'at least 3 rounds', 'at least 1.5', 'never their sum', 'count once',
                     'Home club', 'changed only when they move', 'never on top of another baseline'):
            self.assertIn(fact, text)
        title, text, since = rules.RULES['local-hosting']
        self.assertEqual(since, '2026-11-08')
        for fact in ('for the first time', 'no event has used yet', 'Established home courses never change',
                     'no event is rotated'):
            self.assertIn(fact, text)
        self.assertEqual((FAM.SCALE, FAM.REGION_ROUNDS, FAM.COUNTRY_ROUNDS), (15.0, 3.0, 1.5))   # as the text says


class CoursePageTests(unittest.TestCase):
    def test_course_page_section(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
        import observer_history as OH

        class W:
            live, a = None, None

            def courses(self):
                return dict(VenueRoleTests.COURSES, odd=_course('Odd', 'Nowhere Town', 'standard', ('Club',)))
        html = OH.course_place_section(W(), 'muni', W().courses()['muni'], 0)
        self.assertIn('State / province: Merseyside', html)
        self.assertIn('local club', html)
        self.assertIn('Carrick Fields Links', html)
        html = OH.course_place_section(W(), 'std', W().courses()['std'], 5)
        self.assertIn('event venue', html)
        self.assertNotIn('No event has been played here', html)
        html = OH.course_place_section(W(), 'odd', W().courses()['odd'], 0)
        self.assertIn('unknown', html)


if __name__ == '__main__':
    unittest.main()
