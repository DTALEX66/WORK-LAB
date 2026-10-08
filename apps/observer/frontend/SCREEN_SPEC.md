# SCREEN_SPEC — WORK-LAB Observer main surface

Companion to `DESIGN.md`. Where DESIGN.md owns tokens and component contracts, this file owns
**page-level layout, state behaviour and reachability**, and every clause here is written as something
`scripts/audit/topbar_geometry_via_cdp.py` can assert on a rendered window. Numbers marked *measured*
come from `.project-local/artifacts/design-qa-20261008/` (screenshots at six widths,
`live-state.json`, `contrast-corrected.json`).

Target surface: `apps/observer/frontend`, route `/?view=<evidence|work|execution|taskpacks|delivery|
execution-detail|agents|projects|workflows|…>`, desktop WebView (Chromium) and desktop browser.

## Regions

```
┌──────────┬───────────────────────────────────────────────┐
│          │  A  top bar: brand-mark + search + status      │
│  R rail  ├───────────────────────────────────────────────┤
│          │  B  action row: 通知 / 工作区 / 密度 / 主题 …   │
│          ├───────────────────────────────────────────────┤
│          │  C  main: view content                         │
└──────────┴───────────────────────────────────────────────┘
```

- **R rail** — fixed 210px (`{spacing}` rhythm per DESIGN.md Layout). Contains brand block, grouped nav,
  footer. It is the only element permitted to be full-height.
- **A top bar** — one row, height ≤ 64px at comfortable density. *Measured 129px tall including region B;
  the two rows are one visual band today and must either be declared one band or be separated.*
- **B action row** — grouped controls. Belongs to the top bar band; must be visually attached to A
  (shared surface or an explicit divider), not floating over C.
- **C main** — scrolls. Never scrolls the document instead of itself.

## Boundary rules (normative)

1. Every band boundary must be carried by **at least two** of: a surface/colour step, a ≥ `{spacing.lg}`
   gap, a visible divider ≥ 1px at ≥ 3:1 against both sides, or a labelled region.
   *Violation today (measured): the top bar separates from content with a 0.8px hairline at 60% alpha
   (1.23:1), no shadow, and `main` has no top border; region B floats over region C.*
2. Region C must not start underneath region A. If overlap is used for a glass effect, the reserved
   padding must be ≥ A's height and the assertion must check both numbers.
   *Violation today (measured): `main.top` is 128px above `topbar.bottom` at every width, in both themes.*
   This is not only a visual grouping problem: WCAG 2.2 **2.4.11 Focus Not Obscured (Minimum)** forbids
   author content entirely hiding the focused component, so an overlapping bar must be proven not to cover
   a focused control — asserted by focusing the first and last focusable element of region C and checking
   their rects against region A's, not by eyeballing a screenshot.
3. The rail's right edge may use `{colors.hairline}`, but the rail must also be a distinct surface
   (`{colors.surface-sidebar}` ≠ `{colors.canvas}`) so the boundary survives a hairline being invisible.
4. Every interactive target is ≥ **24×24 CSS px** (WCAG 2.5.8 AA, including its Spacing exception) and any
   repeated primary control ≥ 32px on its shortest side; see DESIGN.md `External standards` for the
   conflicting vendor numbers and why 24 was chosen over 40/44/48.

## Navigation reachability (normative)

1. **Every nav item is reachable.** For each `.nav button`, either its rect is inside the viewport, or
   its scroll ancestor reports `scrollHeight > clientHeight` and scrolling to it brings it into view.
   A container with `overflow-y: auto` whose `clientHeight == scrollHeight` is a defect, not a scroll
   container.
   *Violation today (measured at 1386×807): `.sidebar` height 1707px with `overflow-y: visible`;
   `.nav` `clientHeight == scrollHeight == 1496`; document `scrollHeight == clientHeight == 807`;
   23 nav items, 9 reachable, the rest permanently clipped.*
2. The rail is height-bounded to the viewport (`100dvh` or grid row sizing) so rule 1 can be satisfied
   at any window height, including the smallest supported 600px. **Fixed by `36f9a297`** — measured after
   the change: `.nav` clientHeight 1505 → 595 against scrollHeight 1505, `scrollTop` reaches 910, the last
   item (设置) is visible with `elementFromPoint` landing inside its own button, and clicking it moves
   `.active`.
