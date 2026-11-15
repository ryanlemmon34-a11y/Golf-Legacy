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
  revalidated after 1 January's and the block planning's effects, before any field, charge or result).
* The year end (docs/career/YEAR_END.md) is a sequence of committed stages: the season review and the annual intent
  (keep the golfer, switch to a newcomer, or end the career) before any of the winter runs; then, for a kept golfer,
  their winter career choice and staff, the winter's career decisions (the AI decides nothing for them), their
  residence, and the rest of the winter; after a switch (or a retirement), one of ten genuine juniors of the new class
  on 1 January, before anything of the new season runs. A golfer left behind is an AI golfer through the whole
  winter; the player never makes their winter choices.
* Offers to the controlled golfer (coach, caddie, a job from the work pathway) become pending decisions. Nothing is
  ended, assigned, charged or reserved until the player answers. Acceptance revalidates, then applies the same
  consequence as the AI path.
* Hidden potential never enters a view, decision, notice or explanation.
"""
from __future__ import annotations

import random
import copy

FORMAT = 2                  # the career record's format (2: control stints and winter answers; a format-1 record is
                            # read and upgraded, keeping its history as one stint); a newer one is refused, never guessed
SCHEMA = 1                  # the command payloads' schema
BLOCK = 4                   # planning period: the engine's four-week block (13 a season), not a calendar month
NOTICES_KEPT = 200
CATEGORIES = ('physical', 'long_game', 'short_game', 'putting', 'mental')
CATEGORY_LABEL = {'physical': 'Physical', 'long_game': 'Long game', 'short_game': 'Short game', 'putting': 'Putting',
                  'mental': 'Mental game'}
OFFER_KINDS = ('coach_offer', 'caddie_offer', 'job')
# Why the player's planned entry did or did not stand (Season._career_evidence; career.week_entry). One canonical text
# per reason; nothing else describes it.
ENTRY_TEXT = {
    'entered': 'your entry was accepted',
    'school_lineup': 'not selected for your school\'s college lineup',
    'field_full': 'the field filled with golfers ahead of you in its entry order',
    'quota': 'the places this field keeps for golfers like you (amateurs or visitors) were taken',
    'not_eligible': 'you are not eligible for it this week',
    'clash': 'it clashes with an event you are already committed to that week',
    'cost': 'you cannot pay for the trip',
    'superseded': 'a rule-selected place you accepted that week came first',
}
# The season's week classification (Season.ACCESS) as reason codes
ACCESS_CODES = {'played: first choice': 'played', 'played: alternative': 'played_alternative',
                'played: selected field': 'played_selected', 'injured': 'injured',
                'shut out: every acceptable field full': 'field_full',
                'not selected for the college lineup': 'school_lineup',
                'no suitable event scheduled': 'no_event', 'not eligible for the events scheduled': 'not_eligible',
                'could not afford any event': 'cost', 'declined the events on offer': 'declined',
                'chose to train': 'train', 'chose to rest': 'rest', 'chose to work': 'work'}
YEAR_END_KINDS = ('season_review', 'winter_career', 'winter_staff', 'winter_residence', 'choose_newcomer')
CANDIDATES = 10             # newcomers offered at a switch: a seeded sample of the new junior class, drawn once


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
        self.weekly_recaps = {}               # observation only, (year, week) -> played-week evidence
        # control stints, oldest first: who the player controlled, from when to when (None: still), and how chosen
        self.stints = [{'golfer_id': golfer_id, 'from': [year, week], 'to': None, 'how': dict(entry)}]
        self.winter = {}                      # year -> the player's year-end answers ('intent', 'career', 'staff', ...)

    # ---- reading -------------------------------------------------------------------------------------------------
    def controls(self, gid):
        return self.status == 'active' and gid == self.golfer_id

    def winter_answer(self, year, key='career'):
        """The player's year-end answer for `year` (None: not given -- the option that changes nothing applies)."""
        return self.winter.get(year, {}).get(key)

    def controlled_at(self, year, week):
        """The golfer the player controlled in that week (None: no one), from the stints."""
        for st in self.stints:
            if tuple(st['from']) <= (year, week) and (st['to'] is None or (year, week) <= tuple(st['to'])):
                return st['golfer_id']
        return None

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
        """A coach or caddie approaches the controlled golfer: a pending offer, with nothing ended, assigned or
        charged. A coach's offer holds its place in the coach's book until it is answered (staff.offer_reservations).
        Open until the end of the planning period it was made in."""
        y, w = when
        deadline = (y, min(52, block_start(max(1, w)) + BLOCK)) if block_start(max(1, w)) + BLOCK <= 52 else None
        if kind == 'coach':
            fee = getattr(person, 'fee', 0.0)
            terms = (f'a share of future prize money ({_share_text()})' if arrangement == 'share'
                     else f'a fee of ${fee:,.0f} a year')
            text = (f'Coach {person.name} (reputation {person.reputation:.0f}) offers to coach you for {terms}. '
                    f'Why: {why}.')
            payload = {'staff': person.id, 'name': person.name, 'arrangement': arrangement, 'fee': fee, 'why': why,
                       'when': [y, w], 'reserved': True}    # (holds a place in the coach's book: offer_reservations)
            return self.ensure('coach_offer', ('coach', person.id, y), y, w, deadline, payload, text,
                               ('accept', 'decline'))
        text = (f'Caddie {person.name} (reputation {person.reputation:.0f}) offers to carry your bag for '
                f'${person.weekly_fee:,.0f} a week when you play. Why: {why}.')
        payload = {'staff': person.id, 'name': person.name, 'weekly_fee': person.weekly_fee, 'why': why, 'when': [y, w],
                   'reserved': True}                   # (held for the player until answered: caddie_reservations)
        return self.ensure('caddie_offer', ('caddie', person.id, y), y, w, deadline, payload, text, ('accept', 'decline'))

    def job_offer(self, year, week, weeks_blocked):
        """The work pathway would put the controlled golfer in a job: the player decides, before this week."""
        text = (f'For {weeks_blocked} weeks you could not afford any event you were eligible for, and there is no family '
                'money left. You can take a part-time job and keep playing as an amateur (the ordinary salary, living '
                'costs and schedule of a working amateur; less time to train) or keep trying full-time.')
        return self.ensure('job', ('job', year, block_start(week)), year, week, (year, week),
                           {'weeks_blocked': weeks_blocked}, text, ('accept', 'decline'))


