# 项目定义：HERMES + CC Switch + Codex 工作流增强项目

## 一句话定位

`Workflow-assistance` 是 DTALEX66 的 **HERMES + CC Switch + Codex 工作流增强项目**：用于沉淀、迁移和持续强化 Hermes Agent 在 Windows / GitHub / Codex / CC Switch 环境下的配置、技能、MCP、排错经验和自动化工作流。

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

## 本地项目定义

- 本地路径：`D:\All projects\Workflow-assistance`
- 本地角色：可编辑、可验证、可提交的工作流增强资产源目录。
- 本地操作原则：先检查 → 小步修改 → 语法/安全验证 → commit → push。

## GitHub 云端项目定义

- 云端仓库：`https://github.com/DTALEX66/Workflow-assistance`
- 云端角色：跨电脑同步的 HERMES + CC Switch + Codex 工作流增强资产库。
- 云端应保持：README 定位清晰、部署命令指向 `Workflow-assistance`、topics/description 能反映 Hermes、CC Switch、Codex、workflow automation。

## 标准闭环

1. 在本地仓库修改配置、技能、脚本或文档。
2. 运行语法检查、安全扫描和 Git 状态检查。
3. 用 conventional commit 提交。
4. 推送到 GitHub。
5. 新电脑 clone 后执行 `setup.ps1` 或 `setup.sh`，再手动补齐本机私密凭证和 OAuth。

## 目标状态

这个项目的目标不是“只备份配置”，而是逐步成为 DTALEX66 的 Agent 工作流中枢：

- Hermes：稳定模型/provider/MCP/skills 配置。
- CC Switch：稳定代理与网络路径。
- Codex：稳定 GPT OAuth 与 coding-agent 协作路径。
- Workflow：把可复用经验沉淀为脚本、模板、技能和排错手册。
