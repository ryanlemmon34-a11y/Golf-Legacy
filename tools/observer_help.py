"""Small, deterministic contextual explanations for the read-only observer.

Append ``help_for(label)`` OUTSIDE sorting links/buttons; emit HELP_CSS in the
page stylesheet and HELP_JS once near the end of body. Unknown labels get no
control. Explicit keys (e.g. prestige_golfer) disambiguate a reused heading.
Descriptions are plain text, never trusted HTML. Sources: golfsim.ratings,
golfsim.golfstats, observer_data.GROUP_NOTE and the observer's Prestige notes.
"""
from html import escape
import re

from golfsim.ratings import ATTRIBUTES

TEXT = {
    'power': 'Higher Power adds driving distance and physical reach, leaving shorter clubs into greens and making more long approaches reachable. Longer drives also spread farther offline at the same Driving Accuracy. Rating: 0–100.',
    'stamina': 'Higher Stamina reduces fatigue during rounds and busy schedules, helping preserve distance and accuracy. It also reduces event injury risk and can raise a professional’s target number of events. Rating: 0–100.',
    'recovery_rate': 'Higher Recovery reduces fatigue carried into later rounds and clears more fatigue during weeks off. It helps a golfer stay fresh without directly improving their shot-making skills. Rating: 0–100.',
    'injury_resistance': 'Higher Injury Resistance lowers the chance of an injury after an event. Fatigue, age and Stamina also affect that risk. It has no direct effect on an individual shot. Rating: 0–100.',
    'driving_accuracy': 'Higher Driving Accuracy narrows the sideways spread of tee shots and lay-ups, helping avoid rough and hazards. The same accuracy rating produces more yards of spread on a longer drive. Rating: 0–100.',
    'long_irons': 'Higher Long Irons tightens the spread of long approaches, especially beyond about 200 effective yards. Power and wind change the effective distance, so the same hole can test different clubs. Rating: 0–100.',
    'mid_irons': 'Higher Mid/Short Irons tightens approach spread, chiefly around 140–180 effective yards. It also helps reduce the contact-error floor shared with Wedge Play and Ball-Striking Consistency. Rating: 0–100.',
    'wedges': 'Higher Wedge Play tightens short-approach spread, chiefly inside 115 effective yards, blending into iron play beyond that. It also helps reduce contact errors that remain even on short shots. Rating: 0–100.',
    'ball_flight': 'Higher Ball-Flight Control reduces wind effects and dogleg misses, and helps approaches hold firm greens. It improves control in difficult conditions rather than making the golfer immune to them. Rating: 0–100.',
    'chipping': 'Higher Chipping/Pitching brings shots around the green closer to the hole, reduces failed chips and raises chip-in chances. Rough, pressure and a short-sided lie can still make the shot harder. Rating: 0–100.',
    'bunker': 'Higher Bunker Play brings greenside sand shots closer, reduces failures to escape and improves hole-out chances. It also reduces the extra approach-shot spread caused by a fairway bunker. Rating: 0–100.',
    'recovery_play': 'Higher Recovery Play improves the chance of a successful attacking escape from trees and reduces the extra spread from rough and recovery shots. Course Management helps decide whether to attempt the escape. Rating: 0–100.',
    'short_putting': 'Higher Short Putting increases the chance of holing putts, with its strongest effect inside eight feet and a smaller effect farther away. Distance, green reading, pressure and daily form still matter. Rating: 0–100.',
    'lag_putting': 'Higher Lag Putting leaves shorter follow-up putts after a miss and helps longer-putt make chances. Poor speed control is punished more by fast, sloping greens. Rating: 0–100.',
    'green_reading': 'Higher Green Reading improves putt make chances and reduces the extra difficulty of fast, sloping greens. Its effect grows with slope; it does not replace speed control or short-putt skill. Rating: 0–100.',
    'striking_consistency': 'Higher Ball-Striking Consistency reduces day-to-day and week-to-week swing variation and mishit risk. It also helps reduce the contact-error floor on approaches; it does not guarantee identical rounds. Rating: 0–100.',
    'putting_consistency': 'Higher Putting Consistency reduces day-to-day and week-to-week putting variation and short-putt lapses. Short Putting, Lag Putting and Green Reading still determine the underlying putting skills. Rating: 0–100.',
    'composure': 'Higher Composure reduces the performance penalty from pressure. That helps preserve shot control and putting when the cut line, contention or a late lead makes the situation tense. Rating: 0–100.',
    'resilience': 'Higher Resilience makes the after-effects of bad holes fade faster, so frustration disrupts fewer later shots and putts. It does not erase the score already recorded. Rating: 0–100.',
    'management': 'Higher Course Management reduces judgement errors in tee-club, pin-attack, lay-up and tree-escape choices. It also helps handle wind in the seasonal weather model. Aggression separately biases willingness to take risks. Rating: 0–100.',
    'focus': 'Higher Focus reduces mental errors, including the extra distraction of rain. Fatigue, pressure and frustration can still raise mistake risk; focus is not the same as technical accuracy. Rating: 0–100.',
}
TEXT.update({
    'overall': 'A scoring-weighted summary of the 21 attributes, not a separate shot skill or the mean of the three groups. The engine uses individual attributes for distance, accuracy, decisions and putting.',
    'physical': 'Mean of Power, Stamina, Recovery and Injury Resistance. These individual ratings affect reach, fatigue and injury risk; this displayed group average is not an extra performance bonus.',
    'technical': 'Mean of the 13 Long Game, Short Game, Putting and Consistency attributes. Those individual skills control shots and putting; this group average is a summary, not an extra shot modifier.',
    'mental': 'Mean of Composure, Resilience, Course Management and Focus. Those individual ratings affect pressure, recovery from bad holes, decisions and errors; the group average adds no separate bonus.',
    'prestige': 'Public standing, not an ability rating. Its calculation depends on whether this is a person, tournament, course or nation; see the page’s detailed Prestige explanation.',
    'prestige_golfer': 'A golfer’s public standing (0–100), built from recent results and lasting title legacy. It helps determine professional sponsor income, event preferences and staff-market appeal; it does not improve shot skill.',
    'prestige_staff': 'Public reputation in this role (0–100). It affects fees and how golfers and staff choose partnerships. Actual teaching or caddie skills are separate, so greater fame does not guarantee better help.',
    'prestige_event': 'An event’s standing (0–100). Higher Prestige makes it more attractive to golfers and increases the ranking points and fame available for the same finish. It can also trigger a venue review when an eligible event outgrows its course.',
    'prestige_course': 'A course’s standing from events hosted in the previous five completed seasons. It helps determine whether an event has outgrown its venue and breaks ties between suitable replacement courses. It does not change the layout or shot difficulty.',
    'prestige_nation': 'National standing shifts each nation’s share of future new golfers through a gradually changing participation multiplier. It does not increase the worldwide total, improve entrants’ talent or change existing golfers’ nationality.',
    'aggression': 'A fixed 0–100 personality trait: cautious to attacking. It biases choices toward risk, not ability; a golfer still needs the physical reach for a shot.',
    'scoring': 'Total strokes divided by completed 18-hole stroke-play rounds. Raw scoring average: not adjusted for course or field. Lower is better. A recorded outcome, not a shot-control rating.',
    'distance': 'Average yards of first tee shots hit with a driver on par 4s and 5s, including carry, roll and misses. Re-tees, woods and irons are excluded. A recorded outcome, not a shot-control rating.',
    'fairways': 'Percentage of first tee shots on par 4s and 5s that finish on the fairway. Bunkers and drivable greens do not count as fairway hits. A recorded outcome, not a shot-control rating.',
    'gir': 'Greens in regulation: the percentage of holes reaching the putting surface, or holing out, within par minus two strokes. Penalties count; the fringe is not the green. A recorded outcome, not a shot-control rating.',
    'scrambling': 'Percentage of holes with a missed green in regulation that still finish in par or better. A recorded outcome, not a shot-control rating.',
    'sand': 'Percentage of holes with a greenside bunker shot where the golfer gets down in at most two strokes from the bunker. A recorded outcome, not a shot-control rating.',
    'putts_round': 'Strokes played on the putting surface divided by completed rounds. Fringe strokes are not putts. A recorded outcome, not a shot-control rating.',
    'putts_gir': 'Putts on greens-in-regulation holes divided by those holes. A holed approach counts as a GIR with zero putts. A recorded outcome, not a shot-control rating.',
    'birdies': 'Birdies, eagles and better scores combined, divided by completed rounds. A recorded outcome, not a shot-control rating.',
    'bogeys': 'Bogeys, double bogeys and worse scores combined, divided by completed rounds. A recorded outcome, not a shot-control rating.',
    'sg_total': 'Strokes gained per round against the engine’s own expected-strokes table. Positive means strokes gained. This is not a validated real-world baseline. A recorded outcome, not a shot-control rating.',
    'coverage': 'Starts with recorded golf statistics out of all starts. Missing statistics are not zero; career figures include only recorded seasons.',
    'starts': 'Recorded main-event appearances. Qualifying stages are counted separately, not as starts. The selected season and tour scope determine which events count.',
    'wins': 'Recorded first-place finishes in the selected scope. Qualifying stages are excluded. Earlier unrecorded career results are not implied.',
    'runner_up': 'Recorded second-place finishes, including ties. This is separate from the Top 2 count, which also includes wins.',
    'top2': 'Finishes of second or better, including wins and ties. Do not add Top 2, Top 5 and Top 10 together.',
    'top5': 'Finishes of fifth or better, including wins and ties. This overlaps with Top 2 and Top 10.',
    'top10': 'Finishes of tenth or better, including wins and ties. This overlaps with Top 2 and Top 5.',
    'cuts': 'Cuts made out of stroke-play events that had a cut. Events without a cut do not enter this denominator.',
    'missed_cuts': 'Stroke-play events with a cut where the golfer missed that cut. Events without a cut are excluded.',
    'prize': 'Gross tournament prize money, before costs. Unknown or unconfirmed amounts are kept separate from a recorded zero; see the page’s payout coverage notes.',
    'peak_overall': 'Highest Overall supported by the stored ratings. Recorded Peak means earlier career coverage is incomplete, so a higher unrecorded peak may have existed.',
})