def upgrade(c):
    """A format-1 career record read by this build: its history kept as one control stint (ended if it ended), no
    winter answers. Nothing recorded is reinterpreted; an ended career stays ended. Returns the record."""
    if getattr(c, 'format', None) == 1:
        c.stints = [{'golfer_id': c.golfer_id, 'from': list(c.started),
                     'to': list(c.ended) if c.ended else None, 'how': dict(c.entry)}]
        c.winter = {}
        c.format = 2
    return c


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


def work_unavailable(season, g, year, planning=True, weeks=None):
    """Why the golfer may not plan a week of paid work ('' if they may): the engine's own rules -- a full-time
    professional whose funds would not cover three months of living costs (Season.needs_paid_work), or for whom the
    monthly plan's paid-work rule opens work this block (Season.block_work_case: money short and results not paying
    for their golf, or stuck -- unable to afford any trip or their committed costs), exactly as the AI planner
    judges it. Once planned, a work week stands (as the AI's planned work weeks do) even if a prize arrives
    meanwhile; it is paid WORK_WAGE, like any golfer's."""
    if g.status != 'pro' or g.lifestyle != 'full_time':
        return 'only a full-time professional takes paid work weeks (amateurs and part-time professionals have jobs)'
    if not planning or season.needs_paid_work(g, year):
        return ''
    if weeks and season.block_work_case(g, year, list(weeks))[0]:
        return ''
    return ('paid work is for a professional short of money (funds under three months of living costs, or unable '
            'to pay for their golf this period); yours is not')


def check_choice(season, g, year, week, ch, planning=False):
    """('ok' | 'injured' | 'invalid', reason) for one week's choice, judged now by the engine's own rules
    (planning: as the plan is made -- the block's open weeks, or True; otherwise as a planned week is about to be
    played)."""
    if not isinstance(ch, dict):
        return 'invalid', 'no choice for this week'
    kind = ch.get('kind')
    inj = injured_until(season, g.id, year, week)
    if kind == 'rest':
        return 'ok', ''
    if kind == 'work':                                 # paid work: the AI's rules decide who may; an injured golfer
        why = work_unavailable(season, g, year, bool(planning),     # does light work, as the AI's do
                               planning if isinstance(planning, (list, tuple)) else None)
        return ('invalid', why) if why else ('ok', '')
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
    if ch['kind'] == 'work':
        return 'work', None
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
    if c is None or c.status not in ('active', 'choosing'):
        return None
    y, w, ph = cursor['year'], cursor['week'], cursor['phase']
    g = season.g.get(c.golfer_id)
    if ph == 'start':
        if c.status == 'active' and (g is None or g.lifestyle == 'retired') and c.stints[-1]['from'][0] < y:
            # the golfer retired (the player's own winter choice) or died over the winter: their stint ends with the
            # season they played, and the player may pick a newcomer of this new class
            _end_stint(c, y - 1, 53)
            c.status = 'choosing'
            c.note(y, 1, 'stint', f'{g.name if g else "Your golfer"} is no longer playing. You can take control of one '
                                  f'of the juniors entering the world for {y}, or end the career.')
        if c.status == 'choosing':
            d = _newcomer_decision(season, c, y)
            return {'kind': 'decision', 'ids': [d['id']]} if d is not None else None
        return None                                    # 1 January runs; what it brings is checked before the week
    if c.status != 'active':
        return None
    if ph == 'end':
        return _year_end_gate(season, c, g, y)
    if g is None or g.lifestyle == 'retired':
        d = c.ensure('unsupported', ('unsupported', 'retired', y), y, w, None, {},
                     'The golfer is no longer playing. This build cannot continue a career past that point.',
                     ('return_to_ai',))
        return {'kind': 'decision', 'ids': [d['id']]}
    if ph == 'week':
        if c.plan_for(y, w) is None:
            w0 = block_start(w)
            c.ensure('plan', ('plan', y, w0), y, w, (y, w0),
                     {'block': [y, w0]}, f'Plan weeks {w0}–{block_weeks(w0)[-1]} of {y}: an event, training, rest '
                                        '(or, for a professional short of money, paid work) for each week, and what '
                                        'to do if selected or invited.', ('plan',))
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


# ---- the year end (docs/career/YEAR_END.md) ----------------------------------------------------------------------------

def _end_stint(c, year, week):
    if c.stints and c.stints[-1]['to'] is None:
        c.stints[-1]['to'] = [year, week]
    c._bump()


def winter_stage(season, c, year):
    """The year-end stage the career is at in season `year`'s winter (cursor at week 52 'end'), from what has run and
    what the player has answered: 'season_review', 'winter_choices', 'winter_residence' (a player stage, possibly
    already answered), or 'engine' (the next winter part runs)."""
    done = season.winter_parts_done(year)
    a = c.winter.get(year, {})
    if 'intent' not in a:
        return 'season_review'
    if done == 1:
        return 'winter_choices'
    if done == 2:
        return 'winter_residence'
    return 'engine'


