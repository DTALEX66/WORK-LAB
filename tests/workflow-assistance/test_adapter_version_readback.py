"""Gate: a registry version claim must be backed by the receipt that produced it.

`provenance.version` is allowed to carry only a natively verified value, and AG-07 gave it a structured
`version_readback` so drift is machine-checkable. Five entries were filled on 2026-10-07 from a Windows
version-resource read, so the claim now has an upstream artifact. This gate is what makes that pairing
enforceable instead of a promise in prose: a version without a matching, un-launched receipt fails, and so
does a version readback that quietly promotes a detection state a hash was supposed to own.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "config/adapter-registry.json"
RECEIPT = ROOT / "docs/audits/TOOL_VERSION_METADATA_PROBE_2026-10-07.json"

# manifest-only clients: no live entry point is declared, so nothing may be observed for them yet.
DECLARATIVE_ONLY = {"cursor", "claude-code", "workbuddy"}


class AdapterVersionReadbackGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.entries = {e["id"]: e for e in cls.registry["entries"]}
        cls.receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

    def receipt_row(self, adapter: str) -> dict:
        return self.receipt["results"][adapter]

    def observed_version(self, adapter: str) -> str | None:
        row = self.receipt_row(adapter)
        if row.get("fileVersion"):
            return row["fileVersion"]
        binary = row.get("binary") or {}
        return binary.get("fileVersion")

    def test_the_receipt_declares_that_nothing_was_launched(self) -> None:
        self.assertIs(False, self.receipt["launchedAnyProcessForVersion"])
        for adapter, row in self.receipt["results"].items():
            if "launched" in row:
                self.assertIs(False, row["launched"], adapter)

    def test_every_version_readback_agrees_with_the_registry_version(self) -> None:
        for adapter, entry in self.entries.items():
            readback = entry["provenance"].get("version_readback")
            if not readback:
                continue
            self.assertEqual(entry["provenance"]["version"], readback["verified_version"], adapter)
            self.assertTrue(readback.get("observed_at"), f"{adapter}: an undated observation cannot age")
            self.assertTrue(readback.get("method"), adapter)
            self.assertNotIn("UNVERIFIED", readback["verified_version"],
                             f"{adapter}: a placeholder is not a verified version")

    def test_a_file_version_claim_is_reproducible_from_the_receipt(self) -> None:
        claimed = [a for a, e in self.entries.items()
                   if (e["provenance"].get("version_readback") or {}).get("method", "")
                   .startswith("windows-file-version-resource")]
        self.assertGreaterEqual(len(claimed), 4, "the gate must have real rows to check")
        for adapter in claimed:
            with self.subTest(adapter=adapter):
                self.assertEqual(self.entries[adapter]["provenance"]["version"],
                                 self.observed_version(adapter),
                                 "registry version is not the number the receipt read from the binary")

    def test_a_version_readback_never_promotes_a_detection_state(self) -> None:
        # A readback proves which binary is installed; it does not verify the package hash, so it cannot
        # buy evidence_state.
        for adapter, entry in self.entries.items():
            if entry["provenance"].get("version_readback"):
                self.assertIn(entry["detection"]["evidence_state"],
                              {"UNVERIFIED", "BLOCKED", "SKIPPED_OPTIONAL"}, adapter)

    def test_declared_only_clients_stay_unverified(self) -> None:
        for adapter in DECLARATIVE_ONLY:
            entry = self.entries[adapter]
            self.assertEqual("UNVERIFIED", entry["provenance"]["version"], adapter)
            self.assertNotIn("version_readback", entry["provenance"], adapter)

    def test_hermes_and_deepseek_harness_keep_their_older_dated_readbacks(self) -> None:
        # Both were observed before this receipt existed; aging them out is honest, deleting the record is not.
        for adapter in ("hermes", "deepseek-harness"):
            readback = self.entries[adapter]["provenance"]["version_readback"]
            self.assertRegex(readback["observed_at"], r"^\d{4}-\d{2}-\d{2}$", adapter)
            self.assertLessEqual(readback["observed_at"], "2026-10-07", adapter)
            self.assertEqual(self.entries[adapter]["provenance"]["version"],
                             readback["verified_version"], adapter)

    def test_the_wrapper_and_the_resourceless_binary_are_not_claimed_as_versions(self) -> None:
        hermes = self.receipt_row("hermes")
        self.assertEqual("FILE_EXISTS_WITHOUT_VERSION_RESOURCE", hermes["verdict"])
        self.assertNotIn("fileVersion", hermes)
        self.assertEqual("ENTRY_IS_WRAPPER_USE_LIVE_PROBE", self.receipt_row("codex")["verdict"])
        # The codex number in the registry therefore came from running the wrapper, not from a file.
        self.assertEqual("official-cli-version-readback",
                         self.entries["codex"]["provenance"]["version_readback"]["method"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