def _normal(label):
    return re.sub(r'\s+', ' ', str(label).strip().casefold().replace('_', ' '))


ALIASES = {_normal(k): k for k in TEXT}
ALIASES.update({_normal(label): key for key, label, _, _ in ATTRIBUTES})
ALIASES.update({_normal(label): key for label, key in {
    'Scoring average (raw)': 'scoring', 'Driving dist.': 'distance',
    'Driving distance (yds)': 'distance', 'Fairways hit': 'fairways',
    'Greens in regulation': 'gir', 'Sand saves': 'sand', 'Putts/rd': 'putts_round',
    'Putts per round': 'putts_round', 'Putts/GIR': 'putts_gir', 'Putts per GIR': 'putts_gir',
    'Birdies+/rd': 'birdies', 'Bogeys+/rd': 'bogeys', 'SG/rd (engine)': 'sg_total',
    'Strokes gained per round (engine table)': 'sg_total',
    'Prestige · now': 'prestige_golfer', 'Prestige · last recorded': 'prestige_golfer',
    'Runner-up':'runner_up', 'Top 2':'top2', 'Top 5':'top5', 'Top 10':'top10',
    'Cuts made':'cuts', 'Missed cuts':'missed_cuts', 'Prize money':'prize',
    'Peak Overall':'peak_overall', 'Recorded Peak Overall':'peak_overall',
}.items()})


