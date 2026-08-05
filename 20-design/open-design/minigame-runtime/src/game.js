import { getAvailableActions, performAction } from './actions.js';
import { applyAnomaly, pickNextAnomaly } from './events.js';
import { getToneForState, summarizeFailure } from './feedback.js';
import { recordFailure, recordSuccessfulShift, reviveFromAd, saveSnapshot, tickState } from './state.js';
import CONFIG from './gameConfig.js';
import { playClick, playSuccess, playFail, playAnomaly, playWarning, playCrash, playRevive, playRestart } from './audio.js';
import { t, actionLabel, getSkin, getAnomalies } from './skinManager.js';
import { createRewardedAd } from '../platform/platform.js';
import { getDecodedMonitorText, getDirectionLabel, getDomLabels, getDoorLabel } from './uiLabels.js';
import { loadArchive, commitSessionToArchive, getArchiveSkinProgress } from './archive.js';
import { trackEvent } from './analytics.js';
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
  cctvGif: document.querySelector('[data-cctv-gif]'),
  monitorCaption: document.querySelector('#monitorCaption'),
  monitorFloor: document.querySelector('#monitorFloor'),
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
  openArchiveBtn: document.querySelector('#openArchiveBtn'),
  archiveOverlay: document.querySelector('#archiveOverlay'),
  archiveStats: document.querySelector('#archiveStats'),
  archiveAnomalyList: document.querySelector('#archiveAnomalyList'),
  closeArchiveBtn: document.querySelector('#closeArchiveBtn'),
  overlay: document.querySelector('#failureOverlay'),
  failureReason: document.querySelector('#failureReason'),
  failureMetrics: document.querySelector('#failureMetrics'),
  postRunSummary: document.querySelector('#postRunSummary'),
  adHint: document.querySelector('#adHint'),
  reviveButton: document.querySelector('#reviveButton'),
  restartButton: document.querySelector('#restartButton'),
  remainingLabel: document.querySelector('#remainingLabel'),
  systemState: document.querySelector('#systemState'),
  powerQuick: document.querySelector('#powerQuick'),
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
let fakeEndingTracked = false;

function analyticsPayload(extra = {}) {
  return {
    skinId: getSkin().meta?.id,
    elapsed: state.elapsed,
    remaining: state.remaining,
    anomalyLevel: state.anomalyLevel,
    ...extra,
  };
}

function ensureTimer() {
  if (timer) return;
  if (els.startOverlay) els.startOverlay.hidden = true;
  timer = window.setInterval(loop, 1000);
  trackEvent('game_start', analyticsPayload());
}

function bindPress(element, handler) {
  if (!element) return;
  let handledAt = 0;
  const run = (event) => {
    event?.preventDefault?.();
    const now = Date.now();
    if (now - handledAt < 350) return;
    handledAt = now;
    handler(event);
  };
  element.addEventListener('click', run);
  element.addEventListener('touchend', run, { passive: false });
  element.addEventListener('pointerup', run);
}

const showReviveAd = createRewardedAd(CONFIG.adUnits.revive, {
  onReward: () => {
    trackEvent('revive_ad_reward', analyticsPayload({ adUnitId: CONFIG.adUnits.revive }));
    playRevive();
    state = reviveFromAd(state);
    nextAnomalyAt = scheduleNextAnomalyAfterRevive(state.elapsed);
    render();
  },
});
const showDecodeAd = createRewardedAd(CONFIG.adUnits.decode, {
  onReward: () => {
    const before = state.adHintsUsed;
    runAction('unlockHiddenLog');
    if (state.adHintsUsed > before) {
      trackEvent('hidden_log_unlock', analyticsPayload({ adUnitId: CONFIG.adUnits.decode }));
    }
  },
});
const showTruthAd = createRewardedAd(CONFIG.adUnits.truth, {
  onReward: () => {
    playRevive();
    state = structuredClone(state);
    state.fakeEndingUnlocked = true;
    render();
  },
});

const ACTION_ICONS = {
  openDoor: '◀▯▶',
  closeDoor: '▶▯◀',
  moveUp: '▲',
  moveDown: '▼',
  emergencyStop: 'STOP',
  restartSystem: '↻',
  inspectLog: 'LOG',
  unlockHiddenLog: 'DEC',
};

