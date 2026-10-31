"""Observer gaps from the requirement review: Prestige sorts both ways on every directory (missing values last
either way); a golfer's Prestige shown with its two parts (the last 52 weeks' fame and the fading legacy) where they
are recorded, and "not recorded" otherwise; My World's "first shared major" and "retirement into a staff role"
items, each recorded fact once; and each round's conditions on an edition's pages, from the recorded data (current
season and archived), "not recorded" when absent.

The Unit classes need no world (run them any time); WorldGaps builds a small world (scale 0.03).

Run from the project folder:  python -m unittest tests.test_observer_gaps -v
"""
from __future__ import annotations

import re
from collections import defaultdict
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from types import SimpleNamespace as NS                               # noqa: E402
from golfsim import prestige as PR                                    # noqa: E402
import observer as O                                                  # noqa: E402
import observer_data as OD                                            # noqa: E402
import observer_history as OH                                         # noqa: E402
import observer_myworld as MW                                         # noqa: E402
from unittest import mock                                             # noqa: E402


def text(h):
    return re.sub(r'<[^>]+>', '', h)


def column(html, i):
    """The cells of column i of the page's first table body, as text ('' for an empty cell)."""
    body = html.split('<tbody>', 1)[1].split('</tbody>', 1)[0]
    rows = re.findall(r'<tr>(.*?)</tr>', body, re.S)
    return [text(re.findall(r'<td[^>]*>(.*?)</td>', r, re.S)[i]).strip() for r in rows]


def num(v):
    return float(v) if v not in ('', None) else None


class UnitDirectorySort(unittest.TestCase):
    """directory_sort: numbers both ways, missing values last either way, ties by name then id."""

    rows = [(1, {'name': 'Bea'}, None), (2, {'name': 'Al'}, None), (3, {'name': 'Cy'}, None),
            (4, {'name': 'Di'}, None), (5, {'name': 'Ed'}, None)]
    pres = {1: 50.0, 2: None, 3: 70.5, 4: 50.0, 5: 9.0}
    values = {'reputation': lambda r: UnitDirectorySort.pres[r[0]], 'name': lambda r: r[1]['name'],
              'born': lambda r: None}

    def ids(self, sort, d):
        return [r[0] for r in O.directory_sort(self.rows, sort, d, self.values)]

    def test_prestige_descending_first_missing_last(self):
        self.assertEqual(self.ids('reputation', ''), [3, 1, 4, 5, 2])
        self.assertEqual(self.ids('reputation', 'desc'), [3, 1, 4, 5, 2])

    def test_prestige_ascending_missing_still_last(self):
        self.assertEqual(self.ids('reputation', 'asc'), [5, 1, 4, 3, 2])   # ties (Bea, Di) by name both ways

    def test_names_both_ways_and_unknown_sort(self):
        self.assertEqual(self.ids('name', ''), [2, 1, 3, 4, 5])
        self.assertEqual(self.ids('name', 'desc'), [5, 4, 3, 1, 2])
        self.assertEqual(self.ids('nonsense', 'bogus'), [2, 1, 3, 4, 5])   # (an unknown sort: by name)
        self.assertEqual(self.ids('born', 'asc'), [2, 1, 3, 4, 5])         # nothing recorded: name order


class UnitPrestigeParts(unittest.TestCase):
    """The two parts of a golfer's Prestige: shown from the running world's figures, "not recorded" without them."""

    def test_parts_from_the_running_world(self):
        fame, legacy = 123.456, 38.8
        w = NS(live=NS(people={7: {'prestige': round(PR.player_prestige(fame, legacy), 1),
                                   'prestige_parts': (fame, legacy)}}))
        self.assertEqual(OH.prestige_parts(w, 7), (fame, legacy))
        h = OH.prestige_parts_html(w, 7)
        self.assertIn(f"results {fame:.1f} fame points (alone, Prestige {PR.player_prestige(fame, 0):.1f})", h)
        self.assertIn(f"legacy {legacy:.1f} points (alone, Prestige {PR.player_prestige(0, legacy):.1f})", h)
        self.assertIn('40 points for a major', h)
        self.assertNotIn('not recorded', h)

    def test_not_recorded_without_them(self):
        for w in (NS(live=None), NS(live=NS(people={})), NS(live=NS(people={7: {'prestige': 50.0}}))):
            self.assertIsNone(OH.prestige_parts(w, 7))
            self.assertIn('not recorded', OH.prestige_parts_html(w, 7))


