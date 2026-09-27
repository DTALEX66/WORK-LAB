# HERMES 更新与维护记录（2026-09-27）

**性质**：维护记录与可复核入口，**不是**新的任务权威。`currentTaskpack`（`WORK-LAB-UNIFIED-PRODUCT-CONVERGENCE-TASKPACK-20260918`）**仍然权威**；本文件是覆盖层/交接视图，登记在 `.project/governance/taskpack-authority-index.json` 的 `staticHandoffViews`（`is_authority: false`）。
**目标软件**：Hermes Agent（受管客户端）。**执行者**：DSH / DeepSeek（外部写入者身份维护 Hermes）。
**本轮结论**：Hermes 已由 `v0.21.3 (2026.9.14)` 更新至 **`v0.21.5+3115.g10938a7 (2026.9.24)`**，更新器自报 `outcome=success`、exit 0，桌面入口真实启动读回通过；**受管覆盖层本轮零新增漂移**（guard verify 前后逐字相同）；同时**登记 3 项既有覆盖层漂移**（本轮**未**修复，需单独授权）。

---

## 0. 四层证据分层（禁止合并）

| 层 | 本轮结论 | 证据 |
|---|---|---|
| ① Existence 存在 | PASS | 21/21 受管目标 live 仍在（3 项内容已漂移，见 §5） |
| ② Source equivalence 源等价 | **有缺口** | 本轮**未**发布（guard 拒绝既有漂移），覆盖层未与仓库源重新对齐；`SOUL.md` 与 3 个 skill 仍为旧基线 |
| ③ Runtime enablement 运行时启用 | PASS | `hermes --version` 读回新版本；`doctor` 读回 config v46；runtime venv 已切换 |
| ④ Behavioral application 行为生效 | PASS（限桌面入口） | 桌面 `.lnk` 启动 → 6 进程、主窗口标题 `Hermes`、`responding=True`、关闭后进程归零 |

> 本文件同时严守两类更新的区分：**厂商更新**（Hermes 代码/配置迁移/桌面产物）与**工作流覆盖层更新**（WORK-LAB 自己的 skills/SOUL/bin 发布）。二者互不证明。

---

## 1. 最终状态（可核对的值）

| 项 | 更新前 | 更新后 |
|---|---|---|
| 引擎版本 | `0.21.3 (2026.9.14)` | **`0.21.5+3115.g10938a7 (2026.9.24)`** |
| 安装 HEAD | `98f758ae7e8db83c2bb9214c3b35adf41df15f03` | **`10938a7cf93be84b9f8695699e607ab423d87db4`** |
| 配置版本 | `v45` | **`v46`**（两个 profile 均已迁移） |
| 新增提交 | — | **8183** 个（更新器自报 `Found 8183 new commit(s)`） |
| 安装方式 | `git`（`hermes-agent` 检出） | 不变 |
| Python 运行时 | 3.11.15 | 独立 runtime venv `Python 3.14.7`（`hermes doctor` 读回，已在本进程生效） |
| CLI `--version` | `v0.21.3 (2026.9.14) · upstream 98f758ae` | `v0.21.5+3115.g10938a7 (2026.9.24) · upstream 10938a7c` |
| 更新器结论 | — | `outcome=success`、`exit 0`、`finished_at 2026-09-27T02:01:38Z` |
| 受管字段 | `display.language=zh`、`display.busy_input_mode=queue` | **未被升级改动**（逐字读回一致） |
| 桌面入口 | 桌面 + 开始菜单 `.lnk` → `win-unpacked\Hermes.exe` | **未被改动**，`Test-Path=True`，真实启动读回通过 |
| hooks | `All shell hooks look healthy`（2026-09-17 复核后） | **`All shell hooks look healthy`**（1 个 hook，批准未失效） |
| 受管资产 guard | 21 目标；3 项既有漂移（拒绝发布） | **逐字相同**（3 项漂移，零新增） |
| 仓库分支 | `main` | `main`（更新后本地 == `origin/main` == `10938a7c`） |

### 1.1 `doctor` 读回（`export` 存档见 §7）

