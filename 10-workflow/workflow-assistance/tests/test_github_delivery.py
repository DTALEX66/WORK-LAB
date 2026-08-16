"""Contract tests for GitHub Delivery Accelerator (upload + review).

Covers: conventional message prefixing, safety no-message behavior, review
recommendation logic (mergeable/checks/local gate), and repo manifest.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/workflow"))

from github_upload_accelerator import _prefix, _sanitize, upload
from github_review_accelerator import review
from github_common import MANAGED_REPOS


class UploadAcceleratorTests(unittest.TestCase):
    def test_prefix_existing_conventional_kept(self) -> None:
        self.assertEqual(_prefix("fix: typo"), "fix: typo")

    def test_prefix_infers_fix(self) -> None:
        self.assertEqual(_prefix("fix the crash"), "fix: fix the crash")

    def test_prefix_infers_docs(self) -> None:
        self.assertEqual(_prefix("update readme"), "docs: update readme")

    def test_prefix_infers_feat(self) -> None:
        self.assertEqual(_prefix("add new module"), "feat: add new module")

    def test_prefix_falls_back_chore(self) -> None:
        self.assertEqual(_prefix("random message"), "chore: random message")

    def test_sanitize_strips_newlines(self) -> None:
        self.assertEqual(_sanitize("a\nb"), "a b")

    @mock.patch("github_upload_accelerator.git")
    @mock.patch("github_upload_accelerator.git_ok")
    @mock.patch("github_upload_accelerator.local_path")
    def test_no_message_no_action(self, lp, gok, git) -> None:
        lp.return_value = Path("dummy")
        gok.return_value = (True, " M file.txt")
        result = upload("X", None, push=True)
        self.assertEqual(result["status"], "DIRTY_NO_ACTION")
        git.assert_not_called()

    @mock.patch("github_upload_accelerator.git")
    @mock.patch("github_upload_accelerator.git_ok")
    @mock.patch("github_upload_accelerator.local_path")
    def test_with_message_commits_and_pushes(self, lp, gok, git) -> None:
        lp.return_value = Path("dummy")
        gok.side_effect = [
            (True, " M file.txt"),      # status
            (True, "main"),             # branch
            (False, ""),                # upstream (none)
        ]
        result = upload("X", "fix bug", push=True)
        self.assertEqual(result["status"], "DONE")
        self.assertEqual(result["commit"], "fix: fix bug")
        calls = [c[0][1:] for c in git.call_args_list]
        self.assertIn(("add", "-A"), calls)
        self.assertIn(("push", "-u", "origin", "main"), calls)


class ReviewAcceleratorTests(unittest.TestCase):
    @mock.patch("github_review_accelerator._run_local_gate")
    @mock.patch("github_review_accelerator.request")
    def test_approve_when_clean_and_checks_pass(self, req, gate) -> None:
        req.side_effect = [
            {"title": "t", "head": {"sha": "abc123"}, "mergeable": True, "mergeable_state": "clean"},
            {"check_runs": [{"name": "ci", "conclusion": "success"}]},
        ]
        gate.return_value = {"applicable": True, "passed": True}
        r = review("DTALEX66/WORK-LAB", 1)
        self.assertEqual(r["recommendation"], "APPROVE")
        self.assertEqual(r["reasons"], [])

    @mock.patch("github_review_accelerator._run_local_gate")
    @mock.patch("github_review_accelerator.request")
    def test_block_when_check_fails(self, req, gate) -> None:
        req.side_effect = [
            {"title": "t", "head": {"sha": "abc123"}, "mergeable": True, "mergeable_state": "clean"},
            {"check_runs": [{"name": "ci", "conclusion": "failure"}]},
        ]
        gate.return_value = {"applicable": True, "passed": True}
        r = review("DTALEX66/WORK-LAB", 1)
        self.assertEqual(r["recommendation"], "BLOCK")
        self.assertIn("check-runs not all success", r["reasons"])

    @mock.patch("github_review_accelerator._run_local_gate")
    @mock.patch("github_review_accelerator.request")
    def test_block_when_local_gate_fails(self, req, gate) -> None:
        req.side_effect = [
            {"title": "t", "head": {"sha": "abc123"}, "mergeable": True, "mergeable_state": "clean"},
            {"check_runs": [{"name": "ci", "conclusion": "success"}]},
        ]
        gate.return_value = {"applicable": True, "passed": False}
        r = review("DTALEX66/WORK-LAB", 1)
        self.assertEqual(r["recommendation"], "BLOCK")
        self.assertIn("local quality gate FAILED", r["reasons"])

    def test_managed_repos_manifest(self) -> None:
        self.assertGreaterEqual(len(MANAGED_REPOS), 4)
        names = [e["local"] for e in MANAGED_REPOS]
        self.assertIn("WORK-LAB", names)
        self.assertIn("DESIGN-LAB", names)


if __name__ == "__main__":
    unittest.main()
