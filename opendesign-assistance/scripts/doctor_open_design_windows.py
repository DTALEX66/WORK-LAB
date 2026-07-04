#!/usr/bin/env python
"""Diagnose a Windows Open Design + Codex + OPEN-DESIGN-Assistance setup.

The doctor is read-only. It reports presence/shape/version checks and never
prints OAuth tokens, API keys, or secret config values.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_MODEL = "gpt-5.5"
DEFAULT_PORTS = (5294, 5499)
DEFAULT_PERMISSION_ROOT = Path(r"D:\All projects")
LOCATION_ID = "loc_open_design_assistance"
PERMISSION_LOCATION_ID = "loc_all_projects"


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


def windows_home() -> Path:
    return Path(os.environ.get("USERPROFILE") or Path.home())


def default_config_path() -> Path:
    appdata = os.environ.get("APPDATA") or str(windows_home() / "AppData" / "Roaming")
    return Path(appdata) / "Open Design" / "namespaces" / "release-stable-win" / "data" / "app-config.json"


def default_open_design_exe() -> Path:
    return Path(r"D:\Programs\Open Design\Open Design.exe")


def default_codex_home() -> Path:
    return windows_home() / ".codex"


def read_json(path: Path) -> tuple[dict[str, Any] | None, str]:
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), "ok"
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report any parse failure.
        return None, f"invalid json: {exc}"


def read_toml(path: Path) -> tuple[dict[str, Any] | None, str]:
    if not path.exists():
        return None, "missing"
    try:
        return tomllib.loads(path.read_text(encoding="utf-8")), "ok"
    except Exception as exc:  # noqa: BLE001
        return None, f"invalid toml: {exc}"


def find_codex_bin(config: dict[str, Any] | None, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    configured = (((config or {}).get("agentCliEnv") or {}).get("codex") or {}).get("CODEX_BIN")
    if configured:
        return str(configured)
    for name in ("codex.cmd", "codex.exe", "codex"):
        found = shutil.which(name)
        if found:
            return found
    root = windows_home() / "AppData" / "Local" / "OpenAI" / "Codex" / "bin"
    if root.exists():
        for pattern in ("*/codex.exe", "*/codex.cmd"):
            found = sorted(root.glob(pattern), reverse=True)
            if found:
                return str(found[0])
    return None


def has_codex_login(codex_home: Path) -> bool:
    auth = codex_home / "auth.json"
    if not auth.exists():
        return False
    try:
        data = json.loads(auth.read_text(encoding="utf-8"))
    except Exception:
        return False
    if data.get("auth_mode") == "chatgpt":
        return True
    tokens = data.get("tokens") or {}
    return bool(tokens.get("access" + "_token"))


def run_version(exe: str, codex_home: Path) -> tuple[bool, str]:
    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    try:
        proc = subprocess.run([exe, "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, timeout=30)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    return proc.returncode == 0, proc.stdout.strip()


def port_open(port: int, timeout: float = 0.35) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False


def git_clean(project_root: Path) -> tuple[bool, str]:
    if not (project_root / ".git").exists():
        return False, "not a git repository"
    proc = subprocess.run(["git", "status", "--short", "--branch"], cwd=project_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    clean = proc.returncode == 0 and len(lines) == 1 and "origin/" in lines[0]
    return clean, proc.stdout.strip()


def norm(path: object) -> str:
    return str(path).replace("/", "\\").rstrip("\\").lower()


def discover_od_skill_roots(permission_root: Path) -> list[Path]:
    try:
        return sorted(path for path in permission_root.rglob(".od-skills") if path.is_dir())
    except OSError:
        return []


def powershell_read_dir(path: Path) -> tuple[bool, str]:
    env = os.environ.copy()
    env["OD_SKILLS_PATH"] = str(path)
    try:
        proc = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "$ErrorActionPreference='Stop'; Get-ChildItem -LiteralPath $env:OD_SKILLS_PATH -Force | Select-Object -First 1 -ExpandProperty Name",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            timeout=30,
        )
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    detail = (proc.stdout or b"").decode("utf-8", errors="replace").strip()
    if not detail:
        detail = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
    return proc.returncode == 0, detail or str(path)


def codex_root_checks(config: dict[str, Any], root: Path, label: str) -> tuple[Check, Check]:
    root_norm = norm(root)
    writable_roots = ((config.get("sandbox_workspace_write") or {}).get("writable_roots") or [])
    writable_ok = any(norm(item) == root_norm for item in writable_roots)

    projects = config.get("projects") or {}
    trusted = projects.get(str(root).lower()) or projects.get(str(root)) or {}
    trusted_ok = trusted.get("trust_level") == "trusted"
    return (
        Check(f"Codex {label} writable", writable_ok, str(root)),
        Check(f"Codex {label} trusted", trusted_ok, str(root)),
    )


def codex_permission_checks(codex_home: Path, permission_root: Path) -> list[Check]:
    config, status = read_toml(codex_home / "config.toml")
    if config is None:
        detail = f"{codex_home / 'config.toml'} ({status})"
        return [Check("Codex permission root writable", False, detail), Check("Codex permission root trusted", False, detail)]

    checks = list(codex_root_checks(config, permission_root, "permission root"))
    od_skill_roots = discover_od_skill_roots(permission_root)
    checks.append(Check(".od-skills directories discovered", bool(od_skill_roots), ", ".join(str(path) for path in od_skill_roots) or "none"))
    for path in od_skill_roots:
        checks.extend(codex_root_checks(config, path, ".od-skills root"))
        ok, detail = powershell_read_dir(path)
        checks.append(Check("PowerShell .od-skills read", ok, f"{path} -> {detail}"))
    return checks


def diagnose(args: argparse.Namespace) -> list[Check]:
    project_root = Path(args.project_root).resolve()
    permission_root = Path(args.permission_root).resolve()
    config_path = Path(args.config)
    open_design_exe = Path(args.open_design_exe)
    codex_home = Path(args.codex_home)
    launcher = Path(args.launcher) if args.launcher else open_design_exe.with_name("Open Design - GPT Codex Proxy.bat")

    config, config_status = read_json(config_path)
    codex_bin = find_codex_bin(config, args.codex_bin)
    project_locations = (config or {}).get("projectLocations") or []
    location_paths = {str(loc.get("path")) for loc in project_locations if isinstance(loc, dict)}
    location_ids = {str(loc.get("id")) for loc in project_locations if isinstance(loc, dict)}
    default_location = (config or {}).get("defaultProjectLocationId")
    model = (((config or {}).get("agentModels") or {}).get("codex") or {}).get("model")

    checks = [
        Check("project root exists", project_root.exists(), str(project_root)),
        Check("permission root exists", permission_root.exists(), str(permission_root)),
        Check("Open Design executable exists", open_design_exe.exists(), str(open_design_exe)),
        Check("app-config.json valid", config is not None, f"{config_path} ({config_status})"),
        Check("agentId is codex", (config or {}).get("agentId") == "codex", str((config or {}).get("agentId"))),
        Check("default model configured", model == args.expected_model, str(model)),
        Check("project location registered", str(project_root) in location_paths, str(project_root)),
        Check("permission root registered", str(permission_root) in location_paths or PERMISSION_LOCATION_ID in location_ids, str(permission_root)),
        Check("default project location selected", default_location == LOCATION_ID, str(default_location)),
        Check("Codex home exists", codex_home.exists(), str(codex_home)),
        Check("Codex OAuth/login present", has_codex_login(codex_home), str(codex_home / "auth.json")),
        Check("Codex executable discovered", bool(codex_bin), codex_bin or "missing"),
        Check("proxy launcher exists", launcher.exists(), str(launcher)),
        Check("portable setup doc exists", (project_root / "opendesign-assistance" / "usage-notes" / "PORTABLE_OPEN_DESIGN_SETUP.md").exists()),
        Check("plugin workspace exists", (project_root / "opendesign-assistance" / "plugins").exists()),
        Check("repo is clean and tracks origin", *git_clean(project_root)),
    ]
    checks.extend(codex_permission_checks(codex_home, permission_root))

    if codex_bin:
        ok, version = run_version(codex_bin, codex_home)
        checks.append(Check("Codex CLI runs", ok, version))

    for port in args.ports:
        checks.append(Check(f"Open Design local port {port} reachable", port_open(port), "optional; false is OK when app is closed"))

    log = config_path.with_name("logs") / "latest.log"
    fallback_log = config_path.parent / "latest.log"
    checks.append(Check("daemon latest.log seen", log.exists() or fallback_log.exists(), str(log if log.exists() else fallback_log)))
    return checks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only doctor for Open Design + OPEN-DESIGN-Assistance on Windows.")
    parser.add_argument("--project-root", default=str(Path.cwd()), help="OPEN-DESIGN-Assistance clone")
    parser.add_argument("--permission-root", default=str(DEFAULT_PERMISSION_ROOT), help="Codex writable/trusted root expected for Open Design calls")
    parser.add_argument("--config", default=str(default_config_path()), help="Open Design app-config.json")
    parser.add_argument("--open-design-exe", default=str(default_open_design_exe()), help="Open Design.exe path")
    parser.add_argument("--codex-bin", default=None, help="Optional explicit codex.exe/codex.cmd path")
    parser.add_argument("--codex-home", default=str(default_codex_home()), help="Codex OAuth home")
    parser.add_argument("--launcher", default=None, help="Optional launcher .bat path")
    parser.add_argument("--expected-model", default=DEFAULT_MODEL, help="Expected Codex model")
    parser.add_argument("--ports", nargs="*", type=int, default=list(DEFAULT_PORTS), help="Local ports to probe")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on any required failure")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    checks = diagnose(args)
    required_names = {
        "project root exists",
        "permission root exists",
        "app-config.json valid",
        "agentId is codex",
        "default model configured",
        "project location registered",
        "permission root registered",
        "default project location selected",
        "Codex home exists",
        "Codex OAuth/login present",
        "Codex executable discovered",
        "Codex permission root writable",
        "Codex permission root trusted",
        ".od-skills directories discovered",
        "Codex .od-skills root writable",
        "Codex .od-skills root trusted",
        "PowerShell .od-skills read",
        "Codex CLI runs",
        "portable setup doc exists",
        "repo is clean and tracks origin",
    }
    print("OPEN_DESIGN_ASSISTANCE_DOCTOR")
    failed_required = []
    for check in checks:
        status = "PASS" if check.ok else ("WARN" if check.name not in required_names else "FAIL")
        print(f"{status} {check.name}: {check.detail}")
        if not check.ok and check.name in required_names:
            failed_required.append(check.name)
    if failed_required:
        print("DOCTOR_RESULT=FAIL")
        if args.strict:
            raise SystemExit(1)
    else:
        print("DOCTOR_RESULT=OK")


if __name__ == "__main__":
    main()
