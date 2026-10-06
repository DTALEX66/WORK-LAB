"""AG-20 gate: the tracked mirror of the recovered-source registry must stay true.

The atlas Source Registry itself lives under the git-ignored `.project-local`
runtime root, so it is machine-local and nothing enforces it (ERR-114 says so in
its own remaining_boundary). This tracked mirror is the part a gate can check:
every `tracked` entry is re-hashed here, and every `machine-local` entry is
checked for honest labelling rather than being silently trusted.

Discovered dynamically by `run_quality_gate.py governance`, so no manifest edit
is needed to put it in CI.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / ".project" / "governance" / "recovered-source-registry.json"
STATUSES = {"tracked", "machine-local", "absent", "unpinned"}
REQUIRED_FIELDS = ("id", "kind", "status", "path", "observedAt", "originalLocation",
                   "coverageRelation", "verificationCommand", "notes")
# The five originals AG-19 pins. Dropping one of these rows must fail the gate:
# the absent timeline is the most important entry in the file, not the least.
PINNED_ORIGINALS = {
    "src-worklab-summary-2026-09",
    "src-conversation-timeline-2026-09",
    "src-startup-prompt-2026-09-28",
    "src-final-execution-doc-2026-09-28",
}


def git_tracked(rel: str) -> bool:
    return subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=ROOT,
                          capture_output=True).returncode == 0


def digest(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


class RecoveredSourceRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        assert REGISTRY.exists(), f"missing {REGISTRY}"
        cls.data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.entries = cls.data["entries"]

    def test_registry_declares_its_schema_policy_and_scope(self) -> None:
        self.assertEqual(self.data["schemaVersion"], "work-lab/recovered-source-registry/v1")
        self.assertTrue(self.data["scope"].strip())
        for key in ("tracked", "machine-local", "absent", "unpinned", "never"):
            self.assertIn(key, self.data["policy"], f"policy does not define {key}")
        self.assertTrue(self.data["generatedAgainstHead"], "no head recorded")

    def test_entries_are_present_unique_and_fully_described(self) -> None:
        self.assertGreaterEqual(len(self.entries), 8,
                                "an almost-empty registry is not a clean registry")
        ids = [e["id"] for e in self.entries]
        self.assertEqual(len(ids), len(set(ids)), "duplicate entry id")
        for e in self.entries:
            for field in REQUIRED_FIELDS:
                self.assertTrue(str(e.get(field, "")).strip(), f"{e.get('id')} missing {field}")
            self.assertIn(e["status"], STATUSES, f"{e['id']} has an undeclared status")

    def test_every_pinned_original_still_has_a_row(self) -> None:
        present = {e["id"] for e in self.entries}
        self.assertEqual(PINNED_ORIGINALS - present, set(),
                         "an AG-19 pinned original was dropped from the registry")

    def test_tracked_entries_exist_in_git_and_hash_to_what_is_recorded(self) -> None:
        tracked = [e for e in self.entries if e["status"] == "tracked"]
        self.assertGreaterEqual(len(tracked), 6,
                                "the tracked half of the registry vanished; the gate would pass vacuously")
        for e in tracked:
            self.assertTrue((ROOT / e["path"]).exists(), f"{e['id']} points at a missing file")
            self.assertTrue(git_tracked(e["path"]), f"{e['id']} claims tracked but is not versioned")
            self.assertEqual(digest(e["path"]), e["sha256"],
                             f"{e['id']} drifted from its recorded digest")
            self.assertGreater(e["bytes"], 0, f"{e['id']} records a non-positive size")

    def test_machine_local_entries_cannot_masquerade_as_tracked(self) -> None:
        for e in [x for x in self.entries if x["status"] == "machine-local"]:
            self.assertTrue(e["path"].startswith(".project-local/"),
                            f"{e['id']} is machine-local but not under the ignored runtime root")
            self.assertFalse(git_tracked(e["path"]), f"{e['id']} is versioned yet labelled machine-local")
            self.assertIn("CI", e["notes"] + self.data["policy"]["machine-local"])
            if (ROOT / e["path"]).exists():
                self.assertEqual(digest(e["path"]), e["sha256"],
                                 f"{e['id']} drifted on the machine that measured it")

    def test_absent_and_unpinned_entries_make_no_digest_claim(self) -> None:
        absent = [e for e in self.entries if e["status"] == "absent"]
        unpinned = [e for e in self.entries if e["status"] == "unpinned"]
        self.assertTrue(absent, "the unrecovered timeline must keep an absent row")
        for e in absent + unpinned:
            self.assertIsNone(e["sha256"], f"{e['id']} makes a hash claim it cannot support")
            self.assertIsNone(e["bytes"], f"{e['id']} makes a size claim it cannot support")
        timeline = next(e for e in absent if "timeline" in e["id"])
        for marker in ("15,558,839", "432,344", "not 'deleted'"):
            self.assertIn(marker, timeline["notes"] + timeline["originalLocation"],
                          f"the timeline row lost the negative-proof detail {marker}")

    def test_migrated_assets_record_where_they_came_from(self) -> None:
        migrated = [e for e in self.entries if e["kind"] == "migrated-asset"]
        self.assertEqual(len(migrated), 5, "the brand set is five files")
        for e in migrated:
            self.assertIn("apps/observer/web/assets/brand/", e["originalLocation"],
                          f"{e['id']} does not record its original location")
            self.assertIn("byte-identical", e["coverageRelation"],
                          f"{e['id']} does not record its coverage relation")
            self.assertIn("6de25fe", e["verificationCommand"] + e["notes"],
                          f"{e['id']} does not name the recovery point")


if __name__ == "__main__":
    unittest.main()
