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

        self.assertTrue(retired.isdisjoint(selected))
        self.assertEqual(selected, all_tests - retired)
        self.assertIn("tests/workflow-assistance/test_codex_global_asset_sync.py", selected)

    def test_governance_modules_are_importable_from_tests_pythonpath(self) -> None:
        modules = [Path(path).stem for path in MODULE.governance_test_files()]
        self.assertIn("test_codex_global_asset_sync", modules)
        self.assertNotIn("test_design_token_compliance", modules)
        self.assertTrue(all("/" not in module and "\\" not in module for module in modules))


if __name__ == "__main__":
    unittest.main()
