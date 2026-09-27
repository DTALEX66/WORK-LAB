# WORK-LAB 前端 UI 最终落地 · 实施报告（L10b / B10 完全复刻）

> 本文件覆盖两个连续的执行：**L10（B10 收敛，已合并 PR #142）**与
> **L10b（B10 1:1 完全复刻，本分支）**。§1–§8 为 L10b 现状；§9 保留 L10 历史记录。

- L10b 分支：`p1/ui-l10-full-replica`（base `main` @ `f95baef`；父提交 `2255ddd` 皮肤层，`4da62a2` 交接）
- 执行模式：高自主串行主线（free-tier 子代理仍不可用）
- 权威顺序：**B10 单一文件 = 视觉/结构唯一事实源**；低批次仅补充细节，不推翻
- 数据源真值：sidecar v3 `SnapshotV3`（executions[] / tasks / governance.families / ci[] /
  workspace.plan / sourceRefs）；缺失一律 **UNKNOWN**，不伪造 KPI / 任务包 / 集成健康 / 审批态
- Observer §8 只读铁律：无 execute/approve/retry/apply/rollback/写 ledger
- 无鉴权铁律：零 lock / 访问令牌 / 密码 / OAuth / 鉴权入口（本地个人研究）

---

## 1. L10b 目标与达成

L10 已经把 12 页做成 B10 **风格**；L10b 把它做成 B10 **DOM 结构**：shell 与 12 页全部改
为 B10 单一文件里逐字存在的类（`.app` `.sidebar` `.nav` `.nav-dot` `.topbar` `.search`
`.content` `.page-head` `.panel` `.kpi` `.table` `.tag` `.list-item` `.graph-stage`
`.canvas` `.node` `.flow-svg` `.metric-row` `.status-stack` `.empty` `.mono` `.palette`
`.overlay` `.drawer` `.toast`），皮肤层 `src/skins/b10.css` 为 B10 `<style>` 块的逐字拷贝。

数据仍来自真实 v3 快照投影；测试锚点文案（CI 契约）逐字保留 —— **B10 赢在结构/样式，
锚点赢在文案**。

## 2. 皮肤层与 cascade 事实（先证明再改）

B10 皮肤是 **unlayered** 规则，`index.css` 的 Tailwind 位于 `@layer components/utilities`。
未分层规则优先级高于任何 `@layer`，因此 **B10 自动胜过 Tailwind**，无需 `!important`。
构建产物单文件 `dist/assets/index-*.css` 的规则偏移已回读验证
（Tailwind `.panel` 5,399 → B10 `.app` 20,303 → B10 `.canvas` 30,506 → L10b shell 38,410）。

新增 `src/skins/l10b-shell.css`（唯一非 B10 样式文件，逐条有理由）：rail 断点可见性、
compact 单列网格、`.toast-stack` 角落锚定、`.sr-only`、以及把 `.sidebar` 左右内边距从
18px 调到 16px 让 B10 品牌字标在 280px 栏内单行显示（B10 字体/字号/字距未改）。

## 3. 12 页 IA 映射（全部可达、全部 B10 DOM）

