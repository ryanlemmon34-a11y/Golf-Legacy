"""Contextual event labels and qualifying targets (read only).

Series names are kept as they are (ids, names, schedules and recorded history are unchanged). Where two series of a
calendar share a name -- e.g. the USA's national amateur championship (NATIONAL_AMATEUR_USA, stroke play, its week
varies by world) and the USA Amateur (USA_AMATEUR, match play, week 33) are both "USA Amateur Championship" -- the
label adds what tells them apart: the format, the kind of championship or tour, and the week.

A qualifying event's target is the event it feeds, from the rules that build its field (e.g. USA Amateur Qualifying,
week 30, feeds the USA Amateur, week 33 -- not the national championship); `target` returns it with its week.
"""
from __future__ import annotations

from .calendar import TOUR_BY_KEY

CATEGORY_WORDS = {'national_amateur': 'national amateur championship', 'elite_amateur': 'open amateur championship',
                  'national_open': 'national open', 'college_postseason': 'college post-season'}

_cache = {}


def _series(cal):
    return {s.series_id: s for s in cal.series}


def _duplicates(cal):
    key = id(cal)
    hit = _cache.get(key)
    if hit is not None and hit[0] is cal:
        return hit[1]
    names = {}
    for s in cal.series:
        names.setdefault(s.name, []).append(s)
    dup = {n: v for n, v in names.items() if len(v) > 1}
    _cache[key] = (cal, dup)
    return dup


def _fmt(s):
    return 'match play' if s.match_play else f'{s.holes}-hole stroke play'


def _kind(s):
    if s.category in CATEGORY_WORDS:
        return CATEGORY_WORDS[s.category]
    t = TOUR_BY_KEY.get(s.tour)
    return t.name if t else s.kind


def label(cal, series_id):
    """The series' name, or, when another series of this calendar has the same name, the name with what tells them
    apart: '<name> (<format or kind>, week <n>)'. Unknown ids are returned as they are."""
    s = _series(cal).get(series_id)
    if s is None:
        return series_id
    same = _duplicates(cal).get(s.name)
    if not same:
        return s.name
    others = [o for o in same if o is not s]
    parts = []
    if any(_fmt(o) != _fmt(s) for o in others):
        parts.append(_fmt(s))
    if any(_kind(o) != _kind(s) for o in others) or not parts:
        parts.append(_kind(s))
    parts.append(f'week {s.week}')
    return f'{s.name} ({", ".join(parts)})'


def target(cal, series_id):
    """The event a qualifying series feeds: {'id', 'label', 'week'} or None (not a qualifier, or its target is not in
    this calendar). From the field rules: USA Open local -> final qualifying -> USA Open; Britannia regional -> final
    -> Britannia Open; USA Amateur Qualifying -> USA Amateur; club professional sectionals -> their championship;
    Q-school stages in order; college regionals -> the national championship."""
    by = _series(cal)
    spec = cal.spec
    t = None
    if series_id == 'USA_AMATEUR_QUALIFYING':
        t = 'USA_AMATEUR'
    elif series_id in {sid for sid, _, _ in spec.usa_local}:
        t = 'USA_OPEN_FINAL'
    elif series_id in ('USA_OPEN_FINAL', 'USA_OPEN_FINAL_INTL'):
        t = 'USA_OPEN'
    elif series_id in {sid for sid, _, _ in spec.britannia_regional}:
        t = 'BRITANNIA_FINAL'
    elif series_id == 'BRITANNIA_FINAL':
        t = 'BRITANNIA_OPEN'
    elif series_id == 'CLUB_PRO_SECTIONALS':
        t = 'CLUB_PRO_CHAMPIONSHIP'
    else:
        chain = ('PT_QSCHOOL_PRE', 'PT_QSCHOOL_FIRST', 'PT_QSCHOOL_SECOND', 'PT_QSCHOOL_FINAL',
                 'EU_QSCHOOL_FIRST', 'EU_QSCHOOL_SECOND', 'EU_QSCHOOL_FINAL')
        if series_id in chain[:3] or series_id in chain[4:6]:
            t = chain[chain.index(series_id) + 1]
        else:
            s = by.get(series_id)
            if s is not None and s.category == 'college_postseason' and 'REGIONAL' in series_id:
                t = next((x for x in by if x.startswith('COLLEGE_NATIONAL')), None)
    if t is None or t not in by:
        return None
    return {'id': t, 'label': label(cal, t), 'week': by[t].week}


def context(cal, series_id):
    """{'id', 'name', 'label', 'week', 'target'} for a series (read only)."""
    s = _series(cal).get(series_id)
    if s is None:
        return {'id': series_id, 'name': None, 'label': series_id, 'week': None, 'target': None}
    return {'id': series_id, 'name': s.name, 'label': label(cal, series_id), 'week': s.week,
            'target': target(cal, series_id)}
