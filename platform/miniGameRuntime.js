/**
 * miniGameRuntime.js — 微信/抖音小游戏 Canvas 运行时入口
 *
 * 不依赖 DOM/window。只使用小游戏全局 API（wx/tt）或标准全局函数。
 */

import CONFIG from '../src/gameConfig.js';
import { expireInspection, openInspection, submitInspection } from '../src/incidentDecision.js';
import { t } from '../src/skinManager.js';
import { performAction } from '../src/actions.js';
import { getAnomalyResolutionAction } from '../src/visualState.js';
import { applyAnomaly, findAnomaly, pickNextAnomaly } from '../src/events.js';
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
  restartRuntimeSession,
  scheduleNextAnomalyAfterRevive,
  scheduleNextAnomalyAfterTrigger,
} from '../src/runtimeSession.js';
import { init, onCanvasClick, render } from './canvasRenderer.js';
import { bindMiniGameLifecycle, checkDouyinSidebar, navigateToDouyinSidebar } from './douyinIntegration.js';
import { createMiniGameAudio } from './miniGameAudio.js';
import { createMiniGameClock } from './miniGameClock.js';
import { createCctvMotionController } from './cctvMotion.js';
import { shouldApplyReward } from '../src/rewardGuard.js';

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
    const info = api.getSystemInfoSync();
    let menuButtonRect = null;
    try { menuButtonRect = api.getMenuButtonBoundingClientRect?.() || null; } catch { /* optional host API */ }
    return { ...info, menuButtonRect };
  }
  return { windowWidth: 750, windowHeight: 1334, pixelRatio: 1, menuButtonRect: null };
}

export function createMiniGameRewardedAd(api, adUnitId, options = {}) {
  const {
    onReward,
    onError,
    onStart,
    onSettled,
    releaseMode = CONFIG.releaseMode,
  } = options;

  if (!api || typeof api.createRewardedVideoAd !== 'function' || !adUnitId) {
    return (context = null) => {
      const error = new Error('[MINIGAME] rewarded ad API or adUnitId unavailable');
      const meta = { attemptId: null, context };
      if (!releaseMode) onReward?.(meta);
      onError?.(error, meta);
      onSettled?.(meta);
      return Promise.resolve();
    };
  }

  let activeAttempt = null;
  let attemptSequence = 0;

  const settle = (attempt, rewarded, error = null) => {
    if (!attempt || attempt.settled) return;
    attempt.settled = true;
    if (activeAttempt === attempt) activeAttempt = null;
    const meta = { attemptId: attempt.id, context: attempt.context };
    try {
      if (rewarded || (!releaseMode && error)) onReward?.(meta);
      if (error) onError?.(error, meta);
    } finally {
      onSettled?.(meta);
      attempt.ad.offClose?.(attempt.closeHandler);
      attempt.ad.offError?.(attempt.errorHandler);
      attempt.ad.destroy?.();
    }
  };

  return (context = null) => {
    if (activeAttempt && !activeAttempt.settled) return Promise.resolve();
    const ad = api.createRewardedVideoAd({ adUnitId });
    const attempt = {
      id: ++attemptSequence,
      context,
      settled: false,
      ad,
      closeHandler: null,
      errorHandler: null,
    };
    attempt.closeHandler = (res) => settle(attempt, Boolean(res?.isEnded));
    attempt.errorHandler = (error) => settle(attempt, false, error);
    activeAttempt = attempt;
    onStart?.({ attemptId: attempt.id, context: attempt.context });
    ad.onClose?.(attempt.closeHandler);
    ad.onError?.(attempt.errorHandler);

    return Promise.resolve()
      .then(() => ad.show())
      .catch((showError) => {
        if (attempt.settled) return undefined;
        return Promise.resolve()
          .then(() => ad.load?.())
          .then(() => ad.show())
          .catch((loadError) => settle(attempt, false, loadError || showError));
      });
  };
}

