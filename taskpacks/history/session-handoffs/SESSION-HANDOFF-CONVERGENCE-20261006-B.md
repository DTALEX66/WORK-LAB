# SESSION-HANDOFF-CONVERGENCE-20261006-B

> 只读交接记录，不授予任何权限。分支 `task-decomposition/atlas-gap-archive-20261001`（PR #162），
> 交接时刻远端头 `eb06f9e`，`main` 仍为 `cd4daa8`（本轮未合并）。
> 上一份交接：`taskpacks/current/SESSION-HANDOFF-P0C-20261006.md` —— 它的核心结论已被本轮推翻，见下 §3。

## 0. 一句话

**release 不黑屏、按钮失效是能力授权缺失、"黑屏"是 GDI 取证盲区；桌面表面证明仍欠一次目测。**

## 1. 本轮已完成（全部已提交并推送）

| SHA | 内容 | 关键证据 |
|---|---|---|
| `c6d51a6` | 窗控按钮 ACL 授权 + 吞异常修复 + 契约门禁 | 构建产物 `gen/schemas/capabilities.json` 六项授权；门禁双向注入验证 |
| `770d733` | ERR-105：新鲜度改为内容判据 + 补 src→dist 边界 | 7→14 条测试；真树三段证伪（PASS→STALE→PASS） |
| `4a8b27a` | ERR-105 台账闭环 + 修 ledger 末行 | `ERROR_LEDGER_PASS` |
| `3abf1bf` | 无边框壳顶部边距实测修复 | `.search` top `0→12`（主窗与 compact 面板） |
| `307d90b` | ERR-106/107 记录（撤回黑屏与 CDP 过度声称） | 台账 107 |
| `8003980` | 蓝图落仓 + 覆盖矩阵 + CI 接线 + 审计快照 + README 纠偏 | `BLUEPRINT_COVERAGE_PASS rows=87` |
| `a018fbe` | 重生成 current state（digest 真实变动） | `CURRENT_STATE_FRESHNESS_PASS` |
| `4115d63` | ERR-109：修我打破的 CI 计数守卫并升级为命令清单 | CI `integration` 由红转绿 |
| `0726a14` | CI 绿读回 + U19 作业内真实结论 | 19/19 pass 于 `4115d63` |
| `44b778d` | **T02 结清**：本机完整门重跑 | `QUALITY_GATE_PASS modules=180 executed=1896 ran=1904 skipped=8 exit 0` |
| `eb06f9e` | 精确 SHA 读回 + 工具陷阱记录 | 见 §5 |

另外：`C:\Users\ALEX\WorkBuddy\Worktrees\WORK-LAB\...` 工作树已迁入
`.project-local\imported-from-workbuddy-20261006\`（`.project-local` 2,309 文件 / 469,199,969 B 与
`.workbuddy` 2 文件 **逐文件 sha256 全等**），原目录与 worktree 注册已清除；`DESIGN-LAB` 的 4 个工作树
经用户确认属其他项目，**未触碰**。

## 2. 已确立的事实（不要重复论证）

1. **release 前端确实运行**：启动 0.49s 后 `GET /api/v1/snapshot` + `GET /api/v1/events`
   （`Accept: text/event-stream`）以 `Origin: http://tauri.localhost` 全部 200；主窗
   `1600×1025` visible，带 `Chrome_RenderWidgetHostHWND` 子窗。
2. **"黑屏"= GDI 盲区**：screen BitBlt 与 PrintWindow 都读 GDI 重定向表面，拍不到
   DirectComposition 合成层；`#08090a` 就是 `tauri.conf.json` 里的窗口 `backgroundColor`。
3. **按钮失效 = Tauri v2 ACL 默认拒绝**：`core:window:default` 只含只读命令；
   `allow-minimize/toggle-maximize/close`、`core:webview:allow-set-webview-zoom` 必须单独授。
4. **CDP 不可依赖**：`WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` 的 flag 确实进了浏览器进程命令行，
   私有 `WEBVIEW2_USER_DATA_FOLDER` 也生效，但 HTTP 端点在耐心轮询下（9 轮 / 12s 超时）
   **接受 TCP 却零字节**；仅早期两次短超时偶然成功。别把 `connect()` 成功当"端点可用"。
