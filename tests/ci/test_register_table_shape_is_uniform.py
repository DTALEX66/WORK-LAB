"""The register's tables must be rectangular, and the checker must not be fooled by escaped pipes.

Nine rows in this register carried a piped shell command inside a backtick span and were therefore read
by markdown as extra columns -- their Status landed under the Evidence heading. Another section declared
a three-column header while ten of its rows carried a Priority column. Both were invisible to every gate
that existed, because the register is a text surface and nothing parsed it as a table.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "ci"))

import verify_register_table_shape as shape  # noqa: E402

REGISTER = REPO / "taskpacks/current/OPEN-TASK-REGISTER.md"


class RealRegister(unittest.TestCase):
    def test_the_live_register_is_rectangular(self) -> None:
        self.assertEqual(0, shape.main([]), "the register has rows that do not match their table header")

    def test_the_register_has_several_tables_and_many_rows(self) -> None:
        bad, tables, rows = shape.scan(REGISTER.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(tables), 3, tables)
        self.assertGreater(rows, 100, f"only {rows} rows judged; the parser lost a table")
        self.assertEqual([], bad)


class ScanJudgement(unittest.TestCase):
    def test_an_extra_column_is_caught(self) -> None:
        text = ("# T\n\n| ID | Status | Evidence |\n|---|---|---|\n"
                "| A | GREEN | ok |\n| B | P1 | DONE | note |\n")
        bad, tables, rows = shape.scan(text)
        self.assertEqual(1, len(bad), bad)
        self.assertEqual("B", bad[0][2])
        self.assertEqual(2, rows)

    def test_a_missing_column_is_caught_too(self) -> None:
        text = "| ID | Priority | Status |\n|---|---|---|\n| A | P0 | OK |\n| B | OK |\n"
        bad, _tables, _rows = shape.scan(text)
        self.assertEqual(1, len(bad), bad)

    def test_an_escaped_pipe_is_content_not_a_column(self) -> None:
        text = ("| ID | Priority | Status |\n|---|---|---|\n"
                "| A | P0 | grep -E 'a\\|b' = 0 |\n")
        bad, _tables, rows = shape.scan(text)
        self.assertEqual([], bad, f"the row is three cells; the backslash-pipe is inside the evidence: {bad}")
        self.assertEqual(1, rows)

    def test_a_separate_table_gets_its_own_width(self) -> None:
        text = ("| ID | Status |\n|---|---|\n| A | ok |\n\nprose\n\n"
                "| ID | Priority | Status |\n|---|---|---|\n| B | P1 | ok |\n")
        bad, tables, rows = shape.scan(text)
        self.assertEqual(2, len(tables), tables)
        self.assertEqual([], bad)
        self.assertEqual(2, rows)

    def test_a_file_with_no_table_fails_instead_of_passing(self) -> None:
        bad, tables, rows = shape.scan("# Notes\n\n- nothing tabular here\n")
        self.assertEqual([], tables)
        self.assertEqual(0, rows)
        self.assertEqual([], bad)


class FailClosedMain(unittest.TestCase):
    def test_a_planted_register_with_a_wide_row_is_red(self) -> None:
        import subprocess
        import tempfile
        root = REPO / ".project-local" / "runs"
        root.mkdir(parents=True, exist_ok=True)
        planted = Path(tempfile.mkdtemp(prefix="register-shape-", dir=str(root))) / "planted.md"
        planted.write_text("| ID | Status |\n|---|---|\n| A | ok |\n| B | P0 | extra |\n",
                           encoding="utf-8", newline="\n")
        try:
            proc = subprocess.run([sys.executable,
                                   str(REPO / "scripts" / "ci" / "verify_register_table_shape.py"),
                                   "--register", str(planted)],
                                  cwd=REPO, capture_output=True)
            out = (proc.stdout + proc.stderr).decode("utf-8", "replace")
            self.assertEqual(1, proc.returncode, out)
            self.assertIn("wrong_width=1", out)
        finally:
            import shutil
            shutil.rmtree(planted.parent, ignore_errors=True)

    def test_a_header_with_no_rows_is_called_out(self) -> None:
        import subprocess
        planted = REPO / ".project-local" / "runs" / "register-no-rows.md"
        planted.parent.mkdir(parents=True, exist_ok=True)
        planted.write_text("| ID | Status |\n|---|---|\n", encoding="utf-8", newline="\n")
        try:
            proc = subprocess.run([sys.executable,
                                   str(REPO / "scripts" / "ci" / "verify_register_table_shape.py"),
                                   "--register", str(planted)],
                                  cwd=REPO, capture_output=True)
            out = (proc.stdout + proc.stderr).decode("utf-8", "replace")
            self.assertEqual(1, proc.returncode, out)
            self.assertIn("rows=0", out)
        finally:
            planted.unlink()


if __name__ == "__main__":
    unittest.main()
