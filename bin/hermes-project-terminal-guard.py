#!/usr/bin/env python
"""Fail-closed Hermes pre-tool hook for project-scoped terminal execution.

The hook receives Hermes' JSON hook payload on stdin and only permits the
``terminal`` tool when the call declares a Git-project workdir and invokes the
installed ``hermes-project-data.py`` wrapper for that same workdir.  It is a
policy gate for normal Hermes tool calls, not an operating-system sandbox:
processes deliberately launched outside Hermes or programs that write hard-
coded absolute paths can still escape OS-level containment.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


BLOCK_PREFIX = "PROJECT DATA BOUNDARY BLOCKED:"
SHELL_CONTROL = re.compile(r"(?:;|&&|\|\||(?<!\|)\|(?!\|)|\n|\r)")
PROJECT_CURRENT = re.compile(r"(?:^|\s)--project\s+(?:[\"']?\.[\\/]?[\"']?)(?=\s|$)")
WRAPPER = re.compile(r"(?:^|[\s\"'])[^\s\"']*hermes-project-data\.py(?=[\s\"'])", re.IGNORECASE)
SUBCOMMAND = re.compile(r"(?:^|\s)(?:init|check|policy|cleanup|run|kanban)(?=\s|$)")


def block(reason: str) -> int:
    print(json.dumps({"action": "block", "message": f"{BLOCK_PREFIX} {reason}"}))
    return 0


def project_root(workdir: str) -> Path | None:
    try:
        candidate = Path(workdir).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    result = subprocess.run(
        ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        return None
    try:
        return Path(result.stdout.strip()).resolve(strict=True)
    except (OSError, RuntimeError):
        return None


def validate(payload: dict[str, Any]) -> str | None:
    if payload.get("tool_name") != "terminal":
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return "terminal input is missing."

    workdir = tool_input.get("workdir")
    if not isinstance(workdir, str) or not workdir.strip():
        return "terminal calls must declare an explicit Git-project workdir."
    if project_root(workdir.strip()) is None:
        return "workdir must resolve inside an existing Git project."

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return "terminal command is missing."
    if SHELL_CONTROL.search(command):
        return "shell chaining/redirection is forbidden; invoke one wrapper command only."
    if not WRAPPER.search(command):
        return "invoke hermes-project-data.py --project . <subcommand> instead of a raw terminal command."
    if not PROJECT_CURRENT.search(command):
        return "the wrapper must use --project . so it is pinned to terminal.workdir."
    if not SUBCOMMAND.search(command):
        return "the wrapper subcommand must be init, check, policy, cleanup, run, or kanban."
    if re.search(r"(?:^|\s)run(?=\s|$)", command) and " -- " not in command:
        return "wrapper run requires -- before the child command."
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        return block("hook payload is not valid JSON.")
    if not isinstance(payload, dict):
        return block("hook payload is not an object.")
    reason = validate(payload)
    return block(reason) if reason else 0


if __name__ == "__main__":
    raise SystemExit(main())
