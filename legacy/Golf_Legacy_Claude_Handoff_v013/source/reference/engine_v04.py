"""Golf Legacy v0.4 calibration iteration.

A working-copy extension of v0.3, not a validated sports prediction model.
Elite skill is nonlinear; ranking never grants a scoring bonus. Hole order,
fields, cuts and pairing rules remain v0.3. See CALIBRATION_REPORT.md.
"""
from __future__ import annotations
import argparse, csv, json, math
from pathlib import Path
from statistics import mean
import engine_v03 as base
from engine_v03 import A, BASE_PROB

OUTCOMES=(-2,-1,0,1,2,3)

def technical_rating(g,hole):
 z=g.attrs
 if hole.par==3:return .07*z[0]+.12*z[2]+.50*z[3]+.05*z[4]+.20*z[6]+.06*z[11]
 if hole.par==5:return .20*z[0]+.09*z[1]+.22*z[2]+.20*z[3]+.08*z[4]+.17*z[6]+.04*z[11]
 return .11*z[0]+.18*z[1]+.07*z[2]+.30*z[3]+.12*z[4]+.18*z[6]+.04*z[11]

def hole_probabilities(quality,hole,major=False,dispersion=1.):
 """v0.3 marginal mean, optionally lower variance without shifting the mean.

 Mix the original categorical outcome with its adjacent-integer distribution.
 This preserves expected strokes; dispersion is a variance mixture weight,
 NOT the resulting standard deviation. No extra RNG draw is needed.
 """
 d=hole.diff+.65+(.65 if major else 0.)
 eagle,birdie,bogey,double,triple=BASE_PROB[hole.par]
 birdie=max(.018,min(.70,birdie+.0038*quality-.046*d))
 bogey=max(.025,min(.53,bogey-.0026*quality+.056*d))
 double=max(.002,min(.14,double-.00040*quality+.016*d+hole.hazard*.004))
 triple=max(.0001,min(.040,triple-.00007*quality+.003*d))
 eagle=max(0,min(.15,eagle+.00060*quality if hole.par==5 else eagle+.00008*quality))
 nonpar=[eagle,birdie,bogey,double,triple]
 # Extreme diagnostic inputs should never create invalid probability mass.
 total=sum(nonpar)
 if total>1:nonpar=[p/total for p in nonpar]
 eagle,birdie,bogey,double,triple=nonpar
 p=[eagle,birdie,max(0.,1-sum(nonpar)),bogey,double,triple]
 if dispersion>=1:return p
 if not 0<=dispersion<=1:raise ValueError('dispersion must lie in [0,1]')
 mu=sum(x*y for x,y in zip(OUTCOMES,p));lo=math.floor(mu);hi=math.ceil(mu)
 concentrated=[0.]*6
 if lo==hi:concentrated[lo+2]=1.
 else:concentrated[lo+2]=hi-mu;concentrated[hi+2]=mu-lo
 return [dispersion*x+(1-dispersion)*y for x,y in zip(p,concentrated)]

