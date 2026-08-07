from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "workflow"
VERIFY = ROOT / "scripts" / "workflow" / "verify_core_schemas.py"
EXPECTED = {
    "client-adapter.schema.json",
    "adapter-registry.schema.json",
    "task-card.schema.json",
    "domain-pack.schema.json",
    "action-plan.schema.json",
    "run-event.schema.json",
    "evidence-envelope.schema.json",
    "error.schema.json",
    "task-ledger.schema.json",
    "observer-event.schema.json",
    "rule-asset.schema.json",
    "skill-package.schema.json",
    "growth-candidate.schema.json",
    "project-profile.schema.json",
    "gate-registry.schema.json",
    "gate-plan.schema.json",
    "blocker.schema.json",
    "ci-observation.schema.json",
    "evidence-manifest.schema.json",
    "model-policy.schema.json",
    "memory-record.schema.json",
    "rule-drift.schema.json",
}


class CoreSchemaTests(unittest.TestCase):
    def test_core_schema_set_has_neutral_metadata_and_required_contracts(self) -> None:
        self.assertEqual({p.name for p in SCHEMA_DIR.glob("*.schema.json")}, EXPECTED)
        for name in sorted(EXPECTED):
            data = json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
            self.assertEqual(data["type"], "object", name)
            self.assertIn("$id", data, name)
            self.assertIn("schema_version", data["required"], name)
            serialized = json.dumps(data, ensure_ascii=False)
            for forbidden in ("gpt-5.5", "gpt-5.6", "deepseek-chat", "kimi-k2"):
                self.assertNotIn(forbidden, serialized, name)

    def test_action_plan_is_approval_and_rollback_bounded(self) -> None:
        data = json.loads((SCHEMA_DIR / "action-plan.schema.json").read_text(encoding="utf-8"))
        self.assertIn("approval", data["required"])
        self.assertIn("rollback", data["required"])
        self.assertIn("approval_required", json.dumps(data))
        self.assertIn("WAITING_APPROVAL", json.dumps(data))

    def test_verifier_runs_without_client_runtime(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VERIFY), "--schema-dir", str(SCHEMA_DIR)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("CORE_SCHEMA_CONTRACT_PASS", result.stdout)
        self.assertIn("schemas=22", result.stdout)

    def test_verifier_rejects_schema_missing_required_contract(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            for path in SCHEMA_DIR.glob("*.schema.json"):
                (temp / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            broken = temp / "action-plan.schema.json"
            data = json.loads(broken.read_text(encoding="utf-8"))
            data["required"].remove("rollback")
            broken.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VERIFY), "--schema-dir", str(temp)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("rollback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
