import test from 'node:test';
import assert from 'node:assert/strict';

import CONFIG from '../src/gameConfig.js';
import { createRewardedAd, env } from '../platform/platform.js';

test('platform detects Node test environment as browser fallback', () => {
  assert.equal(env, 'browser');
});

test('browser rewarded ad mock resolves and grants reward', async () => {
  const originalDuration = CONFIG.adContent.adVideoDuration;
  CONFIG.adContent.adVideoDuration = 0;

  let rewarded = false;
  const show = createRewardedAd('test-adunit-platform-mock', {
    onReward: () => {
      rewarded = true;
    },
  });

  await show();

  assert.equal(rewarded, true);
  CONFIG.adContent.adVideoDuration = originalDuration;
});

test('platform rewarded ads never grant on load failure in release mode', async () => {
  const originalWx = globalThis.wx;
  const originalReleaseMode = CONFIG.releaseMode;
  let rewards = 0;
  let errors = 0;

  globalThis.wx = {
    createRewardedVideoAd() {
      return {
        onClose() {},
        onError() {},
        show: () => Promise.reject(new Error('show failed')),
        load: () => Promise.reject(new Error('load failed')),
      };
    },
  };
  CONFIG.releaseMode = true;

  try {
    const platform = await import(`../platform/platform.js?release-fail-closed=${Date.now()}`);
    const show = platform.createRewardedAd('adunit-real-release', {
      onReward: () => { rewards += 1; },
      onError: () => { errors += 1; },
    });
    await show();

    assert.equal(rewards, 0);
    assert.equal(errors, 1);
  } finally {
    CONFIG.releaseMode = originalReleaseMode;
    if (originalWx === undefined) delete globalThis.wx;
    else globalThis.wx = originalWx;
  }
});
