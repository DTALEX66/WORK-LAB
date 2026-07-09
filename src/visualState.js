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

const ACTIVE_ANOMALY_CCTV_STATES = Object.freeze({
  stop_failure: '08_emergency_stop',
  door_refuse: '09_door_jammed',
  phantom_floor: '16_wrong_floor',
  camera_delay: '11_camera_glitch',
  log_echo: '17_loop_corridor',
  auto_button: '12_scan_active',
  floor_jump: '16_wrong_floor',
  zero_passenger_shadow: '15_anomaly_wandering',
  negative_floor: '16_wrong_floor',
  weight_mismatch: '14_shadow_inside',
  power_drain: '06_power_low',
  light_flicker: '10_signal_lost',
  emergency_lights: '07_power_outage',
  passenger_duplicate: '13_entity_near',
  door_gap_whisper: '14_shadow_inside',
  camera_blackout: '10_signal_lost',
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

function getCctvState(state, anomalyLevel) {
  if (state.gameOver || anomalyLevel >= 5) return '20_threat_high';
  if (state.activeAnomaly && ACTIVE_ANOMALY_CCTV_STATES[state.activeAnomaly]) {
    return ACTIVE_ANOMALY_CCTV_STATES[state.activeAnomaly];
  }
  if (state.fakeEndingCooldownRemaining > 0) return '23_cooldown_safe';
  if (state.power <= 5) return '07_power_outage';
  if (state.power <= 22) return '06_power_low';
  if (state.stability >= 92 && state.elapsed > 0) return '19_stabilized';
  if (state.direction === 'up') return '04_moving_up';
  if (state.direction === 'down') return '05_moving_down';
  if (state.door === 'open') return '01_door_open';
  if (anomalyLevel >= 3) return '13_entity_near';
  if (anomalyLevel > 0) return '11_camera_glitch';
  return '00_idle_closed';
}

export function deriveVisualState(state) {
  const anomalyLevel = Number(state?.anomalyLevel ?? 0);
  const active = Boolean(state?.activeAnomaly) || anomalyLevel > 0 || Boolean(state?.gameOver);
  const pressure = clampVisualValue(anomalyLevel / 6, 0, 1);
  const safeState = state ?? {};

  return {
    tone: getTone(anomalyLevel, Boolean(state?.gameOver)),
    glitch: active,
    shake: Boolean(state?.gameOver) || anomalyLevel >= 4,
    noise: Boolean(state?.gameOver) ? 1 : Number((0.18 + pressure * 0.82).toFixed(2)),
    highlightAction: getHighlightAction(safeState),
    cctvState: getCctvState(safeState, anomalyLevel),
  };
}
