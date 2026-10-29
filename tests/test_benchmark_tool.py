"""The benchmark undoes everything it changes even when a skip fails: instrumentation removed, memory
sampling stopped, the observer (session, workers, history snapshot) closable afterwards.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from golfsim import session as SES                                    # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import benchmark_skip as B                                            # noqa: E402
import observer                                                       # noqa: E402


class BenchmarkCleanupTests(unittest.TestCase):
    def test_a_failed_skip_leaves_nothing_patched_or_running(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        Session.create(tmp / 'w', seed=3, workers=1, world=generate_world(seed=3, scale=0.02)).close()
        w = observer.World(tmp / 'w')
        commit, publish, settle, reload_ = Session._commit, SES._publish_archive, SES.settle_heap, w.reload
        threads = set(threading.enumerate())
        a = SimpleNamespace(seasons=1, profile=None)
        with mock.patch.object(observer.World, 'submit', side_effect=RuntimeError('the skip failed')), \
                self.assertRaises(RuntimeError):
            B._skips(a, w, observer, Session, SES, None)
        self.assertIs(Session._commit, commit)
        self.assertIs(SES._publish_archive, publish)
        self.assertIs(SES.settle_heap, settle)
        self.assertEqual(w.reload, reload_)
        self.assertFalse([t for t in threading.enumerate() if t not in threads and t.is_alive()])  # sampler stopped
        w.close()
        self.assertIsNone(w.a)


if __name__ == '__main__':
    unittest.main()
