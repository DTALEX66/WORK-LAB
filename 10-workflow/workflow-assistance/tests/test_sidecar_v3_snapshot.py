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
from durable_worker import CollectorResult
from sidecar import WorkflowSidecar, create_server
from snapshot_validator import validate_snapshot
from workspace_evidence import load_workspace_evidence

PROJECT_ROOT = Path(r"D:\All projects\WORK-LAB")


def make_sidecar(runtime_root: Path) -> WorkflowSidecar:
    return WorkflowSidecar(PROJECT_ROOT, runtime_root)


class CompositionRootTests(unittest.TestCase):
    def test_workspace_evidence_loads_plan_governance_and_history_as_typed_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "50-taskpacks").mkdir()
            (root / "00-governance" / "generated").mkdir(parents=True)
            (root / "50-taskpacks" / "WORK-LAB-MASTER-2.0-APPROVAL-PACKAGE.md").write_text(
                "# Master\n> Status: `DELIVERED_PENDING_REMAINING_APPROVALS`\n"
                "28 个 WL3 任务:\n  VERIFIED_LOCAL: 24\n  BLOCKED(工具链):  1\n  RECONCILE_REQUIRED: 3\n"
                "| WL3-000 | VERIFIED_LOCAL | freshness |\n| WL3-620 | BLOCKED | portable |\n"
                "1. **Hermes/Codex global config live apply** — ✅ Codex 已完成；Hermes live 未动；\n",
                encoding="utf-8",
            )
            (root / "00-governance" / "generated" / "CURRENT_STATE.json").write_text(
                json.dumps({
                    "schema_version": "work-lab-current-state/v1",
                    "generated_at": "2026-08-14T12:58:47Z",
                    "modules": [{"id": "workflow-assistance"}, {"id": "work-lab-observer"}],
                    "contracts": {"count": 30},
                    "skills": {"count": 13},
                    "module_ownership": {"single_writer": True},
                    "stage3": {"taskpack_id": "WORK-LAB-FINAL-MASTER-CONTROL-PLANE", "task_count": 28},
                    "unverified_capabilities": ["commercial_release"],
                }),
                encoding="utf-8",
            )
            (root / "50-taskpacks" / "error-ledger.json").write_text(
                json.dumps({
                    "schema_version": "work-lab/error-ledger/v1",
                    "generated_at": "2026-08-14T12:00:00Z",
                    "summary": {"total": 60, "by_classification": {"contract_drift": 27}},
                    "errors": [{"error_id": "ERR-060", "title": "fail closed", "status_after": "PASS"}],
                }),
                encoding="utf-8",
            )

            evidence = load_workspace_evidence(root)
            self.assertEqual(evidence["plan"]["status"], "DELIVERED_PENDING_REMAINING_APPROVALS")
            self.assertEqual(evidence["plan"]["counts"]["verifiedLocal"], 24)
            self.assertEqual(evidence["plan"]["tasks"][-1]["taskId"], "WL3-620")
            self.assertEqual(evidence["plan"]["approvals"][0]["state"], "PARTIAL")
            self.assertEqual(evidence["governance"]["contracts"], 30)
            self.assertEqual(evidence["history"]["totalErrors"], 60)
            self.assertEqual(evidence["history"]["recentErrors"][0]["errorId"], "ERR-060")
            self.assertEqual({item["evidenceKind"] for item in evidence["sources"]}, {"PLAN", "STATIC_BASELINE", "HISTORY"})

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

    def test_unapproved_registered_project_is_excluded_from_index_and_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = CanonicalStore(Path(tmp) / "c.sqlite")
            try:
                store.register_project("work-lab", str(PROJECT_ROOT), display_name="WORK-LAB")
                store.register_project("unapproved", str(Path(tmp) / "unapproved"))
                store.register_project("approved-external", str(Path(tmp) / "approved"))
                store.upsert_project_definition(
                    "approved-external",
                    {
                        "schema_version": "workflow/product-project/v1",
                        "project_id": "approved-external",
                        "display_name": "Approved External",
                        "approved": True,
                    },
                )

                index = load_approved_index(store)
                self.assertEqual(set(index.projects), {"work-lab", "approved-external"})

                snap = build_v3_snapshot(store, index, revision=0)
                self.assertEqual(
                    {project["projectId"] for project in snap["projects"]},
                    {"work-lab", "approved-external"},
                )
            finally:
                store.close()

    def test_build_v3_snapshot_flat_and_null(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = CanonicalStore(Path(tmp) / "c.sqlite")
            try:
                index = load_approved_index(store)
                snap = build_v3_snapshot(
                    store, index, revision=1,
                    events_url="http://127.0.0.1:9/api/v1/events",
                    transport_state="OFFLINE",
                    freshness_state="STALE",
                )
                self.assertEqual(snap["schemaVersion"], "workflow/snapshot/v3")
                self.assertIsInstance(snap["executions"], list)
                self.assertEqual(snap["tokenSummary"]["costQuality"], "UNKNOWN")
                self.assertIsNone(snap["tokenSummary"]["inputTokens"])
                self.assertEqual(snap["transport"]["eventsUrl"], "http://127.0.0.1:9/api/v1/events")
                self.assertEqual(snap["transport"]["transportState"], "OFFLINE")
                self.assertEqual(snap["transport"]["freshnessState"], "STALE")
                self.assertTrue(validate_snapshot(snap)["valid"])
            finally:
                store.close()

    def test_build_v3_snapshot_exposes_only_real_registry_task_and_local_git_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = CanonicalStore(Path(tmp) / "c.sqlite")
            try:
                store.register_project("work-lab", str(PROJECT_ROOT), display_name="WORK-LAB")
                store.upsert_task({"task_id": "t1", "project_id": "work-lab", "status": "PENDING"})
                store.append_quality(
                    {
                        "row_id": "git-work-lab-test",
                        "project_id": "work-lab",
                        "scope": "git",
                        "quality": "EXACT_SOURCE",
                        "coverage": "PARTIAL",
                        "freshness": "STALE",
                        "observed_at": "2026-08-14T14:59:30Z",
                        "last_good_at": "2026-08-14T14:59:30Z",
                        "head_sha": "769345d21fb9df9d0acafe13f953e41597658b80",
                        "branch": "main",
                        "dirty_count": 10,
                        "sourceRef": "git-rev-parse",
                    }
                )
                snap = build_v3_snapshot(store, load_approved_index(store), revision=0)
                project = snap["projects"][0]
                self.assertEqual(snap["tasks"], {"PENDING": 1})
                self.assertEqual(snap["sourceWatermark"], "2026-08-14T14:59:30Z")
                self.assertEqual(project["activityState"], "REGISTERED")
                self.assertEqual(project["git"]["localSha"], "769345d21fb9df9d0acafe13f953e41597658b80")
                self.assertEqual(project["git"]["branch"], "main")
                self.assertEqual(project["git"]["dirtyCount"], 10)
                self.assertEqual(project["git"]["matchState"], "UNVERIFIED")
                self.assertEqual(project["git"]["observedAt"], "2026-08-14T14:59:30Z")
                self.assertEqual(project["git"]["quality"], "EXACT_SOURCE")
                self.assertEqual(project["git"]["sourceRef"], "git-rev-parse")
                self.assertEqual(snap["executions"], [])
                self.assertEqual(snap["ci"], [])
            finally:
                store.close()

    def test_build_v3_snapshot_preserves_workspace_evidence_without_claiming_live(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = CanonicalStore(Path(tmp) / "c.sqlite")
            try:
                evidence = {"plan": {"status": "PLANNED"}, "history": {"totalErrors": 3}}
                snap = build_v3_snapshot(
                    store,
                    load_approved_index(store),
                    revision=0,
                    transport_state="OFFLINE",
                    workspace_evidence=evidence,
                )
                self.assertEqual(snap["workspace"], evidence)
                self.assertEqual(snap["transport"]["transportState"], "OFFLINE")
            finally:
                store.close()


class SidecarV3SnapshotTests(unittest.TestCase):
    def _start(self) -> tuple[WorkflowSidecar, object, Path]:
        runtime = Path(tempfile.mkdtemp())
        sidecar = make_sidecar(runtime)
        server = create_server(sidecar, port=0, live_updates=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def stop_server() -> None:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.addCleanup(stop_server)
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

    def test_sse_connection_state_counts_concurrent_clients(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sidecar = make_sidecar(Path(tmp))
            try:
                initial = sidecar.v3_snapshot()["transport"]
                self.assertFalse(initial["eventStreamConnected"])
                self.assertIsNone(initial["connectedSince"])
                sidecar.mark_sse_connected()
                sidecar.mark_sse_connected()
                self.assertTrue(sidecar.has_sse_connections())
                connected = sidecar.v3_snapshot()["transport"]
                self.assertTrue(connected["eventStreamConnected"])
                self.assertIsNotNone(connected["connectedSince"])
                sidecar.mark_sse_disconnected()
                self.assertTrue(sidecar.has_sse_connections(), "one disconnect must not hide the remaining client")
                sidecar.mark_sse_disconnected()
                self.assertFalse(sidecar.has_sse_connections())
                disconnected = sidecar.v3_snapshot()["transport"]
                self.assertFalse(disconnected["eventStreamConnected"])
                self.assertIsNone(disconnected["connectedSince"])
                sidecar.mark_sse_disconnected()
                self.assertFalse(sidecar.has_sse_connections(), "connection count never goes negative")
            finally:
                sidecar.close()

    def test_sidecar_startup_does_not_invent_heartbeat_or_writer_freshness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sidecar = make_sidecar(Path(tmp))
            try:
                transport = sidecar.v3_snapshot()["transport"]
                self.assertIsNone(transport["lastHeartbeatAt"])
                self.assertIsNone(transport["writerWatermarkAt"])
            finally:
                sidecar.close()

    def test_fresh_writer_and_complete_collector_health_can_reach_live(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sidecar = make_sidecar(Path(tmp))
            try:
                now = time.time()
                for name in ("task", "git", "usage", "quality", "growth"):
                    sidecar.store.upsert_collector_health(
                        {
                            "name": name,
                            "totalRuns": 1,
                            "lastRunAt": "2026-08-15T00:00:00Z",
                            "lastSuccessAt": "2026-08-15T00:00:00Z",
                            "consecutiveFailures": 0,
                        }
                    )
                sidecar._revision = 1
                sidecar._last_heartbeat_at = now
                sidecar._last_write_at = now
                sidecar.mark_sse_connected()
                transport = sidecar.v3_snapshot()["transport"]
                self.assertEqual(transport["transportState"], "LIVE")
                self.assertEqual(transport["freshnessState"], "FRESH")
            finally:
                sidecar.close()

    def test_embedded_worker_lifecycle_writes_health_and_stops_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sidecar = make_sidecar(Path(tmp))
            def healthy_collector(store: CanonicalStore, project_id: str) -> CollectorResult:
                return CollectorResult(kind="quality", ok=True, records=[])
            try:
                sidecar.start_worker(tick_seconds=0.05, collectors=[healthy_collector])
                deadline = time.time() + 2.0
                while not sidecar.store.list_collector_health() and time.time() < deadline:
                    time.sleep(0.02)
                self.assertTrue(sidecar.worker_running())
                health_names = {row["name"] for row in sidecar.store.list_collector_health()}
                self.assertIn("healthy_collector", health_names)
                self.assertIn("worker_loop", health_names)
                self.assertEqual(sidecar.store.list_projects()[0]["project_id"], "work-lab")
            finally:
                sidecar.close()
            self.assertFalse(sidecar.worker_running())

    def test_sse_connection_scope_releases_count_after_handshake_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sidecar = make_sidecar(Path(tmp))
            try:
                with self.assertRaisesRegex(RuntimeError, "handshake failed"):
                    with sidecar.sse_connection():
                        self.assertTrue(sidecar.has_sse_connections())
                        raise RuntimeError("handshake failed")
                self.assertFalse(sidecar.has_sse_connections())
            finally:
                sidecar.close()


if __name__ == "__main__":
    unittest.main()
