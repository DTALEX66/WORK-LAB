#!/usr/bin/env python
"""Fail-closed project-local runtime-data boundary for agent task commands.

The wrapper scopes standard temporary, cache, log, artifact, pip, and Python
bytecode paths to ``<git-root>/.hermes/task-runtime``. It intentionally cannot
sandbox a command that explicitly writes an arbitrary absolute path; callers
must use this wrapper and project rules must deny external output paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Mapping, Sequence


class ProjectDataBoundaryError(RuntimeError):
    """Raised when task runtime data cannot be safely contained."""


class RuntimeLayout:
    def __init__(self, project_root: Path, paths: dict[str, Path], env: dict[str, str]) -> None:
        self.project_root = project_root
        self.paths = paths
        self.env = env


def discover_project_root(start: Path | str = ".") -> Path:
    start_path = Path(start).resolve()
    result = subprocess.run(
        ["git", "-C", str(start_path), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ProjectDataBoundaryError(f"not inside a Git project: {start_path}")
    return Path(result.stdout.strip()).resolve()


def require_contained(project_root: Path, candidate: Path) -> Path:
    root = project_root.resolve()
    resolved = candidate.resolve(strict=False)
    if not resolved.is_relative_to(root):
        raise ProjectDataBoundaryError(f"path escapes project root: {candidate}")
    return resolved


def require_ignored(project_root: Path, relative_path: Path) -> None:
    result = subprocess.run(
        ["git", "-C", str(project_root), "check-ignore", "-q", "--no-index", relative_path.as_posix()],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ProjectDataBoundaryError(
            f"project runtime root must be git-ignored before use: {relative_path.as_posix()}"
        )


def prepare_layout(start: Path | str = ".") -> RuntimeLayout:
    project_root = discover_project_root(start)
    hermes_root = require_contained(project_root, project_root / ".hermes")
    runtime_root = require_contained(project_root, hermes_root / "task-runtime")
    require_ignored(project_root, runtime_root.relative_to(project_root) / ".containment-probe")
    paths = {
        "root": runtime_root,
        "tmp": runtime_root / "tmp",
        "cache": runtime_root / "cache",
        "logs": runtime_root / "logs",
        "artifacts": runtime_root / "artifacts",
        "pip-cache": runtime_root / "pip-cache",
        "pycache": runtime_root / "pycache",
    }
    for path in paths.values():
        require_contained(project_root, path)
        path.mkdir(parents=True, exist_ok=True)
    env = {
        "TMP": str(paths["tmp"]),
        "TEMP": str(paths["tmp"]),
        "TMPDIR": str(paths["tmp"]),
        "XDG_CACHE_HOME": str(paths["cache"]),
        "PIP_CACHE_DIR": str(paths["pip-cache"]),
        "PYTHONPYCACHEPREFIX": str(paths["pycache"]),
        "UV_CACHE_DIR": str(paths["cache"] / "uv"),
        "NPM_CONFIG_CACHE": str(paths["cache"] / "npm"),
        "npm_config_cache": str(paths["cache"] / "npm"),
        "YARN_CACHE_FOLDER": str(paths["cache"] / "yarn"),
        "PLAYWRIGHT_BROWSERS_PATH": str(paths["cache"] / "playwright-browsers"),
        "CARGO_TARGET_DIR": str(paths["cache"] / "cargo-target"),
        "MYPY_CACHE_DIR": str(paths["cache"] / "mypy"),
        "RUFF_CACHE_DIR": str(paths["cache"] / "ruff"),
        "PRE_COMMIT_HOME": str(paths["cache"] / "pre-commit"),
        "HERMES_KANBAN_HOME": str(hermes_root),
        "HERMES_PROJECT_RUNTIME_ROOT": str(paths["root"]),
        "HERMES_PROJECT_ARTIFACTS": str(paths["artifacts"]),
        "HERMES_PROJECT_LOGS": str(paths["logs"]),
    }
    return RuntimeLayout(project_root, paths, env)


def write_task_data_policy(layout: RuntimeLayout) -> Path:
    """Write an ignored, project-local policy without touching source files."""
    policy_path = layout.project_root / ".hermes" / "TASK_DATA_POLICY.md"
    require_contained(layout.project_root, policy_path)
    policy_path.write_text(
        """# Project-local task data policy

All task-scoped state belongs under this repository's `.hermes/` directory.

## Required locations

- queues and durable task state: `.hermes/tasks/` or `.hermes/sleep-mode/`
- plans and handoffs: `.hermes/plans/` and `.hermes/handoffs/`
- temporary command data: `.hermes/task-runtime/`
- durable verification evidence: `.hermes/task-artifacts/` or `.hermes/evidence/`
- Hermes project board: `.hermes/kanban/` (run through `hermes-project-data.py kanban`)

## Required launcher

Use `hermes-project-data.py --project . run -- <command>` for commands that can
write caches, logs, downloads, test output, or artifacts. It redirects temporary
and common tool caches to `.hermes/task-runtime/` and pins `HERMES_KANBAN_HOME`
to this project.

## Prohibited locations

