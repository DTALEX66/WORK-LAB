"""Gate: the canonical gate runner must never decode a child with the host locale.

Measured 2026-10-08: the governance batch died with `TypeError: can only concatenate str (not "NoneType")`,
which destroyed the whole gate receipt on the machine that produces the most receipts. The cause is two
ends disagreeing. `subprocess.run(..., text=True)` with no `encoding=` decodes with the locale, and on this
host that is cp936, while mandatory test modules print Chinese failure text through a `PYTHONIOENCODING`
that the batch had pinned to UTF-8. On the invalid byte, subprocess's own `_readerthread` raises
`UnicodeDecodeError` inside a thread, the exception is printed to the parent's stderr and *swallowed by the
threading module*, and `communicate()` hands back `None` for that stream. So the crash was not the decode
error anyone could read in the log -- it was the `None` that came out of it five frames away.

CI on Ubuntu could never show this: its locale already matches the child. That is why the guard here is
structural rather than behavioural -- it fails on any host.

The sibling gate `test_workflow_locale_discipline_gate.py` polices the *recorded CI commands* for the same
class; this one polices the pipes the harness itself opens. Different subject, same fault.

Discovered dynamically by `run_quality_gate.py governance`.
"""
from __future__ import annotations

import ast
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Every file on the path that turns a batch run into a gate receipt. The set is closed and named: a new
# member has to be added deliberately, and an entry whose file is gone fails the shape check below.
ENFORCED = (
    ROOT / "services" / "orchestration" / "run_quality_gate.py",
    ROOT / "tests" / "workflow-assistance" / "test_wloss_gates.py",
    ROOT / "tests" / "workflow-assistance" / "test_workflow_governance.py",
)
RUNNER = ENFORCED[0]
PIPE_FUNCTIONS = {"run", "Popen", "check_output", "check_call", "call"}

# Capability floor, measured 2026-10-08: the runner opens 8 text-mode pipes. The number only has to stay
# above the level at which a matcher that finds nothing would still report "0 violations", so it is a floor
# on the scanner's sight, not a photograph of the backlog.
TEXT_PIPE_FLOOR = 6


def text_mode_pipes(source: str) -> tuple[list[int], list[int]]:
    """(undeclared-encoding line numbers, all text-mode pipe line numbers) for one source."""
    tree = ast.parse(source)
    undeclared: list[int] = []
    every: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if getattr(node.func, "attr", None) not in PIPE_FUNCTIONS:
            continue
        keywords = {kw.arg for kw in node.keywords}
        if "text" not in keywords and "universal_newlines" not in keywords:
            continue
        every.append(node.lineno)
        if "encoding" not in keywords:
            undeclared.append(node.lineno)
    return sorted(undeclared), sorted(every)


class GateRunnerEncodingTests(unittest.TestCase):
    def test_the_enforced_set_is_the_files_that_are_really_there(self) -> None:
        missing = [path.relative_to(ROOT).as_posix() for path in ENFORCED if not path.is_file()]
        self.assertEqual(missing, [], f"the enforced set names files that no longer exist: {missing}")

    def test_every_text_pipe_in_the_enforced_files_declares_an_encoding(self) -> None:
        for path in ENFORCED:
            with self.subTest(target=path.relative_to(ROOT).as_posix()):
                undeclared, every = text_mode_pipes(path.read_text(encoding="utf-8"))
                self.assertGreaterEqual(
                    len(every), TEXT_PIPE_FLOOR if path is RUNNER else 1,
                    f"{path.name}: the scanner saw {len(every)} text-mode pipes; at zero the "
                    "no-violation verdict below is not evidence, only a blind matcher",
                )
                self.assertEqual(
                    undeclared, [],
                    f"subprocess text pipes without an explicit encoding at lines {undeclared}: a child "
                    "that prints anything outside the host codepage kills the reader thread and returns "
                    "None, which destroys the gate receipt (ERR-211)",
                )

    def test_the_matcher_fires_on_the_bad_shape_and_not_on_the_good_one(self) -> None:
        bad, good = text_mode_pipes(
            "import subprocess\n"
            "subprocess.run(['python', 'x.py'], text=True, capture_output=True)\n"
            "subprocess.run(['python', 'y.py'], text=True, encoding='utf-8', errors='replace')\n"
        )
        self.assertEqual(bad, [2], "an undeclared text pipe was not detected -- the rule cannot hold")
        self.assertEqual(good, [2, 3], "the scan lost a pipe that already declares its encoding")

    def test_the_batch_child_env_pins_the_output_encoding(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        start = source.index("def _run_governance_batch")
        body = source[start:source.index("\ndef ", start + 1)]
        self.assertIn('env["PYTHONIOENCODING"]', body,
                      "the batch child writes with whatever locale it inherited while the parent reads "
                      "UTF-8; both ends have to be pinned or the two disagree on a Chinese failure line")


class RepoWideNoticeTests(unittest.TestCase):
    def test_the_rest_of_the_repository_is_reported_not_failed(self) -> None:
        # Not every tool prints non-ASCII, so this is a visible number that may only shrink: the runner is
        # the one file whose crash destroys a gate receipt, and that one is enforced above.
        files = subprocess.run(["git", "-c", "core.quotePath=false", "ls-files", "*.py"],
                               cwd=ROOT, capture_output=True, text=True,
                               encoding="utf-8", errors="replace").stdout.split()
        sites = 0
        holders = 0
        for rel in files:
            path = ROOT / rel
            if not path.is_file():
                continue
            try:
                undeclared, _ = text_mode_pipes(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError, OSError):
                continue
            if undeclared:
                holders += 1
                sites += len(undeclared)
        self.assertGreater(sites, 0, "the scan found no undeclared pipes anywhere, which means it is not "
                                     "looking; widen it instead of trusting this notice")
        print(f"NOTICE_ENCODING_DEBT files={holders} sites={sites} scope=tracked_python "
              f"enforced_files={len(ENFORCED)}")


if __name__ == "__main__":
    unittest.main()
