"""Local SQLite scorecard archive, with a one-season RAM staging area.

A player round stores an 18-byte scorecard in *physical hole* order and its
actual pairing/tee assignment. Completed seasons are atomically appended to a
permanent SQLite archive. The staging database is cleared only AFTER a
successful durable archive transaction, keeping history depth out of the hot
scoring/write path and avoiding year-over-year latency growth.

In a full game we will also archive at monthly save checkpoints, but these
benchmarks use year-end commits for efficient historical tests.
"""
from __future__ import annotations
import json, sqlite3, zlib
from pathlib import Path

DDL='''
CREATE TABLE IF NOT EXISTS events(
 event_id TEXT PRIMARY KEY, year INTEGER NOT NULL, week INTEGER NOT NULL,
 series_id TEXT NOT NULL, event TEXT NOT NULL, course_id INTEGER NOT NULL,
 holes INTEGER NOT NULL, tour TEXT NOT NULL, kind TEXT NOT NULL,
 purse_usd REAL NOT NULL, winner_id INTEGER NOT NULL, winning_to_par INTEGER NOT NULL,
 entrants INTEGER NOT NULL, finishers INTEGER NOT NULL, cut_line INTEGER, playoffs INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS events_series_year ON events(series_id,year);
CREATE INDEX IF NOT EXISTS events_course ON events(course_id,year);
CREATE TABLE IF NOT EXISTS entries(
 event_id TEXT NOT NULL, golfer_id INTEGER NOT NULL, position INTEGER,
 gross_strokes INTEGER NOT NULL, completed_holes INTEGER NOT NULL,
 purse_usd REAL NOT NULL, entry_reason TEXT NOT NULL,
 PRIMARY KEY(event_id,golfer_id));
CREATE INDEX IF NOT EXISTS entries_golfer ON entries(golfer_id,event_id);
CREATE TABLE IF NOT EXISTS rounds(
 event_id TEXT NOT NULL, golfer_id INTEGER NOT NULL, round_no INTEGER NOT NULL,
 gross_strokes INTEGER NOT NULL, holes BLOB NOT NULL,
 pairing_id INTEGER NOT NULL, start_tee INTEGER NOT NULL, start_slot INTEGER NOT NULL,
 PRIMARY KEY(event_id,golfer_id,round_no));
CREATE TABLE IF NOT EXISTS exemptions(
 target_series TEXT NOT NULL, golfer_id INTEGER NOT NULL, source_event TEXT NOT NULL,
 source_type TEXT NOT NULL, earned_year INTEGER NOT NULL, earned_week INTEGER NOT NULL,
 expires_year INTEGER NOT NULL, slots INTEGER NOT NULL,
 PRIMARY KEY(target_series,golfer_id,source_event));
CREATE INDEX IF NOT EXISTS exemptions_target ON exemptions(target_series,earned_year);
CREATE TABLE IF NOT EXISTS ranking_snapshots(
 year INTEGER NOT NULL, week INTEGER NOT NULL, snapshot BLOB NOT NULL,
 PRIMARY KEY(year,week));
CREATE TABLE IF NOT EXISTS hole_record_history(
 course_id INTEGER NOT NULL, hole_number INTEGER NOT NULL,
 year INTEGER NOT NULL, week INTEGER NOT NULL, event_id TEXT NOT NULL,
 golfer_id INTEGER NOT NULL, round_no INTEGER NOT NULL, strokes INTEGER NOT NULL,
 PRIMARY KEY(event_id,golfer_id,round_no,hole_number));
CREATE INDEX IF NOT EXISTS hole_record_course ON hole_record_history(course_id,hole_number,year);
CREATE TABLE IF NOT EXISTS course_record_history(
 course_id INTEGER NOT NULL, year INTEGER NOT NULL, week INTEGER NOT NULL,
 event_id TEXT NOT NULL, golfer_id INTEGER NOT NULL, round_no INTEGER NOT NULL, strokes INTEGER NOT NULL,
 PRIMARY KEY(event_id,golfer_id,round_no));
'''
TABLE_COLUMNS={
 'events':16, 'entries':7, 'rounds':8, 'exemptions':8,
 'ranking_snapshots':3, 'course_record_history':7, 'hole_record_history':8,
}
TABLE_ORDER=tuple(TABLE_COLUMNS)

