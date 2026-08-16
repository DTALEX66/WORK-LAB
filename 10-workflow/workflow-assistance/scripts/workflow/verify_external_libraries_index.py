# -*- coding: utf-8 -*-
"""Verify external-libraries-index.json: JSON valid, sharedRoots resolve, assets present."""
import json, sys, pathlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

INDEX = pathlib.Path(r"D:\All projects\WORK-LAB\00-governance\external-libraries-index.json")
errors = []

if not INDEX.exists():
    print("FAIL missing index")
    sys.exit(1)

d = json.loads(INDEX.read_text(encoding="utf-8"))

# schema + policy
if d.get("schemaVersion") != "work-lab/external-libraries-index/v1":
    errors.append("schemaVersion mismatch")
if "policy" not in d or "内容" not in d["policy"]:
    errors.append("policy missing content-exclusion clause")

# sharedRoots resolve
for name, root in d.get("sharedRoots", {}).items():
    if not pathlib.Path(root).is_dir():
        errors.append(f"sharedRoot {name} not resolvable: {root}")

# libraries: id/kind/ownedBy/assets
libs = d.get("libraries", [])
if not libs:
    errors.append("no libraries")
for lib in libs:
    for field in ("id", "sharedRoot", "relativePath", "kind", "ownedBy"):
        if not lib.get(field):
            errors.append(f"library {lib.get('id','?')} missing {field}")
    root = d.get("sharedRoots", {}).get(lib.get("sharedRoot", ""))
    if root and not pathlib.Path(root).joinpath(lib["relativePath"]).exists():
        errors.append(f"library path not resolvable: {lib['id']} -> {root}\\{lib['relativePath']}")

# asset lists present for model libs
for lib in libs:
    if lib.get("kind") == "model-weights" and not lib.get("assets"):
        errors.append(f"model library {lib['id']} has empty assets (must list, not upload)")

if errors:
    print("FAIL:")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print(f"PASS external-libraries-index: {len(libs)} libraries, {len(d.get('sharedRoots', {}))} roots, JSON valid, paths resolve")
