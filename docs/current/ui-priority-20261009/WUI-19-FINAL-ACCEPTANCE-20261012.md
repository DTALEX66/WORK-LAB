# WUI-19 核心桌面最终验收报告（2026-10-12 · 分层）

本报告按交付层次写：**实现 / 测试 / 真实来源 / 桌面安装 / 接受 / 发布**。
措辞纪律：`PASS` 只在对应层有可复算证据时使用；缺证据的层写「未执行」或「未通过」，不写成 PASS。
包内 `docs/history/owner-inputs/record-20261010/ui-v2-readable/WORK-LAB_UI_深化_v2/verification/model_tests.txt`
属模型自测，**本报告不把模型自测当实机通过**。

判定基线（成文时实测，非继承交接措辞）：

| 项 | 值 | 复算方式 |
|---|---|---|
| 分支 | `task-decomposition/atlas-gap-archive-20261001` | `git rev-parse --abbrev-ref HEAD` |
| HEAD | `14713aa31fb90c01b3d968e6134426f7cf790ccd` | `git rev-parse HEAD` |
| `origin/main` | `cd4daa83e107afab8438c0e85f63a10e75314d5a` | `git rev-parse origin/main` |
| 本线领先 main | **481** 个提交 | `git rev-list --count origin/main..HEAD` |
| 工作集 | 未提交（commit/push 需 owner 单独授权，本轮未执行） | `git status --porcelain` |

---

## 0. 结论（先说不能交付的部分）

**当前状态是「可评审工作集 + 明确缺口」，不是「成熟可部署」。**
生产阻断项未过：桌面 200% 显示缩放派生检查失败；原生键盘门从未产出判定；六条云端审计缺陷本轮已修但未提交、未进 CI；
隔离试用的写入面（发起/取消）未获授权，三页因此展示不出一次真实端到端试用；
本地全量门在本沙箱内 `GATE_EXIT=1`，归因见 §2.1（其中 4 组是本轮引入并已修，剩余为宿主删除守卫与符号链接权限）。

---

## 1. 实现层

| 面 | 状态 | 证据 |
|---|---|---|
| Observer 前端（29+ lane） | 已实现 | `apps/observer/frontend/src/lib/viewRegistry.ts`（本轮新增 `trial-plan` / `trial-failure` / `trial-readback` 三 lane） |
| v3 快照投影 | 已实现 | `packages/client-neutral-core/scripts/snapshot_api.py`；本轮新增 `operationProgress` / `isolatedTrials` 两段 |
| 组合根接线 | 已实现 | `services/orchestration/composition_root.py`：`_ci_rows` 补 `projectId`、`_git_state` 不再回退他仓、`_task_ledger_read_models` 读 Task Ledger |
| 隔离试用三页 | 已实现（读侧） | `apps/observer/frontend/src/views/IsolatedTrialView.tsx`，页内 `button/input/select/textarea` 计数 0 |
| 隔离试用写入面 | **未实现** | `services/control/control_service.py` 对真实客户端目标继续按 `TARGET_NOT_AUTHORISED` 拒绝；本轮未自开可写目标 |

本轮修复的六条云端审计缺陷（来源 WL-REC-0104，SHA-256 `b8bd438e…`）：

| 编号 | 缺陷 | 修法 | 账本 |
|---|---|---|---|
| WL-L01 (P1) | 项目 Git 错归属（两处 `or` 回退顶替他人仓库） | 只读 `git_map[project_id]`；缺失即 UNKNOWN；新增 `sourceProjectId` 命名归属 | ERR-268 |
| WL-L02 (P2) | 项目 CI 恒为空（`_ci_rows` 丢 `projectId`） | 投影补 `projectId`，下游过滤谓词得以成立 | ERR-269 |
| WL-L03 (P2) | 部分估计被 `_rollup_usage` 提升为 EXACT | 抽出共享谓词 `_merge_cost_quality`，两处同规则 | ERR-270 |
| WL-L04 (P2) | 吞掉 `setItem` 异常仍写「已自动保存」 | `writeModel` 返回 outcome；失败态显示「未保存」+ 原因 + 重试 | ERR-271 |
| W01 (P1) | 传输徽标以本地 flag 覆盖后端真值 | 单点派生 `transportTruth(snap, live, error)` + 采样时刻 `sourceWatermark` | ERR-272 |
| W02 (P2) | 画布：连线无效、No active pointer、overlay 吞平移、fit 只重置 zoom | `toModel` / `nodeAt` / `connectingRef` / 背景判定 / fit 五处 | ERR-273 |

