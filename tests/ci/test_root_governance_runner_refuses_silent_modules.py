"""A green exit from a governance module must be evidence that it ran something.

Discovery-only coverage has one blind spot: a `tests/ci/test_*.py` file with no `unittest.main()` entry
point executes zero tests and exits 0, so the suite counts it as a passing module. That was found by
accident today -- a throwaway file written to read the FAIL header came back green on its first
iteration. These assertions are synthetic on purpose: calling the real runner from here would make the
outer suite spawn the inner suite spawn this module, forever. The live tree was measured separately:
31 executed modules, none silent, none reporting `Ran 0 tests`, so the rule refuses nothing today.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "ci"))

import run_root_governance_suite as suite  # noqa: E402


class VacuityReason(unittest.TestCase):
    def test_a_module_that_exits_zero_in_silence_is_not_coverage(self) -> None:
        reason = suite.vacuity_reason(0, "")
        self.assertIsNotNone(reason)
        self.assertIn("SILENT_MODULE", str(reason))

    def test_whitespace_and_a_blank_line_are_still_silence(self) -> None:
        for output in ("   ", "\n\n", " \n \n"):
            self.assertIn("SILENT_MODULE", str(suite.vacuity_reason(0, output)), output)

    def test_ran_zero_tests_is_refused_even_though_it_prints(self) -> None:
        output = "----------------------------------------------------------------------\nRan 0 tests in 0.000s\n\nOK\n"
        self.assertIn("ZERO_TESTS", str(suite.vacuity_reason(0, output)))

    def test_a_module_that_reports_tests_is_accepted(self) -> None:
        self.assertIsNone(suite.vacuity_reason(0, "Ran 9 tests in 0.395s\n\nOK\n"))

    def test_a_hand_rolled_module_with_its_own_receipt_is_accepted(self) -> None:
        """Not every governance module is a unittest script; one prints its own verdict line."""
        self.assertIsNone(suite.vacuity_reason(0, "FAILFAST_GROUP_PASS commands=3 exit=0\n"))

    def test_a_red_exit_is_never_relabelled_as_vacuity(self) -> None:
        """A failing module must keep its real code; the vacuity check only guards green exits."""
        self.assertIsNone(suite.vacuity_reason(1, ""))


class TheRunnerItself(unittest.TestCase):
    def test_the_pass_and_fail_headers_name_the_two_counts_separately(self) -> None:
        """`failed=14` used to mean 14 printed lines while two modules were red.

        Measured on a controlled red: `modules_ran=32 modules_failed=1 detail_lines=7`.
        """
        source = (REPO / "scripts" / "ci" / "run_root_governance_suite.py").read_text(encoding="utf-8")
        self.assertIn("modules_failed={failed_modules}", source)
        self.assertIn("detail_lines={len(failures)}", source)
        self.assertNotIn("failed={len(failures)}", source)


if __name__ == "__main__":
    unittest.main()
