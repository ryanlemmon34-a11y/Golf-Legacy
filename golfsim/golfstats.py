"""Golf-performance statistics: what is counted while every shot is simulated, and how it is aggregated.

Each golfer's counters for one edition (summed over their stroke-play rounds at their site) are kept in
the archive (an edition's `golf`), so season, career and tour figures are always sums of counts divided by
sums of opportunities -- never averages of averages (1/2 and 8/10 make 9/12, 75%). Definitions are
versioned (`VERSION`); seasons played before an engine counted them have none and read "not recorded".

Definitions (version 1):
- **Rounds**: completed 18-hole stroke-play rounds (match-play holes and playoff holes are not rounds and
  are not counted in any statistic here: a match stops when it is decided).
- **Scoring average** (raw): strokes / rounds. Not adjusted for course or field.
- **Driving distance**: the first tee shot on each par 4 and par 5 that was hit with a driver, measured
  where the ball finished (carry and roll, along the line of play, after any dogleg or landing limit),
  in yards -- fairway, rough, bunker or hazard alike (misses are included, not only fairways). A re-tee
  after out of bounds is not measured again. Fairway woods and irons off the tee are not measured drives.
- **Driving accuracy** (fairways hit): first tee shots on par 4s and 5s finishing on the fairway / those
  tee shots. A fairway bunker is not the fairway; a drive finishing on or beside a drivable green counts
  as an attempt without a fairway hit. Par 3 tee shots are not counted.
- **Greens in regulation**: holes where the ball was on the putting surface after at most par - 2 strokes
  (penalty strokes included; the fringe is not the putting surface), or holed from off the green within
  par - 2 strokes (an ace, a holed approach: a GIR with no putts) / holes played.
- **Scrambling**: holes without a green in regulation finished in par or better / holes without a GIR.
  Separate from **sand saves**: up and down (holed in at most two strokes) from a greenside bunker /
  holes with a greenside bunker shot.
- **Putts**: strokes played on the putting surface (a stroke from the fringe is not a putt). Putts per
  round = putts / rounds; putts per GIR = putts on GIR holes / GIR holes; three-putts are holes with
  three or more putts.
- **Scores by hole**: eagles or better, birdies, pars, bogeys, double bogeys, worse; scoring average on
  par 3s, 4s and 5s (strokes / holes of that par); penalty strokes.
- **Strokes gained** (off the tee, approach, around the green, putting): against the engine's own
  expected-strokes table by lie and distance, summed per shot. Kept, but not a validated real-world
  baseline: shown labelled as the engine's.
- **Longest drive**: the single longest measured drive, with its round and hole.
"""
from __future__ import annotations

VERSION = 1
# One edition's counters for a golfer: integers (yards and strokes gained in tenths / hundredths so the
# archive stays exact and compact).
FIELDS = ('rounds', 'holes', 'strokes', 'drives', 'drive_tenths', 'fairways', 'fairway_att', 'gir', 'putts',
          'gir_putts', 'three_putts', 'scr_att', 'scr_made', 'sand_att', 'sand_saves', 'penalties',
          'eagles', 'birdies', 'pars', 'bogeys', 'doubles', 'worse',
          'p3_strokes', 'p3_holes', 'p4_strokes', 'p4_holes', 'p5_strokes', 'p5_holes',
          'sg_ott', 'sg_app', 'sg_arg', 'sg_putt')
N = len(FIELDS)
IDX = {k: i for i, k in enumerate(FIELDS)}
SG = ('sg_ott', 'sg_app', 'sg_arg', 'sg_putt')


