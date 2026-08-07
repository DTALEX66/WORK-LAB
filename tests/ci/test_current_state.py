from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.ci.generate_current_state import (
    build_state,
    check_stale_references,
    content_digest,
)


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ci" / "generate_current_state.py"


class CurrentStateTests(unittest.TestCase):
    def test_build_state_records_canonical_modules_skills_design_and_ci(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            evidence = Path(raw) / "ci.json"
            evidence.write_text(
                json.dumps(
                    {
                        "databaseId": 31139441168,
                        "workflowName": "work-lab-gate",
                        "status": "completed",
                        "conclusion": "success",
                        "headSha": "471e90a99b4234e4f5c031c4280c2eba8b065439",
                        "url": "https://github.com/DTALEX66/WORK-LAB/actions/runs/31139441168",
                        "attempt": 1,
                        "jobs": [
                            {"name": "aggregate", "status": "completed", "conclusion": "success"}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            state = build_state(ROOT, ci_evidence=evidence)

        self.assertEqual([item["id"] for item in state["modules"]], ["workflow-assistance", "work-lab-observer"])
        self.assertEqual(state["skills"]["count"], 13)

        self.assertEqual(state["ci"]["run_id"], 31139441168)
        self.assertEqual(
            next(job["conclusion"] for job in state["ci"]["jobs"] if job["name"] == "aggregate"),
            "success",
        )
        self.assertEqual(state["workflow_identity"]["workflow_name"], "work-lab-gate")
        self.assertEqual(state["workflow_identity"]["aggregate_job"], "aggregate")
        self.assertEqual(state["contracts"]["count"], 27)
        self.assertEqual(len(state["skills"]["items"]), 13)

    def test_content_digest_is_stable_when_generated_at_changes(self) -> None:
        first = build_state(ROOT)
        second = build_state(ROOT)
        first["generated_at"] = "2026-01-01T00:00:00Z"
        second["generated_at"] = "2029-01-01T00:00:00Z"
        self.assertEqual(content_digest(first), content_digest(second))

    def test_stale_reference_check_detects_old_workflow_and_fourth_module(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "README.md"
            path.write_text(
                "required workflow-governance; active module minigame",
                encoding="utf-8",
            )
            findings = check_stale_references([path])
        self.assertIn("workflow-governance", " ".join(findings))
        self.assertIn("fourth-active-module", " ".join(findings))

    def test_cli_generates_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output_dir = Path(raw)
            json_out = output_dir / "CURRENT_STATE.json"
            md_out = output_dir / "CURRENT_STATE.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(ROOT),
                    "--json-out",
                    str(json_out),
                    "--markdown-out",
                    str(md_out),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(json_out.is_file())
            self.assertTrue(md_out.is_file())
            self.assertIn("CURRENT_STATE_PASS", result.stdout)
            self.assertEqual(json.loads(json_out.read_text(encoding="utf-8"))["skills"]["count"], 13)


if __name__ == "__main__":
    unittest.main()
