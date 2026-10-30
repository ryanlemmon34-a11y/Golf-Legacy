"""Name variety (2090 world audit: three in four names carried a middle initial by 2089, because every new
name had to differ from every name in history and the banks ran short).

Run from the project folder:  python -m unittest tests.test_names -v
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import names as N                                           # noqa: E402
from golfsim.population import generate_world                            # noqa: E402

INITIAL = re.compile(r' [A-Z]\. ')


class NameTests(unittest.TestCase):
    def test_the_starting_world_draws_from_the_original_banks(self):
        """A seed's starting world is unchanged by the larger banks (they serve later arrivals only)."""
        rng_a, rng_b = random.Random(5), random.Random(5)
        a = [N.make_name('USA', rng_a, set()) for _ in range(50)]
        given, family = N.B['en_us']
        self.assertTrue(all(n.split(' ')[0] in given and n.split(' ')[-1] in family for n in a))
        self.assertEqual(a, [N.make_name('USA', rng_b, set()) for _ in range(50)])
        w = generate_world(seed=3, scale=0.05)
        self.assertEqual(len({g.name for g in w.golfers}), len(w.golfers))   # still unique at the start

    def test_arrivals_prefer_new_names_then_retired_ones_never_initials(self):
        """With every combination of a small bank already used once, arrivals take a retired person's
        name (one no active person holds) rather than a middle initial; active people never share."""
        given, family = N.BX['kr']
        every = {f'{g} {f}' for g in given for f in family}
        active = set(sorted(every)[:len(every) // 2])
        taken, in_use = set(every), set(active)
        rng = random.Random(9)
        got = [N.make_name('South Korea', rng, taken, in_use) for _ in range(200)]
        self.assertFalse(any(INITIAL.search(n) for n in got))
        self.assertEqual(len(set(got)), len(got))                            # no two arrivals alike
        self.assertFalse(set(got) & active)                                  # nobody active shares a name

    def test_new_names_first(self):
        rng = random.Random(1)
        taken, in_use = set(), set()
        got = [N.make_name('Japan', rng, taken, in_use) for _ in range(500)]
        self.assertEqual(len(set(got)), 500)
        self.assertFalse(any(INITIAL.search(n) for n in got))

    def test_banks_only_grow(self):
        for bank, (given, family) in N.B.items():
            bg, bf = N.BX[bank]
            self.assertEqual(bg[:len(given)], given)
            self.assertEqual(bf[:len(family)], family)
            self.assertEqual(len(set(bg)), len(bg))
            self.assertEqual(len(set(bf)), len(bf))


if __name__ == '__main__':
    unittest.main()
