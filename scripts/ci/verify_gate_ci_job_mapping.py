#!/usr/bin/env python3
"""W07 (2026-10-17): prove the CI-job <-> local-gate mapping, in both directions.

Why
---
The profile says which local gate a change requires. The workflows say which jobs actually run -- and their
job IDs are what branch protection aggregates. Before this checker, the two sides agreed by *resemblance*:
the five heavy gates happened to share their IDs with the workflow jobs, and four additional required jobs
(`schema-fixtures`, `observer-readonly`, `config-compiler`, `capsule-verify`) were covered by nothing at all,
invisibly. A rename on either side, or a new job, would have changed what CI requires without changing what a
writer's local run suggests -- and nothing would have said so.

What it enforces
----------------
1. every profile gate names a `ci_job` that exists as a job ID in one of the workflows;
2. every job ID in either workflow is accounted for -- claimed by a gate, or declared `structural_jobs` (the
   plan/aggregate machinery), or declared under `additional_required_jobs` (a required job with no gate);
3. no stale declarations: every declared job exists, and a declared `local_route` names a tracked file;
4. `local_route: null` is ALLOWED and is the point -- it makes a CI-only check visible. Silence is what this
   rejects, not a gap.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / ".project" / "governance" / "work-lab.project-profile.yaml"
WORKFLOWS = (ROOT / ".github" / "workflows" / "work-lab-gate.yml",
             ROOT / ".github" / "workflows" / "wlr-060-gates.yml")


def tracked_files(root: Path) -> set[str]:
    result = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", check=False)
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def workflow_jobs(paths: tuple[Path, ...]) -> dict[str, str]:
    """job id -> the workflow file it lives in. The id is what `needs:` and branch protection use; the
    display `name:` is deliberately ignored -- `workflow` is displayed as "workflow-assistance", and a
    mapping written against the display name would look right and match nothing."""
    jobs: dict[str, str] = {}
    for path in paths:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for job_id in (data.get("jobs") or {}):
            jobs[str(job_id)] = path.name
    return jobs


def audit(profile: dict[str, Any], jobs: dict[str, str], tracked: set[str]) -> list[str]:
    problems: list[str] = []
    gates = profile.get("gates") or {}
    ci = profile.get("ci") or {}
    structural = ci.get("structural_jobs") or {}
    additional = ci.get("additional_required_jobs") or {}

    claimed: dict[str, str] = {}
    for gate_id, gate in gates.items():
        job = (gate or {}).get("ci_job")
        if not job:
            problems.append(f"gate {gate_id!r} names no ci_job; the CI side of this gate is unstated")
            continue
        if job not in jobs:
            problems.append(f"gate {gate_id!r} claims ci_job {job!r}, which is not a job in any workflow")
            continue
        if job in claimed and claimed[job] != gate_id:
            problems.append(f"ci_job {job!r} is claimed by both {claimed[job]!r} and {gate_id!r}")
        claimed[job] = gate_id

    for job_id in sorted(jobs):
        if job_id in claimed or job_id in structural or job_id in additional:
            continue
        problems.append(f"workflow job {job_id!r} ({jobs[job_id]}) is claimed by no gate and declared nowhere; "
                        f"a required job a writer cannot see from a local run")

    for job_id in sorted(list(structural) + list(additional)):
        if job_id not in jobs:
            problems.append(f"profile declares job {job_id!r}, which no workflow defines (stale declaration)")

    for job_id, entry in sorted(additional.items()):
        entry = entry or {}
        route = entry.get("local_route", "MISSING")
        if route == "MISSING":
            problems.append(f"additional job {job_id!r} declares no local_route; use null with a reason "
                            f"instead of omitting the field, so 'CI-only' is a statement and not a gap")
            continue
        if route is None:
            if not entry.get("note"):
                problems.append(f"additional job {job_id!r} declares local_route: null without a note")
            continue
        # A route is a command; the first token that looks like a repo path decides whether it is tracked.
        candidates = [token for token in str(route).split() if "/" in token]
        if not candidates:
            problems.append(f"additional job {job_id!r} local_route {route!r} names no repo path")
            continue
        target = candidates[0].lstrip("./")
        if target not in tracked:
            problems.append(f"additional job {job_id!r} local_route points at {target!r}, which is not tracked")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)

    profile = yaml.safe_load(PROFILE.read_text(encoding="utf-8")) or {}
    jobs = workflow_jobs(WORKFLOWS)
    if not jobs:
        print("GATE_CI_JOB_MAPPING_FAIL no jobs found in the workflows; a checker that sees nothing "
              "reports nothing")
        return 1
    problems = audit(profile, jobs, tracked_files(args.root))
    print(f"GATE_CI_JOB_MAPPING jobs={len(jobs)} gates={len(profile.get('gates') or {})} "
          f"structural={len((profile.get('ci') or {}).get('structural_jobs') or {})} "
          f"additional={len((profile.get('ci') or {}).get('additional_required_jobs') or {})}")
    for problem in problems:
        print(f"  {problem}")
    if problems:
        print(f"GATE_CI_JOB_MAPPING_FAIL problems={len(problems)}")
        return 1
    print("GATE_CI_JOB_MAPPING_PASS every job is claimed or declared, every gate names a real job")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
