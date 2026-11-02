"""Headroom study (experiment only; nothing here changes the game). Library for run.py. Extends the reviewed
starting-ability study's library (build/v17-readiness-study 5c7dce9, docs/review/readiness/study/study.py) with the
headroom arms of PLAN.md; everything the reviewed study validated (the candidate-aligned replay, the paired layer, the
projection) is unchanged.

Headroom arms (PLAN.md): the tempo T used in the YOUTH deficit only is a smooth (C1), monotone transform of the
unchanged peak-age draw p -- identity for p >= K, slope s below K - w, a quadratic blend between (readiness_knee).
Decline keeps p. The same T serves the new professionals' age-18 tracking check and their entry. B1/B2/B2c keep each
candidate's A0 stored-potential target (isolation); B2p stores potential by the production rule (the inherited
promotion effect). Scouting and status decisions see only the observable entry overall, as in production.

    B1   mild        K 24.5, w 2, s 0.5     raw potential before the cap (A0's order)   A0 target kept
    B2   stronger    K 25.5, w 2, s 0.3     raw potential before the cap                A0 target kept
    B2c  B2 + cap order (explicit combination)                                          A0 target kept
    B2p  B2 with the production potential-storage rule

The reviewed study's description follows.


Four ways of drawing how ready a new golfer is (their *readiness tempo*), everything else as coded:

    A0  no change (baseline)       readiness = the peak-age draw; raw potential before the 99 cap
    A1  cap order only             as A0, with potential capped at 99 *before* the youth deficit is subtracted
    A2  independent readiness      readiness tempo = 27 + 2 e (e ~ N(0, 1), keyed by the candidate); the peak-age
                                   draw keeps setting decline only
    A3  weakly correlated tempo    readiness tempo = 27 + 2 (rho z + sqrt(1 - rho^2) e), z = (peak - 27) / 2:
                                   the peak-age draw is the fixed input (its distribution unchanged), rho = 0.3
    A3r5 (sensitivity)             A3 with rho = 0.5

What the arms can and cannot do: A2, A3 and A3r5 keep the readiness tempo's distribution N(27, 2) (the peak-age
draw's own), so they cannot by themselves lower juniors' starting overall or how often a near-finished teenager is
generated: they change WHO is precocious (readiness no longer, or only weakly, the same draw as decline) and so how
early readiness goes with early decline. A1 changes only candidates whose raw potential is above 99.

Every arm keeps the readiness tempo's distribution N(27, 2) -- the peak-age draw's own -- and keeps the growth law
(development.develop_week), the decline law (development.age_year), the scouts' rule (population._keep_young, which
projects with a typical peak of 27), the status and sampling rules and every parameter unchanged. The youth deficit
uses the readiness tempo; the old-age part of the deficit and all later decline use the peak-age draw.

Two layers:

  replay  Test2's production random streams (`{seed}:juniors:{year}:{country}`, `{seed}:new-pros:...`), consumed
          exactly as population._junior_draw / _new_pro_draw consume them: candidate d is production's draw d, with
          every value production drew for it (potential, peak, aging, luck, the scouts' coin and noise, age, status
          and sampling coins). An arm changes only how those values are combined. Values production never drew for
          a candidate (a coin an arm can need when production stopped earlier) and the readiness noise e come from
          generators keyed by that candidate alone, so nothing an arm adds shifts another candidate or the production
          stream. Each nation's entrants are the first k passers, k = Test2's RECORDED allocation (fixed: this layer
          does not recompute totals, shares or national prestige); A0 reproduces Test2's rows exactly.
  paired  the same candidates under every arm: each nation-year draws a fixed number of candidates (the existing
          rule's count) from a study stream that consumes the same number of values per candidate whatever happens
          (potential, peak, aging, luck, the scouts' coin and noise, the age and status coins; e from a generator
          keyed by the candidate), so candidate d is the same person under every arm and only the arm decides who
          passes. Selection is RECALCULATED: the existing rule's filter over its fixed candidate count (every passer,
          no allocation), so the pass count can differ by arm. Nation profiles are the starting ones (they never
          change in a world); shares, carry and national prestige are not modelled here.

Trajectories (bounded check): a selected entrant is built with the production builders (population._make_golfer,
development.init_ceilings) and developed week by week with the production development_week / age_year under a
fixed schedule (standard: 13 four-week blocks a year, each one tournament of four rounds, two training weeks in
the category choose_category picks and one rest week; light: one tournament, one training week, two rest weeks),
self-coached (coaching quality 0.3: no coach), no paid work, no injuries (so no permanent injury losses), no
retirement or quitting, full competitive experience, from entry to 40. The schedule is the same for every arm, so
differences come from the entry draw alone. A projection is a bounded check of the development laws on these
entrants, not a reproduction of any realized career (real careers differ in schedule, coaching, injuries, money,
access to events and retirement).
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
    knee: tuple | None = None                    # (K, w, s): headroom arms (readiness_knee)
    keep_target: bool = False                    # store A0's potential target (isolation) instead of the production rule


ARMS = {a.name: a for a in (
    Arm('A0', False, None, 'no change (baseline)'),
    Arm('A1', True, None, 'cap order corrected only'),
    Arm('A2', False, 0.0, 'independent readiness'),
    Arm('A3', False, 0.3, 'weakly correlated tempo (rho 0.3)'),
    Arm('A3r5', False, 0.5, 'correlated tempo, sensitivity (rho 0.5)'),
    Arm('B1', False, None, 'headroom mild (K 24.5, w 2, s 0.5)', (24.5, 2.0, 0.5), True),
    Arm('B2', False, None, 'headroom stronger (K 25.5, w 2, s 0.3)', (25.5, 2.0, 0.3), True),
    Arm('B2c', True, None, 'B2 + cap order (explicit combination)', (25.5, 2.0, 0.3), True),
    Arm('B2p', False, None, 'B2, production potential storage (promotion effect)', (25.5, 2.0, 0.3), False),
)}
HEADROOM_ARMS = ('B1', 'B2', 'B2c', 'B2p')
IDENTITY = Arm('A3r1', False, 1.0, 'identity check: rho 1 must equal A0')


def readiness_knee(p, K, w, s):
    """The headroom arms' tempo for the youth deficit: identity for p >= K; slope s for p < K - w; between them a
    quadratic blend whose slope runs linearly from s to 1, so T is continuous with a continuous slope (C1), monotone,
    and T >= p everywhere."""
    if p >= K:
        return p
    if p >= K - w:
        return K - (s * (K - p) + (1.0 - s) / (2.0 * w) * (w * w - (p - K + w) ** 2))
    return K - (1.0 - s) * w / 2.0 - s * (K - p)


def tempo(arm, peak, eps):
    if arm.knee is not None:
        return readiness_knee(peak, *arm.knee)
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


# ---- replay layer: the production streams, each candidate's values recorded as production draws them -------------

class _Proxy:
    """Records the club-professional coin population._status draws (only in that branch), from the production
    stream."""

    def __init__(self, rng):
        self.rng, self.u = rng, None

    def random(self):
        self.u = self.rng.random()
        return self.u


def production_values(kind, crng, prof):
    """One production draw (population._junior_draw / _new_pro_draw), consumed exactly as production consumes it:
    {label: value} for every value production drew for this candidate (only those), and the production row."""
    mu = P._mu(prof)
    v = {'pot': crng.gauss(mu, P.POTENTIAL_SD), 'peak': crng.gauss(27.0, 2.0)}
    v['aging'] = math.exp(crng.gauss(0, 0.3))
    v['luck'] = crng.gauss(0, P.CAREER_LUCK_SD)
    pot, peak, aging, luck = v['pot'], v['peak'], v['aging'], v['luck']
    if kind == 'juniors':
        cur = pot - P.age_deficit(18, peak, aging) + luck
        if cur < P.KEEP_OVERALL:
            return v, None
        cur = min(cur, 99.0)
        v['u_keep'], v['scout'] = crng.random(), crng.gauss(0, P.SCOUTING_SD)
        if P._keep_young(cur, 18, v['u_keep'], v['scout']):
            return v, ('', 18, max(min(pot, 99.0), cur), peak, cur, 'amateur', aging)
        return v, None
    v['age'] = age = crng.choice(P.NEW_PRO_AGES)
    cur18 = pot - P.age_deficit(18, peak, aging) + luck
    tracked = False
    if cur18 >= P.KEEP_OVERALL:
        v['u_keep'], v['scout'] = crng.random(), crng.gauss(0, P.SCOUTING_SD)
        tracked = P._keep_young(cur18, 18, v['u_keep'], v['scout'])
    cur = pot - P.age_deficit(age, peak, aging) + luck
    if tracked or cur < P.KEEP_OVERALL:
        return v, None
    cur = min(cur, 99.0)
    v['u_status'] = crng.random()
    proxy = _Proxy(crng)
    status = P._status(max(age, 23), cur, prof, v['u_status'], proxy)
    if proxy.u is not None:
        v['u_club'] = proxy.u
    if status != 'pro':
        return v, None
    v['u_sample'] = crng.random()
    if v['u_sample'] < P._keep_probability('pro', age, cur):
        return v, ('', age, max(min(pot, 99.0), cur), peak, cur, 'pro', aging)
    return v, None


def candidate_tuple(kind, v, key):
    """The candidate as every arm sees it: production's values where production drew them; any value production
    did not draw for this candidate (an arm may need a coin production never reached) and the readiness noise e
    from generators keyed by the candidate alone (`{key}:aux`, `{key}:readiness`), drawn in a fixed order. Nothing
    an arm adds can move another candidate's values or the production stream."""
    aux = random.Random(f'{key}:aux')
    fill = {'u_keep': aux.random(), 'scout': aux.gauss(0, P.SCOUTING_SD), 'u_status': aux.random(),
            'u_club': aux.random(), 'u_sample': aux.random()}
    eps = random.Random(f'{key}:readiness').gauss(0.0, 1.0)
    g = lambda k: v[k] if k in v else fill[k]
    return (v['pot'], v['peak'], v['aging'], v['luck'], eps, g('u_keep'), g('scout'), v.get('age', 18),
            g('u_status'), g('u_club'), g('u_sample'))


