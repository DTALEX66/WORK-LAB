# 交接提示词 · 2026-10-18 阶段（main `fae41c4d`）

> **这是给下一个会话的提示词，不是权威。** 权威顺序仍是
> `WORK-LAB-AUTHORITY.md` → `.project/governance/project-authority-index.json` → 唯一 CURRENT 任务包 →
> `taskpacks/current/OPEN-TASK-REGISTER.md`。本文所有数字都注明了测量命令与口径；**未测的写"未测"**。
> 本文与机器的冲突，以机器为准，并把本文当缺陷改掉。

---

## 0. 先做这四步（不要跳过，也不要先读历史）

```bash
git fetch origin && git log --oneline -1 origin/main           # 期望 fae41c4d 之后的提交
gh run list --branch main --limit 3                            # 期望两个 workflow 都是 success
.project-local/toolchains/wl-py311/Scripts/python.exe -V       # 期望 Python 3.11.15
git status --short                                             # 期望只有并行写者的 4 个文件（见 §6）
```

然后按 `AGENTS.md` 的 8 步权威引导链读：`WORK-LAB-AUTHORITY.md` → 机器权威索引 → `AGENTS.md` → CURRENT 任务包
→ 唯一 open register → 相关机器合同。**别先通读历史资料**（`docs/history/**` 是冻结证据，只按需点名查）。

---

## 1. 这个阶段做了什么（一句话版）

把「有生产阻断、有红门、有脏投影、有 1.9 GB 运行时堆料」的状态，推进到**全绿、账本诚实、体积减半**，
并为四类**反复出现的失败**各加了一道机器门。

### 1.1 W 计划（方案 W01–W12）：12 条全部落地

| 条目 | 落地物 | 证据 |
|---|---|---|
| W01 去重重运行 | push 仅 main，分支由 PR 覆盖 | PR #164 |
| W02 分段计时 + 真缓存 | 前端四步 + Rust/npm 缓存 | PR #164，运行日志可见 |
| W03 投影提前失败 | contracts shape 检查提到 2712 例批之前 | PR #164 |
| W04 桌面验收分层 | `scripts/audit/desktop_capability_probe.py`（六层，不启动产品） | PR #173；本机六层全 PASS |
| W05 快照读截止 | 8s 硬截止 + 真 abort（卸载时） | PR #164 |
| W06 轮询安全网 | 流健康时不读只查陈旧度（45s），同签名不重渲染 | PR #174；3 例测试 |
| W07 未分类路径具名 | plan 输出 `unclassified_paths{path,reason,needs}` | PR #166 |
| W07 后半 gate↔CI job | profile 每 gate 带 `ci_job` + 双向不变量验证器 | PR #171；当场抓到 `wlr060-aggregate` 无人认领 |
| W08 context pack 预算 | 必需段永不切、可丢段整段具名、双 digest | PR #165；4 例测试（含二分定位档位边界） |
| W09 能力不超证据 | `verify_adapter_support_levels.py` 4 条规则 | PR #172；7 例测试（6 例伪证） |
| W10 可追溯小结果文件 | `ci_summary` + upload-artifact（钉 SHA），**缺输入永不渲染成通过** | PR #169/#170；本仓首批 artifact |
| W11 调用链记录 | `gate-stages.json`（阶段/退出/秒/成员/失败测试 ID） | PR #169 |
| W12 索引忽略范围 | 资料索引声明历史/大产物默认不进查询 | PR #167 |

**W10/W11 当天投入、当天回收**：本阶段后面三次 CI 红，全部先用 `ci-summary-<job>.json` 与
`gate-stages.json` 定位（一次给出失败阶段+退出码+耗时+成员数+失败测试名+点名的那一行），**没有再去 grep 日志**。

### 1.2 UI 任务线（register 25 行）

`15 EXECUTED / 9 PARTIAL / 1 NOT_EXECUTED`（测量：
`grep '^| WUI-' taskpacks/current/OPEN-TASK-REGISTER.md | wc -l` 与逐行状态列）。

其中本阶段解决了**唯一的生产阻断项**：HUD 在 200% 显示缩放下越界（780→680，12 处镜像）。
9 个 PARTIAL 的卡点分类见 §3。

### 1.3 CI 与仓库卫生

- **四次同类 CI 红的根因**（`path:LINE` 指针腐坏）已根治，见 §2。
- 体积：`.project-local` **1952 MB → 1048 MB**；仓库总计 ~1836 MB。
- 分支：本地与远端只剩 `main`；开放 PR 0。

---

## 2. 四类反复失败的机制与本阶段的解毒（**最该继承的部分**）

