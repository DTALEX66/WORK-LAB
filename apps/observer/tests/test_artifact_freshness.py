"""Contract tests for the content-keyed artifact freshness gate (ERR-105).

The rule this replaces compared mtimes alone, and on a working copy where git
normalises line endings that made two mistakes at once: a file whose bytes were
untouched but whose mtime moved forged a STALE verdict for a perfectly current
binary, while nothing at all compared frontend/src to frontend/dist, so a binary
embedding a superseded bundle passed as fresh. Both directions have to fail
closed, so both are exercised here.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from u19_webview_e2e import artifact_freshness, content_change_floor  # noqa: E402
from u19_webview_e2e import receipt_verdict  # noqa: E402
from write_artifact_receipt import write_receipt  # noqa: E402

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


class BuildReceiptTests(unittest.TestCase):
    """The receipt closes what content evidence cannot: a rollback to an older
    commit leaves every input matching HEAD, so nothing in the tree evidences
    the change — but the bytes the build consumed are recorded, and they do not
    match afterwards."""

    def fake_build(self, root: Path, obs: Path) -> Path:
        exe_dir = obs / ".tmp-build" / "release"
        exe_dir.mkdir(parents=True, exist_ok=True)
        exe = exe_dir / "app.exe"
        exe.write_bytes(b"MSVC-built-binary-v1\n")
        return exe

    def test_matching_inputs_certify_the_binary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            obs = build_repo(root)
            exe = self.fake_build(root, obs)
            write_receipt(root, obs, exe)

            verdict = receipt_verdict(root, obs, exe)
            self.assertTrue(verdict["usable"])
            self.assertTrue(verdict["matches"])
            self.assertEqual(verdict["changedInputs"], [])
            # Rust sources, the crate manifests, tauri.conf.json, capabilities
            # and the embedded bundle — the compiler's whole input set.
            self.assertGreaterEqual(verdict["inputCount"], 5)
            recorded = json.loads(Path(str(exe) + ".inputs.json").read_text(
                encoding="utf-8"))
            paths = [i["path"] for i in recorded["inputs"]]
            self.assertIn("apps/observer/frontend/dist/index.js", paths)
            self.assertIn("apps/observer/src-tauri/src/lib.rs", paths)

    def test_a_matching_receipt_does_not_outrank_a_stale_bundle(self) -> None:
        """Ordering matters: the receipt attests that the binary consumed the
        dist on disk, which is worthless if that dist is itself older than the
        frontend source that should have rebuilt it."""
        import u19_webview_e2e as u19_module
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            obs = build_repo(root)
            committed = commit_time(root)
            exe_dir = obs / ".tmp-build" / "release"
            exe_dir.mkdir(parents=True)
            exe = exe_dir / "app.exe"
            exe.write_bytes(b"MSVC-built-binary-v1\n")
            write_receipt(root, obs, exe)
            self.assertTrue(receipt_verdict(root, obs, exe)["matches"])

            source = obs / "frontend" / "src" / "App.tsx"
            source.write_text("export const a = 99\n", encoding="utf-8")
            set_mtime(source, committed + 20 * HOUR)

            saved_root, saved_obs = u19_module.ROOT, u19_module.OBS
            saved_env = os.environ.get("CARGO_TARGET_DIR")
            u19_module.ROOT, u19_module.OBS = root, obs
            os.environ["CARGO_TARGET_DIR"] = str(obs / ".tmp-build")
            try:
                chosen, report = u19_module.resolve_app_exe()
            finally:
                u19_module.ROOT, u19_module.OBS = saved_root, saved_obs
                if saved_env is None:
                    os.environ.pop("CARGO_TARGET_DIR", None)
                else:
                    os.environ["CARGO_TARGET_DIR"] = saved_env
            self.assertIsNone(chosen)
            self.assertEqual(report["status"], "STALE_OR_MISSING_BINARY")
            self.assertIn("npm run build", report["reason"])

    def test_a_rollback_that_leaves_no_tree_trace_is_still_seen(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            obs = build_repo(root)
            first = git(root, "rev-parse", "HEAD")
            (obs / "src-tauri" / "src" / "lib.rs").write_text(
                "fn main() { /* the shipped version */ }\n", encoding="utf-8")
            git(root, "add", "-A")
            git(root, "commit", "-q", "-m", "shipped")
            exe = self.fake_build(root, obs)
            write_receipt(root, obs, exe)
            self.assertTrue(receipt_verdict(root, obs, exe)["matches"])

            # Roll the tree back. Every file then matches *some* committed
            # state, mtimes are irrelevant, and `git diff HEAD` shows a change
            # only because HEAD moved — the receipt is what proves the binary
            # was not built from this content.
            git(root, "checkout", first, "--", "apps/observer/src-tauri/src/lib.rs")
            verdict = receipt_verdict(root, obs, exe)
            self.assertTrue(verdict["usable"])
            self.assertFalse(verdict["matches"])
            self.assertEqual(verdict["changedInputs"],
                             ["apps/observer/src-tauri/src/lib.rs"])

    def test_a_receipt_for_other_bytes_attests_to_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            obs = build_repo(root)
            exe = self.fake_build(root, obs)
            write_receipt(root, obs, exe)
            exe.write_bytes(b"someone replaced this binary\n")

            verdict = receipt_verdict(root, obs, exe)
            self.assertFalse(verdict["usable"])
            self.assertIn("different binary", verdict["reason"])

    def test_an_input_added_after_the_build_is_not_certified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            obs = build_repo(root)
            exe = self.fake_build(root, obs)
            write_receipt(root, obs, exe)
            (obs / "frontend" / "dist" / "index.js").write_text(
                "rebuilt without a receipt\n", encoding="utf-8")

            verdict = receipt_verdict(root, obs, exe)
            self.assertFalse(verdict["matches"])
            self.assertIn("apps/observer/frontend/dist/index.js",
                          verdict["changedInputs"])

    def test_absent_receipt_is_absent_not_a_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            obs = build_repo(root)
            exe = self.fake_build(root, obs)
            verdict = receipt_verdict(root, obs, exe)
            self.assertFalse(verdict["present"])
            self.assertFalse(verdict["usable"])
            self.assertFalse(verdict["matches"])

    def test_a_garbled_receipt_is_unusable_not_a_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            obs = build_repo(root)
            exe = self.fake_build(root, obs)
            write_receipt(root, obs, exe)
            Path(str(exe) + ".inputs.json").write_text("{not json", encoding="utf-8")

            verdict = receipt_verdict(root, obs, exe)
            self.assertTrue(verdict["present"])
            self.assertFalse(verdict["usable"])
            self.assertIn("error", verdict)


if __name__ == "__main__":
    unittest.main()
