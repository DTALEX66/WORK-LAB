from __future__ import annotations

import hashlib
import json
import sys

REQUIRED = {"workflow", "observer", "token-monitor", "supply-chain-security", "integration"}
PLAN_GATES = {"workflow", "observer", "token-monitor", "supply-chain-security", "integration"}
JOB_NAMES = {
    "workflow": "workflow",
    "observer": "observer",
    "token-monitor": "token-monitor",
    "supply-chain-security": "supply-chain-security",
    "integration": "integration",
}


def _plan_digest(plan: dict[str, object]) -> str:
    payload = {key: value for key, value in plan.items() if key not in {"generated_at", "plan_id", "plan_digest"}}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _resolve_plan(data: dict[str, object]) -> tuple[set[str], str | None, str | None]:
    raw_plan = data.get("gate_plan")
    if raw_plan is None:
        return set(REQUIRED), None, None
    if not isinstance(raw_plan, dict):
        raise ValueError("gate_plan must be an object")
    if raw_plan.get("schema_version") != "workflow/gate-plan/v1":
        raise ValueError("gate_plan schema_version must be workflow/gate-plan/v1")
    required = raw_plan.get("required_gates")
    changed_paths = raw_plan.get("changed_paths")
    digest = raw_plan.get("plan_digest")
    source_identity = raw_plan.get("source_identity")
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        raise ValueError("gate_plan.required_gates must be a string list")
    if len(required) != len(set(required)):
        raise ValueError("gate_plan.required_gates must be unique")
    if not isinstance(changed_paths, list) or not all(isinstance(item, str) and item for item in changed_paths):
        raise ValueError("gate_plan.changed_paths must be a non-empty-string list")
    normalized_required = set(required)
    unknown = normalized_required - PLAN_GATES
    if unknown:
        raise ValueError(f"gate_plan contains unknown gates: {sorted(unknown)}")
    if changed_paths and not normalized_required:
        raise ValueError("gate_plan with changed paths must require at least one gate")
    if (
        not isinstance(digest, dict)
        or digest.get("algorithm") != "sha256"
        or not isinstance(digest.get("value"), str)
    ):
        raise ValueError("gate_plan.plan_digest must be sha256")
    computed = _plan_digest(raw_plan)
    if digest["value"] != computed:
        raise ValueError("gate_plan digest mismatch")
    if not isinstance(source_identity, dict):
        raise ValueError("gate_plan.source_identity must be an object")
    commit_identity = source_identity.get("commit")
    tree_identity = source_identity.get("tree")
    if not isinstance(commit_identity, dict) or not isinstance(commit_identity.get("oid"), str) or not commit_identity["oid"]:
        raise ValueError("gate_plan source commit oid is required")
    if not isinstance(tree_identity, dict) or not isinstance(tree_identity.get("oid"), str) or not tree_identity["oid"]:
        raise ValueError("gate_plan source tree oid is required")
    commit = commit_identity["oid"]
    return normalized_required, digest["value"], commit


def main(payload: str) -> int:
    try:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("aggregate payload must be an object")
        required, digest, plan_commit = _resolve_plan(data)
        expected_digest = data.get("expected_plan_digest")
        if digest is not None:
            if not isinstance(expected_digest, str) or not expected_digest:
                raise ValueError("aggregate expected plan digest is required")
            if expected_digest != digest:
                raise ValueError("aggregate expected plan digest does not match plan")
        expected_commit = data.get("expected_head_sha")
        if plan_commit is not None:
            if not isinstance(expected_commit, str) or not expected_commit:
                raise ValueError("aggregate expected head SHA is required")
            if expected_commit != plan_commit:
                raise ValueError("aggregate plan commit does not match head SHA")
        jobs = data.get("jobs", {})
        if not isinstance(jobs, dict):
            raise ValueError("aggregate jobs must be an object")
        bad = [JOB_NAMES[name] for name in required if jobs.get(JOB_NAMES[name]) not in {"success", "passed"}]
        if bad:
            result = {"status": "FAIL", "missing_or_failed": sorted(bad)}
            if digest is not None:
                result["plan_digest"] = digest
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
            return 1
        result = {"status": "PASS", "required": sorted(JOB_NAMES[name] for name in required)}
        if digest is not None:
            result["plan_digest"] = digest
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "reason": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.stdin.read()))
