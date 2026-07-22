from __future__ import annotations

import subprocess
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from scripts.workflow.run_taskpack_agent import (
    DEFAULT_SKILLS,
    AgentResult,
    HermesAgentBackend,
    RunnerError,
    TaskPackRunner,
    _parse_args,
)


@dataclass
class FakeRepo:
    head_value: str = "base"
    staged_tree_value: str = "tree-base"
    status_value: str = ""
    released: bool = False

    def head(self) -> str:
        return self.head_value

    def head_tree(self) -> str:
        return "tree-base"

    def staged_tree(self) -> str:
        return self.staged_tree_value

    def snapshot(self) -> tuple[str, str]:
        return self.staged_tree_value, self.status_value

    def verify_released(self, baseline_head: str) -> None:
        if baseline_head != "base":
            raise AssertionError(f"unexpected baseline: {baseline_head}")
        self.released = True


class FakeAgent:
    def __init__(self, repo: FakeRepo, decisions: list[str]) -> None:
        self.repo = repo
        self.decisions = iter(decisions)
        self.writer_calls: list[tuple[str | None, str]] = []
        self.review_calls: list[str] = []

    def run_writer(self, prompt: str, *, resume: str | None = None) -> AgentResult:
        self.writer_calls.append((resume, prompt))
        if resume is None:
            self.repo.staged_tree_value = "tree-v1"
            self.repo.status_value = "M  shared/migration.py"
        elif "NO-GO" in prompt:
            self.repo.staged_tree_value = "tree-v2"
        elif "GO" in prompt:
            self.repo.head_value = "released"
            self.repo.status_value = ""
        return AgentResult(stdout="writer complete", stderr="", session_id="session-A")

    def run_reviewer(self, prompt: str) -> str:
        self.review_calls.append(prompt)
        return next(self.decisions)


class TaskPackAgentRunnerTests(unittest.TestCase):
    def test_hermes_backend_resumes_without_agent_timeout(self) -> None:
        calls: list[tuple[list[str], dict[str, object]]] = []

        def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="writer complete\n",
                stderr="\nsession_id: continued-session\n",
            )

        with tempfile.TemporaryDirectory() as raw:
            with patch("scripts.workflow.run_taskpack_agent.shutil.which", return_value="hermes"), patch(
                "scripts.workflow.run_taskpack_agent.subprocess.run", side_effect=fake_run
            ):
                result = HermesAgentBackend(Path(raw), hermes="hermes").run_writer(
                    "continue work", resume="initial-session"
                )

        self.assertEqual(result.session_id, "continued-session")
        self.assertEqual(calls[0][0][calls[0][0].index("--resume") + 1], "initial-session")
        self.assertNotIn("timeout", calls[0][1])

    def test_high_risk_runner_resumes_one_writer_lineage_until_review_go(self) -> None:
        repo = FakeRepo()
        agent = FakeAgent(repo, ["NO-GO\nshared/migration.py:10 missing proof", "GO"])

        TaskPackRunner(repo=repo, agent=agent, max_review_rounds=3, publish=True).run(
            "repair the migration", risk="high"
        )

        self.assertEqual([resume for resume, _ in agent.writer_calls], [None, "session-A", "session-A"])
        self.assertEqual(len(agent.review_calls), 2)
        self.assertIn("tree-v1", agent.review_calls[0])
        self.assertIn("tree-v2", agent.review_calls[1])
        self.assertTrue(repo.released)

    def test_reviewer_cannot_change_frozen_tree(self) -> None:
        repo = FakeRepo()
        agent = FakeAgent(repo, ["GO"])

        def editing_review(_prompt: str) -> str:
            repo.status_value = "M  shared/migration.py\n?? reviewer-note.txt"
            return "GO"

        agent.run_reviewer = editing_review  # type: ignore[method-assign]
        with self.assertRaisesRegex(RunnerError, "reviewer changed"):
            TaskPackRunner(repo=repo, agent=agent).run("repair", risk="high")

    def test_low_risk_runner_uses_configured_release_ref(self) -> None:
        repo = FakeRepo()
        agent = FakeAgent(repo, [])

        TaskPackRunner(repo=repo, agent=agent, release_ref="origin/feat/sleep", publish=True).run(
            "add a pure adapter", risk="low"
        )

        prompt = agent.writer_calls[0][1]
        self.assertIn("origin/feat/sleep", prompt)
        self.assertNotIn("HEAD equal to origin/main", prompt)
        self.assertTrue(repo.released)

    def test_high_risk_runner_uses_configured_release_ref(self) -> None:
        repo = FakeRepo()
        agent = FakeAgent(repo, ["GO"])

        TaskPackRunner(repo=repo, agent=agent, release_ref="origin/feat/sleep", publish=True).run(
            "repair a governed boundary", risk="high"
        )

        release_prompt = agent.writer_calls[-1][1]
        self.assertIn("origin/feat/sleep", release_prompt)
        self.assertNotIn("HEAD equal to origin/main", release_prompt)

    def test_default_runner_stages_without_releasing(self) -> None:
        repo = FakeRepo()
        agent = FakeAgent(repo, [])

        TaskPackRunner(repo=repo, agent=agent).run("stage a bounded task", risk="low")

        self.assertFalse(repo.released)
        self.assertIn("Do not commit, push", agent.writer_calls[0][1])

    def test_default_skills_are_global_not_cognitive_os_specific(self) -> None:
        skills = DEFAULT_SKILLS.split(",")
        self.assertIn("project-data-boundary", skills)
        self.assertNotIn("cognitive-loop-os", skills)

    def test_cli_requires_an_explicit_remote_ref(self) -> None:
        with patch(
            "sys.argv",
            ["run_taskpack_agent.py", "--risk", "low", "--mission", "bounded task"],
        ):
            with self.assertRaises(SystemExit):
                _parse_args()


if __name__ == "__main__":
    unittest.main()
