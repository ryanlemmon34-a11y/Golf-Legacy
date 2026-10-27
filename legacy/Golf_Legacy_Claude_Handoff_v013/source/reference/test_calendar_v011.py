#!/usr/bin/env python3
"""Repeatable validation tests for the 0.11 schedule contract."""
import json
from collections import Counter
from pathlib import Path
from calendar_generator_v011 import (
    get_schedule,audit,make_row,MAJORS,ANCHOR_NATIONAL,FORMAT_WEIGHTS,
    PRESTIGE_FORMAT,PURSE_FORMAT,QUALIFIERS,
)

SEEDS=(42,1217,2601,202,404)
YEARS=range(2027,2087)


def run():
    report=[]
    for seed in SEEDS:
        first=None
        for year in YEARS:
            rows=get_schedule(year,seed)
            stats=audit(rows)
            assert stats['valid'],(seed,year,stats['errors'])
            assert len(rows)==358 and len({r['series_id'] for r in rows})==358
            # No double-booked course, active circuit or major blackout event.
            assert len([r for r in rows if r['week']==14])==1
            assert all(sum(r['kind']=='major' and r['week']==w for r in rows)==1 for w in MAJORS)
            assert all(r['rounds']*18==r['holes'] for r in rows)
            assert any(r['holes']==18 and r['tier']==4 for r in rows)
            assert all(r['cut_after_holes']==0 for r in rows if r['holes']<=36)
            assert all(r['purse_usd']==0 for r in rows if r['kind']=='qualifying')
            assert all(r['purse_usd']>0 for r in rows if r['kind'] in ('regular','national_open','major'))
            by_series={r['series_id']:r for r in rows}
            if first is None:
                first=by_series
            else:
                assert first.keys()==by_series.keys(), (seed,year,'series stability')
                assert all(first[k]['holes']==by_series[k]['holes'] for k in first), (seed,year,'length stability')
                assert all(first[k]['prestige']==by_series[k]['prestige'] for k in first), (seed,year,'prestige stability')
                assert all(first[k]['purse_usd']==by_series[k]['purse_usd'] for k in first), (seed,year,'purse stability')
            for country,(wk,_) in ANCHOR_NATIONAL.items():
                event=by_series['NATIONAL_'+country.upper().replace(' ','_')]
                assert event['week']==wk and event['holes']==72
                assert event['qualification_target']=='MAJOR_30'
                assert event['qualification_slots']==1
            # Every staged pathway is a true link to a future-week event.
            for r in rows:
                if r['qualification_target']:
                    target=by_series[r['qualification_target']]
                    assert r['week']<target['week'], (seed,year,r['event'])
                    assert r['qualification_slots']>=1
                if r['advancement_path']:
                    assert r['holes']>=54 and r['advancement_slots']>=1
            # No major has a cut when below 36 holes; all majors are 72.
            assert all(r['holes']==72 and r['cut_after_holes']==36 for r in rows if r['kind']=='major')
        report.append({'seed':seed,'years_tested':60,'total_calendar_editions':358*60,
                       'major_week_failures':0,'series_format_drift':0,'qualification_chronology_failures':0})
    # Same seed/year must be bit-for-bit repeatable.
    assert get_schedule(2027,1217)==get_schedule(2027,1217)
    # Within a tier, a longer ordinary event must never have a smaller purse/prestige.
    for tier in (1,2,3,4):
        vals=[]
        for holes,_ in FORMAT_WEIGHTS[tier]:
            r=make_row(2027,2,f'X{tier}_{holes}','test','Tour','Global',tier,
                       'regular','Test Course','rotating','',holes,75)
            vals.append((holes,r['prestige'],r['purse_usd']))
        assert all(a[1]<b[1] and a[2]<b[2] for a,b in zip(vals,vals[1:])), (tier,vals)
    return report

if __name__=='__main__':
    result=run()
    output=Path(__file__).resolve().parent/'long_run_schedule_audit.json'
    output.write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2))
    print('PASSED: 300 season schedules, fixed majors, qualifying chronology, stable series formats and prizes')
