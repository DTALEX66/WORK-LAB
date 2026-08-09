from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/workflow"))
from sidecar import WorkflowSidecar, create_server  # noqa: E402

class SidecarTests(unittest.TestCase):
    def test_health_and_projection_are_get_only(self):
        with tempfile.TemporaryDirectory() as raw:
            sidecar = WorkflowSidecar(ROOT, Path(raw))
            sidecar.ledger.append({"event_id": "evt-1", "occurred_at": "2026-08-08T00:00:00Z", "source": "fixture", "outcome": "completed"})
            sidecar.ledger.append({"event_id": "evt-2", "occurred_at": "2026-08-08T00:01:00Z", "source": "fixture", "outcome": "completed"})
            sidecar.tasks.create("task-1", "idem-1")
            server = create_server(sidecar)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                with urlopen(base + "/healthz") as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(json.load(response)["ledgerOwner"], "workflow-assistance")
                blocked = Request(base + "/healthz", headers={"Origin": "https://external.invalid"})
                with self.assertRaises(Exception):
                    urlopen(blocked)
                with urlopen(base + "/api/projection") as response:
                    self.assertEqual(response.status, 200)
                    projection = json.load(response)
                    self.assertEqual(projection["schema_version"], "workflow/sidecar-projection/v1")
                    self.assertEqual(projection["tasks"], {"count": 1, "by_status": {"QUEUED": 1}})
                with urlopen(base + "/api/v1/events") as response:
                    self.assertEqual(response.headers["Content-Type"].split(";")[0], "text/event-stream")
                    self.assertIn(b"evt-1", response.read())
                reconnect = Request(base + "/api/v1/events", headers={"Last-Event-ID": "evt-1"})
                with urlopen(reconnect) as response:
                    body = response.read()
                    self.assertNotIn(b"evt-1", body)
                    self.assertIn(b"evt-2", body)
                request = Request(base + "/healthz", method="POST")
                with self.assertRaises(Exception):
                    urlopen(request)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

if __name__ == "__main__":
    unittest.main()
