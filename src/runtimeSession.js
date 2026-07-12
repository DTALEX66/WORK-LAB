import CONFIG from './gameConfig.js';
import { createInitialState } from './state.js';

export function createRuntimeSession() {
  return {
    state: createInitialState(),
    nextAnomalyAt: CONFIG.anomaly.firstTriggerAt,
  };
}

export function restartRuntimeSession(previousSession = null) {
  const session = createRuntimeSession();
  const previous = previousSession?.state;
  if (!previous) return session;

  session.state.consecutiveFailures = previous.consecutiveFailures || 0;
  session.state.fakeEndingCooldownRemaining = previous.fakeEndingCooldownRemaining || 0;
  session.state.fakeEndingCount = previous.fakeEndingCount || 0;
  session.state.tutorialStep = Math.min(4, previous.tutorialStep || 0);
  session.state.fakeEndingTriggered = false;
  session.state.fakeEndingUnlocked = false;
  return session;
}

export function scheduleNextAnomalyAfterTrigger(elapsed, random = Math.random) {
  const cd = CONFIG.anomaly;
  const span = cd.cooldownMax - cd.cooldownMin + 1;
  return elapsed + cd.cooldownMin + Math.floor(random() * span);
}

export function scheduleNextAnomalyAfterRevive(elapsed) {
  return elapsed + CONFIG.anomaly.cooldownMin;
}
