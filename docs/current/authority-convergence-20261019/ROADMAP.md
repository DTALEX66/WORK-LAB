# WORK-LAB 收敛版路线图（2026-10-19）

本路线图替代此前过度扩张的未来愿景，不删除历史资料。它是规划与状态视图，不是第二 Authority，
也不是新的任务账本；当前任务真值仍是 `taskpacks/current/OPEN-TASK-REGISTER.md`，当前计划是
`taskpacks/current/WORK-LAB-AUTHORITY-CONVERGENCE-TASKPACK-20261019.md`。

权威链：最新明确用户决定 > `WORK-LAB-AUTHORITY.md` > `.project/governance/project-authority-index.json`
> 当前任务包与唯一 open register > `AGENTS.md` 与作用域合同 > exact-SHA 代码/CI/运行读回 > 冻结历史。

## CURRENT — 当前主线

当前主线优先交付**一个真实最小问题闭环**，不以模拟数据、Agent 自述或单一退出码冒充接通。
下列条目的“现状”是 2026-10-19 对仓库的只读核对结果。用户 2026-10-19 指令
“执行所有未完成的任务，按照最新发你的任务包”作为具体 Task Grant，只授权并交付了第 9 项
（一个真实最小问题闭环，ML-001）；第 2-8 项作为系统能力仍**未获得实施授权**。

