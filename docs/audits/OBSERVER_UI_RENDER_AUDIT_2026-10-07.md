# Observer 生产界面渲染审计 — 2026-10-07

> 对象：`apps/observer/frontend/dist`（Vite 产物），由 `services/orchestration/sidecar.py
> --frontend-root` 在 `http://127.0.0.1:61911/` 只读服务；数据是真 sidecar v3 快照
> （1 个项目 work-lab、0 执行、token 全 null、transport OFFLINE/DELAYED、revision 0）。
> 方法：**无窗口的 headless Chromium 真实视口渲染**（声明根
> `10-toolchains/playwright/chromium_headless_shell-1228`），逐车道截图 + 哈希比对，
> 再用眼睛判断版式。脚本：`.project-local/runs/convergence-20261007-c/ui_render_shots.py`；
> 证据：`.project-local/artifacts/ui-audit-20261007/`（26 张 PNG + `render-inventory.json`）。

## 为什么不用 `--dump-dom`

带 `--virtual-time-budget` 的 `--dump-dom` 会**挂死**（实测 120s 超时）：应用持有 SSE 长连接，
虚拟时间等不到静默。只用 `--screenshot` 则正常渲染并退出。这条写在这里是为了下次不再试错。

## 机器判定的结论（不需要眼睛）

- 26 次渲染**全部产出可信 PNG**（最小 50 KB），`thin=[]`；
- **没有任何两条车道产出逐字节相同的 PNG**（`duplicate_renders={}`）——这抓的是"路由没真的切换"；
- 深色总览 ≠ 浅色总览 ⇒ 主题开关有效；深色总览 ≠ 紧凑总览 ⇒ 布局开关有效；
- 320 / 820 / 1440 三档 work 车道各自不同 ⇒ 视口确实参与布局。

## 用眼睛看到的（按严重度）

1. **窄屏顶栏堆叠**（320px）：汉堡、搜索、`通知/工作区/紧凑/浅色` 四个动作各占一行，
   顶栏吃掉约 40% 首屏高度。功能没坏（导航抽屉存在、按钮仍可达，
   `test_desktop_component_contract.js` 的窄屏动作簇断言守着可达性），
   但这是**商业级观感的头号短板**：≤560px 应把动作簇收进抽屉或降为图标，
   搜索框应缩略而不是截断成 `搜...`。
2. **车道标题在窄栏里折行**（320px 的"执行详情" + `0 条 · 真实投影`）：
   标题与副信息并排导致双双折行；应改为窄屏堆叠。
3. **诚实性表现良好**（这是本项目最在意的一条，逐屏核对）：
   Token KPI 显示 `UNKNOWN`、覆盖显示 `UNKNOWN` 而不是 `0/0`、
   趋势面板写"无趋势数据（UNKNOWN）"、空执行列表写
   `暂无执行记录（registry 中无 active execution）`，
   没有任何一处把缺失渲染成 0 或"正常"；`revision 0` 是真值不是伪造。
4. **禁用的 `导出状态 / 新建执行` 按钮**：外观与可用按钮一致（b10.css 无 `:disabled` 规则），
   靠 Tooltip 说明原因。已知的遗留观感债，非本次引入。
5. `无告警信号` 是绿色 chip：文字准确（确实没有告警），但在满屏 UNKNOWN 的语境里
   绿色容易被读成"系统健康"。属可选优化，不改事实。

## 未做的事（明确记录）

- 没有改 CSS：本轮只出审计结论。第 1、2 条是下一步的 UI 工单，
  动之前必须先跑 `test_desktop_component_contract.js` 与
  `test_production_surface_static_contract.js`（字号/溢出/微角色白名单都在那里）。
- 品牌 SVG 已迁入 `frontend/src/assets/brand/` 但**未挂载**到头部（现头部是文字锁扣）。
