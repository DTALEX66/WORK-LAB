# WORK-LAB · UI 最终落地参考清单（L10 Execution Reference Manifest）

> 本清单是 L10 UI 工程落地执行（2026-09-27）的共享视觉事实源。所有页面/组件/代理
> 的工作必须锁定到本清单；发现与清单冲突时，按权威等级 B10 > B09 > B08 > B07 >
> B06 > B05 > B04 > B03 > B02 > B01 裁决，并把裁决记入 `UI_DECISIONS.md`。
>
> 参考资产根：`D:\All projects\UI套件`（用户授权只读源，**不得**把 zip/原图散进业务
> 源码；项目内引用走 `src/assets/generated/` 或组件/CSS token，见 §10 资产策略）。
> 解压工作区：`.project-local/runs/ui-suite/`（gitignored，非权威内容，仅审计用）。

## 1. 权威批次（WORK-LAB 相关条目，SHA 见 .project-local/runs/ui-suite/extraction-report.json）

| 批次 | 文件 | 类型 | 权威角色 | 是否最终权威 |
|---|---|---|---|---|
| B10 | 10_B10_.../work-lab_最终版_高保真可部署UI.zip | 可部署静态 UI（index.html 43KB） | 视觉/光效/动效/交互 最高权威 | ✅ 是 |
| B09 | 09_B09_.../work-lab_L9_交互式真实Demo.zip | 交互 Demo（interactive-demo.html） | 真实交互行为参考 | ✅ 是 |
| B08 | 08_B08_.../work-lab_L8_React_TypeScript_可运行原型.zip | React/TS 原型 + ui-core 包 | 工程结构与组件 API 参考 | ✅ 是 |
| B07 | 07_B07_.../WORK-LAB_L7_前端开发规范工程包.zip | 路由/权限/状态机/组件契约 | 前端治理规范 | ✅ 是 |
| B06 | 06_B06_.../WORK-LAB_L6_18张交互状态+Tokens.zip | 交互状态图 18 张 + interaction_tokens.json | 状态/响应式规范 | ✅ 是 |
| B05 | 05_B05_.../WORK-LAB_L5_12张高保真产品页面.zip | 12 张 1920×1080 产品页面 | 页面 IA 与内容模块 | ✅ 是 |
| B04 | 04_B04_.../WORK-LAB_L4_组件系统_16张+Tokens.zip | 组件系统 16 张 + design_tokens.json | 组件/token 规范 | ✅ 是 |
| B03 | 03_B03_.../WORK-LAB_10张页面级UI_统一体系.zip | 10 张页面级母版 | 页面母版关系 | 参考 |
| B02 | 02_B02_.../WORK-LAB_L2_VI+UI_36张细节图.zip | Logo 构造/图标/细节 | VI 细节 | 参考 |
| B01 | 01_B01_.../WORK-LAB_VI+UI_24张全套.zip | 品牌基础图 | 品牌/Logo | 参考 |

## 2. 视觉锁死（B10 + L4 tokens.json + L7 tokens.json，三方一致，已 CI 断言于 tokens.test.ts）

- 深黑 `#050D16` · 深海军 sidebar `#07111C` · surface `#081420` · surface2 `#0C1B2A`
- 边框 `#17435D` · 文本 `#EEF6FC` · 弱化 `#8EABBC`
- 主交互 Electric Blue `#2A91FF` · 信号/连线 Cyan `#20CDE1`（**只用于信号与辅助高亮**）
- 状态色：success `#22C55E` / warning `#F59E0B` / error `#EF4444` / info `#3882F6`
- 半径 4/10/16/22 · 阴影 `0 20px 80px rgba(0,0,0,.35)` · 玻璃模糊 18px
- 动效：hover 120ms / base 180ms / modal 220ms / drawer 280ms / emphasis 420ms / pressed 80ms
- 密度：comfortable 68 / default 56 / compact 44
- **禁止**：橙色/金色/米白主色、浅色企业 SaaS、大面积紫、玻璃泛滥、霓虹夜店。
  光效 = 系统状态语言（节点发光、活动 pulse、选中 glow、hover 边缘高亮），非装饰。

## 3. 产品信息架构（B07 routes.json + B10 导航，12 路由）

