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
  let closeHandler;
  let showCalls = 0;
  let rewards = 0;
  const api = {
    createRewardedVideoAd() {
      return {
        onClose(handler) { closeHandler = handler; },
        onError() {},
        show: async () => { showCalls += 1; },
        load: async () => {},
      };
    },
  };
  const show = createMiniGameRewardedAd(api, 'adunit-real', {
    releaseMode: true,
    onReward: () => { rewards += 1; },
  });

  await Promise.all([show(), show()]);
  assert.equal(showCalls, 1);
  closeHandler({ isEnded: true });
  assert.equal(rewards, 1);
});

test('mini-game decode action is gated by the decode rewarded-ad slot', () => {
  const source = readFileSync(new URL('../platform/miniGameRuntime.js', import.meta.url), 'utf8');
  assert.match(source, /const decodeAd = createMiniGameRewardedAd/, 'runtime should create a dedicated decode ad');
  assert.match(source, /actionId === 'unlockHiddenLog'[\s\S]*decodeAd\(\)/, 'decode action must not call performAction before ad reward');
});
