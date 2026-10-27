"""v0.6 candidate: smooth extreme skill, local opportunities, earned premier access."""
import argparse,csv,json,math
from pathlib import Path
import engine_v05 as prior
from engine_v03 import Tour
from engine_v04 import technical_rating

def elite_bonus(rating,curve=.03,threshold=90.,width=3.):
 if width<=0:raise ValueError('tail width must be positive')
 x=max(0.,rating-75.)
 if rating<=threshold:return curve*x*x
 t=threshold-75.
 return curve*t*t+2*curve*t*width*math.log1p((rating-threshold)/width)

class World(prior.World):
 def __init__(self,*args,tail_width=3.,regional_minis=True,earned_access=True,**kwargs):
  self.tail_width=tail_width;self.regional_minis=regional_minis;self.earned_access=earned_access
  self.entry_opportunities=[]
  super().__init__(*args,**kwargs)
 def _setup_tours(self):
  super()._setup_tours()
  if self.regional_minis:
   self.tours=[t for t in self.tours if t.tier!=4]
   for region in ('Americas','Europe','Asia','Africa','Oceania'):
    self.tours.append(Tour(len(self.tours),f'{region} Mini Circuit',region,4,21,12,100,45000))
 def _schedule(self):
  schedule=[];reserved=set();top=self.tours[0]
  for name,week,cid,cut,fieldsize in [('Founders Masters',12,0,50,96),('World Open',21,None,60,144),('Heritage Championship',31,None,70,144),('Summit Invitational',41,1,70,144)]:
   available=[c for c in self.courses.values() if (week,c.id) not in reserved]
   course=self.courses[cid] if cid is not None else self.r.choice(available)
   reserved.add((week,course.id));schedule.append((week,0,name,top,course,True,cut,fieldsize))
  for tour in self.tours:
   local=[c for c in self.courses.values() if tour.region=='Global' or self.countries[c.country]['region']==tour.region]
   if len(local)<4:local=list(self.courses.values())
   already=set();count=max(1,round(tour.events*self.events_scale))
   for i in range(count):
    week=3+round(i*42/max(1,count-1))+(tour.id*3)%6
    free=[c for c in local if (week,c.id) not in reserved]
    candidates=[c for c in free if c.id not in already] or free
    if not candidates:raise ValueError('No available regional venue for scheduled event')
    course=self.r.choice(candidates);already.add(course.id);reserved.add((week,course.id))
    schedule.append((week,1+tour.id,f'{tour.name} Event {i+1}',tour,course,False,65,tour.slots))
  return sorted(schedule,key=lambda x:(x[0],x[1]))
 def _hole_quality(self,g,hole,major,rd,partner_aura=0,weather=0):
  q=super()._hole_quality(g,hole,major,rd,partner_aura,weather)
  rating=technical_rating(g,hole)
  return q-self.elite_curve*max(0.,rating-75.)**2+elite_bonus(rating,self.elite_curve,width=self.tail_width)
 def _choose_field(self,tour,major,week):
  eligible=[g for g in self.golfers.values() if not g.retired and g.annual_starts<27 and g.last_week!=week and (not major or g.annual_major_starts<4) and (major or abs(g.tier-tour.tier)<=1)]
  affordable=[g for g in eligible if self.economics.can_start(g,tour.tier,self.year,week)]
  chosen=super()._choose_field(tour,major,week)
  self.entry_opportunities.append({'year':self.year,'week':week,'event_id':self.current_event_id,'tour':tour.name,'tier':tour.tier,'region':tour.region,'major':int(major),'slots':tour.slots,'eligible_before_budget':len(eligible),'affordable_demand':len(affordable),'local_affordable_demand':sum(self.countries[g.country]['region']==tour.region for g in affordable),'field':len(chosen),'local_starts':sum(self.countries[g.country]['region']==tour.region for g in chosen)})
  return chosen
 def _tour_moves(self):
  qualified={r['winner_id']:r['year'] for r in self.major_history if r['year']>=self.year-4} if self.earned_access else {}
  prior_state={gid:(self.golfers[gid].tier,len(self.golfers[gid].career)) for gid in qualified}
  super()._tour_moves()
  for gid,win_year in qualified.items():
   g=self.golfers[gid]
   if g.retired:continue
   old,log_start=prior_state[gid]
   # Exempt status supersedes ordinary percentile movement, not two contradictory moves.
   recent=g.career[log_start:];kept=[]
   for event in recent:
    if event['event'] in ('Promoted','Relegated'):
     self.stats['promotions' if event['event']=='Promoted' else 'relegations']-=1
    else:kept.append(event)
   g.career[log_start:]=kept;g.tier=1
   if old>1:
    g.career.append({'year':self.year,'event':'Premier eligibility earned','timing':'year_end','from':old,'to':1,'reason':'Major victory within the preceding five seasons','qualifying_win_year':win_year})
 def summary(self):
  out=super().summary();out['model_version']='0.6'
  out['calibration'].update({'upper_tail_threshold':90,'upper_tail_log_width':self.tail_width,'regional_mini_circuits':self.regional_minis,'major_earned_premier_access':self.earned_access})
  return out
 def export(self,root):
  out=super().export(root)
  with open(Path(root)/'entry_opportunities.csv','w',newline='') as f:
   if self.entry_opportunities:
    wr=csv.DictWriter(f,fieldnames=list(self.entry_opportunities[0]));wr.writeheader();wr.writerows(self.entry_opportunities)
  return out

def main():
 p=argparse.ArgumentParser();p.add_argument('--years',type=int,default=30);p.add_argument('--seed',type=int,default=909);p.add_argument('--population',type=int,default=1700);p.add_argument('--events-scale',type=float,default=1.);p.add_argument('--out',default='results_v06');p.add_argument('--tail-width',type=float,default=3.)
 a=p.parse_args();w=World(a.seed,a.population,a.events_scale,tail_width=a.tail_width).run(a.years,verbose=True);print(json.dumps(w.export(a.out),indent=2))
if __name__=='__main__':main()
