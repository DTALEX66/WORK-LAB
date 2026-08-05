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
from typing import Callable, Iterable

try:
    import yaml
except Exception as exc:  # pragma: no cover - environment guard
    raise SystemExit(f"PyYAML is required: {exc}")


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
MANAGED_DISPLAY_KEYS = {"busy_input_mode", "language", "skin"}
MANAGED_SESSION_KEYS = {"auto_prune"}
MANAGED_MEMORY_KEYS = {
    "memory_enabled",
    "user_profile_enabled",
    "memory_char_limit",
    "user_char_limit",
}
# Root-level files are particularly sensitive in a user-owned Hermes home.
# Keep this a closed, reviewed inventory rather than treating schema input as
# authority to introduce future config/auth/environment targets.
APPROVED_MANAGED_FILE_MAPPINGS = frozenset({("config/SOUL.md", "SOUL.md")})


class PreservedConfigPromotionGuard:
    """Semantic user-owned config snapshot captured from the staged source."""

    def __init__(
        self,
        *,
        snapshot: dict,
        repo_data: dict,
        contract: dict,
        retiring_legacy_plugins: bool,
    ) -> None:
        self.snapshot = snapshot
        self.repo_data = repo_data
        self.contract = contract
        self.retiring_legacy_plugins = retiring_legacy_plugins


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
            "managed": {
                "display.busy_input_mode": "replace",
                "display.language": "replace",
                "display.skin": "replace",
                "sessions.auto_prune": "replace",
                "memory.memory_enabled": "replace",
                "memory.user_profile_enabled": "replace",
                "memory.memory_char_limit": "replace",
                "memory.user_char_limit": "replace",
                "platform_toolsets.cli": "replace",
                "mcp_servers": {"strategy": "merge_owned", "owned_names": ["context7"]},
                "hooks.pre_tool_call": "replace_owned_matcher",
                "plugins.enabled": "merge_additive",
            },
            "preserved": [
                "model.provider",
                "model.default",
                "model.base_url",
                "model.api_key",
                "model.other",
                "credentials",
                "mcp_servers.user_defined",
                "quick_commands.user_defined",
                "model_picker.user_defined",
                "plugins.user_enabled",
            ],
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


def managed_mcp_names(contract: dict) -> set[str]:
    """Return exactly the MCP names the declarative contract grants to the pack."""

    managed = contract.get("managed")
    mcp_contract = managed.get("mcp_servers") if isinstance(managed, dict) else None
    if not isinstance(mcp_contract, dict) or mcp_contract.get("strategy") != "merge_owned":
        raise ValueError("managed config contract must define mcp_servers merge_owned strategy")
    names = mcp_contract.get("owned_names")
    if not isinstance(names, list) or not names or not all(isinstance(name, str) and name for name in names):
        raise ValueError("managed config contract mcp_servers.owned_names must be a non-empty string list")
    if len(set(names)) != len(names):
        raise ValueError("managed config contract mcp_servers.owned_names must be unique")
    return set(names)