class FakeWorld:
    """Just enough of observer.World for My World's team items: results with the team each recorded, stints (the
    history's relations table and the snapshot's), roles and the snapshot's career decisions."""

    def __init__(self, results=(), stints=(), roles=None, transitions=None, years=(2030,), first_year=2030):
        self._results = defaultdict(list)
        for r in results:
            self._results[r['golfer']].append(r)
        self.roles = roles or {}
        rel = [NS(**d) for d in stints if d.get('archived')]
        self.a = NS(years=list(years), people={},
                    rel=NS(of_golfer=lambda g: [x for x in rel if x.golfer == g],
                           of_staff=lambda st: [x for x in rel if x.staff == st]))
        self.live = NS(first_year=first_year, stints=[dict(d) for d in stints if not d.get('archived')],
                       transitions=transitions or {}, people={})

    def results(self, pid):
        return sorted(self._results[pid], key=lambda r: (r['year'], r['week']))

    def person(self, pid):
        return {'roles': self.roles.get(pid, ['golfer'])}

    def person_link(self, pid):
        return f'<a href="/golfer/{pid}">P{pid}</a>'

    def name(self, pid):
        return f'P{pid}'

    def series_name(self, sid):
        return sid


def win(golfer, year, week, eid, coach=0, caddie=0, pos=1):
    return {'golfer': golfer, 'year': year, 'week': week, 'event': eid, 'series': eid.split(':')[1], 'pos': pos,
            'coach': coach, 'caddie': caddie, 'route': None}


def stint(i, kind, staff, golfer, start, end=None, archived=True):
    return {'id': i, 'kind': kind, 'staff': staff, 'golfer': golfer, 'start': start, 'end': end, 'arrangement': 'fee',
            'started_by': 'golfer', 'reason_start': '', 'reason_end': '', 'ended_by': None, 'terms': 0.0,
            'archived': archived}


MAJORS = {'2031:MAJ_A', '2031:MAJ_B', '2032:MAJ_A'}


def collect(fn, w, pid, start, *extra):
    out = []
    fn(w, pid, start, lambda y, wk, kind, html, eid=None, key=None: out.append((y, wk, kind, text(html), key)),
       *extra)
    return out