def _year_end_gate(season, c, g, y):
    legacy = [d for d in c.pending() if d['kind'] == 'season_end']
    if legacy:                                         # (a stop recorded by an earlier build: answered as it was)
        return {'kind': 'decision', 'ids': [d['id'] for d in legacy]}
    offers = [d for d in c.pending(OFFER_KINDS)]
    a = c.winter.setdefault(y, {})
    stage = winter_stage(season, c, y)
    ids = []
    if stage == 'season_review':
        choices = [
            {'key': 'keep', 'label': f'Keep playing as {g.name}',
             'facts': {'detail': f'You make {g.name}\'s winter choices next (career path, staff, residence).'}},
            {'key': 'switch', 'label': 'Switch to a newcomer',
             'facts': {'detail': f'{g.name} returns to AI control now, before the winter: the AI makes all their winter '
                                 f'decisions. On 1 January {y + 1} you choose one of {CANDIDATES} juniors entering '
                                 'the world (they exist whoever you choose).'}},
            {'key': 'end_career', 'label': 'End the career',
             'facts': {'detail': 'Every golfer is under AI control from now on. This cannot be undone.'}}]
        d = c.ensure('season_review', ('season_review', y), y, 52, None, {'year': y, 'choices': choices},
                     f'The {y} season is over. Keep playing as {g.name}, switch to one of the juniors entering the '
                     f'world for {y + 1} (chosen on 1 January, after the winter; {g.name} carries on under AI control '
                     'through the winter), or end the career.', [x['key'] for x in choices])
        ids.append(d['id'])
    elif stage == 'winter_choices':
        from .careers import player_winter_options
        row = season.snapshots[y].get(g.id, {})
        if 'career' not in a:
            opts = player_winter_options(season, g, row, y)
            if len(opts) == 1:
                a['career'] = opts[0][0]
                c.note(y, 53, 'winter', f'Winter {y}: {opts[0][1]} (the only option for {g.name} this winter).',
                       key=('winter_career', y))
            else:
                d = c.ensure('winter_career', ('winter_career', y), y, 52, None,
                             {'year': y, 'choices': [{'key': k, 'label': lab, 'facts': f} for k, lab, f in opts]},
                             f'Winter {y}: what does {g.name} do next season?', tuple(k for k, _, _ in opts))
                ids.append(d['id'])
        if 'staff' not in a:
            opts = staff_options(season, g)
            if len(opts) == 1:
                a['staff'] = {}
            else:
                st = season.staff
                who = [f'coach {st.coach(g.id).name}' if st.coach(g.id) else None,
                       f'caddie {st.caddie(g.id).name}' if st.caddie(g.id) else None]
                co, ca = st.coach(g.id), st.caddie(g.id)
                labels = {'keep': 'Keep your team',
                          'let_go_coach': f'Let coach {co.name if co else ""} go',
                          'let_go_caddie': f'Let caddie {ca.name if ca else ""} go',
                          'let_go_both': 'Let both go'}
                d = c.ensure('winter_staff', ('winter_staff', y), y, 52, None,
                             {'year': y, 'coach': co.id if co else None, 'caddie': ca.id if ca else None,
                              'choices': [{'key': k, 'label': labels[k], 'facts': {}} for k in opts]},
                             f'Winter {y}: keep your team ({", ".join(x for x in who if x)}) for next season, or let '
                             'someone go? (Staff may still decide to move on themselves, as they always could.)', opts)
                ids.append(d['id'])
    elif stage == 'winter_residence':
        if 'residence' not in a:
            from . import residence as RES
            opt = None if g is None or g.lifestyle == 'retired' else \
                RES.player_move_option(season, g, y, season.snapshots[y])
            if opt is None:
                a['residence'] = 'stay'
            elif not opt['affordable']:
                a['residence'] = 'stay'
                c.note(y, 53, 'winter', f'Winter {y}: a move to {opt["country"]} would suit your golf, but its cost '
                                        f'(${opt["cost"]:,.0f}) is more than your own money allows: you stay.',
                       key=('winter_residence', y))
            else:
                choices = [{'key': 'stay', 'label': f'Stay in {opt["from"]}', 'facts': {}},
                           {'key': f'move:{opt["country"]}', 'label': f'Move to {opt["country"]}',
                            'facts': {'cost': opt['cost'], 'travel_saved': opt['travel_saved'], 'own': opt['own']}}]
                d = c.ensure('winter_residence', ('winter_residence', y), y, 52, None,
                             dict(opt, year=y, choices=choices),
                             f'Winter {y}: move to {opt["country"]}'
                             + (' (your homeland)' if opt['home'] else '') + ' or stay where you live? Moving costs '
                             f'${opt["cost"]:,.0f} from your own money; '
                             + (f'about ${opt["travel_saved"]:,.0f} a season less travel to your events.'
                                if opt['travel_saved'] >= 0 else
                                f'about ${-opt["travel_saved"]:,.0f} a season more travel to your events.'),
                             ('stay', f'move:{opt["country"]}'))
                ids.append(d['id'])
    if offers or ids:
        return {'kind': 'decision', 'ids': [d['id'] for d in offers] + ids}
    return None


def staff_options(season, g):
    st = season.staff
    has_coach, has_caddie = st.coach(g.id) is not None, st.caddie(g.id) is not None
    opts = ['keep']
    if has_coach:
        opts.append('let_go_coach')
    if has_caddie:
        opts.append('let_go_caddie')
    if has_coach and has_caddie:
        opts.append('let_go_both')
    return tuple(opts)


def candidates(season, year):
    """The newcomers offered at a switch for `year`: a seeded uniform sample of that year's junior class (genuine
    entrants the normal rules created; none is created here), at most CANDIDATES, sorted by id."""
    cls = sorted(gid for gid, r in season.creations.get(year, {}).items()
                 if r.get('path') == 'junior' and gid in season.g and season.g[gid].lifestyle != 'retired')
    if len(cls) <= CANDIDATES:
        return cls
    return sorted(random.Random(f'{season.seed}:career:candidates:{year}').sample(cls, CANDIDATES))