class HistoryStore:
 def __init__(self,path=':memory:'):
  self.path=str(path)
  self.db=sqlite3.connect(':memory:')
  self.db.executescript(DDL)
  self.archive_db=None
  if self.path!=':memory:':
   Path(self.path).parent.mkdir(parents=True,exist_ok=True)
   self.archive_db=sqlite3.connect(self.path)
   self.archive_db.execute('PRAGMA journal_mode=DELETE')
   self.archive_db.execute('PRAGMA synchronous=FULL')
   self.archive_db.executescript(DDL)
  self.events_written=0
  self.archived_seasons=0

 def record_event(self,row,scores,positions,payouts,pairings,entry_reasons):
  eid=row['event_id']
  pairs={(p['round'],gid):p for p in pairings for gid in p['golfer_ids']}
  self.db.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(
   eid,row['year'],row['week'],row['series_id'],row['event'],row['course_id'],row['holes'],
   row['tour'],row['kind'],row['purse_usd'],row['winner_id'],row['to_par'],
   row['field'],row['made_cut'],row.get('cut_score'),row['playoff_holes']))
  entries=[];rounds=[]
  for gid,score in scores.items():
   cards=score['hole_cards'];completed=18*sum(any(card) for card in cards)
   entries.append((eid,gid,positions.get(gid),score['total'],completed,
                   payouts.get(gid,0.),entry_reasons.get(gid,'tour_membership')))
   for no,card in enumerate(cards,1):
    if not any(card):continue
    if len(card)!=18 or any(not 1<=v<=12 for v in card):raise AssertionError('corrupt 18-hole card')
    p=pairs[(no,gid)]
    rounds.append((eid,gid,no,score['round_scores'][no-1],bytes(card),
                   p['pairing_id'],p['tee'],p['tee_slot']))
  self.db.executemany('INSERT INTO entries VALUES (?,?,?,?,?,?,?)',entries)
  self.db.executemany('INSERT INTO rounds VALUES (?,?,?,?,?,?,?,?)',rounds)
  self.events_written+=1

 def add_exemption(self,row):
  self.db.execute('INSERT OR IGNORE INTO exemptions VALUES (?,?,?,?,?,?,?,?)',(
   row['target_series'],row['golfer_id'],row['source_event'],row['source_type'],
   row['earned_year'],row['earned_week'],row['expires_year'],row.get('slots',1)))

 def add_course_record(self,course_id,year,week,event_id,golfer_id,round_no,strokes):
  self.db.execute('INSERT OR IGNORE INTO course_record_history VALUES (?,?,?,?,?,?,?)',(
   course_id,year,week,event_id,golfer_id,round_no,strokes))

 def add_hole_record(self,course_id,hole_number,year,week,event_id,golfer_id,round_no,strokes):
  self.db.execute('INSERT OR IGNORE INTO hole_record_history VALUES (?,?,?,?,?,?,?,?)',(
   course_id,hole_number,year,week,event_id,golfer_id,round_no,strokes))

 def add_rankings(self,year,week,rankings):
  compact=[[gid,round(score,8)] for gid,score in rankings.items()]
  payload=zlib.compress(json.dumps(compact,separators=(',',':')).encode('utf8'),level=3)
  self.db.execute('INSERT OR REPLACE INTO ranking_snapshots VALUES (?,?,?)',(year,week,payload))

 def rankings_at(self,year,week):
  row=self.db.execute('SELECT snapshot FROM ranking_snapshots WHERE year=? AND week=?',(year,week)).fetchone()
  if not row and self.archive_db:
   row=self.archive_db.execute('SELECT snapshot FROM ranking_snapshots WHERE year=? AND week=?',(year,week)).fetchone()
  return json.loads(zlib.decompress(row[0])) if row else []

 def commit_week(self):
  # Weekly result integrity in RAM. The permanent snapshot is published at
  # the season boundary; future playable saves can use monthly checkpoints.
  self.db.commit()

 def checkpoint_season(self):
  """Append one season atomically to disk, then clear its RAM scorecards.

  This avoids writing through SQLite disk B-trees during every simulated hole.
  Future speed tests can change the archive frequency without changing golf.
  """
  self.db.commit()
  if self.archive_db is None:return
  # Native SQLite backup/INSERT-SELECT avoids issuing tens of thousands of
  # individual Python-to-disk inserts. All historical data stays intact.
  if self.archived_seasons==0:
   self.db.backup(self.archive_db,pages=512)
  else:
   self.db.execute('ATTACH DATABASE ? AS persistent',(self.path,))
   try:
    self.db.execute('BEGIN IMMEDIATE')
    for table in TABLE_ORDER:
     self.db.execute(f'INSERT INTO persistent.{table} SELECT * FROM main.{table}')
    self.db.commit()
   except:
    self.db.rollback()
    raise
   finally:
    self.db.execute('DETACH DATABASE persistent')
  for table in reversed(TABLE_ORDER):
   self.db.execute(f'DELETE FROM {table}')
  self.db.commit()
  self.archived_seasons+=1

 def audit(self):
  rows_bad=bad_sum=events=entries=rounds=snapshots=exemptions=duplicate=hole_records=0
  for conn in (self.db,self.archive_db):
   if conn is None:continue
   rows_bad+=conn.execute('SELECT count(*) FROM rounds WHERE length(holes)!=18').fetchone()[0]
   for gross,card in conn.execute('SELECT gross_strokes, holes FROM rounds'):
    bad_sum+=int(sum(card)!=gross)
   duplicate+=conn.execute('SELECT count(*)-count(DISTINCT year||":"||week||":"||event) FROM events').fetchone()[0]
   events+=conn.execute('SELECT count(*) FROM events').fetchone()[0]
   entries+=conn.execute('SELECT count(*) FROM entries').fetchone()[0]
   rounds+=conn.execute('SELECT count(*) FROM rounds').fetchone()[0]
   snapshots+=conn.execute('SELECT count(*) FROM ranking_snapshots').fetchone()[0]
   exemptions+=conn.execute('SELECT count(*) FROM exemptions').fetchone()[0]
   hole_records+=conn.execute('SELECT count(*) FROM hole_record_history').fetchone()[0]
  return {'events':events,'entries':entries,'rounds':rounds,'holes':rounds*18,
   'bad_round_lengths':rows_bad,'bad_round_sums':bad_sum,
   'duplicate_event_names_in_week':duplicate,'rankings_snapshots':snapshots,
   'exemptions':exemptions,'hole_record_changes':hole_records,'seasons_on_disk':self.archived_seasons}

 def close(self):
  self.db.commit()
  if self.archive_db:self.archive_db.close()
  self.db.close()
