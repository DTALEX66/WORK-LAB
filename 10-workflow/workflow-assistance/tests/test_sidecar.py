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
                evil_suffix = Request(base + "/healthz", headers={"Origin": "http://127.0.0.1.evil.invalid"})
                with self.assertRaises(Exception):
                    urlopen(evil_suffix)
                allowed = Request(base + "/healthz", headers={"Origin": "http://localhost:8765"})
                with urlopen(allowed) as response:
                    self.assertEqual(response.headers["Access-Control-Allow-Origin"], "http://localhost:8765")
                with urlopen(base + "/api/projection") as response:
                    self.assertEqual(response.status, 200)
                    projection = json.load(response)
                    self.assertEqual(projection["schema_version"], "workflow/sidecar-projection/v1")
                    self.assertEqual(projection["tasks"], {"count": 1, "by_status": {"QUEUED": 1}})
                with urlopen(base + "/api/v1/events") as response:
                    self.assertEqual(response.headers["Content-Type"].split(";")[0], "text/event-stream")
                    body = response.read()
                    self.assertIn(b"evt-1", body)
                    self.assertIn(b"id: evt-1\ndata: ", body)
                    self.assertNotIn(b"\\ndata:", body)
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

    def test_bind_lock_descriptor_and_get_projection_are_fail_closed(self):
        with tempfile.TemporaryDirectory() as raw:
            runtime = Path(raw)
            sidecar = WorkflowSidecar(ROOT, runtime)
            with self.assertRaises(ValueError):
                create_server(sidecar, host="0.0.0.0")

            server = create_server(sidecar)
            endpoint = runtime / "sidecar-endpoint.json"
            self.assertTrue(endpoint.is_file())
            descriptor = json.loads(endpoint.read_text(encoding="utf-8"))
            self.assertEqual(descriptor["schemaVersion"], "workflow/sidecar-endpoint/v1")
            self.assertEqual(descriptor["port"], server.server_port)
            with self.assertRaises(RuntimeError):
                create_server(WorkflowSidecar(ROOT, runtime))

            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with urlopen(f"http://127.0.0.1:{server.server_port}/api/projection") as response:
                    projection = json.load(response)
                self.assertEqual(projection["tasks"], {"count": 0, "by_status": {}})
                self.assertFalse((runtime / "task-ledger").exists(), "GET projection must not create Task Ledger state")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
            self.assertFalse(endpoint.exists())

            replacement = create_server(WorkflowSidecar(ROOT, runtime))
            replacement.server_close()

if __name__ == "__main__":
    unittest.main()