class UnitTeamNews(unittest.TestCase):
    """My World's first shared major and retirement into a staff role, from recorded facts only."""

    def world(self):
        results = [win(1, 2031, 15, '2031:MAJ_A', coach=10, caddie=20),
                   win(1, 2031, 20, '2031:OPEN', coach=11, caddie=20),              # not a major
                   win(1, 2031, 28, '2031:MAJ_B', coach=10, caddie=21),             # a second major with coach 10
                   win(1, 2031, 30, '2031:MAJ_C', coach=10, pos=2),                 # (not a win)
                   win(2, 2032, 15, '2032:MAJ_A', coach=12, caddie=20)]             # caddie 20's other client
        stints = [stint(1, 'coach', 10, 1, (2030, 1)), stint(2, 'caddie', 20, 1, (2029, 40), (2031, 53)),
                  stint(3, 'caddie', 21, 1, (2031, 22), archived=False), stint(4, 'caddie', 20, 2, (2032, 1),
                                                                                   archived=False),
                  stint(5, 'coach', 11, 1, (2031, 18), (2031, 25))]
        return FakeWorld(results, stints, roles={10: ['coach'], 20: ['caddie'], 21: ['caddie']},
                         years=(2030, 2031))

    def majors(self, w, pid, start=(2030, 0)):
        return collect(MW._shared_majors, w, pid, start, lambda eid: eid in MAJORS)

    def test_a_golfers_first_major_with_each_coach_and_caddie(self):
        got = self.majors(self.world(), 1)
        self.assertEqual(sorted(x[4] for x in got), sorted([('first-major', 1, 10, 'coach'),
                                                           ('first-major', 1, 20, 'caddie'),
                                                           ('first-major', 1, 21, 'caddie')]))
        by = {x[4][2]: x for x in got}
        self.assertEqual(by[10][:3], (2031, 15, 'shared major'))       # the first, never the second with coach 10
        self.assertEqual(by[21][:2], (2031, 28))
        self.assertIn('P1 won the 2031 MAJ_A with P10 as coach: their first major together', by[10][3])
        self.assertNotIn('records began', by[10][3])
        self.assertIn('since the records began', by[20][3])             # together since before the first season
        self.assertFalse(any(x[4][2] == 11 for x in got))               # coach 11 won no major with them

    def test_the_same_item_whoever_is_followed(self):
        w = self.world()
        golfer = {x[4]: x for x in self.majors(w, 1)}
        coach = self.majors(w, 10)
        self.assertEqual(coach, [golfer[('first-major', 1, 10, 'coach')]])
        caddie = {x[4]: x for x in self.majors(w, 20)}
        self.assertEqual(set(caddie), {('first-major', 1, 20, 'caddie'), ('first-major', 2, 20, 'caddie')})
        self.assertEqual(caddie[('first-major', 1, 20, 'caddie')], golfer[('first-major', 1, 20, 'caddie')])

    def test_only_inside_the_window(self):
        got = self.majors(self.world(), 1, (2031, 15))
        self.assertEqual([x[4] for x in got], [('first-major', 1, 21, 'caddie')])
        self.assertEqual(self.majors(self.world(), 1, (2032, 0)), [])

    def test_retirement_into_a_staff_role_from_the_snapshot(self):
        t = {'gid': 5, 'kind': 'became coach', 'age': 41, 'via': 'stopped chasing'}
        w = FakeWorld(roles={5: ['golfer', 'coach']}, transitions={2031: [t]}, years=(2030,))
        got = collect(MW._staff_role, w, 5, (2030, 0))
        self.assertEqual(len(got), 1)
        y, wk, kind, html, key = got[0]
        self.assertEqual((y, wk, kind, key), (2031, 52, 'staff role', ('staff-role', 5, 2031)))
        self.assertIn('P5 retired from playing after the 2031 season and became a coach at 41 (they stopped '
                      'chasing a playing career)', html)
        raw = []
        MW._staff_role(w, 5, (2030, 0), lambda *a, **k: raw.append(a[3]))
        self.assertIn('href="/golfer/5?tab=coaching"', raw[0])
        self.assertEqual(collect(MW._staff_role, w, 5, (2031, 52)), [])  # read since: not again
        nobody = FakeWorld(roles={5: ['golfer']}, transitions={2031: [t]})
        self.assertEqual(collect(MW._staff_role, nobody, 5, (2030, 0)), [])   # no staff career: nothing read

    def test_retirement_into_a_staff_role_archived_once(self):
        t = {'gid': 5, 'kind': 'became caddie', 'age': 30, 'via': 'retirement'}
        w = FakeWorld(roles={5: ['golfer', 'caddie']}, transitions={2030: [t], 2031: [{**t, 'gid': 6}]},
                      years=(2029, 2030))
        with mock.patch.object(OD, 'career_rows', lambda w_, pid: [(2029, {}), (2030, {'decisions': [t]})]):
            got = collect(MW._staff_role, w, 5, (2029, 0))
        self.assertEqual([(x[0], x[1], x[4]) for x in got], [(2030, 52, ('staff-role', 5, 2030))])
        self.assertIn('became a caddie at 30', got[0][3])
        self.assertNotIn('stopped chasing', got[0][3])
        plain = {'gid': 5, 'kind': 'retired', 'age': 30}
        with mock.patch.object(OD, 'career_rows', lambda w_, pid: [(2030, {'decisions': [plain]})]), \
                mock.patch.object(OH, 'decisions', lambda w_, pid, y: [plain]):
            self.assertEqual(collect(MW._staff_role, FakeWorld(roles={5: ['golfer', 'caddie']}), 5, (2029, 0)), [])


