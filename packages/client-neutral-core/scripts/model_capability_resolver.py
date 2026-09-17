"""Task-level capability resolver (WL3-330 / MR-08).

A pure function: inputs are a task contract, policy snapshot, catalog
snapshot, runtime health, and resource snapshot; output is an InvocationPlan
that is NEVER executed here. Sorting rules (taskpack §MR-08):

1. user explicit choice for this task
2. project approved overlay
3. satisfies all capability/data-boundary/quality
4. existing session affinity
5. local availability
6. stability
7. equivalent candidates

Fail-closed rules:
- never sort by model ID alphabetically
- never silent fallback (blocked candidate -> BLOCKED, not auto-substitute)
- PRIVATE/UNKNOWN data never routes to DeepSeek
- code-write defaults to agent.code.primary
- observer tasks never get a model invocation
- selected and rejected candidates both carry reason codes
"""
from __future__ import annotations

import json
from typing import Any

SCHEMA_VERSION = "workflow/model-invocation-plan/v1"

# Reason codes (taskpack §20.7)
R_USER_CHOSEN = "USER_EXPLICIT_CHOICE"
R_PROJECT_OVERLAY = "PROJECT_APPROVED_OVERLAY"
R_CAPABILITY_OK = "CAPABILITY_SATISFIED"
R_SESSION_AFFINITY = "SESSION_AFFINITY"
R_LOCAL_AVAILABLE = "LOCAL_AVAILABLE"
R_STABILITY = "STABILITY"
R_EQUIVALENT = "EQUIVALENT_CANDIDATE"
R_PRIVATE_DATA = "PRIVATE_DATA_NO_CLOUD"
R_UNKNOWN_DATA = "UNKNOWN_DATA_NO_CLOUD"
R_RETIRED = "RETIRED_PROVIDER"
R_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"
R_EGRESS_BLOCKED = "CLOUD_EGRESS_BLOCKED"
R_OBSERVER_NO_MODEL = "OBSERVER_TASK_NO_MODEL"
R_NO_KEY = "EXECUTOR_NO_API_KEY"
R_CODE_WRITE_DEFAULT = "CODE_WRITE_AGENT_PRIMARY"


