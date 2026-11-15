"""The controlled golfer's money: where it came from and went, and why sponsors and backers pay what they do
(read only; records and the engine's own formulas, nothing estimated).

`money_view(season, golfer, year)`:
* `funds`: the money they hold now -- their own cash, family backing, their backers' money for this season -- and
  what they can spend on golf (Season.spendable);
* `seasons`: this season's and last season's ledgers (finance.Ledger: every line the engine books, income and
  costs); older seasons are in the world's archive, not here (null);
* `sponsor`: this season's sponsor contract (Season.contracts) and the rule behind it: professionals only, from
  their Prestige (prestige.endorsements); amateurs have none;
* `backer`: the backing deal (yearly dollars, 0 = none), the money the backers put up or got back this season
  (Season.backer_flows), and the year their last deal ended, if one did.
"""
from __future__ import annotations

LINES_IN = ('prize', 'sponsors', 'salary', 'work', 'support', 'backer_support', 'am_support')
LINES_OUT = ('events', 'caddie', 'caddie_share', 'coaching', 'coach_share', 'living', 'backer_share', 'moving')
LABELS = {'prize': 'prize money', 'sponsors': 'sponsor contract', 'salary': 'salary (job)', 'work': 'paid work weeks',
          'support': 'family support', 'backer_support': 'backers covering shortfalls',
          'am_support': 'amateur support (paid golf costs, in kind)', 'events': 'entry fees and travel',
          'caddie': 'caddie fees', 'caddie_share': "caddie's share of prize money", 'coaching': 'coaching fees',
          'coach_share': "coach's share of prize money", 'living': 'living costs',
          'backer_share': "backers' share of prize money", 'moving': 'moving home'}


def _ledger(season, gid, year):
    led = season.ledgers.get(year, {}).get(gid)
    if led is None:
        return None
    return {'income': {k: round(getattr(led, k), 2) for k in LINES_IN},
            'costs': {k: round(getattr(led, k), 2) for k in LINES_OUT},
            'total_income': round(led.income, 2), 'total_costs': round(led.costs, 2), 'net': round(led.net, 2)}


def money_view(season, g, year):
    from . import prestige as PR
    gid = g.id
    flows = season.backer_flows.get(year, {})
    pres = season.player_prestige(gid)
    pro = g.status == 'pro' and g.lifestyle != 'retired'
    return {
        'year': year, 'labels': dict(LABELS),
        'funds': {'cash': round(g.cash, 2), 'family_backing': round(g.backing, 2),
                  'backer_funds': round(g.backer_funds, 2), 'spendable': round(season.spendable(g, year), 2),
                  'needs_paid_work': bool(pro and g.lifestyle == 'full_time' and season.needs_paid_work(g, year))},
        'seasons': {str(year): _ledger(season, gid, year), str(year - 1): _ledger(season, gid, year - 1)},
        'sponsor': {'contract': round(season.contracts.get(gid, 0.0), 2), 'prestige': round(pres, 2),
                    'rule': ('a professional\'s sponsor contract for the season follows their Prestige '
                             '(set on 1 January)') if pro else 'amateurs have no sponsor contracts',
                    'at_this_prestige_now': round(PR.endorsements(pres), 2) if pro else 0.0},
        'backer': {'deal': round(g.backer or 0.0, 2), 'put_up': round(flows.get((gid, 'put_up'), 0.0), 2),
                   'returned': round(flows.get((gid, 'returned'), 0.0), 2),
                   'last_deal_ended': season.backer_ended.get(gid)},
    }
