"""Golf Legacy v0.5: coherent starting cohorts and funded, auditable careers.

Working simulation model, not a validated real-world golf prediction model.
All economic figures are fictional scenario assumptions in USD-equivalent.
"""
from __future__ import annotations
import argparse,csv,gzip,heapq,json,math,random,sys,time
from collections import Counter,defaultdict
from pathlib import Path
from statistics import mean
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'economics'))
from career_economics import Economics,allocate_prizes,cents,ANNUAL_OVERHEAD,EVENT_COST,STATUS_ACTIVE,STATUS_RETIRED
import engine_v05_growth as growth
from engine_v03 import A

class World(growth.World):
 def __init__(self,*args,sponsorship=False,outside_work=True,bankroll_events=4,**kwargs):
  kwargs.setdefault('elite_curve',.03)
  super().__init__(*args,**kwargs)
  self.bankroll_events=bankroll_events;self.purse_audits=[];self.initialization_rows=[];self.training_exposure_by_id={};self.season_performance={}
  self.economics=Economics(self.seed,sponsorship=sponsorship,outside_work=outside_work)
  # Established membership is a noisy proxy for fictional prehistory, not random
  # placement unrelated to ability, and not a claim of simulated qualifying.
  r=random.Random(self.seed^0x51504)
  ordered=sorted(self.golfers.values(),key=lambda g:self._ability(g)+r.gauss(0,3.5),reverse=True)
  for i,g in enumerate(ordered):
   frac=i/max(1,len(ordered));g.tier=1 if frac<.16 else 2 if frac<.44 else 3 if frac<.77 else 4
   old=g.cash;g.cash=max(g.cash,ANNUAL_OVERHEAD[g.tier]+bankroll_events*EVENT_COST[g.tier])
   self.initialization_rows.append({'golfer_id':g.id,'age':self.year-g.born,'operating_tier':g.tier,
    'original_generated_savings':round(old,2),'opening_scenario_bankroll':round(g.cash,2),
    'note':'Established-world opening condition, not earned income or a later bailout'})
   self.economics.register(g,self.year,initial=True)
 def _year_development(self,g):
  saved_starts=g.annual_major_starts;saved_tier=g.tier;prior_slump=g.slump
  g.annual_major_starts=self.completed_major_starts.get(g.id,saved_starts)
  g.tier=self.economics.accounts[g.id].season_tier
  try:self._develop_attributes(g)
  finally:g.annual_major_starts=saved_starts;g.tier=saved_tier
  if prior_slump>0 and g.slump_years==0:
   g.slump=0.;g.career.append({'year':self.year,'event':'Recovered from technical slump','timing':'year_end'})
 def _rank_and_archive(self):
  start=len(self.annual_golfers)
  super()._rank_and_archive()
  for row in self.annual_golfers[start:]:
   g=self.golfers[row['golfer_id']];a=self.economics.accounts[g.id]
   row['operating_tier']=a.season_tier;row['economic_status']=a.status;row['closing_golf_bankroll']=g.cash
   row['funded_training_exposure']=self.training_exposure_by_id.get(g.id,0.)
   row['year_end_world_rank']=g.rank
 def run(self,years=30,verbose=False):
  start=time.perf_counter()
  for _ in range(years):
   season_players=[g for g in self.golfers.values() if not g.retired]
   for g in season_players:self.economics.begin_season(g,self.year)
   self.season_performance={g.id:{'starts':0,'cuts':0,'top10s':0,'rounds':0,'field_relative_strokes':0.,'tier_sum':0.} for g in season_players}
   last_week=-1
   for ev in self._schedule():
    week=ev[0]
    if week!=last_week:
     for g in season_players:self.economics.advance_to_week(g,self.year,week)
     last_week=week
    self._simulate_event(ev)
   for g in season_players:
    observed=self.season_performance[g.id]
    performance={'starts':observed['starts'],'rounds_observed':observed['rounds'],
     'cut_rate':observed['cuts']/observed['starts'] if observed['starts'] else None,
     'field_relative_strokes_per_round':observed['field_relative_strokes']/observed['rounds'] if observed['rounds'] else None,
     'top10s':observed['top10s'],'mean_event_tier':observed['tier_sum']/observed['starts'] if observed['starts'] else None,
     'operating_tier':self.economics.accounts[g.id].season_tier}
    row=self.economics.end_season(g,self.year,review=False,performance=performance)
    self.training_exposure_by_id[g.id]=row['training_exposure']
   self._tour_moves();self._rank_and_archive()
   for g in season_players:
    self._year_development(g)
    biological_exit=g.retired
    if biological_exit:self.economics.mark_retired(g,self.year,reason='Age-related career exit in the fictional lifecycle model')
    self.economics.review_career(g,self.year)
    if g.retired and not biological_exit:self.stats['retirements']+=1;self.stats['financial_career_exits']+=1
   num=sum(not g.retired for g in self.golfers.values())
   for _ in range(max(0,self.population-num)):
    g=self._create_golfer();g.coach_id=self._new_staff('coach',g.id).id;g.caddie_id=self._new_staff('caddie',g.id).id
    self.economics.register(g,self.year+1,initial=False)
   self._evolve_countries()
   if verbose:print(f'seed={self.seed} year={self.year} events={len(self.event_history)} golfers={len(self.golfers)} time={time.perf_counter()-start:.1f}s',flush=True)
   self.year+=1
  self.stats['runtime_seconds']=round(time.perf_counter()-start,3)
  return self
 def summary(self):
  out=super().summary();out['model_version']='0.5'
  out['calibration'].update({'initial_bankroll_reserved_events':self.bankroll_events,'initial_membership':'noisy skill-informed shares16/28/33/23 percent'})
  out['economics']=self.economics.validate(self.golfers)
  out['purse_conservation_errors']=sum(r['paid_cents']!=r['purse_cents'] for r in self.purse_audits)
  return out
 def export(self,root):
  out=super().export(root);self.economics.export(root)
  for name,rows in [('purse_audits.csv',self.purse_audits),('initialization.csv',self.initialization_rows)]:
   if rows:
    with (Path(root)/name).open('w',newline='',encoding='utf8') as f:
     writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
  return out

 def _choose_field(self,tour,major,week):
  # Constraint: one tournament per golfer per week, and upper-end schedule cap.
  viable=[g for g in self.golfers.values() if not g.retired and g.annual_starts<27 and g.annual_major_starts<4 if major] if major else [g for g in self.golfers.values() if not g.retired and g.annual_starts<27]
  viable=[g for g in viable if self.economics.can_start(g,tour.tier,self.year,week)]
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
  if len(result)<3:return []
  for g in result:
   if not self.economics.pay_entry(g,self.current_event_id,tour.tier,self.year,week):
    raise AssertionError('Selected golfer could not fund entry')
   g.annual_starts+=1
   if major:g.annual_major_starts+=1
   g.last_week=week
  self.event_shocks={g.id:self.r.gauss(0,self.event_noise)*self._consistency_scale(g) for g in result} if self.event_noise else {}
  if major:
   active=sorted((g for g in self.golfers.values() if not g.retired),key=self._ability,reverse=True)
   ranks={g.id:i+1 for i,g in enumerate(active)}
   for g in result:self.major_entry_context.append({'year':self.year,'week':week,'golfer_id':g.id,'ability_rank':ranks[g.id],
    'previous_world_rank':g.rank,'ability':round(self._ability(g),4),'age':self.year-g.born,'prodigy':int(g.prodigy),
    'injury':round(g.injury,3),'slump':round(g.slump,3),'form':round(g.form,3)})
  return result

 def _simulate_event(self,info):
  week,_,name,tour,course,major,cut_number,field_size=info
  self.current_event_id=f'{self.year}:{week}:{name}'
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
  payouts=allocate_prizes([g.id for g in final],scores,winner.id,purse)
  self.purse_audits.append({'year':self.year,'event_id':self.current_event_id,'purse':purse,
   'paid':sum(payouts.values()),'paid_cents':sum(cents(v) for v in payouts.values()),'purse_cents':cents(purse),'finishers':len(final)})
  round_field_means=[mean(sg['round_scores'][i] for sg in scores.values() if sg['round_scores'][i]>0) for i in range(4)]
  point_base=100 if major else tour.prestige*.72
  for g in field:
   g.starts+=1
   score=scores[g.id]
   perf=self.season_performance.setdefault(g.id,{'starts':0,'cuts':0,'top10s':0,'rounds':0,'field_relative_strokes':0.,'tier_sum':0.})
   perf['starts']+=1;perf['tier_sum']+=tour.tier;perf['cuts']+=int(g.id in positions);perf['top10s']+=int(positions.get(g.id,9999)<=10)
   # Compare common opening rounds only, not changing weekend survivor fields.
   for i,strokes in enumerate(score['round_scores'][:2]):
    if strokes>0:perf['rounds']+=1;perf['field_relative_strokes']+=round_field_means[i]-strokes
   if g.id in positions:
    g.cuts+=1;pos=positions[g.id]
    pts=point_base / (pos**.72)
    money=payouts[g.id]
    g.season_points+=pts
    self.economics.credit_prize(g,self.current_event_id,money,self.year,week)
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

 def _develop_attributes(self,g):
  if g.retired:return
  age=self.year-g.born
  g.fatigue=max(0,g.fatigue-self.r.uniform(15,35))
  staff=self.staff[g.coach_id]
  coachbonus=1+max(-.1,min(.16,(mean(staff.skills)-65)*.006))
  high_level=1.065 if g.tier==1 else 1.035 if g.tier==2 else 1.0 if g.tier==3 else .95
  efficiency=coachbonus*high_level*g.growth_rate*(1-g.injury/45)*(1-g.fatigue/340)*self.training_exposure_by_id.get(g.id,1.)
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
  if age>=51 or (age>=38 and self.r.random()<.055+(age-38)*.016):
   g.retired=True;self.stats['retirements']+=1
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
   if not g.retired and self.economics.accounts[g.id].status==STATUS_ACTIVE:by[g.tier].append(g)
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

def main():
 p=argparse.ArgumentParser();p.add_argument('--years',type=int,default=30);p.add_argument('--seed',type=int,default=707)
 p.add_argument('--population',type=int,default=1700);p.add_argument('--events-scale',type=float,default=1.)
 p.add_argument('--out',default='results_v05');p.add_argument('--quiet',action='store_true')
 p.add_argument('--elite-curve',type=float,default=.03);p.add_argument('--sponsorship',action='store_true',help='Enable optional passive income experiment; off by default')
 p.add_argument('--no-outside-work',action='store_true');p.add_argument('--bankroll-events',type=int,default=4)
 a=p.parse_args();w=World(a.seed,a.population,a.events_scale,elite_curve=a.elite_curve,sponsorship=a.sponsorship,
  outside_work=not a.no_outside_work,bankroll_events=a.bankroll_events).run(a.years,verbose=not a.quiet)
 print(json.dumps(w.export(a.out),indent=2))
if __name__=='__main__':main()
