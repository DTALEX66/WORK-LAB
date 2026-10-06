# U03 — Static-web → React Parity Matrix

> Taskpack U03 (P0): "Create static-web → React parity matrix, migrate valid
> capability, then retire static web as production." This document is the
> required parity matrix. It is evidence-based (call-site scans of the running
> static surface vs. the React UI), not a claim.

## Decision scope

The retired static surface lives at `apps/observer/web/` (9 scripts, 5 styles,
6 node contract suites). The React production UI lives at
`apps/observer/frontend/` (Tauri ships `frontend/dist` via `frontendDist:
"../frontend/dist"`; the live browser read-only entry opens `web/index.html`
with `?api=` pointed at the sidecar). `observer_live_server.py` is a **retired
fail-closed stub** (exit 2, by design) — the real static-serving path is
`services/orchestration/sidecar.py`.

Deletion of `web/` is **not** this step. Per the iron law "no deletion before
parity" and the release iron law (no claim without a real WebView artifact),
`web/` retirement is gated on **U19** (Windows Tauri E2E) and the exact-SHA
release. U03 here = **parity matrix + migrate valid capability only**.

## Capability-by-capability verdict

| Static capability | Source | Call sites in running static app | React status | Verdict | Action |
|---|---|---|---|---|---|
| **`WlA11y.announce`** — WCAG 2.2 AA polite live-region announcements (theme switch, LIVE/STALE/OFFLINE data-source transitions) | `web/scripts/accessibility.js` | `app.js` ×4 (`WlA11y.announce(...)`) | **Missing** | **VALID gap** | **Migrated** to React `src/lib/a11y.ts` (stateless DOM live-region, pure + SSR-safe) and wired into `App.tsx` theme + data-source transitions; covered by `src/lib/a11y.test.ts` (5 tests) |
| `WlA11y.bindSectionNav` / `setActiveNav` — in-page anchor navigation + keyboard nav | `web/scripts/accessibility.js` | `render.js` | React sidebar/view registry (`viewRegistry.ts`) + URL routing replaces in-page anchor nav | Redundant in React (a different, better IA) | **Not migrated** — capability superseded by the view registry, not dropped |
| **`WlCharts.lineChart`** — native SVG line/area chart | `web/scripts/charts.js` | `render.js` ×1 (pre-v3 legacy path only) | Missing | **NOT valid surface** | **Not migrated** — the v3 snapshot carries **no time-series data source**; rendering a chart would be a fabricated KPI (forbidden by the front-truth discipline). Left for a task that first ships the data source |
| `WlFormat.escapeHtml` | `web/scripts/formatters.js` | `app.js` ×1 | React auto-escapes string children | Redundant in React | **Not migrated** |
| `WlFormat` other helpers (intOrDash/tokens/costAmount/duration/relativeTime) | `web/scripts/formatters.js` | not called by the running v3 app | React `lib/api.ts` `fmt*` (truth-preserving: null → UNKNOWN/—) | Parity already held by `api.ts` | **Not re-migrated** — `api.ts` formatters already encode the null→UNKNOWN discipline |

## What "parity" means here (and is now true)

- **Valid a11y capability (announcer)**: React now owns a WCAG AA polite
  live region, announced on the same four state words the static surface used
  (theme dark/light, LIVE loaded, STALE last-good, OFFLINE no-fake-data).
  Real-DOM tests (`a11y.test.ts`) prove an announce lands in
  `div[role=status][aria-live=polite]` and that the singleton region is
  reused, not duplicated.
- **Charts / escapeHtml**: intentionally *not* ported — porting them would
  either duplicate React-native behavior (escapeHtml) or fabricate a KPI with
  no data source (WlCharts). The matrix records this as an explicit,
  evidence-based decision, not an oversight.
- **Navigation**: the static anchor-nav is superseded by the typed view
  registry + URL routing (U04), which is the better IA — not a loss.

## Evidence

- `a11y.test.ts`: 5/5 green (jsdom real DOM).
- Full React suite: 23/23 green (was 18; +5 a11y), `tsc` clean, `vite build`
  green.
- Call-site scan: `WlCharts` 1 site (legacy render.js, no v3 data),
  `WlFormat` 1 site (`escapeHtml`), `WlA11y.announce` 4 sites — the matrix is
  derived from these counts, not from assumption.

## Remaining gate (not this step)

Retiring `web/` from production requires:
1. **U19** — a real Windows Tauri E2E (WebView, not `about:blank`) proving the
   React `dist` surface is the production entry.
2. The exact-SHA release (tag + checksum + installer + public readback).
Only then is `web/` deletion "parity reached" and safe. Until then the static
surface stays as the browser read-only entry — it is live, not dead.


