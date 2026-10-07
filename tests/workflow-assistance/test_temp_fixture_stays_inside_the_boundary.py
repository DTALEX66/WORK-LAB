"""Gate: a throwaway fixture directory must not be created outside the project boundary.

ERR-140: `tests/ci/test_project_authority_reference.py` built its copy of the live authority package
with a bare `tempfile.mkdtemp(prefix="auth-ref-")`. `tearDown` did call `shutil.rmtree(...,
ignore_errors=True)`, and on this machine that swallow let nineteen complete mirrors of
`WORK-LAB-AUTHORITY.md`, both authority indexes, the open-task register, the error ledger and the
current taskcards sit in `%TEMP%` — 304 files / 7,126,653 bytes of governance material outside the
Git root, which `.project/governance/project-data-boundary.json` forbids ("all content this project
produces — builds, caches, temp files, evidence … stays locked inside the project Git root"). The
residue was released by `scripts/maintenance/release_authority_reference_temp_residue.py` after a
per-file manifest and an archive of the contents that differed from the live tree; the root cause is
the `dir=` argument this gate now enforces for its own file.

`mkdtemp` is the target because it leaks unless someone remembers to remove it.
`tempfile.TemporaryDirectory()` deletes itself on context exit, so 300+ of those are not the defect
class here and are deliberately out of scope.

Matching is done on the syntax tree, not on line text: the docstring of the fixed file *mentions*
`mkdtemp(prefix="auth-ref-")`, and a textual matcher reports prose as a violation.

Discovered dynamically by `run_quality_gate.py governance`.
"""
from __future__ import annotations

import ast
import subprocess
import unittest
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXED = "tests/ci/test_project_authority_reference.py"

# Same-module debt: test helpers that build fixtures. Listed so the count is visible and can shrink.
DEBT_TESTS = {
    "tests/ci/test_source_ledger_v4.py": 1,
    "tests/workflow-assistance/nf08_b_durable_inbox.py": 1,
    "tests/workflow-assistance/nf23_software_registry_and_install_probe.py": 1,
    "tests/workflow-assistance/nf24_observer_readonly_boundary.py": 1,
    "tests/workflow-assistance/test_canonical_store_v2.py": 4,
    "tests/workflow-assistance/test_cleanup.py": 1,
    "tests/workflow-assistance/test_context_pack_recovery.py": 1,
    "tests/workflow-assistance/test_session_federation.py": 5,
    "tests/workflow-assistance/test_sidecar_endpoint.py": 1,
    "tests/workflow-assistance/test_sidecar_v3_snapshot.py": 1,
    "tests/workflow-assistance/test_usage_ingestion.py": 1,
    "tests/workflow-assistance/test_wlgm_privacy.py": 3,
}
# Cross-module debt (client-neutral-core / services): AGENTS.md requires an explicit cross-module
# task card before changing those owners' code, so they are named here rather than edited silently.
DEBT_PRODUCTION = {
    "packages/client-neutral-core/scripts/platform_collector.py": 1,
    "packages/client-neutral-core/scripts/verify_gate_runtime_convergence.py": 2,
    "services/session-federation/gate.py": 4,
}


def tracked_python() -> list[str]:
    raw = subprocess.run(["git", "-c", "core.quotePath=false", "ls-files", "-z", "*.py"],
                         cwd=ROOT, capture_output=True).stdout.split(b"\0")
    return [p.decode("utf-8", "replace") for p in raw if p]


def bare_mkdtemp_calls(source: str) -> list[int]:
    """Line numbers of `mkdtemp(...)` calls in this source that pass no `dir=` keyword."""
    found = []
    with warnings.catch_warnings():
        # several parsed modules carry invalid escape sequences in their own docstrings; that is
        # their business, and letting it print once per file buries the gate's actual output
        warnings.simplefilter("ignore", SyntaxWarning)
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return found
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = (func.attr if isinstance(func, ast.Attribute)
                else func.id if isinstance(func, ast.Name) else "")
        if name != "mkdtemp":
            continue
        if any(kw.arg == "dir" for kw in node.keywords):
            continue
        found.append(node.lineno)
    return found


def scan() -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    for rel in tracked_python():
        path = ROOT / rel
        if not path.is_file():
            continue
        lines = bare_mkdtemp_calls(path.read_text(encoding="utf-8", errors="replace"))
        if lines:
            out[rel] = lines
    return out


class TempFixtureBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sites = scan()

    def test_the_matcher_distinguishes_a_call_from_a_sentence_about_a_call(self) -> None:
        self.assertEqual(bare_mkdtemp_calls('tmp = tempfile.mkdtemp(prefix="x-")'), [1])
        self.assertEqual(bare_mkdtemp_calls('tempfile.mkdtemp(dir=ROOT)'), [])
        self.assertEqual(bare_mkdtemp_calls('# an earlier version used mkdtemp(prefix="auth-ref-")'), [])
        self.assertEqual(bare_mkdtemp_calls('from tempfile import mkdtemp\nmkdtemp()'), [2])
        # a local name shadowing mkdtemp is treated as a call too: over-reporting is the safe side of
        # a boundary gate, so this is the documented behaviour rather than a precision bug
        self.assertEqual(bare_mkdtemp_calls('mkdtemp = 1\nmkdtemp(3)'), [2])

    def test_the_file_that_leaked_is_now_clean(self) -> None:
        self.assertNotIn(FIXED, self.sites,
                         "the ERR-140 offender is bare again: pass dir= inside .project-local/runs")
        source = (ROOT / FIXED).read_text(encoding="utf-8")
        self.assertIn("dir=_runtime_root()", source, "the fixture no longer pins its temp root")

    def test_every_remaining_bare_site_is_a_named_debt_that_can_only_shrink(self) -> None:
        pinned = {f: n for d in (DEBT_TESTS, DEBT_PRODUCTION) for f, n in d.items()}
        measured = {f: len(lines) for f, lines in self.sites.items()}
        new = {f: n for f, n in measured.items() if f not in pinned}
        self.assertEqual(new, {}, f"unadjudicated bare mkdtemp sites: {new}")
        for f, n in measured.items():
            self.assertLessEqual(n, pinned[f],
                                 f"{f} grew from {pinned[f]} to {n} bare mkdtemp sites")

    def test_the_pinned_debt_is_real_so_the_table_cannot_be_satisfied_by_an_empty_scan(self) -> None:
        """Anti-vacuity: every pinned file must actually be found by the matcher.

        If this fails because a site was fixed, that is good news — delete the row and the entry, do
        not widen the matcher's blind spot to keep a stale number.
        """
        self.assertGreaterEqual(sum(DEBT_TESTS.values()), 20)
        self.assertGreaterEqual(sum(DEBT_PRODUCTION.values()), 6)
        measured = {f: len(lines) for f, lines in self.sites.items()}
        for f, n in {**DEBT_TESTS, **DEBT_PRODUCTION}.items():
            self.assertTrue((ROOT / f).is_file(), f"{f} in the debt table does not exist")
            self.assertEqual(measured.get(f), n,
                             f"{f}: the debt table says {n}, the tree says {measured.get(f)}")

    def test_the_releaser_and_recovery_tools_exist_for_their_register_citations(self) -> None:
        for tool in ("scripts/maintenance/release_authority_reference_temp_residue.py",
                     "scripts/maintenance/recover_shared_root_original.py",
                     "scripts/audit/outside_root_spill_sweep.py"):
            self.assertTrue((ROOT / tool).is_file(), f"{tool} is cited by the register but missing")


if __name__ == "__main__":
    unittest.main()