5. **CI 作业绿 ≠ 桌面表面证明**：`observer` 作业内 U19 自报 `VERDICT: SKIPPED_HEADLESS`
   （`webview_readback FAIL`、`gdi_render_proof FAIL`），exit 0 只是 R5 无头边界。
6. **Tauri 凭据链已闭**：`Record the artifact input receipt`（CI 步骤，真实 runner 已 `✓`）+
   本地 bat；门禁 `basis=build-receipt`，凭据与磁盘二进制不符即视为不可用并降级上报。

## 3. 已撤回、不得再走的三条路

- ERR-102 的"release 只画背景色"定性 → 已撤回（ERR-104）。
- "release 构建没有 CDP 端点，因为 `Cargo.toml` 缺 `[features] devtools`" → 机制错误；
  但"CDP 可达"也被过度声称，已撤回（ERR-107）。**不要为拿 devtools 改构建配置**，它解决不了这个问题。
- "mtime 判二进制新鲜度" → 已废弃（ERR-105）；`git status` 报 modified 而 `git diff` 为空是本仓库常态。

## 4. 未完成清单（分类，附真实状态）

**A. 只需你 5 秒目测（我不再自行拉界面）**
- T03/U19 真实桌面表面：跑 `.project-local\runs\u19-msvc-20261006\target\release\app.exe`
  （sha256 前缀 `6f73c14eb542f1a7`，`9,850,368 B`，22:09 构建）——
  看：①右上角 最小化/最大化-还原/关闭 是否有反应（ERR-103 修复的复认）；
  ②顶部命令行上边距观感是否合理（ERR-106，实测 12px）；③整体是否就是你想要的界面。
  你的目测结论优先级高于我任何仪器。

**B. 纯静默可做，尚未做**
- ERR-105 盲点(2)：未提交编辑把 mtime 拨到构建之前仍只能靠 mtime；要闭掉需构建期凭据覆盖
  **前端构建链自身输入**（`frontend/src`、`package-lock.json`、vite/tsconfig、node_modules 版本）。
- 覆盖矩阵缺口：蓝图原文 19 行候选 vs `.project/governance/future-candidate-registry.json` 14 条，
  **5 条未登记**（且 W03 自称 14，来源内部矛盾）。补登记是纯文档活。
- `errata`：`docs/audits/BLUEPRINT_SYNC_AUDIT_2026-10-06.md` 是按需重录的，`eb06f9e` 的 CI 结果
  尚未回写（前一条 `44b778d` 两次 run 均 success）。
- 旧账：`test_exact_tree_review.py` 在特性分支必然失败（断言 HEAD==origin/main、任务全 COMPLETED），
  CI 不调用它 —— 已写入 ERR-109 remaining_boundary，别去追。

**C. 需要你的明确授权才能做**
- 合并 PR #162 到 `main`；发行/打包发布；安装或改动全局配置；写其他项目。
- 四条旧分支退役（`audit/client-asset-inventory-20260930`、`codex/github-delivery-incident-20260929`、
  `codex/github-delivery-repair-20260929`、`g15-dsh-codex-registry-reconcile-20260930`）。

**D. 在册产品缺口（按优先级）**
- P0：`AG-19` 缺失原件恢复（原始长聊天、`WORK-LAB-SUMMARY`、9/28 startup/final 附件）；
  `U02`/`U03`/`U08` 仍 PARTIAL（P0）。
- P1：`AG-09` 双执行器黄金链（需你选项目+两执行器）、`AG-10` 模型真实 consumer、
  `AG-11` OCR/ASR 全矩阵、`AG-15` 可写薄 Control、`AG-14` 产品 UI 收敛、`AG-12`/`AG-13`、`AG-20`。
- P2：`AG-16`/`AG-17`（Super Entry 首链、Web-GPT transport 决策）、`AG-18`（与 DESIGN-LAB Launcher 分工）。
- `U18` 双执行器、`U19` 桌面层为长期挂账项。