def _newcomer_decision(season, c, y):
    for d in c.pending(('choose_newcomer',)):
        return d
    if any(d['kind'] == 'choose_newcomer' and d['payload']['year'] == y for d in c.decisions.values()):
        return None
    ids = candidates(season, y)
    text = (f'Choose who to play as from {y}: one of {len(ids)} juniors entering the world this season '
            f'(a fixed draw from the class of {sum(1 for r in season.creations.get(y, {}).values() if r.get("path") == "junior")}; '
            'the others carry on under AI control), or end the career.')
    choices = [{'key': str(i), 'label': season.g[i].name, 'facts': candidate_facts(season, season.g[i], y)}
               for i in ids]
    choices.append({'key': 'end_career', 'label': 'End the career',
                    'facts': {'detail': 'Every golfer is under AI control from now on. This cannot be undone.'}})
    return c.ensure('choose_newcomer', ('choose_newcomer', y), y, 1, None,
                    {'year': y, 'candidates': ids, 'choices': choices}, text, [x['key'] for x in choices])


def candidate_facts(season, g, year):
    """What the player may see of a newcomer: their public profile as it stands (no potential, ceilings, peak age,
    aging rate or any other hidden fact)."""
    from .calendar import TOUR_BY_KEY
    t = TOUR_BY_KEY.get(g.tour)
    return {'id': g.id, 'name': g.name, 'country': g.country, 'age': g.age(year), 'status': g.status,
            'lifestyle': g.lifestyle, 'tour': t.name if t else (g.tour or None),
            'overall': round(g.overall, 1),
            'attrs': [(label, [(k, round(g.attrs[k], 1)) for k in keys if k in g.attrs]) for label, keys in ATTR_GROUPS],
            'funds': round(g.cash + g.backing + g.backer_funds, 2)}


def _answer_year_end(season, c, d, cursor, answer):
    y, w = _now(cursor)
    kind = d['kind']
    yr = d['payload'].get('year', y)
    a = c.winter.setdefault(yr, {}) if kind != 'choose_newcomer' else None
    if kind == 'season_review':
        if cursor['phase'] != 'end' or season.winter_parts_done(yr):
            raise CareerError('The season review can only be answered before the winter starts.')
        if answer == 'end_career':
            return _end_control(season, c, cursor, {})
        offers = c.pending(OFFER_KINDS)
        if offers:
            raise CareerError('Answer the pending offers first: ' + '; '.join(x['text'].split('.')[0] for x in offers)
                              + '.')
        a['intent'] = answer
        c.resolve(d, 'resolved', y, w, answer)
        g = season.g.get(c.golfer_id)
        if answer == 'switch':
            _end_stint(c, yr, 52)
            c.status = 'choosing'
            c.log.append((y, w, f'switching: {g.name if g else c.golfer_id} returns to AI control for the winter'))
            c.note(y, w, 'stint', f'{g.name if g else "Your golfer"} carries on under AI control from the end of {yr}. '
                                  f'On 1 January {yr + 1} you choose one of the juniors entering the world.')
        else:
            c.log.append((y, w, f'kept {g.name if g else c.golfer_id} for {yr + 1}'))
        return {'ok': True, 'answer': answer}
    if kind == 'winter_career':
        if season.winter_parts_done(yr) != 1:
            raise CareerError('This winter choice is no longer open.')
        a['career'] = answer
        label = next((x['label'] for x in d['payload']['choices'] if x['key'] == answer), answer)
        c.resolve(d, 'resolved', y, w, label)
        c.log.append((y, w, f'winter {yr}: {label}'))
        return {'ok': True, 'answer': answer}
    if kind == 'winter_staff':
        if season.winter_parts_done(yr) != 1:
            raise CareerError('This winter choice is no longer open.')
        a['staff'] = {'coach': 'let_go' if answer in ('let_go_coach', 'let_go_both') else 'keep',
                      'caddie': 'let_go' if answer in ('let_go_caddie', 'let_go_both') else 'keep'}
        c.resolve(d, 'resolved', y, w, answer)
        c.log.append((y, w, f'winter {yr}: staff {answer.replace("_", " ")}'))
        return {'ok': True, 'answer': answer}
    if kind == 'winter_residence':
        if season.winter_parts_done(yr) != 2:
            raise CareerError('This winter choice is no longer open.')
        a['residence'] = answer
        c.resolve(d, 'resolved', y, w, answer)
        c.log.append((y, w, f'winter {yr}: residence {answer}'))
        return {'ok': True, 'answer': answer}
    if kind == 'choose_newcomer':
        if cursor['phase'] != 'start':
            raise CareerError('A newcomer is chosen on 1 January, before anything of the season runs.')
        if answer == 'end_career':
            c.resolve(d, 'resolved', y, w, 'ended the career')
            c.status = 'ended'
            c.ended = (y, 1)
            c.log.append((y, w, 'ended the career'))
            c.note(y, 1, 'end', 'The career has ended. Every golfer is under AI control.')
            return {'ok': True, 'answer': answer}
        pick = int(answer)
        g = season.g.get(pick)
        if g is None or g.lifestyle == 'retired':
            raise CareerError('That golfer is no longer playing: choose another.')
        c.golfer_id = pick
        c.status = 'active'
        c.stints.append({'golfer_id': pick, 'from': [y, 1], 'to': None,
                         'how': {'kind': 'junior', 'class': y, 'candidates': len(d['payload']['candidates']),
                                 'rule': 'chosen by the player from a seeded sample of the season\'s junior class'}})
        c.resolve(d, 'resolved', y, w, f'chose {g.name}')
        c.log.append((y, w, f'took control of {g.name}'))
        c.note(y, 1, 'start', f'You now control {g.name}, one of the juniors entering the world for {y}.')
        return {'ok': True, 'answer': answer, 'golfer': pick, 'name': g.name}
    raise CareerError('Unknown year-end decision.')


# ---- commands -----------------------------------------------------------------------------------------------------------

