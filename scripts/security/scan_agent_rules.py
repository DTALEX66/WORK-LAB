#!/usr/bin/env python3
"""Scan agent rule/prompt files for common safety issues.

Usage:
  python scripts/security/scan_agent_rules.py templates skills docs
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\ufeff]")
INJECTION = re.compile(
    r"ignore (all )?(previous|prior) instructions|system prompt|developer message|exfiltrate|send .*token|curl .*\|\s*(sh|bash)|powershell -encodedcommand",
    re.I,
)
SECRET_HINT = re.compile(r"(api[_-]?key|secret|password|passwd|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}", re.I)

EXTS = {'.md', '.txt', '.yaml', '.yml', '.json', '.toml'}


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


def main(argv: list[str]) -> int:
    roots = [Path(a) for a in argv[1:]] or [Path('templates'), Path('skills'), Path('docs')]
    issues: list[str] = []
    for root in roots:
        if root.is_file() and root.suffix.lower() in EXTS:
            issues.extend(scan_file(root))
        elif root.exists():
            for path in root.rglob('*'):
                if path.is_file() and path.suffix.lower() in EXTS:
                    issues.extend(scan_file(path))
    if issues:
        print('\n'.join(issues))
        return 1
    print('scan_agent_rules: OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
