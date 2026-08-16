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
    governance: dict[str, Any] | None = None,
    workspace: dict[str, Any] | None = None,
    source_watermark: str | None = None,
    generated_at: str | None = None,
    platform_map: dict[str, str] | None = None,
    git_map: dict[str, dict[str, Any]] | None = None,
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
            "eventsUrl": (transport or {}).get("eventsUrl"),
        },
        "coverage": {
            "numerator": (transport or {}).get("coverageNumerator"),
            "denominator": (transport or {}).get("coverageDenominator"),
            "scope": (transport or {}).get("coverageScope"),
        },
        "governance": _governance_projection(governance),
        "workspace": workspace or {},
        "projects": [_project_projection(p, executions, usage_by_project, git_state, ci_runs, platform_map, git_map) for p in projects],
        "executions": executions,
        "tasks": (store_projection or {}).get("tasks_by_status", {}),
        "tokenSummary": _token_summary(usage),
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
    platform_map: dict[str, str] | None = None,
    git_map: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    project_id = project.get("projectId")
    effective_git = (git_map or {}).get(project_id) or git_state
    project_executions = [e for e in executions if e.get("anchorProjectId") == project_id]
    active = sum(
        1 for e in project_executions if e.get("state") in {"RUNNING", "STARTING", "WAITING_USER", "WAITING_APPROVAL", "BLOCKED"}
    )
    usage = usage_by_project.get(project_id, {})
    project_ci = [r for r in ci_runs if r.get("projectId") == project_id]
    # WLGM-180: aggregate working areas from executions (never duplicated).
    working_areas: list[str] = []
    for e in project_executions:
        area = e.get("workingArea")
        if area and area not in working_areas:
            working_areas.append(area)
    return {
        "projectId": project_id,
        "agentPlatform": (platform_map or {}).get(project_id) or project.get("agentPlatform"),
        "displayName": project.get("displayName"),
        "identityState": project.get("identityState") or "UNRESOLVED",
        "activityState": project.get("activityState") or "UNKNOWN",
        "attentionState": project.get("attentionState") or "NONE",
        "activeExecutionCount": active,
        "workingAreas": working_areas,
        "visibility": project.get("visibility") or "UNKNOWN",
        "quality": project.get("quality") or "UNKNOWN",
        "lastStrongEvidenceAt": project.get("lastStrongEvidenceAt"),
        "repositories": project.get("repositories", []),
        "git": {
            "localSha": (effective_git or {}).get("localSha"),
            "remoteSha": (effective_git or {}).get("remoteSha"),
            "matchState": _git_match_state(effective_git or {}),
            "branch": (effective_git or {}).get("branch"),
            "dirtyCount": (effective_git or {}).get("dirtyCount"),
            "observedAt": (effective_git or {}).get("observedAt"),
            "quality": (effective_git or {}).get("quality"),
            "freshness": (effective_git or {}).get("freshness"),
            "sourceRef": (effective_git or {}).get("sourceRef"),
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


def _governance_projection(governance: dict[str, Any] | None) -> dict[str, Any]:
    """WLGM-180 §7: Rules/Skills/Memory/Adapter drift surface.

    Unknown when no data source declares it; never fabricates counts. Each
    family carries current/drift and a quality label.
    """
    if not governance:
        return {
            "state": "UNKNOWN",
            "families": {
                "rules": {"state": "UNKNOWN", "current": None, "drift": None},
                "skills": {"state": "UNKNOWN", "current": None, "drift": None},
                "memory": {"state": "UNKNOWN", "current": None, "drift": None},
                "adapters": {"state": "UNKNOWN", "current": None, "drift": None},
            },
        }
    families = {}
    for name in ("rules", "skills", "memory", "adapters"):
        family = governance.get(name) or {}
        current = family.get("current")
        drift = family.get("drift")
        if current is None and drift is None:
            state = "UNKNOWN"
        elif (drift or 0) > 0:
            state = "DRIFT"
        else:
            state = "CLEAN"
        families[name] = {"state": state, "current": current, "drift": drift}
    return {"state": governance.get("state") or "UNKNOWN", "families": families}


def _rollup_usage(usage: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    rolled: dict[str, dict[str, Any]] = {}
    for sample in usage:
        project_id = sample.get("projectId") or "unknown"
        entry = rolled.setdefault(project_id, {"inputTokens": None, "outputTokens": None, "totalTokens": None, "costQuality": "UNKNOWN"})
        for field in ("inputTokens", "outputTokens", "totalTokens"):
            value = sample.get(field)
            if isinstance(value, int) and not isinstance(value, bool):
                entry[field] = (entry[field] or 0) + value
        quality = sample.get("costQuality")
        if quality == "EXACT":
            entry["costQuality"] = "EXACT"
        elif quality == "ESTIMATED" and entry["costQuality"] != "EXACT":
            entry["costQuality"] = "ESTIMATED"
    return rolled


def _token_summary(usage: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate usage into tokenSummary with null-vs-zero discipline (P0-3).

    No usage -> every field null, costQuality UNKNOWN; a field missing from
    every sample stays null (never padded to 0); EXACT only when every sample
    declares EXACT, ESTIMATED when any does, else UNKNOWN.
    """
    if not usage:
        return {"inputTokens": None, "outputTokens": None, "totalTokens": None, "costQuality": "UNKNOWN"}

    def _sum(field: str) -> int | None:
        values = [u.get(field) for u in usage if isinstance(u.get(field), int) and not isinstance(u.get(field), bool)]
        return sum(values) if values else None

    qualities = [u.get("costQuality") for u in usage]
    if all(q == "EXACT" for q in qualities):
        cost_quality = "EXACT"
    elif any(q == "ESTIMATED" for q in qualities):
        cost_quality = "ESTIMATED"
    else:
        cost_quality = "UNKNOWN"
    return {
        "inputTokens": _sum("inputTokens"),
        "outputTokens": _sum("outputTokens"),
        "totalTokens": _sum("totalTokens"),
        "costQuality": cost_quality,
    }


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
    if remote is None and ci is None:
        return "UNVERIFIED"
    return "MISMATCH"
