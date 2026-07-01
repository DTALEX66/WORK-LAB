import { getAvailableActions, performAction } from './actions.js';
import { applyAnomaly, pickNextAnomaly } from './events.js';
import { getToneForState, summarizeFailure } from './feedback.js';
import { recordFailure, recordSuccessfulShift, reviveFromAd, saveSnapshot, tickState } from './state.js';
import CONFIG from './gameConfig.js';
import { playClick, playSuccess, playFail, playAnomaly, playWarning, playCrash, playRevive, playRestart } from './audio.js';
import { t, actionLabel, getSkin } from './skinManager.js';
import { createRewardedAd } from '../platform/platform.js';
import { getDecodedMonitorText, getDirectionLabel, getDomLabels, getDoorLabel } from './uiLabels.js';
import {
  createRuntimeSession,
  restartRuntimeSession,
  scheduleNextAnomalyAfterRevive,
  scheduleNextAnomalyAfterTrigger,
} from './runtimeSession.js';

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
  fakeEndingEyebrow: document.querySelector('#fakeEndingEyebrow'),
  fakeEndingTitle: document.querySelector('#fakeEndingTitle'),
  fakeEndingText: document.querySelector('#fakeEndingText'),
  fakeEndingTruth: document.querySelector('#fakeEndingTruth'),
  fakeEndingTruthBtn: document.querySelector('#fakeEndingTruthBtn'),
  fakeEndingRestartBtn: document.querySelector('#fakeEndingRestartBtn'),
  monitor: document.querySelector('#monitor'),
  monitorSignal: document.querySelector('#monitorSignal'),
  monitorThreat: document.querySelector('#monitorThreat'),
  actions: document.querySelector('#actions'),
  logs: document.querySelector('#logs'),
  forceAnomaly: document.querySelector('#forceAnomaly'),
  startOverlay: document.querySelector('#startOverlay'),
  startTitle: document.querySelector('#startTitle'),
  startCopy: document.querySelector('#startCopy'),
  startChecklist: document.querySelector('#startChecklist'),
  startFailureRules: document.querySelector('#startFailureRules'),
  startButton: document.querySelector('#startButton'),
  overlay: document.querySelector('#failureOverlay'),
  failureReason: document.querySelector('#failureReason'),
  failureMetrics: document.querySelector('#failureMetrics'),
  adHint: document.querySelector('#adHint'),
  reviveButton: document.querySelector('#reviveButton'),
  restartButton: document.querySelector('#restartButton'),
  remainingLabel: document.querySelector('#remainingLabel'),
  statusPanelTitle: document.querySelector('#statusPanelTitle'),
  monitorPanelTitle: document.querySelector('#monitorPanelTitle'),
  actionPanelTitle: document.querySelector('#actionPanelTitle'),
  logPanelTitle: document.querySelector('#logPanelTitle'),
  failureTitle: document.querySelector('#failureTitle'),
  floorLabel: document.querySelector('#floorLabel'),
  doorLabel: document.querySelector('#doorLabel'),
  directionLabel: document.querySelector('#directionLabel'),
  passengersLabel: document.querySelector('#passengersLabel'),
  powerLabel: document.querySelector('#powerLabel'),
  stabilityLabel: document.querySelector('#stabilityLabel'),
  anomalyLevelLabel: document.querySelector('#anomalyLevelLabel'),
  reviveCountLabel: document.querySelector('#reviveCountLabel'),
  adHintsCountLabel: document.querySelector('#adHintsCountLabel'),
  hiddenLogsCountLabel: document.querySelector('#hiddenLogsCountLabel'),
};

let session = createRuntimeSession();
let state = session.state;
let nextAnomalyAt = session.nextAnomalyAt;
let timer = null;
let lastTone = 'normal';
let crashPlayed = false;

function ensureTimer() {
  if (timer) return;
  if (els.startOverlay) els.startOverlay.hidden = true;
  timer = window.setInterval(loop, 1000);
}

const showReviveAd = createRewardedAd(CONFIG.adUnits.revive, {
  onReward: () => {
    playRevive();
    state = reviveFromAd(state);
    nextAnomalyAt = scheduleNextAnomalyAfterRevive(state.elapsed);
    render();
  },
});
const showDecodeAd = createRewardedAd(CONFIG.adUnits.decode, {
  onReward: () => runAction('unlockHiddenLog'),
});
const showTruthAd = createRewardedAd(CONFIG.adUnits.truth, {
  onReward: () => {
    playRevive();
    state = structuredClone(state);
    state.fakeEndingUnlocked = true;
    render();
  },
});


