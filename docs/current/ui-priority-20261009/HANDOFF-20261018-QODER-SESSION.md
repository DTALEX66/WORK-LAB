# 交接提示词 · 2026-10-18 晚段（main `f6077d18` → QODER 新会话）

> **FROZEN_20261019 — 本文是 UI 轮次的历史交接，不再是当前指令。**
> 用户 2026-10-19 决定：其他任务冻结，唯一 CURRENT 为
> `taskpacks/current/WORK-LAB-AUTHORITY-CONVERGENCE-TASKPACK-20261019.md`；
> 当前路线图见 `docs/current/authority-convergence-20261019/ROADMAP.md`。
> 本文数字与证据保留原样，未完成项不被冻结关闭，也不因冻结被视为已交付。

> **这是给下一个会话的提示词，不是权威。** 权威顺序仍是
> `WORK-LAB-AUTHORITY.md` → `.project/governance/project-authority-index.json` → 唯一 CURRENT 任务包 →
> `taskpacks/current/OPEN-TASK-REGISTER.md`。本文所有数字都注明了测量命令与口径；**未测的写"未测"**。
> 本文与机器的冲突，以机器为准，并把本文当缺陷改掉。
>
> 上一份交接是 `docs/current/ui-priority-20261009/HANDOFF-20261018-SESSION.md`（基线 `fae41c4d`，仍有效，
> 本文只覆盖它之后的增量）。两份冲突时以**本文**为准。

---

## 0. 先做这四步（不要跳过，也不要先读历史）

```bash
git fetch origin && git log --oneline -1 origin/main      # 期望 f6077d18（PR #177 的 squash 合并）
gh run list --branch main --limit 3                        # 期望两个 workflow 都 success；PR #177 是 12/12
.project-local/toolchains/wl-py311/Scripts/python.exe -V   # 期望 Python 3.11.15
git status --short                                         # 期望只有并行写者的 4 个文件（见 §6）
```

然后按 `AGENTS.md` 的 8 步权威引导链读：`WORK-LAB-AUTHORITY.md` → 机器权威索引 → `AGENTS.md` →
CURRENT 任务包 → 唯一 open register → 相关机器合同。**别先通读历史资料**（`docs/history/**` 是冻结证据，
只按需点名查）。

### 0.1 交接时的分支态（与上一份不同，注意）

| 项 | 值 |
|---|---|
| `origin/main` | `f6077d18`（PR #177 已合并） |
| 本地 `main` | 已用 `git branch -f main origin/main` 同步到 `f6077d18`，**未 checkout** |
| 当前 HEAD | `feat/w06-stream-cost-and-audit` @ `8f6540df`（内容已进 main，分支**未删除**） |
| 开放 PR | 0（#176、#177 均已合并） |

因为有 4 个并行写者文件是脏的，**不要为了删分支而 `git switch main`**；需要同步 main 就用
`git branch -f main origin/main`（不动工作区）。

---

## 1. 这一轮做了什么（一句话版）

补齐了 **W04 的最后一块读数**、**W06 的测量半条**，做了一次**全量审计（定位/前端/后端/门禁）**，
修掉一个**发布路径上的真缺陷**，并把 PR #177 从四轮红推到 12/12 全绿合并。

### 1.1 W04 补齐：CI runner 的桌面能力读数

`scripts/audit/desktop_capability_probe.py` 的六层里，只有 `session` 在托管 runner 上是 FAIL。
读数（run `39121405373`）：`session FAIL` / `display 1024x768 PASS` / `draw 0xff00 PASS` /
`webview2 154.0.4258.62 PASS` / `loopback PASS` / `cleanup PASS`。
**判读：这是环境缺一层（无交互会话），不是产品缺陷**——这类环境不得尝试 U19 回读。
已写进 `docs/current/ui-priority-20261009/DESKTOP-VERIFICATION-LAYERS.md`，PR #176 合并。

### 1.2 W06 的测量半条：探针 + 基线

新探针 `scripts/audit/observer_stream_cost_probe.py`（可复跑；退出码 0/1/3 = MEASURED/FAILED/INCOMPLETE）。
数字在 `docs/current/ui-priority-20261009/STREAM-COST-BASELINE-20261018.md`：

