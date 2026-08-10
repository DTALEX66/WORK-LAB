from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "config-ownership.json"

class ConfigOwnershipTests(unittest.TestCase):
    def test_manifest_is_platform_neutral_and_fail_closed(self) -> None:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], "workflow/config-ownership/v1")
        self.assertTrue(data["user_overlay"]["preserve_unknown"])
        self.assertEqual(data["official_baseline"]["mode"], "OBSERVE")
        self.assertIn("PLATFORM_INTERNAL", data["excluded_layers"])
        self.assertIn("SECRET", data["excluded_layers"])
        fields = {item["path"]: item for item in data["fields"]}
        self.assertEqual(fields["credentials"]["mode"], "FORBIDDEN")
        self.assertEqual(fields["desktop.internal_state"]["mode"], "IGNORE")
        self.assertEqual(fields["model.routing"]["mode"], "OBSERVE")

if __name__ == "__main__":
    unittest.main()
