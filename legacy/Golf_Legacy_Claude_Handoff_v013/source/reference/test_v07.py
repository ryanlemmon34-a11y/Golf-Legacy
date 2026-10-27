import unittest
from collections import Counter
from engine_v07 import World

class NationalOpenTests(unittest.TestCase):
 def setUp(self):
  self.world=World(seed=1217,population=200,events_scale=.20)
 def test_calendar_locations_and_competition(self):
  w=self.world
  for year in (2027,2028):
   w.year=year
   schedule=w._schedule()
   self.assertEqual(len({(e[0],e[4].id) for e in schedule}),len(schedule))
   opens=[e for e in schedule if 'National Open' in e[2]]
   self.assertGreaterEqual(len(opens),8)
   for e in opens:
    host=e[2].removesuffix(' National Open')
    self.assertEqual(e[4].country,host)
    self.assertIn(e[3].tier,(2,3))
    self.assertFalse(e[5])
    self.assertFalse(any(other[0]==e[0] and (other[5] or other[3].tier==1) for other in schedule))
 def test_home_starts_cannot_be_automatic_or_double_booked(self):
  w=self.world
  w.run(1)
  starts=[x for x in w.home_open_invites]
  self.assertGreater(len(starts),0)
  self.assertEqual(len({(x['year'],x['week'],x['golfer_id']) for x in starts}),len(starts))
  for x in starts:
   self.assertEqual(w.golfers[x['golfer_id']].country,x['host_country'])
   self.assertLess(x['normal_tier'],x['event_tier'])
  self.assertEqual(w.summary()['purse_conservation_errors'],0)
  self.assertTrue(w.summary()['economics']['valid'])

if __name__=='__main__':unittest.main()