## 2. 测试层（本轮全部实测）

| 检查 | 结果 |
|---|---|
| 新增 Python 守门 | `test_snapshot_project_git_ci_and_usage_precision.py` 11 例 OK；`test_isolated_trial_snapshot_surface.py` 5 例 OK |
| 新增前端守门 | `workflowEditorPersist.contract.test.tsx` 4 例；`topbarTransportTruth.contract.test.tsx` 21 例；`workflowCanvas.geometry.test.tsx` 13 例；`isolatedTrial.contract.test.tsx` 13 例 —— 均 OK |
| 快照回归 | `test_sidecar_v3_snapshot` + `test_snapshot_v3_schema_is_the_single_shape_authority` + `test_snapshot_sse_live` 共 **50 例 OK** |
| 前端全量 | `tsc --noEmit` 退出 **0**；`vitest run` **62 文件 / 710 用例全绿** |
| 账本形状门 | `tests/ci/test_register_table_shape_is_uniform.py` 9 例 OK |
| 引用门 | `tests/workflow-assistance/test_ui_v2_csv_citations_resolve.py` 8 例 OK（本轮因插行导致 5 个 `path:line` 指针失配，已按守门谓词 `pointer_findings` 列全并逐条重定位） |
| 合同面 | `CONTRACT_CATALOG_PASS contracts=45 schemas=45`；`CONTRACT_SSOT_PASS contracts=45 disk_schemas=57 unlisted_declared=12`；`GENERATED_CONTRACT_TYPES contracts=45` |
| 错误账本 | `ERROR_LEDGER_PASS entries=272 classifications=14 raw_sensitive_data=false counts_consistent=true` |
| 伪证（守门有效性） | 5 个伪证脚本全部 PASS：`falsify_l01_l03_fixes.py`（8 项定罪）、`falsify_l04_claim.py`（3 项定罪）、`falsify_w01_transport_truth.py`（13 项定罪）、`falsify_w02_canvas.py`（8 项定罪）、`falsify_wui21_trial_pages.py`（承载面 2 项 + 页面 2 项定罪）；每次均按 sha256/字节快照还原 |
| 本地全量门 | **未通过（NOT GREEN）**：`python services/orchestration/run_quality_gate.py verify` 两次实测均为 `GATE_EXIT=1`，`failed_gate=governance`，`modules_run=249/250`，`Ran 2702 tests` → `FAILED (failures=12..21, errors=14, skipped=6)`。逐项归因见 §2.1 |

### 2.1 本地门未通过：逐项归因（不改绿、不跳过）

第一次跑（与 reseal/vitest/build 并发）`failures=21 errors=14`；清空并发后第二次跑 `failures=12 errors=14`。
第二次的 26 项失败全部落在四个模块，且与本轮改动无关，逐项有据：

| 模块 | 数量 | 归因 | 证据 |
|---|---|---|---|
| `test_workflow_governance` | 15 | **环境**：工作台 CLI 的 `sitecustomize.py` 在 `tempfile` 清理时触发批量删除守卫（`_check_bulk_delete_guard` → `SystemExit(1)`），因此 12 个 `codex_global_guidance` / `portable_install` 用例在**独立运行时通过、在门批量里报错** | 完整 traceback 指向 `…/cli/vendor/shim/sitecustomize.py:873 _check_bulk_delete_guard` |
| `test_github_delivery` | 10 | 同上（ERROR 发生在 teardown） | 单跑该模块 **16 passed** |
| `test_machine_identity::test_symlinked_runtime_ancestor_is_rejected` | 1 | **既有失败 / 环境**：Windows 符号链接权限 | 把本轮源码改动 `git stash` 后单跑**仍失败**，证明与本轮无关 |
| `test_action_plan_sync::test_plan_rejects_real_symlinked_managed_parent_when_supported` | 1 | 同上 | 同上 |

第一次跑里另有 4 组**确属本轮**的失败，已全部修复并复跑通过（不在第二次的失败列表里）：

