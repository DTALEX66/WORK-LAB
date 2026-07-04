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
