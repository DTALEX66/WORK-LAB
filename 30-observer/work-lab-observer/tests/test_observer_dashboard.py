from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.request import urlopen, Request
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from observer_dashboard import create_server, ReadOnlyObserverStore  # noqa: E402
from observer_store import ObserverStore  # noqa: E402
from observer_runtime import ObserverInputError  # noqa: E402


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
                self.assertEqual(projection["schemaVersion"], "work-lab/observer-projection/v2")
                self.assertEqual(projection["summary"]["registeredProjects"], 0)
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
                self.assertEqual(projection["schemaVersion"], "work-lab/observer-projection/v2")
                self.assertEqual(projection["summary"]["registeredProjects"], 1)
                self.assertEqual({p["projectId"] for p in projection["projects"]}, {"work-lab"})
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()

    def test_authority_projection_uses_observed_runtime_projects_not_repo_modules(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            (project / ".git").mkdir()
            runtime = project / ".hermes" / "task-runtime" / "observer"
            runtime.mkdir(parents=True)

            def ev(eid: str, project_id: str, event_type: str = "task.status") -> dict:
                return {
                    "eventId": eid,
                    "schemaVersion": "work-lab/observer-event/v1",
                    "eventType": event_type,
                    "sourceModule": "hermes-runtime",
                    "sourceId": "task-ledger",
                    "projectId": project_id,
                    "taskId": eid,
                    "observedAt": "2026-08-07T00:00:00Z",
                    "contentDigest": "0" * 64,
                    "coverage": "full",
                    "quality": "source-exact",
                }

            ObserverStore(runtime, project_root=project).append([
                ev("p1", "cognitive-loop-os", "task.progress"),
                ev("p2", "work-lab", "task.progress"),
                ev("p3", "obsidian-assistance", "task.progress"),
            ])
            server = create_server(project, runtime, port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with urlopen(f"http://127.0.0.1:{server.server_port}/api/dashboard") as response:
                    projection = json.load(response)
                self.assertEqual(projection["summary"]["registeredProjects"], 3)
                self.assertEqual(
                    {p["projectId"] for p in projection["projects"]},
                    {"cognitive-loop-os", "work-lab", "obsidian-assistance"},
                )
                self.assertNotIn("workflow-assistance", {p["projectId"] for p in projection["projects"]})
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
            store.append([
                ev("w1", "WA-001", None),
                ev("w2", "WA-002", None),
                ev("p1", "FX-100", "fixture-external"),
                ev("retired", "OD-100", "open-design"),
            ])
            server = create_server(project, runtime, port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with urlopen(f"http://127.0.0.1:{server.server_port}/api/projects") as response:
                    result = json.load(response)
                self.assertEqual(result["count"], 2)
                by_id = {p["projectId"]: p for p in result["projects"]}
                self.assertEqual(by_id["work-lab"]["taskCount"], 2)
                self.assertEqual(by_id["fixture-external"]["taskCount"], 1)
                self.assertEqual(by_id["fixture-external"]["eventCount"], 1)
                self.assertNotIn("open-design", by_id)
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()

    def test_write_verbs_return_405(self) -> None:
        import http.client
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            (project / ".git").mkdir()
            runtime = project / ".hermes" / "task-runtime" / "observer"
            runtime.mkdir(parents=True)
            server = create_server(project, runtime, port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                port = server.server_port
                for method in ("POST", "PUT", "PATCH", "DELETE"):
                    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                    try:
                        conn.request(method, "/", body=b"{}")
                        resp = conn.getresponse()
                        self.assertEqual(resp.status, 405, f"{method} should be 405, got {resp.status}")
                        resp.read()
                    finally:
                        conn.close()
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()

    def test_readonly_observer_store_rejects_append(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            (project / ".git").mkdir()
            runtime = project / ".hermes" / "task-runtime" / "observer"
            runtime.mkdir(parents=True)
            store = ObserverStore(runtime, project_root=project)
            ro = ReadOnlyObserverStore(store)
            # read surface works
            self.assertEqual(ro.read_events(), [])
            self.assertIn("eventCount", ro.rebuild_projection()["overview"])
            # append is refused at runtime
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
            with self.assertRaises(ObserverInputError):
                ro.append([event])

    def test_api_endpoints_are_read_only_json(self) -> None:
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
                endpoints = ["/api/dashboard", "/api/projects", "/api/tasks", "/api/usage", "/api/quality", "/api/ci", "/api/governance", "/healthz"]
                for ep in endpoints:
                    with urlopen(base + ep, timeout=10) as r:
                        self.assertEqual(r.status, 200, ep)
                        json.load(r)  # must be valid JSON
                # tasks reflects the event
                with urlopen(base + "/api/tasks") as r:
                    tasks = json.load(r)
                self.assertEqual(tasks["count"], 1)
                self.assertIn("WA-001", tasks["tasks"])
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()


if __name__ == "__main__":
    unittest.main()
