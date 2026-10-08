---
version: alpha
name: WORK-LAB Observer — Liquid Glass control plane
description: "Design contract for the WORK-LAB Observer desktop front-end, captured from the shipped implementation (pinned B10 skin + L10b overlay + src/theme/tokens.ts) and from measured rendering evidence. Dark is the default theme; light is an overlay. Read-only projection surface, so no component in this system may mutate workflow state."
colors:
  primary: "#2A91FF"
  secondary: "#20CDE1"
  on-primary: "#050D16"
  ink: "#EEF6FC"
  muted: "#8EABBC"
  canvas: "#050D16"
  surface-sidebar: "#07111C"
  surface-panel: "#081420"
  surface-raised: "#0C1B2A"
  hairline: "#17435D"
  success: "#22C55E"
  warning: "#F59E0B"
  danger: "#EF4444"
  info: "#3882F6"
typography:
  kpi-value:
    fontFamily: "Inter, 'Segoe UI', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: 30px
    fontWeight: 700
    lineHeight: 1
    letterSpacing: -0.025em
  heading-lg:
    fontFamily: "Inter, 'Segoe UI', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: 18px
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: 0px
  brand-name:
    fontFamily: "Inter, 'Segoe UI', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: 17px
    fontWeight: 400
    lineHeight: 1.15
    letterSpacing: 0px
  body-md:
    fontFamily: "Inter, 'Segoe UI', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0px
  body-strong:
    fontFamily: "Inter, 'Segoe UI', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: 16px
    fontWeight: 700
    lineHeight: 1.5
    letterSpacing: 0px
  label-caps:
    fontFamily: "Inter, 'Segoe UI', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: 12px
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: 0.08em
  meta-sm:
    fontFamily: "Inter, 'Segoe UI', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.35
    letterSpacing: 0px
  code-mono:
    fontFamily: "'JetBrains Mono', Consolas, monospace"
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0px
rounded:
  none: 0px
  sm: 4px
  md: 10px
  lg: 16px
  xl: 22px
  full: 9999px
spacing:
  xxs: 4px
  xs: 6px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  xxl: 32px
  section: 40px
components:
  nav-item:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.body-md}"
    rounded: "{rounded.md}"
    padding: "8px 14px"
    height: 38px
  nav-item-active:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink}"
    typography: "{typography.body-md}"
    rounded: "{rounded.md}"
    padding: "8px 14px"
    height: 38px
  action-button:
    backgroundColor: "{colors.surface-panel}"
    textColor: "{colors.ink}"
    typography: "{typography.body-md}"
    rounded: "{rounded.lg}"
    padding: "10px 16px"
    height: 44px
  text-input-search:
    backgroundColor: "{colors.surface-panel}"
    textColor: "{colors.ink}"
    typography: "{typography.body-md}"
    rounded: "{rounded.lg}"
    padding: "10px 14px"
    height: 44px
  kpi-card:
    backgroundColor: "{colors.surface-panel}"
    textColor: "{colors.ink}"
    typography: "{typography.kpi-value}"
    rounded: "{rounded.xl}"
    padding: "20px"
  state-chip:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.muted}"
    typography: "{typography.code-mono}"
    rounded: "{rounded.sm}"
    padding: "2px 6px"
  status-danger:
    backgroundColor: "transparent"
    textColor: "{colors.danger}"
    typography: "{typography.heading-lg}"
    rounded: "{rounded.none}"
    padding: "0px"
  brand-mark:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary}"
    rounded: "{rounded.none}"
    width: 42px
    height: 22px
---

# WORK-LAB Observer design contract

## Overview

This system was **captured from the shipped implementation**, not designed first. Three sources carry
numbers today and they do not agree; the authority order is fixed below and every token in the
frontmatter is traceable to source #1.

1. `src/theme/tokens.ts` — declared single source of truth, mirrored by `src/index.css` and asserted by
   `src/theme/tokens.test.ts`. **Authoritative.**
2. `src/skins/b10.css` (pinned skin, immutable per decision D-11) and `src/skins/l10b-shell.css`
   (overlay). Binding for anything they define that #1 is silent about; the overlay may only add, never
   rewrite #1's roles.
3. `src/assets/brand/design-tokens.json` (`name: WORK-LAB Observer Liquid Glass`, `version: 2.0.0`).
   Supporting evidence for brand accents and glass parameters only — its `radii` block conflicts with
   #1 and is recorded in Known Gaps rather than merged.

Product feel: dark, dense, instrument-like. A control plane, not a marketing surface. Cyan→blue accents
carry state; nothing decorative may outrank a number. The surface is a strict read-only projection —
no component in this file authorises a write, approve, retry or rollback action.

