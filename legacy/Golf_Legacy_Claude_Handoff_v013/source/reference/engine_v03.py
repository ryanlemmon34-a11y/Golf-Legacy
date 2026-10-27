"""Golf Legacy v0.3: age curves, genuinely early-ready rare prodigies; independently seeded, event-time-ordered hole-by-hole world simulator.

Requires Python 3.10+. Built from v0.1's fictional world constants. This is an
UNCALIBRATED simulation test bed, not a validated golf prediction model.

Tournament model: paired threesomes (R1-R2, opposite waves/tees), weekend
score-ordered twosomes (leaders last), 36-hole top-N-and-ties cut, live projected
cut pressure and late-contending pressure, hole-specific outcomes, and playoffs.

Usage: python engine_v03.py --years 30 --seed 42 --out results_v02_seed42
"""
from __future__ import annotations
import argparse, csv, gzip, heapq, json, math, random, time
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from engine import REGIONS, FIRST, LAST, ARCHETYPES

ATTRS=('drive_power','drive_accuracy','long_iron','approach','short_game','trouble_recovery',
       'putting','putt_consistency','ball_consistency','composure','resilience',
       'management','stamina','recovery','injury_resistance')
A={name:i for i,name in enumerate(ATTRS)}
SKILL=(.095,.105,.065,.235,.095,.055,.175,.033,.033,.03,.03,.049)
COUNTRY_CHOICES=list(REGIONS)
STYLE=['Links','Parkland','Desert','Mountain','Coastal','Heathland','Woodland']
BASE_PROB={3:(.001,.135,.195,.030,.003),4:(.004,.235,.165,.026,.003),5:(.065,.425,.095,.014,.002)}
# prob order: eagle, birdie, bogey, double, triple; remainder par.

@dataclass(slots=True)
class Golfer:
 id:int; name:str; country:str; born:int; archetype:str; tier:int
 attrs:list; caps:list; stage:int; risk:int; coachability:int; durability:int
 form:float=0.; slump:float=0.; slump_years:int=0; injury:float=0.; confidence:float=0.; fatigue:float=0.
 cash:float=25000.; wins:int=0; majors:int=0; starts:int=0; cuts:int=0; earnings:float=0.
 season_points:float=0.; last_points:float=0.; season_wins:int=0; rank:int=9999; peak_rank:int=9999
 retired:bool=False; annual_starts:int=0; annual_major_starts:int=0; last_week:int=-1
 coach_id:int=-1; caddie_id:int=-1; relationship:int=35
 # Hidden biological/development parameters. A "prodigy" is a rare starting
 # configuration, never a predetermined win count or scripted career.
 readiness:float=0.; growth_rate:float=1.; physical_peak:int=32; technical_peak:int=36
 mental_peak:int=42; physical_decline:float=.8; technical_decline:float=.25
 mental_decline:float=.14; prodigy:bool=False
 visited:dict=field(default_factory=dict); career:list=field(default_factory=list)

@dataclass(slots=True)
class Staff:
 id:int; name:str; role:str; born:int; country:str; archetype:str
 skills:list; caps:list; retired:bool=False; assigned_to:int=-1; wins:int=0; majors:int=0
 visits:dict=field(default_factory=dict)

@dataclass(slots=True)
class Hole:
 number:int; par:int; yards:int; diff:float; width:float; hazard:float; green:float

@dataclass(slots=True)
class Course:
 id:int; name:str; country:str; style:str; par:int; length:int; holes:list
 record:int=999; record_holder:int=-1; record_year:int=0; visits:int=0
 course_winners:dict=field(default_factory=dict); hole_records:list=field(default_factory=list)

@dataclass(slots=True)
class Tour:
 id:int; name:str; region:str; tier:int; prestige:int; events:int; slots:int; purse:int