def description_for(label):
    """Exact, case-insensitive plain-text heading/attribute lookup; no fuzzy guesses."""
    return TEXT.get(ALIASES.get(_normal(label)), '')


def help_trigger(label, description):
    """Standalone button. Native title and accessible name remain useful without JS.

    No server IDs/counters: repeated renders are byte-for-byte identical. JS adds
    a unique description ID once the full document is present.
    """
    if not description:
        return ''
    name = f'About {label}'
    return (f'<button type="button" class="context-help" data-help-label="{escape(name, quote=True)}" '
            f'data-help="{escape(str(description), quote=True)}" '
            f'aria-label="{escape(name + ": " + str(description), quote=True)}" '
            f'title="{escape(str(description), quote=True)}"><span aria-hidden="true">?</span></button>')


def help_for(label, key=None):
    """Help suffix for a visible label, optionally selecting an explicit meaning."""
    return help_trigger(label, description_for(key if key is not None else label))


HELP_CSS = r'''
.context-help {display:inline-flex;align-items:center;justify-content:center;vertical-align:middle;
 margin:0 0 0 .35em;padding:0;width:1.4rem;height:1.4rem;min-width:1.4rem;min-height:1.4rem;border:1px solid currentColor;
 border-radius:50%;background:transparent;color:var(--muted,#65736c);font:600 .75rem/1 system-ui,sans-serif;
 cursor:help;opacity:.8;}
.context-help:hover,.context-help:focus-visible {opacity:1;color:var(--accent,#245c42);}
.context-help:focus-visible {outline:2px solid currentColor;outline-offset:3px;}
.context-help-popover {position:fixed;z-index:10000;box-sizing:border-box;max-width:22rem;
 padding:.8rem 1rem;background:#172b23;color:#fff;border:1px solid #8ba398;border-radius:.6rem;
 box-shadow:0 6px 24px #0003;font:400 .875rem/1.5 system-ui,sans-serif;white-space:normal;
 text-align:left;overflow-wrap:anywhere;overflow:auto;}
.context-help-popover[hidden] {display:none;}
'''

