"""World course library, venue assignment and per-layout records.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import random
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim.calendar import MAJOR_VENUES, MAJOR_WEEKS                                  # noqa: E402
from golfsim.course_gen import REAL_NAME_BLOCKLIST, _blocked                             # noqa: E402
from golfsim.course_library import CourseLibrary, default_library, event_level, rate_layout   # noqa: E402
from golfsim.geography import CITY_BY_NAME                                               # noqa: E402
from golfsim.golfer import uniform_golfer                                                # noqa: E402
from golfsim.records import RecordBook                                                   # noqa: E402
from golfsim.tournament import play_event                                                # noqa: E402

LIB = default_library()


class LibraryTests(unittest.TestCase):
    def test_380_courses_and_venue_checks(self):
        self.assertEqual(len(LIB.sites), 380)
        self.assertEqual(LIB.validate(10), [])

    def test_deterministic(self):
        other = CourseLibrary()
        self.assertEqual(list(other.sites), list(LIB.sites))
        a = LIB.course(next(iter(LIB.sites)) + ':Championship')
        b = other.course(next(iter(other.sites)) + ':Championship')
        self.assertEqual(a.holes, b.holes)

    def test_elite_one_layout_premier_only(self):
        elite = [s for s in LIB.sites.values() if s['cls'] == 'elite']
        self.assertTrue(28 <= len(elite) <= 40)
        for s in elite:
            self.assertEqual(list(s['layouts']), ['Championship'])
        for year in range(2027, 2037):
            for eid, vs in LIB.venues(year).items():
                s = LIB.calendar.by_id[eid.split(':', 1)[1]]
                for v in vs:
                    if LIB.sites[v.course_id]['cls'] == 'elite':
                        self.assertLessEqual(s.tier, 1, eid)

    def test_majors_at_their_venues(self):
        for year in range(2027, 2037):
            vs = LIB.venues(year)
            self.assertEqual(vs[f'{year}:TOUR_MASTERS'][0].course_id, 'georgia-national-golf-club')
            for sid in ('PREMIER_TOUR_CHAMPIONSHIP', 'USA_OPEN', 'BRITANNIA_OPEN'):
                v = vs[f'{year}:{sid}'][0]
                self.assertIn(v.city, MAJOR_VENUES[sid][1])
                self.assertEqual(LIB.sites[v.course_id]['cls'], 'elite')
            self.assertEqual(LIB.sites[vs[f'{year}:BRITANNIA_OPEN'][0].course_id]['style'], 'Links')

    def test_mid_courses_have_easier_layouts_used_by_lower_levels(self):
        std = [s for s in LIB.sites.values() if s['cls'] == 'standard']
        self.assertTrue(all('Club' in s['layouts'] for s in std))
        self.assertGreater(sum('Forward' in s['layouts'] for s in std), len(std) * 0.3)
        used = Counter()
        for year in range(2027, 2030):
            for eid, vs in LIB.venues(year).items():
                s = LIB.calendar.by_id[eid.split(':', 1)[1]]
                for v in vs:
                    used[(s.tier, v.layout)] += 1
        self.assertGreater(used[(6, 'Forward')], 50)          # amateurs use forward tees
        self.assertGreater(used[(4, 'Club')], 50)             # mini tours use club tees
        self.assertEqual(sum(n for (t, lay), n in used.items() if t <= 2 and lay != 'Championship'), 0)

    def test_easier_layouts_are_easier(self):
        rng = random.Random(3)
        sites = [s for s in LIB.sites.values() if 'Forward' in s['layouts'] and s['cls'] == 'standard']
        for s in rng.sample(sites, 3):
            champ, club, fwd = (s['layouts'][k] for k in ('Championship', 'Club', 'Forward'))
            self.assertEqual(champ.holes[0].par, fwd.holes[0].par)
            self.assertGreater(champ.yards, club.yards)
            self.assertGreater(club.yards, fwd.yards)
            r = [rate_layout(c, rounds=40)['amateur'] for c in (champ, club, fwd)]
            self.assertGreater(r[0], r[1])
            self.assertGreater(r[1], r[2])

    def test_difficulty_by_class(self):
        """Pros struggle on elite courses and destroy municipal ones; amateurs are punished far more."""
        rng = random.Random(5)
        def avg(cls, layout, level):
            ss = [s for s in LIB.sites.values() if s['cls'] == cls and layout in s['layouts']]
            return sum(rate_layout(s['layouts'][layout], rounds=30)[level] - s['layouts'][layout].par
                       for s in rng.sample(ss, 4)) / 4
        elite_pro, muni_pro = avg('elite', 'Championship', 'tour'), avg('municipal', 'Regular', 'tour')
        elite_am, muni_am = avg('elite', 'Championship', 'amateur'), avg('municipal', 'Regular', 'amateur')
        self.assertGreater(elite_pro, 0.5)
        self.assertLess(muni_pro, -3.5)
        self.assertGreater(elite_am - muni_am, (elite_pro - muni_pro) + 3)

    def test_courses_in_real_cities_with_fictional_names(self):
        names = [s['name'] for s in LIB.sites.values()]
        self.assertEqual(len(names), len(set(names)))
        for s in LIB.sites.values():
            self.assertIn(s['city'], CITY_BY_NAME)
            self.assertEqual(CITY_BY_NAME[s['city']].country, s['country'])
            if not s.get('hand_built'):
                self.assertFalse(_blocked(s['name']), s['name'])
        self.assertIn('pine valley', REAL_NAME_BLOCKLIST)

    def test_no_course_double_booked(self):
        for year in (2027, 2033):
            per_week = Counter()
            for eid, vs in LIB.venues(year).items():
                week = LIB.calendar.by_id[eid.split(':', 1)[1]].week
                for v in vs:
                    per_week[(week, v.course_id)] += 1
            self.assertEqual(max(per_week.values()), 1)
            self.assertEqual(sum(1 for (w, _) in per_week if w in MAJOR_WEEKS), 4)

    def test_event_levels(self):
        by = LIB.calendar.by_id
        self.assertEqual(event_level(by['USA_OPEN']), 'major')
        self.assertEqual(event_level(by['PT_PREMIER_PLAYERS_CHAMPIONSHIP']), 'flagship')
        self.assertEqual(event_level(by['USA_OPEN_FINAL']), 'top')


class RecordTests(unittest.TestCase):
    def test_records_kept_per_layout(self):
        site = next(s for s in LIB.sites.values() if s['cls'] == 'standard' and 'Forward' in s['layouts'])
        book = RecordBook()
        rng = random.Random(11)
        field = [uniform_golfer(r, name=f'P{r}') for r in (40, 50, 60, 70, 80)]
        boards = {}
        for key in ('Championship', 'Forward'):
            course = site['layouts'][key]
            boards[key], _ = board, _ = play_event(field, course, rng, cut_top=99, rounds_n=2, cut_after=None,
                                  on_round=book.round_recorder(course, f'2027:TEST_{key}', 2027, 10, 4))
            book.add_event(course, board, 36, f'2027:TEST_{key}', 2027, 10, 4)
        champ = book.layouts[site['layouts']['Championship'].layout_id]
        fwd = book.layouts[site['layouts']['Forward'].layout_id]
        self.assertEqual(champ.rounds, 10)
        self.assertEqual(fwd.rounds, 10)
        self.assertNotEqual(champ.layout_id, fwd.layout_id)
        self.assertEqual(champ.course_record.score, min(m.score for _, m in champ.history))
        self.assertEqual(champ.lowest_totals[36].score, min(t for _, t, _ in boards['Championship']))
        self.assertLess(fwd.scoring_average, champ.scoring_average)
        self.assertTrue(all(b is not None for b in champ.hole_best))
        self.assertIn(champ.layout_id, book.to_dict())

    def test_record_setting_order(self):
        from golfsim.records import LayoutRecords, Mark
        r = LayoutRecords('x:Championship', 72)
        for i, s in enumerate((74, 70, 70, 71, 66)):
            r.add_round(Mark(s, s - 72, f'G{i}', 'e', 2027, 1, 1, 2))
        self.assertEqual(r.course_record.score, 66)
        self.assertEqual([k for k, _ in r.history], ['set', 'set', 'equalled', 'set'])
        self.assertEqual(r.course_record.golfer, 'G4')
        self.assertEqual(r.highest_round.score, 74)


if __name__ == '__main__':
    unittest.main()
