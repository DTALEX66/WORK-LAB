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
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


BLOCK_PREFIX = "PROJECT DATA BOUNDARY BLOCKED:"
SHELL_CONTROL = re.compile(r"(?:;|&&|\|\||(?<!\|)\|(?!\|)|\n|\r)")

WRAPPER_NAME = "hermes-project-data.py"
SUBCOMMANDS = {"init", "check", "policy", "cleanup", "run", "kanban"}


def canonical_wrapper(raw: str) -> bool:
    normalized = raw.replace("\\", "/")
    if normalized in {"$HERMES_HOME/bin/hermes-project-data.py", "${HERMES_HOME}/bin/hermes-project-data.py"}:
        return True
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        return False
    home = os.environ.get("HERMES_HOME")
    if home:
        expected = (Path(home) / "bin" / WRAPPER_NAME).resolve()
        try:
            return candidate.resolve(strict=True) == expected
        except (OSError, RuntimeError):
            return False
    return False


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
    try:
        argv = shlex.split(command, posix=True)
    except ValueError:
        return "terminal command quoting is invalid."
    if len(argv) < 4:
        return "invoke hermes-project-data.py with the wrapper executable and arguments."
    if Path(argv[0]).name.lower() not in {"python", "python3", "python.exe", "python3.exe"}:
        return "the wrapper executable must be invoked by Python."
    wrapper = Path(argv[1]).name.lower()
    if wrapper != WRAPPER_NAME:
        return "the command executable must be hermes-project-data.py, not a textual mention."
    if not canonical_wrapper(argv[1]):
        return "the wrapper path must be the canonical deployed Hermes wrapper, not a fake same-name executable."
    if "--project" not in argv or argv[argv.index("--project") + 1 : argv.index("--project") + 2] != ["."]:
        return "the wrapper must use --project . so it is pinned to terminal.workdir."
    project_index = argv.index("--project")
    subcommand_index = project_index + 2
    if len(argv) <= subcommand_index or argv[subcommand_index] not in SUBCOMMANDS:
        return "the wrapper subcommand must be init, check, policy, cleanup, run, or kanban."
    if argv[subcommand_index] == "run" and (len(argv) <= subcommand_index + 1 or argv[subcommand_index + 1] != "--"):
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
