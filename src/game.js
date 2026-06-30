import { AVAILABLE_ACTIONS, performAction } from './actions.js';
import { applyAnomaly, pickNextAnomaly } from './events.js';
import { getToneForState, summarizeFailure } from './feedback.js';
import { createInitialState, reviveFromAd, saveSnapshot, tickState } from './state.js';
import CONFIG from './gameConfig.js';
import { playClick, playSuccess, playFail, playAnomaly, playWarning, playCrash, playRevive, playRestart } from './audio.js';

const root = document.querySelector('.console-shell');
const els = {
  remaining: document.querySelector('#remaining'),
  floor: document.querySelector('#floor'),
  door: document.querySelector('#door'),
  direction: document.querySelector('#direction'),
  passengers: document.querySelector('#passengers'),
  power: document.querySelector('#power'),
  powerText: document.querySelector('#powerText'),
  stability: document.querySelector('#stability'),
  stabilityText: document.querySelector('#stabilityText'),
  anomalyLevel: document.querySelector('#anomalyLevel'),
  reviveCount: document.querySelector('#reviveCount'),
  adHintsCount: document.querySelector('#adHintsCount'),
  hiddenLogsCount: document.querySelector('#hiddenLogsCount'),
  fakeEndingOverlay: document.querySelector('#fakeEndingOverlay'),
  fakeEndingText: document.querySelector('#fakeEndingText'),
  fakeEndingTruth: document.querySelector('#fakeEndingTruth'),
  fakeEndingTruthBtn: document.querySelector('#fakeEndingTruthBtn'),
  fakeEndingRestartBtn: document.querySelector('#fakeEndingRestartBtn'),
  monitor: document.querySelector('#monitor'),
  actions: document.querySelector('#actions'),
  logs: document.querySelector('#logs'),
  forceAnomaly: document.querySelector('#forceAnomaly'),
  overlay: document.querySelector('#failureOverlay'),
  failureReason: document.querySelector('#failureReason'),
  adHint: document.querySelector('#adHint'),
  reviveButton: document.querySelector('#reviveButton'),
  restartButton: document.querySelector('#restartButton'),
};

let state = createInitialState();
let nextAnomalyAt = CONFIG.anomaly.firstTriggerAt;
let timer = null;
let lastTone = 'normal';
let crashPlayed = false;

function labelDoor(value) {
  return value === 'open' ? '开启' : '关闭';
}

function labelDirection(value) {
  return { up: '上行', down: '下行', idle: '待机' }[value] ?? value;
}

function renderActions() {
  els.actions.replaceChildren();
  const lockedCount = state.hiddenLogs.filter(h => h.locked).length;
  for (const action of AVAILABLE_ACTIONS) {
    // 解码加密记录按钮只在有锁定日志时显示
    if (action.id === 'unlockHiddenLog' && lockedCount === 0) continue;
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = action.id === 'unlockHiddenLog'
      ? `${action.label} (${lockedCount})`
      : action.label;
    button.dataset.action = action.id;
    button.addEventListener('click', () => dispatchAction(action.id));
    els.actions.append(button);
  }
}

