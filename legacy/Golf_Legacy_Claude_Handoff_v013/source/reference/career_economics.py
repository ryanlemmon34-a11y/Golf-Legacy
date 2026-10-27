"""Auditable fictional golf-bankroll economics, v0.5.

All amounts are SIMULATED USD-equivalent dollars. This is not a claim about
actual tour salaries, subsidies, sponsorship prevalence, or retirement rates.
Cash is disposable golf bankroll, NOT household wealth. Outside-work receipts
are net contributions after personal living costs/tax, not gross wages. There
is no borrowing, unrecorded rescue, future-prize credit, or negative bankroll.
The module uses a separate keyed RNG and never consumes a world's scoring RNG.
"""
from __future__ import annotations

import csv
import hashlib
import math
import random
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Mapping, Sequence

EVENT_COST = {1: 3900., 2: 2100., 3: 1000., 4: 420.}
ANNUAL_OVERHEAD = {1: 75000., 2: 32000., 3: 15000., 4: 8000.}
SPONSOR_CAP = {1: 60000., 2: 18000., 3: 6000., 4: 2000.}
STATUS_ACTIVE, STATUS_HIATUS, STATUS_RETIRED = 'active', 'hiatus', 'retired'


def cents(amount: float) -> int:
    if not math.isfinite(float(amount)):
        raise ValueError('Money must be finite')
    return int((Decimal(str(amount)) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def dollars(amount: int) -> float:
    return amount / 100


def allocate_prizes(final_ids: Sequence[int], scores: Mapping[int, Any],
                    winner_id: int, purse: float) -> dict[int, float]:
    """Allocate the ENTIRE purse among finishers; missed cuts are not supplied.

    Scores may be totals or engine score dictionaries with a ``total`` key.
    A playoff produces a sole winner; the other same-score golfers share the
    occupied runner-up places. Ties split combined place money, with at most
    one cent difference (stable ID tie break). The descending schedule is a
    fictional assumption: winner 18%, rest normalized rank^-0.85. For small fields where that would overpay second place, use normalized
    rank^-0.85 throughout to retain monotonicity.
    """
    ids = list(final_ids)
    if not ids or len(set(ids)) != len(ids) or winner_id not in ids:
        raise ValueError('Need unique finishers including the winner')
    total_cents = cents(purse)
    if total_cents < 0:
        raise ValueError('Purse cannot be negative')
    get_score = lambda gid: scores[gid]['total'] if isinstance(scores[gid], Mapping) else scores[gid]
    ordered = sorted(ids, key=lambda gid: (get_score(gid), gid))
    if get_score(winner_id) != get_score(ordered[0]):
        raise ValueError('Winner must have a minimum total')
    n = len(ids)
    raw_all = [rank ** -.85 for rank in range(1, n + 1)]
    if n == 1:
        weights = [1.]
    else:
        tail = [.82 * v / sum(raw_all[1:]) for v in raw_all[1:]]
        weights = [.18] + tail if tail[0] <= .18 else [v / sum(raw_all) for v in raw_all]
    slots = [int(total_cents * weight) for weight in weights]
    # Fractional-cent residuals awarded by largest remainder, then place.
    residual_order = sorted(range(n), key=lambda i: (-(total_cents * weights[i] - slots[i]), i))
    for index in residual_order[:total_cents - sum(slots)]:
        slots[index] += 1
    groups = [[winner_id]]
    for gid in ordered:
        if gid == winner_id:
            continue
        if len(groups) > 1 and get_score(groups[-1][0]) == get_score(gid):
            groups[-1].append(gid)
        else:
            groups.append([gid])
    result, offset = {}, 0
    for group in groups:
        shared, remainder = divmod(sum(slots[offset:offset + len(group)]), len(group))
        for index, gid in enumerate(sorted(group)):
            result[gid] = dollars(shared + (index < remainder))
        offset += len(group)
    assert sum(cents(v) for v in result.values()) == total_cents
    return result


@dataclass
class CareerAccount:
    golfer_id: int
    opening_cents: int
    balance_cents: int
    status: str = STATUS_ACTIVE
    season_year: int | None = None
    season_tier: int = 4
    week: int = 0
    starts: int = 0
    denied_starts: int = 0
    season_opening_cents: int = 0
    season_prize_cents: int = 0
    season_cost_cents: int = 0
    season_work_cents: int = 0
    season_sponsor_cents: int = 0
    training_paid: bool = False
    work_fraction: float = 0.
    work_capacity_cents: int = 0
    ambition: float = .5
    patience: int = 4
    opportunity_weight: float = .5
    poor_years: int = 0
    hiatus_years: int = 0
    total_hiatus_years: int = 0
    last_prize_cents: int = 0
    last_golf_net_cents: int = 0
    net_history: list[int] = field(default_factory=list)
    performance_history: list[dict] = field(default_factory=list)
    reviewed_year: int | None = None
    closed: bool = False
    paid_events: set[str] = field(default_factory=set)
    paid_prizes: set[str] = field(default_factory=set)
    denied_events: set[str] = field(default_factory=set)


class Economics:
    """One account per golfer. Own ALL cash mutations after registration.

    Methods mutate g.cash and may change g.tier (financial downshift), g.retired
    (permanent exit), and append explicitly timed g.career records. The caller
    must not independently add prizes, subtract event/annual costs, or apply the
    old debt-exit condition. An external biological retirement can be synced
    using mark_retired(). A temporary hiatus never sets g.retired.
    """
    def __init__(self, seed: int = 42, *, sponsorship: bool = False, outside_work: bool = True,
                 reassessment_age: int = 26,
                 event_cost: Mapping[int, float] | None = None,
                 annual_overhead: Mapping[int, float] | None = None):
        self.seed, self.sponsorship, self.outside_work = seed, sponsorship, outside_work
        self.reassessment_age = reassessment_age
        self.event_cost = dict(EVENT_COST if event_cost is None else event_cost)
        self.annual_overhead = dict(ANNUAL_OVERHEAD if annual_overhead is None else annual_overhead)
        if set(self.event_cost) != {1, 2, 3, 4} or set(self.annual_overhead) != {1, 2, 3, 4}:
            raise ValueError('Exactly four fictional tiers are required')
        if any(not math.isfinite(v) or v < 0 for v in [*self.event_cost.values(), *self.annual_overhead.values()]):
            raise ValueError('Costs must be finite and nonnegative')
        self.accounts: dict[int, CareerAccount] = {}
        self.ledger: list[dict] = []
        self.seasons: list[dict] = []
        self.transitions: list[dict] = []

    def _rng(self, gid: int, year: int, purpose: str) -> random.Random:
        raw = f'golf-economics-v05|{self.seed}|{gid}|{year}|{purpose}'.encode()
        return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], 'big'))

    def register(self, g, year: int, *, initial: bool = False) -> CareerAccount:
        if g.id in self.accounts:
            self._check_cash(g)
            return self.accounts[g.id]
        amount = cents(g.cash)
        if amount < 0:
            raise ValueError('Cannot import an unfunded negative bankroll; no silent debt forgiveness')
        r = self._rng(g.id, year, 'profile')
        a = CareerAccount(g.id, amount, amount, season_tier=g.tier,
                          work_capacity_cents=cents(r.uniform(12000, 32000)),
                          ambition=r.uniform(.15, .95), patience=r.randint(2, 6),
                          opportunity_weight=r.uniform(.2, .75))
        if g.retired:
            a.status = STATUS_RETIRED
        self.accounts[g.id] = a
        g.cash = dollars(amount)
        self.ledger.append(dict(sequence=len(self.ledger), year=year, week=0,
                                golfer_id=g.id, category='opening_bankroll',
                                amount=dollars(amount), balance=dollars(amount), event_id='',
                                note='Initial disposable golf savings; not career earnings'))
        return a

    def _check_cash(self, g) -> CareerAccount:
        a = self.accounts[g.id]
        if cents(g.cash) != a.balance_cents:
            raise AssertionError(f'Unledgered cash mutation for golfer {g.id}: {g.cash} != {dollars(a.balance_cents)}')
        return a

    def _post(self, g, amount_cents: int, category: str, year: int, week: int,
              event_id: str = '', note: str = ''):
        a = self._check_cash(g)
        if a.balance_cents + amount_cents < 0:
            raise ValueError('Transaction would spend unavailable funds')
        a.balance_cents += amount_cents
        g.cash = dollars(a.balance_cents)
        self.ledger.append(dict(sequence=len(self.ledger), year=year, week=week,
                                golfer_id=g.id, category=category,
                                amount=dollars(amount_cents), balance=g.cash,
                                event_id=str(event_id), note=note))

    def _transition(self, g, year: int, week: int, event: str, reason: str, **details):
        row = dict(year=year, week=week, golfer_id=g.id, event=event, reason=reason, **details)
        self.transitions.append(row)
        g.career.append(dict(year=year, week=week, event=event,
                             timing='season_start' if week == 0 else 'year_end' if week == 52 else 'in_season',
                             reason=reason, **details))

    def begin_season(self, g, year: int) -> dict:
        a = self.register(g, year)
        if a.season_year == year:
            raise ValueError('Season already opened')
        if a.season_year is not None and (not a.closed or year <= a.season_year):
            raise ValueError('Close the previous season and advance the year first')
        a.season_year, a.closed, a.week = year, False, 0
        a.starts = a.denied_starts = 0
        a.season_opening_cents = a.balance_cents
        a.season_prize_cents = a.season_cost_cents = a.season_work_cents = a.season_sponsor_cents = 0
        a.paid_events.clear(); a.paid_prizes.clear(); a.denied_events.clear()
        a.training_paid = False
        if g.retired or a.status == STATUS_RETIRED:
            a.status = STATUS_RETIRED
            return self.snapshot(g)
        r = self._rng(g.id, year, 'season')
        # One passive, capped annual performance payment. No sponsor brands,
        # negotiation, management, guaranteed renewal, or low-cash rescue.
        # Only completed prior prizes count; no prospect's hidden potential.
        if self.sponsorship and a.status == STATUS_ACTIVE:
            threshold = cents(self.annual_overhead[g.tier] * .4)
            if a.last_prize_cents >= max(1, threshold):
                probability = min(.65, .15 + .20 * min(2., a.last_prize_cents / max(1, cents(self.annual_overhead[g.tier]))))
                if self._rng(g.id, year, 'sponsorship').random() < probability:
                    amount = min(cents(SPONSOR_CAP[g.tier]), round(a.last_prize_cents * .12))
                    self._post(g, amount, 'sponsorship', year, 0,
                               note='Optional capped 12% prior-season-prize performance payment; no guaranteed renewal')
                    a.season_sponsor_cents += amount
        if a.status == STATUS_HIATUS:
            runway = cents(self.annual_overhead[4] + 3 * self.event_cost[4] + 2000)
            age = year - g.born
            desire = max(.05, .25 + .55 * a.ambition - max(0, age - 35) * .025)
            if a.balance_cents >= runway and r.random() < desire:
                a.status = STATUS_ACTIVE
                old = g.tier
                g.tier = 4  # Return through affordable lesser competition, not restored elite status.
                self._transition(g, year, 0, 'Returned from career hiatus', 'Savings runway rebuilt; chose a lower-cost return', from_tier=old, to_tier=4)
                a.hiatus_years = 0
            else:
                a.season_tier = g.tier
                a.work_fraction = 1.
                return self.snapshot(g)
        old = g.tier
        tier = old
        # Prepay the full operating year BEFORE first entry. No next-tier
        # retroactive bill, future prize credit, or future work advance.
        while tier < 4 and a.balance_cents < cents(self.annual_overhead[tier] + self.event_cost[tier]):
            tier += 1
        if a.balance_cents < cents(self.annual_overhead[tier] + self.event_cost[tier]):
            a.status, a.work_fraction, a.season_tier = STATUS_HIATUS, 1., g.tier
            self._transition(g, year, 0, 'Career hiatus', 'Insufficient funded operating-year and first-event runway')
            return self.snapshot(g)
        g.tier = a.season_tier = tier
        if tier != old:
            self._transition(g, year, 0, 'Financial downshift', 'Chose an affordable circuit rather than unfunded participation', from_tier=old, to_tier=tier)
        cost = cents(self.annual_overhead[tier])
        self._post(g, -cost, 'annual_overhead', year, 0,
                   note=f'Prepaid actual operating tier {tier}; excludes per-event travel/caddie costs')
        a.season_cost_cents += cost
        a.training_paid = True
        # Affluent established players can train full time; lower-runway players
        # use limited outside work, costing practice time as well as generating cash.
        a.work_fraction = 0. if not self.outside_work or a.balance_cents >= cents(2 * self.annual_overhead[tier]) else r.uniform(.15, .50)
        return self.snapshot(g)

    def advance_to_week(self, g, year: int, week: int) -> dict:
        a = self._check_cash(g)
        if a.season_year != year or a.closed or not 0 <= week <= 52 or week < a.week:
            raise ValueError('Economics requires an open season and nondecreasing weeks 0..52')
        if a.status != STATUS_RETIRED and self.outside_work:
            # Cumulative rounded accrual makes calling frequency irrelevant.
            annual = round(a.work_capacity_cents * a.work_fraction)
            desired = annual * week // 52
            amount = desired - a.season_work_cents
            if amount:
                self._post(g, amount, 'outside_work_net', year, week,
                           note='Earned elapsed-time contribution after household costs/tax; not gross wages')
                a.season_work_cents += amount
        a.week = week
        return self.snapshot(g)

    def can_start(self, g, tour_tier: int, year: int, week: int) -> bool:
        a = self._check_cash(g)
        if a.season_year != year or a.closed or week != a.week:
            raise ValueError('Call advance_to_week before testing event affordability')
        return bool(not g.retired and a.status == STATUS_ACTIVE and a.training_paid and
                    a.balance_cents >= cents(self.event_cost[tour_tier]))

    def pay_entry(self, g, event_id: str, tour_tier: int, year: int, week: int) -> bool:
        a = self._check_cash(g)
        key = str(event_id)
        if key in a.paid_events:
            raise ValueError('Duplicate event cost / start')
        if not self.can_start(g, tour_tier, year, week):
            if key not in a.denied_events:
                a.denied_events.add(key); a.denied_starts += 1
            return False
        amount = cents(self.event_cost[tour_tier])
        self._post(g, -amount, 'event_cost', year, week, key,
                   note=f'Tier {tour_tier} travel/caddie/participation budget; not an official tour entry fee')
        a.paid_events.add(key); a.starts += 1; a.season_cost_cents += amount
        return True

    def credit_prize(self, g, event_id: str, money: float, year: int, week: int) -> None:
        a = self._check_cash(g)
        key = str(event_id)
        amount = cents(money)
        if a.season_year != year or a.closed or week != a.week:
            raise ValueError('Prize must post in the open event week, after its cost')
        if key not in a.paid_events or key in a.paid_prizes or amount < 0:
            raise ValueError('Prize needs a funded start, no duplicate payment, and nonnegative money')
        self._post(g, amount, 'prize', year, week, key, note='Earned only after tournament result')
        a.paid_prizes.add(key); a.season_prize_cents += amount
        # Engine must NOT also increment earnings for this prize.
        g.earnings = dollars(cents(g.earnings) + amount)

    def training_exposure(self, g) -> float:
        a = self.accounts[g.id]
        if a.status == STATUS_RETIRED:
            return 0.
        if not a.training_paid:
            return .12  # Uncoached maintenance while working, not a full-time grind.
        practice_time = 1 - .65 * a.work_fraction
        competition = .65 + .35 * min(1., a.starts / 12)
        return max(0., min(1., practice_time * competition))

    def mark_retired(self, g, year: int, *, reason: str = 'Age/health or personal career decision', week: int = 52):
        a = self._check_cash(g)
        if a.status != STATUS_RETIRED:
            a.status = STATUS_RETIRED
            g.retired = True
            self._transition(g, year, week, 'Retired', reason, age=year-g.born)
        if a.closed and a.season_year == year:
            for row in reversed(self.seasons):
                if row['golfer_id'] == g.id and row['year'] == year:
                    row['next_status'] = STATUS_RETIRED
                    break

    def end_season(self, g, year: int, *, review: bool = False, performance: Mapping[str, Any] | None = None) -> dict:
        a = self._check_cash(g)
        if a.season_year != year or a.closed:
            raise ValueError('Close each open season exactly once')
        self.advance_to_week(g, year, 52)
        training = self.training_exposure(g)
        before = a.status
        net = a.season_prize_cents + a.season_sponsor_cents - a.season_cost_cents
        if before == STATUS_HIATUS:
            a.hiatus_years += 1; a.total_hiatus_years += 1
        elif before == STATUS_ACTIVE:
            opportunity = round(a.work_capacity_cents * a.opportunity_weight)
            a.poor_years = a.poor_years + 1 if net < opportunity else 0
        a.last_prize_cents, a.last_golf_net_cents = a.season_prize_cents, net
        a.net_history = (a.net_history + [net])[-3:]
        if performance is not None:
            observed = dict(performance)
            observed['year'] = year
            if 'field_relative_strokes_per_round' not in observed and 'field_adjusted_strokes_per_round' in observed:
                observed['field_relative_strokes_per_round'] = observed['field_adjusted_strokes_per_round']
            if int(observed.get('starts', -1)) != a.starts:
                raise ValueError('Observed performance starts must match funded starts')
            if observed.get('cut_rate') is None and observed.get('starts') == 0:
                observed['cut_rate'] = 0.  # No-start history never passes progress sample gates.
            if observed.get('rounds_observed', 0) < 0 or not 0 <= observed.get('cut_rate', 0) <= 1:
                raise ValueError('Invalid observed rounds/cut rate')
            for key in ('field_relative_strokes_per_round', 'field_adjusted_strokes_per_round', 'mean_event_tier'):
                if observed.get(key) is not None and not math.isfinite(float(observed[key])):
                    raise ValueError('Observed performance values must be finite')
            a.performance_history = (a.performance_history + [observed])[-3:]
        else:
            a.performance_history = []  # Missing seasons cannot imply a continuous trend.
        progress = self.observed_progress(g)

        row = dict(year=year, golfer_id=g.id, age=year-g.born, operating_tier=a.season_tier,
                   season_status=before, next_status=a.status, opening_cash=dollars(a.season_opening_cents),
                   closing_cash=g.cash, prizes=dollars(a.season_prize_cents),
                   sponsorship=dollars(a.season_sponsor_cents), outside_work_net=dollars(a.season_work_cents),
                   golf_costs=dollars(a.season_cost_cents), golf_net=dollars(net),
                   prize_net=dollars(a.season_prize_cents - a.season_cost_cents),
                   starts=a.starts, denied_starts=a.denied_starts, training_exposure=round(training, 6),
                   outside_work_fraction=round(a.work_fraction, 6), poor_years=a.poor_years,
                   hiatus_years=a.hiatus_years, observable_progress=progress['progressing'],
                   progress_reason=progress['reason'], min_tour_runway_events=round(a.balance_cents / max(1, cents(self.event_cost[4])), 2))
        expected = a.season_opening_cents + a.season_prize_cents + a.season_sponsor_cents + a.season_work_cents - a.season_cost_cents
        if expected != a.balance_cents:
            raise AssertionError('Season accounting does not reconcile')
        a.closed = True
        self.seasons.append(row)
        if review:
            self.review_career(g, year)
        return row

    def observed_progress(self, g) -> dict:
        """Three consecutive, sampled seasons only; no caps/ability oracle.

        Score values are actual field-relative strokes per round (higher better),
        NOT a cross-tour field-strength estimate. A weaker tour mix is therefore
        not credited as scoring/cut development.
        Thresholds are transparent fictional noise guards, not fitted statistics.
        """
        history = self.accounts[g.id].performance_history
        no = dict(progressing=False, reason='Insufficient sustained observed progress')
        if len(history) != 3 or any(history[i+1]['year'] != history[i]['year'] + 1 for i in (0, 1)):
            return no
        if any(row.get('starts', 0) < 4 or row.get('rounds_observed', 0) < 12 for row in history):
            return no
        values = [row.get('field_relative_strokes_per_round', row.get('field_adjusted_strokes_per_round')) for row in history]
        cut_rates = [row.get('cut_rate', 0.) for row in history]
        tiers = [row.get('mean_event_tier', row.get('operating_tier')) for row in history]
        nonweakening_opportunities = all(value is not None for value in tiers) and all(tiers[i+1] <= tiers[i] + .10 for i in (0, 1))
        score_progress = nonweakening_opportunities and all(value is not None for value in values) and all(values[i+1] - values[i] >= .05 for i in (0, 1)) and values[2] - values[0] >= .35
        cut_progress = nonweakening_opportunities and all(row.get('starts', 0) >= 8 for row in history) and all(cut_rates[i+1] - cut_rates[i] >= .03 for i in (0, 1)) and cut_rates[2] - cut_rates[0] >= .12
        opportunity_progress = all(value is not None for value in tiers) and tiers[0] >= tiers[1] >= tiers[2] and tiers[0] - tiers[2] >= .75
        # More difficult actual opportunities count only with reasonably stable
        # cuts and field-adjusted scoring, not an unsupported card/ability claim.
        opportunity_progress = opportunity_progress and all(value is not None for value in values) and min(values[1:]) >= values[0] - .10 and min(cut_rates[1:]) >= cut_rates[0] - .10
        reasons = []
        if score_progress: reasons.append('sustained same-or-higher-tier field-relative scoring improvement')
        if cut_progress: reasons.append('sustained same-or-higher-tier cut-rate improvement')
        if opportunity_progress: reasons.append('higher-tier actual opportunities with stable performance')
        return dict(progressing=bool(reasons), reason='; '.join(reasons) if reasons else no['reason'])

    def financial_exit_probability(self, g, year: int) -> float:
        """Inspectable probability; does not draw RNG or waive affordability."""
        a = self.accounts[g.id]
        age = year - g.born
        if a.status != STATUS_ACTIVE or a.poor_years < a.patience or age < self.reassessment_age:
            return 0.
        # Two successive net improvements avoid treating a single lucky prize
        # as a durable career arc. Observed scoring/cuts can independently help.
        improving = len(a.net_history) == 3 and all(a.net_history[i+1] > a.net_history[i] for i in (0, 1)) and a.net_history[-1] - a.net_history[0] > cents(max(3000., .20 * self.annual_overhead[a.season_tier]))
        buffer = a.balance_cents / max(1, cents(self.annual_overhead[a.season_tier]))
        probability = min(.65, .06 + .035 * (a.poor_years - a.patience) + .012 * max(0, age - self.reassessment_age))
        if improving or self.observed_progress(g)['progressing']:
            probability *= .35
        if buffer >= 3:
            probability *= .45
        if len(a.net_history) >= 2 and sum(a.net_history) >= 0:
            probability *= .65
        return probability

    def review_career(self, g, year: int) -> dict:
        """Apply career choice AFTER snapshots/development; no duplicate review.

        Age 26 is a configurable soft reassessment point, never a forced cut.
        Three-year results, improvement, savings, personal patience, and chance
        change financial exit propensity. This is fictional behavior, not a
        measured age-specific retirement probability.
        """
        a = self._check_cash(g)
        if a.season_year != year or not a.closed or a.reviewed_year == year:
            raise ValueError('Review once, after closing the matching season')
        a.reviewed_year = year
        if g.retired and a.status != STATUS_RETIRED:
            self.mark_retired(g, year)
        if not g.retired:
            r = self._rng(g.id, year, 'career_review')
            age = year - g.born
            if a.status == STATUS_HIATUS:
                probability = min(.72, .025 + .035 * a.hiatus_years + .012 * max(0, age - 30))
                if a.hiatus_years >= a.patience and r.random() < probability:
                    self.mark_retired(g, year, reason='Chose permanent exit after a working hiatus and reassessment')
            elif a.poor_years >= a.patience and age >= self.reassessment_age:
                probability = self.financial_exit_probability(g, year)
                if r.random() < probability:
                    self.mark_retired(g, year, reason='Sustained net golf returns did not justify opportunity cost', week=52)
            if not g.retired and a.status == STATUS_ACTIVE:
                runway = cents(self.annual_overhead[4] + 3 * self.event_cost[4])
                if a.balance_cents < runway:
                    a.status = STATUS_HIATUS
                    self._transition(g, year, 52, 'Career hiatus', 'Paused full-time competition to rebuild an affordable runway')
        for row in reversed(self.seasons):
            if row['golfer_id'] == g.id and row['year'] == year:
                row['next_status'] = a.status
                break
        return self.snapshot(g)

    def snapshot(self, g) -> dict:
        a = self._check_cash(g)
        return dict(status=a.status, season_tier=a.season_tier, cash=g.cash,
                    starts=a.starts, training_exposure=self.training_exposure(g),
                    overhead_prepaid=a.training_paid, work_fraction=a.work_fraction,
                    work_capacity=dollars(a.work_capacity_cents))

    def validate(self, golfers: Mapping[int, Any] | None = None) -> dict:
        balances, errors = {}, []
        for entry in self.ledger:
            gid = entry['golfer_id']
            balances[gid] = balances.get(gid, 0) + cents(entry['amount'])
            if balances[gid] != cents(entry['balance']) or balances[gid] < 0:
                errors.append(f'Invalid balance at transaction {entry["sequence"]}')
        for gid, a in self.accounts.items():
            if balances.get(gid) != a.balance_cents:
                errors.append(f'Final ledger mismatch for {gid}')
            if golfers is not None and cents(golfers[gid].cash) != a.balance_cents:
                errors.append(f'Unledgered final cash for {gid}')
        return dict(valid=not errors, errors=errors, accounts=len(self.accounts), transactions=len(self.ledger),
                    negative_balances=sum(a.balance_cents < 0 for a in self.accounts.values()),
                    statuses={status: sum(a.status == status for a in self.accounts.values())
                              for status in (STATUS_ACTIVE, STATUS_HIATUS, STATUS_RETIRED)})

    def export(self, root: str | Path) -> dict:
        root = Path(root); root.mkdir(parents=True, exist_ok=True)
        for name, rows in [('economics_ledger.csv', self.ledger), ('economics_seasons.csv', self.seasons),
                           ('economics_transitions.csv', self.transitions)]:
            if not rows:
                continue
            names = list(dict.fromkeys(key for row in rows for key in row))
            with (root / name).open('w', encoding='utf8', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=names); writer.writeheader(); writer.writerows(rows)
        return self.validate()
