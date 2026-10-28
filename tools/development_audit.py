"""Development and caddie audit: what coaches, caddies and the development rules actually do.

    python tools/development_audit.py            -> reports/DEVELOPMENT_AUDIT.md

1. One season of development by coaching (none, ordinary coach, strong specialist, youth specialist)
   across ages and distances from potential, under the previous training mapping (an uncoached golfer
   trained at 0.88) and the current one (uncoached = 1.0, the calibrated baseline; coaches add to it).
2. Caddies in actual scoring: own bag, ordinary and strong caddies, with and without pressure and
   course familiarity (common random numbers, so differences are not noise).
3. Lifecycle invariants over 25 simulated years for a sample of golfers: ceilings and the 99 cap never
   exceeded, plateauing near the ceiling, late (mental) improvement, aging, serious injuries, and
   physical maturation of teenagers during rest and work weeks (and none for adults).

Debug report: it reads hidden attributes (ceilings, potential) on purpose.
"""
from __future__ import annotations

import copy
import random
import statistics as S
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import development as D                                 # noqa: E402
from golfsim import staff as ST                                      # noqa: E402
from golfsim.course import ashford_ridge                             # noqa: E402
from golfsim.engine import play_round                                # noqa: E402
from golfsim.golfer import CADDIE_SKILLS, Caddie, uniform_golfer     # noqa: E402
from golfsim.population import generate_world                        # noqa: E402

OLD = lambda q: 0.7 + 0.6 * q                                        # the mapping in 98b483d
NEW = D.coach_multiplier


def sample(world, age, gap, n, seed):
    pool = [g for g in world.golfers if g.age(world.year) == age and g.overall < 85]
    rng = random.Random(seed)
    out = []
    for g in rng.sample(pool, min(n, len(pool))):
        g = copy.deepcopy(g)
        g.potential = min(99.0, g.overall + gap)
        D.init_ceilings(g, age, random.Random(g.id))
        out.append(g)
    return out


def one_season(g, age, coach, mapping):
    """20 tournaments, 26 training weeks, 6 rest weeks, with the given coach (or none)."""
    st = ST.Staff()
    if coach:
        c = st.new_coach(random.Random(0), 'USA', 2027, 45, coach['teaching'], 50,
                         coach.get('speciality') or D.choose_category(g, random.Random(1)), coach.get('youth', False),
                         50, 'audit')
        st.coach_of[g.id] = c.id
    D.coach_multiplier = mapping
    before = g.overall
    rng = random.Random(g.id)
    for w in range(52):
        if w % 5 in (0, 2) and w < 50:
            D.develop_week(g, 'play', age, rounds=4)
        elif w % 9 == 8:
            D.develop_week(g, 'rest', age)
        else:
            cat = D.choose_category(g, rng, st.insight(g))
            D.develop_week(g, 'train', age, cat, coach=st.coaching(g, cat, age))
    D.coach_multiplier = NEW
    return g.overall - before


def coaching_table(world):
    scenarios = (('No coach', None), ('Ordinary coach (teaching 50)', {'teaching': 50}),
                 ('Strong specialist (teaching 80, their weakest area)', {'teaching': 80}),
                 ('Youth specialist (teaching 60)', {'teaching': 60, 'youth': True}))
    out = ['## 1. One season of development by coaching', '',
           'Average overall gained in one season (20 events, 26 training weeks, 6 rest) by 25 golfers per cell. '
           '"gap" = points below their potential at the start. Previous mapping (98b483d): training × (0.7 + 0.6 '
           '× quality), so an uncoached golfer trained at 0.88 of the calibrated rate. Current: × (1 + 0.5 × '
           'max(0, quality − 0.3)), so uncoached = 1.0 (the calibrated baseline) and coaches add to it.', '',
           '| Age | Gap | ' + ' | '.join(f'{n} (prev / now)' for n, _ in scenarios) + ' |',
           '|---|---|' + '---|' * len(scenarios)]
    for age in (18, 21, 25, 30, 35):
        for gap in (15, 7, 2):
            golfers = sample(world, age, gap, 25, age * 100 + gap)
            cells = []
            for _, coach in scenarios:
                old = S.mean(one_season(copy.deepcopy(g), age, coach, OLD) for g in golfers)
                new = S.mean(one_season(copy.deepcopy(g), age, coach, NEW) for g in golfers)
                cells.append(f'{old:+.2f} / {new:+.2f}')
            out.append(f'| {age} | {gap} | ' + ' | '.join(cells) + ' |')
    return out


