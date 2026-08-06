#!/usr/bin/env python3
"""Verify typed cross-module dependencies and runtime decoupling."""
from __future__ import annotations

import json
from pathlib import Path

EXPECTED_MODULES = {
    "workflow-assistance": "10-workflow/workflow-assistance",
    "open-design": "20-design/open-design",
    "work-lab-observer": "30-observer/work-lab-observer",
}
TYPES = {"governance", "runtime", "build", "handoff", "observed-by", "fixture", "archive-of"}


def verify(root: Path) -> list[str]:
    errors: list[str] = []
    path = root / "00-governance" / "module-dependencies.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"unreadable: {exc}"]
    modules = data.get("modules")
    if not isinstance(modules, dict) or set(modules) != set(EXPECTED_MODULES):
        return ["modules must exactly match the three canonical modules"]
    if set(data.get("dependencyTypes", [])) != TYPES:
        errors.append("dependencyTypes must include v2 governance/runtime/build/handoff/observed-by/fixture/archive-of")
    for module_id, expected_path in EXPECTED_MODULES.items():
        entry = modules[module_id]
        if entry.get("path") != expected_path:
            errors.append(f"{module_id}: path mismatch")
        observed_by = entry.get("observedBy")
        if not isinstance(observed_by, list):
            errors.append(f"{module_id}: observer relation missing")
        elif module_id != "work-lab-observer" and "work-lab-observer" not in observed_by:
            errors.append(f"{module_id}: observer relation missing")
        elif module_id == "work-lab-observer" and observed_by:
            errors.append("work-lab-observer: observer cannot observe itself")
        for dependency in entry.get("dependencies", []):
            target = dependency.get("module")
            if target not in EXPECTED_MODULES or target == module_id:
                errors.append(f"{module_id}: invalid dependency target {target}")
            types = set(dependency.get("types", []))
            if not types or not types <= TYPES:
                errors.append(f"{module_id}->{target}: invalid dependency type")
            if "runtime" in types:
                errors.append(f"{module_id}->{target}: runtime coupling is not allowed")
    if data.get("runtimeEdges") != []:
        errors.append("runtimeEdges must remain empty until separately approved")
    if data.get("policy", {}).get("observedByIsReadOnly") is not True:
        errors.append("observedBy must be read-only")
    return errors


def main() -> int:
    errors = verify(Path(__file__).resolve().parents[2])
    if errors:
        for error in errors:
            print(f"MODULE_DEPENDENCIES_FAIL {error}")
        return 1
    print("MODULE_DEPENDENCIES_PASS modules=3 runtime_edges=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
