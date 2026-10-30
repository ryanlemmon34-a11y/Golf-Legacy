"""Major places and money: every place records the money it was decided on (what the golfer could draw, what
was set aside, what remained, the trip's cost and who paid), and the qualification ledger shows it; places
decided before this was kept say "not recorded". An earned place is never lost for money alone: the organizer
pays the trip's travel and entry, in kind (in no golfer's ledger, once per trip); injury still withdraws a
golfer; ordinary events and qualifying keep their costs.

Run from the project folder:  python -m unittest tests.test_major_funding -v
"""
from __future__ import annotations

import pickle
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer as O                                                  # noqa: E402


class MoneyFacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=91, workers=1, world=generate_world(seed=91, scale=0.03))
        s.advance(22)                                                   # the reference calendar's first two majors
        cls.rights = {m: {g: dict(r) for g, r in book.items()} for m, book in s.season.major_rights[2027].items()}
        s.close()
        cls.w = O.World(cls.tmp / 'w', workers=1)
        cls.w.reload()

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_every_decided_place_records_its_money(self):
        self.assertEqual(sorted(self.rights), ['PREMIER_TOUR_CHAMPIONSHIP', 'TOUR_MASTERS'])
        for major, book in self.rights.items():
            for gid, r in book.items():
                if r['result'].startswith('withdrawn') or r['result'].startswith('expired'):
                    continue                                            # (decided by injury, retirement, status)
                m = r.get('money')
                self.assertIsNotNone(m, (major, gid, r['result']))
                self.assertLessEqual(abs(m['funds'] - m['set_aside'] - m['spendable']), 1)   # (each rounded)
                self.assertGreater(m['trip'], 0)
                self.assertIn(m['paid_by'], ('golfer', 'organizer', 'school', 'club'))
                if r['result'] == 'declined: could not pay the trip':
                    self.assertLess(m['spendable'], m['trip'])          # the reason, in numbers

    def test_the_ledger_page_shows_it(self):
        html = O.render(self.w, '/qualification', parse_qs('major=TOUR_MASTERS&year=2027'))[1]
        self.assertIn('Money when the field was set', html)
        self.assertIn('could draw $', html)
        self.assertIn('paid by the golfer', html)

    def test_older_places_say_not_recorded(self):
        import observer_history as OH
        self.assertIn('not recorded', OH._place_money(O, {'result': 'entered'}))



