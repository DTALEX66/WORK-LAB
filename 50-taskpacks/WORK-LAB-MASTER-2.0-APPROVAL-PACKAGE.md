# WORK-LAB Master TaskPack v2.0 — WL3-820 Approval Package

> Status: `DELIVERED_PENDING_REMAINING_APPROVALS` (2026-08-15 local supplement; current WIP is not Git-delivered)
> Generated: 2026-08-10; Observer/Tauri evidence reconciled 2026-08-15
> Repository: `DTALEX66/WORK-LAB` · Branch: `main`
> Head: `cd4a27f769865fc40f6e02372a25db3d58f62537`
> Candidate tree (frozen, temp-index): `f1578cbd40b8edba329547efa56c74ec98a23b6d` (475 files)

## 1. 执行摘要

按 Master TaskPack v2.0（WL3-000..820）全量推进，本批次完成本地实现与验证：

```text
28 个 WL3 任务:
  VERIFIED_LOCAL: 27
  BLOCKED(工具链):  0
  LOCAL_VERIFIED_READY_FOR_APPROVAL: 1  (WL3-820 当前树交付批准)
```

## 2. 各任务最终状态（evidence grade: LOCAL_VERIFIED）

| 任务 | 状态 | 证据 |
|---|---|---|
| WL3-000 | VERIFIED_LOCAL | freshness 修复 + CURRENT_STATE 真实回读 |
| WL3-010 | VERIFIED_LOCAL | 两模块收口 + CI 无 design/minigame Gate |
| WL3-100 | VERIFIED_LOCAL | 真实平台发现（codex/hermes UNIQUE） |
| WL3-110 | VERIFIED_LOCAL | reconciler fail-closed |
| WL3-120 | VERIFIED_LOCAL | 受控复现 metadata 指纹 |
| WL3-200 | VERIFIED_LOCAL | 唯一 ownership registry v2（8 层/30 字段） |
| WL3-210 | VERIFIED_LOCAL | 三方协调器（rebase/quarantine/CAS） |
| WL3-220 | VERIFIED_LOCAL | 13 Skills 完整包 digest |
| WL3-300 | VERIFIED_LOCAL | Growth 状态机（project/global 分门） |
| WL3-310 | VERIFIED_LOCAL | 记忆治理（TTL/supersedes/隔离/pinned） |
| WL3-320 | VERIFIED_LOCAL | Skill/Plugin/MCP 供应链扫描 |
| WL3-330 | VERIFIED_LOCAL | 模型 lane/billing（subscription not-metered） |
| WL3-400/410 | VERIFIED_LOCAL | durable worker + 事务 lease |
| WL3-420 | VERIFIED_LOCAL | 跨项目注册（真实 MINIGAME canary） |
| WL3-500 | VERIFIED_LOCAL | Canonical SQLite WAL |
| WL3-510 | VERIFIED_LOCAL | 四类真实 collector |
| WL3-520 | VERIFIED_LOCAL | CI concurrency/timeout |
| WL3-600 | VERIFIED_LOCAL | 真实 SSE（heartbeat/cursor/续传） |
| WL3-605/610 | VERIFIED_LOCAL | 唯一 Observer UI + canonical 消费 |
| WL3-620 | VERIFIED_LOCAL | 项目内 xwin sysroot + rust-lld；`cargo tauri build --no-bundle` 真实 artifact 与 WebView2 验收 |
| WL3-700 | VERIFIED_LOCAL | 四真实 Adapter conformance |
| WL3-710 | VERIFIED_LOCAL | 未来 Agent 分级（L0-L4） |
| WL3-720 | VERIFIED_LOCAL | 6 换平台演练 core 不分叉 |
| WL3-800 | VERIFIED_LOCAL | 集成门禁 6 项检查通过 |
| WL3-810 | VERIFIED_LOCAL | 体积审计 438 文件/2.65 MiB |
| WL3-820 | LOCAL_VERIFIED_READY_FOR_APPROVAL | 本包 |

## 3. 本地验证证据