| 门 | 失败原因 | 修法 |
|---|---|---|
| `test_default_load_doc_citations_resolve` | 账本新写的 15 处引用仍是简写 | `scripts/audit/normalise_doc_citations.py --apply` 多遍至 `rewritten=0`，并把 6 处脚本名展开为 `.project-local/runs/wui-20261011/…` 全路径 |
| `test_ledger_fix_commit_binding` | ERR-268..273 记 `PASS` 却无 `fixedCommit` | 未提交前一律降为 `PARTIAL` 并在 `lifecycle.note` 写明原因（commit 需 owner 授权） |
| `test_ledger_regression_command_targets` / `test_ledger_unbound_triage` | 派生审计对着旧的 265/269 条账本 | 按序重发 `ledger_regression_command_targets.py --apply` → `triage_unbound_ledger_records.py`，两门 30 例全绿 |
| `test_generated_contract_types_project_the_schema` | 新增两段后生成类型多出 4 处 collapse，且门把 7 写死 | 前端 `GENERATED_COLLAPSED_PATHS` 补 4 条实测 collapse；门的地板由 `assertEqual(7,…)` 改为 `assertGreaterEqual(len(measured), 11, …)` 并写明理由（真正的双向不变式是紧邻其后的 `measured == declared` 相等断言，未被削弱） |

结论：**本地门在本沙箱内无法转绿，且这不是产品红灯**——它卡在宿主 CLI 的删除守卫与 Windows 符号链接权限上。
CI 的结论仍须以同一 SHA 的 runner 为准；本仓**没有**在本地把它读成 PASS。

环境侧非产品故障（如实记录，不改绿）：`vitest` 偶发 `EPERM ... AppData\Local\Temp\...\web\40b9f1f3…`
未处理错误，来自 brokered fs shim 写临时文件；复跑全绿。

## 3. 真实来源层

| 项 | 状态 |
|---|---|
| 渲染 bundle | **`01b09ea79711c3a8deac06e8c1e706d43951e72e5fdf14521628c9c1d229ed8a`**（本轮三次重建后作废了 `3e01320a…`、`77161e86…`、`9ea98ba2…`） |
| 证据封印 | `EVIDENCE_SEAL_PASS bundle=01b09ea7… files=28 BOUND=21 UNBOUND=4 STALE=3 cited=9/9` |
| 渲染读回 | 12 屏截图 + 几何/可读性/显示缩放/SSE 修订收据均按步重跑；几何门 `GEOMETRY_GATE_PASS`，可读性四步 `LEGIBILITY_GATE_PASS`，SSE `SSE_REVISION_GATE_PASS`（伪证步 exit=1 为其自身对照，按设计记 PASS） |
| 未绑定收据 | 4 张 `UNBOUND`（不带 bundle 身份，如 `legibility-settled.json`）——如实保留，不改写为已绑定 |
| STALE 天花板 | 3 张 `keyboard-focus` 系列：native 键盘门报 `KEYBOARD_FOCUS_GATE_NOT_RUN`，**无 release app.exe 时重建 dist 也造不出该判定** |
| 验收清单 | `UIV2-ACCEPTANCE-CHECKLIST.csv` **44 行 × 9 列**：`通过 3 / 部分通过 16 / 未通过 2 / 未执行 22 / 不执行（按决定）1`（本轮 T18 由「未执行」改「部分通过」，T19 仍「未执行」并改写理由） |
| 绑定矩阵 | `UIV2-INTERFACE-BINDING-MATRIX.csv` **40 行 × 14 列**：`已绑定 0 / 部分 21 / 待绑定 19`。**没有一行能同时给出真实字段路径、源码位置与证据**，故一行都不许用演示值凑成「已绑定」 |

## 4. 桌面安装层

| 项 | 状态 | 说明 |
|---|---|---|
| Rust/Tauri 构建 | 本机无证据 | CI 的 observer 作业在 `33051db7` 跑过 `Build the real Tauri desktop binary (MSVC)` 与 `U19 real-WebView E2E readback (WINDOWS_TAURI_E2E)`；**那是 CI 的读数，本机没有 release 二进制** |
| Windows 安装/卸载/升级 | **未执行** | 本轮未做，也不由本仓自行安装到用户机器 |
| 用户备份/恢复演练 | **未执行** | 依赖上一项 |
| 原生键盘门 | **未执行** | `KEYBOARD_FOCUS_GATE_NOT_RUN`，证据面自报 |
| 200% 显示缩放 | **未通过** | `DISPLAY_SCALING_GATE_FAIL`：HUD 440×780 logical、`resizable=false` → 需 880×1560 physical，实测工作区 2560×1392，「弹窗不裁切」在 200% 不成立。修法（HUD 尺寸 or 允许滚动/缩放）需 owner 定夺 |
| 移动端 | 按决定不做 | 用户 2026-10-07 已删除该范围，390/320/768 三档停在同一权威下 |

## 5. 接受层