def snapshot_preserved_live_config(
    live_data: dict,
    repo_data: dict,
    contract: dict,
    *,
    retiring_legacy_plugins: bool = False,
) -> dict:
    """Capture the user-owned config surface before a workflow overlay merge.

    The ownership contract intentionally grants the repository a narrow set of
    direct keys plus three merge-owned collections.  Everything else is a live
    user choice and must remain semantically identical after a future sync.
    This snapshot contains no rendered configuration and is only used for an
    in-process equality check before a staged config can be promoted.
    """

    managed = contract.get("managed")
    if not isinstance(managed, dict):
        raise ValueError("managed config contract must define managed mappings")

    managed_children: dict[str, set[str | None]] = {}
    for raw_path in managed:
        if not isinstance(raw_path, str) or not raw_path:
            raise ValueError("managed config paths must be non-empty strings")
        root, *children = raw_path.split(".")
        managed_children.setdefault(root, set()).add(children[0] if children else None)

    snapshot: dict = {}
    for root, value in live_data.items():
        children = managed_children.get(root)
        if children is None:
            snapshot[root] = deepcopy(value)
            continue
        if None in children:
            # Whole-root merge strategies (currently MCP servers) receive a
            # narrower, ownership-aware snapshot below.
            continue
        if not isinstance(value, dict):
            snapshot[root] = deepcopy(value)
            continue
        preserved_children = {
            key: deepcopy(child)
            for key, child in value.items()
            if key not in children
        }
        if preserved_children:
            snapshot[root] = preserved_children

    live_mcp = live_data.get("mcp_servers")
    if isinstance(live_mcp, dict):
        owned_mcp_names = managed_mcp_names(contract)
        user_mcp = {
            name: deepcopy(value)
            for name, value in live_mcp.items()
            if name not in owned_mcp_names
        }
        if user_mcp:
            snapshot["mcp_servers.user_defined"] = user_mcp

    live_hooks = live_data.get("hooks")
    if isinstance(live_hooks, dict):
        pre_tool = live_hooks.get("pre_tool_call")
        if isinstance(pre_tool, list):
            user_pre_tool = [
                deepcopy(hook)
                for hook in pre_tool
                if not isinstance(hook, dict) or hook.get("matcher") != "terminal"
            ]
            if user_pre_tool:
                snapshot["hooks.pre_tool_call.user_defined"] = user_pre_tool

    live_plugins = live_data.get("plugins")
    repo_plugins = repo_data.get("plugins")
    if isinstance(live_plugins, dict) and isinstance(repo_plugins, dict):
        current_enabled = live_plugins.get("enabled")
        repo_enabled = repo_plugins.get("enabled")
        if isinstance(current_enabled, list) and isinstance(repo_enabled, list):
            managed_plugin_names = set(repo_enabled)
            if retiring_legacy_plugins:
                managed_plugin_names.update(RETIRED_MANAGED_PLUGINS)
            user_enabled = [
                name
                for name in current_enabled
                if name not in managed_plugin_names
            ]
            if user_enabled:
                snapshot["plugins.user_enabled"] = user_enabled

    return snapshot


def assert_preserved_live_config(
    snapshot: dict,
    live_data: dict,
    repo_data: dict,
    contract: dict,
    *,
    retiring_legacy_plugins: bool = False,
) -> None:
    """Fail closed if a workflow sync changed any user-owned config state."""

    if snapshot != snapshot_preserved_live_config(
        live_data,
        repo_data,
        contract,
        retiring_legacy_plugins=retiring_legacy_plugins,
    ):
        raise ValueError("preserved live config changed by workflow sync")


def assert_preserved_live_config_before_promotion(
    guard: PreservedConfigPromotionGuard,
    home: Path,
) -> None:
    """Reject a live user-config change immediately before config replacement."""

    live_cfg = home / "config.yaml"
    live_data = yaml.safe_load(live_cfg.read_text(encoding="utf-8")) or {} if live_cfg.exists() else {}
    if not isinstance(live_data, dict):
        raise ValueError("live config root must be a mapping before workflow promotion")
    assert_preserved_live_config(
        guard.snapshot,
        live_data,
        guard.repo_data,
        guard.contract,
        retiring_legacy_plugins=guard.retiring_legacy_plugins,
    )


def load_managed_skill_roots(repo: Path) -> tuple[str, ...]:
    """Return the exact repository-owned skill roots declared by the contract."""

    contract = load_config_contract(repo)
    workflow = contract.get("global_workflow")
    roots = workflow.get("owned_asset_roots") if isinstance(workflow, dict) else None
    if not isinstance(roots, list) or not roots:
        raise ValueError("managed config contract must declare exact owned_asset_roots")

    normalized: list[str] = []
    for raw in roots:
        if not isinstance(raw, str):
            raise ValueError("owned_asset_roots entries must be strings")
        relative = Path(raw)
        if relative.is_absolute() or ".." in relative.parts or relative.parts[:1] != ("skills",):
            raise ValueError(f"invalid managed skill root: {raw}")
        value = relative.as_posix()
        if value in normalized:
            raise ValueError(f"duplicate managed skill root: {value}")
        source = repo / relative
        if not (source / "SKILL.md").is_file():
            raise ValueError(f"managed skill root is missing SKILL.md: {value}")
        normalized.append(value)
    return tuple(normalized)


