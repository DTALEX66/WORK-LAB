# 执行状态日志 — WORK-LAB-UNIVERSAL-WORKFLOW-TASKPACK-20260916

**性质**：append-only 状态账本（不重写历史）。每卡一条记录，格式：
`### NF-xx-SYNC | <status> | <evidence-level> | <commit> | <date>`。
**执行边界**：可自执行片（仓内契约/设计/合成+多进程测试/CI/规则澄清/账本）做到闭环；
真实外部副作用片（真实云端发布、第二真实项目、第二执行软件、真实双环境、付费模型）
建好代码 + 合成证据后诚实标 `BLOCKED` + 精确依赖，绝不伪造 PASS。
**基线**：`r4-recovery-exec @ de2f3fd`；main `e5231f0`（不合并、不重开历史）。

---

### NF-00-SYNC | PASS(可自执行片) | DOCUMENT_CHECK | pending | 2026-09-16
- 状态：锁卡完成。范围更正 + UNIVERSAL 包登记进 authority-index；4 类范围区分（WORK-LAB
  代码开发 / 目标项目接入 / 远端发布 / 本机部署）已记录；20 个旧父卡承接去向已在
  TASKS.json carry_forward 固化（15 续 + 4 条件项 deferred）。
- 真实外部片（BLOCKED，精确依赖）：真实"目标项目接入 + 远端发布目标"落地需用户对
  具体目标项目与发布空间的接入授权（本包 `grants_new_permissions=false`）。锁卡本身不授权。
- 证据：`taskpack-authority-index.json` 新增 `universalWorkflowPack` 段 + 本记录。

### NF-01-SYNC | PASS(可自执行片) | INTEGRATION | pending | 2026-09-16
- 可自执行片已闭环：
  * 纯函数模块 `packages/client-neutral-core/scripts/artifact_flow_policy.py`
    （5 决策路径 ALLOW/PENDING_AUTHORIZATION/ISOLATE/REJECT + 嵌套秘密检测 + 项目偏好 scoping）。
  * `tests/workflow-assistance/nf01_rule_semantics_artifact_flow.py` 18/18 全绿（gate-direct）。
  * `docs/decisions/global-execution-standard.md` 追加 §七 dated 澄清（不改 5 维原义、不新增全局限速）。
  * `.project/governance/project-data-boundary.json` append-only 增加 artifactFlowSemantics（既有键全部保留）。
- 真实外部片（BLOCKED，精确依赖）：AT-02「同一全局规则部署到两种真实软件真实回读」需对应软件写权限授权；本卡不伪造 PASS。


### NF-03-SYNC | PASS(可自执行片) | INTEGRATION | pending | 2026-09-16
- 可自执行片已闭环：
  * 纯函数模块 `packages/client-neutral-core/scripts/project_binding_registry.py`
    （稳定不透明 project_id + 可选 repo 关联 + git/artifact 基线 + 材料位置/能力白名单
     + 本机 root binding overlay + 云端路径拒绝 + 同名不串 + 未知 ID fail-closed）。
  * `tests/workflow-assistance/nf03_project_binding_registry.py` 15/15 全绿（gate-direct）。
- 覆盖 AT-05（同名同任务号隔离）/ AT-06（换设备路径重绑定只信本机 binding）/ AT-07（第三非 Git 项目仅配置接入）的合成可自执行片。
- 真实外部片（BLOCKED，精确依赖）：真实目标项目与路径需用户对该项目的接入授权；合成项目限定当前批准测试根。非 Git 项目的原生执行限制须对真实执行软件诚实标注。

### NF-08-0 | PASS(可自执行片) | INTEGRATION | pending | 2026-09-16
- 兼容扩展交接格式（增量，未造第二套权威格式）：
  * `packages/client-neutral-core/scripts/handoff_envelope.py`：v2 信封（登记驱动项目引用 + 源/目标软件分离 + 环境绑定 + 任务修订号 + 基线种类 git/artifact + 不可变摘要 + receipt 位置 + 目标能力 + 授权引用 + supersedes 链）。
  * `.project/governance/federation/federation-envelope.v2.schema.json`：v2 schema，v1 schema 原样保留供旧读取方。
  * `tests/workflow-assistance/nf08_0_handoff_envelope_v2.py` 18/18 全绿：v1 可读、v2 显式拒绝 v1 不静默截断、项目ID≠客户端ID、同任务同修订不同摘要=冲突不覆盖、高修订走 supersede 链不合并、迟到低修订结果保留待审不推进、授权只信本地可信授权记录（payload 自声明忽略）、Ready 指针仅在不可变快照完整后发布、v1→v2 迁移未登记引用 fail-closed。
- 真实外部片（BLOCKED）：真实项目间跨机交接需对目标项目授权 + 真实环境节点；本地授权记录/注册表需对真实软件配置面消费。