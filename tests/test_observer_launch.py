"""The observer started the way the Windows launcher starts it: `tools/observer.py` run as a script (RUN_OBSERVER_WINDOWS.bat),
and re-run as '__mp_main__' by a spawned worker. Each in a fresh interpreter, so nothing imported by other tests helps."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'tools' / 'observer.py'


def run(args, **kw):
    return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True, timeout=180, **kw)


class LaunchAsScript(unittest.TestCase):
    def test_help_as_a_script(self):
        r = run([str(SCRIPT), '--help'])
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        self.assertIn('usage: observer.py', r.stdout)
        self.assertNotIn('Traceback', r.stderr)

    def test_spawned_worker_import_resolves_the_career_routes(self):
        """A spawned worker re-runs the main script as '__mp_main__': it must load completely, as the `observer` the
        page modules import, with the career routes in its page table."""
        code = (
            'import runpy, sys\n'
            f'g = runpy.run_path({str(SCRIPT)!r}, run_name="__mp_main__")\n'
            'import observer, observer_career\n'
            'assert observer.PAGES["/career"] is observer_career.career_page\n'
            'assert observer.PAGES["/career"] is g["PAGES"]["/career"]\n'
            'assert observer_career.esc is g["esc"] and observer_career.table is g["table"]\n'
            'print("ok")\n')
        r = run(['-c', code])
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        self.assertEqual(r.stdout.strip(), 'ok')

    def test_the_world_library_serves_over_http(self):
        """`python tools/observer.py --worlds <new folder> --port 0`: the server starts, the World library page and a
        career route answer over real HTTP, and Quit is not needed (the process is stopped by the test)."""
        lib = Path(tempfile.mkdtemp(prefix='obs_launch_')) / 'worlds'
        p = subprocess.Popen([sys.executable, str(SCRIPT), '--worlds', str(lib), '--port', '0', '--workers', '1'],
                             cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                             env=dict(os.environ, PYTHONUNBUFFERED='1'))
        try:
            url, deadline = None, time.time() + 120
            while url is None and time.time() < deadline:
                line = p.stdout.readline()
                if not line:
                    if p.poll() is not None:
                        break
                    continue
                m = re.search(r'(http://localhost:\d+/)', line)
                if m:
                    url = m.group(1)
            self.assertIsNotNone(url, 'no server address printed; stderr: ' + (p.stderr.read() if p.poll() is not None
                                                                              else '')[-2000:])
            with urllib.request.urlopen(url, timeout=60) as r:
                self.assertEqual(r.status, 200)
                body = r.read().decode('utf-8')
            self.assertIn('World library', body)
            with urllib.request.urlopen(url + 'career', timeout=60) as r:         # a career route, without a world
                self.assertIn(r.status, (200,))
        finally:
            p.terminate()
            try:
                p.wait(timeout=30)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait(timeout=30)
            p.stdout.close()
            p.stderr.close()


if __name__ == '__main__':
    unittest.main()
