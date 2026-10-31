"""Geography, familiarity and course use (roadmap G1): every course's state / province normalised from its
city (unknown, never guessed, when the geography lacks the city), how each course came to be built, why a
course hosts no events (a local club, explained by the venue policy, never forced into a rotation), and the
regional familiarity baseline (rules 2026-11-08): bounded, a floor never a sum, counted once for identical
birthplace and residence, honest about unknown places, deterministic.

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
from golfsim.course_library import course_place, default_library, venue_role    # noqa: E402
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
        self.assertEqual(venue_role(self.COURSES, 'muni', 3), ('event venue', ''))

    def test_unused_municipal_behind_a_standard_course(self):
        role, why = venue_role(self.COURSES, 'muni', 0)
        self.assertEqual(role, 'local club')
        self.assertIn('Carrick Fields Links', why)
        self.assertIn('low-level', why)
        self.assertIn('entry-level', why)
        self.assertNotIn('Royal Holly Rock', why)          # an elite course is no competitor at these levels

    def test_unused_course_that_ranks_first(self):
        role, why = venue_role(self.COURSES, 'lone', 0)
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


class RuleTextTests(unittest.TestCase):
    def test_rule_and_version(self):
        from golfsim import rules
        self.assertEqual(rules.RULES_VERSION, '2026-11-08')
        self.assertEqual(rules.VERSIONS[-1][0], rules.RULES_VERSION)
        title, text, since = rules.RULES['course-familiarity']
        self.assertEqual(since, '2026-11-08')
        for fact in ('1 - exp(-rounds / 15)', 'at least 3 rounds', 'at least 1.5', 'never their sum', 'count once'):
            self.assertIn(fact, text)
        self.assertEqual((FAM.SCALE, FAM.REGION_ROUNDS, FAM.COUNTRY_ROUNDS), (15.0, 3.0, 1.5))   # as the text says


class CoursePageTests(unittest.TestCase):
    def test_course_page_section(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
        import observer_history as OH

        class W:
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
