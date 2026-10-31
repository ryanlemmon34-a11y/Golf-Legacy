"""Amateur support: restricted, in-kind help with golf costs for amateurs who show success (rules 2026-11-02).

An initial calibration, not proven amounts: three bands with season caps, earned only by what can be seen --
the amateur ranking, titles, major results and places, and recent results -- never hidden ability or potential.

    Band A, up to $25,000   amateur ranking 1-10; last season's USA Amateur or Britannia Amateur champion or
                            annual amateur award; a top-25 finish in a major as an amateur
    Band B, up to $12,000   amateur ranking 11-50; an earned major place this season (an amateur's conditional
                            place included); a continental amateur title or the USA Mid-Amateur
    Band C, up to $5,000    amateur ranking 51-150; or results-based scouting: among the 150 amateurs with the
                            most amateur ranking points won in the last 26 weeks

What it pays: an amateur's own golf costs as they are incurred -- event travel and entry, a caddie's weekly fee
and a coach's fee -- out of one season cap. Never cash, living costs or moving; unused support lapses at the
season's end. It is restricted money, so it counts toward what a golfer can afford for golf only (Season.
spendable), never toward anything else.

Payment order: a school pays its college events and a club its professional's section golf (nothing to cover);
then this support; then the golfer's own money. The organizer pays a major trip only when support and the
golfer's money together cannot (Season.major_field), so no trip is paid twice.

Timing: the season's budget opens in week 1 from last season's facts and the places already earned for this
one. A new Band A or B achievement during the season raises the cap from the next week (the difference is
added); support is never cut during a season. Renewal each winter: the band the facts give, but never more than
one band below the one held at the end of last season (A -> B -> C -> none), so one quiet year is not a cliff.
It ends on turning professional or retiring (nothing is drawn by anyone who is no longer an amateur).

Ledger: each covered cost stays in the golfer's ledger where it belongs (events, caddie, coaching) and the
support that paid it is a matching income line (am_support), so cash moves only by what the golfer paid; every
payment is also recorded with its band, what it covered and the event (Season.am_support_log).
"""
from __future__ import annotations

BANDS = {'A': 25000.0, 'B': 12000.0, 'C': 5000.0}
ORDER = ('A', 'B', 'C')
COVERS = ('events', 'caddie', 'coaching')          # the golf costs it pays (never living, moving or shares)
PAYER = 'amateur support'
MARQUEE = ('USA_AMATEUR', 'BRITANNIA_AMATEUR')
CONTINENTAL = ('EUROPEAN_AMATEUR', 'ASIA_PACIFIC_AMATEUR', 'LATIN_AMERICA_AMATEUR', 'AFRICA_AMATEUR', 'USA_MID_AMATEUR')
SCOUT_WEEKS = 26
SCOUT_TOP = 150


def better(a, b):
    """The higher of two bands (None = none)."""
    if a is None:
        return b
    if b is None:
        return a
    return a if ORDER.index(a) <= ORDER.index(b) else b


def step_down(band):
    return None if band in (None, 'C') else ORDER[ORDER.index(band) + 1]


def eligible(g):
    return g.status == 'amateur' and g.lifestyle != 'retired'


def _majors(season):
    return [s.series_id for s in season.cal.series if s.kind == 'major']


def facts(season, titles_year, places_years):
    """{gid: [(band, reason)]}: the season's title, major-result and major-place facts, gathered once per pass
    (the ranking is read per golfer): titles and top-25s of `titles_year`, earned places for `places_years`."""
    ctx, name = season.ctx, (lambda sid: season.cal.by_id[sid].name)
    out = {}

    def add(gid, band, why):
        if gid is not None:
            out.setdefault(gid, []).append((band, why))
    for sid in MARQUEE:
        add(ctx.winner(sid, titles_year), 'A', f'{titles_year} {name(sid)} champion')
    add(ctx.award('amateur_award', titles_year), 'A', f'{titles_year} annual amateur award')
    for sid in _majors(season):
        for gid in ctx.placed(sid, titles_year, 25):
            add(gid, 'A', f'top 25 at the {titles_year} {name(sid)}')
    for y in places_years:
        for major, book in sorted(season.major_rights.get(y, {}).items()):
            for gid, r in sorted(book.items()):
                if not str(r.get('result') or '').startswith(('expired', 'withdrawn: retired')):
                    add(gid, 'B', f'an earned place in the {y} {name(major)}')
    for sid in CONTINENTAL:
        if sid in season.cal.by_id:
            add(ctx.winner(sid, titles_year), 'B', f'{titles_year} {name(sid)} champion')
    return out


