"""Biggest Upsets (roadmap B2, open item O9): the audited historical upset examples as regression and presentation
fixtures for editions that have no pre-event estimate.

Source of the examples: the owner's expanded roadmap (Golf_Legacy_Expanded_World_Roadmap_2026-10-30, section 9, B2
"Preserve the stories without forcing the answer") and its audit register N09 (Chris Jefferson). They come from the
audited archive (completed seasons 2027-2083), played long before upset-model-1 recorded any estimate, so every one
of them has no `upset` record. What those documents state is used as data (event, year, winner, and for Jefferson
his status, age, 72-hole total of 280 and two-hole playoff; for Carroll, that Harper was in the field and finished
behind him). Everything else is a labelled placeholder: the other entrants, the weeks, the 2038 major's name (the
audit does not name it), the year of Carroll's France event (not stated) and Harper's place. No chance, odds, rank
by a model or Overall is attached to any of them: the earlier retrospective screen was not calibrated win
probabilities and is never turned into odds here.

What is locked in: the statistics rows carry no model and no chance; the Biggest Upsets page leaves these editions
out of the ranked list and counts them as "not recorded" (all events and majors only); the edition's estimate panel
says "not recorded"; the story names the missing estimate among what is not in the record and claims no upset; a
"not estimated" record shows its recorded reason (or says no reason was recorded); and nothing is worked out
afterwards (the model's functions are made to fail while all of this is rendered).

Quick unit tests (no world, nothing simulated; well under a second):
    python -m unittest tests.test_upset_examples -v
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tests'))
from golfsim import upsets as UP                                      # noqa: E402
import test_upsets as TU                                              # noqa: E402  (the Upsets page fixture)

HARPER = 200                                                          # Barnaby Harper
# The audited examples. 'facts' are the documents' words; 'synthetic' names what the fixture had to make up.
EXAMPLES = (
    {'eid': '2041:AUSTRALIA_OPEN', 'name': 'Australia Open', 'tier': 1, 'major': False, 'winner': 101,
     'winner_name': 'Jack Ashcroft', 'week': 49, 'facts': 'Jack Ashcroft, 2041 Australia Open: a strong candidate',
     'synthetic': 'week (the current calendar\'s), the other entrants'},
    {'eid': '2035:USA_OPEN', 'name': 'USA Open', 'tier': 0, 'major': True, 'winner': 102,
     'winner_name': 'Reed Slater', 'week': 24, 'facts': 'Reed Slater, 2035 USA Open: a strong candidate',
     'synthetic': 'week, the other entrants'},
    {'eid': '2042:BRITANNIA_OPEN', 'name': 'Britannia Open', 'tier': 0, 'major': True, 'winner': 103,
     'winner_name': 'Gordon Kinnear', 'week': 28, 'facts': 'Gordon Kinnear, 2042 Britannia: a different kind of surprise',
     'synthetic': 'week, the other entrants'},
    {'eid': '2034:TOUR_MASTERS', 'name': 'Masters', 'tier': 0, 'major': True, 'winner': 104,
     'winner_name': 'Chris Jefferson', 'week': 15, 'total': 280, 'playoff': 2, 'status': 'amateur', 'born': 2015,
     'facts': 'Chris Jefferson, 2034 Tour Masters (N09): 19, amateur (M16 from his 2033 college national title), all '
              'pre-event top 50 entered, shot 280 and won a two-hole playoff; closest prior recorded Overall 75.1 '
              '(77.6 is next winter, not event time)',
     'synthetic': 'week, the runner-up (tied at 280) and the other entrants, birth year from his age'},
    {'eid': '2038:MAJOR_NOT_NAMED', 'name': 'Major (not named in the audit)', 'tier': 0, 'major': True, 'winner': 105,
     'winner_name': 'Stewart Ellison', 'week': 30, 'facts': 'Stewart Ellison, a 2038 major: a different kind of surprise',
     'synthetic': 'which major (not named), week, the other entrants'},
    {'eid': '2068:USA_OPEN', 'name': 'USA Open', 'tier': 0, 'major': True, 'winner': 106,
     'winner_name': 'Sebastian Egger', 'week': 24, 'facts': 'Sebastian Egger, 2068 USA Open: a different kind of surprise',
     'synthetic': 'week, the other entrants'},
    {'eid': '2050:FRANCE_OPEN', 'name': 'France Open', 'tier': 1, 'major': False, 'winner': 107,
     'winner_name': 'Aidan Carroll', 'week': 39, 'beaten': HARPER,
     'facts': 'Aidan Carroll beating Harper in France: one famous opponent is not an exceptionally strong whole field',
     'synthetic': 'the year (not stated), week, Harper\'s place behind Carroll, the other entrants'},
)
LEGACY = {'eid': '2030:LEGACY_EVENT', 'name': 'Legacy Event', 'tier': 3, 'major': False, 'winner': 108,
          'winner_name': 'Legacy Winner', 'week': 12, 'facts': 'a generic edition played before estimates were kept',
          'synthetic': 'everything'}
CASES = EXAMPLES + (LEGACY,)
PLACEHOLDERS = (901, 902, 903)                                        # 'Field golfer N (synthetic)'
FIRST_ESTIMATED = 2084                                                # a synthetic season with recorded estimates


def people():
    out = {c['winner']: {'name': c['winner_name'], 'country': 'USA', 'born': c.get('born', 2000), 'initial': False,
                         'golfer': {'status': 'pro'}} for c in CASES}
    out[HARPER] = {'name': 'Barnaby Harper', 'country': 'ENG', 'born': 2028, 'initial': False, 'golfer': {'status': 'pro'}}
    for k, g in enumerate(PLACEHOLDERS, 1):
        out[g] = {'name': f'Field golfer {k} (synthetic)', 'country': 'USA', 'born': 2000, 'initial': False,
                  'golfer': {'status': 'pro'}}
    for g, _ in TU.FIELD:
        out[g] = {'name': f'Golfer {g}', 'country': 'USA', 'born': 2050, 'initial': False, 'golfer': {'status': 'pro'}}
    return out


def edition(c, course=('NOPAR', 'x')):
    """The archived edition of an example: final places (and the totals the audit records), no round scores, and no
    `upset` record -- it was played before estimates were kept."""
    total = c.get('total')
    others = ([c['beaten']] if c.get('beaten') else []) + list(PLACEHOLDERS)
    finish = [[c['winner'], 1, total]]
    if c.get('playoff'):
        finish.append([others[0], 2, total])                      # tied after regulation (the runner-up: synthetic)
        others = others[1:]
    finish += [[g, len(finish) + 1, None] for g in others]
    y, sid = c['eid'].split(':')
    return {'id': c['eid'], 'series': sid, 'week': c['week'], 'year': int(y), 'name': c['name'],
            'tour': 'MAJORS' if c['major'] else 'PT', 'tier': c['tier'], 'kind': 'major' if c['major'] else 'regular',
            'category': 'major' if c['major'] else 'regular', 'rounds': 4, 'match_play': False,
            'playoff': c.get('playoff') or 0, 'finish': [finish], 'sites': [[course[0], course[1], 'City']],
            'team': {}, 'origin': 'archive'}


def estimated_edition(eid='2084:RECORDED_EVENT', week=20, **kw):
    """A synthetic edition from a season with recorded estimates (the real model on a six-golfer field)."""
    return TU._edition(eid, week, 2, TU.FIELD, 5, **kw)


def numbers_claimed(text):
    """Chances in the page's wording: '12.3%' or '1 in 2,345' (URL escapes such as %3A are not chances)."""
    return re.findall(r'\d+(?:\.\d+)?%|\b1 in [\d,]+', re.sub(r'%[0-9A-Fa-f]{2}', '', text))


