#!/usr/bin/env python3
"""Golf Legacy v0.11 auditable 52-week tournament-format calendar.

Standalone calendar fixture generator. Does NOT modify the scoring simulation.
The professional tournament/event totals match the v0.9 calendar fixture.
Every modeled tournament/qualifier has explicit 18/36/54/72-hole rules.
"""
from __future__ import annotations
import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent
MAJORS = {
    14: ('Legends of Golf Masters Event', 'Legends Magnolia Club', 'fixed', 96, 50),
    19: ('Premier Tour Championship', None, 'rotating', 156, 70),
    24: ('American Open', None, 'rotating', 156, 60),
    30: ('Brittania Open', None, 'rotating', 156, 70),
}
REGIONS = ['Americas', 'Europe', 'Asia', 'Africa', 'Oceania']
COUNTRIES = {
    'Americas': ['United States','Canada','Mexico','Brazil','Argentina','Chile'],
    'Europe': ['England','Scotland','Ireland','Wales','Sweden','Spain','France','Germany'],
    'Asia': ['Japan','South Korea','India','Thailand','China','Philippines'],
    'Africa': ['South Africa','Kenya','Nigeria','Morocco'],
    'Oceania': ['Australia','New Zealand','Fiji','Papua New Guinea'],
}
TOURS = [
    ('Americas Premier','Americas',1,13),('Europe Premier','Europe',1,12),('Asia Pacific Premier','Asia',1,9),
    ('Americas Challenger','Americas',2,13),('Europe Challenger','Europe',2,12),('Asia Challenger','Asia',2,10),
    ('Oceania Challenger','Oceania',2,7),('Africa Challenger','Africa',2,7),
    ('Americas Regional','Americas',3,10),('Europe Regional','Europe',3,10),('Asia Regional','Asia',3,9),
    ('Africa Regional','Africa',3,8),('Oceania Regional','Oceania',3,7),
    ('Americas Mini Circuit','Americas',4,12),('Europe Mini Circuit','Europe',4,12),
    ('Asia Mini Circuit','Asia',4,12),('Africa Mini Circuit','Africa',4,12),('Oceania Mini Circuit','Oceania',4,12),
]
for region in REGIONS:
    TOURS.extend([(f'{region} Secondary Regional',region,3,10),
                  (f'{region} Local Pro 1',region,4,10),
                  (f'{region} Local Pro 2',region,4,10)])
assert len(TOURS) == 33 and sum(t[3] for t in TOURS) == 337
COURSES = {r: [f'{r} Tournament Course {i:02}' for i in range(1,36)] for r in REGIONS}

# These four historically important National Opens get immutable series weeks.
# Their winners earn a *conditional* berth for the current-year Week 30 major,
# subject to legitimate nationality-neutral tournament rules and eligibility.
ANCHOR_NATIONAL = {
    'Scotland': (21, 'Europe Challenger'),
    'Kenya': (22, 'Africa Challenger'),
    'Japan': (25, 'Asia Challenger'),
    'Australia': (27, 'Oceania Challenger'),
}

