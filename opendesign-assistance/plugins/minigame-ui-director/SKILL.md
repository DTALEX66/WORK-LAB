---
name: minigame-ui-director
zh_name: "小游戏 UI 导演"
description: "Generate mobile minigame screens with strong HUD/console/game feel, using OPEN-DESIGN-Assistance runtime and design references."
triggers:
  - "小游戏 UI"
  - "游戏 HUD"
  - "IAA 游戏界面"
  - "mobile minigame UI"
---

# Minigame UI Director

Use this skill inside Open Design when the user wants a playable/mobile game interface rather than a generic website or form.

## Inputs to ask for

- `platform`: `h5`, `wechat`, `douyin`, `android-webview`, or `generic-mobile`.
- `screen`: `start`, `main`, `failure`, `archive`, `skin-select`, `settings`, or `shop`.
- `theme`: default to `anomaly-monitor-dark` unless the user provides another theme.
- `monetization`: `rewarded-ad`, `interstitial`, `banner`, or `none`.

## Mandatory visual direction

1. Make the center of gravity a game surface, not a form.
2. Use HUD framing, short chips, icon-first controls, compact labels, and clear hierarchy.
3. Main visual area should dominate before menus, stats, or prose.
4. Avoid survey forms, SaaS dashboards, ordinary admin panels, generic cards, and long explanatory copy.
5. For anomaly/monitor themes, CCTV or surveillance content must be visually primary.

## Repository context

Use these references when available:

```text
design-system/DESIGN.md
design-system/05_DESIGN_COMMAND_CENTER/design-tokens/anomaly_monitor_dark.tokens.json
design-system/05_DESIGN_COMMAND_CENTER/component-rules/monitor_console.components.json
minigame-runtime/index.html
minigame-runtime/styles.css
minigame-runtime/src/game.js
minigame-runtime/platform/canvasRenderer.js
minigame-runtime/assets/generated/
```

## Output contract

Return a concise design package:

```text
1. Screen goal
2. Layout zones
3. Component list
4. Visual style notes
5. Interaction notes
6. Asset references
7. Implementation hints for minigame-runtime
```

If producing HTML, make it a self-contained prototype with responsive mobile-first CSS.