def _start_class(season, y):
    return sorted(gid for gid, r in season.creations.get(y, {}).items()
                  if r.get('path') == 'junior' and gid in season.g and season.g[gid].lifestyle != 'retired')


def start_view(season, cursor):
    """Before a career: the newcomers the player may start as now (docs/career/INITIAL_SELECTION.md), or None when no
    career can start here (a career exists, the cursor is not a season's 1 January, or there is no junior class yet).
    The candidates are career.candidates(season, year) -- the same seeded sample of the genuine class as the annual
    newcomer choice -- with the same public facts. Read only: no golfer is created, no draw of the world is made."""
    if getattr(season, 'career', None) is not None:
        return None
    if cursor['phase'] != 'start' or cursor['week'] != 1:
        return None
    y = cursor['year']
    cls = _start_class(season, y)
    if not cls:
        return None
    ids = candidates(season, y)
    choices = [{'key': str(i), 'label': season.g[i].name, 'facts': candidate_facts(season, season.g[i], y)}
               for i in ids]
    return {'year': y, 'cursor': dict(cursor), 'class_size': len(cls), 'options': [x['key'] for x in choices],
            'choices': choices, 'candidates': [dict(x['facts']) for x in choices],
            'text': f'Choose who to play as from {y}: one of {len(ids)} juniors entering the world this season (a fixed '
                    f'draw from the class of {len(cls)}; the others carry on under AI control).'}


def new_career(season, cursor, action):
    """Take control of one genuine newcomer of this season's junior class (the normal entrant rules created it; no
    golfer is created here; no ability, potential or other hidden fact is read):
    * {'golfer': '<id>'}: the player's choice among start_view's candidates (the same seeded sample as the annual
      newcomer choice);
    * no 'golfer' (the original command): a seeded uniform draw over the whole class, as before."""
    if getattr(season, 'career', None) is not None:
        raise CareerError('This world already has a career. One career per world in this build.')
    if cursor['phase'] != 'start' or cursor['week'] != 1:
        raise CareerError('A career starts on 1 January of a season, before anything of that season has been played.')
    y = cursor['year']
    cls = _start_class(season, y)
    if not cls:
        raise CareerError(f'There is no newcomer class for {y} yet: a world creates its first one at the end of its '
                          'first season.')
    if 'golfer' in action:
        ids = candidates(season, y)
        if not isinstance(action['golfer'], str) or action['golfer'] not in [str(i) for i in ids]:
            raise CareerError('Choose one of the newcomers offered for this season.')
        pick = int(action['golfer'])
        entry = {'kind': 'junior', 'class': y, 'class_size': len(cls), 'candidates': len(ids),
                 'rule': 'chosen by the player from a seeded sample of the season\'s junior class'}
    else:
        pick = random.Random(f'{season.seed}:career:newcomer:{y}').choice(cls)
        entry = {'kind': 'junior', 'class': y, 'class_size': len(cls),
                 'rule': 'a seeded uniform draw over the season\'s junior class'}
    c = Career(pick, y, 1, entry)
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
    if getattr(c, 'format', None) == 1:
        upgrade(c)
    if getattr(c, 'format', None) != FORMAT:
        raise CareerError(f'This career was saved in format {getattr(c, "format", None)}; this build reads format {FORMAT}.')
    if action.get('version') is not None and action['version'] != c.version:
        raise StaleCareer('This form was drawn before the latest change to the career: nothing was changed. '
                          'Look at the career page again and choose from what it shows now.')
    if c.status == 'choosing':
        d = c.decisions.get(action.get('decision'))
        if t != 'decide' or d is None or d['kind'] != 'choose_newcomer':
            raise CareerError('Choose a newcomer (or end the career) first.')
        return _decide(season, c, cursor, action)
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
        code, why = check_choice(season, g, y, w, ch, planning=weeks)
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
        elif ch['kind'] == 'work':
            clean[w] = {'kind': 'work'}
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
    g = season.g.get(c.golfer_id)
    if answer == 'return_to_ai':
        return _end_control(season, c, cursor, action)
    if d['kind'] in YEAR_END_KINDS:
        return _answer_year_end(season, c, d, cursor, answer)
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
            problem = 'their book is now full' + ('' if p.get('reserved') else
                                                  ' (an offer made by an earlier build, which held no place for it)')
        elif p['arrangement'] == 'share' and shares >= coach.capacity // 3:
            problem = 'they have no room left for share-of-winnings players' + ('' if p.get('reserved') else
                                                  ' (an offer made by an earlier build, which held no place for it)')
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
        problem = 'they now carry another bag' + ('' if p.get('reserved') else
                                                  ' (an offer made by an earlier build, which did not hold them for you)')
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
    _end_stint(c, y, w)
    c.log.append((y, w, 'returned the golfer to AI control'))
    if cursor['phase'] in ('week', 'planned'):
        # the player's intents for the rest of this block are replaced by the AI's own plan (no side effects; a
        # week already prepared keeps the plan it was prepared with): see Season.replan_after_handback
        season.replan_after_handback(c.golfer_id, y, w, prepared=cursor['phase'] == 'planned')
    g = season.g.get(c.golfer_id)
    c.note(y, w, 'end', f'{g.name if g else "The golfer"} is back under AI control from {date_text(y, w)}.')
    return {'ok': True, 'ended': [y, w]}


# ---- views (plain data for any interface; never hidden potential, ceilings or development figures) -----------------------

# The same presentation taxonomy as every player profile; training categories are separate.
from .ratings import ATTRIBUTES as _RATED_ATTRIBUTES
ATTR_GROUPS = tuple((group, tuple(k for k, _, section, _ in _RATED_ATTRIBUTES if section == group))
                    for group in dict.fromkeys(section for _, _, section, _ in _RATED_ATTRIBUTES))


