"""Gate: a push is permitted only by a receipt that names the exact head and says GATE_EXIT=0.

The ordering rule (commit -> verify at HEAD -> push) has been broken three times, twice by me: once by
pushing a head whose own gate run had already printed GATE_EXIT=1 (ERR-181, reading the wrapper's exit
code instead of the file), once just now by pushing after a governance-only run. A receipt that does not
record which head it describes cannot answer the only question that matters, so `run_quality_gate.py`
stamps GATE_HEAD and this tool matches it.
"""
from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("push_permit", ROOT / "scripts" / "ci" / "push_permit.py")
permit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(permit)  # type: ignore[attr-defined]

HEAD = "a" * 40
OTHER = "b" * 40


def write(runs: Path, name: str, body: str) -> Path:
    path = runs / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8", newline="")
    return path


class DecideTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.runs = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_a_green_receipt_naming_this_head_permits_the_push(self) -> None:
        write(self.runs, "gate.log", f"QUALITY_GATE_PASS gates=verify\n"
                              f"GATE_HEAD={HEAD} GATE_TREE=x GATE_FULL=yes gates=51\n"
                              "GATE_SEMANTICS STRUCTURAL_LOCAL_PASS=yes\nGATE_EXIT=0\n")
        code, msg = permit.decide(HEAD, [self.runs / "gate.log"])
        self.assertEqual(code, 0, msg)
        self.assertIn("PUSH_PERMIT_OK", msg)

    def test_a_green_receipt_for_another_head_does_not_permit_this_one(self) -> None:
        # The decisive case: the previous head was verified, this one was not.
        write(self.runs, "gate.log", f"GATE_HEAD={OTHER} GATE_TREE=x GATE_FULL=yes\nGATE_EXIT=0\n")
        code, msg = permit.decide(HEAD, [self.runs / "gate.log"])
        self.assertEqual(code, 1)
        self.assertIn("NO_RECEIPT", msg)

    def test_a_receipt_that_recorded_red_refuses_and_quotes_the_exit(self) -> None:
        write(self.runs, "gate.log", f"GATE_HEAD={HEAD} GATE_TREE=x GATE_FULL=yes\n"
                                     "QUALITY_GATE_FAIL gate=security\nGATE_EXIT=1\n")
        code, msg = permit.decide(HEAD, [self.runs / "gate.log"])
        self.assertEqual(code, 1)
        self.assertIn("RECEIPT_RED", msg)
        self.assertIn("GATE_EXIT=1", msg)

    def test_a_narrow_run_on_the_right_head_is_its_own_verdict(self) -> None:
        # GATE_FULL=no means someone ran one cheap gate. Reading that as "verified" is the exact
        # mistake this tool exists to stop, so it must be named rather than folded into NO_RECEIPT.
        write(self.runs, "gate.log", f"GATE_HEAD={HEAD} GATE_TREE=x GATE_FULL=no gates=1\nGATE_EXIT=0\n")
        code, msg = permit.decide(HEAD, [self.runs / "gate.log"])
        self.assertEqual(code, 1)
        self.assertIn("PARTIAL_ONLY", msg)
        self.assertIn("gates_run=['no']", msg)
        ok, allowed = permit.decide(HEAD, [self.runs / "gate.log"], allow_partial=True)
        self.assertEqual(ok, 0, allowed)

    def test_a_receipt_from_before_the_stamp_exists_is_refused_not_assumed(self) -> None:
        write(self.runs, "old.log", f"GATE_HEAD={HEAD}\nGATE_EXIT=0\n")
        code, msg = permit.decide(HEAD, [self.runs / "old.log"])
        self.assertEqual(code, 1)
        self.assertIn("PARTIAL_ONLY", msg)

    def test_a_full_receipt_that_recorded_red_is_named_as_red(self) -> None:
        # Reachable only because the stamp is written before the first gate runs: a failed full verify
        # must be distinguishable from a head nobody ever tested.
        write(self.runs, "gate.log", f"GATE_HEAD={HEAD} GATE_TREE=x GATE_FULL=yes gates=50\n"
                                     "### gate: governance\nQUALITY_GATE_FAIL gate=governance exit_code=1\n"
                                     "GATE_EXIT=1\n")
        code, msg = permit.decide(HEAD, [self.runs / "gate.log"])
        self.assertEqual(code, 1)
        self.assertIn("RECEIPT_RED", msg)

    def test_a_receipt_with_no_exit_line_is_not_a_pass(self) -> None:
        # A killed or still-running batch leaves a file that mentions the head and says nothing else.
        write(self.runs, "gate.log", f"GATE_HEAD={HEAD} GATE_TREE=x GATE_FULL=yes\n### gate: governance\n")
        code, msg = permit.decide(HEAD, [self.runs / "gate.log"])
        self.assertEqual(code, 1)
        self.assertIn("NO_EXIT_LINE", msg)

    def test_the_last_exit_line_wins_when_a_file_holds_two_runs(self) -> None:
        write(self.runs, "gate.log",
              f"GATE_HEAD={HEAD} GATE_FULL=yes\nGATE_EXIT=0\nappended rerun\nGATE_EXIT=1\n")
        code, msg = permit.decide(HEAD, [self.runs / "gate.log"])
        self.assertEqual(code, 1, msg)
        self.assertIn("RECEIPT_RED", msg)

    def test_an_unreadable_receipt_is_refused_rather_than_crashing_the_verdict(self) -> None:
        path = write(self.runs, "gate.log", f"GATE_HEAD={HEAD} GATE_FULL=yes\nGATE_EXIT=0\n")
        original = permit.read
        with mock.patch.object(permit, "read", side_effect=lambda p: "" if p == path else original(p)):
            code, msg = permit.decide(HEAD, [path])
        self.assertEqual(code, 1)
        self.assertIn("NO_RECEIPT", msg)


class MainTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.runs = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def run_main(self, argv: list[str]) -> tuple[int, str]:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = permit.main(argv)
        return code, buffer.getvalue().strip()

    def test_an_unresolvable_rev_is_named_not_guessed(self) -> None:
        with mock.patch.object(permit, "resolve", return_value=None):
            code, msg = self.run_main(["--head", "not-a-commit", "--runs", str(self.runs)])
        self.assertEqual(code, 1)
        self.assertIn("NOT_A_COMMIT", msg)

    def test_a_missing_runs_directory_is_a_distinct_verdict(self) -> None:
        with mock.patch.object(permit, "resolve", return_value=HEAD):
            code, msg = self.run_main(["--head", "a" * 40,
                                       "--runs", str(self.runs / "absent")])
        self.assertEqual(code, 3)
        self.assertIn("PUSH_PERMIT_NOT_RUN", msg)

    def test_a_short_sha_is_resolved_before_it_is_matched(self) -> None:
        # The caller passes any rev form; the tool must expand it, because receipts carry 40 hex and a
        # seven-character prefix would otherwise match nothing and read as "never verified".
        with mock.patch.object(permit, "resolve", return_value=HEAD) as resolved:
            code, msg = self.run_main(["--head", "abcdef1", "--runs", str(self.runs)])
        self.assertEqual(resolved.call_args.args[0], "abcdef1")
        self.assertEqual(resolved.call_args.args[1], ROOT)
        self.assertEqual(code, 1)
        self.assertIn("NO_RECEIPT", msg)


class ReceiptIsStampedTests(unittest.TestCase):
    """The tool is only as good as the stamp; pin that the gate writes it."""

    def test_the_gate_stamps_the_head_its_verdict_belongs_to(self) -> None:
        source = (ROOT / "services" / "orchestration" / "run_quality_gate.py").read_text(encoding="utf-8")
        self.assertIn("GATE_HEAD={commit} GATE_TREE={tree} GATE_FULL={full} gates={len(names)}", source)

    def test_the_stamp_precedes_the_first_gate_so_a_red_run_is_attributable(self) -> None:
        # The whole point of RECEIPT_RED is unreachable if the stamp is only printed on the pass path:
        # "ran and failed" would then look exactly like "never ran", which is the confusion this tool
        # was written to remove.
        source = (ROOT / "services" / "orchestration" / "run_quality_gate.py").read_text(encoding="utf-8")
        body = source.split("def run_gate_sequence(", 1)[1].split("\ndef ", 1)[0]
        self.assertLess(body.index("GATE_HEAD="), body.index("### gate:"),
                        "the head stamp is emitted after the gates run")

    def test_the_head_helper_returns_a_full_sha_here(self) -> None:
        runner_spec = importlib.util.spec_from_file_location(
            "rQG", ROOT / "services" / "orchestration" / "run_quality_gate.py")
        runner = importlib.util.module_from_spec(runner_spec)
        runner_spec.loader.exec_module(runner)  # type: ignore[attr-defined]
        commit, tree = runner._git_head_identity()
        self.assertRegex(commit, r"^[0-9a-f]{40}$")
        self.assertRegex(tree, r"^[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main(verbosity=2)
