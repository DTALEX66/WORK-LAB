---
name: anomaly-monitor-hud
zh_name: "异常监控 HUD"
description: "Specialized Open Design skill for CCTV, surveillance, anomaly monitor, and control-console HUD interfaces."
triggers:
  - "异常监控"
  - "CCTV HUD"
  - "监控终端"
  - "control console"
---

# Anomaly Monitor HUD

Use this skill for dark surveillance, monitoring-room, CCTV, anomaly-detection, and hardware-control interfaces.

## Inputs

- `scene`: `elevator`, `hospital`, `security`, `factory`, `subway`, `hotel`, or custom.
- `riskLevel`: `low`, `medium`, `high`, `critical`.
- `surface`: `mobile`, `desktop`, `tablet`, `stream-overlay`.

## Visual rules

1. CCTV/monitor content must be the hero surface.
2. Controls look like hardware, not survey buttons.
3. Telemetry appears as short chips, codes, meters, and status strips.
4. Logs are compact and atmospheric, never a paragraph wall.
5. Red is reserved for danger; cyan/green is reserved for system state.
6. Glitch/noise supports readability; it never covers the primary controls.

## Output contract

```text
1. Scene summary
2. HUD layout zones
3. Control model
4. Telemetry model
5. CCTV/asset references
6. Color/type/material notes
7. Responsive behavior
8. Implementation prompt
```
