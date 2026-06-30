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
  for (const action of AVAILABLE_ACTIONS) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = action.label;
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
  els.monitor.textContent = state.monitor;

  els.logs.replaceChildren();
  for (const line of state.logs.slice(-CONFIG.logs.displayLines)) {
    const li = document.createElement('li');
    li.className = line.type;
    li.textContent = line.text;
    els.logs.append(li);
  }
  els.logs.scrollTop = els.logs.scrollHeight;

  if (state.gameOver) {
    els.failureReason.textContent = summarizeFailure(state);
    els.adHint.textContent = state.lastAdHint ? `广告提示：${state.lastAdHint}` : '广告提示：先关门，再重启系统，避免连续移动。';
    els.overlay.hidden = false;
  } else {
    els.overlay.hidden = true;
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

renderActions();
render();
timer = window.setInterval(loop, 1000);
window.addEventListener('beforeunload', () => window.clearInterval(timer));
