"""Birthplace and residence (docs/RESIDENCE.md): nationality fixed, birthplace fixed, residence moves by
recorded, dated moves; college moves are free; residence drives travel costs and proximity, never
entry rights; one geography per person across playing and staff careers; legacy people stay unknown.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import copy
import pickle
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import finance as FIN                                    # noqa: E402
from golfsim import residence as RES                                  # noqa: E402
from golfsim.archive import Archive, ArchiveWriter                    # noqa: E402
from golfsim.calendar import TOUR_BY_KEY                              # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.season import Season                                     # noqa: E402


def sa_tour():
    """A tour whose events are in South Africa (the setting for a West African professional's move)."""
    return next(k for k, t in TOUR_BY_KEY.items() if t.tier in (3, 4) and t.countries and t.countries[0][0] == 'South Africa')


class ResidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = s = Season(generate_world(seed=11, scale=0.2), seed=11, development=True, workers=4)
        cls.start = {g.id: (g.country, s.places.birth.get(g.id)) for g in s.world.golfers}
        s.start_year(2027)
        for w in range(1, 53):
            s.advance_week(2027, w)
        s.finish_year(2027)

    @classmethod
    def tearDownClass(cls):
        cls.s.close()

    def test_nationality_and_birthplace_never_change(self):
        s = self.s
        for gid, (country, birth) in self.start.items():
            self.assertEqual(s.g[gid].country, country)
            self.assertEqual(s.places.birth.get(gid), birth)
        moved = [m['person'] for m in s.move_log.get(2027, []) if m['person'] in self.start]
        self.assertTrue(moved)                                               # people did move
        for gid in moved:
            self.assertEqual(s.g[gid].country, self.start[gid][0])           # nationality untouched

    def test_college_golfers_live_at_a_college_base(self):
        s = self.s
        college = [g for g in s.active_golfers() if g.tour.startswith('CO_US')]
        self.assertTrue(all(s.places.home[g.id][0] == 'USA' for g in college))
        self.assertGreater(len({s.places.home[g.id][1] for g in college}), 10)   # not all in one state
        foreign = [g for g in college if g.country != 'USA']
        self.assertTrue(foreign)
        for g in foreign:
            self.assertNotEqual(g.country, 'USA')
            self.assertEqual(s.places.college[g.id][1], s.places.home[g.id])
        new = [g for g in college if s.places.first[g.id][0] == 2027 and s.places.first[g.id][1] == 53]
        self.assertTrue(new)                                                 # this winter's arrivals too
        self.assertTrue(all('college' in s.places.first[g.id][3] for g in new))

    def test_a_college_move_is_free_even_deep_in_debt(self):
        s = copy.deepcopy(self.s)
        g = next(g for g in s.active_golfers() if g.country != 'USA' and g.status == 'amateur'
                 and not g.tour.startswith('CO_') and g.lifestyle == 'full_time')
        g.cash, g.backing, g.backer_funds = -250000.0, 0.0, 0.0              # far beyond any credit
        before = s.places.home[g.id]
        led = copy.deepcopy(s.ledgers[2027].get(g.id))
        g.tour = 'CO_US_D1'                                                  # a place at a US college
        RES.settle(s, 2027, 53)
        self.assertEqual(s.places.home[g.id][0], 'USA')
        self.assertNotEqual(s.places.home[g.id], before)
        self.assertEqual(g.cash, -250000.0)                                  # nothing charged
        after = s.ledgers[2027].get(g.id)
        self.assertEqual(getattr(after, 'moving', 0.0), getattr(led, 'moving', 0.0) if led else 0.0)
        y, w, frm, to, why = s.places.moves[g.id][-1]
        self.assertEqual((frm, to), (before, s.places.home[g.id]))
        self.assertIn('paid by the school', why)
        g.tour = 'CO_US_SMALL'                                               # a transfer: still free
        RES.settle(s, 2027, 53)
        self.assertEqual(s.places.college[g.id][0], 'CO_US_SMALL')
        self.assertEqual(g.cash, -250000.0)

    def test_residence_sets_costs_but_not_entry_rights(self):
        s = copy.deepcopy(self.s)
        pros = [g for g in s.active_golfers() if g.status == 'pro' and g.lifestyle == 'full_time' and g.country == 'USA'
                and g.tour in TOUR_BY_KEY and TOUR_BY_KEY[g.tour].tier == 4 and s.staff.caddie(g.id) is None]
        a, b = pros[0], next(g for g in pros[1:] if g.tour == pros[0].tour)
        s.places.move(b.id, 2027, 53, ('England', 'Surrey'), 'test')
        tour = a.tour
        s.__dict__.pop('_trip_cost', None)
        ab = (s.tour_trip_cost(a, tour), s.tour_trip_cost(b, tour))
        s.__dict__.pop('_trip_cost', None)
        ba = (s.tour_trip_cost(b, tour), s.tour_trip_cost(a, tour))
        self.assertEqual(ab, ba[::-1])                                       # whatever the order
        self.assertGreater(ab[1], ab[0])                                     # England is far from a US mini tour
        self.assertEqual(b.country, 'USA')
        week = 10
        for e in (e for e in s.cal.editions(2028) if e.week == week):
            self.assertEqual(s.eligible(a, e.series, week), s.eligible(b, e.series, week), e.series.series_id)
        self.assertEqual(b.tour, tour)                                       # no card from moving

    def test_payments_follow_residence_through_the_real_weeks(self):
        """Two golfers of one nationality, one living abroad: every event each plays is charged from where
        they live (fees, plans and appeal caches keyed by residence, not shared by nationality)."""
        s = Season(generate_world(seed=16, scale=0.2), seed=16, development=True, workers=1)
        s.start_year(2027)
        movers = [g for g in s.active_golfers() if g.status == 'pro' and g.lifestyle == 'full_time'
                  and g.country == 'USA' and s.staff.caddie(g.id) is None][:40:2]
        for g in movers:
            s.places.move(g.id, 2027, 0, ('Canada', 'Ontario'), 'test')
            g.cash += 50000                                                  # so they can afford to play
        for w in range(1, 9):
            s.advance_week(2027, w)
        checked = 0
        for g in s.active_golfers():
            if g.status != 'pro' or g.country != 'USA' or not s.played[2027].get(g.id):
                continue
            expected = 0.0
            for r in s.results.values():
                for k, site in enumerate(r.finish):
                    if any(gid == g.id for gid, _, _ in site):
                        expected += FIN.event_cost(g, s.cal.by_id[r.series_id], r.sites[min(k, len(r.sites) - 1)][2],
                                                   s.home_country(g))
            self.assertAlmostEqual(s.ledger(2027, g.id).events, expected, delta=0.01, msg=g.id)
            checked += g in movers
        self.assertGreater(checked, 3)
        s.close()

    def _setting(self, cash, live_in, adaptability=70.0):
        s = copy.deepcopy(self.s)
        g = next(g for g in s.active_golfers() if g.status == 'pro' and g.country not in ('South Africa',)
                 and COUNTRY_REGION(g.country) == 'Africa')
        g.country = 'Nigeria'                                                # a West African professional
        s.places.birth[g.id] = ('Nigeria', 'Lagos State')
        s.places.home[g.id] = live_in
        g.status, g.lifestyle, g.tour = 'pro', 'full_time', sa_tour()
        g.cash, g.backing, g.backer_funds, g.backer = cash, 0.0, 0.0, 0.0
        g.personality['adaptability'] = adaptability
        return s, g

    def test_moving_staying_and_returning_are_all_possible(self):
        s, g = self._setting(5000.0, ('Nigeria', 'Lagos State'), adaptability=100.0)
        best, p = RES.move_odds(s, g, 2027)
        self.assertEqual(best, 'South Africa')                               # a broke player feels every flight
        self.assertGreater(p, 0.5)                                           # likely ...
        self.assertLess(p, 1.0)                                              # ... never certain
        s, g = self._setting(5000.0, ('Nigeria', 'Lagos State'), adaptability=0.0)
        self.assertLess(RES.move_odds(s, g, 2027)[1], p)                     # home pulls harder on others
        s, g = self._setting(3_000_000.0, ('Nigeria', 'Lagos State'))
        best, p = RES.move_odds(s, g, 2027)
        self.assertLess(p, 0.1)                                              # wealthy: travel is no burden, stays
        s, g = self._setting(3_000_000.0, ('South Africa', 'Gauteng'))
        best, p = RES.move_odds(s, g, 2027)
        self.assertEqual(best, 'Nigeria')                                    # a successful expatriate may go home
        self.assertGreater(p, 0.3)
        self.assertLess(p, 1.0)
        s, g = self._setting(3_000_000.0, ('South Africa', 'Gauteng'), adaptability=100.0)
        self.assertLess(RES.move_odds(s, g, 2027)[1], RES.move_odds(*self._setting(3_000_000.0, ('South Africa', 'Gauteng'))[:2], 2027)[1])
        s, g = self._setting(5000.0, ('South Africa', 'Gauteng'))
        self.assertEqual(RES.move_odds(s, g, 2027), ('South Africa', 0.0))   # a broke expatriate stays near events

    def test_a_career_move_is_paid_for_and_then_held(self):
        s, g = self._setting(40000.0, ('Nigeria', 'Lagos State'), adaptability=100.0)
        s.places.since[g.id] = 2020
        cash = g.cash
        RES.review_moves(s, 2027, {})
        moved = s.places.home[g.id][0] == 'South Africa'
        if moved:
            self.assertAlmostEqual(cash - g.cash, RES.MOVE_COST)
            self.assertEqual(s.ledgers[2027][g.id].moving, RES.MOVE_COST)
        s.places.home[g.id] = ('South Africa', 'Gauteng')
        s.places.since[g.id] = 2027
        g.cash = 3_000_000.0                                                 # now they could go home ...
        before = list(s.places.moves.get(g.id, []))
        RES.review_moves(s, 2028, {})
        self.assertEqual(s.places.moves.get(g.id, []), before)               # ... but not the next winter

    def test_one_geography_across_playing_and_staff_careers(self):
        s = copy.deepcopy(self.s)
        g = next(g for g in s.active_golfers() if g.status == 'pro' and s.places.known(g.id))
        rng = __import__('random').Random(1)
        k = s.staff.from_golfer(g, 2027, 'caddie', rng, 'mini-tour')
        s.staff.caddies[k.id] = k
        self.assertEqual(k.id, g.id)
        place = s.places.home[g.id]
        RES._record(s, k.id, 2028, 53, ('Japan', 'Tokyo'), 'to be near their player')
        self.assertEqual(s.places.home[g.id], ('Japan', 'Tokyo'))            # one record: no stale golfer copy
        self.assertTrue(any('Moved from' in t for _, t in k.history))
        self.assertEqual(s.places.residence_at(g.id, 2027), place)           # the past stays where it was
        people = ArchiveWriter.__new__(ArchiveWriter)
        people.created, people.initial = {}, set()
        p = people.state_tables(s)['people.json.gz'][g.id]
        self.assertEqual(p['nationality'], g.country)
        self.assertEqual(p['residence'], {'country': 'Japan', 'region': 'Tokyo'})
        self.assertEqual(p['moves'][-1]['reason'], 'to be near their player')
        self.assertIn('caddie', p)

    def test_archive_answers_where_they_lived_then(self):
        import tempfile
        s = self.s
        d = Path(tempfile.mkdtemp())
        w = ArchiveWriter(d, s)
        w.write_year(s, 2027) if 2027 in s.snapshots else None
        w.write_state(s)
        a = Archive(d)
        moved = next(m for m in s.move_log[2027])
        pid = moved['person']
        self.assertEqual(a.residence_at(pid, 2027, 52), {'country': moved['from'][0], 'region': moved['from'][1]})
        self.assertEqual(a.residence_at(pid, 2028), {'country': moved['to'][0], 'region': moved['to'][1]})
        if 2027 in s.snapshots and pid in s.snapshots[2027]:
            self.assertEqual(a.year(2027)['careers'][pid]['residence'], list(moved['from']))
        self.assertEqual(a.geography(pid)['moves'][-1]['reason'], moved['reason'])

    def test_legacy_people_stay_unknown(self):
        s = Season(generate_world(seed=17, scale=0.1), seed=17, development=True, workers=1)
        state = s.__getstate__()
        for k in ('places', 'move_log', 'move_blocked'):
            del state[k]
        old = Season.__new__(Season)
        old.__setstate__(pickle.loads(pickle.dumps(state)))
        g = old.world.golfers[0]
        self.assertFalse(old.places.known(g.id))
        self.assertIsNone(old.places.export(g.id)['birthplace'])
        self.assertEqual(old.home_country(g), g.country)                     # travel from their nationality
        RES.settle(old, 2027, 53)
        self.assertFalse(old.places.known(g.id))                             # never invented afterwards
        self.assertFalse(old.places.moves)


class MoveFundingTests(unittest.TestCase):
    """A winter move is paid at once, in its own year, by the one funding order (cash, then backers' money,
    then family money), with each pot reconcilable; a move the golfer's own money cannot cover is not made.
    The move itself is forced (its odds set to certain for one golfer) so every case really moves."""

    @classmethod
    def setUpClass(cls):
        cls.base = Season(generate_world(seed=18, scale=0.1), seed=18, development=True, workers=1)
        cls.base.start_year(2027)

    def _move(self, cash, backer_funds=0.0, backer=0.0, backing=0.0):
        from unittest import mock
        s = copy.deepcopy(self.base)
        g = next(g for g in s.active_golfers() if g.status == 'pro' and g.lifestyle == 'full_time'
                 and g.tour in TOUR_BY_KEY and s.places.known(g.id) and s.staff.coach(g.id) is None)
        g.cash, g.backer_funds, g.backer, g.backing = cash, backer_funds, backer, backing
        self.assertLess(FIN.RESERVE_WEEKS * s.committed_weekly(g), 4000)   # living costs only: the reserve
        s.places.since[g.id] = 2000
        here = s.places.home[g.id][0]
        dest = 'England' if here != 'England' else 'Japan'
        before = copy.deepcopy(s.ledger(2027, g.id))
        odds = lambda season, x, year, changed=False: (dest, 1.0) if x.id == g.id else (season.places.home[x.id][0], 0.0)
        with mock.patch.object(RES, 'move_odds', odds):
            RES.review_moves(s, 2027, {})
        return s, g, before, dest

    def test_backers_money_pays_before_the_next_years_top_up(self):
        s, g, before, dest = self._move(cash=0.0, backer_funds=10000.0, backer=20000.0)
        self.assertEqual(s.places.home[g.id][0], dest)                      # it really moved
        led = s.ledger(2027, g.id)
        self.assertEqual(led.moving - before.moving, RES.MOVE_COST)
        self.assertEqual(led.backer_support - before.backer_support, RES.MOVE_COST)   # drawn now, this year
        self.assertEqual((g.cash, g.backer_funds), (0.0, 4000.0))           # from the pot that was left
        s.start_backing(g, 2028)                                            # 1 January: the deal tops up
        self.assertEqual(g.backer_funds, 20000.0)
        self.assertEqual(s.backer_flows[2028][(g.id, 'put_up')], 16000.0)  # 2028's money did not pay for it

    def test_family_money_pays_when_there_are_no_backers(self):
        s, g, before, dest = self._move(cash=0.0, backing=10000.0)
        self.assertEqual(s.places.home[g.id][0], dest)
        led = s.ledger(2027, g.id)
        self.assertEqual(led.support - before.support, RES.MOVE_COST)
        self.assertEqual((g.cash, g.backing), (0.0, 4000.0))

    def test_cash_pays_first(self):
        s, g, before, dest = self._move(cash=20000.0, backer_funds=10000.0, backer=20000.0, backing=5000.0)
        self.assertEqual(s.places.home[g.id][0], dest)
        led = s.ledger(2027, g.id)
        self.assertEqual(led.moving - before.moving, RES.MOVE_COST)
        self.assertEqual(led.backer_support + led.support, before.backer_support + before.support)
        self.assertEqual((g.cash, g.backer_funds, g.backing), (14000.0, 10000.0, 5000.0))

    def test_cash_then_backers_then_family(self):
        s, g, before, dest = self._move(cash=3000.0, backer_funds=2000.0, backer=20000.0, backing=10000.0)
        self.assertEqual(s.places.home[g.id][0], dest)
        self.assertEqual((g.cash, g.backer_funds, g.backing), (0.0, 0.0, 9000.0))
        led = s.ledger(2027, g.id)
        self.assertEqual((led.backer_support - before.backer_support, led.support - before.support), (2000.0, 1000.0))

    def test_a_move_their_own_money_cannot_cover_is_not_made(self):
        s, g, before, dest = self._move(cash=1000.0, backing=2000.0)
        self.assertNotEqual(s.places.home[g.id][0], dest)
        self.assertEqual((g.cash, g.backing), (1000.0, 2000.0))
        self.assertEqual(s.ledger(2027, g.id).moving, before.moving)
        self.assertEqual(s.move_blocked[2027], 1)


def COUNTRY_REGION(country):
    from golfsim.geography import COUNTRIES
    return COUNTRIES[country].region


if __name__ == '__main__':
    unittest.main()
