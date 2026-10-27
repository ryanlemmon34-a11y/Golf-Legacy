import math,unittest
import engine_v06 as e
class CandidateTests(unittest.TestCase):
 def test_taper_continuous_monotone_and_preserves_ordinary_range(self):
  for x in range(40,91):self.assertAlmostEqual(e.elite_bonus(x),.03*max(0,x-75)**2)
  eps=1e-5
  self.assertAlmostEqual((e.elite_bonus(90+eps)-e.elite_bonus(90))/eps,(e.elite_bonus(90)-e.elite_bonus(90-eps))/eps,places=4)
  values=[e.elite_bonus(x/10) for x in range(750,1001)]
  self.assertTrue(all(b>=a for a,b in zip(values,values[1:])))
  self.assertLess(e.elite_bonus(100),.03*25**2)
 def test_real_extra_fields_not_huge_fields(self):
  w=e.World(42,100,audit=False);minis=[t for t in w.tours if t.tier==4]
  self.assertEqual(len(minis),5);self.assertEqual(sum(t.slots*t.events for t in minis),6000)
  self.assertTrue(all(t.slots==100 for t in minis));self.assertEqual(len(w._schedule()),191)
 def test_no_double_booked_venues(self):
  for seed in (42,707,808,909):
   w=e.World(seed,50,audit=False);events=w._schedule();keys=[(x[0],x[4].id) for x in events]
   self.assertEqual(len(keys),len(set(keys)))
 def test_major_achievement_earns_access_not_hidden_talent(self):
  w=e.World(42,100,audit=False);g=next(iter(w.golfers.values()));g.tier=4
  w.major_history.append({'winner_id':g.id,'year':w.year});w._tour_moves()
  self.assertEqual(g.tier,1);self.assertTrue(any(x['event']=='Premier eligibility earned' for x in g.career))
  self.assertFalse(any(x['event'] in ('Promoted','Relegated') for x in g.career))
 def test_earned_access_expires(self):
  w=e.World(42,100,audit=False);g=next(iter(w.golfers.values()));g.tier=4
  w.major_history.append({'winner_id':g.id,'year':w.year-5});w._tour_moves();self.assertNotEqual(g.tier,1)
 def test_local_capacity_still_cash_gated_and_reconciles(self):
  w=e.World(42,100,events_scale=.03,audit=False).run(1)
  self.assertTrue(w.economics.validate(w.golfers)['valid'])
  self.assertEqual(sum(g.starts for g in w.golfers.values()),sum(e['field'] for e in w.event_history))
  self.assertTrue(all(x['field']<=x['slots'] and x['field']<=x['affordable_demand'] for x in w.entry_opportunities))
if __name__=='__main__':unittest.main()
