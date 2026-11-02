"""Career mode: one golfer under human control in the living world (roadmap Phases A and B).

Design and boundaries: docs/career/PHASE_AB_PLAN.md. In short:

* The career record (`Career`) is plain data held by the season (`season.career`), so it is saved in the same
  checkpoint as the world, its clock and its random state. `None` is an all-AI world, and every engine hook is then
  a no-op.
* Commands are an application-level API (`apply`): versioned payloads (`schema`), validated by the same rule
  services the AI uses, each returning a result or raising CareerError with the reason and changing nothing.
  `Session.career_action` runs them under the session's lock, recognises repeated operation keys and commits a new
  checkpoint generation, exactly like an advance.
* Gates (`gate`) tell the session when it must stop before a part of the simulation. They run before the week is
  prepared (a plan is missing, or a decision is due) and again after the week is prepared (the week's choice
  revalidated after 1 January's and the block planning's effects, before any field, charge or result). Winter is
  not playable in this build, so its gate always stops; the golfer can be returned to AI control.
* Offers to the controlled golfer (coach, caddie, a job from the work pathway) become pending decisions. Nothing is
  ended, assigned, charged or reserved until the player answers. Acceptance revalidates, then applies the same
  consequence as the AI path.
* Hidden potential never enters a view, decision, notice or explanation.
"""
from __future__ import annotations

import random

FORMAT = 1                  # the career record's format: a save with a newer one is refused, never guessed at
SCHEMA = 1                  # the command payloads' schema
BLOCK = 4                   # planning period: the engine's four-week block (13 a season), not a calendar month
NOTICES_KEPT = 200
CATEGORIES = ('physical', 'long_game', 'short_game', 'putting', 'mental')
CATEGORY_LABEL = {'physical': 'Physical', 'long_game': 'Long game', 'short_game': 'Short game', 'putting': 'Putting',
                  'mental': 'Mental game'}
OFFER_KINDS = ('coach_offer', 'caddie_offer', 'job')


class CareerError(Exception):
    """A command that cannot proceed. The message is the reason, and nothing was changed."""


class StaleCareer(CareerError):
    """The command was drawn for an earlier state of the career (a form left open, a repeated click)."""


def block_start(week):
    return week - (week - 1) % BLOCK


def block_weeks(w0):
    return [w for w in range(w0, w0 + BLOCK) if w <= 52]


def entrant_decides(series):
    """Qualifying, where entrants decide whether to try; everything else rule-selected is accept or decline."""
    return series.category in ('qualifier', 'q_school')


def date_text(year, week):
    return f'week {week} of {year}'


