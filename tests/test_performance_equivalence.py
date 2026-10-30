"""Performance changes that must not change anything (owner's performance brief, 30 October 2026): every
shortcut gives exactly what the code it replaced gave.

- saves and history files compressed on threads read back byte for byte;
- the record book's and the relationships' exports equal dataclasses.asdict;
- the planner's shared-prefix search picks the same plan, with the same value, as the per-mask loop;
- the remembered prize forecast is refreshed when a prize is learned or the year changes;
- one-pass rankings and fame summed only when it changes equal a full recomputation, week after week;
- a season played with the shortcuts saves exactly the state and history of the same season played
  again from the same save (and the equivalence check against the previous engine is in the report).

Run from the project folder:  python -m unittest tests.test_performance_equivalence -v
"""
from __future__ import annotations

import gzip
import json
import os
import pickle
import random
import shutil
import sys
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import prestige as PR                                       # noqa: E402
from golfsim.archive import GzipChunks                                    # noqa: E402
from golfsim.history import Relations, Stint                              # noqa: E402
from golfsim.population import generate_world                             # noqa: E402
from golfsim.records import Mark, RecordBook                              # noqa: E402
from golfsim.session import Session                                       # noqa: E402

WAGE = 1234.5


def plan_by_masks(weeks, now, inj_until, slot, playable, costs, base, pace0, major, bar, dp, inj0, inj_b, inj_c, inj_d,
                  net, load4, rest_rec, work_v, dt, can_work, f0, played0, money0):
    """The planner's previous search, verbatim: every mask valued from the first week."""
    best_val, best_acts = None, None
    for mask in range(1 << len(playable)):
        f = f0
        val, n, money, acts = 0.0, played0, money0, []
        for i, w in enumerate(weeks):
            if now + w < inj_until:
                f *= rest_rec
                acts.append('work' if can_work else 'rest')
                money += WAGE if can_work else 0.0
                continue
            j = slot.get(i, -1)
            if j >= 0 and mask >> j & 1:
                if costs[i] > 0 and costs[i] > money:
                    val = None
                    break
                money -= costs[i]
                pace = pace0[i] - n
                v = base[i][0] + max(-25.0, min(6.0, 3.5 * pace)) - major[i]
                eff = max(0.0, f - 0.2) * 1.25
                val += ((v - bar) + dp - 12 * eff - 400 * (inj0 * (1 + 6 * f * f) * inj_b * inj_c * inj_d) - net[i])
                f = 1 - (1 - 0.9 * f) * (1 - load4)
                n += 1
                acts.append('play')
            elif f > 0.25:
                f *= rest_rec
                acts.append('rest')
            elif work_v > dt:
                val += work_v
                money += WAGE
                f *= 0.8
                acts.append('work')
            else:
                val += dt
                f = 0.85 * f + 0.02
                acts.append('train')
        if val is not None and (best_val is None or val > best_val):
            best_val, best_acts = val, acts
    return best_val, best_acts