- **CPU**：三个窗口各差一件事，占单核 **0.17% / 0.36% / 1.04%**。
- **端到端延迟**：n=10，min **6.484s** / p50 **6.500s** / p95 **7.485s**。
  由 **7.5s 的 SSE 推送节拍**决定（心跳 15s、watcher 轮询 0.25s 都不是瓶颈），**属设计包络不是回归**。
- **推论**：流成本约单核 1%，所以 W02 悬置的"token-monitor 缓存优化"在这条路径上**不值得做**。

### 1.3 全量审计（四技能）

报告在 `docs/audits/FULL-AUDIT-20261018.md`（`docs/audits/**` 是冻结根，不被活文档路径门扫描）。
一句话结论：**定位没漂，承诺漂了**。

- 定位一致：前端**零写路径**实测成立（零 POST/PUT/PATCH/DELETE）、两个模块根、外部软件执行业务、手机端不做。
- 四条自我承诺各有**运行期反例**：①证据摘要自证（`apps/observer/frontend/src/lib/evidenceRange.ts:309-322`
  拿同一个 `wholeDigest` 跟自己比，必绿）；②采集器"跑了"被记成"交付了"
  （`packages/client-neutral-core/scripts/collectors.py:110` 空 records 仍 `ok=True` → 健康表新鲜 →
  coverage N/N → live gate 可判 LIVE）；③单写者有三处裸 `sqlite3` 旁路
  （`services/receipts/usage_estimator.py:81`、`services/receipts/execution_recorder.py:53`，且硬编码 `D:\`
  路径、无 `__main__` 保护）；④Observer 运行时跨模块导入编排内部
  （`apps/observer/src/observer_store.py:29-31`），与 `.project/governance/module-dependencies.json`
  的 `runtimeEdges: []` 不符。
- **7 道核心门从未在 CI 执行**（两个 workflow 里 grep 命中均为 0），而 CI 里真正跑的只读检查只是
  "源码里出现 `raise` 字样"（`scripts/ci/verify_observer_readonly.py:23-32`）。
- `start-observer.cmd` 三重矛盾 → 一键入口目前不可能连通。
- 报告里每条标了 ✅（我逐行复核）/ ◐（子审计报的、我没复核）——**据此改代码前先复读那几行**。

### 1.4 顺带修掉的真缺陷

文档化启动方式 `python services/orchestration/sidecar.py …` 在干净 shell 里
`ModuleNotFoundError: canonical_store`。根因：`tests/conftest.py` 只在 pytest 下注入模块根，
所以**每次绿灯都没走过真正发布出去的那条启动路径**。已在 `services/orchestration/sidecar.py`
按自身位置推导模块根并写明理由，新增 `tests/ci/test_sidecar_documented_launch.py`
（清空 `PYTHONPATH` 跑文档命令 + 要求 `/api/v1/snapshot` 真的应答）。

---

## 2. 最该继承的部分（**这一轮的代价几乎都在这里**）

### 2.1 新增/改动 tracked `.py` 时必踩的四道门（PR #177 四轮红的全部原因）

| # | 门 | 触发 | 正确做法 |
|---|---|---|---|
| 1 | `test_tool_inventory_coverage` | 新增 `.py` 未登记 | 先 `git add` 显式路径，再跑 `scripts/audit/tool_inventory_readback.py --out docs/audits/TOOL_INVENTORY_2026-10-07.json` |
| 2 | `test_no_text_pipe_anywhere_decodes_with_the_locale` | `subprocess` 文本管道没声明编码 | 一律 `text=True, encoding="utf-8", errors="replace"`（ERR-211：cp936 主机上子进程打印非 ASCII 会杀死 reader 线程，stream 变 None，判决被抹掉） |
| 3 | `test_the_chain_is_normalised_not_merely_resolvable` | scoped 文档里的引用是**简写** | 在 AGENTS/README/AUTHORITY/登记等 9 份文档里提到文件名，**一律写全路径**（"能解析"≠"读者能照着打开"） |
| 4 | `test_the_shipped_inventory_describes_the_tree` | **改了**已登记的 `.py` → 清单里的 sha256/字节/行数过期 | 改完任何一个已登记工具，**必须重发清单** |

第 4 条最阴：第一次是因为"新增"红的，第二次是因为"修改"红的。

### 2.2 新规矩：推之前只跑秒级 preflight（CI 上 1.4 秒）

`.github/workflows/work-lab-gate.yml` 有一个 **"Fast projection and contract-shape preflight"** 步骤，
存在的目的就是"让这类错误在几秒内以它自己的名字失败"。**推之前跑这 6 项就够**：

```bash
PY=.project-local/toolchains/wl-py311/Scripts/python.exe
$PY scripts/ci/verify_contract_catalog.py            # CONTRACT_CATALOG_PASS
$PY scripts/ci/verify_contract_ssot.py               # CONTRACT_SSOT_PASS
$PY scripts/ci/verify_gate_ci_job_mapping.py         # GATE_CI_JOB_MAPPING_PASS
$PY scripts/ci/verify_adapter_support_levels.py      # ADAPTER_SUPPORT_LEVELS_PASS
$PY scripts/ci/verify_live_doc_paths_resolve.py      # LIVE_DOC_PATHS_PASS missing=0
$PY tests/workflow-assistance/test_tool_inventory_coverage.py   # 12 passed
```

### 2.3 别在本机跑全量 governance 门

`services/orchestration/run_quality_gate.py governance` 在本机是 **2719 个测试 / 31 分钟**（CI 只要 132 秒），
而且 23 个失败里 **14 个是本机噪声**（git delivery、portable install、适配器版本戳、ledger 274 vs 276）。
**CI 才是裁判**；本机只跑 §2.2 与 §5 里点名的那几条。

### 2.4 仪器自检（第二次遇到"仪器坏"）

本机**外部读子进程 CPU 是坏的**：helper 自报 `process_time()` 0.8125s，父进程 `GetProcessTimes` 同期只看到
0.0938–0.125s 且**冻结**。若不查，探针会把每个窗口都报成"0.0%，免费"。
解法：先跑控制实验（烧已知 CPU 的子进程），读不到就判定采样器盲 → 降级同进程托管 →
报告里写明 `instrumentCheck` / `effectiveMode` / `cpuAttribution`。
（第一次是 W04 的 `session` 层。）**凡测外部世界，先测仪器。**

### 2.5 抓 CI 失败日志的正确姿势

`gh api repos/DTALEX66/WORK-LAB/actions/jobs/<id>/logs` 在这里返回**空 zip**；
要用 `gh run view --job <job_id> --log-failed`，且**必须等整个 run 结束**才拿得到。

---

## 3. 硬规矩（前 5 条继承自上一份交接，后 3 条是本轮新增）

1. **禁止 `git add -u <dir>`**。只按显式路径 `git add`。
2. **并行写者的文件只能"撤索引"，不能"改内容"**。移出自己的 PR 用 `git reset` 撤暂存；
   `git checkout origin/main -- <file>` 会覆盖工作区 = 数据丢失。
3. **投影按"将要推送的状态"算**：先暂存 → 重发 → 再提交。隔离别人的脏文件用显式路径的
   `git stash push -- <paths>`，不要 `-u`。
4. **被逐行引用的文件里插行 → 立刻跑** `scripts/ci/repoint_source_pointers.py`（drift≠0 就 `--apply`）。行号只量不猜。
5. **禁止** `git reset --hard` / `git clean` / force-push；分支必须经 PR。
6. **【新】推之前跑 §2.2 的 6 项 preflight**，别把 CI 当探测手段（一轮 6–10 分钟）。
7. **【新】改完任何已登记工具立刻重发工具清单**；在 scoped 文档里写文件名一律全路径。
8. **【新】不要为了"再确认一遍"去跑全量门**——它在本机又慢又吵；CI 红就只修它点名的那一条。

---

## 4. 环境事实（本机，别硬编码到别处）

| 事实 | 值 / 位置 |
|---|---|
| 项目解释器 | `.project-local/toolchains/wl-py311/Scripts/python.exe`（Python **3.11.15**）；CI 是 Ubuntu + 3.12.3 |
| Rust / MSVC（2026-10-18 实测，旧“本机无 Rust”作废） | `D:\All projects\OS External Configuration\toolchains\rust\cargo\bin` 的 `rustc/cargo` **1.97.1**；必须设 `RUSTUP_TOOLCHAIN=stable-x86_64-pc-windows-msvc`（该 rustup 的默认是 **GNU**，不设会去找 `dlltool.exe` 而误判“工具链缺失”）；MSVC `14.44.35207` + Windows SDK `10.0.28000.0`；`vcvars64.bat` 要用 CRLF 的 `.cmd` 调用，git-bash 的 `cmd //c 'call "…"'` 会转义引号并假 exit 0。实测 `apps/token-monitor/src-tauri`: `cargo check --locked` exit 0/43.31s，`cargo build --release --locked --features custom-protocol` exit 0/1m28s（`cargo-target/release/hermes-token-monitor.exe`，8,939,008 B） |
| 依赖锁 | `packages/client-neutral-core/requirements.lock` |
| 运行时根 | `.project-local/runs/`（临时/缓存），证据 `.project-local/artifacts/` |
| CI 时长 | `workflow-assistance` ≈2–9 min（其中 governance 批 132s）；`observer` ≈9–16 min；整轮 ≈15–20 min |
| 本机的"假失败" | 全量 governance 批在本机有 14 个 errors 属主机环境；**不要把它们当回归** |
| 工具清单 | `docs/audits/TOOL_INVENTORY_2026-10-07.json`（trackedTools=77，withLedgerPromise=19） |

