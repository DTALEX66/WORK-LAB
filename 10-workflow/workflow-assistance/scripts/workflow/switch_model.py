#!/usr/bin/env python3
"""Plan-first Hermes model switcher using only official config operations."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Model IDs are intentionally never defaulted here.  The user chooses them
# explicitly with --model or the matching HERMES_*_MODEL environment variable.
KIMI_BASE_URL = os.environ.get("HERMES_KIMI_BASE_URL", "https://api.moonshot.cn/v1")
MISSING = object()


def selected_model(override: str | None, env_name: str, target: str) -> str:
    model = (override or os.environ.get(env_name, "")).strip()
    if not model:
        raise SystemExit(
            f"No model selected for {target}; pass --model MODEL or set {env_name}. "
            "The workflow never chooses a model automatically."
        )
    return model


def run(cmd: list[str], timeout: int = 30, check: bool = False) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(
        cmd,
        text=True,
        encoding='utf-8',
        errors='replace',
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    if check and cp.returncode != 0:
        raise SystemExit(f"command failed: {' '.join(cmd)}\n{cp.stdout or ''}")
    return cp


def hermes_home() -> Path:
    if os.environ.get('HERMES_HOME'):
        return Path(os.environ['HERMES_HOME'])
    if os.name == 'nt':
        return Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData/Local'))) / 'hermes'
    return Path.home() / '.hermes'


SECRET_PATTERNS = [
    (re.compile(r'Bearer\s+[A-Za-z0-9._~+/=-]{16,}', re.I), 'Bearer [REDACTED]'),
    (re.compile(r'eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}'), 'jwt-[REDACTED]'),
    (re.compile(r'github_pat_[A-Za-z0-9_]{20,}'), 'github_pat_[REDACTED]'),
    (re.compile(r'gh[pousr]_[A-Za-z0-9_]{20,}'), 'gh_[REDACTED]'),
    (re.compile(r'npm_[A-Za-z0-9]{20,}'), 'npm_[REDACTED]'),
    (re.compile(r'xox[baprs]-[A-Za-z0-9-]{10,}'), 'xox-[REDACTED]'),
    (re.compile(r'sk-[A-Za-z0-9_-]{8,}'), 'sk-[REDACTED]'),
    (re.compile(r'(?i)(access[_-]?token|refresh[_-]?token|id[_-]?token|bearer[_-]?token|api[_-]?key|secret|password)\s*[:=]\s*["\']?[^\s,}\]\"\']+'), r'\1=[REDACTED]'),
    (re.compile(r'(?i)(access[_-]?token|refresh[_-]?token|id[_-]?token|bearer[_-]?token|api[_-]?key|secret|password)["\']?\s*[:=]\s*["\'][^"\']+["\']'), r'\1=[REDACTED]'),
]


def redact(text: str) -> str:
    for pat, repl in SECRET_PATTERNS:
        text = pat.sub(repl, text)
    return text

def env_has(name: str) -> bool:
    """Check only the current process environment; never inspect Hermes .env."""

    return bool(os.environ.get(name))


def _config_value(data: dict, dotted_key: str) -> object:
    current: object = data
    for part in dotted_key.split('.'):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _get_config_value(key: str) -> object:
    """Read one non-secret field through the official Hermes CLI only."""

    cp = run(['hermes', 'config', 'get', '--json', key], timeout=30)
    if cp.returncode != 0:
        return MISSING
    try:
        return json.loads(cp.stdout.strip())
    except json.JSONDecodeError:
        return MISSING


def _restore_config(applied: list[tuple[str, object]]) -> list[str]:
    failures: list[str] = []
    for key, previous in reversed(applied):
        if previous is MISSING:
            restored = run(['hermes', 'config', 'unset', key], timeout=30)
            if restored.returncode != 0:
                failures.append(key)
        elif isinstance(previous, (str, int, float, bool)) or previous is None:
            restored = run(
                ['hermes', 'config', 'set', key, '' if previous is None else str(previous)],
                timeout=30,
            )
            if restored.returncode != 0:
                failures.append(key)
    return failures


def set_config(pairs: list[tuple[str, str]]) -> None:
    if not shutil.which('hermes'):
        raise SystemExit('hermes command not found')
    before = {key: _get_config_value(key) for key, _ in pairs}
    applied: list[tuple[str, object]] = []
    for key, value in pairs:
        cp = run(['hermes', 'config', 'set', key, value], timeout=30)
        print(redact(cp.stdout).strip() or f'set {key}')
        if cp.returncode != 0:
            rollback_failures = _restore_config(applied)
            suffix = f'; rollback failed for {rollback_failures}' if rollback_failures else ''
            raise SystemExit(f'config update failed at {key}; restored {len(applied)} prior field(s){suffix}')
        applied.append((key, before.get(key)))

    after = {key: _get_config_value(key) for key, _ in pairs}
    mismatches = [key for key, value in pairs if after.get(key) != value]
    if mismatches:
        rollback_failures = _restore_config(applied)
        suffix = f'; rollback failed for {rollback_failures}' if rollback_failures else ''
        raise SystemExit(
            'config verification failed; restored prior fields: '
            + ', '.join(mismatches)
            + suffix
        )


def build_action_plan(target: str, pairs: list[tuple[str, str]], *, approved: bool) -> dict:
    return {
        "schema_version": "workflow/action-plan/v1",
        "plan_id": f"hermes-model-switch-{target}",
        "task_id": "WL3-200",
        "status": "APPROVED" if approved else "WAITING_APPROVAL",
        "target": {
            "adapter": "hermes",
            "operation": "switch-model-route",
            "project_root": ".",
        },
        "steps": [
            {
                "id": f"set-{index}",
                "action": f"hermes config set {key}",
                "mode": "write",
                "side_effects": ["global Hermes user configuration"],
            }
            for index, (key, _value) in enumerate(pairs, start=1)
        ],
        "approval": {
            "approval_required": True,
            "status": "APPROVED" if approved else "PENDING",
            **({"approved_by": "explicit-cli-flag"} if approved else {}),
        },
        "rollback": {
            "available": True,
            "strategy": "read-before-write; restore previous value or official config unset when absent",
        },
        "constraints": {
            "allowed_paths": [],
            "forbidden_paths": ["credentials", "auth stores", "sessions", "memory"],
            "network": "explicit",
        },
    }


def plan_or_apply(
    target: str,
    pairs: list[tuple[str, str]],
    *,
    apply: bool,
    approved: bool,
) -> int:
    plan = build_action_plan(target, pairs, approved=approved)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if not apply:
        print("ACTION_PLAN_ONLY no configuration changed; use --apply --approved after review")
        return 0
    if not approved:
        print("ACTION_PLAN_BLOCKED approval_required=true use --approved after reviewing the plan")
        return 2
    set_config(pairs)
    print("ACTION_PLAN_READBACK_PASS")
    return 0


def codex_auth_present() -> bool:
    cp = run(['hermes', 'auth', 'list', 'openai-codex'], timeout=30)
    return cp.returncode == 0 and 'credentials' in cp.stdout.lower()


def live_marker(provider: str, model: str, marker: str) -> None:
    cp = run(
        ['hermes', 'chat', '--provider', provider, '-m', model, '-q', f'Reply exactly: {marker}', '-Q', '--toolsets', 'safe'],
        timeout=180,
    )
    if cp.returncode != 0 or marker not in cp.stdout.splitlines():
        raise SystemExit(f'LIVE verification failed for {provider}/{model}: {redact(cp.stdout)}')
    print(f'LIVE_OK provider={provider} model={model}')


def status() -> None:
    print('=== Hermes config summary ===')
    for key in ('model.provider', 'model.default'):
        cp = run(['hermes', 'config', 'get', '--json', key], timeout=30)
        print(f'{key}={redact(cp.stdout.strip()) if cp.returncode == 0 else "unavailable"}')
    print('\n=== Prerequisites ===')
    print(f'HERMES_HOME={hermes_home()}')
    print(f'KIMI_API_KEY={"present" if env_has("KIMI_API_KEY") or env_has("KIMI_CN_API_KEY") else "missing"}')
    print(f'DEEPSEEK_API_KEY={"present" if env_has("DEEPSEEK_API_KEY") else "missing"}')
    for name in ('HTTPS_PROXY', 'HTTP_PROXY', 'ALL_PROXY'):
        print(f'{name}={"declared" if env_has(name) else "not-declared"}')
    cp = run(['hermes', 'auth', 'list'], timeout=30)
    print('\n=== Auth providers (redacted) ===')
    print(redact(cp.stdout))


def main() -> int:
    ap = argparse.ArgumentParser(description='Switch Hermes between user-selected provider lanes')
    ap.add_argument('target', choices=['gpt', 'chatgpt', 'deepseek', 'dp', 'kimi', 'k3', 'kimi-fast', 'kimi-turbo', 'status'])
    ap.add_argument('--model', help='explicit model ID; required for every switch target')
    ap.add_argument('--no-verify', action='store_true', help='skip prerequisite checks')
    ap.add_argument('--live', action='store_true', help='run a real marker after writing config (uses provider quota)')
    ap.add_argument('--apply', action='store_true', help='apply the reviewed ActionPlan')
    ap.add_argument('--approved', action='store_true', help='confirm explicit approval for the global config write')
    args = ap.parse_args()

    if args.target == 'status':
        status()
        return 0

    if args.target in {'kimi', 'k3', 'kimi-fast', 'kimi-turbo'}:
        if args.apply and not args.no_verify and not (env_has('KIMI_API_KEY') or env_has('KIMI_CN_API_KEY')):
            raise SystemExit('KIMI_API_KEY/KIMI_CN_API_KEY missing in the current environment')
        if args.target == 'kimi-turbo':
            model = selected_model(args.model, 'HERMES_KIMI_TURBO_MODEL', args.target)
            label = 'Kimi selected model'
        elif args.target == 'kimi-fast':
            model = selected_model(args.model, 'HERMES_KIMI_FAST_MODEL', args.target)
            label = 'Kimi selected model'
        else:
            model = selected_model(args.model, 'HERMES_KIMI_MODEL', args.target)
            label = 'Kimi selected model'
        pairs = [
            ('model.provider', 'kimi-coding'),
            ('model.base_url', KIMI_BASE_URL),
            ('model.default', model),
        ]
        result = plan_or_apply(args.target, pairs, apply=args.apply, approved=args.approved)
        if result != 0 or not args.apply:
            return result
        if args.live:
            live_marker('kimi-coding', model, 'OK_KIMI_SWITCH_LIVE')
        print(f'Switched to {label}. Start a new session or /reset for it to take effect.')
        return 0

    if args.target in {'deepseek', 'dp'}:
        if args.apply and not args.no_verify and not env_has('DEEPSEEK_API_KEY'):
            raise SystemExit('DEEPSEEK_API_KEY missing in environment or Hermes .env')
        model = selected_model(args.model, 'HERMES_DEEPSEEK_MODEL', args.target)
        pairs = [
            ('model.provider', 'deepseek'),
            ('model.base_url', 'https://api.deepseek.com/v1'),
            ('model.default', model),
        ]
        result = plan_or_apply(args.target, pairs, apply=args.apply, approved=args.approved)
        if result != 0 or not args.apply:
            return result
        if args.live:
            live_marker('deepseek', model, 'OK_DEEPSEEK_SWITCH_LIVE')
        print('Switched to DeepSeek. Start a new session or /reset for it to take effect.')
        return 0

    if args.target in {'gpt', 'chatgpt'}:
        if args.apply and not args.no_verify and not codex_auth_present():
            raise SystemExit('No openai-codex OAuth credential found; run: hermes auth add openai-codex')
        model = selected_model(args.model, 'HERMES_GPT_MODEL', args.target)
        pairs = [
            ('model.provider', 'openai-codex'),
            ('model.default', model),
            ('model.base_url', ''),
        ]
        result = plan_or_apply(args.target, pairs, apply=args.apply, approved=args.approved)
        if result != 0 or not args.apply:
            return result
        if args.live:
            live_marker('openai-codex', model, 'OK_GPT_SWITCH_LIVE')
        print('Switched to GPT via openai-codex OAuth. Start a new session or /reset for it to take effect.')
        return 0
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
