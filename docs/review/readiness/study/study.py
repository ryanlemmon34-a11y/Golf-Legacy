"""Starting-ability study (experiment only; nothing here changes the game). Library for run.py.

Four ways of drawing how ready a new golfer is (their *readiness tempo*), everything else as coded:

    A0  no change (baseline)       readiness = the peak-age draw; raw potential before the 99 cap
    A1  cap order only             as A0, with potential capped at 99 *before* the youth deficit is subtracted
    A2  independent readiness      readiness tempo = 27 + 2 e (e ~ N(0, 1), its own stream); the peak-age draw
                                   keeps setting decline only
    A3  weakly correlated tempo    readiness tempo = 27 + 2 (rho z + sqrt(1 - rho^2) e), z = (peak - 27) / 2:
                                   the peak-age draw is the fixed input (its distribution unchanged), rho = 0.3
    A3r5 (sensitivity)             A3 with rho = 0.5

Every arm keeps the readiness tempo's distribution N(27, 2) -- the peak-age draw's own -- and keeps the growth law
(development.develop_week), the decline law (development.age_year), the scouts' rule (population._keep_young, which
projects with a typical peak of 27), the status and sampling rules and every parameter unchanged. The youth deficit
uses the readiness tempo; the old-age part of the deficit and all later decline use the peak-age draw.

Two layers:

  replay  the production random streams (`{seed}:juniors:{year}:{country}` and `{seed}:new-pros:...`) consumed
          exactly as population._junior_draw / _new_pro_draw consume them, each nation's entrants the first k
          passers of its stream (k = the allocation Test2 recorded; this is what entrant_rows produces when a
          nation's profile is unchanged, as it always is). A0 reproduces Test2's cohorts; the other arms are what an
          implementation of the arm would have generated from the same seed. The readiness noise e comes from its
          own stream (`{seed}:readiness:{pathway}:{year}:{country}`, one value per draw), so the production stream
          is untouched -- but a candidate whose drop/keep outcome changes consumes a different number of draws, so
          later candidates in that nation-year differ between arms (stream-level pairing, as a real change would).
  paired  the same candidates under every arm: each nation-year draws a fixed number of candidates (the existing
          rule's count) from a study stream that consumes the same number of values per candidate whatever happens
          (potential, peak, aging, luck, e, the scouts' coin and noise, the age and status coins), so candidate d is
          the same person under every arm and only the arm decides who passes. Selection is the existing rule's
          filter (every passer, not an allocation), so its total can differ by arm.

Trajectories (bounded check): a selected entrant is built with the production builders (population._make_golfer,
development.init_ceilings) and developed week by week with the production development_week / age_year under a
fixed standard schedule (13 four-week blocks a year: one tournament of four rounds, two training weeks in the
category choose_category picks, one rest week; self-coached, quality 0.3; no injuries, no quitting), from entry
to 40. The schedule is the same for every arm, so differences come from the entry draw alone.
"""
from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass

P = D = None                                   # golfsim.population / development, set by setup()
NATIONS = None


def setup(checkout):
    import sys
    global P, D, NATIONS
    sys.path.insert(0, checkout)
    from golfsim import development as _D
    from golfsim import population as _P
    from golfsim.nations import nations
    P, D, NATIONS = _P, _D, nations()


@dataclass(frozen=True)
class Arm:
    name: str
    cap_first: bool
    rho: float | None                            # None: readiness tempo = the peak-age draw (A0, A1)
    label: str


ARMS = {a.name: a for a in (
    Arm('A0', False, None, 'no change (baseline)'),
    Arm('A1', True, None, 'cap order corrected only'),
    Arm('A2', False, 0.0, 'independent readiness'),
    Arm('A3', False, 0.3, 'weakly correlated tempo (rho 0.3)'),
    Arm('A3r5', False, 0.5, 'correlated tempo, sensitivity (rho 0.5)'),
)}
IDENTITY = Arm('A3r1', False, 1.0, 'identity check: rho 1 must equal A0')


def tempo(arm, peak, eps):
    if arm.rho is None:
        return peak
    if arm.rho == 1.0:
        return peak
    return 27.0 + 2.0 * (arm.rho * (peak - 27.0) / 2.0 + math.sqrt(1.0 - arm.rho * arm.rho) * eps)


def deficit(age, t, peak, aging):
    """population.age_deficit with the youth part from the readiness tempo t and the old part from the peak-age
    draw (the same arithmetic in the same order: with t == peak it is age_deficit bit for bit)."""
    young = max(0.0, t - age)
    grow = 0.36 * young ** 1.55
    old = max(0.0, age - (peak + 7))
    decline = 0.15 * aging * old ** 1.6
    return grow + decline