class Career:
    """One golfer under human control. Plain data only: no renderer objects, handlers or file paths."""

    def __init__(self, golfer_id, year, week, entry):
        self.format = FORMAT
        self.id = 'C1'
        self.golfer_id = golfer_id
        self.status = 'active'                # 'active' | 'ended'
        self.started = (year, week)
        self.ended = None
        self.entry = dict(entry)              # how the golfer was chosen (rule, class, size): no hidden facts
        self.version = 0                      # changes with every change: forms carry it (stale submissions)
        self.seq = 0
        self.plans = {}                       # (year, block start) -> {'weeks': {week: choice}, 'policy', 'made'}
        self.decisions = {}                   # id -> decision (pending, accepted, declined, withdrawn, closed)
        self.notices = []                     # information only, newest last
        self.log = []                         # (year, week, what the player did)

    # ---- reading -------------------------------------------------------------------------------------------------
    def controls(self, gid):
        return self.status == 'active' and gid == self.golfer_id

    def plan_for(self, year, week):
        return self.plans.get((year, block_start(week)))

    def choice(self, year, week):
        p = self.plan_for(year, week)
        return p['weeks'].get(week) if p else None

    def policy(self, year, week):
        p = self.plan_for(year, week)
        return p['policy'] if p else None

    def accepts(self, year, week, series):
        """Whether the player's policy for this period takes a rule-selected place (or tries qualifying)."""
        pol = self.policy(year, week)
        if pol is None:
            return False
        return pol['qualifying'] == 'enter' if entrant_decides(series) else pol['selected'] == 'accept'

    def fallback(self, year, week):
        ch = self.choice(year, week)
        return ch.get('fallback') if ch and ch.get('kind') == 'event' else None

    def pending(self, kinds=None):
        return [d for d in self.decisions.values() if d['status'] == 'pending' and (kinds is None or d['kind'] in kinds)]

    def due(self, year, week):
        """Pending decisions that must be answered before this week is played."""
        return [d for d in self.pending() if d['deadline'] is None or tuple(d['deadline']) <= (year, week)]

    # ---- writing (every change bumps the version) --------------------------------------------------------------------
    def _bump(self):
        self.version += 1

    def note(self, year, week, kind, text, key=None):
        if key is not None and any(n.get('key') == key for n in self.notices):
            return                                      # (said once)
        self.seq += 1
        self.notices.append({'id': f'N{self.seq}', 'year': year, 'week': week, 'kind': kind, 'text': text, 'key': key})
        del self.notices[:-NOTICES_KEPT]
        self._bump()

    def ensure(self, kind, key, year, week, deadline, payload, text, options):
        """The pending decision with this key, created if there is none (never twice)."""
        for d in self.decisions.values():
            if d['key'] == key and d['status'] == 'pending':
                return d
        self.seq += 1
        d = {'id': f'D{self.seq}', 'kind': kind, 'key': key, 'status': 'pending', 'created': [year, week],
             'deadline': None if deadline is None else list(deadline), 'payload': dict(payload), 'text': text,
             'options': list(options), 'resolved': None}
        self.decisions[d['id']] = d
        self._bump()
        return d

    def resolve(self, d, status, year, week, text):
        d['status'] = status
        d['resolved'] = {'at': [year, week], 'text': text}
        self._bump()

    # ---- the engine's hooks ------------------------------------------------------------------------------------------
    def staff_offer(self, season, kind, person, g, why, when, arrangement=None):
        """A coach or caddie approaches the controlled golfer: a pending offer, with nothing ended, assigned, charged or
        reserved. Open until the end of the planning period it was made in."""
        y, w = when
        deadline = (y, min(52, block_start(max(1, w)) + BLOCK)) if block_start(max(1, w)) + BLOCK <= 52 else None
        if kind == 'coach':
            fee = getattr(person, 'fee', 0.0)
            terms = (f'a share of future prize money ({_share_text()})' if arrangement == 'share'
                     else f'a fee of ${fee:,.0f} a year')
            text = (f'Coach {person.name} (reputation {person.reputation:.0f}) offers to coach you for {terms}. '
                    f'Why: {why}.')
            payload = {'staff': person.id, 'name': person.name, 'arrangement': arrangement, 'fee': fee, 'why': why,
                       'when': [y, w]}
            return self.ensure('coach_offer', ('coach', person.id, y), y, w, deadline, payload, text,
                               ('accept', 'decline'))
        text = (f'Caddie {person.name} (reputation {person.reputation:.0f}) offers to carry your bag for '
                f'${person.weekly_fee:,.0f} a week when you play. Why: {why}.')
        payload = {'staff': person.id, 'name': person.name, 'weekly_fee': person.weekly_fee, 'why': why, 'when': [y, w]}
        return self.ensure('caddie_offer', ('caddie', person.id, y), y, w, deadline, payload, text, ('accept', 'decline'))

    def job_offer(self, year, week, weeks_blocked):
        """The work pathway would put the controlled golfer in a job: the player decides, before this week."""
        text = (f'For {weeks_blocked} weeks you could not afford any event you were eligible for, and there is no family '
                'money left. You can take a part-time job and keep playing as an amateur (the ordinary salary, living '
                'costs and schedule of a working amateur; less time to train) or keep trying full-time.')
        return self.ensure('job', ('job', year, block_start(week)), year, week, (year, week),
                           {'weeks_blocked': weeks_blocked}, text, ('accept', 'decline'))


def _share_text():
    from .staff import SCOUT_SHARE
    return f'{SCOUT_SHARE:.0%} of prize money'


# ---- shared validation (the same rule services as the AI) ---------------------------------------------------------------

def edition(season, year, event_id):
    for e in season.cal.editions(year):
        if e.event_id == event_id:
            return e
    return None


def city_of(season, year, event_id):
    return season.venues(year)[event_id][0].city


def injured_until(season, gid, year, week):
    """The absolute week the golfer is injured until, if injured in this week (else None)."""
    inj = season.injured.get(gid)
    if inj is not None and season.abs_week(year, week) < inj[0]:
        return inj[0]
    return None


