# WORK-LAB 权威收敛报告（2026-10-19）

## 0. 结论

**PASS（按本轮任务包范围）**：权威/路线图/文档收敛与**一个真实最小问题闭环**均已交付。
闭环对象为 `WORK-LAB-MINIMAL-LOOP-001`（Hermes 适配器声明了没有实现的能力 `resume`），
修复为真实产品代码（`services/execution-federation/hermes_adapter.py`），验证为能力门转绿、
12+49 项回归测试与适配器层真实读回；方案已固化为
`docs/current/authority-convergence-20261019/solutions/SOLUTION-001-ACP-HERMES-RESUME.md`。
包内 10 项验收标准全部覆盖（逐项见 §12）。

以下状态**不因本轮 PASS 而合并或提前**：exact-SHA CI 未运行（改动未提交），AAOS 候选未提交
（无已接通 API，且提交≠接收），问题中心/解决方案库作为**系统能力**仍是 NOT_IMPLEMENTED——
本轮交付的是其中一条真实闭环，不是这些模块的整体实现。

权威依据：用户 2026-10-19 明确决定“其他任务冻结，以这份任务为当前权威与闭环目标（更新项目内的权威和规划），
未来能力暂时冻结和延期延后”，以及 `docs/history/owner-inputs/20261019/WORK-LAB_权威收敛任务包_20261019.zip`
（`WL-REC-0105`，SHA-256 `36a2614dff217c1f9ad96838ba0304ac3d734e23ad9ebb3e86bb00e2114be2a0`）。

## 1. 仓库基线（编辑前）

| 项 | 值 |
| --- | --- |
| 分支 | docs/handoff-20261018-qoder（分支名，非仓库路径） |
| HEAD | `0369d349d46b75c7048b884331bb40a0f42d4e34` |
| HEAD tree | `d2a0222992f0171e0fc999dd6bb032ccbd40ed1f` |
| `origin/main` | `f6077d18cfc76d588d9315ec0ac82769c3009d9a` |
| `origin/main` tree | `6dcb2094ffa5fdb693e959de5aaa870eea8b1f78` |
| HEAD 与 `origin/main` | HEAD 领先 1 个提交，`f6077d18` 是 HEAD 的祖先 |
| dirty 状态 | 编辑前 59 个 porcelain 条目；含 4 个受保护的并行写者文件 |
| 顶层人类权威 | `WORK-LAB-AUTHORITY.md` |
| 顶层机器权威 | `.project/governance/project-authority-index.json` |
| 作用域任务权威 | `.project/governance/taskpack-authority-index.json` |
| 唯一开放任务账本 | `taskpacks/current/OPEN-TASK-REGISTER.md` |

受保护、未修改的 4 个并行写者文件：`AGENTS.md`、`config/adapter-registry.json`、
`config/client-evidence.json`、`taskpacks/current/error-ledger.json`。
工作树中另有先前 WUI/HUD 未提交改动；本任务没有回退、覆盖或提交它们。
测量时还发现暂存区已含先前 WUI/HUD 改动（不是本任务产生）；本任务只用显式路径追加自己的文件，
没有 `git reset`/取消暂存任何既有条目，也没有 commit。

## 2. 正式定位

WORK-LAB（工作流实验室 / Workflow Lab）是面向个人 AI 工作环境的、客户端中立的
**工作流管理、治理、运行监测与问题闭环系统**。它连接和管理用户使用的 AI Agent、开发工具、
工作流软件、模型服务、插件及相关运行环境；发现和汇总问题，生成解决建议或可交给现有 Agent
的修复任务包/提示词，跟踪验证修复结果，固化可复用解决方案，并把有长期价值的知识候选提交 AAOS
正式审核与接收。

**明确非目标：** WORK-LAB 不是 Agent、不是通用 Agent Runtime、不是模型网关、不是通用聊天客户端，
也不是所有项目的统一专业审计官。它不替代 Codex、Claude Code、Qoder、WorkBuddy 执行实际开发与故障修复；
不接管 DESIGN-LAB 的专业视觉判断；不取代 AAOS 的正式知识真源；不强制所有任务经过 WORK-LAB。

权威落点：`WORK-LAB-AUTHORITY.md` §2；机器索引 `.project/governance/project-authority-index.json`；
路线图 `docs/current/authority-convergence-20261019/ROADMAP.md`。

## 3. 定位冲突矩阵

