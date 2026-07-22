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


def merge_live_config(repo: Path, home: Path, *, apply: bool) -> None:
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

    cmd_wrapper = home / "bin/hermes-npx.cmd"
    sh_wrapper = home / "bin/hermes-npx"
    wrapper = (cmd_wrapper if cmd_wrapper.exists() else sh_wrapper).as_posix()
    for name, config in repo_mcp.items():
        if not isinstance(config, dict):
            raise ValueError(f"mcp server {name!r} must be a mapping")
        deployed = dict(config)
        if deployed.get("command") == "hermes-npx":
            deployed["command"] = wrapper
        live_mcp[name] = deployed

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
        apply=args.apply,
    )
    copytree(repo / "skills", home / "skills", apply=args.apply)
    remove_retired_managed_assets(home, apply=args.apply)
    copytree(repo / "bin", home / "bin", apply=args.apply)
    copyfile(repo / "config/.env.template", home / ".env.template", apply=args.apply)
    merge_live_config(repo, home, apply=args.apply)
    prune_workflow_sync_backups(home, apply=args.apply)

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
