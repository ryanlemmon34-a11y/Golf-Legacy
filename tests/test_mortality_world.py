"""Death after retirement in a small running world (rules 2026-11-07): deaths happen only in the winter, never to an
active competitive golfer, never before recorded work or play; a dying coach's or caddie's partnerships end with the
reason; the season files and the people table record them; the observer shows the recorded fact with the age frozen,
marks and filters deceased people, also from the archive alone; and a world saved and resumed dies the same.

The risk is raised for this test (at least 6 % a year at every age) so a three-season world of young people has
deaths to check; the rule's own curve is checked in tests/test_mortality.py.

Run from the project folder:  python -m unittest tests.test_mortality_world -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import mortality as M                                    # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer as O                                                  # noqa: E402

SEED, SCALE, SEASONS = 31, 0.05, 3
REAL = M.annual_risk


def raised(age):
    return max(0.06, REAL(age))


def run(directory, split=None):
    """A world advanced SEASONS seasons and one week; with `split`, closed and reopened after that many weeks."""
    weeks = SEASONS * 52 + 1
    with mock.patch.object(M, 'annual_risk', raised):
        s = Session.create(directory, seed=SEED, workers=1, world=generate_world(seed=SEED, scale=SCALE))
        if split:
            s.advance(split)
            s.close()
            s = Session.open(directory, workers=1)
            s.advance(weeks - split)
        else:
            s.advance(weeks)
    return s


class SmallWorld(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.s = run(cls.tmp / 'w')
        cls.season = cls.s.season
        cls.first = cls.season.first_year
        cls.deaths = dict(cls.season.deaths)
        cls.s.close()
        cls.w = O.World(cls.tmp / 'w', workers=1)
        cls.w.reload()

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_deaths_only_in_the_winter_and_never_an_active_golfer(self):
        self.assertTrue(self.deaths)
        s = self.season
        self.assertEqual(s.mortality_done, set(range(self.first, self.first + SEASONS)))
        roles = set()
        for pid, d in self.deaths.items():
            self.assertEqual(d['week'], 53)
            self.assertIn(d['year'], range(self.first, self.first + SEASONS))
            g = s.g.get(pid)
            self.assertTrue(g is None or g.lifestyle == 'retired')
            born = g.born if g is not None else (s.staff.coaches.get(pid) or s.staff.caddies.get(pid)).born
            self.assertEqual(d['age'], d['year'] - born)
            roles.update(d['roles'])
        self.assertTrue(roles & {'coach', 'caddie'})               # (working or retired staff among them)

    def test_dead_staff_stop_working_and_their_partnerships_end_with_the_reason(self):
        st = self.season.staff
        dead = set(self.deaths)
        for table in (st.coaches, st.caddies):
            for p in table.values():
                self.assertEqual(p.status == 'deceased', p.id in dead)
        self.assertFalse(dead & (set(st.coach_of.values()) | set(st.caddie_of.values())))
        by_death = [x for x in st.rel.stints if x.ended_by == 'death']
        for x in by_death:
            self.assertEqual(x.end, (self.deaths[x.staff]['year'], 53))
            self.assertEqual(x.reason_end, f'{x.kind} died')
        for x in st.rel.stints:                                    # never dated before recorded work or play
            for pid in (x.staff, x.golfer):
                if pid in dead:
                    when = (self.deaths[pid]['year'], 53)
                    self.assertLessEqual(x.start, when)
                    self.assertIsNotNone(x.end)
                    self.assertLessEqual(x.end, when)

    def test_no_result_or_team_after_a_death(self):
        dead = self.deaths
        for y in self.w.a.years:
            for e in self.w.a.year(y)['events']:
                for site in e['finish']:
                    for gid, _, _ in site:
                        self.assertFalse(gid in dead and dead[gid]['year'] < y)
                for team in e['team'].values():
                    for pid in team:
                        self.assertFalse(pid in dead and dead[pid]['year'] < y)

    def test_season_files_and_people_table(self):
        a = self.w.a
        for y in a.years:
            got = {r['person']: r for r in a.year(y).get('deaths', [])}
            want = {pid: d for pid, d in self.deaths.items() if d['year'] == y}
            self.assertEqual(set(got), set(want))
            for pid, d in want.items():
                self.assertEqual((got[pid]['age'], got[pid]['week'], got[pid]['roles']), (d['age'], 53, d['roles']))
        for pid, d in self.deaths.items():
            if d['year'] in a.years and pid in a.people:
                self.assertEqual(a.died(pid), {'year': d['year'], 'week': 53, 'age': d['age']})

    def test_profile_directory_and_filters(self):
        pid, d = min(self.deaths.items())
        html = O.render(self.w, f'/golfer/{pid}', {})[1]
        self.assertIn(f'Died in the winter after season {d["year"]}, aged {d["age"]}', html)
        self.assertNotIn('<p class="lead">Age ', html)
        role = d['roles'][0]
        path = {'golfer': '/golfers', 'coach': '/coaches', 'caddie': '/caddies'}[role]
        dead_list = O.render(self.w, path, parse_qs('alive=deceased&q=' + self.w.person(pid)['name'].split()[0]))[1]
        self.assertIn(f'/golfer/{pid}"', dead_list)
        living = O.render(self.w, path, parse_qs('alive=living&q=' + self.w.person(pid)['name'].split()[0]))[1]
        self.assertNotIn(f'/golfer/{pid}"', living)
        for tab in ('playing', 'results', 'team', 'coaching', 'caddying'):   # every page of theirs still works
            O.render(self.w, f'/golfer/{pid}', parse_qs(f'tab={tab}'))

    def test_archive_only_browsing_shows_deaths(self):
        archived = {pid: d for pid, d in self.deaths.items() if d['year'] in self.w.a.years}
        if not archived:
            self.skipTest('no death in a published season')
        w = O.World(self.tmp / 'w', workers=1, read_only=True)
        try:
            w.reload()
            pid, d = min(archived.items())
            html = O.render(w, f'/golfer/{pid}', {})[1]
            self.assertIn(f'Died in the winter after season {d["year"]}, aged {d["age"]}', html)
        finally:
            w.close()

    def test_saved_and_resumed_the_same(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            s = run(tmp / 'w', split=52 + 20)
            self.assertEqual(s.season.deaths, self.deaths)
            s.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
