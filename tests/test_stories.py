"""Tournament stories (roadmap T1-T3): facts carry sources, patterns follow the recorded rounds, text is
deterministic per edition and varied across editions, missing data is omitted honestly, facts are taken as of the
event (later seasons never change a story), the cache keys on (edition, perspective, fact version, narrative
version) and nothing here touches the simulation.

The unit classes use a synthetic fact source (no world, no simulation; well under a second):
    python -m unittest tests.test_stories.StoryFactTests tests.test_stories.StoryPatternTests \\
        tests.test_stories.StoryTextTests tests.test_stories.StoryCacheTests tests.test_stories.StoryIsolationTests -v
The integration class builds a small world (simulation; run it with the full suite):
    python -m unittest tests.test_stories.StoryWorldTests -v
"""
from __future__ import annotations

import ast
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
import observer_stories as S                                          # noqa: E402

PAR = 72
NAMES = {1: 'Ada Lin', 2: 'Bo Park', 3: 'Cy Moss', 4: 'Di Vale', 5: 'Ed Roy', 6: 'Fay Orr', 7: 'Gus Hale',
         8: 'Hal Reed', 9: 'Ivy Dunn', 10: 'Jo Kerr', 11: 'Kit Ames', 12: 'Lou Penn'}


class FakeSource:
    """A history in plain data, with the WorldSource interface."""

    def __init__(self, first_year=2027):
        self.eds, self.people, self.rank, self.mom, self.pre, self.extra_starts = {}, {}, {}, {}, {}, []
        self.fy = first_year
        self.no_index = False
        self.stamps = {}
        for g, n in NAMES.items():
            self.people[g] = {'name': n, 'country': 'USA', 'born': 1995 + g, 'initial': False}

    # building
    def add(self, eid, scores, week=20, series='TOUR_MASTERS', tier=0, category='major', kind='major', name='Masters',
            playoff=None, finish=None, holes=None, course=('AUG', 'main')):
        y = int(eid.split(':')[0])
        if finish is None:
            tot = sorted(((sum(v), g) for g, v in scores.items() if len(v) == 4), key=lambda x: (x[0], x[1]))
            finish, last, pos = [], None, 0
            for i, (t, g) in enumerate(tot, 1):
                if t != last:
                    pos, last = i, t
                finish.append([g, pos, t])
            if playoff:
                win = playoff['winner']
                finish.sort(key=lambda r: (r[2], r[0] != win))
                for r in finish:
                    if r[2] == finish[0][2]:
                        r[1] = 1 if r[0] == win else 2
            finish += [[g, None, None] for g, v in scores.items() if len(v) < 4]
        e = {'id': eid, 'series': series, 'week': week, 'year': y, 'name': name, 'tour': 'MAJORS' if tier == 0 else 'PT',
             'tier': tier, 'category': category, 'kind': kind, 'rounds': 4, 'match_play': False,
             'sites': [[course[0], course[1], 'Augusta']], 'finish': [finish],
             'scores': [{str(g): v for g, v in scores.items()}] if scores else None,
             'playoff': (len(playoff['holes']) if playoff and playoff.get('holes') else (1 if playoff else 0)),
             'playoffs': [playoff] if playoff and playoff.get('holes') is not None else None,
             'team': {}, 'origin': 'archive'}
        if not scores:
            del e['scores']
        if e['playoffs'] is None:
            del e['playoffs']
        self.eds[eid] = e
        return e

    # the interface
    def edition(self, eid):
        e = self.eds.get(eid)
        return None if e is None else dict(e)

    def person(self, pid):
        return dict(self.people.get(pid, {'name': f'#{pid}'}))

    def first_year(self):
        return self.fy

    def course(self, cid):
        return {'AUG': {'name': 'Augusta Pines', 'layouts': {'main': {'par': PAR}}},
                'NOPAR': {'name': 'Unrated Links', 'layouts': {}}}.get(cid, {})

    def series(self, sid):
        return {'name': sid}

    def starts(self, pid):
        out = []
        for e in self.eds.values():
            for k, site in enumerate(e['finish']):
                for g, p, t in site:
                    if g == pid:
                        out.append({'year': e['year'], 'week': e['week'], 'event': e['id'], 'series': e['series'],
                                    'name': e['name'], 'tour': e['tour'], 'tier': e['tier'], 'category': e['category'],
                                    'pos': p, 'site': k})
        out += [r for r in self.extra_starts if r.get('person') == pid]
        return sorted(out, key=lambda r: (r['year'], r['week'], r['event']))

    def series_editions(self, sid):
        return [{'event': e['id'], 'year': e['year'], 'week': e['week'],
                 'winner': next((g for g, p, _ in e['finish'][0] if p == 1), None)}
                for e in self.eds.values() if e['series'] == sid]

    def series_results(self, sid):
        if self.no_index:
            return None
        out = []
        for e in self.eds.values():
            if e['series'] != sid:
                continue
            fin = e['finish'][0]
            w = next(((g, t) for g, p, t in fin if p == 1), (None, None))
            oth = [t for g, p, t in fin if p is not None and p > 1 and t is not None]
            out.append({'event': e['id'], 'year': e['year'], 'week': e['week'], 'course': e['sites'][0][0],
                        'layout': e['sites'][0][1], 'winner': w[0], 'winner_total': w[1],
                        'second_total': min(oth) if oth else None})
        return out

    def ranking(self, year, week, amateur=False):
        order = self.rank.get((year, week))
        return None if order is None else {'order': order, 'year': year, 'week': week,
                                           'href': f'/rankings?kind=points&year={year}&week={week}'}

    def moments(self, eid):
        return list(self.mom.get(eid, []))

    def pre_event(self, eid):
        return self.pre.get(eid)

    def stamp(self, eid):
        return self.stamps.get(eid, 'archive:fixed')

    def cacheable(self, eid):
        return True