# Week 13/18/23/29 final pathways are fully reserved before other fixtures.
# A 36-hole final qualifier can feed directly to a major. It is a realistic
# qualification-format exception to the general longer=more prestigious rule.
QUALIFIERS = [
    (8,  'Legends Amateur Qualifier - Asia-Pacific',54,80,'MAJOR_14',1,'direct_amateur_win'),
    (10, 'Legends Amateur Qualifier - Latin America',54,80,'MAJOR_14',1,'direct_amateur_win'),
    (11, 'American Open Local Qualifier - West',18,96,'QUAL_AMERICAN_REGIONAL_WEST',12,'advance_stage'),
    (12, 'American Open Local Qualifier - East',18,96,'QUAL_AMERICAN_REGIONAL_EAST',12,'advance_stage'),
    (12, 'Club Professional Regional Qualifying',36,120,'QUAL_PREMIER_FINAL',40,'advance_stage'),
    (13, 'Legends Masters Final Invitational Qualifier',54,100,'MAJOR_14',1,'direct_major_win'),
    (16, 'American Open Regional Qualifier - East',36,96,'QUAL_AMERICAN_FINAL',18,'advance_stage'),
    (17, 'American Open Regional Qualifier - West',36,96,'QUAL_AMERICAN_FINAL',18,'advance_stage'),
    (18, 'Premier Professional Qualification Championship',72,144,'MAJOR_19',20,'direct_major_top_finishers'),
    (21, 'American Open Sectional Qualifying',36,96,'QUAL_AMERICAN_FINAL',18,'advance_stage'),
    (23, 'American Open Final Qualifying',36,144,'MAJOR_24',12,'direct_major_top_finishers'),
    (25, 'Brittania Regional Qualifying - Europe',36,96,'QUAL_BRITTANIA_FINAL',18,'advance_stage'),
    (25, 'Brittania Regional Qualifying - Asia',36,96,'QUAL_BRITTANIA_FINAL',18,'advance_stage'),
    (26, 'Brittania Regional Qualifying - Africa',36,96,'QUAL_BRITTANIA_FINAL',18,'advance_stage'),
    (27, 'Brittania Regional Qualifying - Oceania',36,96,'QUAL_BRITTANIA_FINAL',18,'advance_stage'),
    (28, 'Brittania Sectional Final Qualifying',36,96,'QUAL_BRITTANIA_FINAL',18,'advance_stage'),
    (29, 'Brittania Open Final Qualifying',36,144,'MAJOR_30',12,'direct_major_top_finishers'),
]
FORMAT_WEIGHTS = {
    1: ((54,.15),(72,.85)),
    2: ((36,.10),(54,.60),(72,.30)),
    3: ((18,.15),(36,.45),(54,.35),(72,.05)),
    4: ((18,.45),(36,.40),(54,.15)),
}
# Format modifiers are *within-tier* bonuses. Tier, field and tradition can
# outweigh duration. Amateur/qualifying fields have prize money = $0.
BASE_PRESTIGE = {1:82,2:61,3:42,4:23}
BASE_PURSE = {1:3_000_000,2:750_000,3:140_000,4:30_000}
PRESTIGE_FORMAT = {18:-6,36:0,54:5,72:10}
PURSE_FORMAT = {18:.45,36:.70,54:1.0,72:1.35}
ROUND_DAYS = {18:'Sat',36:'Sat|Sun',54:'Fri|Sat|Sun',72:'Thu|Fri|Sat|Sun'}


def seeded_rng(year, seed, tag):
    digest = hashlib.blake2b(f'{year}:{seed}:{tag}'.encode('utf8'),digest_size=8).digest()
    return random.Random(int.from_bytes(digest,'big'))


def choose_format(year,seed,series_id,tier):
    opts = FORMAT_WEIGHTS[tier]
    # Event-series formats are stable across years; only course/date need rotate.
    return seeded_rng(2027,seed,'format:'+series_id).choices(
        [x[0] for x in opts],weights=[x[1] for x in opts],k=1)[0]


def allowed_weeks(region,tier):
    weeks = [w for w in range(1,53) if w not in MAJORS and (tier!=1 or w>=4)]
    preferred = {
        'Americas':set(range(4,49)),
        'Europe':set(range(10,44)),
        'Asia':set(range(1,48)),
        'Africa':set(range(1,18))|set(range(32,53)),
        'Oceania':set(range(1,19))|set(range(38,53)),
    }[region]
    return weeks,preferred


def choose_tour_weeks(year,seed,region,tier,count,tour_name,excluded=()):
    choices, preferred = allowed_weeks(region,tier)
    r=seeded_rng(year,seed,'week:'+tour_name)
    picks=[]
    for _ in range(count):
        candidates=[w for w in choices if w not in picks and w not in excluded]
        weights=[3 if w in preferred else .5 for w in candidates]
        picks.append(r.choices(candidates,weights=weights,k=1)[0])
    return sorted(picks)


