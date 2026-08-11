"""Contract tests for the Observer canonical projection adapter (WL3-610)."""

from __future__ import annotations

import tempfile
import unittest
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_ROOT.parents[1]
sys.path.insert(0, str(MODULE_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "10-workflow" / "workflow-assistance" / "scripts" / "workflow"))

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
        # Dashboard freshness uses the UI vocabulary (fresh/stale/offline/unknown),
        # never the raw source-mode string — renderers must not see unmapped modes.
        self.assertEqual(dashboard["freshness"]["state"], "stale")
        self.assertEqual(dashboard["quality"]["freshness"], "stale")
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
        self.assertIsNone(dashboard["usage"]["totalTokens"])
        self.assertEqual(dashboard["usage"]["quality"]["dataQuality"], "UNKNOWN")

    def test_live_mode_maps_to_fresh_vocabulary(self) -> None:
        reader = CanonicalProjectionReader(self.store)
        reader.set_mode("LIVE")
        dashboard = reader.to_dashboard()
        self.assertEqual(dashboard["mode"], "LIVE")
        self.assertEqual(dashboard["freshness"]["state"], "fresh")
        self.assertEqual(dashboard["usage"]["quality"]["freshness"], "fresh")
        self.assertEqual(dashboard["ci"]["quality"]["freshness"], "fresh")

    def test_offline_mode_maps_to_offline_vocabulary(self) -> None:
        reader = CanonicalProjectionReader(self.store)
        reader.set_mode("OFFLINE")
        dashboard = reader.to_dashboard()
        self.assertEqual(dashboard["freshness"]["state"], "offline")
        self.assertEqual(dashboard["quality"]["freshness"], "offline")

    def test_usage_series_carries_observed_at_bucket(self) -> None:
        self.store.upsert_task({"task_id": "t1", "project_id": "p", "status": "COMPLETED"})
        # usage_samples rows are written by the Workflow owner; insert a sample
        # through a short-lived writer connection so the reader projection can
        # pick it up without sharing transaction state.
        import sqlite3

        writer = sqlite3.connect(self.store.path)
        try:
            writer.execute(
                "INSERT INTO usage_samples "
                "(sample_id, project_id, provider, model, observed_at, input_tokens, output_tokens, total_tokens, quality) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("s1", "p", "deepseek", "deepseek-v4-flash", "2026-08-11T10:00:00+00:00", 100, 50, 150, "exact"),
            )
            writer.commit()
        finally:
            writer.close()
        dashboard = CanonicalProjectionReader(self.store).to_dashboard()
        self.assertEqual(len(dashboard["usage"]["series"]), 1)
        self.assertEqual(dashboard["usage"]["series"][0]["bucket"], "2026-08-11T10:00:00+00:00")
        self.assertEqual(dashboard["usage"]["series"][0]["inputTokens"], 100)
        self.assertEqual(dashboard["usage"]["series"][0]["outputTokens"], 50)
        self.assertEqual(dashboard["usage"]["totalTokens"], 150)


if __name__ == "__main__":
    unittest.main()