| # | 旧表述/位置 | 结论 | 理由 | 影响文件/处理 |
| --- | --- | --- | --- | --- |
| 1 | `README.md`：“AI工作观测与配置治理工作台” | AMEND | 只描述观测/配置，缺少问题闭环、修复协作、方案固化与 AAOS 候选出口 | `README.md` 首屏改为新定位并指向新 CURRENT |
| 2 | `WORK-LAB-AUTHORITY.md` §2：观测/配置治理工作台；§3：UI-first current scope | AMEND | 产品本体与当前范围被 2026-10-19 决定取代；UI 不再优先 | 重写 §2/§3，保留 §4-§6 的数据真值、模块、安全和证据规则 |
| 3 | `.project/governance/project-authority-index.json`：`authorityId=...UI-PRIORITY`、`uiFirst=true` | AMEND | 机器权威必须与人类权威同一切换 | 新 `authorityId`、新 CURRENT、新 `currentDecision`，保留历史决定 |
| 4 | `.project/governance/taskpack-authority-index.json`：UI 包为唯一 CURRENT | AMEND | 单一 CURRENT 需要切换；旧包保留为 SUPERSEDED | UI 包移入 `SUPERSEDED`，新收敛包进入 `CURRENT` |
| 5 | `taskpacks/history/pre-convergence-20261019/WORK-LAB-UI-PRIORITY-TASKPACK-20261009.md`：自称唯一 CURRENT、UI-first | FREEZE / SUPERSEDED | 不删除历史，但不能继续派工；未完成 WUI 行不因冻结关闭 | 文件保留，顶部加 SUPERSEDED/FROZEN 提示 |
| 6 | `taskpacks/current/OPEN-TASK-REGISTER.md`：2026-10-09 UI 优先切换、唯一 CURRENT 指向 UI 包 | AMEND（仅表头）/ FREEZE（行） | 账本必须指向新 CURRENT；历史行与证据保留，不无证关闭 | 表头改为 2026-10-19 冻结与新 CURRENT；WUI 行原样保留 |
| 7 | `taskpacks/current/README.md`：唯一 CURRENT 指向 UI 包 | AMEND | 目录入口会误导新会话 | 改为新 CURRENT + 冻结说明 |
| 8 | `docs/history/archive/HANDOFFS-AND-PROMPTS-20261019.zip`（成员 NEXT-AGENT-PROMPT）：UI 后续交接 | FREEZE / SUPERSEDED | 稳定入口仍指向 UI 任务，需显式失效 | 顶部加冻结横幅并指向新 CURRENT |
| 9 | `docs/history/archive/HANDOFFS-AND-PROMPTS-20261019.zip`（成员 HANDOFF-20261018-QODER-SESSION）：UI 轮次交接 | FREEZE | 历史交接保留，但不能再作为当前指令 | 顶部加冻结横幅 |
| 10 | `docs/current/workflow-assistance/workflow/active-authority-index.md`：2026-10-09 UI 范围切换 | AMEND | 导航索引不是第二权威，但必须指向当前权威 | 顶部范围说明改为 2026-10-19 |
| 11 | `docs/current/DOCUMENT-CENSUS.md`：UI 当前任务与交接 | AMEND | 文档总索引需要反映新 CURRENT；旧计数仍是其日期快照 | 顶部加 2026-10-19 增量说明，不改旧盘点数字 |
| 12 | `docs/decisions/PROJECT_POSITIONING.md`：2026-10-09 定位 | AMEND | 决策记录是常见入口，必须与顶层权威一致 | 重写为 2026-10-19 收敛定位 |
| 13 | `docs/current/workflow-assistance/workflow/project-definition.md`：2026-10-09 产品定位补充、UI 优先 | AMEND | 作用域定义需要与顶层权威一致；其“非 Agent/非模型网关”边界保留 | 更新定位段落与 UI 状态，保留 Observer/Control/三方边界 |
| 14 | `docs/future/WORK-LAB-SUPER-ENTRY-COMMAND-CENTER-LAB-ROUTER-2026-09-27.md`：超级入口、LAB Router、Agent 调度/执行大脑 | RETIRE（作为产品目标）/ FREEZE（文件） | 与“不是 Agent/Runtime、不是第四产品入口、不做复杂自主编排”的定位冲突；历史研究保留 | 顶部加冻结横幅，不删除原文 |
| 15 | `docs/future/WORK-LAB-BLUEPRINT-20261006.md`：完整未来蓝图 | FREEZE | 已有 FROZEN_ARCHIVED 标记；历史依据，非当前派工 | 不改正文；由新路线图取代其未来范围 |
| 16 | `AGENTS.md`：workflow-assistance 范围、受管客户端与五维底线；第 12 行仍写“唯一CURRENT是 UI 包，UI 优先” | KEEP（规则）/ OWNER DECISION（第 12 行） | 执行规则、模块、安全和五维底线仍有效；第 12 行与 2026-10-19 决定冲突，但该文件是受保护的并行写者文件 | 本任务不修改该文件；机器权威与 verifier 已指向收敛包。建议 owner 授权后把第 12 行改为收敛包 |
| 17 | `docs/history/**`、`taskpacks/history/**`：旧任务/审计/交接 | FREEZE | 冻结历史只作来源，不得据名称重新派工 | 不修改；需要时点名读取 |
| 18 | WUI 报告（含 `docs/history/archive/ui-priority-20261009/WUI-19-FINAL-ACCEPTANCE-20261012.md`） | FREEZE | 记录的是过去轮次与证据；冻结不改写历史字节 | 不修改；其未完成项保持原状态 |
| 19 | HUD 融合/紧凑 HUD 扩展方向 | FREEZE（产品方向） | 既有 HUD 是桌面观测面，可保留；新融合扩展不属于当前问题闭环 | 不新增 HUD 功能；既有代码与测试保留 |
| 20 | 手机端相关表述 | KEEP（不做）/ 不再新建任务 | 2026-10-09 决定仍有效；新包未要求手机端 | 不新建手机端延后/冻结任务 |
| 21 | `docs/current/workflow-assistance-README.md`、`docs/current/workflow-assistance/workflow/codex-global-enhancement.md` 的“非 Runtime/非模型网关”边界 | KEEP | 与新定位兼容，且是重要的反向边界 | 不改正文；由顶层权威统一表述 |
| 22 | `services/memory`、`services/session-federation` 的跨项目记忆/会话联邦能力 | DEFER | 新路线图明确延期研究，不承诺实施 | 保留代码与历史，不将其作为当前前置 |
| 23 | `.agents/skills/work-lab-workflow/SKILL.md`（源 `projections/agents/source/work-lab-workflow/SKILL.md`）：仍把 UI 包写成 current taskpack，产品描述停留在旧定位 | AMEND | 这是新会话默认读取的技能；陈旧的默认材料会让新会话直接继承错误的 CURRENT | 更新源文件的定位、问题闭环、验证范围与冻结规则，运行 `projections/agents/generate.py` 重生成投影，并用 canonical generator 修正 `config/skills-inventory.json` 的 8 条陈旧哈希 |
| 24 | 根目录 6 份历史文档的 disposition banner：权威链仍写 UI 包为 CURRENT | AMEND（仅 banner） | `scripts/ci/verify_root_document_dispositions.py` 实测 6 条 `STALE_POINTER`，新会话读根文件时会看到错误 CURRENT；正文必须保持逐字不变 | 仅改 banner 的权威链并注明 UI 包已 SUPERSEDED/FROZEN；正文与 BEGIN/END 之外字节未动，verifier 与 16 项测试通过 |
| 25 | `scripts/audit/normalise_doc_citations.py` 的默认加载 scope：第 5 步仍写 UI 包，并保留两份已冻结的 UI 入口文档 | AMEND | 该工具自己声明 scope 是 auditBootstrap 的读取顺序；权威切换后它仍在检查一份已 SUPERSEDED 的包，而真正的 CURRENT 任务包与收敛报告/路线图没有被检查 | scope 改为收敛任务包 + 本报告/路线图；删除只被旧 UI 文档使用的一条包内文件允许项（`SOURCE_BASELINE`，不带扩展名，避免再次成为引用）；把 verifier 输出字面量 `OPEN-TASK-REGISTER.md` 登记为不可改写；实测 `docs=9 citations=862 rewritten=0 blocked=0`，9 项测试通过 |
| 26 | `docs/history/archive/ui-priority-20261009/TASK-BREAKDOWN.json`：`currentTaskpack` 仍为 UI 包（无 banner 的 JSON 历史字段） | FREEZE / NON-NORMATIVE | 它是 UI 轮次的机器可读拆解，不是治理索引；改写历史 JSON 会破坏其日期证据 | 不修改；当前权威只由 `.project/governance/taskpack-authority-index.json` 决定 |