## 2026-10-07 实测对等清单（本轮新增，非沿用旧表格）

方法说明：先按断言名逐个统计旧树套件，再按**测试标题**（不是关键字命中）在生产树里找等价物。
关键字搜索曾给出"概念已存在"的假乐观（例如 `UNKNOWN` 在 `frontend/src` 出现 36 处），
但"出现该词"不等于"有一条断言守着它"，因此下表只认后者。

| 旧树套件 | 断言数 | 契约主题 | 生产侧等价物 |
|---|---|---|---|
| `test_projection_contract.js` | 13 | 不伪造真值（UNKNOWN、估算≠账单、RFC3339、覆盖率、前向兼容） | **无** |
| `test_read_only_surface.js` | 17 | 只读面（无可变控件、无重试控件、无 CDN、不读凭据、仅 loopback、last-good、拒绝低 revision 乱序） | **无** |
| `test_render_v3.js` | 19（另一声明风格，按套件运行计入总数） | v3 渲染契约 | **无** |
| `test_responsive_contract.js` | 11 | 响应式（无横向溢出、DPI 安全断点、body ≥12px、tabular-nums、CJK/SHA 换行、reduced-motion、320px-safe） | 部分（`test_desktop_component_contract.js` 只钉住顶部留白与网格归属） |
| `test_visual_assets_r2.js` | 5 | 品牌资产与设计令牌（本地 SVG、批准的关注主题/视图、只读） | 部分（主题令牌有 `theme/tokens.test.ts` 断言双主题与 legacy purple 清除） |

生产侧现存量：vitest/RTL 标题 84 条（焦点陷阱、提示语义、主题令牌、CommandPalette、
空态/未知态诚实标题），桌面契约 11 条（能力授权映射、原生调用 await、无边框留白、
窄屏动作簇可达、标签单源、KPI 网格归属、错误边界挂载）。

**结论（纠正本轮开始时的判断）**：U03 的卡点不是浏览器入口——入口已在
`tests/workflow-assistance/test_sidecar_ui_browser_entry.py`（8 例）里钉到同一份 Vite `dist/`。
真正的卡点是：这 65 条只读与不伪造契约目前**只存在于旧树套件中**，
`git rm -r apps/observer/web` 会连带删掉它们所描述的对象，而这些套件读的就是
`web/index.html`、`web/styles/*.css`、`web/scripts/*.js`。
先删除即等于**删除项目的铁律测试**，与"truth tests outrank new features"相反。

因此切换的可执行顺序（逐项可验证，不做无法验证的那一步）：
1. 把 `test_read_only_surface.js` 与 `test_projection_contract.js` 的断言逐条重锚到生产面
   （`frontend/index.html`、`frontend/src/skins/*.css`、`frontend/dist` 与
   `src-tauri/tauri.conf.json`/`capabilities`），并保留同名主题；
2. 把 `test_responsive_contract.js` 的溢出/字号/换行/reduced-motion/320px 断言重锚到壳层 CSS，
   `test_visual_assets_r2.js` 重锚到 `frontend/src/assets` 与令牌；
3. 两条生产侧入口都各有门禁之后，删除 `web/` 与 `helpers.js` 的 `WEB/loadScripts`，
   同步 `scripts/ci/required_groups.json:27` 的 glob 与 `tests/ci/test_failfast_group.py`
   钉死清单（ERR-109）、`run_quality_gate.py:1362` 受护路径、README/架构文档、
   `observer_live_server.py` 退役桩文案；
4. 删除前落 `web/` 全量哈希清单与整目录保留点，并更新 `WORK-LAB-AUTHORITY.md` §7 的日期事实。

第 1 步完成前，`web/` 不删；U03 保持 PARTIAL。

### 2026-10-07 步骤 1 落地进度（同一轮内）

新增 `apps/observer/tests/test_production_surface_static_contract.js`（11 条静态契约），
把旧树里**文件级**那部分保证重锚到生产面：入口无远程运行时/CDN、skins 无 `url(http`/`@import http`、
UI 层无写请求（`method: POST/PUT/PATCH/DELETE` 与带 options 的 `fetch` 都为 0）、
UI 层不读凭据/env/cookie、主题与布局态不落 web storage（编辑器画布模型为唯一具名例外）、
横向溢出抑制、tabular-nums、CJK/SHA 换行、`prefers-reduced-motion`、
基础字号不被压低且**所有 <12px 声明必须落在具名微角色**（`.winctl-zoom`、`.load-strip`、
`.brand small`、`.tag/.badge`、`.kpi small`）。

