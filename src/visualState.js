/**
 * visualState.js — 驱动 CCTV 视觉状态的核心映射
 *
 * V4 重构原则：
 * - CCTV 状态由 anomalyContent.js 的 visualState 字段驱动
 * - 所有异常必须有对应的 visualState 映射
 * - 正常状态由运行时条件推导，不硬编码
 */
import { getAllAnomalyContents, getAnomalyCctvState } from './anomalyContent.js';

function clampVisualValue(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

// ─── 异常动作提示（用于 V3 DOM 界面 / 非 base 模式的遗留兼容） ──
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

// ─── 异常 CCTV 状态映射（从 anomalyContent.js 驱动） ────────
// getAnomalyCctvState() 现在是统一入口

export function getAnomalyResolutionAction(anomalyId) {
  return ACTIVE_ANOMALY_ACTION_HINTS[anomalyId] || null;
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

function getTone(anomalyLevel, gameOver) {
  if (gameOver) return 'danger';
  if (anomalyLevel >= 4) return 'critical';
  if (anomalyLevel >= 1) return 'warn';
  return 'normal';
}

function getCctvState(state, anomalyLevel) {
  if (state.result === 'success') return '19_stabilized';
  if (state.gameOver || anomalyLevel >= 5) return '20_threat_high';

  // 异常 CCTV 状态由 anomalyContent.js 驱动
  if (state.activeAnomaly) {
    const cctvState = getAnomalyCctvState(state.activeAnomaly);
    if (cctvState) return cctvState;
  }

  if (state.fakeEndingCooldownRemaining > 0) return '23_cooldown_safe';
  if (state.power <= 5) return '07_power_outage';
  if (state.power <= 22) return '06_power_low';

  // 正常运行时状态
  if (state.direction === 'up') return '04_moving_up';
  if (state.direction === 'down') return '05_moving_down';
  if (state.door === 'open') return '01_door_open';
  // 开门中动画
  if (state.door === 'opening') return '02_door_opening';
  // 关门中动画
  if (state.door === 'closing') return '03_door_closing';

  if (state.stability >= 92 && state.elapsed > 0) return '19_stabilized';
  if (anomalyLevel >= 3) return '13_entity_near';
  if (anomalyLevel > 0) return '10_signal_lost';
  return '00_idle_closed';
}

export function deriveVisualState(state) {
  const neutralInspection = state?.inspection?.status === 'pending' && state?.inspection?.kind === 'normal';
  const anomalyLevel = neutralInspection ? 0 : Number(state?.anomalyLevel ?? 0);
  const safeState = neutralInspection
    ? { ...(state ?? {}), activeAnomaly: null, anomalyLevel: 0 }
    : (state ?? {});
  const success = safeState.result === 'success';
  const active = !success && (Boolean(safeState.activeAnomaly) || anomalyLevel > 0 || Boolean(safeState.gameOver));
  const pressure = clampVisualValue(anomalyLevel / 6, 0, 1);

  return {
    tone: success ? 'normal' : getTone(anomalyLevel, Boolean(safeState.gameOver)),
    glitch: active,
    shake: !success && (Boolean(safeState.gameOver) || anomalyLevel >= 4),
    noise: success ? 0.18 : Boolean(safeState.gameOver) ? 1 : Number((0.18 + pressure * 0.82).toFixed(2)),
    highlightAction: getHighlightAction(safeState),
    cctvState: getCctvState(safeState, anomalyLevel),
  };
}