class UnitWinterBoundary(unittest.TestCase):
    """The review's case: a retirement into coaching decided in the winter after 2031, the world at 2032 week 1. The
    digest's "now" is 2031 week 52, and "Mark all as read" stores it: every item shown then must be read by it --
    the retirement, the staff role and a major won in week 52 -- and none returned again."""

    def world(self):
        w = FakeWorld([win(5, 2031, 52, '2031:MAJ_A', coach=10)], [stint(1, 'coach', 10, 5, (2031, 1))],
                      roles={5: ['golfer', 'coach'], 10: ['coach']}, years=(2030, 2031))
        w.live.cursor = {'year': 2032, 'week': 1}
        w.live.people = {5: {'lifestyle': 'retired', 'status': 'pro', 'tour': ''}}
        rows = [{'year': y, 'lifestyle': 'full_time', 'status': 'pro', 'tour': 'T'} for y in (2030, 2031)]
        w.a.index = NS(seasons=lambda pid: rows if pid == 5 else [])
        w.tours = lambda: {'T': {'name': 'Tour'}}
        return w

    def items(self, w, start):
        decided = [(2030, {}), (2031, {'decisions': [{'gid': 5, 'kind': 'became coach', 'age': 40,
                                                      'via': 'retirement'}]})]
        with mock.patch.object(OD, 'career_rows', lambda w_, pid: decided if pid == 5 else []):
            return (collect(MW._status_changes, w, 5, start) + collect(MW._staff_role, w, 5, start)
                    + collect(MW._shared_majors, w, 5, start, lambda eid: eid in MAJORS))

    def test_marked_read_at_week_one_reads_the_winter(self):
        w = self.world()
        seen = MW.now(w)
        self.assertEqual(seen, (2031, 52))
        shown = self.items(w, (2031, 40))                               # before marking read: all three, dated
        self.assertEqual(sorted((x[0], x[1], x[2]) for x in shown),    # no later than "now"
                         [(2031, 52, 'shared major'), (2031, 52, 'staff role'), (2031, 52, 'status')])
        self.assertIn('P5: retired after the 2031 season', [x[3] for x in shown])
        self.assertEqual(self.items(w, seen), [])                       # read: none returned again
        w.live.cursor = {'year': 2032, 'week': 9}                       # (and not later either)
        self.assertEqual(self.items(w, MW.now(w)), [])
        self.assertEqual(len(self.items(w, (2031, 51))), 3)             # the same items, the same dates


class UnitRoundConditions(unittest.TestCase):
    """Each round's wind, rain and pin difficulty as recorded; "not recorded" when absent, never estimated."""

    full = {'conditions': [[[12.3, 0, 0.45], [20.1, 1, 0.45], [7.0, 0, 0.5]], None]}

    def test_each_round_as_recorded(self):
        h = OH.conditions_line(self.full, 0)
        self.assertIn('R1 wind 12.3 mph, dry, pin difficulty 0.45', h)
        self.assertIn('R2 wind 20.1 mph, rain, pin difficulty 0.45', h)
        self.assertIn('R3 wind 7.0 mph, dry, pin difficulty 0.5', h)
        self.assertNotIn('not recorded', h)
        self.assertEqual(OH.round_conditions(self.full, 0)[1], (20.1, True, 0.45))

    def test_a_replay_shows_nothing_beyond_the_round(self):
        h = OH.conditions_line(self.full, 0, 2)
        self.assertIn('R2 wind 20.1 mph', h)
        self.assertNotIn('R3', h)

    def test_not_recorded(self):
        for full, site in ((self.full, 1), (self.full, 5), (None, 0), ({'scores': [{}]}, 0), ({'conditions': []}, 0)):
            self.assertIsNone(OH.round_conditions(full, site))
            self.assertIn('Round conditions: not recorded', OH.conditions_line(full, site))


