"""Biggest Upsets (roadmap B1/B2): the pre-event estimate model (upset-model-1), its recording in the simulation
and the archive, and the observer's Upsets page.

Quick unit tests (no world, no season): run from the project folder
    python -m unittest tests.test_upsets -v
The whole-season check that recording changes no outcome is HeavyEquivalenceTests, run only when asked:
    GOLF_HEAVY_TESTS=1 python -m unittest tests.test_upsets.HeavyEquivalenceTests -v
"""
from __future__ import annotations

import copy
import json
import math
import os
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import upsets as UP                                      # noqa: E402
from golfsim.course import ashford_ridge                               # noqa: E402
from golfsim.golfer import ARCHETYPES, archetype_golfer, uniform_golfer   # noqa: E402


def balance_field():
    """The balance report's upset-test field (tools/balance_test.py section 6), rebuilt from its seed."""
    rng = random.Random(77)
    field, names, idx = [], list(ARCHETYPES), 0
    for ov, count in [(88, 2), (84, 4), (80, 14), (77, 30), (74, 44), (71, 30), (67, 20)]:
        for _ in range(count):
            o = ov + rng.uniform(-1.5, 1.5)
            g = archetype_golfer(names[idx % len(names)], round(o, 1), name=f'P{idx:03d}')
            g.personality['big_stage'] = rng.uniform(20, 80)
            field.append(g)
            idx += 1
    return field


class ModelTests(unittest.TestCase):
    def test_version_and_sum(self):
        self.assertEqual(UP.VERSION, 'upset-model-1')
        ps = UP.win_probabilities([70, 75, 80, 60, 72.5], 4)
        self.assertAlmostEqual(sum(ps), 1.0, places=12)
        self.assertTrue(all(p > 0 for p in ps))

    def test_deterministic(self):
        rng = random.Random(3)
        ovs = [rng.uniform(40, 85) for _ in range(150)]
        a = UP.estimate(list(enumerate(ovs, 1)), 4)
        b = UP.estimate(list(enumerate(ovs, 1)), 4)
        self.assertEqual(a, b)
        # the field's order does not change anyone's chance
        rev = UP.estimate(list(reversed(list(enumerate(ovs, 1)))), 4)
        self.assertEqual(a['p'], rev['p'])

    def test_uses_no_random_numbers(self):
        state = random.getstate()
        UP.estimate([(1, 70.0), (2, 75.0), (3, 80.0)], 4)
        self.assertEqual(random.getstate(), state)

    def test_monotonic_in_overall(self):
        ps = UP.win_probabilities([60, 65, 70, 75, 80, 85], 4)
        self.assertEqual(ps, sorted(ps))

    def test_ties_share_a_chance_and_rank(self):
        pre = UP.estimate([(5, 75.0), (2, 75.0), (9, 70.0)], 4)
        self.assertEqual(pre['p'][5], pre['p'][2])
        facts = lambda g: {'status': 'pro', 'age': 30, 'wr': None, 'ar': None}
        rec = UP.record(pre, 5, facts)
        self.assertEqual(rec['rank'], 1)
        self.assertEqual(rec['favourite'], 2)                   # equal chances: the lower person id first
        self.assertEqual([g for g, _ in rec['top']], [2, 5, 9])

    def test_missing_overall_is_the_fields_lowest(self):
        a = UP.estimate([(1, 80.0), (2, None), (3, 60.0)], 4)
        b = UP.estimate([(1, 80.0), (2, 60.0), (3, 60.0)], 4)
        self.assertEqual(a['p'], b['p'])
        self.assertIsNone(a['overall'][2])
        rec = UP.record(a, 2, lambda g: {})
        self.assertEqual(rec['overall_rank'], 3)                # unknown Overall ranks last

    def test_degenerate_fields(self):
        self.assertEqual(UP.win_probabilities([], 4), [])
        self.assertEqual(UP.win_probabilities([42.0], 4), [1.0])
        self.assertFalse(UP.estimate([], 4)['estimated'])
        mp = UP.estimate([(1, 70.0), (2, 71.0)], 0, match_play=True)
        self.assertFalse(mp['estimated'])
        self.assertIn('match play', mp['why'])
        self.assertEqual(UP.record(mp, 1, lambda g: {}), {'model': UP.VERSION, 'estimated': False, 'why': mp['why']})

    def test_large_and_weak_fields(self):
        # one 75 among 155 others of 75: about 1 in 156; the same golfer against a field of 45s: a strong favourite
        big = UP.win_probabilities([75.0] * 156, 4)
        self.assertAlmostEqual(big[0], 1 / 156, delta=1e-9)
        weak = UP.win_probabilities([75.0] + [45.0] * 30, 4)
        self.assertGreater(weak[0], 0.85)
        self.assertGreater(weak[0], 100 * max(weak[1:]))
        # a 60 beating a field of 80s is a huge upset; a 60 beating 40s is not
        self.assertLess(UP.win_probabilities([60.0] + [80.0] * 40, 4)[0], 1e-4)        # (an even chance: 1 in 41)
        self.assertGreater(UP.win_probabilities([60.0] + [40.0] * 40, 4)[0], 0.3)        # (over 12 times an even share)
        # more rounds favour the better golfer
        self.assertGreater(UP.win_probabilities([80.0, 75.0], 4)[0], UP.win_probabilities([80.0, 75.0], 1)[0])
        # very small chances stay representable (an extreme upset is ranked, not lost as zero)
        tiny = UP.win_probabilities([20.0] + [85.0] * 100, 4)[0]
        self.assertGreater(tiny, 0.0)
        self.assertLess(tiny, 1e-12)

    def test_calibration_against_the_balance_report(self):
        """Model 1 against the engine's measured upset test (reports/BALANCE_REPORT.md section 6): per-start win
        chances by Overall band within a factor that allows for its sampling noise."""
        field = balance_field()
        ovs = [g.overall for g in field]
        ps = UP.win_probabilities(ovs, 4)
        measured = {(86, 100): 0.1545, (82, 86): 0.0430, (78, 82): 0.0123, (75, 78): 0.0046, (72, 75): 0.0020}
        for (lo, hi), m in measured.items():
            got = [p for o, p in zip(ovs, ps) if lo <= o < hi]
            mean = sum(got) / len(got)
            self.assertLess(abs(math.log(mean / m)), math.log(1.25), (lo, hi, mean, m))

    def test_odds_text(self):
        self.assertEqual(UP.odds_text(0.123), '12.3%')
        self.assertEqual(UP.odds_text(0.0004), '1 in 2,500')
        self.assertEqual(UP.odds_text(None), 'not recorded')


