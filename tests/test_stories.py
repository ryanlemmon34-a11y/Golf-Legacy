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
from golfsim import golfstats as GS                                   # noqa: E402

PAR = 72
NAMES = {1: 'Ada Lin', 2: 'Bo Park', 3: 'Cy Moss', 4: 'Di Vale', 5: 'Ed Roy', 6: 'Fay Orr', 7: 'Gus Hale',
         8: 'Hal Reed', 9: 'Ivy Dunn', 10: 'Jo Kerr', 11: 'Kit Ames', 12: 'Lou Penn'}


class FakeSource:
    """A history in plain data, with the WorldSource interface."""

    def __init__(self, first_year=2027):
        self.eds, self.people, self.rank, self.mom, self.extra_starts = {}, {}, {}, {}, []
        self.fy = first_year
        self.no_index = False
        self.stamps = {}
        self.pending = 0                                 # seasons the golf history is still waiting for
        for g, n in NAMES.items():
            self.people[g] = {'name': n, 'country': 'USA', 'born': 1995 + g, 'initial': False}

    # building
    def add(self, eid, scores, week=20, series='TOUR_MASTERS', tier=0, category='major', kind='major', name='Masters',
            playoff=None, finish=None, holes=None, course=('AUG', 'main'), rounds=4, golf=None):
        y = int(eid.split(':')[0])
        if finish is None:
            tot = sorted(((sum(v), g) for g, v in scores.items() if len(v) == rounds), key=lambda x: (x[0], x[1]))
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
            finish += [[g, None, None] for g, v in scores.items() if len(v) < rounds]
        e = {'id': eid, 'series': series, 'week': week, 'year': y, 'name': name, 'tour': 'MAJORS' if tier == 0 else 'PT',
             'tier': tier, 'category': category, 'kind': kind, 'rounds': rounds, 'match_play': False,
             'sites': [[course[0], course[1], 'Augusta']], 'finish': [finish],
             'scores': [{str(g): v for g, v in scores.items()}] if scores else None,
             'playoff': (len(playoff['holes']) if playoff and playoff.get('holes') else (1 if playoff else 0)),
             'playoffs': [playoff] if playoff and playoff.get('holes') is not None else None,
             'team': {}, 'origin': 'archive'}
        if not scores:
            del e['scores']
        if e['playoffs'] is None:
            del e['playoffs']
        if golf:                                         # {golfer: counters (FIELDS order)}, as a season file keeps them
            e['golf'] = [{str(g): v for g, v in golf.items()}]
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
        return {'name': next((e['name'] for e in self.eds.values() if e['series'] == sid), sid)}

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

    def golf_history(self, pid, y, wk, eid):
        out = []
        for e in self.eds.values():
            if not S.story_level(e) or e['id'] == eid or (e['year'], e['week']) >= (y, wk):
                continue
            for site in e.get('golf') or []:
                v = site.get(str(pid))
                if v:
                    c = dict(zip(GS.FIELDS, v))
                    out.append({'event': e['id'], 'year': e['year'], 'week': e['week'],
                                **{k: c[k] for k in ('rounds', 'putts', 'sg_ott', 'sg_app', 'sg_arg', 'sg_putt')}})
        return out, self.pending

    def series_results(self, sid, before=None):
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
                        'second_total': min(oth) if oth else None, 'rounds': e['rounds']})
        return out

    def ranking(self, year, week, amateur=False):
        order = self.rank.get((year, week))
        return None if order is None else {'order': order, 'year': year, 'week': week,
                                           'href': f'/rankings?kind=points&year={year}&week={week}'}

    def moments(self, eid):
        return list(self.mom.get(eid, []))

    def stamp(self, eid):
        return self.stamps.get(eid, 'archive:fixed')

    def cacheable(self, eid):
        return True


def golf_vec(rounds=4, putts=None, fir=(30, 56), gir=45, scr=(15, 27), sand=(3, 5), drives=50, dist=300.0,
             sg=(0.0, 0.0, 0.0, 0.0), strokes=None):
    """A golfer's golf-statistics counters for one edition, in the archive's order (golfstats.FIELDS, then the
    longest drive): strokes gained in hundredths, distance in tenths of a yard."""
    c = dict.fromkeys(GS.FIELDS, 0)
    c.update(rounds=rounds, holes=18 * rounds, strokes=strokes or 70 * rounds, drives=drives,
             drive_tenths=round(dist * 10 * drives), fairways=fir[0], fairway_att=fir[1], gir=gir,
             putts=putts if putts is not None else 29 * rounds, scr_made=scr[0], scr_att=scr[1], sand_saves=sand[0],
             sand_att=sand[1], sg_ott=round(sg[0] * 100), sg_app=round(sg[1] * 100), sg_arg=round(sg[2] * 100),
             sg_putt=round(sg[3] * 100))
    return [c[k] for k in GS.FIELDS] + [3105, 2, 7]


