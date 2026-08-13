# Active Authority Index

> WLG-110 · WORK-LAB Global Config Governance DeDup TaskPack (2026-08-13)
>
> 每个规则只有一个规范来源；其他文件必须是引用或标注 `superseded`/`archive`。

## 1. 活跃权威（Active — 唯一规范来源）

| 领域 | 权威文件 | 角色 |
|---|---|---|
| 字段级配置所有权 | `config/config-ownership.json` | 唯一字段权威（`single_authority: true`） |
| 外部项目端点 | `config/project-profiles.json` | 只读端点声明（地址 + 协议元数据） |
| 项目 profile 合同 | `schemas/workflow/project-profile.schema.json` | 外部项目声明 schema |
| Gate 计划合同 | `schemas/workflow/gate-plan.schema.json` | 计划合同 |
| Gate 注册合同 | `schemas/workflow/gate-registry.schema.json` | 语义 gate 注册 |
| Task Ledger 真值 | `scripts/workflow/task_ledger.py` | WORK-LAB 自身任务真值 |
| 全局 runner | `scripts/workflow/run_taskpack_agent.py` | 唯一全局 TaskPack runner |
| 全局验证层 | `scripts/workflow/gate_vocabulary.py` | 全局 tier 词汇（TARGETED/STAGE/NIGHTLY/RC/RELEASE） |
| 全局 hash 预算 | `scripts/workflow/hash_budget.py` | 三层 digest 预算 |
| 审计触发 | `scripts/workflow/audit_triggers.py` | 全仓审计触发去重 |
| Apply 安全 | `scripts/workflow/apply_safety.py` | plan→diff→approval→backup→apply→readback→rollback |
| 官方基准 | 各客户端官方配置 | 官方 schema 优先，不可被 overlay 覆盖 |

## 2. 兼容/参考（Compatible — 引用权威，不重复定义）

- `docs/workflow/official-plus-user-configuration-standard.md`：只解释 `config-ownership.json`，不重复字段表。
- `docs/workflow/managed-software-and-assets.md`：受管软件/资产清单，引用字段权威。
- `docs/workflow/examples/governance.yml.example`：documented example，非活跃 CI（WLG-080）。

## 3. 已取代/历史（Superseded / Archive）

- 历史 handoff 与审计：`docs/handoffs/`、`docs/audit/` 中带日期的交接文档（如
  `workflow-baseline-and-recovery-handoff-2026-08-13.md`）记录当时状态，**不构成当前规范**。
- `90-archive-manifests/`：跨机迁移、旧产品（minigame）、历史状态清单。
- 历史 taskpacks：`50-taskpacks/` 中 `*-COMPLETE.md` 与 `*-20260812.md` 为完成记录，不重复
  当前测试数量/SHA/中间失败。
- `CODEX-DESKTOP-STORE-UPDATE-BEHAVIOR-20260812.md`：历史调查记录，部分表述已由
  `codex-desktop-update-state-investigation-2026-08-13.md` 降级，仅作归档。

## 4. README 链接规则

- README 只链接权威文件（上表 Active 列），不链接历史记录。
- 新增权威文件时必须登记到本索引；历史文件不得回链为规范来源。
- 归档操作：移入 `90-archive-manifests/`（保留 Git 历史），不删除。
