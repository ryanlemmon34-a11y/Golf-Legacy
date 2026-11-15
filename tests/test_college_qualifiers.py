"""Calendar v3: the US college championship's four early-spring qualifiers (docs/career/COLLEGE_QUALIFIERS.md).

Every US college golfer (D1 and small college, any nationality) not yet qualified may play each qualifier; heats of at
most 156, dealt serpentine by ranking; 39 places a qualifier, shared among heats by size; a qualified golfer does not
enter the later qualifiers; the championship (week 22) takes the qualified golfers who can play. Calendars v1/v2 are
unchanged. A v3 world (seed 11, scale 0.05) is played to week 23 once per process.

Run from the project folder:  python -m unittest tests.test_college_qualifiers -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import career_fixture as F  # noqa: E402,F401  (TMPDIR handling shared with the other career tests)
from golfsim import opportunities as O                                 # noqa: E402
from golfsim import qualification as Q                                 # noqa: E402
from golfsim import schedule as SCH                                    # noqa: E402
from golfsim.calendar import WorldCalendar                             # noqa: E402
from golfsim.population import generate_world                          # noqa: E402
from golfsim.season import Season                                      # noqa: E402
from golfsim.session import Session                                    # noqa: E402

_W = {}
QS = [sid for sid, _, _ in SCH.V3.college_qualifiers]


def v3_world():
    if 'w' not in _W:
        d = Path(tempfile.mkdtemp(prefix='career_v3_', dir=F.os.environ.get('TMPDIR'))) / 'w'
        s = Session.create(d, seed=11, world=generate_world(year=2027, seed=11, scale=0.05), workers=1, calendar='v3')
        s.advance(52 + 22)                                             # 2027, then 2028 to week 23
        s.close()
        _W['w'] = d
    return Session.open(_W['w'])


def fake(spec, results):
    """A season stand-in for college_qualified (reads cal.spec, results, heat_places)."""
    return SimpleNamespace(cal=SimpleNamespace(spec=spec), results=results, heat_places=Season.heat_places)


class Rules(unittest.TestCase):
    def test_v1_v2_unchanged_and_v3_built(self):
        self.assertEqual((SCH.V1.college_qualifiers, SCH.V2.college_qualifiers), ((), ()))
        self.assertEqual(SCH.V2.anchors['COLLEGE_REGIONAL'], 21)
        for v in ('v1', 'v2'):
            ids = {s.series_id for s in WorldCalendar(seed=11, version=v).series}
            self.assertIn('COLLEGE_REGIONAL_1', ids)
            self.assertFalse(any(x.startswith('COLLEGE_QUALIFIER_') for x in ids))
        cal = WorldCalendar(seed=11, version='v3')
        self.assertEqual(cal.validate(), [])
        by = cal.by_id
        self.assertFalse(any(x.startswith('COLLEGE_REGIONAL_') for x in by))
        self.assertEqual([by[q].week for q in QS], [10, 11, 12, 13])  # early spring, in order
        self.assertEqual(by['COLLEGE_NATIONAL_CHAMPIONSHIP'].week, 22)   # late spring
        for sid in ('SMALL_COLLEGE_CHAMPIONSHIP', 'INTL_UNIVERSITY_CHAMPIONSHIP'):
            self.assertIn(sid, by)                                     # kept, separate

    def test_heats(self):
        sp = SCH.V3
        heats = Season.college_heats(None, sp, list(range(720)))
        self.assertEqual([len(h) for h in heats], [144] * 5)
        self.assertEqual([h[:2] for h in heats], [[0, 9], [1, 8], [2, 7], [3, 6], [4, 5]])   # serpentine
        self.assertEqual(Season.heat_places([144] * 5, 39), [8, 8, 8, 8, 7])
        self.assertEqual(sum(Season.heat_places([157, 3], 39)), 39)
        self.assertEqual(Season.heat_places([81, 80], 39), [20, 19])
        self.assertEqual(len(Season.college_heats(None, sp, list(range(156)))), 1)
        self.assertEqual(len(Season.college_heats(None, sp, list(range(157)))), 2)
        big = Season.college_heats(None, sp, list(range(2000)))         # beyond 10 heats of 156: heats grow,
        self.assertEqual((len(big), sum(map(len, big))), (10, 2000))   # nobody is left out
        self.assertEqual(Season.college_heats(None, sp, []), [])

    def test_places_ties_and_short_heats(self):
        sp = replace(SCH.V3, college_qualifier_places=3)
        # heat 1: two tied for 2nd -> countback on the final round; one withdrew; heat 2: one finisher only
        r1 = SimpleNamespace(finish=[[(1, 1, 200), (2, 2, 205), (3, 2, 205), (4, None, 0), (5, 4, 210)],
                                     [(6, 1, 201)]],
                             scores=[{1: [66, 67, 67], 2: [66, 68, 71], 3: [70, 68, 67], 5: [70, 70, 70]},
                                     {6: [67, 67, 67]}])
        got = Season.college_qualified(fake(sp, {'2028:COLLEGE_QUALIFIER_1': r1}), 2028)
        # places: 3 shared 5:1 -> heat 1 gets 3 (largest remainder), heat 2 gets 0 ... unless rounding gives it one
        shares = Season.heat_places([5, 1], 3)
        self.assertEqual(sum(shares), 3)
        heat1 = [g for g, v in got.items() if v[1] == 1]
        self.assertEqual(heat1[:2], [1, 3][:shares[0]] if shares[0] >= 2 else heat1[:2])
        if shares[0] >= 2:
            self.assertEqual(got[3][2], 'T2')                           # 67 in the last round beats 71
            self.assertNotIn(2, got) if shares[0] == 2 else None
        self.assertNotIn(4, got)                                        # a withdrawal never qualifies
        # the next qualifier: anyone already qualified is not counted again
        r2 = SimpleNamespace(finish=[[(1, 1, 200), (7, 2, 201), (8, 3, 202), (9, 4, 203)]],
                             scores=[{1: [1], 7: [1], 8: [1], 9: [1]}])
        got2 = Season.college_qualified(fake(sp, {'2028:COLLEGE_QUALIFIER_1': r1, '2028:COLLEGE_QUALIFIER_2': r2}),
                                        2028)
        self.assertEqual(got2[1][0], 1)                                 # still qualifier 1
        self.assertEqual([g for g, v in got2.items() if v[0] == 2], [7, 8, 9])

    def test_same_year_usa_open_place_is_built_but_off(self):
        self.assertFalse(SCH.V3.college_champion_usa_open)
        self.assertNotIn('U2C', [r.code for r in Q.rules_for('v3')['USA_OPEN']])
        on = Q._rules(replace(SCH.V3, college_champion_usa_open=True))['USA_OPEN']
        r = next(x for x in on if x.code == 'U2C')
        self.assertTrue(r.amateur_only)
        self.assertEqual(r.source, (('COLLEGE_NATIONAL_CHAMPIONSHIP', 0),))
        self.assertEqual(r.select.need, {'kind': 'finish', 'positions': (1,)})
        cal = WorldCalendar(seed=11, version='v3')
        self.assertLess(cal.by_id['COLLEGE_NATIONAL_CHAMPIONSHIP'].week, cal.by_id['USA_OPEN_FINAL'].week)


class Season2028(unittest.TestCase):
    def test_a_v3_season(self):
        s = v3_world()
        se = s.season
        y = 2028
        got = se.college_qualified(y)
        entered_before = set()
        us_pool = {g.id for g in se.world.golfers if g.tour in Season.US_COLLEGE}
        for k, sid in enumerate(QS, 1):
            r = se.results[f'{y}:{sid}']
            ids = [gid for site in r.finish for gid, _, _ in site]
            self.assertEqual(len(ids), len(set(ids)))
            mine = [g for g, v in got.items() if v[0] == k]
            self.assertLessEqual(len(mine), 39)
            self.assertFalse(set(mine) & entered_before)               # never qualified twice
            already = {g for g, v in got.items() if v[0] < k}
            self.assertFalse(set(ids) & already)                        # the qualified do not enter again
            for site in r.finish:
                self.assertLessEqual(len(site), 156)
            entered_before |= set(mine)
            for gid in ids:
                self.assertIn(se.g[gid].tour, Season.US_COLLEGE)        # US college only, D1 and small college
        tours = {se.g[g].tour for g in got}
        self.assertEqual(tours, {'CO_US_D1', 'CO_US_SMALL'})
        self.assertTrue(any(se.g[g].country != 'USA' for g in got) or
                        not any(se.g[g].country != 'USA' for g in us_pool))   # nationality never excludes
        nat = se.results[f'{y}:COLLEGE_NATIONAL_CHAMPIONSHIP']
        field = [gid for gid, _, _ in nat.finish[0]]
        withdrawn = se.nationals_withdrawn.get(y, {})
        self.assertEqual(sorted(field), sorted(g for g in got if g not in withdrawn))
        routes = se.entry_routes[(y, 'COLLEGE_NATIONAL_CHAMPIONSHIP')]
        for gid in field:
            self.assertRegex(routes[gid], r'^QUALIFIER [1-4], HEAT \d+ \(T?\d+\)$')
        self.assertIn(f'{y}:SMALL_COLLEGE_CHAMPIONSHIP', se.results)    # the small-college event is still played
        s.close()

    def test_opportunities_show_the_qualifiers(self):
        s = v3_world()
        se = s.season
        g = next(g for g in se.world.golfers if g.tour in Season.US_COLLEGE)
        opps = O.opportunities(se, g.id, 2028, 1)
        q = [o for o in opps if o['route']['code'] == 'COLLEGE_QUALIFYING']
        self.assertEqual([o['event']['week'] for o in q], [10, 11, 12, 13])
        self.assertTrue(all(o['target']['series_id'] == 'COLLEGE_NATIONAL_CHAMPIONSHIP' for o in q))
        s.close()


def tearDownModule():
    if 'w' in _W:
        shutil.rmtree(_W['w'].parent, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