def caddie_table():
    course = ashford_ridge()
    g = uniform_golfer(70)
    cads = (('Own bag', ST.self_caddie()), ('Ordinary caddie (55)', Caddie('o', {k: 55.0 for k in CADDIE_SKILLS})),
            ('Strong caddie (80)', Caddie('s', {k: 80.0 for k in CADDIE_SKILLS})))
    out = ['', '## 2. Caddies in actual scoring', '',
           'Mean score of an all-70 golfer over 600 rounds on Ashford Ridge (par 72), common random numbers. '
           '"Pressure" = a constant 0.6 pressure on every shot (contention); "familiar" = the caddie has worked '
           '40 rounds at the course (the player none).', '',
           '| Caddie | Normal | Under pressure | Familiar caddie |', '|---|---|---|---|']
    def mean(cad, pressure=None, n=600):
        return S.mean(play_round(g, course, random.Random(7_000_003 + i), caddie=cad,
                                 pressure_fn=(lambda h, s: pressure) if pressure else None).score for i in range(n))
    for name, cad in cads:
        fam = copy.deepcopy(cad)
        fam.familiarity[course.familiarity_key] = 40
        out.append(f'| {name} | {mean(cad):.2f} | {mean(cad, 0.6):.2f} | {mean(fam):.2f} |')
    return out


def lifecycle(world):
    rng = random.Random(5)
    golfers = [copy.deepcopy(g) for g in rng.sample([g for g in world.golfers if g.age(world.year) <= 24 and g.ceilings], 150)]
    over_ceiling = over_99 = 0
    by_age = {}
    plateau = []
    injuries = lasting = 0
    for year in range(25):
        for g in golfers:
            age = g.age(world.year + year)
            start = g.overall
            gap0 = sum(g.ceilings[k] - g.attrs[k] for k in g.attrs) / len(g.attrs)
            for w in range(52):
                act = 'play' if w % 5 in (0, 2) else 'rest' if w % 9 == 8 else 'train'
                cat = D.choose_category(g, rng)
                D.develop_week(g, act, age, cat, rounds=4 if act == 'play' else 0)
            if rng.random() < 0.04:
                injuries += 1
                lasting += bool(D.serious_injury(g, rng.choice((6, 12, 20)), rng))
            D.age_year(g, age + 1, rng, D.experience_factor(21 * 4))
            over_ceiling += sum(1 for k in g.attrs if g.attrs[k] > g.ceilings[k] + 1e-9)
            over_99 += sum(1 for k in g.attrs if g.attrs[k] > 99.0 + 1e-9)
            by_age.setdefault(age, []).append(g.overall - start)
            if gap0 < 0.5 and age < 30:
                plateau.append(g.overall - start)
    out = ['', '## 3. Lifecycle invariants (150 golfers aged 18-24, 25 years)', '',
           f'- Attribute-years above their ceiling: **{over_ceiling}**; above 99: **{over_99}**.',
           f'- Plateau: golfers within 0.5 of their ceilings (under 30) gained {S.mean(plateau) if plateau else 0:+.2f} '
           f'a year on average ({len(plateau)} golfer-years).',
           f'- Injuries simulated: {injuries}; with lasting damage: {lasting} (10+ weeks only).', '',
           '| Age | Golfer-years | Average change in overall |', '|---|---|---|']
    for lo, hi in ((18, 21), (22, 25), (26, 29), (30, 33), (34, 37), (38, 41), (42, 48)):
        xs = [d for a in range(lo, hi + 1) for d in by_age.get(a, [])]
        if xs:
            out.append(f'| {lo}-{hi} | {len(xs)} | {S.mean(xs):+.2f} |')
    # maturation during rest and work: teenagers grow physically, adults do not; no skill practice
    teen, adult = sample(world, 18, 12, 30, 1), sample(world, 28, 12, 30, 2)
    def rest_year(g, age):
        b = dict(g.attrs)
        for _ in range(52):
            D.develop_week(g, 'rest', age)
        phys = S.mean(g.attrs[k] - b[k] for k in D.CATEGORIES['physical'])
        skill = S.mean(g.attrs[k] - b[k] for k in g.attrs if D.CATEGORY_OF[k] != 'physical')
        return phys, skill
    t = [rest_year(g, 18) for g in teen]
    a = [rest_year(g, 28) for g in adult]
    out += ['', f'- A year of only rest or work: 18-year-olds gained {S.mean(p for p, _ in t):+.2f} physical, '
                f'{S.mean(s for _, s in t):+.2f} skill; 28-year-olds {S.mean(p for p, _ in a):+.2f} physical, '
                f'{S.mean(s for _, s in a):+.2f} skill (maturation is physical only and stops at 23).']
    return out