def load_managed_binary_paths(repo: Path) -> tuple[str, ...]:
    """Return exact repository-owned binary/launcher paths from the contract."""

    contract = load_config_contract(repo)
    workflow = contract.get("global_workflow")
    paths = workflow.get("owned_binary_paths") if isinstance(workflow, dict) else None
    if not isinstance(paths, list) or not paths:
        raise ValueError("managed config contract must declare exact owned_binary_paths")

    normalized: list[str] = []
    for raw in paths:
        if not isinstance(raw, str):
            raise ValueError("owned_binary_paths entries must be strings")
        relative = Path(raw)
        if relative.is_absolute() or ".." in relative.parts or relative.parts[:1] != ("bin",):
            raise ValueError(f"invalid managed binary path: {raw}")
        value = relative.as_posix()
        if value in normalized:
            raise ValueError(f"duplicate managed binary path: {value}")
        if not (repo / relative).is_file():
            raise ValueError(f"managed binary path is missing: {value}")
        normalized.append(value)
    return tuple(normalized)


def load_managed_file_mappings(repo: Path) -> tuple[tuple[str, str], ...]:
    """Return exact repository-file to live-file mappings from the contract."""

    contract = load_config_contract(repo)
    workflow = contract.get("global_workflow")
    mappings = workflow.get("owned_file_mappings") if isinstance(workflow, dict) else None
    if not isinstance(mappings, list) or not mappings:
        raise ValueError("managed config contract must declare exact owned_file_mappings")

    normalized: list[tuple[str, str]] = []
    targets: set[str] = set()
    for raw in mappings:
        if not isinstance(raw, dict) or set(raw) != {"source", "target"}:
            raise ValueError("owned_file_mappings entries must contain only source and target")
        source_raw = raw["source"]
        target_raw = raw["target"]
        if not isinstance(source_raw, str) or not isinstance(target_raw, str):
            raise ValueError("owned_file_mappings source and target must be strings")
        source = Path(source_raw)
        target = Path(target_raw)
        if (
            source.is_absolute()
            or ".." in source.parts
            or source.parts[:1] != ("config",)
            or not (repo / source).is_file()
        ):
            raise ValueError(f"invalid managed file source: {source_raw}")
        if (
            target.is_absolute()
            or ".." in target.parts
            or len(target.parts) != 1
            or target.name != target_raw
        ):
            raise ValueError(f"invalid managed file target: {target_raw}")
        source_value = source.as_posix()
        target_value = target.as_posix()
        if target_value in targets:
            raise ValueError(f"duplicate managed file target: {target_value}")
        targets.add(target_value)
        normalized.append((source_value, target_value))
    if frozenset(normalized) != APPROVED_MANAGED_FILE_MAPPINGS:
        raise ValueError("owned_file_mappings must exactly match the approved managed file mapping allowlist")
    return tuple(normalized)


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


def replace_managed_skill_trees(
    repo: Path,
    staging: Path,
    managed_roots: Iterable[str],
) -> None:
    """Replace repo-owned skill directories without retaining stale live files.

    The live skills root also contains Hermes-bundled and user-installed skills,
    so replacing the whole root would destroy unrelated data. A plain
    ``copytree(..., dirs_exist_ok=True)`` is not sufficient either: files that
    were removed from an owned skill in the repository would remain active in
    the live directory. Replace only the exact subtrees declared by the reviewed
    ownership contract.
    """

    for relative_text in managed_roots:
        relative = Path(relative_text)
        source = repo / relative
        target = staging / relative
        print(f"replace managed skill tree: {source} -> {target}")
        if target.exists() or target.is_symlink():
            _remove_path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)


def atomic_replace_paths(
    staging: Path,
    home: Path,
    rels: Iterable[str],
    *,
    remove_rels: Iterable[str] = (),
    before_replace: Callable[[str], None] | None = None,
) -> None:
    """Replace managed roots as one rollback-capable filesystem transaction."""
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    rollback = home / f".workflow-assistance-rollback-{stamp}"
    records: list[tuple[Path, Path | None, bool]] = []
    rollback_failed = False
    operation_failed = False
    removal_set = set(remove_rels)
    rollback.mkdir(parents=True, exist_ok=False)
    try:
        for relative in rels:
            source = staging / relative
            source_exists = source.exists() or source.is_symlink()
            if not source_exists and relative not in removal_set:
                continue
            if before_replace is not None:
                before_replace(relative)
            target = home / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            previous = rollback / relative
            had_target = target.exists() or target.is_symlink()
            records.append((target, previous if had_target else None, False))
            if had_target:
                previous.parent.mkdir(parents=True, exist_ok=True)
                os.replace(target, previous)
            if source_exists:
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


