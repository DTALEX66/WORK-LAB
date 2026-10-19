"""The 2026-10-19 archive normalization must not be re-indexable.

`scripts/ci/verify_stale_surface_paths.py` is the only guard that looks at the WHOLE active
surface -- the authority-index gate sees `docs/current/` plus three named files, so a stale
pointer in `.project/governance/`, `scripts/`, `tests/` or `apps/` would pass every other gate.
These tests keep that guard from becoming decoration: a planted old path must convict, the frozen
`original-tree/` spelling must NOT convict, and an allowance that stops being used must convict.

This module lives in `tests/ci/` on purpose: `scripts/ci/run_root_governance_suite.py` globs that
directory, so the gate is measured by CI the moment it lands instead of waiting to be registered.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "scripts" / "ci" / "verify_stale_surface_paths.py"
MANIFEST = ROOT / "docs/history/archive/MOVED-PATHS-20261019.json"


def _load():
    spec = importlib.util.spec_from_file_location("verify_stale_surface_paths", VERIFIER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = _load()


def _runtime_root() -> Path:
    """Scratch stays inside the declared project boundary (ERR-140 convention)."""
    path = ROOT / ".project-local/runs"
    path.mkdir(parents=True, exist_ok=True)
    return path


class LiveTree(unittest.TestCase):
    def test_the_live_tree_is_clean_and_the_verdict_is_named(self) -> None:
        self.assertEqual(0, MODULE.main([]))

    def test_the_population_is_measured_not_assumed(self) -> None:
        manifest = MODULE.load_manifest(MANIFEST)
        result = MODULE.scan(ROOT, manifest)
        self.assertGreaterEqual(result["scanned"], MODULE.SCAN_FLOOR,
                                "a scan below the floor is a blind instrument, not a clean tree")
        self.assertEqual(54, manifest["counts"]["moves"])
        self.assertEqual(48, len(MODULE.old_patterns(manifest)),
                         "47 moved paths + 1 forbidden prefix; a missing pattern means the gate "
                         "stopped seeing a move")

    def test_every_moved_file_lives_at_its_new_path_with_the_recorded_bytes(self) -> None:
        """The hash chain runs root -> archive path -> ZIP member, and every link is checked."""
        manifest = MODULE.load_manifest(MANIFEST)
        archive = ROOT / manifest["consolidation"]["archive"]
        with zipfile.ZipFile(archive) as bundle:
            for move in manifest["moves"]:
                if "removedInto" in move:
                    with bundle.open(move["to"]) as handle:
                        raw = handle.read()
                    self.assertEqual(move["sha256"], hashlib.sha256(raw).hexdigest(),
                                     f"archive member differs from the move record: {move['to']}")
                    self.assertFalse((ROOT / move["to"]).exists(),
                                     f"consolidated file is still loose: {move['to']}")
                    continue
                target = ROOT / move["to"]
                self.assertTrue(target.is_file(), f"moved file missing: {move['to']}")
                raw = target.read_bytes()
                self.assertEqual(move["sha256"], hashlib.sha256(raw).hexdigest(),
                                 f"bytes differ from the move record: {move['to']}")
                self.assertEqual(move["bytes"], len(raw), f"size differs: {move['to']}")

    def test_the_consolidated_archive_is_whole_and_its_members_are_all_gone_from_the_tree(self) -> None:
        """Deletion is only defensible because one artifact holds every byte, provably."""
        manifest = MODULE.load_manifest(MANIFEST)
        block = manifest["consolidation"]
        archive = ROOT / block["archive"]
        record = json.loads((ROOT / block["manifest"]).read_text(encoding="utf-8"))
        self.assertEqual(block["archiveSha256"], hashlib.sha256(archive.read_bytes()).hexdigest())
        self.assertEqual(block["members"], len(record["members"]))
        tracked = set(MODULE.tracked_files(ROOT))
        with zipfile.ZipFile(archive) as bundle:
            self.assertEqual(sorted(bundle.namelist()),
                             sorted(entry["path"] for entry in record["members"]))
            for entry in record["members"]:
                with bundle.open(entry["path"]) as handle:
                    raw = handle.read()
                self.assertEqual(entry["sha256"], hashlib.sha256(raw).hexdigest(), entry["path"])
                self.assertEqual(entry["bytes"], len(raw), entry["path"])
                self.assertEqual(zipfile.crc32(raw) & 0xFFFFFFFF, entry["crc32"], entry["path"])
                self.assertNotIn(entry["path"], tracked,
                                 f"consolidated file is still tracked: {entry['path']}")
                self.assertFalse((ROOT / entry["path"]).exists(), entry["path"])

    def test_a_pointer_kept_because_governance_reads_it_is_still_on_disk(self) -> None:
        """Four handoffs matched the pattern but were kept: a machine pointer names each one."""
        block = MODULE.load_manifest(MANIFEST)["consolidation"]
        self.assertGreaterEqual(len(block["keptInPlace"]), 4)
        for path, reason in block["keptInPlace"].items():
            self.assertTrue((ROOT / path).is_file(), f"{path} is gone but is still governed")
            self.assertGreater(len(reason), 40, path)

    def test_no_enforced_old_path_still_exists_on_disk(self) -> None:
        manifest = MODULE.load_manifest(MANIFEST)
        for move in manifest["moves"]:
            if "/" not in move["from"]:
                continue
            self.assertFalse((ROOT / move["from"]).exists(),
                             f"old path is back on disk: {move['from']}")
        for entry in manifest["forbiddenPrefixes"]:
            self.assertFalse((ROOT / entry["prefix"]).exists(),
                             f"old directory is back on disk: {entry['prefix']}")

    def test_the_recorded_basename_moves_are_not_present_at_the_root(self) -> None:
        """The seven basename moves cannot be path-matched, so the root itself is checked."""
        manifest = MODULE.load_manifest(MANIFEST)
        names = manifest["notEnforced"]["paths"]
        self.assertEqual(7, len(names), names)
        for name in names:
            self.assertFalse((ROOT / name).exists(), f"{name} reappeared at the repository root")


class SyntheticTree(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = Path(tempfile.mkdtemp(prefix="stale-paths-", dir=_runtime_root()))
        self.manifest = MODULE.load_manifest(MANIFEST)
        # The live allowances name live files; a scratch tree without them would report
        # ALLOWANCE_UNMET for every case and blur which finding is under test.
        self.manifest["allowances"] = []
        self._files = []
        self._tracked = MODULE.tracked_files
        MODULE.tracked_files = lambda root: list(self._files)

    def tearDown(self) -> None:
        MODULE.tracked_files = self._tracked
        shutil.rmtree(self.scratch, ignore_errors=True)

    def _write(self, rel: str, text: str) -> None:
        path = self.scratch / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        self._files.append(rel)

    def test_a_planted_old_path_on_an_active_surface_is_convicted(self) -> None:
        self._write("docs/current/POINTER.md",
                    "接手指令见 taskpacks/current/ORCA-PILOT-TASK-CARD-20260925.md\n")
        result = MODULE.scan(self.scratch, self.manifest)
        self.assertEqual([], result["allowanceFailures"])
        self.assertTrue(any(f.startswith("STALE docs/current/POINTER.md:1")
                            and "ORCA-PILOT-TASK-CARD-20260925.md" in f
                            for f in result["findings"]), result["findings"])

    def test_a_planted_old_directory_prefix_is_convicted(self) -> None:
        self._write(".project/governance/pointer.json",
                    '{"x": "docs/current/ui-priority-20261009/anything.md"}\n')
        result = MODULE.scan(self.scratch, self.manifest)
        self.assertTrue(any("STALE .project/governance/pointer.json:1" in f
                            for f in result["findings"]), result["findings"])

    def test_a_frozen_original_tree_spelling_is_not_convicted(self) -> None:
        """The guard that makes the whole scope survivable: history keeps its own operands.

        This is the regression test for the alternation bug. `(?<!x)a|b|c` parses as
        `((?<!x)a)|b|c`, so one lookbehind guarded only the first of 48 alternatives and every
        `original-tree` archivePath in the taskpack index read as stale.
        """
        frozen = ("taskpacks/history/UI-PRIORITY-CUTOVER-20261009/original-tree/"
                  "taskpacks/current/ORCA-PILOT-TASK-CARD-20260925.md")
        self._write("docs/audits/RECORD.md", f"引用 {frozen}\n")
        result = MODULE.scan(self.scratch, self.manifest)
        self.assertEqual([], result["findings"],
                         "a frozen original-tree path must never be called stale")

    def test_history_and_evidence_roots_are_out_of_scope(self) -> None:
        for rel in ("docs/history/archive/RECORD.md", "taskpacks/history/OLD.md",
                    "reports/audit-evidence/R.md", "knowledge-staging/x/SKILL.md",
                    ".workbuddy/note.md"):
            self._write(rel, "taskpacks/current/ORCA-PILOT-TASK-CARD-20260925.md\n")
        self._write("docs/current/LIVE.md", "taskpacks/current/ORCA-PILOT-TASK-CARD-20260925.md\n")
        result = MODULE.scan(self.scratch, self.manifest)
        self.assertEqual(1, len(result["findings"]), result["findings"])
        self.assertTrue(result["findings"][0].startswith("STALE docs/current/LIVE.md"), result["findings"])

    def test_an_allowance_that_stops_being_used_fails(self) -> None:
        """Renaming the last stale pointer away must reopen the licence, not pass silently."""
        self.manifest["allowances"] = [{"path": "README.md", "reason": "declared but nothing to allow",
                                        "minOccurrences": 1}]
        self._write("README.md", "clean text\n")
        result = MODULE.scan(self.scratch, self.manifest)
        self.assertEqual([], result["findings"])
        self.assertTrue(any(f.startswith("ALLOWANCE_UNMET README.md") for f in
                            result["allowanceFailures"]), result["allowanceFailures"])

    def test_the_manifest_itself_is_not_scanned(self) -> None:
        """The move record names every old path; convicting its own file would be nonsense."""
        self._write("docs/history/archive/MOVED-PATHS-20261019.json",
                    json.dumps({"moves": []}))
        self.assertIn("docs/history/archive/MOVED-PATHS-20261019.json",
                      [x for x in self._files])
        self.assertFalse(MODULE.in_scope("docs/history/archive/MOVED-PATHS-20261019.json",
                                         self.manifest))

    def test_a_binary_file_cannot_hide_a_stale_pointer_or_crash_the_scan(self) -> None:
        self._write("apps/observer/blob.dat", "taskpacks/current/ORCA-PILOT-TASK-CARD-20260925.md\n")
        (self.scratch / "apps/observer/blob.dat").write_bytes(b"\xff\xfe\x00 binary\n")
        result = MODULE.scan(self.scratch, self.manifest)
        self.assertEqual([], result["findings"],
                         "undecodable bytes are skipped, they are not a failure of the instrument")


class ManifestShape(unittest.TestCase):
    def test_every_allowance_carries_a_reason_and_a_minimum(self) -> None:
        manifest = MODULE.load_manifest(MANIFEST)
        self.assertGreaterEqual(len(manifest["allowances"]), 4)
        for entry in manifest["allowances"]:
            self.assertTrue(len(entry.get("reason", "")) > 40, entry)
            self.assertGreaterEqual(entry.get("minOccurrences", 0), 1, entry)
            self.assertTrue((ROOT / entry["path"]).is_file(), f"allowance names a missing file: {entry}")

    def test_the_directive_is_recorded_verbatim(self) -> None:
        """The move is justified by an owner decision, so the decision itself is the evidence."""
        manifest = MODULE.load_manifest(MANIFEST)
        for fragment in ("旧的过时的冗余的陈旧的", "全部归档到该去汇总的地方", "防止再次索引路径到旧资料上"):
            self.assertIn(fragment, manifest["directive"], fragment)


if __name__ == "__main__":
    unittest.main()
