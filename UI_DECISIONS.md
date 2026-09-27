# UI_DECISIONS — L10 冲突裁决记录

> 权威等级（`00_批次顺序_文件映射_权威规则.md`）：B10 > B09 > B08 > B07 > B06 >
> B05 > B04 > B03 > B02 > B01。低批次只补细节，不推翻高批次已定事实。
> 本文件记录 L10 执行（2026-09-27）中出现的冲突与裁决。

## D-01 · 路由形态：B07 路径路由 vs 仓内 lane 制
- **冲突**：B07 route-matrix 给的是 `/workflows`、`/workflows/:id/edit` 等路径路由；
  仓内现状是 `?view=` lane 深链 + `viewRegistry`（仓内无 react-router 依赖，Tauri
  桌面壳注入 `?view=`/`?api=` 参数，已有契约测试锁定）。
- **裁决**：保持 lane 制（B10 自身也是 `location.hash` 路由，非路径路由；仓内 Tauri
  契约优先）。B07 的 12 路由语义映射为 12 个 lane（见 UI_REFERENCE_MANIFEST §3 代码
  映射表），页面 IA 与 B07 一致；不引入 router 依赖（工程铁律：不为视觉重构破坏
  现有壳层契约）。

## D-02 · 侧边栏宽度 280 vs 260
- **冲突**：B10 `.app` 网格 `grid-template-columns:280px 1fr`；L7 component-overrides
  写 `Sidebar width 260`；B07 AppShell 示例未给宽度。
- **裁决**：**B10 赢（280px）**——B10 是最高视觉权威；L7 属 B07（低于 B10）。
  折叠宽保持 L7 的 72px（L7 唯一明确的折叠值，B10 未定义折叠态）。

## D-03 · TopBar 高度 78 vs 72
- **冲突**：B10 `.topbar{height:78px}`；L7 `Topbar height 72`。
- **裁决**：**B10 赢（78px）**。搜索栏形态 1:1 B10（`min(620px,54vw)`、14px 圆角、
  inset 高光）；状态真值（LIVE/传输/新鲜度/revision）保留仓内真实投影，不取 B10
  demo 的假数值。

## D-04 · 圆角：L4 radius lg=16 vs B10 面板 18px
- **冲突**：L4 design_tokens `radius: sm4/md10/lg16/xl22`；B10 `.panel{border-radius:18px}`
  、`.node{16px}`、`.modal{22px}`。
- **裁决**：**token 层保留 L4 值（4/10/16/22，CI 断言于 tokens.test.ts）**；B10 18px
  面板圆角通过 B10 面板视觉类的局部 radius 表达（`.wl-*` 类内联），不改全局 token——
  两者都是权威，不动被 CI 锁定的单一真值源。

## D-05 · 总览 KPI 数值：B10 demo 数字 vs 仓内真值纪律
- **冲突**：B10 `kpiCard("12","运行中工作流")` 等是演示数据；仓内铁律（U07/B5）
  "UNKNOWN ≠ 0，不伪造 KPI"。
- **裁决**：**布局 1:1 B10（4 列 KPI 卡 + count-up 大数字 + glow），数值全部来自
  v3 snapshot 真实投影；无数据 ⇒ UNKNOWN。** B10 数字只作视觉参照，不进运行时。

## D-06 · 审批/运行按钮：B10 可操作形态 vs Observer §8 只读铁律
- **冲突**：B10 审批中心有可点 `approveBtn`、编辑器有"保存并发布/运行"；
  AGENTS.md §8 只读铁律 + views.test.tsx 断言"无 批准/拒绝/撤销 按钮"。
- **裁决**：**页面结构与视觉 1:1 B10（风险 pill/上下文/审计记录行）；交互语义服从
  只读铁律**——无真实审批契约时整页渲染 UnknownState + 契约缺口说明；编辑器
  "发布/运行" 按钮渲染但 disabled + tooltip 说明"真实 workflow 执行契约未接入"，
  画布拖拽/连线/缩放为本地编辑模型（B10 localStorage 同款行为，允许）。

## D-07 · 趋势图数据源：B10 sparkline 序列 vs 无真实序列
- **冲突**：B10 `sparkline([18,26,...])` 为硬编码；v3 snapshot 不携带执行趋势序列。
- **裁决**：趋势图 1:1 B10 组件形态（渐变 stroke SVG），**数据缺失 ⇒ 空图占位 +
  "无趋势数据（UNKNOWN）"**，不用 B10 假序列冒充真值（Sparkline 组件已按此实现）。

## D-08 · 光效强度：B10 ambient blur 80px vs §八"禁止玻璃效果泛滥"
- **冲突**：B10 `.ambient` blur(80px) + `.sidebar backdrop-filter:blur(18px)`。
- **裁决**：**B10 赢**——§八 禁止的是"泛滥/霓虹/全页发光"，B10 的 3 团微弱环境光
  （opacity .45、blur 80px、12s 缓浮）正是"微弱蓝色环境光"的要求值，1:1 保留；
  不做全页发光、不加 extra neon。

## D-09 · Overview 与 Work lane（D3 已验收）
- **裁决**：总览按 B10 重构（KPI/趋势/Observer Map/系统状态/告警/最近执行）；
  D3 的 `work` lane 及其 B5 文案（"数据源未接入"等）原样保留，不并入总览——
  两 lane 并存，Nav 分组归位（主线接线决定）。

## D-10 · 资产策略（详见 ASSET_REPLACEMENT_MANIFEST.md）
- **裁决**：Logo 保留 B10 "WL" 渐变字标（不重设计）；网格/环境光/节点光效纯 CSS
  1:1 复刻；1920×1080 参考图仅 QA 对照，不进运行时；本轮**零新增位图资产**。
