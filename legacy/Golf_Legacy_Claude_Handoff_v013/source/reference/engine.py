"""Golf Legacy: seeded, zero-dependency 30-year world simulation prototype.
Run: python engine.py --years 30 --seed 42 --out results
This is a testbed, not a calibrated golf prediction model.
"""
from __future__ import annotations
import argparse, csv, json, math, random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ATTRS=['distance','accuracy','approach','short_game','putting','management','composure','consistency']
WEIGHTS=[.11,.13,.26,.12,.20,.07,.06,.05]
REGIONS={
 'USA':('Americas',1.24,1.20,0.0), 'Canada':('Americas',.95,1.00,0.0), 'Mexico':('Americas',.72,.83,0.0),
 'Brazil':('Americas',.54,.70,.002), 'Argentina':('Americas',.70,.80,0.0), 'Colombia':('Americas',.62,.78,.005),
 'England':('Europe',1.02,1.10,0.0),'Scotland':('Europe',.88,1.06,0.0),'Ireland':('Europe',.85,1.03,0.0),
 'Spain':('Europe',.89,1.03,0.0),'Sweden':('Europe',.84,1.02,0.0),'Germany':('Europe',.78,.98,0.0),
 'France':('Europe',.81,.97,0.0),'Poland':('Europe',.52,.75,.012),'Turkey':('Europe',.49,.69,.008),
 'Japan':('Asia',1.04,1.08,0.0),'South Korea':('Asia',1.03,1.08,0.0),'China':('Asia',.59,.75,.012),
 'India':('Asia',.51,.72,.014),'Thailand':('Asia',.76,.90,.004),'Philippines':('Asia',.59,.79,.006),
 'Australia':('Oceania',.98,1.08,0.0),'New Zealand':('Oceania',.83,.98,0.0),
 'South Africa':('Africa',.96,1.07,0.0),'Morocco':('Africa',.42,.62,.012),'Kenya':('Africa',.44,.64,.014),
 'Nigeria':('Africa',.41,.60,.017),'Egypt':('Africa',.48,.68,.008),
}
FIRST=['Alex','Ben','Chris','Daniel','Ethan','Felix','George','Hugo','Ian','James','Kai','Leo','Marcus','Nathan','Oliver','Peter','Ryan','Samuel','Theo','Victor','William','Yuto','Min','Arjun','Luca','Mateo']
LAST=['Anderson','Bennett','Brooks','Carter','Diaz','Evans','Fischer','Grant','Hayes','Ito','Kim','Lewis','Miller','Nakamura','Ortiz','Price','Reed','Sato','Singh','Taylor','Walker','Young','Zhang','Silva','Okafor','Kowalski']
ARCHETYPES={'Power':(0,1),'Precision':(1,2),'Short Game':(3,4),'Technician':(5,7),'Shotmaker':(0,2),'All Rounder':()}

@dataclass
class Golfer:
 id:int; name:str; country:str; born:int; archetype:str; tier:int; attrs:list; ceilings:list
 form:float=0; slump:float=0; slump_years:int=0; injury:float=0; confidence:float=0; cash:float=15000; wins:int=0; majors:int=0
 starts:int=0; cuts:int=0; earnings:float=0; season_points:float=0; last_points:float=0
 career:list=field(default_factory=list); retired:bool=False; season_wins:int=0
 peak_rank:int=999999; rank:int=999999; nation_legacy:bool=False

@dataclass
class Course:
 id:int; name:str; country:str; style:str; par:int; length:int; difficulty:float; accuracy_bias:float; power_bias:float
 record:int=999; record_holder:int=-1; record_year:int=0; visits:int=0; editions:list=field(default_factory=list)

@dataclass
class Tour:
 id:int; name:str; region:str; tier:int; prestige:int; events:int; slots:int; purse:float

