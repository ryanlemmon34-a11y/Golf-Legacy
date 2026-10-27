"""Golf Legacy v0.7 national-open experiment based on frozen v0.6.

Home-country opens replace EXISTING regional/challenger event editions,
rotating venues within host countries and reserving a small invitation lane
for credible home-country golfers whose normal tour is stronger.

This is a fictional, uncalibrated opportunity mechanism, not a real-world
representation of exemption categories or real event attendance.
"""
from __future__ import annotations
import argparse, csv, json, random
from collections import Counter
from pathlib import Path
import engine_v06 as baseline

class World(baseline.World):
 def __init__(self,*args,national_opens=True,invitation_rate=.68,**kwargs):
  self.national_opens=national_opens
  self.invitation_rate=invitation_rate
  self.home_open_meta={}
  self.home_open_records=[]
  self.home_open_invites=[]
  self.home_open_decisions=[]
  self.home_open_venue_last={}
  self.home_open_stats=Counter()
  super().__init__(*args,**kwargs)

 def _schedule(self):
  schedule=super()._schedule()
  self.home_open_meta={}
  if not self.national_opens:return schedule
  # Identify available feeder/secondary-tour events, already scheduled at
  # non-conflicting course/week coordinates by v0.6.
  region_slots={r:[] for r in ('Americas','Europe','Asia','Africa','Oceania')}
  for i,ev in enumerate(schedule):
   week,priority,name,tour,course,major,cut,field_size=ev
   if not major and tour.tier in (2,3) and tour.region in region_slots:
    region_slots[tour.region].append(i)
  occupied={(e[0],e[4].id) for e in schedule}
  countries_by_region={r:[c for c in self.countries if self.countries[c]['region']==r] for r in region_slots}
  new=list(schedule)
  quiet_weeks=[w for w in range(2,50) if not any(e[0]==w and (e[5] or e[3].tier==1) for e in schedule)]
  scheduled_opens_by_week=Counter()
  # Rotation priority ensures countries missing an annual edition eventually host.
  for region,countries in countries_by_region.items():
   if not countries:continue
   slots=region_slots[region]
   if not slots:continue
   rotate=(self.year-2027)%len(countries)
   ordered=countries[rotate:]+countries[:rotate]
   # Avoid choosing all tier-2 or all tier-3 events; a national open can be
   # attractive to premier golfers even if hosted by a lower-tier circuit.
   for country in ordered[:min(len(ordered),len(slots))]:
    country_courses=[c for c in self.courses.values() if c.country==country]
    if not country_courses:continue
    preferences=sorted(slots,key=lambda idx:(
     abs(new[idx][3].tier-(3 if self.countries[country]['infra']<1.05 else 2)),
     abs(new[idx][0]-(15+((self.year+sum(map(ord,country)))%27))), idx))
    chosen=None
    for idx in preferences:
     ev=new[idx]
     local_quiet=sorted(quiet_weeks,key=lambda w:(
      any(other[0]==w and other[3].id==ev[3].id for j,other in enumerate(new) if j!=idx),
      scheduled_opens_by_week[w],abs(w-ev[0]),w))
     for quiet_week in local_quiet:
      if any(other[0]==quiet_week and other[3].id==ev[3].id for j,other in enumerate(new) if j!=idx):continue
      free=[c for c in country_courses if (quiet_week,c.id) not in occupied or
            (quiet_week==ev[0] and c.id==ev[4].id)]
      if free:
       previously=self.home_open_venue_last.get(country)
       alternatives=[c for c in free if c.id!=previously]
       course=self.r.choice(alternatives or free)
       chosen=(idx,quiet_week,course);break
     if chosen is not None:break
    if chosen is None:continue
    idx,quiet_week,course=chosen;ev=new[idx]
    old_week,priority,old_name,tour,old_course,major,cut,fieldsize=ev
    occupied.remove((old_week,old_course.id));occupied.add((quiet_week,course.id))
    week=quiet_week
    scheduled_opens_by_week[week]+=1
    name=f'{country} National Open'
    new[idx]=(week,priority,name,tour,course,False,cut,fieldsize)
    self.home_open_meta[(self.year,week,name)]={'host_country':country,'host_tour':tour.name,
     'tier':tour.tier,'course_id':course.id,'year':self.year,'week':week,'event':name}
    self.home_open_venue_last[country]=course.id
    slots.remove(idx)
  return sorted(new,key=lambda x:(x[0],x[1]))

 def _choose_field(self,tour,major,week):
  event_key=(self.year,week,self.current_event_id.split(':',2)[-1])
  info=self.home_open_meta.get(event_key)
  if info is None:return super()._choose_field(tour,major,week)
  host=info['host_country']
  eligible=[g for g in self.golfers.values() if
   g.country==host and not g.retired and g.tier<tour.tier and
   g.annual_starts<27 and g.last_week!=week and
   self.economics.can_start(g,tour.tier,self.year,week)]
  # Strong current ability and/or proven victories signal a relevant hometown
  # star; this is not an automatic right to a tournament invitation.
  eligible=[g for g in eligible if g.tier==1 or g.majors>0 or g.wins>=2]
  eligible.sort(key=lambda g:(g.majors>0,g.wins,self._ability(g)),reverse=True)
  max_invites=min(4,max(1,tour.slots//20))
  invites=[]
  for g in eligible:
   if len(invites)>=max_invites:break
   # Participation remains elective and finances/schedule constrained;
   # established local champions are a bit likelier to accept.
   acceptance=min(.91,self.invitation_rate+(.09 if g.majors else 0)-(.07 if g.fatigue>65 else 0))
   accepted=self.r.random()<acceptance
   self.home_open_decisions.append({'year':self.year,'week':week,'event':info['event'],
    'host_country':host,'golfer_id':g.id,'golfer':g.name,'tier':g.tier,
    'career_wins_before':g.wins,'career_majors_before':g.majors,'accepted':int(accepted)})
   if accepted:invites.append(g)
  original_slots=tour.slots
  tour.slots=original_slots-len(invites)
  old_weeks={g.id:g.last_week for g in invites}
  for g in invites:g.last_week=week  # hold reserved seats out of regular selection
  try:
   field=super()._choose_field(tour,major,week)
  finally:
   tour.slots=original_slots
   for g in invites:g.last_week=old_weeks[g.id]
  if len(field)<3:
   # This should not arise at normal scale; avoid charging invitees when
   # no tournament can be held. v0.6 owns any base-field cancellations.
   return field
  for g in invites:
   if not self.economics.pay_entry(g,self.current_event_id,tour.tier,self.year,week):
    raise AssertionError('Home invite was confirmed affordable but could not pay')
   g.annual_starts+=1;g.last_week=week
   self.event_shocks[g.id]=self.r.gauss(0,self.event_noise)*self._consistency_scale(g) if self.event_noise else 0
   field.append(g)
   self.home_open_invites.append({'year':self.year,'week':week,'event':info['event'],
    'host_country':host,'golfer_id':g.id,'golfer':g.name,'normal_tier':g.tier,
    'event_tier':tour.tier,'major_wins_before':g.majors,'professional_wins_before':g.wins,
    'entry_reason':'accepted national-open invitation'})
  # v0.6 appends the main field-allocation audit during its _choose_field.
  # Update totals to include the special invitation lane.
  row=self.entry_opportunities[-1]
  row['slots']=original_slots
  row['field']=len(field)
  row['local_starts']=sum(self.countries[g.country]['region']==tour.region for g in field)
  row['eligible_before_budget']+=len(invites)
  row['affordable_demand']+=len(invites)
  row['local_affordable_demand']+=len(invites)
  self.home_open_stats['accepted_elite_visits']+=len(invites)
  self.home_open_stats['offered_elite_invites']+=sum(x['year']==self.year and x['week']==week and x['event']==info['event'] for x in self.home_open_decisions)
  return field

 def _simulate_event(self,info):
  week,_,name,tour,course,major,_,_=info
  before=len(self.event_history)
  super()._simulate_event(info)
  created=len(self.event_history)>before
  meta=self.home_open_meta.get((self.year,week,name))
  if created:
   record=self.event_history[-1]
   record.update({'national_open':int(bool(meta)),
    'host_country':meta['host_country'] if meta else '',
    'invited_elite_home_starts':sum(1 for x in self.home_open_invites if x['year']==self.year and x['week']==week and x['event']==name) if meta else 0})
   if meta:
    row={**meta,'winner_id':record['winner_id'],'winner':record['winner'],
     'winner_country':record['winner_country'],'home_winner':int(record['winner_country']==meta['host_country']),
     'field':record['field'],'invited_elite_home_starts':record['invited_elite_home_starts'],
     'course_name':record['course'],'purse':tour.purse}
    self.home_open_records.append(row)
    self.home_open_stats['events']+=1
    self.home_open_stats['home_winners']+=row['home_winner']
  elif meta:
   self.home_open_stats['cancelled_home_opens']+=1

 def summary(self):
  d=super().summary();d['model_version']='0.7-national-opens'
  d['national_opens']={'completed':len(self.home_open_records),
   'accepted_elite_visits':len(self.home_open_invites),
   'countries_hosted':len({x['host_country'] for x in self.home_open_records}),
   'home_wins':sum(x['home_winner'] for x in self.home_open_records),
   'invitation_decisions':len(self.home_open_decisions)}
  return d

 def export(self,root):
  out=super().export(root)
  root=Path(root)
  for name,rows in [('national_opens.csv',self.home_open_records),
                    ('national_open_invites.csv',self.home_open_invites),
                    ('national_open_decisions.csv',self.home_open_decisions)]:
   with (root/name).open('w',newline='',encoding='utf-8') as file:
    if rows:
     w=csv.DictWriter(file,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
  (root/'national_open_summary.json').write_text(json.dumps(self.summary()['national_opens'],indent=2))
  return out

def main():
 p=argparse.ArgumentParser();p.add_argument('--years',type=int,default=60);p.add_argument('--seed',type=int,default=1217)
 p.add_argument('--population',type=int,default=1700);p.add_argument('--events-scale',type=float,default=1.0)
 p.add_argument('--out',default='world_v07');p.add_argument('--quiet',action='store_true')
 p.add_argument('--no-national-opens',action='store_true');p.add_argument('--invitation-rate',type=float,default=.68)
 a=p.parse_args();world=World(a.seed,a.population,a.events_scale,national_opens=not a.no_national_opens,
  invitation_rate=a.invitation_rate).run(a.years,verbose=not a.quiet)
 print(json.dumps(world.export(a.out),indent=2))
if __name__=='__main__':main()
