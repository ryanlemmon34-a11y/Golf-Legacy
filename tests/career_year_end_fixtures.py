"""Write the example year-end view fixtures of docs/career/YEAR_END.md (docs/career/year_end_fixtures/*.json): the
committed career view's 'year_end' model (golfsim.career.year_end_view) at each stage, and a planner week with the
paid-work option, on the career test world (seed 11, scale 0.05). Test set-ups are marked: the rested fixture golfer
is given a series-amateur tour and a coach and caddie; the residence example takes control of golfer 146, whom the
residence rule would move.

Run from the project folder:  python tests/career_year_end_fixtures.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import test_career_year_end as T                                      # noqa: E402
from golfsim import career as CA                                      # noqa: E402

OUT = ROOT / 'docs' / 'career' / 'year_end_fixtures'


def dump(s, name, model=None):
    OUT.mkdir(parents=True, exist_ok=True)
    v = model if model is not None else CA.view(s.season, s.cursor)['year_end']
    (OUT / f'{name}.json').write_text(json.dumps(v, indent=1, ensure_ascii=False, default=list) + '\n')
    print(name)


def main():
    # keep: review -> winter choices (career + staff) -> 1 January
    s = T.at_review()
    s.season.g[s.season.career.golfer_id].tour = 'AM_NORTH_AMERICA'
    T.staffed(s)
    dump(s, '1_season_review')
    T.decide(s, T.one(s, 'season_review'), 'keep')
    s.advance_career('next', op_key='w0')
    dump(s, '2_winter_choices')
    T.decide(s, T.one(s, 'winter_career'), 'turn_pro')
    T.decide(s, T.one(s, 'winter_staff'), 'let_go_caddie')
    dump(s, '2b_winter_choices_answered')
    s.advance_career('next', op_key='w1')
    s.advance_career('next', op_key='w2')
    g = s.season.g[s.season.career.golfer_id]
    for d in s.season.career.pending(CA.OFFER_KINDS):
        T.decide(s, d, 'decline')
    if not s.season.needs_paid_work(g, 2029):
        g.cash = g.backing = g.backer_funds = 0.0                     # (test set-up: short of money)
        s.season.ledgers.get(2028, {}).pop(g.id, None)
    wk = CA.planner(s.season, s.cursor, 2029, 1)['weeks'][0]
    dump(s, '6_planner_week_paid_work', {'work': wk['work'], 'command_week': {'kind': 'work'}})
    s.close()
    # residence
    s = T.at_review()
    c = s.season.career
    c.golfer_id = c.stints[0]['golfer_id'] = 146
    s._commit()
    T.decide(s, T.one(s, 'season_review'), 'keep')
    s.advance_career('next', op_key='w0')
    for d in c.pending(CA.YEAR_END_KINDS):
        T.decide(s, d, d['options'][0])
    s.advance_career('next', op_key='w1')
    dump(s, '3_winter_residence')
    s.close()
    # switch: the AI's winter, then the newcomer choice
    s = T.at_review()
    T.decide(s, T.one(s, 'season_review'), 'switch')
    dump(s, '4_switched_winter_ai')
    s.advance_career('next', op_key='w')
    dump(s, '5_choose_newcomer')
    s.close()


if __name__ == '__main__':
    main()