def upset_record(winner=5, p=0.00291, rank=6, field=6, favourite=2, favourite_p=0.3, overall=71.4, overall_rank=5,
                 status='pro', wr=88):
    """An edition's `upset` record in exactly the format golfsim/upsets.record archives (upset-model-1)."""
    top = sorted({favourite: favourite_p, 1: 0.2, 3: 0.1, 4: 0.09, 6: 0.05, winner: p}.items(), key=lambda x: (-x[1], x[0]))
    return {'model': 'upset-model-1', 'estimated': True, 'site': 0, 'field': field, 'rounds': 4,
            'top': [[g, q] for g, q in top[:5]], 'favourite': favourite, 'favourite_p': favourite_p,
            'favourite_overall': 84.2, 'favourite_facts': {'status': 'pro', 'age': 31, 'wr': 1, 'ar': None},
            'winner': winner, 'p': p, 'rank': rank, 'overall_rank': overall_rank, 'overall': overall,
            'winner_facts': {'status': status, 'age': 26, 'wr': wr, 'ar': 3 if status == 'amateur' else None}}


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
            self.assertTrue(s['src'] or any(not isinstance(p, str) for p in s['parts']), s)   # a claim, a link
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

    def test_upset_record_read_exactly(self):
        """The edition's `upset` record (golfsim/upsets.record, upset-model-1) is read as recorded; anything else is
        an honest omission, and no upset is claimed."""
        src = FakeSource()
        e = comeback(src)
        eid = '2031:TOUR_MASTERS'
        rec = S.assemble(src, eid)                                    # absent: played before estimates were kept
        self.assertNotIn('upset', rec['facts'])
        self.assertTrue(any('not recorded' in m and 'pre-event win estimate' in m for m in rec['missing']))
        e['upset'] = {'model': 'upset-model-1', 'estimated': False, 'why': 'match play (model 1 covers stroke play only)'}
        rec = S.assemble(src, eid)
        self.assertNotIn('upset', rec['facts'])
        self.assertTrue(any('not estimated: match play' in m for m in rec['missing']), rec['missing'])
        e['upset'] = dict(upset_record(), model='upset-model-9')       # a model this build does not know
        self.assertNotIn('upset', S.assemble(src, eid)['facts'])
        e['upset'] = upset_record(winner=3)                           # names someone else as the winner
        self.assertNotIn('upset', S.assemble(src, eid)['facts'])
        e['upset'] = upset_record()
        f = S.assemble(src, eid)['facts']['upset']
        self.assertEqual((f['model'], f['winner_p'], f['winner_rank'], f['field'], f['overall'], f['overall_rank']),
                         ('upset-model-1', 0.00291, 6, 6, 71.4, 5))
        self.assertEqual((f['favourite'], f['favourite_p'], f['favourite_overall'], f['favourite_pos']), (2, 0.3, 84.2, 2))
        self.assertEqual(f['winner_facts']['wr'], 88)
        self.assertEqual(len(f['top']), 5)
        self.assertEqual(f['src'][0][1], '/event/2031%3ATOUR_MASTERS')
        self.assertEqual((S.odds_text(0.00291), S.odds_text(0.123), S.odds_text(None)),
                         ('1 in 344', '12.3%', 'not recorded'))

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
        src.eds['2031:TOUR_MASTERS']['upset'] = upset_record(p=0.00291)
        p, tags = self.primary(src, '2031:TOUR_MASTERS')
        self.assertEqual(p, 'upset')                                  # the winner's recorded chance, under 3 %
        self.assertIn('comeback', tags)
        src.eds['2031:TOUR_MASTERS']['upset'] = upset_record(p=0.031, rank=3)
        self.assertNotIn('upset', self.primary(src, '2031:TOUR_MASTERS')[1])
        src.eds['2031:TOUR_MASTERS']['upset'] = upset_record(p=0.0299, rank=4)
        self.assertEqual(self.primary(src, '2031:TOUR_MASTERS')[0], 'upset')

    def test_playoff_upset_keeps_the_upset_context(self):
        """A playoff leads the story, but a winner with a recorded 0.291% chance still gets the chance, the favourite
        and the model -- in the story and in the sentences the Biggest Upsets page takes (those citing 'upset')."""
        src = FakeSource()
        playoff_case(src)                                             # Di Vale (4) beats Cy Moss (3) in a playoff
        src.eds['2032:TOUR_MASTERS']['upset'] = upset_record(winner=4, p=0.00291, rank=5, field=5, favourite=1,
                                                             favourite_p=0.35, overall=70.2, overall_rank=5)
        rec = S.assemble(src, '2032:TOUR_MASTERS')
        primary, tags = S.patterns(rec)
        self.assertEqual(primary, 'playoff')
        self.assertIn('upset', tags)
        st = S.narrate(rec, NAMES.get)
        texts = [s.text() for s in st['sentences']]
        self.assertIn('playoff', texts[0])
        upset = [s.text() for s in st['sentences'] if 'upset' in s.facts]
        joined = ' '.join(upset)
        self.assertIn('1 in 344', joined)
        self.assertIn('5th of 5', joined)
        self.assertIn('Ada Lin', joined)                              # the favourite, at 35.0%, and how they finished
        self.assertIn('35.0%', joined)
        self.assertIn('upset-model-1', joined)
        self.assertEqual(texts[1], upset[0])                          # straight after the playoff lead
        self.assertEqual(texts, [s.text() for s in S.narrate(S.assemble(src, '2032:TOUR_MASTERS'),
                                                             NAMES.get)['sentences']])   # deterministic

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
        src.eds['2031:TOUR_MASTERS']['upset'] = upset_record()
        t = ' '.join(self.text(src, '2031:TOUR_MASTERS'))
        self.assertIn('1 in 344', t)                                  # worded as the Biggest Upsets page words it
        self.assertIn('6th of 6', t)
        self.assertIn('Overall', t)
        self.assertIn('Bo Park', t)                                   # the favourite, and how they finished
        self.assertIn('30.0%', t)
        self.assertIn('upset-model-1', t)
        self.assertIn('world No. 88', t)                              # no ranking table: the one recorded with it

    def test_favourite_who_won(self):
        src = FakeSource()
        runaway(src)
        src.eds['2030:TOUR_MASTERS']['upset'] = upset_record(winner=1, p=0.4, rank=1, favourite=1, favourite_p=0.4)
        st = S.narrate(S.assemble(src, '2030:TOUR_MASTERS'), NAMES.get)
        self.assertNotIn('upset', st['patterns'])
        self.assertTrue(any('as the favourite, at 40.0%' in s.text() for s in st['sentences']))

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
        self.assertFalse({m for m in mods if m.startswith('golfsim')} - {'golfsim'}, mods)
        froms = {(n.module, a.name) for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) for a in n.names}
        self.assertEqual({(m, a) for m, a in froms if (m or '').startswith('golfsim')}, {('golfsim', 'golfstats')})
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


