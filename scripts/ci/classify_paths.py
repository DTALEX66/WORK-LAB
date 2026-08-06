from __future__ import annotations
import sys
from pathlib import Path

ROOTS = {
    "workflow": Path("10-workflow/workflow-assistance"),
    "open-design": Path("20-design/open-design"),
    "observer": Path("30-observer/work-lab-observer"),
}

def classify(paths: list[str]) -> dict[str, list[str]]:
    result = {name: [] for name in ROOTS}
    result["root"] = []
    for raw in paths:
        p = Path(raw.replace('\\', '/'))
        owner = next((name for name, root in ROOTS.items() if p == root or root in p.parents), "root")
        result[owner].append(raw)
    return result

if __name__ == "__main__":
    print(classify(sys.argv[1:]))
