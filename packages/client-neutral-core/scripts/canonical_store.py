"""Workflow-owned canonical SQLite WAL store.

Single source of runtime truth for WORK-LAB. Append/event semantics are
auditable; projections are rebuildable from canonical facts. Secrets,
prompt/response bodies, tool payloads and sensitive absolute paths are
forbidden. Token fields use a strict allowlist so legal usage counters such as
``input_tokens`` are accepted while auth tokens remain rejected.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping

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

# Tables a retention ceiling may touch: the append-only event ledgers. Identity/registry tables and the
# migration history are excluded by derivation, so a table added to WAL_TABLES is retention-exempt until
# someone states which category it belongs to -- an unlisted table cannot be pruned by accident.
RETENTION_EXEMPT_TABLES = ("schema_migrations", "projects", "tasks")
RETAINABLE_TABLES = tuple(table for table in WAL_TABLES if table not in RETENTION_EXEMPT_TABLES)

# Preference order for the "newest timestamp" witness; the column is resolved per table from
# PRAGMA table_info, so a table that renames or drops one is not silently left unwatched.
_NEWEST_COLUMNS = (
    "updated_at",
    "occurred_at",
    "observed_at",
    "generated_at",
    "last_run_at",
    "discovered_at",
    "approved_at",
    "registered_at",
    "created_at",
    "applied_at",
    "started_at",
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
    # Names were always screened; values were not. A provider token carried under an allowed field
    # (``provider``, ``note``, ``sourceRef``) used to be written to the canonical store, and the
    # ingest path is exactly where a foreign file's content becomes a project fact.
    from artifact_flow_policy import secret_value_paths  # noqa: PLC0415 - shared predicate, no cycle
    leaked = secret_value_paths(record)
    if leaked:
        raise ValueError(f"sensitive value(s) at: {sorted(leaked)}")
    if allow_usage_tokens:
        return
    auth_hits = _scan_keys(record, AUTH_TOKEN_FRAGMENTS)
    if auth_hits:
        raise ValueError(f"auth token field(s) not allowed here: {sorted(auth_hits)}")


class CanonicalStore:
    """Thread-safe canonical SQLite WAL store with migrations and readback."""

    def __init__(self, path: Path, *, readonly: bool = False) -> None:
        self.readonly = readonly
        self.path = path.resolve()
        if readonly:
            # Observer capability-level read-only: no directory creation, no
            # schema migration, no WAL pragma write, SQLite URI mode=ro. Any
            # write statement on this connection fails closed with
            # OperationalError (attempt to write a readonly database).
            if not self.path.is_file():
                raise FileNotFoundError(f"canonical store missing: {self.path}")
            self._conn = sqlite3.connect(
                f"file:{self.path}?mode=ro", uri=True, check_same_thread=False
            )
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._lock = __import__("threading").RLock()
            return
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
            # WLGM-140: back up the pre-v2 database ONCE, before the v2 migration
            # runs, so an interrupted migration is recoverable. Idempotent: only
            # when version 2 is not yet recorded.
            if 2 not in existing:
                try:
                    backup = self.path.with_name(self.path.name + f".bak-v2-{_now_slug()}")
                    import shutil

                    # WAL mode: checkpoint into the main db file so the backup
                    # copy actually contains the tables/data.
                    self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    shutil.copy2(self.path, backup)
                except (OSError, shutil.Error):
                    # Backup is best-effort; the atomic transaction below is the
                    # real interruption guard. Never fail open without backup.
                    backup = None
                if backup is None:
                    raise RuntimeError("cannot create pre-v2 backup; migration refused")
            # WLGM-140 incremental tables (idempotent). BEGIN/COMMIT live INSIDE
            # the script because executescript implicitly commits any pending
            # transaction first; an interruption rolls the whole v2 migration
            # back atomically.
            self._conn.executescript(
                """
                BEGIN;
                CREATE TABLE IF NOT EXISTS project_definitions (
                    project_id TEXT PRIMARY KEY,
                    definition_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS project_root_bindings (
                    binding_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    root TEXT NOT NULL,
                    repository_id TEXT,
                    worktree_id TEXT,
                    kind TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS repository_identities (
                    repository_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    remote_identity TEXT,
                    role TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS worktree_identities (
                    worktree_id TEXT PRIMARY KEY,
                    repository_id TEXT NOT NULL,
                    root TEXT NOT NULL,
                    kind TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS agent_instances (
                    agent_instance_id TEXT PRIMARY KEY,
                    agent TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    payload TEXT
                );
                CREATE TABLE IF NOT EXISTS agent_capabilities (
                    adapter_id TEXT PRIMARY KEY,
                    installed INTEGER NOT NULL,
                    capabilities_json TEXT NOT NULL,
                    evidence_level TEXT NOT NULL,
                    observed_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    agent TEXT NOT NULL,
                    anchor_project_id TEXT,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS execution_instances (
                    execution_id TEXT PRIMARY KEY,
                    agent TEXT NOT NULL,
                    session_id TEXT,
                    anchor_project_id TEXT,
                    repository_id TEXT,
                    worktree_id TEXT,
                    working_area TEXT,
                    state TEXT NOT NULL,
                    state_quality TEXT NOT NULL,
                    started_at TEXT,
                    last_heartbeat_at TEXT,
                    transport_state TEXT,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS execution_evidence (
                    event_id TEXT PRIMARY KEY,
                    execution_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    evidence_level TEXT NOT NULL,
                    quality TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    dedupe_key TEXT NOT NULL UNIQUE,
                    source_ref TEXT,
                    payload TEXT
                );
                CREATE TABLE IF NOT EXISTS execution_heartbeats (
                    event_id TEXT PRIMARY KEY,
                    execution_id TEXT NOT NULL,
                    observed_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS collector_health (
                    name TEXT PRIMARY KEY,
                    total_runs INTEGER NOT NULL DEFAULT 0,
                    last_run_at TEXT,
                    last_success_at TEXT,
                    consecutive_failures INTEGER NOT NULL DEFAULT 0,
                    circuit_open_until REAL,
                    dropped_count INTEGER NOT NULL DEFAULT 0,
                    refused_rows INTEGER NOT NULL DEFAULT 0,
                    delivered_rows INTEGER NOT NULL DEFAULT 0,
                    last_refusal_reason TEXT,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS project_activity_projection (
                    project_id TEXT PRIMARY KEY,
                    projection_json TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    generated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS projection_revisions (
                    revision INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    projection_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sse_state (
                    key TEXT PRIMARY KEY,
                    value INTEGER NOT NULL
                );
                COMMIT;
                """
            )
            if 2 not in existing:
                self._conn.execute(
                    "INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES (2, ?)",
                    (_now(),),
                )
            if 3 not in existing:
                self._conn.execute(
                    "INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES (3, ?)",
                    (_now(),),
                )
            # Version 4: a refused ingest row gets its own named columns. `dropped_count` already means
            # "events this collector dropped from its bounded queue", and putting ingest refusals in it
            # would make one number answer two different questions with two different remedies.
            health_columns = {row[1] for row in self._conn.execute("PRAGMA table_info(collector_health)")}
            for column, declaration in (("refused_rows", "INTEGER NOT NULL DEFAULT 0"),
                                         ("delivered_rows", "INTEGER NOT NULL DEFAULT 0"),
                                         ("last_refusal_reason", "TEXT")):
                if column not in health_columns:
                    self._conn.execute(
                        f"ALTER TABLE collector_health ADD COLUMN {column} {declaration}")
            if 4 not in existing:
                self._conn.execute(
                    "INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES (4, ?)",
                    (_now(),),
                )
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

    def newest_changes(self) -> dict[str, list[object]]:
        """Per tracked table: row count, highest rowid and newest timestamp.

        The sidecar's live gate compared counts and status tallies, so an in-place update -- a lease
        acquired, a checkpoint advanced -- moved nothing it could see, and the Observer kept rendering
        the previous state until some row happened to be inserted. Measured: writing a checkpoint,
        lease holder and fencing token onto an existing task left the fingerprint byte-identical.

        The timestamp column is read out of the table rather than restated here, so a schema change
        cannot silently leave the witness blind, and the highest rowid still catches a mutation whose
        author forgot to bump a timestamp.
        """
        with self._lock:
            witness: dict[str, list[object]] = {}
            for table in WAL_TABLES:
                stamp = self._newest_column(table)
                select = "COUNT(*), COALESCE(MAX(rowid), 0)"
                select += f", MAX({stamp})" if stamp else ", NULL"
                row = self._conn.execute(f"SELECT {select} FROM {table}").fetchone()
                witness[table] = [row[0], row[1], row[2]]
            # timestamps alone are not a content witness: a lease renewal can land in the same second and
            # a fencing token can bump without any text column changing, so the mutable hot table is
            # witnessed by what it actually holds
            tasks = self._conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(fencing_token),0), "
                "COALESCE(SUM(LENGTH(COALESCE(checkpoint,''))),0), "
                "COALESCE(SUM(LENGTH(COALESCE(lease_holder,''))),0), "
                "COALESCE(MAX(updated_at),''), COALESCE(MAX(lease_expires_at),'') FROM tasks"
            ).fetchone()
            witness["tasks_state"] = [tasks[0], tasks[1], tasks[2], tasks[3], tasks[4], tasks[5]]
            return witness

    def _newest_column(self, table: str) -> str | None:
        """The timestamp column a table is ordered by, read out of the table itself.

        Shared by the fingerprint witness and by retention: two lists of "which column is newest" would drift,
        and a prune that ordered by the wrong column would delete the newest rows while reporting success.
        """
        columns = [row[1] for row in self._conn.execute(f"PRAGMA table_info({table})").fetchall()]
        return next((name for name in _NEWEST_COLUMNS if name in columns), None)

    def disk_footprint(self) -> dict[str, int]:
        """Bytes the store actually occupies, read from SQLite's own page math plus the WAL sidecar files.

        Reported separately from row counts because "bounded" is a statement about bytes: a ceiling in rows does
        not tell the owner what the file costs, and a checkpoint can reclaim the WAL without changing the main
        database at all.
        """
        with self._lock:
            page_size = int(self._conn.execute("PRAGMA page_size").fetchone()[0])
            page_count = int(self._conn.execute("PRAGMA page_count").fetchone()[0])
        # Two different numbers, both honest and both labelled: `PRAGMA page_count` is the *logical* size and
        # in WAL mode it counts pages the main file has not absorbed yet, while stat() is the bytes the owner's
        # file explorer would show. Conflating them makes a reclaim look like it happened when only the WAL
        # moved, so the report carries each and names which one totals into `totalBytes`.
        report = {"pageSizeBytes": page_size, "pageCount": page_count,
                  "logicalDatabaseBytes": page_size * page_count,
                  "databaseFileBytes": self.path.stat().st_size if self.path.is_file() else 0,
                  "walBytes": 0, "shmBytes": 0}
        for key, suffix in (("walBytes", "-wal"), ("shmBytes", "-shm")):
            sidecar = Path(f"{self.path}{suffix}")
            if sidecar.is_file():
                report[key] = sidecar.stat().st_size
        report["totalBytes"] = (report["databaseFileBytes"] + report["walBytes"] + report["shmBytes"])
        return report

    def enforce_retention(self, limits: Mapping[str, int], *, allow_prune: bool) -> dict[str, Any]:
        """Cap the append-only event tables; every other table is refused by name.

        Without ``allow_prune`` this is a report, not an action: ``wouldDelete`` carries the numbers a prune
        *would* produce and nothing is removed, so an operator can see the cost of a ceiling before granting it.
        """
        unknown = sorted(set(limits) - set(RETAINABLE_TABLES))
        if unknown:
            raise ValueError(f"RETENTION_TABLE_NOT_PERMITTED {unknown}; retainable set is "
                             f"{sorted(RETAINABLE_TABLES)}")
        bad = sorted(table for table, rows in limits.items() if not isinstance(rows, int) or rows < 1)
        if bad:
            raise ValueError(f"RETENTION_CEILING_INVALID {bad}: a ceiling below 1 would empty a table")
        before = self.disk_footprint()
        report: dict[str, Any] = {"allowPrune": allow_prune, "tables": {}, "before": before}
        removed_total = 0
        with self._lock:
            for table, ceiling in sorted(limits.items()):
                stamp = self._newest_column(table)
                order = f"{stamp} DESC, rowid DESC" if stamp else "rowid DESC"
                count = int(self._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                excess = max(0, count - ceiling)
                kept_sql = f"SELECT rowid FROM {table} ORDER BY {order} LIMIT ?"
                entry: dict[str, Any] = {"rowsBefore": count, "ceiling": ceiling,
                                         "newestColumn": stamp, "orderBy": order,
                                         "wouldDelete": excess, "deleted": 0, "rowsAfter": count}
                if excess and allow_prune:
                    self._conn.execute(
                        f"DELETE FROM {table} WHERE rowid NOT IN ({kept_sql})", (ceiling,))
                    entry["deleted"] = self._conn.execute("SELECT changes()").fetchone()[0]
                    entry["rowsAfter"] = int(
                        self._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                    removed_total += int(entry["deleted"])
                report["tables"][table] = entry
            if removed_total:
                self._conn.commit()
                self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        report["deletedTotal"] = removed_total
        report["after"] = self.disk_footprint()
        report["bytesReclaimed"] = before["totalBytes"] - report["after"]["totalBytes"]
        return report

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
            # MAX, not COUNT: a COUNT-derived sequence restarts colliding the moment retention prunes, and a
            # cursor value that repeats is worse than one that gaps. Nothing reads this column today, which is
            # exactly why the rule has to be stated here rather than discovered by a consumer.
            sequence = self._conn.execute(
                "SELECT COALESCE(MAX(sequence), 0) + 1 FROM telemetry_events"
            ).fetchone()[0]
            self._conn.execute(
                """
                INSERT OR IGNORE INTO telemetry_events
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
                ON CONFLICT(sample_id) DO UPDATE SET
                    project_id=excluded.project_id,
                    provider=excluded.provider,
                    model=excluded.model,
                    lane=excluded.lane,
                    observed_at=excluded.observed_at,
                    window_start=excluded.window_start,
                    window_end=excluded.window_end,
                    input_tokens=excluded.input_tokens,
                    output_tokens=excluded.output_tokens,
                    cache_read_tokens=excluded.cache_read_tokens,
                    cache_write_tokens=excluded.cache_write_tokens,
                    reasoning_tokens=excluded.reasoning_tokens,
                    tool_tokens=excluded.tool_tokens,
                    subagent_tokens=excluded.subagent_tokens,
                    total_tokens=excluded.total_tokens,
                    billing_type=excluded.billing_type,
                    cost_estimate=excluded.cost_estimate,
                    cost_reconciled=excluded.cost_reconciled,
                    quality=excluded.quality,
                    source_ref=excluded.source_ref
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


    def record_platform_observations(self, records: list[dict[str, Any]]) -> None:
        """Record project->platform observations (Observer cross-project view)."""
        with self._lock:
            for rec in records:
                project_id = str(rec.get("project_id") or "")
                platform = str(rec.get("platform") or "")
                if not project_id or not platform:
                    continue
                # A fresh UUID made every collector tick an append-only row,
                # causing platform_observations to grow forever and making
                # query order the accidental source of truth.  The current
                # platform observation is a keyed fact; history belongs in
                # the canonical event/quality ledger, not this projection.
                observation_id = f"platform-{project_id}"
                self._conn.execute(
                    """
                    INSERT INTO platform_observations
                    (observation_id, project_id, platform, observed_at, payload)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(observation_id) DO UPDATE SET
                        platform=excluded.platform,
                        observed_at=excluded.observed_at,
                        payload=excluded.payload
                    """,
                    (
                        observation_id,
                        project_id,
                        platform,
                        datetime.now(timezone.utc).isoformat(),
                        rec.get("payload", "{}"),
                    ),
                )
            self._conn.commit()

    def query_platform_observations(self, project_id: str | None = None) -> list[dict[str, Any]]:
        """Latest platform observation per project (or filtered by project_id)."""
        sql = "SELECT project_id, platform, observed_at, payload FROM platform_observations"
        params: tuple = ()
        if project_id:
            sql += " WHERE project_id = ?"
            params = (project_id,)
        sql += " ORDER BY observed_at DESC"
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        latest: dict[str, dict[str, Any]] = {}
        for r in rows:
            pid = str(r[0] or "")
            if pid and pid not in latest:
                latest[pid] = {
                    "project_id": pid,
                    "platform": r[1],
                    "observed_at": r[2],
                    "payload": r[3],
                }
        return list(latest.values())

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

    def insert_task_if_absent(self, task: dict[str, Any]) -> bool:
        """Create a task, or report that the identity already exists -- without overwriting theirs.

        `upsert_task` resolves a conflict by taking the incoming row wholesale, including
        lease_holder / lease_expires_at / fencing_token. A writer that has no lease to claim (a control-plane
        create) therefore wipes a live holder's lease and can send the fencing token backwards, which
        destroys the exact property the fence exists to provide. Identity creation and identity conflict
        are different outcomes; this one says which happened, in a single transaction, and touches nothing
        that already exists.
        """
        validate_record(task, allow_usage_tokens=False)
        task_id = str(task["task_id"])
        with self._lock:
            cursor = self._conn.execute(
                """
                INSERT INTO tasks
                (task_id, project_id, status, created_at, updated_at, checkpoint,
                 lease_holder, lease_expires_at, fencing_token)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO NOTHING
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
            return cursor.rowcount == 1

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
                UPDATE tasks SET lease_holder=?, lease_expires_at=?, fencing_token=?, updated_at=?
                WHERE task_id=?
                """,
                (holder, _now_for_expiry(expires_at), token, now, task_id),
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
                "UPDATE tasks SET lease_expires_at=?, updated_at=? WHERE task_id=?",
                (_now_for_expiry(expires_at), _now(), task_id),
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
                "UPDATE tasks SET lease_holder=NULL, lease_expires_at=NULL, updated_at=? WHERE task_id=?",
                (_now(), task_id),
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
                ON CONFLICT(row_id) DO UPDATE SET
                    project_id=excluded.project_id,
                    scope=excluded.scope,
                    quality=excluded.quality,
                    coverage=excluded.coverage,
                    freshness=excluded.freshness,
                    observed_at=excluded.observed_at,
                    last_good_at=excluded.last_good_at,
                    payload=excluded.payload
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
                raw = item.get("checkpoint")
                # An identity over exactly what is stored, computed here where the bytes live: the read
                # surface must be able to say "this checkpoint exists and this is which one" without the
                # projection ever holding the text. A checkpoint that will not parse still gets a digest,
                # because "unreadable" is a different claim from "absent".
                item["checkpointDigest"] = (
                    hashlib.sha256(raw.encode("utf-8")).hexdigest()
                    if isinstance(raw, str) and raw else None)
                if raw in (None, ""):
                    item["checkpoint"] = None
                    item["checkpointParseState"] = "ABSENT"
                else:
                    try:
                        item["checkpoint"] = json.loads(raw)
                        item["checkpointParseState"] = "PARSED"
                    except (json.JSONDecodeError, TypeError):
                        item["checkpoint"] = None
                        item["checkpointParseState"] = "UNPARSEABLE"
                result.append(item)
            return result

    def projection(self) -> dict[str, Any]:
        with self._lock:
            telemetry_count = self._conn.execute("SELECT COUNT(*) FROM telemetry_events").fetchone()[0]
            task_counts: dict[str, int] = {}
            for row in self._conn.execute("SELECT status, COUNT(*) AS n FROM tasks GROUP BY status"):
                task_counts[row["status"]] = row["n"]
            usage = self._conn.execute(
                "SELECT provider, model, COUNT(*) AS samples, "
                "SUM(input_tokens) AS input_tokens, SUM(output_tokens) AS output_tokens, "
                "SUM(total_tokens) AS tokens, MAX(observed_at) AS observed_at "
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

    def upsert_project_definition(self, project_id: str, definition: dict[str, Any]) -> None:
        validate_record(definition, allow_usage_tokens=False)
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO project_definitions (project_id, definition_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    definition_json=excluded.definition_json,
                    updated_at=excluded.updated_at
                """,
                (project_id, json.dumps(definition, ensure_ascii=False, sort_keys=True), _now()),
            )
            self._conn.commit()

    def get_project_definition(self, project_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT definition_json FROM project_definitions WHERE project_id=?", (project_id,)
            ).fetchone()
        if not row:
            return None
        try:
            return json.loads(row["definition_json"])
        except json.JSONDecodeError:
            return None

    def upsert_execution_instance(self, status: dict[str, Any]) -> None:
        validate_record(status, allow_usage_tokens=False)
        execution_id = str(status["executionId"])
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO execution_instances
                (execution_id, agent, session_id, anchor_project_id, repository_id,
                 worktree_id, working_area, state, state_quality, started_at,
                 last_heartbeat_at, transport_state, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(execution_id) DO UPDATE SET
                    agent=excluded.agent,
                    session_id=excluded.session_id,
                    anchor_project_id=excluded.anchor_project_id,
                    repository_id=excluded.repository_id,
                    worktree_id=excluded.worktree_id,
                    working_area=excluded.working_area,
                    state=excluded.state,
                    state_quality=excluded.state_quality,
                    last_heartbeat_at=excluded.last_heartbeat_at,
                    transport_state=excluded.transport_state,
                    updated_at=excluded.updated_at
                """,
                (
                    execution_id,
                    str(status.get("agent", "unknown")),
                    status.get("sessionId"),
                    status.get("anchorProjectId"),
                    status.get("repositoryId"),
                    status.get("worktreeId"),
                    status.get("workingArea"),
                    str(status.get("state", "UNKNOWN")),
                    str(status.get("stateQuality", "UNKNOWN")),
                    status.get("startedAt"),
                    status.get("lastHeartbeatAt"),
                    status.get("transportState"),
                    _now(),
                ),
            )
            self._conn.commit()

    def append_execution_evidence(self, record: dict[str, Any]) -> str:
        """Append one validated execution evidence record; dedupe key enforced."""
        validate_record(record, allow_usage_tokens=False)
        event_id = str(record.get("eventId") or uuid.uuid4().hex)
        dedupe_key = str(record.get("dedupeKey") or event_id)
        with self._lock:
            try:
                self._conn.execute(
                    """
                    INSERT INTO execution_evidence
                    (event_id, execution_id, event_type, evidence_level, quality,
                     occurred_at, observed_at, dedupe_key, source_ref, payload)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        str(record.get("executionId", "unknown")),
                        str(record.get("eventType", "unknown")),
                        str(record.get("evidenceLevel", "C")),
                        str(record.get("quality", "UNKNOWN")),
                        str(record.get("occurredAt", _now())),
                        str(record.get("observedAt", _now())),
                        dedupe_key,
                        record.get("sourceRef"),
                        json.dumps(record, ensure_ascii=False, sort_keys=True),
                    ),
                )
                self._conn.commit()
                return event_id
            except sqlite3.IntegrityError:
                # Duplicate dedupe key: replayed event is a no-op (never double-counts).
                existing = self._conn.execute(
                    "SELECT event_id FROM execution_evidence WHERE dedupe_key=?", (dedupe_key,)
                ).fetchone()
                return existing["event_id"] if existing else event_id

    # A health row has more than one author: the scheduler speaks about queue drops, the worker about
    # ingest refusals. Writing a whole row from a writer that only observed some of it used to reset the
    # other writer's fields to `record.get(..., 0)` defaults, so an unwritten field silently became "zero"
    # — which is the same lie as padding an unknown. Only the keys the caller actually named get written.
    _COLLECTOR_HEALTH_COLUMNS = {
        "totalRuns": ("total_runs", int),
        "lastRunAt": ("last_run_at", str),
        "lastSuccessAt": ("last_success_at", str),
        "consecutiveFailures": ("consecutive_failures", int),
        "circuitOpenUntil": ("circuit_open_until", float),
        "droppedCount": ("dropped_count", int),
        "refusedRows": ("refused_rows", int),
        "deliveredRows": ("delivered_rows", int),
        "lastRefusalReason": ("last_refusal_reason", str),
    }

    def upsert_collector_health(self, record: dict[str, Any]) -> None:
        """Write only the fields this caller named. An absent key is left alone; an explicit ``None``
        clears the column, because a closed circuit has to be storable."""
        name = str(record.get("name", "unknown"))
        columns: list[str] = ["name"]
        values: list[Any] = [name]
        for key, (column, caster) in self._COLLECTOR_HEALTH_COLUMNS.items():
            if key not in record:
                continue
            value = record[key]
            columns.append(column)
            values.append(None if value is None else caster(value))
        assignments = ", ".join(f"{column}=excluded.{column}" for column in columns[1:])
        placeholders = ", ".join("?" for _ in columns)
        with self._lock:
            self._conn.execute(
                f"""
                INSERT INTO collector_health ({", ".join(columns)}, updated_at)
                VALUES ({placeholders}, ?)
                ON CONFLICT(name) DO UPDATE SET
                    {assignments}{", updated_at=excluded.updated_at" if assignments else ""}
                """,
                (*values, _now()),
            )
            self._conn.commit()

    def save_projection(self, project_id: str, projection: dict[str, Any]) -> int:
        """Persist the latest projection and append a revision (WLGM-150 base)."""
        with self._lock:
            row = self._conn.execute(
                "SELECT revision FROM project_activity_projection WHERE project_id=?", (project_id,)
            ).fetchone()
            revision = (row["revision"] if row else 0) + 1
            self._conn.execute(
                """
                INSERT INTO project_activity_projection (project_id, projection_json, revision, generated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    projection_json=excluded.projection_json,
                    revision=excluded.revision,
                    generated_at=excluded.generated_at
                """,
                (project_id, json.dumps(projection, ensure_ascii=False, sort_keys=True), revision, _now()),
            )
            self._conn.execute(
                """
                INSERT INTO projection_revisions (project_id, generated_at, projection_json)
                VALUES (?, ?, ?)
                """,
                (project_id, _now(), json.dumps(projection, ensure_ascii=False, sort_keys=True)),
            )
            self._conn.commit()
            return revision

    def list_executions(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM execution_instances ORDER BY updated_at DESC").fetchall()
            return [dict(row) for row in rows]

    # ---- WLGM composition root read helpers (pure SELECT, additive) ----

    def list_usage_samples(self) -> list[dict[str, Any]]:
        """All usage_samples rows for the v3 snapshot usage projection."""
        with self._lock:
            rows = self._conn.execute("SELECT * FROM usage_samples ORDER BY observed_at DESC").fetchall()
            return [dict(row) for row in rows]

    def list_ci_runs(self) -> list[dict[str, Any]]:
        """All ci_runs rows for the v3 snapshot ci projection."""
        with self._lock:
            rows = self._conn.execute("SELECT * FROM ci_runs ORDER BY observed_at DESC").fetchall()
            return [dict(row) for row in rows]

    def list_collector_health(self) -> list[dict[str, Any]]:
        """All collector_health rows (coverage numerator/denominator source)."""
        with self._lock:
            rows = self._conn.execute("SELECT * FROM collector_health ORDER BY updated_at DESC").fetchall()
            return [dict(row) for row in rows]

    def list_source_quality(self) -> list[dict[str, Any]]:
        """All source_quality rows with payload JSON parsed (git/source scope)."""
        with self._lock:
            rows = self._conn.execute("SELECT * FROM source_quality ORDER BY observed_at DESC").fetchall()
            result = []
            for row in rows:
                item = dict(row)
                try:
                    item["payload"] = json.loads(item.get("payload") or "{}")
                except (json.JSONDecodeError, TypeError):
                    item["payload"] = {}
                result.append(item)
            return result

    def seed_revision(self) -> int:
        """Persisted SSE revision seed: sse_state.last_revision (fallback:
        MAX(revision) over projection_revisions for pre-v3 databases)."""
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM sse_state WHERE key = 'last_revision'"
            ).fetchone()
            if row is not None:
                return int(row[0] or 0)
            row = self._conn.execute("SELECT COALESCE(MAX(revision), 0) FROM projection_revisions").fetchone()
            return int(row[0] or 0)

    def record_revision(self, revision: int) -> None:
        """Persist the latest SSE revision so a restarted sidecar seeds its hub
        from here, keeping Last-Event-ID cursors monotonic across restarts."""
        with self._lock:
            self._conn.execute(
                "INSERT INTO sse_state (key, value) VALUES ('last_revision', ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (revision,),
            )
            self._conn.commit()

    def max_watermark(self) -> str | None:
        """Newest canonical observation across every surfaced collector table."""
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT MAX(observed_at) FROM (
                    SELECT observed_at FROM telemetry_events
                    UNION ALL SELECT observed_at FROM usage_samples
                    UNION ALL SELECT observed_at FROM ci_runs
                    UNION ALL SELECT observed_at FROM source_quality
                    UNION ALL SELECT last_run_at AS observed_at FROM collector_health
                )
                """
            ).fetchone()
            return rows[0] if rows and rows[0] else None

    def close(self) -> None:
        with self._lock:
            # R4/T11: WAL mode must checkpoint(TRUNCATE) before close so -wal/-shm
            # files merge and release; otherwise tmp db dir cannot be removed
            # (WinError 5 on Windows) and hermetic tests leak tmp dirs.
            try:
                self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            except Exception:
                pass
            self._conn.close()


def _now_for_expiry(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _now_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def rollback_v2_backup(path: Path) -> Path | None:
    """WLGM-140: restore the pre-v2 backup (created on first v2 migration).

    Returns the restored backup path, or None when no backup exists. The caller
    must close any open connection to ``path`` before calling. Never follows
    symlinks: the backup is a plain sibling file of ``path``.
    """
    resolved = path.resolve()
    candidates = sorted(resolved.parent.glob(resolved.name + ".bak-v2-*"))
    if not candidates:
        return None
    backup = candidates[-1]
    import shutil

    shutil.copy2(backup, resolved)
    return backup


@contextmanager
def open_store(path: Path) -> Iterator[CanonicalStore]:
    store = CanonicalStore(path)
    try:
        yield store
    finally:
        store.close()


if __name__ == "__main__":
    import project_temp

    with project_temp.fixture_root(prefix='canonical-store-selftest-') as temporary:
        store = CanonicalStore(Path(temporary) / "canonical.sqlite")
        print("CANONICAL_STORE_OK", store.integrity_check())
        store.close()
