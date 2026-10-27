"""End-to-end major qualifying demonstration: every shot of every event is simulated.

    python tools/qualifying_demo.py

Builds a synthetic world (Premier, Challenger and lower-tour pros, club professionals, elite
amateurs), then plays two seasons of the top of the calendar: all 36 Premier Tour events, the elite
amateur championships (including match play), the Club Professional Championship, USA Open local and
final qualifying, Britannia regional and final qualifying, and the four majors. 2026 is a warm-up year
that creates history; the 2027 major fields are then built purely by the real-life qualification rules.

Stand-ins (until the season system exists): tour fields are taken from members in ranking order with
some top players resting; the world ranking and points lists are simple versions computed from these
simulated results; lower tours are not played. Courses are the calibration courses.
Writes reports/QUALIFYING_DEMO_REPORT.md.
"""
from __future__ import annotations

import random
import statistics as S
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import qualification as Q                                              # noqa: E402
from golfsim.calendar import WorldCalendar                                           # noqa: E402
from golfsim.course import ashford_ridge, georgia_national, hard_course, windy_links, easy_course  # noqa: E402
from golfsim.engine import Conditions                                                 # noqa: E402
from golfsim.golfer import ARCHETYPES, archetype_golfer                               # noqa: E402
from golfsim.tournament import play_event, play_stroke_and_match                      # noqa: E402

RNG = random.Random(2027)
COURSE = {'mid': ashford_ridge(), 'georgia': georgia_national(), 'hard': hard_course(), 'links': windy_links(),
          'easy': easy_course()}
POINTS = [500, 300, 190, 135, 110, 100, 90, 85, 80, 75, 70, 65, 60, 57, 55, 53, 51, 49, 47, 45]
CIRCUITS = (('PT_AMERICAS', .55, 'USA'), ('PT_EUROPE', .30, 'England'), ('PT_ASIA_PACIFIC', .15, 'Australia'))
COUNTRY_POOL = {'PT_AMERICAS': ['USA'] * 7 + ['Canada', 'Mexico', 'Argentina', 'Colombia'],
                'PT_EUROPE': ['England', 'Scotland', 'Ireland', 'Spain', 'Sweden', 'Germany', 'France', 'Denmark',
                              'South Africa', 'Italy', 'Northern Ireland'],
                'PT_ASIA_PACIFIC': ['Australia', 'Japan', 'South Korea', 'China', 'Thailand', 'India', 'New Zealand']}


