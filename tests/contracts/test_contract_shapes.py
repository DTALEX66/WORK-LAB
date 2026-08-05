import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class ContractShapeTests(unittest.TestCase):
    def test_root_contracts_have_schema_versions(self):
        files = [
            ROOT / "00-governance/contracts/compatibility-manifest.json",
            ROOT / "00-governance/contracts/contract-catalog.json",
            ROOT / "00-governance/contracts/evidence-envelope.schema.json",
            ROOT / "00-governance/contracts/runtime-lock.schema.json",
            ROOT / "00-governance/migration-status.json",
            ROOT / "00-governance/module-ownership.json",
            ROOT / "00-governance/projects.json",
        ]
        for path in files:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(data.get("schemaVersion") or data.get("$id"), path.as_posix())

    def test_projects_preserve_three_module_paths(self):
        data = json.loads((ROOT / "00-governance/projects.json").read_text(encoding="utf-8"))
        self.assertEqual([m["path"] for m in data["modules"]], [
            "10-workflow/workflow-assistance",
            "20-design/open-design",
            "30-products/minigame",
        ])
        self.assertTrue(data["singleWriter"])
        self.assertFalse(data["externalMutationDefault"])

if __name__ == "__main__":
    unittest.main()
