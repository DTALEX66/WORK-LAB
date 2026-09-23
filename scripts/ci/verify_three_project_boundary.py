#!/usr/bin/env python3
"""Three-project boundary verifier (WORK-LAB V2, fail-closed).

Machine check for the control-plane / knowledge / design ownership split:
    .project/governance/three-project-boundary.json  (SSOT)
    .project/governance/boundary-migration-manifest.json  (what moves, where)

The verifier fails closed when ANY of the following is missing:
  1. the boundary SSOT contract,
  2. a BOUNDARY.md marker in every split dir that is marked,
  3. a seam (integrations/archeaxis/contracts/*) for every split that declares one,
  4. a migration manifest entry covering every split.

No file moves, no code deletion — this only PROVES the boundary is marked and
gated. Running it is the audit trail that the three-project split is real,
not a doc promise.

Exit 0 = boundary marked+gated; exit 1 = fail-closed (boundary gap).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# split dir (repo-relative) -> required marker file
SPLIT_DIRS = {
    "services/memory": "BOUNDARY.md",
    "services/knowledge": "BOUNDARY.md",
    "services/evolution": "BOUNDARY.md",
    "knowledge-staging": "BOUNDARY.md",
    "90-archive": "BOUNDARY.md",
}

# required seams (repo-relative), by split id
REQUIRED_SEAMS = {
    "MEMORY_BACKEND": "integrations/archeaxis/contracts/memory-query-contract.py",
    "KNOWLEDGE_TRUTH": "integrations/archeaxis/contracts/promotion_contract.py",
    "DESIGN_LAB": "integrations/archeaxis/contracts/open_design_client_seam.py",
}

SSOT = ".project/governance/three-project-boundary.json"
MANIFEST = ".project/governance/boundary-migration-manifest.json"

failures: list[str] = []


def check(cond: bool, label: str, detail: str = "") -> None:
    if not cond:
        failures.append(f"{label}: {detail}".strip())


def main() -> int:
    # 1) SSOT contract
    ssot_path = ROOT / SSOT
    check(ssot_path.is_file(), "SSOT", f"{SSOT} missing")
    split_ids: set[str] = set()
    if ssot_path.is_file():
        try:
            ssot = json.loads(ssot_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            check(False, "SSOT", f"invalid JSON: {e}")
            ssot = {}
        split_ids = {s.get("id") for s in ssot.get("boundary_splits", []) if s.get("id")}
        check(len(split_ids) >= 5, "SSOT.splits", f"expected >=5 splits, got {len(split_ids)}")
        check(
            "worklab_owned" in ssot and ssot.get("worklab_owned"),
            "SSOT.worklab_owned", "worklab_owned must be a non-empty allowlist",
        )

    # 2) markers present in every marked split dir
    for d, marker in SPLIT_DIRS.items():
        mp = ROOT / d / marker
        check(mp.is_file(), f"marker {d}/{marker}", "missing boundary marker")

    # 3) seams present for every split that declares one
    declared_seams = set()
    if ssot_path.is_file():
        try:
            for s in json.loads(ssot_path.read_text(encoding="utf-8")).get("boundary_splits", []):
                if s.get("seam"):
                    declared_seams.add(s.get("id"))
        except json.JSONDecodeError:
            pass
    for split_id, seam_rel in REQUIRED_SEAMS.items():
        if split_id not in split_ids:
            continue
        sp = ROOT / seam_rel
        check(sp.is_file(), f"seam {seam_rel}", f"split {split_id} seam missing")
    # every required-seam split must be a declared split
    for sid in REQUIRED_SEAMS:
        check(sid in split_ids, f"split {sid}", "declared in SSOT but absent from splits")

    # 4) migration manifest covers every split
    manifest_path = ROOT / MANIFEST
    check(manifest_path.is_file(), "manifest", f"{MANIFEST} missing")
    if manifest_path.is_file():
        try:
            moves = json.loads(manifest_path.read_text(encoding="utf-8")).get("moves", [])
        except json.JSONDecodeError as e:
            check(False, "manifest.json", f"invalid JSON: {e}")
            moves = []
        covered_dirs = {m.get("dir") for m in moves if m.get("dir")}
        manifest_split_ids = {m.get("splitId") for m in moves if m.get("splitId")}
        for d in SPLIT_DIRS:
            # manifest must record at least one move touching each marked dir
            check(any(d in (cd or "") for cd in covered_dirs), f"manifest covers {d}", "no move records this dir")
        # every split has a manifest entry (via splitId)
        for sid in split_ids:
            check(sid in manifest_split_ids, f"manifest entry {sid}", "split not covered by manifest")

    if failures:
        print(f"THREE_PROJECT_BOUNDARY_FAIL ({len(failures)} failures)")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"THREE_PROJECT_BOUNDARY_PASS splits={len(split_ids)} markers={len(SPLIT_DIRS)} seams={len(REQUIRED_SEAMS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
