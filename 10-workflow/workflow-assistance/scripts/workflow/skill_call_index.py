"""Skill-call index — per-project cache mapping task keywords -> skills.

First run scans SKILL.md descriptions and builds an index; later runs look up
the index directly instead of re-scanning every time. Optimization layer on top
of the "scan skills before executing" rule.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

INDEX_FILE = ".hermes/skill-call-index.json"
WORD_RE = re.compile(r"[a-zA-Z0-9_\u4e00-\u9fff-]{3,}")


def _load(root):
    f = Path(root) / INDEX_FILE
    if not f.exists():
        return {"version": 1, "keywords": {}, "lastBuilt": None}
    return json.loads(f.read_text(encoding="utf-8"))


def _save(root, data):
    f = Path(root) / INDEX_FILE
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def build(root, skills_dir):
    idx = {"version": 1, "keywords": {}, "lastBuilt": time.time()}
    sp = Path(skills_dir)
    if not sp.exists():
        _save(root, idx)
        return idx
    for skill in sp.rglob("SKILL.md"):
        text = skill.read_text(encoding="utf-8", errors="ignore")
        # description: ... (frontmatter line)
        m = re.search(r"description:\s*(.+)", text)
        desc = (m.group(1) if m else "") + " " + skill.parent.name
        name = skill.parent.name
        for w in WORD_RE.findall(desc.lower()):
            idx["keywords"].setdefault(w, [])
            if name not in idx["keywords"][w]:
                idx["keywords"][w].append(name)
    _save(root, idx)
    return idx


def lookup(root, task):
    idx = _load(root)
    if not idx.get("keywords"):
        return []
    hits = {}
    for w in WORD_RE.findall(task.lower()):
        for skill in idx["keywords"].get(w, []):
            hits[skill] = hits.get(skill, 0) + 1
    return [s for s, _ in sorted(hits.items(), key=lambda kv: -kv[1])]


def record(root, task, skill):
    idx = _load(root)
    for w in WORD_RE.findall(task.lower()):
        idx["keywords"].setdefault(w, [])
        if skill not in idx["keywords"][w]:
            idx["keywords"][w].append(skill)
    _save(root, idx)
    return {"recorded": True, "skill": skill}
