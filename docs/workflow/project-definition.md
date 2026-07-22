# 项目定义：HERMES + CC Switch + Codex 工作流增强项目

## 一句话定位

`Workflow-assistance` 是 DTALEX66 的 **Hermes Agent + CC Switch + Codex 全局工作流增强项目**：用于沉淀、迁移和持续强化用户所有项目里的 Hermes 会话习惯、模型/provider 切换、CC Switch 代理路径、Codex 执行与复审方式、MCP 默认策略、长任务持久化、项目数据边界、排错经验、验证脚本和自动化工作流。

本仓库只是这些全局增强资产的可审计源目录，不是增强目标本身。增强目标是用户的整体 Agent 工作流：Hermes Agent 是运行与编排入口，CC Switch 是网络/路由辅助层，Codex 是编码执行与复审协作面；`D:\All projects\Workflow-assistance` 负责保存可迁移、可验证、可同步到 live Hermes Home 的配置、脚本、技能、模板和规范。

## 项目边界

本项目保存的是“全局工作流增强资产”，不是任何运行时主体的安装包，也不是只对本仓库生效的局部工具集：

- 不包含 Hermes Agent 安装主体。
- 不包含 CC Switch 安装主体。
- 不包含 Codex CLI / ChatGPT OAuth 的真实凭证。
- 不提交 `.env`、`auth.json`、API Key、Token、会话数据库、缓存或日志。

## 全局增强边界

| 范围 | 属于本项目 | 不属于本项目 |
|---|---|---|
| Hermes Agent | 可迁移配置基线、skills、MCP 默认策略、Gateway/cron/sleep-mode 说明、live 同步脚本 | Hermes Agent 核心源码、真实凭据、会话数据库、运行日志 |
| CC Switch | 代理端口/网络路径排错、Provider 前置检查、环境变量模板 | CC Switch 主程序安装包、用户真实代理凭据 |
| Codex | launcher、任务票据、单写者/worktree 规范、只读复审与 exact-tree 证据规则 | Codex CLI 主体、OpenAI OAuth token、模型服务凭据 |
| 任意业务项目 | `.hermes/` 项目数据边界、任务 artifact/ledger 规范、可复制 Agent rules | 业务项目源码本身、项目私有数据、临时一次性修复 |
| Workflow-assistance 仓库 | 全局增强资产源、文档、治理测试、同步/doctor 脚本 | 把本仓库当成唯一使用场景或运行时 sandbox |

新增内容必须回答两个问题：

1. 它是否增强 **Hermes Agent + CC Switch + Codex 的全局工作流**，而不是只方便当前仓库一次操作？
2. 它是否可以安全迁移到其他机器/项目，而不携带密钥、会话、日志、缓存或用户私有数据？

如果答案是否定的，只能放在项目本地 `.hermes/` 或一次性任务 artifact 中，不得进入默认 portable config、全局 skill、默认 MCP 或同步脚本。

## 三层职责

| 层级 | 责任 | 本仓库沉淀内容 |
|---|---|---|
| Hermes Agent | Agent 运行、模型/provider、工具、技能、MCP、记忆与会话 | `config/`、`skills/`、`bin/hermes-npx*`、Hermes doctor/切换脚本 |
| CC Switch | 本地代理、网络通道、Agent 生态辅助 | 代理环境变量模板、排错手册、与 Hermes/Codex 协作约定 |
| Codex / OpenAI OAuth | GPT 订阅/OAuth 路线、Codex CLI/工作流协作 | OAuth 流程说明、任务单模板、`CODEX.md`/Agent rules 模板 |

## 当前同步状态

运行时状态必须由现场 doctor/marker 重新验证；本文件不保存机器专属路径、凭据状态或历史 smoke 结论。

- 本地仓库：`D:\All projects\Workflow-assistance`
- 云端仓库：`https://github.com/DTALEX66/Workflow-assistance`
- live Hermes Home：`%LOCALAPPDATA%\hermes`（或 `$HERMES_HOME`）。
- Git / live / provider 状态：用 `git status`、`hermes_workflow_doctor.py` 与需要时的 `--live` marker 现场确认。
- 同步保留当前 provider/model、OAuth/API key、私有 MCP 和用户自定义命令；同步 portable 的模型 picker、快捷命令与速度策略。
- 默认 MCP：仅 `context7`；其他 MCP 必须按任务审计后启用。

## 可迁移资产清单

