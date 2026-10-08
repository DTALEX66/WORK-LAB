"""The reference-resolution rule must be able to go red, and must not pass on an empty scan.

The rule exists because the authority index sent readers to two directories that have not existed since
the 2026-09 convergence, and because the README's normative 仓库结构 block advertised `bin/`, `skills/`
and `scripts/workflow/` as repository directories. Resolution is against `git ls-files` rather than the
filesystem, so these assertions plant tracked-path sets instead of touching disk -- which is also why the
verdict cannot depend on what a particular machine has in `.project-local/`.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "ci"))

import verify_authority_index_paths as checker  # noqa: E402

INDEX = "docs/current/workflow-assistance/workflow/active-authority-index.md"
README = "docs/current/workflow-assistance-README.md"
# a synthetic tracked set that is enough to answer the references these fixtures write
TRACKED = ["WORK-LAB-AUTHORITY.md", "config/config-ownership.json",
           "docs/current/workflow-assistance-README.md", INDEX,
           "scripts/setup-workflow.sh", "scripts/setup-workflow.ps1",
           "docs/current/workflow-assistance/workflow/managed-software-and-assets.md",
           "packages/client-neutral-core/skills/one/SKILL.md",
           "packages/client-neutral-core/bin/codex"]


class ResolutionAgainstTheTrackedTree(unittest.TestCase):
    def test_a_directory_counts_as_real_only_when_a_tracked_file_sits_under_it(self) -> None:
        self.assertTrue(checker.resolves(TRACKED, "config/", "directory"))
        self.assertFalse(checker.resolves(TRACKED, "scripts/workflow/", "directory"))

    def test_a_file_reference_must_be_tracked_exactly(self) -> None:
        self.assertTrue(checker.resolves(TRACKED, "scripts/setup-workflow.sh", "file"))
        self.assertFalse(checker.resolves(TRACKED, "setup.sh", "file"))

    def test_relative_links_are_folded_before_judging(self) -> None:
        """The README writes `../../.github/workflows/work-lab-gate.yml`, which is a real tracked file."""
        folded = checker.anchored(README, "../../.github/workflows/work-lab-gate.yml")
        self.assertEqual(".github/workflows/work-lab-gate.yml", folded)

    def test_placeholders_are_never_tried(self) -> None:
        for ref in ("<project>/.project-local/runs/", "~/path/x.md", "$CODEX_HOME/AGENTS.md",
                    "docs/workflow/*.md"):
            self.assertTrue(checker.is_placeholder(ref), ref)

    def test_a_declared_prefix_covers_its_children(self) -> None:
        self.assertEqual(".project-local/", checker.declared(".project-local/artifacts/"))
        self.assertIsNone(checker.declared("scripts/workflow/"))


class SurfaceChecks(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="reference-paths-", dir=str(_runtime_root())))
        self.addCleanup(shutil.rmtree, self.dir, True)

    def test_a_dead_directory_in_a_fenced_map_is_caught(self) -> None:
        """The 仓库结构 block is written without backticks; a backtick-only reader would call it clean."""
        text = "```text\nbin/                 wrapper\nconfig/              baseline\n```\n"
        rows, broken, stale = checker.check(self.dir_parent(), TRACKED, self.write("map.md", text))
        self.assertEqual(1, len(broken), f"expected bin/ to fire, got {broken}")
        self.assertEqual("bin/", broken[0][1])
        self.assertEqual([], stale)

    def test_a_dead_backticked_file_is_caught_and_a_declared_one_is_not(self) -> None:
        text = ("- `scripts/workflow/gone.py`: x\n"
                "- `.project-local/artifacts/`: declared as the untracked evidence root\n")
        _rows, broken, _stale = checker.check(self.dir_parent(), TRACKED, self.write("refs.md", text))
        self.assertEqual(["scripts/workflow/gone.py"], [row[1] for row in broken])

    def test_a_declaration_whose_path_becomes_tracked_is_stale(self) -> None:
        rows, broken, stale = checker.check(
            self.dir_parent(), [".project-local/runs/x.json"],
            self.write("decl.md", "- `.project-local/artifacts/`: x\n"))
        self.assertEqual([], broken)
        self.assertEqual(1, len(stale), f"a live path declared as non-repo must be reported: {rows}")

    def test_a_surface_with_no_references_fails_instead_of_passing(self) -> None:
        _rows, broken, _stale = checker.check(self.dir_parent(), TRACKED,
                                              self.write("empty.md", "# Title\n\nprose only\n"))
        self.assertEqual([], broken, "check() has nothing to judge; main() must call that a failure")

    def dir_parent(self) -> Path:
        return self.dir

    def write(self, name: str, text: str) -> str:
        (self.dir / name).write_text(text, encoding="utf-8", newline="\n")
        self.assertEqual(text, (self.dir / name).read_text(encoding="utf-8"))
        return name


def _runtime_root() -> Path:
    p = REPO / ".project-local" / "runs"
    p.mkdir(parents=True, exist_ok=True)
    return p


class RealSurfaces(unittest.TestCase):
    def run_tool(self, *extra: str) -> tuple[int, str]:
        proc = subprocess.run([sys.executable, str(REPO / "scripts" / "ci"
                                                    / "verify_authority_index_paths.py"), *extra],
                              cwd=REPO, capture_output=True)
        return proc.returncode, (proc.stdout + proc.stderr).decode("utf-8", "replace")

    def test_every_default_surface_is_named_and_resolves(self) -> None:
        code, out = self.run_tool()
        self.assertEqual(0, code, out)
        for target in checker.DEFAULT_TARGETS:
            self.assertIn(f"target={target} refs=", out, f"{target} is not judged by the default run")
        self.assertIn("broken=0", out)
        self.assertIn(f"targets={len(checker.DEFAULT_TARGETS)}", out)

    def test_each_surface_yields_references_so_none_is_guarded_in_name_only(self) -> None:
        tracked = checker.tracked_paths(REPO)
        for target in checker.DEFAULT_TARGETS:
            rows, broken, stale = checker.check(REPO, tracked, target)
            self.assertGreater(len(rows), 0, f"{target} yields no references at all")
            self.assertEqual([], broken, f"{target} has unresolved references")
            self.assertEqual([], stale, f"{target} has a stale declaration")

    def test_a_backticked_term_with_a_slash_is_not_a_path(self) -> None:
        """`GUI/TUI` in the troubleshooting doc is a mode pair, not a missing file."""
        self.assertFalse(checker.looks_like_path("GUI/TUI"))
        self.assertTrue(checker.looks_like_path("docs/current/x.md"))

    def test_the_root_absolute_authority_pointer_is_still_covered(self) -> None:
        """/WORK-LAB-AUTHORITY.md is the top authority; excluding it would be a silent blind spot."""
        self.assertTrue(checker.looks_like_path("/WORK-LAB-AUTHORITY.md"))
        index = (REPO / INDEX).read_text(encoding="utf-8")
        self.assertIn("/WORK-LAB-AUTHORITY.md", [row[1] for row in checker.references(index)])

    def test_only_the_untracked_runtime_root_is_declared(self) -> None:
        """Measured 2026-10-08: everything else resolves, so a new declaration needs its own reason."""
        self.assertEqual({".project-local/"}, set(checker.DECLARED_NON_PATHS))

    def test_the_tool_refuses_an_empty_tracked_set(self) -> None:
        """A checker that can resolve nothing must not report a clean tree."""
        original = checker.tracked_paths
        try:
            checker.tracked_paths = lambda root: []
            code = checker.main([])
        finally:
            checker.tracked_paths = original
        self.assertEqual(1, code)

    def test_git_ls_files_returns_a_usable_set(self) -> None:
        tracked = checker.tracked_paths(REPO)
        self.assertGreater(len(tracked), 1000, f"only {len(tracked)} tracked paths; suspicious")
        self.assertIn("scripts/setup-workflow.sh", tracked)


if __name__ == "__main__":
    unittest.main()
