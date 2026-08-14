"""WLOSS-700 tests: changed-files gate selection."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "workflow" / "run_quality_gate.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("quality_gate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ChangedFilesSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.m = load_runner()

    def test_snapshot_change_selects_snapshot_gate(self) -> None:
        selected = self.m.select_gates_for_changed(["10-workflow/workflow-assistance/scripts/workflow/snapshot_api.py"])
        self.assertIn("snapshot-schema-v3", selected)
        self.assertIn("compile", selected)

    def test_workflow_change_selects_only_fast_gates(self) -> None:
        selected = self.m.select_gates_for_changed([".github/workflows/work-lab-gate.yml"])
        self.assertEqual(set(selected), {"compile"})

    def test_store_test_selects_writer_and_convergence(self) -> None:
        selected = self.m.select_gates_for_changed(["10-workflow/workflow-assistance/tests/test_canonical_store_v2.py"])
        for gate in ("canonical-single-writer", "runtime-convergence", "governance", "compile"):
            self.assertIn(gate, selected)

    def test_tauri_change_selects_tauri_gate(self) -> None:
        selected = self.m.select_gates_for_changed(["30-observer/work-lab-observer/src-tauri/tauri.conf.json"])
        self.assertIn("tauri-readonly-shell", selected)

    def test_canary_change_selects_canary_gate(self) -> None:
        selected = self.m.select_gates_for_changed(["10-workflow/workflow-assistance/scripts/workflow/canary_runner.py"])
        self.assertIn("work-lab-os-canary", selected)

    def test_module_relative_path_matches(self) -> None:
        selected = self.m.select_gates_for_changed(["scripts/workflow/evidence_aggregator.py"])
        self.assertIn("execution-state-machine", selected)

    def test_order_follows_verify_order(self) -> None:
        selected = self.m.select_gates_for_changed(["10-workflow/workflow-assistance/tests/test_snapshot_sse_live.py"])
        order = self.m.VERIFY_ORDER
        positions = [order.index(g) for g in selected]
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()
