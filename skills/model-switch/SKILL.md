---
name: model-switch
description: 在 Hermes 的 GPT(openai-codex OAuth + CC Switch) 与 DeepSeek 官方 Provider 之间安全切换，并诊断 Codex/CC Switch/MCP 基线。
tags: [hermes, provider, routing, deepseek, openai, codex, proxy, cc-switch, mcp]
---

# Hermes Provider 路由切换

## 触发条件

| 用户说 | 动作 |
|---|---|
| 切DP / 切换DP / 换DP / 切换到DeepSeek | 切到 DeepSeek 直连 |
| 切GPT / 切换GPT / 换GPT / 切换到GPT | 切到 GPT via openai-codex OAuth |
| 检查模型 / 工作流体检 / CC Switch 诊断 / Codex 诊断 | 运行 workflow doctor |

## 优先使用脚本

在 `Workflow-assistance` 仓库内，优先使用已审计脚本：

```bash
# 查看当前配置与前提
python scripts/workflow/switch_model.py status

# 切到 GPT via ChatGPT OAuth + CC Switch
python scripts/workflow/switch_model.py gpt

# 切到 DeepSeek 官方 Provider
python scripts/workflow/switch_model.py deepseek

# 全链路体检：Hermes / GPT / DeepSeek / CC Switch / Codex / MCP / Node
python scripts/workflow/hermes_workflow_doctor.py
```

切换后必须 `/reset` 或重启 Hermes；`.env` 代理变量变更必须完全重启 Hermes。

## 路由方案

### A. GPT via openai-codex OAuth + CC Switch

```text
Hermes → CC Switch(:7890) → chatgpt.com/backend-api/codex → gpt-5.5
```

前提：

- `127.0.0.1:7890` 监听；
- `hermes auth list` 中有 `openai-codex` OAuth；
- `.env` 中有：
  - `HTTPS_PROXY=http://127.0.0.1:7890`
  - `HTTP_PROXY=http://127.0.0.1:7890`

CLI 等效：

```bash
hermes config set model.provider openai-codex
hermes config set model.default gpt-5.5
hermes config set model.base_url ''
hermes config set model.api_key ''
```

### B. DeepSeek 直连

```text
Hermes → api.deepseek.com/v1 → deepseek-v4-flash
```

前提：`.env` 中有 `DEEPSEEK_API_KEY`。

CLI 等效：

```bash
hermes config set model.provider deepseek
hermes config set model.base_url https://api.deepseek.com/v1
hermes config set model.default deepseek-v4-flash
hermes config set model.api_key ''
```

### C. Codex 本地生态

Codex 当前可作为独立编码 Agent/插件生态使用；本机常见路径：

```text
~/.codex/plugins/.plugin-appserver/codex.exe
```

如果 `codex` 不在 PATH，不要判定为未安装；先查上述路径：

```bash
~/.codex/plugins/.plugin-appserver/codex.exe --version
```

Codex 配置中可能存在 bearer token；诊断输出必须脱敏，不要复制 `auth.json` 或 `config.toml` 中的密钥字段。

### D. MCP Node wrapper

当前系统 PATH 可能有旧 Node；MCP 默认走 `bin/hermes-npx*` wrapper，优先使用 Hermes bundled Node v22：

```bash
bin/hermes-npx -y @upstash/context7-mcp@3.2.2 --help
bin/hermes-npx -y @modelcontextprotocol/server-sequential-thinking@2025.12.18 --help
bin/hermes-npx -y public-apis-mcp@0.0.10 --help
```

## 排查顺序

1. 运行 `python scripts/workflow/hermes_workflow_doctor.py`。
2. GPT 不通：先查 `127.0.0.1:7890`，再查代理访问 `chatgpt.com` / `auth.openai.com`。
3. DeepSeek 不通：查 `DEEPSEEK_API_KEY` 和 `api.deepseek.com`。
4. MCP 不通：查 `hermes-npx` 是否使用 Hermes bundled Node v22。
5. Codex 不通：查 `.codex/plugins/.plugin-appserver/codex.exe` 和 `127.0.0.1:15721`。

## 安全规则

- 不输出 API Key、OAuth token、bearer token、auth.json 内容。
- 不把 ChatGPT 订阅当 OpenAI API Key。
- 不把真实 `.env` 上传仓库。
- 切换 Provider 后必须重新开会话验证，不能假装当前会话模型已变。