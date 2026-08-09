"""Dry-run field-level configuration coordinator; apply is intentionally absent."""
from __future__ import annotations

from typing import Any


def plan_changes(identity: dict[str, Any], ownership: dict[str, Any], observed: dict[str, Any], desired: dict[str, Any]) -> dict[str, Any]:
    unique = bool(identity.get("apply_allowed"))
    fields = []
    declared = {item["path"]: item for item in ownership.get("fields", [])}
    for path in sorted(set(observed) | set(desired)):
        if observed.get(path) == desired.get(path):
            continue
        rule = declared.get(path, {"owner": "USER_OVERLAY", "mode": "OBSERVE"})
        mode = rule.get("mode", "OBSERVE")
        fields.append({"path": path, "owner": rule.get("owner"), "mode": mode, "from": observed.get(path), "to": desired.get(path), "action": "QUARANTINE" if mode in {"OBSERVE", "IGNORE", "FORBIDDEN"} else "PATCH"})
    allowed = unique and all(field["action"] == "PATCH" for field in fields)
    return {"schema_version": "workflow/config-action-plan/v1", "status": "DRY_RUN", "approval_required": bool(fields), "apply_allowed": allowed, "rollback": {"required": bool(fields), "strategy": "backup-readback-rollback"}, "fields": fields}