def golf_week(src, eid, putts, sg_putt, week=10, rounds=4, name='Open', golfer=1):
    """An earlier story edition (Premier) where `golfer` played every round with these putts and SG putting."""
    sc = {golfer: [70] * rounds, 2: [71] * rounds, 3: [72] * rounds}
    golf = {golfer: golf_vec(rounds=rounds, putts=putts, sg=(0.5, 0.5, 0.2, sg_putt)),
            2: golf_vec(rounds=rounds), 3: golf_vec(rounds=rounds)}
    return src.add(eid, sc, week=week, series=eid.split(':', 1)[1], tier=1, category='regular', kind='regular',
                   name=name, rounds=rounds, golf=golf)


def acceptance_case(src):
    """A synthetic reproduction of the reviewed save (fictional data): the 2041 Australia Open won by eight with 99
    putts, SG putting +7.10, 34 of 56 fairways, 41 of 72 greens, 23 of 31 scrambles, 5 of 6 sand saves; earlier
    four-round weeks with more putts but, in 2039 Fiji, better SG putting (+10.85); a three-round week with fewer
    putts (another format) and a later week (after the event) that must not count."""
    golf_week(src, '2038:PT_ONE', 110, 1.0, name='First Open')
    golf_week(src, '2039:PT_FIJI', 104, 10.85, name='Fiji Open')
    golf_week(src, '2040:PT_TWO', 101, 3.0, name='Second Open')
    golf_week(src, '2040:PT_THREE', 70, 2.0, week=12, rounds=3, name='Short Open')
    golf_week(src, '2042:PT_LATE', 95, 12.0, name='Late Open')
    scores = {1: [67, 67, 68, 68], 2: [70, 69, 70, 69]}
    golf = {1: golf_vec(putts=99, fir=(34, 56), gir=41, scr=(23, 31), sand=(5, 6), drives=52, dist=301.2,
                        sg=(3.00, 4.00, 1.50, 7.10)),
            2: golf_vec(putts=106, sg=(0.79, 1.68, 0.68, 4.45))}
    for g in range(3, 13):                               # the rest of the field, all four rounds, all behind
        scores[g] = [71, 71, 71, 71 + g]
        golf[g] = golf_vec(putts=110 + g, gir=38, sg=(0.1, 0.2, 0.1, -0.5 - g / 10))
    return src.add('2041:PT_AUS', scores, week=49, series='PT_AUS', tier=1, category='flagship', kind='regular',
                   name='Australia Open', golf=golf)