def prepare_staging(
    repo: Path,
    home: Path,
    managed_roots: tuple[str, ...],
    managed_binaries: tuple[str, ...],
    managed_file_mappings: tuple[tuple[str, str], ...],
    *,
    include_config: bool = False,
) -> tuple[Path, PreservedConfigPromotionGuard | None]:
    """Build a complete managed view without mutating the live Hermes home."""
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    # Keep nested managed skill paths below legacy Windows MAX_PATH limits.
    staging = home / f".wa-stg-{stamp}"
    staging.mkdir(parents=True, exist_ok=False)
    try:
        if include_config:
            for relative in ("config.yaml", ".workflow-assistance-state.yaml"):
                live = home / relative
                if live.exists():
                    (staging / relative).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(live, staging / relative)
        replace_managed_skill_trees(repo, staging, managed_roots)
        for relative in managed_binaries:
            copyfile(repo / relative, staging / relative, apply=True)
        for source_relative, target_relative in managed_file_mappings:
            copyfile(repo / source_relative, staging / target_relative, apply=True)
        copyfile(repo / "config/.env.template", staging / ".env.template", apply=True)
        config_guard = (
            merge_live_config(repo, staging, apply=True, wrapper_root=home) if include_config else None
        )
        return staging, config_guard
    except Exception:
        try:
            shutil.rmtree(staging)
        except Exception as cleanup_error:
            print(f"STAGING_CLEANUP_INCOMPLETE preserved={staging}")
            raise RuntimeError(f"failed to clean partial staging directory: {staging}") from cleanup_error
        raise


