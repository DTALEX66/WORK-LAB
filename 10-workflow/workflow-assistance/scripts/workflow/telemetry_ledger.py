"""Workflow-owned append-only telemetry ledger.

Only normalized metadata and numeric usage are accepted. Observer consumes a
projection; it never owns or mutates this ledger.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SENSITIVE = {"token", "password", "secret", "cookie", "authorization", "prompt", "response", "api_key", "apikey"}


def _keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return {str(k).lower() for k in value} | set().union(*(_keys(v) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(_keys(v) for v in value)) if value else set()
    return set()


class TelemetryLedger:
    def __init__(self, path: Path) -> None:
        self.path = path.resolve()

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("schema_version") != "workflow/telemetry-ledger/v1":
                raise ValueError("unsupported telemetry schema")
            if _keys(row) & SENSITIVE:
                raise ValueError("sensitive telemetry key")
            rows.append(row)
        return rows

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(event, dict) or not event.get("event_id"):
            raise ValueError("event_id is required")
        if _keys(event) & SENSITIVE:
            raise ValueError("sensitive telemetry key")
        existing = self.read()
        if any(row["event_id"] == event["event_id"] for row in existing):
            raise ValueError("duplicate event_id")
        record = {
            "schema_version": "workflow/telemetry-ledger/v1",
            "sequence": len(existing) + 1,
            "project_id": "unknown",
            "sourceRef": "unknown",
            "producer": "workflow-assistance",
            "occurredAt": event.get("occurred_at", "unknown"),
            "observedAt": event.get("observed_at", "unknown"),
            "freshness": "UNKNOWN",
            "coverage": "UNKNOWN",
            "quality": "UNKNOWN",
            "dedupe_key": event["event_id"],
            "payload_digest": "REDACTED",
            "redaction_state": "REDACTED",
            **event,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        return record

    def projection(self) -> dict[str, Any]:
        rows = self.read()
        return {"schema_version": "workflow/telemetry-projection/v1", "event_count": len(rows), "last_sequence": len(rows), "events": [{"event_id": r["event_id"], "occurred_at": r.get("occurred_at"), "source": r.get("source"), "outcome": r.get("outcome")} for r in rows]}
