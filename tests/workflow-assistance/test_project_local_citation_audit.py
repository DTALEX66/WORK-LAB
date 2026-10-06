"""Gate: a tracked document may not cite an absent `.project-local` evidence path without a disposition.

The auditable claim is not "how many absent paths are there" (that number is an artefact of the
scanner's scope: 28 from one pass, 200 tokens from a full-tree pass). It is the narrower one this
gate protects — every path that survives classification as a possible unavailable-evidence claim
must carry a hand-written disposition, so a reader is never sent to bytes that are not there.

Negative controls feed the classifier the exact sentence shapes that shipped so its buckets cannot
rot: an instruction to create a file must not be confused with a claim that the file is evidence.
"""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "audit" / "project_local_citation_audit.py"
AUDIT = ROOT / "docs" / "audits" / "PROJECT_LOCAL_CITATION_AUDIT_2026-10-07.json"

spec = importlib.util.spec_from_file_location("plca", SCRIPT)
plca = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plca)

REVIEW_CLASSES = ("machine_field_pointing_at_absent_path", "unclassified_needs_human_read")


def classify(line: str, file: str = "docs/current/some-doc.md",
             token: str = ".project-local/runs/x/receipt.json") -> str:
    return plca.classify(token, file, line)


class CitationAuditGate(unittest.TestCase):
    def test_shipped_audit_exists_and_is_the_current_schema(self) -> None:
        doc = json.loads(AUDIT.read_text(encoding="utf-8"))
        self.assertEqual(doc["schemaVersion"], "work-lab/project-local-citation-audit/v2")
        self.assertGreater(doc["scope"]["trackedFilesScanned"], 1500)

    def test_every_queued_path_has_a_disposition(self) -> None:
        doc = json.loads(AUDIT.read_text(encoding="utf-8"))
        unadjudicated = [p for p, d in doc["dispositions"].items() if d == "UNADJUDICATED"]
        self.assertEqual(unadjudicated, [], "queued citations without a per-path disposition")
        self.assertEqual(doc["counts"]["unadjudicated"], 0)

    def test_the_two_repaired_claims_are_reachable_on_disk(self) -> None:
        # the P0C re-point must land on bytes that actually exist, or the correction is itself a lie
        imported = (ROOT / ".project-local" / "imported-from-workbuddy-20261006" /
                    "WORK-LAB__task-decomposition-atlas-gap-archive-20261001-381e33ec" /
                    ".project-local" / "runs" / "p0c-diag-20261006")
        self.assertTrue(imported.is_dir(), "the re-pointed evidence root is not on disk")
        self.assertGreater(len(list(imported.iterdir())), 10)
        self.assertTrue((ROOT / "taskpacks" / "current" / "error-ledger.json").is_file())

    def test_an_evidence_citation_to_an_absent_path_reaches_the_review_queue(self) -> None:
        self.assertIn(classify("复现命令（证据在 `.project-local/runs/x/receipt.json`）："), REVIEW_CLASSES)
        self.assertIn(classify('see .project-local/runs/x/receipt.json for the full capture'),
                      REVIEW_CLASSES)

    def test_a_declared_destination_is_not_an_evidence_claim(self) -> None:
        self.assertEqual(classify('DEFAULT_OUT = Path(".project-local/runs/x/receipt.json")',
                                 "scripts/ci/x.py"),
                         "declared_output_destination_or_fixture_in_code")
        self.assertEqual(classify("python audit.py --output .project-local/runs/x/receipt.json"),
                         "declared_output_destination_or_fixture_in_code")

    def test_a_removal_record_is_not_an_evidence_claim(self) -> None:
        self.assertEqual(classify("deleted: this path must not exist after cleanup"),
                         "negative_assertion_or_removal_record")
        self.assertEqual(classify("legacy isolated-checkout layout, no longer used"),
                         "negative_assertion_or_removal_record")

    def test_a_placeholder_never_counts_as_one_missing_file(self) -> None:
        self.assertEqual(classify("writes .project-local/runs/probe-202XX.json",
                                  token=".project-local/runs/probe-202XX.json"),
                         "path_pattern_or_truncated_token")

    def test_the_scanner_is_not_vacuous_on_this_tree(self) -> None:
        # an empty bucket table would make every assertion above pass by accident
        doc = json.loads(AUDIT.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(doc["countsByClass"]), 5)
        self.assertGreaterEqual(sum(v["citations"] for v in doc["countsByClass"].values()), 150)
        self.assertGreaterEqual(len(doc["unavailableEvidenceReviewQueue"]), 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
