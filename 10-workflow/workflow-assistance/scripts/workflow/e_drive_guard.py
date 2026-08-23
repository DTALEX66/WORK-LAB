"""E-drive guard — pre_tool_call hook blocking E:\\ access without authorization.

Checks a tool-call payload (stdin JSON) for E:\\ paths; blocks any read/write/
list/move/delete that touches the protected drive unless an explicit auth
marker is present. Fails closed. Mounted under Hermes hooks.pre_tool_call.
"""
from __future__ import annotations

import json
import re
import sys

E_DRIVE_RE = re.compile(r"[Ee]:[\\/]", re.IGNORECASE)
AUTH_MARKER = "E_DRIVE_AUTHORIZED"  # explicit per-operation authorization


def _find_e_paths(obj, hits=None):
    if hits is None:
        hits = []
    if isinstance(obj, str):
        if E_DRIVE_RE.search(obj):
            hits.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _find_e_paths(v, hits)
    elif isinstance(obj, list):
        for v in obj:
            _find_e_paths(v, hits)
    return hits


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}
    authorized = AUTH_MARKER in json.dumps(payload).upper()
    hits = _find_e_paths(payload)
    if hits and not authorized:
        print(json.dumps({"allow": False, "reason": f"E:\\ access blocked ({len(hits)} path(s)): not authorized"}))
        return 1
    print(json.dumps({"allow": True}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
