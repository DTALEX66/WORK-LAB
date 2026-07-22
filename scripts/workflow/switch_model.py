#!/usr/bin/env python3
"""Safe Hermes model switcher for the DTALEX66 Hermes workflow.

No secrets are printed. The script only writes Hermes config via official
`hermes config set` commands and performs prerequisite diagnostics.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import yaml


GPT_MODEL = os.environ.get("HERMES_GPT_MODEL", "gpt-5.6-sol")
DEEPSEEK_MODEL = os.environ.get("HERMES_DEEPSEEK_MODEL", "deepseek-v4-flash")
KIMI_MODEL = os.environ.get("HERMES_KIMI_MODEL", "kimi-k3")
KIMI_FAST_MODEL = os.environ.get("HERMES_KIMI_FAST_MODEL", "kimi-k2.7-code")
KIMI_TURBO_MODEL = os.environ.get("HERMES_KIMI_TURBO_MODEL", "kimi-k2.7-code-highspeed")
KIMI_BASE_URL = os.environ.get("HERMES_KIMI_BASE_URL", "https://api.moonshot.cn/v1")


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

def port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def env_has(name: str) -> bool:
    if os.environ.get(name):
        return True
    p = hermes_home() / '.env'
    if not p.exists():
        return False
    for line in p.read_text(encoding='utf-8', errors='ignore').splitlines():
        if line.strip().startswith(name + '=') and line.split('=', 1)[1].strip():
            return True
    return False


def _config_value(data: dict, dotted_key: str) -> object:
    current: object = data
    for part in dotted_key.split('.'):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _load_config_snapshot() -> dict:
    config_path = hermes_home() / 'config.yaml'
    if not config_path.exists():
        return {}
    loaded = yaml.safe_load(config_path.read_text(encoding='utf-8')) or {}
    if not isinstance(loaded, dict):
        raise SystemExit('Hermes config root must be a mapping')
    return loaded


def _restore_config(applied: list[tuple[str, object]]) -> None:
    for key, previous in reversed(applied):
        if isinstance(previous, (str, int, float, bool)) or previous is None:
            run(['hermes', 'config', 'set', key, '' if previous is None else str(previous)], timeout=30)


def set_config(pairs: list[tuple[str, str]]) -> None:
    if not shutil.which('hermes'):
        raise SystemExit('hermes command not found')
    before = _load_config_snapshot()
    applied: list[tuple[str, object]] = []
    for key, value in pairs:
        cp = run(['hermes', 'config', 'set', key, value], timeout=30)
        print(redact(cp.stdout).strip() or f'set {key}')
        if cp.returncode != 0:
            _restore_config(applied)
            raise SystemExit(f'config update failed at {key}; restored {len(applied)} prior field(s)')
        applied.append((key, _config_value(before, key)))

    after = _load_config_snapshot()
    mismatches = [key for key, value in pairs if _config_value(after, key) != value]
    if mismatches:
        _restore_config(applied)
        raise SystemExit('config verification failed; restored prior fields: ' + ', '.join(mismatches))


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
    print('=== Hermes config ===')
    cp = run(['hermes', 'config'], timeout=30)
    for line in redact(cp.stdout).splitlines():
        if any(k in line for k in ['provider', 'default', 'base_url', 'api_key']):
            print(line)
    print('\n=== Prerequisites ===')
    print(f'HERMES_HOME={hermes_home()}')
    print(f'KIMI_API_KEY={"present" if env_has("KIMI_API_KEY") or env_has("KIMI_CN_API_KEY") else "missing"}')
    print(f'DEEPSEEK_API_KEY={"present" if env_has("DEEPSEEK_API_KEY") else "missing"}')
    print(f'CC Switch 127.0.0.1:7890={"open" if port_open("127.0.0.1", 7890) else "closed"}')
    print(f'Codex proxy 127.0.0.1:15721={"open" if port_open("127.0.0.1", 15721) else "closed"}')
    cp = run(['hermes', 'auth', 'list'], timeout=30)
    print('\n=== Auth providers (redacted) ===')
    print(redact(cp.stdout))


def main() -> int:
    ap = argparse.ArgumentParser(description='Switch Hermes between the curated DTALEX66 model lanes')
    ap.add_argument('target', choices=['gpt', 'chatgpt', 'deepseek', 'dp', 'kimi', 'k3', 'kimi-fast', 'kimi-turbo', 'status'])
    ap.add_argument('--no-verify', action='store_true', help='skip prerequisite checks')
    ap.add_argument('--live', action='store_true', help='run a real marker after writing config (uses provider quota)')
    args = ap.parse_args()

    if args.target == 'status':
        status()
        return 0

    if args.target in {'kimi', 'k3', 'kimi-fast', 'kimi-turbo'}:
        if not args.no_verify and not (env_has('KIMI_API_KEY') or env_has('KIMI_CN_API_KEY')):
            raise SystemExit('KIMI_API_KEY/KIMI_CN_API_KEY missing in environment or Hermes .env')
        if args.target == 'kimi-turbo':
            model = KIMI_TURBO_MODEL
            label = 'Kimi K2.7 Code HighSpeed'
        elif args.target == 'kimi-fast':
            model = KIMI_FAST_MODEL
            label = 'Kimi K2.7 Code'
        else:
            model = KIMI_MODEL
            label = 'Kimi K3'
        set_config([
            ('model.provider', 'kimi-coding'),
            ('model.base_url', KIMI_BASE_URL),
            ('model.default', model),
            ('model.api_key', ''),
        ])
        if args.live:
            live_marker('kimi-coding', model, 'OK_KIMI_SWITCH_LIVE')
        print(f'Switched to {label}. Start a new session or /reset for it to take effect.')
        return 0

    if args.target in {'deepseek', 'dp'}:
        if not args.no_verify and not env_has('DEEPSEEK_API_KEY'):
            raise SystemExit('DEEPSEEK_API_KEY missing in environment or Hermes .env')
        set_config([
            ('model.provider', 'deepseek'),
            ('model.base_url', 'https://api.deepseek.com/v1'),
            ('model.default', DEEPSEEK_MODEL),
            ('model.api_key', ''),
        ])
        if args.live:
            live_marker('deepseek', DEEPSEEK_MODEL, 'OK_DEEPSEEK_SWITCH_LIVE')
        print('Switched to DeepSeek. Start a new session or /reset for it to take effect.')
        return 0

    if args.target in {'gpt', 'chatgpt'}:
        if not args.no_verify and not codex_auth_present():
            raise SystemExit('No openai-codex OAuth credential found; run: hermes auth add openai-codex')
        set_config([
            ('model.provider', 'openai-codex'),
            ('model.default', GPT_MODEL),
            ('model.base_url', ''),
            ('model.api_key', ''),
        ])
        if args.live:
            live_marker('openai-codex', GPT_MODEL, 'OK_GPT_SWITCH_LIVE')
        print('Switched to GPT via openai-codex OAuth. Start a new session or /reset for it to take effect.')
        return 0
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