---

## 5. 怎么验证（照抄即可，别自创新口径）

秒级 preflight 见 §2.2。要更完整时再加这四条（都是秒级到几十秒）：

```bash
$PY scripts/ci/repoint_source_pointers.py            # 期望 drift=0（unresolved=5 是历史遗留，不猜）
$PY scripts/ci/verify_authority_index_paths.py       # 期望 broken=0
$PY scripts/audit/normalise_doc_citations.py         # 期望 rewritten=0 blocked=0
$PY scripts/ci/verify_register_table_shape.py        # 期望 REGISTER_TABLE_SHAPE_PASS
```

另有两个快校验器直接吃登记正文，改登记后值得跑：
`scripts/audit/register_pin_reachability.py`、`scripts/ci/verify_project_authority_reference.py`。

**前端改动**必须跑：`$PY apps/observer/scripts/frontend_toolchain.py contracts`，然后重封
（`build` → `reseal_wui_evidence.py --only <十步>` → `seal_wui_evidence.py`）。

---

## 6. 绝对不能碰的东西

1. **并行写者的 4 个文件**（工作区里始终是"已修改未提交"）：
   `AGENTS.md`、`config/adapter-registry.json`、`config/client-evidence.json`、`taskpacks/current/error-ledger.json`。
   权威基准是 `.project-local/runs/writer-files-before.txt`（sha256），每次操作后 `sha256sum -c` 必须四个 OK。
