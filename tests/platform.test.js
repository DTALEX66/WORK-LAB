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

test('host rewarded ads settle each attempt once across duplicate and out-of-order callbacks', async () => {
  for (const hostName of ['wx', 'tt']) {
    const originalWx = globalThis.wx;
    const originalTt = globalThis.tt;
    const originalReleaseMode = CONFIG.releaseMode;
    const closeHandlers = [];
    const errorHandlers = [];
    let showCalls = 0;
    let rewards = 0;
    let errors = 0;
    let rewardMeta;
    let errorMeta;

    delete globalThis.wx;
    delete globalThis.tt;
    globalThis[hostName] = {
      createRewardedVideoAd() {
        return {
          onClose(handler) { closeHandlers.push(handler); },
          onError(handler) { errorHandlers.push(handler); },
          show: async () => { showCalls += 1; },
          load: async () => {},
        };
      },
    };
    CONFIG.releaseMode = true;

    try {
      const platform = await import(`../platform/platform.js?${hostName}-attempt=${Date.now()}-${Math.random()}`);
      const show = platform.createRewardedAd(`adunit-${hostName}-attempt`, {
        onReward: (meta) => { rewards += 1; rewardMeta = meta; },
        onError: (_error, meta) => { errors += 1; errorMeta = meta; },
      });

      await Promise.all([show({ runToken: 7 }), show({ runToken: 7 })]);
      assert.equal(showCalls, 1, `${hostName} should ignore a concurrent show`);
      closeHandlers[0]({ isEnded: true });
      closeHandlers[0]({ isEnded: true });
      errorHandlers[0](new Error('late error'));
      assert.equal(rewards, 1, `${hostName} should reward a completed attempt once`);
      assert.equal(errors, 0, `${hostName} should ignore callbacks after settlement`);
      assert.equal(rewardMeta?.context?.runToken, 7, `${hostName} should return the originating run token`);

      await show({ runToken: 8 });
      closeHandlers[0]({ isEnded: true });
      assert.equal(rewards, 1, `${hostName} should ignore a stale callback from the prior attempt`);
      errorHandlers[1](new Error('ad failed'));
      errorHandlers[1](new Error('duplicate failure'));
      closeHandlers[1]({ isEnded: true });
      assert.equal(rewards, 1, `${hostName} should not reward a failed release attempt`);
      assert.equal(errors, 1, `${hostName} should report a failed attempt once`);
      assert.equal(errorMeta?.context?.runToken, 8, `${hostName} should report the failed attempt context`);
    } finally {
      CONFIG.releaseMode = originalReleaseMode;
      if (originalWx === undefined) delete globalThis.wx;
      else globalThis.wx = originalWx;
      if (originalTt === undefined) delete globalThis.tt;
      else globalThis.tt = originalTt;
    }
  }
});

test('platform rewarded ads never grant on load failure in release mode', async () => {
  const originalWx = globalThis.wx;
  const originalTt = globalThis.tt;
  const originalReleaseMode = CONFIG.releaseMode;
  let rewards = 0;
  let errors = 0;

  delete globalThis.tt;
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
    if (originalTt === undefined) delete globalThis.tt;
    else globalThis.tt = originalTt;
  }
});