## 4. 当前能力映射（2026-10-19 只读核对）

| 能力 | 现状 | 证据 | 缺口 |
| --- | --- | --- | --- |
| 监测数据源 | PARTIAL：仓内有有界 collector、Snapshot v3 和只读 Observer；未证明所有受管客户端端到端 LIVE | `packages/client-neutral-core/scripts/collectors.py`（`collect_task_ledger`、`collect_git_ci`、`collect_usage_files`、`collect_source_quality`、`collect_growth_watcher`）；`packages/client-neutral-core/scripts/snapshot_api.py` 的 `SNAPSHOT_SCHEMA_VERSION = "workflow/snapshot/v3"`；`.project-local/runs/authority-convergence-20261019/collectors.txt`、`snapshot-version.txt` | 未证明每个 Adapter 的真实采集/新鲜度；无统一的 source/freshness 面板；采集失败与 UNKNOWN 的端到端呈现未验证 |
| 问题中心 | NOT_IMPLEMENTED | 对 `services`、`integrations`、`packages/client-neutral-core`、`apps/observer/frontend/src` 检索 `issue[_-]?center|IssueCenter|问题中心`，命中 0；`.project-local/runs/authority-convergence-20261019/issue-center-hits.txt` | 没有问题 ID、去重、分类、优先级、项目/软件/版本关联、日志片段、处理状态或 UI |
| 修复任务包 | PARTIAL：有通用 TaskPack runner、任务协议和账本；本轮人工交付了一份真实修复交接卡 | `services/orchestration/run_taskpack_agent.py`；`services/task-governance/task_protocol.py`；`packages/client-neutral-core/scripts/task_ledger.py`；`.project-local/runs/authority-convergence-20261019/minimal-loop-candidate-acp-hermes-resume-20261019.md`；`docs/current/authority-convergence-20261019/implementation/WORK-LAB-MINIMAL-LOOP-001-ACP-HERMES-RESUME.md` | issue→repair 的自动生成器仍不存在；本轮交接是人工写出的，不是产品功能 |
| 修复验证 | PARTIAL：有完成权威、证据聚合和 CI 门；本轮第一次把真实修复接到可重跑的验证与读回 | `services/task-governance/completion_authority.py`；`services/receipts/evidence_aggregator.py`；`services/receipts/execution_evidence.py`；`.project-local/artifacts/authority-convergence-20261019/minimal-loop/01..04` | 待处理/已交接/处理中/待验证/失败/已解决/已固化的产品状态机仍不存在；本轮状态记在实现卡与方案记录里 |
| 解决方案库 | NOT_IMPLEMENTED（系统能力）/ 首条记录已存在 | 检索 `solution[_-]?library|SolutionLibrary|解决方案库` 命中 0；`docs/current/authority-convergence-20261019/solutions/SOLUTION-001-ACP-HERMES-RESUME.md` | 无方案 schema 的机器实现、检索与复验；第一条记录是文件，不是可查询的库 |
| AAOS 候选出口 | CONTRACT_ONLY | `integrations/archeaxis/contracts/promotion_contract.py`（`KnowledgeCandidate`、`ArcheAxisHandoffEnvelope`、`export_permission` 默认拒绝）；`services/knowledge/promotion_gate.py`；`services/knowledge/BOUNDARY.md`；`.project-local/runs/authority-convergence-20261019/aaos-contracts.txt` | 没有 AAOS API 客户端/提交回执/接收状态读回；未提交任何候选；AAOS 的正式审核与接收权未变 |
| Control / Observer 分离 | SCAFFOLD | `services/control/control_service.py`（loopback 写边界）；`scripts/ci/verify_observer_readonly.py`；`scripts/ci/verify_observer_readonly_boundary.py` | 问题/修复生命周期尚无 Control 写路径；本次未新增任何写操作 |
| 真实最小闭环 | DELIVERED（`WORK-LAB-MINIMAL-LOOP-001`，适配器层验证） | `scripts/ci/verify_acp_adapter_honesty.py` 从红转绿；`services/execution-federation/hermes_adapter.py` 实改；`.../minimal-loop/01..04` 四份收据；实现卡与 `SOLUTION-001` | 闭环的“发现”来源是仓内 AG-06 能力门（真实、可复现），不是外部已接入客户端；Hermes 原生会话恢复仍不存在，也未被声称存在 |

“命中 0”是上述作用域内的只读检索结果；它证明这些作用域里没有同名实现，不代表所有历史资料或外部项目中不存在相关讨论。

## 5. 路线图收敛结果

完整清单见 `docs/current/authority-convergence-20261019/ROADMAP.md`：

- **CURRENT（9 项）**：权威收敛、真实数据源与诚实 Observer 状态、问题中心、问题摘要/Agent 修复任务包、
  修复跟踪与验证、解决方案库、AAOS 候选出口、Control/Observer 分离、一个真实最小闭环。
  第 9 项已由 2026-10-19 用户指令（“执行所有未完成的任务，按照最新发你的任务包”）作为具体 Task Grant
  交付：`WORK-LAB-MINIMAL-LOOP-001` 完成发现→摘要→历史匹配→交接→修复→验证→固化。
  第 2-8 项仍只是该闭环中被用到或被指出的能力面；它们作为**系统能力**没有获得整体实施授权。
- **NEXT**：更多连接器、聚类与历史检索、受限低风险自动化、方案过期/版本适用性/回归复验、
  真实可获取的成本/Token/资源汇总。
- **FROZEN**：新 Agent/Runtime 框架、全自动多 Agent 编排、大规模插件/MCP/模型/数据库安装、
  全局自动改写配置、重型多租户/Kubernetes、私人会话自动采集、WUI 后续实施。
- **DEFERRED**：跨项目/跨软件长期记忆与会话联邦、复杂跨客户端恢复、广泛高风险自动派发/修复、
  第二套知识真源、企业级部署、全软件实时深度监测。
