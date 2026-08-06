from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from observer_runtime import (  # noqa: E402
    IncrementalCursor,
    ObserverInputError,
    append_events,
    mutation_surface,
    project_tasks,
    quality_summary,
)


def event(event_id: str, *, task_id: str = "WA-001", quality: str = "source-exact") -> dict:
    return {
        "eventId": event_id,
        "schemaVersion": "work-lab/observer-event/v1",
        "eventType": "task.status",
        "sourceModule": "workflow-assistance",
        "sourceId": "ledger",
        "taskId": task_id,
        "observedAt": "2026-08-06T00:00:00Z",
        "contentDigest": hashlib.sha256(event_id.encode()).hexdigest(),
        "coverage": "full",
        "quality": quality,
    }


class ObserverRuntimeTests(unittest.TestCase):
    def test_incremental_cursor_deduplicates_and_tracks_rotation(self):
        cursor = IncrementalCursor(max_batch=2)
        first = cursor.ingest([event("e1"), event("e2")], next_cursor="b")
        second = cursor.ingest([event("e2"), event("e3")], next_cursor="a")
        self.assertEqual([item["eventId"] for item in first], ["e1", "e2"])
        self.assertEqual([item["eventId"] for item in second], ["e3"])
        self.assertEqual(cursor.rotation, 1)

    def test_event_budget_and_sensitive_input_fail_closed(self):
        with self.assertRaises(ObserverInputError):
            IncrementalCursor(max_batch=1).ingest([event("e1"), event("e2")], next_cursor="a")
        unsafe = event("unsafe")
        unsafe["payload"] = {"token": "[REDACTED]"}
        with self.assertRaises(ObserverInputError):
            IncrementalCursor().ingest([unsafe], next_cursor="a")

    def test_projection_is_rebuildable_and_does_not_change_input(self):
        history = [event("e1"), event("e2", task_id="OD-004", quality="partial")]
        before = [dict(item) for item in history]
        projection = project_tasks(history)
        self.assertEqual(projection["WA-001"]["events"], 1)
        self.assertEqual(projection["OD-004"]["quality"], "partial")
        self.assertEqual(history, before)

    def test_append_is_observer_owned_and_deduplicated(self):
        log = []
        self.assertEqual(append_events(log, [event("e1"), event("e1")]), 1)
        self.assertEqual(len(log), 1)

    def test_quality_and_mutation_surface_are_fail_closed(self):
        summary = quality_summary([event("e1"), event("e2", quality="partial")])
        self.assertEqual(summary["quality"], "partial")
        surface = mutation_surface()
        self.assertFalse(surface["externalMutation"])
        self.assertFalse(surface["ledgerMutation"])
        self.assertNotIn("approve", " ".join(surface["allowedWrites"]))


if __name__ == "__main__":
    unittest.main()