| 反复出现的形态 | 机制 | 现在的解毒 |
|---|---|---|
| 改了 schema 没重生成投影 | 生成器与提交态分离 | 门 `test_ci_invoked_verifiers_have_a_local_route` / `test_shipped_projections_are_current` 会红；**规矩：同一次改动内重生成** |
| 行了号指针腐坏 | 引用面（603 条）远大于校验面（51 个目标） | `repoint_source_pointers.py`（按引用的代码重推导，`--apply`）+ 门 `test_source_pointers_are_current` |
| 活文档引用已删除的路径 | 同上 | `verify_live_doc_paths_resolve.py`（历史根冻结、例外须带理由+日期、**例外过期也算失败**） |
| 工具清单被改动带旧 | 清单按 `git-index` 计摘要 | **先 `git add` 再重发**（`tool_inventory_readback.py`），否则记录的是 HEAD 的旧字节 |

### 2.1 五条硬规矩（违反过、代价明确）

1. **禁止 `git add -u <dir>`**。它会把并行写者已改的文件扫进你的索引（本阶段踩了三次）。只按显式路径 `git add`。
2. **并行写者的文件只能"撤索引"，不能"改内容"**。移出自己的 PR 用 `git reset` 撤暂存；
   `git checkout origin/main -- <file>` 会**覆盖工作区**，那是数据丢失（本阶段踩过一次，靠 `git fsck` 找回）。
3. **投影按"将要推送的状态"算**：先暂存→重发→再提交。要隔离别人的脏文件，用**显式路径**的 `git stash push -- <paths>`，
   不要 `-u`（`-u` 会把整棵树 capture 进去，弹出时冲突会传播成 `<<<<<<<` 标记）。
4. **被逐行引用的文件里插行 → 立刻跑指针门**：`python scripts/ci/repoint_source_pointers.py`
   （drift≠0 就读它的提示跑 `--apply`）。行号**只量不猜**。
5. **环境噪声用证据分辨，不靠手动复跑到绿**。几何门的冷启动已把等待提到 90s 并把日志尾带进失败原因。

---

## 3. 仍未完成的事（**不要当成"已收口"**）

### 3.1 需要 owner 决定（我无权替你定）

| 项 | 卡点 |
|---|---|
| **WUI-10** 隔离试用的写入面 | 需要 owner 指定"授权写入目标" |
| **WUI-08** 四步生产者语义 | 需要 owner 定语义归属（源评价→目标→差异→试用→验证→部署） |
| **FUT-020**（候选注册表） | AGPL-3.0 许可姿态势必 owner 决定 |
| **FUT-010** | 需要 owner 的 ChatGPT 账号与官方路径 |

### 3.2 已裁定不可实施（**不要再试**）

- **WUI-03**（D-11 针死）、**WUI-17**（旧消费者迁移，历史文件锁死）；
- 根级 6 份历史文档**禁止删除**：WUI-17 要求保原始字节，且 `UI_IMPLEMENTATION_REPORT.md` 是
  `tests/workflow-assistance/test_path_text_is_one_predicate.py` 的**载荷**（大写反例）。

### 3.3 可自行开工（不需要 owner）

| 项 | 说明 |
|---|---|
| **W06 的测量半条** | 请求数已由测试断言；**CPU 与端到端数据延迟未测**（需长跑观测）。后端"按版本复用纯投影"未动。 |
| **W04 的 runner 读数** | 探针已接线在 U19 之前并进 artifact；**CI runner 上的读数尚未采集**（下次 CI 跑完看 `desktop_capability.json`）。 |
| **W02 的取舍半条** | token-monitor 缓存与 `cargo check` 冗余判定未做（需实测取舍）。 |
| 5 条**片段引文** | 带省略号的旧引用无法机械定位，需人判断（`repoint_source_pointers.py` 报 `UNRESOLVED`）。 |
| `AGENTS.md` 的 Hermes exe 路径 | 在并行写者手里；已登记为带理由的例外，改完删例外。 |

---

## 4. 环境事实（本机，别硬编码到别处）

| 事实 | 值 / 位置 |
|---|---|
| 项目解释器 | `.project-local/toolchains/wl-py311/Scripts/python.exe`（Python **3.11.15**） |
| 前端工具链 | `apps/observer/scripts/frontend_toolchain.py`，Node 由它自带探测（实测 v22.11.0） |
| Python 依赖锁 | `packages/client-neutral-core/requirements.lock`（`torch==2.6.0`，CPU 副本） |
| 运行时根 | `.project-local/runs/`（临时/缓存），证据 `.project-local/artifacts/` |
| CI 时长 | `workflow-assistance` ≈2–9 min；`observer` ≈9–16 min；一次完整 run ≈15–20 min |
| CI 已知不稳定点 | 几何门曾因 runner 冷启动 Chrome 未在 25s 内公告而红；**已提到 90s 并带日志尾**。若仍红且日志尾显示 Chrome 未起，是环境不是产品。 |

