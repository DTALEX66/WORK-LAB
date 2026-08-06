from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/workflow/sync_hermes_workflow_assets.py"


def load_module():
    spec = importlib.util.spec_from_file_location("workflow_sync_action_plan", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_isolated_roots(raw: str) -> tuple[Path, Path]:
    base = Path(raw)
    repo = base / "repo"
    home = base / "hermes-home"
    shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(".hermes", "__pycache__"))
    home.mkdir()
    return repo, home


class ActionPlanSyncTests(unittest.TestCase):
    def test_sync_builds_exact_plan_without_writing_home(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as raw:
            repo, home = make_isolated_roots(raw)
            plan = module.build_action_plan(repo, home)
            self.assertEqual(plan["schema_version"], "workflow/action-plan/v1")
            self.assertEqual(plan["status"], "WAITING_APPROVAL")
            self.assertTrue(plan["approval"]["approval_required"])
            self.assertTrue(plan["rollback"]["available"])
            targets = {step["target"] for step in plan["steps"]}
            self.assertIn("SOUL.md", targets)
            self.assertIn(".env.template", targets)
            self.assertEqual(plan["config"]["operation"], "skip_mixed_ownership")
            self.assertNotIn("sha256", plan["config"]["before"])
            self.assertFalse(any(home.iterdir()))

    def test_apply_requires_explicit_approval(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo, home = make_isolated_roots(raw)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--repo", str(repo), "--home", str(home), "--apply"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("ACTION_PLAN_BLOCKED", result.stdout)
            self.assertFalse(any(home.iterdir()))

    def test_approved_apply_reads_back_the_planned_state(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo, home = make_isolated_roots(raw)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--repo", str(repo), "--home", str(home), "--apply", "--approved"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("ACTION_PLAN_READBACK_PASS", result.stdout)
            self.assertTrue((home / "SOUL.md").is_file())

    def test_approved_apply_does_not_read_or_replace_live_config(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as raw:
            repo, home = make_isolated_roots(raw)
            live_config = home / "config.yaml"
            original = (
                "model:\n  provider: user-provider\n  default: user-model\n"
                "mcp_servers:\n  user_mcp:\n    command: user-command\n"
                "display:\n  language: en\n  skin: stock\n"
                "  busy_input_mode: immediate\nplugins:\n"
                "  enabled: [user-plugin]\nplatform_toolsets:\n  cli: [terminal]\n"
            )
            live_config.write_text(original, encoding="utf-8")
            module.deploy_portable(
                repo,
                home,
                apply=True,
                include_backup=False,
                allow_project_runtime_home=True,
            )
            self.assertEqual(live_config.read_text(encoding="utf-8"), original)
            self.assertFalse((home / ".workflow-assistance-state.yaml").exists())


    def test_readback_rejects_source_mutation_after_plan(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as raw:
            repo, home = make_isolated_roots(raw)
            plan = module.build_action_plan(repo, home)
            soul = repo / "config/SOUL.md"
            soul.write_text(soul.read_text(encoding="utf-8") + "\nmutation-after-plan\n", encoding="utf-8")
            module.deploy_portable(
                repo,
                home,
                apply=True,
                include_backup=False,
                allow_project_runtime_home=True,
            )
            with self.assertRaisesRegex(RuntimeError, "SOUL.md"):
                module.verify_action_plan_readback(plan, repo, home)

    def test_plan_output_rejects_external_path(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo, home = make_isolated_roots(raw)
            output = Path(raw) / "outside.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--repo", str(repo), "--home", str(home), "--plan-json", str(output)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must stay inside", result.stdout + result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
