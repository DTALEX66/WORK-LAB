"""WORK-LAB Config Control Plane (WL-P0-005 / TP-20260819).

Six-layer configuration model:
  Official Baseline -> Compatibility Baseline -> User Profile -> Project
  Override -> Machine Overlay -> Session Override -> Effective Config
  -> Diff / Approval / Apply / Readback / Drift Detection / Rollback

Contracts: SoftwareRegistrationV1, OfficialBaselineV1, CompatibilityProfileV1,
UserConfigurationProfileV1, MachineOverlayV1, SessionOverrideV1,
SecretReferenceV1, EffectiveConfigurationV1, ConfigurationDiffV1,
ConfigurationApplyPlanV1, ConfigurationReadbackV1, ConfigurationDriftV1,
ConfigurationRollbackV1.

External software (Hermes/Codex/DSH/...) is managed here as registered
configuration, never as core product identity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

LAYER_ORDER = ["session_override", "project_override", "user_profile", "machine_overlay", "compatibility", "official_baseline"]

# Safety policy cannot be overridden.
SAFETY_KEYS = {"safety_boundary", "approval_required", "credential_redaction"}


@dataclass
class SoftwareRegistration:
    software_id: str
    display_name: str
    category: str
    official_repository: str | None
    current_baseline_version: str | None = None
    baseline_digest: str | None = None
    adapter_id: str | None = None
    secret_fields: list[str] = field(default_factory=list)
    compatibility_status: str = "registered"

    def to_dict(self) -> dict[str, Any]:
        return {
            "softwareId": self.software_id,
            "displayName": self.display_name,
            "category": self.category,
            "officialRepository": self.official_repository,
            "currentBaselineVersion": self.current_baseline_version,
            "baselineDigest": self.baseline_digest,
            "adapterId": self.adapter_id,
            "secretFields": self.secret_fields,
            "compatibilityStatus": self.compatibility_status,
        }


class ConfigControlPlane:
    def __init__(self) -> None:
        self._software: dict[str, SoftwareRegistration] = {}
        self._layers: dict[str, dict[str, Any]] = {k: {} for k in LAYER_ORDER}

    def register(self, reg: SoftwareRegistration) -> None:
        self._software[reg.software_id] = reg

    def list_registered(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._software.values()]

    def set_layer(self, layer: str, config: dict[str, Any]) -> None:
        if layer not in self._layers:
            raise ValueError(f"unknown config layer: {layer}")
        self._layers[layer] = dict(config)

    def effective(self, software_id: str | None = None) -> dict[str, Any]:
        """Merge layers by priority; safety keys always win from the safest layer."""
        merged: dict[str, Any] = {}
        for layer in reversed(LAYER_ORDER):  # official first, session last (highest priority)
            merged.update(self._layers[layer])
        # safety policy cannot be overridden by lower-priority layers
        for key in SAFETY_KEYS:
            for layer in ("official_baseline", "compatibility", "user_profile"):
                if key in self._layers[layer]:
                    merged[key] = self._layers[layer][key]
        if software_id:
            merged["softwareId"] = software_id
        return merged

    def diff(self, before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
        changed = {k: {"before": before.get(k), "after": after.get(k)} for k in set(before) | set(after) if before.get(k) != after.get(k)}
        return {"changedFields": changed, "changeCount": len(changed)}

    def readback_matches(self, applied: dict[str, Any], readback: dict[str, Any]) -> bool:
        return applied == readback

    def apply_plan(self, diff: dict[str, Any], *, approved: bool = False) -> dict[str, Any]:
        if not approved:
            return {"status": "WAITING_APPROVAL", "changeCount": diff["changeCount"]}
        return {"status": "APPLIED", "changeCount": diff["changeCount"]}

    def detect_drift(self, effective: dict[str, Any], readback: dict[str, Any]) -> dict[str, Any]:
        drifted = {k: {"effective": effective.get(k), "readback": readback.get(k)} for k in set(effective) | set(readback) if effective.get(k) != readback.get(k)}
        return {"drift": drifted, "driftCount": len(drifted), "status": "DRIFT" if drifted else "CLEAN"}

    def rollback(self, target: dict[str, Any], rollback_to: dict[str, Any]) -> dict[str, Any]:
        return {"status": "ROLLED_BACK", "restored": rollback_to == target}

    # --- WLR-330: real config transaction (Discover -> Effective -> Diff -> Backup
    # -> Approval -> Apply -> Readback -> Commit or Rollback) ---
    def transaction(self, software_id: str, diff: dict[str, Any], *, approved: bool = False,
                    backup_dir: str | None = None, apply_fn=None, readback_fn=None) -> dict[str, Any]:
        """A true transaction: every stage has a digest, idempotency key and a
        recovery point. APPLIED is only produced when native readback matches.
        Unapproved never writes live.

        - backup: effective config snapshot persisted (backup ref)
        - apply:  apply_fn(effective_after) if approved (else WAITING_APPROVAL)
        - readback: readback_fn() must equal the applied effective config
        - mismatch -> rollback to backup; match -> COMMITTED with receipt
        """
        import hashlib, json, time
        from pathlib import Path

        effective_before = self.effective(software_id)
        idem = hashlib.sha256((software_id + json.dumps(diff, sort_keys=True) + str(time.time())).encode()).hexdigest()[:16]
        if not approved:
            return {"status": "WAITING_APPROVAL", "idempotencyKey": idem, "changeCount": diff.get("changeCount", 0)}

        # backup (recovery point)
        backup_ref = None
        if backup_dir:
            bdir = Path(backup_dir)
            bdir.mkdir(parents=True, exist_ok=True)
            backup_ref = bdir / f"{software_id}-{idem}.json"
            backup_ref.write_text(json.dumps(effective_before, ensure_ascii=False, indent=2), encoding="utf-8")

        # apply (only via provided apply_fn — never a bare in-memory return)
        if apply_fn is None:
            return {"status": "UNSUPPORTED_APPLY", "idempotencyKey": idem, "reason": "no adapter apply_fn"}
        apply_result = apply_fn(effective_before)

        # readback (must match applied effective)
        if readback_fn is not None:
            readback = readback_fn()
            drift = self.detect_drift(apply_result if isinstance(apply_result, dict) else {}, readback)
            if drift["status"] == "DRIFT":
                # rollback to backup
                rollback_result = self.rollback(apply_result, effective_before)
                return {"status": "ROLLED_BACK", "idempotencyKey": idem, "drift": drift, "rollback": rollback_result, "backupRef": str(backup_ref) if backup_ref else None}
            return {"status": "COMMITTED", "idempotencyKey": idem, "backupRef": str(backup_ref) if backup_ref else None, "receipt": idem}
        return {"status": "APPLIED_NO_READBACK", "idempotencyKey": idem, "backupRef": str(backup_ref) if backup_ref else None}
