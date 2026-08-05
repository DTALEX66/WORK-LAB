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
            "20-design/open-design/x",
            "30-products/minigame/x",
            "README.md",
        ])
        self.assertEqual([len(result[k]) for k in ["workflow", "open-design", "minigame", "root"]], [1, 1, 1, 1])

    def test_aggregate_rejects_cancelled_job(self):
        payload = json.dumps({"jobs": {"workflow": "success", "open-design": "cancelled", "minigame": "success", "integration": "success"}})
        result = subprocess.run([sys.executable, str(ROOT / "scripts/ci/aggregate_gate.py")], input=payload, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)

if __name__ == "__main__":
    unittest.main()
