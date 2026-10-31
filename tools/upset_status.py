"""Whether an edition's recorded pre-event estimate (Biggest Upsets, roadmap B1/B2) can be shown for its winner, and
if not, why -- one rule and one wording for the statistics rows, the Biggest Upsets page (ranking and coverage
line), the edition's estimate panel and the tournament story.

Plain definitions only (no engine import): the supported model versions are declared here, and
tests/test_upset_examples.py checks that they include golfsim.upsets.VERSION.
"""
from __future__ import annotations

SUPPORTED = ('upset-model-1',)        # the model versions the observer reads (golfsim/upsets.py VERSION)
NO_REASON = 'no reason recorded'
NOT_RECORDED = 'not recorded: played before estimates were kept, and none is worked out afterwards'
WINNER_MISSING = ('estimate recorded, but the winner\'s chance is not in it (the estimate names no winner matching '
                  'the result)')
OTHER_SITE = 'estimate recorded for the first site only'


def unsupported(model):
    return f'unsupported model {model} (this build reads {", ".join(SUPPORTED)} only)'


def not_estimated(why):
    return f'not estimated: {why or NO_REASON}'


def status(rec, winner, site=0):
    """(kind, reason) for an edition's `upset` record and its winner: ('ok', None) when the winner's recorded chance
    can be shown and ranked; otherwise kind is 'not_recorded', 'unsupported', 'not_estimated', 'other_site' or
    'winner_missing', with the reason in words."""
    if not rec:
        return 'not_recorded', NOT_RECORDED
    if rec.get('model') not in SUPPORTED:
        return 'unsupported', unsupported(rec.get('model'))
    if not rec.get('estimated'):
        return 'not_estimated', not_estimated(rec.get('why'))
    if site != rec.get('site', 0):
        return 'other_site', OTHER_SITE
    if rec.get('winner') is None or rec.get('winner') != winner or rec.get('p') is None:
        return 'winner_missing', WINNER_MISSING
    return 'ok', None
