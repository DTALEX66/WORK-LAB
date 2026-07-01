import { appendLog, checkFailure, clamp, cloneState } from './state.js';
import CONFIG from './gameConfig.js';
import { t, actionLabel } from './skinManager.js';

const ACTIONS = {
  openDoor(state) {
    if (state.moving) return fail(state, t('actionFailMessages.openDoor_moving'));
    let next = cloneState(state);
    next.door = 'open';
    next.monitor = t('monitor.actions.openDoor', { floor: next.floor });
    next = appendLog(next, 'info', t('actionLogMessages.openDoor', { floor: next.floor }));
    return ok(next, t('actionFeedback.openDoor'));
  },

  closeDoor(state) {
    let next = cloneState(state);
    next.door = 'closed';
    next.monitor = t('monitor.actions.closeDoor');
    next = appendLog(next, 'info', t('actionLogMessages.closeDoor'));
    return ok(next, t('actionFeedback.closeDoor'));
  },

  moveUp(state) {
    if (state.door !== 'closed') return fail(state, t('actionFailMessages.moveUp_doorNotClosed'));
    let next = cloneState(state);
    const a = CONFIG.actions.moveUp;
    next.floor += 1;
    next.moving = true;
    next.direction = 'up';
    next.power = clamp(next.power - a.powerCost, 0, 100);
    next.stability = clamp(next.stability - a.stabilityCost, 0, 100);
    next.monitor = t('monitor.actions.moveUp', { floor: next.floor });
    next = appendLog(next, 'info', t('actionLogMessages.moveUp', { floor: next.floor }));
    return ok(checkFailure(next), t('actionFeedback.moveUp'));
  },

  moveDown(state) {
    if (state.door !== 'closed') return fail(state, t('actionFailMessages.moveDown_doorNotClosed'));
    let next = cloneState(state);
    const a = CONFIG.actions.moveDown;
    next.floor -= 1;
    next.moving = true;
    next.direction = 'down';
    next.power = clamp(next.power - a.powerCost, 0, 100);
    next.stability = clamp(next.stability - a.stabilityCost, 0, 100);
    next.monitor = t('monitor.actions.moveDown', { floor: next.floor });
    next = appendLog(next, 'info', t('actionLogMessages.moveDown', { floor: next.floor }));
    return ok(checkFailure(next), t('actionFeedback.moveDown'));
  },

  emergencyStop(state) {
    let next = cloneState(state);
    const es = CONFIG.actions.emergencyStop;
    if (next.activeAnomaly === 'stop_failure') {
      next.anomalyLevel = clamp(next.anomalyLevel + 1, 0, 6);
      next.stability = clamp(next.stability - es.stabilityCostOnFailure, 0, 100);
      next = appendLog(next, 'danger', t('actionLogMessages.emergencyStop_fail'));
      return fail(checkFailure(next), t('actionFeedback.emergencyStop_fail'));
    }
    next.moving = false;
    next.direction = 'idle';
    next.stability = clamp(next.stability - es.stabilityCost, 0, 100);
    next.monitor = t('monitor.actions.emergencyStop');
    next = appendLog(next, 'warn', t('actionLogMessages.emergencyStop'));
    return ok(checkFailure(next), t('actionFeedback.emergencyStop'));
  },

  restartSystem(state) {
    let next = cloneState(state);
    const rs = CONFIG.actions.restartSystem;
    next.anomalyLevel = Math.max(0, next.anomalyLevel - rs.anomalyLevelReduce);
    next.stability = clamp(next.stability + rs.stabilityRestore, 0, 100);
    next.power = clamp(next.power - rs.powerCost, 0, 100);
    next.moving = false;
    next.direction = 'idle';
    next.activeAnomaly = null;
    next.monitor = t('monitor.actions.restartSystem');
    next = appendLog(next, 'warn', t('actionLogMessages.restartSystem', { cost: rs.powerCost }));
    return ok(checkFailure(next), t('actionFeedback.restartSystem'));
  },

  inspectLog(state) {
    let next = appendLog(state, 'info', t('actionLogMessages.inspectLog'));
    const lockedCount = next.hiddenLogs.filter(h => h.locked).length;
    if (lockedCount > 0) {
      next = appendLog(next, 'ad', t('actionLogMessages.inspectLog_hiddenRecords', { count: lockedCount }));
    }
    return ok(next, t('actionFeedback.inspectLog'));
  },

  unlockHiddenLog(state) {
    // 找到第一条仍锁定的隐藏日志
    const locked = state.hiddenLogs.find(h => h.locked);
    if (!locked) {
      return fail(state, t('actionFeedback.unlockHiddenLog_noLocked'));
    }
    const unlocked = state.adHintsUsed;
    if (unlocked >= CONFIG.hiddenLogs.maxUnlockedPerRun) {
      return fail(state, t('actionFeedback.unlockHiddenLog_limit', { count: unlocked }));
    }
    let next = cloneState(state);
    const idx = next.hiddenLogs.findIndex(h => h.id === locked.id);
    if (idx !== -1) {
      next.hiddenLogs[idx] = { ...next.hiddenLogs[idx], locked: false };
    }
    next.adHintsUsed += 1;
    next = appendLog(next, 'ad', t('actionLogMessages.unlockHiddenLog_ok'));
    next.monitor = t('ui.decodeMonitor', { title: locked.title });
    return ok(next, t('ui.unlockResult', { title: locked.title }));
  },
};

function ok(state, message) {
  return { ok: true, state, message };
}

function fail(state, message) {
  const next = appendLog(state, 'warn', message);
  return { ok: false, state: next, message };
}

export function performAction(state, actionId) {
  const action = ACTIONS[actionId];
  if (!action) return fail(state, t('actionFailMessages.unknownAction', { actionId }));
  if (state.gameOver && actionId !== 'inspectLog') return fail(state, t('actionFailMessages.gameOver'));
  return action(state);
}

const ACTION_IDS = [
  'openDoor',
  'closeDoor',
  'moveUp',
  'moveDown',
  'emergencyStop',
  'restartSystem',
  'inspectLog',
  'unlockHiddenLog',
];

export function getAvailableActions() {
  return ACTION_IDS.map(id => ({ id, label: actionLabel(id) }));
}
