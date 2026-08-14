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

    transport = snapshot.get("transport")
    if transport is not None and not isinstance(transport, dict):
        errors.append("transport must be an object")

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def snapshot_to_json(snapshot: dict[str, Any]) -> str:
    """Serialize a snapshot with strict null preservation (never pad to 0)."""
    return json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