def make_row(year,week,series_id,name,tour,region,tier,kind,course,policy,host,holes,field,
             qualification_target='',qualification_slots=0,qualification_rule='',anchor=False,cut_override=None,
             advancement_path='',advancement_rule='',advancement_slots=0):
    if holes not in ROUND_DAYS:
        raise ValueError(f'Invalid number of holes: {holes}')
    cut_after=0
    cut_top=0
    if holes==72 and kind in ('major','regular','national_open'):
        cut_after=36
        cut_top=cut_override if cut_override is not None else {1:65,2:65,3:55,4:0}.get(tier,0)
    elif holes==54 and kind=='national_open':
        cut_after=36
        cut_top=60
    elif holes==54 and tier==2 and kind=='regular':
        cut_after=36
        cut_top=65
    if not cut_top:cut_after=0
    if kind=='major':
        prestige,purse=100,17_000_000
    elif kind=='qualifying':
        # Real qualifying/amateur events do not pay prize purses.
        prestige=min(78,35+PRESTIGE_FORMAT[holes]+(10 if anchor else 0))
        purse=0
    else:
        prestige=min(97,BASE_PRESTIGE[tier]+PRESTIGE_FORMAT[holes]+(8 if kind=='national_open' else 0))
        purse=round(BASE_PURSE[tier]*PURSE_FORMAT[holes]*(1.4 if kind=='national_open' else 1)/1000)*1000
    # Smaller number = higher scheduling and field-allocation priority.
    # This is distinct from the event's prestige score and never overrides
    # global-major blackout weeks or a locked tournament field.
    priority=(0 if kind=='major' else
              1 if anchor and kind=='qualifying' else
              2 if anchor and kind=='national_open' else
              3 if tier==1 else
              4 if kind=='qualifying' else
              5 if tier==2 else 6 if tier==3 else 7)
    return dict(year=year,week=week,entry_priority=priority,series_id=series_id,event_id=f'{year}:{series_id}',
        event=name,tour=tour,region=region,tier=tier,kind=kind,course=course,course_policy=policy,
        host_country=host,holes=holes,rounds=holes//18,round_days=ROUND_DAYS[holes],
        field_target=field,cut_after_holes=cut_after,cut_top_n=cut_top,prestige=prestige,
        purse_usd=purse,qualification_target=qualification_target,
        qualification_slots=qualification_slots,qualification_rule=qualification_rule,
        advancement_path=advancement_path,advancement_rule=advancement_rule,advancement_slots=advancement_slots,
        fixed_week_anchor=int(anchor))


