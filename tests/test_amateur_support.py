"""Amateur support (rules 2026-11-02): restricted, in-kind help with an amateur's golf costs, earned by observable
success. Payment order (a school's or club's own events, then the support, then the golfer), exhausted budgets,
in-season upgrades (never a cut), renewal one band lower at most, the end on turning professional, no double
funding with the major-trip guarantee, never living or moving costs, and the unchanged affordability rule for
everyone else. Every payment is recorded with what it covered and the band, and the books reconcile.

Run from the project folder:  python -m unittest tests.test_amateur_support -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import amateur_support as AS                               # noqa: E402
from golfsim import finance as FIN                                      # noqa: E402
from golfsim.population import generate_world                           # noqa: E402
from golfsim.season import Season                                       # noqa: E402


def fresh(seed=93):
    s = Season(generate_world(seed=seed, scale=0.05), seed=seed, development=True, workers=1, calendar='v2')
    s.start_year(2027)
    return s


class Rules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import copy
        cls.s = fresh()
        cls.opened = copy.deepcopy(cls.s.am_support)                     # as week 1 opened (tests change it)

    @classmethod
    def tearDownClass(cls):
        cls.s.close()

    def amateur(self, band=None, exclude=()):
        s = self.s
        return next(g for g in sorted(s.world.golfers, key=lambda x: x.id) if AS.eligible(g) and g.id not in exclude
                    and (band is None and g.id not in s.am_support or band and s.am_support.get(g.id, {}).get('band') == band))

    def test_bands_open_from_observable_facts(self):
        s = self.s
        self.assertTrue(self.opened)
        for gid, c in self.opened.items():
            g = s.g[gid]
            self.assertTrue(AS.eligible(g))
            self.assertEqual(c['cap'], AS.BANDS[c['band']])
            self.assertEqual((c['drawn'], c['from']), (0.0, [2027, 1]))
            self.assertTrue(c['basis'])
            rank = s.am_pos.get(gid)
            if rank is not None and rank <= 10:
                self.assertEqual(c['band'], 'A')
            for why in c['basis']:                                       # nothing hidden: ranks, titles, results
                self.assertFalse(any(w in why for w in ('potential', 'ceiling', 'overall')))
        for gid, rank in s.am_pos.items():
            if rank <= 150 and AS.eligible(s.g[gid]):
                self.assertIn(gid, self.opened)                          # the top 150 are all supported

    def test_payment_order_and_an_exhausted_budget(self):
        s = self.s
        g = self.amateur('C')
        c = s.am_support[g.id]
        cash0, led = g.cash, s.ledger(2027, g.id)
        ev0, sup0 = led.events, led.am_support
        s.spend(g, 2027, 'events', 3000.0, '2027:TEST_A')                # support first
        self.assertEqual((round(g.cash - cash0, 2), c['drawn']), (0.0, 3000.0))
        s.spend(g, 2027, 'events', 4000.0, '2027:TEST_B')                # 2,000 left: the golfer pays the rest
        self.assertEqual((round(g.cash - cash0, 2), c['drawn']), (-2000.0, 5000.0))
        s.spend(g, 2027, 'coaching', 500.0)                              # exhausted: all theirs
        self.assertEqual(round(g.cash - cash0, 2), -2500.0)
        self.assertEqual(AS.left(s, g), 0.0)
        self.assertEqual((led.events - ev0, led.am_support - sup0), (7000.0, 5000.0))   # cost in full, support beside
        log = [p for p in s.am_support_log[2027] if p['gid'] == g.id]
        self.assertEqual([(p['covers'], p['amount'], p['event'], p['band']) for p in log],
                         [('events', 3000.0, '2027:TEST_A', 'C'), ('events', 2000.0, '2027:TEST_B', 'C')])

    def test_only_golf_costs(self):
        s = self.s
        g = self.amateur('B')
        before = s.am_support[g.id]['drawn']
        cash0 = g.cash
        for field in ('living', 'moving'):
            s.spend(g, 2027, field, 1000.0)
        self.assertEqual(s.am_support[g.id]['drawn'], before)            # never living costs or moves
        self.assertEqual(round(g.cash - cash0, 2), -2000.0)
        s.spend(g, 2027, 'caddie', 800.0)                               # a caddie's weekly fee: yes
        self.assertEqual(s.am_support[g.id]['drawn'], before + 800.0)

    def test_school_and_club_events_draw_nothing(self):
        s = self.s
        college = next((g for g in s.world.golfers if g.id in s.am_support and g.tour.startswith('CO_')), None)
        if college is None:
            self.skipTest('no supported college golfer in this world')
        series = next(x for x in s.cal.series if x.tier == 5)
        self.assertEqual(FIN.event_payer(college, series), 'school')
        self.assertEqual(FIN.event_cost(college, series, series.cities[0]), 0.0)   # nothing to cover

    def test_support_counts_for_golf_choices_only_for_the_supported(self):
        s = self.s
        g = self.amateur('A')
        pro = next(x for x in s.world.golfers if x.status == 'pro' and x.lifestyle == 'full_time')
        unsup = self.amateur('C')                                        # an amateur without support:
        held = s.am_support.pop(unsup.id)
        base = lambda x: s.funds(x, 2027) - FIN.RESERVE_WEEKS * s.committed_weekly(x) - s._reserved.get(x.id, 0.0)
        try:
            self.assertEqual(s.spendable(g, 2027), base(g) + AS.left(s, g))
            self.assertEqual(s.spendable(pro, 2027), base(pro))          # everyone else: the rule as it was
            self.assertEqual(s.spendable(unsup, 2027), base(unsup))
        finally:
            s.am_support[unsup.id] = held
        ordinary = next(x for x in s.cal.series if x.category == 'regular' and x.tier == 3)
        qualifying = next(x for x in s.cal.series if x.kind == 'qualifying')
        for series in (ordinary, qualifying):                             # can_afford itself is unchanged
            cost = s.trip_cost(pro, series, series.cities[0])
            self.assertTrue(s.can_afford(pro, series, series.cities[0], cost))
            self.assertFalse(s.can_afford(pro, series, series.cities[0], cost - 1))

    def test_an_upgrade_adds_the_difference_and_nothing_is_cut(self):
        s = self.s
        g = self.amateur('C', exclude={self.amateur('C').id})
        c = s.am_support[g.id]
        c['drawn'] = 1000.0
        s.am_pos[g.id] = 30                                              # into the top 50 this week
        AS.upgrade(s, 2027, 20)
        self.assertEqual((c['band'], c['cap'], c['drawn']), ('B', 12000.0, 1000.0))
        self.assertEqual(c['upgrades'][-1][:3], [2027, 21, 'B'])         # from the next week
        s.am_pos[g.id] = 140                                             # slipping back cuts nothing
        AS.upgrade(s, 2027, 21)
        self.assertEqual((c['band'], c['cap']), ('B', 12000.0))

    def test_turning_professional_ends_it(self):
        s = self.s
        g = self.amateur('B', exclude=set())
        g.status = 'pro'
        try:
            self.assertEqual(AS.left(s, g), 0.0)
            before = s.am_support[g.id]['drawn']
            s.spend(g, 2027, 'events', 500.0)
            self.assertEqual(s.am_support[g.id]['drawn'], before)
        finally:
            g.status = 'amateur'


class Seasons(unittest.TestCase):
    """A whole season and the next winter: the books, the archive record, renewal one band lower at most, the end
    on turning professional, and the major-trip guarantee never paying what the support pays."""

    @classmethod
    def setUpClass(cls):
        cls.s = s = fresh(97)
        for w in range(1, 53):
            s.advance_week(2027, w)
        cls.held = {g: c['band'] for g, c in s.am_support.items()}
        cls.status = {g: s.g[g].status for g in cls.held}
        s.finish_year(2027)
        s.start_year(2028)

    @classmethod
    def tearDownClass(cls):
        cls.s.close()

    def test_the_books_reconcile(self):
        s = self.s
        for g in s.world.golfers:
            led = s.ledgers[2027].get(g.id)
            if led is not None and g.id in self.held:
                pays = [p['amount'] for p in s.am_support_log[2027] if p['gid'] == g.id]
                self.assertAlmostEqual(led.am_support, sum(pays), delta=0.01 * len(pays) + 0.01)   # (each rounded)
        closed = s.am_support_seasons[2027]
        for gid, c in closed.items():
            self.assertLessEqual(c['drawn'], c['cap'] + 1e-6)
            self.assertAlmostEqual(sum(c['paid'].values()), c['drawn'], delta=0.5)
            self.assertTrue(set(c['paid']) <= set(AS.COVERS))

    def test_renewal_steps_down_one_band_at_most(self):
        s = self.s
        order = AS.ORDER
        for gid, band in self.held.items():
            g = s.g.get(gid)
            if g is None or not AS.eligible(g):
                self.assertNotIn(gid, s.am_support)                     # turned professional or retired: ended
                continue
            self.assertIn(gid, s.am_support, (gid, band))
            new = s.am_support[gid]['band']
            self.assertLessEqual(order.index(new), order.index(band) + 1, (gid, band, new))
        ended = [c for c in s.am_support_seasons[2027].values() if c['ended']]
        self.assertTrue(ended)
        self.assertTrue(all(c['ended'] in ('turned professional', 'retired') for c in ended))

    def test_no_trip_is_paid_twice(self):
        s = self.s
        grants = {(t['event'], t['gid']) for t in s.travel_grants[2027]}
        paid = {(p['event'], p['gid']) for p in s.am_support_log[2027] if p['covers'] == 'events'}
        self.assertFalse(grants & paid)                                 # organizer or support, never both
        for major, book in s.major_rights[2027].items():
            for gid, r in book.items():
                m = r.get('money')
                if m and gid in self.held and r['result'] == 'entered':
                    self.assertIn(m['paid_by'], ('amateur support', 'golfer and amateur support', 'organizer',
                                                 'golfer', 'school'))
                    if m['paid_by'] == 'amateur support':
                        self.assertGreaterEqual(m['support'], m['trip'])

    def test_it_is_archived(self):
        from golfsim.archive import ArchiveWriter
        import tempfile
        w = ArchiveWriter(Path(tempfile.mkdtemp()), self.s, touch=False)
        chunk = w.year_chunk(self.s, 2027) if hasattr(w, 'year_chunk') else None
        if chunk is None:
            self.skipTest('no direct chunk builder')
        self.assertEqual(set(chunk['amateur_support']), {str(g) for g in self.s.am_support_seasons[2027]})


class Shown(unittest.TestCase):
    """The profile says who is supported, by what band and why, and what it paid; the qualification ledger's money
    shows the support's part."""

    def test_profile_and_ledger(self):
        import shutil
        import tempfile
        sys.path.insert(0, str(ROOT / 'tools'))
        import observer as O
        from urllib.parse import parse_qs
        from golfsim.session import Session
        tmp = Path(tempfile.mkdtemp())
        try:
            s = Session.create(tmp / 'w', seed=93, workers=1, world=generate_world(seed=93, scale=0.05))
            s.advance(16)
            c = dict(s.season.am_support)
            s.close()
            w = O.World(tmp / 'w', workers=1)
            try:
                gid, con = next((g, x) for g, x in sorted(c.items()) if x['drawn'] > 0)
                html = O.render(w, f'/golfer/{gid}', {})[1]
                self.assertIn(f'<dt>Amateur support</dt><dd>Band {con["band"]}: up to ${con["cap"]:,.0f}', html)
                self.assertIn(con['basis'][0], html)
                q = O.render(w, '/qualification', parse_qs('major=TOUR_MASTERS&year=2027'))[1]
                self.assertIn('Money when the field was set', q)
            finally:
                w.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
