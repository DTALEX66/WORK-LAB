from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from observer_dashboard import create_server  # noqa: E402
from observer_store import ObserverStore  # noqa: E402


class ObserverDashboardTests(unittest.TestCase):
    def test_dashboard_and_json_are_reachable_read_only_entries(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            (project / ".git").mkdir()
            runtime = project / ".hermes" / "task-runtime" / "observer"
            runtime.mkdir(parents=True)
            server = create_server(project, runtime, port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                with urlopen(base + "/healthz") as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(json.load(response)["readOnly"], True)
                with urlopen(base + "/") as response:
                    page = response.read().decode("utf-8")
                self.assertIn("WORK-LAB Observer", page)
                self.assertIn("EXTERNAL MUTATION: FALSE", page)
                with urlopen(base + "/api/dashboard") as response:
                    projection = json.load(response)
                self.assertEqual(projection["overview"]["eventCount"], 0)
                self.assertFalse(projection["mutationSurface"]["externalMutation"])
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()

    def test_dashboard_reads_observer_owned_store_projection(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            (project / ".git").mkdir()
            runtime = project / ".hermes" / "task-runtime" / "observer"
            runtime.mkdir(parents=True)
            event = {
                "eventId": "e1",
                "schemaVersion": "work-lab/observer-event/v1",
                "eventType": "task.status",
                "sourceModule": "workflow-assistance",
                "sourceId": "ledger",
                "taskId": "WA-001",
                "observedAt": "2026-08-07T00:00:00Z",
                "contentDigest": "0" * 64,
                "coverage": "full",
                "quality": "source-exact",
            }
            ObserverStore(runtime, project_root=project).append([event])
            server = create_server(project, runtime, port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with urlopen(f"http://127.0.0.1:{server.server_port}/api/dashboard") as response:
                    projection = json.load(response)
                self.assertEqual(projection["overview"]["taskCount"], 1)
                self.assertEqual(projection["tasks"]["WA-001"]["events"], 1)
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()


if __name__ == "__main__":
    unittest.main()