def no_model_calls():
    """While active, any attempt to work out an estimate fails the test: nothing is reconstructed afterwards."""
    boom = AssertionError('an estimate was worked out for an edition after it was played')
    return mock.patch.multiple(UP, estimate=mock.Mock(side_effect=boom), win_probabilities=mock.Mock(side_effect=boom),
                               reproduce=mock.Mock(side_effect=boom), total_params=mock.Mock(side_effect=boom))


class ExampleDataTests(unittest.TestCase):
    def test_fixtures_hold_the_recorded_facts_and_no_estimate(self):
        self.assertEqual(len(EXAMPLES), 7)
        self.assertEqual(sum(c['major'] for c in EXAMPLES), 5)
        for c in CASES:
            e = edition(c)
            self.assertNotIn('upset', e)
            blob = json.dumps(e).lower()
            for word in ('chance', 'odds', 'probab', '"p"', 'overall', 'model'):
                self.assertNotIn(word, blob, c['eid'])
            self.assertFalse({'p', 'chance', 'odds', 'rank', 'overall'} & set(c), c['eid'])
        j = edition(EXAMPLES[3])
        self.assertEqual(j['finish'][0][:2], [[104, 1, 280], [PLACEHOLDERS[0], 2, 280]])
        self.assertEqual(j['playoff'], 2)
        carroll = edition(EXAMPLES[6])['finish'][0]
        self.assertEqual([g for g, _, _ in carroll][:2], [107, HARPER])   # Harper in the field, behind Carroll

    def test_statistics_rows_record_no_model_and_no_chance(self):
        import observer_stats as ST
        import observer_upsets as OU
        with no_model_calls():
            for c in CASES:
                (row,) = ST.upset_rows([edition(c)], int(c['eid'][:4]))
                r = dict(zip(OU.COLUMNS, row))
                self.assertEqual((r['event_id'], r['winner'], r['field']), (c['eid'], c['winner'], len(edition(c)['finish'][0])), c['eid'])
                self.assertEqual(r['major'], int(c['major']))
                self.assertIsNone(r['model'])                         # not recorded: no model ...
                self.assertIsNone(r['p'])                             # ... no chance ...
                self.assertIsNone(r['detail'])                        # ... and no rank by the model
                self.assertIsNone(r['status'])                        # status and age at the event: not recorded
                self.assertIsNone(r['age'])
        j = dict(zip(OU.COLUMNS, ST.upset_rows([edition(EXAMPLES[3])], 2034)[0]))
        self.assertEqual((j['playoff'], j['margin']), (2, 0))         # the result, kept apart, as recorded


