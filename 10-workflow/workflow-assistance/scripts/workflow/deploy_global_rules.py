"""Deploy global rules — sync the single source of truth to every software.

Single source: 00-governance/global-execution-standard.md (global boundaries).
This tool syncs those boundaries into each software's rule file via a managed
block (marker-delimited), so a change to the source propagates to all software
and never drifts. Idempotent.
"""
from __future__ import annotations

import re
from pathlib import Path

# Single source of truth (key -> zh/en text)
GLOBAL_BOUNDARIES = [
    ("safety-e", "E盘禁访", "Never access E:\\ without explicit per-path, per-operation authorization in the current request."),
    ("data-boundary", "数据边界", "All task data (temp, cache, logs, artifacts) stays inside the project .hermes/; no spill to user home, other projects, or shared libraries."),
    ("official-first", "官方优先", "Software updates follow official releases only; never privately build/package versions."),
    ("skill-discipline", "技能调用纪律", "Before executing a task, check the skill-call index / scan SKILL.md, load the matching skill, and record the mapping; never just start."),
]

MARKER_BEGIN = "<!-- GLOBAL-RULES-MANAGED-BLOCK BEGIN -->"
MARKER_END = "<!-- GLOBAL-RULES-MANAGED-BLOCK END -->"


def _block(zh: bool) -> str:
    lines = [MARKER_BEGIN]
    for key, zh_name, en_text in GLOBAL_BOUNDARIES:
        if zh:
            # zh rendering: use zh name as heading + en text
            lines.append(f"- [{zh_name}] {en_text}")
        else:
            lines.append(f"- {en_text}")
    lines.append(MARKER_END)
    return "\n".join(lines)


def sync_file(path: Path, zh: bool) -> bool:
    """Insert/update the managed block in a target rule file."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    block = _block(zh)
    pattern = re.compile(rf"{re.escape(MARKER_BEGIN)}.*?{re.escape(MARKER_END)}", re.DOTALL)
    if pattern.search(text):
        new_text = pattern.sub(block.replace("\\", "\\\\"), text)
    else:
        new_text = text.rstrip() + "\n\n" + block + "\n"
    path.write_text(new_text, encoding="utf-8")
    return True


TARGETS = [
    (Path(r"C:\Users\ALEX\AppData\Local\hermes\SOUL.md"), True),   # Hermes (zh)
    (Path(r"C:\Users\ALEX\.codex\AGENTS.md"), False),               # Codex (en)
]


def deploy() -> dict:
    results = {}
    for path, zh in TARGETS:
        ok = sync_file(path, zh)
        results[str(path)] = "synced" if ok else "missing"
    return results


if __name__ == "__main__":
    import json
    print(json.dumps(deploy(), indent=1))
