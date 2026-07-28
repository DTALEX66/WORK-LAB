#!/usr/bin/env python
"""Deploy portable Workflow-assistance assets into the active Hermes home.

The repository is the only portable source of truth. This script never reads or
copies secrets/runtime state and never writes live skill content back into the
repository. Without ``--apply`` it is a dry run.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import datetime as dt
import hashlib
import os
import shutil
from pathlib import Path
from typing import Iterable

try:
    import yaml
except Exception as exc:  # pragma: no cover - environment guard
    raise SystemExit(f"PyYAML is required: {exc}")


MANAGED_MCP_SERVERS = {"context7", "public-apis", "sequential-thinking"}
RETIRED_MANAGED_PLUGINS = {"disk-cleanup", "google_meet", "spotify"}
PLUGIN_RETIREMENT_MIGRATION = 1
WORKFLOW_SYNC_BACKUP_KEEP = 2
RETIRED_MANAGED_SKILL_ASSETS = {
    "model-switch/references/cc-switch-codex-hermes.md",
    "model-switch/references/oauth-credential-sync.md",
    "software-development/agent-workflow-fortress/references/hermes-provider-mcp-workflow.md",
    "software-development/hermes-provider-routing",
    "software-development/windows-development-environment/references/codex++-proxy-routing.md",
    "software-development/windows-development-environment/references/credential-audit-and-template.md",
    "software-development/windows-development-environment/references/github-credential-extraction.md",
    "software-development/windows-development-environment/references/provider-network-troubleshooting.md",
    "software-development/windows-development-environment/references/third-party-proxy-setup.md",
    "software-development/windows-development-environment/references/cognitive-loop-os-tauri-build.md",
    "software-development/windows-development-environment/references/cognitive-loop-os-desktop-workflow.md",
    "software-development/python-testing/references/deterministic-e2e-test-pattern.md",
    "software-development/cognitive-loop-os",
    "software-development/screenlingua",
}
MANAGED_DISPLAY_KEYS = {"busy_input_mode", "streaming"}
MANAGED_MODEL_KEYS = {"max_tokens"}
MANAGED_AGENT_KEYS = {"reasoning_effort"}
MANAGED_QUICK_COMMAND_PREFIX = "切换"


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_hermes_home() -> Path:
    if os.environ.get("HERMES_HOME"):
        return Path(os.environ["HERMES_HOME"])
    if os.name == "nt":
        root = os.environ.get("LOCALAPPDATA")
        return Path(root) / "hermes" if root else Path.home() / "AppData/Local/hermes"
    return Path.home() / ".hermes"


def validate_deployment_paths(repo: Path, home: Path, *, allow_project_runtime_home: bool = False) -> None:
    """Reject overlapping source and deployment roots before any backup or write."""
    runtime_root = repo / ".hermes" / "task-runtime"
    if allow_project_runtime_home and home.is_relative_to(runtime_root):
        return
    try:
        overlaps = repo == home or repo.is_relative_to(home) or home.is_relative_to(repo)
    except ValueError:
        overlaps = False
    if overlaps:
        raise ValueError(
            "portable deployment repo and Hermes home must be distinct, non-overlapping directories: "
            f"repo={repo} home={home}"
        )


def load_config_contract(repo: Path) -> dict:
    """Load the reviewed portable ownership contract before merging config."""

    path = repo / "config/managed-config-schema.yaml"
    # Keep the library-level merge API compatible with minimal test/consumer
    # repositories. Full package deployment separately requires this file.
    data = (
        yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if path.exists()
        else {
            "schema_version": 1,
            "managed": {"display.busy_input_mode": "replace", "display.streaming": "replace", "agent.reasoning_effort": "replace", "model.max_tokens": "replace", "model_picker.custom_lanes": "replace", "quick_commands": {"owned_prefix": "切换"}},
            "preserved": ["model.provider", "model.default", "model.api_key"],
        }
    )
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("managed config contract schema_version must be 1")
    managed = data.get("managed")
    preserved = data.get("preserved")
    if not isinstance(managed, dict) or not isinstance(preserved, list):
        raise ValueError("managed config contract must define managed mappings and preserved paths")
    for required in ("model.provider", "model.default", "model.api_key"):
        if required not in preserved:
            raise ValueError(f"managed config contract must preserve {required}")
    return data


def sha_tree(path: Path) -> tuple[str | None, int]:
    if not path.exists():
        return None, 0
    digest = hashlib.sha256()
    count = 0
    ignored = {".git", "__pycache__", ".cache", "logs", "sessions"}
    for file in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        if any(part in ignored for part in file.parts):
            continue
        digest.update(file.relative_to(path).as_posix().encode("utf-8") + b"\0")
        digest.update(file.read_bytes())
        count += 1
    return digest.hexdigest()[:16], count


def copytree(src: Path, dst: Path, *, apply: bool) -> None:
    if not src.exists():
        print(f"skip missing tree: {src}")
        return
    print(f"copy tree: {src} -> {dst}")
    if apply:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, dirs_exist_ok=True)


def copyfile(src: Path, dst: Path, *, apply: bool) -> None:
    if not src.exists():
        print(f"skip missing file: {src}")
        return
    print(f"copy file: {src} -> {dst}")
    if apply:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def remove_retired_managed_assets(home: Path, *, apply: bool) -> None:
    """Remove only package-owned paths that have an explicit retirement record."""

    skills = home / "skills"
    for relative in sorted(RETIRED_MANAGED_SKILL_ASSETS):
        target = skills / Path(relative)
        if not target.exists():
            continue
        print(f"remove retired managed skill asset: {target}")
        if not apply:
            continue
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()


def backup_paths(home: Path, rels: Iterable[str], *, apply: bool) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = home / "backups" / f"workflow-assistance-sync-{stamp}"
    print(f"backup root: {backup}")
    if not apply:
        return backup
    backup.mkdir(parents=True, exist_ok=True)
    for rel in rels:
        src = home / rel
        if not src.exists():
            continue
        dst = backup / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    return backup


def prune_workflow_sync_backups(
    home: Path, *, apply: bool, keep: int = WORKFLOW_SYNC_BACKUP_KEEP
) -> int:
    """Keep only recent backups created by this synchronizer, never user backups."""
    if keep < 1:
        raise ValueError("workflow sync backup retention must keep at least one backup")
    root = home / "backups"
    if not root.exists():
        return 0
    candidates = sorted(
        (
            item
            for item in root.iterdir()
            if item.is_dir() and item.name.startswith("workflow-assistance-sync-")
        ),
        key=lambda item: item.name,
        reverse=True,
    )
    stale = candidates[keep:]
    for item in stale:
        print(f"prune stale workflow sync backup: {item}")
        if apply:
            shutil.rmtree(item)
    return len(stale)


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def _fsync_path(path: Path) -> None:
    """Flush a replaced file; directory fsync is unavailable on Windows."""
    if path.is_file():
        with path.open("r+b") as handle:
            os.fsync(handle.fileno())
    elif os.name != "nt":
        flags = getattr(os, "O_DIRECTORY", 0)
        fd = os.open(path, os.O_RDONLY | flags)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def atomic_replace_paths(staging: Path, home: Path, rels: Iterable[str]) -> None:
    """Replace managed roots as one rollback-capable filesystem transaction."""
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    rollback = home / f".workflow-assistance-rollback-{stamp}"
    records: list[tuple[Path, Path | None, bool]] = []
    rollback_failed = False
    operation_failed = False
    rollback.mkdir(parents=True, exist_ok=False)
    try:
        for relative in rels:
            source = staging / relative
            if not source.exists():
                continue
            target = home / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            previous = rollback / relative
            had_target = target.exists()
            records.append((target, previous if had_target else None, False))
            if had_target:
                previous.parent.mkdir(parents=True, exist_ok=True)
                os.replace(target, previous)
            os.replace(source, target)
            records[-1] = (target, previous if had_target else None, True)
            _fsync_path(target)
    except Exception:
        operation_failed = True
        for target, previous, installed in reversed(records):
            if installed and target.exists():
                try:
                    _remove_path(target)
                except Exception:
                    rollback_failed = True
            if previous is not None and previous.exists():
                try:
                    os.replace(previous, target)
                except Exception:
                    rollback_failed = True
        if rollback_failed:
            print(f"ROLLBACK_INCOMPLETE preserved={rollback}")
        raise
    finally:
        if rollback.exists() and not rollback_failed:
            try:
                shutil.rmtree(rollback)
            except Exception:
                rollback_failed = True
                print(f"ROLLBACK_CLEANUP_INCOMPLETE preserved={rollback}")
                if not operation_failed:
                    raise
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def prepare_staging(repo: Path, home: Path) -> Path:
    """Build a complete managed view without mutating the live Hermes home."""
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    staging = home / f".workflow-assistance-staging-{stamp}"
    staging.mkdir(parents=True, exist_ok=False)
    for relative in ("skills", "bin"):
        live = home / relative
        if live.exists():
            shutil.copytree(live, staging / relative, dirs_exist_ok=True)
    for relative in ("config.yaml", ".env.template", ".workflow-assistance-state.yaml"):
        live = home / relative
        if live.exists():
            (staging / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(live, staging / relative)
    copytree(repo / "skills", staging / "skills", apply=True)
    copytree(repo / "bin", staging / "bin", apply=True)
    copyfile(repo / "config/.env.template", staging / ".env.template", apply=True)
    remove_retired_managed_assets(staging, apply=True)
    merge_live_config(repo, staging, apply=True, wrapper_root=home)
    return staging


def merge_live_config(
    repo: Path,
    home: Path,
    *,
    apply: bool,
    wrapper_root: Path | None = None,
) -> None:
    """Merge portable entries while preserving live provider/model and custom MCPs."""

    repo_cfg = repo / "config/config.yaml"
    live_cfg = home / "config.yaml"
    if not repo_cfg.exists():
        print("skip config merge: missing repository config")
        return
    contract = load_config_contract(repo)
    repo_data = yaml.safe_load(repo_cfg.read_text(encoding="utf-8")) or {}
    live_data = (
        yaml.safe_load(live_cfg.read_text(encoding="utf-8")) or {}
        if live_cfg.exists()
        else deepcopy(repo_data)
    )
    if not isinstance(live_data, dict) or not isinstance(repo_data, dict):
        raise ValueError("config roots must be mappings")

    live_mcp = live_data.setdefault("mcp_servers", {})
    repo_mcp = repo_data.get("mcp_servers") or {}
    if not isinstance(live_mcp, dict) or not isinstance(repo_mcp, dict):
        raise ValueError("mcp_servers must be mappings")
    for retired in MANAGED_MCP_SERVERS - set(repo_mcp):
        live_mcp.pop(retired, None)

    wrapper_home = wrapper_root or home
    cmd_wrapper = wrapper_home / "bin/hermes-npx.cmd"
    sh_wrapper = wrapper_home / "bin/hermes-npx"
    # The config is prepared in staging but consumed after promotion into
    # ``wrapper_home``. Select by target platform, never by staging-time
    # existence of the final path.
    wrapper = (cmd_wrapper if os.name == "nt" else sh_wrapper).as_posix()
    for name, config in repo_mcp.items():
        if not isinstance(config, dict):
            raise ValueError(f"mcp server {name!r} must be a mapping")
        deployed = dict(config)
        if deployed.get("command") == "hermes-npx":
            deployed["command"] = wrapper
        live_mcp[name] = deployed

    repo_hooks = repo_data.get("hooks") or {}
    live_hooks = live_data.setdefault("hooks", {})
    if not isinstance(repo_hooks, dict) or not isinstance(live_hooks, dict):
        raise ValueError("hooks must be mappings")
    repo_pre_tool = repo_hooks.get("pre_tool_call") or []
    live_pre_tool = live_hooks.get("pre_tool_call") or []
    if not isinstance(repo_pre_tool, list) or not isinstance(live_pre_tool, list):
        raise ValueError("hooks.pre_tool_call must be lists")
    managed_pre_tool = []
    for hook in repo_pre_tool:
        if not isinstance(hook, dict):
            raise ValueError("pre_tool_call entries must be mappings")
        deployed_hook = deepcopy(hook)
        if deployed_hook.get("matcher") == "terminal":
            guard = (wrapper_home / "bin/hermes-project-terminal-guard.py").as_posix()
            python_command = "python" if os.name == "nt" else "python3"
            deployed_hook["command"] = f'{python_command} "{guard}"'
        managed_pre_tool.append(deployed_hook)
    if managed_pre_tool:
        custom_pre_tool = [
            hook
            for hook in live_pre_tool
            if isinstance(hook, dict) and hook.get("matcher") != "terminal"
        ]
        live_hooks["pre_tool_call"] = custom_pre_tool + managed_pre_tool

    plugins = live_data.setdefault("plugins", {})
    repo_enabled = (repo_data.get("plugins") or {}).get("enabled") or []
    state_file = home / ".workflow-assistance-state.yaml"
    state = (
        yaml.safe_load(state_file.read_text(encoding="utf-8")) or {}
        if state_file.exists()
        else {}
    )
    if not isinstance(state, dict):
        raise ValueError("workflow assistance state must be a mapping")
    retire_legacy_plugins = state.get("plugin_retirement_migration", 0) < PLUGIN_RETIREMENT_MIGRATION
    if isinstance(plugins, dict):
        current_enabled = plugins.get("enabled") or []
        retained = (
            [name for name in current_enabled if name not in RETIRED_MANAGED_PLUGINS]
            if retire_legacy_plugins
            else list(current_enabled)
        )
        plugins["enabled"] = list(dict.fromkeys(retained + repo_enabled))
        plugins.setdefault("disabled", [])

    repo_display = repo_data.get("display") or {}
    live_display = live_data.setdefault("display", {})
    if not isinstance(repo_display, dict) or not isinstance(live_display, dict):
        raise ValueError("display must be a mapping")
    for key in MANAGED_DISPLAY_KEYS:
        if key in repo_display:
            live_display[key] = repo_display[key]

    repo_model = repo_data.get("model") or {}
    live_model = live_data.setdefault("model", {})
    if not isinstance(repo_model, dict) or not isinstance(live_model, dict):
        raise ValueError("model must be a mapping")
    for key in MANAGED_MODEL_KEYS:
        if key in repo_model:
            live_model[key] = repo_model[key]

    repo_agent = repo_data.get("agent") or {}
    live_agent = live_data.setdefault("agent", {})
    if not isinstance(repo_agent, dict) or not isinstance(live_agent, dict):
        raise ValueError("agent must be a mapping")
    for key in MANAGED_AGENT_KEYS:
        if key in repo_agent:
            live_agent[key] = repo_agent[key]

    # Picker lanes are portable UX, not credentials or current session state.
    repo_picker = repo_data.get("model_picker") or {}
    live_picker = live_data.setdefault("model_picker", {})
    if not isinstance(repo_picker, dict) or not isinstance(live_picker, dict):
        raise ValueError("model_picker must be a mapping")
    if "custom_lanes" in repo_picker:
        live_picker["custom_lanes"] = deepcopy(repo_picker["custom_lanes"])

    # Replace only workflow-owned aliases; preserve unrelated user commands.
    repo_commands = repo_data.get("quick_commands") or {}
    live_commands = live_data.setdefault("quick_commands", {})
    if not isinstance(repo_commands, dict) or not isinstance(live_commands, dict):
        raise ValueError("quick_commands must be mappings")
    for name in list(live_commands):
        if name.startswith(MANAGED_QUICK_COMMAND_PREFIX):
            live_commands.pop(name)
    live_commands.update(deepcopy(repo_commands))

    model = live_data.get("model") or {}
    managed_paths = ",".join(sorted(contract["managed"]))
    print("merge live config: contract managed =", managed_paths)
    print("merge live config: preserve provider/model =", model.get("provider"), model.get("default"))
    print("merge live config: mcp =", list(live_mcp))
    if apply:
        live_cfg.write_text(
            yaml.safe_dump(live_data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        if retire_legacy_plugins:
            state["plugin_retirement_migration"] = PLUGIN_RETIREMENT_MIGRATION
            state_file.write_text(
                yaml.safe_dump(state, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )


def deploy_portable(
    repo: Path,
    home: Path,
    *,
    apply: bool,
    include_backup: bool = True,
    allow_project_runtime_home: bool = False,
) -> None:
    """Run the single deployment orchestration used by CLI and verifier."""

    repo = repo.resolve()
    home = home.resolve()
    if not repo.is_dir() or not home.is_dir():
        raise ValueError("portable deployment requires existing repo and home directories")
    validate_deployment_paths(repo, home, allow_project_runtime_home=allow_project_runtime_home)
    if include_backup:
        backup_paths(
            home,
            [
                "config.yaml",
                ".env.template",
                ".workflow-assistance-state.yaml",
                "bin",
                "skills/autonomous-ai-agents/codex",
                "skills/model-switch",
                "skills/software-development",
            ],
            apply=apply,
        )
    if apply:
        staging = prepare_staging(repo, home)
        atomic_replace_paths(
            staging,
            home,
            (
                "skills",
                "bin",
                "config.yaml",
                ".env.template",
                ".workflow-assistance-state.yaml",
            ),
        )
    else:
        copytree(repo / "skills", home / "skills", apply=False)
        remove_retired_managed_assets(home, apply=False)
        copytree(repo / "bin", home / "bin", apply=False)
        copyfile(repo / "config/.env.template", home / ".env.template", apply=False)
        merge_live_config(repo, home, apply=False)
    if include_backup:
        prune_workflow_sync_backups(home, apply=apply)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(default_repo_root()))
    parser.add_argument("--home", default=str(default_hermes_home()))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo)
    home = Path(args.home)
    if not repo.exists():
        raise SystemExit(f"repo not found: {repo}")
    if not home.exists():
        raise SystemExit(f"Hermes home not found: {home}")

    deploy_portable(repo, home, apply=args.apply)

    print("\nsummary hashes:")
    for label, path in (
        ("repo skills", repo / "skills"),
        ("live skills", home / "skills"),
        ("repo bin", repo / "bin"),
        ("live bin", home / "bin"),
    ):
        print(label, sha_tree(path))


if __name__ == "__main__":
    main()
