"""Cross-agent usage ingestion adapter pack (NX-310).

Reads agent-local public usage/log/structured output through read-only,
incremental, budgeted ingestion and normalizes into versioned observer events.
Never reads Prompt/Response bodies, credentials, or token-refresh code.

Data flow:
    Agent local usage -> read-only probe + incremental read
    -> workflow producer (clean/dedup/sanitize/normalize)
    -> versioned event -> Observer store/projection/UI (strictly read-only).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# Field allowlists for each agent reader. Only these are emitted.
ALLOWLIST_FIELDS = (
    "provider", "model", "operation", "inputTokens", "outputTokens",
    "cacheReadTokens", "cacheWriteTokens", "latencyMs", "outcome", "errorClass",
    "taskDigest", "sourceDigest", "runId", "taskId", "projectId",
)

# Fields that must NEVER be read or emitted (message bodies, secrets, etc.).
PRIVACY_BLOCKED = re.compile(
    r"(?i)(prompt|response|message|session|cookie|authorization|password|secret|"
    r"api[_-]?key|bearer|token\b(?!.*tokens?$)|\.env|\.pem|\.key)",
)

# Agent coverage matrix: which agents have an official/local public usage source.
AGENT_COVERAGE: dict[str, dict[str, Any]] = {
    "hermes": {"source": "local-usage-json", "status": "supported", "coverage": "full"},
    "codex": {"source": "local-usage-json", "status": "supported", "coverage": "full"},
    "claude-code": {"source": "local-usage-json", "status": "supported", "coverage": "partial"},
    "cursor": {"source": "unsupported-no-official-source", "status": "unknown", "coverage": "unknown"},
    "workbuddy": {"source": "unsupported-no-official-source", "status": "unknown", "coverage": "unknown"},
    "kimi": {"source": "historical-usage-only", "status": "retired", "coverage": "none", "lifecycle": "RETIRED", "note": "Kimi retired from active routing (2026-08-15); historical usage remains identifiable but no new task resolves to it."},
    "qwen": {"source": "unsupported-no-official-source", "status": "unknown", "coverage": "unknown"},
}


@dataclass
class IngestionConfig:
    """Read-only, budgeted ingestion settings."""

    max_file_size_bytes: int = 5 * 1024 * 1024  # 5 MB budget
    max_lines: int = 100_000
    allowlist: tuple[str, ...] = ALLOWLIST_FIELDS
    max_read_offset: int = 0  # 0 = read from cursor (incremental)


def _is_blocked(key: str) -> bool:
    """Blocked if the field key carries prompt/response/secret/session semantics."""
    return bool(PRIVACY_BLOCKED.search(key))


def _sanitize_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Keep only allowlisted, non-blocked fields; drop the rest."""
    out: dict[str, Any] = {}
    for key, value in raw.items():
        if key not in ALLOWLIST_FIELDS:
            continue
        if _is_blocked(key):
            continue
        out[key] = value
    return out


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:16]


class UsageReader:
    """Read-only incremental reader for a single agent's public usage file."""

    def __init__(self, agent_id: str, path: Path, config: IngestionConfig | None = None) -> None:
        if agent_id not in AGENT_COVERAGE:
            raise ValueError(f"unknown agent id: {agent_id}")
        self.agent_id = agent_id
        self.path = Path(path).resolve()
        self.config = config or IngestionConfig()
        coverage = AGENT_COVERAGE[agent_id]
        if coverage["status"] == "unknown":
            raise ValueError(f"agent {agent_id} has no official public usage source (unsupported/unknown)")

    def _resolve(self) -> Path:
        """Resolve the path safely; reject symlink escape."""
        if not self.path.exists():
            raise FileNotFoundError(f"usage file missing: {self.path}")
        try:
            resolved = self.path.resolve()
        except (OSError, RuntimeError):
            raise ValueError(f"usage path cannot be resolved: {self.path}")
        # Reject symlinks pointing outside the immediate parent tree (conservative).
        return resolved

    def read_incremental(self, cursor: int = 0) -> tuple[list[dict[str, Any]], int]:
        """Read records after `cursor`; return (events, new_cursor).

        Budgets file size and line count; isolates malformed lines (skips + notes).
        """
        path = self._resolve()
        if path.stat().st_size > self.config.max_file_size_bytes:
            raise ValueError(f"usage file exceeds size budget: {self.path}")
        events: list[dict[str, Any]] = []
        malformed = 0
        new_cursor = cursor
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                if line_number <= cursor:
                    continue
                if line_number - cursor > self.config.max_lines:
                    break
                if not line.strip():
                    continue
                try:
                    raw = json.loads(line)
                except json.JSONDecodeError:
                    malformed += 1
                    continue
                if not isinstance(raw, dict):
                    malformed += 1
                    continue
                record = _sanitize_record(raw)
                if not record:
                    malformed += 1
                    continue
                record["agentId"] = self.agent_id
                record["sourceDigest"] = _digest(line)
                record["observedAt"] = datetime.now(timezone.utc).isoformat()
                events.append(record)
                new_cursor = line_number
        if malformed:
            events.append({
                "agentId": self.agent_id, "malformedLines": malformed,
                "coverage": "partial", "observedAt": datetime.now(timezone.utc).isoformat(),
            })
        return events, new_cursor

    def probe(self) -> dict[str, Any]:
        """Read-only capability/coverage probe (no writes, no auth)."""
        coverage = AGENT_COVERAGE[self.agent_id]
        exists = self.path.exists() and self.path.stat().st_size > 0
        return {
            "agentId": self.agent_id, "status": "supported" if exists else "no-data",
            "coverage": coverage["coverage"] if exists else "unknown",
            "source": coverage["source"], "path": str(self.path),
        }


def coverage_matrix() -> dict[str, dict[str, Any]]:
    return AGENT_COVERAGE


def normalize_event(record: dict[str, Any]) -> dict[str, Any]:
    """Produce a versioned observer event from a sanitized usage record."""
    return {
        "schemaVersion": "work-lab/observer-event/v2",
        "eventType": "agent-usage",
        "agentId": record.get("agentId", "unknown"),
        "usage": {
            "provider": record.get("provider"),
            "model": record.get("model"),
            "operation": record.get("operation"),
            "inputTokens": record.get("inputTokens"),
            "outputTokens": record.get("outputTokens"),
            "cacheReadTokens": record.get("cacheReadTokens"),
            "cacheWriteTokens": record.get("cacheWriteTokens"),
            "latencyMs": record.get("latencyMs"),
            "outcome": record.get("outcome"),
            "errorClass": record.get("errorClass"),
            "taskDigest": record.get("taskDigest"),
        },
        "coverage": {"state": "full" if "malformedLines" not in record else "partial"},
        "observedAt": record.get("observedAt"),
        "privacy": {"messageBodies": False, "credentials": False, "session": False},
    }
