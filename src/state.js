import CONFIG from './gameConfig.js';
import { createFeedbackLine } from './feedback.js';

export function createInitialState() {
  const c = CONFIG.initial;
  return {
    floor: c.floor,
    door: c.door,
    moving: c.moving,
    direction: c.direction,
    power: c.power,
    stability: c.stability,
    anomalyLevel: c.anomalyLevel,
    passengers: c.passengers,
    gameOver: c.gameOver,
    elapsed: 0,
    remaining: c.duration,
    adRevivesUsed: 0,
    hiddenLogsUnlocked: 0,
    lastAdHint: '',
    monitor: '监控画面稳定：1 层轿厢内有 1 名乘客。',
    activeAnomaly: null,
    snapshots: [],
    hiddenLogs: [],
    adHintsUsed: 0,
    consecutiveFailures: 0,
    fakeEndingTriggered: false,
    fakeEndingUnlocked: false,
    logs: [createFeedbackLine('info', '异常电梯控制台已接管。等待操作员指令。', 0)],
  };
}

export function cloneState(state) {
  return structuredClone(state);
}

export function appendLog(state, type, message) {
  const next = cloneState(state);
  next.logs.push(createFeedbackLine(type, message, next.elapsed ?? 0));
  if (next.logs.length > CONFIG.logs.maxLines) next.logs = next.logs.slice(-CONFIG.logs.maxLines);
  return next;
}

export function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

export function checkFailure(state) {
  const next = cloneState(state);
  const f = CONFIG.failure;
  if (next.power <= f.powerMin || next.stability <= f.stabilityMin || next.anomalyLevel >= f.anomalyLevelMax || next.passengers < f.passengersMin) {
    next.gameOver = true;
    next.moving = false;
    next.direction = 'idle';
  }
  return next;
}

export function saveSnapshot(state) {
  const snapshots = [...(state.snapshots || [])];
  // Build a clean copy of the state without the snapshots array (no nesting)
  const clean = {};
  for (const key of Object.keys(state)) {
    if (key === 'snapshots') continue;
    clean[key] = structuredClone(state[key]);
  }
  snapshots.push({ at: state.elapsed, state: clean });
  const next = cloneState(state);
  next.snapshots = snapshots;
  return next;
}

export function reviveFromAd(state) {
  const snapshots = state.snapshots || [];
  const rollbackWindow = CONFIG.adRevive.rollbackWindow;
  const targetElapsed = Math.max(0, state.elapsed - rollbackWindow);
  let best = null;
  let bestDist = Infinity;
  for (const snap of snapshots) {
    const dist = Math.abs(snap.at - targetElapsed);
    if (dist < bestDist) {
      bestDist = dist;
      best = snap;
    }
  }

  let next;
  if (best) {
    next = cloneState(best.state);
    next.snapshots = snapshots; // preserve snapshot history
    next.rollbackSeconds = state.elapsed - best.at;
  } else {
    // No snapshot early enough — fall back to initial baseline
    next = createInitialState();
    next.snapshots = snapshots;
    next.rollbackSeconds = state.elapsed;
    next.elapsed = state.elapsed; // keep the clock running
    next.remaining = Math.max(1, state.remaining);
  }

  next.gameOver = false;
  next.door = 'closed';
  next.moving = false;
  next.direction = 'idle';
  next.activeAnomaly = null;
  next.adRevivesUsed += 1;
  next.monitor = `广告复活完成：回滚到 ${next.rollbackSeconds} 秒前的系统状态。`;
  next = appendLog(next, 'ad', `广告复活完成：回滚 ${next.rollbackSeconds} 秒，恢复至可控状态。`);
  return next;
}

export function tickState(state, seconds = 1) {
  let next = cloneState(state);
  const tk = CONFIG.tick;
  next.elapsed += seconds;
  next.remaining = clamp(next.remaining - seconds, 0, CONFIG.initial.duration);
  if (next.moving) {
    next.power = clamp(next.power - seconds * tk.powerDrainMoving, 0, 100);
    next.stability = clamp(next.stability - seconds * tk.stabilityDrainMoving, 0, 100);
  } else {
    next.power = clamp(next.power - seconds * tk.powerDrainIdle, 0, 100);
  }
  if (next.remaining <= 0) {
    next.gameOver = true;
    next = appendLog(next, 'success', '本轮值守结束。系统仍未解释全部异常。');
  }
  return checkFailure(next);
}