const ACTION_SHORT_LABELS = {
  openDoor: '开门',
  closeDoor: '关门',
  moveUp: '上行',
  moveDown: '下行',
  emergencyStop: '急停',
  restartSystem: '重启',
  inspectLog: '日志',
  unlockHiddenLog: '解码',
};

const CCTV_GIF_ASSETS = {
  elevator: 'assets/generated/cctv-basement-lift-door-open-lite-loop.gif',
  hospital: 'assets/generated/cctv-hospital-ward-native-lite-loop.gif',
  security: 'assets/generated/cctv-security-room-native-lite-loop.gif',
  factory: 'assets/generated/cctv-factory-native-lite-loop.gif',
  subway: 'assets/generated/cctv-subway-platform-native-lite-loop.gif',
  hotel: 'assets/generated/cctv-hotel-lobby-native-lite-loop.gif',
};

function syncCctvBackground(skinId) {
  const asset = CCTV_GIF_ASSETS[skinId] || CCTV_GIF_ASSETS.elevator;
  if (els.cctvGif && !els.cctvGif.src.endsWith(asset)) {
    els.cctvGif.hidden = false;
    els.cctvGif.src = asset;
  }
}


function renderActions() {
  els.actions.replaceChildren();
  const lockedCount = state.hiddenLogs.filter(h => h.locked).length;
  for (const action of getAvailableActions()) {
    // 解码加密记录按钮只在有锁定日志时显示
    if (action.id === 'unlockHiddenLog' && lockedCount === 0) continue;
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.action = action.id;
    button.className = [
      'hardware-key',
      action.id === 'emergencyStop' ? 'danger emergency-stop' : '',
      action.id === 'unlockHiddenLog' ? 'decode-key' : '',
    ].filter(Boolean).join(' ');
    const led = document.createElement('span');
    led.className = 'key-led';
    led.setAttribute('aria-hidden', 'true');
    const keycap = document.createElement('span');
    keycap.className = 'action-keycap';
    const icon = document.createElement('span');
    icon.className = 'action-icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = ACTION_ICONS[action.id] || '●';
    const label = document.createElement('span');
    label.className = 'action-label';
    label.textContent = ACTION_SHORT_LABELS[action.id] || (action.id === 'unlockHiddenLog'
      ? actionLabel(action.id, lockedCount)
      : action.label);
    button.setAttribute('aria-label', action.id === 'unlockHiddenLog'
      ? actionLabel(action.id, lockedCount)
      : action.label);
    keycap.append(icon, label);
    button.append(led, keycap);
    bindPress(button, () => dispatchAction(action.id));
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
  if (els.powerQuick) els.powerQuick.textContent = `PWR ${Math.round(state.power)}`;
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
    if (els.systemState) els.systemState.textContent = signal;
  }
  if (els.monitorThreat) els.monitorThreat.textContent = labels.monitorThreat(state.anomalyLevel);
  // 显示已解锁的隐藏日志内容
  const unlockedHidden = state.hiddenLogs.filter(h => !h.locked);
  const monitorText = unlockedHidden.length > 0
    ? getDecodedMonitorText(unlockedHidden[unlockedHidden.length - 1])
    : state.monitor;
  if (els.monitorCaption) els.monitorCaption.textContent = monitorText;
  else els.monitor.textContent = monitorText;
  if (els.monitorFloor) els.monitorFloor.textContent = state.floor;
  if (els.monitor) {
    els.monitor.dataset.door = state.door;
    els.monitor.dataset.moving = String(state.moving);
    els.monitor.dataset.anomaly = state.anomalyLevel > 0 ? 'active' : 'clear';
    els.monitor.dataset.passengers = state.passengers > 0 ? 'present' : 'missing';
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
      // 局后复盘
      if (els.postRunSummary) {
        const unlockedLogs = state.hiddenLogs.filter(h => !h.locked).length;
        const totalAnomalies = state.anomaliesTriggeredTotal || 0;
        const peakSeverity = state.maxAnomalySeverity || 0;
        const severityLabel = peakSeverity >= 4 ? '致命' : peakSeverity >= 2 ? '高' : peakSeverity > 0 ? '低' : '无';
        const items = [
          ['存活秒数', state.elapsed],
          ['触发异常', totalAnomalies],
          ['最高威胁', `${peakSeverity}（${severityLabel}）`],
          ['解锁日志', unlockedLogs],
          ['复活次数', state.adRevivesUsed || 0],
        ];
        if (state.fakeEndingTriggered) items.push(['假结局', '已触发']);
        els.postRunSummary.replaceChildren(...items.map(([label, value]) => {
          const item = document.createElement('span');
          const labelEl = document.createElement('b');
          const valueEl = document.createElement('strong');
          labelEl.textContent = label;
          valueEl.textContent = value;
          item.append(labelEl, valueEl);
          return item;
        }));
      }
    }
  } else {
    els.overlay.hidden = true;
    els.fakeEndingOverlay.hidden = true;
  }
}

