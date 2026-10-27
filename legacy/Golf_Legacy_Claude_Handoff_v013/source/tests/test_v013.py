"""v0.13 targeted integration acceptance tests.

Run: PYTHONPATH=. python -m unittest discover -s tests -v
"""
from __future__ import annotations
import sqlite3, tempfile,unittest
from collections import Counter
from pathlib import Path
from engine_v013 import World,revised_calendar,MAJOR_WEEKS
from rankings import RankingBook,age_weight,divisor,tie_positions
from history_store import HistoryStore

class RankingMathTests(unittest.TestCase):
 def test_rolling_weight(self):
  self.assertEqual(age_weight(0),1)
  self.assertEqual(age_weight(13),1)
  self.assertAlmostEqual(age_weight(14),90/91)
  self.assertAlmostEqual(age_weight(103),1/91)
  self.assertEqual(age_weight(104),0)
  self.assertEqual(divisor(0),40)
  self.assertEqual(divisor(30),40)
  self.assertEqual(divisor(50),50)
  self.assertEqual(divisor(78),52)
 def test_field_ties_and_ranking_event_eligibility(self):
  scores={1:280,2:281,3:281,4:284}
  positions=tie_positions([1,2,3,4],scores,1)
  self.assertEqual(positions[2],(2,(2,3)))
  self.assertEqual(positions[3],(2,(2,3)))
  book=RankingBook(); book.register_starts(10,36,'regular',4,[1,2,3,4])
  self.assertFalse(book.award_event('18',10,18,'regular',4,50,positions,scores))
  self.assertFalse(book.award_event('36',10,36,'regular',3,50,positions,scores))
  self.assertEqual(len(book.starts),0)
  a=book.award_event('72',10,72,'regular',2,50,positions,scores)
  b=book.award_event('54',12,54,'regular',2,50,positions,scores)
  self.assertAlmostEqual(b[1]/a[1],.75)
  self.assertAlmostEqual(a[2],a[3])
  book.register_starts(10,72,'regular',2,[1,2,3,4]);book.register_starts(12,54,'regular',2,[1,2,3,4])
  ranked=book.update(12,[1,2,3,4]);self.assertEqual(next(iter(ranked)),1)
  rank_104=book.update(116,[1,2,3,4]);self.assertEqual(rank_104[1],0)

class CalendarTests(unittest.TestCase):
 def test_major_week_blackouts_and_invariant_series(self):
  for seed in (42,1217,2601):
   baseline=None
   for year in (2027,2028,2035,2086):
    rows=revised_calendar(year,seed)
    self.assertEqual(len(rows),360)
    self.assertEqual(Counter(r['premier_class'] for r in rows if r['tier']==1),
                     Counter(flagship=8,standard=20,opportunity=8))
    for week in MAJOR_WEEKS:
     self.assertEqual(len([r for r in rows if r['week']==week]),1)
    for week in (15,20,25,31):
     self.assertGreaterEqual(len([r for r in rows if r['week']==week and r['premier_class']=='opportunity']),1)
    self.assertEqual(sum(r['tier']==1 for r in rows),36)
    self.assertEqual(sum(r['tier']==0 for r in rows),4)
    self.assertEqual(len({r['series_id'] for r in rows}),360)
    now={r['series_id']:(r['holes'],r['prestige'],r['purse_usd']) for r in rows}
    if baseline is None:baseline=now
    else:self.assertEqual(now,baseline)
    for r in rows:
     if r['qualification_target'].startswith('MAJOR_'):
      target={14:14,19:19,24:24,30:30}[int(r['qualification_target'].split('_')[1])]
      self.assertLess(r['week'],target)

class TournamentEngineTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.db=Path(self.tmp.name)/'test.sqlite'
  self.w=World(seed=1217,population=450,events_scale=1,db_path=self.db)
  for g in self.w.golfers.values():self.w.economics.begin_season(g,2027)
  self.schedule=self.w._schedule()
 def tearDown(self):
  self.w.history.close()
  self.tmp.cleanup()
 def play(self,event):
  week=event[0]
  for g in self.w.golfers.values():self.w.economics.advance_to_week(g,2027,week)
  self.w._simulate_event(event)
 def test_all_four_formats_and_archived_round_integrity(self):
  done={}
  for row in self.w.fixture_rows:
   if row['kind']=='qualifying' and row['qualification_rule']=='direct_amateur_win':continue
   h=row['holes']
   if h not in done and row['kind']=='regular':done[h]=row
  self.assertEqual(set(done),{18,36,54,72})
  for holes,row in sorted(done.items(),key=lambda pair:pair[1]['week']):
   event=next(e for e in self.schedule if e[2]==row['event'] and e[0]==row['week'])
   self.play(event)
   sql=self.w.history.db
   eid=self.w.current_event_id
   entries=sql.execute('SELECT golfer_id,completed_holes FROM entries WHERE event_id=?',(eid,)).fetchall()
   self.assertTrue(entries)
   if holes<=36:self.assertTrue(all(n==holes for _,n in entries))
   else:self.assertTrue(all(n in (36,holes) for _,n in entries))
   rounds=sql.execute('SELECT golfer_id,round_no,holes,gross_strokes,start_tee FROM rounds WHERE event_id=?',(eid,)).fetchall()
   self.assertTrue(all(len(blob)==18 and sum(blob)==score for _,_,blob,score,_ in rounds))
   self.assertTrue(all(tee in (1,10) for *_,tee in rounds))
   if holes==18:self.assertTrue(all(no==1 for _,no,*_ in rounds))
   if holes==36:self.assertTrue(all(no in (1,2) for _,no,*_ in rounds))
   self.assertEqual(sql.execute('select count(*) from entries where event_id=? and position=1',(eid,)).fetchone()[0],1)
   self.assertEqual(self.w.purse_audits[-1]['purse_cents'],self.w.purse_audits[-1]['paid_cents'])
  self.assertEqual(self.w.history.audit()['bad_round_sums'],0)
 def test_qualifier_win_enters_next_week_major_with_source(self):
  for wk in (13,14):
   ev=next(e for e in self.schedule if e[0]==wk and
          ('Final Invitational Qualifier' in e[2] if wk==13 else 'Legends of Golf Masters' in e[2]))
   self.play(ev)
   if wk==13:
    winner=self.w.event_history[-1]['winner_id']
    self.assertTrue(any(x['target_series']=='MAJOR_14' and x['golfer_id']==winner
                        for x in self.w.exemption_ledger))
   self.w._commit_week(wk)
  row=self.w.history.db.execute('SELECT entry_reason FROM entries WHERE event_id=? AND golfer_id=?',
    (self.w.current_event_id,winner)).fetchone()
  self.assertEqual(row,('earned_qualifier_or_national_exemption',))
  incorrect=self.w.history.db.execute('''SELECT COUNT(*) FROM exemptions x
                   WHERE x.source_event NOT IN (SELECT event_id FROM events)''').fetchone()[0]
  self.assertEqual(incorrect,0)
 def test_national_open_winner_is_invited_to_brittania_major(self):
  national=next(e for e in self.schedule if e[0]==27 and e[2]=='Australia National Open')
  major=next(e for e in self.schedule if e[0]==30 and e[2]=='Brittania Open')
  self.play(national)
  champion=self.w.event_history[-1]['winner_id']
  self.assertTrue(any(r['golfer_id']==champion and r['target_series']=='MAJOR_30'
                      and r['source_type']=='national_open_winner'
                      for r in self.w.exemption_ledger))
  self.w._commit_week(27)
  self.play(major)
  reason=self.w.history.db.execute('SELECT entry_reason FROM entries WHERE event_id=? AND golfer_id=?',
                   (self.w.current_event_id,champion)).fetchone()
  self.assertEqual(reason,('earned_qualifier_or_national_exemption',))

 def test_amateur_only_qualifier_must_not_fabricate_pro_winner(self):
  ev=next(e for e in self.schedule if 'Legends Amateur Qualifier - Asia-Pacific' in e[2])
  self.play(ev)
  self.assertEqual(self.w.stats['amateur_only_qualifier_deferred'],1)
  self.assertEqual(self.w.history.db.execute('SELECT count(*) FROM exemptions').fetchone()[0],0)
 def test_sqlite_reopen_and_compact_historical_scoring(self):
  ev=next(e for e in self.schedule if e[0]!=14 and self.w.fixtures[(2027,e[0],e[2])]['holes']==18)
  self.play(ev)
  expected=self.w.history.audit()
  self.w.history.checkpoint_season()
  con=sqlite3.connect(self.db)
  self.assertEqual(con.execute('SELECT count(*) FROM rounds').fetchone()[0],expected['rounds'])
  self.assertTrue(all(len(b)==18 for (b,) in con.execute('select holes from rounds')))
  con.close()

if __name__=='__main__':unittest.main()