def entry_cost(season, g, year, ed):
    """What entering costs the golfer (Season.trip_cost: travel and fees, plus a caddie's weekly fee): the cost the
    weekly entries compare with spendable funds."""
    return season.trip_cost(g, ed.series, city_of(season, year, ed.event_id))


def explain_ineligible(season, g, s, week):
    """Why Season.eligible says no, in the rule's own terms (the same branches)."""
    from .calendar import TOUR_BY_KEY
    t = TOUR_BY_KEY.get(s.tour)
    tname = t.name if t else s.tour
    if s.category == 'national_open' and s.tier >= 2:
        return f'open to professionals, and to amateurs from {s.host_country} in the amateur top 300'
    if s.tier == 1:
        return ('Premier Tour events take Premier and Challenger members, the world top 500 and current winners; '
                'amateurs only in the amateur top 25')
    if s.tier == 2:
        return f'professionals only: Premier and Challenger members, and regional or mini-tour players from {tname}\'s countries'
    if s.tier == 3:
        return f'professionals only: members of tours up to Regional, or professionals from {tname}\'s countries'
    if s.tier == 4:
        return f'professionals only: {tname} members, players from its countries and mini-tour players of its region'
    if s.tier == 5:
        return f'only for {tname} teams'
    if s.tier == 6:
        return f'for amateurs of {tname}: its members, amateurs from or living in its countries, college golfers there'
    if s.tier == 8:
        return 'club professionals of the region only'
    return 'not open to this golfer'


def check_choice(season, g, year, week, ch):
    """('ok' | 'injured' | 'invalid', reason) for one week's choice, judged now by the engine's own rules."""
    if not isinstance(ch, dict):
        return 'invalid', 'no choice for this week'
    kind = ch.get('kind')
    inj = injured_until(season, g.id, year, week)
    if kind == 'rest':
        return 'ok', ''
    if kind not in ('train', 'event'):
        return 'invalid', 'unknown choice'
    if inj is not None:
        y, w = divmod(inj - 1, 52)
        return 'injured', f'injured until {date_text(season.first_year + y, w + 1)}: the golfer rests (injury rule)'
    if kind == 'train':
        if ch.get('category') not in CATEGORIES:
            return 'invalid', 'choose what to train'
        return 'ok', ''
    ed = edition(season, year, ch.get('event_id'))
    if ed is None or ed.week != week:
        return 'invalid', 'that event is not played in this week'
    if season.is_special(ed.series):
        return 'invalid', ('this event chooses its own field (selection, invitation or qualifying): it is covered by '
                           'the period\'s policy, not by entering')
    if (not g.tour and g.status != 'club_pro') or g.lifestyle == 'retired':
        return 'invalid', 'the golfer has no tour or series to enter events from'
    if not season.eligible(g, ed.series, week):
        return 'invalid', 'not eligible: ' + explain_ineligible(season, g, ed.series, week)
    cost = entry_cost(season, g, year, ed)
    money = season.spendable(g, year)
    if not (cost <= 0 or cost <= money):
        return 'invalid', f'cannot afford it: it costs ${cost:,.0f} and ${max(0.0, money):,.0f} is available for golf'
    fb = ch.get('fallback') or {}
    if fb.get('kind') not in ('train', 'rest') or (fb.get('kind') == 'train' and fb.get('category') not in CATEGORIES):
        return 'invalid', 'choose what to do if the entry is not accepted (train a category, or rest)'
    return 'ok', ''


def to_engine(ch):
    """A choice as the engine's weekly plan (action, training category)."""
    if ch['kind'] == 'event':
        fb = ch['fallback']
        return 'play', (fb['category'] if fb['kind'] == 'train' else None)
    if ch['kind'] == 'train':
        return 'train', ch['category']
    return 'rest', None


def install(season, year, w0):
    """The player's plan for a block as the engine's weekly plan (the AI planner never writes it)."""
    c = season.career
    p = c.plans.get((year, w0))
    if p is None:
        return
    season.plans[c.golfer_id] = {w: to_engine(ch) for w, ch in p['weeks'].items()}


# ---- gates --------------------------------------------------------------------------------------------------------------

