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
