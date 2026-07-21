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


def load_sync(repo: Path):
    path = repo / "scripts/workflow/sync_hermes_workflow_assets.py"
    spec = importlib.util.spec_from_file_location("workflow_sync_verify", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load sync script: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(repo: Path, home: Path) -> list[str]:
    repo = repo.resolve()
    home = home.resolve()
    if not (repo / "workflow-manifest.yaml").exists():
        raise RuntimeError("workflow-manifest.yaml is required")
    if not (repo / "config/managed-config-schema.yaml").exists():
        raise RuntimeError("managed-config-schema.yaml is required")

    home.mkdir(parents=True, exist_ok=True)
    sync = load_sync(repo)
    sync.copytree(repo / "skills", home / "skills", apply=True)
    sync.copytree(repo / "bin", home / "bin", apply=True)
    sync.copyfile(repo / "config/.env.template", home / ".env.template", apply=True)
    sync.merge_live_config(repo, home, apply=True)

    config = yaml.safe_load((home / "config.yaml").read_text(encoding="utf-8")) or {}
    required = {
        "display.streaming": config.get("display", {}).get("streaming") is True,
        "agent.reasoning_effort": config.get("agent", {}).get("reasoning_effort") == "low",
        "model.max_tokens": config.get("model", {}).get("max_tokens") == 8192,
        "model_picker.custom_lanes": bool(config.get("model_picker", {}).get("custom_lanes", {}).get("enabled")),
        "quick_commands": bool(config.get("quick_commands")),
        "context7": "context7" in (config.get("mcp_servers") or {}),
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