def band_of(rank, found):
    """(band, [reasons]) from the amateur ranking `rank` and the golfer's facts `found`."""
    out = list(found)
    if rank is not None:
        out.append(('A' if rank <= 10 else 'B' if rank <= 50 else 'C' if rank <= 150 else None,
                    f'amateur ranking {rank}'))
    band = None
    for b, _ in out:
        band = better(band, b)
    return band, [why for b, why in out if b == band and b is not None]


def recent_form(season, year, week):
    """{gid: rank} of amateurs by amateur ranking points won in the last SCOUT_WEEKS weeks (the scouting route:
    results only, never ratings or potential), top SCOUT_TOP."""
    now = season.abs_week(year, week)
    pts = {}
    for gid, rows in season.am.items():
        g = season.g.get(gid)
        if g is None or not eligible(g):
            continue
        s = sum(p for aw, p in rows if now - aw < SCOUT_WEEKS)
        if s > 0:
            pts[gid] = s
    ids = sorted(pts, key=lambda k: (-pts[k], k))[:SCOUT_TOP]
    return {gid: i + 1 for i, gid in enumerate(ids)}


def open_season(season, year):
    """Week 1: each amateur's band from last season's facts and this season's places, never more than one band
    below what they held at last season's end; the budget opens for the season."""
    prev = season.am_support_held.get(year - 1, {})
    form = recent_form(season, year, 0)
    found = facts(season, year - 1, (year,))
    contracts = {}
    for g in sorted(season.world.golfers, key=lambda x: x.id):
        if not eligible(g):
            continue
        band, why = band_of(season.am_pos.get(g.id), found.get(g.id, ()))
        if band is None and g.id in form:
            band, why = 'C', [f'scouting: {form[g.id]} in amateur ranking points won over the last {SCOUT_WEEKS} weeks']
        kept = step_down(prev.get(g.id))
        if kept is not None and better(kept, band) == kept and kept != band:
            band, why = kept, [f'renewed one band lower (held {prev[g.id]} last season)']
        if band is None:
            continue
        contracts[g.id] = {'band': band, 'cap': BANDS[band], 'drawn': 0.0, 'from': [year, 1], 'basis': why,
                           'upgrades': [], 'ended': None}
    season.am_support = contracts


def upgrade(season, year, week):
    """After the week: a new Band A or B achievement raises the cap from the next week (never a cut)."""
    found = facts(season, year, (year, year + 1))
    for g in season.active_golfers():
        if not eligible(g):
            continue
        rank = season.am_pos.get(g.id)
        if (rank is None or rank > 50) and g.id not in found:
            continue
        c = season.am_support.get(g.id)
        if c is not None and c['band'] == 'A':
            continue
        band, why = band_of(rank, found.get(g.id, ()))
        if band not in ('A', 'B'):
            continue
        if c is None:
            season.am_support[g.id] = {'band': band, 'cap': BANDS[band], 'drawn': 0.0, 'from': [year, week + 1],
                                       'basis': why, 'upgrades': [], 'ended': None}
        elif better(band, c['band']) == band and band != c['band']:
            c['upgrades'].append([year, week + 1, band, why])
            c['cap'] += BANDS[band] - BANDS[c['band']]
            c['band'] = band


def left(season, g):
    """What this season's support can still pay for (0 for anyone without an active contract)."""
    c = season.am_support.get(g.id)
    if c is None or not eligible(g):
        return 0.0
    return max(0.0, c['cap'] - c['drawn'])


def cover(season, g, year, field, amount, what=None):
    """The part of a golf cost the support pays (drawn and logged here; the caller books the ledger)."""
    if field not in COVERS or amount <= 0:
        return 0.0
    rest = left(season, g)
    if rest <= 0:
        return 0.0
    paid = min(amount, rest)
    c = season.am_support[g.id]
    c['drawn'] += paid
    season.am_support_log[year].append({'week': season.week, 'gid': g.id, 'covers': field, 'event': what,
                                        'amount': round(paid, 2), 'band': c['band']})
    return paid


def close_season(season, year):
    """The season's contracts as they ended (archived), and the band each golfer holds into the winter."""
    paid = {}
    for p in season.am_support_log.get(year, ()):
        d = paid.setdefault(p['gid'], {})
        d[p['covers']] = d.get(p['covers'], 0.0) + p['amount']
    out = {}
    for gid, c in sorted(season.am_support.items()):
        g = season.g.get(gid)
        ended = (None if g is not None and eligible(g) else
                 'retired' if g is None or g.lifestyle == 'retired' else 'turned professional')
        out[gid] = dict(c, drawn=round(c['drawn'], 2), ended=ended,
                        paid={k: round(v, 2) for k, v in sorted(paid.get(gid, {}).items())})
    season.am_support_seasons[year] = out
    season.am_support_held[year] = {gid: c['band'] for gid, c in out.items()}
    return out