- **RETIRED**：WORK-LAB 作为 Agent/通用聊天产品、作为全项目专业审计官、以数量证明进度、
  以假数据/自述/HTTP 200/单一退出码伪造成功、超级入口/Command Center/LAB Router 作为执行大脑。
- **解冻门槛**：最小闭环稳定 + 明确用户场景 + 合法接口/权限 + 风险可控 + 维护成本合理 +
  独立验收 + 用户批准；先做小范围试验，未达净收益即停止。

## 6. 来源登记与冻结处理

- 新来源包已登记为 `WL-REC-0105`，归档于
  `docs/history/owner-inputs/20261019/WORK-LAB_权威收敛任务包_20261019.zip`（9,459 B，
  SHA-256 `36a2614dff217c1f9ad96838ba0304ac3d734e23ad9ebb3e86bb00e2114be2a0`），包含 5 个成员，
  ZIP 内顶层目录为 `WORK-LAB_权威收敛任务包/`；五个成员均为 `.md`：
  `README`、`TASKPACK`、`AUTHORITY`、`ROADMAP`、`ACCEPTANCE`（包内文件名，不是仓库路径）。
- 登记结果：105 条资料、2,387 条包内成员；源清单 186 个文件（50 归档 / 136 排除 / 0 未决）。
- 包内程序未执行；包内提示和历史验证不额外授予权限。
- WUI 与历史任务没有关闭、没有改状态、没有清零缺陷；只加冻结/失效提示。
- 没有创建第二任务账本；CURRENT 仍由 `.project/governance/taskpack-authority-index.json` 唯一指定。

## 7. 测试报告

以下命令在编辑后的工作树上运行；精确 HEAD 为编辑前 `0369d349d46b75c7048b884331bb40a0f42d4e34`
（本任务未提交，故工作树内容与该提交不同，差异即本报告 §8 的文件）。结构门读取的是工作树/暂存区，
不是一次新的 CI 运行；因此这些结果**不等于** exact-SHA CI。表 24 是适配器层的真实运行读回，
但它证明的是适配器行为，不证明 Hermes 原生进程或桌面界面。

