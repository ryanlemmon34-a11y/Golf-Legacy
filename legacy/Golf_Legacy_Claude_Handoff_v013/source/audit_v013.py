"""Independent, read-only integrity audit of a Golf Legacy v0.13 SQLite save."""
from __future__ import annotations
import argparse,json,sqlite3,zlib
from collections import Counter,defaultdict
from pathlib import Path

def audit(path):
 con=sqlite3.connect(str(path))
 errors=[];counts=Counter()
 events={r[0]:dict(year=r[1],week=r[2],holes=r[3],kind=r[4],purse=r[5],
                   winner=r[6],cut_line=r[7],entrants=r[8]) for r in con.execute(
  'SELECT event_id,year,week,holes,kind,purse_usd,winner_id,cut_line,entrants FROM events')}
 entries={};entries_by_event=defaultdict(list)
 for eid,gid,pos,gross,comp,money,reason in con.execute(
   'SELECT event_id,golfer_id,position,gross_strokes,completed_holes,purse_usd,entry_reason FROM entries'):
  counts['entries']+=1;entries[(eid,gid)]=(pos,gross,comp,money,reason)
  entries_by_event[eid].append((gid,pos,gross,comp,money))
 rounds_by_entry=defaultdict(dict);group_members=defaultdict(list)
 for eid,gid,rd,gross,blob,pair,tee,slot in con.execute(
  'SELECT event_id,golfer_id,round_no,gross_strokes,holes,pairing_id,start_tee,start_slot FROM rounds'):
  counts['rounds']+=1;counts['holes']+=18
  if len(blob)!=18 or sum(blob)!=gross:errors.append(f'Bad round bytes {eid}:{gid}:{rd}')
  if not 1<=rd<=events[eid]['holes']//18:errors.append(f'Invalid round number {eid}:{gid}:{rd}')
  if tee not in (1,10):errors.append(f'Invalid start tee {eid}:{gid}:{rd}')
  rounds_by_entry[(eid,gid)][rd]=gross
  group_members[(eid,rd,pair)].append((gid,tee,slot))
 for (eid,gid),(pos,gross,comp,money,reason) in entries.items():
  scores=rounds_by_entry.get((eid,gid),{})
  expected=18*len(scores)
  if comp!=expected or sum(scores.values())!=gross:
   errors.append(f'Gross/holes mismatched {eid}:{gid}')
  if scores and sorted(scores)!=list(range(1,len(scores)+1)):
   errors.append(f'Nonconsecutive round participation {eid}:{gid}')
  n=events[eid]['holes']
  if n<=36 and comp!=n:errors.append(f'Uncut short event incomplete {eid}:{gid}')
  if n>=54 and comp not in (36,n):errors.append(f'Invalid event duration {eid}:{gid}')
 for (eid,rd,pair),members in group_members.items():
  maximum=3 if rd<=2 else 2
  if len(members)>maximum or len({x[0] for x in members})!=len(members):
   errors.append(f'Broken pairing {eid}:{rd}:{pair}')
  if len({(x[1],x[2]) for x in members})!=1:
   errors.append(f'Broken tee/schedule {eid}:{rd}:{pair}')
 for eid,e in events.items():
  results=entries_by_event[eid]
  if len(results)!=e['entrants']:errors.append(f'Field size mismatch {eid}')
  winners=[r for r in results if r[1]==1]
  if len(winners)!=1 or winners[0][0]!=e['winner']:
   errors.append(f'No sole correct winner {eid}')
  finishers=[r for r in results if r[1] is not None]
  if finishers and min(r[2] for r in finishers)!=winners[0][2]:
   errors.append(f'Lowest stroke total not winner {eid}')
  if round(sum(r[4] for r in results)*100)!=round(e['purse']*100):
   errors.append(f'Prize purse mismatch {eid}')
  if e['holes']<54 and any(r[1] is None for r in results):
   errors.append(f'Short event has a cut {eid}')
  if e['cut_line'] is not None:
   for gid,pos,gross,comp,money in results:
    rr=rounds_by_entry[eid,gid];two=rr.get(1,0)+rr.get(2,0)
    if (two<=e['cut_line']) != (pos is not None):
     errors.append(f'Cut line/tie mismatch {eid}:{gid}')
 counts['events']=len(events)
 bad_same_week=con.execute('''SELECT count(*) FROM
   (SELECT e.year,e.week,x.golfer_id FROM events e JOIN entries x ON x.event_id=e.event_id
    GROUP BY e.year,e.week,x.golfer_id HAVING count(*)>1)''').fetchone()[0]
 if bad_same_week:errors.append(f'Duplicated golfer-week entries {bad_same_week}')
 counts['duplicate_golfer_weeks']=bad_same_week
 for week in (14,19,24,30):
  for yr in sorted(set(e['year'] for e in events.values())):
   comp=[e for e in events.values() if e['week']==week and e['year']==yr]
   if len(comp)!=1 or comp[0]['kind']!='major':errors.append(f'Major week violation {yr}:{week}')
 bad_sources=con.execute('''SELECT count(*) FROM exemptions WHERE
    source_event NOT IN (SELECT event_id FROM events)''').fetchone()[0]
 if bad_sources:errors.append(f'Exemption source not in archive: {bad_sources}')
 counts['bad_exemption_sources']=bad_sources
 record_rows=con.execute('''SELECT course_id,year,week,event_id,strokes FROM course_record_history
                              ORDER BY course_id,year,week,rowid''').fetchall()
 prior={}
 for cid,year,week,eid,strokes in record_rows:
  if cid in prior and strokes>=prior[cid]:
   errors.append(f'Course record not improving: course={cid}, strokes={strokes}')
  prior[cid]=strokes
 counts['course_record_changes']=len(record_rows)
 prev_hole={}
 for cid,hole,year,week,eid,strokes in con.execute('''SELECT course_id,hole_number,year,week,event_id,strokes
      FROM hole_record_history ORDER BY course_id,hole_number,year,week,rowid'''):
  key=(cid,hole)
  if key in prev_hole and strokes>=prev_hole[key]:
   errors.append(f'Hole record not improving {key}: {strokes}')
  prev_hole[key]=strokes
 counts['hole_record_changes']=con.execute('SELECT count(*) FROM hole_record_history').fetchone()[0]
 for year,week,blob in con.execute('SELECT year,week,snapshot FROM ranking_snapshots'):
  try:
   rr=json.loads(zlib.decompress(blob))
   if len(rr)!=len({x[0] for x in rr}):errors.append(f'Duplicate ranks W{year}:{week}')
  except Exception as err:errors.append(f'Ranking archive unreadable {year}:{week} {err}')
 counts['weekly_rankings']=con.execute('SELECT count(*) FROM ranking_snapshots').fetchone()[0]
 counts['amateur_qualifiers_scored']=con.execute("SELECT count(*) FROM events WHERE event LIKE '%Legends Amateur Qualifier%'").fetchone()[0]
 con.close()
 return {'path':str(path),'passed':not errors,'errors':errors[:100],
         'error_count':len(errors),'counts':dict(counts)}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('db');p.add_argument('--output',default='')
 args=p.parse_args();result=audit(args.db);message=json.dumps(result,indent=2)
 if args.output:Path(args.output).write_text(message)
 print(message)
 raise SystemExit(0 if result['passed'] else 1)
