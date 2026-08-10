"""Contract tests for the config-ownership registry (WL3-200)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config/config-ownership.json"
EXPECTED_LAYERS = {
    "UPSTREAM_OFFICIAL", "USER_OVERLAY", "PROJECT_OVERLAY", "TASK_EPHEMERAL",
    "PLATFORM_INTERNAL", "RUNTIME_EPHEMERAL", "SECRET", "COSMETIC",
}


class ConfigOwnershipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_single_authority_v2(self) -> None:
        self.assertEqual(self.registry["schema_version"], "workflow/config-ownership/v2")
        self.assertTrue(self.registry["single_authority"])

    def test_all_layers_and_modes_present(self) -> None:
        self.assertEqual(set(self.registry["layers"]), EXPECTED_LAYERS)
        self.assertEqual(set(self.registry["operation_modes"]), {"MANAGE", "OBSERVE", "IGNORE", "FORBIDDEN"})

    def test_unknown_fields_default_to_quarantine(self) -> None:
        default = self.registry["default_unknown"]
        self.assertEqual(default["mode"], "OBSERVE")
        self.assertTrue(default["quarantine"])

    def test_secret_fields_are_forbidden(self) -> None:
        secret_fields = [f for f in self.registry["fields"] if f["layer"] == "SECRET"]
        self.assertTrue(secret_fields)
        for field in secret_fields:
            self.assertEqual(field["mode"], "FORBIDDEN")

    def test_field_paths_are_unique_and_cover_all_layers(self) -> None:
        paths = [field["path"] for field in self.registry["fields"]]
        self.assertEqual(len(paths), len(set(paths)))
        used_layers = {field["layer"] for field in self.registry["fields"]}
        self.assertIn("USER_OVERLAY", used_layers)
        self.assertIn("SECRET", used_layers)
        self.assertIn("PLATFORM_INTERNAL", used_layers)


if __name__ == "__main__":
    unittest.main()
