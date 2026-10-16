"""W07 (2026-10-17): the CI-job <-> local-gate mapping, and the falsifications that keep it honest.

Why the falsifications matter more than the pass: the mapping is a *claim about two other files*. A checker
that only re-reads today's tree proves today's tree; these cases plant the three failures the mapping exists
to catch -- a gate naming a job that does not exist, a job nothing claims, and a CI-only check that is silent
about being CI-only -- and require each to be reported with its name.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ci" / "verify_gate_ci_job_mapping.py"


def load_module():
    spec = importlib.util.spec_from_file_location("verify_gate_ci_job_mapping", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def profile_with(**gates):
    return {"gates": {name: {"ci_job": job} for name, job in gates.items()}, "ci": {}}


class MappingTests(unittest.TestCase):
    def test_the_live_mapping_passes_and_names_every_job(self) -> None:
        proc = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        out = proc.stdout + proc.stderr
        self.assertEqual(0, proc.returncode, out)
        self.assertIn("GATE_CI_JOB_MAPPING_PASS", out)
        self.assertIn("every job is claimed or declared", out)

    def test_a_gate_naming_a_nonexistent_job_is_reported(self) -> None:
        module = load_module()
        problems = module.audit(profile_with(workflow="workflow", observer="nope-not-a-job"),
                                {"workflow": "work-lab-gate.yml"}, set())
        self.assertTrue(any("nope-not-a-job" in problem for problem in problems),
                        f"a gate claiming a job that does not exist must be named: {problems}")

    def test_a_job_no_one_claims_is_reported(self) -> None:
        """The rule W07 asks for: a required CI job a writer cannot see from a local run."""
        module = load_module()
        problems = module.audit(profile_with(workflow="workflow"),
                                {"workflow": "work-lab-gate.yml", "silent-new-job": "work-lab-gate.yml"}, set())
        self.assertTrue(any("silent-new-job" in problem for problem in problems),
                        f"an unclaimed job must be reported, not tolerated: {problems}")

    def test_a_ci_only_route_must_say_so_and_a_stale_declaration_is_caught(self) -> None:
        module = load_module()
        profile = profile_with(workflow="workflow")
        # `capsule-verify` exists in the workflow but declares no local_route field at all -> the field is
        # missing, which is exactly the silence this checker rejects.
        profile["ci"] = {"additional_required_jobs": {"capsule-verify": {"note": "CI only, honest"}}}
        problems = module.audit(profile, {"workflow": "work-lab-gate.yml", "capsule-verify": "wlr-060-gates.yml"},
                                set())
        self.assertTrue(any("declares no local_route" in problem for problem in problems), problems)

        # Declaring it as null WITH a note is the accepted shape: the gap is visible on purpose.
        profile["ci"]["additional_required_jobs"]["capsule-verify"] = {
            "local_route": None, "note": "CI-only with negative controls; no local test module"}
        self.assertEqual([], [p for p in module.audit(
            profile, {"workflow": "work-lab-gate.yml", "capsule-verify": "wlr-060-gates.yml"}, set())
            if "capsule-verify" in p])

    def test_a_local_route_pointing_at_an_untracked_file_is_reported(self) -> None:
        module = load_module()
        profile = profile_with(workflow="workflow")
        profile["ci"] = {"additional_required_jobs": {
            "config-compiler": {"local_route": "python tests/ci/does_not_exist.py", "note": "x"}}}
        problems = module.audit(profile, {"workflow": "work-lab-gate.yml", "config-compiler": "x.yml"}, set())
        self.assertTrue(any("not tracked" in problem for problem in problems), problems)


if __name__ == "__main__":
    unittest.main(verbosity=2)
