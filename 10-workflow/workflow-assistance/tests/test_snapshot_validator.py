"""WLGM-150 tests: snapshot v3 schema validator."""
from __future__ import annotations

import unittest

from snapshot_api import build_snapshot
from snapshot_validator import validate_snapshot


def valid_snapshot() -> dict:
    return build_snapshot(
        revision=3,
        generated_at="2026-08-14T00:00:00Z",
        projects=[{"projectId": "p", "displayName": "P"}],
        executions=[{"executionId": "e1", "anchorProjectId": "p", "state": "RUNNING"}],
    )


class SnapshotValidatorTests(unittest.TestCase):
    def test_valid_snapshot_passes(self) -> None:
        result = validate_snapshot(valid_snapshot())
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["errors"], [])

    def test_wrong_schema_version_fails(self) -> None:
        snapshot = valid_snapshot()
        snapshot["schemaVersion"] = "workflow/snapshot/v2"
        result = validate_snapshot(snapshot)
        self.assertFalse(result["valid"])
        self.assertTrue(any("schemaVersion" in e for e in result["errors"]))

    def test_missing_revision_fails(self) -> None:
        snapshot = valid_snapshot()
        del snapshot["revision"]
        result = validate_snapshot(snapshot)
        self.assertFalse(result["valid"])

    def test_bad_generated_at_fails(self) -> None:
        snapshot = valid_snapshot()
        snapshot["generatedAt"] = "not-a-timestamp"
        result = validate_snapshot(snapshot)
        self.assertFalse(result["valid"])
        self.assertTrue(any("RFC3339" in e for e in result["errors"]))

    def test_missing_project_id_fails(self) -> None:
        snapshot = valid_snapshot()
        snapshot["projects"] = [{"displayName": "no-id"}]
        result = validate_snapshot(snapshot)
        self.assertFalse(result["valid"])
        self.assertTrue(any("projectId" in e for e in result["errors"]))

    def test_duplicate_project_id_warns(self) -> None:
        snapshot = valid_snapshot()
        snapshot["projects"] = [
            {"projectId": "p", "displayName": "P"},
            {"projectId": "p", "displayName": "P2"},
        ]
        result = validate_snapshot(snapshot)
        self.assertTrue(result["valid"])
        self.assertTrue(any("duplicate" in w for w in result["warnings"]))

    def test_null_tokens_not_coerced(self) -> None:
        snapshot = valid_snapshot()
        snapshot["tokenSummary"] = {"inputTokens": None, "outputTokens": None, "totalTokens": None}
        result = validate_snapshot(snapshot)
        self.assertTrue(result["valid"], result["errors"])

    def test_string_token_fails(self) -> None:
        snapshot = valid_snapshot()
        snapshot["tokenSummary"] = {"inputTokens": "120000"}
        result = validate_snapshot(snapshot)
        self.assertFalse(result["valid"])
        self.assertTrue(any("tokenSummary.inputTokens" in e for e in result["errors"]))

    def test_negative_count_fails(self) -> None:
        snapshot = valid_snapshot()
        snapshot["projects"] = [{"projectId": "p", "activeExecutionCount": -1}]
        result = validate_snapshot(snapshot)
        self.assertFalse(result["valid"])

    def test_non_object_fails(self) -> None:
        result = validate_snapshot("not-a-snapshot")  # type: ignore[arg-type]
        self.assertFalse(result["valid"])

    def test_build_snapshot_output_is_valid(self) -> None:
        snapshot = build_snapshot(
            revision=1,
            projects=[{"projectId": "p"}],
            executions=[{"executionId": "e1", "anchorProjectId": "p", "state": "RUNNING"}],
        )
        result = validate_snapshot(snapshot)
        self.assertTrue(result["valid"], result["errors"])


if __name__ == "__main__":
    unittest.main()
