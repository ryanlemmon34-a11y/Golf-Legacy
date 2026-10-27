"""Shot-by-shot hole simulation.

How a hole is played
--------------------
1. Tee shot (par 4/5): the golfer picks a club (driver, 3-wood or long iron)
   by weighing distance against the hole's trouble. Distance comes from Power,
   direction from Driving Accuracy; wind, form, pressure and fatigue widen the
   spread; Ball-Flight Control fights wind and shapes around doglegs. Where the
   ball stops decides the lie: fairway, rough, fairway bunker, trees, water or
   out of bounds.
2. Approach: proximity to the hole depends on the distance (as the golfer's own
   club, so short hitters play longer clubs), the lie, and the right skill for
   that club (Long Irons, Mid/Short Irons or Wedges). The ball lands in 2-D
   around the aim point; the green's size and the pin position decide whether
   it holds the green, finds a bunker, the water or the rough.
   Par 5s: go for the green or lay up (Course Management, Aggression).
3. Around the green: Chipping or Bunker Play decide how close it finishes, with
   chances of duffing/thinning and of holing out. Short-sided misses are harder.
4. Trouble: from the trees, punch out or try the miracle shot (Recovery Play).
5. Putting: make chance by distance (Short Putting, Green Reading, green speed
   and slope); misses leave a second putt whose length depends on Lag Putting.

Throughout: Ball-Striking Consistency and Focus control mishits and mental
errors, Putting Consistency the day's putting form, Composure how much
pressure costs, Resilience how long a bad hole lingers, Stamina/Recovery how
much fatigue builds. Caddie skills and course familiarity give small,
bounded help in the situations they suit.

All randomness comes from the `random.Random` instance passed in, so a seed
reproduces every shot exactly.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import ratings as R
from .baseline import expected as baseline
from .golfer import neutral_caddie

TOUR_DRIVE = 298.0          # tour-average driver distance, the club-selection reference
RUNAWAY_GUARD = 60          # a hole this long means a bug: raise, never invent a score
_LIE_BASELINE = {'tee': 'tee', 'fairway': 'fairway', 'rough': 'rough', 'around': 'rough',
                 'fringe': 'fringe', 'sand': 'sand', 'fairway_bunker': 'fairway_bunker',
                 'trees': 'trees'}
# Tour-average make percentage by putt length (feet).
_MAKE = ((0.5, .999), (1, .997), (2, .99), (3, .955), (4, .88), (5, .77), (6, .66), (7, .57),
         (8, .50), (9, .44), (10, .40), (12, .32), (15, .23), (20, .15), (25, .10), (30, .07),
         (40, .045), (50, .03), (60, .022), (80, .012), (100, .008), (150, .004))
_MAKE_LOGIT = tuple((d, math.log(p / (1 - p))) for d, p in _MAKE)


@dataclass
class Conditions:
    wind_mph: float = 6.0
    rain: bool = False
    pin_difficulty: float = 0.45     # 0 centre pins .. 1 tucked tournament pins


def pin_sheet(course, cond, rng):
    """One hole location per green for a round, shared by everyone playing that round.

    Positions are (x, y) yards from the centre of the green: x along the line of play (+ = back),
    y across it (+ = right). Harder set-ups tuck pins nearer the edges.
    """
    depth = 0.32 + 0.5 * cond.pin_difficulty
    pins = []
    for h in course.holes:
        r = h.green_radius * depth * (0.7 + 0.3 * rng.random())
        a = rng.random() * 6.2832
        pins.append((r * math.cos(a), r * math.sin(a)))
    return tuple(pins)


@dataclass
class WeekForm:
    """A golfer's form for the whole tournament week (shared by all rounds)."""
    strike: float = 0.0              # log-dispersion offset (negative = sharper)
    putt: float = 0.0                # putting log-odds offset

    @staticmethod
    def draw(rng, golfer=None):
        """Week-to-week swings scale with the golfer's consistency: juniors swing far more than pros."""
        s_scale = p_scale = 1.0
        if golfer is not None:
            s_scale = R.interp(R.STRIKE_FORM_SD, golfer.attrs['striking_consistency']) / R.interp(R.STRIKE_FORM_SD, 75)
            p_scale = R.interp(R.PUTT_FORM_SD, golfer.attrs['putting_consistency']) / R.interp(R.PUTT_FORM_SD, 75)
        return WeekForm(rng.gauss(0, .06 * s_scale), rng.gauss(0, .11 * p_scale))