| # | 命令 | 退出码 | 摘要 |
| --- | --- | --- | --- |
| 1 | `python scripts/ci/verify_project_authority_reference.py` | 0 | `AUTHORITY_REFERENCE_PASS top=WORK-LAB-AUTHORITY.md current=WORK-LAB-AUTHORITY-CONVERGENCE-TASKPACK-20261019 register=OPEN-TASK-REGISTER.md` |
| 2 | `python scripts/ci/verify_authority_index_paths.py` | 0 | `AUTHORITY_INDEX_PATHS_TOTAL targets=58 refs=1376 broken=0 declared_in_row=17 no_tree_claims=10 failed_targets=0` |
| 3 | `python scripts/ci/verify_refs_surface_policies.py` | 0 | `REFS_SURFACE_POLICIES_PASS head=0369d349d46b surfaces=662 refs=4166 external_surfaces=559 external_refs=3327 external_broken_declared=2871 ratchet_surfaces=103 ratchet_baseline=386 ratchet_broken_today=386 new=0 fixed=0 declaration_problems=0` |
| 4 | `python scripts/audit/normalise_doc_citations.py` | 0 | `DOC_CITATIONS CHECKED docs=9 citations=897 rewritten=0 blocked=0 generic_allowed=16 absent_quoted=9 stale_allowances=0`；首次为 `rewritten=2`（窄引用的方案文件名/路线图简写），按门自身提示 `--apply` 规范化后复跑为 0 |
| 5 | `python scripts/ci/verify_register_table_shape.py` | 0 | `REGISTER_TABLE_SHAPE_PASS tables=1 rows=25 wrong_width=0` |
| 6 | `python tests/ci/test_register_table_shape_is_uniform.py` | 0 | `Ran 9 tests` / `OK`（精确时长随运行波动，以收据原文为准）；随后同一 `REGISTER_TABLE_SHAPE_PASS` 行 |
| 7 | `python scripts/maintenance/owner_material_catalog.py build-index` | 0 | `{"status":"PASS","catalogRows":2492}`；重生成 `docs/history/owner-inputs/INDEX.md`、`docs/history/owner-inputs/CATALOG.html` 与两份 CSV 投影 |
| 8 | `python scripts/maintenance/owner_material_catalog.py verify` | 0 | `{"status":"PASS","registeredMaterials":105,"indexedArchiveMembersIncludingNested":2387,"sourceFilesInventoried":186,"relatedSourceFiles":50,"excludedForeignFiles":136,"mixedRelatedMembers":56,"unresolvedSourceFiles":0,"sourceReadback":"NOT_EXECUTED","sourceModified":false,"productImplementation":"NOT_EXECUTED","errors":[]}` |
| 9 | `python scripts/ci/verify_live_doc_paths_resolve.py` | 0（首次 1） | 最终 `LIVE_DOC_PATHS_PASS every live citation resolves`（`LIVE_DOC_PATHS citations=805 missing=0 stale_exceptions=0`）；首次 FAIL 的实测原因是报告把分支名放在反引号中，被 `PATH_RE` 当作 `docs/...` 路径；改为明示“分支名，非仓库路径”后通过 |
| 10 | Python `json.load` on the two governance indexes + `docs/history/owner-inputs/RECORD-ARCHIVE-REGISTER.json` + `docs/history/owner-inputs/RECORD-SOURCE-CENSUS.json` | 0 | 四份 JSON 全部 `JSON_OK` |
| 11 | `git diff --check` / `git diff --cached --check`（仅本任务路径） | 0 / 0 | 无空白错误 |
| 12 | `env PYTHONIOENCODING=utf-8 .project-local/toolchains/wl-py311/Scripts/python.exe tests/workflow-assistance/test_agent_default_material_is_regenerated_and_current.py` | 0 | 完整文件 `Ran 8 tests` / `OK`；`AgentDefaultMaterialTests` 覆盖源→投影字节一致、两次生成幂等、content_hash、必需定位标记、引用路径可解析与 <10KB 预算；`DerivedProjectionDriftTests` 的 PyYAML 依赖缺口由项目解释器闭合，生成后投影字节未变。UTF-8 绑定是命令的一部分：未绑定时该测试调用的 context pack 会因 GBK stdout 无法编码 U+2194 而中止（本轮实测 1 failure） |
| 13 | `python scripts/ci/verify_root_document_dispositions.py` | 0（修复前 1） | 修复前 6 条 `STALE_POINTER`；最终 `ROOT_DISPOSITIONS_PASS root_md=11 authority=2 convention=3 historical=6` |
| 14 | `python tests/workflow-assistance/test_root_document_dispositions.py` | 0 | `Ran 16 tests` / `OK`；含 banner 外正文逐字不变的守卫 |
| 15 | `python tests/workflow-assistance/test_default_load_doc_citations_resolve.py` | 0 | `Ran 9 tests` / `OK`；断言 9 份默认加载文档的 897 条引用全部唯一可解析且无简写 |
| 16 | `python scripts/ci/verify_observer_readonly_boundary.py` | 0 | `OBSERVER_READONLY_PASS runtime=non-GET-denied data_layer=read_only sources_scanned=82` |
| 17 | `python scripts/ci/verify_model_registry_integrity.py` | 0 | `MODEL_REGISTRY_INTEGRITY_PASS providers=9 models=10 runtimes=3 processLibraries=2 externalAssets=0 served_bindings=0` |
| 18 | `python scripts/ci/verify_acp_adapter_honesty.py` | 0（修复前 1） | **修复前**：`DECLARED_CAPABILITY_WITHOUT_IMPLEMENTATION hermes advertises execution capability 'resume' but resume() produced no real effect`（既有失败，非收敛文档轮次引入）。**修复后**：`ACP_HONESTY_PASS executors=5 operations=40 executable=0 native_verified=0`。修复与收据见 #21 |
| 19 | `.project-local/toolchains/wl-py311/Scripts/python.exe scripts/maintenance/owner_material_catalog.py verify --source-root "D:/All projects/Record"` | 1 | **源目录清单漂移，非本任务引入**：`"status": "FAIL"`、`"sourceReadback": "FAIL"`，唯一错误 `Record file inventory drift; reclassify new/missing materials`。仓内归档与成员校验本身通过（见 #8）；失败仅因源目录相对 2026-10-11 快照新增了未分类文件，见 #20。未重分类：新文件属其他项目/UI/AAOS/ASTRYN/调研材料，超出本收敛任务范围，且来源目录归 owner 管辖 |
| 20 | `.project-local/toolchains/wl-py311/Scripts/python.exe .project-local/runs/authority-convergence-20261019/diff_source_census.py` | 0 | 漂移定量（只读诊断）：`snapshotDate 2026-10-11`、`expected 186 actual 204`、`NEW 18`；脚本仅在存在缺失时打印 MISSING 行，本次无该行（0 缺失由 expected/actual/NEW 推出）；新增项含 UI/Backend/ASTRYN 任务包 ZIP、AAOS ZIP、DESIGN-LAB ZIP、若干图片与 `观猹项目调研与三项目增强评估_20261013.md`。2026-10-19 交付包已在 `incrementalAppends` 中登记（`WL-REC-0105`），不属于这 18 项 |
| 21 | `.project-local/toolchains/wl-py311/Scripts/python.exe scripts/ci/verify_acp_adapter_honesty.py`（修复后） | 0 | `ACP_HONESTY_PASS executors=5 operations=40 executable=0 native_verified=0`；收据 `.../minimal-loop/01-acp-honesty.out`。修复前同一命令为 exit 1（#18） |
| 22 | `.project-local/toolchains/wl-py311/Scripts/python.exe tests/workflow-assistance/test_execution_federation.py` | 0 | `Ran 12 tests` / `OK`；收据 `.../minimal-loop/02-federation-tests.out` |
| 23 | `.project-local/toolchains/wl-py311/Scripts/python.exe tests/workflow-assistance/nf22_registry_and_acp_honesty_gates.py` | 0 | `Ran 49 tests` / `OK`；收据 `.../minimal-loop/03-nf22-tests.out` |
| 24 | `.project-local/toolchains/wl-py311/Scripts/python.exe .project-local/runs/authority-convergence-20261019/minimal_loop_readback.py` | 0 | 适配器层真实读回（伪造可启动二进制使 launchable 分支真的执行）：`verdict=PASS`；`supports` 14 项不含 `resume`；`resumeStatus=NOT_SUPPORTED`、`resumeOk=false`；`launchable/resume_absent/non_execution_planes_intact/execution_planes_intact/no_resume_declaration_in_source` 全真；读回适配器 5,697 B、SHA-256 `1735299435b743cc138a97b13b68bfb1c203130ddd6f6ac1427514418d1c3fe4`；收据 `.../minimal-loop/04-readback.out` |

表 1-14 的机器门原始输出与退出码保存在 `.project-local/artifacts/authority-convergence-20261019/gates/`；
机器索引 `.project-local/artifacts/authority-convergence-20261019/gate-receipts.json` 记录 14 个门的命令、
退出码、输出字节数与 SHA-256，并绑定当前 HEAD `0369d349d46b75c7048b884331bb40a0f42d4e34`
（本次实测 14/14 exit 0，`allPass=true`）。另用独立脚本重算 14 份输出的字节数与 SHA-256、逐门比对
`.exit` 与收据退出码：`GATE_RECEIPT_BINDING gates=14 allPass=True problems=0`
（`.project-local/artifacts/authority-convergence-20261019/gates/binding-check.out`）。表 15-20 的附加只读消费者检查单独保存在
`.project-local/artifacts/authority-convergence-20261019/additional/`：15-18 与 20 退出 0（18 为修复后）；
19（外部来源目录清单漂移）为红色，非本任务引入，也不计入 14 门捆绑。表 21-24 是最小闭环的修复与读回收据，
保存在 `.project-local/artifacts/authority-convergence-20261019/minimal-loop/`，四份均退出 0。
除 #24 外，以上是**工作树门禁/测试收据**，不是 exact-SHA CI。

未执行项及原因：

- 完整本地治理套件：按现行约束不跑，CI 是最终裁判；本轮只跑与改动面相关的最小门。
- 真实运行/桌面/Tauri/键盘/DPI：WUI 已冻结，未重新拉起界面，也未把旧字节上的读数当作当前证据。
- 最小闭环的真实采集/修复/回读：已按用户 2026-10-19 指令执行（`WORK-LAB-MINIMAL-LOOP-001`），
  但来源是仓内 AG-06 能力门而非外部客户端采集，验证到适配器层；Hermes 原生进程的真实会话恢复未做。