def runaway(src, eid='2030:TOUR_MASTERS', week=20):
    # golfer 1 leads after every round and wins by 6
    return src.add(eid, {1: [66, 67, 68, 69], 2: [70, 70, 69, 72], 3: [71, 70, 70, 70], 4: [72, 71, 70, 71],
                         5: [73, 72, 71, 70], 6: [74, 75]}, week=week)


def comeback(src, eid='2031:TOUR_MASTERS'):
    # golfer 5 is twelve behind after round three (2 leads), shoots 64 and wins by four
    return src.add(eid, {2: [66, 67, 66, 80], 5: [70, 70, 71, 64], 3: [69, 70, 70, 71], 4: [70, 70, 70, 71],
                         1: [72, 71, 70, 69], 6: [76, 77]})


def playoff_case(src, eid='2032:TOUR_MASTERS'):
    po = {'players': [3, 4], 'winner': 4, 'holes': [[1, 18, {'3': 4, '4': 4}], [2, 10, {'3': 5, '4': 4}]]}
    return src.add(eid, {3: [68, 69, 70, 70], 4: [70, 69, 69, 69], 1: [70, 70, 70, 70], 2: [71, 71, 70, 70],
                         5: [72, 72, 72, 72]}, playoff=po)


class StoryFactTests(unittest.TestCase):
    def test_every_fact_has_resolvable_sources(self):
        src = FakeSource()
        runaway(src)
        src.rank[(2030, 19)] = [2, 1, 3, 4]
        src.mom['2030:TOUR_MASTERS'] = [{'kind': 'course record', 'person': 1, 'event': '2030:TOUR_MASTERS',
                                          'layout': 'AUG:main', 'score': 66, 'to_par': -6, 'round': 1, 'previous': 67}]
        rec = S.assemble(src, '2030:TOUR_MASTERS')
        self.assertTrue(rec['facts'])
        for key, v in rec['facts'].items():
            for it in (v if isinstance(v, list) else [v]):
                self.assertTrue(it.get('src'), key)
                for label, href in it['src']:
                    self.assertTrue(label)
                    self.assertTrue(_resolves(src, href), (key, href))
        # sentences: every link in the prose resolves too, and every sentence names its facts or sources
        st = S.story_data(S.narrate(rec, lambda g: NAMES[g]))
        for s in st['sentences']:
            self.assertTrue(s['facts'] or s['src'], s)
            for p in s['parts']:
                if not isinstance(p, str):
                    self.assertTrue(_resolves(src, p[1]), p)
            for label, href in s['src']:
                self.assertTrue(_resolves(src, href), href)

    def test_round_facts(self):
        src = FakeSource()
        comeback(src)
        r = S.assemble(src, '2031:TOUR_MASTERS')['facts']['rounds']
        self.assertEqual(r['n'], 4)
        self.assertEqual(r['leaders'][2]['golfers'], [2])
        self.assertEqual(r['leaders'][2]['total'], 199)
        self.assertEqual(r['winner_path'][2]['behind'], 12)          # 211 vs 199
        self.assertEqual(r['behind_entering_final'], 12)
        self.assertEqual(r['took_lead'], 4)
        self.assertEqual(r['low'][3]['golfers'], [5])
        self.assertEqual(r['leaders_entering_final'][0]['golfer'], 2)

    def test_as_of_the_event(self):
        """Counts are those before the event: a later win does not change an earlier story's facts or text."""
        src = FakeSource()
        runaway(src, '2030:TOUR_MASTERS')
        a = S.assemble(src, '2030:TOUR_MASTERS')
        ta = [s.text() for s in S.narrate(a, NAMES.get)['sentences']]
        runaway(src, '2031:TOUR_MASTERS')                              # golfer 1 wins again the next year
        b = S.assemble(src, '2030:TOUR_MASTERS')
        self.assertEqual(a['digest'], b['digest'])
        self.assertEqual(ta, [s.text() for s in S.narrate(b, NAMES.get)['sentences']])
        c = S.assemble(src, '2031:TOUR_MASTERS')['facts']['winner']
        self.assertEqual((c['wins_before'], c['majors_before'], c['series_wins_before']), (1, 1, 1))
        self.assertTrue(S.assemble(src, '2031:TOUR_MASTERS')['facts']['defending']['won'])

    def test_retained_history_qualifier(self):
        src = FakeSource()
        runaway(src)
        src.people[1]['initial'] = True                               # playing before the world began
        rec = S.assemble(src, '2030:TOUR_MASTERS')
        self.assertTrue(any('retained history' in m for m in rec['missing']))
        text = ' '.join(s.text() for s in S.narrate(rec, NAMES.get)['sentences'])
        self.assertIn('retained history', text)
        self.assertNotIn('first career', text)

    def test_honest_omissions(self):
        src = FakeSource()
        src.add('2030:TOUR_MASTERS', None, finish=[[1, 1, 280], [2, 2, 282], [3, 3, 285]], course=('NOPAR', 'x'))
        src.no_index = True
        rec = S.assemble(src, '2030:TOUR_MASTERS')
        miss = ' '.join(rec['missing'])
        for what in ('round-by-round scores', 'course par', 'ranking', 'pre-event win estimate', 'earlier editions'):
            self.assertIn(what, miss)
        self.assertNotIn('rounds', rec['facts'])
        self.assertNotIn('upset', rec['facts'])
        st = S.narrate(rec, NAMES.get)
        text = ' '.join(s.text() for s in st['sentences'])
        self.assertIn('Ada Lin', text)
        self.assertIn('280', text)
        for invented in ('under par', 'round', 'No. ', 'estimate', 'putt', 'yard', 'feet', 'lucky', 'bounce'):
            self.assertNotIn(invented, text)
        self.assertNotIn('upset', st['patterns'])

    def test_pre_event_record_shapes(self):
        win = 3
        for raw in ({'winner_p': 0.012, 'favourite': 1, 'favourite_p': 0.21},
                    {'probs': {'1': 0.21, '2': 0.1, '3': 0.012}},
                    {'probabilities': {1: 21.0, 2: 10.0, 3: 1.2}}):
            got = S.normalise_pre_event(raw, win, [])
            self.assertAlmostEqual(got['winner_p'], 0.012, places=6)
            self.assertEqual(got['favourite'], 1)
        self.assertIsNone(S.normalise_pre_event({'note': 'nothing'}, win, []))
        self.assertEqual(S._pre_event_entry({'2030:X': {'p': 0.1}}, '2030:X'), {'p': 0.1})
        self.assertEqual(S._pre_event_entry([{'event': '2030:X', 'p': 0.1}], '2030:X'), {'event': '2030:X', 'p': 0.1})
        self.assertEqual(S._pre_event_entry({'events': [{'id': '2030:X', 'p': 0.2}]}, '2030:X')['p'], 0.2)
        self.assertIsNone(S._pre_event_entry({'2030:Y': {}}, '2030:X'))

    def test_story_levels(self):
        self.assertEqual(S.story_level({'kind': 'major', 'tier': 0}), 'major')
        self.assertEqual(S.story_level({'tier': 1, 'category': 'regular'}), 'premier')
        self.assertEqual(S.story_level({'tier': 3, 'category': 'circuit_championship'}), 'prestige')
        self.assertIsNone(S.story_level({'tier': 4, 'category': 'regular'}))
        self.assertIsNone(S.story_level({'tier': 1, 'category': 'q_school'}))
        self.assertTrue(S.notable({'tier': 0, 'category': 'major', 'pos': 7}))
        self.assertFalse(S.notable({'tier': 1, 'category': 'regular', 'pos': 7}))
        self.assertFalse(S.notable({'tier': 0, 'category': 'major', 'pos': None}))


