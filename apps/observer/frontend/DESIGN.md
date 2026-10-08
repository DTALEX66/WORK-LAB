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

## External standards this contract is measured against

Every numeric clause below cites a primary source. Where two authorities conflict the clause names both
and picks one with a reason; it never averages them.

**Text size.** WCAG 2.2 sets **no** minimum font size — small text is policed by contrast (1.4.3), by
200% zoom (1.4.4), by reflow at 320 CSS px (1.4.10) and by text spacing (1.4.12). The floors below come
from design systems, and they are product rules, not WCAG claims: Apple's "UI Design Dos" says text should
be at least **11pt**; Material 3's smallest role is `label-small` **11sp/16**; IBM Carbon's scale bottoms
out at **12px/16**; PatternFly's `--pf-t--global--font--size--100` is **12px**; Grafana's
`createTypography.ts` uses base **14** with **12** as the small step. No authoritative source endorses
9px, so this contract's floor is **12px** for any text a user must read.

**Contrast.** WCAG 1.4.3 AA: **4.5:1** normal, **3:1** large, where "large" is 18pt (≈24px) or 14pt bold
(≈18.66px bold); AAA is 7:1 / 4.5:1. 1.4.11 AA: **3:1** for UI-component states, boundaries and graphical
objects, exempting purely decorative ones. 1.4.1 A: colour is never the only carrier — a status surface
needs a label or glyph plus shape/weight/position, and must not rely on red-vs-green alone.

**Targets.** WCAG 2.5.8 AA is the hard floor: **24×24 CSS px**, with the Spacing exception permitting a
smaller visible control if a 24×24 clearance surrounds it. Apple asks **44×44pt**, Microsoft **7.5mm ≈
40×40px at 135 PPI**, Google commonly 48dp, NN/g 1cm² — these conflict and are *not* averaged. For a
mouse-driven desktop WebView the defensible floor is 2.5.8's 24×24, and this product additionally requires
**≥32px** for a repeated primary control because the rail row is the highest-frequency target.

**Focus.** WCAG 2.2 adds 2.4.11 **Focus Not Obscured (Minimum)** (AA) — the focused component may not be
entirely hidden by author content, which is a direct constraint on an overlapping top bar — and 2.4.13
Focus Appearance (AAA: indicator area of a 2px perimeter, 3:1 focused-vs-unfocused).

**Rail behaviour.** No design system mandates a scrollable rail; the binding rules are 2.1.1 Keyboard,
2.4.11 and the ARIA APG **Disclosure Navigation** pattern (each group is a disclosure button,
`aria-expanded`, Space/Enter toggles, Escape returns focus). The expectation is therefore **both**: the
rail is its own keyboard-reachable scroll container *and* its groups collapse. Rancher's
`shell/components/nav/Group.vue` implements the per-group form.

**Toolbar overflow.** Fluent **CommandBar** specifies a "see more" overflow button with primary commands
moving to the secondary area when space is limited; Carbon **OverflowMenu** is the named pattern for
"more options exist but space is constrained". A toolbar that wraps into a vertical column satisfies
neither.

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

Light theme re-binds the same role names (`src/index.css` `html.light` block plus the mirrored skin
tokens in `src/skins/l10b-shell.css`): canvas `#F4F7FA`, ink `#0B1420` (17.21:1), muted `#4A6172`
(5.64:1 on panel, 6.02:1 on canvas), hairline `#D5E2EC`.

Muted is `#4A6172` and not `#5A7184` because the two token vocabularies in this shell disagreed (see
Known Gaps): the B10 skin already carried `#4A6172`, and the Tailwind layer carried `#5A7184`, which
measures 4.43:1 on `panel2` — under AA by a margin made entirely of one duplicated role name. One
value per role removed the failure and the discrepancy at the same time.

**Text-accent rule (normative).** A fill accent and an accent used as text are different roles.
`{colors.primary}` `#1B7FE6` in light measures 3.74:1 on the rail, so text that wants the accent takes
`--primary-text` `#1565C0` (5.34:1) instead of darkening every filled control.

**Contrast rule (normative).** Text a user must read: ≥ 4.5:1 at sizes below 18.66px, ≥ 3:1 at
≥ 18.66px bold or ≥ 24px. Non-text UI and icons: ≥ 3:1. A hairline may be below 3:1 only if the
information it separates is also conveyed by spacing or a label.

**How a ratio is computed (normative).** The instrument composites the ancestor stack root-first, but
the *decider* is the first layer from the text outward that carries a gradient or is opaque — and a
gradient is evaluated at every colour stop, with each stop's own alpha preserved. Two reasons, both
measured here: listing the page background as a candidate scored white text on a green pill at 1.04:1
"against white", a backdrop the glyph never touches; and dropping a stop's alpha turned
`.nav button.active`'s 26%-primary wash into solid `#2A91FF` and reported an 11:1 selected row as a
2.92:1 failure. A wrong number in the instrument sends the fix to the wrong file.