- AAOS 提交/接收：没有已接通的 AAOS API，未提交；不伪造回执。
- 来源目录新文件的重新分类：`verify --source-root` 已实测（#19），漂移定量为 18 项新增、0 项缺失（#20）；
  这些文件属于其他项目/UI/AAOS/ASTRYN/调研材料，超出本收敛任务范围，来源目录归 owner 管辖，故未改动。
  2026-10-19 交付 ZIP 的 SHA-256 已单独计算并登记（§6）。
- commit/push/PR/merge/release：未执行，等待 owner 明确授权。

## 8. 修改文件清单

（以实际 `git status` 为准；下列为本任务新增或编辑的文件。）

- `WORK-LAB-AUTHORITY.md`
- `.project/governance/project-authority-index.json`
- `.project/governance/taskpack-authority-index.json`
- `taskpacks/current/WORK-LAB-AUTHORITY-CONVERGENCE-TASKPACK-20261019.md`（新）
- `taskpacks/current/OPEN-TASK-REGISTER.md`（仅表头冻结说明；行保留）
- `taskpacks/current/README.md`
- `taskpacks/history/pre-convergence-20261019/WORK-LAB-UI-PRIORITY-TASKPACK-20261009.md`（仅顶部失效提示）
- `README.md`
- `docs/decisions/PROJECT_POSITIONING.md`
- `docs/current/authority-convergence-20261019/ROADMAP.md`（新）
- `docs/current/authority-convergence-20261019/AUTHORITY-CONVERGENCE-20261019.md`（新，本文件）
- `docs/current/authority-convergence-20261019/implementation/WORK-LAB-MINIMAL-LOOP-001-ACP-HERMES-RESUME.md`（新，实现卡）
- `docs/current/authority-convergence-20261019/solutions/SOLUTION-001-ACP-HERMES-RESUME.md`（新，首条方案记录）
- `services/execution-federation/hermes_adapter.py`（**产品修复**：移除未实现的 `Capability.RESUME` 声明，5 行新增/1 行删除）
- `.project-local/runs/authority-convergence-20261019/minimal_loop_readback.py`（新，适配器层读回脚本）
- `.project-local/artifacts/authority-convergence-20261019/minimal-loop/01-acp-honesty.out`、`02-federation-tests.out`、`03-nf22-tests.out`、`04-readback.out`（新，最小闭环收据）
- `docs/history/archive/HANDOFFS-AND-PROMPTS-20261019.zip`（成员 NEXT-AGENT-PROMPT）（仅顶部失效提示）
- `docs/history/archive/HANDOFFS-AND-PROMPTS-20261019.zip`（成员 HANDOFF-20261018-QODER-SESSION）（仅顶部失效提示）
- `docs/current/workflow-assistance/workflow/active-authority-index.md`（范围说明）
- `docs/current/workflow-assistance/workflow/project-definition.md`（定位补充）
- `docs/current/DOCUMENT-CENSUS.md`（增量说明）
- `docs/future/WORK-LAB-SUPER-ENTRY-COMMAND-CENTER-LAB-ROUTER-2026-09-27.md`（冻结提示）
- `docs/history/owner-inputs/20261019/WORK-LAB_权威收敛任务包_20261019.zip`（新归档）
- `docs/history/owner-inputs/RECORD-ARCHIVE-REGISTER.json`
- `docs/history/owner-inputs/RECORD-ARCHIVE-MEMBERS.jsonl`
- `docs/history/owner-inputs/RECORD-SOURCE-CENSUS.json`
- `scripts/maintenance/owner_material_catalog.py`（仅把生成索引首屏指向新 CURRENT/路线图/报告，并保留 UI 历史交接链接）
- `scripts/audit/normalise_doc_citations.py`（默认加载 scope 从已失效 UI 包切到收敛任务包 + 本报告/路线图；删除不再使用的包内文件允许项；新增 verifier 输出字面量允许项，防止收据被机械改写）
- `projections/agents/source/work-lab-workflow/SKILL.md`（默认技能源：新定位、问题闭环状态分离、当前任务包与冻结规则；版本 1.2.0）
- `.agents/skills/work-lab-workflow/SKILL.md`（由 `projections/agents/generate.py` 重生成，content_hash 已更新）
- `config/skills-inventory.json`（由 `scripts/ci/generate_skills_inventory.py` 重生成：19 条中 8 条陈旧哈希按磁盘/HEAD 实测修正，含本技能新哈希；无技能增删）
- `docs/history/archive/root-ui-records-20261019/ASSET_REPLACEMENT_MANIFEST.md`、`docs/history/archive/HANDOFFS-AND-PROMPTS-20261019.zip`（成员 HANDOFF-UI-L10B）、`docs/history/archive/root-ui-records-20261019/UI_DECISIONS.md`、`docs/history/archive/root-ui-records-20261019/UI_IMPLEMENTATION_REPORT.md`、`docs/history/archive/root-ui-records-20261019/UI_REFERENCE_MANIFEST.md`、`docs/history/archive/root-ui-records-20261019/VISUAL_QA_REPORT.md`
  （仅 disposition banner 的权威链改指新 CURRENT；正文与 banner 外字节未动，由 verifier 与 16 项测试守卫）
- 由 `scripts/maintenance/owner_material_catalog.py build-index` 生成的 `docs/history/owner-inputs/INDEX.md`、`docs/history/owner-inputs/CATALOG.html`、`docs/history/owner-inputs/RECORD-ARCHIVE-REGISTER.csv`、`docs/history/owner-inputs/RECORD-ARCHIVE-MEMBERS.csv`

未修改：`AGENTS.md`、`config/adapter-registry.json`、`config/client-evidence.json`、
`taskpacks/current/error-ledger.json`；没有修改 DESIGN-LAB/AAOS；没有覆盖任何未提交工作。

**2026-10-19 归档对齐说明**：本表记录的是权威收敛当时的改动。同日按用户指示执行的归档规范化
（54 项 `git mv`，含本表里的 UI 包目录、UI 任务包与六份根级 UI 记录）把它们的最终位置改到
`docs/history/archive/` 与 `taskpacks/history/pre-convergence-20261019/`；本表路径已随之改指。
逐件移动与哈希见 `docs/history/archive/MOVED-PATHS-20261019.json`，任务包侧记录见
`taskpacks/current/WORK-LAB-AUTHORITY-CONVERGENCE-TASKPACK-20261019.md` §11。