3. Scrolling is necessary but not sufficient. Per the ARIA APG **Disclosure Navigation** pattern (and
   Rancher's `shell/components/nav/Group.vue`), each group is a disclosure button with `aria-expanded`,
   Space/Enter toggling and Escape returning focus, so a long rail can be shortened as well as scrolled.
   Group collapse is **not implemented** — recorded as an open deviation, not as satisfied by the fix.
4. Group captions (`{typography.label-caps}`) are decorative duplicates of the item labels below them
   and must not be the only way to find a group by keyboard.
5. Active item is marked by fill **plus** edge bar **plus** `aria-current="page"` — colour alone is
   insufficient, and the active state must be distinguishable in the light theme too.

## Action row and overflow (normative)

1. The action row never stacks vertically. When the band cannot fit all controls, controls beyond the
   primary action and the theme toggle collapse into a `更多` menu button. This is the named pattern in
   Fluent **CommandBar** (a "see more" button; primary commands move to the secondary area when space is
   limited) and Carbon **OverflowMenu** ("additional options… but there is a space constraint") — a
   wrapping column satisfies neither.
   *Violation today (measured): `.top-actions { flex-wrap: wrap }`, 4 children, no overflow control;
   at 430px the row's usable width is 76px and the buttons stack into a column.*
2. The overflow menu is a real menu: `aria-expanded`, keyboard operable, focus returned to the trigger on
   close, and it must not be clipped by region A's bounds.
3. Minimum touch/click target 44×44px for every control in A and B.

## Responsive bands (normative)

| Band | Rail | Action row | Search | Required assertions |
|---|---|---|---|---|
| ≥ 1100px | 210px visible | inline | full width | no horizontal overflow; no wrap |
| 760–1099px | 210px visible | overflow menu allowed | full width | no horizontal overflow; primary action visible |
| < 760px | icon rail or drawer | overflow menu required | icon + shortcut chip | no horizontal overflow; every item reachable; targets ≥ 44px |

*Measured today: the rail stays 210px at 1400/1100/900/700/560/430 — i.e. 49% of a 430px window — and
`?view=compact` does not change with width. `compact` is a user density mode; it is not a breakpoint and
must never be cited as responsive evidence.*

## Degraded and offline states (normative)

1. When the backend snapshot is unreachable, the surface must show the degraded card. Showing fabricated
   or cached-as-live data is forbidden (`UNKNOWN ≠ 0`, `STALE ≠ LIVE`).
2. **The degraded card must identify the view it belongs to.** Ten views currently render a byte-identical
   card, so a successful navigation is indistinguishable from a dead click — the owner's report of
   "左侧导航没反应" came from exactly this, not from a broken handler (verified: `active`/`aria-current`
   move, and the card's reason line changes from `事件流中断 — 已停止 LIVE 宣称…` to
   `快照获取失败 (数据源离线或端点不可达) — 保持 UNKNOWN，不伪造数据`).
   Required: view title, the specific resource that is unavailable, and the last known freshness or
   `UNKNOWN`.
3. Retry affordance must be visible and must state what retrying does in a read-only projection
   (re-read only; no side effects).
4. A reconnect loop must not cause a visible flash: no region may repaint its background before its text
   colours, and theme/palette changes are excluded from colour transitions.
   *Measured today: nav text passes through 1.22:1 for up to ~300ms after a theme switch.*

## States required per region

- Rail item: default, hover, focus-visible, active/selected, disabled.
- Action button: default, hover, focus-visible, pressed, disabled, loading (when it triggers a re-read).
- Search: empty, focused (visible ring, not colour-only), typing, no-result, cleared.
- Main card: loading skeleton, populated, empty, degraded/offline, error with reason code.

## Text and contrast (normative, restated from DESIGN.md)

- No meaningful text below 12px. *Measured minimum today: 9px.*
- Text contrast ≥ 4.5:1 below 18.66px (≥ 3:1 for large/bold). Measured in the settled state:
  dark theme 0 of 52 nodes fail; light theme 3 of 52 fail — avatar glyph 1.13:1, brand sub-label
  3.74:1, hint chip 4.43:1.
- Theme selection persists across reload. *Measured today: `localStorage` is empty after selecting
  light, so the choice is lost.*

## Gate coverage owed

`scripts/audit/topbar_geometry_via_cdp.py` currently asserts 17 checks across two viewports
(1262 and 482) and passes. It does **not** assert: rail reachability, band boundaries, action overflow,
contrast, theme persistence, or the degraded-card-per-view rule. Those six assertion families are the
acceptance list for this spec; each must include a planted-failure control proving it can go red.
