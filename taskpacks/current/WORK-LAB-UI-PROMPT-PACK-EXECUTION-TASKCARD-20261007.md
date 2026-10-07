# WORK-LAB UI 提示词包执行 — TASK CARD（2026-10-07）

**Task ID:** `WORK-LAB-UI-PROMPT-PACK-EXECUTION-TASKCARD-20261007`
**Status:** ACTIVE-CURRENT（执行已授权，交付未开始）— owner 2026-10-07 指令「按照提示词任务包推进」+
「将新 UI 任务并入目标」。本卡取代 2026-09-25 卡中「只登记路线、不授权写 UI 码」的限制，但**不取代**其
跨项目边界与单写者规则。
**Authority 链:** `/WORK-LAB-AUTHORITY.md` → `taskpack-authority-index.json` →
`WORK-LAB-UNIFIED-PRODUCT-CONVERGENCE-TASKPACK-20260918` → 本卡。
**唯一在册任务行:** `taskpacks/current/OPEN-TASK-REGISTER.md` 的 `UI-PRODUCT-PROMPT-20261007`。
**工作区（隔离、单写者）:** 分支 `ui-commercial-polish-20261007` @ `.project-local/worktrees/ui-20261007`。
**交付纪律（owner 本轮明令）:** UI 代码**不提交、不推送、不开 PR、不合并**；不装全局包；
不跨项目搬运业务真值；不修改 E:/F:。

**Deferral（本卡自身的授权边界）:** this card **does not authorize** committing, pushing, opening a PR or
merging UI code, does not authorize installing any package globally, and does not authorize writing
outside this project or touching E:/F:. It carries **no execution authority of its own**: the permission
to edit UI source comes from the owner's dated instruction recorded in
`taskpacks/current/OPEN-TASK-REGISTER.md` row `UI-PRODUCT-PROMPT-20261007` (user decision > all
records), and every further side effect still needs per-operation authorization. Where this card and
the 2026-09-25 card disagree, the supersession note inside that card is the pointer.

## 1. 来源钉住（owner 材料根，只读，永不改写）

| 文件 | 大小 | sha256（前 16） | mtime (UTC) |
|---|---|---|---|
| `WORKLAB_CODEX_PROMPT.md` | 6,501 B | `31bfdba2bfc2fad9…` | 2026-10-07T00:58:35Z |
| `UI_KIT_AUDIT.md` | 10,181 B | `1eaf44826132b2f0…` | 2026-10-07T00:58:55Z |
| `UI_COMPONENT_ADOPTION_PLAN.md` | 6,397 B | `5e6b472a0d0ca5d3…` | 2026-10-07T00:59:00Z |
| `WORK-LAB_UI开发资料总包_按批次.zip` | 37,048,117 B | `c94ff634dad3fa47…` | 2026-10-07T00:54:42Z |

zip 内部结构按批次 B01…B10 + `00_壳底_PROMPT`；设计引用权重 **B10 > B09 > … > B01**（仅权重，不升级为
项目 Authority）。已抽取文本层到 `.project-local/runs/convergence-20261007-k/uipack/`
（B04/B06/B07 tokens、B08 原型、B10 终版、00 清单；图像成员只读中央目录，未膨胀）。

## 2. 基底与工作区事实（动态实测，不用历史报告）

- `origin/main = cd4daa83e107afab8438c0e85f63a10e75314d5a`，tree `a36e97ecbcb951e53a4c877e14244aa626d70fc8`；
  `ui-taskpack-e-20260930` 与之相同（0/0）。
- **并入为 no-op**：`cd4daa83` 是本分支祖先（`rev-list --count 285704a..cd4daa83 = 0`），Codex worktree
  `git status --porcelain` 为空 ⇒ 无可吸收提交；其 `Permission denied` 属该 agent 沙箱。
- **基底取 `285704a`**：`apps/observer/web` 在 main 上 24 文件、在本尖端 0 文件（重复树已退役）；
  `apps/observer/frontend` 69→83 文件。取 main 会复活已退役的重复真值树。

## 3. 目标（提示词 8 步 → 本卡的阶段门）