| 路由 | 页 | 页面组件（本仓落位） | 数据真值（v3 snapshot 投影） |
|---|---|---|---|
| `/` | 总览 Overview | `OverviewView`（App 内联 overview 重写） | KPI(执行态统计)/最近执行/Observer 信号图/系统状态/告警/最近任务包 |
| `/workflows` | 工作流 | `WorkflowsView`（新 `views/WorkflowsView.tsx`） | 搜索/筛选/状态/负责人/版本/最后执行 |
| `/workflows/:id/edit` | 工作流编辑器 | `WorkflowEditorView`（新 `views/WorkflowEditorView.tsx` + `components/graph/`） | 节点画布(Trigger/Validate/Agent/Tool/Approval/Condition/Deploy/Output) 缩放/平移/拖动/选择/连线/删除/属性/保存/发布/运行 |
| `/task-packs` | 任务包 | `TaskPacksView`（重写） | 真实 tasks 计数 + plan.tasks 明细 |
| `/observer` | 观察者 | `ObserverView`（新 `views/ObserverView.tsx`，替换旧 graph 位） | 拓扑(Agent/Workflow/Tool/MCP/Memory/TaskPack/异常) + 指标 + 趋势 + **严格只读**（§8） |
| `/policies` | 规则与策略 | `RulesPolicyView`（重写） | governance.families 真值 |
| `/integrations` | 集成 / MCP | `IntegrationsView`（重写） | adapters 族 + 7 客户端 registry（文档位，非实时健康） |
| `/memory` | 记忆管理 | `MemoryView`（重写，views/MemoryRegistryView.tsx 合并） | governance memory 族 + workspace.history |
| `/audit` | 审计追踪 | `AuditTrailView`（重写） | CI runs + executions + sourceRefs，只读可筛选 |
| `/approvals` | 审批中心 | `ApprovalsView`（重写） | workspace.plan.approvals；**无真实审批契约 ⇒ 缺字段显式 UNKNOWN，不伪造可操作按钮** |
| `/settings` | 系统设置 | `SettingsView`（重写） | 数据源 descriptor/传输真值/版本 |
| `/executions/:id` | 执行详情 | `ExecutionDetailView`（新） | 单执行真值 + 项目/token/git 关联 |

侧边栏 280px（可折叠 72px；移动端 Sheet）、顶部 78px（全局搜索/Ctrl+K 面板/状态/通知/账户区）、
面包屑、搜索、状态栏、用户区与 B10 结构一致。

## 4. UI Core（统一组件层，禁止页面内大量 hardcode）

- 布局：`AppShell` `Sidebar` `TopBar` `Breadcrumb` `PageHeader` `ResponsiveGrid` `SplitPane`
- 输入：`Button` `IconButton` `Input` `Select` `Tabs` `Search`
- 数据：`Card` `KPI` `Table` `Tree` `List` `Timeline` `Graph` `Badge` `Status` `Progress`
- 反馈：`Modal` `Drawer` `Tooltip` `Popover` `ContextMenu` `Toast` `Alert` `Empty` `Loading` `Error`
- 治理：`Permission` `Approval` `VersionCompare`
- 命令：`CommandPalette`（已存在，保持契约）
- 新增落位：`src/components/ui/`（基础）与 `src/components/graph/`（NodeGraph/Timeline，B10 光效版）。

## 5. 光效（B10 关键帧 1:1，落 CSS 变量 + 类，不逐页写）

- 环境光：微弱蓝色 ambient（`--glow-ambient` 40% primary blur）+ 32px 网格底纹（`.grid-bg`）
- 面板：hover 边框 primary 44% + `--glow-card`（0 18px 44px rgba(0,0,0,.22)）
- 节点/连线：`--glow-node` drop-shadow primary 40%；连线虚线 `dashMove` 3.6s linear 无限流
- 活动核心：`pulse` 3s ease-in-out（scale 1→1.05, opacity 1→.86）
- KPI 大数字：`text-shadow: 0 0 24px primary/32%`（`.big-number`）
- 扫描线（观测面板）：`scanSweep` 2.4s
- 全部动效尊重 `prefers-reduced-motion`（已有 `@media` 降级块，新动效必须并入）