def _harder(excess, amp):
    """Course-condition effect: difficulty above neutral is magnified for weaker skills (amp > 1);
    conditions easier than neutral give everyone the same modest relief, so a weak golfer is
    still a weak golfer on an easy course."""
    return excess * amp if excess > 0 else excess * 0.5


def _sig(x):
    return 1.0 / (1.0 + math.exp(-x))


def _rayleigh(rng, mean):
    return mean * 0.7979 * math.sqrt(-2.0 * math.log(1.0 - rng.random()))


@dataclass
class RoundStats:
    score: int = 0
    to_par: int = 0
    holes: list = field(default_factory=list)
    fairways: int = 0
    fairway_att: int = 0
    gir: int = 0
    putts: int = 0
    three_putts: int = 0
    scramble_att: int = 0
    scramble_made: int = 0
    sand_att: int = 0
    sand_saves: int = 0
    penalties: int = 0
    drives: list = field(default_factory=list)
    eagles: int = 0
    birdies: int = 0
    pars: int = 0
    bogeys: int = 0
    doubles: int = 0
    worse: int = 0
    aces: int = 0
    mishits: int = 0
    sg_ott: float = 0.0
    sg_app: float = 0.0
    sg_arg: float = 0.0
    sg_putt: float = 0.0
    par_scores: dict = field(default_factory=lambda: {3: [0, 0], 4: [0, 0], 5: [0, 0]})


