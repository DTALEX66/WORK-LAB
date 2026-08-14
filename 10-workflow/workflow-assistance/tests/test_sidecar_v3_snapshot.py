"""P0-1/P0-2 tests: composition root + sidecar v3 snapshot wiring."""
from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
from pathlib import Path

from canonical_store import CanonicalStore
from composition_root import build_v3_snapshot, load_approved_index
from sidecar import WorkflowSidecar, create_server
from snapshot_validator import validate_snapshot

PROJECT_ROOT = Path(r"D:\All projects\WORK-LAB")


def make_sidecar(runtime_root: Path) -> WorkflowSidecar:
    return WorkflowSidecar(PROJECT_ROOT, runtime_root)


class CompositionRootTests(unittest.TestCase):
    def test_load_approved_index_from_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = CanonicalStore(Path(tmp) / "c.sqlite")
            try:
                store.register_project("work-lab", str(PROJECT_ROOT))
                index = load_approved_index(store)
                self.assertIn("work-lab", set(index.projects.keys()))
                # machine root binding present so resolution can succeed.
                project = index.by_root(str(PROJECT_ROOT))
                self.assertIsNotNone(project)
            finally:
                store.close()

    def test_build_v3_snapshot_flat_and_null(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = CanonicalStore(Path(tmp) / "c.sqlite")
            try:
                index = load_approved_index(store)
                snap = build_v3_snapshot(
                    store, index, revision=1,
                    events_url="http://127.0.0.1:9/api/v1/events", transport_state="OFFLINE",
                )
                self.assertEqual(snap["schemaVersion"], "workflow/snapshot/v3")
                self.assertIsInstance(snap["executions"], list)
                self.assertEqual(snap["tokenSummary"]["costQuality"], "UNKNOWN")
                self.assertIsNone(snap["tokenSummary"]["inputTokens"])
                self.assertEqual(snap["transport"]["eventsUrl"], "http://127.0.0.1:9/api/v1/events")
                self.assertEqual(snap["transport"]["transportState"], "OFFLINE")
                self.assertTrue(validate_snapshot(snap)["valid"])
            finally:
                store.close()


class SidecarV3SnapshotTests(unittest.TestCase):
    def _start(self) -> tuple[WorkflowSidecar, object, Path]:
        runtime = Path(tempfile.mkdtemp())
        sidecar = make_sidecar(runtime)
        server = create_server(sidecar, port=0, live_updates=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        return sidecar, server, runtime

    def test_v1_snapshot_endpoint_returns_v3(self) -> None:
        import urllib.request

        sidecar, server, _ = self._start()
        port = int(server.server_address[1])
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/v1/snapshot", timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        self.assertEqual(data["schemaVersion"], "workflow/snapshot/v3")
        self.assertIsInstance(data["executions"], list)
        self.assertEqual(data["tokenSummary"]["costQuality"], "UNKNOWN")
        self.assertIn("eventsUrl", data["transport"])
        # transport verdict comes from the live gate; never fabricated LIVE.
        self.assertIn(data["transport"]["transportState"], {"OFFLINE", "DELAYED", "LIVE", "UNKNOWN", "CONNECTING"})

    def test_legacy_projection_still_served(self) -> None:
        import urllib.request

        _, server, _ = self._start()
        port = int(server.server_address[1])
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/projection", timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        self.assertEqual(data["schema_version"], "workflow/sidecar-projection/v1")

    def test_events_url_backfilled(self) -> None:
        sidecar, server, _ = self._start()
        port = int(server.server_address[1])
        self.assertEqual(sidecar._events_url, f"http://127.0.0.1:{port}/api/v1/events")


if __name__ == "__main__":
    unittest.main()
