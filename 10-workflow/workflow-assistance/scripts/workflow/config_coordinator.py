"""Three-way configuration coordinator (WL3-210).

Discover actual -> classify ownership -> compare previous upstream / new
upstream / user overlay -> ActionPlan -> approval when required -> narrow apply
through stable official interface -> readback -> rollback or evidence commit.

Apply is approval-gated and intentionally not invoked here; this module only
produces plans and readback/rollback evidence for already-applied overlays.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

UNKNOWN_DEFAULT = {"mode": "OBSERVE", "layer": "USER_OVERLAY", "adapter": None, "quarantine": True}
NON_PATCH_MODES = {"OBSERVE", "IGNORE", "FORBIDDEN"}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def classify_field(rule: dict[str, Any] | None) -> dict[str, Any]:
    if not rule:
        return dict(UNKNOWN_DEFAULT)
    return {
        "mode": str(rule.get("mode", "OBSERVE")),
        "layer": str(rule.get("layer", rule.get("owner", "USER_OVERLAY"))),
        "adapter": rule.get("adapter"),
        "quarantine": rule.get("layer") == "SECRET" or rule.get("mode") in NON_PATCH_MODES,
    }


def three_way_compare(
    ownership_registry: dict[str, Any],
    *,
    previous_upstream: dict[str, Any],
    new_upstream: dict[str, Any],
    user_overlay: dict[str, Any],
    identity_apply_allowed: bool,
) -> dict[str, Any]:
    """Compare three config layers and emit a field-level ActionPlan."""
    declared = {item["path"]: item for item in ownership_registry.get("fields", [])}
    paths = sorted(set(previous_upstream) | set(new_upstream) | set(user_overlay))
    fields: list[dict[str, Any]] = []
    for path in paths:
        old = previous_upstream.get(path)
        new = new_upstream.get(path)
        user = user_overlay.get(path)
        if old == new and user is None:
            continue  # no drift, no overlay
        rule = declared.get(path)
        classification = classify_field(rule)
        if user is not None and old != new:
            # Upstream changed under a user overlay -> rebase candidate, keep intent.
            change = "UPSTREAM_CHANGED_WITH_OVERLAY"
            action = "REBASE_OR_QUARANTINE" if classification["quarantine"] else "REBASE"
        elif user is not None:
            change = "USER_OVERLAY"
            action = "QUARANTINE" if classification["quarantine"] else "KEEP"
        elif old != new:
            change = "UPSTREAM_CHANGED"
            action = "QUARANTINE" if classification["quarantine"] else "REBASE"
        else:
            change = "UNCHANGED"
            action = "NONE"
        fields.append(
            {
                "path": path,
                "layer": classification["layer"],
                "mode": classification["mode"],
                "change": change,
                "action": action,
                "previous_upstream": old,
                "new_upstream": new,
                "user_overlay": user,
                "adapter": classification["adapter"],
            }
        )
    patchable = [f for f in fields if f["action"] not in {"QUARANTINE", "NONE"}]
    quarantined = [f for f in fields if f["action"] == "QUARANTINE"]
    apply_allowed = identity_apply_allowed and bool(patchable) and not quarantined
    return {
        "schema_version": "workflow/config-action-plan/v1",
        "status": "DRY_RUN",
        "identity_apply_allowed": identity_apply_allowed,
        "approval_required": bool(fields),
        "apply_allowed": apply_allowed,
        "patchable_fields": [f["path"] for f in patchable],
        "quarantined_fields": [f["path"] for f in quarantined],
        "rollback": {"required": bool(patchable), "strategy": "backup-cas-readback-rollback"},
        "fields": fields,
    }


def overlay_digest(values: dict[str, Any]) -> str:
    """Stable digest over the overlay for CAS and readback evidence."""
    encoded = json.dumps(values, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def readback_overlay(path: Path, expected_digest: str) -> dict[str, Any]:
    """Read back an applied overlay and verify it matches the recorded digest."""
    if not path.is_file():
        return {"status": "MISSING", "expected_digest": expected_digest}
    values = _load_json(path)
    actual = overlay_digest(values)
    return {
        "status": "PASS" if actual == expected_digest else "DRIFT",
        "expected_digest": expected_digest,
        "actual_digest": actual,
        "values": values,
    }


def rollback_plan(plan: dict[str, Any], backup: dict[str, Any] | None) -> dict[str, Any]:
    """Fenced rollback plan: only fields recorded in the plan, from the backup."""
    if not backup:
        return {"status": "NO_BACKUP", "apply": False}
    paths = {f["path"] for f in plan.get("fields", [])}
    restore = [p for p in sorted(paths) if p in backup]
    return {
        "schema_version": "workflow/config-rollback-plan/v1",
        "status": "READY",
        "apply": bool(restore),
        "restore_fields": restore,
        "strategy": "recorded-ownership-hash-fenced",
    }