class World:
 def __init__(self,seed=42,population=1700,events_scale=1.):
  self.r=random.Random(seed);self.seed=seed;self.year=2027;self.events_scale=events_scale
  self.golfers={};self.courses={};self.tours=[];self.events=[];self.world_years=[];self.countries={}
  self.rising=[];self.nextid=1;self.countries_history=[]
  for c,(region,weight,infrastructure,growth) in REGIONS.items():
   self.countries[c]={'region':region,'weight':weight,'infrastructure':infrastructure,'base':infrastructure,'growth':growth,'stars':0,'wins':0,'investment':0.0}
  self._init_tours();self._init_courses();
  for _ in range(population):self._new_golfer(initial=True)

 def _init_tours(self):
  defs=[('Americas Premier','Americas',1,94,13,120,14000000),('Europe Premier','Europe',1,88,12,120,9000000),('Asia Pacific Premier','Asia',1,83,9,105,6000000),
   ('Americas Challenger','Americas',2,65,13,120,1200000),('Europe Challenger','Europe',2,61,12,120,1100000),('Asia Challenger','Asia',2,58,10,105,800000),
   ('Oceania Challenger','Oceania',2,55,7,100,650000),('Africa Challenger','Africa',2,54,7,100,600000),
   ('Americas Regional','Americas',3,39,10,100,180000),('Europe Regional','Europe',3,37,10,100,175000),('Asia Regional','Asia',3,37,9,100,150000),('Africa Regional','Africa',3,34,8,85,115000),
   ('Oceania Regional','Oceania',3,36,7,90,135000),('Global Mini Tour','Global',4,21,12,100,45000)]
  self.tours=[Tour(i,*d) for i,d in enumerate(defs)]

 def _init_courses(self):
  styles=['Links','Parkland','Desert','Mountain','Coastal','Heathland','Woodland']
  places=['Heritage','Royal','Pine','Valley','Summit','Highland','Oak','Riverside','Cedar','Golden','Bay','Stone','Emerald','Ridge','Lakes','Windward']
  endings=['Golf Club','Country Club','Links','Golf Resort','Championship Course','Golf Park']
  countries=list(self.countries)
  for i in range(240):
   c=countries[i%len(countries)];sty=self.r.choice(styles)
   par=self.r.choices([70,71,72],[2,2,6])[0];length=self.r.randrange(6350,7651,25)
   name=f'{self.r.choice(places)} {self.r.choice(places)} {self.r.choice(endings)} #{i+1}'
   self.courses[i]=Course(i,name,c,sty,par,length,self.r.uniform(-1.7,2.1),self.r.uniform(-1,1),self.r.uniform(-1,1))

 def _new_golfer(self,initial=False):
  r=self.r
  cs=list(self.countries);weights=[self.countries[c]['weight']*self.countries[c]['infrastructure'] for c in cs]
  c=r.choices(cs,weights)[0];a=r.choice(list(ARCHETYPES));region=self.countries[c]['region']
  birth=self.year-r.randint(18,40) if initial else self.year-18
  # Extremely strong prospects may arise without an imposed count or cooldown.
  talent=min(15,max(-16,r.gauss(0,6)))
  if r.random()<.003:talent+=r.uniform(12,22)
  infra=self.countries[c]['infrastructure']
  ceilings=[min(100,max(44,r.gauss(77+talent+2*(infra-1),8))) for _ in ATTRS]
  for idx in ARCHETYPES[a]:ceilings[idx]=min(100,ceilings[idx]+r.uniform(8,14))
  age=self.year-birth;development=min(.91,max(.35,.47+(age-18)*.025))
  attrs=[min(m,max(28,m*development+r.gauss(0,3))) for m in ceilings]
  g=Golfer(self.nextid,r.choice(FIRST)+' '+r.choice(LAST),c,birth,a,4 if not initial else r.choices([1,2,3,4],[.13,.25,.34,.28])[0],attrs,ceilings,cash=r.uniform(10000,80000))
  self.golfers[g.id]=g;self.nextid+=1
  return g

 def _ability(self,g):
  return sum(v*w for v,w in zip(g.attrs,WEIGHTS)) + g.form + g.confidence*.10 -g.injury*.55-g.slump

 def _choose_field(self,tour,seeded,major=False):
  eligible=[g for g in self.golfers.values() if not g.retired and (major or g.tier==tour.tier)]
  # Global events and cross-region invites; home-region membership preference.
  def utility(g):
   same=self.countries[g.country]['region']==tour.region or tour.region=='Global'
   return self._ability(g)+(3 if same else -2) + self.r.gauss(0,5) + (6 if major and g.tier==1 else 0)
  eligible.sort(key=utility,reverse=True)
  field=eligible[:tour.slots]
  if len(field)<tour.slots:
   others=[g for g in self.golfers.values() if not g.retired and g.id not in {x.id for x in field}]
   others.sort(key=utility,reverse=True);field+=others[:tour.slots-len(field)]
  return field

 def _round(self,g,course,round_no,major=False):
  r=self.r;abilities=self._ability(g)
  course_fit=(g.attrs[0]-65)*course.power_bias*.014+(g.attrs[1]-65)*course.accuracy_bias*.018
  skill=(abilities-68)*.115
  pressure=(g.attrs[6]-70)*.012 if major else 0
  sigma=max(2.2,3.6-(g.attrs[7]-60)*.010)
  # Common environmental shock influences entire field that round.
  value=course.par+course.difficulty+(course.length-6900)*.0018 -skill -course_fit-pressure+r.gauss(0,sigma)
  return max(course.par-13,min(course.par+21,round(value)))

 def _simulate_event(self,tour,course,week,major=False,series=''):
  field=self._choose_field(tour,week,major); scores={g.id:[] for g in field}
  for rn in range(4):
   active=field
   if rn==2:
    ordered=sorted(field,key=lambda g:sum(scores[g.id])); cutoff=sum(scores[ordered[min(69,len(ordered)-1)].id]);active=[g for g in field if sum(scores[g.id])<=cutoff]
   if rn>=2:active=[g for g in field if len(scores[g.id])==rn]
   for g in active:scores[g.id].append(self._round(g,course,rn,major))
  finalists=[g for g in field if len(scores[g.id])==4]
  finalists.sort(key=lambda g:(sum(scores[g.id]),self.r.random()))
  leader=finalists[0] if finalists else None
  purse=tour.purse*(2.2 if major else 1)*self.r.uniform(.87,1.13)
  points_base=(65 if major else tour.prestige*.62)
  course.visits+=1
  if leader:course.editions.append([self.year,series or tour.name,leader.id,sum(scores[leader.id])])
  for g in field:
   g.starts+=1;result=scores[g.id]
   if len(result)==4:
    g.cuts+=1;pos=finalists.index(g)+1
    point=points_base/(pos**.68)
    earn=purse*(.16 if pos==1 else .065/(pos**.75))
    g.season_points+=point;g.earnings+=earn;g.cash+=earn
    if pos==1:
     g.wins+=1;g.season_wins+=1;g.confidence=min(9,g.confidence+2.3)
     if major:g.majors+=1
    elif pos<=10:g.confidence=min(9,g.confidence+.6)
   else:pos=None;g.confidence=max(-9,g.confidence-.30)
   g.form=max(-6,min(6,.77*g.form+self.r.gauss(0,1.5)+(0.7 if pos is not None and pos<=15 else -.15)))
   # Record official competitive round scores (course configuration simplified in prototype).
   for score in result:
    if score<course.record:course.record=score;course.record_holder=g.id;course.record_year=self.year
   g.cash-=450 if tour.tier==4 else (2600 if tour.tier==1 else 1250)
  event={'year':self.year,'week':week,'event':series or tour.name+' Open','tour':tour.name,'tier':tour.tier,'major':major,
         'course_id':course.id,'course':course.name,'winner_id':leader.id if leader else None,
         'winner':leader.name if leader else None,'winner_country':leader.country if leader else None,
         'winning_score':sum(scores[leader.id]) if leader else None,'par_total':course.par*4,
         'field_size':len(field)}
  self.events.append(event)
  return event

 def _courses_for_tour(self,tour):
  regional=[c for c in self.courses.values() if self.countries[c.country]['region']==tour.region]
  if tour.region=='Global' or len(regional)<4:regional=list(self.courses.values())
  return regional

 def _year_events(self):
  # Two fixed-course majors and two rotating majors; not all editions use same venue.
  majors=[('Founders Masters',True,0),('World Open',False,None),('Heritage Championship',False,None),('Summit Invitational',True,1)]
  top=self.tours[0]
  for i,(name,fixed,id_) in enumerate(majors):
   course=self.courses[id_] if fixed else self.r.choice(list(self.courses.values()))
   yield(top,course,12+i*9,True,name)
  for tour in self.tours:
   courses=self._courses_for_tour(tour)
   used=set()
   for n in range(max(1,round(tour.events*self.events_scale))):
    options=[c for c in courses if c.id not in used] or courses
    course=self.r.choice(options);used.add(course.id)
    yield(tour,course,2+n*3%49,False,f'{tour.name} Event {n+1}')

 def _development(self,g):
  age=self.year-g.born
  if g.retired:return
  base=1.7 if age<23 else (1.15 if age<30 else (.55 if age<36 else -.45-(age-36)*.085))
  modifier={1:1.11,2:1.05,3:1.0,4:.91}[g.tier]
  challenge=1 if abs(self._ability(g)-(85 if g.tier==1 else 72 if g.tier==2 else 61 if g.tier==3 else 50))<16 else .84
  training=max(.20,modifier*challenge*(1-max(0,g.injury)/32))
  trained=self.r.randrange(len(ATTRS))
  for j,m in enumerate(g.ceilings):
   gap=max(0,m-g.attrs[j]);factor=(gap/max(m,1))**.85
   gain=max(0,base)*training*(2.0 if j==trained else .62)*factor*3.2
   loss=max(0,-base)*(.65 if j in (5,6) else 1.1)
   g.attrs[j]=min(m,max(20,g.attrs[j]+gain-loss+self.r.gauss(0,.14)))
  # Occasional shocks; causes recorded before effects, so history can explain slumps.
  if g.slump_years>0:
   g.slump_years-=1;g.slump=max(0,g.slump-self.r.uniform(1.0,4.0))
  elif self.r.random()<.028:
   g.slump=self.r.uniform(3,10);g.slump_years=self.r.choice([1,1,2,3]);g.career.append({'year':self.year,'event':'Technical slump','severity':round(g.slump,1)})
  if self.r.random()<(.022+max(0,age-32)*.002):
   g.injury=min(18,g.injury+self.r.uniform(2,11));g.career.append({'year':self.year,'event':'Injury','severity':round(g.injury,1)})
  g.injury=max(0,g.injury-self.r.uniform(1.5,5))
  g.confidence*=.62;g.form*=.4
  g.cash-=({1:85000,2:37000,3:18000,4:8000}[g.tier])
  if g.cash<0:g.confidence=max(-9,g.confidence-1.1)
  if age>=51 or (age>=39 and self.r.random()<.05+(age-39)*.012) or (age>=30 and g.cash < -110000):
   g.retired=True;g.career.append({'year':self.year,'event':'Retired','age':age})

 def _tour_moves(self):
  by_tier=defaultdict(list)
  for g in self.golfers.values():
   if not g.retired:by_tier[g.tier].append(g)
  for tier,golfers in by_tier.items():
   golfers.sort(key=lambda x:x.season_points,reverse=True)
   for idx,g in enumerate(golfers):
    old=g.tier
    pct=idx/max(1,len(golfers))
    if tier>1 and pct<({2:.19,3:.17,4:.18}[tier]) and (g.cash>0 or self.r.random()<.85):g.tier-=1
    elif tier<4 and pct>({1:.90,2:.88,3:.86}[tier]) and g.season_points<12:g.tier+=1
    if old!=g.tier:g.career.append({'year':self.year,'event':'Promoted' if g.tier<old else 'Relegated','from':old,'to':g.tier})

 def _country_evolution(self):
  # Results boost programs with lag; investment shocks and mean reversion prevent permanent monotonic growth.
  elite=Counter(g.country for g in self.golfers.values() if not g.retired and g.tier==1)
  for c,v in self.countries.items():
   visits=elite[c]
   program_boost=.007*min(12,visits)+v['growth']
   if self.r.random()<.018:v['investment']+=self.r.uniform(.06,.16)
   v['investment']*=.94
   v['infrastructure']+=.010*(v['base']-v['infrastructure'])+program_boost*.22+v['investment']*.04+self.r.gauss(0,.009)
   v['infrastructure']=max(.38,min(1.8,v['infrastructure']))
   self.countries_history.append({'year':self.year,'country':c,'infrastructure':round(v['infrastructure'],3),'premier_golfers':visits})

 def _rank_and_archive(self):
  active=[g for g in self.golfers.values() if not g.retired]
  active.sort(key=lambda g:g.season_points+.35*g.last_points,reverse=True)
  for i,g in enumerate(active):g.rank=i+1;g.peak_rank=min(g.peak_rank,g.rank)
  champions=[e for e in self.events if e['year']==self.year and e['major']]
  leader=active[0] if active else None
  self.world_years.append({'year':self.year,'world_no1':leader.id if leader else None,'world_no1_name':leader.name if leader else None,
   'unique_major_winners':len({e['winner_id'] for e in champions}), 'major_winners':[e['winner'] for e in champions],
   'active_golfers':len(active),'countries_top50':len({g.country for g in active[:50]})})
  for g in active:
   if g.season_wins:g.career.append({'year':self.year,'event':'Season victories','count':g.season_wins})
   g.last_points=g.season_points;g.season_points=0;g.season_wins=0

 def step(self):
  for _,course,week,major,name in self._year_events():self._simulate_event(_,course,week,major,name)
  self._rank_and_archive();self._tour_moves()
  for g in list(self.golfers.values()):self._development(g)
  # Maintain roughly steady active population with youth replacement.
  desired=self.initial_population
  n=sum(not g.retired for g in self.golfers.values())
  for _ in range(max(0,desired-n)):self._new_golfer()
  self._country_evolution();self.year+=1

 def run(self,years=30):
  self.initial_population=sum(not g.retired for g in self.golfers.values())
  for _ in range(years):self.step()
  return self

 def export(self,out):
  out=Path(out);out.mkdir(parents=True,exist_ok=True)
  def csvout(name,items):
   if not items:return
   with (out/name).open('w',newline='',encoding='utf8') as f:
    writer=csv.DictWriter(f,fieldnames=list(items[0]));writer.writeheader();writer.writerows(items)
  csvout('tournaments.csv',self.events)
  csvout('world_seasons.csv',self.world_years)
  csvout('country_development.csv',self.countries_history)
  csvout('courses.csv',[{'id':c.id,'name':c.name,'country':c.country,'style':c.style,'par':c.par,'length':c.length,'visits':c.visits,'record':c.record if c.record<999 else '', 'record_holder':self.golfers[c.record_holder].name if c.record_holder>=0 else '', 'record_year':c.record_year} for c in self.courses.values()])
  csvout('golfers.csv',[{'id':g.id,'name':g.name,'country':g.country,'archetype':g.archetype,'birth_year':g.born,'current_tier':g.tier,'retired':g.retired,'wins':g.wins,'majors':g.majors,'starts':g.starts,'cuts':g.cuts,'peak_rank':g.peak_rank,'earnings':round(g.earnings,2),'cash':round(g.cash,2),'events':len(g.career)} for g in self.golfers.values()])
  with (out/'career_events.json').open('w',encoding='utf8') as f:json.dump({g.id:g.career for g in self.golfers.values() if g.career},f,separators=(',',':'))
  with (out/'course_editions.json').open('w',encoding='utf8') as f:json.dump({c.id:c.editions for c in self.courses.values()},f,separators=(',',':'))
  majorw=Counter(e['winner_id'] for e in self.events if e['major'])
  major_champs=sorted(majorw.items(),key=lambda x:-x[1])
  yrs=len(self.world_years)
  report={'seed':self.seed,'years':yrs,'initial_golfers':self.initial_population,'total_generated_golfers':len(self.golfers),
   'tournaments':len(self.events),'course_count':len(self.courses),'courses_used':sum(c.visits>0 for c in self.courses.values()),
   'major_winners_unique':len(majorw),'most_majors':major_champs[0][1] if major_champs else 0,
   'top_major_champions':[{'golfer':self.golfers[gid].name,'country':self.golfers[gid].country,'majors':num} for gid,num in major_champs[:15]],
   'most_tour_wins':max(g.wins for g in self.golfers.values()),
   'top_career_winners':[{'name':g.name,'country':g.country,'wins':g.wins,'majors':g.majors} for g in sorted(self.golfers.values(),key=lambda g:-g.wins)[:12]],
   'top50_country_count_by_year':[{'year':x['year'],'count':x['countries_top50']} for x in self.world_years],
   'slump_events':sum(1 for g in self.golfers.values() for e in g.career if e['event']=='Technical slump'),
   'injury_events':sum(1 for g in self.golfers.values() for e in g.career if e['event']=='Injury')}
  with (out/'summary.json').open('w',encoding='utf8') as f:json.dump(report,f,indent=2)
  return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--years',type=int,default=30);p.add_argument('--seed',type=int,default=42);p.add_argument('--population',type=int,default=1700);p.add_argument('--events-scale',type=float,default=1.0);p.add_argument('--out',default='results')
 args=p.parse_args();world=World(args.seed,args.population,args.events_scale).run(args.years);res=world.export(args.out);print(json.dumps(res,indent=2))
if __name__=='__main__':main()