**Disabled text (normative).** WCAG 1.4.3 exempts inactive controls. This contract does not, at the
lower bar: a disabled label must clear **3:1**. The reason is specific to a read-only projection — the
disabled button *is* the message ("执行由 Task Protocol 创建，Observer 不发起执行"), so a control whose
label cannot be read has lost the only thing it was there to say. `opacity: 0.55` over b10's bright
filled gradient measured 1.62:1 in dark and 1.71:1 in light; the disabled state is now carried by a
neutral surface with `--muted` ink, which clears 5:1 in both themes. Opacity is not a contrast strategy.

**On-primary rule.** `{colors.on-primary}` is `{colors.canvas}` in dark (6.13:1 on `{colors.primary}`).
In light theme white-on-primary measures **4.02:1** and therefore fails the text rule: light-theme
filled controls must use `#0B1420` ink on the accent, or a darker accent stop. See Known Gaps.

## Typography

Rendered census of the shipped Overview screen at 1262×668, both themes
(`scripts/audit/text_legibility_via_cdp.py`, receipt `.project-local/artifacts/LEGIBILITY_AFTER_FLOOR.json`):
33 leaf text nodes, **smallest 12px**, lowest measured ratio 5.19:1 in dark and 5.34:1 in light. Before
the floor sweep the same instrument found 12 nodes below 12px (a 9px `{components.state-chip}`, the 10px
`{typography.label-caps}` group captions, the brand caption, the first-frame strip, the zoom readout)
and 3 AA failures in light.

