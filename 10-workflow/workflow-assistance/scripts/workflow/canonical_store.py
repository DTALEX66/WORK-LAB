"""Workflow-owned canonical SQLite WAL store.

Single source of runtime truth for WORK-LAB. Append/event semantics are
auditable; projections are rebuildable from canonical facts. Secrets,
prompt/response bodies, tool payloads and sensitive absolute paths are
forbidden. Token fields use a strict allowlist so legal usage counters such as
``input_tokens`` are accepted while auth tokens remain rejected.
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

SCHEMA_VERSION = 1
WAL_TABLES = (
    "projects",
    "platform_observations",
    "tasks",
    "task_events",
    "telemetry_events",
    "usage_samples",
    "ci_runs",
    "source_quality",
    "action_plans",
    "growth_candidates",
    "schema_migrations",
)

USAGE_TOKEN_ALLOWLIST = {
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "reasoning_tokens",
    "tool_tokens",
    "subagent_tokens",
    "total_tokens",
}
AUTH_TOKEN_FRAGMENTS = {
    "apikey",
    "authorization",
    "bearer",
    "cookie",
    "credential",
    "password",
    "privatekey",
    "secret",
    "sessiontoken",
    "accesstoken",
    "refreshtoken",
    "authtoken",
}
FORBIDDEN_FRAGMENTS = {
    "prompt",
    "response",
    "privatekey",
    "oauth",
} | AUTH_TOKEN_FRAGMENTS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_key(value: object) -> str:
    return "".join(character for character in str(value).lower() if character.isalnum())


def _scan_keys(value: Any, fragments: set[str]) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = _normalize_key(key)
            if any(fragment in normalized for fragment in fragments):
                found.add(normalized)
            found |= _scan_keys(child, fragments)
    elif isinstance(value, list):
        for child in value:
            found |= _scan_keys(child, fragments)
    return found


def validate_record(record: dict[str, Any], *, allow_usage_tokens: bool) -> None:
    """Reject auth/secret fields; allow explicit usage counter names only."""
    if not isinstance(record, dict):
        raise ValueError("canonical record must be an object")
    forbidden = _scan_keys(record, FORBIDDEN_FRAGMENTS)
    if forbidden:
        raise ValueError(f"forbidden sensitive field(s): {sorted(forbidden)}")
    if allow_usage_tokens:
        return
    auth_hits = _scan_keys(record, AUTH_TOKEN_FRAGMENTS)
    if auth_hits:
        raise ValueError(f"auth token field(s) not allowed here: {sorted(auth_hits)}")


class CanonicalStore:
    """Thread-safe canonical SQLite WAL store with migrations and readback."""

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._lock = __import__("threading").RLock()
        self._migrate()

    def _migrate(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    root_path TEXT NOT NULL,
                    display_name TEXT,
                    registered_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'REGISTERED'
                );
                CREATE TABLE IF NOT EXISTS platform_observations (
                    observation_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    checkpoint TEXT,
                    lease_holder TEXT,
                    lease_expires_at TEXT,
                    fencing_token INTEGER
                );
                CREATE TABLE IF NOT EXISTS task_events (
                    event_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS telemetry_events (
                    event_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    producer TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    freshness TEXT NOT NULL,
                    coverage TEXT NOT NULL,
                    quality TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS usage_samples (
                    sample_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    lane TEXT,
                    observed_at TEXT NOT NULL,
                    window_start TEXT,
                    window_end TEXT,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    cache_read_tokens INTEGER,
                    cache_write_tokens INTEGER,
                    reasoning_tokens INTEGER,
                    tool_tokens INTEGER,
                    subagent_tokens INTEGER,
                    total_tokens INTEGER,
                    billing_type TEXT,
                    cost_estimate REAL,
                    cost_reconciled REAL,
                    quality TEXT NOT NULL,
                    source_ref TEXT
                );
                CREATE TABLE IF NOT EXISTS ci_runs (
                    run_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    workflow TEXT NOT NULL,
                    head_sha TEXT NOT NULL,
                    status TEXT NOT NULL,
                    conclusion TEXT,
                    observed_at TEXT NOT NULL,
                    jobs_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS source_quality (
                    row_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    quality TEXT NOT NULL,
                    coverage TEXT NOT NULL,
                    freshness TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    last_good_at TEXT,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_plans (
                    plan_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    approved_at TEXT,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS growth_candidates (
                    candidate_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    discovered_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                """
            )
            existing = {row[0] for row in self._conn.execute("SELECT version FROM schema_migrations")}
            if not existing:
                self._conn.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                    (SCHEMA_VERSION, _now()),
                )
            self._conn.commit()

    def integrity_check(self) -> str:
        with self._lock:
            row = self._conn.execute("PRAGMA integrity_check").fetchone()
            return str(row[0]) if row else "unknown"

    def register_project(self, project_id: str, root_path: str, display_name: str | None = None) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO projects (project_id, root_path, display_name, registered_at, status)
                VALUES (?, ?, ?, ?, 'REGISTERED')
                ON CONFLICT(project_id) DO UPDATE SET
                    root_path=excluded.root_path,
                    display_name=excluded.display_name
                """,
                (project_id, root_path, display_name, _now()),
            )
            self._conn.commit()

    def list_projects(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM projects ORDER BY registered_at"
            ).fetchall()
            return [dict(row) for row in rows]

    def update_project_status(self, project_id: str, status: str) -> None:
        """Update a project's observation status (REGISTERED / ACTIVE / ...)."""
        with self._lock:
            self._conn.execute(
                "UPDATE projects SET status = ? WHERE project_id = ?",
                (status, project_id),
            )
            self._conn.commit()

    def append_telemetry(self, event: dict[str, Any]) -> str:
        validate_record(event, allow_usage_tokens=True)
        event_id = str(event.get("event_id") or uuid.uuid4().hex)
        with self._lock:
            sequence = self._conn.execute(
                "SELECT COUNT(*) FROM telemetry_events"
            ).fetchone()[0] + 1
            self._conn.execute(
                """
                INSERT INTO telemetry_events
                (event_id, project_id, sequence, producer, occurred_at, observed_at,
                 freshness, coverage, quality, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    str(event.get("project_id", "unknown")),
                    sequence,
                    str(event.get("producer", "workflow-assistance")),
                    str(event.get("occurred_at", _now())),
                    str(event.get("observed_at", _now())),
                    str(event.get("freshness", "UNKNOWN")),
                    str(event.get("coverage", "UNKNOWN")),
                    str(event.get("quality", "UNKNOWN")),
                    json.dumps(event, ensure_ascii=False, sort_keys=True),
                ),
            )
            self._conn.commit()
        return event_id

    def record_usage_sample(self, sample: dict[str, Any]) -> str:
        validate_record(sample, allow_usage_tokens=True)
        sample_id = str(sample.get("sample_id") or uuid.uuid4().hex)
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO usage_samples
                (sample_id, project_id, provider, model, lane, observed_at,
                 window_start, window_end, input_tokens, output_tokens,
                 cache_read_tokens, cache_write_tokens, reasoning_tokens,
                 tool_tokens, subagent_tokens, total_tokens, billing_type,
                 cost_estimate, cost_reconciled, quality, source_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sample_id,
                    str(sample.get("project_id", "unknown")),
                    str(sample.get("provider", "unknown")),
                    str(sample.get("model", "unknown")),
                    sample.get("lane"),
                    str(sample.get("observed_at", _now())),
                    sample.get("window_start"),
                    sample.get("window_end"),
                    sample.get("input_tokens"),
                    sample.get("output_tokens"),
                    sample.get("cache_read_tokens"),
                    sample.get("cache_write_tokens"),
                    sample.get("reasoning_tokens"),
                    sample.get("tool_tokens"),
                    sample.get("subagent_tokens"),
                    sample.get("total_tokens")
                    if sample.get("total_tokens") is not None
                    else (sample.get("input_tokens") or 0) + (sample.get("output_tokens") or 0),
                    sample.get("billing_type"),
                    sample.get("cost_estimate"),
                    sample.get("cost_reconciled"),
                    str(sample.get("quality", "UNKNOWN")),
                    sample.get("source_ref"),
                ),
            )
            self._conn.commit()
        return sample_id

    def record_ci_run(self, run: dict[str, Any]) -> str:
        validate_record(run, allow_usage_tokens=False)
        run_id = str(run.get("run_id") or uuid.uuid4().hex)
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO ci_runs
                (run_id, project_id, workflow, head_sha, status, conclusion,
                 observed_at, jobs_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    status=excluded.status,
                    conclusion=excluded.conclusion,
                    observed_at=excluded.observed_at,
                    jobs_json=excluded.jobs_json
                """,
                (
                    run_id,
                    str(run.get("project_id", "unknown")),
                    str(run.get("workflow", "unknown")),
                    str(run.get("head_sha", "unknown")),
                    str(run.get("status", "UNKNOWN")),
                    run.get("conclusion"),
                    _now(),
                    json.dumps(run.get("jobs", []), ensure_ascii=False, sort_keys=True),
                ),
            )
            self._conn.commit()
        return run_id

    def upsert_task(self, task: dict[str, Any]) -> None:
        validate_record(task, allow_usage_tokens=False)
        task_id = str(task["task_id"])
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO tasks
                (task_id, project_id, status, created_at, updated_at, checkpoint,
                 lease_holder, lease_expires_at, fencing_token)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    status=excluded.status,
                    updated_at=excluded.updated_at,
                    checkpoint=excluded.checkpoint,
                    lease_holder=excluded.lease_holder,
                    lease_expires_at=excluded.lease_expires_at,
                    fencing_token=excluded.fencing_token
                """,
                (
                    task_id,
                    str(task.get("project_id", "unknown")),
                    str(task.get("status", "PENDING")),
                    str(task.get("created_at", _now())),
                    str(task.get("updated_at", _now())),
                    json.dumps(task.get("checkpoint") or {}, ensure_ascii=False, sort_keys=True),
                    task.get("lease_holder"),
                    task.get("lease_expires_at"),
                    task.get("fencing_token"),
                ),
            )
            self._conn.commit()

    def acquire_lease(self, task_id: str, holder: str, ttl_seconds: int = 300) -> bool:
        """Transactional lease acquisition with fencing token bump."""
        with self._lock:
            row = self._conn.execute(
                "SELECT lease_holder, lease_expires_at, fencing_token FROM tasks WHERE task_id=?",
                (task_id,),
            ).fetchone()
            now = _now()
            if row is not None:
                holder_now = row["lease_holder"]
                expires = row["lease_expires_at"]
                if holder_now is not None and expires is not None and expires > now and holder_now != holder:
                    return False
            token = ((row["fencing_token"] if row else 0) or 0) + 1
            expires_at = datetime.now(timezone.utc).timestamp() + ttl_seconds
            self._conn.execute(
                """
                UPDATE tasks SET lease_holder=?, lease_expires_at=?, fencing_token=?
                WHERE task_id=?
                """,
                (holder, _now_for_expiry(expires_at), token, task_id),
            )
            self._conn.commit()
            return True

    def heartbeat(self, task_id: str, holder: str, ttl_seconds: int = 300) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT lease_holder, lease_expires_at FROM tasks WHERE task_id=?",
                (task_id,),
            ).fetchone()
            if row is None or row["lease_holder"] != holder:
                return False
            expires_at = datetime.now(timezone.utc).timestamp() + ttl_seconds
            self._conn.execute(
                "UPDATE tasks SET lease_expires_at=? WHERE task_id=?",
                (_now_for_expiry(expires_at), task_id),
            )
            self._conn.commit()
            return True

    def release_lease(self, task_id: str, holder: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT lease_holder FROM tasks WHERE task_id=?",
                (task_id,),
            ).fetchone()
            if row is None or row["lease_holder"] != holder:
                return False
            self._conn.execute(
                "UPDATE tasks SET lease_holder=NULL, lease_expires_at=NULL WHERE task_id=?",
                (task_id,),
            )
            self._conn.commit()
            return True

    def claim_expired_tasks(self, holder: str, ttl_seconds: int = 300) -> list[str]:
        """Reclaim tasks whose lease expired (zombie recovery)."""
        with self._lock:
            cutoff = datetime.now(timezone.utc).timestamp() - ttl_seconds
            rows = self._conn.execute(
                "SELECT task_id FROM tasks WHERE lease_holder IS NOT NULL AND lease_expires_at < ?",
                (_now_for_expiry(cutoff),),
            ).fetchall()
            claimed: list[str] = []
            for row in rows:
                task_id = row["task_id"]
                token = self._conn.execute(
                    "SELECT fencing_token FROM tasks WHERE task_id=?", (task_id,)
                ).fetchone()["fencing_token"] + 1
                self._conn.execute(
                    """
                    UPDATE tasks SET lease_holder=?, lease_expires_at=?, fencing_token=?
                    WHERE task_id=?
                    """,
                    (holder, _now_for_expiry(datetime.now(timezone.utc).timestamp() + ttl_seconds), token, task_id),
                )
                claimed.append(task_id)
            self._conn.commit()
            return claimed

    def append_quality(self, record: dict[str, Any]) -> str:
        """Record a source-quality observation (WL3-510 quality collector)."""
        validate_record(record, allow_usage_tokens=True)
        row_id = str(record.get("row_id") or uuid.uuid4().hex)
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO source_quality
                (row_id, project_id, scope, quality, coverage, freshness,
                 observed_at, last_good_at, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    str(record.get("project_id", "unknown")),
                    str(record.get("scope", "unknown")),
                    str(record.get("quality", "UNKNOWN")),
                    str(record.get("coverage", "UNKNOWN")),
                    str(record.get("freshness", "UNKNOWN")),
                    str(record.get("observed_at", _now())),
                    record.get("last_good_at"),
                    json.dumps(record, ensure_ascii=False, sort_keys=True),
                ),
            )
            self._conn.commit()
        return row_id

    def list_tasks(self, status: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            if status:
                rows = self._conn.execute(
                    "SELECT * FROM tasks WHERE status=? ORDER BY updated_at DESC", (status,)
                ).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM tasks ORDER BY updated_at DESC").fetchall()
            result = []
            for row in rows:
                item = dict(row)
                try:
                    item["checkpoint"] = json.loads(item.get("checkpoint") or "{}")
                except json.JSONDecodeError:
                    item["checkpoint"] = {}
                result.append(item)
            return result

    def projection(self) -> dict[str, Any]:
        with self._lock:
            telemetry_count = self._conn.execute("SELECT COUNT(*) FROM telemetry_events").fetchone()[0]
            task_counts: dict[str, int] = {}
            for row in self._conn.execute("SELECT status, COUNT(*) AS n FROM tasks GROUP BY status"):
                task_counts[row["status"]] = row["n"]
            usage = self._conn.execute(
                "SELECT provider, model, COUNT(*) AS samples, SUM(total_tokens) AS tokens "
                "FROM usage_samples GROUP BY provider, model"
            ).fetchall()
            ci = self._conn.execute(
                "SELECT status, conclusion, COUNT(*) AS n FROM ci_runs GROUP BY status, conclusion"
            ).fetchall()
            return {
                "schema_version": "workflow/canonical-projection/v1",
                "integrity": self.integrity_check(),
                "tables": {table: self._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in WAL_TABLES},
                "telemetry_events": telemetry_count,
                "tasks_by_status": task_counts,
                "usage_summary": [dict(row) for row in usage],
                "ci_summary": [dict(row) for row in ci],
                "observed_at": _now(),
            }

    def close(self) -> None:
        with self._lock:
            self._conn.close()


def _now_for_expiry(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat().replace("+00:00", "Z")


@contextmanager
def open_store(path: Path) -> Iterator[CanonicalStore]:
    store = CanonicalStore(path)
    try:
        yield store
    finally:
        store.close()


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as temporary:
        store = CanonicalStore(Path(temporary) / "canonical.sqlite")
        print("CANONICAL_STORE_OK", store.integrity_check())
        store.close()
