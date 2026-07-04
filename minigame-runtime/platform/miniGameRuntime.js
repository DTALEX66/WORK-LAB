/**
 * miniGameRuntime.js — 微信/抖音小游戏 Canvas 运行时入口
 *
 * 不依赖 DOM/window。只使用小游戏全局 API（wx/tt）或标准全局函数。
 */

import CONFIG from '../src/gameConfig.js';
import { performAction } from '../src/actions.js';
import { applyAnomaly, pickNextAnomaly } from '../src/events.js';
import {
  createInitialState,
  reviveFromAd,
  saveSnapshot,
  tickState,
  recordFailure,
  recordSuccessfulShift,
} from '../src/state.js';
import {
  createRuntimeSession,
  scheduleNextAnomalyAfterRevive,
  scheduleNextAnomalyAfterTrigger,
} from '../src/runtimeSession.js';
import { init as initCanvasRenderer, onCanvasClick, render } from './canvasRenderer.js';

function getHostApi() {
  if (typeof wx !== 'undefined' && wx) return wx;
  if (typeof tt !== 'undefined' && tt) return tt;
  return null;
}

function getNow() {
  return Date.now();
}

function nextFrame(api, callback) {
  if (api && typeof api.requestAnimationFrame === 'function') {
    return api.requestAnimationFrame(callback);
  }
  if (typeof requestAnimationFrame === 'function') {
    return requestAnimationFrame(callback);
  }
  return setTimeout(callback, 16);
}

function getSystemInfo(api) {
  if (api && typeof api.getSystemInfoSync === 'function') {
    return api.getSystemInfoSync();
  }
  return { windowWidth: 750, windowHeight: 1334, pixelRatio: 1 };
}

function createRewardedAd(api, adUnitId, onReward) {
  if (!api || typeof api.createRewardedVideoAd !== 'function' || !adUnitId) {
    return () => Promise.resolve().then(onReward);
  }

  const ad = api.createRewardedVideoAd({ adUnitId });
  let granted = false;
  ad.onClose?.((res) => {
    if (res && res.isEnded && !granted) {
      granted = true;
      onReward?.();
    }
  });
  ad.onError?.(() => {
    if (!granted) {
      granted = true;
      onReward?.();
    }
  });

  return () => ad.show()
    .catch(() => ad.load?.().then(() => ad.show()))
    .catch(() => {
      if (!granted) {
        granted = true;
        onReward?.();
      }
    });
}

export function startMiniGame() {
  const api = getHostApi();
  if (!api || typeof api.createCanvas !== 'function') {
    throw new Error('[MINIGAME] mini-game runtime requires wx.createCanvas() or tt.createCanvas()');
  }

  const canvas = api.createCanvas();
  const info = getSystemInfo(api);
  const dims = initCanvasRenderer(canvas);
  let session = createRuntimeSession();
  let state = session.state;
  let nextAnomalyAt = session.nextAnomalyAt;
  let lastTickAt = getNow();
  let lastSnapshotAt = 0;
  let failureRecorded = false;

  const reviveAd = createRewardedAd(api, CONFIG.adUnits?.revive, () => {
    state = reviveFromAd(state);
    nextAnomalyAt = scheduleNextAnomalyAfterRevive(state.elapsed);
    failureRecorded = false;
  });

  const truthAd = createRewardedAd(api, CONFIG.adUnits?.truth, () => {
    state = { ...state, fakeEndingUnlocked: true, fakeEndingTruth: state.lastAdHint || '' };
  });

  function restart() {
    session = createRuntimeSession();
    state = session.state;
    nextAnomalyAt = session.nextAnomalyAt;
    lastSnapshotAt = 0;
    failureRecorded = false;
  }

  function forceAnomaly() {
    if (state.gameOver) return;
    const event = pickNextAnomaly(state);
    const result = applyAnomaly(state, event.id);
    state = result.state;
    nextAnomalyAt = scheduleNextAnomalyAfterTrigger(state.elapsed);
  }

  function handleAction(actionId) {
    if (state.gameOver) return;
    const result = performAction(state, actionId);
    state = result.state;
  }

  function handleAd(kind) {
    if (kind === 'truth') {
      truthAd();
    } else {
      reviveAd();
    }
  }

  function onTouch(e) {
    const touch = e.touches?.[0] || e.changedTouches?.[0] || e;
    const screenW = info.windowWidth || 750;
    const screenH = info.windowHeight || 1334;
    const x = (touch.clientX ?? touch.x ?? 0) * (750 / screenW);
    const y = (touch.clientY ?? touch.y ?? 0) * (dims.height / screenH);
    onCanvasClick(x, y, state, {
      onAction: handleAction,
      onForceAnomaly: forceAnomaly,
      onAdRevive: handleAd,
      onRestart: restart,
    });
  }

  api.onTouchStart?.(onTouch);

  function update() {
    const now = getNow();
    const delta = Math.floor((now - lastTickAt) / 1000);
    if (delta > 0) {
      lastTickAt += delta * 1000;
      if (!state.gameOver) {
        for (let i = 0; i < delta; i += 1) {
          state = tickState(state, 1);
          if (!state.gameOver && state.elapsed - lastSnapshotAt >= CONFIG.adRevive.snapshotInterval) {
            state = saveSnapshot(state);
            lastSnapshotAt = state.elapsed;
          }
          if (!state.gameOver && state.elapsed >= nextAnomalyAt) {
            const event = pickNextAnomaly(state);
            const result = applyAnomaly(state, event.id);
            state = result.state;
            nextAnomalyAt = scheduleNextAnomalyAfterTrigger(state.elapsed);
          }
        }
      }
      if (state.gameOver && !failureRecorded) {
        state = state.remaining <= 0 ? recordSuccessfulShift(state) : recordFailure(state);
        failureRecorded = true;
      }
    }

    render(state);
    nextFrame(api, update);
  }

  render(state);
  nextFrame(api, update);
  return { canvas, getState: () => state, restart };
}
