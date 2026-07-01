import { AVAILABLE_ACTIONS, performAction } from './actions.js';
import { applyAnomaly, pickNextAnomaly } from './events.js';
import { getToneForState, summarizeFailure } from './feedback.js';
import { createInitialState, appendLog, reviveFromAd, saveSnapshot, tickState } from './state.js';
import CONFIG from './gameConfig.js';
import { playClick, playSuccess, playFail, playAnomaly, playWarning, playCrash, playRevive, playRestart } from './audio.js';
import { t, actionLabel, getSkin } from './skinManager.js';

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
  const labels = getSkin().doorLabels || { open: '开启', closed: '关闭' };
  return labels[value] || value;
}

function labelDirection(value) {
  const labels = getSkin().directionLabels || { up: '上行', down: '下行', idle: '待机' };
  return labels[value] || value;
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
      ? actionLabel(action.id, lockedCount)
      : action.label;
    button.dataset.action = action.id;
    button.addEventListener('click', () => dispatchAction(action.id));
    els.actions.append(button);
  }
}

function render() {
  renderActions();
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
      els.fakeEndingText.textContent = t('fakeEnding.text', {
        count: state.consecutiveFailures,
        threshold: threshold,
      });
      if (state.fakeEndingUnlocked) {
        els.fakeEndingTruth.textContent = t('fakeEnding.truthContent');
        els.fakeEndingTruthBtn.hidden = true;
      } else {
        els.fakeEndingTruth.textContent = t('fakeEnding.truthPlaceholder');
        els.fakeEndingTruthBtn.hidden = false;
      }
    } else {
      // 正常失败
      els.fakeEndingOverlay.hidden = true;
      els.overlay.hidden = false;
      els.failureReason.textContent = summarizeFailure(state);
      els.adHint.textContent = state.lastAdHint
        ? t('failure.adHintPrefix', { hint: state.lastAdHint })
        : t('failure.defaultHint');
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
    state = appendLog(state, 'success', t('ui.shiftComplete'));
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

els.forceAnomaly.textContent = t('ui.triggerTest');
els.forceAnomaly.addEventListener('click', triggerAnomaly);
els.reviveButton.textContent = t('ui.viewAd');
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

// 从皮肤设置标题和副标题
const meta = getSkin().meta;
if (meta) {
  const titleEl = document.querySelector('#gameTitle');
  const subEl = document.querySelector('#gameSubtitle');
  if (titleEl) titleEl.textContent = meta.name;
  if (subEl) subEl.textContent = meta.subtitle;
  root.dataset.skin = meta.id;
}

render();
timer = window.setInterval(loop, 1000);
window.addEventListener('beforeunload', () => window.clearInterval(timer));