class World:
    def __init__(self):
        self.golfers, self.ctx = {}, None
        self.group, self.circuit = {}, {}
        self.cal = WorldCalendar(2027)
        self.ctx = Q.QualificationContext.from_calendar(self.cal)
        self.points = defaultdict(lambda: defaultdict(float))     # (tour, year) -> id -> points
        self.wr_points = defaultdict(list)                        # id -> [(year, week, pts)]
        self.base = {}
        self.log = defaultdict(list)
        self.holes = 0
        gid = 0
        def add(group, overall, status, age, country, circuit=None):
            nonlocal gid
            gid += 1
            g = archetype_golfer(list(ARCHETYPES)[gid % len(ARCHETYPES)], round(max(20, min(96, overall)), 1),
                                 name=f'{group[:3]}{gid}')
            g.personality['big_stage'] = RNG.uniform(15, 85)
            self.golfers[gid] = g
            self.ctx.people[gid] = Q.Person(gid, g.name, status, age, country)
            self.group[gid] = group
            self.circuit[gid] = circuit
            self.base[gid] = overall
        for _ in range(450):
            c = RNG.choices([c for c, _, _ in CIRCUITS], [w for _, w, _ in CIRCUITS])[0]
            add('Premier', RNG.gauss(74, 4.6), 'pro', RNG.randint(22, 46), RNG.choice(COUNTRY_POOL[c]), c)
        for _ in range(700):
            c = RNG.choices([c for c, _, _ in CIRCUITS], [w for _, w, _ in CIRCUITS])[0]
            add('Challenger', RNG.gauss(67, 3.5), 'pro', RNG.randint(21, 40), RNG.choice(COUNTRY_POOL[c]), c)
        for _ in range(1200):
            add('Lower-tour pro', RNG.gauss(57, 6), 'pro', RNG.randint(20, 45), RNG.choice(['USA'] * 4 + ['England', 'Canada', 'Australia', 'Japan']))
        for _ in range(300):
            add('Club pro', RNG.gauss(52, 6), 'club_pro', RNG.randint(28, 58), 'USA')
        for _ in range(320):
            region = RNG.choice(['USA'] * 4 + ['England', 'Scotland', 'Spain', 'Sweden', 'Japan', 'South Korea',
                                               'Australia', 'Argentina', 'Mexico', 'South Africa', 'Thailand', 'China'])
            add('Amateur', RNG.gauss(56, 7), 'amateur', RNG.randint(17, 23) if RNG.random() < .8 else RNG.randint(25, 45), region)

    # -- rankings (stand-in) ----------------------------------------------------------------------
    def snapshot(self, year, week):
        def score(gid):
            recent = sum(p * (1 if (year - y) * 52 + week - w <= 13 else .55)
                         for y, w, p in self.wr_points[gid] if 0 <= (year - y) * 52 + week - w < 104)
            return (self.base[gid] - 60) * 2.2 + recent
        pros = [g for g in self.golfers if self.ctx.people[g].status != 'club_pro']
        self.ctx.world_rankings[(year, week)] = sorted(pros, key=score, reverse=True)
        ams = [g for g in self.golfers if self.ctx.people[g].status == 'amateur']
        self.ctx.amateur_rankings[(year, week)] = sorted(ams, key=score, reverse=True)
        for tour in ('PT_AMERICAS', 'PT_EUROPE'):
            pts = self.points[(tour, year)]
            if pts:
                self.ctx.standings[(tour, year, week)] = sorted(pts, key=pts.get, reverse=True)

    def rank(self, year, week):
        return {g: i for i, g in enumerate(self.ctx.ranking(year, week))}

    # -- playing events ---------------------------------------------------------------------------
    def play(self, ed, field_ids, course, cut_top=65, prestige=0.8, cond=None, sites=1):
        s = ed.series
        field = [self.golfers[g] for g in field_ids]
        by_name = {self.golfers[g].name: g for g in field_ids}
        if s.match_play:
            res = play_stroke_and_match(field, course, RNG)
            finish = [(by_name[g.name], pos) for g, pos in res]
            self.holes += len(field) * 36 + 63 * 18
            self.ctx.add_result(s.series_id, ed.year, finish)
            return finish
        chunks = [field[i::sites] for i in range(sites)] if sites > 1 else [field]
        all_finish = []
        for site, chunk in enumerate(chunks):
            board, _ = play_event(chunk, course, RNG, cut_top=cut_top, prestige=prestige, rounds_n=s.rounds,
                                  cut_after=2 if s.cut_top else None,
                                  cond_by_round={r: cond for r in range(1, 5)} if cond else None)
            finish, pos, last = [], 0, None
            for i, (g, total, rounds) in enumerate(board):
                pos = 1 if i == 0 else (pos if total == last else i + 1)
                if i == 1 and total == board[0][1]:
                    pos = 2                                  # playoff loser
                last = total
                finish.append((by_name[g.name], pos))
                self.holes += 18 * len(rounds)
            made = {g for g, _ in finish}
            finish += [(by_name[g.name], None) for g in chunk if by_name[g.name] not in made]
            self.holes += sum(36 for g in chunk if by_name[g.name] not in made)
            self.ctx.add_result(s.series_id, ed.year, finish, site=site)
            all_finish += finish
        return all_finish

    def award(self, ed, finish, tour=None, weight=1.0):
        for gid, pos in finish:
            if pos is None or pos > len(POINTS) * 3:
                continue
            pts = POINTS[pos - 1] if pos <= len(POINTS) else 40 * 0.97 ** (pos - len(POINTS))
            if tour:
                self.points[(tour, ed.year)][gid] += pts * weight
            self.wr_points[gid].append((ed.year, ed.week, pts * weight / 25))

    def tour_field(self, ed, year, week):
        """Stand-in for the weekly entry system: members in ranking order, some stars resting."""
        s = ed.series
        rank = self.rank(year, week - 1)
        members = [g for g in self.golfers if self.circuit[g] == s.tour and self.group[g] == 'Premier']
        rest = .55 if s.category == 'opportunity' else .25
        members = [g for g in members if not (rank.get(g, 999) < 40 and RNG.random() < rest)]
        if s.category == 'flagship':                     # flagships draw stars from every circuit
            members += [g for g in self.golfers if self.group[g] == 'Premier' and self.circuit[g] != s.tour
                        and rank.get(g, 999) < 60 and RNG.random() < .5]
        members.sort(key=lambda g: rank.get(g, 9999))
        field = members[:s.field]
        if len(field) < s.field:
            subs = sorted((g for g in self.golfers if self.group[g] == 'Challenger' and self.circuit[g] == s.tour),
                          key=lambda g: rank.get(g, 9999))
            field += subs[:s.field - len(field)]
        return field

    def run_year(self, year, last_week, warmup):
        eds = [e for e in self.cal.editions(year) if e.week <= last_week]
        fields = {}
        for week in range(1, last_week + 1):
            for ed in [e for e in eds if e.week == week]:
                s = ed.series
                sid = s.series_id
                rank = self.rank(year, week - 1)
                if s.kind == 'major':
                    if warmup:     # pre-history: the year before the world starts has no qualifying record
                        pool = sorted(self.ctx.ranking(year, week - 1), key=lambda g: rank.get(g, 9999))
                        ids = [g for g in pool if self.ctx.people[g].status != 'club_pro'][:s.field]
                    else:
                        f = Q.build_field(sid, year, self.ctx)
                        fields[sid] = f
                        ids = f.ids()
                    course, cond = {'TOUR_MASTERS': ('georgia', None), 'PREMIER_TOUR_CHAMPIONSHIP': ('mid', None),
                                    'USA_OPEN': ('hard', None), 'BRITANNIA_OPEN': ('links', Conditions(wind_mph=18))}[sid]
                    finish = self.play(ed, ids, COURSE[course], cut_top=s.cut_top, prestige=1.0, cond=cond)
                    self.award(ed, finish, 'PT_AMERICAS', 1.5)
                    self.award(ed, finish, 'PT_EUROPE', 1.5)
                elif s.tier == 1:
                    finish = self.play(ed, self.tour_field(ed, year, week), COURSE['mid'], cut_top=s.cut_top)
                    self.award(ed, finish, s.tour, 1.0 if s.category != 'opportunity' else .6)
                elif sid in ('NATIONAL_OPEN_JAPAN', 'NATIONAL_OPEN_NEW_ZEALAND', 'NATIONAL_OPEN_SOUTH_KOREA'):
                    pool = [g for g in self.golfers if self.group[g] in ('Challenger', 'Lower-tour pro')
                            and self.circuit[g] in ('PT_ASIA_PACIFIC', None)]
                    stars = [g for g in self.golfers if self.circuit[g] == 'PT_ASIA_PACIFIC' and self.group[g] == 'Premier']
                    field = RNG.sample(stars, min(25, len(stars))) + RNG.sample(pool, 120)
                    self.award(ed, self.play(ed, field, COURSE['mid'], cut_top=60))
                elif s.category == 'elite_amateur':
                    ams = [g for g in self.golfers if self.ctx.people[g].status == 'amateur'
                           and (s.eligibility != 'mid_amateur' or self.ctx.people[g].age >= 25)]
                    ams.sort(key=lambda g: self.base[g] + RNG.gauss(0, 6), reverse=True)
                    self.award(ed, self.play(ed, ams[:s.field], COURSE['mid'], cut_top=60), weight=.5)
                elif sid == 'CLUB_PRO_CHAMPIONSHIP':
                    clubs = sorted((g for g in self.golfers if self.group[g] == 'Club pro'),
                                   key=lambda g: self.base[g] + RNG.gauss(0, 5), reverse=True)
                    self.play(ed, clubs[:s.field], COURSE['mid'], cut_top=70)
                elif not warmup and sid.startswith(('USA_OPEN_LOCAL', 'USA_OPEN_FINAL', 'BRITANNIA_REGIONAL', 'BRITANNIA_FINAL')):
                    self.qualifying(ed, year, week)
            self.snapshot(year, week)
        if warmup:
            for tour in ('PT_AMERICAS', 'PT_EUROPE'):
                pts = self.points[(tour, year)]
                self.ctx.standings[(tour, year)] = sorted(pts, key=pts.get, reverse=True)
            # Lower tours are not simulated in this demo: their order-of-merit winners are stand-ins.
            for tour in ('CH_JAPAN', 'CH_ASIA', 'RG_AUSTRALASIA', 'RG_SOUTHERN_AFRICA'):
                cands = [g for g in self.golfers if self.group[g] == 'Challenger']
                self.ctx.standings[(tour, year)] = [max(RNG.sample(cands, 40), key=lambda g: self.base[g])]
        return fields

    def qualifying(self, ed, year, week):
        s = ed.series
        sid = s.series_id
        major = 'USA_OPEN' if sid.startswith('USA_OPEN') else 'BRITANNIA_OPEN'
        rank = self.rank(year, week - 1)
        exempt = {e.golfer_id for e in Q.build_field(major, year, self.ctx).entries if e.primary[1:] not in ('Q', 'F')}
        exempt_from_local = {g for g in self.golfers if rank.get(g, 9999) < (250 if major == 'USA_OPEN' else 300)}
        if sid.startswith(('USA_OPEN_LOCAL', 'BRITANNIA_REGIONAL')):
            # Open to professionals and amateurs good enough (handicap ~0.4 or better = rating 40+).
            pool = [g for g in self.golfers if g not in exempt and g not in exempt_from_local
                    and self.base[g] >= 40 and self.ctx.people[g].status != 'club_pro' and not self.log[('entered', major)].count(g)]
            n = s.field * s.sites
            entrants = RNG.sample(pool, min(n, len(pool)))
            self.log[('entered', major)] += entrants
            finish = self.play(ed, entrants, COURSE['easy' if major == 'USA_OPEN' else 'links'], sites=s.sites,
                               cond=None if major == 'USA_OPEN' else Conditions(wind_mph=14))
            per = Q.STAGES['USA_OPEN_FINAL' if major == 'USA_OPEN' else 'BRITANNIA_FINAL']['per_site']
            for site in range(s.sites):
                adv = [g for g, pos in self.ctx.finishers(sid, year, site) if pos is not None][:per]
                self.log[('advanced', major)] += adv
            self.log[('local_sites', major)].append(s.sites)
        else:
            # Final qualifying: local/regional advancers plus players exempt from the earlier stage.
            advanced = [g for g in self.log[('advanced', major)] if g not in self.log[('final', major)]]
            direct = [g for g in exempt_from_local if g not in exempt and self.ctx.people[g].status != 'club_pro'
                      and RNG.random() < .7 and g not in self.log[('final', major)]]
            total = s.field * s.sites
            if sid == 'USA_OPEN_FINAL_INTL':
                direct = [g for g in direct if self.circuit[g] in ('PT_EUROPE', 'PT_ASIA_PACIFIC')]
                entrants = (direct[:total])
            else:
                entrants = (advanced + direct)[:total]
            self.log[('final', major)] += entrants
            self.play(ed, entrants, COURSE['mid' if major == 'USA_OPEN' else 'links'], sites=s.sites,
                      cond=None if major == 'USA_OPEN' else Conditions(wind_mph=14))