class WorldGaps(unittest.TestCase):
    """One small world: two archived seasons and a few weeks of the third."""

    @classmethod
    def setUpClass(cls):
        from golfsim.population import generate_world
        from golfsim.session import Session
        cls.tmp = Path(tempfile.mkdtemp())
        cls.path = cls.tmp / 'w'
        s = Session.create(cls.path, seed=41, workers=1, world=generate_world(seed=41, scale=0.03))
        s.advance(2 * 52 + 6)
        s.close()
        cls.w = O.World(cls.path, workers=1)
        cls.w.reload()

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def page(self, path):
        u = urlparse(path)
        return O.render(self.w, u.path, parse_qs(u.query))[1]

    def whole(self, path, col):
        """Column `col` over every page of a directory (its whole sorted set)."""
        out, n = [], 1
        while True:
            html = self.page(f'{path}&page={n}')
            out += column(html, col)
            m = re.search(r'page (\d+) of (\d+)', html)
            if not m or int(m.group(1)) >= int(m.group(2)):
                return out
            n += 1

    # ---- 1. Prestige sorts both ways -------------------------------------------------------------------------
    def check_both_ways(self, path, col):
        down = [num(v) for v in self.whole(f'{path}?sort=reputation', col)]
        up = [num(v) for v in self.whole(f'{path}?sort=reputation&dir=asc', col)]
        known_down = [v for v in down if v is not None]
        known_up = [v for v in up if v is not None]
        self.assertTrue(known_down, path)
        self.assertEqual(known_down, sorted(known_down, reverse=True))
        self.assertEqual(known_up, sorted(known_up))
        self.assertEqual(sorted(known_up), sorted(known_down))          # the same people, the other way round
        for vals in (down, up):                                         # missing values last, in either direction
            first_missing = next((i for i, v in enumerate(vals) if v is None), len(vals))
            self.assertTrue(all(v is None for v in vals[first_missing:]), path)
        self.assertEqual(self.whole(f'{path}?sort=reputation&dir=desc', col),
                         self.whole(f'{path}?sort=reputation', col))   # (descending is the usual first direction)

    def test_golfers_prestige_both_ways(self):
        self.check_both_ways('/golfers', 6)
        html = self.page('/golfers?sort=reputation&dir=asc')
        self.assertIn('<option value="asc" selected>', html)
        self.assertIn('listed last either way', html)

    def test_coaches_and_caddies_prestige_both_ways(self):
        self.check_both_ways('/coaches', 4)
        self.check_both_ways('/caddies', 4)

    # ---- 2. Prestige with its parts ---------------------------------------------------------------------------
    def test_prestige_parts_on_the_profile(self):
        season = self.w.session.season
        lv = self.w.live
        shown = 0
        for g in sorted(p for p, x in lv.people.items() if x.get('prestige') is not None)[:40]:
            fame, legacy = lv.people[g]['prestige_parts']
            self.assertEqual((fame, legacy), (season.fame.get(g, 0.0), season.legacy.get(g, 0.0)))   # the engine's
            self.assertEqual(round(PR.player_prestige(fame, legacy), 1), lv.people[g]['prestige'])    # exactly
            html = self.page(f'/golfer/{g}')
            row = html.split('<dt>Prestige</dt><dd>', 1)[1].split('</dd>', 1)[0]
            self.assertTrue(row.startswith(f'{lv.people[g]["prestige"]} '))
            self.assertIn(f'results {fame:.1f} fame points', row)
            self.assertIn(f'legacy {legacy:.1f} points', row)
            shown += 1
        self.assertTrue(shown)
        self.assertTrue(any(season.legacy.get(g, 0) > 0 for g in lv.people))   # (some golfer has a legacy)

    def test_prestige_parts_not_recorded_in_the_history_alone(self):
        arch = O.World(self.path / 'archive', workers=1)                # the published history, no running world
        try:
            g = next(p for p, x in arch.a.people.items() if ((x.get('golfer') or {}).get('prestige')) is not None)
            row = O.render(arch, f'/golfer/{g}', {})[1].split('<dt>Prestige</dt><dd>', 1)[1].split('</dd>', 1)[0]
            self.assertIn('as the published history ends', row)
            self.assertIn('not recorded', row)
            self.assertNotIn('fame points', row)
        finally:
            arch.close()

    # ---- 3. My World: first shared major, retirement into a staff role ---------------------------------------
    def major_wins(self):
        """[(year, week, event, winner, coach, caddie)] of every major played, from the editions' recorded teams
        (the season files and the running world), oldest first."""
        w, out = self.w, []
        for eid, y, wk in w.a.index.db.execute("SELECT event_id, year, week FROM editions WHERE category = 'major' "
                                               "OR tour = 'MAJORS'"):
            e = w.edition(eid)
            for r in e['rows']:
                if r['pos'] == 1:
                    out.append((y, wk, eid, r['person']) + tuple(w.a.team_at(r['person'], eid)))
        for eid, e in w.live.editions.items():
            if e.get('category') == 'major' or e.get('tour') == 'MAJORS':
                for gid, pos, _ in (e['finish'][0] if e['finish'] else ()):
                    if pos == 1:
                        team = e['team'].get(gid) or e['team'].get(str(gid)) or (0, 0)
                        out.append((int(eid.split(':')[0]), e['week'], eid, gid) + tuple(team))
        return sorted(out)

    def follow(self, people):
        return [('person', p, '', None) for p in dict.fromkeys(people)]

    def test_first_shared_majors_each_once(self):
        wins = self.major_wins()
        want = {}
        for y, wk, eid, g, coach, caddie in wins:
            for st, role in ((coach, 'coach'), (caddie, 'caddie')):
                if st:
                    want.setdefault((g, st, role), (y, wk, eid))
        if not want:
            self.skipTest('no major won with a coach or caddie in this small world')
        people = [x for g, st, _ in want for x in (g, st)]
        got = [x for x in MW.digest(self.w, self.follow(people), (self.w.a.years[0] - 1, 0)) if x[2] == 'shared major']
        self.assertEqual(len(got), len(want))                           # one item per pair, both sides followed
        for (g, st, role), (y, wk, eid) in want.items():
            mine = [x for x in got if f'/golfer/{g}"' in x[3] and f'/golfer/{st}"' in x[3] and f' as {role}:' in x[3]]
            self.assertEqual(len(mine), 1, (g, st, role))
            self.assertEqual(mine[0][:2], (y, wk))
            self.assertIn(f'/event/{quote(eid)}"', mine[0][3])
        with mock.patch.object(O, 'shortlist', lambda w: self.follow(people)), \
                mock.patch.object(O, 'shortlist_seen', lambda w: None):
            page = O.render(self.w, '/my-world', parse_qs(f'since={self.w.a.years[0] - 1}.0'))[1]
        self.assertIn('their first major together', page)

    def test_retirement_into_a_staff_role_each_once(self):
        want = {}
        for y in self.w.a.years:
            for t in self.w.a.year(y)['transitions']:
                if t['kind'] in ('became coach', 'became caddie'):
                    want[t['gid']] = (y, t['kind'].split()[1])
        season = self.w.session.season
        for y, ts in season.transitions.items():
            if y not in self.w.a.years:
                for t in ts:
                    if t['kind'] in ('became coach', 'became caddie'):
                        want[t['gid']] = (y, t['kind'].split()[1])
        if not want:
            self.skipTest('no golfer became a coach or caddie in this small world')
        got = [x for x in MW.digest(self.w, self.follow(want), (self.w.a.years[0] - 1, 0)) if x[2] == 'staff role']
        self.assertEqual(len(got), len(want))
        for g, (y, role) in want.items():
            mine = [x for x in got if x[3].startswith(f'<a href="/golfer/{g}">')]
            self.assertEqual(len(mine), 1, g)
            self.assertEqual(mine[0][:2], (y, 52))
            self.assertIn(f'after the {y} season and became a {role}', text(mine[0][3]))
            self.assertIn(f'href="/golfer/{g}?tab={"coaching" if role == "coach" else "caddying"}"', mine[0][3])
        not_staff = [('person', g, '', None) for g, p in self.w.live.people.items()
                     if p.get('lifestyle') == 'retired' and g not in want][:20]
        self.assertFalse([x for x in MW.digest(self.w, not_staff, (self.w.a.years[0] - 1, 0)) if x[2] == 'staff role'])

    # ---- 4. Round conditions on the edition's pages ----------------------------------------------------------
    def expect(self, conds, upto=None):
        return [f'R{i} wind {wind} mph, {"rain" if rain else "dry"}, pin difficulty {pins}'
                for i, (wind, rain, pins) in enumerate(conds[:upto] if upto else conds, 1)]

    def check_edition(self, eid, conds):
        final = self.page(f'/event/{quote(eid)}')
        for line in self.expect(conds):
            self.assertIn(line, final)
        self.assertNotIn('Round conditions: not recorded', final)
        if len(conds) >= 2:                                             # the replay: rounds 1..k only
            replay = self.page(f'/event/{quote(eid)}?view=rounds&round=1')
            self.assertIn(self.expect(conds)[0], replay)
            self.assertNotIn(self.expect(conds)[1], replay)
            replay = self.page(f'/event/{quote(eid)}?view=rounds&round=2')
            for line in self.expect(conds, 2):
                self.assertIn(line, replay)

    def test_conditions_current_season(self):
        season = self.w.session.season
        eid, r = next((eid, r) for eid, r in sorted(self.w.live.editions.items())
                      if len(r.get('conditions') or ()) == 1 and r['conditions'][0])
        self.check_edition(eid, season.results[eid].conditions[0])      # as the running world recorded them

    def test_conditions_archived(self):
        y = self.w.a.years[-1]
        e = next(e for e in self.w.a.year(y)['events'] if len(e.get('conditions') or ()) == 1 and e['conditions'][0])
        self.check_edition(e['id'], e['conditions'][0])                 # as the season file recorded them

    def test_conditions_not_recorded(self):
        y = self.w.a.years[-1]
        e = next(e for e in self.w.a.year(y)['events'] if len(e.get('conditions') or ()) == 1 and e['conditions'][0])
        real = OH.full_edition
        with mock.patch.object(OH, 'full_edition', lambda w, ed: {k: v for k, v in (real(w, ed) or {}).items()
                                                                   if k != 'conditions'}):
            final = self.page(f'/event/{quote(e["id"])}')
            replay = self.page(f'/event/{quote(e["id"])}?view=rounds&round=1')
        for html in (final, replay):
            self.assertIn('Round conditions: not recorded', html)
            self.assertNotIn(' mph, ', html)
        with mock.patch.object(OH, 'full_edition', lambda w, ed: None):  # (no full record at all)
            self.assertIn('Round conditions: not recorded', self.page(f'/event/{quote(e["id"])}'))


if __name__ == '__main__':
    unittest.main()
