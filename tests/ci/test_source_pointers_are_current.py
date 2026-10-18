"""Line pointers into fast-moving source must be re-derived mechanically, not re-measured by hand.

Measured over two days: four separate CI failures came from `path:LINE` citations pointing at a blank line or
at unrelated code after someone edited the file above them. Every repair was manual -- read the gate's message,
guess the new number, push, fail one line off -- which is why the same failure kept coming back under a new
number. This module pins the mechanical path instead:

* `scripts/ci/repoint_source_pointers.py` re-derives each pointer from the code it quotes (`--apply`), so a
  repair is one command rather than a guess;
* this gate runs it in check mode, so the next drift is a red line WITH the command that fixes it.

What it deliberately does NOT require: `UNRESOLVED` (a fragment quote whose target is genuinely ambiguous) and
`NARRATIVE` (a bare number in prose, which the pack's own matrix gate already tests for "not a blank line").
Failing on those would push editors to delete citations to make the gate green -- the opposite of the point.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "scripts" / "ci" / "repoint_source_pointers.py"
MATRIX = ROOT / "docs" / "current" / "ui-priority-20261009" / "UIV2-INTERFACE-BINDING-MATRIX.csv"


class PointerDriftTests(unittest.TestCase):
    def test_no_quoted_pointer_has_drifted(self) -> None:
        proc = subprocess.run([sys.executable, str(TOOL)], cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        out = proc.stdout + proc.stderr
        self.assertIn("REPOINT citations=", out, out)
        self.assertEqual(0, proc.returncode,
                         "a quoted pointer no longer lands on the code it quotes. Fix it mechanically, do not "
                         "re-measure by hand:\n"
                         f"  python scripts/ci/repoint_source_pointers.py --apply\n{out}")

    def test_the_tool_refuses_to_guess_an_unresolvable_quote(self) -> None:
        """A quote that is nowhere in the target must be reported, never silently re-pointed."""
        script = TOOL.read_text(encoding="utf-8")
        self.assertIn("UNRESOLVED", script)
        self.assertIn("nothing is guessed", script)

    def test_the_matrix_is_the_default_target(self) -> None:
        """The tool's default must be the file that actually drifts; a default nobody runs is decoration."""
        proc = subprocess.run([sys.executable, str(TOOL)], cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        self.assertIn("REPOINT citations=", proc.stdout + proc.stderr)
        self.assertTrue(MATRIX.is_file(), "the default target must exist")


if __name__ == "__main__":
    unittest.main(verbosity=2)
