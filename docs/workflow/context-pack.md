# Context Pack 生成器

Context Pack 是给新会话、长任务恢复、Codex/CC Switch handoff 和人工复盘使用的**安全上下文包**。它吸收 `repomix` / `gitingest` 的“仓库转 LLM-friendly context”方法，但保持 Workflow-assistance 的边界：不 vendor 第三方源码，不安装默认运行时，不收集密钥、会话、日志或缓存。

## 目标

`Workflow-assistance` 是全局 Hermes Agent + CC Switch + Codex 工作流增强包。Context Pack 用于快速重建这条工作流的可迁移状态：

- 当前 Git branch、HEAD、status 和最近提交；
- portable 资产 inventory；
- skills inventory；
- README、项目定义、Gateway/cron、Agent eval、MCP、project-data-boundary 等白名单文档摘要；
- handoff reminders：repo/live/session 分层、Gateway delivery 分层、单写者、context-pack 不是实际产品任务完成。

## 入口

```bash
python scripts/workflow/build_context_pack.py
```

默认输出：

```text
.hermes/task-artifacts/context-pack.md
```

该目录必须被 Git 忽略；否则脚本 fail-closed。当前仓库 `.gitignore` 已包含：

```text
.hermes/
```

也可以显式指定：

```bash
python scripts/workflow/build_context_pack.py --output .hermes/task-artifacts/context-pack.md
python scripts/workflow/build_context_pack.py --stdout --max-chars 20000
```

## 安全边界

脚本只读取 tracked allowlist 和 Git 元数据，并明确排除：

- `.env`；
- `auth.json`；
- `state.db`；
- `.hermes/`；
- logs/cache/session/runtime data；
- `node_modules`、venv、构建产物；
- 任何项目根外输出路径。

输出前会对常见 token/API key/password/Bearer/GitHub/npm/Slack/JWT 模式做脱敏。Context Pack 不保证覆盖所有秘密格式，因此不要把真实私密文件加入 allowlist。

## 不是完成证明

Context Pack 是 handoff/evidence artifact，不是实际产品任务完成，也不是 live Hermes 已加载证明。它不能替代：

- `python tests/test_workflow_governance.py -v`；
- `python scripts/security/scan_agent_rules.py ...`；
- `hermes mcp test context7`；
- `scripts/workflow/sync_hermes_workflow_assets.py --apply`；
- exact-tree review / CI verdict。

## 推荐使用场景

- 新会话前生成一个干净上下文；
- 长任务 sleep-mode/cron 每轮留下 handoff；
- 交给 Codex/CC Switch 之前提供 repo 状态摘要；
- 发生上下文过大时，用 context pack 替代整段历史和大段 tool output。

## 验证

```bash
python scripts/workflow/build_context_pack.py --max-chars 20000
python -m py_compile scripts/workflow/build_context_pack.py
python tests/test_workflow_governance.py -v
python scripts/security/scan_agent_rules.py templates skills docs scripts README.md
```

如果系统要求 fresh ad-hoc evidence，可在 `C:\Users\admin\AppData\Local\Temp\hermes-verify-*` 创建临时脚本，检查默认输出路径、Git-ignore fail-closed、脱敏和单测方法。