class _Store:
    """A statistics store with the examples, the generic legacy edition, and one synthetic season with recorded
    estimates (one estimated stroke-play edition, one match play edition, one not-estimated record without a
    reason)."""

    def __init__(self):
        import observer_stats as ST
        self.tmp = Path(tempfile.mkdtemp())
        self.store = ST.StatsStore(self.tmp / 's.sqlite')
        by_year = {}
        for c in CASES:
            by_year.setdefault(int(c['eid'][:4]), []).append(edition(c))
        noreason = estimated_edition('2084:NO_REASON', 22, recorded=False)
        noreason['upset'] = {'model': UP.VERSION, 'estimated': False}
        by_year[FIRST_ESTIMATED] = [estimated_edition(),
                                    estimated_edition('2084:MATCH_EVENT', 21, match_play=True, kind='amateur'),
                                    noreason]
        self.editions = {e['id']: e for evs in by_year.values() for e in evs}
        for y, evs in sorted(by_year.items()):
            self.store.put(y, str(y), {}, {}, {}, {}, upsets=ST.upset_rows(evs, y))
        self.w = TU.FakeWorld(self.store.db, people(), years=sorted(by_year))

    def close(self):
        self.store.close()
        shutil.rmtree(self.tmp, ignore_errors=True)


class BiggestUpsetsPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fx = _Store()
        cls.w = cls.fx.w

    @classmethod
    def tearDownClass(cls):
        cls.fx.close()

    def page(self, **q):
        import observer_upsets as OU
        with no_model_calls():
            return OU.page(self.w, TU._q(**q))[1]

    @staticmethod
    def table(html):
        return html.split('<tbody>', 1)[1].split('</tbody>', 1)[0] if '<tbody>' in html else ''

    def test_examples_are_left_out_of_the_ranked_list(self):
        import observer_upsets as OU
        rows, _ = OU.rows_for(self.w)
        ranked = sorted((r for r in rows if r['p'] is not None), key=OU.rank_key)
        self.assertEqual([r['event_id'] for r in ranked], ['2084:RECORDED_EVENT'])
        for scope in ('', 'major'):
            body = self.table(self.page(scope=scope))
            for c in CASES:
                self.assertNotIn(quote(c['eid']), body, c['eid'])
                self.assertNotIn(c['winner_name'], body)
        body = self.table(self.page())
        self.assertEqual(len(body.split('</tr>')) - 1, 1)             # one ranked row: the estimated edition
        self.assertIn('href="/event/2084%3ARECORDED_EVENT"', body)

    def test_coverage_counts_them_as_not_recorded(self):
        html = self.page()
        self.assertIn('1 winners with a recorded estimate (seasons 2084–2084); 8 not recorded (played before '
                      'estimates were kept)', html)
        major = self.page(scope='major')
        self.assertIn('0 winners with a recorded estimate; 5 not recorded (played before estimates were kept).', major)
        self.assertIn('No winner with a recorded estimate matches', major)
        self.assertEqual(numbers_claimed(self.table(major)), [])
        self.assertIn('not calibrated win probabilities or a definitive upset ranking', major)   # the B2 note
        self.assertIn('Editions played before then show “not recorded”', major)
        old = self.page(to=2083)
        self.assertIn('8 not recorded', old)
        self.assertNotIn('not estimated', old.split('Ranked by')[0])  # nothing before 2084 is marked not estimated

    def test_not_estimated_shows_the_recorded_reason(self):
        html = self.page(**{'from': FIRST_ESTIMATED})
        self.assertIn('; 2 not estimated: match play (model 1 covers stroke play only) (1), no reason recorded (1).',
                      html)
        self.assertNotIn('not estimated (match play)', html)          # the reason is never assumed

    def test_the_same_list_with_the_examples_present_or_not(self):
        """Editions without an estimate change no rank: the ranked list is the same with or without them."""
        import observer_upsets as OU
        rows, _ = OU.rows_for(self.w)
        a = [r['event_id'] for r in sorted((r for r in rows if r['p'] is not None), key=OU.rank_key)]
        b = [r['event_id'] for r in sorted((r for r in rows if r['p'] is not None and r['year'] >= FIRST_ESTIMATED),
                                           key=OU.rank_key)]
        self.assertEqual(a, b)


class EventPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fx = _Store()

    @classmethod
    def tearDownClass(cls):
        cls.fx.close()

    def panel(self, eid):
        import observer_upsets as OU
        with no_model_calls():
            return OU.event_panel(self.fx.w, self.fx.editions[eid])

    def test_each_example_says_not_recorded(self):
        for c in CASES:
            p = self.panel(c['eid'])
            self.assertEqual(p, '<p class="muted">Pre-event estimate: not recorded (this edition was played before '
                                'estimates were kept; none is worked out afterwards).</p>', c['eid'])
            self.assertEqual(numbers_claimed(p), [])
            for word in (UP.VERSION, 'favourite', 'Top ', 'Overall', 'by the model'):
                self.assertNotIn(word, p)

    def test_not_estimated_panel_gives_the_recorded_reason(self):
        self.assertIn('not estimated (match play (model 1 covers stroke play only))', self.panel('2084:MATCH_EVENT'))
        p = self.panel('2084:NO_REASON')
        self.assertIn('not estimated (no reason recorded)', p)
        self.assertNotIn('None', p)

    def test_an_estimated_edition_still_shows_its_estimate(self):
        import observer_upsets as OU
        p = OU.event_panel(self.fx.w, self.fx.editions['2084:RECORDED_EVENT'])
        self.assertIn(UP.VERSION, p)
        self.assertTrue(numbers_claimed(p))


