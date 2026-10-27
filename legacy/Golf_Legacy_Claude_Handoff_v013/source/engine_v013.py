"""Golf Legacy v0.13 first scored-calendar integration: EXPERIMENTAL.

Built on frozen v0.7/v0.8 numerical performance models. Gate 1 supports
18/36/54/72 rounds, chronological tee slots, live cut/lead pressure, ties,
playoffs, purse reconciliation and permanent SQLite scorecards.
Gate 2 provides a provisional OWGR-style weekly ranking ledger.
Gate 3 provides provenance-based feeder-to-major qualification for targeted
fixtures, NOT yet full tour membership/Q-school/college/weekly AI planning.

Do NOT describe this as a completed 6,000-golfer or 60-year world.
"""
from __future__ import annotations
import argparse, csv, hashlib, heapq, json, math, random, time
from collections import Counter,defaultdict
from pathlib import Path
from statistics import mean
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'reference'))
from capacity_engine_v08 import World as ReferenceWorld
import engine_v03 as historical_base
from engine_v03 import A, Tour
# Additional host countries from the global calendar enter the same probabilistic
# talent population as existing v0.7 countries; their weights are fictional.
EXTRA_COUNTRIES={
 'Wales':('Europe',.60,.83,0.),'Chile':('Americas',.52,.75,0.),
 'Fiji':('Oceania',.18,.55,0.),'Papua New Guinea':('Oceania',.12,.46,0.),
}
for _country,_spec in EXTRA_COUNTRIES.items():
 if _country not in historical_base.REGIONS:
  historical_base.REGIONS[_country]=_spec
  historical_base.COUNTRY_CHOICES.append(_country)
from career_economics import allocate_prizes,cents
from calendar_generator_v011 import get_schedule as legacy_schedule,make_row,MAJORS
from rankings import RankingBook,tie_positions
from history_store import HistoryStore

MAJOR_WEEKS={14,19,24,30}
SPECIAL_PREMIER={
 'PREMIER_FLAGSHIP_AMERICAS':('Americas Premier','Americas',8,'Atlantic Invitational'),
 'PREMIER_FLAGSHIP_EUROPE':('Europe Premier','Europe',35,'Continental Classic'),
}


def slug(s):return s.upper().replace(' ','_')
def keyed_int(seed,*parts):
 d=hashlib.blake2b(':'.join(map(str,(seed,*parts))).encode(),digest_size=8).digest()
 return int.from_bytes(d,'big')


