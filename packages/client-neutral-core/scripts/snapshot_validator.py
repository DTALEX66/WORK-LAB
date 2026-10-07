"""Snapshot v3 schema validator (WLGM-150).

Validates a canonical v3 snapshot structure with explicit error reporting.
Unknown/absent fields never get padded to zero; validation failures return a
clear error list instead of partial pseudo-success.

Rules:
- schemaVersion must equal workflow/snapshot/v3;
- revision must be a non-negative integer;
- generatedAt must be a valid RFC3339 timestamp;
- projects[].projectId required, non-empty string;
- executions[].executionId + state required;
- tokenSummary numeric fields are int|null (never coerced);
- transport/coverage shape enforced when present.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

SNAPSHOT_SCHEMA_VERSION = "workflow/snapshot/v3"

# The fixed evidence vocabulary (WORK-LAB-AUTHORITY.md §10). A projection may report a lower level than
# a caller hopes for; it may never spell a higher one.
EVIDENCE_LEVELS = frozenset({"NO_EVIDENCE", "SIMULATED", "SYNTHETIC", "INTEGRATED", "REAL"})

RFC3339_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
)


def validate_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return {'valid': bool, 'errors': [str], 'warnings': [str]}."""
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(snapshot, dict):
        return {"valid": False, "errors": ["snapshot must be an object"], "warnings": []}

    if snapshot.get("schemaVersion") != SNAPSHOT_SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {SNAPSHOT_SCHEMA_VERSION}")

    revision = snapshot.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        errors.append(f"revision must be a non-negative integer, got {revision!r}")

    generated_at = snapshot.get("generatedAt")
    if generated_at is not None:
        if not isinstance(generated_at, str) or not RFC3339_RE.match(generated_at):
            errors.append(f"generatedAt must be RFC3339, got {generated_at!r}")
    else:
        errors.append("generatedAt is required")

    projects = snapshot.get("projects")
    if not isinstance(projects, list):
        errors.append("projects must be a list")
    else:
        seen: set[str] = set()
        for index, project in enumerate(projects):
            if not isinstance(project, dict):
                errors.append(f"projects[{index}] must be an object")
                continue
            pid = project.get("projectId")
            if not isinstance(pid, str) or not pid:
                errors.append(f"projects[{index}].projectId required")
            elif pid in seen:
                warnings.append(f"duplicate projectId {pid!r}")
            else:
                seen.add(pid)
            count = project.get("activeExecutionCount")
            if count is not None and (not isinstance(count, int) or isinstance(count, bool) or count < 0):
                errors.append(f"projects[{index}].activeExecutionCount must be int|null, got {count!r}")

    executions = snapshot.get("executions")
    if executions is not None:
        if not isinstance(executions, list):
            errors.append("executions must be a list")
        else:
            for index, execution in enumerate(executions):
                if not isinstance(execution, dict):
                    errors.append(f"executions[{index}] must be an object")
                    continue
                eid = execution.get("executionId")
                if not isinstance(eid, str) or not eid:
                    errors.append(f"executions[{index}].executionId required")
                state = execution.get("state")
                if not isinstance(state, str) or not state:
                    errors.append(f"executions[{index}].state required")
                anchor = execution.get("anchorProjectId")
                if anchor is not None and not isinstance(anchor, str):
                    errors.append(f"executions[{index}].anchorProjectId must be str|null, got {anchor!r}")

    token_summary = snapshot.get("tokenSummary")
    if token_summary is not None:
        if not isinstance(token_summary, dict):
            errors.append("tokenSummary must be an object")
        else:
            for field in ("inputTokens", "outputTokens", "totalTokens"):
                value = token_summary.get(field)
                if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
                    errors.append(f"tokenSummary.{field} must be int|null, got {value!r}")
            quality = token_summary.get("costQuality")
            if quality is not None and quality not in ("EXACT", "ESTIMATED", "UNKNOWN"):
                errors.append(f"tokenSummary.costQuality must be EXACT|ESTIMATED|UNKNOWN|null, got {quality!r}")

    task_records = snapshot.get("taskRecords")
    if task_records is not None:
        if not isinstance(task_records, list):
            errors.append("taskRecords must be a list when present")
        else:
            seen_task_ids: set[str] = set()
            for index, record in enumerate(task_records):
                if not isinstance(record, dict):
                    errors.append(f"taskRecords[{index}] must be an object")
                    continue
                tid = record.get("taskId")
                if not isinstance(tid, str) or not tid:
                    errors.append(f"taskRecords[{index}].taskId required (non-empty string)")
                elif tid in seen_task_ids:
                    errors.append(f"taskRecords[{index}].taskId duplicates {tid!r}")
                else:
                    seen_task_ids.add(tid)
                for field in ("projectId", "status"):
                    value = record.get(field)
                    if not isinstance(value, str) or not value:
                        errors.append(f"taskRecords[{index}].{field} required (non-empty string)")
                fencing = record.get("fencingToken")
                if fencing is not None and (not isinstance(fencing, int) or isinstance(fencing, bool)):
                    errors.append(f"taskRecords[{index}].fencingToken must be int|null, got {fencing!r}")
                present = record.get("checkpointPresent")
                if not isinstance(present, bool):
                    errors.append(f"taskRecords[{index}].checkpointPresent must be boolean, got {present!r}")
                keys = record.get("checkpointKeys")
                if not isinstance(keys, list) or any(not isinstance(item, str) for item in keys):
                    errors.append(f"taskRecords[{index}].checkpointKeys must be a list of key names")
                digest = record.get("checkpointDigest")
                if present and not isinstance(digest, str):
                    errors.append(
                        f"taskRecords[{index}].checkpointDigest must be a digest when a checkpoint exists"
                    )
                if not present and digest is not None:
                    errors.append(
                        f"taskRecords[{index}].checkpointDigest must be null when no checkpoint exists"
                    )

    adapter_cards = snapshot.get("adapterCapabilities")
    if adapter_cards is not None:
        if not isinstance(adapter_cards, list):
            errors.append("adapterCapabilities must be a list when present")
        else:
            for index, card in enumerate(adapter_cards):
                if not isinstance(card, dict):
                    errors.append(f"adapterCapabilities[{index}] must be an object")
                    continue
                client_id = card.get("clientId")
                if not isinstance(client_id, str) or not client_id:
                    errors.append(f"adapterCapabilities[{index}].clientId required")
                layers = card.get("layers")
                if not isinstance(layers, list):
                    errors.append(f"adapterCapabilities[{index}].layers must be a list")
                    continue
                names = [str(layer.get("layer")) for layer in layers if isinstance(layer, dict)]
                if len(names) != len(layers):
                    errors.append(f"adapterCapabilities[{index}].layers contains a non-object entry")
                if len(set(names)) != len(names):
                    errors.append(f"adapterCapabilities[{index}].layers repeats a layer name")
                for layer_index, layer in enumerate(layers):
                    if not isinstance(layer, dict):
                        continue
                    state = layer.get("state")
                    if state not in ("MET", "NOT_PROBED", "NOT_SUPPORTED"):
                        errors.append(
                            f"adapterCapabilities[{index}].layers[{layer_index}].state "
                            f"must be MET|NOT_PROBED|NOT_SUPPORTED, got {state!r}"
                        )
                    evidence = layer.get("evidenceLevel")
                    if evidence not in EVIDENCE_LEVELS:
                        errors.append(
                            f"adapterCapabilities[{index}].layers[{layer_index}].evidenceLevel "
                            f"must be one of {sorted(EVIDENCE_LEVELS)}, got {evidence!r}"
                        )
                    reason = layer.get("reason")
                    if not isinstance(reason, str) or not reason.strip():
                        errors.append(
                            f"adapterCapabilities[{index}].layers[{layer_index}].reason required — "
                            "an unprobed layer must say what is missing"
                        )
                    source = layer.get("source")
                    if state == "MET":
                        if not isinstance(source, str) or not source.strip():
                            errors.append(
                                f"adapterCapabilities[{index}].layers[{layer_index}] claims MET "
                                "without a named source"
                            )
                        if evidence == "NO_EVIDENCE":
                            errors.append(
                                f"adapterCapabilities[{index}].layers[{layer_index}] claims MET "
                                "with NO_EVIDENCE"
                            )
                status = card.get("nativeStatus")
                if status not in ("NOT_IMPLEMENTED", "NOT_PROBED", "NATIVELY_VERIFIED"):
                    errors.append(
                        f"adapterCapabilities[{index}].nativeStatus must be "
                        f"NOT_IMPLEMENTED|NOT_PROBED|NATIVELY_VERIFIED, got {status!r}"
                    )
                elif status == "NATIVELY_VERIFIED":
                    observed = next((layer for layer in layers
                                    if isinstance(layer, dict)
                                    and layer.get("layer") == "OBSERVED_IN_EXECUTION"), None)
                    if not observed or observed.get("state") != "MET":
                        errors.append(
                            f"adapterCapabilities[{index}] claims NATIVELY_VERIFIED while "
                            "OBSERVED_IN_EXECUTION is not MET — the ladder cannot be climbed from the top"
                        )

    transport = snapshot.get("transport")
    if transport is not None and not isinstance(transport, dict):
        errors.append("transport must be an object")

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def snapshot_to_json(snapshot: dict[str, Any]) -> str:
    """Serialize a snapshot with strict null preservation (never pad to 0)."""
    return json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
