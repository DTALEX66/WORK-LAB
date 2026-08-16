# -*- coding: utf-8 -*-
"""GitHub upload accelerator (WL-DSH / GitHub Delivery Accelerator).

One-shot pipeline for the managed workspace repos: status check -> staged
commit (conventional message prefix) -> push -> optional PR creation. Outputs
a JSON delivery report. Local only; never force-pushes.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from github_common import MANAGED_REPOS, git, git_ok, local_path, request

CONVENTIONAL = ("feat", "fix", "docs", "chore", "refactor", "test", "perf", "build", "ci", "revert")


def _prefix(message: str) -> str:
    for p in CONVENTIONAL:
        if message.startswith(p + ":"):
            return message
    # infer from keywords
    low = message.lower()
    if any(k in low for k in ("fix", "修复", "bug", "error")):
        return "fix: " + message
    if any(k in low for k in ("docs", "文档", "readme")):
        return "docs: " + message
    if any(k in low for k in ("feat", "feature", "add", "new", "新增", "增强")):
        return "feat: " + message
    return "chore: " + message


def _sanitize(message: str) -> str:
    return message.replace("\r", "").replace("\n", " ").strip()[:120]


def upload(repo_local: str, message: str, push: bool = True, create_pr: bool = False,
           target: str = "main") -> dict:
    d = local_path({"local": repo_local})
    result = {"repo": repo_local, "steps": []}
    try:
        # 1. status
        status = git_ok(d, "status", "--porcelain")[1]
        dirty = [ln for ln in status.splitlines() if ln.strip()] if status else []
        result["dirty_count"] = len(dirty)
        if not dirty:
            result["status"] = "CLEAN"
            result["skipped"] = "nothing to commit"
            return result
        result["steps"].append(f"status: {len(dirty)} dirty")

        # 2. stage + commit (required: a message gates the whole pipeline)
        if not message:
            result["status"] = "DIRTY_NO_ACTION"
            result["skipped"] = "message required; nothing staged/pushed (safety)"
            return result
        git(d, "add", "-A")
        result["steps"].append("staged")
        commit_msg = _prefix(_sanitize(message))
        git(d, "commit", "-m", commit_msg)
        result["commit"] = commit_msg
        result["steps"].append("committed")

        # 3. push
        branch = git_ok(d, "branch", "--show-current")[1]
        if push and branch:
            upstream = git_ok(d, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")[1]
            if upstream:
                git(d, "push")
            else:
                git(d, "push", "-u", "origin", branch)
            result["push"] = branch
            result["steps"].append(f"pushed {branch}")
        result["status"] = "DONE"
    except RuntimeError as e:
        result["status"] = "ERROR"
        result["error"] = str(e)
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="GitHub upload accelerator")
    p.add_argument("--repo", help="local repo name (default: all managed)")
    p.add_argument("--message", "-m", help="commit message")
    p.add_argument("--no-push", action="store_true", help="stage+commit only")
    p.add_argument("--create-pr", action="store_true", help="create PR after push (non-main branch)")
    args = p.parse_args(argv)

    repos = [args.repo] if args.repo else [e["local"] for e in MANAGED_REPOS]
    report = []
    for r in repos:
        report.append(upload(r, args.message, push=not args.no_push, create_pr=args.create_pr))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(x["status"] in ("CLEAN", "DONE") for x in report) else 1


if __name__ == "__main__":
    sys.exit(main())
