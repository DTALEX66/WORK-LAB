"""Contract tests for the three-way config coordinator (WL3-210)."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("config_coordinator", ROOT / "scripts/workflow/config_coordinator.py")
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)

OWNERSHIP = json.loads((ROOT / "config/config-ownership.json").read_text(encoding="utf-8"))


class ConfigCoordinatorTests(unittest.TestCase):
    def test_user_overlay_managed_field_is_patchable_when_unique(self) -> None:
        plan = MOD.three_way_compare(
            OWNERSHIP,
            previous_upstream={"display.language": "zh"},
            new_upstream={"display.language": "zh"},
            user_overlay={"display.language": "en"},
            identity_apply_allowed=True,
        )
        self.assertEqual(plan["status"], "DRY_RUN")
        self.assertTrue(plan["apply_allowed"])
        field = next(f for f in plan["fields"] if f["path"] == "display.language")
        self.assertEqual(field["change"], "USER_OVERLAY")
        self.assertEqual(field["action"], "KEEP")

    def test_secret_field_is_quarantined_even_with_unique_identity(self) -> None:
        plan = MOD.three_way_compare(
            OWNERSHIP,
            previous_upstream={},
            new_upstream={"credentials": {"api_key": "x"}},
            user_overlay={},
            identity_apply_allowed=True,
        )
        self.assertFalse(plan["apply_allowed"])
        self.assertIn("credentials", plan["quarantined_fields"])

    def test_unknown_field_defaults_to_quarantine(self) -> None:
        plan = MOD.three_way_compare(
            OWNERSHIP,
            previous_upstream={"mystery.key": 1},
            new_upstream={"mystery.key": 2},
            user_overlay={},
            identity_apply_allowed=True,
        )
        self.assertFalse(plan["apply_allowed"])
        self.assertIn("mystery.key", plan["quarantined_fields"])

    def test_upstream_change_with_user_overlay_is_rebase_candidate(self) -> None:
        plan = MOD.three_way_compare(
            OWNERSHIP,
            previous_upstream={"display.busy_input_mode": "queue"},
            new_upstream={"display.busy_input_mode": "drop"},
            user_overlay={"display.busy_input_mode": "queue"},
            identity_apply_allowed=True,
        )
        field = next(f for f in plan["fields"] if f["path"] == "display.busy_input_mode")
        self.assertEqual(field["change"], "UPSTREAM_CHANGED_WITH_OVERLAY")
        self.assertEqual(field["action"], "REBASE")

    def test_readback_and_rollback_are_hash_fenced(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "overlay.json"
            path.write_text(json.dumps({"display.language": "en"}), encoding="utf-8")
            digest = MOD.overlay_digest({"display.language": "en"})
            readback = MOD.readback_overlay(path, digest)
            self.assertEqual(readback["status"], "PASS")
            plan = MOD.three_way_compare(
                OWNERSHIP,
                previous_upstream={"display.language": "zh"},
                new_upstream={"display.language": "zh"},
                user_overlay={"display.language": "en"},
                identity_apply_allowed=True,
            )
            rollback = MOD.rollback_plan(plan, {"display.language": "zh"})
            self.assertEqual(rollback["status"], "READY")
            self.assertIn("display.language", rollback["restore_fields"])


if __name__ == "__main__":
    unittest.main()