class Guarantee(unittest.TestCase):
    """Reconstructed scenarios, not replays: the archive keeps the 269 major places Test 1 10.30 lost for money
    (221 amateurs, 42 professionals, 6 club professionals) but not each golfer's balance at the time, so the
    money positions behind them -- no savings, deep debt, no backers -- are given to golfers who hold earned
    places in a reference-calendar Masters, across the statuses present; one of them is also injured."""

    @classmethod
    def setUpClass(cls):
        from collections import defaultdict
        from golfsim import qualification as Q
        from golfsim.season import Season
        s = Season(generate_world(seed=93, scale=0.05), seed=93, development=True, workers=1, calendar='v2')
        s.start_year(2027)
        for wk in range(1, 15):                                         # to the week before the Masters (week 15)
            s.advance_week(2027, wk)
        f = Q.build_field('TOUR_MASTERS', 2027, s.ctx)
        by = defaultdict(list)
        for e in f.entries:
            g = s.g.get(e.golfer_id)
            if g is not None and g.lifestyle != 'retired' and g.id not in s.injured:
                by[g.status].append(g.id)
        cls.by = dict(by)
        cls.broke = by['pro'][:3] + by.get('amateur', [])[:3] + by.get('club_pro', [])[:2]
        cls.hurt = by['pro'][3]
        cls.rich = by['pro'][4]
        for gid in cls.broke + [cls.hurt]:
            g = s.g[gid]
            g.cash, g.backing, g.backer_funds = -250000.0, 0.0, 0.0      # deep debt, no backers
        s.g[cls.rich].cash += 1e7
        s.injured[cls.hurt] = (s.abs_week(2027, 30), 'scenario', 15)
        ledger = lambda gid: s.ledgers[2027].get(gid)
        cls.before = {gid: (s.g[gid].cash, (ledger(gid).events if ledger(gid) else 0.0)) for gid in cls.broke + [cls.rich]}
        cls.blob = pickle.dumps(s)
        s.advance_week(2027, 15)
        cls.s = s
        cls.again = pickle.loads(cls.blob)                              # the same week again, from the same save
        cls.again.advance_week(2027, 15)

    @classmethod
    def tearDownClass(cls):
        cls.s.close()
        cls.again.close()

    def test_no_earned_place_is_lost_for_money(self):
        s = self.s
        self.assertGreaterEqual(len(self.broke), 3)
        book = s.major_rights[2027]['TOUR_MASTERS']
        played = {g for rows in s.ctx.results[('TOUR_MASTERS', 2027)].values() for g, _ in rows}
        for gid in self.broke:
            self.assertEqual(book[gid]['result'], 'entered', (gid, s.g[gid].status))
            self.assertIn(gid, played)
            m = book[gid]['money']
            self.assertLess(m['spendable'], m['trip'])                  # they could not have paid
            self.assertEqual(m['paid_by'], 'organizer')
        self.assertFalse(any(r['result'].startswith('declined') for r in book.values()))
        self.assertEqual(book[self.hurt]['result'], 'withdrawn: injured')   # injury still applies
        self.assertFalse(any(t['gid'] == self.hurt for t in s.travel_grants[2027]))

    def test_the_trip_is_paid_in_kind_once(self):
        s = self.s
        grants = [t for t in s.travel_grants[2027] if t['event'].endswith('TOUR_MASTERS')]
        self.assertEqual(sorted(t['gid'] for t in grants), sorted(self.broke))   # one each, nobody else
        for t in grants:
            self.assertEqual((t['covers'], t['week']), ('travel and entry', 15))
            self.assertGreater(t['amount'], 0)
            led = s.ledgers[2027].get(t['gid'])
            cash0, events0 = self.before[t['gid']]
            self.assertEqual(led.events if led else 0.0, events0)        # nothing in the golfer's books
            net0 = self.net_before(t['gid'])                             # cash moved only by what the books show
            self.assertAlmostEqual(s.g[t['gid']].cash - cash0, (led.net if led else 0.0) - net0, places=4)
        led = s.ledgers[2027][self.rich]                                 # a golfer who can pay, pays
        self.assertGreater(led.events, self.before[self.rich][1])
        self.assertEqual(s.major_rights[2027]['TOUR_MASTERS'][self.rich]['money']['paid_by'], 'golfer')

    def net_before(self, gid):
        b = pickle.loads(self.blob).ledgers[2027].get(gid)
        return b.net if b else 0.0

    def test_ordinary_events_keep_their_costs(self):
        majors = {'TOUR_MASTERS', 'PREMIER_TOUR_CHAMPIONSHIP', 'USA_OPEN', 'BRITANNIA_OPEN'}
        s = self.s
        g = s.g[self.hurt]                                              # still in deep debt (did not play)
        regular = next(x for x in s.cal.series if x.category == 'regular' and x.tier == 2)
        qualifying = next(x for x in s.cal.series if x.kind == 'qualifying')
        for series in (regular, qualifying):                            # no guarantee there: the usual rule
            self.assertFalse(s.can_afford(g, series, series.cities[0], s.spendable(g, 2027)), series.series_id)
        self.assertFalse(any(sid in majors for lst in self.s.declined[2027].values() for sid in lst))
        self.assertEqual({t['event'].split(':')[1] for t in self.s.travel_grants[2027]}, {'TOUR_MASTERS'})

    def test_the_same_week_from_the_same_save_is_identical(self):
        a, b = self.s, self.again
        self.assertEqual(a.travel_grants[2027], b.travel_grants[2027])
        self.assertEqual(a.ctx.results[('TOUR_MASTERS', 2027)], b.ctx.results[('TOUR_MASTERS', 2027)])
        self.assertEqual(pickle.loads(pickle.dumps(a)).travel_grants[2027], a.travel_grants[2027])   # kept in saves


if __name__ == '__main__':
    unittest.main()
