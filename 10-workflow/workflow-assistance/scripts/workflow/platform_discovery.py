"""Read-only platform discovery for Codex/Hermes logical instances (WL3-100).

Discovers package -> executable -> launcher -> config root -> profile -> active
process metadata without reading credentials, sessions, or private bodies.
Windows: App Execution Alias (PATH), Start Menu shortcuts, running process
images. Degrades gracefully to UNAVAILABLE when nothing is found; never
auto-uninstalls or mutates anything.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import platform_identity as identity


@dataclass
class DiscoveredEntry:
    package_identity: str
    executable_realpath: str
    launcher_id: str
    launcher_target: str | None
    binary_digest: str | None
    effective_config_root: str | None
    profile_id: str | None
    discovered_version: str | None
    freshness: str = "FRESH"
    active_process: bool = False
    source: str = "unknown"
    logical_instance_id: str | None = None


def _sha256_file(path: Path) -> str | None:
    import hashlib

    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _realpath(candidate: str | Path) -> str | None:
    try:
        resolved = Path(candidate).resolve()
        return str(resolved) if resolved.is_file() else None
    except OSError:
        return None


def _which(name: str) -> str | None:
    return shutil.which(name)


def _config_root_home(directory: str | None) -> str | None:
    if not directory:
        return None
    path = Path(directory).expanduser()
    return str(path) if path.is_dir() else None


def _version_from_executable(executable: str) -> str | None:
    try:
        result = subprocess.run(
            [executable, "--version"],
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        output = (result.stdout or result.stderr or "").strip()
        return output.splitlines()[0][:120] if output else None
    except (OSError, subprocess.SubprocessError):
        return None


def _running_processes() -> set[str]:
    """Best-effort process image names (Windows tasklist or ps)."""
    names: set[str] = set()
    try:
        if os.name == "nt":
            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                text=True,
                capture_output=True,
                timeout=20,
                check=False,
                encoding="utf-8",
                errors="replace",
            )
            for line in (result.stdout or "").splitlines():
                fields = line.split(",")
                if len(fields) >= 1:
                    names.add(fields[0].strip('"').lower())
        else:
            result = subprocess.run(
                ["ps", "-eo", "comm"],
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
                encoding="utf-8",
                errors="replace",
            )
            for line in (result.stdout or "").splitlines():
                name = line.strip().lower()
                if name:
                    names.add(Path(name).name)
    except (OSError, subprocess.SubprocessError):
        pass
    return names


def _windows_start_menu_shortcuts() -> list[Path]:
    """Read Start Menu .lnk files (names only; contents are never parsed)."""
    shortcuts: list[Path] = []
    if os.name != "nt":
        return shortcuts
    roots = [
        Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
    ]
    for root in roots:
        if not root.is_dir():
            continue
        try:
            for link in root.rglob("*.lnk"):
                shortcuts.append(link)
        except OSError:
            continue
    return shortcuts


def discover_codex() -> list[DiscoveredEntry]:
    entries: list[DiscoveredEntry] = []
    codex = _which("codex")
    config_root = _config_root_home(os.environ.get("CODEX_HOME") or "~/.codex")
    running = _running_processes()
    launcher_target = None
    if codex:
        real = _realpath(codex)
        if real:
            launcher_target = codex
            entries.append(
                DiscoveredEntry(
                    package_identity="codex-cli",
                    executable_realpath=real,
                    launcher_id="codex-path",
                    launcher_target=launcher_target,
                    binary_digest=_sha256_file(Path(real)),
                    effective_config_root=config_root,
                    profile_id="codex-user",
                    discovered_version=_version_from_executable(real),
                    active_process=Path(real).name.lower() in running,
                    source="app-execution-alias/path",
                    logical_instance_id="codex",
                )
            )
    else:
        entries.append(
            DiscoveredEntry(
                package_identity="codex-cli",
                executable_realpath="",
                launcher_id="codex-path",
                launcher_target=None,
                binary_digest=None,
                effective_config_root=config_root,
                profile_id="codex-user",
                discovered_version=None,
                active_process=False,
                source="missing",
                logical_instance_id="codex",
            )
        )
    return entries


def discover_hermes() -> list[DiscoveredEntry]:
    entries: list[DiscoveredEntry] = []
    hermes = _which("hermes")
    config_root = _config_root_home(os.environ.get("HERMES_HOME") or "~/.hermes")
    running = _running_processes()
    if hermes:
        real = _realpath(hermes)
        if real:
            entries.append(
                DiscoveredEntry(
                    package_identity="hermes-agent",
                    executable_realpath=real,
                    launcher_id="hermes-path",
                    launcher_target=hermes,
                    binary_digest=_sha256_file(Path(real)),
                    effective_config_root=config_root,
                    profile_id="hermes-default",
                    discovered_version=_version_from_executable(real),
                    active_process=Path(real).name.lower() in running,
                    source="path",
                    logical_instance_id="hermes",
                )
            )
    else:
        entries.append(
            DiscoveredEntry(
                package_identity="hermes-agent",
                executable_realpath="",
                launcher_id="hermes-path",
                launcher_target=None,
                binary_digest=None,
                effective_config_root=config_root,
                profile_id="hermes-default",
                discovered_version=None,
                active_process=False,
                source="missing",
                logical_instance_id="hermes",
            )
        )
    return entries


def discover_all() -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for entry in discover_codex() + discover_hermes():
        observations.append(
            {
                "logical_instance_id": entry.logical_instance_id,
                "package_identity": entry.package_identity,
                "executable_realpath": entry.executable_realpath,
                "launcher_id": entry.launcher_id,
                "launcher_target": entry.launcher_target,
                "binary_digest": entry.binary_digest,
                "effective_config_root": entry.effective_config_root,
                "profile_id": entry.profile_id,
                "discovered_version": entry.discovered_version,
                "freshness": entry.freshness,
                "active_process": entry.active_process,
                "source": entry.source,
            }
        )
    return observations


def resolve_current_platform() -> dict[str, Any]:
    """Run real discovery and classify identities via the canonical resolver."""
    observations = discover_all()
    resolved = identity.resolve_identity(observations)
    resolved["discovery_source"] = "real-platform-probe"
    resolved["probed"] = {
        "codex_cli": _which("codex") is not None,
        "hermes_cli": _which("hermes") is not None,
        "os": os.name,
        "start_menu_links": len(_windows_start_menu_shortcuts()),
    }
    return resolved


if __name__ == "__main__":
    print(json.dumps(resolve_current_platform(), ensure_ascii=False, indent=2, default=str))
