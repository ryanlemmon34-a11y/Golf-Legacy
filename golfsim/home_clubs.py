"""Home clubs: the local course each golfer belongs to where they live (rules 2026-11-08;
the owner's decision on unused local courses; docs/FAMILIARITY_AND_AGGRESSION.md).

A golfer's home club is a course in the state / province (or equivalent) they live in: a municipal course
there if there is one (the local, public courses most golf is played on), else any course there that is not
an elite championship venue; where the state / province has none or is unknown, the same choice within the
country (basis 'country'). The pick among candidates is a stable draw per golfer and place, so it is
reproducible and does not depend on the order people are processed. It is recorded with its date and kept
while they live in the same place; a move to another place gives a new home club, recorded as a new entry.

What it does: the home club takes part in the existing familiarity mechanism only, as the regional baseline
(familiarity.REGION_ROUNDS) for that one course -- which a home club in their own state / province already
has. So it adds something only where the club had to be found by country, and even then it is the same
floor, taken once (the larger of rounds played, the regional baseline and the home-club floor; never a sum).
There is no separate home advantage and no practice-round count.
"""
from __future__ import annotations

import hashlib

from .course_library import course_place


def _h(*parts):
    return int.from_bytes(hashlib.blake2b(':'.join(map(str, parts)).encode(), digest_size=8).digest(), 'big')


def club_index(lib):
    """{'region': {(country, subdivision): ([municipal], [other non-elite])}, 'country': {country: (...)}},
    course ids sorted, from a library's sites (or a {cid: site} dict)."""
    sites = getattr(lib, 'sites', lib)
    region, country = {}, {}
    for cid in sorted(sites):
        site = sites[cid]
        cls = site.get('cls', site.get('class'))
        if cls == 'elite':
            continue
        place = course_place(site)
        k = 0 if cls == 'municipal' else 1
        if place[0]:
            country.setdefault(place[0], ([], []))[k].append(cid)
            if place[1]:
                region.setdefault(place, ([], []))[k].append(cid)
    return {'region': region, 'country': country}


def pick(index, seed, gid, place):
    """(course id, basis) of a home club for a person living at `place` ((country, subdivision or None)):
    basis 'region' (in their state / province) or 'country'; (None, None) where the country has no course."""
    if not place or not place[0]:
        return None, None
    for basis, pool in (('region', index['region'].get(tuple(place)) if place[1] else None),
                        ('country', index['country'].get(place[0]))):
        if not pool:
            continue
        cands = pool[0] or pool[1]
        if cands:
            return cands[_h(seed, 'homeclub', gid, place[0], place[1]) % len(cands)], basis
    return None, None


def current(season, gid):
    """The course id of a golfer's home club now, or None."""
    rows = getattr(season, 'home_clubs', {}).get(gid)
    return rows[-1][2] if rows else None


def familiarity_at_club(season, g):
    """A golfer's familiarity at their current home club, explicitly (never inferred from a top-ten list):
    {'course', 'rounds' (competitive rounds actually played there), 'engine_rounds' (what the engine is given:
    the larger of those and the regional / home-club floor), 'value' (1 - exp(-engine_rounds / 15)), 'from'
    ('played', 'region', 'country' or 'home club')}; None without a home club."""
    from . import familiarity as FAM
    cid = current(season, g.id)
    if cid is None:
        return None
    rounds = float(g.familiarity.get(cid, 0.0))
    eff, src = FAM.engine_rounds(rounds, season.course_baseline(g.id, cid))
    return {'course': cid, 'rounds': round(rounds, 1), 'engine_rounds': round(eff, 2),
            'value': round(FAM.value(eff), 4), 'from': src}


def assign(season, year, week):
    """Give every golfer whose residence is recorded a home club where they live, recording a new dated entry
    only when they have none or have moved since (their club's place differs from where they live)."""
    P = season.places
    book = season.__dict__.setdefault('home_clubs', {})
    index = None
    for g in season.world.golfers:
        if g.id in P.legacy or not P.known(g.id):
            continue
        home = P.home[g.id]
        rows = book.get(g.id)
        if rows and tuple(rows[-1][4]) == tuple(home):
            continue
        if index is None:
            index = club_index(season.lib)
        cid, basis = pick(index, season.seed, g.id, home)
        if (rows[-1][2] if rows else None) == cid:
            continue                                 # (the same club, or still none)
        book.setdefault(g.id, []).append([year, week, cid, basis, list(home)])   # (None: no course where they live)
