#!/usr/bin/env python3
"""Verify source-pinned GitHub Actions and safe dependency-source metadata."""
from __future__ import annotations

import re
from pathlib import Path

ACTION_RE = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)(?:\s+#\s*(v[^\s]+))?\s*$")
PINNED_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")
UNSAFE_PIPE_RE = re.compile(r"(?:curl|wget)[^\n|]*\|\s*(?:sh|bash)\b", re.IGNORECASE)


def verify(root: Path) -> list[str]:
    errors: list[str] = []
    workflows = sorted((root / ".github" / "workflows").glob("*.y*ml"))
    if not workflows:
        return ["no GitHub workflow files found"]
    action_count = 0
    for workflow in workflows:
        text = workflow.read_text(encoding="utf-8")
        if UNSAFE_PIPE_RE.search(text):
            errors.append(f"{workflow}: network installer pipe is forbidden")
        for line_number, line in enumerate(text.splitlines(), 1):
            if "uses:" not in line:
                continue
            match = ACTION_RE.match(line)
            if not match:
                errors.append(f"{workflow}:{line_number}: malformed uses metadata")
                continue
            action, version = match.groups()
            if not PINNED_RE.fullmatch(action):
                errors.append(f"{workflow}:{line_number}: action must use a full commit SHA: {action}")
            if not version or not version.startswith("v"):
                errors.append(f"{workflow}:{line_number}: pinned action needs a version comment")
            action_count += 1
    return errors if errors else []


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    errors = verify(root)
    if errors:
        for error in errors:
            print(f"SUPPLY_CHAIN_FAIL {error}")
        return 1
    workflows = len(list((root / ".github" / "workflows").glob("*.y*ml")))
    actions = sum(
        1
        for workflow in (root / ".github" / "workflows").glob("*.y*ml")
        for line in workflow.read_text(encoding="utf-8").splitlines()
        if "uses:" in line
    )
    print(f"SUPPLY_CHAIN_PASS workflows={workflows} actions={actions} source=pinned-sha")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