function renderActions() {
  els.actions.replaceChildren();
  const lockedCount = state.hiddenLogs.filter(h => h.locked).length;
  for (const action of getAvailableActions()) {
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
  const labels = getDomLabels();
  renderActions();
  root.dataset.tone = getToneForState(state);
  els.remaining.textContent = Math.ceil(state.remaining);
  els.floor.textContent = state.floor;
  els.door.textContent = getDoorLabel(state.door);
  els.direction.textContent = getDirectionLabel(state.direction);
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
  const tone = getToneForState(state);
  if (els.monitorSignal) {
    const signal = tone === 'danger' || tone === 'critical'
      ? labels.monitorSignal.corrupted
      : state.anomalyLevel > 0 || tone === 'warn'
        ? labels.monitorSignal.unstable
        : labels.monitorSignal.stable;
    els.monitorSignal.textContent = signal;
  }
  if (els.monitorThreat) els.monitorThreat.textContent = labels.monitorThreat(state.anomalyLevel);

  // 显示已解锁的隐藏日志内容
  const unlockedHidden = state.hiddenLogs.filter(h => !h.locked);
  if (unlockedHidden.length > 0) {
    const last = unlockedHidden[unlockedHidden.length - 1];
    els.monitor.textContent = getDecodedMonitorText(last);
  } else {
    els.monitor.textContent = state.monitor;
  }

  els.logs.replaceChildren();
  for (const line of state.logs.slice(-CONFIG.logs.displayLines)) {
    const li = document.createElement('li');
    li.className = [line.type, line.priority ? `log-priority-${line.priority}` : 'log-priority-normal'].join(' ');
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
        count: state.fakeEndingCount || CONFIG.fakeEnding.consecutiveFailuresThreshold,
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
      if (els.failureMetrics) {
        const metrics = labels.failureMetrics.map(({ key, label }) => {
          const value = key === 'remaining' ? Math.ceil(state.remaining) : Math.round(state[key]);
          return [label, value];
        });
        els.failureMetrics.replaceChildren(...metrics.map(([label, value]) => {
          const item = document.createElement('span');
          const labelEl = document.createElement('b');
          const valueEl = document.createElement('strong');
          labelEl.textContent = label;
          valueEl.textContent = value;
          item.append(labelEl, valueEl);
          return item;
        }));
      }
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
  ensureTimer();
  playClick();
  if (actionId === 'unlockHiddenLog') {
    showDecodeAd();
    return;
  }
  runAction(actionId);
}

function runAction(actionId) {
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
  ensureTimer();
  const picked = pickNextAnomaly(state);
  const result = applyAnomaly(state, picked.id);
  state = result.state;
  playAnomaly();
  nextAnomalyAt = scheduleNextAnomalyAfterTrigger(state.elapsed);
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
    state = recordSuccessfulShift(state);
    render();
    return;
  }

  // 检测失败 → 递增连续失败计数
  if (state.gameOver) {
    state = recordFailure(state);
  }
  // Save a snapshot on interval for ad-revive rollback
  const ar = CONFIG.adRevive;
  if (state.elapsed > 0 && state.elapsed % ar.snapshotInterval === 0) {
    state = saveSnapshot(state);
  }
  if (!state.gameOver && state.elapsed >= nextAnomalyAt) triggerAnomaly();
  // Play warning sound on tone transitions to critical/danger
  const currentTone = getToneForState(state);
  if (currentTone === 'danger' || currentTone === 'critical') {
    if (lastTone !== currentTone) playWarning();
  }
  lastTone = currentTone;
  render();
}

function restart() {
  if (timer) {
    window.clearInterval(timer);
    timer = null;
  }
  if (els.startOverlay) els.startOverlay.hidden = false;
  session = restartRuntimeSession();
  state = session.state;
  nextAnomalyAt = session.nextAnomalyAt;
  render();
}

function applyDomLabels() {
  const labels = getDomLabels();
  els.remainingLabel.textContent = labels.countdown;
  els.statusPanelTitle.textContent = labels.statusPanel;
  els.monitorPanelTitle.textContent = labels.monitorPanel;
  els.actionPanelTitle.textContent = labels.actionPanel;
  els.logPanelTitle.textContent = labels.logPanel;
  els.failureTitle.textContent = labels.failureTitle;
  els.forceAnomaly.textContent = labels.forceAnomaly;
  els.reviveButton.textContent = labels.revive;
  els.restartButton.textContent = labels.restart;
  els.fakeEndingTruthBtn.textContent = labels.revealTruth;
  els.fakeEndingRestartBtn.textContent = labels.restart;
  if (els.fakeEndingEyebrow) els.fakeEndingEyebrow.textContent = t('fakeEnding.eyebrow');
  if (els.fakeEndingTitle) els.fakeEndingTitle.textContent = t('fakeEnding.title');
  if (els.startTitle) els.startTitle.textContent = labels.start.title;
  if (els.startCopy) els.startCopy.textContent = labels.start.copy;
  if (els.startButton) els.startButton.textContent = labels.start.button;
  if (els.startChecklist) {
    els.startChecklist.replaceChildren(...labels.start.checklist.map((item) => {
      const li = document.createElement('li');
      li.textContent = item;
      return li;
    }));
  }
  if (els.startFailureRules) {
    els.startFailureRules.replaceChildren(
      Object.assign(document.createElement('span'), { textContent: labels.start.failureRulesTitle }),
      ...labels.start.failureRules.map((item) => {
        const badge = document.createElement('b');
        badge.textContent = item;
        return badge;
      }),
    );
  }
  els.floorLabel.textContent = labels.status.floor;
  els.doorLabel.textContent = labels.status.door;
  els.directionLabel.textContent = labels.status.direction;
  els.passengersLabel.textContent = labels.status.passengers;
  els.powerLabel.textContent = labels.status.power;
  els.stabilityLabel.textContent = labels.status.stability;
  els.anomalyLevelLabel.textContent = labels.status.anomalyLevel;
  els.reviveCountLabel.textContent = labels.status.reviveCount;
  els.adHintsCountLabel.textContent = labels.status.adHintsCount;
  els.hiddenLogsCountLabel.textContent = labels.status.hiddenLogsCount;
}

applyDomLabels();
els.startButton?.addEventListener('click', () => {
  playClick();
  ensureTimer();
});
els.forceAnomaly.addEventListener('click', triggerAnomaly);
els.reviveButton.addEventListener('click', () => {
  showReviveAd();
});
els.restartButton.addEventListener('click', () => {
  playRestart();
  restart();
});

// 假结局按钮
els.fakeEndingTruthBtn.addEventListener('click', () => {
  showTruthAd();
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
window.addEventListener('beforeunload', () => window.clearInterval(timer));