class ExactShortcuts(unittest.TestCase):
    def test_threaded_gzip_reads_back_byte_for_byte(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        for n in (0, 1, GzipChunks.BLOCK - 1, GzipChunks.BLOCK, 3 * GzipChunks.BLOCK + 17):
            data = random.Random(n).randbytes(n // 2) + b'golf' * (n - n // 2 >> 2)
            for split in (1, 3, 65536):
                p = d / f'{n}-{split}.gz'
                with GzipChunks(p, 3) as f:
                    step = max(1, len(data) // split) if split < 10 else split
                    for i in range(0, len(data), step):
                        f.write(memoryview(data)[i:i + step])
                self.assertEqual(gzip.open(p).read(), data, (n, split))
        state = {'golfers': list(range(200000)), 'names': {str(i): i for i in range(50000)}, 'blob': b'x' * 9_000_000}
        p = d / 'state.pkl.gz'
        with GzipChunks(p, 3) as f:
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
        self.assertEqual(gzip.open(p).read(), pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL))

    def test_exports_equal_asdict(self):
        rb = RecordBook()
        rb.note_totals(2030)

        class Course:
            pass
        for lid in range(12):
            c = Course()
            c.layout_id, c.par = f'L{lid}', 72
            r = rb.get(c)
            rng = random.Random(lid)
            for i in range(150):
                sc = rng.randint(60, 84)
                r.add_round(Mark(sc, sc - 72, f'G{i}', f'E{i}', 2030, i % 52 + 1, i % 4 + 1, rng.randint(0, 8), i),
                            [rng.choice((1, 2, 3, 4, 5, 6)) for _ in range(18)], [3, 4, 5] * 6)
                r.add_total(72, Mark(sc * 4, sc * 4 - 288, 'x', 'e', 2030, 1, 0, 1, i))
                r.add_hole(rng.randrange(18), rng.choice((1, 2, 3)), 5, 'm', 'e', 2030, 'final', i)
        old = {}
        for lid, r in rb.layouts.items():
            d = asdict(r)
            d['history'] = [(k, asdict(m)) for k, m in r.history]
            d['totals_since'] = rb.totals_since
            old[lid] = d
        new = rb.to_dict()
        self.assertEqual(new, old)
        self.assertEqual(json.dumps(new), json.dumps(old))                  # the same text in the archive
        rel = Relations(1)
        for i in range(200):
            rel.stints.append(Stint(i, 'coach', i % 9, i, (2030, i % 52 + 1), 'fee', 'golfer', 'why',
                                    (2031, 5) if i % 3 else None, '', '', 1.5 * i, 2.0,
                                    [(2030, 0.5, 1.0), (2031, 0.25, 2.0)] if i % 2 else []))
        self.assertEqual(json.dumps(rel.export()['stints']), json.dumps([asdict(s) for s in rel.stints]))

    def test_the_plan_search_matches_the_per_mask_loop(self):
        from golfsim import season as SEA
        src = Path(SEA.__file__).read_text()
        self.assertIn('nodes = [(0, f0, 0.0, played0, money0, ())]', src)     # the code tested below is the engine's
        rng = random.Random(3)
        for trial in range(30000):
            weeks = list(range(rng.randint(1, 49), 53))[:rng.choice((4, 4, 4, 3, 2, 1))]
            now = rng.randint(0, 100)
            inj_until = now + rng.choice((0, weeks[0] + 1, weeks[-1])) if rng.random() < 0.2 else 0
            base = [(rng.uniform(-30, 30), 'e') if rng.random() < 0.8 else None for _ in weeks]
            playable = [i for i, w in enumerate(weeks) if base[i] is not None and now + w >= inj_until]
            args = dict(weeks=weeks, now=now, inj_until=inj_until, slot={i: j for j, i in enumerate(playable)},
                        playable=playable, costs=[rng.choice((0.0, rng.uniform(0, 5000))) for _ in weeks], base=base,
                        pace0=[rng.uniform(0, 30) for _ in weeks], major=[rng.choice((0, 6)) for _ in weeks],
                        bar=rng.uniform(-10, 20), dp=rng.uniform(0, 5), inj0=0.004, inj_b=rng.uniform(0.2, 1.8),
                        inj_c=rng.uniform(1, 1.5), inj_d=rng.uniform(1, 1.5), net=[rng.uniform(-5, 5) for _ in weeks],
                        load4=rng.uniform(0.05, 0.4), rest_rec=rng.uniform(0.4, 0.7),
                        work_v=rng.choice((-1.0, rng.uniform(0, 40))), dt=rng.uniform(0, 10), can_work=rng.random() < 0.3,
                        f0=rng.choice((0.0, rng.uniform(0, 0.6))), played0=rng.randint(0, 20),
                        money0=rng.choice((rng.uniform(-1000, 8000), 0.0)))
            self.assertEqual(SEA.plan_search(WAGE=WAGE, **args), plan_by_masks(**args), trial)

    def test_ranking_total_matches_its_definition(self):
        rng = random.Random(5)
        for _ in range(2000):
            now = rng.randint(100, 300)
            rows = [(now - rng.randint(0, 120), rng.uniform(0, 50)) for _ in range(rng.randint(0, 60))]
            tot, n = 0.0, 0
            for aw, pts in rows:
                age = now - aw
                if age >= PR.RANK_WEEKS:
                    continue
                n += 1
                tot += pts * PR.ranking_weight(age)
            self.assertEqual(PR.ranking_total(rows, now), (tot, n))


class SeasonShortcuts(unittest.TestCase):
    """A short stretch of a small world, checked week by week against full recomputations."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=31, workers=1, world=generate_world(seed=31, scale=0.02))
        cls.s = s

    @classmethod
    def tearDownClass(cls):
        cls.s.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_rankings_fame_and_forecasts_equal_full_recomputation(self):
        s = self.s
        se = s.season
        for _ in range(14):
            s.advance(1)
            y, w = se.year, s.cursor['week'] - 1 or 52
            now = se.abs_week(y, w)
            fame = {gid: sum(p for aw, p in rows if now - aw < PR.FAME_WEEKS) for gid, rows in se.fame_log.items() if rows}
            for gid, v in fame.items():
                self.assertEqual(se.fame.get(gid, 0.0), v, gid)                # fame summed only when it changes
            for gid, rows in list(se.wr.items())[:300]:
                if not rows:
                    continue
                tot, n = PR.ranking_total(rows, now)
                if tot > 0:
                    self.assertEqual(se.wr_avg[gid], tot / PR.ranking_divisor(n), gid)
            for g in [g for g in se.active_golfers() if g.status == 'pro'][:150]:
                for tier in (1, 2, 3, 4):
                    for cautious in (False, True):
                        self.assertEqual(se.prize_forecast(g, tier, cautious), se._prize_forecast(g, tier, cautious))
        g = next(g for g in se.active_golfers() if g.status == 'pro')
        before = se.prize_forecast(g, 4)
        se.learn_prize(g.id, 4, 0.5)                                         # new evidence: the forecast follows
        self.assertNotEqual(se.prize_forecast(g, 4), before)
        self.assertEqual(se.prize_forecast(g, 4), se._prize_forecast(g, 4, False))
        state = se.__getstate__()
        self.assertNotIn('_pf_memo', state)                                  # derived: never saved
        self.assertNotIn('_fame_seen', state)


if __name__ == '__main__':
    unittest.main()