2. **账本与投影的口径差**：工作区账本 **276 条**、已发布投影 **274 条**。**不要现在重发投影**——
   重发必须由"提交账本的那次改动"一并做。因此 `test_shipped_projections_are_current`
   与几个 ledger 计数门在**本机**会红，这是已知口径差，不是回归。
3. Hermes live config 的 `mcp_servers.*`、`hermes.model.*`、`sessions.*`、`memory.*`、`hooks.*`、`plugins`
   全是 **OBSERVE**；受管字段只有 `display.language` 与 `display.busy_input_mode`。
4. `.workbuddy/` 是项目数据，不是缓存，别删。本轮全部过程记录在 `.workbuddy/memory/` 目录下按日期命名的
   日志文件里（**未纳入 git 跟踪**，所以文档里不要把它当可解析路径引用——那会让权威索引门转红）。

---

## 7. 交接时的运行态（2026-10-18 23:1x，口径见括号）

| 项 | 值 |
|---|---|
| `origin/main` | `f6077d18`，两个 workflow 全绿；PR #177 是 **12/12** |
| 开放 PR / 远程分支 | 0 / 只剩 `main`（本地另留 `feat/w06-stream-cost-and-audit` @ `8f6540df`） |
| register 状态词计数 | 18 EXECUTED / 13 PARTIAL / 5 NOT_EXECUTED（`grep -oE 'EXECUTED\|PARTIAL\|NOT_EXECUTED' taskpacks/current/OPEN-TASK-REGISTER.md \| sort \| uniq -c`） |
| 账本 | 工作区 276 / 已发布 274（见 §6.2） |
| 本轮新增文件 | `scripts/audit/observer_stream_cost_probe.py`、`tests/ci/test_observer_stream_cost_probe.py`、`tests/ci/test_sidecar_documented_launch.py`、`docs/audits/FULL-AUDIT-20261018.md`、`docs/current/ui-priority-20261009/STREAM-COST-BASELINE-20261018.md` |
| 本轮新增测试 | 探针 9 例 + 文档化启动 2 例（本地均绿） |