def gate(season, cursor):
    """None if the next part may run; otherwise {'kind': 'decision', 'ids': [...]} (decisions may be created here)."""
    c = getattr(season, 'career', None)
    if c is None or c.status != 'active':
        return None
    y, w, ph = cursor['year'], cursor['week'], cursor['phase']
    g = season.g.get(c.golfer_id)
    if ph == 'start':
        return None                                    # 1 January runs; what it brings is checked before the week
    if g is None or g.lifestyle == 'retired':
        d = c.ensure('unsupported', ('unsupported', 'retired', y), y, w, None, {},
                     'The golfer is no longer playing. This build cannot continue a career past that point.',
                     ('return_to_ai',))
        return {'kind': 'decision', 'ids': [d['id']]}
    if ph == 'end':
        d = c.ensure('season_end', ('season_end', y), y, 52, None, {'year': y},
                     f'The {y} season is over. Season-end decisions (turning professional, college, residence, '
                     'retirement) and the season review are not playable in this build. Return the golfer to AI '
                     'control to let the world continue: the AI then makes those decisions for them.', ('return_to_ai',))
        return {'kind': 'decision', 'ids': [d['id']]}
    if ph == 'week':
        if g.status == 'pro' and g.lifestyle == 'full_time' and season.needs_paid_work(g, y):
            # (not reachable in this build's slice -- a newcomer is an amateur and status changes only in the winter --
            # but never bypassed silently: a professional short of money takes paid work weeks, not yet plannable)
            c.ensure('unsupported', ('unsupported', 'paid_work', y, block_start(w)), y, w, None, {},
                     'Your money would not cover three months of living costs. A professional in that position takes '
                     'paid work weeks, which this build cannot yet plan for a player. Return the golfer to AI control '
                     '(the AI then plans their weeks, paid work included).', ('return_to_ai',))
        if c.plan_for(y, w) is None:
            w0 = block_start(w)
            c.ensure('plan', ('plan', y, w0), y, w, (y, w0),
                     {'block': [y, w0]}, f'Plan weeks {w0}–{block_weeks(w0)[-1]} of {y}: an event, training or rest for '
                                        'each week, and what to do if selected or invited.', ('plan',))
    else:                                              # 'planned': revalidate this week's choice before it counts
        ch = c.choice(y, w)
        code, why = check_choice(season, g, y, w, ch)
        if code == 'injured' and ch.get('kind') != 'rest':
            c.note(y, w, 'injury', f'{date_text(y, w)}: {why}.', key=('injured', y, w))
        elif code == 'invalid':
            c.ensure('replan', ('replan', y, w), y, w, (y, w), {'week': [y, w], 'reason': why},
                     f'Your plan for {date_text(y, w)} can no longer be played: {why}. Choose again for this week.',
                     ('plan',))
    due = c.due(y, w)
    if due:
        return {'kind': 'decision', 'ids': [d['id'] for d in due]}
    return None


# ---- commands -----------------------------------------------------------------------------------------------------------

def new_career(season, cursor, action):
    """Take control of one genuine newcomer: a member of the junior class the normal entrant rules created for this
    season, picked by a seeded uniform draw over the class (no ability, potential or other hidden fact is read). No
    golfer is created; the person already exists in the world."""
    if getattr(season, 'career', None) is not None:
        raise CareerError('This world already has a career. One career per world in this build.')
    if cursor['phase'] != 'start' or cursor['week'] != 1:
        raise CareerError('A career starts on 1 January of a season, before anything of that season has been played.')
    y = cursor['year']
    cls = sorted(gid for gid, r in season.creations.get(y, {}).items()
                 if r.get('path') == 'junior' and gid in season.g and season.g[gid].lifestyle != 'retired')
    if not cls:
        raise CareerError(f'There is no newcomer class for {y} yet: a world creates its first one at the end of its '
                          'first season.')
    pick = random.Random(f'{season.seed}:career:newcomer:{y}').choice(cls)
    c = Career(pick, y, 1, {'kind': 'junior', 'class': y, 'class_size': len(cls),
                            'rule': 'a seeded uniform draw over the season\'s junior class'})
    g = season.g[pick]
    c.note(y, 1, 'start', f'You now control {g.name}, one of the {len(cls)} juniors who entered the world for {y}.')
    season.career = c
    return {'ok': True, 'golfer': pick, 'name': g.name}


