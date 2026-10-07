"""Gate the verification stamper: it writes traceability fields, so its refusals are the product.

A `verifiedCommit` is the strongest claim in the ledger — that CI looked at this exact head and the
record was inside it. The tool must therefore fail closed on every ambiguity, and the tests below
each hand it an ambiguous case and require a refusal. The ancestry check has its own test because the
first version compared a captured stdout against zero and refused everything: an ancestry test prints
nothing, so only the return code answers the question.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "audit" / "stamp_record_verification.py"
LEDGER = ROOT / "taskpacks/current/error-ledger.json"

spec = importlib.util.spec_from_file_location("stamp_record_verification", SCRIPT)
stamper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stamper)  # type: ignore[attr-defined]


def row(error_id: str, fixed: str, verified: str | None = None) -> dict:
    return {"error_id": error_id, "lifecycle": {"fixedCommit": fixed, "verifiedCommit": verified}}


class HeadResolutionTests(unittest.TestCase):
    def test_an_unresolvable_short_name_is_not_a_commit(self) -> None:
        self.assertEqual("", stamper.head_of("deadbee"))
        self.assertEqual(40, len(stamper.head_of("HEAD")))


class AncestryTests(unittest.TestCase):
    def test_the_real_check_accepts_a_known_descendant_pair(self) -> None:
        # Measured on this repository rather than asserted in the abstract: the stamp that this
        # tool's first version wrongly refused, because it compared captured stdout to zero and an
        # ancestry test prints nothing.
        doc = json.loads(LEDGER.read_text(encoding="utf-8"))
        row148 = next(e for e in doc["errors"] if e["error_id"] == "ERR-148")
        sha = stamper.head_of("07082ed")
        rc = subprocess.run(["git", "merge-base", "--is-ancestor",
                             row148["lifecycle"]["fixedCommit"], sha],
                            cwd=ROOT, capture_output=True).returncode
        self.assertEqual(0, rc, "the stamper must not refuse a genuine descendant")

    def test_the_cli_refuses_a_head_that_cannot_be_resolved(self) -> None:
        proc = subprocess.run([sys.executable, str(SCRIPT), "ERR-149", "deadbee"],
                              cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                              errors="replace")
        self.assertEqual(1, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("REFUSED ERR-149", proc.stdout)
        self.assertIn("does not resolve", proc.stdout)

    def test_an_already_verified_record_is_never_overwritten(self) -> None:
        proc = subprocess.run([sys.executable, str(SCRIPT), "ERR-143", "285704a"],
                              cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                              errors="replace")
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("already stamped", proc.stdout)
        after = json.loads(LEDGER.read_text(encoding="utf-8"))
        row = next(e for e in after["errors"] if e["error_id"] == "ERR-143")
        self.assertEqual("285704a", row["lifecycle"]["verifiedCommit"][:7],
                         "an existing verifiedCommit must survive untouched")


class CiVerdictTests(unittest.TestCase):
    def test_no_run_for_the_head_is_reported_as_unknown_not_green(self) -> None:
        payload = json.dumps([])
        with mock.patch.object(stamper.subprocess, "run",
                               return_value=subprocess.CompletedProcess([], 0, payload, "")):
            verdict = stamper.ci_verdict("f" * 40)
        self.assertFalse(verdict["known"])
        self.assertIn("NO_RUN_FOR_THIS_HEAD", verdict["reason"])

    def test_a_still_running_workflow_is_unknown_rather_than_a_pass(self) -> None:
        rows = [{"databaseId": 1, "headSha": "a" * 40, "workflowName": "work-lab-gate",
                 "status": "in_progress", "conclusion": None}]
        with mock.patch.object(stamper.subprocess, "run",
                               return_value=subprocess.CompletedProcess([], 0, json.dumps(rows), "")):
            verdict = stamper.ci_verdict("a" * 40)
        self.assertFalse(verdict["known"])
        self.assertIn("still in_progress", verdict["reason"])

    def test_a_failing_workflow_is_reported_and_never_upgraded(self) -> None:
        rows = [{"headSha": "b" * 40, "workflowName": "work-lab-gate", "status": "completed",
                 "conclusion": "failure"},
                {"headSha": "b" * 40, "workflowName": "wlr-060-production-gates",
                 "status": "completed", "conclusion": "success"}]
        with mock.patch.object(stamper.subprocess, "run",
                               return_value=subprocess.CompletedProcess([], 0, json.dumps(rows), "")):
            verdict = stamper.ci_verdict("b" * 40)
        self.assertTrue(verdict["known"])
        self.assertEqual("failure", verdict["verdict"])

    def test_a_gh_query_failure_is_unknown(self) -> None:
        with mock.patch.object(stamper.subprocess, "run",
                               return_value=subprocess.CompletedProcess([], 1, "", "boom")):
            verdict = stamper.ci_verdict("c" * 40)
        self.assertFalse(verdict["known"])
        self.assertIn("GH_QUERY_FAILED", verdict["reason"])


class RecordPresenceTests(unittest.TestCase):
    def test_a_head_that_cannot_show_the_record_cannot_verify_it(self) -> None:
        # 5143726 is ERR-149's own fix commit, so ancestry passes trivially — but the record is
        # written in the commit after it. A stamp there would claim a readback of a record the
        # tested tree does not contain.
        proc = subprocess.run([sys.executable, str(SCRIPT), "ERR-149", "5143726"],
                              cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                              errors="replace")
        self.assertEqual(1, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("REFUSED ERR-149", proc.stdout)
        self.assertIn("does not contain the record", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