---

## 8. 仍未完成的事（**不要当成"已收口"**）

### 8.1 需要 owner 决定（审计无权定，我**没有**自动派工）

| 项 | 卡点 |
|---|---|
| **F-01** 证据摘要自证 | 改成用调用方传入的 `expectedDigest` 与实测比；补一例不相等的测试（现有测试把它写死了） |
| **B-01** 采集器"跑了≠交付了" | 空 `records` 必须记未成功；健康判据改成"交付数 > 0 或显式声明空源" |
| **B-02/B-03** 单写者旁路 | 三个裸 `sqlite3` 写者删掉或改走 `CanonicalStore` |
| **7 道门未接 CI** | 至少把 `observer-readonly-boundary`、`canonical-single-writer`、`snapshot-schema-v3` 接进去 |
| `start-observer.cmd` 三重矛盾 | `--port 0` 却探测 61867、打开不存在的 `apps/observer/web`、`file://` 的 `Origin:null` 被拒 |
| 范围问题 | `services/session-federation`、`execution-federation`、`radar`（合计 ~6.7k 行）是否仍在范围内；"UI 优先"是否含工程量分配 |
| 上一份遗留 | **WUI-10** 写入目标、**WUI-08** 生产者语义、**FUT-020** AGPL 姿态、**FUT-010** 需 owner 账号 |

### 8.2 已裁定不可实施（**不要再试**）

- **WUI-03**（D-11 针死）、**WUI-17**（旧消费者迁移，历史文件锁死）；
- 根级 6 份历史文档**禁止删除**（WUI-17 要求保原始字节，且 `UI_IMPLEMENTATION_REPORT.md` 是
  `tests/workflow-assistance/test_path_text_is_one_predicate.py` 的载荷）。

### 8.3 可自行开工（不需要 owner）

| 项 | 说明 |
|---|---|
| **W06 剩下的半条** | 请求数与 CPU/延迟已测；**小时级长跑观测**未做。后端"按版本复用纯投影"未动。 |
| **W02 的取舍半条** | token-monitor 缓存与 `cargo check` 冗余判定未做——但 W06 已给出"这条路径上不值得做"的实测依据，可据此收口。 |
| **P1 里的门升级** | `scripts/ci/verify_observer_readonly.py` 从"字符串存在性"升级为行为检查（AST/导入面/写语句） |
| 5 条**片段引文** | 带省略号的旧引用无法机械定位（`repoint_source_pointers.py` 报 `UNRESOLVED`），需人判断 |

---

## 9. 给出下一个会话的建议起点（按性价比）

1. **先跑 §0 的四步 + §2.2 的 6 项 preflight**，确认基线与你读到的一致（1 分钟内，省掉后面所有"这不是我以为的状态"）。
2. **读 `docs/audits/FULL-AUDIT-20261018.md` 的 §5**，然后**把 §8.1 的前四项拿给 owner 裁定**——
   这四项是"能产生错误结论、且有真实路径"的，其余都可以排队。
3. 若 owner 给了口径，**从 F-01（摘要自证）开始**：它最小、最容易被假绿咬到，且已有现成测试可改。
4. 想继续做测量：W06 的小时级长跑（探针已可复跑，直接加 `--duration` 之类即可，注意退出码语义别放宽）。
5. **别去做的事**：本机跑全量 governance 门；碰 4 个写者文件；现在重发账本投影。
