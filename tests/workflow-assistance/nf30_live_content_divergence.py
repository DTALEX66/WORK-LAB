"""Negative controls for the live-content-divergence rule (audit F04).

F04 found that the deployed copy of `windows-development-environment` is ahead of
the repository source: 145 lines versus 142, including two lesson entries (30 and 31)
and a `references/frontend-baseline-contract.md` that the repository does not have.
A digest comparison cannot see that, and the sanctioned single-direction publish
would overwrite the deployed file and destroy all of it.

The rule that must hold is therefore about actionability, not existence: if an entry
declares that the deployed copy is ahead, the declaration has to name the content, a
remediation path, and the impact of a redeploy — otherwise it records a loss without
making it fixable.

Synthetic fixtures plus one live assertion. Nothing is written.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "packages" / "client-neutral-core" / "scripts" / "security" / "check_skill_provenance.py"


def _load():
    spec = importlib.util.spec_from_file_location("ag06o_skill_provenance", SPEC)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


P = _load()


class LiveDivergenceControls(unittest.TestCase):
    def _validate(self, divergence, *, live_sha_equals_source=True) -> str:
        """Build a minimal manifest and return the raised message, or ''."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            skill = repo / "skills" / "s1"
            skill.mkdir(parents=True)
            body = (
                "---\n"
                "name: s1\n"
                "version: 1.0.0\n"
                "metadata:\n"
                "  hermes:\n"
                "    tags: [test]\n"
                "---\n"
                "body\n"
            )
            (skill / "SKILL.md").write_text(body, encoding="utf-8")
            digest = P.sha256(skill / "SKILL.md")
            entry = {
                "name": "s1",
                "source": "skills/s1/SKILL.md",
                "source_sha256": digest,
                "live": "skills/s1/SKILL.md",
                "live_sha256": digest if live_sha_equals_source else "0" * 64,
                "version": "1.0.0",
                "trust": "repository-controlled",
                "enabled": True,
                "permission": "skill-guidance",
                "profile_scope": "default",
            }
            if divergence is not None:
                entry["live_content_divergence"] = divergence
            manifest = {
                "schema_version": 1,
                "source_roots": ["skills"],
                "entries": [entry],
            }
            path = repo / "provenance.yaml"
            path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
            try:
                P.validate(repo, path)
            except ValueError as exc:
                return str(exc)
            return ""

    @staticmethod
    def _complete() -> dict:
        return {
            "live_ahead_of_source": True,
            "live_only_lessons": ["30. a lesson"],
            "remediation_path": "review then land in source and publish",
            "effect_if_redeployed_without_review": "the lesson is destroyed",
        }

    def test_complete_divergence_passes(self) -> None:
        self.assertEqual(self._validate(self._complete()), "")

    def test_divergence_without_remediation_fails(self) -> None:
        block = self._complete()
        block.pop("remediation_path")
        message = self._validate(block)
        self.assertIn("live divergence without remediation", message)

    def test_divergence_without_impact_fails(self) -> None:
        block = self._complete()
        block.pop("effect_if_redeployed_without_review")
        message = self._validate(block)
        self.assertIn("live divergence without impact", message)

    def test_divergence_without_content_fails(self) -> None:
        block = self._complete()
        block["live_only_lessons"] = []
        block["live_only_references"] = []
        message = self._validate(block)
        self.assertIn("live divergence without content", message)

    def test_reference_only_divergence_is_accepted(self) -> None:
        block = self._complete()
        block["live_only_lessons"] = []
        block["live_only_references"] = [{"rel": "references/x.md", "sha256": "a" * 64}]
        self.assertEqual(self._validate(block), "")

    def test_not_ahead_is_ignored(self) -> None:
        block = self._complete()
        block["live_ahead_of_source"] = False
        self.assertEqual(self._validate(block), "")

    def test_self_inconsistency_still_fails(self) -> None:
        # The AG-06c rule must survive: live==source with differing digests is
        # self-contradictory regardless of any divergence block.
        message = self._validate(None, live_sha_equals_source=False)
        self.assertIn("live/source self-inconsistency", message)

    def test_live_manifest_records_the_windows_divergence(self) -> None:
        manifest = yaml.safe_load(
            (ROOT / "config/skill-provenance.yaml").read_text(encoding="utf-8")
        )
        entry = next(
            e for e in manifest["entries"] if e["name"] == "windows-development-environment"
        )
        block = entry["live_content_divergence"]
        self.assertIs(block["live_ahead_of_source"], True)
        self.assertEqual(len(block["live_only_lessons"]), 2)
        self.assertTrue(block["live_only_references"])
        self.assertTrue(block["remediation_path"])
        self.assertTrue(block["effect_if_redeployed_without_review"])
        # The dangling citation is part of the record, not smoothed away.
        self.assertTrue(block["stale_citations"])

    def test_live_manifest_divergence_names_the_missing_reference(self) -> None:
        manifest = yaml.safe_load(
            (ROOT / "config/skill-provenance.yaml").read_text(encoding="utf-8")
        )
        entry = next(
            e for e in manifest["entries"] if e["name"] == "windows-development-environment"
        )
        refs = entry["live_content_divergence"]["live_only_references"]
        self.assertEqual(refs[0]["rel"], "references/frontend-baseline-contract.md")
        # And that reference must genuinely be absent from the repository source,
        # which is why a redeploy would lose it.
        repo_ref = (
            ROOT
            / "packages/client-neutral-core/skills/software-development"
            / "windows-development-environment/references/frontend-baseline-contract.md"
        )
        self.assertFalse(repo_ref.exists())

    def test_live_manifest_passes_the_gate(self) -> None:
        manifest_path = ROOT / "config/skill-provenance.yaml"
        self.assertEqual(P.validate(ROOT, manifest_path), 0)


if __name__ == "__main__":
    unittest.main()