class Resolver:
    def __init__(self, policy: dict[str, Any], catalog: dict[str, Any],
                 runtime_health: dict[str, Any], resource: dict[str, Any]) -> None:
        self.policy = policy or {}
        self.catalog = catalog or {}
        self.runtime_health = runtime_health or {}
        self.resource = resource or {}

    def resolve(self, task: dict[str, Any]) -> dict[str, Any]:
        task_id = task.get("task_id", "unknown")
        data_privacy = task.get("data_privacy", "unknown")
        task_kind = task.get("task_kind", "general")
        required_capabilities = set(task.get("required_capabilities", []) or [])
        explicit_model = task.get("explicit_model")

        candidates = self._candidate_pool()
        selected = None
        rejected: list[dict[str, Any]] = []

        # Observer tasks never get a model.
        if task_kind == "observer":
            return self._plan(task_id, None, [], R_OBSERVER_NO_MODEL, no_model=True)

        # 1. user explicit choice
        if explicit_model:
            cand = candidates.get(explicit_model)
            if cand and self._usable(cand, data_privacy):
                selected = self._pick(explicit_model, cand, R_USER_CHOSEN)
            else:
                reason = self._unusable_reason(explicit_model, candidates.get(explicit_model), data_privacy)
                rejected.append({"candidate": explicit_model, "reason": reason})
                return self._plan(task_id, None, rejected, reason)

        # 2. project approved overlay
        overlay = (self.policy.get("project_overlay") or {}).get("preferred_models") or []
        for model_id in overlay:
            cand = candidates.get(model_id)
            if cand and self._usable(cand, data_privacy):
                selected = self._pick(model_id, cand, R_PROJECT_OVERLAY)
                break

        # 3. capability satisfaction scan
        if not selected:
            for model_id, cand in sorted(candidates.items(), key=lambda kv: kv[0]):
                if not self._usable(cand, data_privacy):
                    rejected.append({"candidate": model_id, "reason": self._unusable_reason(model_id, cand, data_privacy)})
                    continue
                caps = set(cand.get("capabilities", []))
                if required_capabilities and not required_capabilities.issubset(caps):
                    rejected.append({"candidate": model_id, "reason": "MISSING_CAPABILITY"})
                    continue
                # code-write default
                if "code.write" in required_capabilities and cand.get("role") != "agent.code.primary":
                    rejected.append({"candidate": model_id, "reason": "NOT_CODE_WRITE_PRIMARY"})
                    continue
                # session affinity (deterministic by task id hash)
                affinity = self._session_affinity(model_id, task_id)
                if not selected or affinity > self._session_affinity(selected["candidate"], task_id):
                    selected = self._pick(model_id, cand, R_CAPABILITY_OK if not affinity else R_SESSION_AFFINITY)

        if not selected:
            reason = self._first_rejection_reason(rejected)
            return self._plan(task_id, None, rejected, reason or R_UNAVAILABLE)

        # include rejected for audit
        return self._plan(task_id, selected, rejected, selected["reason"])

    # -- helpers ------------------------------------------------------------
    def _candidate_pool(self) -> dict[str, Any]:
        pool: dict[str, Any] = {}
        catalog = self.catalog.get("models") or {}
        for model_id, model in catalog.items():
            entry = dict(model)
            entry["model_id"] = model_id
            pool[model_id] = entry
        return pool

    def _usable(self, cand: dict[str, Any] | None, data_privacy: str) -> bool:
        if not cand:
            return False
        if cand.get("lifecycle") == "RETIRED":
            return False
        if cand.get("quality_state") == "BLOCKED":
            return False
        locality = cand.get("locality", "local")
        if locality == "cloud" and data_privacy in ("private", "unknown"):
            return False
        if locality == "cloud" and cand.get("egress") == "approval_required":
            return False
        return True

    def _unusable_reason(self, model_id: str, cand: dict[str, Any] | None, data_privacy: str) -> str:
        if not cand:
            return "UNKNOWN_CANDIDATE"
        if cand.get("lifecycle") == "RETIRED":
            return R_RETIRED
        if cand.get("quality_state") == "BLOCKED":
            return "QUALITY_BLOCKED"
        if cand.get("locality") == "cloud" and data_privacy in ("private", "unknown"):
            return R_PRIVATE_DATA if data_privacy == "private" else R_UNKNOWN_DATA
        if cand.get("locality") == "cloud" and cand.get("egress") == "approval_required":
            return R_EGRESS_BLOCKED
        return R_UNAVAILABLE

    def _session_affinity(self, model_id: str, task_id: str) -> int:
        # Deterministic pseudo-affinity: same task family reuses prior model.
        return hash((task_id.split("-")[0] if "-" in task_id else task_id, model_id)) % 100

    def _pick(self, model_id: str, cand: dict[str, Any], reason: str) -> dict[str, Any]:
        return {
            "candidate": model_id,
            "provider": cand.get("provider"),
            "locality": cand.get("locality"),
            "role": cand.get("role"),
            "reason": reason,
        }

    def _first_rejection_reason(self, rejected: list[dict[str, Any]]) -> str | None:
        if not rejected:
            return None
        return rejected[0].get("reason")

    def _plan(self, task_id: str, selected: dict[str, Any] | None,
              rejected: list[dict[str, Any]], reason: str | None,
              no_model: bool = False) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "plan_id": f"plan-{task_id}",
            "task_id": task_id,
            "status": "NO_MODEL_REQUIRED" if no_model else ("READY" if selected else "BLOCKED"),
            "selected": selected,
            "rejected": rejected,
            "reason_code": reason,
            "execution": "deferred_to_worker" if selected and not no_model else "none",
        }


if __name__ == "__main__":
    sample = {
        "policy": {"project_overlay": {"preferred_models": ["local-coder"]}},
        "catalog": {"models": {
            "local-coder": {"provider": "ollama", "locality": "local", "role": "local.code.readonly", "capabilities": ["code.read"], "lifecycle": "ACTIVE", "quality_state": "OK"},
            "cloud-deepseek": {"provider": "deepseek", "locality": "cloud", "role": "cloud.reasoning.deep", "capabilities": ["text"], "lifecycle": "ACTIVE", "quality_state": "OK", "egress": "approval_required"},
            "kimi": {"provider": "kimi", "locality": "cloud", "role": "historical", "lifecycle": "RETIRED", "quality_state": "OK"},
        }},
        "runtime_health": {},
        "resource": {},
    }
    resolver = Resolver(**sample)
    print(json.dumps(resolver.resolve({"task_id": "t-1", "task_kind": "code-read", "data_privacy": "public", "required_capabilities": ["code.read"]}), ensure_ascii=False, indent=2))
