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
                self.assertIn("外部变更", page)
                self.assertIn("看见工作", page)
                with urlopen(base + "/api/dashboard") as response:
                    projection = json.load(response)
                self.assertEqual(projection["overview"]["eventCount"], 0)
                self.assertFalse(projection["mutationSurface"]["externalMutation"])
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()

    def test_four_views_share_projection_and_render(self) -> None:
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
                base = f"http://127.0.0.1:{server.server_port}"
                views = {"full": ("?view=full", "任务投影", "用量与成本", "数据质量"),
                         "compact": ("?view=compact", "任务投影", "用量", "成本状态")}
                for theme in ("dark", "light"):
                    for view, (qs, *must) in views.items():
                        with urlopen(base + "/" + qs + f"&theme={theme}") as response:
                            page = response.read().decode("utf-8")
                        self.assertEqual(response.status, 200)
                        # view + theme class applied
                        self.assertIn(f"theme-{theme}", page)
                        self.assertIn(f"class=\"theme-{theme} {view}\"", page)
                        for m in must:
                            self.assertIn(m, page, f"missing {m!r} in {view}/{theme}")
                # Projection identical across views
                with urlopen(base + "/api/dashboard?view=full&theme=dark") as r:
                    p1 = json.load(r)
                with urlopen(base + "/api/dashboard?view=compact&theme=light") as r:
                    p2 = json.load(r)
                self.assertEqual(p1, p2)
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()

    def test_no_write_endpoints(self) -> None:
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
                page = urlopen(base + "/").read().decode("utf-8")
                for marker in ("action=", "method=\"post\"", "method=\"PUT\"", "method=\"DELETE\"", "onclick", "<button"):
                    self.assertNotIn(marker.lower(), page.lower(), f"write surface leaked: {marker}")
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


    def test_api_projects_groups_cross_project_events(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            (project / ".git").mkdir()
            runtime = project / ".hermes" / "task-runtime" / "observer"
            runtime.mkdir(parents=True)

            def ev(eid: str, task: str, project_id: str | None = None) -> dict:
                event = {
                    "eventId": eid,
                    "schemaVersion": "work-lab/observer-event/v1",
                    "eventType": "task.status",
                    "sourceModule": "workflow-assistance",
                    "sourceId": "ledger",
                    "taskId": task,
                    "observedAt": "2026-08-07T00:00:00Z",
                    "contentDigest": "0" * 64,
                    "coverage": "full",
                    "quality": "source-exact",
                }
                if project_id:
                    event["projectId"] = project_id
                return event

            store = ObserverStore(runtime, project_root=project)
            store.append([ev("w1", "WA-001", None), ev("w2", "WA-002", None), ev("p1", "OD-100", "open-design")])
            server = create_server(project, runtime, port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with urlopen(f"http://127.0.0.1:{server.server_port}/api/projects") as response:
                    result = json.load(response)
                self.assertEqual(result["count"], 2)
                by_id = {p["projectId"]: p for p in result["projects"]}
                self.assertEqual(by_id["work-lab"]["taskCount"], 2)
                self.assertEqual(by_id["open-design"]["taskCount"], 1)
                self.assertEqual(by_id["open-design"]["eventCount"], 1)
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()


if __name__ == "__main__":
    unittest.main()
