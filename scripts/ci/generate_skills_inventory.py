"""Generate dynamic skills inventory (R4/T40) - no fixed counts.

Scans every executor skills tree under integrations/executors/*/skills and the
managed root if present, emits an inventory with per-skill sha256 and a source
digest. Downstream verify uses this to detect drift and never assumes a fixed
skill count.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scan_skills(root: Path) -> list[dict]:
    out = []
    if not root.exists():
        return out
    for sk in sorted(root.rglob("SKILL.md")):
        name = sk.parent.name
        out.append({"name": name, "path": str(sk.relative_to(REPO)), "sha256": _hash_file(sk)})
    return out


def main() -> int:
    skills: list[dict] = []
    sources = []
    for root in (REPO / "integrations").glob("executors/*/skills"):
        found = scan_skills(root)
        skills.extend(found)
        sources.append(str(root.relative_to(REPO)))
    managed = REPO / "skills"
    if managed.exists():
        skills.extend(scan_skills(managed))
        sources.append("skills")
    skills.sort(key=lambda s: s["name"])
    digest = hashlib.sha256(json.dumps(skills, sort_keys=True).encode()).hexdigest()
    inventory = {
        "schema_version": "workflow/skills-inventory/v1",
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "count": len(skills),
        "sourceDigest": digest,
        "sources": sources,
        "skills": skills,
    }
    out = REPO / "config" / "skills-inventory.json"
    out.write_text(json.dumps(inventory, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"SKILLS_INVENTORY count={len(skills)} digest={digest[:16]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
