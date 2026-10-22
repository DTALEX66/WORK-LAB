# 跨模块任务卡：问题中心的生产者与界面合同声明（2026-10-22）

**状态：** CURRENT / 由 owner 本轮指令授权（「现在你按照审计报告来做后端 前端我交给STITCH 做好了 再告诉给你接入」）
**卡片性质：** AGENTS.md 规定跨模块改动需要一张显式卡；本次改动同时落在两个规范模块根上，这张卡就是那张。
**权威链：** 最新用户决定 > `WORK-LAB-AUTHORITY.md` > `.project/governance/project-authority-index.json` >
`taskpacks/current/WORK-LAB-AUTHORITY-CONVERGENCE-TASKPACK-20261019.md` > 唯一 open register > `AGENTS.md` >
`module-ownership.json`（`crossModuleWrites: "explicit-cross-task-only"`）。

## 1. 涉及的模块与写入归属

| 模块根 | 归属 | 本次改的文件 | 单一写者 |
| --- | --- | --- | --- |
| `packages/client-neutral-core` | workflow-assistance | `scripts/issue_projection.py`（新）、`scripts/canonical_store.py`、`scripts/snapshot_api.py`、`scripts/snapshot_validator.py`、`generated/contracts.ts`（生成物）、`packages/contracts/schemas/workflow/snapshot-v3.schema.json` | workflow-assistance |
| `apps/observer` | work-lab-observer | `frontend/src/types.ts`、`frontend/src/contractConformance.ts` | work-lab-observer |
| 支撑面（非模块根） | workflow-assistance | `services/orchestration/composition_root.py`、`tests/workflow-assistance/test_issue_projection.py`（新）、`tests/workflow-assistance/test_snapshot_issue_section.py`（新）、`tests/workflow-assistance/test_canonical_store_v2.py`、`tests/workflow-assistance/test_snapshot_v3_schema_is_the_single_shape_authority.py` | workflow-assistance |

Observer 侧只新增**合同声明**（可选字段与编译期 `Refines` 断言），没有任何渲染消费者、没有可点控件、没有任何写路径：
`PINNED_REFINEMENT_PATHS` 故意不加入 `issues`/`issuesSummary`，所以
`scripts/ci/verify_snapshot_keys_rendered.py` 的 22 键总体不变、界面仍不消费这两个键。
这正是 owner「前端交给 STITCH，做好再接入」的边界：契约先存在，画面后来才有。

## 2. 为什么必须同时改两侧（不是顺手扩张）

`tests/workflow-assistance/test_snapshot_v3_schema_is_the_single_shape_authority.py` 断言
「schema 顶层键集 == `types.ts` 的 SnapshotV3 声明」，两个方向都比。只加后端键会让它判红：
这是 ROADMAP 第 11 行那条「不许后端有、界面不说」的机器形式。所以加键的动作天然跨模块，
拆成两个 PR 只会让其中一枚带着红门进 main。

## 3. 交付内容与验收标准

| 项 | 落点 | 验收（已实测） |
| --- | --- | --- |
| 从已存事实派生问题 | `issue_projection.py`：10 类闭合词汇、声明式优先级规则表、指纹去重单一机制、分母与来源状态 | `tests/workflow-assistance/test_issue_projection.py` 20 例，含「每类必须真能产出」「absent≠空」「扫描截断不得自称完整」 |
| 快照携带 | `snapshot_api.build_snapshot` 条件展开 + schema `properties` 与双向 `allOf` 条件 | 4 枚植入反例（缺 scope、重复指纹、带内容字段、分母不自洽）均被拒；无 issues 的快照不带键 |
| 运行期守门 | `snapshot_validator._validate_issues` | `tests/workflow-assistance/test_snapshot_issue_section.py` 17 例 |
| 生成合同 | `scripts/ci/generate_contract_types.py` → `contracts.ts` | `npm run typecheck` exit 0；前端 `vitest` 68 文件 826 例全绿 |
| 真机读回 | `services/orchestration/sidecar.py` 随机端口起，`/api/v1/snapshot` 实取 | 25 键、`valid=True errors=[]`、`issues` 1 行（`SOURCE_INCOMPLETE_COVERAGE`，work-lab），`rowsScanned=8 sourcesRead=4 complete=True` |

## 4. 明确不做

- 不做界面呈现、不加控件、不加路由（STITCH 那一轮）。
- 不新增 Control 动词，不改 `config/adapter-registry.json`；问题的状态变更仍无写路径，投影只报 `status: OPEN`。
- 不接通问题→修复任务包的生成（那是下一张卡），不在本卡里声称闭环已完成。
- 不建第二任务账本；`issue_projection` 只读 canonical 事实，不写任何账。

## 5. 退出与回滚

回滚按文件集合整体反转：删除 `issue_projection.py` 与两份新测试、
把 `snapshot_api.py`/`snapshot_validator.py`/`composition_root.py`/`canonical_store.py`/schema/`contracts.ts`/
`types.ts`/`contractConformance.ts` 恢复到卡前字节即可，无数据迁移、无外部副作用。
`canonical_store.upsert_collector_health` 的收紧（ERR-290）是独立可回退的一处：它拒绝未映射键与空写，
既有调用方与全部测试都用 camelCase 已映射键，实测不受影响。