```text
Full quality-gate verify sequence: 21 gates PASS
  governance 443 tests OK (skipped=4) · runtime-convergence 91 tests OK
  compile/security/schemas/adapters/ACL/OTel/usage/memory/ledger/portable/shell/pwsh PASS
Observer: Python 57 tests OK (incl. canonical projection + events retirement)
          JS 43 passed, 0 failed
Root CI suite: 14/14 files pass (test_exact_tree_review precommit-clean precondition expected-fail by design)
Browser visual acceptance: console_messages=0 js_errors=0 (dark dashboard)
Real dual-project canary: WORK-LAB + MINIGAME (collector + SSE LIVE frame)
Swap drills: 6/6 core-not-forked
Repo size audit: tracked=438 files, 2.65 MiB, duplicate groups=1
WL3-800 integration gate: 6/6 checks passed
CURRENT_STATE freshness: PASS (head 699ab50, branch main, CI run 31344245919)
CI routing: GATE_PLAN_PASS required_gates=[observer] for observer-path changes
Frozen candidate tree: f1578cbd40b8edba329547efa56c74ec98a23b6d (475 files, temp-index, no real index mutation)
GATE-RUNTIME-CONVERGENCE: claimable=True — 9/10 passed; #9 Tauri real Sidecar
  is toolchain-only pending (cargo absent) and does not block per Master TaskPack §15
```

2026-08-15 当前本地树补充证据：Observer JS `53 passed, 0 failed`；Sidecar v3 focused `12 tests OK`；正确 production Tauri 命令已生成并启动 `src-tauri/target/release/app.exe`；真实 WebView2 已读回 Snapshot/SSE、TaskPack、审批、治理、历史与来源。该证据仍是本地 dirty-tree evidence，不冒充 exact-SHA CI、签名安装包或 release。

本轮还修复了初始 snapshot 失败后的产品内重试、SSE 重连退避被重置、多客户端连接状态误判、响应头阶段断开导致的连接计数泄漏，以及 sidecar 启动时间冒充 heartbeat/writer freshness；不依赖启动器 workaround，也不把连接可达性提升成持续 writer `LIVE`。

## 4. 唯一批准清单（状态截至 2026-08-10 更新）

1. **commit/push/PR** — ✅ 已完成：#33/#34/#35/#36/#37/#38/#39/#40/#41/#43/#44/#45 全部 squash merge 到 main（head `ee909fd`）；
2. **Hermes/Codex global config live apply** — ✅ Codex overlay v3 已 apply+verify（10 skills，含 openhuman-integration 与 self-improvement，PR #41/#43）；Hermes live 未动（按边界合同）；
3. **双入口/双安装卸载或配置迁移** — ✅ 已对账：入口矩阵与职责边界见 `docs/workflow/dual-entry-install.md`（Hermes setup.* → sync_hermes_workflow_assets；Codex legacy bootstrap 仅目标不存在时最小引导，canonical sync 管理全部受管表面；无并行安装面）；
4. **Windows toolchain/portable/sign/release** — ◐ WORK-LAB Observer Tauri 工程与 portable production EXE 已在项目内 xwin/rust-lld 路径构建并运行；代码签名、installer/ZIP、release 仍未执行；
5. **paid provider smoke** — ✅ 已执行（2026-08-10）：deepseek `WA_SMOKE_221826_ds` 与 openai-codex `WA_SMOKE_221837_gpt` 精确 marker 回读，EXIT=0；kimi 未登录跳过；凭据未读取；
6. **真实外部项目 tracked profile** — ❌ 未执行（MINIGAME 仅只读 canary，未写）；
7. **归档删除或 Git 历史减重** — ✅ 已完成：WORK-LAB-ARCHIVE 退休删除（含敏感 Chrome 测试痕迹），证据并入 `90-archive-manifests/migration-20260805/`（PR #40）。

## 5. 明确未宣称

- 当前 dirty tree 的 exact-SHA CI — 未执行；历史 #33-#41 main CI 不能证明当前 Observer WIP；
- 便携 production EXE — 已本地构建并运行；未签名、未打 installer/ZIP、未发布；
- 正式 production release — 否；
- Hermes live apply、真实外部项目 profile 写入 — 否（待逐项授权）；paid provider smoke 仅保留 2026-08-10 历史证据，不冒充当前树验证。

最终状态：**`DELIVERED_PENDING_REMAINING_APPROVALS`** — WL3-620 本地技术阻塞已解除；当前 Observer/Tauri WIP 已本地实现、测试、构建并运行。当前树的 commit/push/CI、签名/installer/ZIP、Hermes live apply、外部项目 profile 与正式 release 仍是独立授权/发布边界。
