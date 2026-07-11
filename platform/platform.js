/**
 * platform.js — 平台抽象层
 *
 * 统一浏览器/微信小游戏/抖音小游戏的 API 差异。
 * 游戏引擎只依赖此模块，不直接调用平台 API。
 */

import CONFIG from '../src/gameConfig.js';

// ── 环境检测 ──
const env = (() => {
  if (typeof wx !== 'undefined' && wx && typeof wx.createRewardedVideoAd === 'function') {
    return 'wechat';
  }
  if (typeof tt !== 'undefined' && tt && typeof tt.createRewardedVideoAd === 'function') {
    return 'douyin';
  }
  return 'browser';
})();

// ── Canvas ──
let mainCanvas = null;
let mainCtx = null;

/**
 * 获取/创建主画布
 */
export function getCanvas(width = 750, height = 1334) {
  if (mainCanvas) return mainCanvas;

  if (env === 'wechat') {
    mainCanvas = wx.createCanvas();
    mainCanvas.width = width;
    mainCanvas.height = height;
  } else if (env === 'douyin') {
    mainCanvas = tt.createCanvas();
    mainCanvas.width = width;
    mainCanvas.height = height;
  } else {
    // 浏览器模式 — 使用 DOM 渲染，canvas 仅作为 fallback
    mainCanvas = document.createElement('canvas');
    mainCanvas.width = width;
    mainCanvas.height = height;
    mainCanvas.style.display = 'none';
    document.body.appendChild(mainCanvas);
  }

  mainCtx = mainCanvas.getContext('2d');
  return mainCanvas;
}

export function getContext() {
  if (!mainCtx) getCanvas();
  return mainCtx;
}

// ── 广告 ──
let adInstances = {};

function createHostRewardedAd(hostApi, adUnitId, callbacks, label) {
  const { onReward, onError } = callbacks;
  let activeAttempt = null;
  let attemptSequence = 0;

  const settle = (attempt, { rewarded = false, error = null } = {}) => {
    if (!attempt || attempt.settled) return;
    attempt.settled = true;
    if (activeAttempt === attempt) activeAttempt = null;
    const meta = { attemptId: attempt.id, context: attempt.context };
    if (error) console.warn(`[ad:${label}] error:`, error);
    if (rewarded || (error && !CONFIG.releaseMode)) onReward?.(meta);
    if (error) onError?.(error, meta);
    attempt.ad.offClose?.(attempt.closeHandler);
    attempt.ad.offError?.(attempt.errorHandler);
    attempt.ad.destroy?.();
  };

  return (context = null) => {
    if (activeAttempt && !activeAttempt.settled) return Promise.resolve();
    const ad = hostApi.createRewardedVideoAd({ adUnitId });
    const attempt = {
      id: ++attemptSequence,
      context,
      settled: false,
      ad,
      closeHandler: null,
      errorHandler: null,
    };
    attempt.closeHandler = (res) => settle(attempt, { rewarded: Boolean(res?.isEnded) });
    attempt.errorHandler = (error) => settle(attempt, { error });
    activeAttempt = attempt;
    ad.onClose(attempt.closeHandler);
    ad.onError(attempt.errorHandler);

    return Promise.resolve()
      .then(() => ad.show())
      .catch((showError) => {
        if (attempt.settled) return undefined;
        return Promise.resolve()
          .then(() => ad.load?.())
          .then(() => ad.show())
          .catch((loadError) => settle(attempt, { error: loadError || showError }));
      });
  };
}

/**
 * 创建激励视频广告
 * @param {string} adUnitId - 广告位 ID
 * @param {object} callbacks - { onReward, onError }
 * @returns {function} show() 函数
 */
export function createRewardedAd(adUnitId, callbacks = {}) {
  if (adInstances[adUnitId]) return adInstances[adUnitId];

  const { onReward, onError } = callbacks;

  if (env === 'wechat') {
    const show = createHostRewardedAd(wx, adUnitId, callbacks, 'wechat');
    adInstances[adUnitId] = show;
    return show;
  }

  if (env === 'douyin') {
    const show = createHostRewardedAd(tt, adUnitId, callbacks, 'douyin');
    adInstances[adUnitId] = show;
    return show;
  }

  // 浏览器模式 — 模拟广告；同样回传发起时上下文，供运行时拒绝陈旧奖励。
  let browserAttempt = null;
  let browserAttemptSequence = 0;
  const show = (context = null) => {
    if (browserAttempt && !browserAttempt.settled) return Promise.resolve();
    browserAttempt = { id: ++browserAttemptSequence, context, settled: false };
    const activeAttempt = browserAttempt;
    return new Promise((resolve) => {
      console.log('[ad] 模拟广告播放中...');
      setTimeout(() => {
        activeAttempt.settled = true;
        console.log('[ad] 模拟广告完成');
        onReward?.({ attemptId: activeAttempt.id, context: activeAttempt.context });
        resolve();
      }, CONFIG?.adContent?.adVideoDuration ?? 2000);
    });
  };
  adInstances[adUnitId] = show;
  return show;
}

// ── 存储 ──
export function setStorage(key, value) {
  try {
    const data = JSON.stringify(value);
    if (env === 'wechat') wx.setStorageSync(key, data);
    else if (env === 'douyin') tt.setStorageSync(key, data);
    else localStorage.setItem(key, data);
  } catch (e) {
    console.warn('[storage] set failed:', e);
  }
}

export function getStorage(key, fallback = null) {
  try {
    let data;
    if (env === 'wechat') data = wx.getStorageSync(key);
    else if (env === 'douyin') data = tt.getStorageSync(key);
    else data = localStorage.getItem(key);
    return data ? JSON.parse(data) : fallback;
  } catch {
    return fallback;
  }
}

// ── 事件绑定 ──
export function onTouch(canvas, handler) {
  const cb = (e) => {
    const touch = e.touches?.[0] || e;
    const rect = canvas.getBoundingClientRect?.();
    const x = (touch.clientX || touch.x) - (rect?.left || 0);
    const y = (touch.clientY || touch.y) - (rect?.top || 0);
    handler(x, y, e);
  };

  if (env === 'wechat') {
    wx.onTouchStart(cb);
  } else if (env === 'douyin') {
    tt.onTouchStart(cb);
  } else {
    canvas.addEventListener('click', cb);
  }
}

// ── 信息 ──
export function getSystemInfo() {
  if (env === 'wechat') return wx.getSystemInfoSync();
  if (env === 'douyin') return tt.getSystemInfoSync();
  return {
    windowWidth: window.innerWidth,
    windowHeight: window.innerHeight,
    pixelRatio: window.devicePixelRatio || 1,
    platform: 'browser',
  };
}

export { env };