class World:
 def __init__(self,seed:int=42,population:int=1700,events_scale:float=1.,audit:bool=True):
  self.r=random.Random(seed);self.seed=seed;self.population=population;self.events_scale=events_scale;self.audit=audit
  self.year=2027; self.next_id=1; self.next_staff_id=1
  self.golfers={};self.staff={};self.courses={};self.tours=[]
  self.countries={c:{'region':t[0],'weight':t[1],'base':t[2], 'infra':t[2],
   'investment':0.,'role_models':0.,'development_spend':0., 'young_added':0} for c,t in REGIONS.items()}
  self.major_history=[];self.event_history=[];self.world_years=[];self.countries_history=[];self.records=[]
  self.featured_tournament=None;self.validation=[];self.stats=Counter();self.event_finishes=[]
  self._setup_tours();self._setup_courses()
  for _ in range(population):self._create_golfer(initial=True)
  self._assign_initial_staff()

 def _setup_tours(self):
  specs=[('Americas Premier','Americas',1,94,13,120,14000000),('Europe Premier','Europe',1,88,12,120,9000000),('Asia Pacific Premier','Asia',1,83,9,105,6000000),
   ('Americas Challenger','Americas',2,65,13,120,1200000),('Europe Challenger','Europe',2,61,12,120,1100000),('Asia Challenger','Asia',2,58,10,105,800000),
   ('Oceania Challenger','Oceania',2,55,7,100,650000),('Africa Challenger','Africa',2,54,7,100,600000),
   ('Americas Regional','Americas',3,39,10,100,180000),('Europe Regional','Europe',3,37,10,100,175000),('Asia Regional','Asia',3,37,9,100,150000),
   ('Africa Regional','Africa',3,34,8,85,115000),('Oceania Regional','Oceania',3,36,7,90,135000),('Global Mini Tour','Global',4,21,12,100,45000)]
  self.tours=[Tour(i,*data) for i,data in enumerate(specs)]

 def _setup_courses(self):
  words=['Heritage','Royal','Pine','Valley','Summit','Highland','Oak','Riverside','Cedar','Golden','Bay','Stone','Emerald','Ridge','Lakes','Windward']
  endings=['Golf Club','Country Club','Links','Golf Resort','Championship Course','Golf Park']
  for i in range(240):
   country=COUNTRY_CHOICES[i%len(COUNTRY_CHOICES)];style=self.r.choice(STYLE);par=self.r.choices([70,71,72],[2,2,6])[0]
   pars=[3]*4+[5]*4+[4]*(par-4*3-4*5-0)  # wrong: par4 count must solve via hole count
   # Build 18 holes, par 70/71/72 by converting two/fewer par 5s to par 4s.
   num_par5=par-68 # par70: 2 par5; par71:3 par5; par72:4 par5
   pars=[3]*4+[5]*num_par5+[4]*(14-num_par5);self.r.shuffle(pars)
   holes=[]
   for n,p in enumerate(pars,1):
    yards=int(self.r.gauss({3:185,4:425,5:565}[p],{3:35,4:60,5:48}[p]))
    difficulty=self.r.uniform(-.36,.53)
    holes.append(Hole(n,p,max(95,yards),difficulty,self.r.random(),self.r.random(),self.r.random()))
   length=sum(h.yards for h in holes)
   name=f'{self.r.choice(words)} {self.r.choice(words)} {self.r.choice(endings)} #{i+1}'
   self.courses[i]=Course(i,name,country,style,par,length,holes,hole_records=[99]*18)

 def _create_golfer(self,initial=False):
  r=self.r
  weights=[self.countries[c]['weight']*self.countries[c]['infra']**1.2 for c in COUNTRY_CHOICES]
  country=r.choices(COUNTRY_CHOICES,weights)[0]
  arch=r.choice(tuple(ARCHETYPES))
  age=r.randint(18,39) if initial else 18
  # RARE UPPER TAIL: approx 0.016% of generated golfers are born with the
  # unusual combination of broad ability, early readiness and high mental base.
  # This does NOT grant wins, majors, exemptions or guaranteed longevity.
  prodigy=r.random()<.00016
  talent=max(-18,min(15,r.gauss(0,6.0)))
  if prodigy:talent+=r.uniform(14,19)
  infra=self.countries[country]['infra']
  caps=[max(45,min(100,r.gauss(76.5+talent+2.4*(infra-1),7.0))) for _ in ATTRS]
  # Archetype mappings corrected for the current 15-attribute scheme.
  choices={'Power':(0,1),'Precision':(1,3),'Short Game':(4,5,6),
           'Technician':(9,10,11),'Shotmaker':(0,2,3),'All Rounder':()}
  for idx in choices.get(arch,()):caps[idx]=min(100,caps[idx]+r.uniform(6,11))
  for j in (A['composure'],A['resilience'],A['management']):
   caps[j]=min(100,max(40,caps[j]+r.gauss(0,4)))
  # Development timing varies by individual; outliers can still peak earlier
  # or later, independent of whether they are prodigies.
  physical_peak=max(27,min(38,round(r.gauss(32.0,2.6))))
  technical_peak=max(30,min(43,round(r.gauss(36.0,3.0))))
  mental_peak=max(35,min(51,round(r.gauss(42.0,4.0))))
  readiness=max(-.045,min(.075,r.gauss(.005,.031)))
  if prodigy: readiness+=r.uniform(.11,.16)
  growth_rate=max(.70,min(1.45,r.gauss(1.0,.15)))
  if prodigy: growth_rate=min(1.55,growth_rate+r.uniform(.08,.22))
  attrs=[]
  for j,cap in enumerate(caps):
   if j in (A['drive_power'],A['stamina'],A['recovery']):
    ratio=.795 + min(max(age-18,0),13)*.014
    if age>physical_peak:ratio-=.011*(age-physical_peak)
   elif j==A['injury_resistance']:
    ratio=.94 # mostly innate and not ordinarily trainable
   elif j in (A['composure'],A['resilience'],A['management']):
    ratio=.76+min(max(age-18,0),24)*.0085
    if age>mental_peak:ratio-=.003*(age-mental_peak)
   else:
    ratio=.79+min(max(age-18,0),18)*.0115
    if age>technical_peak:ratio-=.004*(age-technical_peak)
   ratio+=readiness + r.gauss(0,.015)
   # Prodigies have unusual EARLY technical/mental expression; a high ceiling
   # alone would not get them to the world stage before age 22.
   if prodigy and j in (A['composure'],A['resilience'],A['management']):ratio+=.025
   attrs.append(max(25,min(cap,cap*ratio+r.gauss(0,1.1))))
  # Mental stage has an innate foundation but major experience gradually helps.
  stage=round(max(0,min(100,r.gauss(50+talent*.50,16))))
  if prodigy:stage=max(stage,round(r.uniform(75,97)))
  # Initial world is already populated by veterans. New amateurs normally
  # start low, although an unprecedented amateur can be quickly selected for
  # majors and move up through competition.
  tier=r.choices([1,2,3,4],[.16,.28,.33,.23])[0] if initial else 4
  name=r.choice(FIRST)+' '+r.choice(LAST)
  g=Golfer(self.next_id,name,country,self.year-age,arch,tier,attrs,caps,stage,
   r.randrange(101),r.randrange(101),r.randrange(101),cash=r.uniform(15000,85000),
   readiness=readiness,growth_rate=growth_rate,physical_peak=physical_peak,
   technical_peak=technical_peak,mental_peak=mental_peak,
   physical_decline=r.uniform(.55,.95),technical_decline=r.uniform(.13,.32),
   mental_decline=r.uniform(.08,.19),prodigy=prodigy)
  self.golfers[g.id]=g;self.next_id+=1
  return g

 def _new_staff(self,role,assigned_to=-1):
  r=self.r;specs=(['course_strategy','green_reading','preparation','mental_support','communication'] if role=='caddie' else
   ['technical','putting','approach','mental','evaluation','communication'])
  quality=r.gauss(69,12);caps=[min(99,max(40,quality+r.gauss(6,13))) for _ in specs]
  skills=[max(30,min(c,c*r.uniform(.67,.96))) for c in caps]
  s=Staff(self.next_staff_id,r.choice(FIRST)+' '+r.choice(LAST),role,self.year-r.randint(24,58),r.choice(COUNTRY_CHOICES),r.choice(specs),skills,caps,assigned_to=assigned_to)
  self.staff[s.id]=s;self.next_staff_id+=1;return s

 def _assign_initial_staff(self):
  for g in self.golfers.values():
   g.coach_id=self._new_staff('coach',g.id).id
   g.caddie_id=self._new_staff('caddie',g.id).id

 def _ability(self,g):
  return (sum(g.attrs[i]*SKILL[i] for i in range(12)) -g.slump-.43*g.injury +g.form+.11*g.confidence-.035*g.fatigue)

 def _choose_field(self,tour,major,week):
  # Constraint: one tournament per golfer per week, and upper-end schedule cap.
  viable=[g for g in self.golfers.values() if not g.retired and g.annual_starts<27 and g.annual_major_starts<4 if major] if major else [g for g in self.golfers.values() if not g.retired and g.annual_starts<27]
  if major:
   # Majors draw principally from the strongest golfers in the world, regardless of home circuit.
   viable.sort(key=lambda g:self._ability(g)+self.r.gauss(0,3.7)+(.8 if g.tier==1 else 0),reverse=True)
  else:
   # Strong priority for level-appropriate members, regional fit and reasonable scheduling.
   def priority(g):
    diff=abs(g.tier-tour.tier)
    tier_bonus=9 if diff==0 else (-6 if diff==1 else -28)
    region=self.countries[g.country]['region']
    region_bonus=4.5 if region==tour.region or tour.region=='Global' else -3
    fatigue_cost=max(0,g.fatigue-20)*.12
    busy=g.annual_starts*0.42
    return self._ability(g)*.23+tier_bonus+region_bonus-fatigue_cost-busy+self.r.gauss(0,5)
   viable.sort(key=priority,reverse=True)
  result=[]
  for g in viable:
   if len(result)>=tour.slots:break
   if getattr(g,'last_week',-1)==week:continue # last_week intentionally optional for older saves
   # Actual choice based on approximate tier preference and finances; no fake automatic qualification here.
   if not major and abs(g.tier-tour.tier)>1:continue
   result.append(g)
  if len(result)<min(24,tour.slots):
   self.validation.append({'year':self.year,'event':tour.name,'issue':'too_few_entrants','count':len(result)})
  for g in result:
   g.annual_starts+=1
   if major:g.annual_major_starts+=1
   g.last_week=week
  return result

 def _schedule(self):
  schedule=[];top=self.tours[0]
  majors=[('Founders Masters',12,0,50,96),('World Open',21,None,60,144),('Heritage Championship',31,None,70,144),('Summit Invitational',41,1,70,144)]
  for name,week,cid,cut,fieldsize in majors:
   chosen=self.courses[cid] if cid is not None else self.r.choice(list(self.courses.values()))
   schedule.append((week,0,name,top,chosen,True,cut,fieldsize))
  for tour in self.tours:
   available=[c for c in self.courses.values() if tour.region=='Global' or self.countries[c.country]['region']==tour.region]
   if len(available)<4:available=list(self.courses.values())
   already=set()
   count=max(1,round(tour.events*self.events_scale))
   for i in range(count):
    week=3+round(i*42/max(1,count-1))+(tour.id*3)%6
    candidates=[c for c in available if c.id not in already] or available
    course=self.r.choice(candidates);already.add(course.id)
    schedule.append((week,1+tour.id,f'{tour.name} Event {i+1}',tour,course,False,65,tour.slots))
  return sorted(schedule,key=lambda x:(x[0],x[1]))

 def _initial_groups(self,field):
  # Weekday triples remain intact Thu-Fri; switch AM/PM waves and starting tees.
  players=list(field);self.r.shuffle(players)
  groups=[players[i:i+3] for i in range(0,len(players),3)]
  mid=(len(groups)+1)//2
  def cards(roundno):
   out=[]
   for ix,group in enumerate(groups):
    wave=0 if ix<mid else 1
    wave_index=ix if wave==0 else ix-mid
    start_tee=1 if wave_index%2==0 else 10
    pos=wave_index//2
    if roundno==2:
     wave=1-wave;start_tee=10 if start_tee==1 else 1
    start_slot=wave*34+pos # 34 slots gap: approximately 6.8hr for 12min groups
    out.append({'players':group,'start_slot':start_slot,'start_tee':start_tee,'group_id':ix})
   return out
  return cards(1),cards(2)

 def _weekend_groups(self,field,scores,roundno):
  # Worst scores first, low scores last, weekend twosomes. Ties broken by prior round
  # completion order recorded in prev_order (first-in-last-out).
  order=sorted(field,key=lambda g:(scores[g.id]['total'],scores[g.id].get('prev_order',0)),reverse=True)
  if len(order)%2:
   groups=[[order[0]]]+[order[i:i+2] for i in range(1,len(order),2)]
  else:groups=[order[i:i+2] for i in range(0,len(order),2)]
  return [{'players':group,'start_slot':i,'start_tee':1,'group_id':i} for i,group in enumerate(groups)]

 def _hole_quality(self,g,hole,major,rd,partner_aura=0,weather=0):
  z=g.attrs;ref=70
  # Hole-specific shot profile with sensible technical specialization.
  if hole.par==3:
   technical=(.07*z[0]+.12*z[2]+.50*z[3]+.05*z[4]+.20*z[6]+.06*z[11])
  elif hole.par==5:
   technical=(.20*z[0]+.09*z[1]+.22*z[2]+.20*z[3]+.08*z[4]+.17*z[6]+.04*z[11])
  else:
   technical=(.11*z[0]+.18*z[1]+.07*z[2]+.30*z[3]+.12*z[4]+.18*z[6]+.04*z[11])
  precision=z[1]-ref;recovery=z[5]-ref
  fit=precision*(.6-hole.width)*.09+recovery*(hole.hazard-.5)*.055
  distance=z[0]-ref
  fit+=distance*(min(1.2,max(-1.2,(hole.yards-{3:180,4:430,5:560}[hole.par])/120)))*.045
  putting_effect=(z[6]-ref)*(hole.green-.5)*.036
  c=self.staff[g.caddie_id]
  staff_quality=((c.skills[0]-65)*.017+(c.skills[1]-65)*.013+(c.skills[2]-65)*.009)
  staff_quality*=.55+.005*g.relationship
  course_know=math.log1p(g.visited.get(hole.number+10000*self.current_course_id,0))*.13
  mental_stage=(g.stage-50)*.035 if major else 0
  # Day/round pressure comes later because it requires live scoreboard context.
  quality=technical-ref+fit+putting_effect+staff_quality+course_know+mental_stage
  quality+=g.form+.10*g.confidence-g.slump-.50*g.injury-.026*g.fatigue+weather
  quality-=max(0,partner_aura)*(max(0,65-z[9]))*.004
  return quality

 def _score_hole(self,quality,hole,psych_shift=0,major=False):
  r=self.r;quality+=psych_shift
  setup_difficulty=hole.diff+.65+(.65 if major else 0.)
  eagle,birdie,bogey,double,triple=BASE_PROB[hole.par]
  # 1 quality point ~0.11 expected strokes per 18 holes, close to early calibration target.
  birdie=max(.018,min(.70,birdie+.0038*quality-.046*setup_difficulty))
  bogey=max(.025,min(.53,bogey-.0026*quality+.056*setup_difficulty))
  double=max(.002,min(.14,double-.00040*quality+.016*setup_difficulty+hole.hazard*.004))
  triple=max(.0001,min(.040,triple-.00007*quality+.003*setup_difficulty))
  eagle=max(0,min(.15,eagle+.00060*quality if hole.par==5 else eagle+.00008*quality))
  x=r.random()
  if x<eagle:return -2
  x-=eagle
  if x<birdie:return -1
  x-=birdie
  if x<bogey:return 1
  x-=bogey
  if x<double:return 2
  x-=double
  if x<triple:return 3
  return 0

 def _play_round(self,field,groups,scores,rd,course,major,cut_target,record_audit=False):
  # Every group moves through 18 holes in tee-time order. A tee-10 group plays
  # 10..18, then 1..9. Pressure is computed from the leaderboard AS OF that slot.
  r=self.r
  for g in field:
   scores[g.id]['current_holes']=0
  heap=[];schedule_seen=[];pressure_cut=0;pressure_lead=0;first_record=[]
  for k,group in enumerate(groups):
   heapq.heappush(heap,(group['start_slot'],k,0))
   schedule_seen.append({'round':rd,'pairing_id':k,'tee':group['start_tee'],'tee_slot':group['start_slot'],
    'golfer_ids':[g.id for g in group['players']]})
  hole_pars=[h.par for h in course.holes]
  projected_cut=0;live_leader=0;processed=0;last_group_finished=[]
  while heap:
   slot,k,step=heapq.heappop(heap);group=groups[k]
   hole_idx=(group['start_tee']-1+step)%18;hole=course.holes[hole_idx]
   if rd==2 and processed%18==0:
    # Live cut projection from only the strokes already played, never future results.
    all_vals=sorted(scores[g.id]['total']-scores[g.id]['par_played'] for g in field)
    projected_cut=all_vals[min(cut_target-1,len(all_vals)-1)]
   if rd==4 and processed%8==0:
    live_leader=min(scores[g.id]['total']-scores[g.id]['par_played'] for g in field)
   # Snapshot BEFORE anyone in the same pair/triple scores this hole.
   outcomes=[]
   for g in group['players']:
    sg=scores[g.id];hplayed=sg['current_holes'];diff=sg['total']-sg['par_played']
    cut_pressure=(rd==2 and step>=12 and abs(diff-projected_cut)<=2.5)
    lead_pressure=(rd==4 and step>=9 and diff-live_leader<=3)
    # Pairing with a decorated winner has a small intimidation effect, only at majors.
    aura=max((min(8,other.majors)*.8 for other in group['players'] if other.id!=g.id),default=0) if major else 0
    weather=(.42 if (slot>35 and course.style=='Links') else 0) + (.25 if rd==3 and course.style=='Desert' else 0)
    q=self._hole_quality(g,hole,major,rd,aura,weather)
    # Mentally tough golfers respond better to the CUT and final-round lead pressure.
    mind=(g.attrs[A['composure']]-50)*(.085 if lead_pressure else .055 if cut_pressure else 0)
    if step>0 and sg['last_hole']>=2:
     mind+=(g.attrs[A['resilience']]-50)*.038
    outcomes.append((g,self._score_hole(q,hole,mind,major),cut_pressure,lead_pressure,diff))
   for g,relative,is_cut,is_lead,diff in outcomes:
    sg=scores[g.id];strokes=hole.par+relative
    sg['total']+=strokes;sg['par_played']+=hole.par;sg['round_scores'][rd-1]+=strokes
    sg['current_holes']+=1;sg['last_hole']=relative
    if relative<0:sg['birdies']+=1
    if relative>=2:sg['doubles']+=1
    if strokes<course.hole_records[hole_idx]:
     course.hole_records[hole_idx]=strokes
    if is_cut:pressure_cut+=1
    if is_lead:pressure_lead+=1
    if record_audit:
     first_record.append({'round':rd,'minute_slot':slot,'pairing':k,'player_id':g.id,'golfer':g.name,
      'physical_hole':hole.number,'par':hole.par,'strokes':strokes,
      'score_to_par_after':sg['total']-sg['par_played'],
      'near_projected_cut':bool(is_cut),'near_live_lead':bool(is_lead),
      'projected_cut_to_par':projected_cut if rd==2 else None})
   if step==17:
    for g in group['players']:
     sg=scores[g.id];sg['prev_order']=processed
     if sg['round_scores'][rd-1]<course.record:
      course.record=sg['round_scores'][rd-1];course.record_holder=g.id;course.record_year=self.year
   else:
    heapq.heappush(heap,(slot+1,k,step+1))
   processed+=1
  return {'pairings':schedule_seen,'cut_pressure_holes':pressure_cut,'lead_pressure_holes':pressure_lead,'hole_audit':first_record}

 def _simulate_event(self,info):
  week,_,name,tour,course,major,cut_number,field_size=info
  # Major has its own field-size convention.
  original_slots=tour.slots
  if major:tour.slots=field_size
  field=self._choose_field(tour,major,week)
  tour.slots=original_slots
  if len(field)<3:return
  self.current_course_id=course.id
  scores={g.id:{'total':0,'round_scores':[0,0,0,0], 'current_holes':0,'par_played':0,'last_hole':0,'birdies':0,'doubles':0,'prev_order':0} for g in field}
  for g in field:
   g.visited[course.id]=g.visited.get(course.id,0)+1
   self.staff[g.caddie_id].visits[course.id]=self.staff[g.caddie_id].visits.get(course.id,0)+1
  r1,r2=self._initial_groups(field);pairings=[];featured=self.audit and self.year==2027 and name=='Founders Masters'
  v1=self._play_round(field,r1,scores,1,course,major,cut_number,featured);pairings.extend(v1['pairings'])
  v2=self._play_round(field,r2,scores,2,course,major,cut_number,featured);pairings.extend(v2['pairings'])
  after36={g.id:scores[g.id]['total'] for g in field}
  cutoff=sorted(after36.values())[min(cut_number,len(field))-1]
  survivors=[g for g in field if after36[g.id]<=cutoff]
  weekend3=self._weekend_groups(survivors,scores,3)
  v3=self._play_round(survivors,weekend3,scores,3,course,major,cut_number,featured);pairings.extend(v3['pairings'])
  weekend4=self._weekend_groups(survivors,scores,4)
  final_pairs=[x.id for x in weekend4[-1]['players']]
  # Verify leaders are in the final Sunday group according to their 54-hole standings.
  expected_last=[g.id for g in sorted(survivors,key=lambda g:scores[g.id]['total'])[:len(weekend4[-1]['players'])]]
  if any(scores[g.id]['total']<max(scores[self.golfers[pid].id]['total'] for pid in final_pairs) for g in survivors if g.id not in final_pairs):
   self.validation.append({'year':self.year,'event':name,'issue':'leaders_not_in_final_pairing'})
  v4=self._play_round(survivors,weekend4,scores,4,course,major,cut_number,featured);pairings.extend(v4['pairings'])
  final=sorted(survivors,key=lambda g:(scores[g.id]['total'],scores[g.id]['prev_order']))
  best=scores[final[0].id]['total']
  tied=[g for g in final if scores[g.id]['total']==best]
  playoff_holes=0
  if len(tied)>1:
   # Sudden death (fictional rule applied uniformly): no hole can end in unresolved tied champion.
   while len(tied)>1 and playoff_holes<24:
    hole=course.holes[playoff_holes%18];plays={g.id:self._score_hole(self._hole_quality(g,hole,major,4)+.8,hole,(g.attrs[A['composure']]-50)*.18,major) for g in tied}
    besthole=min(plays.values());tied=[g for g in tied if plays[g.id]==besthole];playoff_holes+=1
   if len(tied)>1:tied.sort(key=lambda g:g.id);tied=tied[:1]
  winner=tied[0]
  # Assert basic invariants.
  self.stats['holes_scored']+=sum(36 if g not in survivors else 72 for g in field)
  self.stats['cuts_made']+=len(survivors);self.stats['players_started']+=len(field)
  self.stats['projected_cut_pressure_holes']+=v2['cut_pressure_holes'];self.stats['lead_pressure_holes']+=v4['lead_pressure_holes']
  self.stats['playoff_events']+=(playoff_holes>0);self.stats['playoff_holes']+=playoff_holes
  self.stats['pairing_count']+=len(pairings)
  self.stats['hole_record_breaks']+=sum(1 for h in course.hole_records if h!=99) if course.visits==0 else 0
  if any(len(p['golfer_ids'])>3 if p['round']<=2 else len(p['golfer_ids'])>2 for p in pairings):
   self.validation.append({'year':self.year,'event':name,'issue':'oversized_pairing'})
  if len({p for card in pairings if card['round']==1 for p in card['golfer_ids']})!=len(field):
   self.validation.append({'year':self.year,'event':name,'issue':'duplicate_opening_pairing'})
  if len({p for card in pairings if card['round']==4 for p in card['golfer_ids']})!=len(survivors):
   self.validation.append({'year':self.year,'event':name,'issue':'duplicate_final_pairing'})
  # Award tied non-winning positions based on score; sole winner from playoff.
  rank=1;last=None;positions={}
  for i,g in enumerate(final):
   sc=scores[g.id]['total']
   if sc!=last:rank=i+1;last=sc
   positions[g.id]=rank
  positions[winner.id]=1
  if len(tied)==1 and playoff_holes:
   for g in final:
    if g.id!=winner.id and scores[g.id]['total']==best:positions[g.id]=2
  purse=tour.purse*(2.2 if major else 1)
  point_base=100 if major else tour.prestige*.72
  for g in field:
   g.starts+=1
   score=scores[g.id]
   if g.id in positions:
    g.cuts+=1;pos=positions[g.id]
    pts=point_base / (pos**.72)
    money=purse*(.16 if pos==1 else .065/pos**.75)
    g.season_points+=pts;g.earnings+=money;g.cash+=money
    if pos==1:
     g.wins+=1;g.season_wins+=1;g.confidence=min(9,g.confidence+2.5)
     if major:g.majors+=1
     self.staff[g.caddie_id].wins+=1;self.staff[g.coach_id].wins+=1
     if major:self.staff[g.caddie_id].majors+=1;self.staff[g.coach_id].majors+=1
     g.career.append({'year':self.year,'event':'Major victory' if major else 'Tournament victory','name':name,'course_id':course.id})
    elif pos<=10:g.confidence=min(9,g.confidence+.55)
   else:
    g.confidence=max(-9,g.confidence-.24)
   round_avg=sum(score['round_scores'])/(4 if g.id in positions else 2)
   # Actual form and physical toll, mean-reverting and largely non-scripted.
   performance=(course.par-round_avg)*.13
   g.form=max(-5,min(5,.86*g.form+.16*performance+self.r.gauss(0,.17)))
   g.fatigue=min(100,g.fatigue+(3.5 if major else 2.5))
   g.cash-=({1:3900,2:2100,3:1000,4:420}[tour.tier])
  course.visits+=1
  course.course_winners[winner.id]=course.course_winners.get(winner.id,0)+1
  record={'year':self.year,'week':week,'event':name,'tour':tour.name,'tier':tour.tier,'major':int(major),
   'course_id':course.id,'course':course.name,'winner_id':winner.id,'winner':winner.name,'winner_country':winner.country,
   'winning_score':best,'to_par':best-course.par*4,'course_par':course.par,'field':len(field),
   'made_cut':len(survivors),'cut_score':cutoff,'playoff_holes':playoff_holes,
   'cut_pressure_holes':v2['cut_pressure_holes'],'contending_pressure_holes':v4['lead_pressure_holes']}
  self.event_history.append(record)
  if major:
   self.major_history.append(record)
   # Full major leaderboard stays preserved in game history.
   for g in field:
    sg=scores[g.id];self.event_finishes.append({'year':self.year,'event':name,'golfer_id':g.id,'golfer':g.name,'country':g.country,
     'rank':positions.get(g.id),'cut':g.id in positions,'r1':sg['round_scores'][0],'r2':sg['round_scores'][1],
     'r3':sg['round_scores'][2] if g.id in positions else '', 'r4':sg['round_scores'][3] if g.id in positions else '',
     'total':sg['total'],'birdies':sg['birdies'],'doubles_or_worse':sg['doubles']})
  if featured:
   self.featured_tournament={'event':record,'final_sunday_pair':final_pairs,'expected_last_pair':expected_last,
    'pairings':pairings,'final_scores':sorted([{'golfer_id':g.id,'name':g.name,'r1':scores[g.id]['round_scores'][0],
     'r2':scores[g.id]['round_scores'][1],'r3':scores[g.id]['round_scores'][2],'r4':scores[g.id]['round_scores'][3],
     'total':scores[g.id]['total']} for g in survivors],key=lambda x:x['total']),
    'hole_audit':v1['hole_audit']+v2['hole_audit']+v3['hole_audit']+v4['hole_audit']}

 def _year_development(self,g):
  if g.retired:return
  age=self.year-g.born
  g.fatigue=max(0,g.fatigue-self.r.uniform(15,35))
  staff=self.staff[g.coach_id]
  coachbonus=1+max(-.1,min(.16,(mean(staff.skills)-65)*.006))
  high_level=1.065 if g.tier==1 else 1.035 if g.tier==2 else 1.0 if g.tier==3 else .95
  efficiency=coachbonus*high_level*g.growth_rate*(1-g.injury/45)*(1-g.fatigue/340)
  focus=self.r.randint(0,11)
  for j,cap in enumerate(g.caps):
   gap=max(0,cap-g.attrs[j])
   diminishing=(gap/(gap+9))**1.20 if gap>0 else 0
   if j in (A['drive_power'],A['stamina'],A['recovery']):
    if age<=22:base=3.3
    elif age<=27:base=1.65
    elif age<=g.physical_peak:base=.78
    else:base=0
    decline=(g.physical_decline+.115*(age-g.physical_peak)) if age>g.physical_peak else 0
   elif j==A['injury_resistance']:
    base=0;decline=max(0,age-39)*.08
   elif j in (A['composure'],A['resilience'],A['management']):
    if age<=25:base=.85
    elif age<=39:base=.61
    elif age<=g.mental_peak:base=.30
    else:base=0
    decline=(g.mental_decline+.028*(age-g.mental_peak)) if age>g.mental_peak else 0
   else:
    if age<=22:base=3.0
    elif age<=27:base=1.65
    elif age<=32:base=.95
    elif age<=g.technical_peak:base=.50
    else:base=0
    decline=(g.technical_decline+.045*(age-g.technical_peak)) if age>g.technical_peak else 0
   # Technical focus matters but does not violate hidden ceilings.
   focusfactor=1.30 if j==focus else 1.0
   growth=base*efficiency*diminishing*focusfactor
   noise=self.r.gauss(0,.07)
   g.attrs[j]=max(20,min(cap,g.attrs[j]+growth-decline+noise))
  # Major experience helps express innate temperament gradually, not rewrite it.
  g.stage=max(0,min(100,g.stage+min(1.0,g.annual_major_starts*.09)*(100-g.stage)/120))
  if g.slump_years>0:
   g.slump_years-=1;g.slump=max(0,g.slump-self.r.uniform(1.1,3.5))
  elif self.r.random()<.024:
   g.slump=self.r.uniform(2.5,8);g.slump_years=self.r.choice([1,1,2,3]);g.career.append({'year':self.year,'event':'Technical slump','severity':round(g.slump,1)})
   self.stats['slumps']+=1
  susceptibility=1+(65-g.durability)/150
  if self.r.random()<(.019+max(0,age-32)*.002)*susceptibility:
   g.injury=min(18,g.injury+self.r.uniform(2,9));g.career.append({'year':self.year,'event':'Injury','severity':round(g.injury,1)})
   self.stats['injuries']+=1
  g.injury=max(0,g.injury-self.r.uniform(1.0,4))
  g.confidence*=.63;g.form*=.4
  g.cash-=({1:75000,2:32000,3:15000,4:8000}[g.tier])
  if g.cash<0:g.confidence=max(-9,g.confidence-1.0)
  if age>=51 or (age>=38 and self.r.random()<.055+(age-38)*.016) or (age>=29 and g.cash< -140000):
   g.retired=True;g.career.append({'year':self.year,'event':'Retired','age':age});self.stats['retirements']+=1
  if not g.retired and self.r.random()<.052:
   if self.r.random()<.5:
    old=self.staff[g.caddie_id];old.assigned_to=-1
    g.caddie_id=self._new_staff('caddie',g.id).id
   else:
    old=self.staff[g.coach_id];old.assigned_to=-1
    g.coach_id=self._new_staff('coach',g.id).id
   g.relationship=22;g.career.append({'year':self.year,'event':'Staff change'})
  else:g.relationship=min(100,g.relationship+4)

 def _tour_moves(self):
  by=defaultdict(list)
  for g in self.golfers.values():
   if not g.retired:by[g.tier].append(g)
  # Simplified earned advancement: AI accepts offers based on finances, age, skill, and risk.
  for tier,golfers in by.items():
   golfers.sort(key=lambda x:x.season_points,reverse=True)
   for idx,g in enumerate(golfers):
    previous=g.tier;percentile=idx/max(1,len(golfers))
    if tier>1 and percentile <({2:.15,3:.14,4:.16}[tier]):
     chance=.65+.0025*g.risk +(.1 if g.cash>50000 else -.12)
     if self.r.random()<chance:g.tier-=1
    elif tier<4 and percentile>({1:.89,2:.88,3:.86}[tier]) and g.season_points<20:g.tier+=1
    if g.tier!=previous:
     g.career.append({'year':self.year,'event':'Promoted' if g.tier<previous else 'Relegated','from':previous,'to':g.tier})
     self.stats['promotions' if g.tier<previous else 'relegations']+=1

 def _evolve_countries(self):
  premier=Counter(g.country for g in self.golfers.values() if not g.retired and g.tier==1)
  winners=Counter(e['winner_country'] for e in self.major_history if self.year-7<=e['year']<=self.year)
  for name,v in self.countries.items():
   old=v['infra']; stars=premier[name]; champs=winners[name]
   # Role models last several seasons, encouraging junior participation and investment.
   v['role_models']=.87*v['role_models']+.025*stars+.16*champs
   if self.r.random()<.025:v['investment']+=self.r.uniform(.08,.24)
   if self.r.random()<.013:v['investment']-=self.r.uniform(.07,.20)
   v['investment']*=.90
   delta=.018*(v['base']-old)+.018*(v['role_models']-.65)+.08*v['investment']+self.r.gauss(0,.013)
   v['infra']=max(.40,min(1.85,old+delta))
   self.countries_history.append({'year':self.year,'country':name,'infrastructure':round(v['infra'],4),
    'premier_golfers':stars,'major_winners_last8y':champs,'development_change':round(delta,4)})

 def _rank_and_archive(self):
  active=[g for g in self.golfers.values() if not g.retired]
  active.sort(key=lambda g:g.season_points+.36*g.last_points,reverse=True)
  for rank,g in enumerate(active,1):g.rank=rank;g.peak_rank=min(g.peak_rank,rank)
  majors=[e for e in self.major_history if e['year']==self.year]
  no1=active[0] if active else None
  self.world_years.append({'year':self.year,'world_no1':no1.id if no1 else 0,
   'world_no1_name':no1.name if no1 else '',
   'unique_major_winners':len({e['winner_id'] for e in majors}),
   'major_winners':' / '.join(e['winner'] for e in majors),
   'active_golfers':len(active),'countries_top50':len({g.country for g in active[:50]})})
  for g in active:
   g.last_points=g.season_points;g.season_points=0;g.season_wins=0;g.annual_starts=0;g.annual_major_starts=0;g.fatigue*=.35
   g.last_week=-1

 def run(self,years=30,verbose=False):
  start=time.perf_counter()
  for i in range(years):
   for ev in self._schedule():self._simulate_event(ev)
   self._tour_moves();self._rank_and_archive()
   for g in tuple(self.golfers.values()):self._year_development(g)
   num=sum(not g.retired for g in self.golfers.values())
   for _ in range(max(0,self.population-num)):
    g=self._create_golfer();g.coach_id=self._new_staff('coach',g.id).id;g.caddie_id=self._new_staff('caddie',g.id).id
   self._evolve_countries()
   if verbose: print(f'seed={self.seed} year={self.year} events={len(self.event_history)} golfers={len(self.golfers)} time={time.perf_counter()-start:.1f}s',flush=True)
   self.year+=1
  self.stats['runtime_seconds']=round(time.perf_counter()-start,3)
  return self

 def summary(self):
  ctr=Counter(e['winner_id'] for e in self.major_history)
  winctr=Counter(e['winner_id'] for e in self.event_history)
  no1=Counter(y['world_no1'] for y in self.world_years)
  top=sorted(ctr.items(),key=lambda x:-x[1])
  scores=[e['to_par'] for e in self.event_history]
  majorscores=[e['to_par'] for e in self.major_history]
  country_first={}
  for m in self.major_history:
   country_first.setdefault(m['winner_country'],m['year'])
  return {'seed':self.seed,'years':len(self.world_years),'start_year':2027,'end_year':self.year-1,
   'initial_active_population':self.population,'generated_golfers':len(self.golfers),
   'active_final':sum(not g.retired for g in self.golfers.values()),'total_tournaments':len(self.event_history),
   'majors':len(self.major_history),'courses':len(self.courses),'courses_used':sum(c.visits>0 for c in self.courses.values()),
   'major_champions_unique':len(ctr),'most_majors':max(ctr.values(),default=0),
   'most_total_wins':max(winctr.values(),default=0),
   'top_major_champions':[{'id':gid,'name':self.golfers[gid].name,'country':self.golfers[gid].country,'majors':val,
    'all_tour_wins':winctr[gid]} for gid,val in top[:12]],
   'most_years_world_no1':max(no1.values(),default=0),
   'top_world_no1':[{'id':gid,'name':self.golfers[gid].name,'years':years,'majors':ctr[gid]} for gid,years in no1.most_common(5)],
   'major_winner_countries':len(set(x['winner_country'] for x in self.major_history)),
   'first_major_by_country':country_first,
   'avg_major_winning_to_par':round(mean(majorscores),2) if majorscores else None,
   'range_major_winning_to_par':[min(majorscores),max(majorscores)] if majorscores else [],
   'mean_all_event_winning_to_par':round(mean(scores),2) if scores else None,
   'fixed_course_series':{'Founders Masters':len({e['course_id'] for e in self.major_history if e['event']=='Founders Masters'}),
    'Summit Invitational':len({e['course_id'] for e in self.major_history if e['event']=='Summit Invitational'})},
   'rotating_series':{'World Open':len({e['course_id'] for e in self.major_history if e['event']=='World Open'}),
    'Heritage Championship':len({e['course_id'] for e in self.major_history if e['event']=='Heritage Championship'})},
   'stats':dict(self.stats),'validation_errors':self.validation[:30],'validation_error_count':len(self.validation)}

 def export(self,root):
  root=Path(root);root.mkdir(parents=True,exist_ok=True)
  def csv_write(name,rows):
   if not rows:return
   with (root/name).open('w',newline='',encoding='utf8') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
  csv_write('events.csv',self.event_history)
  csv_write('majors_full_results.csv',self.event_finishes)
  csv_write('world_seasons.csv',self.world_years)
  csv_write('country_development.csv',self.countries_history)
  csv_write('courses.csv',[{'id':c.id,'name':c.name,'country':c.country,'style':c.style,'par':c.par,'length':c.length,
   'visits':c.visits,'course_record':c.record if c.record<999 else '',
   'record_holder':self.golfers[c.record_holder].name if c.record_holder>0 else '',
   'record_year':c.record_year,'hole_records':';'.join(map(str,c.hole_records))} for c in self.courses.values()])
  csv_write('golfers.csv',[{'id':g.id,'name':g.name,'country':g.country,'age':self.year-g.born,'archetype':g.archetype,
   'tier':g.tier,'retired':g.retired,'wins':g.wins,'majors':g.majors,'starts':g.starts,'cuts':g.cuts,
   'peak_rank':g.peak_rank,'career_earnings':round(g.earnings,2),'remaining_cash':round(g.cash,2),
   'stage_temperament':g.stage,'prodigy_candidate':int(g.prodigy),'physical_peak':g.physical_peak,'technical_peak':g.technical_peak,'mental_peak':g.mental_peak,'coach_id':g.coach_id,'caddie_id':g.caddie_id} for g in self.golfers.values()])
  csv_write('staff.csv',[{'id':s.id,'name':s.name,'role':s.role,'born':s.born,'country':s.country,'archetype':s.archetype,
   'tour_wins_associated':s.wins,'majors_associated':s.majors,'assigned_to':s.assigned_to} for s in self.staff.values()])
  with gzip.open(root/'career_events.json.gz','wt',encoding='utf8') as f:
   json.dump({str(g.id):g.career for g in self.golfers.values() if g.career},f,separators=(',',':'))
  if self.featured_tournament:
   with gzip.open(root/'featured_major_hole_audit.json.gz','wt',encoding='utf8') as f:json.dump(self.featured_tournament,f,separators=(',',':'))
  out=self.summary()
  (root/'summary.json').write_text(json.dumps(out,indent=2),encoding='utf8')
  return out

def main():
 p=argparse.ArgumentParser();p.add_argument('--years',type=int,default=30);p.add_argument('--seed',type=int,default=42)
 p.add_argument('--population',type=int,default=1700);p.add_argument('--events-scale',type=float,default=1.)
 p.add_argument('--out',type=str,default='results_v02');p.add_argument('--quiet',action='store_true')
 args=p.parse_args()
 world=World(args.seed,args.population,args.events_scale).run(args.years,verbose=not args.quiet)
 summary=world.export(args.out);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
