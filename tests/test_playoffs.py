"""Playoffs (roadmap v14, the 2035 Tour Masters review): every player in a playoff is shown, won or lost; the
number of players and extra holes is stated; each extra hole is kept from now on (sudden death: who went out
when); each site of a multi-site event keeps its own playoff; editions played before the holes were kept show
the players and result from the recorded finish and say the holes were not recorded.

Deterministic: rounds and playoff holes are scripted, so the playoffs are exactly the ones described.

Run from the project folder:  python -m unittest tests.test_playoffs -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import season as SEA                                         # noqa: E402
from golfsim import tournament as T                                       # noqa: E402
from golfsim.archive import _played                                       # noqa: E402
from golfsim.course_library import default_library                        # noqa: E402
from golfsim.engine import RoundStats                                     # noqa: E402
from golfsim.population import generate_world                             # noqa: E402
import observer_history as OH                                             # noqa: E402


def scripted(rounds, playoff):
    """play_round / play_hole stand-ins: rounds[gid] = [scores], playoff[gid] = [strokes on extra hole 1, 2...]."""
    played = {}

    def play_round(g, course, rng, cond=None, caddie=None, round_no=1, week_form=None, pressure_fn=None, pins=None):
        st = RoundStats()
        st.score = rounds[g.id][round_no - 1]
        st.holes = [4] * 17 + [st.score - 68]
        return st

    def play_hole(pl, hole, idx, rng, st, pressure=0.0, state=None, pin=None):
        gid = pl.golfer.id
        n = played.get(gid, 0)
        played[gid] = n + 1
        return playoff[gid][n]
    return play_round, play_hole


class PlayoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lib = default_library()
        cls.course = lib.course(next(v for vs in lib.venues(2027).values() for v in vs))
        cls.golfers = generate_world(seed=5, scale=0.01).golfers[:6]

    def site(self, rounds, playoff, n_rounds=2):
        ids = [g.id for g in self.golfers]
        rounds = {ids[i]: r for i, r in enumerate(rounds)}
        playoff = {ids[i]: p for i, p in enumerate(playoff)}
        pr, ph = scripted(rounds, playoff)
        task = {'event_id': '2035:TOUR_MASTERS', 'site': 0, 'course': self.course, 'golfers': list(self.golfers),
                'caddies': [None] * len(self.golfers), 'match_play': False, 'rounds': n_rounds, 'cut_top': 0,
                'prestige': 90.0, 'seed': 7}
        with mock.patch.object(T, 'play_round', pr), mock.patch.object(T, 'play_hole', ph):
            out = SEA.play_site(task)
        return ids, out

    def test_three_player_playoff_with_an_early_elimination(self):
        # A, B, C tie at 140; C goes out at the first extra hole, B at the third; D and the rest behind
        ids, out = self.site([[70, 70], [71, 69], [72, 68], [72, 72], [75, 75], [76, 76]],
                             [[4, 4, 3], [4, 4, 4], [5], [], [], []])
        A, B, C = ids[:3]
        finish = out['finish']
        self.assertEqual(out['playoff'], 3)
        self.assertEqual(finish[0][:2], (A, 1))
        self.assertEqual(sorted((g, p, t) for g, p, t in finish if t == 140), sorted([(A, 1, 140), (B, 2, 140), (C, 2, 140)]))
        ev = SEA.playoff_evidence(finish, out)
        self.assertEqual(ev['winner'], A)
        self.assertEqual(sorted(ev['players']), sorted([A, B, C]))
        self.assertEqual([n for n, h, sc in ev['holes']], [1, 2, 3])
        self.assertEqual(ev['holes'][0][2], {A: 4, B: 4, C: 5})              # all three on the first extra hole
        self.assertEqual(ev['holes'][1][2], {A: 4, B: 4})                    # C out
        self.assertEqual(ev['holes'][2][2], {A: 3, B: 4})
        self.assertEqual(ev['holes'][0][1], 18)                              # extra holes 18, 17, 18 (course holes)
        self.assertEqual(ev['holes'][1][1], 17)
        res = SimpleNamespace(scores=[{}], prizes=[{}], conditions=[None], holes=[], pars=[], golf=[], points=[],
                              matches=[[]], playoffs=[ev])
        rec = {'finish': [finish], 'playoff': out['playoff'], 'rounds': 2, **_played(res)}
        self.assertEqual(OH.playoff_status(rec, 0, A), 'Won playoff')
        self.assertEqual(OH.playoff_status(rec, 0, C), 'Lost playoff (out at extra hole 1)')
        self.assertEqual(OH.playoff_status(rec, 0, B), 'Lost playoff (out at extra hole 3)')
        self.assertEqual(OH.playoff_status(rec, 0, ids[3]), '')
        w = SimpleNamespace(person_link=lambda g: f'<a href="/golfer/{g}">{g}</a>', name=lambda g: f'G{g}')
        html = OH.playoff_lines(w, rec, 0)
        self.assertIn('3 players tied at 140', html)
        self.assertIn('3 extra holes', html)
        for g in (A, B, C):
            self.assertIn(f'/golfer/{g}"', html)

    def test_two_player_playoff_over_several_holes(self):
        ids, out = self.site([[70, 70], [70, 70], [74, 74]] + [[80, 80]] * 3,
                             [[4, 4, 4, 4], [4, 4, 4, 5]] + [[]] * 4)
        A, B = ids[:2]
        self.assertEqual(out['playoff'], 4)
        ev = SEA.playoff_evidence(out['finish'], out)
        self.assertEqual(ev['winner'], A)
        self.assertEqual(ev['players'], [A, B])
        self.assertEqual(len(ev['holes']), 4)
        self.assertTrue(all(set(sc) == {A, B} for n, h, sc in ev['holes']))

    def test_older_editions_show_the_players_but_not_the_holes(self):
        # recorded before playoff holes were kept: the finish names everyone tied, the holes are not recorded
        rec = {'finish': [[(11, 1, 283), (12, 2, 283), (13, 2, 283), (14, 4, 285)]], 'playoff': 2, 'rounds': 4}
        po = OH.playoff_at(rec, 0)
        self.assertEqual(po['players'], [11, 12, 13])
        self.assertIsNone(po['holes'])
        self.assertEqual(po['length'], 2)
        self.assertEqual(OH.playoff_status(rec, 0, 12), 'Lost playoff')
        self.assertEqual(OH.playoff_status(rec, 0, 11), 'Won playoff')
        w = SimpleNamespace(person_link=lambda g: str(g), name=lambda g: str(g))
        self.assertIn('not recorded', OH.playoff_lines(w, rec, 0))

    def test_each_site_keeps_its_own_playoff(self):
        # a two-site qualifier: a playoff at site 1 only; the old record keeps one number for the edition
        site0 = [(1, 1, 140), (2, 2, 141)]
        site1 = [(3, 1, 139), (4, 2, 139), (5, 3, 142)]
        res = SimpleNamespace(scores=[{}, {}], prizes=[{}, {}], conditions=[None, None], holes=[], pars=[], golf=[],
                              points=[], matches=[[], []],
                              playoffs=[None, {'players': [3, 4], 'winner': 3, 'holes': [[1, 18, {3: 3, 4: 4}]]}])
        rec = {'finish': [site0, site1], 'playoff': 1, **_played(res)}
        self.assertIsNone(OH.playoff_at(rec, 0))
        self.assertEqual(OH.playoff_at(rec, 1)['players'], [3, 4])
        old = {'finish': [site0, site1], 'playoff': 1}                      # before per-site evidence
        self.assertIsNone(OH.playoff_at(old, 0))
        self.assertEqual(OH.playoff_at(old, 1)['players'], [3, 4])
        self.assertIsNone(OH.playoff_at(old, 1)['length'])                  # the length is not known per site


class SeasonPlayoffs(unittest.TestCase):
    """A small world's season: every playoff's evidence agrees with the finish, prizes, points and moments."""

    def test_playoffs_reconcile_with_results_prizes_points_and_pages(self):
        import shutil
        import tempfile
        from urllib.parse import parse_qs, urlparse
        from golfsim.archive import Archive
        from golfsim.session import Session
        import observer as O
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        s = Session.create(tmp / 'w', seed=41, workers=1, world=generate_world(seed=41, scale=0.03))
        s.advance(53)
        s.close()
        with Archive(tmp / 'w' / 'archive') as a:
            d = a.year(2027)
            moments = {m['event']: m for m in d['moments'] if m['kind'] == 'playoff'}
            seen = 0
            for e in d['events']:
                for k, site in enumerate(e['finish']):
                    po = (e.get('playoffs') or [None] * len(e['finish']))[k]
                    tied = [g for g, p, t in site if t is not None and site[0][2] == t and p in (1, 2)]
                    if po is None:
                        self.assertTrue(len(tied) < 2 or e.get('match_play'), (e['id'], k))
                        continue
                    seen += 1
                    self.assertEqual(sorted(po['players']), sorted(tied), e['id'])
                    self.assertEqual(po['winner'], site[0][0])
                    self.assertGreaterEqual(len(po['holes']), 1)
                    last = po['holes'][-1][2]
                    self.assertIn(str(po['winner']), last)                  # the winner played the last extra hole
                    self.assertEqual(min(last.values()), last[str(po['winner'])])
                    losers = [g for g in po['players'] if g != po['winner']]
                    prizes = e['prizes'][k]
                    if e.get('purse'):
                        paid = {prizes.get(str(g)) for g in losers}
                        self.assertEqual(len(paid), 1, e['id'])             # tied runners-up are paid alike
                    pts = (e.get('points') or [{}] * (k + 1))[k]
                    if pts:
                        self.assertEqual(len({pts.get(str(g)) for g in losers}), 1)
                    if k == 0 and e['id'] in moments:
                        self.assertEqual(sorted(moments[e['id']]['beat']), sorted(losers))
                        self.assertEqual(moments[e['id']]['holes'], len(po['holes']))
            self.assertGreater(seen, 0)
            e = next(e for e in d['events'] if any(e.get('playoffs') or []) and len(e['finish']) == 1
                     and (e.get('rounds') or 0) >= 2)
            eid, n = e['id'], e['rounds']
        w = O.World(tmp / 'w', workers=1)
        w.reload()
        self.addCleanup(w.close)
        page = O.render(w, '/event/' + eid, {})[1]
        self.assertIn('Won playoff', page)
        self.assertIn('Lost playoff', page)
        self.assertIn('players tied', page)
        final = O.render(w, '/event/' + eid, {'view': ['rounds'], 'round': [str(n)]})[1]
        self.assertIn('Won playoff', final)
        early = O.render(w, '/event/' + eid, {'view': ['rounds'], 'round': ['1']})[1]
        self.assertNotIn('playoff', early.split('<tbody>')[1].split('</tbody>')[0].lower())


if __name__ == '__main__':
    unittest.main()