def round_counters(st):
    """One round's counters (FIELDS order) from the engine's RoundStats, and its longest drive
    (tenths of a yard, hole number) or None."""
    ps = st.par_scores
    c = (1, len(st.holes), st.score, len(st.drives), round(10 * sum(st.drives)), st.fairways, st.fairway_att,
         st.gir, st.putts, st.gir_putts, st.three_putts, st.scramble_att, st.scramble_made, st.sand_att,
         st.sand_saves, st.penalties, st.eagles, st.birdies, st.pars, st.bogeys, st.doubles, st.worse,
         ps[3][0], ps[3][1], ps[4][0], ps[4][1], ps[5][0], ps[5][1],
         round(100 * st.sg_ott), round(100 * st.sg_app), round(100 * st.sg_arg), round(100 * st.sg_putt))
    long = (round(10 * st.long_drive), st.long_drive_hole) if st.long_drive else None
    return c, long


def add(into, c):
    """Sum counters `c` into the list `into` (FIELDS order)."""
    for i, v in enumerate(c):
        into[i] += v
    return into


def empty():
    return [0] * N


# ---- derived figures (each: numerator, denominator, scale); None where the denominator is zero --------
def _div(a, b, k=1.0):
    return a * k / b if b else None


METRICS = {
    # key: (label, function of a counters dict, format, higher is better)
    'scoring': ('Scoring average (raw)', lambda c: _div(c['strokes'], c['rounds']), '{:.2f}', False),
    'distance': ('Driving distance (yds)', lambda c: _div(c['drive_tenths'], c['drives'], 0.1), '{:.1f}', True),
    'fairways': ('Fairways hit', lambda c: _div(c['fairways'], c['fairway_att'], 100), '{:.1f}%', True),
    'gir': ('Greens in regulation', lambda c: _div(c['gir'], c['holes'], 100), '{:.1f}%', True),
    'scrambling': ('Scrambling', lambda c: _div(c['scr_made'], c['scr_att'], 100), '{:.1f}%', True),
    'sand': ('Sand saves', lambda c: _div(c['sand_saves'], c['sand_att'], 100), '{:.1f}%', True),
    'putts_round': ('Putts per round', lambda c: _div(c['putts'], c['rounds']), '{:.2f}', False),
    'putts_gir': ('Putts per GIR', lambda c: _div(c['gir_putts'], c['gir']), '{:.3f}', False),
    'three_putts': ('Three-putts per round', lambda c: _div(c['three_putts'], c['rounds']), '{:.2f}', False),
    'birdies': ('Birdies or better per round', lambda c: _div(c['birdies'] + c['eagles'], c['rounds']), '{:.2f}', True),
    'bogeys': ('Bogeys or worse per round', lambda c: _div(c['bogeys'] + c['doubles'] + c['worse'], c['rounds']),
               '{:.2f}', False),
    'par3': ('Par 3 scoring', lambda c: _div(c['p3_strokes'], c['p3_holes']), '{:.3f}', False),
    'par4': ('Par 4 scoring', lambda c: _div(c['p4_strokes'], c['p4_holes']), '{:.3f}', False),
    'par5': ('Par 5 scoring', lambda c: _div(c['p5_strokes'], c['p5_holes']), '{:.3f}', False),
    'sg_total': ('Strokes gained per round (engine table)',
                 lambda c: _div(sum(c[k] for k in SG), c['rounds'], 0.01), '{:+.2f}', True),
}
# the sample each figure is a share of (shown beside it, and used for qualification)
SAMPLE = {'scoring': 'rounds', 'distance': 'drives', 'fairways': 'fairway_att', 'gir': 'holes',
          'scrambling': 'scr_att', 'sand': 'sand_att', 'putts_round': 'rounds', 'putts_gir': 'gir',
          'three_putts': 'rounds', 'birdies': 'rounds', 'bogeys': 'rounds', 'par3': 'p3_holes',
          'par4': 'p4_holes', 'par5': 'p5_holes', 'sg_total': 'rounds'}


def as_dict(vec):
    return dict(zip(FIELDS, vec))


def metric(key, counters):
    """The figure for `key` from a counters dict (None where its denominator is zero: N/A, not zero)."""
    return METRICS[key][1](counters)


def fmt(key, value):
    return 'N/A' if value is None else METRICS[key][2].format(value)