class StoryGolfTests(unittest.TestCase):
    """How the winner played, from the recorded golf statistics: figures with their denominators, strokes gained
    (engine table) against the field and the runner-up, and personal bests to that date with links to the
    earlier event -- format to format, strictly before the event, qualified for careers that began earlier."""

    def story(self, src, eid='2041:PT_AUS', **kw):
        rec = S.assemble(src, eid, **kw)
        return rec, ' '.join(s.text() for s in S.narrate(rec, NAMES.get)['sentences']), \
            S.story_data(S.narrate(rec, NAMES.get))

    def test_acceptance_example(self):
        src = FakeSource()
        acceptance_case(src)
        rec, text, st = self.story(src)
        g = rec['facts']['golf']
        self.assertEqual((g['putts'], g['fairways'], g['fairway_att'], g['gir'], g['holes'], g['scr_made'],
                          g['scr_att'], g['sand_saves'], g['sand_att']), (99, 34, 56, 41, 72, 23, 31, 5, 6))
        self.assertAlmostEqual(g['sg']['sg_putt'], 7.10)
        vs = g['vs_runner_up']
        self.assertEqual((vs['golfer'], vs['margin']), (2, 8))
        self.assertEqual(vs['parts'], {'sg_ott': 2.21, 'sg_app': 2.32, 'sg_arg': 0.82, 'sg_putt': 2.65})
        self.assertEqual((vs['sum'], vs['unaccounted']), (8.0, 0.0))
        self.assertRegex(text, r'putting \+7\.10|\+7\.10 putting')
        for want in ('99 putts (24.75 a round)', 'hit 34 of 56 fairways', '41 of 72 greens in regulation',
                     'up and down 23 times in 31 tries', '5 of 6 from greenside bunkers',
                     'the engine\'s expected-strokes table', '+2.21 off the tee', '+2.32 on approach',
                     '+0.82 around the green', '+2.65 putting', 'eight-stroke margin',
                     'lowest four-round total', 'best putting week by strokes gained was still the 2039 Fiji Open (+10.85)'):
            self.assertIn(want, text)
        self.assertNotIn('not accounted', text)
        self.assertNotIn('retained history', text)
        h = rec['facts']['golf_history']
        self.assertEqual(h['comparable'], 3)                          # 2038, 2039, 2040: four rounds, before 2041
        self.assertEqual(h['lowest_putts_before']['event'], '2040:PT_TWO')
        self.assertEqual(h['best_sg_putt_before']['event'], '2039:PT_FIJI')
        self.assertTrue(h['lowest_putts'])
        self.assertFalse(h['best_sg_putt'])
        self.assertNotIn('Late Open', text)                           # after the event: never used
        self.assertNotIn('Short Open', text)                          # three rounds: not comparable
        links = {p[1] for s in st['sentences'] for p in s['parts'] if not isinstance(p, str)}
        self.assertIn('/event/2039%3APT_FIJI?view=stats', links)      # the earlier event, linked
        self.assertIn('/rules#golf-statistics', links)
        srcs = {h_ for s in st['sentences'] for _, h_ in s['src']}
        self.assertIn('/event/2041%3APT_AUS?view=stats', srcs)        # the edition's statistics page
        self.assertIn('led in putts (fewest)', text)

    def test_retained_history_and_strict_cutoff(self):
        src = FakeSource()
        acceptance_case(src)
        src.people[1]['initial'] = True
        _, text, _ = self.story(src)
        self.assertIn('lowest four-round total among majors, Premier events and championships in the retained '
                      'history to that date', text)
        rec, text, _ = self.story(src, '2040:PT_TWO')                 # only two comparable weeks before: no claim
        self.assertEqual(rec['facts']['golf_history']['comparable'], 2)
        self.assertNotIn('to that date', text)

    def test_unaccounted_and_missing_statistics(self):
        src = FakeSource()
        e = acceptance_case(src)
        v = e['golf'][0]['2']
        v[GS.IDX['sg_putt']] += 50                                    # the parts now sum to 7.50, not 8
        _, text, _ = self.story(src)
        self.assertIn('+0.50 is not accounted for by strokes gained', text)
        del e['golf']
        rec, text, _ = self.story(src)
        self.assertTrue(any('golf statistics' in m for m in rec['missing']))
        for word in ('putts', 'fairways', 'strokes gained', 'greens in regulation'):
            self.assertNotIn(word, text)

    def test_pending_index_is_honest_and_not_kept(self):
        src = FakeSource()
        acceptance_case(src)
        src.pending = 4
        tmp = Path(tempfile.mkdtemp())
        try:
            c = S.StoryCache(tmp / 'stories.sqlite')
            rec, st = S.tell(src, '2041:PT_AUS', cache=c, names=NAMES.get)
            self.assertNotIn('golf_history', rec['facts'])
            self.assertTrue(any('4 season(s) still being indexed' in m for m in rec['missing']))
            self.assertIsNone(S.StoryCache(tmp / 'stories.sqlite').get_facts('2041:PT_AUS', None, None,
                                                                              'archive:fixed'))   # not kept on disk
            src.pending = 0
            rec, _ = S.tell(src, '2041:PT_AUS', cache=S.StoryCache(tmp / 'stories.sqlite'), names=NAMES.get)
            self.assertIn('golf_history', rec['facts'])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_perspective_golf(self):
        src = FakeSource()
        acceptance_case(src)
        _, text, _ = self.story(src, perspective=2)
        self.assertIn('Bo Park took 106 putts over four rounds; strokes gained against the engine\'s expected-strokes '
                      'table: +7.60 in all, +4.45 putting', text)


