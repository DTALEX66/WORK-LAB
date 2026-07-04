import CONFIG from './gameConfig.js';
import { createInitialState } from './state.js';

export function createRuntimeSession() {
  return {
    state: createInitialState(),
    nextAnomalyAt: CONFIG.anomaly.firstTriggerAt,
  };
}

export function restartRuntimeSession() {
  return createRuntimeSession();
}

export function scheduleNextAnomalyAfterTrigger(elapsed, random = Math.random) {
  const cd = CONFIG.anomaly;
  const span = cd.cooldownMax - cd.cooldownMin + 1;
  return elapsed + cd.cooldownMin + Math.floor(random() * span);
}

export function scheduleNextAnomalyAfterRevive(elapsed) {
  return elapsed + CONFIG.anomaly.cooldownMin;
}