def apply(season, cursor, action):
    """Run one command. Raises CareerError (nothing changed) or returns a result."""
    if not isinstance(action, dict) or action.get('schema') != SCHEMA:
        raise CareerError(f'Unsupported command format (this build reads schema {SCHEMA}).')
    t = action.get('type')
    if t == 'new_career':
        return new_career(season, cursor, action)
    c = getattr(season, 'career', None)
    if c is None:
        raise CareerError('This world has no career.')
    if getattr(c, 'format', None) != FORMAT:
        raise CareerError(f'This career was saved in format {getattr(c, "format", None)}; this build reads format {FORMAT}.')
    if action.get('version') is not None and action['version'] != c.version:
        raise StaleCareer('This form was drawn before the latest change to the career: nothing was changed. '
                          'Look at the career page again and choose from what it shows now.')
    if c.status != 'active':
        raise CareerError('This career has ended: the golfer is under AI control.')
    if t == 'plan_block':
        return _plan_block(season, c, cursor, action)
    if t == 'decide':
        return _decide(season, c, cursor, action)
    if t == 'end_control':
        return _end_control(season, c, cursor, action)
    raise CareerError(f'Unknown command {t!r}.')


def _now(cursor):
    return cursor['year'], (1 if cursor['phase'] == 'start' else cursor['week'])


def plannable(cursor):
    """The blocks the player may plan now: the current one (its weeks not yet played) and the next."""
    if cursor['phase'] == 'end':
        return []
    y, w = _now(cursor)
    w0 = block_start(w)
    return [(y, b) for b in (w0, w0 + BLOCK) if b <= 52]


def open_weeks(cursor, w0):
    """The weeks of a block that can still be (re)planned: not yet played. The current week can be re-planned until
    it is played."""
    y, w = _now(cursor)
    return [x for x in block_weeks(w0) if x >= w]


def _plan_block(season, c, cursor, action):
    try:
        y, w0 = int(action['block'][0]), int(action['block'][1])
    except (KeyError, TypeError, ValueError, IndexError):
        raise CareerError('Which planning period is this plan for?')
    if (y, w0) not in plannable(cursor):
        raise CareerError(f'Weeks {w0}–{block_weeks(w0)[-1]} of {y} cannot be planned now (only the current period and '
                          'the next).')
    g = season.g[c.golfer_id]
    weeks = open_weeks(cursor, w0)
    given = {int(k): v for k, v in (action.get('weeks') or {}).items()}
    errors = []
    for w in weeks:
        ch = given.get(w)
        code, why = check_choice(season, g, y, w, ch)
        if code == 'injured':
            errors.append(f'week {w}: {why}; choose rest')
        elif code == 'invalid':
            errors.append(f'week {w}: {why}')
    pol = action.get('policy') or {}
    if pol.get('selected') not in ('accept', 'decline'):
        errors.append('choose whether to accept a place if selected or invited in this period')
    if pol.get('qualifying') not in ('enter', 'skip'):
        errors.append('choose whether to enter qualifying in this period')
    if errors:
        raise CareerError('The plan was not saved: ' + '; '.join(errors) + '.')
    old = c.plans.get((y, w0))
    kept = {w: ch for w, ch in (old['weeks'].items() if old else ()) if w not in weeks}   # weeks already played
    clean = {}
    for w in weeks:
        ch = given[w]
        if ch['kind'] == 'event':
            fb = ch['fallback']
            clean[w] = {'kind': 'event', 'event_id': ch['event_id'],
                        'fallback': {'kind': fb['kind'], 'category': fb.get('category') if fb['kind'] == 'train' else None}}
        elif ch['kind'] == 'train':
            clean[w] = {'kind': 'train', 'category': ch['category']}
        else:
            clean[w] = {'kind': 'rest'}
    ny, nw = _now(cursor)
    c.plans[(y, w0)] = {'weeks': {**kept, **clean}, 'policy': {'selected': pol['selected'], 'qualifying': pol['qualifying']},
                        'made': [ny, nw]}
    for d in c.pending(('plan', 'replan')):
        key = d['key']
        if (d['kind'] == 'plan' and key == ('plan', y, w0)) or (d['kind'] == 'replan' and key[1] == y and key[2] in weeks):
            c.resolve(d, 'resolved', ny, nw, 'planned')
    if (y, w0) == plannable(cursor)[0]:
        install(season, y, w0)                         # the current block: the engine's plan follows at once
    c.log.append((ny, nw, f'planned weeks {weeks[0]}–{weeks[-1]} of {y}'))
    c._bump()
    return {'ok': True, 'block': [y, w0], 'weeks': weeks}