---

## 5. 怎么验证（照抄即可，别自创新口径）

```bash
PY=.project-local/toolchains/wl-py311/Scripts/python.exe
$PY scripts/ci/verify_live_doc_paths_resolve.py          # 期望 LIVE_DOC_PATHS_PASS missing=0
$PY scripts/ci/repoint_source_pointers.py                # 期望 drift=0
$PY scripts/ci/verify_gate_ci_job_mapping.py             # 期望 GATE_CI_JOB_MAPPING_PASS
$PY scripts/ci/verify_adapter_support_levels.py          # 期望 ADAPTER_SUPPORT_LEVELS_PASS
$PY scripts/ci/verify_root_document_dispositions.py      # 期望 ROOT_DISPOSITIONS_PASS
$PY scripts/ci/verify_authority_index_paths.py           # 期望 broken=0
$PY scripts/audit/normalise_doc_citations.py             # 期望 rewritten=0 blocked=0
$PY scripts/ci/verify_supply_chain.py                    # 期望 SUPPLY_CHAIN_PASS（新增 action 必须钉 40 位 SHA）
$PY services/orchestration/run_quality_gate.py root-governance-suite   # 期望 QUALITY_GATE_PASS
```

**前端改动**必须跑：`$PY apps/observer/scripts/frontend_toolchain.py contracts`，然后**重封**：
`build` → `reseal_wui_evidence.py --only <十步>` → `seal_wui_evidence.py`（本阶段用的是
`slice-capture / geometry / legibility-* ×4 / display-scaling / sse-revision / sse-falsification / seal`）。

---

## 6. 绝对不能碰的东西

1. **并行写者的 4 个文件**（工作区里始终是"已修改未提交"）：
   `AGENTS.md`、`config/adapter-registry.json`、`config/client-evidence.json`、`taskpacks/current/error-ledger.json`。
   它们的**权威基准**是 `.project-local/runs/writer-files-before.txt`（sha256），每次操作后跑一次
   `sha256sum -c` 必须四个 OK。
2. **账本与投影的口径差**：工作区账本是 **276 条**（240 PASS / 27 PARTIAL / 7 FAIL / 1 UNVERIFIED / 1 BLOCKED），
   已发布投影是 **274 条**。**不要现在重发投影**——那会把不属于你这次推送的状态写进去。
   重发必须由"提交账本的那次改动"一并做。
3. Hermes live config 的 `mcp_servers.*`、`hermes.model.*`、`sessions.*`、`memory.*`、`hooks.*`、`plugins`
   全是 **OBSERVE**；受管字段只有 `display.language` 与 `display.busy_input_mode`。
4. **禁止** `git reset --hard` / `git clean` / `force-push`。分支必须经 PR；`strict` 要求分支与 main 同步。
5. `.workbuddy/` 是项目数据，不是缓存，别删。

---

## 7. 交接时的运行态（2026-10-18 18:2x，测量口径见括号）

| 项 | 值 |
|---|---|
| main | `fae41c4d`（`git log --oneline -1`）；`wlr-060-production-gates` success |
| 开放 PR / 分支 | 0 / 仅 `main`（本地与远端） |
| register | 25 行：15 EXECUTED / 9 PARTIAL / 1 NOT_EXECUTED |
| 账本 | 工作区 276 / 已发布 274（见 §6.2） |
| 体积 | `.project-local` **1048 MB**（toolchains 28 + artifacts 365 + imported 453 + runs ~157 + quarantine 22） |
| 新增门 | 6 个（2 个指针/路径类 + gate↔job + 能力证据 + 桌面能力探针 + ci_summary） |
| 新增测试 | 源指针 3 例、活文档路径 4 例、gate↔job 5 例、能力证据 7 例、桌面探针 7 例、ci_summary 6 例 |

---

## 8. 给出下一个会话的建议起点（按性价比）

1. **先跑 §5 的九条命令**，确认基线与你读到的一致（30 秒，省掉后面所有"这不是我以为的状态"）。
2. **等一次 CI 完成**，下载 `ci-summary-observer.json` 里的 `desktop_capability.json` —— 那是 W04 唯一还缺的读数，
   同时验证 W10 的 artifact 通路在合并后仍然可用。
3. 若 owner 给了 WUI-10 的写入目标，按 `docs/current/ui-priority-20261009/UI-V2-INTAKE-20261010.md` 的三条约束开工。
4. 想继续缩体积：`.project-local/imported-from-workbuddy-20261006`（453 MB）是**唯一副本**（源已不存在），
   动它之前先问 owner；`runs/tmp` 会持续增长（测试套件有 305 处 `TemporaryDirectory` 债务）。