def merge_live_config(
    repo: Path,
    home: Path,
    *,
    apply: bool,
    wrapper_root: Path | None = None,
) -> PreservedConfigPromotionGuard | None:
    """Merge portable entries while preserving live provider/model and custom MCPs."""

    repo_cfg = repo / "config/config.yaml"
    live_cfg = home / "config.yaml"
    if not repo_cfg.exists():
        print("skip config merge: missing repository config")
        return None
    contract = load_config_contract(repo)
    repo_data = yaml.safe_load(repo_cfg.read_text(encoding="utf-8")) or {}
    live_data = (
        yaml.safe_load(live_cfg.read_text(encoding="utf-8")) or {}
        if live_cfg.exists()
        else {}
    )
    if not isinstance(live_data, dict) or not isinstance(repo_data, dict):
        raise ValueError("config roots must be mappings")
    state_file = home / ".workflow-assistance-state.yaml"
    state = (
        yaml.safe_load(state_file.read_text(encoding="utf-8")) or {}
        if state_file.exists()
        else {}
    )
    if not isinstance(state, dict):
        raise ValueError("workflow assistance state must be a mapping")
    retire_legacy_plugins = state.get("plugin_retirement_migration", 0) < PLUGIN_RETIREMENT_MIGRATION
    preserved_snapshot = snapshot_preserved_live_config(
        live_data,
        repo_data,
        contract,
        retiring_legacy_plugins=retire_legacy_plugins,
    )

    live_mcp = live_data.setdefault("mcp_servers", {})
    repo_mcp = repo_data.get("mcp_servers") or {}
    if not isinstance(live_mcp, dict) or not isinstance(repo_mcp, dict):
        raise ValueError("mcp_servers must be mappings")
    owned_mcp_names = managed_mcp_names(contract)
    undeclared_repo_mcp = set(repo_mcp) - owned_mcp_names
    if undeclared_repo_mcp:
        raise ValueError(
            "repository config declares MCPs outside managed ownership: " + ", ".join(sorted(undeclared_repo_mcp))
        )
    for retired in owned_mcp_names - set(repo_mcp):
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
    if isinstance(plugins, dict):
        current_enabled = plugins.get("enabled") or []
        retained = (
            [name for name in current_enabled if name not in RETIRED_MANAGED_PLUGINS]
            if retire_legacy_plugins
            else list(current_enabled)
        )
        plugins["enabled"] = list(dict.fromkeys(retained + repo_enabled))

    repo_display = repo_data.get("display") or {}
    live_display = live_data.setdefault("display", {})
    if not isinstance(repo_display, dict) or not isinstance(live_display, dict):
        raise ValueError("display must be a mapping")
    for key in MANAGED_DISPLAY_KEYS:
        if key in repo_display:
            live_display[key] = repo_display[key]

    repo_sessions = repo_data.get("sessions") or {}
    live_sessions = live_data.setdefault("sessions", {})
    if not isinstance(repo_sessions, dict) or not isinstance(live_sessions, dict):
        raise ValueError("sessions must be mappings")
    for key in MANAGED_SESSION_KEYS:
        if key in repo_sessions:
            live_sessions[key] = deepcopy(repo_sessions[key])

    repo_memory = repo_data.get("memory") or {}
    live_memory = live_data.setdefault("memory", {})
    if not isinstance(repo_memory, dict) or not isinstance(live_memory, dict):
        raise ValueError("memory must be mappings")
    for key in MANAGED_MEMORY_KEYS:
        if key in repo_memory:
            live_memory[key] = deepcopy(repo_memory[key])

    repo_platforms = repo_data.get("platform_toolsets") or {}
    live_platforms = live_data.setdefault("platform_toolsets", {})
    if not isinstance(repo_platforms, dict) or not isinstance(live_platforms, dict):
        raise ValueError("platform_toolsets must be mappings")
    if "cli" in repo_platforms:
        cli = repo_platforms["cli"]
        if not isinstance(cli, list) or not all(isinstance(name, str) for name in cli):
            raise ValueError("platform_toolsets.cli must be a list of names")
        live_platforms["cli"] = deepcopy(cli)

    # model picker lanes, and model-switching commands
    # are deliberately outside repository ownership. This merge leaves their
    # semantic values untouched, although YAML serialization may normalize the
    # file representation.
    assert_preserved_live_config(
        preserved_snapshot,
        live_data,
        repo_data,
        contract,
        retiring_legacy_plugins=retire_legacy_plugins,
    )
    managed_paths = ",".join(sorted(contract["managed"]))
    print("merge live config: contract managed =", managed_paths)
    print("merge live config: model/provider routing = preserved, unmanaged")
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
    return PreservedConfigPromotionGuard(
        snapshot=preserved_snapshot,
        repo_data=repo_data,
        contract=contract,
        retiring_legacy_plugins=retire_legacy_plugins,
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
    managed_roots = load_managed_skill_roots(repo)
    managed_binaries = load_managed_binary_paths(repo)
    managed_file_mappings = load_managed_file_mappings(repo)
    managed_files = tuple(target for _, target in managed_file_mappings)
    retired_roots = tuple(f"skills/{relative}" for relative in RETIRED_MANAGED_SKILL_ASSETS)
    if include_backup:
        backup_paths(
            home,
            tuple(
                dict.fromkeys(
                    (
                        ".env.template",
                        *managed_roots,
                        *managed_binaries,
                        *managed_files,
                        *retired_roots,
                    )
                )
            ),
            apply=apply,
        )
    if apply:
        staging, _ = prepare_staging(
            repo,
            home,
            managed_roots,
            managed_binaries,
            managed_file_mappings,
            include_config=False,
        )

        atomic_replace_paths(
            staging,
            home,
            tuple(
                dict.fromkeys(
                    (
                        *managed_roots,
                        *managed_binaries,
                        *managed_files,
                        ".env.template",
                        *retired_roots,
                    )
                )
            ),
            remove_rels=retired_roots,
        )
    else:
        for relative in managed_roots:
            copytree(repo / relative, home / relative, apply=False)
        remove_retired_managed_assets(home, apply=False)
        for relative in managed_binaries:
            copyfile(repo / relative, home / relative, apply=False)
        for source_relative, target_relative in managed_file_mappings:
            copyfile(repo / source_relative, home / target_relative, apply=False)
        copyfile(repo / "config/.env.template", home / ".env.template", apply=False)
        print("skip mixed-ownership live config.yaml: portable sync never promotes it")
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
