"""Death after retirement (roadmap C2, owner decision D6, rules 2026-11-07): who can die, when, how it is recorded,
and that it is reproducible and processed once. Synthetic people only (no world, no season played): quick.

Run from the project folder:  python -m unittest tests.test_mortality -v
(The small-world checks are in tests/test_mortality_world.py.)
"""
from __future__ import annotations

import copy
import random
import sys
import unittest
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import mortality as M                                    # noqa: E402
from golfsim import rules as R                                        # noqa: E402
from golfsim import staff as ST                                       # noqa: E402
from golfsim.archive import ArchiveWriter, season_deaths              # noqa: E402
from golfsim.golfer import CADDIE_SKILLS, uniform_golfer              # noqa: E402

YEAR = 2027


class FakeSeason:
    """Just what the winter's mortality reads and writes: the world's golfers, the staff, the seed and the log."""

    def __init__(self, golfers, staff, seed=7):
        self.world = SimpleNamespace(golfers=golfers)
        self.g = {g.id: g for g in golfers}
        self.staff = staff
        self.seed = seed
        self.mortality_on = True
        self.deaths = {}
        self.mortality_done = set()
        self.history = defaultdict(list)

    def log(self, gid, year, week, text):
        self.history[gid].append((year, week, text))

    def player_prestige(self, gid):
        return 0.0


def golfer(pid, born, lifestyle='full_time', status='pro'):
    g = uniform_golfer(60, name=f'Golfer {pid}')
    g.id, g.born, g.country, g.lifestyle, g.status = pid, born, 'USA', lifestyle, status
    g.tour = '' if lifestyle == 'retired' else 'MINI_US'
    return g


def coach(st, pid, born, former=0):
    return st.new_coach(random.Random(pid), 'USA', YEAR, YEAR - born, 50, 50, 'putting', False, 50, 'test',
                        former=former, name=f'Coach {pid}', pid=pid)


def caddie(st, pid, born, former=0):
    return st.new_caddie(random.Random(pid), 'USA', YEAR, YEAR - born, {s: 50 for s in CADDIE_SKILLS}, 50, 'test',
                         former=former, name=f'Caddie {pid}', pid=pid)


def population(n=3000, seed=11):
    """Active golfers of every age (some impossibly old, to test the rule rather than the curve), retired golfers,
    retired golfers who coach or caddie, and staff who never played."""
    rng = random.Random(seed)
    st = ST.Staff(seed=0)
    golfers = []
    for pid in range(1, n + 1):
        born = YEAR - rng.randint(15, 110)
        kind = rng.random()
        if kind < 0.5:
            golfers.append(golfer(pid, born, rng.choice(('full_time', 'part_time')),
                                  rng.choice(('pro', 'amateur', 'club_pro'))))
        elif kind < 0.75:
            golfers.append(golfer(pid, born, 'retired'))
        elif kind < 0.85:
            golfers.append(golfer(pid, born, 'retired'))
            (coach if rng.random() < 0.5 else caddie)(st, pid, born, former=pid)
        else:
            (coach if rng.random() < 0.5 else caddie)(st, pid, born)
    return FakeSeason(golfers, st)


def first_death_winter(seed, pid, born, start=YEAR, stop=YEAR + 80):
    """The first winter in which this person's own draw falls under the risk at their age."""
    return next(y for y in range(start, stop) if M.draw(seed, y, pid) < M.annual_risk(y - born))