def main():
    t0 = time.perf_counter()
    w = World()
    w.snapshot(2025, 52)
    w.run_year(2026, 52, warmup=True)
    fields = w.run_year(2027, 30, warmup=False)
    elapsed = time.perf_counter() - t0
    labels = {r.code: (r.label, r.analogue) for rules in Q.RULES.values() for r in rules}
    out = ['# Major qualifying demonstration — 2027', '',
           f'Two simulated seasons at the top of the world calendar (2026 warm-up, 2027 to week 30): '
           f'{w.holes:,} holes, every shot simulated, in {elapsed:.0f} seconds. '
           f'World: {len(w.golfers):,} golfers (450 Premier, 700 Challenger, 1,200 lower-tour pros, 300 club pros, '
           '320 elite amateurs).', '',
           '_Stand-ins until the season system exists: tour fields come from members in ranking order; the world '
           'ranking and points lists are simple versions computed from these simulated results; lower tours are '
           'not played; courses are the calibration courses._', '']
    real = {'TOUR_MASTERS': 'About 85-95 invitees, ~5-7 amateurs, no open qualifying.',
            'PREMIER_TOUR_CHAMPIONSHIP': '156 players: 20 club professionals, nearly all of the world top 100.',
            'USA_OPEN': '156 players: roughly half exempt; ~10,000 entrants at local qualifying; ~60-70 places from final qualifying.',
            'BRITANNIA_OPEN': '156 players: ~16 from Final Qualifying, ~20-30 from the Open Qualifying Series, ~6-10 amateurs.'}
    for sid in Q.MAJOR_SERIES:
        f = fields[sid]
        finish = dict(w.ctx.finishers(sid, 2027))
        winner = w.ctx.winner(sid, 2027)
        prim = {e.golfer_id: e.primary for e in f.entries}
        ams = sum(w.ctx.people[g].status == 'amateur' for g in f.ids())
        clubs = sum(w.ctx.people[g].status == 'club_pro' for g in f.ids())
        out += [f'## {w.cal.by_id[sid].name} (week {Q.MAJOR_WEEK[sid]})', '',
                f'Field: **{len(f.entries)}** players — {ams} amateurs, {clubs} club professionals. Real life: {real[sid]}', '',
                '| Entry route (primary) | Real-life analogue | Players | Best finish |', '|---|---|---|---|']
        best = defaultdict(lambda: None)
        for g, code in prim.items():
            pos = finish.get(g)
            if pos is not None and (best[code] is None or pos < best[code]):
                best[code] = pos
        for code, n in sorted(f.route_counts.items(), key=lambda kv: [r.code for r in Q.RULES[sid]].index(kv[0])):
            bf = best[code]
            out.append(f'| {labels[code][0]} | {labels[code][1]} | {n} | {"MC" if bf is None else bf} |')
        wcode = prim.get(winner, '?')
        g = w.golfers[winner]
        out += ['', f'**Champion:** {g.name} (overall {g.overall:.1f}, {w.group[winner]}), entered via '
                f'“{labels[wcode][0]}”{", also exempt via " + ", ".join(labels[c][0] for c in next(e for e in f.entries if e.golfer_id == winner).sources[1:]) if len(next(e for e in f.entries if e.golfer_id == winner).sources) > 1 else ""}.', '']
    out += ['## Qualifying stages, 2027', '', '| Stage | Players | Sites | Notes |', '|---|---|---|---|']
    for major, local_name, final_name in (('USA_OPEN', 'Local qualifying (18 holes)', 'Final qualifying (36 holes)'),
                                         ('BRITANNIA_OPEN', 'Regional qualifying (18 holes)', 'Final qualifying (36 holes)')):
        out.append(f'| {w.cal.by_id[major].name}: {local_name} | {len(w.log[("entered", major)])} | '
                   f'{sum(w.log[("local_sites", major)])} | {len(w.log[("advanced", major)])} advanced |')
        out.append(f'| {w.cal.by_id[major].name}: {final_name} | {len(w.log[("final", major)])} | '
                   f'{10 if major == "USA_OPEN" else 4} | {fields[major].route_counts.get("UQ" if major == "USA_OPEN" else "BQ", 0)} qualified |')
    text = '\n'.join(out) + '\n'
    (ROOT / 'reports' / 'QUALIFYING_DEMO_REPORT.md').write_text(text, encoding='utf8')
    print(text)


if __name__ == '__main__':
    main()
