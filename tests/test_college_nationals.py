"""The college national championship's field (rules 2026-11-12).

The places are still the first 39 finishers of each of the four regionals, with the same field limit; then a
qualifier who cannot play that week withdraws. "Can play" is the same set the college post-season already uses
(`d1`: a D1 college golfer who is free that week -- not injured, not retired, not committed elsewhere). The place is
not passed down to the 40th finisher (there is no reserve list); the reason is kept and written in the golfer's
career history. Worlds saved before the rule keep the field as earned.

Small fixtures only (no season is played). Run from the project folder:
    python -m unittest tests.test_college_nationals -v
"""
from __future__ import annotations

import sys
import unittest
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import rules as R                                            # noqa: E402
from golfsim.season import Season                                         # noqa: E402

YEAR = 2055
FIRST = 2027
NATIONALS_WEEK = 22
REGIONAL_WEEK = 21


def golfer(gid, tour='CO_US_D1', lifestyle='full_time'):
    return NS(id=gid, tour=tour, status='amateur', lifestyle=lifestyle, country='USA')


class Stub(Season):
    """A Season with only what the college post-season fields read (no world, no calendar, no play)."""

    def __init__(self, golfers, finishers, new_rules=True, busy=()):
        self._golfers = list(golfers)
        self.g = {g.id: g for g in golfers}
        self.am_pos = {}
        self.injured = {}
        self.first_year = FIRST
        self.seed = 11
        self.history = defaultdict(list)
        self.college_nationals_availability = new_rules
        self.nationals_withdrawn = defaultdict(dict)
        self.busy = set(busy)
        self._finishers = finishers                     # regional k -> [(gid, pos)]
        self.ctx = NS(finishers=lambda sid, year: self._finishers[int(sid.rsplit('_', 1)[1])])
        # what update_fatigue reads (the injury clock)
        self.fatigue = defaultdict(float)
        self._week_load, self._week_event, self.week_rounds = {}, {}, {}

    def active_golfers(self):
        return [g for g in self._golfers if g.lifestyle != 'retired']

    def observed_form(self, gid):
        return 0.0

    def free(self, g):
        """What special_field passes in: Season.available (injury, retirement, the week's other commitments)."""
        return g.id not in self.injured and g.lifestyle != 'retired' and g.id not in self.busy

    def nationals(self, field=156):
        s = NS(series_id='COLLEGE_NATIONAL_CHAMPIONSHIP', field=field, name='College National Championship')
        ed = NS(series=s, week=NATIONALS_WEEK)
        return self.college_postseason(ed, YEAR, self.free)[0]


def regionals(n=45, start=1000, missed_every=0):
    """Four regionals of `n` finishers each (positions 1..n in order); every `missed_every`-th has no position
    (withdrew during the regional), so 'the first 39 with a position' is not simply the first 39 rows."""
    out, golfers = {}, []
    for k in range(1, 5):
        rows = []
        for i in range(n):
            gid = start + 100 * k + i
            golfers.append(golfer(gid))
            pos = None if missed_every and i % missed_every == missed_every - 1 else i + 1
            rows.append((gid, pos))
        out[k] = rows
    return out, golfers


def earned(finishers, field=156):
    ids = []
    for k in range(1, 5):
        ids += [gid for gid, pos in finishers[k] if pos is not None][:39]
    return ids[:field]


class FieldTests(unittest.TestCase):
    def test_healthy_qualifiers_all_play_in_the_earned_order(self):
        fin, gs = regionals(missed_every=7)
        s = Stub(gs, fin)
        self.assertEqual(s.nationals(), earned(fin))
        self.assertEqual(len(s.nationals()), 156)
        self.assertEqual(dict(s.nationals_withdrawn), {})

    def test_an_injured_qualifier_withdraws_and_no_one_is_promoted(self):
        fin, gs = regionals()
        s = Stub(gs, fin)
        hurt = fin[2][10][0]
        s.injured[hurt] = (s.abs_week(YEAR, NATIONALS_WEEK) + 12, 'hand', 12)
        field = s.nationals()
        want = [gid for gid in earned(fin) if gid != hurt]
        self.assertEqual(field, want)                               # the same order, one place fewer
        self.assertEqual(len(field), 155)
        self.assertNotIn(fin[2][39][0], field)                      # the 40th finisher is not promoted
        self.assertEqual(s.nationals_withdrawn[YEAR], {hurt: 'injured'})
        self.assertTrue(any('Withdrew from the College National Championship (injured)' in t
                            for _, _, t in s.history[hurt]))

    def test_each_reason_is_recorded(self):
        fin, gs = regionals()
        retired, gone, busy, hurt = fin[1][0][0], fin[1][1][0], fin[3][5][0], fin[4][38][0]
        s = Stub(gs, fin, busy={busy})
        s.g[retired].lifestyle = 'retired'
        s.g[gone].tour = 'CO_INTL'                                  # no longer a D1 golfer
        s.injured[hurt] = (s.abs_week(YEAR, NATIONALS_WEEK) + 3, 'back', 3)
        field = s.nationals()
        self.assertEqual(s.nationals_withdrawn[YEAR], {retired: 'retired', gone: 'no longer a D1 college golfer',
                                                        busy: 'could not play that week', hurt: 'injured'})
        self.assertEqual(field, [g for g in earned(fin) if g not in (retired, gone, busy, hurt)])

    def test_the_field_limit_applies_before_withdrawals(self):
        fin, gs = regionals()
        s = Stub(gs, fin)
        cut = earned(fin, field=100)
        s.injured[cut[0]] = (s.abs_week(YEAR, NATIONALS_WEEK) + 2, 'wrist', 2)
        field = s.nationals(field=100)
        self.assertEqual(field, cut[1:])                            # 99: the 101st earned place stays out
        self.assertNotIn(earned(fin)[100], field)

    def test_deterministic(self):
        fin, gs = regionals(missed_every=5)
        a, b = Stub(gs, fin), Stub(gs, fin)
        for s in (a, b):
            s.injured[fin[1][3][0]] = (s.abs_week(YEAR, NATIONALS_WEEK) + 1, 'ankle', 1)
        self.assertEqual(a.nationals(), b.nationals())

    def test_saves_from_before_the_rule_keep_the_field_as_earned(self):
        fin, gs = regionals()
        s = Stub(gs, fin, new_rules=False)
        s.injured[fin[2][10][0]] = (s.abs_week(YEAR, NATIONALS_WEEK) + 12, 'hand', 12)
        self.assertEqual(s.nationals(), earned(fin))
        self.assertEqual(dict(s.nationals_withdrawn), {})