class Curve(unittest.TestCase):
    def test_values(self):
        for age, q in ((60, 0.0096), (70, 0.0228), (80, 0.0554), (90, 0.1356), (100, 0.3327)):
            self.assertAlmostEqual(M.annual_risk(age), q, places=4)
        self.assertAlmostEqual(M.annual_risk(0), 0.0005 + 0.000041, places=9)
        self.assertEqual(M.annual_risk(110), 0.5)                    # capped at 50 % a year
        self.assertEqual(M.annual_risk(150), 0.5)
        ages = range(0, 130)
        self.assertTrue(all(M.annual_risk(a) <= M.annual_risk(a + 1) for a in ages))   # never falls with age

    def test_the_draw_is_uniform_and_its_own(self):
        xs = [M.draw(3, YEAR, pid) for pid in range(20000)]
        self.assertTrue(all(0.0 <= x < 1.0 for x in xs))
        self.assertAlmostEqual(sum(xs) / len(xs), 0.5, delta=0.01)
        random.seed(1)
        a = M.draw(3, YEAR, 42)
        random.seed(2)
        random.random()
        self.assertEqual(M.draw(3, YEAR, 42), a)                     # no shared random stream
        self.assertNotEqual(M.draw(3, YEAR, 42), M.draw(3, YEAR + 1, 42))
        self.assertNotEqual(M.draw(3, YEAR, 42), M.draw(4, YEAR, 42))

    def test_rules_text(self):
        self.assertIn('2026-11-07', [v for v, _ in R.VERSIONS])        # (later versions may follow it)
        self.assertGreaterEqual(R.RULES_VERSION, '2026-11-07')
        self.assertEqual(R.VERSIONS[-1][0], R.RULES_VERSION)
        title, text, since = R.RULES['mortality']
        self.assertEqual(since, '2026-11-07')
        for fact in ('never dies', 'winter after season Y', '0.0005 + 0.000041 x e^(0.09 a)', '50 %',
                     'provisional game calibration', 'every nation', 'never processed twice', '"coach died"'):
            self.assertIn(fact, text)


class WhoCanDie(unittest.TestCase):
    def test_active_competitive_golfers_never_die(self):
        s = population()
        active = {g.id for g in s.world.golfers if g.lifestyle != 'retired'}
        self.assertTrue(any(YEAR - s.g[g].born >= 100 for g in active))   # risk at its cap, still never
        for y in range(YEAR, YEAR + 40):
            M.winter(s, y)
        self.assertFalse(active & set(s.deaths))
        self.assertTrue(s.deaths)                                    # (everyone else could, and some did)
        roles = {r for d in s.deaths.values() for r in d['roles']}
        self.assertEqual(roles, {'golfer', 'coach', 'caddie'})       # retired golfers, staff, former golfers on staff
        never_played = {c.id for c in list(s.staff.coaches.values()) + list(s.staff.caddies.values())
                        if c.id not in s.g}
        self.assertTrue(never_played & set(s.deaths))

    def test_retired_people_die_at_about_the_curve(self):
        s = population(n=20000, seed=5)
        at_risk = [(pid, rec) for pid, rec in M.people(s).items() if M.eligible(rec)]
        expected = sum(M.annual_risk(YEAR - rec['born']) for _, rec in at_risk)
        died = M.winter(s, YEAR)
        self.assertAlmostEqual(len(died), expected, delta=4 * expected ** 0.5)

    def test_unknown_birth_year_never_dies(self):
        st = ST.Staff(seed=0)
        s = FakeSeason([golfer(1, 0, 'retired')], st)
        for y in range(YEAR, YEAR + 50):
            M.winter(s, y)
        self.assertEqual(s.deaths, {})

    def test_a_world_from_before_the_rule_never_processes_deaths(self):
        s = population()
        s.mortality_on = False
        for y in range(YEAR, YEAR + 20):
            self.assertEqual(M.winter(s, y), [])
        self.assertEqual((s.deaths, s.mortality_done), ({}, set()))