def _decide(season, c, cursor, action):
    d = c.decisions.get(action.get('decision'))
    if d is None:
        raise CareerError('No such decision.')
    if d['status'] != 'pending':
        at = d['resolved']['at'] if d['resolved'] else None
        raise CareerError(f'This decision was already {d["status"]}'
                          + (f' ({date_text(*at)})' if at else '') + ': nothing was changed.')
    answer = action.get('answer')
    if answer not in d['options']:
        raise CareerError(f'Choose one of: {", ".join(d["options"])}.')
    y, w = _now(cursor)
    g = season.g[c.golfer_id]
    if answer == 'return_to_ai':
        return _end_control(season, c, cursor, action)
    if d['kind'] == 'coach_offer':
        return _answer_coach(season, c, d, g, y, w, answer)
    if d['kind'] == 'caddie_offer':
        return _answer_caddie(season, c, d, g, y, w, answer)
    if d['kind'] == 'job':
        from . import work_pathway as WP
        if answer == 'accept':
            if not WP.tracked(g):
                c.resolve(d, 'withdrawn', y, w, 'no longer applies: the golfer is not a full-time amateur outside college')
                return {'ok': False, 'reason': d['resolved']['text']}
            WP.take_job(season, g, y, w, d['payload']['weeks_blocked'])
            c.resolve(d, 'accepted', y, w, 'took a part-time job')
        else:
            c.resolve(d, 'declined', y, w, 'kept trying full-time')
        c.log.append((y, w, f'{answer}ed the job'))
        return {'ok': True, 'answer': answer}
    raise CareerError('This decision is answered by planning (use the planner).')


def _answer_coach(season, c, d, g, y, w, answer):
    from . import staff as ST
    st = season.staff
    p = d['payload']
    coach = st.coaches.get(p['staff'])
    why = p['why']
    if answer == 'decline':
        if coach is not None:
            st.refuse(season, 'coach', coach, g, (y, w), 'coach', 'golfer', why, 'declined by the player')
        c.resolve(d, 'declined', y, w, 'declined')
        c.log.append((y, w, f'declined coach {p["name"]}'))
        return {'ok': True, 'answer': 'decline'}
    problem = None
    if coach is None or coach.status != 'active':
        problem = 'the coach is no longer working'
    else:
        students = sum(1 for cid in st.coach_of.values() if cid == coach.id)
        shares = sum(1 for gid, cid in st.coach_of.items() if cid == coach.id and st.deal.get(gid) == 'share')
        if st.coach(g.id) is coach:
            problem = 'they already coach you'
        elif students >= coach.capacity:
            problem = 'their book is now full'
        elif p['arrangement'] == 'share' and shares >= coach.capacity // 3:
            problem = 'they have no room left for share-of-winnings players'
        elif p['arrangement'] == 'fee' and coach.fee > ST.coach_budget(season, g, y):
            problem = f'their fee (${coach.fee:,.0f} a year) is more than you can now commit to a coach'
    if problem:
        c.resolve(d, 'withdrawn', y, w, f'could not be accepted: {problem}')
        return {'ok': False, 'reason': d['resolved']['text']}
    cur = st.coach(g.id)
    if cur is not None:                                 # one stint replaced, through the same staff functions
        st.end_coach(season, g.id, (y, w), f'left for an approach from {coach.name}', 'golfer')
    st.assign_coach(season, g, coach, p['arrangement'], (y, w), 'coach', why, 'accepted by the player')
    c.resolve(d, 'accepted', y, w, 'accepted')
    c.log.append((y, w, f'accepted coach {p["name"]}'))
    return {'ok': True, 'answer': 'accept'}


