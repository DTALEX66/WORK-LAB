"""The authority-index path rule must be able to go red, and must not pass by being empty.

Section 3 of the index sent readers to two directories that have not existed since the 2026-09
convergence, and nothing noticed until a tool was written to look. That is the shape of failure this
file exists for: a navigation surface whose pointers are believed because no one can check them. The
assertions plant the faults rather than trusting that the real index happens to be clean.
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

INDEX = REPO / "docs/current/workflow-assistance/workflow/active-authority-index.md"


def _runtime_root() -> Path:
    """The git-ignored in-boundary runtime root, auto-created: a fresh CI checkout has no .project-local."""
    p = REPO / ".project-local" / "runs"
    p.mkdir(parents=True, exist_ok=True)
    return p


class AuthorityIndexPaths(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="authority-index-paths-", dir=str(_runtime_root())))
        self.addCleanup(shutil.rmtree, self.dir, True)

    def run_tool(self, index: Path) -> tuple[int, str]:
        proc = subprocess.run([sys.executable, str(REPO / "scripts" / "ci"
                                                    / "verify_authority_index_paths.py"),
                               "--index", str(index)],
                              cwd=REPO, capture_output=True)
        return proc.returncode, (proc.stdout + proc.stderr).decode("utf-8", "replace")

    def plant(self, text: str) -> Path:
        copy = self.dir / "planted-index.md"
        copy.write_text(text, encoding="utf-8", newline="\n")
        self.assertEqual(text, copy.read_text(encoding="utf-8"), "the planted bytes were rewritten")
        return copy

    def test_the_real_index_passes_and_reports_a_bounded_count(self) -> None:
        code, out = self.run_tool(INDEX)
        self.assertEqual(0, code, out)
        self.assertIn("broken=0", out)
        self.assertIn("refs=", out)

    def test_a_dead_file_reference_is_caught(self) -> None:
        copy = self.plant("- `docs/current/workflow-assistance/workflow/zz-does-not-exist.md`: x\n")
        code, out = self.run_tool(copy)
        self.assertEqual(1, code, out)
        self.assertIn("is not a file", out)

    def test_a_dead_directory_reference_is_caught(self) -> None:
        copy = self.plant("- 历史归档：`docs/handoffs/` 里的东西\n")
        code, out = self.run_tool(copy)
        self.assertEqual(1, code, out)
        self.assertIn("is not a directory", out)

    def test_an_index_with_no_references_fails_instead_of_passing(self) -> None:
        copy = self.plant("# Index\n\nNo paths here at all.\n")
        code, out = self.run_tool(copy)
        self.assertEqual(1, code, out)
        self.assertIn("refs=0", out)

    def test_a_reference_relative_to_the_index_own_directory_resolves(self) -> None:
        """The real index lives beside the docs it lists, and `../`-style refs must not be false reds."""
        shutil.copyfile(INDEX, self.dir / "mirror-index.md")
        copy = self.dir / "mirror-index.md"
        code, out = self.run_tool(copy)
        self.assertEqual(0, code, f"a copy of the clean index in another directory went red: {out}")

    def test_a_bare_filename_is_not_treated_as_a_path(self) -> None:
        copy = self.plant("- 只解释 `config-ownership.json`，不重复字段表。\n")
        code, out = self.run_tool(copy)
        self.assertIn("refs=0", out)
        self.assertEqual(1, code, out)

    def test_a_declaration_that_now_resolves_is_reported(self) -> None:
        """The allowlist cannot become a hiding place: declaring a live path is itself a fault."""
        rows = [(1, "config/config-ownership.json", "file")]
        original = dict(checker.DECLARED_NON_PATHS)
        try:
            checker.DECLARED_NON_PATHS["config/config-ownership.json"] = "declared while absent"
            broken, stale = checker.verdict(REPO, INDEX, rows)
            self.assertEqual([], broken)
            self.assertEqual([(1, "config/config-ownership.json", "file")], stale)
        finally:
            checker.DECLARED_NON_PATHS.clear()
            checker.DECLARED_NON_PATHS.update(original)

    def test_the_current_index_declares_nothing(self) -> None:
        """Measured on 2026-10-08: every pointer resolves, so an exclusion here needs a new reason."""
        self.assertEqual({}, dict(checker.DECLARED_NON_PATHS))


if __name__ == "__main__":
    unittest.main()