function dispatchAction(actionId) {
  ensureTimer();
  playClick();
  trackEvent('action_click', analyticsPayload({ actionId }));
  if (actionId === 'unlockHiddenLog') {
    trackEvent('hidden_log_ad_start', analyticsPayload({ adUnitId: CONFIG.adUnits.decode }));
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
  trackEvent('anomaly_trigger', analyticsPayload({
    anomalyId: result.event.id,
    severity: result.event.severity,
  }));
  playAnomaly();
  nextAnomalyAt = scheduleNextAnomalyAfterTrigger(state.elapsed);
  render();
}

function loop() {
  if (state.gameOver) {
    if (!crashPlayed) {
      playCrash();
      crashPlayed = true;
      trackEvent('game_over', analyticsPayload({
        reason: summarizeFailure(state).reason,
        anomaliesTriggeredTotal: state.anomaliesTriggeredTotal || 0,
        maxAnomalySeverity: state.maxAnomalySeverity || 0,
      }));
      // 提交本局数据到跨局档案库
      try {
        const ids = state.hiddenLogs?.map(h => h.id?.replace(/_log$/, '')).filter(Boolean) || [];
        const unlockedIds = state.hiddenLogs?.filter(h => !h.locked).map(h => h.id) || [];
        commitSessionToArchive({
          skinId: getSkin().meta?.id,
          anomaliesTriggeredTotal: state.anomaliesTriggeredTotal || 0,
          maxAnomalySeverity: state.maxAnomalySeverity || 0,
          anomalyIds: ids,
          unlockedLogIds: unlockedIds,
        });
        refreshArchiveButton();
      } catch { /* localStorage unavailable — skip */ }
    }
    render();
    return;
  }
  crashPlayed = false;
  fakeEndingTracked = false;
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
    if (state.fakeEndingTriggered && !fakeEndingTracked) {
      fakeEndingTracked = true;
      trackEvent('fake_ending_trigger', analyticsPayload({
        fakeEndingCount: state.fakeEndingCount,
      }));
    }
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
  fakeEndingTracked = false;
  render();
  refreshArchiveButton();
}

function refreshArchiveButton() {
  if (!els.openArchiveBtn) return;
  const archive = loadArchive();
  els.openArchiveBtn.hidden = archive.sessionsPlayed === 0;
}

function renderArchive() {
  const archive = loadArchive();
  const skinProgress = getArchiveSkinProgress(archive, getSkin().meta?.id, getAnomalies());
  if (els.archiveStats) {
    const ids = Object.keys(archive.encounteredAnomalies).length;
    const logs = Object.keys(archive.unlockedLogs).length;
    const items = [
      ['总场次', archive.sessionsPlayed],
      ['遭遇异常', ids],
      ['解锁日志', logs],
      ['总异常数', archive.totalAnomaliesTriggered],
      ['最高威胁', archive.highestSeverity],
      ['皮肤进度', `${skinProgress.encounteredCount}/${skinProgress.totalAnomalies}`],
      ['日志解锁', `${skinProgress.unlockedLogsCount}/${skinProgress.totalAnomalies}`],
    ];
    els.archiveStats.replaceChildren(...items.map(([label, value]) => {
      const item = document.createElement('span');
      const labelEl = document.createElement('b');
      const valueEl = document.createElement('strong');
      labelEl.textContent = label;
      valueEl.textContent = value;
      item.append(labelEl, valueEl);
      return item;
    }));
  }
  if (els.archiveAnomalyList) {
    const anomalies = getAnomalies();
    els.archiveAnomalyList.replaceChildren(...Object.entries(archive.encounteredAnomalies)
      .sort((a, b) => b[1] - a[1])
      .map(([id, count]) => {
        const def = anomalies.find(a => a.id === id);
        const item = document.createElement('div');
        item.className = 'anomaly-entry';
        const name = document.createElement('span');
        name.textContent = def?.title || id;
        const badge = document.createElement('strong');
        badge.textContent = `×${count}`;
        item.append(name, badge);
        return item;
      }));
  }
}

function applyDomLabels() {
  const labels = getDomLabels();
  els.remainingLabel.textContent = 'TIMER';
  els.statusPanelTitle.textContent = 'STATUS';
  els.monitorPanelTitle.textContent = 'CCTV';
  els.actionPanelTitle.textContent = 'CTRL';
  els.logPanelTitle.textContent = 'LOG';
  els.failureTitle.textContent = labels.failureTitle;
  els.forceAnomaly.textContent = 'ANOM';
  els.forceAnomaly.setAttribute('aria-label', labels.forceAnomaly);
  els.reviveButton.textContent = labels.revive;
  els.restartButton.textContent = labels.restart;
  els.fakeEndingTruthBtn.textContent = labels.revealTruth;
  els.fakeEndingRestartBtn.textContent = labels.restart;
  if (els.fakeEndingEyebrow) els.fakeEndingEyebrow.textContent = t('fakeEnding.eyebrow');
  if (els.fakeEndingTitle) els.fakeEndingTitle.textContent = t('fakeEnding.title');
  if (els.startTitle) els.startTitle.textContent = '接管电梯';
  if (els.startCopy) els.startCopy.textContent = '看监控，按键救场。';
  if (els.startButton) els.startButton.textContent = 'OVERRIDE';
  if (els.startChecklist) {
    const compactMissions = ['60s', 'CCTV', 'CONTROL'];
    els.startChecklist.replaceChildren(...compactMissions.map((item) => {
      const chip = document.createElement('span');
      chip.textContent = item;
      return chip;
    }));
  }
  if (els.startFailureRules) {
    const compactRisks = ['POWER', 'STABILITY', 'ANOMALY'];
    els.startFailureRules.replaceChildren(...compactRisks.map((item) => {
      const chip = document.createElement('span');
      chip.textContent = item;
      return chip;
    }));
  }
  els.floorLabel.textContent = 'F';
  els.doorLabel.textContent = 'DOOR';
  els.directionLabel.textContent = 'DIR';
  els.passengersLabel.textContent = 'PAX';
  els.powerLabel.textContent = 'PWR';
  els.stabilityLabel.textContent = 'STB';
  els.anomalyLevelLabel.textContent = 'ANOM';
  els.reviveCountLabel.textContent = 'REV';
  els.adHintsCountLabel.textContent = 'DEC';
  els.hiddenLogsCountLabel.textContent = 'LOCK';
}

applyDomLabels();
refreshArchiveButton();
bindPress(els.startButton, () => {
  playClick();
  ensureTimer();
});
bindPress(els.forceAnomaly, triggerAnomaly);
bindPress(els.reviveButton, () => {
  trackEvent('revive_ad_start', analyticsPayload({ adUnitId: CONFIG.adUnits.revive }));
  showReviveAd();
});
bindPress(els.restartButton, () => {
  playRestart();
  restart();
});

// 假结局按钮
bindPress(els.fakeEndingTruthBtn, () => {
  showTruthAd();
});
bindPress(els.fakeEndingRestartBtn, () => {
  playRestart();
  restart();
});

// 档案库
bindPress(els.openArchiveBtn, () => {
  renderArchive();
  els.archiveOverlay.hidden = false;
});
bindPress(els.closeArchiveBtn, () => {
  els.archiveOverlay.hidden = true;
});

// 从皮肤设置标题和副标题
const meta = getSkin().meta;
if (meta) {
  const titleEl = document.querySelector('#gameTitle');
  const subEl = document.querySelector('#gameSubtitle');
  if (titleEl) titleEl.textContent = meta.name;
  if (subEl) subEl.textContent = meta.subtitle;
  root.dataset.skin = meta.id;
  syncCctvBackground(meta.id);
}

render();
window.addEventListener('beforeunload', () => window.clearInterval(timer));