class StoryDefectTests(unittest.TestCase):
    """Fixtures for the review's defects at aafe369."""

    def test_first_professional_win_after_an_amateur_win(self):
        src = FakeSource()
        src.add('2029:AM_CUP', {7: [70] * 4, 8: [72] * 4}, series='AM_CUP', tier=6, category='national_amateur',
                kind='regular', name='Amateur Cup')
        src.add('2030:TOUR_MASTERS', {7: [70, 70, 70, 70], 8: [71, 70, 70, 70], 9: [72, 72, 72, 72]})
        rec = S.assemble(src, '2030:TOUR_MASTERS')
        self.assertEqual(rec['facts']['winner']['wins_before'], 0)
        self.assertEqual(S.patterns(rec)[0], 'first_win')
        text = ' '.join(s.text() for s in S.narrate(rec, NAMES.get)['sentences'])
        self.assertIn('on the professional tours', text)
        self.assertNotIn('recorded career', text)
        amateur = S.assemble(src, '2029:AM_CUP')
        t2 = ' '.join(s.text() for s in S.narrate(amateur, NAMES.get)['sentences'])
        self.assertIn('in amateur and college golf', t2)

    def test_history_compares_format_to_format(self):
        """A prior three-round 200 (-16 against its own 216) is not read as a four-round total."""
        src = FakeSource()
        for y, sc in ((2026, 278), (2027, 276), (2028, 274)):        # -10, -12, -14 over 72 holes
            src.add(f'{y}:TOUR_MASTERS', {1: [sc - 210, 70, 70, 70], 2: [80, 80, 80, 80]})
        src.add('2029:TOUR_MASTERS', {3: [66, 67, 67], 2: [75, 75, 75]}, rounds=3)   # 200: -16 over 54 holes
        src.add('2030:TOUR_MASTERS', {4: [67, 67, 68, 68], 2: [72, 72, 72, 72]})     # 270: -18 over 72 holes
        h = S.assemble(src, '2030:TOUR_MASTERS')['facts']['history']
        self.assertEqual((h['prior'], h['same_format'], h['other_format'], h['unknown_format']), (4, 3, 1, 0))
        self.assertEqual(h['lowest_to_par_before'], -14)
        self.assertTrue(h['lowest_to_par'])
        text = ' '.join(s.text() for s in S.narrate(S.assemble(src, '2030:TOUR_MASTERS'), NAMES.get)['sentences'])
        self.assertIn('earlier 72-hole editions (one earlier edition over another number of holes not compared)', text)
        # a format not yet indexed: no 'lowest' claim, and an honest omission
        src.series_results = lambda sid, before=None: [dict(r, rounds=None) if r['event'] == '2029:TOUR_MASTERS'
                                                       else r for r in FakeSource.series_results(src, sid)]
        rec = S.assemble(src, '2030:TOUR_MASTERS')
        self.assertFalse(rec['facts']['history']['lowest_to_par'])
        self.assertTrue(any('being indexed' in m for m in rec['missing']))

    def test_historical_ranking_links(self):
        self.assertEqual(S._order_href(True, 2031, 7), '/rankings?kind=amateur&year=2031&week=7')
        self.assertEqual(S._order_href(False, 2031, 7), '/rankings?kind=world&year=2031&week=7')

    def test_names_are_checked_when_a_story_is_reused(self):
        src = FakeSource()
        runaway(src)
        tmp = Path(tempfile.mkdtemp())
        try:
            c = S.StoryCache(tmp / 'stories.sqlite')
            _, st = S.tell(src, '2030:TOUR_MASTERS', cache=c, names=NAMES.get)
            self.assertIn('Ada Lin', S.render_sentence(st['sentences'][0], str))
            renamed = {**NAMES, 1: 'Ada Lin-Moss'}
            _, st2 = S.tell(src, '2030:TOUR_MASTERS', cache=S.StoryCache(tmp / 'stories.sqlite'), names=renamed.get)
            self.assertIn('Ada Lin-Moss', S.render_sentence(st2['sentences'][0], str))
            self.assertEqual(st2['names']['1'], 'Ada Lin-Moss')
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class StoryArchiveIndexTests(unittest.TestCase):
    """The archive path of WorldSource: an archived season is decoded once for all its stories, its story index is
    kept under the season's published signature (reused after a resume, rebuilt when the season is republished),
    and stories read through it say exactly what the season file says."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        src = self.src = FakeSource()
        runaway(src, '2030:TOUR_MASTERS', week=20)
        comeback(src, '2030:PT_OPEN')
        src.eds['2030:PT_OPEN'].update(series='PT_OPEN', tier=1, category='regular', kind='regular', name='Pine Open',
                                       week=12, id='2030:PT_OPEN', tour='PT')
        src.add('2030:PT_SMALL', {1: [70, 70, 70, 70], 2: [71, 71, 71, 71]}, series='PT_SMALL', tier=4,
                category='regular', kind='regular', name='Small Open', week=30)        # no story index entry
        src.rank[(2030, 19)] = [2, 1, 3]
        src.rank[(2030, 11)] = [1, 5]
        src.eds['2030:PT_OPEN']['upset'] = upset_record()
        season = {'events': [{**{k: v for k, v in e.items() if k not in ('year', 'origin')},
                              'team': {}, 'holes': [{'1': [[4] * 18] * 4}], 'golf': [{}]} for e in src.eds.values()],
                  'ranking_points': {'19': [[2, 9.0, 40], [1, 8.0, 40], [3, 7.0, 40]], '11': [[1, 9.0, 40], [5, 1.0, 40]]},
                  'rankings': {'world': {}, 'amateur': {}}}
        test = self

        class Arch:
            years = [2030]
            world = {'first_year': 2030, 'series': {}}
            people = {}
            index = None
            sig = 'years/2030.g1.json.gz'

            def signature(self, y):
                return self.sig

            def year(self, y):
                test.decodes += 1
                return season
        self.decodes = 0
        self.arch = Arch()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def source(self, cache):
        src, arch = self.src, self.arch
        w = type('W', (), {})()
        w.a, w.live = arch, None
        w.edition = lambda eid: {'id': eid, 'year': int(eid.split(':')[0]), 'source': 'archive'}
        w.series_info = lambda sid: {}

        class Src(S.WorldSource):                     # the index-backed reads, from the fake history
            def person(self, pid):
                return src.person(pid)

            def course(self, cid):
                return src.course(cid)

            def series(self, sid):
                return src.series(sid)

            def first_year(self):
                return 2030

            def starts(self, pid):
                return src.starts(pid)

            def series_editions(self, sid):
                return src.series_editions(sid)

            def series_results(self, sid):
                return src.series_results(sid)

            def moments(self, eid):
                return src.moments(eid)
        return Src(w, cache)

    def texts(self, src, eid, cache, **kw):
        _, st = S.tell(src, eid, cache=cache, names=NAMES.get, **kw)
        return [''.join(p if isinstance(p, str) else p[0] for p in s['parts']) for s in st['sentences']]

    def test_one_decode_per_season_and_resume(self):
        path = self.tmp / 'stories.sqlite'
        c = S.StoryCache(path)
        a = self.texts(self.source(c), '2030:TOUR_MASTERS', c)
        self.assertEqual((self.decodes, c.seasons_built), (1, 1))
        b = self.texts(self.source(c), '2030:PT_OPEN', c)
        self.assertEqual(self.decodes, 1)                              # the same season: no second decode
        # the same words as from the season's own record
        self.assertEqual(a, [s.text() for s in S.narrate(S.assemble(self.src, '2030:TOUR_MASTERS'), NAMES.get)['sentences']])
        self.assertEqual(b, [s.text() for s in S.narrate(S.assemble(self.src, '2030:PT_OPEN'), NAMES.get)['sentences']])
        self.assertTrue(any('1 in 344' in t for t in b))              # the pre-event estimate, through the index
        # a resume: a new cache over the same file; a new perspective needs new facts, and no decode
        c2 = S.StoryCache(path)
        p = self.texts(self.source(c2), '2030:PT_OPEN', c2, perspective=2)
        self.assertEqual(self.decodes, 1)
        self.assertEqual(c2.seasons_built, 0)
        self.assertTrue(p[0].startswith('Bo Park'))
        # an edition without a story level is read from the season file itself
        self.texts(self.source(c2), '2030:PT_SMALL', c2)

    def test_republished_season_is_reindexed(self):
        path = self.tmp / 'stories.sqlite'
        c = S.StoryCache(path)
        self.texts(self.source(c), '2030:TOUR_MASTERS', c)
        self.arch.sig = 'years/2030.g2.json.gz'                       # a recovery published the season again
        c2 = S.StoryCache(path)
        self.texts(self.source(c2), '2030:TOUR_MASTERS', c2)
        self.assertEqual((self.decodes, c2.seasons_built), (2, 1))

    def test_extract_is_compact(self):
        ext = S.season_extract(self.arch.year(2030))
        self.assertEqual(sorted(ext['events']), ['2030:PT_OPEN', '2030:TOUR_MASTERS'])
        for e in ext['events'].values():
            self.assertNotIn('holes', e)                              # no hole-by-hole cards
            self.assertEqual(e['golf_keys'], list(S.GOLF_KEYS))        # golf: only the counters stories read
        self.assertEqual(sorted(ext['world']), ['11', '19'])
        self.assertEqual(ext['events']['2030:PT_OPEN']['upset'], upset_record())
        self.assertNotIn('upset', ext['events']['2030:TOUR_MASTERS'])


class StoryLiveViewTests(unittest.TestCase):
    """The observer's own path (World, WorldSource, the edition page's Story tab, profiles' and My World's
    entry points) over a hand-built snapshot of a current season: no simulation, no archive."""

    def setUp(self):
        import observer as O
        from observer_live import LiveView
        self.O = O
        self.tmp = Path(tempfile.mkdtemp())
        src = FakeSource()
        runaway(src, '2030:TOUR_MASTERS', week=20)
        comeback(src, '2030:PT_OPEN')
        src.eds['2030:PT_OPEN'].update(series='PT_OPEN', tier=1, category='regular', kind='regular', name='Pine Open',
                                       week=12, id='2030:PT_OPEN', tour='PT')
        eds, by_person = {}, {}
        for eid, e in src.eds.items():
            e = {k: v for k, v in e.items() if k not in ('year', 'origin')}
            e['team'] = {1: (11, 12)} if eid == '2030:TOUR_MASTERS' else {}
            e['routes'] = {}
            eds[eid] = e
            for k, site in enumerate(e['finish']):
                for g, pos, _ in site:
                    by_person.setdefault(g, []).append((eid, k, pos))
        people = {g: {'name': n, 'country': 'USA', 'born': 1995 + g, 'status': 'pro', 'lifestyle': 'full_time',
                      'tour': 'PT', 'turned_pro': 2020, 'roles': ['golfer'], 'initial': g == 3}
                  for g, n in NAMES.items()}
        live = LiveView(cursor={'year': 2030, 'week': 30, 'phase': 'week'}, generation=7, year=2030, people=people,
                        editions=eds, by_person=by_person, schedule=[], first_year=2030,
                        series={'TOUR_MASTERS': {'name': 'Masters', 'tour': 'MAJORS', 'tier': 0, 'kind': 'major',
                                                 'category': 'major'},
                                'PT_OPEN': {'name': 'Pine Open', 'tour': 'PT', 'tier': 1, 'kind': 'regular',
                                            'category': 'regular'}},
                        courses={'AUG': {'name': 'Augusta Pines', 'layouts': {'main': {'par': 72}}}},
                        tours={'PT': {'name': 'Premier Tour', 'tier': 1}, 'MAJORS': {'name': 'Majors', 'tier': 0}},
                        rank_top={19: [[2, 9.0, 40], [1, 8.0, 40], [3, 7.0, 40]], 11: [[1, 9.0, 40], [5, 1.0, 40]]},
                        moments=[{'kind': 'hole-in-one', 'person': 1, 'event': '2030:TOUR_MASTERS', 'week': 20,
                                  'layout': 'AUG:main', 'hole': 7, 'stage': 'round 2'}],
                        records={}, wr={}, am={}, home={}, first={}, birth={}, moves={}, rules_version='2026-11-03')
        w = O.World.__new__(O.World)
        w.path = w.archive_dir = self.tmp
        w.session, w.a, w.live, w.label = None, None, live, 'test'
        self.w = w

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_story_tab_and_facts(self):
        O = self.O
        title, body = O.event(self.w, {'view': ['story']}, '2030:TOUR_MASTERS')
        self.assertIn('class="lead"', body)
        self.assertIn('Ada Lin', body)
        self.assertIn('hole-in-one at the 7th hole in round 2', body)
        self.assertIn('/rankings?kind=points&amp;year=2030&amp;week=19', body)
        self.assertIn('coached by', body)
        facts = O.event(self.w, {'view': ['story'], 'facts': ['1']}, '2030:TOUR_MASTERS')[1]
        self.assertIn('Recorded values', facts)
        final = O.event(self.w, {}, '2030:TOUR_MASTERS')[1]
        self.assertIn('Read the story', final)
        self.assertIn('view=story', final)
        # the current season's story is cached in memory only, keyed by the snapshot's generation
        cache = S.cache_for(self.w)
        self.assertTrue(any(k[0] == 'facts' and k[-1] == 'live:7' for k in cache.mem))

    def test_perspective_and_comeback_on_the_page(self):
        body = self.O.event(self.w, {'view': ['story'], 'for': ['2']}, '2030:PT_OPEN')[1]
        self.assertIn('Bo Park', body)
        self.assertIn('position after each round', body)
        self.assertIn('12 strokes', body)

    def test_entry_points(self):
        import observer_data as OD
        import observer_myworld as MW
        rows = OD.results(self.w, 1)
        sec = S.profile_section(self.w, 1, rows)
        self.assertIn('view=story', sec)
        self.assertIn('2030:TOUR_MASTERS', unquote(sec))
        dig = MW.digest(self.w, [('person', '2', '', '')], (2030, 0))
        self.assertTrue(any('for=2' in x[3] and 'story' in x[3] for x in dig), dig)   # 2nd at the Open: a story

    def test_retained_history_on_the_page(self):
        self.w.live.people[5]['initial'] = True                       # the winner was playing before the world began
        body = self.O.event(self.w, {'view': ['story']}, '2030:PT_OPEN')[1]
        self.assertIn('retained history', body)
        self.assertIn('Not in the record', body)


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
