"""v0.5 candidate: initialize veterans on the same development law as entrants.

This does NOT force a target age, give age-based win bonuses, or add rare stars.
The v0.3 veteran initializer matured technical skill faster/later than its actual
annual development system. We reconstruct an expected injury-free development
history using each golfer's own ceilings, readiness, growth and decline traits.
"""
import math
from statistics import mean
import engine_v04 as prior
from engine_v03 import A

class World(prior.World):
 def _create_golfer(self,initial=False):
  g=super()._create_golfer(initial=initial)
  if not initial:
   # Replenishment occurs after the current season; debut next season at18,
   # rather than skipping the age18 development year.
   g.born+=1
   return g
  age=self.year-g.born
  for j,cap in enumerate(g.caps):
   # Retain the initializer's small individual attribute-specific noise.
   if j in (A['drive_power'],A['stamina'],A['recovery']):
    old_ratio=.795+min(max(age-18,0),13)*.014
    if age>g.physical_peak:old_ratio-=.011*(age-g.physical_peak)
    ratio18=.795
   elif j==A['injury_resistance']:old_ratio=.94;ratio18=.94
   elif j in (A['composure'],A['resilience'],A['management']):
    old_ratio=.76+min(max(age-18,0),24)*.0085
    if age>g.mental_peak:old_ratio-=.003*(age-g.mental_peak)
    ratio18=.76+(.025 if g.prodigy else 0)
    if g.prodigy:old_ratio+=.025
   else:
    old_ratio=.79+min(max(age-18,0),18)*.0115
    if age>g.technical_peak:old_ratio-=.004*(age-g.technical_peak)
    ratio18=.79
   residual=g.attrs[j]-min(cap,cap*(old_ratio+g.readiness))
   value=max(25,min(cap,min(cap,cap*(ratio18+g.readiness))+residual))
   for historical_age in range(18,age):
    gap=max(0,cap-value);diminishing=(gap/(gap+9))**1.2 if gap else 0.
    if j in (A['drive_power'],A['stamina'],A['recovery']):
     rate=3.3 if historical_age<=22 else 1.65 if historical_age<=27 else .78 if historical_age<=g.physical_peak else 0
     decline=g.physical_decline+.115*(historical_age-g.physical_peak) if historical_age>g.physical_peak else 0
    elif j==A['injury_resistance']:rate=0;decline=max(0,historical_age-39)*.08
    elif j in (A['composure'],A['resilience'],A['management']):
     rate=.85 if historical_age<=25 else .61 if historical_age<=39 else .30 if historical_age<=g.mental_peak else 0
     decline=g.mental_decline+.028*(historical_age-g.mental_peak) if historical_age>g.mental_peak else 0
    else:
     rate=3. if historical_age<=22 else 1.65 if historical_age<=27 else .95 if historical_age<=32 else .50 if historical_age<=g.technical_peak else 0
     decline=g.technical_decline+.045*(historical_age-g.technical_peak) if historical_age>g.technical_peak else 0
    # Neutral historical resources: modest average competition multiplier;
    # expected rotating-focus factor, no perfect coach or forced full ceiling.
    efficiency=1.03*g.growth_rate
    focus=1.025 if j<12 else 1.
    value=max(20,min(cap,value+rate*efficiency*diminishing*focus-decline))
   g.attrs[j]=value
  return g
 def _rank_and_archive(self):
  start=len(self.annual_golfers)
  super()._rank_and_archive()
  for row in self.annual_golfers[start:]:
   g=self.golfers[row['golfer_id']]
   row['mean_technical_cap']=round(mean(g.caps[:9]),3)
   row['initial_population']=int(g.id<=self.population)
 def summary(self):
  out=super().summary();out['model_version']='0.5-growth-candidate'
  out['calibration']['coherent_veteran_initialization']=True
  return out
