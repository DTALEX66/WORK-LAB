from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
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
            'base_url = "https://user-owned.invalid/v1"\n'
            '\n[mcp_servers.user-owned]\n'
            'command = "safe-placeholder"\n'
            '\n[plugins.user-owned]\n'
            'enabled = true\n'
            '\n[future_settings]\n'
            'opaque = "keep-me"\n',
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
            self.assertEqual(parsed["base_url"], "https://user-owned.invalid/v1")
            self.assertIn("user-owned", parsed["mcp_servers"])
            self.assertTrue(parsed["plugins"]["user-owned"]["enabled"])
            self.assertEqual(parsed["future_settings"]["opaque"], "keep-me")
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
            self.assertEqual(parsed["base_url"], "https://user-owned.invalid/v1")
            self.assertTrue(parsed["plugins"]["user-owned"]["enabled"])
            self.assertEqual(parsed["future_settings"]["opaque"], "keep-me")
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
            self.assertEqual(migrated["phase"], "applied")
            self.assertEqual(len(migrated["managed_skill_names"]), 10)
            self.assertEqual(module.verify_overlay(codex_home, agent_home, ROOT / "codex-assets")["status"], "PASS")
            self.assertEqual(
                module.rollback_overlay(codex_home, agent_home, ROOT / "codex-assets")["status"],
                "ROLLED_BACK",
            )
            self.assertEqual(
                module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")["status"],
                "APPLIED",
            )
            self.assertEqual(module.verify_overlay(codex_home, agent_home, ROOT / "codex-assets")["status"], "PASS")

    def test_legacy_migration_survives_advanced_source_and_dissolved_config_block(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            codex_home, agent_home = self.make_homes(Path(td))
            module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")

            # Simulate the source advancing after the legacy apply.
            tmp_src = Path(td) / "codex-assets-advanced"
            shutil.copytree(ROOT / "codex-assets", tmp_src)
            marker = "\n- advanced source marker for migration regression\n"
            with tmp_src.joinpath("global-guidance.md").open("a", encoding="utf-8") as handle:
                handle.write(marker)

            # Simulate a Codex Desktop rewrite dissolving the managed config block.
            (codex_home / "config.toml").write_text(
                'model_provider = "user-provider"\n'
                'model = "user-model"\n'
                'base_url = "https://user-owned.invalid/v1"\n',
                encoding="utf-8",
            )

            state_path = codex_home / module.STATE_FILE
            legacy = json.loads(state_path.read_text("utf-8"))
            legacy["version"] = 2
            for key in ("phase", "managed_block_hashes", "previous_block_hashes", "previous_target_hashes"):
                legacy.pop(key, None)
            state_path.write_text(json.dumps(legacy), encoding="utf-8")

            plan = module.build_plan(codex_home, agent_home, tmp_src)
            result = module.apply_overlay(codex_home, agent_home, tmp_src)

            self.assertIn("MIGRATE_OWNERSHIP_STATE", [action["action"] for action in plan["actions"]])
            self.assertEqual(result["status"], "APPLIED")
            parsed = tomllib.loads((codex_home / "config.toml").read_text("utf-8"))
            self.assertEqual(parsed["approval_policy"], "on-request")
            self.assertEqual(parsed["sandbox_mode"], "workspace-write")
            self.assertEqual(parsed["project_doc_max_bytes"], 65536)
            guidance = (codex_home / "AGENTS.md").read_text("utf-8")
            self.assertIn("advanced source marker", guidance)
            migrated = json.loads(state_path.read_text("utf-8"))
            self.assertEqual(migrated["version"], module.VERSION)
            self.assertEqual(sorted(migrated["managed_config_fields"]), sorted(module.MANAGED_CONFIG))
            self.assertEqual(module.verify_overlay(codex_home, agent_home, tmp_src)["status"], "PASS")

    def test_legacy_migration_still_blocks_on_edited_managed_block(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            codex_home, agent_home = self.make_homes(Path(td))
            module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")

            # Keep the managed config block but edit a value inside it.
            config_text = (codex_home / "config.toml").read_text("utf-8")
            config_text = config_text.replace('approval_policy = "on-request"', 'approval_policy = "never"')
            (codex_home / "config.toml").write_text(config_text, encoding="utf-8")

            state_path = codex_home / module.STATE_FILE
            legacy = json.loads(state_path.read_text("utf-8"))
            legacy["version"] = 2
            for key in ("phase", "managed_block_hashes", "previous_block_hashes", "previous_target_hashes"):
                legacy.pop(key, None)
            state_path.write_text(json.dumps(legacy), encoding="utf-8")

            with self.assertRaisesRegex(module.ManagedConflict, "managed config block changed after apply"):
                module.build_plan(codex_home, agent_home, ROOT / "codex-assets")

    def test_legacy_migration_blocks_on_unmarked_guidance_block(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            codex_home, agent_home = self.make_homes(Path(td))
            module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")

            # Replace the marked guidance block with unmarked user content.
            (codex_home / "AGENTS.md").write_text(
                "# User guidance\n\nUser-owned paragraph without managed markers.\n",
                encoding="utf-8",
            )

            state_path = codex_home / module.STATE_FILE
            legacy = json.loads(state_path.read_text("utf-8"))
            legacy["version"] = 2
            for key in ("phase", "managed_block_hashes", "previous_block_hashes", "previous_target_hashes"):
                legacy.pop(key, None)
            state_path.write_text(json.dumps(legacy), encoding="utf-8")

            with self.assertRaisesRegex(module.ManagedConflict, "managed guidance block changed after apply"):
                module.build_plan(codex_home, agent_home, ROOT / "codex-assets")

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

    def test_apply_rejects_managed_config_drift_instead_of_repairing_it(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            codex_home, agent_home = self.make_homes(Path(td))
            module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")
            config_path = codex_home / "config.toml"
            config_path.write_text(
                config_path.read_text("utf-8").replace(
                    'sandbox_mode = "workspace-write"',
                    'sandbox_mode = "read-only"',
                ),
                encoding="utf-8",
            )

            with self.assertRaises(module.ManagedConflict):
                module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")

            self.assertEqual(tomllib.loads(config_path.read_text("utf-8"))["sandbox_mode"], "read-only")

    def test_apply_rejects_managed_guidance_drift_instead_of_repairing_it(self) -> None:
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

            with self.assertRaises(module.ManagedConflict):
                module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")

            self.assertIn("another language", guidance_path.read_text("utf-8"))

    def test_rollback_rejects_extra_user_field_inside_managed_config_block(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            codex_home, agent_home = self.make_homes(Path(td))
            module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")
            config_path = codex_home / "config.toml"
            config_path.write_text(
                config_path.read_text("utf-8").replace(
                    module.CONFIG_BEGIN,
                    module.CONFIG_BEGIN + '\npost_apply_user_field = "keep-me"',
                ),
                encoding="utf-8",
            )

            with self.assertRaises(module.ManagedConflict):
                module.rollback_overlay(codex_home, agent_home, ROOT / "codex-assets")

            self.assertEqual(
                tomllib.loads(config_path.read_text("utf-8"))["post_apply_user_field"],
                "keep-me",
            )

    def test_apply_detects_config_change_between_preflight_and_atomic_replace(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            codex_home, agent_home = self.make_homes(Path(td))
            config_path = codex_home / "config.toml"
            original_atomic_write = module._atomic_write
            injected = False

            def racing_atomic_write(path, data, *, expected_current=module.NO_EXPECTATION):
                nonlocal injected
                if path == config_path and not injected:
                    injected = True
                    path.write_text(
                        path.read_text("utf-8").replace("user-provider", "concurrent-provider"),
                        encoding="utf-8",
                    )
                return original_atomic_write(path, data, expected_current=expected_current)

            module._atomic_write = racing_atomic_write
            try:
                with self.assertRaises(module.ManagedConflict):
                    module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")
            finally:
                module._atomic_write = original_atomic_write

            self.assertEqual(
                tomllib.loads(config_path.read_text("utf-8"))["model_provider"],
                "concurrent-provider",
            )

    def test_interrupted_apply_records_recoverable_pending_state(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            codex_home, agent_home = self.make_homes(Path(td))
            guidance_path = codex_home / "AGENTS.md"
            original_atomic_write = module._atomic_write

            def failing_atomic_write(path, data, *, expected_current=module.NO_EXPECTATION):
                if path == guidance_path:
                    raise OSError("simulated interrupted apply")
                return original_atomic_write(path, data, expected_current=expected_current)

            module._atomic_write = failing_atomic_write
            try:
                with self.assertRaises(OSError):
                    module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")
            finally:
                module._atomic_write = original_atomic_write

            state_path = codex_home / module.STATE_FILE
            pending = json.loads(state_path.read_text("utf-8"))
            self.assertEqual(pending["phase"], "applying")

            result = module.rollback_overlay(codex_home, agent_home, ROOT / "codex-assets")

            self.assertEqual(result["status"], "ROLLED_BACK")
            self.assertFalse(state_path.exists())
            parsed = tomllib.loads((codex_home / "config.toml").read_text("utf-8"))
            self.assertEqual(parsed["model_provider"], "user-provider")
            self.assertNotIn("approval_policy", parsed)
            self.assertNotIn(module.GUIDANCE_BEGIN, guidance_path.read_text("utf-8"))

    def test_apply_removes_retired_owned_skill_before_dropping_ownership(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            base = Path(td)
            codex_home, agent_home = self.make_homes(base / "homes")
            source_root = base / "codex-assets"
            shutil.copytree(ROOT / "codex-assets", source_root)
            module.apply_overlay(codex_home, agent_home, source_root)
            retired = "workflow-assistance-windows-development"
            shutil.rmtree(source_root / "skills" / retired)

            result = module.apply_overlay(codex_home, agent_home, source_root)

            self.assertEqual(result["status"], "APPLIED")
            self.assertFalse((agent_home / "skills" / retired).exists())
            state = json.loads((codex_home / module.STATE_FILE).read_text("utf-8"))
            self.assertNotIn(retired, state["managed_skill_names"])

    def test_interrupted_rollback_is_retryable_from_rolling_back_state(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            codex_home, agent_home = self.make_homes(Path(td))
            module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")
            original_rmtree = module.shutil.rmtree
            removed_skills = 0

            def failing_rmtree(path, *args, **kwargs):
                nonlocal removed_skills
                target = Path(path)
                if target.name.startswith("workflow-assistance-"):
                    removed_skills += 1
                    if removed_skills == 2:
                        raise OSError("simulated interrupted rollback")
                return original_rmtree(path, *args, **kwargs)

            module.shutil.rmtree = failing_rmtree
            try:
                with self.assertRaises(OSError):
                    module.rollback_overlay(codex_home, agent_home, ROOT / "codex-assets")
            finally:
                module.shutil.rmtree = original_rmtree

            state_path = codex_home / module.STATE_FILE
            interrupted = json.loads(state_path.read_text("utf-8"))
            self.assertEqual(interrupted["phase"], "rolling_back")

            result = module.rollback_overlay(codex_home, agent_home, ROOT / "codex-assets")

            self.assertEqual(result["status"], "ROLLED_BACK")
            self.assertFalse(state_path.exists())
            self.assertFalse((codex_home / module.RULE_RELATIVE).exists())
            self.assertFalse(list((agent_home / "skills").glob("workflow-assistance-*")))
            parsed = tomllib.loads((codex_home / "config.toml").read_text("utf-8"))
            self.assertEqual(parsed["model_provider"], "user-provider")
            self.assertNotIn("approval_policy", parsed)

    def test_apply_rejects_skill_root_symlink_or_windows_junction(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".hermes/task-runtime/tmp") as td:
            base = Path(td)
            codex_home, agent_home = self.make_homes(base / "homes")
            agent_home.mkdir(parents=True)
            outside = base / "outside"
            outside.mkdir()
            skills_link = agent_home / "skills"
            try:
                if os.name == "nt":
                    result = subprocess.run(
                        ["cmd.exe", "/d", "/c", "mklink", "/J", str(skills_link), str(outside)],
                        text=True,
                        encoding="mbcs",
                        errors="replace",
                        capture_output=True,
                    )
                    if result.returncode != 0:
                        self.skipTest(f"junction creation unavailable: {result.stderr.strip()}")
                else:
                    os.symlink(outside, skills_link, target_is_directory=True)

                with self.assertRaises(module.ManagedConflict):
                    module.apply_overlay(codex_home, agent_home, ROOT / "codex-assets")

                self.assertFalse(list(outside.iterdir()))
                self.assertFalse((codex_home / module.STATE_FILE).exists())
            finally:
                if skills_link.is_symlink():
                    skills_link.unlink()
                elif skills_link.exists():
                    os.rmdir(skills_link)


if __name__ == "__main__":
    unittest.main()
