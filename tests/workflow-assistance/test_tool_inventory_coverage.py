"""Gate: the tracked-instrument inventory must describe the tree exactly.

`docs/audits/PROBE_TOOL_PROMOTION_2026-10-07.json` recorded a promotion event (22 scratch originals
became tracked tools) and then quietly stopped being true as more tools shipped. This gate replaces
"an inventory somebody remembers to update" with a checked property: every tracked file under
`scripts/audit/` and `scripts/maintenance/` appears once in
`docs/audits/TOOL_INVENTORY_2026-10-07.json`, its digest is the digest of the committed blob, and its
byte and line counts are the current ones.

Digests are blob-based on purpose — `.gitattributes` sets `* text=auto`, so the same source has
different working bytes per platform, and recording working-tree bytes is precisely what turned CI red
at three heads (ERR-125).
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "docs" / "audits" / "TOOL_INVENTORY_2026-10-07.json"
DIRS = ("scripts/audit/", "scripts/maintenance/")


def tracked_tools() -> list[str]:
    raw = subprocess.run(["git", "-c", "core.quotePath=false", "ls-files", "-z"],
                         cwd=ROOT, capture_output=True).stdout.split(b"\0")
    return sorted(p.decode("utf-8", "replace") for p in raw
                  if p and p.decode("utf-8", "replace").startswith(DIRS))


def blob(rel: str) -> bytes | None:
    r = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True)
    return r.stdout if r.returncode == 0 else None


def describe(rel: str) -> tuple[str, int, int, str]:
    data = blob(rel)
    basis = "git-blob-at-HEAD"
    if data is None:
        data = (ROOT / rel).read_bytes()
        basis = "working-tree-uncommitted"
    lines = data.count(b"\n") + (0 if data.endswith(b"\n") or not data else 1)
    return hashlib.sha256(data).hexdigest(), len(data), lines, basis


def violations(entries: list[dict], tools: list[str]) -> list[str]:
    out = []
    listed = [e["path"] for e in entries]
    seen = set()
    dupes = sorted({p for p in listed if p in seen or seen.add(p)})
    if dupes:
        out.append(f"duplicate inventory entries: {dupes}")
    missing = sorted(set(tools) - set(listed))
    extra = sorted(set(listed) - set(tools))
    if missing:
        out.append(f"tracked instruments absent from the inventory: {missing}")
    if extra:
        out.append(f"inventory names files that are not tracked: {extra}")
    for e in entries:
        path = e["path"]
        if path not in set(tools):
            continue                      # already reported as phantom; can't be digested
        sha, size, lines, basis = describe(path)
        if e.get("sha256") != sha:
            out.append(f"{path}: inventory sha256 {e.get('sha256')!r} != current {basis} {sha!r}")
        if e.get("bytes") != size:
            out.append(f"{path}: inventory bytes {e.get('bytes')} != {size}")
        if e.get("lines") != lines:
            out.append(f"{path}: inventory lines {e.get('lines')} != {lines}")
        if e.get("digestBasis") not in {"git-blob-at-HEAD", "working-tree-uncommitted"}:
            out.append(f"{path}: digestBasis {e.get('digestBasis')!r} is not a named basis")
        if not re.fullmatch(r"[0-9a-f]{64}", str(e.get("sha256") or "")):
            out.append(f"{path}: sha256 is not 64 lowercase hex")
    return out


class ToolInventoryCoverageGate(unittest.TestCase):
    def setUp(self) -> None:
        self.doc = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.tools = tracked_tools()
        self.entries = self.doc["tools"]

    def test_the_inventory_is_not_vacuous(self) -> None:
        self.assertGreaterEqual(len(self.tools), 25,
                                "so few tracked tools that coverage proves nothing")
        self.assertGreaterEqual(len(self.entries), 25)

    def test_the_shipped_inventory_describes_the_tree(self) -> None:
        self.assertEqual(violations(self.entries, self.tools), [])

    def test_counts_agree_with_the_entries(self) -> None:
        counts = self.doc["counts"]
        self.assertEqual(counts["trackedTools"], len(self.entries))
        self.assertEqual(counts["withLedgerPromise"],
                         sum(1 for e in self.entries if e["citedByLedgerPromises"]))
        self.assertEqual(counts["referencedSomewhere"],
                         sum(1 for e in self.entries if e["citedByRecords"]))
        self.assertEqual(counts["unclaimed"], len(self.doc["unclaimed"]))

    def test_every_tool_is_reachable_from_a_record(self) -> None:
        # an instrument nothing cites is either a duplicate of another or an unwritten promise
        self.assertEqual(self.doc["unclaimed"], [],
                         "tracked tools that no record or ledger promise names")

    def test_every_ledger_promise_target_is_in_the_inventory(self) -> None:
        ledger = json.loads((ROOT / "taskpacks/current/error-ledger.json").read_text(encoding="utf-8"))
        named = set()
        for err in ledger["errors"]:
            cmd = (err.get("lifecycle") or {}).get("regressionCommand") or ""
            for tool in self.tools:
                if PurePosixPath(tool).name in cmd:
                    named.add(tool)
        listed = {e["path"] for e in self.entries}
        self.assertEqual(sorted(named - listed), [],
                         "a ledger promise names a tool the inventory does not carry")

    # ---------------- negative controls
    def test_a_tool_missing_from_the_inventory_is_refused(self) -> None:
        entries = [e for e in self.entries if e["path"] != self.tools[0]]
        self.assertTrue(any("absent from the inventory" in v
                            for v in violations(entries, self.tools)))

    def test_a_phantom_entry_is_refused(self) -> None:
        entries = self.entries + [{"path": "scripts/audit/never_existed.py",
                                   "sha256": "0" * 64, "bytes": 1, "lines": 1,
                                   "digestBasis": "git-blob-at-HEAD"}]
        self.assertTrue(any("not tracked" in v for v in violations(entries, self.tools)))

    def test_a_stale_digest_is_refused(self) -> None:
        entries = [dict(e, sha256="f" * 64) if e["path"] == self.tools[1] else e
                   for e in self.entries]
        self.assertTrue(any("!= current" in v for v in violations(entries, self.tools)))

    def test_a_wrong_line_count_is_refused(self) -> None:
        entries = [dict(e, lines=e["lines"] + 3) if e["path"] == self.tools[2] else e
                   for e in self.entries]
        self.assertTrue(any("inventory lines" in v for v in violations(entries, self.tools)))

    def test_an_unnamed_digest_basis_is_refused(self) -> None:
        entries = [dict(e, digestBasis="checked-out-windows-bytes") if e["path"] == self.tools[3]
                   else e for e in self.entries]
        self.assertTrue(any("digestBasis" in v for v in violations(entries, self.tools)))

    def test_a_duplicate_entry_is_refused(self) -> None:
        entries = self.entries + [dict(self.entries[0])]
        self.assertTrue(any("duplicate inventory entries" in v
                            for v in violations(entries, self.tools)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
