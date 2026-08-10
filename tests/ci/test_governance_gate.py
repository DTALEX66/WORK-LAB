import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class GovernanceGateTests(unittest.TestCase):
    def test_classifier_assigns_each_owner(self):
        spec = importlib.util.spec_from_file_location("classifier", ROOT / "scripts/ci/classify_paths.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.classify([
            "10-workflow/workflow-assistance/x",
            "30-observer/work-lab-observer/x",
            "README.md",
        ])
        self.assertEqual([len(result[k]) for k in ["workflow", "observer", "root"]], [1, 1, 1])

    def test_aggregate_rejects_cancelled_job(self):
        payload = json.dumps({"jobs": {"workflow": "success", "observer": "cancelled", "integration": "success"}})
        result = subprocess.run([sys.executable, str(ROOT / "scripts/ci/aggregate_gate.py")], input=payload, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)

    def test_root_workflow_uses_real_needs_results(self):
        workflow = (ROOT / ".github/workflows/work-lab-gate.yml").read_text(encoding="utf-8")
        normalized = "".join(workflow.split())
        for job in ("workflow", "observer", "integration"):
            self.assertIn(f"needs.{job}.result", normalized)
        self.assertNotIn('"workflow":"success"', normalized)
        self.assertIn("needs:", workflow)

    def test_required_workflow_checks_current_state_freshness_and_stage3_baseline(self):
        workflow = (ROOT / ".github/workflows/work-lab-gate.yml").read_text(encoding="utf-8")
        self.assertIn("python scripts/ci/generate_current_state.py --check-current", workflow)
        self.assertIn("python tests/ci/test_stage3_baseline.py", workflow)


    def test_contract_catalog_references_real_schemas(self):
        script = ROOT / "scripts/ci/verify_contract_catalog.py"
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("CONTRACT_CATALOG_PASS contracts=30 schemas=30", result.stdout)

if __name__ == "__main__":
    unittest.main()
