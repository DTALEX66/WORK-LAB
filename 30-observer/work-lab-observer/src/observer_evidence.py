from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

from observer_runtime import ObserverInputError, validate_event


SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "cookie",
    "password",
    "prompt",
    "response",
    "secret",
    "token",
}
WORKFLOW_SCHEMA = "workflow/evidence-envelope/v1"
EVENT_SCHEMA = "work-lab/observer-event/v1"


def _keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return {str(key).lower() for key in value} | set().union(*(_keys(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(_keys(item) for item in value)) if value else set()
    return set()


def _digest(value: Any) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _reject_sensitive(value: Any) -> None:
    sensitive = sorted(_keys(value) & SENSITIVE_KEYS)
    if sensitive:
        raise ObserverInputError(f"sensitive evidence keys rejected: {', '.join(sensitive)}")


def _event(*, event_id: str, task_id: str, event_type: str, source_id: str, source_digest: str, quality: str, evidence_refs: list[str]) -> dict[str, Any]:
    event = {
        "eventId": event_id,
        "schemaVersion": EVENT_SCHEMA,
        "eventType": event_type,
        "sourceModule": "workflow-assistance" if event_type.startswith("evidence.") else "open-design",
        "sourceId": source_id,
        "taskId": task_id,
        "observedAt": "source-bound",
        "contentDigest": source_digest,
        "coverage": "full",
        "quality": quality,
        "evidenceRefs": evidence_refs,
    }
    return validate_event(event)


def workflow_evidence_events(envelopes: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for envelope in envelopes:
        if not isinstance(envelope, dict) or envelope.get("schema_version") != WORKFLOW_SCHEMA:
            raise ObserverInputError("unsupported workflow evidence envelope")
        _reject_sensitive(envelope)
        required = {"evidence_id", "task_id", "state", "level", "source", "artifacts", "redaction"}
        if not required.issubset(envelope):
            raise ObserverInputError("workflow evidence envelope is incomplete")
        if envelope["state"] not in {"NOT_RUN", "PASS", "FAIL", "BLOCKED", "UNVERIFIED", "SKIPPED_OPTIONAL"}:
            raise ObserverInputError("unsupported workflow evidence state")
        if envelope["redaction"].get("secrets_stored") is not False:
            raise ObserverInputError("workflow evidence must declare secrets_stored=false")
        refs = [item["path"] for item in envelope["artifacts"] if isinstance(item, dict) and isinstance(item.get("path"), str)]
        events.append(
            _event(
                event_id=f"workflow-evidence:{envelope['evidence_id']}",
                task_id=envelope["task_id"],
                event_type=f"evidence.{envelope['state'].lower()}",
                source_id=envelope["evidence_id"],
                source_digest=_digest(envelope),
                quality="source-exact" if envelope["state"] == "PASS" else "partial",
                evidence_refs=refs,
            )
        )
    return events


def open_design_benchmark_event(registry: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(registry, dict) or registry.get("schema_version") != "open-design/benchmark-registry/v1":
        raise ObserverInputError("unsupported Open Design benchmark registry")
    _reject_sensitive(registry)
    benchmarks = registry.get("benchmarks")
    repeatability = registry.get("repeatability")
    if not isinstance(benchmarks, list) or not benchmarks or not isinstance(repeatability, dict):
        raise ObserverInputError("Open Design benchmark registry is incomplete")
    if repeatability.get("human_calibration_required_for_promotion") is not True:
        raise ObserverInputError("benchmark promotion must require human calibration")
    refs = [entry["id"] for entry in benchmarks if isinstance(entry, dict) and isinstance(entry.get("id"), str)]
    return _event(
        event_id=f"open-design-benchmark:{_digest(registry)[:16]}",
        task_id="OD-BENCHMARK-REGISTRY",
        event_type="benchmark.registry",
        source_id="benchmark-registry",
        source_digest=_digest(registry),
        quality="partial",
        evidence_refs=refs,
    )
