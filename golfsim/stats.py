"""Aggregate RoundStats into the familiar tour statistics."""
from __future__ import annotations

import statistics as S


def summarize(rounds):
    n = len(rounds)
    holes = 18 * n
    def tot(attr):
        return sum(getattr(r, attr) for r in rounds)
    scores = [r.score for r in rounds]
    drives = [d for r in rounds for d in r.drives]
    gir = tot('gir')
    out = {
        'rounds': n,
        'scoring_avg': S.mean(scores),
        'score_sd': S.pstdev(scores),
        'best': min(scores),
        'worst': max(scores),
        'driving_distance': S.mean(drives) if drives else 0.0,
        'driver_pct': len(drives) / max(1, tot('fairway_att')),
        'fairways_pct': tot('fairways') / max(1, tot('fairway_att')),
        'gir_pct': gir / holes,
        'scrambling_pct': tot('scramble_made') / max(1, tot('scramble_att')),
        'sand_save_pct': tot('sand_saves') / max(1, tot('sand_att')),
        'putts_per_round': tot('putts') / n,
        'three_putts_per_round': tot('three_putts') / n,
        'eagles': tot('eagles') / n,
        'birdies': tot('birdies') / n,
        'pars': tot('pars') / n,
        'bogeys': tot('bogeys') / n,
        'doubles_plus': (tot('doubles') + tot('worse')) / n,
        'penalties': tot('penalties') / n,
        'aces_per_1000': 1000 * tot('aces') / n,
        'sg_ott': tot('sg_ott') / n,
        'sg_app': tot('sg_app') / n,
        'sg_arg': tot('sg_arg') / n,
        'sg_putt': tot('sg_putt') / n,
    }
    for par in (3, 4, 5):
        s = sum(r.par_scores[par][0] for r in rounds)
        c = sum(r.par_scores[par][1] for r in rounds)
        out[f'par{par}_avg'] = s / c if c else 0.0
    return out
