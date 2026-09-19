from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "services/orchestration" / "run_quality_gate.py"
SPEC = importlib.util.spec_from_file_location("run_quality_gate", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class QualityGateTests(unittest.TestCase):
    def test_dependency_preflight_fails_once_with_install_instruction(self) -> None:
        with patch.object(MODULE.importlib.util, "find_spec", return_value=None):
            self.assertEqual(MODULE.dependency_preflight(), 2)

    def test_runtime_adapter_gate_is_explicit_but_not_in_default_verify(self) -> None:
        self.assertIn("portable-install-runtime", MODULE.GATES)
        self.assertNotIn("portable-install-runtime", MODULE.VERIFY_ORDER)

    def test_governance_excludes_only_retired_tests(self) -> None:
        selected = set(MODULE.governance_test_files())
        retired = {f"tests/{name}" for name in MODULE.RETIRED_ORDINARY_TESTS}
        all_tests = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "tests" / "workflow-assistance").glob("test_*.py")
        }
        all_negative = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "tests" / "workflow-assistance").glob("nf*.py")
        }

        # P0-05: mandatory discovery is ordinary + negative-control tests, minus
        # the retired set. No hard-coded count; the negative controls are part
        # of the mandatory set now.
        self.assertTrue(retired.isdisjoint(selected))
        self.assertEqual(selected, (all_tests | all_negative) - retired)
        self.assertIn("tests/workflow-assistance/test_codex_global_asset_sync.py", selected)
        self.assertIn("tests/workflow-assistance/nf01_rule_semantics_artifact_flow.py", selected)

    def test_governance_discovers_negative_controls(self) -> None:
        modules = MODULE.mandatory_discovery_modules()
        # A representative negative-control module is importable in the gate.
        self.assertIn("nf01_rule_semantics_artifact_flow", modules)
        self.assertIn("nf14_universal_signoff", modules)
        # No hard-coded count masquerading as truth: the set is discovered.
        self.assertGreater(len([m for m in modules if m.startswith("nf")]), 0)

    def test_governance_not_run_is_not_pass(self) -> None:
        # P0-05 fail-closed: a clean process exit that executed ZERO tests must
        # not be reported as PASS.
        with patch.object(MODULE, "_run_governance_batch", return_value=(0, "no banner here\n")):
            self.assertEqual(MODULE.gate_governance(), 1)

    def test_governance_empty_set_is_not_pass(self) -> None:
        # P0-05 fail-closed: an empty mandatory set is a red flag, not a pass.
        with patch.object(MODULE, "mandatory_discovery_modules", return_value=[]):
            self.assertEqual(MODULE.gate_governance(), 1)

    def test_governance_failed_batch_is_not_pass(self) -> None:
        # P0-05 fail-closed: a non-zero batch exit is propagated, never PASS.
        with patch.object(
            MODULE, "_run_governance_batch", return_value=(1, "Ran 3 tests in 0.1s\nFAILED (failures=1)\n")
        ):
            self.assertEqual(MODULE.gate_governance(), 1)

    def test_negative_mutation_breaks_mandatory_gate(self) -> None:
        # P0-05 negative mutation (real, not simulated): write a throwaway
        # negative-control module whose condition is intentionally broken, run
        # it through the gate's real batch runner, and assert the gate fails.
        # This is the "break one mandatory NF condition -> aggregate must fail"
        # guarantee, with no mutation of any tracked test file.
        import tempfile

        broken = "nf00_mutation_probe"
        tmp_mod = ROOT / "tests" / "workflow-assistance" / f"{broken}.py"
        tmp_mod.write_text(
            "import unittest\n\n\nclass MutationProbe(unittest.TestCase):\n"
            "    def test_broken_condition_fails(self):\n"
            "        self.fail('mandatory negative control intentionally broken')\n\n"
            "if __name__ == '__main__':\n    unittest.main()\n",
            encoding="utf-8",
        )
        try:
            # A single broken mandatory negative control, run through the gate's
            # real batch runner, must produce a non-zero exit -> gate FAIL.
            exit_code, _ = MODULE._run_governance_batch([broken])
            self.assertEqual(exit_code, 1)
            # And the gate wrapper itself reports failure on that same batch.
            with patch.object(MODULE, "_run_governance_batch", return_value=(1, "Ran 1 test in 0.0s\nFAILED (failures=1)\n")):
                self.assertEqual(MODULE.gate_governance(), 1)
        finally:
            tmp_mod.unlink(missing_ok=True)

    def test_governance_modules_are_importable_from_tests_pythonpath(self) -> None:
        modules = [Path(path).stem for path in MODULE.governance_test_files()]
        self.assertIn("test_codex_global_asset_sync", modules)
        self.assertNotIn("test_design_token_compliance", modules)
        self.assertTrue(all("/" not in module and "\\" not in module for module in modules))


if __name__ == "__main__":
    unittest.main()
