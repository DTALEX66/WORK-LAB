#!/usr/bin/env python
"""Verify Workflow-assistance can populate an isolated empty Hermes home.

This is a structural portability contract. It never invokes Hermes, reads a
real home, copies credentials, or issues network/model requests.
"""
from __future__ import annotations

import argparse
import importlib.util
import tempfile
from pathlib import Path

import yaml


MANIFEST_SCHEMA_VERSION = 1
SUPPORTED_CONFIG_VERSION = 33
SUPPORTED_RUNTIME_FEATURES = {
    "quick_commands",
    "model_picker.custom_lanes",
    "hermes_config_check",
}


def load_sync(repo: Path):
    path = repo / "scripts/workflow/sync_hermes_workflow_assets.py"
    spec = importlib.util.spec_from_file_location("workflow_sync_verify", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load sync script: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_manifest(repo: Path) -> dict:
    path = repo / "workflow-manifest.yaml"
    if not path.exists():
        raise RuntimeError("workflow-manifest.yaml is required")
    manifest = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(manifest, dict) or manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise RuntimeError(f"workflow manifest schema_version must be {MANIFEST_SCHEMA_VERSION}")
    compatibility = manifest.get("compatibility")
    if not isinstance(compatibility, dict):
        raise RuntimeError("workflow manifest compatibility must be a mapping")
    if compatibility.get("config_version") != SUPPORTED_CONFIG_VERSION:
        raise RuntimeError(
            "workflow manifest config_version must be "
            f"{SUPPORTED_CONFIG_VERSION} for this portable verifier"
        )
    features = compatibility.get("required_runtime_features")
    if not isinstance(features, list) or not features or not all(isinstance(item, str) for item in features):
        raise RuntimeError("workflow manifest required_runtime_features must be a non-empty string list")
    unknown = sorted(set(features) - SUPPORTED_RUNTIME_FEATURES)
    if unknown:
        raise RuntimeError("workflow manifest has unsupported runtime features: " + ", ".join(unknown))
    return compatibility


def verify(repo: Path, home: Path) -> list[str]:
    repo = repo.resolve()
    home = home.resolve()
    if not (repo / "config/managed-config-schema.yaml").exists():
        raise RuntimeError("managed-config-schema.yaml is required")
    compatibility = load_manifest(repo)

    home.mkdir(parents=True, exist_ok=True)
    sync = load_sync(repo)
    sync.copytree(repo / "skills", home / "skills", apply=True)
    sync.copytree(repo / "bin", home / "bin", apply=True)
    sync.copyfile(repo / "config/.env.template", home / ".env.template", apply=True)
    sync.merge_live_config(repo, home, apply=True)

    config = yaml.safe_load((home / "config.yaml").read_text(encoding="utf-8")) or {}
    runtime_feature_checks = {
        "quick_commands": bool(config.get("quick_commands")),
        "model_picker.custom_lanes": bool(
            config.get("model_picker", {}).get("custom_lanes", {}).get("enabled")
        ),
        # This structural verifier proves the portable declaration only. A real
        # `hermes config check` belongs to an explicit isolated integration gate.
        "hermes_config_check": True,
    }
    missing_features = [
        feature for feature in compatibility["required_runtime_features"] if not runtime_feature_checks[feature]
    ]
    if missing_features:
        raise RuntimeError("isolated config lacks manifest runtime features: " + ", ".join(missing_features))

    context7 = (config.get("mcp_servers") or {}).get("context7")
    if not isinstance(context7, dict):
        raise RuntimeError("isolated config missing context7 mapping")
    wrappers = [home / "bin/hermes-npx.cmd", home / "bin/hermes-npx"]
    wrapper = next((candidate for candidate in wrappers if candidate.exists()), None)
    if wrapper is None or Path(str(context7.get("command", ""))).resolve() != wrapper.resolve():
        raise RuntimeError("isolated config context7 command does not reference the copied wrapper")
    args = context7.get("args") or []
    if not any(
        isinstance(arg, str)
        and arg.startswith("@upstash/context7-mcp@")
        and not arg.endswith("@latest")
        for arg in args
    ):
        raise RuntimeError("isolated config context7 package must use a pinned version")

    required = {
        "manifest.config_version": True,
        "manifest.required_runtime_features": True,
        "display.streaming": config.get("display", {}).get("streaming") is True,
        "agent.reasoning_effort": config.get("agent", {}).get("reasoning_effort") == "low",
        "model.max_tokens": config.get("model", {}).get("max_tokens") == 8192,
        "model_picker.custom_lanes": bool(config.get("model_picker", {}).get("custom_lanes", {}).get("enabled")),
        "quick_commands": bool(config.get("quick_commands")),
        "context7": "context7" in (config.get("mcp_servers") or {}),
        "context7.wrapper": True,
    }
    failed = [name for name, ok in required.items() if not ok]
    if failed:
        raise RuntimeError("isolated config missing: " + ", ".join(failed))
    if (home / ".env").exists() or (home / "auth.json").exists():
        raise RuntimeError("isolated verification must not create credentials")
    return sorted(required)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify portable workflow installation into an isolated Hermes home.")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--home", type=Path, help="Empty isolated home; omitted uses a temporary directory.")
    args = parser.parse_args(argv)
    if args.home:
        checks = verify(args.repo, args.home)
    else:
        with tempfile.TemporaryDirectory() as raw:
            checks = verify(args.repo, Path(raw) / "hermes")
    print("PORTABLE_INSTALL_VERIFY_PASS checks=" + ",".join(checks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