## 9. 风险与回滚

**风险：**

1. 旧消费者若硬编码 UI 任务包路径，会读到已失效的 UI-first 指令；已在该包、交接、README、账本表头加显式提示。
2. 冻结可能让未完成 WUI 项“消失”；已保留全部行、状态与证据，并在路线图写明冻结不等于关闭。
3. 新来源包已加入资料登记与源清单；`--source-root` 复核实测为红色（#19）：源目录相对 2026-10-11 快照新增
   18 个未分类文件、缺失 0（#20）。这些文件属其他项目且来源目录归 owner 管辖，未重分类，因此该项在 owner
   处理前会持续显示 `FAIL`；它不改变仓内归档与成员的校验结果（#8 通过）。
4. 本任务改了一处产品代码（`services/execution-federation/hermes_adapter.py` 的 `RESUME` 声明）。风险是若有调用方依赖
   `supports` 中出现 `resume` 来选择恢复路径——那样的调用方本来就踩在假声明上，能力门判红；
   移除后它们会得到 `NOT_SUPPORTED`，这是如实的降级而非新的失败。适配器其他能力与行为未动。
   文档与索引切换后，必须由下一次 CI 在提交后的 exact SHA 上重新验证，不能把本报告的结构门结果当作 CI 结果。
5. 工作树含先前未提交改动；本任务只在指定文件上追加编辑，未触碰 4 个受保护并行写者文件。
6. `AGENTS.md` 第 12 行仍写“唯一CURRENT是 UI 包，UI 优先”，该文件是受保护的并行写者文件，未修改；
   `docs/history/archive/ui-priority-20261009/TASK-BREAKDOWN.json` 的 `currentTaskpack` 字段与若干已冻结 taskcard
   也保留历史 UI 指向。这些是残留旧口径，不能作为当前权威：新会话须按 `WORK-LAB-AUTHORITY.md` →
   `.project/governance/project-authority-index.json` → 收敛任务包解析；机器 verifier 已通过。
   若要清理 `AGENTS.md` 这一行，需 owner 明确授权后单独修改。

**回滚：**

- 仅回滚本任务的文件到编辑前字节；不使用 `git reset --hard`、`git clean` 或全仓还原。
- 产品修复单独可回滚：在 `services/execution-federation/hermes_adapter.py` 恢复
  `acp.Capability.RESUME,` 一行并移除说明注释；回滚后 AG-06 能力门会回到实测的红色（预期可伪证）。
- 若要恢复 UI-first：把两个治理索引的 CURRENT/decision 指回 UI 包，并移除本任务新增的冻结横幅；
  历史 UI 包本身未被删除，可直接恢复为 current（需 owner 明确决定）。
- 新归档与登记行是追加式；如撤回归档决定，可整组删除 `WL-REC-0105` 记录、5 条成员行和归档 ZIP，
  然后重跑 `build-index` 与 `verify`。

## 10. 状态区分（不得合并）

| 状态 | 本轮结果 |
| --- | --- |
| 权威更新 | DELIVERED：`WORK-LAB-AUTHORITY.md` 与两个治理索引已切换 |
| 代码实现 | DELIVERED：`services/execution-federation/hermes_adapter.py` 移除未实现的 `RESUME` 声明（ML-001） |
| 真实运行验证 | DELIVERED（适配器层）：能力门转绿 + 适配器 launchable 分支真实读回（`resumeStatus=NOT_SUPPORTED`）；未拉起 Observer/Tauri/桌面，也未证明 Hermes 原生恢复 |
| 受控测试 | 见 §7；14 门 + 附加检查 + ML-001 的 12/49 项回归 |
| 方案固化 | DELIVERED：`docs/current/authority-convergence-20261019/solutions/SOLUTION-001-ACP-HERMES-RESUME.md`（症状/根因/版本/步骤/证据/失效/回滚） |
| AAOS 接收 | NOT_EXECUTED：只有候选合同，没有提交或接收回执；提交≠接收 |
| 任务关闭 | ML-001 关闭；其余任务保持冻结（冻结≠关闭），未无证改状态 |
| exact-SHA CI | NOT_EXECUTED：改动未提交，工作树门禁≠CI |

## 11. 下一步

1. 等待 owner 对本次权威收敛与 ML-001 修复结果的确认；提交/推送由 owner 另行授权。
2. 在提交后的 exact SHA 上运行 CI，确认两个治理索引、来源登记与产品修复在干净检出中同样通过；
   `services/execution-federation/hermes_adapter.py` 的改动必须进入 exact-SHA CI 才算最终验证。
3. 最小闭环已交付（`WORK-LAB-MINIMAL-LOOP-001` / `SOLUTION-001`）。若 owner 要继续，应给出**下一个**
   具体 Task Grant 并选定问题；问题中心/解决方案库作为系统能力仍未被授权整体实施。
4. AAOS 候选仍不提交：没有已接通 API。只有在存在真实接收回执时才能写“AAOS 已接收”，
   不把“已提交”或“本地方案记录”写成接收。
5. 账本派生投影的重发**不需要 owner 授权**，本段原先的说法是错的，已按代码实测改正并执行：
   `scripts/audit/ledger_regression_command_targets.py` 无条件按 `--audit-out`（默认即出厂投影）写出，
   只有账本才受 `--apply` 控制。先只读预览（`changed_existing=0`，新增行只有 ERR-276 与 ERR-277，
   `repointMap`/`handAdjudicated` 未变），再落地重发两份派生审计（投影 274→276、PATH_GONE 36→38、
   `docs/audits/LEDGER_UNBOUND_TRIAGE_2026-10-07.json` 的 unboundPass 94→96），受保护账本字节未动。
   本地门实测 `50 passed, 1 failed`：本轮之前 8 项红里的 4 项成因消除，仍属 owner 的是
   ERR-276/277 的 `fixedCommit` 绑定（必须有真实修复提交才可写）、executor registry pin、DSH 日期合同、
   派生审计幂等（未裁决的 `.project-local/artifacts/wui-20261009/refs-census-20261018.json`）。

## 12. 包内 10 项验收标准逐项覆盖