def _answer_caddie(season, c, d, g, y, w, answer):
    from . import staff as ST
    st = season.staff
    p = d['payload']
    k = st.caddies.get(p['staff'])
    why = p['why']
    if answer == 'decline':
        if k is not None:
            st.refuse(season, 'caddie', k, g, (y, w), 'caddie', 'golfer', why, 'declined by the player')
        c.resolve(d, 'declined', y, w, 'declined')
        c.log.append((y, w, f'declined caddie {p["name"]}'))
        return {'ok': True, 'answer': 'decline'}
    problem = None
    if k is None or k.status != 'active':
        problem = 'the caddie is no longer working'
    elif k.id in st._bags() and st.caddie(g.id) is not k:
        problem = 'they now carry another bag'
    elif st.caddie(g.id) is k:
        problem = 'they already carry your bag'
    elif k.weekly_fee * max(1, season.target_events(g)) > ST.caddie_budget(season, g, y):
        problem = f'their fee (${k.weekly_fee:,.0f} a week) is more than you can now commit to a caddie'
    if problem:
        c.resolve(d, 'withdrawn', y, w, f'could not be accepted: {problem}')
        return {'ok': False, 'reason': d['resolved']['text']}
    if st.caddie(g.id) is not None:
        st.end_caddie(season, g.id, (y, w), f'left for an approach from {k.name}', 'golfer')
    st.assign_caddie(season, g, k, (y, w), why, 'accepted by the player', started_by='caddie')
    c.resolve(d, 'accepted', y, w, 'accepted')
    c.log.append((y, w, f'accepted caddie {p["name"]}'))
    return {'ok': True, 'answer': 'accept'}


def _end_control(season, c, cursor, action):
    offers = c.pending(OFFER_KINDS)
    if offers:
        raise CareerError('Answer the pending offers first: ' + '; '.join(d['text'].split('.')[0] for d in offers) + '.')
    y, w = _now(cursor)
    for d in c.pending():
        c.resolve(d, 'closed', y, w, 'the golfer returned to AI control')
    c.status = 'ended'
    c.ended = (y, w)
    c.log.append((y, w, 'returned the golfer to AI control'))
    if cursor['phase'] in ('week', 'planned'):
        # the player's intents for the rest of this block are replaced by the AI's own plan (no side effects; a
        # week already prepared keeps the plan it was prepared with): see Season.replan_after_handback
        season.replan_after_handback(c.golfer_id, y, w, prepared=cursor['phase'] == 'planned')
    g = season.g.get(c.golfer_id)
    c.note(y, w, 'end', f'{g.name if g else "The golfer"} is back under AI control from {date_text(y, w)}.')
    return {'ok': True, 'ended': [y, w]}


# ---- views (plain data for any interface; never hidden potential, ceilings or development figures) -----------------------

ATTR_GROUPS = (('Long game', ('driving_accuracy', 'long_irons', 'mid_irons', 'ball_flight', 'striking_consistency', 'power')),
               ('Short game', ('wedges', 'chipping', 'bunker', 'recovery_play')),
               ('Putting', ('short_putting', 'lag_putting', 'green_reading', 'putting_consistency')),
               ('Mental', ('composure', 'resilience', 'management', 'focus')),
               ('Body', ('stamina', 'recovery_rate', 'injury_resistance')))


def choice_text(season, year, ch):
    if not ch:
        return 'not planned'
    if ch['kind'] == 'rest':
        return 'Rest'
    if ch['kind'] == 'train':
        return f'Train: {CATEGORY_LABEL[ch["category"]]}'
    ed = edition(season, year, ch['event_id'])
    fb = ch['fallback']
    return (f'Enter {ed.series.name if ed else ch["event_id"]} (if not accepted: '
            + ('rest' if fb['kind'] == 'rest' else f'train {CATEGORY_LABEL[fb["category"]].lower()}') + ')')


def week_options(season, g, year, week):
    """What the golfer could do in one week, judged now by the engine's rules: events open to entry (eligible or not,
    with the reason; cost and whether it is affordable now) and the week's rule-selected events (not entered: covered
    by the period's policy)."""
    from .calendar import TOUR_BY_KEY
    events, selected = [], []
    money = season.spendable(g, year)
    inj = injured_until(season, g.id, year, week)
    for ed in sorted((e for e in season.cal.editions(year) if e.week == week), key=lambda e: (e.series.tier, e.series.name)):
        s = ed.series
        city = city_of(season, year, ed.event_id)
        t = TOUR_BY_KEY.get(s.tour)
        row = {'event_id': ed.event_id, 'name': s.name, 'tier': s.tier, 'tour': t.name if t else s.tour, 'city': city,
               'country': _country(city), 'days': ','.join(str(d) for d in sorted(s.day_set))}
        if season.is_special(s):
            row['rule'] = ('qualifying: entrants decide (your period policy)' if entrant_decides(s)
                           else 'field chosen by the event\'s rules (your period policy decides whether to accept)')
            selected.append(row)
            continue
        ok = season.eligible(g, s, week) and (g.tour or g.status == 'club_pro')
        row['eligible'] = bool(ok)
        row['why'] = '' if ok else explain_ineligible(season, g, s, week)
        if ok:
            cost = entry_cost(season, g, year, ed)
            row['cost'] = round(cost, 2)
            row['affordable'] = cost <= 0 or cost <= money
            if not row['affordable']:
                row['why'] = f'costs ${cost:,.0f}; ${max(0.0, money):,.0f} available for golf'
        events.append(row)
    return {'week': week, 'events': events, 'selected': selected, 'money': round(money, 2),
            'injured_until': inj}