| # | 页 | registry lane | 组件 | B10 结构 |
|---|----|---------------|------|----------|
| 1 | Overview | `overview` | `OverviewView`（内联） | `.page-head` + `.kpi-grid`×4 `.panel.kpi` + `.two-col`(spark / `.metric-row`+`.status-stack`) + `.split`(`.list` / `.graph-stage` core+6 `.node-dot`) + 告警/任务包 |
| 2 | Workflows | `workflows` | `WorkflowsView` | `.toolbar`(`.input`+`.seg`) + `.panel > .table-wrap > .table` + `.empty` |
| 3 | **Workflow Editor（核心）** | `workflow-editor` | `WorkflowEditorView` + `WorkflowCanvas` | `.split`[`.panel > .canvas`(`.flow-svg` 动画虚线 + 可拖拽 `.node`) \| `.panel` 属性与运行配置 + 嵌套 部署说明] |
| 4 | Task Packs | `task-packs` | `TaskPacksView` | `.metric-row` 大数字 + `.table` 明细（真实 `snap.tasks`/`plan.tasks`） |
| 5 | Observer | `observer` | `ObserverView` + `NodeGraph` | `.split` + `.graph-stage`(核心 pulse + 6 `.node-dot`) + `.metric-row`；零可执行按钮 |
| 6 | Rules & Policy | `rules-policy` | `RulesPolicyView` | `.list-item` 家族行 + `.tag.ok/warn` 漂移真值 |
| 7 | Integrations / MCP | `integrations` | `IntegrationsView` | `.list-item` 适配器 + 7 客户端静态文档（非实时健康） |
| 8 | Memory Registry | `memory` | `MemoryView`（Views.tsx） | `.two-col` + `.list-item` 漂移真值 + 错误账本 |
| 9 | Audit Trail | `audit` | `AuditTrailView` | `.toolbar > .seg` + `.table` + `.mono` 来源引用；无重试/撤销 |
| 10 | Approval Center | `approvals` | `ApprovalsView` | `.table` 请求/风险/状态；**B10 演示的「审批」动作列刻意缺席**（只读），无批准/拒绝/撤销 |
| 11 | Settings | `settings` | `SettingsView`（Views.tsx） | `.split` + `.list-item` 数据源/版本/水位；**无令牌/无锁定/无鉴权入口** |
| 12 | Execution Detail | `execution-detail` | `ExecutionDetailView` | `.split`(执行列表 `.list-item` \| 详情 `.list-item` + 只读说明嵌套 `.panel`) |

其余可达 lane（Compact HUD 之外的 Work / Projects / Agents / Executions / Models /
Tools / Monitoring / Delivery / Trust / Software）同批迁移到 `.panel` / `.table` /
`.list-item` / `.tag`。

导航：`Sidebar` 的 7 组 `NAV_GROUPS`（首页/工作/智能体/项目/治理/集成/系统）保持
P1-01 不变式（22 lane 恰好归一组、无重复），改为 B10 `.nav button` + `.nav-dot`
（active = 渐变 + `::before` 青色→蓝色光条）。

## 4. 统一 Design System

- **原始层**：`src/skins/b10.css`（B10 `<style>` 逐字，533 行）—— `.panel` `.kpi`
  `.table` `.tag` `.list-item` `.canvas` `.node` `.flow-svg` `.graph-stage`
  `.metric-row` `.status-stack` `.empty` `.mono` `.palette` `.overlay` `.drawer`
  `.toast` `.primary-btn/.ghost-btn/.soft-btn/.danger-btn` 全部由它提供，组件只负责
  结构与数据。
- **壳层**：`src/skins/l10b-shell.css`（仅断点/角落/可见性，见 §2）。
- **组件层**：`components/ui/*`（button/card/badge/status/table/list/input/states/
  page-header/sparkline/progress/tooltip/modal/drawer/toast/command-palette/tag）
  与 `components/graph/*`（node-graph / workflow-canvas）不再自带视觉，改为挂 B10 类。
- **dashboard 层**：`KPICard`（`.panel.kpi` + `.kpi-number` 锚点）、`ExecutionTable`
  （`.panel > .table-wrap > .table`）、`ProjectPanel`/`TokenPanel`（`.list-item`）。
- **动效**：全部来自 B10 关键帧（`floatGlow` / `dashMove` / `pulse` / `scanSweep`）
  + `b10.css` 末尾的 `prefers-reduced-motion` 停机块。

## 5. 无鉴权铁律（用户 verbatim：「都是本地个人研究使用的 禁止加锁，加访问令牌等」）

全 `src/**/*.tsx` 检索 `password|passwd|api[-_ ]?key|access[-_ ]?token|Bearer|Authorization|登录|令牌|密码|鉴权`
→ **2 处命中，全部是「声明不存在」的说明文案**（`App.tsx` 工作区抽屉、`Views.tsx` 设置页）。
无锁屏、无令牌输入、无凭证弹窗、无审批理由输入、无 OAuth 门。