断言先证伪再用：注入 CDN script、组件里加 PATCH、正文加 10px 规则、往 `lib/a11y.ts` 塞
`localStorage` —— 4/4 各自变红，文件按字节复原（`falsify_prod_surface.py`）。
两条断言首版**是我自己写错**而非生产偏离：路径分隔符未归一导致编辑器没被排除（报出 4 处
"违规"），以及把 body 字号规则误用成"任何 px 字号"（把品牌小标签算成违规）；
都按事实改正而不是放宽。

**步骤 1 只完成一半**：`test_projection_contract.js`(13) 与 `test_render_v3.js`(19) 的
**投影真值与渲染契约仍未重锚**（它们断言的是 fixture 数值、估算≠账单、RFC3339、
覆盖率、乱序 revision 拒绝等，React 侧由 `truth.test.tsx`/`lib/api.test.ts` 部分承担但
未逐条对齐），故 `apps/observer/web` 仍不删，U03 保持 PARTIAL。基准 `214acb0`。

### 2026-10-07 投影真值 13 条的逐条归属（只认具名测试标题）

生产侧现有 87 条具名断言被用于判定；下列 13 条旧断言里，**5 条**能指到具名等价物，**8 条 OPEN**。

| 旧断言（test_projection_contract.js） | 生产侧归属 |
|---|---|
| fixture parses as valid JSON object with core keys | **OPEN — no named production assertion covers this** |
| inline API FIXTURE matches authoritative fixture numbers | **OPEN — no named production assertion covers this** |
| input/output/cache/cost never collapsed into a fabricated total token | lib/api.test.ts — fmtTokens null/undefined -> UNKNOWN, never "0"; executionsToRows: unknown project -> null tokens + UNKNOWN quality (no 0) |
| cost shown as API estimate / USD, never as an exact bill | lib/api.test.ts — fmtCostQuality: absent -> UNKNOWN; components/truth.test.tsx — TokenPanel with no data renders UNKNOWN everywhere, no 0 |
| subscriptionUsage=not-metered renders as 订阅未计量, never 0 | **OPEN — no named production assertion covers this** |
| all fixture dates are strict RFC3339 | **OPEN — no named production assertion covers this** |
| coverage has numerator/denominator/scope | **OPEN — no named production assertion covers this** |
| unknown/new fields are forward compatible (extra keys ignored, no crash) | **OPEN — no named production assertion covers this** |
| missing required core keys degrade gracefully (no crash, partial/unknown shown) | **OPEN — no named production assertion covers this** |
| empty-new-install fixture renders (empty state, no crash, no fake success) | components/truth.test.tsx — ProjectPanel with no data says the registry is empty / UNKNOWN; ExecutionTable with no data and no source says waiting, not fabricates rows |
| schema file is valid JSON and lists the 10 core required keys | **OPEN — no named production assertion covers this** |
| bundled snapshot has an explicit non-live mode | App.behavior.test.tsx — without a ?api= the write-back adds no api param (no fabricated source); every KPI number is UNKNOWN when there is no snapshot |
| compact header reflects the active data mode | components/truth.test.tsx — CompactHUD with no data shows UNKNOWN transport + 0-fabrication; App.behavior.test.tsx — ?view=compact renders the Compact HUD, no sidebar rail |

`test_render_v3.js` 的 19 条同法处理前，`web/` 不删。OPEN 项的共同主题：fixture 数值一致性、RFC3339 严格日期、覆盖率三元组、未知字段前向兼容、缺键优雅降级、schema 必含 10 键、not-metered 渲染为「订阅未计量」而非 0——这些都是可从 v3 快照/`lib/api.ts` 直接断言的纯函数级性质，迁移不需要真实素材。

### 2026-10-07 步骤 1 完成：8 条 OPEN 投影契约已重锚（基准 `10ae5cb`）

新增 `frontend/src/lib/projectionTruthContract.test.ts`（8 条具名行为断言，标题里写清它替代哪条旧断言）
与 `tests/test_production_surface_static_contract.js` 的 3 条文件级断言（11→14）。
文件级那一半不能放进 vitest：`frontend/tsconfig.json` 没有 `@types/node`，
`node:fs` 直接 `TS2307`，而 CI 会跑 `npm run typecheck`——所以磁盘扫描留在 node 套件里。