class StoryPatternTests(unittest.TestCase):
    def primary(self, src, eid, **kw):
        return S.patterns(S.assemble(src, eid, **kw))

    def test_runaway_and_wire_to_wire(self):
        src = FakeSource()
        runaway(src)
        p, tags = self.primary(src, '2030:TOUR_MASTERS')
        self.assertEqual(p, 'runaway')
        self.assertIn('wire_to_wire', tags)
        self.assertIn('first_win', tags)

    def test_comeback(self):
        src = FakeSource()
        comeback(src)
        self.assertEqual(self.primary(src, '2031:TOUR_MASTERS')[0], 'comeback')

    def test_playoff(self):
        src = FakeSource()
        playoff_case(src)
        rec = S.assemble(src, '2032:TOUR_MASTERS')
        self.assertEqual(S.patterns(rec)[0], 'playoff')
        self.assertEqual(rec['facts']['playoff']['players'], [3, 4])
        self.assertEqual(rec['facts']['result']['margin'], 0)

    def test_upset_only_with_a_recorded_estimate(self):
        src = FakeSource()
        comeback(src)
        self.assertNotIn('upset', self.primary(src, '2031:TOUR_MASTERS')[1])
        src.pre['2031:TOUR_MASTERS'] = {'probs': {'2': 0.3, '1': 0.2, '3': 0.1, '4': 0.1, '5': 0.01}}
        p, tags = self.primary(src, '2031:TOUR_MASTERS')
        self.assertEqual(p, 'upset')
        self.assertIn('comeback', tags)
        src.pre['2031:TOUR_MASTERS'] = {'probs': {'2': 0.3, '5': 0.25}}
        self.assertNotIn('upset', self.primary(src, '2031:TOUR_MASTERS')[1])

    def test_first_win(self):
        src = FakeSource()
        src.add('2030:PT_OPEN', {1: [70, 70, 70, 70], 2: [71, 70, 70, 71], 3: [70, 71, 72, 70], 4: [71, 71, 71, 71]},
                series='PT_OPEN', tier=1, category='regular', kind='regular', name='Pine Open')
        src.add('2030:PT_OTHER', {2: [68, 68, 68, 68], 1: [72, 72, 72, 72]}, week=10, series='PT_OTHER', tier=1,
                category='regular', kind='regular', name='Other Open')
        rec = S.assemble(src, '2030:PT_OPEN')
        self.assertEqual(rec['facts']['winner']['wins_before'], 0)
        p, tags = S.patterns(rec)
        self.assertIn('first_win', tags)
        self.assertEqual(p, 'first_win')                              # 1 stroke, but first win leads
        rec2 = S.assemble(src, '2030:PT_OTHER')
        self.assertEqual(S.patterns(rec2)[0], 'runaway')

    def test_close_finish(self):
        src = FakeSource()
        src.add('2030:PT_OPEN', {1: [70, 70, 70, 70], 2: [69, 71, 70, 71], 3: [72, 71, 72, 70]}, series='PT_OPEN',
                tier=1, category='regular', kind='regular', name='Pine Open')
        src.extra_starts.append({'person': 1, 'year': 2029, 'week': 3, 'event': '2029:PT_X', 'series': 'PT_X',
                                 'tier': 1, 'category': 'regular', 'tour': 'PT', 'pos': 1})
        self.assertEqual(self.primary(src, '2030:PT_OPEN')[0], 'close_finish')


