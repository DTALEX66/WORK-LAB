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
