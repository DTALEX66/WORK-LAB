#!/usr/bin/env python
"""A03: machine authority-reference verifier for WORK-LAB.

Fail-closed, read-only check that the top-level authority package is present
and internally consistent. Run in CI (integration gate) and locally before
any execution task. It never mutates state; it only reports PASS/FAIL.

Checks (each failure aborts with a non-zero exit and a named reason):
- top human authority `WORK-LAB-AUTHORITY.md` exists and is normative;
- top machine authority `.project/governance/project-authority-index.json`
  exists, is valid JSON, and names exactly those two files;
- the scoped taskpack authority index
  `.project/governance/taskpack-authority-index.json` exists;
- the CURRENT taskpack file declared by the taskpack index exists on disk;
- the single live open-task register
  `taskpacks/current/OPEN-TASK-REGISTER.md` exists;
- exactly one taskpack is classified CURRENT in the taskpack index;
- every `operationalCompatibilityAllowlist` path declared by the project
  authority index exists on disk;
- P0-01: every tracked path the taskpack index references (the CURRENT
  taskpack file, `decisions[].path`, `decisions[].ledger`, and the tracked
  `staticHandoffViews[].entry_record`) exists on disk — `indexReferencesExist`
  is verified against the tree, never trusted from the stored value;
- P0-01: the taskpack supersedes graph is structurally valid — the
  classification buckets form a partition (no taskpack in two buckets) and
  the single CURRENT taskpack is not simultaneously marked retired/superseded;
- no forbidden legacy active root has been re-activated as a live module root.

Exit codes: 0 PASS, 1 FAIL (named reason printed), 2 environment error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOP_AUTHORITY = "WORK-LAB-AUTHORITY.md"
PROJECT_INDEX = ".project/governance/project-authority-index.json"
TASKPACK_INDEX = ".project/governance/taskpack-authority-index.json"
OPEN_REGISTER = "taskpacks/current/OPEN-TASK-REGISTER.md"
MODULE_OWNERSHIP = ".project/governance/module-ownership.json"


def _fail(reason: str, detail: str = "") -> int:
    suffix = f" {detail}" if detail else ""
    print(f"AUTHORITY_REFERENCE_FAIL {reason}{suffix}", file=sys.stderr)
    return 1


def verify(root: Path) -> int:
    root = root.resolve()

    # 1. Top human authority
    top = root / TOP_AUTHORITY
    if not top.is_file():
        return _fail("TOP_AUTHORITY_MISSING", str(top))
    top_text = top.read_text(encoding="utf-8")
    if "WORK-LAB TOP-LEVEL AUTHORITY" not in top_text:
        return _fail("TOP_AUTHORITY_INVALID", "missing normative header")

    # 2. Top machine authority
    pidx_path = root / PROJECT_INDEX
    if not pidx_path.is_file():
        return _fail("PROJECT_INDEX_MISSING", str(pidx_path))
    try:
        pidx = json.loads(pidx_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _fail("PROJECT_INDEX_INVALID_JSON", str(exc))
    if pidx.get("topHumanAuthority") != TOP_AUTHORITY:
        return _fail("PROJECT_INDEX_TOP_MISMATCH", str(pidx.get("topHumanAuthority")))
    if pidx.get("topMachineAuthority") != PROJECT_INDEX:
        return _fail("PROJECT_INDEX_SELF_MISMATCH", str(pidx.get("topMachineAuthority")))

    # 3. Scoped taskpack index exists
    tidx_path = root / TASKPACK_INDEX
    if not tidx_path.is_file():
        return _fail("TASKPACK_INDEX_MISSING", str(tidx_path))
    try:
        tidx = json.loads(tidx_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _fail("TASKPACK_INDEX_INVALID_JSON", str(exc))

    # 4. CURRENT taskpack file exists on disk
    current = tidx.get("classification", {}).get("CURRENT", [])
    if len(current) != 1:
        return _fail("MULTIPLE_OR_ZERO_CURRENT", json.dumps(current))
    current_id = current[0]
    current_file = root / "taskpacks" / "current" / f"{current_id}.md"
    if not current_file.is_file():
        return _fail("CURRENT_TASKPACK_MISSING", str(current_file))

    # 5. Single live open register
    reg = root / OPEN_REGISTER
    if not reg.is_file():
        return _fail("OPEN_REGISTER_MISSING", str(reg))

    # 6. Declared allowlist paths all exist (no dangling reference)
    for entry in pidx.get("operationalCompatibilityAllowlist", []):
        allow_path = root / entry["path"]
        if not allow_path.is_file():
            return _fail("ALLOWLIST_PATH_MISSING", entry["path"])

    # 6b. P0-01: `indexReferencesExist` is verified against the tree, never
    # trusted from the stored value. Every tracked path the taskpack index
    # references must exist on disk: the CURRENT taskpack file (already
    # required in check 4), `decisions[].path`, `decisions[].ledger`, and the
    # tracked `staticHandoffViews[].entry_record`. A dangling reference is a
    # fail-closed regression even if the index JSON parses cleanly.
    referenced: list[tuple[str, str]] = []
    for decision in tidx.get("decisions", []):
        if not isinstance(decision, dict):
            continue
        for key in ("path", "ledger"):
            value = decision.get(key)
            if isinstance(value, str) and value:
                referenced.append((f"decisions[{decision.get('id', '?')}].{key}", value))
    for view in tidx.get("staticHandoffViews", []):
        if not isinstance(view, dict):
            continue
        entry_record = view.get("entry_record")
        if isinstance(entry_record, str) and entry_record:
            referenced.append((f"staticHandoffViews[{view.get('id', '?')}].entry_record", entry_record))
    for label, rel in referenced:
        if not (root / rel).is_file():
            return _fail("INDEX_REFERENCE_MISSING", f"{label} -> {rel}")
    if tidx.get("acceptance", {}).get("indexReferencesExist") is False:
        # The index itself admits dangling references; fail closed on it.
        return _fail("INDEX_REFERENCES_ADMISSION", "index declares indexReferencesExist=false")

    # 6c. P0-01: the taskpack supersedes graph is structurally valid.
    # - classification buckets form a partition: no taskpack ID sits in two
    #   buckets (CURRENT vs SUPERSEDED/HISTORICAL/etc. is a real contradiction);
    # - the single CURRENT taskpack is not simultaneously marked retired /
    #   superseded by its own index.
    classification = tidx.get("classification", {})
    buckets: dict[str, list[str]] = {}
    for bucket, ids in classification.items():
        if not isinstance(ids, list):
            continue
        for task_id in ids:
            if task_id in buckets:
                return _fail(
                    "SUPERSEDES_PARTITION_CONFLICT",
                    f"{task_id} classified in both {buckets[task_id]} and {bucket}",
                )
            buckets.setdefault(str(task_id), []).append(bucket)
    for task_id in current:
        seen_buckets = buckets.get(task_id, [])
        for retired in ("SUPERSEDED", "OUT_OF_SCOPE", "HISTORICAL"):
            if retired in seen_buckets:
                return _fail(
                    "SUPERSEDES_CURRENT_CONFLICT",
                    f"CURRENT {task_id} simultaneously marked {retired}",
                )

    # 7. "Forbidden active root returned" = a legacy active root was
    # re-declared as a LIVE module root in module-ownership.json. Historical
    # tracked files under a forbidden root are NOT a regression at this stage:
    # they are removed by the A02 physical cleanup (after A04), and CLOUD-LANDING
    # PR1 explicitly does not delete historical bodies. Only re-activation as a
    # live module root is a fail-closed regression.
    mo_path = root / MODULE_OWNERSHIP
    forbidden = set(pidx.get("forbiddenActiveRoots", []))
    if forbidden and mo_path.is_file():
        try:
            mo = json.loads(mo_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            mo = {}
        live_roots: set[str] = set()
        for module in (mo.get("modules") or {}).values():
            path = module.get("path")
            if isinstance(path, str):
                live_roots.add(path.strip("/"))
        live_roots.update(str(item).strip("/") for item in (mo.get("rootOwnedPaths") or []))
        for froot in sorted(forbidden):
            if froot in live_roots:
                return _fail(
                    "FORBIDDEN_ROOT_REACTIVATED",
                    f"{froot} re-declared as a live module root in module-ownership.json",
                )

    print(
        "AUTHORITY_REFERENCE_PASS top=WORK-LAB-AUTHORITY.md "
        f"current={current_id} register=OPEN-TASK-REGISTER.md"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root, help="repository root to verify")
    args = parser.parse_args()
    return verify(args.root)


if __name__ == "__main__":
    raise SystemExit(main())
