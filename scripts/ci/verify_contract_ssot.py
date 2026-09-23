#!/usr/bin/env python3
"""U16: Cross-language contract SSOT conformance (catalog-driven, no hardcoded counts).

Single source of truth for cross-language contracts = the JSON Schema set,
referenced by .project/governance/contracts/contract-catalog.json.

This verifier is CATALOG-DRIVEN (P0-4.1: it never hardcodes a contract count,
so adding a contract cannot break the gate just because a number was frozen).

Hard-fail (exit 1) on real SSOT drift:
  1. catalog malformed (missing id/owner/schemaPath, duplicate ids)
  2. a catalog entry points to a schema that does NOT exist on disk
  3. the generated TS projection (packages/client-neutral-core/generated/contracts.ts)
     is missing, or its contract id set != the catalog id set (type drift)

ADVISORY (printed, does NOT fail the gate):
  A. on-disk .schema.json files under the canonical roots that are not in the
     catalog. These are surfaced so a reviewer can decide whether each is a
     cross-language authority (should be cataloged) or a helper schema (fine).
     Not every schema on disk is a cross-language contract authority, so this
     is a report, not a hard gate.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CANONICAL_SCHEMA_ROOTS = (
    "packages/contracts/schemas",
    ".project/governance/contracts",
    "apps/observer/schemas",
)
GENERATED_TS = "packages/client-neutral-core/generated/contracts.ts"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_catalog(root: Path) -> list[dict]:
    p = root / ".project" / "governance" / "contracts" / "contract-catalog.json"
    if not p.is_file():
        print(f"CONTRACT_SSOT_FAIL catalog missing: {p}")
        sys.exit(1)
    data = json.loads(p.read_text(encoding="utf-8"))
    entries = data.get("contracts")
    if not isinstance(entries, list):
        print("CONTRACT_SSOT_FAIL catalog 'contracts' must be an array")
        sys.exit(1)
    return entries


def _disk_schemas(root: Path) -> set[str]:
    found: set[str] = set()
    for rel_root in CANONICAL_SCHEMA_ROOTS:
        base = root / rel_root
        if not base.is_dir():
            continue
        for p in base.rglob("*.schema.json"):
            if "src-tauri" in p.parts or "target" in p.parts:
                continue
            found.add(p.relative_to(root).as_posix())
    return found


def _ts_contract_ids(root: Path) -> set[str] | None:
    p = root / GENERATED_TS
    if not p.is_file():
        return None
    text = p.read_text(encoding="utf-8")
    return set(re.findall(r"// @contract ([A-Za-z0-9_\-]+)", text))


def main() -> int:
    root = _repo_root()
    errors: list[str] = []

    entries = _load_catalog(root)
    ids = [e.get("id") for e in entries]
    cat_ids = set(ids)

    # 1. catalog well-formed
    if len(ids) != len(cat_ids):
        dup = sorted({i for i in ids if i and ids.count(i) > 1})
        errors.append(f"duplicate contract ids: {dup}")
    for e in entries:
        for field in ("id", "owner", "schemaPath"):
            if not e.get(field):
                errors.append(f"catalog entry missing '{field}': {e}")

    # 2. every catalog schemaPath exists on disk
    seen: set[str] = set()
    for e in entries:
        sp = e.get("schemaPath", "").replace("\\", "/")
        if not sp:
            continue
        if sp in seen:
            errors.append(f"duplicate schemaPath: {sp}")
        seen.add(sp)
        if not (root / sp).is_file():
            errors.append(f"catalog '{e.get('id')}' -> missing schema {sp}")

    # 3. generated TS projection present + id set == catalog id set
    ts_ids = _ts_contract_ids(root)
    if ts_ids is None:
        errors.append(f"generated TS projection missing: {GENERATED_TS} "
                      f"(run scripts/ci/generate_contract_types.py)")
    else:
        missing = sorted(cat_ids - ts_ids)
        extra = sorted(ts_ids - cat_ids)
        if missing:
            errors.append("generated TS missing contracts: " + ", ".join(missing))
        if extra:
            errors.append("generated TS has unknown contracts: " + ", ".join(extra))

    # ADVISORY: unlisted on-disk schemas
    disk = _disk_schemas(root)
    unlisted = sorted(d for d in disk if d not in seen)

    if errors:
        for u in unlisted:
            print(f"CONTRACT_SSOT_ADVISORY unlisted-on-disk-schema {u}")
        for err in errors:
            print(f"CONTRACT_SSOT_FAIL {err}")
        return 1

    print(f"CONTRACT_SSOT_PASS contracts={len(cat_ids)} "
          f"disk_schemas={len(disk)} unlisted_advisory={len(unlisted)}")
    for u in unlisted:
        print(f"  [advisory] unlisted-on-disk-schema {u}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