def choice_text(season, year, ch):
    if not ch:
        return 'not planned'
    if ch['kind'] == 'rest':
        return 'Rest'
    if ch['kind'] == 'work':
        return 'Paid work'
    if ch['kind'] == 'train':
        return f'Train: {CATEGORY_LABEL[ch["category"]]}'
    ed = edition(season, year, ch['event_id'])
    fb = ch['fallback']
    return (f'Enter {ed.series.name if ed else ch["event_id"]} (if not accepted: '
            + ('rest' if fb['kind'] == 'rest' else f'train {CATEGORY_LABEL[fb["category"]].lower()}') + ')')


def week_options(season, g, year, week, weeks=None):
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
    from .finance import WORK_WAGE
    w0 = block_start(week)
    why = work_unavailable(season, g, year, weeks=[x for x in block_weeks(w0) if x >= week] if weeks is None else weeks)
    return {'week': week, 'events': events, 'selected': selected, 'money': round(money, 2),
            'injured_until': inj, 'work': {'available': not why, 'wage': WORK_WAGE, 'why': why}}


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
              'overall': round(g.overall, 1), 'overall_exact': round(g.overall, 3),
              'attrs_exact': {k: round(x, 3) for k, x in g.attrs.items()}, 'attrs': attrs, 'prestige': round(season.player_prestige(g.id), 1),
              'world_rank': season.wr_pos.get(g.id), 'amateur_rank': season.am_pos.get(g.id),
              'funds': round(season.funds(g, y), 2), 'spendable': round(season.spendable(g, y), 2),
              'coach': coach.name if coach else None, 'coach_id': coach.id if coach else None,
              'caddie': caddie.name if caddie else None, 'caddie_id': caddie.id if caddie else None,
              'injured_until': inj, 'fatigue': round(season.fatigue.get(g.id, 0.0), 4),
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
    from .career_context import context
    return {'context': context(season, g, y, w), 'format': c.format, 'id': c.id, 'status': c.status, 'version': c.version, 'started': list(c.started),
            'ended': list(c.ended) if c.ended else None, 'entry': dict(c.entry), 'cursor': dict(cursor),
            'date': [y, w], 'golfer': golfer, 'blocks': blocks, 'plannable': [list(b) for b in can],
            'plan_next': plan_now,
            'pending': [dict(d) for d in c.pending()],
            'resolved': [dict(d) for d in c.decisions.values() if d['status'] != 'pending'][-10:],
            'notices': list(c.notices[-20:]), 'log': list(c.log[-20:]),
            'recaps': period_recaps(c), 'readiness': readiness(season, g, y, w),
            'stints': [stint_view(season, st) for st in getattr(c, 'stints', [])],
            'year_end': year_end_view(season, cursor)}


def stint_view(season, st):
    g = season.g.get(st['golfer_id'])
    return {'golfer_id': st['golfer_id'], 'name': g.name if g else None, 'from': list(st['from']),
            'to': list(st['to']) if st['to'] else None, 'how': dict(st['how'])}


def season_review(season, c, gid, year):
    """One golfer's season as the career recorded it (the weekly recaps of the weeks the player controlled them)
    and as the world stands now. Every key is always present; a figure the records cannot give is None."""
    from .calendar import TOUR_BY_KEY
    g = season.g.get(gid)
    weeks = [r for (y, w), r in sorted(getattr(c, 'weekly_recaps', {}).items())
             if y == year and r.get('golfer_id', c.controlled_at(y, w)) == gid]
    events = [e for r in weeks for e in r['events']]
    placed = [e for e in events if e['position'] is not None]
    best = min(placed, key=lambda e: e['position']) if placed else None
    acts = {}
    for r in weeks:
        acts[r['activity']] = acts.get(r['activity'], 0) + 1
    prizes = [e['prize'] for e in events if e['prize'] is not None]
    led = season.ledgers.get(year, {}).get(gid)
    t = TOUR_BY_KEY.get(g.tour) if g else None
    first = _as_dict(weeks[0]['before']) if weeks else None
    return {'year': year, 'golfer_id': gid, 'name': g.name if g else None, 'age': g.age(year) if g else None,
            'status': g.status if g else None, 'lifestyle': g.lifestyle if g else None,
            'tour': t.name if t else (g.tour if g else None),
            'recorded_weeks': len(weeks), 'complete': len(weeks) == 52,
            'events': len(events), 'wins': sum(1 for e in events if e['position'] == 1),
            'top10': sum(1 for e in events if e['position'] is not None and e['position'] <= 10),
            'missed_cuts': sum(1 for e in events if e['position'] is None),
            'best_finish': {'position': best['position'], 'event': best['name'], 'tied': best['tied']} if best else None,
            'prize_money': round(sum(prizes), 2) if events else 0.0,
            'income': round(led.income, 2) if led is not None else None,
            'activity': acts,
            'overall_start': first['overall'] if first else None,
            'overall_now': round(g.overall, 3) if g else None,
            'world_rank': season.wr_pos.get(gid), 'amateur_rank': season.am_pos.get(gid),
            'funds': round(season.funds(g, year), 2) if g else None}


def _as_dict(x):
    return x if isinstance(x, dict) else None


