# Workflow-assistance 受管软件与内容清单

> 生效基准：main `a2c51a3` + open-design skill（PR #55 合并后更新 SHA）
> 本文档是增强模块的**管理面总账**：列出 Workflow-assistance 管理哪些软件（平台/客户端）以及各自管理什么内容。所有权语义以 `config/config-ownership.json` 为唯一权威，部署以 `workflow-manifest.yaml` 为准。

## 1. 受管软件（适配器与平台）

| 软件 | 角色 | 支持级 | 管理方式 | 所有权 |
|---|---|---|---|---|
| **Hermes** | 主动客户端（执行面） | deep | 受管 skills/bin/SOUL/.env.template 同步到 live Home | USER_OVERLAY / MANAGE |
| **Codex** | 主动客户端（执行面） | deep | 全局 guidance overlay、rules、11 个 user skills、3 个受管 config 字段 | USER_OVERLAY / MANAGE |
| **CC Switch** | provider 路由客户端 | deep | 只读观察 provider catalog/routing；codex.skill_sync 等平台内部同步 IGNORE | USER_OVERLAY / OBSERVE |
| **GitHub** | 交付通道 | deep | 6 个 Hermes github skills、Codex github-delivery skill、CI（work-lab-gate）、gh 认证 | USER_OVERLAY / OBSERVE |
| **OpenHuman** | 本地 AI 桌面代理（观察源） | experimental | 全局配置/注册归 WORK-LAB MANAGE；openhuman-integration skill（私有边界 + junction 验证阶梯）；workspace_metadata OBSERVE、runtime_memory IGNORE | PLATFORM_INTERNAL / OBSERVE |
| **Open Design** | 已迁出独立库（只读观察） | experimental | 全局配置/迁移指针/注册归 WORK-LAB MANAGE；open-design-integration skill（迁移边界 + 主张验证）；内部设计资料不动；read_only_mcp OBSERVE | PROJECT_OVERLAY / OBSERVE |
| **Cursor** | 未来客户端（未接入） | manifest-only | 仅清单登记，无写入 | USER_OVERLAY / OBSERVE |
| **Claude Code** | 未来客户端（未接入） | manifest-only | 仅清单登记，无写入 | USER_OVERLAY / OBSERVE |
| **WorkBuddy** | 未来客户端（未接入） | manifest-only | 仅清单登记，无写入 | USER_OVERLAY / OBSERVE |
| **Workflow** | 增强模块自身 | — | 管理自己的 memory.growth_policy、task 租约/检查点、cache/logs 边界 | USER_OVERLAY / MANAGE |

## 2. 受管内容（资产清单）

### 2.1 Codex 用户 overlay（`~/.codex` + `~/.agents`）

| 资产 | 位置 | 数量 |
|---|---|---|
| 全局 guidance | `~/.codex/AGENTS.md`（WORK-LAB managed block） | 1 |
| 全局 rules | `~/.codex/rules/workflow-assistance.rules` | 1 |
| 用户 skills | `~/.agents/skills/workflow-assistance-*` | 11 |
| 受管 config 字段 | `config.toml` managed block：`approval_policy` `sandbox_mode` `project_doc_max_bytes` | 3 |
| overlay state | `~/.codex/.workflow-assistance-state.json` | 1 |

11 个 skills：

```text
workflow-assistance-evidence-verification
workflow-assistance-github-delivery
workflow-assistance-openhuman-integration
workflow-assistance-open-design-integration   ← 2026-08-11 新增
workflow-assistance-project-data-boundary
workflow-assistance-python-testing
workflow-assistance-safe-project-execution
workflow-assistance-self-improvement
workflow-assistance-single-writer-delivery
workflow-assistance-systematic-debugging
workflow-assistance-windows-development
```

### 2.2 Hermes 受管资产（`C:\Users\<user>\AppData\Local\hermes`）