class Player:
    """A golfer's ratings compiled into shot parameters for one round."""

    def __init__(self, golfer, course, cond, caddie, rng, round_no=1, week_form=None):
        a, p = golfer.attrs, golfer.personality
        cad = caddie or neutral_caddie()
        wf = week_form or WeekForm.draw(rng, golfer)
        ip = R.interp
        self.golfer = golfer
        comm = 0.6 + 0.4 * R.norm(cad.skills['communication'])
        self.c_read = (cad.skills['green_reading'] - 50) / 50 * comm
        self.c_yard = (cad.skills['yardage'] - 50) / 50 * comm
        self.c_strat = (cad.skills['strategy'] - 50) / 50 * comm
        self.c_mental = (cad.skills['mental_support'] - 50) / 50 * comm
        fam = 1 - math.exp(-golfer.familiarity.get(course.name, 0) / 15.0)
        cfam = 1 - math.exp(-cad.familiarity.get(course.name, 0) / 15.0)
        cfam *= R.norm(cad.skills['course_knowledge']) * comm
        self.fam = fam + (1 - fam) * 0.5 * cfam

        firm = sum(h.green_firmness for h in course.holes) / 18 - (0.3 if cond.rain else 0)
        self.roll = 1 + (firm - 0.5) * 0.06 - (0.03 if cond.rain else 0)
        self.drive = ip(R.DRIVE_DISTANCE, a['power'])
        # Accuracy is angular: the same rating sprays a longer drive further offline.
        self.sigma = ip(R.DRIVE_SIGMA, a['driving_accuracy']) * self.drive / TOUR_DRIVE
        self.m_long = ip(R.APPROACH_MULT, a['long_irons'])
        self.m_mid = ip(R.APPROACH_MULT, a['mid_irons'])
        self.m_wedge = ip(R.APPROACH_MULT, a['wedges'])
        self.contact = ip(R.CONTACT_FLOOR, (a['mid_irons'] + a['wedges'] + a['striking_consistency']) / 3)
        self.m_chip = ip(R.SHORT_MULT, a['chipping'])
        self.m_sand = ip(R.SHORT_MULT, a['bunker'])
        self.chip_fail = ip(R.CHIP_FAIL, a['chipping'])
        self.sand_fail = ip(R.BUNKER_FAIL, a['bunker'])
        self.rec_ok = ip(R.RECOVERY_SUCCESS, a['recovery_play'])
        self.rough_skill = ip(R.ROUGH_SKILL, a['recovery_play'])
        self.lapse = ip(R.PUTT_LAPSE, a['putting_consistency'])
        self.putt_shift = ip(R.PUTT_SHORT_SHIFT, a['short_putting'])
        self.lag = ip(R.LAG_MULT, a['lag_putting'])
        self.read = ip(R.READ_SHIFT, a['green_reading'])
        self.read_n = R.norm(a['green_reading'])
        self.bfc = R.norm(a['ball_flight'])
        self.mishit = ip(R.MISHIT_RATE, a['striking_consistency'])
        self.mental = ip(R.MENTAL_ERROR, a['focus'])
        self.noise = ip(R.DECISION_NOISE, a['management']) * (1 - 0.2 * self.c_strat) * (1 - 0.2 * self.fam)
        self.composure = R.norm(a['composure'])
        self.mgmt = R.norm(a['management'])
        self.big_stage = (p['big_stage'] - 50) / 50
        self.aggr = (p['aggression'] - 50) / 50
        self.tilt_decay = (0.88 - 0.62 * R.norm(a['resilience'])) * (1 - 0.06 * self.c_mental)
        stam, rec = R.norm(a['stamina']), R.norm(a['recovery_rate'])
        self.fatigue_round = (1 - stam) * 0.9
        self.fatigue_week = (round_no - 1) * 0.22 * (1 - rec) * (1 - 0.4 * stam)
        # The day's form: how sharp the swing and the putter are today.
        self.day_disp = math.exp(rng.gauss(0, ip(R.STRIKE_FORM_SD, a['striking_consistency'])) + wf.strike)
        self.day_putt = rng.gauss(0, ip(R.PUTT_FORM_SD, a['putting_consistency'])) + wf.putt
        self.wind = cond.wind_mph / 20.0
        self.reach_fw = self.drive * 0.90       # 3-wood from a fairway
        self.plans = {}

    # -- situational multipliers -------------------------------------------
    def pressure_effect(self, pressure):
        if pressure <= 0:
            return 0.0
        return pressure * (1 - 0.85 * self.composure) * (1 - 0.25 * self.big_stage) * (1 - 0.07 * self.c_mental)

    def approach_mult(self, de):
        if de <= 115:
            return self.m_wedge
        if de < 140:
            t = (de - 115) / 25
            return self.m_wedge * (1 - t) + self.m_mid * t
        if de <= 180:
            return self.m_mid
        if de < 200:
            t = (de - 180) / 20
            return self.m_mid * (1 - t) + self.m_long * t
        return self.m_long

    def make_prob(self, ft, hole, state):
        logit = R.interp(_MAKE_LOGIT, ft)
        ws = 1.0 if ft <= 8 else max(0.35, 1 - (ft - 8) / 20)
        shift = ws * self.putt_shift - (1 - ws) * 0.6 * math.log(self.lag)
        slope_f = 0.5 + hole.green_slope
        dist_f = min(1.0, ft / 5.0)
        shift += (self.read + 0.08 * self.fam + 0.055 * self.c_read * (1 - 0.5 * self.read_n)) * slope_f * dist_f
        gd = 0.10 * (hole.green_speed - 11.5) + 0.6 * (hole.green_slope - 0.5)
        # Hard greens cost weak readers far more than strong ones.
        shift -= _harder(gd, 1.6 - 1.1 * self.read_n) * min(1.0, ft / 4.0)
        shift += self.day_putt - 0.15 * state.tilt - 0.15 * state.fat
        shift -= state.press * (0.5 if ft <= 12 else 0.25)
        return _sig(logit + shift)

    def leave(self, ft, hole, state, rng):
        if ft <= 6:
            mean = (0.9 + 0.12 * ft) * math.sqrt(self.lag)
        else:
            mean = (0.35 + 0.07 * ft) * self.lag
        amp = self.lag ** 2.5   # fast, sloping greens magnify poor speed control
        mean *= (1 + _harder(0.05 * (hole.green_speed - 11.5), amp)) * (1 + _harder(0.30 * (hole.green_slope - 0.5), amp))
        mean *= math.exp(-0.5 * self.day_putt) * (1 + 0.2 * state.press)
        return max(0.25, rng.gammavariate(2.0, mean / 2.0))


class HoleState:
    __slots__ = ('tilt', 'press', 'disp', 'err', 'fat')

    def __init__(self):
        self.tilt = 0.0
        self.press = 0.0
        self.disp = 1.0
        self.err = 0.0
        self.fat = 0.0


# ---------------------------------------------------------------------------
# Strategy helpers (cheap analytic estimates; the shots themselves are random)
# ---------------------------------------------------------------------------
_SIDE_COST = {'open': 0.30, 'trees': 0.80, 'water': 1.15, 'ob': 1.9}


