from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/workflow/growth_candidates.py"


def load_module():
    spec = importlib.util.spec_from_file_location("growth_candidates", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def candidate(module, status: str = "discovered") -> dict:
    value = {
        "schema_version": "workflow/growth-candidate/v1",
        "candidateId": "candidate-1",
        "origin": "local-fixture",
        "classification": "learn",
        "status": status,
        "risk": "low",
    }
    if status != "discovered":
        value["sourceDigest"] = "a" * 64
    return value


class GrowthCandidateLifecycleTests(unittest.TestCase):
    def test_discovery_creates_schema_valid_candidate(self) -> None:
        module = load_module()
        result = module.discover("candidate-1", "local-fixture", "learn", "low")
        self.assertEqual(result["status"], "discovered")
        module.validate_candidate(result)

    def test_lifecycle_promotes_only_through_each_gate(self) -> None:
        module = load_module()
        value = candidate(module)
        for target in ("isolated", "scanned", "evaluated", "candidate"):
            value = module.transition(value, target, source_digest="a" * 64)
        with self.assertRaisesRegex(ValueError, "approval"):
            module.promote(value)
        approved = module.promote(value, approval=True)
        self.assertEqual(approved["status"], "approved")

    def test_invalid_skip_and_terminal_transitions_fail_closed(self) -> None:
        module = load_module()
        with self.assertRaisesRegex(ValueError, "transition"):
            module.transition(candidate(module), "approved")
        with self.assertRaisesRegex(ValueError, "transition"):
            module.transition(candidate(module, "approved"), "candidate")

    def test_quarantine_and_rollback_are_explicit(self) -> None:
        module = load_module()
        quarantined = module.quarantine(candidate(module, "evaluated"))
        self.assertEqual(quarantined["status"], "blocked")
        retired = module.rollback(candidate(module, "approved"))
        self.assertEqual(retired["status"], "retired")

    def test_schema_shape_and_digest_are_revalidated(self) -> None:
        module = load_module()
        bad = candidate(module)
        bad["unexpected"] = "reject"
        with self.assertRaisesRegex(ValueError, "additional"):
            module.validate_candidate(bad)
        with self.assertRaisesRegex(ValueError, "digest"):
            module.transition(candidate(module), "isolated", source_digest="bad")


if __name__ == "__main__":
    unittest.main()
