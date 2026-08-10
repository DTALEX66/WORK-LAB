"""Contract tests for the Observer canonical projection adapter (WL3-610)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from canonical_store import CanonicalStore
from observer_canonical import CanonicalProjectionReader, VALID_MODES


class ObserverCanonicalTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.store = CanonicalStore(Path(self._temporary.name) / "canonical.sqlite")

    def tearDown(self) -> None:
        self.store.close()
        self._temporary.cleanup()

    def test_snapshot_reads_canonical_facts_read_only(self) -> None:
        self.store.register_project("work-lab", r"D:\All projects\WORK-LAB")
        self.store.upsert_task({"task_id": "t1", "project_id": "work-lab", "status": "RUNNING"})
        self.store.upsert_task({"task_id": "t2", "project_id": "work-lab", "status": "COMPLETED_LOCAL"})
        reader = CanonicalProjectionReader(self.store)
        snapshot = reader.read_snapshot()
        self.assertEqual(snapshot["mode"], "SNAPSHOT")
        self.assertEqual(snapshot["freshness"], "STALE")
        self.assertEqual(len(snapshot["projects"]), 1)
        self.assertEqual(snapshot["tasksByStatus"]["RUNNING"], 1)

    def test_dashboard_maps_counts_and_never_fabricates_live(self) -> None:
        self.store.upsert_task({"task_id": "t1", "project_id": "p", "status": "PENDING"})
        self.store.upsert_task({"task_id": "t2", "project_id": "p", "status": "BLOCKED_POLICY"})
        reader = CanonicalProjectionReader(self.store)
        dashboard = reader.to_dashboard()
        self.assertEqual(dashboard["mode"], "SNAPSHOT")
        self.assertEqual(dashboard["freshness"]["state"], "STALE")
        self.assertEqual(dashboard["summary"]["tasks"]["waiting"], 1)
        self.assertEqual(dashboard["summary"]["tasks"]["blocked"], 1)
        self.assertEqual(dashboard["mutationSurface"]["externalMutation"], False)

    def test_live_mode_only_after_explicit_transition(self) -> None:
        reader = CanonicalProjectionReader(self.store)
        reader.set_mode("LIVE")
        snapshot = reader.read_snapshot()
        self.assertEqual(snapshot["mode"], "LIVE")
        self.assertEqual(snapshot["freshness"], "LIVE")
        with self.assertRaises(ValueError):
            reader.set_mode("BOGUS")

    def test_valid_modes_are_bounded(self) -> None:
        self.assertEqual(
            VALID_MODES,
            {"LIVE", "STALE", "SNAPSHOT", "FIXTURE", "OFFLINE", "UNKNOWN"},
        )

    def test_usage_unknown_when_no_source(self) -> None:
        reader = CanonicalProjectionReader(self.store)
        dashboard = reader.to_dashboard()
        self.assertEqual(dashboard["usage"]["totalTokens"], 0)
        self.assertEqual(dashboard["usage"]["quality"]["dataQuality"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
