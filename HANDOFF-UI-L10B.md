# HANDOFF · UI L10b — B10 1:1 full style replication

> Dated handoff (2026-09-27). Frozen evidence, not a taskpack. The NEW session
> picks up the live task from the user directive quoted below.

## 0. User directive (verbatim, still active)
- 铁律约束："都是本地个人研究使用的  禁止加锁，加访问令牌等"
  → 全前端零 lock / token / password / OAuth / 鉴权入口 / 审批理由输入框。
- 任务指令："我要完全复刻UI套件里的本项目样式，不完成就不要回复我了"
  → 1:1 复刻 `D:\All projects\UI套件` B10（最终版高保真可部署UI）的全部
    12 页 DOM/视觉结构 + 统一 Design System 皮肤；数据仍来自真实 v3
    snapshot 投影（UNKNOWN 诚实纪律不变）。完成后才回复用户。

## 1. Exact repo state (verified 2026-09-27)
- Branch: `p1/ui-l10-full-replica` @ commit `2255ddd`
- Base: `main` @ `f95baef` (L10 partial B10 convergence, merged via PR #142,
  CI 7/7 green; PR closed, branch deleted)
- L10b delta on this branch so far: ONLY two files
  - `apps/observer/frontend/src/skins/b10.css` (533 lines) — B10 verbatim
    `<style>` block (1:1 from the B10 single-file), loaded AFTER index.css
  - `apps/observer/frontend/src/main.tsx` — `import './skins/b10.css'`
- Working tree clean after commit. Nothing else in flight.

## 2. B10 authoritative source (read this FIRST in the new session)
- B10 single-file: `.project-local/runs/ui-suite/work-lab_最终版_高保真可部署UI/index.html`
  (43,685 bytes / 1031 lines: head+`<style>` L1-530, body DOM L531-616,
  JS L618-1029). It is the VISUAL FACT SOURCE for every class, grid,
  radius, glow, and page structure.
  NOTE: reads of this path must go through `execute_code` (Python) —
  the project-data-boundary hook blocks absolute `D:\` paths in terminal.
- B10 DOM structure (verbatim, from L532-616):
  - `.app` grid `280px 1fr` + `.ambient` (3 glow blobs via ::before/::after)
    + `.grid-bg` (32px grid, radial mask, opacity .22)
  - `aside.sidebar` → `.brand` (`.brand-mark` 48px "WL" + `h1` WORK-LAB +
    `small` "AI WORKFLOW CONTROL PLANE") / `.nav` (11 flat buttons:
    `.nav-dot` + label; active = gradient + `::before` cyan→blue edge bar) /
    `.sidebar-footer` (`.avatar` "A" + "Alex / Personal Workspace")
  - `main.main` → `header.topbar` (78px; `.search` = ⌘K 搜索框
    `min(620px,54vw)`; `.top-actions` = `.ghost-btn` 通知/工作区) /
    `section.content#content` (padding 26px 28px 30px)
  - Global overlays: `.overlay#modal` (`.modal`) / `aside.drawer` /
    `.palette` / `.toast`
- B10 page structures (renderPageHead + per-page):
  - overview: `.page-head` + `.kpi-grid` 4× `.panel.kpi` (`strong`+`small`+
    `.trend up|warn`) + `.two-col` (`.spark` 趋势 / `.metric-row` 4×
    `.metric-box` + `.status-stack` `.tag ok|info|warn`) + `.split`
    (`.list` 最近执行 / `.graph-stage` Observer Signal Map: core pulse +
    6 `.node-dot` satellites + connector lines)
  - workflows: `.page-head` + `.toolbar` (`.input` search + `.seg` 全部/稳定/
    运行中/需关注) + `.panel > .table-wrap > .table` (5 cols + 编辑
    `.ghost-btn`)
  - editor (CORE interactive): `.split` — `.panel > .canvas` (`.flow-svg`
    animated dashed edges + draggable `.node` 150px tiles) + right
    `.panel` 属性与运行配置 (`.list-item` rows + nested 部署说明 panel)
  - approvals: `.table` 请求/风险(`.tag bad|warn`)/提交者/状态/审批
    `.primary-btn`
  - audit: `.panel > pre.mono` log lines
  - generic lanes (taskpacks/observer/policy/integrations/memory/settings):
    `.three-col` × `.panel` `.list-item` demo structure
