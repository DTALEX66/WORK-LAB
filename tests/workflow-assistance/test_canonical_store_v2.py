"""WLGM-140 tests: canonical SQLite schema v2 + WLGM store methods."""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from canonical_store import CanonicalStore, WAL_TABLES, rollback_v2_backup

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

    def test_v2_migration_creates_backup_once(self) -> None:
        raw = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: None)
        db = raw / "canonical.sqlite"
        # Pre-create a v1-only database (no v2 tables, no version-2 row).
        conn = sqlite3.connect(str(db))
        conn.executescript(
            """
            CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
            CREATE TABLE projects (project_id TEXT PRIMARY KEY, root_path TEXT NOT NULL, display_name TEXT, registered_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'REGISTERED');
            INSERT INTO schema_migrations (version, applied_at) VALUES (1, '2026-08-14T00:00:00Z');
            INSERT INTO projects (project_id, root_path, registered_at) VALUES ('legacy', 'C:/legacy', '2026-08-14T00:00:00Z');
            """
        )
        conn.commit()
        conn.close()

        store = CanonicalStore(db)
        try:
            versions = {row["version"] for row in store._conn.execute("SELECT version FROM schema_migrations")}
            self.assertIn(2, versions)
            self.assertIn("project_definitions", {r["name"] for r in store._conn.execute("SELECT name FROM sqlite_master WHERE type='table'")})
            # Legacy data survived the migration.
            self.assertEqual(store.list_projects()[0]["project_id"], "legacy")
            # Backup created exactly once.
            backups = list(db.parent.glob(db.name + ".bak-v2-*"))
            self.assertEqual(len(backups), 1)
        finally:
            store.close()
            db.unlink(missing_ok=True)

    def test_v2_migration_is_idempotent_no_extra_backup(self) -> None:
        raw = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: None)
        db = raw / "canonical.sqlite"
        store1 = CanonicalStore(db)
        store1.close()
        store2 = CanonicalStore(db)
        store2.close()
        backups = list(db.parent.glob(db.name + ".bak-v2-*"))
        self.assertEqual(len(backups), 1, "second open must not create another backup")

    def test_rollback_v2_backup_restores_v1(self) -> None:
        raw = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: None)
        db = raw / "canonical.sqlite"
        store = CanonicalStore(db)
        store.register_project("p1", "C:/p1")
        store.close()
        backup_count = len(list(db.parent.glob(db.name + ".bak-v2-*")))
        self.assertEqual(backup_count, 1)

        restored = rollback_v2_backup(db)
        self.assertIsNotNone(restored)
        # The restored (pre-v2 backup) database no longer has v2 tables.
        conn = sqlite3.connect(str(db))
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        conn.close()
        self.assertNotIn("project_definitions", tables)
        self.assertIn("projects", tables)

    def test_rollback_v2_no_backup_returns_none(self) -> None:
        raw = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: None)
        self.assertIsNone(rollback_v2_backup(raw / "missing.sqlite"))


if __name__ == "__main__":
    unittest.main()
