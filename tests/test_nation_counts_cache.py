"""The Nations list's counts, worked out once per history and snapshot (tools/observer.py nation_counts,
major_champions): the same values as counting every time, counted again whenever the published history, the snapshot
or the records' statistics change, and never keeping an old history alive.

Run from the project folder:  python -m unittest tests.test_nation_counts_cache -v
"""
from __future__ import annotations

import gc
import random
import sys
import unittest
import weakref
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.history_stats import Starts                              # noqa: E402
import observer as O                                                  # noqa: E402


def unpacked(stats):
    """The definition: a golfer with any start in a major edition finished in first place."""
    return {pid for pid, ss in stats.starts.items() if any(s[5] == 'major' and s[6] == 1 for s in ss)}


def make_stats(seed, seasons=6, people=400):
    rnd = random.Random(seed)
    st = Starts()
    sig = {}
    for y in range(2030, 2030 + seasons):
        eds = [(y, wk, f'{y}:E{wk}', 'PT', 1, rnd.choice(['major', 'premier', 'regular', 'major', 'college']))
               for wk in range(1, 30)]
        ranks = st.add_editions(eds)
        touched = set()
        for e in eds:
            field = rnd.sample(range(people), 60)
            for i, pid in enumerate(field):
                pos = None if i > 50 else (1 if i < rnd.choice([1, 1, 2]) else 1 + i)   # ties for first, missed cuts
                st.add(pid, ranks[e[2]], pos)
                touched.add(pid)
        st.settle(touched)
        sig[y] = f'years/{y}.g{y - 2029:06d}.json.gz'
    return NS(starts=st, sig=sig, complete=True)


class Snapshot:
    def __init__(self, generation, wr):
        self.generation, self.wr, self.people = generation, wr, {}


class Hist:
    def __init__(self, people):
        self.people = people


class World:
    """What nation_counts reads: the history, the snapshot, the statistics, people."""

    def __init__(self, people, stats, live=None):
        self.a = Hist(people)
        self.live = live
        self._stats = stats
        self.person_calls = 0

    @property
    def stats(self):
        return self._stats

    def all_people(self):
        return set(self.a.people) | (set(self.live.people) if self.live else set())

    def person(self, pid):
        self.person_calls += 1
        p = self.a.people.get(pid)
        return dict(p) if p else None


def people(n=400, seed=3):
    rnd = random.Random(seed)
    out = {}
    for pid in range(n):
        roles = ['golfer'] if pid % 7 else ['coach']
        out[pid] = {'name': f'P{pid}', 'country': rnd.choice(['USA', 'Fiji', 'Argentina', 'Norway']), 'roles': roles,
                    **({'golfer': {'lifestyle': rnd.choice(['full-time', 'retired', 'part-time']), 'tour': 'PT'}}
                       if 'golfer' in roles else {})}
    return out


class MajorChampions(unittest.TestCase):
    def test_packed_test_equals_the_definition(self):
        for seed in range(12):
            st = make_stats(seed)
            w = World(people(), st)
            self.assertEqual(O.major_champions(w), unpacked(st), seed)
            self.assertTrue(O.major_champions(w))

    def test_statistics_without_packed_starts_use_the_definition(self):
        st = make_stats(1)
        plain = NS(starts={pid: st.starts[pid] for pid in st.starts}, sig=dict(st.sig), complete=True)
        self.assertEqual(O.major_champions(World(people(), plain)), unpacked(st))

    def test_counted_again_when_the_statistics_change(self):
        st = make_stats(2)
        w = World(people(), st)
        first = O.major_champions(w)
        self.assertIs(O.major_champions(w), first)                           # kept
        st.sig[2030] = 'years/2030.g000099.json.gz'                          # a season published again ...
        st.starts.clear()                                                    # ... and read again: other results
        eds = [(2030, 1, '2030:E1', 'PT', 1, 'major')]
        ranks = st.starts.add_editions(eds)
        st.starts.add(7, ranks['2030:E1'], 1)
        self.assertEqual(O.major_champions(w), {7})
        w._stats = None
        self.assertEqual(O.major_champions(w), set())                       # no history


class NationCounts(unittest.TestCase):
    def setUp(self):
        self.st = make_stats(4)
        self.w = World(people(), self.st, Snapshot(10, {1: 1, 2: 50, 3: 101}))

    def fresh(self):
        return O._nation_counts(self.w)

    def test_same_values_and_counted_once(self):
        got = O.nation_counts(self.w)
        self.assertEqual(got, self.fresh())
        self.assertGreater(sum(r[3] for r in got.values()), 0)              # some major champions counted
        n = self.w.person_calls
        self.assertIs(O.nation_counts(self.w), got)
        self.assertEqual(self.w.person_calls, n)                            # nobody looked at again

    def test_counted_again_for_a_new_snapshot(self):
        O.nation_counts(self.w)
        self.w.live = Snapshot(11, {5: 1})                                  # the next generation
        self.assertEqual(O.nation_counts(self.w), self.fresh())
        n = self.w.person_calls
        O.nation_counts(self.w)
        self.assertEqual(self.w.person_calls, n)

    def test_counted_again_for_a_new_history(self):
        before = O.nation_counts(self.w)
        p = people()
        p[0]['country'] = 'Peru'
        self.w.a = Hist(p)                                                  # republished
        got = O.nation_counts(self.w)
        self.assertIn('Peru', got)
        self.assertNotEqual(got, before)
        self.assertEqual(got, self.fresh())

    def test_counted_again_when_the_statistics_change(self):
        O.nation_counts(self.w)
        self.st.sig[2031] = 'years/2031.g000123.json.gz'
        n = self.w.person_calls
        O.nation_counts(self.w)
        self.assertGreater(self.w.person_calls, n)

    def test_an_old_history_is_not_kept_alive(self):
        O.nation_counts(self.w)
        old = weakref.ref(self.w.a)
        self.w.a = Hist(people())
        gc.collect()
        self.assertIsNone(old())

    def test_objects_without_weak_references_are_counted_every_time(self):
        w = NS(a=NS(people=people()), live=None, stats=self.st, all_people=lambda: set(range(400)),
               person=lambda pid: dict(people()[pid]))
        self.assertEqual(O.nation_counts(w), O._nation_counts(w))
        self.assertNotIn('_nation_counts', vars(w))


if __name__ == '__main__':
    unittest.main()