class WorkingStaff(unittest.TestCase):
    def setUp(self):
        self.st = st = ST.Staff(seed=0)
        born = YEAR - 95                                             # a retired golfer, now coaching and caddying
        self.y = first_death_winter(7, 500, born)
        self.person = golfer(500, born, 'retired')
        self.clients = [golfer(501, YEAR - 25), golfer(502, YEAR - 30)]
        self.bag = golfer(503, YEAR - 28)
        self.c = coach(st, 500, born, former=500)
        self.k = caddie(st, 500, born, former=500)                   # (one person, two staff records)
        self.s = FakeSeason([self.person] + self.clients + [self.bag], st)
        for g in self.clients:
            st.assign_coach(self.s, g, self.c, 'fee', (self.y, 1), 'golfer', 'test')
        st.assign_caddie(self.s, self.bag, self.k, (self.y, 1))

    def test_partnerships_end_with_the_reason_at_the_winter(self):
        for y in range(YEAR, self.y + 1):
            M.winter(self.s, y)
        d = self.s.deaths[500]
        self.assertEqual((d['year'], d['week'], d['age']), (self.y, 53, self.y - self.person.born))
        ended = [x for x in self.st.rel.stints if x.staff == 500]
        self.assertEqual(len(ended), 3)
        for x in ended:
            self.assertEqual(x.end, (self.y, 53))
            self.assertEqual(x.ended_by, 'death')
            self.assertIn('died', x.reason_end)
        self.assertFalse(500 in self.st.coach_of.values() or 500 in self.st.caddie_of.values())
        self.assertEqual((self.c.status, self.k.status), ('deceased', 'deceased'))   # they stop working
        for g in self.clients + [self.bag]:                          # each golfer's log says why it ended
            self.assertTrue(any('died' in t and (y, w) == (self.y, 53) for y, w, t in self.s.history[g.id]))

    def test_one_person_dies_once_in_every_record(self):
        for y in range(YEAR, self.y + 30):
            M.winter(self.s, y)
        self.assertEqual(list(self.s.deaths), [500])
        self.assertEqual(self.s.deaths[500]['roles'], ['golfer', 'coach', 'caddie'])
        text = M.death_text(self.y, self.y - self.person.born)
        self.assertEqual(text, f'Died in the winter after season {self.y}, aged {self.y - self.person.born}')
        self.assertEqual([t for _, _, t in self.s.history[500]].count(text), 1)
        for rec in (self.c, self.k):
            self.assertEqual([t for _, t in rec.history].count(text), 1)
            self.assertEqual(rec.history[-1], (self.y, text))
        self.assertEqual(self.person.lifestyle, 'retired')          # nothing deleted, nothing rewritten
        self.assertEqual(self.person.born, YEAR - 95)

    def test_no_death_dated_before_recorded_work_or_play(self):
        s = population(n=4000, seed=3)
        rng = random.Random(1)
        working = [c for c in s.staff.coaches.values()]
        actives = [g for g in s.world.golfers if g.lifestyle != 'retired']
        for y in range(YEAR, YEAR + 30):
            for c in working:                                        # a season's work starts in week 1
                if c.status == 'active' and rng.random() < 0.3:
                    g = rng.choice(actives)
                    if g.id not in s.staff.coach_of:
                        s.staff.assign_coach(s, g, c, 'fee', (y, 1), 'golfer', 'test')
            M.winter(s, y)
        self.assertTrue(s.deaths)
        for pid, d in s.deaths.items():
            self.assertEqual(d['week'], 53)                          # never a week inside the season
            for x in s.staff.rel.stints:
                if pid in (x.staff, x.golfer):
                    self.assertLessEqual(x.start, (d['year'], 53))
                    self.assertIsNotNone(x.end)
                    self.assertLessEqual(x.end, (d['year'], 53))
        self.assertFalse(set(s.staff.coach_of.values()) & set(s.deaths))