Two orthogonal axes exist and must not be confused:

- **Theme**: `dark` (default, `:root`) / `light` (`html.light`). Colour roles only.
- **Density view**: `?view=full` / `?view=compact`. Layout density only. **This is a user-selected mode,
  not a responsive breakpoint** — see Responsive Behavior.

## Colors

Semantic roles, dark theme (measured contrast against the role it sits on, WCAG 2.1 relative luminance,
alpha composited down the ancestor chain):

| Token | Value | Role | Measured |
|---|---|---|---|
| `{colors.canvas}` | `#050D16` | app background | — |
| `{colors.ink}` | `#EEF6FC` | primary text | 17.87:1 on canvas |
| `{colors.muted}` | `#8EABBC` | secondary text, labels | 8.09:1 on canvas, 7.22:1 on `{colors.surface-raised}` |
| `{colors.primary}` | `#2A91FF` | accent, links, focus | 6.13:1 on canvas |
| `{colors.danger}` | `#EF4444` | error, refused, offline | 5.19:1 on canvas |
| `{colors.hairline}` | `#17435D` | borders | 1.23:1 vs canvas — **decorative only, never carries meaning alone** |

Light theme re-binds the same role names (`src/index.css` `html.light` block): canvas `#F4F7FA`,
ink `#0B1420` (17.21:1), muted `#5A7184` (4.73:1 on canvas, 5.08:1 on panel), primary `#1B7FE6`
(3.74:1 on canvas), hairline `#D5E2EC`.

**Contrast rule (normative).** Text a user must read: ≥ 4.5:1 at sizes below 18.66px, ≥ 3:1 at
≥ 18.66px bold or ≥ 24px. Non-text UI and icons: ≥ 3:1. A hairline may be below 3:1 only if the
information it separates is also conveyed by spacing or a label.

**On-primary rule.** `{colors.on-primary}` is `{colors.canvas}` in dark (6.13:1 on `{colors.primary}`).
In light theme white-on-primary measures **4.02:1** and therefore fails the text rule: light-theme
filled controls must use `#0B1420` ink on the accent, or a darker accent stop. See Known Gaps.

## Typography

Rendered census of the shipped screen (52 text-bearing nodes, both themes): the dominant level is
`{typography.body-md}` 16px/400 (30 nodes); group captions are 10px/600 with 1.2px tracking; the search
hint chip is 9px mono; the brand sub-label is 10px.

**Type floor (normative).** No text a user must read below **12px**. Below 12px is permitted only for a
decorative glyph that repeats information available elsewhere, and such a node must be `aria-hidden`.
The current 9px `{components.state-chip}` and 10px `{typography.label-caps}` usage violates this floor;
the frontmatter above already states the corrected 12px values, so implementing the standard means
raising them, not lowering the rule.

Tabular figures are required on every metric (`font-variant-numeric: tabular-nums` on
`{typography.kpi-value}`), so KPI columns do not jitter between polls.

## Layout

- Shell: fixed left rail + top bar + scrolling main. Rail width 210px at comfortable density.
- Rail rhythm: nav groups separated by `{spacing.xs}` inside a group and `{spacing.md}` between groups;
  each group carries a `{typography.label-caps}` caption.
- Main content max rhythm follows `{spacing.section}` between cards; cards use `{spacing.lg}` internal
  padding at KPI size, `{spacing.md}` elsewhere.
- **The rail is a scroll container and must be bounded.** See the reachability rule in Responsive
  Behavior — this is the single most severe gap in the current implementation.

## Elevation & Depth

- `{components.kpi-card}` and panels: `--shadow: 0 20px 80px rgba(0,0,0,.35)`; softer surfaces use
  `--shadow-soft: 0 12px 48px rgba(0,0,0,.22)`.
- Glass: blur 18px (`--blur`), brand file claims 34px — conflict recorded, `src/theme/tokens.ts` wins.
- The top bar is separated from content by a hairline only. Because a hairline alone failed the
  legibility intent (measured 0.8px at 60% alpha), a band boundary must be carried by **either** a
  visible surface change **or** ≥ `{spacing.lg}` gap **or** a labelled region. Overlapping the main
  region under the bar (measured: main top sits 128px above the bar bottom) is permitted only when the
  main region reserves matching padding — and that pairing must be asserted, not assumed.

## Shapes

