#!/usr/bin/env python3
"""Run the root `tests/ci/` governance suite as a discovery-driven gate.

WHY THIS EXISTS (2026-10-01). The canonical gate ran 43 `tests/workflow-assistance/`
modules and **zero** of the 22 `tests/ci/` ones. That is a real blind spot, and it was
not hypothetical: while reconciling the independent audit I edited the shared
`taskpacks/current/error-ledger.json`, ran the canonical gate to green, pushed, and CI
failed on `scripts/ci/verify_error_ledger.py` — a verifier the local gate never
invoked. Two defects (an invalid `phase` enum value and the original-failure
`exit_code` being 0) were only found by CI. Running this module catches that whole
class locally, before a push.

DISCOVERY, NOT A LIST. The suite is globbed, so a new `tests/ci/test_*.py` is covered
the moment it lands instead of being silently skipped — the exact failure mode above.
Only a module this gate declares as POST_MERGE is excluded, and an exclusion must be
justified in EXCLUSIONS and have its reason asserted below, so the list cannot quietly
grow into "whatever was failing".

Read-only. Exit 0 = all pass, 1 = a failure, 2 = discovery problem.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS_CI = ROOT / "tests" / "ci"

# Modules that assert POST-MERGE repository state and therefore cannot pass on an
# unpublished branch. Each entry must carry a reason naming the state it asserts.
EXCLUSIONS = {
    "test_exact_tree_review.py": (
        "asserts report['head'] == report['originMain'] and a clean worktree, i.e. "
        "post-merge state; on a PR branch HEAD is necessarily ahead of origin/main, "
        "so this is a release-time re-check, not a pre-merge gate. It is deliberately "
        "NOT referenced by the CI integration job for the same reason."
    ),
}


def _discover() -> list[Path]:
    if not TESTS_CI.is_dir():
        raise SystemExit(f"CI_ROOT_GOVERNANCE_DISCOVERY_FAIL: {TESTS_CI} missing")
    modules = sorted(p for p in TESTS_CI.glob("test_*.py") if p.is_file())
    if not modules:
        raise SystemExit(
            "CI_ROOT_GOVERNANCE_DISCOVERY_FAIL: no tests/ci/test_*.py discovered; the "
            "suite cannot silently be empty"
        )
    return modules


def main() -> int:
    modules = _discover()
    for name in EXCLUSIONS:
        if Path(name).name not in {m.name for m in modules}:
            raise SystemExit(
                f"CI_ROOT_GOVERNANCE_EXCLUSION_STALE: {name} is excluded but no longer "
                "exists; drop the exclusion so the list stays meaningful"
            )

    ran = 0
    failures: list[str] = []
    for module in modules:
        if module.name in EXCLUSIONS:
            continue
        completed = subprocess.run(
            [sys.executable, str(module)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        ran += 1
        if completed.returncode != 0:
            tail = (completed.stdout + completed.stderr).strip().splitlines()[-6:]
            failures.append(f"{module.name} (rc={completed.returncode})")
            for line in tail:
                failures.append(f"    {line}")

    if failures:
        print(f"CI_ROOT_GOVERNANCE_FAIL ran={ran} failed={len(failures)}")
        for line in failures:
            print(f"  {line}")
        return 1

    skipped = len(modules) - ran
    print(
        f"CI_ROOT_GOVERNANCE_PASS modules={ran} excluded_post_merge={skipped} "
        f"discovered={len(modules)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
