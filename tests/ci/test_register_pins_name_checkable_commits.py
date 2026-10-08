"""A register pin must name a commit a reader can check out, and the checker must not be fooled.

Twelve distinct hashes were pinned by 23 rows and contained by zero refs: pre-squash branch heads, three
of which (656e7d2, 8114d8e, 09c6dd2) GitHub has never received at all -- `GET /commits/<sha>/pulls` answers
422. `git cat-file` still answered for them, so every earlier "does this pin resolve?" check passed. The
distinction the gate now draws is containment by a ref, not existence of an object.

The three states are not interchangeable: 34 pins sit on the open PR branch and are legitimate today, and
an earlier count of "40 not ancestors of origin/main" would have failed a healthy register.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "audit"))

import register_pin_reachability as pins  # noqa: E402

REGISTER = "taskpacks/current/OPEN-TASK-REGISTER.md"
# a commit that is on main, and one that exists locally but no ref contains it
ON_MAIN = "62f666ef36999b846ea1c9bcb075a0970be18933"
ZERO_REFS = "0600d6f680dd"


def _runtime_root() -> Path:
    p = REPO / ".project-local" / "runs"
    p.mkdir(parents=True, exist_ok=True)
    return p


class Classification(unittest.TestCase):
    def test_a_landing_commit_is_reported_on_main(self) -> None:
        state, full, refs = pins.classify(REPO, ON_MAIN[:7])
        self.assertEqual("ON_MAIN", state, f"{full} {refs[:3]}")
        self.assertEqual(40, len(full))

    def test_a_squashed_branch_head_is_caught_by_containment_not_existence(self) -> None:
        state, full, refs = pins.classify(REPO, ZERO_REFS)
        self.assertEqual("ZERO_REFS", state, f"{full} unexpectedly has refs {refs[:3]}")
        self.assertEqual([], refs)
        self.assertEqual(0, subprocess.run(["git", "cat-file", "-e", full + "^{commit}"],
                                           cwd=REPO, capture_output=True).returncode,
                         "the object exists; that is exactly why an existence test is not enough")

    def test_an_unresolvable_token_is_its_own_state(self) -> None:
        state, full, refs = pins.classify(REPO, "deadbee")
        self.assertEqual("UNRESOLVABLE", state)
        self.assertEqual("", full)


class RowExtraction(unittest.TestCase):
    def test_a_bare_hash_without_the_marker_is_not_a_pin(self) -> None:
        rows = pins.rows_with_pins("| A | DONE | see 656e7d2 for the head |\n")
        self.assertEqual([], rows, "@ is what makes a hash a pin; the note must be able to name heads")

    def test_a_pin_is_attributed_to_its_row(self) -> None:
        rows = pins.rows_with_pins(f"| U20 | P1 | CLOSED@{ON_MAIN[:7]} | evidence |\n")
        self.assertEqual(1, len(rows))
        self.assertEqual(("U20", [ON_MAIN[:7]]), (rows[0][1], rows[0][2]))


class TheRealRegister(unittest.TestCase):
    def run_tool(self, *extra: str) -> tuple[int, str]:
        proc = subprocess.run([sys.executable, str(REPO / "scripts" / "audit"
                                                    / "register_pin_reachability.py"), *extra],
                              cwd=REPO, capture_output=True)
        return proc.returncode, (proc.stdout + proc.stderr).decode("utf-8", "replace")

    def test_every_live_pin_is_contained_by_a_ref(self) -> None:
        code, out = self.run_tool("--check")
        self.assertEqual(0, code, out)
        head = out.splitlines()[0]
        self.assertIn("PIN_REACHABILITY_PASS", head)
        self.assertNotIn("ZERO_REFS=", head, f"a dangling pin is still being counted: {head}")
        self.assertNotIn("UNRESOLVABLE=", head, f"an unresolvable token is still being counted: {head}")

    def test_the_checker_reports_a_bounded_pin_count(self) -> None:
        _code, out = self.run_tool()
        head = out.splitlines()[0]
        self.assertIn("pins=", head)
        self.assertIn("distinct_tokens=", head)
        self.assertIn("rows_with_pins=", head)

    def test_a_planted_dead_pin_turns_the_check_red(self) -> None:
        workdir = Path(tempfile.mkdtemp(prefix="pin-reachability-", dir=str(_runtime_root())))
        try:
            planted = workdir / "register.md"
            planted.write_text(f"| ID | Priority | Status | Work |\n|---|---|---|---|\n"
                               f"| X | P1 | DONE@{ZERO_REFS} | planted dead pin |\n",
                               encoding="utf-8", newline="\n")
            code, out = self.run_tool("--register", str(planted), "--check")
            self.assertEqual(1, code, out)
            self.assertIn("ZERO_REFS 0600d6f", out)
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    def test_a_file_with_no_pins_fails_instead_of_passing(self) -> None:
        workdir = Path(tempfile.mkdtemp(prefix="pin-empty-", dir=str(_runtime_root())))
        try:
            empty = workdir / "register.md"
            empty.write_text("| ID | Priority | Status | Work |\n|---|---|---|---|\n"
                             "| X | P1 | DONE | no pins here |\n", encoding="utf-8", newline="\n")
            code, out = self.run_tool("--register", str(empty), "--check")
            self.assertEqual(1, code, out)
            self.assertIn("rows_with_pins=0", out)
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    def test_the_register_itself_still_carries_many_pins(self) -> None:
        """A guard that could pass on an emptied file guards nothing."""
        text = (REPO / REGISTER).read_text(encoding="utf-8")
        rows = pins.rows_with_pins(text)
        self.assertGreater(len(rows), 40, f"only {len(rows)} rows carry pins; the extractor changed")


if __name__ == "__main__":
    unittest.main()
