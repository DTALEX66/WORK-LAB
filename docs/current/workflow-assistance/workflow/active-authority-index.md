# Active Authority Index

> **NON-AUTHORITY VIEW** — 本文件是只读分类索引，不是第二顶层 Authority。
>
> **Top authority = `/WORK-LAB-AUTHORITY.md`**
> Machine authority = `.project/governance/project-authority-index.json`
> 本文件仅供快速导航；若与上述两份冲突，以上述两份为准。

## 1. 活跃权威（Active — 唯一规范来源）

| 领域 | 权威文件 | 角色 |
|---|---|---|
| 字段级配置所有权 | `config/config-ownership.json` | 唯一字段权威（`single_authority: true`） |
| 外部项目端点 | `config/project-profiles.json` | 只读端点声明（地址 + 协议元数据） |
| 项目 profile 合同 | `packages/contracts/schemas/workflow/project-profile.schema.json` | 外部项目声明 schema |
| Gate 计划合同 | `packages/contracts/schemas/workflow/gate-plan.schema.json` | 计划合同 |
| Gate 注册合同 | `packages/contracts/schemas/workflow/gate-registry.schema.json` | 语义 gate 注册 |
| Task Ledger 真值 | `packages/client-neutral-core/scripts/task_ledger.py` | WORK-LAB 自身任务真值 |
| 全局 runner | `services/orchestration/run_taskpack_agent.py` | 唯一全局 TaskPack runner |
| 全局 gate 词汇 | `services/policy/gate_vocabulary.py` | 全局 tier 词汇（TARGETED/STAGE/NIGHTLY/RC/RELEASE） |
| 全局 hash 预算 | `services/policy/hash_budget.py` | 三层 digest 预算 |
| 审计触发 | `packages/client-neutral-core/scripts/audit_triggers.py` | 全仓审计触发去重 |
| Apply 安全 | `services/policy/apply_safety.py` | plan→diff→approval→backup→apply→readback→rollback |
| 官方基准 | 各客户端官方配置 | 官方 schema 优先，不可被 overlay 覆盖 |

## 2. 兼容/参考（Compatible — 引用权威，不重复定义）

- `docs/current/workflow-assistance/workflow/official-plus-user-configuration-standard.md`：只解释 `config-ownership.json`，不重复字段表。
- `docs/current/workflow-assistance/workflow/managed-software-and-assets.md`：受管软件/资产清单，引用字段权威。
- `docs/current/workflow-assistance/workflow/examples/governance.yml.example`：documented example，非活跃 CI（WLG-080）。

## 3. 已取代/历史（Superseded / Archive）

- 历史 handoff 与审计：`docs/handoffs/`、`docs/audit/` 中带日期的交接文档（如
  `workflow-baseline-and-recovery-handoff-2026-08-13.md`）记录当时状态，**不构成当前规范**，
  仅作归档。
- `taskpacks/history/`：完成 taskpack、旧 release、dated closure。
- `docs/history/archive/session-history/`：跨机迁移、旧产品（minigame）、历史状态清单。
- `CODEX-DESKTOP-STORE-UPDATE-BEHAVIOR-20260812.md`：历史调查记录，部分表述已由
  `codex-desktop-update-state-investigation-2026-08-13.md` 降级，仅作归档。

## 4. README 链接规则

- README 只链接权威文件（上表 Active 列），不链接历史记录。
- 新增权威文件时必须登记到本索引；历史文件不得回链为规范来源。
- 归档操作：移入 `taskpacks/history/` 或 `docs/history/`（保留 Git 历史），不删除。
