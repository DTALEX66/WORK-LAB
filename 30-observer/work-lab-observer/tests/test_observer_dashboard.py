from __future__ import annotations

import http.client
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

MODULE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_ROOT.parents[1]
sys.path.insert(0, str(MODULE_ROOT / "src"))
sys.path.insert(0, str(MODULE_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "10-workflow" / "workflow-assistance" / "scripts" / "workflow"))

from canonical_store import CanonicalStore  # noqa: E402
from observer_dashboard import _allowed_origin, create_server  # noqa: E402


class ObserverDashboardTests(unittest.TestCase):
    def make_project(self, raw: str) -> tuple[Path, Path]:
        project = Path(raw)
        (project / ".git").mkdir()
        path = project / ".hermes" / "task-runtime" / "workflow" / "canonical.sqlite"
        writer = CanonicalStore(path)
        writer.register_project("work-lab", "<redacted>", "WORK-LAB")
        writer.upsert_task({"task_id": "t1", "project_id": "work-lab", "status": "RUNNING"})
        writer.close()
        return project, path

    def serve(self, project: Path, path: Path):
        server = create_server(project, path, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread

    def test_get_endpoints_read_canonical_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project, path = self.make_project(raw)
            before = (path.stat().st_mtime_ns, path.stat().st_size)
            server, thread = self.serve(project, path)
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                with urlopen(base + "/api/dashboard") as response:
                    projection = json.load(response)
                self.assertEqual(projection["mode"], "SNAPSHOT")
                self.assertEqual(projection["schemaVersion"], "workflow/snapshot/v3")
                self.assertEqual(len(projection["projects"]), 1)
                self.assertIsNone(projection["tokenSummary"]["totalTokens"])
                for endpoint in ("/api/projects", "/api/tasks", "/api/usage", "/api/quality", "/api/ci", "/api/governance", "/healthz"):
                    with urlopen(base + endpoint) as response:
                        self.assertEqual(response.status, 200)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
            self.assertEqual(before, (path.stat().st_mtime_ns, path.stat().st_size))
            self.assertFalse((project / ".hermes" / "task-runtime" / "observer").exists())

    def test_live_mode_requires_a_discovered_live_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project, path = self.make_project(raw)
            endpoint = path.parent / "sidecar-endpoint.json"
            endpoint.write_text(
                json.dumps(
                    {
                        "schemaVersion": "workflow/sidecar-endpoint/v1",
                        "pid": os.getpid(),
                        "eventsUrl": "http://127.0.0.1:43123/api/v1/events",
                    }
                ),
                encoding="utf-8",
            )
            server, thread = self.serve(project, path)
            try:
                with urlopen(f"http://127.0.0.1:{server.server_port}/api/dashboard") as response:
                    projection = json.load(response)
                self.assertEqual(projection["mode"], "LIVE")
                self.assertEqual(projection["transport"]["state"], "discovered")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_origin_and_methods_are_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project, path = self.make_project(raw)
            server, thread = self.serve(project, path)
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                allowed = Request(base + "/api/dashboard", headers={"Origin": "http://localhost:3000"})
                with urlopen(allowed) as response:
                    self.assertEqual(response.headers["Access-Control-Allow-Origin"], "http://localhost:3000")
                tauri = Request(base + "/api/dashboard", headers={"Origin": "http://tauri.localhost"})
                with urlopen(tauri) as response:
                    self.assertEqual(response.headers["Access-Control-Allow-Origin"], "http://tauri.localhost")
                with self.assertRaises(Exception):
                    urlopen(Request(base + "/api/dashboard", headers={"Origin": "https://external.invalid"}))
                for method in ("POST", "PUT", "PATCH", "DELETE"):
                    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                    connection.request(method, "/api/dashboard")
                    self.assertEqual(connection.getresponse().status, 405)
                    connection.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_html_views_have_no_write_controls(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project, path = self.make_project(raw)
            server, thread = self.serve(project, path)
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                for view in ("full", "compact"):
                    for theme in ("dark", "light"):
                        page = urlopen(f"{base}/?view={view}&theme={theme}").read().decode("utf-8").lower()
                        for marker in ('method="post"', 'method="put"', 'method="delete"', "<button", "onclick"):
                            self.assertNotIn(marker, page)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_missing_store_and_fixed_port_guess_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            (project / ".git").mkdir()
            missing = project / ".hermes" / "task-runtime" / "workflow" / "canonical.sqlite"
            with self.assertRaises(FileNotFoundError):
                create_server(project, missing, port=0)
            self.assertFalse(missing.parent.exists())
        source = (MODULE_ROOT / "scripts" / "observer_dashboard.py").read_text(encoding="utf-8")
        self.assertNotIn("default=8765", source)

    def test_windows_pid_probe_uses_read_only_process_handle(self) -> None:
        source = (MODULE_ROOT / "scripts" / "observer_dashboard.py").read_text(encoding="utf-8")
        windows_branch = source.index('if os.name == "nt"')
        posix_signal = source.index("os.kill(pid, 0)")
        self.assertLess(windows_branch, posix_signal)
        self.assertIn("PROCESS_QUERY_LIMITED_INFORMATION".lower(), source.lower())
        self.assertIn("GetExitCodeProcess", source)
        self.assertTrue(_allowed_origin("tauri://localhost"))
        self.assertTrue(_allowed_origin("http://tauri.localhost"))
        self.assertFalse(_allowed_origin("http://tauri.localhost.evil.invalid"))


if __name__ == "__main__":
    unittest.main()