| 资产 | 数量 |
|---|---|
| 受管 skill roots（13 个：autonomous-ai-agents/codex、github/* 5、model-switch、software-development/* 6） | 13 |
| 受管 launcher/bin（codex、hermes-npx、hermes-project-data.py、terminal-guard 等） | 6 |
| `SOUL.md`（managed mapping） | 1 |
| `.env.template` | 1 |

### 2.3 仓库侧权威资产（`10-workflow/workflow-assistance/`）

| 资产 | 路径 |
|---|---|
| 所有权合同 | `config/config-ownership.json` |
| 隔离空 home 兼容配方 | `config/managed-config-schema.yaml` |
| Codex overlay 源 | `codex-assets/global-guidance.md`、`codex-assets/rules/`、`codex-assets/skills/`（11） |
| 部署清单 | `workflow-manifest.yaml` |
| 同步器 | `scripts/workflow/sync_codex_global_assets.py`、`sync_hermes_workflow_assets.py` |
| 边界合同 | `config/codex-enhancement-boundary.json` |
| 性能诊断 | `docs/workflow/codex-performance-diagnosis.md` |
| 执行可靠性 | `docs/workflow/codex-execution-reliability.md` |
| 配置标准 | `docs/workflow/official-plus-user-configuration-standard-2026-08-11.md` |

## 3. 硬边界（所有软件一律适用）

```text
SECRET（credentials/api_keys/auth_tokens/oauth_state/prompt_response_bodies）→ FORBIDDEN
RUNTIME_EPHEMERAL（sessions/cache/logs/openhuman.runtime_memory/codex.local_memories）→ IGNORE
PLATFORM_INTERNAL（desktop 状态/openhuman 元数据/cc-switch 平台同步）→ OBSERVE
```

- 不读取、复制、哈希或归档任何凭据/密钥/正文；
- 不跨客户端同步 prompt/skill/session/memory（`cross_client_prompt_skill_session_sync_forbidden`）；
- `E:\` 全盘保护；`~/.codex/memories/**`、`~/.openhuman/**` 私有运行时禁读；
- 用户 provider/model/认证/Desktop 状态属于用户，增强模块只观察不接管；
- **Open Design / OpenHuman 分层**：两者的全局配置（注册、迁移指针、目录映射、MCP 声明）归 WORK-LAB 增强模块 MANAGE；被切割的 Open Design 内部设计资料与两个平台的私有运行时（`~/.openhuman/**`、Open Design 远端库内容）一律不读不动。
- **Open Design 能力边界**（`open_design_capability_owned_by_open_design_project`）：任何能提升设计能力的配置——模型/工具选择、生成参数、设计资产、设计规范——属于 Open Design 项目本身（`DTALEX66/OPEN-DESIGN-Assistance`），本项目不采集、不管理、不 sync；WORK-LAB 只管理非设计性质的全局配置（指针/注册/映射/MCP 声明/审计边界）。

## 4. 变更与同步流程

1. 改仓库权威资产（skills/rules/guidance/合同）；
2. 跑 `sync_codex_global_assets.py apply|verify`（Codex 侧）与 `sync_hermes_workflow_assets.py --apply --approved`（Hermes 侧）；
3. 重新生成 `CURRENT_STATE`（`scripts/ci/generate_current_state.py --root .`）；
4. 更新本清单与 error-ledger；提交、PR、exact-SHA CI、合并；
5. 合并后再回读 live verify，报告 `SOURCE_EQUIVALENT + ENABLED + BEHAVIORALLY_APPLIED` 分层证据。

## 5. 当前状态（2026-08-11）

```text
Codex overlay:   11 skills · verify PASS · issues=[]
Hermes live:     source==live hash 一致（bin + skills）
CC Switch:       127.0.0.1:15721 运行中 · Codex 经 cc-switch-official 端到端 PASS
GitHub:          gh 已登录 DTALEX66 · CI 5 jobs 全绿（main 精确 SHA）
OpenHuman:       skill 已载入 · 跨项目实测可引用
Open Design:     skill 已载入（PR #55）· 跨项目实测可引用
```
