# -*- coding: utf-8 -*-
"""GitHub review accelerator (WL-DSH / GitHub Delivery Accelerator).

One-shot PR review preflight for managed repos: pull PR metadata (mergeable,
checks), optionally run the local quality gate as a pre-merge signal, and
emit a review recommendation (approve/block + reasons). Read-only; never
merges or approves automatically.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from github_common import MANAGED_REPOS, request

WORKFLOW_MODULE = Path(r"D:\All projects\WORK-LAB\packages\client-neutral-core")


def _run_local_gate(repo: str) -> dict:
    """Run the local quality gate as a pre-merge signal (only for WORK-LAB)."""
    if repo != "DTALEX66/WORK-LAB":
        return {"applicable": False, "note": "local gate is WORK-LAB-specific"}
    try:
        r = subprocess.run(
            ["python", str(WORKFLOW_MODULE / "scripts/workflow/run_quality_gate.py"), "verify"],
            capture_output=True, text=True, timeout=600,
        )
        out = r.stdout + r.stderr
        passed = "QUALITY_GATE_PASS" in out
        return {
            "applicable": True,
            "passed": passed,
            "exit_code": r.returncode,
            "gates": out.split("gates=")[-1].splitlines()[0][:200] if "gates=" in out else "",
        }
    except Exception as e:
        return {"applicable": True, "passed": False, "error": str(e)}


def review(repo: str, pr_number: int, local_gate: bool = True) -> dict:
    pr = request("GET", f"/pulls/{pr_number}", repo=repo)
    mergeable = pr.get("mergeable")
    mergeable_state = pr.get("mergeable_state")
    checks = request("GET", f"/commits/{pr['head']['sha']}/check-runs", repo=repo)
    runs = checks.get("check_runs", [])
    statuses = {}
    for run in runs:
        statuses[run["name"]] = run.get("conclusion") or run.get("status")

    # recommendation
    reasons = []
    check_ok = all(c in ("success", "neutral", "skipped") for c in statuses.values()) if statuses else None
    if mergeable is False:
        reasons.append("mergeable=false (conflict)")
    if mergeable_state not in ("clean", "draft"):
        reasons.append(f"mergeable_state={mergeable_state}")
    if check_ok is False:
        reasons.append("check-runs not all success")

    local = _run_local_gate(repo) if local_gate else {}
    if local.get("applicable") and not local.get("passed"):
        reasons.append("local quality gate FAILED")

    approved = mergeable is True and mergeable_state == "clean" and check_ok is not False and (not local.get("applicable") or local.get("passed"))
    return {
        "repo": repo,
        "pr": pr_number,
        "title": pr.get("title", "")[:80],
        "head_sha": pr["head"]["sha"][:12],
        "mergeable": mergeable,
        "mergeable_state": mergeable_state,
        "checks": statuses,
        "local_gate": local,
        "recommendation": "APPROVE" if approved else "BLOCK",
        "reasons": reasons,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="GitHub review accelerator")
    p.add_argument("--repo", required=True, help="repo (owner/name)")
    p.add_argument("--pr", type=int, required=True, help="PR number")
    p.add_argument("--no-local-gate", action="store_true")
    args = p.parse_args(argv)

    result = review(args.repo, args.pr, local_gate=not args.no_local_gate)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["recommendation"] == "APPROVE" else 1


if __name__ == "__main__":
    sys.exit(main())
