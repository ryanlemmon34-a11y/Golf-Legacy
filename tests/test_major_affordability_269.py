"""F2: every one of the 269 major places Test 1 10.30 declined for money, by category, through today's entry path.

tests/fixtures/major_affordability_declines_269.json (HAL's manifest; README beside it) lists each recorded decline:
the major, the year and week, the golfer's status, the qualification routes and whether the place was earned or
conditional (an amateur's place, which lapses on turning professional). It does NOT keep the money behind them --
null is unknown, and no balance is invented here. So this is coverage, not a replay of the old world: for every row
an explicitly SYNTHETIC golfer is built with that row's status, residence, lifestyle and routes, in that row's
year, and is made broke on purpose (no savings, credit used up, no family money, no backers, no amateur
support), with a caddie on the bag. Only the facts that give those routes are recorded (a fresh qualification
context per row), and the major's week is run through the real weekly path (Season.run_week with that week's
major edition only: special_field -> major_field -> lock_rights -> reserve -> the round played -> record_event).

Each row asserts: the place is used (in the field, played), the right is recorded 'entered' with its routes, state
and money facts (could not pay; paid by the organizer), the organizer paid the travel and entry once, in kind (one
travel grant; nothing in the golfer's events ledger; cash moves only by what the books show), and the caddie's
week stays the golfer's. Every conditional row is run a second time with a golfer who has turned professional:
the place lapses ('expired: turned professional'), nobody pays anything.

Rows are grouped by category (status, major, earned/conditional, routes): one fact recipe per category, asserted
row by row with subTest(case_id). About 15 seconds on a tiny world (scale 0.01); no season is simulated.

Run from the project folder:  python -m unittest tests.test_major_affordability_269 -v
"""
from __future__ import annotations

import copy
import json
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import finance as FIN                                    # noqa: E402
from golfsim import qualification as Q                                # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.season import Season                                     # noqa: E402

FIXTURE = ROOT / 'tests' / 'fixtures' / 'major_affordability_declines_269.json'
HARPER = 23529
NOBODY = -1                      # a winner who is not in the world (so a runner-up place is the golfer's alone)
AGE = {'amateur': 24, 'pro': 30, 'club_pro': 40}


def load_rows():
    m = json.loads(FIXTURE.read_text())
    return m, [dict(zip(m['columns'], r)) for r in m['cases']]


def category(r):
    return r['status'], r['major'], r['right_state'], tuple(sorted(r['qualification_routes']))


# The facts behind each route code (calendar v2 rules), for a golfer `gid` in the `y` edition of the major:
# ('result', series, edition year, [(gid, position)]), ('ranking', year, cut-off, [ids in order]) or ('award', year).
# Ids that are not in the world (NOBODY, negative ids) hold the places ahead of the golfer and are never eligible.
def route_facts(code, gid, y):
    win, second = [(gid, 1)], [(NOBODY, 1), (gid, 2)]
    return {
        'U2': [('result', 'USA_AMATEUR', y - 1, win)], 'M4': [('result', 'USA_AMATEUR', y - 1, win)],
        'B10': [('result', 'USA_AMATEUR', y - 1, win)],
        'U2R': [('result', 'USA_AMATEUR', y - 1, second)], 'M4R': [('result', 'USA_AMATEUR', y - 1, second)],
        'U3': [('result', 'USA_MID_AMATEUR', y - 1, win)], 'M8': [('result', 'USA_MID_AMATEUR', y - 1, win)],
        'U4': [('result', 'BRITANNIA_AMATEUR', y - 1, win)], 'M5': [('result', 'BRITANNIA_AMATEUR', y - 1, win)],
        'B9': [('result', 'BRITANNIA_AMATEUR', y, win)],
        'M6': [('result', 'ASIA_PACIFIC_AMATEUR', y - 1, win)], 'B12': [('result', 'ASIA_PACIFIC_AMATEUR', y - 1, win)],
        'M7': [('result', 'LATIN_AMERICA_AMATEUR', y, win)],
        'M16': [('result', 'COLLEGE_NATIONAL_CHAMPIONSHIP', y - 1, win)],
        'B11': [('result', 'EUROPEAN_AMATEUR', y, win)],
        'UA': [('award', y - 1)], 'B13': [('award', y - 1)],
        'M1': [('result', 'TOUR_MASTERS', y - 2, win)],               # a past champion (not last year's top 12)
        'M9': [('result', 'TOUR_MASTERS', y - 1, [(gid, 5)])],
        'M10': [('result', 'USA_OPEN', y - 1, [(gid, 3)])],
        'U5': [('result', 'TOUR_MASTERS', y - 1, win)], 'B3': [('result', 'TOUR_MASTERS', y - 1, win)],
        'P2': [('result', 'TOUR_MASTERS', y - 1, win)],
        'U7': [('result', 'USA_OPEN', y - 1, [(gid, 5)])],
        'B2': [('result', 'BRITANNIA_OPEN', y - 1, [(gid, 4)])],
        'P4': [('result', 'PREMIER_TOUR_CHAMPIONSHIP', y - 1, [(gid, 5)])],
        'P5': [('result', 'CLUB_PRO_CHAMPIONSHIP', y, win)],
        'UQ': [('result', 'USA_OPEN_FINAL', y, win)], 'BQ': [('result', 'BRITANNIA_FINAL', y, win)],
        'B5': [('ranking', y, 'britannia_ranking', [gid])], 'BF': [('ranking', y, 'britannia_fill', [gid])],
        # the USA Open's fill list is the week-24 ranking, whose top 60 is exempt (U10): just outside it
        'UF': [('ranking', y, 'usa_fill', list(range(-60, 0)) + [gid])],
    }[code]