def revised_calendar(year,seed):
 """Build 40 tier 0/1 events: 4 majors + 8 flagship, 20 standard,
 8 opportunity. Post-major weeks 15/20/25/31 host opportunity events.
 All series identities, lengths and prize tiers remain stable across years.
 """
 rows=legacy_schedule(year,seed)
 for key,(tour,region,week,name) in SPECIAL_PREMIER.items():
  already={(r['tour'],r['week']) for r in rows if r['kind'] not in ('major','qualifying')}
  # A flagship owns its permanent week; ordinary events conflicting with it
  # are relocated below, after every fixed anchor has been placed.
  row=make_row(year,week,key,name,tour,region,1,'regular',f'{region} Tournament Course 34',
   'rotating','',72,120,anchor=True)
  rows.append(row)
 regulars=[r for r in rows if r['tier']==1]
 assert len(regulars)==36
 # Fixed post-major opportunity series stay the same identity every year.
 post_map={15:'TOUR_AMERICAS_PREMIER_01',20:'TOUR_EUROPE_PREMIER_01',
           25:'TOUR_ASIA_PACIFIC_PREMIER_01',31:'TOUR_EUROPE_PREMIER_02'}
 post_series=[]
 for week,series in post_map.items():
  matches=[r for r in regulars if r['series_id']==series]
  if len(matches)!=1:raise AssertionError('Missing stable opportunity series '+series)
  choice=matches[0];choice['week']=week
  choice['course']=f'{choice["region"]} Post Major Opportunity {week} Course'
  choice['event']=f'{choice["region"]} Week {week} Opportunity Open'
  choice['fixed_week_anchor']=1
  post_series.append(series)
 # Priority cascade: fixed anchors claim their weeks first; conflicting normal
 # Premier editions move to open weeks rather than displacing major feeders.
 by_tour=defaultdict(list)
 for r in regulars:by_tour[r['tour']].append(r)
 for tour,events in by_tour.items():
  fixed=[r for r in events if r['fixed_week_anchor']]
  occupied={r['week'] for r in fixed}
  if len(occupied)!=len(fixed):raise AssertionError('Two fixed Premier anchors conflict '+tour)
  for r in sorted((r for r in events if not r['fixed_week_anchor']),key=lambda x:(x['week'],x['series_id'])):
   if r['week'] in occupied:
    valid=[w for w in range(4,53) if w not in occupied and w not in MAJOR_WEEKS]
    r['week']=min(valid,key=lambda w:(abs(w-r['week']),w))
    r['course']=f'{r["region"]} Alternative Venue {r["series_id"]}'
   occupied.add(r['week'])
 # Select permanent flagship/standard/opportunity series, not yearly rankings.
 remaining=[r for r in regulars if r['series_id'] not in post_series and r['series_id'] not in SPECIAL_PREMIER]
 # Prefer long-format prestige for flagship and short-format for additional opportunity fixtures.
 flagship=sorted(remaining,key=lambda r:(-r['holes'],keyed_int(seed,'flagship',r['series_id'])))[:6]
 fids={r['series_id'] for r in flagship}
 remaining=[r for r in remaining if r['series_id'] not in fids]
 more_opp=sorted(remaining,key=lambda r:(r['holes'],keyed_int(seed,'opportunity',r['series_id'])))[:4]
 oids={r['series_id'] for r in more_opp}|set(post_series)
 for r in regulars:
  if r['series_id'] in SPECIAL_PREMIER or r['series_id'] in fids:
   r['prestige']=93 if r['holes']==72 else 88
   r['purse_usd']=16_000_000 if r['holes']==72 else 14_000_000
   r['premier_class']='flagship'
  elif r['series_id'] in oids:
   r['prestige']=64 if r['holes']==72 else 60
   r['purse_usd']=5_500_000 if r['holes']==72 else 4_500_000
   r['premier_class']='opportunity'
  else:
   r['prestige']=81 if r['holes']==72 else 76
   r['purse_usd']=10_000_000 if r['holes']==72 else 8_000_000
   r['premier_class']='standard'
  r['entry_priority']=3
 for r in rows:
  if r['kind']=='major':r['purse_usd']=22_000_000
  r.setdefault('premier_class','')
 rows.sort(key=lambda r:(r['week'],r['entry_priority'],r['event']))
 if sum(r['tier']==0 for r in rows)!=4 or sum(r['tier']==1 for r in rows)!=36:
  raise AssertionError('Must have exactly 4 tier 0 and 36 tier 1 fixtures')
 if Counter(r['premier_class'] for r in regulars)!={'flagship':8,'standard':20,'opportunity':8}:
  raise AssertionError('Premier category distribution incorrect')
 for w in MAJOR_WEEKS:
  if len([r for r in rows if r['week']==w])!=1:raise AssertionError(f'Major week {w} conflict')
 if any(sum(r['tour']==tour and r['week']==week for r in rows if r['tier']==1)>1
        for week in range(1,53) for tour in ('Americas Premier','Europe Premier','Asia Pacific Premier')):
  raise AssertionError('Premier tour duplicated in the same week')
 return rows

