# 项目定义：HERMES + CC Switch + Codex 工作流增强项目

## 一句话定位

`Workflow-assistance` 是 DTALEX66 的 **HERMES + CC Switch + Codex 工作流增强项目**：用于沉淀、迁移和持续强化 Hermes Agent 在 Windows / GitHub / Codex / CC Switch 环境下的配置、技能、MCP、排错经验、验证脚本和自动化工作流。

## 项目边界

本项目保存的是“工作流增强资产”，不是任何运行时主体的安装包：

- 不包含 Hermes Agent 安装主体。
- 不包含 CC Switch 安装主体。
- 不包含 Codex CLI / ChatGPT OAuth 的真实凭证。
- 不提交 `.env`、`auth.json`、API Key、Token、会话数据库、缓存或日志。

## 三层职责

| 层级 | 责任 | 本仓库沉淀内容 |
|---|---|---|
| Hermes Agent | Agent 运行、模型/provider、工具、技能、MCP、记忆与会话 | `config/`、`skills/`、`bin/hermes-npx*`、Hermes doctor/切换脚本 |
| CC Switch | 本地代理、网络通道、Agent 生态辅助 | 代理环境变量模板、排错手册、与 Hermes/Codex 协作约定 |
| Codex / OpenAI OAuth | GPT 订阅/OAuth 路线、Codex CLI/工作流协作 | OAuth 流程说明、任务单模板、`CODEX.md`/Agent rules 模板 |

## 当前同步状态

截至 2026-07-04，本项目已完成 GitHub 云端、本地仓库与 live Hermes Home 的三层互验：

- 本地仓库：`D:\All projects\Workflow-assistance`
- 云端仓库：`https://github.com/DTALEX66/Workflow-assistance`
- live Hermes Home：`C:\Users\admin\AppData\Local\hermes`
- Git 状态：本地 `main` 与 `origin/main` 同步，工作区干净。
- live provider/model：保留当前 Hermes 运行配置，不由仓库模板强行覆盖。
- 默认 MCP：`public-apis`、`sequential-thinking`、`context7` 已完成 smoke test。

## 可迁移资产清单

| 资产 | 仓库位置 | live Hermes 目标 | 说明 |
|---|---|---|---|
| Hermes 配置模板 | `config/config.yaml` | `config.yaml` | 新机器基线；同步脚本合并时保留 live provider/model |
| 环境变量模板 | `config/.env.template` | `.env.template` | 只放占位说明，不放真实密钥 |
| MCP wrapper | `bin/hermes-npx*` | `bin/hermes-npx*` | Windows live config 指向 `.cmd`；优先 bundled Node，缺失时可回退 PATH Node >=20 |
| 技能 | `skills/` | `skills/` | 包含 model-switch、python-testing、windows-development-environment、screenlingua、agent-workflow-fortress |
| 同步脚本 | `scripts/workflow/sync_hermes_workflow_assets.py` | 手动运行 | repo ↔ live 定向同步；每次 apply 前备份可迁移资产 |
| 排错记录 | `TROUBLESHOOTING.md`、`docs/workflow/error-fixes-2026-07-04.md` | 仓库文档 | 记录 Windows MCP、路径、GitHub CLI、验证等已踩坑 |

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
hermes mcp test public-apis
hermes mcp test sequential-thinking
hermes mcp test context7
```

如果只改同步脚本且没有完整测试套件，应创建 `C:\Users\admin\AppData\Local\Temp\hermes-verify-*` 临时脚本做隔离 ad-hoc 验证，并在运行后清理。

## 标准闭环

1. 在本地仓库修改配置、技能、脚本或文档。
2. 运行语法检查、安全扫描和 Git 状态检查。
3. 用 conventional commit 提交。
4. 推送到 GitHub。
5. 新电脑 clone 后执行 `setup.ps1` 或 `setup.sh`，再手动补齐本机私密凭证和 OAuth。
6. 对 live Hermes Home 做同步时优先使用 `scripts/workflow/sync_hermes_workflow_assets.py --apply`，不要全量覆盖真实 `.env`、auth、session、logs。

## 目标状态

这个项目的目标不是“只备份配置”，而是逐步成为 DTALEX66 的 Agent 工作流中枢：

- Hermes：稳定模型/provider/MCP/skills 配置。
- CC Switch：稳定代理与网络路径。
- Codex：稳定 GPT OAuth 与 coding-agent 协作路径。
- Workflow：把可复用经验沉淀为脚本、模板、技能和排错手册。
- Sync：让 repo、GitHub、live Hermes Home 之间形成可审计、可回滚、可复验的闭环。