class StoryTextTests(unittest.TestCase):
    def text(self, src, eid, **kw):
        return [s.text() for s in S.narrate(S.assemble(src, eid, **kw), NAMES.get)['sentences']]

    def test_deterministic(self):
        src = FakeSource()
        comeback(src)
        a = self.text(src, '2031:TOUR_MASTERS')
        b = self.text(src, '2031:TOUR_MASTERS')
        self.assertEqual(a, b)
        st = S.story_data(S.narrate(S.assemble(src, '2031:TOUR_MASTERS'), NAMES.get))
        import json
        self.assertEqual(json.loads(json.dumps(st)), st)               # plain data (what the cache keeps)

    def test_variety_across_editions(self):
        """Editions of the same shape do not all open with the same words."""
        src = FakeSource()
        openings = set()
        for y in range(2030, 2042):
            eid = f'{y}:PT_E{y}'
            src.add(eid, {1: [66, 67, 68, 69], 2: [70, 70, 69, 72], 3: [71, 70, 70, 70]}, series=f'PT_E{y}', tier=1,
                    category='regular', kind='regular', name=f'Event {y}')
            first = self.text(src, eid)[0]
            openings.add(re.sub(r'\d{4} Event \d{4}|\d+', '#', first))
        self.assertGreaterEqual(len(openings), 2)

    def test_patterns_open_differently(self):
        src = FakeSource()
        runaway(src)
        comeback(src)
        playoff_case(src)
        firsts = {self.text(src, e)[0] for e in ('2030:TOUR_MASTERS', '2031:TOUR_MASTERS', '2032:TOUR_MASTERS')}
        self.assertEqual(len(firsts), 3)
        play = ' '.join(self.text(src, '2032:TOUR_MASTERS'))
        self.assertIn('playoff', play.lower())
        self.assertIn('second extra hole', play)
        cb = self.text(src, '2031:TOUR_MASTERS')
        self.assertTrue(any('12' in s or 'twelve' in s for s in cb[:1]), cb[0])

    def test_upset_text_states_the_estimate(self):
        src = FakeSource()
        comeback(src)
        src.pre['2031:TOUR_MASTERS'] = {'probs': {'2': 0.3, '1': 0.2, '3': 0.1, '4': 0.1, '5': 0.01}}
        t = ' '.join(self.text(src, '2031:TOUR_MASTERS'))
        self.assertIn('1.0%', t)
        self.assertIn('Bo Park', t)                                   # the favourite, and how they finished

    def test_perspective(self):
        src = FakeSource()
        comeback(src)
        t = self.text(src, '2031:TOUR_MASTERS', perspective=2)
        self.assertTrue(t[0].startswith('Bo Park finished 2nd') or t[0].startswith('At the'), t[0])
        self.assertTrue(any("position after each round" in s for s in t))
        same = S.assemble(src, '2031:TOUR_MASTERS', perspective=5)       # the winner's own view is the event's
        self.assertIsNone(same['perspective'])

    def test_no_generic_praise(self):
        src = FakeSource()
        for f in (runaway, comeback, playoff_case):
            f(src)
        for eid in src.eds:
            t = ' '.join(self.text(src, eid)).lower()
            for word in ('brilliant', 'stunning', 'magnificent', 'heroic', 'clutch', 'superb', 'lucky', 'bounce'):
                self.assertNotIn(word, t)


class StoryCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_cache_keys_and_reuse(self):
        src = FakeSource()
        runaway(src)
        cache = S.StoryCache(self.tmp / 'stories.sqlite')
        rec, st = S.tell(src, '2030:TOUR_MASTERS', cache=cache, names=NAMES.get)
        self.assertEqual(cache.misses, 1)
        rec2, st2 = S.tell(src, '2030:TOUR_MASTERS', cache=cache, names=NAMES.get)
        self.assertEqual(cache.hits, 1)
        self.assertEqual(st, st2)
        # a new cache object over the same file (a resume): read from disk, identical
        again = S.StoryCache(self.tmp / 'stories.sqlite')
        rec3, st3 = S.tell(src, '2030:TOUR_MASTERS', cache=again, names=NAMES.get)
        self.assertEqual(again.hits, 1)
        self.assertEqual(st3, st)
        # perspective is part of the key
        _, sp = S.tell(src, '2030:TOUR_MASTERS', perspective=2, cache=again, names=NAMES.get)
        self.assertNotEqual(sp['sentences'][0], st['sentences'][0])

    def test_stamp_and_versions_invalidate(self):
        src = FakeSource()
        runaway(src)
        cache = S.StoryCache(self.tmp / 'stories.sqlite')
        S.tell(src, '2030:TOUR_MASTERS', cache=cache, names=NAMES.get)
        src.stamps['2030:TOUR_MASTERS'] = 'archive:republished'        # a recovery republished the season
        S.tell(src, '2030:TOUR_MASTERS', cache=S.StoryCache(self.tmp / 'stories.sqlite'), names=NAMES.get)
        c = S.StoryCache(self.tmp / 'stories.sqlite')
        self.assertIsNone(c.get_facts('2030:TOUR_MASTERS', None, None, 'archive:fixed'))
        self.assertIsNotNone(c.get_facts('2030:TOUR_MASTERS', None, None, 'archive:republished'))
        old = S.FACT_VERSION
        try:
            S.FACT_VERSION = old + 1
            self.assertIsNone(S.StoryCache(self.tmp / 'stories.sqlite').get_facts('2030:TOUR_MASTERS', None, None,
                                                                                  'archive:republished'))
        finally:
            S.FACT_VERSION = old
        rec, _ = S.tell(src, '2030:TOUR_MASTERS', cache=c, names=NAMES.get)
        oldn = S.NARRATIVE_VERSION
        try:
            S.NARRATIVE_VERSION = oldn + 1
            self.assertIsNone(S.StoryCache(self.tmp / 'stories.sqlite').get_story(rec['digest']))
        finally:
            S.NARRATIVE_VERSION = oldn

    def test_later_seasons_keep_the_cached_story(self):
        """The archived edition's stamp covers its own and earlier seasons only (WorldSource.stamp): a later
        season leaves the key, and the story, as they were."""
        src = FakeSource()
        runaway(src)
        cache = S.StoryCache(self.tmp / 'stories.sqlite')
        _, st = S.tell(src, '2030:TOUR_MASTERS', cache=cache, names=NAMES.get)
        runaway(src, '2031:TOUR_MASTERS')
        _, st2 = S.tell(src, '2030:TOUR_MASTERS', cache=S.StoryCache(self.tmp / 'stories.sqlite'), names=NAMES.get)
        self.assertEqual(st, st2)

    def test_world_source_stamp_covers_earlier_seasons_only(self):
        class A:
            years = [2027, 2028, 2029]
            sigs = {2027: 'a', 2028: 'b', 2029: 'c'}

            def signature(self, y):
                return self.sigs[y]
        w = type('W', (), {})()
        w.a, w.live = A(), None
        src = S.WorldSource(w)
        s1 = src.stamp('2028:X')
        w.a.years = [2027, 2028, 2029, 2030]
        w.a.sigs[2030] = 'd'
        w.a.sigs[2029] = 'c2'
        self.assertEqual(src.stamp('2028:X'), s1)                     # later seasons: unchanged
        w.a.sigs[2027] = 'a2'
        self.assertNotEqual(src.stamp('2028:X'), s1)                  # an earlier season republished: new key
        self.assertIsNone(src.stamp('2031:X'))


