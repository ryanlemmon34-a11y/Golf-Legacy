"""End of season: who plays where next year (tour cards, promotion, relegation, Q-School).

Premier Tour (300 members across three circuits)
    keep        top 200 on the season's Premier money list (all Premier events and majors);
                winners of a Premier event this season or last; major champions of the last 5 years
    lose        everyone else drops to their region's Challenger tour
    promoted    Challenger Tour Americas top 25, Europe top 20, Asia and Japan top 8, Latin America &
                Canada top 5; Premier Tour Q-School final top 5 and ties; Europe Q-School final top 20
    circuits    the top 10 on Premier Tour Europe and the top 5 on Asia-Pacific move to Americas
Challenger tours
    promoted: each Regional tour's top 8, each Mini tour's top 4, Q-School (Premier final 6th-45th,
    Europe final 21st-60th, Japan Q-School top 30, Asia Q-School top 35), players losing Premier cards
    keep: the best members on the tour's money list, enough to keep the tour at full size (at least
    half of them); the rest drop to their regional or mini tour
Regional tours
    keep their size: as many members drop to a mini tour as come in (at least 60% stay); each Mini
    tour's next 6 move up to their country's (or region's) regional tour
Mini tours are open: everyone else.
"""
from __future__ import annotations

from collections import defaultdict

from .calendar import TOUR_BY_KEY
from .geography import COUNTRIES
from .population import (CHALLENGER_BY_COUNTRY, CHALLENGER_BY_REGION, MEMBERS_PER_FIELD, MINI_BY_REGION,
                         REGIONAL_BY_COUNTRY, REGIONAL_BY_REGION)

PREMIER_TOURS = ('PT_AMERICAS', 'PT_EUROPE', 'PT_ASIA_PACIFIC')
PREMIER_KEEP = 200
CHALLENGER_TO_PREMIER = {'CH_AMERICAS': (25, 'PT_AMERICAS'), 'CH_EUROPE': (20, 'PT_EUROPE'),
                         'CH_ASIA': (8, 'PT_ASIA_PACIFIC'), 'CH_JAPAN': (8, 'PT_ASIA_PACIFIC'),
                         'CH_LATAM_CANADA': (5, 'PT_AMERICAS')}
CHALLENGER_KEEP, REGIONAL_KEEP = 0.50, 0.60     # minimum share of members who keep their card
TIERS_NAME = {2: 'Challenger', 3: 'Regional'}
REGIONAL_UP, MINI_UP_CHALLENGER, MINI_UP_REGIONAL = 8, 4, 6


def home_challenger(g):
    return CHALLENGER_BY_COUNTRY.get(g.country, CHALLENGER_BY_REGION[COUNTRIES[g.country].region])[0]


def home_mini(g):
    minis = [k for k, t in TOUR_BY_KEY.items() if t.tier == 4 and any(c == g.country for c, _ in t.countries)]
    options = minis or list(MINI_BY_REGION[COUNTRIES[g.country].region])
    return options[g.id % len(options)]


def home_lower(g):
    return REGIONAL_BY_COUNTRY.get(g.country) or home_mini(g)


