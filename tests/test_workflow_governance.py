from __future__ import annotations

import importlib.util
import json
import re
import subprocess
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
        self.assertEqual(config["display"]["busy_input_mode"], "queue")
        non_core = {"spotify", "x_search", "video", "tts"}
        self.assertTrue(non_core.isdisjoint(config["platform_toolsets"]["cli"]))

    def test_portable_config_has_documented_kimi_speed_lanes_and_aliases(self) -> None:
        config = yaml.safe_load((ROOT / "config/config.yaml").read_text(encoding="utf-8"))
        lanes = config["model_picker"]["custom_lanes"]
        self.assertTrue(lanes["enabled"])
        kimi = next(lane for lane in lanes["lanes"] if lane["label"] == "KIMI 系列")
        self.assertEqual(kimi["provider"], "kimi-coding")
        self.assertEqual(
            kimi["models"][:3],
            ["kimi-k3", "kimi-k2.7-code-highspeed", "kimi-k2.7-code"],
        )
        quick = config["quick_commands"]
        self.assertEqual(quick["切换kimi"]["target"], "/model kimi-k3 --provider kimi-coding")
        self.assertEqual(quick["切换kimi稳"]["target"], "/model kimi-k3 --provider kimi-coding")
        self.assertEqual(
            quick["切换kimi快"]["target"],
            "/model kimi-k2.7-code --provider kimi-coding",
        )
        self.assertEqual(
            quick["切换kimi极速"]["target"],
            "/model kimi-k2.7-code-highspeed --provider kimi-coding",
        )
        self.assertTrue(all(spec["type"] == "alias" for spec in quick.values()))

    def test_readme_documents_kimi_speed_lane_commands_without_auto_switching(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for command in (
            "python scripts/workflow/switch_model.py kimi       # Kimi K3",
            "python scripts/workflow/switch_model.py kimi-fast  # Kimi K2.7 Code",
            "python scripts/workflow/switch_model.py kimi-turbo # Kimi K2.7 Code HighSpeed",
        ):
            self.assertIn(command, readme)
        self.assertIn("不会自动更改当前会话", readme)
        self.assertIn("`/reset`", readme)

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
                "plugins:\n  enabled: [security-guidance, web/ddgs]\n"
                "display:\n  busy_input_mode: queue\n  skin: portable\n"
                "model_picker:\n  custom_lanes:\n    enabled: true\n    lanes: []\n"
                "quick_commands:\n  portable: {type: alias, target: /model kimi-k3 --provider kimi-coding}\n",
                encoding="utf-8",
            )
            (home / "config.yaml").write_text(
                "model:\n  provider: openai-codex\n  default: gpt-current\n"
                "mcp_servers:\n  public-apis: {}\n  sequential-thinking: {}\n  custom: {}\n"
                "plugins:\n  enabled: [disk-cleanup, google_meet, spotify, custom-plugin]\n"
                "display:\n  busy_input_mode: interrupt\n  skin: live\n"
                "model_picker:\n  custom_lanes:\n    enabled: false\n  local_picker_flag: true\n"
                "quick_commands:\n  custom: {type: alias, target: /help}\n",
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
            self.assertEqual(result["display"]["busy_input_mode"], "queue")
            self.assertEqual(result["display"]["skin"], "live")
            self.assertTrue(result["model_picker"]["custom_lanes"]["enabled"])
            self.assertTrue(result["model_picker"]["local_picker_flag"])
            self.assertEqual(result["quick_commands"]["portable"]["type"], "alias")
            self.assertEqual(result["quick_commands"]["custom"]["target"], "/help")

            result["plugins"]["enabled"].append("spotify")
            (home / "config.yaml").write_text(
                yaml.safe_dump(result, sort_keys=False), encoding="utf-8"
            )
            module.merge_live_config(repo, home, apply=True)
            rerun = yaml.safe_load((home / "config.yaml").read_text(encoding="utf-8"))
            self.assertIn("spotify", rerun["plugins"]["enabled"])
            self.assertEqual(rerun["display"]["busy_input_mode"], "queue")
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

    def test_readme_documents_the_complete_current_feature_surface(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for heading in (
            "## 项目定位",
            "## 功能总览",
            "## Portable 部署与安全同步",
            "## 模型切换与路由诊断",
            "## Codex 编码执行器",
            "## MCP 与 Hermes 原生工具",
            "## Agent 工作流治理",
            "## Skills 能力库",
            "## 安全与隐私",
            "## 模板、文档与审计",
            "## 测试与持续集成",
            "## 使用边界",
        ):
            self.assertIn(heading, readme)
        for command_or_path in (
            "scripts/workflow/sync_hermes_workflow_assets.py",
            "scripts/workflow/build_context_pack.py",
            "scripts/workflow/mcp_candidate_audit.py",
            "scripts/workflow/run_quality_gate.py",
            "scripts/workflow/switch_model.py",
            "scripts/workflow/hermes_workflow_doctor.py",
            "scripts/security/scan_agent_rules.py",
            "Justfile",
            "templates/task-tickets/model-neutral-agent-task.md",
            "templates/evals/agent-behavior-smoke.yaml",
            "templates/ui/skin-presets.yaml",
            "templates/windows-terminal/catppuccin-mocha.json",
            "docs/audit/model-neutral-agent-harness-absorption-2026-07.yaml",
            "hermes mcp test context7",
            "git write-tree",
            "--live",
        ):
            self.assertIn(command_or_path, readme)
        for skill in (ROOT / "skills").rglob("SKILL.md"):
            self.assertIn(skill.parent.name, readme, skill.relative_to(ROOT).as_posix())
        for template in (ROOT / "templates").rglob("*.md"):
            self.assertIn(template.name, readme, template.relative_to(ROOT).as_posix())
        for document in (ROOT / "docs").rglob("*"):
            if document.is_file() and document.suffix in {".md", ".yaml"}:
                self.assertIn(document.relative_to(ROOT).as_posix(), readme)
        config = yaml.safe_load((ROOT / "config/config.yaml").read_text(encoding="utf-8"))
        for toolset in config["platform_toolsets"]["cli"]:
            self.assertIn(f"`{toolset}`", readme)
        for semantic in (
            "创建时间戳备份",
            "退役 managed MCP 每次同步都会移除",
            "一次性迁移状态只保护退役插件",
            "输出 repo/live 目录哈希",
            "绝不把 live skills",
            "显示脱敏后的 Hermes Provider/模型配置",
            "Hermes 版本、配置、认证 inventory 和 MCP inventory",
            "普通端口、HTTP 状态和结构检查不等于真实模型执行",
            "Context7 查询会外发数据",
            "一个 checkout 只能有一个 writer",
            "Task Ticket、plan mode、hook、路径声明和 worktree 都不是安全 sandbox",
            "全局可迁移工作流增强包",
            "不是只服务本仓库的项目内脚本集合",
            "live Hermes Home 才是运行时落点",
            "只对本仓库有用的临时脚本不得被包装成默认全局能力",
            "Context Pack",
            ".hermes/task-artifacts/context-pack.md",
            "MCP_CANDIDATE_AUDIT_PASS",
            "UI/Skin 系统",
            "不默认安装 UI runtime",
            "本地 quality gate runner 命令顺序",
            "python scripts/workflow/run_quality_gate.py verify",
            "每次 push 和 pull request",
            "CI verdict 绑定提交 SHA",
        ):
            self.assertIn(semantic, readme)
        self.assertNotIn("避免后续误删用户重新启用的功能", readme)
        self.assertIn("不会安装 Hermes、Codex 或 CC Switch 主体", readme)
        self.assertIn("结构检查不等于真实模型执行", readme)

    def test_project_definition_scope_is_global_workflow_enhancement(self) -> None:
        definition = (ROOT / "docs/workflow/project-definition.md").read_text(
            encoding="utf-8"
        )
        for marker in (
            "全局工作流增强项目",
            "本仓库只是这些全局增强资产的可审计源目录",
            "增强目标是用户的整体 Agent 工作流",
            "## 全局增强边界",
            "任意业务项目",
            "不得进入默认 portable config、全局 skill、默认 MCP 或同步脚本",
        ):
            self.assertIn(marker, definition)
        self.assertIn("Hermes Agent + CC Switch + Codex 的全局工作流", definition)
        self.assertNotIn("只对本仓库生效的局部工具集：\n\n## 三层职责", definition)

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
        for marker in (
            "PowerShell selection policy",
            "prefer **PowerShell 7** via `pwsh`",
            "powershell.exe",
        ):
            self.assertIn(marker, body)
        for name in (
            "codex++-proxy-routing.md",
            "provider-network-troubleshooting.md",
            "third-party-proxy-setup.md",
            "credential-audit-and-template.md",
            "github-credential-extraction.md",
        ):
            self.assertFalse((skill / "references" / name).exists(), name)

    def test_sleep_mode_is_portable_and_enforces_durable_queue_boundaries(self) -> None:
        skill = ROOT / "skills/software-development/sleep-mode/SKILL.md"
        self.assertTrue(skill.exists())
        body = skill.read_text(encoding="utf-8")
        for marker in (
            ".hermes/sleep-mode/",
            "state.json",
            "activity.jsonl",
            "每个项目只允许一条活跃写队列",
            "one writer, one bounded task per cycle",
            "不计入进度",
            "mode != active",
            "高风险",
        ):
            self.assertIn(marker, body)

        sync = (ROOT / "scripts/workflow/sync_hermes_workflow_assets.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('copytree(repo / "skills", home / "skills", apply=args.apply)', sync)

    def test_project_data_boundary_is_deployable_and_fail_closed(self) -> None:
        helper = ROOT / "bin/hermes-project-data.py"
        skill = ROOT / "skills/software-development/project-data-boundary/SKILL.md"
        doc = ROOT / "docs/workflow/project-data-boundary.md"
        self.assertTrue(helper.exists())
        self.assertTrue(skill.exists())
        self.assertTrue(doc.exists())
        body = helper.read_text(encoding="utf-8")
        for marker in (
            "git-ignored",
            "check-ignore",
            "TMP",
            "PIP_CACHE_DIR",
            "PYTHONPYCACHEPREFIX",
            "path escapes project root",
        ):
            self.assertIn(marker, body)
        self.assertIn("hermes-project-data.py", (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_context_pack_generator_is_project_local_and_secret_redacting(self) -> None:
        script = ROOT / "scripts/workflow/build_context_pack.py"
        doc = ROOT / "docs/workflow/context-pack.md"
        self.assertTrue(script.exists())
        self.assertTrue(doc.exists())

        spec = importlib.util.spec_from_file_location("context_pack", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            (repo / ".gitignore").write_text(".hermes/\n", encoding="utf-8")
            (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
            (repo / "config").mkdir()
            secret = "github_pat_" + "A" * 30
            (repo / "config/config.yaml").write_text(
                f"display:\n  busy_input_mode: queue\napi_key: {secret}\n",
                encoding="utf-8",
            )
            (repo / "docs/workflow").mkdir(parents=True)
            (repo / "docs/workflow/project-definition.md").write_text(
                "# Definition\nHermes Agent + CC Switch + Codex\n",
                encoding="utf-8",
            )
            subprocess.run(
                [
                    "git",
                    "add",
                    ".gitignore",
                    "README.md",
                    "config/config.yaml",
                    "docs/workflow/project-definition.md",
                ],
                cwd=repo,
                check=True,
                capture_output=True,
            )

            output = module.write_context_pack(repo, module.DEFAULT_OUTPUT, max_chars=20000)
            body = output.read_text(encoding="utf-8")
            self.assertEqual(
                module.canonical_path(output).relative_to(module.canonical_path(repo)).as_posix(),
                ".hermes/task-artifacts/context-pack.md",
            )
            self.assertIn("Workflow-assistance Context Pack", body)
            self.assertIn("global Hermes Agent + CC Switch + Codex workflow", body)
            self.assertIn("[REDACTED]", body)
            self.assertNotIn(secret, body)
            self.assertNotIn("auth.json", "\n".join(module.tracked_inventory(repo)))

            with self.assertRaises(SystemExit):
                module.write_context_pack(repo, Path("context-pack.md"), max_chars=20000)
            with self.assertRaises(SystemExit):
                module.write_context_pack(repo, Path("../context-pack.md"), max_chars=20000)

    def test_context_pack_uses_canonical_paths_for_windows_short_name_aliases(self) -> None:
        script = ROOT / "scripts/workflow/build_context_pack.py"
        spec = importlib.util.spec_from_file_location("context_pack_alias", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            (repo / ".gitignore").write_text(".hermes/\n", encoding="utf-8")
            (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", ".gitignore", "README.md"],
                cwd=repo,
                check=True,
                capture_output=True,
            )

            alias_root = Path(str(repo) + "-SHORT-ALIAS")
            real_canonical_path = module.canonical_path

            def fake_canonical_path(path: Path) -> Path:
                text = str(path)
                alias = str(alias_root)
                if text == alias or text.startswith(alias + "\\") or text.startswith(alias + "/"):
                    suffix = text[len(alias) :].lstrip("\\/")
                    return repo / suffix if suffix else repo
                return real_canonical_path(path)

            module.canonical_path = fake_canonical_path
            try:
                output = module.write_context_pack(
                    alias_root, Path(".hermes/task-artifacts/context-pack.md"), max_chars=20000
                )
            finally:
                module.canonical_path = real_canonical_path

            self.assertEqual(
                module.canonical_path(output).relative_to(module.canonical_path(repo)).as_posix(),
                ".hermes/task-artifacts/context-pack.md",
            )

    def test_quality_gate_runner_is_canonical_and_just_is_optional(self) -> None:
        runner = ROOT / "scripts/workflow/run_quality_gate.py"
        justfile = ROOT / "Justfile"
        doc = ROOT / "docs/workflow/local-quality-gates.md"
        workflow = ROOT / ".github/workflows/governance.yml"
        self.assertTrue(runner.exists())
        self.assertTrue(justfile.exists())
        self.assertTrue(doc.exists())

        spec = importlib.util.spec_from_file_location("quality_gate", runner)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertEqual(
            module.VERIFY_ORDER,
            ("governance", "compile", "security", "context-pack", "mcp-audit", "shell", "powershell"),
        )
        self.assertEqual(set(module.GATES), set(module.VERIFY_ORDER))
        self.assertIn("scripts/workflow/run_quality_gate.py", module.tracked_python_files())
        self.assertIn("tests/test_workflow_governance.py", module.tracked_python_files())

        body = runner.read_text(encoding="utf-8")
        for marker in (
            "QUALITY_GATE_PASS",
            "QUALITY_GATE_FAIL",
            "build_context_pack.py",
            "mcp_candidate_audit.py",
            "scan_agent_rules.py",
            "usable_bash()",
            "Git Bash / GNU bash not found",
            "shutil.which(\"pwsh\") or shutil.which(\"powershell.exe\")",
            "ParseFile((Resolve-Path ./setup.ps1)",
        ):
            self.assertIn(marker, body)
        self.assertNotIn("shell=True", body)
        self.assertNotIn("npm install just", body)
        self.assertNotIn("choco install just", body)

        just = justfile.read_text(encoding="utf-8")
        self.assertIn("python scripts/workflow/run_quality_gate.py verify", just)
        self.assertIn("python scripts/workflow/run_quality_gate.py mcp-audit", just)
        self.assertIn("just is not a required dependency", just)

        combined = "\n".join(
            (
                doc.read_text(encoding="utf-8"),
                workflow.read_text(encoding="utf-8"),
                (ROOT / "README.md").read_text(encoding="utf-8"),
            )
        )
        for marker in (
            "python scripts/workflow/run_quality_gate.py verify",
            "just is not a required dependency",
            "QUALITY_GATE_PASS",
            "QUALITY_GATE_FAIL",
            "context-pack",
            "mcp-audit",
            "PowerShell gate 优先 `pwsh`",
        ):
            self.assertIn(marker, combined)
        self.assertEqual(
            workflow.read_text(encoding="utf-8").count(
                "python scripts/workflow/run_quality_gate.py verify"
            ),
            2,
        )
        for setup in ("setup.sh", "setup.ps1"):
            self.assertNotIn("just", (ROOT / setup).read_text(encoding="utf-8").lower())

        list_result = subprocess.run(
            [sys.executable, str(runner), "list"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("verify: Run governance, compile, security, context-pack, mcp-audit", list_result.stdout)

    def test_mcp_candidate_audit_is_fail_closed_and_does_not_enable_defaults(self) -> None:
        script = ROOT / "scripts/workflow/mcp_candidate_audit.py"
        doc = ROOT / "docs/mcp/mcp-catalog-governance.md"
        stack = ROOT / "docs/mcp/workflow-mcp-stack.md"
        self.assertTrue(script.exists())
        self.assertTrue(doc.exists())

        spec = importlib.util.spec_from_file_location("mcp_candidate_audit", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        good = {
            "schema_version": 1,
            "name": "docs-search-mcp",
            "status": "candidate",
            "default_enable": False,
            "source": {
                "package": "@example/docs-search-mcp@1.2.3",
                "repository": "https://github.com/example/docs-search-mcp",
                "license": "MIT",
                "version": "1.2.3",
            },
            "purpose": "Search a public docs index not covered by Context7.",
            "distinct_advantage": "Narrow public docs index with stable citations.",
            "data_external": True,
            "permissions": {
                "filesystem": "none",
                "network": "public docs API",
                "browser": "none",
                "credentials": [],
            },
            "required_env": [],
            "overlaps_native_tools": ["web_search"],
            "smoke": {
                "command": "hermes mcp test docs-search-mcp",
                "status": "not_run",
                "evidence": "candidate only",
            },
            "prompt_schema_budget": {
                "measured": False,
                "command": "hermes prompt-size --json",
                "delta_tokens": None,
            },
        }
        passed, findings = module.audit_candidate(good)
        self.assertTrue(passed, findings)

        bad = dict(good)
        bad["default_enable"] = True
        bad["source"] = dict(good["source"], package="@example/docs-search-mcp@latest", version="latest")
        bad["smoke"] = dict(good["smoke"], status="not_run")
        passed, findings = module.audit_candidate(bad)
        self.assertFalse(passed)
        codes = {finding["code"] for finding in findings}
        self.assertTrue(
            {
                "default_enable_requested",
                "default_without_smoke_pass",
                "default_without_prompt_budget",
                "unpinned_version",
            }.issubset(codes),
            findings,
        )

        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            template = temp / "candidate.yaml"
            module.write_template(template)
            template_body = yaml.safe_load(template.read_text(encoding="utf-8"))
            self.assertFalse(template_body["default_enable"])
            result = subprocess.run(
                [sys.executable, str(script), str(template)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("MCP_CANDIDATE_AUDIT_PASS", result.stdout)

        combined = "\n".join(
            (
                script.read_text(encoding="utf-8"),
                doc.read_text(encoding="utf-8"),
                stack.read_text(encoding="utf-8"),
                (ROOT / "README.md").read_text(encoding="utf-8"),
            )
        )
        for marker in (
            "MCP_CANDIDATE_AUDIT_PASS",
            "MCP_CANDIDATE_AUDIT_FAIL",
            "default_enable_requested",
            "overlaps_native_tools",
            "prompt_schema_budget",
            "不等于 server 已配置、已运行、已安全或已默认启用",
        ):
            self.assertIn(marker, combined)
        self.assertNotIn("hermes mcp add", script.read_text(encoding="utf-8"))
        self.assertEqual(
            set(yaml.safe_load((ROOT / "config/config.yaml").read_text(encoding="utf-8"))["mcp_servers"]),
            {"context7"},
        )

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

    def test_kimi_speed_lane_contract_is_consistent(self) -> None:
        switcher = (ROOT / "scripts/workflow/switch_model.py").read_text(encoding="utf-8")
        skill = (ROOT / "skills/model-switch/SKILL.md").read_text(encoding="utf-8")
        lanes = (ROOT / "skills/model-switch/references/current-model-lanes.md").read_text(
            encoding="utf-8"
        )
        latency = (ROOT / "skills/model-switch/references/latency-tuning.md").read_text(
            encoding="utf-8"
        )

        for marker in (
            'KIMI_MODEL = os.environ.get("HERMES_KIMI_MODEL", "kimi-k3")',
            'KIMI_FAST_MODEL = os.environ.get("HERMES_KIMI_FAST_MODEL", "kimi-k2.7-code")',
            'KIMI_TURBO_MODEL = os.environ.get("HERMES_KIMI_TURBO_MODEL", "kimi-k2.7-code-highspeed")',
            "'kimi-fast'",
            "'kimi-turbo'",
            "if args.target == 'kimi-turbo':",
            "elif args.target == 'kimi-fast':",
        ):
            self.assertIn(marker, switcher)

        for document in (skill, lanes, latency):
            self.assertIn("kimi-k2.7-code", document)
            self.assertIn("kimi-k2.7-code-highspeed", document)
        self.assertIn("/切换KIMI快", lanes)
        self.assertIn("/切换KIMI极速", lanes)
        self.assertIn("kimi-fast` → Kimi K2.7 Code", lanes)
        self.assertIn("kimi-turbo` → Kimi K2.7 Code HighSpeed", lanes)

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

    def test_agent_behavior_eval_template_is_safe_and_model_neutral(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        doc_path = ROOT / "docs/workflow/agent-evaluation.md"
        template_path = ROOT / "templates/evals/agent-behavior-smoke.yaml"
        absorption = (ROOT / "docs/absorption/open-source-workflow-absorption.md").read_text(
            encoding="utf-8"
        )

        self.assertTrue(doc_path.exists())
        self.assertTrue(template_path.exists())
        self.assertIn("docs/workflow/agent-evaluation.md", readme)
        self.assertIn("templates/evals/agent-behavior-smoke.yaml", readme)
        self.assertIn("promptfoo/promptfoo", absorption)

        doc = doc_path.read_text(encoding="utf-8")
        template_body = template_path.read_text(encoding="utf-8")
        template = yaml.safe_load(template_body)

        self.assertEqual(template["schema_version"], 1)
        self.assertEqual(template["source"]["inspiration"], "promptfoo/promptfoo")
        self.assertEqual(template["source"]["runtime_dependency"], "none")
        self.assertEqual(template["source"]["license"], "MIT")
        self.assertEqual(
            template["assertion_policy"]["artifact_root"],
            ".hermes/task-artifacts/evals/",
        )
        self.assertGreaterEqual(len(template["cases"]), 6)

        combined = "\n".join((doc, template_body, absorption))
        for marker in (
            "不安装 runner",
            "不配置 provider",
            "不保存真实 trace",
            "不把任何外部评估运行时",
            "不默认发起模型请求",
            "不是完整测试套件 green",
            "Gateway process running",
            "interrupted delegation",
            "PowerShell 7",
            "display.busy_input_mode: queue",
        ):
            self.assertIn(marker, combined)

        forbidden = (
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "LANGFUSE_PUBLIC_KEY",
            "LANGFUSE_SECRET_KEY",
            "provider: openai",
            "provider: anthropic",
            "npm install promptfoo",
            "npx promptfoo",
        )
        for marker in forbidden:
            self.assertNotIn(marker, combined)

    def test_ui_skin_absorption_pack_is_lightweight_and_runtime_neutral(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        doc_path = ROOT / "docs/workflow/ui-skin-system.md"
        presets_path = ROOT / "templates/ui/skin-presets.yaml"
        patterns_path = ROOT / "templates/ui/agent-chat-ui-patterns.md"
        checklist_path = ROOT / "templates/ui/terminal-theme-checklist.md"
        terminal_path = ROOT / "templates/windows-terminal/catppuccin-mocha.json"
        absorption = (ROOT / "docs/absorption/open-source-workflow-absorption.md").read_text(
            encoding="utf-8"
        )
        skill = (
            ROOT / "skills/software-development/agent-workflow-fortress/SKILL.md"
        ).read_text(encoding="utf-8")
        reference = (
            ROOT
            / "skills/software-development/agent-workflow-fortress/references/ui-skin-absorption.md"
        ).read_text(encoding="utf-8")

        for path in (doc_path, presets_path, patterns_path, checklist_path, terminal_path):
            self.assertTrue(path.exists(), path.relative_to(ROOT).as_posix())
            self.assertIn(path.relative_to(ROOT).as_posix(), readme)

        presets = yaml.safe_load(presets_path.read_text(encoding="utf-8"))
        terminal = json.loads(terminal_path.read_text(encoding="utf-8"))

        self.assertEqual(presets["schema_version"], 1)
        self.assertEqual(presets["runtime_dependency"], "none")
        self.assertFalse(presets["default_applied"])
        self.assertEqual(
            presets["presets"]["catppuccin-mocha"]["colors"]["base"],
            "#1e1e2e",
        )
        self.assertEqual(
            presets["presets"]["catppuccin-mocha"]["colors"]["mauve"],
            "#cba6f7",
        )
        self.assertEqual(
            terminal["name"],
            "Catppuccin Mocha - Workflow Assistance",
        )
        self.assertEqual(terminal["background"], "#1e1e2e")
        self.assertEqual(terminal["foreground"], "#cdd6f4")

        sources = {item["repository"] for item in presets["sources"]}
        self.assertTrue(
            {
                "catppuccin/catppuccin",
                "catppuccin/windows-terminal",
                "shadcn-ui/ui",
                "assistant-ui/assistant-ui",
            }.issubset(sources)
        )
        self.assertTrue(presets["boundaries"]["no_default_install"])
        self.assertTrue(presets["boundaries"]["no_runtime_assets"])
        self.assertTrue(presets["boundaries"]["no_terminal_settings_write"])
        self.assertTrue(presets["boundaries"]["no_hermes_live_config_write"])

        combined = "\n".join(
            (
                doc_path.read_text(encoding="utf-8"),
                presets_path.read_text(encoding="utf-8"),
                patterns_path.read_text(encoding="utf-8"),
                checklist_path.read_text(encoding="utf-8"),
                absorption,
                skill,
                reference,
            )
        )
        for marker in (
            "Catppuccin",
            "shadcn-ui",
            "assistant-ui",
            "template available, not applied",
            "不默认安装 UI runtime",
            "不自动修改 Hermes live config",
            "不自动改用户 settings",
            "repo/live/session",
            "tool call timeline",
            "verification evidence",
            "Open WebUI / NextChat / Vercel AI Chatbot",
        ):
            self.assertIn(marker, combined)

        forbidden = (
            "npm install shadcn",
            "npx shadcn",
            "npm install assistant-ui",
            "npm install open-webui",
            "git clone https://github.com/open-webui/open-webui",
            "Copy-Item",
            "Set-Content $env:LOCALAPPDATA",
            "hermes config set model.provider",
            "hermes mcp add",
            "plugins enable",
        )
        for marker in forbidden:
            self.assertNotIn(marker, combined)


if __name__ == "__main__":
    unittest.main()