export function startMiniGame() {
  const api = getHostApi();
  if (!api || typeof api.createCanvas !== 'function') {
    throw new Error('[MINIGAME] mini-game runtime requires wx.createCanvas() or tt.createCanvas()');
  }

  const canvas = api.createCanvas();
  const info = getSystemInfo(api);
  const dims = init(canvas, info);
  const clock = createMiniGameClock(getNow);
  const cctvMotion = createCctvMotionController(getNow);
  const audio = createMiniGameAudio(api);
  const vibrate = (type = 'light') => {
    try { api.vibrateShort?.({ type }); } catch { /* optional haptics */ }
  };
  const audioStorageKey = 'minigame_audio_muted_v1';
  try {
    audio.setMuted(api.getStorageSync?.(audioStorageKey) === true);
  } catch {
    audio.setMuted(false);
  }
  let sidebarAvailable = typeof api.navigateToScene === 'function' && typeof api.checkScene === 'function';
  const refreshSidebarAvailability = () => checkDouyinSidebar(api).then((available) => {
    sidebarAvailable = available;
    return available;
  });
  refreshSidebarAvailability();
  let session = createRuntimeSession();
  let state = session.state;
  let nextAnomalyAt = session.nextAnomalyAt;
  let lastSnapshotAt = 0;
  let failureRecorded = false;
  let runToken = 0;
  let nextNormalInspectionAt = Number.POSITIVE_INFINITY;
  let lifecycleHidden = false;
  let adPauseActive = false;

  function pauseForAd() {
    adPauseActive = true;
    clock.pause();
    cctvMotion.pause();
    audio.stopAll();
  }

  function resumeAfterAd() {
    adPauseActive = false;
    if (!lifecycleHidden) {
      clock.resume();
      cctvMotion.resume();
    }
  }

  function showAdError() {
    api.showToast?.({ title: t('ui.adUnavailable'), icon: 'none' });
  }

  const reviveAd = createMiniGameRewardedAd(api, CONFIG.adUnits?.revive, {
    releaseMode: CONFIG.releaseMode,
    onReward: (meta) => {
      if (!shouldApplyReward(meta, runToken, 'revive', state)) return;
      state = reviveFromAd(state);
      cctvMotion.reset();
      state = { ...state, inspection: null };
      nextNormalInspectionAt = state.elapsed + 4;
      audio.play('result');
      nextAnomalyAt = scheduleNextAnomalyAfterRevive(state.elapsed);
      failureRecorded = false;
    },
    onStart: pauseForAd,
    onSettled: resumeAfterAd,
    onError: (error) => {
      console.warn('[MINIGAME] revive ad failed', error);
      showAdError();
    },
  });

  const truthAd = createMiniGameRewardedAd(api, CONFIG.adUnits?.truth, {
    releaseMode: CONFIG.releaseMode,
    onReward: (meta) => {
      if (!shouldApplyReward(meta, runToken, 'truth', state)) return;
      state = { ...state, fakeEndingUnlocked: true, fakeEndingTruth: state.lastAdHint || '' };
    },
    onStart: pauseForAd,
    onSettled: resumeAfterAd,
    onError: (error) => {
      console.warn('[MINIGAME] truth ad failed', error);
      showAdError();
    },
  });

  const decodeAd = createMiniGameRewardedAd(api, CONFIG.adUnits?.decode, {
    releaseMode: CONFIG.releaseMode,
    onReward: (meta) => {
      if (!shouldApplyReward(meta, runToken, 'decode', state)) return;
      const result = performAction(state, 'unlockHiddenLog');
      state = result.state;
    },
    onStart: pauseForAd,
    onSettled: resumeAfterAd,
    onError: (error) => {
      console.warn('[MINIGAME] decode ad failed', error);
      showAdError();
    },
  });

  function getViewState() {
    return {
      started: clock.isStarted(),
      paused: clock.isPaused(),
      muted: audio.isMuted(),
      sidebarAvailable,
      cctvMotion: cctvMotion.sample(state),
    };
  }

  function toggleMute() {
    const muted = audio.setMuted(!audio.isMuted());
    try {
      api.setStorageSync?.(audioStorageKey, muted);
    } catch {
      // Audio preference persistence is best-effort and never blocks play.
    }
  }

  function start() {
    if (clock.isStarted()) return;
    audio.play('boot');
    state = openInspection(state, {
      id: `baseline-${runToken}`,
      kind: 'normal',
      title: t('ui.baselineInspectionTitle'),
      duration: 6,
    });
    nextNormalInspectionAt = Number.POSITIVE_INFINITY;
    clock.start();
  }

  function openSidebar() {
    navigateToDouyinSidebar(api).then((opened) => {
      if (!opened) api.showToast?.({ title: '当前环境无法打开侧边栏', icon: 'none' });
    });
  }

  function restart() {
    runToken += 1;
    audio.play('boot');
    clock.start();
    session = restartRuntimeSession({ state });
    state = session.state;
    cctvMotion.reset();
    state = openInspection(state, {
      id: `baseline-${runToken}`,
      kind: 'normal',
      title: t('ui.baselineInspectionTitle'),
      duration: 6,
    });
    nextNormalInspectionAt = Number.POSITIVE_INFINITY;
    nextAnomalyAt = session.nextAnomalyAt;
    lastSnapshotAt = 0;
    failureRecorded = false;
  }

  function resolveActiveAnomalyAutomatically(feedbackKey) {
    if (!state.activeAnomaly) return false;
    const automaticAction = getAnomalyResolutionAction(state.activeAnomaly);
    const before = state;
    const scoreBeforeTreatment = state.score || 0;
    const automatic = automaticAction ? performAction(state, automaticAction) : { ok: false, state };
    state = {
      ...automatic.state,
      activeAnomaly: null,
      score: scoreBeforeTreatment,
      lastFeedback: t(feedbackKey),
    };
    if (automatic.ok) cctvMotion.startAction(automaticAction, before, state);
    return automatic.ok;
  }

  function handleDecision(choice) {
    if (state.gameOver) return;
    const inspectionKind = state.inspection?.kind;
    const result = submitInspection(state, choice);
    state = result.state;
    if (!result.accepted) {
      if (result.coached) {
        audio.play('wrong');
        vibrate('medium');
      }
      return;
    }
    if (result.correct && inspectionKind === 'normal') {
      audio.play('release');
      vibrate('light');
    } else if (result.correct && inspectionKind === 'anomaly') {
      audio.play('lockdown');
      vibrate('medium');
    } else {
      audio.play('wrong');
      vibrate('heavy');
    }

    // 基础模式不增加第二次按钮学习：异常判断结束后由系统自动执行对应处置。
    if (inspectionKind === 'anomaly' && state.activeAnomaly) {
      resolveActiveAnomalyAutomatically(result.correct ? 'ui.autoResolutionCorrect' : 'ui.autoResolutionWrong');
    }

    // 正常放行后电梯自动离站：操作成为结果反馈，不再让新手学习四键驾驶。
    if (result.correct && inspectionKind === 'normal' && !state.activeAnomaly) {
      const automaticAction = state.door === 'closed' ? 'moveUp' : 'closeDoor';
      const before = state;
      const automatic = performAction(state, automaticAction);
      state = automatic.state;
      if (automatic.ok) {
        cctvMotion.startAction(automaticAction, before, state);
        audio.play(automaticAction === 'moveUp' ? 'motor' : 'click');
      }
    }
    // 教学第二班必须直接进入异常，不允许中间插入随机正常巡检。
    const tutorialStep = Number(state.tutorialStep || 0);
    nextNormalInspectionAt = tutorialStep === 1
      ? Number.POSITIVE_INFINITY
      : state.elapsed + (tutorialStep === 3 ? 2 : 4);
  }

  function handleAction(actionId) {
    if (state.gameOver) return;
    if (actionId === 'unlockHiddenLog') {
      decodeAd({ runToken });
      return;
    }
    const before = state;
    const result = performAction(state, actionId);
    state = result.state;
    if (result.ok) {
      cctvMotion.startAction(actionId, before, state);
      audio.play('release');
      vibrate('light');
    } else {
      audio.play('wrong');
      vibrate('heavy');
    }
  }

  function handleAd(kind) {
    if (kind === 'truth') {
      truthAd({ runToken });
    } else {
      reviveAd({ runToken });
    }
  }

  function onTouch(e) {
    const touch = e.touches?.[0] || e.changedTouches?.[0] || e;
    const screenW = info.windowWidth || 750;
    const screenH = info.windowHeight || 1334;
    const x = (touch.clientX ?? touch.screenX ?? touch.x ?? 0) * (750 / screenW);
    const y = (touch.clientY ?? touch.screenY ?? touch.y ?? 0) * (dims.height / screenH);
    onCanvasClick(x, y, state, {
      onAction: handleAction,
      onDecision: handleDecision,
      onToggleMute: toggleMute,
      onAdRevive: handleAd,
      onRestart: restart,
      onStart: start,
      onSidebar: openSidebar,
    }, getViewState());
  }

  api.onTouchStart?.(onTouch);
  bindMiniGameLifecycle(api, {
    onPause: () => {
      lifecycleHidden = true;
      clock.pause();
      cctvMotion.pause();
      audio.stopAll();
    },
    onResume: () => {
      lifecycleHidden = false;
      refreshSidebarAvailability();
      if (!adPauseActive) {
        clock.resume();
        cctvMotion.resume();
      }
    },
  });

  function update() {
    const delta = clock.consumeDeltaSeconds();
    if (delta > 0) {
      if (!state.gameOver) {
        for (let i = 0; i < delta; i += 1) {
          state = tickState(state, 1);
          if (!state.gameOver) {
            const expiredKind = state.inspection?.kind;
            const expiry = expireInspection(state);
            state = expiry.state;
            if (expiry.timedOut) {
              audio.play(expiry.coached ? 'wrong' : 'result');
              if (expiredKind === 'anomaly' && state.activeAnomaly) {
                resolveActiveAnomalyAutomatically('ui.autoResolutionTimeout');
              }
              const stepAfterTimeout = Number(state.tutorialStep || 0);
              nextNormalInspectionAt = stepAfterTimeout === 1
                ? Number.POSITIVE_INFINITY
                : state.elapsed + (stepAfterTimeout === 3 ? 2 : 4);
            }
          }
          if (
            !state.gameOver
            && state.inspection?.status !== 'pending'
            && !state.activeAnomaly
            && state.elapsed >= nextNormalInspectionAt
            && (Number(state.tutorialStep || 0) === 3 || state.elapsed + 3 < nextAnomalyAt)
          ) {
            cctvMotion.reset();
            state = openInspection(state, {
              id: `baseline-${runToken}-${state.elapsed}`,
              kind: 'normal',
              title: t('ui.baselineInspectionTitle'),
              duration: 4,
            });
            audio.play('boot');
            nextNormalInspectionAt = Number.POSITIVE_INFINITY;
          }
          if (!state.gameOver && state.elapsed - lastSnapshotAt >= CONFIG.adRevive.snapshotInterval) {
            state = saveSnapshot(state);
            lastSnapshotAt = state.elapsed;
          }
          if (
            !state.gameOver
            && state.inspection?.status !== 'pending'
            && !state.activeAnomaly
            && state.elapsed >= nextAnomalyAt
          ) {
            // 第二班固定为楼层跳变，确保教学展示具体可比较的画面/主控矛盾。
            const event = Number(state.tutorialStep || 0) === 1
              ? (findAnomaly('floor_jump') || pickNextAnomaly(state))
              : pickNextAnomaly(state);
            const beforeAnomaly = state;
            audio.play('boot');
            const result = applyAnomaly(state, event.id);
            state = openInspection(result.state, {
              id: event.id,
              kind: 'anomaly',
              title: t('ui.anomalyInspectionTitle'),
              duration: 5,
            });
            cctvMotion.startAnomaly(beforeAnomaly, state);
            nextNormalInspectionAt = Number.POSITIVE_INFINITY;
            nextAnomalyAt = scheduleNextAnomalyAfterTrigger(state.elapsed);
          }
        }
      }
      if (state.gameOver && !failureRecorded) {
        state = state.result === 'success' ? recordSuccessfulShift(state) : recordFailure(state);
        audio.play('result');
        failureRecorded = true;
      }
    }

    render(state, getViewState());
    nextFrame(api, update);
  }

  render(state, getViewState());
  nextFrame(api, update);
  return { canvas, getState: () => state, restart, start };
}