- `✓ Config version up to date (v46)`、`✓ No deprecated config keys or env vars`、`✓ state.db: WAL journal mode`、`✓ Runtime venv staged (active in this process)`、`✓ Lock file OK`
- `Found 2 issue(s)`，均**非本轮引入且不阻塞**：
  1. `state.db is large (4.1 GB)` —— `sessions.auto_prune` 早已为 `true`，官方给出的可选动作是离线跑 `hermes sessions optimize-storage`（预计回收 ~60% ≈ 2.5 GB）；
  2. `Run 'hermes setup' to configure missing API keys` —— 可选平台/工具凭据提示（Discord/Feishu/x_search/computer_use/browser-cdp 等），与更新无关。

---

## 2. 版本升级执行（官方通道）

**目标选择**：上游最新稳定 tag = **`v2026.9.24`（commit `f97608f1`，`pyproject.toml` version = `0.21.5`）**。
本机为 **Git 检出安装**（`install method: git`），官方 `hermes update` 的语义就是**跟随 `origin/main`**（`--branch` 解析为 `origin/<name>`），因此实际落点为 `origin/main @ 10938a7c`，即 **`v0.21.5+3115`**（相对发布 tag 领先 3115 个提交；GitHub compare `v2026.9.24...main` 于 09-27 读数为 ahead 3098）。

**执行链**（全部由官方更新器完成，无自定义替代流程）：

```
hermes update --yes --backup
  ├─ pre-update snapshot      : 20260927-014302-pre-update（default）+ deepseek-review 兄弟快照
  ├─ full backup              : backups\pre-update-2026-09-27-094303.zip (1.8 GB, 142.3 s)
  ├─ fetch                    : Found 8183 new commit(s)
  ├─ pull (ff)                : 98f758ae → 10938a7c，清理 128 个 stale __pycache__
  ├─ post-swap hand-off       : 交新解释器（pm）继续
  │    ├─ Node 依赖 → TUI 构建 → web UI 构建
  │    ├─ isolated runtime venv（Python 3.14.7）→ Python 依赖
  │    ├─ 桌面打包应用（Electron build + package）
  │    ├─ bundled skills 同步：default ↑3 updated / ~1 user-modified；deepseek-review ↑14 updated / ~5 user-modified
  │    └─ config 迁移 v45 → v46（两个 profile）
  └─ pm install               : agent-browser（rc=0）
```

**桌面产物说明（登记，避免误读）**：Git 检出安装**没有"下载预编译桌面包"这条路径**——桌面产物 `hermes-agent/apps/desktop/release/win-unpacked/Hermes.exe` 由**同一检出**构建，官方更新器在检出内检测到桌面需要重建时自动执行 `electron-builder` 打包。本轮实测：`win-unpacked\Hermes.exe` mtime 推进至 `2026-09-27 09:58:35`（213,953,536 B）；`desktop-build-stamp.json.contentHash` 未变（`ad2871a0…`），说明**桌面源码内容未变、产物按内容寻址重建**，不是换版本。

**用户配置保持**：更新 receipt 读回 `gateway_restart.restarted_services = []`、`failed_units = []`、`incomplete = false`、`relaunched_profiles = []`；`pm_venv_rebuild.ok = true`。受管字段与用户模型/路由/认证未出现在任何改写路径中。

---

## 3. 验收门（逐项，本轮实测）

| # | 门 | 判据 | 结果 |
|---|---|---|---|
| 1 | 版本读回 | `hermes --version` == 目标版本 | **PASS** `v0.21.5+3115.g10938a7 (2026.9.24)` |
| 2 | 配置版本 | `doctor` → `Config version up to date (v46)`，两 profile 同步迁移 | **PASS** |
| 3 | 更新器自证 | receipt `outcome=success` + exit 0 | **PASS** |
| 4 | 健康检查 | `hermes doctor` | **PASS（2 项非阻塞既有 issue）** |
| 5 | hooks | `hermes hooks doctor` | **PASS** `All shell hooks look healthy`（allowlisted / script unchanged / JSON valid） |
| 6 | 受管资产 guard | `sync_hermes_workflow_assets.py`（无 `--apply`，只读判定） | **零新增漂移**：前后 drift 集合逐字相同（3 项既有） |
| 7 | curator 漂移 | `curator_foldback.py --check` | 5 项漂移（见 §5），与厂商更新无关 |
| 8 | 桌面入口真实启动 | 启动 → 进程/窗口/响应读回 → 关闭 | **PASS** `process_count=6`、`main_window_title=Hermes`、`responding=true`、关闭后 `0` |
| 9 | 回滚材料就位 | 代码 ref + 数据备份 + 快照 | **PASS**（见 §6），且本轮备份**已核实含 `SOUL.md`（3492 条目）**，修复了 2026-09-17 记录的产品侧缺口 |