# ---- replay layer: the production streams, consumed exactly as production consumes them ---------------------------

def junior_draw(crng, rr, country, mu, arm):
    """population._junior_draw under an arm: (row or None, facts). rr: the readiness stream (one value a draw)."""
    pot = crng.gauss(mu, P.POTENTIAL_SD)
    peak = crng.gauss(27.0, 2.0)
    aging = math.exp(crng.gauss(0, 0.3))
    eps = rr.gauss(0.0, 1.0)
    t = tempo(arm, peak, eps)
    base = min(pot, 99.0) if arm.cap_first else pot
    cur = base - deficit(18, t, peak, aging) + crng.gauss(0, P.CAREER_LUCK_SD)
    f = {'pot': pot, 'peak': peak, 'aging': aging, 'tempo': t, 'cur18': cur, 'age': 18}
    if cur < P.KEEP_OVERALL:
        f['stage'] = 'below_keep'
        return None, f
    cur = min(cur, 99.0)
    pot_s = max(min(pot, 99.0), cur)
    if P._keep_young(cur, 18, crng.random(), crng.gauss(0, P.SCOUTING_SD)):
        f['stage'] = 'kept'
        return (country, 18, pot_s, peak, cur, 'amateur', aging), f
    f['stage'] = 'scouted_out'
    return None, f


def new_pro_draw(crng, rr, country, mu, prof, arm):
    """population._new_pro_draw under an arm."""
    pot = crng.gauss(mu, P.POTENTIAL_SD)
    peak = crng.gauss(27.0, 2.0)
    aging = math.exp(crng.gauss(0, 0.3))
    luck = crng.gauss(0, P.CAREER_LUCK_SD)
    age = crng.choice(P.NEW_PRO_AGES)
    eps = rr.gauss(0.0, 1.0)
    t = tempo(arm, peak, eps)
    base = min(pot, 99.0) if arm.cap_first else pot
    cur18 = base - deficit(18, t, peak, aging) + luck
    tracked = cur18 >= P.KEEP_OVERALL and P._keep_young(cur18, 18, crng.random(), crng.gauss(0, P.SCOUTING_SD))
    cur = base - deficit(age, t, peak, aging) + luck
    f = {'pot': pot, 'peak': peak, 'aging': aging, 'tempo': t, 'cur18': cur18, 'cur': cur, 'age': age}
    if tracked or cur < P.KEEP_OVERALL:
        f['stage'] = 'tracked_as_junior' if tracked else 'below_keep'
        return None, f
    cur = min(cur, 99.0)
    pot_s = max(min(pot, 99.0), cur)
    if P._status(max(age, 23), cur, prof, crng.random(), crng) != 'pro':
        f['stage'] = 'not_pro'
        return None, f
    if crng.random() < P._keep_probability('pro', age, cur):
        f['stage'] = 'kept'
        return (country, age, pot_s, peak, cur, 'pro', aging), f
    f['stage'] = 'sampled_out'
    return None, f


def replay_cohort(kind, year, seed, country, k, arm):
    """The first k passers of a nation's production stream under an arm, and the facts of every draw consumed
    (the existing rule's own _cand_n draws at least, as entrant_rows consumes them)."""
    prof = NATIONS[country]
    tag = 'juniors' if kind == 'juniors' else 'new-pros'
    crng = random.Random(f'{seed}:{tag}:{year}:{country}')
    rr = random.Random(f'{seed}:readiness:{tag}:{year}:{country}')
    mu = P._mu(prof)
    need = P._cand_n(kind, prof)
    rows, facts, d = [], [], 0
    while d < need or len(rows) < k:
        if kind == 'juniors':
            row, f = junior_draw(crng, rr, country, mu, arm)
        else:
            row, f = new_pro_draw(crng, rr, country, mu, prof, arm)
        f['d'] = d
        f['in_existing_rule'] = d < need
        if row is not None:
            f['passer'] = len(rows)
            f['entered'] = len(rows) < k
            rows.append((row, f))
        facts.append(f)
        d += 1
    return rows[:k], facts


# ---- paired layer: the same candidates under every arm -------------------------------------------------------------

class _Fixed:
    """A stand-in rng for population._status's club-professional coin (pre-drawn, so consumption is fixed)."""

    def __init__(self, u):
        self.u = u

    def random(self):
        return self.u