- B10 JS behavior to mirror: Ctrl/Cmd+K palette, Esc closes all, node drag
  + localStorage persist, modal confirm flow, toast 1800ms.

## 3. What REMAINS (the actual task)
Reskin shell + 12 pages to B10 DOM classes (b10.css classes already exist
verbatim): `App.tsx` shell (`.app`/`.sidebar`/`.topbar`/`.content`/
overlays), `Sidebar.tsx` (keep NAV_GROUPS 7-group invariant + all 22 lanes
+ aria-label "侧边导航"; restyle to B10 `.nav button` + `.nav-dot` +
`.brand-mark`), `TopStatusBar.tsx` (B10 `.search` + `.top-actions` ghost
buttons; keep honest LIVE dot / coverage / revision), `CommandPalette` /
`Modal` / `Drawer` / toast → B10 `.palette` / `.overlay .modal` /
`.drawer` / `.toast`. Then every view: Overview / Workflows /
WorkflowEditor / TaskPacks / Observer / RulesPolicy / Integrations /
Memory / Audit / Approvals / Settings / ExecutionDetail — B10
`.page-head` + `.panel/.kpi/.table/.tag/.list-item/.graph-stage/.canvas/
.node/.metric-row/.status-stack/.empty/.mono` structure, data still from
the real v3 projection (UNKNOWN when absent; NEVER fabricated).

### Test anchor contract (CI gate — MUST keep passing; grep output is the
### authoritative list, files in apps/observer/frontend/src)
- App.smoke: `审计追踪` (nav), `搜索或命令…`, `Ctrl K`,
  aria-label `侧边导航`, `LIVE` ≥1, click 审计追踪 → `无审计记录`
- App.behavior: `[data-layout="compact"|"full"]`, `侧边导航` presence,
  html `.light`+colorScheme, `?api=` preserved, `.kpi-number` first 3 =
  `UNKNOWN` (no `0`), `数据源未接入` ≥1
- viewRegistry: VIEW_REGISTRY 22 entries all have components;
  NAV_GROUPS exactly 7 groups, ids partition all reachable lanes once
- l10-views: see full anchor list (workflows `daily-gate`/`legacy-route`
  filter; editor `添加 Trigger 节点`/`校验`/`属性面板`/`保存并发布`/
  `运行` disabled/`审批门` delete; observer `FRESH`/`1/1 · unit`/
  `[role="img"]` aria `观察者拓扑`, zero write buttons, no `LIVE · 只读`;
  exec-detail `EX-1`/`hermes`/`运行中`/`s3://audit/EX-1`/`无执行记录`)
- views: `技能`/`漂移`/`规则`/`当前快照未携带治理契约明细`;
  `work-lab-gate @ 00f45a10 · run 35545037452`/`EX-77 · hermes`/
  `gh.run/35545037452` ≥2/no 重试|撤销; `无审计记录`; `APPR-1`/`pending`/
  no 批准|拒绝|撤销 buttons/`审批数据未知`; `CLEAN`/`cc-switch`/
  `open-design`/`受控（无实时状态投影）`/`无集成明细`;
  `rules`/`3`/`TASK-1`/`无任务包计数`
- WorkView.behavior: `ex-1`/`运行中`/`success`/`1 条证据引用`
- truth: `数据源未接入|registry 为空`/`无软件身份投影`
- components: Modal dialog role/aria, CommandPalette filter+Enter,
  EmptyState/UnknownState titles — restyle Modal/Drawer/Palette to B10
  classes WITHOUT breaking these role/aria contracts
