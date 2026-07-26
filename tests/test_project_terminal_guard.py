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