def get_schedule(year=2027,seed=1217):
    rows=[];occupied=set()
    tours_by_name={t[0]:t for t in TOURS}
    national_weeks_by_tour=defaultdict(set)
    national_counts=Counter()

    # Reserve the global majors before the rest of the annual calendar.
    for week,(name,course,policy,field,cut) in MAJORS.items():
        if policy=='rotating':
            r=seeded_rng(year,seed,f'major-course:{name}')
            venue_num=((year-2027)*7+list(MAJORS).index(week)*11+r.randrange(7))%39+1
            course=f'World Championship Venue {venue_num:02}'
        rows.append(make_row(year,week,f'MAJOR_{week}',name,'World Major','Global',0,
            'major',course,policy,'',72,field,anchor=True,cut_override=cut))
        occupied.add((week,course))

    # Historic final qualifiers are fixed-week series. Earlier local/regional
    # qualifying stages also appear in the calendar, explicitly linked.
    for index,(week,name,holes,field,target,slots,rule) in enumerate(QUALIFIERS,1):
        series_id={13:'QUAL_LEGENDS_FINAL',18:'QUAL_PREMIER_FINAL',23:'QUAL_AMERICAN_FINAL',
                   29:'QUAL_BRITTANIA_FINAL',16:'QUAL_AMERICAN_REGIONAL_EAST',
                   17:'QUAL_AMERICAN_REGIONAL_WEST'}.get(week)
        if not series_id:
            series_id=f'QUAL_{name.upper().replace(" ","_").replace("-","_")}'
        course=f'Qualifying Venue {index:02d}'
        rows.append(make_row(year,week,series_id,name,'Qualifying Circuit','Global',5,
            'qualifying',course,'rotating','',holes,field,target,slots,rule,
            anchor=week in (13,18,23,29)))
        occupied.add((week,course))

    # Assign each national championship a long-lived host circuit, even when
    # its course and date rotate. That keeps tour event-series IDs stable.
    for region,countries in COUNTRIES.items():
        host_choices=[t for t in TOURS if t[1]==region and t[2] in (2,3)]
        for index,country in sorted(enumerate(countries),key=lambda item:item[1] not in ANCHOR_NATIONAL):
            anchored=country in ANCHOR_NATIONAL
            if anchored:
                week,tour_name=ANCHOR_NATIONAL[country]
            else:
                tour_name=host_choices[index%len(host_choices)][0]
                _,_,tier,_=tours_by_name[tour_name]
                choices,preferred=allowed_weeks(region,tier)
                available=[w for w in choices if w not in national_weeks_by_tour[tour_name]]
                rnd=seeded_rng(year,seed,'national-week:'+country)
                week=rnd.choices(available,weights=[3 if w in preferred else .5 for w in available],k=1)[0]
            _,_,tier,total_tour_events=tours_by_name[tour_name]
            if week in national_weeks_by_tour[tour_name]:
                raise AssertionError(f'National opens double-book tour {tour_name} in week {week}')
            national_weeks_by_tour[tour_name].add(week)
            national_counts[tour_name]+=1
            if national_counts[tour_name]>total_tour_events:
                raise AssertionError(f'Too many nationals on {tour_name}')
            course=f'{country} Championship Course {(year-2027)%4+1}'
            if (week,course) in occupied:
                raise AssertionError(f'National venue clash {country}')
            occupied.add((week,course))
            holes=72 if anchored or seeded_rng(2027,seed,'national-format:'+country).random()<.48 else 54
            target='MAJOR_30' if anchored else ''
            path=f'TIER_{tier-1}_QUALIFYING' if not anchored and holes==72 else ''
            rows.append(make_row(year,week,f'NATIONAL_{country.upper().replace(" ","_")}',
                f'{country} National Open',tour_name,region,tier,'national_open',course,
                'rotating',country,holes,{1:120,2:110,3:95,4:75}[tier],
                target,1 if anchored else 0,'national_open_winner' if anchored else '',
                anchor=anchored,advancement_path=path,
                advancement_rule='winner_qualifying_eligibility' if path else '',
                advancement_slots=1 if path else 0))

    # Ordinary events use the remaining slots, without displacing the fixed
    # championship weeks already occupied by a given host tour.
    for tour_name,region,tier,total_events in TOURS:
        count=total_events-national_counts[tour_name]
        weeks=choose_tour_weeks(year,seed,region,tier,count,tour_name,
                                national_weeks_by_tour[tour_name])
        rnd=seeded_rng(year,seed,'course:'+tour_name)
        used=[]
        for ordinal,week in enumerate(weeks,1):
            possible=[c for c in COURSES[region] if (week,c) not in occupied and c not in used]
            if not possible:
                possible=[c for c in COURSES[region] if (week,c) not in occupied]
            course=rnd.choice(possible)
            used.append(course);occupied.add((week,course))
            series_id=f'TOUR_{tour_name.upper().replace(" ","_")}_{ordinal:02d}'
            holes=choose_format(year,seed,series_id,tier)
            advances=bool(holes==72 or (holes==54 and ordinal%3==0))
            path=f'TIER_{tier-1}_QUALIFYING' if advances and tier>1 else ''
            rows.append(make_row(year,week,series_id,f'{tour_name} Event {ordinal}',tour_name,
                region,tier,'regular',course,'rotating','',holes,
                {1:120,2:110,3:95,4:75}[tier],
                advancement_path=path,
                advancement_rule='winner_qualifying_eligibility' if path else '',
                advancement_slots=1 if path else 0))
    return sorted(rows,key=lambda x:(x['week'],x['entry_priority'],x['event']))