class Coverage269(unittest.TestCase):
    """All 269 rows, each through the real major entry path in its own minimal state (see the module docstring)."""

    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.rows = load_rows()
        world = generate_world(seed=97, scale=0.01)                   # a tiny world: templates and a calendar
        s = Season(world, seed=97, development=False, workers=1, calendar='v2')
        s.start_year(s.first_year)
        cls.s = s
        cls.templates = {st: next(g for g in world.golfers if g.status == st and g.lifestyle != 'retired')
                         for st in ('amateur', 'pro', 'club_pro')}
        cls.cut = s.cal.spec.cutoffs
        cls.out, cls.lapsed = {}, {}
        for r in sorted(cls.rows, key=lambda r: (r['year'], r['event_week'], r['case_id'])):
            cls.out[r['case_id']] = cls.run_row(r, lapse=False)
            if r['right_state'] == 'conditional':
                cls.lapsed[r['case_id']] = cls.run_row(r, lapse=True)

    @classmethod
    def tearDownClass(cls):
        cls.s.close()

    # ---- one row: a synthetic broke golfer, the route's facts, the major's week --------------------------
    @classmethod
    def golfer(cls, r, lapse):
        s = cls.s
        y = r['year']
        g = copy.deepcopy(cls.templates[r['status']])
        g.id = s.world.new_id()
        g.name = f'Synthetic {r["case_id"]}' + (' (turned pro)' if lapse else '')
        g.country, g.born, g.lifestyle = r['country'], y - AGE[r['status']], r['lifestyle']
        g.familiarity = {}
        # broke on purpose: no savings and the credit line used up; no family money, no backers
        g.cash = -FIN.credit_limit(0.0)
        g.backing = g.backer = g.backer_funds = 0.0
        if lapse:                                                      # held a place as an amateur, then turned pro
            g.status, g.turned_pro = 'pro', y
        s.world.golfers.append(g)
        s.g[g.id] = g
        s.places.home[g.id] = tuple(r['residence'])
        s.am_support.pop(g.id, None)                                   # no amateur support
        k = next(k for kid, k in sorted(s.staff.caddies.items()) if kid not in s.staff._bags())
        s.staff.assign_caddie(s, g, k, (y, r['event_week'] - 1), 'scenario')
        return g, k

    @classmethod
    def run_row(cls, r, lapse):
        s = cls.s
        y, wk, sid = r['year'], r['event_week'], r['major']
        g, k = cls.golfer(r, lapse)
        s.ctx = Q.QualificationContext.from_calendar(s.cal)            # only this row's facts
        s.refresh_people(y)
        for code in r['qualification_routes']:
            for f in route_facts(code, g.id, y):
                if f[0] == 'result':
                    _, series, ey, rows = f
                    s.ctx.add_result(series, ey, s.ctx.finishers(series, ey) + rows, week=s.ctx.event_weeks[series])
                elif f[0] == 'ranking':
                    s.ctx.world_rankings[(f[1], cls.cut[f[2]])] = f[3]
                else:
                    s.ctx.awards[('amateur_award', f[1])] = g.id
        if lapse:                                                      # the place as recorded before the field
            s.note_right(y, sid, g.id, r['qualification_routes'], 'conditional', r['right_awarded'],
                         ['synthetic scenario'])
        ed = next(e for e in s.cal.editions(y) if e.series.series_id == sid)
        led = lambda: s.ledgers[y].get(g.id)
        receipts = s.staff_receipts[y][('caddie', k.id)]
        cash0 = g.cash
        spend0 = s.spendable(g, y)
        s.year = y
        s.run_week(y, wk, [ed])                                        # the major's week, through the real path
        res = s.results.get(ed.event_id)                               # (an unheld week keeps an older result)
        out = dict(
            gid=g.id, event=ed.event_id, week=wk, spendable_before=spend0,
            in_field=g.id in s.entry_routes.get((y, sid), {}),
            route=s.entry_routes.get((y, sid), {}).get(g.id),
            played=bool(res) and any(x[0] == g.id for f in res.finish for x in f),
            right=copy.deepcopy(s.major_rights[y].get(sid, {}).get(g.id)),
            grants=[dict(t) for t in s.travel_grants[y] if t['gid'] == g.id],
            declined=list(s.declined[y].get(g.id, [])),
            events=led().events if led() else 0.0, caddie=led().caddie if led() else 0.0,
            caddie_share=led().caddie_share if led() else 0.0,
            net=led().net if led() else 0.0, cash=g.cash - cash0,
            caddie_fee=k.weekly_fee, caddie_receipts=s.staff_receipts[y][('caddie', k.id)] - receipts,
            cost=FIN.event_cost(g, ed.series, s.lib.venues(y)[ed.event_id][0].city, s.home_country(g)))
        s.staff.end_caddie(s, g.id, (y, wk), 'scenario over', 'golfer')   # free the bag; retire the scenario golfer
        g.lifestyle = 'retired'
        s.injured.pop(g.id, None)
        return out

    # ---- the table ------------------------------------------------------------------------------------
    def each(self, which=None):
        """[(row, its subTest labels, what its run recorded)], every row of the manifest (or those `which` keeps)."""
        return [(r, dict(case=r['case_id'], category=category(r)), self.out[r['case_id']])
                for r in self.rows if which is None or which(r)]

    def test_the_place_is_used(self):
        for r, tag, o in self.each():
            with self.subTest(**tag):
                self.assertTrue(o['in_field'])
                self.assertIn(o['route'], r['qualification_routes'])   # entered by one of the row's own routes
                self.assertTrue(o['played'])
                self.assertEqual(o['declined'], [])

    def test_the_right_is_recorded_entered_with_its_money(self):
        for r, tag, o in self.each():
            with self.subTest(**tag):
                right = o['right']
                self.assertEqual(right['result'], 'entered')
                self.assertEqual(set(right['routes']), set(r['qualification_routes']))
                self.assertEqual(right['state'], r['right_state'])    # a conditional place, still an amateur: honoured
                m = right['money']
                self.assertLess(m['spendable'], m['trip'])             # could not have paid
                self.assertLessEqual(o['spendable_before'], 0)
                self.assertEqual(m['support'], 0)
                self.assertEqual(m['paid_by'], 'organizer')
                self.assertEqual(m['trip'], round(o['cost'] + o['caddie_fee']))   # travel and entry, and the caddie

    def test_the_organizer_pays_travel_and_entry_once_in_kind(self):
        for r, tag, o in self.each():
            with self.subTest(**tag):
                self.assertEqual(len(o['grants']), 1)
                t = o['grants'][0]
                self.assertEqual((t['event'], t['week'], t['covers'], t['source']),
                                 (o['event'], r['event_week'], 'travel and entry', 'organizer: an earned major place'))
                self.assertGreater(t['amount'], 0)
                self.assertAlmostEqual(t['amount'], o['cost'], places=2)
                self.assertEqual(o['events'], 0.0)                     # in no golfer's ledger
                self.assertAlmostEqual(o['cash'], o['net'], places=4)  # cash moved only by what the books show

    def test_the_caddies_week_stays_the_golfers(self):
        for r, tag, o in self.each():
            with self.subTest(**tag):
                self.assertAlmostEqual(o['caddie'], o['caddie_fee'], places=2)
                # the caddie is paid by the golfer: the week's fee (and a professional's prize share, if any)
                self.assertAlmostEqual(o['caddie_receipts'], o['caddie_fee'] + o['caddie_share'], places=2)

    def test_a_conditional_place_lapses_on_turning_professional(self):
        for r, tag, o in self.each(lambda r: r['right_state'] == 'conditional'):
            with self.subTest(**tag):
                lo = self.lapsed[r['case_id']]
                self.assertEqual(lo['right']['result'], 'expired: turned professional')
                self.assertFalse(lo['in_field'] or lo['played'])
                self.assertEqual(lo['grants'], [])
                self.assertEqual(lo['events'], 0.0)
        self.assertEqual(len(self.lapsed), self.manifest['counts']['by_right_state']['conditional'])

    def test_every_row_is_covered(self):
        ids = [r['case_id'] for r in self.rows]
        self.assertEqual(len(ids), 269)
        self.assertEqual(len(set(ids)), 269)
        self.assertEqual(set(self.out), set(ids))
        c = self.manifest['counts']
        self.assertEqual(Counter(r['status'] for r in self.rows), c['by_status'])
        self.assertEqual(Counter(r['major'] for r in self.rows), c['by_major'])
        self.assertEqual(Counter(r['right_state'] for r in self.rows), c['by_right_state'])
        self.assertEqual(len({r['person_id'] for r in self.rows}), c['unique_people'])
        cats = defaultdict(list)
        for r in self.rows:
            cats[category(r)].append(r['case_id'])
        self.assertEqual(sum(map(len, cats.values())), 269)            # every row in exactly one category
        self.assertTrue(all(self.out[i]['right']['result'] == 'entered' for i in ids))

    def test_harper_all_eight_with_the_modeled_six_labelled(self):
        harper = [r for r in self.rows if r['person_id'] == HARPER]
        self.assertEqual(len(harper), 8)                               # every recorded Harper decline
        recorded_2047 = [r for r in harper if r['year'] == 2047]       # recorded, no modeled cost
        modeled = [r for r in harper if r['harper_modeled_trip_cost'] is not None]
        self.assertEqual(len(recorded_2047), 2)
        self.assertEqual(len(modeled), 6)                              # the previously modeled 2048-2050 subset
        self.assertEqual({r['year'] for r in modeled}, {2048, 2049, 2050})
        self.assertEqual(len(recorded_2047) + len(modeled), self.manifest['counts']['harper_total'])
        self.assertEqual(len(modeled), self.manifest['counts']['harper_previously_modeled_subset'])
        for r in harper:
            with self.subTest(case=r['case_id']):
                self.assertEqual(self.out[r['case_id']]['right']['result'], 'entered')
                self.assertEqual(len(self.out[r['case_id']]['grants']), 1)

    def test_no_historical_money_is_invented(self):
        m = self.manifest
        self.assertEqual(m['common_unknown_fields'], {'decision_time_balance': None, 'recorded_trip_cost': None})
        c = m['counts']
        self.assertEqual((c['recorded_cost_available'], c['decision_time_balance_available']), (0, 0))
        for r in self.rows:                                            # only Harper's six carry a (modeled) cost
            self.assertEqual(r['harper_modeled_trip_cost'] is not None,
                             r['person_id'] == HARPER and r['year'] >= 2048)


if __name__ == '__main__':
    unittest.main()
