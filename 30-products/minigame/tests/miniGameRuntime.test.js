import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

import { createMiniGameRewardedAd } from '../platform/miniGameRuntime.js';

function createRejectingAdApi() {
  return {
    createRewardedVideoAd() {
      return {
        onClose() {},
        onError() {},
        show: () => Promise.reject(new Error('show failed')),
        load: () => Promise.reject(new Error('load failed')),
      };
    },
  };
}

test('mini-game rewarded ads fail closed in release mode', async () => {
  let rewards = 0;
  let errors = 0;
  const show = createMiniGameRewardedAd(createRejectingAdApi(), 'adunit-real', {
    releaseMode: true,
    onReward: () => { rewards += 1; },
    onError: () => { errors += 1; },
  });

  await show();

  assert.equal(rewards, 0);
  assert.equal(errors, 1);
});

test('mini-game rewarded ads expose start and settlement hooks for active clock pause', async () => {
  let closeHandler;
  let starts = 0;
  let settlements = 0;
  const api = {
    createRewardedVideoAd() {
      return {
        onClose(handler) { closeHandler = handler; },
        onError() {},
        show: () => Promise.resolve(),
      };
    },
  };
  const show = createMiniGameRewardedAd(api, 'adunit-real', {
    releaseMode: true,
    onStart: () => { starts += 1; },
    onSettled: () => { settlements += 1; },
  });
  await show();
  assert.equal(starts, 1);
  assert.equal(settlements, 0);
  closeHandler({ isEnded: false });
  assert.equal(settlements, 1);
});

test('mini-game rewarded ads reward exactly once only after completed close', async () => {
  let closeHandler;
  let rewards = 0;
  const api = {
    createRewardedVideoAd() {
      return {
        onClose(handler) { closeHandler = handler; },
        onError() {},
        show: () => Promise.resolve(),
        load: () => Promise.resolve(),
      };
    },
  };
  const show = createMiniGameRewardedAd(api, 'adunit-real', {
    releaseMode: true,
    onReward: () => { rewards += 1; },
  });

  await show();
  closeHandler({ isEnded: false });
  assert.equal(rewards, 0);

  await show();
  closeHandler({ isEnded: true });
  closeHandler({ isEnded: true });

  assert.equal(rewards, 1);
});

test('mini-game rewarded ads ignore duplicate show attempts until close', async () => {
  const closeHandlers = [];
  let showCalls = 0;
  let rewards = 0;
  let rewardMeta;
  const api = {
    createRewardedVideoAd() {
      return {
        onClose(handler) { closeHandlers.push(handler); },
        onError() {},
        show: async () => { showCalls += 1; },
        load: async () => {},
      };
    },
  };
  const show = createMiniGameRewardedAd(api, 'adunit-real', {
    releaseMode: true,
    onReward: (meta) => { rewards += 1; rewardMeta = meta; },
  });

  await Promise.all([show({ runToken: 12 }), show({ runToken: 12 })]);
  assert.equal(showCalls, 1);
  closeHandlers[0]({ isEnded: true });
  assert.equal(rewards, 1);
  assert.equal(rewardMeta?.context?.runToken, 12);

  await show({ runToken: 13 });
  closeHandlers[0]({ isEnded: true });
  assert.equal(rewards, 1, 'stale close from first attempt must not settle the second attempt');
  closeHandlers[1]({ isEnded: true });
  assert.equal(rewards, 2);
  assert.equal(rewardMeta?.context?.runToken, 13);
});

test('mini-game runtime drives and pauses the CCTV motion timeline', () => {
  const source = readFileSync(new URL('../platform/miniGameRuntime.js', import.meta.url), 'utf8');
  assert.match(source, /createCctvMotionController\(getNow\)/);
  assert.match(source, /cctvMotion\.startAction\(actionId, before, state\)/);
  assert.match(source, /cctvMotion\.startAnomaly\(beforeAnomaly, state\)/);
  assert.match(source, /cctvMotion:\s*cctvMotion\.sample\(state\)/);
  assert.match(source, /clock\.pause\(\);[\s\S]*cctvMotion\.pause\(\)/);
  assert.match(source, /clock\.resume\(\);[\s\S]*cctvMotion\.resume\(\)/);
  assert.match(source, /cctvMotion\.reset\(\);\s*state = openInspection/, 'each new normal class must clear stale anomaly/action motion');
});