class ReplayStream:
    """A nation's production stream for one pathway and year, as candidates: candidate d is production's draw d
    (the same values under every arm). `production` keeps the production row of each draw, for the identity
    check."""

    def __init__(self, kind, year, seed, country):
        tag = 'juniors' if kind == 'juniors' else 'new-pros'
        self.kind, self.country, self.prof = kind, country, NATIONS[country]
        self.crng = random.Random(f'{seed}:{tag}:{year}:{country}')
        self.keybase = f'{seed}:{tag}:{year}:{country}'
        self.cands, self.production = [], []

    def get(self, d):
        while len(self.cands) <= d:
            v, row = production_values(self.kind, self.crng, self.prof)
            n = len(self.cands)
            self.cands.append(candidate_tuple(self.kind, v, f'{self.keybase}:{n}'))
            self.production.append(None if row is None else (self.country,) + row[1:])
        return self.cands[d]


def replay_entrants(stream, k, arm, need):
    """Under an arm: the first k passers of the stream (the recorded allocation), and the outcome of each of the
    existing rule's `need` candidates (for the recalculated pass counts). Returns (entrants, outcomes):
    entrants [(d, row, facts)], outcomes [(d, stage, facts)] for d < need."""
    entrants, outcomes, d = [], [], 0
    while d < need or len(entrants) < k:
        stage, row, f = paired_outcome(stream.kind, stream.get(d), stream.country, arm)
        if d < need:
            outcomes.append((d, stage, f))
        if row is not None and len(entrants) < k:
            entrants.append((d, row, f))
        d += 1
    return entrants, outcomes


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
    for d in range(n):
        pot = rng.gauss(mu, P.POTENTIAL_SD)
        peak = rng.gauss(27.0, 2.0)
        aging = math.exp(rng.gauss(0, 0.3))
        luck = rng.gauss(0, P.CAREER_LUCK_SD)
        eps = random.Random(f'{seed}:paired:{kind}:{year}:{country}:{d}:readiness').gauss(0.0, 1.0)
        u_keep, scout = rng.random(), rng.gauss(0, P.SCOUTING_SD)
        age = rng.choice(P.NEW_PRO_AGES) if kind == 'new_pros' else 18
        u_status, u_club, u_sample = rng.random(), rng.random(), rng.random()
        out.append((pot, peak, aging, luck, eps, u_keep, scout, age, u_status, u_club, u_sample))
    return out