HELP_JS = r'''
(function () {
  function init() {
    if (document.querySelector('[data-context-help-popup]')) return;
    const tip = document.createElement('div');
    tip.className = 'context-help-popover';
    tip.dataset.contextHelpPopup = '';
    tip.setAttribute('role', 'tooltip');
    let id = 'context-help-description', n = 0;
    while (document.getElementById(id)) id = 'context-help-description-' + (++n);
    tip.id = id;
    tip.hidden = true;
    document.body.appendChild(tip); // outside table overflow containers
    let active = null, pinned = false, timer;
    function hide() {
      clearTimeout(timer);
      if (active) active.removeAttribute('aria-describedby');
      active = null; pinned = false; tip.hidden = true;
    }
    function position() {
      if (!active) return;
      const r = active.getBoundingClientRect(), gap = 8, pad = 8;
      const w = document.documentElement.clientWidth, h = window.innerHeight;
      if (r.bottom < 0 || r.top > h || r.right < 0 || r.left > w) { hide(); return; }
      tip.style.maxWidth = Math.max(1, Math.min(352, w - 2 * pad)) + 'px';
      // Fit on the roomier vertical side, never cover the triggering cell.
      const below = h - r.bottom - gap - pad, above = r.top - gap - pad;
      const useBelow = below >= Math.min(160, above);
      tip.style.maxHeight = Math.max(1, useBelow ? below : above) + 'px';
      const t = tip.getBoundingClientRect();
      tip.style.left = Math.max(pad, Math.min(r.left, w - t.width - pad)) + 'px';
      tip.style.top = (useBelow ? r.bottom + gap : Math.max(pad, r.top - gap - t.height)) + 'px';
    }
    function show(button, pin) {
      clearTimeout(timer);
      if (active !== button) { hide(); active = button; }
      pinned = pin || pinned;
      tip.textContent = button.dataset.help;
      button.setAttribute('aria-describedby', id);
      tip.hidden = false; position();
    }
    function later() {
      clearTimeout(timer);
      timer = setTimeout(function () {
        if (!pinned && active && document.activeElement !== active && !tip.matches(':hover')) hide();
      }, 160);
    }
    document.querySelectorAll('.context-help').forEach(function (button) {
      button.setAttribute('aria-label', button.dataset.helpLabel);
      button.setAttribute('title', ''); // suppress native and inherited header tooltips
      button.addEventListener('mouseenter', function () { show(button, false); });
      button.addEventListener('mouseleave', later);
      button.addEventListener('focus', function () { show(button, false); });
      button.addEventListener('blur', function () { pinned = false; later(); });
      button.addEventListener('click', function (event) {
        event.preventDefault(); event.stopPropagation();
        if (active === button && pinned) hide(); else show(button, true);
      });
      button.addEventListener('keydown', function (event) {
        // Do not let header keyboard sorting handle this control.
        if (event.key === 'Enter' || event.key === ' ') event.stopPropagation();
      });
    });
    tip.addEventListener('mouseenter', function () { clearTimeout(timer); });
    tip.addEventListener('mouseleave', later);
    document.addEventListener('keydown', function (event) { if (event.key === 'Escape') hide(); });
    document.addEventListener('click', function (event) {
      if (!event.target.closest('.context-help') && !tip.contains(event.target)) hide();
    });
    window.addEventListener('resize', position);
    // Dismiss on table/page scroll: no orphan popup over a clipped trigger.
    document.addEventListener('scroll', function (event) { if (event.target !== tip) hide(); }, true);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
'''