## 5. 本轮我犯的错（新会话别重犯）

1. 用 GDI 双路径互证合成表面 → 同一盲区（ERR-104）。
2. 把 `connect_ex()` 成功说成"CDP 可达"并据此规划下一步 → ERR-107。
3. 用 mtime 判产物新鲜度 → ERR-105。
4. 给 required group 加命令却没跑 `tests/ci/test_failfast_group.py` 就推 → 打破 CI（ERR-109）。
5. 新门禁未先证伪就信：投影手改原本不报错、"不得含自身摘要"逻辑上永不可能失败（虚报保护）。
6. 用 shell 字符串改脚本/批处理：`sed` 与转义把 `\toolchains` 变成 TAB+`oolchains`，
   批处理守卫测了从未 set 的 `%BUILD_EXIT%` → 静默失效。
7. `git commit -F - <<'MSG' && git push …` 同行链接两次 → 空消息中止 + 正文被当命令执行。
   **多行消息一律先 Write 文件再 `-F`。**
8. 判定制用 `tail -1` 文本而非退出码 → 负控制套件会打印它期望的 FAIL 行，凭空造出两个失败。
9. `gh run list --branch` 把 2026-10-02 的无关旧 run 排在前面 → 差点把陌生 SHA 当本轮结果上报；
   先 `gh pr view --json headRefOid` 钉住头，再按 SHA 过滤。
10. 提交消息误粘上一条旧文案 → 只能对未推送提交 `--amend` 修消息（并用 tree sha 证明内容未变）。

## 6. 下次接手的恢复清单（按序）

1. `git fetch` → `git ls-remote origin refs/heads/main refs/heads/task-decomposition/atlas-gap-archive-20261001`。
2. 读序：`WORK-LAB-AUTHORITY.md` → `.project/governance/project-authority-index.json` → `AGENTS.md` →
   `.project/governance/taskpack-authority-index.json` → `taskpacks/current/OPEN-TASK-REGISTER.md`
   （查 `T02-FULLGATE-RERUN` / `CI-READBACK-FINAL` / `P0C-DESKTOP-PROOF` / `TOPBAR-EDGE` 四行）。
3. 工具链：Python `.project-local/toolchains/wl-py311/Scripts/python.exe`（**必须前置 PATH**，否则
   `failfast_group.py` 挑到托管 3.13.12 缺 `jsonschema` 假失败）；Node 显式加
   `D:\All projects\OS External Configuration\10-toolchains\scoop\apps\nodejs-lts\24.18.0`；
   构建用 `.project-local/runs/u19-msvc-20261006/build-tauri-msvc.bat`（已含写凭据步骤），并
   `export CARGO_TARGET_DIR=D:\All projects\WORK-LAB\.project-local\runs\u19-msvc-20261006\target`。
4. 快速自检（全静默）：`python scripts/ci/verify_blueprint_coverage.py`、
   `python tests/ci/test_failfast_group.py`、`python scripts/ci/verify_error_ledger.py`、
   `python scripts/ci/verify_project_authority_reference.py`；
   两组 `failfast_group --group observer-web-contracts|observer-python-skeleton`。
5. 不要重跑历史审计、不要重新论证 §2/§3 已定之事，直接从 §4 挑一项。

## 7. 铁律（违反即返工）

- Observer 永远只读；不新增第二账本、第二成本真值、第二套 UI、长期 shadow-main、全仓 Rust 重写。
- 未拿到证据一律 FAIL/PENDING，不伪报 PASS；本地 `QUALITY_GATE_PASS ≠ CI 绿`；CI 绿 ≠ 桌面证明。
- 新鲜度/唯一性判定用内容（哈希、`git diff`），不用 mtime、不用 `git status`。
- 新门禁必须先注入违规证伪再用；判定制看退出码。
- 多行文本/脚本先 Write 文件再执行，写后按字节核对；不手抄 SHA。
- 桌面程序启动是打扰：先做完全部静默验证，一次启动要有明确理由；用户目测优先于我的仪器。
- 只处理本项目；其他项目目录与工作树不迁移、不清理、不写。不合并 main、不发行、不装、不写全局配置。