class World(base.World):
 def __init__(self,*args,elite_curve=.04,dispersion=.58,event_noise=2.,round_noise=3.,familiarity=True,**kwargs):
  if elite_curve<0 or not 0<=dispersion<=1:raise ValueError('invalid calibration parameters')
  self.elite_curve=elite_curve;self.dispersion=dispersion
  self.event_noise=event_noise;self.round_noise=round_noise;self.familiarity=familiarity
  self.event_shocks={};self.round_shocks={};self.annual_golfers=[];self.major_entry_context=[];self.completed_major_starts={}
  super().__init__(*args,**kwargs)
 def _choose_field(self,tour,major,week):
  field=super()._choose_field(tour,major,week)
  self.event_shocks={g.id:self.r.gauss(0,self.event_noise)*self._consistency_scale(g) for g in field} if self.event_noise else {}
  if major:
   active=sorted((g for g in self.golfers.values() if not g.retired),key=self._ability,reverse=True)
   ranks={g.id:i+1 for i,g in enumerate(active)}
   for g in field:self.major_entry_context.append({'year':self.year,'week':week,'golfer_id':g.id,'ability_rank':ranks[g.id],
    'previous_world_rank':g.rank,'ability':round(self._ability(g),4),'age':self.year-g.born,'prodigy':int(g.prodigy),
    'injury':round(g.injury,3),'slump':round(g.slump,3),'form':round(g.form,3)})
  return field
 def _consistency_scale(self,g):
  # Both consistency attributes now affect correlated execution variability,
  # not talent or mean scoring. Putting does not get double-counted.
  consistency=.65*g.attrs[A['ball_consistency']]+.35*g.attrs[A['putt_consistency']]
  return max(.65,min(1.45,1+(75-consistency)*.012))
 def _play_round(self,field,groups,scores,rd,course,major,cut_target,record_audit=False):
  self.round_shocks={g.id:self.r.gauss(0,self.round_noise)*self._consistency_scale(g) for g in field} if self.round_noise else {}
  return super()._play_round(field,groups,scores,rd,course,major,cut_target,record_audit)
 def _hole_quality(self,g,hole,major,rd,partner_aura=0,weather=0):
  q=super()._hole_quality(g,hole,major,rd,partner_aura,weather)
  # Smooth, continuous upper tail: +1 developed technical point matters more
  # at elite levels. Temporary form, caddies and mental effects are NOT squared.
  elite=max(0.,technical_rating(g,hole)-75.)
  q+=self.elite_curve*elite*elite
  q+=self.event_shocks.get(g.id,0.)+self.round_shocks.get(g.id,0.)
  if self.familiarity:
   # v0.3 recorded visits by course.id but looked them up with hole-number keys.
   # Exclude this current visit and retain a small diminishing-return effect.
   q-=math.log1p(g.visited.get(hole.number+10000*self.current_course_id,0))*.13
   visits=max(0,g.visited.get(self.current_course_id,0)-1)
   q+=math.log1p(visits)*.13
  return q
 def _score_hole(self,quality,hole,psych_shift=0,major=False):
  p=hole_probabilities(quality+psych_shift,hole,major,self.dispersion)
  x=self.r.random()
  for index in (0,1,3,4,5,2):
   x-=p[index]
   if x<0:return OUTCOMES[index]
  return 0
 def _rank_and_archive(self):
  # Record pre-development season state. Never infer a narrative cause from
  # a later result; injuries/slumps retain their actual dated career log.
  for g in self.golfers.values():
   if not g.retired:self.annual_golfers.append({'year':self.year,'golfer_id':g.id,'name':g.name,'age':self.year-g.born,
    'tier':g.tier,'ability':round(self._ability(g),3),'technical_mean':round(mean(g.attrs[:9]),3),
    'physical_power':round(g.attrs[A['drive_power']],3),'mental_mean':round(mean(g.attrs[9:12]),3),
    'season_points':round(g.season_points,4),'season_wins':g.season_wins,'career_majors':g.majors,
    'starts':g.annual_starts,'major_starts':g.annual_major_starts,'injury':round(g.injury,3),
    'slump':round(g.slump,3),'form':round(g.form,3),'prodigy':int(g.prodigy)})
  self.completed_major_starts={g.id:g.annual_major_starts for g in self.golfers.values() if not g.retired}
  super()._rank_and_archive()
 def _year_development(self,g):
  # v0.3 reset exposure before development, making stage learning unreachable.
  saved=g.annual_major_starts
  prior_slump_years=g.slump_years
  prior_slump=g.slump
  g.annual_major_starts=self.completed_major_starts.get(g.id,saved)
  super()._year_development(g)
  g.annual_major_starts=saved
  if prior_slump>0 and g.slump_years==0:
   # A dated temporary episode ends; residual severity must not last forever.
   g.slump=0.
   g.career.append({'year':self.year,'event':'Recovered from technical slump','timing':'year_end'})
 def summary(self):
  out=super().summary()
  out['model_version']='0.4';out['calibration']={'elite_curve':self.elite_curve,'dispersion':self.dispersion,
   'event_quality_sd':self.event_noise,'round_quality_sd':self.round_noise,'familiarity_fix':self.familiarity}
  return out
 def export(self,root):
  out=super().export(root)
  golfer_path=Path(root)/'golfers.csv'
  with golfer_path.open(newline='',encoding='utf8') as f:rows=list(csv.DictReader(f))
  for row in rows:row['born']=self.golfers[int(row['id'])].born
  if rows:
   with golfer_path.open('w',newline='',encoding='utf8') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
  for name,rows in [('annual_golfers.csv',self.annual_golfers),('major_entry_context.csv',self.major_entry_context)]:
   if rows:
    with (Path(root)/name).open('w',newline='',encoding='utf8') as f:
     writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
  return out

def main():
 p=argparse.ArgumentParser();p.add_argument('--years',type=int,default=30);p.add_argument('--seed',type=int,default=505)
 p.add_argument('--population',type=int,default=1700);p.add_argument('--events-scale',type=float,default=1.)
 p.add_argument('--out',default='results_v04');p.add_argument('--quiet',action='store_true')
 p.add_argument('--elite-curve',type=float,default=.04);p.add_argument('--dispersion',type=float,default=.58)
 p.add_argument('--event-noise',type=float,default=2.);p.add_argument('--round-noise',type=float,default=3.)
 p.add_argument('--no-familiarity',action='store_true')
 a=p.parse_args();w=World(a.seed,a.population,a.events_scale,elite_curve=a.elite_curve,dispersion=a.dispersion,
  event_noise=a.event_noise,round_noise=a.round_noise,familiarity=not a.no_familiarity).run(a.years,verbose=not a.quiet)
 print(json.dumps(w.export(a.out),indent=2))
if __name__=='__main__':main()