def year_end_view(season, cursor):
    """The year end as the player may see it now (docs/career/YEAR_END.md), or None outside it: the stage, the
    season under review, the decision now open (its choices with their facts), the answers already given, the
    newcomers on offer. Read only."""
    c = getattr(season, 'career', None)
    if c is None:
        return None
    y, w, ph = cursor['year'], cursor['week'], cursor['phase']
    if ph == 'end' and c.status == 'active':
        yr = y
        stage = winter_stage(season, c, y)
        gid = c.golfer_id
    elif ph == 'start' and c.status == 'choosing':
        yr, stage = y - 1, 'choose_newcomer'
        gid = c.stints[-1]['golfer_id'] if c.stints else c.golfer_id
    elif ph == 'end' and c.status == 'choosing':
        yr, stage = y, 'winter_ai'                       # (switched: the AI runs the former golfer's winter)
        gid = c.stints[-1]['golfer_id'] if c.stints else c.golfer_id
    else:
        return None
    if stage == 'engine':
        stage = 'winter_running'
    pend = [d for d in c.pending(YEAR_END_KINDS)]
    return {'year': yr, 'stage': stage, 'winter_parts_done': season.winter_parts_done(yr), 'version': c.version,
            'review': season_review(season, c, gid, yr),
            'decisions': [{'id': d['id'], 'kind': d['kind'], 'text': d['text'], 'options': list(d['options']),
                           'choices': copy.deepcopy(d['payload'].get('choices', []))} for d in pend],
            'offers': [d['id'] for d in c.pending(OFFER_KINDS)],
            'answers': copy.deepcopy(c.winter.get(yr, {})),
            'candidates': [dict(x['facts']) for x in pend[0]['payload']['choices'] if x['key'] != 'end_career']
            if pend and pend[0]['kind'] == 'choose_newcomer' else None}


def planner(season, cursor, year, w0):
    """The planner for one block: each open week's options, the week's current choice and the period policy."""
    c = season.career
    g = season.g[c.golfer_id]
    if (year, w0) not in plannable(cursor):
        raise CareerError(f'Weeks {w0}–{block_weeks(w0)[-1]} of {year} cannot be planned now.')
    p = c.plans.get((year, w0))
    weeks = []
    ow = open_weeks(cursor, w0)
    for w in ow:
        o = week_options(season, g, year, w, ow)
        o['current'] = p['weeks'].get(w) if p else None
        weeks.append(o)
    return {'block': [year, w0], 'weeks': weeks, 'policy': dict(p['policy']) if p else None,
            'categories': [(k, CATEGORY_LABEL[k]) for k in CATEGORIES], 'version': c.version}


# ---- recorded career feedback (observation only, never read by simulation decisions) -------------------------------

def _snapshot(season, g, year):
    from .ratings import ATTRIBUTE_KEYS
    return {'overall': round(g.overall, 3), 'attrs': {k: round(g.attrs[k], 3) for k in ATTRIBUTE_KEYS},
            'fatigue': round(season.fatigue.get(g.id, 0.0), 4),
            'funds': round(season.funds(g, year), 2), 'cash': round(g.cash, 2)}


def begin_week_feedback(season, year, week):
    """Read only the controlled golfer, before the prepared week runs. No random draws or accumulator creation."""
    from . import development as D
    c = getattr(season, 'career', None)
    if c is None or c.status != 'active':
        return None
    g = season.g.get(c.golfer_id)
    if g is None:
        return None
    return {'before': _snapshot(season, g, year),
            'acc': list(season.dev_acc.get(year, {}).get(g.id, [0.0] * D.ACC_LEN)),
            'planned': choice_text(season, year, c.choice(year, week))}


def finish_week_feedback(season, year, week, before, event_ids):
    """Persist actual outcomes. Older saves start recording here; no invented historical deltas."""
    if before is None:
        return
    from . import development as D
    c = season.career
    g = season.g[c.golfer_id]
    rows = []
    series = {s.series_id: s for s in season.cal.series}
    for eid in event_ids:
        r = season.results[eid]
        ser = series.get(r.series_id)
        for site, finish in enumerate(r.finish):
            mine = next((x for x in finish if x[0] == g.id), None)
            if mine is None:
                continue
            _, pos, total = mine
            scores = getattr(r, 'scores', [])
            prizes = getattr(r, 'prizes', [])
            points = getattr(r, 'points', [])
            rounds = scores[site].get(g.id) if site < len(scores) else None
            rows.append({'id': eid, 'name': ser.name if ser else eid, 'position': pos, 'score': total,
                         'rounds': list(rounds) if rounds is not None else None,
                         'prize': prizes[site].get(g.id, 0.0) if site < len(prizes) else None,
                         'points': points[site].get(g.id, 0.0) if site < len(points) else None,
                         'field': len(finish), 'site': site, 'match_play': bool(ser and ser.match_play),
                         'tied': pos is not None and sum(1 for _, p, _ in finish if p == pos) > 1,
                         'finish_label': ('Winner' if pos == 1 else f'Finished {pos}' if pos is not None
                                          else 'Out before the final bracket' if ser and ser.match_play else 'Missed cut')})
    current = season.dev_acc.get(year, {}).get(g.id, [0.0] * D.ACC_LEN)
    development = {}
    for i, source in enumerate(D.SOURCES):
        development[source] = {
            'overall': round(current[D.OVERALL + i] - before['acc'][D.OVERALL + i], 4),
            'categories': {cat: round(current[i * 5 + j] - before['acc'][i * 5 + j], 4)
                           for j, cat in enumerate(D.CATS)}}
    action, category = season.plans.get(g.id, {}).get(week, ('rest', None))
    actual = season.week_activity.get(g.id, 'not recorded')
    rec = {'year': year, 'week': week, 'golfer_id': g.id, 'activity': actual, 'planned': before['planned'],
           'training_category': category if actual == 'train' else None,
           'before': before['before'], 'after': _snapshot(season, g, year), 'events': rows,
           'development': development,
           'development_recorded': bool(season.development and g.ceilings),
           'injuries': [dict(x) for x in season.injury_episodes(year).get(g.id, []) if x['week'] == week],
           'entry': week_entry(season, c, year, week)}
    if not hasattr(c, 'weekly_recaps'):
        c.weekly_recaps = {}
    c.weekly_recaps[(year, week)] = rec


