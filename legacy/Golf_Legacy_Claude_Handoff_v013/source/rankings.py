"""Golf Legacy experimental weekly OWGR-style rankings (NOT official OWGR).

Ranking points are earned from eligible 54/72-hole sanctioned events.  A
rolling two-year average is used; the event field rating is frozen before
competition.  The official OWGR points curves / Glicko-style SG model are NOT
reproduced here; the initial scoring proxy and award curve need calibration.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
from math import isfinite

@dataclass(frozen=True)
class RankingResult:
    golfer_id:int
    week_index:int
    points:float
    source_id:str


def age_weight(age_weeks):
    if age_weeks < 0: raise ValueError('future result')
    if age_weeks <= 13: return 1.0
    if age_weeks >= 104: return 0.0
    return (104-age_weeks)/91.0


def divisor(n_starts):
    return max(40, min(52, n_starts))


def tie_positions(finalists, scores, winner_id):
    """Winner alone; share occupied position awards for the rest of a tied group.

    finals scores map id -> cumulative gross strokes. Playoff winner is sole 1st.
    Return each golfer -> (starting finish rank, ranks occupied by tie group).
    """
    ordered=sorted(finalists, key=lambda gid:(scores[gid],gid))
    if not ordered or winner_id not in ordered: raise ValueError('invalid field')
    if scores[winner_id]!=scores[ordered[0]]: raise ValueError('playoff winner was not lowest score')
    groups=[[winner_id]]
    for gid in ordered:
        if gid==winner_id:continue
        if len(groups)>1 and scores[groups[-1][0]]==scores[gid]:groups[-1].append(gid)
        else:groups.append([gid])
    out={}; rank=1
    for group in groups:
        occupied=tuple(range(rank,rank+len(group)))
        for gid in group:out[gid]=(rank,occupied)
        rank+=len(group)
    return out

class RankingBook:
    def __init__(self):
        self.results=defaultdict(list)
        self.starts=defaultdict(list)
        self.rankings={}
        self.snapshots=[]
        self.field_snapshots=[]
        self.point_awards=[]

    def event_field_rating(self, entrants, ability_func, week, event_id):
        """Provisional pre-event field rating from observed form and ability proxy.

        TODO: replace with observed adjusted strokes gained only after a sufficiently
        established observation window. This is not the official OWGR field algorithm.
        """
        abilities=[ability_func(g) for g in entrants]
        top=sorted(abilities,reverse=True)[:min(30,len(abilities))]
        top_average=sum(top)/len(top) if top else 65.0
        rating=max(5.0,min(85.,(top_average-63.)*2.0+35.0))
        row=dict(event_id=event_id,week_index=week,top30_ability=round(top_average,4),
                 field_rating=round(rating,4),entrants=len(entrants),method='v0.13_provisional_pre_event_ability_proxy')
        self.field_snapshots.append(row)
        return rating

    def award_event(self, event_id, week_index, holes, kind, tier, field_rating, final_positions, stroke_totals):
        if holes not in (54,72) or kind=='qualifying' or tier not in (0,1,2,3):return {}
        base=100.0 if kind=='major' else max(4.,min(70.,field_rating*.72 + (8 if tier==1 else 2 if tier==2 else -5)))
        if holes==54:base*=.75
        # final_positions contains {gid:(rank,occupied_ranks)}.  No retroactive recalculation.
        awarded={}
        for gid,(rank,occupied) in final_positions.items():
            raw=sum(base/(p**.77) for p in occupied)/len(occupied)
            if rank>70:raw=0.0
            if raw<1e-7:continue
            awarded[gid]=raw
            self.results[gid].append(RankingResult(gid,week_index,raw,event_id))
            self.point_awards.append(dict(event_id=event_id,week_index=week_index,golfer_id=gid,
                                          position=rank,holes=holes,points=round(raw,6),field_rating=round(field_rating,4)))
        return awarded

    def register_starts(self, week_index, holes, kind, tier, golfers):
        if holes not in (54,72) or kind=='qualifying' or tier not in (0,1,2,3):return
        for gid in golfers:self.starts[gid].append(week_index)

    def update(self,week_index,active_ids):
        points={}
        for gid in active_ids:
            valid=[e for e in self.results.get(gid,()) if 0<=week_index-e.week_index<104]
            valid_starts=sum(0<=week_index-w<104 for w in self.starts.get(gid,()))
            if not valid:points[gid]=0.0;continue
            adjusted=sum(e.points*age_weight(week_index-e.week_index) for e in valid)
            points[gid]=adjusted/divisor(valid_starts)
        self.rankings=dict(sorted(points.items(),key=lambda kv:(-kv[1],kv[0])))
        return self.rankings
