from __future__ import annotations
import json
import sys

REQUIRED = {"workflow", "open-design", "minigame", "integration"}

def main(payload: str) -> int:
    data = json.loads(payload)
    jobs = data.get("jobs", {})
    bad = [name for name in REQUIRED if jobs.get(name) not in {"success", "passed"}]
    if bad:
        print(json.dumps({"status": "FAIL", "missing_or_failed": sorted(bad)}))
        return 1
    print(json.dumps({"status": "PASS", "required": sorted(REQUIRED)}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.stdin.read()))