function render() {
  root.dataset.tone = getToneForState(state);
  els.remaining.textContent = Math.ceil(state.remaining);
  els.floor.textContent = state.floor;
  els.door.textContent = labelDoor(state.door);
  els.direction.textContent = labelDirection(state.direction);
  els.passengers.textContent = state.passengers;
  els.power.value = state.power;
  els.powerText.textContent = Math.round(state.power);
  els.stability.value = state.stability;
  els.stabilityText.textContent = Math.round(state.stability);
  els.anomalyLevel.textContent = state.anomalyLevel;
  els.reviveCount.textContent = state.adRevivesUsed;

  // 隐藏日志统计
  const lockedCount = state.hiddenLogs.filter(h => h.locked).length;
  const unlockedCount = state.hiddenLogs.filter(h => !h.locked).length;
  if (els.hiddenLogsCount) els.hiddenLogsCount.textContent = lockedCount;
  if (els.adHintsCount) els.adHintsCount.textContent = state.adHintsUsed;

  // 显示已解锁的隐藏日志内容
  const unlockedHidden = state.hiddenLogs.filter(h => !h.locked);
  if (unlockedHidden.length > 0) {
    const last = unlockedHidden[unlockedHidden.length - 1];
    els.monitor.textContent = `[解码记录] ${last.title}\n${last.content}`;
  } else {
    els.monitor.textContent = state.monitor;
  }

  els.logs.replaceChildren();
  for (const line of state.logs.slice(-CONFIG.logs.displayLines)) {
    const li = document.createElement('li');
    li.className = line.type;
    li.textContent = line.text;
    els.logs.append(li);
  }
  els.logs.scrollTop = els.logs.scrollHeight;

  if (state.gameOver) {
    if (state.fakeEndingTriggered) {
      // 假结局
      els.overlay.hidden = true;
      els.fakeEndingOverlay.hidden = false;
      const threshold = CONFIG.fakeEnding.consecutiveFailuresThreshold;
      els.fakeEndingText.textContent =
        `系统检测到操作员第 ${state.consecutiveFailures} 次系统崩溃。\n` +
        `根据《异常控制员守则》第 7 条，您已被标记为"异常关联人员"。\n` +
        `前 ${threshold - 1} 次记录已被永久删除。\n` +
        `建议您立即离开控制台并联系安保部门。`;
      if (state.fakeEndingUnlocked) {
        els.fakeEndingTruth.textContent =
          '这不是第一次，也不会是最后一次。\n' +
          '这座建筑的异常系统从未被修复。\n' +
          '每一任值班员最后都变成了「异常事件」本身。\n' +
          '系统日志中关于「乘客」的记载——都是前任值班员的热源信号。\n' +
          '你现在坐的位置，就是上一任值班员被发现的地方。';
        els.fakeEndingTruthBtn.hidden = true;
      } else {
        els.fakeEndingTruth.textContent = '[???] 观看广告揭示真相。';
        els.fakeEndingTruthBtn.hidden = false;
      }
    } else {
      // 正常失败
      els.fakeEndingOverlay.hidden = true;
      els.overlay.hidden = false;
      els.failureReason.textContent = summarizeFailure(state);
      els.adHint.textContent = state.lastAdHint
        ? `广告提示：${state.lastAdHint}`
        : '广告提示：先关门，再重启系统，避免连续移动。';
    }
  } else {
    els.overlay.hidden = true;
    els.fakeEndingOverlay.hidden = true;
  }
}

function dispatchAction(actionId) {
  playClick();
  const result = performAction(state, actionId);
  state = result.state;
  if (result.ok) {
    playSuccess();
  } else {
    playFail();
  }
  render();
}

function triggerAnomaly() {
  if (state.gameOver) return;
  const event = pickNextAnomaly(state);
  const result = applyAnomaly(state, event.id);
  state = result.state;
  playAnomaly();
  const cd = CONFIG.anomaly;
  nextAnomalyAt = state.elapsed + cd.cooldownMin + Math.floor(Math.random() * (cd.cooldownMax - cd.cooldownMin + 1));
  render();
}

function loop() {
  if (state.gameOver) {
    if (!crashPlayed) {
      playCrash();
      crashPlayed = true;
    }
    render();
    return;
  }
  crashPlayed = false;
  state = tickState(state, 1);

  // 成功值守 → 重置连续失败计数
  if (state.gameOver && state.remaining <= 0) {
    state = structuredClone(state);
    state.consecutiveFailures = 0;
    state = appendLog(state, 'success', '值守完成。连续失败计数已重置。');
    render();
    return;
  }

  // 检测失败 → 递增连续失败计数
  if (state.gameOver) {
    state = structuredClone(state);
    state.consecutiveFailures += 1;
    const fe = CONFIG.fakeEnding;
    if (state.consecutiveFailures >= fe.consecutiveFailuresThreshold && !state.fakeEndingTriggered) {
      state.fakeEndingTriggered = true;
      state.fakeEndingUnlocked = false;
    }
  }
  // Save a snapshot on interval for ad-revive rollback
  const ar = CONFIG.adRevive;
  if (state.elapsed > 0 && state.elapsed % ar.snapshotInterval === 0 && state.snapshots.length < ar.maxSnapshots) {
    state = saveSnapshot(state);
  }
  if (!state.gameOver && state.elapsed >= nextAnomalyAt) triggerAnomaly();
  // Play warning sound on tone transitions to critical/danger
  const tone = getToneForState(state);
  if (tone === 'danger' || tone === 'critical') {
    if (lastTone !== tone) playWarning();
  }
  lastTone = tone;
  render();
}

function restart() {
  state = createInitialState();
  nextAnomalyAt = 7;
  render();
}

els.forceAnomaly.addEventListener('click', triggerAnomaly);
els.reviveButton.addEventListener('click', () => {
  playRevive();
  state = reviveFromAd(state);
  nextAnomalyAt = state.elapsed + 8;
  render();
});
els.restartButton.addEventListener('click', () => {
  playRestart();
  restart();
});

// 假结局按钮
els.fakeEndingTruthBtn.addEventListener('click', () => {
  playRevive();
  state = structuredClone(state);
  state.fakeEndingUnlocked = true;
  render();
});
els.fakeEndingRestartBtn.addEventListener('click', () => {
  playRestart();
  restart();
});

renderActions();
render();
timer = window.setInterval(loop, 1000);
window.addEventListener('beforeunload', () => window.clearInterval(timer));
