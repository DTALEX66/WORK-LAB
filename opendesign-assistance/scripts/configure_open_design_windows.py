#!/usr/bin/env python
"""Configure Open Design on Windows to reuse this assistance repo.

This script intentionally stores no API keys. It configures Open Design to use the
local Codex CLI + CODEX_HOME OAuth/subscription state, points Open Design at a
project root such as D:\\All projects\\OPEN-DESIGN-Assistance, and grants Codex a
safe writable/trusted root for Open Design calls such as D:\\All projects.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_MODEL = "gpt-5.5"
DEFAULT_PROXY = "http://127.0.0.1:7890"
DEFAULT_SOCKS_PROXY = "socks5://127.0.0.1:7890"
DEFAULT_PERMISSION_ROOT = Path(r"D:\All projects")
LOCATION_ID = "loc_open_design_assistance"
PERMISSION_LOCATION_ID = "loc_all_projects"


def windows_home() -> Path:
    return Path(os.environ.get("USERPROFILE") or Path.home())


def default_config_path() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        appdata = str(windows_home() / "AppData" / "Roaming")
    return Path(appdata) / "Open Design" / "namespaces" / "release-stable-win" / "data" / "app-config.json"


def default_open_design_exe() -> Path:
    return Path(r"D:\Programs\Open Design\Open Design.exe")


def default_codex_home() -> Path:
    return windows_home() / ".codex"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any], dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def find_codex_bin(explicit: str | None) -> str:
    if explicit:
        return str(Path(explicit))

    candidates: list[Path] = []
    home = windows_home()
    codex_root = home / "AppData" / "Local" / "OpenAI" / "Codex" / "bin"
    if codex_root.exists():
        candidates.extend(sorted(codex_root.glob("*/codex.exe"), reverse=True))
        candidates.extend(sorted(codex_root.glob("*/codex.cmd"), reverse=True))

    for name in ("codex.cmd", "codex.exe", "codex"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))

    if not candidates:
        raise SystemExit(
            "Could not find Codex CLI. Install/log in to Codex first, then pass --codex-bin explicitly."
        )
    return str(candidates[0])


def has_codex_oauth(codex_home: Path) -> bool:
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
    access_key = "access" + "_token"
    return bool(tokens.get(access_key))


def backup(path: Path, dry_run: bool) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = path.with_name(f"app-config.backup-open-design-assistance-{stamp}.json")
    if not dry_run:
        shutil.copy2(path, out)
    return out


def backup_codex_config(path: Path, dry_run: bool) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = path.with_name(f"config.backup-open-design-assistance-{stamp}.toml")
    if not dry_run:
        shutil.copy2(path, out)
    return out


def toml_literal_path(path: Path) -> str:
    return str(path).replace("'", "\\'")


def update_codex_permissions(codex_home: Path, permission_root: Path, dry_run: bool) -> Path | None:
    """Grant Codex workspace-write access to permission_root.

    Codex uses CODEX_HOME/config.toml for sandbox policy. Open Design can pass a
    project under D:\\All projects, but Codex still refuses writes unless that root
    is trusted/writable here.
    """
    config_path = codex_home / "config.toml"
    root_text = toml_literal_path(permission_root)
    root_key = str(permission_root).lower()
    text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    backup_path = backup_codex_config(config_path, dry_run)

    writable_match = re.search(r"(?m)^writable_roots\s*=\s*\[(.*?)\]\s*$", text)
    if writable_match:
        current = writable_match.group(1)
        if root_text.lower() not in current.lower():
            updated = current.rstrip()
            if updated:
                updated += ", "
            updated += f"'{root_text}'"
            text = text[: writable_match.start(1)] + updated + text[writable_match.end(1) :]
    elif "[sandbox_workspace_write]" in text:
        text = re.sub(
            r"(?m)^\[sandbox_workspace_write\]\s*$",
            lambda _match: f"[sandbox_workspace_write]\nwritable_roots = ['{root_text}']",
            text,
            count=1,
        )
    else:
        text = text.rstrip() + f"\n\n[sandbox_workspace_write]\nwritable_roots = ['{root_text}']\n"

    project_header = f"[projects.'{root_key}']"
    if project_header.lower() not in text.lower():
        text = text.rstrip() + f"\n\n{project_header}\ntrust_level = \"trusted\"\n"

    if not dry_run:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(text, encoding="utf-8")
    return backup_path


def add_project_location(config: dict[str, Any], project_root: Path, permission_root: Path) -> None:
    project_root_text = str(project_root)
    permission_root_text = str(permission_root)
    location = {"id": LOCATION_ID, "name": "OPEN-DESIGN-Assistance", "path": project_root_text}
    permission_location = {"id": PERMISSION_LOCATION_ID, "name": "All projects", "path": permission_root_text}
    locations = config.setdefault("projectLocations", [])
    locations = [
        loc
        for loc in locations
        if loc.get("id") not in {LOCATION_ID, PERMISSION_LOCATION_ID}
        and loc.get("path") not in {project_root_text, permission_root_text}
    ]
    locations.extend([permission_location, location])
    config["projectLocations"] = locations
    config["defaultProjectLocationId"] = LOCATION_ID

    recent = [project_root_text, permission_root_text]
    for item in config.get("recentLinkedDirs", []):
        if item not in recent:
            recent.append(item)
    config["recentLinkedDirs"] = recent[:10]


def configure(
    config_path: Path,
    project_root: Path,
    codex_bin: str,
    codex_home: Path,
    permission_root: Path,
    model: str,
    dry_run: bool,
) -> dict[str, Any]:
    config = read_json(config_path)
    config.setdefault("onboardingCompleted", True)
    config["agentId"] = "codex"
    config.setdefault("agentModels", {}).setdefault("codex", {})["model"] = model
    config.setdefault("agentCliEnv", {}).setdefault("codex", {})["CODEX_BIN"] = codex_bin
    config["agentCliEnv"]["codex"]["CODEX_HOME"] = str(codex_home)
    add_project_location(config, project_root, permission_root)
    write_json(config_path, config, dry_run)
    return config


def create_launcher(
    launcher_path: Path,
    open_design_exe: Path,
    codex_bin: str,
    codex_home: Path,
    proxy: str | None,
    dry_run: bool,
) -> None:
    lines = ["@echo off"]
    if proxy:
        lines.extend([
            f'set "HTTP_PROXY={proxy}"',
            f'set "HTTPS_PROXY={proxy}"',
            f'set "ALL_PROXY={DEFAULT_SOCKS_PROXY}"',
        ])
    lines.extend([
        f'set "CODEX_BIN={codex_bin}"',
        f'set "CODEX_HOME={codex_home}"',
        f'start "Open Design" "{open_design_exe}"',
        "",
    ])
    if dry_run:
        return
    launcher_path.parent.mkdir(parents=True, exist_ok=True)
    launcher_path.write_text("\r\n".join(lines), encoding="utf-8")


def smoke_codex(codex_bin: str, codex_home: Path) -> str:
    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    proc = subprocess.run([codex_bin, "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, timeout=30)
    if proc.returncode != 0:
        raise SystemExit(proc.stdout)
    return proc.stdout.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configure Open Design for OPEN-DESIGN-Assistance reuse on Windows.")
    parser.add_argument("--project-root", default=str(Path.cwd()), help="Cloned OPEN-DESIGN-Assistance directory")
    parser.add_argument("--config", default=str(default_config_path()), help="Open Design app-config.json path")
    parser.add_argument("--open-design-exe", default=str(default_open_design_exe()), help="Open Design.exe path")
    parser.add_argument("--codex-bin", default=None, help="Native codex.exe/codex.cmd path; auto-detected when omitted")
    parser.add_argument("--codex-home", default=str(default_codex_home()), help="Codex OAuth home, usually %%USERPROFILE%%\\.codex")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Codex model shown in Open Design")
    parser.add_argument("--launcher", default=None, help="Optional launcher .bat path")
    parser.add_argument("--permission-root", default=str(DEFAULT_PERMISSION_ROOT), help="Codex writable/trusted root for Open Design calls")
    parser.add_argument("--no-proxy", action="store_true", help="Do not put proxy env vars into launcher")
    parser.add_argument("--skip-codex-permission-update", action="store_true", help="Do not modify CODEX_HOME/config.toml")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print planned config without writing")
    parser.add_argument("--skip-codex-oauth-check", action="store_true", help="Do not require CODEX_HOME/auth.json to exist yet")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config)
    codex_home = Path(args.codex_home)
    permission_root = Path(args.permission_root).resolve()
    codex_bin = find_codex_bin(args.codex_bin)

    if not project_root.exists():
        raise SystemExit(f"Project root does not exist: {project_root}")
    if not permission_root.exists():
        raise SystemExit(f"Permission root does not exist: {permission_root}")
    if not args.skip_codex_oauth_check and not has_codex_oauth(codex_home):
        raise SystemExit(
            f"Codex OAuth not found in {codex_home}. Run Codex login on this computer first, "
            "or re-run with --skip-codex-oauth-check for staging."
        )

    version = smoke_codex(codex_bin, codex_home)
    backup_path = backup(config_path, args.dry_run)
    codex_backup_path = None
    if not args.skip_codex_permission_update:
        codex_backup_path = update_codex_permissions(codex_home, permission_root, args.dry_run)
    config = configure(config_path, project_root, codex_bin, codex_home, permission_root, args.model, args.dry_run)

    launcher = Path(args.launcher) if args.launcher else Path(args.open_design_exe).with_name("Open Design - GPT Codex Proxy.bat")
    create_launcher(
        launcher,
        Path(args.open_design_exe),
        codex_bin,
        codex_home,
        None if args.no_proxy else DEFAULT_PROXY,
        args.dry_run,
    )

    print("OPEN_DESIGN_ASSISTANCE_CONFIG_OK")
    print(f"project_root={project_root}")
    print(f"permission_root={permission_root}")
    print(f"config_path={config_path}")
    print(f"backup_path={backup_path or '[none]'}")
    print(f"codex_config_backup={codex_backup_path or '[none]'}")
    print(f"agentId={config.get('agentId')}")
    print(f"model={config.get('agentModels', {}).get('codex', {}).get('model')}")
    print(f"codex_bin={codex_bin}")
    print(f"codex_home={codex_home}")
    print(f"codex_version={version}")
    print(f"launcher={launcher}")
    if args.dry_run:
        print("dry_run=true")


if __name__ == "__main__":
    main()
