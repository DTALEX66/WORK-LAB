"""The sidecar's documented entry has to be runnable *as documented*, not only under pytest.

Recorded defect (2026-10-18): `python services/orchestration/sidecar.py --project-root . ...`
-- the command in `apps/observer/README.md` and the one `apps/observer/start-observer.cmd`
launches -- died with `ModuleNotFoundError: No module named 'canonical_store'` in a clean
shell. Every CI run stayed green because `tests/conftest.py` injects the module roots before
any test imports the sidecar, so the only path that was ever exercised was the test path.

This asserts the launcher path with a cleaned environment. `PYTHONPATH` is dropped on purpose:
leaving it in would let a developer's shell -- or this repo's own bootstrap -- repair the exact
condition the test exists to detect.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIDECAR = ROOT / "services" / "orchestration" / "sidecar.py"


class DocumentedLaunchTests(unittest.TestCase):
    def test_the_documented_command_answers_ready_without_pythonpath(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            environment = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
            process = subprocess.Popen(
                [
                    sys.executable, str(SIDECAR),
                    "--project-root", str(ROOT),
                    "--runtime-root", str(Path(tmp) / "runtime"),
                    "--host", "127.0.0.1",
                    "--port", "0",
                    "--no-worker",
                ],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                cwd=str(ROOT), env=environment,
            )
            try:
                assert process.stdout is not None
                output = ""
                for _ in range(40):  # the sidecar prints one ready line and then serves
                    line = process.stdout.readline()
                    if not line:
                        break
                    output += line
                    if "WORKFLOW_SIDECAR_READY" in line:
                        break
                    if "Traceback" in line or "Error" in line:
                        break
                self.assertIn("WORKFLOW_SIDECAR_READY", output, output)
                match = re.search(r"url=http://[^:]+:(\d+)", output)
                self.assertIsNotNone(match, output)
                port = int(match.group(1))
                self.assertGreater(port, 0)
                self.assertIn("worker=disabled", output)
                # "ready" must mean serving, not just a banner: the snapshot route has to answer.
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/v1/snapshot", timeout=10) as response:
                    self.assertEqual(200, response.status)
                    payload = response.read().decode("utf-8")
                self.assertIn("revision", payload)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                if process.stdout is not None:
                    process.stdout.close()

    def test_the_bootstrap_names_the_roots_it_adds(self) -> None:
        """A silent sys.path insert would be a new magic; the file has to say which roots."""
        source = SIDECAR.read_text(encoding="utf-8")
        self.assertIn("packages/client-neutral-core/scripts", source)
        self.assertIn("sys.path", source)
        # the reason has to be in the file, because the next reader will ask why
        self.assertIn("conftest", source)


if __name__ == "__main__":
    unittest.main()
