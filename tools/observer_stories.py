"""Tournament stories (roadmap T1-T3): readable recaps written locally from recorded facts, each claim linked to
where it can be checked.

Three layers, none of which runs in the simulation (no narration in the shot or weekly loops; the engine and the
archive are unchanged and nothing here writes simulation state):

1. **Facts** (`assemble`): a structured record of one edition, from what the history recorded -- the field, each
   round's scores and leaders, the winner's path, any playoff, the world ranking the week before, the winner's
   earlier results, the tournament's earlier editions, the moments recorded during the event and, when the edition
   recorded one, the pre-event win estimate (its own `upset` record, golfsim/upsets.py). Every fact carries its
   source references ([label, href]): an edition page, a round of the replay, a profile's results, the ranking of
   that week, a course page, or the story's own inspection view for a recorded value no other page shows. Facts are taken **as of the event**: earlier results
   only, the ranking published the week before, the tournament's earlier editions. A story written later, after
   more seasons, says what it said when the season was archived. What was not recorded is listed in `missing`
   and left out of the prose (no shot paths, putt lengths, form draws or dates are ever made up; career counts of
   golfers who were already playing when the world began say "in the retained history").
2. **Pattern** (`patterns`): the story's shape from the facts -- playoff, upset (only when the edition's recorded
   pre-event estimate gave the winner under UPSET_P), comeback, runaway, wire-to-wire, first win, close finish, match play or a standard recap -- each with
   its own order of sections, so an upset opens with the odds and a runaway with the margin.
3. **Narrative** (`narrate`): sentences built from those facts with phrasing chosen deterministically by the
   edition (and perspective) -- never at random when viewed -- so a story reads the same every time it is opened,
   before or after a resume, while different editions do not all open alike. Only informative facts are used: a
   milestone, a record or a field-strength line appears when it says something, not as filler.

Caching (T3): stories are written when opened. The fact record is kept in `observer_cache/stories.sqlite` beside
the world (a temporary folder for histories browsed read-only) under (edition, perspective, site, FACT_VERSION,
the stamp of the seasons the facts are drawn from); the story under (that fact record's digest,
NARRATIVE_VERSION). The stamp of an archived edition covers only its own and earlier seasons, so later seasons
never invalidate it (the historical perspective is kept) while a recovery that republishes one of those seasons
does. An edition of the current season is stamped by the snapshot's generation (kept in memory only).

How they won (golf statistics): the edition's recorded golf-statistics counters (golfsim/golfstats.py, an
edition's `golf`, kept since the golf-statistics update; definitions at /rules#golf-statistics) give the winner's
putts, fairways hit of first tee shots on par 4s and 5s, measured driving distance, greens in regulation of holes
played, scrambling and greenside sand saves with their attempts, and strokes gained off the tee, on approach,
around the green and putting -- against the engine's own expected-strokes table, always labelled so, never as a
real-world baseline. The field comparison is among golfers who played the same number of rounds; the margin over a
single runner-up is split by strokes gained only when both have statistics for the same rounds, and any part the
strokes gained do not account for (penalties, rounding) is stated. Personal bests to that date (lowest putt total,
best strokes-gained putting and total weeks) compare weeks of the same number of rounds at story editions (majors,
Premier events and championships: the editions the story index keeps), strictly before the event, linked to the
earlier event, and say "in the retained history" for a career that began before the world. Nothing is said of
shots, putt lengths or form: none is recorded.

Indexes (T3): earlier wins and best finishes come from the archive index's starts by person, comparisons from its
editions by series, moments from its moments table -- all one query each, grown a season at a time as the history
is published. What a story needs of the season file itself (round scores, playoffs, the ranking of the week
before, the pre-event estimate) is kept in a per-season story index (`season_extract`) beside the cache, built
the first time a story of that season is opened (one decode, for all its story editions) and kept under the
season's published signature: a century of history opens each season's stories with a decode at most once, and
not again after a resume, while a republished season is indexed afresh. The same pass records every edition's
number of rounds (`edition_rounds`: the tournament's history compares 72-hole winners with 72-hole winners) and
each golfer's golf weeks at story editions (`golf_weeks`, indexed by golfer). A story that needs more than
INLINE_SEASONS unindexed seasons starts a background process that indexes the rest of the history once, says
meanwhile which comparisons are still being indexed, and keeps those facts for the session only.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sqlite3
import sys
import threading
import zlib
from collections import OrderedDict
from pathlib import Path
from urllib.parse import quote, urlencode

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from golfsim import golfstats as GS                                     # noqa: E402  (definitions only)

FACT_VERSION = 3
NARRATIVE_VERSION = 2

# pattern thresholds (strokes, or a probability), documented on the story page
UPSET_P = 0.03                 # recorded pre-event win estimate below 3 %
COMEBACK_FINAL = 3             # three or more behind entering the final round
COMEBACK_ANY = 5               # or five or more behind after an earlier round
RUNAWAY = 5                    # won by five or more
CLOSE = 1                      # won by one
GOLF_HISTORY_MIN = 3           # earlier comparable weeks needed before a personal-best claim is made
INLINE_SEASONS = 2             # seasons indexed while a story waits; more are indexed in the background
# the golf-statistics counters a story reads (golfsim/golfstats.py, definitions version 1; strokes gained in
# hundredths, against the engine's own expected-strokes table)
GOLF_KEYS = ('rounds', 'holes', 'strokes', 'drives', 'drive_tenths', 'fairways', 'fairway_att', 'gir', 'putts',
             'scr_att', 'scr_made', 'sand_att', 'sand_saves', 'penalties', 'sg_ott', 'sg_app', 'sg_arg', 'sg_putt')
SG_PARTS = (('sg_ott', 'off the tee'), ('sg_app', 'on approach'), ('sg_arg', 'around the green'),
            ('sg_putt', 'putting'))
SG_TABLE = ['the engine\'s expected-strokes table', '/rules#golf-statistics']
GOLF_SCOPE = 'among majors, Premier events and championships'   # the editions a story's index keeps (story_level)

MAJOR_SERIES = ('TOUR_MASTERS', 'PREMIER_TOUR_CHAMPIONSHIP', 'USA_OPEN', 'BRITANNIA_OPEN')
PRESTIGE_CATEGORIES = ('flagship', 'circuit_championship', 'national_open', 'national_amateur', 'elite_amateur',
                       'college_postseason')
QUALIFYING = ('qualifier', 'q_school')
PATTERN_NAMES = {'playoff': 'Playoff', 'upset': 'Upset', 'comeback': 'Comeback', 'runaway': 'Runaway victory',
                 'wire_to_wire': 'Wire to wire', 'first_win': 'First win', 'close_finish': 'Close finish',
                 'match_play': 'Match play', 'standard': 'Recap'}
STRUCTURES = {
    'playoff': ('lead', 'stakes', 'rounds', 'playoff', 'how', 'milestones', 'history', 'moments', 'perspective'),
    'upset': ('lead', 'upset', 'stakes', 'rounds', 'separation', 'how', 'milestones', 'history', 'moments', 'perspective'),
    'comeback': ('lead', 'comeback', 'stakes', 'rounds', 'separation', 'how', 'milestones', 'history', 'moments',
                 'perspective'),
    'runaway': ('lead', 'separation', 'how', 'stakes', 'rounds', 'milestones', 'history', 'moments', 'perspective'),
    'wire_to_wire': ('lead', 'rounds', 'separation', 'how', 'stakes', 'milestones', 'history', 'moments', 'perspective'),
    'first_win': ('lead', 'milestones', 'stakes', 'rounds', 'separation', 'how', 'history', 'moments', 'perspective'),
    'close_finish': ('lead', 'stakes', 'rounds', 'separation', 'how', 'milestones', 'history', 'moments', 'perspective'),
    'match_play': ('lead', 'stakes', 'matches', 'milestones', 'history', 'perspective'),
    'standard': ('lead', 'stakes', 'rounds', 'separation', 'how', 'milestones', 'history', 'moments', 'perspective'),
}


# ---- which editions get a story ---------------------------------------------------------------------------------
def is_major(e):
    return (e.get('kind') == 'major' or e.get('category') == 'major' or e.get('tour') == 'MAJORS'
            or e.get('tier') == 0 or e.get('series') in MAJOR_SERIES)


def story_level(e):
    """'major', 'premier' or 'prestige' for an edition offered a story (majors first, then the Premier Tour and
    each circuit's flagship and national championships), else None. Any edition's story can still be opened."""
    if not e or e.get('category') in QUALIFYING:
        return None
    if is_major(e):
        return 'major'
    if e.get('tier') == 1:
        return 'premier'
    if e.get('category') in PRESTIGE_CATEGORIES:
        return 'prestige'
    return None


def notable(r):
    """A start worth a story link on a profile or in My World: a win in a story edition, or a top-10 in a major
    or a top-5 in a Premier event (r: a results row with tier, category, tour, pos)."""
    lv = story_level(r)
    pos = r.get('pos')
    if lv is None or pos is None:
        return False
    return pos == 1 or (lv == 'major' and pos <= 10) or (lv == 'premier' and pos <= 5)


def story_href(eid, pid=None, facts=False):
    q = {'view': 'story'}
    if pid is not None:
        q['for'] = pid
    if facts:
        q['facts'] = 1
    return f'/event/{quote(eid)}?{urlencode(q)}'


# ---- where the facts come from ------------------------------------------------------------------------------------
class WorldSource:
    """The observer World as a fact source (the published history and the committed snapshot). Read-only.

    With a StoryCache, an archived season is read through its story index (`season_extract`): the first story
    of a season decodes the season file once and keeps every story edition's facts, the rankings of the weeks
    before them and the pre-event estimates, compressed, under the season's published signature; every other
    story of that season, in this session or after a resume, opens without decoding the season again."""

    def __init__(self, w, cache=None):
        self.w = w
        self.cache = cache

    def _archived(self, eid):
        w = self.w
        y = int(eid.split(':')[0])
        return not (w.live is not None and eid in w.live.editions) and bool(w.a) and y in w.a.years

    def season(self, y):
        """Season y's story index (None without a cache, or for a season not in the published history)."""
        w = self.w
        if self.cache is None or not (w.a and y in w.a.years):
            return None
        sig = str(w.a.signature(y))
        got = self.cache.get_season(y, sig)
        if got is None:
            import observer_history as OH
            d = OH._season_file(w, y)
            if d is None:
                return None
            got = season_extract(d)
            self.cache.put_season(y, sig, got)
        return got

    def edition(self, eid):
        import observer_history as OH
        w = self.w
        if self._archived(eid):
            y = int(eid.split(':')[0])
            ext = self.season(y)
            if ext is not None and eid in ext['events']:
                return {**ext['events'][eid], 'year': y, 'origin': 'archive'}
        e = w.edition(eid)
        if e is None:
            return None
        full = OH.full_edition(w, e)
        if full is None:
            return None
        out = dict(full)
        out['year'] = e['year']
        out['origin'] = 'live' if e.get('source') == 'current season' else 'archive'
        meta = w.series_info(out['series']) or {}
        out.setdefault('kind', meta.get('kind'))
        return out

    def person(self, pid):
        w = self.w
        p = w.person(pid) or {}
        initial = None
        if w.a and pid in w.a.people:
            initial = w.a.people[pid].get('initial')
        elif w.live is not None and pid in w.live.people:
            initial = w.live.people[pid].get('initial')
        return {'name': p.get('name') or f'#{pid}', 'country': p.get('country'), 'born': p.get('born'),
                'initial': initial}

    def first_year(self):
        w = self.w
        if w.a:
            return w.a.world.get('first_year', w.a.years[0] if w.a.years else None)
        return getattr(w.live, 'first_year', None) if w.live is not None else None

    def course(self, cid):
        return self.w.courses().get(cid) or {}

    def series(self, sid):
        return self.w.series_info(sid) or {}

    def starts(self, pid):
        import observer_data as OD
        return OD.results(self.w, pid)

    def series_editions(self, sid):
        return self.w.editions_of(sid)

    def indexed(self, years):
        """(the archived seasons among `years` whose story index matches the season as published, the number still
        being indexed). Up to INLINE_SEASONS missing seasons are indexed now; more start the background indexer
        (StoryCache.start_indexer) and are reported as pending."""
        w = self.w
        if self.cache is None or not w.a:
            return set(), 0
        sigs = {y: str(w.a.signature(y)) for y in years if y in w.a.years}
        have = self.cache.indexed_years(sigs)
        missing = sorted(set(sigs) - have)
        if missing and len(missing) <= INLINE_SEASONS:
            for y in missing:
                self.season(y)
            return set(sigs), 0
        if missing:
            every = {y: str(w.a.signature(y)) for y in w.a.years}
            done = self.cache.indexed_years(every)
            self.cache.start_indexer([[y, str(w.a.year_path(y)), every[y]] for y in sorted(set(every) - done)])
        return have, len(missing)

    def golf_history(self, pid, y, wk, eid):
        """(the golfer's golf weeks before (y, wk) at story editions: [{event, year, week, rounds, putts, sg_ott,
        sg_app, sg_arg, sg_putt}], seasons still being indexed), or (None, 0) without a story index."""
        w = self.w
        if self.cache is None or self.cache.path is None:
            return None, 0
        rows = [r for r in self.starts(pid) if (r['year'], r['week']) < (y, wk) and r['event'] != eid
                and story_level(r) and not r.get('live')]
        have, pending = self.indexed({r['year'] for r in rows})
        out = self.cache.golf_weeks(pid, sorted(have))
        out = [r for r in out if (r['year'], r['week']) < (y, wk) and r['event'] != eid]
        if w.live is not None:                           # the current season's earlier story editions
            for e in w.live.editions.values():
                if (int(e['id'].split(':')[0]), e['week']) >= (y, wk) or e['id'] == eid or not story_level(e):
                    continue
                for site in e.get('golf') or []:
                    v = site.get(str(pid)) or site.get(pid)
                    if v:
                        c = dict(zip(GS.FIELDS, v))
                        out.append({'event': e['id'], 'year': int(e['id'].split(':')[0]), 'week': e['week'],
                                    **{k: c[k] for k in ('rounds', 'putts', 'sg_ott', 'sg_app', 'sg_arg', 'sg_putt')}})
        return out, pending

    def series_results(self, sid, before=None):
        """[{event, year, week, layout, course, winner, winner_total, second_total, rounds}] of every edition
        (first site), from the archive index (one query) and the snapshot, with each edition's own number of
        rounds from the story index (None for a season not indexed yet); None without an index (not compared)."""
        w = self.w
        if not (w.a and w.a.index is not None) and w.a:
            return None
        out = []
        if w.a:
            idx = w.a.index
            q = ('SELECT e.event_id, e.year, e.week, si.course, si.layout, '
                 '(SELECT st.person FROM starts st WHERE st.eid = e.eid AND st.site = 0 AND st.pos = 1 ORDER BY st.rowid LIMIT 1), '
                 '(SELECT st.total FROM starts st WHERE st.eid = e.eid AND st.site = 0 AND st.pos = 1 ORDER BY st.rowid LIMIT 1), '
                 '(SELECT MIN(st.total) FROM starts st WHERE st.eid = e.eid AND st.site = 0 AND st.pos > 1) '
                 'FROM editions e LEFT JOIN sites si ON si.eid = e.eid AND si.site = 0 WHERE e.series = ?'
                 + idx.upto('e.year') + ' ORDER BY e.year, e.week')
            out = [{'event': eid, 'year': y, 'week': wk, 'course': c, 'layout': lay, 'winner': g,
                    'winner_total': t, 'second_total': s2, 'rounds': None}
                   for eid, y, wk, c, lay, g, t, s2 in idx.db.execute(q, (sid,))]
            want = [r for r in out if before is None or (r['year'], r['week']) < tuple(before)]
            have, _ = self.indexed({r['year'] for r in want})
            known = self.cache.edition_rounds([r['event'] for r in want if r['year'] in have]) if self.cache else {}
            for r in out:
                r['rounds'] = known.get(r['event'])
        if w.live is not None:
            for e in w.live.editions.values():
                if e['series'] != sid or not e['finish'] or not e['finish'][0]:
                    continue
                fin = e['finish'][0]
                win = next(((g, t) for g, p, t in fin if p == 1), (None, None))
                others = [t for g, p, t in fin if p is not None and p > 1 and t is not None]
                out.append({'event': e['id'], 'year': int(e['id'].split(':')[0]), 'week': e['week'],
                            'course': e['sites'][0][0], 'layout': e['sites'][0][1], 'winner': win[0],
                            'winner_total': win[1], 'second_total': min(others) if others else None,
                            'rounds': e.get('rounds')})
        return out

    def ranking(self, year, week, amateur=False):
        """The ranking published after (year, week): {'order': [pids, No. 1 first], 'href'} or None."""
        w = self.w
        if week < 1:
            year, week = year - 1, 52
        live_year = w.live.year if w.live is not None else None
        href = f'/rankings?{urlencode({"kind": "points", "year": year, "week": week})}'
        ext = self.season(year) if not (live_year == year and not (w.a and year in w.a.years)) else None
        if ext is not None:
            got = (ext['amateur'] if amateur else ext['world']).get(str(week))
            if got is not None:
                if amateur or not got['points']:
                    return {'order': got['order'], 'href': _order_href(amateur, year, week),
                            'year': year, 'week': week, 'order_only': True}
                return {'order': got['order'], 'href': href, 'year': year, 'week': week}
        if live_year == year and not (w.a and year in w.a.years):
            if amateur:
                return None
            rows = (getattr(w.live, 'rank_top', {}) or {}).get(week)
            return {'order': [r[0] for r in rows], 'href': href, 'year': year, 'week': week} if rows else None
        if not (w.a and year in w.a.years):
            return None
        import observer_golf as OG
        d = OG._rankings(w, year) or {}
        if not amateur:
            rows = (d.get('ranking_points') or {}).get(str(week))
            if rows:
                return {'order': [r[0] for r in rows], 'href': href, 'year': year, 'week': week}
        order = ((d.get('rankings') or {}).get('amateur' if amateur else 'world') or {}).get(str(week))
        if order:
            return {'order': list(order), 'href': _order_href(amateur, year, week), 'year': year,
                    'week': week, 'order_only': True}
        return None

    def moments(self, eid):
        w = self.w
        y = int(eid.split(':')[0])
        if w.live is not None and eid in w.live.editions:
            return [m for m in (getattr(w.live, 'moments', None) or []) if m.get('event') == eid]
        if not (w.a and y in w.a.years):
            return []
        if w.a.index is not None:                    # (one query over the small moments table)
            idx = w.a.index
            return [dict(json.loads(d), kind=k, person=p, event=e, layout=lay, week=wk)
                    for d, k, p, e, lay, wk in idx.db.execute(
                        'SELECT detail, kind, person, event_id, layout, week FROM moments WHERE year = ? AND event_id = ? '
                        'ORDER BY rowid', (y, eid))]
        return [m for m in (w.a.year(y).get('moments') or []) if m.get('event') == eid]

    def stamp(self, eid):
        """What identifies the facts' inputs: an archived edition's own and earlier seasons as published (later
        seasons never change it), or the snapshot's generation for the current season."""
        w = self.w
        y = int(eid.split(':')[0])
        if w.live is not None and eid in w.live.editions:
            return f'live:{w.live.generation}'
        if not (w.a and y in w.a.years):
            return None
        sigs = [str(w.a.signature(yy)) for yy in w.a.years if yy <= y]
        return 'archive:' + hashlib.sha1('|'.join(sigs).encode()).hexdigest()

    def cacheable(self, eid):
        """Archived editions are cached on disk; the current season's only in memory (they change weekly)."""
        w = self.w
        return not (w.live is not None and eid in w.live.editions)


def _order_href(amateur, year, week):
    """The recorded order of a past week's world or amateur ranking (the Rankings page, that week)."""
    return f'/rankings?{urlencode({"kind": "amateur" if amateur else "world", "year": year, "week": week})}'


# ---- the story index of a season (compact, built once per published season) ----------------------------------------
EXTRACT_VERSION = 3
EXTRACT_KEYS = ('id', 'series', 'week', 'name', 'tour', 'tier', 'category', 'kind', 'rounds', 'match_play', 'sites',
                'finish', 'scores', 'playoff', 'playoffs', 'matches', 'prestige', 'field_size', 'upset')


def season_extract(d):
    """What stories read of one season file, for its story editions only (`story_level`): each edition's
    classification, sites, finish, round scores, playoffs and matches and the winners' teams (no hole-by-hole
    cards, statistics, prizes or routes) and its recorded pre-event estimate (`upset`); the world ranking (top 200
    order) of each week before one of them and of week 52 (the next season's week-1 events), the amateur ranking
    likewise. Also each story edition's golf statistics (GOLF_KEYS of every golfer, `golf_keys` naming them), the
    number of rounds of every edition of the season (`rounds_of`: comparisons are made format to format) and
    each golfer's golf weeks at story editions (`golf_weeks`: their personal bests to any date). A few hundred
    kilobytes a season compressed, against the whole season file."""
    evs, weeks, am_weeks = {}, {52}, {52}
    rounds_of, golf_weeks = {}, []
    pick = [GS.IDX[k] for k in GOLF_KEYS]
    for e in d.get('events', []):
        rounds_of[e['id']] = e.get('rounds')
        if not story_level(e):
            continue
        x = {k: e[k] for k in EXTRACT_KEYS if k in e}
        wins = {g for site in e.get('finish') or [] for g, p, _ in site if p == 1}
        x['team'] = {str(g): list(t) for g, t in (e.get('team') or {}).items() if int(g) in wins}
        if e.get('golf'):
            x['golf'] = [{str(g): [v[i] for i in pick] for g, v in site.items()} for site in e['golf']]
            x['golf_keys'] = list(GOLF_KEYS)
            for site in e['golf']:
                for g, v in site.items():
                    golf_weeks.append([int(g), e['week'], e['id'], v[GS.IDX['rounds']], v[GS.IDX['putts']],
                                       v[GS.IDX['sg_ott']], v[GS.IDX['sg_app']], v[GS.IDX['sg_arg']],
                                       v[GS.IDX['sg_putt']]])
        evs[e['id']] = json_safe(x)
        (am_weeks if (e.get('tier') or 0) >= 5 else weeks).add(e['week'] - 1)
    rp, rk = d.get('ranking_points') or {}, d.get('rankings') or {}
    world, amateur = {}, {}
    for wk in sorted(weeks):
        rows = rp.get(str(wk))
        if rows:
            world[str(wk)] = {'order': [r[0] for r in rows], 'points': True}
        elif (rk.get('world') or {}).get(str(wk)):
            world[str(wk)] = {'order': list(rk['world'][str(wk)]), 'points': False}
    for wk in sorted(am_weeks):
        if (rk.get('amateur') or {}).get(str(wk)):
            amateur[str(wk)] = {'order': list(rk['amateur'][str(wk)]), 'points': False}
    return {'version': EXTRACT_VERSION, 'events': evs, 'world': world, 'amateur': amateur, 'rounds_of': rounds_of,
            'golf_weeks': golf_weeks}


def json_safe(x):
    return json.loads(json.dumps(x, default=list))


# The pre-event win estimate (roadmap B1/B2, golfsim/upsets.py): an edition's `upset` record, exactly as
# upsets.record writes it -- {'model', 'estimated', 'site', 'field', 'rounds', 'top': [[golfer, chance]],
# 'favourite', 'favourite_p', 'favourite_overall', 'favourite_facts', 'winner', 'p', 'rank', 'overall_rank',
# 'overall', 'winner_facts'} with facts {'status', 'age', 'wr', 'ar'} as at the event; or {'model', 'estimated':
# False, 'why'}. Worked out before the first shot; the story reads it and never works one out afterwards.
UPSET_MODELS = ('upset-model-1',)


def upset_fact(rec, winner, site):
    """(the upset fact, None) from an edition's recorded estimate, or (None, what is missing and why)."""
    if not rec:
        return None, ('a pre-event win estimate (not recorded: played before estimates were kept, and none is worked '
                      'out afterwards), so no upset is claimed')
    if not rec.get('estimated'):
        return None, f'a pre-event win estimate (not estimated: {rec.get("why") or "no reason recorded"})'
    if rec.get('model') not in UPSET_MODELS:
        return None, f'a pre-event win estimate this build can read (model {rec.get("model")})'
    if site != rec.get('site', 0):
        return None, 'a pre-event win estimate for this site (the estimate covers the first site only)'
    if rec.get('winner') is None or rec['winner'] != winner or rec.get('p') is None:
        return None, 'the winner\'s pre-event chance (the estimate names no winner matching the result)'
    return {'model': rec['model'], 'field': rec.get('field'), 'rounds': rec.get('rounds'),
            'winner_p': rec['p'], 'winner_rank': rec.get('rank'), 'overall_rank': rec.get('overall_rank'),
            'overall': rec.get('overall'), 'winner_facts': rec.get('winner_facts') or {},
            'favourite': rec.get('favourite'), 'favourite_p': rec.get('favourite_p'),
            'favourite_overall': rec.get('favourite_overall'), 'favourite_facts': rec.get('favourite_facts') or {},
            'top': [list(x) for x in rec.get('top') or []]}, None


def odds_text(p):
    """A chance as the Biggest Upsets page words it (golfsim.upsets.odds_text): '12.3%', or '1 in 2,350' under 1%."""
    if p is None:
        return 'not recorded'
    if p >= 0.01:
        return f'{100 * p:.1f}%'
    if p <= 0:
        return 'below 1 in 10^300'
    return f'1 in {float(f"{1 / p:.3g}"):,.0f}'


# ---- facts ----------------------------------------------------------------------------------------------------------
def ref(label, href):
    return [label, href]


def _event_href(eid, **q):
    return f'/event/{quote(eid)}' + (f'?{urlencode(q)}' if q else '')


def _results_href(pid, **q):
    return f'/golfer/{pid}?' + urlencode({'tab': 'results', **{k: v for k, v in q.items() if v not in (None, '')}})


def _round_href(eid, k, site=0):
    return _event_href(eid, view='rounds', round=k, site=site)


def standings(scores, k):
    """[(total after k rounds, golfer)], best first, of everyone who played k rounds."""
    rows = [(sum(v[:k]), int(g)) for g, v in scores.items() if len(v) >= k]
    rows.sort()
    return rows


def place_of(rows, gid):
    """(position, tied, total) of a golfer in standings rows."""
    t = next((x for x, g in rows if g == gid), None)
    if t is None:
        return None, False, None
    return 1 + sum(1 for x, _ in rows if x < t), sum(1 for x, _ in rows if x == t) > 1, t


def assemble(src, eid, perspective=None, site=None):
    """The fact record of one edition (see the module notes), or None when the edition is not in the history."""
    e = src.edition(eid)
    if e is None:
        return None
    y, wk = e['year'], e['week']
    sid = e['series']
    finish_all = e.get('finish') or []
    if site is None:
        site = 0
        if perspective is not None:
            site = next((k for k, s in enumerate(finish_all) if any(g == perspective for g, _, _ in s)), 0)
    site = max(0, min(site, max(0, len(finish_all) - 1)))
    finish = [tuple(r) for r in (finish_all[site] if site < len(finish_all) else [])]
    missing = []
    facts = {}
    sites = e.get('sites') or []
    cid, layout = (sites[site][0], sites[site][1]) if site < len(sites) else (None, None)
    course = src.course(cid) if cid else {}
    par = ((course.get('layouts') or {}).get(layout) or {}).get('par')
    if par is None:
        missing.append('the course par (scores are given in strokes only)')
    level = story_level(e)
    facts['event'] = {
        'id': eid, 'name': e.get('name') or src.series(sid).get('name', sid), 'series': sid, 'year': y, 'week': wk,
        'level': level, 'major': is_major(e), 'tier': e.get('tier'), 'category': e.get('category'),
        'tour': e.get('tour'), 'rounds': e.get('rounds'), 'match_play': bool(e.get('match_play')),
        'field': len(finish), 'sites': len(sites), 'site': site, 'course': cid,
        'course_name': course.get('name', cid), 'layout': layout, 'par': par, 'origin': e.get('origin'),
        'src': [ref('final result', _event_href(eid))] + ([ref('course', f'/course/{quote(cid)}')] if cid else [])}
    winner = next((g for g, p, _ in finish if p == 1), None)
    if winner is None:
        missing.append('a winner at this site')
        return _record(eid, site, perspective, facts, missing)
    wtot = next((t for g, p, t in finish if g == winner), None)
    others = [(t, g) for g, p, t in finish if g != winner and p is not None and t is not None]
    second = min(others)[0] if others else None
    runners = sorted(g for t, g in others if t == second)
    rounds_n = e.get('rounds') or 0
    scores_all = e.get('scores') or []
    scores = {str(g): v for g, v in (scores_all[site] if site < len(scores_all) and scores_all[site] else {}).items()}
    played = len(scores.get(str(winner), ())) if scores else rounds_n
    to_par = (wtot - par * played) if (par and wtot is not None and played) else None
    facts['result'] = {'winner': winner, 'total': wtot, 'to_par': to_par, 'second_total': second,
                       'runners_up': runners, 'margin': (second - wtot) if (second is not None and wtot is not None) else None,
                       'src': [ref('final result', _event_href(eid))]}
    # ---- the edition in the tournament's history
    eds = sorted(src.series_editions(sid) or [], key=lambda x: (x['year'], x['week'], x['event']))
    before = [x for x in eds if (x['year'], x['week']) < (y, wk) and x['event'] != eid]
    facts['edition_no'] = {'n': len(before) + 1, 'src': [ref('every edition', f'/series/{quote(sid)}')]}
    if before:
        prev = before[-1]
        d = prev.get('winner')
        if d is not None:
            here = next(((p, t) for s in finish_all for g, p, t in s if g == d), None)
            facts['defending'] = {'champion': d, 'event': prev['event'], 'year': prev['year'],
                                  'played': here is not None, 'pos': here[0] if here else None,
                                  'won': d == winner,
                                  'src': [ref(f'{prev["year"]} edition', _event_href(prev['event'])),
                                          ref('this edition', _event_href(eid))]}
    # ---- rounds
    if e.get('match_play'):
        _match_facts(e, eid, winner, facts, missing)
    elif not scores:
        missing.append('round-by-round scores (this edition was played before round scores were kept; '
                       'only final places and totals are recorded)')
    else:
        _round_facts(eid, site, scores, winner, rounds_n or max(len(v) for v in scores.values()), par, facts)
    # ---- playoff
    po = _playoff(e, site)
    if po is not None:
        if po['holes'] is None:
            missing.append('the playoff holes\' scores (played before they were kept)')
        po['src'] = [ref('playoff', _event_href(eid))]
        facts['playoff'] = po
    # ---- the winner's record before this week
    person = src.person(winner)
    facts['winner'] = _career(src, winner, person, e, y, wk, eid, missing)
    # ---- the ranking published the week before, and the field's strength by it
    amateur = (e.get('tier') or 0) >= 5
    rk = src.ranking(y, wk - 1, amateur=amateur)
    if rk is None:
        missing.append(f'the {"amateur" if amateur else "world"} ranking of the week before')
    else:
        order = rk['order']
        pos = {g: i for i, g in enumerate(order, 1)}
        in_field = {g: (p, t) for s in finish_all for g, p, t in s}
        top = sorted((pos[g], g) for g in in_field if g in pos)
        facts['ranking'] = {
            'kind': 'amateur' if amateur else 'world', 'year': rk['year'], 'week': rk['week'], 'kept': len(order),
            'winner_rank': pos.get(winner), 'top10_in_field': sum(1 for r, _ in top if r <= 10),
            'top50_in_field': sum(1 for r, _ in top if r <= 50),
            'best_in_field': [[r, g, in_field[g][0]] for r, g in top[:3]],
            'src': [ref(f'ranking after {rk["year"]} week {rk["week"]}', rk['href'])]}
    # ---- the pre-event estimate (an upset is claimed only from the edition's recorded one)
    pre, why = upset_fact(e.get('upset'), winner, site)
    if pre is None:
        missing.append(why)
    else:
        fav = pre.get('favourite')
        pre['favourite_pos'] = next((p for g, p, _ in finish if g == fav), None) if fav is not None else None
        pre['favourite_tied'] = (pre['favourite_pos'] is not None
                                 and sum(1 for g, p, _ in finish if p == pre['favourite_pos']) > 1)
        pre['src'] = [ref('pre-event estimate', _event_href(eid)),
                      ref('recorded values', story_href(eid, facts=True) + '#f-upset')]
        facts['upset'] = pre
    # ---- how the winner played: the recorded golf statistics, against the field and the runner-up
    golf = golf_of(e, site)
    if e.get('match_play'):
        pass
    elif golf is None:
        missing.append('golf statistics (played before they were kept; never estimated from scores)')
    else:
        g = _golf_fact(eid, golf, winner, runners, facts['result']['margin'])
        if g is None:
            missing.append('the winner\'s golf statistics')
        else:
            facts['golf'] = g
            if not g.get('vs_runner_up') and len(runners) == 1 and facts['result']['margin']:
                missing.append('a strokes-gained comparison with the runner-up (their statistics are not comparable)')
            gh = _golf_history(src, winner, person, y, wk, eid, g, missing)
            if gh is not None:
                facts['golf_history'] = gh
    # ---- comparisons with the tournament's earlier editions
    hist = _series_results(src, sid, (y, wk))
    if hist is None:
        missing.append('comparisons with earlier editions (the history index is not available)')
    else:
        facts_h = _history(src, hist, eid, y, wk, sid, to_par, facts['result']['margin'], played)
        if facts_h is not None:
            facts['history'] = facts_h
            if facts_h['unknown_format']:
                missing.append(f'comparisons with {facts_h["unknown_format"]} earlier edition(s) whose format is still '
                               'being indexed')
    # ---- moments recorded during the event
    ms = []
    for m in src.moments(eid) or ():
        k = m.get('kind')
        if k not in ('course record', 'hole-in-one', 'albatross'):
            continue
        lay = m.get('layout') or ''
        c = lay.split(':')[0] if lay else cid
        item = {'kind': k, 'person': m.get('person'), 'round': _round_no(m), 'hole': m.get('hole'),
                'score': m.get('score'), 'to_par': m.get('to_par'), 'previous': m.get('previous'),
                'previous_holder': m.get('previous_holder'),
                'src': [ref('course records', f'/course/{quote(c)}')] if c else []}
        if item['round'] and not e.get('match_play'):
            item['src'].append(ref(f'round {item["round"]}', _round_href(eid, item['round'], site)))
        ms.append(item)
    if ms:
        facts['moments'] = ms
    # ---- the team that week
    team = e.get('team') or {}
    t = team.get(winner) or team.get(str(winner))
    if t and (t[0] or t[1]):
        facts['team'] = {'coach': t[0] or None, 'caddie': t[1] or None,
                         'src': [ref('the team that week', _event_href(eid))]}
    # ---- a golfer's own view
    if perspective is not None and perspective != winner:
        facts['perspective'] = _perspective(src, perspective, e, site, finish, scores, winner, par, y, wk, eid)
        mine = (golf or {}).get(perspective)
        if mine and mine.get('rounds'):
            facts['perspective']['golf'] = {'rounds': mine['rounds'], 'putts': mine['putts'],
                                            'sg': {k: mine[k] / 100 for k, _ in SG_PARTS},
                                            'sg_total': round(sum(mine[k] for k, _ in SG_PARTS) / 100, 2)}
    return _record(eid, site, perspective if perspective != winner else None, facts, missing)


def _record(eid, site, perspective, facts, missing):
    rec = {'version': FACT_VERSION, 'event': eid, 'site': site, 'perspective': perspective, 'facts': facts,
           'missing': missing}
    rec['digest'] = digest(rec)
    return rec


def digest(rec):
    body = {k: v for k, v in rec.items() if k != 'digest'}
    return hashlib.sha1(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _round_no(m):
    if isinstance(m.get('round'), int):
        return m['round']
    st = str(m.get('stage') or '')
    if st.startswith('round '):
        try:
            return int(st.split()[1])
        except (IndexError, ValueError):
            return None
    return None


def _round_facts(eid, site, scores, winner, n, par, facts):
    leaders, path, low, gap = [], [], [], []
    for k in range(1, n + 1):
        rows = standings(scores, k)
        if not rows:
            break
        best = rows[0][0]
        lead = sorted(g for t, g in rows if t == best)
        leaders.append({'golfers': lead, 'total': best, 'to_par': best - par * k if par else None})
        pos, tied, tot = place_of(rows, winner)
        rs = scores.get(str(winner), [])
        path.append({'pos': pos, 'tied': tied, 'total': tot, 'behind': (tot - best) if tot is not None else None,
                     'score': rs[k - 1] if len(rs) >= k else None})
        day = [(v[k - 1], int(g)) for g, v in scores.items() if len(v) >= k]
        lo = min(s for s, _ in day)
        low.append({'score': lo, 'golfers': sorted(g for s, g in day if s == lo), 'to_par': lo - par if par else None})
        nxt = [t for t, g in rows if g != winner]
        gap.append((nxt[0] - tot) if (pos == 1 and nxt and tot is not None) else None)
    k_n = len(leaders)
    took = None
    for k in range(k_n, 0, -1):                       # the round after which the winner led (alone or shared) for good
        if path[k - 1]['pos'] == 1:
            took = k
        else:
            break
    behind = [(p['behind'], k) for k, p in enumerate(path, 1) if p['behind'] is not None and k < k_n]
    max_behind = max(behind, key=lambda x: (x[0], -x[1])) if behind else (0, None)
    moves = []
    for k in range(2, k_n + 1):
        a, b = path[k - 2]['pos'], path[k - 1]['pos']
        if a is not None and b is not None and a - b > 0:
            moves.append((a - b, k, a, b))
    best_move = max(moves, key=lambda x: (x[0], -x[1])) if moves else None
    final_leaders = []
    if k_n >= 2:
        for g in leaders[k_n - 2]['golfers']:         # who led entering the final round, if not the winner
            if g == winner:
                continue
            rs = scores.get(str(g), [])
            fin_rows = standings(scores, k_n)
            pos, tied, _ = place_of(fin_rows, g)
            final_leaders.append({'golfer': g, 'final_round': rs[k_n - 1] if len(rs) >= k_n else None,
                                  'pos': pos, 'tied': tied})
    facts['rounds'] = {
        'n': k_n, 'par': par, 'leaders': leaders, 'winner_path': path, 'low': low, 'gap': gap, 'took_lead': took,
        'led_every_round': all(p['pos'] == 1 for p in path),
        'max_behind': {'strokes': max_behind[0], 'round': max_behind[1]},
        'behind_entering_final': path[k_n - 2]['behind'] if k_n >= 2 else None,
        'best_move': ({'gain': best_move[0], 'round': best_move[1], 'from': best_move[2], 'to': best_move[3],
                       'score': path[best_move[1] - 1]['score']} if best_move else None),
        'leaders_entering_final': final_leaders,
        'src': [ref(f'after round {k}', _round_href(eid, k, site)) for k in range(1, k_n + 1)]}


def _match_facts(e, eid, winner, facts, missing):
    ms = [m for m in (e.get('matches') or []) if m and winner in (m[1], m[2])]
    if not ms:
        missing.append('the matches (not recorded for this edition)')
        return
    facts['matches'] = {'path': [{'stage': m[0], 'won': m[1] == winner, 'opponent': m[2] if m[1] == winner else m[1],
                                  'result': m[3] if len(m) > 3 else None} for m in ms],
                        'src': [ref('final result', _event_href(eid))]}


def _playoff(e, site):
    rec = e.get('playoffs')
    if rec is not None and site < len(rec):
        p = rec[site]
        if p is None:
            return None
        return {'players': list(p['players']), 'winner': p['winner'], 'length': len(p['holes']),
                'holes': [[n, h, {str(g): v for g, v in sc.items()}] for n, h, sc in p['holes']]}
    if not e.get('playoff') or site >= len(e.get('finish') or []):
        return None
    fin = e['finish'][site]
    if not fin or fin[0][2] is None:
        return None
    players = [g for g, p, t in fin if t == fin[0][2] and p in (1, 2)]
    if len(players) < 2:
        return None
    return {'players': players, 'winner': fin[0][0], 'holes': None,
            'length': e['playoff'] if len(e['finish']) == 1 else None}


def _career(src, gid, person, e, y, wk, eid, missing):
    """The winner's record strictly before this week (as it stood then)."""
    rows = [r for r in (src.starts(gid) or []) if (r['year'], r['week']) < (y, wk) and r['event'] != eid
            and r.get('category') not in QUALIFYING]
    amateur_scope = (e.get('tier') or 0) >= 5
    in_scope = (lambda r: (r.get('tier') or 0) >= 5) if amateur_scope else (lambda r: r.get('tier') is not None
                                                                          and r['tier'] <= 4)
    wins = [r for r in rows if r['pos'] == 1 and in_scope(r)]
    majors = [r for r in rows if is_major(r)]
    major_wins = [r for r in majors if r['pos'] == 1]
    best_major = min((r['pos'] for r in majors if r['pos'] is not None), default=None)
    series_wins = [r for r in rows if r['series'] == e['series'] and r['pos'] == 1]
    slam = None
    if is_major(e) and e['series'] in MAJOR_SERIES:
        had = {r['series'] for r in major_wins if r['series'] in MAJOR_SERIES}
        if e['series'] not in had and len(had) == len(MAJOR_SERIES) - 1:
            slam = True
    initial = bool(person.get('initial'))
    first_year = src.first_year()
    if initial:
        missing.append(f'results before the world began in {first_year} (counts are of the retained history)')
    born = person.get('born')
    return {'golfer': gid, 'name': person.get('name'), 'initial': initial, 'first_year': first_year,
            'scope': 'amateur' if amateur_scope else 'professional', 'wins_before': len(wins),
            'starts_before': len(rows), 'majors_before': len(major_wins), 'major_starts_before': len(majors),
            'best_major_before': best_major, 'series_wins_before': len(series_wins),
            'last_win': wins[-1]['event'] if wins else None, 'slam': bool(slam),
            'age': (y - born) if born else None,
            'src': [ref('results', _results_href(gid)), ref('wins', _results_href(gid, outcome='win'))]}


def _series_results(src, sid, before):
    try:
        return src.series_results(sid, before=before)
    except TypeError:                                    # (a source without the date bound)
        return src.series_results(sid)


def _history(src, hist, eid, y, wk, sid, to_par, margin, rounds_n):
    """The tournament's earlier editions of the same format (the same number of rounds, each edition's own; each
    winning total against its own venue's par for that many rounds): is this the lowest winning score to par,
    the widest margin? Editions of another format are left out; while some formats are still being indexed, no
    'lowest' or 'widest' claim is made."""
    prior = [h for h in hist if (h['year'], h['week']) < (y, wk) and h['event'] != eid]
    if not prior:
        return None
    known = [h for h in prior if h.get('rounds')]
    same = [h for h in known if h['rounds'] == rounds_n]
    tp, mg = [], []
    for h in same:
        c = src.course(h.get('course')) if h.get('course') else {}
        p = ((c.get('layouts') or {}).get(h.get('layout')) or {}).get('par')
        if h.get('winner_total') is not None and p:
            tp.append(h['winner_total'] - p * h['rounds'])
        if h.get('winner_total') is not None and h.get('second_total') is not None:
            mg.append(h['second_total'] - h['winner_total'])
    complete = len(known) == len(prior)
    out = {'prior': len(prior), 'rounds': rounds_n, 'same_format': len(same), 'other_format': len(known) - len(same),
           'unknown_format': len(prior) - len(known), 'compared_to_par': len(tp), 'compared_margin': len(mg),
           'lowest_to_par_before': min(tp) if tp else None, 'largest_margin_before': max(mg) if mg else None,
           'src': [ref('every edition', f'/series/{quote(sid)}')]}
    out['lowest_to_par'] = bool(complete and to_par is not None and tp and len(tp) == len(same) and to_par < min(tp))
    out['largest_margin'] = bool(complete and margin is not None and mg and len(mg) == len(same) and margin > max(mg))
    return out


def golf_of(e, site):
    """{golfer: counters} of an edition's site from its recorded golf statistics (the season file's FIELDS order,
    or the story index's GOLF_KEYS), or None where none were recorded."""
    g = e.get('golf')
    if not g or site >= len(g) or not g[site]:
        return None
    keys = e.get('golf_keys') or GS.FIELDS
    return {int(pid): dict(zip(keys, v)) for pid, v in g[site].items()}


def _golf_fact(eid, golf, winner, runners, margin):
    """The winner's recorded statistics, their place in the field among golfers who played the same number of
    rounds, and the margin over a single runner-up split by strokes gained (engine table)."""
    me = golf.get(winner)
    if not me or not me.get('rounds'):
        return None
    n = me['rounds']
    comp = [c for c in golf.values() if c.get('rounds') == n]

    def rank(key, lower=False):
        v = me[key]
        better = sum(1 for c in comp if (c[key] < v if lower else c[key] > v))
        return [1 + better, sum(1 for c in comp if c[key] == v) > 1]
    sg = {k: me[k] / 100 for k, _ in SG_PARTS}
    out = {'golfer': winner, 'rounds': n, 'holes': me['holes'], 'putts': me['putts'], 'fairways': me['fairways'],
           'fairway_att': me['fairway_att'], 'drives': me['drives'],
           'distance': round(me['drive_tenths'] / me['drives'] / 10, 1) if me['drives'] else None,
           'gir': me['gir'], 'scr_made': me['scr_made'], 'scr_att': me['scr_att'], 'sand_saves': me['sand_saves'],
           'sand_att': me['sand_att'], 'penalties': me.get('penalties'), 'sg': sg,
           'sg_total': round(sum(me[k] for k, _ in SG_PARTS) / 100, 2), 'comparable': len(comp),
           'ranks': {'putts': rank('putts', True), 'gir': rank('gir'), **{k: rank(k) for k, _ in SG_PARTS}},
           'src': [ref('statistics', _event_href(eid, view='stats')), ref('definitions', '/rules#golf-statistics')]}
    if len(runners) == 1 and margin:
        r = golf.get(runners[0])
        if r and r.get('rounds') == n:
            parts = {k: round((me[k] - r[k]) / 100, 2) for k, _ in SG_PARTS}
            total = round(sum(me[k] - r[k] for k, _ in SG_PARTS) / 100, 2)
            out['vs_runner_up'] = {'golfer': runners[0], 'margin': margin, 'parts': parts, 'sum': total,
                                   'unaccounted': round(margin - total, 2)}
    return out


def _golf_history(src, pid, person, y, wk, eid, this, missing):
    """The golfer's earlier golf weeks of the same number of rounds at story editions, strictly before this one:
    their lowest putt total and best strokes-gained putting and total weeks to that date, with the events."""
    fn = getattr(src, 'golf_history', None)
    rows, pending = fn(pid, y, wk, eid) if fn else (None, 0)
    if rows is None:
        missing.append('comparisons with their earlier weeks (no story index for this history)')
        return None
    if pending:
        missing.append(f'comparisons with their earlier weeks ({pending} season(s) still being indexed)')
        return None
    n = this['rounds']
    same = [r for r in rows if r['rounds'] == n and (r['year'], r['week']) < (y, wk) and r['event'] != eid]
    tot = lambda r: sum(r[k] for k, _ in SG_PARTS)
    out = {'golfer': pid, 'rounds': n, 'comparable': len(same), 'initial': bool(person.get('initial')),
           'scope': GOLF_SCOPE, 'src': [ref('results', _results_href(pid))]}
    if not same:
        return out
    label = lambda r: f'{r["year"]} {src.series(r["event"].split(":", 1)[1]).get("name") or r["event"].split(":", 1)[1]}'
    lp = min(same, key=lambda r: (r['putts'], r['year'], r['week'], r['event']))
    bp = max(same, key=lambda r: (r['sg_putt'], -r['year'], -r['week']))
    bt = max(same, key=lambda r: (tot(r), -r['year'], -r['week']))
    week = lambda r, v: {'event': r['event'], 'label': label(r), 'year': r['year'], 'value': v,
                         'href': _event_href(r['event'], view='stats')}
    out.update({'lowest_putts_before': week(lp, lp['putts']), 'best_sg_putt_before': week(bp, bp['sg_putt'] / 100),
                'best_sg_total_before': week(bt, round(tot(bt) / 100, 2)),
                'lowest_putts': this['putts'] < lp['putts'], 'equalled_putts': this['putts'] == lp['putts'],
                'best_sg_putt': round(this['sg']['sg_putt'], 2) > bp['sg_putt'] / 100,
                'best_sg_total': this['sg_total'] > round(tot(bt) / 100, 2)})
    for k in ('lowest_putts_before', 'best_sg_putt_before', 'best_sg_total_before'):
        r_ = ref(out[k]['label'], out[k]['href'])
        if r_ not in out['src']:
            out['src'].append(r_)
    return out


def _perspective(src, pid, e, site, finish, scores, winner, par, y, wk, eid):
    me = next(((p, t) for g, p, t in finish if g == pid), None)
    person = src.person(pid)
    wtot = next((t for g, p, t in finish if g == winner), None)
    out = {'golfer': pid, 'name': person.get('name'), 'played': me is not None, 'pos': me[0] if me else None,
           'total': me[1] if me else None, 'tied': bool(me and me[0] is not None
                                                      and sum(1 for g, p, t in finish if p == me[0]) > 1),
           'behind': (me[1] - wtot) if (me and me[1] is not None and wtot is not None) else None,
           'initial': bool(person.get('initial')),
           'src': [ref('final result', _event_href(eid)), ref('results', _results_href(pid))]}
    if scores and str(pid) in scores:
        rs = scores[str(pid)]
        path = []
        for k in range(1, len(rs) + 1):
            pos, tied, _ = place_of(standings(scores, k), pid)
            path.append({'pos': pos, 'tied': tied, 'score': rs[k - 1]})
        best = min(range(len(rs)), key=lambda i: (rs[i], i))
        out['path'] = path
        out['best_round'] = {'round': best + 1, 'score': rs[best], 'to_par': rs[best] - par if par else None,
                             'day_low': rs[best] == min(v[best] for v in scores.values() if len(v) > best),
                             'href': _round_href(eid, best + 1, site)}
        out['rounds_src'] = [ref(f'after round {k}', _round_href(eid, k, site)) for k in range(1, len(rs) + 1)]
    rows = [r for r in (src.starts(pid) or []) if (r['year'], r['week']) < (y, wk) and r['event'] != eid]
    if is_major(e):
        prev = [r['pos'] for r in rows if is_major(r) and r['pos'] is not None]
        out['best_major_before'] = min(prev) if prev else None
        out['major_starts_before'] = sum(1 for r in rows if is_major(r))
    return out


# ---- patterns -------------------------------------------------------------------------------------------------------
def patterns(rec):
    """(primary, [every pattern that applies]) from a fact record."""
    f = rec['facts']
    res = f.get('result')
    if res is None:
        return 'standard', []
    tags = []
    if f.get('event', {}).get('match_play'):
        tags.append('match_play')
    if f.get('playoff'):
        tags.append('playoff')
    up = f.get('upset')
    if up and up.get('winner_p') is not None and up['winner_p'] < UPSET_P:
        tags.append('upset')
    r = f.get('rounds')
    if r:
        bef = r.get('behind_entering_final')
        mb = r.get('max_behind') or {}
        if (bef is not None and bef >= COMEBACK_FINAL) or (mb.get('strokes') or 0) >= COMEBACK_ANY:
            tags.append('comeback')
    m = res.get('margin')
    if m is not None and m >= RUNAWAY:
        tags.append('runaway')
    if r and r.get('led_every_round') and r.get('n', 0) >= 2 and not any(
            p['tied'] for p in r['winner_path'][:-1]):    # alone in front after each round (a playoff ties the last)
        tags.append('wire_to_wire')
    w = f.get('winner') or {}
    if w.get('wins_before') == 0:
        tags.append('first_win')
    if m == CLOSE and 'playoff' not in tags:
        tags.append('close_finish')
    order = ('match_play', 'playoff', 'upset', 'comeback', 'runaway', 'first_win', 'wire_to_wire', 'close_finish')
    primary = next((p for p in order if p in tags), 'standard')
    return primary, tags


# ---- words ----------------------------------------------------------------------------------------------------------
WORDS = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten')
ORDW = ('', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth')


def num(n):
    return WORDS[n] if 0 <= n < len(WORDS) else f'{n:,}'


def ordinal(n):
    if n is None:
        return '—'
    suf = 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f'{n}{suf}'


def ord_word(n):
    return ORDW[n] if 0 < n < len(ORDW) else ordinal(n)


def art(n):
    """'a 64', 'an 80', 'an 18'."""
    t = str(n)
    return ('an ' if t.startswith('8') or t in ('11', '18') else 'a ') + t


def strokes(n):
    return f'{num(n)} stroke{"s" if n != 1 else ""}'


def to_par_text(tp):
    if tp is None:
        return None
    return 'level par' if tp == 0 else f'{abs(tp)} {"under" if tp < 0 else "over"} par'


def place_text(pos, tied):
    if pos is None:
        return 'outside the places'
    if pos == 1:
        return 'tied for the lead' if tied else 'in the lead'
    return f'tied for {ordinal(pos)}' if tied else ordinal(pos)


def finish_text(pos, tied=False):
    if pos is None:
        return 'missed the cut'
    return f'finished {"tied " if tied else ""}{ordinal(pos)}'


def round_name(k, n):
    return 'the final round' if k == n and n > 1 else f'the {ord_word(k)} round'


def pick(key, slot, options):
    """One of `options`, chosen by the edition and the slot (never at random): the same story every time it is
    opened, different editions phrased differently."""
    h = int(hashlib.sha1(f'{key}|{slot}'.encode()).hexdigest(), 16)
    return options[h % len(options)]


# ---- sentences --------------------------------------------------------------------------------------------------------
class Sentence:
    """Parts (text, or [label, href] links) and the fact keys whose sources support it."""

    def __init__(self, parts, facts, src=()):
        self.parts = parts
        self.facts = list(facts)
        self.src = [list(s) for s in src]

    def text(self):
        return ''.join(p if isinstance(p, str) else p[0] for p in self.parts)

    def to_dict(self):
        return {'parts': self.parts, 'facts': self.facts, 'src': self.src}


def _expand(v):
    """A slot's parts: text, one link [label, href], or a list of parts (several names)."""
    if isinstance(v, (list, tuple)) and v and not isinstance(v[0], str):
        return [x if isinstance(x, str) else list(x) for x in v]
    if isinstance(v, (list, tuple)):
        return [list(v)]
    return [str(v)]


def fill(template, **slots):
    """Parts from a template with {slot}s; a slot is text or a [label, href] link."""
    import re
    parts = []
    pos = 0
    for m in re.finditer(r'\{(\w+)\}', template):
        if m.start() > pos:
            parts.append(template[pos:m.start()])
        parts += _expand(slots[m.group(1)])
        pos = m.end()
    if pos < len(template):
        parts.append(template[pos:])
    out = []
    for p in parts:                                       # merge neighbouring text
        if isinstance(p, str) and out and isinstance(out[-1], str):
            out[-1] += p
        else:
            out.append(p)
    if out and isinstance(out[0], str):
        out[0] = out[0][:1].upper() + out[0][1:]
    return out


class Writer:
    def __init__(self, rec, names):
        self.rec = rec
        self.f = rec['facts']
        self.names = names
        self.key = f'{rec["event"]}|{rec.get("perspective")}|{rec.get("site")}'
        self.out = []

    def who(self, pid):
        return [self.names(pid), f'/golfer/{pid}']

    def whos(self, pids):
        names = [self.who(g) for g in pids]
        if len(names) <= 1:
            return names
        out = []
        for i, n in enumerate(names):
            if i:
                out.append(' and ' if i == len(names) - 1 else ', ')
            out.append(n)
        return out

    # facts whose sentences link the round they speak of inline (their every-round sources would be noise)
    INLINE = ('rounds',)

    def _src(self, facts, extra_src):
        src = []
        for k in facts:
            if k in self.INLINE:
                continue
            v = self.f.get(k)
            for it in (v if isinstance(v, list) else [v]):
                for s in (it or {}).get('src', ()):
                    if s not in src:
                        src.append(s)
        for s in extra_src:
            if list(s) not in src:
                src.append(list(s))
        return src

    def say(self, template, facts, extra_src=(), **slots):
        self.out.append(Sentence(fill(template, **slots), facts, self._src(facts, extra_src)))

    def say_parts(self, parts, facts, extra_src=()):
        if parts and isinstance(parts[0], str):
            parts[0] = parts[0][:1].upper() + parts[0][1:]
        self.out.append(Sentence(parts, facts, self._src(facts, extra_src)))

    def pick(self, slot, options):
        return pick(self.key, slot, options)

    # -- shared slots
    def event_link(self):
        ev = self.f['event']
        return [f'{ev["year"]} {ev["name"]}', _event_href(ev['id'])]

    def total(self):
        r = self.f['result']
        tp = to_par_text(r.get('to_par'))
        if r.get('total') is None:
            return 'the recorded total'
        return f'{r["total"]} ({tp})' if tp else f'{r["total"]}'

    def round_link(self, k, label=None):
        r = self.f['rounds']
        return [label or f'after {round_name(k, r["n"])}', r['src'][k - 1][1]]


def narrate(rec, names):
    """The story of a fact record: {'primary', 'patterns', 'sentences': [Sentence], 'missing'} (names(pid) ->
    the golfer's name as shown)."""
    primary, tags = patterns(rec)
    w = Writer(rec, names)
    if 'result' not in rec['facts']:
        w.say('No winner is recorded for this site, so there is no story to tell.', ['event'])
        return {'primary': primary, 'patterns': tags, 'sentences': w.out, 'missing': rec['missing']}
    secs = list(STRUCTURES[primary])
    if 'comeback' in tags and 'comeback' not in secs and 'rounds' in secs:   # a comeback inside an upset or playoff
        secs.insert(secs.index('rounds') + 1, 'comeback')
    if 'upset' in tags and 'upset' not in secs:          # an upset inside a playoff: its chance right after the lead
        secs.insert(1, 'upset')
    for section in secs:
        SECTIONS[section](w, primary, tags)
    return {'primary': primary, 'patterns': tags, 'sentences': w.out, 'missing': rec['missing'],
            'fact_digest': rec['digest'], 'version': NARRATIVE_VERSION}


# each section adds sentences only when its facts say something
def _lead(w, primary, tags):
    f = w.f
    res, ev = f['result'], f['event']
    persp = f.get('perspective')
    W, E, T = w.who(res['winner']), w.event_link(), w.total()
    if persp:
        P = w.who(persp['golfer'])
        if persp['played']:
            w.say(w.pick('plead', ['{P} {F} at the {E}, which {W} won at {T}.',
                                   'At the {E}, won by {W} at {T}, {P} {F}.']),
                  ['perspective', 'result'], P=P, F=finish_text(persp['pos'], persp['tied']), E=E, W=W, T=T)
        else:
            w.say('{P} was not in the field at this site of the {E}, won by {W} at {T}.', ['perspective', 'result'],
                  P=P, E=E, W=W, T=T)
    runners = res['runners_up']
    margin = res.get('margin')
    if primary == 'playoff':
        po = f['playoff']
        losers = [g for g in po['players'] if g != po['winner']]
        n = len(po['players'])
        tpl = w.pick('lead', ['{W} won the {E} in a playoff, beating {L} after {N} players finished level at {T}.',
                              'It took extra holes to settle the {E}: {N} players tied at {T}, and {W} beat {L} in the playoff.',
                              '{W} came through a playoff against {L} to win the {E}, after regulation ended with {N} '
                              'players tied at {T}.'])
        parts = fill(tpl.replace('{L}', '\x00'), W=W, E=E, N=num(n), T=T)
        _splice(parts, w.whos(losers))
        w.say_parts(parts, ['result', 'playoff'])
        return
    if primary == 'match_play':
        m = f.get('matches')
        final = m['path'][-1] if m else None
        if final and final['won']:
            w.say(w.pick('lead', ['{W} won the {E}, beating {O} in the {S}{R}.',
                                  'The {E} went to {W}, who beat {O} in the {S}{R}.']),
                  ['result', 'matches'], W=W, E=E, O=w.who(final['opponent']), S=final['stage'],
                  R=f' ({final["result"]})' if final.get('result') else '')
        else:
            w.say('{W} won the {E}.', ['result'], W=W, E=E)
        return
    M = strokes(margin) if margin else 'a share of first'
    if primary == 'upset':
        up = f['upset']
        if up.get('winner_rank') and up.get('field'):
            tpl = w.pick('lead', ['{W} won the {E} at {T} with a pre-event chance of {P}, {R} of {N} in the field.',
                                  'Rated {R} of {N} before the {E}, at {P} to win, {W} won it at {T}.',
                                  '{W} won the {E} at {T}, an outcome the pre-event estimate put at {P} ({R} of {N}).'])
            w.say(tpl, ['result', 'upset'], W=W, E=E, T=T, P=odds_text(up['winner_p']),
                  R=ordinal(up['winner_rank']), N=f'{up["field"]:,}')
        else:
            w.say(w.pick('lead', ['{W} won the {E} at {T} with a pre-event chance of {P}.',
                                  'Given {P} to win before it started, {W} won the {E} at {T}.']),
                  ['result', 'upset'], W=W, E=E, T=T, P=odds_text(up['winner_p']))
        return
    if primary == 'comeback':
        r = f['rounds']
        bef = r.get('behind_entering_final') or 0
        mb = r['max_behind']
        k, d = (r['n'] - 1, bef) if bef >= COMEBACK_FINAL and bef >= mb['strokes'] else (mb['round'], mb['strokes'])
        tpl = w.pick('lead', ['{W} came from {D} back {A} to win the {E} at {T}.',
                              'Trailing by {D} {A}, {W} won the {E} at {T}.',
                              '{W} won the {E} at {T}, having been {D} behind the lead {A}.'])
        w.say(tpl, ['result', 'rounds'], W=W, E=E, T=T, D=strokes(d), A=w.round_link(k))
        return
    if primary == 'runaway':
        tpl = w.pick('lead', ['{W} won the {E} by {M} at {T}.',
                              'The {E} was won by {M}: {W} finished at {T}.',
                              '{W} ran away with the {E}, finishing {M} clear at {T}.'])
        w.say(tpl, ['result'], W=W, E=E, T=T, M=strokes(margin) if margin else M)
        return
    if primary == 'wire_to_wire':
        n = f['rounds']['n']
        tpl = w.pick('lead', ['{W} led after every round and won the {E} at {T}.',
                              '{W} won the {E} wire to wire, at the top of the leaderboard after each of the {N} rounds, '
                              'finishing at {T}.',
                              'From the first round to the last, {W} held at least a share of the lead at the {E}, '
                              'winning at {T}.'])
        w.say(tpl, ['result', 'rounds'], W=W, E=E, T=T, N=num(n))
        return
    if primary == 'first_win':
        c = f['winner']
        S = 'on the professional tours' if c['scope'] == 'professional' else 'in amateur and college golf'
        Q = ' in the retained history' if c['initial'] else ''
        tpl = w.pick('lead', ['{W} won {S} for the first time{Q} at the {E}, finishing at {T}.',
                              'The {E} brought {W}\'s first win {S}{Q}, at {T}.'])
        w.say(tpl, ['result', 'winner'], W=W, E=E, T=T, S=S, Q=Q)
        return
    if primary == 'close_finish':
        tpl = w.pick('lead', ['{W} won the {E} by a single stroke at {T}, ahead of {L}.',
                              'One stroke separated {W} from {L} at the {E}; {W2} won at {T}.',
                              'The {E} went to {W} by one stroke, at {T}, with {L} next.'])
        parts = fill(tpl.replace('{L}', '\x00'), W=W, E=E, T=T, W2=w.names(res['winner']))
        _splice(parts, w.whos(runners[:3]))
        w.say_parts(parts, ['result'])
        return
    tpl = w.pick('lead', ['{W} won the {E} at {T}, {M} ahead of {L}.',
                          'The {E} went to {W} at {T}, {M} clear of {L}.',
                          '{W} finished {M} ahead of {L} to win the {E} at {T}.'])
    parts = fill(tpl.replace('{L}', '\x00'), W=W, E=E, T=T, M=M)
    _splice(parts, w.whos(runners[:3]) if runners else ['the rest of the field'])
    w.say_parts(parts, ['result'])


def _splice(parts, insert):
    """Replace the \\x00 marker in parts with the given parts (a list of names)."""
    for i, p in enumerate(parts):
        if isinstance(p, str) and '\x00' in p:
            a, b = p.split('\x00', 1)
            new = ([a] if a else []) + [x if isinstance(x, (list, str)) else list(x) for x in insert] + ([b] if b else [])
            parts[i:i + 1] = new
            return


def _stakes(w, primary, tags):
    f = w.f
    ev = f['event']
    bits = []
    no = f.get('edition_no', {}).get('n')
    kind = ('one of the four majors' if ev['major'] else 'a Premier Tour event' if ev['tier'] == 1
            else 'its circuit\'s flagship championship' if ev['category'] in ('flagship', 'circuit_championship')
            else 'a national championship' if ev['category'] in ('national_open', 'national_amateur')
            else None)
    if no and kind:
        C = [ev['course_name'] or ev['course'], f'/course/{quote(ev["course"])}'] if ev.get('course') else 'its venue'
        w.say(w.pick('stakes', ['The {E2} is {K}; this was the {N} edition played in this world, at {C}.',
                                'This was the {N} {E2} in the world\'s history, {K}, played at {C}.']),
              ['event', 'edition_no'], E2=ev['name'], K=kind, N=ordinal(no), C=C)
    d = f.get('defending')
    if d and primary != 'match_play':
        D = w.who(d['champion'])
        if d['won']:
            w.say(w.pick('def', ['{D} was the defending champion and kept the title.',
                                 'It was a successful defence: {D} had also won the {Y} edition.']),
                  ['defending'], D=D, Y=d['year'])
        elif d['played']:
            w.say(w.pick('def', ['The defending champion, {D}, {F}.', '{D}, champion in {Y}, {F} this time.']),
                  ['defending'], D=D, Y=d['year'], F=finish_text(d['pos']))
    up = f.get('upset')
    if up and primary != 'upset' and up.get('favourite') == f['result']['winner']:
        w.say('{W} went in as the favourite, at {P} by the pre-event estimate.', ['upset'],
              W=w.who(f['result']['winner']), P=odds_text(up['winner_p']))
    rk = f.get('ranking')
    if rk and (ev['major'] or ev['tier'] == 1):
        R = [f'the {rk["kind"]} ranking of the week before', rk['src'][0][1]]
        if rk['top10_in_field']:
            best = rk['best_in_field'][0] if rk['best_in_field'] else None
            if best and best[1] != f['result']['winner']:
                w.say(w.pick('field', ['{N} of the top 10 in {R} were in the field; the highest ranked, No. {B} {G}, {F}.',
                                       'The field held {N} of the top 10 in {R}. No. {B} {G} {F}.']),
                      ['ranking'], N=num(rk['top10_in_field']), R=R, B=best[0], G=w.who(best[1]),
                      F=finish_text(best[2]))
            else:
                w.say('{N} of the top 10 in {R} were in the field.', ['ranking'], N=num(rk['top10_in_field']), R=R)
        wr = rk.get('winner_rank')
        if wr is not None:
            w.say(w.pick('wrank', ['{W} went in at No. {K} in {R}.', '{W} was No. {K} in {R}.']), ['ranking'],
                  W=w.who(f['result']['winner']), K=wr, R=R)
        else:
            w.say('{W} was outside the recorded top {N} of {R}.', ['ranking'], W=w.who(f['result']['winner']),
                  N=rk['kept'], R=R)


def _upset(w, primary, tags):
    up = w.f.get('upset')
    if not up:
        return
    win = w.f['result']['winner']
    W = w.who(win)
    if primary != 'upset':                               # the lead told another shape: the chance comes first here
        if up.get('winner_rank') and up.get('field'):
            w.say(w.pick('uchance', ['{W} had gone in with a pre-event chance of {P}, {R} of {N} in the field.',
                                     'Before the first shot, the estimate gave {W} {P} to win, {R} of {N}.']),
                  ['upset'], W=W, P=odds_text(up['winner_p']), R=ordinal(up['winner_rank']), N=f'{up["field"]:,}')
        else:
            w.say('{W} had gone in with a pre-event chance of {P}.', ['upset'], W=W, P=odds_text(up['winner_p']))
    if up.get('overall') is not None and up.get('overall_rank') and up.get('field'):
        w.say(w.pick('uov', ['By Overall at the event, {W} ({O}) was {R} of {N}.',
                             '{W}\'s Overall at the event was {O}, {R} of {N} in the field.']),
              ['upset'], W=W, O=up['overall'], R=ordinal(up['overall_rank']), N=f'{up["field"]:,}')
    fav = up.get('favourite')
    if fav is not None and fav != win and up.get('favourite_p') is not None:
        fo = up.get('favourite_overall')
        w.say(w.pick('ufav', ['The favourite was {F} at {P}{O}, who {H}.',
                              '{F}, the favourite at {P}{O}, {H}.']),
              ['upset'], F=w.who(fav), P=odds_text(up['favourite_p']), O=f' (Overall {fo})' if fo is not None else '',
              H=finish_text(up['favourite_pos'], up.get('favourite_tied')))
    wf = up.get('winner_facts') or {}
    if 'ranking' not in w.f and wf.get('wr'):              # the ranking recorded with the estimate
        w.say('{W} went in at world No. {K}.', ['upset'], W=W, K=wf['wr'])
    if wf.get('status') == 'amateur':
        w.say('{W} played as an amateur.', ['upset'], W=W)
    w.say('The estimate ({M}) was worked out from the field before the first shot; the result plays no part in it.',
          ['upset'], M=str(up['model']))


def _comeback(w, primary, tags):
    r = w.f.get('rounds')
    if not r:
        return
    n = r['n']
    lead = r['leaders_entering_final']
    path = r['winner_path']
    if n >= 2 and lead:
        g = lead[0]
        k = n - 1
        w.say(w.pick('cb', ['{G} led {A} at {L}; {W} was {P}, {D} back.',
                            '{G} held the lead {A} at {L}, with {W} {P} and {D} behind.']),
              ['rounds'], G=w.who(g['golfer']), A=w.round_link(k), L=_score_txt(r['leaders'][k - 1]),
              W=w.who(w.f['result']['winner']), P=place_text(path[k - 1]['pos'], path[k - 1]['tied']),
              D=strokes(path[k - 1]['behind']))
        last = path[n - 1]['score']
        if last is not None and g.get('final_round') is not None:
            w.say(w.pick('cb2', ['In {F}, {W} scored {S} while {G} scored {S2} and {H}.',
                                 '{W} returned {aS} in {F}; {G} had {aS2} and {H}.']),
                  ['rounds'], F=w.round_link(n, 'the final round'), W=w.who(w.f['result']['winner']), S=last,
                  aS=art(last), aS2=art(g['final_round']), G=w.who(g['golfer']), S2=g['final_round'], H=finish_text(g['pos'], g['tied']))


def _to_place(pos, tied):
    if pos == 1:
        return 'a share of the lead' if tied else 'the lead'
    return place_text(pos, tied)


def _score_txt(leader):
    tp = to_par_text(leader.get('to_par'))
    return f'{leader["total"]}' + (f' ({tp})' if tp else '')


def _rounds(w, primary, tags):
    r = w.f.get('rounds')
    if not r:
        return
    n, path, leaders, low = r['n'], r['winner_path'], r['leaders'], r['low']
    win = w.f['result']['winner']
    W = w.who(win)
    said = 0
    if primary == 'wire_to_wire':
        g = [x for x in r['gap'] if x is not None]
        s0 = path[0]['score']
        w.say(w.pick('r1', ['{W} opened with {S} to lead {A}{T}.', 'A first-round {S} put {W} in front {A}{T}.']),
              ['rounds'], W=W, S=s0, A=w.round_link(1), T=' (shared)' if path[0]['tied'] else '')
        if g and any(g):
            w.say('The lead over the next player after each round: {G}.', ['rounds'], extra_src=r['src'],
                  G=', '.join('shared' if not x else strokes(x) for x in r['gap'][:n]))
        return
    # the first round's leader, unless it was the winner and the story leads elsewhere
    l1 = leaders[0]
    if win not in l1['golfers']:
        p1 = path[0]
        w.say(w.pick('r1', ['{G} led {A} at {L}, with {W} {P}.', '{G} was in front {A} at {L}; {W} was {P}.']),
              ['rounds'], G=w.whos(l1['golfers'][:2]) if len(l1['golfers']) <= 2 else f'{len(l1["golfers"])} players',
              A=w.round_link(1), L=_score_txt(l1), W=W, P=place_text(p1['pos'], p1['tied']))
        said += 1
    bm = r.get('best_move')
    cb = 'comeback' in tags
    if bm and bm['gain'] >= 3 and not (cb and bm['round'] == n):
        w.say(w.pick('move', ['{W} moved from {A} to {B} with {aS} in {R}.',
                              '{aS} in {R} took {W} from {A} to {B}.']),
              ['rounds'], W=W, A=place_text(bm['from'], False),
              B=_to_place(bm['to'], path[bm['round'] - 1]['tied']), aS=art(bm['score']),
              R=w.round_link(bm['round'], round_name(bm['round'], n)))
        said += 1
    took = r.get('took_lead')
    if cb:
        pass                                          # (the comeback section has told how the lead was taken)
    elif took and took > 1 and took < n:
        w.say(w.pick('took', ['{W} took the lead {A} and kept it to the end.',
                              '{W} led {A} and was not caught.']),
              ['rounds'], W=W, A=w.round_link(took))
        said += 1
    elif took == n and n > 1 and primary not in ('comeback', 'playoff'):
        w.say('{W} was not in front {A} and took the lead only in {F}.', ['rounds'], W=W, A=w.round_link(n - 1),
              F=w.round_link(n, 'the final round'))
    # the winner's low round, when it was the day's lowest
    best_k = min(range(n), key=lambda i: (path[i]['score'] if path[i]['score'] is not None else 999, i))
    s = path[best_k]['score']
    if s is not None and win in low[best_k]['golfers'] and said < 3 and not (cb and best_k == n - 1):
        tp = to_par_text(low[best_k]['to_par'])
        alone = len(low[best_k]['golfers']) == 1
        w.say(w.pick('low', ['{W}\'s {S}{TP} in {R} was the {X} round of the day.',
                             'The {X} score in {R} was {W}\'s {S}{TP}.']),
              ['rounds'], W=W, S=s, TP=f' ({tp})' if tp else '', R=w.round_link(best_k + 1, round_name(best_k + 1, n)),
              X='lowest' if alone else 'joint lowest')


def _separation(w, primary, tags):
    f = w.f
    r = f.get('rounds')
    res = f['result']
    m = res.get('margin')
    if not m:
        return
    if r and primary in ('runaway', 'wire_to_wire', 'upset', 'standard', 'first_win', 'close_finish', 'comeback'):
        n = r['n']
        g = r['gap']
        if n >= 2 and g[n - 2] is not None and primary in ('runaway', 'wire_to_wire', 'standard', 'first_win'):
            last = r['winner_path'][n - 1]['score']
            w.say(w.pick('sep', ['{W} went into {F} {G} ahead and closed with {S}, to win by {M}.',
                                 'With a lead of {G} {A}, {W} scored {S} in {F} and won by {M}.']),
                  ['rounds', 'result'], W=w.who(res['winner']), F=w.round_link(n, 'the final round'),
                  G=strokes(g[n - 2]), S=last, M=strokes(m), A=w.round_link(n - 1))
            return
    if primary == 'runaway' and not r:
        return
    told = {g['golfer'] for g in (r or {}).get('leaders_entering_final', ())} if 'comeback' in tags else set()
    if res['runners_up'] and primary not in ('close_finish', 'standard') and not set(res['runners_up']) <= told:
        parts = fill(w.pick('ru', ['{L} finished second, {M} back.', 'Second place went to {L}, {M} behind.']).replace(
            '{L}', '\x00'), M=strokes(m))
        _splice(parts, w.whos(res['runners_up'][:3]))
        w.say_parts(parts, ['result'])


def _playoff_section(w, primary, tags):
    po = w.f.get('playoff')
    if not po:
        return
    if po['holes']:
        last = po['holes'][-1]
        win = str(po['winner'])
        sc = last[2]
        others = [(int(g), v) for g, v in sc.items() if g != win and v is not None]
        if win in sc and others:
            parts = fill('It ended at the {N} extra hole (the course\'s {H}), where {W} scored {S} to \x00.',
                         N=ord_word(last[0]), H=ordinal(last[1]), W=w.who(po['winner']), S=sc[win])
            ins = []
            for i, (g, v) in enumerate(others):
                if i:
                    ins.append(' and ')
                ins += [[w.names(g), f'/golfer/{g}'], f'\'s {v}']
            _splice(parts, ins)
            w.say_parts(parts, ['playoff'])
        else:
            w.say('The playoff lasted {N} extra hole{S}.', ['playoff'], N=num(po['length']),
                  S='s' if po['length'] != 1 else '')
    elif po.get('length'):
        w.say('The playoff lasted {N} extra hole{S}; the scores on those holes were not recorded.', ['playoff'],
              N=num(po['length']), S='s' if po['length'] != 1 else '')


def _milestones(w, primary, tags):
    c = w.f.get('winner')
    if not c:
        return
    ev = w.f['event']
    W = w.who(c['golfer'])
    Q = ' in the retained history' if c['initial'] else ''
    wins = c['wins_before']
    scope = 'on the professional tours' if c['scope'] == 'professional' else 'in amateur and college golf'
    WL = ['win', c['src'][1][1]]
    if ev['major']:
        mb = c['majors_before']
        if mb == 0:
            if c['major_starts_before']:
                best = c['best_major_before']
                w.say(w.pick('m1', ['It was the first major win{Q} for {W}, at the {N} major start; the best finish '
                                    'before was {B}.',
                                    '{W} had played {K} major{P} before{Q} without winning one (best: {B}).']),
                      ['winner'], Q=Q, W=W, N=ordinal(c['major_starts_before'] + 1), K=num(c['major_starts_before']),
                      P='s' if c['major_starts_before'] != 1 else '', B=_best_txt(best))
            elif primary != 'first_win':
                w.say('It was {W}\'s first major start{Q}, and a win.', ['winner'], W=W, Q=Q)
        else:
            w.say(w.pick('mn', ['It was the {N} major win{Q} for {W}.', '{W} now had {K} majors{Q}.']), ['winner'],
                  N=ord_word(mb + 1), K=num(mb + 1), W=W, Q=Q)
        if c['slam']:
            w.say('With it {W} completed the career Grand Slam: a win in each of the four majors{Q}.', ['winner'],
                  W=W, Q=Q, extra_src=[['Career Grand Slam', '/grand-slam']])
    if primary != 'first_win':
        if wins == 0:
            w.say('It was the first {WL} {S}{Q} for {W}.', ['winner'], WL=WL, S=scope, Q=Q, W=W)
        elif wins + 1 in (2, 3, 5) or (wins + 1) % 10 == 0 or not ev['major']:
            w.say(w.pick('nw', ['It was {W}\'s {N} {WL} {S}{Q}.', '{W} had now won {K} times {S}{Q}.']), ['winner'],
                  W=W, N=ordinal(wins + 1), K=f'{wins + 1:,}', WL=WL, S=scope, Q=Q)
    sw = c['series_wins_before']
    d = w.f.get('defending')
    if sw and not (d and d['won']):
        w.say('{W} had won this tournament {K} before.', ['winner'], W=W,
              K='once' if sw == 1 else 'twice' if sw == 2 else f'{num(sw)} times')
    t = w.f.get('team')
    if t and ev['major']:
        if t['coach'] and t['caddie']:
            w.say('{W} was coached by {C} that week, with {K} caddying.', ['team'], W=W, C=w.who(t['coach']),
                  K=w.who(t['caddie']))
        elif t['coach']:
            w.say('{W} was coached by {C} that week.', ['team'], W=W, C=w.who(t['coach']))
        else:
            w.say('{K} caddied for {W} that week.', ['team'], W=W, K=w.who(t['caddie']))


def _sg(x):
    return f'{x:+.2f}'


GOLF_FIRSTS = (('putts', 'putts (fewest)'), ('gir', 'greens in regulation'), ('sg_putt', 'strokes gained putting'),
               ('sg_app', 'strokes gained on approach'), ('sg_arg', 'strokes gained around the green'),
               ('sg_ott', 'strokes gained off the tee'))


def _how(w, primary, tags):
    """How the winner played, from the recorded golf statistics: the figures over the week with their
    denominators, strokes gained against the engine's table, where they led the field, the margin over the
    runner-up split by strokes gained, and their earlier weeks."""
    g = w.f.get('golf')
    if not g:
        return
    W = w.who(g['golfer'])
    n = g['rounds']
    R = f'{num(n)} round{"s" if n != 1 else ""}'
    D = f' (measured drives averaged {g["distance"]:.1f} yards)' if g['distance'] else ''
    SC = (f', and got up and down {g["scr_made"]} times in {g["scr_att"]} tries after missing a green'
          if g['scr_att'] else '')
    SA = f' ({g["sand_saves"]} of {g["sand_att"]} from greenside bunkers)' if g['sand_att'] else ''
    w.say(w.pick('golf', ['Over the {R}, {W} took {P} putts ({PR} a round), hit {F} of {FA} fairways{D} and {G} of {H} '
                          'greens in regulation{SC}{SA}.',
                          '{W} hit {F} of {FA} fairways{D} and {G} of {H} greens in regulation over the {R}, took {P} '
                          'putts ({PR} a round){SC}{SA}.']),
          ['golf'], W=W, R=R, P=g['putts'], PR=f'{g["putts"] / n:.2f}', F=g['fairways'], FA=g['fairway_att'], D=D,
          G=g['gir'], H=g['holes'], SC=SC, SA=SA)
    sg = g['sg']
    w.say(w.pick('sg', ['By strokes gained against {T}: putting {PU}, approach {AP}, around the green {AR}, off the tee '
                        '{OT}, {TO} in all.',
                        'Against {T}, {W}\'s strokes gained came to {TO} in all: {PU} putting, {AP} on approach, {AR} '
                        'around the green and {OT} off the tee.']),
          ['golf'], T=SG_TABLE, W=W, PU=_sg(sg['sg_putt']), AP=_sg(sg['sg_app']), AR=_sg(sg['sg_arg']),
          OT=_sg(sg['sg_ott']), TO=_sg(g['sg_total']))
    firsts = [(label, g['ranks'][k][1]) for k, label in GOLF_FIRSTS if g['ranks'][k][0] == 1]
    if firsts and g['comparable'] >= 10:
        items = [label + (' (shared)' if tied else '') for label, tied in firsts]
        items = items[0] if len(items) == 1 else ', '.join(items[:-1]) + ' and ' + items[-1]
        w.say('Among the {C} golfers who played all {R}, {W} led in {I}.', ['golf'], C=g['comparable'], R=R,
              W=W, I=items)
    vs = g.get('vs_runner_up')
    if vs:
        p = vs['parts']
        rest = (f'; {vs["unaccounted"]:+.2f} is not accounted for by strokes gained' if abs(vs['unaccounted']) >= 0.05
                else '')
        w.say(w.pick('vs', ['Against {L}, the {M}-stroke margin breaks down by strokes gained into {OT} off the tee, {AP} '
                            'on approach, {AR} around the green and {PU} putting{X}.',
                            'Split by strokes gained, the {M}-stroke margin over {L} was {OT} off the tee, {AP} on '
                            'approach, {AR} around the green and {PU} putting{X}.']),
              ['golf'], L=w.who(vs['golfer']), M=num(vs['margin']), OT=_sg(p['sg_ott']), AP=_sg(p['sg_app']),
              AR=_sg(p['sg_arg']), PU=_sg(p['sg_putt']), X=rest)
    h = w.f.get('golf_history')
    if not h or h['comparable'] < GOLF_HISTORY_MIN:
        return
    NR = f'{num(n)}-round'
    Q = ' in the retained history' if h['initial'] else ''
    lp, bp = h['lowest_putts_before'], h['best_sg_putt_before']
    EV = lambda x: [x['label'], x['href']]
    if h['lowest_putts']:
        if not h['best_sg_putt'] and bp['value'] > sg['sg_putt']:
            w.say('The {P} putts were {W}\'s lowest {NR} total {S}{Q} to that date, but the best putting week by '
                  'strokes gained was still the {EV} ({V}).', ['golf', 'golf_history'], P=g['putts'], W=W, NR=NR,
                  S=GOLF_SCOPE, Q=Q, EV=EV(bp), V=_sg(bp['value']))
        else:
            w.say('The {P} putts were {W}\'s lowest {NR} total {S}{Q} to that date (the fewest before: {LP} at the '
                  '{EV}).', ['golf', 'golf_history'], P=g['putts'], W=W, NR=NR, S=GOLF_SCOPE, Q=Q, LP=lp['value'],
                  EV=EV(lp))
    elif h['best_sg_putt']:
        w.say('It was {W}\'s best putting week by strokes gained {S}{Q} to that date ({V}; the best before was the '
              '{EV}, {V0}).', ['golf', 'golf_history'], W=W, S=GOLF_SCOPE, Q=Q, V=_sg(sg['sg_putt']), EV=EV(bp),
              V0=_sg(bp['value']))
    if h['best_sg_total'] and not (h['lowest_putts'] or h['best_sg_putt']):
        bt = h['best_sg_total_before']
        w.say('Its {V} strokes gained in all was {W}\'s best {NR} week {S}{Q} to that date (before: the {EV}, '
              '{V0}).', ['golf', 'golf_history'], V=_sg(g['sg_total']), W=W, NR=NR, S=GOLF_SCOPE, Q=Q, EV=EV(bt),
              V0=_sg(bt['value']))


def _best_txt(pos):
    return 'none recorded' if pos is None else ('a win' if pos == 1 else ordinal(pos))


def _history_section(w, primary, tags):
    h = w.f.get('history')
    if not h:
        return
    res = w.f['result']
    H = f'{h["rounds"] * 18}-hole' if h.get('rounds') else 'same-format'
    X = (f' ({num(h["other_format"])} earlier edition{"s" if h["other_format"] != 1 else ""} over another number of '
         'holes not compared)') if h.get('other_format') else ''
    if h['lowest_to_par'] and h['same_format'] >= 3:
        w.say(w.pick('hist', ['{T} was the lowest winning score to par in the {N} earlier {H} editions{X}.',
                              'No earlier winner of the {E2}, in {N} {H} editions, had finished as low as {T}{X}.']),
              ['history', 'result'], T=to_par_text(res['to_par']), N=num(h['same_format']), H=H, X=X,
              E2=w.f['event']['name'])
    if h['largest_margin'] and h['same_format'] >= 3:
        w.say('The {M}-stroke margin was the widest in the tournament\'s {N} earlier {H} editions{X}.',
              ['history', 'result'], M=num(res['margin']), N=num(h['same_format']), H=H, X=X)


def _moments_section(w, primary, tags):
    ms = w.f.get('moments') or []
    winner = w.f['result']['winner']
    persp = (w.f.get('perspective') or {}).get('golfer')
    crs = [m for m in ms if m['kind'] == 'course record']
    if crs:
        m = crs[-1]
        tp = to_par_text(m.get('to_par'))
        w.say('{G} set the course record with {S}{TP}{R}{P}.', [], extra_src=m['src'], G=w.who(m['person']),
              S=m.get('score'), TP=f' ({tp})' if tp else '',
              R=f' in round {m["round"]}' if m.get('round') else '',
              P=f', beating the {m["previous"]} that stood before' if m.get('previous') else '')
    for m in ms:
        if m['kind'] in ('hole-in-one', 'albatross') and m['person'] in (winner, persp):
            w.say('{G} made {K} at the {H} hole{R}.', [], extra_src=m['src'], G=w.who(m['person']),
                  K='a hole-in-one' if m['kind'] == 'hole-in-one' else 'an albatross',
                  H=ordinal(m['hole']) if m.get('hole') else '',
                  R=f' in round {m["round"]}' if m.get('round') else '')
    others = [m for m in ms if m['kind'] == 'hole-in-one' and m['person'] not in (winner, persp)]
    if others:
        w.say('{N} other hole{S}-in-one {V} recorded during the event.', [], extra_src=others[0]['src'],
              N=num(len(others)).capitalize() if len(others) > 1 else 'One', S='s' if len(others) > 1 else '',
              V='were' if len(others) > 1 else 'was')


def _matches_section(w, primary, tags):
    m = w.f.get('matches')
    if not m or len(m['path']) < 2:
        return
    parts = ['On the way, ', w.who(w.f['result']['winner']), ' beat ']
    for i, x in enumerate(m['path'][:-1]):
        if i:
            parts.append(', ' if i < len(m['path']) - 2 else ' and ')
        parts.append(w.who(x['opponent']))
        parts.append(f' ({x["stage"]}' + (f', {x["result"]})' if x.get('result') else ')'))
    parts.append('.')
    w.say_parts(parts, ['matches'])


def _perspective_section(w, primary, tags):
    p = w.f.get('perspective')
    if not p or not p['played']:
        return
    P = w.who(p['golfer'])
    path = p.get('path')
    if path:
        steps = ', '.join(place_text(x['pos'], x['tied']).replace('in the lead', '1st').replace('tied for the lead', 'T1')
                          .replace('tied for ', 'T') for x in path)
        w.say('{P}\'s position after each round: {S}.', [], extra_src=p['rounds_src'], P=P, S=steps)
        b = p.get('best_round')
        if b:
            tp = to_par_text(b['to_par'])
            w.say('{P}\'s best round was {S}{TP} in {K}{D}.', [], P=P, S=b['score'],
                  TP=f' ({tp})' if tp else '', K=[f'round {b["round"]}', b['href']],
                  D=', the lowest of that round' if b['day_low'] else '')
    if p.get('behind') is not None and p['pos'] is not None:
        w.say('{P} finished {B} behind the winner.', ['perspective'], P=P, B=strokes(p['behind']))
    pg = p.get('golf')
    if pg:
        w.say('{P} took {N} putts over {R}; strokes gained against {S}: {T} in all, {PU} putting.', ['perspective'],
              extra_src=[['statistics', _event_href(w.rec['event'], view='stats')]], P=P, N=pg['putts'],
              R=f'{num(pg["rounds"])} round{"s" if pg["rounds"] != 1 else ""}', T=_sg(pg['sg_total']), S=SG_TABLE,
              PU=_sg(pg['sg']['sg_putt']))
    if 'best_major_before' in p and p['pos'] is not None:
        prev = p['best_major_before']
        Q = ' in the retained history' if p['initial'] else ''
        if prev is None and p['major_starts_before'] == 0:
            w.say('It was {P}\'s first major start{Q}.', ['perspective'], P=P, Q=Q)
        elif prev is None or p['pos'] < prev:
            w.say('It was {P}\'s best finish in a major{Q} (before: {B}).', ['perspective'], P=P, Q=Q, B=_best_txt(prev))


SECTIONS = {'how': _how, 'lead': _lead, 'stakes': _stakes, 'upset': _upset, 'comeback': _comeback, 'rounds': _rounds,
            'separation': _separation, 'playoff': _playoff_section, 'milestones': _milestones,
            'history': _history_section, 'moments': _moments_section, 'matches': _matches_section,
            'perspective': _perspective_section}


# ---- the cache ------------------------------------------------------------------------------------------------------
class StoryCache:
    """Fact records and stories, kept when opened: in memory (bounded) and, for archived editions, in a small
    SQLite file beside the observer's other caches. Keys: (edition, perspective, site, FACT_VERSION, the stamp
    of the seasons the facts come from) for facts; (fact digest, NARRATIVE_VERSION) for stories."""

    MEMORY = 128

    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.mem = OrderedDict()
        self.lock = threading.Lock()
        self.hits = self.misses = self.seasons_built = 0

    def _db(self):
        if self.path is None:
            return None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            db = sqlite3.connect(self.path, timeout=5)
            db.execute('PRAGMA journal_mode=WAL')          # (the background indexer writes while pages read)
            db.execute('CREATE TABLE IF NOT EXISTS facts(event TEXT, perspective INT, site INT, version INT, stamp TEXT, '
                       'record TEXT, PRIMARY KEY(event, perspective, site))')
            db.execute('CREATE TABLE IF NOT EXISTS stories(digest TEXT, version INT, story TEXT, '
                       'PRIMARY KEY(digest, version))')
            db.execute('CREATE TABLE IF NOT EXISTS seasons(year INT PRIMARY KEY, sig TEXT, version INT, data BLOB)')
            db.execute('CREATE TABLE IF NOT EXISTS edition_rounds(event_id TEXT PRIMARY KEY, year INT, rounds INT)')
            db.execute('CREATE TABLE IF NOT EXISTS golf_weeks(person INT, year INT, week INT, event_id TEXT, rounds INT, '
                       'putts INT, sg_ott INT, sg_app INT, sg_arg INT, sg_putt INT)')
            db.execute('CREATE INDEX IF NOT EXISTS golf_weeks_person ON golf_weeks(person, year)')
            db.execute('CREATE INDEX IF NOT EXISTS golf_weeks_year ON golf_weeks(year)')
            db.execute('CREATE INDEX IF NOT EXISTS edition_rounds_year ON edition_rounds(year)')
            return db
        except (sqlite3.Error, OSError):
            return None

    @staticmethod
    def fact_key(eid, perspective, site, stamp):
        return ('facts', eid, perspective, site, FACT_VERSION, stamp)

    def get_facts(self, eid, perspective, site, stamp, disk=True):
        k = self.fact_key(eid, perspective, site, stamp)
        with self.lock:
            if k in self.mem:
                self.mem.move_to_end(k)
                self.hits += 1
                return self.mem[k]
        if disk and stamp is not None:
            db = self._db()
            if db is not None:
                try:
                    row = db.execute('SELECT version, stamp, record FROM facts WHERE event = ? AND perspective = ? AND '
                                     'site = ?', (eid, -1 if perspective is None else perspective,
                                                  -1 if site is None else site)).fetchone()
                finally:
                    db.close()
                if row and row[0] == FACT_VERSION and row[1] == stamp:
                    rec = json.loads(row[2])
                    self._remember(k, rec)
                    self.hits += 1
                    return rec
        self.misses += 1
        return None

    def put_facts(self, rec, stamp, disk=True, perspective=None, site=None):
        """Kept under the request's own (perspective, site): None means "the winner's" and "the golfer's site"."""
        k = self.fact_key(rec['event'], perspective, site, stamp)
        self._remember(k, rec)
        if disk and stamp is not None:
            db = self._db()
            if db is not None:
                try:
                    with db:                               # replaces the edition's earlier record (one per key)
                        db.execute('INSERT OR REPLACE INTO facts VALUES (?, ?, ?, ?, ?, ?)',
                                   (rec['event'], -1 if perspective is None else perspective, -1 if site is None else site,
                                    FACT_VERSION, stamp, json.dumps(rec)))
                except sqlite3.Error:
                    pass
                finally:
                    db.close()

    def get_story(self, dig, disk=True):
        k = ('story', dig, NARRATIVE_VERSION)
        with self.lock:
            if k in self.mem:
                self.mem.move_to_end(k)
                return self.mem[k]
        if disk:
            db = self._db()
            if db is not None:
                try:
                    row = db.execute('SELECT story FROM stories WHERE digest = ? AND version = ?',
                                     (dig, NARRATIVE_VERSION)).fetchone()
                finally:
                    db.close()
                if row:
                    st = json.loads(row[0])
                    self._remember(k, st)
                    return st
        return None

    def put_story(self, dig, story, disk=True):
        self._remember(('story', dig, NARRATIVE_VERSION), story)
        if disk:
            db = self._db()
            if db is not None:
                try:
                    with db:
                        db.execute('INSERT OR REPLACE INTO stories VALUES (?, ?, ?)',
                                   (dig, NARRATIVE_VERSION, json.dumps(story)))
                except sqlite3.Error:
                    pass
                finally:
                    db.close()

    def get_season(self, y, sig):
        """Season y's story index if it was built from the season as published now (its signature), else None."""
        k = ('season', y, sig, EXTRACT_VERSION)
        with self.lock:
            if k in self.mem:
                self.mem.move_to_end(k)
                return self.mem[k]
        db = self._db()
        if db is None:
            return None
        try:
            row = db.execute('SELECT sig, version, data FROM seasons WHERE year = ?', (y,)).fetchone()
        finally:
            db.close()
        if row and row[0] == sig and row[1] == EXTRACT_VERSION:
            got = json.loads(zlib.decompress(row[2]))
            self._remember(k, got)
            return got
        return None

    def put_season(self, y, sig, ext):
        ext = dict(ext)
        rounds_of, golf_weeks = ext.pop('rounds_of', {}), ext.pop('golf_weeks', [])
        self._remember(('season', y, sig, EXTRACT_VERSION), ext)
        self.seasons_built += 1
        db = self._db()
        if db is None:
            return
        try:
            with db:                                       # replaces an index of the season as published before
                db.execute('DELETE FROM edition_rounds WHERE year = ?', (y,))
                db.execute('DELETE FROM golf_weeks WHERE year = ?', (y,))
                db.executemany('INSERT OR REPLACE INTO edition_rounds VALUES (?, ?, ?)',
                               [(eid, y, r) for eid, r in rounds_of.items()])
                db.executemany('INSERT INTO golf_weeks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                               [(g, y, wk, eid, n, pu, a, b, c, d) for g, wk, eid, n, pu, a, b, c, d in golf_weeks])
                db.execute('INSERT OR REPLACE INTO seasons VALUES (?, ?, ?, ?)',
                           (y, sig, EXTRACT_VERSION, zlib.compress(json.dumps(ext).encode(), 6)))
        except sqlite3.Error:
            pass
        finally:
            db.close()

    def indexed_years(self, sigs):
        """The seasons of {year: signature} whose story index was built from the season as published now."""
        db = self._db()
        if db is None or not sigs:
            if db is not None:
                db.close()
            return set()
        try:
            rows = db.execute('SELECT year, sig, version FROM seasons').fetchall()
        finally:
            db.close()
        return {y for y, sig, v in rows if sigs.get(y) == sig and v == EXTRACT_VERSION}

    def golf_weeks(self, pid, years):
        db = self._db()
        if db is None or not years:
            if db is not None:
                db.close()
            return []
        try:
            q = (f'SELECT year, week, event_id, rounds, putts, sg_ott, sg_app, sg_arg, sg_putt FROM golf_weeks WHERE '
                 f'person = ? AND year IN ({",".join("?" * len(years))}) ORDER BY year, week, event_id')
            keys = ('year', 'week', 'event', 'rounds', 'putts', 'sg_ott', 'sg_app', 'sg_arg', 'sg_putt')
            return [dict(zip(keys, r)) for r in db.execute(q, [pid, *years])]
        finally:
            db.close()

    def edition_rounds(self, eids):
        db = self._db()
        if db is None or not eids:
            if db is not None:
                db.close()
            return {}
        try:
            out = {}
            for i in range(0, len(eids), 500):
                chunk = eids[i:i + 500]
                out.update(db.execute(f'SELECT event_id, rounds FROM edition_rounds WHERE event_id IN '
                                      f'({",".join("?" * len(chunk))})', chunk).fetchall())
            return out
        finally:
            db.close()

    def start_indexer(self, jobs):
        """Index these seasons ([year, season file, signature]) in a separate process (decoding season files would
        otherwise hold up the pages), once at a time; the stories that wait for them say so meanwhile."""
        if self.path is None or not jobs or self.indexing():
            return
        import subprocess
        self.path.parent.mkdir(parents=True, exist_ok=True)
        jobfile = self.path.with_suffix('.jobs.json')
        jobfile.write_text(json.dumps(jobs))
        with open(self.path.with_suffix('.log'), 'w') as err:
            self.indexer = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), 'index', str(self.path),
                                             str(jobfile)], stdout=subprocess.DEVNULL, stderr=err)

    def indexing(self):
        p = getattr(self, 'indexer', None)
        return p is not None and p.poll() is None

    def stop_indexer(self):
        p = getattr(self, 'indexer', None)
        if p is not None and p.poll() is None:
            p.terminate()
            try:
                p.wait(5)
            except Exception:
                p.kill()

    def _remember(self, k, v):
        with self.lock:
            self.mem[k] = v
            self.mem.move_to_end(k)
            while len(self.mem) > self.MEMORY:
                self.mem.popitem(last=False)


def story_data(story):
    """A narrated story as plain data (what the cache keeps), with the names it shows ({golfer: name}): a cached
    story is used only while every name still reads the same."""
    names = {}
    for s in story['sentences']:
        for p in s.parts:
            if not isinstance(p, str) and str(p[1]).startswith('/golfer/') and str(p[1])[8:].isdigit():
                names[str(p[1])[8:]] = p[0]
    return {'primary': story['primary'], 'patterns': story['patterns'], 'missing': story['missing'],
            'sentences': [s.to_dict() for s in story['sentences']], 'version': NARRATIVE_VERSION,
            'fact_digest': story.get('fact_digest'), 'names': names}


def _pending(rec):
    return any('still being indexed' in m for m in rec['missing'])


def tell(src, eid, perspective=None, site=None, cache=None, names=None):
    """(fact record, story data) for an edition, through the cache when one is given; (None, None) when the
    edition is not in the history."""
    stamp = src.stamp(eid)
    disk = getattr(src, 'cacheable', lambda e: True)(eid)
    rec = cache.get_facts(eid, perspective, site, stamp, disk) if cache is not None and stamp is not None else None
    if rec is None:
        rec = assemble(src, eid, perspective, site)
        if rec is None:
            return None, None
        if cache is not None and stamp is not None:      # (facts waiting for the index: this session only)
            cache.put_facts(rec, stamp, disk and not _pending(rec), perspective, site)
    names = names or (lambda g: src.person(g).get('name') or f'#{g}')
    st = cache.get_story(rec['digest'], disk) if cache is not None else None
    if st is not None and any(names(int(g)) != n for g, n in (st.get('names') or {}).items()):
        st = None                                        # a name reads differently now: written again
    if st is None:
        st = story_data(narrate(rec, names))
        if cache is not None:
            cache.put_story(rec['digest'], st, disk)
    return rec, st


# ---- the observer's pages ---------------------------------------------------------------------------------------------
def cache_for(w):
    c = w.__dict__.get('_story_cache')
    if c is None:
        path = None
        try:
            import observer_stats as ST
            p = ST.cache_path(w)
            path = p.with_name(p.name.replace('stats.sqlite', 'stories.sqlite'))
        except Exception:
            path = None
        c = w._story_cache = StoryCache(path)
    return c


def plain_name(w, pid):
    p = w.person(pid) if hasattr(w, 'person') else None
    return (p or {}).get('name') or f'#{pid}'


def render_sentence(s, esc):
    out = []
    links = set()
    for p in s['parts']:
        if isinstance(p, str):
            out.append(esc(p))
        else:
            out.append(f'<a href="{esc(p[1])}">{esc(p[0])}</a>')
            links.add(p[1])
    srcs = [x for x in s['src'] if x[1] not in links]
    tail = (' <span class="muted src">[' + ', '.join(f'<a href="{esc(h)}">{esc(lbl)}</a>' for lbl, h in srcs) + ']</span>'
            if srcs else '')
    return ''.join(out) + tail


def story_view(w, q, e):
    """The Story tab of an edition page: the recap from its facts, or the facts themselves (?facts=1)."""
    import observer as O
    eid = e['id']
    persp = O.one(q, 'for')
    persp = int(persp) if persp and str(persp).lstrip('-').isdigit() else None
    site = O.one(q, 'site')
    site = int(site) if site and site.isdigit() else None
    rec, st = tell(WorldSource(w, cache_for(w)), eid, persp, site, cache_for(w), names=lambda g: plain_name(w, g))
    if rec is None:
        return '<p class="muted">This edition is not in the published history or the current season.</p>'
    if O.one(q, 'facts'):
        return facts_view(w, rec, st)
    out = []
    lv = rec['facts']['event'].get('level')
    sents = st['sentences']
    if sents:
        out.append(f'<p class="lead">{render_sentence(sents[0], O.esc)}</p>')
    body = [render_sentence(s, O.esc) for s in sents[1:]]
    for i in range(0, len(body), 3):                     # short paragraphs
        out.append('<p>' + ' '.join(body[i:i + 3]) + '</p>')
    tags = ', '.join(PATTERN_NAMES[t] for t in st['patterns']) or 'recap'
    out.append(f'<p class="muted">Story shape: {O.esc(PATTERN_NAMES[st["primary"]])} (applies: {O.esc(tags)}). '
               f'<a href="{O.esc(story_href(eid, rec["perspective"], facts=True))}">Inspect the facts behind it</a>.'
               + ('' if lv else ' Stories are offered for majors, the Premier Tour and each circuit\'s flagship and '
                  'national championships; this one was opened directly.') + '</p>')
    if st['missing']:
        out.append('<p class="muted">Not in the record, so not in the story: ' + O.esc('; '.join(st['missing'])) + '.</p>')
    out.append('<p class="muted">Written from the recorded results when opened, without any outside service; the same '
               'facts always give the same words. Nothing here is simulated or affects results. Every linked claim '
               'opens the page it comes from. Counts and comparisons are as they stood when the event was played.</p>')
    return ''.join(out)


def facts_view(w, rec, st):
    import observer as O
    rows = []
    for k, v in rec['facts'].items():
        items = v if isinstance(v, list) else [v]
        for i, it in enumerate(items):
            vals = {kk: vv for kk, vv in it.items() if kk != 'src'}
            src = ', '.join(f'<a href="{O.esc(h)}">{O.esc(lbl)}</a>' for lbl, h in it.get('src', ()))
            rows.append([f'<span id="f-{O.esc(k)}">{O.esc(k)}{"" if len(items) == 1 else f" {i + 1}"}</span>',
                         f'<code>{O.esc(json.dumps(vals, sort_keys=True, default=str))}</code>', src or '—'])
    back = story_href(rec['event'], rec['perspective'])
    return (f'<p><a href="{O.esc(back)}">← the story</a> · fact version {FACT_VERSION}, narrative version '
            f'{NARRATIVE_VERSION}, digest <code>{O.esc(rec["digest"])}</code></p>'
            + O.table(['Fact', 'Recorded values', 'Sources'], rows)
            + ('<p class="muted">Not recorded: ' + O.esc('; '.join(rec['missing'])) + '.</p>' if rec['missing'] else '')
            + '<p class="muted">The facts are drawn from the season files and the history index (earlier results, '
              'earlier editions, the ranking of the week before), as of the week the event was played.</p>')


def headline(w, eid):
    """The story's first sentence as HTML (for the edition page and the Biggest Upsets list), or ''."""
    import observer as O
    try:
        rec, st = tell(WorldSource(w, cache_for(w)), eid, None, None, cache_for(w), names=lambda g: plain_name(w, g))
    except Exception as e:                            # a story never breaks the result page it decorates...
        if type(e).__name__ == 'ArchiveChanged':      # ...but a rolled-back history redraws the page (render)
            raise
        return ''
    if not st or not st['sentences']:
        return ''
    return render_sentence(st['sentences'][0], O.esc)


def upset_explanation(w, eid):
    """For the Biggest Upsets list and an edition's estimate panel: the story's upset sentences (its lead when the
    story is not an upset story), each claim linked, as HTML, followed by a link to the whole story; '' when the
    edition is not in the history. Called as observer_stories.upset_explanation(w, event_id)."""
    import observer as O
    rec, st = tell(WorldSource(w, cache_for(w)), eid, None, None, cache_for(w), names=lambda g: plain_name(w, g))
    if not st:
        return ''
    keep = [s for s in st['sentences'] if 'upset' in s['facts']] or st['sentences'][:1]
    return (' '.join(render_sentence(s, O.esc) for s in keep)
            + f' <a href="{O.esc(story_href(eid))}">The story</a>')


def profile_section(w, pid, rows):
    """The Stories list on a golfer's profile: their notable performances, newest first, each linked to its story."""
    import observer as O
    got = [r for r in rows if notable(r)]
    if not got:
        return ''
    got = list(reversed(got))
    shown = got[:15]
    items = ''.join(
        f'<li>{O.esc(r["year"])} {O.event_link(w, r["event"])}: '
        f'{"won" if r["pos"] == 1 else "finished " + ordinal(r["pos"])} · '
        f'<a href="{O.esc(story_href(r["event"], None if r["pos"] == 1 else pid))}">story</a></li>' for r in shown)
    more = (f'<p class="muted">{len(got) - len(shown)} more in the <a href="/golfer/{pid}?tab=results">results</a>.</p>'
            if len(got) > len(shown) else '')
    return (f'<h2>Stories ({len(got)})</h2><ul>{items}</ul>{more}<p class="muted">Wins in majors, Premier events and '
            'flagship championships, top-10 finishes in majors and top-5s in Premier events; each story is written '
            'from the recorded results when opened.</p>')


# ---- the background indexer (a separate process: python tools/observer_stories.py index STORE JOBS) -------------------
def index_seasons(store, jobs):
    """Build the story index of each [year, season file, signature] not already indexed as published."""
    c = StoryCache(store)
    for y, path, sig in jobs:
        if y in c.indexed_years({y: sig}):
            continue
        with gzip.open(path, 'rt') as f:
            d = json.load(f)
        c.put_season(y, sig, season_extract(d))
        c.mem.clear()


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == 'index':
        index_seasons(Path(sys.argv[2]), json.loads(Path(sys.argv[3]).read_text()))
