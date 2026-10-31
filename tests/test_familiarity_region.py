"""Geography of courses and course use (roadmap G1): every course's state / province normalised from its
city (unknown, never guessed, when the geography lacks the city), how each course came to be built, and
why a course hosts no events (a local club, explained by the venue policy, never forced into a rotation).

Quick unit tests only: no season is simulated and no world is generated.
Run from the project folder:  python -m unittest tests.test_familiarity_region -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim.course import ashford_ridge                                        # noqa: E402
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
