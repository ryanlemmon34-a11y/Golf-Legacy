"""Earned Premier Tour rights independent of membership (2090 world audit: Jack H. Harris, a world top-five
player and five-time major champion, stayed a Challenger member for a decade and was shut out of ordinary
Premier fields).

Run from the project folder:  python -m unittest tests.test_entry_rights -v
"""
from __future__ import annotations

import pickle
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import careers                                              # noqa: E402
from golfsim.cards import apply_cards, premier_circuit, winner_exemptions   # noqa: E402
from golfsim.population import generate_world                            # noqa: E402
from golfsim.season import FULL_STATUS, PREMIER_TOURS, Season            # noqa: E402

WORLD = generate_world(seed=11)


def season(results=(), year=2027):
    """A season on 1 January of `year`, with earlier results recorded first: (series, year, gid, pos)."""
    s = Season(pickle.loads(pickle.dumps(WORLD)), seed=11, workers=1, calendar='v1')   # (classic weeks)
    s.refresh_people(year)
    for sid, y, gid, pos in results:
        s.ctx.add_result(sid, y, [(gid, pos)])
    s.start_finances(year)
    return s


def challenger_member(s, tour='CH_ASIA'):
    return next(g for g in s.world.golfers if g.tour == tour and g.status == 'pro' and g.lifestyle == 'full_time')


def premier_event(s, tour='PT_ASIA_PACIFIC'):
    return next(x for x in s.cal.series if x.tier == 1 and x.category == 'standard' and x.tour == tour)


def synthetic_money(s, year=2027, seed=3):
    """A money list for every professional on their own tour (members also on the Premier list)."""
    rng = random.Random(seed)
    for g in s.world.golfers:
        if g.status == 'pro':
            keys = [g.tour] + (['PREMIER'] if g.tour in PREMIER_TOURS else [])
            for k in keys:
                s.money[(k, year)][g.id] = rng.random() * 1e6 * (1 + g.overall / 10)


class ExemptionWindowTests(unittest.TestCase):
    def test_windows_and_reasons(self):
        s = season()
        a, b, c = [g.id for g in s.world.golfers[:3]]
        for sid, y, gid in (('USA_OPEN', 2022, a), ('USA_OPEN', 2021, b), ('PT_PACIFIC_COAST_PRO_AM', 2025, c),
                            ('PT_PACIFIC_COAST_PRO_AM', 2024, a)):
            s.ctx.add_result(sid, y, [(gid, 1)])
        held = winner_exemptions(s, 2027)
        self.assertEqual(held.get(a), 'won the 2022 USA Open')      # a major: five seasons (2022-2026)
        self.assertNotIn(b, held)                                    # expired
        self.assertEqual(held.get(c), 'won the 2025 Pacific Coast Pro-Am')   # a Premier event: two seasons
        self.assertNotIn(c, winner_exemptions(s, 2028))
        self.assertEqual(winner_exemptions(s, 2028).get(a), None)    # the 2022 major lapses after 2027


class AccessionTests(unittest.TestCase):
    def test_nonmember_major_champion_earns_a_card_and_exempt_rights(self):
        s = season()
        synthetic_money(s)
        harris = challenger_member(s)
        s.money[('CH_ASIA', 2027)].pop(harris.id, None)              # never played his home tour
        s.money[('PREMIER', 2027)][harris.id] = 50_000.0              # little Premier money either
        s.ctx.add_result('USA_OPEN', 2027, [(harris.id, 1)])
        apply_cards(s, 2027)
        self.assertEqual(harris.tour, premier_circuit(harris))
        self.assertIn(harris.tour, PREMIER_TOURS)
        self.assertEqual(s.card_reasons[2028][harris.id], 'Premier card earned: won the 2027 USA Open')
        moves = [m for m in s.card_log[2027] if m[0] == harris.id]
        self.assertEqual(len(moves), 1)                              # one membership, one recorded change
        self.assertEqual(moves[0][1:3], ('CH_ASIA', harris.tour))
        s.premier_rights(2028)
        self.assertEqual(s.rights[2028][harris.id], ('exempt', 'won the 2027 USA Open'))

    def test_premier_money_earns_a_card_without_a_win(self):
        s = season()
        synthetic_money(s)
        rich, poor = [g for g in s.world.golfers if g.tour == 'CH_EUROPE' and g.status == 'pro'
                      and g.lifestyle == 'full_time'][:2]
        pm = s.money[('PREMIER', 2027)]
        members = sorted((g for g in s.world.golfers if g.tour in PREMIER_TOURS and g.lifestyle == 'full_time'),
                         key=lambda g: s.standing_key(pm, g.id))
        pm[rich.id] = pm[members[199].id] + 1.0                       # ahead of the last member to keep a card
        pm[poor.id] = pm[members[199].id] - 1.0
        for g in (rich, poor):
            s.money[('CH_EUROPE', 2027)][g.id] = 0.0
        apply_cards(s, 2027)
        self.assertIn(rich.tour, PREMIER_TOURS)
        self.assertTrue(s.card_reasons[2028][rich.id].startswith('Premier card earned: $'))
        self.assertNotIn(poor.tour, PREMIER_TOURS)

    def test_ranking_alone_promotes_no_one(self):
        """A highly ranked golfer with no Premier win and no Premier money is promoted only by the
        ordinary pathways: no automatic promotion of everyone near the top of the ranking."""
        s = season()
        synthetic_money(s)
        g = challenger_member(s, 'CH_EUROPE')
        s.wr_pos[g.id] = 3
        s.money[('CH_EUROPE', 2027)][g.id] = 0.0
        s.money[('PREMIER', 2027)].pop(g.id, None)
        apply_cards(s, 2027)
        self.assertNotIn(g.tour, PREMIER_TOURS)

    def test_part_timers_are_not_carded(self):
        s = season()
        synthetic_money(s)
        g = challenger_member(s)
        g.lifestyle = 'part_time'
        s.ctx.add_result('USA_OPEN', 2027, [(g.id, 1)])
        apply_cards(s, 2027)
        self.assertNotIn(g.tour, PREMIER_TOURS)

    def test_amateur_major_champion_turns_pro_onto_the_premier_tour(self):
        s = season()
        g = next(x for x in s.world.golfers if x.status == 'amateur' and not x.tour.startswith('CO_'))
        s.ctx.add_result('BRITANNIA_OPEN', 2026, [(g.id, 1)])
        careers.turn_pro(s, g, 2027, 40, 'from the amateur ranks', winner_exemptions(s, 2028).get(g.id))
        self.assertEqual(g.tour, premier_circuit(g))
        self.assertEqual(s.card_reasons[2028][g.id], 'Premier card earned: won the 2026 Britannia Open')
        other = next(x for x in s.world.golfers if x.status == 'amateur' and x.id != g.id
                     and not x.tour.startswith('CO_'))
        careers.turn_pro(s, other, 2027, 40, 'from the amateur ranks')
        self.assertNotIn(other.tour, PREMIER_TOURS)


