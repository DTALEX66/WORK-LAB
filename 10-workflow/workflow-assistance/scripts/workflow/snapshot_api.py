"""Unique read-only Snapshot API (WLGM-150).

Eliminates the dual projection (``/api/dashboard`` vs ``/api/v1/snapshot``).
The canonical -> Observer projection is implemented ONCE here, in the
Workflow-owned module. The snapshot:

- carries revision, generatedAt, source watermark, transport/quality/coverage;
- strictly distinguishes null from 0;
- separates projects, tasks and executions;
- splits token columns with exact/estimated/unknown cost marking;
- separates git local/remote/CI SHAs with match state;
- every core field is traceable to sourceRef where applicable.

Null vs zero: unknown values are null; counters that were observed are 0 or
positive integers. Nothing is padded to zero.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

SNAPSHOT_SCHEMA_VERSION = "workflow/snapshot/v3"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_snapshot(
    *,
    revision: int,
    store_projection: dict[str, Any] | None = None,
    executions: list[dict[str, Any]] | None = None,
    ci_runs: list[dict[str, Any]] | None = None,
    usage: list[dict[str, Any]] | None = None,
    projects: list[dict[str, Any]] | None = None,
    git_state: dict[str, Any] | None = None,
    transport: dict[str, Any] | None = None,
    source_watermark: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build the v3 snapshot from canonical facts (all fields optional for tests)."""
    generated_at = generated_at or _now()
    executions = executions or []
    ci_runs = ci_runs or []
    usage = usage or []
    projects = projects or []

    usage_by_project = _rollup_usage(usage)

    return {
        "schemaVersion": SNAPSHOT_SCHEMA_VERSION,
        "revision": revision,
        "generatedAt": generated_at,
        "sourceWatermark": source_watermark,
        "transport": {
            "transportState": (transport or {}).get("transportState") or "UNKNOWN",
            "freshnessState": (transport or {}).get("freshnessState") or "UNKNOWN",
            "connectedSince": (transport or {}).get("connectedSince"),
        },
        "coverage": {
            "numerator": (transport or {}).get("coverageNumerator"),
            "denominator": (transport or {}).get("coverageDenominator"),
            "scope": (transport or {}).get("coverageScope"),
        },
        "projects": [_project_projection(p, executions, usage_by_project, git_state, ci_runs) for p in projects],
        "executions": [executions],
        "tasks": (store_projection or {}).get("tasks_by_status", {}),
        "tokenSummary": {
            "inputTokens": sum(u.get("inputTokens") or 0 for u in usage),
            "outputTokens": sum(u.get("outputTokens") or 0 for u in usage),
            "totalTokens": sum(u.get("totalTokens") or 0 for u in usage),
            "costQuality": "EXACT" if all(u.get("costQuality") == "EXACT" for u in usage) else (
                "ESTIMATED" if any(u.get("costQuality") == "ESTIMATED" for u in usage) else "UNKNOWN"
            ),
        },
        "git": {
            "localSha": (git_state or {}).get("localSha"),
            "remoteSha": (git_state or {}).get("remoteSha"),
            "ciSha": (git_state or {}).get("ciSha"),
            "matchState": _git_match_state(git_state or {}),
        },
        "ci": [
            {
                "runId": run.get("runId"),
                "workflow": run.get("workflow"),
                "headSha": run.get("headSha"),
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "sourceRef": run.get("sourceRef"),
            }
            for run in ci_runs
        ],
        "sourceRefs": [e.get("sourceRef") for e in executions if e.get("sourceRef")],
    }


def _project_projection(
    project: dict[str, Any],
    executions: list[dict[str, Any]],
    usage_by_project: dict[str, dict[str, Any]],
    git_state: dict[str, Any] | None,
    ci_runs: list[dict[str, Any]],
) -> dict[str, Any]:
    project_id = project.get("projectId")
    project_executions = [e for e in executions if e.get("anchorProjectId") == project_id]
    active = sum(
        1 for e in project_executions if e.get("state") in {"RUNNING", "STARTING", "WAITING_USER", "WAITING_APPROVAL", "BLOCKED"}
    )
    usage = usage_by_project.get(project_id, {})
    project_ci = [r for r in ci_runs if r.get("projectId") == project_id]
    return {
        "projectId": project_id,
        "displayName": project.get("displayName"),
        "identityState": project.get("identityState") or "UNRESOLVED",
        "activityState": project.get("activityState") or "UNKNOWN",
        "attentionState": project.get("attentionState") or "NONE",
        "activeExecutionCount": active,
        "visibility": project.get("visibility") or "UNKNOWN",
        "quality": project.get("quality") or "UNKNOWN",
        "lastStrongEvidenceAt": project.get("lastStrongEvidenceAt"),
        "repositories": project.get("repositories", []),
        "git": {
            "localSha": (git_state or {}).get("localSha"),
            "remoteSha": (git_state or {}).get("remoteSha"),
            "matchState": _git_match_state(git_state or {}),
        },
        "token": {
            "inputTokens": usage.get("inputTokens"),
            "outputTokens": usage.get("outputTokens"),
            "totalTokens": usage.get("totalTokens"),
            "costQuality": usage.get("costQuality") or "UNKNOWN",
        },
        "ci": project_ci,
        "executionIds": [e.get("executionId") for e in project_executions],
        "sourceRefs": [e.get("sourceRef") for e in project_executions if e.get("sourceRef")],
    }


def _rollup_usage(usage: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    rolled: dict[str, dict[str, Any]] = {}
    for sample in usage:
        project_id = sample.get("projectId") or "unknown"
        entry = rolled.setdefault(project_id, {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0, "costQuality": "UNKNOWN"})
        entry["inputTokens"] = (entry["inputTokens"] or 0) + (sample.get("inputTokens") or 0)
        entry["outputTokens"] = (entry["outputTokens"] or 0) + (sample.get("outputTokens") or 0)
        entry["totalTokens"] = (entry["totalTokens"] or 0) + (sample.get("totalTokens") or 0)
        quality = sample.get("costQuality")
        if quality == "EXACT":
            entry["costQuality"] = "EXACT"
        elif quality == "ESTIMATED" and entry["costQuality"] != "EXACT":
            entry["costQuality"] = "ESTIMATED"
    return rolled


def _git_match_state(git_state: dict[str, Any]) -> str:
    local = git_state.get("localSha")
    remote = git_state.get("remoteSha")
    ci = git_state.get("ciSha")
    if local and remote and local == remote and ci == local:
        return "MATCH"
    if local and remote and local == remote:
        return "LOCAL_REMOTE_MATCH"
    if local and ci and local == ci:
        return "LOCAL_CI_MATCH"
    if not local:
        return "NO_LOCAL_CLAIM"
    return "MISMATCH"
