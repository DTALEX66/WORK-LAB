"""Observer canonical projection adapter (WL3-610).

Observer consumes the Workflow-owned canonical SQLite WAL (the single runtime
fact source) through a read-only path and renders a dashboard projection. The
legacy ``observer-events.jsonl`` store is no longer authoritative for business
facts; this module never writes to the canonical store and never mutates any
authoritative state. The connection degrades to STALE/OFFLINE/UNKNOWN instead
of fabricating LIVE values.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

VALID_MODES = {"LIVE", "STALE", "SNAPSHOT", "FIXTURE", "OFFLINE", "UNKNOWN"}


class SQLiteReadOnlyStore:
    """Minimal canonical-store reader using SQLite ``mode=ro`` only."""

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()
        if not self.path.is_file():
            raise FileNotFoundError(f"canonical SQLite store not found: {self.path}")
        uri = self.path.as_uri() + "?mode=ro"
        self._conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def integrity_check(self) -> str:
        row = self._conn.execute("PRAGMA integrity_check").fetchone()
        return str(row[0]) if row else "unknown"

    def list_projects(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self._conn.execute("SELECT * FROM projects ORDER BY registered_at")]

    def list_tasks(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self._conn.execute("SELECT * FROM tasks ORDER BY updated_at DESC")]

    def projection(self) -> dict[str, Any]:
        tables = {
            str(row[0])
            for row in self._conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        task_counts = {
            str(row["status"]): int(row["n"])
            for row in self._conn.execute("SELECT status, COUNT(*) AS n FROM tasks GROUP BY status")
        }
        usage = [
            dict(row)
            for row in self._conn.execute(
                "SELECT provider, model, COUNT(*) AS samples, SUM(total_tokens) AS tokens "
                "FROM usage_samples GROUP BY provider, model"
            )
        ]
        ci = [
            dict(row)
            for row in self._conn.execute(
                "SELECT status, conclusion, COUNT(*) AS n FROM ci_runs GROUP BY status, conclusion"
            )
        ]
        return {
            "integrity": self.integrity_check(),
            "tables": {name: self._conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0] for name in sorted(tables)},
            "telemetry_events": self._conn.execute("SELECT COUNT(*) FROM telemetry_events").fetchone()[0],
            "tasks_by_status": task_counts,
            "usage_summary": usage,
            "ci_summary": ci,
        }

    def close(self) -> None:
        self._conn.close()


class CanonicalProjectionReader:
    """Read-only facade over the canonical SQLite WAL for Observer rendering."""

    def __init__(self, store: Any, project_id: str = "work-lab") -> None:
        self.store = store
        self.project_id = project_id
        self._mode = "SNAPSHOT"

    def mode(self) -> str:
        return self._mode

    def set_mode(self, mode: str) -> None:
        if mode not in VALID_MODES:
            raise ValueError(f"invalid projection mode: {mode}")
        self._mode = mode

    def read_snapshot(self) -> dict[str, Any]:
        base = self.store.projection()
        projects = self.store.list_projects()
        tasks = self.store.list_tasks()
        usage = base.get("usage_summary", [])
        ci = base.get("ci_summary", [])
        by_status = base.get("tasks_by_status", {})

        project_rows = [
            {
                "projectId": row["project_id"],
                "displayName": row.get("display_name") or row["project_id"],
                "root": "<redacted-root>" if row.get("root_path") else None,
                "status": row.get("status", "UNKNOWN"),
                # Frontend renders on `state` (running/waiting/blocked/completed/...).
                # Map canonical status to the frontend state vocabulary.
                "state": _dashboard_project_state(row.get("status", "UNKNOWN")),
                "agentPlatform": None,
                "ciState": None,
            }
            for row in projects
        ]
        task_rows = [
            {
                "taskId": row["task_id"],
                "status": row["status"],
                "updatedAt": row.get("updated_at"),
                "leaseHolder": row.get("lease_holder"),
            }
            for row in tasks
        ]
        usage_rows = [
            {
                "provider": row.get("provider"),
                "model": row.get("model"),
                "samples": row.get("samples"),
                "tokens": row.get("tokens"),
            }
            for row in usage
        ]
        ci_rows = [
            {"status": row.get("status"), "conclusion": row.get("conclusion"), "runs": row.get("n")}
            for row in ci
        ]
        return {
            "schemaVersion": "work-lab/observer-canonical-projection/v1",
            "mode": self._mode,
            "projectId": self.project_id,
            "integrity": base.get("integrity", "unknown"),
            "tables": base.get("tables", {}),
            "projects": project_rows,
            "tasks": task_rows,
            "tasksByStatus": by_status,
            "usage": usage_rows,
            "ci": ci_rows,
            "telemetryEvents": base.get("telemetry_events", 0),
            "freshness": "STALE" if self._mode == "SNAPSHOT" else self._mode,
        }

    def to_dashboard(self) -> dict[str, Any]:
        """Map canonical facts onto the Observer dashboard projection shape."""
        snapshot = self.read_snapshot()
        by_status = snapshot["tasksByStatus"]
        counts = {
            "running": by_status.get("RUNNING", 0) + by_status.get("RUNNING_LOCAL", 0),
            "waiting": by_status.get("PENDING", 0) + by_status.get("WAITING_APPROVAL", 0),
            "blocked": by_status.get("BLOCKED", 0) + by_status.get("BLOCKED_POLICY", 0),
            "failed": by_status.get("FAILED", 0) + by_status.get("FAILED_RECOVERABLE", 0),
            "completed": by_status.get("COMPLETED", 0) + by_status.get("COMPLETED_LOCAL", 0),
            "unknown": by_status.get("UNKNOWN", 0),
        }
        total_tokens = sum(int(row.get("tokens") or 0) for row in snapshot["usage"]) if snapshot["usage"] else None
        input_tokens = sum(
            int(row.get("tokens") or 0) for row in snapshot["usage"]
        ) if snapshot["usage"] else None
        usage_quality = "EXACT_SOURCE" if snapshot["usage"] else "UNKNOWN"
        # usage series: one point per usage row (bucket = observed timestamp).
        usage_series = []
        for row in snapshot["usage"]:
            tokens = int(row.get("tokens") or 0)
            usage_series.append(
                {
                    "bucket": row.get("observed_at") or row.get("occurred_at"),
                    "inputTokens": tokens,
                    "outputTokens": tokens,
                }
            )
        return {
            "schemaVersion": "work-lab/observer-projection/v2",
            "mode": snapshot["mode"],
            "generatedAt": None,
            "freshness": {"state": snapshot["freshness"], "ageSeconds": None, "lastGoodAt": None},
            "summary": {
                "registeredProjects": len(snapshot["projects"]),
                "activeProjects": counts["running"] + counts["waiting"],
                "tasks": counts,
            },
            "projects": snapshot["projects"],
            "usage": {
                "totalTokens": total_tokens,
                "inputTokens": input_tokens,
                "outputTokens": input_tokens,
                "quality": {"dataQuality": usage_quality, "freshness": snapshot["freshness"]},
                "series": usage_series,
            },
            "ci": {
                "runs": snapshot["ci"],
                "quality": {"dataQuality": "EXACT_SOURCE" if snapshot["ci"] else "UNKNOWN", "freshness": snapshot["freshness"]},
            },
            "governance": {
                "rules": {"current": None, "drift": None, "quarantined": None, "conflicts": None, "stale": None},
                "skills": {"current": None, "drift": None, "quarantined": None, "conflicts": None, "stale": None},
            },
            "quality": {
                "integrity": snapshot["integrity"],
                "freshness": snapshot["freshness"],
                "telemetryEvents": snapshot["telemetryEvents"],
                "unknown": None,
                "malformed": None,
                "dropped": None,
                "duplicate": None,
            },
            "mutationSurface": {"externalMutation": False, "readOnly": True},
            "sourceRef": "workflow-canonical-sqlite-wal",
        }


def _dashboard_project_state(status: str) -> str:
    """Map canonical project status to the frontend `state` vocabulary."""
    mapping = {
        "ACTIVE": "running",
        "REGISTERED": "idle",
        "PENDING": "waiting",
        "WAITING_APPROVAL": "waiting",
        "BLOCKED": "blocked",
        "BLOCKED_POLICY": "blocked",
        "FAILED": "failed",
        "COMPLETED": "completed",
        "UNKNOWN": "unknown",
    }
    return mapping.get(status.upper(), "unknown")


def open_canonical_reader(path: Path, project_id: str = "work-lab") -> CanonicalProjectionReader:
    store = SQLiteReadOnlyStore(path)
    return CanonicalProjectionReader(store, project_id=project_id)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Read the canonical SQLite projection read-only")
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--mode", default="SNAPSHOT")
    args = parser.parse_args()
    reader = open_canonical_reader(args.store.resolve())
    reader.set_mode(args.mode)
    print(json.dumps(reader.to_dashboard(), ensure_ascii=False, indent=2))
