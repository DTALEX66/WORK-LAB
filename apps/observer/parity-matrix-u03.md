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
