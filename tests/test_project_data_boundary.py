from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin" / "hermes-project-data.py"


def load_module():
    spec = importlib.util.spec_from_file_location("project_data_boundary", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProjectDataBoundaryTests(unittest.TestCase):
    def make_repo(self, *, ignored: bool) -> Path:
        raw = tempfile.TemporaryDirectory()
        self.addCleanup(raw.cleanup)
        root = Path(raw.name) / "repo"
        root.mkdir()
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        if ignored:
            (root / ".gitignore").write_text(".hermes/\n", encoding="utf-8")
        return root

    def test_prepare_scopes_all_standard_task_output_roots_to_ignored_project_directory(self) -> None:
        module = load_module()
        repo = self.make_repo(ignored=True)

        layout = module.prepare_layout(repo)

        # Git may canonicalize Windows 8.3 aliases (for example RUNNER~1) to
        # the long user-directory form. Compare all contained outputs against
        # the resolved Git root returned by the runtime boundary itself.
        project_root = layout.project_root
        self.assertEqual(project_root, module.discover_project_root(repo))
        for path in layout.paths.values():
            self.assertTrue(path.is_dir(), path)
            self.assertTrue(path.resolve().is_relative_to(project_root), path)
        self.assertTrue(layout.paths["tmp"].is_relative_to(project_root / ".hermes" / "task-runtime"))
        self.assertEqual(layout.env["TMP"], str(layout.paths["tmp"]))
        self.assertEqual(layout.env["TEMP"], str(layout.paths["tmp"]))
        self.assertEqual(layout.env["TMPDIR"], str(layout.paths["tmp"]))
        self.assertEqual(layout.env["PIP_CACHE_DIR"], str(layout.paths["pip-cache"]))
        self.assertEqual(layout.env["PYTHONPYCACHEPREFIX"], str(layout.paths["pycache"]))
        self.assertEqual(layout.env["UV_CACHE_DIR"], str(layout.paths["cache"] / "uv"))
        self.assertEqual(layout.env["NPM_CONFIG_CACHE"], str(layout.paths["cache"] / "npm"))
        self.assertEqual(layout.env["HERMES_KANBAN_HOME"], str(project_root / ".hermes"))

    def test_prepare_fails_closed_when_project_runtime_root_is_not_git_ignored(self) -> None:
        module = load_module()
        repo = self.make_repo(ignored=False)

        with self.assertRaisesRegex(module.ProjectDataBoundaryError, "git-ignored"):
            module.prepare_layout(repo)

    def test_exec_receives_project_local_temp_and_cache_environment(self) -> None:
        module = load_module()
        repo = self.make_repo(ignored=True)
        layout = module.prepare_layout(repo)
        command = [
            sys.executable,
            "-c",
            "import json, os; print(json.dumps({k: os.environ[k] for k in ['TMP','TEMP','TMPDIR','PIP_CACHE_DIR','PYTHONPYCACHEPREFIX']}))",
        ]

        result = module.run_command(layout, command)

        observed = json.loads(result.stdout)
        self.assertEqual(observed, {key: layout.env[key] for key in observed})

    def test_windows_long_python_inline_command_is_materialized_inside_project_runtime(self) -> None:
        module = load_module()
        repo = self.make_repo(ignored=True)
        layout = module.prepare_layout(repo)
        command = [sys.executable, "-c", "print('ok')\n" + "# padding\n" * 4000]

        prepared = module.prepare_command(layout, command, windows=True, limit=1000)

        self.assertEqual(prepared[0], sys.executable)
        self.assertTrue(Path(prepared[1]).is_relative_to(layout.paths["tmp"]))
        self.assertTrue(Path(prepared[1]).is_file())
        self.assertEqual(module.run_command(layout, command, windows=True, limit=1000).stdout.strip(), "ok")

    def test_windows_long_non_python_command_fails_with_response_file_guidance(self) -> None:
        module = load_module()
        repo = self.make_repo(ignored=True)
        layout = module.prepare_layout(repo)

        with self.assertRaisesRegex(module.ProjectDataBoundaryError, "response file"):
            module.prepare_command(layout, ["tool", "x" * 2000], windows=True, limit=1000)

    def test_init_policy_covers_native_kanban_without_touching_source_files(self) -> None:
        module = load_module()
        repo = self.make_repo(ignored=True)
        layout = module.prepare_layout(repo)

        policy = module.write_task_data_policy(layout)

        self.assertEqual(policy, layout.project_root / ".hermes" / "TASK_DATA_POLICY.md")
        content = policy.read_text(encoding="utf-8")
        self.assertIn("HERMES_KANBAN_HOME", content)
        self.assertIn("global Hermes home", content)

    def test_cleanup_removes_transient_runtime_data_but_preserves_cache_by_default(self) -> None:
        module = load_module()
        repo = self.make_repo(ignored=True)
        layout = module.prepare_layout(repo)
        transient = layout.paths["tmp"] / "generated.tmp"
        cache = layout.paths["cache"] / "tool-cache.bin"
        transient.write_bytes(b"temporary")
        cache.write_bytes(b"cache")

        removed = module.cleanup_runtime(layout)

        self.assertEqual(removed["tmp"], len(b"temporary"))
        self.assertFalse(transient.exists())
        self.assertTrue(cache.exists())
        self.assertTrue(layout.paths["tmp"].is_dir())

    def test_cleanup_all_regenerable_also_removes_tool_cache(self) -> None:
        module = load_module()
        repo = self.make_repo(ignored=True)
        layout = module.prepare_layout(repo)
        cache = layout.paths["cache"] / "tool-cache.bin"
        pip_cache = layout.paths["pip-cache"] / "wheel.bin"
        cache.write_bytes(b"cache")
        pip_cache.write_bytes(b"wheel")

        removed = module.cleanup_runtime(layout, include_caches=True)

        self.assertEqual(removed["cache"], len(b"cache"))
        self.assertEqual(removed["pip-cache"], len(b"wheel"))
        self.assertFalse(cache.exists())
        self.assertFalse(pip_cache.exists())

    def test_rejects_any_explicit_output_path_outside_the_project(self) -> None:
        module = load_module()
        repo = self.make_repo(ignored=True)

        with self.assertRaisesRegex(module.ProjectDataBoundaryError, "escapes project root"):
            module.require_contained(repo, repo.parent / "outside")


if __name__ == "__main__":
    unittest.main()