| # | 验收标准（任务包原文要点） | 状态 | 落点/证据 |
| --- | --- | --- | --- |
| 1 | 正式定位：工作流管理/治理/监测/问题闭环，客户端中立 | DONE | §2；`WORK-LAB-AUTHORITY.md` §2；`.project/governance/project-authority-index.json` |
| 2 | 明确非目标：不是 Agent/Runtime/模型网关/聊天客户端/全项目审计官 | DONE | §2；`WORK-LAB-AUTHORITY.md` §2；`README.md` |
| 3 | 问题闭环各阶段分别记录，不合并为“完成” | DONE | 实现卡 §6 状态分离；`SOLUTION-001` §9；本报告 §10 |
| 4 | 状态必须诚实：UNKNOWN/STALE/来源/时间/新鲜度，不补 0 | DONE（规则保留）/ 本轮未新增采集 | `WORK-LAB-AUTHORITY.md` §4；Observer 只读门 #16；ML-001 读回不把 `executable=0` 写成可用 |
| 5 | Observer 只读；写经独立授权 Control | DONE（规则与门保留） | `WORK-LAB-AUTHORITY.md` §5；#16 `OBSERVER_READONLY_PASS`；本轮未新增写路径 |
| 6 | AAOS 保留知识审核/接收权，只提交候选并读状态 | DONE（边界保留） | §4 AAOS 行；`services/knowledge/BOUNDARY.md`；本报告 §10 AAOS=NOT_EXECUTED |
| 7 | 跨项目记忆/会话联邦/自主 Agent 协作冻结或延期 | DONE | `docs/current/authority-convergence-20261019/ROADMAP.md` FROZEN/DEFERRED；§3 行 22 |
| 8 | 复用既有唯一账本与编号，不建第二真相；不无证关闭 | DONE | `OPEN-TASK-REGISTER.md` 表头；`SOLUTION-001` 编号；ML-001 有证据关闭 |
| 9 | 不覆盖 dirty、不改 DESIGN-LAB/AAOS、不伪造测试/功能 | DONE | §1 基线与受保护文件；§8 未修改清单；本报告 §7 证据边界 |
| 10 | 优先交付一个真实最小问题闭环 | DONE | ML-001：AG-06 能力门从红转绿、真实产品修复、12+49 回归、适配器读回、`SOLUTION-001` |

“DONE”指该项在本轮范围内被覆盖并有落点；它不把未做的系统能力（问题中心、方案库、
AAOS 接通、exact-SHA CI）算作已完成。

### exact-SHA CI 证据（0045017a，run 39239568709）

结论 `failure`；绿作业：gate-plan / integration / observer / supply-chain-security / token-monitor；红作业：aggregate / workflow-assistance。
红作业里点名的失败测试共 8 个，其中 **8 个是本轮之前就存在的**（同一批在
本轮起点 `6b6678c3` 的 run 里就已红：DSH 日期回读、executor registry pin、账本 274/276 派生三件、
ERR-276 绑定、派生审计幂等），**本轮新增 0 个**（零回归）。
本地=远端 True（实测）。本行原文里的"工作树干净"是记录器模板常量，不是当次实测——事后核对该 head
提交时工作树确为干净，所以这句话碰巧为真，但一条没量过的断言不该出现在收据里；模板已改为实测该字段。
本轮引入过并已被抓住修掉的回归是
`test_workspace_evidence_loads_plan_governance_and_history_as_typed_sources` 的 `KeyError: 'plan'`
（归档迁移时把证据源指到了 671 B 的桩文件上），它在本 run 的失败清单里已不再出现。

### exact-SHA CI 证据（263cb8f4，run 39241704566）

结论 `failure`；绿作业：gate-plan / integration / observer / supply-chain-security / token-monitor；红作业：aggregate / workflow-assistance。
红作业里点名的失败测试共 9 个，其中 **8 个是本轮之前就存在的**（同一批在
本轮起点 `6b6678c3` 的 run 里就已红：DSH 日期回读、executor registry pin、账本 274/276 派生三件、
ERR-276 绑定、派生审计幂等），**本轮新增 1 个**：test_the_chain_is_normalised_not_merely_resolvable。
本地=远端 True。**这条判决记下的"工作树干净"是假的**：记录当下工作树有 3 份未提交改动（就是下面这项修复
的文档），模板把状态字段写成了常量而没有实测。生成器已改为读 `git status --porcelain -z` 的条数，
后续判决不会再出现未量化的状态断言。
本轮在这个 head 上确实引入并暴露了一个回归：`test_the_chain_is_normalised_not_merely_resolvable` 报
`0 != 1 : 1 citation(s) are still shorthand`。原因是归档轮写进
`docs/current/DOCUMENT-CENSUS.md` 的 owner 段落用裸文件名引用了派生脚本，引用规范化门（本地
`tests/workflow-assistance/test_default_load_doc_citations_resolve.py` 与 CI 的 workflow-assistance 作业）
都判红。修复只走工具自身的通道：`scripts/audit/normalise_doc_citations.py --apply` 改写那一个 token
为 `scripts/audit/triage_unbound_ledger_records.py`，门恢复 9/9 绿、`rewritten=0 blocked=0`，随下一提交
在其 exact SHA 上复验。

### exact-SHA CI 证据（0aa6e2e7，run 39248107323）

结论 `failure`；绿作业：gate-plan / integration / observer / supply-chain-security / token-monitor；红作业：aggregate / workflow-assistance。
红作业里点名的失败测试共 8 个，其中 **8 个是本轮之前就存在的**（同一批在
本轮起点 `6b6678c3` 的 run 里就已红：DSH 日期回读、executor registry pin、账本 274/276 派生三件、
ERR-276 绑定、派生审计幂等），**本轮新增 0 个**（零回归）。
本地=远端 False（记录当下追正提交 `78a26488` 尚未推送，本地领先一格；推送后两端相等），工作树干净。这个 head 就是上一段那条新增红的修复提交：失败清单回到 8 个，全部为本轮之前既有的红，
本轮新增为 0（`failures=8, skipped=13`，与起点 `6b6678c3` 的同名集合逐字相等）。
上一条判决里那条假的"工作树干净"已在本提交内追正，生成器改为实测 `git status --porcelain -z` 的条数。
**本轮的逐 head 证据到此为止**：再为"记录这段证据的那个提交"生成一条新判决，会让记录永远追自己的 CI，
因此随后那个只追加本段的文档提交只由它自己的 run 判定，其结论在会话里读出，不再写进报告。
