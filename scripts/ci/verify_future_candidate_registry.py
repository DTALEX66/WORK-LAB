"""
future_candidate_registry validator (GOAL 31 / P2-06).

Machine-SSOT check for the deferred-candidate registry
`.project/governance/future-candidate-registry.json`.

Design (fail-open, like verify_contract_ssot.py):
- Validates every entry against `contracts/future-candidate-registry.schema.json`.
- Enforces the invariants a registry consumer relies on:
    * every candidate status is a known enum value;
    * every candidate has default_enabled == False unless status is PROMOTED
      (a PROMOTED candidate must have promotion evidence in the task register);
    * ids are unique and match ^FUT-\\d{3}$;
    * the registry declares no execution authority (governance.production_authorized
      must stay false) so a registry row can never be mistaken for a pilot grant.
- Schema-conformance failures are ADVISORY (exit 0 with warnings) so a new field
  in the registry never silently breaks the gate; structural integrity failures
  (duplicate ids, PROMOTED without authorization, non-boolean default_enabled)
  are HARD and fail the gate.

Exit codes: 0 = pass (or advisory warnings only); 1 = hard integrity violation.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REGISTRY = REPO / ".project/governance/future-candidate-registry.json"
SCHEMA = REPO / ".project/governance/contracts/future-candidate-registry.schema.json"

STATUS_ENUM = {"DEFERRED", "PILOT_CANDIDATE", "PILOT", "PROMOTED", "REJECTED"}
ID_RE = re.compile(r"^FUT-\d{3}$")
REQUIRED = [
    "id", "name", "role", "source", "license", "windows_support",
    "native_overlap", "integration_mode", "permissions", "data_boundary",
    "status", "default_enabled", "pilot_trigger", "promotion_criteria",
    "rejection_reason", "last_verified_at",
]


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    hard_errors: list[str] = []
    warnings: list[str] = []

    if not REGISTRY.exists():
        hard_errors.append("registry missing: " + REGISTRY.name)
    else:
        reg = load_json(REGISTRY)

        if reg.get("schemaVersion") != "work-lab/future-candidate-registry/v1":
            warnings.append(f"schemaVersion={reg.get('schemaVersion')!r} (expected v1)")

        gov = reg.get("governance", {})
        if gov.get("production_authorized") is not False:
            hard_errors.append(
                "governance.production_authorized must stay false (registry grants no pilot authority)"
            )
        if gov.get("default_enabled") is not False:
            hard_errors.append(
                "governance.default_enabled must stay false (no candidate auto-enabled)"
            )

        seen_ids: set[str] = set()
        for c in reg.get("candidates", []):
            cid = c.get("id", "<no-id>")
            if not ID_RE.match(cid):
                hard_errors.append(f"candidate {cid}: id does not match ^FUT-\\d{{3}}$")
            if cid in seen_ids:
                hard_errors.append(f"duplicate candidate id {cid}")
            seen_ids.add(cid)

            missing = [k for k in REQUIRED if k not in c]
            if missing:
                warnings.append(f"{cid}: missing fields {missing}")

            if c.get("status") not in STATUS_ENUM:
                hard_errors.append(f"{cid}: status {c.get('status')!r} not in {sorted(STATUS_ENUM)}")

            de = c.get("default_enabled")
            if not isinstance(de, bool):
                hard_errors.append(f"{cid}: default_enabled must be boolean, got {type(de).__name__}")
            elif de and c.get("status") != "PROMOTED":
                hard_errors.append(
                    f"{cid}: default_enabled=true is only allowed when status=PROMOTED"
                )

            if c.get("status") == "PROMOTED":
                task_card = c.get("task_card")
                if not task_card:
                    hard_errors.append(
                        f"{cid}: PROMOTED requires a task_card path (promotion evidence in the register)"
                    )
                elif REPO.exists():
                    tc = REPO / task_card
                    if not tc.exists():
                        hard_errors.append(f"{cid}: task_card path missing: {task_card}")

    # schema conformance is advisory
    if SCHEMA.exists():
        try:
            import jsonschema  # type: ignore
            schema = load_json(SCHEMA)
            reg = load_json(REGISTRY)
            errs = sorted(jsonschema.Draft202012Validator(schema).iter_errors(reg), key=str)
            for e in errs:
                warnings.append(f"schema: {e.message}")
        except Exception as exc:  # jsonschema absent or registry unreadable
            warnings.append(f"schema conformance skipped ({exc.__class__.__name__})")

    if warnings:
        print("FUTURE_CANDIDATE_REGISTRY_ADVISORY")
        for w in warnings:
            print("  - " + w)

    if hard_errors:
        print("FUTURE_CANDIDATE_REGISTRY_INTEGRITY_FAIL")
        for e in hard_errors:
            print("  ! " + e)
        return 1

    print("FUTURE_CANDIDATE_REGISTRY_PASS candidates=%d" % len(load_json(REGISTRY).get("candidates", [])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