- If B10 wording conflicts with an anchor: keep the anchor string (they are
  the repo's CI contract); B10 wins for STRUCTURE/STYLE, not for these
  pinned texts.

## 4. Known pitfalls (from L10/L10b execution)
- CSS comment containing literal `*/` (e.g. `--glow-*/--grid-line`) closes
  the comment early → postcss build fails. b10.css is already clean.
- jsdom lacks ResizeObserver → polyfill lives in `src/test/setup.ts`.
- getByRole `name:` with regex fails TS type — use string literals.
- Duplicate text anchors (list+detail panes) → use getAllByText.
- Project-data-boundary hook: terminal = single wrapper command
  (`python "...hermes-project-data.py" --project . run -- <one command>`,
  workdir "D:\All projects\WORK-LAB"); NO shell chaining, NO `/dev/null`,
  NO absolute paths outside the Git project. Reading `D:\All projects\UI套件`
  or `.project-local` files → use execute_code/Python, not terminal.
- Free-tier sub-agents unreliable last session (3/3 interrupted) — run
  serially on the mainline.

## 5. Verification + delivery (do all, in order, before replying to user)
1. `npx tsc --noEmit` clean
2. `npx vitest run` — all 11 files / ≥72 tests green
3. `npm run build` green (from apps/observer/frontend)
4. Visual QA via `npm run preview` + browser screenshot if a channel exists;
   otherwise mark pixel layer UNVERIFIED (honest tiering, like L10)
5. NO-AUTH sweep: zero lock/token/password/API-key input in all 12 pages
6. git commit (single-line messages via `-F` file or short -m; multi-line -m
   is blocked by the boundary hook) → push `p1/ui-l10-full-replica` →
   PR to main → wait exact-SHA CI (`work-lab-gate` 7 jobs +
   `wlr-060-production-gates`) → squash-merge → delete branch
7. Update the four report files (UI_IMPLEMENTATION_REPORT /
   UI_REFERENCE_MANIFEST / ASSET_REPLACEMENT_MANIFEST / VISUAL_QA_REPORT)
   for L10b + closeout evidence under `.project-local/runs/ui-suite/`
8. Then — and only then — report to the user.

## 6. Handoff prompt (paste into the NEW session)
```
继续 UI L10b：B10 完全复刻（不完成不要回复我）。

仓库：D:\All projects\WORK-LAB，分支 p1/ui-l10-full-replica（main @ f95baef
已含 L10 收敛；L10b 增量提交 2255ddd = skins/b10.css 皮肤层 + main.tsx 接入）。

第一步读：
1) 仓库根 HANDOFF-UI-L10B.md（完整交接：现状/锚点/坑/交付清单）
2) .project-local/runs/ui-suite/work-lab_最终版_高保真可部署UI/index.html
   （B10 视觉事实源，43685 字节；读它用 execute_code/Python，终端被边界拦截）
3) apps/observer/frontend/src/skins/b10.css（已落盘的 B10 逐字皮肤层）

任务：把 shell（App/Sidebar/TopStatusBar/CommandPalette/Modal/Drawer/Toast）
+ 12 页全部改为 B10 1:1 DOM 结构（.app/.sidebar/.nav/.nav-dot/.topbar/
.search/.content/.page-head/.panel/.kpi/.table/.tag/.list-item/.graph-stage/
.canvas/.node/.flow-svg/.metric-row/.status-stack/.empty/.mono/.palette/
.overlay/.drawer/.toast），数据仍来自真实 v3 snapshot（缺失=UNKNOWN，不伪造）。
必须保住 HANDOFF 第 3 节列出的全部测试锚点（CI 契约）；B10 赢在结构/样式，
锚点文案不动。

铁律：① 都是本地个人研究使用，禁止加锁/访问令牌/鉴权入口（零 lock/token UI）
② Observer 只读（零 批准/拒绝/撤销/重试/回滚 按钮出现在只读页）
③ 深海军蓝 #050D16 + 电光蓝 #2A91FF + 青色 #20CDE1 品牌锁；禁橙/金/米白/
   浅SaaS/大面积紫/玻璃泛滥
④ terminal 一律 python "C:\Users\ALEX\AppData\Local\hermes\bin\hermes-project-data.py"
   --project . run -- <单条命令>（workdir D:\All projects\WORK-LAB），
   禁止 shell 链/重定向//dev/null/项目外绝对路径；多行 commit message 用 -F 文件
⑤ 完成后 tsc + vitest + vite build 全绿 → commit/push/PR → CI exact-SHA
   7/7 → squash merge main → 删除分支 → 更新 4 份报告 + closeout 证据 →
   才回复我（附完整证据分级）
```
