from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable
import json

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas/observer-event.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)
SENSITIVE_KEYS = {"api_key", "apikey", "authorization", "password", "secret", "token", "cookie", "prompt", "response"}


class ObserverInputError(ValueError):
    """Raised when an observed event is invalid or privacy-unsafe."""


def _keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return {str(k).lower() for k in value} | set().union(*(_keys(v) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(_keys(v) for v in value)) if value else set()
    return set()


def validate_event(event: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise ObserverInputError("event must be an object")
    sensitive = sorted(_keys(event) & SENSITIVE_KEYS)
    if sensitive:
        raise ObserverInputError(f"sensitive keys rejected: {', '.join(sensitive)}")
    errors = sorted(VALIDATOR.iter_errors(event), key=lambda error: list(error.path))
    if errors:
        raise ObserverInputError(errors[0].message)
    return deepcopy(event)


def append_events(log: list[dict[str, Any]], events: Iterable[dict[str, Any]], *, max_events: int = 256) -> int:
    """Append only validated observer-owned events; never mutates a source ledger."""
    if max_events < 1:
        raise ValueError("max_events must be positive")
    existing = {event["eventId"] for event in log}
    accepted = 0
    for raw in events:
        event = validate_event(raw)
        if event["eventId"] in existing:
            continue
        if len(log) >= max_events:
            raise ObserverInputError("observer event budget exceeded")
        log.append(event)
        existing.add(event["eventId"])
        accepted += 1
    return accepted


class IncrementalCursor:
    def __init__(self, *, max_batch: int = 128) -> None:
        if max_batch < 1:
            raise ValueError("max_batch must be positive")
        self.max_batch = max_batch
        self.cursor = ""
        self.rotation = 0
        self.seen: set[str] = set()

    def ingest(self, events: Iterable[dict[str, Any]], *, next_cursor: str) -> list[dict[str, Any]]:
        batch = list(events)
        if len(batch) > self.max_batch:
            raise ObserverInputError("collector batch budget exceeded")
        accepted: list[dict[str, Any]] = []
        for raw in batch:
            event = validate_event(raw)
            if event["eventId"] in self.seen:
                continue
            self.seen.add(event["eventId"])
            accepted.append(event)
        if next_cursor < self.cursor:
            self.rotation += 1
        self.cursor = next_cursor
        return accepted


def project_tasks(events: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Rebuild a read-only task view from event history."""
    tasks: dict[str, dict[str, Any]] = {}
    for event in events:
        task_id = event.get("taskId")
        if not task_id:
            continue
        current = tasks.setdefault(task_id, {"taskId": task_id, "events": 0})
        current["events"] += 1
        current["lastEventType"] = event["eventType"]
        current["quality"] = event["quality"]
        current["coverage"] = event.get("coverage", "unknown")
        current["observedAt"] = event["observedAt"]
    return deepcopy(tasks)


def quality_summary(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    total = 0
    for event in events:
        total += 1
        quality = event["quality"]
        counts[quality] = counts.get(quality, 0) + 1
    return {"quality": "source-exact" if total and counts.get("source-exact") == total else "partial" if total else "unknown", "coverage": "full" if total else "unknown", "counts": counts}


def mutation_surface() -> dict[str, Any]:
    return {"externalMutation": False, "ledgerMutation": False, "approvalMutation": False, "gitControl": False, "allowedWrites": ["observer-owned-events", "observer-owned-projections", "observer-owned-reports"]}