def audit(rows):
    errors=[]
    assert rows
    year=rows[0]['year']
    seen_tour_weeks=Counter();seen_courses=Counter();ids=Counter();series=Counter()
    by_id={r['series_id']:r for r in rows}
    seen_national=[]
    for row in rows:
        wk,holes=row['week'],row['holes']
        ids[row['event_id']]+=1;series[row['series_id']]+=1
        seen_courses[(wk,row['course'])]+=1
        if row['kind'] not in ('major','qualifying'):
            seen_tour_weeks[(row['tour'],wk)]+=1
        if wk not in range(1,53):errors.append(f'Bad week: {wk}')
        if holes not in (18,36,54,72) or row['rounds']*18!=holes:errors.append(f'Invalid format: {row["event"]}')
        if row['round_days']!=ROUND_DAYS[holes]:errors.append(f'Round day mismatch: {row["event"]}')
        if row['cut_after_holes'] not in (0,36):errors.append(f'Invalid cut round: {row["event"]}')
        if row['cut_after_holes'] and (holes<54 or row['cut_top_n']<=0):errors.append(f'Invalid cut config: {row["event"]}')
        if holes<=36 and (row['cut_after_holes'] or row['cut_top_n']):errors.append(f'Short event has cut: {row["event"]}')
        if row['kind']=='major' and (holes!=72 or row['prestige']!=100):errors.append(f'Major format wrong: {row["event"]}')
        if row['kind']=='qualifying' and row['purse_usd']!=0:errors.append(f'Qualifying has purse: {row["event"]}')
        if row['kind']=='national_open':
            seen_national.append(row['host_country'])
            if holes<54:errors.append(f'National open too short: {row["event"]}')
        target=row['qualification_target']
        if target.startswith('MAJOR_'):
            dest=by_id.get(target)
            if not dest:errors.append(f'Unknown major target {target}')
            elif wk>=dest['week']:errors.append(f'Qualifier after or during major: {row["event"]}')
            if holes<36:errors.append(f'18-hole event directly enters major: {row["event"]}')
        elif target and target.startswith('QUAL_'):
            dest=by_id.get(target)
            # Regional qualifying can pool multiple series for the next stage.
            if not dest:errors.append(f'Unknown qualifying target {target}')
            elif dest and wk>=dest['week']:errors.append(f'Qualifier after destination: {row["event"]}')
        if row['qualification_slots'] and not target:errors.append(f'Qualifier without target: {row["event"]}')
        if row['advancement_slots'] and not row['advancement_path']:
            errors.append(f'Advancement without destination: {row["event"]}')
        if row['advancement_path'] and holes<54:
            errors.append(f'Short regular tournament advances to next tour: {row["event"]}')
    for wk in range(1,53):
        events=[r for r in rows if r['week']==wk]
        if wk in MAJORS:
            if len(events)!=1 or events[0]['kind']!='major' or events[0]['event']!=MAJORS[wk][0]:
                errors.append(f'Week {wk} major blackout violation')
        if wk==1 and any(r['tier']==1 for r in events):errors.append('Week 1 premier event')
    for label,c in [('event_id',ids),('series_id',series),('tour-week',seen_tour_weeks),('course-week',seen_courses)]:
        errors.extend(f'Duplicate {label}: {k}' for k,n in c.items() if n>1)
    if len(rows)!=358:errors.append(f'Expected 358 fixtures, got {len(rows)}')
    if sum(r['kind']=='national_open' for r in rows)!=28:errors.append('National open count wrong')
    if sum(r['kind']=='major' for r in rows)!=4:errors.append('Major count wrong')
    if sum(r['kind']=='qualifying' for r in rows)!=len(QUALIFIERS):errors.append('Qualifying event count wrong')
    if len(set(seen_national))!=28:errors.append('Countries lack unique national opens')
    for country,(wk,tour) in ANCHOR_NATIONAL.items():
        x=[r for r in rows if r['host_country']==country and r['kind']=='national_open']
        if len(x)!=1 or x[0]['week']!=wk or x[0]['tour']!=tour or x[0]['holes']!=72:
            errors.append(f'Anchored national open broken: {country}')
    for wk in (13,18,23,29):
        anchors=[r for r in rows if r['week']==wk and r['kind']=='qualifying' and r['fixed_week_anchor']]
        if len(anchors)!=1:errors.append(f'Missing anchored final qualifier week {wk}')
    # Strictly test same-tier, same-event-kind format monotonicity.
    for tier in (1,2,3,4):
        lengths=sorted(set(x[0] for x in FORMAT_WEIGHTS[tier]))
        prev=None
        for holes in lengths:
            probe=make_row(year,2,f'PROBE_{tier}_{holes}','probe','Probe','Global',tier,'regular',
                           'probe','rotating','',holes,75)
            metrics=(probe['prestige'],probe['purse_usd'])
            if prev and any(a<=b for a,b in zip(metrics,prev)):
                errors.append(f'Length bonuses not increasing in tier {tier}')
            prev=metrics
    by_holes=Counter(r['holes'] for r in rows)
    by_tier=Counter('Major' if r['kind']=='major' else 'Qualifier' if r['kind']=='qualifying' else str(r['tier']) for r in rows)
    event_capacity=sum(r['holes']*r['field_target'] for r in rows if r['kind']!='qualifying')
    all_72_capacity=sum(72*r['field_target'] for r in rows if r['kind']!='qualifying')
    return dict(valid=not errors,errors=errors,year=year,fixtures=len(rows),
        majors=4,national_opens=28,qualifying_fixtures=len(QUALIFIERS),
        tour_and_major_events=len(rows)-len(QUALIFIERS),by_holes=dict(sorted(by_holes.items())),
        by_tier=dict(by_tier),direct_major_feeders=sum(bool(r['qualification_target'].startswith('MAJOR_')) for r in rows),
        qualifying_path_events=sum(bool(r['advancement_path']) for r in rows),
        annual_entrant_hole_capacity=event_capacity,all_72_entrant_hole_capacity=all_72_capacity,
        scheduled_hole_reduction_pct=round(100*(1-event_capacity/all_72_capacity),1))


