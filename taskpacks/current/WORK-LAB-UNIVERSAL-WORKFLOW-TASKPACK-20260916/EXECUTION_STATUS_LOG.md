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

### NF-08-A | PASS(可自执行片) | INTEGRATION | pending | 2026-09-16
- 可自执行片已闭环：
  * `packages/client-neutral-core/scripts/publish_planner.py`：发布规划 + 逐动作权限审计（纯函数，无网络、不读凭据）。
    材料分级路由存储目标 / 大正文先固定版本工件再摘要+引用 / 逐动作写权核对（push≠全动作）/ 回读校验 / 幂等 / 公开目标拒收私人 canary。
  * `tests/workflow-assistance/nf08_a_publish_planner.py` 21/21 全绿（AT-11/12/13 合成片）。
- 真实外部片（BLOCKED，精确依赖）：真实服务端写 + 回读需目标空间发布权限与用户对这批材料外发的授权；未获写权停在 PUBLISH_PENDING_AUTHORIZATION，不称同步成功。

### NF-08-B | PASS(可自执行片) | INTEGRATION | pending | 2026-09-16
- 可自执行片已闭环：
  * `packages/client-neutral-core/scripts/durable_inbox.py`：复用既有 TaskLedger 持久化边界（ledger.json + 原子 os.replace + orphan 恢复 + 租约 fence），未新增独立队列库。
    inbox/outbox/认领/命名空间可暂停/事件身份去重/条件请求+Retry-After/先持久化认领意图再调执行器/恢复对账不重起/内容不变不重写工件。
  * `tests/workflow-assistance/nf08_b_durable_inbox.py` 12/12 全绿（AT-14/15/16/17 合成片：跨进程不重起、并发单派发、A故障不阻B、同步检查不调用模型、工件不重复写）。
- 真实外部片（BLOCKED）：真实订阅需项目/节点接入授权；持久化限当前批准根；多机不复制活动 ledger 做多主。

### NF-05-SYNC | PASS(可自执行片) | INTEGRATION | pending | 2026-09-16
- 可自执行片已闭环：
  * `packages/client-neutral-core/scripts/capability_roles.py`：客户端能力按角色登记 + 探针驱动（非固定七项 enum）。
    角色语义分区 planner/executor/reviewer/storage/observer；能力=探针确认的动态集合；GitHub/CC Switch 按真实角色登记、无 execute 探针即不可当执行者；同一 adapter_id 被两项目复用（分发键=adapter 非项目名，无按名分派）；缺 Hermes 其它执行器仍可用（按能力选执行器）；缺接口=PARTIAL/UNSUPPORTED+补齐前提，不报"全功能完成"。
  * `tests/workflow-assistance/nf05_capability_roles.py` 12/12 全绿（AT-18/19/20 合成片）。
- 真实外部片（BLOCKED）：真实客户端探针/启动需原生会话许可与对应授权；元数据探针≠付费调用。

### NF-08-C | PASS(可自执行片) | INTEGRATION | pending | 2026-09-16
- 可自执行片已闭环：
  * `packages/client-neutral-core/scripts/dispatch_contract.py`：分派到执行的合同（不再停在交接模拟）。
    分派前冻结 task/revision/baseline/执行者/授权引用+解析本机工作区；脏工作树不自动 pull/reset；记录启动前意图+真实 run/session ID+实际指令源（非 --last）；低风险确定性先跑、Agent 任务需费用授权否则 HOLD、假执行器仅算契约证据；换执行者先确认旧运行体 COMPLETED/PAUSED 只交剩余工作；启动失败分层归因（transport/permission/runtime/model，不阻其它项目）；exit 0 或模型 DONE 不算验收全部通过。
  * `tests/workflow-assistance/nf08_c_dispatch_contract.py` 12/12 全绿（AT-11/18/21 合成片）。
- 真实外部片（BLOCKED）：真实原生执行器启动+模型费用授权；不自动获得 commit/push/merge；不拼接远端 shell。