class AvailableWeekBoundary(unittest.TestCase):
    """The injury clock (Season.injure / update_fatigue): injured at the end of week W for n weeks, a golfer misses
    weeks W+1..W+n and can enter again from week W+n+1."""

    def field_after(self, inj_week, weeks):
        fin, gs = regionals()
        s = Stub(gs, fin)
        gid = fin[1][0][0]
        s.injuries = defaultdict(list)
        s.injure(gid, YEAR, inj_week, weeks, 'knee')
        for w in range(inj_week, NATIONALS_WEEK):                    # the weeks' ends before the nationals
            s.update_fatigue(YEAR, w)
        return gid, s.nationals()

    def test_available_in_the_nationals_week_plays(self):
        gid, field = self.field_after(REGIONAL_WEEK - 1, 1)          # out week 21 only; back for week 22
        self.assertIn(gid, field)

    def test_out_through_the_nationals_week_withdraws(self):
        gid, field = self.field_after(REGIONAL_WEEK, 1)              # injured at the regional: out week 22
        self.assertNotIn(gid, field)

    def test_back_the_week_after_still_withdraws(self):
        gid, field = self.field_after(REGIONAL_WEEK - 1, 2)          # out weeks 21-22, available week 23
        self.assertNotIn(gid, field)


class RealCases(unittest.TestCase):
    """The three golfers found in the Test2 save (seed 386509): injured at their regional in week 21 and archived as
    playing the week-22 national championship anyway. Their recorded injuries, replayed on the injury clock, now
    withdraw them; everyone else who earned a place still plays."""

    CASES = (   # (year, regional, regional position, gid, kind, weeks out, available (year, week)) as archived
        (2055, 2, 31, 27970, 'ankle', 12, (2055, 34)),   # Barnaby Read: played 71/80/74/81
        (2055, 2, 2, 30440, 'hand', 12, (2055, 34)),     # Cole Lowery: played 76/86
        (2027, 3, 18, 4421, 'back', 2, (2027, 24)),      # Robert Miller: played 83/87
    )

    def test_each_withdraws_and_the_rest_play(self):
        for year, k, pos, gid, kind, weeks, available in self.CASES:
            fin, gs = regionals()
            rows = fin[k]
            rows[pos - 1] = (gid, pos)                                # the golfer at their archived position
            gs.append(golfer(gid))
            s = Stub(gs, fin)
            s.first_year = FIRST
            s.injuries = defaultdict(list)
            s.injure(gid, year, REGIONAL_WEEK, weeks, kind)
            back = s.injured[gid][0]
            self.assertEqual(back, s.abs_week(*available))           # the archived "available" week
            s.update_fatigue(year, REGIONAL_WEEK)                       # the regional week ends
            field = s.college_postseason(NS(series=NS(series_id='COLLEGE_NATIONAL_CHAMPIONSHIP', field=156,
                                                      name='College National Championship'), week=NATIONALS_WEEK),
                                         year, s.free)[0]
            self.assertNotIn(gid, field, gid)
            self.assertEqual(s.nationals_withdrawn[year], {gid: 'injured'})
            self.assertEqual(field, [g for g in earned(fin) if g != gid])


class RulesText(unittest.TestCase):
    def test_versioned(self):
        self.assertGreaterEqual(R.RULES_VERSION, '2026-11-12')
        self.assertIn('2026-11-12', dict(R.VERSIONS))
        self.assertEqual(R.RULES['college-postseason'][2], '2026-11-12')
        self.assertIn('not passed', R.RULES['college-postseason'][1])


if __name__ == '__main__':
    unittest.main()