## 6. 诚实态 / 只读纪律

- 缺失 → `.empty` / `UnknownState` / `UNKNOWN`；不伪造 0、不伪造「全部干净」、不伪造
  任务包运行态、不伪造集成健康、不伪造已审批。
- 审批页不渲染批准/拒绝/撤销；审计页不渲染重试/撤销/重放；Observer / Execution
  Detail / Work 页零写操作控件。`ErrorState` 的 `重试` 动作已**删除**，使任何状态组件
  都无法给只读页递出重试入口。
- 真实值才显示：KPI 第 4 格绑定真实 transport 词（LIVE 契约），趋势行仅在真实存在时渲染，
  B10 演示里的 `↑ 18%` 无真实来源 ⇒ 不渲染。

## 7. 验证回读（本地真实输出）

- `tsc -p tsconfig.json --noEmit` → 干净（exit 0）
- `vitest run` → **Test Files 11 passed / Tests 72 passed**（全部 HANDOFF §3 锚点）
- `vite build` → 绿（dist JS 267.72 kB / gzip 82.46 kB；CSS 39.31 kB）
- 构建产物 cascade 偏移回读见 §2
- 像素层：17 张 headless 截图（真实渲染路径，`?api=` 指向本地 preview 服务的
  v3 形状快照），覆盖 overview/observer/workflows/editor/execution-detail/approvals/
  audit/task-packs/rules-policy/integrations/software/memory/work/settings/compact/light
- 本地测试 ≠ CI：exact-SHA 结论以 GitHub Actions 在该 SHA 的 terminal-success 为准
  （交付后回填；ERR-089 纪律）

## 8. 交付物与边界

| 文件 | 位置 | 说明 |
|------|------|------|
| `UI_IMPLEMENTATION_REPORT.md` | 仓库根 | 本文件（L10b + L10 历史） |
| `UI_REFERENCE_MANIFEST.md` | 仓库根 | 参考清单 + L10b 代码映射 |
| `ASSET_REPLACEMENT_MANIFEST.md` | 仓库根 | 资产判定（含 L10b 判定） |
| `VISUAL_QA_REPORT.md` | 仓库根 | 视觉验收（像素层本轮已 VERIFIED） |
| `.project-local/runs/ui-suite/l10b-closeout.md` | 本地（gitignored） | 完整 closeout 证据 |
| `.project-local/runs/ui-suite/l10b-verify/` | 本地（gitignored） | 验证 harness + 日志 + 17 张截图 |

已知边界（诚实分级，详见 closeout §4）：浅色主题只做到「壳层翻转 + B10 表面保持深色」
（`b10.css` 逐字编码了 B10 深色调色板，不做令牌间接化）；编辑器画布为本地编辑模型，
发布/运行在真实契约接入前保持禁用；`graph-stage` 卫星标签锚点相对 B10 演示偏移约 4px
（真实容器尺寸下会压住节点，改为贴圆外侧，B10 结构/样式不变）。

---

## 9. 历史记录：L10（B10 风格收敛，PR #142）

- 分支 `p1/ui-final-l10`（base `c8b948d`），已 squash-merge 到 `main` @ `f95baef`，CI 7/7 绿。
- 产出：12 页 IA 重组（B07 页面矩阵）+ 交互式 Workflow Editor + Observer 只读拓扑 +
  `index.css` 的 `--glow-*` / `--grid-line` token 与 B10 关键帧 + 30+ 共享组件 +
  `l10-views.test.tsx` 10 测试。
- 当时边界：像素级截图通道不可用 ⇒ VISUAL_QA 的光效/动效层标记 **UNVERIFIED**。
  **L10b 已用 headless Chromium 截图闭环该缺口**（见 §7 与 `VISUAL_QA_REPORT.md`）。
- 当时根因修复：`index.css` 注释内 `--glow-*/--grid-line` 的 `*/` 提前闭合 CSS 注释
  导致 postcss 崩溃 → 注释措辞修正。L10b 新增的 `l10b-shell.css` 已复查无同类问题。
