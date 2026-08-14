"""WLGM-140 tests: canonical SQLite schema v2 + WLGM store methods."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from canonical_store import CanonicalStore, WAL_TABLES

V2_TABLES = {
    "project_definitions",
    "project_root_bindings",
    "repository_identities",
    "worktree_identities",
    "agent_instances",
    "agent_capabilities",
    "sessions",
    "execution_instances",
    "execution_evidence",
    "execution_heartbeats",
    "collector_health",
    "project_activity_projection",
    "projection_revisions",
}


class CanonicalStoreV2Tests(unittest.TestCase):
    def _store(self) -> CanonicalStore:
        raw = tempfile.TemporaryDirectory()
        self.addCleanup(raw.cleanup)
        return CanonicalStore(Path(raw.name) / "canonical.sqlite")

    def test_v2_tables_created(self) -> None:
        store = self._store()
        try:
            rows = store._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN (%s)" % ",".join("?" * len(V2_TABLES)),
                tuple(sorted(V2_TABLES)),
            ).fetchall()
            found = {row["name"] for row in rows}
            self.assertEqual(found, V2_TABLES)
        finally:
            store.close()

    def test_migrations_versioned(self) -> None:
        store = self._store()
        try:
            versions = {row["version"] for row in store._conn.execute("SELECT version FROM schema_migrations")}
            self.assertIn(2, versions)
        finally:
            store.close()

    def test_project_definition_roundtrip(self) -> None:
        store = self._store()
        try:
            store.upsert_project_definition("work-lab", {"project_id": "work-lab", "display_name": "WORK-LAB"})
            loaded = store.get_project_definition("work-lab")
            self.assertEqual(loaded["display_name"], "WORK-LAB")
        finally:
            store.close()

    def test_upsert_execution_instance_idempotent(self) -> None:
        store = self._store()
        try:
            status = {
                "executionId": "exec-1",
                "agent": "hermes",
                "sessionId": "s1",
                "anchorProjectId": "p",
                "state": "RUNNING",
                "stateQuality": "SOURCE_REPORTED",
            }
            store.upsert_execution_instance(status)
            store.upsert_execution_instance(status)
            executions = store.list_executions()
            self.assertEqual(len(executions), 1)
            self.assertEqual(executions[0]["state"], "RUNNING")
        finally:
            store.close()

    def test_evidence_dedupe_replay_no_double_count(self) -> None:
        store = self._store()
        try:
            record = {
                "eventId": "evt-1",
                "executionId": "exec-1",
                "eventType": "execution_running",
                "evidenceLevel": "A",
                "quality": "SOURCE_REPORTED",
                "occurredAt": "2026-08-14T00:00:00Z",
                "observedAt": "2026-08-14T00:00:00Z",
                "dedupeKey": "dup-key-1",
                "sourceRef": "src-1",
            }
            first = store.append_execution_evidence(record)
            replay = store.append_execution_evidence(record)
            self.assertEqual(first, replay)
            count = store._conn.execute("SELECT COUNT(*) FROM execution_evidence WHERE dedupe_key='dup-key-1'").fetchone()[0]
            self.assertEqual(count, 1)
        finally:
            store.close()

    def test_evidence_rejects_auth_fields(self) -> None:
        store = self._store()
        try:
            with self.assertRaises(ValueError):
                store.append_execution_evidence(
                    {"eventId": "x", "executionId": "e", "eventType": "execution_running", "api_key": "sk-1"}
                )
        finally:
            store.close()

    def test_collector_health_upsert(self) -> None:
        store = self._store()
        try:
            store.upsert_collector_health({"name": "git-collector", "totalRuns": 3, "consecutiveFailures": 0})
            store.upsert_collector_health({"name": "git-collector", "totalRuns": 4, "consecutiveFailures": 1})
            rows = store._conn.execute("SELECT * FROM collector_health WHERE name='git-collector'").fetchall()
            self.assertEqual(rows[0]["total_runs"], 4)
            self.assertEqual(rows[0]["consecutive_failures"], 1)
        finally:
            store.close()

    def test_projection_revision_increments(self) -> None:
        store = self._store()
        try:
            r1 = store.save_projection("p", {"projectId": "p", "activityState": "IDLE"})
            r2 = store.save_projection("p", {"projectId": "p", "activityState": "ACTIVE"})
            self.assertEqual(r2, r1 + 1)
            revisions = store._conn.execute("SELECT COUNT(*) FROM projection_revisions").fetchone()[0]
            self.assertEqual(revisions, 2)
        finally:
            store.close()

    def test_old_schema_upgrade_keeps_history(self) -> None:
        store = self._store()
        try:
            store.register_project("legacy", "C:/legacy")
            projects = store.list_projects()
            self.assertEqual(len(projects), 1)
            self.assertEqual(store.integrity_check(), "ok")
        finally:
            store.close()


if __name__ == "__main__":
    unittest.main()
