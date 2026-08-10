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
from pathlib import Path
from typing import Any

try:
    from canonical_store import CanonicalStore  # type: ignore
except ImportError:  # pragma: no cover - path fallback for CI layouts
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2] / "scripts" / "workflow"))
    from canonical_store import CanonicalStore  # type: ignore

VALID_MODES = {"LIVE", "STALE", "SNAPSHOT", "FIXTURE", "OFFLINE", "UNKNOWN"}


class CanonicalProjectionReader:
    """Read-only facade over the canonical SQLite WAL for Observer rendering."""

    def __init__(self, store: CanonicalStore, project_id: str = "work-lab") -> None:
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
        total_tokens = sum(int(row.get("tokens") or 0) for row in snapshot["usage"])
        usage_quality = "EXACT_SOURCE" if snapshot["usage"] else "UNKNOWN"
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
                "inputTokens": None,
                "outputTokens": None,
                "quality": {"dataQuality": usage_quality, "freshness": snapshot["freshness"]},
                "series": [],
            },
            "ci": {
                "runs": snapshot["ci"],
                "quality": {"dataQuality": "EXACT_SOURCE" if snapshot["ci"] else "UNKNOWN", "freshness": snapshot["freshness"]},
            },
            "governance": {
                "rules": {"current": 0, "drift": 0, "quarantined": 0, "conflicts": 0, "stale": 0},
                "skills": {"current": 0, "drift": 0, "quarantined": 0, "conflicts": 0, "stale": 0},
            },
            "quality": {
                "integrity": snapshot["integrity"],
                "freshness": snapshot["freshness"],
                "telemetryEvents": snapshot["telemetryEvents"],
                "unknown": 0,
                "malformed": 0,
                "dropped": 0,
                "duplicate": 0,
            },
            "mutationSurface": {"externalMutation": False, "readOnly": True},
            "sourceRef": "workflow-canonical-sqlite-wal",
        }


def open_canonical_reader(path: Path, project_id: str = "work-lab") -> CanonicalProjectionReader:
    store = CanonicalStore(path)
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