def week_entry(season, c, year, week):
    """The canonical account of the controlled golfer's entry in one week, from evidence recorded when each decision
    was made (Season._career_evidence) -- never re-judged from today's ranking or state. Keys always present; a fact
    not recorded is None ('recorded': False for weeks played before this evidence was kept: then only the season's
    own access log speaks, without positions or cut-offs).

    {'year', 'week', 'recorded': bool,
     'choice': {'kind', 'event'} | None,           the player's plan for the week
     'access': str | None, 'access_code': str | None,   the week's classification (Season.ACCESS / ACCESS_CODES)
     'event': id | None, 'event_label': str | None, the event the player's entry was for
     'code': str | None, 'text': str | None,       why it stood or not (ENTRY_TEXT)
     'position': int | None, 'applicants': int | None, 'capacity': int | None, 'admitted': int | None,
                                                   the player's place in that event's entry order as decided
     'by': id | None,                              the rule-selected event that came first ('superseded')
     'entered': {'event', 'how', 'label'} | None,  what they played ('entry' | 'selected')
     'declined': [series id], 'clashed': [series id]}   rule-selected places not taken by policy / by a clash"""
    from . import event_labels as EL
    ev = getattr(c, 'entry_evidence', {}).get((year, week))
    ch = c.choice(year, week)
    out = {'year': year, 'week': week, 'recorded': ev is not None,
           'choice': {'kind': ch['kind'], 'event': ch.get('event_id')} if ch else None,
           'access': None, 'access_code': None, 'event': None, 'event_label': None, 'code': None, 'text': None,
           'position': None, 'applicants': None, 'capacity': None, 'admitted': None, 'by': None, 'entered': None,
           'declined': [], 'clashed': []}
    if ev is not None:
        for k in ('event', 'code', 'position', 'applicants', 'capacity', 'admitted', 'by'):
            out[k] = ev.get(k)
        out['access'] = ev.get('access')
        out['declined'] = list(ev.get('declined', []))
        out['clashed'] = list(ev.get('clashed', []))
        if ev.get('entered'):
            eid, how = ev['entered']
            out['entered'] = {'event': eid, 'how': how, 'label': EL.label(season.cal, _sid(eid))}
    else:                                              # (an older save: the season's own log, nothing more)
        gid = c.controlled_at(year, week) or c.golfer_id
        for wk, why, wanted, played in season.access_log.get(year, {}).get(gid, []):
            if wk == week:
                out['access'], out['event'] = why, wanted
                if played:
                    out['entered'] = {'event': played, 'how': None, 'label': EL.label(season.cal, _sid(played))}
    if out['access'] is not None:
        out['access_code'] = ACCESS_CODES.get(out['access'])
        if out['code'] is None and out['access_code'] in ('field_full', 'school_lineup'):
            out['code'] = out['access_code']           # (old saves: the log's own reason)
    if out['code'] is not None:
        out['text'] = ENTRY_TEXT.get(out['code'])
    if out['event'] is not None:
        out['event_label'] = EL.label(season.cal, _sid(out['event']))
    return out


def _sid(event_id):
    return event_id.split(':', 1)[1] if ':' in event_id else event_id


def period_recaps(c):
    """Public, copied period evidence. Partial old-save/unfinished blocks are explicitly identified."""
    grouped = {}
    for (year, week), rec in sorted(getattr(c, 'weekly_recaps', {}).items()):
        grouped.setdefault((year, block_start(week)), []).append(copy.deepcopy(rec))
    out = []
    for (year, first), rows in sorted(grouped.items(), reverse=True):
        sums = {}
        for row in rows:
            for source, change in row['development'].items():
                d = sums.setdefault(source, {'overall': 0.0, 'categories': {}})
                d['overall'] += change['overall']
                for cat, value in change['categories'].items():
                    d['categories'][cat] = d['categories'].get(cat, 0.0) + value
        for d in sums.values():
            d['overall'] = round(d['overall'], 4)
            d['categories'] = {k: round(v, 4) for k, v in d['categories'].items()}
        out.append({'year': year, 'start_week': first, 'end_week': min(52, first + BLOCK - 1),
                    'complete': [r['week'] for r in rows] == block_weeks(first), 'weeks': rows,
                    'before': rows[0]['before'], 'after': rows[-1]['after'], 'development': sums,
                    'recorded_weeks': [r['week'] for r in rows]})
    return out


def readiness(season, g, year, week):
    """Transparent fatigue guidance from the actual end-of-week formulas, never hidden potential."""
    f = season.fatigue.get(g.id, 0.0)
    inj = injured_until(season, g.id, year, week)
    rest = f * (0.40 + 0.30 * (1 - g.attrs['recovery_rate'] / 100)) if f else 0.0
    train = 0.85 * f + 0.02 * (1.4 - 0.8 * g.attrs['stamina'] / 100)
    rest, train = (x if x > 0.005 else 0.0 for x in (rest, train))
    enabled = bool(season.development and g.ceilings)
    label = 'Recovering from injury' if inj else 'Rest would help' if f > 0.2 else 'Ready to train or compete'
    detail = ('An injury currently prevents tournament entry. Follow the recovery window.' if inj else
              'Fatigue is above 20%; the engine reduces distance and increases physical tiredness during play. '
              'A rest week clears more fatigue than training.' if f > 0.2 else
              'Fatigue is at or below 20%, so there is no season-fatigue performance penalty. ' +
              ('Training builds skills; competition also develops the mental game.' if enabled else
               'Attribute development is not enabled for this golfer in this world.'))
    return {'label': label, 'detail': detail, 'fatigue': round(f, 4), 'performance_threshold': 0.2,
            'rest_after': round(rest, 4), 'train_after': round(train, 4), 'injured_until': inj,
            'forecast_note': 'Next-week fatigue if you only rest or train, with no tournament. Estimates are not an automatic plan.',
            'training_note': 'Weekly changes can be small. Recorded training gains are separated from natural maturing, '
                             'tournament development and injury changes.',
            'part_time_training': g.lifestyle == 'part_time', 'training_enabled': enabled}