class FieldPriorityTests(unittest.TestCase):
    def test_exempt_nonmember_goes_ahead_of_members_without_exemptions(self):
        probe = season()
        harris = challenger_member(probe)
        s = season([('TOUR_MASTERS', 2026, harris.id, 1)])
        harris = s.g[harris.id]
        ev = premier_event(s)
        self.assertEqual(s.winners_now()[harris.id], 'won the 2026 Tour Masters')
        self.assertTrue(s.eligible(harris, ev, ev.week))
        cond = next(s.g[g] for g, (r, _) in s.rights[2027].items() if r == 'conditional')
        full = next(s.g[g] for g, (r, _) in s.rights[2027].items() if r == 'full')
        self.assertLess(s.priority(harris, ev), s.priority(full, ev))
        self.assertLess(s.priority(harris, ev), s.priority(cond, ev))
        self.assertEqual(s.entry_route(harris, ev), 'WINNER EXEMPTION (not a member)')
        # he may still play below the Premier Tour: no ban on lower-tour starts
        ch = next(x for x in s.cal.series if x.tour == 'CH_ASIA' and x.category == 'regular')
        self.assertTrue(s.eligible(harris, ch, ch.week))

    def test_without_an_exemption_a_nonmember_queues_behind_members(self):
        s = season()
        g = challenger_member(s)
        ev = premier_event(s)
        cond = next(s.g[x] for x, (r, _) in s.rights[2027].items() if r == 'conditional')
        self.assertGreater(s.priority(g, ev), s.priority(cond, ev))

    def test_a_win_during_the_season_is_an_exemption_from_that_week(self):
        s = season()
        g = challenger_member(s)
        cond = next(s.g[x] for x, (r, _) in s.rights[2027].items() if r == 'conditional')
        ev = premier_event(s)
        before = s.priority(cond, ev)
        for who, sid in ((g, 'PT_PACIFIC_COAST_PRO_AM'), (cond, 'USA_OPEN')):
            s.ctx.add_result(sid, 2027, [(who.id, 1)])
            s.earned[2027][who.id] = f'won the 2027 {s.cal.by_id[sid].name}'   # as record_event does
        self.assertEqual(s.priority(g, ev)[0], 1)
        self.assertLess(s.priority(cond, ev), before)                # a conditional member who wins is exempt
        self.assertEqual(s.entry_route(cond, ev), 'PREMIER EXEMPT')
        # the same exemptions rebuilt from the recorded results (a save from before they were kept)
        s.earned.pop(2027)
        self.assertEqual(s.winners_now()[g.id], 'won the 2027 Pacific Coast Pro-Am')
        self.assertEqual(s.winners_now()[cond.id], 'won the 2027 USA Open')

    def test_exemptions_and_cards_survive_save_and_reload(self):
        s = season()
        synthetic_money(s)
        g = challenger_member(s)
        s.ctx.add_result('USA_OPEN', 2027, [(g.id, 1)])
        s.earned[2027][g.id] = 'won the 2027 USA Open'
        t = pickle.loads(pickle.dumps(s))
        self.assertEqual(t.winners_now()[g.id], 'won the 2027 USA Open')
        apply_cards(t, 2027)
        self.assertIn(t.g[g.id].tour, PREMIER_TOURS)
        self.assertEqual(sum(1 for m in t.card_log[2027] if m[0] == g.id), 1)
        t.close()
        s.close()

    def test_full_status_counts_only_members(self):
        s = season()
        rights = [r for r, _ in s.rights[2027].values()]
        self.assertEqual(rights.count('full') + rights.count('exempt'), FULL_STATUS)


class InSeasonTests(unittest.TestCase):
    def test_a_major_won_in_play_is_an_exemption_from_that_week(self):
        """The Tour Masters (week 18) played in full: its champion holds an exemption from then on,
        recorded by record_event (not only rebuilt from results)."""
        s = season()
        eds = [e for e in s.cal.editions(2027) if e.week == 18]
        s.run_week(2027, 18, eds)
        s.close()
        w = s.results['2027:TOUR_MASTERS'].winner()
        self.assertEqual(s.earned[2027][w], 'won the 2027 Tour Masters')


if __name__ == '__main__':
    unittest.main()