| 次序 | 当前条目 | 现状（2026-10-19） | 证据/缺口 |
| --- | --- | --- | --- |
| 1 | 权威定位、职责边界和路线图收敛 | 本次交付（文档） | 本文件、`WORK-LAB-AUTHORITY.md`、`docs/current/authority-convergence-20261019/AUTHORITY-CONVERGENCE-20261019.md` |
| 2 | 真实数据源接入；Observer 诚实呈现状态、错误、阻塞、来源、时间、新鲜度与 UNKNOWN | PARTIAL：仓内有有界 collector、Snapshot v3 与只读 Observer；未证明所有受管客户端端到端 LIVE | `packages/client-neutral-core/scripts/collectors.py`、`packages/client-neutral-core/scripts/snapshot_api.py`、`apps/observer`；缺口见收敛报告能力映射 |
| 3 | 问题中心：去重、分类、优先级、项目/软件/版本关联、关键日志和处理状态 | NOT_IMPLEMENTED | 仓库中没有 issue-center 模块或 Observer 问题视图；缺口由本次只读检索记录在收敛报告 |
| 4 | 问题摘要与 Agent 修复任务包生成；优先可靠人工交接，只有已验证连接才允许自动派发 | PARTIAL：通用 TaskPack runner 与任务协议存在，但没有从问题摘要生成修复包的通路 | `services/orchestration/run_taskpack_agent.py`、`services/task-governance/task_protocol.py`；缺口是 issue→repair 生成器与已核验接口 |
| 5 | 修复状态跟踪与实际结果验证；记录测试、运行读回、版本和失败原因 | PARTIAL：完成权威与证据链存在，未接入问题修复状态机 | `services/task-governance/completion_authority.py`、`services/receipts/evidence_aggregator.py`；缺口是修复生命周期与读回 |
| 6 | 解决方案库最小闭环：成功方案带适用条件、步骤、证据、回滚和失效条件 | NOT_IMPLEMENTED | 没有解决方案库模块或视图；`services/knowledge/promotion_gate.py` 只是知识提升闸门，不是方案库 |
| 7 | AAOS 知识候选出口：只提交精选候选并读取正式接收状态 | FROZEN_20261019（项目联动延后，用户指示）；合同层仍是 CONTRACT_ONLY：候选/回执合同与提升闸门存在，未接通 AAOS API，未读取正式接收状态 | `integrations/archeaxis/contracts/promotion_contract.py`、`services/knowledge/promotion_gate.py`、`services/knowledge/BOUNDARY.md`；冻结不撤销合同，也不声称接收 |
| 8 | 保持 Control/Observer 权限分离，保护用户配置和未提交改动 | SCAFFOLD：Control 是 loopback 写边界，Observer 有只读门；尚无问题/修复写路径 | `services/control/control_service.py`、`scripts/ci/verify_observer_readonly.py`、`scripts/ci/verify_observer_readonly_boundary.py` |
| 9 | 验证一个真实最小闭环，不以模拟数据冒充接通 | DELIVERED（2026-10-19，`WORK-LAB-MINIMAL-LOOP-001`）：AG-06 能力门从红转绿；产品修复 `services/execution-federation/hermes_adapter.py`；12+49 回归测试；适配器 launchable 分支真实读回；固化 `SOLUTION-001`。AAOS 候选 NOT_SUBMITTED，exact-SHA CI 未跑 | 不是外部客户端采集来源，而是仓内可复现的能力门；Hermes 原生会话恢复仍不存在，也未声称存在 |
| 10 | 本仓独立运行跑通（不依赖任何其它项目） | DELIVERED（2026-10-19 实测，非文档）：`services/orchestration/sidecar.py` 在随机回环端口 READY；`/healthz` = `{"ledgerOwner":"workflow-assistance","observerMutation":false,"readOnlyControl":true}`；`/api/v1/snapshot` 200、schema `workflow/snapshot/v3`、152,058 B；同一进程 `--frontend-root apps/observer/frontend/dist` 服务已构建 UI（200）；渲染出的 Observer 读数随快照前进（revision 7→12→17），缺数据保持 UNKNOWN。 | 缺口：一键入口 `apps/observer/start-observer.cmd` 原本指向不存在的路径且写死端口，已修并加守卫 `tests/ci/test_observer_launcher_chain_is_runnable.py`（6 例，种回原缺陷可判红）；Task Ledger 源 `.hermes/task-runtime/task-ledger/ledger.json` [no-tree-claim CLIENT_HOME ref=.hermes/task-runtime/task-ledger/ledger.json] 本机缺失→计数 UNKNOWN；Tauri 桌面 exe 与像素级视觉 QA 本轮未启动 |
| 11 | 快照声明的每一项事实都要有界面消费（不许"后端有、界面不说"） | DELIVERED（2026-10-19 实测）：契约钉住 22 个 v3 键，界面源码此前只消费 20 个——`artifactHandles`/`artifactHandlesSummary` 零消费（快照已发 200 行把手、枚举 5024、省略 4824、敏感名拒 231、剪枝 114、有摘要 40/无摘要 160）。现补证据泳道把手块，并加机器门 `scripts/ci/verify_snapshot_keys_rendered.py` + `tests/ci/test_snapshot_keys_are_rendered.py`（6 例，其中 4 例是"必须能判红"的植入反例；套件自选发现 56 模块含此门）。 | 活链探针实测：按 unrecorded 过滤渲染 160 行=后端 rowsWithoutDigest、行先于事实格、最小计算字号 12px、无内容读取/重试控件、错误过滤值被显式拒绝 |
| 12 | 界面仪器的绿必须带分母，不许把样本说成全量 | DELIVERED（2026-10-20 实测）：`scripts/audit/text_legibility_via_cdp.py` 每条泳道现报 `presentNodes` 与 `sweepStopsUsed`/`sweepStopsNeeded`，缺任一项由 `coverage_was_reported` 判红；新增 `sampled_nodes_stay_within_the_measured_population`（采样数超过页面实际存在的叶子文本即判红），`tests/ci/test_text_legibility_gate.py` 56 例全绿 | 一趟两主题 × 31 泳道实测 46 秒（17:09:39Z→17:10:25Z），报出 sampled 2,933 / present 8,006、sweep_stops 298/564；直接读 DOM 证明把手泳道实有 200 行 / 1,200 个 `data-origin` 格 / 23,031px 列表，而修好滚动后的扫掠只采到 143 个节点；把预算提到能覆盖全量仍未做，等 owner 对作业时长的取舍 |

最小闭环的固定顺序：
`发现 → 去重/关联 → 问题摘要 → 匹配历史方案 → 建议或 Agent 修复任务包 → 用户/授权策略交接 → Agent 实际修复 → 测试与运行读回 → 关闭或继续 → 方案固化 → 必要时 AAOS 知识候选`。
发现、分析、建议、已交接、Agent 声称完成、技术验证通过、方案固化、候选提交、AAOS 接收/审核必须分开记录。

## NEXT — 当前闭环稳定后再考虑

