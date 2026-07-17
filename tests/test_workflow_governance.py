from __future__ import annotations

import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class WorkflowGovernanceTests(unittest.TestCase):
    def test_portable_config_defaults_to_context7_only(self) -> None:
        config = yaml.safe_load((ROOT / "config/config.yaml").read_text(encoding="utf-8"))
        self.assertEqual(set(config["mcp_servers"]), {"context7"})
        self.assertEqual(
            set(config["plugins"]["enabled"]),
            {"security-guidance", "web/ddgs"},
        )
        non_core = {"spotify", "x_search", "video", "tts"}
        self.assertTrue(non_core.isdisjoint(config["platform_toolsets"]["cli"]))

    def test_sync_uses_repo_skills_as_single_source(self) -> None:
        source = (ROOT / "scripts/workflow/sync_hermes_workflow_assets.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("MERGED_MODEL_SWITCH", source)
        self.assertNotIn("write_text(MERGED_MODEL_SWITCH", source)

    def test_sync_removes_retired_managed_mcps_and_preserves_model(self) -> None:
        script = ROOT / "scripts/workflow/sync_hermes_workflow_assets.py"
        spec = importlib.util.spec_from_file_location("workflow_sync", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            repo = temp / "repo"
            home = temp / "home"
            (repo / "config").mkdir(parents=True)
            home.mkdir()
            (repo / "config/config.yaml").write_text(
                "mcp_servers:\n  context7:\n    command: hermes-npx\n    args: [-y, context7]\n"
                "plugins:\n  enabled: [security-guidance, web/ddgs]\n",
                encoding="utf-8",
            )
            (home / "config.yaml").write_text(
                "model:\n  provider: openai-codex\n  default: gpt-current\n"
                "mcp_servers:\n  public-apis: {}\n  sequential-thinking: {}\n  custom: {}\n"
                "plugins:\n  enabled: [disk-cleanup, google_meet, spotify, custom-plugin]\n",
                encoding="utf-8",
            )

            module.merge_live_config(repo, home, apply=True)
            result = yaml.safe_load((home / "config.yaml").read_text(encoding="utf-8"))
            self.assertEqual(result["model"]["default"], "gpt-current")
            self.assertEqual(set(result["mcp_servers"]), {"context7", "custom"})
            self.assertEqual(
                set(result["plugins"]["enabled"]),
                {"security-guidance", "web/ddgs", "custom-plugin"},
            )

            result["plugins"]["enabled"].append("spotify")
            (home / "config.yaml").write_text(
                yaml.safe_dump(result, sort_keys=False), encoding="utf-8"
            )
            module.merge_live_config(repo, home, apply=True)
            rerun = yaml.safe_load((home / "config.yaml").read_text(encoding="utf-8"))
            self.assertIn("spotify", rerun["plugins"]["enabled"])
            self.assertTrue((home / ".workflow-assistance-state.yaml").exists())

    def test_sync_removes_only_explicitly_retired_managed_skill_assets(self) -> None:
        script = ROOT / "scripts/workflow/sync_hermes_workflow_assets.py"
        spec = importlib.util.spec_from_file_location("workflow_sync_retired", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            retired = [
                "model-switch/references/oauth-credential-sync.md",
                "software-development/windows-development-environment/references/github-credential-extraction.md",
                "software-development/windows-development-environment/references/codex++-proxy-routing.md",
                "software-development/hermes-provider-routing/SKILL.md",
            ]
            for relative in retired:
                target = home / "skills" / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("stale", encoding="utf-8")
            keep = home / "skills/custom-skill/SKILL.md"
            keep.parent.mkdir(parents=True)
            keep.write_text("keep", encoding="utf-8")

            module.remove_retired_managed_assets(home, apply=True)
            self.assertTrue(keep.exists())
            for relative in retired:
                self.assertFalse((home / "skills" / relative).exists(), relative)

    def test_sync_initializes_missing_live_config_from_portable_baseline(self) -> None:
        script = ROOT / "scripts/workflow/sync_hermes_workflow_assets.py"
        spec = importlib.util.spec_from_file_location("workflow_sync_new", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            repo = temp / "repo"
            home = temp / "home"
            (repo / "config").mkdir(parents=True)
            home.mkdir()
            (repo / "config/config.yaml").write_text(
                "model:\n  provider: openai-codex\n  default: gpt-portable\n"
                "platform_toolsets:\n  cli: [terminal, file]\n"
                "mcp_servers:\n  context7:\n    command: hermes-npx\n",
                encoding="utf-8",
            )

            module.merge_live_config(repo, home, apply=True)
            result = yaml.safe_load((home / "config.yaml").read_text(encoding="utf-8"))
            self.assertEqual(result["model"]["default"], "gpt-portable")
            self.assertEqual(result["platform_toolsets"]["cli"], ["terminal", "file"])
            self.assertEqual(set(result["mcp_servers"]), {"context7"})

    def test_setup_does_not_default_enable_optional_capabilities(self) -> None:
        scripts = "\n".join(
            (ROOT / name).read_text(encoding="utf-8") for name in ("setup.sh", "setup.ps1")
        )
        for command in (
            "tools enable x_search",
            "tools enable video",
            "tools enable spotify",
            "plugins enable disk-cleanup",
            "plugins enable google_meet",
            "plugins enable spotify",
        ):
            self.assertNotIn(command, scripts)
        self.assertNotIn("[switch]$DryRun", (ROOT / "setup.ps1").read_text(encoding="utf-8"))
        for name in ("setup.sh", "setup.ps1"):
            setup = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("sync_hermes_workflow_assets.py", setup)
            self.assertIn("--apply", setup)
        self.assertNotIn('cp "$PACK_DIR/config/config.yaml"', (ROOT / "setup.sh").read_text(encoding="utf-8"))
        self.assertNotIn("Copy-Item -Path $configSrc -Destination $configDst -Force", (ROOT / "setup.ps1").read_text(encoding="utf-8"))

    def test_readme_never_extracts_credentials_from_auth_files(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("json.load(open(r'~/.codex/auth.json'))", readme)
        self.assertIn("skills/model-switch/SKILL.md", readme)

    def test_doctor_distinguishes_structural_and_live_checks(self) -> None:
        doctor = (ROOT / "scripts/workflow/hermes_workflow_doctor.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("server-sequential-thinking", doctor)
        self.assertNotIn("public-apis-mcp", doctor)
        self.assertIn("['hermes', 'mcp', 'test', 'context7']", doctor)
        self.assertIn("--live", doctor)
        self.assertIn("structural checks do not prove provider execution", doctor)

        sys.path.insert(0, str(ROOT / "scripts/workflow"))
        try:
            spec = importlib.util.spec_from_file_location(
                "workflow_doctor", ROOT / "scripts/workflow/hermes_workflow_doctor.py"
            )
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            sys.path.pop(0)
        self.assertFalse(module.has_exact_marker("Only reply OK_LIVE", "OK_LIVE"))
        self.assertFalse(module.has_exact_marker("prompt: OK_LIVE", "OK_LIVE"))
        self.assertTrue(module.has_exact_marker("noise\nOK_LIVE\n", "OK_LIVE"))
        leaked = "github_pat_" + "A" * 30 + " npm_" + "B" * 30 + " xoxb-" + "C" * 30
        redacted = module.redact(leaked)
        self.assertNotIn("A" * 30, redacted)
        self.assertNotIn("B" * 30, redacted)
        self.assertNotIn("C" * 30, redacted)

        json_secret = '"access_token": "' + "D" * 30 + '"'
        redacted_json = module.redact(json_secret)
        self.assertNotIn("D" * 30, redacted_json)
        self.assertIn("[REDACTED]", redacted_json)

    def test_windows_skill_does_not_bypass_provider_or_credential_boundaries(self) -> None:
        skill = ROOT / "skills/software-development/windows-development-environment"
        body = (skill / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("hermes config set model.provider", body)
        self.assertNotIn('cp config/config.yaml "$HERMES_HOME/config.yaml"', body)
        self.assertNotIn('cp -r skills/* "$HERMES_HOME/skills/"', body)
        self.assertNotIn("tools enable x_search", body)
        self.assertIn("sync_hermes_workflow_assets.py", body)
        for name in (
            "codex++-proxy-routing.md",
            "provider-network-troubleshooting.md",
            "third-party-proxy-setup.md",
            "credential-audit-and-template.md",
            "github-credential-extraction.md",
        ):
            self.assertFalse((skill / "references" / name).exists(), name)

    def test_portable_skills_do_not_link_to_missing_references(self) -> None:
        for skill in (ROOT / "skills").rglob("SKILL.md"):
            body = skill.read_text(encoding="utf-8")
            references = re.findall(r"references/[A-Za-z0-9._+/-]+\.md", body)
            missing = [ref for ref in references if not (skill.parent / ref).exists()]
            self.assertEqual(missing, [], skill.relative_to(ROOT).as_posix())

    def test_codex_skill_matches_current_noninteractive_boundary(self) -> None:
        body = (ROOT / "skills/autonomous-ai-agents/codex/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("`codex exec`, `codex review`", body)
        self.assertIn("use `pty=false`", body)
        self.assertIn("One writer per checkout", body)
        self.assertNotIn("codex --yolo exec", body)
        self.assertNotIn("exec --full-auto", body)
        self.assertNotIn("background=true, pty=true", body)

    def test_review_alias_has_no_second_commit_or_autofix_pipeline(self) -> None:
        body = (ROOT / "skills/software-development/requesting-code-review/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("agent-workflow-fortress", body)
        self.assertNotIn("git add -A &&", body)
        self.assertNotIn("Auto-fix loop", body)
        self.assertNotIn("git stash", body)
        self.assertNotIn("frozen-review references", body)

    def test_model_routing_has_one_executable_source_of_truth(self) -> None:
        active = [
            ROOT / "config/config.yaml",
            ROOT / "scripts/workflow/switch_model.py",
            ROOT / "scripts/workflow/hermes_workflow_doctor.py",
            ROOT / "skills/model-switch/SKILL.md",
        ]
        combined = "\n".join(path.read_text(encoding="utf-8") for path in active)
        self.assertNotIn("gpt-5.5", combined)
        self.assertIn("from switch_model import DEEPSEEK_MODEL, GPT_MODEL", combined)
        self.assertNotIn("hermes config set model.provider", (active[-1]).read_text(encoding="utf-8"))
        refs = ROOT / "skills/model-switch/references"
        self.assertFalse((refs / "cc-switch-codex-hermes.md").exists())
        self.assertFalse((refs / "oauth-credential-sync.md").exists())
        fortress_ref = ROOT / "skills/software-development/agent-workflow-fortress/references/hermes-provider-mcp-workflow.md"
        self.assertFalse(fortress_ref.exists())

    def test_external_harness_absorption_is_model_and_paid_api_neutral(self) -> None:
        fortress = ROOT / "skills/software-development/agent-workflow-fortress"
        reference = fortress / "references/free-local-agent-harness-absorption.md"
        template = ROOT / "templates/task-tickets/model-neutral-agent-task.md"
        self.assertTrue(reference.exists())
        self.assertTrue(template.exists())

        skill = (fortress / "SKILL.md").read_text(encoding="utf-8")
        reference_body = reference.read_text(encoding="utf-8")
        template_body = template.read_text(encoding="utf-8")
        combined = "\n".join((skill, reference_body, template_body))

        self.assertIn("references/free-local-agent-harness-absorption.md", skill)
        self.assertIn("https://github.com/xai-org/grok-build", reference_body)
        for marker in (
            "Completion contract",
            "Structured run state",
            "Fail-closed safety",
            "Single writer",
            "Exact-tree evidence",
        ):
            self.assertIn(marker, combined)
        for section in (
            "## Completion Contract",
            "## Run State Contract",
            "## Isolation and Permissions",
            "## Verification Evidence",
            "## Cost and Network Boundary",
        ):
            self.assertIn(section, template_body)
        self.assertNotIn(
            "Planning/review blocks edit tools, shell writes, redirection, and write-capable child workers.",
            template_body,
        )
        for enforcement_field in (
            "Enforcement mechanism: `<external sandbox/container/VM plus path and tool policy>`",
            "Tool deny list: `<edit, shell, redirection, child-worker and other denied capabilities>`",
            "Sandbox support verified: `<OS, command, result, or no>`",
            "Negative-control command/result: `<prove shell writes, chained commands and child writes are denied>`",
            "Declaring `plan` or `review` does not enforce read-only behavior.",
            "If enforcement or a negative control is unavailable, the task is `blocked`; do not claim read-only execution.",
            "Policy checks fail closed on errors, timeouts, malformed output, or uninspectable input.",
        ):
            self.assertIn(enforcement_field, template_body)

        forbidden = (
            "XAI_API_KEY",
            "api.x.ai",
            "provider: xai",
            "grok -p",
            "--model",
            "grok-4",
            "grok-build-0",
        )
        for marker in forbidden:
            self.assertNotIn(marker, combined)

    def test_model_neutral_absorption_is_discoverable_and_audited(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        audit = ROOT / "docs/audit/model-neutral-agent-harness-absorption-2026-07.md"
        manifest_path = ROOT / "docs/audit/model-neutral-agent-harness-absorption-2026-07.yaml"
        self.assertIn("templates/task-tickets/model-neutral-agent-task.md", readme)
        self.assertTrue(audit.exists())
        self.assertTrue(manifest_path.exists())

        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(
            manifest["source"]["commit"],
            "98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce",
        )
        self.assertEqual(
            manifest["source"]["source_revision"],
            "124d85bc5dc6e7805560215fcc6d5413944920e1",
        )
        self.assertEqual(manifest["source"]["license"], "Apache-2.0")
        self.assertEqual(manifest["runtime_assets"], [])
        self.assertEqual(
            set(manifest["excluded_capabilities"]),
            {"models", "paid_apis", "providers", "credentials", "external_binaries"},
        )
        local_artifacts = manifest["local_artifacts"]
        self.assertGreaterEqual(len(local_artifacts), 6)
        for relative in local_artifacts:
            self.assertTrue((ROOT / relative).is_file(), relative)
            self.assertFalse(relative.startswith(("config/", "scripts/", "bin/")), relative)
        for evidence in manifest["evidence"]:
            self.assertTrue(evidence["upstream_paths"])
            self.assertTrue(evidence["local_paths"])
            for upstream_path in evidence["upstream_paths"]:
                self.assertFalse(upstream_path.startswith("http"), upstream_path)
            for local_path in evidence["local_paths"]:
                self.assertIn(local_path, local_artifacts)
                self.assertTrue((ROOT / local_path).is_file(), local_path)

        body = audit.read_text(encoding="utf-8")
        self.assertIn("https://github.com/xai-org/grok-build/tree/", body)
        self.assertIn(manifest["source"]["commit"], body)
        self.assertIn(manifest["source"]["source_revision"], body)
        self.assertIn("契约要求，不是运行时隔离证明", body)
        self.assertIn("已吸收", body)
        self.assertIn("明确排除", body)
        self.assertIn("未安装外部执行器", body)
        for marker in ("api.x.ai", "XAI_API_KEY", "grok -p", "--model"):
            self.assertNotIn(marker, body)


if __name__ == "__main__":
    unittest.main()