PATHS = (('Balanced (20 events, 26 training weeks)', 20, 26),
         ('Light competition (8 events, 38 training weeks)', 8, 38),
         ('Tournament-only (25 events, no training)', 25, 0),
         ('Training-only (no events, 46 training weeks)', 0, 46),
         ('Zero events, no training (rest or work)', 0, 0))


def path_years(g, age0, years, events, train, rng, competition_rules=True):
    """Run a golfer through `years` seasons of one schedule; 4 rounds per event, the rest of the year
    rest. Returns {age: overall at the start of that age}."""
    out = {}
    for y in range(years):
        age = age0 + y
        out[age] = g.overall
        weeks = ['play'] * events + ['train'] * train
        weeks += ['rest'] * (52 - len(weeks))
        rng.shuffle(weeks)
        rounds = 0.0
        exp = D.experience_factor(4.0 * events) if competition_rules else 1.0   # a steady schedule
        for act in weeks:
            if act == 'play':
                D.develop_week(g, 'play', age, rounds=4, experience=exp)
                rounds += 4
            elif act == 'train':
                D.develop_week(g, 'train', age, D.choose_category(g, rng), experience=exp)
            else:
                D.develop_week(g, 'rest', age)
        D.age_year(g, age + 1, rng, D.experience_factor(rounds) if competition_rules else 1.0)
    out[age0 + years] = g.overall
    return out


def paths_table(world):
    golfers = sample(world, 18, 15, 40, 18_15)
    out = ['', '## 4. Training and competition: development paths from 18 to 30', '',
           'The same 40 golfers (18, 15 points below potential), uncoached, run from 18 to 30 through one fixed '
           'schedule each year. "Now" applies the competition rules (composure, resilience, course management, '
           'focus and tournament consistency only train as far as recent competitive rounds support; the mental '
           'game matures each year with the rounds played); "before" is the same schedule without them. Whether '
           'the events were missed by choice or because every field was full makes no difference to development: '
           'the engine develops what a golfer did, not why.', '',
           '| Schedule | Overall at 22 (before / now) | at 26 | at 30 | Mental at 30 | Left below potential at 30 |',
           '|---|---|---|---|---|---|']
    for name, events, train in PATHS:
        row = {}
        for rules in (False, True):
            ages, mental, left = [], [], []
            for g in golfers:
                g = copy.deepcopy(g)
                ages.append(path_years(g, 18, 12, events, train, random.Random(g.id), rules))
                mental.append(S.mean(g.attrs[k] for k in D.CATEGORIES['mental']))
                left.append(max(0.0, g.potential - g.overall))
            row[rules] = ({a: S.mean(x[a] for x in ages) for a in (22, 26, 30)}, S.mean(mental), S.mean(left))
        (b, bm, bl), (n, nm, nl) = row[False], row[True]
        out.append(f'| {name} | {b[22]:.1f} / {n[22]:.1f} | {b[26]:.1f} / {n[26]:.1f} | {b[30]:.1f} / {n[30]:.1f} '
                   f'| {bm:.1f} / {nm:.1f} | {bl:.1f} / {nl:.1f} |')
    start = S.mean(g.overall for g in golfers)
    out += ['', f'Starting overall {start:.1f}; average potential {S.mean(g.potential for g in golfers):.1f}.']
    return out


def main():
    world = generate_world()
    out = ['# Golf Legacy — Development and Caddie Audit', '',
           'Generated by `python tools/development_audit.py`. A debug report: it reads hidden attributes.', '']
    out += coaching_table(world)
    out += caddie_table()
    out += lifecycle(world)
    out += paths_table(world)
    out += ['', '## Where hidden values are still used', '',
            '- **Training choices** (what to work on, and the planner\'s value of training vs playing) use each '
            'attribute\'s true room to its ceiling seen through a persistent personal misreading (wider for poor '
            'judges of their own game, narrowed by a coach). The misreading is fixed per golfer and attribute, so '
            'it does not converge on the truth over time; but it is anchored on the hidden ceiling.',
            '- **Scouting** by coaches uses observed level, the typical growth for the player\'s age and their '
            'observed improvement over the last year, plus scouting noise — not hidden potential.',
            '- **Development itself** (what a week actually does) uses the true ceilings, as it should.']
    path = ROOT / 'reports' / 'DEVELOPMENT_AUDIT.md'
    path.write_text('\n'.join(out) + '\n')
    print('wrote', path)


if __name__ == '__main__':
    main()