def paired_candidates(kind, year, seed, country):
    """The nation-year's candidates for the paired layer: tuples of every value any arm can need, drawn in a fixed
    order from `{seed}:paired:{pathway}:{year}:{country}` (one candidate always consumes the same values)."""
    prof = NATIONS[country]
    n = P._cand_n(kind, prof)
    rng = random.Random(f'{seed}:paired:{kind}:{year}:{country}')
    mu = P._mu(prof)
    out = []
    for _ in range(n):
        pot = rng.gauss(mu, P.POTENTIAL_SD)
        peak = rng.gauss(27.0, 2.0)
        aging = math.exp(rng.gauss(0, 0.3))
        luck = rng.gauss(0, P.CAREER_LUCK_SD)
        eps = rng.gauss(0.0, 1.0)
        u_keep, scout = rng.random(), rng.gauss(0, P.SCOUTING_SD)
        age = rng.choice(P.NEW_PRO_AGES) if kind == 'new_pros' else 18
        u_status, u_club, u_sample = rng.random(), rng.random(), rng.random()
        out.append((pot, peak, aging, luck, eps, u_keep, scout, age, u_status, u_club, u_sample))
    return out


def paired_outcome(kind, cand, country, arm):
    """(stage, row-or-None, facts) of one paired candidate under an arm, by the production filters."""
    pot, peak, aging, luck, eps, u_keep, scout, age, u_status, u_club, u_sample = cand
    t = tempo(arm, peak, eps)
    base = min(pot, 99.0) if arm.cap_first else pot
    cur18 = base - deficit(18, t, peak, aging) + luck
    f = {'pot': pot, 'peak': peak, 'aging': aging, 'tempo': t, 'cur18': cur18, 'age': age}
    if kind == 'juniors':
        if cur18 < P.KEEP_OVERALL:
            return 'below_keep', None, f
        cur = min(cur18, 99.0)
        if P._keep_young(cur, 18, u_keep, scout):
            return 'kept', (country, 18, max(min(pot, 99.0), cur), peak, cur, 'amateur', aging), f
        return 'scouted_out', None, f
    tracked = cur18 >= P.KEEP_OVERALL and P._keep_young(cur18, 18, u_keep, scout)
    cur = base - deficit(age, t, peak, aging) + luck
    f['cur'] = cur
    if tracked:
        return 'tracked_as_junior', None, f
    if cur < P.KEEP_OVERALL:
        return 'below_keep', None, f
    cur = min(cur, 99.0)
    if P._status(max(age, 23), cur, NATIONS[country], u_status, _Fixed(u_club)) != 'pro':
        return 'not_pro', None, f
    if u_sample < P._keep_probability('pro', age, cur):
        return 'kept', (country, age, max(min(pot, 99.0), cur), peak, cur, 'pro', aging), f
    return 'sampled_out', None, f


# ---- trajectories ---------------------------------------------------------------------------------------------------

SCHEDULES = {
    # per four-week block (13 a year): activities in order; 'play' = a four-round tournament
    'standard': ('play', 'train', 'train', 'rest'),
    'light': ('play', 'train', 'rest', 'rest'),
}
AGES = (18, 21, 25, 30, 35, 40)


def study_id(*parts):
    return int(hashlib.sha1(':'.join(map(str, parts)).encode()).hexdigest()[:12], 16)


def build(row, gid, key):
    """A golfer from an entrant row with the production builders; personality and attribute noise keyed by the
    candidate (`key`), not by the arm, so the same candidate keeps them under every arm."""
    g = P._make_golfer(gid, row, 0, key, NATIONS, set())
    D.init_ceilings(g, row[1], random.Random(f'{key}:ceilings'))
    return g


def project(g, entry_age, key, schedule='standard', to_age=40):
    """Overall at each age from entry to `to_age` (index by age), under the standard schedule."""
    rng = random.Random(f'{key}:develop')
    block = SCHEDULES[schedule]
    rounds_a_year = 4 * 13 * block.count('play')
    exp = D.experience_factor(rounds_a_year)
    out = {entry_age: g.overall}
    for age in range(entry_age, to_age):
        for _ in range(13):
            cat = None
            for act in block:
                if act == 'train':
                    if cat is None:
                        cat = D.choose_category(g, rng)
                    D.develop_week(g, 'train', age, cat, 0.0, coach=0.3, experience=exp, gain=False)
                elif act == 'play':
                    D.develop_week(g, 'play', age, None, 4.0, gain=False)
                else:
                    D.develop_week(g, 'rest', age, gain=False)
        D.age_year(g, age + 1, rng, exp)
        out[age + 1] = g.overall
    return out