| 阶段 | 交付 | 门禁 |
|---|---|---|
| P1 只读基线审计 | HEAD/dirty、入口、页面、组件/tokens、API、状态合同、测试/CI、证据缺口 | 已完成（见报告 §10） |
| P2 页面—领域—API—permission/receipt—测试映射 | 逐泳道标 implemented / partial / stub / mock / unknown | 已完成（清单表） |
| P3 组件与 primitive 决策 | 单页对比 + **不装新包**结论 | 已判定：现有 20 个自研 primitive（无 Radix 依赖需求） |
| P4 tokens/AppShell/导航修正 | 用现有栈，不新主题层、不大迁移 | **token 校准不是缺口**（已撤回错判，见 §4）；余 G2 |
| P5 golden path 薄入口→合同→授权→执行→读回→Observer | 一条可重复路径贯通 | 缺值/错误态被展示为绿色者必须先归零 |
| P6 高频治理组件逐页补强 | 状态标签、权限上下文、审批差异、执行时间线、配置 diff/readback、错误恢复、审计记录 | G1 |
| P7 组件/状态图库 + 键盘/焦点/缩放/视觉回归 + 真实 Windows/Tauri 与 CI | 几何断言入门禁 | G3 |
| P8 `UI_IMPLEMENTATION_REPORT.md` | HEAD、变更、映射、组件来源/许可、真实证据、验证命令/结果、未完成、回滚 | 报告已建 §10，随阶段增补 |

## 4. 已实测的红线与撤回

- **应用 token 已是提示词方向**：`src/theme/tokens.ts` 的 `DARK` = `#050D16/#081420/#0C1B2A/#17435D/
  #EEF6FC/#8EABBC` + primary `#2A91FF` + secondary `#20CDE1`，`tokens.test.ts` 断言
  `"42 145 255" // #2A91FF`、`"32 205 225" // cyan, NOT purple`；`App.tsx:292 loadingStrip` 在首帧
  缺失时明写「数值保持 UNKNOWN，不预填任何数据」，`App.tsx:203-209` aria-live 播报 LOADING/OFFLINE。
- **撤回**：本卡接手初稿曾判「现有 tokens 蓝紫需校准」——蓝紫只存在于**应用不消费**的两件被 digest 钉住
  的档案物（`assets/brand/design-tokens.json` 全树 0 import、`work-lab-observer-symbol.svg` 渐变）。
  修改它们会撞 `test_recovered_source_registry` 漂移门禁 ⇒ 列为 **owner 决策项**，不是 UI 缺口。
- `.tsx` 中品牌 hex 字面量 **0**；唯一例外 `TopStatusBar.tsx:62` 的 `#F59E0B`（G2）。

## 5. 待办缺口（本卡的实际工作量）

- **G1** `PermissionState` 与「动作级 disabled ＋原因」：后端合同未实现的写动作必须禁用并说明；
  `OfflineState` 要么被用要么删；配 vitest，不得把缺数据渲染成绿色。
- **G2** 顶栏品牌标记（`currentColor` 内联或 tray 几何，**不碰被钉档案**）＋ 去 `#F59E0B` 字面量改走 token。
- **G3** 把 `scripts/audit/topbar_geometry_via_cdp.py`、`cdp_layout_probe.mjs` 接成**几何**门禁：
  矩形与重叠面积、`elementFromPoint` 命中测试（含覆盖层遮住自己开关的情形）、偏移实测不硬编码；
  改前先取快照以证伪自身改动。presence/class/aria 断言不得再被当作布局证据。

## 6. 完成定义（不得以代理信号替代）

Observer 写权限为零；UNKNOWN/STALE/PARTIAL/ERROR 对视觉与读屏均可区分；键盘闭环
（Ctrl/Cmd+K、Esc、焦点转移与归还）、Reduced Motion 生效；覆盖成功/无数据/加载/断网/无权限/后端未实现/
真实失败与恢复；Work Unit・审批・配置・回执均可读回真实后端；**截图、CI 绿灯、本地静态存储都不得单独作为
产品完成证明**；报告须含未完成项与回滚方式。

## 7. 回滚

未提交工作只存在于 `.project-local/worktrees/ui-20261007`：删该 worktree ＋ 删分支
`ui-commercial-polish-20261007` 即完全回滚，收敛线 `285704a…` 不受影响。