class World(ReferenceWorld):
 def __init__(self,seed=1217,population=450,events_scale=1.0,db_path=':memory:',
              stop_after_week=52,sqlite_history=True,**kwargs):
  self.fixtures={};self.fixture_rows=[];self.exemption_ledger=[];self.entry_reasons={}
  self.tour_standings=defaultdict(float);self.ranking_book=RankingBook()
  self.stop_after_week=stop_after_week;self.persist_history=sqlite_history
  self.history=HistoryStore(db_path) if sqlite_history else None
  self.last_rank_week=-1;self.timeline=[];self.all_scorecards=[]
  self._round_count=4;self._cut_round=2;self._recording_event=None
  super().__init__(seed=seed,population=population,events_scale=events_scale,**kwargs)
  self.tour_by_name={t.name:t for t in self.tours}
  assert len(self.tour_by_name)==len(self.tours)

 def _map_course(self,row,occupied):
  """Map fixture's stable hosted venue into actual generated course identities.

  Every independent course must have 18 real hole profiles and permanent ID.
  For countries not yet represented in v0.7 course generation, a same-region
  venue is TEMPORARY and explicit in the data; not falsely named national home.
  """
  week=row['week'];name=row['series_id'];year=row['year'];host=row['host_country']
  if row['kind']=='major' and week==14:
   chosen=self.courses[0]
   if (week,chosen.id) in occupied:raise AssertionError('fixed major course collision')
   occupied.add((week,chosen.id));return chosen
  # Stage qualifiers need real existing host courses, not placeholder names.
  canonical={'United States':'USA'}.get(host,host)
  local=[c for c in self.courses.values() if c.country==canonical]
  regional=[c for c in self.courses.values() if self.countries[c.country]['region']==row['region']]
  eligible=local or regional or list(self.courses.values())
  if row['kind']=='major':eligible=list(self.courses.values())
  basis=keyed_int(self.seed,name,year) if row['course_policy']=='rotating' else keyed_int(self.seed,name)
  for offset in range(len(eligible)):
   course=eligible[(basis+offset)%len(eligible)]
   if (week,course.id) not in occupied:
    occupied.add((week,course.id));return course
  raise RuntimeError(f'No venue available for {name} W{week}')

 def _schedule(self):
  self.fixtures={};self.home_open_meta={};occupied=set();entries=[]
  rows=revised_calendar(self.year,self.seed)
  if self.events_scale<1:
   # Stable gate-test subset; major/qualifier/national anchors always retained.
   rows=[r for r in rows if r['kind']!='regular' or keyed_int(self.seed,r['series_id'])%10000<int(self.events_scale*10000)]
  rows=[r for r in rows if r['week']<=self.stop_after_week]
  for row in rows:
   row=dict(row)
   if row['kind']=='major':tour=self.tour_by_name['Americas Premier']
   elif row['kind']=='qualifying':
    tour=Tour(-1,'Qualifying Circuit','Global',4,row['prestige'],0,row['field_target'],0)
   else:
    if row['tour'] not in self.tour_by_name:raise KeyError(row['tour'])
    tour=self.tour_by_name[row['tour']]
   course=self._map_course(row,occupied)
   if row['kind']=='national_open':
    country={'United States':'USA'}.get(row['host_country'],row['host_country'])
    self.home_open_meta[(self.year,row['week'],row['event'])]={
     'host_country':country,'host_tour':tour.name,'tier':tour.tier,
     'course_id':course.id,'year':self.year,'week':row['week'],'event':row['event']}
   self.fixtures[(self.year,row['week'],row['event'])]=row
   entries.append((row['week'],row['entry_priority'],row['event'],tour,course,
                   row['kind']=='major',row['cut_top_n'],row['field_target']))
  self.fixture_rows=rows
  return sorted(entries,key=lambda e:(e[0],e[1],e[2]))

 def _grant(self,source,target,ids,source_type,slots):
  if not target:return
  for gid in ids[:slots]:
   rec={'target_series':target,'golfer_id':gid,'source_event':self.current_event_id,
        'source_type':source_type,'earned_year':self.year,'earned_week':source['week'],
        'expires_year':self.year,'slots':slots}
   if any(x['target_series']==target and x['golfer_id']==gid and x['earned_year']==self.year for x in self.exemption_ledger):continue
   self.exemption_ledger.append(rec)
   if self.history:self.history.add_exemption(rec)

 def _qualified_ids(self,target):
  return {e['golfer_id'] for e in self.exemption_ledger
          if e['target_series']==target and e['earned_year']==self.year and
             e['earned_week']<self.current_fixture['week']}

 def _choose_field(self,tour,major,week):
  fx=self.current_fixture
  if fx['kind'] not in ('major','qualifying'):
   field=super()._choose_field(tour,major,week)
   self.entry_reasons={g.id:('national_open_invitation' if any(x['golfer_id']==g.id and x['year']==self.year and
      x['week']==week and x['event']==fx['event'] for x in self.home_open_invites[-6:]) else 'tour_priority') for g in field}
   return field
  target=fx['series_id'];qual=self._qualified_ids(target)
  candidates=[g for g in self.golfers.values() if not g.retired and
    g.annual_starts<27 and g.last_week!=week and (not major or g.annual_major_starts<4)
    and self.economics.can_start(g,tour.tier,self.year,week)]
  if major:
   # Event-specific, published qualifying categories. Do not fill missing slots
   # with unqualified golfers and invent a ranking exemption after the fact.
   top_n={14:50,19:100,24:60,30:70}[week]
   rank=self.ranking_book.rankings
   rank_order=list(rank) if rank else []
   ranked_ids=set(rank_order[:top_n])
   # Past champions and recent eligible prestigious event winners constitute
   # separate qualification categories; the archive records their real source.
   historic=[e for e in self.major_history if e['series_id']==target and
             (week==14 or self.year-e['year']<=5)]
   champions={e['winner_id'] for e in historic}
   designated={e['winner_id'] for e in self.event_history if e['kind']=='regular'
               and e['tier']==1 and e.get('premier_class')=='flagship'
               and 0<=self.year-e['year']<=1}
   allowed=qual|ranked_ids|champions|designated
   qualified=[g for g in candidates if g.id in allowed]
   def reason(g):
    if g.id in qual:return 'earned_qualifier_or_national_exemption'
    if g.id in champions:return 'previous_major_champion'
    if g.id in designated:return 'designated_premier_champion'
    return 'published_world_ranking_category'
   qualified.sort(key=lambda g:(
     0 if g.id in qual else 1 if g.id in champions else 2 if g.id in designated else 3,
     rank_order.index(g.id) if g.id in rank else 99999,g.id))
   field=qualified[:fx['field_target']]
   self.entry_reasons={g.id:reason(g) for g in field}
   if len(field)<fx['field_target']:
    self.stats['unfilled_major_exemption_slots']+=fx['field_target']-len(field)

  else:
   # Earlier stages supply genuine entry places to the next stage, while open
   # qualifying fills non-reserved field positions. Amateurs not yet modeled.
   reserved=[g for g in candidates if g.id in qual]
   others=[g for g in candidates if g.id not in qual]
   others.sort(key=lambda g:(abs(g.tier-3),-self._ability(g),g.id))
   field=(reserved+others)[:fx['field_target']]
   self.entry_reasons={g.id:('previous_qualifying_stage' if g.id in qual else 'open_qualifying_entry') for g in field}
  if len(field)<3:return []
  for g in field:
   if not self.economics.pay_entry(g,self.current_event_id,tour.tier,self.year,week):raise AssertionError('Unfunded entry')
   g.annual_starts+=1;g.last_week=week
   if major:g.annual_major_starts+=1
  self.event_shocks={g.id:self.r.gauss(0,self.event_noise)*self._consistency_scale(g) for g in field} if self.event_noise else {}
  self.entry_opportunities.append({'year':self.year,'week':week,'event_id':self.current_event_id,
   'tour':tour.name,'tier':fx['tier'],'region':fx['region'],'major':int(major),
   'slots':fx['field_target'],'eligible_before_budget':len(candidates),'affordable_demand':len(candidates),
   'local_affordable_demand':len(candidates),'field':len(field),'local_starts':0})
  return field

 def _play_round(self,field,groups,scores,rd,course,major,cut_target,record_audit=False):
  """Same v0.7 scoring model; adapt only event-final-round pressure and audit.

  Work is queued by tee slot, pairing, and physical hole order. Contenders
  never see scores from a future hole; pressure is evaluated pre-shot.
  """
  self.round_shocks={g.id:self.r.gauss(0,self.round_noise)*self._consistency_scale(g) for g in field} if self.round_noise else {}
  for g in field:scores[g.id]['current_holes']=0
  queue=[];pairings=[];audit=[];cut_holes=lead_holes=0;processed=0
  for k,group in enumerate(groups):
   heapq.heappush(queue,(group['start_slot'],k,0))
   pairings.append({'round':rd,'pairing_id':k,'tee':group['start_tee'],
                    'tee_slot':group['start_slot'],'golfer_ids':[g.id for g in group['players']]})
  projected_cut=live_leader=0
  is_cut_round=(self._cut_round>0 and rd==self._cut_round)
  is_final_round=(rd==self._round_count)
  while queue:
   slot,k,step=heapq.heappop(queue);group=groups[k]
   hole_idx=(group['start_tee']-1+step)%18;hole=course.holes[hole_idx]
   if is_cut_round and processed%18==0:
    vals=sorted(scores[g.id]['total']-scores[g.id]['par_played'] for g in field)
    projected_cut=vals[min(max(1,cut_target),len(vals))-1]
   if is_final_round and processed%8==0:
    live_leader=min(scores[g.id]['total']-scores[g.id]['par_played'] for g in field)
   outcomes=[]
   for g in group['players']:
    sg=scores[g.id];diff=sg['total']-sg['par_played']
    cut_pressure=(is_cut_round and step>=12 and abs(diff-projected_cut)<=2.5)
    lead_pressure=(is_final_round and step>=9 and diff-live_leader<=3)
    aura=max((min(8,other.majors)*.8 for other in group['players'] if other.id!=g.id),default=0) if major else 0
    weather=(.42 if (slot>35 and course.style=='Links') else 0)+(.25 if rd==3 and course.style=='Desert' else 0)
    q=self._hole_quality(g,hole,major,rd,aura,weather)
    mind=(g.attrs[A['composure']]-50)*(.085 if lead_pressure else .055 if cut_pressure else 0)
    if step>0 and sg['last_hole']>=2:mind+=(g.attrs[A['resilience']]-50)*.038
    outcomes.append((g,self._score_hole(q,hole,mind,major),cut_pressure,lead_pressure))
   for g,relative,is_cut,is_lead in outcomes:
    sg=scores[g.id];strokes=hole.par+relative
    sg['total']+=strokes;sg['par_played']+=hole.par;sg['round_scores'][rd-1]+=strokes
    sg['current_holes']+=1;sg['last_hole']=relative
    sg['hole_cards'][rd-1][hole_idx]=strokes
    if relative<0:sg['birdies']+=1
    if relative>=2:sg['doubles']+=1
    if strokes<course.hole_records[hole_idx]:
     course.hole_records[hole_idx]=strokes
     if self.history:self.history.add_hole_record(course.id,hole.number,self.year,
       self.current_fixture['week'],self.current_event_id,g.id,rd,strokes)
    cut_holes+=int(is_cut);lead_holes+=int(is_lead)
    if record_audit:audit.append({'round':rd,'minute_slot':slot,'pairing':k,'player_id':g.id,
       'physical_hole':hole.number,'par':hole.par,'strokes':strokes,
       'score_to_par_after':sg['total']-sg['par_played'],'near_projected_cut':bool(is_cut),
       'near_live_lead':bool(is_lead),'projected_cut_to_par':projected_cut if is_cut_round else None})
   if step==17:
    for g in group['players']:
     sg=scores[g.id];sg['prev_order']=processed
     if sg['round_scores'][rd-1]<course.record:
      course.record=sg['round_scores'][rd-1];course.record_holder=g.id;course.record_year=self.year
      if self.history:self.history.add_course_record(course.id,self.year,self.current_fixture['week'],
                                     self.current_event_id,g.id,rd,course.record)
   else:heapq.heappush(queue,(slot+1,k,step+1))
   processed+=1
  return {'pairings':pairings,'cut_pressure_holes':cut_holes,
          'lead_pressure_holes':lead_holes,'hole_audit':audit}

 def _simulate_event(self,info):
  week,_,name,tour,course,major,cut_number,field_size=info
  fx=self.fixtures[(self.year,week,name)];self.current_fixture=fx
  if fx['kind']=='qualifying' and fx['qualification_rule']=='direct_amateur_win':
   self.stats['amateur_only_qualifier_deferred']+=1
   return  # no amateur-player status system yet: never award a false exemption
  self.current_event_id=f'{self.year}:{week}:{name}';self.current_course_id=course.id
  original_slots=tour.slots;tour.slots=field_size
  try:field=self._choose_field(tour,major,week)
  finally:tour.slots=original_slots
  if len(field)<3:
   self.validation.append(dict(year=self.year,event=name,issue='insufficient_field',field=len(field)))
   return
  self._round_count=fx['rounds'];self._cut_round=2 if fx['cut_after_holes']==36 else 0
  n=fx['rounds'];scores={g.id:{'total':0,'round_scores':[0]*n,'hole_cards':[[0]*18 for _ in range(n)],
   'current_holes':0,'par_played':0,'last_hole':0,'birdies':0,'doubles':0,'prev_order':0} for g in field}
  for g in field:
   g.visited[course.id]=g.visited.get(course.id,0)+1
   self.staff[g.caddie_id].visits[course.id]=self.staff[g.caddie_id].visits.get(course.id,0)+1
  r1,r2=self._initial_groups(field)
  all_pairings=[];record_audit=self.audit and self.featured_tournament is None and major
  audit=[];cutline=None;survivors=list(field);cut_holes=lead_holes=0;final_pair=[]
  for rd in range(1,n+1):
   if rd==1:groups=r1
   elif rd==2:groups=r2
   else:groups=self._weekend_groups(survivors,scores,rd)
   if rd==n:
    final_pair=[g.id for g in groups[-1]['players']]
    if n>=3:
     max_leader=max(scores[g]['total'] for g in final_pair)
     if any(scores[g.id]['total']<max_leader for g in survivors if g.id not in final_pair):
      self.validation.append(dict(year=self.year,event=name,issue='leaders_not_in_last_pair'))
   v=self._play_round(survivors,groups,scores,rd,course,major,cut_number,record_audit)
   all_pairings.extend(v['pairings']);audit.extend(v['hole_audit']);cut_holes+=v['cut_pressure_holes'];lead_holes+=v['lead_pressure_holes']
   if self._cut_round==rd and rd<n:
    ordered=sorted(scores[g.id]['total'] for g in field)
    cutline=ordered[min(max(1,cut_number),len(ordered))-1]
    survivors=[g for g in field if scores[g.id]['total']<=cutline]
  final=sorted(survivors,key=lambda g:(scores[g.id]['total'],scores[g.id]['prev_order']))
  best=scores[final[0].id]['total'];tied=[g for g in final if scores[g.id]['total']==best]
  playoff_holes=0
  while len(tied)>1 and playoff_holes<24:
   hole=course.holes[playoff_holes%18]
   values={g.id:self._score_hole(self._hole_quality(g,hole,major,n)+.8,hole,(g.attrs[A['composure']]-50)*.18,major) for g in tied}
   low=min(values.values());tied=[g for g in tied if values[g.id]==low];playoff_holes+=1
  if len(tied)>1:tied=[min(tied,key=lambda g:g.id)]
  winner=tied[0]
  final_positions=tie_positions([g.id for g in final],{gid:scores[gid]['total'] for gid in scores},winner.id)
  positions={gid:rank for gid,(rank,_) in final_positions.items()}
  purse=fx['purse_usd'];payouts=allocate_prizes([g.id for g in final],scores,winner.id,purse)
  self.purse_audits.append(dict(year=self.year,event_id=self.current_event_id,purse=purse,
   paid=sum(payouts.values()),paid_cents=sum(cents(v) for v in payouts.values()),purse_cents=cents(purse),finishers=len(final)))
  mean_rounds=[mean(score['round_scores'][i] for score in scores.values() if score['round_scores'][i]>0) for i in range(n)]
  field_rating=self.ranking_book.event_field_rating(field,self._ability,(self.year-2027)*52+week,self.current_event_id)
  points=self.ranking_book.award_event(self.current_event_id,(self.year-2027)*52+week,fx['holes'],fx['kind'],fx['tier'],
                                       field_rating,final_positions,{gid:scores[gid]['total'] for gid in scores})
  self.ranking_book.register_starts((self.year-2027)*52+week,fx['holes'],fx['kind'],fx['tier'],[g.id for g in field])
  for g in field:
   sg=scores[g.id];g.starts+=1
   perf=self.season_performance.setdefault(g.id,{'starts':0,'cuts':0,'top10s':0,'rounds':0,'field_relative_strokes':0.,'tier_sum':0.})
   perf['starts']+=1;perf['cuts']+=int(g.id in positions);perf['top10s']+=int(positions.get(g.id,9999)<=10)
   perf['tier_sum']+=min(4,max(1,tour.tier))
   for i in range(min(2,n)):
    st=sg['round_scores'][i]
    if st:
     perf['rounds']+=1;perf['field_relative_strokes']+=mean_rounds[i]-st
   if g.id in positions:
    g.cuts+=1;rank=positions[g.id]
    if fx['kind'] not in ('qualifying',):
     g.season_points+= (100 if major else fx['prestige']*.72)/(rank**.72)
     self.tour_standings[(self.year,fx['tour'],g.id)]+=fx['prestige']/(rank**.72)
    self.economics.credit_prize(g,self.current_event_id,payouts[g.id],self.year,week)
    if rank==1 and fx['kind']!='qualifying':
     g.wins+=1;g.season_wins+=1;g.confidence=min(9,g.confidence+2.5)
     if major:g.majors+=1
     self.staff[g.caddie_id].wins+=1;self.staff[g.coach_id].wins+=1
     if major:self.staff[g.caddie_id].majors+=1;self.staff[g.coach_id].majors+=1
     g.career.append(dict(year=self.year,week=week,event='Major victory' if major else 'Tournament victory',
                          name=name,course_id=course.id,holes=fx['holes']))
    elif rank<=10:g.confidence=min(9,g.confidence+.55)
   else:g.confidence=max(-9,g.confidence-.24)
   completed_rounds=sum(bool(v) for v in sg['round_scores']);avg=sg['total']/completed_rounds
   g.form=max(-5,min(5,.86*g.form+.16*(course.par-avg)*.13+self.r.gauss(0,.17)))
   # Fewer rounds create less fatigue than a major.
   g.fatigue=min(100,g.fatigue+(3.5 if major else 2.5)*(fx['holes']/72))
  # Award the exact specified qualifier places AFTER the event is final.
  ordered=sorted(final_positions,key=lambda gid:(final_positions[gid][0],gid))
  self._grant(fx,fx['qualification_target'],ordered,fx['qualification_rule'],fx['qualification_slots'])
  if fx['tier']==1 and fx['kind']!='qualifying':
   # Winner's provisional two-season membership exemption, with provenance.
   ex=dict(target_series='TOUR:'+fx['tour'],golfer_id=winner.id,source_event=self.current_event_id,
           source_type='premier_event_winner',earned_year=self.year,earned_week=week,
           expires_year=self.year+2,slots=1)
   self.exemption_ledger.append(ex)
   if self.history:self.history.add_exemption(ex)
  self.stats['holes_scored']+=sum(18*sum(bool(r) for r in s['round_scores']) for s in scores.values())
  self.stats['cuts_made']+=len(survivors);self.stats['players_started']+=len(field)
  self.stats['projected_cut_pressure_holes']+=cut_holes;self.stats['lead_pressure_holes']+=lead_holes
  self.stats['playoff_events']+=int(playoff_holes>0);self.stats['playoff_holes']+=playoff_holes
  self.stats['pairing_count']+=len(all_pairings)
  course.visits+=1;course.course_winners[winner.id]=course.course_winners.get(winner.id,0)+1
  row=dict(year=self.year,week=week,event=name,series_id=fx['series_id'],event_id=self.current_event_id,
   tour=fx['tour'],tier=fx['tier'],major=int(major),kind=fx['kind'],prestige=fx['prestige'],premier_class=fx.get('premier_class',''),
   course_id=course.id,course=course.name,holes=fx['holes'],rounds=n,purse_usd=purse,
   winner_id=winner.id,winner=winner.name,winner_country=winner.country,winning_score=best,
   to_par=best-course.par*n,course_par=course.par,field=len(field),made_cut=len(survivors),
   cut_score=cutline,playoff_holes=playoff_holes,cut_pressure_holes=cut_holes,
   contending_pressure_holes=lead_holes,field_rating=round(field_rating,4))
  self.event_history.append(row)
  if fx['kind']=='national_open':
   host={'United States':'USA'}.get(fx['host_country'],fx['host_country'])
   visits=sum(x['year']==self.year and x['week']==week and x['event']==name for x in self.home_open_invites)
   self.home_open_records.append(dict(year=self.year,week=week,event=name,
    host_country=host,host_tour=fx['tour'],course_id=course.id,course_name=course.name,
    winner_id=winner.id,winner=winner.name,winner_country=winner.country,
    home_winner=int(winner.country==host),invited_elite_home_starts=visits,
    holes=fx['holes'],purse=purse))
   self.home_open_stats['events']+=1
   self.home_open_stats['home_winners']+=int(winner.country==host)
  if major:
   self.major_history.append(row)
   for g in field:
    sg=scores[g.id]
    rec=dict(year=self.year,event=name,golfer_id=g.id,golfer=g.name,country=g.country,
             rank=positions.get(g.id),cut=g.id in positions,rounds=sg['round_scores'],total=sg['total'],
             birdies=sg['birdies'],doubles_or_worse=sg['doubles'])
    self.event_finishes.append(rec)
  if record_audit:
   self.featured_tournament={'event':row,'final_pair':final_pair,'pairings':all_pairings,
       'hole_audit':audit,'final_scores':[{ 'golfer_id':g.id,'total':scores[g.id]['total'],
          'round_scores':scores[g.id]['round_scores']} for g in final]}
  if self.history:self.history.record_event(row,scores,positions,payouts,all_pairings,self.entry_reasons)
  self.timeline.append(dict(year=self.year,week=week,event_id=self.current_event_id,holes=fx['holes'],
                            entrants=len(field),qualifications=len(self.exemption_ledger)))

 def _commit_week(self,week):
  wi=(self.year-2027)*52+week
  active=[g.id for g in self.golfers.values() if not g.retired]
  ranks=self.ranking_book.update(wi,active)
  if self.history:
   self.history.add_rankings(self.year,week,ranks)
   self.history.commit_week()
  self.last_rank_week=wi
  for pos,gid in enumerate(ranks,1):
   g=self.golfers[gid];g.rank=pos;g.peak_rank=min(g.peak_rank,pos)

 def _rank_and_archive(self):
  super()._rank_and_archive()
  if self.last_rank_week>=0:
   ordered=list(self.ranking_book.rankings)
   for rank,gid in enumerate(ordered,1):
    g=self.golfers[gid];g.rank=rank;g.peak_rank=min(rank,g.peak_rank)
   if ordered:
    self.world_years[-1]['world_no1']=ordered[0]
    self.world_years[-1]['world_no1_name']=self.golfers[ordered[0]].name

 def run(self,years=1,verbose=False):
  start=time.perf_counter()
  for _ in range(years):
   season_players=[g for g in self.golfers.values() if not g.retired]
   for g in season_players:self.economics.begin_season(g,self.year)
   self.season_performance={g.id:dict(starts=0,cuts=0,top10s=0,rounds=0,field_relative_strokes=0.,tier_sum=0.) for g in season_players}
   schedule=self._schedule();events_by_week=defaultdict(list)
   for e in schedule:events_by_week[e[0]].append(e)
   for week in range(1,self.stop_after_week+1):
    for g in season_players:self.economics.advance_to_week(g,self.year,week)
    for e in events_by_week[week]:self._simulate_event(e)
    self._commit_week(week)
   for g in season_players:
    s=self.season_performance[g.id]
    performance=dict(starts=s['starts'],rounds_observed=s['rounds'],
      cut_rate=s['cuts']/s['starts'] if s['starts'] else None,
      field_relative_strokes_per_round=s['field_relative_strokes']/s['rounds'] if s['rounds'] else None,
      top10s=s['top10s'],mean_event_tier=s['tier_sum']/s['starts'] if s['starts'] else None,
      operating_tier=self.economics.accounts[g.id].season_tier)
    row=self.economics.end_season(g,self.year,review=False,performance=performance)
    self.training_exposure_by_id[g.id]=row['training_exposure']
   self._tour_moves();self._rank_and_archive()
   for g in season_players:
    self._year_development(g)
    biological_exit=g.retired
    if biological_exit:self.economics.mark_retired(g,self.year,reason='Age-related career exit in fictional lifecycle model')
    self.economics.review_career(g,self.year)
    if g.retired and not biological_exit:self.stats['retirements']+=1;self.stats['financial_career_exits']+=1
   num=sum(not g.retired for g in self.golfers.values())
   for _ in range(max(0,self.population-num)):
    g=self._create_golfer();g.coach_id=self._new_staff('coach',g.id).id;g.caddie_id=self._new_staff('caddie',g.id).id
    self.economics.register(g,self.year+1,initial=False)
   self._evolve_countries()
   if self.history:self.history.checkpoint_season()
   if verbose:print(f'v0.13 seed={self.seed} year={self.year} events={len(self.event_history)} '
                    f'time={time.perf_counter()-start:.1f}s',flush=True)
   self.year+=1
  self.stats['runtime_seconds']=round(time.perf_counter()-start,3)
  return self

 def summary(self):
  out=super().summary()
  out.update(model_version='0.13-calendar-integration-experimental',
             calendar_fixtures=len(self.fixture_rows),ranking_awards=len(self.ranking_book.point_awards),
             exemption_records=len(self.exemption_ledger),history_audit=self.history.audit() if self.history else None)
  return out

 def export(self,root):
  # Reference export expects featured final scores r1/r2/r3/r4 for every major;
  # convert v0.13's flexible structure without changing the original archive.
  root=Path(root);root.mkdir(parents=True,exist_ok=True)
  def write_csv(name,rows):
   if not rows:return
   keys=list(dict.fromkeys(k for row in rows for k in row))
   with (root/name).open('w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
  write_csv('events.csv',self.event_history)
  write_csv('exemptions.csv',self.exemption_ledger)
  write_csv('field_strength.csv',self.ranking_book.field_snapshots)
  write_csv('world_point_awards.csv',self.ranking_book.point_awards)
  write_csv('tour_standings.csv',[dict(year=y,tour=t,golfer_id=gid,points=round(pts,6))
                for (y,t,gid),pts in self.tour_standings.items()])
  write_csv('major_results.csv',self.event_finishes)
  write_csv('national_open_results.csv',self.home_open_records)
  write_csv('national_open_invites.csv',self.home_open_invites)
  write_csv('purse_audits.csv',self.purse_audits)
  write_csv('calendar_used.csv',self.fixture_rows)
  write_csv('country_development.csv',self.countries_history)
  write_csv('world_seasons.csv',self.world_years)
  if self.featured_tournament:
   (root/'featured_major_hole_audit.json').write_text(json.dumps(self.featured_tournament),encoding='utf8')
  report=self.summary();(root/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf8')
  return report


def main():
 p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=1217)
 p.add_argument('--population',type=int,default=450);p.add_argument('--years',type=int,default=1)
 p.add_argument('--events-scale',type=float,default=.25)
 p.add_argument('--stop-week',type=int,default=52)
 p.add_argument('--db',default=':memory:');p.add_argument('--out',default='results_v013')
 p.add_argument('--quiet',action='store_true');a=p.parse_args()
 w=World(seed=a.seed,population=a.population,events_scale=a.events_scale,
   stop_after_week=a.stop_week,db_path=a.db).run(a.years,verbose=not a.quiet)
 print(json.dumps(w.export(a.out),indent=2))
if __name__=='__main__':main()
