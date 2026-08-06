#!/usr/bin/env python
"""Fail-closed verifier for the client-neutral Workflow JSON Schema contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

EXPECTED = {
    "client-adapter.schema.json": ("workflow/client-adapter/v1", {"schema_version", "interface", "entries"}),
    "adapter-registry.schema.json": ("workflow/adapter-registry/v1", {"schema_version", "interface", "entries"}),
    "task-card.schema.json": ("work-lab/task-card/v1", {"schema_version", "id", "title", "scope", "action", "acceptance"}),
    "domain-pack.schema.json": ("workflow/domain-pack/v1", {"schema_version", "pack_id", "version", "display_name", "description", "capabilities", "entrypoints", "evidence_policy", "safety"}),
    "action-plan.schema.json": ("workflow/action-plan/v1", {"schema_version", "plan_id", "status", "target", "steps", "approval", "rollback"}),
    "run-event.schema.json": ("workflow/run-event/v1", {"schema_version", "event_id", "run_id", "task_id", "phase", "status", "timestamp"}),
    "evidence-envelope.schema.json": ("workflow/evidence-envelope/v1", {"schema_version", "evidence_id", "task_id", "state", "level", "source", "artifacts", "redaction"}),
    "error.schema.json": ("workflow/error/v1", {"schema_version", "error_code", "class", "retryable", "external_write_retryable", "message"}),
    "task-ledger.schema.json": ("workflow/task-ledger/v1", {"schema_version", "tasks"}),
    "observer-event.schema.json": ("workflow/observer-event/v1", {"schema_version", "sequence", "event_id", "run_id", "task_id", "event_type", "occurred_at", "source", "payload"}),
    "rule-asset.schema.json": ("workflow/rule-asset/v1", {"schema_version", "id", "version", "origin", "scope", "risk", "status"}),
    "skill-package.schema.json": ("workflow/skill-package/v1", {"schema_version", "id", "version", "source", "packageDigest", "status"}),
    "growth-candidate.schema.json": ("workflow/growth-candidate/v1", {"schema_version", "candidateId", "origin", "classification", "status", "risk"}),
}
FORBIDDEN_KEYS = {"api_key", "apikey", "authorization", "password", "secret", "token", "provider", "model"}


def _walk_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return {str(key).lower() for key in value} | {item for child in value.values() for item in _walk_keys(child)}
    if isinstance(value, list):
        return {item for child in value for item in _walk_keys(child)}
    return set()


def verify_schema_dir(schema_dir: Path) -> list[str]:
    errors: list[str] = []
    for name, (schema_version, required) in EXPECTED.items():
        path = schema_dir / name
        if not path.is_file():
            errors.append(f"missing {name}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(data)
        except (OSError, UnicodeError, json.JSONDecodeError, SchemaError) as exc:
            errors.append(f"{name}: invalid JSON Schema: {exc}")
            continue
        if data.get("type") != "object":
            errors.append(f"{name}: type must be object")
        if data.get("properties", {}).get("schema_version", {}).get("const") != schema_version:
            errors.append(f"{name}: schema_version must be {schema_version}")
        missing = sorted(required - set(data.get("required", [])))
        if missing:
            errors.append(f"{name}: missing required contract fields: {', '.join(missing)}")
        sensitive = sorted(_walk_keys(data) & FORBIDDEN_KEYS)
        if sensitive:
            errors.append(f"{name}: forbidden credential/provider/model keys: {', '.join(sensitive)}")
    examples = schema_dir / "examples"
    valid_path = examples / "valid-action-plan.json"
    invalid_path = examples / "invalid-action-plan.json"
    action_schema = schema_dir / "action-plan.schema.json"
    if action_schema.is_file() and valid_path.is_file() and invalid_path.is_file():
        schema = json.loads(action_schema.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        valid = json.loads(valid_path.read_text(encoding="utf-8"))
        invalid = json.loads(invalid_path.read_text(encoding="utf-8"))
        valid_errors = list(validator.iter_errors(valid))
        invalid_errors = list(validator.iter_errors(invalid))
        if valid_errors:
            errors.append(f"valid-action-plan.json: positive control failed: {valid_errors[0].message}")
        if not invalid_errors:
            errors.append("invalid-action-plan.json: negative control unexpectedly passed")
    else:
        errors.append("missing JSON Schema positive/negative instance controls")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema-dir", type=Path, default=Path(__file__).resolve().parents[2] / "schemas" / "workflow")
    args = parser.parse_args()
    errors = verify_schema_dir(args.schema_dir.resolve())
    if errors:
        for error in errors:
            print(f"CORE_SCHEMA_CONTRACT_FAIL {error}")
        return 1
    print(f"CORE_SCHEMA_CONTRACT_PASS schemas={len(EXPECTED)} positive_control=PASS negative_control=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
