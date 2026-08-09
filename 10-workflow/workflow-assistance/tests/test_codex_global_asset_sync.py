from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/workflow/sync_codex_global_assets.py"
spec = importlib.util.spec_from_file_location("sync_codex_global_assets", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class CodexGlobalAssetSyncTests(unittest.TestCase):
    def make_homes(self, base: Path) -> tuple[Path, Path]:
        codex_home = base / ".codex"
        agent_home = base / ".agents"
        codex_home.mkdir(parents=True)
        (codex_home / "config.toml").write_text(
            'model_provider = "user-provider"\n'
            'model = "user-model"\n'
            '\n[mcp_servers.user-owned]\n'
            'command = "safe-placeholder"\n',
            encoding="utf-8",
        )
        (codex_home / "AGENTS.md").write_text(
            "# User guidance\n\nKeep my existing preference.\n", encoding="utf-8"
        )
        return codex_home, agent_home

    def test_apply_preserves_user_config_and_installs_owned_assets(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            codex_home, agent_home = self.make_homes(Path(td))

            result = module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")

            self.assertEqual(result["status"], "APPLIED")
            parsed = tomllib.loads((codex_home / "config.toml").read_text("utf-8"))
            self.assertEqual(parsed["model_provider"], "user-provider")
            self.assertEqual(parsed["model"], "user-model")
            self.assertIn("user-owned", parsed["mcp_servers"])
            self.assertEqual(parsed["approval_policy"], "on-request")
            self.assertEqual(parsed["sandbox_mode"], "workspace-write")
            self.assertEqual(parsed["project_doc_max_bytes"], 65536)
            guidance = (codex_home / "AGENTS.md").read_text("utf-8")
            self.assertIn("Keep my existing preference.", guidance)
            self.assertEqual(guidance.count(module.GUIDANCE_BEGIN), 1)
            self.assertTrue((codex_home / "rules/workflow-assistance.rules").is_file())
            installed = sorted((agent_home / "skills").glob("workflow-assistance-*/SKILL.md"))
            self.assertGreaterEqual(len(installed), 6)
            self.assertEqual(module.verify_overlay(codex_home, agent_home, ROOT / "codex-assets")["status"], "PASS")

    def test_apply_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            codex_home, agent_home = self.make_homes(Path(td))
            module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")
            first = {
                "config": (codex_home / "config.toml").read_bytes(),
                "guidance": (codex_home / "AGENTS.md").read_bytes(),
            }

            result = module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")

            self.assertEqual(result["status"], "NO_CHANGE")
            self.assertEqual((codex_home / "config.toml").read_bytes(), first["config"])
            self.assertEqual((codex_home / "AGENTS.md").read_bytes(), first["guidance"])

    def test_conflicting_skill_fails_before_writes(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            codex_home, agent_home = self.make_homes(Path(td))
            conflict = agent_home / "skills/workflow-assistance-safe-project-execution/SKILL.md"
            conflict.parent.mkdir(parents=True)
            conflict.write_text("user-owned conflict", encoding="utf-8")
            original_config = (codex_home / "config.toml").read_bytes()
            original_guidance = (codex_home / "AGENTS.md").read_bytes()

            with self.assertRaises(module.ManagedConflict):
                module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")

            self.assertEqual((codex_home / "config.toml").read_bytes(), original_config)
            self.assertEqual((codex_home / "AGENTS.md").read_bytes(), original_guidance)
            self.assertEqual(conflict.read_text("utf-8"), "user-owned conflict")

    def test_rollback_removes_only_managed_overlay(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            codex_home, agent_home = self.make_homes(Path(td))
            module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")

            result = module.rollback_overlay(codex_home, agent_home, ROOT / "codex-assets")

            self.assertEqual(result["status"], "ROLLED_BACK")
            parsed = tomllib.loads((codex_home / "config.toml").read_text("utf-8"))
            self.assertEqual(parsed["model_provider"], "user-provider")
            self.assertEqual(parsed["model"], "user-model")
            self.assertNotIn("approval_policy", parsed)
            self.assertNotIn("sandbox_mode", parsed)
            self.assertNotIn("project_doc_max_bytes", parsed)
            guidance = (codex_home / "AGENTS.md").read_text("utf-8")
            self.assertIn("Keep my existing preference.", guidance)
            self.assertNotIn(module.GUIDANCE_BEGIN, guidance)
            self.assertFalse((codex_home / "rules/workflow-assistance.rules").exists())
            self.assertFalse(list((agent_home / "skills").glob("workflow-assistance-*")))

    def test_plan_never_manages_user_routing_or_mcp(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            codex_home, agent_home = self.make_homes(Path(td))

            plan = module.build_plan(codex_home, agent_home, ROOT / "codex-assets")

            managed_fields = set(plan["managed_config_fields"])
            self.assertEqual(
                managed_fields,
                {"approval_policy", "sandbox_mode", "project_doc_max_bytes"},
            )
            rendered = str(plan).lower()
            self.assertNotIn("model_provider", managed_fields)
            self.assertNotIn("mcp_servers", managed_fields)
            self.assertNotIn("safe-placeholder", rendered)

    def test_legacy_state_is_migrated_without_replacing_owned_assets(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            codex_home, agent_home = self.make_homes(Path(td))
            module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")
            state_path = codex_home / module.STATE_FILE
            legacy = json.loads(state_path.read_text("utf-8"))
            legacy["version"] = 1
            legacy.pop("managed_skill_names", None)
            state_path.write_text(json.dumps(legacy), encoding="utf-8")

            plan = module.build_plan(codex_home, agent_home, ROOT / "codex-assets")
            result = module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")

            self.assertIn("MIGRATE_OWNERSHIP_STATE", [action["action"] for action in plan["actions"]])
            self.assertEqual(result["status"], "APPLIED")
            migrated = json.loads(state_path.read_text("utf-8"))
            self.assertEqual(migrated["version"], module.VERSION)
            self.assertEqual(len(migrated["managed_skill_names"]), 8)
            self.assertEqual(module.verify_overlay(codex_home, agent_home, ROOT / "codex-assets")["status"], "PASS")

    def test_verify_rejects_modified_guidance_block(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            codex_home, agent_home = self.make_homes(Path(td))
            module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")
            guidance_path = codex_home / "AGENTS.md"
            guidance_path.write_text(
                guidance_path.read_text("utf-8").replace(
                    "Communicate with the user in Chinese",
                    "Communicate with the user in another language",
                ),
                encoding="utf-8",
            )

            result = module.verify_overlay(codex_home, agent_home, ROOT / "codex-assets")

            self.assertEqual(result["status"], "FAIL")
            self.assertIn("guidance_drift", result["issues"])

    def test_rollback_without_state_never_deletes_managed_looking_assets(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            codex_home, agent_home = self.make_homes(Path(td))
            module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")
            state_path = codex_home / module.STATE_FILE
            state_path.unlink()
            rule_path = codex_home / module.RULE_RELATIVE
            skill_path = agent_home / "skills/workflow-assistance-safe-project-execution/SKILL.md"

            with self.assertRaises(module.ManagedConflict):
                module.rollback_overlay(codex_home, agent_home, ROOT / "codex-assets")

            self.assertTrue(rule_path.exists())
            self.assertTrue(skill_path.exists())
            self.assertIn(module.GUIDANCE_BEGIN, (codex_home / "AGENTS.md").read_text("utf-8"))

    def test_exact_preexisting_skill_is_not_silently_adopted(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            codex_home, agent_home = self.make_homes(Path(td))
            source = ROOT / "codex-assets/skills/workflow-assistance-safe-project-execution"
            target = agent_home / "skills/workflow-assistance-safe-project-execution"
            target.parent.mkdir(parents=True)
            shutil.copytree(source, target)

            with self.assertRaises(module.ManagedConflict):
                module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")

            self.assertEqual((target / "SKILL.md").read_bytes(), (source / "SKILL.md").read_bytes())


if __name__ == "__main__":
    unittest.main()
