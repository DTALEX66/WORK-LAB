import { appendLog, checkFailure, clamp, cloneState } from './state.js';
import CONFIG from './gameConfig.js';

const ACTIONS = {
  openDoor(state) {
    if (state.moving) return fail(state, '电梯移动中，禁止开门。');
    let next = cloneState(state);
    next.door = 'open';
    next.monitor = `监控：${next.floor} 层电梯门已打开。门外走廊光线异常。`;
    next = appendLog(next, 'info', `电梯门已在 ${next.floor} 层打开。`);
    return ok(next, '电梯门已打开。');
  },

  closeDoor(state) {
    let next = cloneState(state);
    next.door = 'closed';
    next.monitor = '监控：轿厢门闭合。画面存在轻微拖影。';
    next = appendLog(next, 'info', '电梯门已关闭。');
    return ok(next, '电梯门已关闭。');
  },

  moveUp(state) {
    if (state.door !== 'closed') return fail(state, '门未关闭，禁止移动。');
    let next = cloneState(state);
    const a = CONFIG.actions.moveUp;
    next.floor += 1;
    next.moving = true;
    next.direction = 'up';
    next.power = clamp(next.power - a.powerCost, 0, 100);
    next.stability = clamp(next.stability - a.stabilityCost, 0, 100);
    next.monitor = `监控：电梯上行至 ${next.floor} 层。乘客未看向摄像头。`;
    next = appendLog(next, 'info', `电梯开始上行，当前楼层 ${next.floor}。`);
    return ok(checkFailure(next), '电梯开始上行。');
  },

  moveDown(state) {
    if (state.door !== 'closed') return fail(state, '门未关闭，禁止移动。');
    let next = cloneState(state);
    const a = CONFIG.actions.moveDown;
    next.floor -= 1;
    next.moving = true;
    next.direction = 'down';
    next.power = clamp(next.power - a.powerCost, 0, 100);
    next.stability = clamp(next.stability - a.stabilityCost, 0, 100);
    next.monitor = `监控：电梯下行至 ${next.floor} 层。楼层指示灯短暂闪烁。`;
    next = appendLog(next, 'info', `电梯开始下行，当前楼层 ${next.floor}。`);
    return ok(checkFailure(next), '电梯开始下行。');
  },

  emergencyStop(state) {
    let next = cloneState(state);
    const es = CONFIG.actions.emergencyStop;
    if (next.activeAnomaly === 'stop_failure') {
      next.anomalyLevel = clamp(next.anomalyLevel + 1, 0, 6);
      next.stability = clamp(next.stability - es.stabilityCostOnFailure, 0, 100);
      next = appendLog(next, 'danger', '急停按钮无响应。异常等级上升。');
      return fail(checkFailure(next), '急停按钮失效。');
    }
    next.moving = false;
    next.direction = 'idle';
    next.stability = clamp(next.stability - es.stabilityCost, 0, 100);
    next.monitor = '监控：电梯急停。轿厢灯光闪烁 3 次。';
    next = appendLog(next, 'warn', '执行急停：移动已停止，稳定度下降。');
    return ok(checkFailure(next), '急停已执行。');
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
    next.monitor = '监控：系统重启后恢复画面。部分录像帧丢失。';
    next = appendLog(next, 'warn', '系统重启完成：异常等级下降，但消耗 10 点电源。');
    return ok(checkFailure(next), '系统重启完成。');
  },

  inspectLog(state) {
    const next = appendLog(state, 'info', '操作员查看系统日志：最近 30 秒存在未授权楼层请求。');
    return ok(next, '已查看系统日志。');
  },

  unlockHiddenLog(state) {
    // 找到第一条仍锁定的隐藏日志
    const locked = state.hiddenLogs.find(h => h.locked);
    if (!locked) {
      return fail(state, '没有待解码的加密记录。');
    }
    const unlocked = state.adHintsUsed;
    if (unlocked >= CONFIG.hiddenLogs.maxUnlockedPerRun) {
      return fail(state, `本局已解码 ${unlocked} 条记录，达到上限。`);
    }
    let next = cloneState(state);
    const idx = next.hiddenLogs.findIndex(h => h.id === locked.id);
    if (idx !== -1) {
      next.hiddenLogs[idx] = { ...next.hiddenLogs[idx], locked: false };
    }
    next.adHintsUsed += 1;
    next = appendLog(next, 'ad', CONFIG.hiddenLogs.unlockLogMessage);
    next.monitor = `解码完成：${locked.title}。完整内容已写入系统日志。`;
    return ok(next, `已解码：${locked.title}`);
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
  if (!action) return fail(state, `未知操作：${actionId}`);
  if (state.gameOver && actionId !== 'inspectLog') return fail(state, '系统已崩溃，必须复活或重新开始。');
  return action(state);
}

export const AVAILABLE_ACTIONS = [
  { id: 'openDoor', label: '开门' },
  { id: 'closeDoor', label: '关门' },
  { id: 'moveUp', label: '上行' },
  { id: 'moveDown', label: '下行' },
  { id: 'emergencyStop', label: '急停' },
  { id: 'restartSystem', label: '系统重启' },
  { id: 'inspectLog', label: '查看日志' },
  { id: 'unlockHiddenLog', label: '解码加密记录' },
];
