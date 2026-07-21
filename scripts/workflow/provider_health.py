#!/usr/bin/env python
"""Create a secret-free provider/model inventory with optional live validation.

Without --live, all configured lanes are intentionally UNVERIFIED. This keeps
health reporting free of tokens, network calls and credential contents.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path

import yaml


def configured_models(config: dict) -> dict[str, dict[str, str]]:
    models: dict[str, dict[str, str]] = {}
    picker = ((config.get("model_picker") or {}).get("custom_lanes") or {})
    for lane in picker.get("lanes") or []:
        if not isinstance(lane, dict):
            continue
        provider = str(lane.get("provider") or "")
        for model in lane.get("models") or []:
            if provider and isinstance(model, str):
                models[f"{provider}/{model}"] = {"provider": provider, "model": model}
    route = config.get("model") or {}
    provider = route.get("provider")
    model = route.get("default")
    if isinstance(provider, str) and isinstance(model, str):
        models.setdefault(f"{provider}/{model}", {"provider": provider, "model": model})
    return models


def live_check(provider: str, model: str) -> str:
    marker = "WORKFLOW_PROVIDER_HEALTH_OK"
    result = subprocess.run(
        ["hermes", "chat", "--provider", provider, "-m", model, "-q", f"Reply exactly: {marker}", "-Q", "--toolsets", "safe"],
        text=True,
        capture_output=True,
        check=False,
        timeout=180,
    )
    return "LIVE_OK" if result.returncode == 0 and marker in result.stdout.splitlines() else "LIVE_FAILED"


def build_report(config: dict, *, live: bool) -> dict[str, object]:
    entries = configured_models(config)
    statuses: dict[str, dict[str, str]] = {}
    for key, entry in entries.items():
        status = live_check(entry["provider"], entry["model"]) if live else "UNVERIFIED"
        statuses[key] = {**entry, "status": status}
    overall = "LIVE_OK" if statuses and all(item["status"] == "LIVE_OK" for item in statuses.values()) else "UNVERIFIED"
    if live and any(item["status"] == "LIVE_FAILED" for item in statuses.values()):
        overall = "LIVE_FAILED"
    return {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "secret_free": True,
        "overall_status": overall,
        "models": statuses,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a secret-free provider/model health report.")
    parser.add_argument("--config", type=Path, default=Path("config/config.yaml"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--live", action="store_true", help="Run real marker requests; consumes provider quota.")
    args = parser.parse_args(argv)
    config = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
    report = build_report(config, live=args.live)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PROVIDER_HEALTH_REPORT status={report['overall_status']} models={len(report['models'])} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
