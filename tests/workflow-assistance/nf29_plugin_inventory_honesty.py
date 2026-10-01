"""Negative controls for the AG-06l plugin-inventory honesty gate (audit F07).

Audit F07 had two halves. The visible one was a record carrying `commit: null`
while the live install metadata declared a revision. The important one is the
caveat attached to it: **a revision string cannot prove the installed bytes match
that commit.** Verified live on chrome-profiles - the declared revision is
correct, `git rev-parse HEAD` equals it, and yet the working tree does not match,
because `__init__.py` is locally modified (24,433 B installed vs 23,764 B
committed).

So the gate must fail in both directions: when a record claims presence without
observation, and when an observation hides a local delta. The third state matters
too - when nothing is installed there are no bytes to compare, and forcing
true/false there would fabricate a comparison that never happened.

Synthetic fixtures only. No plugin file, no live install metadata, no network.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "scripts" / "ci" / "verify_plugin_inventory.py"


def _load():
    spec = importlib.util.spec_from_file_location("ag06l_plugin_inventory", SPEC)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


P = _load()

LIVE = ROOT / "config" / "plugin-inventory.json"


def _observed(**overrides) -> dict:
    block = {
        "observed_at": "2026-10-01",
        "method": "git rev-parse HEAD plus per-file sha256",
        "observed_commit": "5b9c3257b464c0f926d4355149a8aed9c8f307b4",
        "working_tree_matches_commit": True,
    }
    block.update(overrides)
    return block


def _entry(**overrides) -> dict:
    entry = {
        "id": "p1",
        "lifecycle": "enabled",
        "pinned": False,
        "observed": _observed(),
    }
    entry.update(overrides)
    return {"entries": [entry]}


class PluginInventoryNegativeControls(unittest.TestCase):
    def _check(self, obj: dict) -> list[str]:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as handle:
            json.dump(obj, handle, ensure_ascii=False)
            path = Path(handle.name)
        try:
            return P.check_inventory(path)
        finally:
            path.unlink()

    def test_well_observed_entry_passes(self) -> None:
        self.assertEqual(self._check(_entry()), [])

    def test_presence_without_observation_fails(self) -> None:
        obj = _entry()
        obj["entries"][0].pop("observed")
        problems = self._check(obj)
        self.assertTrue(any("PLUGIN_PRESENCE_WITHOUT_OBSERVATION" in p for p in problems))

    def test_local_delta_must_be_named(self) -> None:
        # The heart of F07: claiming the working tree differs from the commit
        # without saying which path would let the delta disappear.
        obj = _entry(observed=_observed(working_tree_matches_commit=False))
        problems = self._check(obj)
        self.assertTrue(any("PLUGIN_LOCAL_DELTA_UNNAMED" in p for p in problems))

    def test_local_delta_with_named_paths_passes(self) -> None:
        obj = _entry(
            observed=_observed(
                working_tree_matches_commit=False,
                locally_modified_paths=["__init__.py"],
                installed_file_digests={"__init__.py": "a" * 64},
                committed_file_digests={"__init__.py": "b" * 64},
            )
        )
        self.assertEqual(self._check(obj), [])

    def test_undecided_comparison_fails(self) -> None:
        block = _observed()
        block.pop("working_tree_matches_commit")
        problems = self._check(_entry(observed=block))
        self.assertTrue(any("PLUGIN_OBSERVATION_UNDECIDED" in p for p in problems))

    def test_not_comparable_requires_a_reason(self) -> None:
        block = _observed(working_tree_matches_commit="NOT_COMPARABLE")
        problems = self._check(_entry(observed=block))
        self.assertTrue(any("PLUGIN_COMPARISON_UNEXPLAINED" in p for p in problems))

    def test_not_comparable_with_reason_passes(self) -> None:
        # Nothing installed means no bytes to compare; that is an honest answer.
        obj = _entry(
            lifecycle="discovered",
            observed=_observed(
                working_tree_matches_commit="NOT_COMPARABLE",
                comparison_not_possible_reason="no installed directory observed",
                observed_commit=None,
            ),
        )
        obj["entries"][0]["pinned"] = True
        self.assertEqual(self._check(obj), [])

    def test_observation_must_be_dated(self) -> None:
        block = _observed()
        block.pop("observed_at")
        problems = self._check(_entry(observed=block))
        self.assertTrue(any("PLUGIN_OBSERVATION_UNDATED" in p for p in problems))

    def test_floating_revision_needs_an_observed_commit(self) -> None:
        obj = _entry(observed=_observed(observed_commit=None))
        problems = self._check(obj)
        self.assertTrue(
            any("PLUGIN_FLOATING_WITHOUT_OBSERVED_REVISION" in p for p in problems)
        )

    def test_declared_vs_observed_disagreement_must_be_explained(self) -> None:
        obj = _entry(declared_vs_observed={"agreement": False})
        problems = self._check(obj)
        self.assertTrue(
            any("PLUGIN_DISAGREEMENT_WITHOUT_INTERPRETATION" in p for p in problems)
        )

    def test_known_revision_but_null_commit_fails(self) -> None:
        # The original F07 shape.
        obj = _entry(declared_revision="5b9c3257" + "0" * 32, commit=None)
        obj["entries"][0]["observed"]["installed_directory_present"] = True
        problems = self._check(obj)
        self.assertTrue(any("PLUGIN_REVISION_KNOWN_BUT_UNRECORDED" in p for p in problems))

    def test_live_inventory_passes_the_gate(self) -> None:
        self.assertTrue(LIVE.is_file())
        self.assertEqual(P.check_inventory(LIVE), [])

    def test_live_chrome_profiles_records_its_real_delta(self) -> None:
        data = json.loads(LIVE.read_text(encoding="utf-8"))
        entry = next(e for e in data["entries"] if e["id"] == "chrome-profiles")
        observed = entry["observed"]
        # The declared revision is correct AND the working tree still differs.
        # Both facts must survive in the record; dropping either one recreates the
        # audit's complaint.
        self.assertEqual(observed["observed_commit"], entry["declared_revision"])
        self.assertIs(observed["working_tree_matches_commit"], False)
        self.assertEqual(observed["locally_modified_paths"], ["__init__.py"])
        self.assertIn("__init__.py", observed["installed_file_digests"])
        self.assertNotEqual(
            observed["installed_file_digests"]["__init__.py"],
            observed["committed_file_digests"]["__init__.py"],
        )
        self.assertIs(entry["pinned"], False)
        self.assertEqual(entry["version_kind"], "FLOATING_REVISION")

    def test_live_uninstalled_entries_keep_declared_lifecycle(self) -> None:
        # The disagreement must be RECORDED, not resolved by rewriting the
        # declared lifecycle to match today's observation.
        data = json.loads(LIVE.read_text(encoding="utf-8"))
        for entry in data["entries"]:
            if entry["id"] == "chrome-profiles":
                continue
            with self.subTest(plugin=entry["id"]):
                self.assertEqual(entry["lifecycle"], "enabled")
                dvo = entry["declared_vs_observed"]
                self.assertIs(dvo["agreement"], False)
                self.assertTrue(dvo["interpretation"])
                self.assertIs(entry["observed"]["installed_directory_present"], False)


if __name__ == "__main__":
    unittest.main()
