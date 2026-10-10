"""Mandatory gate: a synthetic secret must not survive ingest into canonical state.

WUI-18's canary clause says the canary uses *synthetic* secrets -- nothing real is planted, and nothing
planted may be stored. The store has always refused a field NAMED like a credential
(``{"api_key": ...}``), so this gate aims at the shape it could not see: a provider token carried as a
VALUE under an ordinary field. Measured 2026-10-10, ``collect_usage_files`` turns a foreign ``usage.jsonl``
line into a canonical record with whatever ``provider``/``model``/``note`` strings it found, so a key hiding
in one of those fields used to be written to ``canonical.sqlite`` and then projected to the Observer.

The negative controls are the point: each planted shape has to be refused, and the two shapes a real
repository is full of -- a 64-hex error fingerprint and a 40-hex commit SHA -- have to keep passing. A guard
that refused those would have broken the worker loop, which is how it was found (an existing
``test_durable_worker`` case convicted it on the first run).
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from canonical_store import CanonicalStore, validate_record
from collectors import collect_usage_files
import project_temp

# Synthetic shapes only. None of these is a live credential; they exist to be caught.
PLANTED = {
    "sk-provider-key": "sk-" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4",
    "aws-style-access-key": "AKIA" + "ABCDEFGHIJKLMNOP",
    "github-server-token": "ghs_" + "0123456789abcdefghij",
    "bearer-header": "Bearer " + "abcdefghijklmnop",
    "raw-base64-blob": "Q" * 64 + "=",
}
BENIGN = {
    "error_fingerprint": "a" * 64,
    "commit_sha": "1234567890abcdef1234567890abcdef12345678",
    "stable_id": "usage-" + "0123456789abcdef0123456789abcdef",
    "note_prose": "the goal mentions a bearer token rotation, but carries no key",
}


class SyntheticSecretCanaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = project_temp.fixture_dir(prefix="canary-ingest-")

    def tearDown(self) -> None:
        project_temp.force_release(self.root)

    def record(self, field: str, value: str) -> dict:
        return {
            "project_id": "work-lab",
            "provider": "github" if field != "provider" else value,
            "model": value if field == "model" else "gpt-test",
            "observed_at": "2026-10-10T00:00:00Z",
            "quality": "EXACT_SOURCE",
            "source_ref": ".hermes/task-artifacts/usage.jsonl",
            "sample_id": "usage-abc",
            "input_tokens": 5,
            "note": value if field == "note" else "",
        }

    def test_a_planted_key_is_refused_wherever_it_is_hidden(self) -> None:
        refused: list[str] = []
        for shape, value in PLANTED.items():
            for field in ("provider", "model", "note"):
                finding = None
                try:
                    validate_record(self.record(field, value), allow_usage_tokens=True)
                except ValueError as exc:
                    finding = str(exc)
                self.assertIsNotNone(finding, f"{shape} in {field} was accepted by validate_record")
                self.assertIn("sensitive value(s) at", finding, f"{shape} in {field}")
                self.assertIn(field, finding, f"{shape} in {field} was not named by path")
                refused.append(f"{shape}/{field}")
        self.assertEqual(15, len(refused), "every planted shape must be caught in every allowed field")

    def test_a_planted_key_in_a_nested_list_is_refused_too(self) -> None:
        record = self.record("provider", "github")
        record["tags"] = ["routine", PLANTED["aws-style-access-key"]]
        with self.assertRaises(ValueError) as refused:
            validate_record(record, allow_usage_tokens=True)
        self.assertIn("tags[1]", str(refused.exception))

    def test_digests_and_prose_are_not_credentials(self) -> None:
        record = self.record("provider", "openai")
        record.update({"error_fingerprint": BENIGN["error_fingerprint"],
                       "head_sha": BENIGN["commit_sha"],
                       "event_id": BENIGN["stable_id"],
                       "note": BENIGN["note_prose"]})
        validate_record(record, allow_usage_tokens=True)  # must not raise

    def test_the_canary_never_reaches_the_canonical_store_through_the_collector(self) -> None:
        artifacts = self.root / ".hermes" / "task-artifacts"
        artifacts.mkdir(parents=True)
        poisoned = {"provider": PLANTED["sk-provider-key"], "model": "gpt-test", "input_tokens": 7}
        honest = {"provider": "openai", "model": "gpt-test", "input_tokens": 3}
        (artifacts / "usage.jsonl").write_text(
            "\n".join(json.dumps(row) for row in (poisoned, honest)) + "\n", encoding="utf-8")

        store = CanonicalStore(self.root / "canonical.sqlite")
        try:
            store.register_project("work-lab", str(self.root), display_name="canary")
            collected = collect_usage_files(store, "work-lab", artifacts)
            self.assertEqual(2, len(collected.records),
                             "the collector should see both lines; the refusal belongs at ingest")
            stored = 0
            refusals = 0
            for row in collected.records:
                try:
                    store.record_usage_sample(row)
                    stored += 1
                except ValueError:
                    refusals += 1
            self.assertEqual(1, refusals, f"the planted key was not refused: {refusals}")
            self.assertEqual(1, stored, "an honest line must not be collateral damage")
            rows = store.list_usage_samples()
            self.assertEqual(1, len(rows), "only the honest sample should be readable back")
            self.assertEqual("openai", rows[0]["provider"])
            self.assertNotIn(PLANTED["sk-provider-key"], json.dumps(rows, ensure_ascii=False),
                             "the readback still carries the planted key")
            self.assertNotIn(PLANTED["sk-provider-key"], json.dumps(store.projection(), ensure_ascii=False,
                                                                    default=str),
                             "the canonical projection still carries the planted key")
        finally:
            store.close()


if __name__ == "__main__":
    unittest.main()
