# Workflow-assistance 受管软件与内容清单

> 本文档记录受管面与运行时审计口径，不替代当前 Git SHA、精确 CI 或逐机 readback。软件版本
> 更新由用户或官方稳定版渠道决定；WORK-LAB 只在用户明确授权的升级后故障场景恢复自己拥有的
> 工作流资产。
> 本文档是增强模块的**管理面总账**：列出 Workflow-assistance 管理哪些软件（平台/客户端）以及各自管理什么内容。所有权语义以 `config/config-ownership.json` 为唯一权威，部署以 `workflow-manifest.yaml` 为准。

## 1. 受管软件（适配器与平台）

| 软件 | 角色 | 支持级 | 管理方式 | 所有权 |
|---|---|---|---|---|
| **Hermes** | 主动客户端（执行面） | deep | 受管 skills/bin/SOUL/.env.template 同步到 live Home | USER_OVERLAY / MANAGE |
| **Codex** | 主动客户端（执行面） | deep | 全局 guidance overlay、rules、14 个 user skills、3 个受管 config 字段 | USER_OVERLAY / MANAGE |
| **CC Switch** | provider 路由客户端 | deep | 只读观察 provider catalog/routing；codex.skill_sync 等平台内部同步 IGNORE | USER_OVERLAY / OBSERVE |
| **GitHub** | 交付通道 | deep | 6 个 Hermes github skills、Codex github-delivery skill、CI（work-lab-gate）、gh 认证 | USER_OVERLAY / OBSERVE |
| **OpenHuman** | 本地 AI 桌面代理（观察源） | experimental | 仅管理合同明确声明的非私有全局配置；观察 workspace_metadata；openhuman-integration skill 提供私有边界与 junction 验证阶梯 | PLATFORM_INTERNAL / OBSERVE |
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
| 用户 skills | `~/.agents/skills/workflow-assistance-*` | 14 |
| 受管 config 字段 | `config.toml` managed block：`approval_policy` `sandbox_mode` `project_doc_max_bytes` | 3 |
| overlay state | `$CODEX_HOME/.workflow-assistance-state.json` | 1 |

14 个 skills：

```text
workflow-assistance-evidence-verification
workflow-assistance-github-delivery
workflow-assistance-observer-delivery
workflow-assistance-openhuman-integration
workflow-assistance-open-design-integration   ← 2026-08-11 新增
workflow-assistance-project-data-boundary
workflow-assistance-python-testing
workflow-assistance-safe-project-execution
workflow-assistance-self-improvement
workflow-assistance-single-writer-delivery
workflow-assistance-systematic-debugging
workflow-assistance-update-safety
workflow-assistance-verification-hardening
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

## 4. 变更、同步与升级后恢复流程

1. 改仓库权威资产（skills/rules/guidance/合同）；
2. 对 live 资产先生成并审阅 ActionPlan。用户明确批准后，运行 `sync_codex_global_assets.py apply|verify`（Codex 侧）或 `sync_hermes_workflow_assets.py --apply --approved`（Hermes 侧）；
3. 重新生成 `CURRENT_STATE`（`scripts/ci/generate_current_state.py --root .`）；
4. 更新本清单与 error-ledger；提交、PR、exact-SHA CI、合并；
5. 合并后再回读 live verify，报告 `SOURCE_EQUIVALENT + ENABLED + BEHAVIORALLY_APPLIED` 分层证据。

日常官方软件更新不在此流程内。若用户升级后发现受管工作流失效，先只读分类为官方 runtime、受管 overlay、用户 overlay、未知/隔离字段或外部项目问题；只允许对本清单明确拥有的资产进行用户批准后的最小恢复。不得把官方安装、Provider/模型、认证、会话、Desktop 私有状态或 Open Design 设计能力当作恢复目标。

## 5. 历史状态快照（2026-08-11）

```text
Codex overlay:   当时记录的历史数量；当前受管集合以机器合同和 verify 输出为准
Hermes live:     当时的单机观察；不得外推为其它电脑或未来版本的事实
CC Switch:       127.0.0.1:15721 运行中 · Codex 经 cc-switch-official 端到端 PASS
GitHub:          gh 已登录 DTALEX66 · CI 5 jobs 全绿（main 精确 SHA）
OpenHuman:       skill 已载入 · 跨项目实测可引用
Open Design:     skill 已载入 · 跨项目实测可引用
```

## 6. 五维运行时基线（审计标准，2026-08-11 起强制）

见 `AGENTS.md`「Five-dimension runtime baseline」。本清单登记各软件快照：

| 维度 | Hermes | Codex | CC Switch | OpenHuman | Open Design |
|---|---|---|---|---|---|
| 入口唯一 | 官方 GUI 入口 + `hermes` CLI；实际目标逐机回读 | bash+cmd 单一 wrapper（版本目录 glob 一致） | 桌面 .lnk→cc-switch.exe | 已安装时桌面 .lnk→官方 exe | 桌面 .lnk→Open Design.exe |
| 桌面可达 | 逐机 Test-Path 链路回读 | CLI 无 GUI（官方形态，入口唯一） | 逐机回读 | 未安装为 N/A，不伪造通过 | 逐机回读 |
| 官方标准+用户配置 | config-ownership MANAGE 受管字段 | overlay 3 字段，用户字段 preserve | OBSERVE，catalog/routing MANAGE | 全局配置 MANAGE/私有 IGNORE | 非设计配置 MANAGE/设计能力 IGNORE |
| 无阻塞 | 受管 skills 按需加载；实际大小逐机核验 | 14 个受管 skills；大小和按需加载逐机核验 | 代理超时与运行状态逐机核验 | N/A 或逐机核验 | N/A 或独立项目核验 |
| 模型满血 | 用户/官方模型配置：只读观察，不自动调参 | Provider/model 路由属用户；不自动覆盖 | 官方路由由其自身负责；只读观察 | N/A | 设计能力属独立项目，不在此审计范围 |

审计命令：桌面快捷方式 `Test-Path` 全链；wrapper `--version`；`config-ownership.json` 字段层校验；skills 体积 `du -sh`；模型 `reasoning_effort` grep + CC Switch proxy_config 检查。
