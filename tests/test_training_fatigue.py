"""Regression: practice incurs its existing load even when starting completely fresh."""
import unittest
from tests.test_career_foundation import started, plan, golfer
import career_fixture as F
from golfsim import career as CA
from golfsim.session import Session

class TrainingFatigue(unittest.TestCase):
    def test_boundaries_sequences_and_forecast_parity(self):
        s = started('training-fatigue-boundary')
        g, season, y = golfer(s), s.season, s.cursor['year']
        # Isolate the actual fatigue-update method from tournament loads/development.
        season._week_load.clear()
        for stamina in (0, 50, 100):
            g.attrs['stamina'] = stamina
            load = .02 * (1.4 - .8 * stamina / 100)
            for initial in (0, .004, .02, .3, 1):
                season.fatigue[g.id] = g.fatigue = initial
                season.week_activity[g.id] = 'train'
                forecast = CA.readiness(season, g, y, 1)['train_after']
                season.update_fatigue(y, 1)
                expected = .85 * initial + load
                self.assertAlmostEqual(g.fatigue, expected)
                self.assertEqual(season.fatigue[g.id], g.fatigue)
                self.assertEqual(forecast, round(g.fatigue, 4))
                self.assertGreater(g.fatigue, 0)
                self.assertLessEqual(g.fatigue, 1)
            season.fatigue[g.id] = g.fatigue = 0
            expected = 0
            for week in range(1, 9):
                season.week_activity[g.id] = 'train'
                expected = .85 * expected + load
                season.update_fatigue(y, week)
                self.assertAlmostEqual(g.fatigue, expected)
            for week in range(9, 25):
                season.week_activity[g.id] = 'rest'
                forecast = CA.readiness(season, g, y, week)['rest_after']
                previous = g.fatigue
                season.update_fatigue(y, week)
                self.assertLessEqual(g.fatigue, previous)
                self.assertEqual(forecast, round(g.fatigue, 4))
            self.assertEqual(g.fatigue, 0)
        s.close()

    def test_real_training_records_and_reload_are_deterministic(self):
        a = started('training-fatigue-save')
        y = a.cursor['year']
        g = golfer(a)
        self.assertEqual(a.season.fatigue[g.id], 0)
        plan(a, (y, 1), {w: {'kind': 'train', 'category': 'putting'} for w in range(1, 5)})
        b = Session.open(F.copy_of(a.dir))
        a.advance_career('period')
        b.advance_one_week()
        path = b.dir
        b.close()
        b = Session.open(path)
        b.advance_career('period')
        self.assertEqual(F.digest(a), F.digest(b))
        va, vb = CA.view(a.season, a.cursor), CA.view(b.season, b.cursor)
        self.assertEqual(va['recaps'], vb['recaps'])
        rows = va['recaps'][0]['weeks']
        self.assertEqual(rows[0]['before']['fatigue'], 0)
        self.assertTrue(all(r['after']['fatigue'] > 0 for r in rows))
        self.assertTrue(all(r['activity'] == 'train' for r in rows))
        self.assertEqual(va['golfer']['fatigue'], rows[-1]['after']['fatigue'])
        self.assertEqual(va['readiness']['fatigue'], va['golfer']['fatigue'])
        a.close(); b.close()
