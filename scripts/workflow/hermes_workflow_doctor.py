#!/usr/bin/env python3
"""Audit the Hermes ⇄ GPT/DeepSeek ⇄ CC Switch ⇄ Codex workflow.

The report is redacted by default and safe to paste into issues/PRs. It checks:
- Hermes config/auth/MCP state
- GPT via CC Switch proxy reachability
- DeepSeek reachability
- Hermes bundled Node vs PATH Node, and MCP smoke tests
- Codex CLI/proxy discovery
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

SECRET_PATTERNS = [
    (re.compile(r'sk-[A-Za-z0-9_-]{8,}'), 'sk-[REDACTED]'),
    (re.compile(r'(?i)(access_token|refresh_token|id_token|bearer_token|api[_-]?key|token|secret|password)\s*[:=]\s*[^\s,}\]]+'), r'\1=[REDACTED]'),
]


def redact(text: str) -> str:
    for pat, repl in SECRET_PATTERNS:
        text = pat.sub(repl, text)
    return text


def run(cmd, timeout=30, env=None):
    try:
        cp = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, env=env)
        return cp.returncode, redact(cp.stdout.strip())
    except Exception as e:
        return 124, f'{type(e).__name__}: {e}'


def port_open(host, port, timeout=1.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def hermes_home():
    if os.environ.get('HERMES_HOME'):
        return Path(os.environ['HERMES_HOME'])
    if os.name == 'nt':
        return Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData/Local'))) / 'hermes'
    return Path.home() / '.hermes'


def hermes_node_dir():
    h = hermes_home()
    for p in [h / 'node', Path.home() / 'AppData/Local/hermes/node', Path('/c/Users') / os.environ.get('USERNAME', '') / 'AppData/Local/hermes/node']:
        if (p / ('node.exe' if os.name == 'nt' else 'node')).exists() or (p / 'node.exe').exists():
            return p
    return None


def print_section(title):
    print(f'\n=== {title} ===')


def print_cmd(label, cmd, timeout=30, env=None, max_lines=40):
    code, out = run(cmd, timeout=timeout, env=env)
    status = 'OK' if code == 0 else f'WARN exit={code}'
    print(f'[{status}] {label}: {" ".join(map(str, cmd))}')
    if out:
        lines = out.splitlines()
        for line in lines[:max_lines]:
            print('  ' + line)
        if len(lines) > max_lines:
            print(f'  ... ({len(lines)-max_lines} more lines)')
    return code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true', help='reserved for future machine-readable output')
    args = ap.parse_args()

    failures = []
    hhome = hermes_home()
    print('Hermes workflow doctor (redacted)')
    print(f'HERMES_HOME={hhome}')

    print_section('Hermes')
    if not shutil.which('hermes'):
        print('[FAIL] hermes command not found')
        failures.append('hermes missing')
    else:
        print_cmd('version', ['hermes', '--version'])
        print_cmd('config path', ['hermes', 'config', 'path'])
        print_cmd('env path', ['hermes', 'config', 'env-path'])
        print_cmd('auth list', ['hermes', 'auth', 'list'], max_lines=80)
        print_cmd('mcp list', ['hermes', 'mcp', 'list'], max_lines=80)

    print_section('Network / Providers')
    cc = port_open('127.0.0.1', 7890)
    codex_proxy = port_open('127.0.0.1', 15721)
    cc_status = 'OK' if cc else 'WARN'
    codex_status = 'OK' if codex_proxy else 'WARN'
    print(f'[{cc_status}] CC Switch proxy 127.0.0.1:7890 = {"open" if cc else "closed"}')
    print(f'[{codex_status}] Codex local proxy 127.0.0.1:15721 = {"open" if codex_proxy else "closed"}')
    print_cmd('DeepSeek HEAD', ['curl', '-sI', '--max-time', '8', 'https://api.deepseek.com'], timeout=12, max_lines=4)
    if cc:
        print_cmd('ChatGPT via CC Switch', ['curl', '-sI', '--proxy', 'http://127.0.0.1:7890', '--max-time', '12', 'https://chatgpt.com'], timeout=15, max_lines=5)
        print_cmd('Auth OpenAI via CC Switch', ['curl', '-sI', '--proxy', 'http://127.0.0.1:7890', '--max-time', '12', 'https://auth.openai.com'], timeout=15, max_lines=5)

    print_section('Node / MCP smoke')
    print_cmd('PATH node', ['node', '--version'])
    path_npm = shutil.which('npm') or shutil.which('npm.cmd')
    if path_npm:
        print_cmd('PATH npm', [path_npm, '--version'])
    else:
        print('[WARN] PATH npm not found')
    nodedir = hermes_node_dir()
    env = os.environ.copy()
    if nodedir:
        env['PATH'] = str(nodedir) + os.pathsep + env.get('PATH', '')
        node_cmd = nodedir / ('node.exe' if (nodedir / 'node.exe').exists() else 'node')
        npx_cmd = nodedir / ('npx.cmd' if (nodedir / 'npx.cmd').exists() else 'npx')
        print(f'[OK] Hermes bundled node dir: {nodedir}')
        print_cmd('Hermes node', [str(node_cmd), '--version'], env=env)
        print_cmd('Context7 help', [str(npx_cmd), '-y', '@upstash/context7-mcp', '--help'], timeout=60, env=env, max_lines=12)
        print_cmd('Sequential Thinking help', [str(npx_cmd), '-y', '@modelcontextprotocol/server-sequential-thinking', '--help'], timeout=60, env=env, max_lines=12)
        print_cmd('public-apis help', [str(npx_cmd), '-y', 'public-apis-mcp@latest', '--help'], timeout=60, env=env, max_lines=12)
    else:
        print('[WARN] Hermes bundled node not found; MCPs will rely on PATH node')

    print_section('Codex')
    candidates = []
    for p in [Path.home() / '.codex/plugins/.plugin-appserver/codex.exe', Path.home() / 'AppData/Local/OpenAI/Codex/bin/codex.exe']:
        if p.exists():
            candidates.append(p)
    if shutil.which('codex'):
        candidates.insert(0, Path(shutil.which('codex')))
    if candidates:
        for p in candidates[:3]:
            print_cmd(f'codex version ({p})', [str(p), '--version'], timeout=20, max_lines=5)
    else:
        print('[WARN] codex executable not found in PATH or known plugin path')
    cfg = Path.home() / '.codex/config.toml'
    if cfg.exists():
        print('[OK] Codex config found; redacted key lines:')
        for line in cfg.read_text(encoding='utf-8', errors='ignore').splitlines()[:80]:
            if any(k in line.lower() for k in ['model', 'base_url', 'wire_api', 'mcp_servers', 'enabled']):
                print('  ' + redact(line))

    print_section('Summary')
    if failures:
        print('[FAIL] hard failures: ' + ', '.join(failures))
        return 1
    print('[OK] doctor completed; review WARN lines for optional improvements')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
