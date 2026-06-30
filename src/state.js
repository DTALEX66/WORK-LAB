import { createFeedbackLine } from './feedback.js';

export function createInitialState() {
  return {
    floor: 1,
    door: 'closed',
    moving: false,
    direction: 'idle',
    power: 100,
    stability: 100,
    anomalyLevel: 0,
    passengers: 1,
    gameOver: false,
    elapsed: 0,
    remaining: 60,
    adRevivesUsed: 0,
    hiddenLogsUnlocked: 0,
    lastAdHint: '',
    monitor: '监控画面稳定：1 层轿厢内有 1 名乘客。',
    activeAnomaly: null,
    logs: [createFeedbackLine('info', '异常电梯控制台已接管。等待操作员指令。', 0)],
  };
}

export function cloneState(state) {
  return structuredClone(state);
}

export function appendLog(state, type, message) {
  const next = cloneState(state);
  next.logs.push(createFeedbackLine(type, message, next.elapsed ?? 0));
  if (next.logs.length > 80) next.logs = next.logs.slice(-80);
  return next;
}

export function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

export function checkFailure(state) {
  const next = cloneState(state);
  if (next.power <= 0 || next.stability <= 0 || next.anomalyLevel >= 6 || next.passengers < 0) {
    next.gameOver = true;
    next.moving = false;
    next.direction = 'idle';
  }
  return next;
}

export function reviveFromAd(state) {
  let next = cloneState(state);
  next.gameOver = false;
  next.power = Math.max(45, next.power);
  next.stability = Math.max(45, next.stability);
  next.anomalyLevel = Math.min(2, next.anomalyLevel);
  next.door = 'closed';
  next.moving = false;
  next.direction = 'idle';
  next.activeAnomaly = null;
  next.adRevivesUsed += 1;
  next.monitor = '广告复活完成：系统回滚到可控状态，但异常残留仍在。';
  next = appendLog(next, 'ad', '广告复活完成：恢复电力与稳定度，异常等级暂时压低。');
  return next;
}

export function tickState(state, seconds = 1) {
  let next = cloneState(state);
  next.elapsed += seconds;
  next.remaining = clamp(next.remaining - seconds, 0, 60);
  if (next.moving) {
    next.power = clamp(next.power - seconds * 0.7, 0, 100);
    next.stability = clamp(next.stability - seconds * 0.25, 0, 100);
  } else {
    next.power = clamp(next.power - seconds * 0.18, 0, 100);
  }
  if (next.remaining <= 0) {
    next.gameOver = true;
    next = appendLog(next, 'success', '本轮值守结束。系统仍未解释全部异常。');
  }
  return checkFailure(next);
}