class NoHindsightTests(unittest.TestCase):
    def test_record_leaves_the_estimate_unchanged(self):
        pre = UP.estimate([(1, 80.0), (2, 70.0), (3, 65.0)], 4)
        before = copy.deepcopy(pre)
        rec = UP.record(pre, 3, lambda g: {'status': 'amateur', 'age': 19, 'wr': None, 'ar': 4})
        self.assertEqual(pre, before)
        self.assertEqual(rec['p'], pre['p'][3])
        self.assertEqual(rec['rank'], 3)
        self.assertEqual(rec['winner_facts']['status'], 'amateur')
        # the same estimate whoever wins: only the lookup differs
        self.assertEqual(UP.record(pre, 1, lambda g: {})['top'], rec['top'])

    def test_every_stored_chance_is_reproduced_from_the_snapshot_alone(self):
        rng = random.Random(11)
        for n, rounds in ((156, 4), (80, 3), (30, 2), (6, 4)):
            field = [(rng.randrange(1000, 60000), rng.gauss(62, 12)) for _ in range(n)]
            field[5] = (field[5][0], None)                              # an unknown Overall travels as None
            winner = field[n // 2][0]
            rec = UP.record(UP.estimate(field, rounds), winner, lambda g: {'status': 'pro', 'age': 30, 'wr': None})
            rec = json.loads(json.dumps(rec))                           # as archived (JSON)
            self.assertEqual(sorted(rec['inputs']), ['ids', 'overall'])  # ids and Overall only: nothing hidden
            self.assertEqual(rec['inputs']['ids'], [g for g, _ in field])
            self.assertTrue(all(o is None or o == round(o, UP.OVERALL_DECIMALS) for o in rec['inputs']['overall']))
            again = UP.reproduce(rec)                                    # from model, rounds and inputs alone
            self.assertEqual(again[rec['winner']], rec['p'])
            self.assertEqual(again[rec['favourite']], rec['favourite_p'])
            self.assertEqual([[g, again[g]] for g, _ in rec['top']], rec['top'])
            self.assertEqual(rec['rank'], 1 + sum(1 for p in again.values() if p > rec['p']))
        with self.assertRaises(ValueError):
            UP.reproduce({'model': 'upset-model-0', 'estimated': True, 'rounds': 4})

    def test_snapshot_size_per_edition(self):
        """Archive growth (docs/HISTORY_AND_PERSISTENCE.md): about 11 bytes per entrant for the snapshot and about
        450 bytes for the rest of the record (uncompressed JSON; ids up to five digits, Overall to one decimal)."""
        rng = random.Random(2)
        for n in (30, 80, 156):
            field = [(rng.randrange(10000, 60000), rng.gauss(62, 12)) for _ in range(n)]
            rec = UP.record(UP.estimate(field, 4), field[3][0], lambda g: {'status': 'pro', 'age': 31, 'wr': 412,
                                                                          'ar': None})
            inputs = len(json.dumps(rec['inputs'], separators=(',', ':')))
            whole = len(json.dumps(rec, separators=(',', ':')))
            self.assertLessEqual(inputs, 12 * n + 30, n)
            self.assertLessEqual(whole - inputs, 500, n)

    def test_play_site_estimate_is_made_before_play_and_changes_nothing(self):
        """The worker's estimate is computed from the field before any shot, uses no random numbers and leaves
        the result exactly as without it (a tiny one-round event: a unit test, not a simulation run)."""
        from golfsim.season import play_site
        golfers = []
        for i, ov in enumerate((80, 74, 68, 62), 1):
            g = uniform_golfer(ov, name=f'G{i}')
            g.id = i
            golfers.append(g)
        task = {'event_id': '2027:TEST', 'site': 0, 'course': ashford_ridge(), 'golfers': golfers,
                'match_play': False, 'caddies': [], 'rounds': 1, 'cut_top': 0, 'prestige': 50, 'seed': 12345}
        ratings = [dict(g.attrs) for g in golfers]
        off = play_site(dict(task, estimate=False))
        on = play_site(dict(task, estimate=True))
        est = on.pop('estimate')
        self.assertNotIn('estimate', off)
        self.assertEqual(json.dumps(on, sort_keys=True, default=str), json.dumps(off, sort_keys=True, default=str))
        self.assertEqual(est, UP.estimate([(g.id, g.overall) for g in golfers], 1))
        self.assertEqual([dict(g.attrs) for g in golfers], ratings)
        self.assertEqual(est['rounds'], 1)


def _edition(eid, week, tier, field, winner, rounds=4, kind='pro', category='regular', tour='PT_AMERICAS',
             recorded=True, playoff=0, scores=None, facts=None, match_play=False):
    """An edition record (archive.edition_record form) with, when `recorded`, its pre-event estimate."""
    totals = {g: 280 + i for i, (g, _) in enumerate(field)}
    totals[winner] = 270 if not playoff else 279
    order = sorted(totals, key=lambda g: (totals[g], g != winner))
    finish = [[(g, 1 if g == winner else 2 + i, None if match_play else totals[g]) for i, g in enumerate(order)]]
    e = {'id': eid, 'series': eid.split(':')[1], 'week': week, 'name': eid.split(':')[1].title(), 'tour': tour,
         'tier': tier, 'kind': kind, 'category': category, 'rounds': rounds, 'match_play': match_play,
         'playoff': playoff, 'finish': finish, 'sites': [['c1', 'L1', 'City']]}
    if scores:
        e['scores'] = [scores]
    if recorded:
        pre = UP.estimate(field, rounds, match_play)
        f = facts or {}
        e['upset'] = UP.record(pre, winner, lambda g: f.get(g, {'status': 'pro', 'age': 30, 'wr': g, 'ar': None}))
    return e


FIELD = [(1, 85.0), (2, 80.0), (3, 75.0), (4, 70.0), (5, 65.0), (6, 60.0)]


def season_events():
    y30 = [_edition('2030:OLD_MAJOR', 10, 0, FIELD, 6, kind='major', category='major', tour='MAJORS', recorded=False),
           _edition('2030:OLD_EVENT', 12, 2, FIELD, 5, recorded=False)]
    am = {4: {'status': 'amateur', 'age': 19, 'wr': None, 'ar': 3}}
    y31 = [_edition('2031:MAJOR_A', 14, 0, FIELD, 5, kind='major', category='major', tour='MAJORS'),
           _edition('2031:PREMIER_B', 15, 1, FIELD, 4, facts=am, playoff=2),
           _edition('2031:REGIONAL_C', 16, 3, FIELD, 6, scores={'6': [72, 70, 69, 59], '1': [66, 66, 66, 75],
                                                                 '2': [70, 70, 70, 70]}),
           _edition('2031:REGIONAL_D', 16, 3, FIELD, 6),               # the same field and winner: an equal chance
           _edition('2031:FAVOURITE_E', 17, 2, FIELD, 1),
           _edition('2031:MATCH_F', 18, 6, FIELD, 2, match_play=True, kind='amateur'),
           _edition('2031:QUAL_G', 18, 7, FIELD, 6, kind='qualifying', category='qualifier')]
    return {2030: y30, 2031: y31}


class FakeWorld:
    """What the Upsets page reads of a world: the statistics store, people, names and tours."""

    def __init__(self, db, people, live=None, years=(2030, 2031)):
        from types import SimpleNamespace
        self.db = db
        self.a = SimpleNamespace(years=list(years), people=people)
        self.live = live

    def statistics(self):
        return self.db, None

    def person(self, pid):
        return self.a.people.get(pid)

    def person_link(self, pid):
        import observer as O
        return f'<a href="/golfer/{pid}">{O.esc(self.a.people[pid]["name"])}</a>' if pid else '-'

    def series_name(self, sid):
        return sid.title()

    def tours(self):
        return {'PT_AMERICAS': {'name': 'Premier Tour Americas'}, 'MAJORS': {'name': 'Majors'}}


def _q(**q):
    return {k: [str(v)] for k, v in q.items()}


class PageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        import observer_stats as ST
        cls.tmp = Path(tempfile.mkdtemp())
        store = ST.StatsStore(cls.tmp / 's.sqlite')
        cls.events = season_events()
        for y, evs in cls.events.items():
            store.put(y, str(y), {}, {}, {}, {}, upsets=ST.upset_rows(evs, y))
        cls.store = store
        people = {g: {'name': f'Golfer {g}', 'country': 'USA' if g % 2 else 'ENG', 'born': 2012 - g,
                      'golfer': {'status': 'pro'}} for g in range(1, 7)}
        people[6]['initial'] = True
        cls.w = FakeWorld(store.db, people)

    @classmethod
    def tearDownClass(cls):
        import shutil
        cls.store.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def page(self, **q):
        import observer_upsets as OU
        return OU.page(self.w, _q(**q))[1]

    def ranked_ids(self, **q):
        import observer_upsets as OU
        rows, _ = OU.rows_for(self.w)
        chosen = OU.select(self.w, rows, _q(**q))
        return [r['event_id'] for r in sorted((r for r in chosen if r['p'] is not None), key=OU.rank_key)]

    def test_rows_from_the_record(self):
        import observer_stats as ST
        rows = {r[2]: r for r in ST.upset_rows(self.events[2031], 2031)}
        self.assertNotIn('2031:QUAL_G', rows)                          # qualifying stages are not listed
        c = rows['2031:REGIONAL_C']
        self.assertEqual(c[16], 13)                                    # 211 after three rounds, the leader 198
        self.assertEqual(c[14], 10)                                    # margin: kept apart from the estimate
        self.assertIsNone(rows['2031:MATCH_F'][10])                    # match play: not estimated
        self.assertEqual(rows['2031:MATCH_F'][9], UP.VERSION)
        old = ST.upset_rows(self.events[2030], 2030)
        self.assertTrue(all(r[9] is None and r[10] is None and r[19] is None for r in old))   # not recorded

    def test_ranking_lowest_chance_first_with_stable_ties(self):
        ids = self.ranked_ids()
        self.assertEqual(ids[:2], ['2031:REGIONAL_C', '2031:REGIONAL_D'])   # equal chances: by date, then id
        self.assertEqual(ids[-1], '2031:FAVOURITE_E')
        self.assertNotIn('2031:MATCH_F', ids)
        self.assertFalse(any(i.startswith('2030') for i in ids))       # B2: nothing reconstructed
        self.assertEqual(ids, self.ranked_ids())                        # the same inputs, the same ranking

    def test_tied_chances_share_a_rank(self):
        import observer_upsets as OU
        rows = [{'p': p, 'year': 2031, 'week': wk, 'event_id': f'2031:E{wk}'}
                for p, wk in ((0.01, 1), (0.02, 3), (0.02, 2), (0.03, 4), (0.04, 5), (0.04, 6), (0.04, 7))]
        ranked = sorted(rows, key=OU.rank_key)
        self.assertEqual([r['event_id'] for r in ranked][1:3], ['2031:E2', '2031:E3'])   # tied: by date
        self.assertEqual(OU.competition_ranks(ranked), [(1, False), (2, True), (2, True), (4, False), (5, True),
                                                        (5, True), (5, True)])
        # on the page: the fixture's two equal chances are both ranked 1 and marked tied; the next row is 3rd
        html = self.page()
        cells = [c.split('</td>')[0] for c in html.split('<tr><td class=n>')[1:]]
        self.assertEqual([c.split(' ')[0] for c in cells], ['1', '1', '3', '4', '5'])
        self.assertEqual(sum('tied</span>' in c for c in cells), 2)
        self.assertIn('Equal chances share a rank (competition ranking: 1, 2, 2, 4)', html)
        self.assertIn('not calibrated betting odds', html)
        self.assertIn('leaves out form, course fit', html)

    def test_drama_never_enters_the_ranking(self):
        import observer_upsets as OU
        rows, _ = OU.rows_for(self.w)
        a = [r['event_id'] for r in sorted((r for r in rows if r['p'] is not None), key=OU.rank_key)]
        for r in rows:
            r['margin'], r['playoff'], r['back'] = 99, 5, 20
        b = [r['event_id'] for r in sorted((r for r in rows if r['p'] is not None), key=OU.rank_key)]
        self.assertEqual(a, b)

    def test_majors_only_and_filters(self):
        self.assertEqual(self.ranked_ids(scope='major'), ['2031:MAJOR_A'])
        self.assertEqual(set(self.ranked_ids(level=3)), {'2031:REGIONAL_C', '2031:REGIONAL_D'})
        self.assertEqual(self.ranked_ids(**{'from': 2032}), [])
        self.assertEqual(len(self.ranked_ids(to=2031)), 5)
        self.assertEqual(self.ranked_ids(nation='ENG'), ['2031:REGIONAL_C', '2031:REGIONAL_D', '2031:PREMIER_B'])
        self.assertEqual(self.ranked_ids(event='premier'), ['2031:PREMIER_B'])
        self.assertEqual(self.ranked_ids(series='MAJOR_A'), ['2031:MAJOR_A'])
        self.assertEqual(self.ranked_ids(field=100), [])
        html = self.page(scope='major')
        self.assertIn('aria-pressed="true">Majors only', html)

    def test_status_and_age_at_the_event(self):
        # golfer 4 is a professional now; they won 2031:PREMIER_B as a 19-year-old amateur
        self.assertEqual(self.ranked_ids(status='amateur'), ['2031:PREMIER_B'])
        html = self.page(status='amateur')
        self.assertIn('19* · amateur', html)
        self.assertIn('amateur No. 3', html)
        self.assertIn('amateur winner', html)

    def test_entries_link_to_the_result_and_the_golfer_and_explain(self):
        import observer as O
        html = self.page()
        self.assertIn('href="/event/2031%3AREGIONAL_C"', html)
        self.assertIn('href="/golfer/6"', html)
        self.assertIn('/golfer/6?tab=results&year=2031', html)
        self.assertIn('6th of 6 by Overall', html)
        self.assertIn('favourite <a href="/golfer/1">', html)
        self.assertIn('came from 13 back', html)
        self.assertIn('playoff (2 extra holes)', html)
        self.assertEqual(O.PAGES['/upsets'].__module__, 'observer_upsets')

    def test_first_win_counts_unrecorded_editions_too(self):
        import observer_upsets as OU
        rows, _ = OU.rows_for(self.w)
        first = OU.first_wins(rows)
        self.assertTrue(first['2030:OLD_MAJOR'])                       # golfer 6's first win (2030, not recorded)
        self.assertFalse(first['2031:REGIONAL_C'])
        self.assertTrue(first['2031:PREMIER_B'])

    def test_b2_unrecorded_seasons_say_so(self):
        import observer_upsets as OU
        html = self.page(to=2030)
        self.assertIn('2 not recorded', html)
        self.assertIn('No winner with a recorded estimate matches', html)
        self.assertIn('not calibrated win probabilities', html)
        old = OU.event_panel(self.w, self.events[2030][0])
        self.assertIn('not recorded', old)
        self.assertNotIn('%', old)
        panel = OU.event_panel(self.w, self.events[2031][0])
        self.assertIn('Pre-event estimate', panel)
        self.assertIn(UP.VERSION, panel)
        self.assertIn('not estimated', OU.event_panel(self.w, self.events[2031][5]))
        self.assertEqual(OU.event_panel(self.w, self.events[2031][6]), '')   # a qualifying stage: nothing

    def test_live_season_rows(self):
        from types import SimpleNamespace
        import observer_upsets as OU
        live = SimpleNamespace(cursor={'year': 2032, 'week': 3},
                               editions={'2032:LIVE': _edition('2032:LIVE', 2, 2, FIELD, 3)})
        rows, _ = OU.rows_for(FakeWorld(self.w.db, self.w.a.people, live=live))
        self.assertIn('2032:LIVE', {r['event_id'] for r in rows})


@unittest.skipUnless(os.environ.get('GOLF_HEAVY_TESTS') == '1', 'whole-season run: set GOLF_HEAVY_TESTS=1')
class HeavyEquivalenceTests(unittest.TestCase):
    """Same seed, recording on and off: every outcome identical (results, statistics, rankings, money, records)."""

    def test_recording_changes_no_outcome(self):
        from golfsim.population import generate_world
        from golfsim.season import Season
        import equivalence_check as EQ
        weeks = int(os.environ.get('GOLF_HEAVY_WEEKS', '8'))

        def run(on):
            s = Season(generate_world(seed=2027), seed=2027, workers=2)
            s.upset_estimates = on
            eds = s.cal.editions(2027)
            for w in range(1, weeks + 1):
                s.run_week(2027, w, [e for e in eds if e.week == w])
            s.close()
            return s

        a, b = run(True), run(False)
        self.assertEqual([(e, r.finish, r.playoff) for e, r in sorted(a.results.items())],
                         [(e, r.finish, r.playoff) for e, r in sorted(b.results.items())])
        for part in ('pstats', 'records', 'moments', 'history', 'wr_pos', 'am_pos', 'ledgers'):
            x, y = getattr(a, part), getattr(b, part)
            x, y = (x.to_dict(), y.to_dict()) if hasattr(x, 'to_dict') else (x, y)
            self.assertEqual(EQ.digest(EQ.canon(x)), EQ.digest(EQ.canon(y)), part)
        self.assertEqual([(g.id, sorted(g.attrs.items()), g.cash) for g in a.world.golfers],
                         [(g.id, sorted(g.attrs.items()), g.cash) for g in b.world.golfers])
        got = [r.upset for r in a.results.values() if r.upset and r.upset.get('estimated')]
        self.assertTrue(got)
        self.assertTrue(all(r.upset is None for r in b.results.values()))


if __name__ == '__main__':
    unittest.main()