| 资产 | 仓库位置 | live Hermes 目标 | 说明 |
|---|---|---|---|
| Hermes 配置模板 | `config/config.yaml` | `config.yaml` | 新机器基线；同步脚本合并时保留 live provider/model，并管理 `display.busy_input_mode=queue` |
| 环境变量模板 | `config/.env.template` | `.env.template` | 只放占位说明，不放真实密钥 |
| MCP wrapper | `bin/hermes-npx*` | `bin/hermes-npx*` | Windows live config 指向 `.cmd`；优先 bundled Node，缺失时可回退 PATH Node >=20 |
| 技能 | `skills/` | `skills/` | 包含 codex、model-switch、sleep-mode、project-data-boundary、python-testing、windows-development-environment、agent-workflow-fortress；其中 sleep-mode 通过项目 `.hermes/sleep-mode/` 状态账本和 Hermes cron 管理持久队列，不复制运行时或凭据 |
| 项目数据执行器 | `bin/hermes-project-data.py` | `bin/hermes-project-data.py` | fail-closed 验证 Git ignore，并把任务临时文件、缓存、日志、测试环境与产物锁到 `<project>/.hermes/task-runtime/` |
| 同步脚本 | `scripts/workflow/sync_hermes_workflow_assets.py` | 手动运行 | repo ↔ live 定向同步；每次 apply 前备份可迁移资产 |
| 排错记录 | `TROUBLESHOOTING.md`、`docs/workflow/error-fixes-2026-07-04.md`、`docs/workflow/gateway-cron-delivery.md` | 仓库文档 | 记录 Windows MCP、路径、GitHub CLI、Gateway/cron delivery、验证等已踩坑 |

## 本地项目定义

- 本地路径：`D:\All projects\Workflow-assistance`
- 本地角色：可编辑、可验证、可提交的工作流增强资产源目录。
- 本地操作原则：先检查 → 小步修改 → 语法/安全/MCP 或 ad-hoc 验证 → commit → push。

## GitHub 云端项目定义

- 云端仓库：`https://github.com/DTALEX66/Workflow-assistance`
- 云端角色：跨电脑同步的 HERMES + CC Switch + Codex 工作流增强资产库。
- 云端应保持：README 定位清晰、部署命令指向 `Workflow-assistance`、topics/description 能反映 Hermes、CC Switch、Codex、MCP、workflow automation。

## 验证基线

修改仓库后至少根据变更类型运行以下检查：

```bash
git status --short --branch
bash -n setup.sh
bash -n bin/hermes-npx
python -m py_compile scripts/workflow/sync_hermes_workflow_assets.py scripts/workflow/hermes_workflow_doctor.py scripts/workflow/switch_model.py scripts/security/scan_agent_rules.py
python scripts/security/scan_agent_rules.py .
hermes mcp test context7
```

隔离 ad-hoc 验证也必须通过 `bin/hermes-project-data.py --project . run -- ...`，使临时脚本和所有运行数据保留在当前项目的 `.hermes/task-runtime/`，不得写入用户 Temp。

## 标准闭环

1. 在本地仓库修改配置、技能、脚本或文档。
2. 运行语法检查、安全扫描和 Git 状态检查。
3. Windows 上 Hermes terminal 默认是 Git-Bash/MSYS；需要 PowerShell 时优先显式使用 PowerShell 7：`pwsh -NoProfile -Command ...`，只有旧模块/COM/Desktop edition 兼容问题才回退 `powershell.exe` 5.1。
4. 用 conventional commit 提交。
5. 推送到 GitHub。
6. 新电脑 clone 后执行 `setup.ps1` 或 `setup.sh`，再手动补齐本机私密凭证和 OAuth。
7. 对 live Hermes Home 做同步时优先使用 `scripts/workflow/sync_hermes_workflow_assets.py --apply`，不要全量覆盖真实 `.env`、auth、session、logs。

## 目标状态

这个项目的目标不是“只备份配置”，而是逐步成为 DTALEX66 的 Agent 工作流中枢：

- Hermes：稳定模型/provider/MCP/skills 配置。
- CC Switch：稳定代理与网络路径。
- Codex：稳定 GPT OAuth 与 coding-agent 协作路径。
- Workflow：把可复用经验沉淀为脚本、模板、技能和排错手册。
- Sync：让 repo、GitHub、live Hermes Home 之间形成可审计、可回滚、可复验的闭环。