test('mini-game runtime starts calm BGM after user gesture and switches with anomaly pressure', () => {
  const source = readFileSync(new URL('../platform/miniGameRuntime.js', import.meta.url), 'utf8');
  assert.match(source, /function start\(\)[\s\S]*audio\.setMusicState\('calm'\)/);
  assert.match(source, /state\.activeAnomaly \? 'pressure' : 'calm'/);
  assert.match(source, /pauseForAd[\s\S]*audio\.stopAll\(\)/);
  assert.match(source, /resumeAfterAd[\s\S]*audio\.resumeMusic\(\)/);
  assert.match(source, /onPause:[\s\S]*audio\.stopAll\(\)/);
  assert.match(source, /onResume:[\s\S]*audio\.resumeMusic\(\)/);
});

test('base 60-second mode auto-resolves reported anomalies without a second player control layer', () => {
  const runtimeSource = readFileSync(new URL('../platform/miniGameRuntime.js', import.meta.url), 'utf8');
  const rendererSource = readFileSync(new URL('../platform/canvasRenderer.js', import.meta.url), 'utf8');
  assert.match(runtimeSource, /getAnomalyResolutionAction\(state\.activeAnomaly\)/);
  assert.match(runtimeSource, /基础模式不增加第二次按钮学习/);
  assert.match(runtimeSource, /教学第二班必须直接进入异常/);
  assert.match(runtimeSource, /findAnomaly\('floor_jump'\)/);
  assert.match(rendererSource, /系统处置中/);
  assert.doesNotMatch(rendererSource.match(/export function getCanvasVisibleActionButtons[\s\S]*?\n}/)?.[0] || '', /recommended:\s*true/);
});

test('quick V5 tutorial handoff installs the first chain shift, while later outcomes advance it', () => {
  const source = readFileSync(new URL('../platform/miniGameRuntime.js', import.meta.url), 'utf8');
  assert.match(source, /openScheduledNightInspection\(scheduleNextNightShift\(state, __V5_CONTENT__\)\)/);
  assert.match(source, /function scheduleFollowingNightShift[\s\S]*advanceCurrentNightEventChain[\s\S]*openScheduledNightInspection/);
  assert.match(source, /expiredNightShift[\s\S]*scheduleFollowingNightShift\(state, \{ correct: false \}\)/);
});

test('mini-game decode action is gated by the decode rewarded-ad slot', () => {
  const source = readFileSync(new URL('../platform/miniGameRuntime.js', import.meta.url), 'utf8');
  assert.match(source, /const decodeAd = createMiniGameRewardedAd/, 'runtime should create a dedicated decode ad');
  assert.match(source, /onReward:\s*\(meta\)[\s\S]*shouldApplyReward\(meta, runToken, 'decode', state\)/, 'decode reward should reject stale or invalid state');
  assert.match(source, /actionId === 'unlockHiddenLog'[\s\S]*decodeAd\(\{ runToken \}\)/, 'decode action must carry the originating run token');
  assert.match(source, /onStart:\s*pauseForAd/);
  assert.match(source, /onSettled:\s*resumeAfterAd/);
  assert.match(source, /function pauseForAd\(\)[\s\S]*clock\.pause\(\)/);
  assert.match(source, /function resumeAfterAd\(\)[\s\S]*!lifecycleHidden[\s\S]*clock\.resume\(\)/);
  assert.match(source, /state\.result === 'success' \? recordSuccessfulShift/, 'Canvas loop should consume the state-machine result');
});