`{rounded.sm}` 4px chips and inline code, `{rounded.md}` 10px nav rows and small controls,
`{rounded.lg}` 16px inputs and action buttons, `{rounded.xl}` 22px cards, `{rounded.full}` avatars.
Rendered evidence also contains 12px, 14px, 18px and 20px radii that map to no token — those are drift,
not a scale.

## Components

State coverage required for every interactive family: default, hover, **focus-visible**, active,
disabled, loading, empty, error. `{components.nav-item-active}` is expressed with both a fill change and
a `::before` edge bar plus `aria-current="page"` — colour alone is never the only signal.
`{components.brand-mark}` is the cut-out project logo used as a CSS mask with the skin gradient behind
it; the glow lives on the unmasked parent, because a mask applied after a filter clips its own glow.

## Do's and Don'ts

- **Do** take colour, radius and duration from `{colors.*}` / `{rounded.*}` / the motion scale in
  `src/theme/tokens.ts`. **Don't** write a hex, an `arbitrary Tailwind value` or a `px` radius in a
  component.
- **Do** keep `src/skins/b10.css` byte-identical (decision D-11). All new shell behaviour goes in the
  overlay with a specificity-raising selector.
- **Do** treat `?view=compact` as a density mode. **Don't** cite it as evidence of responsive support.
- **Don't** render a fabricated value. An unavailable field shows `UNKNOWN`; an offline source shows the
  degraded card. **But** the degraded card must name the view it belongs to (see SCREEN_SPEC.md).
- **Don't** let a theme crossfade pass through a sub-AA frame; colour changes on theme switch are
  instant, motion is reserved for state, not for repainting the palette.
- **Don't** put meaningful text below 12px, and never make a hairline the only separator.

## Responsive Behavior

Normative bands, to be asserted by `scripts/audit/topbar_geometry_via_cdp.py`:

- **≥ 1100px**: rail 210px, action row inline, no wrapping.
- **760–1099px**: rail 210px, action row may drop secondary controls into an overflow menu; the primary
  action and the theme toggle stay visible.
- **< 760px**: rail collapses to an icon rail or a drawer; the action row becomes an overflow menu; no
  horizontal page overflow; every control ≥ 44px tall.
- **Vertical reachability (all bands)**: every item in `{components.nav-item}` is either visible in the
  viewport or reachable by scrolling the rail. A scroll container that cannot scroll is a defect, not a
  layout. The rail must be height-bounded (`100dvh` or grid row sizing) so its `overflow-y` is live.
- Overflow收纳: when the action row cannot fit, controls collapse into a `更多` menu; they must not
  stack vertically forever.

## Known Gaps

`needs-design-decision` unless marked otherwise (implementation deviation).

1. **Dead rail scroll** — `.sidebar` grows to content (measured height 1707px in an 807px viewport,
   `overflow-y: visible`), so `.nav { overflow-y: auto }` never engages
   (`clientHeight == scrollHeight == 1496`) and the document cannot scroll either
   (`scrollHeight 807 == clientHeight 807`). 23 nav items exist, 9 are reachable. Implementation
   deviation; blocker.
2. **Theme is not persisted** — after selecting light, `localStorage` keys are empty
   (`lsKeys: ""`), so the choice is lost on reload. Needs a product decision on storage location
   (this project forbids new credential/config layers, but a UI preference is not one).
3. **Sub-AA frames during theme crossfade** — measured nav text passing through 1.22:1 for up to
   ~300ms after a switch. Implementation deviation.
4. **Light-theme contrast failures (settled state)** — 3 of 52 text nodes fail AA: avatar glyph 1.13:1,
   brand sub-label 3.74:1, 9px hint chip 4.43:1. Dark theme: 0 failures.
5. **Type floor violated** — 9px and 10px meaningful text in both themes.
6. **Three token sources disagree** — radii: `src/theme/tokens.ts` 4/10/16/22 vs
   `design-tokens.json` 11/20/30 vs rendered 12/14/18/20; glass blur 18px vs 34px. Decision needed on
   whether `design-tokens.json` is a brand handoff artefact (then it must stop claiming to be the UI
   token source) or the UI source (then `tokens.ts` changes).
7. **Two parallel variable vocabularies** — the Tailwind layer reads `--color-*` / `--*-rgb` while the
   B10 skin reads `--bg` / `--text` / `--muted` / `--border` / `--surface`. Both define "muted" and
   "border" with different values, so a theme change can repaint one layer and not the other. This is
   the root cause shape behind gaps 3 and 4 and needs one canonical role set.
8. **No machine-readable contract existed before this file** — `verify_design_contract.py` reported
   `DESIGN_CONTRACT_PASS` while touching no rendered value; passing it is not evidence of UI compliance.