**That census was scoped to the degraded state, and said so too broadly.** With no backend the shell
renders the offline card, so the 33 nodes never included a filled status pill, a disabled primary action
or a KPI numeral — precisely where the light theme was still failing. Run against a live v3 snapshot
(`--live-backend`, the release line's own sidecar on a dynamic loopback port) the same screen yields 61
nodes and found three more defects: `.tag` pills at 1.15:1, the disabled `新建执行` at 1.62:1 dark /
1.71:1 light, and the gradient-backdrop arithmetic in the instrument itself. After those fixes the live
census reads 61 nodes, 0 below floor, 0 AA failures, 0 disabled-label failures in **both** themes
(receipt `.project-local/artifacts/LEGIBILITY_LIVE2.json`). Ledger ERR-218 records the over-broad claim
so the next measured sentence states what it measured.

**Every view, with data (`--all-views`, 2026-10-08):** the census now clicks all 23 rail lanes and
scores each screen it produces — 1023 text nodes per theme, **0 below floor, 0 AA failures, 0
disabled-label failures, 0 thin views** in both themes
(receipt `.project-local/artifacts/LEGIBILITY_ALLVIEWS2.json`). Reaching that took four fixes the
single-view census could not see: the observer topology's node names were `fontSize="5"` inside a
100-unit viewBox (5 CSS px — they now live in `GraphLegend` at 12px, selectable, state named in words);
the segmented filter's selected tab was white on b10's primary→cyan gradient at 2.56:1 dark / 2.88:1
light; light-theme `--warning` amber used as *text* measured 4.48:1; and the instrument itself could not
parse the `oklab()` colours Chrome reports, which turned ten measurable nodes into UNKNOWN failures.

**Type floor (normative).** No text a user must read below **12px**. Below 12px is permitted only for a
decorative glyph that repeats information available elsewhere, and such a node must be `aria-hidden`.
The floor is enforced twice: the rendered instrument fails any node under 12px whose role is not
declared (and the declaration list is empty — every role that claimed an exemption turned out to be
text a user reads), and `tests/workflow-assistance/test_no_sub_floor_text_in_the_observer_source.py`
fails the source for the views a single page load does not render. The pinned skin is the one place a
sub-12 declaration may still be written, and only because `l10b-shell.css` restates that selector at
12px or above — "we cannot change it" is not the same as "nobody did".

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

## Reference systems

Closest analogues to a dark, dense, read-only control plane, with where their tokens actually live —
consulted rather than copied wholesale, and each with one thing not to take.

| System | Token source | Take | Don't take |
|---|---|---|---|
| Grafana | `packages/grafana-data/src/themes/createTypography.ts`, `createSpacing.ts`, `public/sass/grafana.dark.scss` | 14px base / 12px floor, even-pixel discipline for size and line-height | variable-density panels and plugin theme overrides |
| EUI (Kibana) | `packages/eui/src/global_styling/variables/`, `eui-theme-common/…/size.ts` | the 8-step spacing ramp and the `EuiSideNav` group model | light-first defaults |
| PatternFly (Keycloak admin UI) | `patternfly:src/patternfly/base/tokens/tokens-dark.scss` | a paired dark token set and the 12/14px ramp | a 16px base body |
| Portainer | `app/assets/css/theme.css`, `colors.json` | a JSON colour token file feeding a dark admin shell | Bootstrap/RDash 11–12px legacy chrome |
| Rancher Dashboard | `shell/assets/styles/`, `shell/components/nav/`, `HeaderPageActionMenu.vue` | collapsible + pinned nav groups and a page-action overflow menu | mixed Element-Plus sizing |
| Jaeger UI | `packages/jaeger-ui/src` (no token file found) | waterfall row density and the left rail | inline-styled MUI with no token layer |
| Langfuse | `web/src/styles/globals.css`, `fonts.ts` | one CSS-variable token set driving both themes — which is exactly the shape of the light-theme failures recorded below | doc-site prose typography leaking into app chrome |
| SigNoz | `frontend/src/styles/`, antd theme tokens | log/trace table density | theme values left inline instead of tokenised |

## Known Gaps

`needs-design-decision` unless marked otherwise (implementation deviation).

1. ~~**Dead rail scroll**~~ — CLOSED 2026-10-08. `.app` had no height, so the rail grew to its content
   (1707px in an 807px viewport) and `.nav { overflow-y: auto }` never engaged; 9 of 23 items were
   reachable. The shell layer now gives the column a real height and the rail scrolls and collapses:
   measured `clientH 432 / scrollH 1554`, `overflow=True`, last item hit-testable, 7 group disclosures.
   Enforced by `scripts/audit/topbar_geometry_via_cdp.py` (`nav_items_reachable`,
   `nav_groups_are_disclosures`).
2. **Theme is not persisted to web storage — by contract, not by accident.** I first recorded this as a
   gap and built the storage fallback; `apps/observer/tests/test_production_surface_static_contract.js`
   ("theme and layout state never persist to web storage") fails the build on any `localStorage` /
   `sessionStorage` use in the UI layer, so the feature was reverted rather than the test relaxed: a
   projection whose appearance depends on hidden client state cannot be reproduced from its URL, and this
   project's evidence depends on exactly that. The sanctioned mechanism already works — toggling the
   theme rewrites the address (`?theme=light`), so reloading *that* URL comes back light, measured by the
   legibility instrument (`theme_actually_applied PASS asked=light html.class='light'`) and asserted by
   `src/themeSwitch.contract.test.tsx`. Reloading the bare address returns to dark, which is the design
   language, not a loss. If the owner wants the choice to survive a bare relaunch, the place that decides
   is the desktop shell's launch URL, and that is an owner-level call, not a UI-layer storage exception.
3. ~~**Sub-AA frames during theme crossfade**~~ — CLOSED 2026-10-08. The pinned skin eases colour over
   ~200-300ms and nav text was measured passing through 1.22:1. `App.tsx` now holds `transition` and
   `animation` off on `<html>` for the two frames the swap needs (`.theme-instant`), so the palette
   changes in one frame and hover/press motion stays animated; the release is asserted on real
   `requestAnimationFrame` boundaries, not on timers.
4. ~~**Light-theme contrast failures (settled state)**~~ — CLOSED 2026-10-08. The three failures were
   `.avatar` (white glyph on light `--surface2`, 1.13:1), `.brand small` (`var(--primary)` as text,
   3.74:1) and the 9px hint chip (4.43:1). Fixed in the shell layer because b10 stays verbatim (D-11):
   the avatar glyph takes ink in light, the brand caption takes `--primary-text`, and `--color-muted`
   was aligned to the value the skin already carried. Same instrument, same viewport:
   0 AA failures in either theme, lowest ratio 5.34:1 in light.
5. ~~**Type floor violated**~~ — CLOSED 2026-10-08. 125 `text-[9px]/[10px]/[11px]` utilities across 30
   files and three shell micro roles were raised to 12px; see Typography for the two enforcement points.
6. **Three token sources disagree** — radii: `src/theme/tokens.ts` 4/10/16/22 vs
   `design-tokens.json` 11/20/30 vs rendered 12/14/18/20; glass blur 18px vs 34px. Decision needed on
   whether `design-tokens.json` is a brand handoff artefact (then it must stop claiming to be the UI
   token source) or the UI source (then `tokens.ts` changes).
7. **Two parallel variable vocabularies** — the Tailwind layer reads `--color-*` / `--*-rgb` while the
   B10 skin reads `--bg` / `--text` / `--muted` / `--border` / `--surface`. PARTIALLY CLOSED: `muted`
   now carries one value in both, which is what removed gap 4's chip failure. The remaining pairs
   (`border`, `surface`, `primary`) still name different values with the same word, so a theme change
   can repaint one layer and not the other. Needs one canonical role set.
8. **The static micro-role allowlist is now dead weight** —
   `apps/observer/tests/test_production_surface_static_contract.js` permits sub-12px CSS in seven named
   roles. After the floor sweep the skin declares sub-12px in one place only (`.brand small`, pinned by
   b10 and overridden here), so six of its allowlist entries match nothing and nothing fails. It reports
   "no offenders" without noticing its own list rotted; the staleness rule
   `no_stale_floor_exception` in the legibility instrument is the model to copy.
9. **The rendered proof does not run in CI** — both browser instruments need a Chromium binary, which
   the Actions runner does not have, so they are run locally against `dist` and their receipts are cited
   by hand. CI enforces the source-level guards. `verify_design_contract.py` still parses token files and
   touches no rendered value, so its `DESIGN_CONTRACT_PASS` is not evidence of UI compliance.