def write_csv(path,rows):
    with open(path,'w',newline='',encoding='utf8') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def build(years=(2027,2028),seed=1217):
    summaries=[]
    for year in years:
        rows=get_schedule(year,seed)
        stats=audit(rows)
        if stats['errors']:raise AssertionError('\n'.join(stats['errors']))
        write_csv(OUT/f'calendar_{year}.csv',rows)
        weekly=[]
        for wk in range(1,53):
            events=[e for e in rows if e['week']==wk]
            count=Counter(e['tier'] for e in events)
            weekly.append(dict(year=year,week=wk,
                anchor_name='; '.join(e['event'] for e in events if e['fixed_week_anchor']),
                premier=count[1],challenger=count[2],regional=count[3],mini=count[4],
                qualifiers=count[5],national_opens=sum(e['kind']=='national_open' for e in events),
                holes_18=sum(e['holes']==18 for e in events),holes_36=sum(e['holes']==36 for e in events),
                holes_54=sum(e['holes']==54 for e in events),holes_72=sum(e['holes']==72 for e in events),
                total_events=len(events)))
        write_csv(OUT/f'week_by_week_{year}.csv',weekly)
        summaries.append(stats)
    (OUT/'audit_summary.json').write_text(json.dumps(summaries,indent=2),encoding='utf8')
    print(json.dumps(summaries,indent=2))

if __name__=='__main__':
    build()