def _country(city):
    from .geography import CITY_BY_NAME
    c = CITY_BY_NAME.get(city)
    return c.country if c else ''


def view(season, cursor):
    """The career as the player may see it now (None without a career)."""
    from .calendar import TOUR_BY_KEY
    c = getattr(season, 'career', None)
    if c is None:
        return None
    g = season.g.get(c.golfer_id)
    y, w = _now(cursor)
    st = season.staff
    coach, caddie = st.coach(g.id), st.caddie(g.id)
    t = TOUR_BY_KEY.get(g.tour)
    attrs = [(label, [(k, round(g.attrs[k], 1)) for k in keys if k in g.attrs]) for label, keys in ATTR_GROUPS]
    inj = injured_until(season, g.id, y, w)
    golfer = {'id': g.id, 'name': g.name, 'country': g.country, 'age': g.age(y), 'status': g.status,
              'lifestyle': g.lifestyle, 'tour': t.name if t else (g.tour or '—'), 'tour_key': g.tour,
              'overall': round(g.overall, 1), 'attrs': attrs, 'prestige': round(season.player_prestige(g.id), 1),
              'world_rank': season.wr_pos.get(g.id), 'amateur_rank': season.am_pos.get(g.id),
              'funds': round(season.funds(g, y), 2), 'spendable': round(season.spendable(g, y), 2),
              'coach': coach.name if coach else None, 'coach_id': coach.id if coach else None,
              'caddie': caddie.name if caddie else None, 'caddie_id': caddie.id if caddie else None,
              'injured_until': inj, 'fatigue': round(season.fatigue.get(g.id, 0.0), 1),
              'played': len(season.played.get(y, {}).get(g.id, ())),
              'activity': dict(season.activity_counts.get(y, {}).get(g.id, {}))}
    blocks = []
    for (by, b0) in sorted(c.plans):
        if by == y and b0 + BLOCK > w - BLOCK:                # the current and next block, and the one just played
            p = c.plans[(by, b0)]
            blocks.append({'block': [by, b0], 'policy': dict(p['policy']), 'made': p['made'],
                           'weeks': [{'week': x, 'text': choice_text(season, by, p['weeks'].get(x)),
                                      'played': x < w or cursor['phase'] == 'end'} for x in block_weeks(b0)]})
    plan_now = None
    can = plannable(cursor) if c.status == 'active' else []
    for (py, p0) in can:
        if (py, p0) not in c.plans or any(d['kind'] in ('plan', 'replan') for d in c.pending()):
            plan_now = [py, p0]
            break
    return {'format': c.format, 'id': c.id, 'status': c.status, 'version': c.version, 'started': list(c.started),
            'ended': list(c.ended) if c.ended else None, 'entry': dict(c.entry), 'cursor': dict(cursor),
            'date': [y, w], 'golfer': golfer, 'blocks': blocks, 'plannable': [list(b) for b in can],
            'plan_next': plan_now,
            'pending': [dict(d) for d in c.pending()],
            'resolved': [dict(d) for d in c.decisions.values() if d['status'] != 'pending'][-10:],
            'notices': list(c.notices[-20:]), 'log': list(c.log[-20:])}


def planner(season, cursor, year, w0):
    """The planner for one block: each open week's options, the week's current choice and the period policy."""
    c = season.career
    g = season.g[c.golfer_id]
    if (year, w0) not in plannable(cursor):
        raise CareerError(f'Weeks {w0}–{block_weeks(w0)[-1]} of {year} cannot be planned now.')
    p = c.plans.get((year, w0))
    weeks = []
    for w in open_weeks(cursor, w0):
        o = week_options(season, g, year, w)
        o['current'] = p['weeks'].get(w) if p else None
        weeks.append(o)
    return {'block': [year, w0], 'weeks': weeks, 'policy': dict(p['policy']) if p else None,
            'categories': [(k, CATEGORY_LABEL[k]) for k in CATEGORIES], 'version': c.version}
