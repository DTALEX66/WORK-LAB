from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("telemetry_ledger", ROOT / "scripts/workflow/telemetry_ledger.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

class TelemetryLedgerTests(unittest.TestCase):
    def test_append_is_idempotence_guarded_and_projection_is_redacted(self):
        with tempfile.TemporaryDirectory() as raw:
            ledger = module.TelemetryLedger(Path(raw) / "telemetry.jsonl")
            row = ledger.append({"event_id": "e1", "occurred_at": "2026-08-08T00:00:00Z", "source": "workflow", "outcome": "completed", "usage_total": 3})
            self.assertEqual(row["sequence"], 1)
            self.assertEqual(ledger.projection()["event_count"], 1)
            with self.assertRaises(ValueError):
                ledger.append({"event_id": "e1", "source": "workflow"})

    def test_sensitive_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            ledger = module.TelemetryLedger(Path(raw) / "telemetry.jsonl")
            with self.assertRaises(ValueError):
                ledger.append({"event_id": "e2", "prompt": "redacted"})

if __name__ == "__main__":
    unittest.main()
