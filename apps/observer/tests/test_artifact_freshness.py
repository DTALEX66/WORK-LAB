"""Contract tests for the content-keyed artifact freshness gate (ERR-105).

The rule this replaces compared mtimes alone, and on a working copy where git
normalises line endings that made two mistakes at once: a file whose bytes were
untouched but whose mtime moved forged a STALE verdict for a perfectly current
binary, while nothing at all compared frontend/src to frontend/dist, so a binary
embedding a superseded bundle passed as fresh. Both directions have to fail
closed, so both are exercised here.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from u19_webview_e2e import artifact_freshness, content_change_floor  # noqa: E402

HOUR = 3600


def git(root: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=freshness-test",
         "-c", "user.email=freshness@test.invalid", *args],
        capture_output=True, text=True, check=True)
    return done.stdout.strip()


def build_repo(root: Path) -> Path:
    """The real apps/observer layout, minimally, inside a throwaway repo."""
    obs = root / "apps" / "observer"
    (obs / "frontend" / "src").mkdir(parents=True)
    (obs / "src-tauri" / "src").mkdir(parents=True)
    (obs / "frontend" / "index.html").write_text("<html></html>\n", encoding="utf-8")
    (obs / "frontend" / "package.json").write_text("{}\n", encoding="utf-8")
    (obs / "frontend" / "src" / "App.tsx").write_text("export const a = 1\n",
                                                      encoding="utf-8")
    (obs / "src-tauri" / "Cargo.toml").write_text("[package]\n", encoding="utf-8")
    (obs / "src-tauri" / "tauri.conf.json").write_text("{}\n", encoding="utf-8")
    (obs / "src-tauri" / "src" / "lib.rs").write_text("fn main() {}\n",
                                                      encoding="utf-8")
    dist = obs / "frontend" / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>built</html>\n", encoding="utf-8")
    (dist / "index.js").write_text("built\n", encoding="utf-8")
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "inputs")
    return obs


def commit_time(root: Path) -> float:
    return float(git(root, "log", "-1", "--format=%ct"))


def set_mtime(path: Path, when: float) -> None:
    os.utime(path, (when, when))


class ArtifactFreshnessTests(unittest.TestCase):
    def test_touch_without_edit_evidences_no_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            obs = build_repo(root)
            committed = commit_time(root)
            # The bytes stay identical; only the timestamp moves. This is what a
            # CRLF filter pass, a checkout or a stash does to a real working
            # copy, and it must not be able to fail the gate.
            set_mtime(obs / "src-tauri" / "Cargo.toml", committed + 10 * HOUR)
            set_mtime(obs / "frontend" / "src" / "App.tsx", committed + 10 * HOUR)

            floor, detail = content_change_floor(root, obs, ["src-tauri/Cargo.toml"])
            self.assertEqual(floor, 0.0,
                             "a content-free touch must not forge staleness")
            self.assertEqual(detail["changedSinceHead"], [])
            freshness = artifact_freshness(root, obs)
            self.assertFalse(freshness["distSuperseded"])
            self.assertLess(freshness["binaryFloor"], committed + HOUR)

    def test_a_real_edit_counts_even_when_its_mtime_is_back_dated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            obs = build_repo(root)
            committed = commit_time(root)
            edited = obs / "src-tauri" / "src" / "lib.rs"
            edited.write_text("fn main() { /* changed */ }\n", encoding="utf-8")
            set_mtime(edited, committed - 10 * HOUR)

            floor, detail = content_change_floor(root, obs, ["src-tauri/src"])
            self.assertAlmostEqual(floor, committed - 10 * HOUR, delta=2)
            self.assertEqual(detail["changedSinceHead"],
                             ["apps/observer/src-tauri/src/lib.rs"])
            freshness = artifact_freshness(root, obs)
            self.assertAlmostEqual(freshness["rustFloor"], committed - 10 * HOUR,
                                   delta=2)
            self.assertEqual(freshness["rustDetail"]["changedSinceHead"],
                             ["apps/observer/src-tauri/src/lib.rs"])

    def test_an_untracked_new_input_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            obs = build_repo(root)
            committed = commit_time(root)
            new_file = obs / "frontend" / "src" / "Added.tsx"
            new_file.write_text("export const added = true\n", encoding="utf-8")
            set_mtime(new_file, committed + 2 * HOUR)

            floor, detail = content_change_floor(root, obs, ["frontend/src"])
            self.assertAlmostEqual(floor, committed + 2 * HOUR, delta=2)
            self.assertIn("apps/observer/frontend/src/Added.tsx",
                          detail["changedSinceHead"])

    def test_a_deleted_input_fails_the_gate_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            obs = build_repo(root)
            (obs / "src-tauri" / "src" / "lib.rs").unlink()

            before = time.time()
            floor, detail = content_change_floor(root, obs, ["src-tauri/src"])
            self.assertGreaterEqual(floor, before)
            self.assertEqual(detail["deletedInputs"],
                             ["apps/observer/src-tauri/src/lib.rs"])

    def test_dist_older_than_its_source_is_superseded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            obs = build_repo(root)
            committed = commit_time(root)
            source = obs / "frontend" / "src" / "App.tsx"
            source.write_text("export const a = 2\n", encoding="utf-8")
            set_mtime(source, committed + 5 * HOUR)
            set_mtime(obs / "frontend" / "dist" / "index.js", committed + HOUR)

            freshness = artifact_freshness(root, obs)
            self.assertTrue(freshness["distSuperseded"],
                            "a bundle older than the source feeding it must fail")
            # Two different boundaries: the binary must beat dist, and dist is
            # the stage that failed against the source.
            self.assertAlmostEqual(freshness["binaryFloor"], committed + HOUR,
                                   delta=5)
            self.assertAlmostEqual(freshness["frontendSourceFloor"],
                                   committed + 5 * HOUR, delta=5)

    def test_rebuilt_dist_clears_the_stage_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            obs = build_repo(root)
            committed = commit_time(root)
            source = obs / "frontend" / "src" / "App.tsx"
            source.write_text("export const a = 3\n", encoding="utf-8")
            set_mtime(source, committed + 5 * HOUR)
            for name in ("index.js", "index.html"):
                set_mtime(obs / "frontend" / "dist" / name, committed + 6 * HOUR)

            freshness = artifact_freshness(root, obs)
            self.assertFalse(freshness["distSuperseded"])
            self.assertEqual(freshness["basis"], "content-not-mtime")

    def test_an_edited_file_beyond_text_is_not_a_change(self) -> None:
        """The exact defect that blocked this gate twice on 2026-10-06."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            obs = build_repo(root)
            committed = commit_time(root)
            target = obs / "src-tauri" / "Cargo.toml"
            # Rewrite identical bytes and move the timestamp, which is what
            # `git status` reports as modified while `git diff` reports nothing.
            target.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
            set_mtime(target, committed + 10 * HOUR)

            self.assertEqual("", git(root, "diff", "--name-only", "HEAD", "--",
                                     "apps/observer/src-tauri/Cargo.toml"))
            floor, _ = content_change_floor(root, obs, ["src-tauri/Cargo.toml"])
            self.assertEqual(floor, 0.0)


if __name__ == "__main__":
    unittest.main()
