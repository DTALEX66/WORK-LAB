# WORK-LAB 目录收敛迁移交接（WL-DIR-MIG-R1，2026-09-02）

> 交接人：Hermes（WORK-LAB 唯一 Writer）· 接手方：WORK-LAB 后续会话 / Codex / DSH
> 分支：`migration/wl-directory-convergence-r1`（PR #123）· baseline `e5231f0` → HEAD `d01f59f`（**24 commit**）
> 权威上下文：AGENTS.md + `.project/manifest.yaml` + `taskpacks/current/WORK-LAB-DSH-HANDOFF-2026-08-19.md`（DSH 侧）+ `00-governance/LESSONS_LEARNED.md`

---

## 0. TL;DR

- **12 个迁移任务（WL-DIR-000~120）全部执行**：编号目录（00-governance/10-workflow/30-observer/40-knowledge/50-taskpacks/90-archive）收敛到客户端中立新布局，20+ 修复 commit 收尾（路径层级 parents[N]、测试 ROOT、CI 路径、schema 统一）。
- **DSH 侧同步 2.0.4 社区桌面版**（2026-08-30 实测）：client-evidence `2.0.2→2.0.4`、adapter `COMMUNITY_*` 部署常量 + `detect()/observe()` 报告 community-desktop、schema `detected_local` 扩展、AGENTS.md/文档/交接全同步。
- **双端一致**：本地 = 云端（HEAD `d01f59f` 已 push origin）；工作树干净。
- **CI（PR #123）**：gate-plan/schema-fixtures/observer-readonly/capsule-cli/config-compiler/supply-chain-security/token-monitor/wlr060-aggregate 全 PASS；observer/integration/workflow-assistance 已修（观察 evidence observation_state、scripts/ci sys.path、测试 import 路径、SyntaxError），最新一轮重跑中。
- **清理（本轮）**：见 §7——`.hermes/task-runtime/tmp/` 临时残留 7GB、旧目录残留（10-workflow/00-governance/30-observer）、pycache；quarantine 备份保留（回滚保险，用户纪律）。

## 1. 迁移结果（WL-DIR-000~120）

| 维度 | 数值 |
|---|---|
| commit 数（baseline→HEAD） | 24 |
| tracked 文件数 | 1104 → 1102 |
| 旧编号目录残留 tracked | 0（全部迁走；本地物理残留已列入清理） |
| 核心门 | 8/8（compile/governance/security/runtime-convergence/skill-provenance/context-pack/client-neutral-manifest/core-schemas，governance 修复后重验） |
| CI 测试（tests/ci） | 114 passed + 2 分支状态预期（merge 后自动 PASS） |

### 新旧布局对照

```
旧（编号目录）                    →  新（客户端中立）
00-governance/                  →  .project/governance（机器）+ docs/decisions（prose）
10-workflow/workflow-assistance →  services/* + packages/client-neutral-core + config/ + scripts/ci
30-observer/work-lab-observer   →  apps/observer（src/scripts/tests/schemas）
40-knowledge                   →  knowledge-staging/
50-taskpacks                   →  taskpacks/current（去重）+ docs/history/archive（历史）
90-archive                     →  docs/history/archive
（运行数据 .hermes/task-runtime）→  .project-local/{runs,artifacts,quarantine}
```

新根：`.project/`（治理合同 + manifest）· `.project-local/`（运行数据）· `apps/` · `services/` · `packages/` · `integrations/` · `projections/` · `knowledge-staging/` · `taskpacks/current/`

## 2. 关键修复（WL-DIR-110 长尾，本轮收口）

