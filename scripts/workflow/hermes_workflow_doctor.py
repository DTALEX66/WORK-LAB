#!/usr/bin/env python3
"""Redacted Hermes + CC Switch + Codex workflow diagnosis.

Default mode checks structure and reachability only. ``--live`` additionally
runs real provider and Codex execution smokes; only live markers prove execution.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

from switch_model import DEEPSEEK_MODEL, GPT_MODEL


def configure_console_output() -> None:
    """Keep a diagnostic report running on legacy Windows code pages."""

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")


SECRET_PATTERNS = [
    (re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{16,}", re.I), "Bearer [REDACTED]"),
    (re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"), "jwt-[REDACTED]"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "github_pat_[REDACTED]"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"), "gh_[REDACTED]"),
    (re.compile(r"npm_[A-Za-z0-9]{20,}"), "npm_[REDACTED]"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "xox-[REDACTED]"),
    (re.compile(r"sk-[A-Za-z0-9_-]{8,}"), "sk-[REDACTED]"),
    (
        re.compile(
            r"(?i)([\"'])(access[_-]?token|refresh[_-]?token|id[_-]?token|bearer[_-]?token|api[_-]?key|secret|password)\1(\s*[:=]\s*)([\"'])[^\"']+\4"
        ),
        r"\1\2\1\3\4[REDACTED]\4",
    ),
    (
        re.compile(
            r"(?i)(access[_-]?token|refresh[_-]?token|id[_-]?token|bearer[_-]?token|api[_-]?key|secret|password)\s*[:=]\s*[\"']?[^\s,}\]\"']+"
        ),
        r"\1=[REDACTED]",
    ),
]


def redact(text: str) -> str:
    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def run(command: list[str], *, timeout: int = 30, cwd: Path | None = None) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        return completed.returncode, redact((completed.stdout or "").strip())
    except Exception as exc:
        return 124, f"{type(exc).__name__}: {exc}"


def print_command(label: str, command: list[str], *, timeout: int = 30, max_lines: int = 20) -> tuple[int, str]:
    code, output = run(command, timeout=timeout)
    status = "OK" if code == 0 else f"WARN exit={code}"
    print(f"[{status}] {label}")
    lines = output.splitlines()
    for line in lines[:max_lines]:
        print("  " + line)
    if len(lines) > max_lines:
        print(f"  ... ({len(lines) - max_lines} more lines)")
    return code, output


def has_exact_marker(output: str, marker: str) -> bool:
    """Accept only a standalone response line, never a marker embedded in an echoed prompt."""

    return any(line.strip() == marker for line in output.splitlines())


def marker_smoke(label: str, command: list[str], marker: str, *, timeout: int = 120, cwd: Path | None = None) -> bool:
    code, output = run(command, timeout=timeout, cwd=cwd)
    passed = code == 0 and has_exact_marker(output, marker)
    print(f"[{'OK' if passed else 'FAIL'}] {label}: marker={marker!r}, exit={code}")
    if not passed and output:
        for line in output.splitlines()[-8:]:
            print("  " + line)
    return passed


def port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1.0):
            return True
    except OSError:
        return False


def hermes_home() -> Path:
    if os.environ.get("HERMES_HOME"):
        return Path(os.environ["HERMES_HOME"])
    if os.name == "nt":
        root = os.environ.get("LOCALAPPDATA")
        return Path(root) / "hermes" if root else Path.home() / "AppData/Local/hermes"
    return Path.home() / ".hermes"


def hermes_managed_node() -> Path | None:
    """Return Hermes' bundled Node before consulting the ambient PATH.

    Windows often has several unrelated Node installations.  The workflow's
    desktop build and MCP wrappers are intentionally owned by Hermes' bundled
    runtime, so reporting whichever `node` happens to appear first on PATH is
    misleading and can hide a working Hermes installation.
    """

    home = hermes_home()
    candidates = [home / "node" / "node.exe", home / "node" / "bin" / "node"]
    return next((candidate for candidate in candidates if candidate.exists()), None)


def codex_candidates() -> list[Path]:
    """Prefer the desktop/plugin binary; PATH wrappers may lag behind it."""

    candidates = [
        Path.home() / ".codex/plugins/.plugin-appserver/codex.exe",
        Path.home() / "AppData/Local/OpenAI/Codex/bin/codex.exe",
    ]
    path_binary = shutil.which("codex")
    if path_binary:
        candidates.append(Path(path_binary))
    result: list[Path] = []
    for candidate in candidates:
        if candidate.exists() and candidate not in result:
            result.append(candidate)
    return result


def resolve_live_codex_workspace(project_root: Path, requested: Path | None) -> Path:
    """Return a project-local runtime parent for the ephemeral Codex smoke repo."""

    supplied = project_root.resolve()
    result = subprocess.run(
        ["git", "-C", str(supplied), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise SystemExit("--live Codex smoke must run from a Git project root")
    # Git yields a canonical working-tree spelling on Windows, avoiding a mix
    # of 8.3 and long path aliases in containment checks.
    project = Path(result.stdout.strip()).resolve()
    if not os.path.samefile(supplied, project):
        raise SystemExit("--live Codex smoke must run from a Git project root")
    runtime = (project / ".hermes/task-runtime").resolve()
    candidate = requested if requested is not None else Path(".hermes/task-runtime")
    if not candidate.is_absolute():
        candidate = project / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(runtime)
    except ValueError as exc:
        raise SystemExit(
            "--codex-workdir must stay under the current project's .hermes/task-runtime"
        ) from exc
    return candidate


def main() -> int:
    configure_console_output()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
        help="run real GPT, DeepSeek and Codex execution smokes (network/model usage)",
    )
    parser.add_argument(
        "--codex-workdir",
        type=Path,
        metavar="PATH",
        help="project-local parent for the ephemeral Codex smoke repo (must be under .hermes/task-runtime)",
    )
    args = parser.parse_args()
    failures: list[str] = []

    print("Hermes workflow doctor (redacted)")
    print(f"HERMES_HOME={hermes_home()}")

    print("\n=== Hermes structure ===")
    if not shutil.which("hermes"):
        print("[FAIL] hermes command not found")
        return 1
    print_command("Hermes version", ["hermes", "--version"])
    print_command("Hermes config check", ["hermes", "config", "check"], timeout=60)
    print_command("Hermes auth inventory", ["hermes", "auth", "list"], max_lines=40)
    print_command("Hermes MCP inventory", ["hermes", "mcp", "list"], max_lines=20)

    print("\n=== Network / route structure ===")
    for port, role in (
        (7890, "CC Switch network proxy"),
        (15721, "CC Switch Codex router (optional; native Codex OAuth does not depend on it)"),
    ):
        print(f"[{'OK' if port_open(port) else 'WARN'}] {role} 127.0.0.1:{port} = {'open' if port_open(port) else 'closed'}")
    print_command(
        "DeepSeek HTTP reachability (HTTP 401 is reachable, not authenticated)",
        ["curl", "-sSI", "--max-time", "8", "https://api.deepseek.com"],
        timeout=12,
        max_lines=5,
    )
    if port_open(7890):
        print_command(
            "ChatGPT through proxy (HTTP 403 still proves only transport reachability)",
            ["curl", "-sSI", "--proxy", "http://127.0.0.1:7890", "--max-time", "12", "https://chatgpt.com"],
            timeout=15,
            max_lines=6,
        )

    print("\n=== Node / configured MCP ===")
    managed_node = hermes_managed_node()
    if managed_node:
        print_command("Hermes managed Node", [str(managed_node), "--version"])
    else:
        print_command("PATH Node (Hermes managed Node missing)", ["node", "--version"])
    print_command("Configured Context7", ['hermes', 'mcp', 'test', 'context7'], timeout=90)

    print("\n=== Codex structure ===")
    candidates = codex_candidates()
    versions: list[tuple[Path, str]] = []
    for candidate in candidates:
        code, output = print_command(f"Codex version ({candidate})", [str(candidate), "--version"])
        if code == 0:
            versions.append((candidate, output.strip()))
    if not candidates:
        print("[FAIL] Codex executable not found")
        failures.append("codex missing")
    elif len({version for _, version in versions}) > 1:
        print("[WARN] Codex version drift detected; plugin binary is the preferred execution path")

    print("[INFO] Codex private config is intentionally not inspected; use executable, listener and live smoke evidence.")

    if args.live:
        print("\n=== LIVE execution smokes ===")
        if not marker_smoke(
            "Hermes GPT OAuth",
            ["hermes", "chat", "-Q", "--provider", "openai-codex", "-m", GPT_MODEL, "-q", "Only reply OK_GPT_LIVE"],
            "OK_GPT_LIVE",
            timeout=180,
        ):
            failures.append("GPT live smoke")
        if not marker_smoke(
            "Hermes DeepSeek",
            ["hermes", "chat", "-Q", "--provider", "deepseek", "-m", DEEPSEEK_MODEL, "-q", "Only reply OK_DEEPSEEK_LIVE"],
            "OK_DEEPSEEK_LIVE",
            timeout=180,
        ):
            failures.append("DeepSeek live smoke")
        if candidates:
            workspace = resolve_live_codex_workspace(Path.cwd(), args.codex_workdir)
            workspace.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="codex-live-", dir=workspace) as raw:
                workdir = Path(raw)
                run(["git", "init", "-q"], cwd=workdir)
                if not marker_smoke(
                    "Codex exec",
                    [str(candidates[0]), "exec", "--sandbox", "read-only", "Only reply OK_CODEX_LIVE"],
                    "OK_CODEX_LIVE",
                    timeout=180,
                    cwd=workdir,
                ):
                    failures.append("Codex live smoke")
    else:
        print("\n[INFO] structural checks do not prove provider execution; rerun with --live for real smokes")

    print("\n=== Summary ===")
    if failures:
        print("[FAIL] " + ", ".join(failures))
        return 1
    if args.live:
        print("[OK] structural checks and live execution markers passed")
    else:
        print("[OK] structural checks completed; provider execution remains unverified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
