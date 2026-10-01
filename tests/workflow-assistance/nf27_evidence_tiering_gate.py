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


if __name__ == "__main__":
    unittest.main()