def apply_cards(season, year):
    golfers = season.world.golfers
    gid = season.g
    money = season.money
    ctx = season.ctx
    new = {}                                     # gid -> (tier, tour, reason); best tier wins

    def assign(g, tour, reason):
        tier = TOUR_BY_KEY[tour].tier
        cur = new.get(g.id)
        if cur is None or tier < cur[0]:
            new[g.id] = (tier, tour, reason)

    def by_money(tour_key, members):
        m = money[(tour_key, year)]
        return sorted(members, key=lambda g: -m.get(g.id, 0.0))

    pros = [g for g in golfers if g.status == 'pro']
    members = defaultdict(list)
    for g in pros:
        members[g.tour].append(g)

    # Exemptions: Premier winners this season or last, major champions of the last 5 years
    exempt = set()
    for (sid, y), sites in ctx.results.items():
        s = season.cal.by_id.get(sid)
        if s is None or not sites:
            continue
        w = ctx.winner(sid, y)
        if w is None:
            continue
        if s.kind == 'major' and year - 4 <= y <= year:
            exempt.add(w)
        elif s.tier == 1 and year - 1 <= y <= year:
            exempt.add(w)

    # ---- Premier Tour -------------------------------------------------------------------------
    premier = [g for g in pros if g.tour in PREMIER_TOURS]
    order = by_money('PREMIER', premier)
    for i, g in enumerate(order):
        if i < PREMIER_KEEP or g.id in exempt:
            assign(g, g.tour, 'kept card' if i < PREMIER_KEEP else 'winner exemption')
        else:
            assign(g, home_challenger(g), 'lost Premier card')
    for tour, n in (('PT_EUROPE', 10), ('PT_ASIA_PACIFIC', 5)):
        for g in by_money(tour, members[tour])[:n]:
            if new[g.id][1] == tour:
                new[g.id] = (1, 'PT_AMERICAS', f'top {n} on {TOUR_BY_KEY[tour].name}')
    for tour, (n, to) in CHALLENGER_TO_PREMIER.items():
        for g in by_money(tour, members[tour])[:n]:
            assign(g, to, f'top {n} on {TOUR_BY_KEY[tour].name}')

    def qs(sid, lo, hi, tour, reason):
        for g_id, pos in ctx.finishers(sid, year):
            if pos is not None and lo <= pos <= hi and gid[g_id].status == 'pro':
                assign(gid[g_id], tour, reason)

    qs('PT_QSCHOOL_FINAL', 1, 5, 'PT_AMERICAS', 'Q-School medal')
    qs('EU_QSCHOOL_FINAL', 1, 20, 'PT_EUROPE', 'Europe Q-School')
    qs('PT_QSCHOOL_FINAL', 6, 45, 'CH_AMERICAS', 'Q-School')
    qs('EU_QSCHOOL_FINAL', 21, 60, 'CH_EUROPE', 'Europe Q-School')
    qs('JP_QSCHOOL_FINAL', 1, 30, 'CH_JAPAN', 'Japan Q-School')
    qs('ASIA_QSCHOOL_FINAL', 1, 35, 'CH_ASIA', 'Asia Q-School')

    # ---- Challenger, Regional, Mini ------------------------------------------------------------
    for tour, t in TOUR_BY_KEY.items():
        if t.tier == 3:
            for g in by_money(tour, members[tour])[:REGIONAL_UP]:
                assign(g, home_challenger(g), f'top {REGIONAL_UP} on {t.name}')
        elif t.tier == 4:
            order = by_money(tour, members[tour])
            for g in order[:MINI_UP_CHALLENGER]:
                assign(g, home_challenger(g), f'top {MINI_UP_CHALLENGER} on {t.name}')
            for g in order[MINI_UP_CHALLENGER:MINI_UP_CHALLENGER + MINI_UP_REGIONAL]:
                up = REGIONAL_BY_COUNTRY.get(g.country) or next(iter(REGIONAL_BY_REGION[COUNTRIES[g.country].region]), None)
                if up:
                    assign(g, up, f'top 10 on {t.name}')

    def incoming(tour):
        return sum(1 for g_id, (_, to, _) in new.items() if to == tour and gid[g_id].tour != tour)

    # Each Challenger and Regional tour keeps enough of its best members to stay at full size
    # (never fewer than its keep share); the rest drop a level.
    for tier, share, drop in ((2, CHALLENGER_KEEP, home_lower), (3, REGIONAL_KEEP, home_mini)):
        for tour, t in TOUR_BY_KEY.items():
            if t.tier != tier:
                continue
            order = [g for g in by_money(tour, members[tour]) if g.id not in new or new[g.id][0] >= tier]
            target = round(t.field * MEMBERS_PER_FIELD)
            if tier == 3:                        # regional tours hold their size rather than fill to capacity
                target = min(target, len(members[tour]))
            keep = max(round(len(order) * share), target - incoming(tour))
            for i, g in enumerate(order):
                if i < keep:
                    assign(g, tour, 'kept card')
                else:
                    assign(g, drop(g), f'lost {TIERS_NAME[tier]} card')
    for tour, t in TOUR_BY_KEY.items():
        if t.tier == 4:
            for g in members[tour]:
                assign(g, tour, 'mini tour')

    # Premier members not placed above keep a lower card by default
    for g in pros:
        if g.id not in new:
            assign(g, home_mini(g), 'no status')
    log = season.card_log[year]
    for g in pros:
        tier, tour, reason = new[g.id]
        if tour != g.tour:
            log.append((g.id, g.tour, tour, reason))
            g.tour = tour
