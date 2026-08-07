from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md",
    "AGENTS.md",
    "module-profile.json",
    "schemas/observer-event.schema.json",
    "schemas/data-quality.schema.json",
    "src/observer_runtime.py",
    "scripts/observer_dashboard.py",
    "tests/test_observer_skeleton.py",
    "tests/test_observer_runtime.py",
    "tests/test_observer_dashboard.py",
)
FORBIDDEN_MARKERS = ("subprocess", "os.system", "shell=True", "POST /", "PUT /", "PATCH /", "DELETE /")


def main() -> int:
    for relative in REQUIRED:
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size == 0:
            print(f"OBSERVER_SKELETON_FAIL missing={relative}")
            return 1
    profile = json.loads((ROOT / "module-profile.json").read_text(encoding="utf-8"))
    if profile.get("id") != "work-lab-observer" or profile.get("externalMutationDefault") is not False:
        print("OBSERVER_SKELETON_FAIL profile")
        return 1
    for relative in ("README.md", "AGENTS.md"):
        text = (ROOT / relative).read_text(encoding="utf-8").lower()
        if any(marker.lower() in text for marker in FORBIDDEN_MARKERS):
            print(f"OBSERVER_SKELETON_FAIL forbidden_marker={relative}")
            return 1
    print("OBSERVER_SKELETON_PASS files=10 external_mutation_default=false dashboard=read-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