class StoryTests(unittest.TestCase):
    """The tournament story of each example (observer_stories over a synthetic fact source)."""

    def source(self):
        import test_stories as TS
        src = TS.FakeSource()
        src.people.update({g: {k: v for k, v in p.items() if k != 'golfer'} for g, p in people().items()})
        for c in CASES:
            e = edition(c)
            src.eds[c['eid']] = e
        return src

    def test_no_upset_is_claimed_and_the_missing_estimate_is_named(self):
        import observer_stories as S
        src = self.source()
        with no_model_calls():
            for c in CASES:
                rec = S.assemble(src, c['eid'])
                self.assertNotIn('upset', rec['facts'], c['eid'])
                self.assertIn('a pre-event win estimate (not recorded: played before estimates were kept, and none is '
                              'worked out afterwards), so no upset is claimed', rec['missing'])
                st = S.narrate(rec, lambda g: src.people.get(g, {}).get('name'))
                self.assertNotIn('upset', st['patterns'])
                self.assertNotEqual(st['primary'], 'upset')
                text = ' '.join(s.text() for s in st['sentences'])
                self.assertIn(c['winner_name'], text)
                self.assertEqual(numbers_claimed(text), [], c['eid'])
                for word in ('estimate', 'upset', 'favourite', 'chance', 'odds', UP.VERSION, 'Overall'):
                    self.assertNotIn(word, text, c['eid'])

    def test_jefferson_story_keeps_the_recorded_facts(self):
        import observer_stories as S
        src = self.source()
        rec = S.assemble(src, '2034:TOUR_MASTERS')
        st = S.narrate(rec, lambda g: src.people.get(g, {}).get('name'))
        self.assertEqual(st['primary'], 'playoff')                   # the result's shape, not an upset
        text = ' '.join(s.text() for s in st['sentences'])
        self.assertIn('Chris Jefferson', text)
        self.assertIn('280', text)
        self.assertIn('two extra holes', text)
        self.assertNotIn('75.1', text)                                # a prior rating is never turned into a chance
        self.assertNotIn('77.6', text)


class EventPageTests(unittest.TestCase):
    """The observer's own pages for Jefferson's 2034 Masters, held as the current season of a hand-built snapshot
    with no estimate recorded: the edition page (estimate panel), its Story tab and the Biggest Upsets page."""

    def setUp(self):
        import observer as O
        from observer_live import LiveView
        self.O = O
        self.tmp = Path(tempfile.mkdtemp())
        c = EXAMPLES[3]
        e = {k: v for k, v in edition(c).items() if k not in ('year', 'origin')}
        e['routes'] = {}
        by_person = {}
        for g, pos, _ in e['finish'][0]:
            by_person.setdefault(g, []).append((e['id'], 0, pos))
        pp = {g: {'name': p['name'], 'country': p['country'], 'born': p['born'], 'status': 'pro',
                  'lifestyle': 'full_time', 'tour': 'PT', 'turned_pro': 2020, 'roles': ['golfer'], 'initial': False}
              for g, p in people().items()}
        pp[104]['status'] = 'amateur'
        live = LiveView(cursor={'year': 2034, 'week': 30, 'phase': 'week'}, generation=1, year=2034, people=pp,
                        editions={e['id']: e}, by_person=by_person, schedule=[], first_year=2027,
                        series={'TOUR_MASTERS': {'name': 'Masters', 'tour': 'MAJORS', 'tier': 0, 'kind': 'major',
                                                 'category': 'major'}},
                        courses={}, tours={'MAJORS': {'name': 'Majors', 'tier': 0}}, rank_top={}, moments=[],
                        records={}, wr={}, am={}, home={}, first={}, birth={}, moves={}, rules_version='2026-11-03')
        w = O.World.__new__(O.World)
        w.path = w.archive_dir = self.tmp
        w.session, w.a, w.live, w.label = None, None, live, 'test'
        self.w = w

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_edition_page_story_tab_and_upsets_page(self):
        O = self.O
        with no_model_calls():
            final = O.event(self.w, {}, '2034:TOUR_MASTERS')[1]
            story = O.event(self.w, {'view': ['story']}, '2034:TOUR_MASTERS')[1]
            upsets = O.PAGES['/upsets'](self.w, {})[1]
        self.assertIn('Pre-event estimate: not recorded (this edition was played before estimates were kept; none is '
                      'worked out afterwards).', final)
        self.assertNotIn(UP.VERSION, final)
        self.assertIn('Chris Jefferson', story)
        self.assertIn('Not in the record, so not in the story', story)
        self.assertIn('a pre-event win estimate (not recorded: played before estimates were kept, and none is worked '
                      'out afterwards), so no upset is claimed', story)
        for page in (final, story):
            self.assertEqual(numbers_claimed(page), [])
        self.assertIn('0 winners with a recorded estimate; 1 not recorded (played before estimates were kept).', upsets)
        self.assertIn('No winner with a recorded estimate matches', upsets)
        self.assertNotIn('Chris Jefferson', upsets)


if __name__ == '__main__':
    unittest.main()
