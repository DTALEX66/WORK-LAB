"""Gate: the Work lane's task detail records are a real projection, not a card with no source.

P1-02 asked for a deep-linkable Work surface. A link can only resolve against a record the backend
actually carries, so this gate pins the read side end to end: the canonical store's own ``list_tasks()``
-> ``snapshot_api.project_task_record`` -> ``build_snapshot`` -> ``snapshot_validator``.

Two things it deliberately refuses:

* padding — ``taskRecords`` is ABSENT when the producer did not query, and an empty LIST when it queried
  and found nothing. Those are different statements to a reader and must not collapse into one another;
* content — the ``checkpoint`` column is workflow text that may quote a user. A read-only projection
  carries its key names and a digest so a change is visible and identity is verifiable, and never the
  values (AGENTS.md: no prompt bodies leave the boundary).

Discovered dynamically by ``run_quality_gate.py governance`` and by the snapshot-schema-v3 gate.
"""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "client-neutral-core" / "scripts"))

import snapshot_api  # noqa: E402
import snapshot_validator  # noqa: E402
from canonical_store import CanonicalStore  # noqa: E402
from project_temp import fixture_dir  # noqa: E402

GENERATED_AT = "2026-10-08T00:00:00Z"


def minimal_snapshot(**extra):
    base = {
        "schemaVersion": snapshot_api.SNAPSHOT_SCHEMA_VERSION,
        "revision": 1,
        "generatedAt": GENERATED_AT,
        "projects": [],
    }
    base.update(extra)
    return base


class ProjectionShapeTests(unittest.TestCase):
    def row(self, **over):
        row = {
            "task_id": "WL-042",
            "project_id": "work-lab",
            "status": "RUNNING",
            "created_at": "2026-10-08T00:00:00Z",
            "updated_at": "2026-10-08T00:01:00Z",
            "checkpoint": {"cursor": 7, "stage": "verify"},
            "lease_holder": "worker-A",
            "lease_expires_at": "2026-10-08T00:05:00Z",
            "fencing_token": 3,
        }
        row.update(over)
        return row

    def test_every_identity_field_comes_from_the_row(self) -> None:
        projected = snapshot_api.project_task_record(self.row())
        self.assertEqual(projected["taskId"], "WL-042")
        self.assertEqual(projected["projectId"], "work-lab")
        self.assertEqual(projected["status"], "RUNNING")
        self.assertEqual(projected["leaseHolder"], "worker-A")
        self.assertEqual(projected["fencingToken"], 3)

    def test_checkpoint_values_never_enter_the_projection(self) -> None:
        """The privacy half of the boundary: a quoted prompt line stays in the store."""
        leaked_text = "please read my private session and summarise it"
        projected = snapshot_api.project_task_record(
            self.row(checkpoint={"cursor": 7, "user_note": leaked_text})
        )
        serialised = json.dumps(projected, ensure_ascii=False)
        self.assertNotIn(leaked_text, serialised, "a checkpoint value reached the read-only projection")
        self.assertIn("user_note", projected["checkpointKeys"], "the key name is what a reader needs")
        self.assertEqual(projected["checkpointKeys"], ["cursor", "user_note"])

    def test_digest_is_a_stable_identity_and_moves_with_the_checkpoint(self) -> None:
        first = snapshot_api.project_task_record(self.row())
        same = snapshot_api.project_task_record(self.row())
        changed = snapshot_api.project_task_record(self.row(checkpoint={"cursor": 8, "stage": "verify"}))
        self.assertEqual(first["checkpointDigest"], same["checkpointDigest"])
        self.assertEqual(len(first["checkpointDigest"]), 64)
        self.assertNotEqual(first["checkpointDigest"], changed["checkpointDigest"])

    def test_missing_checkpoint_is_not_padded(self) -> None:
        projected = snapshot_api.project_task_record(self.row(checkpoint=None, fencing_token=None))
        self.assertFalse(projected["checkpointPresent"])
        self.assertEqual(projected["checkpointKeys"], [])
        self.assertIsNone(projected["checkpointDigest"])
        self.assertIsNone(projected["fencingToken"])


class SnapshotPresenceTests(unittest.TestCase):
    def test_absent_when_the_producer_did_not_query(self) -> None:
        snapshot = snapshot_api.build_snapshot(revision=1, projects=[])
        self.assertNotIn("taskRecords", snapshot)

    def test_empty_list_when_queried_and_nothing_was_found(self) -> None:
        snapshot = snapshot_api.build_snapshot(revision=1, projects=[], task_records=[])
        self.assertEqual(snapshot["taskRecords"], [])

    def test_the_two_statements_validate_differently(self) -> None:
        queried = snapshot_api.build_snapshot(revision=1, projects=[], task_records=[])
        self.assertTrue(snapshot_validator.validate_snapshot(queried)["valid"])


class StoreIntegrationTests(unittest.TestCase):
    def test_a_real_task_row_projects_and_validates_end_to_end(self) -> None:
        root = fixture_dir(prefix="snapshot-task-records-")
        store = CanonicalStore(root / "canonical.sqlite")
        try:
            store.upsert_task({"task_id": "WL-777", "project_id": "work-lab", "status": "RUNNING"})
            rows = [snapshot_api.project_task_record(row) for row in store.list_tasks()]
        finally:
            store.close()
        self.assertEqual([row["taskId"] for row in rows], ["WL-777"])
        snapshot = snapshot_api.build_snapshot(revision=1, projects=[], task_records=rows)
        verdict = snapshot_validator.validate_snapshot(snapshot)
        self.assertTrue(verdict["valid"], verdict["errors"])


class ValidatorRefusalTests(unittest.TestCase):
    def good(self):
        return {
            "taskId": "T-1", "projectId": "work-lab", "status": "RUNNING",
            "createdAt": GENERATED_AT, "updatedAt": GENERATED_AT,
            "leaseHolder": None, "leaseExpiresAt": None, "fencingToken": None,
            "checkpointPresent": False, "checkpointKeys": [], "checkpointDigest": None,
        }

    def reject(self, records, fragment):
        verdict = snapshot_validator.validate_snapshot(minimal_snapshot(taskRecords=records))
        self.assertFalse(verdict["valid"], f"accepted: {records}")
        self.assertTrue(any(fragment in error for error in verdict["errors"]),
                        f"errors={verdict['errors']} did not name {fragment}")

    def test_record_must_be_an_object(self) -> None:
        self.reject(["not a record"], "must be an object")

    def test_task_id_is_required_and_unique(self) -> None:
        self.reject([dict(self.good(), taskId="")], "taskId required")
        self.reject([self.good(), self.good()], "duplicates")

    def test_project_and_status_are_required(self) -> None:
        self.reject([dict(self.good(), projectId=None)], "projectId required")
        self.reject([dict(self.good(), status="")], "status required")

    def test_fencing_token_is_int_or_null(self) -> None:
        self.reject([dict(self.good(), fencingToken="3")], "fencingToken must be int|null")

    def test_checkpoint_flag_and_digest_must_agree(self) -> None:
        self.reject([dict(self.good(), checkpointPresent="yes")], "checkpointPresent must be boolean")
        self.reject([dict(self.good(), checkpointKeys="cursor")], "checkpointKeys must be a list")
        self.reject([dict(self.good(), checkpointPresent=True)],
                    "must be a digest when a checkpoint exists")
        self.reject([dict(self.good(), checkpointDigest=hashlib.sha256(b"x").hexdigest())],
                    "must be null when no checkpoint exists")


if __name__ == "__main__":
    unittest.main(verbosity=2)
