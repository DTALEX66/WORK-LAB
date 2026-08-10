from __future__ import annotations

import json
import hashlib
from pathlib import Path
import tempfile
import unittest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from observer_runtime import ObserverInputError  # noqa: E402
from observer_store import ObserverStore  # noqa: E402


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


class ObserverStoreTests(unittest.TestCase):
    def make_root(self, raw: str) -> Path:
        (Path(raw) / ".git").mkdir()
        root = Path(raw) / ".hermes" / "task-runtime" / "observer"
        root.mkdir(parents=True)
        return root

    def test_restart_preserves_events_and_rebuilds_projection(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = self.make_root(raw)
            first = ObserverStore(root, project_root=Path(raw))
            self.assertEqual(first.append([event("e1"), event("e2", task_id="WA-002", quality="partial")]), 2)

            restarted = ObserverStore(root, project_root=Path(raw))
            self.assertEqual(restarted.read_events(), [event("e1"), event("e2", task_id="WA-002", quality="partial")])
            projection = restarted.rebuild_projection()
            self.assertEqual(len(projection["tasks"]), 2)
            self.assertTrue(all("taskId" not in task for task in projection["tasks"]))
            self.assertEqual(projection["quality"]["quality"], "partial")
            self.assertEqual(projection["usage"]["records"], 0)

    def test_duplicate_events_are_not_written_twice(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            store = ObserverStore(self.make_root(raw), project_root=Path(raw))
            self.assertEqual(store.append([event("e1"), event("e1")]), 1)
            self.assertEqual(store.append([event("e1")]), 0)
            self.assertEqual(len(store.read_events()), 1)
            self.assertEqual(store.path.read_text(encoding="utf-8").count("\n"), 1)

    def test_sensitive_or_malformed_existing_records_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = self.make_root(raw)
            path = root / "observer-events.jsonl"
            unsafe = event("e1")
            unsafe["payload"] = {"prompt": "must not persist"}
            path.write_text(json.dumps(unsafe) + "\n", encoding="utf-8")
            with self.assertRaises(ObserverInputError):
                ObserverStore(root, project_root=Path(raw)).read_events()

    def test_store_rejects_non_project_runtime_root(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            (Path(raw) / ".git").mkdir()
            outside = Path(raw) / ".hermes" / "task-runtime" / "outside"
            outside.mkdir(parents=True)
            with self.assertRaises(ValueError):
                ObserverStore(outside, project_root=Path(raw))

    def test_store_rejects_runtime_root_outside_project_even_with_matching_names(self) -> None:
        with tempfile.TemporaryDirectory() as project_raw, tempfile.TemporaryDirectory() as other_raw:
            (Path(project_raw) / ".git").mkdir()
            outside = Path(other_raw) / ".hermes" / "task-runtime" / "observer"
            outside.mkdir(parents=True)
            with self.assertRaises(ValueError):
                ObserverStore(outside, project_root=Path(project_raw))


if __name__ == "__main__":
    unittest.main()