## 6. 真值纪律（WORK-LAB Observer §8 只读铁律 + 前端 UNKNOWN 纪律）

- Observer = 只读投影：无 execute/approve/retry/apply/rollback/state-write/telemetry-ledger-write。
- 快照缺字段 ⇒ 显式 `UNKNOWN` / EmptyState，**禁止** 伪造 0、假 LIVE、假健康度、假 KPI。
- 审批中心：真实 `workspace.plan.approvals` 有数据才渲染行；无数据渲染 UnknownState +
  说明"审批契约未接入"，不提供可操作的批准/拒绝按钮（B10 的按钮形态仅作视觉参考，
  实际按钮在契约接入前是禁用态 + tooltip 说明，或整页 UnknownState）。
- Workflow Editor：节点/连线/属性为本地编辑模型（localStorage 或组件 state），
  "发布/运行" 动作在真实 workflow schema 契约接入前渲染为禁用 + 说明，不伪造成功。

## 7. 资产策略（B10 直接可用 ⇒ 直接使用；不可提取 ⇒ 1:1 重生成并登记）

- 品牌 Logo：优先使用 B02 `VI/03_03_主标志_Primary_Logo.png` 语义（几何构造）；
  本仓现有 "WL" 字标（B10 brand-mark 48px 渐变圆角方 + WL 900）已是 B10 最终形态 ⇒ 直接保留，
  不重设计 Logo。
- 背景纹理/网格：B10 纯 CSS（`.grid-bg` + ambient）直接复刻，无需位图。
- 页面级参考图（L5 12 张 / L3 10 张）：**仅审计对照用**，不作为运行时位图进 src/assets
  （避免 230MB 参考资产进仓库）。运行时视觉全部来自 CSS token + 组件。
- 若后续需真实位图（如 hero/星球/控制平面壁纸）：重生成放 `src/assets/generated/`，
  并在 `ASSET_REPLACEMENT_MANIFEST.md` 登记（原参考/为何不能直接用/新位置/用途/尺寸/差异）。

## 8. 代码映射（参考 → 本仓实现）

| 参考位 | 当前实现位 | 差距 |
|---|---|---|
| B10 AppShell/Sidebar/Topbar | `components/layout/{Sidebar,TopStatusBar}` + `App.tsx` | Sidebar 260px 无 B10 active 光条/组头；TopBar 56px 无 B10 78px 搜索栏形态 |
| B10 Overview | `App.tsx` 内联 overview（KPI+表+面板） | 无趋势图/Observer 信号图/告警/系统状态卡（B05 01 页） |
| B10 Editor | 无 | 新增 `WorkflowEditorView` + `components/graph/`（B10 拖拽/连线/光效） |
| B05 12 页 | `views/*.tsx`（治理 5 视图 + Work + 旧 Views） | IA 重组为 B07 路由矩阵；缺 workflows/editor/observer/execution-detail |
| L4 组件系统 | `components/ui/*`（button/input/card/badge/modal/drawer/toast/command-palette/states/tag） | 缺 Table/Tree/Timeline/Graph/Tooltip/Popover/ContextMenu/Status/Progress |
| L6 交互 token | `index.css` 已有 modal/drawer/toast/pulse 关键帧 + reduced-motion | 并入 B10 dashMove/scanSweep/节点 glow |
| L7 路由/权限/状态机 | `lib/viewRegistry.ts`（lane 制，无路由库） | 保持 lane 制（仓内无 router 依赖；B10 也是 hash 路由），NAV_GROUPS 按 B07 重组 |

## 9. 验收（对齐 prompt §16 + B07 acceptance-checklist）

build / typecheck / vitest 全绿；12 路由全部可达；Editor 可交互（缩放/平移/拖/选/连/删/属性）；
Observer 可展示真实拓扑且只读；Approval/Audit 完整且真值诚实；统一 token（无散落品牌色）；
光效/动效/状态/响应式/可访问性（焦点环、44px 命中、对比度、reduced-motion）完成；
产出 `UI_IMPLEMENTATION_REPORT.md` / `ASSET_REPLACEMENT_MANIFEST.md` / `VISUAL_QA_REPORT.md`。
