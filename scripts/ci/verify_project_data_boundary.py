#!/usr/bin/env python3
"""Verify the single project-local runtime/evidence path policy."""
from __future__ import annotations

import json
from pathlib import Path

EXPECTED = {
    "runtimeRoot": ".hermes/task-runtime",
    "taskArtifactsRoot": ".hermes/task-artifacts",
    "canonicalEvidenceRoot": "80-evidence",
}


def verify(root: Path) -> list[str]:
    errors: list[str] = []
    contract_path = root / ".project/governance" / "project-data-boundary.json"
    projects_path = root / ".project/governance" / "projects.json"
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        projects = json.loads(projects_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"unreadable: {exc}"]
    for key, value in EXPECTED.items():
        if contract.get(key) != value:
            errors.append(f"contract {key} must be {value}")
    if contract.get("platformNeutral") is not True:
        errors.append("platformNeutral must be true")
    if ".work-lab" not in contract.get("legacyAliases", []):
        errors.append("legacy .work-lab alias must be explicitly input-only")
    if not any(line.strip() == ".hermes/" for line in (root / ".gitignore").read_text(encoding="utf-8").splitlines()):
        errors.append(".hermes/ must be ignored")
    if not any(line.strip() == "80-evidence/" for line in (root / ".gitignore").read_text(encoding="utf-8").splitlines()):
        errors.append("80-evidence/ must be ignored")
    if projects.get("generatedData", {}).get("evidencePath") != "80-evidence":
        errors.append("projects generatedData.evidencePath must use 80-evidence")
    if projects.get("generatedData", {}).get("runtimeRoot") != EXPECTED["runtimeRoot"]:
        errors.append("projects generatedData.runtimeRoot must use .hermes/task-runtime")
    if projects.get("generatedData", {}).get("taskArtifactsPath") != EXPECTED["taskArtifactsRoot"]:
        errors.append("projects generatedData.taskArtifactsPath must use .hermes/task-artifacts")
    if projects.get("forbiddenRoots") != ["E:\\"]:
        errors.append("projects forbiddenRoots must preserve E: protection")
    return errors


def main() -> int:
    errors = verify(Path(__file__).resolve().parents[2])
    if errors:
        for error in errors:
            print(f"PROJECT_DATA_BOUNDARY_FAIL {error}")
        return 1
    print("PROJECT_DATA_BOUNDARY_PASS runtime=.hermes/task-runtime evidence=80-evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
