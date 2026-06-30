import { AVAILABLE_ACTIONS, performAction } from './actions.js';
import { applyAnomaly, pickNextAnomaly } from './events.js';
import { getToneForState, summarizeFailure } from './feedback.js';
import { createInitialState, reviveFromAd, saveSnapshot, tickState } from './state.js';

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
let nextAnomalyAt = 12;
let timer = null;

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
  for (const line of state.logs.slice(-18)) {
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
  const result = performAction(state, actionId);
  state = result.state;
  render();
}

function triggerAnomaly() {
  if (state.gameOver) return;
  const event = pickNextAnomaly(state);
  const result = applyAnomaly(state, event.id);
  state = result.state;
  nextAnomalyAt = state.elapsed + 13 + Math.floor(Math.random() * 6);
  render();
}

function loop() {
  if (state.gameOver) {
    render();
    return;
  }
  state = tickState(state, 1);
  // Save a snapshot every 10 seconds for ad-revive rollback
  if (state.elapsed > 0 && state.elapsed % 10 === 0 && state.snapshots.length < 12) {
    state = saveSnapshot(state);
  }
  if (!state.gameOver && state.elapsed >= nextAnomalyAt) triggerAnomaly();
  render();
}

function restart() {
  state = createInitialState();
  nextAnomalyAt = 7;
  render();
}

els.forceAnomaly.addEventListener('click', triggerAnomaly);
els.reviveButton.addEventListener('click', () => {
  state = reviveFromAd(state);
  nextAnomalyAt = state.elapsed + 8;
  render();
});
els.restartButton.addEventListener('click', restart);

renderActions();
render();
timer = window.setInterval(loop, 1000);
window.addEventListener('beforeunload', () => window.clearInterval(timer));