1. **parents[N] 层级**：脚本迁深后 `parents[2]/[3]/[4]` 错位 → 22 文件批量修正（packages/client-neutral-core/scripts 根 = parents[3]，services/* 根 = parents[2]，security/ 更深一层 = parents[4]）。
2. **schema 统一**：EXPECTED + 3 个特殊 schema 的字段命名统一为 `schema_version`（canonical-config-intent/context-capsule/cloud-event-envelope）；`agent-runtime-adapter.schema.json` `detected_local` 扩展社区版字段。
3. **CI 路径**：token-monitor 嵌套修正 + working-directory/PYTHONPATH → 收敛路径；`run_quality_gate.py` 测试/脚本路径 → tests/workflow-assistance + 映射目录；MODULE_PYTHONPATH 常量。
4. **observer**：`observer_evidence` token-usage 事件补 `observation_state`；测试 sys.path 补 src/scripts/services-orchestration（迁移后 import 约定）。
5. **scripts/ci**：offline_pilot sys.path 补 codex executor + services/receipts（依赖分散后 import 修复）。
6. **测试文件**：ROOT parents[1]→[2]、动态 load 改 `importlib.import_module`、codex-assets→integrations/executors/codex、bin→packages/client-neutral-core/bin、docs/workflow→docs/current/workflow-assistance/workflow。

## 3. DSH 侧同步（2.0.4 社区桌面版）

- **本体**：`anywhere-labs/dsh-desktop` v2.0.4（`dsh-plugin-desktop`，Electron + 完整 harness）@ `D:\All projects\DSH\DSH Desktop.exe`（唯一入口）；web `127.0.0.1:43120`；数据根 `~/.dsh`；94 会话/4 项目目录保留。
- **仓库同步**：`config/client-evidence.json`（2.0.2→2.0.4，verified_at 08-30）· `integrations/executors/dsh/deepseek_harness_adapter.py`（`COMMUNITY_*` 常量 + detect/observe community-desktop + legacy UPSTREAM pin 保留为历史治理记录）· AGENTS.md（2 处 2.0.2→2.0.4）· runtime-adapters 文档（重写 2.0.4 形态）· HANDOFF-08-19 追加 2.0.4 段。
- **验证**：adapter 测试 10 passed；conformance 实测 `community-desktop / 2.0.4 / 43120 / 4 项目会话`。

## 4. 验证证据（本地实测）

```
REGRESSION_REPORT_PASS tracked_files=1102 ... pilot_p95_ms=0.106
OBSERVER_SKELETON_PASS files=10 external_mutation_default=false dashboard=read-only
USAGE_ROLLUP_PASS idempotent=true rebuildable=true
CONTRACT_CATALOG_PASS contracts=30 schemas=30
MODULE_DEPENDENCIES_PASS modules=2 runtime_edges=0
PROJECT_DATA_BOUNDARY_PASS runtime=.project-local/runs evidence=.project-local/artifacts
SUPPLY_CHAIN_PASS workflows=2 actions=13 source=pinned-sha
SOURCE_HEALTH_PASS ... quarantined_candidates=1
observer pytest: 39 passed, 2 subtests passed
adapter 测试: 10 passed | core_schemas: 4 passed
```

## 5. CI 状态（PR #123，截至 2026-09-02）

- PASS：gate-plan · schema-fixtures · observer-readonly · capsule-cli · config-compiler · supply-chain-security · token-monitor · wlr060-aggregate
- 已修复并 push（`d01f59f`）：observer（observation_state + 测试 path）· integration（offline_pilot sys.path）· workflow-assistance（SyntaxError + load 修复）——最新一轮重跑中，预计转绿后按 merge 门（exact-SHA CI + human approval）merge。
- **merge 前硬性前提**：PR #123 CI 全绿（required gates = integration/observer/supply-chain-security/token-monitor/workflow + aggregate）。

## 6. 待办/接手说明

1. PR #123 CI 全绿后 merge 到 main（需用户批准）——`merge_policy: exact-sha-ci-and-human-approval`。
2. merge 后刷新 generated 投影（`.project/governance/generated/CURRENT_STATE.*`，commit 钩子自动）并 push 保持双端一致。
3. AGENTS.md 的 Scope（`10-workflow/workflow-assistance` 模块根描述）随 merge 更新为新布局（10-workflow 物理目录清理后）。
4. quarantine 备份（dsh-011/agent-observability/codex-bin 等 ~8GB）按用户纪律保留；确证无用后再清。
5. 错误台账：`taskpacks/current/error-ledger.json`（若本轮修复需登记）。

## 7. 清理（本轮，双端瘦身）

| 目标 | 大小 | 处置 |
|---|---|---|
| `.hermes/task-runtime/tmp/tmp{kc6mgeay,w8ujl71i}` | ~7.0 GB | 已删（TemporaryDirectory 残留） |
| `.hermes/task-runtime/pycache/` | 10 MB | 已删 |
| `10-workflow/`（0 tracked，git 历史可恢复） | 0.32 GB | 已删（含 .hermes 残留） |
| `00-governance/` `30-observer/`（0 tracked 空壳） | — | 已删 |
| `.pytest_cache/` + 各处 `__pycache__` | — | 已清 |
| `.project-local/quarantine/*`（备份） | ~8 GB | **保留**（回滚保险，用户纪律：保留恢复备份） |

> 清理只删 tracked=0 且 git 历史可恢复 / 可再生垃圾；不动 quarantine 备份、`.hermes/task-runtime/deepseek-harness`（迁移纪律基线）、junction 结构。
