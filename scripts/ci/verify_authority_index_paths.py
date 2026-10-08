#!/usr/bin/env python3
"""Every path-shaped reference in the active authority index must resolve, or be declared with a reason.

The index is the navigation surface for the whole authority chain and nothing checked it. Measured on
2026-10-08, before any fix: section 2 named
`docs/current/workflow-assistance/workflow/official-plus-user-configuration-standard.md` while the file
on disk carries the date suffix this repo's own AGENTS.md uses, and section 3 sent readers to
`docs/handoffs/` and `docs/audit/` -- directories that do not exist since the 2026-09 convergence,
verified with `ls`. A prose rule that the tree contradicts is not a rule, and a pointer into a void is
worse than no pointer because the reader trusts the index.

A reference is path-shaped when the backticked token contains a separator. Two kinds are checked:
files (a known document/config suffix) and directories (a trailing slash). Bare filenames are prose --
`config-ownership.json` appears inside a sentence, and resolving it would mean guessing which copy the
author meant, which is not verification.

`--index` exists so this rule can be shown firing on a planted path without editing the real file.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_INDEX = Path("docs/current/workflow-assistance/workflow/active-authority-index.md")
FILE_REF = re.compile(r"`([^`\s]*/[^`\s]*\.(?:md|json|py|ts|tsx|yml|yaml|example|lock|txt))`")
DIR_REF = re.compile(r"`([^`\s]+/)`")

# References that are deliberately not repo paths, each with the measured reason. A declaration whose
# path later starts resolving is itself a failure, so this list cannot quietly grow into a hiding place.
# Measured empty on 2026-10-08: after the two section-2/section-3 corrections every reference in the
# index resolves, so the rule today is not holding anything back.
DECLARED_NON_PATHS: dict[str, str] = {}


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists() and (parent / "services").is_dir():
            return parent
    raise SystemExit("AUTHORITY_INDEX_PATHS_FAIL cannot locate WORK-LAB root")


def references(text: str) -> list[tuple[int, str, str]]:
    rows: list[tuple[int, str, str]] = []
    for number, line in enumerate(text.splitlines(), 1):
        for match in FILE_REF.finditer(line):
            rows.append((number, match.group(1), "file"))
        for match in DIR_REF.finditer(line):
            rows.append((number, match.group(1), "directory"))
    return rows


def resolves(root: Path, index: Path, ref: str, kind: str) -> bool:
    rel = ref.lstrip("/")  # a leading slash here means repo-root-relative, not a filesystem root
    for base in (root, index.parent, root / "docs" / "current"):
        candidate = base / rel
        if candidate.is_dir() if kind == "directory" else candidate.is_file():
            return True
    return False


def verdict(root: Path, index: Path, rows: list[tuple[int, str, str]]) -> tuple[list, list]:
    broken = [(n, r, k) for n, r, k in rows
              if r not in DECLARED_NON_PATHS and not resolves(root, index, r, k)]
    stale = [(n, r, k) for n, r, k in rows
             if r in DECLARED_NON_PATHS and resolves(root, index, r, k)]
    return broken, stale


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default=str(DEFAULT_INDEX))
    args = ap.parse_args()

    root = repo_root()
    index = Path(args.index)
    if not index.is_absolute():
        index = root / index
    if not index.is_file():
        print(f"AUTHORITY_INDEX_PATHS_FAIL missing {index}")
        return 1

    rows = references(index.read_text(encoding="utf-8"))
    if not rows:
        print(f"AUTHORITY_INDEX_PATHS_FAIL refs=0 in {index.as_posix()} -- the extractor matched "
              "nothing, which is a broken checker rather than a clean index")
        return 1

    broken, stale = verdict(root, index, rows)
    kinds = {}
    for _, _, kind in rows:
        kinds[kind] = kinds.get(kind, 0) + 1
    flag = "FAIL" if broken or stale else "PASS"
    print(f"AUTHORITY_INDEX_PATHS_{flag} index={index.as_posix()} refs={len(rows)} "
          f"files={kinds.get('file', 0)} directories={kinds.get('directory', 0)} "
          f"broken={len(broken)} declared={len(DECLARED_NON_PATHS)} "
          f"declared_but_resolves={len(stale)}")
    for number, ref, kind in broken:
        print(f"  line {number}: `{ref}` is not a {kind} anywhere under the repo root")
    for _, ref, _ in stale:
        print(f"  declared as a non-path but it now resolves: {ref} -- drop the declaration")
    return 1 if broken or stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