| 项 | 状态 |
|---|---|
| 本轮六条审计缺陷 | **已修 + 有守门 + 有伪证**，但**未提交、未进 CI**；Linux 结论必须由同一 SHA 的 runner 给出，本地绿不算 |
| 隔离试用读模型 | 合同 + 快照承载段 + 三页已交付（读侧）；**事务未发生**，三页当前只会显示 `UNKNOWN（NO_PRODUCER）` |
| 迁移差异/目标验证 | **未执行**：上游四个生产者（`migrationTarget`、差异投影、隔离试用执行、目标侧证据）仍缺，本仓 `capabilityMigration.ts` 只负责把它们保持 `NOT_PROJECTED` |
| 对端协作 | **未执行**：属 WUI-20，需真实对端且发送需单独授权 |

## 6. 发布层

| 项 | 状态 |
|---|---|
| commit / push / PR / merge | **未执行**（需 owner 单独授权） |
| `config.apply` / `readback` / `rollback` | **未获权**，对真实客户端目标继续按 `TARGET_NOT_AUTHORISED` 拒绝 |
| 远端 LFS 载荷第三方复证 | **未走通**：干净克隆里 `git lfs fetch` 报 `AccessDownload=none`，且被无关 `missing object: 3811d93f…` 中断；现有依据只是 push 成功 + `git lfs push --dry-run` 0 行。待补：带凭据的定向下载并比对 SHA-256 `b8bd438e…`（8,038,362 B） |
| 生产阻断项 | 存在（见第 4、5 节），因此**只能交可评审工作集 + 明确缺口** |

---

## 7. 遗留清单（按可执行顺序）

1. 桌面 200% 显示缩放：HUD 尺寸或允许滚动/缩放 —— **owner 决定**。
2. 授权 `config.apply` / `readback` / `rollback` 的目标面 —— **owner 决定**；本仓不自行开可写面（等于自授权）。
3. 隔离试用写入面（WUI-10 约束③）：恢复点只存本次触及范围前态 + 发布摘要，摘要匹配才自动恢复；现成机制在
   `integrations/executors/hermes/managed_asset_baseline.py` 与 `services/policy/single_field_apply_loop.py`。
4. WUI-08 四步缺口的上游生产者：`migrationTarget`、差异投影、目标侧证据。
5. Windows 安装/卸载/升级 + 用户备份恢复演练（需实机）。
6. 远端 LFS 载荷第三方复证（需凭据）。
7. commit / push / CI 复核：把本轮六条缺陷送进同一 SHA 的 runner，Linux 结论以 runner 为准。
8. 活账本 pin 密度：25 行仅 1 行带可核 commit pin —— **owner 决定**是否在 live 表补 pin。
9. 卫生项（破坏性，待授权）：`.project-local/runs/tmp` 残留约 2,033 KB 的清理（需先证明无人引用；
   短名 `t.log` 在 tracked 文本里以子串命中，故上轮未删）；`.project-local/runs/upload-verify-1791720279/` 可再生 scratch；
   三个无独有提交的本地分支（`wui-10/command-identity-readback`、`workbuddy/…381e33ec`、`ui-taskpack-e-20260930`）的删除。

## 8. 本轮自己踩的坑（留给下一轮当约束）

- **伪证脚本不能用「缺陷文本」做还原键**：当缺陷是空字符串时，`text.replace("", fixed)` 会把内容插到文件头。
  本轮发生两次（`falsify_l01_l03_fixes.py` 把 `composition_root.py` 的两行插到第 1 行；
  `falsify_wui21_trial_pages.py` 同样插到文件头且未被检出）。改为**植入前取字节快照、按字节还原**后才可靠。
- **`Path.write_text` 在 Windows 会把 LF 写成 CRLF**：还原时整个文件行尾被改写，而 diff 只显示那一小段。伪证脚本一律字节读写。
- **一次跑完 10 步的重封会被环境删除守卫拦下**：各仪表的 Chrome profile 清理在单次调用内累积超过批量阈值
  （实测 297→321 个文件/次），9 步被记为红但并非产品红。改为每步一次调用后各步按其实况结算；没有绕过任何守卫。
- **插行使 CSV 的 `path:line` 指针腐烂**：本轮 5 个指针失配，必须用守门谓词自身（`pointer_findings` +
  `tracked_file_bodies`）列全，再按引用码文本重定位，最后复跑引用门确认。
- **新增 registry lane 必须同一改动里进导航分组**，否则 IA 不变式门立刻红（`navInvariantViolations()`）。