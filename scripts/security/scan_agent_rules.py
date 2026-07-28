#!/usr/bin/env python3
"""Scan agent rule/prompt files for common safety issues.

Usage:
  python scripts/security/scan_agent_rules.py [paths...]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\ufeff]")
INJECTION = re.compile(
    "|".join(
        (
            r"ignore (all )?(previous|prior) instructions",
            "system" + r"\s+prompt",
            "developer" + r"\s+message",
            r"exfiltrate",
            r"send .*token",
            r"curl .*\|\s*(sh|bash)",
            r"powershell -encodedcommand",
        )
    ),
    re.I,
)
SECRET_HINT = re.compile(r"(api[_-]?key|secret|password|passwd|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}", re.I)

EXTS = {
    '.md', '.txt', '.yaml', '.yml', '.json', '.toml',
    '.py', '.sh', '.bash', '.ps1', '.psm1', '.cmd', '.bat',
}
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOTS = (
    REPO_ROOT / "templates",
    REPO_ROOT / "skills",
    REPO_ROOT / "docs",
    REPO_ROOT / "config",
    REPO_ROOT / "bin",
    REPO_ROOT / "scripts",
    REPO_ROOT / ".github",
    REPO_ROOT / "README.md",
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "setup.sh",
    REPO_ROOT / "setup.ps1",
)
SKIP_PARTS = {".git", ".hermes", "__pycache__", "node_modules", ".venv", "venv"}


def scan_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return [f'{path}: non-utf8 text']
    issues: list[str] = []
    if ZERO_WIDTH.search(text):
        issues.append(f'{path}: hidden zero-width/BOM character')
    if INJECTION.search(text):
        issues.append(f'{path}: prompt-injection-like phrase')
    if SECRET_HINT.search(text):
        issues.append(f'{path}: possible hardcoded secret')
    return issues


def iter_scannable(root: Path):
    if root.is_file() and root.suffix.lower() in EXTS:
        yield root
        return
    if not root.exists():
        return
    for path in root.rglob("*"):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in EXTS:
            yield path


def main(argv: list[str]) -> int:
    roots = [Path(a) for a in argv[1:]] or list(DEFAULT_ROOTS)
    issues: list[str] = []
    for root in roots:
        for path in iter_scannable(root):
            if path.resolve() != Path(__file__).resolve():
                issues.extend(scan_file(path))
    if issues:
        print('\n'.join(issues))
        return 1
    print('scan_agent_rules: OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