---

## 4. 与本机五维基线（AGENTS.md）的对应

| 维度 | 本轮结论 |
|---|---|
| 1 唯一入口 | 不变：官方桌面 `win-unpacked\Hermes.exe` + `hermes` CLI；**未新建任何替代启动器/第二运行时** |
| 2 桌面入口 | PASS：桌面 + 开始菜单 `.lnk` 目标链 `Test-Path` 端到端可解析，且真实启动成功 |
| 3 官方基线 + 用户配置 | PASS：官方更新器迁移 v45→v46；受管字段与用户 provider/model/auth 零改写 |
| 4 无阻塞开销 | PASS：hooks 1 个、`doctor` 无阻塞项；覆盖层未新增全局规则 |
| 5 任务级模型策略 | PASS：用户模型路由未触碰；无新增全局成本/速率上限 |

---

## 5. 既有覆盖层漂移（本轮登记，**未修复**）

`sync_hermes_workflow_assets.py`（guard，三方比较 baseline × live × candidate）**拒绝发布**，exit 1：

| 目标 | verdict | baseline | live | 判定 |
|---|---|---|---|---|
| `skills/autonomous-ai-agents/codex` | `DELETED_DRIFT` | `82aaece396b2403f` | `None` | live 目录缺失 |
| `skills/software-development/python-testing` | `UNKNOWN_LIVE_CHANGE` | `2f9ea7dde6d261ee` | `458b2005c9585bf1` | live 非工具发布的内容 |
| `skills/software-development/windows-development-environment` | `UNKNOWN_LIVE_CHANGE` | `5132fc01855817c3` | `ab8da2fab31dc8b3` | 同上 |

`curator_foldback --check`（5 项漂移）额外暴露两项：

- `SOUL.md`：`NEED_REVIEW / REWRITTEN`。**根因已定位**：live `10d1697b92260853`（mtime `2026-09-05`）**早于**仓库 `9da0bd4884af9fdb`（`config/SOUL.md`，commit `62f666e` / 2026-09-23）。即 **live 落后于仓库源**，不是 curator 新写；本轮更新**未触碰** `SOUL.md`（更新日志无相关行，mtime 未前进）。
- `skills/software-development/project-data-boundary`：`REWRITTEN`（live `725276656b1fba4a` vs 仓库 `3508aafe7a9d9343`）。

**性质判定**：全部为**本轮更新之前既存在**的覆盖层↔仓库源不一致；guard 的 fail-closed 行为按设计工作。修复属**独立治理动作**（`--adopt-baseline --adopt-target <target>@<sha256>` 或 `--suspend <target>`，或先把已复核的 live 内容折回仓库），**需用户单独授权**，本轮不做。

---

## 6. 恢复方式