- 按真实需求增加更多软件、Agent、CI 和服务连接器；每个连接器必须有官方接口或可核验读回。
- 提升重复问题聚类和历史方案检索；先做可解释的规则/索引，不把向量库当默认前置。
- 在明确授权、幂等、回滚和验证条件下，对低风险维护动作做有限自动化。
- 解决方案过期检测、版本适用性提醒和回归复验。
- 按需补充成本/Token/资源汇总，只呈现真实可获取的数据；缺失写 UNKNOWN，不补 0。
- 把手摘要的字段进生成 schema（`digest`/`digestSource`、`generatedAt`、`orderingRule`、`cost`、
  `contentIncluded`、`enumerationScope`、`digestIndex` 子键、`order` 与 `orderingKey` 的一致性），
  之后才能撤掉 `apps/observer/frontend/src/contractConformance.ts` 里对 `artifactHandlesSummary.refused`
  的豁免行。这是**跨模块**改动（生产者在 workflow-assistance 侧），需要一张显式跨模块任务卡。
- 把逐泳道的**浏览器扫掠**接进 CI 作业：`scripts/audit/text_legibility_via_cdp.py` 的算术与判定已由
  `tests/ci/test_text_legibility_gate.py`（52 例）在 CI 里钉住，但它启动真浏览器量已构建产物的那一步不在任何
  作业里（CI 的浏览器步骤跑的是 `scripts/audit/topbar_geometry_via_cdp.py`）；
  `scripts/audit/evidence_handles_render_via_headless_chromium.py` 同样只是本机取证。接入会影响共享管道
  （需要浏览器与时长预算），等 owner 点头再做。

NEXT 不是实施承诺；启动任一项仍需用户明确 Task Grant 和独立验收。

## FROZEN — 暂时冻结，不进入当前开发

- 新增与当前问题闭环无直接关系的 Agent/Runtime 框架。
- 全自动自主多 Agent 编排、复杂 Agent 群和自我扩张能力。
- 大规模插件/MCP/模型/数据库批量安装或统一替换。
- 全局自动改写所有客户端配置，或强制所有任务通过 WORK-LAB。
- 重型多租户、集中身份中心、Kubernetes、复杂分布式调度。
- 把全软件私人会话自动采集、跨会话自动拼接作为当前功能。
- WUI-00..WUI-21 及其他 OPEN 账本任务、旧 UI/HUD 扩展、`WORK-LAB-UI-PRIORITY-TASKPACK-20261009` 的后续实施。
- **项目联动（用户 2026-10-19 指示：本项目按照独立运行先运行跑通起来，项目联动延后冻结）**：AAOS 候选提交与
  正式接收状态读取、DESIGN-LAB 设计能力、外部 source-root（owner 的 Record 资料）清点与分类、跨项目记忆与
  会话联邦，全部冻结在本仓独立运行跑通之前。冻结≠关闭：相关账本行、状态与证据原样保留，不因冻结标记为完成。

## DEFERRED — 延后研究，不承诺实施

- 跨项目、跨软件的长期上下文记忆与会话联邦。
- 自动恢复复杂跨客户端任务、跨 Agent 状态同步。
- 广泛自动派发和自动修复高风险问题。
- 自建长期记忆/向量数据库或第二套知识真源。
- 企业级部署、团队协作和远程集中治理。
- 对所有软件的实时深度监测；仅在有官方接口、明确权限和成本收益时逐步接入。

## RETIRED / 不作为产品目标

- 将 WORK-LAB 做成 Agent 本身或通用聊天产品。
- 将 WORK-LAB 定位为所有项目的统一专业审计官。
- 以目录/页面/插件数量证明产品进度。
- 用假数据、Agent 自述、HTTP 200 或单一退出码伪造成功。
- “超级入口 / Command Center / LAB Router”作为系统级执行大脑、Agent 调度器或第四个产品入口的设想；
  该历史设想保留在 `docs/future/WORK-LAB-SUPER-ENTRY-COMMAND-CENTER-LAB-ROUTER-2026-09-27.md`，
  不再作为当前产品目标。

## 解冻门槛

冻结/延期项目只有在以下条件全部满足后才能进入正式路线图：
当前最小闭环稳定；存在明确用户场景；接口和权限合法；风险可控；维护成本合理；能独立验收；用户批准。
解冻前先做小范围试验；未达到净收益即停止。代码存在不等于功能接通，文档更新不等于产品完成，
候选提交不等于 AAOS 接收。

## 路线图管理规则

每项能力必须标注：用户价值、依赖、风险、数据权限、实际证据、维护成本、退出路径和验收标准。
候选名单不等于实施承诺；研究不等于采用；代码存在不等于功能接通；文档更新不等于产品完成。
每次状态变化都必须在唯一 open register 或本次收敛报告中留下证据路径和日期，不得无证关闭历史任务。