| 旧断言 | 生产侧新标题（节选） | 位置 |
|---|---|---|
| fixture parses as valid JSON object with core keys | legacy "fixture parses as valid JSON object with core keys": a v3 snapshot carries every key the front reads, with the declared type | vitest |
| 同上（typed model 漂移守护） | the typed front model declares the v3 core keys, with `software` the only optional | node |
| inline API FIXTURE matches authoritative fixture numbers | legacy "inline API FIXTURE…": with no injected endpoint the descriptor is the labelled non-authoritative loopback fallback, never a fabricated source | vitest |
| 同上（不许内嵌快照字面量） | no v3 snapshot literal is embedded in the production source | node |
| cost shown as API estimate / USD, never as an exact bill ＋ subscriptionUsage=not-metered renders as 订阅未计量, never 0 | legacy "cost shown as API estimate / USD…": the token summary carries counts plus a quality label and nothing that could be read as a bill | vitest |
| 同上（整树不得出现金额/订阅字样） | the production tree renders no currency amount and no subscription wording | node |
| all fixture dates are strict RFC3339 | legacy "all fixture dates are strict RFC3339": real dates localise, malformed ones render UNKNOWN, never "Invalid Date" | vitest |
| coverage has numerator/denominator/scope | legacy "coverage has numerator/denominator/scope": the triple survives projection, a real 0 stays 0, an absent triple stays null | vitest |
| unknown/new fields are forward compatible | legacy "unknown/new fields are forward compatible…": extra keys at any level and unknown enum values never fabricate a positive | vitest |
| missing required core keys degrade gracefully | legacy "missing required core keys degrade gracefully…": absent nested objects degrade to UNKNOWN/null instead of throwing or 0 | vitest |
| empty-new-install fixture renders | legacy "empty-new-install fixture renders…": an empty install projects zero rows and an UNKNOWN transport | vitest |

**迁移时发现的真缺陷（不是测试写错）**：生产侧 7 处日期渲染都是
`x ? new Date(x).toLocaleString() : 'UNKNOWN'`。两个后果：
（1）不合法字符串会渲染成字面 "Invalid Date"；
（2）更坏——`Date.parse('2026-02-30T10:00:00Z')` **不失败**，它滚成 3 月 2 日，
把损坏时间戳伪装成可信时刻。旧契约的"严格 RFC3339"正是防这个。
因此 `lib/api.ts` 新增 `isRfc3339`/`fmtTimestamp`（形状 + 月/日/时/分/秒 + 偏移量 + 闰年的日历校验），
`Views.tsx`(5)、`SoftwareView.tsx`(1)、`WorkflowsView.tsx`(1) 全部改用它。
生产侧两个发射方（`collector_scheduler._now_iso`、`durable_worker`）都输出 `...Z`，
所以严格门不会把真数据判成 UNKNOWN——这条我是先核发射方再改渲染方的。
另外 `snapshotToTransportTruth`/`executionsToRows`/`snapshotToProjectTokens`
原先对 `snap.transport.x` 直接取属性，缺键即抛；快照跨进程（sidecar 可能不同版本），
故按旧契约补了降级。

**证伪 11/11**（`.project-local/runs/convergence-20261007-c/falsify_u03_ports.py`，每条注入后按字节复原并核对 SHA-256）：
`types.ts` 键改名、`api.ts` 里 `authoritative:false→true`、`?? 'UNKNOWN'→'ZERO'`、
绕过 RFC3339 门、覆盖率补 0、`stateTone` 默认落到 `done`、去掉可选链使其抛错、
UNKNOWN 传输粉饰成 LIVE、往 `a11y.ts` 塞 v3 字面量、塞 `USD $4.29`、
以及删掉测试自身 fixture 的一个核心键（这条是断言的变异测试，证明它真在断言）。

两处证伪**首版是我预期写错**而非门禁失效，都已按事实改注入而不是放宽断言：
`transportState ?? 'LIVE'` 打不中"空安装"一例（该例显式传 'UNKNOWN'，`??` 不触发），
`tokenTruth` 补零也打不中它——空安装例的 tokenSummary 是存在且为 null；
换成"把 UNKNOWN 传输粉饰成 LIVE"后由空安装例与降级例同时变红。
`a11y.ts` 那次也暴露 node 侧 needle 要写"账单形状"而不是裸 `$`：`api.ts` 里
`replace(..., 'http://$1')` 的 `$1` 会被裸 `$`+数字命中，第一版把我自己的合规代码报成违规。

实测存量更新：vitest/RTL **具名标题 95 条 / 执行 95 条（15 个文件）**，node 静态契约 **14 条**，
旧树 5 个套件仍为 13/17/19/11/5。全量：`vitest run` 15 files / 95 passed，
`tests/run_all_tests.js` 97 passed 0 failed，`tsc --noEmit` 干净，`vite build` 绿。

**仍未完成**：`test_render_v3.js`(19)、`test_read_only_surface.js`(17)、
`test_responsive_contract.js`(11)、`test_visual_assets_r2.js`(5) 的逐条归属；
这四张表填完并且第 1 步的等价物全部落地之前，`apps/observer/web` 不删，U03 保持 PARTIAL。

