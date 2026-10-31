"""Death after retirement (roadmap C2; owner decision D6; rules 2026-11-07).

Who can die
    Everyone except an active competitive golfer (a golfer whose lifestyle is not 'retired'). A golfer
    who retired from competition can die, whether or not they went on to coach or caddie; so can staff
    who never played in this world, working or retired. One person is one person id (a former golfer
    who coaches or caddies keeps their golfer id: staff.Staff.from_golfer), so a death is recorded once
    and applies to every record of that person.

When
    One consistent processing date: the winter after each season (week 53), once per season, after the
    season's career decisions, the staff's retirements and the ending of departed people's relationships,
    and before outside recruits arrive (staff.end_of_season). A death is recorded as (Y, 53) -- "in the
    winter after season Y" -- with the age then (Y - birth year, the same approximate age the world uses
    everywhere) frozen. No week is ever drawn inside a completed season, so no death is dated before
    anything the person did that season, and nobody dies before the world's first season has ended.

How likely
    PROVISIONAL GAME CALIBRATION, not a validated demographic fact: an annual risk
        q(age) = 0.0005 + 0.000041 * exp(0.09 * age), at most 0.5 a year
    (about 0.9 % at 60, 2.2 % at 70, 5.5 % at 80, 13.5 % at 90, 33 % at 100). The same for every nation.

Reproducible and idempotent
    Each person's draw is a hash of (world seed, season, person id) -- its own stream, so no other random
    draw in the season moves, and the outcome does not depend on the order people are visited or on a
    save and resume. A season is processed at most once (season.mortality_done), so running the winter
    twice never kills twice.

What a death changes
    The person is recorded in season.deaths ({person: {year, week, age, roles}}); a working coach's or
    caddie's open partnerships end through the ordinary stint mechanism (end_coach / end_caddie) with the
    reason recorded at (Y, 53); their staff records stop working (status 'deceased'). Nothing is deleted:
    results, records, relationships, profiles and links stay as they were.

Old people
    Fresh worlds only: a world saved before this rule never processes deaths (no migration). People who are
    already old when a world begins are processed from its first season's end; no past death is invented.
"""
from __future__ import annotations

import hashlib
import math

from . import decision_evidence as DE

Q_BASE, Q_SCALE, Q_RATE, Q_CAP = 0.0005, 0.000041, 0.09, 0.5
WEEK = 53                                          # the winter after the season
DECEASED = 'deceased'                              # a staff record's status once the person has died


def annual_risk(age):
    """The chance of dying in the winter after a season at this age (provisional game calibration)."""
    return min(Q_CAP, Q_BASE + Q_SCALE * math.exp(Q_RATE * age))


def draw(seed, year, pid):
    """A uniform number in [0, 1) for this person this winter: a hash of (seed, year, person), never a
    shared random stream."""
    h = hashlib.blake2b(f'{seed}:death:{year}:{pid}'.encode(), digest_size=8).digest()
    return int.from_bytes(h, 'big') / 2 ** 64


def death_text(year, age):
    return f'Died in the winter after season {year}, aged {age}'


def people(season):
    """{person id: {'born', 'golfer', 'coach', 'caddie'}}: every record of each person in the world."""
    st = season.staff
    out = {}
    for g in season.world.golfers:
        out.setdefault(g.id, {'born': g.born, 'golfer': None, 'coach': None, 'caddie': None})['golfer'] = g
    for kind, table in (('coach', st.coaches), ('caddie', st.caddies)):
        for p in table.values():
            rec = out.setdefault(p.id, {'born': p.born, 'golfer': None, 'coach': None, 'caddie': None})
            rec[kind] = p
            rec['born'] = rec['born'] or p.born
    return out


def eligible(rec):
    """Whether a person can die: never an active competitive golfer; nobody whose birth year is unknown."""
    g = rec['golfer']
    if g is not None and g.lifestyle != 'retired':
        return False
    return bool(rec['born'])


def winter(season, year):
    """Process the winter after season `year` (at most once). Returns the deaths recorded now, as
    [(person id, record)]."""
    if not getattr(season, 'mortality_on', False):
        return []
    done = season.mortality_done
    if year in done:
        return []
    done.add(year)
    deaths = season.deaths
    st = season.staff
    when = (year, WEEK)
    out = []
    book = season.mortality_ev[year] if getattr(season, 'record_decisions', False) else None   # decision evidence
    for pid, rec in sorted(people(season).items()):
        if pid in deaths or not eligible(rec):
            continue
        age = year - rec['born']
        u, q = draw(season.seed, year, pid), annual_risk(age)
        if book is not None:
            DE.record_mortality(book, pid, age, q, u)
        if u >= q:
            continue
        roles = [k for k in ('golfer', 'coach', 'caddie') if rec[k] is not None]
        entry = {'year': year, 'week': WEEK, 'age': age, 'roles': roles}
        deaths[pid] = entry
        text = death_text(year, age)
        if rec['coach'] is not None:
            for gid in sorted(g for g, c in st.coach_of.items() if c == pid):
                st.end_coach(season, gid, when, 'coach died', 'death')
        if rec['caddie'] is not None:
            for gid in sorted(g for g, k in st.caddie_of.items() if k == pid):
                st.end_caddie(season, gid, when, 'caddie died', 'death')
        for kind in ('coach', 'caddie'):
            person = rec[kind]
            if person is not None:
                person.status = DECEASED
                person.history.append((year, text))
        if rec['golfer'] is not None:
            season.log(pid, year, WEEK, text)
        out.append((pid, entry))
    return out


def died(season, pid):
    """The recorded death of a person ({year, week, age, roles}), or None."""
    return getattr(season, 'deaths', {}).get(pid)