Do not create project task caches, reports, scratch files, Kanban boards, or
review artifacts under the user home, Windows temporary directories, Desktop,
another project, or the global Hermes home. Hermes credentials, installation,
global session database, and scheduler configuration remain global platform state.

## Cleanup

Remove confirmed regenerable files from `.hermes/task-runtime/`; retain only
durable handoffs, task records, and evidence required for audit or recovery.
""",
        encoding="utf-8",
    )
    return policy_path


def prepare_command(
    layout: RuntimeLayout,
    command: Sequence[str],
    *,
    windows: bool | None = None,
    limit: int = 30_000,
) -> list[str]:
    """Keep known long Python inline commands below Windows CreateProcess limits.

    Generic executables have incompatible response-file syntaxes, so they fail
    closed with actionable guidance rather than silently retrying a broken command.
    """

    prepared = list(command)
    if not prepared:
        raise ProjectDataBoundaryError("run requires a command after --")
    on_windows = os.name == "nt" if windows is None else windows
    if not on_windows or len(subprocess.list2cmdline(prepared)) <= limit:
        return prepared
    executable = Path(prepared[0]).name.lower()
    if len(prepared) >= 3 and prepared[1] == "-c" and executable.startswith("python"):
        source = prepared[2]
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
        script = layout.paths["tmp"] / f"inline-command-{digest}.py"
        require_contained(layout.project_root, script)
        script.write_text(source, encoding="utf-8")
        return [prepared[0], str(script), *prepared[3:]]
    raise ProjectDataBoundaryError(
        "Windows command line exceeds safe limit; use the tool's response file/input-file option "
        "or place the payload under .hermes/task-runtime/"
    )


def run_command(
    layout: RuntimeLayout,
    command: Sequence[str],
    *,
    windows: bool | None = None,
    limit: int = 30_000,
) -> subprocess.CompletedProcess[str]:
    prepared = prepare_command(layout, command, windows=windows, limit=limit)
    env = os.environ.copy()
    env.update(layout.env)
    return subprocess.run(
        prepared,
        cwd=layout.project_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def run_kanban_command(layout: RuntimeLayout, command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Run the native Kanban CLI with its board root pinned to this project."""
    if not command:
        raise ProjectDataBoundaryError(
            "kanban requires arguments after --, for example: -- boards list"
        )
    hermes = shutil.which("hermes")
    if hermes is None:
        raise ProjectDataBoundaryError("native Hermes CLI is not available on PATH")
    env = os.environ.copy()
    env.update(layout.env)
    return subprocess.run(
        [hermes, "kanban", *command],
        cwd=layout.project_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def cleanup_runtime(layout: RuntimeLayout, *, include_caches: bool = False) -> dict[str, int]:
    """Remove only confirmed-regenerable project-local runtime data.

    Durable handoffs and verification evidence belong in ``.hermes/task-artifacts``
    and are intentionally outside this cleanup scope. By default dependency caches
    stay available for the next task; callers may explicitly include them.
    """
    names = ["tmp", "logs", "artifacts", "pycache"]
    if include_caches:
        names.extend(["cache", "pip-cache"])
    removed: dict[str, int] = {}
    for name in names:
        path = layout.paths[name]
        require_contained(layout.project_root, path)
        removed[name] = sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
        shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
    return removed


def layout_payload(layout: RuntimeLayout) -> Mapping[str, object]:
    return {
        "project_root": str(layout.project_root),
        "runtime_root": str(layout.paths["root"]),
        "paths": {name: str(path) for name, path in layout.paths.items()},
        "environment": layout.env,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".", help="any path inside the target Git project")
    parser.add_argument("--json", action="store_true", help="emit the contained layout as JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "check", "policy", "cleanup"):
        subparsers.add_parser(name, help="prepare/verify the project-local runtime root")
    subparsers.choices["cleanup"].add_argument(
        "--all-regenerable",
        action="store_true",
        help="also remove dependency/tool caches under task-runtime",
    )
    run_parser = subparsers.add_parser("run", help="run a command with local temporary/cache paths")
    run_parser.add_argument("args", nargs=argparse.REMAINDER, help="command to run; prefix with --")
    kanban_parser = subparsers.add_parser("kanban", help="run Hermes Kanban with project-local board storage")
    kanban_parser.add_argument("args", nargs=argparse.REMAINDER, help="Kanban arguments; prefix with --")
    args = parser.parse_args()
    try:
        layout = prepare_layout(args.project)
        if args.command == "init":
            write_task_data_policy(layout)
        if args.command in {"init", "check"}:
            payload = layout_payload(layout)
            print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else payload["runtime_root"])
            return 0
        if args.command == "policy":
            print(write_task_data_policy(layout))
            return 0
        if args.command == "cleanup":
            print(json.dumps(cleanup_runtime(layout, include_caches=args.all_regenerable), ensure_ascii=False))
            return 0
        command = args.args[1:] if args.args[:1] == ["--"] else args.args
        result = run_kanban_command(layout, command) if args.command == "kanban" else run_command(layout, command)
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return result.returncode
    except ProjectDataBoundaryError as exc:
        print(f"project-data-boundary: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
