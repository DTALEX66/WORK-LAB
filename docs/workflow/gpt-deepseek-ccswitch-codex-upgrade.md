# Hermes + GPT/DeepSeek + CC Switch + Codex 全链路工作流

## 目标

把个人 Hermes 工作流升级成可迁移、可审计、可给对公项目复用的三引擎体系：

```text
Hermes 负责：任务编排、技能、记忆、MCP、审计、跨会话沉淀
GPT     负责：高质量复杂推理/编码（openai-codex OAuth + ChatGPT 订阅）
DeepSeek负责：直连备用、低延迟/低成本中文与代码任务
CC Switch负责：代理网络与 Codex/ChatGPT 生态连通
Codex   负责：独立编码 Agent、插件生态、任务执行面
```

## 当前实测状态（2026-07）

| 组件 | 状态 | 证据/命令 |
|---|---|---|
| Hermes | 可用 | `hermes --version` |
| GPT | 可用 | `openai-codex` OAuth 凭证存在，当前模型 `gpt-5.5` |
| DeepSeek | 可用 | `DEEPSEEK_API_KEY` 存在，`api.deepseek.com` 可达 |
| CC Switch | 可用 | `127.0.0.1:7890` 监听，`curl --proxy ... https://chatgpt.com` |
| Codex | 可用但不在 PATH | `~/.codex/plugins/.plugin-appserver/codex.exe --version` |
| Codex proxy | 可用 | `127.0.0.1:15721` 监听 |
| MCP Node | 已修复路径风险 | 系统 Node v16；Hermes bundled Node v22.23.1；通过 `hermes-npx` wrapper 固定优先使用 Hermes Node |

## 路由矩阵

| 场景 | 推荐路线 | 命令 |
|---|---|---|
| 默认高质量推理/编码 | GPT via CC Switch | `python scripts/workflow/switch_model.py gpt` |
| 代理不可用/成本优先 | DeepSeek 直连 | `python scripts/workflow/switch_model.py deepseek` |
| Codex 独立执行任务 | Codex CLI/插件 | 使用 `templates/task-tickets/cc-switch-agent-task.md` |
| 新机器体检 | Doctor | `python scripts/workflow/hermes_workflow_doctor.py` |

## 默认 MCP 策略

默认启用：

1. `public-apis`：公共 API 发现。
2. `sequential-thinking`：复杂任务拆解。
3. `context7`：实时库文档，减少过期 API 用法。

不默认启用：

- `@playwright/mcp`：已用 Hermes Node v22 smoke test 可启动，但 Hermes 已有 `browser`/`computer_use`。除非要把同一 Playwright MCP 暴露给多 Agent，否则不默认扩大浏览器权限面。
- filesystem/memory MCP：Hermes 已有原生 file/memory 工具，重复会增加权限面和上下文噪声。

## 对公项目标准循环

1. `git status --short --branch`，确认工作区。
2. `python scripts/workflow/hermes_workflow_doctor.py`，确认 Hermes/GPT/DeepSeek/CC Switch/Codex 基线。
3. 生成任务单：复制 `templates/task-tickets/cc-switch-agent-task.md`，填写 allowed/forbidden paths、测试命令、输出契约。
4. Hermes 做编排和审计；Codex/子 Agent 做隔离实现；DeepSeek 作为备用 Provider。
5. 每次落地前运行：
   ```bash
   python scripts/security/scan_agent_rules.py templates skills docs scripts
   python scripts/workflow/hermes_workflow_doctor.py
   git diff --check
   ```
6. 提交前必须确认：无 `.env`、`auth.json`、Token、OAuth 文件、安装主体或大二进制。

## 新机器部署注意

- 本仓库不保存 Hermes/CC Switch/Codex 安装主体。
- `setup.ps1` / `setup.sh` 会复制 `bin/hermes-npx*` 到 Hermes home，并把部署后的 `config.yaml` 的 MCP 命令改为绝对 wrapper 路径。
- 这避免系统 PATH 中旧 Node（如 v16）导致 Context7/Playwright 等 MCP 启动失败。
- GPT OAuth 必须每台机器重新登录：`hermes auth add openai-codex`。
- DeepSeek Key 写入 `.env`，不要写进 `config.yaml` 或仓库。

## 故障优先级

1. GPT 不通：先查 `127.0.0.1:7890`，再查 `auth.openai.com/chatgpt.com` 代理访问。
2. 模型不对：查 `hermes config` 的 `model.provider/default/base_url/api_key`，切换后 `/reset` 或重启。
3. MCP 不通：查 `hermes mcp list/test`，再查 `hermes-npx` 是否使用 Hermes Node v22。
4. Codex 不通：查 `~/.codex/config.toml` 的 `base_url`、`model`、`wire_api`，不要输出 bearer token。