class Reproducible(unittest.TestCase):
    def test_processing_a_winter_twice_never_kills_twice(self):
        once = population()
        twice = copy.deepcopy(once)
        for y in range(YEAR, YEAR + 15):
            M.winter(once, y)
            M.winter(twice, y)
            self.assertEqual(M.winter(twice, y), [])
        self.assertEqual(once.deaths, twice.deaths)
        self.assertEqual(once.mortality_done, twice.mortality_done)
        self.assertEqual([(x.staff, x.golfer, x.end, x.reason_end) for x in once.staff.rel.stints],
                         [(x.staff, x.golfer, x.end, x.reason_end) for x in twice.staff.rel.stints])
        self.assertEqual(dict(once.history), dict(twice.history))

    def test_deterministic_per_seed_year_and_person(self):
        a = population()
        b = copy.deepcopy(a)
        random.Random(9).shuffle(b.world.golfers)                    # the order people are visited never matters
        for y in range(YEAR, YEAR + 15):
            M.winter(a, y)
            random.random()                                          # nor any other random draw
            M.winter(b, y)
        self.assertEqual(a.deaths, b.deaths)
        for pid, d in a.deaths.items():                              # each one is that person's own draw that winter
            self.assertLess(M.draw(a.seed, d['year'], pid), M.annual_risk(d['age']))
        c = copy.deepcopy(population())
        c.seed = 8
        for y in range(YEAR, YEAR + 15):
            M.winter(c, y)
        self.assertNotEqual(set(a.deaths), set(c.deaths))            # another world, other deaths

    def test_a_saved_and_resumed_world_dies_the_same(self):
        a = population()
        for y in range(YEAR, YEAR + 12):
            M.winter(a, y)
        b = population()
        for y in range(YEAR, YEAR + 5):
            M.winter(b, y)
        import pickle
        b = pickle.loads(pickle.dumps(b))                            # (a save and resume between winters)
        for y in range(YEAR + 5, YEAR + 12):
            M.winter(b, y)
        self.assertEqual(a.deaths, b.deaths)


class Observer(unittest.TestCase):
    def test_frozen_age_and_the_recorded_fact(self):
        import observer as O
        import observer_data as OD
        p = {'name': 'X', 'born': 1950, 'died': {'year': 2031, 'week': 53, 'age': 81}}
        self.assertEqual(OD.death_text(OD.died(p)), 'Died in the winter after season 2031, aged 81')
        self.assertEqual(OD.age_at(p, 2020), 70)
        self.assertEqual(OD.age_at(p, 2031), 81)
        self.assertEqual(OD.age_at(p, 2060), 81)                     # frozen
        self.assertEqual(OD.age_at({'born': 1950}, 2060), 110)
        self.assertIsNone(OD.age_at({'born': 0}, 2060))
        w = SimpleNamespace(live=SimpleNamespace(cursor={'year': 2060}), a=None)
        self.assertEqual(O.age_text(w, 1950, None, p['died']), '81*')
        self.assertEqual(O.age_text(w, 1950, 2020, p['died']), '70*')
        self.assertEqual(O.age_text(w, 1950), '110*')
        self.assertIn('deceased', O.status_cell(p, 'retired'))
        self.assertEqual(O.status_cell(p, 'deceased'), 'deceased')   # (a staff record already says so)
        self.assertEqual(O.status_cell({'born': 1950}, 'retired'), 'retired')


class Archive(unittest.TestCase):
    def test_season_files_and_the_people_table_record_deaths(self):
        s = population(n=1500)
        s.places = None
        s.records = SimpleNamespace(to_dict=lambda: {})
        for y in range(YEAR, YEAR + 20):
            M.winter(s, y)
        self.assertTrue(s.deaths)
        rows = [r for y in range(YEAR, YEAR + 20) for r in season_deaths(s, y)]
        self.assertEqual(sorted(r['person'] for r in rows), sorted(s.deaths))   # each once, in its own season
        for r in rows:
            self.assertEqual({k: r[k] for k in ('year', 'week', 'age', 'roles')}, s.deaths[r['person']])
        self.assertEqual(season_deaths(s, YEAR + 30), [])
        w = ArchiveWriter.__new__(ArchiveWriter)                     # (the tables only: nothing is written)
        w.created, w.initial = {}, set()
        people = w.state_tables(s)['people.json.gz']
        for pid, d in s.deaths.items():
            self.assertEqual(people[pid]['died'], {'year': d['year'], 'week': 53, 'age': d['age']})
        self.assertFalse(any('died' in p for pid, p in people.items() if pid not in s.deaths))


if __name__ == '__main__':
    unittest.main()