def _tee_plan(pl, hole, rng):
    """Choose a tee club for this hole today: (name, distance factor, spread factor)."""
    key = hole.number
    if key in pl.plans:
        return pl.plans[key]
    clubs = (('driver', 1.0, 1.0), ('3-wood', 0.92, 0.87), ('iron', 0.80, 0.72))
    best, best_v = None, 1e9
    wind_f = 1 + pl.wind * hole.wind_exposure * (0.55 - 0.40 * pl.bfc)
    for name, df, sf in clubs:
        carry = pl.drive * df * pl.roll
        sigma = pl.sigma * sf * wind_f
        half = hole.fairway_width / 2
        extra_rough = 0.0
        if hole.landing_limit and carry > hole.landing_limit:
            over = carry - hole.landing_limit
            if hole.dogleg:
                half = max(4.0, half - over * hole.dogleg * (1 - 0.6 * pl.bfc))
                carry = hole.landing_limit + over * (1 - hole.dogleg) * 0.6
            else:
                extra_rough = min(0.7, over / 25)
                carry = hole.landing_limit + over * 0.35
        p_fw = math.erf(half / (sigma * 1.4142)) * (1 - extra_rough)
        p_out = 1 - math.erf((half + hole.rough_width) / (sigma * 1.4142))
        p_rough = max(0.0, 1 - p_fw - p_out)
        rem = max(5.0, hole.plays - carry)
        side = (_SIDE_COST[hole.left] + _SIDE_COST[hole.right]) / 2
        v = (p_fw * baseline('fairway', rem) + p_rough * baseline('rough', rem)
             + p_out * (baseline('rough', rem) + side))
        if name == 'driver':
            # Aggressive players lean to driver; poor course managers overuse it (ego).
            v -= 0.06 * pl.aggr + 0.10 * (1 - pl.mgmt) ** 2
        v += rng.gauss(0, pl.noise * 0.25)
        if v < best_v:
            best, best_v = (name, df, sf), v
    pl.plans[key] = best
    return best


def _side_hazard(hole, lat, beyond, rng):
    """Where a ball that left the playing corridor ends up.

    lat: signed lateral position (- left, + right); beyond: yards past the corridor edge.
    Returns (lie, penalty, out_of_bounds). Out of bounds means stroke and distance.
    """
    side = hole.left if lat < 0 else hole.right
    if side == 'ob':
        return None, 1, True
    if side == 'water':
        return 'rough', 1, False
    if side == 'trees':
        # Deep into the woods: lost ball or unplayable lie (penalty, drop in the trees).
        return 'trees', 1 if beyond > 12 and rng.random() < 0.3 else 0, False
    return 'rough', 0, False


def _attack_pin(pl, hole, mean_ft, rng):
    ratio = mean_ft / (hole.green_radius * 3.0)
    value = (0.85 - ratio) * 2.2 - (1.1 if hole.green_water else 0) - (0.4 if hole.greenside_bunkers > 0.7 else 0)
    value += 0.6 * pl.aggr + rng.gauss(0, pl.noise * 3)
    return value > 0


