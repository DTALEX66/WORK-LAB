# INTEGRATED-TASKPACK-20260916 · P0 收口回执（NF-00 / NF-01 / NF-02）

- 生成：2026-09-16 · 执行者：Hermes（三方治理统一后由 Hermes 执行）
- 唯一项目：`DTALEX66/WORK-LAB` · 分支 `r4-recovery-exec` · 基线 head `693471c`
- 本回执为**非敏感**交付回执；无凭据正文、无 Cookie、无浏览器库、无 E 盘访问。
- 任务卡 `TASKS.json` 为静态交接视图，本回执登记到既有权威入口，**不接管运行时账本**。

## NF-00 · 锁定真实执行基线与交接入口（P0 · 入口）

完成证据：
- 只读确认：repo=`DTALEX66/WORK-LAB`，branch=`r4-recovery-exec`，本地 head 与远端 `r4-recovery-exec` 一致于包基线 `693471c01f12956ec6e95567a164edde1a7f0879`，worktree clean；main=`e5231f0`。
- 包完整性：ZIP SHA256 `76e31e94…`（6/6 SHA256SUMS OK）；解包仅到 `.project-local/runs/integrated-taskpack-20260916/`，未安装为全局规则。
- 登记：`.project/governance/taskpack-authority-index.json` 新增本包条目，`classification=static_handoff_view`，不新建第 N 套权威台账；R1（2026-08-25）有效期至 2026-09-24，**未谎称过期**；R4 本地来源清单缺口已记录、未用私人会话库回填。
- 基线回执：`.project-local/runs/NF-00-baseline-receipt-20260916.json`（运行数据，不入 Git）。

验收点核对：唯一 repo/ref/head/作用域 ✅；旧包索引有效期内被准确处理 ✅；导出任务视图不成为任务存储/自动执行器 ✅。

## NF-01 · 统一规则语义与历史任务收口（P0 · 轻量化）

完成证据（最小差异，不动其他规则）：
- `docs/decisions/global-execution-standard.md`：
  - "全功率" 残留 → 改为「模型中性：provider/model/reasoning 跟随用户原生选择，low/medium/high 本身非故障；不设全局限速/降级/后台覆写」，消除「用户可选 low/medium/high」与「必须全功率」双生效冲突。
  - "技能强制调用（解决直接开干）" → "技能按需调用（fail-open）"；"强制执行步骤②" → "按需走步骤②（命中才加载，未命中直接执行，绝不阻塞）"，与非安全建议不阻塞语义对齐。
  - 两处死路径 `10-workflow/workflow-assistance/scripts/...`（`project_drift_check.py`、`skill_call_index.py`，全仓库 0 个 tracked 文件、磁盘仅陈旧 `__pycache__`）→ 移入历史说明并指向当前 `packages/client-neutral-core` + `services/`，不批量篡改历史。
- `packages/client-neutral-core/scripts/deploy_global_rules.py`：docstring 指向**不存在**的 `.project/governance/global-execution-standard.md`（真实权威文档在 `docs/decisions/`）→ 修正为真实路径；仅 docstring，零行为逻辑改动。
- 残留扫描：`全功率 / 强制调用 / 10-workflow 活引用` 全部清零（`10-workflow` 仅保留 2 处主动标注的"历史失效说明"）。

验收点核对：不再"用户可选档位"与"必须全功率"并存 ✅；三方循环审核/重复全仓审计要求消除 ✅；每个历史任务有处置、未知不写 CLOSED ✅；仅文档/配置权属仓内变更，全局部署留待 NF-07/NF-10 ✅。
零回归：无测试引用该文档；147 条相关测试全绿。

## NF-02 · 精确 SHA 的 CI 真相与顺序依赖测试根治（P0 · 可靠性）

**先拿同一 head/job/attempt 的原始证据**（CI run `34993528858`，job `workflow-assistance`，attempt 1，head `693471c`）：
- `gh api` 拉原始 job 日志：真实失败 = `Ran 22 tests … FAILED (errors=9)`，9 个 error **全部** `ModuleNotFoundError: No module named 'services'`，源自 `services/radar/radar_observations.py` L33 顶层 `from services.radar.radar_core import …` 及其在 `test_radar.py` 3 个新测试方法里的直接 `from services…` 导入。
- 定位机制：gate 用 `python tests/workflow-assistance/test_radar.py` **直跑**，`sys.path[0]` = 测试目录，repo 根的 `services` 包**不在 path 上**；仓库铁律（40+ 文件同约定）是 `_load()` 按文件路径 `spec_from_file_location` exec service。我 WLR-058 新增的 9 个测试方法 + 模块顶层**违反了这条约定** → 本地 pytest 从根跑（`services` 在 path）故绿，gate 独立 runner 才炸——被 deselect 掩盖的双轨差异。
- 澄清：日志里的 `sqlite3.ProgrammingError: Cannot operate on a closed database` 是 sidecar SSE 线程打的**非致命异常噪声**，非失败点（该线程在 `test_sse_handler_loop_stops_after_server_close` 关闭 handler 后打印）。
- **纠正旧定性**：本地"5 项顺序相关 flaky"（open-tasks 第 41 行）与 CI 的 9 个 error 是**不同层面**——CI 的 9 个 error 是纯 module-level 导入失败（`No module named 'services'`），不是顺序污染；本地顺序相关失败才是另一现象。两者不合并。

