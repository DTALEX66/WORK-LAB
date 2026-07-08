function clampVisualValue(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

const ACTIVE_ANOMALY_ACTION_HINTS = Object.freeze({
  stop_failure: 'restartSystem',
  door_refuse: 'closeDoor',
  phantom_floor: 'inspectLog',
  camera_delay: 'inspectLog',
  log_echo: 'inspectLog',
  auto_button: 'restartSystem',
  floor_jump: 'inspectLog',
  zero_passenger_shadow: 'inspectLog',
  negative_floor: 'inspectLog',
  weight_mismatch: 'inspectLog',
  power_drain: 'restartSystem',
  light_flicker: 'restartSystem',
  emergency_lights: 'restartSystem',
  passenger_duplicate: 'closeDoor',
  door_gap_whisper: 'closeDoor',
  camera_blackout: 'inspectLog',
});

function getTone(anomalyLevel, gameOver) {
  if (gameOver) return 'danger';
  if (anomalyLevel >= 4) return 'critical';
  if (anomalyLevel >= 1) return 'warn';
  return 'normal';
}

function getHighlightAction(state) {
  if (state.gameOver) return 'restartSystem';
  if (state.activeAnomaly && ACTIVE_ANOMALY_ACTION_HINTS[state.activeAnomaly]) {
    return ACTIVE_ANOMALY_ACTION_HINTS[state.activeAnomaly];
  }
  if (state.anomalyLevel >= 4) return 'restartSystem';
  if (state.anomalyLevel >= 2) return 'inspectLog';
  return null;
}

export function deriveVisualState(state) {
  const anomalyLevel = Number(state?.anomalyLevel ?? 0);
  const active = Boolean(state?.activeAnomaly) || anomalyLevel > 0 || Boolean(state?.gameOver);
  const pressure = clampVisualValue(anomalyLevel / 6, 0, 1);

  return {
    tone: getTone(anomalyLevel, Boolean(state?.gameOver)),
    glitch: active,
    shake: Boolean(state?.gameOver) || anomalyLevel >= 4,
    noise: Boolean(state?.gameOver) ? 1 : Number((0.18 + pressure * 0.82).toFixed(2)),
    highlightAction: getHighlightAction(state ?? {}),
  };
}
