#!/usr/bin/env python3
"""Fail-closed verification for the root contract catalog and owned schemas."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, SchemaError

EXPECTED = {
    "module-profile": "root-governance",
    "source-ledger": "root-governance",
    "capability-conformance": "root-governance",
    "task-card": "workflow",
    "runtime-lock": "workflow",

    "domain-pack": "workflow",
    "evidence-envelope": "root-governance",
    "release-manifest": "root-governance",
    "adapter-capability": "workflow",
    "action-plan": "workflow",
    "task-ledger-event": "workflow",
    "rule-asset": "workflow",
    "skill-package": "workflow",
    "growth-candidate": "workflow",
    "observer-event": "observer",
    "observer-pricing": "observer",
    "data-quality": "observer",
    "dashboard-projection": "observer",

    "archive-manifest": "root-governance",
    "project-profile": "workflow",
    "gate-registry": "workflow",
    "gate-plan": "workflow",
    "blocker": "workflow",
    "ci-observation": "workflow",
    "evidence-manifest": "workflow",
    "model-policy": "workflow",
    "memory-record": "workflow",
    "rule-drift": "workflow",
}
CANONICAL_SCHEMA_PREFIXES = {
    "module-profile": ("00-governance/",),
    "source-ledger": ("00-governance/",),
    "capability-conformance": ("00-governance/",),
    "task-card": ("10-workflow/",),
    "runtime-lock": ("00-governance/",),

    "domain-pack": ("10-workflow/",),
    "evidence-envelope": ("00-governance/",),
    "release-manifest": ("00-governance/",),
    "adapter-capability": ("10-workflow/",),
    "action-plan": ("10-workflow/",),
    "task-ledger-event": ("10-workflow/",),
    "rule-asset": ("10-workflow/",),
    "skill-package": ("10-workflow/",),
    "growth-candidate": ("10-workflow/",),
    "observer-event": ("30-observer/",),
    "observer-pricing": ("30-observer/",),
    "data-quality": ("30-observer/",),
    "dashboard-projection": ("30-observer/",),

    "archive-manifest": ("00-governance/",),
    "project-profile": ("10-workflow/",),
    "gate-registry": ("10-workflow/",),
    "gate-plan": ("10-workflow/",),
    "blocker": ("10-workflow/",),
    "ci-observation": ("10-workflow/",),
    "evidence-manifest": ("10-workflow/",),
    "model-policy": ("10-workflow/",),
    "memory-record": ("10-workflow/",),
    "rule-drift": ("10-workflow/",),
}


def verify_catalog(root: Path) -> list[str]:
    errors: list[str] = []
    catalog_path = root / "00-governance" / "contracts" / "contract-catalog.json"
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"catalog unreadable: {exc}"]

    entries = catalog.get("contracts")
    if not isinstance(entries, list):
        return ["catalog contracts must be an array"]

    by_id: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            errors.append("catalog entry missing string id")
            continue
        contract_id = entry["id"]
        if contract_id in by_id:
            errors.append(f"duplicate contract id: {contract_id}")
        by_id[contract_id] = entry

    if set(by_id) != set(EXPECTED):
        errors.append(f"catalog ids must equal {sorted(EXPECTED)}; got {sorted(by_id)}")

    seen_paths: set[str] = set()
    for contract_id, owner in EXPECTED.items():
        entry = by_id.get(contract_id)
        if entry is None:
            continue
        if entry.get("owner") != owner:
            errors.append(f"{contract_id}: owner must be {owner}")
        schema_path = entry.get("schemaPath")
        if not isinstance(schema_path, str) or not schema_path:
            errors.append(f"{contract_id}: schemaPath is required")
            continue
        normalized = schema_path.replace("\\", "/")
        if normalized.startswith("/") or normalized.startswith("../") or "/../" in normalized:
            errors.append(f"{contract_id}: schemaPath escapes repository: {schema_path}")
            continue
        if normalized in seen_paths:
            errors.append(f"duplicate schemaPath: {normalized}")
        seen_paths.add(normalized)
        if not normalized.startswith(CANONICAL_SCHEMA_PREFIXES[contract_id]):
            errors.append(f"{contract_id}: schemaPath is outside its canonical module boundary: {schema_path}")
        path = root / Path(normalized)
        if not path.is_file():
            errors.append(f"{contract_id}: missing schema {normalized}")
            continue
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
        except (OSError, UnicodeError, json.JSONDecodeError, SchemaError) as exc:
            errors.append(f"{contract_id}: invalid JSON Schema: {exc}")
            continue
        if not isinstance(schema.get("$id"), str) or not schema["$id"]:
            errors.append(f"{contract_id}: schema $id is required")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    errors = verify_catalog(root)
    if errors:
        for error in errors:
            print(f"CONTRACT_CATALOG_FAIL {error}")
        return 1
    print(f"CONTRACT_CATALOG_PASS contracts={len(EXPECTED)} schemas={len(EXPECTED)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
