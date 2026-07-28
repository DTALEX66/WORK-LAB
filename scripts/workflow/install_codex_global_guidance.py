#!/usr/bin/env python
"""Safely install the portable global Codex baseline without overwriting user rules."""
from __future__ import annotations

import argparse
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "templates" / "agent-rules" / "CODEX_GLOBAL_AGENTS.md"


def is_link_or_reparse_point(path: Path) -> bool:
    """Reject links so this installer cannot redirect writes outside Codex Home."""
    try:
        status = path.lstat()
    except FileNotFoundError:
        return False
    reparse_flag = getattr(os, "FILE_ATTRIBUTE_REPARSE_POINT", 0x0400)
    return path.is_symlink() or bool(getattr(status, "st_file_attributes", 0) & reparse_flag)


def linked_ancestor(path: Path) -> Path | None:
    """Return the first link/reparse point from a target up to its volume root."""
    current = path.absolute()
    while True:
        if is_link_or_reparse_point(current):
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def plan(codex_home: Path) -> tuple[int, str, Path]:
    """Return a non-destructive action code, marker, and target path."""
    target = codex_home / "AGENTS.md"
    override = codex_home / "AGENTS.override.md"
    if override.exists():
        return 2, "CODEX_GUIDANCE_BLOCKED_OVERRIDE", target
    if target.exists():
        return 1, "CODEX_GUIDANCE_EXISTS", target
    return 0, "CODEX_GUIDANCE_READY", target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Install the Workflow-assistance Codex global baseline only when no user rule file exists."
    )
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--apply", action="store_true", help="create AGENTS.md only when it is absent")
    args = parser.parse_args(argv)

    codex_home = args.codex_home.expanduser().absolute()
    unsafe_ancestor = linked_ancestor(codex_home)
    if unsafe_ancestor is not None:
        print(f"CODEX_GUIDANCE_BLOCKED_LINK target={codex_home} ancestor={unsafe_ancestor}")
        print("No existing Codex rule file was changed.")
        return 0
    code, marker, target = plan(codex_home)
    print(f"{marker} target={target}")
    if code:
        print("No existing Codex rule file was changed.")
        return 0
    if not args.apply:
        print("Run again with --apply to create the global baseline.")
        return 0

    content = TEMPLATE.read_text(encoding="utf-8")
    codex_home.mkdir(parents=True, exist_ok=True)
    unsafe_ancestor = linked_ancestor(target)
    if unsafe_ancestor is not None:
        print(f"CODEX_GUIDANCE_BLOCKED_LINK target={target} ancestor={unsafe_ancestor}")
        print("No existing Codex rule file was changed.")
        return 0
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print(f"CODEX_GUIDANCE_EXISTS target={target}")
        print("No existing Codex rule file was changed.")
        return 0
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(content)
    print(f"CODEX_GUIDANCE_WRITTEN target={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
