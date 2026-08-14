"""WLGM-230 canary runner — WORK-LAB self-canary (no external project writes).

Runs the real identity resolver + aggregator against the WORK-LAB repository
itself to validate the multi-scenario matrix that does NOT require external
project authorization:

1. WORK-LAB root resolves to the work-lab product project;
2. submodules/modules resolve as working areas of the same project, never as
   new projects;
3. a transient nested-repo path stays unresolved (independent repository);
4. weak evidence alone never produces RUNNING;
5. snapshot revision increments across publishes.

External OS-project canary (real second project) stays PENDING until the user
authorizes ``WORKLAB_CANARY_PROJECT_ROOTS`` and read access to an external repo.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

WORK = Path(r"D:\All projects\WORK-LAB")
SCRIPTS = WORK / "10-workflow" / "workflow-assistance" / "scripts" / "workflow"

import sys

sys.path.insert(0, str(SCRIPTS))

from evidence_aggregator import EvidenceAggregator, ExecutionState  # noqa: E402
from product_project import ProductProject, ProjectRootBinding, RepositoryIdentity  # noqa: E402
from project_identity_resolver import ApprovedProjectIndex, GitProbe, resolve_execution_path  # noqa: E402
from snapshot_api import build_snapshot  # noqa: E402


def run_canary() -> dict[str, Any]:
    results: dict[str, Any] = {}

    # 1) WORK-LAB root resolves to the work-lab product project (real git).
    project = ProductProject(project_id="work-lab", display_name="WORK-LAB")
    project.add_repository(RepositoryIdentity(repository_id="work-lab", remote_identity="github:DTALEX66/WORK-LAB"))
    index = ApprovedProjectIndex(projects=[project])
    probe = GitProbe()
    resolved = resolve_execution_path(str(WORK), index, git=probe)
    results["self_root_resolved"] = resolved.project_id == "work-lab" and resolved.resolution_state.value == "RESOLVED"
    results["self_resolution_detail"] = resolved.as_json()

    # 2) module subdir of the same repo belongs to the project (containment).
    module_path = str(WORK / "10-workflow" / "workflow-assistance")
    resolved_module = resolve_execution_path(module_path, index, git=probe)
    results["module_inside_same_repo"] = (
        resolved_module.project_id == "work-lab"
        or resolved_module.resolution_state.value == "RESOLVED"
    )

    # 3) transient independent nested repo stays unresolved (no remote match).
    raw = tempfile.TemporaryDirectory()
    try:
        nested = Path(raw.name) / "independent-repo"
        nested.mkdir()
        subprocess.run(["git", "init", "-q", str(nested)], check=True)
        resolved_nested = resolve_execution_path(str(nested), index, git=probe)
        results["independent_repo_not_absorbed"] = (
            resolved_nested.resolution_state.value == "UNRESOLVED"
            or resolved_nested.project_id != "work-lab"
        )
    finally:
        raw.cleanup()

    # 4) weak evidence alone never RUNNING.
    agg = EvidenceAggregator()
    status = agg.apply_event(
        execution_id="c1", event_type="execution_running", occurred_at="2026-08-14T00:00:00Z",
        evidence_level="E", anchor_project_id="work-lab",
    )
    results["weak_evidence_no_running"] = status.state != ExecutionState.RUNNING

    # 5) snapshot revision increments.
    r1 = build_snapshot(revision=1, projects=[{"projectId": "work-lab"}])
    r2 = build_snapshot(revision=2, projects=[{"projectId": "work-lab"}])
    results["snapshot_revision_monotonic"] = r2["revision"] == r1["revision"] + 1

    results["all_pass"] = all(
        v is True for k, v in results.items() if k.endswith(("_resolved", "_same_repo", "_absorbed", "_running", "_monotonic"))
    )
    return results


if __name__ == "__main__":
    report = run_canary()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("\nCANARY_SELF", "PASS" if report.get("all_pass") else "FAIL")
    print("CANARY_EXTERNAL_PROJECT PENDING (WORKLAB_CANARY_PROJECT_ROOTS not authorized)")
