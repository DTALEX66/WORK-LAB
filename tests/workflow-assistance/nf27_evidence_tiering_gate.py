"""Negative controls for the AG-06i evidence-tiering gate (audit F15/F16).

Audit F15/F16 exposed a class of defect, not a single typo: an evidence bundle can
be *internally consistent* — every digest matches, every tally adds up — while
still inviting a reader to conclude something it cannot support. The two concrete
cases were `external_roots_touched: []` (which cannot show a root was never read)
and a secret scan whose scanner source was not retained (so it cannot be
re-derived by a third party).

The gate must therefore be testable in both directions: it has to refuse an
untiered behavioural claim, and it must refuse a sub-VERIFIED claim that names
nothing it cannot establish — because that is precisely the shape that *reads* as
proof. A gate that only checked for the block's presence would pass the very text
that caused the finding.

Synthetic fixtures only. No bundle content is modified, no network call, no file
outside a temp dir is written.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "scripts" / "ci" / "verify_evidence_tiering.py"


def _load():
    spec = importlib.util.spec_from_file_location("ag06i_evidence_tiering", SPEC)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V = _load()


def _bundle(**overrides) -> dict:
    base = {
        "schema": "test/bundle/v1",
        "secrets_included": False,
        "external_roots_touched": [],
        "behavior_declarations": {
            "evidence_tier": "DECLARED",
            "tier_definition": "declared by the generating procedure, not reproduced",
            "generating_procedure_retained": False,
            "claims": [
                {
                    "field": "external_roots_touched",
                    "tier": "DECLARED",
                    "can_establish": ["the bundle records no external-root access"],
                    "cannot_establish": [
                        "that no external root was read",
                        "that no external root was written",
                    ],
                }
            ],
        },
    }
    base.update(overrides)
    return base


class EvidenceTieringNegativeControls(unittest.TestCase):
    def _check(self, obj: dict) -> list[str]:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as handle:
            json.dump(obj, handle, ensure_ascii=False)
            path = Path(handle.name)
        try:
            return V.check_bundle(path)
        finally:
            path.unlink()

    # --- the gate must PASS a properly tiered bundle ---------------------
    def test_tiered_bundle_passes(self) -> None:
        self.assertEqual(self._check(_bundle()), [])

    # --- and must FAIL each way the original defect could recur ----------
    def test_behavioural_claim_without_any_tier_block_fails(self) -> None:
        obj = _bundle()
        obj.pop("behavior_declarations")
        problems = self._check(obj)
        self.assertTrue(problems)
        self.assertIn("BEHAVIOURAL_CLAIM_WITHOUT_TIER", problems[0])

    def test_declared_claim_naming_nothing_it_cannot_establish_fails(self) -> None:
        # This is the important one: the block IS present, the tier IS valid, and
        # the entry still reads as proof. Presence-only checking would miss it.
        obj = _bundle()
        obj["behavior_declarations"]["claims"][0].pop("cannot_establish")
        problems = self._check(obj)
        self.assertTrue(problems)
        self.assertIn("BEHAVIOURAL_CLAIM_OVERREACH", problems[0])

    def test_empty_cannot_establish_also_fails(self) -> None:
        obj = _bundle()
        obj["behavior_declarations"]["claims"][0]["cannot_establish"] = []
        problems = self._check(obj)
        self.assertTrue(problems)
        self.assertIn("BEHAVIOURAL_CLAIM_OVERREACH", problems[0])

    def test_unknown_top_level_tier_fails(self) -> None:
        obj = _bundle()
        obj["behavior_declarations"]["evidence_tier"] = "PROBABLY"
        problems = self._check(obj)
        self.assertTrue(any("BEHAVIOURAL_TIER_UNKNOWN" in p for p in problems))

    def test_unknown_claim_tier_fails(self) -> None:
        obj = _bundle()
        obj["behavior_declarations"]["claims"][0]["tier"] = "MAYBE"
        problems = self._check(obj)
        self.assertTrue(any("BEHAVIOURAL_CLAIM_TIER_UNKNOWN" in p for p in problems))

    def test_verified_claim_with_unretained_procedure_fails(self) -> None:
        # Cannot claim third-party re-derivability while admitting the procedure
        # that produced it was not kept.
        obj = _bundle()
        obj["behavior_declarations"]["claims"][0]["tier"] = "VERIFIED"
        problems = self._check(obj)
        self.assertTrue(any("BEHAVIOURAL_UNREPRODUCIBLE_VERIFIED" in p for p in problems))

    def test_malformed_claims_list_fails(self) -> None:
        obj = _bundle()
        obj["behavior_declarations"]["claims"] = []
        problems = self._check(obj)
        self.assertTrue(any("BEHAVIOURAL_CLAIMS_MALFORMED" in p for p in problems))

    def test_claim_without_field_or_label_fails(self) -> None:
        obj = _bundle()
        entry = obj["behavior_declarations"]["claims"][0]
        entry.pop("field")
        problems = self._check(obj)
        self.assertTrue(any("BEHAVIOURAL_CLAIM_UNLABELLED" in p for p in problems))

    def test_non_claiming_bundle_needs_no_tier_block(self) -> None:
        # A bundle that asserts no behaviour is not forced to carry tiering.
        self.assertEqual(self._check({"schema": "test/bundle/v1", "counts": {"files": 3}}), [])

    def test_verified_tier_with_retained_procedure_passes(self) -> None:
        obj = _bundle()
        obj["behavior_declarations"]["generating_procedure_retained"] = True
        obj["behavior_declarations"]["claims"][0]["tier"] = "VERIFIED"
        obj["behavior_declarations"]["claims"][0]["can_establish"] = ["re-derivable"]
        self.assertEqual(self._check(obj), [])

    # --- the LIVE bundle must actually satisfy the new gate --------------
    def test_live_evidence_bundles_pass_the_gate(self) -> None:
        base = ROOT / "reports" / "audit-evidence" / "assets-20260930"
        paths = [
            base / "MANIFEST.json",
            base / "CLEANUP-CANDIDATES.json",
            base / "global-workflow-coverage.json",
            base / "inventory-verification.json",
            base / "asset-inventory.json",
        ]
        for path in paths:
            with self.subTest(bundle=path.name):
                self.assertTrue(path.is_file(), f"missing live bundle {path}")
                self.assertEqual(V.check_bundle(path), [], f"{path.name} failed tiering")

    def test_live_manifest_states_the_tier_it_cannot_exceed(self) -> None:
        manifest = json.loads(
            (ROOT / "reports/audit-evidence/assets-20260930/MANIFEST.json").read_text(
                encoding="utf-8"
            )
        )
        block = manifest["behavior_declarations"]
        self.assertEqual(block["evidence_tier"], "DECLARED")
        # The unretained-procedure admission must stay recorded, otherwise the
        # bundle would be free to present its findings as re-derivable.
        self.assertIs(block["generating_procedure_retained"], False)
        fields = {claim["field"] for claim in block["claims"]}
        self.assertIn("external_roots_touched", fields)
        for claim in block["claims"]:
            if claim["tier"] != "VERIFIED":
                self.assertTrue(
                    claim["cannot_establish"],
                    "a sub-VERIFIED claim must name what it cannot establish",
                )


class CleanupCandidateNegativeControls(unittest.TestCase):
    """Audit F13/F14: a candidate list must not read as a delete queue.

    F14 is a blocker: live user state must never sit in such a list without an
    explicit, machine-readable rejection, because a reinstall-time reader may act
    on the list as written. F13 adds that overlapping globs need a declared
    precedence so two candidates cannot both own one path.
    """

    def _check(self, obj: dict) -> list[str]:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as handle:
            json.dump(obj, handle, ensure_ascii=False)
            path = Path(handle.name)
        try:
            return V.check_cleanup_candidates(path)
        finally:
            path.unlink()

    @staticmethod
    def _rejected(**overrides) -> dict:
        candidate = {
            "id": "CC-9",
            "path_token": "x",
            "disposition": "REJECT_USER_DATA",
            "disposition_reason": "live user state",
            "deletion_rejected": True,
            "authorization_required": True,
            "executed": False,
            "permitted_actions": ["observe_metadata"],
            "forbidden_actions": ["delete", "move"],
        }
        candidate.update(overrides)
        return {"candidates": [candidate]}

    def test_properly_rejected_user_state_passes(self) -> None:
        self.assertEqual(self._check(self._rejected()), [])

    def test_candidate_without_disposition_fails(self) -> None:
        obj = self._rejected()
        obj["candidates"][0].pop("disposition")
        problems = self._check(obj)
        self.assertTrue(any("CLEANUP_CANDIDATE_UNDISPOSITIONED" in p for p in problems))

    def test_rejected_but_marked_executed_fails(self) -> None:
        problems = self._check(self._rejected(executed=True))
        self.assertTrue(any("CLEANUP_REJECTED_BUT_EXECUTED" in p for p in problems))

    def test_rejected_without_deletion_rejected_flag_fails(self) -> None:
        problems = self._check(self._rejected(deletion_rejected=False))
        self.assertTrue(any("CLEANUP_REJECTED_WITHOUT_FLAG" in p for p in problems))

    def test_rejected_without_authorization_gate_fails(self) -> None:
        problems = self._check(self._rejected(authorization_required=False))
        self.assertTrue(any("CLEANUP_REJECTED_WITHOUT_AUTH_GATE" in p for p in problems))

    def test_rejected_without_forbidden_actions_fails(self) -> None:
        problems = self._check(self._rejected(forbidden_actions=[]))
        self.assertTrue(
            any("CLEANUP_REJECTED_WITHOUT_FORBIDDEN_ACTIONS" in p for p in problems)
        )

    def test_overlap_needs_a_declared_precedence(self) -> None:
        obj = {
            "candidates": [
                {"id": "A", "disposition": "CANDIDATE_NOT_AUTHORIZED", "overlaps_with": ["B"]},
                {"id": "B", "disposition": "CANDIDATE_NOT_AUTHORIZED", "overlaps_with": ["A"]},
            ]
        }
        problems = self._check(obj)
        self.assertTrue(any("CLEANUP_OVERLAP_WITHOUT_PRECEDENCE" in p for p in problems))

    def test_overlap_must_be_reciprocal(self) -> None:
        obj = {
            "candidates": [
                {
                    "id": "A",
                    "disposition": "CANDIDATE_NOT_AUTHORIZED",
                    "overlaps_with": ["B"],
                    "precedence_over": ["B"],
                },
                {"id": "B", "disposition": "CANDIDATE_NOT_AUTHORIZED"},
            ]
        }
        problems = self._check(obj)
        self.assertTrue(any("CLEANUP_OVERLAP_NOT_RECIPROCAL" in p for p in problems))

    def test_dangling_overlap_fails(self) -> None:
        obj = {
            "candidates": [
                {
                    "id": "A",
                    "disposition": "CANDIDATE_NOT_AUTHORIZED",
                    "overlaps_with": ["ZZ"],
                    "precedence_over": ["ZZ"],
                }
            ]
        }
        problems = self._check(obj)
        self.assertTrue(any("CLEANUP_OVERLAP_DANGLING" in p for p in problems))

    def test_live_cleanup_candidates_pass_and_reject_user_state(self) -> None:
        path = (
            ROOT
            / "reports/audit-evidence/assets-20260930/CLEANUP-CANDIDATES.json"
        )
        self.assertEqual(V.check_cleanup_candidates(path), [])
        data = json.loads(path.read_text(encoding="utf-8"))
        rejected = {
            c["id"] for c in data["candidates"] if c.get("disposition") == "REJECT_USER_DATA"
        }
        # These are the two the audit called a blocker. If a future edit drops the
        # rejection, this test fails rather than the list silently becoming a
        # delete queue again.
        self.assertEqual(rejected, {"CC-4", "HH-1"})
        for candidate in data["candidates"]:
            self.assertIs(candidate.get("executed"), False)
            self.assertIs(candidate.get("authorization_required"), True)

    def test_live_overlap_precedence_is_declared(self) -> None:
        data = json.loads(
            (
                ROOT / "reports/audit-evidence/assets-20260930/CLEANUP-CANDIDATES.json"
            ).read_text(encoding="utf-8")
        )
        by_id = {c["id"]: c for c in data["candidates"]}
        self.assertIn("CC-3", by_id["CC-1"].get("overlaps_with", []))
        self.assertIn("CC-1", by_id["CC-3"].get("overlaps_with", []))
        self.assertIn("CC-3", by_id["CC-1"].get("precedence_over", []))


class ArchiveCoverageNegativeControls(unittest.TestCase):
    """Audit F05: a silent enumeration gap must not pass as complete coverage.

    The archive claimed every SKILL.md main file was copied, while its enumeration
    only descended into categorised directories, so root-level skills were never
    captured - 5 of them, one being a MANAGED skill. The tell is structural: one
    nesting level richly populated and a sibling level empty.
    """

    def _check(self, obj: dict) -> list[str]:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as handle:
            json.dump(obj, handle, ensure_ascii=False)
            path = Path(handle.name)
        try:
            return V.check_archive_index_coverage(path)
        finally:
            path.unlink()

    def test_single_depth_population_is_flagged(self) -> None:
        obj = {
            "files": [
                {"archive_path": f"hermes/skills/.archive/s{i}/SKILL.md"}
                for i in range(5)
            ]
        }
        problems = self._check(obj)
        self.assertTrue(any("ARCHIVE_SKILL_DEPTH_UNAUDITED" in p for p in problems))

    def test_declared_reconciliation_clears_the_flag(self) -> None:
        obj = {
            "files": [
                {"archive_path": f"hermes/skills/.archive/s{i}/SKILL.md"}
                for i in range(5)
            ],
            "skills_depth_reconciliation": {"hermes": {"declared_not_silent": True}},
        }
        self.assertEqual(self._check(obj), [])

    def test_categorised_with_root_present_is_not_flagged(self) -> None:
        # The healthy shape: categorised skills AND root-level skills both present,
        # which is what the live tree actually holds.
        obj = {
            "files": [
                {"archive_path": "hermes/skills/.archive/a/SKILL.md"},
                {"archive_path": "hermes/skills/software-development/b/SKILL.md"},
                {"archive_path": "hermes/skills/model-switch/SKILL.md"},
            ]
        }
        self.assertEqual(self._check(obj), [])

    def test_root_level_layout_is_not_flagged_and_categorised_only_is(self) -> None:
        # Pins the semantics instead of a hand-counted number: the root-level
        # layout `<client>/skills/<name>/SKILL.md` is the SAME depth the detection
        # derives, so an index holding only that layout is not an enumeration gap;
        # an index holding only a categorised layout is.
        root_only = {"files": [{"archive_path": "hermes/skills/model-switch/SKILL.md"}]}
        self.assertEqual(self._check(root_only), [])
        categorised_only = {
            "files": [
                {"archive_path": "hermes/skills/.archive/a/SKILL.md"},
                {"archive_path": "hermes/skills/software-development/b/SKILL.md"},
            ]
        }
        self.assertTrue(self._check(categorised_only))

    def test_shallow_only_index_is_not_flagged(self) -> None:
        obj = {"files": [{"archive_path": "hermes/skills/a/SKILL.md"}]}
        self.assertEqual(self._check(obj), [])

    def test_index_without_files_is_ignored(self) -> None:
        self.assertEqual(self._check({"totals": {"copied": 0}}), [])

    def test_live_archive_declares_its_depth_reconciliation(self) -> None:
        path = ROOT / "reports/audit-archive/20260930/ARCHIVE-INDEX.json"
        self.assertEqual(V.check_archive_index_coverage(path), [])
        data = json.loads(path.read_text(encoding="utf-8"))
        reconciliation = data["skills_depth_reconciliation"]["hermes"]
        self.assertEqual(reconciliation["entries_at_shallow_layout"], 0)
        self.assertIs(reconciliation["declared_not_silent"], True)
        # The managed skill that was missing must stay named.
        self.assertIn("model-switch", reconciliation["reason"])
        self.assertIn("MANAGED", reconciliation["reason"])


if __name__ == "__main__":
    unittest.main()
