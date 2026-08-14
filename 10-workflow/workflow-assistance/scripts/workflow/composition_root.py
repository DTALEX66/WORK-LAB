"""唯一运行组合根：approved ProductProject → canonical → v3 Snapshot → SSE → Observer。

WLGM P0-1/P0-2 收口：sidecar 与 durable_worker 通过本模块组装新链路，旧
collectors/EventHub/v1 投影保留兼容。本模块不修改任何既有模块。

- ``load_approved_index`` 从 canonical 读 approved ProductProject 定义；
- ``build_v3_snapshot`` 组装 snapshot_api.build_snapshot 的全部入参，transport
  由调用方传入的 live-gate verdict 决定（LIVE 只能来自 live gate）。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from canonical_store import CanonicalStore
from product_project import ProductProject, ProjectRootBinding
from project_identity_resolver import ApprovedProjectIndex
from snapshot_api import build_snapshot

# 显式批准白名单：默认仅 WORK-LAB 自身；其余项目需经 upsert_project_definition
# 持久化 approved=True 后才收集（未批准 → 绝不自动收集）。
EXPLICIT_APPROVED: set[str] = {"work-lab"}


def load_approved_index(store: CanonicalStore) -> ApprovedProjectIndex:
    """从 canonical 构造 ApprovedProjectIndex（定义缺失时降级为占位，approved=False）。"""
    projects: list[ProductProject] = []
    machine_roots: dict[str, str] = {}
    for row in store.list_projects():
        project_id = str(row.get("project_id") or row.get("projectId") or "")
        if not project_id:
            continue
        definition = store.get_project_definition(project_id)
        if definition:
            project = ProductProject.from_definition(definition)
        else:
            # 占位：display_name 来自 projects 表；approved 由白名单决定，
            # 未批准项目绝不自动收集（resolve 保持 UNRESOLVED/候选）。
            project = ProductProject(
                project_id=project_id,
                display_name=str(row.get("display_name") or project_id),
            )
        root = str(row.get("root_path") or "")
        if root:
            project.add_root_binding(
                ProjectRootBinding(
                    binding_id=f"{project_id}-root",
                    project_id=project_id,
                    root=root,
                )
            )
            machine_roots[project_id] = root
        projects.append(project)
    return ApprovedProjectIndex(projects=projects, machine_roots=machine_roots)


def _project_rows(store: CanonicalStore, index: ApprovedProjectIndex) -> list[dict[str, Any]]:
    """projects 表行 → v3 project projection（identityState 由 index 判定）。"""
    projections: list[dict[str, Any]] = []
    for row in store.list_projects():
        project_id = str(row.get("project_id") or "")
        if not project_id:
            continue
        root = str(row.get("root_path") or "")
        project = index.by_root(root) if root else None
        projections.append(
            {
                "projectId": project_id,
                "displayName": str(row.get("display_name") or project_id),
                "activityState": str(row.get("status") or "UNKNOWN"),
                "identityState": "RESOLVED" if project is not None else "UNRESOLVED",
            }
        )
    return projections


def _execution_rows(store: CanonicalStore) -> list[dict[str, Any]]:
    """execution_instances 行 → v3 execution projection (snake_case → camelCase)。"""
    executions: list[dict[str, Any]] = []
    for row in store.list_executions():
        executions.append(
            {
                "executionId": str(row.get("execution_id") or ""),
                "anchorProjectId": row.get("anchor_project_id"),
                "workingArea": row.get("working_area"),
                "state": str(row.get("state") or "UNKNOWN"),
                "stateQuality": str(row.get("state_quality") or "UNKNOWN"),
                "agent": row.get("agent"),
                "sessionId": row.get("session_id"),
                "sourceRef": row.get("source_ref"),
            }
        )
    return executions


def _usage_rows(store: CanonicalStore) -> list[dict[str, Any]]:
    """usage_samples 行 → v3 usage sample（snake_case → camelCase）。"""
    samples: list[dict[str, Any]] = []
    for row in store.list_usage_samples():
        samples.append(
            {
                "projectId": row.get("project_id"),
                "provider": row.get("provider"),
                "model": row.get("model"),
                "inputTokens": row.get("input_tokens"),
                "outputTokens": row.get("output_tokens"),
                "totalTokens": row.get("total_tokens"),
                "costQuality": str(row.get("quality") or "UNKNOWN"),
            }
        )
    return samples


def _ci_rows(store: CanonicalStore) -> list[dict[str, Any]]:
    """ci_runs 行 → v3 ci projection。"""
    runs: list[dict[str, Any]] = []
    for row in store.list_ci_runs():
        runs.append(
            {
                "runId": row.get("run_id"),
                "workflow": row.get("workflow"),
                "headSha": row.get("head_sha"),
                "status": row.get("status"),
                "conclusion": row.get("conclusion"),
                "sourceRef": row.get("source_ref"),
            }
        )
    return runs


def _collector_coverage(store: CanonicalStore) -> dict[str, Any]:
    """collector_health 行 → coverage（新鲜 collector 数/总数）。"""
    rows = store.list_collector_health()
    total = len(rows)
    fresh = sum(1 for row in rows if str(row.get("state") or "") == "healthy")
    return {"numerator": fresh, "denominator": total, "scope": "collector_health"}


def build_v3_snapshot(
    store: CanonicalStore,
    index: ApprovedProjectIndex,
    *,
    revision: int,
    events_url: str | None,
    transport_state: str,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """组装 v3 snapshot（transport 由 live-gate verdict 决定，绝不伪造 LIVE）。"""
    return build_snapshot(
        revision=revision,
        generated_at=generated_at,
        store_projection={},
        projects=_project_rows(store, index),
        executions=_execution_rows(store),
        usage=_usage_rows(store),
        ci_runs=_ci_rows(store),
        transport={
            "transportState": transport_state,
            "eventsUrl": events_url,
            "coverageNumerator": _collector_coverage(store)["numerator"],
            "coverageDenominator": _collector_coverage(store)["denominator"],
            "coverageScope": _collector_coverage(store)["scope"],
        },
    )