| 层面 | 材料 | 可用性 |
|---|---|---|
| Hermes 数据/配置 | `hermes import "C:\Users\ALEX\AppData\Local\hermes\backups\pre-update-2026-09-27-094303.zip"` | **1,923,061,795 B / 3492 条目 / 未压缩 4,746,320,062 B**；**已核实含 `state.db`、`config.yaml`、`SOUL.md`、`auth.json`、`.env`**（两 profile 均在） |
| state.db 专用快照 | `state-snapshots\20260927-014302-pre-update`（default）、`20260927-014303-pre-update`（deepseek-review） | 存在（state.db 4.1 GB 超 1.0 GB 上限，快照按策略跳过该文件并保留更旧快照作为恢复源） |
| Hermes 代码 | reflog：`10938a7cf9 main@{2026-09-27 09:48:29} merge origin/main: Fast-forward` 之前一行为 `98f758ae7e`（旧提交仍在对象库，`git cat-file -t` = `commit`） | 可用；本轮**未生成**新的 `refs/hermes-update-backups/*`（仅 09-12/09-17 两条历史 ref） |
| 受管覆盖层 | `HERMES_HOME\.workflow-assistance-baseline.json`（21 目标基线）+ `HERMES_HOME\backups\workflow-assistance-sync-*` | 存在；本轮**未发布**，覆盖层无写入 |
| hook 批准 | `HERMES_HOME\shell-hooks-allowlist.json`（`hooks doctor` 读回 `approved 2026-09-17T12:18:25.985000Z` / `script unchanged`） | 未失效，无需刷新 |

---

## 7. 证据边界与存档（被 gitignore，**不入源码管理**）

| 材料 | 路径 |
|---|---|
| 运行证据（本轮） | `.project-local/runs/hermes-update-20260927/`：`pre-state-20260927.json`、`update-20260927-run2.log`、`doctor-after.log`、`hooks-doctor-after.log`、`guard-verify-after.log`、`curator-check-after.log`、`desktop-launch-readback.json`、`watch.log` |
| curator 漂移报告/差异 | `.project-local/artifacts/curator-foldback/curator-foldback-report.json` + 各目标 `.diff` |
| Hermes 侧更新 receipt | `HERMES_HOME\logs\update_receipts\latest.json`（`outcome=success`） |
| Hermes 侧更新日志 | `HERMES_HOME\logs\update.log`（含 `Found 8183 new commit(s)` 与完成行） |

**边界说明**：全部内容位于项目 Git 根内；未读写 `E:\`/`F:\`；未读取任何凭据、token、`.env` 值或提示/响应正文（备份**清单**仅按文件名核对包含关系，未解包内容读取）。`.env`/`auth.json` 未在本记录中输出任何值。

---

## 8. 仍存在的限制（继承 + 本轮新增）

| # | 限制 | 影响 |
|---|---|---|
| L-1 | **原生取消能力受限**（沿用 09-17 记录）：无会话级取消 | 是：禁止假设"可取消" |
| L-2 | 计费/额度 `UNKNOWN`（目录价 ≠ 账单） | 是：禁止成本声明 |
| L-3 | `EXACT_SHA_CI_UNVERIFIED`：Hermes 侧无 exact-SHA CI 覆盖 | 是：不得写 CI green |
| L-6 | curator ↔ 受管目录结构性冲突：策略为折回，删除/改写类仍需人工 | 否（新增类可自动折回） |
| L-9 | 第二 profile 独立性：`deepseek-review` 有独立 skills/SOUL；覆盖层仅作用根 profile | 是：禁止外推 |
| **L-10（本轮新增）** | **安装落点跟随 `origin/main`（`v0.21.5+3115`），非发布 tag**：本机运行的是未发布主线代码（相对 `v2026.9.24` 领先 3115 提交） | 中：稳定性风险高于 tag；若需 tag 基线，需官方支持 `origin/<tag>` 或改用 tag 检出（本轮未做） |
| **L-11（本轮新增）** | **覆盖层与仓库源不一致未收敛**（3 项 guard 漂移 + 2 项 curator 漂移，含 `SOUL.md` 落后于仓库） | 是：**覆盖层"源等价"层不成立**；修复需单独授权 |
| — | 产品备份**已含 `SOUL.md`**（本轮实测 3492 条目） | 是：**2026-09-17 记录 §2 的该缺口已关闭** |

---

## 9. 本轮未做（明确边界）

- 未修复 §5 的覆盖层漂移（guard 保持 fail-closed，不 `--adopt`、不 `--suspend`、不 `--apply`）。
- 未执行 `hermes sessions optimize-storage`（离线可选动作，需停机窗口）。
- 未改动任何 Hermes 全局规则/技能/模型/提供商/认证；未新建第二运行时或替代启动器。
- 未推 `main`、未开 PR（本轮交付停在短分支提交，按 `WORK-LAB-AUTHORITY.md` §11）。