# ---------------------------------------------------------------------------
# The hole
# ---------------------------------------------------------------------------
def play_hole(pl, hole, hidx, rng, st, pressure=0.0, state=None, pin=None):
    """Play one hole shot by shot until the ball is holed. Returns strokes; updates RoundStats `st`.

    `pin` is the round's shared hole location (see `pin_sheet`). Competitions must pass it so every
    golfer plays the same pin; it is only drawn here for a one-off hole with no round context.
    """
    state = state or HoleState()
    par = hole.par
    state.tilt *= pl.tilt_decay
    state.press = pl.pressure_effect(pressure)
    fat = (hidx / 17.0) * pl.fatigue_round + pl.fatigue_week
    state.fat = fat
    wind_f = 1 + pl.wind * hole.wind_exposure * (0.55 - 0.40 * pl.bfc) * (1 - 0.10 * pl.c_yard)
    disp = pl.day_disp * wind_f * (1 + 0.15 * state.press) * (1 + 0.09 * state.tilt) * (1 + 0.08 * fat)
    err_p = (pl.mishit * (1 + 0.9 * state.press) * (1 + 0.6 * state.tilt) * (1 + 0.7 * fat)
             + pl.mental * (1 + 1.5 * fat) * (1 + 0.6 * state.press))
    dist_sd = 0.035 + 0.025 * pl.wind * hole.wind_exposure

    G = hole.green_radius
    if pin is None:
        r, a = G * 0.55 * (0.7 + 0.3 * rng.random()), rng.random() * 6.2832
        pin = (r * math.cos(a), r * math.sin(a))
    pin_x, pin_y = pin

    strokes = 0
    lie = 'tee'
    dist = float(hole.plays)        # yards (feet once on the green)
    short_sided = False
    gir = False
    putts = 0
    sand_at = None
    missed_green_once = False

    def sg_add(cat, before, after, penalty=0):
        val = before - after - 1 - penalty
        if cat == 'ott':
            st.sg_ott += val
        elif cat == 'app':
            st.sg_app += val
        elif cat == 'arg':
            st.sg_arg += val
        else:
            st.sg_putt += val

    while True:
        if strokes >= RUNAWAY_GUARD:
            raise RuntimeError(f'Runaway hole: {strokes} strokes on hole {hole.number} (engine bug)')
        if lie == 'green':
            if strokes <= par - 2 and not gir:
                gir = True
            n = 0
            ft = dist
            while True:
                n += 1
                before = baseline('green', ft)
                p_make = pl.make_prob(ft, hole, state)
                if ft <= 8 and rng.random() < pl.lapse * (1 + 1.5 * state.press) * (1 + 0.5 * state.fat):
                    p_make *= 0.55
                if rng.random() < p_make:
                    sg_add('putt', before, 0)
                    break
                ft = pl.leave(ft, hole, state, rng)
                sg_add('putt', before, baseline('green', ft))
                if strokes + n >= RUNAWAY_GUARD:
                    raise RuntimeError(f'Runaway putting on hole {hole.number} (engine bug)')
            strokes += n
            putts += n
            break

        before = baseline(_LIE_BASELINE[lie], dist)
        penalty = 0
        mis = rng.random() < err_p
        if mis:
            st.mishits += 1

        # ------------------------------------------------------- tee shot
        if lie == 'tee' and par >= 4:
            club, df, sf = _tee_plan(pl, hole, rng)
            total = pl.drive * df * pl.roll * (1 + rng.gauss(0, dist_sd)) * (1 - 0.012 * fat)
            sigma = pl.sigma * sf * disp
            if mis:
                total *= 0.65 + 0.23 * rng.random()
                sigma *= 2.0
            lat = rng.gauss(0, sigma)
            forced_rough = False
            if hole.landing_limit and total > hole.landing_limit:
                over = total - hole.landing_limit
                if hole.dogleg:
                    outside = -1 if hole.bend == 'R' else 1
                    lat += outside * over * hole.dogleg * (1 - 0.6 * pl.bfc)
                    total = hole.landing_limit + over * (1 - hole.dogleg) * 0.6
                else:
                    forced_rough = over > 8 and rng.random() < min(0.7, over / 25)
                    total = hole.landing_limit + over * 0.35
            if club == 'driver':
                st.drives.append(total)
            st.fairway_att += 1
            strokes += 1
            rem = hole.plays - total
            half = hole.fairway_width / 2
            a = abs(lat)
            corridor = half + hole.rough_width
            # Hazards first: a drive that leaves the corridor is in trouble however far it went.
            if a <= corridor and abs(rem) <= 30:     # drove it to the green complex
                if abs(rem) <= G and a <= G:
                    lie, dist = 'green', 3 * math.hypot(rem, lat)
                elif rng.random() < hole.greenside_bunkers * 0.55:
                    lie, dist = 'sand', math.hypot(rem, lat)
                else:
                    lie, dist = 'around', max(3.0, math.hypot(rem, lat))
                sg_add('ott', before, baseline(_LIE_BASELINE[lie] if lie != 'green' else 'green', dist))
                continue
            dist = abs(rem) if abs(rem) > 60 else max(3.0, math.hypot(rem, a))
            if a <= half and not forced_rough:
                lie = 'fairway_bunker' if rng.random() < hole.fairway_bunkers * 0.06 else 'fairway'
            elif a <= half + hole.rough_width:
                if a <= half + 7 and rng.random() < hole.fairway_bunkers * 0.5:
                    lie = 'fairway_bunker'
                else:
                    lie = 'rough'
            else:
                lie, penalty, ob = _side_hazard(hole, lat, a - corridor, rng)
                if ob:                  # out of bounds: stroke and distance
                    st.penalties += 1
                    strokes += 1
                    sg_add('ott', before, baseline('tee', hole.plays), 1)
                    lie, dist = 'tee', float(hole.plays)
                    continue
            if lie == 'fairway':
                st.fairways += 1
            if penalty:
                st.penalties += 1
                strokes += 1
            sg_add('ott', before, baseline(_LIE_BASELINE[lie], dist), penalty)
            continue

        # ------------------------------------------------------- trouble (trees)
        if lie == 'trees':
            strokes += 1
            de = dist * (TOUR_DRIVE / pl.drive) ** 0.5
            gap = 0.35 * (pl.approach_mult(de) - 1)
            ev_punch = 1 + baseline('fairway', max(30, dist - 42)) + gap
            p_ok = pl.rec_ok * (1 - 0.15 * hole.rough_severity)
            ev_go = p_ok * (baseline('rough', dist) + 0.35 + gap) + (1 - p_ok) * (1 + baseline('trees', max(20, dist - 15)))
            ev_go -= 0.12 * pl.aggr
            go = ev_go + rng.gauss(0, pl.noise) < ev_punch
            if go and rng.random() < p_ok and not mis:
                lie = 'recovery_shot'   # handled by the approach code below
            elif go:
                if rng.random() < 0.6:
                    dist = max(20.0, dist - 30 * rng.random())
                    lie = 'trees'
                else:
                    dist = max(20.0, dist - 20 - 40 * rng.random())
                    lie = 'rough'
                sg_add('app', before, baseline(_LIE_BASELINE[lie], dist))
                continue
            else:
                dist = max(25.0, dist - 25 - 35 * rng.random())
                lie = 'fairway' if rng.random() < 0.8 else 'rough'
                sg_add('app', before, baseline(_LIE_BASELINE[lie], dist))
                continue
            strokes -= 1                # the approach code counts this stroke

        # ------------------------------------------------------- short game
        if lie in ('around', 'fringe', 'sand') or (lie in ('rough', 'fairway') and dist <= 40):
            strokes += 1
            D = dist
            cat = 'arg'
            if lie == 'sand':
                if sand_at is None:
                    sand_at = strokes - 1
                    st.sand_att += 1
                fail = pl.sand_fail * (1 + 0.5 * hole.rough_severity) * (1 + 0.9 * state.press) * (1 + 0.3 * state.tilt)
                if rng.random() < fail or mis:
                    if rng.random() < 0.7:
                        sg_add(cat, before, baseline('sand', D))
                        continue                 # still in the bunker
                    lie, dist = 'around', 8 + 15 * rng.random()
                    short_sided = True
                    sg_add(cat, before, baseline('rough', dist))
                    continue
                if rng.random() < min(0.12, 0.05 * math.exp(-D / 18) / pl.m_sand ** 1.5):
                    sg_add(cat, before, 0)
                    break
                amp = pl.m_sand ** 1.5
                mean = (3.5 + 0.25 * D) * pl.m_sand * (1 + _harder(0.3 * (hole.green_firmness - 0.5), amp))
                mean *= 1 + _harder(0.04 * (hole.green_speed - 11.5), amp)
                mean *= (1.35 if short_sided else 1.0) * math.sqrt(pl.day_disp)
            else:
                sev = hole.rough_severity if lie in ('around', 'rough') else 0.0
                lie_m = 0.55 if lie == 'fringe' else (1.0 if lie == 'fairway' else 1.0 + 0.55 * sev * pl.rough_skill)
                fail = pl.chip_fail * (1 + 0.8 * sev) * (1.4 if short_sided else 1) * (1 + 0.9 * state.press) * (1 + 0.3 * state.tilt)
                if lie == 'fringe':
                    fail *= 0.4
                if rng.random() < fail or (mis and rng.random() < 0.5):
                    if rng.random() < 0.5:
                        dist = max(2.0, D * (0.45 + 0.4 * rng.random()))
                        lie = 'around'
                    else:
                        dist = 8 + 14 * rng.random()
                        lie, short_sided = 'around', True
                    sg_add(cat, before, baseline('rough', dist))
                    continue
                if rng.random() < min(0.15, 0.09 * math.exp(-D / 18) / pl.m_chip ** 1.5) * (0.5 if short_sided else 1):
                    sg_add(cat, before, 0)
                    break
                mean = (2.5 + 0.2 * D) * pl.m_chip * lie_m * (1.45 if short_sided else 1.0)
                amp = pl.m_chip ** 1.5
                mean *= (1 + _harder(0.06 * (hole.green_speed - 11.5), amp)) * (1 + _harder(0.3 * (hole.green_slope - 0.5), amp))
                mean *= math.sqrt(pl.day_disp) * (1 + 0.1 * state.press)
            ft = _rayleigh(rng, mean)
            lie, dist = 'green', max(0.5, ft)
            sg_add(cat, before, baseline('green', dist))
            continue

        # ------------------------------------------------------- full shot to the green / lay-up
        strokes += 1
        recovery = lie == 'recovery_shot'
        if recovery:
            lie = 'trees'
            before = baseline('trees', dist)
        de = dist * (TOUR_DRIVE / pl.drive) ** 0.5
        reach = pl.reach_fw * (0.88 if lie == 'rough' else 0.78 if lie == 'fairway_bunker' else 1.0)
        if lie == 'fairway_bunker':
            reach = min(reach, 210 * pl.drive / TOUR_DRIVE)
        lay_up = dist > reach
        if not lay_up and par == 5 and strokes == 2 and dist > 200:
            # Go for the green in two, or lay up to a wedge? Weigh it up.
            m = pl.approach_mult(de)
            water_risk = 0.45 if hole.green_water else 0.0
            ev_go = baseline('fairway', dist) + 0.35 * (m - 1) + water_risk * min(1, m * dist / 450)
            ev_lay = 1 + baseline('fairway', 95) + 0.25 * (pl.m_wedge - 1)
            ev_go -= 0.15 * pl.aggr
            lay_up = ev_go + rng.gauss(0, pl.noise) > ev_lay
        if lay_up:
            prev_lie = lie
            if dist - reach <= 70 and par == 4:
                # Just out of reach: hit the longest club available and finish short of the green.
                target = reach
            else:
                target = min(reach, max(dist - 100, dist * 0.55))
            sigma = pl.sigma * 0.55 * disp * (2.0 if mis else 1.0)
            go = target * (1 + rng.gauss(0, 0.05)) * (0.7 if mis else 1.0)
            lat = rng.gauss(0, sigma)
            dist = max(15.0, dist - go)
            half = hole.fairway_width / 2
            a = abs(lat)
            if a <= half:
                lie = 'fairway'
            elif a <= half + hole.rough_width:
                lie = 'fairway_bunker' if (a <= half + 6 and rng.random() < hole.fairway_bunkers * 0.35) else 'rough'
            else:
                lie, penalty, ob = _side_hazard(hole, lat, a - half - hole.rough_width, rng)
                if ob:                  # stroke and distance: replay from where it was hit
                    dist, lie = dist + go, prev_lie
                if penalty:
                    st.penalties += 1
                    strokes += 1
            sg_add('app', before, baseline(_LIE_BASELINE[lie], dist), penalty)
            continue

        m = pl.approach_mult(de)
        base_ft = 3.6 + 0.104 * de + 0.00026 * de * de
        if lie == 'tee':
            lie_m = 0.92
        elif lie == 'fairway':
            lie_m = 1.0
        elif lie == 'rough':
            lie_m = 1 + (0.25 + 0.35 * hole.rough_severity) * pl.rough_skill
        elif lie == 'fairway_bunker':
            lie_m = 1.25 + 0.5 * pl.m_sand
        else:  # recovery shot from the trees
            lie_m = 1 + 1.0 * pl.rough_skill
        # High, soft ball flight (Ball-Flight Control) holds firm greens better.
        firm_m = 1 + _harder((hole.green_firmness - 0.5) * 0.35 * (de / 150) * (0.4 if lie == 'tee' else 1.0),
                             (1.4 - 0.8 * pl.bfc) * m ** 1.5)
        mean_ft = (base_ft * m * lie_m * disp * firm_m * (1 - 0.02 * pl.fam)
                   * (1 - 0.015 * pl.c_yard))
        # Weaker players also have contact error that doesn't shrink with a shorter club.
        mean_ft += pl.contact * lie_m * disp
        if rng.random() < min(0.25, 0.02 * math.exp(-de / 50) / m) and not mis:
            if lie == 'tee':
                st.aces += 1
            sg_add('app', before, 0)
            break
        attack = _attack_pin(pl, hole, mean_ft, rng)
        aim_k = 1.0 if attack else 0.35
        if mis:
            err_yd = _rayleigh(rng, mean_ft * 2.2) / 3
            ang = math.pi + rng.gauss(0, 0.6)       # mishits mostly come up short
            bx = pin_x * aim_k + err_yd * math.cos(ang)
            by = pin_y * aim_k + err_yd * math.sin(ang)
        else:
            # Approach misses are mostly distance (long/short) rather than direction.
            s = mean_ft / 1.2533 / 3
            bx = pin_x * aim_k + rng.gauss(0, s * 1.2)
            by = pin_y * aim_k + rng.gauss(0, s * 0.78)
        from_centre = math.hypot(bx, by)
        to_pin = math.hypot(bx - pin_x, by - pin_y)
        # Greens are irregular and shed balls near their edges, so they hold less than their area.
        if from_centre <= G * 0.88:
            lie, dist = 'green', max(0.5, to_pin * 3)
            sg_add('app', before, baseline('green', dist))
            continue
        missed_green_once = True
        off = max(0.5, from_centre - G * 0.88)
        # A wild miss beside the green is in the hole's side hazards, just like a wild drive.
        lateral_limit = max(G + 6, hole.fairway_width / 2 + hole.rough_width)
        if abs(by) > lateral_limit:
            side_lie, penalty, ob = _side_hazard(hole, by, abs(by) - lateral_limit, rng)
            if penalty:
                st.penalties += 1
                strokes += 1
            if ob:                      # stroke and distance: replay from the same spot
                sg_add('app', before, before, penalty)
                continue
            lie, dist = side_lie, max(10.0, to_pin)
            sg_add('app', before, baseline(_LIE_BASELINE[lie], dist), penalty)
            continue
        if hole.green_water and off > 1.5:
            side = ('front' if bx < -abs(by) else 'back' if bx > abs(by) else 'left' if by < 0 else 'right')
            if side == hole.green_water and rng.random() < (0.85 if off > 3 else 0.5):
                penalty = 1
                st.penalties += 1
                strokes += 1
                lie, dist = 'rough', max(25.0, min(dist, to_pin + 15))
                sg_add('app', before, baseline('rough', dist), penalty)
                continue
        if off > 30:
            lie, dist = 'rough', to_pin
        elif off <= 2.0:
            lie, dist = 'fringe', max(3.0, to_pin)
        elif rng.random() < hole.greenside_bunkers * 0.55 * (1.0 if off < 8 else 0.4):
            lie, dist = 'sand', max(3.0, to_pin)
        else:
            lie, dist = 'around', max(3.0, to_pin)
        short_sided = (to_pin - off) < 4
        sg_add('app', before, baseline(_LIE_BASELINE[lie], dist))

    # ----------------------------------------------------------- bookkeeping
    rel = strokes - par
    st.holes.append(strokes)
    st.score += strokes
    st.putts += putts
    if putts >= 3:
        st.three_putts += 1
    if gir:
        st.gir += 1
    else:
        st.scramble_att += 1
        if rel <= 0:
            st.scramble_made += 1
    if sand_at is not None and strokes - sand_at <= 2:
        st.sand_saves += 1
    if rel <= -2:
        st.eagles += 1
    elif rel == -1:
        st.birdies += 1
    elif rel == 0:
        st.pars += 1
    elif rel == 1:
        st.bogeys += 1
    elif rel == 2:
        st.doubles += 1
    else:
        st.worse += 1
    st.par_scores[par][0] += strokes
    st.par_scores[par][1] += 1
    if rel >= 1:
        state.tilt = min(2.5, state.tilt + 0.6 * rel)
    return strokes


def play_round(golfer, course, rng, cond=None, caddie=None, round_no=1, week_form=None,
               pressure_fn=None, pins=None):
    """Play 18 holes. pressure_fn(hole_index, strokes_to_par_so_far) -> 0..1.

    `pins`: the round's shared pin sheet. Pass the same sheet to every golfer in a competition round;
    if omitted (a stand-alone round) a sheet is drawn for this round.
    """
    cond = cond or Conditions()
    if pins is None:
        pins = pin_sheet(course, cond, rng)
    pl = Player(golfer, course, cond, caddie, rng, round_no, week_form)
    st = RoundStats()
    state = HoleState()
    par_so_far = 0
    for i, hole in enumerate(course.holes):
        pressure = pressure_fn(i, st.score - par_so_far) if pressure_fn else 0.0
        play_hole(pl, hole, i, rng, st, pressure, state, pins[i])
        par_so_far += hole.par
    st.to_par = st.score - course.par
    return st