def a0_target(kind, cand):
    """The candidate's stored potential under A0 (production: max(capped raw potential, entry overall)); the
    headroom arms with keep_target store this, so eventual potential does not change with the arm."""
    pot, peak, aging, luck = cand[:4]
    a = 18 if kind == 'juniors' else cand[7]
    return max(min(pot, 99.0), min(pot - deficit(a, peak, peak, aging) + luck, 99.0))


def _stored(kind, cand, arm, cur, f):
    prod = max(min(cand[0], 99.0), cur)              # the production rule applied to this arm's entry
    f['pot_s_prod'] = prod
    if arm.keep_target:
        f['target'] = a0_target(kind, cand)
        return max(f['target'], cur)
    return prod


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
            return 'kept', (country, 18, _stored(kind, cand, arm, cur, f), peak, cur, 'amateur', aging), f
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
        return 'kept', (country, age, _stored(kind, cand, arm, cur, f), peak, cur, 'pro', aging), f
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


CATS = ('physical', 'long_game', 'short_game', 'putting', 'mental')


def category_profile(values):
    """Mean of a golfer's attribute values (or ceilings) per development category."""
    return [round(sum(values[k] for k in D.CATEGORIES[c]) / len(D.CATEGORIES[c]), 3) for c in CATS]


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