class StoryIsolationTests(unittest.TestCase):
    def test_no_simulation_imports(self):
        """The stories module reads the archive through the observer; it imports nothing from the engine that
        writes state, and the engine never imports it."""
        tree = ast.parse((ROOT / 'tools' / 'observer_stories.py').read_text())
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods |= {a.name for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                mods.add(node.module or '')
        self.assertFalse({m for m in mods if m.startswith('golfsim')}, mods)
        for p in (ROOT / 'golfsim').glob('*.py'):
            self.assertNotIn('observer_stories', p.read_text(), p)


def _resolves(src, href):
    """A link the observer routes, naming something in the source."""
    u = urlparse(href)
    path = unquote(u.path)
    q = parse_qs(u.query)
    if path.startswith('/event/'):
        eid = path[len('/event/'):]
        if eid not in src.eds:
            return False
        if q.get('view') == ['rounds']:
            k = int(q['round'][0])
            return 1 <= k <= 4
        return True
    if path.startswith('/golfer/'):
        return int(path[len('/golfer/'):]) in src.people
    if path.startswith('/series/'):
        return any(e['series'] == path[len('/series/'):] for e in src.eds.values())
    if path.startswith('/course/'):
        return bool(src.course(path[len('/course/'):]))
    if path == '/rankings':
        return (int(q['year'][0]), int(q['week'][0])) in src.rank
    return path in ('/grand-slam', '/moments')


class StoryWorldTests(unittest.TestCase):
    """On a small simulated world: every story of its majors renders, and every link in it resolves in the
    observer, for the archived season and the current one. (Simulation: run with the full suite.)"""

    @classmethod
    def setUpClass(cls):
        from golfsim.population import generate_world
        from golfsim.session import Session
        import observer as O
        cls.O = O
        cls.tmp = Path(tempfile.mkdtemp())
        base = cls.tmp / 'w'
        s = Session.create(base, seed=13, workers=1, world=generate_world(seed=13, scale=0.02))
        s.advance(52 + 20)
        s.close()
        cls.w = O.World(base, workers=1)
        cls.w.reload()

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def page(self, href):
        u = urlparse(href)
        return self.O.render(self.w, u.path, parse_qs(u.query))

    def editions(self):
        w = self.w
        out = [e['id'] for _, e in w.a.events() if S.story_level(e)]
        out += [eid for eid, e in w.live.editions.items() if S.story_level(e)]
        return out

    def test_stories_render_and_links_resolve(self):
        eids = self.editions()
        self.assertTrue(any(e.startswith('2027:') for e in eids))
        self.assertTrue(any(e.startswith('2028:') for e in eids))
        seen = set()
        for eid in eids[:40]:
            title, body = self.page(S.story_href(eid))
            self.assertIn('class="lead"', body, eid)
            for href in set(re.findall(r'href="([^"]+)"', body)):
                href = href.replace('&amp;', '&')
                if href in seen or not href.startswith('/') or href.startswith('/worlds') or '#' in href:
                    continue
                seen.add(href)
                got = self.page(href)
                self.assertIsNotNone(got, href)
                self.assertNotIn('No such', got[1], href)
            facts = self.page(S.story_href(eid, facts=True))[1]
            self.assertIn('Recorded values', facts)

    def test_same_story_twice_and_after_reopen(self):
        eid = self.editions()[0]
        a = self.page(S.story_href(eid))[1]
        b = self.page(S.story_href(eid))[1]
        self.assertEqual(a, b)
        import observer as O
        w2 = O.World(self.w.path, workers=1)
        try:
            w2.reload()
            u = urlparse(S.story_href(eid))
            self.assertEqual(O.render(w2, u.path, parse_qs(u.query))[1], a)
        finally:
            w2.close()

    def test_entry_points(self):
        w = self.w
        winners = [(eid, next(r['person'] for r in w.edition(eid)['rows'] if r['pos'] == 1)) for eid in self.editions()]
        eid, pid = winners[0]
        body = self.page(f'/golfer/{pid}')[1]
        self.assertIn('view=story', body)
        self.assertIn('?view=story', self.page(f'/event/{eid}')[1])
