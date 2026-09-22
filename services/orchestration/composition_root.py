"""唯一运行组合根：approved ProductProject → canonical → v3 Snapshot → SSE → Observer。

WLGM P0-1/P0-2 收口：sidecar 与 durable_worker 通过本模块组装新链路，旧
collectors/EventHub/v1 投影保留兼容。本模块不修改任何既有模块。

- ``load_approved_index`` 从 canonical 读 approved ProductProject 定义；
- ``build_v3_snapshot`` 组装 snapshot_api.build_snapshot 的全部入参，transport
  由调用方传入的 live-gate verdict 决定（LIVE 只能来自 live gate）。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from canonical_store import CanonicalStore
from product_project import ProductProject, ProjectRootBinding
from project_identity_resolver import ApprovedProjectIndex
from snapshot_api import build_snapshot

# ---------------------------------------------------------------------------
# WS-2 / spec-3: software[] wiring into build_v3_snapshot
#
# The canonical software registry (config/software-registry.json) is the single
# source of truth for managed software ids. Real discovery (platform_discovery.
# discover_software_installations) probes the declared install roots and
# classifies each software via the shared resolver (software_installation_identity).
# Any probe failure degrades to software=[] + discoverySource="unavailable" —
# the snapshot build NEVER crashes on discovery.
#
# Cross-package import convention (matches durable_worker.py / canary_runner.py):
# the module roots live under packages/client-neutral-core/scripts after the
# directory convergence. Inject the path once; guard so tests that already
# include that path on sys.path are unaffected.
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[2]
_CNC_SCRIPTS = _ROOT / "packages" / "client-neutral-core" / "scripts"
if str(_CNC_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_CNC_SCRIPTS))

try:
    import platform_discovery as _platform_discovery
    import software_installation_identity as _sii
except Exception:  # pragma: no cover - import failure degrades to unavailable
    _platform_discovery = None  # type: ignore[assignment]
    _sii = None  # type: ignore[assignment]

# Bounded in-memory cache for discovery results (spec: TTL-based, single entry).
# The cache survives across /api/v1/snapshot calls within its TTL so repeated
# discovery probes (subprocess execs of --version, etc.) are not run on every
# SSE publish tick. The TTL is intentionally conservative (60 s) so a user who
# installs software gets a fresh observation within one minute without waiting
# for a full sidecar restart.
_SOFTWARE_DISCOVERY_TTL_SECONDS = 60.0
_software_discovery_cache: dict[str, Any] = {}


def _load_software_registry() -> list[dict[str, Any]]:
    """Read the canonical software registry. Returns [] on any failure."""
    try:
        path = _ROOT / "config" / "software-registry.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("software", [])
    except Exception:
        return []


def _build_software_projection() -> list[dict[str, Any]]:
    """Build the software[] snapshot projection (registry × discovery × resolver).

    Field alignment (frontend SoftwareIdentity, spec step 1/4):
      softwareId, displayName, installRoot, executableRealpath,
      discoveredVersion, releaseChannel, updateAvailable,
      duplicateInstallation, expectedLocation, observedLocation,
      locationStatus, lastVerified, discoverySource

    Truth discipline: when discovery is unavailable, locationStatus stays
    "UNKNOWN" and discoverySource becomes "unavailable" — we never fabricate
    a value. Each entry reflects only the actual probed facts.
    """
    if _platform_discovery is None or _sii is None:
        return []

    # --- Bounded TTL cache (key: revision-independent; value: {at, items}) ---
    now = time.time()
    cached = _software_discovery_cache.get("items")
    if cached is not None and (now - _software_discovery_cache.get("at", 0.0)) < _SOFTWARE_DISCOVERY_TTL_SECONDS:
        return cached

    try:
        registry = _load_software_registry()
        observations = _platform_discovery.discover_software_installations()
        obs_by_id = {str(o.get("software_id") or ""): o for o in observations}

        items: list[dict[str, Any]] = []
        for entry in registry:
            software_id = str(entry.get("softwareId") or "")
            if not software_id:
                continue
            display_name = entry.get("displayName")
            # Canonical registry -> discovery inventory matching.
            # The SOFTWARE_CANDIDATE_INVENTORY in platform_discovery uses
            # "package_identity" keys that mirror "softwareId" in the registry.
            obs = obs_by_id.get(software_id)

            if obs is None:
                # Registry entry with no discovery observation: UNKNOWN.
                items.append(
                    {
                        "softwareId": software_id,
                        "displayName": display_name,
                        "installRoot": None,
                        "executableRealpath": None,
                        "discoveredVersion": None,
                        "releaseChannel": None,
                        "updateAvailable": None,
                        "duplicateInstallation": False,
                        "expectedLocation": None,
                        "observedLocation": None,
                        "locationStatus": "UNKNOWN",
                        "lastVerified": None,
                        "discoverySource": "unavailable",
                    }
                )
                continue

            # Discovery observation present — extract real fields.
            location_status = str(obs.get("location_status") or "UNKNOWN")
            # DUAL_INSTALLATION from the resolver means more than one real root.
            duplicate = location_status == "DUAL_INSTALLATION"
            observed_location = obs.get("observed_existing_location") or obs.get("install_root")

            items.append(
                {
                    "softwareId": software_id,
                    "displayName": display_name,
                    "installRoot": obs.get("install_root"),
                    "executableRealpath": obs.get("executable_realpath") or None,
                    "discoveredVersion": obs.get("discovered_version"),
                    "releaseChannel": obs.get("release_channel"),  # usually None from resolver
                    "updateAvailable": None,  # NOT in resolver; not probed -> never fabricate
                    "duplicateInstallation": duplicate,
                    "expectedLocation": obs.get("expected_existing_location") or obs.get("expected_existing"),
                    "observedLocation": observed_location,
                    "locationStatus": location_status,
                    "lastVerified": obs.get("verified_at"),
                    "discoverySource": obs.get("discovery_source") or "real-platform-probe",
                }
            )

        _software_discovery_cache["items"] = items
        _software_discovery_cache["at"] = now
        return items
    except Exception:
        # Discovery failure → empty projection + unavailable flag (degrade, don't crash).
        _software_discovery_cache.clear()
        return []


def clear_software_discovery_cache() -> None:
    """Public reset for tests / callers that need to force a fresh probe."""
    _software_discovery_cache.clear()


# ---------------------------------------------------------------------------
# End WS-2 / spec-3 software[] wiring
# ---------------------------------------------------------------------------

# 显式批准白名单：默认仅 WORK-LAB 自身；其余项目需经 upsert_project_definition
# 持久化 approved=True 后才收集（未批准 → 绝不自动收集）。
EXPLICIT_APPROVED: set[str] = {"work-lab", "design-lab", "archeaxis-knowledge-os", "obsidian-assistance"}


def load_approved_index(store: CanonicalStore) -> ApprovedProjectIndex:
    """从 canonical 构造 ApprovedProjectIndex；未批准 registry 行不得进入投影。"""
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
            project = ProductProject(
                project_id=project_id,
                display_name=str(row.get("display_name") or project_id),
                approved=project_id in EXPLICIT_APPROVED,
            )
        approved = project_id in EXPLICIT_APPROVED or project.approved
        if not approved or project.deny_listed or project.never_scan:
            continue
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
        if not project_id or project_id not in index.projects:
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


def _agent_platform_map() -> dict[str, str]:
    """Map agent id -> platform display name from the adapter registry.

    Kept dynamic (reads registry, never hard-locks). Unknown agents fall back
    to snapshot_api.AGENT_TO_PLATFORM defaults.
    """
    import json
    from pathlib import Path
    registry_path = Path(__file__).resolve().parents[2] / "config" / "adapter-registry.json"
    mapping: dict[str, str] = {}
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        for entry in data.get("entries", []):
            aid = entry.get("id")
            display = entry.get("display_name") or entry.get("displayName")
            if aid and display:
                mapping[aid.lower()] = str(display).upper()
    except Exception:
        pass
    return mapping


def _collector_coverage(store: CanonicalStore) -> dict[str, Any]:
    """collector_health 行 → coverage；无运行记录时保持空覆盖。"""
    rows = store.list_collector_health()
    if not rows:
        return {"numerator": None, "denominator": None, "scope": None}
    fresh = sum(
        1
        for row in rows
        if row.get("last_success_at")
        and int(row.get("consecutive_failures") or 0) == 0
        and not row.get("circuit_open_until")
    )
    return {"numerator": fresh, "denominator": len(rows), "scope": "collector_health"}


def _git_states(store: CanonicalStore) -> dict[str, dict[str, Any]]:
    """Return the newest Git observation per approved project.

    The previous implementation returned the first ``scope=git`` row and
    passed it to every project.  That made a cross-project dashboard display
    WORK-LAB's branch/SHA on unrelated projects.  Keep the projection
    project-scoped and choose by observed timestamp (the collector writes one
    row per project).
    """
    latest: dict[str, dict[str, Any]] = {}
    for row in store.list_source_quality():
        if str(row.get("scope") or "") != "git":
            continue
        project_id = str(row.get("project_id") or "")
        payload = row.get("payload") or {}
        if isinstance(payload, str):
            try:
                import json
                payload = json.loads(payload)
            except (TypeError, ValueError):
                payload = {}
        if not project_id or not isinstance(payload, dict) or not payload.get("head_sha"):
            continue
        candidate = {
            "localSha": payload.get("head_sha"),
            "remoteSha": payload.get("remote_sha"),
            "ciSha": payload.get("ci_sha"),
            "branch": payload.get("branch"),
            "dirtyCount": payload.get("dirty_count"),
            "observedAt": row.get("observed_at"),
            "quality": row.get("quality"),
            "freshness": row.get("freshness"),
            "sourceRef": payload.get("sourceRef"),
        }
        current = latest.get(project_id)
        if current is None or str(candidate.get("observedAt") or "") >= str(current.get("observedAt") or ""):
            latest[project_id] = candidate
    return latest


def _git_state(store: CanonicalStore) -> dict[str, Any] | None:
    """Backward-compatible single-project helper (WORK-LAB only)."""
    return _git_states(store).get("work-lab") or next(iter(_git_states(store).values()), None)


def build_v3_snapshot(
    store: CanonicalStore,
    index: ApprovedProjectIndex,
    *,
    revision: int,
    events_url: str | None = None,
    transport_state: str = "UNKNOWN",
    freshness_state: str = "UNKNOWN",
    generated_at: str | None = None,
    workspace_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """组装 v3 snapshot（transport 由 live-gate verdict 决定，绝不伪造 LIVE）。"""
    coverage = _collector_coverage(store)
    # Observer cross-project view: map project_id -> primary platform from
    # platform_observations (recorded by the platform collector). Null when
    # no observation exists; never fabricated.
    platform_map = {}
    try:
        for row in store.query_platform_observations():
            platform_map.setdefault(row["project_id"], row["platform"])
    except Exception:
        platform_map = {}
    git_states = _git_states(store)
    return build_snapshot(
        revision=revision,
        generated_at=generated_at,
        source_watermark=store.max_watermark(),
        store_projection=store.projection(),
        projects=_project_rows(store, index),
        executions=_execution_rows(store),
        usage=_usage_rows(store),
        ci_runs=_ci_rows(store),
        transport={
            "transportState": transport_state,
            "freshnessState": freshness_state,
            "eventsUrl": events_url,
            "coverageNumerator": coverage["numerator"],
            "coverageDenominator": coverage["denominator"],
            "coverageScope": coverage["scope"],
        },
        # Keep the top-level Git summary for legacy consumers, but pass the
        # project map so each card is sourced from its own repository.
        git_state=git_states.get("work-lab") or next(iter(git_states.values()), None),
        git_map=git_states,
        workspace=workspace_evidence,
        platform_map=platform_map,
        agent_map=_agent_platform_map(),
        software=_build_software_projection(),
    )
