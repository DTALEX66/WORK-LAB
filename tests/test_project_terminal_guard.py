from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin" / "hermes-project-terminal-guard.py"


def load_module():
    spec = importlib.util.spec_from_file_location("project_terminal_guard", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProjectTerminalGuardTests(unittest.TestCase):
    def make_repo(self) -> Path:
        raw = tempfile.TemporaryDirectory()
        self.addCleanup(raw.cleanup)
        repo = Path(raw.name) / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        return repo

    def payload(self, repo: Path, command: str, *, workdir: str | None = None) -> dict[str, object]:
        return {
            "hook_event_name": "pre_tool_call",
            "tool_name": "terminal",
            "tool_input": {"command": command, **({"workdir": workdir} if workdir is not None else {"workdir": str(repo)})},
            "session_id": "test-session",
        }

    def test_permits_single_project_wrapper_run(self) -> None:
        module = load_module()
        repo = self.make_repo()

        reason = module.validate(self.payload(repo, 'python "$HERMES_HOME/bin/hermes-project-data.py" --project . run -- python -m pytest'))

        self.assertIsNone(reason)

    def test_blocks_raw_terminal_command(self) -> None:
        module = load_module()
        repo = self.make_repo()

        reason = module.validate(self.payload(repo, "python -m pytest"))

        self.assertIn("hermes-project-data.py", reason)

    def test_blocks_wrapper_run_with_external_absolute_output_path(self) -> None:
        module = load_module()
        repo = self.make_repo()

        reason = module.validate(
            self.payload(
                repo,
                'python "$HERMES_HOME/bin/hermes-project-data.py" --project . run -- '
                'python -c "open(\\"C:/outside-task-artifact.txt\\", \\"w\\")"',
            )
        )

        self.assertIn("project", reason)

    def test_blocks_wrapper_run_with_embedded_posix_absolute_path(self) -> None:
        module = load_module()
        repo = self.make_repo()

        for child in (
            'python -c "write(--output=/tmp/outside-task-artifact.txt)"',
            'python -c "write(--output:/tmp/outside-task-artifact.txt)"',
            'python -c "write(/tmp/outside-task-artifact.txt)"',
        ):
            with self.subTest(child=child):
                reason = module.validate(
                    self.payload(
                        repo,
                        'python "$HERMES_HOME/bin/hermes-project-data.py" --project . run -- ' + child,
                    )
                )
                self.assertIn("project", reason)

    def test_blocks_wrapper_run_with_unc_absolute_path(self) -> None:
        module = load_module()
        repo = self.make_repo()

        reason = module.validate(
            self.payload(
                repo,
                r'python "$HERMES_HOME/bin/hermes-project-data.py" --project . run -- '
                r'python --output=\\server\share\outside-task-artifact.txt',
            )
        )

        self.assertIn("project", reason)

    def test_blocks_wrapper_run_with_embedded_unc_absolute_path(self) -> None:
        module = load_module()
        repo = self.make_repo()

        reason = module.validate(
            self.payload(
                repo,
                r'python "$HERMES_HOME/bin/hermes-project-data.py" --project . run -- '
                r'python -c "write(path:\\server\share\outside.txt)"',
            )
        )

        self.assertIn("project", reason)

    def test_blocks_windows_backslash_paths_and_parent_traversal_before_shlex(self) -> None:
        module = load_module()
        repo = self.make_repo()

        for child in (
            r'python -c "open(\"C:\\tmp\\outside-task-artifact.txt\", \"w\")"',
            r'python --dest=C:\\tmp\\outside-task-artifact.txt',
            r'python -c "open(\"..\\outside-task-artifact.txt\", \"w\")"',
            r'python -c "open(\"../outside-task-artifact.txt\", \"w\")"',
        ):
            with self.subTest(child=child):
                reason = module.validate(
                    self.payload(
                        repo,
                        'python "$HERMES_HOME/bin/hermes-project-data.py" --project . run -- ' + child,
                    )
                )
                self.assertIn("project", reason)

    def test_blocks_shell_expansion_that_runs_before_the_wrapper(self) -> None:
        module = load_module()
        repo = self.make_repo()

        for child in (
            r'python -c "open(\"$HOME/outside-task-artifact.txt\", \"w\")"',
            r'python -c "open(\"${TMPDIR}/outside-task-artifact.txt\", \"w\")"',
            r'$(python -c "print(\"unsafe\")") python -m pytest',
            r'`python -c "print(\"unsafe\")"` python -m pytest',
        ):
            with self.subTest(child=child):
                reason = module.validate(
                    self.payload(
                        repo,
                        'python "$HERMES_HOME/bin/hermes-project-data.py" --project . run -- ' + child,
                    )
                )
                self.assertIn("shell expansion", reason)

    def test_blocks_wrapper_prefix_variable_that_is_not_hermes_home(self) -> None:
        module = load_module()
        repo = self.make_repo()

        reason = module.validate(
            self.payload(
                repo,
                '$HERMES_HOME_EVASION python "$HERMES_HOME/bin/hermes-project-data.py" --project . check',
            )
        )

        self.assertIn("shell expansion", reason)

    def test_blocks_single_ampersand_shell_chaining(self) -> None:
        module = load_module()
        repo = self.make_repo()

        reason = module.validate(
            self.payload(
                repo,
                'python "$HERMES_HOME/bin/hermes-project-data.py" --project . run -- python -m pytest & echo unsafe',
            )
        )

        self.assertIn("chaining", reason)

    def test_permits_shell_control_characters_inside_quoted_child_text(self) -> None:
        module = load_module()
        repo = self.make_repo()

        reason = module.validate(
            self.payload(
                repo,
                "python \"$HERMES_HOME/bin/hermes-project-data.py\" --project . run -- "
                "python -c 'print(\"literal; &\")'",
            )
        )

        self.assertIsNone(reason)

    def test_blocks_implicit_or_non_git_workdir(self) -> None:
        module = load_module()
        repo = self.make_repo()

        self.assertIn("explicit", module.validate(self.payload(repo, "echo hi", workdir="")))
        self.assertIn("Git project", module.validate(self.payload(repo, "echo hi", workdir=str(Path(repo.anchor)))))

    def test_blocks_wrong_wrapper_project_and_shell_chaining(self) -> None:
        module = load_module()
        repo = self.make_repo()

        wrong_project = module.validate(self.payload(repo, 'python "$HERMES_HOME/bin/hermes-project-data.py" --project ../other run -- python -m pytest'))
        chained = module.validate(self.payload(repo, 'python "$HERMES_HOME/bin/hermes-project-data.py" --project . run -- python -m pytest && echo unsafe'))

        self.assertIn("--project .", wrong_project)
        self.assertIn("chaining", chained)

    def test_blocks_text_that_only_mentions_the_wrapper(self) -> None:
        module = load_module()
        repo = self.make_repo()

        fake_echo = module.validate(self.payload(repo, "echo hermes-project-data.py --project . check"))
        fake_python = module.validate(self.payload(repo, "python fake.py hermes-project-data.py --project . check"))

        self.assertIn("executable", fake_echo)
        self.assertIn("executable", fake_python)

    def test_blocks_absolute_fake_wrapper_with_the_same_filename(self) -> None:
        module = load_module()
        repo = self.make_repo()
        fake = repo / "hermes-project-data.py"
        fake.write_text("# fake\n", encoding="utf-8")

        reason = module.validate(self.payload(repo, f'python "{fake}" --project . check'))

        self.assertIn("canonical", reason)

    def test_ignores_other_tool_calls(self) -> None:
        module = load_module()

        self.assertIsNone(module.validate({"tool_name": "read_file", "tool_input": {"path": "C:/outside.txt"}}))

    def test_main_outputs_hermes_block_wire_shape(self) -> None:
        module = load_module()
        repo = self.make_repo()
        payload = self.payload(repo, "git status")

        reason = module.validate(payload)
        self.assertTrue(reason)
        self.assertEqual(module.BLOCK_PREFIX, "PROJECT DATA BOUNDARY BLOCKED:")
        self.assertEqual(json.loads(json.dumps({"action": "block", "message": f"{module.BLOCK_PREFIX} {reason}"}))["action"], "block")


if __name__ == "__main__":
    unittest.main()