最小修复（3 文件，回到仓库文件路径加载约定，零功能改动）：
- `services/radar/radar_observations.py`：顶层硬导入 → `if TYPE_CHECKING:` 惰性（模块已有 `from __future__ import annotations`，`Candidate`/`SourceAdapter` 仅出现在类型标注，运行期不求值；`build_ledger`/`_candidate_to_observation` 全鸭子类型）。
- `tests/workflow-assistance/test_radar.py`：3 个新方法的 `from services…` → 复用既有 `_load("radar_core.py","rad_rc")` 按文件路径取 `rc.Candidate`/`rc.StaticSourceAdapter`/`rc.RadarCore`。
- `tests/workflow-assistance/test_price_validation.py`（同型隐患，不在 gate yml 但一并根治）：`from services.radar import price_validation` → 文件路径加载 + `sys.modules` 预注册（`@dataclass` 的 `dataclasses._is_type` 需要 `sys.modules[cls.__module__]`，未注册会在 exec 时 `AttributeError`，同 `_load` 的预注册约定）。

本地复现（与 CI 命令对齐）：
- gate 风格直跑 `python test_radar.py` + `python test_price_validation.py`：**双双 rc=0**（此前 errors=9 的 9 个方法全过）。
- 隔离 venv（`.project-local/runs/gate-venv`，装 `packages/client-neutral-core/requirements.lock`，不碰 Hermes 运行时 venv / 全局 Python）跑 gate 全序列：8 个 runner + 2 个 test 文件 = **10/10 OK**。
- 全量 `pytest tests/workflow-assistance`（隔离 venv）：**1255 passed / 8 skipped / 0 failed / 0 errors**（rc=0）。
- 全仓库 LIVE `from services` / `import services`（非 `TYPE_CHECKING` 块）导入：**0 处残留**。

验收点核对：报告能复现真实失败点 ✅（同一 head/job/attempt 原始日志）；旧补丁（WLR-058 功能）未被无依据推翻 ✅（功能全保留，仅修导入约定）；原始失败顺序 + 最小污染组合通过、后台异常不再被误当失败点 ✅；拟交付精确 SHA 所有 required job 成功 → 见"CI 回填"；生成件来源与目录边界检查一致、未为过门禁删除必要检查 ✅。
- 约束遵守：未循环盲跑全测试；未把旧通过统计当当前 SHA 通过；CI 重跑/推送遵循既有授权（用户 DTALEX66 已授 commit/push），不触碰真实账号任务。

## 剩余与阻塞
- CI 精确 SHA required-job 全绿：**待推送后由 GitHub Actions 回填**（见下）。
- NF-02 do_not「不宣布具体 CI 根因已确认」：根因已由原始日志定位，但"当前 SHA 全 required job 成功"须以推送后的真实 CI 运行为准，本地 10/10 + 1255 全绿为强等价证据。
- 外溢边界（NF-03 等 P1）、收费四臂实验（NF-13/W05/W06/W08 默认不执行）不在 P0 范围。

## 下一张可独立继续的卡
- **NF-03**（P1 · 基础设施）：项目产物边界、工具链发现与外溢定点收尾（状态 PARTIAL_REPORTED，只处理剩余范围；入口 `.project/governance/project-data-boundary.json` + `external-libraries-index.json`）。
- 随后 NF-04→NF-12（P1），WL-R01/WL-R07（P1）。

## CI 精确 SHA 回填（推送后）

- 推送 SHA：`0432b2d8cf2bd5e8b3ebac956f9d040af6ca16e5`（`693471c..0432b2d`，8 文件 +146/-33）。
- `work-lab-gate` @ `0432b2d`（run 35006305898）：**success，7/7 jobs 全绿**（gate-plan / token-monitor / observer / integration / supply-chain-security / **workflow-assistance** / aggregate）。此前自 `5b50e8b` 起连续 6 个 SHA 的 `workflow-assistance` failure（含基线 `693471c`）在 `0432b2d` 转绿。
- `wlr-060-production-gates` @ `0432b2d`（run 35006305953）：**success**。
- 结论：该 SHA 上两个 workflow 的 required job 全部成功，无 failure/missing/cancelled/skipped；NF-02 的"精确 SHA 所有 required job 成功"验收点由 GitHub 真实 CI 运行证实（非本地统计冒充）。
