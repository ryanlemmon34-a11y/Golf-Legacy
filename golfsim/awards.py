"""Trophies: the championships a golfer has won, from the world's recorded results only (read only).

`QualificationContext.results[(series_id, year)]` keeps every edition's winner for good (`Season.prune_history`
trims older results to their winners), so a trophy and its engraving come straight from what was played in this
world: nothing is created, rewritten or inferred. Trophy events:

* `major`   -- the four majors (series kind 'major');
* `college` -- College National Championship, Small College National Championship, World University Championship;
* `amateur` -- the elite amateur championships and the national amateur championships.

Qualifiers, regionals, conference events and multi-site events are not trophies. One winner per edition (playoffs
decide ties); an edition without exactly one recorded winner gives no trophy.
"""
from __future__ import annotations

COLLEGE_TROPHIES = ('COLLEGE_NATIONAL_CHAMPIONSHIP', 'SMALL_COLLEGE_CHAMPIONSHIP', 'INTL_UNIVERSITY_CHAMPIONSHIP')


def trophy_kind(series):
    """'major' | 'college' | 'amateur' | None for a series."""
    if series.kind == 'major':
        return 'major'
    if series.series_id in COLLEGE_TROPHIES:
        return 'college'
    if series.category in ('elite_amateur', 'national_amateur'):
        return 'amateur'
    return None


def _winner(sites):
    if len(sites) != 1:
        return None
    rows = next(iter(sites.values()))
    first = [gid for gid, pos in rows if pos == 1]
    return first[0] if len(first) == 1 else None


def winners(season):
    """{(series_id, year): winner id} for every recorded trophy edition, in date order."""
    by = season.cal.by_id
    out = {}
    for (sid, y), sites in sorted(season.ctx.results.items(), key=lambda kv: (kv[0][1], by[kv[0][0]].week
                                                                                 if kv[0][0] in by else 0, kv[0][0])):
        s = by.get(sid)
        if s is None or trophy_kind(s) is None:
            continue
        w = _winner(sites)
        if w is not None:
            out[(sid, y)] = w
    return out


def _name(season, gid):
    g = season.g.get(gid)
    return g.name if g is not None else None


def trophies(season, gid, career=None):
    """The trophies golfer `gid` has won, oldest first: [{event_id, series_id, event_name, year, winner_id,
    winner_name, kind, times_won, during_control}]. `during_control` is None without a career."""
    from . import event_labels as EL
    by = season.cal.by_id
    out, count = [], {}
    for (sid, y), w in winners(season).items():
        if w != gid:
            continue
        count[sid] = count.get(sid, 0) + 1
        s = by[sid]
        ctl = None
        if career is not None:
            ctl = career.controlled_at(y, s.week) == gid
        out.append({'event_id': f'{y}:{sid}', 'series_id': sid, 'event_name': EL.label(season.cal, sid), 'year': y,
                    'winner_id': gid, 'winner_name': _name(season, gid), 'kind': trophy_kind(s),
                    'times_won': count[sid], 'during_control': ctl})
    return out


def engraving(season, series_id):
    """Every recorded winner of one trophy in this world, oldest first: [{year, winner_id, winner_name}] ([] for a
    series that is not a trophy or has no recorded edition)."""
    return [{'year': y, 'winner_id': w, 'winner_name': _name(season, w)}
            for (sid, y), w in winners(season).items() if sid == series_id]
